extends Node3D
## Fireflies, each its own small light (owner 2026-10-31: "too frequently and densely ... a lot more sparse, and
## spread out ... if they could emit a small glow, like a light source, that would be cool"): a dozen at most, spread
## over 6-30 m round you, each drifting slowly a metre or two above the ground and blinking now and then - a soft
## green-gold dot that lights the grass round it (an OmniLight3D, no shadows). One that strays too far or goes under
## the ground comes back somewhere else round you.
## In Hibernia, when the fireflies are out, a fairy now and then (owner: "a small chance that a glowing fairy (think
## Navi) will appear and fly around ... with a brighter light and random color"): a bright mote in a random colour
## with a faint halo and a trail of sparks, darting about near you for a minute or two, then gone.

const COUNT := 12
const NEAR_M := 6.0
const FAR_M := 30.0
const FIREFLY := Color(0.78, 1.0, 0.35)
const FAIRY_CHANCE := 0.12                   # each minute the fireflies are out in Hibernia

var _flies: Array = []                       # {node, light, mat, phase, rate, vel, ground, ground_at, home}
var _fairy: Dictionary = {}
var _fairy_roll := 30.0
var _amount := 0.0
var _rng := RandomNumberGenerator.new()
var _dot: Texture2D


func _ready() -> void:
	_rng.randomize()
	_dot = _soft_dot()


func tick(at: Vector3, amount: float, hibernia: bool, fairy_tune: float) -> void:
	var dt := get_process_delta_time()
	_amount = move_toward(_amount, amount, dt * 0.2)      # (they come out over a few seconds at dusk)
	var want := int(round(COUNT * clampf(_amount, 0.0, 1.0)))
	while _flies.size() < want:
		_flies.append(_make_fly(at))
	while _flies.size() > want:
		var f: Dictionary = _flies.pop_back()
		(f.node as Node).queue_free()
	var t := Time.get_ticks_msec() / 1000.0
	for f in _flies:
		_move_fly(f, at, dt, t)
	# the fairy
	if hibernia and _amount > 0.5 and fairy_tune > 0.0:
		_fairy_roll -= dt
		if fairy_tune >= 5.0 and _fairy.is_empty():       # (tests: --tune=fairy:10 - one at once)
			_fairy_roll = 0.0
		if _fairy_roll <= 0.0:
			_fairy_roll = 60.0
			if _fairy.is_empty() and _rng.randf() < FAIRY_CHANCE * minf(fairy_tune, 1.0 / FAIRY_CHANCE):
				_fairy = _make_fairy(at)
	if not _fairy.is_empty():
		_move_fairy(at, dt, t, hibernia and _amount > 0.3)


# ---------------------------------------------------------------- fireflies

func _make_fly(at: Vector3) -> Dictionary:
	var node := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(0.09, 0.09)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.albedo_texture = _dot
	m.disable_fog = true
	q.material = m
	node.mesh = q
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var light := OmniLight3D.new()
	light.light_color = FIREFLY
	light.omni_range = 2.6
	light.omni_attenuation = 1.6
	light.shadow_enabled = false
	light.light_volumetric_fog_energy = 0.0
	light.light_specular = 0.2
	node.add_child(light)
	add_child(node)
	var f := {"node": node, "light": light, "mat": m, "phase": _rng.randf() * 20.0, "rate": _rng.randf_range(0.35, 0.7),
			"vel": Vector3.ZERO, "ground": at.y, "ground_at": 0.0, "lift": _rng.randf_range(0.5, 2.2)}
	_place(f, at, true)
	return f


## Somewhere round you (6-30 m), its own height over the ground there.
func _place(f: Dictionary, at: Vector3, anywhere: bool) -> void:
	var a := _rng.randf() * TAU
	var r := _rng.randf_range(NEAR_M if not anywhere else 2.0, FAR_M)
	var p := at + Vector3(cos(a) * r, 0.0, sin(a) * r)
	f.ground = _ground(p, at.y)
	f.ground_at = 0.0
	p.y = float(f.ground) + float(f.lift)
	(f.node as Node3D).global_position = p
	f.vel = Vector3(_rng.randf_range(-1, 1), 0.0, _rng.randf_range(-1, 1)).normalized() * 0.25


func _ground(p: Vector3, near_y: float) -> float:
	if not is_inside_tree():
		return near_y
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, near_y + 25.0, p.z), Vector3(p.x, near_y - 40.0, p.z),
			ZoneLoader.LAYER_FLOOR)
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	return float((hit.position as Vector3).y) if not hit.is_empty() else near_y


