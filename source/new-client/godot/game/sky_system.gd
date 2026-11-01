class_name SkySystem
extends Node3D
## Day/night, sky dome, lighting, fog and weather for a zone, driven by the client's sky_*.dat (via
## pipeline/build_sky.py -> content/sky/<sky>.json) and the client's world clock:
##   - one game day = 24 game hours; daytime (06:00-18:00) runs at WORLD_DAY_INCREMENT (24) x real time and night
##     (18:00-06:00) 25% faster, so a full day/night is 30 + 24 = 54 real minutes (server DayNightCycleTimer data)
##   - dawn / day / dusk / night colour sets for ambient light, sun light, distance fog, sky rings and cloud rings,
##     each with a clear and a stormy version, blended by time of day and storm level
##   - storms from [storm_system]: every `period` minutes a `percent_chance` roll starts one; rain from [rain]
## Gap-fills (mine, not in the files): how the four colour sets blend across the hours, light strength scaling to
## Godot units, rain drawn as thin streak particles, storm ramp time.

const DAY_INCREMENT := 24.0            # world_day_increment in the 1.65 world's server properties
var day_increment := DAY_INCREMENT     # the clock's speed: the server's own (its Time packet) when it sends one
const NIGHT_FACTOR := 1.25             # night runs 25% faster than day
const LIGHT_SCALE := 1.75              # client light amounts (0..1) to Godot light energy
const AMBIENT_SCALE := 1.4
const UNITS := 0.025                   # DAoC units to metres
# when each colour set is at full strength (game hours); between keys the neighbouring sets cross-fade
const PHASE_KEYS := [[0.0, "night"], [4.5, "night"], [6.0, "dawn"], [7.5, "day"], [16.5, "day"], [18.0, "dusk"],
		[19.5, "night"], [24.0, "night"]]

var zone: ZoneLoader
var region: RegionWorld                # seamless zones: every loaded zone gets the night lights and water light
var sky_name := ""
var data: Dictionary
var game_seconds := 10.0 * 3600.0      # time of day in game seconds
var time_scale := 1.0                  # test speed-up on top of the client's rates
var storm := 0.0                       # current storm level 0..1
var storm_target := 0.0
var storm_forced := -1.0               # tests: -1 = let the storm system decide
var server_driven := false             # the server's weather sets storm_target (ZoneViewer): no storms of our own
var night_level := 0.0                 # 0 day .. 1 night, for lamps and glows (zone lights)
var environment: Environment
var sun: DirectionalLight3D

var _sky_mat: ShaderMaterial
var _tex := {}
var _storm_clock := 0.0
var _storm_seed := RandomNumberGenerator.new()
var _rain: GPUParticles3D
var _rain_ceiling := 10.0              # metres above the player that drops start (sky_*.dat [rain] ceiling)
var _follow: Node3D
var dungeon := false                   # zone.json "dungeon": no sky, sun, day/night or weather (see _setup_dungeon)
var _world: WorldEnvironment


## Zone-only sun shadow splits (owner 2026-10-15: the Grove of Domnann's ground shadows flickered under the canopy as
## you moved - "without modifying all shadows across the whole game"). Measured there at a running pace
## (tests/shadow_flicker_probe.gd, the shadow term alone): the default splits 0.1 / 0.2 / 0.5 jumped 25.9 of 7200
## sampled pixels a step, 0.06 / 0.15 / 0.4 jumped 1.6 (edges about a fifth softer). Every other zone keeps Godot's.
const ZONE_SHADOW_SPLITS := {181: [0.06, 0.15, 0.4]}
const DEFAULT_SHADOW_SPLITS := [0.1, 0.2, 0.5]
## ... and a bigger shadow map there (owner 2026-10-15, after the splits: "there's still shadow flickering" under the
## canopy): the project's 2048 atlas holds the 4 cascades at 1024 each, coarser than the leaf cut-outs whose shadows
## shimmer as the cascades follow you; 4096 doubles every cascade's texels in that zone alone.
const ZONE_SHADOW_ATLAS := {181: 4096}
var _shadow_zone := -1


## The zone you are in now (ZoneViewer, as it changes): its shadow splits on the sun, and its shadow map size.
func set_shadow_zone(zone_id: int) -> void:
	if zone_id == _shadow_zone or sun == null:
		return
	_shadow_zone = zone_id
	var sp: Array = ZONE_SHADOW_SPLITS.get(zone_id, DEFAULT_SHADOW_SPLITS)
	sun.directional_shadow_split_1 = float(sp[0])
	sun.directional_shadow_split_2 = float(sp[1])
	sun.directional_shadow_split_3 = float(sp[2])
	var atlas := int(ZONE_SHADOW_ATLAS.get(zone_id, ProjectSettings.get_setting("rendering/lights_and_shadows/directional_shadow/size", 2048)))
	RenderingServer.directional_shadow_atlas_set_size(atlas, bool(ProjectSettings.get_setting(
			"rendering/lights_and_shadows/directional_shadow/16_bits", true)))


func setup(z: ZoneLoader, follow: Node3D, texture_set := "x4plus") -> void:
	zone = z
	_follow = follow
	var skies: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/sky/zone_skies.json"))
	sky_name = String(skies.get(str(int(z.info.id)), "sky_default"))
	data = JSON.parse_string(FileAccess.get_file_as_string("res://content/sky/%s.json" % sky_name))
	_storm_seed.seed = int(z.info.id) * 7919
	_texture_set = texture_set

	var shader: Shader = load("res://game/sky.gdshader")
	_sky_mat = ShaderMaterial.new()
	_sky_mat.shader = shader
	_apply_sky_data()
	_setup_rest(z)


var _texture_set := "x4plus"


## Seamless zones: you crossed into another zone of the region - its fog, and its sky if the client gives it another.
func set_zone(z: ZoneLoader) -> void:
	zone = z
	if dungeon:
		return
	apply_view()
	var skies: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/sky/zone_skies.json"))
	var nm := String(skies.get(str(int(z.info.id)), "sky_default"))
	if nm != sky_name:
		sky_name = nm
		data = JSON.parse_string(FileAccess.get_file_as_string("res://content/sky/%s.json" % sky_name))
		_apply_sky_data()
	_update(0.0)


