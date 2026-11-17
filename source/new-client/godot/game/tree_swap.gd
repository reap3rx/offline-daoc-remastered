extends RefCounted
## (preloaded as TreeSwap by ZoneLoader and Graphics: a new class_name needs the editor to register it)
## The new trees (owner 2026-11-17: "I want to replace all of the trees, eventually, so none of the bad looking low
## poly ones exist" - EZ-Tree, a painterly look that still belongs in DAoC, the same kind of tree as the one it
## replaces, no two alike). content/trees/trees.json names the original tree models that have a replacement and the
## species each becomes; every species has a handful of variants (made by source/new-client/pipeline/trees: EZ-Tree in
## a headless browser, the original trees' own bark and leaf colours). ZoneLoader asks build() for each placed model:
## each tree becomes one of its species' variants, picked by where it stands (the same one every visit), at the
## original's place, turn and size. Collision, the bots' paths and the falling leaves keep the original's footprint.
##   Near (within NEAR_M): the real tree, bark and leaves, swaying, casting shadows.
##   Beyond: a far card that turns to the camera and shows that variant photographed from the nearest of eight
##   directions, lit like the near tree, out to the original's own draw range (times Options > VIDEO view
##   distance).
##   The hand-over is per tree and in time, not in distance (owner 2026-11-17: the distance cross-fade left trees
##   half see-through when you stood still, and whole batches judged by their middle went missing): a tree that
##   crosses NEAR_M (HYST either side, so standing on the line doesn't flicker) dithers from one to the other over
##   FADE_S seconds, then is wholly one. TreeSwap.Driver, one per zone, watches the distances and sets each tree's
##   instance data; the shaders read it.
##   Its collision is its own trunk (owner 2026-11-17: "the new tree trunks have the same collision as the old ones
##   ... running into an invisible wall"): the original's stand-in square (2 x Radius, up to 14 m across) becomes a
##   post the width of the new trunk, and the camera no longer bumps the old canopy's faces.
## Each tree stands on the ground at its spot (the lowest of five points round its trunk), not at the original's
## base: the originals carried metres of trunk underground (owner 2026-11-17: "some trees are too low into the
## ground").
## Options > VIDEO > REMASTERED TREES (Graphics "remastered_trees") switches it; it takes effect as zones load.

const DIR := "res://content/trees"
const NEAR_M := 75.0
## (tests: --tree-near=<metres> moves the switch, to compare the near and far trees from one spot)
static var near_m := -1.0
## Options > VIDEO > TREE DETAIL DISTANCE (Graphics): the hand-over for an ordinary tree, metres; set_detail applies a
## change to the trees already built (owner 2026-11-17: "sliders ... what level of fade out vs performance")
static var detail_m := NEAR_M
static var _drivers: Array = []                  # weakrefs to the zones' Drivers
static var _fixed := false                       # (--tree-near: one hand-over for every tree, the slider ignored)
const HYST := 5.0                   # metres nearer than the hand-over before a tree in view becomes the real one
const LATE := 30.0                  # metres past it before a tree in view becomes the far card
const EARLY := 20.0                 # out of view: the real tree within this far past the hand-over
const HEIGHT_K := 2.6               # a tall tree hands over further out: its height x this, if more than NEAR_M
const FADE_S := 0.7                 # seconds a tree takes to change
const GROW := 1.06                  # a little taller than made, and stood deeper (owner 2026-11-17: some feet showed)
const DEEP := 1.85                  # metres (at scale 1) the trunk's foot goes under the lowest ground round it
const CELL_M := 48.0                # real trees batched per 48 m square (a batch is culled by its middle)
const FAR_CELL_M := 128.0           # far cards per 128 m square: a card is one quad, cheap even where it is hidden
const FAR_REACH := FAR_CELL_M * 0.75
const LEAVES_SHADER := preload("res://game/tree_leaves.gdshader")
const BARK_SHADER := preload("res://game/tree_bark.gdshader")
const FAR_SHADER := preload("res://game/tree_far.gdshader")

## Graphics "remastered_trees" (set by Graphics._statics; zones build on worker threads - a plain static)
static var enabled := true

static var _mutex := Mutex.new()
static var _manifest = null                 # trees.json, or {} when there is none
static var _species := {}                    # species -> {near: Array[ArrayMesh], far_mesh, far_mat}
static var _far_quad: ArrayMesh


