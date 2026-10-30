class_name NifMaterials
extends RefCounted
## Engine materials for converted DAoC models. pipeline/nif_static.py writes each model's materials into the glTF
## (extras.nif_materials): every texture slot with its texture coordinate (0 = UV, 1 = UV2, 2/3 = CUSTOM0.xy/.zw),
## wrap mode, alpha, sidedness, vertex colours and colours. This builds one ShaderMaterial per spec that layers them
## the way the original renderer did: base x tint x dark (light map) x detail (pre-doubled), decal over the top,
## vertex colour multiply, glow and emissive added, gloss as the specular mask. Every layer is weighted by its own
## alpha, because DAoC also puts transparent overlays (vines, lichen) in the dark and detail slots.

const SLOTS := ["base", "dark", "detail", "decal", "glow", "gloss", "tex1", "tex2", "env"]

var texture_set := "x4plus"
var env_strength := 1.0          # how strong the environment-map reflections are (zone_loader: Tuscaran Glacier)
var use_material_light := false     # pregame scenes: keep the material's ambient darkness (spec mat_light), as the client
var _folders := {}                  # texture set name -> folder with <name>.png
var _shaders := {}                  # variant key -> Shader
var _materials := {}                # spec json -> ShaderMaterial
var _textures := {}                 # "set/name" -> Texture2D
var world := false                  # a zone's own models (ZoneLoader): the remastered world shading (SHADER_BODY's WORLD)


## The remastered world look's global shader values (SHADER_BODY), made once before any shader uses them.
static var _globals_lock := Mutex.new()
static var _globals_done := false
const GLOBALS := {"remaster_fx": [RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.0],
		"zone_fill": [RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3.ZERO],
		"relief_strength": [RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.12],
		"shine_strength": [RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.6],
		"wind_strength": [RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 1.0],
		"foliage_light": [RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.7]}


static func ensure_globals() -> void:
	if _globals_done:
		return
	_globals_lock.lock()
	if not _globals_done:
		for k in GLOBALS:                                # (only made here; the engine's list is editor-only)
			RenderingServer.global_shader_parameter_add(k, GLOBALS[k][0], GLOBALS[k][1])
		_globals_done = true
	_globals_lock.unlock()


func _init(folders: Dictionary, initial_set: String) -> void:
	_folders = folders
	texture_set = initial_set if folders.has(initial_set) else folders.keys()[0]


static var WEB := RegEx.create_from_string("(?i)spiderweb|cob_crnr|cobweb")