## The zone's fog (the client's clip distance per zone) times Options > VIDEO view distance; dungeons keep theirs.
func apply_view() -> void:
	if dungeon or zone == null or environment == null:
		return
	var clip := float(zone.info.fog.clip_m) * ZoneLoader.view_mult
	environment.fog_depth_begin = clip * 0.3
	environment.fog_depth_end = clip * 1.6


func _zones() -> Array:
	if region:
		return region.zones.values()
	return [zone] if zone else []


func _apply_sky_data() -> void:
	var texture_set := _texture_set
	var main: Dictionary = data.get("main", {})
	for pair in [["cloud_top", "cloud_top_texture"], ["cloud_bot", "cloud_bot_texture"], ["cloud_top2", "cloud_top_texture2"],
			["cloud_bot2", "cloud_bot_texture2"], ["sun_disk_tex", "sun_texture"], ["sun_glow_tex", "sunglow_texture"],
			["sun_flare_tex", "sunflare_texture"], ["moon_tex", "moon_texture"], ["moonback_tex", "moonback_texture"],
			["star_tex", "star_texture"]]:
		var file := String(main.get(pair[1], ""))
		if file != "":
			_sky_mat.set_shader_parameter(pair[0], _texture(file, texture_set))
	_sky_mat.set_shader_parameter("cloud_tiles", Vector4(_f(main, "cloud_top_tile", 4), _f(main, "cloud_bot_tile", 5),
			_f(main, "cloud_top_tile2", 4), _f(main, "cloud_bot_tile2", 3)))
	_sky_mat.set_shader_parameter("cloud_speeds", Vector4(_f(main, "cloud_top_speed", 4), _f(main, "cloud_bot_speed", 6),
			_f(main, "cloud_top_speed2", 5), _f(main, "cloud_bot_speed2", 9)))
	_sky_mat.set_shader_parameter("sizes", Vector3(_f(main, "sun_scale", 15), _f(main, "sunglow_scale", 175), _f(main, "sunflare_scale", 175)))
	_sky_mat.set_shader_parameter("moon_size", _f(main, "moon_scale", 15))
	_sky_mat.set_shader_parameter("star_scale", _f(main, "star_scale", 2.5))
	_sky_mat.set_shader_parameter("star_density", _f(main, "max_stars", 700))
	_sky_mat.set_shader_parameter("moon_color", _rgba(main.get("moon_color", [255, 247, 191, 255])))
	_sky_mat.set_shader_parameter("moonback_color", _rgba(main.get("moonback_color", [16, 51, 89, 255])))


func _setup_rest(z: ZoneLoader) -> void:
	var sky := Sky.new()
	sky.sky_material = _sky_mat
	sky.process_mode = Sky.PROCESS_MODE_REALTIME
	environment = Environment.new()
	environment.background_mode = Environment.BG_SKY
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_white = 6.0
	environment.ssao_enabled = true
	environment.fog_enabled = true
	environment.fog_mode = Environment.FOG_MODE_DEPTH
	apply_view()
	environment.fog_sky_affect = 0.2
	var world := WorldEnvironment.new()
	world.environment = environment
	add_child(world)
	_world = world

	sun = DirectionalLight3D.new()
	sun.shadow_enabled = true
	# soft, low-detail shadow maps (no ray tracing): trees cast dappled blobs rather than crisp leaf outlines
	sun.directional_shadow_max_distance = 140.0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_blend_splits = true
	sun.shadow_blur = 2.5
	sun.light_angular_distance = 1.2
	add_child(sun)
	_build_rain()
	dungeon = bool(z.info.get("dungeon", false))
	if dungeon:
		_setup_dungeon()
		return
	_update(0.0)


## A dungeon (owner 2026-10-10: Darkness Falls "has no proper lighting, it's missing all its atmosphere" - it was lit
## like a field at noon under the realm sky). The client draws a dungeon with no sky and no sun: the pieces' own baked
## light (vertex colours, dark maps), the zone's lights.csv lights, and the dungeon's fog from its sector.dat - Darkness
## Falls / Dodens Gruva / Tur Suil purple at amount 85, 125 m; the classic dungeons a light blue-grey haze (15, 400 m).
## Mine (no client numbers): the ambient level, how fog amount maps to the fog's reach, the lights always full.
func _setup_dungeon() -> void:
	sky_name = "dungeon"
	sun.visible = false
	if _rain:
		_rain.emitting = false
		_rain.visible = false
	var fc: Array = zone.info.fog.get("color", [0, 0, 0])
	var fog_color := Color(float(fc[0]), float(fc[1]), float(fc[2]))
	var amount := clampf(float(zone.info.fog.get("amount", 0)) / 100.0, 0.0, 1.0)
	var clip := float(zone.info.fog.get("clip_m", 400.0))
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = fog_color.darkened(0.5)
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.82, 0.8, 0.86).lerp(fog_color, 0.12 + 0.2 * amount)
	environment.ambient_light_energy = 0.75
	environment.fog_light_color = fog_color
	environment.fog_light_energy = 1.0
	environment.fog_depth_begin = clip * 0.05
	environment.fog_depth_end = clip * (2.0 - 1.5 * amount)     # amount 85: 90 m to full fog; 15: ~710 m (a haze)
	environment.fog_depth_curve = 1.0
	if zone:
		zone.set_light_level(1.0)                            # the client's lights burn all day underground
	if remastered:
		_remaster_frame()


func set_hour(h: float) -> void:
	game_seconds = fposmod(h, 24.0) * 3600.0
	if not dungeon:
		_update(0.0)


func hour() -> float:
	return game_seconds / 3600.0


## Night for the old server's IsNightTime: the last and first quarter of the day (18:00 - 6:00).
func is_night() -> bool:
	return hour() < 6.0 or hour() >= 18.0


func clock_text() -> String:
	var h := int(hour())
	var m := int(fposmod(game_seconds / 60.0, 60.0))
	return "%02d:%02d" % [h, m]


func _process(delta: float) -> void:
	if zone and int(zone.info.get("id", -1)) != _look_zone:
		apply_look()
	if dungeon:                                              # the clock still runs (camp timers, night NPCs)
		game_seconds = fposmod(game_seconds + delta * day_increment * time_scale, 86400.0)
		if remastered:
			_remaster_frame()                                # (the mist follows you)
		if _wet_set > 0.0 or _flash > 0.0:
			_weather_off()                                   # (no rain underground: dry, no lightning)
		return
	var h := hour()
	var rate := day_increment * (NIGHT_FACTOR if (h >= 18.0 or h < 6.0) else 1.0)
	game_seconds = fposmod(game_seconds + delta * rate * time_scale, 86400.0)
	_weather(delta * time_scale)
	_update(delta)


