extends Control
## The modern interface (owner 2026-11-02, "User Interface": a first pass at a GW2-style HUD that keeps a DAoC feel -
## the client's fonts and stone, married with the modern layout). Options > INTERFACE > STYLE: CLASSIC / MODERN.
##   - bottom centre: the health orb, the endurance (left) and power (right) arcs over it, the experience arc under
##     it, your name and level; quickbars 1 and 2 either side of it; the target plate above it; your effects above
##     the right quickbar;
##   - top left: the menu bar (owner 2026-11-02: "the 6 orbs ... a transparent one locked to the top left of the screen
##     like GW2"): the sheets' orbs from control.bmp, then bags, quests, map and options; the party under it;
##   - top centre: the compass strip (the classic window, kept);
##   - top right: the event tracker (EventTracker), the quest log under it;
##   - bottom right: the minimap (the zone's painted map around you, north up, the wheel zooms it, a click opens
##     the map) with the clock and the zone's name over it.
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
var loot: LootFeed
var pet: PetPanel
var burden: Burden
var menu: Control
var _zone_label: Label
var _clock: Label
var mini := MINI                                         # the minimap's side (its corner grip; [modern_zoom] minimap)
## Pieces moved by EDIT UI (owner 2026-11-04: "make sure every new UI element is movable"): id -> its place as a share
## of the room the screen leaves it (0,0 top left .. 1,1 bottom right), so it keeps its corner at any size or UI scale.
## Kept in settings.cfg [modern_layout]; a piece not listed sits where layout() puts it.
var custom := {}
const LAYOUT_SECTION := "modern_layout"
## The controller's layout (owner 2026-11-10: the controller bar "overlapping ... the buffs, the target health ... Maybe
## they can be moved to different locations in the controller UI"): while the pad's bar is up the HUD has a layout of
## its own - the bar's two halves where the quickbars were, your effects and the pet window moved up out of their way,
## every piece movable by EDIT UI and kept apart from the mouse layout ([modern_layout_pad]).
const PAD_SECTION := "modern_layout_pad"
var pad_mode := false


func _section() -> String:
	return PAD_SECTION if pad_mode else LAYOUT_SECTION


func _load_custom() -> void:
	custom.clear()
	var cfg := ConfigFile.new()
	cfg.load(UiArt.settings_path)
	if cfg.has_section(_section()):
		for k in cfg.get_section_keys(_section()):
			var v = cfg.get_value(_section(), k)
			if v is Vector2:
				custom[k] = v


## The pad's bar came up / went away (PadBar): the matching layout.
func set_pad_mode(on: bool) -> void:
	if on == pad_mode:
		return
	pad_mode = on
	_load_custom()
	layout()


func _pad_bar():
	return Pad.bar if Pad.bar and is_instance_valid(Pad.bar) else null


func _ready() -> void:
	var cfg := ConfigFile.new()
	cfg.load(UiArt.settings_path)
	mini = clampf(float(cfg.get_value("modern_zoom", "minimap", MINI)), 110.0, 380.0)
	_load_custom()
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
	loot = LootFeed.new()
	loot.hud = self
	add_child(loot)
	pet = PetPanel.new()
	pet.hud = self
	add_child(pet)
	burden = Burden.new()
	burden.hud = self
	add_child(burden)
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


## The menu bar, top left.
func _build_menu() -> void:
	menu = HudMenu.new()
	menu.hud = self
	add_child(menu)


## Places everything for the screen size (GameUI._rescale) and parks the classic windows the modern HUD replaces.
func layout() -> void:
	if ui == null:
		return
	var a: Vector2 = ui.area()
	var cx := a.x * 0.5
	var bottom := a.y - 8.0
	orb.position = Vector2(cx - ARC_R - 4, bottom - 2 * ARC_R - 30)
	orb.size = Vector2(2 * ARC_R + 8, 2 * ARC_R + 30)
	menu.position = Vector2(6, 4)
	menu.size = Vector2(HudMenu.ITEMS.size() * (HudMenu.ICON + HudMenu.GAP), HudMenu.ICON)
	party.position = Vector2(8, menu.position.y + HudMenu.ICON + 8)
	party.size = Vector2(PARTY_W, 8 * 24 + 4)
	minimap.position = Vector2(a.x - mini - 8, a.y - mini - 8)
	minimap.size = Vector2(mini, mini)
	loot.size = Vector2(LootFeed.W, LootFeed.ROW * LootFeed.MAX_ROWS)
	loot.position = Vector2(a.x - LootFeed.W - 8, minimap.position.y - 22 - loot.size.y)
	# the quickbars either side of the orb, the compass top centre, the effects over the right bar
	var pb = _pad_bar()
	if pad_mode and pb:
		# the controller's layout: the bar's halves either side of the orb, your effects over the right one (clear of
		# the target plate), the pet window over the left one
		pb.place_default()
		var r: Control = pb.right
		var l: Control = pb.left
		if ui._effects_bar:
			ui._effects_bar.position = Vector2(cx + 135.0, r.position.y - 44.0)
		pet.size = Vector2(PetPanel.W, PetPanel.MAX_H)
		pet.position = Vector2(maxf(8.0, cx - 135.0 - PetPanel.W), l.position.y - 12.0 - PetPanel.MAX_H)
	elif ui.quickbars.size() >= 2:
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
		pet.size = Vector2(PetPanel.W, PetPanel.MAX_H)
		pet.position = Vector2(maxf(8.0, q1.position.x + q1.size.x - PetPanel.W), q1.position.y - 12.0 - PetPanel.MAX_H)
	if ui.windows.has("compass"):
		var comp: Control = ui.windows["compass"]
		comp.position = Vector2(cx - comp.size.x * 0.5, 4)
	if ui.event_tracker:
		ui.event_tracker.position = Vector2(a.x - QUEST_W - 8.0, 46.0)
	quests.position = Vector2(a.x - QUEST_W - 8.0, 46.0)
	quests.size = Vector2(QUEST_W, 200)
	for id in ["status", "target", "minigroup", "time", "minipet"]:
		if ui.windows.has(id):
			ui.windows[id].visible = false
	# what EDIT UI moved goes where it was put
	for e in movable():
		var c: Control = e[2]
		if custom.has(String(e[0])) and c:
			var room := (a - c.size).max(Vector2.ONE)
			c.position = ((custom[String(e[0])] as Vector2) * room).round()
	_zone_label.position = Vector2(minimap.position.x, minimap.position.y - 13)
	_zone_label.size = Vector2(mini - 44, 12)
	_clock.position = Vector2(minimap.position.x + mini - 44, minimap.position.y - 13)
	_clock.size = Vector2(44, 12)
	var bx := minimap.position.x - Burden.W - 6
	if bx < 4.0:
		bx = minimap.position.x + minimap.size.x + 6         # (a minimap moved to the left edge: the bag on its right)
	burden.position = Vector2(bx, minimap.position.y + minimap.size.y - Burden.H)


