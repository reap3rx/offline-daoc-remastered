extends RefCounted
## Player housing outdoors (owner 2026-11-02: "take a first pass at putting Foundations in the game"): the houses the
## server places (HouseCreate 0xD1 - house model 1-12: Albion / Midgard / Hibernia cottage, house, villa, mansion)
## and the lot markers on empty lots (GameLotMarker, objects 1306-1308). Models: pipeline/build_housing.py ->
## content/housing (housing.json; models/*.gltf with the zones' layered materials, textures/original).
## A house is drawn like a zone fixture the client marks Collide: its collidee geometry is a wall, its visible faces a
## floor (porch steps); a house whose NIF has (almost) no collidee geometry is walled by its visible faces instead.

const DIR := "res://content/housing"
const LAYER_WALL := 1
const LAYER_FLOOR := 2
const MIN_COLLISION_TRIANGLES := 50

static var _info := {}
static var _materials: NifMaterials = null
static var _parts := {}                   # gltf path -> {meshes: [[ArrayMesh, Transform3D]], walls, floors}


static func info() -> Dictionary:
	if _info.is_empty():
		var p := DIR + "/housing.json"
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(p)) if FileAccess.file_exists(p) else null
		_info = parsed if parsed is Dictionary else {"houses": {}, "objects": {}}
	return _info


## Is this server object a housing one we draw (a lot marker)?
static func has_object(model: int) -> bool:
	return (info().get("objects", {}) as Dictionary).has(str(model))


static func is_lot_marker(model: int) -> bool:
	return model in [1306, 1307, 1308]


## The house model's name (ph_houses.csv: "Albion Tier 1" ...), "" when unknown.
static func house_name(model: int) -> String:
	return String((info().get("houses", {}) as Dictionary).get(str(model), {}).get("name", ""))


## A house of this model, standing at its origin facing as the server's heading turns it - with its collision.
static func make_house(model: int) -> Node3D:
	var h: Dictionary = (info().get("houses", {}) as Dictionary).get(str(model), {})
	return _make(String(h.get("file", "")), true) if not h.is_empty() else null


## A housing object (lot marker) - no walls, only a floor so it can be clicked.
static func make_object(model: int) -> Node3D:
	var o: Dictionary = (info().get("objects", {}) as Dictionary).get(str(model), {})
	return _make(String(o.get("file", "")), false) if not o.is_empty() else null


static func _make(file: String, walls: bool) -> Node3D:
	if file == "":
		return null
	var parts := _load(DIR.path_join(file))
	if parts.is_empty():
		return null
	var root := Node3D.new()
	for p in parts.meshes:
		var mi := MeshInstance3D.new()
		mi.mesh = p[0]
		mi.transform = p[1]
		root.add_child(mi)
	if walls:
		var wall := StaticBody3D.new()
		wall.name = "HouseWalls"
		wall.collision_layer = LAYER_WALL
		wall.collision_mask = 0
		var ws := CollisionShape3D.new()
		ws.shape = parts.walls
		wall.add_child(ws)
		root.add_child(wall)
		var floor_body := StaticBody3D.new()
		floor_body.name = "HouseFloors"
		floor_body.collision_layer = LAYER_FLOOR
		floor_body.collision_mask = 0
		var fs := CollisionShape3D.new()
		fs.shape = parts.floors
		floor_body.add_child(fs)
		root.add_child(floor_body)
	return root


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
	var meshes := []
	var collision := PackedVector3Array()
	var seen := PackedVector3Array()
	for nd in data.nodes:
		var nm := String(nd.name)
		if nm.begins_with("collision_"):
			collision.append_array(nd.faces)
			continue
		if nm.begins_with("climb_") or nm.begins_with("doorcol"):
			continue                                   # (the doors stay shut and walk-through for now: no interiors yet)
		var mesh := ArrayMesh.new()
		mesh.resource_name = nm
		for sf in nd.surfaces:
			mesh.add_surface_from_arrays(int(sf[3]), sf[0], [], {}, int(sf[1]))
			var si := int(sf[2])
			if si >= 0 and si < specs.size():
				mesh.surface_set_material(mesh.get_surface_count() - 1, _materials.material(specs[si]))
		meshes.append([mesh, nd.xform as Transform3D])
		if not nm.begins_with("door"):
			seen.append_array(nd.faces)
	var walls := ConcavePolygonShape3D.new()
	walls.set_faces(collision if collision.size() >= MIN_COLLISION_TRIANGLES * 3 else seen)
	var floors := ConcavePolygonShape3D.new()
	floors.backface_collision = true
	floors.set_faces(seen)
	var out := {"meshes": meshes, "walls": walls, "floors": floors}
	_parts[path] = out
	return out
