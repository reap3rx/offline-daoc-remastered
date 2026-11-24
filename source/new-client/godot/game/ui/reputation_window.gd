extends ClassicWindow
## The Reputation window (owner 2026-11-22): /rep or Shift+L. Your realm reputation at the top (it grows with every
## faction's standing, each up to its Legend mark, and your RvR deeds), then each zone's two factions - your rank, how
## far to the next, their titles (lit when earned) and what the next rank opens - and the titles you have earned, each
## with WEAR to keep it wherever you go; AUTO goes back to wearing the best one for where you are.
## The server sends it all as "#REPW|{...}" (ReputationService.SendWindow).

const BODY := Vector2(470, 420)
const RANK_COLOR := {"Unknown": Color(0.6, 0.57, 0.52), "Familiar": Color(0.93, 0.89, 0.78), "Trusted": Color(0.55, 0.85, 1.0),
		"Honoured": Color(0.6, 1.0, 0.55), "Legend": Color(1.0, 0.85, 0.45)}

var _title: Label
var _wearing: Label
var _rows: VBoxContainer


func build() -> void:
	closable = true
	_title = UiArt.label("REPUTATION", 10, UiArt.GOLD_HI)
	_title.position = Vector2(8, 4)
	_title.size = Vector2(BODY.x - 16, 14)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_title)
	_wearing = UiArt.label("", 8, UiArt.CREAM)
	_wearing.position = Vector2(12, 22)
	_wearing.size = Vector2(BODY.x - 90, 12)
	_wearing.clip_text = true
	add_child(_wearing)
	var auto := UiArt.button("AUTO", Vector2(56, 14), 8)
	auto.position = Vector2(BODY.x - 72, 20)
	auto.tooltip_text = "Wear your best title for wherever you are"
	auto.pressed.connect(func(): Server.command("/rep title auto"))
	add_child(auto)
	var scroll := ScrollContainer.new()
	scroll.position = Vector2(8, 40)
	scroll.size = Vector2(BODY.x - 16, BODY.y - 50)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	_rows = VBoxContainer.new()
	_rows.custom_minimum_size = Vector2(BODY.x - 30, 0)
	_rows.add_theme_constant_override("separation", 3)
	scroll.add_child(_rows)
	set_window_size(BODY)


func receive(json: String) -> void:
	var d = JSON.parse_string(json)
	if not (d is Dictionary):
		return
	for c in _rows.get_children():
		c.queue_free()
	var wearing := String(d.get("title", ""))
	var locked := String(d.get("locked", ""))
	_wearing.text = ("WEARING: %s%s" % [wearing, "  (KEPT EVERYWHERE)" if locked != "" else "  (BY WHERE YOU ARE)"]) if wearing != "" else "NO TITLE YET - TRUSTED WITH A FACTION EARNS ONE"
	var realm: Dictionary = d.get("realm", {})
	_rows.add_child(_header(String(realm.get("name", "Realm")).to_upper() + " - REALM REPUTATION"))
	var rnext := ""
	for t in realm.get("titles", []):
		if not bool(t.get("earned", false)) and String(t.get("title", "")) != "":
			rnext = "  Next title: %s (%s)." % [String(t.get("title", "")), String(t.get("rank", ""))]
			break
	_rows.add_child(_standing(realm, "Every faction's standing (up to its Legend mark) and your RvR deeds (%s of it).%s" % [_n(float(realm.get("rvr", 0))), rnext]))
	for z in d.get("zones", []):
		_rows.add_child(_header(String(z.get("name", "")).to_upper()))
		for f in z.get("factions", []):
			_rows.add_child(_standing(f, String(f.get("next", ""))))
	var titles: Array = d.get("titles", [])
	_rows.add_child(_header("YOUR TITLES"))
	if titles.is_empty():
		_rows.add_child(_line("None yet.", UiArt.DIM))
	for t in titles:
		_rows.add_child(_title_row(t, String(t.get("title", "")) == locked))
	if not visible:
		show_window()


