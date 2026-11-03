extends Control
## The modern interface (owner 2026-11-02, "User Interface": a first pass at a GW2-style HUD that keeps a DAoC feel -
## the client's fonts and stone, married with the modern layout). Options > INTERFACE > STYLE: CLASSIC / MODERN.
##   - bottom centre: the health orb, the endurance (left) and power (right) arcs over it, the experience arc under
##     it, your name and level; quickbars 1 and 2 either side of it; the target plate above it; your effects above
##     the right quickbar;
##   - top left: the party (click a member to target them);
##   - top centre: the compass strip (the classic window, kept);
##   - top right: the event tracker (EventTracker), the quest log under it;
##   - bottom right: the minimap (the zone's painted map around you, north up, the wheel zooms it, a click opens
##     the map) with the clock and the zone's name over it, and the window buttons under it.
## Everything is drawn in GameUI's layout units, so UI SCALE applies to it all. The classic status / target / mini
## group / time windows are hidden while it is on; the sheets, chat and the other windows are shared.

const ORB_R := 44.0
const ARC_R := 52.0
const ARC_W := 7.0
const MINI := 168.0
const PARTY_W := 190.0
const QUEST_W := 214.0
const RED := Color(0.78, 0.14, 0.12)
const RED_DARK := Color(0.28, 0.04, 0.04)
const GREEN := Color(0.35, 0.78, 0.3)
const YELLOW := Color(0.92, 0.78, 0.25)
const BLUE := Color(0.3, 0.55, 0.95)
const STONE := Color(0.09, 0.085, 0.08, 0.86)
const RIM := Color(0.62, 0.5, 0.28)
const RIM_HI := Color(0.86, 0.71, 0.38)

var ui: GameUI
var player: Node3D
var orb: Orb
var party: Party
var minimap: Minimap
var quests: QuestLog
var menu: Control
var _zone_label: Label
var _clock: Label


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	orb = Orb.new()
	orb.hud = self
	add_child(orb)
	party = Party.new()
	party.hud = self
	add_child(party)
	minimap = Minimap.new()
	minimap.hud = self
	add_child(minimap)
	quests = QuestLog.new()
	quests.hud = self
	add_child(quests)
	_zone_label = UiArt.label("", 9, UiArt.GOLD_HI)
	_zone_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	_zone_label.clip_text = true
	_zone_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_zone_label)
	_clock = UiArt.label("", 9, UiArt.CREAM)
	_clock.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_clock.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_clock)
	_build_menu()
	layout()


## The window buttons under the minimap: the six sheets, the journal, the map and the options.
func _build_menu() -> void:
	menu = Control.new()
	menu.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(menu)
	var items := [["CHAR", func(): ui.show_sheet("character")], ["INV", func(): ui.show_sheet("inventory")],
			["SKILLS", func(): ui.show_sheet("skills")], ["STYLES", func(): ui.show_sheet("combat")],
			["SPELLS", func(): ui.show_sheet("magic")], ["GROUP", func(): ui.show_sheet("group")],
			["QUESTS", func(): ui.journal.toggle_window()], ["MAP", func():
				ui.map_window.player = ui.player
				ui.map_window.toggle_window()],
			["OPTIONS", func(): ui.options.toggle_window()]]
	var bw := floorf((MINI - 2 * 3) / 3.0)
	for i in items.size():
		var b := UiArt.button(items[i][0], Vector2(bw, 14), 7)
		b.position = Vector2((i % 3) * (bw + 3), (i / 3) * 17)
		b.pressed.connect(items[i][1])
		menu.add_child(b)
	menu.size = Vector2(MINI, 3 * 17)