func _weather(delta: float) -> void:
	var ss: Dictionary = data.get("storm_system", {})
	var period := _f(ss, "period", 5) * 60.0
	_storm_clock += delta
	if _storm_clock >= period and not server_driven:
		_storm_clock = 0.0
		if _storm_seed.randf() * 100.0 < _f(ss, "percent_chance", 25):
			storm_target = _storm_seed.randf_range(_f(ss, "min_intensity", 0), _f(ss, "max_intensity", 100)) / 100.0
		else:
			storm_target = 0.0
	var target := storm_forced if storm_forced >= 0.0 else storm_target
	storm = move_toward(storm, target, delta / 45.0)          # storms build and clear over ~45 s


func _phase_weights(h: float) -> Dictionary:
	var w := {"dawn": 0.0, "day": 0.0, "dusk": 0.0, "night": 0.0}
	for i in PHASE_KEYS.size() - 1:
		var a: Array = PHASE_KEYS[i]
		var b: Array = PHASE_KEYS[i + 1]
		if h >= a[0] and h <= b[0]:
			var t := (h - float(a[0])) / maxf(float(b[0]) - float(a[0]), 0.001)
			t = t * t * (3.0 - 2.0 * t)
			w[a[1]] += 1.0 - t
			w[b[1]] += t
			break
	return w


func _blend(section: String, key: String, w: Dictionary) -> Variant:
	# clear and stormy versions, each weighted over dawn/day/dusk/night
	var out = null
	for weather in [["clear", 1.0 - storm], ["stormy", storm]]:
		var sec: Dictionary = data.get("%s_%s" % [section, weather[0]], data.get("%s_clear" % section, {}))
		for phase in w:
			var weight: float = w[phase] * weather[1]
			if weight <= 0.0:
				continue
			var v = sec.get("%s_%s" % [phase, key], null)
			if v == null:
				continue
			if v is Array:
				var c := _rgba(v)
				out = c * weight if out == null else out + c * weight
			else:
				out = float(v) * weight if out == null else out + float(v) * weight
	return out


func _update(_delta: float) -> void:
	var h := hour()
	var w := _phase_weights(h)
	night_level = clampf(float(w.night) + 0.5 * (float(w.dawn) + float(w.dusk)) + storm * 0.3, 0.0, 1.0)
	for zl in _zones():
		(zl as ZoneLoader).set_light_level(night_level)
	# sun path: rises in the east at 06:00, highest at noon tilted south by the ecliptic angle, sets west at 18:00
	var tilt := deg_to_rad(_f(data.get("main", {}), "ecliptic_angle", 15))
	var theta := (h - 6.0) / 12.0 * PI
	var sun_dir := Vector3(cos(theta), sin(theta) * cos(tilt), sin(theta) * sin(tilt)).normalized()
	var moon_dir := -sun_dir
	_sky_mat.set_shader_parameter("sun_dir", sun_dir)
	_sky_mat.set_shader_parameter("moon_dir", moon_dir)

	for ring in ["zenith", "nadir"]:
		var c = _blend("canopy_color", ring, w)
		if c != null:
			_sky_mat.set_shader_parameter("canopy_" + ring, c)
	var cz = _blend("cloud_color", "zenith", w)
	if cz != null:
		_sky_mat.set_shader_parameter("cloud_zenith", cz)
	for side in ["east", "west"]:
		var canopy: Array = []
		var cloud: Array = []
		for i in range(1, 5):
			var c1 = _blend("canopy_color", "%s%d" % [side, i], w)
			canopy.append(c1 if c1 != null else Color.BLACK)
			var c2 = _blend("cloud_color", "%s%d" % [side, i], w)
			cloud.append(c2 if c2 != null else Color(1, 1, 1, 0))
		_sky_mat.set_shader_parameter("canopy_" + side, canopy)
		_sky_mat.set_shader_parameter("cloud_" + side, cloud)

	# sun sprites: dawn/dusk colours, noon colours in the day, storm variants by storm level
	var main: Dictionary = data.get("main", {})
	var noon: float = w.day
	for pair in [["sun_disk_color", "sundisk_color"], ["sun_glow_color", "sunglow_color"], ["sun_flare_color", "sunflare_color"]]:
		var low := _rgba(main.get(pair[1], [255, 255, 255, 0])).lerp(_rgba(main.get(pair[1] + "_storm", [0, 0, 0, 0])), storm)
		var high := _rgba(main.get(pair[1] + "_noon", [255, 255, 255, 0])).lerp(_rgba(main.get(pair[1] + "_noon_storm", [0, 0, 0, 0])), storm)
		var c := low.lerp(high, noon)
		c.a *= clampf(sun_dir.y * 6.0 + 0.3, 0.0, 1.0)      # fade as it sinks below the horizon
		_sky_mat.set_shader_parameter(pair[0], c)
	_sky_mat.set_shader_parameter("star_visibility", float(w.night) * (1.0 - storm))
	_sky_mat.set_shader_parameter("storm", storm)
	_sky_mat.set_shader_parameter("cloud_time", Time.get_ticks_msec() / 1000.0)

	# lights and fog from the file
	var amb = _blend("lights_and_fog", "ambient_light", w)
	var amb_amount = _blend("lights_and_fog", "ambient_light_amount", w)
	var dyn = _blend("lights_and_fog", "dynamic_light", w)
	var dyn_amount = _blend("lights_and_fog", "dynamic_light_amount", w)
	var fog = _blend("lights_and_fog", "distance_fog", w)
	if amb != null:
		environment.ambient_light_color = amb
		environment.ambient_light_energy = float(amb_amount if amb_amount != null else 0.5) * AMBIENT_SCALE \
				* (_t("ambient", 1.0) if remastered else 1.0)
	if fog != null:
		environment.fog_light_color = fog
	var light_dir := sun_dir if sun_dir.y > -0.05 else moon_dir     # at night the moon lights the world
	var up := light_dir if light_dir.y > 0.02 else Vector3(light_dir.x, 0.02, light_dir.z).normalized()
	sun.look_at_from_position(Vector3.ZERO, -up, Vector3.UP if absf(up.y) < 0.99 else Vector3.FORWARD)
	if dyn != null:
		sun.light_color = dyn
	var horizon_fade := clampf(absf(light_dir.y) * 5.0, 0.0, 1.0)
	sun.light_energy = float(dyn_amount if dyn_amount != null else 0.6) * LIGHT_SCALE * horizon_fade
	if fog != null:
		for zl in _zones():
			(zl as ZoneLoader).set_water_light(up, sun.light_color, Color(fog).lightened(0.15))
	if _rain:
		_rain.amount_ratio = 0.0 if _snowing() else clampf(storm * 1.2 - 0.15, 0.0, 1.0)   # (snow zones: AmbientLife's snow)
		_rain.emitting = _rain.amount_ratio > 0.01
		if _follow:
			# emit from the client's rain ceiling above the player (following the feet put the emitter at ground
			# level, so every drop fell straight into the terrain and storms showed no rain)
			_rain.global_position = _follow.global_position + Vector3(0.0, _rain_ceiling, 0.0)
	if remastered:
		_remaster_frame(w, sun_dir)
		_weather_fx(_delta, sun_dir)


