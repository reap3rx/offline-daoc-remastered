extends Node
## Autoload WorldLink. What is left of the game's own bots (the old standalone game: your companions and the world's
## gamebots, simulated here in C#): every bot is the server's now, and that code went 2026-11-15. This keeps the calls
## the game still makes - the map's green dots are live (the server's bots); the rest do nothing.

var bots: Node = null                         # (always null: there are no bots of the game's own)


func zone_entered(_zone: Node3D, _zone_id: int) -> void:
	pass


func zone_switched(_zone: Node3D, _zone_id: int) -> void:
	pass


func zone_left() -> void:
	pass


func pick_bot(_cam: Camera3D, _screen: Vector2) -> Node3D:
	return null


func target_bot(_view: Node3D) -> void:
	pass


func clear_bot_target() -> void:
	pass


## Your realm's bots in your zone, for the map's green dots (Options > BOTS > REALM BOTS ON MAP; enemy bots never).
func bot_dots() -> PackedVector3Array:
	return Server.bot_dots() if Server.active and UiArt.bot_option("map_dots") else PackedVector3Array()


func companion_dots() -> PackedVector3Array:
	return PackedVector3Array()


func inspect_target() -> void:
	pass
