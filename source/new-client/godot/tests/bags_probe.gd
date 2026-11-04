extends Node
## Debug (claude 2026-11-04): the modern bags without the equipment strip; right-click to equip (in the bags and on the
## Hero panel); the zone's events as the server sends them. Puts the item back where it was.
##   --auto-play=hib:Zenuashu --live-probe=bags_probe
var v: Node


func _shot(tag: String) -> void:
	for i in 8:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("E:/Offline DAOC 036c/claude-work/walk/bags_%s.png" % tag)


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _right_click(c: Control) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_RIGHT
	e.pressed = true
	c._gui_input(e)


func _ready() -> void:
	get_tree().create_timer(150.0).timeout.connect(func(): print("[bags] timed out"); get_tree().quit())
	await _wait(25.0)
	v = get_tree().current_scene
	var ui = v.ui
	ui.map_window.visible = false
	ui.set_style("modern", false)
	await _wait(1.0)
	ui.toggle_bags()
	await _wait(1.0)
	print("[bags] window size %s" % str(ui.bags.size))
	await _shot("window")
	# right-click a piece of armour in the bags: it should be worn (what was worn goes to the bag)
	var cell = null
	for c in ui.bags._cells:
		var it := PlayerData.item_at(int(c.slot))
		if c.visible and not it.is_empty() and int(it.get("object_type", 0)) in [32, 33, 34, 35, 36, 37, 38]:
			cell = c
			break
	if cell:
		var from := int(cell.slot)
		var it := PlayerData.item_at(from)
		var to := int(PlayerData.slots_for(it)[0]) if not PlayerData.slots_for(it).is_empty() else -1
		var was := String(PlayerData.item_at(to).get("name", "")) if to >= 0 else ""
		print("[bags] right-click %s (bag %d) -> slot %d, worn there now: %s" % [it.get("name", ""), from, to, was])
		_right_click(cell)
		await _wait(2.5)
		print("[bags] after: slot %d holds %s" % [to, String(PlayerData.item_at(to).get("name", ""))])
		await _shot("equipped")
		# put it back: the bag item (now worn) back to where it was
		var back := -1
		for s in range(40, 80):
			if PlayerData.item_at(s).is_empty():
				back = s
				break
		if was != "":
			# the old piece went to the bags: right-click it to wear it again
			for c in ui.bags._cells:
				if c.visible and String(PlayerData.item_at(int(c.slot)).get("name", "")) == was:
					_right_click(c)
					break
		elif back >= 0:
			PlayerData.move(to, back)
		await _wait(2.5)
		print("[bags] restored: slot %d holds %s" % [to, String(PlayerData.item_at(to).get("name", ""))])
	else:
		print("[bags] no armour in the bags to try")
	ui.toggle_bags()
	# the events of this zone (EventTracker's list from the server's #EV lines)
	await _wait(3.0)
	var evs: Array = preload("res://game/ui/event_tracker.gd").in_zone(207)
	print("[bags] Connacht events: %s" % str(evs.map(func(e): return "%s(%s)" % [String(e.get("id", e.get("title", ""))), String(e.get("state", ""))])))
	get_tree().quit()
