extends Node
## Debug (claude 2026-11-26, the hair's flow - owner: "more true movement to the hair ... more flowy"): one figure in
## one hair style, standing, running, stopping and turning, recorded frame by frame twice - the flow off (the sway as it
## was) and on - for a side-by-side clip. Each frame: <out>_<off|on>_<nnn>.png.
##   Godot --path new-client/godot --fixed-fps 30 -- --zone=0 --time=16 --probe=hair_flow --mute --no-npcs
##       --spot=450,600 --figure=elf_f --style="Long 15" [--yaw=55] [--out=<prefix>]
var v: Node


func _ready() -> void:
	get_tree().create_timer(900.0).timeout.connect(func(): print("[hf] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/hd2/flow/clip"))
	var prefix := String(args.get("figure", "elf_f"))
	var style := String(args.get("style", "Long 1"))
	var cam_yaw := float(args.get("yaw", "55"))
	await get_tree().create_timer(10.0).timeout
	get_window().size = Vector2i(640, 640)
	for n in ["hud", "ui"]:
		if v.get(n):
			v.get(n).visible = false
	v.player.visible = false
	RenderingServer.global_shader_parameter_set("remaster_fx", 1.0)
	Fig3Figure.sway_on = true
	Fig3Figure.wind = 1.0
	var base: Vector3 = v.player.global_position
	if args.has("spot"):
		var xz := String(args["spot"]).split(",")
		base = Vector3(float(xz[0]), 0.0, float(xz[1]))
		base.y = v.zone.height_at(base.x, base.z)
	var cam := Camera3D.new()
	cam.near = 0.02
	cam.fov = 24.0
	v.add_child(cam)
	cam.make_current()
	var fig := Fig3Figure.new()
	fig.blinks = false
	v.add_child(fig)
	if not fig.load_figure(prefix):
		print("[hf] no figure ", prefix)
		get_tree().quit()
		return
	var styles: Array = fig.meta.get("hair_styles", [])
	var hi := 0
	for i in styles.size():
		if String(styles[i].get("label", "")) == style:
			hi = i
	print("[hf] ", prefix, " style ", style, " -> ", hi)
	fig.apply({"face": 0, "hair": hi, "hair_color": 2, "eyes": 2, "skin": 1})
	# (a character's own look - its hair length and fit - from the save: --look-file=<server_looks.json> --char=<name>)
	if args.has("look-file") and args.has("char"):
		var all = JSON.parse_string(FileAccess.get_file_as_string(String(args["look-file"])))
		if all is Dictionary and (all as Dictionary).has(String(args["char"])):
			var lk: Dictionary = (all[String(args["char"])] as Dictionary).duplicate(true)
			if args.has("style"):
				lk["hair"] = hi
			fig.look = {}
			fig.apply(lk)
			print("[hf] the look of ", args["char"], " hair ", lk.get("hair"))
	fig.set_hd(true)
	fig.set_helm(0, false, 0)
	var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
	var hb := sk.find_bone("Bip01 Head")
	for pass_ in ["off", "on"]:
		Fig3Figure.hair_flow_on = pass_ == "on"
		fig.global_position = base
		fig.rotation.y = 0.0
		fig.play("idle")
		for i in 20:
			await get_tree().process_frame
		var pos := base
		var yaw := 0.0
		# 0-3 s standing, 3-6 s running ahead, 6-8.5 s stopped, 8.5-9 s a quick half turn, 9-11 s standing
		var frames := 330
		var moving := false
		for f in frames:
			var t := f / 30.0
			var run := t >= 3.0 and t < 6.0
			if run and not moving:
				fig.play("run")
				moving = true
			elif not run and moving:
				fig.play("idle")
				moving = false
			if run:
				pos += Vector3(sin(yaw), 0.0, cos(yaw)) * (6.0 / 30.0)
			if t >= 8.5 and t < 9.0:
				yaw += PI / 15.0
			fig.global_position = Vector3(pos.x, v.zone.height_at(pos.x, pos.z), pos.z)
			fig.rotation.y = yaw
			# the camera keeps the head and shoulders in view, from the side and a little behind the start's facing
			var hx: Vector3 = (sk.global_transform * sk.get_bone_global_pose(hb)).origin
			var target := hx + Vector3(0, -0.14, 0)
			cam.global_position = target + Vector3(sin(deg_to_rad(cam_yaw)), 0.12, cos(deg_to_rad(cam_yaw))).normalized() * 2.2
			cam.look_at(target)
			await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("%s_%s_%03d.png" % [out, pass_, f])
	print("[hf] done")
	get_tree().quit()
