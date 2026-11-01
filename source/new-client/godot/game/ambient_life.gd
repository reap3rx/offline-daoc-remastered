extends Node3D
## Life in the air (owner 2026-10-31, the remastered look only): fireflies over the grass on clear nights, leaves
## drifting down from the broadleaf trees around you (more in the wind), snow instead of rain in the snowy zones'
## storms, and dust motes hanging in the air underground, glinting where a torch lights them. All GPU particles round
## the player, left in the world as you move (they don't follow you about). SkySystem owns it and calls tick().

## Zones whose storms snow instead of rain: Midgard's snowfields and Albion's Snowdonia (their ground textures are
## mostly snow - content/zones/*/zone.json), Gripklosa and the Tuscaran Glacier in Aegirhamn.
const SNOW_ZONES := [12, 102, 108, 111, 112, 113, 115, 152, 160]

var fireflies: GPUParticles3D
var leaves: GPUParticles3D
var snow: GPUParticles3D
var dust: GPUParticles3D
var _leaf_at := Vector3(INF, 0, INF)        # where the leaves' trees were last gathered
var _leaf_points := 0
var _snow_mat: StandardMaterial3D


static func snowy(zone_id: int) -> bool:
	return zone_id in SNOW_ZONES


func _ready() -> void:
	fireflies = _fireflies()
	leaves = _leaves()
	snow = _snow()
	dust = _dust()
	for p in [fireflies, leaves, snow, dust]:
		p.emitting = false
		add_child(p)


## Every frame: where you are, the hour, the weather. tune: SkySystem._t (the /look panel and --tune keys).
func tick(at: Vector3, zones: Array, zone_id: int, dungeon: bool, night: float, storm: float, wind: float,
		daylight: float, tune: Callable) -> void:
	var snowing := snowy(zone_id) and not dungeon
	# fireflies: clear, calm nights outdoors, not in the snow
	var ff := 0.0
	if not dungeon and not snowing:
		ff = smoothstep(0.55, 0.9, night) * clampf(1.0 - storm * 3.0, 0.0, 1.0) * float(tune.call("fireflies", 1.0))
	_run(fireflies, ff)
	if ff > 0.0:
		fireflies.global_position = at + Vector3(0.0, 1.2, 0.0)
	# leaves from the broadleaf trees within reach (gathered again every 15 m you move)
	if not dungeon and at.distance_to(_leaf_at) > 15.0:
		_leaf_at = at
		_gather_trees(at, zones)
	var lv := 0.0
	if not dungeon and not snowing and _leaf_points > 0:
		lv = clampf(0.25 + 0.3 * wind, 0.0, 1.0) * float(tune.call("leaves", 1.0))
	_run(leaves, lv)
	# snow: the storm's share, as the rain would have been
	var sn := 0.0
	if snowing:
		sn = clampf(storm * 1.3 - 0.1, 0.0, 1.0) * float(tune.call("snow", 1.0))
	_run(snow, sn)
	if sn > 0.0:
		snow.global_position = at + Vector3(0.0, 5.0, 0.0)
		var b := lerpf(0.6, 1.0, daylight)
		_snow_mat.albedo_color = Color(b, b, b * 1.04, 0.9)
		(snow.process_material as ParticleProcessMaterial).initial_velocity_max = 1.6 + wind * 0.4
	# dust underground
	var du := float(tune.call("dust", 1.0)) if dungeon else 0.0
	_run(dust, du)
	if du > 0.0:
		dust.global_position = at + Vector3(0.0, 1.6, 0.0)


func off() -> void:
	for p in [fireflies, leaves, snow, dust]:
		_run(p, 0.0)


static func _run(p: GPUParticles3D, ratio: float) -> void:
	if p == null:
		return
	if ratio <= 0.001:
		if p.emitting:
			p.emitting = false
		return
	p.amount_ratio = clampf(ratio, 0.0, 1.0)
	if not p.emitting:
		p.emitting = true
		if "--life-log" in OS.get_cmdline_user_args():
			print("[life] %s on (%.2f) at %s" % [p.name, ratio, p.global_position])


