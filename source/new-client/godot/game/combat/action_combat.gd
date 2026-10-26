extends Node
## Action Combat (owner 2026-10-26): an opt-in way to fight in melee on the server (game/../server ActionCombat.cs),
## for you only - monsters, gamebots and companions keep the classic rules, and F9 puts you back on them.
##   The mouse always looks and you face where you look (Alt held: the cursor, for the interface); A/D strafe.
##   Left mouse: click = one swing (the weapon's timer still paces it; one click buffers). Hold past HOLD_S and let
##     go = your best anytime style.
##   Right mouse: press = a timed parry (a block with a shield) - the 0.25 s window opens at the press; keep it held
##     = guard (less damage, slower, costs endurance per blow).
##   Q / E / R (rebindable, Options > Controls > Combat): your best usable Position / Reactive / Chain style.
##   Dodge: double-tap A, D or S (or the Dodge key) - a hop and an evade window.
## The HUD: a crosshair; a ring closing in on it when a monster winds up a blow at you (gold = parry now); the
## charge of a held click; the swing timer; the Position / Reactive / Chain lights; what your defense did.
## The server talks to it in "#AC|..." system lines (ServerWorld takes them out of the chat).

const HOLD_S := 0.3                    # a click held this long is an anytime style
const GUARD_AFTER_S := 0.18            # a right press held this long becomes guard
const DOUBLE_TAP_MS := 260
const DODGE_COOLDOWN_MS := 1200
const SOFT_RANGE_M := 12.0             # soft targeting: the monster nearest your aim within this ...
const SOFT_ANGLE := 40.0               # ... and this many degrees of it
const KEEP_ANGLE := 70.0               # your current target is kept while it stays this close to your aim
const PARRY_WINDOW_MS := 250

## npc oid -> msec: its blow's swing was already played at the wind-up (ServerWorld skips the second one)
static var _swung_early := {}

var viewer: Node
var on := false
var _queried := false
var _announced := false
var _lmb_down := false
var _lmb_at := 0
var _rmb_down := false
var _rmb_at := 0
var _guarding := false
var _taps := {}
var _dodge_ready_at := 0
var _ready := "0000"
var _timer_until := 0
var _timer_len := 1
var _windups: Array = []               # [{oid, start, end}]
var _flash_text := ""
var _flash_color := Color.WHITE
var _flash_until := 0
var _marks := {}                       # oid -> Label3D "!" over a monster winding up
var _layer: CanvasLayer
var hud: Control


static func swung_early(oid: int) -> bool:
	return int(_swung_early.get(oid, 0)) > Time.get_ticks_msec()


func setup(v: Node) -> void:
	viewer = v
	_layer = CanvasLayer.new()
	_layer.layer = 5
	add_child(_layer)
	hud = Control.new()
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.draw.connect(_draw_hud)
	_layer.add_child(hud)
	hud.visible = false


func _exit_tree() -> void:
	if on and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _player() -> Player:
	return viewer.player if viewer else null


func _typing() -> bool:
	var p := _player()
	return p != null and p._ui_typing()


# ---------------------------------------------------------------- the server's lines

func on_line(text: String) -> void:
	var f := text.split("|")
	var now := Time.get_ticks_msec()
	match String(f[0]):
		"mode":
			_set_on(f.size() > 1 and f[1] == "1")
		"ready":
			if f.size() > 1:
				_ready = String(f[1])
		"timer":
			if f.size() > 1:
				_timer_len = maxi(1, int(f[1]))
				_timer_until = now + _timer_len
		"whiff":
			var p := _player()
			if p:
				p.swing(p.weapon_stance())                   # out of reach: the blow cuts air
		"windup":
			if f.size() > 2:
				_windup(int(f[1]), int(f[2]))
		"def":
			if f.size() > 2:
				_defended(String(f[1]), int(f[2]))
		"fumble":
			_flash("STUMBLE", Color(1.0, 0.35, 0.3))
			var p := _player()
			if p:
				p.cam_kick = -0.05


func _set_on(v: bool) -> void:
	var was := on
	on = v
	var p := _player()
	if p:
		p.action_mode = on
		p.guard_mult = 1.0
		if not on:
			p.action_cursor = false
	_guarding = false
	_lmb_down = false
	_rmb_down = false
	hud.visible = on
	if not on and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if _announced and was != on and viewer and viewer.ui:
		viewer.ui.center_message("Action Combat ON" if on else "Action Combat OFF", true)
	_announced = true


