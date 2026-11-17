shader_type spatial;
// The new trees far away (TreeSwap): two crossed pictures of the variant (front and side, both in one row per
// species: variant v's front at column 2v, its side at 2v + 1), lit as a rounded canopy.
render_mode cull_disabled, specular_disabled, depth_draw_opaque;
#include "res://game/tree_wind.gdshaderinc"
uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform float count = 6.0;
uniform float brightness = 2.1;    // (the far pictures were taken in soft light)
uniform float alpha_cut = 0.4;
varying vec2 auv;
void vertex() {
	auv = vec2((INSTANCE_CUSTOM.x * 2.0 + UV2.x + UV.x) / (count * 2.0), UV.y);
	NORMAL = normalize(NORMAL * 0.35 + vec3(0.0, 0.75, 0.0));
}
void fragment() {
	vec4 c = texture(atlas, auv);
	ALBEDO = c.rgb * brightness;
	ALPHA = cutout(c.a, textureQueryLod(atlas, auv).x, alpha_cut);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 1.0;
	BACKLIGHT = ALBEDO * 0.25;
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
}
void light() {
	DIFFUSE_LIGHT += (LIGHT_IS_DIRECTIONAL ? 1.0 : ATTENUATION) * LIGHT_COLOR / PI * canopy_shade(NORMAL, LIGHT);
}
