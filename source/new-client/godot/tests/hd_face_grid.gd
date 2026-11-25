extends Node
## Debug (claude 2026-11-25, the character creator plan, phase 3): the HD head (Fig3Figure.set_hd) - one figure, its
## face close, classic then HD then a set of slider looks. Each shot: <out>_<nn>.png.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=hd_face_grid --mute --no-npcs --spot=450,600
##       --figure=bri_m [--out=<prefix>] [--angle=20] [--hair=1]
var v: Node

const LOOKS := [
	["Classic", false, {}],
	["HD", true, {}],
	["Hooded eyes, Roman nose", true, {"eye_hood": 0.9, "nose_hump": 0.6, "nose_curve": 0.5, "nose_projection": 0.3}],
	["Full lips, bow", true, {"upper_lip": 0.8, "lower_lip": 0.7, "cupids_bow": 0.8}],
	["Wide face, square jaw", true, {"head_width": 0.7, "jaw_width": 0.8, "chin_width": 0.5}],
	["Long face, pointed ears", true, {"head_height": 0.6, "face_length": 0.5, "ear_point": 0.9, "chin_length": 0.5}],
	["Upturned almond eyes", true, {"eye_outer_corner": 0.8, "eye_opening": -0.4, "epicanthic": 0.6}],
	["Snub nose, full cheeks", true, {"nose_curve": -0.7, "nose_tip_angle": 0.7, "cheek_fullness": 0.7}],
]

const CLASSIC := [
	["Classic", false, {}],
	["Broad, high crown", false, {"head_width": 0.8, "crown": 0.8, "temples": 0.5}],
	["Long head, sloped brow", false, {"head_length": 0.8, "forehead": -0.8}],
	["Muzzle out", false, {"muzzle": 1.0, "muzzle_width": 0.4}],
	["Flat face", false, {"muzzle": -1.0}],
	["Brow up, nostrils", false, {"brow_angle": 1.0, "nostrils": 1.0}],
	["Hollow cheeks", false, {"cheek_hollow": 1.0}],
	["Jowls", false, {"jowls": 1.0, "head_width": -0.4}],
]


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(600.0).timeout.connect(func(): print("[hd] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/hd/shot"))
	var prefix := String(args.get("figure", "bri_m"))
	var angle := float(args.get("angle", "20"))
	await get_tree().create_timer(10.0).timeout
	get_window().size = Vector2i(800, 800)
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
		face_yaw = atan2(to_sun.x, to_sun.z) + deg_to_rad(25.0)
	var cam := Camera3D.new()
	cam.fov = 18.0
	cam.near = 0.02
	v.add_child(cam)
	cam.make_current()
	var fig := Fig3Figure.new()
	v.add_child(fig)
	if not fig.load_figure(prefix):
		print("[hd] no figure ", prefix)
		get_tree().quit()
		return
	fig.apply({"face": int(args.get("face", "0")), "hair": int(args.get("hair", "0")), "hair_color": 1, "eyes": 2, "skin": 1})
	print("[hd] has hd_head ", fig.meta.has("hd_head"), " features ", fig.face_features().size())
	fig.global_position = base
	fig.rotation.y = face_yaw
	fig.play("idle")
	await _frames(4)
	fig.anim.seek(1.0, true)
	fig.anim.pause()
	var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
	var hb := sk.find_bone("Bip01 Head")
	var target: Vector3 = sk.global_transform * sk.get_bone_global_pose(hb).origin
	var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
	cam.global_position = target + fwd.rotated(Vector3.UP, deg_to_rad(angle)) * 1.6 * fig.scale.x + Vector3(0, 0.08, 0)
	cam.look_at(target + Vector3(0, 0.02, 0))
	var looks: Array = CLASSIC if String(args.get("looks", "")) == "classic" else LOOKS
	for i in looks.size():
		fig.set_hd(looks[i][1])
		fig.set_helm(0, false, 0)                    # (as dressing does: owner 2026-11-25, the classic head came back)
		fig.set_shape(looks[i][2])
		fig.anim.seek(1.0, true)
		await _frames(12)
		var vis := []
		for mi in fig._parts("head"):
			vis.append("%s=%s" % [mi.name, mi.visible])
		get_viewport().get_texture().get_image().save_png("%s_%02d.png" % [out, i])
		print("[hd] ", i, " ", looks[i][0], " hd=", fig.is_hd(), " ", vis)
	get_tree().quit()
