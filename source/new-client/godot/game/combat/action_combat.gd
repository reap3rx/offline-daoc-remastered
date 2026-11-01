extends Node
## Action Combat (owner 2026-10-26): an opt-in way to fight in melee on the server (game/../server ActionCombat.cs),
## for you only - monsters, gamebots and companions keep the classic rules, and F9 puts you back on them.
##   The mouse always looks and you face where you look (Alt held: the cursor, for the interface); A/D strafe.
##   Attack (left mouse): tap = a plain swing - nothing queues (owner 2026-11-01): it goes if it can right now (0.75 s
##     after the last for the quickest weapons, 1.75 s for the slowest), for the share of its damage the weapon has
##     recovered (full at its whole swing time). Hold past HOLD_S while the weapon glows (an anytime style ready) and
##     let go = your best anytime style, at once. With the weapon sheathed, the first tap only draws it.
##   Parry (right mouse): press = a timed parry (a block with a shield) - the window opens at the press: 0.2 s for a
##     parry, 0.15 s for a block, wider with skill (the server's numbers: "windows"). The parry / block plays at once
##     (half speed while it does); only a parry that catches a blow rings out.
##   Lock On (Mouse4): tap = lock onto your target (or what you aim at) - you and the camera keep facing it until it
##     dies or you tap again; hold and move the mouse left / right = the next target that way. The crosshair becomes
##     four triangles closing in on it: green when all your spells (and the bow, with it out) reach it, yellow when
##     some do, red when none do (melee doesn't count).
## Floating combat text: the damage you deal and take, over who took it (and what a parry / block saved).
##   Q / E / R: your best usable Position / Reactive / Chain style. A reactive answers one parry / block / dodge.
##   Dodge: double-tap a strafe / back direction (or the Dodge key) - the dodge animation and an evade window (0.1 s,
##     wider with Evade). No hop: the animation is the tell (owner 2026-10-28).
##   Every one of these is rebindable: Options > Controls > Combat ("Action: ...").
## The HUD: a crosshair; a ring closing in on it when a monster winds up a blow at you (gold = parry now); the
## charge of a held attack; the swing timer; the Position / Reactive / Chain lights; what your defense did.
## Ctrl+F9 (Arrange Combat HUD): drag its parts where you like, switch any of them off; kept in settings.cfg.
## The server talks to it in "#AC|..." system lines (ServerWorld takes them out of the chat).

const HOLD_S := 1.0                    # an attack held this long is an anytime style (owner 2026-10-28: 0.3 too quick, 0.6 too long; 2026-11-01: about 1 s)
const DOUBLE_TAP_MS := 260
const SOFT_RANGE_M := 12.0             # soft targeting: the monster nearest your aim within this ...
const SOFT_ANGLE := 40.0               # ... and this many degrees of it
const KEEP_ANGLE := 70.0               # your current target is kept while it stays this close to your aim
const WEAPONLESS := 19                 # cc_weapons.csv: bare hands' sounds
const SETTINGS := "user://settings.cfg"
const SECTION := "action_hud"

## The HUD's parts: [id, label, movable]
const PARTS := [["crosshair", "Crosshair", false], ["draw", "Bow draw ring", false], ["windup", "Wind-up ring on the attacker", false],
		["windup_cross", "Wind-up ring at the crosshair", false], ["charge", "Charge ring", false],
		["timer", "Swing timer", false], ["lights", "Style lights", true], ["flash", "Defense text", true],
		["marker", "Monster \"!\" marker", false], ["fct", "Floating combat text", false]]
const HIDDEN_BY_DEFAULT := ["windup_cross"]
const INTERACT_M := 6.0                # Interact's reach for what isn't right under the crosshair
const DEFAULT_OFFSET := {"lights": Vector2(0, 64), "flash": Vector2(0, -48)}

## npc oid -> msec: its blow's swing was already played at the wind-up (ServerWorld skips the second one)
static var _swung_early := {}

var viewer: Node
var on := false
var _queried := false
var _announced := false
var _atk_down := false
var _atk_at := 0
var _par_down := false
var _par_at := 0
var _taps := {}
var _dodge_ready_at := 0
var _ready := "0000"
var _has_anytime := false                 # an anytime style has lit this session (a held attack is then a charge)
var _timer_until := 0
var _style_at := 0                       # when the power attack can go (the server's timer: about 1 s after the last blow)
var _timer_len := 1
var _quick_at := 0                       # when a plain swing can go again (the server's timer|full|soonest)
# Lock on (owner 2026-11-01): the target you keep facing; the button held (cycling with the mouse)
const LOCK_MAX_M := 60.0                 # it lets go past this
const LOCK_CYCLE_PX := 90.0              # mouse travel (held) to the next target
const LOCK_TAP_MS := 300
var _lock: Npc = null
var _lock_down := false
var _lock_down_at := 0
var _lock_moved := false                 # the hold cycled (so letting go doesn't unlock)
var _lock_was := false                   # locked when the press began
var _lock_acc := 0.0
var _ranges: Array = []                  # your spells' reaches (DAoC units), refreshed now and then
var _ranges_at := 0
var _windups: Array = []               # [{oid, start, end}]
var _flash_text := ""
var _flash_color := Color.WHITE
var _flash_until := 0
var _marks := {}                       # oid -> Label3D "!" over a monster winding up
var _layer: CanvasLayer
var hud: Control
var _show := {}                        # part -> shown
var _offset := {}                      # movable part -> offset from the screen centre
# archery: a shot being drawn (Shot / Critical Shot held), as the server timed it
const SHOT_DELAY_MS := 1000            # at least this long between shots (ActionCombat.ShotDelayMs)
var _shot_ready_at := 0
var _draw_pending := ""                # a shot button pressed while recovering: drawn as soon as it may
var _drawing := false
var _draw_button := ""                 # "ac_shot" / "ac_crit_shot": the one whose release looses it
var _draw_crit := false
var _draw_at := 0                      # when the draw began (msec)
var _draw_full := 0                    # ms to full draw (0: the server hasn't answered yet)
var _draw_grace := 1200                # held this long past full, the bow overdraws
var _draw_reach := 0                   # the bow's reach in units, before the height bonus (the server's AttackRange)
var _overdraw := false
var _editing := false
var _panel: PanelContainer
var _drag := ""
var _drag_from := Vector2.ZERO
# the reticle: what's under the crosshair becomes your target (spells, pets, ranged - not only melee)
const RETICLE_RANGE_M := 45.0
const RETICLE_DWELL_MS := 200          # a new monster under the crosshair this long takes over the target
var _aim = null                        # the monster under the crosshair now (untyped: it may be gone)
var _aim_since := 0
var _aim_check_at := 0
# the over-the-shoulder camera (Arrange Combat HUD's sliders): metres right / up of the usual view
var cam_side := 0.55
var cam_up := 0.3


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
	hud.gui_input.connect(_hud_input)
	_layer.add_child(hud)
	hud.visible = false
	_load_layout()


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
				if _anytime_ready():
					_has_anytime = true
		"timer":
			if f.size() > 1:
				_timer_len = maxi(1, int(f[1]))
				_timer_until = now + _timer_len
				_quick_at = now + (int(f[2]) if f.size() > 2 else _timer_len)
				_style_at = now + (int(f[3]) if f.size() > 3 else _timer_len)
		"whiff":
			_whiff()                                         # out of reach: the blow cuts air
		"windows":                                       # windows|parry|block|dodge|cooldown (ActionCombat.SendWindows)
			if f.size() > 4:
				_win_parry = int(f[1])
				_win_block = int(f[2])
				_win_dodge = int(f[3])
				_win_cool = int(f[4])
		"windup":
			if f.size() > 2:
				_windup(int(f[1]), int(f[2]))
		"def":
			if f.size() > 2:
				_defended(String(f[1]), int(f[2]), int(f[3]) if f.size() > 3 else 0)
		"fct":                                           # damage: fct|oid (0 = you)|amount|critical|out / pet / in
			if f.size() > 4:
				_damage_text(int(f[1]), int(f[2]), f[3] == "1", String(f[4]))
		"draw":                                          # draw|full|grace|crit, or draw|0: refused / cancelled
			if f.size() > 1 and f[1] != "0":
				_draw_full = int(f[1])
				_draw_grace = int(f[2]) if f.size() > 2 else 1200
				_draw_crit = f.size() > 3 and f[3] == "1"
				_draw_reach = int(f[4]) if f.size() > 4 else 0
			elif _drawing:
				_end_draw(false)
			elif _player():
				_player().bow_release(false)              # (refused as it was loosed: the aim lowered)
		"overdraw":
			_overdraw = true
		"shot":                                          # shot|early / full / overdrawn|critical
			if f.size() > 2:
				if f[2] == "1":
					_flash("CRITICAL SHOT!", Color(1.0, 0.85, 0.3))
				elif f[1] == "overdrawn":
					_flash("OVERDRAWN!", Color(1.0, 0.4, 0.3))
				elif f[1] == "full":
					_flash("FULL DRAW", Color(0.85, 0.95, 1.0))
		"poisons":                                       # poisons|set|model~count~name x4 (PoisonBag.SendState)
			var slots := []
			for i in range(2, f.size()):
				var p3 := String(f[i]).split("~")
				slots.append({"model": int(p3[0]), "count": int(p3[1]) if p3.size() > 1 else 0,
						"name": String(p3[2]) if p3.size() > 2 else ""})
			Server.poison_bag = {"set": int(f[1]) if f.size() > 1 else 0, "slots": slots}
			var ui = viewer.get("ui") if viewer else null
			if ui and ui.windows.has("poisons"):
				ui.windows["poisons"].refresh()
		"styles":                                        # styles|slot|picked|id~name... / styles|end (the styles window)
			if f.size() > 1 and f[1] != "end":
				var opts := []
				for i in range(3, f.size()):
					var kv := String(f[i]).split("~")
					opts.append({"id": int(kv[0]), "name": String(kv[1]) if kv.size() > 1 else ""})
				Server.ac_styles[String(f[1])] = {"picked": int(f[2]) if f.size() > 2 else 0, "options": opts}
			var ui2 = viewer.get("ui") if viewer else null
			if ui2 and ui2.windows.has("ac_styles"):
				ui2.windows["ac_styles"].refresh()
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
		if not on:
			p.action_cursor = false
	_atk_down = false
	_par_down = false
	if not on:
		_set_editing(false)
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
	if viewer and viewer.has_method("note_combat"):
		viewer.note_combat()
	var n := _view(oid)
	if n == null:
		return
	# the blow is drawn so it lands as the server lands it: the swing starts a little into the wind-up
	get_tree().create_timer(maxf(0.0, (ms - 450) / 1000.0)).timeout.connect(func():
		if is_instance_valid(n) and n.is_alive():
			n.play_attack())
	if not bool(_show.get("marker", true)):
		return
	var mark = _marks.get(oid)
	if not is_instance_valid(mark):
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


