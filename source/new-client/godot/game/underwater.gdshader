shader_type spatial;
render_mode unshaded, depth_test_disabled, depth_draw_never, cull_disabled, blend_mix, fog_disabled, shadows_disabled;
// Under the water (owner 2026-10-31, remastered): a screen-filling veil in front of the camera, the murk thickening
// with distance - a few metres of clear water, then nothing but its colour. SkySystem shows it while the camera is
// below the surface of the water it stands in.

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform vec3 murk_color : source_color = vec3(0.05, 0.11, 0.11);
uniform float visibility_m = 14.0;
uniform float surface_y = 0.0;           // the water's surface: looking up, the murk stops there (its underside)        // the distance at which two thirds of the view is murk

void vertex() {
	POSITION = vec4(VERTEX.xy * 2.0, 0.5, 1.0);
}

void fragment() {
	float d = texture(depth_tex, SCREEN_UV).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	v.xyz /= v.w;
	float dist = d <= 0.0 ? 1e6 : length(v.xyz);
	vec3 wdir = normalize((INV_VIEW_MATRIX * vec4(v.xyz, 0.0)).xyz);
	float above = surface_y - INV_VIEW_MATRIX[3].y;
	if (wdir.y > 0.01) {
		dist = min(dist, above / wdir.y);
	}
	float f = 1.0 - exp(-dist / visibility_m);
	// brighter looking up toward the lit surface, darker down into the deep
	ALBEDO = murk_color * (0.55 + 1.4 * smoothstep(-0.4, 0.9, wdir.y));
	ALPHA = clamp(0.15 + 0.85 * f, 0.0, 1.0);
}
