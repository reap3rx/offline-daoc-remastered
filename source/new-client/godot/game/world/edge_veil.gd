extends Node
## The world's edge (owner 2026-11-01: "set up invisible barriers so that the player character can't walk up to the
## edge of the map, and ... mask the borders so you can't see the edge of the geometry in any way"). A region's outer
## edges - zone sides with no built zone beyond them (zones_index.json) - get two things:
##   - a barrier: you stop MARGIN_M short of the edge and slide along it (allows(), Player._client_move);
##   - a veil: land beyond the edge that holds up for a while (how long meanders along the edge) and then falls away
##     into a sea - one for the whole region, its lowest outer-edge water or under its lowest outer-edge ground - that
##     runs on under the fog to the horizon round every built zone. Falling away (rather than rising into hills) leaves
##     no far rim to see the end of, from the ground or from up high. The land beyond is one height field over the
##     region (each built zone's edge heights carried outward, the highest wins; read from the zones' files, so it is
##     the same whatever has loaded): neighbouring zones' skirts meet exactly, gaps between zones fill as saddles.
##     Drawn with each zone's ground (painted colours + detail) and its water for higher lakes; no collision.
##   - a fog bank along it (owner 2026-11-01: "a dense fog near the barriers ... thicker as you approach ... invisible
##     once you're far enough away"): volumetric fog thickening over the last FOG_RAMP_M before an outer edge and
##     thick beyond it; it is drawn only within the volumetric fog's reach round the camera (110 m), so from farther
##     off there is none, and it hides the seams where the land beyond meets the zone. Remastered look only.
## Zone sides shared with another built zone of the region are left alone: the land goes on there.

const BLOCK_M := 204.8                       # one zones.dat block (8192 units)
const MARGIN_M := 28.0                       # how far short of the edge you stop
const ALONG_M := 6.4                         # skirt sample spacing along the edge (2 ground cells)
const OUT_M := [0.0, 3.2, 8.0, 16.0, 28.0, 45.0, 68.0, 98.0, 135.0, 180.0, 235.0, 300.0, 380.0, 470.0, 580.0, 720.0, 900.0]
const SEA_DEPTH := 18.0                      # how far under the sea the skirt ends
const FOG_RAMP_M := 90.0                     # the fog bank thickens over this far before an outer edge
const FOG_DENSITY := 0.08                    # ... to this beyond it (about 40 m of it hides everything)
const LAKE_OUT_M := 60.0                     # a lake higher than the sea goes on this far before the land falls

var region: RegionWorld
var _blocks := {}                            # Vector2i -> true: the region's built blocks
var _region_id := -1
var _sea_y := INF                            # the region's sea level
var _sea: MeshInstance3D                     # the sea: a plane round the camera, cut away over the built blocks
var _sea_mat: ShaderMaterial
var _fog: FogVolume                          # the fog bank: a box round the camera, thick only near outer edges
var _fog_mat: ShaderMaterial
var _mask_min := Vector2i.ZERO               # the built-blocks mask's first block
var _zones := []                             # the region's built outdoor zones: their rectangles and ground (_load_zones)


func setup(r: RegionWorld) -> void:
	region = r
	region.zone_added.connect(_veil)
	_veil(region.current)


