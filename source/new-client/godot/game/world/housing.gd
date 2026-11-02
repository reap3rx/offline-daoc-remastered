extends RefCounted
## Player housing (owner 2026-11-02: "take a first pass at putting Foundations in the game", then "interiors,
## purchasing, and decorating"): the houses the server places (HouseCreate 0xD1 - model 1-12: Albion / Midgard /
## Hibernia cottage, house, villa, mansion; 13-14 the tier 5s), their interiors (HouseEnter 0x08), the lot markers on
## empty lots (GameLotMarker, objects 1306-1308) and the furniture / garden / hookpoint pieces (HousingItem 0x09,
## HouseChangeGarden 0xD2). Models: pipeline/build_housing.py -> content/housing (housing.json; models/*.gltf with the
## zones' layered materials, textures/original).
##
## A house is drawn like a zone fixture the client marks Collide: its collidee geometry is a wall, its visible faces a
## floor (porch steps); a NIF with (almost) no collidee geometry is walled by its visible faces instead. Its looks are
## the HouseCreate's choices: the NIF's roofN / wallN pieces (RoofMaterial / WallMaterial), its doorNN leaves
## (DoorMaterial), the porch and its awning (porch flag, PorchRoofColor), the guild banner / shield pieces, the wood
## (supports: the ph_woodxx placeholder -> ph_wood01..10). An interior stands where the server keeps it - the house's
## spot, 25000 units up, never turned (HouseEnter: the heading "is ignored by the client"; HouseHookpointOffset and the
## entry spots are unturned offsets) - with its door style, carpets (Rug1..4Color) and guild pieces; its placement
## planes (floorplaneN / wallplaneN: not drawn) are what furniture is put on.

const DIR := "res://content/housing"
const LAYER_WALL := 1
const LAYER_FLOOR := 2
const OBJECT_PICK := 1 << 11                  # (ServerWorld.OBJECT_PICK: clicks on the server's things)
const PLACE_PICK := 1 << 12                   # an interior's placement planes (decorating)
const MIN_COLLISION_TRIANGLES := 50
const INTERIOR_Z := 25000                     # DAoC units: where interiors hang (House.Enter / SendEnterHouse)

static var _info := {}
static var _materials: NifMaterials = null
static var _parts := {}                       # gltf path -> parsed parts (see _load)


static func info() -> Dictionary:
	if _info.is_empty():
		var p := DIR + "/housing.json"
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(p)) if FileAccess.file_exists(p) else null
		_info = parsed if parsed is Dictionary else {"houses": {}, "interiors": {}, "objects": {}}
	return _info


## Is this server object one of housing's models (a lot marker, a vault, a hookpoint piece)?
static func has_object(model: int) -> bool:
	return (info().get("objects", {}) as Dictionary).has(str(model))


static func is_lot_marker(model: int) -> bool:
	return model in [1306, 1307, 1308]


## The house model's name (ph_houses.csv: "Albion Tier 1" ...), "" when unknown.
static func house_name(model: int) -> String:
	return String((info().get("houses", {}) as Dictionary).get(str(model), {}).get("name", ""))


## The garden's points of a house model: {point number: Vector3 in the house's frame}.
static func garden_points(model: int) -> Dictionary:
	var g: Dictionary = (info().get("houses", {}) as Dictionary).get(str(model), {}).get("garden", {})
	var out := {}
	for k in g:
		var p: Array = g[k]
		out[int(k)] = Vector3(p[0], p[1], p[2])
	return out


## An interior's hookpoints: {id: [Vector3 in the interior's frame, heading]}.
static func hookpoints(model: int) -> Dictionary:
	var h: Dictionary = (info().get("interiors", {}) as Dictionary).get(str(model), {}).get("hookpoints", {})
	var out := {}
	for k in h:
		var p: Array = h[k]
		out[int(k)] = [Vector3(p[0], p[1], p[2]), int(p[3])]
	return out


## The scene yaw of a house's heading - degrees (DBHouse.Heading: House.OutdoorJumpPoint turns by it in degrees; its
## door faces north at 0, east at 90).
static func house_yaw(heading_degrees: int) -> float:
	return -deg_to_rad(float(heading_degrees))


# ---------------------------------------------------------------- building

