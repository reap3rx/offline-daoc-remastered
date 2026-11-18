extends CanvasLayer
## Floating combat text (owner 2026-11-18 bugs doc: "making sure the numbers can't overlap. Maybe some animation choices
## for how they appear on the nameplates (rainfall, numbers getting blasted off of the nameplate, and any other ideas,
## selectable options in the options menu)"). The numbers are drawn flat on the screen at whole pixels, over the world
## and the nameplates and under the windows, and they follow whoever took the blow. No two cover each other: each
## frame a newer number that would touch an older one is moved up clear of it (and stays moved).
## Options > Interface > DAMAGE NUMBERS > STYLE (settings.cfg [interface] fct_style):
##   0 RISE      up and fade, as before
##   1 RAINFALL  drop from above the head and fade as they fall
##   2 BLAST     knocked off the head in an arc, crits harder
##   3 SCROLL    a column beside the head, each new one pushing the others up
##   4 FOUNTAIN  thrown up and out to either side in turn, falling away

const STYLES := ["Rise", "Rainfall", "Blast", "Scroll", "Fountain"]
const PIXEL := 0.0012                       # the old Label3D's pixel size: sizes keep their look on screen

var _canvas: Control
var _items: Array = []                      # {node, off, at, text, col, px, t, life, style, vel, pos, shift, crit, side}
var _font: Font
var _flip := 1.0

static var _style := 0
static var _style_at := -10.0


## The chosen style, read again at most once a second (Options writes it).
static func style() -> int:
	var now := Time.get_ticks_msec() / 1000.0
	if now - _style_at > 1.0:
		_style_at = now
		_style = clampi(int(UiArt.load_settings().get_value("interface", "fct_style", 0)), 0, STYLES.size() - 1)
	return _style


static func reload() -> void:
	_style_at = -10.0


func _ready() -> void:
	layer = 2                               # over the nameplates (1), under the game's windows (5)
	_font = UiArt.font(true, "damage")      # (Options > Interface > TEXT AND FONTS: damage numbers)
	_canvas = Control.new()
	_canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.draw.connect(_draw_items)
	add_child(_canvas)


## A number or word over `node` (its feet + `off`), or at `at` when there is no node. `size` is the old Label3D font
## size (48 a hit, 64 a crit); `incoming` marks your own damage taken (it goes the other side in SCROLL).
func add(node: Node3D, off: Vector3, at: Vector3, text: String, col: Color, size: int, crit := false, incoming := false) -> void:
	var st := style()
	var it := {"node": node, "off": off, "at": at, "text": text, "col": col, "size": size, "t": 0.0, "style": st,
			"crit": crit, "shift": Vector2.ZERO, "pos": Vector2.ZERO, "vel": Vector2.ZERO,
			"side": -1.0 if incoming else 1.0, "jit": Vector2(randf_range(-14, 14), randf_range(-4, 4)),
			"hidden": true, "anchor": Vector2.ZERO, "alpha": 0.0, "scale": 1.0, "px": 8}   # (placed at the next _process)
	match st:
		0:
			it.life = 1.1
		1:
			it.life = 1.25
			it.jit.x = randf_range(-26, 26)
		2:
			it.life = 1.0
			var a := deg_to_rad(randf_range(-150.0, -30.0))
			var sp := randf_range(240.0, 330.0) * (1.35 if crit else 1.0)
			it.vel = Vector2(cos(a), sin(a)) * sp
		3:
			it.life = 1.6
			it.jit = Vector2.ZERO
		_:
			it.life = 1.3
			_flip = -_flip
			it.vel = Vector2(_flip * randf_range(90.0, 170.0), -randf_range(260.0, 330.0) * (1.15 if crit else 1.0))
	_items.append(it)
	if _items.size() > 80:
		_items.pop_front()


