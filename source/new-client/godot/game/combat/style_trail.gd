class_name StyleTrail
extends Node3D
## The colour flash of a combat style, drawn as the client draws it (game.dll 0x46da71 / 0x46debd; owner 2026-10-17:
## the old afterimage copies looked "really delayed / slow framerate"): one ribbon swept between the held weapon's
## TRAILBASE and TRAILTIP nodes (content/weapons/trails.json, pipeline/add_weapon_trails.py), in the style's Red /
## Green / Blue (styles.csv). From Buildup ms into the swing to Duration ms the trail lays a new base / tip pair each
## time the tip has moved 5 units (0.125 m), 33 pairs at most; every pair fades over a third of a second as it ages,
## the first 0.2 s of the trail fade in and its last 0.1 s fade out. A weapon without the two nodes leaves no trail
## (as in the client). The ribbon follows the wielder (it's kept in the skeleton's frame) so a running swing doesn't
## smear behind.

const STEP := 0.125                          # m the tip moves before the next pair (the client's 5 units)
const MAX_PAIRS := 33                        # the client's strip: 0x42 vertices
const AGE_RATE := 3.0                        # the fade a pair gains each second (the client's V += dt x 3)
const ALPHA := 0.99
const BASE_ALPHA := 0.35                     # the edge at the weapon's base softer than its tip

var _points: Array = []                      # [[weapon model Node3D, base Vector3, tip Vector3]] (model space)
var _frame: Node3D                           # the wielder's skeleton: the ribbon kept in its space
var _color := Color.WHITE
var _wait := 0.0                             # s until the trail starts (Buildup)
var _span := 0.6                             # s it lays pairs for (Duration - Buildup)
var _t := 0.0                                # s since it started
var _pairs: Array = []                       # per weapon: [[base local, tip local, start fade, age]]
var _mesh: ImmediateMesh
var _mi: MeshInstance3D
static var _trails := {}


## Starts a trail on these weapon nodes (the held weapons' bone attachments) for one style.
static func play(world: Node, weapons: Array, trail: Variant) -> void:
	if not (trail is Dictionary) or weapons.is_empty() or int(trail.get("images", 0)) <= 0:
		return
	if glow_on and glow(weapons, trail):
		return
	var t := StyleTrail.new()
	for w in weapons:
		if is_instance_valid(w):
			var p := _trail_points(w)
			if not p.is_empty():
				t._points.append(p)
				if t._frame == null:
					t._frame = (w as Node).get_parent() as Node3D
	if t._points.is_empty() or t._frame == null:
		t.free()
		return
	var rgb: Array = trail.get("rgb", [255, 255, 255])
	t._color = Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))
	t._wait = float(trail.get("buildup", 400)) / 1000.0
	t._span = maxf(0.05, (float(trail.get("ms", 1000)) - float(trail.get("buildup", 400))) / 1000.0)
	for _i in t._points.size():
		t._pairs.append([])
	world.add_child(t)


## The style's colour as a weapon effect instead of the ribbon (owner 2026-11-10: "it loads a weapon effect instead
## when it triggers (kind of like how holding the power attack now does) ... trying to match the color that the replaced
## trail was"): the client's own item glows (spweapons.csv, WeaponModels.add_effect), the one made for the weapon's shape
## in the trail's colour - borrowed from a weapon of the nearest shape when its own family has no such colour. It lights
## at the trail's Buildup and goes out at the end of the swing. A colour none fits (black) keeps the ribbon.
static var glow_on := true
const GLOW_FADE_S := 0.15
const GLOW_LEAD := 0.25                       # the share of the wind-up before the glow lights
const GLOW_SCALE := 0.85
# weapon family -> trail colour -> weapon effect number (content/weapons/weapon_effects.json)
## An entry is the effect itself, or [effect, true]: the two-hander's silver glow recoloured to the trail's colour (a
## family without that colour). The client's blade glows sit along any one-hand weapon; the axe / hammer / mace ones
## sat round the hilt of a sword (owner 2026-11-10 look), so every one-hand weapon takes the sword's, smaller on the
## short ones (daggers, dirks, claws).
const GLOWS := {
	"one": {"yellow": 11, "green": [31, true], "red": 12, "purple": [31, true], "blue": 9, "white": 31, "orange": 7},
	"2h": {"yellow": 32, "green": 33, "red": 30, "purple": [31, true], "blue": 27, "white": 31, "orange": 21},
	"pole": {"yellow": 78, "green": 75, "red": 76, "purple": 88, "blue": 81, "white": 89, "orange": 85},
	"staff": {"yellow": 92, "green": [92, true], "red": 94, "purple": [90, true], "blue": 90, "white": [92, true],
			"orange": [92, true]},
}
const SHORT_SCALE := 0.6


