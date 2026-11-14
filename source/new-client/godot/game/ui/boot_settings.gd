extends Node
## Autoload "BootSettings": applies the player's saved display settings (window mode, resolution, frame cap) the
## moment the game starts, before the login screen - they used to apply only once the world loaded, so the game
## opened windowed and switched on entering (owner 2026-10-09). Test runs (--ui-test, --shots ...) are left alone so
## they stay in their own window. Options > VIDEO applies changes through apply_display() too.
## Modes: "windowed" (a normal window at the resolution), "borderless" (a borderless window over the whole screen),
## "fullscreen" (exclusive full screen) - the last two render the world at the chosen resolution (res_scale).

const TEST_FLAGS := ["ui-test", "ui-shots", "shots", "probe", "live-probe", "tour", "bench", "pregame-shot", "login-shot"]

## Developer mode (owner 2026-10-13: "make sure debug mode like ctrl f12 is disabled on the godot release"): the debug
## text (Ctrl+F12), the bot inspector (Ctrl+F11) and the Ctrl+F1..F11 test keys work only with a dev_mode.txt file in
## the game folder (godot/ - the owner's working copy has one; a release package leaves it out) or --dev on the
## command line; test runs always. Everything else is the same either way.
static var dev: bool = _dev_mode()


static func _dev_mode() -> bool:
	if FileAccess.file_exists("res://dev_mode.txt"):
		return true
	for a in OS.get_cmdline_user_args():
		if a == "--dev" or a.trim_prefix("--").split("=")[0] in TEST_FLAGS:
			return true
	return false


func _ready() -> void:
	# the window's name (owner 2026-11-11: Offline DAoC Remastered) - set here, not as the project's name, which names
	# the folder every player's settings live in
	DisplayServer.window_set_title("Offline DAoC Remastered")
	_build_fps_counter()
	for a in OS.get_cmdline_user_args():
		if a.trim_prefix("--").split("=")[0] in TEST_FLAGS:
			return
	var cfg := UiArt.load_settings()
	if cfg.get_sections().is_empty():
		return
	if cfg.has_section_key("display", "fps_cap"):
		apply_fps(int(cfg.get_value("display", "fps_cap", 0)))
	# the monitor it was kept on (a work PC's second screen: the game came up on the other one, not at 4K)
	var screen := int(cfg.get_value("display", "screen", -1))
	if screen >= 0 and screen < DisplayServer.get_screen_count() and screen != DisplayServer.window_get_current_screen():
		DisplayServer.window_set_current_screen(screen)
	if cfg.has_section_key("display", "window_mode") or cfg.has_section_key("display", "resolution"):
		apply_display(String(cfg.get_value("display", "window_mode", "windowed")), cfg.get_value("display", "resolution", []))
	show_fps(bool(cfg.get_value("display", "show_fps", false)))


static func apply_fps(cap: int) -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED if cap < 0 else DisplayServer.VSYNC_ENABLED)
	Engine.max_fps = maxi(cap, 0)


## The world's render size against the window (owner 2026-11-08: a lower resolution in borderless left a small window
## in the middle of the screen, "not stretched to take up my whole screen as it should"): borderless and full screen
## always cover the screen; a resolution below the screen's renders the 3D world at that size and stretches it, the
## interface staying sharp at the screen's own. Graphics.apply_viewport multiplies its render scale by this.
static var res_scale := 1.0


static func apply_display(mode: String, res) -> void:
	var screen := DisplayServer.window_get_current_screen()
	var full := DisplayServer.screen_get_size(screen)
	var want := Vector2i(int(res[0]), int(res[1])) if res is Array and res.size() == 2 else full
	if mode == "fullscreen":
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, false)
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)
	else:
		if DisplayServer.window_get_mode() != DisplayServer.WINDOW_MODE_WINDOWED:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, mode == "borderless")
		if mode == "borderless":                           # (the whole screen, whatever the resolution)
			DisplayServer.window_set_size(full)
			DisplayServer.window_set_position(DisplayServer.screen_get_position(screen))
		else:
			var area := DisplayServer.screen_get_usable_rect(screen)
			var size := want.min(full)
			DisplayServer.window_set_size(size)
			DisplayServer.window_set_position(area.position + (area.size - size) / 2)
	res_scale = 1.0
	if mode != "windowed" and want.y > 0 and want.y < full.y:
		res_scale = clampf(float(want.y) / float(full.y), 0.25, 1.0)
	var g := (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Graphics") if Engine.get_main_loop() else null
	if g:
		g.apply_viewport()


# ---------------------------------------------------------------- the FPS counter (owner 2026-11-08: "an FPS counter that I
# can tick on ... small in one of the corners of the screen (probably top left)"): Options > VIDEO, [display] show_fps
var _fps_layer: CanvasLayer
var _fps_label: Label
var _fps_t := 0.0


func _build_fps_counter() -> void:
	_fps_layer = CanvasLayer.new()
	_fps_layer.layer = 120
	_fps_layer.visible = false
	add_child(_fps_layer)
	_fps_label = Label.new()
	_fps_label.position = Vector2(6, 4)
	_fps_label.add_theme_font_size_override("font_size", 13)
	_fps_label.add_theme_color_override("font_color", Color(0.95, 0.9, 0.6))
	_fps_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_fps_label.add_theme_constant_override("outline_size", 4)
	_fps_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fps_layer.add_child(_fps_label)
	set_process(false)


func show_fps(on: bool) -> void:
	if _fps_layer == null:
		return
	_fps_layer.visible = on
	set_process(on)
	_fps_t = 1.0


func _process(delta: float) -> void:
	_fps_t += delta
	if _fps_t >= 0.25:                                     # (four times a second: readable, not flickering)
		_fps_t = 0.0
		_fps_label.text = "%d FPS" % roundi(Engine.get_frames_per_second())
