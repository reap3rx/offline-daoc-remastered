extends ClassicWindow
## The zone mark window (owner 2026-11-21: "a window that lets me choose from mob types and difficulty from some presets
## based on the zone design, and then a window to jot some notes down for that spawn, then putting a marker down in
## game"). /zmark asks the server (ZoneMarks.cs) for "#ZMARK|{zone, zoneName, count, kinds, themes, difficulties, sizes,
## times, near:[{id, kind, theme, difficulty, size, time, route, note, dist}]}". PLACE MARK HERE sends the notes a piece at
## a time (/zmark note ...) and then the choices (/zmark add kind theme difficulty size time route); the server saves the
## mark where you stand (runtime\server\zone-marks), puts a glowing orb there and answers with the window again.

const BODY := Vector2(560, 360)
const LEFT_W := 270.0

var _title: Label
var _opts := {}             # "kinds" -> OptionButton
var _route: LineEdit
var _notes: TextEdit
var _near: Label
var _lists := {}            # "kinds" -> Array of names


func build() -> void:
	closable = true
	_title = UiArt.label("ZONE MARK", 10, UiArt.GOLD_HI)
	_title.position = Vector2(8, 4)
	_title.size = Vector2(BODY.x - 16, 14)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_title)
	var rows := [["kinds", "WHAT"], ["themes", "WHO"], ["difficulties", "DIFFICULTY"], ["sizes", "HOW MANY"], ["times", "WHEN"]]
	for i in rows.size():
		var y := 28.0 + i * 26.0
		var l := UiArt.label(rows[i][1], 8, UiArt.GOLD)
		l.position = Vector2(10, y + 5)
		l.size = Vector2(70, 12)
		add_child(l)
		var o := _choice()
		o.position = Vector2(84, y)
		add_child(o)
		_opts[rows[i][0]] = o
	var ry := 28.0 + rows.size() * 26.0
	var rl := UiArt.label("ROUTE", 8, UiArt.GOLD)
	rl.position = Vector2(10, ry + 5)
	rl.size = Vector2(70, 12)
	add_child(rl)
	_route = LineEdit.new()
	_route.position = Vector2(84, ry)
	_route.size = Vector2(176, 20)
	_route.placeholder_text = "patrol name (patrol points)"
	_style_edit(_route)
	add_child(_route)
	var nl := UiArt.label("NOTES", 8, UiArt.GOLD)
	nl.position = Vector2(10, ry + 30)
	nl.size = Vector2(70, 12)
	add_child(nl)
	_notes = TextEdit.new()
	_notes.position = Vector2(10, ry + 46)
	_notes.size = Vector2(BODY.x - 20, 82)
	_notes.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	_notes.placeholder_text = "What should be here, how it should feel, anything else..."
	_style_edit(_notes)
	add_child(_notes)
	var by := BODY.y - 30.0
	var place := UiArt.button("PLACE MARK HERE", Vector2(130, 20), 9)
	place.position = Vector2(10, by)
	place.pressed.connect(_place)
	add_child(place)
	var del := UiArt.button("REMOVE NEAREST", Vector2(120, 20), 9)
	del.position = Vector2(150, by)
	del.pressed.connect(func(): Server.command("/zmark del"))
	add_child(del)
	var refresh := UiArt.button("REFRESH", Vector2(80, 20), 9)
	refresh.position = Vector2(280, by)
	refresh.pressed.connect(func(): Server.command("/zmark"))
	add_child(refresh)
	var nh := UiArt.label("MARKS NEARBY", 8, UiArt.GOLD)
	nh.position = Vector2(LEFT_W + 10, 28)
	nh.size = Vector2(BODY.x - LEFT_W - 20, 12)
	add_child(nh)
	var scroll := ScrollContainer.new()
	scroll.position = Vector2(LEFT_W + 10, 44)
	scroll.size = Vector2(BODY.x - LEFT_W - 20, ry - 20)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	_near = UiArt.label("", 8, UiArt.CREAM, false)
	_near.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_near.custom_minimum_size = Vector2(BODY.x - LEFT_W - 34, 10)
	scroll.add_child(_near)
	set_window_size(BODY)