## Places everything for the screen size (GameUI._rescale) and parks the classic windows the modern HUD replaces.
func layout() -> void:
	if ui == null:
		return
	var a: Vector2 = ui.area()
	var cx := a.x * 0.5
	var bottom := a.y - 8.0
	orb.position = Vector2(cx - ARC_R - 4, bottom - 2 * ARC_R - 30)
	orb.size = Vector2(2 * ARC_R + 8, 2 * ARC_R + 30)
	party.position = Vector2(8, 8)
	party.size = Vector2(PARTY_W, 8 * 24 + 4)
	minimap.position = Vector2(a.x - MINI - 8, a.y - MINI - 8 - menu.size.y - 4)
	minimap.size = Vector2(MINI, MINI)
	menu.position = Vector2(a.x - MINI - 8, a.y - menu.size.y - 6)
	_zone_label.position = Vector2(minimap.position.x, minimap.position.y - 13)
	_zone_label.size = Vector2(MINI - 44, 12)
	_clock.position = Vector2(minimap.position.x + MINI - 44, minimap.position.y - 13)
	_clock.size = Vector2(44, 12)
	# the quickbars either side of the orb, the compass top centre, the effects over the right bar
	if ui.quickbars.size() >= 2:
		var q1: Quickbar = ui.quickbars[0]
		var q2: Quickbar = ui.quickbars[1]
		for q in [q1, q2]:
			if q.vertical:
				q.set_vertical(false)
			q.visible = true
		q1.position = Vector2(cx - ARC_R - 12 - q1.size.x, bottom - q1.size.y)
		q2.position = Vector2(cx + ARC_R + 12, bottom - q2.size.y)
		var fx_y := q2.position.y - 50
		if ui.quickbars.size() >= 3 and ui.quickbars[2].visible and not ui.quickbars[2].vertical:
			var q3: Quickbar = ui.quickbars[2]             # a third bar lying flat: stacked over the right one
			q3.position = Vector2(q2.position.x, q2.position.y - q3.size.y - 4)
			fx_y = q3.position.y - 50
		if ui._effects_bar:
			ui._effects_bar.position = Vector2(q2.position.x, fx_y)
	if ui.windows.has("compass"):
		var comp: Control = ui.windows["compass"]
		comp.position = Vector2(cx - comp.size.x * 0.5, 4)
	if ui.event_tracker:
		ui.event_tracker.position = Vector2(a.x - QUEST_W - 8.0, 46.0)
	quests.position = Vector2(a.x - QUEST_W - 8.0, 46.0)
	quests.size = Vector2(QUEST_W, 200)
	for id in ["status", "target", "minigroup", "time"]:
		if ui.windows.has(id):
			ui.windows[id].visible = false


func _process(_delta: float) -> void:
	if not visible:
		return
	if Engine.get_process_frames() % 4 == 0:
		orb.queue_redraw()
		minimap.queue_redraw()
	if Engine.get_process_frames() % 10 == 0:
		party.queue_redraw()
		quests.queue_redraw()
		if ui.map_window:
			_zone_label.text = String(ui.map_window._zone(ui.map_window.current_zone).get("name", "")).to_upper()
		if ui.sky and ui.sky.has_method("clock_text"):
			_clock.text = String(ui.sky.clock_text()).to_upper()
		else:
			var t := Time.get_time_dict_from_system()
			_clock.text = "%02d:%02d" % [t.hour, t.minute]
	if ui.event_tracker:                                   # the quest log sits under the tracker's own height
		var h: float = ui.event_tracker.content_height()
		quests.position.y = 46.0 + (h + 8.0 if h > 0.0 else 0.0)


## A piece of the HUD: outlined text and stone plates, as every part draws them.
class Part extends Control:
	var hud: Control

	func text(f: Font, at: Vector2, s: String, fs: int, col: Color, align := HORIZONTAL_ALIGNMENT_LEFT, w := -1.0) -> void:
		draw_string_outline(f, at, s, align, w, fs, 2, Color(0, 0, 0, 0.85))
		draw_string(f, at, s, align, w, fs, col)

	func plate(r: Rect2) -> void:
		draw_rect(r, STONE)
		draw_rect(r, RIM, false, 1.0)