const HouseLight := preload("res://game/world/house_light.gd")
## The housing models' light sources, by texture (content/housing: the interiors' wall sconces are fireshell3, the
## Albion / Hibernian lamps lampglow and cndlflame, Midgard's hearths coals_hd / coalstones_hd; the furniture's torches,
## candle tables, tiki torch and forge the same) -> kind: [colour, range m, energy, flicker]. Indoors there is no sun:
## these are what light a room.
const LIGHT_TEXTURES := {
	"fireshell3": "torch", "tiki_flame": "torch", "cndlflame": "candle", "lampglow": "lantern", "lanterntex1": "lantern",
	"coals_hd": "fire", "coalstones_hd": "fire", "coals": "fire", "midcoals": "fire", "coalstones": "fire", "a_coals": "fire",
}
const LIGHT_KINDS := {
	"torch": [Color(1.0, 0.64, 0.32), 10.0, 2.6, 0.12],
	"candle": [Color(1.0, 0.76, 0.48), 4.0, 1.0, 0.1],
	"lantern": [Color(1.0, 0.72, 0.42), 6.5, 1.6, 0.05],
	"fire": [Color(1.0, 0.55, 0.25), 11.0, 3.2, 0.3],
}
const LIGHT_MERGE_M := 0.9                # a sconce's flame and its glow halo: one light


## A house of this model with its looks (the HouseCreate dictionary), collision and click bodies (meta "house_part":
## "door" / "body"). Set the root's meta "house_number" after.
static func make_house(model: int, look: Dictionary) -> Node3D:
	var h: Dictionary = (info().get("houses", {}) as Dictionary).get(str(model), {})
	if h.is_empty():
		return null
	var root := _make(String(h.file), true, "door")
	if root:
		apply_look(root, look)
	return root


## The inside of a house of this model (HouseEnter's dictionary: door style, carpets, guild pieces): walls, floors, the
## way out (meta house_part "exit") and its placement planes (PLACE_PICK, meta "plane" = "floorpN" / "wallpN").
static func make_interior(model: int, look: Dictionary) -> Node3D:
	var it: Dictionary = (info().get("interiors", {}) as Dictionary).get(str(model), {})
	if it.is_empty():
		return null
	var root := _make(String(it.file), true, "exit")
	if root == null:
		return null
	var parts := _load(DIR.path_join(String(it.file)))
	for k in parts.planes:
		var body := StaticBody3D.new()
		body.collision_layer = PLACE_PICK
		body.collision_mask = 0
		body.set_meta("plane", String(k))
		var cs := CollisionShape3D.new()
		var sh := ConcavePolygonShape3D.new()
		sh.backface_collision = true
		sh.set_faces(parts.planes[k])
		cs.shape = sh
		body.add_child(cs)
		root.add_child(body)
	root.set_meta("planes", parts.planes)
	apply_interior_look(root, look)
	return root


## A housing object (lot marker, furniture, garden piece, hookpoint object): its meshes, no collision.
static func make_object(model: int) -> Node3D:
	var o: Dictionary = (info().get("objects", {}) as Dictionary).get(str(model), {})
	return _make(String(o.get("file", "")), false, "") if not o.is_empty() else null


## The house's outside looks: roof / wall / door styles, porch and awning, guild banner and shield, wood.
static func apply_look(root: Node3D, look: Dictionary) -> void:
	var porch := (int(look.get("porch_flags", 0)) & 1) != 0
	var want := {"roof": int(look.get("roof", 0)), "wall": int(look.get("wall", 0)), "door": int(look.get("door", 0))}
	for mi in _meshes(root):
		var t := String(mi.get_meta("tag", ""))
		var v := true
		var m := RegEx.create_from_string("^(roof|wall|door)(\\d+)$").search(t)
		if m and _has_variant(root, m.get_string(1), want[m.get_string(1)]):
			v = int(m.get_string(2)) == int(want[m.get_string(1)])
		elif t == "porch" or t == "tent":
			v = porch
		elif t == "banners":
			v = (int(look.get("porch_flags", 0)) & 2) != 0
		elif t == "shields":
			v = (int(look.get("porch_flags", 0)) & 4) != 0
		mi.visible = v
		if t == "tent" and v:
			_tint(mi, int(look.get("porch_roof_color", 0)))
	_wood(root, int(look.get("truss", 0)))
	_sync_lights(root)


