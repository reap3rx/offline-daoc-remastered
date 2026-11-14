extends CanvasLayer
## Nameplates in the World of Warcraft way (owner 2026-11-13, ideas: "Make monsters you're targeting or that are damaged
## have nameplates. Make them customizable in the menu. Emulate WoW's nameplate system as much as possible.
## Unintrusive, but useful, so we don't have to rely on the target window."). Over the head of each monster shown: a
## slim health bar coloured by how it stands to you (red hostile, yellow neutral, green friendly), its name above the
## bar and its level beside it in its con colour, and under the bar a thin cast bar while it casts. Your target's plate
## is a size bigger with a white frame; the others are a little see-through while you have a target, as WoW's. Plates
## that would overlap move apart upwards (WoW's stacking plates), and they are drawn over the world, under every window.
## While a monster has a plate its ordinary overhead name (NamePlates) is hidden, so the name isn't shown twice.
## Options > Interface > NAMEPLATES (section "nameplates" of settings.cfg):
##   show       0 off, 1 your target only, 2 your target and monsters hurt or fighting (default), 3 every enemy near
##   friendly   your own realm's people and bots too (default off), by the same rule
##   health_text  0 none, 1 the health in percent on the bar
##   scale      0.7 - 1.6
##   stack      move overlapping plates apart (default on)
##   cast_bar   the cast bar under the plate (default on)

const RANGE := 40.0                         # metres: the overhead names' range (NamePlates.NAME_RANGE)
const BAR := Vector2(112, 8)                # px at 1080 lines and size 1.0
const HOSTILE := Color(0.82, 0.13, 0.1)
const NEUTRAL := Color(0.92, 0.78, 0.12)
const FRIEND := Color(0.2, 0.72, 0.22)
const CAST := Color(1.0, 0.72, 0.1)

var manager: NpcManager
var _canvas: Control
var _font: Font
var _plates: Array = []                     # this frame's plates: {n, rect, name, level, lcol, fill, frac, cast, tgt}

static var _opts := {}
static var _opts_at := -10.0


## The settings, read again at most once a second (Options writes them; reload() after a change).
static func opt(key: String) -> Variant:
	var now := Time.get_ticks_msec() / 1000.0
	if now - _opts_at > 1.0:
		_opts_at = now
		var cfg := UiArt.load_settings()
		_opts = {"show": int(cfg.get_value("nameplates", "show", 2)),
				"friendly": bool(cfg.get_value("nameplates", "friendly", false)),
				"health_text": int(cfg.get_value("nameplates", "health_text", 0)),
				"scale": float(cfg.get_value("nameplates", "scale", 1.0)),
				"stack": bool(cfg.get_value("nameplates", "stack", true)),
				"cast_bar": bool(cfg.get_value("nameplates", "cast_bar", true))}
	return _opts.get(key)


static func reload() -> void:
	_opts_at = -10.0


func _ready() -> void:
	layer = 1                                   # over the world, under the game's windows (GameUI is layer 5)
	_font = UiArt.font(true)
	_canvas = Control.new()
	_canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.draw.connect(_draw_plates)
	add_child(_canvas)