## The server's parry rhythm (ActionCombat.PressParry): a press, its window, then half a second before the next
## (owner 2026-10-27: no spamming it) - unless it caught a blow. Pressed early, nothing happens at all. The windows
## grow with Parry / Shields / Evade and their realm abilities (owner 2026-10-28); the server sends them.
var _win_parry := 200
var _win_block := 150
var _win_dodge := 100
var _win_cool := 500
var _parry_ready_at := 0


func _parry_ok(now: int, parry_only := false) -> bool:
	if now < _parry_ready_at:
		return false
	if _press_window(parry_only) <= 0:                 # (never learned: casters - the server's window is 0)
		_flash("YOU CAN'T PARRY", Color(0.8, 0.8, 0.8))
		_parry_ready_at = now + 800
		return false
	_parry_ready_at = now + _press_window(parry_only) + _win_cool
	return true


## The window a parry / block press opens now (ms).
func _press_window(parry_only := false) -> int:
	return _win_block if _blocks() and not parry_only else _win_parry


## A shield carried and the skill to use it (the server's block window is 0 without Shields).
func _blocks() -> bool:
	return _has_shield() and _win_block > 0


func _defended(kind: String, dmg: int, saved: int) -> void:
	var gold := Color(1.0, 0.85, 0.35)
	var blue := Color(0.55, 0.8, 1.0)
	if kind in ["parry", "block"]:
		_parry_ready_at = 0                                # (a caught blow: the next press is free to come at once)
	elif kind == "dodge":
		_dodge_ready_at = 0
	match kind:
		"miss":                                            # in combat, a press that caught nothing: its endurance
			_float_text(0, "MISSED  -%d END" % dmg, Color(0.75, 0.75, 0.75), 32, 0.5)
			return
		"parry":
			_flash("PARRIED  %d saved" % saved if saved > 0 else "PARRIED", gold)
			_float_text(0, "PARRY  %d saved" % saved if saved > 0 else "PARRY", gold, 46, 0.5)
		"block":
			_flash("BLOCKED  %d saved" % saved if saved > 0 else "BLOCKED", blue)
			_float_text(0, "BLOCK  %d saved" % saved if saved > 0 else "BLOCK", blue, 46, 0.5)
		"dodge":
			_flash("DODGED", Color(0.55, 1.0, 0.6))
			_float_text(0, "DODGE", Color(0.55, 1.0, 0.6), 46, 0.5)
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


## A swing at nothing: the swing and the weapon's whoosh (owner 2026-10-26: air swings were silent).
func _whiff() -> void:
	var p := _player()
	if p == null:
		return
	p.swing(p.weapon_stance())
	if p.sounds:
		var ws := int(WeaponModels.info(int(MeleeMath.weapon(PlayerData).get("model", 0))).get("sound_set", 0))
		p.sounds.weapon(ws if ws > 0 else WEAPONLESS, "use")


func _view(oid: int) -> Npc:
	var by_oid = viewer.npcs.get("by_oid") if viewer and viewer.npcs else null
	var st = (by_oid as Dictionary).get(oid) if by_oid is Dictionary else null
	if st == null:
		return null
	var v = st.view
	return v as Npc if is_instance_valid(v) and v is Npc else null


## A number rising over whoever took the blow: white yours (yellow and bigger when critical), green your pet's, red
## what you take. (The server reports every point of damage you deal or take: ActionCombat.ReportDamage.)
func _damage_text(oid: int, amount: int, crit: bool, way: String) -> void:
	match way:
		"in":
			_float_text(0, "-%d" % amount, Color(1.0, 0.3, 0.25), 52 if crit else 42, 0.0)
		"pet":
			_float_text(oid, "%d" % amount, Color(0.55, 0.95, 0.55), 40, 0.0)
		_:
			_float_text(oid, ("%d!" % amount) if crit else "%d" % amount,
					Color(1.0, 0.9, 0.3) if crit else Color(1, 1, 1), 64 if crit else 48, 0.0)


func _float_text(oid: int, text: String, color: Color, size: int, lift: float) -> void:
	if not bool(_show.get("fct", true)) or viewer == null:
		return
	var p := _player()
	var at := Vector3.INF
	if oid == 0:
		if p:
			at = p.global_position + Vector3(0, 2.3 + lift, 0)
	else:
		var n := _view(oid)
		if n:
			at = n.global_position + Vector3(0, n.height + 0.3 + lift, 0)
	if at == Vector3.INF:
		return
	var l := Label3D.new()
	l.text = text
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.fixed_size = true
	l.pixel_size = 0.0012
	l.font_size = size
	l.outline_size = 10
	l.modulate = color
	l.render_priority = 10
	viewer.add_child(l)
	l.global_position = at + Vector3(randf_range(-0.35, 0.35), 0, randf_range(-0.2, 0.2))
	var t := l.create_tween().set_parallel(true)
	t.tween_property(l, "global_position:y", l.global_position.y + 1.3, 1.1).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	t.tween_property(l, "modulate:a", 0.0, 0.5).set_delay(0.6)
	t.chain().tween_callback(l.queue_free)


