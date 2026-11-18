extends Node3D
## Extra foliage (owner 2026-11-17: "planes could use some bushes and other types of foliage ... areas near map
## boundaries becoming thicker with hard to pass foliage like rhododendron or mountain laurels, big thorny looking
## vines"): bushes, scrub and saplings scattered over the open ground, and dense thickets along the world's edge
## where the barrier stops you (EdgeVeil), so the end of the land reads as a wall of growth. Made like the new
## trees (EZ-Tree, the originals' leaf and bark pictures; content/trees/bushes.json), drawn as real 3D bushes round
## you out to reach_m (Options > VIDEO > FOLIAGE DISTANCE), dissolving out there. Client-side decoration with no collision: you, bots and monsters walk
## through them like tall grass, so the server's paths are untouched.
## (preloaded as Foliage by ZoneViewer: a new class_name needs the editor to register it)
## One per loaded zone, a child of its ZoneLoader, in that zone's metres - like GroundClutter. Every bush is where
## the zone's own seed puts it: the same on every visit and for every player.
## Options > VIDEO > EXTRA FOLIAGE turns it off (Graphics: enabled).

const TreeSwap := preload("res://game/tree_swap.gd")
const DIR := "res://content/trees"
const CHUNK_M := 48.0
const CELL_M := 6.4
const REACH_M := 150.0              # the default reach (owner 2026-11-18: 105 m faded in too close)
const FADE_M := 30.0
const OPEN_PER_CELL := 0.24          # bushes per 6.4 m cell on full grass, in a clump (the noise below)
const SCATTER_PER_CELL := 0.02       # ... and anywhere grassy, between the clumps
const EDGE_BAND_M := 90.0            # thickets from the world's edge this far in (you stop 28 m short of it)
const EDGE_PER_CELL := 2.7           # ... this many per cell up to ~40 m in, thinning to none at the band's end
const MAX_SLOPE := 0.75              # rise over run: no bushes on steeper ground than ~37 degrees ...
const EDGE_MAX_SLOPE := 1.8          # ... but the edge thickets climb the hills and cliffs the world ends in (~60 degrees)
## The bushes of each realm: [kind, weight]. Open ground, then the edge thickets.
const PALETTES := {
	"hib": [[["h_gorse", 3], ["h_rhodo", 2], ["h_laurel", 2], ["h_holly", 1], ["h_sapling", 1]],
			[["h_thicket", 4], ["h_bramble", 3], ["h_rhodo", 2], ["h_laurel", 2]]],
	"alb": [[["a_hazel", 3], ["a_hawthorn", 2], ["a_bramble", 2], ["a_holly", 1], ["a_sapling", 1]],
			[["a_thicket", 4], ["a_bramble", 3], ["a_hawthorn", 2], ["a_holly", 1]]],
	"mid": [[["m_juniper", 3], ["m_heather", 3], ["m_birchscrub", 2], ["m_sapling", 1]],
			[["m_thicket", 4], ["m_bramble", 3], ["m_juniper", 2]]],
	"snow": [[["s_juniper", 3], ["s_scrub", 3], ["s_sapling", 1]],
			[["s_thicket", 4], ["s_juniper", 2], ["s_scrub", 2]]],
}

static var enabled := true
static var reach_m := REACH_M        # Options > VIDEO > FOLIAGE DISTANCE (Graphics: set_reach)
static var _mats: Array[ShaderMaterial] = []
static var _gen := 0                 # bumped when the reach changes: every zone's bushes are planted again
static var _kinds := {}              # kind -> {"meshes": [ArrayMesh], "sink": fraction of its height under ground}
static var _loaded := false

var zone: ZoneLoader
var viewer: Node3D
var edges: Node                      # EdgeVeil (null: no outer edges known)
var _realm := "hib"
var _dense: Image
var _avoid := {}                     # Vector2i (2 m cells) -> true: a building, a fixture, a trunk stands there
var _chunks := {}                    # Vector2i -> Node3D (its batches)
var _seed := 0
var _built_gen := 0


