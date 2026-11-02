extends RefCounted
## Personal mounts (owner 2026-11-02, mounts' first pass: "make sure it works in the modern movement system and in the
## action combat system ... bots will need to want to purchase and use mounts too"). The server says who rides what
## with ControlledHorse (0x4E: rider object id, horse id - gamedata horsemap.csv's ID, 0 = off) and PlayerCreate's
## tail; the rider keeps moving itself (you: the modern / classic movement as ever, at the server's speed - MaxSpeed's
## percent; bots: their server positions) while a horse model walks under it and the rider sits in the saddle.
##
## horsemap.csv names a Catacombs monster model per horse (2033 standard, 2035 heavy, 2037 unicorn ...) - part horses
## (Body01_Mount_Horse, its saddle and barding) whose meshes this client doesn't carry; monsters.csv draws them all
## with the classic saddled horse (Classic_Body01_Mount_Horse), so the standard and heavy horses are that horse in
## their own coat: pipeline/build_mount_coats.py writes every coat that fits its body (brown, black, white, grey,
## palomino, spotted, chocolate, clydesdale, appaloosa, dappled grey, leopard, duns, shire dappled, strawberry roan,
## arboreal) beside it, with mount_coats.json (horse id -> coat), and make() swaps it in. The unicorns, the nightmare,
## the epic and the flying mounts keep the nearest model of their own.

const SADDLED := "2173"                       # Brown Horse w/ Saddle (Classic_Body01_Mount_Horse)
const BY_ID := {
	33: "463", 35: "463", 36: "463", 37: "463", 38: "463", 39: "463", 40: "463", 41: "463", 55: "463",   # unicorns
	34: "464",                                # black unicorn
	49: "2224", 50: "2227", 53: "2231",      # nightmare, undead, flame
	51: "2230", 52: "2225",                   # storm, frost
	56: "2257", 54: "2258",                   # sea horse, earth
	61: "1207", 62: "1235", 63: "1236",       # dragonfly, wyvern, gryphon
}
const COATS_JSON := "res://content/monsters/mount_coats.json"
const COAT_DIR := "res://content/monsters/classic_body01_mount_horse__horse_medium_brown/coats"
const SEAT_DEFAULT := 1.35                    # metres up to the saddle when the model has no saddle node


static var _coats := {}                      # horse id (String) -> coat name; read once
static var _coat_tex := {}                   # coat name -> ImageTexture (shared by every horse in that coat)


static func model_key(horse_id: int) -> String:
	return String(BY_ID.get(horse_id, SADDLED))


## The coat a horse wears on the saddled horse ("" for its own brown, or for a horse drawn with another model).
static func coat(horse_id: int) -> String:
	if BY_ID.has(horse_id):
		return ""
	if _coats.is_empty() and FileAccess.file_exists(COATS_JSON):
		var d = JSON.parse_string(FileAccess.get_file_as_string(COATS_JSON))
		_coats = d if d is Dictionary else {"": ""}
	var c := String(_coats.get(str(horse_id), ""))
	return "" if c == "horse_medium_brown" else c


static func _coat_texture(name: String) -> Texture2D:
	if _coat_tex.has(name):
		return _coat_tex[name]
	var tex: Texture2D = null
	for sub in ["x4plus", "original"]:
		var path := "%s/%s/%s.png" % [COAT_DIR, sub, name]
		if FileAccess.file_exists(path):
			var img := Image.load_from_file(ProjectSettings.globalize_path(path))
			if img:
				img.generate_mipmaps()
				tex = ImageTexture.create_from_image(img)
				break
	_coat_tex[name] = tex
	return tex


## Every surface of the horse's model drawn with the coat (its own copy of each material, the shared model's stay).
static func _dress(model: Node, name: String) -> void:
	var tex := _coat_texture(name)
	if tex == null:
		return
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null:
			continue
		for i in m.mesh.get_surface_count():
			var mat := m.get_active_material(i) as BaseMaterial3D
			if mat == null:
				continue
			var own := mat.duplicate() as BaseMaterial3D
			own.albedo_texture = tex
			m.set_surface_override_material(i, own)


## A new horse under a rider: the monster model (monsters.json) in a holder, meta "anim" (its AnimationPlayer),
## "info" (its monsters.json entry), "horse" (the id). null when the model isn't built.
static func make(horse_id: int, mgr: NpcManager, models: Dictionary) -> Node3D:
	var info: Dictionary = models.get(model_key(horse_id), models.get(SADDLED, {}))
	if not info.has("gltf") or mgr == null:
		return null
	var m := mgr.instance_model(String(info.gltf))
	if m == null:
		return null
	var hide := coat(horse_id) if model_key(horse_id) == SADDLED else ""
	if hide != "":
		_dress(m, hide)
	var holder := Node3D.new()
	holder.name = "Mount"
	m.scale *= float(info.get("scale", 1.0))
	holder.add_child(m)
	var players := m.find_children("*", "AnimationPlayer", true, false)
	var ap: AnimationPlayer = players[0] if players.size() > 0 else null
	if ap:
		for c in ["idle", "walk", "run"]:
			if ap.has_animation(c):
				ap.get_animation(c).loop_mode = Animation.LOOP_LINEAR
		if ap.has_animation("idle"):
			ap.play("idle")
	holder.set_meta("anim", ap)
	holder.set_meta("info", info)
	holder.set_meta("horse", horse_id)
	holder.set_meta("coat", hide)
	holder.set_meta("seat", SEAT_DEFAULT * float(info.get("scale", 1.0)))
	return holder


## The saddle's height (metres) above the horse's feet: its model's saddle node once posed, else the default.
static func seat(holder: Node3D) -> float:
	if holder == null or not holder.is_inside_tree():
		return SEAT_DEFAULT
	var sn := holder.find_child("saddle*", true, false) as Node3D
	if sn:
		var y := (holder.global_transform.affine_inverse() * sn.global_position).y
		if y > 0.5:
			holder.set_meta("seat", y)
	return float(holder.get_meta("seat", SEAT_DEFAULT))


## The horse's legs: idle, walk or run, the run's pace matched to the ground speed (monsters.json strides).
static func animate(holder: Node3D, speed_mps: float) -> void:
	if holder == null:
		return
	var ap: AnimationPlayer = holder.get_meta("anim", null)
	if ap == null:
		return
	var info: Dictionary = holder.get_meta("info", {})
	var clip := "idle"
	if speed_mps > 4.5:
		clip = "run"
	elif speed_mps > 0.3:
		clip = "walk"
	if not ap.has_animation(clip):
		clip = "idle" if ap.has_animation("idle") else ""
	if clip == "":
		return
	var rate := 1.0
	var strides: Dictionary = info.get("strides_units", {})
	var secs = info.get("clip_seconds", {})
	if clip != "idle" and strides.has(clip) and secs is Dictionary and (secs as Dictionary).has(clip):
		var per_cycle := float(strides[clip]) * 0.025 / maxf(0.05, float(secs[clip]))   # metres a second at rate 1
		rate = clampf(speed_mps / maxf(0.1, per_cycle), 0.5, 2.5)
	if ap.current_animation != clip:
		ap.play(clip, 0.25)
	ap.speed_scale = rate
