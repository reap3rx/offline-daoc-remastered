class_name Fig3Figure
extends Node3D
## A Catacombs (fig3) player-race figure with the client's character-creation options (pipeline/build_races.py):
## face, eye colour, skin tone, hair style + colour, tattoo, size and the face sliders, applied the client's way.
##   var f := Fig3Figure.new(); add_child(f); f.load_figure("cel_m"); f.apply({"face": 2, "hair": 3, ...})
## A look is a Dictionary; every key is optional (index 0 = the first option, as listed in figure.json):
##   face, eyes, skin, hair (style), hair_color, tattoo, size (0 Short, 1 Average, 2 Tall),
##   sliders (Array of 0..8 per face slider, 4 = neutral), mood (0..8)

const ROOT := "res://content/characters"
const PARTS := ["head", "body", "lbody", "legs", "boots", "arms", "gloves"]

var meta := {}
var model: Node3D
var anim: AnimationPlayer
var look := {}
var _meshes := {}                   # part name -> [MeshInstance3D] (one per shape)
var _textures := {}                 # basename -> Texture2D
var _texture_dir := ""
static var _shaders := {}
static var _scenes := {}                    # race prefix -> PackedScene of its figure
static var _tex_cache := {}                 # textures shared by every figure


## Which clips loop: movement, idles, the cast / aim holds and sitting; everything else (attacks, styles, parries,
## evades, blocks, flinch, death, fire / ready, cast start / end, sit down / stand up) plays once and holds.
const LOOPING := ["ladder", "idle", "walk", "run", "walk_back", "strafe_left", "strafe_right", "swim", "cast_mid", "sit_idle",
	"bow_aim", "xbow_aim", "xbow_idle", "throw_aim", "fly"]


## The loaders below touch no cache: NpcManager's view preparation runs them on a worker thread ahead of a view
## (owner 2026-10-14: a bot's figure, armour textures and helm parsed on the main thread hitched 100-200 ms each
## when the server streamed new ones in), and the main thread keeps what they made.

## A race's figure, packed: tools/pack_scenes.gd's binary copy (~3x faster than the glTF) or the glTF itself.
static func pack_figure(prefix: String) -> PackedScene:
	var dir := "%s/races/%s" % [ROOT, prefix]
	var scn := dir + "/figure.scn"
	if FileAccess.file_exists(scn) and FileAccess.get_modified_time(scn) >= FileAccess.get_modified_time(dir + "/figure.gltf"):
		var ps := ResourceLoader.load(scn, "PackedScene") as PackedScene
		if ps:
			return ps
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	state.base_path = ProjectSettings.globalize_path(dir)
	if doc.append_from_file(dir + "/figure.gltf", state) != OK:
		return null
	var root := doc.generate_scene(state)
	var packed := PackedScene.new()
	packed.pack(root)
	root.free()                                        # only the template: a loose node is never freed for us
	return packed


static func texture_dir(texture_set := "x4plus") -> String:
	var d := "%s/fig3_textures/%s" % [ROOT, texture_set]
	return d if DirAccess.dir_exists_absolute(ProjectSettings.globalize_path(d)) else ROOT + "/fig3_textures/original"


## A figure texture: the GPU-compressed copy (tools/compress_textures.gd: BC7 with mipmaps, a quarter of the memory, no
## decode; owner 2026-10-10: the game crawled for a minute after loading while the 4x skins were decoded), else the png.
static func load_texture(dir: String, key: String) -> Texture2D:
	var bc := "%s_bc/%s.res" % [dir, key]
	if ResourceLoader.exists(bc):
		var cimg := ResourceLoader.load(bc, "Image") as Image
		if cimg:
			return ImageTexture.create_from_image(cimg)
	var path := "%s/%s.png" % [dir, key]
	if not FileAccess.file_exists(path):
		path = "%s/fig3_textures/original/%s.png" % [ROOT, key]
	var img := Image.load_from_file(path)
	if img == null:
		return null
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


static func pack_helm(path: String) -> PackedScene:
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(ProjectSettings.globalize_path(path), st) != OK:
		return null
	var scene := doc.generate_scene(st)
	var packed := PackedScene.new()
	var ok := packed.pack(scene) == OK
	scene.free()
	return packed if ok else null


## The helm file for a worn helm item on this race prefix ("" none) - helms.json, read once.
static func helm_path(model: int, prefix: String) -> String:
	if _helms.is_empty():
		var t = JSON.parse_string(FileAccess.get_file_as_string("res://content/helms/helms.json")) \
				if FileAccess.file_exists("res://content/helms/helms.json") else null
		_helms = t.get("models", {}) if t is Dictionary else {"_": {}}
	var e: Dictionary = _helms.get(str(model), {}).get(prefix, {})
	return "res://content/helms/" + String(e.file) if e.has("file") else ""


## The seed an NPC figure's look comes from: its id, except a King / Queen's retinue (mod 2026-10-25: the server's
## guild line "<name>'s Retinue"): that line and the NPC's own name (the last word, "Squire Anne" -> "Anne"), so the
## same commander has the same face, hair and skin at every summon and every rank.
static func look_seed(spawn: Dictionary) -> String:
	var guild := String(spawn.get("guild", ""))
	if guild.ends_with("'s Retinue"):
		var n := String(spawn.get("name", "")).strip_edges()
		return guild + ":" + n.get_slice(" ", n.get_slice_count(" ") - 1)
	return String(spawn.get("id", ""))


## An NPC's look from its id (the database records no faces / hair for NPCs): the same for a given id every time.
static func npc_look(id: String, meta: Dictionary) -> Dictionary:
	var h := hash(id)
	var count := func(key: String, look: Dictionary, salt: int) -> int:
		var n := option_count_of(meta, look, key)
		return 0 if n <= 0 else absi(h / salt) % n
	var look := {"face": count.call("face", {}, 1), "skin": 0, "hair": count.call("hair", {}, 13),
			"eyes": count.call("eyes", {}, 31), "hair_color": 0}
	look["hair_color"] = count.call("hair_color", look.duplicate(), 97)
	return look


## The texture keys a figure with this look and armour draws (apply / _apply_armor / _apply_cloak) - for preparing.
static func texture_keys(meta: Dictionary, look: Dictionary, parts: Dictionary) -> Array:
	var out := []
	var faces: Array = meta.get("faces", [])
	if faces.size() > 0:
		out.append(String(faces[clampi(int(look.get("face", 0)), 0, faces.size() - 1)].tex))
	var eyes: Array = meta.get("eyes", [])
	if eyes.size() > 0:
		out.append(String(eyes[clampi(int(look.get("eyes", 0)), 0, eyes.size() - 1)]))
	var clothes: Dictionary = meta.get("clothes", {})
	for part in clothes:
		out.append(String(clothes[part].get("tex", "")))
	var styles: Array = meta.get("hair_styles", [])
	if styles.size() > 0:
		var colours: Array = styles[clampi(int(look.get("hair", 0)), 0, styles.size() - 1)].colours
		if colours.size() > 0:
			out.append(String(colours[clampi(int(look.get("hair_color", 0)), 0, colours.size() - 1)].tex))
	for k in parts:
		var want: Array = parts[k]
		if want.size() > 1:
			out.append(String(want[1]))
	return out.filter(func(x): return x != "").map(func(x): return String(x).to_lower())


