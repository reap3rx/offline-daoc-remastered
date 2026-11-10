extends Node
## Autoload "Pad": an Xbox-style gamepad (owner 2026-11-10: "a first pass at controller support ... only usable in
## action combat mode ... movement, menus and basic combat ... emulate WoW Forever's control scheme"). The pad and the
## mouse / keyboard take turns: the first stick push or button makes the pad the active device (its bar replaces the
## quickbars, the mouse pointer becomes a pad-driven one), the first real mouse move or key gives control back.
##
## In the world (Action Combat on - the first button turns it on) every button is a binding (Options > CONTROLS >
## CONTROLLER, owner 2026-11-10: "controller customization ... holding a button be a selectable input"): an input is a
## button, optionally with LB / RB / both held ("rb+x"), optionally held ("b:hold" - its plain binding then goes when
## you let go before HOLD_MS). Sticks: left moves (how far it's pushed is how fast you go), right looks. The defaults
## (DEFAULTS) are listed in the bindings page.
## With a window open (or the Alt cursor) the pad works the interface (owner 2026-11-10: "the cursor moving between each
## element you can interact with (indicated by highlighting that element) and then having the controls on the bottom of
## that UI element that tell you what you can do"): the d-pad jumps between the things you can use, the left stick moves
## the pointer freely, the one under it is framed with its tooltip, and a strip under its window lists what A / X / Y / B
## do there (an element may say itself: pad_actions(); otherwise A clicks, X right-clicks, Y picks it up to move, B
## closes). Carrying something, hold LB / RB / both and press a bar button to drop it on that controller slot.

signal active_changed(on: bool)
signal layer_changed(layer: int)
signal bindings_changed

const PATH := "user://pad_bindings.cfg"
const DEADZONE := 0.18
const TRIGGER_ON := 0.45
const TRIGGER_OFF := 0.3
const LOOK_YAW := 3.4                   # rad / s at full right-stick throw (x the look speed setting)
const LOOK_PITCH := 2.0
const LOOK_CURVE := 1.8                 # small throws turn finely
const CURSOR_SPEED := 1300.0            # px / s at full throw
const SCROLL_MS := 90
const FLICK_ON := 0.8                   # locked on: a right-stick flick this far picks the next target
const FLICK_OFF := 0.35
const AUTO_ON_MS := 3000

## The buttons by name (bindings, the page) and back.
const BUTTONS := {"a": JOY_BUTTON_A, "b": JOY_BUTTON_B, "x": JOY_BUTTON_X, "y": JOY_BUTTON_Y,
		"lb": JOY_BUTTON_LEFT_SHOULDER, "rb": JOY_BUTTON_RIGHT_SHOULDER, "l3": JOY_BUTTON_LEFT_STICK,
		"r3": JOY_BUTTON_RIGHT_STICK, "view": JOY_BUTTON_BACK, "menu": JOY_BUTTON_START, "up": JOY_BUTTON_DPAD_UP,
		"down": JOY_BUTTON_DPAD_DOWN, "left": JOY_BUTTON_DPAD_LEFT, "right": JOY_BUTTON_DPAD_RIGHT}
const NAMES := {"a": "A", "b": "B", "x": "X", "y": "Y", "lb": "LB", "rb": "RB", "lt": "LT", "rt": "RT", "l3": "L3",
		"r3": "R3", "view": "VIEW", "menu": "MENU", "up": "D-UP", "down": "D-DOWN", "left": "D-LEFT", "right": "D-RIGHT"}
## The eight buttons of the bar, each diamond clockwise from the left: d-pad left, up, right, down; X, Y, B, A.
const SLOTS := ["left", "up", "right", "down", "x", "y", "b", "a"]
const LAYERS := ["", "lb+", "rb+", "lb+rb+"]

## [id, label, short (the bar), kind]: "tap" goes once; "held" is down while the input is (attack, jump, the wheel ...).
const ACTIONS := [
	["jump", "Jump", "JUMP", "held"],
	["attack", "Attack (hold: power attack)", "ATTACK", "held"],
	["defend", "Parry / Block", "PARRY", "held"],
	["dodge", "Dodge", "DODGE", "tap"],
	["sprint_hold", "Sprint (while held)", "SPRINT", "held"],
	["sprint_toggle", "Sprint (toggle)", "SPRINT", "tap"],
	["style_auto", "Style (whichever is lit)", "STYLE", "tap"],
	["style_reactive", "Reactive Style", "REACT", "tap"],
	["style_position", "Positional Style", "POSITION", "tap"],
	["style_chain", "Chain Style", "CHAIN", "tap"],
	["interact", "Interact", "USE", "tap"],
	["sheathe", "Weapon In / Out", "SHEATHE", "tap"],
	["weapon_cycle", "Cycle Weapons", "WEAPON", "tap"],
	["run_lock", "Autorun", "RUN", "tap"],
	["sit", "Sit / Stand", "SIT", "tap"],
	["torch", "Torch", "TORCH", "tap"],
	["lock_on", "Lock On", "LOCK", "tap"],
	["target_enemy", "Target Nearest Enemy", "ENEMY", "tap"],
	["target_friend", "Target You / Your Group", "FRIEND", "tap"],
	["hero", "Hero Panel", "HERO", "tap"],
	["bags", "Bags", "BAGS", "tap"],
	["map", "Map", "MAP", "tap"],
	["journal", "Journal", "JOURNAL", "tap"],
	["styles_window", "Action Combat Styles", "STYLES", "tap"],
	["menu_wheel", "Menu Wheel", "MENU", "held"],
	["escape", "Esc / Close Windows", "ESC", "tap"],
]

