extends Node
## Debug (claude 2026-11-25, the HD head rebuilt): one figure's HD head close up and animated, as the owner sees it -
## the face, the eyes, the ear, the neck's join front and back, at a few moments of a few animations, and a few
## slider looks. Each shot: <out>_<nn>_<name>.png.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=hd2_closeup --mute --no-npcs --spot=450,600
##       --figure=elf_m [--out=<prefix>] [--hair=1] [--set=full|quick]
var v: Node

const LOOKS := [
	["wide_square", {"head_width": 1.0, "jaw_width": 0.8, "chin_width": 0.5}],
	["narrow_long", {"head_width": -1.0, "head_height": 0.7, "chin_length": 0.6}],
	["eyes_big_wide", {"eye_size": 1.0, "eye_spacing": 1.0, "eye_opening": 1.0}],
	["eyes_small_deep", {"eye_size": -1.0, "eye_depth": -1.0, "eye_hood": 1.0}],
	["eyes_out_slant", {"eye_depth": 1.0, "eye_outer_corner": 1.0, "eye_inner_corner": 1.0, "epicanthic": -1.0}],
	["ears_big_out", {"ear_size": 1.0, "ear_out": 1.0, "ear_tilt": 1.0}],
	["ears_small_in", {"ear_size": -1.0, "ear_out": -1.0, "ear_tilt": -1.0}],
	["nose_lips", {"nose_width": 1.0, "nose_projection": 1.0, "upper_lip": 1.0, "lower_lip": 1.0, "mouth_width": 1.0}],
	["jaw_chin_neck", {"jaw_drop": 1.0, "jowls": 1.0, "neck_thickness": 1.0, "chin_depth": 1.0}],
]

## The HD look (set=makeup): the skin smooth and weathered, every brow shape, the makeup styles.
const MAKEUP := [
	["smooth", {}],
	["detail_full", {"skin_detail": 1.0}],
	["brows_soft_arch", {"hd_brow": 2}],
	["brows_angled", {"hd_brow": 5, "brow_color": 1}],
	["brows_bushy", {"hd_brow": 7, "brow_thick": 0.6}],
	["brows_thin_high", {"hd_brow": 8, "brow_height": 0.8, "brow_arch": 0.8}],
	["brows_scarred", {"hd_brow": 12}],
	["brows_none", {"hd_brow": 0}],
	["lips_red_gloss", {"lip_color": 2, "lip_amt": 0.85, "lip_gloss": 1.0, "lipline_amt": 0.6, "lipline_color": 1}],
	["liner_thin_wing", {"liner": 1, "liner_wing": 0.7, "lash_amt": 1.4, "lash_len_shape": 1.0}],
	["smoky", {"liner": 3, "shadow": 2, "shadow_color": 3, "shadow_amt": 0.85}],
	["winged_blue", {"liner": 2, "liner_wing": 1.0, "shadow": 3, "shadow_color": 6}],
	["to_brow_plum", {"shadow": 4, "shadow_color": 2, "shadow_amt": 0.6, "lash_color": 2}],
	["halo_gold", {"shadow": 5, "shadow_color": 7, "lash_len_shape": -1.0}],
	["blush_contour", {"blush_amt": 0.7, "blush_color": 0, "contour": 1.0}],
	["war_paint", {"paint": 1, "paint_color": 0}],
	["age_mid", {"hd_age": 0.55}],
	["age_old_weathered", {"hd_age": 1.0, "weather": 0.7}],
	["freckles_band_moles", {"freckles": 3, "freckle_density": 0.8, "moles": 0.8}],
	["freckles_face_flush", {"freckles": 2, "freckle_density": 0.5, "flush": 0.8, "warmth": 0.6}],
	["scar_gash_cheek", {"hd_scar": 2, "scar_x": 1.0, "scar_y": 0.0, "scar_turn": 20.0}],
	["scar_claw_brow", {"hd_scar": 3, "scar_x": -1.0, "scar_y": 0.55, "scar_amt": 0.9}],
	["blink_half", {"_shape": {"blink": 0.5}}],
	["blink_full", {"_shape": {"blink": 1.0}}],
	["expr_smile", {"_expr": 1}],
	["expr_scowl", {"_expr": 2}],
	["expr_surprise", {"_expr": 3}],
	["expr_squint", {"_expr": 4}],
	["eyes_fibrous_big", {"iris": 1, "iris_size": 1.0, "pupil": -1.0}],
	["eyes_starburst_hetero", {"iris": 2, "eye_r": 4}],
	["eyes_ringed_bloodshot", {"iris": 3, "sclera_color": 1, "sclera_amt": 0.8, "pupil": 1.0}],
	["eyes_black_glow", {"iris": 5, "sclera_color": 4, "sclera_amt": 1.0, "eye_glow": 1.0, "eyes_rgb": [0.9, 0.3, 0.1]}],
	["tattoo_own", {"tattoo": 1}],
	["tattoo_moved_red", {"tattoo": 2, "tattoo_x": 0.3, "tattoo_y": -0.4, "tattoo_size": 1.3, "tattoo_turn": 20.0, "tattoo_color": 3}],
	["tattoo_small_gold", {"tattoo": 1, "tattoo_size": 0.7, "tattoo_y": 0.3, "tattoo_color": 5, "tattoo_amt": 0.8}],
	["asym_full", {"_shape": {"eye_level": 1.0, "eye_size_side": 1.0, "nose_lean": 1.0, "cheekbone_level": 1.0, "cheek_side": 1.0, "jaw_side": 1.0, "ear_level": 1.0, "ear_side": 1.0, "nostril_side": 1.0, "mouth_tilt": 1.0}}],
]

