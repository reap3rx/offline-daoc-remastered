extends Node
## Debug (claude 2026-11-06): the face-shape prototype (pipeline/face_morphs.py's fx_ targets) - one head in a set
## of slider presets, each from the front-side, in the game's own light. Each shot: <out>_<nn>.png.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=face_grid --mute --no-npcs --spot=450,600
##       --figure=zz_proto_bri_m [--out=<prefix>] [--angle=25]
var v: Node
var _fig: Fig3Figure

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
	_fig = fig
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
	var dist := float(args.get("dist", "0.85"))          # (--dist: further for the big heads - a dwarf's filled the frame)
	var lift := float(args.get("lift", "0.0"))
	cam.global_position = target + fwd.rotated(Vector3.UP, deg_to_rad(angle)) * dist * fig.scale.x + Vector3(0, 0.03 + lift, 0)
	cam.look_at(target + Vector3(0, 0.02 + lift, 0))
	var heads: Array = fig.model.find_children("*", "MeshInstance3D", true, false)
	var pset := String(args.get("presets", ""))
	var presets: Array = MOUTH if pset == "mouth" else (SKIN if pset == "skin" else PRESETS)
	if pset == "new":                               # (owner 2026-11-06's third pass: the new sliders)
		presets = [["Neutral", {}], ["Squint", {"eye_squint": 1.0}], ["Tip+", {"nose_tip_size": 1.0}],
			["Cheek+", {"cheek_puff": 1.0}], ["Cheek-", {"cheek_puff": -1.0}], ["Full lips", {"lips": 1.0}],
			["Thin lips", {"lips": -1.0}], ["Upper", {"upper_lip": 1.0}], ["Lower", {"lower_lip": 1.0}],
			["Smile", {"smile": 1.0}], ["Frown", {"smile": -1.0}], ["Pout", {"lip_out": 1.0, "mouth_width": -0.6}]]
	if pset == "paint":                             # the new paints, colours and placement
		presets = [["Smoke", {"paint": 7}], ["Crown", {"paint": 8, "paint_color": 2}], ["Nose", {"paint": 9}],
			["Tears", {"paint": 10, "paint_color": 1}], ["Wings", {"paint": 11}], ["Hooks", {"paint": 12, "paint_color": 4}],
			["Jaw", {"paint": 13, "paint_color": 1}], ["Dots", {"paint": 14, "paint_color": 3}], ["Rune", {"paint": 15}],
			["Fade", {"paint": 16, "paint_color": 1}], ["Mask up+big", {"paint": 1, "paint_y": 0.3, "paint_size": 1.3}],
			["Claws turned", {"paint": 2, "paint_turn": 25.0, "paint_color": 2}]]
	if pset == "colour":                            # custom colours, the nose-band freckles
		presets = [["Plain", {}], ["Deep skin", {"skin_rgb": [0.3, 0.19, 0.12]}], ["Brown skin", {"skin_rgb": [0.55, 0.37, 0.25]}],
			["Green eyes", {"eyes_rgb": [0.2, 0.6, 0.3]}], ["Violet eyes", {"eyes_rgb": [0.5, 0.3, 0.8]}],
			["Red hair", {"hair_color_rgb": [0.6, 0.2, 0.08]}], ["Blue hair", {"hair_color_rgb": [0.15, 0.25, 0.6]}],
			["Freckle band", {"freckles": 3}], ["Band dark", {"freckles": 3, "freckle_color": 2, "freckle_amt": 1.2}],
			["Brows black", {"brow_color": 1}], ["Lips custom", {"lip_color_rgb": [0.7, 0.2, 0.35], "lip_amt": 0.6}],
			["Sparse", {"freckles": 4}]]
	if pset == "newhair":                           # the styles made from models (pipeline/import_hair.py)
		presets = []
		var styles: Array = fig.meta.get("hair_styles", [])
		var cols := [1, 4, 8]
		var k := 0
		for si in styles.size():
			if bool(styles[si].get("imported", false)):
				for c in cols.slice(0, 2):
					presets.append(["%s %d" % [styles[si].label, c], {"hair": si, "hair_color": c, "beard": 0}])
				k += 1
		var bs: Array = fig.meta.get("beards", [])
		for b in bs.size():
			if bool(bs[b].get("imported", false)) and presets.size() < 12:
				presets.append(["Beard", {"hair": 0, "hair_color": 4, "beard": b + 1}])
		for si in styles.size():                    # (the sheet filled: the styles over the scalp cap)
			if bool(styles[si].get("imported", false)) and presets.size() < 12:
				presets.append(["%s cap" % styles[si].label, {"hair": si, "hair_color": 4, "beard": 0, "scalp_cap": 1}])
		for si in styles.size():
			if bool(styles[si].get("imported", false)) and presets.size() < 12:
				presets.append(["%s cap 8" % styles[si].label, {"hair": si, "hair_color": 8, "beard": 0, "scalp_cap": 1}])
	if pset == "looks":                             # (--looks=<json file>: [[label, look], ...] - any looks to compare)
		var d = JSON.parse_string(FileAccess.get_file_as_string(String(args.get("looks", ""))))
		if d is Array:
			presets = d
		var lf2 := FileAccess.open(out + "_names.txt", FileAccess.WRITE)
		for pr in presets:
			lf2.store_line(String(pr[0]))
		lf2.close()
	if pset == "allnew":                            # every new style, then beards and moustaches (--from, --count)
		presets = []
		var styles: Array = fig.meta.get("hair_styles", [])
		for si in styles.size():
			if bool(styles[si].get("imported", false)):
				presets.append(["%s - %s" % [styles[si].label, String(styles[si].get("mesh", "")).get_basename()], {"hair": si, "beard": 0, "hair_color": 1}])
		var bald := 0
		for si in styles.size():
			if styles[si].node == null:
				bald = si
		var bs: Array = fig.meta.get("beards", [])
		for b in bs.size():
			if bool(bs[b].get("imported", false)):
				presets.append(["%s - %s" % [bs[b].label, String(bs[b].get("mesh", "")).get_basename()], {"hair": bald, "beard": b + 1, "hair_color": 1, "scalp_cap": 1}])
		var ms: Array = fig.meta.get("moustaches", [])
		for m in ms.size():
			presets.append(["%s - %s" % [ms[m].label, String(ms[m].get("mesh", "")).get_basename()], {"hair": bald, "beard": 0, "moustache": m + 1, "hair_color": 1, "scalp_cap": 1}])
		var sb: Array = fig.meta.get("sideburns", [])
		for m in sb.size():
			presets.append(["%s - %s" % [sb[m].label, String(sb[m].get("mesh", "")).get_basename()], {"hair": bald, "beard": 0, "sideburns": m + 1, "hair_color": 1, "scalp_cap": 1}])
		if args.get("rings", "") != "":             # (only the parts with rings, and the sideburns)
			presets = presets.filter(func(pr): return String(pr[0]).begins_with("Sideburns") or _has_rings(pr[1]))
		var f0 := int(args.get("from", "0"))
		presets = presets.slice(f0, f0 + int(args.get("count", "999")))
		var lf := FileAccess.open(out + "_names.txt", FileAccess.WRITE)
		for pr in presets:
			lf.store_line(String(pr[0]))
		lf.close()
	if pset == "fit":                               # the hair sliders (hf_ targets) on the first new style
		presets = []
		var styles: Array = fig.meta.get("hair_styles", [])
		var si := 0
		for i in styles.size():
			if bool(styles[i].get("imported", false)) and String(styles[i].label).contains(String(args.get("style", ""))):
				si = i
				break
		var nd := String(styles[si].node)
		for v in [["As made", {}], ["Up +1", {"up": 1.0}], ["Up -1", {"up": -1.0}], ["Fwd +1", {"fwd": 1.0}],
				["Fwd -1", {"fwd": -1.0}], ["Size +1", {"size": 1.0}], ["Size -1", {"size": -1.0}], ["Width +1", {"width": 1.0}],
				["Width -1", {"width": -1.0}], ["Len +1", {"len": 1.0}], ["Len -1", {"len": -1.0}], ["Mix", {"size": -0.5, "up": -0.4, "len": 0.6}]]:
			presets.append([v[0], {"hair": si, "beard": 0, "hair_fit": {nd: v[1]}}])
	if pset == "cap":                               # the scalp cap (figure.json hair_under): bald, under styles, sliders
		presets = []
		var styles: Array = fig.meta.get("hair_styles", [])
		var bald := -1
		for si in styles.size():
			if styles[si].node == null:
				bald = si
				break
		var vanilla: Array = []
		var made: Array = []
		for si in fig.creator_styles():
			if styles[si].node != null:
				(made if bool(styles[si].get("imported", false)) else vanilla).append(si)
		if bald >= 0:
			presets.append(["Bald", {"hair": bald, "scalp_cap": 0, "beard": 0}])
			presets.append(["Bald cap", {"hair": bald, "scalp_cap": 1, "beard": 0}])
			presets.append(["Bald cap dark", {"hair": bald, "scalp_cap": 1, "hair_color": 4, "beard": 0}])
			presets.append(["Bald cap Brute", {"hair": bald, "scalp_cap": 1, "beard": 0, "_shape": {"brow_depth": 1.0, "brow_height": -0.6, "jaw_width": 1.0}}])
			presets.append(["Bald cap Long", {"hair": bald, "scalp_cap": 1, "beard": 0, "_shape": {"brow_height": 1.0, "eye_height": 0.6, "chin_length": 1.0}}])
		if bald < 0 and not vanilla.is_empty():     # (no bald style: the cap alone, the styles hidden)
			presets.append(["Cap only", {"hair": vanilla[0], "scalp_cap": 1, "beard": 0, "_nohair": true}])
			presets.append(["Cap only dark", {"hair": vanilla[0], "scalp_cap": 1, "beard": 0, "hair_color": 4, "_nohair": true}])
			presets.append(["Cap Brute", {"hair": vanilla[0], "scalp_cap": 1, "beard": 0, "_nohair": true, "_shape": {"brow_depth": 1.0, "brow_height": -0.6, "jaw_width": 1.0}}])
		for si in vanilla.slice(0, 3):
			presets.append(["Hair %d cap" % si, {"hair": si, "scalp_cap": 1, "beard": 0}])
		for si in made:
			if presets.size() < 12:
				presets.append(["%s cap" % styles[si].label, {"hair": si, "scalp_cap": 1, "beard": 0}])
		for si in made:                             # (fill the sheet: the styles bare, to compare)
			if presets.size() < 12:
				presets.append(["%s bare" % styles[si].label, {"hair": si, "scalp_cap": 0, "beard": 0}])
		for si in vanilla:
			if presets.size() < 12:
				presets.append(["Hair %d bare" % si, {"hair": si, "scalp_cap": 0, "beard": 0}])
		var k := 0
		while presets.size() < 12 and not vanilla.is_empty():    # (a race of few styles: its styles capped, in more colours)
			var si: int = vanilla[k % vanilla.size()]
			presets.append(["Hair %d cap c%d" % [si, 3 + k], {"hair": si, "scalp_cap": 1, "beard": 0, "hair_color": 3 + k}])
			k += 1
	if pset == "turban":                            # the Saracen men's turban over each hair style, dyed
		presets = []
		var k := 0
		for si in fig.creator_styles():
			presets.append(["Hair %d" % (si + 1), {"hair": si, "turban": 1, "turban_color": k % 8}])
			k += 1
		for si in fig.creator_styles():
			if presets.size() < 12:
				presets.append(["Bare %d" % (si + 1), {"hair": si, "turban": 0}])
	if pset == "beard":                             # every beard on one beardless style, then the styles bare
		presets = []
		var styles: Array = fig.meta.get("hair_styles", [])
		var bare := 0
		for si in styles.size():
			if styles[si].node != null and int(styles[si].get("beard", 0)) == 0:
				bare = si
				break
		for b in fig.option_count("beard"):
			presets.append(["Beard %d" % b, {"hair": bare, "beard": b}])
		for si in styles.size():
			if presets.size() < 12 and int(styles[si].get("beard", 0)) > 0 and styles[si].node != null:
				presets.append(["Hair %d bare" % (si + 1), {"hair": si, "beard": 0}])
	var names := []
	for p in presets:
		names.append(String(p[0]))
	for i in presets.size():
		var vals: Dictionary = presets[i][1]
		if pset in ["beard", "turban", "newhair", "cap", "fit", "allnew", "looks"]:
			fig.look = {"face": 0, "hair_color": 1, "eyes": 2, "skin": 1}
			var shp: Dictionary = vals.get("_shape", {})
			var hide_hair := bool(vals.get("_nohair", false))
			vals = vals.duplicate()
			vals.erase("_shape")
			vals.erase("_nohair")
			fig.apply(fig.layered_changes())
			fig.apply(vals)
			fig.set_shape(shp)
			if hide_hair:
				for st in fig.meta.get("hair_styles", []):
					if st.node != null:
						for mh in fig._parts(String(st.node)):
							mh.visible = false
			await _frames(2)
			vals = shp
		if pset in ["skin", "paint", "colour"]:
			fig.look = {"face": 0, "hair": int(args.get("hair", "1")), "hair_color": 1, "eyes": 2, "skin": 1}
			fig.apply(fig.layered_changes())
			fig.apply(vals)
			vals = {}
		if args.has("capred"):                      # (debug: the scalp cap in a plain red material)
			var red := StandardMaterial3D.new()
			red.albedo_color = Color(0.8, 0.1, 0.1)
			for mh in fig._parts("new_scalp"):
				mh.material_override = red
			if args.has("headstd"):
				var hs := StandardMaterial3D.new()
				hs.albedo_color = Color(0.9, 0.75, 0.65)
				for mh in fig._parts("head"):
					mh.material_override = hs
		if args.has("nohead"):                      # (debug: only the scalp cap drawn)
			for mh in heads:
				print("[fg] mesh ", mh.name, " ", mh.get_parent().name, " ", mh.visible)
				mh.visible = String(mh.name).contains("scalp") or String(mh.get_parent().name).contains("scalp")
		if args.has("nohair"):                      # (debug: the style itself hidden - what is under it)
			var sts: Array = fig.meta.get("hair_styles", [])
			for st in sts:
				if st.node != null:
					for mh in fig._parts(String(st.node)):
						mh.visible = false
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


func _has_rings(l: Dictionary) -> bool:
	for kv in [["hair", "hair_styles", 0], ["beard", "beards", 1], ["moustache", "moustaches", 1]]:
		if not l.has(String(kv[0])):
			continue
		var i := int(l[String(kv[0])]) - int(kv[2])
		var list: Array = _fig.meta.get(String(kv[1]), [])
		if (kv[0] == "hair" and l.has("moustache")) or (kv[0] == "hair" and int(l.get("beard", 0)) > 0):
			continue                                   # (the bald style under a beard)
		if i >= 0 and i < list.size() and (list[i] as Dictionary).has("jewels"):
			return true
	return false
