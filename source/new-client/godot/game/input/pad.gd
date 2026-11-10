extends Node
## Autoload "Pad": an Xbox-style gamepad (owner 2026-11-10: "a first pass at controller support ... only usable in
## action combat mode ... movement, menus and basic combat ... emulate WoW Forever's control scheme"). The pad and the
## mouse / keyboard take turns: the first stick push or button makes the pad the active device (its bar replaces the
## quickbars, the mouse pointer becomes a pad-driven one), the first real mouse move or key gives control back.
##
## In the world (Action Combat on - the first button turns it on):
##   Left stick   move; how far it is pushed is how fast you go (walk past the first part of the throw, run beyond)
##   L3           sprint (while you keep moving)
##   Right stick  look; R3 lock on / off - while locked, flick right or left for the next target that way
##   RT           attack: tap a swing, hold the power attack (a bow: hold to draw, let go to loose)
##   LT           parry / block (a bow: the critical shot)
##   A jump - B dodge - X style (whichever is lit: reactive, then chain, then positional) - Y interact (hold: weapon
##                out / away)
##   D-pad        up cycle weapons, right run lock, down sit / stand, left torch
##   LB / RB      held: ability bars - LB quickbar 1, RB quickbar 2, both quickbar 3. The bar's slots 1-8 are the
##                d-pad (left, up, right, down) then the face buttons (X, Y, B, A): each diamond clockwise from the left
##                LB tapped: the next of you and your group; RB tapped: the nearest enemy
##   View         tap: the Hero panel; hold: the menu wheel (pick with either stick, let go to open)
##   Menu         Esc - closes your windows, else untargets / the options
## With a window open (or the Alt cursor) the pad drives the pointer: left stick moves it (the d-pad steps a slot at a
## time), A clicks (hold to drag), X right-clicks, B closes your windows (Esc), right stick scrolls.

signal active_changed(on: bool)
signal layer_changed(layer: int)

const DEADZONE := 0.18
const TRIGGER_ON := 0.45
const TRIGGER_OFF := 0.3
const LOOK_YAW := 3.4                   # rad / s at full right-stick throw
const LOOK_PITCH := 2.0
const LOOK_CURVE := 1.8                 # small throws turn finely
const CURSOR_SPEED := 1300.0            # px / s at full throw
const CURSOR_STEP := 34.0               # a d-pad press in a window: one quickbar slot / bag cell
const SCROLL_MS := 90
const TAP_MS := 220                     # a bumper / View released this soon (nothing else pressed): a tap
const HOLD_Y_MS := 450                  # Y held this long: weapon out / away instead of interact
const FLICK_ON := 0.8                   # locked on: a right-stick flick this far picks the next target
const FLICK_OFF := 0.35
const AUTO_ON_MS := 3000

static var assume_connected := false     # (tests: injected pad events, no pad plugged in)
var active := false                      # the pad is the device in use now
var device := -1
var layer := 0                           # 0 none, 1 LB, 2 RB, 3 both
var sprint := false
var ac: Node = null                      # the Action Combat node (ActionCombatMode.setup attaches it)
var viewer: Node = null
var bar: Control = null                  # the controller bar (pad_bar.gd)

var _down := {}                          # JoyButton -> msec it went down
var _used_in_hold := {}                  # a bumper / View: another button went while it was held
var _rt := false
var _lt := false
var _flick := 0
var _cursor := Vector2.ZERO
var _cursor_shown := false
var _scroll_at := 0
var _auto_at := -100000
var _group_pick := 0
var _group_pick_at := 0
var _layer: CanvasLayer
var _arrow: Control
var _a_drag := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_layer = CanvasLayer.new()
	_layer.layer = 128
	add_child(_layer)
	_arrow = Control.new()
	_arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_arrow.set_anchors_preset(Control.PRESET_FULL_RECT)
	_arrow.visible = false
	_arrow.draw.connect(_draw_arrow)
	_layer.add_child(_arrow)


