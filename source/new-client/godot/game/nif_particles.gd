class_name NifParticles
extends RefCounted
## NetImmerse 4.x particle systems (fires, smoke, glows, clouds, snow) as Godot GPU particles. Specs come from
## pipeline/nif_static.particle_systems (glTF extras.nif_particles); see WORLD IMPORT LESSONS.md "Effects".


## One NetImmerse particle system (nif_static.particle_systems spec) as GPU particles at `at`.
## Always made on the main thread (owner 2026-11-01: the game crashed loading Mongfar - his spells' effects, prefetched
## at login on several workers while the zones' fires were built on others, made particle materials at once and
## corrupted the engine's lists: "~List size_cache" in here, then gone). A worker hands it over and waits its turn.
static func build(spec: Dictionary, at: Transform3D, far: float, materials: NifMaterials) -> GPUParticles3D:
	if OS.get_thread_caller_id() == OS.get_main_thread_id():
		return _build(spec, at, far, materials)
	var out := []
	var done := Semaphore.new()
	(func():
		out.append(NifParticles._build(spec, at, far, materials))
		done.post()).call_deferred()
	var waited := 0
	while not done.try_wait():
		OS.delay_msec(2)
		waited += 2
		if waited > 10000:                                  # (the main loop has stopped - quitting): no particles
			return GPUParticles3D.new()
	return out[0]