## The interior's looks: the front door's style, the carpets (Rug1..4Color: 0 none), the indoor banner / shield.
static func apply_interior_look(root: Node3D, look: Dictionary) -> void:
	var door := int(look.get("door", 0))
	for mi in _meshes(root):
		var t := String(mi.get_meta("tag", ""))
		var v := true
		if t.begins_with("door") and _has_variant(root, "door", door):
			v = int(t.substr(4)) == door
		elif t.begins_with("carpet"):
			var c := int(look.get("rug%d" % clampi(int(t.substr(6)), 1, 4), 0))
			v = c > 0
			if v:
				_tint(mi, c)
		elif t == "banners":
			v = (int(look.get("emblem_flags", 0)) & 1) != 0
		elif t == "shields":
			v = (int(look.get("emblem_flags", 0)) & 2) != 0
		mi.visible = v
	_sync_lights(root)


## A lamp that belongs to a style's piece (a tagged mesh) burns only while that piece shows.
static func _sync_lights(root: Node3D) -> void:
	var shown := {}
	for mi in _meshes(root):
		var t := String(mi.get_meta("tag", ""))
		if t != "" and mi.visible:
			shown[t] = true
	for o in root.find_children("HouseLight*", "OmniLight3D", false, false):
		var t := String(o.get_meta("tag", ""))
		o.visible = t == "" or shown.has(t)


static func _meshes(root: Node3D) -> Array:
	return root.find_children("*", "MeshInstance3D", true, false)


static func _has_variant(root: Node3D, kind: String, n: int) -> bool:
	if not root.has_meta("tags"):
		var tags := {}
		for mi in _meshes(root):
			tags[String(mi.get_meta("tag", ""))] = true
		root.set_meta("tags", tags)
	return (root.get_meta("tags") as Dictionary).has("%s%d" % [kind, n])


## A part tinted with a tints.csv colour (carpets, the awning) - this copy's materials only.
static func _tint(mi: MeshInstance3D, color: int) -> void:
	var c := Fig3Figure.dye(color) if color > 0 else Color.WHITE
	for i in mi.mesh.get_surface_count():
		var m := mi.mesh.surface_get_material(i)
		if m is ShaderMaterial:
			var d := (m as ShaderMaterial).duplicate() as ShaderMaterial
			d.set_shader_parameter("tint", c)
			mi.set_surface_override_material(i, d)


## The house's supports in the wood chosen (TrussMaterial 0-9: ph_wood01..10_hd for the NIF's ph_woodxx placeholder).
static func _wood(root: Node3D, truss: int) -> void:
	var woods: Array = info().get("woods", [])
	if woods.is_empty():
		return
	var tex := String(woods[clampi(truss, 0, woods.size() - 1)])
	for mi in _meshes(root):
		var specs: Array = mi.get_meta("specs", [])
		for i in specs.size():
			var sp = specs[i]
			if not (sp is Dictionary) or not JSON.stringify(sp).contains("ph_woodxx"):
				continue
			var s2: Dictionary = JSON.parse_string(JSON.stringify(sp).replace("ph_woodxx_hd", tex))
			mi.set_surface_override_material(i, _materials.material(s2))


static func _make(file: String, walls: bool, door_part: String) -> Node3D:
	if file == "":
		return null
	var parts := _load(DIR.path_join(file))
	if parts.is_empty():
		return null
	var root := Node3D.new()
	for p in parts.meshes:
		var mi := MeshInstance3D.new()
		mi.mesh = p.mesh
		mi.transform = p.xform
		mi.set_meta("tag", p.tag)
		mi.set_meta("specs", p.specs)
		root.add_child(mi)
	add_lights(root, parts.get("lights", []))
	if walls:
		root.add_child(_body("HouseWalls", LAYER_WALL, parts.walls))
		root.add_child(_body("HouseFloors", LAYER_FLOOR, parts.floors))
		var pick := _body("HouseBody", OBJECT_PICK, parts.floors)
		pick.set_meta("house_part", "body")
		root.add_child(pick)
		if parts.door_shape:
			var dp := _body("HouseDoor", OBJECT_PICK, parts.door_shape)
			dp.set_meta("house_part", door_part)
			root.add_child(dp)
	return root


static func _body(nm: String, layer: int, shape: Shape3D) -> StaticBody3D:
	var b := StaticBody3D.new()
	b.name = nm
	b.collision_layer = layer
	b.collision_mask = 0
	var cs := CollisionShape3D.new()
	cs.shape = shape
	b.add_child(cs)
	return b


