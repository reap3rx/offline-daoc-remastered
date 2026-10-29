# (no class_name: preloaded where used - new scripts are not in the class cache)
extends RefCounted
## Lights you place yourself (owner 2026-10-28: "in areas that have no model, is there a way we can look into adding
## something there? I can manually make a list of locations"): /light add candle | lantern | torch | fire puts one
## where the cursor (the crosshair in action combat) points; /light remove takes the nearest one there away, /light
## undo the last one, /light list counts this zone's. Kept per zone in user://world/placed_lights.json (zone-local
## metres) - the save sync carries the world folder to your other computers. Drawn with remastered lighting, like
## the lamps found on the models (ZoneLoader).

const PATH := "user://world/placed_lights.json"
const KINDS := ["candle", "lantern", "torch", "fire", "magic_red", "magic_blue", "magic_yellow", "magic_green"]
const MAGIC := ["red", "blue", "yellow", "green"]
static var _data := {}                     # zone id (String) -> [{"p": [x, y, z], "k": kind}]
static var _loaded := false
static var _lock := Mutex.new()
static var _last := []                     # [zone id, entry] of the last one placed this session (undo)


static func for_zone(id: int) -> Array:
	_lock.lock()
	_load()
	var out := (_data.get(str(id), []) as Array).duplicate(true)
	_lock.unlock()
	return out


static func add(id: int, at: Vector3, kind: String) -> Dictionary:
	var e := {"p": [snappedf(at.x, 0.01), snappedf(at.y, 0.01), snappedf(at.z, 0.01)], "k": kind}
	_lock.lock()
	_load()
	if not _data.has(str(id)):
		_data[str(id)] = []
	(_data[str(id)] as Array).append(e)
	_last = [id, e]
	_save()
	_lock.unlock()
	return e


## The placed light nearest `at` within `radius` m taken away; {} when none.
static func remove_near(id: int, at: Vector3, radius: float) -> Dictionary:
	_lock.lock()
	_load()
	var list: Array = _data.get(str(id), [])
	var best := -1
	var best_d := radius
	for i in list.size():
		var d := pos(list[i]).distance_to(at)
		if d <= best_d:
			best_d = d
			best = i
	var out := {}
	if best >= 0:
		out = list[best]
		list.remove_at(best)
		_save()
	_lock.unlock()
	return out


## The last one placed this session taken away: [zone id, entry], or [] when there is none.
static func undo() -> Array:
	_lock.lock()
	var out := []
	if not _last.is_empty():
		var list: Array = _data.get(str(_last[0]), [])
		var i := list.find(_last[1])
		if i >= 0:
			list.remove_at(i)
			_save()
			out = _last
		_last = []
	_lock.unlock()
	return out


static func pos(e: Dictionary) -> Vector3:
	var p: Array = e.get("p", [0, 0, 0])
	return Vector3(float(p[0]), float(p[1]), float(p[2]))


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	if FileAccess.file_exists(PATH):
		var d = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if d is Dictionary:
			_data = d


static func _save() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PATH.get_base_dir()))
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_data, "\t"))