static func _load_manifest() -> Dictionary:
	if _manifest == null:
		var f := FileAccess.open(DIR + "/trees.json", FileAccess.READ)
		_manifest = JSON.parse_string(f.get_as_text()) if f else {}
		if not (_manifest is Dictionary):
			_manifest = {}
	return _manifest


## The species that replaces this original model (its file name without the extension), or "".
static func species_of(model_file: String) -> String:
	var m: Dictionary = _load_manifest()
	return String(m.get("models", {}).get(model_file.get_file().get_basename().to_lower(), ""))


static func _near_init() -> void:
	if near_m >= 0.0:
		return
	near_m = detail_m
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--tree-near="):
			near_m = float(a.split("=", true, 1)[1])
			_fixed = true


## The slider moved: the hand-over for the trees to come and the ones already standing.
static func set_detail(m: float) -> void:
	detail_m = clampf(m, 40.0, 250.0)
	_near_init()
	if _fixed:
		return
	near_m = detail_m
	var keep := []
	for w in _drivers:
		var d = w.get_ref()
		if d != null and is_instance_valid(d):
			d.retune(near_m)
			keep.append(w)
	_drivers = keep


## Draw these placed trees as the new ones, under `parent` (the zone). False: no replacement for this model - the
## caller draws the original.
static func build(parent: Node3D, model_file: String, xforms_in: Array[Transform3D], _cell_m: float, far: float, view_mult: float,
		zone_id := -1, ground := Callable()) -> bool:
	var cell_m := CELL_M
	var xforms := xforms_in
	if not enabled or xforms.is_empty() or "--classic-trees" in OS.get_cmdline_user_args():
		return false
	var zones: Array = _load_manifest().get("zones", [])          # (the pilot: Lough Derg only, until it is signed off)
	if not zones.is_empty() and not (float(zone_id) in zones or zone_id in zones):
		return false
	var sp := species_of(model_file)
	if sp == "":
		return false
	_near_init()
	_mutex.lock()
	var s = _species.get(sp)
	if s == null:
		s = _load_species(sp)
		_species[sp] = s
	_mutex.unlock()
	if s.is_empty():
		return false
	if ground.is_valid():
		xforms = _on_ground(xforms_in, ground, float(s.sink))
	var nvar: int = s.near.size()
	# each tree: its variant (by where it stands) and its map cell
	var groups := {}                            # Vector3i(cell x, cell z, variant) -> Array[int]
	var cells := {}                             # Vector2i -> Array[int]
	for i in xforms.size():
		var o := xforms[i].origin
		var v := posmod(hash(Vector2i(roundi(o.x * 4.0), roundi(o.z * 4.0))), nvar)
		var c := Vector2i(clampi(int(o.x / cell_m), 0, 255), clampi(int(o.z / cell_m), 0, 255))
		var k := Vector3i(c.x, c.y, v)
		if not groups.has(k):
			groups[k] = []
		groups[k].append(i)
		c = Vector2i(clampi(int(o.x / FAR_CELL_M), 0, 255), clampi(int(o.z / FAR_CELL_M), 0, 255))
		if not cells.has(c):
			cells[c] = []
		cells[c].append(i)
	var drv := _driver(parent)
	# (a tall tree hands over further out, where it is smaller on the screen: the 46 m grove pines' far cards, seen
	# from under them, matched them worst - owner 2026-11-17)
	# (by the height above the ground; at most 3x: Iarnwood's 150 m trees stand in hundreds)
	var ratio := 1.0 if _fixed else clampf((float(s.height) - float(s.sink)) * HEIGHT_K / NEAR_M, 1.0, float(s.max_ratio))
	var at_m := near_m * ratio
	var base := drv.add_trees(xforms, ratio, float(s.height))    # (each tree's slot in the driver)
	# near: the real trees, one batch per variant per cell
	var reach := CELL_M * 0.75                          # (a batch's middle to its far corner, and some)
	for k in groups:
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true                       # (y: how far the tree is into its change to the far card)
		mm.mesh = s.near[k.z]
		mm.instance_count = groups[k].size()
		for j in groups[k].size():
			mm.set_instance_transform(j, xforms[groups[k][j]])
			mm.set_instance_custom_data(j, Color(0, 1, 0, 0))
			drv.set_near(base + groups[k][j], mm, j)
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "Tree_%s_%d_%d_%d" % [sp, k.x, k.y, k.z]
		mmi.multimesh = mm
		mmi.visibility_range_end = at_m + LATE + reach
		drv.near_nodes.append([mmi, ratio])
		parent.add_child(mmi)
	# far: the crossed cards, one batch per cell (the variant rides in the instance's custom data)
	var cards: Array = s.far_cards
	for c in cells:
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		mm.mesh = s.far_mesh
		mm.instance_count = cells[c].size()
		for j in cells[c].size():
			var i: int = cells[c][j]
			var o := xforms[i].origin
			var v := posmod(hash(Vector2i(roundi(o.x * 4.0), roundi(o.z * 4.0))), nvar)
			var card: Dictionary = cards[v]
			var w := float(card.half) * 2.0
			var h := float(card.top) - float(card.bottom)
			mm.set_instance_transform(j, xforms[i] * Transform3D(Basis.from_scale(Vector3(w, h, w)), Vector3(0, float(card.bottom), 0)))
			mm.set_instance_custom_data(j, Color(float(v), 1, 0, 0))
			drv.set_far(base + i, mm, j, v)
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "TreeFar_%s_%d_%d" % [sp, c.x, c.y]
		mmi.multimesh = mm
		# (it casts a shadow too: in the shadow pass the card turns to the sun, so its shadow is the tree's; without one
		# the sunlit mist showed through the far trees as a milky veil)
		mmi.visibility_range_begin = maxf(at_m - HYST - FAR_REACH, 0.0)
		drv.far_nodes.append([mmi, ratio])
		mmi.set_meta("base_far", far)
		mmi.visibility_range_end = far * view_mult
		mmi.visibility_range_end_margin = far * view_mult * 0.1
		# (no fade mode: a fading instance is drawn in the transparent pass - no ambient occlusion, a milky look)
		parent.add_child(mmi)
	return true