## Material for one spec (a Dictionary from extras.nif_materials); identical specs share one material.
func material(spec: Dictionary) -> ShaderMaterial:
	var key := JSON.stringify(spec, "", true)
	if _materials.has(key):
		return _materials[key]
	var mat := ShaderMaterial.new()
	var alpha := String(spec.get("alpha", "opaque"))
	# spider webs (nspiderweb, cob_crnr): soft alpha the client blended - as a cut-out at their near-zero test
	# threshold they drew as solid white sheets (owner 2026-10-11: Myrkwood's Creepy Web Pine). Only webs: grass,
	# leaves, beams and banners share the low threshold but their alpha is all or nothing - a cut-out is right there.
	if alpha == "mask" and WEB.search(String((spec.get("slots", {}) as Dictionary).get("base", {}).get("tex", ""))):
		alpha = "blend"
	var dt: Array = spec.get("diffuse_tint", [])
	mat.shader = _shader(alpha, bool(spec.get("double_sided", false)), bool(spec.get("unlit", false)), dt.size() == 3,
			bool(spec.get("ambient_only", false)), bool(spec.get("src_invdest", false)) or String(spec.get("dest_keep", "")) == "invsrcalpha")
	if dt.size() == 3:                                    # ambient and diffuse colours of different hues (see _shader)
		mat.set_shader_parameter("diffuse_tint", Vector3(float(dt[0]), float(dt[1]), float(dt[2])))
		var tn: Array = spec.get("tint", [1, 1, 1])
		var dc: Array = spec.get("diffuse", [float(tn[0]) * float(dt[0]), float(tn[1]) * float(dt[1]), float(tn[2]) * float(dt[2])])
		mat.set_shader_parameter("diffuse_col", Vector3(float(dc[0]), float(dc[1]), float(dc[2])))
		mat.set_shader_parameter("split_tint", true)
	mat.set_meta("spec", spec)
	var slots: Dictionary = spec.get("slots", {})
	for slot in SLOTS:
		var has: bool = slots.has(slot)
		mat.set_shader_parameter("has_" + slot, has)
		if has:
			mat.set_shader_parameter(slot + "_uv", int(slots[slot].uv))
			mat.set_shader_parameter(slot + "_wrap", bool(slots[slot].get("wrap", true)))
	if slots.has("env"):
		mat.set_shader_parameter("env_strength", env_strength)
	var tint: Array = spec.get("tint", [1, 1, 1])
	var emissive: Array = spec.get("emissive", [0, 0, 0])
	var k := 1.0
	if use_material_light:
		# fixed-function light: texture x min(emissive + material ambient x ambient light, 1). Our shader adds lit
		# albedo and emission, so cap the albedo part where the emissive already fills the light (sky domes,
		# grass cards); vertex-coloured shapes take their light from the vertex colours
		var e: float = maxf(maxf(float(emissive[0]), float(emissive[1])), float(emissive[2]))
		var m: float = 1.0 if bool(spec.get("vertex_colors", false)) else float(spec.get("mat_light", 1.0))
		k = clampf(minf(m, 1.0 - e), 0.0, 1.0)
	mat.set_shader_parameter("tint", Color(tint[0], tint[1], tint[2]))
	mat.set_shader_parameter("light_scale", k)
	mat.set_shader_parameter("emissive", Color(emissive[0], emissive[1], emissive[2]))
	mat.set_shader_parameter("use_vertex_color", bool(spec.get("vertex_colors", false)))
	mat.set_shader_parameter("alpha_cut", float(spec.get("cut", 0.5)))
	mat.set_shader_parameter("opacity", float(spec.get("opacity", 1.0)))
	mat.set_shader_parameter("specular_amount", 0.5 if spec.get("specular", false) else 0.25)
	mat.set_shader_parameter("blend2", bool(spec.get("blend2", false)))
	mat.set_shader_parameter("detail_x2", bool(spec.get("detail_x2", false)))
	mat.set_shader_parameter("dark_plain", bool(spec.get("dark_plain", false)))
	mat.set_shader_parameter("billboard", {"face": 1, "up": 2}.get(String(spec.get("billboard", "")), 0))
	var scroll: Dictionary = spec.get("uv_scroll", {})        # NiTextureTransformController: looping scrolls
	for slot in scroll:
		var sc: Array = scroll[slot]
		mat.set_shader_parameter(String(slot) + "_scroll", Vector3(float(sc[0]), float(sc[1]), float(sc[2])))
	_bind_textures(mat)
	_materials[key] = mat
	return mat


func set_texture_set(set_name: String) -> void:
	if not _folders.has(set_name):
		return
	texture_set = set_name
	for mat in _materials.values():
		_bind_textures(mat)


func _bind_textures(mat: ShaderMaterial) -> void:
	var slots: Dictionary = mat.get_meta("spec").get("slots", {})
	for slot in slots:
		mat.set_shader_parameter(slot + "_tex", texture(String(slots[slot].tex)))


func _path(tex_name: String) -> String:
	var path := String(_folders[texture_set]).path_join(tex_name + ".png")
	if not FileAccess.file_exists(path) and _folders.has("original"):
		path = String(_folders["original"]).path_join(tex_name + ".png")   # not upscaled yet: use the client's own
	return path


## The texture's picture read from its file (null if none) - never Texture2D.get_image(), which reads the texture
## back from the GPU: on the seamless-zone worker that broke the frame being drawn ("open draw list"), and every
## texture made after it drew black / pink (owner 2026-10-17: black skeletons and horses, pink forge smoke).
func image(tex_name: String) -> Image:
	return Image.load_from_file(_path(tex_name)) if FileAccess.file_exists(_path(tex_name)) else null


var load_usec := 0                  # time spent reading textures (ZoneLoader's "built in" line)


# ---------------------------------------------------------------- compressed textures

## COMPRESSED TEXTURES (Options > Video, owner 2026-10-28: "let's build both, since you can toggle the compressed
## textures"): the world's textures are kept in the graphics card's own block-compressed format (BC1 / BC3 - what the
## original client's DDS files were) instead of raw colour - a quarter of the video memory or less, and read much
## faster. The first time a texture is used it is compressed and saved next to its picture as <name>.bc
## (mipmaps included); after that the .bc is read, unless the picture is newer. Off: the pictures as they are (each
## read from its PNG and its mipmaps made every time). Set by Graphics; worlds built after a change use it.
static var compress := true
const BC_VERSION := 1