## The health orb with its arcs, the target plate above, the name and level under.
class Orb extends Part:

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		tooltip_text = ""

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			if _target_rect().has_point(event.position) and not PlayerData.target.is_empty():
				PlayerData.attack_toggle_requested.emit()       # the target plate: attack mode on / off
				accept_event()

	func _centre() -> Vector2:
		return Vector2(ARC_R + 4, ARC_R + 2)

	func _target_rect() -> Rect2:
		return Rect2(-70, -34, 2 * ARC_R + 8 + 140, 30)

	func _draw() -> void:
		var f := UiArt.font(true)
		var thin := UiArt.font(false)
		var c := _centre()
		var hp := clampf(PlayerData.health, 0.0, 1.0)
		var en := clampf(PlayerData.endurance, 0.0, 1.0)
		var pw := clampf(PlayerData.power, 0.0, 1.0)
		var xp := clampf(PlayerData.exp_frac, 0.0, 1.0)
		# the arcs: tracks, then endurance up the left and power up the right, the experience along the bottom
		draw_arc(c, ARC_R, deg_to_rad(180), deg_to_rad(270), 32, Color(0, 0, 0, 0.7), ARC_W + 2.0, true)
		draw_arc(c, ARC_R, deg_to_rad(270), deg_to_rad(360), 32, Color(0, 0, 0, 0.7), ARC_W + 2.0, true)
		draw_arc(c, ARC_R, deg_to_rad(180), deg_to_rad(270), 32, GREEN.darkened(0.7), ARC_W, true)
		draw_arc(c, ARC_R, deg_to_rad(270), deg_to_rad(360), 32, YELLOW.darkened(0.7), ARC_W, true)
		if en > 0.005:
			draw_arc(c, ARC_R, deg_to_rad(180), deg_to_rad(180 + 90 * en), 32, GREEN, ARC_W, true)
		if pw > 0.005:
			draw_arc(c, ARC_R, deg_to_rad(360 - 90 * pw), deg_to_rad(360), 32, YELLOW, ARC_W, true)
		draw_arc(c, ARC_R, deg_to_rad(45), deg_to_rad(135), 40, Color(0, 0, 0, 0.7), 4.0, true)
		draw_arc(c, ARC_R, deg_to_rad(45), deg_to_rad(135), 40, BLUE.darkened(0.65), 3.0, true)
		if xp > 0.005:                                        # the experience, from the left round the bottom
			draw_arc(c, ARC_R, deg_to_rad(135 - 90 * xp), deg_to_rad(135), 40, BLUE, 3.0, true)
		# the orb: a dark glass ball filled with red up to the health level, a rim of the client's gold
		draw_circle(c, ORB_R + 2.5, Color(0, 0, 0, 0.9))
		draw_circle(c, ORB_R, RED_DARK)
		if hp > 0.002:
			var top := c.y + ORB_R - 2.0 * ORB_R * hp        # the chord's height
			var n := 48
			# the arc on the right from the bottom up to the level, across the chord, and down the left
			var right := PackedVector2Array()
			var left := PackedVector2Array()
			for i in n + 1:
				var ang := deg_to_rad(90.0) - deg_to_rad(180.0) * i / n
				var p := c + Vector2(cos(ang), sin(ang)) * ORB_R
				if p.y >= top:
					right.append(p)
					left.append(Vector2(2 * c.x - p.x, p.y))
			if right.size() >= 2:
				var poly := PackedVector2Array()
				poly.append_array(right)
				var half := sqrt(maxf(0.0, ORB_R * ORB_R - (top - c.y) * (top - c.y)))
				poly.append(Vector2(c.x + half, top))
				poly.append(Vector2(c.x - half, top))
				left.reverse()
				poly.append_array(left)
				draw_colored_polygon(poly, RED)
				draw_line(Vector2(c.x - half, top), Vector2(c.x + half, top), RED.lightened(0.35), 1.5, true)
		# the glass: a highlight at the top left, a shadow at the bottom
		draw_circle(c + Vector2(-ORB_R * 0.35, -ORB_R * 0.4), ORB_R * 0.28, Color(1, 1, 1, 0.08))
		draw_arc(c, ORB_R - 1.5, deg_to_rad(20), deg_to_rad(160), 24, Color(0, 0, 0, 0.35), 3.0, true)
		draw_arc(c, ORB_R, 0, TAU, 64, RIM, 2.0, true)
		draw_arc(c, ORB_R + 1.5, 0, TAU, 64, RIM_HI, 1.0, true)
		# the numbers
		var hp_txt := "%d" % PlayerData.hp if PlayerData.max_hp > 1 else "%d%%" % roundi(hp * 100)
		text(f, Vector2(c.x - ORB_R, c.y + 4), hp_txt, 14, UiArt.CREAM, HORIZONTAL_ALIGNMENT_CENTER, 2 * ORB_R)
		text(thin, Vector2(c.x - ORB_R, c.y + 17), "%d%%" % roundi(hp * 100), 8, UiArt.CREAM, HORIZONTAL_ALIGNMENT_CENTER, 2 * ORB_R)
		var endt := "%d" % PlayerData.end_pts
		var powt := "%d" % PlayerData.power_pts if PlayerData.max_power > 0 else "-"
		text(thin, Vector2(c.x - ARC_R - 2, c.y - ARC_R - 2), endt, 7, GREEN, HORIZONTAL_ALIGNMENT_LEFT)
		text(thin, Vector2(c.x + ARC_R - 14, c.y - ARC_R - 2), powt, 7, YELLOW, HORIZONTAL_ALIGNMENT_RIGHT, 16)
		# the name plate under the orb
		var who := "%s  L%d" % [PlayerData.display_name().to_upper(), PlayerData.level]
		var tw := f.get_string_size(who, HORIZONTAL_ALIGNMENT_LEFT, -1, 9).x
		var np := Rect2(c.x - tw * 0.5 - 8, c.y + ARC_R + 6, tw + 16, 14)
		plate(np)
		text(f, Vector2(np.position.x + 8, np.position.y + 10.5), who, 9, UiArt.GOLD_HI)
		# the target plate above: name in its con colour, its health
		var t := PlayerData.target
		if not t.is_empty():
			var tr := _target_rect()
			plate(tr)
			var hpf := clampf(float(t.get("health", 1.0)), 0.0, 1.0)
			var bar := Rect2(tr.position.x + 6, tr.position.y + 17, tr.size.x - 12, 8)
			draw_rect(bar, Color(0.05, 0.02, 0.02, 0.95))
			draw_rect(Rect2(bar.position, Vector2(bar.size.x * hpf, bar.size.y)), RED)
			draw_rect(bar, RIM.darkened(0.3), false, 1.0)
			text(f, Vector2(tr.position.x + 6, tr.position.y + 12), String(t.get("name", "")).to_upper(), 9, t.get("con_color", UiArt.CREAM), HORIZONTAL_ALIGNMENT_LEFT, tr.size.x - 40)
			text(thin, Vector2(tr.position.x + tr.size.x - 34, tr.position.y + 12), "%d%%" % roundi(hpf * 100), 8, UiArt.CREAM, HORIZONTAL_ALIGNMENT_RIGHT, 28)


