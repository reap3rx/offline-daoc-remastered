extends RefCounted
## Personal mounts (owner 2026-11-02, mounts' first pass: "make sure it works in the modern movement system and in the
## action combat system ... bots will need to want to purchase and use mounts too"). The server says who rides what
## with ControlledHorse (0x4E: rider object id, horse id - gamedata horsemap.csv's ID, 0 = off) and PlayerCreate's
## tail; the rider keeps moving itself (you: the modern / classic movement as ever, at the server's speed - MaxSpeed's
## percent; bots: their server positions) while a horse model walks under it and the rider sits in the saddle.
##
## horsemap.csv names a Catacombs monster model per horse (2033 standard, 2035 heavy, 2037 unicorn, 2034 nightmare,
## 2036 undead): the client's fig3 horse (pipeline/build_cathorse.py: one skeleton, the five bodies, the saddle /
## armour and the barding, each shape its own node by material id) in the horse's coat (mount_coats.json, from
## fig3haircolormap) with the saddle shown (horsematerialmap's choice: ControlledHorse's saddle byte, 0 = the
## plain saddle). Without it (not built yet), the classic saddled horse (Classic_Body01_Mount_Horse) in the coat
## when it fits that body; the epic, sea horse and flying mounts keep the nearest model of their own (BY_ID).

const SADDLED := "2173"                       # Brown Horse w/ Saddle (Classic_Body01_Mount_Horse)
const BY_ID := {
	33: "463", 35: "463", 36: "463", 37: "463", 38: "463", 39: "463", 40: "463", 41: "463", 55: "463",   # unicorns
	34: "464",                                # black unicorn
	49: "2224", 50: "2227", 53: "2231",      # nightmare, undead, flame
	51: "2230", 52: "2225",                   # storm, frost
	56: "2257", 54: "2258",                   # sea horse, earth
	61: "1207", 62: "1235", 63: "1236",       # dragonfly, wyvern, gryphon
}
const CAT_DIR := "res://content/monsters/cathorse"
## horse id -> [Catacombs body, horsematerialmap row] (horsemap.csv's monster: 2033 / 2035 / 2037 ... 2034 / 2036)
const CAT_KIND := {
	1: ["horse", "48"], 2: ["horse", "48"], 3: ["horse", "48"], 4: ["horse", "48"], 5: ["horse", "48"],
	6: ["horse", "48"], 7: ["horse", "48"], 8: ["horse", "48"], 9: ["horse", "48"], 10: ["horse", "48"],
	11: ["horse", "48"], 12: ["horse", "48"], 13: ["horse", "48"], 14: ["horse", "48"], 15: ["horse", "48"],
	57: ["horse", "48"],
	17: ["clydesdale", "50"], 18: ["clydesdale", "50"], 19: ["clydesdale", "50"], 20: ["clydesdale", "50"],
	21: ["clydesdale", "50"], 22: ["clydesdale", "50"], 23: ["clydesdale", "50"], 24: ["clydesdale", "50"],
	25: ["clydesdale", "50"], 26: ["clydesdale", "50"], 27: ["clydesdale", "50"], 28: ["clydesdale", "50"],
	58: ["clydesdale", "50"],
	33: ["unicorn", "52"], 34: ["unicorn", "52"], 35: ["unicorn", "52"], 36: ["unicorn", "52"], 37: ["unicorn", "52"],
	38: ["unicorn", "52"], 39: ["unicorn", "52"], 40: ["unicorn", "52"], 41: ["unicorn", "52"], 55: ["unicorn", "52"],
	49: ["nightmare", "49"], 50: ["undead", "51"],
}
const COATS_JSON := "res://content/monsters/mount_coats.json"
const COAT_DIR := "res://content/monsters/classic_body01_mount_horse__horse_medium_brown/coats"
const SEAT_DEFAULT := 1.35                    # metres up to the saddle when the model has no saddle node


static var _coats := {}                      # horse id (String) -> coat name; read once
static var _coat_tex := {}                   # coat path -> ImageTexture (shared by every horse in that coat)
static var _cat := {}                        # cathorse.json ({} until read; {"missing": true} when not built)


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


static func _coat_texture(name: String, dir := COAT_DIR) -> Texture2D:
	var key := dir + "/" + name
	if _coat_tex.has(key):
		return _coat_tex[key]
	var tex: Texture2D = null
	for sub in ["x4plus", "original"]:
		var path := "%s/%s/%s.png" % [dir, sub, name]
		if FileAccess.file_exists(path):
			var img := Image.load_from_file(ProjectSettings.globalize_path(path))
			if img:
				img.generate_mipmaps()
				tex = ImageTexture.create_from_image(img)
				break
	_coat_tex[key] = tex
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


## cathorse.json (build_cathorse.py), {} when the Catacombs horse isn't built.
static func cat_info() -> Dictionary:
	if _cat.is_empty():
		var path := CAT_DIR + "/cathorse.json"
		var d = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
		_cat = d if d is Dictionary else {"missing": true}
	return {} if _cat.has("missing") else _cat


