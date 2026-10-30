extends Node
## Debug (owner 2026-10-30, Action Combat Styles): in the server's world (--auto-play), open the styles window, list
## what the server sent, open the power-attack chooser, pick its first style and put it back to automatic; pictures.
##   --server=... --auto-play=alb:Name --live-probe=ac_styles_probe --out=<dir>
func _ready() -> void:
	var v := get_tree().current_scene
	var out := ProjectSettings.globalize_path(String(v.args.get("out", "user://ac_styles")))
	DirAccess.make_dir_recursive_absolute(out)
	await get_tree().create_timer(10.0).timeout
	v.ui.windows["ac_styles"].show_window()
	await get_tree().create_timer(3.0).timeout
	for k in Server.ac_styles:
		print("[styles] ", k, " ", Server.ac_styles[k])
	var ac = v.action_combat
	if ac:
		print("[styles] windows: parry ", ac._win_parry, " block ", ac._win_block, " dodge ", ac._win_dodge)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + "/styles_1.png")
	var w = v.ui.windows.get("ac_styles")
	w._choose("anytime")
	await get_tree().create_timer(1.0).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + "/styles_2.png")
	var opts: Array = Server.ac_styles.get("anytime", {}).get("options", [])
	if not opts.is_empty():
		Server.command("/ac pick anytime %d" % int(opts[0].id))
		await get_tree().create_timer(2.0).timeout
		print("[styles] after pick: ", Server.ac_styles.get("anytime"))
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(out + "/styles_3.png")
		Server.command("/ac pick anytime auto")
		await get_tree().create_timer(2.0).timeout
		print("[styles] after auto: ", Server.ac_styles.get("anytime"))
	get_tree().quit()