## ActionCombatMode.setup: the world is up - the bar goes onto its interface.
func attach(combat: Node, v: Node) -> void:
	ac = combat
	viewer = v
	var ui = v.get("ui") if v else null
	if ui and ui.get("root"):
		if bar and is_instance_valid(bar):
			bar.queue_free()
		bar = preload("res://game/input/pad_bar.gd").new()
		bar.ui = ui
		(ui.root as Control).add_child(bar)


func _player() -> Node:
	return viewer.get("player") if viewer and is_instance_valid(viewer) else null


## In the world with Action Combat on, the pointer away: the pad fights. Otherwise it drives the pointer.
func world_mode() -> bool:
	var p := _player()
	if ac == null or not is_instance_valid(ac) or p == null or not Server.playing:
		return false
	return bool(ac.get("on")) and not bool(p.get("action_cursor"))


## The left stick as a move: x right, y forward, length 0..1 (zero inside the dead zone, or when it isn't the pad's turn).
func move_vector() -> Vector2:
	if not active or not world_mode() or device < 0:
		return Vector2.ZERO
	return _stick(JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y) * Vector2(1, -1)


func moving() -> bool:
	return move_vector() != Vector2.ZERO


func _stick(ax: JoyAxis, ay: JoyAxis) -> Vector2:
	var v := Vector2(Input.get_joy_axis(device, ax), Input.get_joy_axis(device, ay))
	var l := v.length()
	if l < DEADZONE:
		return Vector2.ZERO
	return v / l * clampf((l - DEADZONE) / (1.0 - DEADZONE), 0.0, 1.0)


func _set_active(on: bool) -> void:
	if on == active:
		return
	active = on
	if not on:
		_release_all()
		if Input.mouse_mode == Input.MOUSE_MODE_HIDDEN:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	active_changed.emit(on)


# ---------------------------------------------------------------- events

func _input(event: InputEvent) -> void:
	if event.has_meta("pad"):
		return                                             # (our own pointer and key presses)
	if event is InputEventJoypadButton:
		device = event.device
		_set_active(true)
		_button(event.button_index, event.pressed)
		get_viewport().set_input_as_handled()              # (Godot's own ui_* pad mappings stay out of it)
	elif event is InputEventJoypadMotion:
		if absf(event.axis_value) > 0.5:
			device = event.device
			_set_active(true)
		get_viewport().set_input_as_handled()
	elif active and (event is InputEventKey and event.pressed or event is InputEventMouseButton and event.pressed
			or event is InputEventMouseMotion and (event as InputEventMouseMotion).relative.length() > 3.0
			and not (_cursor_shown and (event as InputEventMouseMotion).position.distance_to(_cursor) < 2.0)):
		_set_active(false)                                 # the mouse / keyboard again


func _button(b: JoyButton, pressed: bool) -> void:
	var now := Time.get_ticks_msec()
	if pressed:
		_down[b] = now
		for held in [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_BACK]:
			if held != b and _down.has(held):
				_used_in_hold[held] = true
	var since := now - int(_down.get(b, now))
	if not pressed:
		_down.erase(b)
	if b in [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER]:
		_bumper(b, pressed, since)
		return
	if b == JOY_BUTTON_BACK:
		if bar and is_instance_valid(bar):
			if pressed:
				_used_in_hold[b] = false
				bar.radial_open()
			else:
				var picked: bool = bar.radial_close()
				if not picked and since <= TAP_MS * 2 and not bool(_used_in_hold.get(b, false)):
					_open_hero()
		return
	if b == JOY_BUTTON_START:
		if pressed:
			_key(KEY_ESCAPE)
		return
	if world_mode():
		_world_button(b, pressed, since)
	else:
		_cursor_button(b, pressed)
		if pressed and _player() and Server.playing and ac and not bool(ac.get("on")) and not _pointer_wanted() \
				and now - _auto_at > AUTO_ON_MS:
			_auto_at = now                                 # the pad plays in Action Combat: a button in the world turns it on
			ac.call("_toggle")


