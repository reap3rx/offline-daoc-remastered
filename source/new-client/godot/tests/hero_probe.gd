extends Node
## Debug (claude 2026-11-03): the modern Hero panel - equipment (a slot picked: the backpack filtered), skills
## (specialization + the spellbook roadmap, realm skills), the effective level under the orb with a lower monster
## targeted, a window and the minimap scaled by their corners. Client side only (nothing saved).
##   --auto-play=hib:Zenuashu --live-probe=hero_probe
var v: Node


func _shot(tag: String) -> void:
	for i in 8:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("E:/Offline DAOC 036c/claude-work/walk/hero_%s.png" % tag)


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _ready() -> void:
	get_tree().create_timer(170.0).timeout.connect(func(): print("[hero] timed out"); get_tree().quit())
	await _wait(25.0)
	v = get_tree().current_scene
	var ui = v.ui
	ui.map_window.visible = false
	ui.set_style("modern", false)
	await _wait(1.0)
	# the effective level: the nearest monster targeted
	var sw = v.npcs
	var best = null
	var bd := 1e9
	for st in sw.by_oid.values():
		if st == null or st.view == null or int(st.spawn.get("realm", 0)) != 0:
			continue
		var d: float = st.view.global_position.distance_to(v.player.global_position)
		if d < bd and int(st.spawn.get("level", 0)) > 0:
			bd = d
			best = st.view
	if best:
		sw.select(best)
		print("[hero] targeted %s L%d at %.0f m" % [String(best.spawn.name), int(best.spawn.get("level", 0)), bd])
	await _wait(3.0)
	print("[hero] you L%d, fight level %d" % [PlayerData.level, Server.fight_level])
	await _shot("orb")
	ui.open_hero("equipment")
	await _wait(1.5)
	print("[hero] panel visible %s page %s size %s" % [str(ui.hero.visible), ui.hero.page, str(ui.hero.size)])
	await _shot("equipment")
	for sl in range(40, 80):
		var it := PlayerData.item_at(sl)
		if not it.is_empty():
			print("[hero] bag %d: %s type %d obj %d model %d" % [sl, it.get("name", ""), int(it.get("item_type", -1)), int(it.get("object_type", -1)), int(it.get("model", -1))])
	ui.hero.pick_slot(12)
	await _wait(0.5)
	print("[hero] filter 12: %s" % ui.hero._filter_label.text)
	await _shot("equip_twohand")
	ui.hero.pick_slot(25)
	await _wait(0.5)
	print("[hero] filter 25: %s" % ui.hero._filter_label.text)
	ui.open_hero("skills")
	await _wait(4.0)
	var specs: Array = Server.book.specs
	print("[hero] book: %d points, %d specs" % [int(Server.book.points), specs.size()])
	for sp in specs:
		var have := (sp.skills as Array).filter(func(k): return bool(k.have)).size()
		print("[hero]   %s L%d: %d skills, %d known; first: %s" % [sp.name, sp.level, (sp.skills as Array).size(), have,
				str((sp.skills as Array).slice(0, 3).map(func(k): return "%s %s L%d %s" % [k.group, k.name, k.level, k.have]))])
	print("[hero] trainer specs %d, realm abilities %d, classic trainer shown %s" % [Server.trainer_specs.size(),
			Server.realm_abilities.size(), str(ui.trainer.visible)])
	await _shot("skills")
	if specs.size() > 1:
		ui.hero._book_spec = int(specs[1].index)
		ui.hero._fill_book()
		await _wait(0.5)
		await _shot("skills2")
	ui.hero.show_page("realm")
	await _wait(1.0)
	await _shot("realm")
	ui.hero.set_zoom(0.8, false)
	await _wait(0.5)
	await _shot("hero_small")
	ui.hero.hide_window()
	ui.toggle_bags()
	ui.bags.set_zoom(1.35, false)
	ui.modern.mini = 260.0
	ui.modern.layout()
	await _wait(1.0)
	await _shot("scaled")
	ui.bags.set_zoom(1.0, false)
	ui.toggle_bags()
	get_tree().quit()
