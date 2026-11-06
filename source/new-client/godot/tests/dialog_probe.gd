extends Node
## Debug (claude 2026-11-06): the story dialogue window - a GM jump to Wenna Ashby (Salisbury Plains), a click: the
## quest window (lore, rewards); a [question]; ACCEPT; then her talk once it's under way. Shots in claude-work/walk.
##   --auto-play=alb:Arthur --live-probe=dialog_probe  (a test server; the account a GM there)
var v: Node


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _shot(tag: String) -> void:
	for i in 10:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("E:/Offline DAOC 036c/claude-work/walk/dlg_%s.png" % tag)
	print("[dlg] shot ", tag)


func _find(nm: String) -> int:
	var w = v.get("npcs")
	if w == null or w.get("states") == null:
		return 0
	for s in w.states:
		if String(s.spawn.get("name", "")) == nm:
			return int(s.spawn.get("oid", 0))
	return 0


func _ready() -> void:
	get_tree().create_timer(240.0).timeout.connect(func(): print("[dlg] timed out"); get_tree().quit())
	v = get_tree().current_scene
	await _wait(20.0)
	var r: Vector3 = Server.to_region(1, Vector3(721, 54.5, 216))
	Server.command("/jump to %d %d %d 1" % [int(r.x), int(r.y), int(r.z) + 40])
	await _wait(14.0)
	var oid := _find("Wenna Ashby")
	print("[dlg] Wenna oid ", oid)
	if oid == 0:
		get_tree().quit()
		return
	v.npcs.target_oid(oid)
	await _wait(1.0)
	var me: Vector3 = Server.to_region(1, v.player.global_position)
	Server.client.call("Interact", oid, int(me.x), int(me.y))
	await _wait(2.5)
	var sd = v.ui.get("story_dialog")
	print("[dlg] window ", sd.visible if sd else "none")
	await _shot("offer")
	Server.command("/whisper carter")
	await _wait(2.0)
	await _shot("topic")
	Server.command("/whisper find Aled")
	await _wait(2.0)
	await _shot("accepted")
	Server.client.call("Interact", oid, int(me.x), int(me.y))
	await _wait(2.0)
	await _shot("talk")
	v.ui.journal.show_window()
	for i in Server.quests:
		if String(Server.quests[i].name).to_lower() == "under the stones":
			v.ui.journal.selected = "srv%d" % int(i)
	v.ui.journal.refresh()
	print("[dlg] story info: ", Server.story_info.keys())
	await _wait(1.5)
	await _shot("journal")
	get_tree().quit()
