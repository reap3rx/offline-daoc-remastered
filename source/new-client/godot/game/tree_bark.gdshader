shader_type spatial;
// The new trees' trunks and branches (TreeSwap): the original trees' bark, swaying with their leaves.
render_mode specular_disabled;
#include "res://game/tree_wind.gdshaderinc"
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float height = 25.0;
uniform float brightness = 1.15;
uniform vec2 uv_scale = vec2(1.0, 1.0);
void vertex() {
	vec3 at = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	VERTEX += tree_sway(VERTEX, at, height, TIME);
}
void fragment() {
	ALBEDO = texture(albedo_tex, UV * uv_scale).rgb * brightness;
	ROUGHNESS = 1.0;
}