## The weapon's family for its glow (objects.csv stance): "one", "short" (thrust weapons, hand to hand, the pierce
## sound set), "2h", "pole", "staff"; "" for none (ranged, instruments, shields).
static func glow_family(model: int) -> String:
	var i := WeaponModels.info(model)
	if i.is_empty() or int(i.get("shield", 0)) != 0:
		return ""
	match int(i.get("stance", 1)):
		2, 14:
			return "2h"
		3:
			return "pole"
		4:
			return "staff"
		5, 6, 8, 0:
			return ""
		7, 13:
			return "short"
	return "short" if int(i.get("sound_set", 1)) == 21 else "one"


## A trail colour's name: the hue's band, white when washed out, black when dark.
static func color_name(c: Color) -> String:
	if c.v < 0.15:
		return "black"
	if c.s < 0.2:
		return "white"
	var h := c.h * 360.0
	if h < 15.0 or h >= 335.0:
		return "red"
	if h < 40.0:
		return "orange"
	if h < 75.0:
		return "yellow"
	if h < 170.0:
		return "green"
	if h < 265.0:
		return "blue"
	return "purple"


## The glows for one style on these weapons; false when none could be shown (the caller draws the ribbon).
static func glow(weapons: Array, trail: Dictionary) -> bool:
	var rgb: Array = trail.get("rgb", [255, 255, 255])
	var cname := color_name(Color8(int(rgb[0]), int(rgb[1]), int(rgb[2])))
	# lit a quarter of the way into the client's wind-up (owner 2026-11-10: "they activate a bit slow"), out at the
	# swing's end as before
	var wait := maxf(0.0, float(trail.get("buildup", 400)) / 1000.0) * GLOW_LEAD
	var span := maxf(0.15, float(trail.get("ms", 1000)) / 1000.0 - wait)
	var shown := false
	for w in weapons:
		if not is_instance_valid(w):
			continue
		for h in (w as Node).get_children():
			var n := String(h.name)
			if not n.begins_with("Weapon_") or (h as Node).get_child_count() == 0:
				continue
			var fam := glow_family(int(n.trim_prefix("Weapon_")))
			var pick: Variant = GLOWS.get("one" if fam == "short" else fam, {}).get(cname, 0)
			var effect := int(pick[0]) if pick is Array else int(pick)
			if effect <= 0 or WeaponModels.effect_path(effect) == "":
				continue
			shown = true
			var tint := Color8(int(rgb[0]), int(rgb[1]), int(rgb[2])) if pick is Array else Color.WHITE
			_glow_one(h as Node3D, effect, wait, span, tint, SHORT_SCALE if fam == "short" else 1.0)
	return shown


static func _glow_one(holder: Node3D, effect: int, wait: float, span: float, tint := Color.WHITE, size := 1.0) -> void:
	if wait > 0.0:
		await holder.get_tree().create_timer(wait, false).timeout
	if not is_instance_valid(holder) or not holder.is_inside_tree():
		return
	var old := holder.get_node_or_null("StyleGlow")
	if old:
		old.free()                                          # (a style on the heels of the last one)
	var fx := WeaponModels.add_effect(holder, effect)
	if fx == null:
		return
	fx.name = "StyleGlow"
	fx.scale *= GLOW_SCALE * size
	NifParticles.fit_to_scale(fx)
	if tint != Color.WHITE:
		recolor(fx, tint)
	await holder.get_tree().create_timer(span, false).timeout
	if not is_instance_valid(fx):
		return
	var parts := fx.find_children("*", "GeometryInstance3D", true, false)
	var lights := fx.find_children("FxLight*", "OmniLight3D", true, false)
	var t := fx.create_tween().set_parallel(true)
	for g in parts:
		t.tween_property(g, "transparency", 1.0, GLOW_FADE_S)
	for l in lights:
		t.tween_property(l, "light_energy", 0.0, GLOW_FADE_S)
	t.chain().tween_callback(fx.queue_free)


