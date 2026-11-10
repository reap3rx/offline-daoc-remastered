extends Control
## The controller bar (owner 2026-11-10: "a UI element ... that basically replaces the default hotbars"): while the pad
## is the device in use and Action Combat is on, two diamonds take the quickbars' place at the bottom of the screen -
## the d-pad on the left, the face buttons on the right. Bare, they show what the buttons do in the fight; hold LB / RB
## (both: the third bar) and they turn into that quickbar's slots 1-8 - the slots themselves, so the icons, the reuse
## timers and dragging a spell or style onto them all work as on the quickbars. Each diamond runs clockwise from the
## left: d-pad left, up, right, down = slots 1-4; X, Y, B, A = slots 5-8.
## Also the menu wheel (View held): the windows round a ring, picked with either stick, opened on letting go.

const SLOT := 40.0
const GAP := 4.0
const SPREAD := 165.0                    # each diamond's centre from the screen's centre line
const BOTTOM := 78.0                     # their centres above the bottom edge
const A_GREEN := Color(0.38, 0.74, 0.25)
const B_RED := Color(0.86, 0.25, 0.2)
const X_BLUE := Color(0.26, 0.5, 0.95)
const Y_YELLOW := Color(0.95, 0.78, 0.2)
const PAD_GREY := Color(0.62, 0.6, 0.56)
# where each of the eight buttons sits round its diamond's centre, in Pad.SLOT_BUTTONS order
const OFFSETS := [Vector2(-1, 0), Vector2(0, -1), Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1),
		Vector2(1, 0), Vector2(0, 1)]
const GLYPHS := ["<", "^", ">", "v", "X", "Y", "B", "A"]
const BASE := ["TORCH", "WEAPON", "RUN", "SIT", "STYLE", "USE", "DODGE", "JUMP"]

var ui: Node
var _slots: Array = []                   # [layer 1..3] -> [8 QuickSlot]
var _plates: Array = []                  # 8 base-layer plates
var _hidden_bars := {}                   # quickbar -> its visibility before the bar took over
var _shown := false
var _radial := false
var _radial_pick := -1

const WHEEL := [["HERO", "hero"], ["BAGS", "bags"], ["ABILITIES", "skills"], ["STYLES", "ac_styles"], ["MAP", "map"],
		["JOURNAL", "journal"], ["GUILD", "guild"], ["OPTIONS", "options"]]


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	visible = false
	for i in 8:
		var p := Panel.new()
		p.add_theme_stylebox_override("panel", Quickbar.text_plate())
		p.size = Vector2(SLOT, SLOT)
		p.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := UiArt.label(BASE[i], 7, UiArt.CREAM)
		l.set_anchors_preset(Control.PRESET_FULL_RECT)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		p.add_child(l)
		add_child(p)
		_plates.append(p)
	_slots.append([])
	for layer in range(1, 4):
		var row := []
		for i in 8:
			var s := Quickbar.QuickSlot.new()
			s.bar = layer - 1
			s.slot = i
			s.size = Vector2(31, 31)
			s.scale = Vector2.ONE * (SLOT / 31.0)
			s.visible = false
			add_child(s)
			s._key.visible = false                         # (the button's glyph is drawn instead)
			row.append(s)
		_slots.append(row)
	Pad.layer_changed.connect(func(_l): _show_layer())
	PlayerData.changed.connect(_refresh)
	Keybinds.changed.connect(_refresh)
	if get_parent():
		get_parent().move_child.call_deferred(self, mini(2, get_parent().get_child_count() - 1))
	_refresh()


func _refresh() -> void:
	for layer in range(1, 4):
		for s in _slots[layer]:
			s.refresh()
			s._key.visible = false
			s.tooltip_text = ""


func _centers() -> Array:
	var a: Vector2 = ui.area() if ui and ui.has_method("area") else get_viewport_rect().size
	return [Vector2(a.x * 0.5 - SPREAD, a.y - BOTTOM), Vector2(a.x * 0.5 + SPREAD, a.y - BOTTOM)]


func _slot_pos(i: int) -> Vector2:
	var c: Vector2 = _centers()[0 if i < 4 else 1]
	return c + (OFFSETS[i] as Vector2) * (SLOT + GAP) - Vector2(SLOT, SLOT) * 0.5