func _move_fly(f: Dictionary, at: Vector3, dt: float, t: float) -> void:
	var node := f.node as Node3D
	var p := node.global_position
	if Vector2(p.x - at.x, p.z - at.z).length() > FAR_M + 4.0:
		_place(f, at, false)
		return
	# a slow wander: the heading turns a little at a time; it keeps to its height over the ground
	var v: Vector3 = f.vel
	v = v.rotated(Vector3.UP, sin(t * 0.7 + float(f.phase)) * dt * 1.2)
	f.vel = v
	f.ground_at = float(f.ground_at) + dt
	if float(f.ground_at) > 1.0:
		f.ground_at = 0.0
		f.ground = _ground(p, at.y)
	var want_y := float(f.ground) + float(f.lift) + sin(t * 0.9 + float(f.phase)) * 0.25
	p += v * dt
	p.y = lerpf(p.y, want_y, minf(1.0, dt * 1.5))
	node.global_position = p
	# the blink: a slow glow up and down, dark for a while between (each its own rhythm)
	var c := sin(t * float(f.rate) * TAU * 0.5 + float(f.phase))
	var glow := pow(maxf(c, 0.0), 3.0)
	var m := f.mat as StandardMaterial3D
	m.albedo_color = Color(FIREFLY.r * 2.4, FIREFLY.g * 2.4, FIREFLY.b * 2.4, glow)
	var l := f.light as OmniLight3D
	l.light_energy = glow * 0.55
	l.visible = glow > 0.02


# ---------------------------------------------------------------- the fairy

func _make_fairy(at: Vector3) -> Dictionary:
	var col := Color.from_hsv(_rng.randf(), 0.55, 1.0)
	var node := Node3D.new()
	node.name = "Fairy"
	add_child(node)
	var core := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(0.16, 0.16)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.albedo_texture = _dot
	m.disable_fog = true
	m.albedo_color = Color(col.r * 3.0, col.g * 3.0, col.b * 3.0, 1.0)
	q.material = m
	core.mesh = q
	node.add_child(core)
	var halo := MeshInstance3D.new()
	var hq := QuadMesh.new()
	hq.size = Vector2(0.7, 0.7)
	var hm := m.duplicate() as StandardMaterial3D
	hm.albedo_color = Color(col.r, col.g, col.b, 0.35)
	hq.material = hm
	halo.mesh = hq
	node.add_child(halo)
	var light := OmniLight3D.new()
	light.light_color = col
	light.omni_range = 5.5
	light.omni_attenuation = 1.4
	light.light_energy = 0.0
	light.shadow_enabled = false
	light.light_volumetric_fog_energy = 0.3
	node.add_child(light)
	# a trail of sparks behind it
	var sp := GPUParticles3D.new()
	sp.amount = 40
	sp.lifetime = 0.9
	sp.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, -1, 0)
	pm.spread = 60.0
	pm.initial_velocity_min = 0.05
	pm.initial_velocity_max = 0.3
	pm.gravity = Vector3(0, -0.4, 0)
	pm.scale_min = 0.5
	pm.scale_max = 1.0
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	sp.process_material = pm
	var sq := QuadMesh.new()
	sq.size = Vector2(0.04, 0.04)
	var smat := m.duplicate() as StandardMaterial3D
	smat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	smat.vertex_color_use_as_albedo = true
	smat.albedo_color = Color(col.r * 2.0, col.g * 2.0, col.b * 2.0, 1.0)
	sq.material = smat
	sp.draw_pass_1 = sq
	node.add_child(sp)
	var a := _rng.randf() * TAU
	node.global_position = at + Vector3(cos(a) * 14.0, 2.0, sin(a) * 14.0)
	return {"node": node, "light": light, "halo": hm, "life": _rng.randf_range(60.0, 120.0), "fade": 0.0,
			"goal": node.global_position, "goal_in": 0.0, "vel": Vector3.ZERO, "phase": _rng.randf() * 10.0}


func _move_fairy(at: Vector3, dt: float, t: float, stay: bool) -> void:
	var f := _fairy
	var node := f.node as Node3D
	f.life = float(f.life) - dt
	var leaving := float(f.life) <= 0.0 or not stay
	f.fade = move_toward(float(f.fade), 0.0 if leaving else 1.0, dt * 0.5)
	if leaving and float(f.fade) <= 0.0:
		node.queue_free()
		_fairy = {}
		return
	# darting: a new spot near you every second or two, flown to quickly and a little wobbly
	f.goal_in = float(f.goal_in) - dt
	var p := node.global_position
	if float(f.goal_in) <= 0.0 or p.distance_to(f.goal) < 0.4:
		f.goal_in = _rng.randf_range(0.8, 2.2)
		var a := _rng.randf() * TAU
		var r := _rng.randf_range(2.5, 9.0)
		var g := at + Vector3(cos(a) * r, 0.0, sin(a) * r)
		g.y = _ground(g, at.y) + _rng.randf_range(0.8, 2.6)
		f.goal = g
	var to: Vector3 = (f.goal as Vector3) - p
	var v: Vector3 = f.vel
	v += to.normalized() * minf(to.length(), 3.0) * dt * 6.0
	v *= 1.0 - minf(1.0, dt * 2.2)
	v += Vector3(sin(t * 7.0 + float(f.phase)), cos(t * 9.0), cos(t * 6.0 + float(f.phase))) * dt * 1.2
	f.vel = v
	node.global_position = p + v * dt
	var pulse := 0.85 + 0.15 * sin(t * 5.0 + float(f.phase))
	(f.light as OmniLight3D).light_energy = 1.4 * pulse * float(f.fade)
	var hm := f.halo as StandardMaterial3D
	hm.albedo_color.a = 0.35 * pulse * float(f.fade)
	node.scale = Vector3.ONE * maxf(float(f.fade), 0.01)


static func _soft_dot() -> Texture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.25, Color(1, 1, 1, 0.8))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(0.5, 0.0)
	t.width = 32
	t.height = 32
	return t