func _bumper(b: JoyButton, pressed: bool, since: int) -> void:
	if pressed:
		_used_in_hold[b] = false
	elif world_mode() and since <= TAP_MS and not bool(_used_in_hold.get(b, false)):
		if b == JOY_BUTTON_RIGHT_SHOULDER:
			_fire("target_enemy")
		else:
			_next_friend()
	var l := (1 if _down.has(JOY_BUTTON_LEFT_SHOULDER) else 0) + (2 if _down.has(JOY_BUTTON_RIGHT_SHOULDER) else 0)
	if l != layer:
		layer = l
		layer_changed.emit(layer)


## LB tapped: you, then each of your group in turn (the Target Group #1-8 keys); after a pause it starts with you again.
func _next_friend() -> void:
	var now := Time.get_ticks_msec()
	var n := clampi(PlayerData.group.size(), 1, 8)
	_group_pick = 0 if now - _group_pick_at > 4000 else (_group_pick + 1) % n
	_group_pick_at = now
	_fire("target_group_%d" % (_group_pick + 1))


const SLOT_BUTTONS := [JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_DOWN,
		JOY_BUTTON_X, JOY_BUTTON_Y, JOY_BUTTON_B, JOY_BUTTON_A]


func _world_button(b: JoyButton, pressed: bool, since: int) -> void:
	if layer > 0 and b in SLOT_BUTTONS:
		if pressed:
			_use_slot(layer - 1, SLOT_BUTTONS.find(b))
		return
	match b:
		JOY_BUTTON_A:
			Keybinds.pad_held["jump"] = pressed
		JOY_BUTTON_B:
			if pressed:
				var mv := _stick(JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y)
				ac.call("pad_dodge", Vector3(mv.x, 0.0, mv.y))
		JOY_BUTTON_X:
			if pressed:
				ac.call("pad_style")
		JOY_BUTTON_Y:
			if not pressed:
				if since >= HOLD_Y_MS:
					pass                                       # (the hold already went)
				else:
					ac.call("pad_interact")
		JOY_BUTTON_DPAD_UP:
			if pressed:
				_fire("weapon_cycle")
		JOY_BUTTON_DPAD_RIGHT:
			if pressed:
				_fire("run_lock")
		JOY_BUTTON_DPAD_DOWN:
			if pressed:
				_fire("sit")
		JOY_BUTTON_DPAD_LEFT:
			if pressed:
				_fire("torch")
		JOY_BUTTON_LEFT_STICK:
			if pressed:
				sprint = not sprint
		JOY_BUTTON_RIGHT_STICK:
			if pressed:
				ac.call("pad_lock_tap")


func _use_slot(qbar: int, slot: int) -> void:
	var ui = viewer.get("ui") if viewer else null
	if ui == null:
		return
	var bars: Array = ui.get("quickbars")
	if qbar < bars.size():
		bars[qbar].use_slot(slot)
		if bar and is_instance_valid(bar):
			bar.flash(qbar, slot)


func _open_hero() -> void:
	var ui = viewer.get("ui") if viewer else null
	if ui and ui.has_method("open_hero"):
		ui.open_hero("equipment")


func _pointer_wanted() -> bool:
	var p := _player()
	return p != null and bool(p.get("action_cursor"))


# ---------------------------------------------------------------- the pointer (windows, menus, the screens before the world)

func _cursor_button(b: JoyButton, pressed: bool) -> void:
	match b:
		JOY_BUTTON_A:
			_a_drag = pressed
			_mouse_button(MOUSE_BUTTON_LEFT, pressed)
		JOY_BUTTON_X:
			_mouse_button(MOUSE_BUTTON_RIGHT, pressed)
		JOY_BUTTON_B:
			if pressed:
				_key(KEY_ESCAPE)
		JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_DOWN:
			if pressed:
				var d := {JOY_BUTTON_DPAD_LEFT: Vector2.LEFT, JOY_BUTTON_DPAD_RIGHT: Vector2.RIGHT,
						JOY_BUTTON_DPAD_UP: Vector2.UP, JOY_BUTTON_DPAD_DOWN: Vector2.DOWN}[b] as Vector2
				_move_cursor(d * CURSOR_STEP * _ui_scale())


