class_name SpellFx
extends RefCounted
## Spell visuals and sounds, the client's way (content/spells/spell_fx.json from pipeline/build_spell_fx.py; the
## client's spells.csv / speffects.csv / spnifs.csv and sounds/cc_spells.csv):
##   begin   the spell's own casting animation (start, mid looping), its gather effects on the caster (the hand glows,
##           on the bones speffects names) and the sound set's "gather" sound;
##   fire    the gather effects go, the "cast" effects play on the caster with the "cast" sound;
##   bolt    a projectile effect flies to the target at 850 units / s (BoltSpellHandler) with the "travel" sound;
##   land    the target effect on the target ("targetchest" = chest height, "rootnode" = feet) and the "hit" sound;
##           a resisted spell shows the resist effect and the "resisted" sound instead;
##   fizzle  an interrupted cast drops its gather effects and plays the "fizzle" sound.
## Effects last speffects' Duration (ms) and are then freed. Each plays its NIF's own timeline from the start
## (NifScene.timeline: the particle emit windows, Gleam Ray's streak shown and stretched for half a second).
## Owner 2026-10-10 (Gleam Ray "way overblown, no ray, the explosion massive"): speffects "Auto Scale" = 1 scales the
## effect by the size of the character it sits on (size_of) - the effect NIFs are authored for a full-size figure
## (the explosion's sprites are 2.5 - 6 m), so on a badger cub it is a small pink puff, as in the owner's old-client
## clip; "Track Angle" turns the effect to face the target (the hand burst's streak becomes the ray toward the enemy).

## A bolt's flight (owner 2026-11-09: "one consistent (fast) speed"): faster than the server's 850 units / s (21 m/s),
## the same at any distance - its hit shows a little before the server's damage at long range
const BOLT_SPEED_M := 32.0
## Ray spells (Sun Ray, Gleam Ray ... - a cast effect whose ray shows late in its own timeline, speffects release
## ~0.9 s): the effect starts RAY_LEAD before its ray, so the ray and the hit come almost at once, as a direct damage
## spell's should (owner 2026-11-09: "acting like bolts now and not a DD that lands instantly")
const RAY_LEAD := 0.2
const RAY_FROM := 0.5                        # (a release this late or later: a ray spell)
const FxLight := preload("res://game/fx_light.gd")   # remastered lighting: effects light their surroundings
const Extras := preload("res://game/combat/spell_extras.gd")   # remastered: build-up, burst, trails, scorch, sparks
static var _data := {}
static var _scenes := {}                    # gltf path -> NifScene template (duplicated per use)


static func data() -> Dictionary:
	if _data.is_empty():
		var p = JSON.parse_string(FileAccess.get_file_as_string("res://content/spells/spell_fx.json")) \
				if FileAccess.file_exists("res://content/spells/spell_fx.json") else null
		_data = p if p is Dictionary else {"effects": {}, "fx": {}}
	return _data


static func effect(client_effect: int) -> Dictionary:
	return (data().get("effects", {}) as Dictionary).get(str(client_effect), {})


# Pooled effects (owner 2026-10-10: 250 bots casting at 60+ fps): a finished effect goes back to its pool and the
# next cast of it restarts its timeline - copying a NIF scene (meshes, particle systems, animations) for every cast
# was ~1.4 ms each, ~40 ms a frame in a raid. Effects are also culled (Perf: off screen, beyond fx_range, or over
# max_effects alive - the nearest kept); the characters themselves always stay drawn.
const POOL_MAX := 48                        # spare copies kept per effect NIF
static var _pool := {}                      # gltf path -> [NifScene] ready to reuse
static var _live := {}                      # instance id -> NifScene playing now
static var _prune_at := 0


static func _instance(path: String) -> NifScene:
	var spare: Array = _pool.get(path, [])
	while not spare.is_empty():
		var p = spare.pop_back()
		if is_instance_valid(p):
			(p as NifScene).restart()
			return p
	if not NifScene.is_loaded(path):                   # never loaded: a worker loads it - nothing now (see _play)
		NifScene.prefetch(path, true)
		return null
	var c := NifScene.copy_of(path)
	if c == null:
		return null
	c.timeline = true
	c.set_meta("fx_path", path)
	return c


