extends Control
## The Bard's Song Wheel (HibernianKits.cs; owner 2026-11-20: "an 'ability' that you learn ... place it on the bar, and
## then hold it and a wheel comes up for your song selection ... tapping it would choose a song in some sort of smart
## fashion"). The Song Wheel ability on a quickbar slot or a controller button:
##   tap  - the ability goes to the server, which plays the song that fits the moment;
##   hold - after HOLD_MS a wheel of your songs ("/songwheel list" -> "#SNG|name;name"); point at one with the mouse or
##          a stick and let go to play it (let go in the middle: nothing).

const HOLD_MS := 300
const R_OUT := 170.0
const R_IN := 46.0
const AIM_DEAD := 28.0

static var me: Control = null
static var songs: Array = []

var ui: Node
var _entry := {}
var _held: Variant = null
var _at := 0
var _shown := false
var _pick := -1
var _aim := Vector2.ZERO


static func is_wheel(e: Dictionary) -> bool:
	return String(e.get("kind", "")) == "ability" and String(e.get("name", "")).strip_edges().to_lower() == "song wheel"


## "#SNG|name;name;..." - the songs you know (the best rank of each).
static func receive(text: String) -> void:
	songs = []
	for n in text.split(";", false):
		songs.append(String(n))
	if me and is_instance_valid(me):
		me.queue_redraw()


func _ready() -> void:
	me = self
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## The button went down (input: a keycode, "m<button>" or "pad:<action>").
func press(e: Dictionary, input: Variant) -> void:
	_entry = e
	_held = input
	_at = Time.get_ticks_msec()
	_shown = false
	_pick = -1
	_aim = Vector2.ZERO
	Server.command("/songwheel list")


## A button came up: true when it was the wheel's (a tap plays the smart song, a hold plays the one pointed at).
func release(input: Variant) -> bool:
	if _held == null or (input != null and input != _held):
		return false
	_held = null
	if not _shown:
		Quickbar.use_entry(_entry)
		return true
	_shown = false
	queue_redraw()
	if _pick >= 0 and _pick < songs.size():
		_cast(String(songs[_pick]))
	return true


func holding() -> bool:
	return _held != null


func _cast(song: String) -> void:
	for li in Server.spell_lines.size():
		for sp in (Server.spell_lines[li].spells as Array):
			if String(sp.get("name", "")) == song:
				Quickbar.use_entry({"kind": "spell", "id": "srv:spell:%d:%d" % [li, int(sp.level)], "name": song, "icon": int(sp.get("icon", -1))})
				return
	var first := 0
	while first < Server.skills.size() and int(Server.skills[first].page) == 0:
		first += 1
	for i in range(first, Server.skills.size()):                   # (a hybrid's songs are in the skill list)
		if String(Server.skills[i].get("name", "")) == song:
			Quickbar.use_entry({"kind": "spell", "id": "srv:skill:%d" % (i - first), "name": song})
			return
	PlayerData.message.emit("You don't know %s." % song, "spells")


func _process(_delta: float) -> void:
	if ui and ui.has_method("area"):
		size = ui.area()
	if _held == null:
		return
	if not _shown and Time.get_ticks_msec() - _at >= HOLD_MS:
		_shown = true
		queue_redraw()
	if _shown:
		_stick_aim()


func _stick_aim() -> void:
	var d := Pad.device
	if d < 0:
		return
	var v := Vector2(Input.get_joy_axis(d, JOY_AXIS_LEFT_X), Input.get_joy_axis(d, JOY_AXIS_LEFT_Y))
	var r := Vector2(Input.get_joy_axis(d, JOY_AXIS_RIGHT_X), Input.get_joy_axis(d, JOY_AXIS_RIGHT_Y))
	if r.length() > v.length():
		v = r
	if v.length() >= 0.5:
		_point(v)


func _input(event: InputEvent) -> void:
	if not _shown or not (event is InputEventMouseMotion):
		return
	_aim += (event as InputEventMouseMotion).relative
	if _aim.length() > 120.0:
		_aim = _aim.normalized() * 120.0
	if _aim.length() >= AIM_DEAD:
		_point(_aim)
	get_viewport().set_input_as_handled()                   # (the camera stays put while you pick)


func _point(v: Vector2) -> void:
	if songs.is_empty():
		return
	var ang := fposmod(atan2(v.x, -v.y), TAU)              # 0 = up, clockwise
	var p := int(round(ang / TAU * songs.size())) % songs.size()
	if p != _pick:
		_pick = p
		queue_redraw()


func _draw() -> void:
	if not _shown:
		return
	var font := UiArt.font()
	var c := size * 0.5
	draw_circle(c, R_OUT, Color(0.06, 0.055, 0.05, 0.82))
	draw_arc(c, R_OUT, 0.0, TAU, 64, UiArt.GOLD, 2.0)
	draw_circle(c, R_IN, Color(0.12, 0.1, 0.08, 0.95))
	draw_arc(c, R_IN, 0.0, TAU, 48, Color(0.5, 0.42, 0.25), 1.5)
	var hint := "SONGS" if _pick < 0 or _pick >= songs.size() else String(songs[_pick]).to_upper()
	if songs.is_empty():
		hint = "NO SONGS"
	var hw := font.get_string_size(hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x
	draw_string(font, c + Vector2(-hw * 0.5, 4), hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, UiArt.GOLD_HI)
	for i in songs.size():
		var ang := TAU * i / songs.size()
		var at := c + Vector2(sin(ang), -cos(ang)) * 116.0
		var picked := i == _pick
		var text := String(songs[i]).to_upper()
		var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9).x + 14.0
		var rect := Rect2(at - Vector2(w * 0.5, 11), Vector2(w, 22))
		draw_rect(rect, Color(0.45, 0.36, 0.15, 0.95) if picked else Color(0.17, 0.15, 0.12, 0.92))
		draw_rect(rect, UiArt.GOLD_HI if picked else Color(0.5, 0.42, 0.25), false, 1.5 if picked else 1.0)
		draw_string(font, rect.position + Vector2(7, 15), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9,
				UiArt.GOLD_HI if picked else UiArt.CREAM)
