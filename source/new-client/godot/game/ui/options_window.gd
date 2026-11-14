class_name OptionsWindow
extends ClassicWindow
## The options window (options.bmp 384x420: list area with the client's scroll track, buttons on the stone below).
## Five pages: VIDEO (resolution, window mode, frame cap - the settings the client kept on its loading /
## character-select screens - and the render quality, owner 2026-10-13: presets, view distance, shadows, lighting,
## anti-aliasing, textures, grass, reset to defaults; Graphics), AUDIO, CONTROLS (key presets RPG / FPS / MMO from
## the client's keyboard.dat, every action with two bindings, Mouse 4 / 5 and the wheel bindable, movement style),
## INTERFACE (UI scale), WINDOWS (put closed windows back - owner 2026-10-09). Spell-icon options are left out
## (owner: the client's default icon set). Saved in user://settings.cfg (keys in user://keybinds.cfg).

const HEALTH_PLATES := preload("res://game/npcs/health_plates.gd")
const PAGES := ["video", "audio", "controls", "interface", "chat", "windows", "controller"]
const PAGE_NAMES := ["VIDEO", "AUDIO", "CONTROLS", "INTERFACE", "CHAT", "WINDOWS"]
const RESOLUTIONS := [Vector2i(1280, 720), Vector2i(1366, 768), Vector2i(1600, 900), Vector2i(1920, 1080),
		Vector2i(2560, 1080), Vector2i(2560, 1440), Vector2i(3440, 1440), Vector2i(3840, 2160)]
const FPS_CAPS := [0, 30, 60, 75, 90, 120, 144, 165, 240, -1]   # 0 = monitor refresh (vsync), -1 = unlimited
const VOLUMES := [["Master", "MASTER VOLUME"], ["Effects", "SOUND EFFECTS"], ["Ambient", "AMBIENCE"], ["Music", "MUSIC"]]

signal movement_changed(mode: String)

var ui: GameUI
var page := "video"
var settings := ConfigFile.new()
var _tabs := {}
var _scroll: ScrollContainer
var _list: VBoxContainer
var _capture := []                       # [action id, slot, button] while waiting for a key
var _status: Label
## The character-select screen's copy (owner 2026-11-08: "graphics options and everything else also need to be
## available in the options menu you can access in the character select screen"): no EDIT UI / CHARACTER SELECT.
var pregame := false
# a display change on trial (owner 2026-11-08: "I didn't see any option in game to confirm my setting changes"):
# picked, then APPLY; kept only once KEEP is pressed, put back after CONFIRM_S seconds otherwise
const CONFIRM_S := 15.0
var _pend_res = null                     # [w, h] picked, not yet applied
var _pend_mode := ""
var _trial := {}                         # {"mode", "res"} to go back to while a change is on trial
var _trial_left := 0.0
var _trial_label: Label


func build() -> void:
	settings.load(UiArt.settings_path)
	for i in PAGE_NAMES.size():                            # (CONTROLLER opens from CONTROLS: no tab of its own)
		var b := UiArt.button(PAGE_NAMES[i], Vector2(58, 18), 9)
		b.position = Vector2(9 + i * 59.5, 23)
		b.pressed.connect(show_page.bind(PAGES[i]))
		add_child(b)
		_tabs[PAGES[i]] = b
	_scroll = ScrollContainer.new()
	_scroll.position = Vector2(12, 47)
	_scroll.size = Vector2(362, 331)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	var grab := StyleBoxFlat.new()
	grab.bg_color = UiArt.GOLD.darkened(0.15)
	grab.set_corner_radius_all(2)
	var sb := _scroll.get_v_scroll_bar()
	for k in ["grabber", "grabber_highlight", "grabber_pressed"]:
		sb.add_theme_stylebox_override(k, grab)
	sb.add_theme_stylebox_override("scroll", StyleBoxEmpty.new())
	sb.custom_minimum_size.x = 6
	add_child(_scroll)
	_list = VBoxContainer.new()
	_list.custom_minimum_size = Vector2(344, 0)
	_list.add_theme_constant_override("separation", 4)
	_scroll.add_child(_list)
	_status = UiArt.label("", 9, UiArt.GOLD_HI)
	_status.position = Vector2(12, 380)
	_status.size = Vector2(360, 12)
	_status.clip_text = true
	add_child(_status)
	var buttons := [["EDIT UI", _edit_ui], ["CHARACTER SELECT", _to_character_select], ["QUIT", _quit_game],
			["CLOSE", hide_window]]
	if pregame:
		buttons = [["QUIT", _quit_game], ["CLOSE", hide_window]]
	for i in buttons.size():
		var b := UiArt.button(buttons[i][0], Vector2(86, 20), 9)
		b.position = Vector2(11 + (i + (2 if pregame else 0)) * 91, 394)
		b.pressed.connect(buttons[i][1])
		add_child(b)
	apply_saved()
	show_page(page)


## EDIT UI (owner 2026-11-04): the options close and every movable piece of the HUD is framed to be dragged
## (game/ui/ui_editor.gd).
func _edit_ui() -> void:
	var ui := _game_ui()
	if ui == null:
		return
	hide_window()
	var ed = preload("res://game/ui/ui_editor.gd").new()
	ui.add_child(ed)
	ed.open(ui)


func _game_ui() -> GameUI:
	var n: Node = self
	while n != null and not (n is GameUI):
		n = n.get_parent()
	return n as GameUI


## Apply the saved video / audio settings (called once when the world loads).
## Only what the player actually chose: an unset window mode leaves the window as the game started it (it used to
## force "windowed" and the owner saw full screen flip to a window on entering the world).
## The window mode / resolution / frame cap are applied at start-up (BootSettings); here only the volumes, whose
## buses exist once the world's audio is set up.
func apply_saved() -> void:
	_apply_volumes()


func _current_mode() -> String:
	if DisplayServer.window_get_mode() in [DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN, DisplayServer.WINDOW_MODE_FULLSCREEN]:
		return "fullscreen"
	return "borderless" if DisplayServer.window_get_flag(DisplayServer.WINDOW_FLAG_BORDERLESS) else "windowed"


func show_window() -> void:
	super.show_window()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	show_page(page)


func hide_window() -> void:
	_capture = []
	Pad.cancel_capture()
	if not _trial.is_empty():                              # (closed with a change on trial: put back)
		_end_trial(false)
	super.hide_window()