## The party, top left: a row per member - name, level and class, health bar with the power bar under it.
class Party extends Part:
	const ROW := 24.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			var rows: Array = PlayerData.group_rows()
			var i := int(event.position.y / ROW)
			if i >= 0 and i < rows.size() and not bool(rows[i].get("me", false)):
				PlayerData.member_clicked.emit(rows[i])
				accept_event()

	func _draw() -> void:
		var rows: Array = PlayerData.group_rows()
		if rows.is_empty():
			mouse_filter = Control.MOUSE_FILTER_IGNORE
			return
		mouse_filter = Control.MOUSE_FILTER_STOP
		var f := UiArt.font(true)
		var thin := UiArt.font(false)
		for i in rows.size():
			var m: Dictionary = rows[i]
			var y := i * ROW
			var r := Rect2(0, y, PARTY_W, ROW - 2)
			plate(r)
			var who := String(m.get("name", "")).to_upper()
			var tag := "L%d %s" % [int(m.get("level", 0)), String(m.get("class_name", "")).to_upper()]
			text(f, Vector2(6, y + 10), who, 8, UiArt.GOLD_HI if bool(m.get("me", false)) else UiArt.CREAM)
			text(thin, Vector2(PARTY_W - 6 - 90, y + 10), tag, 7, UiArt.DIM, HORIZONTAL_ALIGNMENT_RIGHT, 90)
			var hb := Rect2(6, y + 13, PARTY_W - 12, 5)
			draw_rect(hb, RED_DARK)
			draw_rect(Rect2(hb.position, Vector2(hb.size.x * clampf(float(m.get("hp", 0.0)), 0.0, 1.0), hb.size.y)), RED)
			var pb := Rect2(6, y + 19, PARTY_W - 12, 2)
			draw_rect(pb, YELLOW.darkened(0.75))
			draw_rect(Rect2(pb.position, Vector2(pb.size.x * clampf(float(m.get("power", 0.0)), 0.0, 1.0), pb.size.y)), YELLOW)


