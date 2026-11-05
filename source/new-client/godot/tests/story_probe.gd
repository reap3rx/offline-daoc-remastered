extends Node
## Debug (claude 2026-11-05): the story quests of Camelot Hills, step by step with /storyquest's testing commands (the
## server's story-quests/.testing flag): the people and their marks, the journal, the map marker, a clue, an
## encounter's monsters, the endings and their rewards. The save is put back from the cloud afterwards.
##   --auto-play=alb:Arthur --live-probe=story_probe
var v: Node


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _shot(tag: String) -> void:
	for i in 8:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("E:/Offline DAOC 036c/claude-work/walk/story_%s.png" % tag)


func _cmd(c: String, wait := 1.2) -> void:
	print("[story] > ", c)
	Server.command(c)
	await _wait(wait)


func _near(words: Array) -> String:
	var out: Array = []
	if v.npcs and v.npcs.get("states") != null:
		for s in v.npcs.states:
			var nm := String(s.spawn.get("name", ""))
			for w in words:
				if nm.to_lower().contains(String(w).to_lower()):
					out.append("%s(q%d,%.0fm)" % [nm, int(s.spawn.get("quest", 0)), (s.pos as Vector3).distance_to(v.player.global_position)])
					break
	return ", ".join(out)


func _journal() -> String:
	var out: Array = []
	for i in Server.quests:
		var q: Dictionary = Server.quests[i]
		out.append("%s :: %s :: %s" % [q.name, q.get("text", ""), str(q.get("goals", []).map(func(g): return String(g.text) + ("(done)" if g.done else "")))])
	return " || ".join(out)


func _ready() -> void:
	get_tree().create_timer(330.0).timeout.connect(func(): print("[story] timed out"); get_tree().quit())
	await _wait(25.0)
	v = get_tree().current_scene
	v.ui.set_style("modern", false)
	var log_lines: Array = []
	PlayerData.message.connect(func(t, _k): log_lines.append(String(t)))
	for q in ["tomb_keeps", "pilgrims", "bell_price"]:
		await _cmd("/storyquest reset " + q, 0.4)
	# --- What the Tomb Keeps
	await _cmd("/storyquest goto npc maren_hale", 4.0)
	print("[story] near Maren: ", _near(["Maren", "Hob", "Ysolde", "Tamsin"]))
	await _shot("cotswold")
	await _cmd("/storyquest talk maren_hale")
	await _cmd("/storyquest say maren_hale Hob")
	await _cmd("/storyquest say maren_hale look for him", 1.5)
	print("[story] journal: ", _journal())
	print("[story] markers: ", str(Server.map_markers))
	await _shot("accepted")
	await _cmd("/storyquest goto npc hob_tanner", 3.0)
	await _cmd("/storyquest talk hob_tanner")
	await _cmd("/storyquest say hob_tanner barrows")
	print("[story] journal: ", _journal())
	await _cmd("/storyquest goto tomb_keeps", 4.0)
	await _cmd("/storyquest click")
	await _shot("camp")
	await _cmd("/storyquest goto tomb_keeps", 6.0)            # into the tomb, to Brother Eadric
	print("[story] in the tomb: ", _near(["Eadric"]))
	await _cmd("/storyquest talk brother_eadric")
	await _cmd("/storyquest say brother_eadric offerings")
	await _cmd("/storyquest goto tomb_keeps", 4.0)
	await _cmd("/storyquest click")
	print("[story] journal: ", _journal())
	await _cmd("/storyquest goto tomb_keeps", 5.0)            # the encounter wakes
	print("[story] encounter: ", _near(["Caddoc", "disciple"]))
	await _shot("encounter")
	await _cmd("/storyquest done tomb_keeps")
	await _cmd("/storyquest goto tomb_keeps", 5.0)            # home: the reach step
	await _cmd("/storyquest talk maren_hale")
	await _cmd("/storyquest say maren_hale the truth", 1.5)
	print("[story] journal: ", _journal())
	await _cmd("/storyquest say maren_hale Hale Family Signet", 1.5)
	await _cmd("/storyquest list")
	# --- The Pilgrim's Letters
	await _cmd("/storyquest goto npc ysolde_marchant", 3.0)
	await _cmd("/storyquest talk ysolde_marchant")
	await _cmd("/storyquest say ysolde_marchant find him")
	await _cmd("/storyquest goto pilgrims", 4.0)
	await _cmd("/storyquest goto pilgrims", 3.0)              # to Gerrit
	await _cmd("/storyquest talk gerrit_woodcutter")
	await _cmd("/storyquest say gerrit_woodcutter letters")
	await _cmd("/storyquest goto pilgrims", 3.0)
	await _cmd("/storyquest click")
	await _cmd("/storyquest goto pilgrims", 5.0)
	print("[story] defend: ", _near(["Elric", "convert"]))
	await _shot("defend")
	await _cmd("/storyquest done pilgrims")
	await _cmd("/storyquest goto pilgrims", 4.0)
	print("[story] home: ", _near(["Elric", "Ysolde"]))
	await _cmd("/storyquest talk ysolde_marchant", 1.5)
	await _cmd("/storyquest say ysolde_marchant Three-Note Band", 1.5)
	# --- The Bell-Wether's Price
	await _cmd("/storyquest goto npc tamsin", 3.0)
	await _cmd("/storyquest talk tamsin")
	await _cmd("/storyquest say tamsin get it back")
	await _cmd("/storyquest goto bell_price", 4.0)
	await _cmd("/storyquest goto bell_price", 5.0)            # the kill step: its faeries
	print("[story] faeries: ", _near(["mischief", "Wren"]))
	await _shot("faeries")
	await _cmd("/storyquest done bell_price")
	await _cmd("/storyquest goto bell_price", 3.0)
	await _cmd("/storyquest talk wren_herald")
	await _cmd("/storyquest say wren_herald bargain")
	await _cmd("/storyquest goto npc tamsin", 3.0)
	await _cmd("/storyquest talk tamsin", 1.5)
	await _cmd("/storyquest say tamsin Sheep-Song Sash", 1.5)
	await _cmd("/storyquest list", 1.5)
	var inv: Array = []
	for s in range(PlayerData.BACKPACK, PlayerData.BACKPACK_END + 1):
		var it := PlayerData.item_at(s)
		if not it.is_empty():
			inv.append(String(it.name))
	print("[story] backpack: ", ", ".join(inv))
	print("[story] messages:\n  " + "\n  ".join(log_lines.slice(maxi(0, log_lines.size() - 120))))
	get_tree().quit()