func _build_rain() -> void:
	var r: Dictionary = data.get("rain", {})
	_rain = GPUParticles3D.new()
	_rain.amount = int(_f(r, "max_drops", 1000))
	var speed := _f(r, "velocity", 500) * UNITS
	var ceiling := _f(r, "ceiling", 400) * UNITS
	var floor_y := _f(r, "floor", -200) * UNITS
	var outer := _f(r, "outer_radius", 800) * UNITS
	_rain_ceiling = ceiling
	_rain.lifetime = (ceiling - floor_y) / maxf(speed, 0.1)
	# the emitter sits at the ceiling and drops fall from there to the floor below the player
	_rain.visibility_aabb = AABB(Vector3(-outer, -(ceiling - floor_y) - 1.0, -outer), Vector3(outer * 2, ceiling - floor_y + 2.0, outer * 2))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(outer, 0.1, outer)
	pm.direction = Vector3(0, -1, 0)
	pm.spread = 2.0
	pm.initial_velocity_min = speed
	pm.initial_velocity_max = speed
	pm.gravity = Vector3.ZERO
	_rain.process_material = pm
	_rain.position.y = ceiling
	var quad := QuadMesh.new()
	quad.size = Vector2(0.02, _f(r, "drop_length", 20) * UNITS)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	mat.billboard_keep_scale = true
	# streak colour: top to bottom colours from the file (alpha fades in toward the bottom of each drop)
	var grad := Gradient.new()
	grad.set_color(0, _rgba(r.get("top_color", [160, 160, 160, 0])))
	grad.set_color(1, _rgba(r.get("bot_color", [160, 160, 160, 64])))
	var gt := GradientTexture2D.new()
	gt.gradient = grad
	gt.fill_from = Vector2(0, 0)
	gt.fill_to = Vector2(0, 1)
	gt.width = 4
	gt.height = 32
	mat.albedo_texture = gt
	mat.albedo_color = Color(1, 1, 1, 1)
	quad.material = mat
	_rain.draw_pass_1 = quad
	_rain.emitting = false
	add_child(_rain)


func _texture(file: String, texture_set: String) -> Texture2D:
	var key := file.to_lower().get_basename()
	if _tex.has(key):
		return _tex[key]
	var path := "res://content/sky/textures/%s/%s.png" % [texture_set, key]
	if not FileAccess.file_exists(path):
		path = "res://content/sky/textures/original/%s.png" % key
	var img := Image.load_from_file(path)
	var t: Texture2D = null
	if img:
		img.generate_mipmaps()
		t = ImageTexture.create_from_image(img)
	_tex[key] = t
	return t


static func _f(d: Dictionary, k: String, fallback: float) -> float:
	var v = d.get(k, fallback)
	return float(v) if not (v is Array) else float(v[0])


static func _rgba(v) -> Color:
	if v is Array:
		var a: float = v[3] if v.size() > 3 else 255.0
		return Color(v[0] / 255.0, v[1] / 255.0, v[2] / 255.0, a / 255.0)
	return Color.WHITE


# ---------------------------------------------------------------- remastered lighting

## REMASTERED LIGHTING (owner 2026-10-28, Options > VIDEO; off = the classic look as above): the same sky files and
## zone fog, drawn with the engine's newer tools -
##   - volumetric fog: a lit haze around you that the sun's shadows cut into shafts under trees, that the zone's
##     torches and fires glow in; its colour is the zone's fog colour of the hour, thicker at dawn, at night and in
##     storms; plus a ground mist (a fog volume that follows you, thinning with height) at dawn and at night.
##     Underground: the dungeon's own fog colour, thicker the foggier the dungeon (Darkness Falls' purple).
##   - the AgX tone curve (bright skies and dark rooms both keep their detail), bloom, indirect light (SSIL),
##     auto exposure (eyes adjusting from a dungeon to daylight, within a narrow range), a little sun glow and sky
##     colour in the far distance fog.
##   - colour grading by realm (Albion warm light / cool shade, Midgard cold, Hibernia green and gold), bluer and
##     paler at night, warmer at dawn and dusk, greyer in storms.
## Every number here is mine (gap-fills, tuned on test shots) - the art tuning is still to come.
var remastered := false
var gi := false                        # real-time bounce light (SDFGI) - Graphics "gi", with remastered only
## Test-shot tuning (--tune=exposure:0.9,fog:0.5 ...): any number below by its key, for comparing looks.
static var tune := {}
static var cli_tune := {}                    # --tune test values: on top of every zone's look
const LOOKS_SHIPPED := "res://game/data/zone_looks.json"
const LOOKS_MINE := "user://world/zone_looks.json"   # the look panel's saves (the save sync carries the world folder)
var _look_zone := -2


## Each zone's tuned look (owner 2026-10-29: art tuning): "default" for every zone, then the zone's own, from the
## shipped file and then yours - the look panel (Ctrl+F12) edits yours. Re-applied when you change zone.
static func looks() -> Dictionary:
	var out := {}
	for path in [LOOKS_SHIPPED, LOOKS_MINE]:
		if FileAccess.file_exists(path):
			var d = JSON.parse_string(FileAccess.get_file_as_string(path))
			if d is Dictionary:
				for k in d:
					if not out.has(k):
						out[k] = {}
					(out[k] as Dictionary).merge(d[k], true)
	return out


