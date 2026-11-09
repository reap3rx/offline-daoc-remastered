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
static var _flow_cache := {}                # hair flow maps (hair_flow), by texture


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
	var styles: Array = meta.get("hair_styles", [])               # (a style disabled for the race - hair tuning -
	var pre := String(meta.get("prefix", ""))                      # gives way to one that isn't)
	if styles.size() > 0 and part_disabled(pre, "hair", styles[clampi(int(look.hair), 0, styles.size() - 1)]):
		var hair_ok := offered_of(meta, pre, "hair")
		if not hair_ok.is_empty():
			look["hair"] = hair_ok[absi(h / 13) % hair_ok.size()]
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
	add_body_bones(model)                           # (before it enters the tree: its skins bind to them)
	add_child(model)
	for node in model.find_children("*", "MeshInstance3D", true, false):
		var part := String(node.name).get_slice("__", 0)    # a part's extra shapes are named <part>__1, __2 ...
		if not _meshes.has(part):
			_meshes[part] = []
		_meshes[part].append(node)
	var players := model.find_children("*", "AnimationPlayer", true, false)
	var skels := model.find_children("*", "Skeleton3D", true, false)
	if players.size() > 0:
		anim = players[0]
		for clip in anim.get_animation_list():
			var a := anim.get_animation(clip)
			a.loop_mode = Animation.LOOP_LINEAR if loops(clip) else Animation.LOOP_NONE
			if (loops(clip) or AnimStyle.group_of(clip) != "") and not a.has_meta("smooth"):
				_use_smooth(prefix, clip, a, skels[0] if skels.size() > 0 else null)
		if skels.size() > 0:
			_add_transitions(prefix, skels[0])
		add_rest_reset(anim)
		if anim.has_animation("idle"):
			anim.play("idle")
	if skels.size() > 0:
		var layers := Layers.new()                  # (first of all: the legs' clip under an action, then the shape)
		layers.name = "Layers"
		layers.fig = self
		(skels[0] as Skeleton3D).add_child(layers)
		var body := BodyShape.new()                 # (first: the sway works on the shaped body)
		body.name = "BodyShape"
		body.fig = self
		(skels[0] as Skeleton3D).add_child(body)
		var sway := Sway.new()
		sway.name = "Sway"
		sway.model = model
		sway.fig = self
		(skels[0] as Skeleton3D).add_child(sway)
	apply({})
	_apply_cloak()
	return true


## The converted clips keep the client's keys - 15 a second - joined with straight lines: a bone's speed changes in a
## step at every key (owner 2026-11-05: "a weird jitteriness ... in male's animations"). The looping clips, and the
## others AnimStyle has a group for, are rebuilt through AnimStyle: curves between the keys, the limbs' overlap, a
## steadier head (owner 2026-11-09: "modernize the feel"). The swings keep their snap for now. Once per race and clip
## (static): every figure of the race shares the result.
const AnimStyle := preload("res://game/anim_style.gd")
static var _smooth_cache := {}               # "prefix/clip" -> Animation
static var _smooth_lock := Mutex.new()       # (figures are loaded on worker threads too)


func _use_smooth(prefix: String, clip: String, a: Animation, sk: Skeleton3D) -> void:
	var key := prefix + "/" + clip
	_smooth_lock.lock()
	if not _smooth_cache.has(key):
		_smooth_cache[key] = AnimStyle.build(a, clip, sk)
	var b: Animation = _smooth_cache[key]
	_smooth_lock.unlock()
	var lib_name := anim.find_animation_library(a)
	var lib := anim.get_animation_library(lib_name)
	var raw := clip.get_slice("/", 1) if clip.contains("/") else clip
	if lib and lib.has_animation(raw):
		lib.remove_animation(raw)
		lib.add_animation(raw, b)


# ---------------------------------------------------------------- transitions (claude 2026-11-09, animation step 6)
## A stop from a run or a walk plays a short clip built from the stride itself (AnimStyle.stop_clip): from the moment the
## next foot plants, easing into the idle - instead of the idle cutting in at whatever point of the stride. A start
## begins the run at its passing pose (the feet together under the body - the nearest to standing). Remastered only
## (stop_clip_for / start_phase answer nothing in Classic). Per race, once (static, as the smoothing).
static var _gaits := {}                      # "prefix/clip" -> AnimStyle.gait


func _add_transitions(prefix: String, sk: Skeleton3D) -> void:
	if not anim.has_animation("idle"):
		return
	for mv: String in ["run", "walk"]:
		if not anim.has_animation(mv):
			continue
		var move := anim.get_animation(mv)
		var lib := anim.get_animation_library(anim.find_animation_library(move))
		var key := prefix + "/" + mv
		_smooth_lock.lock()
		if not _gaits.has(key):
			_gaits[key] = AnimStyle.gait(move, sk)
		var g: Dictionary = _gaits[key]
		_smooth_lock.unlock()
		for foot in ["l", "r"]:
			_stop_clip(prefix, mv, foot, "idle")


## The stop from `move` as `foot` plants, into the stance `into` (the idle, or a combat guard - owner 2026-11-09: a
## stop into the plain idle then snapped to the drawn weapon's guard): built the first time it's wanted, per race.
func _stop_clip(prefix: String, mv: String, foot: String, into: String) -> String:
	var name := "%s_stop_%s" % [mv, foot] + ("" if into == "idle" else "__" + into)
	if anim.has_animation(name):
		return name
	var g: Dictionary = _gaits.get(prefix + "/" + mv, {})
	if not g.has("plant_" + foot) or not anim.has_animation(mv) or not anim.has_animation(into):
		return ""
	var move := anim.get_animation(mv)
	var lib := anim.get_animation_library(anim.find_animation_library(move))
	var ck := prefix + "/" + name
	_smooth_lock.lock()
	if not _smooth_cache.has(ck):
		# the trailing leg's passing pose: the first of the stride's two passings after the plant
		var at := float(g["plant_" + foot])
		var pass_t := -1.0
		if g.has("pass"):
			var half := move.length * 0.5
			var p1 := fposmod(float(g["pass"]), move.length)
			var p2 := fposmod(p1 + half, move.length)
			pass_t = p1 if fposmod(p1 - at, move.length) < fposmod(p2 - at, move.length) else p2
		_smooth_cache[ck] = AnimStyle.stop_clip(move, anim.get_animation(into), at, float(AnimStyle.STOP_SECONDS[mv]),
				foot.to_upper(), pass_t)
	if lib and not lib.has_animation(name):
		lib.add_animation(name, _smooth_cache[ck])
	_smooth_lock.unlock()
	return name if anim.has_animation(name) else ""


static func idle_like(clip: String) -> bool:
	return clip == "idle" or clip.begins_with("combat_idle")


static func is_stop_clip(clip: String) -> bool:
	return clip.contains("_stop_")


## The stop to play when `move` (run / walk), now at `at`, ends into `into` - for the foot that plants next; "" none.
func stop_clip_for(move: String, at: float, into := "idle") -> String:
	if not sway_on or anim == null or not anim.has_animation(move):
		return ""
	var g: Dictionary = _gaits.get(race + "/" + move, {})
	if not g.has("plant_l") or not g.has("plant_r"):
		return ""
	var length := anim.get_animation(move).length
	var foot := "l" if fposmod(float(g.plant_l) - at, length) < fposmod(float(g.plant_r) - at, length) else "r"
	return _stop_clip(race, move, foot, into)


## Where a start begins `move` (its passing pose); -1: from the start as before.
func start_phase(move: String) -> float:
	if not sway_on:
		return -1.0
	var g: Dictionary = _gaits.get(race + "/" + move, {})
	return float(g.get("pass", -1.0))


## Merge `changes` into the current look and redraw.
func apply(changes: Dictionary) -> void:
	look.merge(changes, true)
	for k in changes:                                  # (null: back to the default - a custom colour dropped)
		if changes[k] == null:
			look.erase(k)
	var skin := _skin()
	var tint_parts: Dictionary = meta.get("skin_tint_parts", {})
	# head: face texture x skin tone, eye colour multiplied, tattoo
	var faces: Array = meta.get("faces", [])
	var head := _part("head")
	if head and faces.size() > 0:
		var m := _material(false, false, skin_shading)
		var base: Texture2D = _base_face() if is_layered() else null
		m.set_shader_parameter("albedo_tex", base if base else _tex(faces[clampi(int(look.get("face", 0)), 0, faces.size() - 1)].tex))
		m.set_shader_parameter("tint", skin)
		m.set_shader_parameter("tint_mode", 1)
		var eyes: Array = meta.get("eyes", [])
		if eyes.size() > 0:
			m.set_shader_parameter("eye_tex", _tex(eyes[clampi(int(look.get("eyes", 0)), 0, eyes.size() - 1)]))
			m.set_shader_parameter("has_eye", true)
			var er = custom_colour("eyes")                 # (the creator's colour wheel: any iris colour)
			m.set_shader_parameter("eye_tint", Color(pow(er.r, 2.2), pow(er.g, 2.2), pow(er.b, 2.2), 1.0) if er != null else Color(0, 0, 0, 0))
		var tattoos: Array = meta.get("tattoos", [])
		var ti := int(look.get("tattoo", 0))
		var decal: String = tattoos[ti].tex if ti > 0 and ti < tattoos.size() else ""
		m.set_shader_parameter("has_decal", decal != "")
		if decal != "":
			m.set_shader_parameter("decal_tex", _tex(decal))
		_layers(m)
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
			mi.visible = i == si and not _hair_covered() and not _under_helm(styles[i])
		_jewels(styles[i], i == si and not _hair_covered() and not _under_helm(styles[i]))
		if i == si:
			var colours: Array = styles[i].colours
			if colours.size() > 0:
				var col := hair_colour(colours)
				var m := _hair_material(col)
				_hair_mat = m
				for mi in _parts(node):
					mi.material_override = m
	# the scalp cap under the hair, if worn (figure.json hair_under, pipeline/import_hair.py): in the hair's colour
	_hair_under()
	_apply_hair_fit()
	# the turban over the hair: its cloth from the original texture (the remastered one drew strands into it), dyed
	var tb: Array = meta.get("turbans", [])
	var ti := turban_index()
	for k in tb.size():
		var tn := String(tb[k].node)
		if not _meshes.has(tn):
			continue
		for mi in _parts(tn):
			mi.visible = k + 1 == ti and not _hair_covered()
		if k + 1 == ti:
			var want = custom_colour("turban_color")
			if want == null:
				want = TURBAN_COLORS[clampi(int(look.get("turban_color", 0)), 0, TURBAN_COLORS.size() - 1)]
			var tm := _material(false)
			tm.set_shader_parameter("albedo_tex", load_texture(texture_dir("original"), String(tb[k].tex).to_lower()))
			tm.set_shader_parameter("tint", Color(want.r * 1.2, want.g * 1.2, want.b * 1.2))
			tm.set_shader_parameter("tint_mode", 1)
			tm.set_shader_parameter("relief", 0.1)
			for mi in _parts(tn):
				mi.material_override = tm
	# the beard (men: split off the hair styles by pipeline/split_beards.py): its own style's texture in the hair's
	# colour (the same colour index - the styles list their colours alike)
	var beards: Array = meta.get("beards", [])
	var bi := beard_index()
	for k in beards.size():
		var bnode := String(beards[k].node)
		if not _meshes.has(bnode):
			continue
		for mi in _parts(bnode):
			mi.visible = k + 1 == bi and not _hair_covered()
		_jewels(beards[k], k + 1 == bi and not _hair_covered())
		if k + 1 == bi:
			var bst: Dictionary = styles[clampi(int(beards[k].style), 0, styles.size() - 1)]
			var bcols: Array = beards[k].colours if (beards[k] as Dictionary).has("colours") else bst.colours
			if bcols.size() > 0:
				var bm := _hair_material(hair_colour(bcols) if custom_colour("hair_color") != null else bcols[_beard_colour(styles, bcols)])
				for mi in _parts(bnode):
					mi.material_override = bm
	# the moustache (owner 2026-11-06: "a beard and moustache subfolder" - pipeline/import_hair.py) and the sideburns
	# ("meant to be used in conjunction with other beards"): look.moustache / look.sideburns, 1-based into figure.json
	# "moustaches" / "sideburns", 0 none; coloured as the beard is
	for kind in FACE_HAIR:
		var list: Array = meta.get(String(kind[1]), [])
		var worn := clampi(int(look.get(String(kind[0]), 0)), 0, list.size())
		for k in list.size():
			var mn := String(list[k].node)
			if not _meshes.has(mn):
				continue
			for mi in _parts(mn):
				mi.visible = k + 1 == worn and not _hair_covered()
			_jewels(list[k], k + 1 == worn and not _hair_covered())
			if k + 1 == worn and (list[k].colours as Array).size() > 0:
				var mcols: Array = list[k].colours
				var mm := _hair_material(hair_colour(mcols) if custom_colour("hair_color") != null else mcols[_beard_colour(styles, mcols)])
				for mi in _parts(mn):
					mi.material_override = mm
	if not (meta.get("turbans", []) as Array).is_empty():
		_refresh_hair()                                # (the hair under the turban takes its cap morph)
	# face sliders: 0..8, 4 neutral; below 4 blends the low target, above 4 the high one
	if head:
		var values: Array = look.get("sliders", [])
		var sliders: Array = meta.get("sliders", [])
		for i in sliders.size():
			var v := float(values[i]) if i < values.size() else 4.0
			_blend(head, String(sliders[i].low), clampf((4.0 - v) / 4.0, 0.0, 1.0))
			_blend(head, String(sliders[i].high), clampf((v - 4.0) / 4.0, 0.0, 1.0))
	# face shapes (owner 2026-11-06, the creator's sliders): look.shape {name: -1..1} on the fx_<name> targets of the
	# head and of every hair style (pipeline/face_morphs.py gave the beards the same moves, so they stay on the face)
	_apply_shape()
	# size: the race's Catacombs scale x Short 0.95 / Average 1.0 / Tall 1.05
	var sizes := [0.95, 1.0, 1.05]
	scale = Vector3.ONE * float(meta.get("scale", 1.0)) * float(sizes[clampi(int(look.get("size", 1)), 0, 2)]) \
			* (1.0 + 0.07 * clampf(float((look.get("body", {}) as Dictionary).get("height", 0.0)), -1.0, 1.0))
	_apply_armor()                                         # worn armour over the starter clothes; hides unused variants


# --- the skin layers (the creator's SKIN page; pipeline/skin_layers.py bakes the masks) ---------------------------
## War paint and lip colours (sRGB): the swatches the SKIN page offers, by index (look paint_color / lip_color - lip 0
## is the face's own).
const PAINT_COLORS := [Color(0.13, 0.24, 0.62), Color(0.06, 0.06, 0.07), Color(0.62, 0.12, 0.08), Color(0.9, 0.88, 0.82),
	Color(0.16, 0.42, 0.18), Color(0.78, 0.6, 0.18), Color(0.4, 0.16, 0.5), Color(0.42, 0.4, 0.38)]
const LIP_COLORS := [Color(0, 0, 0), Color(0.62, 0.22, 0.26), Color(0.48, 0.06, 0.1), Color(0.42, 0.1, 0.28),
	Color(0.3, 0.1, 0.22), Color(0.78, 0.36, 0.3), Color(0.45, 0.3, 0.26), Color(0.08, 0.06, 0.07), Color(0.2, 0.26, 0.45)]