static func _build(spec: Dictionary, at: Transform3D, far: float, materials: NifMaterials) -> GPUParticles3D:
	var e: Dictionary = spec.emitter
	var b: Array = e.basis
	var emitter := Transform3D(Basis(Vector3(b[0][0], b[1][0], b[2][0]), Vector3(b[0][1], b[1][1], b[2][1]),
			Vector3(b[0][2], b[1][2], b[2][2])), Vector3(e.origin[0], e.origin[1], e.origin[2]))
	var p := GPUParticles3D.new()
	p.name = "particles_%s" % spec.get("texture", "")
	p.set_meta("nif_spec", spec)                         # NifScene's effect timeline (emit windows, moving emitters)
	p.transform = at * emitter
	p.local_coords = false
	var life := maxf(float(spec.lifetime), 0.05)
	p.lifetime = life
	# moved every frame (Godot's default is 30 a second, interpolated: at 160 fps the sparks stepped - owner
	# 2026-11-09, spell effects "a little rough")
	p.fixed_fps = 0
	p.interpolate = false
	# how many are alive at once: the client's Emit Flags (pipeline 'rate_mode') - 'rate': the emit rate x the lifetime,
	# never past the system's size; 'auto': the system's size (owner 2026-11-01: a Thane's hand glow kept 85 additive
	# glows alive where the client's 30 a second keeps about 5 - a white bubble instead of a flickering spark). Models
	# converted before the flag was kept: the larger of the two, as before.
	var by_rate := int(ceil(float(spec.emit_rate) * (life + float(spec.lifetime_random))))
	match String(spec.get("rate_mode", "")):
		"rate": p.amount = clampi(mini(int(spec.max_particles), by_rate) if int(spec.max_particles) > 0 else by_rate, 1, 512)
		"auto": p.amount = clampi(int(spec.max_particles), 1, 512)
		_: p.amount = clampi(maxi(int(spec.max_particles), by_rate), 1, 512)
	p.preprocess = life + float(spec.lifetime_random)    # already burning when it comes into view
	p.visibility_range_end = far
	var reach := (float(spec.speed) + float(spec.speed_random)) * (life + float(spec.lifetime_random))
	for v in spec.box:
		reach += float(v) * 0.5
	if spec.get("quad") != null:
		reach += float(spec.quad[0])
	reach = maxf(reach, 4.0)                              # campfires stay small; Midgard's drifting clouds travel ~300 m
	p.visibility_aabb = AABB(Vector3(-reach, -maxf(reach, 1.0), -reach), Vector3(reach, reach, reach) * 2.0)
	var pm := ParticleProcessMaterial.new()
	# emission direction: the emitter's up axis tilted by the declination, turned by the planar angle; the
	# declination variation is the cone
	pm.direction = Vector3.UP.rotated(Vector3.RIGHT, float(spec.declination)).rotated(Vector3.UP, float(spec.planar_angle))
	pm.spread = rad_to_deg(float(spec.declination_variation))
	pm.initial_velocity_min = maxf(float(spec.speed) - float(spec.speed_random), 0.0)
	pm.initial_velocity_max = float(spec.speed) + float(spec.speed_random)
	pm.lifetime_randomness = clampf(float(spec.lifetime_random) / life, 0.0, 1.0)
	var box: Array = spec.box
	if box[0] + box[1] + box[2] > 0.0:
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
		pm.emission_box_extents = Vector3(box[0], box[1], box[2]) * 0.5
	var gravity := Vector3.ZERO
	for m in spec.modifiers:
		match String(m.type):
			"gravity":
				var dir := Vector3(m.direction[0], m.direction[1], m.direction[2])
				if String(m.kind) == "spherical":         # pull towards the gravity point, as seen from the emitter
					dir = (Vector3(m.position[0], m.position[1], m.position[2]) - emitter.origin).normalized()
				gravity += at.basis * dir * float(m.force)
			"color":
				var grad := Gradient.new()
				grad.offsets = PackedFloat32Array()
				grad.colors = PackedColorArray()
				for k in m.keys:
					grad.add_point(clampf(float(k[0]), 0.0, 1.0), Color(k[1][0], k[1][1], k[1][2], k[1][3]))
				if grad.get_point_count() > 0:
					var gt := GradientTexture1D.new()
					gt.gradient = grad
					pm.color_ramp = gt
			"growfade":
				var c := Curve.new()
				var g := clampf(float(m.grow) / life, 0.0, 1.0)
				var f := clampf(float(m.fade) / life, 0.0, 1.0)
				c.add_point(Vector2(0.0, 0.0 if g > 0.0 else 1.0))
				if g > 0.0 and g < 1.0:
					c.add_point(Vector2(g, 1.0))
				if f > 0.0 and 1.0 - f > g:
					c.add_point(Vector2(1.0 - f, 1.0))
				c.add_point(Vector2(1.0, 0.0 if f > 0.0 else 1.0))
				var ct := CurveTexture.new()
				ct.curve = c
				pm.scale_curve = ct
			"rotation":                                   # NiParticleRotation: spin in degrees per second
				pm.angular_velocity_min = rad_to_deg(float(m.speed))
				pm.angular_velocity_max = rad_to_deg(float(m.speed))
	pm.gravity = gravity
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2.ONE * float(spec.size) * 2.0     # the controller size is the particle radius (NiParticlesData particle_radius)
	if spec.get("quad") != null:                         # mesh particles: the plane mesh scaled by the radius
		quad.size = Vector2(float(spec.quad[0]), float(spec.quad[1]))
	p.draw_pass_1 = quad
	p.set_meta("nif_quad", quad.size)
	# soft edges: a particle fades as it nears what's behind it (the ground, a wall, a body) instead of cutting off
	# in a hard line - within about a quarter of its size
	var soft := clampf(quad.size.x * 0.25, 0.05, 0.8)
	var blend := str(spec.get("blend", ""))
	if blend in ["screen", "multiply", "invdest_add", "add", ""]:
		var sm := ShaderMaterial.new()
		match blend:
			"screen": sm.shader = _screen_shader()
			"multiply": sm.shader = _multiply_shader()
			"invdest_add": sm.shader = _invdest_add_shader()
			"add": sm.shader = _add_shader()
			_: sm.shader = _mix_shader()
		sm.set_shader_parameter("soft_dist", soft)
		if spec.get("texture") is String and String(spec.texture) != "":
			var tx := materials.texture(String(spec.texture))
			sm.set_shader_parameter("tex", tx)
			if tx == null and blend in ["add", ""]:
				p.visible = false                        # its texture isn't in the client: not a white square
		quad.material = sm
		return p
	var mat := StandardMaterial3D.new()
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.vertex_color_is_srgb = true                     # (the client's colour ramps are gamma colours)
	mat.proximity_fade_enabled = true
	mat.proximity_fade_distance = soft
	if str(spec.get("blend", "")) == "invdest":
		# the client's INVDESTCOLOR / INVSRCALPHA (corpse lights' wisps): the colour in full, the alpha dimming what's
		# behind - a premultiplied blend (as 'mix' they were grey smoke)
		mat.blend_mode = BaseMaterial3D.BLEND_MODE_PREMULT_ALPHA

	if spec.get("texture") is String and String(spec.texture) != "":
		mat.albedo_texture = materials.texture(String(spec.texture))
		if mat.albedo_texture == null:
			p.visible = false                            # its texture isn't in the client: not a white square
	quad.material = mat
	return p