func _windup(oid: int, ms: int) -> void:
	var now := Time.get_ticks_msec()
	_windups.append({"oid": oid, "start": now, "end": now + ms})
	_swung_early[oid] = now + ms + 400
	var by_oid = viewer.npcs.get("by_oid") if viewer and viewer.npcs else null
	var st = (by_oid as Dictionary).get(oid) if by_oid is Dictionary else null
	var n: Npc = st.view as Npc if st and st.view is Npc else null
	if n == null:
		return
	# the blow is drawn so it lands as the server lands it: the swing starts a little into the wind-up
	get_tree().create_timer(maxf(0.0, (ms - 450) / 1000.0)).timeout.connect(func():
		if is_instance_valid(n) and n.is_alive():
			n.play_attack())
	var mark: Label3D = _marks.get(oid)
	if mark == null or not is_instance_valid(mark):
		mark = Label3D.new()
		mark.text = "!"
		mark.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		mark.no_depth_test = true
		mark.font_size = 96
		mark.outline_size = 18
		mark.pixel_size = 0.006
		mark.modulate = Color(1.0, 0.25, 0.15)
		n.add_child(mark)
		_marks[oid] = mark
	mark.position = Vector3(0, n.height + 0.5, 0)
	mark.set_meta("until", now + ms + 150)
	mark.visible = true


func _defended(kind: String, dmg: int) -> void:
	match kind:
		"parry":
			_flash("PARRY  -%d" % dmg if dmg > 0 else "PARRY", Color(1.0, 0.85, 0.35))
		"block":
			_flash("BLOCK  -%d" % dmg if dmg > 0 else "BLOCK", Color(0.55, 0.8, 1.0))
		"dodge":
			_flash("DODGE", Color(0.55, 1.0, 0.6))
		"guard":
			_flash("GUARD  -%d" % dmg, Color(0.8, 0.8, 0.8))
		"tired":
			_flash("TOO TIRED", Color(1.0, 0.4, 0.3))
	var now := Time.get_ticks_msec()
	_windups = _windups.filter(func(w): return int(w.end) > now + 120)   # that blow is answered


func _flash(text: String, color: Color) -> void:
	_flash_text = text
	_flash_color = color
	_flash_until = Time.get_ticks_msec() + 900


## A blow of yours landed (ServerWorld's combat animation): the camera takes a small jolt - the weight of it.
func on_my_hit(styled: bool) -> void:
	var p := _player()
	if on and p:
		p.cam_kick = -0.035 if styled else -0.02


# ---------------------------------------------------------------- input

func _toggle() -> void:
	Server.command("/ac toggle")


func _input(event: InputEvent) -> void:
	var p := _player()
	if p == null or not Server.playing:
		return
	if event is InputEventKey and not event.echo and Keybinds.pressed(event, "action_toggle") and not _typing():
		_toggle()
		get_viewport().set_input_as_handled()
		return
	if not on or _typing() or not p.input_enabled or p.dead:
		return
	var now := Time.get_ticks_msec()
	if event is InputEventMouseButton and not p.action_cursor:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				_lmb_down = true
				_lmb_at = now
				_soft_target()
			elif _lmb_down:
				_lmb_down = false
				_soft_target()
				if now - _lmb_at < int(HOLD_S * 1000.0):
					Server.command("/ac swing")
				else:
					Server.command("/ac style anytime")
			get_viewport().set_input_as_handled()
			return
		if event.button_index == MOUSE_BUTTON_RIGHT:
			if event.pressed:
				_rmb_down = true
				_rmb_at = now
				Server.command("/ac parry")
			else:
				_rmb_down = false
				_end_guard()
			get_viewport().set_input_as_handled()
			return
	if not (event is InputEventKey or event is InputEventMouseButton) or not event.is_pressed() or event.is_echo():
		return
	for kind in ["position", "reactive", "chain"]:
		if Keybinds.pressed(event, "ac_" + kind):
			_soft_target()
			Server.command("/ac style " + kind)
			get_viewport().set_input_as_handled()
			return
	if Keybinds.pressed(event, "ac_dodge"):
		_dodge(_held_dir())
		get_viewport().set_input_as_handled()
		return
	# double-tap a direction: a dodge that way (A / D strafe in action combat, S steps back)
	for pair in [["turn_left", Vector3(-1, 0, 0)], ["turn_right", Vector3(1, 0, 0)], ["move_back", Vector3(0, 0, 1)]]:
		if Keybinds.pressed(event, String(pair[0])):
			var id := String(pair[0])
			if now - int(_taps.get(id, -100000)) <= DOUBLE_TAP_MS:
				_taps[id] = -100000
				_dodge(pair[1])
			else:
				_taps[id] = now
			return