## Scar colours (owner 2026-11-06: "too bright"): healed pale, faint pink, fresh red, dark, silvered.
const SCAR_COLORS := [Color(0.8, 0.62, 0.56), Color(0.86, 0.58, 0.56), Color(0.66, 0.3, 0.28), Color(0.42, 0.3, 0.26),
	Color(0.84, 0.8, 0.78)]
## Headwear that came through as hair styles (owner 2026-11-06, the Saracens: "some hairstyles that are hoods or
## turbans"): pipeline/split_headwear.py cut the turbans' cloth from their styles (figure.json "turbans"; each style's
## own "turban", and "hood" on the hood styles). The hoods leave the creator; a turban is worn over any hair style
## (look turban: 0 none, k = turbans[k-1]; unset: the style's own, as before), dyed (turban_color), and a style of
## its own hair under it takes the helm morph of a close cap (helm hair type TURBAN_HAIR).
const TURBAN_HAIR := 2
## The creator's hair sliders (owner 2026-11-06: "hair sliders so that way players ... can also try to get the hair
## placement, size, and length correct"): the hf_ morph targets pipeline/import_hair.py puts on every style, kept per
## style in look.hair_fit {style node: {key: -1..1}}.
## (Then: "A left/right slider ... one that kind of bends the sides backward ... size height, and size width ... the
## width from back to front" - and wider, to fit each style by hand.)
const HAIR_FIT := [["lr", "Left / Right"], ["up", "Up / Down"], ["fwd", "Forward / Back"], ["size", "Size"],
	["height", "Height"], ["width", "Width"], ["depth", "Depth"], ["wrap", "Wrap"], ["len", "Length"]]
## The face hair worn beside a beard: [look key, figure.json list, the creator's label].
const FACE_HAIR := [["moustache", "moustaches", "Moustache"], ["sideburns", "sideburns", "Sideburns"]]
const TURBAN_COLORS := [Color(0.92, 0.9, 0.84), Color(0.2, 0.18, 0.16), Color(0.55, 0.12, 0.1), Color(0.16, 0.24, 0.5),
	Color(0.18, 0.36, 0.2), Color(0.72, 0.56, 0.24), Color(0.42, 0.3, 0.2), Color(0.4, 0.16, 0.42)]


## The worn turban: 1-based into figure.json "turbans", 0 none.
func turban_index() -> int:
	var tb: Array = meta.get("turbans", [])
	if tb.is_empty():
		return 0
	if look.has("turban"):
		return clampi(int(look.turban), 0, tb.size())
	var styles: Array = meta.get("hair_styles", [])
	if styles.is_empty():
		return 0
	return int(styles[clampi(int(look.get("hair", 0)), 0, styles.size() - 1)].get("turban", 0))


## The hair styles the creator offers: never the hoods; the hair that sat under a turban only with a turban on.
func creator_styles() -> Array:
	var out := []
	var styles: Array = meta.get("hair_styles", [])
	var on := turban_index() > 0
	for i in styles.size():
		if bool(styles[i].get("hood", false)):
			continue
		if int(styles[i].get("turban", 0)) > 0 and not on:
			continue
		if part_hidden(race, "hair", styles[i], tuning_on()):
			continue
		out.append(i)
	return out


## Freckle colours (owner 2026-11-06: "natural freckle colors that might work with other skin tones") - each
## multiplies the skin: tan, brown, dark brown, red-brown, deep, faint.
const FRECKLE_COLORS := [Color(0.66, 0.5, 0.4), Color(0.55, 0.38, 0.28), Color(0.42, 0.28, 0.2), Color(0.7, 0.42, 0.32),
	Color(0.3, 0.22, 0.18), Color(0.8, 0.68, 0.58)]
## Brow colours (look brow_color; 0 = the hair's): black, dark brown, brown, auburn, blonde, grey, white, red.
const BROW_COLORS := [Color(0.06, 0.05, 0.05), Color(0.16, 0.1, 0.07), Color(0.3, 0.2, 0.12), Color(0.4, 0.18, 0.1),
	Color(0.62, 0.5, 0.3), Color(0.45, 0.43, 0.42), Color(0.82, 0.8, 0.76), Color(0.55, 0.22, 0.1)]
## War paint placement (owner 2026-11-06: "up, down, scale, and rotation ... clamped to not go off of the face"):
## look paint_y (eye spacings), paint_size, paint_turn (degrees) within these.
const PAINT_Y := Vector2(-0.45, 0.45)
const PAINT_SIZE := Vector2(0.7, 1.35)
const PAINT_TURN := Vector2(-30.0, 30.0)
static var _layer_tex := {}                     # path -> the mask texture (shared by every figure of the race)


## Whether the look is built from the race's parts (the base face, brows, age, beard as layers - the creator since
## 2026-11-06) rather than one of the original face textures (old characters, NPCs).
func is_layered() -> bool:
	return bool(look.get("v2", false)) and String((meta.get("skin_layers", {}) as Dictionary).get("base", "")) != ""


## The scalp cap (owner 2026-11-06: "put on UNDER the hair every time ... the player can decide if they like it on or
## off with each hair style"): the race's one cap (figure.json hair_under), worn under any style - bald too - when the
## look has scalp_cap on, in the hair colour chosen. Not under a helm that flattens hair (it has no helm morphs).
func _hair_under() -> void:
	var hu: Dictionary = meta.get("hair_under", {})
	if hu.is_empty() or not _meshes.has(String(hu.node)):
		return
	var on := scalp_cap_on() and not _hair_covered() and not (_helm != null and _helm_hair >= 2)
	for mi in _parts(String(hu.node)):
		mi.visible = on
	var cols: Array = hu.get("colours", [])
	if on and cols.size() > 0:
		var m := _hair_material(hair_colour(cols))
		m.set_shader_parameter("fuzz", 0.0)            # (skin-tight: no strands broken off its outline)
		for mi in _parts(String(hu.node)):
			mi.material_override = m


## A style's hair-slider values: the look's own (look.hair_fit, by style node), else the fit tuned for this race
## (hair tuning, below), else none.
func hair_fit_of(node: String) -> Dictionary:
	var own: Dictionary = look.get("hair_fit", {})
	var entry := part_entry(node)
	var out: Dictionary = {}
	if not entry.is_empty():
		out = (tuning_part(race, part_key(String(entry.get("_kind", "hair")), entry)).get("fit", {}) as Dictionary).duplicate()
	if own.has(node):                              # (the look's own over the tuned: a locked style's Length on its fit)
		out.merge(own[node], true)
	return out


## Every part with fit sliders: hair styles, beards, moustaches, sideburns (each entry tagged with its kind).
func fit_parts() -> Array:
	var out := []
	for kind in [["hair", "hair_styles"], ["beard", "beards"], ["moustache", "moustaches"], ["sideburns", "sideburns"]]:
		for st in meta.get(String(kind[1]), []):
			if st.node != null and bool(st.get("fit", false)):
				var e: Dictionary = st.duplicate()
				e["_kind"] = kind[0]
				out.append(e)
	return out


func part_entry(node: String) -> Dictionary:
	for e in fit_parts():
		if String(e.node) == node:
			return e
	return {}


func _apply_hair_fit() -> void:
	for st in fit_parts():
		if not _meshes.has(String(st.node)):
			continue
		var fit := hair_fit_of(String(st.node))
		var nodes := [String(st.node)]
		if st.has("jewels"):
			nodes.append(String(st.jewels.node))
		for nd in nodes:
			for mi in _parts(nd):
				for f in HAIR_FIT:
					_blend(mi, "hf_" + String(f[0]), clampf(float(fit.get(String(f[0]), 0.0)), -1.0, 1.0))


## A part's rings (a dwarf beard's braids, owner 2026-11-06: "missing the models for the rings"): drawn from their own
## texture, untinted, shown with the part.
func _jewels(entry: Dictionary, on: bool) -> void:
	if not entry.has("jewels") or not _meshes.has(String(entry.jewels.node)):
		return
	for mi in _parts(String(entry.jewels.node)):
		mi.visible = on
	if on:
		var m := _material(true)                      # (cut at half: a band's shape in its alpha)
		m.set_shader_parameter("albedo_tex", _tex(String(entry.jewels.tex)))
		m.set_shader_parameter("tint", Color.WHITE)
		m.set_shader_parameter("tint_mode", 0)
		for mi in _parts(String(entry.jewels.node)):
			mi.material_override = m


# --- hair tuning (owner 2026-11-06: "enable all hairstyles ... have a tick box ... Disable for <race> ... put a
# (completed on <date>) somewhere in that UI"): on the owner's machine only - the folder beside the pipeline exists
# - the creator saves each part's fit per race, or disables it for that race, in hair_tuning/<race>.json:
#   {"race": "lur_m", "parts": {"<kind>:<model or node>": {"fit": {..}, "disabled": bool, "done": "2026-11-07"}}}
# The saved fit is every figure's default for that part (players' own sliders over it); a disabled part is left
# out of the creator and of bots' and NPCs' looks. pipeline/import_hair.py later bakes the fits in.
static var _tuning := {}                    # race -> its tuning file, read once


static func tuning_dir() -> String:
	return ProjectSettings.globalize_path("res://").path_join("../../source/new-client/pipeline/hair_tuning").simplify_path()


static func tuning_on() -> bool:
	return DirAccess.dir_exists_absolute(tuning_dir())


static func tuning(race_: String) -> Dictionary:
	if not _tuning.has(race_):
		var path := tuning_dir().path_join(race_ + ".json")
		var d = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
		_tuning[race_] = d if d is Dictionary else {"race": race_, "parts": {}}
	return _tuning[race_]


static func part_key(kind: String, entry: Dictionary) -> String:
	var m: Variant = entry.get("model", "")                # (either may be null: a bald style has no node)
	var n: Variant = entry.get("node", "")
	return "%s:%s" % [kind, str(m) if m != null and str(m) != "" else (str(n) if n != null else "")]


static func tuning_part(race_: String, key: String) -> Dictionary:
	return (tuning(race_).get("parts", {}) as Dictionary).get(key, {})


static func save_tuning_part(race_: String, key: String, part: Dictionary) -> void:
	var t := tuning(race_)
	var parts: Dictionary = t.get("parts", {})
	parts[key] = part
	t["parts"] = parts
	DirAccess.make_dir_recursive_absolute(tuning_dir())
	var f := FileAccess.open(tuning_dir().path_join(race_ + ".json"), FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(t, " ", true))
		f.close()


static func part_disabled(race_: String, kind: String, entry: Dictionary) -> bool:
	return bool(tuning_part(race_, part_key(kind, entry)).get("disabled", false))


## A part the owner has finished for the race (owner 2026-11-08: "disable the sliders/tool for every one that I've
## completed ... Except for the length slider"): its fit fixed, only Length offered; a finished disabled part gone
## from the creator even while tuning.
static func part_locked(race_: String, kind: String, entry: Dictionary) -> bool:
	return tuning_part(race_, part_key(kind, entry)).has("done")


static func part_hidden(race_: String, kind: String, entry: Dictionary, tuning_view: bool) -> bool:
	return part_disabled(race_, kind, entry) and (not tuning_view or part_locked(race_, kind, entry))


## The choices of one kind a look may take (1-based for beards / moustaches / sideburns, 0 = none always offered;
## 0-based hair style indices): all but those disabled for the race - all of them while tuning (shown, marked).
static func offered_of(meta_: Dictionary, race_: String, kind: String, tuning_view := false) -> Array:
	var lists := {"beard": "beards", "moustache": "moustaches", "sideburns": "sideburns", "hair": "hair_styles"}
	var list: Array = meta_.get(String(lists[kind]), [])
	var out := [] if kind == "hair" else [0]
	for i in list.size():
		if kind == "hair" and (bool(list[i].get("hood", false)) or int(list[i].get("turban", 0)) > 0):
			continue
		if not part_hidden(race_, kind, list[i], tuning_view):
			out.append(i if kind == "hair" else i + 1)
	return out


func offered(kind: String) -> Array:
	return offered_of(meta, race, kind, tuning_on())


func scalp_cap_on() -> bool:
	return int(look.get("scalp_cap", 0)) == 1 and not (meta.get("hair_under", {}) as Dictionary).is_empty()


## A hair style made from a model of our own (pipeline/import_hair.py) has no helm morphs to flatten it under a
## helm: under one that would flatten hair it is not drawn.
func _under_helm(style: Dictionary) -> bool:
	return bool(style.get("imported", false)) and _helm != null and _helm_hair >= 2


## The worn beard: 1-based into figure.json "beards", 0 none. A look that never chose one wears its hair style's own
## (the beard the original mesh had).
func beard_index() -> int:
	var beards: Array = meta.get("beards", [])
	if beards.is_empty():
		return 0
	if look.has("beard"):
		return clampi(int(look.beard), 0, beards.size())
	var styles: Array = meta.get("hair_styles", [])
	if styles.is_empty():
		return 0
	return int(styles[clampi(int(look.get("hair", 0)), 0, styles.size() - 1)].get("beard", 0))


## The beard style's colour nearest the hair's (figure.json colours' "rgb"), else the same index.
func _beard_colour(styles: Array, bcols: Array) -> int:
	var hc := int(look.get("hair_color", 0))
	var hcols: Array = styles[clampi(int(look.get("hair", 0)), 0, styles.size() - 1)].colours if styles.size() > 0 else []
	if hcols.is_empty() or not (hcols[clampi(hc, 0, hcols.size() - 1)] as Dictionary).has("rgb"):
		return clampi(hc, 0, bcols.size() - 1)
	var want: Array = hcols[clampi(hc, 0, hcols.size() - 1)].rgb
	var best := clampi(hc, 0, bcols.size() - 1)
	var bd := INF
	for i in bcols.size():
		if not (bcols[i] as Dictionary).has("rgb"):
			continue
		var c: Array = bcols[i].rgb
		var d: float = Vector3(c[0] - want[0], c[1] - want[1], c[2] - want[2]).length_squared() + (0.0 if i == hc else 0.0005)
		if d < bd:
			bd = d
			best = i
	return best


## A hair style colour's material: its texture x tint, lit as hair.
func _hair_material(col: Dictionary) -> ShaderMaterial:
	var flow := hair_flow(String(col.tex))
	var m := _material(true, false, false, flow != null)
	m.set_shader_parameter("albedo_tex", _tex(String(col.tex)))
	m.set_shader_parameter("sheen", 1.0)
	if flow:                                         # redrawn as strands: lit as hair, no relief (it carved
		m.set_shader_parameter("hair_flow", flow)    # the strands into wood grain)
		m.set_shader_parameter("strand_spec", 0.0)      # matte: the strand highlights blew out white
		m.set_shader_parameter("fuzz", 1.0)
	else:
		m.set_shader_parameter("relief", 0.16)      # (its strands, raised)
	m.set_shader_parameter("tint", Color(col.tint[0], col.tint[1], col.tint[2]))
	m.set_shader_parameter("tint_mode", 1)
	return m


