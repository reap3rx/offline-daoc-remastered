extends Control
## Putting skills on the controller (owner 2026-11-10: "highlight the skill in the spell book and hit an 'assign' button,
## and then you press the button combo ... an 'assign skills' button in the skills/spellbook window where you click it,
## press the button combo, then it brings up a window that has assignable skills ... A to assign, or B to cancel").
## Both ways: a spellbook line's ASSIGN (Y) - press the buttons and it goes there; or the Hero panel's ASSIGN TO
## CONTROLLER - press the buttons, then pick the skill from the list. A slot is a button bound to a quickbar slot (the
## bumper combos by default); a button bound to anything else (jump, interact, the style button, moving, the windows)
## is refused - "it'll be important to not let the player place skills ... onto core buttons". A combo nothing uses yet
## takes the first free quickbar slot.

var ui: Node
var skill := {}                          # the skill to place (empty: pick it after the buttons)
var _panel: PanelContainer
var _msg: Label
var _list: VBoxContainer
var _scroll: ScrollContainer
var _target := ""                        # the input chosen
var _slot := Vector2i(-1, -1)            # its quickbar (bar, slot)


static func start(game_ui: Node, what := {}) -> void:
	if game_ui == null:
		return
	var me: Script = load("res://game/input/pad_assign.gd")
	for c in game_ui.root.get_children():
		if c.get_script() == me:
			c.queue_free()
	var a = me.new()
	a.ui = game_ui
	a.skill = what
	game_ui.root.add_child(a)


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.045, 0.04, 0.95)
	sb.border_color = UiArt.GOLD
	sb.set_border_width_all(1)
	sb.set_content_margin_all(10)
	_panel.add_theme_stylebox_override("panel", sb)
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	_panel.add_child(box)
	var title := "PUT %s ON THE CONTROLLER" % String(skill.get("name", "A SKILL")).to_upper()
	box.add_child(UiArt.label(title, 11, UiArt.GOLD_HI))
	_msg = UiArt.label("", 9, UiArt.CREAM)
	_msg.autowrap_mode = TextServer.AUTOWRAP_WORD
	_msg.custom_minimum_size = Vector2(300, 0)
	box.add_child(_msg)
	_scroll = ScrollContainer.new()
	_scroll.custom_minimum_size = Vector2(300, 260)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.visible = false
	box.add_child(_scroll)
	_list = VBoxContainer.new()
	_list.custom_minimum_size = Vector2(286, 0)
	_list.add_theme_constant_override("separation", 2)
	_scroll.add_child(_list)
	var cancel := UiArt.button("CANCEL", Vector2(300, 18), 9)
	cancel.pressed.connect(_close)
	box.add_child(cancel)
	_ask()
	_place.call_deferred()


func _place() -> void:
	await get_tree().process_frame                         # (its new size laid out first)
	_panel.reset_size()
	var a: Vector2 = ui.area() if ui and ui.has_method("area") else get_viewport_rect().size
	_panel.position = ((a - _panel.size) * 0.5).round()


func _ask(why := "") -> void:
	_msg.text = (why + "\n" if why != "" else "") + \
			"PRESS THE CONTROLLER BUTTONS FOR THE SLOT - HOLD LB / RB (OR BOTH) AND PRESS A BUTTON. MENU CANCELS."
	Pad.capture(_got)


func _got(input: String) -> void:
	if not is_inside_tree():
		return
	if input == "menu":
		_close()
		return
	var why := Pad.slot_refusal(input)
	if why != "":
		_ask(why)
		return
	_target = input
	_slot = Pad.slot_for_input(input, true)
	if _slot.x < 0:
		_ask("NO FREE QUICKBAR SLOT LEFT FOR %s." % Pad.describe(input))
		return
	if not skill.is_empty():
		_assign(skill)
		return
	_msg.text = "%s: PICK THE SKILL (D-PAD, A). B CANCELS." % Pad.describe(input)
	_fill()


func _fill() -> void:
	_scroll.visible = true
	for c in _list.get_children():
		c.queue_free()
	var all := known_skills()
	var first: Button = null
	var group := ""
	for d in all:
		if String(d.get("group", "")) != group:                 # each group under its heading
			group = String(d.get("group", ""))
			var hl := UiArt.label(group, 9, UiArt.GOLD_HI)
			hl.custom_minimum_size = Vector2(280, 18)
			hl.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
			_list.add_child(hl)
		var b := Button.new()
		b.text = String(d.name).to_upper()
		b.icon = ItemDb.icon(int(d.get("icon", 0)))
		b.expand_icon = false
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(280, 24)
		b.focus_mode = Control.FOCUS_NONE
		b.add_theme_font_override("font", UiArt.font(true))
		b.add_theme_font_size_override("font_size", 9)
		b.add_theme_color_override("font_color", UiArt.CREAM)
		b.add_theme_color_override("font_hover_color", UiArt.GOLD_HI)
		b.add_theme_constant_override("icon_max_width", 20)
		b.add_theme_stylebox_override("normal", UiArt.bar_style(0))
		b.add_theme_stylebox_override("hover", UiArt.bar_style(1))
		b.add_theme_stylebox_override("pressed", UiArt.bar_style(1))
		b.pressed.connect(_assign.bind(d))
		_list.add_child(b)
		if first == null:
			first = b
	_place.call_deferred()
	if first:
		_point_first.call_deferred(first)


func _point_first(b: Control) -> void:
	await get_tree().process_frame
	if is_instance_valid(b) and Pad.active:
		Pad.call("_point_at", b)