static func loops(clip: String) -> bool:
	# the spell casting styles' middle clip is the hold-while-casting loop (anims.csv "... Mid")
	return clip in LOOPING or clip.begins_with("combat_idle") or (clip.begins_with("cast_") and clip.ends_with("_mid"))

func load_figure(prefix: String, texture_set := "x4plus") -> bool:
	race = prefix
	var dir := "%s/races/%s" % [ROOT, prefix]
	meta = NpcManager._metas[prefix] if NpcManager._metas.has(prefix) and not (NpcManager._metas[prefix] as Dictionary).is_empty() 			else JSON.parse_string(FileAccess.get_file_as_string(dir + "/figure.json"))   # (read only: shared)
	_texture_dir = texture_dir(texture_set)
	# one parsed glTF per race: NPCs of the same race share it (a town has dozens)
	if not _scenes.has(prefix) or _scenes[prefix] == null:
		_scenes[prefix] = pack_figure(prefix)
		if _scenes[prefix] == null:
			push_warning("figure missing: " + prefix)
			return false
	model = (_scenes[prefix] as PackedScene).instantiate() as Node3D
	add_child(model)
	for node in model.find_children("*", "MeshInstance3D", true, false):
		var part := String(node.name).get_slice("__", 0)    # a part's extra shapes are named <part>__1, __2 ...
		if not _meshes.has(part):
			_meshes[part] = []
		_meshes[part].append(node)
	var players := model.find_children("*", "AnimationPlayer", true, false)
	if players.size() > 0:
		anim = players[0]
		for clip in anim.get_animation_list():
			var a := anim.get_animation(clip)
			a.loop_mode = Animation.LOOP_LINEAR if loops(clip) else Animation.LOOP_NONE
			if loops(clip) and not a.has_meta("smooth"):
				_use_smooth(prefix, clip, a)
		add_rest_reset(anim)
		if anim.has_animation("idle"):
			anim.play("idle")
	var skels := model.find_children("*", "Skeleton3D", true, false)
	if skels.size() > 0:
		var sway := Sway.new()
		sway.name = "Sway"
		sway.model = model
		sway.fig = self
		(skels[0] as Skeleton3D).add_child(sway)
	apply({})
	_apply_cloak()
	return true


## The converted clips keep the client's keys - 15 a second - and the import packs them (compressed tracks), which
## always join keys with straight lines: a bone's speed changes in a step at every key, a stutter fifteen times a
## second. Small motions hide it; the men's idle sways the whole body four times as far as the women's, and it showed
## as jitter (owner 2026-11-05: "a weird jitteriness ... in male's animations ... Females seem smooth"). The looping
## clips (idles, walking, running, swimming) are rebuilt unpacked through the same keys, with curves between them:
## every pose is the same, the motion between them smooth. The one-shot swings keep their snap. Once per race and clip
## (static): every figure of the race shares the result.
static var _smooth_cache := {}               # "prefix/clip" -> Animation
static var _smooth_lock := Mutex.new()       # (figures are loaded on worker threads too)


func _use_smooth(prefix: String, clip: String, a: Animation) -> void:
	var key := prefix + "/" + clip
	_smooth_lock.lock()
	if not _smooth_cache.has(key):
		_smooth_cache[key] = smoothed(a)
	var b: Animation = _smooth_cache[key]
	_smooth_lock.unlock()
	var lib_name := anim.find_animation_library(a)
	var lib := anim.get_animation_library(lib_name)
	var raw := clip.get_slice("/", 1) if clip.contains("/") else clip
	if lib and lib.has_animation(raw):
		lib.remove_animation(raw)
		lib.add_animation(raw, b)


static func smoothed(a: Animation) -> Animation:
	var b := Animation.new()
	b.length = a.length
	b.loop_mode = a.loop_mode
	b.step = a.step
	# keys up to, not at, the clip's end: a looping cubic track wraps from its last key back to the first, and a key
	# at the very end is the first one again with no time between them - the curve through it divides by that zero
	# and throws the bones about for a moment every loop (owner 2026-11-05: a Breton archer's leg kicking out once
	# a second while she held her bow drawn, bow_aim's 0.93 s)
	var n := maxi(1, int(ceil(a.length * 15.0 - 0.01)))
	var times: Array = []
	for i in n + 1:
		var tm := i / 15.0
		if i == 0 or tm < a.length - 0.02:
			times.append(tm)
	for t in a.get_track_count():
		var ty := a.track_get_type(t)
		var nt := b.add_track(ty)
		b.track_set_path(nt, a.track_get_path(t))
		b.track_set_enabled(nt, a.track_is_enabled(t))
		b.track_set_interpolation_loop_wrap(nt, a.track_get_interpolation_loop_wrap(t))
		var single := a.track_get_key_count(t) <= 1
		match ty:
			Animation.TYPE_POSITION_3D:
				for tm in ([0.0] if single else times):
					b.position_track_insert_key(nt, tm, a.position_track_interpolate(t, tm))
			Animation.TYPE_ROTATION_3D:
				for tm in ([0.0] if single else times):
					b.rotation_track_insert_key(nt, tm, a.rotation_track_interpolate(t, tm))
			Animation.TYPE_SCALE_3D:
				for tm in ([0.0] if single else times):
					b.scale_track_insert_key(nt, tm, a.scale_track_interpolate(t, tm))
			Animation.TYPE_BLEND_SHAPE:
				for tm in ([0.0] if single else times):
					b.blend_shape_track_insert_key(nt, tm, a.blend_shape_track_interpolate(t, tm))
			_:
				for k in a.track_get_key_count(t):
					b.track_insert_key(nt, a.track_get_key_time(t, k), a.track_get_key_value(t, k), a.track_get_key_transition(t, k))
		b.track_set_interpolation_type(nt, Animation.INTERPOLATION_CUBIC if ty in [Animation.TYPE_POSITION_3D,
				Animation.TYPE_ROTATION_3D, Animation.TYPE_SCALE_3D, Animation.TYPE_BLEND_SHAPE] else a.track_get_interpolation_type(t))
	b.set_meta("smooth", true)
	return b