func setup(z: ZoneLoader, follow: Node3D, edge_veil: Node) -> bool:
	if z.city or bool(z.info.get("dungeon", false)) or "--no-foliage" in OS.get_cmdline_user_args():
		return false
	if not _load_kinds():
		return false
	zone = z
	viewer = follow
	edges = edge_veil
	_seed = int(z.info.id) * 7919
	_realm = _realm_of(z)
	var c = z.info.get("clutter")
	if c is Dictionary and c.has("densemap") and FileAccess.file_exists(z.dir.path_join(c.densemap)):
		_dense = Image.load_from_file(z.dir.path_join(c.densemap))
	_build_avoid()
	return true


## The slider moved: the fade follows at once, and the bushes are planted again out to the new reach.
static func set_reach(m: float) -> void:
	m = clampf(m, 60.0, 300.0)
	if is_equal_approx(m, reach_m):
		return
	reach_m = m
	for mat in _mats:
		mat.set_shader_parameter("fade_start", reach_m - FADE_M)
		mat.set_shader_parameter("fade_end", reach_m)
	_gen += 1


static func _realm_of(z: ZoneLoader) -> String:
	var id := int(z.info.id)
	var realm := "hib"
	if id < 100 or id == 250 or id == 253 or (id >= 260 and id < 266):
		realm = "alb"
	elif id < 180 or id == 251 or (id >= 266 and id < 272):
		realm = "mid"
	if realm == "mid":
		for m in z.info.get("models", []):           # (the snowy north: the zone's own trees are the snowy ones)
			var f := String((m as Dictionary).get("file", "")).to_lower()
			if f.contains("-s.") or f.contains("_s.") or f.contains("_s-"):
				return "snow"
	return realm


static func _load_kinds() -> bool:
	if _loaded:
		return not _kinds.is_empty()
	_loaded = true
	var path := DIR + "/bushes.json"
	if not FileAccess.file_exists(path):
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not d is Dictionary:
		return false
	for kind in d.get("kinds", {}):
		var k: Dictionary = d.kinds[kind]
		var tint := Color(k.get("tint", "#ffffff"))
		var h := float(k.get("height", 3.0))
		var leaves := ShaderMaterial.new()
		leaves.shader = TreeSwap.LEAVES_SHADER
		leaves.set_shader_parameter("albedo_tex", TreeSwap._texture(String(k.leaf)))
		leaves.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
		leaves.set_shader_parameter("height", h * 3.0)        # (sway: a bush moves less than a tree its height)
		var bark := ShaderMaterial.new()
		bark.shader = TreeSwap.BARK_SHADER
		bark.set_shader_parameter("albedo_tex", TreeSwap._texture(String(k.bark)))
		bark.set_shader_parameter("height", h * 3.0)
		for m in [leaves, bark]:
			m.set_shader_parameter("fade_start", reach_m - FADE_M)
			m.set_shader_parameter("fade_end", reach_m)
			_mats.append(m)
		var meshes: Array[ArrayMesh] = []
		for file in k.get("variants", []):
			var mesh := TreeSwap._load_glb(DIR + "/" + String(file), bark, leaves)
			if mesh:
				meshes.append(mesh)
		if not meshes.is_empty():
			_kinds[kind] = {"meshes": meshes, "sink": float(k.get("plant_sink", 0.2)), "height": h}
	return not _kinds.is_empty()


## Where nothing grows: under every placed object (its own size), round every trunk.
func _build_avoid() -> void:
	var radius := {}
	for f in zone.info.get("fixtures", []):
		var m := int(f.m)
		if not radius.has(m):
			var file := String((zone.info.models[m] as Dictionary).get("file", ""))
			var tree := TreeSwap.species_of(file) != "" or int(f.get("radius", 0)) > 0
			radius[m] = -1.0 if tree else float(zone.model_radius.get(m, 6.0))
		var sc := float(f.get("scale", 1.0))
		var r: float = radius[m] * sc + 1.0 if radius[m] > 0.0 else 2.2 * sc
		var p := Vector2(float(f.pos[0]), float(f.pos[2]))
		var n := ceili(r / 2.0)
		var c0 := Vector2i(floori(p.x / 2.0), floori(p.y / 2.0))
		for dz in range(-n, n + 1):
			for dx in range(-n, n + 1):
				var cc := c0 + Vector2i(dx, dz)
				if Vector2((cc.x + 0.5) * 2.0, (cc.y + 0.5) * 2.0).distance_to(p) <= r:
					_avoid[cc] = true


