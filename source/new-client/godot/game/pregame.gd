class_name Pregame
extends Node3D
## Realm select, character select, creation and customize: the old client's pregame screens 1:1
## (frames, medallions, bars, the three 3D realm backdrops from app/pregame) with the "new old" readability pass
## (Minion Pro bold, ALL CAPS, larger text, gold on black). 1.65 creation (owner 2026-10-09): race + BASE class from
## the client's charman/summary.txt (greyed where the client says "not available"); the advanced class comes from a
## trainer at level 5. No "Adjust Attributes" step (stats fill in like the old client). Customize zooms to the face.
## Debug: --pregame-shot=<folder> walks every screen and saves a png of each.

const PRE := "res://content/pregame"
const UI := "res://content/ui"
const GOLD := Color(0.86, 0.71, 0.38)
const GOLD_HI := Color(1.0, 0.85, 0.45)
const CREAM := Color(0.93, 0.89, 0.78)
const DIM := Color(0.55, 0.52, 0.47)
const ERROR := Color(1.0, 0.45, 0.35)
# The client's pregame camera (game.dll 0x599a0e init, 0x59ed4e select setup, 0x59ea59 update; angles in units of
# pi): yaw 1.5pi + 215 deg, pitch 0.031pi - 5 deg, distance 200 units to a target 44 units above the scene origin
# (the scene is shifted by (140, 0, 198.6) so the origin is its floor), camera = target + (-40, 40, 0) +
# R(-distance, 0, 0). Converted to Godot below. Fitted to the owner's screenshots of the real client: +14 deg yaw
# and the character 0.9 m to camera-right of the scene origin (Hibernia select and Albion create both line up).
const CAM_POS := Vector3(-0.727, -3.81, -4.28)
const CAM_LOOK := Vector3(-4.5, -3.865, -1.0)
const CAM_FOV := 40.0
const REALM_LIGHT := {"hib": [Color(1.0, 0.94, 0.8), 1.0], "alb": [Color(1.0, 1.0, 1.0), 1.0], "mid": [Color(1, 1, 1), 1.0]}
const SPOT := Vector3(-4.09, -4.98, -0.679)        # where the character stands
const REALM_NAMES := {"alb": "ALBION", "hib": "HIBERNIA", "mid": "MIDGARD"}
const REALM_ORDER := ["alb", "hib", "mid"]        # realm_selection.tga: red, green, blue panels
# race, charman summary code, figure prefix, names.dat section
const RACES := CharacterFactory.RACES               # the races and base classes live in CharacterFactory
const BASES := CharacterFactory.BASES
const BASE_BUTTON := {"FIGH": "FIGHTER", "ACOL": "ACOLYTE", "MAGE": "MAGE", "ELEM": "ELEMENTALIST", "ROGU": "ROGUE",
		"ARAW": "DISCIPLE", "WARR": "VIKING", "SPIR": "SEER", "MYST": "MYSTIC", "NROG": "ROGUE", "ARMS": "WAY OF ARMS",
		"NATU": "WAY OF NATURE", "MAGI": "WAY OF MAGIC", "STEA": "WAY OF STEALTH", "GROV": "WAY OF THE GROVE"}
const BASE_CLASS := CharacterFactory.BASE_CLASS
# the server's classes -> the base class they come from (charman/summary.txt's race-base codes)
const SERVER_BASE := {"Armsman": "FIGH", "Mercenary": "FIGH", "Paladin": "FIGH", "Reaver": "FIGH", "Cleric": "ACOL",
		"Friar": "ACOL", "Cabalist": "MAGE", "Sorcerer": "MAGE", "Theurgist": "ELEM", "Wizard": "ELEM",
		"Infiltrator": "ROGU", "Minstrel": "ROGU", "Scout": "ROGU", "Necromancer": "ARAW",
		"Warrior": "WARR", "Thane": "WARR", "Berserker": "WARR", "Skald": "WARR", "Savage": "WARR",
		"Healer": "SPIR", "Shaman": "SPIR", "Runemaster": "MYST", "Spiritmaster": "MYST", "Bonedancer": "MYST",
		"Hunter": "NROG", "Shadowblade": "NROG",
		"Blademaster": "ARMS", "Champion": "ARMS", "Hero": "ARMS", "Bard": "NATU", "Druid": "NATU", "Warden": "NATU",
		"Eldritch": "MAGI", "Enchanter": "MAGI", "Mentalist": "MAGI", "Nightshade": "STEA", "Ranger": "STEA",
		"Animist": "GROV", "Valewalker": "GROV"}
# medallion icons in breadcrumbs.tga (64 px cells, normal + hover side by side)
# owner 2026-10-09 (old client screenshots): shield = REALM, dragon = OPTIONS, swords = PLAY and CREATE (one button that
# changes with the selected slot), figure = CUSTOMIZE, skull = DELETE, X = QUIT / CANCEL. Paws / star are not on the
# owner's screens. CONTINUE = the figure (owner's creation screenshot)
const ICON := {"realm": Vector2i(0, 0), "options": Vector2i(2, 0), "delete": Vector2i(0, 1), "continue": Vector2i(2, 2),
			   "play": Vector2i(0, 2), "create": Vector2i(0, 2), "customize": Vector2i(2, 2), "quit": Vector2i(2, 3)}

var meta := {}
var realm := "hib"
var screen := ""
var chars: Array = []
var sel := 0
var draft := {}                                   # the character being created or customized
var editing := false                              # customize an existing character (select screen CUSTOMIZE)
var locks := {}

var _scene: NifScene
var _scene_realm := ""
var _env: Environment
var _cam: Camera3D
var _figure: Fig3Figure
var _figure_key := ""
var _yaw := 0.0
var _zoom := 1.0
var _layer: CanvasLayer
var _root: Control
var _frame: Control
var _wext := 1024.0
var _font_bold: FontFile
var _font_reg: FontFile
var _textures := {}
var _swatch_cache := {}
var _status: Label
var _name_edit: LineEdit
var _desc: RichTextLabel
var _menu: OptionsWindow                     # (the game's own Options window - owner 2026-11-08: the old one was "a real
var _menu_layer: CanvasLayer                 # stunted one and feels disjointed")
var _menu_root: Control
var _drag := 0


func _ready() -> void:
	meta = JSON.parse_string(FileAccess.get_file_as_string(PRE + "/pregame.json"))
	_font_bold = _font("minionpro-bold.ttf")
	_font_reg = _font("minionpro-regular.ttf")
	PregameMusic.play()
	if Server.active:                                      # the server's character lists, as they arrive
		Server.characters_ready.connect(_on_server_characters)
		Server.created.connect(_on_server_created)
		Server.deleted.connect(func(): sel = 0; _show("select"))
		Server.name_checked.connect(_on_name_checked)
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.05, 0.05, 0.07)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(1, 1, 1)
	_env.ambient_light_energy = 1.0                   # set per realm in _load_realm_scene (fitted to the client)
	_env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	_env.fog_enabled = true
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-45, 150, 0)
	sun.light_energy = 0.7
	sun.light_cull_mask = 2                            # lights the character only (figure meshes are on layer 2)
	add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = CAM_FOV
	_cam.far = 3000.0
	add_child(_cam)
	_cam.make_current()
	_layer = CanvasLayer.new()
	add_child(_layer)
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	# clicks on no button / panel pass through to the drag (left: turn the character, right: zoom) - as a full-screen
	# STOP it took every click and the drag never started (a player report 2026-10-17)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = _make_theme()
	_layer.add_child(_root)
	_menu_layer = CanvasLayer.new()
	_menu_layer.layer = 20
	add_child(_menu_layer)
	_menu_root = Control.new()
	_menu_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_menu_root.theme = UiArt.tooltip_theme()
	_menu_layer.add_child(_menu_root)
	_menu = OptionsWindow.new()
	_menu.pregame = true
	_menu.setup("options", "options", Rect2(), Vector2.ZERO)
	_menu_root.add_child(_menu)
	_menu.visible = false
	_menu.build()
	_scale_menu()
	get_viewport().size_changed.connect(_scale_menu)
	get_viewport().size_changed.connect(func(): _show(screen))
	var shot := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--pregame-shot="):
			shot = a.split("=", true, 1)[1]
	_show("realm")
	if shot != "":
		_shots.call_deferred(shot)
	for a in OS.get_cmdline_user_args():                 # test runs with the server: --auto-play=alb:Name
		if a.begins_with("--auto-play=") and Server.active:
			_auto_play.call_deferred(a.split("=", true, 1)[1])


## A test run against the server: that realm's character of that name enters the world (no clicks).
func _auto_play(spec: String) -> void:
	var r := spec.get_slice(":", 0)
	var who := spec.get_slice(":", 1).to_lower()
	_pick_realm(r)
	for i in 120:
		await get_tree().create_timer(0.5).timeout
		chars = Server.characters_in(r)
		for j in chars.size():
			if String((chars[j] as Dictionary).get("name", "")).to_lower() == who:
				sel = j
				_play()
				return
	print("[auto-play] no character %s in %s" % [who, r])


# ---------------------------------------------------------------- screens

func _show(which: String) -> void:
	screen = which
	for c in _root.get_children():
		c.queue_free()
	_status = null
	match which:
		"realm": _build_realm()
		"select": _build_select()
		"create": _build_create()
		"customize": _build_customize()
	_place_camera()


func _build_realm() -> void:
	# owner 2026-10-09: no black bars - the frame (stretched to 16:9 before its x4plus pass, build_pregame.py) fills
	# the whole window; the three realm panels widen with it, so each realm's widgets centre on its panel
	_frame_art("realm_selection_wide", 0, 0, false, true)
	var kx := _wext / 1024.0
	for i in 3:
		var r: String = REALM_ORDER[i]
		var x := (170.0 + i * 342.0) * kx
		var regions: Array = {"alb": [Rect2(0, 0, 122, 206), Rect2(126, 0, 122, 206)],
						"hib": [Rect2(0, 0, 150, 214), Rect2(150, 0, 149, 214)],   # hover cells end 1 px early:
						"mid": [Rect2(0, 0, 126, 218), Rect2(128, 0, 125, 218)]}[r]   # the sheet's white strip follows (owner saw a line)
		var art := _small({"alb": "albion_button", "hib": "hibernia_button", "mid": "midgard_button"}[r])
		var b := TextureButton.new()
		b.texture_normal = _atlas(art, regions[0], 4)
		b.texture_hover = _atlas(art, regions[1], 4)
		b.ignore_texture_size = true
		b.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		_at(b, x - 75, 92, 150, 210)
		b.pressed.connect(_pick_realm.bind(r))
		var d := _label(String(meta.realm_descriptions.get(REALM_NAMES[r].to_lower(), "")).to_upper(), x - 150, 318, 300, 316,
				13, CREAM, HORIZONTAL_ALIGNMENT_CENTER, "L", true)
		d.add_theme_font_override("font", _font_reg)
		var n := Server.characters_in(r).size() if Server.active else CharacterStore.in_realm(Accounts.account, r).size()
		_label("%d CHARACTER%s" % [n, "" if n == 1 else "S"], x - 150, 636, 300, 22, 15, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "L")
	_title("SELECT YOUR REALM")
	_medallion("quit", "QUIT", 44, 726, "L", func(): get_tree().quit())