## The model read once: {meshes: [{mesh, xform, tag, specs}], walls, floors, door_shape, planes: {tag: faces}}.
static func _load(path: String) -> Dictionary:
	if _parts.has(path):
		return _parts[path]
	if _materials == null:
		NifMaterials.ensure_globals()
		_materials = NifMaterials.new({"original": DIR + "/textures/original"}, "original")
		_materials.world = true
	var data := ZoneLoader.model_data(path)
	if data.is_empty():
		push_warning("could not load " + path)
		_parts[path] = {}
		return {}
	var specs: Array = data.specs
	var door_specs := {}
	for ds in data.get("door_specs", []):
		door_specs[int(ds.id)] = ds
	var digits := RegEx.create_from_string("(\\d+)\\s*$")
	var meshes := []
	var collision := PackedVector3Array()
	var seen := PackedVector3Array()
	var door_faces := PackedVector3Array()
	var planes := {}
	var lights := []                              # [{at, kind, tag}] (model space)
	for nd in data.nodes:
		var nm := String(nd.name)
		var xf: Transform3D = nd.xform
		var tag := ""
		if nm.begins_with("collision_"):
			collision.append_array(nd.faces)
			continue
		if nm.begins_with("climb_") or nm.begins_with("doorcol"):
			continue                                   # (doors are clicked, not walked through or into)
		if nm.begins_with("grp_"):
			tag = nm.substr(4).get_slice("__", 0)
			if tag.begins_with("floorp") or tag.begins_with("wallp"):
				var pf: PackedVector3Array = planes.get(tag, PackedVector3Array())
				pf.append_array(nd.faces)                 # (a packed array is a value: put back)
				planes[tag] = pf
				continue
		var door := nm.begins_with("door")
		if door:
			var ds: Dictionary = door_specs.get(int(nm.trim_prefix("door").get_slice("_", 0)), {})
			if not ds.is_empty():
				var c: Array = ds.closed
				xf = Transform3D(Basis(Vector3(c[0], c[1], c[2]), Vector3(c[3], c[4], c[5]), Vector3(c[6], c[7], c[8])),
						Vector3(c[9], c[10], c[11]))
				var m := digits.search(String(ds.get("group", ds.get("name", ""))))
				if m:
					tag = "door%d" % int(m.get_string(1))
			for f in nd.faces:
				door_faces.append(xf * (f as Vector3))
		if tag.begins_with("door") and not door:
			door_faces.append_array(nd.faces)          # a door style (tagged): the doorway to click
		var mesh := ArrayMesh.new()
		mesh.resource_name = nm
		var sspecs := []
		for sf in nd.surfaces:
			mesh.add_surface_from_arrays(int(sf[3]), sf[0], [], {}, int(sf[1]))
			var si := int(sf[2])
			if si >= 0 and si < specs.size():
				mesh.surface_set_material(mesh.get_surface_count() - 1, _materials.material(specs[si]))
				sspecs.append(specs[si])
			else:
				sspecs.append(null)
		meshes.append({"mesh": mesh, "xform": xf, "tag": tag, "specs": sspecs})
		for sf in nd.surfaces:
			var li := int(sf[2])
			var tex := String((specs[li] as Dictionary).get("slots", {}).get("base", {}).get("tex", "")).to_lower() \
					if li >= 0 and li < specs.size() and specs[li] is Dictionary else ""
			if LIGHT_TEXTURES.has(tex):
				_light_spots(lights, (sf[0] as Array)[Mesh.ARRAY_VERTEX], xf, String(LIGHT_TEXTURES[tex]), tag)
		if not door and not tag.begins_with("carpet") and not tag.begins_with("door"):
			seen.append_array(nd.faces)
	var walls := ConcavePolygonShape3D.new()
	walls.set_faces(collision if collision.size() >= MIN_COLLISION_TRIANGLES * 3 else seen)
	var floors := ConcavePolygonShape3D.new()
	floors.backface_collision = true
	floors.set_faces(seen)
	var door_shape: ConcavePolygonShape3D = null
	if not door_faces.is_empty():
		door_shape = ConcavePolygonShape3D.new()
		door_shape.backface_collision = true
		door_shape.set_faces(door_faces)
	var out := {"meshes": meshes, "walls": walls, "floors": floors, "door_shape": door_shape, "planes": planes,
			"lights": lights}
	_parts[path] = out
	return out


# ---------------------------------------------------------------- placement planes

