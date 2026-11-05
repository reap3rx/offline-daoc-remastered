extends Node
## Debug (claude 2026-11-04): quickbar slots found again by name when the server's skill list has moved, and the
## King's summon icons. Puts the bars back as they were.
##   --auto-play=alb:Arthur --live-probe=bars_probe
func _row() -> String:
	var first := 0
	while first < Server.skills.size() and int(Server.skills[first].page) == 0:
		first += 1
	var out: Array = []
	for bank in PlayerData.quickbars[0]:
		for e in bank:
			if e is Dictionary and String(e.get("id", "")).begins_with("srv:skill:"):
				var i := first + int(String(e.id).get_slice(":", 2))
				var at := String(Server.skills[i].name) if i < Server.skills.size() else "?"
				out.append("%s=%s%s" % [e.name, at, "" if at == String(e.name) else " (WRONG)"])
	return ", ".join(out)


func _ready() -> void:
	get_tree().create_timer(90.0).timeout.connect(func(): get_tree().quit())
	await get_tree().create_timer(25.0).timeout
	print("[bars] at login: %s" % _row())
	var icons: Array = []
	for s in Server.skills:
		if String(s.name).begins_with("Summon"):
			icons.append("%s:%d" % [s.name, int(s.icon)])
	print("[bars] summon icons from the server: %s" % ", ".join(icons))
	var saved := JSON.stringify(PlayerData.quickbars)
	# the list "moves": every skill slot pointed one place on, as after a new spell
	for bank in PlayerData.quickbars[0]:
		for e in bank:
			if e is Dictionary and String(e.get("id", "")).begins_with("srv:skill:"):
				e["id"] = "srv:skill:%d" % (int(String(e.id).get_slice(":", 2)) + 1)
	print("[bars] moved: %s" % _row())
	Server._refresh_bar_icons()
	print("[bars] after the fix: %s" % _row())
	PlayerData.quickbars = JSON.parse_string(saved)
	PlayerData._save_server_quickbars()
	await get_tree().create_timer(1.0).timeout
	get_tree().quit()