## Recolour an effect (its own copies of the materials): every colour in it times the tint, the tint brought up to full
## brightness so a pale glow takes the colour without going dark; its light too.
static func recolor(fx: Node, tint: Color) -> void:
	var m := maxf(tint.r, maxf(tint.g, tint.b))
	var t := Color(tint.r / m, tint.g / m, tint.b / m) if m > 0.0 else Color.WHITE
	for n in fx.find_children("*", "", true, false):
		if n is OmniLight3D:
			(n as OmniLight3D).light_color = t
		if n is CPUParticles3D:
			(n as CPUParticles3D).color *= t
		if n is GeometryInstance3D:
			var g := n as GeometryInstance3D
			if g.material_override:
				g.material_override = _tinted(g.material_override, t)
			if g is MeshInstance3D and (g as MeshInstance3D).mesh:
				var mi := g as MeshInstance3D
				for i in mi.mesh.get_surface_count():
					var mat := mi.get_active_material(i)
					if mat:
						mi.set_surface_override_material(i, _tinted(mat, t))
			if g is GPUParticles3D:
				var gp := g as GPUParticles3D
				if gp.process_material is ParticleProcessMaterial:
					# (NifParticles: the colour ramp times this colour) - the tint over the ramp's own cast, so a frosty
					# blue glow tinted purple comes out purple, not blue-purple
					var pm := gp.process_material.duplicate() as ParticleProcessMaterial
					var cast := Color.WHITE
					if pm.color_ramp is GradientTexture1D and (pm.color_ramp as GradientTexture1D).gradient:
						var gr := (pm.color_ramp as GradientTexture1D).gradient
						var sum := Color(0, 0, 0)
						for k in gr.get_point_count():
							var c := gr.get_color(k)
							sum += Color(c.r * c.a, c.g * c.a, c.b * c.a)
						var top := maxf(sum.r, maxf(sum.g, sum.b))
						if top > 0.0:
							cast = Color(maxf(sum.r / top, 0.25), maxf(sum.g / top, 0.25), maxf(sum.b / top, 0.25))
					pm.color = Color(pm.color.r * t.r / cast.r, pm.color.g * t.g / cast.g, pm.color.b * t.b / cast.b, pm.color.a)
					gp.process_material = pm
				for i in gp.draw_passes:
					var dm := gp.get_draw_pass_mesh(i)
					if dm:
						dm = dm.duplicate()
						for si in dm.get_surface_count():
							var sm := dm.surface_get_material(si)
							if sm:
								dm.surface_set_material(si, _tinted(sm, t))
						gp.set_draw_pass_mesh(i, dm)
			if g is CPUParticles3D and (g as CPUParticles3D).mesh:
				var cm := (g as CPUParticles3D).mesh.duplicate() as Mesh
				for si in cm.get_surface_count():
					var sm := cm.surface_get_material(si)
					if sm:
						cm.surface_set_material(si, _tinted(sm, t))
				(g as CPUParticles3D).mesh = cm


static func _tinted(mat: Material, t: Color) -> Material:
	var c := mat.duplicate() as Material
	if c is BaseMaterial3D:
		var b := c as BaseMaterial3D
		b.albedo_color = Color(b.albedo_color.r * t.r, b.albedo_color.g * t.g, b.albedo_color.b * t.b, b.albedo_color.a)
		if b.emission_enabled:
			b.emission = Color(b.emission.r * t.r, b.emission.g * t.g, b.emission.b * t.b)
	elif c is ShaderMaterial:
		var sh := c as ShaderMaterial
		for pname in ["tint", "emissive"]:                      # (NifMaterials' own)
			var v = sh.get_shader_parameter(pname)
			if v is Color:
				sh.set_shader_parameter(pname, Color((v as Color).r * t.r, (v as Color).g * t.g, (v as Color).b * t.b, (v as Color).a))
	return c


## A held weapon's [model node, base, tip]: its Weapon_<model> holder's model and that model's client trail points.
static func _trail_points(attachment: Node) -> Array:
	if _trails.is_empty():
		var j = JSON.parse_string(FileAccess.get_file_as_string("res://content/weapons/trails.json")) 				if FileAccess.file_exists("res://content/weapons/trails.json") else null
		_trails = j if j is Dictionary else {"_": []}
	for h in attachment.get_children():
		var n := String(h.name)
		if not n.begins_with("Weapon_") or (h as Node).get_child_count() == 0:
			continue
		var p: Array = _trails.get(n.trim_prefix("Weapon_"), [])
		if p.size() == 2:
			return [(h as Node).get_child(0), Vector3(p[0][0], p[0][1], p[0][2]), Vector3(p[1][0], p[1][1], p[1][2])]
	return []


## The weapons in a model's hands (the bone attachments on the Held / Hand bones, and the greaves' Shield bones - not the belt or back;
## a shield has no trail).
static func held(model: Node) -> Array:
	var out: Array = []
	if model == null or not is_instance_valid(model):
		return out
	for a in model.find_children("*", "BoneAttachment3D", true, false):
		var bone := String((a as BoneAttachment3D).bone_name)
		if bone in ["Bip01 R Held", "Bip01 L Held", "Bip01 R Hand", "Bip01 R Shield", "Bip01 L Shield"]:   # (greaves: Shield)
			out.append(a)
	return out