## Merge `changes` into the current look and redraw.
func apply(changes: Dictionary) -> void:
	look.merge(changes, true)
	var tones: Array = meta.get("skin_tones", [[1, 1, 1]])
	var tone: Array = tones[clampi(int(look.get("skin", 0)), 0, tones.size() - 1)]
	var skin := skin_tint(tone)
	var tint_parts: Dictionary = meta.get("skin_tint_parts", {})
	# head: face texture x skin tone, eye colour multiplied, tattoo
	var faces: Array = meta.get("faces", [])
	var head := _part("head")
	if head and faces.size() > 0:
		var m := _material(false, false, skin_shading)
		m.set_shader_parameter("albedo_tex", _tex(faces[clampi(int(look.get("face", 0)), 0, faces.size() - 1)].tex))
		m.set_shader_parameter("tint", skin)
		m.set_shader_parameter("tint_mode", 1)
		var eyes: Array = meta.get("eyes", [])
		if eyes.size() > 0:
			m.set_shader_parameter("eye_tex", _tex(eyes[clampi(int(look.get("eyes", 0)), 0, eyes.size() - 1)]))
			m.set_shader_parameter("has_eye", true)
		var tattoos: Array = meta.get("tattoos", [])
		var ti := int(look.get("tattoo", 0))
		var decal: String = tattoos[ti].tex if ti > 0 and ti < tattoos.size() else ""
		m.set_shader_parameter("has_decal", decal != "")
		if decal != "":
			m.set_shader_parameter("decal_tex", _tex(decal))
		for mi in _parts("head"):
			mi.material_override = m
	# starter clothes: skin tone only through alpha-masked ('a') textures on the parts the race tints
	for part in ["body", "lbody", "legs", "boots", "arms", "gloves"]:
		var c: Dictionary = meta.get("clothes", {}).get(part, {})
		if _parts(part).is_empty() or c.is_empty():
			continue
		var m := _material(false)
		m.set_shader_parameter("albedo_tex", _tex(String(c.tex)))
		_finish(m, String(c.tex))
		var tinted := bool(tint_parts.get(part, false)) and String(c.get("chan", "")) == "a"
		m.set_shader_parameter("tint", skin)
		m.set_shader_parameter("tint_mode", 2 if tinted else 0)
		for mi in _parts(part):
			mi.material_override = m
	# hair: one style node visible, its colour = texture x tint
	var styles: Array = meta.get("hair_styles", [])
	var si := clampi(int(look.get("hair", 0)), 0, maxi(styles.size() - 1, 0))
	for i in styles.size():
		var node = styles[i].node
		if node == null or not _meshes.has(node):
			continue
		for mi in _parts(node):
			mi.visible = i == si and not _hair_covered()
		if i == si:
			var colours: Array = styles[i].colours
			if colours.size() > 0:
				var col: Dictionary = colours[clampi(int(look.get("hair_color", 0)), 0, colours.size() - 1)]
				var m := _material(true)
				m.set_shader_parameter("albedo_tex", _tex(String(col.tex)))
				m.set_shader_parameter("sheen", 1.0)
				m.set_shader_parameter("relief", 0.16)          # (its strands, raised)
				_hair_mat = m
				m.set_shader_parameter("tint", Color(col.tint[0], col.tint[1], col.tint[2]))
				m.set_shader_parameter("tint_mode", 1)
				for mi in _parts(node):
					mi.material_override = m
	# face sliders: 0..8, 4 neutral; below 4 blends the low target, above 4 the high one
	if head:
		var values: Array = look.get("sliders", [])
		var sliders: Array = meta.get("sliders", [])
		for i in sliders.size():
			var v := float(values[i]) if i < values.size() else 4.0
			_blend(head, String(sliders[i].low), clampf((4.0 - v) / 4.0, 0.0, 1.0))
			_blend(head, String(sliders[i].high), clampf((v - 4.0) / 4.0, 0.0, 1.0))
	# size: the race's Catacombs scale x Short 0.95 / Average 1.0 / Tall 1.05
	var sizes := [0.95, 1.0, 1.05]
	scale = Vector3.ONE * float(meta.get("scale", 1.0)) * float(sizes[clampi(int(look.get("size", 1)), 0, 2)])
	_apply_armor()                                         # worn armour over the starter clothes; hides unused variants


## Worn armour (content/characters/armor.json from pipeline/build_armor.py): {slot: [variant, texture]} for body /
## legs / boots / arms / gloves. The slot's mesh variant shows (node "<slot>" is the default variant, "<slot>_v<n>"
## the others), the rest of that slot hides, and the armour texture replaces the starter clothes'. Slots not given
## go back to the race's starter clothes.
func set_armor(parts: Dictionary, tints: Dictionary = {}) -> void:
	armor = parts.duplicate()
	armor_tints = tints.duplicate()
	_apply_armor()


var skin_shading := true                    # the remastered skin on the face (tests: false shows the old look)
var armor := {}                             # the worn armour parts (set_armor)
var hood_up := false                        # /hood: the cloak's hood up (the server's hood state for this figure)
var cloak_hidden := false                   # the server's hidden-cloak flag (inventory / equipment packets, bit 0x01)
var cloak_emblem := 0                       # the worn cloak's guild emblem (Emblems), 0 none - set before set_armor
var helm_hidden := false                    # the hidden-helm flag (bit 0x02)
var _helm: Node3D
var _helm_hides_hair := false
var _helm_hair := 0                         # the helm's 'Cata Helm Hair' type: the hair takes its helm morph (-1/-2/-3)
static var _helms := {}
static var _helm_scenes := {}


## The worn cloak on the race's cloak meshes (build_races: cloak_1 hood down, cloak_2 hood up, cloak_3 hoodless):
## the item's Catacombs cloak texture with its dye; none shown without a cloak or when it is hidden.
func _apply_cloak() -> void:
	var cloak: Array = armor.get("cloak", [])
	var show := cloak.size() > 1 and not cloak_hidden
	var have := _cloak_meshes()
	var want := 2 if hood_up and have.has(2) else (1 if have.has(1) else (int(have[0]) if have.size() > 0 else 0))
	for k in have:
		for mi in _parts("cloak_%d" % int(k)):
			mi.visible = show and int(k) == want
	if show and want > 0:
		# single sided, as the client draws cloaks (owner 2026-10-11: drawn double sided its inner and outer layers
		# fought and streaked it)
		var m := _material(false, true)
		m.set_shader_parameter("albedo_tex", _tex(String(cloak[1])))
		m.set_shader_parameter("relief", 0.05)
		var dyed: Color = armor_tints.get("cloak", Color.WHITE)
		m.set_shader_parameter("tint", dyed)
		m.set_shader_parameter("tint_mode", 1 if dyed != Color.WHITE else 0)
		# a guild emblem in place of the dye (the server sends one or the other; owner 2026-10-17: guild gamebots)
		m.set_shader_parameter("has_emblem", cloak_emblem > 0)
		if cloak_emblem > 0:
			m.set_shader_parameter("pattern_tex", Emblems.pattern_texture(cloak_emblem))
			var logo := Emblems.logo_texture(Emblems.decode(cloak_emblem).logo)
			m.set_shader_parameter("logo_tex", logo)
			m.set_shader_parameter("has_logo", logo != null)
		for mi in _parts("cloak_%d" % want):
			mi.material_override = m
	_apply_full_helm()
	_refresh_hair()


## Hood up (with the cloak showing) or a helm that covers the hair: the hair isn't drawn.
func _hair_covered() -> bool:
	return _hood_covers() or (_helm != null and _helm_hides_hair) or _full_helm > 0


## The race's cloak meshes as whole numbers: figure.json's list parses as floats, and has(2) never matched 2.0 - the
## hood-up mesh was never drawn (owner 2026-10-15: "/hood doesn't put a hood over the player's head", every race).
func _cloak_meshes() -> Array:
	return (meta.get("cloaks", []) as Array).map(func(x): return int(x))