## The changes that turn an original-face look into the layered one wearing the same face's brows, beard and lines
## (figure.json skin_layers.face_map).
func layered_changes() -> Dictionary:
	var fm: Array = (meta.get("skin_layers", {}) as Dictionary).get("face_map", [])
	if fm.is_empty():
		return {}
	var f: Dictionary = fm[clampi(int(look.get("face", 0)), 0, fm.size() - 1)]
	var out := {"v2": true, "brows": int(f.get("brows", 1)), "brow_amt": 1.0,
		"age_style": int(f.get("age_style", -1)) + 1, "age": 0.8,
		"stubble_style": int(f.get("stubble_style", -1)) + 1, "stubble": 0.9}
	if not (meta.get("beards", []) as Array).is_empty():
		out["beard"] = beard_index()                 # pinned: changing the hair no longer changes the beard
	if not (meta.get("turbans", []) as Array).is_empty():
		out["turban"] = turban_index()               # (and the turban)
	return out


static var _base_tex := {}


func _base_face() -> Texture2D:
	var path := "%s/races/%s/%s.png" % [ROOT, race, String(meta.skin_layers.base)]
	if not _base_tex.has(path):
		var img := Image.load_from_file(path)
		if img:
			img.generate_mipmaps()
		_base_tex[path] = ImageTexture.create_from_image(img) if img else null
	return _base_tex[path]


## Which of the layers the look wears, as the head shader's slots. Look keys: brows / freckles / scar / paint (the
## option, 0 none), age / stubble (0 .. 1), lip_color (0 the face's own), paint_color.
func _layers(m: ShaderMaterial) -> void:
	var sl: Dictionary = meta.get("skin_layers", {})
	var defs := {}
	for d in sl.get("layers", []):
		defs[String(d.key)] = d
	var hair := Color(0.22, 0.16, 0.11)
	var hrgb: Array = sl.get("hair_rgb", [])
	if custom_colour("hair_color") != null:
		hair = custom_colour("hair_color")
	elif hrgb.size() > 0:
		var h: Array = hrgb[clampi(int(look.get("hair_color", 0)), 0, hrgb.size() - 1)]
		hair = Color(h[0], h[1], h[2])
	# the brows' own colour (owner 2026-11-06: not always the hair's - and a bald man's too): 0 the hair's
	var brow := hair.darkened(0.3)
	if custom_colour("brow_color") != null:
		brow = custom_colour("brow_color")
	elif int(look.get("brow_color", 0)) > 0:
		brow = BROW_COLORS[clampi(int(look.brow_color) - 1, 0, BROW_COLORS.size() - 1)]
	var slots := []                                    # [channel, colour (sRGB), strength, way]
	var pick := func(key: String, opt: int) -> int:
		var d: Dictionary = defs.get(key, {})
		var ch: Array = d.get("chan", [])
		return int(ch[opt - 1]) if opt >= 1 and opt <= ch.size() else -1
	var layered := is_layered()
	var c: int = pick.call("brows", int(look.get("brows", 0))) if layered else -1   # (the old faces paint their own)
	if c >= 0:
		slots.append([c, brow, clampf(float(look.get("brow_amt", 1.0)), 0.0, 1.5) * 0.9, 3])
	c = pick.call("freckles", int(look.get("freckles", 0)))
	if c >= 0:
		var fc = custom_colour("freckle_color")
		if fc == null:
			fc = FRECKLE_COLORS[clampi(int(look.get("freckle_color", 0)), 0, FRECKLE_COLORS.size() - 1)]
		slots.append([c, fc, clampf(float(look.get("freckle_amt", 0.9)), 0.0, 1.2), 2])
	var ast := int(look.get("age_style", 1 if float(look.get("age", 0.0)) > 0.01 else 0))
	if ast > 0:
		slots.append([pick.call("age", ast), Color(0.4, 0.34, 0.32), clampf(float(look.get("age", 0.7)), 0.0, 1.0), 2])
	c = pick.call("scar", int(look.get("scar", 0)))
	if c >= 0:
		var sc = custom_colour("scar_color")
		if sc == null:
			sc = SCAR_COLORS[clampi(int(look.get("scar_color", 0)), 0, SCAR_COLORS.size() - 1)]
		slots.append([c, sc, clampf(float(look.get("scar_amt", 0.55)), 0.0, 1.0), 1])   # (shaded by the skin under it)
	var sst := int(look.get("stubble_style", 1 if float(look.get("stubble", 0.0)) > 0.01 else 0))
	if sst > 0:
		slots.append([pick.call("stubble", sst), hair.darkened(0.4), clampf(float(look.get("stubble", 0.8)), 0.0, 1.0) * 0.95, 3])
	var li := int(look.get("lip_color", 0))
	var lc = custom_colour("lip_color")
	if lc != null or (li > 0 and li < LIP_COLORS.size()):
		slots.append([pick.call("lips", 1), lc if lc != null else LIP_COLORS[li], clampf(float(look.get("lip_amt", 0.6)), 0.0, 1.0), 1])
	_paint(m, sl)
	slots = slots.filter(func(s): return int(s[0]) >= 0)
	m.set_shader_parameter("layer_count", slots.size())
	if slots.is_empty():
		return
	var texs: Array = sl.get("tex", [])
	for i in mini(texs.size(), 7):
		var path := "%s/races/%s/%s.png" % [ROOT, race, texs[i]]
		if not _layer_tex.has(path):
			var img := Image.load_from_file(path)
			if img:
				img.generate_mipmaps()
			_layer_tex[path] = ImageTexture.create_from_image(img) if img else null
		m.set_shader_parameter("layer_tex%d" % i, _layer_tex[path])
	var chs := PackedInt32Array()
	var cols := PackedVector3Array()
	var amts := PackedFloat32Array()
	var modes := PackedInt32Array()
	for i in 7:
		var s: Array = slots[i] if i < slots.size() else [0, Color.WHITE, 0.0, 2]
		var col: Color = s[1]
		var lin := Vector3(col.r, col.g, col.b) if int(s[3]) == 2 else Vector3(pow(col.r, 2.2), pow(col.g, 2.2), pow(col.b, 2.2))
		chs.append(int(s[0]))
		cols.append(lin)
		amts.append(float(s[2]))
		modes.append(int(s[3]))
	m.set_shader_parameter("layer_ch", chs)
	m.set_shader_parameter("layer_col", cols)
	m.set_shader_parameter("layer_amt", amts)
	m.set_shader_parameter("layer_mode", modes)


## War paint: looked up in face space (skin_layers.paint: the atlas, and the face map - each texel's face point), so
## the player places it; the face map's third channel (how much the texel is face) keeps it on the face.
func _paint(m: ShaderMaterial, sl: Dictionary) -> void:
	var pd: Dictionary = sl.get("paint", {})
	var pi := int(look.get("paint", 0))
	if pd.is_empty() or pi <= 0 or pi > (pd.get("options", []) as Array).size():
		m.set_shader_parameter("paint_idx", -1)
		return
	var ap := "%s/races/%s/%s.png" % [ROOT, race, String(pd.atlas)]
	if not _layer_tex.has(ap):
		var img := Image.load_from_file(ap)
		_layer_tex[ap] = ImageTexture.create_from_image(img) if img else null
	var mp := "%s/races/%s/%s" % [ROOT, race, String(pd.map)]
	if not _layer_tex.has(mp):
		var n := int(pd.get("size", 1024))
		var bytes := FileAccess.get_file_as_bytes(mp)
		var img: Image = Image.create_from_data(n, n, false, Image.FORMAT_RGBAH, bytes) if bytes.size() == n * n * 8 else null
		_layer_tex[mp] = ImageTexture.create_from_image(img) if img else null
	if _layer_tex[ap] == null or _layer_tex[mp] == null:
		m.set_shader_parameter("paint_idx", -1)
		return
	var pc = custom_colour("paint_color")
	if pc == null:
		pc = PAINT_COLORS[clampi(int(look.get("paint_color", 0)), 0, PAINT_COLORS.size() - 1)]
	var box: Array = pd.box
	var cen: Array = pd.get("centres", [])
	var cv := float(cen[pi - 1][1]) if pi - 1 < cen.size() else 0.0
	m.set_shader_parameter("paint_atlas", _layer_tex[ap])
	m.set_shader_parameter("paint_map", _layer_tex[mp])
	m.set_shader_parameter("paint_idx", pi - 1)
	m.set_shader_parameter("paint_side", int(pd.get("side", 2)))
	m.set_shader_parameter("paint_box", Vector4(box[0], box[1], box[2], box[3]))
	m.set_shader_parameter("paint_col", Vector3(pow(pc.r, 2.2), pow(pc.g, 2.2), pow(pc.b, 2.2)))
	m.set_shader_parameter("paint_amt", clampf(float(look.get("paint_amt", 0.92)), 0.0, 1.0))
	m.set_shader_parameter("paint_xf", Vector4(clampf(float(look.get("paint_y", 0.0)), PAINT_Y.x, PAINT_Y.y),
		clampf(float(look.get("paint_size", 1.0)), PAINT_SIZE.x, PAINT_SIZE.y),
		deg_to_rad(clampf(float(look.get("paint_turn", 0.0)), PAINT_TURN.x, PAINT_TURN.y)), cv))


## The face, feature by feature (owner 2026-11-06: "choose from eye shapes, nose shapes, lip shapes ..."): each a set
## of named shapes over its own sliders (look.shape, -1 .. 1; Natural = the race's own). The creator offers these and
## keeps the sliders under each for fine tuning.
const FACE_FEATURES := [
	["eyes", "Eyes", ["eye_spacing", "eye_height", "eye_size", "eye_depth", "eye_tilt", "eye_squint"], [
		["Natural", {}], ["Large", {"eye_size": 0.7}], ["Small", {"eye_size": -0.6}], ["Deep-set", {"eye_depth": 0.8, "eye_size": -0.2}],
		["Prominent", {"eye_depth": -0.7, "eye_size": 0.3}], ["Wide-set", {"eye_spacing": 0.7}], ["Close-set", {"eye_spacing": -0.7}],
		["High", {"eye_height": 0.7}], ["Low", {"eye_height": -0.6}], ["Upswept", {"eye_tilt": 0.7}],
		["Downturned", {"eye_tilt": -0.6}], ["Feline", {"eye_tilt": 0.8, "eye_size": -0.3}], ["Narrowed", {"eye_squint": 0.7}],
		["Hooded", {"eye_squint": 0.5, "eye_depth": 0.5}], ["Wide-open", {"eye_squint": -0.6, "eye_size": 0.3}]]],
	["brow", "Brow", ["brow_height", "brow_depth"], [
		["Natural", {}], ["Heavy", {"brow_depth": 0.8, "brow_height": -0.3}], ["Smooth", {"brow_depth": -0.7}],
		["High", {"brow_height": 0.7}], ["Low", {"brow_height": -0.6}]]],
	["nose", "Nose", ["nose_width", "nose_length", "nose_height", "nose_bridge", "nose_tip", "nose_tip_size"], [
		["Natural", {}], ["Button", {"nose_length": -0.7, "nose_width": -0.2, "nose_tip": 0.5}], ["Upturned", {"nose_tip": 0.8}],
		["Hawk", {"nose_bridge": 0.8, "nose_length": 0.5, "nose_tip": -0.6, "nose_width": -0.3}], ["Roman", {"nose_bridge": 0.7, "nose_length": 0.3}],
		["Broad", {"nose_width": 0.8, "nose_height": -0.2}], ["Narrow", {"nose_width": -0.7}], ["Long", {"nose_length": 0.8, "nose_height": -0.4}],
		["Flat", {"nose_length": -0.6, "nose_bridge": -0.6, "nose_width": 0.4}], ["Bulbous", {"nose_tip_size": 0.9, "nose_width": 0.2}],
		["Pinched", {"nose_tip_size": -0.7, "nose_width": -0.4}]]],
	["cheeks", "Cheeks", ["cheekbones", "cheek_puff"], [
		["Natural", {}], ["High", {"cheekbones": 0.8}], ["Soft", {"cheekbones": -0.5, "cheek_puff": 0.3}],
		["Hollow", {"cheekbones": 0.4, "cheek_puff": -0.9}], ["Gaunt", {"cheekbones": 0.7, "cheek_puff": -0.7}],
		["Round", {"cheek_puff": 0.8}], ["Chubby", {"cheek_puff": 1.0, "cheekbones": -0.4}]]],
	["mouth", "Lips", ["lips", "upper_lip", "lower_lip", "mouth_width", "smile", "lip_out", "mouth_height"], [
		["Natural", {}], ["Full", {"lips": 0.8}], ["Thin", {"lips": -0.7}], ["Pouty", {"lower_lip": 0.8, "lip_out": 0.6}],
		["Bow", {"upper_lip": 0.8, "mouth_width": -0.3}], ["Heavy Lower", {"lower_lip": 1.0, "upper_lip": -0.3}],
		["Wide", {"mouth_width": 0.7}], ["Small", {"mouth_width": -0.6, "lips": 0.2}], ["Smiling", {"smile": 0.6}],
		["Stern", {"smile": -0.6, "lips": -0.3}], ["High", {"mouth_height": 0.6}], ["Low", {"mouth_height": -0.6}]]],
	["jaw", "Jaw", ["jaw_width", "jaw_height", "jaw_sharp"], [
		["Natural", {}], ["Square", {"jaw_width": 0.6, "jaw_sharp": 0.5}], ["Strong", {"jaw_width": 0.9, "jaw_sharp": 0.8}],
		["Chiseled", {"jaw_sharp": 1.0, "jaw_height": 0.3}], ["Soft", {"jaw_sharp": -0.8}], ["Narrow", {"jaw_width": -0.6}],
		["Delicate", {"jaw_width": -0.9, "jaw_sharp": -0.4}], ["High", {"jaw_height": 0.8}], ["Low", {"jaw_height": -0.7}]]],
	["chin", "Chin", ["chin_length", "chin_point", "chin_width"], [
		["Natural", {}], ["Pointed", {"chin_point": 0.6, "chin_width": -0.8, "chin_length": 0.2}],
		["Broad", {"chin_width": 0.8}], ["Narrow", {"chin_width": -0.6}], ["Short", {"chin_length": -0.7}],
		["Long", {"chin_length": 0.8}], ["Jutting", {"chin_point": 1.0}], ["Receding", {"chin_point": -0.8}],
		["Sharp", {"chin_width": -1.0, "chin_point": 0.4}]]],
	["ears", "Ears", ["ear_size", "ear_out", "ear_tilt"], [
		["Natural", {}], ["Small", {"ear_size": -0.7}], ["Large", {"ear_size": 0.8}], ["Out", {"ear_out": 0.9}],
		["Swept", {"ear_tilt": 0.9}], ["Large, Swept", {"ear_size": 0.6, "ear_tilt": 0.8}]]],
]


## Which named shape of a feature the look wears (its sliders all at that shape's values), -1: tuned by hand.
static func feature_preset(feature: Array, shape: Dictionary) -> int:
	var presets: Array = feature[3]
	for i in presets.size():
		var vals: Dictionary = presets[i][1]
		var ok := true
		for k in feature[2]:
			if absf(float(shape.get(k, 0.0)) - float(vals.get(k, 0.0))) > 0.03:
				ok = false
				break
		if ok:
			return i
	return -1


