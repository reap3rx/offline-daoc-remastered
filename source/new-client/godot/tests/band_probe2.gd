extends Node
## Debug (claude 2026-11-03): the monsters around you by name and level as the server sends them, with their con for
## your level - to find monsters the level bands missed (grey leftovers next to banded ones).
##   --auto-play=hib:Zenuashu --live-probe=band_probe2
func _ready() -> void:
	await get_tree().create_timer(30.0).timeout
	var v = get_tree().current_scene
	var sw = v.npcs
	print("[band2] you: L%d at %s" % [PlayerData.level, str(v.player.global_position)])
	var by := {}
	for st in sw.by_oid.values():
		if st == null or st.view == null:
			continue
		var sp: Dictionary = st.spawn
		if int(sp.get("realm", 0)) != 0:
			continue
		var dist: float = st.view.global_position.distance_to(v.player.global_position)
		if dist > 300.0:
			continue
		var k := "%s L%d" % [String(sp.get("name", "")), int(sp.get("level", 0))]
		by[k] = int(by.get(k, 0)) + 1
	var keys := by.keys()
	keys.sort()
	for k in keys:
		print("[band2] %s x%d" % [k, by[k]])
	get_tree().quit()