## The hood up over a showing cloak: as the old client, only the face shows - no hair, no helm (owner 2026-10-15).
func _hood_covers() -> bool:
	var cloak_shown := (armor.get("cloak", []) as Array).size() > 1 and not cloak_hidden
	return hood_up and cloak_shown and _cloak_meshes().has(2)


var _full_helm := 0                        # the worn full helm part (fullhelm_<n>), 0 none
var _full_helm_tex := ""


## The race's full helm parts (figure.json full_helms): all hidden but the worn one, which wears the item's texture;
## the head is drawn only without one (the helm stands in for it).
func _apply_full_helm() -> void:
	var have: Array = (meta.get("full_helms", []) as Array).map(func(x): return int(x))
	var n := _full_helm if have.has(_full_helm) else 0
	for k in have:
		for mi in _parts("fullhelm_%d" % k):
			mi.visible = k == n
	if n > 0 and _full_helm_tex != "":
		var m := _material(false)
		m.set_shader_parameter("albedo_tex", _tex(_full_helm_tex))
		m.set_shader_parameter("tint", Color.WHITE)
		m.set_shader_parameter("tint_mode", 0)
		for mi in _parts("fullhelm_%d" % n):
			mi.material_override = m
	for mi in _parts("head"):
		mi.visible = n == 0


func _refresh_hair() -> void:
	var styles: Array = meta.get("hair_styles", [])
	var si := clampi(int(look.get("hair", 0)), 0, maxi(styles.size() - 1, 0))
	for i in styles.size():
		var node = styles[i].node
		if node == null or not _meshes.has(node):
			continue
		for mi in _parts(node):
			mi.visible = i == si and not _hair_covered()
			# under a helm the hair takes that helm type's morph (flattened so it doesn't poke through), else none.
			# Type 1 is the circlets' (the crafted hat06 circlets, the Crown of Zahur - nothing else uses it): a band
			# that shows the hair, which stays as it is (owner 2026-10-14: circlets hid the hair - its morph tore the
			# hair open over the band)
			var morphs: Dictionary = meta.get("helm_hair", {}).get(String(node), {})
			for k in morphs:
				_blend(mi, String(morphs[k]), 1.0 if _helm != null and int(k) == _helm_hair and _helm_hair != 1 else 0.0)


## The helm / hat for this race and gender (content/helms: the item's Catacombs helm, its texture and scale) on the
## head bone; model 0 or hidden takes it off.
func set_helm(model: int, hidden := false, color := 0) -> void:
	if _helm and is_instance_valid(_helm):
		_helm.queue_free()
	_helm = null
	_helm_hides_hair = false
	_helm_hair = 0
	_full_helm = 0
	helm_path(0, "")                                           # (helms.json read once)
	var top: Dictionary = _helms.get(str(model), {}) if model > 0 else {}
	if model > 0 and not hidden and not _hood_covers() and top.has("full"):
		# a head-swap helm (the Dragonsworn helms, the Dubh Sluagh Cairnwarden's Helm): one of the race's full helm
		# parts in place of the head, in the item's own texture (helms.json "full" / "tex"; build_races full_helms)
		_full_helm = int(top.full)
		_full_helm_tex = String(top.get("tex", ""))
	_apply_full_helm()
	if model > 0 and not hidden and not _hood_covers() and _full_helm == 0:     # (a raised hood hides the helm)
		var e: Dictionary = _helms.get(str(model), {}).get(String(meta.get("prefix", "")), {})
		var skel: Skeleton3D = null
		var sk := find_children("*", "Skeleton3D", true, false)
		if sk.size() > 0:
			skel = sk[0]
		# the skeleton's own helm attach node (Bip01 Helmet: turned so helm NIFs sit upright on the head), else the head
		var bone := "Bip01 Helmet" if skel and skel.find_bone("Bip01 Helmet") >= 0 else "Bip01 Head"
		if not e.is_empty() and skel and skel.find_bone(bone) >= 0:
			var path := "res://content/helms/" + String(e.file)
			if not _helm_scenes.has(path):
				_helm_scenes[path] = pack_helm(path)
			var ps: PackedScene = _helm_scenes[path]
			if ps:
				var at := BoneAttachment3D.new()
				at.bone_name = bone
				skel.add_child(at)
				var h := ps.instantiate() as Node3D
				for c in h.find_children("collision*", "", true, false):
					c.queue_free()
				# the mesh as the NIF places it under the helmet node, shape offset included (owner 2026-10-11: undoing the
				# offset floated the hat a hand above the head - the old client keeps it)
				h.transform = WeaponModels.TO_NIF.scaled_local(Vector3.ONE * float(e.get("scale", 100)) / 100.0)
				at.add_child(h)
				var dyed := dye(color)                              # the item's dye on the helm (multiplied)
				for mi in h.find_children("*", "MeshInstance3D", true, false):
					var mesh_i := mi as MeshInstance3D
					mesh_i.layers = 3
					if dyed != Color.WHITE and mesh_i.mesh:
						for si in mesh_i.mesh.get_surface_count():
							var mat := mesh_i.get_active_material(si)
							if mat is BaseMaterial3D:
								var m2 := (mat as BaseMaterial3D).duplicate() as BaseMaterial3D
								m2.albedo_color = m2.albedo_color * dyed
								mesh_i.set_surface_override_material(si, m2)
				_helm = at
				_helm_hair = int(e.get("hair", 0))
	_refresh_hair()
var armor_tints := {}                       # part -> Color: the item's dye (tints.csv, the client multiplies the texture)
static var _dyes := {}


## An item's Color as the client draws it on a Catacombs figure (tints.csv Cata colour); white for none / unknown.
static func dye(id: int) -> Color:
	if id <= 0:
		return Color.WHITE
	if _dyes.is_empty():
		var t = JSON.parse_string(FileAccess.get_file_as_string("res://content/rules/dye_tints.json")) 				if FileAccess.file_exists("res://content/rules/dye_tints.json") else null
		_dyes = t if t is Dictionary else {"_": [1, 1, 1]}
	var c: Array = _dyes.get(str(id), [1, 1, 1])
	return Color(float(c[0]), float(c[1]), float(c[2]))


