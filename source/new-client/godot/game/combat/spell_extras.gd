# (no class_name: preloaded where used - new scripts are not in the class cache)
extends RefCounted
## REMASTERED SPELL EXTRAS (owner 2026-11-09: "the remastered extras ... scorch marks, tail ribbons, etc, and maybe a
## burst of more light when the spell casts (so gathering a small amount of light, then cast a burst)"). Added to the
## client's own effects, never replacing them; only while remastered lighting is on (FxLight.enabled), near the camera,
## and not when the performance governor is cutting effects. Each takes the colour of the effect it goes with
## (FxLight.color_of):
##   gather      the light in the casting hands builds up as the spell gathers ...
##   release     ... and goes off in a flash and a burst of light when it's cast
##   trail       a glowing ribbon behind a bolt
##   impact      a spell landing on an enemy: a scorch mark on the ground with embers dying in it, sparks bouncing off
##               the ground, and heat shimmer for fire
##   ring        an area spell: a ring of light on the ground at its radius, fading

const FxLight := preload("res://game/fx_light.gd")
const RANGE_M := 45.0                        # no extras further than this from the camera
const FIRE_WORDS := ["fire", "flame", "heat", "burn", "blaze", "inferno", "magma", "lava", "ember", "fiery", "scorch",
		"immolat", "pyre", "searing"]

static var _scorch_tex: Texture2D
static var _ember_tex: Texture2D
static var _ring_tex: Texture2D
static var _flash_tex: Texture2D
static var _trail_mat: ShaderMaterial
static var _heat_shader: Shader


static func _ok(at: Vector3, tree_node: Node) -> bool:
	if not FxLight.enabled or tree_node == null or not tree_node.is_inside_tree():
		return false
	if Perf.fx_range < 40.0:
		return false                                     # (the governor is cutting effects: no extras)
	var cam := tree_node.get_viewport().get_camera_3d()
	return cam != null and cam.global_position.distance_to(at) < RANGE_M


static func is_fire(name: String) -> bool:
	var n := name.to_lower()
	for w in FIRE_WORDS:
		if n.contains(w):
			return true
	return false


# ---------------------------------------------------------------- gather and release
## The hand glows' lights (FxLight's held light) start dim and build to full over the first second and a half.
static func gather(handles: Array) -> void:
	if not FxLight.enabled:
		return
	for h in handles:
		if not (h is Node) or not is_instance_valid(h):
			continue
		for l in (h as Node).find_children("FxLight*", "OmniLight3D", true, false):
			var o := l as OmniLight3D
			var full := o.light_energy * 1.4
			o.light_energy = full * 0.15
			o.create_tween().tween_property(o, "light_energy", full, 1.5).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)


## The spell goes off: a flash at the hands and a burst of light, gone in half a second.
static func release(at: Vector3, color: Color, root: Node) -> void:
	if not _ok(at, root) or color.v < 0.1:
		return
	var o := OmniLight3D.new()
	o.light_color = color
	o.light_energy = 7.0
	o.omni_range = 7.0
	o.omni_attenuation = 1.2
	o.shadow_enabled = false
	o.light_volumetric_fog_energy = 1.0
	root.add_child(o)
	o.global_position = at
	var tw := o.create_tween()
	tw.tween_property(o, "light_energy", 0.0, 0.5).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	tw.tween_callback(o.queue_free)
	_flash(at, color, 0.9, 0.28, root)


## A bright billboard flash (bloom-bright at its centre) growing and fading.
static func _flash(at: Vector3, color: Color, size: float, secs: float, root: Node) -> void:
	var q := MeshInstance3D.new()
	var m := QuadMesh.new()
	m.size = Vector2(size, size)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mat.no_depth_test = false
	mat.albedo_texture = _flash_texture()
	mat.albedo_color = Color(color.r * 2.2, color.g * 2.2, color.b * 2.2, 1.0)   # (past white: the glow takes it)
	m.material = mat
	q.mesh = m
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(q)
	q.global_position = at
	q.scale = Vector3.ONE * 0.4
	var tw := q.create_tween().set_parallel(true)
	tw.tween_property(q, "scale", Vector3.ONE * 1.3, secs).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	tw.tween_property(mat, "albedo_color:a", 0.0, secs).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.chain().tween_callback(q.queue_free)