## The crowns of the broadleaf trees within 45 m: the leaves' emission points (four round each crown).
func _gather_trees(at: Vector3, zones: Array) -> void:
	var pts := PackedVector3Array()
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for zl in zones:
		var z := zl as Node3D
		var crowns = z.get("tree_crowns") if z else null
		if crowns == null or (crowns as Array).is_empty():
			continue
		var local := z.to_local(at)
		for c in crowns:
			var p: Vector3 = Vector3(c.x, c.y, c.z)
			if Vector2(p.x - local.x, p.z - local.z).length() > 45.0:
				continue
			for k in 4:
				var off: Vector3 = Vector3(rng.randf_range(-1, 1), rng.randf_range(-0.6, 0.4), rng.randf_range(-1, 1)) * c.w
				pts.append(z.to_global(p + off) - at)
			if pts.size() >= 512:
				break
	_leaf_points = pts.size()
	if pts.is_empty():
		return
	var img := Image.create(pts.size(), 1, false, Image.FORMAT_RGBF)
	for i in pts.size():
		img.set_pixel(i, 0, Color(pts[i].x, pts[i].y, pts[i].z))
	var pm := leaves.process_material as ParticleProcessMaterial
	pm.emission_point_texture = ImageTexture.create_from_image(img)
	pm.emission_point_count = pts.size()
	leaves.global_position = at


# ---------------------------------------------------------------- the four systems

static func _soft_dot(size: int) -> Texture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(0.5, 0.0)
	t.width = size
	t.height = size
	return t


static func _ramp(points: Array) -> GradientTexture1D:
	var g := Gradient.new()
	var offs := PackedFloat32Array()
	var cols := PackedColorArray()
	for p in points:
		offs.append(float(p[0]))
		cols.append(p[1])
	g.offsets = offs
	g.colors = cols
	var t := GradientTexture1D.new()
	t.gradient = g
	return t


func _fireflies() -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = "Fireflies"
	p.amount = 90
	p.lifetime = 7.0
	p.randomness = 0.6
	p.local_coords = false
	p.visibility_aabb = AABB(Vector3(-30, -10, -30), Vector3(60, 20, 60))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(22.0, 1.0, 22.0)
	pm.direction = Vector3(0, 0.2, 0)
	pm.spread = 180.0
	pm.initial_velocity_min = 0.05
	pm.initial_velocity_max = 0.35
	pm.gravity = Vector3.ZERO
	pm.damping_min = 0.1
	pm.damping_max = 0.3
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 1.2
	pm.turbulence_noise_scale = 3.0
	pm.turbulence_noise_speed_random = 0.4
	pm.turbulence_influence_min = 0.05
	pm.turbulence_influence_max = 0.15
	# the glow: slow pulses, each firefly at its own time (the ramp over its life)
	var on := Color(1, 1, 1, 1)
	var dim := Color(1, 1, 1, 0.0)
	pm.color_ramp = _ramp([[0.0, dim], [0.12, on], [0.24, dim], [0.42, dim], [0.52, on], [0.62, dim], [0.8, dim],
			[0.88, on], [1.0, dim]])
	pm.scale_min = 0.7
	pm.scale_max = 1.2
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.13, 0.13)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = _soft_dot(32)
	m.albedo_color = Color(2.2, 2.8, 0.7)          # above 1: the bloom picks them out
	m.disable_fog = true
	q.material = m
	p.draw_pass_1 = q
	return p


func _leaves() -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = "FallingLeaves"
	p.amount = 90
	p.lifetime = 11.0
	p.randomness = 0.5
	p.local_coords = false
	p.visibility_aabb = AABB(Vector3(-60, -30, -60), Vector3(120, 60, 120))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_POINTS
	pm.direction = Vector3(1, -0.3, 0.4)
	pm.spread = 50.0
	pm.initial_velocity_min = 0.2
	pm.initial_velocity_max = 0.8
	pm.gravity = Vector3(0.15, -0.9, 0.05)
	pm.damping_min = 0.6
	pm.damping_max = 1.0
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 2.0
	pm.turbulence_noise_scale = 2.0
	pm.turbulence_influence_min = 0.1
	pm.turbulence_influence_max = 0.3
	pm.angle_min = -180.0
	pm.angle_max = 180.0
	pm.angular_velocity_min = -160.0
	pm.angular_velocity_max = 160.0
	# a leaf turning over as it falls: its size swings (edge-on, flat on), and it fades at the end
	var c := Curve.new()
	for i in 13:
		c.add_point(Vector2(i / 12.0, 1.0 if i % 2 == 0 else 0.35))
	var ct := CurveTexture.new()
	ct.curve = c
	pm.scale_curve = ct
	pm.scale_min = 0.7
	pm.scale_max = 1.3
	pm.color_initial_ramp = _ramp([[0.0, Color(0.35, 0.5, 0.15)], [0.45, Color(0.55, 0.6, 0.2)],
			[0.7, Color(0.8, 0.6, 0.2)], [0.88, Color(0.7, 0.35, 0.12)], [1.0, Color(0.45, 0.3, 0.15)]])
	pm.color_ramp = _ramp([[0.0, Color(1, 1, 1, 0)], [0.05, Color(1, 1, 1, 1)], [0.85, Color(1, 1, 1, 1)], [1.0, Color(1, 1, 1, 0)]])
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.11, 0.15)
	var m := StandardMaterial3D.new()
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = 0.5
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = _leaf_tex()
	m.roughness = 0.8
	q.material = m
	p.draw_pass_1 = q
	return p