func _apply_armor() -> void:
	var parts := armor
	var variants: Dictionary = meta.get("variants", {})
	var clothes: Dictionary = meta.get("clothes", {})
	for slot in ["body", "legs", "boots", "arms", "gloves"]:
		var default_v := int(clothes.get(slot, {}).get("variant", 1))
		var want: Array = parts.get(slot, [])
		var v := int(want[0]) if want.size() > 0 else default_v
		# (as whole numbers: figure.json's lists parse as floats, and has(5) never matched 5.0 - every armour piece
		# fell back to the starter clothes' mesh, no pauldrons on any armour; owner 2026-11-01)
		var have: Array = (variants.get(slot, []) as Array).map(func(x): return int(x))
		if not have.has(v):
			v = default_v                                    # this race lacks that mesh: keep the default shape
		for k in (variants.get(slot, []) as Array):
			var node: String = slot if int(k) == default_v else "%s_v%d" % [slot, int(k)]
			for mi in _parts(node):
				mi.visible = int(k) == v
		var node_name: String = slot if v == default_v else "%s_v%d" % [slot, v]
		var tex := String(want[1]) if want.size() > 1 else String(clothes.get(slot, {}).get("tex", ""))
		if tex == "":
			continue
		var m := _material(false)
		m.set_shader_parameter("albedo_tex", _tex(tex))
		_finish(m, tex)
		# the starter clothes keep the skin tone on their bare skin (Tint Chan 'a' on the parts the race tints): this
		# ran after apply() and drew them untinted - dark-skinned figures had pale arms, hands and Kobold legs under a
		# tinted head (owner 2026-10-11, "red-faced Celts"); real armour has no skin to tint
		var starter := want.size() < 2
		var tinted := starter and bool((meta.get("skin_tint_parts", {}) as Dictionary).get(slot, false)) 				and String(clothes.get(slot, {}).get("chan", "")) == "a"
		m.set_shader_parameter("tint", _skin() if tinted else Color.WHITE)
		m.set_shader_parameter("tint_mode", 2 if tinted else 0)
		if not starter and armor_tints.has(slot) and armor_tints[slot] != Color.WHITE:
			m.set_shader_parameter("tint", armor_tints[slot])   # the item's dye
			m.set_shader_parameter("tint_mode", 1)
		for mi in _parts(node_name):
			mi.material_override = m
	_apply_kilt()
	_apply_cloak()


## A skin tone as the client draws it (owner 2026-10-11, the old client's darkest Celt is a tan and its darkest Norse
## a greyish tan - not the deep red-brown of the tone colour multiplied in full): the fig3tints colour is the skin
## material's diffuse under untinted ambient light, so on the face it comes out half way between white and the tone.
const SKIN_TINT_STRENGTH := 0.5


static func skin_tint(tone: Array) -> Color:
	return Color.WHITE.lerp(Color(float(tone[0]), float(tone[1]), float(tone[2])), SKIN_TINT_STRENGTH)


## The look's skin tone (the race's fig3skincolormap tints).
func _skin() -> Color:
	var tones: Array = meta.get("skin_tones", [[1, 1, 1]])
	var tone: Array = tones[clampi(int(look.get("skin", 0)), 0, tones.size() - 1)]
	return skin_tint(tone)


## The Highlander kilt (lbody, one mesh per body mesh): only the one matching the body worn shows, always in the race's
## own plaid - the Catacombs armour sets carry no lower-body texture (pskins "Cata Chain" etc.), so the client keeps
## the kilt texture. Showing every kilt variant at once gave white, half-plaid skirts (owner 2026-10-10).
func _apply_kilt() -> void:
	var kilts: Array = (meta.get("variants", {}).get("lbody", []) as Array).map(func(x): return int(x))
	var kilt: Dictionary = meta.get("clothes", {}).get("lbody", {})
	if kilts.is_empty() or kilt.is_empty():
		return
	var body_default := int(meta.get("clothes", {}).get("body", {}).get("variant", 1))
	var want: Array = armor.get("body", [])
	var bodies: Array = (meta.get("variants", {}).get("body", []) as Array).map(func(x): return int(x))
	var bv := int(want[0]) if want.size() > 0 and bodies.has(int(want[0])) else body_default
	var kilt_default := int(kilt.get("variant", 1))
	var kv := bv if kilts.has(bv) else kilt_default
	var m := _material(false)
	m.set_shader_parameter("albedo_tex", _tex(String(kilt.get("tex", ""))))
	m.set_shader_parameter("tint", Color.WHITE)
	m.set_shader_parameter("tint_mode", 0)
	for k in kilts:
		var node: String = "lbody" if int(k) == kilt_default else "lbody_v%d" % int(k)
		for mi in _parts(node):
			mi.visible = int(k) == kv
			if int(k) == kv:
				mi.material_override = m


static var _armor := {}


## The armour parts an item model gives a figure of this gender, or {} (pipeline/build_armor.py).
## extension: the item's (the server sends it with the model) picks the torso's Catacombs mesh, as the old client does:
## extension 4 = body mesh 4 (with pauldrons), 0 = mesh 1 - never the number in the texture's name, which is only a
## texture family (owner 2026-11-01: Lancelot's plate and Rian's scale, extension 4, wore mesh 1 here and mesh 4 there;
## Fridwulf's chain hauberk chnbody05, extension 0, wore mesh 5 here and mesh 1 there). Gloves and boots keep theirs.
static func armor_parts(model: int, female: bool, extension := 0) -> Dictionary:
	if _armor.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "/armor.json"))
		_armor = parsed.get("models", {}) if parsed is Dictionary else {"_": {}}
	var parts: Dictionary = _armor.get(str(model), {}).get("f" if female else "m", {})
	if not parts.has("body"):
		return parts
	var out := parts.duplicate()
	var p: Array = (out.body as Array).duplicate()
	p[0] = maxi(1, extension)                                  # (a mesh the race lacks: _apply_armor keeps its default)
	out.body = p
	return out


## Every animated character (player, NPC, monster, bot) gets this: a "RESET" animation holding every bone at its
## rest pose. The deterministic mixer fills any bone the playing clip doesn't key from RESET, so a bone never keeps
## the previous clip's pose. Needed because Godot's glTF import drops one-key tracks equal to the rest pose - the
## client's idle holds Bip01 Pelvis that way, and the spawn jump's 3-degree pelvis stuck through idle (the owner's
## tilted player, 2026-10-09; WORLD IMPORT LESSONS.md).
static func add_rest_reset(anim: AnimationPlayer) -> void:
	var root := anim.get_node_or_null(anim.root_node)
	if root == null:
		return
	var lib := anim.get_animation_library("")
	if lib == null:
		return
	# every copy of a figure shares its scene's animation library: the first copy adds RESET, the rest only need the
	# deterministic mixer - they returned before it was set, so every figure but the first of its race kept the run
	# clip's cloak bones (the idle doesn't key 'cloak control02') and stopped with the cloak flowing out behind
	# (owner 2026-10-16: bots and NPCs, never your own character)
	anim.deterministic = true
	if lib.has_animation("RESET"):
		return
	var reset := Animation.new()
	reset.length = 0.001
	for sk in root.find_children("*", "Skeleton3D", true, false):
		var skel := sk as Skeleton3D
		var base := String(root.get_path_to(skel))
		for i in skel.get_bone_count():
			var rest := skel.get_bone_rest(i)
			var path := NodePath("%s:%s" % [base, skel.get_bone_name(i)])
			var t := reset.add_track(Animation.TYPE_ROTATION_3D)
			reset.track_set_path(t, path)
			reset.rotation_track_insert_key(t, 0.0, rest.basis.get_rotation_quaternion())
			t = reset.add_track(Animation.TYPE_POSITION_3D)
			reset.track_set_path(t, path)
			reset.position_track_insert_key(t, 0.0, rest.origin)
			t = reset.add_track(Animation.TYPE_SCALE_3D)
			reset.track_set_path(t, path)
			reset.scale_track_insert_key(t, 0.0, rest.basis.get_scale())
	lib.add_animation("RESET", reset)
	anim.deterministic = true