func show_page(p: String) -> void:
	settings = UiArt.load_settings()
	if not p in PAGES:
		p = "video"
	page = p
	_capture = []
	_status.text = ""
	Pad.cancel_capture()
	for k in _tabs:
		var lit: bool = k == p or (k == "controls" and p == "controller")
		_tabs[k].add_theme_color_override("font_color", Color(1, 0.8, 0.2) if lit else UiArt.CREAM)
	for c in _list.get_children():
		c.queue_free()
	match p:
		"video": _video()
		"audio": _audio()
		"controls": _controls()
		"interface": _interface()
		"chat": _chat()
		"windows": _windows()
		"controller": _controller()
	_scroll.scroll_vertical = 0


# --- rows -----------------------------------------------------------------------------------------------------

func _row(text: String, control: Control) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	var l := UiArt.label(text, 10, UiArt.CREAM)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.custom_minimum_size.y = 20
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	row.add_child(l)
	control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(control)
	_list.add_child(row)


func _heading(text: String) -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 1)
	var l := UiArt.label(text, 12, UiArt.GOLD_HI)
	l.custom_minimum_size.y = 20
	l.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	box.add_child(l)
	var line := ColorRect.new()
	line.color = UiArt.GOLD.darkened(0.35)
	line.custom_minimum_size = Vector2(0, 1)
	box.add_child(line)
	_list.add_child(box)


func _hint(text: String) -> void:
	var h := UiArt.label(text, 9, UiArt.DIM)
	h.autowrap_mode = TextServer.AUTOWRAP_WORD
	h.custom_minimum_size = Vector2(344, 0)
	_list.add_child(h)


func _choice(items: Array, selected: int, on_pick: Callable) -> OptionButton:
	var o := OptionButton.new()
	o.custom_minimum_size = Vector2(176, 20)
	o.focus_mode = Control.FOCUS_NONE
	o.clip_text = true
	o.fit_to_longest_item = false                          # every dropdown the same width
	o.add_theme_font_override("font", UiArt.font(true))
	o.add_theme_font_size_override("font_size", 9)
	o.add_theme_color_override("font_color", UiArt.CREAM)
	o.add_theme_color_override("font_hover_color", UiArt.GOLD_HI)
	o.add_theme_stylebox_override("normal", UiArt.bar_style(0))
	o.add_theme_stylebox_override("hover", UiArt.bar_style(1))
	o.add_theme_stylebox_override("pressed", UiArt.bar_style(2))
	o.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	for it in items:
		o.add_item(String(it).to_upper())
	o.select(clampi(selected, 0, items.size() - 1))
	o.item_selected.connect(on_pick)
	UiArt.themed(o)
	var pop := o.get_popup()
	pop.add_theme_font_override("font", UiArt.font(true))
	pop.add_theme_font_size_override("font_size", 14)
	pop.add_theme_color_override("font_color", UiArt.CREAM)
	pop.add_theme_color_override("font_hover_color", UiArt.GOLD_HI)
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color(0.07, 0.065, 0.06, 0.97)
	panel.border_color = UiArt.GOLD.darkened(0.3)
	panel.set_border_width_all(1)
	panel.set_content_margin_all(4)
	pop.add_theme_stylebox_override("panel", panel)
	var hov := StyleBoxFlat.new()
	hov.bg_color = Color(0.3, 0.22, 0.1, 0.9)
	pop.add_theme_stylebox_override("hover", hov)
	return o


func _slider(value: float, lo: float, hi: float, step: float, on_change: Callable) -> HSlider:
	var s := HSlider.new()
	s.min_value = lo
	s.max_value = hi
	s.step = step
	s.value = value
	s.custom_minimum_size = Vector2(176, 20)
	s.focus_mode = Control.FOCUS_NONE
	var groove := StyleBoxFlat.new()
	groove.bg_color = Color(0.05, 0.05, 0.05)
	groove.border_color = UiArt.GOLD.darkened(0.45)
	groove.set_border_width_all(1)
	groove.content_margin_top = 2
	groove.content_margin_bottom = 2
	var fill := StyleBoxFlat.new()
	fill.bg_color = UiArt.GOLD.darkened(0.25)
	s.add_theme_stylebox_override("slider", groove)
	s.add_theme_stylebox_override("grabber_area", fill)
	s.add_theme_stylebox_override("grabber_area_highlight", fill)
	s.value_changed.connect(on_change)
	return s


func _toggle(on: bool, on_change: Callable) -> Button:
	var b := UiArt.button("ON" if on else "OFF", Vector2(70, 18), 9)
	b.toggle_mode = true
	b.button_pressed = on
	b.toggled.connect(func(v: bool):
		b.text = "ON" if v else "OFF"
		on_change.call(v))
	return b


func _plate_opt(key: String, value) -> void:
	_save("nameplates", key, value)
	HEALTH_PLATES.reload()


## Re-read the file first: other parts of the UI write it too (window positions, chat boxes, quickbars), and
## writing back an old copy erased them - the owner's windows forgot their places after a quit.
func _save(section: String, key: String, value) -> void:
	settings = UiArt.load_settings()
	settings.set_value(section, key, value)
	UiArt.save_settings(settings)


# --- pages ----------------------------------------------------------------------------------------------------

