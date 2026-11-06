extends ClassicWindow
## The story quests' dialogue and quest window (owner 2026-11-06: "a much more readable dialogue UI ... tied into
## making a quest window (kind of like WoW) where you can see the quest lore and possible rewards"). The server sends
## "#DLG|{json}" (StoryDialog.cs) when a story NPC speaks to you: who, their words, and what kind of moment it is -
##   talk / idle   their words; each [keyword] in them is also a button below
##   offer         the quest window: title, level, GROUP, the giver's words as its lore, what it asks, and its rewards
##                 (experience, money, Marks of Valor, the items you'll be given and the ones you may choose from - by
##                 how it ends - each with its bonuses and lore on hover); ACCEPT and DECLINE
##   topic         the answer to one of the offer's [questions], added under the offer (the window stays the quest's)
##   choice        a decision: its options as large buttons
##   reward        the ending's words and the items to choose from, as cards to click
##   end           the ending's words, with QUEST COMPLETE (or A SAD END)
## An answer is the same whisper the [keyword] always was (Server.command("/whisper ...")).

const BODY := Vector2(470, 410)
const PAD := 12.0
const BUTTONS_H := 50.0

var oid := 0
var _msg := {}
var _name: Label
var _sub: Label
var _scroll: ScrollContainer
var _col: VBoxContainer
var _buttons: HFlowContainer
var _asks: Array = []                       # an offer's options, kept while its topics are answered
var _insert_at := 0                          # where an offer's answered [questions] go: under its words
const MIN_H := 170.0


func build() -> void:
	closable = true
	_name = UiArt.label("", 11, UiArt.GOLD_HI)
	_name.position = Vector2(PAD, 4)
	_name.size = Vector2(BODY.x - 2 * PAD - 16, 14)
	_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_name)
	_sub = UiArt.label("", 7, UiArt.DIM)
	_sub.position = Vector2(PAD, 21)
	_sub.size = Vector2(BODY.x - 2 * PAD, 10)
	_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_sub)
	_scroll = ScrollContainer.new()
	_scroll.position = Vector2(PAD, 36)
	_scroll.size = Vector2(BODY.x - 2 * PAD, BODY.y - 36 - BUTTONS_H - 8)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	UiArt.themed(_scroll)
	add_child(_scroll)
	_col = VBoxContainer.new()
	_col.custom_minimum_size = Vector2(BODY.x - 2 * PAD - 14, 0)
	_col.add_theme_constant_override("separation", 6)
	_scroll.add_child(_col)
	_buttons = HFlowContainer.new()
	_buttons.position = Vector2(PAD, BODY.y - BUTTONS_H - 6)
	_buttons.size = Vector2(BODY.x - 2 * PAD, BUTTONS_H)
	_buttons.alignment = FlowContainer.ALIGNMENT_CENTER
	_buttons.add_theme_constant_override("h_separation", 6)
	_buttons.add_theme_constant_override("v_separation", 4)
	add_child(_buttons)
	set_window_size(BODY)


func receive(json: String) -> void:
	var d = JSON.parse_string(json)
	if not (d is Dictionary):
		return
	var kind := String(d.get("kind", "talk"))
	var q: Dictionary = d.get("quest", {}) if d.get("quest") is Dictionary else {}
	if kind == "topic" and visible and String(_msg.get("kind", "")) == "offer" and int(d.get("oid", 0)) == oid:
		var dv := _divider()
		_col.add_child(dv)
		_col.move_child(dv, _insert_at)
		var ans := _text(String(d.get("text", "")), 11, Color(0.86, 0.83, 0.74))
		_col.add_child(ans)
		_col.move_child(ans, _insert_at + 1)
		_insert_at += 2
		for o in d.get("options", []):
			if not _asks.any(func(a): return String(a.kw).to_lower() == String(o.kw).to_lower()):
				_asks.append(o)
		_fill_buttons(_asks, "offer")
		return
	_msg = d
	oid = int(d.get("oid", 0))
	for c in _col.get_children():
		c.queue_free()
	_name.text = String(d.get("name", "")).to_upper()
	_sub.text = ""
	if not q.is_empty():
		_sub.text = ("%s  -  LEVEL %d%s" % [String(q.get("title", "")), int(q.get("level", 0)),
				"  -  GROUP" if bool(q.get("group", false)) else ""]).to_upper()
	match kind:
		"offer":
			_col.add_child(_heading("QUEST OFFERED", UiArt.GOLD))
		"end":
			var sad := bool(d.get("tragic", false))
			_col.add_child(_heading("A SAD END" if sad else "QUEST COMPLETE", UiArt.RED if sad else UiArt.GREEN))
		"reward":
			_col.add_child(_heading("QUEST COMPLETE", UiArt.GREEN))
		"choice":
			_col.add_child(_heading("A DECISION", UiArt.GOLD))
	_col.add_child(_text(String(d.get("text", ""))))
	_insert_at = _col.get_child_count()
	if kind == "offer" and not q.is_empty():
		if String(q.get("summary", "")) != "":
			_col.add_child(_heading("THE TASK", UiArt.GOLD))
			_col.add_child(_text(String(q.summary), 11, UiArt.CREAM))
		_rewards(d.get("rewards", {}) if d.get("rewards") is Dictionary else {}, false)
	elif kind == "reward":
		_rewards(d.get("rewards", {}) if d.get("rewards") is Dictionary else {}, true)
	elif not q.is_empty() and String(q.get("goal", "")) != "" and kind in ["talk", "idle"]:
		_col.add_child(_text("Now: " + String(q.goal), 9, UiArt.DIM))
	_asks = (d.get("options", []) as Array).duplicate()
	_fill_buttons(_asks, kind)
	_scroll.scroll_vertical = 0
	show_window()
	_fit.call_deferred()


