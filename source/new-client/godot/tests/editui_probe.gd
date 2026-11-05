extends Node
## Debug (claude 2026-11-04): Options > EDIT UI - every modern piece framed, one dragged and kept, then put back.
##   --auto-play=alb:Arthur --live-probe=editui_probe
var v: Node


func _shot(tag: String) -> void:
	for i in 8:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("E:/Offline DAOC 036c/claude-work/walk/editui_%s.png" % tag)


func _ready() -> void:
	get_tree().create_timer(100.0).timeout.connect(func(): get_tree().quit())
	await get_tree().create_timer(25.0).timeout
	v = get_tree().current_scene
	v.ui.set_style("modern", false)
	await get_tree().create_timer(1.0).timeout
	var before: Dictionary = v.ui.modern.custom.duplicate()
	print("[edit] kept before: %s" % str(before))
	v.ui.options.show_window()
	await get_tree().create_timer(0.5).timeout
	v.ui.options._edit_ui()
	await get_tree().create_timer(1.0).timeout
	var ed: Node = null
	for c in v.ui.get_children():
		if c.get_script() == preload("res://game/ui/ui_editor.gd"):
			ed = c
	print("[edit] editor open: %s, options visible: %s" % [str(ed != null), str(v.ui.options.visible)])
	print("[edit] framed: %s" % str(ed._items.map(func(it): return "%s %s" % [it.name, str(ed._rect(it))])))
	await _shot("open")
	for it in ed._items:
		if String(it.id) in ["pet", "loot"]:
			var p0: Vector2 = it.ctrl.position
			ed._move(it, Vector2(-900, -350) if String(it.id) == "pet" else Vector2(-1400, 0))
			ed._let_go(it)
			print("[edit] %s moved %s -> %s, kept %s" % [it.id, str(p0), str(it.ctrl.position), str(v.ui.modern.custom.get(it.id))])
	v.ui.modern.layout()
	print("[edit] after a layout: pet %s loot %s" % [str(v.ui.modern.pet.position), str(v.ui.modern.loot.position)])
	await _shot("moved")
	ed.close()
	await get_tree().create_timer(0.3).timeout
	v.ui.modern.custom = before
	v.ui.modern._save_custom()
	v.ui.modern.layout()
	print("[edit] put back: %s pet %s" % [str(v.ui.modern.custom), str(v.ui.modern.pet.position)])
	get_tree().quit()
