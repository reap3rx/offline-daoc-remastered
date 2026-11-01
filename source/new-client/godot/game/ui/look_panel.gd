# (no class_name: preloaded where used - new scripts are not in the class cache)
extends CanvasLayer
## The look panel (/look; owner 2026-10-29: art tuning): sliders for the remastered look - fog and mist, exposure
## and colour, glow, the world's surfaces, trees, bounce light - changed live, for this zone or for every zone, and
## saved in user://world/zone_looks.json (SkySystem.looks: the shipped looks, then yours). Remastered Lighting only.

const SkySystemScript := preload("res://game/sky_system.gd")

## [key, label, min, max, default] (SkySystem / NifMaterials defaults) - headings are [title]
const KNOBS := [
	["LIGHT AND COLOUR"],
	["exposure", "Exposure", 0.4, 1.6, 0.85],
	["agx", "Contrast (tone curve)", 1.0, 2.0, 1.4],
	["con", "Contrast (grade)", 0.7, 1.3, 1.0],
	["sat", "Saturation", 0.4, 1.6, 1.0],
	["ambient", "Ambient light", 0.3, 2.0, 1.0],
	["aescale", "Eyes adjusting (outdoors)", 0.0, 0.8, 0.25],
	["FOG AND MIST"],
	["fog", "Haze thickness", 0.0, 3.0, 1.0],
	["mist", "Ground mist", 0.0, 3.0, 1.0],
	["sunfog", "Sun shafts", 0.0, 3.0, 1.6],
	["moonfog", "Moonlight in the haze", 0.0, 1.0, 0.15],
	["scatter", "Glare round the sun", 0.0, 0.5, 0.12],
	["aerial", "Distance takes the sky's colour", 0.0, 1.0, 0.3],
	["GLOW"],
	["glow", "Bloom by day", 0.0, 1.5, 0.5],
	["glow_night", "Bloom at night", 0.0, 1.5, 0.3],
	["lampday", "Lamps glowing in the haze by day", 0.0, 1.0, 0.1],
	["SURFACES AND TREES"],
	["relief", "Surface relief", 0.0, 0.4, 0.12],
	["shine", "Shine on light parts", 0.0, 1.5, 0.6],
	["wind", "Wind in trees", 0.0, 3.0, 1.0],
	["foliage", "Rounded canopy light", 0.0, 1.0, 0.7],
	["WEATHER"],
	["clouds", "Volumetric clouds (on / off)", 0.0, 1.0, 1.0],
	["cloud_cover", "Cloud cover in fair weather", 0.0, 1.0, 0.5],
	["cloud_speed", "Cloud speed", 0.0, 4.0, 1.0],
	["cloud_sun", "Sunlight on the clouds", 0.0, 2.0, 0.9],
	["cloud_shade", "Cloud shadow side brightness", 0.0, 2.0, 1.1],
	["storm_wind", "Wind rising in storms", 0.0, 4.0, 1.5],
	["lightning", "Lightning in heavy storms", 0.0, 2.0, 1.0],
	["wet", "Wet ground in the rain", 0.0, 1.5, 1.0],
	["LIFE IN THE AIR / NIGHT SKY"],
	["fireflies", "Fireflies on clear nights", 0.0, 1.0, 1.0],
	["fairy", "Hibernian fairies (chance)", 0.0, 3.0, 1.0],
	["leaves", "Falling leaves", 0.0, 1.0, 1.0],
	["snow", "Snow in snow-zone storms", 0.0, 1.0, 1.0],
	["dust", "Dust in dungeons", 0.0, 1.0, 1.0],
	["aurora", "Northern lights strength", 0.0, 2.0, 1.0],
	["newmoon_light", "Moonlight at new moon", 0.0, 1.0, 0.4],
	["DUNGEONS"],
	["dungeon_amb", "Dungeon ambient", 0.0, 1.2, 0.45],
	["dungeon_fog", "Dungeon fog light", 0.0, 1.5, 0.6],
	["dungeon_emit", "Dungeon fog glow", 0.0, 0.02, 0.004],
	["BOUNCE LIGHT (SDFGI)"],
	["gi", "Bounce light strength", 0.0, 3.0, 1.2],
	["fill", "Zone tint kept under it", 0.0, 2.0, 0.85],
]

var viewer: Node
var _panel: PanelContainer
var _scope: OptionButton
var _rows := {}                              # key -> [HSlider, Label]
var _mine := {}                              # user://world/zone_looks.json as it is being edited
var _title: Label
var _quiet := false