## The quest log under the event tracker: each quest's name and its current objective.
class QuestLog extends Part:

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	## [[title, objective], ...] for up to six quests.
	func entries() -> Array:
		var out: Array = []
		if Server.active:
			var ids := Server.quests.keys()
			ids.sort()
			for i in ids:
				var q: Dictionary = Server.quests[i]
				var obj := ""
				for g in q.get("goals", []):
					if not bool(g.get("done", false)):
						obj = String(g.get("text", ""))
						break
				if obj == "":
					obj = String(q.get("text", "")).split("\n")[0]
				out.append([JournalWindow.LEVEL_TAIL.sub(String(q.get("name", "")), ""), obj])
		else:
			for id in PlayerData.quests.keys():
				var q := QuestDb.quest(String(id))
				var steps: Array = q.get("steps", [])
				var n := int(PlayerData.quests[id].get("step", 1))
				var st: Dictionary = steps[n - 1] if n >= 1 and n <= steps.size() else {}
				out.append([String(q.get("name", id)), String(st.get("text", ""))])
		return out.slice(0, 6)

	func _draw() -> void:
		var list := entries()
		if list.is_empty():
			return
		var f := UiArt.font(true)
		var thin := UiArt.font(false)
		var y := 4.0
		var h := 16.0
		for e in list:
			h += 13.0 + (12.0 if String(e[1]) != "" else 0.0) + 3.0
		draw_rect(Rect2(0, 0, QUEST_W, h), Color(0.02, 0.02, 0.03, 0.62))
		draw_rect(Rect2(0, 0, QUEST_W, h), Color(0.55, 0.45, 0.25, 0.7), false, 1.0)
		text(f, Vector2(8, y + 10), "QUESTS", 8, UiArt.DIM)
		y += 16.0
		for e in list:
			text(f, Vector2(8, y + 10), _fit(f, String(e[0]).to_upper(), 9, QUEST_W - 16), 9, UiArt.GOLD_HI)
			y += 13.0
			if String(e[1]) != "":
				text(thin, Vector2(14, y + 9), _fit(thin, String(e[1]), 8, QUEST_W - 22), 8, UiArt.CREAM)
				y += 12.0
			y += 3.0

	static func _fit(f: Font, s: String, fs: int, w: float) -> String:
		if f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x <= w:
			return s
		while s.length() > 3 and f.get_string_size(s + "...", HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > w:
			s = s.substr(0, s.length() - 1)
		return s + "..."


## The minimap: the zone's painted map around you, north up. The wheel zooms (a fifth to the whole zone across), a
## click opens the map window. Quest marks, events, your realm's bots and companions as on the map.
class Minimap extends Part:
	var span := 0.22                                      # the share of the zone map across the minimap

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		clip_contents = true
		tooltip_text = "THE MAP (M); THE WHEEL ZOOMS"

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed:
			if event.button_index == MOUSE_BUTTON_WHEEL_UP:
				span = maxf(0.06, span / 1.25)
				accept_event()
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				span = minf(1.0, span * 1.25)
				accept_event()
			elif event.button_index == MOUSE_BUTTON_LEFT and hud.ui.map_window:
				hud.ui.map_window.player = hud.ui.player
				hud.ui.map_window.toggle_window()
				accept_event()

	func _draw() -> void:
		var w: MapWindow = hud.ui.map_window if hud.ui else null
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.02, 0.02, 0.03, 0.9))
		if w == null or w.current_zone < 0 or w.player == null:
			draw_rect(Rect2(Vector2.ZERO, size), RIM, false, 1.5)
			return
		var z := w.current_zone
		var u := w._player_units()
		var i := w._area_at(z, u)
		var mr := w.map_rect(z)
		var pic := ""
		var frac := Vector2.ZERO                           # your spot, as a fraction of the shown picture
		var to_frac: Callable
		if i >= 0:                                         # inside an area (a town, a dungeon wing): its map
			var a: Dictionary = (w._zone(z).areas as Array)[i]
			pic = String(a.get("map", ""))
			var r: Array = a.rect
			to_frac = func(uu: Vector2) -> Vector2:
				return (uu - mr.position - Vector2(float(r[0]), float(r[1]))) / Vector2(float(r[2]), float(r[3]))
		else:
			pic = String(w._zone(z).get("map", ""))
			to_frac = func(uu: Vector2) -> Vector2:
				return (uu - mr.position) / mr.size
		frac = to_frac.call(Vector2(u.x, u.y))
		var tex: Texture2D = w._texture(pic)
		var k := size.x / span                             # the picture's size on screen
		var origin := size * 0.5 - frac * k
		if tex:
			draw_texture_rect(tex, Rect2(origin, Vector2(k, k)), false)
		var at := func(uu: Vector2) -> Vector2:
			return origin + (to_frac.call(uu) as Vector2) * k
		var inside := func(p: Vector2) -> bool:
			return Rect2(Vector2.ZERO, size).has_point(p)
		for m in w.zone_quest_marks(z):
			var mp: Vector2 = at.call((m.at as Vector2) / 0.025)
			if not inside.call(mp):
				continue
			var col: Color = {"!": Color(1.0, 0.85, 0.15), "?": Color(0.3, 1.0, 0.35), "o": Color(1.0, 0.55, 0.1),
					"task": Color(0.8, 0.35, 1.0), "event": Color(0.35, 0.85, 1.0)}.get(String(m.kind), Color(0.95, 0.2, 0.15))
			draw_circle(mp, 3.5, Color(0.08, 0.05, 0.0))
			draw_circle(mp, 2.5, col)
		for b in WorldLink.bot_dots():
			var bp: Vector2 = at.call(Vector2(b.x, b.z) / 0.025)
			if inside.call(bp):
				draw_circle(bp, 2.6, Color(0.02, 0.08, 0.02))
				draw_circle(bp, 1.8, Color(0.3, 0.95, 0.3))
		for cpn in WorldLink.companion_dots():
			var cp: Vector2 = at.call(Vector2(cpn.x, cpn.z) / 0.025)
			if inside.call(cp):
				draw_circle(cp, 3.0, Color(0.0, 0.03, 0.1))
				draw_circle(cp, 2.2, Color8(70, 150, 255))
		for e in preload("res://game/ui/event_tracker.gd").in_zone(z):
			var ep: Vector2 = at.call(Vector2(float(e.x), float(e.y)) / 0.025)
			var st := String(e.get("state", "active"))
			var col := Color(1.0, 0.55, 0.1) if st in ["active", "next"] else (Color(0.4, 0.95, 0.35) if st == "success"
					else (Color(0.95, 0.85, 0.45) if st == "dormant" else (Color(0.35, 0.85, 1.0) if st == "giver" else Color(0.95, 0.3, 0.25))))
			var rad := maxf(5.0, float(e.get("r", 60.0)) / 0.025 / mr.size.x * k)
			if st == "giver":
				rad = 4.0
			if ep.distance_to(size * 0.5) > size.x + rad:
				continue
			draw_circle(ep, rad, Color(col.r, col.g, col.b, 0.16))
			draw_arc(ep, rad, 0.0, TAU, 32, Color(col.r, col.g, col.b, 0.9), 1.5)
			if inside.call(ep):
				var pts := PackedVector2Array([ep + Vector2(0, -4), ep + Vector2(4, 0), ep + Vector2(0, 4), ep + Vector2(-4, 0)])
				draw_colored_polygon(pts, col)
		# you, in the middle
		var p := w.player as Player
		var c := size * 0.5
		if p:
			var fwd := Vector2(-sin(p.char_yaw), -cos(p.char_yaw))
			var side := Vector2(-fwd.y, fwd.x)
			var pts := PackedVector2Array([c + fwd * 7.0, c - fwd * 4.0 + side * 4.5, c - fwd * 2.0, c - fwd * 4.0 - side * 4.5])
			draw_colored_polygon(pts, Color(1.0, 0.85, 0.25))
			draw_polyline(PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]]), Color(0.1, 0.05, 0.0), 1.0)
		draw_rect(Rect2(Vector2.ZERO, size), RIM, false, 1.5)
		text(UiArt.font(true), Vector2(size.x * 0.5 - 10, 10), "N", 8, UiArt.GOLD_HI, HORIZONTAL_ALIGNMENT_CENTER, 20)