## A shield in use: worn in the left hand with the one-handed set out - a two-hander or a bow in hand leaves it on
## the back (owner 2026-10-31: right click blocked with a two-hander out; it parries unless a shield is in use).
## The server's own test is the same (ActionCombat.HasShield: the active left weapon).
func _has_shield() -> bool:
	if PlayerData.active_weapon == "twohand":
		var th: Dictionary = PlayerData.item_at(12) if PlayerData.has_method("item_at") else {}
		if not th.is_empty() and int(th.get("hand", 0)) == 1:   # (a one-hander there keeps the shield, as the server)
			return false
	elif PlayerData.active_weapon != "standard":
		return false
	var s: Dictionary = PlayerData.item_at(11) if PlayerData.has_method("item_at") else {}
	return not s.is_empty() and int(s.get("object_type", 0)) == 42


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
	# a melee weapon out: Shift + wheel swaps the poison bag's sets (the bag must hold something)
	if not _ranged() and not _typing() and Keybinds.pressed(event, "poisons_swap") and _bag_used():
		var t := Time.get_ticks_msec()
		if t - _swap_at > 300:                             # (a wheel's notch can come as several events)
			_swap_at = t
			Server.command("/ac poison swap")
		get_viewport().set_input_as_handled()
		return
	if _ranged() and not _typing() and (Keybinds.pressed(event, "arrows_next") or Keybinds.pressed(event, "arrows_prev")):
		Server.command("/ac quiver next" if Keybinds.pressed(event, "arrows_next") else "/ac quiver prev")
		get_viewport().set_input_as_handled()            # (not the camera's zoom)
		return
	if not on or _typing() or not p.input_enabled or p.dead:
		return
	if event is InputEventKey and event.pressed and not event.echo and Keybinds.pressed(event, "ac_hud"):
		_set_editing(not _editing)
		get_viewport().set_input_as_handled()
		return
	if not _editing and not p.action_cursor:
		if Keybinds.matches(event, "ac_lock") and not event.is_echo():
			if event.is_pressed():
				_lock_press()
			else:
				_lock_release()
			get_viewport().set_input_as_handled()
			return
		if _lock_down and event is InputEventMouseMotion:
			_lock_acc += (event as InputEventMouseMotion).relative.x
			if absf(_lock_acc) >= LOCK_CYCLE_PX:
				_lock_cycle(1 if _lock_acc > 0.0 else -1)
				_lock_acc = 0.0
			get_viewport().set_input_as_handled()        # (the camera stays on the lock while you pick)
			return
	if _editing:
		if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
			_set_editing(false)
			get_viewport().set_input_as_handled()
		return                                             # arranging the HUD: no fighting
	var now := Time.get_ticks_msec()
	var mouse := event is InputEventMouseButton
	var echo: bool = event is InputEventKey and event.is_echo()
	if not echo and not (mouse and p.action_cursor) and _ranged():
		# a bow / crossbow out: Shot and Critical Shot draw while held and loose when let go
		for id in ["ac_shot", "ac_crit_shot"]:
			if Keybinds.matches(event, id) and (mouse or event is InputEventKey):
				if event.is_pressed():
					if Time.get_ticks_msec() < _shot_ready_at:
						_draw_pending = id                 # still recovering from the last shot: draws when it can
					else:
						_start_draw(id)
				elif _drawing and _draw_button == id:
					_loose()
				elif _draw_pending == id:
					_draw_pending = ""
				get_viewport().set_input_as_handled()
				return
	if not echo and not (mouse and p.action_cursor) and not _ranged():
		if Keybinds.matches(event, "ac_attack") and (mouse or event is InputEventKey):
			if event.is_pressed():
				_attack_down(now)
			elif _atk_down:
				_attack_up(now)
			get_viewport().set_input_as_handled()
			return
		# Parry Only (Shift + right mouse): with a shield, a parry instead of a block - to open a parry reaction
		if Keybinds.pressed(event, "ac_parry_only"):
			if not _drawn():
				_draw_weapon()
			elif _parry_ok(now, true):
				Server.command("/ac parry only")
				p.action_defend("parry")
			get_viewport().set_input_as_handled()
			return
		if Keybinds.matches(event, "ac_parry") and (mouse or event is InputEventKey):
			if event.is_pressed() and not _drawn():
				_draw_weapon()                                 # sheathed: the first press draws, the next parries
			elif event.is_pressed() and _parry_ok(now):
				Server.command("/ac parry")
				p.action_defend("block" if _blocks() else "parry")   # the move plays now, hit or miss
			get_viewport().set_input_as_handled()
			return
	if mouse and not p.action_cursor and event.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
		get_viewport().set_input_as_handled()              # (unbound buttons do nothing while the mouse looks)
		return
	if not (event is InputEventKey or event is InputEventMouseButton) or not event.is_pressed() or event.is_echo():
		return
	var kinds := ["position", "reactive", "chain"]
	for i in kinds.size():
		if Keybinds.pressed(event, "ac_" + kinds[i]):
			# only when its light is on (its condition met) and the weapon is out: otherwise nothing at all
			if _drawn() and _ready.length() > i and _ready[i] == "1":
				_soft_target()
				Server.command("/ac style " + kinds[i])
			get_viewport().set_input_as_handled()
			return
	if Keybinds.pressed(event, "ac_interact"):
		_interact()
		get_viewport().set_input_as_handled()
		return
	if Keybinds.pressed(event, "ac_dodge"):
		if not _drawn():
			_draw_weapon()                                 # sheathed: the first press draws
		else:
			_dodge(_held_dir())
		get_viewport().set_input_as_handled()
		return
	# double-tap a direction: a dodge that way (A / D strafe in action combat, S steps back)
	for pair in [["turn_left", Vector3(-1, 0, 0)], ["turn_right", Vector3(1, 0, 0)], ["strafe_left", Vector3(-1, 0, 0)],
			["strafe_right", Vector3(1, 0, 0)], ["move_back", Vector3(0, 0, 1)]]:
		if Keybinds.pressed(event, String(pair[0])):
			var id := String(pair[0])
			if now - int(_taps.get(id, -100000)) <= DOUBLE_TAP_MS:
				_taps[id] = -100000
				if _drawn():                               # (sheathed: a double-tap is just walking)
					_dodge(pair[1])
			else:
				_taps[id] = now
			return


func _drawn() -> bool:
	return viewer != null and bool(viewer.get("_server_attack"))