# name, yaw (degrees off the face's front), distance (m), fov, the aim's offset from the eyes' middle (right, up, forward)
const VIEWS := [
	["front", 0.0, 1.5, 12.0, Vector3(0, -0.02, -0.06)],
	["three_quarter", 40.0, 1.5, 12.0, Vector3(0, -0.02, -0.06)],
	["profile", 90.0, 1.5, 12.0, Vector3(0, -0.02, -0.08)],
	["back_quarter", 150.0, 1.5, 14.0, Vector3(0, -0.08, -0.1)],
	["eyes", 25.0, 1.2, 5.0, Vector3(0, 0.0, 0.0)],
	["eye_side", 75.0, 1.2, 5.0, Vector3(0, 0.0, 0.0)],
	["neck_front", 20.0, 1.5, 10.0, Vector3(0, -0.17, -0.06)],
	["neck_back", 180.0, 1.5, 10.0, Vector3(0, -0.15, -0.1)],
	["ear", 100.0, 1.2, 6.0, Vector3(0, 0.0, -0.09)],
]


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(900.0).timeout.connect(func(): print("[hd2] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/hd2/shots/shot"))
	var prefix := String(args.get("figure", "bri_m"))
	var quick := String(args.get("set", "full")) in ["quick", "makeup", "beast"]
	await get_tree().create_timer(10.0).timeout
	get_window().size = Vector2i(720, 720)
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
	cam.near = 0.02
	v.add_child(cam)
	cam.make_current()
	var fig := Fig3Figure.new()
	fig.blinks = false                              # (still shots: no blink mid-frame)
	v.add_child(fig)
	if not fig.load_figure(prefix):
		print("[hd2] no figure ", prefix)
		get_tree().quit()
		return
	fig.apply({"face": 0, "hair": int(args.get("hair", "0")), "hair_color": 1, "eyes": int(args.get("eyes", "2")), "skin": int(args.get("skin", "1"))})
	fig.set_hd(true)
	fig.set_helm(0, false, 0)
	print("[hd2] ", prefix, " has_hd ", fig.has_hd(), " is_hd ", fig.is_hd(), " features ", fig.face_features().size())
	var vis := []
	for mi in fig._parts("head"):
		vis.append("%s=%s" % [mi.name, mi.visible])
	print("[hd2] head parts ", vis)
	fig.global_position = base
	fig.rotation.y = face_yaw
	var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
	var hb := sk.find_bone("Bip01 Head")
	var eb := [sk.find_bone("Bip01 L Eyeball"), sk.find_bone("Bip01 R Eyeball")]
	var n := 0
	var moments := [["idle", 0.4], ["idle", 2.2], ["run", 0.25], ["walk", 0.6]]
	if quick:
		moments = [["idle", 0.4]]
	var shoot := func(tag: String, views: Array):
		for vw in views:
			var hx: Transform3D = sk.global_transform * sk.get_bone_global_pose(hb)
			if eb[0] >= 0 and eb[1] >= 0:
				hx.origin = ((sk.global_transform * sk.get_bone_global_pose(eb[0])).origin + (sk.global_transform * sk.get_bone_global_pose(eb[1])).origin) * 0.5
			var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
			var right: Vector3 = fwd.cross(Vector3.UP).normalized()
			var sc: float = fig.scale.x
			var off: Vector3 = vw[4]
			var target: Vector3 = hx.origin + (right * off.x + Vector3.UP * off.y + fwd * off.z) * sc
			cam.fov = float(vw[3])
			cam.global_position = target + fwd.rotated(Vector3.UP, deg_to_rad(float(vw[1]))) * float(vw[2]) * sc + Vector3(0, 0.04, 0)
			cam.look_at(target)
			await _frames(3)
			get_viewport().get_texture().get_image().save_png("%s_%02d_%s_%s.png" % [out, n, tag, vw[0]])
			n += 1
	for mo in moments:
		fig.play(String(mo[0]))
		await _frames(3)
		fig.anim.seek(float(mo[1]), true)
		fig.anim.pause()
		await _frames(8)
		await shoot.call("%s%d" % [mo[0], int(float(mo[1]) * 10.0)], VIEWS if mo[0] == "idle" and float(mo[1]) < 1.0 else [VIEWS[1], VIEWS[3], VIEWS[4], VIEWS[6], VIEWS[7]])
	fig.play("idle")
	await _frames(3)
	fig.anim.seek(0.4, true)
	fig.anim.pause()
	if String(args.get("set", "full")) == "beast":           # (phase 5: a beast race's own sliders, on its classic head)
		for sh in [["rest", {}], ["tusks_up", {"tusks": 1.0}], ["tusks_down", {"tusks": -1.0}], ["crest_up", {"crest": 1.0}],
				["crest_down", {"crest": -1.0}], ["muzzle", {"muzzle": 1.0, "muzzle_width": 1.0}]]:
			fig.set_shape(sh[1])
			await _frames(6)
			await shoot.call(String(sh[0]), [VIEWS[0], VIEWS[1], VIEWS[2]])
		print("[hd2] done ", n, " shots")
		get_tree().quit()
		return
	if String(args.get("set", "full")) == "makeup":
		var plain := fig.look.duplicate(true)
		for lk in MAKEUP:
			var ch: Dictionary = (lk[1] as Dictionary).duplicate()
			var sh := {}
			if ch.has("lash_len_shape"):
				sh["lash_len"] = ch["lash_len_shape"]
				ch.erase("lash_len_shape")
			if ch.has("_shape"):
				sh = ch["_shape"]
				ch.erase("_shape")
			var ex := int(ch.get("_expr", 0))
			ch.erase("_expr")
			fig.look = plain.duplicate(true)
			fig.expression = {}
			fig.apply(ch)
			fig.set_shape(sh)
			if ex > 0:
				fig.set_expression(ex)
			await _frames(6)
			await shoot.call(String(lk[0]), [VIEWS[0], VIEWS[4]])
		print("[hd2] done ", n, " shots")
		get_tree().quit()
		return
	if not quick:
		for lk in LOOKS:
			fig.set_shape(lk[1])
			await _frames(8)
			await shoot.call(String(lk[0]), [VIEWS[1], VIEWS[4], VIEWS[2], VIEWS[8]])
		fig.set_shape({})
	# the classic head, for the same views (the toggle)
	fig.apply({"hd": 0})
	await _frames(8)
	print("[hd2] classic: is_hd ", fig.is_hd())
	await shoot.call("classic", [VIEWS[1]])
	fig.apply({"hd": 1})
	await _frames(8)
	await shoot.call("hd_again", [VIEWS[1]])
	print("[hd2] done ", n, " shots")
	get_tree().quit()