func _video() -> void:
	_heading("DISPLAY")
	var saved_mode := String(settings.get_value("display", "window_mode", _current_mode()))
	var saved_res = settings.get_value("display", "resolution", [])
	var screen := DisplayServer.screen_get_size(DisplayServer.window_get_current_screen())
	var cur := Vector2i(int(saved_res[0]), int(saved_res[1])) if saved_res is Array and saved_res.size() == 2 \
			else (screen if saved_mode != "windowed" else DisplayServer.window_get_size())
	if _pend_res is Array:
		cur = Vector2i(int(_pend_res[0]), int(_pend_res[1]))
	var names := []
	var sel := 0
	var list := RESOLUTIONS.duplicate()
	list = list.filter(func(r: Vector2i): return r.x <= screen.x and r.y <= screen.y)
	if not list.has(screen):
		list.append(screen)
	for i in list.size():
		names.append("%d X %d" % [list[i].x, list[i].y])
		if list[i] == cur:
			sel = i
	if not _trial.is_empty():                              # a change on trial: keep it or go back
		_trial_label = UiArt.label("", 10, UiArt.GOLD_HI)
		_trial_label.autowrap_mode = TextServer.AUTOWRAP_WORD
		_trial_label.custom_minimum_size = Vector2(344, 0)
		_list.add_child(_trial_label)
		_trial_tick(0.0)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 6)
		var keep := UiArt.button("KEEP", Vector2(110, 20), 9)
		keep.pressed.connect(func(): _end_trial(true))
		row.add_child(keep)
		var back := UiArt.button("REVERT", Vector2(110, 20), 9)
		back.pressed.connect(func(): _end_trial(false))
		row.add_child(back)
		_list.add_child(row)
	_row("RESOLUTION", _choice(names, sel, func(i: int):
		_pend_res = [list[i].x, list[i].y]
		_status.text = "PRESS APPLY TO TRY IT"))
	var modes := ["windowed", "fullscreen", "borderless"]
	var mode_now := _pend_mode if _pend_mode != "" else saved_mode
	_row("WINDOW MODE", _choice(["WINDOWED", "FULLSCREEN", "BORDERLESS WINDOWED"], modes.find(mode_now), func(i: int):
		_pend_mode = modes[i]
		_status.text = "PRESS APPLY TO TRY IT"))
	var apply := UiArt.button("APPLY", Vector2(176, 20), 9)
	apply.pressed.connect(_try_display)
	_row("", apply)
	_hint("BORDERLESS AND FULL SCREEN ALWAYS FILL THE SCREEN: A LOWER RESOLUTION THERE DRAWS THE WORLD AT THAT SIZE AND STRETCHES IT (FASTER), THE INTERFACE STAYING SHARP. A CHANGE IS KEPT ONLY WHEN YOU PRESS KEEP - OTHERWISE IT GOES BACK AFTER %d SECONDS." % int(CONFIRM_S))
	_row("SHOW FPS COUNTER", _toggle(bool(settings.get_value("display", "show_fps", false)), func(v: bool):
		_save("display", "show_fps", v)
		BootSettings.show_fps(v)))
	var caps := []
	for c in FPS_CAPS:
		caps.append("MONITOR REFRESH (VSYNC)" if c == 0 else ("UNLIMITED (NO VSYNC)" if c < 0 else "%d FPS" % c))
	_row("FRAME RATE CAP", _choice(caps, maxi(0, FPS_CAPS.find(int(settings.get_value("display", "fps_cap", 0)))),
			func(i: int):
		_save("display", "fps_cap", FPS_CAPS[i])
		_apply_fps(FPS_CAPS[i])))
	_quality()
	# the frame-rate governor and upscalers (Perf, owner 2026-10-10)
	_heading("PERFORMANCE")
	_hint("GPU: %s" % Perf.gpu_name.to_upper())
	var targets := []
	for t in Perf.TARGETS:
		targets.append("OFF (NO CULLING, FULL DETAIL)" if t == 0 else "%d FPS" % t)
	_row("FPS TARGET", _choice(targets, maxi(0, Perf.TARGETS.find(Perf.target_fps)), func(i: int):
		_save("performance", "target_fps", Perf.TARGETS[i])
		Perf.set_option("target_fps", Perf.TARGETS[i])))
	_hint("WITH A TARGET SET, DETAIL DROPS ONLY WHILE THE GAME IS BELOW IT (A RAID CROWD): FAR SPELL EFFECTS, FAR ANIMATION RATE, NPC SHADOWS, SOUND VOICES. IT COMES BACK WHEN THE SCENE CALMS.")
	_hint("OFF: NOTHING IS CULLED OR SIMPLIFIED - FOR HARDWARE THAT CAN BRUTE FORCE A FULL RAID.")


# --- VIDEO: render quality (Graphics) ------------------------------------------------------------------------

var _preset_buttons := {}