## Option counts for the customize screen.
func option_count(key: String) -> int:
	return option_count_of(meta, look, key)


## The same counts from a figure's meta (figure.json) and a look, without a figure (CharacterFactory: bots' looks).
static func option_count_of(meta: Dictionary, look: Dictionary, key: String) -> int:
	match key:
		"face": return meta.get("faces", []).size()
		"eyes": return meta.get("eyes", []).size()
		"skin": return meta.get("skin_tones", []).size()
		"hair": return meta.get("hair_styles", []).size()
		"hair_color":
			var styles: Array = meta.get("hair_styles", [])
			return styles[clampi(int(look.get("hair", 0)), 0, styles.size() - 1)].colours.size() if styles.size() > 0 else 0
		"tattoo": return meta.get("tattoos", []).size()
		"size": return 3
	return 0


func play(clip: String) -> void:
	if anim and anim.has_animation(clip):
		anim.play(clip, 0.15)


func _part(part_name: String) -> MeshInstance3D:
	var list: Array = _meshes.get(part_name, [])
	return list[0] if list.size() > 0 else null


func _parts(part_name: String) -> Array:
	return _meshes.get(part_name, [])


func _blend(mi: MeshInstance3D, target: String, w: float) -> void:
	if target == "":
		return
	var i := mi.find_blend_shape_by_name(target)
	if i >= 0:
		mi.set_blend_shape_value(i, w)


func _tex(base: String) -> Texture2D:
	var key := base.to_lower()
	if _tex_cache.has(_texture_dir + key):
		return _tex_cache[_texture_dir + key]
	if not _textures.has(key):
		_textures[key] = load_texture(_texture_dir, key)
		if _textures[key] == null:
			push_warning("missing figure texture %s/%s" % [_texture_dir, key])
		_tex_cache[_texture_dir + key] = _textures[key]
	return _textures[key]


## Remastered: how an armour / clothing texture is finished - relief and metal by its kind (the texture names start
## with it: plt plate, scl scale, chn chain, std studded, lea leather, cth cloth, rob robe).
static func _finish(m: ShaderMaterial, tex: String) -> void:
	var t := tex.get_file().to_lower()
	var relief := 0.06
	var metal := 0.0
	if t.begins_with("plt") or t.contains("plate"):
		relief = 0.05
		metal = 1.0
	elif t.begins_with("scl") or t.contains("scale"):
		relief = 0.12
		metal = 0.9
	elif t.begins_with("chn") or t.contains("chain"):
		relief = 0.14
		metal = 0.85
	elif t.begins_with("std") or t.contains("studded"):
		relief = 0.1
		metal = 0.45
	elif t.begins_with("lea"):
		relief = 0.08
	m.set_shader_parameter("relief", relief)
	m.set_shader_parameter("metal", metal)


## Remastered skin (owner 2026-11-05, the character remaster "A+B"): the face lets a little light through and has a
## skin's soft sheen instead of the painted face's flat matte - kept faint, as more blurred the eyes and brows.
const SKIN_SHADING := "if (remaster_fx > 0.5) {\n\t\tSSS_STRENGTH = 0.05;\n\t\tROUGHNESS = 0.55;\n\t\tSPECULAR = 0.4;\n\t}\n\t//CUTOUT"


static func _material(cutout: bool, single_sided := false, skin := false) -> ShaderMaterial:
	var key := ("cutout" if cutout else "solid") + ("_cull" if single_sided else "") + ("_skin" if skin else "")
	if not _shaders.has(key):
		var s := Shader.new()
		var code := SHADER
		if single_sided:                                     # (cloaks: fig3parts 'Double Sided' empty - the client culls)
			code = code.replace("cull_disabled", "cull_back")
		if skin:
			code = code.replace("//CUTOUT", SKIN_SHADING)
		if cutout:
			code = code.replace("//CUTOUT", "ALPHA = c.a;\n\tALPHA_SCISSOR_THRESHOLD = 0.5;")
		s.code = code
		_shaders[key] = s
	var m := ShaderMaterial.new()
	m.shader = _shaders[key]
	return m


