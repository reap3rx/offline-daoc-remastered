extends Node
## Debug (claude 2026-11-05): the redrawn hair across races and styles, as the game draws it (Fig3Figure's hair
## material) - each "race:style:colour" from the front-side and from behind, in the game's own light.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=hair_gallery --mute --no-npcs --spot=450,600
##       --list=bri_m:1:1,cel_f:3:2,... [--out=<prefix>]
var v: Node


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(900.0).timeout.connect(func(): print("[hg] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/walk/hg"))
	await get_tree().create_timer(10.0).timeout
	get_window().size = Vector2i(1600, 900)
	for n in ["hud", "ui"]:
		if v.get(n):
			v.get(n).visible = false
	v.player.visible = false
	var base: Vector3 = v.player.global_position
	if args.has("spot"):
		var xz := String(args["spot"]).split(",")
		base = Vector3(float(xz[0]), 0.0, float(xz[1]))
		base.y = v.zone.height_at(base.x, base.z)
	var face_yaw := 0.0
	var suns := get_tree().root.find_children("*", "DirectionalLight3D", true, false)
	if suns.size() > 0:
		var to_sun: Vector3 = (suns[0] as DirectionalLight3D).global_transform.basis.z
		face_yaw = atan2(to_sun.x, to_sun.z) + deg_to_rad(float(args.get("sun_off", "35")))
	var cam := Camera3D.new()
	cam.fov = 30.0
	cam.near = 0.05
	v.add_child(cam)
	cam.make_current()
	var i := 0
	for entry in String(args.get("list", "bri_m:1:1")).split(","):
		var p := entry.split(":")
		var fig := Fig3Figure.new()
		v.add_child(fig)
		if not fig.load_figure(p[0]):
			print("[hg] no figure ", p[0])
			continue
		fig.apply({"face": 0, "hair": int(p[1]), "hair_color": int(p[2]), "eyes": 2, "skin": 1})
		fig.global_position = base
		fig.rotation.y = face_yaw
		fig.play("idle")
		await _frames(4)
		fig.anim.seek(1.0, true)
		fig.anim.pause()
		var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
		var target: Vector3 = sk.global_transform * sk.get_bone_global_pose(sk.find_bone("Bip01 Head")).origin
		var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
		for sh in [["front", 25.0], ["back", 155.0]]:
			cam.global_position = target + fwd.rotated(Vector3.UP, deg_to_rad(float(sh[1]))) * 0.95 * fig.scale.x + Vector3(0, 0.1, 0)
			cam.look_at(target + Vector3(0, 0.0, 0))
			await _frames(40)
			get_viewport().get_texture().get_image().save_png("%s_%02d_%s.png" % [out, i, sh[0]])
		print("[hg] ", i, " ", entry)
		i += 1
		fig.queue_free()
		await _frames(2)
	get_tree().quit()
