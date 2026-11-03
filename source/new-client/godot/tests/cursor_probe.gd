extends Node
## Debug (claude 2026-11-03): action combat's cursor key as a toggle, windows bringing the cursor out, and the action
## camera's distance kept per character. Puts back what it changed (action combat's state, the character's file).
##   --auto-play=hib:Zenuashu --live-probe=cursor_probe
const AC := preload("res://game/combat/action_combat.gd")
var v: Node


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _alt() -> void:
	var e := InputEventKey.new()
	e.keycode = KEY_ALT
	e.physical_keycode = KEY_ALT
	e.pressed = true
	Input.parse_input_event(e)
	await _wait(0.15)
	var u := e.duplicate() as InputEventKey
	u.pressed = false
	Input.parse_input_event(u)
	await _wait(0.15)


func _ready() -> void:
	get_tree().create_timer(120.0).timeout.connect(func(): print("[cur] timed out"); get_tree().quit())
	await _wait(25.0)
	v = get_tree().current_scene
	var ac = v.action_combat
	var p = v.player
	var path := "user://char_settings/zenuashu.cfg"
	var had := FileAccess.get_file_as_string(path) if FileAccess.file_exists(path) else ""
	var was_on: bool = ac.on
	print("[cur] at login, kept on the server: %s" % str(Server.client_cfg))
	var before: String = ac._packed()
	v.ui.set_style("modern", false)
	if not ac.on:
		Server.command("/ac toggle")
		await _wait(2.0)
	print("[cur] action combat on: %s, cursor out: %s" % [str(ac.on), str(p.action_cursor)])
	AC.cursor_toggle = true
	await _alt()
	print("[cur] toggle, one press: cursor %s" % str(p.action_cursor))
	await _alt()
	print("[cur] toggle, second press: cursor %s" % str(p.action_cursor))
	v.ui.toggle_bags()
	await _wait(0.3)
	print("[cur] bags open: cursor %s" % str(p.action_cursor))
	v.ui.toggle_bags()
	await _wait(0.3)
	print("[cur] bags closed: cursor %s" % str(p.action_cursor))
	v.ui.open_hero("equipment")
	await _wait(0.3)
	await _alt()
	print("[cur] hero open, key pressed: cursor %s" % str(p.action_cursor))
	v.ui.open_hero("equipment")
	await _wait(0.3)
	print("[cur] hero closed: cursor %s" % str(p.action_cursor))
	AC.cursor_toggle = false
	var e := InputEventKey.new()
	e.keycode = KEY_ALT
	e.physical_keycode = KEY_ALT
	e.pressed = true
	Input.parse_input_event(e)
	await _wait(0.3)
	print("[cur] hold mode, held: cursor %s" % str(p.action_cursor))
	var u := e.duplicate() as InputEventKey
	u.pressed = false
	Input.parse_input_event(u)
	await _wait(0.3)
	print("[cur] hold mode, let go: cursor %s" % str(p.action_cursor))
	# the action camera's distance, per character
	p.cam_distance = 3.25
	Server.command("/ac toggle")
	await _wait(2.0)
	var cfg := ConfigFile.new()
	cfg.load(path)
	print("[cur] off: saved ac distance %s, classic distance now %.2f" % [str(cfg.get_value("action_hud", "cam_distance", "none")), p.cam_distance])
	Server.command("/ac toggle")
	await _wait(2.0)
	print("[cur] on again: distance %.2f" % p.cam_distance)
	await _wait(1.5)
	print("[cur] sent to the server: %s" % str(Server.client_cfg))
	if not was_on:
		Server.command("/ac toggle")
		await _wait(2.0)
	await _wait(1.5)
	Server.store_cfg("action_hud", before)                 # (what it was)
	await _wait(1.0)
	if had == "":
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	else:
		var f := FileAccess.open(path, FileAccess.WRITE)
		f.store_string(had)
		f.close()
	print("[cur] restored (ac on: %s)" % str(ac.on))
	get_tree().quit()