func _process(_dt: float) -> void:
	visible = enabled
	if not enabled or viewer == null:
		return
	var cam := get_viewport().get_camera_3d()
	if cam:
		RenderingServer.global_shader_parameter_set("tree_eye", cam.global_position)
	var p := to_local(viewer.global_position)
	var centre := Vector2i(floori(p.x / CHUNK_M), floori(p.z / CHUNK_M))
	if _built_gen != _gen:
		_built_gen = _gen
		for c in _chunks.keys():
			_chunks[c].queue_free()
		_chunks.clear()
	var reach := ceili(reach_m / CHUNK_M)
	var wanted := {}
	for dz in range(-reach, reach + 1):
		for dx in range(-reach, reach + 1):
			var c := centre + Vector2i(dx, dz)
			var mid := Vector2((c.x + 0.5) * CHUNK_M, (c.y + 0.5) * CHUNK_M)
			if mid.distance_to(Vector2(p.x, p.z)) < reach_m + CHUNK_M * 0.71:
				wanted[c] = true
	for c in _chunks.keys():
		if not wanted.has(c):
			_chunks[c].queue_free()
			_chunks.erase(c)
	for c in wanted:
		if not _chunks.has(c):
			_chunks[c] = _build_chunk(c)                    # (one a frame)
			return


func _dense_at(x: float, z: float) -> float:
	if _dense == null:
		return 0.45
	var n := _dense.get_width()
	var px := clampi(int(x / float(zone.info.size_m) * n), 0, n - 1)
	var pz := clampi(int(z / float(zone.info.size_m) * n), 0, n - 1)
	return _dense.get_pixel(px, pz).r


## Clumps: a smooth value noise over ~40 m, the same everywhere for this zone.
func _clump(x: float, z: float) -> float:
	var s := 40.0
	var gx := floori(x / s)
	var gz := floori(z / s)
	var fx := x / s - gx
	var fz := z / s - gz
	fx = fx * fx * (3.0 - 2.0 * fx)
	fz = fz * fz * (3.0 - 2.0 * fz)
	var a := _hash01(gx, gz)
	var b := _hash01(gx + 1, gz)
	var c := _hash01(gx, gz + 1)
	var d := _hash01(gx + 1, gz + 1)
	return lerpf(lerpf(a, b, fx), lerpf(c, d, fx), fz)


func _hash01(x: int, z: int) -> float:
	return float(hash(Vector3i(x, z, _seed)) & 0xffff) / 65535.0


## How far (metres) to the world's edge - the nearest side of a block with no built zone beyond it; INF without one.
func _edge_dist(x: float, z: float) -> float:
	if edges == null or not is_instance_valid(edges) or edges.get("region") == null:
		return INF
	var me: Dictionary = edges.region.entry(int(zone.info.id))
	if me.is_empty():
		return INF
	edges._refresh_blocks()
	var bm := 204.8                                   # (EdgeVeil.BLOCK_M: one zones.dat block)
	var bx := float(me.x) + x / bm
	var bz := float(me.y) + z / bm
	var b0 := Vector2i(floori(bx), floori(bz))
	var best := INF
	for dz in range(-1, 2):
		for dx in range(-1, 2):
			if dx == 0 and dz == 0:
				continue
			var b := b0 + Vector2i(dx, dz)
			if edges._built(b.x, b.y):
				continue
			# distance from the point to that block's square, in metres
			var ex := maxf(maxf(b.x - bx, bx - (b.x + 1)), 0.0)
			var ez := maxf(maxf(b.y - bz, bz - (b.y + 1)), 0.0)
			best = minf(best, Vector2(ex, ez).length() * bm)
	return best