func _quality() -> void:
	_heading("QUALITY PRESET")
	var rec: Array = Graphics.recommended()
	_hint("RECOMMENDED FOR THIS PC: %s  (%s)" % [String(rec[0]).to_upper(), String(rec[1]).to_upper()])
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	_preset_buttons = {}
	for n in Graphics.PRESET_NAMES:
		var b := UiArt.button(n.to_upper(), Vector2(65, 20), 9)
		b.pressed.connect(func():
			Graphics.use_preset(n)
			_status.text = "%s QUALITY" % n.to_upper()
			show_page("video"))
		row.add_child(b)
		_preset_buttons[n] = b
	_list.add_child(row)
	var row2 := HBoxContainer.new()
	row2.add_theme_constant_override("separation", 6)
	var use_rec := UiArt.button("USE RECOMMENDED", Vector2(168, 20), 9)
	use_rec.pressed.connect(func():
		Graphics.use_preset(String(rec[0]))
		_status.text = "%s QUALITY (RECOMMENDED)" % String(rec[0]).to_upper()
		show_page("video"))
	row2.add_child(use_rec)
	var reset := UiArt.button("RESET TO DEFAULTS", Vector2(168, 20), 9)
	reset.pressed.connect(func():
		Graphics.use_preset("defaults")
		_status.text = "GRAPHICS BACK TO THE DEFAULTS"
		show_page("video"))
	row2.add_child(reset)
	_list.add_child(row2)
	_hint("HIGH IS THE GAME'S DEFAULT. ANY CHANGE BELOW MAKES IT CUSTOM.")
	_mark_preset()

	_heading("VIEW DISTANCE")
	_gfx_slider("VIEW DISTANCE", "view_distance", 0.5, Graphics.VIEW_MAX, 0.1, func(v: float): return "%.1fX" % v)
	_hint("STRETCHES EACH ZONE'S FOG, HOW FAR OBJECTS ARE DRAWN AND HOW MANY ZONES AROUND YOU ARE LOADED. 1X IS THE ORIGINAL CLIENT'S LOOK; HIGH VALUES NEED MORE VIDEO MEMORY. DUNGEON FOG IS NEVER CHANGED.")

	_heading("SHADOWS")
	_gfx_toggle("SUN SHADOWS", "shadows")
	_gfx_choice("SHADOW DETAIL", "shadow_size", [1024, 2048, 4096, 8192],
			["LOW (1024)", "MEDIUM (2048)", "HIGH (4096)", "ULTRA (8192)"])
	_gfx_slider("SHADOW DISTANCE", "shadow_distance", 60.0, 600.0, 10.0, func(v: float): return "%d M" % int(v))
	_gfx_choice("SHADOW SOFTNESS", "shadow_filter", [0, 1, 2, 3, 4, 5],
			["0 - HARD", "1 - VERY LOW", "2 - LOW", "3 - MEDIUM", "4 - HIGH", "5 - ULTRA"])

	_heading("REMASTERED LIGHTING")
	_gfx_toggle("REMASTERED LIGHTING", "remastered")
	_gfx_toggle("REAL-TIME BOUNCE LIGHT (SDFGI)", "gi")
	_hint("VOLUMETRIC FOG WITH SUN SHAFTS AND GLOWING TORCHES, MORNING AND NIGHT MIST, A NEWER TONE CURVE, BLOOM, INDIRECT LIGHT, EYES THAT ADJUST TO THE DARK AND A COLOUR MOOD FOR EACH REALM AND HOUR. OFF IS THE CLASSIC LOOK. WHILE ON, IT TURNS BLOOM AND INDIRECT LIGHT ON TOO, FIRES FLICKER AND CAST SHADOWS, YOUR TORCH BECOMES A BELT LANTERN AND SPELLS AND GLOWING WEAPONS LIGHT THEIR SURROUNDINGS. BOUNCE LIGHT LETS SUNLIT GROUND AND WALLS LIGHT THE SHADE BESIDE THEM (REMASTERED ONLY): IT REPLACES EACH ZONE'S OWN AMBIENT TINT, SO NIGHTS GO MUCH DARKER - OFF BY DEFAULT, TRY IT.")

	# (owner 2026-11-08: "an old 'lighting' section ... with SSAO and SSIL in it. Do these conflict with our remastered
	# lighting?" - remastered turns its own indirect light and bloom on, so those two only show for the classic look)
	_heading("LIGHTING")
	_gfx_choice("AMBIENT OCCLUSION (SSAO)", "ssao", [-1, 0, 1, 2, 3, 4],
			["OFF", "VERY LOW", "LOW", "MEDIUM", "HIGH", "ULTRA"])
	if bool(Graphics.value("remastered")):
		_hint("AMBIENT OCCLUSION DARKENS CREVICES AND CONTACT SHADOWS. REMASTERED LIGHTING BRINGS ITS OWN INDIRECT LIGHT AND BLOOM.")
	else:
		_gfx_toggle("INDIRECT LIGHT (SSIL)", "ssil")
		_gfx_toggle("BLOOM", "glow")
		_hint("AMBIENT OCCLUSION DARKENS CREVICES AND CONTACT SHADOWS; INDIRECT LIGHT BOUNCES COLOUR OFF NEARBY SURFACES; BLOOM MAKES SPELLS AND LIGHTS GLOW. THE LAST TWO ARE NEW TO THE LOOK - OFF BY DEFAULT.")

	_heading("ANTI-ALIASING")
	_gfx_choice("MSAA", "msaa", [0, 2, 4, 8], ["OFF", "2X", "4X", "8X"])
	_gfx_choice("SCREEN-SPACE AA", "screen_aa", [0, 1, 2], ["OFF", "FXAA", "SMAA"])
	_gfx_toggle("TEMPORAL AA (TAA)", "taa")
	_gfx_choice("RENDER SCALE", "render_scale", [1.0, 1.25, 1.5, 1.75, 2.0],
			["100% (NATIVE)", "125%", "150%", "175%", "200%"])
	_hint("RENDER SCALE ABOVE 100% IS SUPERSAMPLING: SHARPER EDGES FOR A LOT OF GRAPHICS CARD TIME.")

	_heading("UPSCALING")
	var ups: Array = Graphics.UPSCALERS.keys()
	_gfx_choice("UPSCALER", "upscaler", ups, ups.map(func(k): return String(Graphics.UPSCALERS[k][2])))
	_hint("DRAWS THE WORLD SMALLER AND SCALES IT UP TO THE SCREEN (AMD FSR - ANY GRAPHICS CARD): A LOT MORE FRAMES FOR A LITTLE SOFTNESS. FSR 2 IS THE SHARPER AND DOES ITS OWN ANTI-ALIASING (MSAA AND TAA ARE OFF WITH IT); FSR 1 IS CHEAPER AND SOFTER. RENDER SCALE IS IGNORED WHILE AN UPSCALER IS ON.")

	_heading("TEXTURES")
	_gfx_choice("ANISOTROPIC FILTERING", "aniso", [1, 2, 4, 8, 16], ["OFF", "2X", "4X", "8X", "16X"])
	_hint("KEEPS GROUND AND WALL TEXTURES SHARP AT LOW ANGLES.")
	_gfx_toggle("COMPRESSED TEXTURES", "compressed_textures")
	_hint("KEEPS THE WORLD'S TEXTURES IN THE GRAPHICS CARD'S OWN COMPRESSED FORMAT: A QUARTER OF THE VIDEO MEMORY OR LESS AND FASTER LOADING, A LITTLE SOFTER UP CLOSE. EACH TEXTURE IS COMPRESSED THE FIRST TIME IT IS SEEN (THE FIRST VISIT TO A ZONE IS SLOWER), THEN KEPT. TAKES EFFECT AS ZONES LOAD - CHANGE ZONE OR RESTART TO SEE IT EVERYWHERE.")

	_heading("GRASS")
	_gfx_slider("GRASS DISTANCE", "grass_distance", 30.0, 200.0, 5.0, func(v: float): return "%d M" % int(v))
	_gfx_slider("GRASS DENSITY", "grass_density", 0.0, 1.0, 0.05, func(v: float): return "%d%%" % roundi(v * 100.0))


## The preset buttons: the one the settings are now in gold (none: custom).
func _mark_preset() -> void:
	var cur := Graphics.current_preset()
	for n in _preset_buttons:
		var b: Button = _preset_buttons[n]
		if is_instance_valid(b):
			b.add_theme_color_override("font_color", UiArt.GOLD_HI if n == cur else UiArt.CREAM)


func _gfx_set(key: String, v: Variant) -> void:
	Graphics.set_value(key, v)
	_mark_preset()
	if key == "remastered":                                # (the lighting rows it governs: shown again, in place)
		var at := _scroll.scroll_vertical
		show_page("video")
		await get_tree().process_frame
		_scroll.scroll_vertical = at
	_status.text = "CUSTOM QUALITY" if Graphics.current_preset() == "" else "%s QUALITY" % Graphics.current_preset().to_upper()


func _gfx_toggle(caption: String, key: String) -> void:
	_row(caption, _toggle(bool(Graphics.value(key)), func(v: bool): _gfx_set(key, v)))


func _gfx_choice(caption: String, key: String, vals: Array, names: Array) -> void:
	var sel := 0
	for i in vals.size():
		if Graphics._same(vals[i], Graphics.value(key)):
			sel = i
	_row(caption, _choice(names, sel, func(i: int): _gfx_set(key, vals[i])))