## Interact (owner 2026-10-26): what the crosshair is on - talk to an NPC (a monster: target it), open a door, pick
## up what lies on the ground, manage a companion - else the nearest of those in front of you within INTERACT_M.
func _interact() -> void:
	var p := _player()
	if p == null or p.camera == null or viewer == null:
		return
	var centre := get_viewport().get_visible_rect().size * 0.5
	var npcs: NpcManager = viewer.npcs
	var picked: Dictionary = viewer._click_pick(centre) if viewer.has_method("_click_pick") else {}
	var n: Npc = picked.get("npc")
	if n and n.global_position.distance_to(p.global_position) <= INTERACT_M * 4.0:
		_use_npc(n)
		return
	if String(picked.get("kind", "")) == "door" and viewer._click_door(centre):
		return
	var sw = npcs if npcs and npcs.has_method("click_object") else null
	if sw and sw.click_object(p.camera, centre):
		sw.get_object()
		return
	var bot: Node3D = WorldLink.pick_bot(p.camera, centre)
	if bot and bool(bot.get("companion")) and viewer.companions:
		WorldLink.target_bot(bot)
		viewer.companions.manage(int(bot.get("bot_id")))
		return
	# nothing under the crosshair: the nearest thing to use in front of you
	var acc := {"best": null, "score": INF}            # (a dictionary: the lambda below can't assign outer locals)
	var fwd := -p.camera.global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length() > 0.01 else Vector3.FORWARD
	var consider := func(thing, pos: Vector3, kind: String):
		var to := pos - p.global_position
		to.y = 0.0
		var d := to.length()
		if d > INTERACT_M:
			return
		var ang := rad_to_deg(fwd.angle_to(to.normalized())) if d > 0.5 else 0.0
		if ang > 70.0:
			return
		var s := d + ang * 0.05
		if s < float(acc.score):
			acc.score = s
			acc.best = [kind, thing]
	if npcs:
		for i in npcs.active:
			var v: Npc = npcs.active[i]
			if is_instance_valid(v) and v.state.alive and int(v.spawn.get("realm", 0)) != 0:
				consider.call(v, v.global_position, "npc")
	if sw:
		var objs = sw.get("objects")
		if objs is Dictionary:
			for oid in objs:
				var h = objs[oid]
				if is_instance_valid(h):
					consider.call(int(oid), (h as Node3D).global_position, "object")
	var zones: Array = []
	var rw = viewer.get("region")
	if rw and rw.get("zones") is Dictionary:
		zones = (rw.zones as Dictionary).values()
	elif viewer.get("zone"):
		zones = [viewer.zone]
	for z in zones:
		if is_instance_valid(z) and z.get("doors") is Array:
			for d in z.doors:
				if is_instance_valid(d):
					consider.call(d, (d as Node3D).global_position, "door")
	var best = acc.best
	if best == null:
		PlayerData.message.emit("There is nothing here to use.", "system")
		return
	match String(best[0]):
		"npc":
			_use_npc(best[1])
		"object":
			sw._target_ground(int(best[1]))
			sw.get_object()
		"door":
			if sw and sw.has_method("request_door"):
				sw.request_door(best[1])


## An NPC's window (talk, merchant, vault, trainer) is open: the cursor is out for it until it closes (walking off
## closes it - ZoneViewer._watch_npc_windows).
func _npc_window_open() -> bool:
	var ui = viewer.get("ui") if viewer else null
	if ui == null:
		return false
	for w in [ui.get("merchant"), ui.get("vault"), ui.get("trainer"), ui.get("npc_dialog")]:
		if w != null and is_instance_valid(w) and (w as CanvasItem).visible:
			return true
	return false


func _use_npc(n: Npc) -> void:
	var npcs: NpcManager = viewer.npcs
	if npcs == null or not is_instance_valid(n):
		return
	WorldLink.clear_bot_target()
	npcs.select(n)
	if not _hostile(n):
		npcs.interact(n)                                   # talk, trade, train - as a right-click on it


func _draw_weapon() -> void:
	if viewer and viewer.has_method("_set_server_attack"):
		viewer._set_server_attack(true, true)


## After your target dies, the weapon stays out while other monsters near you are still fighting (owner 2026-10-26:
## you shouldn't have to draw again to parry the next one).
func keep_drawn() -> bool:
	var p := _player()
	if not on or p == null or viewer == null or viewer.npcs == null:
		return false
	var by_oid = viewer.npcs.get("by_oid")
	if not (by_oid is Dictionary):
		return false
	if not _windups.is_empty():
		return true
	var now := Time.get_ticks_msec()
	for st in (by_oid as Dictionary).values():
		if st and st.alive and int(st.spawn.get("realm", 0)) == 0 and int(st.combat_until) > now \
				and (st.pos as Vector3).distance_to(p.global_position) < 25.0:
			return true
	return false


func _has_target() -> bool:
	var npcs: NpcManager = viewer.npcs if viewer else null
	return npcs != null and is_instance_valid(npcs.target) and npcs.target.state.alive


func _attack_down(now: int) -> void:
	_soft_target()
	if not _drawn():
		# the weapon sheathed: the first tap only draws it (owner 2026-10-26) - the next one swings
		if viewer.has_method("_set_server_attack"):
			viewer._set_server_attack(true, true)
		_atk_down = false
		return
	_atk_down = true
	_atk_at = now


func _attack_up(now: int) -> void:
	_atk_down = false
	_soft_target()
	var held := now - _atk_at >= int(HOLD_S * 1000.0)
	var heavy := held and _anytime_ready()
	# A held attack let go before the power attack can go does nothing (owner 2026-11-01: it used to go as a quick
	# swing, which restarted the clock - so the next hold was too soon again, and again). The ring round the crosshair
	# fills as you hold and turns gold when a release would fire the style.
	if held and not heavy and _has_anytime and now < _style_at + 300:   # (+ the lights' lag)
		return
	if not _has_target():
		_whiff()                                           # nothing there: a swing at the air, with its sound
		return
	Server.command("/ac style anytime" if heavy else "/ac swing")


## An anytime style would fire now (its light from the server: known, usable, the weapon recovered).
func _anytime_ready() -> bool:
	return _ready.length() > 3 and _ready[3] == "1"


func _held_dir() -> Vector3:
	var d := Vector3.ZERO
	if Keybinds.held("turn_left") or Keybinds.held_unshared("strafe_left", Player.AC_BUTTONS):
		d.x -= 1.0
	if Keybinds.held("turn_right") or Keybinds.held_unshared("strafe_right", Player.AC_BUTTONS):
		d.x += 1.0
	if Keybinds.held("move_back"):
		d.z += 1.0
	if Keybinds.held("move_forward"):
		d.z -= 1.0
	return d


func _dodge(_dir: Vector3) -> void:
	var now := Time.get_ticks_msec()
	var p := _player()
	if p == null or now < _dodge_ready_at or not p.grounded:
		return
	if _win_dodge <= 0:                                    # (no Evade: the server's window is 0)
		_flash("YOU CAN'T DODGE", Color(0.8, 0.8, 0.8))
		_dodge_ready_at = now + 800
		return
	_dodge_ready_at = now + _win_dodge + _win_cool
	if _drawing:
		Server.command("/ac cancel")                       # (a dodge lowers the bow)
		_end_draw(false)
	Server.command("/ac dodge")
	p.action_defend("evade")                               # (no hop - owner 2026-10-28: the animation is the tell)


var _swap_at := 0


func _bag_used() -> bool:
	for s in (Server.poison_bag.get("slots", []) as Array):
		if String((s as Dictionary).get("name", "")) != "":
			return true
	return false


func _ranged() -> bool:
	return String(PlayerData.active_weapon) == "ranged"


## Archery: the shot button pressed - the bow drawn (you stand to shoot: rooted while drawing).
func _start_draw(button: String) -> void:
	var p := _player()
	if p == null or _drawing:
		return
	if not _drawn() and viewer.has_method("_set_server_attack"):
		viewer._set_server_attack(true, false)            # the bow in hand (attack mode itself never auto-fires here)
	_drawing = true
	_draw_button = button
	_draw_crit = button == "ac_crit_shot"
	_draw_at = Time.get_ticks_msec()
	_draw_full = 0
	_overdraw = false
	p.aiming = true
	p.bow_draw()
	Server.command("/ac draw crit" if _draw_crit else "/ac draw normal")


func _loose() -> void:
	Server.command("/ac loose")
	_end_draw(true)
	_shot_ready_at = Time.get_ticks_msec() + SHOT_DELAY_MS
	_timer_len = SHOT_DELAY_MS                             # (the recovery arc under the crosshair)
	_timer_until = _shot_ready_at
	_quick_at = _shot_ready_at


## The draw over: loosed (the server's BowShoot plays the release) or lowered.
func _end_draw(loosed: bool) -> void:
	if not _drawing:
		return
	_drawing = false
	_overdraw = false
	var p := _player()
	if p:
		p.aiming = false
		if not loosed:
			p.bow_release(false)