func _ui_scale() -> float:
	var ui = viewer.get("ui") if viewer and is_instance_valid(viewer) else null
	return float(ui.root.scale.x) if ui and ui.get("root") else 1.0


func _move_cursor(by: Vector2) -> void:
	var size := get_viewport().get_visible_rect().size
	var to := (_cursor + by).clamp(Vector2.ZERO, size - Vector2.ONE)
	if to == _cursor:
		return
	var e := InputEventMouseMotion.new()
	e.position = to
	e.global_position = to
	e.relative = to - _cursor
	e.button_mask = MOUSE_BUTTON_MASK_LEFT if _a_drag else 0
	e.set_meta("pad", true)
	_cursor = to
	Input.parse_input_event(e)
	if not _a_drag:
		get_viewport().warp_mouse(to)                      # (the window's own pointer there too: hover, tooltips)
	_arrow.queue_redraw()


func _mouse_button(button: MouseButton, pressed: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = button
	e.pressed = pressed
	e.position = _cursor
	e.global_position = _cursor
	e.button_mask = (MOUSE_BUTTON_MASK_LEFT if button == MOUSE_BUTTON_LEFT and pressed else 0)
	e.set_meta("pad", true)
	Input.parse_input_event(e)


## A key press and release, as the keyboard would send it.
func _key(k: Key, shift := false, ctrl := false, alt := false) -> void:
	for down in [true, false]:
		var e := InputEventKey.new()
		e.keycode = k
		e.physical_keycode = k
		e.pressed = down
		e.shift_pressed = shift
		e.ctrl_pressed = ctrl
		e.alt_pressed = alt
		e.set_meta("pad", true)
		Input.parse_input_event(e)


## One of the game's bindable actions, by the key it is bound to now (nothing when it has no key).
func _fire(id: String) -> void:
	for d in (Keybinds._held as Dictionary).get(id, []):
		if int(d.get("key", KEY_NONE)) != KEY_NONE:
			_key(d.key, bool(d.shift), bool(d.ctrl), bool(d.alt))
			return


# ---------------------------------------------------------------- every frame

func _process(delta: float) -> void:
	if device >= 0 and not assume_connected and not Input.get_connected_joypads().has(device):
		device = -1
		_set_active(false)
	var cursor_mode := active and not world_mode()
	if cursor_mode != _cursor_shown:
		_cursor_shown = cursor_mode
		_arrow.visible = cursor_mode
		Keybinds.pad_held.clear()                          # (a jump / a drawn shot doesn't stay held across)
		if cursor_mode:
			_cursor = get_viewport().get_mouse_position()
	if not active or device < 0:
		return
	_triggers()
	if cursor_mode:
		if Input.mouse_mode == Input.MOUSE_MODE_VISIBLE:
			Input.mouse_mode = Input.MOUSE_MODE_HIDDEN     # (the pad's own pointer is drawn instead)
		var mv := _stick(JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y)
		if bar and is_instance_valid(bar) and bar.radial_shown():
			mv = Vector2.ZERO                              # (the wheel takes the sticks)
		if mv != Vector2.ZERO:
			_move_cursor(mv * pow(mv.length(), 0.6) / maxf(mv.length(), 0.001) * CURSOR_SPEED * delta)
		var rs := _stick(JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
		var now := Time.get_ticks_msec()
		if absf(rs.y) > 0.4 and now - _scroll_at > int(SCROLL_MS / absf(rs.y)):
			_scroll_at = now
			_mouse_button(MOUSE_BUTTON_WHEEL_DOWN if rs.y > 0.0 else MOUSE_BUTTON_WHEEL_UP, true)
			_mouse_button(MOUSE_BUTTON_WHEEL_DOWN if rs.y > 0.0 else MOUSE_BUTTON_WHEEL_UP, false)
		_arrow.queue_redraw()
		return
	# Y held: the weapon out / away, once per hold
	if _down.has(JOY_BUTTON_Y) and layer == 0 and Time.get_ticks_msec() - int(_down[JOY_BUTTON_Y]) >= HOLD_Y_MS \
			and not bool(_used_in_hold.get(JOY_BUTTON_Y, false)):
		_used_in_hold[JOY_BUTTON_Y] = true
		_fire("attack_mode")
	if not _down.has(JOY_BUTTON_Y):
		_used_in_hold.erase(JOY_BUTTON_Y)
	if sprint and not moving():
		sprint = false
	_look(delta)


func _triggers() -> void:
	var rt := Input.get_joy_axis(device, JOY_AXIS_TRIGGER_RIGHT)
	var lt := Input.get_joy_axis(device, JOY_AXIS_TRIGGER_LEFT)
	var rt_on := rt >= TRIGGER_ON or (_rt and rt > TRIGGER_OFF)
	var lt_on := lt >= TRIGGER_ON or (_lt and lt > TRIGGER_OFF)
	var world := world_mode()
	if rt_on != _rt:
		_rt = rt_on
		Keybinds.pad_held["ac_shot"] = rt_on and world
		if (world or not rt_on) and ac and is_instance_valid(ac):
			ac.call("pad_attack", rt_on)
	if lt_on != _lt:
		_lt = lt_on
		Keybinds.pad_held["ac_crit_shot"] = lt_on and world
		if (world or not lt_on) and ac and is_instance_valid(ac):
			ac.call("pad_defend", lt_on)


func _look(delta: float) -> void:
	var p := _player()
	if p == null:
		return
	var rs := _stick(JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
	if bar and is_instance_valid(bar) and bar.radial_shown():
		return
	# locked on: a flick sideways is the next target that way (the camera stays on the lock)
	if ac and bool(ac.call("_locked")):
		if _flick == 0 and absf(rs.x) >= FLICK_ON:
			_flick = 1 if rs.x > 0.0 else -1
			ac.call("pad_lock_cycle", _flick)
		elif absf(rs.x) < FLICK_OFF:
			_flick = 0
		rs.x = 0.0
	if rs == Vector2.ZERO:
		return
	var curved := Vector2(signf(rs.x) * pow(absf(rs.x), LOOK_CURVE), signf(rs.y) * pow(absf(rs.y), LOOK_CURVE))
	var sens := float(p.get("mouse_sensitivity")) if p.get("mouse_sensitivity") != null else 1.0
	p.call("pad_look", curved.x * LOOK_YAW * sens * delta, curved.y * LOOK_PITCH * sens * delta)


func _release_all() -> void:
	if _rt and ac and is_instance_valid(ac):
		ac.call("pad_attack", false)
	if _lt and ac and is_instance_valid(ac):
		ac.call("pad_defend", false)
	_rt = false
	_lt = false
	Keybinds.pad_held.clear()
	if _a_drag:
		_a_drag = false
		_mouse_button(MOUSE_BUTTON_LEFT, false)
	_down.clear()
	sprint = false
	if layer != 0:
		layer = 0
		layer_changed.emit(0)
	_arrow.visible = false
	_cursor_shown = false


func _draw_arrow() -> void:
	var s := 1.4
	var pts := PackedVector2Array([Vector2(0, 0), Vector2(0, 17), Vector2(4.5, 13), Vector2(7.5, 20), Vector2(10, 19),
			Vector2(7, 12), Vector2(12.5, 12)])
	for i in pts.size():
		pts[i] = _cursor + pts[i] * s
	_arrow.draw_colored_polygon(pts, Color(0.95, 0.88, 0.62))
	var outline := pts.duplicate()
	outline.append(pts[0])
	_arrow.draw_polyline(outline, Color(0.1, 0.07, 0.03), 1.5, true)