func _held_dir() -> Vector3:
	var d := Vector3.ZERO
	if Keybinds.held("turn_left"):
		d.x -= 1.0
	if Keybinds.held("turn_right"):
		d.x += 1.0
	if Keybinds.held("move_back"):
		d.z += 1.0
	if Keybinds.held("move_forward"):
		d.z -= 1.0
	return d


func _dodge(dir: Vector3) -> void:
	var now := Time.get_ticks_msec()
	var p := _player()
	if p == null or now < _dodge_ready_at or not p.grounded:
		return
	_dodge_ready_at = now + DODGE_COOLDOWN_MS
	_end_guard()
	Server.command("/ac dodge")
	p.dodge(dir)


func _end_guard() -> void:
	if _guarding:
		_guarding = false
		Server.command("/ac guard off")
	var p := _player()
	if p:
		p.guard_mult = 1.0


## Soft targeting: keep your target while you look at it; otherwise the monster nearest your aim, close by.
func _soft_target() -> void:
	var p := _player()
	var npcs: NpcManager = viewer.npcs if viewer else null
	if p == null or npcs == null or p.camera == null:
		return
	var cur: Npc = npcs.target if npcs.target and is_instance_valid(npcs.target) else null
	if cur and cur.state.alive and _aim_score(cur, p, KEEP_ANGLE, SOFT_RANGE_M * 1.5) < INF:
		return
	var best: Npc = null
	var best_score := INF
	for i in npcs.active:
		var n: Npc = npcs.active[i]
		if n == null or not is_instance_valid(n) or not n.state.alive or n.state.stealthed:
			continue
		if int(n.spawn.get("realm", 0)) != 0 or (int(n.spawn.get("flags", 0)) & Npc.FLAG_CANTTARGET):
			continue
		var s := _aim_score(n, p, SOFT_ANGLE, SOFT_RANGE_M)
		if s < best_score:
			best_score = s
			best = n
	if best and best != cur:
		npcs.select(best)


func _aim_score(n: Npc, p: Player, max_angle: float, max_range: float) -> float:
	var to := n.global_position - p.global_position
	to.y = 0.0
	var dist := to.length()
	if dist > max_range:
		return INF
	if dist < 1.0:
		return dist                                        # right on top of you: it's the one
	var fwd := -p.camera.global_transform.basis.z
	fwd.y = 0.0
	if fwd.length() < 0.01:
		return INF
	var ang := rad_to_deg(fwd.normalized().angle_to(to.normalized()))
	if ang > max_angle:
		return INF
	return ang + dist * 3.0


# ---------------------------------------------------------------- every frame

func _process(_delta: float) -> void:
	if not _queried and Server.playing:
		_queried = true
		Server.command("/ac query")
	var p := _player()
	if p == null or not on:
		return
	var now := Time.get_ticks_msec()
	var free := not p.input_enabled or _typing() or p.dead or Keybinds.held("ac_cursor")
	p.action_cursor = free
	if free and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		get_viewport().warp_mouse(get_viewport().get_visible_rect().size * 0.5)
		_lmb_down = false
		if _rmb_down:
			_rmb_down = false
			_end_guard()
	elif not free and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	if _rmb_down and not _guarding and now - _rmb_at >= int(GUARD_AFTER_S * 1000.0):
		_guarding = true
		p.guard_mult = 0.5
		Server.command("/ac guard on")
	_windups = _windups.filter(func(w): return int(w.end) + 150 > now)
	for oid in _marks.keys():
		var m: Label3D = _marks[oid]
		if not is_instance_valid(m):
			_marks.erase(oid)
		elif int(m.get_meta("until", 0)) < now:
			m.visible = false
	hud.queue_redraw()


