extends Node
## Debug / pipeline (claude 2026-11-02, owner: "a solution to making the maps more high-rez, since there are no
## official ones"): the zone drawn from straight above with an orthographic camera, tile by tile, into one big picture
## - every tree, path, building and stream where it really is. Offline zone viewer, noon, no fog, no interface:
##   Godot --path godot -- --zone=207 --probe=map_render --time=13 [--map-px=8192] [--map-tiles=8]
## writes content/maps/render/z<zone>.jpg (4096 px, what the map and minimap draw when zoomed in) and, with --map-png,
## the full picture to claude-work/maps.
var v: Node
const OUT := "E:/Offline DAOC 036c/claude-work/maps"


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _arg(k: String, d: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % k):
			return a.get_slice("=", 1)
	return d


func _ready() -> void:
	get_tree().create_timer(900.0).timeout.connect(func(): print("[map] timed out"); get_tree().quit())
	await _wait(12.0)
	v = get_tree().current_scene
	var zone_id := int(_arg("zone", "207"))
	var total_px := int(_arg("map-px", "8192"))
	var tiles := int(_arg("map-tiles", "8"))
	var px := total_px / tiles
	var size_m: float = float(v.zone.info.get("size_m", 1638.4))
	var tile_m := size_m / tiles
	if v.ui:
		v.ui.visible = false
	v.player.visible = false
	var env: Environment = v.sky.environment if v.sky else null
	if env:
		env.fog_enabled = false
		env.volumetric_fog_enabled = false
	var sv := SubViewport.new()
	sv.size = Vector2i(px, px)
	sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	sv.msaa_3d = Viewport.MSAA_4X
	add_child(sv)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = tile_m
	cam.near = 1.0
	cam.far = 4000.0
	sv.add_child(cam)
	cam.current = true
	var big := Image.create(total_px, total_px, false, Image.FORMAT_RGB8)
	DirAccess.make_dir_recursive_absolute(OUT)
	print("[map] zone %d: %.1f m, %d x %d tiles of %d px" % [zone_id, size_m, tiles, tiles, px])
	var started := Time.get_ticks_msec()
	for j in tiles:
		for i in tiles:
			var cx := (i + 0.5) * tile_m
			var cz := (j + 0.5) * tile_m
			var top := -INF
			for a in 5:
				for b in 5:
					var h: float = v.zone.height_at(i * tile_m + a * tile_m / 4.0, j * tile_m + b * tile_m / 4.0)
					if is_finite(h):
						top = maxf(top, h)
			if not is_finite(top):
				top = 0.0
			v.player.global_position = Vector3(cx, v.zone.height_at(cx, cz), cz)   # (streaming follows the player)
			var at := Vector3(cx, top + 120.0, cz)
			cam.look_at_from_position(at, at + Vector3.DOWN, Vector3.FORWARD)   # north (-Z) up
			for k in 6:
				await get_tree().process_frame
			await RenderingServer.frame_post_draw
			var img := sv.get_texture().get_image()
			img.convert(Image.FORMAT_RGB8)
			big.blit_rect(img, Rect2i(0, 0, px, px), Vector2i(i * px, j * px))
		print("[map] row %d of %d" % [j + 1, tiles])
	if _arg("map-png", "") != "":
		big.save_png("%s/z%03d_render.png" % [OUT, zone_id])
	var dir := ProjectSettings.globalize_path("res://content/maps/render")
	DirAccess.make_dir_recursive_absolute(dir)
	var keep := big.duplicate()
	keep.resize(4096, 4096, Image.INTERPOLATE_LANCZOS)
	keep.save_jpg("%s/z%03d.jpg" % [dir, zone_id], 0.9)
	var small := big.duplicate()
	small.resize(1024, 1024, Image.INTERPOLATE_LANCZOS)
	small.save_jpg("%s/z%03d_render_1024.jpg" % [OUT, zone_id], 0.9)
	print("[map] saved in %d s" % ((Time.get_ticks_msec() - started) / 1000))
	get_tree().quit()
