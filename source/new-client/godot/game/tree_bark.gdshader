shader_type spatial;
// The new trees' trunks and branches (TreeSwap): the original trees' bark, swaying with their leaves.
render_mode specular_disabled;
#include "res://game/tree_wind.gdshaderinc"
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float height = 25.0;
uniform float brightness = 1.15;
uniform vec2 uv_scale = vec2(1.0, 1.0);
uniform float tone = 1.0;
uniform float sat = 1.0;
global uniform vec3 tree_eye;          // (the camera, set by Foliage each frame: the same in the shadow pass)
uniform float fade_start = 0.0;
uniform float fade_end = 0.0;
varying float fade_t;
void vertex() {
	vec3 at = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	// trees: their hand-over (TreeSwap.Driver, per instance); bushes (Foliage): by distance, dissolving out at its reach
	fade_t = fade_end > 0.0 ? smoothstep(fade_start, fade_end, distance(at, tree_eye)) : INSTANCE_CUSTOM.y;
	VERTEX += tree_sway(VERTEX, at, height, TIME);
	if (fade_t > 0.999) {
		VERTEX = vec3(0.0);       // (wholly the far card: nothing to draw)
	}
}
void fragment() {
	if (tree_dither(FRAGCOORD.xy) < fade_t) {
		discard;
	}
	ALBEDO = texture(albedo_tex, UV * uv_scale).rgb * brightness * tone;
	ALBEDO = mix(vec3(dot(ALBEDO, vec3(0.299, 0.587, 0.114))), ALBEDO, sat);
	ROUGHNESS = 1.0;
}