func _process(_dt: float) -> void:
	if region == null or region.current == null or _sea == null or _fog == null:
		return
	var z := region.current
	var me := region.entry(int(z.info.id))
	var on := not z.city and not bool(z.info.get("dungeon", false)) and not me.is_empty() \
			and int(me.get("region", -1)) == _region_id and _sea_y < INF
	_sea.visible = on
	_fog.visible = on
	var cam := get_viewport().get_camera_3d()
	if not on or cam == null:
		return
	# the current zone's corner sits at the scene origin: the region's blocks from there
	_sea_mat.set_shader_parameter("origin_m", -Vector2(float(me.x), float(me.y)) * BLOCK_M)
	_fog_mat.set_shader_parameter("origin_m", -Vector2(float(me.x), float(me.y)) * BLOCK_M)
	_fog.global_position = cam.global_position
	var env := cam.get_world_3d().environment
	if env == null and cam.environment:
		env = cam.environment
	if env:
		_fog_mat.set_shader_parameter("glow", env.fog_light_color)
	var reach := cam.far + 400.0
	_sea_mat.set_shader_parameter("fade_r", cam.far)
	var pm := _sea.mesh as PlaneMesh
	if absf(pm.size.x - reach * 2.0) > 50.0:
		pm.size = Vector2(reach * 2.0, reach * 2.0)
	_sea.global_position = Vector3(snappedf(cam.global_position.x, 64.0), _sea_y, snappedf(cam.global_position.z, 64.0))


const SEA_SHADER := """
shader_type spatial;
render_mode cull_back, blend_mix, depth_draw_always;
uniform sampler2D built : filter_nearest;
uniform ivec2 mask_min;
uniform ivec2 mask_size;
uniform vec2 origin_m;
uniform float block_m;
uniform float fade_r = 3000.0;
uniform vec3 deep : source_color = vec3(0.07, 0.17, 0.23);
varying vec3 wpos;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
void fragment() {
	ivec2 b = ivec2(floor((wpos.xz - origin_m) / block_m)) - mask_min;
	if (b.x >= 0 && b.y >= 0 && b.x < mask_size.x && b.y < mask_size.y && texelFetch(built, b, 0).r > 0.5) {
		discard;
	}
	vec2 p = wpos.xz;
	float t = TIME;
	vec3 n = normalize(vec3(0.035 * sin(p.x * 0.11 + t * 0.9) + 0.02 * sin(p.y * 0.23 - t * 1.3 + p.x * 0.05),
			1.0, 0.035 * cos(p.y * 0.13 + t * 0.7) + 0.02 * cos(p.x * 0.19 + t * 1.1)));
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	ALBEDO = deep;
	// out at the far clip it fades away rather than ending on a line against the sky
	vec3 cam = INV_VIEW_MATRIX[3].xyz;
	ALPHA = 1.0 - smoothstep(fade_r * 0.6, fade_r * 0.97, length(wpos.xz - cam.xz));
	ROUGHNESS = 0.06;
	SPECULAR = 0.55;
}
"""


const FOG_SHADER := """
shader_type fog;
uniform sampler2D built : filter_nearest;
uniform ivec2 mask_min;
uniform ivec2 mask_size;
uniform vec2 origin_m;
uniform float block_m;
uniform float ramp_m;
uniform float density;
uniform vec3 albedo : source_color = vec3(0.82, 0.86, 0.9);
uniform float fog_glow = 0.2;
uniform vec3 glow : source_color = vec3(0.6, 0.7, 0.8);   // the scene's fog colour: lit evenly, it matches the distance
bool is_built(ivec2 b) {
	ivec2 m = b - mask_min;
	return m.x >= 0 && m.y >= 0 && m.x < mask_size.x && m.y < mask_size.y && texelFetch(built, m, 0).r > 0.5;
}
void fog() {
	vec2 p = (WORLD_POSITION.xz - origin_m) / block_m;
	ivec2 cell = ivec2(floor(p));
	float d = 0.0;
	if (is_built(cell)) {
		// metres to the nearest block with nothing built (the ramp is shorter than a block: the 8 round it)
		d = 1e9;
		for (int dy = -1; dy <= 1; dy++) {
			for (int dx = -1; dx <= 1; dx++) {
				ivec2 c = cell + ivec2(dx, dy);
				if ((dx == 0 && dy == 0) || is_built(c)) continue;
				vec2 lo = vec2(c);
				vec2 gap = max(lo - p, vec2(0.0)) + max(p - (lo + 1.0), vec2(0.0));
				d = min(d, length(gap) * block_m);
			}
		}
	}
	float k = 1.0 - smoothstep(0.0, ramp_m, d);
	// softened at the box's top and bottom (it rides with the camera)
	k *= smoothstep(0.0, 0.15, UVW.y) * (1.0 - smoothstep(0.85, 1.0, UVW.y));
	DENSITY = density * k;
	ALBEDO = albedo;
	EMISSION = glow * (fog_glow * k);
}
"""