## A slider with its value in the caption; applied once it stops moving (a shadow map or the grass rebuilt on every
## step of a drag would stutter).
func _gfx_slider(caption: String, key: String, lo: float, hi: float, step: float, fmt: Callable) -> void:
	var start := clampf(float(Graphics.value(key)), lo, hi)
	var s := _slider(start, lo, hi, step, func(_v: float): pass)
	_row(caption, s)
	var row := s.get_parent() as HBoxContainer
	var label := row.get_child(0) as Label
	label.text = "%s  %s" % [caption, fmt.call(start)]
	var ticket := [0]
	s.value_changed.connect(func(v: float):
		label.text = "%s  %s" % [caption, fmt.call(v)]
		ticket[0] += 1
		var mine: int = ticket[0]
		await get_tree().create_timer(0.35).timeout
		if mine == ticket[0] and is_instance_valid(s):
			_gfx_set(key, v))


func _audio() -> void:
	_heading("VOLUME")
	for v in VOLUMES:
		_row(v[1], _slider(_volume(String(v[0])), 0, 100, 1, func(x: float):
			_save("audio", String(v[0]).to_lower(), x)
			_apply_volumes()))


func _controls() -> void:
	var pad := UiArt.button("CONTROLLER SETTINGS AND BUTTONS", Vector2(344, 20), 9)
	pad.pressed.connect(show_page.bind("controller"))
	_list.add_child(pad)
	_heading("MOVEMENT")
	var styles := ["modern", "classic"]
	_row("MOVEMENT STYLE", _choice(["MODERN (FULL-SPEED STRAFE)", "CLASSIC DAOC"],
			styles.find(String(settings.get_value("player", "movement", "modern"))), func(i: int):
		_save("player", "movement", styles[i])
		movement_changed.emit(styles[i])))
	_row("MOUSE SENSITIVITY", _slider(float(settings.get_value("player", "mouse_sensitivity", 1.0)), 0.2, 3.0, 0.05,
			func(x: float):
		_save("player", "mouse_sensitivity", x)
		if ui and ui.player:
			ui.player.set("mouse_sensitivity", x)))
	_row("INVERT MOUSE", _toggle(bool(settings.get_value("player", "invert_mouse", false)),
			func(v: bool):
		_save("player", "invert_mouse", v)
		if ui and ui.player:
			ui.player.set("invert_mouse", v)))
	# owner 2026-11-03: "the option to make the Alt keypress a toggle instead of a hold to use the cursor"
	var modes := ["hold", "toggle"]
	_row("ACTION COMBAT CURSOR KEY", _choice(["HOLD (CURSOR WHILE HELD)", "TOGGLE (PRESS FOR CURSOR, PRESS AGAIN TO HIDE)"],
			1 if bool(settings.get_value("player", "ac_cursor_toggle", false)) else 0, func(i: int):
		_save("player", "ac_cursor_toggle", modes[i] == "toggle")
		preload("res://game/combat/action_combat.gd").cursor_toggle = modes[i] == "toggle"))
	# owner 2026-11-09: the weapon stays out after a kill unless this is on
	_row("ACTION COMBAT: SHEATHE WEAPON AFTER A KILL", _toggle(bool(settings.get_value("player", "ac_sheathe_after_kill", false)),
			func(v: bool):
		_save("player", "ac_sheathe_after_kill", v)
		preload("res://game/combat/action_combat.gd").sheathe_after_kill = v))
	_heading("KEY CONFIGURATION")
	# shared by every character unless this one has its own (the WoW-style override, off by default)
	_row("CHARACTER-SPECIFIC KEY BINDINGS", _toggle(Keybinds.character_specific, func(v: bool):
		Keybinds.set_character_specific(v)
		show_page.call_deferred("controls")
		_status.text = "THIS CHARACTER NOW HAS ITS OWN KEYS" if v else "THIS CHARACTER USES THE SHARED KEYS"))
	var presets := HBoxContainer.new()
	presets.add_theme_constant_override("separation", 6)
	for p in [["default", "DEFAULT"], ["rpg", "RPG"], ["fps", "FPS"], ["mmo", "MMO"]]:
		var b := UiArt.button(p[1], Vector2(82, 18), 9)
		b.pressed.connect(func():
			Keybinds.use_preset(p[0])
			show_page("controls")
			_status.text = "%s KEYS LOADED" % p[1])
		presets.add_child(b)
	_list.add_child(presets)
	_hint("CLICK A KEY TO CHANGE IT, THEN PRESS A KEY OR MOUSE BUTTON (MOUSE 4 / 5 AND THE WHEEL WORK). ESC CANCELS, RIGHT-CLICK CLEARS.")
	var cats: Array = Keybinds.categories.duplicate()
	if not cats.has("Quickbars"):
		cats.append("Quickbars")
	for cat in cats:
		var acts: Array = Keybinds.actions.filter(func(a): return String(a.category) == String(cat))
		if acts.is_empty():
			continue
		_heading(String(cat))
		for a in acts:
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 4)
			var l := UiArt.label(String(a.label), 9, UiArt.CREAM)
			l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			l.custom_minimum_size.y = 18
			l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			l.clip_text = true
			row.add_child(l)
			var keys: Array = Keybinds.bindings.get(a.id, [])
			for slot in Keybinds.SLOTS:
				var b := UiArt.button(String(keys[slot]) if slot < keys.size() and keys[slot] != "" else "-", Vector2(92, 18), 9)
				b.pressed.connect(_start_capture.bind(String(a.id), slot, b))
				b.gui_input.connect(func(e: InputEvent):
					if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_RIGHT and _capture.is_empty():
						Keybinds.bind(String(a.id), slot, "")
						b.text = "-"
						b.accept_event())
				row.add_child(b)
			_list.add_child(row)


