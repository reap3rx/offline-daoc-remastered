extends Node
## Debug (claude 2026-11-06): the face-shape prototype (pipeline/face_morphs.py's fx_ targets) - one head in a set
## of slider presets, each from the front-side, in the game's own light. Each shot: <out>_<nn>.png.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=face_grid --mute --no-npcs --spot=450,600
##       --figure=zz_proto_bri_m [--out=<prefix>] [--angle=25]
var v: Node

const PRESETS := [
	["Neutral", {}],
	["Hawk", {"nose_tip": -0.7, "nose_length": 1.0, "nose_bridge": 1.0, "nose_width": -0.6, "cheekbones": 0.8, "jaw_width": -0.4, "chin_point": 0.6, "brow_depth": 0.6}],
	["Brute", {"jaw_width": 1.0, "brow_depth": 1.0, "brow_height": -0.6, "eye_depth": 0.8, "nose_width": 0.8, "chin_length": 0.4, "cheekbones": 0.5, "lips": 0.4}],
	["Gentle", {"eye_size": 0.8, "nose_length": -0.6, "nose_width": -0.3, "jaw_width": -0.6, "chin_length": -0.4, "lips": 0.6, "cheekbones": -0.3}],
	["Narrow", {"eye_spacing": -0.8, "nose_width": -0.8, "jaw_width": -0.8, "cheekbones": 0.6, "mouth_width": -0.5, "chin_length": 0.6}],
	["Wide", {"eye_spacing": 0.8, "nose_width": 0.8, "jaw_width": 0.8, "mouth_width": 0.7, "cheekbones": -0.4, "chin_length": -0.6}],
	["Snub", {"nose_tip": 1.0, "nose_length": -1.0, "nose_height": 0.6, "nose_width": 0.6, "chin_point": -0.6, "lips": 0.8}],
	["Long", {"chin_length": 1.0, "nose_length": 0.6, "nose_height": -0.5, "eye_height": 0.5, "brow_height": 0.6, "jaw_width": -0.4}],
	["Deep-set", {"eye_depth": 1.0, "brow_depth": 0.8, "eye_size": -0.5, "cheekbones": 0.7, "mouth_width": 0.4}],
	["Big ears", {"ear_size": 1.0, "eye_size": 0.4, "nose_length": -0.3}],
	["Mixed A", {"nose_tip": 0.6, "nose_bridge": 0.7, "eye_spacing": 0.4, "brow_height": 0.5, "mouth_height": 0.5, "chin_point": 0.8, "jaw_width": 0.3}],
	["Mixed B", {"nose_width": -0.5, "nose_height": -0.6, "eye_height": -0.5, "lips": -0.8, "chin_length": -0.8, "cheekbones": 1.0}],
]


## --presets=skin: the skin layers (looks applied, not shapes)
const SKIN := [
	["Plain", {}], ["No brows", {"brows": 0}], ["Brows 3", {"brows": 3}], ["Brows 6", {"brows": 6}],
	["Age 1", {"age_style": 1, "age": 0.9}], ["Age 2", {"age_style": 2, "age": 0.9}], ["Shadow", {"stubble_style": 1, "stubble": 0.9}],
	["Beard", {"stubble_style": 2, "stubble": 1.0}], ["Lips", {"lip_color": 2, "lip_amt": 0.6}], ["Freckles", {"freckles": 2}],
	["Scar", {"scar": 2}], ["Mask", {"paint": 1, "paint_color": 1}],
]

## --presets=mouth: one slider at a time, the mouth and jaw ones (what opened the mouth)
const MOUTH := [
	["Neutral", {}], ["Lips +1", {"lips": 1.0}], ["Lips -1", {"lips": -1.0}], ["Mouth W +1", {"mouth_width": 1.0}],
	["Mouth W -1", {"mouth_width": -1.0}], ["Mouth H +1", {"mouth_height": 1.0}], ["Jaw +1", {"jaw_width": 1.0}],
	["Jaw -1", {"jaw_width": -1.0}], ["Chin L -1", {"chin_length": -1.0}], ["Chin L +1", {"chin_length": 1.0}],
	["Chin P +1", {"chin_point": 1.0}], ["Nose L -1", {"nose_length": -1.0}],
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
	var target: Vector3 = sk.global_transform * sk.get_bone_global_pose(sk.find_bone("Bip01 Head")).origin
	var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
	cam.global_position = target + fwd.rotated(Vector3.UP, deg_to_rad(angle)) * 0.85 * fig.scale.x + Vector3(0, 0.03, 0)
	cam.look_at(target + Vector3(0, 0.02, 0))
	var heads: Array = fig.model.find_children("*", "MeshInstance3D", true, false)
	var pset := String(args.get("presets", ""))
	var presets: Array = MOUTH if pset == "mouth" else (SKIN if pset == "skin" else PRESETS)
	var names := []
	for p in presets:
		names.append(String(p[0]))
	for i in presets.size():
		var vals: Dictionary = presets[i][1]
		if pset == "skin":
			fig.look = {"face": 0, "hair": int(args.get("hair", "1")), "hair_color": 1, "eyes": 2, "skin": 1}
			fig.apply(fig.layered_changes())
			fig.apply(vals)
			vals = {}
		for mi in heads:
			var m := mi as MeshInstance3D
			for b in m.get_blend_shape_count():
				var nm := String(m.mesh.get_blend_shape_name(b))
				if nm.begins_with("fx_"):
					m.set_blend_shape_value(b, float(vals.get(nm.substr(3), 0.0)))
		await _frames(30)
		get_viewport().get_texture().get_image().save_png("%s_%02d.png" % [out, i])
		print("[fg] ", i, " ", names[i])
	get_tree().quit()