func _draw_hud() -> void:
	var p := _player()
	if p == null or not on:
		return
	var now := Time.get_ticks_msec()
	var c := hud.size * 0.5
	var font := ThemeDB.fallback_font
	if not p.action_cursor:
		var cross := Color(1, 1, 1, 0.85)
		hud.draw_circle(c, 1.6, cross)
		for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
			hud.draw_line(c + d * 6.0, c + d * 12.0, cross, 1.5)
	# a held click charging toward the anytime style
	if _lmb_down:
		var f := clampf((now - _lmb_at) / (HOLD_S * 1000.0), 0.0, 1.0)
		hud.draw_arc(c, 16.0, -PI * 0.5, -PI * 0.5 + TAU * f, 40,
				Color(1.0, 0.82, 0.3) if f >= 1.0 else Color(1, 1, 1, 0.7), 2.5 if f >= 1.0 else 2.0)
	# the swing timer: the arc under the crosshair empties as your weapon recovers
	if now < _timer_until:
		var r := float(_timer_until - now) / float(_timer_len)
		hud.draw_arc(c, 24.0, PI * 0.5 - PI * 0.35 * r, PI * 0.5 + PI * 0.35 * r, 24, Color(1, 1, 1, 0.45), 2.0)
	# monsters winding up a blow at you: a ring closing on the crosshair - gold while a parry would catch it
	for w in _windups:
		var total := maxf(1.0, float(int(w.end) - int(w.start)))
		var t := clampf((now - int(w.start)) / total, 0.0, 1.0)
		var left := int(w.end) - now
		var hot := left <= PARRY_WINDOW_MS and left > -60
		var rad := lerpf(78.0, 20.0, t)
		hud.draw_arc(c, rad, 0.0, TAU, 56, Color(1.0, 0.82, 0.3) if hot else Color(1.0, 0.3, 0.2, 0.85), 3.0 if hot else 2.0)
	if not _windups.is_empty():
		hud.draw_arc(c, 20.0, 0.0, TAU, 40, Color(1, 1, 1, 0.25), 1.0)
	# the ready lights
	var names := [["ac_position", "POSITION", Color(0.45, 0.85, 1.0)], ["ac_reactive", "REACTIVE", Color(1.0, 0.8, 0.3)],
			["ac_chain", "CHAIN", Color(0.8, 0.55, 1.0)]]
	var w := 86.0
	var x0 := c.x - w * 1.5
	for i in names.size():
		var lit := _ready.length() > i and _ready[i] == "1"
		var col: Color = names[i][2] if lit else Color(0.6, 0.6, 0.6, 0.35)
		var rect := Rect2(Vector2(x0 + i * w + 4.0, c.y + 64.0), Vector2(w - 8.0, 20.0))
		hud.draw_rect(rect, Color(0, 0, 0, 0.45 if lit else 0.25))
		hud.draw_rect(rect, col, false, 1.5)
		var keys: Array = Keybinds.bindings.get(String(names[i][0]), [])
		var label := "%s %s" % [String(keys[0]) if keys.size() > 0 else "-", String(names[i][1])]
		hud.draw_string(font, rect.position + Vector2(0, 15), label, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x, 12, col)
	if _ready.length() > 3 and _ready[3] == "1":
		hud.draw_string(font, Vector2(c.x - 60.0, c.y + 100.0), "HOLD: ANYTIME", HORIZONTAL_ALIGNMENT_CENTER, 120.0, 11,
				Color(1, 1, 1, 0.55))
	if _guarding:
		hud.draw_string(font, Vector2(c.x - 60.0, c.y - 30.0), "GUARD", HORIZONTAL_ALIGNMENT_CENTER, 120.0, 13,
				Color(0.85, 0.85, 0.85, 0.9))
	if now < _flash_until:
		var a := clampf((_flash_until - now) / 400.0, 0.0, 1.0)
		var fc := _flash_color
		fc.a = a
		hud.draw_string(font, Vector2(c.x - 150.0, c.y - 48.0), _flash_text, HORIZONTAL_ALIGNMENT_CENTER, 300.0, 22, fc)