## The trees stood on the ground: the trunk's foot (sink metres below the model's origin, times its scale) a little
## under the lowest ground round the trunk.
static func _on_ground(xforms: Array[Transform3D], ground: Callable, sink: float) -> Array[Transform3D]:
	var out: Array[Transform3D] = []
	out.resize(xforms.size())
	for i in xforms.size():
		var x := xforms[i]
		var b := x.basis.scaled(Vector3.ONE * GROW)
		var sc := b.get_scale().y
		var o := x.origin
		var r := 1.5 * sc
		var g := float(ground.call(o.x, o.z))
		for off in [Vector2(r, 0), Vector2(-r, 0), Vector2(0, r), Vector2(0, -r)]:
			g = minf(g, float(ground.call(o.x + off.x, o.z + off.y)))
		o.y = g - DEEP * sc + sink * sc
		out[i] = Transform3D(b, o)
	return out


static func _texture(file: String, mipmaps := true, compress := false) -> Texture2D:
	var img := Image.load_from_file(DIR + "/" + file)
	if img == null or img.is_empty():
		push_warning("trees: no texture %s" % file)
		return null
	if mipmaps:
		img.generate_mipmaps()
	if compress:
		img.compress(Image.COMPRESS_S3TC, Image.COMPRESS_SOURCE_SRGB)     # (the far atlases: a quarter of the memory)
	return ImageTexture.create_from_image(img)


static func _load_species(sp: String) -> Dictionary:
	var m: Dictionary = _load_manifest()
	var d: Dictionary = m.get("species", {}).get(sp, {})
	if d.is_empty():
		return {}
	var tint := Color(d.get("tint", "#ffffff"))
	var height := float(d.get("height", 25.0))
	# (tone, sat: a species held back from the rest - owner 2026-11-17: the far birches "pop too much")
	var tone := float(d.get("tone", 1.0))
	var sat := float(d.get("sat", 1.0))
	var leaves := ShaderMaterial.new()
	leaves.shader = LEAVES_SHADER
	leaves.set_shader_parameter("albedo_tex", _texture(String(d.leaf)))
	leaves.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b) * tone)
	leaves.set_shader_parameter("sat", sat)
	leaves.set_shader_parameter("height", height)
	var bark := ShaderMaterial.new()
	bark.shader = BARK_SHADER
	bark.set_shader_parameter("albedo_tex", _texture(String(d.bark)))
	bark.set_shader_parameter("height", height)
	bark.set_shader_parameter("tone", tone * float(d.get("bark_tone", 1.0)))
	bark.set_shader_parameter("sat", sat)
	bark.set_shader_parameter("uv_scale", Vector2(d.get("bark_uv", [1.0, 1.0])[0], d.get("bark_uv", [1.0, 1.0])[1]))
	var near: Array[ArrayMesh] = []
	var trunks: Array[PackedVector3Array] = []
	for file in d.get("variants", []):
		var mesh := _load_glb(DIR + "/" + String(file), bark, leaves)
		if mesh:
			near.append(mesh)
			trunks.append(_trunks(mesh))
	if near.is_empty():
		return {}
	var far := ShaderMaterial.new()
	far.shader = FAR_SHADER
	far.set_shader_parameter("atlas", _texture(String(d.far.atlas), true, true))
	far.set_shader_parameter("views", float(d.far.get("views", 8)))
	far.set_shader_parameter("rows", float(d.far.get("rows", near.size())))
	far.set_shader_parameter("tone", tone)
	far.set_shader_parameter("sat", sat)
	var quad := _far_quad_mesh().duplicate() as ArrayMesh
	quad.surface_set_material(0, far)
	return {"near": near, "far_mesh": quad, "far_cards": d.far.cards, "sink": float(d.get("sink", 0.0)), "trunks": trunks,
			"height": height, "max_ratio": float(d.get("max_ratio", 3.0))}