# Catacombs (fig3) parts, the client's way (pipeline/build_races.py):
#   tint_mode 0 none, 1 whole texture x tint (head: skin tone; hair: the colour's tint),
#   2 tint the bare skin (skins.csv Tint Chan 'a'): the skin is the part whose alpha is under 255 (the hands' and arms'
#     skin sits at 150-240, the leather / cloth around it at 255) - fully, as the head; 2026-10-11, owner: dark-skinned
#     Celts had a dark head on pale arms when the alpha itself was the tint strength
#   eye: the eye-colour texture (white except the iris, same UVs as the face) multiplies the face
#   decal: tattoo, face x lerp(1, 2 x decal, decal alpha): grey-backed Celt tattoos are neutral where unpainted,
#          alpha-masked Troll decals only touch where drawn
#   hair is the only part whose alpha is coverage (cutout); on faces alpha is gloss, on clothes the tint mask
const SHADER := """
shader_type spatial;
render_mode cull_disabled;
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D eye_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D decal_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec3 tint : source_color = vec3(1.0);
uniform int tint_mode = 0;
uniform bool has_eye = false;
uniform bool has_decal = false;
// a cloak's guild emblem (Emblems; the client's $insigniaTexture pixel shader): the pattern on the cloak's set 0 (UV2),
// the logo on its set 2 (CUSTOM0), the cloak's own texture on set 1 - pattern x cloak x 2 x logo, in the client's gamma
uniform sampler2D pattern_tex : filter_linear, repeat_enable;
uniform sampler2D logo_tex : filter_linear_mipmap, repeat_disable;
uniform bool has_emblem = false;
uniform bool has_logo = false;
// remastered (claude 2026-10-31): relief from the texture itself (as the world's stone) and metal that shines like
// metal - set per part from its armour texture (Fig3Figure._finish); hair a soft sheen
uniform float relief = 0.0;
uniform float relief_bias = 3.0;     // how coarse a mip the relief reads: higher = the broad shapes, not the grain
uniform float metal_bias = 2.0;      // the same for which parts shine as metal (0: per pixel)
uniform float metal = 0.0;
uniform float sheen = 0.0;
global uniform float remaster_fx;
// hair away from the skull (a ponytail, long hair down the back) trails behind as the figure moves (Fig3Figure.Sway):
// the further from the skull's middle the more, only the part behind the head (never forward into the face)
uniform vec3 sway_dir = vec3(0.0);
uniform vec3 sway_head = vec3(0.0);
uniform vec3 sway_back = vec3(0.0, 0.0, -1.0);
// stealth (Player hidden look): a dither instead of blending - the head, the hair and the body fade alike, with no
// sorting between the parts (owner 2026-10-31: the head and hair stayed solid or vanished as the camera moved)
uniform float fade = 1.0;
varying vec2 logo_uv;

void vertex() {
	logo_uv = CUSTOM0.xy;
	if (dot(sway_dir, sway_dir) > 1e-6) {
		vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
		float away = smoothstep(0.13, 0.42, distance(wp, sway_head));
		float behind = smoothstep(-0.03, 0.05, dot(wp - sway_head, sway_back));
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (sway_dir * away * behind);
	}
}

void fragment() {
	if (fade < 0.999) {
		vec2 px = floor(FRAGCOORD.xy);
		float ign = fract(52.9829189 * fract(dot(px, vec2(0.06711056, 0.00583715))));
		if (ign >= fade) discard;
	}
	vec4 c = texture(albedo_tex, UV);
	vec3 col = c.rgb;
	if (has_emblem) {
		vec3 g = pow(col, vec3(1.0 / 2.2)) * texture(pattern_tex, UV2).rgb * 2.0;
		if (has_logo) g *= texture(logo_tex, logo_uv).r;
		col = pow(clamp(g, 0.0, 1.0), vec3(2.2));
	}
	else if (tint_mode == 1) col *= tint;
	else if (tint_mode == 2) col *= mix(tint, vec3(1.0), smoothstep(0.90, 0.99, c.a));
	if (has_eye) col *= texture(eye_tex, UV).rgb;
	if (has_decal) {
		vec4 d = texture(decal_tex, UV);
		col *= mix(vec3(1.0), d.rgb * 2.0, d.a);
	}
	ALBEDO = col;
	ROUGHNESS = 0.85;
	SPECULAR = 0.3;
	if (remaster_fx > 0.5) {
		float lum = dot(col, vec3(0.3, 0.59, 0.11));
		if (relief > 0.0) {
			// the texture's light parts raised, its dark seams sunk: the surface gradient bump (no tangents needed)
			float lod = max(textureQueryLod(albedo_tex, UV).x, 0.0) + relief_bias;
			vec2 stp = exp2(lod) / vec2(textureSize(albedo_tex, 0));
			vec3 luma = vec3(0.3, 0.59, 0.11);
			float h0 = dot(textureLod(albedo_tex, UV, lod).rgb, luma);
			vec2 dh = vec2(dot(textureLod(albedo_tex, UV + vec2(stp.x, 0.0), lod).rgb, luma) - h0,
					dot(textureLod(albedo_tex, UV + vec2(0.0, stp.y), lod).rgb, luma) - h0) / stp;
			float dhdx = dot(dh, dFdx(UV));
			float dhdy = dot(dh, dFdy(UV));
			vec3 dpdx = dFdx(VERTEX);
			vec3 dpdy = dFdy(VERTEX);
			vec3 r1 = cross(dpdy, NORMAL);
			vec3 r2 = cross(NORMAL, dpdx);
			float det = dot(dpdx, r1);
			vec3 grad = sign(det) * (dhdx * r1 + dhdy * r2);
			NORMAL = normalize(abs(det) * NORMAL - grad * relief);
		}
		if (metal > 0.0) {
			// the metal is the grey, unsaturated, not-too-dark part of the picture (rings, plates, rivets); leather
			// straps, cloth and gold trim keep their own look
			vec3 mc = col;
			if (metal_bias > 0.0) {
				mc = textureLod(albedo_tex, UV, max(textureQueryLod(albedo_tex, UV).x, 0.0) + metal_bias).rgb;
				if (tint_mode == 1) mc *= tint;
			}
			float mx = max(mc.r, max(mc.g, mc.b));
			float mn = min(mc.r, min(mc.g, mc.b));
			float sat = (mx - mn) / max(mx, 0.001);
			float m = metal * (1.0 - smoothstep(0.1, 0.28, sat)) * smoothstep(0.1, 0.3, dot(mc, vec3(0.3, 0.59, 0.11)));
			METALLIC = m * 0.6;
			ROUGHNESS = mix(0.85, 0.42, m);
			SPECULAR = mix(0.3, 0.5, m);
			ALBEDO = col * (1.0 + 0.25 * m);              // (metal's colour is its reflection: a little lighter base)
		}
		if (sheen > 0.0) {                                // hair: a soft sheen, not a doll's gloss
			ROUGHNESS = mix(ROUGHNESS, 0.68, sheen);
			SPECULAR = mix(SPECULAR, 0.34, sheen);
		}
	}
	//CUTOUT
}
"""


# ---------------------------------------------------------------- cloak and hair sway (claude 2026-10-31)
## Remastered: the cloak and a ponytail trail behind as the figure moves and stir in the wind, on top of what the
## animation does (owner 2026-10-31: "keep in mind clipping"). They only ever swing back, away from the body, and a
## little to the side - never forward into the legs; backing up or standing still they hang as animated. Springs, so
## they settle after a stop. Figures beyond SWAY_RANGE_M are left alone.
static var sway_on := false                  # SkySystem: remastered
var back_gear := false                        # something rides on the back (Player.dress): the cloak hangs as animated
var _hair_mat: ShaderMaterial                # the hair's material (its sway uniforms)
static var wind := 1.0                       # SkySystem: the storm's wind (as the trees')
const SWAY_RANGE_M := 35.0


