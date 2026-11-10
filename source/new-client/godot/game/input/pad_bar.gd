extends Control
## The controller bar (owner 2026-11-10: "a UI element ... that basically replaces the default hotbars"): while the pad
## is the device in use and Action Combat is on, two diamonds take the quickbars' place at the bottom of the screen -
## the d-pad on the left, the face buttons on the right, with what the triggers and bumpers do down their outer sides.
## Each button shows its binding (Pad.bindings) for the bumpers held now: a quickbar slot is the slot itself (its icon,
## its reuse timer, drop a spell or style onto it), anything else a plate with its name. Each diamond runs clockwise
## from the left: d-pad left, up, right, down; X, Y, B, A.
## The two halves are pieces of their own (owner 2026-11-10: "I want every element editable in the Edit UI layout"):
## the modern HUD places them and EDIT UI moves them (ModernHud's controller layout); the classic HUD puts them at the
## bottom centre. Also the menu wheel (the bound button held): the windows round a ring, picked with either stick.

const SLOT := 40.0
const GAP := 4.0
const SPREAD := 165.0                    # each diamond's centre from the screen's centre line
const BOTTOM := 78.0                     # their centres above the bottom edge
const TAG_W := 92.0                      # the outer column of trigger / bumper tags
const DIAMOND := SLOT * 3.0 + GAP * 2.0
const CLUSTER := Vector2(DIAMOND + TAG_W + 8.0, DIAMOND)
const OFFSETS := [Vector2(-1, 0), Vector2(0, -1), Vector2(1, 0), Vector2(0, 1)]

var ui: Node
var left: Cluster
var right: Cluster
var _shown := false
var _radial := false
var _radial_pick := -1

const WHEEL := [["HERO", "hero"], ["BAGS", "bags"], ["ABILITIES", "skills"], ["STYLES", "ac_styles"], ["MAP", "map"],
		["JOURNAL", "journal"], ["GUILD", "guild"], ["OPTIONS", "options"]]


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	left = Cluster.new()
	left.bar = self
	left.side = 0
	right = Cluster.new()
	right.bar = self
	right.side = 1
	for c in [left, right]:
		c.size = CLUSTER
		c.visible = false
		add_child(c)
	Pad.layer_changed.connect(func(_l): _rebuild())
	Pad.bindings_changed.connect(_rebuild)
	PlayerData.changed.connect(_refresh_slots)
	Keybinds.changed.connect(_refresh_slots)
	if get_parent():
		get_parent().move_child.call_deferred(self, mini(2, get_parent().get_child_count() - 1))
	place_default()
	_rebuild()


func shown() -> bool:
	return _shown


## Where the two halves go with nothing moved: either side of the screen's centre at the bottom.
func place_default() -> void:
	var a: Vector2 = ui.area() if ui and ui.has_method("area") else get_viewport_rect().size
	var y := a.y - BOTTOM - DIAMOND * 0.5
	left.position = Vector2(a.x * 0.5 - SPREAD - DIAMOND * 0.5 - (TAG_W + 8.0), y)
	right.position = Vector2(a.x * 0.5 + SPREAD - DIAMOND * 0.5, y)


func _process(_delta: float) -> void:
	var ac = Pad.ac
	var want := Pad.active and ac != null and is_instance_valid(ac) and bool(ac.get("on")) and ui != null \
			and not bool(ui.get("hidden_all"))
	if want != _shown:
		_shown = want
		left.visible = want
		right.visible = want
		_take_bars(want)
		if ui.get("modern"):
			ui.modern.set_pad_mode(want)                   # (its controller layout: this bar's place, the pieces moved)
		else:
			place_default()
		_rebuild()
	if _shown:
		for q in ui.quickbars:
			if q.visible:
				q.visible = false                          # (a layout pass may show them again)
		left.queue_redraw()
		right.queue_redraw()
	visible = true
	if _radial:
		_radial_tick()
	queue_redraw()


