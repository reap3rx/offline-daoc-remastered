extends CanvasLayer
## EDIT UI (owner 2026-11-04: "make sure every new UI element is movable. Maybe in the escape menu, there can be a
## 'Edit UI' button that does all of the elements that we've done, including the action combat floating text and the
## like"): Options > EDIT UI. Every piece of the modern HUD gets a gold frame with its name - drag it anywhere
## (ModernHud.custom keeps where); with Action Combat on, its style lights and defense text are framed too (its own
## offsets, kept per character as before), and the panel turns its parts on and off - floating combat text among them
## (that one rises over whoever is hit, so it has no place of its own to move). RESET puts everything back, DONE or Esc
## ends it. Windows (bags, Hero, chat, the sheets) already move by their title bars.

const AC := preload("res://game/combat/action_combat.gd")
var ui: GameUI
var _had_ac := false
var _view: Control
var _panel: PanelContainer
var _items: Array = []               # [{id, name, kind ("hud" / "ac"), ctrl}]
var _drag := -1
var _from := Vector2.ZERO
var _hover := -1
var _layout_pick: OptionButton


func _ac():
	var scene := get_tree().current_scene
	var ac = scene.get("action_combat") if scene else null
	return ac if ac != null and bool(ac.get("on")) else null


func open(game_ui: GameUI) -> void:
	ui = game_ui
	layer = 60
	_view = Control.new()
	_view.set_anchors_preset(Control.PRESET_FULL_RECT)
	_view.mouse_filter = Control.MOUSE_FILTER_STOP
	_view.draw.connect(_draw_frames)
	_view.gui_input.connect(_input_on_view)
	add_child(_view)
	var ac = _ac()
	_had_ac = ac != null
	if ac:
		ac._editing = true                                  # (draws its movable parts, frees the cursor, no fighting)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if ui.modern and ui.modern.burden:                      # (the encumbered bag shows while you place it)
		ui.modern.burden.preview = true
		ui.modern.burden.refresh()
	if ui._channel_bar:                                     # (the spell charge shows a sample while you place it)
		ui._channel_bar.preview = true
		ui._channel_bar.visible = true
	if ui.modern:                                           # (the layout in use now stays while you arrange it)
		ui.modern.set("lock_mode", 1 if ui.modern.pad_mode else 0)
	_collect()
	_build_panel()


func _collect() -> void:
	_items = []
	if ui.modern:
		for e in ui.modern.movable():
			if e[2] != null and is_instance_valid(e[2]):
				_items.append({"id": String(e[0]), "name": String(e[1]), "kind": "hud", "ctrl": e[2]})
	if _ac():
		_items.append({"id": "lights", "name": "STYLE LIGHTS", "kind": "ac"})
		_items.append({"id": "flash", "name": "DEFENSE TEXT", "kind": "ac"})


## An item's frame on the screen (pixels).
func _rect(it: Dictionary) -> Rect2:
	if String(it.kind) == "ac":
		var ac = _ac()
		if ac == null:
			return Rect2()
		return ac.hud.get_global_transform_with_canvas() * ac._part_rect(String(it.id))
	var c: Control = it.ctrl
	var sz := c.size
	if sz.x < 40.0 or sz.y < 20.0:                          # (an empty strip: still something to take hold of)
		sz = sz.max(Vector2(120, 26))
	return c.get_global_transform_with_canvas() * Rect2(Vector2.ZERO, sz)


func _move(it: Dictionary, screen_delta: Vector2) -> void:
	if String(it.kind) == "ac":
		var ac = _ac()
		if ac:
			var d: Vector2 = ac.hud.get_global_transform_with_canvas().affine_inverse().basis_xform(screen_delta)
			ac._offset[String(it.id)] = (ac._offset.get(String(it.id), Vector2.ZERO) as Vector2) + d
			ac.hud.queue_redraw()
		return
	var c: Control = it.ctrl
	var par := c.get_parent() as CanvasItem
	var d2 := par.get_global_transform_with_canvas().affine_inverse().basis_xform(screen_delta) if par else screen_delta
	var area: Vector2 = ui.area()
	c.position = (c.position + d2).clamp(Vector2.ZERO, (area - c.size).max(Vector2.ZERO))


func _let_go(it: Dictionary) -> void:
	if String(it.kind) == "ac":
		var ac = _ac()
		if ac:
			ac._save_layout()
		return
	if ui.modern:
		ui.modern.keep_place(String(it.id), it.ctrl)