## One variant's glTF: its "bark" and "leaves" meshes as the two surfaces of one mesh.
static func _load_glb(path: String, bark: Material, leaves: Material) -> ArrayMesh:
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(path, st) != OK:
		push_warning("trees: can't read %s" % path)
		return null
	var root := doc.generate_scene(st)
	var out := ArrayMesh.new()
	for want in ["bark", "leaves"]:
		var mi := _find_mesh(root, want)
		if mi == null or mi.mesh == null or mi.mesh.get_surface_count() == 0:
			continue
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, mi.mesh.surface_get_arrays(0))
		out.surface_set_material(out.get_surface_count() - 1, bark if want == "bark" else leaves)
	root.free()
	return out if out.get_surface_count() > 0 else null


static func _find_mesh(n: Node, nm: String) -> MeshInstance3D:
	if n is MeshInstance3D and String(n.name).to_lower().begins_with(nm):
		return n
	for c in n.get_children():
		var r := _find_mesh(c, nm)
		if r:
			return r
	return null


## One unit card standing on the ground (x from -0.5 to 0.5, y from 0 to 1); the far shader turns it to the camera.
static func _far_quad_mesh() -> ArrayMesh:
	if _far_quad:
		return _far_quad
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var corners: Array[Vector3] = []
	var uvs: Array[Vector2] = []
	for c in [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]:
		corners.append(Vector3(c.x - 0.5, c.y, 0.0))
		uvs.append(Vector2(c.x, 1.0 - c.y))
	for idx in [0, 1, 2, 0, 2, 3]:
		st.set_normal(Vector3(0, 0, 1))
		st.set_uv(uvs[idx])
		st.add_vertex(corners[idx])
	_far_quad = st.commit()
	# (the card turns, so its box must hold it in any direction: as wide as it is deep)
	_far_quad.custom_aabb = AABB(Vector3(-0.5, 0, -0.5), Vector3(1, 1, 1))
	return _far_quad


# ---------------------------------------------------------------- collision: the new trunk

## The posts round the trunks of the new tree drawn for this placement (the zone's frame, before grounding): each
## Vector3(x offset, z offset, radius) in metres from the placement's origin, turned and scaled with it - one per trunk
## (a clump has two or three). Empty when this model isn't drawn as a new tree here (ZoneLoader then keeps the
## original's stand-in).
static func trunk_posts(model_file: String, x: Transform3D, zone_id := -1) -> PackedVector3Array:
	if not enabled or "--classic-trees" in OS.get_cmdline_user_args():
		return PackedVector3Array()
	var zones: Array = _load_manifest().get("zones", [])
	if not zones.is_empty() and not (float(zone_id) in zones or zone_id in zones):
		return PackedVector3Array()
	var sp := species_of(model_file)
	_mutex.lock()
	var s = _species.get(sp)
	_mutex.unlock()
	if s == null or s.is_empty():
		return PackedVector3Array()
	var trunks: Array = s.trunks
	var o := x.origin
	var mine: PackedVector3Array = trunks[posmod(hash(Vector2i(roundi(o.x * 4.0), roundi(o.z * 4.0))), trunks.size())]
	var b := x.basis.scaled(Vector3.ONE * GROW)
	var sc := b.get_scale().x
	var out := PackedVector3Array()
	for t in mine:
		var off := b * Vector3(t.x, 0.0, t.y)
		out.append(Vector3(off.x, off.z, t.z * sc * 0.9))     # (0.9: the ring is measured at the buried foot; the bark
	return out                                                 # tapers a little by the ground)


