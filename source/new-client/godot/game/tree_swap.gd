extends RefCounted
## (preloaded as TreeSwap by ZoneLoader and Graphics: a new class_name needs the editor to register it)
## The new trees (owner 2026-11-17: "I want to replace all of the trees, eventually, so none of the bad looking low
## poly ones exist" - EZ-Tree, a painterly look that still belongs in DAoC, the same kind of tree as the one it
## replaces, no two alike). content/trees/trees.json names the original tree models that have a replacement and the
## species each becomes; every species has a handful of variants (made by source/new-client/pipeline/trees: EZ-Tree in
## a headless browser, the original trees' own bark and leaf colours). ZoneLoader asks build() for each placed model:
## each tree becomes one of its species' variants, picked by where it stands (the same one every visit), at the
## original's place, turn and size. Collision, the bots' paths and the falling leaves keep the original's footprint.
##   Near (NEAR_M): the real tree, bark and leaves, swaying, casting shadows.
##   Beyond: a far card - two crossed pictures of that variant from the front and the side - out to the original's
##   own draw range (times Options > VIDEO view distance). The two cross-fade over FADE_M.
## Options > VIDEO > REMASTERED TREES (Graphics "remastered_trees") switches it; it takes effect as zones load.

const DIR := "res://content/trees"
const NEAR_M := 75.0
const FADE_M := 12.0
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


## Draw these placed trees as the new ones, under `parent` (the zone). False: no replacement for this model - the
## caller draws the original.
static func build(parent: Node3D, model_file: String, xforms: Array[Transform3D], cell_m: float, far: float, view_mult: float,
		zone_id := -1) -> bool:
	if not enabled or xforms.is_empty() or "--classic-trees" in OS.get_cmdline_user_args():
		return false
	var zones: Array = _load_manifest().get("zones", [])          # (the pilot: Lough Derg only, until it is signed off)
	if not zones.is_empty() and not (float(zone_id) in zones or zone_id in zones):
		return false
	var sp := species_of(model_file)
	if sp == "":
		return false
	_mutex.lock()
	var s = _species.get(sp)
	if s == null:
		s = _load_species(sp)
		_species[sp] = s
	_mutex.unlock()
	if s.is_empty():
		return false
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
		if not cells.has(c):
			cells[c] = []
		cells[c].append(i)
	# near: the real trees, one batch per variant per cell
	for k in groups:
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = s.near[k.z]
		mm.instance_count = groups[k].size()
		for j in groups[k].size():
			mm.set_instance_transform(j, xforms[groups[k][j]])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "Tree_%s_%d_%d_%d" % [sp, k.x, k.y, k.z]
		mmi.multimesh = mm
		mmi.visibility_range_end = NEAR_M
		mmi.visibility_range_end_margin = FADE_M
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
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
			mm.set_instance_custom_data(j, Color(float(v), 0, 0, 0))
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "TreeFar_%s_%d_%d" % [sp, c.x, c.y]
		mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.visibility_range_begin = NEAR_M
		mmi.visibility_range_begin_margin = FADE_M
		mmi.set_meta("base_far", far)
		mmi.visibility_range_end = far * view_mult
		mmi.visibility_range_end_margin = far * view_mult * 0.1
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		parent.add_child(mmi)
	return true


static func _texture(file: String, mipmaps := true) -> Texture2D:
	var img := Image.load_from_file(DIR + "/" + file)
	if img == null or img.is_empty():
		push_warning("trees: no texture %s" % file)
		return null
	if mipmaps:
		img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


static func _load_species(sp: String) -> Dictionary:
	var m: Dictionary = _load_manifest()
	var d: Dictionary = m.get("species", {}).get(sp, {})
	if d.is_empty():
		return {}
	var tint := Color(d.get("tint", "#ffffff"))
	var height := float(d.get("height", 25.0))
	var leaves := ShaderMaterial.new()
	leaves.shader = LEAVES_SHADER
	leaves.set_shader_parameter("albedo_tex", _texture(String(d.leaf)))
	leaves.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
	leaves.set_shader_parameter("height", height)
	var bark := ShaderMaterial.new()
	bark.shader = BARK_SHADER
	bark.set_shader_parameter("albedo_tex", _texture(String(d.bark)))
	bark.set_shader_parameter("height", height)
	bark.set_shader_parameter("uv_scale", Vector2(d.get("bark_uv", [1.0, 1.0])[0], d.get("bark_uv", [1.0, 1.0])[1]))
	var near: Array[ArrayMesh] = []
	for file in d.get("variants", []):
		var mesh := _load_glb(DIR + "/" + String(file), bark, leaves)
		if mesh:
			near.append(mesh)
	if near.is_empty():
		return {}
	var far := ShaderMaterial.new()
	far.shader = FAR_SHADER
	far.set_shader_parameter("atlas", _texture(String(d.far.atlas)))
	far.set_shader_parameter("count", float(near.size()))
	var quad := _far_quad_mesh().duplicate() as ArrayMesh
	quad.surface_set_material(0, far)
	return {"near": near, "far_mesh": quad, "far_cards": d.far.cards}


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


## Two crossed unit cards standing on the ground (x and z from -0.5 to 0.5, y from 0 to 1): the first faces z (the
## front picture), the second faces x (the side picture; UV2.x = 1 picks it).
static func _far_quad_mesh() -> ArrayMesh:
	if _far_quad:
		return _far_quad
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for k in 2:
		var corners: Array[Vector3] = []
		var uvs: Array[Vector2] = []
		for c in [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]:
			var p := Vector3(c.x - 0.5, c.y, 0.0) if k == 0 else Vector3(0.0, c.y, 0.5 - c.x)
			corners.append(p)
			uvs.append(Vector2(c.x, 1.0 - c.y))
		var nrm := Vector3(0, 0, 1) if k == 0 else Vector3(1, 0, 0)
		for idx in [0, 1, 2, 0, 2, 3]:
			st.set_normal(nrm)
			st.set_uv(uvs[idx])
			st.set_uv2(Vector2(float(k), 0))
			st.add_vertex(corners[idx])
	_far_quad = st.commit()
	return _far_quad
