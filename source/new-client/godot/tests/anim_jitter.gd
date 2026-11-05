extends Node
## Debug (claude 2026-11-05): a figure's idle, frame by frame at 60 fps - the head's position and facing, and how
## unevenly they move (owner: "a weird jitteriness ... in male's animations", females smooth). Headless.
##   Godot --headless --path new-client/godot res://tests/anim_jitter.tscn -- elf_m elf_f
func _ready() -> void:
	print("[jit] start")
	await get_tree().process_frame
	var args := OS.get_cmdline_user_args()
	for prefix in (args if not args.is_empty() else ["elf_m", "elf_f"]):
		var f := Fig3Figure.new()
		add_child(f)
		if not f.load_figure(prefix):
			print("[jit] no figure ", prefix)
			continue
		var ia: Animation = f.anim.get_animation("idle")
		print("[jit] loaded ", prefix, " tracks ", ia.get_track_count(), " type0 ", ia.track_get_type(0), " compressed ", ia.track_is_compressed(0), " interp ", ia.track_get_interpolation_type(0), " keys ", ia.track_get_key_count(0), " smooth ", ia.has_meta("smooth"))
		var sk: Skeleton3D = f.model.find_children("*", "Skeleton3D", true, false)[0]
		f.anim.play("idle")
		var bones := ["Bip01 Head", "Bip01 Neck", "Bip01 Spine2", "Bip01 Spine1", "Bip01 Spine", "Bip01 Pelvis", "Bip01", "Bip01 L Clavicle", "Bip01 R UpperArm"]
		for bn in bones:
			var b := sk.find_bone(bn)
			if b < 0:
				continue
			var pos: Array = []
			var fwd: Array = []
			for i in 480:
				f.anim.seek(i / 60.0, true)
				sk.force_update_all_bone_transforms()
				var g := sk.get_bone_global_pose(b)
				pos.append(g.origin)
				fwd.append(g.basis.x.normalized())
			# jerk: how far each step's motion departs from the average of its neighbours'
			var rough := 0.0
			var worst := 0.0
			var worst_at := 0
			var spikes := 0
			var travel := 0.0
			for i in range(1, 479):
				var a: Vector3 = pos[i] - pos[i - 1]
				var c: Vector3 = pos[i + 1] - pos[i]
				var j := (c - a).length()
				var turn := rad_to_deg((fwd[i] as Vector3).angle_to(fwd[i - 1])) - rad_to_deg((fwd[i + 1] as Vector3).angle_to(fwd[i]))
				var r := absf(turn)
				rough += j
				travel += a.length()
				if r > worst:
					worst = r
					worst_at = i
				if r > 0.25:
					spikes += 1
			print("[jit] %s %-17s travel %7.2f  pos-jerk %6.3f  turn-jerk max %.2f deg at %.2fs, spikes %d" % [prefix, bn, travel, rough, worst, worst_at / 60.0, spikes])
		f.queue_free()
	get_tree().quit()