## An effect is done: back to its pool (its bone holder freed), or freed when the pool is full.
static func release(node: Node) -> void:
	if not is_instance_valid(node):
		return
	var fx: NifScene = node as NifScene
	var holder: Node = null
	if fx == null:
		holder = node
		for c in node.get_children():
			if c is NifScene:
				fx = c
				break
	if fx == null:
		node.queue_free()
		return
	_live.erase(fx.get_instance_id())
	FxLight.detach(fx)
	for c in fx.get_children():
		if c is _Track or c is _Upright:
			c.queue_free()
	if fx.get_parent():
		fx.get_parent().remove_child(fx)
	if holder:
		holder.queue_free()
	var path := String(fx.get_meta("fx_path", ""))
	var spare: Array = _pool.get(path, [])
	if path == "" or spare.size() >= POOL_MAX:
		fx.queue_free()
		return
	spare.append(fx)
	_pool[path] = spare


static func _live_count() -> int:
	var now := Time.get_ticks_msec()
	if now >= _prune_at:                   # effects freed with their character's view
		_prune_at = now + 1000
		for k in _live.keys():
			if not is_instance_valid(_live[k]):
				_live.erase(k)
	return _live.size()


## Behind the loading screen: every effect the zone's monsters and your own spells can show is parsed and its
## textures loaded now, so the first cast of each doesn't stall the game (owner 2026-10-10: a long ~1 fps stretch
## when a crowd started casting). Returns how many effect models were made ready.
## A spell's effect files loading in the background as its cast begins (the cast time is their head start): its
## gathering glows, cast effects, bolt, hit and resist.
static func prefetch(client_effect: int, urgent := true) -> void:
	var e := effect(client_effect)
	if e.is_empty():
		return
	var fx: Dictionary = data().get("fx", {})
	var ids: Array = (e.get("gather", []) as Array) + (e.get("cast_fx", []) as Array)
	for k in ["projectile", "target", "resist", "buildup"]:
		if int(e.get(k, 0)) > 0:
			ids.append(int(e[k]))
	for id in ids:
		var f: Dictionary = fx.get(str(id), {})
		if not f.is_empty():
			NifScene.prefetch(String(f.nif), urgent)


static func preload_effects(client_effects: Array) -> int:
	var paths := {}
	var fx: Dictionary = data().get("fx", {})
	for ce in client_effects:
		var e := effect(int(ce))
		var ids: Array = (e.get("gather", []) as Array) + (e.get("cast_fx", []) as Array)
		for k in ["projectile", "target", "resist"]:
			if int(e.get(k, 0)) > 0:
				ids.append(int(e[k]))
		for id in ids:
			var f: Dictionary = fx.get(str(id), {})
			if not f.is_empty():
				paths[String(f.nif)] = true
	for path in paths:
		var c := NifScene.copy_of(path)        # parses + packs once; the copy itself goes to the pool
		if c:
			c.timeline = true
			c.set_meta("fx_path", path)
			var spare: Array = _pool.get(path, [])
			spare.append(c)
			_pool[path] = spare
	return paths.size()


## The client effects a zone may need: its monsters' spells and the player's.
static func zone_effects(npc_states: Array) -> Array:
	var ces := {}
	for st in npc_states:
		for sid in (st as NpcState).spawn.get("spells", []):
			var ce := int(NpcCasting.spell(int(sid)).get("clienteffect", 0))
			if ce > 0:
				ces[ce] = true
	for line in ClassDb.spell_lines(PlayerData.class_id(), PlayerData.level, PlayerData.specs):
		for sid in line.spells:
			var ce := int(ClassDb.spell(int(sid)).get("clienteffect", 0))
			if ce > 0:
				ces[ce] = true
	return ces.keys()


## How big a character is to the client's Auto Scale, against a standard 1.85 m figure: a race figure's own scale
## (players, humanoid NPCs), a monster model's drawn height / 1.85. Measured against the owner's old-client Gleam Ray
## clip (2026-10-10): the caster's hand glows match at the elf figure's scale, and the hit on a badger cub (about a
## quarter metre tall) is a puff about 1 m across - its height ratio (~0.13), not its spawn size / 50 (0.42, which drew
## the explosion's 6 m purple flash).
const STANDARD_HEIGHT := 1.85
static var _heights := {}                   # model scene path -> its unscaled drawn height