var _hidden_bars := {}


func _take_bars(on: bool) -> void:
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


func _rebuild() -> void:
	if left:
		left.rebuild()
		right.rebuild()


func _refresh_slots() -> void:
	if left:
		left.refresh_slots()
		right.refresh_slots()


## The cell showing an input ("rb+x") now, if it is on show.
func cell_for(input: String) -> Control:
	for c in [left, right]:
		var cell: Control = c.cells.get(input)
		if cell:
			return cell
	return null


## A slot used from the pad (its action, "qb2_3"): it lights up for a moment.
func flash(action: String) -> void:
	for c in [left, right]:
		for input in c.cells:
			if String(Pad.bindings.get(input, "")) == action:
				var s: Control = c.cells[input]
				s.modulate = Color(1.6, 1.4, 0.8)
				s.create_tween().tween_property(s, "modulate", Color.WHITE, 0.25)


static func _ranged() -> bool:
	return String(PlayerData.active_weapon) == "ranged"


## One half: a diamond of four buttons and the outer column of tags (left: LT, LB, LB+RB - right: RT, RB).
class Cluster extends Control:
	var bar
	var side := 0                           # 0 the d-pad, 1 the face buttons
	var cells := {}                         # input -> its cell (a QuickSlot or a plate)

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _buttons() -> Array:
		return Pad.SLOTS.slice(0, 4) if side == 0 else Pad.SLOTS.slice(4, 8)

	func _diamond_origin() -> Vector2:
		return Vector2(TAG_W + 8.0, 0.0) if side == 0 else Vector2.ZERO

	func _slot_pos(i: int) -> Vector2:
		var c := _diamond_origin() + Vector2(DIAMOND, DIAMOND) * 0.5
		return c + (OFFSETS[i] as Vector2) * (SLOT + GAP) - Vector2(SLOT, SLOT) * 0.5

	## The cells for the bumpers held now: each button's binding.
	func rebuild() -> void:
		for c in get_children():
			c.queue_free()
		cells.clear()
		var prefix: String = Pad.LAYERS[Pad.layer]
		var buttons := _buttons()
		for i in 4:
			var input := prefix + String(buttons[i])
			var act := String(Pad.bindings.get(input, ""))
			var hold := false
			if act == "":
				act = String(Pad.bindings.get(input + ":hold", ""))
				hold = act != ""
			var cell: Control
			if act.begins_with("qb") and not hold:
				var f := act.trim_prefix("qb").split("_")
				var s := Quickbar.QuickSlot.new()
				s.bar = int(f[0]) - 1
				s.slot = int(f[1]) - 1
				s.size = Vector2(31, 31)
				s.scale = Vector2.ONE * (SLOT / 31.0)
				add_child(s)
				s.refresh()
				s._key.visible = false                     # (the button's glyph is drawn instead)
				s.tooltip_text = ""
				cell = s
			else:
				var p := Panel.new()
				p.add_theme_stylebox_override("panel", Quickbar.text_plate())
				p.size = Vector2(SLOT, SLOT)
				p.mouse_filter = Control.MOUSE_FILTER_IGNORE
				var l := UiArt.label(String(Pad.action_info(act)[2]) if act != "" else "", 7, UiArt.CREAM)
				l.set_anchors_preset(Control.PRESET_FULL_RECT)
				l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
				l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
				l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				p.add_child(l)
				if act == "":
					p.modulate = Color(1, 1, 1, 0.45)
				add_child(p)
				cell = p
			cell.position = _slot_pos(i)
			cell.set_meta("act", act)
			cells[input] = cell
		queue_redraw()

	func refresh_slots() -> void:
		for input in cells:
			var c: Control = cells[input]
			if c.has_method("refresh"):
				c.refresh()
				c._key.visible = false
				c.tooltip_text = ""

	func _draw() -> void:
		var font := UiArt.font()
		var buttons := _buttons()
		for i in 4:
			var pos := _slot_pos(i)
			var input := String(Pad.LAYERS[Pad.layer]) + String(buttons[i])
			var cell: Control = cells.get(input)
			var act := String(cell.get_meta("act", "")) if cell else ""
			if act.begins_with("qb"):                          # a slot's square (an empty one shows too)
				draw_rect(Rect2(pos, Vector2(SLOT, SLOT)), Color(0.08, 0.07, 0.06, 0.8))
				draw_rect(Rect2(pos, Vector2(SLOT, SLOT)), Color(0.5, 0.42, 0.25), false, 1.0)
			# a style button lights when a press would fire one (the server's lights)
			var lit := ""
			var ac = Pad.ac
			if ac and is_instance_valid(ac) and act.begins_with("style_"):
				var kinds := [["reactive", "R"], ["chain", "C"], ["position", "P"]] if act == "style_auto" \
						else [[act.trim_prefix("style_"), ""]]
				for k in kinds:
					if bool(ac.call("style_lit", k[0])):
						lit += String(k[1]) if k[1] != "" else "*"
			if lit != "":
				draw_rect(Rect2(pos - Vector2(2, 2), Vector2(SLOT + 4, SLOT + 4)), Color(1.0, 0.82, 0.3, 0.9), false, 2.0)
				if act == "style_auto":
					draw_string(font, pos + Vector2(3, SLOT - 3), lit, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, UiArt.GOLD_HI)
			Pad.glyph(self, pos + Vector2(SLOT - 3, 3), String(buttons[i]))
		# the outer column: the trigger, the bumper bars
		var tags := []
		var lay: int = Pad.layer
		if side == 0:
			tags = [["lt", "lt", false], ["lb", "lb+", lay == 1], ["lb+rb", "lb+rb+", lay == 3]]
		else:
			tags = [["rt", "rt", false], ["rb", "rb+", lay == 2]]
		var x := 0.0 if side == 0 else DIAMOND + 8.0
		var y := 6.0
		for t in tags:
			var what := ""
			if String(t[1]).ends_with("+"):
				what = _layer_name(String(t[1]))
			else:
				what = String(Pad.action_info(String(Pad.bindings.get(String(t[1]), "")))[2])
			_tag(Rect2(x, y, TAG_W, 18), Pad.describe(String(t[0])), what, bool(t[2]))
			y += 24.0

	## A bumper layer's name: "BAR 1" when it holds a quickbar's slots, else "MORE".
	static func _layer_name(prefix: String) -> String:
		for b in Pad.SLOTS:
			var a := String(Pad.bindings.get(prefix + String(b), ""))
			if a.begins_with("qb"):
				return "BAR " + a.trim_prefix("qb").split("_")[0]
		return "MORE"

	func _tag(r: Rect2, button: String, what: String, lit: bool) -> void:
		var font := UiArt.font()
		draw_rect(r, Color(0.17, 0.15, 0.12, 0.85) if not lit else Color(0.45, 0.36, 0.15, 0.95))
		draw_rect(r, UiArt.GOLD if lit else Color(0.5, 0.42, 0.25), false, 1.0)
		var text := button + "  " + what
		draw_string(font, r.position + Vector2(5, 13), text, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 8, 9,
				UiArt.GOLD_HI if lit else UiArt.CREAM)


# ---------------------------------------------------------------- the menu wheel and the windows

func radial_shown() -> bool:
	return _radial


func radial_open() -> void:
	_radial = true
	_radial_pick = -1


## Let go: opens the window picked (true), or nothing when the sticks were left in the middle.
func radial_close() -> bool:
	if not _radial:
		return false
	_radial = false
	queue_redraw()
	if _radial_pick < 0:
		return false
	open_window(String(WHEEL[_radial_pick][1]))
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


func _draw() -> void:
	if not _radial:
		return
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


func open_window(id: String) -> void:
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
