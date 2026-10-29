extends SceneTree
## Builds the model and texture caches of the given zones ahead of play (owner 2026-10-28: a first visit to a zone
## spent 15-25 s compressing its textures). Headless: godot --headless --path new-client/godot -s
## res://game/tools/prebuild_caches.gd -- --zones=0,1,2  (tools/sync/prebuild_caches.ps1 runs it for every zone).
func _initialize() -> void:
	var ids: Array = []
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--zones="):
			ids = Array(a.trim_prefix("--zones=").split(",", false)).map(func(x): return int(x))
	for id in ids:
		var dir := "res://content/zones/zone%03d" % id
		if not FileAccess.file_exists(dir.path_join("zone.json")):
			continue
		var z := ZoneLoader.new()
		z.load_zone(dir, "blend", "x4plus")
		z.free()
	print("prebuild done")
	quit()