## Godot carries a particle node's scale into the particles' speed and emitter box but not their size
## (tests/particle_scale_main.gd). Effects scaled to the character they sit on (speffects / moneffects Auto Scale)
## or riding a scaled model call this once they are in the tree: each quad gets its system's world scale.
static func fit_to_scale(root: Node) -> void:
	if root == null:
		return
	for n in root.find_children("*", "GPUParticles3D", true, false):
		var p := n as GPUParticles3D
		if not p.has_meta("nif_quad") or not p.is_inside_tree():
			continue
		var k := p.global_basis.get_scale().x
		if is_equal_approx(float(p.get_meta("fit_k", -1.0)), k):
			continue                                       # a pooled copy at the same size
		var quad: QuadMesh = p.get_meta("own_quad") if p.has_meta("own_quad") else (p.draw_pass_1 as QuadMesh).duplicate()
		quad.size = (p.get_meta("nif_quad") as Vector2) * k
		p.draw_pass_1 = quad
		p.set_meta("own_quad", quad)
		p.set_meta("fit_k", k)


static var _screen: Shader
static var _multiply: Shader
static var _invdest_add: Shader
static var _add: Shader
static var _mix: Shader


## Additive glows (most spell sparks, cores, flares) - and, with remastered lighting, their brightest parts pushed
## past white so the glow (bloom) picks them up: a fireball's core, a heal's sparkle get a soft halo, the dim edges
## stay as they were (owner 2026-11-09).
static func _add_shader() -> Shader:
	if _add == null:
		_add = Shader.new()
		_add.code = SCREEN_SHADER.replace("render_mode blend_mix,", "render_mode blend_add,").replace(
				"""	vec3 c = t.rgb * COLOR.rgb;
	float m = max(max(c.r, c.g), max(c.b, 0.001));
	ALBEDO = c / m;
	ALPHA = m * t.a * COLOR.a;""", """	ALBEDO = t.rgb * COLOR.rgb;
	ALPHA = t.a * COLOR.a;
	float m = max(max(ALBEDO.r, ALBEDO.g), ALBEDO.b) * ALPHA;
	ALBEDO *= 1.0 + GLOW_BOOST * remaster_fx * smoothstep(0.45, 1.0, m);""").replace("//TAIL", "ALPHA *= soft;")
	return _add


## Plain alpha-blended particles (smoke, dust, leaves).
static func _mix_shader() -> Shader:
	if _mix == null:
		_mix = Shader.new()
		_mix.code = SCREEN_SHADER.replace(
				"""	vec3 c = t.rgb * COLOR.rgb;
	float m = max(max(c.r, c.g), max(c.b, 0.001));
	ALBEDO = c / m;
	ALPHA = m * t.a * COLOR.a;""", """	ALBEDO = t.rgb * COLOR.rgb;
	ALPHA = t.a * COLOR.a;""").replace("//TAIL", "ALPHA *= soft;")
	return _mix


