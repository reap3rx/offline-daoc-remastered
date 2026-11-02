extends Control
## Dynamic events (owner 2026-11-01: GW2-style events in every zone). The server (scripts/dynamicevents) sends the
## events of your zone every two seconds as a "#EV|" system line: a JSON list of
##   {id, title, stage, kind, objective, line, progress 0..1, time_left s, x, y (zone metres), r (m), zone, levels,
##    near, state: active | success | fail}.
## The tracker (top right) shows the events you are at - title, stage, objective, a progress bar and the time left -
## and below them one line for each other event in the zone with its distance and direction; a finished one shows its
## outcome for a few seconds. The map draws them all (MapWindow).

static var events: Array = []
static var received_ms := 0

const W := 214.0
const GOLD := Color(1.0, 0.82, 0.35)
const CREAM := Color(0.95, 0.92, 0.82)
const DIM := Color(0.75, 0.72, 0.64)
const BAR := Color(0.95, 0.55, 0.12)
const WIN := Color(0.45, 0.95, 0.4)
const LOSE := Color(0.95, 0.35, 0.3)

var player: Node3D
var current_zone := -1


static func receive(text: String) -> void:
	var parsed = JSON.parse_string(text)
	events = parsed if parsed is Array else []
	received_ms = Time.get_ticks_msec()


## The events to draw on a zone's map.
static func in_zone(zone_id: int) -> Array:
	if Time.get_ticks_msec() - received_ms > 8000:
		return []                                       # (the server stopped telling: nothing is running)
	return events.filter(func(e): return int(e.get("zone", -1)) == zone_id and e.has("x"))


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(_delta: float) -> void:
	if Engine.get_process_frames() % 6 == 0:
		queue_redraw()


func _player_m() -> Vector2:
	if player == null:
		return Vector2.INF
	return Vector2(player.global_position.x, player.global_position.z)   # the current zone sits at the scene origin


static func _dir(v: Vector2) -> String:
	var deg := fposmod(rad_to_deg(atan2(v.x, -v.y)), 360.0)               # north up, clockwise
	return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int(round(deg / 45.0)) % 8]


func _draw() -> void:
	if Time.get_ticks_msec() - received_ms > 8000 or events.is_empty():
		return
	var font := UiArt.font(true)
	var thin := UiArt.font(false)
	var y := 0.0
	var me := _player_m()
	var near: Array = []
	var far: Array = []
	for e in events:
		var st := String(e.get("state", "active"))
		if st != "active" or bool(e.get("near", false)):
			near.append(e)
		else:
			far.append(e)
	var h := 0.0
	for e in near:
		h += 74.0 if String(e.get("state", "active")) == "active" else 34.0
	if not far.is_empty():
		h += 16.0 + far.size() * 13.0
	draw_rect(Rect2(0, 0, W, h + 6), Color(0.02, 0.02, 0.03, 0.62))
	draw_rect(Rect2(0, 0, W, h + 6), Color(0.55, 0.45, 0.25, 0.7), false, 1.0)
	y = 4.0
	for e in near:
		var st := String(e.get("state", "active"))
		_text(font, Vector2(8, y + 11), String(e.get("title", "")), 10, GOLD)
		if st != "active":
			_text(thin, Vector2(8, y + 25), "Event complete" if st == "success" else "Event failed", 9, WIN if st == "success" else LOSE)
			y += 34.0
			continue
		var lv: Array = e.get("levels", [])
		if lv.size() == 2:
			var tag := "%d-%d" % [int(lv[0]), int(lv[1])]
			_text(thin, Vector2(W - 8 - thin.get_string_size(tag, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, y + 11), tag, 8, DIM)
		_text(font, Vector2(8, y + 25), String(e.get("stage", "")), 9, CREAM)
		_text(thin, Vector2(8, y + 38), _fit(thin, String(e.get("objective", "")), 8, W - 16), 8, DIM)
		var p := clampf(float(e.get("progress", 0.0)), 0.0, 1.0)
		var bar := Rect2(8, y + 44, W - 16, 8)
		draw_rect(bar, Color(0.1, 0.08, 0.05, 0.9))
		draw_rect(Rect2(bar.position, Vector2(bar.size.x * p, bar.size.y)), BAR)
		draw_rect(bar, Color(0.6, 0.5, 0.3, 0.9), false, 1.0)
		var t := int(e.get("time_left", 0))
		var clock := "%d:%02d" % [t / 60, t % 60]
		_text(thin, Vector2(8, y + 65), _fit(thin, String(e.get("line", "")), 8, W - 50), 8, CREAM)
		_text(thin, Vector2(W - 8 - thin.get_string_size(clock, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, y + 65), clock, 8, CREAM)
		y += 74.0
	if not far.is_empty():
		_text(font, Vector2(8, y + 11), "EVENTS IN THIS ZONE", 8, DIM)
		y += 16.0
		for e in far:
			var where := ""
			if me != Vector2.INF and int(e.get("zone", -1)) == current_zone:
				var d := Vector2(float(e.x), float(e.y)) - me
				where = "%d m %s" % [int(d.length()), _dir(d)]
			_text(thin, Vector2(10, y + 9), _fit(thin, String(e.get("title", "")), 8, W - 70), 8, CREAM)
			_text(thin, Vector2(W - 8 - thin.get_string_size(where, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, y + 9), where, 8, GOLD)
			y += 13.0


func _text(f: Font, at: Vector2, s: String, fs: int, col: Color) -> void:
	draw_string_outline(f, at, s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 2, Color(0, 0, 0, 0.8))
	draw_string(f, at, s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)


static func _fit(f: Font, s: String, fs: int, w: float) -> String:
	if f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x <= w:
		return s
	while s.length() > 3 and f.get_string_size(s + "...", HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > w:
		s = s.substr(0, s.length() - 1)
	return s + "..."