## A small leaf: a pointed oval with a stem.
static func _leaf_tex() -> Texture2D:
	var n := 32
	var img := Image.create(n, n, true, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var u := (x + 0.5) / n * 2.0 - 1.0
			var v := (y + 0.5) / n * 2.0 - 1.0
			var w := 0.55 * (1.0 - v * v) * (1.0 - 0.25 * v)       # widest above the middle, pointed both ends
			var inside := absf(u) < w and v > -0.95 and v < 0.8
			var stem := absf(u) < 0.06 and v >= 0.8
			var shade := 1.0 - 0.25 * float(absf(u) < 0.05)      # the middle vein
			img.set_pixel(x, y, Color(shade, shade, shade, 1.0) if inside or stem else Color(1, 1, 1, 0))
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


func _snow() -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = "Snow"
	p.amount = 7000
	p.lifetime = 7.0
	p.local_coords = false
	p.preprocess = 6.0
	p.visibility_aabb = AABB(Vector3(-35, -25, -35), Vector3(70, 40, 70))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(22.0, 8.0, 22.0)   # (through the whole air round you: running, you're never
	pm.direction = Vector3(0.25, -1, 0.1)                  # out of it)
	pm.spread = 12.0
	pm.initial_velocity_min = 1.1
	pm.initial_velocity_max = 1.8
	pm.gravity = Vector3.ZERO
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 1.5
	pm.turbulence_noise_scale = 4.0
	pm.turbulence_influence_min = 0.05
	pm.turbulence_influence_max = 0.15
	pm.scale_min = 0.6
	pm.scale_max = 1.3
	pm.color_ramp = _ramp([[0.0, Color(1, 1, 1, 0)], [0.15, Color(1, 1, 1, 1)], [0.85, Color(1, 1, 1, 1)], [1.0, Color(1, 1, 1, 0)]])
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.11, 0.11)
	_snow_mat = StandardMaterial3D.new()
	_snow_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_snow_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_snow_mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	_snow_mat.vertex_color_use_as_albedo = true
	_snow_mat.albedo_texture = _soft_dot(16)
	q.material = _snow_mat
	p.draw_pass_1 = q
	return p


func _dust() -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = "DungeonDust"
	p.amount = 260
	p.lifetime = 14.0
	p.randomness = 0.5
	p.local_coords = false
	p.preprocess = 7.0
	p.visibility_aabb = AABB(Vector3(-15, -6, -15), Vector3(30, 12, 30))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(11.0, 2.2, 11.0)
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 180.0
	pm.initial_velocity_min = 0.0
	pm.initial_velocity_max = 0.04
	pm.gravity = Vector3(0, -0.004, 0)
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.4
	pm.turbulence_noise_scale = 2.0
	pm.turbulence_influence_min = 0.01
	pm.turbulence_influence_max = 0.04
	pm.scale_min = 0.5
	pm.scale_max = 1.4
	pm.color_ramp = _ramp([[0.0, Color(1, 1, 1, 0)], [0.25, Color(1, 1, 1, 0.8)], [0.75, Color(1, 1, 1, 0.8)], [1.0, Color(1, 1, 1, 0)]])
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.03, 0.03)
	var m := StandardMaterial3D.new()
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = _soft_dot(16)
	m.albedo_color = Color(1.6, 1.5, 1.35)              # lit: they show where a torch or a lamp reaches them
	m.emission_enabled = true
	m.emission = Color(0.05, 0.05, 0.06)                # (and only just, in the dark)
	m.roughness = 1.0
	q.material = m
	p.draw_pass_1 = q
	return p