## Soft targeting: keep your target while you look at it; otherwise the monster nearest your aim, close by.
func _soft_target() -> void:
	if _locked():
		return                                             # (locked on: that's your target)
	var p := _player()
	var npcs: NpcManager = viewer.npcs if viewer else null
	if p == null or npcs == null or p.camera == null:
		return
	var cur: Npc = npcs.target if is_instance_valid(npcs.target) else null
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
		Server.command("/ac poison query")                 # (the poison bag starts putting poisons on)
	var p := _player()
	_hold_sprint(p)
	if p == null or not on:
		return
	var now := Time.get_ticks_msec()
	var lp = viewer.get("look_panel") if viewer else null
	var free: bool = _editing or not p.input_enabled or _typing() or p.dead or Keybinds.held("ac_cursor") or _npc_window_open() \
			or (lp != null and is_instance_valid(lp) and lp.visible)
	p.action_cursor = free
	if free and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		get_viewport().warp_mouse(get_viewport().get_visible_rect().size * 0.5)
		_atk_down = false
	elif not free and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_windups = _windups.filter(func(w): return int(w.end) + 150 > now)
	for oid in _marks.keys():
		var m = _marks[oid]                              # (untyped: the monster - and its mark - may be gone)
		if not is_instance_valid(m):
			_marks.erase(oid)
		elif int((m as Label3D).get_meta("until", 0)) < now:
			(m as Label3D).visible = false
	_lock_tick(p, _delta)
	_reticle_tick(p, now)
	if _draw_pending != "" and now >= _shot_ready_at:
		var pend := _draw_pending
		_draw_pending = ""
		if _ranged() and Keybinds.held(pend):
			_start_draw(pend)
	if _drawing and not _ranged():
		Server.command("/ac cancel")
		_end_draw(false)
	p.charge_glow(_atk_down and now - _atk_at >= int(HOLD_S * 1000.0) and _anytime_ready())   # (no glow: nothing to fire)
	p.shoulder = Vector2(cam_side, cam_up)
	hud.queue_redraw()


## Sprint while Shift is held (owner 2026-10-28: in action combat Shift sprints instead of walking - held, not a
## toggle). Only while a movement key is held too, so Shift + a quickbar key doesn't start it. The server's own Sprint
## (its x1.3, its endurance) - "/sprint on" / "off"; its "prepare to sprint" chat lines are kept out of the way.
var _sprint_held := false
var _sprint_quiet_until := 0


func _hold_sprint(p: Player) -> void:
	var want := on and p != null and Server.playing and p.input_enabled and not p.dead and not _typing() \
			and Input.is_physical_key_pressed(KEY_SHIFT) and (_moving_keys() or p.autorun)
	if want == _sprint_held:
		return
	_sprint_held = want
	_sprint_quiet_until = Time.get_ticks_msec() + 1500
	Server.command("/sprint on" if want else "/sprint off")


func _moving_keys() -> bool:
	for id in ["move_forward", "move_back", "turn_left", "turn_right", "strafe_left", "strafe_right"]:
		if Keybinds.held(id):
			return true
	return false


## A sprint chat line that only echoes a hold-Shift sprint starting or stopping (ServerWorld drops it).
func quiet_sprint_line(text: String) -> bool:
	return Time.get_ticks_msec() < _sprint_quiet_until and text.to_lower().contains("sprint") \
			and not text.to_lower().contains("fatigued")


## The reticle: the monster the crosshair is on (its pick shape, else the one nearest the crosshair's line within a
## small angle - easier on small or far ones), up to RETICLE_RANGE_M. Held there RETICLE_DWELL_MS it becomes your
## target (at once when you have none) - so spells, pet commands and ranged attacks follow your aim; looking away
## at nothing keeps the target you had.
func _reticle_tick(p: Player, now: int) -> void:
	if _locked():
		_aim = _lock
		return
	if now < _aim_check_at:
		return
	_aim_check_at = now + 80
	var npcs: NpcManager = viewer.npcs if viewer else null
	if npcs == null or p.camera == null or p.action_cursor:
		_aim = null
		return
	var cam := p.camera
	var centre := get_viewport().get_visible_rect().size * 0.5
	var hit: Npc = npcs.pick(cam, centre)
	var best: Npc = hit if hit and _aimable(hit) and hit.global_position.distance_to(p.global_position) <= RETICLE_RANGE_M else null
	if best == null:
		var from := cam.project_ray_origin(centre)
		var fwd := cam.project_ray_normal(centre)
		var best_ang := INF
		for i in npcs.active:
			var n: Npc = npcs.active[i]
			if not is_instance_valid(n) or not _aimable(n):
				continue
			var mid := n.global_position + Vector3(0, n.height * 0.5, 0)
			var to := mid - from
			var dist := to.length()
			if dist < 0.5 or dist > RETICLE_RANGE_M + 5.0:
				continue
			var ang := rad_to_deg(fwd.angle_to(to))
			var allow := maxf(2.5, rad_to_deg(atan2(maxf(0.6, n.height * 0.5), dist)))
			if ang <= allow and ang < best_ang:
				best_ang = ang
				best = n
	if best != _aim:
		_aim = best
		_aim_since = now
	var cur = npcs.target
	if _aim == null or (is_instance_valid(cur) and cur == _aim):
		return
	if not is_instance_valid(cur) or not cur.state.alive or now - _aim_since >= RETICLE_DWELL_MS:
		_select_quiet(_aim)


## Ally targeting (owner 2026-11-01): while the Target Allies key is held (Left Ctrl) the reticle and the lock look for
## your own realm's people and pets instead of enemies - for heals and buffs. Locking on works the same.
func _ally_scan() -> bool:
	return Keybinds.held("ac_ally") and not _typing()


## Your realm's people (the server's bots and players come as NPCs with their realm) and pets, alive and targetable;
## not peaceful townsfolk (merchants, trainers).
func _ally(n: Npc) -> bool:
	if n == null or not is_instance_valid(n):
		return false
	var flags := int(n.spawn.get("flags", 0))
	return n.state.alive and not n.state.stealthed and int(n.spawn.get("realm", 0)) == PlayerData.realm_id() \
			and PlayerData.realm_id() != 0 and not (flags & Npc.FLAG_CANTTARGET) and not (flags & Npc.FLAG_PEACE)


func _aimable(n: Npc) -> bool:
	return _ally(n) if _ally_scan() else _hostile(n)


## What the reticle picks: monsters, and anyone of an enemy realm - the server's Midgard / Albion "players" (its
## bots, sent as NPCs with their realm) and enemy guards (owner 2026-10-28: Midgard bots in the Old Frontiers could
## only be Alt+clicked). Not your realm's people, not peaceful NPCs, nothing hidden or untargetable.
func _hostile(n: Npc) -> bool:
	var realm := int(n.spawn.get("realm", 0))
	var flags := int(n.spawn.get("flags", 0))
	return n.state.alive and not n.state.stealthed and (realm == 0 or realm != PlayerData.realm_id()) \
			and not (flags & Npc.FLAG_CANTTARGET) and not (flags & Npc.FLAG_PEACE)


# ---------------------------------------------------------------- lock on

func _locked() -> bool:
	if _lock == null:
		return false
	if not is_instance_valid(_lock) or not _lock.state.alive or not _lock.is_inside_tree():
		_lock = null
		return false
	return true


func _lock_press() -> void:
	_lock_down = true
	_lock_down_at = Time.get_ticks_msec()
	_lock_moved = false
	_lock_acc = 0.0
	_lock_was = _locked()
	if not _lock_was:
		var npcs: NpcManager = viewer.npcs if viewer else null
		var cur = npcs.target if npcs else null
		var pick: Npc = _aim if is_instance_valid(_aim) else null
		if pick == null and is_instance_valid(cur) and cur is Npc and (_hostile(cur as Npc) or _ally(cur as Npc)):
			pick = cur as Npc
		if pick == null:
			pick = _lock_candidates(_player()).front() if not _lock_candidates(_player()).is_empty() else null
		if pick:
			_set_lock(pick)


