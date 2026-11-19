extends ClassicWindow
## Your companion's character sheet (owner 2026-11-19: "Also need a way to be able to see their stats, spec, and spells
## available to them"). "/companion sheet" (its interact menu: Character Sheet) asks the server
## (PersonalCompanions.Sheet) for "#CSHEET|{json}": name, class, role, competence, health / power / endurance, the
## stats as they are now, armour factor, weapon skill and resists, each specialization's level, and the abilities,
## styles and spells it can use now. Three columns: who it is, its training, what it can do. REFRESH asks again.

const BODY := Vector2(620, 400)

var _title: Label
var _left: VBoxContainer
var _mid: VBoxContainer
var _right: VBoxContainer


func build() -> void:
	closable = true
	_title = UiArt.label("COMPANION", 10, UiArt.GOLD_HI)
	_title.position = Vector2(8, 4)
	_title.size = Vector2(BODY.x - 16, 14)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_title)
	var w := (BODY.x - 32) / 3.0
	_left = _column(Vector2(8, 24), w)
	_mid = _column(Vector2(16 + w, 24), w)
	_right = _column(Vector2(24 + w * 2, 24), w)
	var again := UiArt.button("REFRESH", Vector2(64, 16), 8)
	again.position = Vector2(BODY.x - 72, BODY.y - 22)
	again.pressed.connect(func(): Server.command("/companion sheet"))
	add_child(again)
	set_window_size(BODY)


func _column(at: Vector2, w: float) -> VBoxContainer:
	var scroll := ScrollContainer.new()
	scroll.position = at
	scroll.size = Vector2(w, BODY.y - 50)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	var box := VBoxContainer.new()
	box.custom_minimum_size = Vector2(w - 12, 0)
	box.add_theme_constant_override("separation", 1)
	scroll.add_child(box)
	return box


func receive(json: String) -> void:
	var d = JSON.parse_string(json)
	if not (d is Dictionary):
		return
	for box in [_left, _mid, _right]:
		for c in box.get_children():
			c.queue_free()
	_title.text = ("%s - LEVEL %d %s %s" % [String(d.get("name", "")), int(d.get("level", 0)), String(d.get("race", "")),
			String(d.get("cls", ""))]).to_upper()
	# who it is: role, competence, its pools, stats, armour and resists
	_head(_left, "ROLE")
	_line(_left, String(d.get("role", "")))
	_line(_left, String(d.get("competence", "")), UiArt.GOLD)
	if not bool(d.get("alive", true)):
		_line(_left, "FALLEN - HELP THEM UP", UiArt.RED)
	_head(_left, "POOLS")
	for pair in [["HEALTH", "hp"], ["POWER", "power"], ["ENDURANCE", "endurance"]]:
		var v: Array = d.get(pair[1], [0, 0])
		if int(v[1]) > 0:
			_pair(_left, pair[0], "%d / %d" % [int(v[0]), int(v[1])])
	_head(_left, "ATTRIBUTES")
	for s in d.get("stats", []):
		_pair(_left, String(s.k), str(int(s.v)))
	_pair(_left, "ARMOR FACTOR", str(int(d.get("af", 0))))
	if String(d.get("weapon", "")) != "":
		_pair(_left, "WEAPON SKILL", str(int(d.get("ws", 0))))
		_line(_left, String(d.get("weapon", "")), UiArt.DIM)
	var gear: Array = d.get("gear", [])
	if not gear.is_empty():
		_head(_left, "WEARING")
		for g in gear:
			_line(_left, "%s: %s" % [String(g.slot), String(g.name)], UiArt.CREAM)
	_head(_left, "RESISTS")
	for s in d.get("resists", []):
		_pair(_left, String(s.k), "%d%%" % int(s.v))
	# its training: specializations, abilities
	_head(_mid, "SPECIALIZATIONS")
	for s in d.get("specs", []):
		_pair(_mid, String(s.name).to_upper(), str(int(s.level)))
	var abil: Array = d.get("abilities", [])
	if not abil.is_empty():
		_head(_mid, "ABILITIES")
		for a in abil:
			_line(_mid, String(a))
	# what it can do: styles, spells by line
	var styles: Array = d.get("styles", [])
	if not styles.is_empty():
		_head(_right, "STYLES")
		for s in styles:
			var open := String(s.get("opening", ""))
			_line(_right, "%s  (%s %d%s)" % [String(s.name), String(s.spec), int(s.level),
					"" if open == "" or open == "Offensive" else ", " + open.to_lower()])
	var line := ""
	for sp in d.get("spells", []):
		if String(sp.line) != line:
			line = String(sp.line)
			_head(_right, line.to_upper())
		_line(_right, "%s  (%d)" % [String(sp.name), int(sp.level)])
	if not visible:
		show_window()


func _head(box: VBoxContainer, text: String) -> void:
	var l := UiArt.label(text, 8, UiArt.GOLD_HI)
	l.custom_minimum_size = Vector2(0, 16)
	l.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	box.add_child(l)


func _line(box: VBoxContainer, text: String, color := UiArt.CREAM) -> void:
	var l := UiArt.label(text, 7, color, false)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(box.custom_minimum_size.x, 0)
	box.add_child(l)


func _pair(box: VBoxContainer, k: String, v: String) -> void:
	var row := HBoxContainer.new()
	var a := UiArt.label(k, 7, UiArt.DIM, false)
	a.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(a)
	row.add_child(UiArt.label(v, 7, UiArt.CREAM, false))
	box.add_child(row)