static func size_of(on: Node3D) -> float:
	var m = on.get("model") if on.get("model") != null else on.get("_model")
	if not (m is Node3D):
		return 1.0
	var model := m as Node3D
	if model is Fig3Figure:
		return absf(model.scale.y)
	var info = on.get("info")
	var key := String((info as Dictionary).get("gltf", "")) if info is Dictionary else ""
	if key == "" or not _heights.has(key):
		var lo := INF
		var hi := -INF
		var inv := model.global_transform.affine_inverse()
		for mi in model.find_children("*", "MeshInstance3D", true, false):
			var b: AABB = (inv * (mi as MeshInstance3D).global_transform) * (mi as MeshInstance3D).get_aabb()
			lo = minf(lo, b.position.y)
			hi = maxf(hi, b.end.y)
		if key == "":
			return (hi - lo if hi > lo else STANDARD_HEIGHT) * absf(model.scale.y) / STANDARD_HEIGHT
		_heights[key] = hi - lo if hi > lo else STANDARD_HEIGHT
	return float(_heights[key]) * absf(model.scale.y) / STANDARD_HEIGHT


## Where a bolt leaves its caster (owner 2026-10-31: bolts didn't come out at the right height for every race - a
## fixed 1.3 m): between the casting hands when the figure has them, else 70% of its height (size_of x 1.85 m).
static func launch_point(caster: Node3D) -> Vector3:
	var sk := _skeleton(caster)
	if sk:
		var pts: Array[Vector3] = []
		for b in ["Bip01 R Hand", "Bip01 L Hand"]:
			var i := sk.find_bone(b)
			if i >= 0:
				pts.append(sk.global_transform * sk.get_bone_global_pose(i).origin)
		if pts.size() == 2:
			return (pts[0] + pts[1]) * 0.5
		if pts.size() == 1:
			return pts[0]
	return caster.global_position + Vector3(0, STANDARD_HEIGHT * 0.7 * size_of(caster), 0)


## Where a bolt meets its target: its chest - 60% of its height.
static func aim_point(target: Node3D) -> Vector3:
	var h = target.get("height")
	var height: float = float(h) if h != null and float(h) > 0.0 else STANDARD_HEIGHT * size_of(target)
	return target.global_position + Vector3(0, height * 0.6, 0)


## Keeps a tracking effect turned toward its target (speffects Track Angle) while its bone moves.
class _Track extends Node:
	var fx: Node3D
	var target: Node3D
	var height := 1.8

	func _process(_d: float) -> void:
		if not is_instance_valid(fx) or not is_instance_valid(target):
			queue_free()
			return
		var to := target.global_position + Vector3(0, height * 0.6, 0)
		var dir := to - fx.global_position
		if dir.length() > 0.01:
			var k := fx.global_basis.get_scale()
			fx.global_basis = Basis.looking_at(dir, Vector3.UP).scaled(k)


## A bone-held effect stands upright with the character, at the bone (owner 2026-11-01: Decree of Steel's sword over
## the head - "Paladin Group Strength hit" on Bip01 Head - lay flat and flew off sideways; the old client draws it
## upright, dancing over the head and coming down like a knighting). Our skeleton's bone frames aren't the client's
## Biped frames (a head bone's x runs up the neck), so the effect takes the bone's place and the character's turn.
## Hand glows keep the hand's (Held / Hand bones).
class _Upright extends Node:
	var fx: Node3D
	var body: Node3D
	var k := 1.0

	func _process(_d: float) -> void:
		if not is_instance_valid(fx) or not is_instance_valid(body):
			queue_free()
			return
		# (turned half round: these effects are made facing the figure's -z - the sword over the head came out behind
		# the character, in the old client it's in front; owner 2026-11-01)
		fx.global_basis = (body.global_basis.orthonormalized() * Basis(Vector3.UP, PI)).scaled(Vector3.ONE * k)


static func _skeleton(root: Node) -> Skeleton3D:
	if root == null:
		return null
	if root.has_meta("fx_skel"):                 # cached: walking a figure's 34 parts on every cast added up
		var c = root.get_meta("fx_skel")
		if c == null or is_instance_valid(c):
			return c
	var s := root.find_children("*", "Skeleton3D", true, false)
	var sk: Skeleton3D = s[0] if s.size() > 0 else null
	root.set_meta("fx_skel", sk)
	return sk


