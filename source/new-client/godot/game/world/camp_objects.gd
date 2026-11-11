extends RefCounted
## The server's new world objects (owner 2026-11-11) - models the item catalogue has none of, drawn here by their
## object model numbers (the server's CampingSupplies / SoulbindStones / TreasureChests use the same numbers):
##   32001-32003  a soulbind stone (Albion, Midgard, Hibernia): the realm's bind stone at three quarters its size
##   32011-32017  a campfire, tiers grey .. purple: the zones' stone ring with its burning logs (Midgard's ringed fire
##                pit for the better tiers), a warm flickering light, the fire a little livelier tier by tier
##   32021-32027  a cooking pot over a fire, tiers grey .. purple
## Models: pipeline/build_camping.py -> content/camping (the zones' fire models with their textures); the bind stones
## are housing's (content/housing/models).

const Housing := preload("res://game/world/housing.gd")
const FxLight := preload("res://game/fx_light.gd")

const SOULBIND := {32001: "models/obj_aphbindstone.gltf", 32002: "models/obj_mphbindstone.gltf",
		32003: "models/obj_hphbindstone.gltf"}
const SOULBIND_SCALE := 0.75
const DIR := "res://content/camping"


static func is_custom(model: int) -> bool:
	return SOULBIND.has(model) or (model >= 32011 and model <= 32017) or (model >= 32021 and model <= 32027)


## The object's model, or null when its files are missing (the caller then shows the loot bag).
static func make(model: int) -> Node3D:
	if SOULBIND.has(model):
		var s := Housing._make(String(SOULBIND[model]), false, "")
		if s:
			s.scale = Vector3.ONE * SOULBIND_SCALE
		return s
	if model >= 32011 and model <= 32017:
		return _fire(model - 32010)
	if model >= 32021 and model <= 32027:
		return _pot(model - 32020)
	return null


static func _fire(tier: int) -> Node3D:
	var root := Node3D.new()
	root.name = "Campfire_%d" % tier
	var ring_file := DIR + ("/valcampfire.gltf" if tier >= 5 else "/campfire.gltf")
	var ring: Node3D = NifScene.copy_of(ring_file) if FileAccess.file_exists(ring_file) else null
	if ring:
		root.add_child(ring)                              # (the zones' models are in metres, upright already)
		for c in ring.find_children("collision*", "", true, false):
			(c as Node).queue_free()
	var logs_file := DIR + "/effect_campfire_sfx.gltf"
	var logs: Node3D = NifScene.copy_of(logs_file) if FileAccess.file_exists(logs_file) else null
	if logs:
		logs.scale = Vector3.ONE * (1.0 + 0.06 * (tier - 1))            # (a better kit: a bigger fire)
		root.add_child(logs)
		NifParticles.fit_to_scale(logs)
	if ring == null and logs == null:
		root.free()
		return null
	var light := OmniLight3D.new()
	light.name = "CampfireLight"
	light.light_color = Color(1.0, 0.62, 0.3)
	light.light_energy = 1.6 + 0.15 * tier
	light.omni_range = 7.0 + 0.5 * tier
	light.omni_attenuation = 1.3
	light.shadow_enabled = true
	light.distance_fade_enabled = true
	light.distance_fade_begin = 60.0
	light.distance_fade_length = 20.0
	light.position = Vector3(0, 0.6, 0)
	root.add_child(light)
	var tw := light.create_tween().set_loops()            # a living flame: the light breathes and flickers
	tw.tween_property(light, "light_energy", light.light_energy * 0.82, 0.23)
	tw.tween_property(light, "light_energy", light.light_energy * 1.08, 0.17)
	tw.tween_property(light, "light_energy", light.light_energy * 0.9, 0.31)
	tw.tween_property(light, "light_energy", light.light_energy, 0.2)
	return root


