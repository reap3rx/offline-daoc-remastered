extends RefCounted
## Housing's menus (owner 2026-11-02: interiors, purchasing and decorating): a short list of choices in the client's
## black granite (UiArt.confirm's frame) - the house's menu (go in / out, its shops and looks, information, the
## lockbox), a furniture piece's (turn it, take it back), a garden piece's. A click outside closes it.

static var _open: Control = null


## entries: [[caption, Callable], ...] - each closes the menu, then calls its Callable.
static func open(parent: Control, title: String, entries: Array) -> Control:
	close()
	var shade := Control.new()
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_STOP
	parent.add_child(shade)
	var w := 220.0
	var h := 34.0 + entries.size() * 20.0 + 10.0
	var box := Control.new()
	box.size = Vector2(w, h)
	var area := parent.size if parent.size != Vector2.ZERO else parent.get_viewport_rect().size
	var at := parent.get_viewport().get_mouse_position()
	box.position = Vector2(clampf(at.x + 12.0, 4.0, area.x - w - 4.0), clampf(at.y - h * 0.5, 4.0, area.y - h - 4.0)).floor()
	shade.add_child(box)
	var holder := Control.new()
	holder.scale = Vector2(0.25, 0.25)
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var np := NinePatchRect.new()
	np.texture = UiArt.tex("chatext")
	np.region_rect = Rect2(0, 64 * UiArt.K, 512 * UiArt.K, 64 * UiArt.K)
	var m := [3, 12, 12, 3]
	var sides := [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]
	for i in 4:
		np.set_patch_margin(sides[i], int(m[i] * UiArt.K))
	np.size = box.size * 4.0
	np.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(np)
	box.add_child(holder)
	var t := UiArt.label(title.to_upper(), 10, UiArt.GOLD_HI)
	t.position = Vector2(0, 12)
	t.size = Vector2(w, 14)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(t)
	var y := 32.0
	for e in entries:
		var b := UiArt.button(String(e[0]), Vector2(w - 36, 16), 9)
		b.position = Vector2(18, y)
		var cb: Callable = e[1]
		b.pressed.connect(func():
			close()
			if cb.is_valid():
				cb.call())
		box.add_child(b)
		y += 20.0
	shade.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and not Rect2(box.position, box.size).has_point(ev.position):
			close())
	_open = shade
	return shade


static func close() -> void:
	if _open and is_instance_valid(_open):
		_open.queue_free()
	_open = null