## One speffects entry on a character: on its bone, at its chest, or at its feet. Returns the node (freed after the
## effect's duration, or by the caller).
static var prof_play_us := 0                 # debug timing (tests/crowd_probe.gd)
## Your target (the zone viewer keeps it): its effects are never culled.
static var focus: Node3D = null
## Characters your own spells just landed on (instance id -> msec): their hits are never culled either - your target
## is cleared the moment it dies, and the killing blow's hit was culled with it (owner 2026-11-10: "the spell effect
## doesn't seem to trigger on hit if the enemy dies").
static var _mine := {}
const MINE_MS := 4000

## Effects on a character smaller than a standard figure are drawn at the standard size (owner 2026-11-10: "if you're
## blasting a smaller enemy it'll still be visible"); a bigger one's still grow with it, so they show outside its body.
const MIN_FX_SIZE := 1.0


static func fx_size(on: Node3D) -> float:
	var k := size_of(on)
	return k if on is Player else maxf(k, MIN_FX_SIZE)
const SAME_FX_MS := 400
const SAME_FX_MAX := 6
static var _fx_burst := {}                  # effect id -> [when its burst began (ticks ms), copies started in it]
static var prof_sound_us := 0


## hit: a damage spell landing, how big (ClassDb.effect_impact): its light goes off like an explosion (FxLight.hit).
static func play(fx_id: int, on: Node3D, height := 1.8, keep := false, target: Node3D = null, skip := 0.0,
		hit := 0.0) -> Node3D:
	var t0 := Time.get_ticks_usec()
	var r := _play(fx_id, on, height, keep, target, skip, hit)
	prof_play_us += Time.get_ticks_usec() - t0
	return r


static func _play(fx_id: int, on: Node3D, height := 1.8, keep := false, target: Node3D = null, skip := 0.0,
		hit := 0.0) -> Node3D:
	var f: Dictionary = (data().get("fx", {}) as Dictionary).get(str(fx_id), {})
	if f.is_empty() or on == null or not on.is_inside_tree():
		return null
	# one effect landing on many at once (a group buff on eight, a crowd's same spell): at most SAME_FX_MAX copies
	# start in SAME_FX_MS (owner 2026-10-14) - the ones on you always show
	var now := Time.get_ticks_msec()
	var burst: Array = _fx_burst.get(fx_id, [0, 0])
	if now - int(burst[0]) > SAME_FX_MS:
		burst = [now, 0]
	if int(burst[1]) >= SAME_FX_MAX and not (on is Player):
		return null
	burst[1] = int(burst[1]) + 1
	_fx_burst[fx_id] = burst
	var cam := on.get_viewport().get_camera_3d()
	# culled: off screen, too far, or too many alive (the nearest win) - never the ones on you or your target (owner
	# 2026-11-09: hits on the mob he was casting at showed rarely - with the card busy the governor had cut fx_range
	# toward 10 m, and a caster's target is 20 - 35 m away)
	if cam and not Perf.brute and not (on is Player) and on != focus \
			and now - int(_mine.get(on.get_instance_id(), -100000)) > MINE_MS:
		var d := cam.global_position.distance_to(on.global_position)
		if d > 6.0 and (d > Perf.fx_range or not cam.is_position_in_frustum(on.global_position + Vector3(0, 1, 0))
				or _live_count() >= Perf.max_effects):
			return null
	var node: Node3D = _instance(String(f.nif))
	if node == null:
		if NifScene.loading(String(f.nif)):
			if keep:
				# a held effect (the casting hands' glow) still loading: a stand-in the caller holds and drops as usual;
				# the glow goes into it once its files are in (owner 2026-10-31: the first spell after loading in
				# showed no art - its files were still loading when it was cast)
				var stand := Node3D.new()
				stand.name = "FxPending"
				on.add_child(stand)
				_fill_when_loaded(stand, fx_id, on, height, target, String(f.nif))
				return stand
			_play_when_loaded(fx_id, on, height, target, String(f.nif), hit)   # a moment late, not a frozen frame
		return null
	_live[node.get_instance_id()] = node
	var bone := String(f.get("node", ""))
	var skel := _skeleton(on)
	var bi := skel.find_bone(bone) if skel and bone.begins_with("Bip01") else -1
	var fx := node
	if bi >= 0:
		var at := BoneAttachment3D.new()
		at.bone_name = skel.get_bone_name(bi)
		skel.add_child(at)
		at.add_child(node)
		node = at
		# the bone's world scale (the model's) cancelled, then the effect's own size: the character's for Auto Scale
		var want := fx_size(on) if bool(f.get("autoscale", false)) else 1.0
		fx.scale = Vector3.ONE * want / maxf(at.global_basis.get_scale().x, 0.001)
		if not (bone.ends_with("Held") or bone.ends_with("Hand")):
			var up := _Upright.new()
			up.fx = fx
			var m = on.get("_model") if on is Player else on.get("model")
			up.body = m if m is Node3D else on              # (the figure turns, not the player's root)
			up.k = want                                   # (its size in the world, as set above)
			fx.add_child(up)
			up._process(0.0)
	else:
		on.add_child(node)
		var k := fx_size(on) if bool(f.get("autoscale", false)) else 1.0
		fx.scale = Vector3.ONE * k / maxf(on.scale.y, 0.001)
		if bone.to_lower().contains("chest"):
			node.position.y = height * 0.6 / maxf(on.scale.y, 0.001)
		elif bone.to_lower().contains("head"):
			node.position.y = height * 0.9 / maxf(on.scale.y, 0.001)
	# the effect itself on the main thread, not the character's posing thread (NPC views pose on worker threads): its
	# timeline shows / hides its meshes, which only the main thread may do (owner 2026-10-11: the earth crack's plates
	# on an NPC logged hundreds of thread errors and didn't animate). Its bone attachment stays with the skeleton - the
	# posing thread moves it every frame (on the main thread, every bone-held effect on a bot logged an error a frame:
	# 100-500 thousand a session, the stutter near bots - owner 2026-10-13)
	AnimLod.keep_on_main(fx)
	if int(f.get("track", 0)) > 0 and target and is_instance_valid(target):
		var tr := _Track.new()
		tr.fx = fx
		tr.target = target
		tr.height = float(target.get("height")) if target.get("height") != null else 1.8
		fx.add_child(tr)
		tr._process(0.0)
	NifParticles.fit_to_scale(fx)
	if skip > 0.0:
		(fx as NifScene).seek(skip)
	for gp in (fx as NifScene).particles():
		(gp as GPUParticles3D).amount_ratio = Perf.particle_ratio   # fewer sparks in a busy fight (Perf governor)
	var lk := fx_size(on) if bool(f.get("autoscale", false)) else 1.0
	if not keep:
		var secs := float(f.get("duration_s", 3.0))
		on.get_tree().create_timer(secs if secs > 0.0 else 3.0).timeout.connect(func(): release(node))
		FxLight.hit(fx, secs if secs > 0.0 else 3.0, hit)   # an impact's flash and / or a glow for the effect's life
	else:
		FxLight.attach(fx, 1.4, 4.5 * clampf(lk, 0.5, 2.0))   # a held glow (the caster's hands while gathering)
	return node