func _build_select() -> void:
	_load_realm_scene()
	_frame_art("character_selection", 12, 268)
	chars = CharacterStore.in_realm(Accounts.account, realm)
	if Server.active:
		# the server's characters (Offline DAoC Rebuilt): asked for once per realm, the screen redrawn when they come
		chars = Server.characters_in(realm)
		if not Server.characters.has(realm):
			Server.request_characters(realm)
	sel = clampi(sel, 0, CharacterStore.SLOTS_PER_REALM - 1)
	_label("SELECT CHARACTER", 760, 64, 248, 32, 22, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "R")
	for i in CharacterStore.SLOTS_PER_REALM:
		var y := 109.0 + i * 45.0
		var slot := Button.new()
		slot.flat = true
		slot.theme_type_variation = "SlotButton"
		_at(slot, 764, y + 1, 240, 43, "R")
		var knob := TextureRect.new()
		var on := i == sel                               # the selected slot's knob is filled, empty ones too
		knob.texture = _atlas(_small("misc_pieces_new"), Rect2(185 if on else 215, 7, 24, 24), 4)
		knob.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		knob.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_at(knob, 770, y + 11, 20, 20, "R")
		if i < chars.size():
			var c: Dictionary = chars[i]
			_label(("%s THE %s" % [c.name, c.class_name]).to_upper(), 796, y + 3, 206, 22, 15,
					GOLD_HI if on else CREAM, HORIZONTAL_ALIGNMENT_LEFT, "R")
			_label(("LEVEL %d IN %s" % [int(c.level), _where(c)]).to_upper(), 796, y + 23, 208, 18, 13, DIM,
					HORIZONTAL_ALIGNMENT_LEFT, "R").add_theme_font_override("font", _font_reg)
		else:
			_label("EMPTY", 796, y + 11, 208, 22, 16, GOLD_HI if i == sel else DIM, HORIZONTAL_ALIGNMENT_LEFT, "R")
		slot.pressed.connect(func(): sel = i; _show("select"))      # every slot selects, empty ones too (owner)
		slot.gui_input.connect(func(e: InputEvent):
			if e is InputEventMouseButton and e.double_click: _play_or_create())
	# one button under the list: PLAY on a character, CREATE on an empty slot (same place, the client's way)
	_medallion("play", "PLAY" if sel < chars.size() else "CREATE", 884, 600, "R", _play_or_create, 66, 24)
	_title("SELECT YOUR CHARACTER")
	var row := [["quit", "QUIT", func(): get_tree().quit()], ["realm", "REALM", func(): _show("realm")],
				["options", "OPTIONS", _toggle_menu], ["customize", "CUSTOMIZE", _customize_existing],
				["delete", "DELETE", _ask_delete]]
	for k in row.size():                                    # spread across the bottom like the client
		_medallion(row[k][0], row[k][1], _wext * (0.095 + k * 0.2025), 726, "L", row[k][2])
	_status_line()
	if Server.active and Server.last_error != "":
		_say(Server.last_error)
		Server.last_error = ""
	_show_figure(chars[sel] if sel < chars.size() else {})


func _build_create() -> void:
	_load_realm_scene()
	_frame_art("character_creation", 240, 238)
	var races: Array = RACES[realm]
	var race: Array = races[int(draft.race)]
	# left: DESCRIPTIONS - the race, then the chosen way / class (charman/summary.txt), like the client's panel
	_label("DESCRIPTIONS", 16, 62, 220, 30, 22, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "L")
	_label(String(race[0]).to_upper(), 24, 96, 210, 26, 20, GOLD_HI, HORIZONTAL_ALIGNMENT_LEFT, "L")
	var info: Dictionary = meta.classes.get("%s-%s" % [race[1], draft.base], {})
	if Server.active:
		_check_server_class()
		# the client's lore for this race and the class's base class (summary.txt is written per race + base: "Celt
		# Way of Magic" names its paths) - owner 2026-10-15: the server's create screen had lost it. A class the 0.36b
		# client added (Sluaghbinder) has its own text in game.dll (pipeline/build_class_lore.py: class_lore).
		info = meta.classes.get("%s-%s" % [race[1], SERVER_BASE.get(_server_class_name(), "")], {})
		if info.is_empty() and (meta.get("class_lore", {}) as Dictionary).has(_server_class_name()):
			info = {"text": String(meta.class_lore[_server_class_name()])}
		_label(_server_class_name().to_upper(), 24, 124, 210, 22, 16, GOLD, HORIZONTAL_ALIGNMENT_LEFT, "L")
	else:
		_label(BASE_BUTTON[draft.base], 24, 124, 210, 22, 16, GOLD, HORIZONTAL_ALIGNMENT_LEFT, "L")
	_desc = RichTextLabel.new()
	_desc.bbcode_enabled = false
	_desc.add_theme_font_override("normal_font", _font_reg)
	_desc.add_theme_font_size_override("normal_font_size", 14)
	_desc.add_theme_color_override("default_color", CREAM)
	_at(_desc, 24, 150, 210, 504, "L")
	_desc.text = String(info.get("text", "")).strip_edges().to_upper()
	_desc.scroll_active = false
	_fit_desc.call_deferred()
	# right: NAME (with RANDOM in the bar), RACE, GENDER, WAY - laid out like the client's panel
	_label("NAME", 790, 80, 216, 30, 22, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "R")
	_name_edit = LineEdit.new()
	_name_edit.placeholder_text = "NAME"
	_name_edit.max_length = CharacterStore.NAME_MAX
	_name_edit.text = String(draft.get("name", ""))
	_name_edit.text_changed.connect(func(t: String):
		var caret := _name_edit.caret_column
		var fixed := t.capitalize().replace(" ", "") if t != "" else t
		if fixed != t:
			_name_edit.text = fixed
			_name_edit.caret_column = caret
		draft["name"] = _name_edit.text)
	var clear := StyleBoxEmpty.new()                    # the frame paints the name box itself (x 796-1002, y 116-137)
	clear.content_margin_left = 6
	_name_edit.add_theme_stylebox_override("normal", clear)
	_name_edit.add_theme_stylebox_override("focus", clear)
	_name_edit.add_theme_font_size_override("font_size", 17)
	_at(_name_edit, 797, 116, 128, 21, "R")
	_bar_button("RANDOM", 929, 119.5, 64, 15, "R", _random_name)     # inside the name box, clear of its border
	# the frame's dotted dividers sit at y 149, 271 and 340: Race fills the band between the first two (its label as
	# the first grid cell, as the client), Gender the next band, Way below the last divider - every realm the same
	var rows := int(ceil((races.size() + 1) / 2.0))
	var ry := 149.0 + (122.0 - rows * 30.0) * 0.5 + 2.0
	_label("RACE", 794, ry, 102, 27, 20, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "R")
	for i in races.size():
		var cell := i + 1
		var b := _bar_button(String(races[i][0]).to_upper(), 794 + (cell % 2) * 106, ry + (cell / 2) * 30, 102, 27, "R",
				func(): draft.race = i; _forget_fits(); _check_base(); _check_server_class(); _show("create"))
		_selected(b, int(draft.race) == i)
		# the chosen class greys the races that can't be it, as the client's create screen (owner 2026-10-15: a
		# Sluaghbinder - Celt and Firbolg only - left every Hibernian race open)
		if Server.active and int(draft.get("class_id", 0)) > 0 and i != int(draft.race):
			b.disabled = not _class_allows(int(draft.class_id), String(races[i][0]))
	_label("GENDER", 790, 275, 216, 24, 20, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "R")
	for g in 2:
		var b := _bar_button(["MALE", "FEMALE"][g], 794 + g * 106, 304, 102, 27, "R",
				func(): draft.gender = g; _forget_fits(); _check_server_class(); _show("create"))
		_selected(b, int(draft.gender) == g)
	if Server.active:
		# the Claude version server's classes for this race (no ways - the old client picked the class itself; the
		# ones the server has switched off or this race can't be are left out - owner 2026-10-11)
		_label("CLASS", 790, 346, 216, 24, 20, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "R")
		var cl := _server_classes()
		for i in cl.size():
			var cid: int = cl[i][0]
			var cb := _bar_button(String(cl[i][1]).to_upper(), 794 + (i % 2) * 106, 376 + (i / 2) * 30, 102, 27, "R",
					func(): draft.class_id = cid; _show("create"))
			_selected(cb, int(draft.get("class_id", 0)) == cid)
	var bases: Array = [] if Server.active else BASES[realm]
	if not Server.active:
		_label("WAY", 790, 346, 216, 24, 20, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "R")
	for i in bases.size():
		var key: String = bases[i]
		var b := _bar_button(BASE_BUTTON[key].trim_prefix("WAY OF "), 794 + (i % 2) * 106, 376 + (i / 2) * 30, 102, 27,
				"R", func(): draft.base = key; _show("create"))
		b.disabled = not _base_ok(key)                   # greyed where the client says the pair is not available
		_selected(b, String(draft.base) == key)
	_title("SELECT YOUR RACE")
	_medallion("quit", "CANCEL", _wext * 0.095, 726, "L", func(): _show("select"))
	_medallion("realm", "REALM", _wext * 0.2975, 726, "L", func(): _show("realm"))
	_medallion("continue", "CONTINUE", _wext * 0.905, 726, "L", _create_continue)
	_status_line()
	_show_figure(_draft_character())


func _build_customize() -> void:
	_load_realm_scene()
	_bare_frame()
	_show_figure(draft if editing else _draft_character())
	var f := _figure
	if not f.is_layered() and not f.layered_changes().is_empty():   # the face taken apart (brows, beard, lines)
		f.apply(f.layered_changes())
		draft.look = f.look.duplicate(true)
	if not _tab in ["face", "skin", "body"] or (_tab == "skin" and (f.meta.get("skin_layers", {}) as Dictionary).is_empty()):
		_tab = "face"
	_creator_chrome()
	var content := _creator_panel()
	var y := 6.0
	match _tab:
		"face": y = _c_face(content, y)
		"skin": y = _c_skin(content, y)
		"body": y = _c_body(content, y)
	content.custom_minimum_size = Vector2(CW, y + 8)
	_status_line()


# ---------------------------------------------------------------- the creator (owner 2026-11-06: WoW's screen as the
# template - the character in its realm, the choices down the right to cycle through, colour bars, FACE / SKIN / BODY)

const CW := 346.0                                       # the options' width (frame units)
const C_PANEL := Color(0.05, 0.04, 0.035, 0.78)
const C_EDGE := Color(0.62, 0.5, 0.26)
var _tab := "face"
var _scroll: ScrollContainer
var _scroll_keep := 0
var _picker: Control


## The window without the client's painted frame: the realm scene fills it.
func _bare_frame() -> void:
	var vp := get_viewport().get_visible_rect().size
	var s := vp.y / 768.0
	_wext = maxf(vp.x / s, 1024.0)
	_frame = Control.new()
	_frame.scale = Vector2(s, s)
	_frame.size = Vector2(_wext, 768)
	_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_frame)


func _cpanel(x: float, y: float, w: float, h: float, anchor: String, alpha := 0.78, edge := C_EDGE, radius := 6) -> Panel:
	var p := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(C_PANEL, alpha)
	sb.border_color = edge
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(radius)
	sb.shadow_color = Color(0, 0, 0, 0.4)
	sb.shadow_size = 5
	p.add_theme_stylebox_override("panel", sb)
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	_at(p, x, y, w, h, anchor)
	return p


## A flat gold-edged button (the creator's own look, not the client's stone bars).
func _cbutton(text: String, parent: Control, x: float, y: float, w: float, h: float, cb: Callable, size := 14,
		active := false) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	for st in ["normal", "hover", "pressed", "disabled"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.34, 0.24, 0.07, 0.95) if active or st == "pressed" else (Color(0.24, 0.18, 0.07, 0.95) if st == "hover" else Color(0.14, 0.11, 0.06, 0.92))
		sb.border_color = Color(1.0, 0.82, 0.4) if active or st == "hover" else C_EDGE
		sb.set_border_width_all(2 if active else 1)
		sb.set_corner_radius_all(4)
		sb.set_content_margin_all(1)
		b.add_theme_stylebox_override(st, sb)
	b.add_theme_font_size_override("font_size", size)
	b.add_theme_color_override("font_color", GOLD_HI if active else GOLD)
	b.add_theme_color_override("font_hover_color", GOLD_HI)
	b.position = Vector2(x, y)
	b.size = Vector2(w, h)
	parent.add_child(b)
	b.pressed.connect(cb)
	return b