## The region's sea: made once its level is known, its mask of built blocks kept with the region.
func _make_sea() -> void:
	if _sea_y == INF:
		return
	if _sea == null:
		_sea_mat = ShaderMaterial.new()
		var sh := Shader.new()
		sh.code = SEA_SHADER
		_sea_mat.shader = sh
		_sea_mat.set_shader_parameter("block_m", BLOCK_M)
		var pm := PlaneMesh.new()
		pm.subdivide_width = 2
		pm.subdivide_depth = 2
		_sea = MeshInstance3D.new()
		_sea.name = "Sea"
		_sea.mesh = pm
		_sea.material_override = _sea_mat
		_sea.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_sea.extra_cull_margin = 16384.0
		region.viewer.add_child(_sea)
		_fog_mat = ShaderMaterial.new()
		var fs := Shader.new()
		fs.code = FOG_SHADER
		_fog_mat.shader = fs
		_fog_mat.set_shader_parameter("block_m", BLOCK_M)
		_fog_mat.set_shader_parameter("ramp_m", FOG_RAMP_M)
		_fog_mat.set_shader_parameter("density", FOG_DENSITY)
		_fog = FogVolume.new()
		_fog.name = "EdgeFog"
		_fog.shape = RenderingServer.FOG_VOLUME_SHAPE_BOX
		_fog.size = Vector3(300.0, 500.0, 300.0)            # past the volumetric fog's 110 m reach all round
		_fog.material = _fog_mat
		region.viewer.add_child(_fog)
	var lo := Vector2i(1 << 20, 1 << 20)
	var hi := Vector2i(-(1 << 20), -(1 << 20))
	for b in _blocks:
		lo = Vector2i(mini(lo.x, b.x), mini(lo.y, b.y))
		hi = Vector2i(maxi(hi.x, b.x), maxi(hi.y, b.y))
	if _blocks.is_empty():
		lo = Vector2i.ZERO
		hi = Vector2i.ZERO
	var sz := hi - lo + Vector2i.ONE
	var img := Image.create(sz.x, sz.y, false, Image.FORMAT_R8)
	for b in _blocks:
		img.set_pixel(b.x - lo.x, b.y - lo.y, Color(1, 0, 0))
	_mask_min = lo
	_sea_mat.set_shader_parameter("built", ImageTexture.create_from_image(img))
	_sea_mat.set_shader_parameter("mask_min", lo)
	_sea_mat.set_shader_parameter("mask_size", sz)
	_fog_mat.set_shader_parameter("built", _sea_mat.get_shader_parameter("built"))
	_fog_mat.set_shader_parameter("mask_min", lo)
	_fog_mat.set_shader_parameter("mask_size", sz)