func _process(delta: float) -> void:
	visible = not GameUI.interface_hidden
	if _items.is_empty():
		return
	var cam := get_viewport().get_camera_3d()
	var vp := get_viewport().get_visible_rect().size
	if cam == null:
		_items.clear()
		return
	var k := vp.y / (2.0 * tan(deg_to_rad(cam.fov * 0.5)))   # (screen px per world unit at unit distance)
	var s := vp.y / 1080.0
	var keep: Array = []
	for it in _items:
		it.t += delta
		if it.t >= it.life:
			continue
		var node = it.node
		if node != null and is_instance_valid(node) and node.is_inside_tree():
			it.at = (node as Node3D).global_position + (it.off as Vector3)
		it.hidden = cam.is_position_behind(it.at)
		it.anchor = cam.unproject_position(it.at)
		it.px = maxi(8, roundi(float(it.size) * PIXEL * k * UiArt.text_scale("damage")))
		var t: float = it.t
		var u := t / float(it.life)
		var p := Vector2.ZERO
		var sc := 1.0
		var a := 1.0
		match int(it.style):
			0:                                              # RISE
				p = Vector2(0, -78.0 * s * (1.0 - pow(1.0 - minf(t / 1.1, 1.0), 3.0)))
				a = 1.0 - clampf((t - 0.6) / 0.5, 0.0, 1.0)
				sc = lerpf(1.45, 1.0, clampf(t / 0.14, 0.0, 1.0)) if it.crit else 1.0
			1:                                              # RAINFALL
				p = Vector2(0, -95.0 * s + 0.5 * 260.0 * s * t * t + 30.0 * s * t)
				a = clampf(t / 0.12, 0.0, 1.0) * (1.0 - clampf((u - 0.55) / 0.45, 0.0, 1.0))
				sc = lerpf(1.3, 1.0, clampf(t / 0.2, 0.0, 1.0)) if it.crit else 1.0
			2:                                              # BLAST
				p = (it.vel as Vector2) * s * t + Vector2(0, 0.5 * 720.0 * s * t * t)
				a = 1.0 - clampf((u - 0.55) / 0.45, 0.0, 1.0)
				sc = lerpf(1.7 if it.crit else 1.3, 0.85, clampf(t / 0.35, 0.0, 1.0))
				if it.crit and t < 0.2:
					p += Vector2(randf_range(-3, 3), randf_range(-3, 3)) * s
			3:                                              # SCROLL
				p = Vector2(float(it.side) * 64.0 * s, -10.0 * s - 52.0 * s * t)
				a = clampf(t / 0.1, 0.0, 1.0) * (1.0 - clampf((u - 0.7) / 0.3, 0.0, 1.0))
				sc = lerpf(1.35, 1.0, clampf(t / 0.15, 0.0, 1.0)) if it.crit else 1.0
			_:                                              # FOUNTAIN
				p = (it.vel as Vector2) * s * t + Vector2(0, 0.5 * 820.0 * s * t * t)
				a = 1.0 - clampf((u - 0.6) / 0.4, 0.0, 1.0)
				sc = lerpf(1.4, 1.0, clampf(t / 0.2, 0.0, 1.0)) if it.crit else 1.0
		it.pos = p + (it.jit as Vector2) * s
		it.scale = sc
		it.alpha = a
		keep.append(it)
	_items = keep
	_unstack()
	_canvas.queue_redraw()


## The box a number covers this frame (its own place + how far it was moved off the others).
func _rect(it: Dictionary) -> Rect2:
	var px := maxi(6, roundi(float(it.px) * float(it.scale)))
	var w := _font.get_string_size(String(it.text), HORIZONTAL_ALIGNMENT_LEFT, -1, px).x
	var h := _font.get_height(px)
	var c: Vector2 = (it.anchor as Vector2) + (it.pos as Vector2) + (it.shift as Vector2)
	return Rect2(c - Vector2(w * 0.5, h), Vector2(w, h)).grow(2.0)


## No overlap: oldest first, each newer number that touches one already placed goes up clear of it. The move is kept
## (it only grows), so a number never jumps back and forth.
func _unstack() -> void:
	var placed: Array = []
	for it in _items:
		if it.hidden:
			continue
		var r := _rect(it)
		var guard := 0
		var moved := true
		while moved and guard < 16:
			moved = false
			guard += 1
			for o in placed:
				if r.intersects(o):
					var up := r.end.y - (o as Rect2).position.y
					it.shift = (it.shift as Vector2) + Vector2(0, -up)
					r.position.y -= up
					moved = true
		placed.append(r)


func _draw_items() -> void:
	for it in _items:
		if it.hidden or float(it.alpha) <= 0.0:
			continue
		var px := maxi(6, roundi(float(it.px) * float(it.scale)))
		var text := String(it.text)
		var w := _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, px).x
		var c: Vector2 = (it.anchor as Vector2) + (it.pos as Vector2) + (it.shift as Vector2)
		var base := Vector2(roundf(c.x - w * 0.5), roundf(c.y - _font.get_descent(px)))
		var col: Color = it.col
		col.a *= float(it.alpha)
		_canvas.draw_string_outline(_font, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, px, maxi(3, roundi(px * 0.2)),
				Color(0, 0, 0, 0.9 * col.a))
		_canvas.draw_string(_font, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, px, col)