# ---------------------------------------------------------------- the bolt's trail
## A ribbon behind `bolt` (in the world, not moving with it), facing the camera, fading along its length; it outlives
## the bolt by its own length, then frees itself.
static func trail(bolt: Node3D, color: Color, width: float = 0.22) -> void:
	if bolt == null or not _ok(bolt.global_position, bolt) or color.v < 0.1:
		return
	var t := _Trail.new()
	t.src = bolt
	t.color = color
	t.width = width
	t.material_override = _trail_material()
	bolt.get_tree().current_scene.add_child(t)


class _Trail extends MeshInstance3D:
	const LIFE := 0.09                           # seconds of path the ribbon shows (~3 m at a bolt's 32 m/s)
	var src: Node3D
	var color := Color.WHITE
	var width := 0.3
	var _pts: Array = []                         # [position, age]
	var _im := ImmediateMesh.new()

	func _ready() -> void:
		top_level = true
		mesh = _im
		cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

	func _process(delta: float) -> void:
		for p in _pts:
			p[1] = float(p[1]) + delta
		while not _pts.is_empty() and float(_pts[0][1]) > LIFE:
			_pts.pop_front()
		var alive := src != null and is_instance_valid(src) and src.is_inside_tree() and src.visible
		if alive:
			var at := src.global_position
			if _pts.is_empty() or (_pts[-1][0] as Vector3).distance_to(at) > 0.04:
				_pts.append([at, 0.0])
		elif _pts.is_empty():
			queue_free()
			return
		_im.clear_surfaces()
		var cam := get_viewport().get_camera_3d()
		if _pts.size() < 2 or cam == null:
			return
		_im.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
		for i in _pts.size():
			var p: Vector3 = _pts[i][0]
			var nb: Vector3 = _pts[mini(i + 1, _pts.size() - 1)][0] if i < _pts.size() - 1 else p
			var pv: Vector3 = _pts[maxi(i - 1, 0)][0]
			var dir := (nb - pv)
			if dir.length() < 0.0001:
				dir = Vector3.FORWARD
			var side := dir.cross(cam.global_position - p).normalized()
			var k := 1.0 - clampf(float(_pts[i][1]) / LIFE, 0.0, 1.0)     # 1 at the head, 0 at the tail
			var w := width * (0.25 + 0.75 * k)
			var c := Color(color.r, color.g, color.b, k * k)
			_im.surface_set_color(c)
			_im.surface_set_uv(Vector2(k, 0.0))
			_im.surface_add_vertex(p + side * w * 0.5)
			_im.surface_set_color(c)
			_im.surface_set_uv(Vector2(k, 1.0))
			_im.surface_add_vertex(p - side * w * 0.5)
		_im.surface_end()


static func _trail_material() -> Material:
	if _trail_mat == null:
		var sh := Shader.new()
		sh.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, fog_disabled;