## The shape with one feature set to its named shape i.
static func with_feature(feature: Array, shape: Dictionary, i: int) -> Dictionary:
	var out := shape.duplicate()
	for k in feature[2]:
		out.erase(k)
	out.merge((feature[3][i][1] as Dictionary), true)
	return out

## The body sliders alone (as they move: the bones read look.body every frame; only the height rescales).
func set_body(body: Dictionary) -> void:
	look["body"] = body
	var sizes := [0.95, 1.0, 1.05]
	scale = Vector3.ONE * float(meta.get("scale", 1.0)) * float(sizes[clampi(int(look.get("size", 1)), 0, 2)]) \
			* (1.0 + 0.07 * clampf(float(body.get("height", 0.0)), -1.0, 1.0))

## The face shapes alone (the creator's sliders call this as they move: no materials rebuilt).
func set_shape(shape: Dictionary) -> void:
	look["shape"] = shape
	_apply_shape()


func _apply_shape() -> void:
	var styles: Array = meta.get("hair_styles", [])
	var shapes: Array = meta.get("face_shapes", [])
	if not shapes.is_empty():
		var shape: Dictionary = look.get("shape", {})
		var meshes: Array = _parts("head").duplicate()
		for st in styles:
			if st.node != null and _meshes.has(st.node):
				meshes.append_array(_parts(st.node))
		for b in meta.get("beards", []) + meta.get("moustaches", []) + meta.get("sideburns", []) + meta.get("turbans", []) \
				+ [meta.get("hair_under", {"node": ""})]:
			if _meshes.has(String(b.node)):
				meshes.append_array(_parts(String(b.node)))
		for b in styles + meta.get("beards", []) + meta.get("moustaches", []) + meta.get("sideburns", []):
			if b.has("jewels") and _meshes.has(String(b.jewels.node)):    # (a beard's rings, with it)
				meshes.append_array(_parts(String(b.jewels.node)))
		for fs in shapes:
			var w := clampf(float(shape.get(String(fs[0]), 0.0)), -1.0, 1.0)
			for mi in meshes:
				_blend(mi, "fx_" + String(fs[0]), w)


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
			mi.visible = i == si and not _hair_covered() and not _under_helm(styles[i])
			# under a helm the hair takes that helm type's morph (flattened so it doesn't poke through), else none.
			# Type 1 is the circlets' (the crafted hat06 circlets, the Crown of Zahur - nothing else uses it): a band
			# that shows the hair, which stays as it is (owner 2026-10-14: circlets hid the hair - its morph tore the
			# hair open over the band)
			var morphs: Dictionary = meta.get("helm_hair", {}).get(String(node), {})
			var under := _helm_hair if _helm != null else \
				(TURBAN_HAIR if turban_index() > 0 and int(styles[i].get("turban", 0)) == 0 else 0)
			for k in morphs:
				_blend(mi, String(morphs[k]), 1.0 if int(k) == under and under != 1 else 0.0)
	if not (meta.get("hair_under", {}) as Dictionary).is_empty():
		var hu: Dictionary = meta.hair_under
		for mi in _parts(String(hu.node)):
			mi.visible = scalp_cap_on() and not _hair_covered() and not (_helm != null and _helm_hair >= 2)
	var tb: Array = meta.get("turbans", [])
	var ti := turban_index()
	for k in tb.size():
		if _meshes.has(String(tb[k].node)):
			for mi in _parts(String(tb[k].node)):
				mi.visible = k + 1 == ti and not _hair_covered() and _helm == null
	for kind in FACE_HAIR:
		var list: Array = meta.get(String(kind[1]), [])
		for k in list.size():
			for mi in _parts(String(list[k].node)):
				mi.visible = k + 1 == int(look.get(String(kind[0]), 0)) and not _hair_covered()
			_jewels(list[k], k + 1 == int(look.get(String(kind[0]), 0)) and not _hair_covered())
	var beards: Array = meta.get("beards", [])
	var bi := beard_index()
	for k in beards.size():
		var bnode := String(beards[k].node)
		if not _meshes.has(bnode):
			continue
		var morphs: Dictionary = meta.get("helm_hair", {}).get(bnode, {})
		_jewels(beards[k], k + 1 == bi and not _hair_covered())
		for mi in _parts(bnode):
			mi.visible = k + 1 == bi and not _hair_covered()
			for h in morphs:
				_blend(mi, String(morphs[h]), 1.0 if _helm != null and int(h) == _helm_hair and _helm_hair != 1 else 0.0)


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


## The look's skin tone (the race's fig3skincolormap tints), or the creator's own skin colour (look.skin_rgb, the
## colour the skin should come out: the tint is that over the face texture's own skin).
func _skin() -> Color:
	var cs = custom_colour("skin")
	if cs != null:
		var b := skin_base()
		return Color(clampf(cs.r / maxf(b.r, 0.05), 0.0, 2.0), clampf(cs.g / maxf(b.g, 0.05), 0.0, 2.0),
				clampf(cs.b / maxf(b.b, 0.05), 0.0, 2.0))
	var tones: Array = meta.get("skin_tones", [[1, 1, 1]])
	var tone: Array = tones[clampi(int(look.get("skin", 0)), 0, tones.size() - 1)]
	return skin_tint(tone)


static var _skin_bases := {}


## The face texture's own skin colour (the middle of the face, untinted) - what a custom skin colour is measured from.
func skin_base() -> Color:
	if _skin_bases.has(race):
		return _skin_bases[race]
	var faces: Array = meta.get("faces", [])
	var t: Texture2D = _base_face() if is_layered() else null
	if t == null and faces.size() > 0:
		t = _tex(String(faces[0].tex))
	var col := Color(0.75, 0.6, 0.5)
	var img: Image = t.get_image() if t else null
	if img:
		img = img.duplicate()
		if img.is_compressed():
			img.decompress()
		img.convert(Image.FORMAT_RGBA8)
		img = img.get_region(Rect2i(img.get_width() * 3 / 10, img.get_height() * 3 / 10, img.get_width() * 2 / 5, img.get_height() / 4))
		img.resize(16, 16, Image.INTERPOLATE_BILINEAR)
		var sum := Color(0, 0, 0, 0)
		for yy in 16:
			for xx in 16:
				sum += img.get_pixel(xx, yy)
		col = Color(sum.r / 256.0, sum.g / 256.0, sum.b / 256.0)
	_skin_bases[race] = col
	return col


## A colour the creator's wheel set (look["<key>_rgb"], sRGB 0..1), else null.
func custom_colour(key: String):
	var a = look.get(key + "_rgb")
	if a is Array and (a as Array).size() >= 3:
		return Color(float(a[0]), float(a[1]), float(a[2]))
	return null


## A hair style's colour as worn: the chosen one, or - a custom colour - the style's lightest texture tinted to it
## (figure.json colours' "rgb": each texture x tint's average).
func hair_colour(colours: Array) -> Dictionary:
	var col: Dictionary = colours[clampi(int(look.get("hair_color", 0)), 0, colours.size() - 1)]
	var want = custom_colour("hair_color")
	if want == null:
		return col
	var best := col
	var bl := -1.0
	for c in colours:
		if (c as Dictionary).has("rgb"):
			var l := float(c.rgb[0]) * 0.3 + float(c.rgb[1]) * 0.59 + float(c.rgb[2]) * 0.11
			if l > bl:
				bl = l
				best = c
	var rgb: Array = best.get("rgb", [0.5, 0.42, 0.33])
	var t: Array = best.get("tint", [1, 1, 1])
	var w: Color = want * 0.85                       # (the strands' sheen lifts it: the bare ratio came out too bright)
	return {"tex": best.tex, "tint": [clampf(float(t[0]) * w.r / maxf(float(rgb[0]), 0.04), 0.0, 3.0),
		clampf(float(t[1]) * w.g / maxf(float(rgb[1]), 0.04), 0.0, 3.0),
		clampf(float(t[2]) * w.b / maxf(float(rgb[2]), 0.04), 0.0, 3.0)], "chan": best.get("chan", "")}


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
		"beard": return meta.get("beards", []).size() + 1
		"moustache": return meta.get("moustaches", []).size() + 1 if not (meta.get("moustaches", []) as Array).is_empty() else 0
		"sideburns": return meta.get("sideburns", []).size() + 1 if not (meta.get("sideburns", []) as Array).is_empty() else 0
		"turban": return meta.get("turbans", []).size() + 1 if not (meta.get("turbans", []) as Array).is_empty() else 0
		"hair_color":
			var styles: Array = meta.get("hair_styles", [])
			var n: int = styles[clampi(int(look.get("hair", 0)), 0, styles.size() - 1)].colours.size() if styles.size() > 0 else 0
			if n == 0 and int(look.get("scalp_cap", 0)) == 1:     # (bald with the scalp cap: the cap's colours)
				n = (meta.get("hair_under", {}).get("colours", []) as Array).size()
			return n
		"tattoo": return meta.get("tattoos", []).size()
		"size": return 3
	return 0


func play(clip: String) -> void:
	if anim and anim.has_animation(clip):
		anim.play(clip, 0.15)


# ---------------------------------------------------------------- start and stop (claude 2026-11-08)
## Owner 2026-11-08 (Guild Wars 2's runner: "a little of the momentum reflected in the animations and movement of the
## hair and cloaks"): Sway's lean, hair and cloak. A trailing figure (drawn a little behind its real place, the legs
## paced to it) was tried and taken out (owner 2026-11-09: "a jittery quality to movement ... still too subtle").
var _near := false                           # Sway ran this frame (remastered, in range)


# ---------------------------------------------------------------- upper / lower body (claude 2026-11-09)
## Owner 2026-11-09: a swing on the move played its own baked step and slid along, turned to where the body ran (in
## action combat, sideways to where you look) - "some sort of way that the upper torso turns to swing in the direction
## of the way the cursor is looking ... while the hips and legs still run in the correct way ... It will have to cover
## styled attack animations too". The client had no upper / lower body blending; Layers adds it: while set_lower names
## a legs clip, the legs (the root, the pelvis, the thighs and down) play it in step, carrying on from where the run was,
## and the upper body plays the action as it was made - turned by `twist` about the hips, spread up the back. Fades in
## and out over LOWER_FADE. Player sets it each frame; an action standing still plays whole, as before.
## The ground for the feet (animation step 3, Sway._feet): the zone viewer sets what answers height_at(x, z, near_y)
## (the region, or the zone) and whether it's a city (a city's grid is its roofs: the floor pick only, as Player).
static var ground_src: Object = null
static var ground_city := false


## Where the head looks (world; INF: ahead) - Player and Npc set it every frame (Sway turns the head; step 2).
var look_point := Vector3.INF
const LOCO_CLIPS := ["run", "walk", "walk_back", "strafe_left", "strafe_right"]
const LOWER_FADE := 0.15
var lower_clip := ""
var lower_speed := 1.0
var lower_twist := 0.0
var _loco_clip := ""                         # the last movement clip playing whole, and where in it (Layers)
var _loco_t := 0.0
var _lower_clip := ""                        # the legs clip Layers last ran under an action, and where in it
var _lower_t := 0.0
var _lower_at := 0


func set_lower(clip: String, speed := 1.0, twist := 0.0) -> void:
	lower_clip = clip
	lower_speed = speed
	lower_twist = clampf(wrapf(twist, -PI, PI), -1.4, 1.4)


## Where the legs are in `clip`, when they just ran it under an action (to carry on in step); -1 otherwise.
func lower_phase(clip: String) -> float:
	if clip == _lower_clip and Time.get_ticks_msec() - _lower_at < 300:
		return _lower_t
	return -1.0


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


## A hair texture's flow map (pipeline/hair_strands.py), or null when the hair wasn't redrawn. Linear (not sRGB, not
## compressed): its channels are directions.
static func hair_flow(tex: String) -> Texture2D:
	var key := tex.to_lower()
	if _flow_cache.has(key):
		return _flow_cache[key]
	var path := ProjectSettings.globalize_path("%s/fig3_textures/hairflow/%s.png" % [ROOT, key])
	var t: Texture2D = null
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(path)
		if img:
			img.generate_mipmaps()
			t = ImageTexture.create_from_image(img)
	_flow_cache[key] = t
	return t


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


## Remastered hair (owner 2026-11-05: "Let's do all of the vanilla hair styles"): its texture redrawn as strands
## (pipeline/hair_strands.py), matte, its outline broken into strands where it's seen edge on (the flow map beside each
## texture, hairflow/: R, G the strands' doubled angle in UV space, B the strand mask). Strand highlights (Kajiya-Kay,
## strand_spec) are there but off: on the low-poly shells they blew out white in patches ("too shiny ... plastic").
const HAIR_UNIFORMS := "uniform sampler2D hair_flow : filter_linear_mipmap;\nuniform float strand_spec = 0.0;\nuniform float fuzz = 0.0;\nvarying vec3 hair_t;"
const HAIR_FRAGMENT := """vec4 hf = texture(hair_flow, UV);
	{
		float th = 0.5 * atan(hf.g * 2.0 - 1.0, hf.r * 2.0 - 1.0);
		vec2 fl = vec2(cos(th), sin(th));
		vec3 dp1 = dFdx(VERTEX);
		vec3 dp2 = dFdy(VERTEX);
		vec2 du1 = dFdx(UV);
		vec2 du2 = dFdy(UV);
		vec3 dp2p = cross(dp2, NORMAL);
		vec3 dp1p = cross(NORMAL, dp1);
		hair_t = normalize((dp2p * du1.x + dp1p * du2.x) * fl.x + (dp2p * du1.y + dp1p * du2.y) * fl.y + NORMAL * 1e-5);
	}
	//CUTOUT"""
const HAIR_CUTOUT := """if (remaster_fx > 0.5) {
		// matte (owner 2026-11-05: "too shiny ... like a plastic doll head" - a low-poly shell can't carry a strand's
		// gloss): no sky reflection, no sheen; the light it gets is soft and wrapped (light() below)
		ROUGHNESS = 1.0;
		SPECULAR = 0.0;
	}
	ALPHA = c.a;
	if (remaster_fx > 0.5 && fuzz > 0.0) {
		float edge = 1.0 - smoothstep(0.08, 0.45, abs(dot(NORMAL, VIEW)));
		ALPHA = c.a * mix(1.0, smoothstep(0.25, 0.55, hf.b), edge * fuzz);
	}
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ALPHA_ANTIALIASING_EDGE = 0.3;"""
const HAIR_LIGHT := """
void light() {
	float ndl = dot(NORMAL, LIGHT);
	if (remaster_fx < 0.5) {
		DIFFUSE_LIGHT += clamp(ndl, 0.0, 1.0) * ATTENUATION * LIGHT_COLOR / PI;
	} else {
		DIFFUSE_LIGHT += clamp(ndl * 0.7 + 0.3, 0.0, 1.0) * ATTENUATION * LIGHT_COLOR / PI;
		vec3 h = normalize(LIGHT + VIEW);
		float d1 = dot(normalize(hair_t + NORMAL * 0.12), h);
		float d2 = dot(normalize(hair_t - NORMAL * 0.12), h);
		float s1 = pow(sqrt(max(0.0, 1.0 - d1 * d1)), 140.0);
		float s2 = pow(sqrt(max(0.0, 1.0 - d2 * d2)), 36.0);
		float vis = smoothstep(-0.1, 0.25, ndl) * ATTENUATION;
		SPECULAR_LIGHT += (vec3(s1) * 0.55 + ALBEDO * s2 * 0.6) * strand_spec * vis * LIGHT_COLOR / PI;
	}
}
"""