## Posts for the player's capsule round those trunks: eight sides each, from a little under the ground to 25 m up (as
## the original's stand-in, which has no top), the capsule's own radius taken off so its centre stops at the bark.
static func trunk_faces(posts: PackedVector3Array, base_y: float, at: Vector3, capsule_r: float) -> PackedVector3Array:
	var y0 := base_y - 2.4 - at.y
	var y1 := base_y + 25.6 - at.y
	var out := PackedVector3Array()
	for p in posts:
		var rr := maxf(p.z + 0.05 - capsule_r, 0.05)
		var c := Vector3(p.x, 0, p.y)
		for k in 8:
			var a0 := TAU * k / 8.0
			var a1 := TAU * (k + 1) / 8.0
			var p0 := c + Vector3(cos(a0) * rr, 0, sin(a0) * rr)
			var p1 := c + Vector3(cos(a1) * rr, 0, sin(a1) * rr)
			var q := [p0 + Vector3(0, y0, 0), p1 + Vector3(0, y0, 0), p1 + Vector3(0, y1, 0), p0 + Vector3(0, y1, 0)]
			for idx in [0, 1, 2, 0, 2, 3]:            # (wound as ZoneLoader.proxy_faces: front outside)
				out.append(q[idx])
	return out


## Where the trunks stand in a variant (at scale 1): the bark's lowest ring of vertices (EZ-Tree starts each trunk with
## one), split into trunks - Vector3(x, z, radius) each. (Not "every bark vertex near the ground": low boughs and a
## clump's spread made that a wall metres out.)
static func _trunks(mesh: ArrayMesh) -> PackedVector3Array:
	var verts: PackedVector3Array = mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var lo := INF
	for v in verts:
		lo = minf(lo, v.y)
	var ring := PackedVector2Array()
	for v in verts:
		if v.y < lo + 0.3:
			ring.append(Vector2(v.x, v.z))
	var gap := 0.6
	while true:                                  # (a wide trunk's ring points are further apart: widen till each is one)
		var groups := _cluster(ring, gap)
		var out := PackedVector3Array()
		var split := false
		for g: PackedVector2Array in groups:
			var c := Vector2.ZERO
			for p in g:
				c += p
			c /= g.size()
			var r := 0.0
			for p in g:
				r = maxf(r, p.distance_to(c))
			if g.size() < 4:
				split = true
			elif r > 0.05:                           # (a bough's tip resting on the ground: no post)
				out.append(Vector3(c.x, c.y, r))
		if (not split and not out.is_empty()) or gap > 2.0:
			if out.is_empty():
				out.append(Vector3(0, 0, 0.3))
			return out
		gap += 0.2
	return PackedVector3Array()


static func _cluster(pts: PackedVector2Array, gap: float) -> Array:
	var seen := PackedByteArray()
	seen.resize(pts.size())
	var out := []
	for i in pts.size():
		if seen[i]:
			continue
		seen[i] = 1
		var g := PackedVector2Array([pts[i]])
		var k := 0
		while k < g.size():
			for j in pts.size():
				if not seen[j] and pts[j].distance_to(g[k]) < gap:
					seen[j] = 1
					g.append(pts[j])
			k += 1
		out.append(g)
	return out


# ---------------------------------------------------------------- the hand-over, per tree, in time

static func _driver(parent: Node3D) -> Driver:
	if parent.has_meta("tree_driver"):
		return parent.get_meta("tree_driver")
	var d := Driver.new()
	d.name = "TreeSwapDriver"
	d.hyst = HYST
	d.late = LATE
	d.early = EARLY
	d.fade_s = FADE_S
	d.near = near_m
	d.reach = CELL_M * 0.75
	parent.set_meta("tree_driver", d)
	_drivers.append(weakref(d))
	parent.add_child(d)
	return d


