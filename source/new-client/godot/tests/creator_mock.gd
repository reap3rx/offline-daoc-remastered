extends Node
## Debug (claude 2026-11-06): a still mock-up of the new character creator (owner: "World of Warcraft has a good
## template ... Realm styling, menus and choices to cycle through where we can ... color pickers where it makes
## sense"): the character standing in its realm, the name across the top, FACE / BODY at the top right, the option
## rows down the right (arrows to cycle, colour bars, sliders for the fine shape), camera buttons top left, BACK and
## FINISH. Nothing works - it's a picture to judge the layout by. Shots: <out>_face.png, <out>_body.png.
##   Godot --path new-client/godot -- --zone=0 --time=17.5 --probe=creator_mock --mute --no-npcs --spot=X,Z
##       --figure=zz_proto_bri_m [--out=<prefix>] [--yaw=<deg>]
var v: Node
var layer: CanvasLayer
var W := 1600.0
var H := 900.0

const GOLD := Color(0.93, 0.76, 0.36)
const GOLD_DIM := Color(0.62, 0.5, 0.26)
const CREAM := Color(0.95, 0.91, 0.82)
const DIM := Color(0.68, 0.64, 0.57)
const ACCENT := Color(0.55, 0.09, 0.08)          # Albion's crimson


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(300.0).timeout.connect(func(): print("[cm] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/walk/creator"))
	var prefix := String(args.get("figure", "zz_proto_bri_m"))
	await get_tree().create_timer(12.0).timeout
	get_window().size = Vector2i(int(W), int(H))
	for n in ["hud", "ui"]:
		if v.get(n):
			v.get(n).visible = false
	v.player.visible = false
	var base: Vector3 = v.player.global_position
	if args.has("spot"):
		var xz := String(args["spot"]).split(",")
		base = Vector3(float(xz[0]), 0.0, float(xz[1]))
		base.y = v.zone.height_at(base.x, base.z)
	var yaw := deg_to_rad(float(args.get("yaw", "0")))
	var fig := Fig3Figure.new()
	v.add_child(fig)
	if not fig.load_figure(prefix):
		get_tree().quit()
		return
	fig.apply({"face": 2, "hair": 1, "hair_color": 1, "eyes": 2, "skin": 1})
	for mi in fig.model.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for b in m.get_blend_shape_count():
			var nm := String(m.mesh.get_blend_shape_name(b))
			var preset := {"fx_nose_length": 0.6, "fx_nose_bridge": 0.7, "fx_cheekbones": 0.6, "fx_jaw_width": 0.3, "fx_chin_point": 0.5, "fx_brow_depth": 0.4}
			if preset.has(nm):
				m.set_blend_shape_value(b, preset[nm])
	fig.global_position = base
	fig.rotation.y = yaw
	fig.play("idle")
	var cam := Camera3D.new()
	cam.near = 0.05
	v.add_child(cam)
	cam.make_current()
	var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
	var side: Vector3 = fwd.cross(Vector3.UP).normalized()
	layer = CanvasLayer.new()
	v.add_child(layer)
	# --- the body view: the whole figure, a little to the left of centre
	var dist := float(args.get("dist", "6.0"))
	cam.fov = 30.0
	cam.global_position = base + fwd * dist + Vector3(0, 1.35, 0) - side * 0.9
	cam.look_at(base + Vector3(0, 1.0, 0) - side * 0.9)
	_build_ui("body")
	await _frames(40)
	get_viewport().get_texture().get_image().save_png(out + "_body.png")
	print("[cm] body")
	# --- the face view: the camera comes in to the head
	for c in layer.get_children():
		c.queue_free()
	var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
	var head: Vector3 = sk.global_transform * sk.get_bone_global_pose(sk.find_bone("Bip01 Head")).origin
	cam.fov = 26.0
	cam.global_position = head + fwd.rotated(Vector3.UP, deg_to_rad(12)) * 1.15 + Vector3(0, 0.02, 0) - side * 0.18
	cam.look_at(head + Vector3(0, -0.04, 0) - side * 0.18)
	_build_ui("face")
	await _frames(40)
	get_viewport().get_texture().get_image().save_png(out + "_face.png")
	print("[cm] face")
	get_tree().quit()


# ---------------------------------------------------------------- the mock UI

func _panel(r: Rect2, alpha := 0.72, border := GOLD_DIM, radius := 6) -> Panel:
	var p := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.04, 0.035, alpha)
	sb.border_color = border
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(radius)
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 6
	p.add_theme_stylebox_override("panel", sb)
	p.position = r.position
	p.size = r.size
	layer.add_child(p)
	return p


func _text(t: String, at: Vector2, sz: int, col := CREAM, w := 0.0, align := HORIZONTAL_ALIGNMENT_LEFT, parent: Node = null) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_override("font", UiArt.font(true))
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	l.add_theme_constant_override("outline_size", 4)
	l.position = at
	if w > 0:
		l.size = Vector2(w, sz + 8)
		l.horizontal_alignment = align
	(parent if parent else layer).add_child(l)
	return l