## A held effect's stand-in (see _play): once the files are in (up to 5 s), the effect plays held on the character,
## released with the stand-in when the caller drops it.
static func _fill_when_loaded(stand: Node3D, fx_id: int, on: Node3D, height: float, target: Node3D, path: String) -> void:
	var tree := on.get_tree()
	var until := Time.get_ticks_msec() + 5000
	while NifScene.loading(path) and Time.get_ticks_msec() < until:
		await tree.process_frame
	if not is_instance_valid(stand) or not stand.is_inside_tree() or not is_instance_valid(on):
		return
	var n := _play(fx_id, on, height, true, target if is_instance_valid(target) else null)
	if n == null:
		return
	if not is_instance_valid(stand) or not stand.is_inside_tree():
		release(n)
		return
	stand.tree_exiting.connect(func(): release(n), CONNECT_ONE_SHOT)


## An effect whose files were still loading: played once they are in (up to 3 s), if its character is still there.
static func _play_when_loaded(fx_id: int, on: Node3D, height: float, target: Node3D, path: String, hit := 0.0) -> void:
	var tree := on.get_tree()
	var until := Time.get_ticks_msec() + 3000
	while NifScene.loading(path) and Time.get_ticks_msec() < until:
		await tree.process_frame
	if NifScene.is_loaded(path) and is_instance_valid(on) and on.is_inside_tree():
		_play(fx_id, on, height, false, target if is_instance_valid(target) else null, 0.0, hit)