static func _material(cutout: bool, single_sided := false, skin := false, hair := false) -> ShaderMaterial:
	var key := ("cutout" if cutout else "solid") + ("_cull" if single_sided else "") + ("_skin" if skin else "") \
		+ ("_hair" if hair else "")
	if not _shaders.has(key):
		var s := Shader.new()
		var code := SHADER
		if single_sided:                                     # (cloaks: fig3parts 'Double Sided' empty - the client culls)
			code = code.replace("cull_disabled", "cull_back")
		if skin:
			code = code.replace("//CUTOUT", SKIN_SHADING)
		if hair:
			code = code.replace("varying vec2 logo_uv;", "varying vec2 logo_uv;\n" + HAIR_UNIFORMS)
			code = code.replace("//CUTOUT", HAIR_FRAGMENT)
			code = code.replace("//CUTOUT", HAIR_CUTOUT if cutout else "") + HAIR_LIGHT
		elif cutout:
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
// the creator's skin layers (pipeline/skin_layers.py, Fig3Figure._layers): up to 7 masks over the face - brows, freckles,
// age lines, a scar, stubble, lip colour, war paint - each a channel of the race's skin_layers_<n> textures, a colour,
// a strength and a way: 1 paint (the colour, shaded by the skin under it), 2 multiply, 3 hair (the colour itself)
uniform sampler2D layer_tex0 : filter_linear_mipmap, repeat_enable;
uniform sampler2D layer_tex1 : filter_linear_mipmap, repeat_enable;
uniform sampler2D layer_tex2 : filter_linear_mipmap, repeat_enable;
uniform sampler2D layer_tex3 : filter_linear_mipmap, repeat_enable;
uniform sampler2D layer_tex4 : filter_linear_mipmap, repeat_enable;
uniform sampler2D layer_tex5 : filter_linear_mipmap, repeat_enable;
uniform sampler2D layer_tex6 : filter_linear_mipmap, repeat_enable;
uniform int layer_count = 0;
uniform int layer_ch[7];
uniform vec3 layer_col[7];
uniform float layer_amt[7];
uniform int layer_mode[7];
// war paint in face space (Fig3Figure._paint): the face map (each texel's face point u, v and how much it is face),
// the paints' atlas, which paint, its colour (linear), strength and placement (up, size, turn, its middle's height)
uniform sampler2D paint_map : filter_linear, repeat_disable;
uniform sampler2D paint_atlas : filter_linear, repeat_disable;
uniform int paint_idx = -1;
uniform int paint_side = 2;
uniform vec4 paint_box = vec4(-1.7, 1.7, -2.4, 1.7);
uniform vec3 paint_col = vec3(0.0);
uniform float paint_amt = 0.0;
uniform vec4 paint_xf = vec4(0.0, 1.0, 0.0, 0.0);
// the creator's own iris colour (a = on): the eye texture's iris recoloured, its detail kept
uniform vec4 eye_tint = vec4(0.0);
varying vec2 logo_uv;
// the body sliders' bust / pecs and glutes (Fig3Figure.BodyShape._bulge): two points each (world xyz, radius) and the
// way they swell (world, times the slider)
uniform vec4 bulge_a = vec4(0.0);
uniform vec4 bulge_b = vec4(0.0);
uniform vec4 bulge_c = vec4(0.0);
uniform vec4 bulge_d = vec4(0.0);
uniform vec3 bulge_ab = vec3(0.0);
uniform vec3 bulge_cd = vec3(0.0);
uniform vec2 bulge_amt = vec2(0.0);

vec3 bulge(vec3 wp, vec3 wn, vec4 p, vec3 d, float amt) {
	if (p.w <= 0.0 || abs(amt) < 1e-4) return vec3(0.0);
	vec3 o = wp - p.xyz;
	float q = dot(o, o) / (p.w * p.w);
	if (q > 4.0) return vec3(0.0);
	float face = smoothstep(-0.2, 0.5, dot(wn, d));      // only the side that faces the way it swells
	return d * amt * p.w * 0.9 * exp(-q * 1.6) * face;
}