## The window as tall as what it holds (a line of talk is a small box, a quest offer the full window).
func _fit() -> void:
	await get_tree().process_frame
	var content := _col.get_combined_minimum_size().y
	var h := clampf(36.0 + content + 8.0 + BUTTONS_H + 6.0, MIN_H, BODY.y)
	min_size = Vector2(BODY.x, MIN_H)
	set_window_size(Vector2(BODY.x, h))
	_scroll.size = Vector2(BODY.x - 2 * PAD, h - 36 - BUTTONS_H - 8)
	_buttons.position = Vector2(PAD, h - BUTTONS_H - 6)
	position.y = clampf(position.y, 0.0, maxf(0.0, get_parent_area_size().y - h))


# ---------------------------------------------------------------- parts

func _heading(t: String, col: Color) -> Label:
	var l := UiArt.label(t, 9, col)
	l.custom_minimum_size = Vector2(_col.custom_minimum_size.x, 13)
	return l


func _divider() -> Control:
	var r := ColorRect.new()
	r.color = Color(UiArt.GOLD, 0.35)
	r.custom_minimum_size = Vector2(_col.custom_minimum_size.x, 1)
	return r


## Their words, readable: a larger face, room between paragraphs, each [keyword] a gold link.
func _text(t: String, size := 12, col := UiArt.CREAM) -> RichTextLabel:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.fit_content = true
	r.scroll_active = false
	r.custom_minimum_size = Vector2(_col.custom_minimum_size.x, 0)
	r.add_theme_font_override("normal_font", UiArt.font(false))
	r.add_theme_font_size_override("normal_font_size", size)
	r.add_theme_color_override("default_color", col)
	r.add_theme_constant_override("line_separation", 3)
	var re := RegEx.create_from_string("\\[([^\\]]+)\\]")
	r.text = re.sub(t.replace("\n", "\n\n").replace("\n\n\n\n", "\n\n"), "[url=$1][color=#f0c060]$1[/color][/url]", true)
	r.meta_clicked.connect(func(m): _answer(String(m)))
	UiArt.themed(r)
	return r


func _rewards(rw: Dictionary, choosing: bool) -> void:
	if rw.is_empty():
		return
	if not choosing:
		_col.add_child(_heading("REWARDS", UiArt.GOLD))
		var parts := []
		if int(rw.get("xp", 0)) > 0:
			parts.append("%s experience" % _num(int(rw.xp)))
		if int(rw.get("copper", 0)) > 0:
			parts.append(_money(int(rw.copper)))
		if int(rw.get("marks", 0)) > 0:
			parts.append("%d Marks of Valor" % int(rw.marks))
		if not parts.is_empty():
			_col.add_child(_text("  -  ".join(parts), 10, UiArt.CREAM))
		var items: Array = rw.get("items", [])
		if not items.is_empty():
			_col.add_child(_text("You will receive:", 9, UiArt.DIM))
			for it in items:
				_col.add_child(ItemRow.make(it, false, self))
	var choice: Array = rw.get("choice", [])
	if not choice.is_empty():
		var note := "Choose one:" if choosing else ("And choose one of these - which, depends on how it ends:" if int(rw.get("endings", 1)) > 1 else "And choose one of these:")
		_col.add_child(_text(note, 9, UiArt.DIM if not choosing else UiArt.GOLD_HI))
		for it in choice:
			_col.add_child(ItemRow.make(it, choosing, self))


