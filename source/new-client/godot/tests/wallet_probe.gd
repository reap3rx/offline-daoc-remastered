extends Node
## Debug (claude 2026-11-03): the wallet - what the server told us ("#WAL|"), the bag grid and the wallet line.
##   --auto-play=hib:Mongfar --live-probe=wallet_probe
func _ready() -> void:
	await get_tree().create_timer(30.0).timeout
	var v = get_tree().current_scene
	var MB = preload("res://game/ui/modern_bags.gd")
	print("[wallet] server says: %s" % str(MB.server_wallet))
	var marks := 0
	for s in range(PlayerData.BACKPACK, PlayerData.BACKPACK_END + 1):
		var it := PlayerData.item_at(s)
		if not it.is_empty() and String(it.get("name", "")).to_lower() == "mark of valor":
			marks += int(PlayerData.entry(s).get("count", 1))
	print("[wallet] marks still in the backpack: %d" % marks)
	v.ui.set_style("modern", false)
	v.ui.toggle_bags()
	await get_tree().create_timer(1.0).timeout
	print("[wallet] bag wallet line: %s" % v.ui.bags._wallet.get_parsed_text().replace("\n", " | "))
	Server.command("/wallet")
	await get_tree().create_timer(2.0).timeout
	get_tree().quit()