## One per zone: every tree's place (the zone's own frame), its near and far instances, and how far it is into its
## change (0 the real tree, 1 the far card). Distances are looked at 7 times a second; a changing tree moves on each
## frame.
class Driver extends Node:
	var pos := PackedVector3Array()                 # each tree's crown middle (the zone's frame)
	var rad := PackedFloat32Array()                 # and a ball round it, for "is it on screen"
	var ratio := PackedFloat32Array()              # its species' hand-over, x the ordinary one (a tall tree's is further)
	var near := 75.0                                # the ordinary hand-over (TreeSwap.near_m)
	var reach := 24.0
	var near_nodes := []                            # [MultiMeshInstance3D, ratio]: their visibility ranges follow near
	var far_nodes := []
	var t := PackedFloat32Array()
	var want := PackedByteArray()
	var near_mm: Array[MultiMesh] = []
	var near_i := PackedInt32Array()
	var far_mm: Array[MultiMesh] = []
	var far_i := PackedInt32Array()
	var far_v := PackedInt32Array()
	var moving := {}                                 # tree -> true while it changes
	var hyst := 5.0
	var late := 30.0
	var early := 20.0
	var fade_s := 0.7
	var _look := 0.0
	var _first := true
	var changed_in_view := 0                        # (counts for the tests: tests/trees_probe.gd --trees-stroll)
	var changed_out_of_view := 0

	func add_trees(xforms: Array[Transform3D], r: float, height: float) -> int:
		var base := pos.size()
		for x in xforms:
			var h := height * x.basis.get_scale().y
			pos.append(x.origin + Vector3(0, h * 0.55, 0))
			rad.append(h * 0.6)
			ratio.append(r)
			t.append(1.0)
			want.append(1)
			near_mm.append(null)
			near_i.append(-1)
			far_mm.append(null)
			far_i.append(-1)
			far_v.append(0)
		_first = true                                # (new trees take their place at once, not by fading)
		return base

	func set_near(k: int, mm: MultiMesh, i: int) -> void:
		near_mm[k] = mm
		near_i[k] = i

	func set_far(k: int, mm: MultiMesh, i: int, v: int) -> void:
		far_mm[k] = mm
		far_i[k] = i
		far_v[k] = v

	## Which trees should be which. On screen a tree only changes when it must: to the real tree once it is nearer
	## than its hand-over less HYST, to the far card only when it is LATE metres past it. Off screen it changes freely
	## (the real tree within EARLY metres past the line), so turning round finds it already right - most changes happen
	## where you can't see them (owner 2026-11-17: trees phasing as you walk, whichever way).
	func _process(delta: float) -> void:
		var cam := get_viewport().get_camera_3d()
		var zone := get_parent() as Node3D
		if cam == null or zone == null:
			return
		_look -= delta
		if _look <= 0.0:
			_look = 0.12
			var to_zone := zone.global_transform.affine_inverse()
			var c3: Vector3 = to_zone * cam.global_position
			var c := Vector2(c3.x, c3.z)
			var planes: Array[Plane] = []
			for pl in cam.get_frustum():
				planes.append(to_zone * pl)
			for k in pos.size():
				var p := pos[k]
				var d := Vector2(p.x, p.z).distance_to(c)
				var n := ratio[k] * near
				var w: int = want[k]
				if _first:
					w = 1 if d > n else 0
					want[k] = w
					t[k] = float(w)
					_apply(k)
					continue
				var seen := true
				for pl in planes:
					if pl.distance_to(p) > rad[k]:
						seen = false
						break
				if not seen:
					w = 0 if d < n + early else 1
				elif d < n - hyst:
					w = 0
				elif d > n + late:
					w = 1
				if w != want[k]:
					want[k] = w
					moving[k] = true
					if seen:
						changed_in_view += 1
					else:
						changed_out_of_view += 1
			_first = false
		if moving.is_empty():
			return
		var step := delta / fade_s
		for k in moving.keys():
			var goal: float = float(want[k])
			t[k] = move_toward(t[k], goal, step)
			_apply(k)
			if t[k] == goal:
				moving.erase(k)

	func retune(m: float) -> void:
		near = m
		for e in near_nodes:
			if is_instance_valid(e[0]):
				(e[0] as GeometryInstance3D).visibility_range_end = m * float(e[1]) + LATE + reach
		for e in far_nodes:
			if is_instance_valid(e[0]):
				(e[0] as GeometryInstance3D).visibility_range_begin = maxf(m * float(e[1]) - HYST - FAR_REACH, 0.0)
		_look = 0.0

	func _apply(k: int) -> void:
		if near_mm[k]:
			near_mm[k].set_instance_custom_data(near_i[k], Color(0, t[k], 0, 0))
		if far_mm[k]:
			far_mm[k].set_instance_custom_data(far_i[k], Color(float(far_v[k]), t[k], 0, 0))