func _build_chunk(c: Vector2i) -> Node3D:
	var root := Node3D.new()
	add_child(root)
	var open: Array = PALETTES[_realm][0]
	var thick: Array = PALETTES[_realm][1]
	var by_mesh := {}                                 # "kind/variant" -> Array[Transform3D]
	var cells := int(CHUNK_M / CELL_M)
	var size := float(zone.info.size_m)
	for cz in cells:
		for cx in cells:
			var wx := c.x * CHUNK_M + (cx + 0.5) * CELL_M
			var wz := c.y * CHUNK_M + (cz + 0.5) * CELL_M
			if wx < 0.0 or wz < 0.0 or wx >= size or wz >= size:
				continue
			var rng := RandomNumberGenerator.new()
			rng.seed = hash(Vector3i(int(wx / CELL_M), int(wz / CELL_M), _seed))
			var dense := _dense_at(wx, wz)
			var ed := _edge_dist(wx, wz)
			var n_edge := 0.0
			if ed < EDGE_BAND_M:
				n_edge = EDGE_PER_CELL * (1.0 - smoothstep(40.0, EDGE_BAND_M, ed)) * (0.7 + 0.6 * _clump(wx + 500.0, wz))
			var n_open := (OPEN_PER_CELL * smoothstep(0.5, 0.85, _clump(wx, wz)) + SCATTER_PER_CELL) * clampf(dense * 1.6, 0.0, 1.0)
			for pass_i in 2:
				var want := n_edge if pass_i == 1 else n_open
				var n := floori(want) + (1 if rng.randf() < want - floorf(want) else 0)
				for k in n:
					var x := wx + rng.randf_range(-0.5, 0.5) * CELL_M
					var z := wz + rng.randf_range(-0.5, 0.5) * CELL_M
					if _avoid.has(Vector2i(floori(x / 2.0), floori(z / 2.0))):
						continue
					var y := zone.height_at(x, z)
					if y < zone.water_level_at(x, z) - 0.05:
						continue
					var slope := maxf(absf(zone.height_at(x + 1.5, z) - zone.height_at(x - 1.5, z)),
							absf(zone.height_at(x, z + 1.5) - zone.height_at(x, z - 1.5))) / 3.0
					if slope > (EDGE_MAX_SLOPE if pass_i == 1 else MAX_SLOPE):
						continue
					var kind := _pick(thick if pass_i == 1 else open, rng)
					if not _kinds.has(kind):
						continue
					var kd: Dictionary = _kinds[kind]
					var v := rng.randi_range(0, (kd.meshes as Array).size() - 1)
					var sc := rng.randf_range(0.75, 1.25) * (rng.randf_range(1.0, 1.45) if pass_i == 1 else 1.0)
					var lean := Vector3(rng.randf_range(-1, 1), 0, rng.randf_range(-1, 1)).normalized() * rng.randf_range(0.0, 0.08)
					var b := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * sc)
					if lean.length() > 0.001:
						b = Basis(Vector3(lean.z, 0, -lean.x).normalized(), lean.length()) * b
					var o := Vector3(x, y - float(kd.sink) * float(kd.height) * sc - slope * 0.6 * sc, z)
					var key := "%s/%d" % [kind, v]
					if not by_mesh.has(key):
						by_mesh[key] = []
					by_mesh[key].append(Transform3D(b, o))
	for key in by_mesh:
		var list: Array = by_mesh[key]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		var kv := String(key).split("/")
		mm.mesh = _kinds[kv[0]].meshes[int(kv[1])]
		mm.instance_count = list.size()
		for i in list.size():
			mm.set_instance_transform(i, list[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.visibility_range_end = reach_m + CHUNK_M * 0.75
		root.add_child(mmi)
	return root


func _pick(pal: Array, rng: RandomNumberGenerator) -> String:
	var total := 0.0
	for e in pal:
		total += float(e[1])
	var r := rng.randf() * total
	for e in pal:
		r -= float(e[1])
		if r <= 0.0:
			return String(e[0])
	return String(pal[-1][0])
