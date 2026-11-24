extends Node
## Fog patches (owner 2026-11-21, marking the haunted forest's edges in Lough Derg with /zmark: "make the area in between
## the notes that say 'Haunted Forest Edge <direction>' be very foggy, like a heavy mist in it that makes it harder to
## see. Have it be a less during the day, but at night have it be very foggy" - and "we have it get more foggy near the
## edge of the map, so maybe this region can be foggy like that?"). Made like the world's edge fog (EdgeVeil): a fog
## box riding with the camera whose shader is thick only inside the patch's outline - a polygon in zone units, from
## game/data/fog_patches.json - thinning over edge_m at its border. Inside, the distance fog also closes in, so it hides
## what's far off with or without Remastered Lighting (the volumetric mist itself needs Remastered Lighting).
## Day and night: day x the patch's density by day, full at night, following the sky's night level.

const DATA := "res://game/data/fog_patches.json"
const UNITS := 0.025                         # DAoC units to metres
const MAX_PTS := 24

var region: RegionWorld
var sky: SkySystem
var _patches := {}                           # zone id (int) -> [patch dicts]
var _vols := {}                              # "zone:i" -> FogVolume
var _deep := 0.0                             # how far inside a patch the camera is now (0..1), for the distance fog
var _was_deep := false
var _sky_affect := 1.0
const MIST_NIGHT := Color(0.13, 0.15, 0.18)
var _debug := "--fogdebug" in OS.get_cmdline_user_args()
## "lift": a patch the server can lift (King Lug's campaign: the Cursed Forest's fog while the Host holds it - the #SIEGE
## line's "lift" list, event_tracker.gd). It fades out over ~20 s, and back in when the line stops saying so.
const ET := preload("res://game/ui/event_tracker.gd")
var _lift := {}                              # lift key -> 0 (fog) .. 1 (lifted)
var _debug_at := 0


func setup(r: RegionWorld) -> void:
	region = r
	process_priority = 100                   # after the sky has set its fog for the frame
	var f := FileAccess.open(DATA, FileAccess.READ)
	if f == null:
		return
	var d = JSON.parse_string(f.get_as_text())
	if d is Dictionary:
		for k in d:
			_patches[int(k)] = d[k]


func _process(dt: float) -> void:
	var t_live := Time.get_ticks_usec()
	_process_timed(dt)
	Perf.proc_add("fog patches", Time.get_ticks_usec() - t_live)