func apply_look(force := false) -> void:
	var id := int(zone.info.get("id", -1)) if zone else -1
	if id == _look_zone and not force:
		return
	_look_zone = id
	var all := looks()
	var t := {}
	t.merge(all.get("default", {}), true)
	t.merge(all.get(str(id), {}), true)
	t.merge(cli_tune, true)
	tune = t
	if remastered:
		set_remastered(true)
var _fill_now := Vector3(-1, -1, -1)
var _cam_attr: CameraAttributesPractical
var _mist: FogVolume
var _mist_mat: FogMaterial
var _grade_tex: GradientTexture1D
var _grade_key := ""
var _grade_at := 0
var _fog_glow := -1.0
var _glow_zones := 0

const REALM_GRADES := {
	# shadow tint, highlight tint, saturation, contrast
	# (the AgX curve is a little paler than the classic one: saturation over 1 gives the colour back)
	"alb": [Color(0.96, 0.98, 1.06), Color(1.04, 1.01, 0.96), 1.15, 1.08],
	"mid": [Color(0.94, 0.99, 1.08), Color(0.99, 1.01, 1.04), 1.05, 1.10],
	"hib": [Color(0.95, 1.04, 1.00), Color(1.05, 1.03, 0.94), 1.22, 1.06],
	"": [Color(1, 1, 1), Color(1, 1, 1), 1.1, 1.06],
}


## Graphics.apply_scene: on / off (and again after any graphics change - the classic settings it overrides).
static func _t(key: String, v: float) -> float:
	return float(tune.get(key, v))


## The world shader's remastered values (NifMaterials SHADER_BODY): relief, shine, wind, canopy light - tunable.
func _world_look(on: bool) -> void:
	NifMaterials.ensure_globals()
	RenderingServer.global_shader_parameter_set("remaster_fx", 1.0 if on else 0.0)
	Fig3Figure.sway_on = on                                  # (cloaks and ponytails: Fig3Figure.Sway)
	RenderingServer.global_shader_parameter_set("relief_strength", _t("relief", 0.12))
	RenderingServer.global_shader_parameter_set("shine_strength", _t("shine", 0.6))
	RenderingServer.global_shader_parameter_set("wind_strength", _t("wind", 1.0))
	_wind_set = -1.0                                         # (the weather sets it again with the storm's share)
	RenderingServer.global_shader_parameter_set("foliage_light", _t("foliage", 0.7))
	if not on:
		RenderingServer.global_shader_parameter_set("zone_fill", Vector3.ZERO)


func set_remastered(on: bool) -> void:
	remastered = on
	if environment == null:
		return
	_world_look(on)
	if not on:
		environment.volumetric_fog_enabled = false
		environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
		environment.tonemap_white = 6.0
		environment.tonemap_exposure = 1.0
		environment.adjustment_enabled = false
		environment.fog_sun_scatter = 0.0
		environment.fog_aerial_perspective = 0.0
		environment.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
		environment.sdfgi_enabled = false
		if dungeon:
			environment.ambient_light_energy = 0.75
			environment.fog_light_energy = 1.0
		if sun:
			sun.shadow_blur = 2.5
		if _world:
			_world.camera_attributes = null
		if _mist:
			_mist.visible = false
		_set_extras(false)
		_weather_off()
		if _life:
			_life.off()
		return
	environment.tonemap_mode = Environment.TONE_MAPPER_AGX
	environment.tonemap_exposure = _t("exposure", 0.85)
	environment.tonemap_agx_contrast = _t("agx", 1.4)
	environment.glow_enabled = true
	environment.glow_intensity = _t("glow", 0.5)
	environment.glow_strength = 1.0
	environment.glow_bloom = 0.02
	environment.glow_hdr_threshold = 1.05
	environment.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	environment.ssil_enabled = _t("ssil", 1.0) > 0.0
	environment.volumetric_fog_enabled = true
	environment.volumetric_fog_length = 110.0
	environment.volumetric_fog_anisotropy = _t("aniso", 0.7)     # light scattered forward: shafts toward the sun
	environment.volumetric_fog_ambient_inject = _t("inject", 0.2)   # the shaded fog still lit by the sky
	environment.volumetric_fog_gi_inject = 1.0
	environment.volumetric_fog_sky_affect = 0.15
	environment.volumetric_fog_detail_spread = 2.0
	environment.fog_sun_scatter = 0.0 if dungeon else _t("scatter", 0.12)
	# darker, more threatening underground (owner 2026-10-28): little ambient light, a dim far fog - the dungeon's own
	# torches and fires do the lighting
	if dungeon:
		environment.ambient_light_energy = _t("dungeon_amb", 0.45)
		environment.fog_light_energy = _t("dungeon_fog", 0.6)
	if sun:
		sun.shadow_blur = _t("shadow_blur", 1.2)            # crisper near the caster, softer far off (its angular size)
	# the engine's bounce light replaces the zone's flat ambient light with what it gathers from the sky and the
	# lit surfaces: by day more depth, but at night and underground the zone's ambient tint (Hibernia's purple nights)
	# is lost and the shade goes near black - an option, off by default (owner to judge)
	environment.sdfgi_enabled = gi and not dungeon
	if gi and not dungeon:
		environment.sdfgi_use_occlusion = true
		environment.sdfgi_read_sky_light = not dungeon
		environment.sdfgi_cascades = 4
		environment.sdfgi_min_cell_size = 0.25
		environment.sdfgi_energy = _t("gi", 1.2)
		environment.sdfgi_bounce_feedback = 0.4
	_set_extras(true)
	environment.fog_aerial_perspective = 0.0 if dungeon else _t("aerial", 0.3)
	if _cam_attr == null:
		_cam_attr = CameraAttributesPractical.new()
		_cam_attr.auto_exposure_enabled = _t("ae", 1.0) > 0.0
		_cam_attr.auto_exposure_speed = 0.6
		# a narrow window: dark rooms brightened a little, glare toned down a little - not a different picture
		_cam_attr.auto_exposure_min_sensitivity = _t("aemin", 80.0)
		_cam_attr.auto_exposure_max_sensitivity = _t("aemax", 160.0)
	# (0.4, the engine's, made daylight 40% brighter); underground the eyes adjust less - the dark stays dark
	_cam_attr.auto_exposure_scale = _t("aescale_dungeon", 0.2) if dungeon else _t("aescale", 0.25)
	if _world:
		_world.camera_attributes = _cam_attr
	if _mist == null:
		_mist = FogVolume.new()
		_mist.name = "GroundMist"
		_mist.shape = RenderingServer.FOG_VOLUME_SHAPE_BOX
		_mist.size = Vector3(220.0, 40.0, 220.0)
		_mist_mat = FogMaterial.new()
		_mist_mat.height_falloff = 0.35
		_mist_mat.edge_fade = 0.3
		_mist.material = _mist_mat
		add_child(_mist)
	_mist.visible = true
	_grade_key = ""
	_fog_glow = -1.0
	_remaster_frame(_phase_weights(hour()), Vector3.UP)