void fragment() {
	float across = 1.0 - abs(UV.y * 2.0 - 1.0);              // brightest down the middle of the ribbon
	float core = smoothstep(0.0, 1.0, across);
	vec3 c = COLOR.rgb * (0.5 + 1.1 * core * core);          // the bolt's colour, its core a little past 1 for the glow
	ALBEDO = c;
	ALPHA = COLOR.a * core;
}
"""
		_trail_mat = ShaderMaterial.new()
		_trail_mat.shader = sh
	return _trail_mat


# ---------------------------------------------------------------- impacts and rings
## A spell landing on an enemy: the scorch, the sparks, and (fire) the heat shimmer. `size` the target's (SpellFx
## size_of), `height` its height (m).
static func impact(target: Node3D, color: Color, size: float, height: float, fire: bool) -> void:
	if target == null or not _ok(target.global_position, target):
		return
	var root := target.get_tree().current_scene
	var ground := target.global_position
	var k := clampf(size, 0.4, 2.5)
	_scorch(ground, color, 1.3 * k, fire, root)
	_sparks(ground + Vector3(0, height * 0.6, 0), ground.y, color, k, root)
	if fire:
		_heat(ground + Vector3(0, height * 0.55, 0), 2.0 * k, 1.4, root)


## An area spell's ring of light on the ground (radius in metres).
static func ring(at: Vector3, color: Color, radius: float, root: Node) -> void:
	if not _ok(at, root) or color.v < 0.1 or radius < 0.5:
		return
	var d := Decal.new()
	d.size = Vector3(radius * 2.2, 0.8, radius * 2.2)
	d.texture_albedo = _ring_texture()
	d.texture_emission = _ring_texture()
	d.albedo_mix = 0.0
	d.modulate = color
	d.emission_energy = 3.0
	d.upper_fade = 0.3
	d.lower_fade = 0.3
	d.cull_mask = 1                                    # (the ground and the world - not the characters)
	root.add_child(d)
	d.global_position = at - Vector3(0, 0.2, 0)
	d.scale = Vector3(0.6, 1, 0.6)
	var tw := d.create_tween().set_parallel(true)
	tw.tween_property(d, "scale", Vector3.ONE, 0.5).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	tw.tween_property(d, "emission_energy", 0.0, 2.2).set_delay(0.3)
	tw.tween_property(d, "modulate:a", 0.0, 2.2).set_delay(0.3)
	tw.chain().tween_callback(d.queue_free)


static func _scorch(at: Vector3, color: Color, size: float, fire: bool, root: Node) -> void:
	var d := Decal.new()
	d.size = Vector3(size, 0.8, size)
	d.texture_albedo = _scorch_texture()
	d.texture_emission = _ember_texture()
	d.albedo_mix = 0.75 if fire else 0.45            # (a fire burns the ground darker; others mostly glow)
	d.modulate = Color(1, 1, 1, 1)
	d.emission_energy = 2.5
	d.upper_fade = 0.35
	d.lower_fade = 0.35
	d.cull_mask = 1
	root.add_child(d)
	# (characters share the world's render layer, so the box itself stops 20 cm above the ground: the mark never
	# climbs the target's legs - owner-visible in the first test, 2026-11-09)
	d.global_position = at - Vector3(0, 0.2, 0)
	d.rotation.y = randf() * TAU
	# the embers in the effect's colour (fire: its own orange), dying over two seconds; the mark over eight
	var ember := Color(1.0, 0.45, 0.12) if fire else color
	d.set_meta("ember", ember)
	d.modulate = Color(ember.r, ember.g, ember.b, 1.0)
	var tw := d.create_tween().set_parallel(true)
	tw.tween_property(d, "emission_energy", 0.0, 2.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(d, "modulate", Color(0.35, 0.33, 0.3, 0.0), 8.0).set_delay(1.5)
	tw.chain().tween_callback(d.queue_free)


## Sparks off the hit, falling and bouncing off the ground (a flat collider at the ground's height, there only while
## they live).
static func _sparks(at: Vector3, ground_y: float, color: Color, k: float, root: Node) -> void:
	var p := GPUParticles3D.new()
	p.amount = 26
	p.one_shot = true
	p.explosiveness = 0.95
	p.lifetime = 1.3
	p.fixed_fps = 0
	p.interpolate = false
	p.collision_base_size = 0.02
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 75.0
	pm.initial_velocity_min = 2.0 * k
	pm.initial_velocity_max = 5.0 * k
	pm.gravity = Vector3(0, -9.8, 0)
	pm.damping_min = 0.5
	pm.damping_max = 1.0
	pm.scale_min = 0.6
	pm.scale_max = 1.2
	pm.collision_mode = ParticleProcessMaterial.COLLISION_RIGID
	pm.collision_bounce = 0.45
	pm.collision_friction = 0.25
	var g := Gradient.new()
	g.set_color(0, Color(color.r * 1.6, color.g * 1.6, color.b * 1.6, 1.0))   # (its colour, a little past 1)
	g.set_color(1, Color(color.r, color.g, color.b, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.07, 0.07) * k
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = _flash_texture()
	q.material = mat
	p.draw_pass_1 = q
	p.visibility_aabb = AABB(Vector3(-4, -3, -4), Vector3(8, 6, 8))
	root.add_child(p)
	p.global_position = at
	var floor_box := GPUParticlesCollisionBox3D.new()
	floor_box.size = Vector3(10, 1, 10)
	root.add_child(floor_box)
	floor_box.global_position = Vector3(at.x, ground_y - 0.5, at.z)
	p.emitting = true
	p.get_tree().create_timer(p.lifetime + 0.3).timeout.connect(func():
		p.queue_free()
		floor_box.queue_free())


## Heat shimmer: what's behind it bent by a rising ripple, fading.
static func _heat(at: Vector3, size: float, secs: float, root: Node) -> void:
	if _heat_shader == null:
		_heat_shader = Shader.new()
		_heat_shader.code = """
shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, fog_disabled;
uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
uniform float strength = 0.012;
void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0, 0, 0), vec4(0, length(MODEL_MATRIX[1].xyz), 0, 0),
			vec4(0, 0, length(MODEL_MATRIX[2].xyz), 0), vec4(0, 0, 0, 1));
}
void fragment() {
	vec2 c = UV * 2.0 - 1.0;
	float edge = clamp(1.0 - length(c), 0.0, 1.0);
	float t = TIME * 3.0;
	vec2 wob = vec2(sin(UV.y * 22.0 - t * 2.3 + sin(UV.x * 9.0)), cos(UV.y * 17.0 - t * 1.7 + UV.x * 6.0));
	vec2 uv = SCREEN_UV + wob * strength * edge * edge;
	ALBEDO = textureLod(screen, uv, 0.0).rgb;
	ALPHA = smoothstep(0.0, 0.35, edge);
}
"""
	var q := MeshInstance3D.new()
	var m := QuadMesh.new()
	m.size = Vector2(size, size * 1.3)
	var mat := ShaderMaterial.new()
	mat.shader = _heat_shader
	m.material = mat
	q.mesh = m
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(q)
	q.global_position = at
	var tw := q.create_tween()
	tw.tween_method(func(v: float): mat.set_shader_parameter("strength", v), 0.016, 0.0, secs).set_ease(Tween.EASE_IN)
	tw.tween_callback(q.queue_free)


# ---------------------------------------------------------------- textures (made once)
static func _radial(size: int, f: Callable) -> Texture2D:
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 1234
	for y in size:
		for x in size:
			var u := (x + 0.5) / size * 2.0 - 1.0
			var v := (y + 0.5) / size * 2.0 - 1.0
			img.set_pixel(x, y, f.call(u, v, rng))
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


static func _noise(u: float, v: float) -> float:
	return 0.5 + 0.25 * sin(u * 13.0 + v * 7.0) * cos(v * 11.0 - u * 5.0) + 0.25 * sin((u + v) * 23.0) * sin(u * 17.0 - v * 19.0)


static func _scorch_texture() -> Texture2D:
	if _scorch_tex == null:
		_scorch_tex = _radial(128, func(u: float, v: float, _r: RandomNumberGenerator) -> Color:
			var d := sqrt(u * u + v * v) * (0.85 + 0.3 * _noise(u * 1.3, v * 1.3))
			var a := clampf(1.0 - smoothstep(0.35, 1.0, d), 0.0, 1.0) * 0.85
			return Color(0.06, 0.05, 0.045, a))
	return _scorch_tex


static func _ember_texture() -> Texture2D:
	if _ember_tex == null:
		_ember_tex = _radial(128, func(u: float, v: float, _r: RandomNumberGenerator) -> Color:
			var d := sqrt(u * u + v * v)
			var spots := clampf((_noise(u * 3.1, v * 3.1) - 0.55) * 4.0, 0.0, 1.0)
			var e := spots * clampf(1.0 - smoothstep(0.2, 0.8, d), 0.0, 1.0) + clampf(1.0 - d * 2.5, 0.0, 1.0) * 0.6
			return Color(e, e, e, 1.0))
	return _ember_tex


static func _ring_texture() -> Texture2D:
	if _ring_tex == null:
		_ring_tex = _radial(256, func(u: float, v: float, _r: RandomNumberGenerator) -> Color:
			var d := sqrt(u * u + v * v) / 0.91                 # (the ring at the radius, inside the decal's margin)
			var ring := exp(-pow((d - 1.0) / 0.04, 2.0))
			var inner := clampf(1.0 - d, 0.0, 1.0) * 0.12
			var e := clampf(ring + inner, 0.0, 1.0)
			return Color(e, e, e, e))
	return _ring_tex


static func _flash_texture() -> Texture2D:
	if _flash_tex == null:
		_flash_tex = _radial(64, func(u: float, v: float, _r: RandomNumberGenerator) -> Color:
			var d := sqrt(u * u + v * v)
			var e := clampf(exp(-d * d * 6.0) + exp(-d * d * 40.0), 0.0, 1.0)
			return Color(1, 1, 1, e))
	return _flash_tex