void vertex() {
	logo_uv = CUSTOM0.xy;
	if (bulge_a.w > 0.0 || bulge_c.w > 0.0) {
		vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
		vec3 wn = normalize(mat3(MODEL_MATRIX) * NORMAL);
		vec3 dv = bulge(wp, wn, bulge_a, bulge_ab, bulge_amt.x) + bulge(wp, wn, bulge_b, bulge_ab, bulge_amt.x)
				+ bulge(wp, wn, bulge_c, bulge_cd, bulge_amt.y) + bulge(wp, wn, bulge_d, bulge_cd, bulge_amt.y);
		VERTEX += inverse(mat3(MODEL_MATRIX)) * dv;
	}
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
	float ref = max(dot(tint, vec3(0.3, 0.59, 0.11)) * 0.45, 0.05);
	if (layer_count > 0) {
		float ch[28];
		vec4 t0 = texture(layer_tex0, UV), t1 = texture(layer_tex1, UV), t2 = texture(layer_tex2, UV);
		vec4 t3 = texture(layer_tex3, UV), t4 = texture(layer_tex4, UV), t5 = texture(layer_tex5, UV);
		vec4 t6 = texture(layer_tex6, UV);
		for (int i = 0; i < 4; i++) {
			ch[i] = t0[i]; ch[4 + i] = t1[i]; ch[8 + i] = t2[i]; ch[12 + i] = t3[i]; ch[16 + i] = t4[i];
			ch[20 + i] = t5[i]; ch[24 + i] = t6[i];
		}
		for (int i = 0; i < layer_count; i++) {
			float m = ch[clamp(layer_ch[i], 0, 27)] * layer_amt[i];
			vec3 lc = layer_col[i];
			if (layer_mode[i] == 1) {
				float shade = clamp(dot(col, vec3(0.3, 0.59, 0.11)) / ref, 0.55, 1.25);
				col = mix(col, lc * shade, m);
			}
			else if (layer_mode[i] == 2) col = mix(col, col * lc, m);
			else col = mix(col, lc, m);
		}
	}
	if (paint_idx >= 0) {
		vec4 fm = texture(paint_map, UV);
		if (fm.z > 0.01) {
			float sgn = fm.x < 0.0 ? -1.0 : 1.0;          // (mirrored: each side turns its own way)
			vec2 c0 = vec2(0.0, paint_xf.w);
			vec2 q = fm.xy - vec2(0.0, paint_xf.x) - c0;
			float a = -paint_xf.z * sgn;
			q = mat2(vec2(cos(a), sin(a)), vec2(-sin(a), cos(a))) * q / paint_xf.y + c0;
			vec2 t = vec2((q.x - paint_box.x) / (paint_box.y - paint_box.x), (paint_box.w - q.y) / (paint_box.w - paint_box.z));
			if (t.x > 0.004 && t.y > 0.004 && t.x < 0.996 && t.y < 0.996) {
				float side = float(paint_side);
				int tile = paint_idx / 4;
				vec2 o = vec2(float(tile % paint_side), float(tile / paint_side));
				vec4 a4 = texture(paint_atlas, (o + t) / side);
				float pm = a4[paint_idx % 4] * clamp(fm.z, 0.0, 1.0) * paint_amt;
				float shade = clamp(dot(col, vec3(0.3, 0.59, 0.11)) / ref, 0.55, 1.25);
				col = mix(col, paint_col * shade, pm);
			}
		}
	}
	if (has_eye) {
		vec3 e = texture(eye_tex, UV).rgb;
		if (eye_tint.a > 0.5) {
			float mn = min(e.r, min(e.g, e.b));
			float iris = clamp((0.9 - mn) * 6.0, 0.0, 1.0);
			float l = dot(e, vec3(0.3, 0.59, 0.11));
			e = mix(vec3(1.0), eye_tint.rgb * clamp(l * 2.2, 0.25, 1.6), iris);
		}
		col *= e;
	}
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


## The body sliders (owner 2026-11-06, the creator's BODY page): look.body {name: -1 .. 1}. Height scales the whole
## figure; the rest are bones scaled after the animation (BodyShape), each undone below it so only its own part
## changes - the arms longer but the hands their size, the chest bigger but the head and arms not.
## The creator's BODY sliders (owner 2026-11-06: chest in three, waist, hips, glutes, thighs, calves; lengths that only
## lengthen): [key, label, group]. -1..1 each in look.body; "chest_size" reads Bust or Pecs by the figure's sex.
const BODY_SLIDERS := [["height", "Height", "OVERALL"], ["head", "Head Size", "OVERALL"],
	["shoulders", "Shoulders", "UPPER BODY"], ["chest_width", "Chest Width", "UPPER BODY"],
	["chest_depth", "Chest Depth", "UPPER BODY"], ["chest_size", "Chest Size", "UPPER BODY"],
	["waist", "Waist", "UPPER BODY"], ["torso", "Torso Length", "UPPER BODY"],
	["arms", "Arm Length", "ARMS"], ["arm_size", "Arm Thickness", "ARMS"], ["hands", "Hands", "ARMS"],
	["hips", "Hips", "LOWER BODY"], ["glutes", "Glutes", "LOWER BODY"], ["legs", "Leg Length", "LOWER BODY"],
	["thighs", "Thighs", "LOWER BODY"], ["calves", "Calves", "LOWER BODY"]]

## The bones whose flesh the body sliders reshape. Each gets a leaf "<bone> def" (rest = the bone's own): the skins'
## weights move to it, so it can be widened or lengthened in its own frame without its children - the arm hanging off
## the chest, the calf off the thigh - inheriting the stretch (a bone scaled in place widened everything below it:
## owner 2026-11-06, "Chest is messing with the entire top half ... Leg length seems to be scaling more than ...").
const BODY_DEFS := ["Pelvis", "Spine", "Spine1", "Spine2", "L Clavicle", "R Clavicle", "L Pauldron", "R Pauldron",
	"L UpperArm", "R UpperArm", "L BicepTwist", "R BicepTwist", "L Forearm", "R Forearm", "L ForeTwist", "R ForeTwist",
	"L ForeTwist1", "R ForeTwist1", "L Thigh", "R Thigh", "L ThighTwist", "R ThighTwist", "L Calf", "R Calf"]


## The def bones on a fresh figure's skeleton, and its skins' weights moved onto them (once per shared skin: every
## figure of a race adds the same bones in the same order, so one rewired skin serves them all).
static func add_body_bones(model: Node3D) -> void:
	var skels := model.find_children("*", "Skeleton3D", true, false)
	if skels.is_empty():
		return
	var sk := skels[0] as Skeleton3D
	var defs := {}
	for n in BODY_DEFS:
		var b := sk.find_bone("Bip01 " + n)
		if b < 0 or sk.find_bone("Bip01 %s def" % n) >= 0:
			continue
		var i := sk.add_bone("Bip01 %s def" % n)
		sk.set_bone_parent(i, b)
		sk.set_bone_rest(i, Transform3D())
		sk.set_bone_pose_position(i, Vector3.ZERO)
		sk.set_bone_pose_rotation(i, Quaternion.IDENTITY)
		sk.set_bone_pose_scale(i, Vector3.ONE)
		defs["Bip01 " + n] = i
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var skin: Skin = (mi as MeshInstance3D).skin
		if skin == null or skin.has_meta("body_defs"):
			continue
		skin.set_meta("body_defs", true)
		for k in skin.get_bind_count():
			var nm := String(skin.get_bind_name(k))
			if nm == "" and skin.get_bind_bone(k) >= 0:
				nm = sk.get_bone_name(skin.get_bind_bone(k))
			if defs.has(nm):
				if String(skin.get_bind_name(k)) != "":
					skin.set_bind_name(k, nm + " def")
				skin.set_bind_bone(k, int(defs[nm]))


class BodyShape extends SkeletonModifier3D:
	var fig: Fig3Figure
	var _b := {}
	var _d := {}
	var _leg := 0.0                              # the leg's rest length (pelvis to ankle), for the lift
	var _up := Vector3.UP
	var _bulged := false                         # bust / glute shapes set on the parts (cleared once when they go)

	func _find(sk: Skeleton3D) -> void:
		for n in ["Head", "Pelvis", "Spine", "Spine1", "Spine2", "Neck", "L Clavicle", "R Clavicle", "L UpperArm",
				"R UpperArm", "L Forearm", "R Forearm", "L ForeTwist", "R ForeTwist", "L ForeTwist1", "R ForeTwist1",
				"L Hand", "R Hand", "L Thigh", "R Thigh", "L Calf", "R Calf", "L Foot", "R Foot", "L Pauldron",
				"R Pauldron", "L Back", "R Back"]:
			_b[n] = sk.find_bone("Bip01 " + n)
		for n in BODY_DEFS:
			_d[n] = sk.find_bone("Bip01 %s def" % n)
		var th: int = _b["L Thigh"]
		var ft: int = _b["L Foot"]
		if th >= 0 and ft >= 0:
			var a := sk.get_bone_global_rest(th).origin
			var c := sk.get_bone_global_rest(ft).origin
			_leg = a.distance_to(c)
			_up = (a - c).normalized()

	## A def bone's shape in the bone's own frame (Biped: x along the bone; on the spine y front-back, z across).
	func _def(sk: Skeleton3D, n: String, s: Vector3) -> void:
		var b: int = _d.get(n, -1)
		if b >= 0:
			sk.set_bone_pose_scale(b, s)

	## A bone moved along its parent's length (the parent grew), or across (z), or front-back (y).
	func _move(sk: Skeleton3D, n: String, f: Vector3) -> void:
		var b: int = _b.get(n, -1)
		if b >= 0 and not f.is_equal_approx(Vector3.ONE):
			sk.set_bone_pose_position(b, sk.get_bone_pose_position(b) * f)

	func _scale(sk: Skeleton3D, n: String, f: float) -> void:
		var b: int = _b.get(n, -1)
		if b >= 0 and absf(f - 1.0) > 0.0005:
			sk.set_bone_pose_scale(b, sk.get_bone_pose_scale(b) * f)

	func _process_modification_with_delta(_delta: float) -> void:
		var sk := get_skeleton()
		if sk == null or fig == null:
			return
		var body: Dictionary = fig.look.get("body", {})
		if body.is_empty():
			if _bulged:
				_bulge(sk, 0.0, 0.0)
			return
		if _b.is_empty():
			_find(sk)
		var v := func(k: String) -> float: return clampf(float(body.get(k, 0.0)), -1.0, 1.0)
		var hd: float = 1.0 + 0.09 * v.call("head")
		var sh: float = 1.0 + 0.2 * v.call("shoulders")
		var cw: float = 1.0 + 0.16 * v.call("chest_width")
		var cd: float = 1.0 + 0.2 * v.call("chest_depth")
		var wa: float = 1.0 + 0.2 * v.call("waist")
		var tor: float = 1.0 + 0.12 * v.call("torso")
		var ar: float = 1.0 + 0.08 * v.call("arms")
		var at: float = 1.0 + 0.24 * v.call("arm_size")
		var hn: float = 1.0 + 0.1 * v.call("hands")
		var hp: float = 1.0 + 0.17 * v.call("hips")
		var lg: float = 1.0 + 0.07 * v.call("legs")
		var tt: float = 1.0 + 0.24 * v.call("thighs")
		var ct: float = 1.0 + 0.24 * v.call("calves")
		_scale(sk, "Head", hd)
		# the trunk: the ribcage (Spine2) wide and deep, the belly (Spine1, Spine) the waist, the pelvis the hips
		_def(sk, "Spine2", Vector3(1.0, cd, cw))
		_def(sk, "Spine1", Vector3(tor, lerpf(1.0, cd, 0.3) * wa, lerpf(1.0, cw, 0.3) * wa))
		_def(sk, "Spine", Vector3(1.0, wa, lerpf(wa, hp, 0.5)))
		_def(sk, "Pelvis", Vector3(1.0, lerpf(1.0, hp, 0.5), hp))
		_move(sk, "Spine2", Vector3(tor, 1.0, 1.0))
		_move(sk, "L Back", Vector3(tor, 1.0, 1.0))
		_move(sk, "R Back", Vector3(tor, 1.0, 1.0))
		_move(sk, "L Thigh", Vector3(1.0, 1.0, hp))
		_move(sk, "R Thigh", Vector3(1.0, 1.0, hp))
		_move(sk, "L Clavicle", Vector3(1.0, 1.0, cw))
		_move(sk, "R Clavicle", Vector3(1.0, 1.0, cw))
		var sw := sh * lerpf(1.0, cw, 0.6)                   # the shoulder joint out with the shoulders and the chest
		for side in ["L ", "R "]:
			_def(sk, side + "Clavicle", Vector3(sw, 1.0, 1.0))
			_move(sk, side + "UpperArm", Vector3(sw, 1.0, 1.0))
			_move(sk, side + "Pauldron", Vector3(sw, 1.0, 1.0))
			_def(sk, side + "Pauldron", Vector3.ONE * lerpf(1.0, at, 0.6))
			for n in ["UpperArm", "BicepTwist", "Forearm", "ForeTwist", "ForeTwist1"]:
				_def(sk, side + n, Vector3(ar, at, at))
			_move(sk, side + "Forearm", Vector3(ar, 1.0, 1.0))
			_move(sk, side + "ForeTwist", Vector3(ar, 1.0, 1.0))
			_move(sk, side + "ForeTwist1", Vector3(ar, 1.0, 1.0))
			_move(sk, side + "Hand", Vector3(ar, 1.0, 1.0))
			_scale(sk, side + "Hand", hn)
			_def(sk, side + "Thigh", Vector3(lg, tt, tt))
			_def(sk, side + "ThighTwist", Vector3(lg, tt, tt))
			_def(sk, side + "Calf", Vector3(lg, ct, ct))
			_move(sk, side + "Calf", Vector3(lg, 1.0, 1.0))
			_move(sk, side + "Foot", Vector3(lg, 1.0, 1.0))
		# longer legs: the hips up by what they gained, so the feet stay on the ground
		var pv: int = _b.get("Pelvis", -1)
		if pv >= 0 and absf(lg - 1.0) > 0.0005 and _leg > 0.0:
			var parent := sk.get_bone_parent(pv)
			var pb := sk.get_bone_global_pose(parent).basis if parent >= 0 else Basis()
			sk.set_bone_pose_position(pv, sk.get_bone_pose_position(pv) + pb.inverse() * (_up * _leg * (lg - 1.0)))
		_bulge(sk, v.call("chest_size"), v.call("glutes"))

	## Bust (pecs) and glutes: the parts' vertex shader swells the flesh round two points on the chest and two on the
	## seat (figure.json "body_marks", pipeline/body_marks.py) - no bone carries them alone. Material uniforms, each
	## figure's own (instance uniforms would take a slot in every NPC's every part).
	func _bulge(sk: Skeleton3D, bust: float, glutes: float) -> void:
		var marks: Dictionary = fig.meta.get("body_marks", {})
		if marks.is_empty() or (absf(bust) < 0.001 and absf(glutes) < 0.001 and not _bulged):
			return
		_bulged = absf(bust) > 0.001 or absf(glutes) > 0.001
		var g := sk.global_transform
		var pts: Array[Vector4] = []
		var dirs: Array[Vector3] = []
		var amts: Array[float] = []
		for k in [["bust", "Spine2", bust], ["glute", "Pelvis", glutes]]:
			var m: Dictionary = marks.get(k[0], {})
			var b: int = _b.get(k[1], -1)
			if m.is_empty() or b < 0:
				pts.append_array([Vector4.ZERO, Vector4.ZERO])
				dirs.append(Vector3.ZERO)
				amts.append(0.0)
				continue
			var t := g * sk.get_bone_global_pose(b)
			var r := float(m.r) * g.basis.get_scale().x
			for p in [m.l, m.rt]:
				var w := t * Vector3(p[0], p[1], p[2])
				pts.append(Vector4(w.x, w.y, w.z, r))
			var d: Array = m.dir
			dirs.append((t.basis * Vector3(d[0], d[1], d[2])).normalized())
			amts.append(float(k[2]))
		var vals := {"bulge_a": pts[0], "bulge_b": pts[1], "bulge_c": pts[2], "bulge_d": pts[3], "bulge_ab": dirs[0],
			"bulge_cd": dirs[1], "bulge_amt": Vector2(amts[0], amts[1])}
		for mi in fig.model.find_children("*", "MeshInstance3D", true, false):
			var mats: Array = [(mi as MeshInstance3D).material_override]
			for si in (mi as MeshInstance3D).get_surface_override_material_count():
				mats.append((mi as MeshInstance3D).get_surface_override_material(si))
			for m in mats:
				if m is ShaderMaterial:
					for k in vals:
						(m as ShaderMaterial).set_shader_parameter(k, vals[k])


class Layers extends SkeletonModifier3D:
	var fig: Fig3Figure
	var _w := 0.0
	var _t := 0.0
	var _clip := ""
	var _twist := 0.0
	var _ready_bones := false
	var _root := -1
	var _pelvis := -1
	var _spine := -1
	var _upper: Array[int] = []                  # Spine1, Spine2: the twist spread up the back
	var _thighs: Array[int] = []                 # (in this rig the thighs hang off the spine, not the pelvis)
	var _below: Array[int] = []                  # calves, feet, toes, thigh twists, the pelvis' robe and belt bones
	var _tracks := {}                            # clip -> {bone: [rotation track, position track]}

	func _bones(sk: Skeleton3D) -> void:
		_ready_bones = true
		_root = sk.find_bone("Bip01")
		_pelvis = sk.find_bone("Bip01 Pelvis")
		_spine = sk.find_bone("Bip01 Spine")
		for n in ["Bip01 Spine1", "Bip01 Spine2"]:
			if sk.find_bone(n) >= 0:
				_upper.append(sk.find_bone(n))
		for side in ["L", "R"]:
			var th := sk.find_bone("Bip01 %s Thigh" % side)
			if th >= 0:
				_thighs.append(th)
			for n in ["Calf", "Foot", "Toe0", "ThighTwist", "Belt"]:
				var b := sk.find_bone("Bip01 %s %s" % [side, n])
				if b >= 0:
					_below.append(b)
		for n in ["Bip01 BackRobe 01", "Bip01 BackRobe 02", "Bip01 FrontRobe 01", "Bip01 FrontRobe 02"]:
			if sk.find_bone(n) >= 0:
				_below.append(sk.find_bone(n))

	func _map(sk: Skeleton3D, a: Animation, clip: String) -> Dictionary:
		if _tracks.has(clip):
			return _tracks[clip]
		var m := {}
		for t in a.get_track_count():
			var ty := a.track_get_type(t)
			if ty != Animation.TYPE_ROTATION_3D and ty != Animation.TYPE_POSITION_3D:
				continue
			var b := sk.find_bone(String(a.track_get_path(t).get_concatenated_subnames()))
			if b < 0:
				continue
			if not m.has(b):
				m[b] = [-1, -1]
			m[b][0 if ty == Animation.TYPE_ROTATION_3D else 1] = t
		_tracks[clip] = m
		return m

	## A bone's pose in the legs' clip (its rest where the clip has no track; its scale as it is now).
	func _local(sk: Skeleton3D, a: Animation, m: Dictionary, b: int) -> Transform3D:
		var rest := sk.get_bone_rest(b)
		var q := rest.basis.get_rotation_quaternion()
		var p := rest.origin
		if m.has(b):
			if m[b][0] >= 0:
				q = a.rotation_track_interpolate(m[b][0], _t)
			if m[b][1] >= 0:
				p = a.position_track_interpolate(m[b][1], _t)
		return Transform3D(Basis(q).scaled(sk.get_bone_pose_scale(b)), p)

	func _set_local(sk: Skeleton3D, b: int, want: Transform3D, w: float, pos: bool) -> void:
		var q0 := sk.get_bone_pose_rotation(b)
		sk.set_bone_pose_rotation(b, q0.slerp(want.basis.get_rotation_quaternion(), w))
		if pos:
			sk.set_bone_pose_position(b, sk.get_bone_pose_position(b).lerp(want.origin, w))

	## The bone's world (skeleton-space) pose made `want` - by w - through its local pose.
	func _set_global(sk: Skeleton3D, b: int, want: Transform3D, w: float) -> void:
		var g := sk.get_bone_global_pose(b)
		var ng := g.interpolate_with(want, w)
		var p := sk.get_bone_parent(b)
		var pg := sk.get_bone_global_pose(p) if p >= 0 else Transform3D.IDENTITY
		var local := pg.affine_inverse() * ng
		sk.set_bone_pose_rotation(b, local.basis.get_rotation_quaternion())
		sk.set_bone_pose_position(b, local.origin)

	func _process_modification_with_delta(delta: float) -> void:
		var sk := get_skeleton()
		if sk == null or fig == null or fig.anim == null:
			return
		var anim := fig.anim
		var cur := String(anim.current_animation)
		if cur in LOCO_CLIPS:
			fig._loco_clip = cur
			fig._loco_t = anim.current_animation_position
		var want := fig.lower_clip != "" and anim.has_animation(fig.lower_clip)
		if want and fig.lower_clip != _clip:
			_t = fig._loco_t if fig._loco_clip == fig.lower_clip and _w <= 0.0 else (_t if _w > 0.0 else 0.0)
			_clip = fig.lower_clip
		_w = move_toward(_w, 1.0 if want else 0.0, delta / LOWER_FADE)
		if want:
			_twist = fig.lower_twist
		if _w <= 0.0 or _clip == "" or not anim.has_animation(_clip):
			_clip = "" if _w <= 0.0 else _clip
			return
		if not _ready_bones:
			_bones(sk)
		if _root < 0 or _pelvis < 0 or _spine < 0:
			return
		var a := anim.get_animation(_clip)
		if want:
			_t = fposmod(_t + delta * fig.lower_speed, maxf(a.length, 0.01))
			fig._lower_clip = _clip
			fig._lower_t = _t
			fig._lower_at = Time.get_ticks_msec()
		var w := smoothstep(0.0, 1.0, _w)
		var m := _map(sk, a, _clip)
		# the upper body as the action has it (before the hips change under it)
		var spine_was := sk.get_bone_global_pose(_spine)
		var l_root := _local(sk, a, m, _root)
		var l_pelvis := _local(sk, a, m, _pelvis)
		var l_spine := _local(sk, a, m, _spine)
		var spine_run := l_root * l_pelvis * l_spine
		var thigh_run: Array[Transform3D] = []
		for th in _thighs:
			thigh_run.append(spine_run * _local(sk, a, m, th))
		_set_local(sk, _root, l_root, w, true)
		_set_local(sk, _pelvis, l_pelvis, w, true)
		# the spine: the action's own turn of the upper body, on the legs' hips, turned back by half the twist
		var sb := sk.global_basis.orthonormalized()
		var up_w := (fig.model.global_basis * Vector3.UP).normalized() if fig.model else Vector3.UP
		var turn := func(ang: float) -> Basis:
			return sb.inverse() * Basis(up_w, ang) * sb
		_set_global(sk, _spine, Transform3D((turn.call(_twist * 0.5) as Basis) * spine_was.basis, spine_run.origin), w)
		for b in _upper:                                      # (and a quarter each further up)
			var g := sk.get_bone_global_pose(b)
			_set_global(sk, b, Transform3D((turn.call(_twist * 0.25) as Basis) * g.basis, g.origin), w)
		# the legs: where the legs' clip has them, whatever the back does above
		for i in _thighs.size():
			_set_global(sk, _thighs[i], thigh_run[i], w)
		for b in _below:
			_set_local(sk, b, _local(sk, a, m, b), w, false)


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
	var _spine: Array[int] = []                  # (the lean into a start, back from a stop: its bones and shares)
	var _spine_w: Array[float] = []
	var _fwd_v := 0.0                            # last frame's speed ahead
	var _lean := 0.0
	var _lean_v := 0.0
	var _vel := Vector3.ZERO                     # the figure's speed (world), measured between its moves
	var _vel_dt := 0.0
	var _vel_s := Vector3.ZERO
	# turning (owner 2026-11-09, "modernize the feel": the client's figures turn as one block, at once): the head turns
	# first and looks into the turn, the shoulders follow, the hips last; running through a curve the body banks in
	var _pelvis := -1
	var _neck_b := -1
	var _head_b := -1
	var _yaw := INF                              # the figure's facing (world, unwrapped: no jump at +-PI)
	var _yaw_raw := 0.0
	var _yaw_dt := 0.0
	var _om := 0.0                               # how fast it turns (rad/s, smoothed)
	var _lag := PackedFloat32Array([0.0, 0.0, 0.0])      # where the hips, the chest and the head face (world yaw)
	var _lag_v := PackedFloat32Array([0.0, 0.0, 0.0])
	var _bank := 0.0
	var _bank_v := 0.0
	# looking (owner 2026-11-09, step 2): the head turns to fig.look_point - where you look, your target, the player
	# an NPC is talking to - and back when it's behind; breathing and a slow sway when standing (more after a run)
	var _ly := 0.0
	var _ly_v := 0.0
	var _lp := 0.0
	var _lp_v := 0.0
	var _breath := 0.0                           # the breath's phase (rad)
	# the feet on uneven ground (step 3): standing, each foot is set on the ground under it - the body lowered to the
	# lower foot, the other leg bent to reach its ground (two-bone IK) - fading in as it comes to rest
	var _thigh: Array[int] = [-1, -1]
	var _calf: Array[int] = [-1, -1]
	var _foot: Array[int] = [-1, -1]
	var _root_b := -1
	var _ik_w := 0.0
	var _ik_d: Array[float] = [0.0, 0.0]
	var _planted := false                        # standing: each foot stays where it was set down ...
	var _plant_p: Array[Vector3] = [Vector3.ZERO, Vector3.ZERO]
	var _plant_b: Array[Basis] = [Basis(), Basis()]
	var _st: Array[float] = [-1.0, -1.0]          # ... until it steps (0..1 through the step; -1 planted) to where the body has it
	var _from_p: Array[Vector3] = [Vector3.ZERO, Vector3.ZERO]
	var _from_b: Array[Basis] = [Basis(), Basis()]
	var _winded := 0.0                           # 0..1: how hard it has been running lately

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
		_pelvis = sk.find_bone("Bip01 Pelvis")
		_neck_b = sk.find_bone("Bip01 Neck")
		_root_b = sk.find_bone("Bip01")
		for k in 2:
			var side: String = ["L", "R"][k]
			_thigh[k] = sk.find_bone("Bip01 %s Thigh" % side)
			_calf[k] = sk.find_bone("Bip01 %s Calf" % side)
			_foot[k] = sk.find_bone("Bip01 %s Foot" % side)
		_head_b = _neck
		for sw in [["Bip01 Spine1", 0.55], ["Bip01 Spine2", 0.45]]:
			var sb := sk.find_bone(String(sw[0]))
			if sb >= 0:
				_spine.append(sb)
				_spine_w.append(float(sw[1]))
		if _spine.is_empty() and sk.find_bone("Bip01 Spine") >= 0:
			_spine.append(sk.find_bone("Bip01 Spine"))
			_spine_w.append(1.0)
		var t := sk.find_bone("Bip01 Ponytail1")
		if t >= 0:
			_tails.append(t)
		_phase = float(get_instance_id() % 997) * 0.37

	func _process_modification_with_delta(delta: float) -> void:
		var sk := get_skeleton()
		if sk == null or not Fig3Figure.sway_on or model == null:
			_last = Vector3.INF
			_still_hair()
			if fig:
				fig._near = false
			return
		if not _ready_bones:
			_bones(sk)
		var pos := sk.global_position
		var cam := get_viewport().get_camera_3d() if is_inside_tree() else null
		if cam and cam.global_position.distance_to(pos) > SWAY_RANGE_M:
			_last = Vector3.INF
			_still_hair()
			if fig:
				fig._near = false
			return
		var dt := maxf(delta, 0.001)
		if fig:
			fig._near = true
		var fresh := _last == Vector3.INF                      # (first frame in range: no change in speed to read)
		# the speed between moves, not between frames: you move 60 times a second (the physics), the frames come at
		# up to 165 - read frame to frame the speed flickers (0, 0, 2.7x ...) and set the lean and hair shaking
		# (owner 2026-11-09: "a jittery quality to movement now"); an NPC's place comes in steps too
		if fresh:
			_vel = Vector3.ZERO
			_vel_dt = 0.0
			_last = pos
		else:
			_vel_dt += dt
			if pos.distance_squared_to(_last) > 1e-8 or _vel_dt > 0.12:
				_vel = (pos - _last) / _vel_dt
				_vel_dt = 0.0
				_last = pos
				if _vel.length() > 25.0:
					_vel = Vector3.ZERO                        # (a teleport, a zone change)
		# (and smoothed: a move lands 2 or 3 frames after the last, so even between moves it reads +-25 %)
		_vel_s = _vel if fresh else _vel_s.lerp(_vel, 1.0 - exp(-dt * 12.0))
		var vel := _vel_s
		# the model faces +Z in its own space (as the converted figures do); in the skeleton's space:
		var to_skel := sk.global_basis.orthonormalized().inverse() * model.global_basis.orthonormalized()
		var fwd := (to_skel * Vector3(0, 0, 1)).normalized()
		var up := (to_skel * Vector3.UP).normalized()
		var right := up.cross(fwd).normalized()
		var v := model.global_basis.orthonormalized().inverse() * vel
		var t := Time.get_ticks_msec() / 1000.0
		var breeze := Fig3Figure.wind * (0.03 + 0.025 * sin(t * 1.3 + _phase) + 0.015 * sin(t * 3.1 + _phase * 2.0))
		var want_back := clampf(v.z * 0.05, 0.0, 0.35) + maxf(breeze, 0.0)
		# starting and stopping (owner 2026-11-08: "a little of the momentum reflected in the animations and movement of
		# the hair and cloaks" - the controls stay tight, the figure only looks it): the change in speed ahead kicks
		# the body - a lean into the first stride, a rock back as it stops, settling with one soft overshoot - and the
		# hair and cloak, which catch up late and swing on past
		# (the speed ahead smoothed a little first: an NPC's position comes in steps)
		var fwd_s := v.z if fresh else lerpf(_fwd_v, v.z, 1.0 - exp(-dt * 14.0))
		var dv := 0.0 if fresh else clampf(fwd_s - _fwd_v, -9.0, 9.0)
		_fwd_v = fwd_s
		# (a stop kicks a third as hard as a start: owner 2026-11-09, "an awkward bounce back as Arthur stops")
		# (a start leans into the run; a stop pitches the body forward over its feet - owner 2026-11-09: the stop
		# leaned the wrong way, back)
		_lean_v += dv * 0.16 if dv > 0.0 else -dv * 0.05
		_back_v += dv * (0.06 if dv > 0.0 else 0.035)
		var want_side := clampf(-v.x * 0.03, -0.15, 0.15) + Fig3Figure.wind * 0.02 * sin(t * 0.9 + _phase)
		# springs (a little under-damped: one soft overshoot as it settles) - in steps of a 60th of a second at
		# most, so a slow frame (a crowded town) can't set them shaking
		var sdt := minf(dt, 0.25)                             # (a hitch: no more than a quarter second at once)
		var steps := ceili(sdt * 60.0)
		var h := sdt / steps
		for _i in steps:
			_lean_v += (-_lean * 70.0 - _lean_v * 13.5) * h            # (nearly critical: no rock past upright)
			_lean += _lean_v * h
			_back_v += ((want_back - _back) * 40.0 - _back_v * 6.5) * h      # (a soft swing on past as it settles)
			_back += _back_v * h
			_side_v += ((want_side - _side) * 30.0 - _side_v * 8.0) * h
			_side += _side_v * h
		_lean = clampf(_lean, -0.14, 0.14)
		var back := clampf(_back, 0.0, 0.45)                   # never forward, into the legs
		var back_h := clampf(_back, -0.12, 0.45)               # (hair may swing a little forward past the head)
		var side_ang := clampf(_side, -0.2, 0.2)
		var axis_back := up.cross(fwd).normalized()           # + swings the lower end back (away from the body)
		_turning(sk, dt, fresh, fwd_s)
		_brake(sk)
		_feet(sk, dt)
		for i in _spine.size():                               # (first: the cloak and hair hang off the leaning back;
			_turn(sk, _spine[i], axis_back, _lean * _spine_w[i], fwd, 0.0)    # + tips the upper body forward)
		# a shield, a two-hander, a slung bow or a quiver on the back: the cloak hangs as the animation has it (owner
		# 2026-11-03: they clipped through the swinging cloak); it swings again once the back is clear
		if fig == null or not fig.back_gear:
			for b in _cloaks:
				_turn(sk, b, axis_back, back, fwd, side_ang)
			for b in _cloaks_mid:
				_turn(sk, b, axis_back, back * 0.35, fwd, side_ang * 0.5)
		for b in _tails:
			_turn(sk, b, axis_back, back_h * 0.8, fwd, side_ang * 1.2)
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
			hm.set_shader_parameter("sway_dir", back_w * (sin(back_h) * 0.75 + absf(bob)) + side_w * (sin(side_ang) * 0.6 + swish)
					+ up_w * bob)
			_hair_live = true

	const LOOK_W := 7.0                          # how quickly the head turns to look (rad/s spring)
	const LOOK_YAW := 1.15                       # as far as the head turns (rad, ~65 deg) ...
	const LOOK_UP := 0.4
	const LOOK_DOWN := 0.35
	const LOOK_GIVE_UP := 1.95                   # ... and past this (~110 deg: behind) it looks ahead again
	const TURN_W := [13.0, 19.0, 30.0]          # how quickly the hips, the chest, the head catch up (rad/s springs)
	const TURN_MAX := 1.2                        # never further behind than this (rad): a snap past it is partly at once
	const TURN_FF := 4.0                         # a steady turn up to this (rad/s - the turn keys) is followed with
	                                             # no lag at all: only a sudden change of facing (the mouse, a strafe,
	                                             # an NPC turning to you) shows the body coming round

	func _turning(sk: Skeleton3D, dt: float, fresh: bool, fwd_speed: float) -> void:
		var f := model.global_basis * Vector3(0, 0, 1)
		var raw := atan2(f.x, f.z)
		var cur := String(fig.anim.current_animation) if fig and fig.anim else ""
		var off := cur.begins_with("ride") or cur.begins_with("sit") or cur.begins_with("death") or cur.begins_with("lie")
		if fresh or _yaw == INF or off:
			_yaw = raw
			_yaw_raw = raw
			_yaw_dt = 0.0
			_om = 0.0
			for i in 3:
				_lag[i] = raw
				_lag_v[i] = 0.0
			_bank = 0.0
			_bank_v = 0.0
			return
		# (the facing changes in steps too: its rate read between changes, as the speed)
		_yaw_dt += dt
		var dy := wrapf(raw - _yaw_raw, -PI, PI)
		if absf(dy) > 1e-5 or _yaw_dt > 0.12:
			var om_raw := dy / _yaw_dt
			_yaw += dy
			_yaw_raw = raw
			_yaw_dt = 0.0
			_om = lerpf(_om, clampf(om_raw, -12.0, 12.0), 0.5)
		elif _yaw_dt > 0.035:
			# no change for two physics ticks: the turn has stopped - at once, not over half a second (owner 2026-11-09:
			# its fading rate kept pushing the body round past where it faced, then it sprang back - a rubber band)
			_om = lerpf(_om, 0.0, 1.0 - exp(-dt * 40.0))
		var ff := clampf(_om, -TURN_FF, TURN_FF)
		var lat := _om * fwd_speed                         # sideways pull running through a curve (m/s2)
		var want_bank := clampf(atan(lat / 9.8) * 0.3, -0.17, 0.17)
		var sdt := minf(dt, 0.25)
		var steps := ceili(sdt * 120.0)
		var h := sdt / steps
		for _i in steps:
			for i in 3:
				var w: float = TURN_W[i]
				var before := _yaw - _lag[i]
				_lag_v[i] += (w * w * before + 2.0 * w * (ff - _lag_v[i])) * h
				_lag[i] += _lag_v[i] * h
				# never past where it faces: catching up, a part that would go by stops there (no swing back)
				if absf(ff) < 0.05 and before * (_yaw - _lag[i]) < 0.0:
					_lag[i] = _yaw
					_lag_v[i] = 0.0
			_bank_v += ((want_bank - _bank) * 90.0 - _bank_v * 19.0) * h     # (critically damped: no lean past upright)
			_bank += _bank_v * h
		for i in 3:
			var d := clampf(_lag[i] - _yaw, -TURN_MAX, TURN_MAX)
			_lag[i] = _yaw + d
		var d_hips := _lag[0] - _yaw
		var d_chest := _lag[1] - _lag[0] + clampf(_om * 0.04, -0.12, 0.12)        # (and a look into the turn)
		var d_head := _lag[2] - _lag[1] + clampf(_om * 0.08, -0.3, 0.3)
		var up_w := (model.global_basis * Vector3.UP).normalized()
		# the look: toward fig.look_point from the chest's facing, within what a neck can turn; behind - straight ahead
		var want_ly := 0.0
		var want_lp := 0.0
		var chest_yaw := _lag[1] + (fig.lower_twist if fig.lower_clip != "" else 0.0)
		if fig.look_point != Vector3.INF and _head_b >= 0:
			var hw := sk.global_transform * sk.get_bone_global_pose(_head_b).origin
			var dv := fig.look_point - hw
			var flat := Vector2(dv.x, dv.z).length()
			if flat > 0.25:
				var rel := wrapf(atan2(dv.x, dv.z) - chest_yaw, -PI, PI)
				if absf(rel) < LOOK_GIVE_UP:
					want_ly = clampf(rel, -LOOK_YAW, LOOK_YAW)
					want_lp = clampf(atan2(dv.y, flat), -LOOK_DOWN, LOOK_UP) * (1.0 - absf(want_ly) / (LOOK_YAW * 2.0))
		for _i in steps:
			_ly_v += (LOOK_W * LOOK_W * (want_ly - _ly) - 2.0 * LOOK_W * _ly_v) * h
			_ly += _ly_v * h
			_lp_v += (LOOK_W * LOOK_W * (want_lp - _lp) - 2.0 * LOOK_W * _lp_v) * h
			_lp += _lp_v * h
		d_head += _ly
		var side_w := up_w.cross(f.normalized()).normalized()          # the way a left turn pulls (the model's +X)
		# the hips: turned, and banked about the ground under them (not the hips: the feet would lift)
		if _pelvis >= 0:
			var r := Basis(up_w.cross(side_w).normalized(), _bank) * Basis(up_w, d_hips)
			_world_turn(sk, _pelvis, r, true)
		for i in _spine.size():
			_world_turn(sk, _spine[i], Basis(up_w, d_chest * _spine_w[i]), false)
		# (the nod about the head's own side axis once it has turned; + up: a turn about +X tips +Z down)
		var nod_axis := Basis(up_w, chest_yaw + d_head) * Vector3(1, 0, 0)
		if _neck_b >= 0 and _head_b >= 0:
			_world_turn(sk, _neck_b, Basis(nod_axis, -_lp * 0.4) * Basis(up_w, d_head * 0.4), false)
			_world_turn(sk, _head_b, Basis(nod_axis, -_lp * 0.6) * Basis(up_w, d_head * 0.6), false)
		elif _head_b >= 0:
			_world_turn(sk, _head_b, Basis(nod_axis, -_lp) * Basis(up_w, d_head), false)
		# breathing and the standing sway: the chest rises a little (quicker and deeper after a run), the upper body
		# drifts slowly side to side - fading out as it moves
		var still := 1.0 - clampf(_vel_s.length() / 2.0, 0.0, 1.0)
		_winded = clampf(_winded + dt * (0.12 if _vel_s.length() > 3.5 else -0.07), 0.0, 1.0)
		_breath = fposmod(_breath + dt * TAU * (0.26 + 0.32 * _winded), TAU)
		if still > 0.0 and _spine.size() > 0:
			var chest_fwd := Basis(up_w, chest_yaw) * Vector3(0, 0, 1)
			var chest_side := Basis(up_w, chest_yaw) * Vector3(1, 0, 0)
			var lift := (0.5 - 0.5 * cos(_breath)) * (0.018 + 0.03 * _winded) * still
			var t_s := Time.get_ticks_msec() / 1000.0
			var drift := (sin(t_s * 0.95 + _phase) * 0.6 + sin(t_s * 0.41 + _phase * 1.7) * 0.4) * 0.014 * still
			_world_turn(sk, _spine[_spine.size() - 1], Basis(chest_side, -lift) * Basis(chest_fwd, drift), false)

	const FEET_MAX := 0.4                        # metres: no more than this up or down to the ground under a foot
	const FEET_FADE := 0.25                      # seconds to come in / go out
	const STEP_DIST := 0.16                      # metres a planted foot may be left from where the body has it ...
	const STEP_TURN := 0.6                       # ... or turned from it (rad, ~35 deg) before it steps
	const STEP_SECONDS := 0.2
	const STEP_LIFT := 0.07
	const FLICK := 6.0                           # rad/s: turning faster, the feet go round with the body

	## The ground's height under a point (world): the terrain and the floors (as Player._floor_below); -INF: none.
	func _ground(p: Vector3) -> float:
		var start := p.y + FEET_MAX + 0.3
		var best := -INF
		var src: Object = Fig3Figure.ground_src
		if src != null and is_instance_valid(src) and not Fig3Figure.ground_city and src.has_method("height_at"):
			var t: float = src.call("height_at", p.x, p.z, p.y)
			if t <= start:
				best = t
		if is_inside_tree():
			var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, start, p.z), Vector3(p.x, p.y - FEET_MAX - 0.3, p.z),
					ZoneLoader.LAYER_FLOOR)
			q.hit_back_faces = false
			var hit := get_world_3d().direct_space_state.intersect_ray(q)
			if hit and float(hit.position.y) > best:
				best = hit.position.y
		return best

	func _feet(sk: Skeleton3D, dt: float) -> void:
		if _foot[0] < 0 or _foot[1] < 0 or _thigh[0] < 0 or _thigh[1] < 0 or _calf[0] < 0 or _calf[1] < 0 or _root_b < 0:
			return
		var cur := String(fig.anim.current_animation) if fig and fig.anim else ""
		var ok := _vel_s.length() < 0.5 and Fig3Figure.ground_src != null and not (cur.begins_with("ride") \
				or cur.begins_with("sit") or cur == "swim" or cur.begins_with("death") or cur == "jump" or cur == "land" \
				or cur.begins_with("lie") or cur == "ladder") and fig.lower_clip == "" \
				and (Fig3Figure.idle_like(cur) or AnimStyle.group_of(cur) == "aim")   # (a swing's own footwork plays)
		_ik_w = move_toward(_ik_w, 1.0 if ok else 0.0, dt / FEET_FADE)
		var xf := sk.global_transform
		# where the clip has the feet now (world) - and their turn
		var nat_p: Array[Vector3] = []
		var nat_b: Array[Basis] = []
		for k in 2:
			var g := sk.get_bone_global_pose(_foot[k])
			nat_p.append(xf * g.origin)
			nat_b.append(xf.basis * g.basis)
		if _ik_w <= 0.0 or not ok:
			_planted = false                                  # (moving: the feet go with the clip)
			_st[0] = -1.0
			_st[1] = -1.0
		elif not _planted:
			_planted = true                                   # (coming to rest: the feet plant where they are)
			_st[0] = -1.0
			_st[1] = -1.0
			for k in 2:
				_plant_p[k] = nat_p[k]
				_plant_b[k] = nat_b[k]
		if _ik_w <= 0.0:
			_ik_d[0] = 0.0
			_ik_d[1] = 0.0
			return
		# planted: a foot left too far from where the body now has it (the body turned or shifted over it) steps there -
		# a quick lift and set down, one foot at a time, the one further off first (owner 2026-11-09: turning on the spot
		# with the walk clip stepping in place looked floaty)
		var want_p: Array[Vector3] = [nat_p[0], nat_p[1]]
		var want_b: Array[Basis] = [nat_b[0], nat_b[1]]
		var lift: Array[float] = [0.0, 0.0]
		if _planted:
			# quicker steps the faster it turns, the next foot off as the last comes down; a flick - the feet just go round
			var fast := absf(_om)
			var secs := lerpf(STEP_SECONDS, 0.12, clampf((fast - 1.0) / 3.0, 0.0, 1.0))
			var need := lerpf(1.0, 0.6, clampf(fast / 3.0, 0.0, 1.0))
			for k in 2:
				if _st[k] >= 0.0:
					_st[k] += dt / secs
					if _st[k] >= 1.0:
						_plant_p[k] = nat_p[k]
						_plant_b[k] = nat_b[k]
						_st[k] = -1.0
			var worst := -1
			var worst_e := need
			for k in 2:
				if _st[k] >= 0.0 or _st[1 - k] >= 0.0 and _st[1 - k] < 0.5:
					continue
				var off := Vector2(_plant_p[k].x - nat_p[k].x, _plant_p[k].z - nat_p[k].z).length() / STEP_DIST
				var fa := (_plant_b[k] * Vector3(0, 0, 1)).normalized()
				var fb := (nat_b[k] * Vector3(0, 0, 1)).normalized()
				var e := maxf(off, absf(Vector2(fa.x, fa.z).angle_to(Vector2(fb.x, fb.z))) / STEP_TURN)
				if e > worst_e:
					worst_e = e
					worst = k
			if worst >= 0:
				_st[worst] = 0.0
				_from_p[worst] = _plant_p[worst]
				_from_b[worst] = _plant_b[worst]
			for k in 2:
				if fast > FLICK:
					_plant_p[k] = nat_p[k]                       # (a flick round: no planting till it slows)
					_plant_b[k] = nat_b[k]
					_st[k] = -1.0
				elif _st[k] >= 0.0:
					var u := smoothstep(0.0, 1.0, _st[k])
					want_p[k] = _from_p[k].lerp(nat_p[k], u)
					want_b[k] = Basis(_from_b[k].get_rotation_quaternion().slerp(nat_b[k].get_rotation_quaternion(), u)).scaled(nat_b[k].get_scale())
					lift[k] = sin(PI * clampf(_st[k], 0.0, 1.0)) * STEP_LIFT
				else:
					want_p[k] = _plant_p[k]
					want_b[k] = _plant_b[k]
		var su := 1.0 / maxf(xf.basis.get_scale().y, 0.001)          # (metres to the skeleton's units)
		var up_s := (xf.basis.inverse() * Vector3.UP).normalized()
		var base_y := model.global_position.y
		var d: Array[float] = [0.0, 0.0]
		for k in 2:
			var g := _ground(Vector3(want_p[k].x, base_y, want_p[k].z))
			var wnt := 0.0 if g == -INF else clampf(g - base_y, -FEET_MAX, FEET_MAX)
			_ik_d[k] = lerpf(_ik_d[k], wnt, clampf(dt * 12.0, 0.0, 1.0))
			d[k] = _ik_d[k] * _ik_w
		var body := clampf(minf(d[0], d[1]), -FEET_MAX * 0.9, 0.2)    # the body down to the lower foot (or up)
		if absf(body) > 0.0005:
			sk.set_bone_pose_position(_root_b, sk.get_bone_pose_position(_root_b) + up_s * body * su)
		var inv := xf.affine_inverse()
		for k in 2:
			# the foot's place: where it is planted (or stepping), on its ground, from where the clip puts it - by the weight
			var tw := Vector3(want_p[k].x, nat_p[k].y + d[k] + lift[k] * _ik_w, want_p[k].z)
			tw = nat_p[k].lerp(tw, _ik_w) + Vector3.UP * 0.0
			var now_s := sk.get_bone_global_pose(_foot[k]).origin
			var delta := inv * tw - now_s
			if delta.length() > 0.0005:
				_two_bone(sk, k, delta)
			var g := sk.get_bone_global_pose(_foot[k])
			var fb: Basis = xf.basis.inverse() * want_b[k]
			var keep := Basis(g.basis.get_rotation_quaternion().slerp(fb.get_rotation_quaternion(), _ik_w)).scaled(g.basis.get_scale())
			_skel_set(sk, _foot[k], Transform3D(keep, g.origin))

	# the brake (owner 2026-11-09, GW2: "plant a foot down, stopping her forward momentum, then resettle into the
	# idle ... you could really feel the character stop based on how her feet planted"): through a stop clip the front
	# foot stays where it came down, the knees give and the hips drop, the upper body leans back against the stop, then
	# rocks a little forward; the planted foot lets go and steps back into the stance as the clip settles
	const BRAKE_DROP := 0.025                    # metres the hips drop at the hardest of a stop from a run
	const BRAKE_LEAN := 0.15                     # rad the upper body pitches forward over the planted foot
	const BRAKE_SETTLE := 0.05                   # rad it settles back past upright after
	var _brake_clip := ""
	var _brake_p := Vector3.ZERO                 # (the figure's own space)
	var _brake_set := false

	func _brake(sk: Skeleton3D) -> void:
		var cur := String(fig.anim.current_animation) if fig and fig.anim else ""
		if not Fig3Figure.is_stop_clip(cur) or _foot[0] < 0 or _foot[1] < 0 or _root_b < 0:
			_brake_clip = ""
			return
		var a := fig.anim.get_animation(cur)
		if a == null or a.length <= 0.0:
			return
		var u := clampf(fig.anim.current_animation_position / a.length, 0.0, 1.0)
		var k := 0 if cur.contains("_stop_l") else 1                  # (the foot that planted: the stop's own)
		var xf := sk.global_transform
		if cur != _brake_clip:
			_brake_clip = cur
			_brake_set = false
		# the front foot pinned where it came down - once the stop has blended in to its own first pose (not at its
		# first frame, mid-stride) - through the hold, so the body settling over it doesn't drag it (owner: a slide)
		if not _brake_set and u >= 0.14:
			_brake_set = true
			_brake_p = model.global_transform.affine_inverse() * (xf * sk.get_bone_global_pose(_foot[k]).origin)
		var pin := smoothstep(0.1, 0.16, u) * (1.0 - smoothstep(AnimStyle.STOP_HOLD, AnimStyle.STOP_HOLD + 0.2, u)) \
				if _brake_set else 0.0
		var amt := 1.0 if cur.begins_with("run") else 0.45
		var b := sin(PI * clampf(u / 0.42, 0.0, 1.0)) * amt                     # the brake: in hard, out by 42 %
		var settle := sin(PI * clampf((u - 0.28) / 0.42, 0.0, 1.0)) * amt       # then the rock forward
		var hold := 1.0 - smoothstep(0.55, 0.85, u)                               # the planted foot lets go late
		# where the clip has the feet (world), and their turn, before the body drops
		var nat_p: Array[Vector3] = []
		var nat_b: Array[Basis] = []
		for i in 2:
			var g := sk.get_bone_global_pose(_foot[i])
			nat_p.append(xf * g.origin)
			nat_b.append(g.basis)
		var su := 1.0 / maxf(xf.basis.get_scale().y, 0.001)
		var up_s := (xf.basis.inverse() * Vector3.UP).normalized()
		sk.set_bone_pose_position(_root_b, sk.get_bone_pose_position(_root_b) - up_s * BRAKE_DROP * b * su)
		var up_w := (model.global_basis * Vector3.UP).normalized()
		var side_w := (model.global_basis * Vector3(1, 0, 0)).normalized()
		var back := BRAKE_LEAN * b - BRAKE_SETTLE * settle                     # (+ about the side axis tips forward:
		                                                                       # the momentum pitches it over, then back)
		for i in _spine.size():
			_world_turn(sk, _spine[i], Basis(side_w, back * _spine_w[i]), false)
		if _neck_b >= 0:
			_world_turn(sk, _neck_b, Basis(side_w, -back * 0.5), false)       # (the head keeps its eyes ahead)
		var inv := xf.affine_inverse()
		for i in 2:
			var tw := nat_p[i]                         # (the feet where the clip has them - the knees take the drop)
			if i == k and pin > 0.0:
				# pinned where it came down - and ON the ground: the run's contact frame has the foot a little above it
				# (owner 2026-11-09: "the foot also stops in the air")
				var pw := model.global_transform * _brake_p
				var g: Dictionary = Fig3Figure._gaits.get(fig.race + "/" + cur.get_slice("_", 0), {})
				var fy := nat_p[i].y
				if g.has("floor"):
					fy = (xf * (up_s * float(g["floor"]))).y
				tw = nat_p[i].lerp(Vector3(pw.x, fy, pw.z), pin)
			var now_s := sk.get_bone_global_pose(_foot[i]).origin
			var delta := inv * tw - now_s
			if delta.length() > 0.0005:
				_two_bone(sk, i, delta)
			var g := sk.get_bone_global_pose(_foot[i])
			_skel_set(sk, _foot[i], Transform3D(nat_b[i], g.origin))

	## The leg (thigh, calf) bent so the foot moves by `delta` (skeleton space), the knee in its own plane.
	func _two_bone(sk: Skeleton3D, k: int, delta: Vector3) -> void:
		var h := sk.get_bone_global_pose(_thigh[k]).origin
		var kn := sk.get_bone_global_pose(_calf[k]).origin
		var an := sk.get_bone_global_pose(_foot[k]).origin
		var tg := an + delta
		var a := h.distance_to(kn)
		var b := kn.distance_to(an)
		if a < 1e-4 or b < 1e-4:
			return
		var c := clampf(h.distance_to(tg), absf(a - b) + 1e-3, a + b - 1e-3)
		var n := (kn - h).cross(an - h)
		if n.length() < 1e-6:
			return                                               # (a straight leg: no plane to bend in - leave it)
		n = n.normalized()
		var want_k := acos(clampf((a * a + b * b - c * c) / (2.0 * a * b), -1.0, 1.0))
		var cur_k := (h - kn).angle_to(an - kn)
		var r1 := Basis(n, want_k - cur_k)
		var r2 := Basis(n, cur_k - want_k)
		var e1 := absf((h - kn).angle_to(r1 * (an - kn)) - want_k)
		var e2 := absf((h - kn).angle_to(r2 * (an - kn)) - want_k)
		_skel_turn(sk, _calf[k], r1 if e1 <= e2 else r2)
		var an2 := sk.get_bone_global_pose(_foot[k]).origin
		var from := (an2 - h).normalized()
		var to := (tg - h).normalized()
		if from.dot(to) < 0.99999:
			_skel_turn(sk, _thigh[k], Basis(Quaternion(from, to)))

	func _skel_turn(sk: Skeleton3D, b: int, r: Basis) -> void:
		var g := sk.get_bone_global_pose(b)
		_skel_set(sk, b, Transform3D(r * g.basis, g.origin))

	func _skel_set(sk: Skeleton3D, b: int, ng: Transform3D) -> void:
		var p := sk.get_bone_parent(b)
		var pg := sk.get_bone_global_pose(p) if p >= 0 else Transform3D.IDENTITY
		var local := pg.affine_inverse() * ng
		sk.set_bone_pose_rotation(b, local.basis.get_rotation_quaternion())

	## A bone turned by `r` (a turn in the world), about its own joint or (ground) about the ground under it.
	func _world_turn(sk: Skeleton3D, b: int, r: Basis, ground: bool) -> void:
		var sb := sk.global_basis.orthonormalized()
		var rs := sb.inverse() * r * sb                  # the same turn in the skeleton's space
		var g := sk.get_bone_global_pose(b)
		var origin := g.origin
		if ground:
			var up_s := (sb.inverse() * (model.global_basis * Vector3.UP)).normalized()
			var foot := sk.global_transform.affine_inverse() * model.global_position   # the figure's feet, in skeleton space
			var pivot := origin - up_s * (origin - foot).dot(up_s)
			origin = pivot + rs * (origin - pivot)
		var ng := Transform3D(rs * g.basis, origin)
		var p := sk.get_bone_parent(b)
		var pg := sk.get_bone_global_pose(p) if p >= 0 else Transform3D.IDENTITY
		var local := pg.affine_inverse() * ng
		sk.set_bone_pose_rotation(b, local.basis.get_rotation_quaternion())
		if ground:
			sk.set_bone_pose_position(b, local.origin)

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
