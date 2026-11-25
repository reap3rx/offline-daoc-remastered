extends Node
## Debug (claude 2026-11-25, the character creator plan, phase 1): the body's shape sliders (bx_ targets,
## pipeline/body_morphs.py) - one figure in a set of presets, mixed with the bone sliders as the creator would.
## Each shot: <out>_<nn>.png.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=body_shape_grid --mute --no-npcs --spot=450,600
##       --figure=bri_m [--out=<prefix>] [--angle=30]
var v: Node

const PRESETS := [
	["Neutral", {}],
	["Bust -", {"chest_size": -1.0}],
	["Bust +", {"chest_size": 1.0}],
	["Glutes -", {"glutes": -1.0}],
	["Glutes +", {"glutes": 1.0}],
	["Hips +", {"hips": 1.0}],
	["Hourglass", {"hips": 1.0, "waist": -0.6, "chest_size": 0.4, "glutes": 0.5}],
	["Slope down", {"shoulder_slope": -1.0}],
	["Slope up", {"shoulder_slope": 1.0}],
	["Chest deep", {"chest_depth": 1.0}],
	["Belly -/+", {"belly": -1.0, "love_handles": 1.0}],
	["Back+traps", {"back_width": 1.0, "traps": 1.0}],
]
func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(600.0).timeout.connect(func(): print("[bs] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/body/shot"))
	var prefix := String(args.get("figure", "bri_m"))
	var angle := float(args.get("angle", "25"))
	await get_tree().create_timer(10.0).timeout
	get_window().size = Vector2i(900, 1000)
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
		face_yaw = atan2(to_sun.x, to_sun.z) + deg_to_rad(35.0)
	var cam := Camera3D.new()
	cam.fov = 22.0
	cam.near = 0.05
	v.add_child(cam)
	cam.make_current()
	var fig := Fig3Figure.new()
	v.add_child(fig)
	if not fig.load_figure(prefix):
		print("[bs] no figure ", prefix)
		get_tree().quit()
		return
	fig.apply({"face": int(args.get("face", "0")), "hair": int(args.get("hair", "1")), "hair_color": 1, "eyes": 2, "skin": 1})
	print("[bs] shapes ", (fig.meta.get("body_shapes", []) as Array).map(func(x): return x[0]))
	print("[bs] sliders ", fig.body_sliders().size())
	var pg = load("res://game/pregame.gd")               # (the creator's script compiles, with the autoloads up)
	print("[bs] pregame compiles ", pg != null and (pg as GDScript).can_instantiate())
	fig.global_position = base
	fig.rotation.y = face_yaw
	fig.play("idle")
	await _frames(4)
	fig.anim.seek(1.0, true)
	fig.anim.pause()
	var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
	var pv := sk.find_bone("Bip01 Spine")
	var target: Vector3 = sk.global_transform * sk.get_bone_global_pose(pv).origin
	var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
	cam.global_position = target + fwd.rotated(Vector3.UP, deg_to_rad(angle)) * 5.2 * fig.scale.x + Vector3(0, 0.1, 0)
	cam.look_at(target + Vector3(0, -0.05, 0))
	for i in PRESETS.size():
		fig.apply({"body": PRESETS[i][1]})
		fig.anim.seek(1.0, true)
		await _frames(20)
		var w := -1.0
		for mi in fig._parts("body"):
			var bi: int = (mi as MeshInstance3D).find_blend_shape_by_name("bx_weight")
			if bi >= 0:
				w = (mi as MeshInstance3D).get_blend_shape_value(bi)
		get_viewport().get_texture().get_image().save_png("%s_%02d.png" % [out, i])
		print("[bs] ", i, " ", PRESETS[i][0], " bx_weight on body=", w)
	get_tree().quit()
