extends Control
## Dynamic events (owner 2026-11-01: GW2-style events in every zone). The server (scripts/dynamicevents) sends the
## events of your zone every two seconds as a "#EV|" system line: a JSON list of
##   {id, title, stage, kind, objective, line, progress 0..1, time_left s, x, y (zone metres), r (m), zone, levels,
##    near, state: active | next (resting before the next stage) | occupied (a failed event's monsters hold the land
##    until driven out: an "occupy" stage, no time limit) | dormant
##    (a disturbance: hint, waiting for someone to come near) | giver (giver: an NPC who'd lead you) | success | fail}.
## The tracker (top right) shows the events you are at - title, stage, objective, a progress bar and the time left -
## and below them one line for each other event in the zone with its distance and direction; a finished one shows its
## outcome for a few seconds. The map draws them all (MapWindow).

static var events: Array = []
static var received_ms := 0
## The zone panel over the events (owner 2026-11-20: "The UI would have to have the Zone information (above the Events)
## Where it told you your XP rate at all times and what zone category it was"): the server's "#ZXP|" line every 30 s and
## on a zone change (ZoneRates.cs) - {name, rating, rate, explore, next (minutes to the next drop, -1 none)}.
static var zone_info := {}
static var zone_ms := -1000000
const ZONE_H := 34.0
const RATING_COLOR := {"Peaceful": Color(0.55, 0.9, 0.5), "Wild": Color(0.95, 0.85, 0.4),
		"Dangerous": Color(0.98, 0.6, 0.25), "Deadly": Color(0.95, 0.32, 0.28),
		"Elite": Color(0.78, 0.45, 0.98)}   # (Elite, 2026-11-23: past Deadly - the purple)


static func receive_zone(text: String) -> void:
	var f := text.split("|")
	if f.size() < 5:
		return
	zone_info = {"name": f[0], "rating": f[1], "rate": float(f[2]), "explore": float(f[3]), "next": int(f[4])}
	zone_ms = Time.get_ticks_msec()


## Your standing with the zone's two factions (owner 2026-11-22: reputation "can even be its own 'xp' bar in the Zone
## window"): the server's "#REP|{zone, factions:[{name, rank, points, lo, hi, title}], realm, title}"
## (ReputationService.Push), two thin bars under the rate line - its rank in its colour, how far to the next.
static var rep_info := {}
const REP_ROW := 15.0
const RANK_COLOR := {"Unknown": Color(0.6, 0.57, 0.52), "Familiar": Color(0.93, 0.89, 0.78), "Trusted": Color(0.55, 0.85, 1.0),
		"Honoured": Color(0.6, 1.0, 0.55), "Legend": Color(1.0, 0.85, 0.45)}


static func receive_rep(text: String) -> void:
	var d = JSON.parse_string(text)
	rep_info = d if d is Dictionary else {}


static func _rep_rows() -> Array:
	var f = rep_info.get("factions")
	return f if f is Array else []


## The zone's siege (ZoneSiege.cs, owner 2026-11-22: Dergan Island): "#SIEGE|{name, state, resolve, enemy, line}" every
## few seconds while you're in its zone - a row with its name and the resolve bar (or HELD), and a line under it.
static var siege_info := {}
static var siege_ms := 0


static func receive_siege(text: String) -> void:
	var d = JSON.parse_string(text)
	siege_info = d if d is Dictionary else {}
	siege_ms = Time.get_ticks_msec()


static func _siege_shown() -> bool:
	return not siege_info.is_empty() and Time.get_ticks_msec() - siege_ms < 15000


static func zone_h() -> float:
	return ZONE_H + REP_ROW * _rep_rows().size() + (REP_ROW * 2.0 if _siege_shown() else 0.0)


static func _zone_shown() -> bool:
	return not zone_info.is_empty() and Time.get_ticks_msec() - zone_ms < 95000