static func _defaults() -> Dictionary:
	var d := {"a": "jump", "b": "dodge", "b:hold": "sprint_hold", "x": "style_auto", "y": "interact",
			"up": "weapon_cycle", "up:hold": "sheathe", "right": "run_lock", "down": "sit", "left": "torch",
			"l3": "sprint_toggle", "r3": "lock_on", "rt": "attack", "lt": "defend", "lb": "target_friend",
			"rb": "target_enemy", "view": "hero", "view:hold": "menu_wheel", "menu": "escape"}
	for i in 8:
		d["lb+" + SLOTS[i]] = "qb1_%d" % (i + 1)
		d["lb+rb+" + SLOTS[i]] = "qb3_%d" % (i + 1)
	for i in [0, 1, 2, 3, 7]:
		d["rb+" + SLOTS[i]] = "qb2_%d" % (i + 1)
	d["rb+x"] = "style_reactive"                       # (owner 2026-11-10: RB + X / Y / B the specific styles)
	d["rb+y"] = "style_position"
	d["rb+b"] = "style_chain"
	return d


static var assume_connected := false     # (tests: injected pad events, no pad plugged in)
var active := false                      # the pad is the device in use now
var device := -1
var layer := 0                           # 0 none, 1 LB, 2 RB, 3 both
var sprint := false                      # the sprint toggle
var sprint_held := false
var ac: Node = null                      # the Action Combat node (ActionCombatMode.setup attaches it)
var viewer: Node = null
var bar: Control = null                  # the controller bar (pad_bar.gd)
var bindings := {}                       # input -> action id
var hold_ms := 300                       # a button held this long is its ":hold" input
var look_speed := 1.0
var invert_look := false

var _down := {}                          # button name -> msec it went down
var _used_mod := {}                      # "lb" / "rb": another button went while it was held
var _pending := {}                       # button name -> [input (with mods), its hold fired]
var _held_actions := {}                  # button name -> [action] down now (to let go on release)
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
var _overlay: Control
var _a_drag := false                     # the pointer's left button is down (a click held, or carrying)
var _carrying := false
var _stick_was := false
var _capture: Callable                   # the bindings page waiting for a press
var _cap_mods := ""
var _cap_button := ""
var _cap_at := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_layer = CanvasLayer.new()
	_layer.layer = 128
	add_child(_layer)
	_overlay = Control.new()
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.draw.connect(_draw_overlay)
	_layer.add_child(_overlay)
	load_bindings()
	var cfg := ConfigFile.new()
	cfg.load("user://settings.cfg")
	hold_ms = int(cfg.get_value("pad", "hold_ms", 300))
	look_speed = float(cfg.get_value("pad", "look_speed", 1.0))
	invert_look = bool(cfg.get_value("pad", "invert_look", false))


# ---------------------------------------------------------------- bindings

func load_bindings() -> void:
	bindings = _defaults()
	var cfg := ConfigFile.new()
	if cfg.load(PATH) == OK and cfg.has_section("bindings"):
		bindings = {}
		for k in cfg.get_section_keys("bindings"):
			var a := String(cfg.get_value("bindings", k, ""))
			if a != "":
				bindings[k] = a
	bindings_changed.emit()


func save_bindings() -> void:
	var cfg := ConfigFile.new()
	for k in bindings:
		cfg.set_value("bindings", k, bindings[k])
	cfg.set_value("meta", "version", 1)
	cfg.save(PATH)
	bindings_changed.emit()


func reset_bindings() -> void:
	bindings = _defaults()
	save_bindings()


## Bind an input to an action (one input does one thing: whatever had it loses it - returned, "" if nothing).
func bind(input: String, action: String) -> String:
	var old := String(bindings.get(input, ""))
	if action == "":
		bindings.erase(input)
	else:
		bindings[input] = action
	save_bindings()
	return old if old != action else ""


func unbind_action(action: String) -> void:
	for k in bindings.keys():
		if bindings[k] == action:
			bindings.erase(k)
	save_bindings()


