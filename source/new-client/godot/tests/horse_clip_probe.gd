extends Node
## Debug (claude 2026-11-03, owner clip: the Catacombs horse "exploding" while it moves): the horse alone, each gait
## clip held at a few points, from the side. Offline zone viewer:
##   Godot --path godot res://game/zone_viewer.tscn -- --zone=200 --probe=horse_clip_probe --time=13
const Mounts := preload("res://game/world/mounts.gd")
var v: Node


func _shot(tag: String) -> void:
	for i in 6:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("E:/Offline DAOC 036c/claude-work/walk/horse_%s.png" % tag)


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _ready() -> void:
	get_tree().create_timer(120.0).timeout.connect(func(): print("[horse] timed out"); get_tree().quit())
	await _wait(12.0)
	v = get_tree().current_scene
	if v.ui:
		v.ui.visible = false
	var sw = v.npcs
	var m: Node3D = Mounts.make(5, sw, sw.models)
	if m == null:
		print("[horse] no model")
		get_tree().quit()
		return
	v.add_child(m)
	var cam := get_viewport().get_camera_3d()
	var fwd := -cam.global_basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var right := cam.global_basis.x
	right.y = 0.0
	right = right.normalized()
	m.global_position = v.player.global_position + fwd * 6.0
	m.look_at(m.global_position + right, Vector3.UP)
	var ap: AnimationPlayer = m.get_meta("anim")
	print("[horse] clips: %s" % str(ap.get_animation_list()))
	var mode := ""
	for a2 in OS.get_cmdline_user_args():
		if a2.begins_with("--horse-mode="):
			mode = a2.get_slice("=", 1)
	var lib := ap.get_animation_library("")
	var idle_paths := {}
	var ia := ap.get_animation("idle")
	for t in ia.get_track_count():
		idle_paths[str(ia.track_get_path(t))] = true
	for clip in ["walk", "run"]:
		var a := ap.get_animation(clip)
		var names := []
		for t in range(a.get_track_count() - 1, -1, -1):
			var path := str(a.track_get_path(t))
			if not idle_paths.has(path):
				names.append(path.get_slice(":", 1))
				if mode == "drop_extra":
					a.remove_track(t)
			elif mode == "rot_only_idle_bones" and a.track_get_type(t) == Animation.TYPE_POSITION_3D:
				a.remove_track(t)
		print("[horse] %s tracks not in idle: %s" % [clip, str(names)])
	for clip in ["idle", "walk", "run"]:
		if not ap.has_animation(clip):
			continue
		var a := ap.get_animation(clip)
		var bad := []
		for t in a.get_track_count():
			if a.track_get_type(t) == Animation.TYPE_POSITION_3D:
				for k in mini(a.track_get_key_count(t), 3):
					var p: Vector3 = a.track_get_key_value(t, k)
					if p.length() > 2.0:
						bad.append("%s %s" % [str(a.track_get_path(t)), str(p)])
						break
		print("[horse] %s: %.2f s, %d tracks, big position keys: %s" % [clip, a.length, a.get_track_count(), str(bad.slice(0, 6))])
		for f in [0.0, 0.33, 0.66]:
			ap.play(clip, 0.0)
			ap.seek(a.length * f, true)
			ap.speed_scale = 0.0
			await _shot("%s_%d" % [clip, int(f * 100)])
	ap.speed_scale = 1.0
	ap.play("idle", 0.0)
	await _wait(0.5)
	ap.play("run", 0.25)                                 # the cross-fade the game does when you start moving
	await _wait(0.12)
	await _shot("fade_idle_run")
	get_tree().quit()