const W := 214.0
const GOLD := Color(1.0, 0.82, 0.35)
const CREAM := Color(0.95, 0.92, 0.82)
const DIM := Color(0.75, 0.72, 0.64)
const BAR := Color(0.95, 0.55, 0.12)
const WIN := Color(0.45, 0.95, 0.4)
const LOSE := Color(0.95, 0.35, 0.3)
const HINT := Color(0.95, 0.85, 0.45)                 # a disturbance, waiting for someone to come near
const GIVER := Color(0.35, 0.85, 1.0)                 # someone who'd lead you, if you ask

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


## The names of the NPCs who'd lead you into an event now (QuestMarkers rings them).
static func givers() -> Array:
	if Time.get_ticks_msec() - received_ms > 8000:
		return []
	return events.filter(func(e): return String(e.get("state", "")) == "giver").map(func(e): return String(e.get("giver", "")))


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(_delta: float) -> void:
	# its text size (Options > Interface > TEXT AND FONTS: "events"): the tracker drawn bigger as a whole, from its
	# top right corner, so its lines keep their places
	var k := UiArt.text_scale("events")
	if not is_equal_approx(scale.x, k):
		scale = Vector2(k, k)
	pivot_offset = Vector2(W, 0.0)
	if Engine.get_process_frames() % 6 == 0:
		queue_redraw()