## The inputs bound to an action, in a steady order.
func inputs_of(action: String) -> Array:
	var out := []
	for k in bindings:
		if bindings[k] == action:
			out.append(k)
	out.sort()
	return out


## Why a controller input can't hold a skill ("" when it can): a button bound to anything but a quickbar slot is a core
## button (owner 2026-11-10: "not let the player place skills ... onto core buttons"); holds, triggers, the bumpers on
## their own, the sticks' clicks and View / Menu are never slots.
func slot_refusal(input: String) -> String:
	if input.ends_with(":hold") or input in ["lt", "rt", "lb", "rb", "l3", "r3", "view", "menu"] \
			or input.ends_with("+l3") or input.ends_with("+r3"):
		return "%s CAN'T HOLD A SKILL - USE THE D-PAD OR A FACE BUTTON, WITH LB / RB FOR MORE." % describe(input)
	var act := String(bindings.get(input, ""))
	if act != "" and not act.begins_with("qb"):
		return "%s IS FOR %s - PICK ANOTHER (OR REBIND IT IN THE CONTROLLER OPTIONS)." % [describe(input),
				String(action_info(act)[1]).to_upper()]
	var hold := String(bindings.get(input + ":hold", ""))
	if act == "" and hold != "":
		return "%s IS FOR %s WHEN HELD - PICK ANOTHER." % [describe(input), String(action_info(hold)[1]).to_upper()]
	return ""


## The quickbar (bar, slot) an input's skill goes in: the slot it is bound to, or - allocate - the first quickbar slot
## no controller button uses yet, its own slot empty (bar 3 first: the keyboard's bars stay as they are), bound to it.
func slot_for_input(input: String, allocate := false) -> Vector2i:
	var act := String(bindings.get(input, ""))
	if act.begins_with("qb"):
		var f := act.trim_prefix("qb").split("_")
		return Vector2i(int(f[0]) - 1, int(f[1]) - 1)
	if not allocate:
		return Vector2i(-1, -1)
	var used := {}
	for k in bindings:
		used[bindings[k]] = true
	for b in [2, 1, 0]:
		for sl in 10:
			var id := "qb%d_%d" % [b + 1, sl + 1]
			if used.has(id):
				continue
			if not (PlayerData.quickbars[b][PlayerData.quickbar_bank[b]][sl] as Dictionary).is_empty():
				continue
			bind(input, id)
			return Vector2i(b, sl)
	return Vector2i(-1, -1)


## "rb+x:hold" -> "HOLD RB + X".
static func describe(input: String) -> String:
	var hold := input.ends_with(":hold")
	var parts := input.trim_suffix(":hold").split("+")
	var names := []
	for p in parts:
		names.append(String(NAMES.get(p, p.to_upper())))
	return ("HOLD " if hold else "") + " + ".join(names)


static func action_info(id: String) -> Array:
	for a in ACTIONS:
		if a[0] == id:
			return a
	if id.begins_with("qb"):
		var f := id.trim_prefix("qb").split("_")
		return [id, "Quickbar %s Slot %s" % [f[0], f[1]], "", "tap"]
	return [id, id, id.to_upper(), "tap"]


## The bindings page: the next press (with LB / RB held first for a combo, held for a hold) goes to `done(input)`.
func capture(done: Callable) -> void:
	_capture = done
	_cap_button = ""


func capturing() -> bool:
	return _capture.is_valid()


func cancel_capture() -> void:
	_capture = Callable()
	_cap_button = ""


func _player() -> Node:
	return viewer.get("player") if viewer and is_instance_valid(viewer) else null


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


func _ui():
	return viewer.get("ui") if viewer and is_instance_valid(viewer) else null


## In the world with Action Combat on, the pointer away: the pad fights. Otherwise it works the interface.
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


func sprinting() -> bool:
	return (sprint or sprint_held) and moving()


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
		var name := _name_of(event.button_index)
		if name != "":
			_button(name, event.pressed)
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


func _name_of(b: JoyButton) -> String:
	for k in BUTTONS:
		if BUTTONS[k] == b:
			return k
	return ""


func _mods() -> String:
	var lb := _down.has("lb")
	var rb := _down.has("rb")
	return "lb+rb+" if lb and rb else ("lb+" if lb else ("rb+" if rb else ""))


