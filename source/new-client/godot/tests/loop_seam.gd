extends Node
## Debug (claude 2026-11-05): a looping clip played across its seam, 120 frames a second - how far a foot, a hand and
## the head move from one frame to the next, the worst step and where (owner: a Breton archer's leg kicking out once
## a loop while she held her bow drawn). Headless.
##   Godot --headless --path new-client/godot res://tests/loop_seam.tscn -- bri_f bow_aim
func _ready() -> void:
	await get_tree().process_frame
	var args := OS.get_cmdline_user_args()
	var prefix: String = args[0] if args.size() > 0 else "bri_f"
	var clips: Array = args.slice(1) if args.size() > 1 else ["bow_aim", "idle", "run", "combat_idle_bow"]
	var f := Fig3Figure.new()
	add_child(f)
	if not f.load_figure(prefix):
		print("[seam] no figure ", prefix)
		get_tree().quit()
		return
	var sk: Skeleton3D = f.model.find_children("*", "Skeleton3D", true, false)[0]
	for clip in clips:
		if not f.anim.has_animation(clip):
			print("[seam] no clip ", clip)
			continue
		var a := f.anim.get_animation(clip)
		f.anim.play(clip)
		for bn in ["Bip01 L Foot", "Bip01 R Foot", "Bip01 L Calf", "Bip01 R Hand", "Bip01 Head"]:
			var b := sk.find_bone(bn)
			if b < 0:
				continue
			var prev := Vector3.ZERO
			var steps: Array = []
			var frames := int(a.length * 3.0 * 120.0)
			for i in frames + 1:
				f.anim.seek(fmod(i / 120.0, a.length), true)
				sk.force_update_all_bone_transforms()
				var o := sk.get_bone_global_pose(b).origin
				if i > 0:
					steps.append((o - prev).length())
				prev = o
			var worst := 0.0
			var at := 0
			var total := 0.0
			for i in steps.size():
				total += steps[i]
				if steps[i] > worst:
					worst = steps[i]
					at = i
			var mean := total / maxf(1, steps.size())
			print("[seam] %s %-16s %-14s len %.3f  mean step %.4f  worst %.4f (x%.1f) at %.3fs of the loop" % [prefix, clip, bn, a.length, mean, worst, worst / maxf(mean, 1e-6), fmod((at + 1) / 120.0, a.length)])
	get_tree().quit()