func _interface() -> void:
	_heading("INTERFACE")
	# the modern HUD (owner 2026-11-02: a GW2-style layout with a DAoC feel) or the 1.65 windows
	var style := String(settings.get_value("interface", "style", "classic"))
	_row("STYLE", _choice(["Classic", "Modern"], 1 if style == "modern" else 0, func(i: int):
		if ui:
			ui.set_style("modern" if i == 1 else "classic")))
	_hint("CLASSIC: THE 1.65 WINDOWS. MODERN: THE HEALTH ORB WITH THE ENDURANCE AND POWER ARCS, THE PARTY TOP LEFT, THE EVENTS AND QUESTS TOP RIGHT, THE MINIMAP BOTTOM RIGHT - OVER THE SAME SHEETS AND CHAT.")
	# the scale applies when the slider is let go (a wheel or key step at once): applied while dragging, the whole
	# interface - this window and its slider too - grew and shrank under the mouse (a player report 2026-10-17)
	var dragging := [false]
	var scale_slider := _slider(float(settings.get_value("interface", "ui_scale", 1.0)), 0.6, 1.6, 0.05, func(x: float):
		_save("interface", "ui_scale", x)
		if ui and not dragging[0]:
			ui.set_ui_scale(x))
	scale_slider.drag_started.connect(func(): dragging[0] = true)
	scale_slider.drag_ended.connect(func(_changed: bool):
		dragging[0] = false
		if ui and is_instance_valid(scale_slider):
			ui.set_ui_scale(scale_slider.value))
	_row("UI SCALE", scale_slider)
	_hint("THE INTERFACE KEEPS ITS SIZE ON SCREEN AT ANY RESOLUTION; UI SCALE MAKES ALL OF IT BIGGER OR SMALLER.")
	# WoW-style nameplates over monsters (HealthPlates; owner 2026-11-13)
	_heading("NAMEPLATES")
	_row("SHOW", _choice(["Off", "Target only", "Target, hurt or fighting", "All enemies near"],
			int(HEALTH_PLATES.opt("show")), func(i: int): _plate_opt("show", i)))
	_hint("A SLIM HEALTH BAR OVER THE HEAD WITH THE NAME, THE LEVEL IN ITS CON COLOUR AND A CAST BAR - RED HOSTILE, YELLOW NEUTRAL, GREEN FRIENDLY. YOUR TARGET'S IS BIGGER WITH A WHITE FRAME.")
	_row("FRIENDLY TOO", _toggle(bool(HEALTH_PLATES.opt("friendly")), func(on: bool): _plate_opt("friendly", on)))
	_row("HEALTH NUMBER", _choice(["None", "Percent"], int(HEALTH_PLATES.opt("health_text")), func(i: int): _plate_opt("health_text", i)))
	_row("SIZE", _slider(float(HEALTH_PLATES.opt("scale")), 0.7, 1.6, 0.05, func(x: float): _plate_opt("scale", x)))
	_row("STACK", _toggle(bool(HEALTH_PLATES.opt("stack")), func(on: bool): _plate_opt("stack", on)))
	_row("CAST BARS", _toggle(bool(HEALTH_PLATES.opt("cast_bar")), func(on: bool): _plate_opt("cast_bar", on)))
	_hint("FRIENDLY TOO: YOUR GROUP, YOUR REALM'S BOTS AND GUARDS GET PLATES BY THE SAME RULE (HANDY FOR HEALERS). STACK: PLATES MOVE APART INSTEAD OF COVERING EACH OTHER.")
	_row("TARGET ON THE ORB", _toggle(bool(settings.get_value("interface", "orb_target", true)), func(on: bool):
		_save("interface", "orb_target", on)
		preload("res://game/ui/modern_hud.gd").Orb.reload()
		if ui:
			for o in ui.find_children("*", "", true, false):
				if o is CanvasItem and o.get_script() != null and o.has_method("show_target"):
					(o as CanvasItem).queue_redraw()))
	_hint("THE MODERN INTERFACE'S TARGET PLATE ABOVE THE HEALTH ORB. OFF: THE NAMEPLATE OVER YOUR TARGET IS ENOUGH.")
	_heading("LOOT")
	_row("AUTO LOOT", _toggle(Loot.autoloot(), func(on: bool): Loot.set_autoloot(on)))
	_hint("ON: COINS AND ITEMS FROM YOUR KILLS GO STRAIGHT INTO YOUR BACKPACK (NOT IN 1.65 - A QUALITY OF LIFE OPTION). OFF: THEY DROP AT THE MONSTER'S FEET FOR YOU TO PICK UP, AS IN THE ORIGINAL.")
	# the bots' names and map dots (bot plan phase 3, owner 2026-10-10: all on by default, mix and match)
	_heading("BOTS")
	_row("COMPANION NAMES", _toggle(BotView.option("names_companions"), func(on: bool): _save("bots", "names_companions", on)))
	_row("GAMEBOT NAMES", _toggle(BotView.option("names_gamebots"), func(on: bool): _save("bots", "names_gamebots", on)))
	_hint("SHOW OR HIDE THE NAMES OVER YOUR COMPANIONS AND OVER THE GAMEBOTS, EACH ON ITS OWN. A BOT YOU CLICK ALWAYS SHOWS ITS NAME.")
	_row("REALM BOTS ON MAP", _toggle(BotView.option("map_dots"), func(on: bool): _save("bots", "map_dots", on)))
	_hint("YOUR REALM'S GAMEBOTS AND COMPANIONS AS GREEN DOTS ON YOUR MAP (ALSO IN DUNGEONS). ENEMY BOTS NEVER SHOW.")
	_hint("THE BOT ROSTER AND THE SERVER SETTINGS (XP RATES, BOT GOALS AND THE REST) ARE IN THE OFFLINE DAOC REBUILT LAUNCHER.")


## CHAT: which message types the chat block's two boxes show (top = chat, bottom = system), one ON / OFF per box.
func _chat() -> void:
	_heading("CHAT BOXES")
	_hint("TWO SEPARATE BOXES: COMBAT (ON TOP) AND CHAT (BELOW, WITH THE TYPING LINE). EACH MOVES AND RESIZES ON ITS OWN. CHOOSE WHAT EACH BOX SHOWS.")
	if ui == null or ui.chat == null or ui.chat_combat == null:
		return
	var head := HBoxContainer.new()
	var hl := UiArt.label("MESSAGES", 9, UiArt.GOLD_HI)
	hl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hl)
	for t in ["COMBAT", "CHAT"]:
		var l := UiArt.label(t, 9, UiArt.GOLD_HI)
		l.custom_minimum_size = Vector2(74, 16)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		head.add_child(l)
	_list.add_child(head)
	for spec in ChatWindow.TYPES:
		var kind: String = spec[0]
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 4)
		var l := UiArt.label(spec[1], 9, UiArt.CREAM)
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		l.custom_minimum_size.y = 18
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		row.add_child(l)
		for box in [ui.chat_combat, ui.chat]:
			var cw: ChatWindow = box
			row.add_child(_toggle(kind in cw.types, func(v: bool):
				var lst: Array = cw.types.duplicate()
				if v and not lst.has(kind):
					lst.append(kind)
				elif not v:
					lst.erase(kind)
				cw.set_types(lst)))
		_list.add_child(row)


