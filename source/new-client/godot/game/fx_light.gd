# (no class_name: preloaded where used - new scripts are not in the class cache)
extends RefCounted
## Light from effects (REMASTERED LIGHTING, owner 2026-10-28: "maybe having spells and weapon effects produce
## light?"): a spell's glows, bolts and bursts, a weapon's flame or glow and a monster's wisp light what is around
## them in the effect's own colour. The colour is worked out once per effect file from its particle textures and
## colour ramps (the bright, opaque texels count most). Spell lights fade out with the effect; weapon and monster
## lights stay while it is there, with a slight shimmer. Only while remastered lighting is on (SkySystem).

static var enabled := false
const MAX_LIVE := 16                       # at most this many spell lights at once (a raid's casting) ...
const MAX_STEADY := 24                     # ... and weapon / monster lights
static var _colors := {}                   # effect path -> Color
static var _tex_colors := {}               # texture instance id -> Color (rgb) with a weight in a
static var _live: Array = []
static var _steady: Array = []


## Remastered on / off (SkySystem): off takes every effect light away.
static func set_enabled(on: bool) -> void:
	enabled = on
	if not on:
		for l in _live + _steady:
			if is_instance_valid(l):
				(l as Node).queue_free()
		_live.clear()
		_steady.clear()


## A light on an effect (a NifScene or its holder); null when off, the colour is too dark, or there are too many.
## fade_s > 0: it dies away over that time (a spell's duration; `fades` false: the caller fades it - hit); 0: it stays
## (weapon / monster effects).
static func attach(fx: Node3D, energy: float, range_m: float, fade_s := 0.0, fades := true) -> OmniLight3D:
	if not enabled or fx == null or not is_instance_valid(fx) or not fx.is_inside_tree():
		return null
	_live = _live.filter(func(l): return is_instance_valid(l))
	_steady = _steady.filter(func(l): return is_instance_valid(l))
	if (fade_s > 0.0 and _live.size() >= MAX_LIVE) or (fade_s <= 0.0 and _steady.size() >= MAX_STEADY):
		return null
	var c := color_of(fx)
	if c.v < 0.15:
		return null
	var o := OmniLight3D.new()
	o.name = "FxLight"
	o.light_color = c
	o.light_energy = energy
	o.omni_range = range_m
	o.omni_attenuation = 1.4
	o.shadow_enabled = false
	o.light_volumetric_fog_energy = 0.6
	o.distance_fade_enabled = true
	o.distance_fade_begin = 40.0
	o.distance_fade_length = 15.0
	o.position = Vector3(0, 0.3, 0)
	fx.add_child(o)
	(_live if fade_s > 0.0 else _steady).append(o)
	if fade_s > 0.0 and fades:
		var tw := o.create_tween()
		tw.tween_interval(fade_s * 0.4)                   # full while the effect is at its brightest ...
		tw.tween_property(o, "light_energy", 0.0, fade_s * 0.6)   # ... then dying with it
	return o


## A landed spell's light (SpellFx._play, everything but a held glow; owner 2026-11-09: "For big hits like DD, the
## light should explode out then fade pretty quickly, like an explosion. Bigger for bigger spells. The light can linger
## as long as the spell effect lives ... poison clouds, but those should be smaller"):
##   - impact > 0 (a damage spell's hit, 0.6 - 2.5 by its damage: ClassDb.effect_impact): a flash out to its peak in a
##     few hundredths of a second, falling away in about a third of one to a small glow
##   - that glow - or, for anything else (a poison's drip, a debuff, a buff, a heal), a smaller soft light that comes up
##     gently, its size by the effect's - stays while the effect is there and goes out with it.
const FLASH_IN := 0.04
const FLASH_OUT := 0.35
static func hit(fx: Node3D, life_s: float, impact := 0.0) -> OmniLight3D:
	var o := attach(fx, 0.0, 1.0, life_s, false)
	if o == null:
		return null
	var ext := extent(fx)
	var kl := clampf(ext / 12.0, 0.4, 1.2)                # the effect's own size, for its glow (a drip ~0.7)
	var glow_e := 0.3 + 0.2 * kl
	var glow_r := 1.5 + 1.2 * kl
	var hold := maxf(life_s * 0.75, 0.1)
	var tw := o.create_tween()
	o.light_energy = 0.0
	if impact > 0.0:
		glow_e = 0.25 + 0.15 * impact
		glow_r = 2.0 + 0.8 * impact
		o.omni_range = 4.0 + 4.0 * impact
		o.omni_attenuation = 1.0                          # (a hard, wide flash)
		tw.tween_property(o, "light_energy", 4.0 + 3.0 * impact, FLASH_IN)
		tw.tween_property(o, "light_energy", glow_e, FLASH_OUT).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
		tw.parallel().tween_property(o, "omni_range", glow_r, FLASH_OUT).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
		tw.parallel().tween_property(o, "omni_attenuation", 1.4, FLASH_OUT)
		hold = maxf(hold - FLASH_IN - FLASH_OUT, 0.05)
	else:
		o.omni_range = glow_r
		var up := minf(0.3, life_s * 0.2)
		tw.tween_property(o, "light_energy", glow_e, up).set_trans(Tween.TRANS_SINE)
		hold = maxf(hold - up, 0.05)
	tw.tween_interval(hold)
	tw.tween_property(o, "light_energy", 0.0, maxf(life_s * 0.25, 0.1))   # out with the effect
	o.set_meta("k", impact)
	o.set_meta("ext", ext)
	return o


