extends Node
## Debug (claude 2026-11-05): the Black Mtns. North / South border from above, after the terrain shader stopped a
## whole-zone colour map wrapping its far edge (the white seam line). Looks along the zone's south edge.
##   Godot --path new-client/godot -- --zone=3 --time=14 --probe=seam_shot --mute --no-npcs --spot=800,1600 --out=<prefix>
var v: Node


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(300.0).timeout.connect(func(): print("[seam] timed out"); get_tree().quit())
	v = get_parent()
	var out := String(v.args.get("out", "E:/Offline DAOC 036c/claude-work/shots/seam"))
	await get_tree().create_timer(20.0).timeout
	get_window().size = Vector2i(1600, 900)
	for n in ["hud", "ui"]:
		if v.get(n):
			v.get(n).visible = false
	v.player.visible = false
	var size := float(v.zone.info.size_m)
	var cam := Camera3D.new()
	cam.fov = 60.0
	cam.far = 3000.0
	v.add_child(cam)
	cam.make_current()
	var i := 0
	for x in [500.0, 800.0, 1100.0]:
		for shot in [[40.0, 70.0], [12.0, 25.0]]:
			var hb: float = v.zone.height_at(x, size - 2.0)
			cam.global_position = Vector3(x - shot[1] * 0.6, hb + shot[0], size - shot[1])
			cam.look_at(Vector3(x, hb, size))
			await _frames(60)
			get_viewport().get_texture().get_image().save_png("%s_%d.png" % [out, i])
			print("[seam] shot ", i, " x=", x)
			i += 1
	get_tree().quit()