func _process(_delta: float) -> void:
	var ac = Pad.ac
	var want := Pad.active and ac != null and is_instance_valid(ac) and bool(ac.get("on")) and ui != null \
			and not bool(ui.get("hidden_all"))
	if want != _shown:
		_shown = want
		_take_bars(want)
		_show_layer()
	if _shown:
		for q in ui.quickbars:
			if q.visible:
				q.visible = false                          # (a layout pass may show them again)
	visible = _shown or _radial
	if _radial:
		_radial_tick()
	if visible:
		queue_redraw()


func _take_bars(on: bool) -> void:
	if ui == null:
		return
	if on:
		_hidden_bars.clear()
		for q in ui.quickbars:
			_hidden_bars[q] = q.visible
			q.visible = false
	else:
		for q in _hidden_bars:
			if is_instance_valid(q):
				q.visible = bool(_hidden_bars[q])
		_hidden_bars.clear()


func _show_layer() -> void:
	var layer := Pad.layer
	for i in 8:
		var pos := _slot_pos(i)
		_plates[i].position = pos
		_plates[i].visible = _shown and layer == 0
		for l in range(1, 4):
			var s: Control = _slots[l][i]
			s.position = pos
			s.visible = _shown and layer == l


## A slot used from the pad: it lights up for a moment.
func flash(qbar: int, slot: int) -> void:
	if qbar + 1 < _slots.size() and slot < 8:
		var s: Control = _slots[qbar + 1][slot]
		s.modulate = Color(1.6, 1.4, 0.8)
		s.create_tween().tween_property(s, "modulate", Color.WHITE, 0.25)


func _draw() -> void:
	if _shown:
		_draw_bar()
	if _radial:
		_draw_wheel()


func _draw_bar() -> void:
	var font := UiArt.font()
	var layer := Pad.layer
	var colors := [PAD_GREY, PAD_GREY, PAD_GREY, PAD_GREY, X_BLUE, Y_YELLOW, B_RED, A_GREEN]
	for i in 8:
		var pos := _slot_pos(i)
		if layer > 0:                                      # an ability bar: the slot's square (an empty one shows too)
			draw_rect(Rect2(pos, Vector2(SLOT, SLOT)), Color(0.08, 0.07, 0.06, 0.8))
			draw_rect(Rect2(pos, Vector2(SLOT, SLOT)), Color(0.5, 0.42, 0.25), false, 1.0)
		# STYLE lights when a press would fire one (the server's lights), the kind lit written under it
		if layer == 0 and i == 4 and Pad.ac and is_instance_valid(Pad.ac):
			var lit := ""
			for k in [["reactive", "R"], ["chain", "C"], ["position", "P"]]:
				if bool(Pad.ac.call("style_lit", k[0])):
					lit += k[1]
			if lit != "":
				draw_rect(Rect2(pos - Vector2(2, 2), Vector2(SLOT + 4, SLOT + 4)), Color(1.0, 0.82, 0.3, 0.9), false, 2.0)
				draw_string(font, pos + Vector2(3, SLOT - 3), lit, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, UiArt.GOLD_HI)
		# the button's glyph in the corner
		var c := pos + Vector2(SLOT - 3, 3)
		draw_circle(c, 7.0, Color(0.05, 0.05, 0.05, 0.9))
		draw_circle(c, 6.0, colors[i])
		draw_string(font, c + Vector2(-3.5, 3.5), GLYPHS[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.05, 0.05, 0.05))
	var cs := _centers()
	# the triggers beside the diamonds, the bumpers' bars over them
	_tag(cs[0] + Vector2(-(SLOT * 1.5 + GAP + 34), 0), "LT", "PARRY" if not _ranged() else "CRIT", false)
	_tag(cs[1] + Vector2(SLOT * 1.5 + GAP + 34, 0), "RT", "ATTACK" if not _ranged() else "SHOOT", false)
	var mid := Vector2((cs[0].x + cs[1].x) * 0.5, cs[0].y - SLOT * 1.5 - GAP - 14)
	_tag(mid + Vector2(-92, 0), "LB", "BAR 1", layer == 1)
	_tag(mid, "LB+RB", "BAR 3", layer == 3)
	_tag(mid + Vector2(92, 0), "RB", "BAR 2", layer == 2)