func _round(c: Vector2, r: float, label: String, active := false) -> void:
	var p := _panel(Rect2(c - Vector2(r, r), Vector2(2 * r, 2 * r)), 0.85, GOLD if active else GOLD_DIM, int(r))
	var sb := p.get_theme_stylebox("panel") as StyleBoxFlat
	sb.set_border_width_all(3 if active else 1)
	if active:
		sb.bg_color = Color(0.32, 0.22, 0.06, 0.92)
	_text(label, c - Vector2(r, 9), 14, GOLD if active else CREAM, 2 * r, HORIZONTAL_ALIGNMENT_CENTER)


func _arrow_button(at: Vector2, glyph: String) -> void:
	var p := _panel(Rect2(at, Vector2(26, 26)), 0.9, GOLD_DIM, 4)
	(p.get_theme_stylebox("panel") as StyleBoxFlat).bg_color = Color(0.2, 0.15, 0.06, 0.95)
	_text(glyph, at + Vector2(0, 1), 16, GOLD, 26, HORIZONTAL_ALIGNMENT_CENTER)


## One option row: the label at the right edge's left, then  [<] [ value ] [>]  - or a colour bar, or a slider.
func _row(y: float, label: String, kind: String, value: Variant) -> void:
	var x0 := W - 470.0
	_text(label.to_upper(), Vector2(x0, y + 3), 14, CREAM, 150, HORIZONTAL_ALIGNMENT_RIGHT)
	var bx := x0 + 162
	match kind:
		"cycle":
			_arrow_button(Vector2(bx, y), "<")
			var p := _panel(Rect2(bx + 32, y, 196, 26), 0.8)
			_text(String(value), Vector2(bx + 32, y + 4), 13, GOLD, 196, HORIZONTAL_ALIGNMENT_CENTER)
			_arrow_button(Vector2(bx + 234, y), ">")
		"colour":
			_arrow_button(Vector2(bx, y), "<")
			var p := _panel(Rect2(bx + 32, y, 196, 26), 0.8)
			var sw := ColorRect.new()
			sw.color = value
			sw.position = Vector2(bx + 38, y + 6)
			sw.size = Vector2(184, 14)
			layer.add_child(sw)
			var hint := ColorRect.new()                  # the picker's handle: a click opens the full colour picker
			hint.color = Color(1, 1, 1, 0.9)
			hint.position = Vector2(bx + 38 + 184 * 0.62, y + 3)
			hint.size = Vector2(3, 20)
			layer.add_child(hint)
			_arrow_button(Vector2(bx + 234, y), ">")
		"slider":
			var track := ColorRect.new()
			track.color = Color(0.25, 0.21, 0.15, 0.95)
			track.position = Vector2(bx + 6, y + 11)
			track.size = Vector2(250, 4)
			layer.add_child(track)
			var fill := ColorRect.new()
			fill.color = GOLD_DIM
			var t := float(value)
			fill.position = Vector2(bx + 6 + 125, y + 11)
			fill.size = Vector2(125 * t, 4)
			if t < 0:
				fill.position.x = bx + 6 + 125 + 125 * t
				fill.size.x = -125 * t
			layer.add_child(fill)
			var knob := _panel(Rect2(Vector2(bx + 6 + 125 + 125 * t - 8, y + 5), Vector2(16, 16)), 1.0, GOLD, 8)
			(knob.get_theme_stylebox("panel") as StyleBoxFlat).bg_color = Color(0.45, 0.32, 0.1, 1)
			var mid := ColorRect.new()
			mid.color = Color(1, 1, 1, 0.35)
			mid.position = Vector2(bx + 6 + 124, y + 7)
			mid.size = Vector2(2, 12)
			layer.add_child(mid)


