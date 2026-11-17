shader_type spatial;
// The new trees far away (TreeSwap): one card that turns to face the camera and shows the variant photographed from
// the nearest of `views` directions round it (blending into the next as you walk round), unlit pictures lit here
// like the near tree: a rounded canopy facing you, the same sun and brightness - so the switch at NEAR_M is the
// same tree, not a different one. Atlas: a row per variant (INSTANCE_CUSTOM.x), the views across.
render_mode cull_disabled, specular_disabled, depth_draw_opaque;
#include "res://game/tree_wind.gdshaderinc"
uniform sampler2D atlas : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float views = 8.0;
uniform float rows = 6.0;
uniform float brightness = 1.45;       // (the near leaves' 1.75, less the near crown's own shadow: measured near vs far in game; the pictures are baked unlit, bark at 1.15 / 1.75)
uniform float alpha_cut = 0.32;
uniform float translucency = 0.3;
uniform float tone = 1.0;
uniform float sat = 1.0;
varying vec2 uv0;
varying vec2 uv1;
varying float blend;
varying vec3 right_w;
varying vec3 toward_w;
varying float fade_t;
void vertex() {
	fade_t = INSTANCE_CUSTOM.y;
	vec3 cam = (inverse(MODEL_MATRIX) * vec4(CAMERA_POSITION_WORLD, 1.0)).xyz;
	vec2 d = cam.xz;
	d = length(d) > 0.0001 ? normalize(d) : vec2(0.0, 1.0);
	float step_a = 6.28318530718 / views;
	float fk = mod(atan(d.x, d.y) / step_a, views);
	float k0 = floor(fk);
	blend = fk - k0;
	float k1 = mod(k0 + 1.0, views);
	vec3 right = vec3(d.y, 0.0, -d.x);
	VERTEX = right * VERTEX.x + vec3(0.0, VERTEX.y, 0.0);
	NORMAL = vec3(d.x, 0.0, d.y);
	float row = INSTANCE_CUSTOM.x;
	uv0 = vec2((k0 + UV.x) / views, (row + UV.y) / rows);
	uv1 = vec2((k1 + UV.x) / views, (row + UV.y) / rows);
	right_w = normalize((MODEL_MATRIX * vec4(right, 0.0)).xyz);
	toward_w = normalize((MODEL_MATRIX * vec4(d.x, 0.0, d.y, 0.0)).xyz);
	if (fade_t < 0.001) {
		VERTEX = vec3(0.0);       // (wholly the near tree: nothing to draw)
	}
}
void fragment() {
	if (tree_dither(FRAGCOORD.xy) >= fade_t) {
		discard;
	}
	// one picture or the other, never both mixed (a mix shows the other view's trunk and branches as a pale ghost):
	// between two views the pixels go to the nearer view in proportion, by a dither that doesn't move
	float pick = fract(tree_dither(FRAGCOORD.xy) + 0.37);
	vec2 uv = pick < blend ? uv1 : uv0;
	vec4 c = textureGrad(atlas, uv, dFdx(uv0), dFdy(uv0));     // (the two views' places differ by a constant: one mip)
	ALBEDO = c.rgb * brightness * tone;
	ALBEDO = mix(vec3(dot(ALBEDO, vec3(0.299, 0.587, 0.114))), ALBEDO, sat);
	ALPHA = cutout(c.a, textureQueryLod(atlas, uv0).x, alpha_cut);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 1.0;
	BACKLIGHT = ALBEDO * translucency;
	// the canopy as a ball facing you (the near leaves' normals point out from the crown's centre the same way)
	float sx = (UV.x - 0.5) * 2.0;
	float sy = clamp(((1.0 - UV.y) - 0.62) / 0.38, -1.0, 1.0);
	vec3 nw = normalize(right_w * sx + vec3(0.0, 1.0, 0.0) * (sy * 0.8 + 0.25) + toward_w * sqrt(max(0.08, 1.0 - sx * sx - sy * sy * 0.64)));
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
}
void light() {
	float sh = LIGHT_IS_DIRECTIONAL ? mix(0.75, 1.0, ATTENUATION) : ATTENUATION;
	DIFFUSE_LIGHT += sh * LIGHT_COLOR / PI * canopy_shade(NORMAL, LIGHT);
}
