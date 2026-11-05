extends Node
## Debug (claude 2026-11-05): race figures side by side - each "before:after" pair of figure folders (the smoothed
## ones beside the old), the face, the side and the whole figure, in the game's own light. The second of each pair can
## have the remastered skin (--skin=1) and its own texture set (--tex2=...).
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=figure_gallery --mute --no-npcs --spot=450,600
##       --pairs=bri_m:bri_m_sub,elf_f:elf_f_sub [--tex=x4plus] [--tex2=x4plus] [--skin=1] [--out=<prefix>]
var v: Node


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(900.0).timeout.connect(func(): print("[gal] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/walk/gal"))
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
		face_yaw = atan2(to_sun.x, to_sun.z) + deg_to_rad(float(args.get("sun_off", "70")))
	var cam := Camera3D.new()
	cam.fov = 30.0
	cam.near = 0.05
	v.add_child(cam)
	cam.make_current()
	var shots := [["face", 0.75, 0.0, "Bip01 Head"], ["side", 0.75, 70.0, "Bip01 Head"], ["body", 3.6, 25.0, "Bip01 Spine"], ["back", 3.2, 160.0, "Bip01 Spine"]]
	for pair in String(args.get("pairs", "bri_m:bri_m_sub")).split(","):
		var two := pair.split(":")
		for i in two.size():
			var fig := Fig3Figure.new()
			fig.skin_shading = i == 1 and args.get("skin", "0") == "1"
			v.add_child(fig)
			if not fig.load_figure(two[i], String(args.get("tex2" if i == 1 else "tex", "x4plus"))):
				print("[gal] no figure ", two[i])
				continue
			fig.apply({"face": 0, "hair": 1, "hair_color": 1, "eyes": 2, "skin": 1})
			if args.has("armor"):                             # --armor=41,42,43,44,45,91: armour models, a cloak
				var female := String(two[i]).contains("_f")
				var parts := {}
				for mdl in String(args["armor"]).split(","):
					parts.merge(Fig3Figure.armor_parts(int(mdl), female), true)
				fig.cloak_emblem = int(args.get("emblem", "0"))
				fig.set_armor(parts)
			fig.global_position = base
			fig.rotation.y = face_yaw
			fig.play("idle")
			await _frames(4)
			fig.anim.seek(1.0, true)
			fig.anim.pause()
			var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
			for sh in shots:
				var bi := sk.find_bone(sh[3])
				var target: Vector3 = sk.global_transform * sk.get_bone_global_pose(bi).origin
				var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
				var dir := fwd.rotated(Vector3.UP, deg_to_rad(float(sh[2])))
				var dist := float(sh[1]) * fig.scale.x
				cam.global_position = target + dir * dist + Vector3(0, 0.05, 0)
				cam.look_at(target + Vector3(0, 0.02, 0))
				await _frames(60)
				var path := "%s_%s_%s_%d.png" % [out, two[0], sh[0], i]
				get_viewport().get_texture().get_image().save_png(path)
				print("[gal] saved ", path)
			fig.queue_free()
			await _frames(2)
	get_tree().quit()
