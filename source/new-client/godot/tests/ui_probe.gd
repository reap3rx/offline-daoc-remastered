extends Node
## Debug (claude 2026-11-02): the modern interface (Options > INTERFACE > STYLE) - the HUD with a target and a party,
## the menu bar opening the character sheet, the modern bags, the big map with its log; then back to classic.
## Client side only.
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
	get_tree().create_timer(150.0).timeout.connect(func(): print("[ui] timed out"); get_tree().quit())
	await _wait(25.0)
	v = get_tree().current_scene
	var ui = v.ui
	v.player.cam_distance = 4.0
	ui.map_window.visible = false
	ui.set_style("modern", false)
	PlayerData.target = {"name": "Sentinel Glynis", "con_color": Color(1.0, 0.9, 0.2), "health": 0.72}
	PlayerData.target_changed.emit()
	PlayerData.group = [{"name": "Caoimhe", "class_name": "Druid", "level": 14, "hp": 0.82, "power": 0.55, "end": 1.0, "effects": []},
			{"name": "Fergal", "class_name": "Hero", "level": 15, "hp": 0.4, "power": 0.1, "end": 0.7, "effects": []}]
	PlayerData.group_changed.emit()
	await _wait(1.5)
	print("[ui] modern: %s panel shown: %s strip shown: %s" % [str(ui.modern != null), str(ui.right_panel.visible), str(ui._strip.visible)])
	await _shot("modern")
	ui.modern.menu.open("character")
	await _wait(0.5)
	print("[ui] sheet: panel %s at %s tab %s" % [str(ui.right_panel.visible), str(ui.right_panel.position), ui.sheet_tab])
	await _shot("sheet")
	ui.modern.menu.open("character")
	ui.modern.menu.open("bags")
	await _wait(0.8)
	var order: Array = ui.bags.sorted_slots()
	var names: Array = []
	for s in order:
		var it := PlayerData.item_at(int(s))
		if not it.is_empty():
			names.append("%s[%d L%d]" % [String(it.get("name", "")), int(it.get("object_type", 0)), int(it.get("level", 0))])
	print("[ui] bags: %d places, sorted: %s" % [order.size(), ", ".join(names)])
	print("[ui] wallet: %s" % ui.bags._wallet.get_parsed_text().replace("\n", " | "))
	await _shot("bags")
	ui.toggle_bags()
	ui.modern.menu.open("map")
	await _wait(1.0)
	print("[ui] bigmap: wide %s size %s log %s" % [str(ui.map_window.wide), str(ui.map_window.size), str(ui.map_window._log.visible)])
	await _shot("bigmap")
	ui.map_window.hide_window()
	ui.set_style("classic", false)
	await _wait(1.0)
	print("[ui] classic: panel %s strip %s windows shown: %s map wide %s" % [str(ui.right_panel.visible), str(ui._strip.visible),
			str(["status", "target", "time"].map(func(id): return ui.windows[id].visible)), str(ui.map_window.wide)])
	await _shot("classic")
	get_tree().quit()