func _process(_delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	_gather()
	_canvas.queue_redraw()
	Perf.proc_add("health plates", Time.get_ticks_usec() - t0)


## Who gets a plate now, and where.
func _gather() -> void:
	_plates.clear()
	var cam := get_viewport().get_camera_3d()
	if manager == null or cam == null or manager.player == null or not is_instance_valid(manager.player):
		return
	var mode := int(opt("show"))
	var friendly := bool(opt("friendly"))
	var vp := get_viewport().get_visible_rect().size
	var s := vp.y / 1080.0 * clampf(float(opt("scale")), 0.5, 2.0)
	var pp := manager.player.global_position
	var casts: Dictionary = manager.get("cast_until") if "cast_until" in manager else {}
	var now := Time.get_ticks_msec()
	var have_target := manager.target != null and is_instance_valid(manager.target)
	for i in manager.active:
		var n: Npc = manager.active[i]
		if not is_instance_valid(n):
			continue
		var plate := false
		if mode > 0 and n.visible and n.state.alive:
			var tgt := n == manager.target
			var friend := n.is_friendly()
			var d := Vector2(n.global_position.x - pp.x, n.global_position.z - pp.z).length()
			var hidden := int(n.spawn.flags) & (Npc.FLAG_DONTSHOWNAME | Npc.FLAG_CANTTARGET) != 0
			if tgt:
				plate = not friend or friendly
			elif mode >= 2 and d <= RANGE and not hidden and (friendly or not friend):
				plate = mode == 3 and not friend or n.state.health < 0.995 or n.state.fighting
		if bool(n.get_meta("hp_plate", false)) != plate:
			n.set_meta("hp_plate", plate)
		if not plate:
			continue
		var head := n.global_position + Vector3(0, n.height + 0.45, 0)
		if cam.is_position_behind(head):
			continue
		var at := cam.unproject_position(head)
		if at.x < -200 or at.y < -100 or at.x > vp.x + 200 or at.y > vp.y + 100:
			continue
		var tgt2 := n == manager.target
		var size := BAR * s * (1.18 if tgt2 else 1.0)
		if int(opt("health_text")) > 0:
			size.y = maxf(size.y, 12.0 * s)
		var cast := -1.0
		var c: Array = casts.get(int(n.spawn.get("oid", -1)), [])
		if bool(opt("cast_bar")) and c.size() == 2 and now < int(c[1]):
			cast = clampf(float(now - int(c[0])) / maxf(1.0, float(int(c[1]) - int(c[0]))), 0.0, 1.0)
		# green your realm's; yellow a peaceful one (and, offline, a monster that won't attack first - the server
		# doesn't send how aggressive a monster is); red the rest
		var fill := HOSTILE
		if n.is_friendly():
			fill = FRIEND
		elif (int(n.spawn.flags) & Npc.FLAG_PEACE) != 0 or not Server.active and n.stance() in ["neutral", "friendly"]:
			fill = NEUTRAL
		var lvl := int(n.state.level)
		_plates.append({"n": n, "at": at, "size": size, "s": s, "name": String(n.spawn.get("name", "")),
				"level": str(lvl) if lvl > 0 else "", "lcol": n.con_color(PlayerData.level), "fill": fill,
				"frac": clampf(n.state.health, 0.0, 1.0), "cast": cast, "tgt": tgt2,
				"alpha": 1.0 if tgt2 or not have_target else 0.72,
				"dist": n.global_position.distance_to(cam.global_position)})
	# farther first, the target last (on top); then stacking: a plate that would cover one below it moves up over it
	_plates.sort_custom(func(a, b):
		if bool(a.tgt) != bool(b.tgt):
			return bool(b.tgt)
		return float(a.dist) > float(b.dist))
	for p in _plates:
		p["rect"] = _rect_of(p)
	if bool(opt("stack")) and _plates.size() > 1:
		var placed: Array = []
		var order := _plates.duplicate()
		order.sort_custom(func(a, b): return (a.rect as Rect2).position.y > (b.rect as Rect2).position.y)
		for p in order:
			var r: Rect2 = p.rect
			var moved := true
			var guard := 0
			while moved and guard < 12:
				moved = false
				guard += 1
				for q in placed:
					var o: Rect2 = q.rect
					if r.intersects(o):
						r.position.y = o.position.y - r.size.y - 1.0
						moved = true
			p["rect"] = r
			placed.append(p)


## The whole plate's box (name line, bar, cast bar) around its anchor over the head.
func _rect_of(p: Dictionary) -> Rect2:
	var s: float = p.s
	var size: Vector2 = p.size
	var name_h := _font.get_height(_name_px(p))
	var h := name_h + size.y + (5.0 * s if float(p.cast) >= 0.0 else 0.0)
	var w := size.x + 26.0 * s                         # (the level to the right)
	return Rect2(Vector2(p.at.x - size.x * 0.5, p.at.y - h), Vector2(w, h))


func _name_px(p: Dictionary) -> int:
	return maxi(9, roundi(13.0 * float(p.s) * (1.1 if bool(p.tgt) else 1.0)))


func _draw_plates() -> void:
	for p in _plates:
		var r: Rect2 = p.rect
		var s: float = p.s
		var a: float = p.alpha
		var size: Vector2 = p.size
		var npx := _name_px(p)
		var name_h := _font.get_height(npx)
		# the name, centred over the bar
		var nw := _font.get_string_size(String(p.name), HORIZONTAL_ALIGNMENT_LEFT, -1, npx).x
		var base := Vector2(r.position.x + size.x * 0.5 - nw * 0.5, r.position.y + _font.get_ascent(npx))
		var ncol := Color(1, 1, 1, a) if bool(p.tgt) else Color(0.92, 0.9, 0.85, a)
		_canvas.draw_string_outline(_font, base, String(p.name), HORIZONTAL_ALIGNMENT_LEFT, -1, npx,
				maxi(2, roundi(npx * 0.22)), Color(0, 0, 0, 0.85 * a))
		_canvas.draw_string(_font, base, String(p.name), HORIZONTAL_ALIGNMENT_LEFT, -1, npx, ncol)
		# the bar: frame, dark back, the health fill
		var bar := Rect2(Vector2(r.position.x, r.position.y + name_h), size)
		var frame := Color(1, 1, 1, 0.95) if bool(p.tgt) else Color(0, 0, 0, 0.9 * a)
		_canvas.draw_rect(bar.grow(1.0 if not bool(p.tgt) else 1.5), frame)
		_canvas.draw_rect(bar, Color(0.06, 0.05, 0.05, 0.82 * a))
		var fill: Color = p.fill
		fill.a = a
		_canvas.draw_rect(Rect2(bar.position, Vector2(size.x * float(p.frac), size.y)), fill)
		_canvas.draw_rect(Rect2(bar.position, Vector2(size.x * float(p.frac), maxf(1.0, size.y * 0.35))),
				Color(1, 1, 1, 0.12 * a))                    # (a little sheen on the top)
		if int(opt("health_text")) > 0:
			var tpx := maxi(8, roundi(size.y * 0.95))
			var txt := "%d%%" % roundi(float(p.frac) * 100.0)
			var tw := _font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx).x
			var tb := Vector2(bar.position.x + size.x * 0.5 - tw * 0.5, bar.position.y + size.y * 0.5 + _font.get_ascent(tpx) * 0.4)
			_canvas.draw_string_outline(_font, tb, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx, 2, Color(0, 0, 0, 0.9 * a))
			_canvas.draw_string(_font, tb, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx, Color(1, 1, 1, a))
		# the level, right of the bar in its con colour
		if String(p.level) != "":
			var lpx := maxi(8, roundi(11.0 * s))
			var lb := Vector2(bar.end.x + 4.0 * s, bar.position.y + size.y * 0.5 + _font.get_ascent(lpx) * 0.4)
			var lc: Color = p.lcol
			lc.a = a
			_canvas.draw_string_outline(_font, lb, String(p.level), HORIZONTAL_ALIGNMENT_LEFT, -1, lpx, 2, Color(0, 0, 0, 0.9 * a))
			_canvas.draw_string(_font, lb, String(p.level), HORIZONTAL_ALIGNMENT_LEFT, -1, lpx, lc)
		# the cast bar under it
		if float(p.cast) >= 0.0:
			var cb := Rect2(Vector2(bar.position.x, bar.end.y + 2.0 * s), Vector2(size.x, maxf(2.0, 3.0 * s)))
			_canvas.draw_rect(cb.grow(1.0), Color(0, 0, 0, 0.9 * a))
			var cc := CAST
			cc.a = a
			_canvas.draw_rect(Rect2(cb.position, Vector2(cb.size.x * float(p.cast), cb.size.y)), cc)