func _choice() -> OptionButton:
	var o := OptionButton.new()
	o.size = Vector2(176, 20)
	o.custom_minimum_size = Vector2(176, 20)
	o.focus_mode = Control.FOCUS_NONE
	o.clip_text = true
	o.fit_to_longest_item = false
	o.add_theme_font_override("font", UiArt.font(true))
	o.add_theme_font_size_override("font_size", 9)
	o.add_theme_color_override("font_color", UiArt.CREAM)
	o.add_theme_color_override("font_hover_color", UiArt.GOLD_HI)
	o.add_theme_stylebox_override("normal", UiArt.bar_style(0))
	o.add_theme_stylebox_override("hover", UiArt.bar_style(1))
	o.add_theme_stylebox_override("pressed", UiArt.bar_style(2))
	o.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	UiArt.themed(o)
	var pop := o.get_popup()
	pop.add_theme_font_override("font", UiArt.font(true))
	pop.add_theme_font_size_override("font_size", 14)
	pop.add_theme_color_override("font_color", UiArt.CREAM)
	pop.add_theme_color_override("font_hover_color", UiArt.GOLD_HI)
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color(0.07, 0.065, 0.06, 0.97)
	panel.border_color = UiArt.GOLD.darkened(0.3)
	panel.set_border_width_all(1)
	pop.add_theme_stylebox_override("panel", panel)
	return o


func _style_edit(c: Control) -> void:
	c.add_theme_font_override("font", UiArt.font(false))
	c.add_theme_font_size_override("font_size", 10)
	c.add_theme_color_override("font_color", UiArt.CREAM)
	c.add_theme_stylebox_override("normal", _box(false))
	c.add_theme_stylebox_override("focus", _box(true))


func _place() -> void:
	var text := _notes.text.strip_edges().replace("\r", "").replace("\n", " / ")
	while text.length() > 0:                    # a chat command is short: the notes go first, in pieces
		var piece := text.substr(0, 150)
		text = text.substr(150)
		Server.command("/zmark note " + piece)
	var route := _route.text.strip_edges().replace(" ", "_")
	if route == "":
		route = "-"
	Server.command("/zmark add %d %d %d %d %d %s" % [_sel("kinds"), _sel("themes"), _sel("difficulties"), _sel("sizes"),
		_sel("times"), route])
	_notes.text = ""
	_notes.release_focus()
	_route.release_focus()


func _sel(key: String) -> int:
	var o: OptionButton = _opts.get(key)
	return maxi(0, o.selected) if o else 0


## The server's lists and the marks nearby: shown, and the window opened.
func receive(json: String) -> void:
	var d = JSON.parse_string(json)
	if not (d is Dictionary):
		return
	_title.text = "ZONE MARK  -  %s  (%d MARKS)" % [String(d.get("zoneName", "")).to_upper(), int(d.get("count", 0))]
	for key in _opts:
		var items: Array = d.get(key, [])
		if items != _lists.get(key, []):
			var o: OptionButton = _opts[key]
			var keep := o.selected
			o.clear()
			for it in items:
				o.add_item(String(it).to_upper())
			o.select(clampi(keep, 0, items.size() - 1))
			_lists[key] = items
	var lines := PackedStringArray()
	for m in d.get("near", []):
		var line := "#%d  %dM AWAY  -  %s, %s, %s, %s, %s" % [int(m.get("id", 0)), int(m.get("dist", 0)) / 40,
			String(m.get("kind", "")), String(m.get("theme", "")), String(m.get("difficulty", "")),
			String(m.get("size", "")), String(m.get("time", ""))]
		if m.get("route") != null and String(m.get("route")) != "":
			line += ", ROUTE " + String(m.get("route"))
		if String(m.get("note", "")) != "":
			line += "\n    " + String(m.get("note", ""))
		lines.append(line)
	_near.text = "\n".join(lines) if lines.size() > 0 else "No marks in this zone yet."
	if not visible:
		show_window()


static func _box(hi: bool) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(0.05, 0.045, 0.04, 0.95)
	s.border_color = UiArt.GOLD if hi else UiArt.GOLD.darkened(0.45)
	s.set_border_width_all(1)
	s.set_content_margin_all(3)
	return s