class Sway extends SkeletonModifier3D:
	var model: Node3D
	var fig: Fig3Figure
	var _neck := -1                              # the head bone (the hair's sway is measured from the skull)
	var _hair_live := false
	var _cloaks: Array[int] = []
	var _cloaks_mid: Array[int] = []
	var _tails: Array[int] = []
	var _last := Vector3.INF
	var _back := 0.0
	var _back_v := 0.0
	var _side := 0.0
	var _side_v := 0.0
	var _phase := 0.0
	var _ready_bones := false

	func _bones(sk: Skeleton3D) -> void:
		_ready_bones = true
		for side in ["C", "L", "R"]:
			var b := sk.find_bone("Bip01 %s Cloak01" % side)
			if b >= 0:
				_cloaks.append(b)
			var mid := sk.find_bone("Bip01 %s Cloak03" % side)
			if mid >= 0:
				_cloaks_mid.append(mid)
		_neck = sk.find_bone("Bip01 Head")
		var t := sk.find_bone("Bip01 Ponytail1")
		if t >= 0:
			_tails.append(t)
		_phase = float(get_instance_id() % 997) * 0.37

	func _process_modification_with_delta(delta: float) -> void:
		var sk := get_skeleton()
		if sk == null or not Fig3Figure.sway_on or model == null:
			_last = Vector3.INF
			_still_hair()
			return
		if not _ready_bones:
			_bones(sk)
		var pos := sk.global_position
		var cam := get_viewport().get_camera_3d() if is_inside_tree() else null
		if cam and cam.global_position.distance_to(pos) > SWAY_RANGE_M:
			_last = Vector3.INF
			_still_hair()
			return
		var dt := maxf(delta, 0.001)
		var vel := Vector3.ZERO if _last == Vector3.INF else (pos - _last) / dt
		_last = pos
		if vel.length() > 25.0:
			vel = Vector3.ZERO                                 # (a teleport, a zone change)
		# the model faces +Z in its own space (as the converted figures do); in the skeleton's space:
		var to_skel := sk.global_basis.orthonormalized().inverse() * model.global_basis.orthonormalized()
		var fwd := (to_skel * Vector3(0, 0, 1)).normalized()
		var up := (to_skel * Vector3.UP).normalized()
		var right := up.cross(fwd).normalized()
		var v := model.global_basis.orthonormalized().inverse() * vel
		var t := Time.get_ticks_msec() / 1000.0
		var breeze := Fig3Figure.wind * (0.03 + 0.025 * sin(t * 1.3 + _phase) + 0.015 * sin(t * 3.1 + _phase * 2.0))
		var want_back := clampf(v.z * 0.05, 0.0, 0.35) + maxf(breeze, 0.0)
		var want_side := clampf(-v.x * 0.03, -0.15, 0.15) + Fig3Figure.wind * 0.02 * sin(t * 0.9 + _phase)
		# springs (a little under-damped: one soft overshoot as it settles)
		_back_v += ((want_back - _back) * 40.0 - _back_v * 9.0) * dt
		_back += _back_v * dt
		_side_v += ((want_side - _side) * 30.0 - _side_v * 8.0) * dt
		_side += _side_v * dt
		var back := clampf(_back, 0.0, 0.45)                   # never forward, into the legs
		var side_ang := clampf(_side, -0.2, 0.2)
		var axis_back := up.cross(fwd).normalized()           # + swings the lower end back (away from the body)
		# a shield, a two-hander, a slung bow or a quiver on the back: the cloak hangs as the animation has it (owner
		# 2026-11-03: they clipped through the swinging cloak); it swings again once the back is clear
		if fig == null or not fig.back_gear:
			for b in _cloaks:
				_turn(sk, b, axis_back, back, fwd, side_ang)
			for b in _cloaks_mid:
				_turn(sk, b, axis_back, back * 0.35, fwd, side_ang * 0.5)
		for b in _tails:
			_turn(sk, b, axis_back, back * 0.8, fwd, side_ang * 1.2)
		# long hair (the Catacombs hair is rigid on the head: its lower part bent in the shader)
		var hm: ShaderMaterial = fig._hair_mat if fig else null
		if hm and _neck >= 0:
			var back_w := -(model.global_basis * Vector3(0, 0, 1)).normalized()
			var side_w := (model.global_basis * Vector3(1, 0, 0)).normalized()
			var up_w := (model.global_basis * Vector3.UP).normalized()
			var hb := sk.get_bone_global_pose(_neck)
			# the skull's middle: a little above the head bone (which sits at the top of the neck)
			var head_w := sk.global_transform * (hb.origin + (to_skel * Vector3.UP).normalized() * 0.1 / maxf(sk.global_basis.get_scale().y, 0.01))
			var speed := Vector2(v.x, v.z).length()
			# running: the hair swings back and bounces / swishes with the stride (owner 2026-10-31: too subtle)
			var bob := sin(t * 10.0 + _phase) * minf(speed, 8.0) * 0.006
			var swish := sin(t * 5.0 + _phase) * minf(speed, 8.0) * 0.008
			hm.set_shader_parameter("sway_head", head_w)
			hm.set_shader_parameter("sway_back", back_w)
			hm.set_shader_parameter("sway_dir", back_w * (sin(back) * 0.75 + absf(bob)) + side_w * (sin(side_ang) * 0.6 + swish)
					+ up_w * bob)
			_hair_live = true

	func _still_hair() -> void:
		if _hair_live and fig and fig._hair_mat:
			fig._hair_mat.set_shader_parameter("sway_dir", Vector3.ZERO)
		_hair_live = false

	func _turn(sk: Skeleton3D, b: int, axis_back: Vector3, back: float, axis_side: Vector3, side: float) -> void:
		var g := sk.get_bone_global_pose(b)
		var p := sk.get_bone_parent(b)
		var pg := sk.get_bone_global_pose(p) if p >= 0 else Transform3D.IDENTITY
		var turn := Basis(axis_back, back) * Basis(axis_side, side)
		var ng := Transform3D(turn * g.basis, g.origin)
		var local := pg.affine_inverse() * ng
		sk.set_bone_pose_rotation(b, local.basis.get_rotation_quaternion())


# ---------------------------------------------------------------- run / walk pace (claude 2026-10-31)
## How fast this figure moves when its run or walk clip plays at normal speed, measured from the clip itself: how far
## the feet sweep forward and back (owner 2026-10-31: "the running animation speed feels off compared to how fast
## they're moving ... especially female characters"). The client's own figures (monnifs.csv strides) said the
## women's run covered 5.9 m a cycle to the men's 4.5 m - the women's legs ran in slow motion. Measured, both clips
## sweep the feet about as far (0.76 / 0.78 m), the women's cycle is quicker (0.8 s to 1.0 s). Playing the clip at
## speed / natural_speed keeps the legs with the ground for every race and sex alike.
## Calibrated so a man's run plays 1.4x at the base run speed (191 units/s) - a runner's cadence, the feet slipping
## a little less than the old client's; walking has no flight, its feet sweep the ground's distance.
const RUN_PACE_K := 4.37
const WALK_PACE_K := 2.0
var race := ""
static var _paces := {}                      # race prefix -> {run: m/s, walk: m/s} at scale 1


func natural_speed(clip: String) -> float:
	if not _paces.has(race):
		_paces[race] = _measure_paces()
	return float((_paces[race] as Dictionary).get(clip, 0.0)) * scale.x


func _measure_paces() -> Dictionary:
	var out := {}
	if anim == null or model == null:
		return out
	var sks := model.find_children("*", "Skeleton3D", true, false)
	if sks.is_empty():
		return out
	var sk: Skeleton3D = sks[0]
	var feet := [sk.find_bone("Bip01 L Foot"), sk.find_bone("Bip01 R Foot")]
	if feet[0] < 0 or feet[1] < 0:
		return out
	var was := anim.current_animation
	var was_at := anim.current_animation_position if was != "" else 0.0
	if not sk.is_inside_tree():
		return out
	var to_model := model.global_transform.affine_inverse() * sk.global_transform   # (skeleton space into the model's own)
	for clip in ["run", "walk"]:
		if not anim.has_animation(clip):
			continue
		var length := anim.get_animation(clip).length
		anim.play(clip)
		var lo := [INF, INF]
		var hi := [-INF, -INF]
		for i in 40:
			anim.seek(length * float(i) / 40.0, true)
			sk.force_update_all_bone_transforms()
			for k in 2:
				var z: float = (to_model * sk.get_bone_global_pose(feet[k]).origin).z
				lo[k] = minf(lo[k], z)
				hi[k] = maxf(hi[k], z)
		var sweep: float = ((hi[0] - lo[0]) + (hi[1] - lo[1])) * 0.5
		if length > 0.0 and sweep > 0.05:
			out[clip] = sweep * (RUN_PACE_K if clip == "run" else WALK_PACE_K) / length
	if was != "":
		anim.play(was)
		anim.seek(was_at, true)
	return out