func _button(name: String, pressed: bool) -> void:
	var now := Time.get_ticks_msec()
	if pressed:
		if _down.has(name):
			return
		_down[name] = now
		for m in ["lb", "rb"]:
			if m != name and _down.has(m):
				_used_mod[m] = true
	var since := now - int(_down.get(name, now))
	if not pressed:
		_down.erase(name)
	if _capture.is_valid():
		_capture_button(name, pressed, since)
		return
	if name in ["lb", "rb"]:
		if pressed:
			_used_mod[name] = false
		elif not bool(_used_mod.get(name, false)) and since < hold_ms and world_mode():
			_run(name, "tap")                              # a bumper tapped on its own
		_set_layer()
		return
	var world := world_mode()
	if not world and name in ["a", "b", "x", "y", "up", "down", "left", "right"]:
		_ui_button(name, pressed)
		if pressed and _player() and Server.playing and ac and not bool(ac.get("on")) and not bool(_player().get("action_cursor")) \
				and now - _auto_at > AUTO_ON_MS:
			_auto_at = now                                 # the pad plays in Action Combat: a button in the world turns it on
			ac.call("_toggle")
		return
	_bound_button(name, pressed, since)


func _set_layer() -> void:
	var l := (1 if _down.has("lb") else 0) + (2 if _down.has("rb") else 0)
	if l != layer:
		layer = l
		layer_changed.emit(layer)


## A bound button: its input with the bumpers held; a hold binding waits to see which it is.
func _bound_button(name: String, pressed: bool, since: int) -> void:
	if pressed:
		var input := _mods() + name
		if bindings.has(input + ":hold"):
			_pending[name] = [input, false]                # tap or hold: decided by the release or the clock (_process)
			return
		var act := String(bindings.get(input, ""))
		if act != "":
			_start(name, act)
		return
	if _pending.has(name):
		var p: Array = _pending[name]
		_pending.erase(name)
		if not bool(p[1]):
			var act := String(bindings.get(String(p[0]), ""))
			if act != "":
				_run(String(p[0]), "tap")                  # let go before the hold: its plain binding, start to finish
				return
	_finish(name)


func _start(name: String, act: String) -> void:
	if String(action_info(act)[3]) == "held":
		_held_actions[name] = act
		_do(act, true)
	else:
		_do(act, true)


func _finish(name: String) -> void:
	if _held_actions.has(name):
		var act := String(_held_actions[name])
		_held_actions.erase(name)
		_do(act, false)


## An input's action from start to finish at once (a tap; a held action pressed for a moment).
func _run(input: String, _how: String) -> void:
	var act := String(bindings.get(input, ""))
	if act == "":
		return
	_do(act, true)
	if String(action_info(act)[3]) == "held":
		get_tree().create_timer(0.12).timeout.connect(func(): _do(act, false))


func _check_holds() -> void:
	var now := Time.get_ticks_msec()
	for name in _pending.keys():
		var p: Array = _pending[name]
		if not bool(p[1]) and _down.has(name) and now - int(_down[name]) >= hold_ms:
			p[1] = true
			var act := String(bindings.get(String(p[0]) + ":hold", ""))
			if act != "":
				_start(name, act)


## What an action does: down = true when it starts (a tap's only call), false when a held one ends.
func _do(act: String, down: bool) -> void:
	var a = ac if ac and is_instance_valid(ac) else null
	if act.begins_with("qb"):
		if down:
			var f := act.trim_prefix("qb").split("_")
			_use_slot(int(f[0]) - 1, int(f[1]) - 1)
		return
	match act:
		"jump":
			Keybinds.pad_held["jump"] = down
		"attack":
			Keybinds.pad_held["ac_shot"] = down
			if a:
				a.call("pad_attack", down)
		"defend":
			Keybinds.pad_held["ac_crit_shot"] = down
			if a:
				a.call("pad_defend", down)
		"sprint_hold":
			sprint_held = down
		"menu_wheel":
			if bar and is_instance_valid(bar):
				if down:
					bar.radial_open()
				else:
					bar.radial_close()
	if not down:
		return
	match act:
		"dodge":
			if a:
				var mv := _stick(JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y)
				a.call("pad_dodge", Vector3(mv.x, 0.0, mv.y))
		"sprint_toggle":
			sprint = not sprint
		"style_auto":
			if a:
				a.call("pad_style")
		"style_reactive", "style_position", "style_chain":
			if a:
				a.call("pad_style", act.trim_prefix("style_"))
		"interact":
			if a:
				a.call("pad_interact")
		"sheathe":
			_fire("attack_mode")
		"weapon_cycle":
			_fire("weapon_cycle")
		"run_lock":
			_fire("run_lock")
		"sit":
			_fire("sit")
		"torch":
			_fire("torch")
		"lock_on":
			if a:
				a.call("pad_lock_tap")
		"target_enemy":
			_fire("target_enemy")
		"target_friend":
			_next_friend()
		"hero":
			_open("hero")
		"bags":
			_open("bags")
		"map":
			_open("map")
		"journal":
			_open("journal")
		"styles_window":
			_open("ac_styles")
		"escape":
			if _carrying:
				_cancel_carry()
			else:
				_key(KEY_ESCAPE)