func _realm() -> String:
	if zone == null or dungeon:
		return ""
	var id := int(zone.info.id)
	if id < 100:
		return "alb"
	if id < 180:
		return "mid"
	if id < 249:
		return "hib"
	return ""


## Every frame while on: the fog of the hour and weather, the mist where you stand, the colour grade.
func _remaster_frame(w: Dictionary = {}, sun_dir := Vector3.UP) -> void:
	if environment == null or zone == null:
		return
	var amount := clampf(float(zone.info.fog.get("amount", 15)) / 100.0, 0.0, 1.0)
	var dawn := float(w.get("dawn", 0.0))
	var dusk := float(w.get("dusk", 0.0))
	var night := float(w.get("night", 0.0))
	var mist := 0.0
	if dungeon:
		var fc: Array = zone.info.fog.get("color", [0.3, 0.3, 0.35])
		var col := Color(float(fc[0]), float(fc[1]), float(fc[2]))
		environment.volumetric_fog_density = 0.004 + 0.022 * amount   # Darkness Falls (85): 0.023
		environment.volumetric_fog_albedo = col.lerp(Color(0.8, 0.8, 0.85), 0.35)
		environment.volumetric_fog_emission = col * _t("dungeon_emit", 0.004)
		mist = 0.01 + 0.03 * amount
	else:
		var haze := 0.0015 + 0.00012 * amount * 100.0     # the zone's own fog amount: 15 a light haze, 60 thick
		haze *= 1.0 + 2.0 * dawn + 0.5 * night + 0.6 * dusk + 2.0 * storm
		environment.volumetric_fog_density = clampf(haze * _t("fog", 1.0), 0.0005, 0.04)
		# near-white: the light's own colour tints it (the zone fog's blue-grey made a cyan wash)
		environment.volumetric_fog_albedo = environment.fog_light_color.lerp(Color(1, 1, 1), _t("albedo_white", 0.8)) * _t("albedo", 0.85)
		environment.volumetric_fog_emission = environment.fog_light_color * (0.01 * night)
		mist = 0.05 * dawn + 0.025 * night + 0.015 * dusk + 0.02 * storm
		# sunlight lights the haze strongly (shafts); the moon only faintly, and scattered less toward you - a bright
		# moon washed the whole night sky and the ground's colours out (owner 2026-10-28); bloom softer at night
		var day := clampf((sun_dir.y + 0.05) * 8.0, 0.0, 1.0)
		if sun:
			sun.light_volumetric_fog_energy = lerpf(_t("moonfog", 0.15), _t("sunfog", 1.6), day)
		environment.volumetric_fog_anisotropy = lerpf(_t("moon_aniso", 0.3), _t("aniso", 0.7), day)
		environment.glow_intensity = lerpf(_t("glow_night", 0.3), _t("glow", 0.5), day)
	var glow := 1.0 if dungeon else lerpf(_t("lampday", 0.1), 1.0, night_level)
	var zs := _zones()
	if absf(glow - _fog_glow) > 0.02 or zs.size() != _glow_zones:   # (and newly loaded zones of the region)
		_fog_glow = glow
		_glow_zones = zs.size()
		for zl in zs:
			(zl as ZoneLoader).set_fog_glow(glow)
	mist *= _t("mist", 1.0)
	if _mist and _follow:
		_mist_mat.density = mist
		_mist.visible = mist > 0.002
		_mist.global_position = _follow.global_position + Vector3(0.0, 2.0, 0.0)
		_mist_mat.albedo = environment.volumetric_fog_albedo
	_update_grade(night, dawn + dusk)
	# bounce light (SDFGI) replaces the zone's flat ambient light: the zone's own tint is put back on every world
	# surface as a fill the shader adds (owner 2026-10-29: "a real fix" - nights and shade keep their colour)
	var fill := Vector3.ZERO
	if gi and not dungeon and environment.sdfgi_enabled:
		var a := environment.ambient_light_color * environment.ambient_light_energy * _t("fill", 0.85)
		fill = Vector3(a.r, a.g, a.b)
	if fill != _fill_now:
		_fill_now = fill
		RenderingServer.global_shader_parameter_set("zone_fill", fill)
	_life_tick(sun_dir)


func _update_grade(night: float, twilight: float) -> void:
	var now := Time.get_ticks_msec()
	if now < _grade_at and _grade_key != "":
		return
	_grade_at = now + 250
	var g: Array = REALM_GRADES.get(_realm(), REALM_GRADES[""])
	var shadow: Color = g[0]
	var high: Color = g[1]
	var sat := float(g[2]) * _t("sat", 1.0)
	var con := float(g[3]) * _t("con", 1.0)
	shadow = shadow * Color(1, 1, 1).lerp(Color(0.92, 0.96, 1.10), night)
	high = high * Color(1, 1, 1).lerp(Color(1.06, 1.0, 0.9), twilight).lerp(Color(0.96, 0.98, 1.04), night)
	sat *= lerpf(1.0, 0.85, night) * lerpf(1.0, 0.8, storm)
	con *= lerpf(1.0, 0.97, storm)
	var key := "%.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f" % [shadow.r, shadow.g, shadow.b, high.r, high.g, high.b, sat, con]
	if key == _grade_key:
		return
	_grade_key = key
	environment.adjustment_enabled = true
	environment.adjustment_saturation = sat
	environment.adjustment_contrast = con
	environment.adjustment_brightness = 1.0
	# a per-channel curve (the engine's 1D colour correction): each channel x -> x * tint(x), the tint going from
	# the shadow colour in the dark end to the highlight colour in the bright end - split toning
	var grad := Gradient.new()
	var offs := PackedFloat32Array()
	var cols := PackedColorArray()
	for i in 17:
		var x := i / 16.0
		var t := shadow.lerp(high, smoothstep(0.0, 1.0, x))
		offs.append(x)
		cols.append(Color(clampf(x * t.r, 0.0, 1.0), clampf(x * t.g, 0.0, 1.0), clampf(x * t.b, 0.0, 1.0)))
	grad.offsets = offs
	grad.colors = cols
	if _grade_tex == null:
		_grade_tex = GradientTexture1D.new()
		_grade_tex.width = 256
	_grade_tex.gradient = grad
	environment.adjustment_color_correction = _grade_tex