func setup(v: Node) -> void:
	viewer = v
	layer = 20
	visible = false
	_panel = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.05, 0.04, 0.92)
	sb.border_color = Color(0.55, 0.45, 0.25)
	sb.set_border_width_all(1)
	sb.set_content_margin_all(10)
	_panel.add_theme_stylebox_override("panel", sb)
	_panel.position = Vector2(20, 60)
	_panel.custom_minimum_size = Vector2(430, 0)
	add_child(_panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 3)
	_panel.add_child(box)
	_title = Label.new()
	_title.add_theme_color_override("font_color", Color(1.0, 0.85, 0.45))
	box.add_child(_title)
	var top := HBoxContainer.new()
	box.add_child(top)
	_scope = OptionButton.new()
	_scope.add_item("This zone")
	_scope.add_item("All zones")
	_scope.item_selected.connect(func(_i): _refresh())
	top.add_child(_scope)
	for b in [["Save", _save], ["Reset", _reset], ["Close", func(): toggle()]]:
		var btn := Button.new()
		btn.text = b[0]
		btn.pressed.connect(b[1])
		top.add_child(btn)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(410, 520)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	box.add_child(scroll)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(list)
	for k in KNOBS:
		if (k as Array).size() == 1:
			var h := Label.new()
			h.text = String(k[0])
			h.add_theme_color_override("font_color", Color(0.85, 0.7, 0.4))
			list.add_child(h)
			continue
		var row := HBoxContainer.new()
		var lbl := Label.new()
		lbl.text = String(k[1])
		lbl.custom_minimum_size = Vector2(190, 0)
		lbl.add_theme_font_size_override("font_size", 12)
		row.add_child(lbl)
		var s := HSlider.new()
		s.min_value = float(k[2])
		s.max_value = float(k[3])
		s.step = (float(k[3]) - float(k[2])) / 200.0
		s.custom_minimum_size = Vector2(150, 0)
		s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(s)
		var val := Label.new()
		val.custom_minimum_size = Vector2(50, 0)
		val.add_theme_font_size_override("font_size", 12)
		row.add_child(val)
		var key := String(k[0])
		s.value_changed.connect(func(x: float): _changed(key, x))
		_rows[key] = [s, val]
		list.add_child(row)
	var hint := Label.new()
	hint.text = "Changes show at once. Save keeps them (this computer, and your others through the save sync)."
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.custom_minimum_size = Vector2(410, 0)
	hint.add_theme_font_size_override("font_size", 11)
	box.add_child(hint)


func toggle() -> void:
	visible = not visible
	if visible:
		_load_mine()
		_refresh()
	elif not _mine.is_empty():
		_save()


func _sky() -> SkySystem:
	return viewer.get("sky") if viewer else null


func _zone_key() -> String:
	var s := _sky()
	return str(int(s.zone.info.get("id", -1))) if s and s.zone else "default"


func _scope_key() -> String:
	return _zone_key() if _scope.selected == 0 else "default"


func _refresh() -> void:
	var s := _sky()
	var zn := String(s.zone.info.get("name", "?")) if s and s.zone else "?"
	_title.text = "LOOK - %s%s" % [zn, "" if (s and s.remastered) else "   (turn on Remastered Lighting to see it)"]
	_quiet = true
	for k in KNOBS:
		if (k as Array).size() == 1:
			continue
		var key := String(k[0])
		var v := SkySystem._t(key, float(k[4]))
		(_rows[key][0] as HSlider).value = v
		_show(key, v)
	_quiet = false


func _show(key: String, v: float) -> void:
	var mine: Dictionary = _mine.get(_scope_key(), {})
	(_rows[key][1] as Label).text = ("%.3f" % v) + (" *" if mine.has(key) else "")


func _changed(key: String, v: float) -> void:
	if _quiet:
		return
	var sk := _scope_key()
	if not _mine.has(sk):
		_mine[sk] = {}
	_mine[sk][key] = snappedf(v, 0.0001)
	SkySystem.tune[key] = v
	_show(key, v)
	var s := _sky()
	if s:
		s.set_remastered(s.remastered)                  # (the values set once per change; the rest read every frame)


func _reset() -> void:
	_mine.erase(_scope_key())
	_write()
	var s := _sky()
	if s:
		_sky_reload(s)
	_refresh()


func _save() -> void:
	_write()
	PlayerData.message.emit("Look saved (%s)." % ("this zone" if _scope.selected == 0 else "all zones"), "system")


func _write() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SkySystem.LOOKS_MINE.get_base_dir()))
	var f := FileAccess.open(SkySystem.LOOKS_MINE, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_mine, "\t"))


func _load_mine() -> void:
	_mine = {}
	if FileAccess.file_exists(SkySystem.LOOKS_MINE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(SkySystem.LOOKS_MINE))
		if d is Dictionary:
			_mine = d


func _sky_reload(s: SkySystem) -> void:
	s.apply_look(true)