func _open(id: String) -> void:
	if bar and is_instance_valid(bar):
		bar.open_window(id)


## LB tapped: you, then each of your group in turn (the Target Group #1-8 keys); after a pause it starts with you again.
func _next_friend() -> void:
	var now := Time.get_ticks_msec()
	var n := clampi(PlayerData.group.size(), 1, 8)
	_group_pick = 0 if now - _group_pick_at > 4000 else (_group_pick + 1) % n
	_group_pick_at = now
	_fire("target_group_%d" % (_group_pick + 1))


func _use_slot(qbar: int, slot: int) -> void:
	var ui = _ui()
	if ui == null:
		return
	var bars: Array = ui.get("quickbars")
	if qbar < bars.size() and slot < 10:
		bars[qbar].use_slot(slot)
		if bar and is_instance_valid(bar):
			bar.flash("qb%d_%d" % [qbar + 1, slot + 1])


func _capture_button(name: String, pressed: bool, since: int) -> void:
	if name in ["lb", "rb"]:
		if pressed:
			_used_mod[name] = false
			_set_layer()
			return
		_set_layer()
		if not bool(_used_mod.get(name, false)) and _cap_button == "":
			_finish_capture(name)                          # a bumper on its own
		return
	if pressed:
		_cap_mods = _mods()
		_cap_button = name
		_cap_at = Time.get_ticks_msec()
		if name in ["l3", "r3", "view", "menu"] and _cap_mods != "":
			_cap_mods = ""                                 # (combos are for the bar's eight buttons)
		return
	if name == _cap_button:
		_finish_capture(_cap_mods + name + (":hold" if since >= hold_ms else ""))


func _finish_capture(input: String) -> void:
	var cb := _capture
	_capture = Callable()
	_cap_button = ""
	if cb.is_valid():
		cb.call(input)


# ---------------------------------------------------------------- the interface

func _ui_button(name: String, pressed: bool) -> void:
	var dirs := {"left": Vector2.LEFT, "right": Vector2.RIGHT, "up": Vector2.UP, "down": Vector2.DOWN}
	# carrying something: LB / RB held and a bar button drops it on that controller slot
	if pressed and _carrying and layer > 0 and name in SLOTS and bar and is_instance_valid(bar):
		var cell: Control = bar.cell_for(LAYERS[layer] + name)
		if cell and cell.is_visible_in_tree():
			_point_at(cell)
			_release_left()
		return
	if dirs.has(name):
		if pressed:
			_nav(dirs[name])
		return
	var f := focused()
	var acts := actions_for(f)
	for e in acts:
		if String(e[0]) == name and e.size() > 2 and (e[2] as Callable).is_valid():
			if pressed:
				(e[2] as Callable).call()
			return
	match name:
		"a":
			if _carrying:
				if not pressed:
					_release_left()
			else:
				_a_drag = pressed
				_mouse_button(MOUSE_BUTTON_LEFT, pressed)
		"x":
			_mouse_button(MOUSE_BUTTON_RIGHT, pressed)
		"y":
			if pressed and f and not _carrying and _scripted(f, "_get_drag_data"):
				_pick_up(f)
		"b":
			if pressed:
				if _carrying:
					_cancel_carry()
				else:
					_key(KEY_ESCAPE)


## What the element under the pointer offers: [[button, label, Callable or null]] - its own pad_actions(), else the
## usual click / right-click / pick up / close.
func actions_for(f: Control) -> Array:
	var out := []
	if _carrying:
		out = [["a", "PLACE"], ["b", "CANCEL"]]
		if bar and is_instance_valid(bar) and bar.visible:
			out.append(["lb", "LB / RB + BUTTON: ONTO THE BAR"])
		return out
	if f == null:
		return [["b", "CLOSE"]]
	if f.has_method("pad_actions"):
		out = f.call("pad_actions")
	else:
		if f is Slider:
			out.append(["a", "HOLD A AND MOVE"])
		elif f is BaseButton or _scripted(f, "_gui_input") or f is LineEdit or f is ItemList:
			out.append(["a", "SELECT"])
		if _scripted(f, "_get_drag_data"):
			out.append(["y", "MOVE"])
	var has_b := false
	for e in out:
		if String(e[0]) == "b":
			has_b = true
	if not has_b:
		out.append(["b", "CLOSE"])
	return out