## The region's built outdoor zones from their files (so the land beyond is the same whichever zone you came in by):
## each one's rectangle (region metres), ground (the 2x grid the zone draws), water mask and levels.
func _load_zones() -> void:
	_zones.clear()
	for k in region._index:
		var e: Dictionary = region._index[k]
		if int(e.get("region", -2)) != _region_id or not bool(e.get("built", false)):
			continue
		var dir := "res://content/zones/zone%03d" % int(k)
		if not FileAccess.file_exists(dir.path_join("zone.json")):
			continue
		var info = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join("zone.json")))
		if not (info is Dictionary) or bool(info.get("city", false)) or bool(info.get("dungeon", false)):
			continue
		var hs := int(info.get("heights_2x_size", info.heights_size))
		var hts := FileAccess.get_file_as_bytes(dir.path_join(String(info.get("heights_2x", info.heights)))).to_float32_array()
		if hts.size() < hs * hs:
			continue
		var size := float(info.size_m)
		var c := {"id": int(k), "x0": float(e.x) * BLOCK_M, "y0": float(e.y) * BLOCK_M, "w": float(e.w) * BLOCK_M,
				"h": float(e.h) * BLOCK_M, "size": size, "hs": hs, "cell": size / float(hs - 1), "hts": hts,
				"mask": null, "levels": {}}
		if info.has("water_mask"):
			c.mask = Image.load_from_file(dir.path_join(String(info.water_mask)))
		for body in info.get("water", []):
			c.levels[int(body.id)] = float(body.height)
		_zones.append(c)


static func _zh(c: Dictionary, x: float, y: float) -> float:
	var hs: int = c.hs
	var hts: PackedFloat32Array = c.hts
	var gx := clampf(x / float(c.cell), 0.0, hs - 1.001)
	var gz := clampf(y / float(c.cell), 0.0, hs - 1.001)
	var ix := int(gx)
	var iz := int(gz)
	var fx := gx - ix
	var fz := gz - iz
	var top := lerpf(hts[iz * hs + ix], hts[iz * hs + ix + 1], fx)
	var bottom := lerpf(hts[(iz + 1) * hs + ix], hts[(iz + 1) * hs + ix + 1], fx)
	return lerpf(top, bottom, fz)


static func _zw(c: Dictionary, x: float, y: float) -> float:
	var mask: Image = c.mask
	if mask == null:
		return -INF
	var n := mask.get_width()
	var size: float = c.size
	var id := roundi(mask.get_pixel(clampi(int(x / size * n), 0, n - 1), clampi(int(y / size * n), 0, n - 1)).r * 255.0)
	return float((c.levels as Dictionary).get(id, -INF))


## The region's sea level: the lowest water along its outer edges, or (lower) 12 m under its lowest outer-edge ground.
func _region_sea() -> float:
	var low_ground := INF
	var low_water := INF
	for c in _zones:
		var bx0 := int(round(float(c.x0) / BLOCK_M))
		var by0 := int(round(float(c.y0) / BLOCK_M))
		for bx in int(round(float(c.w) / BLOCK_M)):
			for by in int(round(float(c.h) / BLOCK_M)):
				# this block's sides with nothing built beyond: [first corner, along] in zone metres
				var sides := []
				if not _built(bx0 + bx, by0 + by - 1):
					sides.append([Vector2(bx, by), Vector2(1, 0)])
				if not _built(bx0 + bx, by0 + by + 1):
					sides.append([Vector2(bx, by + 1), Vector2(1, 0)])
				if not _built(bx0 + bx - 1, by0 + by):
					sides.append([Vector2(bx, by), Vector2(0, 1)])
				if not _built(bx0 + bx + 1, by0 + by):
					sides.append([Vector2(bx + 1, by), Vector2(0, 1)])
				for sd in sides:
					for i in 33:
						var q: Vector2 = ((sd[0] as Vector2) + (sd[1] as Vector2) * (i / 32.0)) * BLOCK_M
						var g := _zh(c, q.x, q.y)
						var l := _zw(c, q.x, q.y)
						if l > g:
							low_water = minf(low_water, l)
						else:
							low_ground = minf(low_ground, g)
	if low_ground == INF and low_water == INF:
		return INF
	return minf(low_water, low_ground - 12.0)


## The zones within reach of a stretch of land beyond (centre, region metres).
func _near(centre: Vector2, radius: float) -> Array:
	var out := []
	for c in _zones:
		var q := Vector2(clampf(centre.x, c.x0, c.x0 + c.w), clampf(centre.y, c.y0, c.y0 + c.h))
		if q.distance_to(centre) <= radius:
			out.append(c)
	return out