## Your level gained: your realm's fanfare (the client's sounds/levalb, levmid, levhib.wav) on the music bus, in place
## of the trifecta effect's spell sound (owner 2026-11-10: "each realm is supposed to have their own sound associated
## with leveling up (like a fanfare). Right now it plays like a buff sound.")
const LEVEL_FANFARE := {"alb": "files/levalb.wav", "mid": "files/levmid.wav", "hib": "files/levhib.wav"}


static func level_fanfare(parent: Node, realm: String) -> void:
	var path := ProjectSettings.globalize_path("res://content/sounds".path_join(String(LEVEL_FANFARE.get(realm, LEVEL_FANFARE.hib))))
	if parent == null or not FileAccess.file_exists(path):
		return
	var p := AudioStreamPlayer.new()
	p.stream = AudioStreamWAV.load_from_file(path)
	if p.stream == null:
		p.free()
		return
	p.bus = "Music" if AudioServer.get_bus_index("Music") >= 0 else "Master"
	p.process_mode = Node.PROCESS_MODE_ALWAYS
	parent.add_child(p)
	p.finished.connect(p.queue_free)
	p.play()


## Someone else's level - a bot, your companion (owner 2026-11-12: "The sound plays at their location, louder the closer
## you are, but not as loud as your own"): the realm's fanfare from where they stand, fading out by 70 m.
static func level_fanfare_at(who: Node3D, realm: String) -> void:
	var path := ProjectSettings.globalize_path("res://content/sounds".path_join(String(LEVEL_FANFARE.get(realm, LEVEL_FANFARE.hib))))
	if who == null or not who.is_inside_tree() or not FileAccess.file_exists(path):
		return
	var p := AudioStreamPlayer3D.new()
	p.stream = AudioStreamWAV.load_from_file(path)
	if p.stream == null:
		p.free()
		return
	p.bus = "Music" if AudioServer.get_bus_index("Music") >= 0 else "Master"
	p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
	p.unit_size = 8.0                                       # full (for another's) within 8 m, then fading with distance
	p.max_distance = 70.0
	p.volume_db = -6.0                                      # never as loud as your own
	p.position = Vector3(0, 1.5, 0)
	who.add_child(p)
	p.finished.connect(p.queue_free)
	p.play()


static func sound(snd: CharacterSounds, set_id: int, event: String) -> void:
	if snd == null or set_id <= 0:
		return
	var t0 := Time.get_ticks_usec()
	_sound(snd, set_id, event)
	prof_sound_us += Time.get_ticks_usec() - t0


# Spells all at once (owner 2026-10-14: a group's buffs, a fight's casters - "sounds like an actual war zone"): the
# same spell sound starting again within SAME_SOUND_MS plays once, and only SPELL_SOUNDS_MAX spell sounds start in
# any SPELL_WINDOW_MS around you; your own spells always sound. (The character sounds' voice cap still applies.)
const SAME_SOUND_MS := 350
const SPELL_WINDOW_MS := 600
const SPELL_SOUNDS_MAX := 4
static var _sound_at := {}                  # spell sound name -> when it last started (ticks ms)
static var _sound_starts: Array = []        # when the spell sounds of the last SPELL_WINDOW_MS started


static func _sound(snd: CharacterSounds, set_id: int, event: String) -> void:
	var row: Dictionary = (snd.index.get("spells", {}) as Dictionary).get(str(set_id), {})
	var name := String(row.get(event, ""))
	if name == "":
		return
	var now := Time.get_ticks_msec()
	while not _sound_starts.is_empty() and now - int(_sound_starts[0]) > SPELL_WINDOW_MS:
		_sound_starts.pop_front()
	var mine := snd.get_parent() is Player
	if not mine and (now - int(_sound_at.get(name, -100000)) < SAME_SOUND_MS or _sound_starts.size() >= SPELL_SOUNDS_MAX):
		return
	_sound_at[name] = now
	_sound_starts.append(now)
	snd.play_structure(name)


## An emote's overlay (emotes.csv Spell column -> spells.csv): Pray 8005 (blue light shafts + a light sprinkle), Level
## Up 8007 (the big camelot knot under you), the realm binds 8010 / 8006 / 8009 - their effects on the character and
## their sound set's hit sound (set 10 for all of them), as the client played the server's emote.
static func emote(client_effect: int, on: Node3D, snd: CharacterSounds) -> void:
	var e := effect(client_effect)
	if e.is_empty() or on == null or not on.is_inside_tree():
		return
	for k in ["buildup", "target"]:
		if int(e.get(k, 0)) > 0:
			play(int(e[k]), on, 1.8)
	sound(snd, int(e.get("sound_set", 0)), "hit")