const FxLight := preload("res://game/fx_light.gd")


## The rest of the remastered look outside the sky: the player's belt lantern, flickering fires (and their shadows),
## light from spell and weapon effects.
func _set_extras(on: bool) -> void:
	ZoneLoader.flicker_enabled = on
	FxLight.set_enabled(on)
	for zl in _zones():
		(zl as ZoneLoader).set_remastered_lights(on)
	if _follow and _follow.has_method("set_lantern"):
		_follow.set_lantern(on)


# ---------------------------------------------------------------- remastered weather (claude 2026-10-30)
## The sky's ray-marched clouds (sky.gdshader), thickening and darkening with the storm; the wind in the trees rising
## with it; lightning in heavy storms; the ground and stone getting wet in the rain and drying after. All tunable in the
## look panel (WEATHER); none of it in the classic look.
var _cloud_clock := 0.0
var _wet := 0.0
var _wet_set := -1.0
var _wind_set := -1.0
var _flash := 0.0
var _flash_next := 6.0
var _flash_pulses := 0
var _flash_rng := RandomNumberGenerator.new()
signal lightning(strength: float)        # a lightning flash (ZoneAudio: the thunder after it)


## How hard it rains now: 0 dry .. 1 the heaviest (the rain particles' share).
func rain_amount() -> float:
	return _rain.amount_ratio if _rain and _rain.emitting else 0.0


func _weather_fx(delta: float, sun_dir: Vector3) -> void:
	if dungeon or _sky_mat == null:
		_weather_off()
		return
	var on := _t("clouds", 1.0) > 0.5
	_sky_mat.set_shader_parameter("remaster_clouds", 1.0 if on else 0.0)
	_sky_mat.set_shader_parameter("cloud_full", _t("cloud_full", 0.0))
	_sky_mat.set_shader_parameter("cloud_jitter", _t("cloud_jitter", 1.0))
	if on:
		_sky_mat.set_shader_parameter("cloud_cover", lerpf(_t("cloud_cover", 0.5), 0.97, storm))
		_sky_mat.set_shader_parameter("cloud_storm", storm)
		_cloud_clock += delta * (1.0 + 2.5 * storm) * _t("cloud_speed", 1.0)
		_sky_mat.set_shader_parameter("cloud_clock", _cloud_clock)
		var lit_dir := sun_dir if sun_dir.y > -0.05 else -sun_dir     # the moon at night (the light the sun node carries)
		_sky_mat.set_shader_parameter("cloud_light_dir", lit_dir)
		var light := Color(0, 0, 0)
		var day := clampf((sun_dir.y + 0.05) * 6.0, 0.0, 1.0)
		if sun:                                                   # (moonlit clouds dimmer than the moonlit ground)
			light = sun.light_color * clampf(sun.light_energy, 0.0, 3.0) * _t("cloud_sun", 0.9) * lerpf(0.4, 1.0, day)
		_sky_mat.set_shader_parameter("cloud_sun", Vector3(light.r, light.g, light.b))
		var zen: Color = _sky_mat.get_shader_parameter("canopy_zenith") if _sky_mat.get_shader_parameter("canopy_zenith") is Color else Color(0.5, 0.6, 0.7)
		var grey := zen.get_luminance()
		var amb := zen.lerp(Color(grey, grey, grey), 0.45) * _t("cloud_shade", 1.1) * lerpf(0.6, 1.0, day)
		_sky_mat.set_shader_parameter("cloud_amb", Vector3(amb.r, amb.g, amb.b))
	# lightning: a heavy storm's flashes, one to three flickers each
	var bolts := _t("lightning", 1.0)
	if storm > 0.6 and bolts > 0.0 and not _snowing():
		_flash_next -= delta
		if _flash_next <= 0.0:
			_flash_pulses = _flash_rng.randi_range(1, 3)
			_flash = _flash_rng.randf_range(0.6, 1.0)
			lightning.emit(_flash)
			_flash_next = _flash_rng.randf_range(5.0, 16.0) / maxf(storm, 0.6)
	if _flash > 0.0:
		_flash = maxf(_flash - delta * 7.0, 0.0)
		if _flash == 0.0 and _flash_pulses > 1:
			_flash_pulses -= 1
			_flash = _flash_rng.randf_range(0.4, 0.9)
	_sky_mat.set_shader_parameter("flash", _flash * bolts)
	if _flash > 0.0:
		environment.ambient_light_energy += _flash * bolts * 0.9
	# the wind picks up with the storm
	var wind := _t("wind", 1.0) * (1.0 + _t("storm_wind", 1.5) * storm)
	if absf(wind - _wind_set) > 0.01:
		_wind_set = wind
		RenderingServer.global_shader_parameter_set("wind_strength", wind)
		Fig3Figure.wind = wind
	_water_fx(sun_dir)
	_night_sky(sun_dir)
	# wet in the rain (a minute to soak), dry after it (three minutes)
	var raining := _rain.amount_ratio if _rain and _rain.emitting else 0.0
	var target := clampf(raining * 1.6, 0.0, 1.0)
	_wet = move_toward(_wet, target, delta / (60.0 if target > _wet else 180.0))
	var wet := _wet * _t("wet", 1.0)
	if absf(wet - _wet_set) > 0.004:
		_wet_set = wet
		RenderingServer.global_shader_parameter_set("wetness", wet)


## Life in the air (AmbientLife): fireflies, falling leaves, snow, dungeon dust round the player.
const AmbientLife := preload("res://game/ambient_life.gd")
var _life: AmbientLife


func _snowing() -> bool:
	return remastered and zone != null and not dungeon and AmbientLife.snowy(int(zone.info.get("id", -1)))