## The land beyond at region point p: for each zone near it, that zone's ground at its nearest edge point q carried
## out (a little of its relief mirrored in), held up for a while - how long varies along the edge, so a high rim's
## skyline beyond meanders - then falling away smoothly to under the sea by the skirt's full reach, with a gentle
## swell; the zones blend by nearness (each its own at its edge, so the land beyond meets it exactly; between two
## neighbours' skirts agree, and a gap between two zones fills as a saddle). Where
## the edge runs under a lake higher than the sea the ground stays under it for LAKE_OUT_M first.
func _land(p: Vector2, near: Array) -> float:
	var full: float = OUT_M[OUT_M.size() - 1]
	var sum := 0.0
	var wsum := 0.0
	for c in near:
		var x0: float = c.x0
		var y0: float = c.y0
		var q := Vector2(clampf(p.x, x0, x0 + float(c.w)), clampf(p.y, y0, y0 + float(c.h)))
		var dist := p.distance_to(q)
		if dist > full:
			continue
		var lq := q - Vector2(x0, y0)
		var g := _zh(c, lq.x, lq.y)
		if dist > 0.5:
			var m := lq + (q - p) / dist * minf(dist, float(c.size) * 0.45)
			g += (_zh(c, m.x, m.y) - g) * 0.4
		var hold := 0.5 + 0.3 * sin(q.x * 0.019 + q.y * 0.017 + 0.8) + 0.2 * sin(q.x * 0.047 - q.y * 0.043 + 2.1)
		var start := lerpf(20.0, 260.0, clampf(hold, 0.0, 1.0))
		var lake := _zw(c, lq.x, lq.y)
		if lake > _zh(c, lq.x, lq.y):
			g = minf(g, lake - 1.5)
			if lake > _sea_y + 0.5:
				start = maxf(start, LAKE_OUT_M)
		var h := g
		if dist > start:
			var t := clampf((dist - start) / (full - start), 0.0, 1.0)
			var swell := (6.0 * sin(p.x * 0.011 + p.y * 0.007 + 1.7) + 3.0 * sin(p.x * 0.029 - p.y * 0.033 + 0.4)) \
					* sin(PI * t) * (1.0 - t)
			h = lerpf(g, minf(g, _sea_y - SEA_DEPTH), smoothstep(0.0, 0.9, t)) + swell
		var wt := (1.0 - smoothstep(full * 0.6, full, dist)) / ((dist + 1.0) * (dist + 1.0))
		sum += h * wt
		wsum += wt
	return sum / wsum if wsum > 0.0 else _sea_y - SEA_DEPTH


func _refresh_blocks() -> void:
	var me := region.entry(int(region.current.info.id))
	var rid := int(me.get("region", -1))
	if rid == _region_id and not _blocks.is_empty():
		return
	_region_id = rid
	_blocks.clear()
	for k in region._index:
		var e: Dictionary = region._index[k]
		if int(e.get("region", -2)) != rid or not bool(e.get("built", false)):
			continue
		for bx in int(e.w):
			for by in int(e.h):
				_blocks[Vector2i(int(e.x) + bx, int(e.y) + by)] = true
	_load_zones()
	_sea_y = _region_sea()
	_make_sea()


func _built(bx: int, by: int) -> bool:
	return _blocks.has(Vector2i(bx, by))


## May you stand here (scene metres, the current zone's frame)? Not within MARGIN_M of an outer edge.
func allows(p: Vector3) -> bool:
	if region == null or region.current == null:
		return true
	_refresh_blocks()
	var me := region.entry(int(region.current.info.id))
	if me.is_empty():
		return true
	var bx := float(me.x) + p.x / BLOCK_M
	var bz := float(me.y) + p.z / BLOCK_M
	var m := MARGIN_M / BLOCK_M
	for d in [Vector2(0, 0), Vector2(m, 0), Vector2(-m, 0), Vector2(0, m), Vector2(0, -m),
			Vector2(m * 0.7, m * 0.7), Vector2(m * 0.7, -m * 0.7), Vector2(-m * 0.7, m * 0.7), Vector2(-m * 0.7, -m * 0.7)]:
		if not _built(floori(bx + d.x), floori(bz + d.y)):
			return false
	return true