## WINDOWS (owner 2026-10-09): one button per window that puts it back where it was before it was closed; RESET
## puts every window back in its default place.
func _windows() -> void:
	_heading("WINDOWS")
	_hint("OPEN OR CLOSE ANY WINDOW (LIT = OPEN). A WINDOW REOPENS WHERE IT WAS. THE PET WINDOW ALSO OPENS BY ITSELF WHEN YOU SUMMON A PET.")
	if ui == null:
		return
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 5)
	for spec in GameUI.RESTORABLE:
		var id: String = spec[0]
		var b := UiArt.button(spec[1], Vector2(168, 20), 10)
		var open: bool = ui.windows.has(id) and ui.windows[id].visible
		if open:
			b.add_theme_color_override("font_color", UiArt.GOLD_HI)
		if id == "minipet" and PlayerData.pet.is_empty():
			b.disabled = true
			b.tooltip_text = "YOU HAVE NO PET"
		if id == "raid" and not ui.raid_active:          # opens with /raid 40 or /raid 80 (level 50)
			b.disabled = true
			b.tooltip_text = "NO RAID - LEVEL 50: /RAID 40 OR /RAID 80"
		b.pressed.connect(func():
			if ui.windows.has(id) and ui.windows[id].visible:
				ui.windows[id].hide_window()
				_status.text = "%s CLOSED" % String(spec[1])
			else:
				ui.restore_window(id)
				_status.text = "%s OPENED" % String(spec[1])
			show_page("windows"))
		grid.add_child(b)
	var pb := UiArt.button("PET BUFFS", Vector2(168, 20), 10)          # the strip under the pet window
	var pb_on: bool = ui._pet_buffs != null and ui._pet_buffs.visible
	if pb_on:
		pb.add_theme_color_override("font_color", UiArt.GOLD_HI)
	pb.pressed.connect(func():
		ui.set_pet_buffs(not pb_on)
		_status.text = "PET BUFFS %s" % ("OFF" if pb_on else "ON")
		show_page("windows"))
	grid.add_child(pb)
	_list.add_child(grid)
	var gap := Control.new()
	gap.custom_minimum_size.y = 8
	_list.add_child(gap)
	var reset := UiArt.button("RESET ALL WINDOWS", Vector2(342, 20), 10)
	reset.pressed.connect(func():
		ui.reset_layout()
		_status.text = "EVERY WINDOW IS BACK IN ITS DEFAULT PLACE"
		show_page("windows"))
	_list.add_child(reset)


# --- the controller (owner 2026-11-10: "controller customization ... holding a button be a selectable input") -----

const PAD_GROUPS := [["COMBAT", ["attack", "defend", "dodge", "jump", "sprint_hold", "sprint_toggle", "sheathe",
		"weapon_cycle", "interact", "lock_on"]], ["STYLES", ["style_auto", "style_reactive", "style_position", "style_chain"]],
		["TARGETING", ["target_enemy", "target_friend"]], ["MOVING ABOUT", ["run_lock", "pull", "sit", "torch"]],
		["CAMERA", ["zoom_in", "zoom_out"]],
		["WINDOWS", ["hero", "bags", "map", "journal", "styles_window", "menu_wheel", "escape"]]]


func _controller() -> void:
	var back := UiArt.button("< KEYBOARD AND MOUSE", Vector2(344, 20), 9)
	back.pressed.connect(show_page.bind("controls"))
	_list.add_child(back)
	_heading("CONTROLLER")
	_row("LOOK SPEED", _slider(Pad.look_speed, 0.3, 2.5, 0.05, func(x: float):
		Pad.look_speed = x
		_save("pad", "look_speed", x)))
	_row("INVERT LOOK (UP / DOWN)", _toggle(Pad.invert_look, func(v: bool):
		Pad.invert_look = v
		_save("pad", "invert_look", v)))
	_row("HOLD TIME (A HELD BUTTON)", _slider(float(Pad.hold_ms), 150.0, 700.0, 10.0, func(x: float):
		Pad.hold_ms = int(x)
		_save("pad", "hold_ms", int(x))))
	_heading("CONTROLLER BUTTONS")
	var reset := UiArt.button("DEFAULT BUTTONS", Vector2(344, 18), 9)
	reset.pressed.connect(func():
		Pad.reset_bindings()
		show_page("controller")
		_status.text = "CONTROLLER BUTTONS BACK TO THE DEFAULTS")
	_list.add_child(reset)
	_hint("CLICK A BOX, THEN PRESS ON THE CONTROLLER. HOLD LB / RB (OR BOTH) FIRST FOR A COMBO; KEEP THE BUTTON DOWN FOR A HOLD. MENU OR ESC CANCELS, RIGHT-CLICK (X) CLEARS. A BUTTON DOES ONE THING: BINDING IT HERE TAKES IT FROM WHATEVER HAD IT.")
	var groups: Array = PAD_GROUPS.duplicate()
	for q in 3:
		var ids := []
		for slot in 10:
			ids.append("qb%d_%d" % [q + 1, slot + 1])
		groups.append(["QUICKBAR %d" % (q + 1), ids])
	for g in groups:
		_heading(String(g[0]))
		if String(g[0]) == "CAMERA":
			_hint("ALSO, ALWAYS: HOLD LB + RB AND PUSH THE RIGHT STICK UP TO ZOOM IN, DOWN TO ZOOM OUT.")
		for id in g[1]:
			_pad_row(String(id))


func _pad_row(id: String) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	var l := UiArt.label(String(Pad.action_info(id)[1]).to_upper(), 9, UiArt.CREAM)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.custom_minimum_size.y = 18
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.clip_text = true
	row.add_child(l)
	var have: Array = Pad.inputs_of(id)
	for slot in 2:
		var input := String(have[slot]) if slot < have.size() else ""
		var b := UiArt.button(Pad.describe(input) if input != "" else "-", Vector2(104, 18), 8)
		b.clip_text = true
		b.pressed.connect(func():
			b.text = "PRESS..."
			_status.text = "PRESS ON THE CONTROLLER FOR %s" % String(Pad.action_info(id)[1]).to_upper()
			Pad.capture(func(got: String):
				if got == "menu":
					_status.text = "CANCELLED"
					b.text = Pad.describe(input) if input != "" else "-"
					return
				if input != "" and input != got:
					Pad.bind(input, "")
				var stolen := Pad.bind(got, id)
				var msg := "%s = %s%s" % [String(Pad.action_info(id)[1]).to_upper(), Pad.describe(got),
						("   (TAKEN FROM %s)" % String(Pad.action_info(stolen)[1]).to_upper()) if stolen != "" else ""]
				_reshow_page.call_deferred("controller", _scroll.scroll_vertical, msg)))
		b.gui_input.connect(func(e: InputEvent):
			if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_RIGHT and input != "":
				Pad.bind(input, "")
				b.text = "-"
				b.accept_event())
		row.add_child(b)
	_list.add_child(row)