func _lock_release() -> void:
	_lock_down = false
	# a tap on a lock you already had lets go of it; a hold that picked another target keeps the new one
	if _lock_was and not _lock_moved and Time.get_ticks_msec() - _lock_down_at <= LOCK_TAP_MS * 3:
		_lock = null


func _set_lock(n: Npc) -> void:
	_lock = n
	_select_quiet(n)


## The targets worth locking: hostile, alive, within LOCK_MAX_M and in front of the camera - sorted nearest the middle.
func _lock_candidates(p: Player) -> Array:
	var out: Array = []
	var npcs: NpcManager = viewer.npcs if viewer else null
	if p == null or npcs == null or p.camera == null:
		return out
	var cam := p.camera
	var mid := get_viewport().get_visible_rect().size * 0.5
	for i in npcs.active:
		var n: Npc = npcs.active[i]
		if not is_instance_valid(n) or not _aimable(n):
			continue
		var at := n.global_position + Vector3(0, n.height * 0.6, 0)
		if at.distance_to(p.global_position) > LOCK_MAX_M or cam.is_position_behind(at):
			continue
		out.append(n)
	out.sort_custom(func(a, b): return cam.unproject_position(a.global_position).distance_to(mid) \
			< cam.unproject_position(b.global_position).distance_to(mid))
	return out


## Held + the mouse moved: the next target that way across the screen (wrapping round).
func _lock_cycle(dir: int) -> void:
	var p := _player()
	var c := _lock_candidates(p)
	if c.is_empty():
		return
	_lock_moved = true
	var cam := p.camera
	c.sort_custom(func(a, b): return cam.unproject_position(a.global_position).x < cam.unproject_position(b.global_position).x)
	var i := c.find(_lock) if _locked() else -1
	if i < 0:
		_set_lock(c[0])
		return
	_set_lock(c[(i + dir + c.size()) % c.size()])


## Locked on: you and the camera turn to it (smoothly); it lets go when it dies or gets too far.
func _lock_tick(p: Player, delta: float) -> void:
	if not _locked():
		p.lock_target = null
		return
	if _lock.global_position.distance_to(p.global_position) > LOCK_MAX_M:
		_lock = null
		p.lock_target = null
		return
	var npcs: NpcManager = viewer.npcs if viewer else null
	if npcs and npcs.target != _lock:
		if is_instance_valid(npcs.target) and npcs.target != _lock and npcs.target is Npc:
			_lock = npcs.target as Npc                     # (you picked another target by hand: the lock moves to it)
		else:
			_select_quiet(_lock)
	p.lock_target = _lock                                  # (the character faces it too: Player._lock_yaw)
	if p.camera == null:
		return
	var fwd := -p.camera.global_basis.z
	fwd.y = 0.0
	var to := _lock.global_position - p.global_position
	to.y = 0.0
	if fwd.length() < 0.01 or to.length() < 0.3:
		return
	var a := fwd.normalized().signed_angle_to(to.normalized(), Vector3.UP)
	p.cam_yaw += a * minf(1.0, delta * 10.0)


## Your spells' reaches (and nothing for melee): from the server's spell list (or the class data offline).
func _spell_ranges() -> Array:
	var now := Time.get_ticks_msec()
	if now < _ranges_at:
		return _ranges
	_ranges_at = now + 3000
	var seen := {}
	if Server.active:
		for line in Server.spell_lines:
			for sp in (line.spells as Array):
				var r := _spell_range(sp as Dictionary)
				if r > 0:
					seen[r] = true
	else:
		for line in ClassDb.spell_lines(PlayerData.class_id(), PlayerData.level, PlayerData.specs):
			for sid in line.spells:
				var r := int(ClassDb.spell(int(sid)).get("range", 0))
				if r > 0:
					seen[r] = true
	_ranges = seen.keys()
	return _ranges


static var _range_by_name := {}


static func _spell_range(sp: Dictionary) -> int:
	var nm := String(sp.get("name", ""))
	var s := ClassDb.spell(int(sp.get("id", 0)))
	if not s.is_empty() and String(s.get("name", "")) == nm:
		return int(s.get("range", 0))
	if _range_by_name.is_empty():
		for k in ClassDb._spells:
			var o: Dictionary = ClassDb._spells[k]
			var n := String(o.get("name", ""))
			if n != "" and not _range_by_name.has(n):
				_range_by_name[n] = int(o.get("range", 0))
	return int(_range_by_name.get(nm, 0))


## The lock's colour: green when every reach you have (spells; the bow too when it's out) gets there, yellow when some
## do, red when none do; white when you have none to measure.
func _lock_color(p: Player) -> Color:
	var reaches: Array = _spell_ranges().duplicate()
	if _ranged():
		reaches.append(_draw_reach if _draw_reach > 0 else 1500)
	if reaches.is_empty():
		return Color(1, 1, 1)
	var dist := _lock.global_position.distance_to(p.global_position) / 0.025
	var n := 0
	for r in reaches:
		if dist <= float(r):
			n += 1
	if n == reaches.size():
		return Color(0.35, 1.0, 0.4)
	if n == 0:
		return Color(1.0, 0.3, 0.25)
	return Color(1.0, 0.85, 0.25)


## The lock reticle: the crosshair grown four times over, its four lines now small see-through triangles pointing in at
## the target, breathing in and out.
func _draw_lock(p: Player, now: int) -> void:
	if p.camera == null:
		return
	var at := _lock.global_position + Vector3(0, _lock.height * 0.6, 0)
	if p.camera.is_position_behind(at):
		return
	var c := p.camera.unproject_position(at)
	var col := _lock_color(p)
	col.a = 0.6
	var r := 34.0 + 5.0 * sin(now * 0.006)
	for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
		var side := Vector2(-d.y, d.x)
		var tip: Vector2 = c + d * (r - 11.0)
		var base: Vector2 = c + d * (r + 5.0)
		hud.draw_colored_polygon(PackedVector2Array([tip, base + side * 7.0, base - side * 7.0]), col)
	hud.draw_circle(c, 1.6, Color(col.r, col.g, col.b, 0.9))


## Target without the "You target [x]" chat line (the reticle changes targets often).
## A spell / ability is about to go to the server (Server.use_entry): what the reticle points at becomes the target
## at once (no dwell), and the character turns to the target - locked on or not (owner 2026-11-01: casters had to
## turn by hand). Not while the cursor is out (a click on a window) - then the target stays as it is.
func before_use() -> void:
	var p := _player()
	if p == null:
		return
	if not on:
		p.face_lock()
		return
	var npcs: NpcManager = viewer.npcs if viewer else null
	if not _locked() and not p.action_cursor and is_instance_valid(_aim) and _aim.state.alive and npcs and npcs.target != _aim:
		_select_quiet(_aim)
	var t: Node3D = npcs.target if npcs and is_instance_valid(npcs.target) else null
	if t != null and t.global_position.distance_to(p.global_position) > LOCK_MAX_M:
		t = null
	p.face_lock(t)


func _select_quiet(n: Npc) -> void:
	var npcs: NpcManager = viewer.npcs if viewer else null
	if npcs == null or not is_instance_valid(n) or not n.state.alive:
		return
	npcs.target = n
	if "target_object" in npcs:
		npcs.set("target_object", 0)
	PlayerData.set_target({"name": String(n.spawn.name), "level": n.state.level, "con_color": n.con_color(PlayerData.level),
			"health": n.state.health, "guild": String(n.spawn.get("guild", ""))})
	if Server.client:
		Server.client.call("Target", int(n.spawn.get("oid", 0)), 0x8000 | 0x6000)


# ---------------------------------------------------------------- the HUD and its layout