## The skirts of one zone: every block-long stretch of its sides with no built zone beyond, and the outer corners.
func _veil(z: ZoneLoader) -> void:
	if z == null or z.city or bool(z.info.get("dungeon", false)):
		return
	_refresh_blocks()
	var e := region.entry(int(z.info.id))
	if e.is_empty() or int(e.get("region", -1)) != _region_id:
		return
	var size := float(z.info.size_m)
	var w := int(e.w)
	var h := int(e.h)
	var ex := int(e.x)
	var ey := int(e.y)
	var world0 := Vector2(ex * BLOCK_M, ey * BLOCK_M)       # the zone's corner in the region (metres): the hills' noise
	var mat := z.skirt_material()
	if _sea_y == INF:
		return
	var sea := _sea_y
	var root := Node3D.new()
	root.name = "EdgeVeil"
	z.add_child(root)
	# which corners get a fan: both sides open there and nothing built diagonally beyond
	var fan := {}
	var corners := {"nw": [Vector2(0, 0), Vector2(-1, -1), Vector2i(ex - 1, ey - 1), Vector2i(ex - 1, ey), Vector2i(ex, ey - 1)],
			"ne": [Vector2(size, 0), Vector2(1, -1), Vector2i(ex + w, ey - 1), Vector2i(ex + w, ey), Vector2i(ex + w - 1, ey - 1)],
			"sw": [Vector2(0, size), Vector2(-1, 1), Vector2i(ex - 1, ey + h), Vector2i(ex - 1, ey + h - 1), Vector2i(ex, ey + h)],
			"se": [Vector2(size, size), Vector2(1, 1), Vector2i(ex + w, ey + h), Vector2i(ex + w, ey + h - 1), Vector2i(ex + w - 1, ey + h)]}
	for k in corners:
		var c: Array = corners[k]
		var dg: Vector2i = c[2]
		var sa: Vector2i = c[3]
		var sb: Vector2i = c[4]
		fan[k] = not _built(dg.x, dg.y) and not _built(sa.x, sa.y) and not _built(sb.x, sb.y)
	# sides: [origin, along, outward, block beyond for segment k, segments, the corner fans at its two ends]
	var sides := [[Vector2(0, 0), Vector2(1, 0), Vector2(0, -1), Vector2i(ex, ey - 1), Vector2i(1, 0), w, "nw", "ne"],
			[Vector2(0, size), Vector2(1, 0), Vector2(0, 1), Vector2i(ex, ey + h), Vector2i(1, 0), w, "sw", "se"],
			[Vector2(0, 0), Vector2(0, 1), Vector2(-1, 0), Vector2i(ex - 1, ey), Vector2i(0, 1), h, "nw", "sw"],
			[Vector2(size, 0), Vector2(0, 1), Vector2(1, 0), Vector2i(ex + w, ey), Vector2i(0, 1), h, "ne", "se"]]
	for sd in sides:
		var b0: Vector2i = sd[3]
		var step: Vector2i = sd[4]
		var n: int = sd[5]
		var outward := Vector2i(int((sd[2] as Vector2).x), int((sd[2] as Vector2).y))
		var open := []
		for k in n:
			var b := b0 + step * k
			open.append(not _built(b.x, b.y))
		var reaches := []
		for k in n:
			reaches.append(_reach(b0 + step * k, outward))
		for k in n:
			if not open[k]:
				continue
			# an inner corner at an end: land built beyond the neighbouring stretch (its own skirt comes round the
			# corner at right angles - the two meet on the diagonal, mitred)
			var dg0: Vector2i = corners[sd[6]][2]
			var dg1: Vector2i = corners[sd[7]][2]
			var prev_inner: bool = not open[k - 1] if k > 0 else _built(dg0.x, dg0.y)
			var next_inner: bool = not open[k + 1] if k < n - 1 else _built(dg1.x, dg1.y)
			var reach: float = reaches[k]
			# the reach eases into the neighbouring stretches' over their shared ends (no step between them)
			var r_prev: float = reaches[k - 1] if k > 0 and open[k - 1] else reach
			var r_next: float = reaches[k + 1] if k < n - 1 and open[k + 1] else reach
			_strip(z, root, mat, sea, (sd[0] as Vector2) + (sd[1] as Vector2) * (k * BLOCK_M), sd[1], sd[2],
					size, world0, Vector3(r_prev, reach, r_next), prev_inner, next_inner)
	for k in corners:
		if fan[k]:
			var c: Array = corners[k]
			var dg: Vector2i = c[2]
			var d: Vector2 = c[1]
			var reach := minf(_reach(dg, Vector2i(int(d.x), 0)), _reach(dg, Vector2i(0, int(d.y))))
			_corner(z, root, mat, sea, c[0], d, size, world0, reach)