## A style row's trail: its own (styles.json) or, for the monster / pet rows of npcs.json / pets.json, the class
## style with the same StyleID.
static func trail_of(style: Dictionary, two_hand := false) -> Variant:
	var key := "trail_2h" if two_hand else "trail"
	if style.get(key) is Dictionary:
		return style[key]
	return ClassDb.style(int(style.get("styleid", 0))).get(key)


## A monster's / pet's style: the style is decided at the blow's impact, part way through its swing - the trail
## covers the rest of the swing from there (its Imagenum over half a second).
static func play_from_impact(world: Node, model: Node, style: Dictionary) -> void:
	var trail: Variant = trail_of(style)
	if not (trail is Dictionary):
		return
	var t: Dictionary = (trail as Dictionary).duplicate()
	t["buildup"] = 0
	t["ms"] = 500
	play(world, held(model), t)


## The server's game (0.36c): CombatAnimation carries the style as a styles.csv row - its trail from
## content/rules/style_fx.json (pipeline/build_style_anims.py: [Imagenum, Duration ms, Buildup ms, Red, Green, Blue,
## Hit Effect]). Null without one (owner 2026-10-16: no style colour flashes in the server's game - only the offline
## combat started trails).
static var _rows := {}


static func of_row(row: int) -> Variant:
	if _rows.is_empty():
		var t = JSON.parse_string(FileAccess.get_file_as_string("res://content/rules/style_fx.json")) 				if FileAccess.file_exists("res://content/rules/style_fx.json") else null
		_rows = t if t is Dictionary else {"_": []}
	var f: Array = _rows.get(str(row), [])
	if f.size() < 6 or int(f[0]) <= 0:
		return null
	return {"images": int(f[0]), "ms": int(f[1]), "buildup": int(f[2]), "rgb": [int(f[3]), int(f[4]), int(f[5])]}


func _ready() -> void:
	top_level = true
	global_transform = Transform3D.IDENTITY
	_mesh = ImmediateMesh.new()
	_mi = MeshInstance3D.new()
	_mi.mesh = _mesh
	_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.vertex_color_use_as_albedo = true
	_mi.material_override = m
	add_child(_mi)


func _process(delta: float) -> void:
	if not is_instance_valid(_frame):
		queue_free()
		return
	if _wait > 0.0:
		_wait -= delta
		if _wait > 0.0:
			return
		delta = -_wait                                     # the part of this frame after the start
	_t += delta
	var to_frame := _frame.global_transform.affine_inverse()
	var alive := false
	for i in _points.size():
		var pairs: Array = _pairs[i]
		for q in pairs:
			q[3] += delta * AGE_RATE
		while not pairs.is_empty() and float(pairs[0][2]) + float(pairs[0][3]) >= 1.0:
			pairs.pop_front()                               # faded out
		var p: Array = _points[i]
		var held: Variant = p[0]
		var w: Node3D = held as Node3D if is_instance_valid(held) else null   # (a weapon freed mid-swing: a
		if _t <= _span and w != null and w.is_visible_in_tree():               # companion gone, a weapon swap)
			var base := to_frame * (w.global_transform * (p[1] as Vector3))
			var tip := to_frame * (w.global_transform * (p[2] as Vector3))
			var last_tip: Vector3 = pairs[-1][1] if not pairs.is_empty() else Vector3.INF
			if pairs.is_empty() or (_frame.global_transform.basis * (tip - last_tip)).length() >= STEP:
				var fade := 0.0                              # the trail's own fade in / out (the new pair's V)
				if _t < 0.2:
					fade = (0.2 - _t) * 5.0
				elif _t > _span - 0.1:
					fade = (_t - (_span - 0.1)) * 5.0
				pairs.append([base, tip, clampf(fade, 0.0, 1.0), 0.0])
				if pairs.size() > MAX_PAIRS:
					pairs.pop_front()
		alive = alive or not pairs.is_empty() or _t <= _span
	_rebuild()
	if not alive:
		queue_free()


## The ribbons, rebuilt each frame in world space from the skeleton's frame.
func _rebuild() -> void:
	_mesh.clear_surfaces()
	var tf := _frame.global_transform
	for pairs in _pairs:
		if pairs.size() < 2:
			continue
		_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
		for q in pairs:
			var a := ALPHA * (1.0 - clampf(float(q[2]) + float(q[3]), 0.0, 1.0))
			_mesh.surface_set_color(Color(_color, a * BASE_ALPHA))
			_mesh.surface_add_vertex(tf * (q[0] as Vector3))
			_mesh.surface_set_color(Color(_color, a))
			_mesh.surface_add_vertex(tf * (q[1] as Vector3))
		_mesh.surface_end()
