extends ClassicWindow
## The tier tuning window (owner 2026-11-21: "make it a window that pops up if I type /tier tune (so I can tune all tiers
## of hits, takes, and presses)"). /tier tune asks the server (MonsterTiers.cs, TierCommandHandler) for
## "#TUNE|{level, like, toughness, bite, tiers:[{name, hits, takes, press, nowHits, nowTakes}]}"; a row for each con:
##   HITS  - how hard that tier hits you, times its target (1 = as fitted; a con is the same fight at every level)
##   TAKES - how much of your damage it takes (2 = it goes down twice as fast)
##   PRESS - added to each blow in a row you land on it, up to five (0 = no pressing on that tier)
##   NOW   - what the two come to for you at your level, everything counted
## Each change goes to the server at once (/tier tune tier <name> hits|takes|press <v>), is saved there
## (tier-tuning.txt) and the window refreshes from its answer. Open to everyone, so it can be used out of GM mode
## (monsters don't fight a GM).

const BODY := Vector2(500, 266)
const ROW_H := 24.0
const TOP := 40.0
const COLORS := {
	"grey": Color(0.62, 0.62, 0.62), "green": Color(0.4, 0.9, 0.4), "blue": Color(0.45, 0.65, 1.0),
	"yellow": Color(1.0, 0.92, 0.35), "orange": Color(1.0, 0.62, 0.25), "red": Color(1.0, 0.35, 0.3),
	"purple": Color(0.8, 0.5, 1.0) }
const COL_X := {"hits": 70.0, "takes": 170.0, "press": 270.0}

var _title: Label
var _edits := {}            # "green:hits" -> LineEdit
var _now := {}              # "green" -> Label
var _globals := {}          # "toughness" -> LineEdit
var _values := {}           # "green:hits" -> float (press as a fraction)


func build() -> void:
	closable = true
	_title = UiArt.label("TIER TUNING", 10, UiArt.GOLD_HI)
	_title.position = Vector2(8, 4)
	_title.size = Vector2(BODY.x - 16, 14)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_title)
	_head("TIER", 10, 50)
	_head("HITS YOU x", COL_X.hits, 94)
	_head("TAKES x", COL_X.takes, 94)
	_head("PRESS % / HIT", COL_X.press, 94)
	_head("NOW AT YOUR LEVEL", 372, 120)
	var names := ["grey", "green", "blue", "yellow", "orange", "red", "purple"]
	for i in names.size():
		var n: String = names[i]
		var y := TOP + i * ROW_H
		var l := UiArt.label(n.to_upper(), 9, COLORS[n])
		l.position = Vector2(10, y + 4)
		l.size = Vector2(56, 12)
		add_child(l)
		for what in ["hits", "takes", "press"]:
			_stepper(n + ":" + what, Vector2(COL_X[what], y), func(v: float): _send_tier(n, what, v))
		var now := UiArt.label("", 8, UiArt.CREAM)
		now.position = Vector2(372, y + 5)
		now.size = Vector2(124, 12)
		add_child(now)
		_now[n] = now
	var gy := TOP + 7 * ROW_H + 8
	var t := UiArt.label("ALL TOUGHNESS", 8, UiArt.CREAM)
	t.position = Vector2(10, gy + 5)
	t.size = Vector2(90, 12)
	add_child(t)
	_stepper("toughness", Vector2(100, gy), func(v: float): _send_global("toughness", v))
	var b := UiArt.label("ALL BITE", 8, UiArt.CREAM)
	b.position = Vector2(200, gy + 5)
	b.size = Vector2(60, 12)
	add_child(b)
	_stepper("bite", Vector2(254, gy), func(v: float): _send_global("bite", v))
	var reset := UiArt.button("RESET TIERS", Vector2(96, 18), 8)
	reset.position = Vector2(BODY.x - 106, gy + 1)
	reset.pressed.connect(func(): Server.command("/tier tune reset"))
	add_child(reset)
	var hint := UiArt.label("HITS: HOW HARD IT HITS YOU  -  TAKES: HOW FAST IT GOES DOWN  -  PRESS: BONUS PER HIT IN A ROW", 6, UiArt.DIM)
	hint.position = Vector2(8, BODY.y - 18)
	hint.size = Vector2(BODY.x - 16, 10)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(hint)
	set_window_size(BODY)