## The zone: its name and danger rating, and what its monsters pay you now (experience and coin), with the exploration
## part and when it next drops.
func _draw_zone(font: Font, thin: Font) -> void:
	var z := zone_info
	var zh := zone_h()
	draw_rect(Rect2(0, 0, W, zh), Color(0.02, 0.02, 0.03, 0.62))
	draw_rect(Rect2(0, 0, W, zh), Color(0.55, 0.45, 0.25, 0.7), false, 1.0)
	_text(font, Vector2(8, 13), String(z.name).to_upper(), 10, GOLD)
	var rating := String(z.rating)
	var rc: Color = RATING_COLOR.get(rating, CREAM)
	_text(font, Vector2(W - 8 - font.get_string_size(rating.to_upper(), HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, 13), rating.to_upper(), 8, rc)
	var rate := float(z.rate)
	var line := "XP and coin x%s" % _num(rate)
	var nxt := int(z.next)
	if nxt >= 0:
		line += "  -  drops in %d min" % maxi(1, nxt)
	else:
		line += "  -  well explored today"
	_text(thin, Vector2(8, 27), line, 9, WIN if rate >= 1.2 else (CREAM if rate >= 1.0 else LOSE))
	# the zone's factions: your rank with each, and how far to the next
	var y := ZONE_H - 3.0
	for f in _rep_rows():
		var rank := String(f.get("rank", "Unknown"))
		var rc2: Color = RANK_COLOR.get(rank, CREAM)
		var bw := 58.0
		_text(thin, Vector2(8, y + 10), _fit(thin, "%s  %s" % [String(f.get("name", "")), rank.to_upper()], 8, W - 24 - bw), 8, rc2)
		var lo := float(f.get("lo", 0))
		var hi := float(f.get("hi", 0))
		var frac := 1.0 if hi <= lo else clampf((float(f.get("points", 0)) - lo) / (hi - lo), 0.0, 1.0)
		var bar := Rect2(W - 8 - bw, y + 4, bw, 6)
		draw_rect(bar, Color(0.1, 0.08, 0.05, 0.9))
		draw_rect(Rect2(bar.position, Vector2(bar.size.x * frac, bar.size.y)), rc2)
		draw_rect(bar, Color(0.6, 0.5, 0.3, 0.9), false, 1.0)
		y += REP_ROW
	# the zone's siege: its name and how full the resolve is (or that it's held), and how it stands
	if _siege_shown():
		var st := String(siege_info.get("state", ""))
		var held := st == "held"
		var sc: Color = WIN if held else (GOLD if st in ["open", "assault"] else CREAM)
		var bw2 := 58.0
		_text(thin, Vector2(8, y + 10), _fit(thin, String(siege_info.get("name", "")).to_upper(), 8, W - 24 - bw2), 8, sc)
		var bar2 := Rect2(W - 8 - bw2, y + 4, bw2, 6)
		if held:
			_text(thin, Vector2(W - 8 - thin.get_string_size("HELD", HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, y + 10), "HELD", 8, WIN)
		else:
			draw_rect(bar2, Color(0.1, 0.08, 0.05, 0.9))
			draw_rect(Rect2(bar2.position, Vector2(bar2.size.x * clampf(float(siege_info.get("resolve", 0)) / 100.0, 0.0, 1.0), bar2.size.y)), GOLD)
			var en := clampf(float(siege_info.get("enemy", 0)) / 100.0, 0.0, 1.0)
			if en > 0.0:                                 # the enemy's strength: a red sliver under it
				draw_rect(Rect2(bar2.position + Vector2(0, bar2.size.y), Vector2(bar2.size.x * en, 2)), LOSE)
			draw_rect(bar2, Color(0.6, 0.5, 0.3, 0.9), false, 1.0)
		y += REP_ROW
		var sline := String(siege_info.get("line", ""))
		_text(thin, Vector2(8, y + 10), _fit(thin, sline, 8, W - 16), 8, LOSE if sline.begins_with("Under attack") else DIM)
		y += REP_ROW


static func _num(v: float) -> String:
	var s := "%.2f" % v
	while s.ends_with("0"):
		s = s.substr(0, s.length() - 1)
	return s.trim_suffix(".")


func _player_m() -> Vector2:
	if player == null:
		return Vector2.INF
	return Vector2(player.global_position.x, player.global_position.z)   # the current zone sits at the scene origin


static func _dir(v: Vector2) -> String:
	var deg := fposmod(rad_to_deg(atan2(v.x, -v.y)), 360.0)               # north up, clockwise
	return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int(round(deg / 45.0)) % 8]


## The height the tracker draws now (the modern HUD's quest log sits under it).
func content_height() -> float:
	var zh := (zone_h() + 4.0) * scale.y if _zone_shown() else 0.0
	if Time.get_ticks_msec() - received_ms > 8000 or events.is_empty():
		return zh
	var h := 0.0
	var far := 0
	for e in events:
		var st := String(e.get("state", "active"))
		if st in ["success", "fail"] or (st in ["active", "next", "occupied"] and bool(e.get("near", false))):
			h += 74.0 if st in ["active", "occupied"] else (60.0 if st == "next" else 34.0)
		else:
			far += 1
	if far > 0:
		h += 16.0 + far * 13.0
	return (h + 6.0) * scale.y + zh


func _draw() -> void:
	var t_draw := Time.get_ticks_usec()
	_draw_timed()
	Perf.note("drawing: event_tracker", t_draw)


func _draw_timed() -> void:
	var font := UiArt.font(true, "events")
	var thin := UiArt.font(false, "events")
	if _zone_shown():
		_draw_zone(font, thin)
		draw_set_transform(Vector2(0, zone_h() + 4.0))
	if Time.get_ticks_msec() - received_ms > 8000 or events.is_empty():
		draw_set_transform(Vector2.ZERO)
		return
	var y := 0.0
	var me := _player_m()
	var near: Array = []
	var far: Array = []
	for e in events:
		var st := String(e.get("state", "active"))
		if st in ["success", "fail"] or (st in ["active", "next", "occupied"] and bool(e.get("near", false))):
			near.append(e)
		else:
			far.append(e)
	var h := 0.0
	for e in near:
		var st := String(e.get("state", "active"))
		h += 74.0 if st in ["active", "occupied"] else (60.0 if st == "next" else 34.0)
	if not far.is_empty():
		h += 16.0 + far.size() * 13.0
	draw_rect(Rect2(0, 0, W, h + 6), Color(0.02, 0.02, 0.03, 0.62))
	draw_rect(Rect2(0, 0, W, h + 6), Color(0.55, 0.45, 0.25, 0.7), false, 1.0)
	y = 4.0
	for e in near:
		var st := String(e.get("state", "active"))
		_text(font, Vector2(8, y + 11), String(e.get("title", "")), 10, LOSE if st == "occupied" else GOLD)
		if st in ["success", "fail"]:
			_text(thin, Vector2(8, y + 25), "Event complete" if st == "success" else "Event failed", 9, WIN if st == "success" else LOSE)
			y += 34.0
			continue
		var lv: Array = e.get("levels", [])
		if lv.size() == 2:
			var tag := "%d-%d" % [int(lv[0]), int(lv[1])]
			_text(thin, Vector2(W - 8 - thin.get_string_size(tag, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, y + 11), tag, 8, DIM)
		var t := int(e.get("time_left", 0))
		var clock := "OCCUPIED" if st == "occupied" else "%d:%02d" % [t / 60, t % 60]
		if st == "next":
			_text(font, Vector2(8, y + 25), "Next: " + String(e.get("stage", "")), 9, CREAM)
			_text(thin, Vector2(8, y + 38), _fit(thin, String(e.get("objective", "")), 8, W - 16), 8, DIM)
			_text(thin, Vector2(8, y + 52), String(e.get("line", "")), 8, WIN)
			_text(thin, Vector2(W - 8 - thin.get_string_size(clock, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, y + 52), clock, 8, CREAM)
			y += 60.0
			continue
		_text(font, Vector2(8, y + 25), String(e.get("stage", "")), 9, CREAM)
		_text(thin, Vector2(8, y + 38), _fit(thin, String(e.get("objective", "")), 8, W - 16), 8, DIM)
		var p := clampf(float(e.get("progress", 0.0)), 0.0, 1.0)
		var bar := Rect2(8, y + 44, W - 16, 8)
		draw_rect(bar, Color(0.1, 0.08, 0.05, 0.9))
		draw_rect(Rect2(bar.position, Vector2(bar.size.x * p, bar.size.y)), LOSE if st == "occupied" else BAR)
		draw_rect(bar, Color(0.6, 0.5, 0.3, 0.9), false, 1.0)
		_text(thin, Vector2(8, y + 65), _fit(thin, String(e.get("line", "")), 8, W - 24 - thin.get_string_size(clock, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x), 8, CREAM)
		_text(thin, Vector2(W - 8 - thin.get_string_size(clock, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, y + 65), clock, 8, CREAM)
		y += 74.0
	if not far.is_empty():
		_text(font, Vector2(8, y + 11), "EVENTS IN THIS ZONE", 8, DIM)
		y += 16.0
		for e in far:
			var st := String(e.get("state", "active"))
			var where := ""
			if me != Vector2.INF and int(e.get("zone", -1)) == current_zone and e.has("x"):
				var d := Vector2(float(e.x), float(e.y)) - me
				where = "%d m %s" % [int(d.length()), _dir(d)]
			# a running one by its title; a disturbance by what you'd notice; a giver by who is asking
			var line := String(e.get("hint", "")) if st in ["dormant", "giver"] else String(e.get("title", ""))
			var col := HINT if st == "dormant" else (GIVER if st == "giver" else (LOSE if st == "occupied" else CREAM))
			_text(thin, Vector2(10, y + 9), _fit(thin, line, 8, W - 70), 8, col)
			_text(thin, Vector2(W - 8 - thin.get_string_size(where, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x, y + 9), where, 8, GOLD)
			y += 13.0


func _text(f: Font, at: Vector2, s: String, fs: int, col: Color) -> void:
	draw_string_outline(f, at, s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 2, Color(0, 0, 0, 0.8))
	draw_string(f, at, s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)


static func _fit(f: Font, s: String, fs: int, w: float) -> String:
	return UiArt.fit(f, s, fs, w)