## Every piece EDIT UI can move: [id, name, Control].
func movable() -> Array:
	var out: Array = [["orb", "HEALTH ORB AND TARGET", orb], ["menu", "MENU BAR", menu], ["party", "PARTY", party],
			["minimap", "MINIMAP", minimap], ["quests", "QUEST LOG", quests], ["loot", "LOOT FEED", loot],
			["pet", "PET WINDOW", pet]]
	if ui == null:
		return out
	if ui.event_tracker:
		out.append(["events", "EVENT TRACKER", ui.event_tracker])
	var pb = _pad_bar()
	if pad_mode and pb:
		out.append(["pad_left", "CONTROLLER: D-PAD", pb.left])
		out.append(["pad_right", "CONTROLLER: BUTTONS", pb.right])
	else:
		for i in ui.quickbars.size():
			if i < 3 and ui.quickbars[i].visible:
				out.append(["bar%d" % (i + 1), "QUICKBAR %d" % (i + 1), ui.quickbars[i]])
	if ui._effects_bar:
		out.append(["effects", "YOUR EFFECTS", ui._effects_bar])
	if ui.windows.has("compass"):
		out.append(["compass", "COMPASS", ui.windows["compass"]])
	return out


## EDIT UI let go of a piece: its place kept.
func keep_place(id: String, c: Control) -> void:
	var room := (ui.area() - c.size).max(Vector2.ONE)
	custom[id] = (c.position / room).clamp(Vector2.ZERO, Vector2.ONE)
	_save_custom()
	layout()


func reset_places() -> void:
	custom.clear()
	_save_custom()
	layout()


func _save_custom() -> void:
	var cfg := ConfigFile.new()
	cfg.load(UiArt.settings_path)
	if cfg.has_section(_section()):
		cfg.erase_section(_section())
	for k in custom:
		cfg.set_value(_section(), k, custom[k])
	cfg.save(UiArt.settings_path)


func _process(_delta: float) -> void:
	if not visible:
		return
	if Engine.get_process_frames() % 4 == 0:
		orb.queue_redraw()
		minimap.queue_redraw()
	if Engine.get_process_frames() % 10 == 0:
		burden.refresh()
		party.queue_redraw()
		pet.queue_redraw()
		menu.queue_redraw()
		quests.queue_redraw()
		if ui.map_window:
			_zone_label.text = String(ui.map_window._zone(ui.map_window.current_zone).get("name", "")).to_upper()
		if ui.sky and ui.sky.has_method("clock_text"):
			_clock.text = String(ui.sky.clock_text()).to_upper()
		else:
			var t := Time.get_time_dict_from_system()
			_clock.text = "%02d:%02d" % [t.hour, t.minute]
	if ui.event_tracker and not custom.has("quests"):    # the quest log sits under the tracker, at its own height
		var h: float = ui.event_tracker.content_height()
		quests.position = ui.event_tracker.position + Vector2(ui.event_tracker.size.x - QUEST_W, h + 8.0 if h > 0.0 else 0.0)


## A piece of the HUD: outlined text and stone plates, as every part draws them.
class Part extends Control:
	var hud: Control

	func text(f: Font, at: Vector2, s: String, fs: int, col: Color, align := HORIZONTAL_ALIGNMENT_LEFT, w := -1.0) -> void:
		draw_string_outline(f, at, s, align, w, fs, 2, Color(0, 0, 0, 0.85))
		draw_string(f, at, s, align, w, fs, col)

	func plate(r: Rect2) -> void:
		draw_rect(r, STONE)
		draw_rect(r, RIM, false, 1.0)


