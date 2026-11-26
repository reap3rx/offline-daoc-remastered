extends Node
## Debug (claude 2026-11-26, the hair and helm check - owner: "do your helm and hair checks, and let me know what you
## see"): every hair style the creator offers a figure, on the HD head, from the front three-quarter and the back;
## then every helm the race wears (one per model file), over a short and a long style. PNGs into --out=<folder>:
## <fig>_hair_<index>_<front|back>.png, <fig>_helm_<model>_<short|long>.png.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=hair_check --mute --no-npcs --spot=450,600
##       --figures=bri_m,bri_f [--out=<folder>] [--helms=0]
var v: Node
var cam: Camera3D


func _ready() -> void:
	get_tree().create_timer(3000.0).timeout.connect(func(): print("[hc] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/hd2/check"))
	DirAccess.make_dir_recursive_absolute(out)
	await get_tree().create_timer(10.0).timeout
	get_window().size = Vector2i(360, 360)
	for n in ["hud", "ui"]:
		if v.get(n):
			v.get(n).visible = false
	v.player.visible = false
	var base: Vector3 = v.player.global_position
	if args.has("spot"):
		var xz := String(args["spot"]).split(",")
		base = Vector3(float(xz[0]), 0.0, float(xz[1]))
		base.y = v.zone.height_at(base.x, base.z)
	if args.has("flow"):                         # (to compare: the hair's flow, the remastered look)
		Fig3Figure.hair_flow_on = String(args["flow"]) == "1"
	if args.has("fx"):
		RenderingServer.global_shader_parameter_set("remaster_fx", float(args["fx"]))
	var only: Array = String(args.get("styles", "")).split(",", false)
	cam = Camera3D.new()
	cam.near = 0.02
	cam.fov = 24.0
	v.add_child(cam)
	cam.make_current()
	for prefix in String(args.get("figures", "bri_m")).split(","):
		var fig := Fig3Figure.new()
		fig.blinks = false
		v.add_child(fig)
		if not fig.load_figure(prefix):
			print("[hc] no figure ", prefix)
			fig.queue_free()
			continue
		fig.global_position = base
		fig.apply({"face": 0, "hair": 0, "hair_color": 2, "eyes": 2, "skin": 1})
		fig.set_hd(true)
		fig.set_helm(0, false, 0)
		fig.play("idle")
		for i in 10:
			await get_tree().process_frame
		fig.anim.pause()
		var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
		var hb := sk.find_bone("Bip01 Head")
		var offer: Array = fig.creator_styles()
		var styles: Array = fig.meta.get("hair_styles", [])
		for hi in offer:
			if not only.is_empty() and not only.has(str(int(hi))):
				continue
			fig.apply({"hair": int(hi)})
			if args.has("fit"):                      # (trying a fit: added over the style's saved one)
				var node := String(styles[int(hi)].get("node", ""))
				var base_fit := fig.hair_fit_of(node).duplicate()
				for kv in String(args["fit"]).split(";", false):        # (size:0.4;height:0.3 - quotes don't survive the shell)
					var k := String(kv).get_slice(":", 0)
					base_fit[k] = float(base_fit.get(k, 0.0)) + float(String(kv).get_slice(":", 1))
				fig.apply({"hair_fit": {node: base_fit}})
				print("[hc] fit ", node, " ", base_fit)
			await _frames(3)
			for view in [["front", 35.0], ["back", 160.0]]:
				_aim(sk, hb, float(view[1]))
				await _frames(2)
				get_viewport().get_texture().get_image().save_png("%s/%s_hair_%02d_%s%s.png" % [out, prefix, int(hi), view[0], String(args.get("tag", ""))])
		print("[hc] ", prefix, " ", offer.size(), " styles")
		if String(args.get("helms", "1")) != "0":
			# a short style and a long one (by label), each helm model file once
			var short_i := -1
			var long_i := -1
			for hi in offer:
				var lab := String(styles[int(hi)].get("label", ""))
				if short_i < 0 and lab.begins_with("Short"):
					short_i = int(hi)
				if lab.begins_with("Long"):
					long_i = int(hi)
			if short_i < 0:                          # (no Short style - the women's lists: the first Medium, else the first)
				for hi in offer:
					if String(styles[int(hi)].get("label", "")).begins_with("Medium"):
						short_i = int(hi)
						break
				if short_i < 0 and offer.size() > 0:
					short_i = int(offer[0])
			fig.set_helm(0, false, 0)
			var seen := {}
			var models := []
			for k in Fig3Figure._helms:
				var e = Fig3Figure.helm_entry(int(k), String(fig.meta.get("prefix", prefix)))
				if e is Dictionary and e.has("file") and not seen.has(String(e.get("file", ""))):
					seen[String(e.get("file", ""))] = true
					models.append(int(k))
			models.sort()
			for m in models:
				for hs in [["short", short_i], ["long", long_i]]:
					if int(hs[1]) < 0:
						continue
					fig.apply({"hair": int(hs[1])})
					fig.set_helm(m, false, 0)
					await _frames(4)
					_aim(sk, hb, 35.0)
					await _frames(2)
					get_viewport().get_texture().get_image().save_png("%s/%s_helm_%04d_%s.png" % [out, prefix, m, hs[0]])
			fig.set_helm(0, false, 0)
			print("[hc] ", prefix, " ", models.size(), " helms")
		fig.queue_free()
		await _frames(3)
	print("[hc] done")
	get_tree().quit()


func _aim(sk: Skeleton3D, hb: int, yaw_deg: float) -> void:
	var hx: Vector3 = (sk.global_transform * sk.get_bone_global_pose(hb)).origin
	var target := hx + Vector3(0, -0.02, 0)
	var y := deg_to_rad(yaw_deg)
	cam.global_position = target + Vector3(sin(y), 0.1, cos(y)).normalized() * 1.25
	cam.look_at(target)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