## A bag / worn item's buttons (the modern bags' cells, the classic backpack rows and worn slots - owner 2026-11-10:
## "A equip, Y drop, B sell"): A wears it (or uses it; a worn one comes off), X picks it up to move, Y drops it (asked
## first), B sells it while a merchant is open.
func item_actions(slot: int) -> Array:
	var it := PlayerData.item_at(slot)
	if it.is_empty():
		return []
	var ui = _ui()
	var out := []
	var pack := PlayerData.is_backpack(slot)
	if not pack:
		out.append(["a", "REMOVE", func(): PlayerData.unequip(slot)])
	elif not PlayerData.slots_for(it).is_empty():
		out.append(["a", "EQUIP", func(): PlayerData.equip(slot)])
	elif Server.active:
		out.append(["a", "USE", func(): Server.use("srv:%d" % slot)])
	out.append(["x", "MOVE", func(): _pick_up(focused())])
	if pack and ui:
		out.append(["y", "DROP", _drop_asked.bind(slot)])
	var m = ui.get("merchant") if ui else null
	if pack and m and is_instance_valid(m) and m.visible:
		out.append(["b", "SELL", func(): PlayerData.sell(slot, String(m.npc_name))])
	return out


func _drop_asked(slot: int) -> void:
	var ui = _ui()
	if ui == null:
		return
	var name := String(PlayerData.item_at(slot).get("name", "item"))
	UiArt.confirm(ui.root, "DROP", "Drop the %s?" % name, "DROP", "KEEP",
			func(): ui.item_dropped_on_world.emit(slot, Vector2(1, 1)))


## Pick up what's under the pointer, as a press and a little pull with the left button: the game's own drag then
## carries it until A puts it down (or B / Esc lets it go back).
func _pick_up(f: Control) -> void:
	if f == null:
		return
	_point_at(f)
	_a_drag = true
	_carrying = true
	_mouse_button(MOUSE_BUTTON_LEFT, true)
	var at := _cursor
	await get_tree().process_frame                         # (moves in one frame are merged: each its own frame)
	_move_cursor(Vector2(14, 0), true)
	await get_tree().process_frame
	_move_cursor(at - _cursor, true)
	await get_tree().process_frame
	if not get_viewport().gui_is_dragging():
		_release_left()                                    # (nothing came up with it)


func _release_left() -> void:
	_mouse_button(MOUSE_BUTTON_LEFT, false)
	_a_drag = false
	_carrying = false


func _cancel_carry() -> void:
	get_viewport().gui_cancel_drag()
	_release_left()


func _ui_scale() -> float:
	var ui = _ui()
	return float(ui.root.scale.x) if ui and ui.get("root") else 1.0


## The element the pointer is on: the control under it, or the nearest of its parents that can be used.
func focused() -> Control:
	var c := get_viewport().gui_get_hovered_control()
	while c:
		if _usable(c):
			return c
		if c is ClassicWindow:
			return null
		c = c.get_parent() as Control
	return null


func _usable(c: Control) -> bool:
	if not c.is_visible_in_tree() or c.mouse_filter != Control.MOUSE_FILTER_STOP or c is ClassicWindow \
			or c is ScrollContainer or c is ScrollBar:
		return false
	var s := c.size * c.get_global_transform_with_canvas().get_scale()
	var wide := 1400.0 if c is BaseButton else 520.0         # (a button the width of its page still counts)
	if s.x < 6.0 or s.y < 6.0 or s.x > wide or s.y > 260.0:
		return false
	return c is BaseButton or c is LineEdit or c is Slider or c is ItemList or c.has_method("pad_actions") \
			or _scripted(c, "_get_drag_data") or _scripted(c, "_gui_input") or c.tooltip_text != ""


static var _script_methods := {}


## A method the control's own script defines (Control's virtuals are there on every control).
static func _scripted(c: Object, m: String) -> bool:
	var sc = c.get_script()
	if sc == null:
		return false
	if not _script_methods.has(sc):
		var names := {}
		for d in (sc as Script).get_script_method_list():
			names[String(d.name)] = true
		_script_methods[sc] = names
	return (_script_methods[sc] as Dictionary).has(m)


func _screen_rect(c: Control) -> Rect2:
	return c.get_global_transform_with_canvas() * Rect2(Vector2.ZERO, c.size)


## Every element that can be used in the open windows (and the controller bar): the d-pad's targets.
func _usables() -> Array:
	var out := []
	var vp := get_viewport().get_visible_rect()
	var ui = _ui()
	var stack: Array = [ui] if ui else [get_tree().root]       # (in the world: the interface only, not the scene)
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if (n is CanvasItem and not (n as CanvasItem).visible) or (n is CanvasLayer and not (n as CanvasLayer).visible):
			continue
		if n is Control and _usable(n as Control):
			var r := _screen_rect(n as Control)
			if vp.intersects(r):
				out.append(n)
		for ch in n.get_children():
			stack.append(ch)
	return out


func _window_of(c: Control) -> ClassicWindow:
	var n: Node = c
	while n:
		if n is ClassicWindow:
			return n
		n = n.get_parent()
	return null