## Over your carrying capacity (owner 2026-11-12: "a red bag icon with a weight, near the map or bags, instead of the
## 'You are encumbered' chat spam"): what you carry / can carry, beside the minimap while it lasts.
class Burden extends Part:
	const W := 50.0
	const H := 44.0
	var now := -1
	var most := -1

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_PASS
		size = Vector2(W, H)
		visible = false

	## What you carry and can carry: the server's Encumberance packet, or the game's own sums offline.
	func refresh() -> void:
		var n := -1
		var m := -1
		if Server.weight_max >= 0:
			n = Server.weight_now
			m = Server.weight_max
		elif PlayerData.stats.size() >= 8:
			n = PlayerData.inventory_weight()
			m = maxi(int(PlayerData.effective_stats()[0]), int(PlayerData.stats[0]))
		var over := m > 0 and n > m
		if over != visible or n != now or m != most:
			now = n
			most = m
			visible = over
			tooltip_text = ("ENCUMBERED: YOU CARRY %d OF %d LBS AND MOVE MORE SLOWLY" % [n, m]) if over else ""
			queue_redraw()

	func _draw() -> void:
		if now < 0 or most <= 0:
			return
		var c := Vector2(W * 0.5, 17.0)
		var red := Color(0.86, 0.16, 0.12)
		# the sack: a round body, a gathered neck and its tie
		var body := PackedVector2Array()
		var rim := PackedVector2Array()
		for i in 24:
			var a := TAU * i / 24.0
			var p := Vector2(cos(a) * 12.0, sin(a) * 10.5)
			if p.y > 6.0:
				p.y = 6.0 + (p.y - 6.0) * 0.4                # a flatter bottom: it sits
			body.append(c + Vector2(0, 5) + p)
			rim.append(c + Vector2(0, 5) + p * 1.12)
		draw_colored_polygon(rim, Color(0.05, 0.02, 0.01))
		draw_colored_polygon(body, red)
		var neck := PackedVector2Array([c + Vector2(-5, -11), c + Vector2(5, -11), c + Vector2(3.5, -5), c + Vector2(-3.5, -5)])
		draw_colored_polygon(neck, red.darkened(0.15))
		draw_line(c + Vector2(-6, -5), c + Vector2(6, -5), Color(0.95, 0.8, 0.45), 2.0)
		draw_line(c + Vector2(-5, -11), c + Vector2(5, -11), Color(0.05, 0.02, 0.01), 1.5)
		text(UiArt.font(true), c + Vector2(-4, 9), "!", 12, UiArt.CREAM)
		text(UiArt.font(false), Vector2(0, H - 2), "%d/%d" % [now, most], 9, Color(1.0, 0.45, 0.4),
				HORIZONTAL_ALIGNMENT_CENTER, W)


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
		# your level, and in brackets the level you fight your target at while scaled down to it (LevelScaling:
		# owner 2026-11-03 "the effective level ... next to the actual level of the character in parenthesis")
		var who := "%s  L%d" % [PlayerData.display_name().to_upper(), PlayerData.level]
		var eff := Server.fight_level if Server.active else 0
		var scaled := "  (%d)" % eff if eff > 0 and eff < PlayerData.level else ""
		var tw := f.get_string_size(who, HORIZONTAL_ALIGNMENT_LEFT, -1, 9).x
		var sw := f.get_string_size(scaled, HORIZONTAL_ALIGNMENT_LEFT, -1, 9).x if scaled != "" else 0.0
		var np := Rect2(c.x - (tw + sw) * 0.5 - 8, c.y + ARC_R + 6, tw + sw + 16, 14)
		plate(np)
		text(f, Vector2(np.position.x + 8, np.position.y + 10.5), who, 9, UiArt.GOLD_HI)
		if scaled != "":
			text(f, Vector2(np.position.x + 8 + tw, np.position.y + 10.5), scaled, 9, Color(1.0, 0.6, 0.25))
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