func _life_tick(sun_dir: Vector3) -> void:
	if _life == null:
		_life = AmbientLife.new()
		_life.name = "AmbientLife"
		add_child(_life)
	var at: Vector3                                          # round the camera (what sees them), else the player
	var cam := get_viewport().get_camera_3d()
	if cam:
		at = cam.global_position
	elif _follow:
		at = _follow.global_position
	else:
		return
	var daylight := clampf((sun_dir.y + 0.05) * 6.0, 0.0, 1.0)
	if "--life-log" in OS.get_cmdline_user_args() and Engine.get_process_frames() % 120 == 0:
		print("[life] zone %s storm %.2f snowing %s night %.2f at %s" % [zone.info.get("id"), storm, _snowing(), night_level, at])
	_life.tick(at, _zones(), int(zone.info.get("id", -1)), dungeon, night_level, storm,
			_wind_set if _wind_set > 0.0 else 1.0, daylight, Callable(self, "_t"), _realm())


## The night sky (remastered): the moon's phases - a cycle of eight game days, its light waxing and waning with it -
## and in Midgard (and Snowdonia) the northern lights on some clear nights, stronger on some than others.
var moon_illumination := 1.0


func _night_sky(sun_dir: Vector3) -> void:
	var days := Time.get_unix_time_from_system() * day_increment / 86400.0
	var ph := fposmod(days / _t("moon_cycle", 8.0) + 0.5, 1.0)
	if _t("moon_phase", -1.0) >= 0.0:                         # tests: --tune=moon_phase:0.25
		ph = _t("moon_phase", 0.5)
	moon_illumination = (1.0 - cos(ph * TAU)) * 0.5
	_sky_mat.set_shader_parameter("moon_phase_on", 1.0)
	_sky_mat.set_shader_parameter("moon_phase", ph)
	if sun and sun_dir.y <= -0.05:                            # the moon lights the night: less of it, less light
		sun.light_energy *= lerpf(_t("newmoon_light", 0.4), 1.0, moon_illumination)
	# the northern lights: Midgard's, or a snow zone's, clear nights; how strong is the night's own (hashed by date)
	var a := 0.0
	if _realm() == "mid" or AmbientLife.snowy(int(zone.info.get("id", -1))):
		var night_no := roundf(days - fposmod(hour() - 12.0, 24.0) / 24.0)   # (one number from noon to the next noon)
		var h := fposmod(sin(night_no * 12.9898) * 43758.5453, 1.0)
		var strength := smoothstep(0.3, 0.85, h)
		if _t("aurora_force", -1.0) >= 0.0:
			strength = _t("aurora_force", 1.0)
		var dark := clampf(-sun_dir.y * 6.0, 0.0, 1.0)
		a = strength * dark * clampf(1.0 - storm * 2.5, 0.0, 1.0) * _t("aurora", 1.0)
	_sky_mat.set_shader_parameter("aurora", a)
	_sky_mat.set_shader_parameter("aurora_time", Time.get_ticks_msec() / 1000.0)


## The remastered water (owner 2026-10-31): its sky, rain rings and light, and the murk when the camera is under it.
const UNDERWATER_SHADER := preload("res://game/underwater.gdshader")
var _under: MeshInstance3D
var _under_mat: ShaderMaterial


func _water_fx(sun_dir: Vector3) -> void:
	var zen: Color = _sky_mat.get_shader_parameter("canopy_zenith") if _sky_mat.get_shader_parameter("canopy_zenith") is Color else Color(0.35, 0.5, 0.7)
	var day := clampf((sun_dir.y + 0.05) * 6.0, 0.0, 1.0)
	var lit := lerpf(_t("water_night", 0.22), 1.0, day) * lerpf(1.0, 0.6, storm)
	var murk := Color(0.08, 0.19, 0.19).lerp(Color(0.05, 0.09, 0.1), storm) * lit * _t("murk", 1.0)
	var rain := rain_amount() * _t("ripples", 1.0)
	for zl in _zones():
		(zl as ZoneLoader).set_water_weather(zen, rain, lit, storm, murk)
	_underwater(murk)


## The murk veil in front of the camera while it is below the surface of the water it is in.
func _underwater(murk: Color) -> void:
	var cam := get_viewport().get_camera_3d() if is_inside_tree() else null
	if _under and not is_instance_valid(_under):           # (it went with a camera that was freed)
		_under = null
	var under := false
	var level := 0.0
	if cam and remastered and not dungeon:
		var p := cam.global_position
		for zl in _zones():
			var z := zl as ZoneLoader
			var lx := p.x - z.global_position.x
			var lz := p.z - z.global_position.z
			var size := float(z.info.get("size_m", 0.0))
			if lx >= 0.0 and lz >= 0.0 and lx < size and lz < size:
				level = z.water_level_at(lx, lz) + z.global_position.y
				under = p.y < level - 0.05
				break
	if under and _under == null:
		_under_mat = ShaderMaterial.new()
		_under_mat.shader = UNDERWATER_SHADER
		_under_mat.render_priority = 100
		_under = MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(1, 1)
		_under.mesh = q
		_under.material_override = _under_mat
		_under.extra_cull_margin = 16384.0
		_under.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if _under:
		if under and _under.get_parent() != cam:
			if _under.get_parent():
				_under.get_parent().remove_child(_under)
			cam.add_child(_under)
			_under.position = Vector3(0, 0, -0.5)
		_under.visible = under
		if under:
			_under_mat.set_shader_parameter("murk_color", murk)
			_under_mat.set_shader_parameter("surface_y", level)
			_under_mat.set_shader_parameter("visibility_m", _t("underwater_m", 14.0) * lerpf(1.0, 0.6, storm))


func _weather_off() -> void:
	if _sky_mat:
		_sky_mat.set_shader_parameter("aurora", 0.0)
		_sky_mat.set_shader_parameter("moon_phase_on", 0.0)
		_sky_mat.set_shader_parameter("remaster_clouds", 0.0)
		_sky_mat.set_shader_parameter("flash", 0.0)
	_flash = 0.0
	if _under and is_instance_valid(_under):
		_under.visible = false
	if _wet_set != 0.0:
		_wet_set = 0.0
		RenderingServer.global_shader_parameter_set("wetness", 0.0)
	_wind_set = -1.0