func _reshow_page(p: String, at: int, message: String) -> void:
	show_page(p)
	_status.text = message
	await get_tree().process_frame
	if is_instance_valid(_scroll) and page == p:
		_scroll.scroll_vertical = at


# --- key capture ----------------------------------------------------------------------------------------------

func _start_capture(id: String, slot: int, b: Button) -> void:
	if not _capture.is_empty():
		_capture[2].text = _key_text(_capture[0], _capture[1])
	_capture = [id, slot, b]
	b.text = "PRESS A KEY"
	_status.text = "PRESS A KEY FOR %s" % Keybinds.label_of(id).to_upper()


func _key_text(id: String, slot: int) -> String:
	var keys: Array = Keybinds.bindings.get(id, [])
	return String(keys[slot]) if slot < keys.size() and keys[slot] != "" else "-"


func _input(event: InputEvent) -> void:
	if Pad.capturing() and visible and event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		Pad.cancel_capture()
		show_page("controller")
		_status.text = "CANCELLED"
		get_viewport().set_input_as_handled()
		return
	if _capture.is_empty() or not visible:
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		_capture[2].text = _key_text(_capture[0], _capture[1])
		_capture = []
		_status.text = ""
		get_viewport().set_input_as_handled()
		return
	var pressed: bool = (event is InputEventKey and event.pressed and not event.echo) or \
			(event is InputEventMouseButton and event.pressed)
	if not pressed:
		return
	var binding := Keybinds.describe(event)
	if binding == "":
		return
	get_viewport().set_input_as_handled()
	var id: String = _capture[0]
	var slot: int = _capture[1]
	_capture = []
	var stolen := Keybinds.bind(id, slot, binding)
	_status.text = "%s = %s%s" % [Keybinds.label_of(id).to_upper(), binding.to_upper(),
			("   (TAKEN FROM %s)" % stolen.to_upper()) if stolen != "" else ""]
	_reshow_controls.call_deferred(_scroll.scroll_vertical, _status.text)


## The controls page drawn again with the new keys, where you were in it and with the binding's message kept (a player
## report 2026-10-17: every key bound jumped the list back to the top, and the rebuild wiped "TAKEN FROM ...").
func _reshow_controls(at: int, message: String) -> void:
	show_page("controls")
	_status.text = message
	await get_tree().process_frame                         # the rows laid out: the scroll range is back
	if is_instance_valid(_scroll) and page == "controls":
		_scroll.scroll_vertical = at


func capturing() -> bool:
	return not _capture.is_empty() or Pad.capturing()


# --- apply ----------------------------------------------------------------------------------------------------

## APPLY: the picked resolution / window mode tried, the old one kept to go back to.
func _try_display() -> void:
	if _pend_res == null and _pend_mode == "":
		_status.text = "NOTHING CHANGED"
		return
	var old_mode := String(settings.get_value("display", "window_mode", _current_mode()))
	var old_res = settings.get_value("display", "resolution", [])
	if not (old_res is Array and old_res.size() == 2):
		var ws := DisplayServer.window_get_size()
		old_res = [ws.x, ws.y]
	if _trial.is_empty():
		_trial = {"mode": old_mode, "res": old_res}
	var mode := _pend_mode if _pend_mode != "" else old_mode
	var res = _pend_res if _pend_res is Array else old_res
	_trial["new_mode"] = mode
	_trial["new_res"] = res
	_pend_res = null
	_pend_mode = ""
	_apply_window(mode, res)
	_trial_left = CONFIRM_S
	show_page("video")


func _trial_tick(delta: float) -> void:
	_trial_left -= delta
	if is_instance_valid(_trial_label):
		_trial_label.text = "KEEP THESE DISPLAY SETTINGS? GOING BACK IN %d SECONDS." % ceili(maxf(_trial_left, 0.0))
	if _trial_left <= 0.0:
		_end_trial(false)


func _process(delta: float) -> void:
	if not _trial.is_empty():
		_trial_tick(delta)


## KEEP: saved (the game starts with it). REVERT / time up / closed: the old one put back.
func _end_trial(keep: bool) -> void:
	if _trial.is_empty():
		return
	var t := _trial
	_trial = {}
	if keep:
		_save("display", "window_mode", t.new_mode)
		_save("display", "resolution", t.new_res)
		_save("display", "screen", DisplayServer.window_get_current_screen())
		_status.text = "DISPLAY SETTINGS KEPT"
	else:
		_apply_window(String(t.mode), t.res)
		_status.text = "DISPLAY SETTINGS PUT BACK"
	if visible and page == "video":
		show_page.call_deferred("video")


func _apply_fps(cap: int) -> void:
	BootSettings.apply_fps(cap)


func _apply_window(mode: String, res) -> void:
	BootSettings.apply_display(mode, res)                 # one place for the window rules (game/ui/boot_settings.gd)


## A bus's saved volume; sound effects start at the old shared "effects + ambience" level until set on their own.
func _volume(bus: String) -> float:
	var fallback = settings.get_value("audio", "ambient", 100) if bus == "Effects" else 100
	return float(settings.get_value("audio", bus.to_lower(), fallback))


func _apply_volumes() -> void:
	for v in VOLUMES:
		var i := AudioServer.get_bus_index(v[0])
		if i >= 0:
			var x := _volume(String(v[0]))
			AudioServer.set_bus_volume_db(i, linear_to_db(maxf(x / 100.0, 0.0001)))


func _to_character_select() -> void:
	if Server.active:                                      # the server's /quit: saved, then its Quit brings the
		hide_window()                                      # character screen (Server.quit_world)
		Server.quit_world(false)
		return
	PlayerData.save_character()
	get_tree().change_scene_to_file("res://game/pregame.tscn")


func _quit_game() -> void:
	if Server.active:                                      # saved by the server first, then out of the game
		hide_window()
		Server.quit_world(true)
		return
	get_tree().quit()