## How far the land beyond may reach from a block outside the edge: half the open ground to the next built block
## outward (another zone across a gap - its own skirt meets this one halfway), the full skirt when open beyond.
func _reach(b: Vector2i, outward: Vector2i) -> float:
	var full: float = OUT_M[OUT_M.size() - 1]
	for i in 3:
		var q := b + outward * i
		if _built(q.x, q.y):
			return clampf(i * BLOCK_M * 0.5, 40.0, full)
	return full


func _strip(z: ZoneLoader, root: Node3D, mat: Material, sea: float, origin: Vector2, along: Vector2,
		out: Vector2, size: float, world0: Vector2, reaches: Vector3, prev_inner: bool, next_inner: bool) -> void:
	var reach := reaches.y
	var count := int(round(BLOCK_M / ALONG_M))
	var lake := -INF                                        # a lake above the sea at this stretch of edge, if any
	for i in range(0, count + 1, 4):
		var p := origin + along * (i * ALONG_M) - out * 1.0
		var l := z.water_level_at(clampf(p.x, 0.0, size), clampf(p.y, 0.0, size))
		if l > -INF and l > z.height_at(clampf(p.x, 0.0, size), clampf(p.y, 0.0, size)):
			lake = maxf(lake, l)
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var rows := OUT_M.size()
	var full: float = OUT_M[rows - 1]
	var near := _near(world0 + origin + along * (BLOCK_M * 0.5) + out * (reach * 0.5), BLOCK_M * 0.5 + reach * 0.5 + full + 10.0)
	for i in count + 1:
		var e := origin + along * (i * ALONG_M)
		var sa := i * ALONG_M
		# the reach eases into the neighbouring stretches' over the shared ends
		var r_base := reach
		if sa < 100.0:
			r_base = lerpf((reaches.x + reach) * 0.5, reach, sa / 100.0)
		elif sa > BLOCK_M - 100.0:
			r_base = lerpf((reaches.z + reach) * 0.5, reach, (BLOCK_M - sa) / 100.0)
		# at an inner corner the skirt stops at the diagonal, where the skirt of the land round the corner takes over
		# (the same land, so they meet exactly)
		var r_here := r_base
		if prev_inner:
			r_here = minf(r_here, maxf(sa, 0.5))
		if next_inner:
			r_here = minf(r_here, maxf(BLOCK_M - sa, 0.5))
		for r in rows:
			var d: float = float(OUT_M[r]) / full * r_here
			var p := e + out * d
			verts.append(Vector3(p.x, _land(world0 + p, near), p.y))
			var m := e - out * minf(d, size * 0.45)       # the painted ground mirrored like the heights
			uvs.append(Vector2(clampf(m.x / size, 0.0, 1.0), clampf(m.y / size, 0.0, 1.0)))
	_add_mesh(root, mat, verts, uvs, count + 1, rows)
	if lake > sea + 0.5:                                    # a higher lake carries on a little before the land falls
		var wm := z.water_material_at(clampf(origin.x + along.x * BLOCK_M * 0.5 - out.x * 2.0, 0.0, size),
				clampf(origin.y + along.y * BLOCK_M * 0.5 - out.y * 2.0, 0.0, size))
		if wm:
			var lb := origin + along * BLOCK_M + out * minf(LAKE_OUT_M, reach * 0.3)
			_water_quad(root, wm, Vector2(minf(origin.x, lb.x), minf(origin.y, lb.y)),
					Vector2(absf(lb.x - origin.x), absf(lb.y - origin.y)), lake)


