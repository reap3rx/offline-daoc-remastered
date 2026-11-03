extends Node
## Debug (claude 2026-11-02): the modern HUD (Options > INTERFACE > STYLE) - the orb with a target and a party, the
## minimap, the quest log; the map zoomed; then back to classic. Client side only.
##   --auto-play=hib:Mongfar --live-probe=ui_probe
var v: Node


func _shot(tag: String) -> void:
	for i in 8:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("E:/Offline DAOC 036c/claude-work/walk/ui_%s.png" % tag)


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _ready() -> void:
	get_tree().create_timer(120.0).timeout.connect(func(): print("[ui] timed out"); get_tree().quit())
	await _wait(25.0)
	v = get_tree().current_scene
	v.player.cam_distance = 4.0
	v.ui.map_window.visible = false
	v.ui.set_style("modern", false)
	PlayerData.target = {"name": "Sentinel Glynis", "con_color": Color(1.0, 0.9, 0.2), "health": 0.72}
	PlayerData.target_changed.emit()
	PlayerData.group = [{"name": "Caoimhe", "class_name": "Druid", "level": 14, "hp": 0.82, "power": 0.55, "end": 1.0, "effects": []},
			{"name": "Fergal", "class_name": "Hero", "level": 15, "hp": 0.4, "power": 0.1, "end": 0.7, "effects": []}]
	PlayerData.group_changed.emit()
	await _wait(1.5)
	PlayerData.health = 0.62
	PlayerData.endurance = 0.8
	PlayerData.power = 0.45
	PlayerData.exp_frac = 0.37
	print("[ui] modern: %s windows hidden: %s" % [str(v.ui.modern != null), str(["status", "target", "minigroup", "time"].map(func(id): return not v.ui.windows[id].visible))])
	await _shot("modern")
	v.ui.map_window.player = v.player
	v.ui.map_window.show_window()
	await _wait(0.5)
	var view = v.ui.map_window._view
	view.zoom = 3.0
	v.ui.map_window.follow = true
	await _wait(0.5)
	print("[ui] map zoom %.1f pan %s" % [view.zoom, str(view.pan)])
	await _shot("map")
	v.ui.map_window.hide_window()
	v.ui.set_style("classic", false)
	await _wait(1.0)
	print("[ui] classic: %s windows shown: %s" % [str(v.ui.modern == null), str(["status", "target", "minigroup", "time"].map(func(id): return v.ui.windows[id].visible))])
	await _shot("classic")
	get_tree().quit()