static func load_image(path: String, allow_compress := true) -> Image:
	var bc := path.get_basename() + ".bc"
	if compress and allow_compress and FileAccess.file_exists(bc) and FileAccess.file_exists(path) \
			and FileAccess.get_modified_time(bc) >= FileAccess.get_modified_time(path):
		var f := FileAccess.open(bc, FileAccess.READ)
		if f:
			var d = f.get_var()
			f.close()
			if d is Dictionary and int((d as Dictionary).get("v", 0)) == BC_VERSION:
				var cached := Image.create_from_data(int(d.w), int(d.h), true, int(d.f) as Image.Format, d.data)
				if cached and not cached.is_empty():
					return cached
	var img := Image.load_from_file(path) if FileAccess.file_exists(path) else null
	if img == null:
		return null
	img.generate_mipmaps()
	if not (compress and allow_compress):
		return img
	# BC1 when it has no alpha, BC3 when it does (the engine picks); sizes that aren't multiples of 4 stay raw
	if img.get_width() % 4 != 0 or img.get_height() % 4 != 0:
		return img
	if img.compress(Image.COMPRESS_S3TC, Image.COMPRESS_SOURCE_SRGB) != OK or not img.is_compressed():
		return img
	var tmp := bc + ".tmp"
	var w := FileAccess.open(tmp, FileAccess.WRITE)
	if w:
		w.store_var({"v": BC_VERSION, "w": img.get_width(), "h": img.get_height(), "f": int(img.get_format()),
				"data": img.get_data()})
		w.close()
		DirAccess.remove_absolute(ProjectSettings.globalize_path(bc))
		DirAccess.rename_absolute(ProjectSettings.globalize_path(tmp), ProjectSettings.globalize_path(bc))
	return img
var load_count := 0


func texture(tex_name: String) -> Texture2D:
	var key := "%s/%s" % [texture_set, tex_name]
	if not _textures.has(key):
		var t0 := Time.get_ticks_usec()
		load_count += 1
		var path := _path(tex_name)
		var img := load_image(path)
		if img == null:
			push_warning("missing texture " + path)
			_textures[key] = null
		else:
			_textures[key] = ImageTexture.create_from_image(img)
		load_usec += Time.get_ticks_usec() - t0
	return _textures[key]


