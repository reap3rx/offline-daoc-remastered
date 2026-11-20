extends SceneTree
## Headless: for each race/sex, a sword and a staff in the right hand, every run-like clip sampled; the closest any
## point of the weapon's box comes to the head bone (metres) and at which tilt (degrees out, about the weapon's X)
## that closeness is gone. Usage: godot --headless --path <proj> -s res://game/tools/clip_measure.gd

const RACES := ["ava_m","ava_f","bri_m","bri_f","cel_m","cel_f","dwa_m","dwa_f","elf_m","elf_f","fir_m","fir_f","fro_m","fro_f","hal_m","hal_f","hig_m","hig_f","inc_m","inc_f","kob_m","kob_f","lur_m","lur_f","nor_m","nor_f","sar_m","sar_f","sha_m","sha_f","syl_m","syl_f","tro_m","tro_f","val_m","val_f"]

func _corners(w: Node3D) -> Array:
	var pts := []
	for mi in w.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null: continue
		var bb := m.mesh.get_aabb()
		for i in 8:
			pts.append(m.global_transform * bb.get_endpoint(i))
	return pts

func _min_head(fig: Node3D, skel: Skeleton3D, head: int, w: Node3D) -> float:
	var hp := skel.global_transform * skel.get_bone_global_pose(head).origin
	var best := 99.0
	for p in _corners(w):
		best = minf(best, (p as Vector3).distance_to(hp))
	# also the weapon's long axis, sampled
	return best

func _initialize() -> void:
	await process_frame
	var sword := -1
	var staff := -1
	for id in range(1, 3000):
		var i := WeaponModels.info(id)
		if i.is_empty(): continue
		var st := WeaponModels.stance(id)
		if sword < 0 and st == "" and int(i.get("shield", 0)) == 0 and WeaponModels.path_of(id) != "": sword = id
		if staff < 0 and st == "staff" and WeaponModels.path_of(id) != "": staff = id
		if sword > 0 and staff > 0: break
	print("MEASURE sword=%d staff=%d" % [sword, staff])
	for race in RACES:
		var fig := Fig3Figure.new()
		root.add_child(fig)
		if not fig.load_figure(race):
			fig.queue_free(); continue
		await process_frame
		var sk := fig.find_children("*", "Skeleton3D", true, false)
		if sk.is_empty(): fig.queue_free(); continue
		var skel := sk[0] as Skeleton3D
		var head := skel.find_bone("Bip01 Head")
		var held := skel.find_bone("Bip01 R Held")
		var anim: AnimationPlayer = fig.anim
		if head < 0 or held < 0 or anim == null:
			print("MEASURE %s no head/held/anim" % race); fig.queue_free(); continue
		for wid in [sword, staff]:
			var at := BoneAttachment3D.new()
			at.bone_name = "Bip01 R Held"
			skel.add_child(at)
			var w := WeaponModels.make(wid, true, false)
			at.add_child(w)
			var base := w.transform
			for clip in anim.get_animation_list():
				var c := String(clip)
				if not (c == "run" or c == "walk" or c.begins_with("combat_run") or c.begins_with("run_")):
					continue
				var a := anim.get_animation(c)
				var res := []
				for tilt in [0.0, 10.0, 20.0, 30.0]:
					w.transform = base
					w.rotate_object_local(Vector3(1, 0, 0), deg_to_rad(tilt))
					var worst := 99.0
					anim.play(c)
					for k in 24:
						anim.seek(a.length * k / 24.0, true)
						skel.force_update_all_bone_transforms() if skel.has_method("force_update_all_bone_transforms") else null
						at.global_transform = skel.global_transform * skel.get_bone_global_pose(held)
						worst = minf(worst, _min_head(fig, skel, head, w))
					res.append("%d:%.2f" % [tilt, worst])
				print("MEASURE %s %s %s %s" % [race, "sword" if wid == sword else "staff", c, " ".join(res)])
			at.queue_free()
		fig.queue_free()
		await process_frame
	quit()
