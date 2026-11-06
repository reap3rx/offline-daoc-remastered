extends Node
## Debug (claude 2026-11-06): the body sliders (Fig3Figure.BodyShape) - one figure in a set of slider presets, whole,
## from an angle. Each shot: <out>_<nn>.png.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=body_grid --mute --no-npcs --spot=450,600
##       --figure=bri_m [--out=<prefix>] [--angle=30]
var v: Node

const PRESETS := [
	["Neutral", {}],
	["Chest wide", {"chest_width": 1.0}],
	["Chest deep", {"chest_depth": 1.0}],
	["Chest size", {"chest_size": 1.0}],
	["Waist thin", {"waist": -1.0}],
	["Torso long", {"torso": 1.0}],
	["Hips", {"hips": 1.0}],
	["Glutes", {"glutes": 1.0}],
	["Legs long", {"legs": 1.0}],
	["Thighs calves", {"thighs": 1.0, "calves": 1.0}],
	["Arms long", {"arms": 1.0}],
	["Arms thick", {"arm_size": 1.0, "shoulders": 0.6}],
	["Head small", {"head": -1.0}],
	["Slight", {"chest_width": -0.8, "chest_depth": -0.6, "waist": -0.8, "hips": -0.5, "thighs": -0.8, "calves": -0.6, "arm_size": -0.8, "chest_size": -0.6, "glutes": -0.5}],
	["Heavy", {"chest_width": 0.8, "chest_depth": 0.8, "waist": 1.0, "hips": 0.8, "thighs": 0.9, "calves": 0.7, "arm_size": 0.8, "chest_size": 0.7, "glutes": 0.8, "shoulders": 0.5}],
]
func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(600.0).timeout.connect(func(): print("[fg] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/walk/fg"))
	var prefix := String(args.get("figure", "zz_proto_bri_m"))
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
		print("[fg] no figure ", prefix)
		get_tree().quit()
		return
	fig.apply({"face": int(args.get("face", "0")), "hair": int(args.get("hair", "1")), "hair_color": 1, "eyes": 2, "skin": 1})
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
		fig.anim.seek(1.0, true)                    # (the paused skeleton re-posed: its modifiers run again)
		await _frames(20)
		get_viewport().get_texture().get_image().save_png("%s_%02d.png" % [out, i])
		print("[bg] ", i, " ", PRESETS[i][0])
	get_tree().quit()
