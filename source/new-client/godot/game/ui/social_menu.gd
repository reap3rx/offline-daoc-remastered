extends Control
## The interact menu (owner 2026-11-11: hold Interact on another player, a bot or your pet - "a small menu that has
## ways you can interact with that person"): invite / kick, buff, follow, assist, whisper, your pet's orders. The
## server decides what is offered (SocialMenuCommandHandler: you, your pet, a bot of your realm, your group's leader)
## and sends #SMENU|title|label=action|...; an action is a slash command (run as if typed), "@pet:order" (the pet
## window's button) or "@whisper:Name" (the chat line, ready to type). The controller works it like any window: the
## d-pad moves between the entries, A picks, B closes. A click outside closes it too.

var _box: Control
var _first: Button


func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false


func open(title: String, entries: Array) -> void:
	for c in get_children():
		c.queue_free()
	_first = null
	var w := 196.0
	var row := 19.0
	var h := 34.0 + row * entries.size() + 8.0
	_box = Control.new()
	_box.size = Vector2(w, h)
	var area: Vector2 = (get_parent() as Control).size if get_parent() is Control and (get_parent() as Control).size != Vector2.ZERO \
			else get_viewport_rect().size
	_box.position = (Vector2(area.x * 0.5 - w * 0.5, area.y * 0.55 - h * 0.5)).floor()
	_box.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_box)
	var bg := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.03, 0.025, 0.02, 0.9)
	sb.border_color = Color(0.62, 0.5, 0.26, 0.95)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(2)
	bg.add_theme_stylebox_override("panel", sb)
	bg.size = _box.size
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box.add_child(bg)
	var t := UiArt.label(title.to_upper(), 10, UiArt.GOLD_HI)
	t.position = Vector2(6, 8)
	t.size = Vector2(w - 12, 14)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	t.clip_text = true
	_box.add_child(t)
	var y := 30.0
	for e in entries:
		var b := UiArt.button(String(e[0]).to_upper(), Vector2(w - 24, 16), 9)
		b.position = Vector2(12, y)
		b.pressed.connect(_pick.bind(e[1]))
		_box.add_child(b)
		if _first == null:
			_first = b
		y += row
	visible = true
	# the controller's pointer onto the first entry (the d-pad goes from there)
	if _first and Pad.active:
		await get_tree().process_frame
		if is_instance_valid(_first) and Pad.has_method("_point_at"):
			Pad.call("_point_at", _first)


func close() -> void:
	visible = false
	for c in get_children():
		c.queue_free()


func _pick(action: Variant) -> void:
	close()
	if action is Callable:                                # the client's own menus (an item in your bags)
		(action as Callable).call()
		return
	run_action(String(action), get_tree())


## An entry's action, as the menu (or anything else) would run it.
static func run_action(action: String, tree: SceneTree) -> void:
	if action.begins_with("@pet:"):
		PlayerData.pet_command(action.trim_prefix("@pet:"))
		return
	var ui = _game_ui(tree)
	if action.begins_with("@whisper:"):
		if ui and ui.get("chat"):
			ui.chat.start_typing("/send %s " % action.trim_prefix("@whisper:"))
		return
	if ui and ui.get("chat"):
		ui.chat.run_line(action)                          # client commands (/follow) and the server's alike
	else:
		Server.command(action)


static func _game_ui(tree: SceneTree):
	var v := tree.current_scene
	return v.get("ui") if v else null


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and _box \
			and not Rect2(_box.position, _box.size).has_point(event.position):
		close()
		accept_event()


func _input(event: InputEvent) -> void:
	if visible and event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()