## The Catacombs horse dressed for this horse: its body (the others hidden), its coat on it, the saddle's shapes
## (horsematerialmap's armour choice; saddle 0 = the plain saddle) and no barding yet.
static func _dress_cat(m: Node, horse_id: int, saddle: int) -> String:
	var kind: Array = CAT_KIND[horse_id]
	var body := String(kind[0])
	var choices: Dictionary = (cat_info().get("choices", {}) as Dictionary).get(String(kind[1]), {})
	var armor_ids := []
	for ch in choices.get("armor", []):
		if int(ch.selection) == saddle:
			armor_ids = ch.ids
	if armor_ids.is_empty() and saddle != 0:
		for ch in choices.get("armor", []):
			if int(ch.selection) == 0:
				armor_ids = ch.ids
	var shown := {}
	for i in armor_ids:
		if int(i) > 0:
			shown[int(i)] = true
	if _coats.is_empty() and FileAccess.file_exists(COATS_JSON):
		var d = JSON.parse_string(FileAccess.get_file_as_string(COATS_JSON))
		_coats = d if d is Dictionary else {"": ""}
	var coat_name := String(_coats.get(str(horse_id), ""))
	var tex := _coat_texture(coat_name, CAT_DIR) if coat_name != "" else null
	for mi in m.find_children("*", "MeshInstance3D", true, false):
		var n := String(mi.name)
		if n.begins_with("body_"):
			var on := n.begins_with("body_%s_" % body)
			mi.visible = on
			if on and tex:
				var mesh := (mi as MeshInstance3D).mesh
				for i in (mesh.get_surface_count() if mesh else 0):
					var mat := (mi as MeshInstance3D).get_active_material(i) as BaseMaterial3D
					if mat:
						var own := mat.duplicate() as BaseMaterial3D
						own.albedo_texture = tex
						(mi as MeshInstance3D).set_surface_override_material(i, own)
		elif n.begins_with("armor_"):
			mi.visible = shown.has(int(n.trim_prefix("armor_").get_slice("_", 0)))
		elif n.begins_with("barding_"):
			mi.visible = false
	return coat_name


## A new horse under a rider: the Catacombs horse in its coat and saddle (else the monster model - monsters.json) in
## a holder, meta "anim" (its AnimationPlayer), "info" (strides, clip lengths), "horse" (the id). null when no model
## is built.
static func make(horse_id: int, mgr: NpcManager, models: Dictionary, saddle := 0) -> Node3D:
	if mgr == null:
		return null
	var info: Dictionary = {}
	var m: Node3D = null
	var hide := ""
	if CAT_KIND.has(horse_id) and not cat_info().is_empty():
		info = cat_info()
		m = mgr.instance_model(String(info.gltf))
		if m:
			hide = _dress_cat(m, horse_id, saddle)
	if m == null:
		info = models.get(model_key(horse_id), models.get(SADDLED, {}))
		if not info.has("gltf"):
			return null
		m = mgr.instance_model(String(info.gltf))
		if m == null:
			return null
		hide = coat(horse_id) if model_key(horse_id) == SADDLED else ""
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
	return seat_point(holder).y


## Where the rider sits, in the holder's parent's space (the rider's own space: the horse hangs under the rider's
## node): the model's saddle node - forward / back as well as up, so the rider sits in the saddle, not on the
## withers (owner 2026-11-02 clip) - else straight up by the default height.
static func seat_point(holder: Node3D) -> Vector3:
	if holder == null:
		return Vector3(0, SEAT_DEFAULT, 0)
	if holder.is_inside_tree():
		var sn := holder.find_child("saddle*", true, false) as Node3D
		if sn:
			var local := holder.global_transform.affine_inverse() * sn.global_position
			if local.y > 0.5:
				holder.set_meta("seat", local.y)
				holder.set_meta("seat_local", local)
	var l: Vector3 = holder.get_meta("seat_local", Vector3(0, float(holder.get_meta("seat", SEAT_DEFAULT)), 0))
	return holder.transform * l


## The moment of ride_horse the rider sits lowest (its pelvis lowest above the feet): the pose held standing still -
## the clip starts on a frame half out of the saddle (owner 2026-11-02 / probe: standing in the stirrups). Found once
## per rider by stepping the clip, kept on the AnimationPlayer.
static func _still_time(anim: AnimationPlayer) -> float:
	if anim.has_meta("ride_still"):
		return float(anim.get_meta("ride_still"))
	var best := 0.0
	var root := anim.get_node_or_null(anim.root_node)
	var sk: Skeleton3D = null
	if root:
		var found := root.find_children("*", "Skeleton3D", true, false)
		sk = found[0] if found.size() > 0 else null
	var bone := sk.find_bone("Bip01 Pelvis") if sk else -1
	if bone >= 0:
		var length := anim.get_animation("ride_horse").length
		var low := INF
		for k in 16:
			var t := length * k / 16.0
			anim.seek(t, true)
			var y := sk.get_bone_global_pose(bone).origin.y
			if y < low:
				low = y
				best = t
	anim.set_meta("ride_still", best)
	return best


## The rider's ride_horse pose kept in step with the horse: at the horse's own pace while it moves, held still while
## it stands (owner 2026-11-02: "bouncing around as if they're riding even when standing still").
static func rider_pose(anim: AnimationPlayer, holder: Node3D, speed_mps: float) -> void:
	if anim == null or not anim.has_animation("ride_horse"):
		return
	if anim.current_animation != "ride_horse":
		anim.get_animation("ride_horse").loop_mode = Animation.LOOP_LINEAR
		anim.play("ride_horse", 0.2)
	if speed_mps <= 0.3:
		if anim.speed_scale != 0.0:
			# no cross-fade into a held pose: paused mid-blend the fade never finished and the rider stood on the
			# saddle in the idle pose (probe 2026-11-02)
			anim.speed_scale = 1.0
			anim.stop()
			anim.play("ride_horse", 0.0)
			anim.advance(0.0)
			anim.seek(_still_time(anim), true)
			anim.speed_scale = 0.0
		return
	if anim.speed_scale == 0.0:
		anim.play("ride_horse", 0.0)
	var hp: AnimationPlayer = holder.get_meta("anim", null) if holder else null
	anim.speed_scale = clampf(hp.speed_scale if hp else 1.0, 0.5, 2.0) if speed_mps > 4.5 else 0.6


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