func _ranged() -> bool:
	return String(PlayerData.active_weapon) == "ranged"


func _tag(at: Vector2, button: String, what: String, lit: bool) -> void:
	var font := UiArt.font()
	var text := button + "  " + what
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9).x + 12.0
	var r := Rect2(at - Vector2(w * 0.5, 8), Vector2(w, 16))
	draw_rect(r, Color(0.17, 0.15, 0.12, 0.85) if not lit else Color(0.45, 0.36, 0.15, 0.95))
	draw_rect(r, UiArt.GOLD if lit else Color(0.5, 0.42, 0.25), false, 1.0)
	draw_string(font, r.position + Vector2(6, 12), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, UiArt.GOLD_HI if lit else UiArt.CREAM)


# ---------------------------------------------------------------- the menu wheel

func radial_shown() -> bool:
	return _radial


func radial_open() -> void:
	_radial = true
	_radial_pick = -1
	visible = true


## Let go: opens the window picked (true), or nothing when the sticks were left in the middle.
func radial_close() -> bool:
	if not _radial:
		return false
	_radial = false
	queue_redraw()
	if _radial_pick < 0:
		return false
	_open(String(WHEEL[_radial_pick][1]))
	return true


func _radial_tick() -> void:
	var d := Pad.device
	if d < 0:
		return
	var v := Vector2(Input.get_joy_axis(d, JOY_AXIS_LEFT_X), Input.get_joy_axis(d, JOY_AXIS_LEFT_Y))
	var r := Vector2(Input.get_joy_axis(d, JOY_AXIS_RIGHT_X), Input.get_joy_axis(d, JOY_AXIS_RIGHT_Y))
	if r.length() > v.length():
		v = r
	if v.length() < 0.5:
		return                                             # (the last pick stays until another is pointed at)
	var ang := fposmod(atan2(v.x, -v.y), TAU)              # 0 = up, clockwise
	_radial_pick = int(round(ang / TAU * WHEEL.size())) % WHEEL.size()


func _draw_wheel() -> void:
	var font := UiArt.font()
	var a: Vector2 = ui.area() if ui and ui.has_method("area") else get_viewport_rect().size
	var c := a * 0.5
	draw_circle(c, 170.0, Color(0.06, 0.055, 0.05, 0.82))
	draw_arc(c, 170.0, 0.0, TAU, 64, UiArt.GOLD, 2.0)
	draw_circle(c, 46.0, Color(0.12, 0.1, 0.08, 0.95))
	draw_arc(c, 46.0, 0.0, TAU, 48, Color(0.5, 0.42, 0.25), 1.5)
	var hint := "MENU" if _radial_pick < 0 else String(WHEEL[_radial_pick][0])
	var hw := font.get_string_size(hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
	draw_string(font, c + Vector2(-hw * 0.5, 4), hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, UiArt.GOLD_HI)
	for i in WHEEL.size():
		var ang := TAU * i / WHEEL.size()
		var at := c + Vector2(sin(ang), -cos(ang)) * 116.0
		var picked := i == _radial_pick
		var text := String(WHEEL[i][0])
		var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x + 16.0
		var rect := Rect2(at - Vector2(w * 0.5, 12), Vector2(w, 24))
		draw_rect(rect, Color(0.45, 0.36, 0.15, 0.95) if picked else Color(0.17, 0.15, 0.12, 0.92))
		draw_rect(rect, UiArt.GOLD_HI if picked else Color(0.5, 0.42, 0.25), false, 1.5 if picked else 1.0)
		draw_string(font, rect.position + Vector2(8, 16), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 10,
				UiArt.GOLD_HI if picked else UiArt.CREAM)


func _open(id: String) -> void:
	if ui == null:
		return
	match id:
		"hero":
			ui.open_hero("equipment")
		"skills":
			ui.open_hero("skills")
		"bags":
			ui.show_sheet("inventory")
		"ac_styles":
			PlayerData.window_toggle.emit("ac_styles")
		"map":
			if ui.map_window:
				ui.map_window.player = ui.player
				ui.map_window.toggle_window()
		"journal":
			if ui.journal:
				ui.journal.toggle_window()
		"guild":
			if ui.get("guild_window"):
				ui.guild_window.toggle_window()
		"options":
			if ui.options:
				ui.options.toggle_window()
