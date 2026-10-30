extends ClassicWindow
## Action Combat Styles (owner 2026-10-30): which style each action-combat move fires - the held attack (an anytime
## style), the reaction after you parry, block or dodge, and the front / side / back positionals. Each slot's button
## shows its pick; click it for the styles you know for that slot (hover one: its delve) or BEST AVAILABLE (the old
## automatic choice, the default). Chains need no pick: the chain button fires whichever follows. The server keeps
## the picks on the character (ActionCombat.SetPick) and only follows a pick the weapon in hand can do.
## Opened from the COMBAT sheet's ACTION COMBAT STYLES button.

const BODY := Vector2(236, 214)
const SLOTS := [
	["anytime", "POWER ATTACK"],
	["parry", "AFTER A PARRY"],
	["block", "AFTER A BLOCK"],
	["dodge", "AFTER A DODGE"],
	["front", "FRONT POSITIONAL"],
	["side", "SIDE POSITIONAL"],
	["back", "BACK POSITIONAL"],
]

var _rows: Control
var _chooser: Control
var _buttons := {}
var _choosing := ""


func build() -> void:
	closable = true
	var title := UiArt.label("ACTION COMBAT STYLES", 10, UiArt.GOLD_HI)
	title.position = Vector2(8, 4)
	title.size = Vector2(BODY.x - 16, 14)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(title)
	_rows = Control.new()
	_rows.position = Vector2(0, 24)
	_rows.size = Vector2(BODY.x, BODY.y - 30)
	add_child(_rows)
	for i in SLOTS.size():
		var y := float(i) * 24.0
		var l := UiArt.label(String(SLOTS[i][1]), 7, UiArt.CREAM)
		l.position = Vector2(10, y + 3)
		l.size = Vector2(84, 12)
		_rows.add_child(l)
		var b := UiArt.button("...", Vector2(128, 16), 8)
		b.position = Vector2(98, y)
		var slot := String(SLOTS[i][0])
		b.pressed.connect(func(): _choose(slot))
		_rows.add_child(b)
		_buttons[slot] = b
	var hint := UiArt.label("CHAINS FOLLOW ON THEIR OWN", 7, UiArt.DIM)
	hint.position = Vector2(8, BODY.y - 20)
	hint.size = Vector2(BODY.x - 16, 10)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(hint)
	set_window_size(BODY)
	visibility_changed.connect(func():
		if visible:
			_choosing = ""
			Server.command("/ac styles"))
	if visible:                                            # (left open last time: its lists now)
		Server.command.call_deferred("/ac styles")
	refresh()


## The style's place among the server's skills (its icon and delve text), or -1.
static func _skill_index(style_name: String) -> int:
	var first := PanelSheets._first_skill()
	for i in Server.skills.size():
		var sk: Dictionary = Server.skills[i]
		if int(sk.page) == 2 and String(sk.name) == style_name:
			return i - first
	return -1


func _name_of(slot: String, id: int) -> String:
	for o in (Server.ac_styles.get(slot, {}).get("options", []) as Array):
		if int(o.id) == id:
			return String(o.name)
	return ""


func refresh() -> void:
	if _rows == null:
		return
	for s in SLOTS:
		var slot := String(s[0])
		var b: Button = _buttons[slot]
		var info: Dictionary = Server.ac_styles.get(slot, {})
		var opts: Array = info.get("options", [])
		var picked := _name_of(slot, int(info.get("picked", 0)))
		b.disabled = opts.is_empty()
		b.text = "NO STYLE AVAILABLE" if opts.is_empty() else (picked.to_upper() if picked != "" else "BEST AVAILABLE")
		b.tooltip_text = "" if picked == "" else picked.to_upper()
	if _choosing != "":
		_choose(_choosing)


## The list of styles for one slot, over the rows; a click picks one.
func _choose(slot: String) -> void:
	_choosing = slot
	if _chooser:
		_chooser.queue_free()
	_rows.visible = false
	_chooser = Control.new()
	_chooser.position = Vector2(0, 22)
	_chooser.size = Vector2(BODY.x, BODY.y - 46)
	add_child(_chooser)
	var info: Dictionary = Server.ac_styles.get(slot, {})
	var head := UiArt.label(_title_of(slot), 8, UiArt.GOLD_HI)
	head.position = Vector2(10, 0)
	head.size = Vector2(150, 12)
	_chooser.add_child(head)
	var back := UiArt.button("BACK", Vector2(50, 14), 8)
	back.position = Vector2(BODY.x - 62, -1)
	back.pressed.connect(_close_chooser)
	_chooser.add_child(back)
	var scroll := ScrollContainer.new()
	scroll.position = Vector2(10, 16)
	scroll.size = Vector2(BODY.x - 20, _chooser.size.y - 18)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_chooser.add_child(scroll)
	var list := VBoxContainer.new()
	list.custom_minimum_size = Vector2(BODY.x - 28, 0)
	list.add_theme_constant_override("separation", 1)
	scroll.add_child(list)
	var picked := int(info.get("picked", 0))
	list.add_child(_option_row(slot, 0, "BEST AVAILABLE (AUTOMATIC)", picked == 0))
	for o in (info.get("options", []) as Array):
		list.add_child(_option_row(slot, int(o.id), String(o.name), picked == int(o.id)))


func _title_of(slot: String) -> String:
	for s in SLOTS:
		if String(s[0]) == slot:
			return String(s[1])
	return slot.to_upper()


func _option_row(slot: String, id: int, style_name: String, chosen: bool) -> Control:
	var row: Control
	var idx := _skill_index(style_name) if id > 0 else -1
	if idx >= 0:
		var sk: Dictionary = Server.skills[idx + PanelSheets._first_skill()]
		row = PanelSheets._server_row("style", "srv:skill:%d" % idx, style_name, "style", int(sk.icon), "")
	else:
		row = PanelSheets._text_row(style_name, "")
		row.mouse_filter = Control.MOUSE_FILTER_STOP
	if chosen:
		var mark := ColorRect.new()
		mark.color = Color(1.0, 0.8, 0.3, 0.18)
		mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
		mark.set_anchors_preset(Control.PRESET_FULL_RECT)
		row.add_child(mark)
		row.move_child(mark, 0)
	row.gui_input.connect(func(e: InputEvent):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			Server.command("/ac pick %s %s" % [slot, str(id) if id > 0 else "auto"])
			_close_chooser())
	return row


func _close_chooser() -> void:
	_choosing = ""
	if _chooser:
		_chooser.queue_free()
		_chooser = null
	_rows.visible = true