func _head(text: String, x: float, w: float) -> void:
	var l := UiArt.label(text, 7, UiArt.GOLD)
	l.position = Vector2(x, 24)
	l.size = Vector2(w, 10)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER if x > 20 else HORIZONTAL_ALIGNMENT_LEFT
	add_child(l)


## [-] [value] [+]: the step is 0.05 (5 for PRESS, shown as a percent); typing a value and pressing Enter sends it too.
func _stepper(key: String, at: Vector2, send: Callable) -> void:
	var pct := key.ends_with(":press")
	var minus := UiArt.button("-", Vector2(18, 18), 9)
	minus.position = at + Vector2(0, 1)
	add_child(minus)
	var e := LineEdit.new()
	e.position = at + Vector2(22, 0)
	e.size = Vector2(48, 20)
	e.alignment = HORIZONTAL_ALIGNMENT_CENTER
	e.add_theme_font_override("font", UiArt.font(true))
	e.add_theme_font_size_override("font_size", 9)
	e.add_theme_color_override("font_color", UiArt.CREAM)
	e.add_theme_stylebox_override("normal", _box(false))
	e.add_theme_stylebox_override("focus", _box(true))
	add_child(e)
	var plus := UiArt.button("+", Vector2(18, 18), 9)
	plus.position = at + Vector2(74, 1)
	add_child(plus)
	_edits[key] = e
	var step := func(dir: float):
		var v: float = float(_values.get(key, 0.0)) + dir * 0.05
		v = maxf(0.0 if pct else 0.05, snappedf(v, 0.01))
		_set_value(key, v)
		send.call(v)
	minus.pressed.connect(func(): step.call(-1.0))
	plus.pressed.connect(func(): step.call(1.0))
	e.text_submitted.connect(func(text: String):
		e.release_focus()
		if not text.strip_edges().is_valid_float():
			_set_value(key, float(_values.get(key, 0.0)))
			return
		var v := text.strip_edges().to_float() / (100.0 if pct else 1.0)
		if v < 0.0 or (v <= 0.0 and not pct):
			_set_value(key, float(_values.get(key, 0.0)))
			return
		_set_value(key, v)
		send.call(v))


func _set_value(key: String, v: float) -> void:
	_values[key] = v
	var e: LineEdit = _edits.get(key)
	if e and not e.has_focus():
		e.text = ("%d" % roundi(v * 100.0)) if key.ends_with(":press") else ("%.2f" % v)


func _send_tier(tier: String, what: String, v: float) -> void:
	Server.command("/tier tune tier %s %s %s" % [tier, what, String.num(v, 3)])


func _send_global(what: String, v: float) -> void:
	Server.command("/tier tune %s %s" % [what, String.num(v, 3)])


## The server's numbers: shown, and the window opened.
func receive(json: String) -> void:
	var d = JSON.parse_string(json)
	if not (d is Dictionary):
		return
	# (one footing at every level since 2026-11-22: a con is the same fight whatever your level - no "you fight like")
	_title.text = "TIER TUNING  -  LEVEL %d  (THE SAME AT EVERY LEVEL)" % int(d.get("level", 0))
	for t in d.get("tiers", []):
		var n := String(t.get("name", ""))
		for what in ["hits", "takes", "press"]:
			_set_value(n + ":" + what, float(t.get(what, 0.0)))
		if _now.has(n):
			_now[n].text = "HITS x%.2f  TAKES x%.2f" % [float(t.get("nowHits", 0.0)), float(t.get("nowTakes", 0.0))]
	_set_value("toughness", float(d.get("toughness", 1.0)))
	_set_value("bite", float(d.get("bite", 1.0)))
	if not visible:
		show_window()


static func _like(p: float) -> String:
	var names := ["GREY", "GREEN", "BLUE", "YELLOW", "ORANGE", "RED", "PURPLE"]
	var i := clampi(roundi(p) + 3, 0, 6)
	return "A %s (%.1f)" % [names[i], p]


static func _box(hi: bool) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(0.05, 0.045, 0.04, 0.95)
	s.border_color = UiArt.GOLD if hi else UiArt.GOLD.darkened(0.45)
	s.set_border_width_all(1)
	s.set_content_margin_all(2)
	return s