static func _pot(tier: int) -> Node3D:
	# a black iron cauldron hung from a tripod of green sticks over the fire, stew steaming in it - built here (the
	# item catalogue's only pot is the frontier's boiling-oil vat, many times too big)
	var root := Node3D.new()
	root.name = "CookingPot_%d" % tier
	var iron := StandardMaterial3D.new()
	iron.albedo_color = Color(0.09, 0.085, 0.08)
	iron.metallic = 0.75
	iron.roughness = 0.45
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.32, 0.22, 0.13)
	wood.roughness = 0.9
	var stew := StandardMaterial3D.new()
	stew.albedo_color = Color(0.45, 0.24, 0.1)
	stew.roughness = 0.35
	stew.emission_enabled = true
	stew.emission = Color(0.35, 0.14, 0.04)
	stew.emission_energy_multiplier = 0.6
	var hang := 0.72                                        # the pot's middle above the ground (over the logs)
	var body := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.3
	sphere.height = 0.5
	sphere.material = iron
	body.mesh = sphere
	body.position = Vector3(0, hang, 0)
	root.add_child(body)
	var rim := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.24
	torus.outer_radius = 0.29
	torus.material = iron
	rim.mesh = torus
	rim.position = Vector3(0, hang + 0.2, 0)
	root.add_child(rim)
	var top := MeshInstance3D.new()
	var disc := CylinderMesh.new()
	disc.top_radius = 0.25
	disc.bottom_radius = 0.25
	disc.height = 0.02
	disc.material = stew
	top.mesh = disc
	top.position = Vector3(0, hang + 0.17, 0)
	root.add_child(top)
	var apex := Vector3(0, hang + 0.95, 0)
	for k in 3:                                             # the tripod: three sticks meeting over the pot
		var a := TAU * k / 3.0 + 0.4
		var foot := Vector3(cos(a) * 0.85, 0.0, sin(a) * 0.85)
		var stick := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.025
		cyl.bottom_radius = 0.035
		cyl.height = foot.distance_to(apex) + 0.12
		cyl.material = wood
		stick.mesh = cyl
		root.add_child(stick)
		stick.look_at_from_position((foot + apex) * 0.5, apex, Vector3.UP if absf((apex - foot).normalized().dot(Vector3.UP)) < 0.99 else Vector3.RIGHT)
		stick.rotate_object_local(Vector3.RIGHT, PI / 2)
	var chain := MeshInstance3D.new()
	var link := CylinderMesh.new()
	link.top_radius = 0.008
	link.bottom_radius = 0.008
	link.height = apex.y - (hang + 0.2)
	link.material = iron
	chain.mesh = link
	chain.position = Vector3(0, (apex.y + hang + 0.2) * 0.5, 0)
	root.add_child(chain)
	root.add_child(_steam(Vector3(0, hang + 0.2, 0), tier))
	return root


## Steam off the stew: soft grey puffs rising and fading (more of them for the better pots).
static func _steam(at: Vector3, tier: int) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = "Steam"
	p.position = at
	p.amount = 10 + tier * 2
	p.lifetime = 2.6
	p.preprocess = 2.0
	var m := ParticleProcessMaterial.new()
	m.direction = Vector3.UP
	m.spread = 12.0
	m.initial_velocity_min = 0.25
	m.initial_velocity_max = 0.45
	m.gravity = Vector3(0, 0.05, 0)
	m.scale_min = 0.6
	m.scale_max = 1.3
	m.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	m.emission_sphere_radius = 0.15
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0.0))
	fade.add_point(0.2, Color(1, 1, 1, 0.35))
	fade.set_color(fade.get_point_count() - 1, Color(1, 1, 1, 0.0))
	var ramp := GradientTexture1D.new()
	ramp.gradient = fade
	m.color_ramp = ramp
	p.process_material = m
	var quad := QuadMesh.new()
	quad.size = Vector2(0.35, 0.35)
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.vertex_color_use_as_albedo = true
	mat.albedo_color = Color(0.85, 0.85, 0.85)
	var g := GradientTexture2D.new()                        # a soft round puff
	var gg := Gradient.new()
	gg.set_color(0, Color(1, 1, 1, 1))
	gg.set_color(1, Color(1, 1, 1, 0))
	g.gradient = gg
	g.fill = GradientTexture2D.FILL_RADIAL
	g.fill_from = Vector2(0.5, 0.5)
	g.fill_to = Vector2(1.0, 0.5)
	mat.albedo_texture = g
	quad.material = mat
	p.draw_pass_1 = quad
	return p