func _corner(z: ZoneLoader, root: Node3D, mat: Material, sea: float, at: Vector2, dir: Vector2,
		size: float, world0: Vector2, reach: float) -> void:
	var steps := 10
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var rows := OUT_M.size()
	var full: float = OUT_M[rows - 1]
	var near := _near(world0 + at + dir * (reach * 0.5), reach + full + 10.0)
	for i in steps + 1:
		# a quarter turn between the two outward directions of this corner
		var a := float(i) / steps * PI * 0.5
		var n := Vector2(dir.x * cos(a), dir.y * sin(a)).normalized()
		for r in rows:
			var d: float = float(OUT_M[r]) / full * reach
			var p := at + n * d
			verts.append(Vector3(p.x, _land(world0 + p, near), p.y))
			var m := at - n * minf(d, size * 0.45)
			uvs.append(Vector2(clampf(m.x / size, 0.0, 1.0), clampf(m.y / size, 0.0, 1.0)))
	_add_mesh(root, mat, verts, uvs, steps + 1, rows)


## A grid of (cols x rows) vertices (rows of one column together) as triangles facing up, with smooth normals.
func _add_mesh(root: Node3D, mat: Material, verts: PackedVector3Array, uvs: PackedVector2Array, cols: int, rows: int) -> void:
	var idx := PackedInt32Array()
	for c in cols - 1:
		for r in rows - 1:
			var a := c * rows + r
			var b := (c + 1) * rows + r
			idx.append_array([a, a + 1, b, b, a + 1, b + 1])
	# make every triangle face up whichever way the stretch runs: wound as the zone's ground is (Godot's front faces
	# go clockwise seen from the front - (v1 - v0) x (v2 - v0) points down for a face looking up)
	for t in range(0, idx.size(), 3):
		var p0 := verts[idx[t]]
		var nrm := (verts[idx[t + 1]] - p0).cross(verts[idx[t + 2]] - p0)
		if nrm.y > 0.0:
			var tmp := idx[t + 1]
			idx[t + 1] = idx[t + 2]
			idx[t + 2] = tmp
	var normals := PackedVector3Array()
	normals.resize(verts.size())
	for t in range(0, idx.size(), 3):
		var p0 := verts[idx[t]]
		var nrm := (verts[idx[t + 1]] - p0).cross(verts[idx[t + 2]] - p0)
		for k in 3:
			normals[idx[t + k]] -= nrm
	for i in normals.size():
		normals[i] = normals[i].normalized() if normals[i].length() > 0.0 else Vector3.UP
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, mat)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)


static func _water_quad(root: Node3D, wm: Material, lo: Vector2, sz: Vector2, level: float) -> void:
	var pm := PlaneMesh.new()
	pm.size = sz
	pm.subdivide_width = 8
	pm.subdivide_depth = 8
	var mi := MeshInstance3D.new()
	mi.mesh = pm
	mi.material_override = wm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position = Vector3(lo.x + sz.x * 0.5, level, lo.y + sz.y * 0.5)
	root.add_child(mi)