func _ctext(text: String, parent: Control, x: float, y: float, w: float, h: float, size: int, col: Color,
		align := HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var l := Label.new()
	while size > 9 and _font_bold.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > w:
		size -= 1
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	l.horizontal_alignment = align
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.position = Vector2(x, y)
	l.size = Vector2(w, h)
	parent.add_child(l)
	return l


## Everything around the options: the character's realm, race and class (top left, with the way back to change
## them), the camera buttons, the name across the top, FACE / SKIN / BODY and the whole-look die (top right),
## BACK and FINISH.
func _creator_chrome() -> void:
	# the right side darkened a little, where the options sit
	var shade := ColorRect.new()
	shade.color = Color(0, 0, 0, 0.22)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_at(shade, 1024 - 380, 0, 380, 768, "R")
	# realm, race, class
	var races: Array = RACES[realm]
	var race := String(races[int(draft.get("race", 0))][0]) if not editing else String(draft.get("race_name", draft.get("race", "")))
	var cls := _server_class_name() if Server.active and not editing else String(BASE_BUTTON.get(draft.get("base", ""), draft.get("class", "")))
	var info := _cpanel(20, 18, 270, 66, "L")
	_ctext(REALM_NAMES.get(realm, ""), info, 12, 6, 246, 16, 12, Color(0.86, 0.4, 0.34))
	_ctext(("%s  -  %s" % [race, cls]).to_upper() if not editing else String(draft.get("name", "")).to_upper(), info, 12, 22, 246, 22, 17, GOLD_HI)
	if not editing:
		var chg := _ctext("CHANGE RACE OR CLASS", info, 12, 44, 160, 16, 11, DIM)
		chg.mouse_filter = Control.MOUSE_FILTER_STOP
		chg.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		chg.gui_input.connect(func(e: InputEvent):
			if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
				draft.look = _figure.look.duplicate(true)
				_show("create"))
	# the camera: turn, zoom, face / whole figure
	var cams := _cpanel(20, 92, 270, 36, "L", 0.6)
	var cb := [["<", func(): _yaw -= 0.35; _place_camera()], [">", func(): _yaw += 0.35; _place_camera()],
		["-", func(): _zoom = clampf(_zoom + 0.15, 0.45, 2.0); _place_camera()],
		["+", func(): _zoom = clampf(_zoom - 0.15, 0.45, 2.0); _place_camera()]]
	for i in cb.size():
		_cbutton(String(cb[i][0]), cams, 6 + i * 34, 5, 28, 26, cb[i][1], 16)
	_cbutton("FACE" if _body_view else "BODY", cams, 150, 5, 112, 26, func():
		_body_view = not _body_view
		_zoom = 1.0
		_show("customize"), 13)
	# the name, top centre (set on the race screen; shown here, a new one from the die)
	var nm := _cpanel(512 - 130, 18, 260, 40, "C", 0.85)
	_ctext(String(draft.get("name", "")).to_upper(), nm, 0, 4, 260, 32, 20, CREAM, HORIZONTAL_ALIGNMENT_CENTER)
	# FACE / SKIN / BODY, and the die
	var tabs := [["FACE", "face"]]
	if not (_figure.meta.get("skin_layers", {}) as Dictionary).is_empty():
		tabs.append(["SKIN", "skin"])
	tabs.append(["BODY", "body"])
	var tb := Control.new()
	tb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_at(tb, 1024 - 24 - tabs.size() * 76 - 46, 20, tabs.size() * 76 + 46, 52, "R")
	for i in tabs.size():
		var key: String = tabs[i][1]
		_cbutton(String(tabs[i][0]), tb, 46 + i * 76, 0, 70, 44, func():
			_keep_scroll(false)
			_tab = key
			_body_view = key == "body"
			_zoom = 1.0
			_show("customize"), 16, _tab == key)
	var die := _cbutton("?", tb, 0, 6, 36, 32, func():
		_keep_scroll(true)
		_randomize(), 18)
	die.tooltip_text = "RANDOM LOOK (LOCKED CHOICES STAY)"
	# BACK, FINISH
	var bar := Control.new()
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_at(bar, 0, 700, _wext, 50, "L")
	var back := _cbutton("<  BACK", bar, 24, 0, 190, 44, func(): _show("select" if editing else "create"), 18)
	(back.get_theme_stylebox("normal") as StyleBoxFlat).bg_color = Color(0.45, 0.08, 0.07, 0.95)
	var fin := _cbutton("SAVE" if editing else "FINISH", bar, _wext - 24 - 230, 0, 230, 44, _customize_continue, 20)
	(fin.get_theme_stylebox("normal") as StyleBoxFlat).bg_color = Color(0.3, 0.21, 0.06, 0.96)
	_ctext("DRAG TO TURN  -  RIGHT DRAG OR WHEEL TO ZOOM", bar, 0, 26, _wext, 18, 11, DIM, HORIZONTAL_ALIGNMENT_CENTER)


var _body_view := false


## The options' panel, right side, scrolling; returns the control the rows go in.
func _creator_panel() -> Control:
	var p := _cpanel(1024 - 24 - CW - 16, 84, CW + 16, 600, "R", 0.74)
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.position = Vector2(8, 8)
	_scroll.size = Vector2(CW + 4, 584)
	p.add_child(_scroll)
	var c := Control.new()
	c.custom_minimum_size = Vector2(CW, 10)
	c.mouse_filter = Control.MOUSE_FILTER_PASS
	_scroll.add_child(c)
	var keep := _scroll_keep
	var sc := _scroll
	get_tree().process_frame.connect(func():
		if is_instance_valid(sc):
			sc.scroll_vertical = keep, CONNECT_ONE_SHOT)
	return c


## Keep the panel where it was scrolled to across the rebuild a choice makes (a new tab starts at the top).
func _keep_scroll(keep: bool) -> void:
	_scroll_keep = _scroll.scroll_vertical if keep and is_instance_valid(_scroll) else 0


func _redraw() -> void:
	draft.look = _figure.look.duplicate(true)
	_keep_scroll(true)
	_show("customize")


func _c_header(p: Control, text: String, y: float) -> float:
	_ctext(text, p, 0, y + 4, CW, 20, 13, GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	var line := ColorRect.new()
	line.color = Color(C_EDGE, 0.6)
	line.position = Vector2(10, y + 26)
	line.size = Vector2(CW - 20, 1)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(line)
	return y + 32


## A lock beside a row: RANDOM leaves it alone.
func _c_lock(p: Control, key: String, y: float) -> void:
	var misc := _small("misc_pieces_new")
	var tb := TextureButton.new()
	tb.toggle_mode = true
	tb.button_pressed = locks.get(key, false)
	tb.texture_normal = _atlas(misc, Rect2(226, 209, 10, 11), 4)
	tb.texture_pressed = _atlas(misc, Rect2(244, 210, 7, 10), 4)
	tb.ignore_texture_size = true
	tb.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	tb.tooltip_text = "LOCK (RANDOM LEAVES IT ALONE)"
	tb.position = Vector2(CW - 16, y + 6)
	tb.size = Vector2(12, 14)
	p.add_child(tb)
	tb.toggled.connect(func(on: bool): locks[key] = on)


## [<] value [>]: cycles. label_cb: the label clickable (a feature's fine tuning).
func _c_cycle(p: Control, label: String, value: String, step: Callable, y: float, lock_key := "",
		label_cb := Callable()) -> float:
	var l := _ctext(label.to_upper(), p, 0, y, 112, 26, 14, CREAM, HORIZONTAL_ALIGNMENT_RIGHT)
	if label_cb.is_valid():
		l.mouse_filter = Control.MOUSE_FILTER_STOP
		l.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		l.gui_input.connect(func(e: InputEvent):
			if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
				label_cb.call())
	_cbutton("<", p, 120, y, 26, 26, func(): step.call(-1), 15)
	var box := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.03, 0.025, 0.02, 0.85)
	sb.border_color = Color(C_EDGE, 0.7)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(3)
	box.add_theme_stylebox_override("panel", sb)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.position = Vector2(150, y)
	box.size = Vector2(142, 26)
	p.add_child(box)
	_ctext(value.to_upper(), p, 152, y, 138, 26, 13, GOLD_HI, HORIZONTAL_ALIGNMENT_CENTER)
	_cbutton(">", p, 296, y, 26, 26, func(): step.call(1), 15)
	if lock_key != "":
		_c_lock(p, lock_key, y)
	return y + 32


## A look key cycled through its values (0 .. n-1).
func _c_key(p: Control, label: String, key: String, values: Array, y: float, def := 0) -> float:
	if values.is_empty():
		return y
	var cur := clampi(int(draft.look.get(key, def)), 0, values.size() - 1)
	return _c_cycle(p, label, String(values[cur]), func(d: int):
		var change := {key: (cur + d + values.size()) % values.size()}
		if key == "hair":
			change["hair_color"] = int(draft.look.get("hair_color", 0))
		_figure.apply(change)
		_redraw(), y, key)


## The hair style row: the race's styles less the headwear that came through as styles (Fig3Figure.creator_styles).
func _c_hair_style(p: Control, y: float) -> float:
	var styles: Array = _figure.meta.get("hair_styles", [])
	var offer: Array = _figure.creator_styles()
	if offer.is_empty():
		return y
	var cur_i := int(draft.look.get("hair", 0))
	var at := offer.find(cur_i)
	var label := String(styles[cur_i].label) if cur_i >= 0 and cur_i < styles.size() else "-"
	if cur_i >= 0 and cur_i < styles.size():
		label += _tune_mark("hair", styles[cur_i])
	return _c_cycle(p, "Hair Style", label, func(d: int):
		var n: int = offer[(at + d + offer.size()) % offer.size()] if at >= 0 else offer[0]
		_figure.apply({"hair": n, "hair_color": int(draft.look.get("hair_color", 0))})
		_redraw(), y, "hair")


## A colour bar: the colour itself, arrows through the choices, a click on it opens them all - and, mode "wheel" or
## "skin" (owner 2026-11-06: "a color wheel ... rather than swatches"), a colour of the player's own (look
## "<key>_rgb", which the figure prefers to the choice; a swatch or an arrow drops it).
func _c_colour(p: Control, label: String, key: String, colours: Array, y: float, mode := "wheel") -> float:
	if colours.is_empty():
		return y
	var cur := clampi(int(draft.look.get(key, 0)), 0, colours.size() - 1)
	var own = _figure.custom_colour(key)
	_ctext(label.to_upper(), p, 0, y, 112, 26, 14, CREAM, HORIZONTAL_ALIGNMENT_RIGHT)
	var pick := func(i: int):
		_figure.apply({key: i, key + "_rgb": null})
		_redraw()
	_cbutton("<", p, 120, y, 26, 26, func(): pick.call((cur - 1 + colours.size()) % colours.size()), 15)
	var bar := Button.new()
	bar.focus_mode = Control.FOCUS_NONE
	var paint_bar := func(c: Color):
		for st in ["normal", "hover", "pressed"]:
			var sb := StyleBoxFlat.new()
			sb.bg_color = c
			sb.border_color = Color(1.0, 0.82, 0.4) if st == "hover" else Color(0.05, 0.04, 0.03)
			sb.set_border_width_all(2)
			sb.set_corner_radius_all(3)
			bar.add_theme_stylebox_override(st, sb)
	paint_bar.call(own if own != null else colours[cur])
	bar.position = Vector2(150, y + 2)
	bar.size = Vector2(142, 22)
	bar.tooltip_text = "custom" if own != null else "%d / %d" % [cur + 1, colours.size()]
	p.add_child(bar)
	var custom := Callable()
	if mode != "":
		custom = func(c: Color):                       # (live, as the wheel turns: the figure only - no rebuild)
			_figure.apply({key + "_rgb": [snappedf(c.r, 0.001), snappedf(c.g, 0.001), snappedf(c.b, 0.001)]})
			paint_bar.call(c)
	bar.pressed.connect(func(): _open_picker(colours, -1 if own != null else cur, pick, bar, custom,
			own if own != null else colours[cur], mode))
	_cbutton(">", p, 296, y, 26, 26, func(): pick.call((cur + 1) % colours.size()), 15)
	_c_lock(p, key, y)
	return y + 32


## Every choice of a colour at once, under its bar; a click takes one, a click anywhere else closes it. With a
## custom callback: under them the wheel (any colour) or, mode "skin", the race's own range of skin colours.
func _open_picker(colours: Array, cur: int, pick: Callable, near: Control = null, custom := Callable(),
		start := Color.WHITE, mode := "") -> void:
	if is_instance_valid(_picker):
		_picker.queue_free()
	_picker = Control.new()
	_picker.mouse_filter = Control.MOUSE_FILTER_STOP
	_picker.position = Vector2.ZERO
	_picker.size = Vector2(_wext, 768)
	_frame.add_child(_picker)
	var changed := [false]
	_picker.gui_input.connect(func(e: InputEvent):
		if e is InputEventMouseButton and e.pressed:
			_picker.queue_free()
			if changed[0]:
				_redraw())
	var cols := 8
	var rows := int(ceil(colours.size() / float(cols)))
	var w := cols * 34 + 16
	var extra := 0.0
	if custom.is_valid():
		extra = 196.0 if mode == "skin" else 300.0
	var h := rows * 30 + 16 + extra
	var at := Vector2(_wext - 24 - w - 8, 124)
	if near:
		var local: Vector2 = _frame.get_global_transform().affine_inverse() * near.global_position
		at = Vector2(minf(local.x + near.size.x - w, _wext - w - 8), local.y + near.size.y + 4)
		if at.y + h > 740:
			at.y = maxf(local.y - h - 4, 8.0)
	var box := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(C_PANEL, 0.96)
	sb.border_color = Color(1.0, 0.82, 0.4)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(6)
	sb.shadow_color = Color(0, 0, 0, 0.5)
	sb.shadow_size = 6
	box.add_theme_stylebox_override("panel", sb)
	box.position = at
	box.size = Vector2(w, h)
	_picker.add_child(box)
	for i in colours.size():
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		for st in ["normal", "hover", "pressed"]:
			var bs := StyleBoxFlat.new()
			bs.bg_color = colours[i]
			bs.border_color = GOLD_HI if i == cur or st == "hover" else Color(0.05, 0.04, 0.03)
			bs.set_border_width_all(2)
			bs.set_corner_radius_all(3)
			b.add_theme_stylebox_override(st, bs)
		b.position = Vector2(8 + (i % cols) * 34, 8 + (i / cols) * 30)
		b.size = Vector2(30, 26)
		box.add_child(b)
		b.pressed.connect(func():
			_picker.queue_free()
			pick.call(i))
	if not custom.is_valid():
		return
	var top := rows * 30 + 12.0
	_ctext("CUSTOM", box, 0, top, w, 18, 12, GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	if mode == "skin":
		var field := TextureRect.new()
		var img := _skin_field(258, 150)
		field.texture = ImageTexture.create_from_image(img)
		field.position = Vector2(8, top + 22)
		field.size = Vector2(w - 16, 150)
		field.stretch_mode = TextureRect.STRETCH_SCALE
		field.mouse_filter = Control.MOUSE_FILTER_STOP
		box.add_child(field)
		var mark := ColorRect.new()
		mark.color = Color(1, 1, 1, 0.9)
		mark.size = Vector2(6, 6)
		mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
		mark.visible = false
		field.add_child(mark)
		var take := func(pos: Vector2):
			var q := Vector2(clampf(pos.x / field.size.x, 0.0, 0.999), clampf(pos.y / field.size.y, 0.0, 0.999))
			mark.position = Vector2(q.x * field.size.x - 3, q.y * field.size.y - 3)
			mark.visible = true
			changed[0] = true
			custom.call(img.get_pixel(int(q.x * img.get_width()), int(q.y * img.get_height())))
		field.gui_input.connect(func(e: InputEvent):
			if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
				take.call(e.position)
			elif e is InputEventMouseMotion and (e.button_mask & MOUSE_BUTTON_MASK_LEFT):
				take.call(e.position))
		return
	var cp := ColorPicker.new()
	cp.edit_alpha = false
	cp.picker_shape = ColorPicker.SHAPE_HSV_WHEEL
	cp.sampler_visible = false
	cp.color_modes_visible = false
	cp.sliders_visible = false
	cp.hex_visible = false
	cp.presets_visible = false
	cp.can_add_swatches = false
	cp.color = start
	cp.position = Vector2(8, top + 20)
	cp.custom_minimum_size = Vector2(w - 16, 260)
	cp.size = Vector2(w - 16, 270)
	box.add_child(cp)
	cp.color_changed.connect(func(c: Color):
		changed[0] = true
		custom.call(c))


## The custom skin colours a race takes (owner 2026-11-06: "natural for the race ... darker skin for humans and
## elves"): across, pale to deep; down, cool (pink) to warm (olive). Human-coloured races get the whole human range
## (and their own tones within it); the others (trolls, kobolds ...) their own tones, extended lighter and darker.
func _skin_field(w: int, h: int) -> Image:
	var tones: Array = _figure.meta.get("skin_tones", [])
	var base := _figure.skin_base()
	var own: Array[Color] = []
	for t in tones:
		var k := Fig3Figure.skin_tint(t)
		own.append(Color(base.r * k.r, base.g * k.g, base.b * k.b))
	own.sort_custom(func(a: Color, b: Color): return a.get_luminance() > b.get_luminance())
	var human := true
	for c in own:
		if not (c.r >= c.g and c.g >= c.b * 0.92):           # (blue, green or grey skins: their own range)
			human = false
	var stops: Array[Color] = []
	if human or own.is_empty():
		stops = [Color(0.97, 0.86, 0.79), Color(0.88, 0.7, 0.6), Color(0.76, 0.56, 0.42), Color(0.6, 0.41, 0.28),
			Color(0.44, 0.28, 0.18), Color(0.3, 0.19, 0.12), Color(0.19, 0.12, 0.08)]
	else:
		stops.append(own[0].lightened(0.25))
		stops.append_array(own)
		stops.append(own[own.size() - 1].darkened(0.35))
	var img := Image.create(w, h, false, Image.FORMAT_RGB8)
	for x in w:
		var t := float(x) / float(w - 1) * float(stops.size() - 1)
		var i := mini(int(t), stops.size() - 2)
		var c: Color = stops[i].lerp(stops[i + 1], t - float(i))
		for y in h:
			var u := float(y) / float(h - 1)
			var m: Color = Color(1.05, 0.95, 0.98).lerp(Color(1.0, 1.0, 1.0), u * 2.0) if u < 0.5 \
				else Color(1.0, 1.0, 1.0).lerp(Color(0.99, 1.0, 0.84), (u - 0.5) * 2.0)
			img.set_pixel(x, y, Color(clampf(c.r * m.r, 0, 1), clampf(c.g * m.g, 0, 1), clampf(c.b * m.b, 0, 1)))
	return img


## A slider row (indented under its choice when sub).
func _c_slider(p: Control, label: String, value: float, lo: float, hi: float, changed: Callable, y: float,
		sub := true, reset := 0.0, step := 0.05) -> float:
	_ctext(label.to_upper(), p, 0, y, 140 if sub else 112, 22, 12 if sub else 14, CREAM if not sub else Color(CREAM, 0.85),
			HORIZONTAL_ALIGNMENT_RIGHT)
	var s := HSlider.new()
	s.min_value = lo
	s.max_value = hi
	s.step = step
	s.value = value
	s.position = Vector2(150, y + 2)
	s.size = Vector2(142, 18)
	p.add_child(s)
	s.value_changed.connect(func(v: float): changed.call(snappedf(v, step)))
	s.gui_input.connect(func(e: InputEvent):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_RIGHT:
			s.value = reset
			s.accept_event())
	return y + 25


func _c_amount(p: Control, label: String, key: String, def: float, lo: float, hi: float, y: float) -> float:
	return _c_slider(p, label, float(draft.look.get(key, def)), lo, hi, func(v: float):
		_figure.apply({key: v})
		draft.look[key] = v, y, true, def)


## The fit under a style's row (owner 2026-11-08: "The Hair, Beard, Sideburns, and Moustache fit sections of the UI
## can now all go away, and just have the length slider for each right under the style selector"): Length alone -
## the rest of the fit is the one tuned for the race. While tuning, a part not yet finished keeps every slider and
## the save / disable controls (Shar, Frostalf and the copied face hair still to check).
func _c_part_fit(p: Control, kind: String, y: float) -> float:
	var lists := {"hair": "hair_styles", "beard": "beards", "moustache": "moustaches", "sideburns": "sideburns"}
	var list: Array = _figure.meta.get(String(lists[kind]), [])
	var i := int(draft.look.get("hair", 0)) if kind == "hair" else \
			(_figure.beard_index() if kind == "beard" else int(draft.look.get(kind, 0))) - 1
	if i < 0 or i >= list.size() or list[i].node == null or not bool(list[i].get("fit", false)):
		return y
	var node := String(list[i].node)
	var entry := _figure.part_entry(node)
	var locked := entry.is_empty() or Fig3Figure.part_locked(_figure.race, String(entry._kind), entry)
	if Fig3Figure.tuning_on() and not locked:
		return _c_fit_rows(p, {"hair": "HAIR", "beard": "BEARD", "moustache": "MOUSTACHE", "sideburns": "SIDEBURNS"}[kind] + " FIT", node, y)
	return _c_fit_slider(p, node, "len", "Length", y)


## One part's fit sliders (Fig3Figure.HAIR_FIT), kept by its node in look.hair_fit. Right-click: back to none. While
## tuning (Fig3Figure.tuning_on), the race's save / disable / completed controls under them.
func _c_fit_rows(p: Control, title: String, node: String, y: float) -> float:
	y = _c_header(p, title, y + 4)
	var entry := _figure.part_entry(node)
	var locked := not entry.is_empty() and Fig3Figure.part_locked(_figure.race, String(entry._kind), entry)
	for f in Fig3Figure.HAIR_FIT:
		if locked and String(f[0]) != "len":       # (a finished style: its fit fixed, Length only)
			continue
		y = _c_fit_slider(p, node, String(f[0]), String(f[1]), y)
	if Fig3Figure.tuning_on() and not locked:
		y = _c_tuning(p, node, y)
	return y


## One fit slider for a part (look.hair_fit, by node: over the race's tuned fit). Right-click: 0.
func _c_fit_slider(p: Control, node: String, k: String, label: String, y: float) -> float:
	return _c_slider(p, label, float(_figure.hair_fit_of(node).get(k, 0.0)), -1.0, 1.0, func(v: float):
		var all: Dictionary = (draft.look.get("hair_fit", {}) as Dictionary).duplicate(true)
		var one: Dictionary = all.get(node, _figure.hair_fit_of(node)).duplicate()
		one[k] = v
		all[node] = one
		draft.look["hair_fit"] = all
		_figure.look["hair_fit"] = all
		_figure._apply_hair_fit(), y, true, 0.0, 0.01)


## The fit slider values in the look (look.hair_fit, by mesh node) dropped - one node's, or all: a node name is
## the race's own (new_beard_5 is a different beard on a Valkyn than on a Kobold), so values set on one race must
## not carry to the next one picked (owner 2026-11-08: tuned fits "off again ... when I close down the client and
## reopen it, it's back"), and once saved the tuned fit is the style's own.
func _forget_fits(node := "") -> void:
	for l in [draft.get("look", {}), _figure.look if _figure else {}]:
		if not (l as Dictionary).has("hair_fit"):
			continue
		if node == "":
			l.erase("hair_fit")
		else:
			var all: Dictionary = (l.hair_fit as Dictionary).duplicate(true)
			all.erase(node)
			l["hair_fit"] = all


# --- hair tuning (owner 2026-11-06: "a tick box ... that says Disable for <race> ... put a (completed on <date>)
# somewhere in that UI"): on the owner's machine only (Fig3Figure.tuning_on). Saved to hair_tuning/<race>.json.
func _tune_race() -> String:
	return "%s %s" % [String(RACES[realm][int(draft.race)][0]), "Male" if int(draft.gender) == 0 else "Female"]


## " (done)" / " (disabled)" after a choice's name while tuning.
func _tune_mark(kind: String, entry: Dictionary) -> String:
	if not Fig3Figure.tuning_on() or entry.is_empty():
		return ""
	var part := Fig3Figure.tuning_part(_figure.race, Fig3Figure.part_key(kind, entry))
	if bool(part.get("disabled", false)):
		return " (disabled)"
	return " (done)" if part.has("done") else ""


func _c_tuning(p: Control, node: String, y: float) -> float:
	var entry := _figure.part_entry(node)
	if entry.is_empty():
		return y
	var rc := _figure.race
	var key := Fig3Figure.part_key(String(entry._kind), entry)
	var part := Fig3Figure.tuning_part(rc, key).duplicate(true)
	var today := Time.get_date_string_from_system()
	var off := bool(part.get("disabled", false))
	y += 4
	_cbutton("Save fit for " + _tune_race(), p, 8, y, CW - 16, 26, func():
		part["fit"] = _figure.hair_fit_of(node).duplicate()
		part["disabled"] = false
		part["done"] = today
		part["node"] = node
		Fig3Figure.save_tuning_part(rc, key, part)
		_forget_fits(node)
		_redraw(), 13)
	y += 30
	_cbutton(("[X] " if off else "[  ] ") + "Disable for " + _tune_race(), p, 8, y, CW - 16, 26, func():
		part["disabled"] = not off
		part["done"] = today
		part["node"] = node
		Fig3Figure.save_tuning_part(rc, key, part)
		_forget_fits(node)
		_redraw(), 13, off)
	y += 30
	var when := "(completed on %s)" % String(part.done) if part.has("done") else "(not done yet)"
	_ctext(when, p, 0, y, CW, 20, 12, Color(CREAM, 0.85), HORIZONTAL_ALIGNMENT_CENTER)
	y += 20
	var n := 0
	var done := 0
	for e in _figure.fit_parts():
		n += 1
		if Fig3Figure.tuning_part(rc, Fig3Figure.part_key(String(e._kind), e)).has("done"):
			done += 1
	_ctext("%s: %d of %d done" % [_tune_race(), done, n], p, 0, y, CW, 20, 12, GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	return y + 24


## A beard / moustache / sideburns row: the choices offered for the race (Fig3Figure.offered - while tuning, all of
## them, marked).
func _c_face_hair(p: Control, label: String, key: String, kind: String, list: Array, y: float, cur: int) -> float:
	var offer: Array = _figure.offered(kind)
	if offer.size() <= 1:
		return y
	var at := offer.find(cur)
	var shown := "None" if cur <= 0 or cur > list.size() else String(list[cur - 1].label) + _tune_mark(kind, list[cur - 1])
	return _c_cycle(p, label, shown, func(d: int):
		var n: int = offer[(at + d + offer.size()) % offer.size()] if at >= 0 else offer[0]
		_figure.apply({key: n})
		_redraw(), y, key)


# --- FACE: skin and eye colour, hair, then the face feature by feature
func _c_face(p: Control, y: float) -> float:
	var f := _figure
	y = _c_header(p, "APPEARANCE", y)
	y = _c_colour(p, "Skin Color", "skin", _skin_colours(), y, "skin")
	y = _c_colour(p, "Eye Color", "eyes", _eye_colours(), y)
	y = _c_hair_style(p, y)
	y = _c_part_fit(p, "hair", y)
	if not (f.meta.get("hair_under", {}) as Dictionary).is_empty():      # (the scalp cap: on or off under any style)
		y = _c_key(p, String(f.meta.hair_under.get("label", "Scalp Cap")), "scalp_cap", ["Off", "On"], y)
	if f.option_count("turban") > 0:              # (Saracens: a turban worn over any hair style)
		var tl: Array = ["None"] + f.meta.turbans.map(func(x): return String(x.label))
		var tcur := f.turban_index()
		y = _c_cycle(p, "Headwear", String(tl[tcur]), func(d: int):
			var n := (tcur + d + tl.size()) % tl.size()
			_figure.apply({"turban": n})
			if not _figure.creator_styles().has(int(_figure.look.get("hair", 0))) and not _figure.creator_styles().is_empty():
				_figure.apply({"hair": _figure.creator_styles()[0]})    # (the hair from under a turban, gone with it)
			_redraw(), y, "turban")
		if tcur > 0:
			y = _c_colour(p, "Turban Color", "turban_color", Fig3Figure.TURBAN_COLORS, y)
	if f.option_count("beard") > 1:                 # (men: the beards split off the hair styles)
		y = _c_face_hair(p, "Beard", "beard", "beard", f.meta.beards, y, f.beard_index())
		y = _c_part_fit(p, "beard", y)
	for kind in Fig3Figure.FACE_HAIR:              # (moustaches; sideburns, owner 2026-11-06: "its own category")
		if f.option_count(String(kind[0])) > 1:
			y = _c_face_hair(p, String(kind[2]), String(kind[0]), String(kind[0]), f.meta[String(kind[1])], y,
					int(f.look.get(String(kind[0]), 0)))
			y = _c_part_fit(p, String(kind[0]), y)
	if f.option_count("hair_color") > 0 and (_hair_has_mesh() or f.beard_index() > 0 or f.scalp_cap_on() \
			or int(f.look.get("moustache", 0)) > 0 or int(f.look.get("sideburns", 0)) > 0):
		y = _c_colour(p, "Hair Color", "hair_color", _hair_colours(), y)
	if not f.is_layered():
		y = _c_key(p, "Face", "face", f.meta.get("faces", []).map(func(x): return String(x.label)), y)
	if f.option_count("tattoo") > 0:
		y = _c_key(p, "Tattoo", "tattoo", f.meta.get("tattoos", []).map(func(x): return String(x.label)), y)
	var shapes: Array = f.meta.get("face_shapes", [])
	if not shapes.is_empty():
		y = _c_header(p, "FEATURES", y + 4)
		var have := {}
		for fs in shapes:
			have[String(fs[0])] = String(fs[1])
		for feat in Fig3Figure.FACE_FEATURES:
			var keys: Array = (feat[2] as Array).filter(func(k): return have.has(k))
			if keys.is_empty():
				continue
			var fkey := String(feat[0])
			var shape: Dictionary = f.look.get("shape", {})
			var cur := Fig3Figure.feature_preset(feat, shape)
			var n: int = (feat[3] as Array).size()
			var open := _tune == fkey
			y = _c_cycle(p, ("- " if open else "+ ") + String(feat[1]), String(feat[3][cur][0]) if cur >= 0 else "Custom",
				func(d: int):
					var i: int = (cur + d + n) % n if cur >= 0 else (0 if d > 0 else n - 1)
					_figure.set_shape(Fig3Figure.with_feature(feat, _figure.look.get("shape", {}), i))
					_redraw(), y, "shape_" + fkey,
				func():
					_tune = "" if open else fkey
					_redraw())
			if open:
				for key in keys:
					y = _c_slider(p, String(have[key]), float(shape.get(key, 0.0)), -1.0, 1.0, func(v: float):
						var sh: Dictionary = (_figure.look.get("shape", {}) as Dictionary).duplicate()
						if absf(v) < 0.001:
							sh.erase(key)
						else:
							sh[key] = v
						draft.look["shape"] = sh
						_figure.set_shape(sh), y)
				y += 4
		_ctext("CLICK A FEATURE'S NAME TO FINE TUNE IT", p, 0, y, CW, 16, 10, DIM, HORIZONTAL_ALIGNMENT_CENTER)
		y += 20
	var sliders: Array = f.meta.get("sliders", [])
	if not sliders.is_empty():
		y = _c_header(p, "CLASSIC SHAPES", y + 4)
		for i in sliders.size():
			var arr: Array = draft.look.get("sliders", [4, 4, 4, 4])
			y = _c_slider(p, String(sliders[i].label), float(arr[i]) if i < arr.size() else 4.0, 0, 8, func(v: float):
				var a: Array = (draft.look.get("sliders", [4, 4, 4, 4]) as Array).duplicate()
				while a.size() <= i:
					a.append(4)
				a[i] = int(v)
				draft.look["sliders"] = a
				_figure.apply({"sliders": a}), y, false, 4.0)
	return y


# --- SKIN: the face's parts and markings
func _c_skin(p: Control, y: float) -> float:
	var on := func(k: String) -> bool: return int(draft.look.get(k, 0)) > 0
	var layers: Array = (_figure.meta.get("skin_layers", {}) as Dictionary).get("layers", [])
	y = _c_header(p, "FACE DETAIL", y)
	for d in layers:
		var key := String(d.key)
		if key == "stubble" and _figure.race.ends_with("_f"):
			continue                                   # (owner 2026-11-06: no stubble for women)
		var opts := ["None"]
		opts.append_array(d.options)
		match key:
			"brows":
				y = _c_key(p, "Brows", "brows", opts, y)
				if on.call("brows"):
					y = _c_amount(p, "Density", "brow_amt", 1.0, 0.3, 1.4, y)
					var hc: Array = _hair_colours()                 # (0: the hair's colour - for a bald man, his
					var bc := [hc[clampi(int(draft.look.get("hair_color", 0)), 0, hc.size() - 1)] if hc.size() > 0 \
						else Color(0.22, 0.16, 0.11)]                 # style's)
					bc.append_array(Fig3Figure.BROW_COLORS)
					y = _c_colour(p, "Brow Color", "brow_color", bc, y)
			"age":
				y = _c_key(p, "Age Lines", "age_style", opts, y)
				if on.call("age_style"):
					y = _c_amount(p, "Strength", "age", 0.7, 0.1, 1.0, y)
			"stubble":
				y = _c_key(p, "Stubble", "stubble_style", opts, y)
				if on.call("stubble_style"):
					y = _c_amount(p, "Strength", "stubble", 0.8, 0.1, 1.0, y)
			"freckles":
				y = _c_key(p, "Freckles", "freckles", opts, y)
				if on.call("freckles"):
					y = _c_colour(p, "Freckle Color", "freckle_color", Fig3Figure.FRECKLE_COLORS, y)
					y = _c_amount(p, "Strength", "freckle_amt", 0.9, 0.1, 1.2, y)
			"scar":
				y = _c_key(p, "Scar", "scar", opts, y)
				if on.call("scar"):
					y = _c_colour(p, "Scar Color", "scar_color", Fig3Figure.SCAR_COLORS, y)
					y = _c_amount(p, "Strength", "scar_amt", 0.55, 0.1, 1.0, y)
			"lips":
				var cols := [Color(0.62, 0.42, 0.4)]   # (the first: the face's own)
				cols.append_array(Fig3Figure.LIP_COLORS.slice(1))
				y = _c_colour(p, "Lip Color", "lip_color", cols, y)
				if on.call("lip_color") or _figure.custom_colour("lip_color") != null:
					y = _c_amount(p, "Strength", "lip_amt", 0.6, 0.1, 1.0, y)
			"paint":
				y = _c_header(p, "WAR PAINT", y + 4)
				y = _c_key(p, "Pattern", "paint", opts, y)
				if on.call("paint"):
					y = _c_colour(p, "Paint Color", "paint_color", Fig3Figure.PAINT_COLORS, y)
					y = _c_amount(p, "Strength", "paint_amt", 0.92, 0.1, 1.0, y)
					var pyv := Fig3Figure.PAINT_Y                  # (owner 2026-11-06: placed by hand, never off the face)
					y = _c_amount(p, "Up / Down", "paint_y", 0.0, pyv.x, pyv.y, y)
					y = _c_amount(p, "Size", "paint_size", 1.0, Fig3Figure.PAINT_SIZE.x, Fig3Figure.PAINT_SIZE.y, y)
					y = _c_amount(p, "Turn", "paint_turn", 0.0, Fig3Figure.PAINT_TURN.x, Fig3Figure.PAINT_TURN.y, y)
	return y


# --- BODY: the figure's proportions (Fig3Figure.BODY_SLIDERS: bones scaled after the animation)
func _c_body(p: Control, y: float) -> float:
	y = _c_header(p, "BODY", y)
	y = _c_colour(p, "Skin Color", "skin", _skin_colours(), y, "skin")
	var body: Dictionary = draft.look.get("body", {})
	var group := ""
	var female := _figure.race.ends_with("_f")
	for bs in Fig3Figure.BODY_SLIDERS:
		var key := String(bs[0])
		if String(bs[2]) != group:
			group = String(bs[2])
			y = _c_header(p, group, y + 4)
		var label := String(bs[1])
		if key == "chest_size":
			label = "Bust" if female else "Pecs"
		y = _c_slider(p, label, float(body.get(key, 0.0)), -1.0, 1.0, func(v: float):
			var b: Dictionary = (_figure.look.get("body", {}) as Dictionary).duplicate()
			if absf(v) < 0.001:
				b.erase(key)
			else:
				b[key] = v
			draft.look["body"] = b
			_figure.set_body(b), y, false)
	y += 4
	_cbutton("RANDOM BODY", p, 60, y, 110, 26, func():
		_figure.apply({"body": _random_body()})
		_redraw(), 12)
	_cbutton("RESET BODY", p, 180, y, 110, 26, func():
		_figure.apply({"body": {}, "size": 1})
		_redraw(), 12)
	_c_lock(p, "body", y)
	return y + 34


## A body of the race's own kind, a little either way.
func _random_body() -> Dictionary:
	var b := {}
	for bs in Fig3Figure.BODY_SLIDERS:
		if randf() < 0.6:
			b[String(bs[0])] = snappedf(clampf(randfn(0.0, 0.35), -0.8, 0.8), 0.05)
	return b


var _tune := ""                                    # the feature whose sliders are open


## A random skin: brows always, mostly plain otherwise - now and then freckles, lines, a scar, war paint; beards on
## men. all: every layer (the SKIN page's own RANDOM), else only those not locked.
func _random_skin(all := false) -> Dictionary:
	var out := {}
	var free := func(k: String) -> bool: return all or not locks.get(k, false)
	var count := func(k: String) -> int:
		for d in (_figure.meta.get("skin_layers", {}) as Dictionary).get("layers", []):
			if String(d.key) == k:
				return (d.options as Array).size()
		return 0
	if free.call("brows") and count.call("brows") > 0:
		out["brows"] = randi_range(1, count.call("brows"))
		out["brow_amt"] = snappedf(randf_range(0.7, 1.15), 0.05)
	if free.call("freckles"):
		out["freckles"] = 0 if randf() < 0.75 else randi_range(1, maxi(count.call("freckles"), 1))
		out["freckle_color"] = randi() % Fig3Figure.FRECKLE_COLORS.size()
		out["freckle_color_rgb"] = null
	if free.call("age_style"):
		out["age_style"] = 0 if randf() < 0.65 else randi_range(1, count.call("age"))
		out["age"] = snappedf(randf_range(0.3, 0.9), 0.05)
	if free.call("scar"):
		out["scar"] = 0 if randf() < 0.8 else randi_range(1, 4)
	if free.call("stubble_style"):
		out["stubble_style"] = randi_range(0, count.call("stubble")) if not _figure.race.ends_with("_f") and randf() < 0.6 else 0
		out["stubble"] = snappedf(randf_range(0.4, 1.0), 0.05)
	if free.call("paint"):
		out["paint"] = 0 if randf() < 0.85 else randi_range(1, maxi(count.call("paint"), 1))
		out["paint_color"] = randi() % Fig3Figure.PAINT_COLORS.size()
		out["paint_color_rgb"] = null
		for k in ["paint_y", "paint_size", "paint_turn", "paint_amt"]:
			out[k] = null
	if free.call("lip_color"):
		out["lip_color"] = 0 if randf() < 0.8 else randi_range(1, Fig3Figure.LIP_COLORS.size() - 1)
		out["lip_amt"] = snappedf(randf_range(0.35, 0.7), 0.05)
	return out


## A face of the race's own kind: each feature its natural shape or now and then another named one (all: the SHAPE
## page's own RANDOM, else the locked features stay).
func _random_shape(all := false) -> Dictionary:
	var sh: Dictionary = (_figure.look.get("shape", {}) as Dictionary).duplicate()
	for feat in Fig3Figure.FACE_FEATURES:
		if not all and locks.get("shape_" + String(feat[0]), false):
			continue
		var i := 0 if randf() < 0.5 else randi_range(1, (feat[3] as Array).size() - 1)
		sh = Fig3Figure.with_feature(feat, sh, i)
	return sh


# ---------------------------------------------------------------- actions

func _on_server_characters(r: String) -> void:
	if screen == "realm" or (screen == "select" and r == realm):
		_show(screen)


func _pick_realm(r: String) -> void:
	realm = r
	sel = 0
	_show("select")


func _start_create() -> void:
	editing = false
	_yaw = 0.0
	_zoom = 1.0
	draft = {"race": 0, "gender": 0, "base": BASES[realm][0], "name": "", "look": {}}
	_check_base()
	_show("create")


func _create_continue() -> void:
	draft.name = _name_edit.text.strip_edges()
	if Server.active:
		var nerr := Server.name_error(String(draft.name))
		if nerr != "":
			_say(nerr)
			return
		if int(draft.get("class_id", 0)) == 0:
			_say("Choose a class.")
			return
		_say("Checking the name...")
		Server.check_name(String(draft.name))           # _on_name_checked goes on
		return
	var err := CharacterStore.check_name(Accounts.account, String(draft.name))
	if err != "":
		_say(err)
		return
	if not _base_ok(String(draft.base)):
		_say("That class is not available to this race.")
		return
	_yaw = 0.0
	_zoom = 1.0
	_show("customize")


func _customize_existing() -> void:
	if sel >= chars.size():
		return
	editing = true
	_yaw = 0.0
	_zoom = 1.0
	draft = (chars[sel] as Dictionary).duplicate(true)
	_show("customize")


func _customize_continue() -> void:
	draft.look = _figure.look.duplicate(true)
	if editing:
		if Server.active:
			Server.save_look(String(draft.name), draft.look)
			chars = Server.characters_in(realm)
		else:
			CharacterStore.update(Accounts.account, draft)
		_show("select")
	else:
		_finish_create()


## 1.65 has no starting-location screen: a new character starts where the old server's StartupLocation table puts
## its race + base class (owner 2026-10-09). Until that zone is built the character appears at Mag Mell
## (CharacterStore.start_of); the real start stays saved with the character.
func _finish_create() -> void:
	if Server.active:
		var race_name := String(RACES[realm][int(draft.race)][0])
		var err := Server.create_character(realm, race_name, int(draft.gender) == 1, int(draft.class_id), String(draft.name),
				draft.look)
		if err != "":
			_say(err)
			return
		_say("Creating %s..." % draft.name)
		return                                              # _on_server_created goes on
	var c := CharacterFactory.make(realm, int(draft.race), int(draft.gender), String(draft.base), draft.name, draft.look)
	draft["start"] = c.start
	var err := CharacterStore.add(Accounts.account, c)
	if err != "":
		_say(err)
		return
	chars = CharacterStore.in_realm(Accounts.account, realm)
	sel = chars.size() - 1
	_show("select")


func _play_or_create() -> void:
	if sel < chars.size():
		_play()
	else:
		_start_create()


func _play() -> void:
	if sel >= chars.size():
		return
	if Server.active:                                     # the server puts the character in the world (Server.enter_world)
		_say("Entering the world...")
		Server.enter_world(chars[sel])
		return
	CharacterStore.selected = chars[sel]
	get_tree().change_scene_to_file("res://game/zone_viewer.tscn")


func _ask_delete() -> void:
	if sel >= chars.size():
		return
	var c: Dictionary = chars[sel]
	# owner 2026-10-10: the black granite of the in-game windows, not the engine's grey dialog - the client's stone
	# chat-box frame (chatext) as a nine-patch over a dimmed screen, gold title, cream text, the stone-bar buttons
	var shade := ColorRect.new()
	shade.color = Color(0, 0, 0, 0.55)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(shade)
	var w := 480.0
	var h := 170.0
	var box := Control.new()
	box.size = Vector2(w, h)
	box.position = ((_root.get_viewport_rect().size if _root.size == Vector2.ZERO else _root.size) - box.size) * 0.5
	shade.add_child(box)
	var holder := Control.new()                          # the art at x4 inside a 1/4-scale holder (ChatWindow's way)
	holder.scale = Vector2(0.25, 0.25)
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var np := NinePatchRect.new()
	np.texture = UiArt.tex("chatext")
	np.region_rect = Rect2(0, 64 * UiArt.K, 512 * UiArt.K, 64 * UiArt.K)
	var m := [3, 12, 12, 3]
	var sides := [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]
	for i in 4:
		np.set_patch_margin(sides[i], int(m[i] * UiArt.K))
	np.size = box.size * 4.0
	np.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(np)
	box.add_child(holder)
	var close := func(): shade.queue_free()
	var title := Label.new()
	title.text = "DELETE CHARACTER"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 18)
	title.add_theme_color_override("font_color", GOLD_HI)
	title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	title.add_theme_constant_override("shadow_offset_x", 2)
	title.add_theme_constant_override("shadow_offset_y", 2)
	title.position = Vector2(0, 22)
	title.size = Vector2(w, 26)
	box.add_child(title)
	var text := Label.new()
	text.text = ("DELETE %s, LEVEL %d %s OF %s?\nTHIS CANNOT BE UNDONE." % [String(c.name), int(c.get("level", 1)),
			String(c.get("class_name", "")), String(REALM_NAMES.get(String(c.get("realm", realm)), ""))]).to_upper()
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	text.add_theme_font_size_override("font_size", 15)
	text.add_theme_color_override("font_color", CREAM)
	text.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	text.add_theme_constant_override("shadow_offset_x", 1)
	text.add_theme_constant_override("shadow_offset_y", 1)
	text.position = Vector2(0, 56)
	text.size = Vector2(w, 44)
	box.add_child(text)
	var del := Button.new()
	del.text = "DELETE"
	del.position = Vector2(w * 0.5 - 150, h - 52)
	del.size = Vector2(130, 30)
	del.pressed.connect(func():
		close.call()
		if Server.active:
			Server.delete_character(realm, c)
			return
		CharacterStore.remove(Accounts.account, String(c.name))
		sel = 0
		_show("select"))
	box.add_child(del)
	var keep := Button.new()
	keep.text = "KEEP"
	keep.position = Vector2(w * 0.5 + 20, h - 52)
	keep.size = Vector2(130, 30)
	keep.pressed.connect(close)
	box.add_child(keep)
	var corner := Button.new()                           # the frame art's corner square closes it, like the old X
	corner.flat = true
	corner.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	corner.add_theme_stylebox_override("hover", StyleBoxEmpty.new())
	corner.add_theme_stylebox_override("pressed", StyleBoxEmpty.new())
	corner.position = Vector2(w - 14, 0)
	corner.size = Vector2(14, 14)
	corner.tooltip_text = "CLOSE"
	corner.pressed.connect(close)
	box.add_child(corner)
	shade.gui_input.connect(func(e):                      # a click outside the box: keep
		if e is InputEventMouseButton and e.pressed and not Rect2(box.position, box.size).has_point(e.position):
			close.call())
	keep.grab_focus()


func _random_name() -> void:
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	draft.name = CharacterFactory.random_name(realm, int(draft.race), rng)
	_name_edit.text = draft.name


func _randomize() -> void:
	var f := _figure
	var l := {}
	for k in ["face", "eyes", "skin", "hair", "tattoo"]:
		if not locks.get(k, false) and f.option_count(k) > 0:
			l[k] = randi() % f.option_count(k)
			l[k + "_rgb"] = null                       # (a colour of the player's own goes with it)
	if l.has("hair"):
		if not locks.get("turban", false) and f.option_count("turban") > 0:
			f.apply({"turban": 0 if randf() < 0.6 else randi_range(1, f.option_count("turban") - 1)})
		var offer: Array = f.creator_styles()
		if not offer.is_empty():
			l["hair"] = offer[randi() % offer.size()]
	if not locks.get("hair_color", false):
		l["hair_color_rgb"] = null
	if not locks.get("turban", false) and f.option_count("turban") > 0:
		l["turban_color"] = randi() % Fig3Figure.TURBAN_COLORS.size()
		l["turban_color_rgb"] = null
	# (beards, moustaches, sideburns: of those not disabled for the race - hair tuning)
	for fk in [["beard", 0.35], ["moustache", 0.6], ["sideburns", 0.7]]:
		var offer: Array = f.offered(String(fk[0])).filter(func(x): return int(x) > 0)
		if not locks.get(String(fk[0]), false) and not offer.is_empty():
			l[String(fk[0])] = 0 if randf() < float(fk[1]) else int(offer[randi() % offer.size()])
	f.apply(l)
	if not locks.get("hair_color", false) and f.option_count("hair_color") > 0:
		f.apply({"hair_color": randi() % f.option_count("hair_color")})
	if not locks.get("sliders", false):
		var arr := []
		for i in f.meta.get("sliders", []).size():
			arr.append(randi() % 9)
		f.apply({"sliders": arr})
	f.set_shape(_random_shape())
	if not locks.get("body", false):
		f.apply({"body": _random_body(), "size": 1})
	if not (f.meta.get("skin_layers", {}) as Dictionary).is_empty():
		f.apply(_random_skin())
	draft.look = f.look.duplicate(true)
	_show("customize")


func _check_base() -> void:
	if not _base_ok(String(draft.base)):
		for k in BASES[realm]:
			if _base_ok(k):
				draft.base = k
				return


func _base_ok(key: String) -> bool:
	return CharacterFactory.available(realm, int(draft.get("race", 0)), key)


# ---------------------------------------------------------------- the server's classes (Offline DAoC Rebuilt)

func _server_classes() -> Array:
	var race_name := String(RACES[realm][int(draft.race)][0])
	return Server.classes_for(realm, int(Server.RACE_BY_NAME.get(race_name, 0)), int(draft.gender) == 1)


func _class_allows(class_id: int, race_name: String) -> bool:
	for c in Server.classes_for(realm, int(Server.RACE_BY_NAME.get(race_name, 0)), int(draft.gender) == 1):
		if int(c[0]) == class_id:
			return true
	return false


func _check_server_class() -> void:
	if not Server.active:
		return
	var cl := _server_classes()
	for c in cl:
		if int(c[0]) == int(draft.get("class_id", 0)):
			return
	draft["class_id"] = int(cl[0][0]) if cl.size() > 0 else 0


func _server_class_name() -> String:
	for c in _server_classes():
		if int(c[0]) == int(draft.get("class_id", 0)):
			return String(c[1])
	return ""


func _on_name_checked(n: String, result: int) -> void:
	if screen != "create" or n.to_lower() != String(draft.get("name", "")).to_lower():
		return
	if result == 2:
		_say("That name is already taken.")
	elif result == 1:
		_say("That name is not allowed.")
	else:
		_yaw = 0.0
		_zoom = 1.0
		_show("customize")


func _on_server_created(ok: bool, why: String) -> void:
	chars = Server.characters_in(realm)
	if ok:
		for i in chars.size():
			if String(chars[i].name).to_lower() == String(draft.get("name", "")).to_lower():
				sel = i
		_show("select")
	else:
		_say(why)


func _draft_character() -> Dictionary:
	var race: Array = RACES[realm][int(draft.race)]
	return {"prefix": "%s_%s" % [race[2], "m" if int(draft.gender) == 0 else "f"], "look": draft.get("look", {})}


# ---------------------------------------------------------------- 3D

func _load_realm_scene() -> void:
	if _scene_realm == realm:
		return
	if _scene:
		_scene.queue_free()
	_scene = NifScene.new()
	add_child(_scene)
	_scene.load_scene("%s/%s/scene.gltf" % [PRE, realm])
	_scene_realm = realm
	var fog: Dictionary = meta.fog.get(realm, {})
	if not fog.is_empty():
		_env.fog_light_color = Color(fog.color[0], fog.color[1], fog.color[2])
		_env.fog_density = float(fog.density) * 0.00004
	# scene light per realm, fitted to the owner's client screenshots: the client's fixed-function lighting darkens
	# these materials (ambient / diffuse ~0.6-0.7); Midgard was right at full light (owner: "looks good")
	var light: Array = REALM_LIGHT.get(realm, [Color(1, 1, 1), 1.0])
	_env.ambient_light_color = light[0]
	_env.ambient_light_energy = light[1]


func _show_figure(c: Dictionary) -> void:
	var prefix := String(c.get("prefix", ""))
	if prefix == "":
		if _figure:
			_figure.queue_free()
			_figure = null
			_figure_key = ""
		return
	if _figure == null or _figure_key != prefix:
		if _figure:
			_figure.queue_free()
		_figure = Fig3Figure.new()
		add_child(_figure)
		_figure.load_figure(prefix)
		_figure_key = prefix
		for mi in _figure.find_children("*", "MeshInstance3D", true, false):
			(mi as MeshInstance3D).layers = 3              # scene light + the character light
	_figure.position = SPOT
	_figure.visible = true
	_figure.look = {}
	_figure.apply(c.get("look", {}))
	_dress_figure(c)
	if screen == "customize":
		draft["look"] = _figure.look.duplicate(true)
		draft["prefix"] = prefix


## The character's worn armour and weapons on the select screen, as in game (owner 2026-10-10: the staff and armour
## didn't show) - Player.dress with the saved inventory (slot -> {id}).
var _figure_gear: Array = []


func _dress_figure(c: Dictionary) -> void:
	for g in _figure_gear:
		if is_instance_valid(g):
			g.queue_free()
	_figure_gear.clear()
	var inv: Dictionary = c.get("inventory", {}) if c.get("inventory") is Dictionary else {}
	var item_at := func(slot: int) -> Dictionary:
		var e = inv.get(str(slot))
		return ItemDb.item(String(e.id)) if e is Dictionary and e.has("id") else {}
	_figure_gear = Player.dress(_figure, item_at, String(c.get("active_weapon", "standard")), false)
	for g in _figure_gear:
		for mi in (g as Node).find_children("*", "MeshInstance3D", true, false):
			(mi as MeshInstance3D).layers = 3              # scene light + the character light, like the figure


func _place_camera() -> void:
	if _cam == null:
		return
	var k := _figure.scale.x if _figure else 1.0
	var to_cam := CAM_POS - SPOT
	to_cam.y = 0.0
	var bearing := atan2(to_cam.x, to_cam.z)
	if _figure:
		_figure.rotation.y = bearing + _yaw              # faces the camera; drag / arrows turn it
	match screen:
		"select", "realm":
			_cam.position = CAM_POS                      # the client's view, character left of the panel
			_cam.look_at(CAM_LOOK)
		"create":
			_cam.position = CAM_POS                      # same camera, aimed at the character (owner's create shot)
			_cam.look_at(SPOT + Vector3(0, 1.1, 0))
		"customize":
			# the client zooms in to the face (distance 40 units, target between the head bones); kept on the
			# select camera's side so the backdrop stays the same, face centred in the open scene area
			var head := _head_position()
			var dir := to_cam.normalized()
			if _body_view:                               # the whole figure (BODY)
				var mid := SPOT + Vector3(0, 0.95 * k, 0)
				_cam.position = mid + dir * (3.3 * k * _zoom)
				_cam.look_at(mid)
			else:
				_cam.position = head + dir * (0.95 * k * _zoom)
				_cam.look_at(head)
			var x := (_wext - 380.0) * 0.5
			var ndc := (x - _wext * 0.5) / (_wext * 0.5)
			var vp := get_viewport().get_visible_rect().size
			var half_h := tan(deg_to_rad(_cam.fov * 0.5)) * (vp.x / maxf(vp.y, 1.0))
			_cam.rotate_object_local(Vector3.UP, atan(ndc * half_h))


func _head_position() -> Vector3:
	if _figure:
		for s in _figure.model.find_children("*", "Skeleton3D", true, false):
			var s3: Skeleton3D = s
			var b := s3.find_bone("Bip01 Head")
			if b >= 0:
				return s3.global_transform * s3.get_bone_global_pose(b).origin + Vector3(0, 0.04 * _figure.scale.x, 0)
	return SPOT + Vector3(0, 1.65, 0)


## The Options window at the game's interface scale (GameUI's: the client's 800x600 layout, readable at 1080p), centred.
func _scale_menu() -> void:
	var vp := get_viewport().get_visible_rect().size
	var cfg := UiArt.load_settings()
	var s := vp.y / 600.0 * 0.78 * float(cfg.get_value("interface", "ui_scale", 1.0))
	_menu_root.scale = Vector2(s, s)
	_menu_root.size = vp / s
	_menu.position = ((vp / s) - _menu.size) / 2.0


func _toggle_menu() -> void:
	if _menu.visible:
		_menu.hide_window()
	else:
		_scale_menu()
		_menu.show_window()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE and _menu.visible and not _menu.capturing():
		_menu.hide_window()
		get_viewport().set_input_as_handled()
		return
	if screen not in ["select", "create", "customize"]:
		return
	if event is InputEventMouseButton:
		_drag = event.button_index if event.pressed else 0
		if screen == "customize" and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			_zoom = clampf(_zoom + (-0.08 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 0.08), 0.45, 2.0)
			_place_camera()
	elif event is InputEventMouseMotion and _drag != 0:
		if not Input.is_mouse_button_pressed(_drag):       # let go over a button (the GUI took the release)
			_drag = 0
			return
		if _drag == MOUSE_BUTTON_LEFT:
			_yaw += event.relative.x * 0.01
		elif _drag == MOUSE_BUTTON_RIGHT and screen == "customize":
			_zoom = clampf(_zoom + event.relative.y * 0.005, 0.45, 2.0)
		_place_camera()


# ---------------------------------------------------------------- customize rows

func _hair_has_mesh() -> bool:
	var styles: Array = _figure.meta.get("hair_styles", [])
	var i := int(draft.look.get("hair", 0))
	return i < styles.size() and styles[i].node != null


func _eye_colours() -> Array:
	return _figure.meta.get("eyes", []).map(func(t): return _swatch(String(t), Color.WHITE, "iris"))


func _skin_colours() -> Array:
	var face: String = _figure.meta.faces[0].tex if _figure.meta.get("faces", []).size() > 0 else ""
	return _figure.meta.get("skin_tones", []).map(func(c): return _swatch(face, Fig3Figure.skin_tint(c), "face"))


func _hair_colours() -> Array:
	var styles: Array = _figure.meta.get("hair_styles", [])
	var i := clampi(int(draft.look.get("hair", 0)), 0, styles.size() - 1)
	var cols: Array = styles[i].colours
	if cols.is_empty() and _figure.scalp_cap_on():          # (bald with the scalp cap: its colours)
		cols = _figure.meta.hair_under.get("colours", [])
	return cols.map(func(c): return _swatch(String(c.tex), Color(c.tint[0], c.tint[1], c.tint[2]), "hair"))


## A swatch from the option's own client texture: the iris colour of an eye-colour texture (it is white except the
## iris), the middle of the face times a skin tint, or a hair texture's covered pixels times the hair tint.
func _swatch(tex: String, tint: Color, kind: String) -> Color:
	var key := "%s|%s|%s" % [tex, tint.to_html(), kind]
	if _swatch_cache.has(key):
		return _swatch_cache[key]
	var img: Image = _figure._tex(tex).get_image() if tex != "" and _figure._tex(tex) else null
	var col := tint
	if img:
		img = img.duplicate()
		if img.is_compressed():
			img.decompress()
		img.convert(Image.FORMAT_RGBA8)
		if kind == "face":
			img = img.get_region(Rect2i(img.get_width() * 3 / 10, img.get_height() * 3 / 10, img.get_width() * 2 / 5, img.get_height() / 4))
		# (an iris is a small part of its texture: at 32 x 32 it averaged into the white - the women's eye swatches
		# all came out alike; owner 2026-11-06)
		var rs := 128 if kind == "iris" else 32
		img.resize(rs, rs, Image.INTERPOLATE_BILINEAR)
		var sum := Color(0, 0, 0, 0)
		var n := 0.0
		for yy in rs:
			for xx in rs:
				var p := img.get_pixel(xx, yy)
				var lum := (p.r + p.g + p.b) / 3.0
				if kind == "iris" and (lum > 0.8 or lum < 0.06):
					continue
				if kind == "hair" and p.a < 0.5:
					continue
				sum += p
				n += 1.0
		if n > 0:
			col = Color(sum.r / n * tint.r, sum.g / n * tint.g, sum.b / n * tint.b)
	_swatch_cache[key] = col
	return col


# ---------------------------------------------------------------- frame + widgets

## The screen frame (1024x768 art, 2x x4plus copy): scaled to the window height; on wide screens the middle stretches
## while the side panels keep their shape (left / right = the panel widths that must not stretch). letterbox: the
## whole frame keeps its aspect (realm select).
func _frame_art(name: String, left: float, right: float, letterbox := false, fill := false) -> void:
	var vp := get_viewport().get_visible_rect().size
	var s := vp.y / 768.0
	_wext = 1024.0 if letterbox else maxf(vp.x / s, 1024.0)
	_frame = Control.new()
	_frame.scale = Vector2(s, s)
	_frame.position = Vector2((vp.x - 1024.0 * s) * 0.5 if letterbox else 0.0, 0)
	_frame.size = Vector2(_wext, 768)
	_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_frame)
	if letterbox:
		var black := ColorRect.new()
		black.color = Color.BLACK
		black.set_anchors_preset(Control.PRESET_FULL_RECT)
		black.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_root.add_child(black)
		_root.move_child(black, 0)
	var tex := _full(name)
	if fill:                                           # art already made wide: the whole picture spans the window
		var all := TextureRect.new()
		all.texture = tex
		all.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		all.stretch_mode = TextureRect.STRETCH_SCALE
		all.mouse_filter = Control.MOUSE_FILTER_IGNORE
		all.size = Vector2(_wext, 768)
		_frame.add_child(all)
		return
	var k := tex.get_width() / 1024.0
	var pieces := [[0.0, left, 0.0, left], [left, 1024.0 - right, left, _wext - right], [1024.0 - right, 1024.0, _wext - right, _wext]]
	for p in pieces:
		if p[1] - p[0] <= 0:
			continue
		var tr := TextureRect.new()
		tr.texture = _atlas(tex, Rect2(p[0], 0, p[1] - p[0], 768), k)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_SCALE
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		tr.position = Vector2(p[2], 0)
		tr.size = Vector2(p[3] - p[2], 768)
		_frame.add_child(tr)


## Place a widget in frame units (1024x768): anchor L keeps x from the left edge, R from the right edge (the right
## panel), C from the centre.
## The description in its box (owner 2026-10-15: "make sure the text fits ... without flowing out of the box"): 16 of
## summary.txt's texts ran past the 504 px box at 14 (the Celt / Firbolg Way of Nature to 660) - a size smaller each
## frame until it fits (11 the least), hidden meanwhile so it doesn't flash.
const DESC_SIZES := [14, 13, 12, 11]


func _fit_desc() -> void:
	var d := _desc
	if d == null or not is_instance_valid(d):
		return
	d.modulate.a = 0.0
	for fs in DESC_SIZES:
		d.add_theme_font_size_override("normal_font_size", fs)
		await get_tree().process_frame
		await get_tree().process_frame
		if not is_instance_valid(d):
			return
		if d.get_content_height() <= d.size.y:
			break
	d.modulate.a = 1.0


func _at(node: Control, x: float, y: float, w: float, h: float, anchor := "L") -> void:
	var shift: float = {"L": 0.0, "C": (_wext - 1024.0) * 0.5, "R": _wext - 1024.0}[anchor]
	if node.get_parent() == null:                      # into the tree first: a button sized before its theme font
		_frame.add_child(node)                         # applies keeps the default font's (taller) size
	node.position = Vector2(x + shift, y)
	node.size = Vector2(w, h)


func _label(text: String, x: float, y: float, w: float, h: float, size: int, color: Color,
		align := HORIZONTAL_ALIGNMENT_LEFT, anchor := "L", wrap := false) -> Label:
	var l := Label.new()
	if wrap:                                           # before sizing: an unwrapped label grows to its text width
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	l.text = text
	if not wrap:                                       # never overflow the box: shrink the text until it fits
		while size > 9 and _font_bold.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > w:
			size -= 1
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	l.horizontal_alignment = align
	if not wrap:
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.clip_text = false
	_at(l, x, y, w, h, anchor)
	return l


func _title(text: String) -> void:
	_label(text, 160, 660, 704, 36, 26, GOLD, HORIZONTAL_ALIGNMENT_CENTER, "C")


func _status_line() -> void:
	_status = _label("", 160, 630, 704, 26, 17, ERROR, HORIZONTAL_ALIGNMENT_CENTER, "C")


func _say(text: String) -> void:
	if _status:
		_status.text = text.to_upper()


## A medallion button (breadcrumbs.tga, normal / hover) with its caption underneath.
func _medallion(icon: String, caption: String, cx: float, cy: float, anchor: String, cb: Callable, size := 50.0,
		caption_size := 13) -> void:
	var art := _small("breadcrumbs")
	var cell: Vector2i = ICON[icon]
	var b := TextureButton.new()
	b.texture_normal = _atlas(art, Rect2(cell.x * 64, cell.y * 64, 64, 64), 4)
	b.texture_hover = _atlas(art, Rect2((cell.x + 1) * 64, cell.y * 64, 64, 64), 4)
	b.texture_pressed = b.texture_hover
	b.ignore_texture_size = true
	b.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	b.tooltip_text = caption
	_at(b, cx - size * 0.5, cy - size * 0.5 - 6, size, size, anchor)
	b.pressed.connect(cb)
	_label(caption, cx - 70, cy + size * 0.5 - 8, 140, caption_size + 6, caption_size, CREAM, HORIZONTAL_ALIGNMENT_CENTER, anchor)


## A text button on the client's stone bars (misc_pieces_new.tga short bars: normal, hover, pressed, disabled).
func _bar_button(text: String, x: float, y: float, w: float, h: float, anchor: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	var fs := 14                                       # shrink until the label fits (ELEMENTALIST, WAY OF THE GROVE ...)
	while fs > 7 and (_font_bold.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > w - 10
			or _font_bold.get_height(fs) + 4 > h):            # and fits the height (RANDOM in the name box)
		fs -= 1
	b.add_theme_font_size_override("font_size", fs)
	b.clip_text = true
	_at(b, x, y, w, h, anchor)
	b.pressed.connect(cb)
	return b


func _selected(b: Button, on: bool) -> void:
	if on:                                              # the client: gold text on the normal dark bar
		b.add_theme_color_override("font_color", Color(1.0, 0.8, 0.2))
		b.add_theme_color_override("font_hover_color", Color(1.0, 0.85, 0.35))


func _bar_style(state: int) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _small("misc_pieces_new")
	s.region_rect = Rect2(0, (105 + state * 22) * 4, 102 * 4, 22 * 4)
	s.set_content_margin_all(2)
	return s


func _make_theme() -> Theme:
	var t := Theme.new()
	t.default_font = _font_bold                         # owner: ALL CAPS and bold
	t.default_font_size = 16
	for cls in ["Label", "LineEdit", "Button"]:
		t.set_color("font_color", cls, CREAM)
	t.set_color("font_hover_color", "Button", GOLD_HI)
	t.set_color("font_pressed_color", "Button", Color(1.0, 0.75, 0.0))
	t.set_color("font_disabled_color", "Button", Color(0.4, 0.38, 0.35))
	t.set_stylebox("normal", "Button", _bar_style(0))
	t.set_stylebox("hover", "Button", _bar_style(1))
	t.set_stylebox("pressed", "Button", _bar_style(2))
	t.set_stylebox("disabled", "Button", _bar_style(3))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_type_variation("SlotButton", "Button")
	var hl := _box(Color(1, 0.85, 0.45, 0.10), Color(0, 0, 0, 0), 0)
	for k in ["normal", "focus", "disabled"]:
		t.set_stylebox(k, "SlotButton", StyleBoxEmpty.new())
	t.set_stylebox("hover", "SlotButton", hl)
	t.set_stylebox("pressed", "SlotButton", hl)
	var edit := StyleBoxTexture.new()
	edit.texture = _small("misc_pieces_new")
	edit.region_rect = Rect2(0, 52 * 4, 160 * 4, 26 * 4)        # the black bar
	edit.set_content_margin_all(4)
	t.set_stylebox("normal", "LineEdit", edit)
	t.set_stylebox("focus", "LineEdit", edit)
	t.set_font_size("font_size", "LineEdit", 20)
	t.set_color("caret_color", "LineEdit", GOLD)
	t.set_color("font_placeholder_color", "LineEdit", Color(CREAM, 0.35))
	t.set_color("font_color", "TooltipLabel", CREAM)
	t.set_stylebox("panel", "TooltipPanel", _box(Color(0, 0, 0, 0.9), GOLD.darkened(0.3), 1))
	t.set_stylebox("panel", "AcceptDialog", _box(Color(0.03, 0.03, 0.03, 0.97), GOLD, 2))
	return t


func _box(bg: Color, border: Color, w: int) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(w)
	s.set_content_margin_all(8)
	return s


# ---------------------------------------------------------------- art

func _atlas(tex: Texture2D, region: Rect2, k: float) -> AtlasTexture:
	var a := AtlasTexture.new()
	a.atlas = tex
	a.region = Rect2(region.position * k, region.size * k)
	return a


func _small(name: String) -> Texture2D:
	return _load_png("%s/ui/small/%s.png" % [PRE, name], "%s/ui/original_small/%s.png" % [PRE, name])


func _full(name: String) -> Texture2D:
	return _load_png("%s/ui/full/%s.png" % [PRE, name], "%s/ui/original_full/%s.png" % [PRE, name])


func _load_png(path: String, fallback: String) -> Texture2D:
	if _textures.has(path):
		return _textures[path]
	var img := Image.load_from_file(ProjectSettings.globalize_path(path))
	if img == null:
		img = Image.load_from_file(ProjectSettings.globalize_path(fallback))
	var tex: Texture2D = null
	if img:
		img.generate_mipmaps()
		tex = ImageTexture.create_from_image(img)
	_textures[path] = tex
	return tex


func _font(file: String) -> FontFile:
	var f := FontFile.new()
	f.load_dynamic_font(ProjectSettings.globalize_path("%s/fonts/%s" % [UI, file]))
	return f


# ---------------------------------------------------------------- debug

func _shots(folder: String) -> void:
	DirAccess.make_dir_recursive_absolute(folder)
	Accounts.account = "pregameshot"                   # a throwaway test account, never the owner's characters
	CharacterStore.remove(Accounts.account, "Brennan")
	var save := func(n: String):
		for i in 30:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("%s/%s.png" % [folder, n])
	await save.call("1_realm")
	var shot_realm := "hib"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shot-realm="):
			shot_realm = a.split("=", true, 1)[1]
	_pick_realm(shot_realm)
	await save.call("2_select")
	_toggle_menu()                                       # the Options window here (as in the game)
	await save.call("2b_options")
	_menu._scroll.scroll_vertical = 100000
	await save.call("2c_options_end")
	_toggle_menu()
	_start_create()
	draft.name = "Brennan"
	_show("create")
	await save.call("3_create")
	_name_edit.text = "Brennan"
	_create_continue()
	await save.call("4_customize")
	if not _figure.meta.get("face_shapes", []).is_empty():
		_figure.set_shape({"nose_tip": 0.8, "cheekbones": 0.8, "chin_point": 0.6, "chin_width": -0.8, "chin_length": 0.2, "eye_size": 0.7})
		draft.look = _figure.look.duplicate(true)
		_tune = "nose"
		_show("customize")
		await save.call("5_shape")
		_tune = ""
	if not (_figure.meta.get("skin_layers", {}) as Dictionary).is_empty():
		_figure.apply({"brows": 2, "freckles": 1, "age_style": 1, "age": 0.6, "scar": 1, "stubble_style": 2, "stubble": 0.9,
				"lip_color": 2, "lip_amt": 0.5, "paint": 0})
		draft.look = _figure.look.duplicate(true)
		_tab = "skin"
		_show("customize")
		await save.call("5_skin")
		_open_picker(Fig3Figure.SCAR_COLORS, 0, func(i): pass, null, func(c): pass, Color(0.8, 0.6, 0.5))
		await save.call("5_skin_picker")
		_open_picker(_skin_colours(), 0, func(i): pass, null, func(c): pass, Color(0.8, 0.6, 0.5), "skin")
		await save.call("5_skin_field")
		if is_instance_valid(_picker):
			_picker.queue_free()
	_tab = "body"
	_body_view = true
	_figure.apply({"body": {"height": 0.5, "shoulders": 0.8, "chest_width": 0.8, "chest_size": 0.8, "waist": -0.7,
			"arms": 0.5, "arm_size": 0.8, "legs": 0.8, "head": -0.5, "thighs": 0.8, "glutes": 0.8}})
	draft.look = _figure.look.duplicate(true)
	_show("customize")
	await save.call("5_body")
	_tab = "face"
	_body_view = false
	_customize_continue()
	await save.call("6_select_with_character")
	CharacterStore.remove(Accounts.account, "Brennan")
	get_tree().quit()


## Where the character is now (owner 2026-10-10: the list showed where characters were made): the zone of its saved
## location, or its start zone before it has played.
var _zone_names := {}


func _where(c: Dictionary) -> String:
	if String(c.get("location_text", "")) != "":         # the server's own words for where the character is
		return String(c.location_text)
	var loc = c.get("location")
	if loc is Dictionary and loc.has("zone"):
		if _zone_names.is_empty():
			var ix = JSON.parse_string(FileAccess.get_file_as_string("res://content/zones/zones_index.json")) 					if FileAccess.file_exists("res://content/zones/zones_index.json") else null
			if ix is Dictionary:
				for k in ix:
					_zone_names[int(k)] = String(ix[k].get("name", ""))
		var n := String(_zone_names.get(int(loc.zone), ""))
		if n != "":
			return n
	return String(CharacterStore.start_of(c).zone_name)