func _load_layout() -> void:
	var cfg := ConfigFile.new()
	cfg.load(SETTINGS)
	for part in PARTS:
		_show[part[0]] = bool(cfg.get_value(SECTION, "show_" + String(part[0]), not HIDDEN_BY_DEFAULT.has(part[0])))
	for id in DEFAULT_OFFSET:
		var v = cfg.get_value(SECTION, "at_" + String(id), DEFAULT_OFFSET[id])
		_offset[id] = v if v is Vector2 else DEFAULT_OFFSET[id]
	cam_side = float(cfg.get_value(SECTION, "cam_side", cam_side))
	cam_up = float(cfg.get_value(SECTION, "cam_up", cam_up))


func _save_layout() -> void:
	var cfg := ConfigFile.new()
	cfg.load(SETTINGS)
	for id in _show:
		cfg.set_value(SECTION, "show_" + String(id), bool(_show[id]))
	for id in _offset:
		cfg.set_value(SECTION, "at_" + String(id), _offset[id])
	cfg.set_value(SECTION, "cam_side", cam_side)
	cfg.set_value(SECTION, "cam_up", cam_up)
	cfg.save(SETTINGS)


func _part_rect(id: String) -> Rect2:
	var c := hud.size * 0.5 + (_offset.get(id, Vector2.ZERO) as Vector2)
	match id:
		"lights":
			return Rect2(c + Vector2(-129, 0), Vector2(258, 44))
		"flash":
			return Rect2(c + Vector2(-150, -22), Vector2(300, 30))
	return Rect2(c, Vector2.ZERO)


func _set_editing(v: bool) -> void:
	if v == _editing:
		return
	_editing = v
	_drag = ""
	hud.mouse_filter = Control.MOUSE_FILTER_STOP if v else Control.MOUSE_FILTER_IGNORE
	if v:
		_build_panel()
	elif _panel:
		_panel.queue_free()
		_panel = null
		_save_layout()


func _build_panel() -> void:
	_panel = PanelContainer.new()
	_panel.position = Vector2(40, 140)
	var box := VBoxContainer.new()
	_panel.add_child(box)
	var title := Label.new()
	title.text = "COMBAT HUD - drag the boxes to move them"
	box.add_child(title)
	for part in PARTS:
		var cb := CheckBox.new()
		cb.text = String(part[1])
		cb.button_pressed = bool(_show.get(part[0], true))
		var id := String(part[0])
		cb.toggled.connect(func(on_: bool):
			_show[id] = on_
			_save_layout())
		box.add_child(cb)
	# the camera over your shoulder (action combat only): the crosshair off the back of your head
	for s in [["Camera: to the side", "cam_side", -1.5, 1.5], ["Camera: higher", "cam_up", -0.5, 1.2]]:
		var lab := Label.new()
		lab.text = String(s[0])
		box.add_child(lab)
		var sl := HSlider.new()
		sl.min_value = float(s[2])
		sl.max_value = float(s[3])
		sl.step = 0.05
		sl.value = float(get(String(s[1])))
		sl.custom_minimum_size = Vector2(220, 18)
		var key := String(s[1])
		sl.value_changed.connect(func(val: float):
			set(key, val)
			_save_layout())
		box.add_child(sl)
	var row := HBoxContainer.new()
	box.add_child(row)
	var reset := Button.new()
	reset.text = "Reset positions"
	reset.pressed.connect(func():
		for id in DEFAULT_OFFSET:
			_offset[id] = DEFAULT_OFFSET[id]
		_save_layout())
	row.add_child(reset)
	var done := Button.new()
	done.text = "Done"
	done.pressed.connect(func(): _set_editing(false))
	row.add_child(done)
	_layer.add_child(_panel)


func _hud_input(event: InputEvent) -> void:
	if not _editing:
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_drag = ""
			for id in DEFAULT_OFFSET:
				if _part_rect(String(id)).has_point(event.position):
					_drag = String(id)
					_drag_from = event.position - (_offset[id] as Vector2)
					break
		else:
			if _drag != "":
				_save_layout()
			_drag = ""
		hud.accept_event()
	elif event is InputEventMouseMotion and _drag != "":
		_offset[_drag] = event.position - _drag_from
		hud.accept_event()


func _draw_attacker_ring(w: Dictionary, now: int, font: Font) -> void:
	var p := _player()
	var n := _view(int(w.oid))
	if p == null or p.camera == null or n == null:
		return
	var total := maxf(1.0, float(int(w.end) - int(w.start)))
	var t := clampf((now - int(w.start)) / total, 0.0, 1.0)
	var left := int(w.end) - now
	var hot := left <= _press_window() and left > -60
	var col := Color(1.0, 0.82, 0.3) if hot else Color(1.0, 0.3, 0.2, 0.9)
	var head := n.global_position + Vector3(0, n.height * 0.65, 0)
	var size := hud.size
	var at := p.camera.unproject_position(head)
	var behind := p.camera.is_position_behind(head)
	if not behind and Rect2(Vector2(24, 24), size - Vector2(48, 48)).has_point(at):
		var dist := maxf(1.0, p.camera.global_position.distance_to(head))
		var scale := clampf(8.0 / dist, 0.45, 1.3)
		hud.draw_arc(at, lerpf(64.0, 14.0, t) * scale, 0.0, TAU, 48, col, 3.0 if hot else 2.0)
		hud.draw_arc(at, 14.0 * scale, 0.0, TAU, 32, Color(1, 1, 1, 0.3), 1.0)
		return
	# off screen: an arrow on the edge, pointing at it
	var centre := size * 0.5
	var dir := (at - centre) * (-1.0 if behind else 1.0)
	if dir.length() < 1.0:
		dir = Vector2(0, 1)
	dir = dir.normalized()
	var reach := minf(size.x, size.y) * 0.42
	var tip := centre + dir * reach
	var side := Vector2(-dir.y, dir.x)
	var grow := lerpf(10.0, 18.0, t)
	hud.draw_colored_polygon(PackedVector2Array([tip + dir * grow, tip - dir * grow * 0.4 + side * grow * 0.7,
			tip - dir * grow * 0.4 - side * grow * 0.7]), col)


