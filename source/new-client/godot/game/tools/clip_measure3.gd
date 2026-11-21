extends SceneTree
## Headless: Lurikeen male (and a few others) running with many one-handers; for each, the nearest corner to the head
## bone over the run, with the weapon turned 30 degrees about different axes (its own X, or the hand's X / Y / Z, both
## ways) - which turn clears the head for every weapon.
const RACES := ["lur_m", "kob_m", "hal_f", "cel_m", "lur_f", "cel_f"]
var _log: FileAccess

func _p(t: String) -> void:
	print(t)
	_log.store_line(t)
	_log.flush()

func _corners(w: Node3D) -> Array:
	var pts := []
	for mi in w.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null: continue
		var bb := m.mesh.get_aabb()
		for i in 8:
			pts.append(m.global_transform * bb.get_endpoint(i))
	return pts

func _initialize() -> void:
	_log = FileAccess.open("E:/Offline DAOC 036c/claude-work/cm3_log.txt", FileAccess.WRITE)
	await process_frame
	var FF = load("res://game/fig3_figure.gd")
	var WM = load("res://game/weapon_models.gd")
	var ids := []
	var seen := {}
	for id in range(1, 4000):
		var i: Dictionary = WM.info(id)
		if i.is_empty() or int(i.get("shield", 0)) > 0: continue
		if String(WM.stance(id)) != "": continue
		var nm := String(i.get("name", "")).to_lower()
		var bad := false
		for b in ["helm", "tunic", "lute", "drum", "flute", "grave", "cap", "harp", "robe", "glove", "boot", "sleeve", "leg", "cloak", "shield", "torch", "book", "bow"]:
			if b in nm: bad = true
		if bad: continue
		var path: String = WM.path_of(id)
		if path == "" or seen.has(path): continue
		seen[path] = true
		ids.append(id)
		if ids.size() >= 60: break
	_p("WEAPONS " + str(ids))
	var variants := [["0", 0.0, 0.0], ["x30", 30.0, 0.0], ["x45", 45.0, 0.0], ["x60", 60.0, 0.0], ["x75", 75.0, 0.0], ["x90", 90.0, 0.0],
		["x45y20", 45.0, 20.0], ["x60y20", 60.0, 20.0], ["x45y-20", 45.0, -20.0]]
	for race in RACES:
		var fig: Node3D = FF.new()
		root.add_child(fig)
		if not fig.load_figure(race):
			fig.queue_free(); continue
		await process_frame
		var skel := fig.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
		var head := skel.find_bone("Bip01 Head")
		var nub := skel.find_bone("Bip01 HeadNub")
		_p("HEAD %s nub=%d" % [race, nub])
		var held := skel.find_bone("Bip01 R Held")
		var anim: AnimationPlayer = fig.anim
		var a := anim.get_animation("run")
		for wid in ids:
			var at := BoneAttachment3D.new()
			at.bone_name = "Bip01 R Held"
			skel.add_child(at)
			var w: Node3D = WM.make(wid, true, false)
			if w == null:
				at.queue_free(); continue
			at.add_child(w)
			var base := w.transform
			var res := []
			for v in variants:
				w.transform = base.rotated_local(Vector3(1, 0, 0), deg_to_rad(float(v[1]))).rotated(Vector3(0, 1, 0), deg_to_rad(float(v[2])))
				var worst := 99.0
				anim.play("run")
				for k in 24:
					anim.seek(a.length * k / 24.0, true)
					at.global_transform = skel.global_transform * skel.get_bone_global_pose(held)
					var hp := skel.global_transform * skel.get_bone_global_pose(head).origin
					if nub >= 0:
						hp = hp.lerp(skel.global_transform * skel.get_bone_global_pose(nub).origin, 0.5)
					for p in _corners(w):
						worst = minf(worst, (p as Vector3).distance_to(hp))
				res.append("%s:%.2f" % [v[0], worst])
			_p("M %s %d %s %s" % [race, wid, String(WM.info(wid).get("name", "")).replace(" ", "_"), " ".join(res)])
			at.queue_free()
		fig.queue_free()
		await process_frame
	_p("DONE")
	quit()