## How big an effect is in the world (metres across): its particles' reach and its meshes' bounds, at its scale.
static func extent(fx: Node3D) -> float:
	var best := 0.0
	for gp in fx.find_children("*", "GPUParticles3D", true, false):
		var p := gp as GPUParticles3D
		best = maxf(best, p.visibility_aabb.size.x * p.global_basis.get_scale().x)
	for mi in fx.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh:
			var a := m.get_aabb()
			best = maxf(best, maxf(a.size.x, a.size.z) * m.global_basis.get_scale().x)
	return best


## A spell effect done (SpellFx.release, back to its pool): its light goes with it.
static func detach(fx: Node) -> void:
	if fx == null:
		return
	for c in fx.get_children():
		if c is OmniLight3D and c.name.begins_with("FxLight"):
			c.queue_free()


## The effect's colour: its particles' textures (bright, opaque texels weighted most) tinted by their colour ramps,
## brightened so the strongest channel is full.
static func color_of(fx: Node) -> Color:
	var key := String(fx.get_meta("fx_path", fx.scene_file_path))
	if key != "" and _colors.has(key):
		return _colors[key]
	var sum := Vector3.ZERO
	var weight := 0.0
	for gp in fx.find_children("*", "GPUParticles3D", true, false):
		var p := gp as GPUParticles3D
		var tex: Texture2D = null
		var mesh := p.draw_pass_1
		if mesh and mesh.surface_get_material(0) is StandardMaterial3D:
			tex = (mesh.surface_get_material(0) as StandardMaterial3D).albedo_texture
		elif mesh and mesh.surface_get_material(0) is ShaderMaterial:
			tex = (mesh.surface_get_material(0) as ShaderMaterial).get_shader_parameter("tex")
		var tc := _texture_color(tex)
		var ramp := Color(1, 1, 1)
		var pm := p.process_material as ParticleProcessMaterial
		if pm and pm.color_ramp is GradientTexture1D and (pm.color_ramp as GradientTexture1D).gradient:
			var g := (pm.color_ramp as GradientTexture1D).gradient
			var acc := Color(0, 0, 0)
			for i in g.get_point_count():
				acc += g.get_color(i)
			ramp = acc / maxf(float(g.get_point_count()), 1.0)
		var w := tc.a * float(maxi(p.amount, 1))
		sum += Vector3(tc.r * ramp.r, tc.g * ramp.g, tc.b * ramp.b) * w
		weight += w
	# the effect's own meshes (rings, swirls, flares: many spell effects are animated textured meshes, no particles)
	for mi in fx.find_children("*", "MeshInstance3D", true, false):
		var m3 := mi as MeshInstance3D
		if m3.mesh == null:
			continue
		for i in m3.mesh.get_surface_count():
			var mat := m3.get_active_material(i)
			var tex: Texture2D = null
			var tint := Color(1, 1, 1)
			if mat is StandardMaterial3D:
				tex = (mat as StandardMaterial3D).albedo_texture
				tint = (mat as StandardMaterial3D).albedo_color
			elif mat is ShaderMaterial:
				var t = (mat as ShaderMaterial).get_shader_parameter("base_tex")
				tex = t if t is Texture2D else null
				var tn = (mat as ShaderMaterial).get_shader_parameter("tint")
				tint = tn if tn is Color else Color(1, 1, 1)
			var tc := _texture_color(tex)
			var w := tc.a * 40.0
			sum += Vector3(tc.r * tint.r, tc.g * tint.g, tc.b * tint.b) * w
			weight += w
	var c := Color(1, 1, 1) if weight <= 0.0 else Color(sum.x / weight, sum.y / weight, sum.z / weight)
	var m := maxf(c.r, maxf(c.g, c.b))
	if m > 0.001:
		c = Color(c.r / m, c.g / m, c.b / m)
	if weight <= 0.0:
		c = Color(0, 0, 0)                               # (nothing drawn: no light)
	if key != "":
		_colors[key] = c
	return c


static func _texture_color(tex: Texture2D) -> Color:
	if tex == null:
		return Color(1, 1, 1, 1)
	var id := tex.get_instance_id()
	if _tex_colors.has(id):
		return _tex_colors[id]
	var img := tex.get_image()
	var out := Color(1, 1, 1, 1)
	if img:
		img = img.duplicate()
		if img.is_compressed():
			img.decompress()
		img.resize(16, 16, Image.INTERPOLATE_BILINEAR)
		var acc := Vector3.ZERO
		var w := 0.0
		for y in 16:
			for x in 16:
				var p := img.get_pixel(x, y)
				var k := p.a * p.v                       # bright, opaque texels are the light
				acc += Vector3(p.r, p.g, p.b) * k
				w += k
		if w > 0.0:
			out = Color(acc.x / w, acc.y / w, acc.z / w, clampf(w / 64.0, 0.05, 1.0))
	_tex_colors[id] = out
	return out
