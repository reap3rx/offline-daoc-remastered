extends Node
## Debug (claude 2026-10-31, remastered characters): in a town (offline), dress your figure as an armoured NPC with
## a cloak, then pictures: the armour up close (remastered / classic), standing (cloak at rest), running (the cloak
## trailing), just stopped (settling).
##   --zone=26 --figure=bri_m --remastered=1 --probe=char_probe --out=<dir>
var v: Node
var out := ""


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + "/" + name + ".png")
	print("[char] shot ", name)


func _ready() -> void:
	v = get_tree().current_scene
	out = ProjectSettings.globalize_path(String(v.args.get("out", "user://char_probe")))
	DirAccess.make_dir_recursive_absolute(out)
	await get_tree().create_timer(10.0).timeout
	v.ui.visible = false
	var fig: Fig3Figure = v.player._model as Fig3Figure
	var best: Fig3Figure = null
	var best_score := -1
	for n in v.npcs.active.values():
		var m = n.get("model")
		if m is Fig3Figure:
			var a: Dictionary = (m as Fig3Figure).armor
			var score := 0
			if (a.get("cloak", []) as Array).size() > 1:
				score += 2
			var body := String((a.get("body", ["", ""]) as Array)[1]) if (a.get("body", []) as Array).size() > 1 else ""
			if body.begins_with("plt") or body.begins_with("chn") or body.begins_with("scl"):
				score += 3
			if score > best_score:
				best_score = score
				best = m
	var figs := 0
	for n in v.npcs.active.values():
		if n.get("model") is Fig3Figure:
			figs += 1
	print("[char] views %d, figures %d, player model %s" % [v.npcs.active.size(), figs, v.player._model])
	if best == null or fig == null:
		print("[char] no armoured NPC / no figure")
		get_tree().quit()
		return
	print("[char] dressed as ", best.get_parent().name, " armour ", best.armor)
	var dress: Dictionary = best.armor.duplicate()
	if v.args.has("nocloak"):
		dress.erase("cloak")
	fig.set_armor(dress, best.armor_tints)
	if v.args.has("hair"):
		fig.apply({"hair": int(v.args["hair"])})
	v.player.hold()
	var cam := Camera3D.new()
	v.add_child(cam)
	cam.current = true
	var p: Vector3 = v.player.global_position
	var face: Vector3 = (fig.model.global_basis * Vector3(0, 0, 1)).normalized()
	face.y = 0.0
	face = face.normalized()
	var side := face.cross(Vector3.UP).normalized()
	# the armour up close, from the front
	cam.global_position = p + face * 2.2 + Vector3(0, 1.4, 0)
	cam.look_at(p + Vector3(0, 1.1, 0))
	await get_tree().create_timer(1.5).timeout
	await _shot("armor_remastered")
	v.sky.set_remastered(false)
	await get_tree().create_timer(1.0).timeout
	await _shot("armor_classic")
	v.sky.set_remastered(true)
	# standing, from the side (the cloak at rest)
	cam.global_position = p + side * 3.5 + Vector3(0, 1.3, 0)
	cam.look_at(p + Vector3(0, 1.0, 0))
	await get_tree().create_timer(1.5).timeout
	await _shot("cloak_still")
	# running forward 7 m/s for 1.6 s, the camera keeping beside
	if fig.anim and fig.anim.has_animation("run"):
		fig.anim.play("run")
	var t := 0.0
	while t < 1.6:
		var d := get_process_delta_time()
		t += d
		v.player.global_position += face * 7.0 * d
		var q: Vector3 = v.player.global_position
		cam.global_position = q + side * 3.5 + Vector3(0, 1.3, 0)
		cam.look_at(q + Vector3(0, 1.0, 0))
		await get_tree().process_frame
	await _shot("cloak_running")
	if fig.anim and fig.anim.has_animation("idle"):
		fig.anim.play("idle")
	await get_tree().create_timer(0.25).timeout
	await _shot("cloak_stopping")
	await get_tree().create_timer(2.0).timeout
	await _shot("cloak_settled")
	get_tree().quit()