func _process_timed(_dt: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if region == null or cam == null or _patches.is_empty():
		return
	if sky == null and region.viewer:
		sky = region.viewer.get("sky")
	var night := sky.night_level if sky else 0.0
	var deep := 0.0
	var dense := 0.0
	var dense_end := 45.0
	_update_lifts(_dt)
	var seen := {}
	for zid in _patches:
		var zl: ZoneLoader = region.zones.get(zid)
		if zl == null or not is_instance_valid(zl):
			continue
		var list: Array = _patches[zid]
		for i in list.size():
			var p: Dictionary = list[i]
			var pts := PackedVector2Array()
			for q in p.get("points", []):
				var w := zl.to_global(Vector3(float(q[0]) * UNITS, 0.0, float(q[1]) * UNITS))
				pts.append(Vector2(w.x, w.z))
			if pts.size() < 3:
				continue
			var edge := float(p.get("edge_m", 40.0))
			var here := Vector2(cam.global_position.x, cam.global_position.z)
			var sd := _signed_dist(here, pts)
			var key := "%d:%d" % [zid, i]
			seen[key] = true
			var vol: FogVolume = _vols.get(key)
			var near := sd < 200.0                      # within the fog box's reach of the outline
			if vol == null:
				vol = _make_volume(p)
				_vols[key] = vol
			var strength := _strength(p, night)
			if p.has("lift"):
				strength *= 1.0 - float(_lift.get(String(p["lift"]), 0.0))
			if strength < 0.02:                         # a night-only mist by day: none at all
				near = false
			vol.visible = near
			if near:
				var m := vol.material as ShaderMaterial
				var arr := PackedVector2Array(pts)
				arr.resize(MAX_PTS)
				m.set_shader_parameter("pts", arr)
				m.set_shader_parameter("count", mini(pts.size(), MAX_PTS))
				m.set_shader_parameter("density", float(p.get("density", 0.07)) * strength)
				m.set_shader_parameter("night", clampf(night, 0.0, 1.0) * float(p.get("night_glow", 1.0)))
				m.set_shader_parameter("base_y", zl.global_position.y + float(p.get("floor", 0.0)) * UNITS - 4.0)
				if sky and sky.environment:
					m.set_shader_parameter("glow", sky.environment.fog_light_color)
				vol.global_position = cam.global_position
			var k := clampf(-sd / edge, 0.0, 1.0) if strength >= 0.02 else 0.0
			if k > deep:
				deep = k
				dense = strength
				dense_end = float(p.get("end_m", 45.0))
	for key in _vols.keys():
		if not seen.has(key):
			_vols[key].queue_free()
			_vols.erase(key)
	_deep = deep
	_distance_fog(deep, dense, dense_end)
	if _debug and Time.get_ticks_msec() > _debug_at:
		_debug_at = Time.get_ticks_msec() + 1000
		print("[fog] vols %d deep %.2f strength %.2f night %.2f cam %s end %.1f" % [_vols.size(), deep, dense, night,
			str(cam.global_position), sky.environment.fog_depth_end if sky and sky.environment else -1.0])


## Inside a patch the distance fog closes in: at night to about night_end_m, by day to day_end_m (the zone's own
## fog everywhere else, put back on the way out).
func _distance_fog(deep: float, strength: float, night_end := 45.0) -> void:
	if sky == null or sky.environment == null or sky.dungeon:
		return
	var env := sky.environment
	if deep <= 0.001:
		if _was_deep:
			_was_deep = false
			sky.apply_view()
			env.fog_sky_affect = _sky_affect
		return
	if not _was_deep:
		_was_deep = true
		_sky_affect = env.fog_sky_affect
	sky.apply_view()                                    # the zone's own fog, then pulled in from it
	var end_m := lerpf(160.0, night_end, strength)      # day (strength ~0.35): ~120 m; night: 45 m (a patch's "end_m": its own)
	env.fog_depth_end = lerpf(env.fog_depth_end, end_m, deep)
	env.fog_depth_begin = lerpf(env.fog_depth_begin, 2.0, deep)
	# the far side of the mist is mist, not dark: at night it fades to a pale grey-blue, and hides the sky
	var mist := MIST_NIGHT.lerp(env.fog_light_color, 1.0 - clampf(sky.night_level, 0.0, 1.0))
	env.fog_light_color = env.fog_light_color.lerp(mist, deep)
	env.fog_sky_affect = lerpf(_sky_affect, 1.0, deep * strength)


func _update_lifts(dt: float) -> void:
	var on: Array = []
	if not ET.siege_info.is_empty() and Time.get_ticks_msec() - ET.siege_ms < 15000:
		var l = ET.siege_info.get("lift", [])
		if l is Array:
			on = l
	var keys := {}
	for zid in _patches:
		for p in _patches[zid]:
			if p.has("lift"):
				keys[String(p["lift"])] = true
	for key in keys:
		var target := 1.0 if on.has(key) else 0.0
		var cur := float(_lift.get(key, target))
		_lift[key] = move_toward(cur, target, dt / 20.0)


## How thick a patch is now (0..1). Default: day x density by day, full at night. "when": "dawn" (owner 2026-11-24,
## Connla: "deep fog in the mornings... clear at day and night"): only round sunrise - in from 04:00, full 05:00-07:30,
## gone by 09:00 - at the patch's "dawn" strength (default 1).
func _strength(p: Dictionary, night: float) -> float:
	if str(p.get("when", "")) == "dawn":
		var h: float = sky.hour() if sky else 12.0
		var w := clampf(h - 4.0, 0.0, 1.0) * (1.0 - clampf((h - 7.5) / 1.5, 0.0, 1.0)) if h < 9.0 else 0.0
		return float(p.get("dawn", 1.0)) * w
	return lerpf(float(p.get("day", 0.35)), 1.0, clampf(night, 0.0, 1.0))


## Distance from p to the outline: negative inside.
static func _signed_dist(p: Vector2, pts: PackedVector2Array) -> float:
	var d := INF
	var inside := false
	var n := pts.size()
	var j := n - 1
	for i in n:
		var a := pts[i]
		var b := pts[j]
		var e := b - a
		var t := clampf((p - a).dot(e) / maxf(e.length_squared(), 0.0001), 0.0, 1.0)
		d = minf(d, (p - (a + e * t)).length())
		if (a.y > p.y) != (b.y > p.y) and p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x:
			inside = not inside
		j = i
	return -d if inside else d


func _make_volume(p: Dictionary) -> FogVolume:
	var m := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = FOG_SHADER
	m.shader = sh
	m.set_shader_parameter("edge_m", float(p.get("edge_m", 40.0)))
	m.set_shader_parameter("height_m", float(p.get("height_m", 30.0)))
	var c: Array = p.get("color", [0.78, 0.82, 0.86])
	m.set_shader_parameter("albedo", Color(float(c[0]), float(c[1]), float(c[2])))
	var v := FogVolume.new()
	v.name = "FogPatch"
	v.shape = RenderingServer.FOG_VOLUME_SHAPE_BOX
	v.size = Vector3(300.0, 300.0, 300.0)               # past the volumetric fog's 110 m reach all round
	v.material = m
	add_child(v)
	return v


const FOG_SHADER := """
shader_type fog;
uniform vec2 pts[24];
uniform int count;
uniform float density;
uniform float edge_m = 40.0;
uniform float base_y;
uniform float height_m = 30.0;
uniform vec3 albedo : source_color = vec3(0.78, 0.82, 0.86);
uniform vec3 glow : source_color = vec3(0.6, 0.7, 0.8);
uniform float night = 0.0;
uniform vec3 ghost : source_color = vec3(0.3, 0.36, 0.42);   // at night the mist gives off a faint pale light of its own
float sdist(vec2 p) {
	float d = 1e9;
	bool inside = false;
	for (int i = 0; i < 24; i++) {
		if (i >= count) break;
		int j = (i == 0) ? count - 1 : i - 1;
		vec2 a = pts[i];
		vec2 b = pts[j];
		vec2 e = b - a;
		float t = clamp(dot(p - a, e) / max(dot(e, e), 0.0001), 0.0, 1.0);
		d = min(d, length(p - (a + e * t)));
		if (((a.y > p.y) != (b.y > p.y)) && (p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x)) inside = !inside;
	}
	return inside ? -d : d;
}
void fog() {
	vec3 w = WORLD_POSITION;
	float k = clamp(-sdist(w.xz) / edge_m, 0.0, 1.0);
	k = k * k * (3.0 - 2.0 * k);
	// low and drifting: thickest near the ground, thinning upward; slow rolling lumps so it isn't a flat wall
	float h = 1.0 - smoothstep(0.0, height_m, w.y - base_y);
	float roll = 0.75 + 0.25 * sin(w.x * 0.045 + TIME * 0.18) * sin(w.z * 0.05 - TIME * 0.13 + w.x * 0.01);
	DENSITY = density * k * h * roll;
	ALBEDO = albedo;
	EMISSION = mix(glow * 0.15, ghost, night) * k * roll;
}
"""