## The caster starts casting: returns the gather effects (to drop at fire / fizzle).
static func begin(client_effect: int, caster: Node3D, snd: CharacterSounds) -> Array:
	var e := effect(client_effect)
	var out := []
	var cam := caster.get_viewport().get_camera_3d() if caster.is_inside_tree() else null
	if cam and not Perf.brute and cam.global_position.distance_to(caster.global_position) > Perf.gather_range:
		sound(snd, int(e.get("sound_set", 0)), "gather")
		return out                           # a far caster's hand glows: off under load (Perf)
	for id in e.get("gather", []):
		var n := play(int(id), caster, 1.8, true)
		if n:
			out.append(n)
	Extras.gather(out)
	sound(snd, int(e.get("sound_set", 0)), "gather")
	return out


static func drop(handles: Array) -> void:
	for n in handles:
		_wind_down(n)
	handles.clear()


## A held effect let go (the gathering glow as the spell goes off, or the cast broken): its particles stop being made
## and the live ones finish their short lives before it goes back to the pool - the old client's hand sparks flicker
## out after the cast (owner 2026-11-01).
static func _wind_down(node: Node) -> void:
	if not is_instance_valid(node) or not node.is_inside_tree():
		release(node)
		return
	var fx: NifScene = node as NifScene
	if fx == null:
		for c in node.get_children():
			if c is NifScene:
				fx = c
				break
	if fx == null or fx.particles().is_empty():
		release(node)
		return
	var longest := 0.0
	for gp in fx.particles():
		longest = maxf(longest, (gp as GPUParticles3D).lifetime)
	fx.winding_down = true
	node.get_tree().create_timer(clampf(longest, 0.05, 1.0)).timeout.connect(func(): release(node))


static func fizzle(client_effect: int, handles: Array, snd: CharacterSounds) -> void:
	drop(handles)
	sound(snd, int(effect(client_effect).get("sound_set", 0)), "fizzle")


## The spell goes off: cast effects on the caster, the cast sound, and (for a bolt) the projectile toward the target.
## `then` runs when it arrives (immediately with no projectile).
static func fire(client_effect: int, handles: Array, caster: Node3D, snd: CharacterSounds, target: Node3D = null,
		then: Callable = Callable()) -> void:
	# the burst as it goes off, in the gathered glow's colour (remastered)
	for h in handles:
		if h is Node and is_instance_valid(h) and caster and caster.is_inside_tree():
			Extras.release(launch_point(caster), FxLight.color_of(h), caster.get_tree().current_scene)
			break
	drop(handles)
	var e := effect(client_effect)
	# a character's caster effects (spells.csv Effect2 / 3) go with its casting animation: a spell with none (Anim1-3
	# all 0 - the skald's songs and chants) shows only its target effect (owner 2026-10-14: a skald showed the
	# minstrel's musical notes, alb_min_cst, where the original shows only the small blue effect over the head)
	var animated := (e.get("anims", []) as Array).any(func(a): return String(a) != "")
	var figure := caster is Player or (caster is Npc and (caster as Npc).model is Fig3Figure)
	var rel := float(e.get("release_s", 0.0))
	var skip := maxf(rel - RAY_LEAD, 0.0) if rel >= RAY_FROM and int(e.get("projectile", 0)) == 0 else 0.0
	if animated or not figure:
		for id in e.get("cast_fx", []):
			play(int(id), caster, 1.8, false, target, skip)
	sound(snd, int(e.get("sound_set", 0)), "cast")
	var pid := int(e.get("projectile", 0))
	if pid > 0 and target and is_instance_valid(target) and caster.is_inside_tree():
		var f: Dictionary = (data().get("fx", {}) as Dictionary).get(str(pid), {})
		var bolt: Node3D = _instance(String(f.get("nif", ""))) if not f.is_empty() else null
		if bolt == null and not f.is_empty() and NifScene.loading(String(f.nif)):
			# the bolt's files still loading (the first cast after loading in): it flies once they are in, up to 1.5 s
			var tree := caster.get_tree()
			var until := Time.get_ticks_msec() + 1500
			while NifScene.loading(String(f.nif)) and Time.get_ticks_msec() < until:
				await tree.process_frame
			if is_instance_valid(caster) and caster.is_inside_tree() and is_instance_valid(target):
				bolt = _instance(String(f.nif))
		if bolt:
			caster.get_tree().current_scene.add_child(bolt)
			var from := launch_point(caster)
			var to := aim_point(target)
			bolt.global_position = from
			bolt.look_at(to, Vector3.UP, true) if from.distance_to(to) > 0.01 else null
			FxLight.attach(bolt, 2.5, 7.0)                 # a bolt lights the ground it flies over
			Extras.trail(bolt, FxLight.color_of(bolt))     # ... and draws a ribbon behind it (remastered)
			sound(snd, int(e.get("sound_set", 0)), "travel")
			# it homes in: each frame it flies at BOLT_SPEED_M toward where the target is now, not where it was when
			# the bolt left (owner 2026-11-09: bolts flew to where the target had been - "supposed to hone in")
			var tree := caster.get_tree()
			var until := Time.get_ticks_msec() + 6000      # (a target that outruns it, or a stuck frame: it lands anyway)
			while is_instance_valid(bolt) and Time.get_ticks_msec() < until:
				await tree.process_frame
				if not is_instance_valid(bolt):
					break
				if is_instance_valid(target) and target.is_inside_tree():
					to = aim_point(target)
				var step := BOLT_SPEED_M * bolt.get_process_delta_time()
				var gap := to - bolt.global_position
				if gap.length() <= step:
					bolt.global_position = to
					break
				bolt.global_position += gap.normalized() * step
				if gap.length() > 0.05:
					bolt.look_at(to, Vector3.UP, true)
			if is_instance_valid(bolt):
				release(bolt)
			if then.is_valid():
				then.call()
			return
	if then.is_valid():
		then.call()