func _fill_buttons(options: Array, kind: String) -> void:
	for c in _buttons.get_children():
		c.queue_free()
	var big := kind == "choice"
	for o in options:
		var role := String(o.get("role", "ask"))
		if role == "reward":
			continue                                     # (the item cards are the reward's buttons)
		var kw := String(o.get("kw", ""))
		var caption := kw
		if role == "accept":
			caption = "ACCEPT"
		elif role == "ask" and kind in ["offer", "topic"]:
			caption = "ASK ABOUT " + kw
		var w := 200.0 if big else clampf(28.0 + 6.5 * caption.length(), 70.0, 220.0)
		var b := UiArt.button(caption, Vector2(w, 18 if big else 15), 10 if big else 9)
		if role == "accept":
			b.add_theme_color_override("font_color", UiArt.GOLD_HI)
			b.tooltip_text = "\"%s\"" % kw
		b.pressed.connect(func(): _answer(kw))
		_buttons.add_child(b)
	if kind in ["offer", "talk", "idle", "end", "topic"]:
		var close := UiArt.button("DECLINE" if kind == "offer" else "GOODBYE", Vector2(80, 15), 9)
		close.pressed.connect(hide_window)
		_buttons.add_child(close)


func _answer(kw: String) -> void:
	Server.command("/whisper " + kw)


## A reward: picked (its card clicked) - the choice is made, the window done.
func pick(item_name: String) -> void:
	_answer(item_name)
	hide_window()


func _scroll_to_end() -> void:
	await get_tree().process_frame
	_scroll.scroll_vertical = int(_scroll.get_v_scroll_bar().max_value)


static func _num(n: int) -> String:
	var s := str(n)
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return s + out


static func _money(c: int) -> String:
	var g := c / 10000
	var s := (c / 100) % 100
	var cc := c % 100
	var parts := []
	if g > 0:
		parts.append("%d gold" % g)
	if s > 0:
		parts.append("%d silver" % s)
	if cc > 0 or parts.is_empty():
		parts.append("%d copper" % cc)
	return " ".join(parts)


## One reward item: its icon, name (in its con colour), slot and level; its bonuses and lore on hover. A reward to
## choose is a card: a click takes it.
class ItemRow:
	extends PanelContainer

	var data := {}
	var choosing := false
	var owner_window: Node

	static func make(it: Dictionary, pick: bool, win: Node) -> ItemRow:
		var r := ItemRow.new()
		r.data = it
		r.choosing = pick
		r.owner_window = win
		r.tooltip_text = String(it.get("name", ""))
		r.mouse_filter = Control.MOUSE_FILTER_STOP
		if pick:
			r.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.08, 0.07, 0.06, 0.85) if not pick else Color(0.16, 0.12, 0.06, 0.9)
		sb.border_color = Color(UiArt.GOLD, 0.25 if not pick else 0.6)
		sb.set_border_width_all(1)
		sb.set_corner_radius_all(3)
		sb.content_margin_left = 4
		sb.content_margin_right = 4
		sb.content_margin_top = 2
		sb.content_margin_bottom = 2
		r.add_theme_stylebox_override("panel", sb)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 6)
		row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		r.add_child(row)
		var icon := TextureRect.new()
		icon.texture = ItemDb.icon(Server.item_icon(int(it.get("model", 0))))
		icon.custom_minimum_size = Vector2(22, 22)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(icon)
		var txt := VBoxContainer.new()
		txt.add_theme_constant_override("separation", -2)
		txt.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(txt)
		var nm := UiArt.label(String(it.get("name", "")), 10, ItemTooltip.con_color(int(it.get("level", 0)), PlayerData.level))
		nm.mouse_filter = Control.MOUSE_FILTER_IGNORE
		txt.add_child(nm)
		var bon: Array = it.get("lines", [])
		var sub := "%s  -  level %d" % [String(it.get("slot", "")), int(it.get("level", 0))]
		if not bon.is_empty():
			sub += "  -  " + ", ".join(bon.slice(0, 4).map(func(l): return String(l).strip_edges()))
		var sl := UiArt.label(sub, 7, UiArt.DIM, false)
		sl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		sl.clip_text = true
		sl.custom_minimum_size = Vector2(380, 0)
		txt.add_child(sl)
		return r

	func _gui_input(event: InputEvent) -> void:
		if choosing and event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			owner_window.pick(String(data.get("name", "")))
			accept_event()

	func _make_custom_tooltip(_for_text: String) -> Object:
		var lines := ["%s - level %d" % [String(data.get("slot", "")), int(data.get("level", 0))]]
		for l in data.get("lines", []):
			lines.append(String(l))
		var lore := String(data.get("lore", ""))
		if lore != "":
			lines.append("")
			var line := ""
			for w in lore.split(" ", false):                # the lore, wrapped
				if line.length() + w.length() > 52:
					lines.append(line)
					line = ""
				line = (line + " " + w).strip_edges()
			if line != "":
				lines.append(line)
		if choosing:
			lines.append("")
			lines.append("Click to choose")
		return ItemTooltip.text_box(String(data.get("name", "")), lines)