func _input_on_view(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_drag = _at(event.position)
			_from = event.position
		elif _drag >= 0:
			_let_go(_items[_drag])
			_drag = -1
		_view.accept_event()
		_view.queue_redraw()
	elif event is InputEventMouseMotion:
		if _drag >= 0:
			_move(_items[_drag], event.position - _from)
			_from = event.position
		else:
			_hover = _at(event.position)
		_view.accept_event()
		_view.queue_redraw()


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()
	elif event is InputEventJoypadButton:
		_pad_button(event as InputEventJoypadButton)
		get_viewport().set_input_as_handled()            # (the controller's buttons are the editor's while it is open)


# ---------------------------------------------------------------- the controller (owner 2026-11-23: "UI editing on
# controller. hitting A on it will allow you to lock in on an element and move it")
# The d-pad picks a piece (the nearest that way), A takes hold of it, the left stick or the d-pad moves it, A again
# puts it down (B too). Y switches the layout being arranged (keyboard and mouse / controller). B with nothing held, or
# MENU, ends it.
var _pad_sel := -1
var _pad_held := false
const PAD_SPEED := 700.0                       # pixels a second, the stick all the way over
const PAD_NUDGE := 6.0                         # pixels a d-pad press while holding a piece


func _pad_button(e: InputEventJoypadButton) -> void:
	if not e.pressed:
		return
	if _items.is_empty():
		return
	if _pad_sel < 0 or _pad_sel >= _items.size():
		_pad_sel = 0
	var dirs := {JOY_BUTTON_DPAD_LEFT: Vector2.LEFT, JOY_BUTTON_DPAD_RIGHT: Vector2.RIGHT, JOY_BUTTON_DPAD_UP: Vector2.UP,
			JOY_BUTTON_DPAD_DOWN: Vector2.DOWN}
	match e.button_index:
		JOY_BUTTON_A:
			if _pad_held:
				_let_go(_items[_pad_sel])
				_pad_held = false
			else:
				_pad_held = true
		JOY_BUTTON_B:
			if _pad_held:
				_let_go(_items[_pad_sel])
				_pad_held = false
			else:
				close()
				return
		JOY_BUTTON_START:
			close()
			return
		JOY_BUTTON_Y:
			_switch_layout(not (ui.modern and ui.modern.pad_mode))
		_:
			if dirs.has(e.button_index):
				var d: Vector2 = dirs[e.button_index]
				if _pad_held:
					_move(_items[_pad_sel], d * PAD_NUDGE)
				else:
					_pad_pick(d)
	_hover = _pad_sel
	_view.queue_redraw()


## The nearest piece that way from the one picked (wrapping round to the far side when there is none).
func _pad_pick(dir: Vector2) -> void:
	var here := _rect(_items[_pad_sel]).get_center()
	var best := -1
	var best_score := INF
	var far := -1
	var far_d := -INF
	for i in _items.size():
		if i == _pad_sel:
			continue
		var r := _rect(_items[i])
		if r.size == Vector2.ZERO:
			continue
		var d := r.get_center() - here
		var along := d.dot(dir)
		if along > 4.0:
			var score := along + absf(d.cross(dir)) * 2.0
			if score < best_score:
				best_score = score
				best = i
		elif -along > far_d:
			far_d = -along
			far = i
	_pad_sel = best if best >= 0 else (far if far >= 0 else _pad_sel)


## Which layout is being arranged: the controller's or the keyboard and mouse one.
func _switch_layout(pad: bool) -> void:
	if ui.modern == null:
		return
	if _pad_held and _pad_sel >= 0 and _pad_sel < _items.size():
		_let_go(_items[_pad_sel])
	_pad_held = false
	_drag = -1
	ui.modern.set("lock_mode", 1 if pad else 0)
	ui.modern.set_pad_mode(pad)
	_collect()
	_pad_sel = mini(_pad_sel, _items.size() - 1)
	if _layout_pick and is_instance_valid(_layout_pick):
		_layout_pick.select(1 if pad else 0)


func _process(_d: float) -> void:
	if _pad_held and _pad_sel >= 0 and _pad_sel < _items.size() and Pad.device >= 0:
		var v := Vector2(Input.get_joy_axis(Pad.device, JOY_AXIS_LEFT_X), Input.get_joy_axis(Pad.device, JOY_AXIS_LEFT_Y))
		if v.length() > 0.2:
			_move(_items[_pad_sel], v * PAD_SPEED * _d)
	if _had_ac:                                          # (Action Combat's own Esc ended its part: all of it ends)
		var scene := get_tree().current_scene
		var ac = scene.get("action_combat") if scene else null
		if ac == null or not bool(ac.get("_editing")):
			close()
			return
	if _view:
		_view.queue_redraw()


func _at(p: Vector2) -> int:
	for i in range(_items.size() - 1, -1, -1):           # (the smaller pieces on top win: last first)
		if _rect(_items[i]).has_point(p):
			return i
	return -1


func _draw_frames() -> void:
	_view.draw_rect(Rect2(Vector2.ZERO, _view.size), Color(0, 0, 0, 0.18))
	var f := UiArt.font(true)
	var fs := int(round(11.0 * maxf(1.0, ui.root.scale.x)))   # (the names at the HUD's own scale)
	for i in _items.size():
		var r := _rect(_items[i])
		if r.size == Vector2.ZERO:
			continue
		var hot := i == _drag or i == _hover or i == _pad_sel
		if i == _pad_sel and _pad_held:
			_view.draw_rect(r.grow(3.0), Color(0.45, 0.85, 1.0, 1.0), false, 2.0)   # (held by the controller)
		_view.draw_rect(r, Color(1.0, 0.82, 0.35, 0.16 if hot else 0.07))
		_view.draw_rect(r, Color(1.0, 0.82, 0.35, 1.0 if hot else 0.7), false, 2.0 if hot else 1.0)
		var label := String(_items[i].name)
		var at := r.position + Vector2(4, fs + 2)
		_view.draw_string_outline(f, at, label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 3, Color(0, 0, 0, 0.9))
		_view.draw_string(f, at, label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(1.0, 0.86, 0.45))


func _build_panel() -> void:
	_panel = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.045, 0.04, 0.92)
	sb.border_color = Color(0.86, 0.71, 0.38)
	sb.set_border_width_all(1)
	sb.set_content_margin_all(10)
	_panel.add_theme_stylebox_override("panel", sb)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	_panel.add_child(box)
	box.add_child(UiArt.label("EDIT UI", 12, UiArt.GOLD_HI))
	var hint := UiArt.label("Drag any framed piece to move it. Windows move by their title bars. Controller: the d-pad "
			+ "picks a piece, A takes hold of it (move it with the left stick), A puts it down, Y switches the layout, B ends.",
			9, UiArt.CREAM)
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD
	hint.custom_minimum_size = Vector2(250, 0)
	box.add_child(hint)
	if ui.modern:
		box.add_child(UiArt.label("LAYOUT TO ARRANGE", 9, UiArt.DIM))
		_layout_pick = OptionButton.new()
		_layout_pick.add_item("KEYBOARD AND MOUSE")
		_layout_pick.add_item("CONTROLLER")
		_layout_pick.focus_mode = Control.FOCUS_NONE
		_layout_pick.add_theme_font_override("font", UiArt.font(true))
		_layout_pick.add_theme_font_size_override("font_size", 10)
		_layout_pick.select(1 if ui.modern.pad_mode else 0)
		_layout_pick.item_selected.connect(func(i: int): _switch_layout(i == 1))
		box.add_child(_layout_pick)
	var ac = _ac()
	if ac:
		box.add_child(UiArt.label("ACTION COMBAT - SHOW", 9, UiArt.DIM))
		for part in AC.PARTS:
			var cb := CheckBox.new()
			cb.text = String(part[1])
			cb.focus_mode = Control.FOCUS_NONE
			cb.button_pressed = bool(ac._show.get(part[0], true))
			cb.add_theme_font_override("font", UiArt.font(false))
			cb.add_theme_font_size_override("font_size", 10)
			var id := String(part[0])
			cb.toggled.connect(func(v: bool):
				ac._show[id] = v
				ac._save_layout())
			box.add_child(cb)
	else:
		var n := UiArt.label("Turn on Action Combat to place its style lights and defense text too.", 9, UiArt.DIM)
		n.autowrap_mode = TextServer.AUTOWRAP_WORD
		n.custom_minimum_size = Vector2(250, 0)
		box.add_child(n)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var reset := UiArt.button("RESET ALL", Vector2(110, 20), 10)
	reset.pressed.connect(_reset)
	row.add_child(reset)
	var done := UiArt.button("DONE", Vector2(110, 20), 10)
	done.pressed.connect(close)
	row.add_child(done)
	box.add_child(row)
	add_child(_panel)
	_panel.scale = Vector2.ONE * maxf(1.0, ui.root.scale.x * 0.9)   # (as big as the HUD it arranges)
	await get_tree().process_frame
	var vp := get_viewport().get_visible_rect().size
	_panel.position = Vector2(vp.x * 0.22, vp.y * 0.2)               # (clear of the middle, where the combat parts sit)


func _reset() -> void:
	if ui.modern:
		ui.modern.reset_places()
	var ac = _ac()
	if ac:
		for id in AC.DEFAULT_OFFSET:
			ac._offset[id] = AC.DEFAULT_OFFSET[id]
		ac._save_layout()


var _closed := false


func close() -> void:
	if _closed:
		return
	_closed = true
	if ui and ui.modern and is_instance_valid(ui.modern):   # (back to following whatever is in use)
		ui.modern.set("lock_mode", -1)
		var pb = ui.modern._pad_bar()
		ui.modern.set_pad_mode(pb != null and bool(pb.shown()))
	if ui and is_instance_valid(ui._channel_bar):
		ui._channel_bar.preview = false
	if ui and ui.modern and is_instance_valid(ui.modern) and ui.modern.burden:
		ui.modern.burden.preview = false
		ui.modern.burden.refresh()
	var ac = _ac()
	if ac:
		ac._editing = false
		ac._drag = ""
		ac._save_layout()
	queue_free()
