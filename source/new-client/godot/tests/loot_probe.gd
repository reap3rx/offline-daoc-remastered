extends Node
## Debug (claude 2026-11-04): the modern loot feed (an item dropped and picked up again: the server's "#LOOT|" line),
## the minimap's edge marks, the modern pet window (the King's commander and a retainer), the bags' con frames and the
## compare tooltip. The save is put back from the cloud copy afterwards.
##   --auto-play=alb:Arthur --live-probe=loot_probe
var v: Node


func _shot(tag: String) -> void:
	for i in 8:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("E:/Offline DAOC 036c/claude-work/walk/loot_%s.png" % tag)


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _spell(words: Array) -> String:
	var first := Server.skills.size()                     # (a hybrid's spells are skills: "srv:skill:<n>", n after the specs)
	for i in Server.skills.size():
		if int(Server.skills[i].page) != 0:
			first = i
			break
	for i in range(first, Server.skills.size()):
		for w in words:
			if String(Server.skills[i].get("name", "")).to_lower().contains(w):
				return "srv:skill:%d" % (i - first)
	for li in Server.spell_lines.size():
		for sp in Server.spell_lines[li].spells:
			var n := String(sp.name).to_lower()
			for w in words:
				if n.contains(w) and int(sp.level) <= PlayerData.level:
					return "srv:spell:%d:%d" % [li, int(sp.level)]
	return ""


func _ready() -> void:
	get_tree().create_timer(170.0).timeout.connect(func(): print("[loot] timed out"); get_tree().quit())
	await _wait(25.0)
	v = get_tree().current_scene
	v.ui.set_style("modern", false)
	await _wait(1.0)
	var names: Array = []
	for l in Server.spell_lines:
		for sp in l.spells:
			names.append("%s(%d)" % [sp.name, int(sp.level)])
	print("[loot] spells: %s" % ", ".join(names))
	var bn: Array = []
	for bar in PlayerData.quickbars:
		for bank in bar:
			for e in bank:
				if e is Dictionary and not e.is_empty():
					bn.append("%s:%s" % [e.get("kind", ""), e.get("name", "")])
	print("[loot] on the bars: %s" % ", ".join(bn))
	# --- the pet: the commander, then a retainer
	var cmd := _spell(["summon squire"])
	print("[loot] commander spell: %s" % cmd)
	if cmd != "":
		Server.use(cmd)
		await _wait(7.0)
	print("[loot] pet: %s  classic window visible: %s" % [str(PlayerData.pet), str(v.ui.windows["minipet"].visible)])
	var ret := _spell(["summon acolyte"])
	print("[loot] retainer spell: %s" % ret)
	if ret != "":
		Server.use(ret)
		await _wait(6.0)
	await _wait(4.0)
	print("[loot] retinue: %s" % str(Server.pet_retinue))
	await _shot("pet")
	# --- loot: a gear item dropped and picked up again
	var gear := -1
	for s in range(PlayerData.BACKPACK, PlayerData.BACKPACK_END + 1):
		var it := PlayerData.item_at(s)
		if not it.is_empty() and not PlayerData.slots_for(it).is_empty() and not String(it.name).to_lower().contains("personal"):
			gear = s
			break
	print("[loot] gear slot %d: %s" % [gear, str(PlayerData.item_at(gear).get("name", "")) if gear >= 0 else ""])
	if gear >= 0:
		Server.client.call("MoveItem", gear, 1, 1)
		await _wait(2.0)
		v.npcs.target_nearest_loot()
		await _wait(0.6)
		v.npcs.get_object()
		await _wait(1.5)
	# and a few made up here, the shapes the server sends: money, a currency, junk, a stack
	var feed = v.ui.modern.loot
	feed.receive("m|23456")
	await _wait(0.3)
	feed.receive("i|4|116|100|0|0|-3|trash|Soul Gem (Empty)")
	await _wait(0.3)
	feed.receive("i|12|1438|100|0|1|-3|currency|Mark of Valor")
	await _wait(0.3)
	feed.receive("i|1|2133|94|18250|14|1|item|Ancient Ring of Valor")
	feed.receive("m|180")
	await _wait(0.6)
	print("[loot] feed rows: %s" % str(feed.rows.map(func(r): return "%s x%d %s v%d con%d" % [r.kind, int(r.count), r.name, int(r.value), int(r.con)])))
	await _shot("feed")
	# --- the minimap zoomed right in: what's past the rim is pinned to it
	var ET = preload("res://game/ui/event_tracker.gd")
	print("[loot] events here: %s" % str(ET.in_zone(v.ui.map_window.current_zone).map(func(e): return String(e.get("state", "")))))
	print("[loot] marks: %s" % str(v.ui.map_window.marks.map(func(m): return String(m.kind))))
	v.ui.modern.minimap.span = 0.06
	await _wait(0.2)
	var pp: Vector3 = v.player.global_position
	v.ui.map_window.marks = v.ui.map_window.marks + [{"at": Vector2(pp.x + 150.0, pp.z - 60.0), "kind": "step"}, {"at": Vector2(pp.x - 90.0, pp.z + 200.0), "kind": "task"}]
	await _wait(0.1)
	await _shot("minimap")
	v.ui.modern.minimap.span = 0.22
	# --- the bags: con frames, and the compare box put on screen to look at
	v.ui.toggle_bags()
	await _wait(1.0)
	var cmp: Control = null
	for s in range(PlayerData.BACKPACK, PlayerData.BACKPACK_END + 1):
		var it := PlayerData.item_at(s)
		if not it.is_empty() and ItemTooltip.worn_slot(it) >= 0:
			Server.prefetch_item(s)
			Server.prefetch_item(ItemTooltip.worn_slot(it))
			await _wait(1.5)
			cmp = ItemTooltip.compare(s)
			print("[loot] compare %s vs slot %d: %s" % [String(it.name), ItemTooltip.worn_slot(it), cmp.get_class() if cmp else "null"])
			break
	if cmp:
		var pc := PanelContainer.new()
		pc.add_child(cmp)
		pc.position = Vector2(40, 260)
		v.ui.root.add_child(pc)
	await _shot("bags")
	print("[loot] done")
	await _wait(1.0)
	get_tree().quit()