## invdest: the layer's source factor is INVDESTCOLOR (spec src_invdest, nif_static): its colour added in full (no
## alpha multiply) and, for a blend, its alpha only dims what's behind - a premultiplied blend (corpse lights ...).
## destcolor: source factor DESTCOLOR (nif_static): what's behind x (1 + colour), or with invdest (destination
## INVSRCALPHA, spec dest_keep) x (colour + 1 - alpha) - a multiply blend; black leaves what's behind as it was.
func _shader(alpha: String, double_sided: bool, unlit := false, split := false, ambient_only := false, invdest := false) -> Shader:
	var key := "%s/%s/%s/%s/%s/%s/%s" % [alpha, double_sided, unlit, split, ambient_only, invdest, world]
	if _shaders.has(key):
		return _shaders[key]
	var modes := ["cull_disabled" if double_sided else "cull_back"]
	unlit = unlit and alpha != "add" and alpha != "destcolor"   # spec "unlit": the client's emissive-only lighting mode
	if unlit and alpha != "screen":
		modes.append("unshaded")
	if alpha == "blend" and invdest:
		modes.append_array(["blend_premul_alpha", "depth_draw_never"])
	elif alpha == "blend":
		modes.append("depth_draw_opaque")
	elif alpha == "add":                                 # additive glows (flares, cores, plasma): no depth write
		# fog off: fogging an additive card ADDS the fog colour (torch flames turned into grey cones, owner 2026-10-09)
		modes.append_array(["blend_add", "depth_draw_never", "unshaded", "fog_disabled"])
	elif alpha == "screen":                              # client src SRCALPHA, dst INVSRCCOLOR (black-backed clouds)
		modes.append_array(["blend_mix", "depth_draw_never", "unshaded"])
	elif alpha == "destcolor":                           # behind x ALBEDO (above 1 brightens: the HDR buffer keeps it)
		modes.append_array(["blend_mul", "depth_draw_never", "unshaded", "fog_disabled"])
	ensure_globals()
	var defs := ""
	if world and not unlit and alpha in ["opaque", "mask", "blend"]:
		defs += "#define WORLD\n"                       # the world's own surfaces: remastered relief, fill (below)
		if ambient_only:
			defs += "#define FOLIAGE\n"                 # trees and bushes: wind, rounded canopy light
		if alpha == "mask":
			defs += "#define CUTOUT\n"                  # leaves, grass cards, fences: edges kept at a distance
		if ambient_only and alpha in ["mask", "blend"]:
			defs += "#define LEAVES\n"                  # the see-through part of a tree: the only part the wind moves
	var code := "shader_type spatial;\nrender_mode %s;\n" % ", ".join(modes) + defs + SHADER_BODY
	if ambient_only and not unlit and alpha != "add" and alpha != "screen":
		# the zone's nifs.csv "Ambient Only" column (trees, evergreens, bushes): the client lights these without any
		# shading - ambient plus the whole sun / moon light, no angle falloff, no shadows (Midgard noon: ambient
		# 0.42/0.49/0.60 + sun 0.5 = the owner's screenshot of a Small Evergreen at its texture's own colour). Their
		# cards share normals at the trunk line, which angle shading turned into a black column (owner 2026-10-14:
		# Malmohus' pines, "giant black lines"). Lamps and the torch still fall off with distance.
		code += """
uniform vec3 diffuse_tint = vec3(1.0);
void light() {
	float shade = 1.0;
#ifdef FOLIAGE
	// remastered: a canopy lit as a rough ball (NORMAL points out from the trunk, fragment()) - the sunny side
	// brighter, the far side in its own shade, never black
	shade = mix(1.0, 0.45 + 0.8 * clamp((dot(NORMAL, LIGHT) + 0.4) / 1.4, 0.0, 1.0), foliage_light * remaster_fx);
#endif
	DIFFUSE_LIGHT += (LIGHT_IS_DIRECTIONAL ? 1.0 : ATTENUATION) * LIGHT_COLOR / PI * diffuse_tint * shade;
}
"""
	elif split and not unlit and alpha != "add" and alpha != "screen":
		# the client's E_A_D lighting with an ambient colour of another hue than the diffuse: ALBEDO carries the
		# ambient colour (the ambient light shows it) and the direct light is tinted diffuse / ambient - so the sun
		# shows the diffuse colour, as the client (owner 2026-10-14: Jordheim's grass bright green, paths orange)
		# ... the direct light on the UNTINTED texture x the diffuse colour, as specular light (not multiplied by the
		# ambient-tinted ALBEDO): a ratio diffuse / ambient can't bring back a channel the ambient lacks (owner
		# 2026-10-15: Trollheim's ice wall, ambient 0 / 0.72 / 1 and diffuse 0.84 / 0.96 / 1, was cyan in the sun -
		# the old client's is pale). Where the ratio was exact (most materials) the result is the same as before.
		code += """
uniform vec3 diffuse_col = vec3(1.0);
void light() {
	SPECULAR_LIGHT += clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * ATTENUATION * LIGHT_COLOR / PI * split_raw * diffuse_col;
}
"""
	if unlit:                                            # unshaded draws ALBEDO alone: the emission is its colour
		code = code.replace("//UNLIT_OUT", "ALBEDO = EMISSION;")
	if alpha == "mask":
		# remastered world cut-outs (leaves, fences): the alpha raised with the mip level, so far trees don't thin out
		# into sticks, and sharpened to the pixel so the edge is clean instead of a jagged half-transparent fringe
		code = code.replace("//ALPHA_OUT", """float a = c.a * opacity;
#ifdef CUTOUT
	if (remaster_fx > 0.5) {
		a *= 1.0 + max(textureQueryLod(base_tex, pick(base_uv, base_wrap, vec2(textureSize(base_tex, 0)))).x, 0.0) * 0.22;
		a = clamp((a - alpha_cut) / max(fwidth(a), 0.0001) + 0.5, 0.0, 1.0);
		ALPHA = a;
		ALPHA_SCISSOR_THRESHOLD = 0.5;
	} else {
		ALPHA = a;
		ALPHA_SCISSOR_THRESHOLD = alpha_cut;
	}
#else
	ALPHA = a;
	ALPHA_SCISSOR_THRESHOLD = alpha_cut;
#endif""")
	elif alpha == "blend":
		code = code.replace("//ALPHA_OUT", "ALPHA = c.a * opacity;")
	elif alpha == "add":
		# unshaded, so the fixed-function light goes in here: texture x min(emissive + lit part, 1) (an emissive-only
		# flame card had light_scale 0 and drew nothing)
		code = code.replace("//ALPHA_OUT", "ALBEDO = c.rgb * min(emissive + vec3(light_scale), vec3(1.0)) * %s;" % (
				"opacity" if invdest else "c.a * opacity"))
	elif alpha == "destcolor":
		# the client blends in gamma space with its colour capped at 1 (fixed function): a mid grey brightens 1.5x in
		# gamma = 2.4x in our linear buffer, not 1.2x
		code = code.replace("//ALPHA_OUT", "ALBEDO = pow(pow(clamp(c.rgb * min(emissive + vec3(light_scale), vec3(1.0)), 0.0, 1.0), vec3(1.0 / 2.2)) + vec3(%s), vec3(2.2));" % (
				"1.0 - clamp(c.a * opacity, 0.0, 1.0)" if invdest else "1.0"))
	elif alpha == "screen":                              # c*a + behind*(1 - c*a) as a mix blend: alpha = brightest channel
		code = code.replace("//ALPHA_OUT", "float m = max(max(ALBEDO.r, ALBEDO.g), max(ALBEDO.b, 0.001));
	ALPHA = m * c.a * opacity;
	ALBEDO /= m;")
	var shader := Shader.new()
	shader.code = code
	_shaders[key] = shader
	return shader


const SHADER_BODY := """
// REMASTERED LIGHTING's world look (owner 2026-10-29; SkySystem sets them, the look panel tunes them)
global uniform float remaster_fx;      // 1 while remastered lighting is on
global uniform vec3 zone_fill;         // the zone's ambient tint, added back while bounce light (SDFGI) replaces it
global uniform float relief_strength;  // surface relief from the texture's light and dark (metres per unit)
global uniform float shine_strength;   // smoother, shinier light parts
global uniform float wind_strength;    // trees and bushes sway
global uniform float foliage_light;    // canopies shaded as rounded shapes
varying vec3 fol_n;
uniform sampler2D base_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D dark_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D detail_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D decal_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D glow_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D gloss_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D env_tex : source_color, filter_linear_mipmap, repeat_enable;   // NiTextureEffect sphere map
uniform bool has_env;
uniform float env_strength = 1.0;
uniform sampler2D tex1_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex2_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform bool has_tex1; uniform bool has_tex2; uniform int tex1_uv; uniform int tex2_uv;
uniform bool tex1_wrap = true; uniform bool tex2_wrap = true;
uniform bool blend2;            // client two-texture blend: mix(tex2, tex1, vertex alpha), vertex rgb = baked light
uniform bool detail_x2 = false; // detail texture stored as is: multiply x2 here (pregame light maps go above 1.0)
uniform bool dark_plain = false; // the dark map multiplies colour and alpha as the client's (an effect's shaping mask: NifScene)
uniform int billboard = 0;      // 1 face the camera, 2 turn about the up axis (NiBillboardNode)
uniform bool has_base; uniform bool has_dark; uniform bool has_detail;
uniform bool has_decal; uniform bool has_glow; uniform bool has_gloss;
uniform int base_uv; uniform int dark_uv; uniform int detail_uv; uniform int decal_uv; uniform int glow_uv; uniform int gloss_uv;
uniform bool base_wrap = true; uniform bool dark_wrap = true; uniform bool detail_wrap = true;
uniform bool decal_wrap = true; uniform bool glow_wrap = true; uniform bool gloss_wrap = true;
uniform vec3 tint : source_color = vec3(1.0);
uniform vec3 emissive : source_color = vec3(0.0);
uniform bool use_vertex_color;
uniform float alpha_cut = 0.5;
uniform float opacity = 1.0;
uniform float specular_amount = 0.25;
// NiTextureTransformController scrolls: (du, dv, period in s) per slot, 0 period = still
uniform vec3 base_scroll = vec3(0.0); uniform vec3 dark_scroll = vec3(0.0); uniform vec3 detail_scroll = vec3(0.0);
uniform vec3 decal_scroll = vec3(0.0); uniform vec3 glow_scroll = vec3(0.0);
// NiUVController that plays once / ping-pongs: the offset at the effect's time, set by NifScene (uv_anim)
uniform vec2 base_offset = vec2(0.0); uniform vec2 dark_offset = vec2(0.0); uniform vec2 detail_offset = vec2(0.0);
uniform vec2 decal_offset = vec2(0.0); uniform vec2 glow_offset = vec2(0.0);
uniform float light_scale = 1.0;   // pregame: the lit part only (emission keeps the full colour)
uniform bool split_tint = false;   // split light (_shader): the tint on ALBEDO only, split_raw keeps the colour without it
varying vec3 split_raw;

varying vec2 uv_a;
varying vec2 uv_b;
varying vec2 uv_c;
varying vec2 uv_d;
varying vec2 env_sm;               // the sphere map coordinate, per vertex as the client made it

void vertex() {
	if (billboard == 1) {
		// NetImmerse NiBillboardNode: the card's own +Z faces the camera and +Y is up. The vertices arrive axis-
		// converted (Godot = NIF x, z, -y), so take the NIF axes back: view right = x, up = NIF y, toward = NIF z
		// ... turned half round about the up axis: the card's +Z points AWAY from the camera (owner 2026-10-15: a corpse
		// light's 2.5 m streak cylinder is a dim ring round the flame with the core in front - pointed at the camera
		// it was a giant cone; a flat card looks the same from either side)
		VERTEX = vec3(-VERTEX.x, -VERTEX.z, -VERTEX.y);
		NORMAL = vec3(0.0, 0.0, 1.0);
		// at the node's own scale (an effect sized to its target - the cards were always drawn full size), facing the
		// camera's POSITION (not just its view plane): the corpse lights' cylinders off to the side of the screen ran
		// toward its middle as smears; facing the camera's position each is seen end-on, a ring round its core
		float s = length(MODEL_MATRIX[0].xyz);
		vec3 to_cam = INV_VIEW_MATRIX[3].xyz - MODEL_MATRIX[3].xyz;
		to_cam = length(to_cam) > 0.0001 ? normalize(to_cam) : INV_VIEW_MATRIX[2].xyz;
		vec3 right = cross(INV_VIEW_MATRIX[1].xyz, to_cam);
		right = length(right) > 0.0001 ? normalize(right) : INV_VIEW_MATRIX[0].xyz;
		vec3 up = cross(to_cam, right);
		MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * s, 0.0), vec4(up * s, 0.0), vec4(to_cam * s, 0.0), MODEL_MATRIX[3]);
	} else if (billboard == 2) {
		float s = length(MODEL_MATRIX[0].xyz);
		vec3 up = vec3(0.0, 1.0, 0.0);
		vec3 side = normalize(cross(up, INV_VIEW_MATRIX[2].xyz));
		vec3 fwd = normalize(cross(side, up));
		MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(side * s, 0.0), vec4(up * s, 0.0), vec4(fwd * s, 0.0), MODEL_MATRIX[3]);
	}
#ifdef FOLIAGE
	// a tree or bush (stands on its origin): a rounded normal for the canopy light
	fol_n = normalize(vec3(VERTEX.x, 0.6 + VERTEX.y * 0.12, VERTEX.z) + vec3(0.0, 0.001, 0.0));
	fol_n = normalize((MODELVIEW_MATRIX * vec4(fol_n, 0.0)).xyz);
#ifdef LEAVES
	// only the leaves move, so trunks stay put: branches sway from about 2.5 m up, more towards the top, and
	// every leaf flutters a little
	if (remaster_fx > 0.5 && wind_strength > 0.0) {
		vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
		float h = clamp(VERTEX.y / 6.0, 0.0, 1.6);
		float hb = clamp((VERTEX.y - 2.5) / 5.0, 0.0, 1.4);
		float ph = dot(MODEL_MATRIX[3].xyz, vec3(0.13, 0.0, 0.17));
		float sway = sin(TIME * 1.1 + ph) * 0.65 + sin(TIME * 2.3 + ph * 1.7) * 0.35;
		vec3 off = vec3(sway, 0.0, sway * 0.55) * 0.08 * hb * hb;
		off += vec3(sin(TIME * 6.5 + wp.x * 2.1 + wp.y * 3.1), sin(TIME * 7.9 + wp.z * 2.3) * 0.5,
				sin(TIME * 5.7 + wp.z * 1.9 + wp.y * 2.7)) * 0.025 * min(h * 2.0, 1.0);
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (off * wind_strength);
	}
#endif
#endif
	uv_a = UV;
	uv_b = UV2;
	uv_c = CUSTOM0.xy;
	uv_d = CUSTOM0.zw;
	if (has_env) {
		// the client's sphere-mapped environment map: NetImmerse's fixed function made the coordinate per VERTEX
		// (the camera-space reflection) and the card blended it across the triangle. Per pixel it hits the sphere
		// map's pole at grazing angles - white streaks fanning from a point on Tuscaran Glacier's floor that swung
		// with the camera (owner 2026-10-17)
		vec3 vp = (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
		vec3 vn = normalize((MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
		vec3 r = reflect(normalize(vp), vn);
		float sm = max(2.0 * sqrt(r.x * r.x + r.y * r.y + (r.z + 1.0) * (r.z + 1.0)), 1e-4);
		env_sm = vec2(r.x / sm + 0.5, 0.5 - r.y / sm);
	}
}

// a clamped layer (the NIF's CLAMP_S_CLAMP_T): its coordinates held half a texel - at the mip level drawn - inside
// the picture. The samplers repeat, and clamping to 0 / 1 alone let the filter blend in the opposite edge (owner
// 2026-10-11: the earth crack's plates took its hot rim glow's bright bottom row and looked like orange playdough)
vec2 pick(int i, bool wrap, vec2 size) {
	vec2 uv = i == 0 ? uv_a : (i == 1 ? uv_b : (i == 2 ? uv_c : uv_d));
	if (wrap) return uv;
	vec2 d = max(abs(dFdx(uv)), abs(dFdy(uv))) * size;
	vec2 inset = 0.5 * exp2(max(0.0, log2(max(max(d.x, d.y), 1e-6)))) / size;
	return clamp(uv, min(inset, vec2(0.5)), max(1.0 - inset, vec2(0.5)));
}

vec2 scr(vec3 s) {
	return s.z > 0.0 ? s.xy * fract(TIME / s.z) : vec2(0.0);
}

bool inside(int i) {
	vec2 uv = i == 0 ? uv_a : (i == 1 ? uv_b : (i == 2 ? uv_c : uv_d));
	return all(greaterThanEqual(uv, vec2(0.0))) && all(lessThanEqual(uv, vec2(1.0)));
}

void fragment() {
	vec4 c = has_base ? texture(base_tex, pick(base_uv, base_wrap, vec2(textureSize(base_tex, 0))) + scr(base_scroll) + base_offset) : vec4(1.0);
	if (blend2 && has_tex1 && has_tex2) {
		vec4 t1 = texture(tex1_tex, pick(tex1_uv, tex1_wrap, vec2(textureSize(tex1_tex, 0))));
		vec4 t2 = texture(tex2_tex, pick(tex2_uv, tex2_wrap, vec2(textureSize(tex2_tex, 0))));
		c = vec4(mix(t2.rgb, t1.rgb, COLOR.a), 1.0);
	}
	if (!split_tint) c.rgb *= tint;
	// dark and detail maps multiply, weighted by their own alpha: opaque light maps darken everywhere, while DAoC's
	// transparent overlays in these slots (climbing vines, lichen) only touch the surface where they're drawn
	if (has_dark) {
		vec4 d = texture(dark_tex, pick(dark_uv, dark_wrap, vec2(textureSize(dark_tex, 0))) + scr(dark_scroll) + dark_offset);
		if (dark_plain) c *= d; else c.rgb *= mix(vec3(1.0), d.rgb, d.a);
	}
	if (has_detail) {
		vec4 d = texture(detail_tex, pick(detail_uv, detail_wrap, vec2(textureSize(detail_tex, 0))) + scr(detail_scroll) + detail_offset);
		c.rgb *= mix(vec3(1.0), d.rgb * (detail_x2 ? 4.594 : 1.0), d.a);   // x2 in the client's gamma space = x2^2.2 in linear
	}
	if (has_decal && (decal_wrap || inside(decal_uv))) {
		vec4 d = texture(decal_tex, pick(decal_uv, decal_wrap, vec2(textureSize(decal_tex, 0))) + scr(decal_scroll) + decal_offset);
		c.rgb = mix(c.rgb, d.rgb, d.a);
	}
	if (use_vertex_color) c *= blend2 ? vec4(COLOR.rgb, 1.0) : COLOR;
	split_raw = c.rgb * light_scale;
	if (split_tint) c.rgb *= tint;
	ALBEDO = c.rgb * light_scale;
	vec4 g = has_glow ? texture(glow_tex, pick(glow_uv, glow_wrap, vec2(textureSize(glow_tex, 0))) + scr(glow_scroll) + glow_offset) : vec4(0.0);
	EMISSION = emissive * c.rgb + g.rgb * g.a;
	if (has_env) {
		// the client's sphere-mapped environment map (NiTextureEffect): the view reflection's sphere-map coordinate,
		// added over the surface (the glassy shields, potions, slime blobs - owner 2026-10-11: missing)
		vec3 env = texture(env_tex, env_sm).rgb;
		// a gloss map says how reflective each spot is (NetImmerse: the environment map scaled by the gloss map) -
		// the client multiplied in its gamma space, so the raw gloss bytes count squared-ish here in linear. Unscaled,
		// Tuscaran Glacier's ice (icymap over icesheetnoalpha) drowned its own blue sheet in a moving white glare
		// (owner 2026-10-17: "the old client is reflective too but its nowhere near what ours is")
		if (has_gloss)
			env *= pow(texture(gloss_tex, pick(gloss_uv, gloss_wrap, vec2(textureSize(gloss_tex, 0)))).rgb, vec3(2.2));
		EMISSION += env * env_strength;
	}
	ROUGHNESS = 0.9;
	SPECULAR = has_gloss ? texture(gloss_tex, pick(gloss_uv, gloss_wrap, vec2(textureSize(gloss_tex, 0)))).r * 0.8 : specular_amount;
#ifdef WORLD
	if (remaster_fx > 0.5) {
		EMISSION += ALBEDO * zone_fill;                  // (zero unless bounce light is on)
		float lum = dot(ALBEDO, vec3(0.3, 0.59, 0.11));
#ifdef FOLIAGE
		NORMAL = normalize(mix(NORMAL, fol_n, 0.85));
#else
		// relief: the texture's light parts raised, its dark seams sunk (a bump from the picture itself - the
		// surface gradient method, no tangents needed), then smoother and shinier where it is light
		if (relief_strength > 0.0 && has_base) {
			// the height's slope along the texture (two neighbouring texels at the mip drawn), carried onto the
			// screen by the texture coordinates' own slopes - smooth per pixel
			vec2 buv = pick(base_uv, base_wrap, vec2(textureSize(base_tex, 0))) + scr(base_scroll) + base_offset;
			float lod = max(textureQueryLod(base_tex, buv).x, 0.0) + 1.5;   // (a coarser mip: the shapes, not the grain)
			vec2 stp = exp2(lod) / vec2(textureSize(base_tex, 0));
			vec3 luma = vec3(0.3, 0.59, 0.11);
			float h0 = dot(textureLod(base_tex, buv, lod).rgb, luma);
			vec2 dh = vec2(dot(textureLod(base_tex, buv + vec2(stp.x, 0.0), lod).rgb, luma) - h0,
					dot(textureLod(base_tex, buv + vec2(0.0, stp.y), lod).rgb, luma) - h0) / stp;
			float dhdx = dot(dh, dFdx(buv));
			float dhdy = dot(dh, dFdy(buv));
			vec3 dpdx = dFdx(VERTEX);
			vec3 dpdy = dFdy(VERTEX);
			vec3 r1 = cross(dpdy, NORMAL);
			vec3 r2 = cross(NORMAL, dpdx);
			float det = dot(dpdx, r1);
			vec3 grad = sign(det) * (dhdx * r1 + dhdy * r2);
			NORMAL = normalize(abs(det) * NORMAL - grad * relief_strength);
		}
		ROUGHNESS = mix(0.92, 0.55, smoothstep(0.25, 0.85, lum) * shine_strength);
		SPECULAR = max(SPECULAR, specular_amount * (0.6 + 1.2 * lum * shine_strength));
#endif
	}
#endif
	//UNLIT_OUT
	//ALPHA_OUT
}
"""