## The party, top left: a row per member - name, level and class, health bar with the power bar under it. The member
## you have selected (your target) is framed; while you lead the group, its row shows KICK (owner 2026-11-11:
## "highlight the group member ... little buttons that appear that let you kick them if you're the group leader").
class Party extends Part:
	const ROW := 24.0
	const BTNS := [["KICK", "/disband %s"]]                  # (no LEAD: the bots can't lead a group)
	const BTN_W := 34.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		PlayerData.target_changed.connect(queue_redraw)

	## You lead your group (the server's group list: the leader first).
	static func leading() -> bool:
		var gm: Array = Server.group_members
		return not gm.is_empty() and int(gm[0].get("oid", 0)) == Server.me_oid

	static func selected(m: Dictionary) -> bool:
		return not bool(m.get("me", false)) and String(m.get("name", "")) != "" \
				and String(PlayerData.target.get("name", "")) == String(m.get("name", ""))

	func _btn_rect(row: int, k: int) -> Rect2:
		return Rect2(PARTY_W - 4 - (BTNS.size() - k) * (BTN_W + 2), row * ROW + 2, BTN_W, 10)

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			var rows: Array = PlayerData.group_rows()
			var i := int(event.position.y / ROW)
			if i >= 0 and i < rows.size() and not bool(rows[i].get("me", false)):
				if leading() and selected(rows[i]):
					for k in BTNS.size():
						if _btn_rect(i, k).has_point(event.position):
							Server.command(String(BTNS[k][1]) % String(rows[i].get("name", "")))
							accept_event()
							return
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
			var sel := selected(m)
			if sel:
				draw_rect(r.grow(-1), Color(RIM_HI, 0.18))
				draw_rect(r, RIM_HI, false, 2.0)
			var who := String(m.get("name", "")).to_upper()
			var tag := "L%d %s" % [int(m.get("level", 0)), String(m.get("class_name", "")).to_upper()]
			# their colour on the map beside the name (owner 2026-11-12): a triangle, your companion's a star
			if not bool(m.get("me", false)):
				var comp := String(PlayerData.get_meta("companion", "")) if PlayerData.has_meta("companion") else ""
				var mk := {"colour": preload("res://game/ui/group_marks.gd").row_colour(rows, i), "star": comp != "" and String(m.get("name", "")) == comp}
				preload("res://game/ui/group_marks.gd").draw_member(self, Vector2(10, y + 7), mk, 0.85)
			text(f, Vector2(18, y + 10), who, 8, UiArt.GOLD_HI if bool(m.get("me", false)) or sel else UiArt.CREAM, \
					HORIZONTAL_ALIGNMENT_LEFT, PARTY_W - 102 if sel else -1.0)
			if sel and leading():
				for k in BTNS.size():
					var br := _btn_rect(i, k)
					draw_rect(br, Color(0.35, 0.07, 0.05, 0.95) if k == 0 else Color(0.18, 0.14, 0.07, 0.95))
					draw_rect(br, RIM_HI, false, 1.0)
					text(thin, Vector2(br.position.x, br.position.y + 8), String(BTNS[k][0]), 7, UiArt.CREAM, HORIZONTAL_ALIGNMENT_CENTER, BTN_W)
			else:
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

	# the grip in its top left corner (it sits in the screen's bottom right): drag to make it bigger or smaller
	const GRIP := 12.0
	var _sizing := false
	var _from := Vector2.ZERO
	var _start := 0.0

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseMotion:
			mouse_default_cursor_shape = Control.CURSOR_FDIAGSIZE if _sizing or Rect2(0, 0, GRIP, GRIP).has_point(event.position) \
					else Control.CURSOR_ARROW
			if _sizing:
				var k: float = get_global_transform().get_scale().x
				var d := (get_global_mouse_position() - _from) / maxf(0.01, k)
				hud.mini = clampf(_start - maxf(d.x, d.y), 110.0, 380.0)
				hud.layout()
				accept_event()
			return
		if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed and Rect2(0, 0, GRIP, GRIP).has_point(event.position):
				_sizing = true
				_from = get_global_mouse_position()
				_start = hud.mini
				accept_event()
				return
			if not event.pressed and _sizing:
				_sizing = false
				var cfg := ConfigFile.new()
				cfg.load(UiArt.settings_path)
				cfg.set_value("modern_zoom", "minimap", hud.mini)
				cfg.save(UiArt.settings_path)
				accept_event()
				return
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

	static var _near := {}

	## The outdoor zones touching a zone in its region: [[zone, dx, dy, w, h]] in its map's units (region units from
	## its corner) - zones_index.json's 8192-unit blocks.
	static func _neighbours(z: int) -> Array:
		if _near.has(z):
			return _near[z]
		var out := []
		var me: Dictionary = Server.zone_info(z)
		if not me.is_empty():
			var mx := float(me.x)
			var my := float(me.y)
			for key in Server._index:
				var o: Dictionary = Server._index[key]
				if int(key) == z or int(o.get("region", -1)) != int(me.get("region", -2)) or int(o.get("type", 0)) != 0:
					continue
				var gap_x := maxf(float(o.x) - (mx + float(me.w)), mx - (float(o.x) + float(o.w)))
				var gap_y := maxf(float(o.y) - (my + float(me.h)), my - (float(o.y) + float(o.h)))
				if gap_x <= 0.5 and gap_y <= 0.5:                # touching, corners too
					out.append([int(key), (float(o.x) - mx) * 8192.0, (float(o.y) - my) * 8192.0, float(o.w) * 8192.0, float(o.h) * 8192.0])
		_near[z] = out
		return out

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
		var mix := MapWindow.render_mix(0.6 / span) if i < 0 else 0.0
		# the zones next to this one, around it (owner 2026-11-12: "stitch map together so that minimap doesn't show black
		# at the edge of the zones"): each where it lies in the region, its painted map (and its render close in)
		if i < 0 and not w._zone(z).has("map_rect"):
			for n in _neighbours(z):
				var nr := Rect2(origin + Vector2(n[1], n[2]) / mr.size.x * k, Vector2(n[3], n[4]) / mr.size.x * k)
				if not nr.intersects(Rect2(Vector2.ZERO, size)):
					continue
				var nt: Texture2D = w._texture(String(w._zone(int(n[0])).get("map", "")))
				if nt:
					draw_texture_rect(nt, nr, false)
				var nrt: Texture2D = w.render_texture(int(n[0])) if mix > 0.0 else null
				if nrt:
					draw_texture_rect(nrt, nr, false, Color(1, 1, 1, mix))
		if tex:
			draw_texture_rect(tex, Rect2(origin, Vector2(k, k)), false)
		# the zone drawn from above over it when close in (MapWindow.render_texture), the painted map when far out
		var rt: Texture2D = w.render_texture(z) if mix > 0.0 else null
		if rt:
			draw_texture_rect(rt, Rect2(origin, Vector2(k, k)), false, Color(1, 1, 1, mix))
			w.draw_render_labels(self, z, origin, k, size.x / 0.55, mix, Rect2(Vector2.ZERO, size))
		var at := func(uu: Vector2) -> Vector2:
			return origin + (to_frac.call(uu) as Vector2) * k
		var inside := func(p: Vector2) -> bool:
			return Rect2(Vector2.ZERO, size).has_point(p)
		var edges: Array = []                              # [place, colour, is an event] past the minimap's edge
		for m in w.zone_quest_marks(z):
			var mp: Vector2 = at.call((m.at as Vector2) / 0.025)
			var col: Color = {"!": Color(1.0, 0.85, 0.15), "?": Color(0.3, 1.0, 0.35), "o": Color(1.0, 0.55, 0.1),
					"task": Color(0.8, 0.35, 1.0), "event": Color(0.35, 0.85, 1.0)}.get(String(m.kind), Color(0.95, 0.2, 0.15))
			if not inside.call(mp):
				if String(m.kind) in ["?", "step", "task"]:   # your quests' goals and hand-ins (not every giver)
					edges.append([mp, col, false])
				continue
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
		# your group: a triangle each in its colour, your companion a star (GroupMarks)
		for gm in preload("res://game/ui/group_marks.gd").members(get_tree()):
			var gp: Vector2 = at.call(Vector2(gm.pos.x, gm.pos.z) / 0.025)
			if inside.call(gp):
				preload("res://game/ui/group_marks.gd").draw_member(self, gp, gm)
		# your companion's idea: its star in a ring (past the edge, a pointer to it)
		var cm := preload("res://game/ui/group_marks.gd").live_mark(z, w.player.global_position)
		if not cm.is_empty():
			var cmp: Vector2 = at.call(Vector2(cm.pos.x, cm.pos.z) / 0.025)
			if inside.call(cmp):
				preload("res://game/ui/group_marks.gd").draw_mark(self, cmp)
			else:
				edges.append([cmp, preload("res://game/ui/group_marks.gd").MARK_COLOUR, false])
		for e in preload("res://game/ui/event_tracker.gd").in_zone(z):
			var ep: Vector2 = at.call(Vector2(float(e.x), float(e.y)) / 0.025)
			var st := String(e.get("state", "active"))
			var col := Color(1.0, 0.55, 0.1) if st in ["active", "next"] else (Color(0.4, 0.95, 0.35) if st == "success"
					else (Color(0.95, 0.85, 0.45) if st == "dormant" else (Color(0.35, 0.85, 1.0) if st == "giver" else Color(0.95, 0.3, 0.25))))
			var rad := maxf(5.0, float(e.get("r", 60.0)) / 0.025 / mr.size.x * k)
			if st == "giver":
				rad = 4.0
			if not inside.call(ep) and st in ["active", "next", "giver"]:   # (a giver: one waiting for you to start it)
				edges.append([ep, col, true])
			if ep.distance_to(size * 0.5) > size.x + rad:
				continue
			draw_circle(ep, rad, Color(col.r, col.g, col.b, 0.16))
			draw_arc(ep, rad, 0.0, TAU, 32, Color(col.r, col.g, col.b, 0.9), 1.5)
			if inside.call(ep):
				var pts := PackedVector2Array([ep + Vector2(0, -4), ep + Vector2(4, 0), ep + Vector2(0, 4), ep + Vector2(-4, 0)])
				draw_colored_polygon(pts, col)
		_edge_marks(edges)
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
		for j in 3:                                        # the resize grip, top left
			var gk := 3.0 + j * 3.5
			draw_line(Vector2(1, gk), Vector2(gk, 1), Color(RIM_HI, 0.85), 1.2, true)
		text(UiArt.font(true), Vector2(size.x * 0.5 - 10, 10), "N", 8, UiArt.GOLD_HI, HORIZONTAL_ALIGNMENT_CENTER, 20)


	## What lies beyond the minimap at this zoom (owner 2026-11-04: "an icon or indicator ... that alerts you to where
	## an event is if you're not able to see it at your current zoom level ... Same with quest objectives"): a glowing
	## pointer pinned to the rim in its direction, until it comes into the minimap. Events are diamonds, quest goals dots.
	func _edge_marks(edges: Array) -> void:
		var c := size * 0.5
		var half := c - Vector2(10, 10)
		var pulse := 0.55 + 0.45 * sin(Time.get_ticks_msec() / 260.0)
		for e in edges:
			var d: Vector2 = (e[0] as Vector2) - c
			if d.length() < 0.001:
				continue
			var t := minf(half.x / maxf(absf(d.x), 0.001), half.y / maxf(absf(d.y), 0.001))
			var at: Vector2 = c + d * t
			var col: Color = e[1]
			var dir := d.normalized()
			var side := Vector2(-dir.y, dir.x)
			draw_circle(at, 11.0, Color(col.r, col.g, col.b, 0.2 * pulse))
			draw_circle(at, 7.5, Color(col.r, col.g, col.b, 0.3 * pulse))
			# the pointer: an arrowhead on the rim side, the mark itself inside it
			var tip := at + dir * 10.0
			draw_colored_polygon(PackedVector2Array([tip, at + dir * 4.0 + side * 5.0, at + dir * 4.0 - side * 5.0]), Color(0.08, 0.05, 0.0))
			draw_colored_polygon(PackedVector2Array([at + dir * 9.0, at + dir * 4.5 + side * 4.0, at + dir * 4.5 - side * 4.0]), col)
			if bool(e[2]):
				draw_colored_polygon(PackedVector2Array([at + Vector2(0, -5), at + Vector2(5, 0), at + Vector2(0, 5), at + Vector2(-5, 0)]), Color(0.08, 0.05, 0.0))
				draw_colored_polygon(PackedVector2Array([at + Vector2(0, -3.8), at + Vector2(3.8, 0), at + Vector2(0, 3.8), at + Vector2(-3.8, 0)]), col)
			else:
				draw_circle(at, 4.5, Color(0.08, 0.05, 0.0))
				draw_circle(at, 3.4, col)