## Every skill you can use, in groups (owner 2026-11-13: "the list of abilities should be organized by category. So thrust
## styles together, Earth magic spells together, etc."; "Stealth was not appearing on my infiltrator"; "things like
## 'abilities: dual wield' which is just text" left out): [{kind, id, icon, border, name, group}], group by group -
## the smart heals, each spell line (a hybrid's by its specialization), each weapon's styles, then the abilities.
static func known_skills() -> Array:
	var out := []
	if not Server.active:
		return out
	for e in Server.smart_heal_entries():
		var d: Dictionary = e.duplicate()
		d["group"] = "AUTOMATIC HEALS"
		out.append(d)
	var spells := []                                         # [group, entry] in the server's order
	var styles := []
	var abilities := []
	# a list caster's lines (the baseline and the specialization line of a name together)
	for li in Server.spell_lines.size():
		var line: Dictionary = Server.spell_lines[li]
		for sp in (line.spells as Array):
			var kind := "style" if String(sp.get("kind", "spell")) == "style" else "spell"
			var ic2: Array = Server.skill_icon(kind, int(sp.icon))
			var g := String(line.name).to_upper()
			if kind == "style":
				g += " STYLES"
			(styles if kind == "style" else spells).append([g, {"kind": kind, "id": "srv:spell:%d:%d" % [li, int(sp.level)],
					"icon": int(ic2[0]), "border": int(ic2[1]), "name": String(sp.name), "lv": int(sp.level)}])
	# the skill list: hybrid spells and songs under their specialization, styles under their weapon, abilities
	var first := PanelSheets._first_skill()
	var style_spec := _style_specs()
	for i in Server.skills.size():
		var sk: Dictionary = Server.skills[i]
		var pg := int(sk.page)
		if pg == 0:
			if String(sk.name) in PanelSheets.SPEC_ACTIONS and int(sk.level) > 0:   # Stealth: the spec itself is used
				var ics: Array = Server.skill_icon("icon", int(sk.icon))
				abilities.append(["ABILITIES", {"kind": "ability", "id": "srv:spec:%d" % i, "icon": int(ics[0]),
						"border": int(ics[1]), "name": String(sk.name), "lv": 0}])
			continue
		var kind: String = "ability" if pg in [1, 5, 6] else ("style" if pg == 2 else "spell")
		var ic: Array = Server.skill_icon("icon" if kind == "ability" else kind, int(sk.icon))
		var d := {"kind": kind, "id": "srv:skill:%d" % (i - first), "icon": int(ic[0]), "border": int(ic[1]),
				"name": String(sk.name), "lv": int(sk.level)}
		if kind == "ability":
			if int(ic[0]) < 0:
				continue                                         # (a passive line of text: Weaponry, Dual Wield ...)
			abilities.append(["REALM ABILITIES" if pg == 6 else "ABILITIES", d])
		elif kind == "style":
			styles.append([String(style_spec.get(String(sk.name), "OTHER")).to_upper() + " STYLES", d])
		else:
			var sp_i := int(sk.get("special", 0xFE))
			var head := "SONGS" if pg == 4 or sp_i == 0xFF else "SPELLS"
			if sp_i >= 0 and sp_i < Server.skills.size() and int(Server.skills[sp_i].page) == 0:
				head = String(Server.skills[sp_i].name).to_upper()
			spells.append([head, d])
	# spells by line in the server's order (lowest level first in each); styles by weapon; abilities by name
	for gi in 2:
		var grp: Array = spells if gi == 0 else styles
		var by_name := gi == 1
		var order := {}
		for e in grp:
			if not order.has(e[0]):
				order[e[0]] = order.size()
		grp.sort_custom(func(a, b):
			if a[0] != b[0]:
				return String(a[0]) < String(b[0]) if by_name else int(order[a[0]]) < int(order[b[0]])
			return int(a[1].lv) < int(b[1].lv) or (int(a[1].lv) == int(b[1].lv) and String(a[1].name) < String(b[1].name)))
	abilities.sort_custom(func(a, b):
		if a[0] != b[0]:
			return String(a[0]) == "ABILITIES"
		return String(a[1].name) < String(b[1].name))
	for e in spells + styles + abilities:
		var d: Dictionary = e[1]
		d["group"] = e[0]
		out.append(d)
	return out


## A style's name -> its specialization's name, for your class (ClassDb's styles).
static func _style_specs() -> Dictionary:
	var out := {}
	ClassDb.style(0)                                         # (loads the class data)
	var cid := PlayerData.class_id()
	for k in ClassDb._styles:
		var s: Dictionary = ClassDb._styles[k]
		var c := int(s.get("classid", 0))
		if c != 0 and c != cid:
			continue
		var key := String(s.get("speckeyname", ""))
		var nm := String(s.get("name", ""))
		if not out.has(nm) or c == cid:
			out[nm] = String(ClassDb.spec(key).get("name", key))
	return out


func _assign(d: Dictionary) -> void:
	var bank: int = PlayerData.quickbar_bank[_slot.x]
	PlayerData.quickbars[_slot.x][bank][_slot.y] = {"kind": String(d.kind), "id": String(d.id), "icon": int(d.icon),
			"name": String(d.name), "border": int(d.get("border", -1))}
	PlayerData.save_character()
	PlayerData.changed.emit()
	PlayerData.message.emit("%s is on %s." % [String(d.name), Pad.describe(_target)], "system")
	_close()


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		get_viewport().set_input_as_handled()              # (Esc / the pad's B: this box only, not every window)
		_close()


func _close() -> void:
	Pad.cancel_capture()
	queue_free()