## The client's INVDESTCOLOR / ONE (a few glows): the particle's colour added in full - its alpha takes no part.
static func _invdest_add_shader() -> Shader:
	if _invdest_add == null:
		_invdest_add = Shader.new()
		_invdest_add.code = SCREEN_SHADER.replace("render_mode blend_mix,", "render_mode blend_add,").replace(
				"""	vec3 c = t.rgb * COLOR.rgb;
	float m = max(max(c.r, c.g), max(c.b, 0.001));
	ALBEDO = c / m;
	ALPHA = m * t.a * COLOR.a;""", """	ALBEDO = t.rgb * COLOR.rgb;""").replace("//TAIL", "ALBEDO *= soft;")
	return _invdest_add


## The client's multiply blend (src DESTCOLOR, dst INVSRCALPHA or ZERO): what is behind x (the particle's colour + the
## part its alpha lets through) - a tint that darkens or colours, never glows (the Shaman's poison mist).
static func _multiply_shader() -> Shader:
	if _multiply == null:
		_multiply = Shader.new()
		_multiply.code = SCREEN_SHADER.replace("render_mode blend_mix,", "render_mode blend_mul,").replace(
				"""	vec3 c = t.rgb * COLOR.rgb;
	float m = max(max(c.r, c.g), max(c.b, 0.001));
	ALBEDO = c / m;
	ALPHA = m * t.a * COLOR.a;""", """	float a = t.a * COLOR.a;
	ALBEDO = clamp(t.rgb * COLOR.rgb + vec3(1.0 - a), 0.0, 1.0);   // the blend exactly, as the card clamped it""").replace(
				"//TAIL", "ALBEDO = mix(vec3(1.0), ALBEDO, soft);")
	return _multiply


## Camera-facing particle quads with the client's screen blend (src SRCALPHA, dst INVSRCCOLOR): black adds nothing,
## the colour-ramp alpha fades each particle in and out.
static func _screen_shader() -> Shader:
	if _screen == null:
		_screen = Shader.new()
		_screen.code = SCREEN_SHADER.replace("//TAIL", "ALPHA *= soft;")
	return _screen


## (all particle shaders, owner 2026-11-09 - spell effects "a little rough": the colour ramps read as the gamma colours
## they are; soft edges against the depth behind; //TAIL is each blend's own way to apply the fade)
const GLOW_BOOST := 1.6
const SCREEN_SHADER := """
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, unshaded;
uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform float soft_dist = 0.3;
global uniform float remaster_fx;
const float GLOW_BOOST = 1.6;

void vertex() {
	vec3 lo = COLOR.rgb / 12.92;
	vec3 hi = pow((COLOR.rgb + 0.055) / 1.055, vec3(2.4));
	COLOR.rgb = mix(hi, lo, vec3(lessThan(COLOR.rgb, vec3(0.04045))));
	mat4 w = mat4(normalize(INV_VIEW_MATRIX[0]), normalize(INV_VIEW_MATRIX[1]), normalize(INV_VIEW_MATRIX[2]), MODEL_MATRIX[3]);
	float a = INSTANCE_CUSTOM.x;
	w = w * mat4(vec4(cos(a), -sin(a), 0.0, 0.0), vec4(sin(a), cos(a), 0.0, 0.0), vec4(0.0, 0.0, 1.0, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	MODELVIEW_MATRIX = VIEW_MATRIX * w;
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0),
			vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0), vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0),
			vec4(0.0, 0.0, 0.0, 1.0));
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
}

void fragment() {
	vec4 t = texture(tex, UV);
	vec3 c = t.rgb * COLOR.rgb;
	float m = max(max(c.r, c.g), max(c.b, 0.001));
	ALBEDO = c / m;
	ALPHA = m * t.a * COLOR.a;
	float soft = 1.0;
	if (soft_dist > 0.0) {
		float d = texture(depth_tex, SCREEN_UV).r;
		vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
		soft = clamp((VERTEX.z - v.z / v.w) / soft_dist, 0.0, 1.0);
	}
	//TAIL
}
"""


