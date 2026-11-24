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
const CAST := Color(0.72, 0.35, 1.0)                  # purple: a spell you can interrupt (owner 2026-11-19)
const ENDURANCE := Color(0.35, 0.85, 0.3)             # its endurance - its poise (owner 2026-11-19, MonsterMoves)
const POWER := Color(0.3, 0.55, 1.0)                  # its power, when it has any

var manager: NpcManager
var _canvas: Control
var _font: Font
var _lvl_font: Font                         # (the level: the bold face made heavier still)
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
				"cast_bar": bool(cfg.get_value("nameplates", "cast_bar", true)),
				"lines": bool(cfg.get_value("nameplates", "lines", true)),
				"line_px": float(cfg.get_value("nameplates", "line_px", 4.0))}
	return _opts.get(key)


static func reload() -> void:
	_opts_at = -10.0


func _ready() -> void:
	layer = 1                                   # over the world, under the game's windows (GameUI is layer 5)
	_font = UiArt.font(true, "plates")
	var heavy := FontVariation.new()
	heavy.base_font = _font
	heavy.variation_embolden = 0.9
	_lvl_font = heavy
	_canvas = Control.new()
	_canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.draw.connect(_draw_plates)
	add_child(_canvas)


func _process(_delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	_canvas.visible = not GameUI.interface_hidden          # (Alt+Z: the interface hidden)
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
			var hidden := int(n.spawn.flags) & (Npc.FLAG_DONTSHOWNAME | Npc.FLAG_CANTTARGET) != 0 or n.is_critter()
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
		# no level beside the bar any more (everyone fights on one footing, owner 2026-11-19): the border's colour
		# says how strong it is next to you instead
		_plates.append({"n": n, "at": at, "size": size, "s": s, "name": String(n.spawn.get("name", "")),
				"title": String(NamePlates.titles.get(int(n.spawn.get("oid", -1)), "")),
				"level": "", "lcol": n.con_color(PlayerData.level), "fill": fill, "edge": n.strength_color(),
				# the name in the colour it had before the plate came up (its con colour; your realm's green)
				# (owner 2026-11-23)
				"ncol": NamePlates.FRIENDLY if n.is_friendly() else n.con_color(PlayerData.level),
				"boss": is_boss(n),
				"frac": clampf(n.state.health, 0.0, 1.0), "cast": cast, "tgt": tgt2,
				"vit": manager.vit.get(int(n.spawn.get("oid", -1)), [100, -1]) if "vit" in manager else [100, -1],
				"dbf": _debuffs_of(n) if tgt2 else [],
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


## The debuffs on your target, over its name (owner 2026-11-20: "can we show them on the target nameplate, the icon?"):
## the server's list (#DBF, TargetDebuffs.cs), each icon with its seconds left under it; the ones run out are dropped.
const DEBUFF_PX := 26.0                     # icon size at 1080 lines and size 1.0


func _debuffs_of(n: Npc) -> Array:
	if not "debuffs" in manager:
		return []
	var now := Time.get_ticks_msec()
	var out := []
	for e in manager.debuffs.get(int(n.spawn.get("oid", -1)), []):
		if int(e[1]) == 0 or int(e[1]) > now:
			out.append(e)
	return out


## A bot's reputation title (NamePlates.titles), small and gold over its name.
func _title_px(p: Dictionary) -> int:
	return maxi(8, roundi(_name_px(p) * 0.8))


func _title_h(p: Dictionary) -> float:
	return 0.0 if String(p.get("title", "")) == "" else _font.get_height(_title_px(p))


func _debuff_h(p: Dictionary) -> float:
	return 0.0 if (p.get("dbf", []) as Array).is_empty() else (DEBUFF_PX + 11.0) * float(p.s)


## The whole plate's box (name line, bar, cast bar) around its anchor over the head.
func _rect_of(p: Dictionary) -> Rect2:
	var s: float = p.s
	var size: Vector2 = p.size
	var name_h := _font.get_height(_name_px(p))
	var h := name_h + size.y + (5.0 * s if float(p.cast) >= 0.0 else 0.0) + _lines_h(p) + _debuff_h(p) + _title_h(p)
	var left := _left_w(p)                             # (the level - and a boss's skull - to the left of the bar)
	return Rect2(Vector2(p.at.x - size.x * 0.5 - left, p.at.y - h), Vector2(size.x + left, h))


## The level, large and bold, left of the bar (owner 2026-11-14: "Put the level in large and bold on the left side of the
## health, and if the mob is a boss mob, then put a skull icon next to it").
## The endurance line (every plate) and the power line under it (only what has power), under the health bar.
func _line_px(p: Dictionary) -> float:
	return maxf(2.0, float(opt("line_px")) * float(p.s))


func _lines_h(p: Dictionary) -> float:
	if not bool(opt("lines")):
		return 0.0
	var v: Array = p.get("vit", [100, -1])
	return (_line_px(p) + 1.5) * (2.0 if int(v[1]) >= 0 else 1.0) + 1.0


func _level_px(p: Dictionary) -> int:
	return maxi(12, roundi(21.0 * float(p.s) * (1.1 if bool(p.tgt) else 1.0) * UiArt.text_scale("plates")))


func _left_w(p: Dictionary) -> float:
	var w := 0.0
	if String(p.level) != "":
		w += _lvl_font.get_string_size(String(p.level), HORIZONTAL_ALIGNMENT_LEFT, -1, _level_px(p)).x + 5.0 * float(p.s)
	if bool(p.boss):
		w += _skull_w(p) + 3.0 * float(p.s)
	return w


func _skull_w(p: Dictionary) -> float:
	return 17.0 * float(p.s)


## A boss: a named monster - in DAoC their names are capitalised (a "Grimwold", not a "crypt spider").
static func is_boss(n: Npc) -> bool:
	var nm := String(n.spawn.get("name", "")).strip_edges()
	if nm == "" or int(n.spawn.get("realm", 0)) != 0:
		return false
	var c := nm.substr(0, 1)
	return c != c.to_lower()


## A small skull (vector: the round head, its jaw and teeth, two dark eyes) in the box (centre c, size w).
func _skull(c: Vector2, w: float, a: float) -> void:
	var bone := Color(0.93, 0.9, 0.82, a)
	var dark := Color(0.08, 0.04, 0.03, a)
	_canvas.draw_circle(c + Vector2(0, -w * 0.1), w * 0.5 + 1.0, Color(0, 0, 0, 0.85 * a))
	_canvas.draw_rect(Rect2(c + Vector2(-w * 0.3 - 1.0, w * 0.05), Vector2(w * 0.6 + 2.0, w * 0.45 + 1.0)), Color(0, 0, 0, 0.85 * a))
	_canvas.draw_circle(c + Vector2(0, -w * 0.1), w * 0.5, bone)
	_canvas.draw_rect(Rect2(c + Vector2(-w * 0.3, w * 0.05), Vector2(w * 0.6, w * 0.42)), bone)
	_canvas.draw_circle(c + Vector2(-w * 0.2, -w * 0.08), w * 0.15, dark)
	_canvas.draw_circle(c + Vector2(w * 0.2, -w * 0.08), w * 0.15, dark)
	_canvas.draw_colored_polygon(PackedVector2Array([c + Vector2(0, w * 0.06), c + Vector2(-w * 0.07, w * 0.2),
			c + Vector2(w * 0.07, w * 0.2)]), dark)
	for k in [-1, 0, 1]:
		_canvas.draw_line(c + Vector2(k * w * 0.13, w * 0.3), c + Vector2(k * w * 0.13, w * 0.47), dark, maxf(1.0, w * 0.06))


func _name_px(p: Dictionary) -> int:
	return maxi(9, roundi(13.0 * float(p.s) * (1.1 if bool(p.tgt) else 1.0) * UiArt.text_scale("plates")))


func _draw_plates() -> void:
	for p in _plates:
		var r: Rect2 = p.rect
		var s: float = p.s
		var a: float = p.alpha
		var size: Vector2 = p.size
		var npx := _name_px(p)
		var name_h := _font.get_height(npx)
		var left := _left_w(p)
		# its debuffs in a row over the name, centred, each with its seconds left
		var dbf: Array = p.get("dbf", [])
		if not dbf.is_empty():
			var ip := DEBUFF_PX * s
			var gap := 3.0 * s
			var row_w := dbf.size() * ip + (dbf.size() - 1) * gap
			var x0 := r.position.x + left + size.x * 0.5 - row_w * 0.5
			var now := Time.get_ticks_msec()
			var tpx := maxi(8, roundi(9.0 * s))
			for k in dbf.size():
				var e: Array = dbf[k]
				var ic := Server.skill_icon("spell", int(e[0]))
				var tex: Texture2D = ItemDb.icon(int(ic[0]))
				var box := Rect2(Vector2(roundf(x0 + k * (ip + gap)), roundf(r.position.y)), Vector2(ip, ip))
				_canvas.draw_rect(box.grow(1.5), Color(0.55, 0.05, 0.05, a))     # (a red edge: a debuff)
				if tex:
					_canvas.draw_texture_rect(tex, box, false, Color(1, 1, 1, a))
				if int(e[1]) > 0:
					var secs := ceili((int(e[1]) - now) / 1000.0)
					var txt := "%d" % secs if secs < 60 else "%dm" % ceili(secs / 60.0)
					var tw := _font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx).x
					var tb := Vector2(box.position.x + ip * 0.5 - tw * 0.5, box.end.y + _font.get_ascent(tpx) + 1.0)
					_canvas.draw_string_outline(_font, tb, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx, 2, Color(0, 0, 0, 0.9 * a))
					_canvas.draw_string(_font, tb, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx, Color(1, 1, 1, a))
			r.position.y += _debuff_h(p)
		# a bot's title over its name
		var title := String(p.get("title", ""))
		if title != "":
			var tpx2 := _title_px(p)
			var tw2 := _font.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx2).x
			var tb2 := Vector2(r.position.x + left + size.x * 0.5 - tw2 * 0.5, r.position.y + _font.get_ascent(tpx2))
			var tc := NamePlates.TITLE_COLOR
			tc.a = a
			_canvas.draw_string_outline(_font, tb2, title, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx2, maxi(2, roundi(tpx2 * 0.22)), Color(0, 0, 0, 0.85 * a))
			_canvas.draw_string(_font, tb2, title, HORIZONTAL_ALIGNMENT_LEFT, -1, tpx2, tc)
			r.position.y += _title_h(p)
		# the name, centred over the bar
		var nw := _font.get_string_size(String(p.name), HORIZONTAL_ALIGNMENT_LEFT, -1, npx).x
		var base := Vector2(r.position.x + left + size.x * 0.5 - nw * 0.5, r.position.y + _font.get_ascent(npx))
		var ncol: Color = p.get("ncol", Color(0.92, 0.9, 0.85))
		if bool(p.tgt):
			ncol = ncol.lightened(0.2)                       # (your target's a touch brighter)
		ncol.a = a
		_canvas.draw_string_outline(_font, base, String(p.name), HORIZONTAL_ALIGNMENT_LEFT, -1, npx,
				maxi(2, roundi(npx * 0.22)), Color(0, 0, 0, 0.85 * a))
		_canvas.draw_string(_font, base, String(p.name), HORIZONTAL_ALIGNMENT_LEFT, -1, npx, ncol)
		# the bar: frame, dark back, the health fill
		var bar := Rect2(Vector2(r.position.x + left, r.position.y + name_h), size)
		var frame := Color(1, 1, 1, 0.95) if bool(p.tgt) else Color(0, 0, 0, 0.9 * a)
		if p.get("edge") != null:
			var ec: Color = p.edge
			ec.a = 0.95 if bool(p.tgt) else 0.85 * a
			_canvas.draw_rect(bar.grow(2.5 if bool(p.tgt) else 1.5), Color(0, 0, 0, 0.9 * a))
			frame = ec
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
		# the level, large and bold left of the bar in its con colour; a boss's skull before it
		var lx := bar.position.x - 5.0 * s
		if String(p.level) != "":
			var lpx := _level_px(p)
			var lw := _lvl_font.get_string_size(String(p.level), HORIZONTAL_ALIGNMENT_LEFT, -1, lpx).x
			lx -= lw
			var lb := Vector2(lx, bar.position.y + size.y * 0.5 + _lvl_font.get_ascent(lpx) * 0.36)
			var lc: Color = p.lcol
			lc.a = a
			_canvas.draw_string(_lvl_font, lb + Vector2(1.5, 1.5) * s, String(p.level), HORIZONTAL_ALIGNMENT_LEFT, -1, lpx,
					Color(0, 0, 0, 0.9 * a))                     # (a drop shadow, then the dark edge, then the number)
			_canvas.draw_string_outline(_lvl_font, lb, String(p.level), HORIZONTAL_ALIGNMENT_LEFT, -1, lpx,
					maxi(3, roundi(lpx * 0.18)), Color(0, 0, 0, 0.95 * a))
			_canvas.draw_string(_lvl_font, lb, String(p.level), HORIZONTAL_ALIGNMENT_LEFT, -1, lpx, lc)
			lx -= 3.0 * s
		if bool(p.boss):
			var sw := _skull_w(p)
			_skull(Vector2(lx - sw * 0.5, bar.position.y + size.y * 0.5), sw, a)
		# its endurance (green) and, if it has any, its power (blue): thin lines under the bar
		var v: Array = p.get("vit", [100, -1])
		var ly := bar.end.y + 2.0
		var lh := _line_px(p)
		for pair in ([[int(v[0]), ENDURANCE], [int(v[1]), POWER]] if bool(opt("lines")) else []):
			if int(pair[0]) < 0:
				continue
			var lb := Rect2(Vector2(bar.position.x, ly), Vector2(size.x, lh))
			_canvas.draw_rect(lb.grow(0.5), Color(0, 0, 0, 0.85 * a))
			var lc: Color = pair[1]
			lc.a = a
			_canvas.draw_rect(Rect2(lb.position, Vector2(lb.size.x * clampf(int(pair[0]) / 100.0, 0.0, 1.0), lh)), lc)
			ly += lh + 1.5
		# the cast bar under them
		if float(p.cast) >= 0.0:
			var cb := Rect2(Vector2(bar.position.x, ly + 2.0 * s), Vector2(size.x, maxf(2.0, 3.0 * s)))
			_canvas.draw_rect(cb.grow(1.0), Color(0, 0, 0, 0.9 * a))
			var cc := CAST
			cc.a = a
			_canvas.draw_rect(Rect2(cb.position, Vector2(cb.size.x * float(p.cast), cb.size.y)), cc)