func _build_ui(tab: String) -> void:
	# a soft vignette, darker on the right where the options sit
	var shade := ColorRect.new()
	shade.position = Vector2(W - 520, 0)
	shade.size = Vector2(520, H)
	shade.color = Color(0, 0, 0, 0.28)
	layer.add_child(shade)
	# camera buttons, top left: turn left / right, zoom out / in, undo / redo
	var cx := 26.0
	for g in ["<", ">", "-", "+", "U", "R"]:
		_arrow_button(Vector2(cx, 24), g)
		cx += 34 if g not in [">", "+"] else 46
	# realm and choices, top left under the camera row
	var rp := _panel(Rect2(24, 66, 300, 64), 0.75, GOLD_DIM)
	_text("ALBION", Vector2(36, 72), 13, Color(0.86, 0.35, 0.3))
	_text("BRITON  -  ARMSMAN", Vector2(36, 92), 18, GOLD)
	_text("Change race or class", Vector2(36, 114), 11, DIM)
	# the name, top centre, with the random-name die
	_text("NAME", Vector2(W * 0.5 - 150, 16), 15, CREAM, 300, HORIZONTAL_ALIGNMENT_CENTER)
	_panel(Rect2(W * 0.5 - 150, 40, 300, 34), 0.85, GOLD_DIM)
	_text("Aldric", Vector2(W * 0.5 - 150, 46), 18, CREAM, 300, HORIZONTAL_ALIGNMENT_CENTER)
	_panel(Rect2(W * 0.5 - 196, 41, 32, 32), 0.9, GOLD_DIM, 5)
	_text("?", Vector2(W * 0.5 - 196, 46), 18, GOLD, 32, HORIZONTAL_ALIGNMENT_CENTER)
	# FACE / BODY, top right, and the whole-look die
	_round(Vector2(W - 170, 64), 32, "FACE", tab == "face")
	_round(Vector2(W - 92, 64), 32, "BODY", tab == "body")
	_panel(Rect2(W - 248, 50, 30, 30), 0.9, GOLD_DIM, 5)
	_text("?", Vector2(W - 248, 54), 18, GOLD, 30, HORIZONTAL_ALIGNMENT_CENTER)
	# the options
	var y := 140.0
	if tab == "face":
		_text("APPEARANCE", Vector2(W - 470, y - 26), 13, GOLD, 440, HORIZONTAL_ALIGNMENT_CENTER)
		_row(y, "Skin Color", "colour", Color(0.93, 0.74, 0.62)); y += 36
		_row(y, "Face", "cycle", "Weathered"); y += 36
		_row(y, "Hair Style", "cycle", "Swept Back"); y += 36
		_row(y, "Hair Color", "colour", Color(0.72, 0.52, 0.22)); y += 36
		_row(y, "Beard", "cycle", "Moustache & Goatee"); y += 36
		_row(y, "Brows", "cycle", "Heavy"); y += 36
		_row(y, "Eye Color", "colour", Color(0.45, 0.58, 0.7)); y += 36
		_row(y, "Markings", "cycle", "Old Scar"); y += 46
		_text("FACE SHAPE", Vector2(W - 470, y - 8), 13, GOLD, 440, HORIZONTAL_ALIGNMENT_CENTER); y += 18
		_row(y, "Nose Length", "slider", 0.6); y += 30
		_row(y, "Nose Bridge", "slider", 0.7); y += 30
		_row(y, "Brow Ridge", "slider", 0.4); y += 30
		_row(y, "Cheekbones", "slider", 0.6); y += 30
		_row(y, "Jaw Width", "slider", 0.3); y += 30
		_row(y, "Chin", "slider", 0.5); y += 30
		_text("+ 12 more: eyes, mouth, ears ...", Vector2(W - 470, y + 2), 12, DIM, 440, HORIZONTAL_ALIGNMENT_RIGHT)
	else:
		_text("BODY", Vector2(W - 470, y - 26), 13, GOLD, 440, HORIZONTAL_ALIGNMENT_CENTER)
		_row(y, "Skin Color", "colour", Color(0.93, 0.74, 0.62)); y += 36
		_row(y, "Physique", "cycle", "Soldier"); y += 46
		_text("PROPORTIONS", Vector2(W - 470, y - 8), 13, GOLD, 440, HORIZONTAL_ALIGNMENT_CENTER); y += 18
		_row(y, "Height", "slider", 0.3); y += 30
		_row(y, "Build", "slider", 0.45); y += 30
		_row(y, "Shoulders", "slider", 0.35); y += 30
		_row(y, "Arms", "slider", 0.2); y += 30
		_row(y, "Legs", "slider", 0.0); y += 30
		_row(y, "Head Size", "slider", -0.1); y += 40
		_text("PREVIEW", Vector2(W - 470, y - 8), 13, GOLD, 440, HORIZONTAL_ALIGNMENT_CENTER); y += 18
		_row(y, "Outfit", "cycle", "Starting Clothes"); y += 36
		_row(y, "Pose", "cycle", "Idle"); y += 36
	# BACK and FINISH
	var back := _panel(Rect2(40, H - 76, 220, 48), 0.95, Color(0.9, 0.45, 0.35), 6)
	(back.get_theme_stylebox("panel") as StyleBoxFlat).bg_color = Color(ACCENT, 0.95)
	_text("<  BACK", Vector2(40, H - 64), 20, GOLD, 220, HORIZONTAL_ALIGNMENT_CENTER)
	var fin := _panel(Rect2(W - 300, H - 76, 260, 48), 0.95, GOLD, 6)
	(fin.get_theme_stylebox("panel") as StyleBoxFlat).bg_color = Color(0.28, 0.2, 0.06, 0.95)
	_text("FINISH", Vector2(W - 300, H - 64), 20, GOLD, 260, HORIZONTAL_ALIGNMENT_CENTER)
	_text("Drag to turn  -  scroll to zoom", Vector2(0, H - 30), 12, DIM, W, HORIZONTAL_ALIGNMENT_CENTER)