## The height (the interior's frame) of a floor plane under (x, z), or NAN when the plane isn't under it.
static func plane_height(faces: PackedVector3Array, x: float, z: float) -> float:
	var best := NAN
	for i in range(0, faces.size() - 2, 3):
		var a := faces[i]
		var b := faces[i + 1]
		var c := faces[i + 2]
		var d := (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z)
		if absf(d) < 1e-9:
			continue
		var l1 := ((b.z - c.z) * (x - c.x) + (c.x - b.x) * (z - c.z)) / d
		var l2 := ((c.z - a.z) * (x - c.x) + (a.x - c.x) * (z - c.z)) / d
		var l3 := 1.0 - l1 - l2
		if l1 >= -0.01 and l2 >= -0.01 and l3 >= -0.01:
			var y := l1 * a.y + l2 * b.y + l3 * c.y
			best = y if is_nan(best) else maxf(best, y)
	return best


## A wall plane's frame: {origin, u (along it, level), up, normal} - a wall item's X / Y are DAoC units along u and up
## from origin (the plane's lowest, leftmost corner as seen from the side its normal points to).
static func wall_frame(faces: PackedVector3Array) -> Dictionary:
	if faces.size() < 3:
		return {}
	var n := (faces[1] - faces[0]).cross(faces[2] - faces[0]).normalized()
	n.y = 0.0
	if n.length() < 0.01:
		return {}
	n = n.normalized()
	var u := Vector3.UP.cross(n).normalized()
	var umin := INF
	var ymin := INF
	for f in faces:
		umin = minf(umin, (f as Vector3).dot(u))
		ymin = minf(ymin, (f as Vector3).y)
	var o: Vector3 = faces[0]
	var origin := u * umin + Vector3.UP * ymin + n * o.dot(n)
	return {"origin": origin, "u": u, "up": Vector3.UP, "normal": n}


# ---------------------------------------------------------------- lights

## The clumps of one surface's vertices (model space) as light spots: a flame's light just above its top, a lantern's
## in its middle, a hearth's a little above its coals. Spots within LIGHT_MERGE_M of one already found are the same
## lamp (a sconce's flame and its glow) - the brighter kind wins.
static func _light_spots(spots: Array, verts: PackedVector3Array, xf: Transform3D, kind: String, tag: String) -> void:
	var clumps: Array = []                                   # [aabb]
	for v in verts:
		var p := xf * v
		var hit := false
		for i in clumps.size():
			var box: AABB = clumps[i]
			if box.grow(0.5).has_point(p):
				clumps[i] = box.expand(p)
				hit = true
				break
		if not hit:
			clumps.append(AABB(p, Vector3.ZERO))
	var order := ["candle", "lantern", "torch", "fire"]
	for box in clumps:
		var b: AABB = box
		var c := b.get_center()
		var at := c
		match kind:
			"torch", "candle":
				at = Vector3(c.x, b.end.y + 0.08, c.z)
			"fire":
				at = Vector3(c.x, b.end.y + 0.3, c.z)
		var merged := false
		for sp in spots:
			if (sp.at as Vector3).distance_to(at) < LIGHT_MERGE_M:
				if order.find(kind) > order.find(String(sp.kind)):
					sp.kind = kind
					sp.at = at
				merged = true
				break
		if not merged:
			spots.append({"at": at, "kind": kind, "tag": tag})


## The model's lamps as lights under root (a style's own lamp - a tagged piece - shows only with its piece:
## apply_look hides the light with the mesh, as the light hangs under it).
static func add_lights(root: Node3D, spots: Array) -> void:
	var i := 0
	for sp in spots:
		var k: Array = LIGHT_KINDS.get(String(sp.kind), LIGHT_KINDS.torch)
		var o: OmniLight3D = HouseLight.new()
		o.name = "HouseLight%d" % i
		i += 1
		o.position = sp.at
		o.light_color = k[0]
		o.omni_range = float(k[1])
		o.omni_attenuation = 1.2
		o.light_energy = float(k[2])
		o.shadow_enabled = false
		o.distance_fade_enabled = true
		o.distance_fade_begin = 50.0
		o.distance_fade_length = 20.0
		o.set("base", float(k[2]))
		o.set("flicker", float(k[3]))
		o.set("flick_seed", randf() * 100.0)
		o.set_meta("tag", String(sp.get("tag", "")))
		root.add_child(o)