func _draw_hud() -> void:
	var p := _player()
	if p == null or not on:
		return
	var now := Time.get_ticks_msec()
	var c := hud.size * 0.5
	var font := ThemeDB.fallback_font
	if _locked() and not _editing:
		_draw_lock(p, now)
	elif _show.get("crosshair", true) and (not p.action_cursor or _editing):
		var cross := Color(1, 1, 1, 0.85)
		if is_instance_valid(_aim):
			cross = Color(0.35, 1.0, 0.45, 0.95) if _ally(_aim) else Color(1.0, 0.35, 0.3, 0.95)
		hud.draw_circle(c, 1.6, cross)
		for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
			hud.draw_line(c + d * 6.0, c + d * 12.0, cross, 1.5)
	# a held attack charging toward the anytime style
	if _show.get("charge", true) and _atk_down and _anytime_ready():
		var f := clampf((now - _atk_at) / (HOLD_S * 1000.0), 0.0, 1.0)
		hud.draw_arc(c, 16.0, -PI * 0.5, -PI * 0.5 + TAU * f, 40,
				Color(1.0, 0.82, 0.3) if f >= 1.0 else Color(1, 1, 1, 0.7), 2.5 if f >= 1.0 else 2.0)
	elif _show.get("charge", true) and _atk_down and _has_anytime and now < _style_at:
		# held before the power attack can go: a dim ring fills toward it (gold above once the style is ready)
		var r := clampf(float(now - _atk_at) / float(maxi(1, _style_at - _atk_at)), 0.0, 1.0)
		hud.draw_arc(c, 16.0, 0.0, TAU, 40, Color(0, 0, 0, 0.3), 2.0)
		hud.draw_arc(c, 16.0, -PI * 0.5, -PI * 0.5 + TAU * r, 40, Color(1, 1, 1, 0.45), 2.0)
	# the bow's draw: a ring filling around the crosshair - gold when fully drawn, then red as it overdraws
	if _drawing and _show.get("draw", true):
		var held := now - _draw_at
		var full := float(_draw_full) if _draw_full > 0 else 1.0e9
		var fill := clampf(held / full, 0.0, 1.0)
		var r := 26.0
		hud.draw_arc(c, r, 0.0, TAU, 48, Color(0, 0, 0, 0.35), 4.0)
		if held < full:
			hud.draw_arc(c, r, -PI * 0.5, -PI * 0.5 + TAU * fill, 48, Color(1, 1, 1, 0.85), 3.0)
		elif held < full + _draw_grace and not _overdraw:
			hud.draw_arc(c, r, 0.0, TAU, 48, Color(1.0, 0.82, 0.3), 3.5)          # full draw: loose now
		else:
			var o := clampf((held - full - _draw_grace) / 2500.0, 0.0, 1.0)
			var pulse := 0.6 + 0.4 * sin(now * 0.02)
			hud.draw_arc(c, r, 0.0, TAU, 48, Color(1.0, 0.82 * (1.0 - o), 0.3 * (1.0 - o), pulse), 3.5 + 2.0 * o)
			hud.draw_arc(c, r + 6.0, -PI * 0.5, -PI * 0.5 + TAU * o, 48, Color(1.0, 0.2, 0.15, 0.9), 2.5)
		if _draw_crit:
			hud.draw_string(font, c + Vector2(-60, r + 22.0), "CRITICAL SHOT", HORIZONTAL_ALIGNMENT_CENTER, 120.0, 11,
					Color(1.0, 0.85, 0.35, 0.9))
		# out of the bow's reach (the server's own range: the bow's type, Archery Range, the arrows, height): said here
		var tgt = viewer.npcs.target if viewer and viewer.npcs else null
		if _draw_reach > 0 and is_instance_valid(tgt):
			var tn := tgt as Node3D
			var dist := Vector2(tn.global_position.x - p.global_position.x, tn.global_position.z - p.global_position.z).length() / 0.025
			var reach := _draw_reach + (p.global_position.y - tn.global_position.y) / 0.025 / 2.0
			if dist > reach:
				hud.draw_string(font, c + Vector2(-80, r + 36.0), "OUT OF RANGE  %d / %d" % [roundi(dist), roundi(reach)],
						HORIZONTAL_ALIGNMENT_CENTER, 160.0, 11, Color(1.0, 0.4, 0.3, 0.95))
	# the swing timer: the arc under the crosshair empties as your weapon recovers - grey until a plain swing can go,
	# then white (a swing now lands for part of its damage) until it's whole (full damage, styles ready)
	if _show.get("timer", true) and now < _timer_until:
		var r := float(_timer_until - now) / float(_timer_len)
		var col := Color(0.6, 0.6, 0.6, 0.35) if now < _quick_at else Color(1, 1, 1, 0.6)
		hud.draw_arc(c, 24.0, PI * 0.5 - PI * 0.35 * r, PI * 0.5 + PI * 0.35 * r, 24, col, 2.0)
	# monsters winding up a blow at you: a ring closing in on each of them (an arrow at the screen's edge when one is
	# off screen or behind you) - gold while a parry would catch it
	if _show.get("windup", true):
		for w in _windups:
			_draw_attacker_ring(w, now, font)
	if _show.get("windup_cross", false):
		for w in _windups:
			var total := maxf(1.0, float(int(w.end) - int(w.start)))
			var t := clampf((now - int(w.start)) / total, 0.0, 1.0)
			var left := int(w.end) - now
			var hot := left <= _press_window() and left > -60
			var rad := lerpf(78.0, 20.0, t)
			hud.draw_arc(c, rad, 0.0, TAU, 56, Color(1.0, 0.82, 0.3) if hot else Color(1.0, 0.3, 0.2, 0.85), 3.0 if hot else 2.0)
		if not _windups.is_empty():
			hud.draw_arc(c, 20.0, 0.0, TAU, 40, Color(1, 1, 1, 0.25), 1.0)
	# the ready lights
	if _ranged() and not _editing:
		if _show.get("lights", true):
			var ar := _part_rect("lights")
			var q := int(Server.get("active_quiver"))
			var e: Dictionary = PlayerData.entry(13 + q) if q > 0 else {}
			var it: Dictionary = PlayerData.item_at(13 + q) if q > 0 else {}
			var txt := "NO ARROWS SELECTED (CTRL+Q)" if it.is_empty() else "%s  x%d   [%d/4]" % [String(it.get("name", "")).to_upper(), int(e.get("count", 1)), q]
			hud.draw_string(font, ar.position + Vector2(0, 15), txt, HORIZONTAL_ALIGNMENT_CENTER, ar.size.x, 12,
					Color(1.0, 0.45, 0.35) if it.is_empty() else Color(0.9, 0.9, 0.85, 0.9))
	elif _show.get("lights", true) or _editing:
		var lr := _part_rect("lights")
		var names := [["ac_position", "POSITION", Color(0.45, 0.85, 1.0)], ["ac_reactive", "REACTIVE", Color(1.0, 0.8, 0.3)],
				["ac_chain", "CHAIN", Color(0.8, 0.55, 1.0)]]
		var w := 86.0
		var dim := 1.0 if _show.get("lights", true) else 0.35
		for i in names.size():
			var lit := _ready.length() > i and _ready[i] == "1"
			var col: Color = names[i][2] if lit else Color(0.6, 0.6, 0.6, 0.35)
			col.a *= dim
			var rect := Rect2(lr.position + Vector2(i * w + 4.0, 0), Vector2(w - 8.0, 20.0))
			hud.draw_rect(rect, Color(0, 0, 0, (0.45 if lit else 0.25) * dim))
			hud.draw_rect(rect, col, false, 1.5)
			var keys: Array = Keybinds.bindings.get(String(names[i][0]), [])
			var label := "%s %s" % [String(keys[0]) if keys.size() > 0 else "-", String(names[i][1])]
			hud.draw_string(font, rect.position + Vector2(0, 15), label, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x, 12, col)
		if (_ready.length() > 3 and _ready[3] == "1") or _editing:
			hud.draw_string(font, lr.position + Vector2(69, 38), "HOLD: ANYTIME", HORIZONTAL_ALIGNMENT_CENTER, 120.0, 11,
					Color(1, 1, 1, 0.55 * dim))
		if _bag_used() and not _editing:                    # the poison set on its way to your weapons
			var bag: Dictionary = Server.poison_bag
			var set_i := int(bag.get("set", 0))
			var sl: Array = bag.get("slots", [])
			var a_name := String(sl[set_i * 2].get("name", "-")) if sl.size() > set_i * 2 else "-"
			var b_name := String(sl[set_i * 2 + 1].get("name", "-")) if sl.size() > set_i * 2 + 1 else "-"
			hud.draw_string(font, lr.position + Vector2(0, 54), "POISONS %d: %s / %s" % [set_i + 1,
					a_name if a_name != "" else "-", b_name if b_name != "" else "-"], HORIZONTAL_ALIGNMENT_CENTER, lr.size.x, 10,
					Color(0.6, 0.95, 0.5, 0.8 * dim))
	if (_show.get("flash", true) and now < _flash_until) or _editing:
		var fr := _part_rect("flash")
		var a := clampf((_flash_until - now) / 400.0, 0.0, 1.0) if not _editing else (1.0 if _show.get("flash", true) else 0.35)
		var fc := _flash_color if not _editing else Color(1.0, 0.85, 0.35)
		fc.a = a
		hud.draw_string(font, fr.position + Vector2(0, 22), _flash_text if not _editing else "PARRY  -12",
				HORIZONTAL_ALIGNMENT_CENTER, fr.size.x, 22, fc)
	if _editing:
		for id in DEFAULT_OFFSET:
			var r := _part_rect(String(id))
			hud.draw_rect(r, Color(1, 1, 1, 0.7 if _drag == id else 0.35), false, 1.0)