## "#PET|oid,role,health,name|..." (HeroInfo.cs) -> Server.pet_retinue.
static func receive_pets(line: String) -> void:
	var out: Array = []
	for part in line.split("|", false):
		var f := part.split(",", true, 3)
		if f.size() == 4:
			out.append({"oid": int(f[0]), "role": f[1], "health": int(f[2]), "name": f[3]})
	Server.pet_retinue = out


## The pet window (owner 2026-11-04: "the new UI [doesn't have] a pet window element"): over the left quickbar - your
## pet's name, stance and health, its buffs, the commands as a row of plates (click; drag one onto a quickbar as on the
## classic window), and a commander's retinue under it - each retainer / minion with its role and health. Only while
## you have a pet; the classic pet window stays out of the way in this style.
class PetPanel extends Part:
	const W := 232.0
	const MAX_H := 150.0
	const CMDS := [["ATTACK", "attack"], ["FOLLOW", "follow"], ["STAY", "stay"], ["AGGR", "aggressive"],
			["DEF", "defensive"], ["PASS", "passive"], ["DISMISS", "release"]]
	const ROLE := {"healer": ["H", Color(0.4, 0.95, 0.45)], "melee": ["M", Color(0.95, 0.4, 0.3)],
			"caster": ["C", Color(0.45, 0.65, 1.0)], "debuffer": ["D", Color(0.8, 0.45, 1.0)],
			"archer": ["A", Color(0.95, 0.85, 0.3)], "buffer": ["B", Color(0.4, 0.9, 0.95)]}
	const BTN_Y := 30.0
	const BTN_H := 15.0
	var _hover := -1
	var _content_h := 0.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		clip_contents = false

	## Only the drawn part takes the mouse (nothing at all without a pet).
	func _has_point(p: Vector2) -> bool:
		return not PlayerData.pet.is_empty() and p.x >= 0 and p.x <= W and p.y >= 0 and p.y <= _content_h

	func _btn_rect(i: int) -> Rect2:
		var bw := (W - 8.0 - (CMDS.size() - 1) * 2.0) / CMDS.size()
		return Rect2(4 + i * (bw + 2.0), BTN_Y, bw, BTN_H)

	func _btn_at(p: Vector2) -> int:
		for i in CMDS.size():
			if _btn_rect(i).has_point(p):
				return i
		return -1

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseMotion:
			var h := _btn_at(event.position)
			if h != _hover:
				_hover = h
				queue_redraw()
		elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			var i := _btn_at(event.position)
			if i >= 0:
				PlayerData.pet_command(String(CMDS[i][1]))
				queue_redraw()
				accept_event()

	func _notification(what: int) -> void:
		if what == NOTIFICATION_MOUSE_EXIT and _hover != -1:
			_hover = -1
			queue_redraw()

	## A command dragged onto a quickbar: the slot gives it, as the classic window's buttons do.
	func _get_drag_data(at: Vector2) -> Variant:
		var i := _btn_at(at)
		if i < 0:
			return null
		var prev := UiArt.button(String(CMDS[i][0]), _btn_rect(i).size, 8)
		prev.modulate = Color(1, 1, 1, 0.8)
		set_drag_preview(prev)
		return {"kind": "petcmd", "id": String(CMDS[i][1]), "icon": -1, "name": "PET " + String(CMDS[i][1]).to_upper()}

	func _get_tooltip(at: Vector2) -> String:
		var i := _btn_at(at)
		return "" if i < 0 else "PET: %s (DRAG ONTO A QUICKBAR)" % String(CMDS[i][1]).to_upper()

	func _draw() -> void:
		var pd: Dictionary = PlayerData.pet
		if pd.is_empty():
			_content_h = 0.0
			return
		var f := UiArt.font(true)
		var thin := UiArt.font(false)
		var fx: Array = Server.pet_effects_list() if Server.active else []
		var subs: Array = Server.pet_retinue if Server.active else []
		var h := BTN_Y + BTN_H + 4.0 + (17.0 if not fx.is_empty() else 0.0) + (subs.size() * 15.0 + 4.0 if not subs.is_empty() else 0.0)
		_content_h = h
		draw_rect(Rect2(0, 0, W, h), Color(0.02, 0.02, 0.03, 0.66))
		draw_rect(Rect2(0, 0, W, h), Color(0.55, 0.45, 0.25, 0.75), false, 1.0)
		var mode := String(pd.get("mode", "defensive"))
		text(f, Vector2(6, 12), QuestLog._fit(f, String(pd.get("name", "")).to_upper(), 9, W - 90), 9, UiArt.GOLD_HI)
		text(thin, Vector2(W - 86, 12), mode.to_upper(), 7, UiArt.DIM, HORIZONTAL_ALIGNMENT_RIGHT, 80)
		var hp := clampf(float(pd.get("health", 1.0)), 0.0, 1.0)
		var hb := Rect2(6, 17, W - 12, 7)
		draw_rect(hb, RED_DARK)
		draw_rect(Rect2(hb.position, Vector2(hb.size.x * hp, hb.size.y)), RED)
		draw_rect(hb, Color(0, 0, 0, 0.6), false, 1.0)
		text(thin, Vector2(hb.position.x, hb.position.y + 6.5), "%d%%" % roundi(hp * 100.0), 6, UiArt.CREAM, HORIZONTAL_ALIGNMENT_CENTER, hb.size.x)
		for i in CMDS.size():
			var r := _btn_rect(i)
			var on := String(CMDS[i][1]) == mode
			draw_rect(r, Color(0.16, 0.13, 0.09, 0.95) if i == _hover else STONE)
			draw_rect(r, RIM_HI if on or i == _hover else RIM, false, 1.0)
			text(f, Vector2(r.position.x, r.position.y + 10.5), String(CMDS[i][0]), 7, UiArt.GOLD_HI if on else UiArt.CREAM,
					HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		var y := BTN_Y + BTN_H + 4.0
		if not fx.is_empty():
			var x := 6.0
			for e in fx.slice(0, 12):
				var tex: Texture2D = ItemDb.icon(int(e.icon))
				if tex:
					draw_texture_rect(tex, Rect2(x, y, 14, 14), false)
				draw_rect(Rect2(x, y, 14, 14), Color(0, 0, 0, 0.7), false, 1.0)
				x += 16.0
			y += 17.0
		if not subs.is_empty():
			draw_line(Vector2(6, y), Vector2(W - 6, y), Color(0.55, 0.45, 0.25, 0.45), 1.0)
			y += 3.0
			for sp in subs:
				var role: Array = ROLE.get(String(sp.role), ["?", UiArt.CREAM])
				var dead := int(sp.health) < 0
				var c := Vector2(13, y + 6.5)
				draw_circle(c, 6.0, Color(0, 0, 0, 0.7))
				draw_arc(c, 6.0, 0, TAU, 20, role[1], 1.2)
				text(f, Vector2(7, y + 10), String(role[0]), 8, role[1], HORIZONTAL_ALIGNMENT_CENTER, 12)
				text(thin, Vector2(24, y + 10), QuestLog._fit(thin, String(sp.name), 8, 100), 8, UiArt.DIM if dead else UiArt.CREAM)
				var sb := Rect2(128, y + 4, W - 134, 5)
				draw_rect(sb, RED_DARK)
				if not dead:
					var k := clampf(int(sp.health) / 100.0, 0.0, 1.0)
					draw_rect(Rect2(sb.position, Vector2(sb.size.x * k, sb.size.y)), RED if k > 0.35 else Color(1.0, 0.3, 0.1))
				y += 15.0


## The loot feed (owner 2026-11-04, after ESO's LootDrop Reborn: "loot that you pick up appears on a scrolling, and
## then disappearing graphic on the side of the screen ... the icon of the item, the name, the quality, and the sell
## value ... bordered by the color the item cons to you ... money, trash, and other currency drops"): over the minimap,
## the newest row at the bottom pushing the older ones up; each slides in, stays a while and fades. The same item
## again while its row is still up adds to its count. Fed by the server's "#LOOT|" lines (LootFeed.cs).
class LootFeed extends Part:
	const W := 250.0
	const ROW := 31.0
	const MAX_ROWS := 8
	const LIFE := 7.0
	const COIN_COLS := [Color(0.75, 0.85, 1.0), Color(0.85, 0.9, 0.95), Color(1.0, 0.82, 0.3), Color(0.8, 0.8, 0.82),
			Color(0.85, 0.5, 0.3)]
	var rows: Array = []                                 # [{kind, name, count, icon, quality, value, con, t, y}]

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	## One "#LOOT|" line (after the prefix): "i|count|model|quality|value|level|con|kind|name" or "m|copper".
	func receive(line: String) -> void:
		var f := line.split("|", true, 8)
		var now := Time.get_ticks_msec() / 1000.0
		var r := {}
		if f.size() >= 2 and f[0] == "m":
			r = {"kind": "money", "name": "", "count": 1, "icon": 0, "quality": 0, "value": int(f[1]), "con": -99}
		elif f.size() >= 9 and f[0] == "i":
			r = {"kind": f[7], "name": f[8], "count": int(f[1]), "icon": Server.item_icon(int(f[2])), "quality": int(f[3]),
					"value": int(f[4]), "con": int(f[6])}
		else:
			return
		for o in rows:                                     # the same thing again while its row is up: one row
			if String(o.kind) == String(r.kind) and String(o.name) == String(r.name) and now - float(o.t) < LIFE - 1.0:
				o.count = int(o.count) + int(r.count)
				o.value = int(o.value) + int(r.value)
				o.t = now
				o.bump = now
				return
		r.t = now
		r.bump = now
		r.y = size.y
		rows.append(r)
		while rows.size() > MAX_ROWS:
			rows.pop_front()

	func _process(delta: float) -> void:
		if rows.is_empty():
			return
		var now := Time.get_ticks_msec() / 1000.0
		rows = rows.filter(func(o): return now - float(o.t) < LIFE)
		for i in rows.size():                              # the newest at the bottom, the others eased up into place
			var want := size.y - (rows.size() - i) * ROW
			rows[i].y = lerpf(float(rows[i].y), want, clampf(delta * 12.0, 0.0, 1.0))
		queue_redraw()

	func _draw() -> void:
		var now := Time.get_ticks_msec() / 1000.0
		var f := UiArt.font(true)
		var thin := UiArt.font(false)
		for o in rows:
			var age := now - float(o.t)
			var a := clampf((LIFE - age) / 1.2, 0.0, 1.0)  # the last second and a bit: fading
			var slide := clampf((now - float(o.get("bump", o.t))) / 0.22, 0.0, 1.0)
			var x := (1.0 - ease(slide, 0.4)) * 40.0
			var y := float(o.y)
			var con := int(o.con)
			var edge: Color = ItemTooltip.CON.get(con, RIM) if con > -10 else Color(1.0, 0.82, 0.3)
			if String(o.kind) == "trash":
				edge = ItemTooltip.CON[-3]
			var r := Rect2(x, y + 1, W - x, ROW - 3)
			draw_rect(r, Color(0.03, 0.03, 0.035, 0.72 * a))
			draw_rect(Rect2(r.position, Vector2(3, r.size.y)), Color(edge, 0.95 * a))
			draw_rect(r, Color(edge.r, edge.g, edge.b, 0.55 * a), false, 1.0)
			var ic := Rect2(x + 7, y + 3, 24, 24)
			if String(o.kind) == "money":
				draw_circle(ic.get_center(), 9.0, Color(0.35, 0.22, 0.05, a))
				draw_circle(ic.get_center(), 7.5, Color(1.0, 0.8, 0.3, a))
				draw_circle(ic.get_center() + Vector2(-2, -2), 3.0, Color(1.0, 0.95, 0.7, 0.8 * a))
			else:
				var tex: Texture2D = ItemDb.icon(int(o.icon)) if int(o.icon) > 0 else null
				draw_rect(ic.grow(1), Color(0.0, 0.0, 0.0, 0.8 * a))
				if tex:
					draw_texture_rect(tex, ic, false, Color(1, 1, 1, a))
				draw_rect(ic.grow(1), Color(edge, a), false, 2.0)
			var tx := x + 38
			if String(o.kind) == "money":
				text(f, Vector2(tx, y + 19), "COINS", 9, Color(UiArt.DIM, a))
				_coins(f, W - 6, y + 19, int(o.value), a)
				continue
			var nm := ("%dx " % int(o.count) if int(o.count) > 1 else "") + String(o.name)
			var name_col: Color = Color(edge, a) if String(o.kind) == "item" else (Color(1.0, 0.85, 0.45, a) if String(o.kind) == "currency" else Color(0.75, 0.73, 0.7, a))
			text(f, Vector2(tx, y + 13), QuestLog._fit(f, nm, 9, W - tx - 8), 9, name_col)
			var sub := "CURRENCY" if String(o.kind) == "currency" else ("JUNK" if String(o.kind) == "trash" else ("QUA %d%%" % int(o.quality) if int(o.quality) > 0 else ""))
			text(thin, Vector2(tx, y + 25), sub, 7, Color(UiArt.DIM, a))
			if int(o.value) > 0:
				_coins(thin, W - 6, y + 25, int(o.value), a, 8)

	## Copper as "1g 2s 30c", right-aligned at x, each coin in its colour.
	func _coins(f: Font, right: float, y: float, copper: int, a: float, fs := 9) -> void:
		var parts: Array = []
		var m := copper / (100 * 100 * 1000 * 1000)
		var p := (copper / (100 * 100 * 1000)) % 1000
		var g := (copper / 10000) % 1000
		var sv := (copper / 100) % 100
		var c := copper % 100
		var vals := [m, p, g, sv, c]
		var tags := ["m", "p", "g", "s", "c"]
		for i in 5:
			if int(vals[i]) > 0 or (i == 4 and parts.is_empty()):
				parts.append([str(vals[i]) + tags[i], COIN_COLS[i]])
		var xx := right
		for i in range(parts.size() - 1, -1, -1):
			var w := f.get_string_size(String(parts[i][0]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			xx -= w
			text(f, Vector2(xx, y), String(parts[i][0]), fs, Color(parts[i][1], a))
			xx -= 4.0


## The menu bar (top left, no backing - GW2's): the sheets' orbs as the client paints them on control.bmp (character,
## skills, styles, spells, group), then drawn orbs in the same gold for the bags, quests, map and options. Hover: its
## name and key; lit while its window is open.
class HudMenu extends Part:
	const ICON := 24.0
	const GAP := 4.0
	# [id, name, key action, control.bmp tab index or -1]
	# (owner 2026-11-03: the Hero panel takes the character, skills, styles and spells sheets - HERO and SKILLS)
	const ITEMS := [["hero", "HERO", "show_stats", 0], ["skills", "SKILLS", "show_skills", 2],
			["group", "GROUP", "show_group", 5], ["bags", "INVENTORY", "show_inventory", -1],
			["quests", "QUEST JOURNAL", "show_journal", -1], ["map", "MAP", "show_map", -1], ["options", "OPTIONS", "", -1]]
	const TAB_X := [13, 41, 70, 98, 126, 154]
	var _hover := -1

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		tooltip_text = "MENU"

	func _index_at(p: Vector2) -> int:
		var i := int(p.x / (ICON + GAP))
		return i if i >= 0 and i < ITEMS.size() and p.x - i * (ICON + GAP) <= ICON and p.y >= 0 and p.y <= ICON else -1

	func _get_tooltip(at: Vector2) -> String:
		var i := _index_at(at)
		if i < 0:
			return ""
		var key := Keybinds.text(String(ITEMS[i][2])) if String(ITEMS[i][2]) != "" else "ESC"
		return String(ITEMS[i][1]) + ("  (%s)" % key if key != "" else "")

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseMotion:
			var i := _index_at(event.position)
			if i != _hover:
				_hover = i
				queue_redraw()
		elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			var i := _index_at(event.position)
			if i >= 0:
				open(String(ITEMS[i][0]))
				accept_event()

	func _notification(what: int) -> void:
		if what == NOTIFICATION_MOUSE_EXIT and _hover != -1:
			_hover = -1
			queue_redraw()

	func open(id: String) -> void:
		var ui: GameUI = hud.ui
		match id:
			"bags":
				ui.toggle_bags()
			"quests":
				ui.journal.toggle_window()
			"map":
				ui.map_window.player = ui.player
				ui.map_window.toggle_window()
			"options":
				ui.options.toggle_window()
			"hero":
				ui.open_hero("equipment")
			"skills":
				ui.open_hero("skills")
			_:
				ui.show_sheet(id)

	func _is_open(id: String) -> bool:
		var ui: GameUI = hud.ui
		match id:
			"bags":
				return ui.bags != null and ui.bags.visible
			"quests":
				return ui.journal.visible
			"map":
				return ui.map_window.visible
			"options":
				return ui.options.visible
			"hero":
				return ui.hero != null and ui.hero.visible and ui.hero.page == "equipment"
			"skills":
				return ui.hero != null and ui.hero.visible and ui.hero.page == "skills"
		return ui.right_panel.visible and ui.sheet_tab == id

	func _draw() -> void:
		for i in ITEMS.size():
			var r := Rect2(i * (ICON + GAP), 0, ICON, ICON)
			var c := r.get_center()
			var lit := _is_open(String(ITEMS[i][0]))
			draw_circle(c, ICON * 0.52, Color(0, 0, 0, 0.45))     # a soft shadow so the orbs read on bright sky
			var tab := int(ITEMS[i][3])
			if tab >= 0:
				# control.bmp: the normal row at y 3, the hover row 32 below; 25 x 24 art px per orb
				var src := Rect2(TAB_X[tab], 3 + (32 if i == _hover else (96 if lit else 0)), 25, 24)
				draw_texture_rect_region(UiArt.tex("control"), r, Rect2(src.position * UiArt.K, src.size * UiArt.K))
			else:
				_orb(c, ICON * 0.46, String(ITEMS[i][0]), i == _hover, lit)

	## A drawn orb as control.bmp paints them: a grey stone disc, the glyph cut into it - bright cyan on hover, teal
	## while its window is open.
	func _orb(c: Vector2, rad: float, id: String, hover: bool, lit := false) -> void:
		draw_circle(c, rad + 1.0, Color(0.16, 0.16, 0.17))
		draw_circle(c, rad, Color(0.42, 0.42, 0.43))
		draw_arc(c, rad - 1.2, deg_to_rad(200), deg_to_rad(340), 16, Color(0.6, 0.6, 0.62), 1.2, true)   # lit top edge
		draw_arc(c, rad - 1.2, deg_to_rad(20), deg_to_rad(160), 16, Color(0.25, 0.25, 0.26), 1.2, true)   # shaded foot
		var g := Color(0.15, 0.95, 1.0) if hover else (Color(0.1, 0.7, 0.75) if lit else Color(0.3, 0.3, 0.31))
		var k := rad * 0.55
		match id:
			"bags":                                          # a pouch: a round sack with a tied neck
				draw_circle(c + Vector2(0, k * 0.25), k * 0.8, g)
				draw_rect(Rect2(c + Vector2(-k * 0.35, -k * 0.85), Vector2(k * 0.7, k * 0.45)), g)
				draw_line(c + Vector2(-k * 0.5, -k * 0.4), c + Vector2(k * 0.5, -k * 0.4), Color(0.42, 0.42, 0.43), 1.2)
			"quests":                                        # a scroll
				draw_rect(Rect2(c + Vector2(-k * 0.6, -k * 0.8), Vector2(k * 1.2, k * 1.6)), g)
				for j in 3:
					var y := -k * 0.4 + j * k * 0.4
					draw_line(c + Vector2(-k * 0.35, y), c + Vector2(k * 0.35, y), Color(0.42, 0.42, 0.43), 1.0)
				draw_circle(c + Vector2(0, -k * 0.85), k * 0.3, g)
				draw_circle(c + Vector2(0, k * 0.85), k * 0.3, g)
			"map":                                           # a folded map
				var pts := PackedVector2Array([c + Vector2(-k, -k * 0.7), c + Vector2(-k * 0.33, -k * 0.9), c + Vector2(k * 0.33, -k * 0.7),
						c + Vector2(k, -k * 0.9), c + Vector2(k, k * 0.7), c + Vector2(k * 0.33, k * 0.9), c + Vector2(-k * 0.33, k * 0.7),
						c + Vector2(-k, k * 0.9)])
				draw_colored_polygon(pts, g)
				draw_line(c + Vector2(-k * 0.33, -k * 0.9), c + Vector2(-k * 0.33, k * 0.7), Color(0.42, 0.42, 0.43), 1.0)
				draw_line(c + Vector2(k * 0.33, -k * 0.7), c + Vector2(k * 0.33, k * 0.9), Color(0.42, 0.42, 0.43), 1.0)
			"options":                                       # a cog
				for j in 8:
					var a := j * TAU / 8.0
					draw_line(c + Vector2(cos(a), sin(a)) * k * 0.6, c + Vector2(cos(a), sin(a)) * k * 1.05, g, 2.2)
				draw_circle(c, k * 0.7, g)
				draw_circle(c, k * 0.3, Color(0.42, 0.42, 0.43))