## The d-pad in a window: the nearest usable element that way (its own window first).
func _nav(dir: Vector2) -> void:
	var here := _cursor
	var cur := focused()
	if cur == null and is_instance_valid(_last_focus) and _last_focus.is_visible_in_tree():
		cur = _last_focus                                  # (carrying: the pointer's control is the drag's)
	if cur:
		here = _screen_rect(cur).get_center()
	var win := _window_of(cur) if cur else null
	var best: Control = null
	var best_score := INF
	for c in _usables():
		if c == cur:
			continue
		var d: Vector2 = _screen_rect(c).get_center() - here
		var along := d.dot(dir)
		if along < 6.0:
			continue
		var side := absf(d.cross(dir))
		if side > along * 2.5:
			continue                                       # (well off to the side: not "that way")
		var score := along + side * 2.0 + (0.0 if win == null or _window_of(c) == win else 400.0)
		if score < best_score:
			best_score = score
			best = c
	if best:
		_point_at(best)


var _last_focus: Control = null


func _point_at(c: Control) -> void:
	_last_focus = c
	_move_cursor(_screen_rect(c).get_center() - _cursor)


func _move_cursor(by: Vector2, force := false) -> void:
	var size := get_viewport().get_visible_rect().size
	var to := (_cursor + by).clamp(Vector2.ZERO, size - Vector2.ONE)
	if to == _cursor and not force:
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
	_overlay.queue_redraw()


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
		Keybinds.pad_held.clear()                          # (a jump / a drawn shot doesn't stay held across)
		for n in _held_actions.keys():
			_finish(n)
		_pending.clear()
		if cursor_mode:
			_cursor = get_viewport().get_mouse_position()
	_overlay.visible = cursor_mode
	if not active or device < 0:
		return
	_check_holds()
	_triggers()
	if cursor_mode:
		if Input.mouse_mode == Input.MOUSE_MODE_VISIBLE:
			Input.mouse_mode = Input.MOUSE_MODE_HIDDEN     # (the pad's own pointer is drawn instead)
		var mv := _stick(JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y)
		if bar and is_instance_valid(bar) and bar.radial_shown():
			mv = Vector2.ZERO                              # (the wheel takes the sticks)
		if mv != Vector2.ZERO:
			_move_cursor(mv * pow(mv.length(), 0.6) / maxf(mv.length(), 0.001) * CURSOR_SPEED * delta)
		elif _stick_was and focused() == null:
			_snap_near()                                   # let go of the stick near something: onto it
		_stick_was = mv != Vector2.ZERO
		var rs := _stick(JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
		var now := Time.get_ticks_msec()
		if absf(rs.y) > 0.4 and now - _scroll_at > int(SCROLL_MS / absf(rs.y)):
			_scroll_at = now
			_mouse_button(MOUSE_BUTTON_WHEEL_DOWN if rs.y > 0.0 else MOUSE_BUTTON_WHEEL_UP, true)
			_mouse_button(MOUSE_BUTTON_WHEEL_DOWN if rs.y > 0.0 else MOUSE_BUTTON_WHEEL_UP, false)
		_overlay.queue_redraw()
		return
	if sprint and not moving():
		sprint = false
	_look(delta)


func _snap_near() -> void:
	var best: Control = null
	var bd := 48.0
	for c in _usables():
		var d := _screen_rect(c).get_center().distance_to(_cursor)
		if d < bd:
			bd = d
			best = c
	if best:
		_point_at(best)


func _triggers() -> void:
	var rt := Input.get_joy_axis(device, JOY_AXIS_TRIGGER_RIGHT)
	var lt := Input.get_joy_axis(device, JOY_AXIS_TRIGGER_LEFT)
	var rt_on := rt >= TRIGGER_ON or (_rt and rt > TRIGGER_OFF)
	var lt_on := lt >= TRIGGER_ON or (_lt and lt > TRIGGER_OFF)
	for t in [["rt", rt_on, _rt], ["lt", lt_on, _lt]]:
		if t[1] == t[2]:
			continue
		if t[0] == "rt":
			_rt = rt_on
		else:
			_lt = lt_on
		if _capture.is_valid():
			if t[1]:
				_finish_capture(String(t[0]))
			continue
		if t[1] and not world_mode():
			continue                                       # (not in a window)
		var act := String(bindings.get(String(t[0]), ""))
		if act == "":
			continue
		if t[1]:
			_start(String(t[0]), act)
		else:
			_finish(String(t[0]))


func _look(delta: float) -> void:
	var p := _player()
	if p == null:
		return
	var rs := _stick(JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
	if bar and is_instance_valid(bar) and bar.radial_shown():
		return
	# locked on: a flick sideways is the next target that way (the camera stays on the lock)
	if ac and is_instance_valid(ac) and bool(ac.call("_locked")):
		if _flick == 0 and absf(rs.x) >= FLICK_ON:
			_flick = 1 if rs.x > 0.0 else -1
			ac.call("pad_lock_cycle", _flick)
		elif absf(rs.x) < FLICK_OFF:
			_flick = 0
		rs.x = 0.0
	if rs == Vector2.ZERO:
		return
	var curved := Vector2(signf(rs.x) * pow(absf(rs.x), LOOK_CURVE), signf(rs.y) * pow(absf(rs.y), LOOK_CURVE))
	if invert_look:
		curved.y = -curved.y
	p.call("pad_look", curved.x * LOOK_YAW * look_speed * delta, curved.y * LOOK_PITCH * look_speed * delta)


func _release_all() -> void:
	for n in _held_actions.keys():
		_finish(n)
	_rt = false
	_lt = false
	Keybinds.pad_held.clear()
	if _a_drag:
		if _carrying:
			get_viewport().gui_cancel_drag()
		_release_left()
	_down.clear()
	_pending.clear()
	sprint = false
	sprint_held = false
	if layer != 0:
		layer = 0
		layer_changed.emit(0)
	_cursor_shown = false
	_overlay.visible = false


# ---------------------------------------------------------------- the pointer, the frame, the hints

const GLYPH_COLORS := {"a": Color(0.38, 0.74, 0.25), "b": Color(0.86, 0.25, 0.2), "x": Color(0.26, 0.5, 0.95),
		"y": Color(0.95, 0.78, 0.2)}


static func glyph(ci: CanvasItem, at: Vector2, button: String, r := 7.0) -> void:
	var font := UiArt.font()
	var col: Color = GLYPH_COLORS.get(button, Color(0.62, 0.6, 0.56))
	ci.draw_circle(at, r, Color(0.05, 0.05, 0.05, 0.9))
	ci.draw_circle(at, r - 1.0, col)
	var t: String = {"up": "^", "down": "v", "left": "<", "right": ">"}.get(button, String(NAMES.get(button, button)))
	var fs := int(r * 1.3)
	var w := font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	ci.draw_string(font, at + Vector2(-w * 0.5, fs * 0.38), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(0.05, 0.05, 0.05))


func _draw_overlay() -> void:
	var f := focused()
	if f and not _carrying:
		var r := _screen_rect(f).grow(2.0)
		_overlay.draw_rect(r, Color(1.0, 0.85, 0.4, 0.12))
		_overlay.draw_rect(r, Color(1.0, 0.85, 0.4, 0.95), false, 2.0)
	_draw_hints(f)
	var s := 1.4
	var pts := PackedVector2Array([Vector2(0, 0), Vector2(0, 17), Vector2(4.5, 13), Vector2(7.5, 20), Vector2(10, 19),
			Vector2(7, 12), Vector2(12.5, 12)])
	for i in pts.size():
		pts[i] = _cursor + pts[i] * s
	_overlay.draw_colored_polygon(pts, Color(0.95, 0.88, 0.62))
	var outline := pts.duplicate()
	outline.append(pts[0])
	_overlay.draw_polyline(outline, Color(0.1, 0.07, 0.03), 1.5, true)


## The strip under the element's window: what each button does here.
func _draw_hints(f: Control) -> void:
	var acts := actions_for(f)
	if acts.is_empty():
		return
	var font := UiArt.font()
	var fs := int(round(10.0 * maxf(1.0, _ui_scale())))
	var r := 8.0 * maxf(1.0, _ui_scale())
	var w := 0.0
	for e in acts:
		w += r * 2.0 + 4.0 + font.get_string_size(String(e[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 14.0
	var anchor := Rect2(_cursor, Vector2(1, 1))
	var win := _window_of(f) if f else null
	if win and win.is_visible_in_tree():
		anchor = _screen_rect(win)
	elif f:
		anchor = _screen_rect(f)
	var vp := get_viewport().get_visible_rect().size
	var h := r * 2.0 + 8.0
	var at := Vector2(anchor.get_center().x - w * 0.5, anchor.end.y + 4.0)
	if at.y + h > vp.y:
		at.y = anchor.position.y - h - 4.0                 # (no room under it: over it)
	at = at.clamp(Vector2.ZERO, (vp - Vector2(w, h)).max(Vector2.ZERO))
	_overlay.draw_rect(Rect2(at, Vector2(w, h)), Color(0.06, 0.055, 0.05, 0.92))
	_overlay.draw_rect(Rect2(at, Vector2(w, h)), Color(0.62, 0.5, 0.28), false, 1.0)
	var x := at.x + 8.0
	for e in acts:
		glyph(_overlay, Vector2(x + r, at.y + h * 0.5), String(e[0]), r)
		x += r * 2.0 + 4.0
		_overlay.draw_string(font, Vector2(x, at.y + h * 0.5 + fs * 0.36), String(e[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs,
				UiArt.CREAM)
		x += font.get_string_size(String(e[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 14.0
