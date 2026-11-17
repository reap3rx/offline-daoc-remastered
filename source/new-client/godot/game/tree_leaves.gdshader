shader_type spatial;
// The new trees' leaf cards (TreeSwap): the original trees' own leaf pictures, cut out, lit as a rounded canopy (the
// cards' normals point out from the crown's centre), a little light through them, swaying with the wind.
render_mode cull_disabled, specular_disabled, depth_draw_opaque;
#include "res://game/tree_wind.gdshaderinc"
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform vec3 tint = vec3(1.0);
uniform float height = 25.0;
uniform float brightness = 1.75;
uniform float alpha_cut = 0.45;
uniform float translucency = 0.3;
varying float fade_t;
void vertex() {
	vec3 at = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	fade_t = tree_fade(at);
	VERTEX += tree_sway(VERTEX, at, height, TIME);
	VERTEX += NORMAL * 0.04 * sin(TIME * 3.7 + VERTEX.x * 1.3 + VERTEX.z * 1.7) * (0.3 + wind_strength);   // (flutter)
}
void fragment() {
	if (tree_dither(FRAGCOORD.xy) < fade_t) {
		discard;
	}
	vec4 c = texture(albedo_tex, UV);
	ALBEDO = c.rgb * tint * brightness * COLOR.rgb;    // (COLOR: the crown's own shade, deep leaves darker)
	ALPHA = cutout(c.a, textureQueryLod(albedo_tex, UV).x, alpha_cut);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 1.0;
	BACKLIGHT = ALBEDO * translucency;
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;          // (both sides of a card take the crown's light, not a flipped one)
	}
}
void light() {
	float sh = LIGHT_IS_DIRECTIONAL ? mix(0.75, 1.0, ATTENUATION) : ATTENUATION;
	DIFFUSE_LIGHT += sh * LIGHT_COLOR / PI * canopy_shade(NORMAL, LIGHT);
}