## On the target: its effect (or the resist effect) and the hit / resisted sound (heard at the target if it has
## sounds, else at the caster).
## A cast effect with a release moment (its streak / flash shows partway in: Gleam Ray's ray at 0.93 s) holds the
## target effect and its sound until then, as the old client did (the ray first, then the puff); the damage itself is
## already dealt.
## hostile: a spell on an enemy (the caller knows the sides) - remastered, it scorches the ground and throws sparks.
const AREA_RING_M := 4.0                     # (the effect data has no radius: an area spell's ring this wide)
static var _ring_at := {}


## mine: your own spell (or one on you) - its hit always shows, even on a target that just died.
static func land(client_effect: int, target: Node3D, height: float, snd: CharacterSounds, resisted := false,
		hostile := false, mine := false) -> void:
	var e := effect(client_effect)
	if mine and target:
		if _mine.size() > 256:
			_mine.clear()
		_mine[target.get_instance_id()] = Time.get_ticks_msec()
	var wait := float(e.get("release_s", 0.0))
	if wait >= RAY_FROM and int(e.get("projectile", 0)) == 0:
		wait = RAY_LEAD                                    # (its cast effect started just before the ray: fire)
	if wait > 0.0 and target and target.is_inside_tree():
		await target.get_tree().create_timer(wait).timeout
		if not is_instance_valid(target) or not target.is_inside_tree():
			return
	var id := int(e.get("resist" if resisted else "target", 0))
	var shown: Node3D = null
	if id > 0:
		shown = play(id, target, height, false, null, 0.0, 0.0 if resisted else ClassDb.effect_impact(client_effect))
	if not resisted and FxLight.enabled:
		var col := FxLight.color_of(shown) if shown else Color(1, 1, 1)
		if hostile:
			Extras.impact(target, col, fx_size(target), height, Extras.is_fire(String(e.get("name", ""))))
		if int(e.get("radius", 0)) > 0:                 # an area spell: one ring for its burst, not one per target
			var now := Time.get_ticks_msec()
			if now - int(_ring_at.get(client_effect, -10000)) > 600:
				_ring_at[client_effect] = now
				Extras.ring(target.global_position, col, AREA_RING_M, target.get_tree().current_scene)
	if not resisted and int(e.get("buildup", 0)) > 0 and int(e.buildup) != id:
		play(int(e.buildup), target, height)            # spells.csv Buildup Effect, with the target effect (a summon's
														# only one: Arawn's eyes on a necromancer's new servant)
	sound(snd, int(e.get("sound_set", 0)), "resisted" if resisted else "hit")