func _header(text: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(BODY.x - 30, 18)
	var l := UiArt.label(text, 9, UiArt.GOLD)
	l.position = Vector2(2, 4)
	l.size = Vector2(BODY.x - 34, 12)
	c.add_child(l)
	var rule := ColorRect.new()
	rule.color = Color(0.55, 0.45, 0.25, 0.6)
	rule.position = Vector2(2, 17)
	rule.size = Vector2(BODY.x - 34, 1)
	c.add_child(rule)
	return c


func _line(text: String, col: Color) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(BODY.x - 30, 13)
	var l := UiArt.label(text, 7, col, false)
	l.position = Vector2(4, 0)
	l.size = Vector2(BODY.x - 38, 12)
	l.clip_text = true
	c.add_child(l)
	return c


## One faction (or the realm): its name and your rank, the bar to the next rank, its titles, what comes next.
func _standing(f: Dictionary, note: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(BODY.x - 30, 58)
	var rank := String(f.get("rank", "Unknown"))
	var col: Color = RANK_COLOR.get(rank, UiArt.CREAM)
	var name := UiArt.label(String(f.get("name", "")), 9, UiArt.CREAM)
	name.position = Vector2(4, 0)
	name.size = Vector2(260, 12)
	name.clip_text = true
	c.add_child(name)
	var rl := UiArt.label(rank.to_upper(), 9, col)
	rl.position = Vector2(BODY.x - 150, 0)
	rl.size = Vector2(110, 12)
	rl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	c.add_child(rl)
	var lo := float(f.get("lo", 0))
	var hi := float(f.get("hi", 0))
	var pts := float(f.get("points", 0))
	var frac := 1.0 if hi <= lo else clampf((pts - lo) / (hi - lo), 0.0, 1.0)
	var back := ColorRect.new()
	back.color = Color(0.1, 0.08, 0.05, 0.95)
	back.position = Vector2(4, 15)
	back.size = Vector2(BODY.x - 120, 7)
	c.add_child(back)
	var fill := ColorRect.new()
	fill.color = col
	fill.position = back.position
	fill.size = Vector2(back.size.x * frac, back.size.y)
	c.add_child(fill)
	var nums := UiArt.label(("%s / %s" % [_n(pts), _n(hi)]) if hi > lo else _n(pts), 7, UiArt.DIM, false)
	nums.position = Vector2(BODY.x - 112, 13)
	nums.size = Vector2(76, 10)
	nums.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	c.add_child(nums)
	var parts := []
	for t in f.get("titles", []):
		var tt := String(t.get("title", ""))
		if tt != "" and bool(t.get("earned", false)):
			parts.append(tt)
	var tl := UiArt.label(("TITLES: " + ", ".join(parts)) if not parts.is_empty() else "NO TITLE HERE YET", 7,
			UiArt.CREAM if not parts.is_empty() else UiArt.DIM, false)
	tl.position = Vector2(4, 26)
	tl.size = Vector2(BODY.x - 38, 11)
	tl.clip_text = true
	c.add_child(tl)
	var nl := UiArt.label(note, 7, UiArt.DIM, false)
	nl.position = Vector2(4, 39)
	nl.size = Vector2(BODY.x - 38, 11)
	nl.clip_text = true
	c.add_child(nl)
	return c


func _title_row(t: Dictionary, kept: bool) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(BODY.x - 30, 18)
	var l := UiArt.label("%s  (%s, %s)" % [String(t.get("title", "")), String(t.get("from", "")), String(t.get("rank", ""))], 8,
			UiArt.GOLD_HI if kept else UiArt.CREAM)
	l.position = Vector2(4, 3)
	l.size = Vector2(BODY.x - 110, 12)
	l.clip_text = true
	c.add_child(l)
	var wear := UiArt.button("KEPT" if kept else "WEAR", Vector2(56, 14), 8)
	wear.position = Vector2(BODY.x - 96, 1)
	wear.disabled = kept
	var n := int(t.get("n", 0))
	wear.pressed.connect(func(): Server.command("/rep title %d" % n))
	c.add_child(wear)
	return c


static func _n(v: float) -> String:
	var s := str(int(v))
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return s + out
