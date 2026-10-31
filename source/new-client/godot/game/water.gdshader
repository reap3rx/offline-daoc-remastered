shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;
// Zone water from the client's own pieces only (owner rule 2026-10-09: bring assets over, don't replace them):
//   - the zone's water texture (sector.dat [riverNN] texture=watery.tga), scrolling at the river's flow value
//   - the client's environment-bump map app/water/bump3.tga (du/dv in RG) offsetting the lookups, as the client's
//     bump stage does: this is the fine moving ripple in the client
//   - a sky cloud layer (zones/sky) as the reflected environment, no trees or shore
//   - plain alpha blending, so the bottom shows through in the shallows
// Still to confirm against the client (listed in WORLD IMPORT LESSONS.md): exact env texture, blend amounts, alpha.

uniform sampler2D water_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D bump_tex : filter_linear_mipmap, repeat_enable;          // du/dv in RG, 0.5 = no offset
uniform sampler2D env_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform float water_repeat_m = 12.0;
uniform float bump_repeat_m = 6.0;
uniform float bump_scale = 0.06;         // how far the du/dv map pushes the lookups
uniform float env_amount = 0.45;
uniform float opacity = 0.78;
uniform vec2 drift = vec2(0.010, 0.004); // repeats per second, from the zone's flow value
uniform vec3 sky_color : source_color = vec3(0.55, 0.68, 0.78);
uniform vec3 sun_dir = vec3(0.4, 0.7, 0.5);              // kept for the loader; unused
uniform vec3 sun_color : source_color = vec3(1.0, 0.95, 0.86);
uniform bool use_color = false;          // the Shrouded Isles' textureless water: sector.dat base_color
uniform vec3 base_color : source_color = vec3(0.333, 0.314, 0.251);
// The textureless water's depth (owner 2026-10-15: Modernagrav's sea "completely clear ... you can see the bottom",
// the client's is dark grey): the base colour's own 0.35 alpha over the shallows, darker and closer to opaque as the
// water behind the surface gets deeper - the scene's depth under it, so it follows the real sea bed.
uniform bool depth_fade = false;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform float deep_m = 4.0;              // this much water behind the surface: fully deep
uniform float deep_opacity = 0.92;
uniform float deep_dark = 0.5;           // the deep colour: base_color times this

// The remastered water (owner 2026-10-31, remaster_fx on; the classic water above stays as it was): the sky and the
// shore mirrored in it (screen-space: what is on screen, the sky's colours where the ray leaves it), more of it the
// flatter you look (Fresnel), the bottom seen through it bent by the ripples and lost with depth, foam where it
// meets the shore, rings where the rain lands, the sun's glint. Looked at from below: the murk.
global uniform float remaster_fx;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform vec3 sky_top : source_color = vec3(0.35, 0.5, 0.7);
uniform float rain = 0.0;                // how hard it rains: the rings
uniform float lit = 1.0;                 // day 1 .. night: the water's own colour and the foam dim with it
uniform float storm = 0.0;
uniform vec3 murk_color : source_color = vec3(0.05, 0.11, 0.11);
uniform float clarity_m = 2.2;           // the bottom fades out over about this much water
uniform float foam_m = 0.7;              // foam this deep at the shore
uniform float wave = 1.0;
uniform float reflect_amount = 1.0;

varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

vec2 hash22(vec2 q) {
	vec3 a = fract(vec3(q.xyx) * vec3(0.1031, 0.1030, 0.0973));
	a += dot(a, a.yzx + 33.33);
	return fract((a.xx + a.yz) * a.zy);
}

// Rain rings: drops land in cells of the surface, each ring spreading and fading; more cells live the harder it rains.
vec2 rain_rings(vec2 p, float t, float amount) {
	vec2 acc = vec2(0.0);
	for (int layer = 0; layer < 3; layer++) {
		vec2 q = p * 2.2 + vec2(float(layer) * 0.37, float(layer) * 0.71);
		vec2 cell = floor(q);
		vec2 h = hash22(cell + float(layer) * 17.13);
		if (h.y > amount) {
			continue;
		}
		vec2 c = cell + 0.3 + 0.4 * h;
		float ph = fract(t * (0.9 + 0.3 * h.y) + h.x * 7.31);
		vec2 dv = q - c;
		float d = length(dv) + 1e-4;
		float x = d - ph * 0.42;
		float w = sin(x * 55.0) * exp(-x * x * 900.0) * (1.0 - ph) * (1.0 - ph);
		acc += dv / d * w;
	}
	return acc;
}

vec3 remaster(vec3 surface, vec2 p, float t, vec2 dudv, vec2 screen_uv, vec3 vtx, mat4 view, mat4 proj, mat4 inv_proj,
		vec3 cam, vec3 to_eye, bool front) {
	// the surface's slope: the client's du/dv ripple twice, crossing, and the rain's rings
	vec2 d2 = texture(bump_tex, p / (bump_repeat_m * 2.7) - drift.yx * t * 2.5 + vec2(0.37, 0.11)).rg * 2.0 - 1.0;
	vec2 slope = (dudv + d2 * 0.7) * 0.07 * wave * (1.0 + storm);
	slope += rain_rings(p, t, rain) * 0.35 * clamp(rain * 2.0, 0.0, 1.0);
	vec3 n = normalize(vec3(-slope.x, 1.0, -slope.y));
	float dist_eye = length(vtx);
	// the water behind the surface: the scene's depth here, as a vertical depth below the surface
	float d0 = texture(depth_tex, screen_uv).r;
	vec4 bed = inv_proj * vec4(screen_uv * 2.0 - 1.0, d0, 1.0);
	bed.xyz /= bed.w;
	float behind = max(distance(bed.xyz, vtx), 0.0);
	float deep = behind * max(abs(to_eye.y), 0.08);
	if (!front) {
		// from below: the world above only through the window straight overhead (Snell's window, ~49 degrees); past
		// it the surface mirrors the murk back down
		vec3 above = texture(screen_tex, screen_uv + slope * 0.08).rgb;
		float window = smoothstep(0.6, 0.75, abs(to_eye.y));
		return mix(murk_color * lit * 1.6, mix(above, murk_color * lit, 0.3), window);
	}
	// the bottom, bent by the ripples (not where the bent look lands on something in front of the water)
	vec2 bent = screen_uv + slope * 0.06 * clamp(deep, 0.0, 1.0);
	float db = texture(depth_tex, bent).r;
	vec4 bb = inv_proj * vec4(bent * 2.0 - 1.0, db, 1.0);
	bb.xyz /= bb.w;
	if (bb.z > vtx.z) {
		bent = screen_uv;
	}
	vec3 bottom = texture(screen_tex, bent).rgb;
	float max_tint = depth_fade ? deep_opacity : opacity;
	vec3 body = depth_fade ? mix(surface, surface * deep_dark, smoothstep(0.0, deep_m, deep)) : surface;
	float absorb = mix(0.12, max_tint, 1.0 - exp(-deep / clarity_m));
	vec3 col = mix(bottom, body * lit, absorb);
	// the reflection: the sky's colours (the cloud layer over them), or what's on screen where the mirrored ray meets it
	vec3 r = reflect(-to_eye, n);
	r.y = max(r.y, 0.02);
	vec3 sky = mix(sky_color, sky_top, sqrt(clamp(r.y, 0.0, 1.0)));
	vec2 env_uv = r.xz / (r.y + 0.25) * 0.35 + vec2(t * 0.003, 0.0);
	vec3 env = texture(env_tex, env_uv).rgb;
	sky = mix(sky, sky * env * 1.6, 0.35 + 0.4 * storm);
	vec3 refl = sky;
	if (dist_eye < 400.0) {
		vec3 wp = cam - to_eye * dist_eye;
		float prev = 0.0;
		float hit = 0.0;
		vec2 huv = vec2(0.0);
		for (int i = 1; i <= 20; i++) {
			float s = 0.6 * pow(1.3, float(i));
			vec3 vp = (view * vec4(wp + r * s, 1.0)).xyz;
			vec4 cp = proj * vec4(vp, 1.0);
			if (cp.w <= 0.0) {
				break;
			}
			vec2 uv = cp.xy / cp.w * 0.5 + 0.5;
			if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
				break;
			}
			float sd = texture(depth_tex, uv).r;
			vec4 sv = inv_proj * vec4(uv * 2.0 - 1.0, sd, 1.0);
			sv.xyz /= sv.w;
			if (vp.z < sv.z && sv.z - vp.z < s * 0.4 + 1.0) {
				// a few halvings between the last miss and this hit
				float a = prev;
				float b = s;
				for (int k = 0; k < 4; k++) {
					float m = (a + b) * 0.5;
					vec3 vm = (view * vec4(wp + r * m, 1.0)).xyz;
					vec4 cm = proj * vec4(vm, 1.0);
					vec2 um = cm.xy / cm.w * 0.5 + 0.5;
					vec4 sm = inv_proj * vec4(um * 2.0 - 1.0, texture(depth_tex, um).r, 1.0);
					sm.xyz /= sm.w;
					if (vm.z < sm.z) {
						b = m;
						uv = um;
					} else {
						a = m;
					}
				}
				vec2 edge = min(uv, 1.0 - uv);
				hit = smoothstep(0.0, 0.08, min(edge.x, edge.y)) * (1.0 - smoothstep(250.0, 400.0, dist_eye));
				huv = uv;
				break;
			}
			prev = s;
		}
		if (hit > 0.0) {
			refl = mix(refl, texture(screen_tex, huv).rgb, hit);
		}
	}
	float cosv = clamp(dot(n, to_eye), 0.0, 1.0);
	float fres = 0.02 + 0.98 * pow(1.0 - cosv, 5.0);
	fres = clamp(mix(0.1, 1.0, fres) * reflect_amount, 0.0, 1.0);
	col = mix(col, refl, fres);
	// the sun's (the moon's) glint, broken up in the rain
	float g = pow(max(dot(r, normalize(sun_dir)), 0.0), 350.0) * (1.0 - storm) * (1.0 - 0.7 * rain);
	col += sun_color * g * 3.0 * smoothstep(0.0, 0.1, sun_dir.y);
	// foam along the shore, lapping, broken up by the ripple map
	float fn = texture(bump_tex, p / 1.7 + vec2(t * 0.02, -t * 0.013)).r * texture(bump_tex, p / 0.83 - vec2(t * 0.015, t * 0.01)).g * 2.0;
	float fw = foam_m * (0.7 + 0.3 * sin(t * 1.1 + fn * 5.0));
	float band = 1.0 - smoothstep(0.0, fw, deep);
	float foam = band * smoothstep(0.5, 0.8, fn + 0.3 * band);
	foam *= 1.0 - smoothstep(120.0, 220.0, dist_eye);
	col = mix(col, vec3(0.82, 0.86, 0.86) * mix(sky_color * 1.2, vec3(1.0), 0.5) * lit, foam * 0.6);
	// the very edge: no hard line where the surface meets the ground
	col = mix(bottom, col, smoothstep(0.0, 0.12, deep));
	return col;
}

void fragment() {
	float t = TIME;
	vec2 p = world_pos.xz;
	vec2 dudv = texture(bump_tex, p / bump_repeat_m + drift * t * 4.0).rg * 2.0 - 1.0;
	vec3 surface = use_color ? base_color : texture(water_tex, p / water_repeat_m + drift * t + dudv * bump_scale).rgb;
	vec3 cam = (INV_VIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 to_eye = normalize(cam - world_pos);
	vec3 r = reflect(-to_eye, vec3(0.0, 1.0, 0.0));
	vec2 env_uv = r.xz / (abs(r.y) + 0.25) * 0.35 + dudv * bump_scale + vec2(t * 0.003, 0.0);
	if (remaster_fx > 0.5) {
		ALBEDO = remaster(surface, p, t, dudv, SCREEN_UV, VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, INV_PROJECTION_MATRIX,
				cam, to_eye, cam.y > world_pos.y);
		ALPHA = 1.0;
	} else {
	vec3 env = texture(env_tex, env_uv).rgb * sky_color * 1.6;
	float alpha = opacity;
	if (depth_fade) {
		float d = texture(depth_tex, SCREEN_UV).r;
		vec4 bed = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
		bed.xyz /= bed.w;
		float k = smoothstep(0.0, 1.0, clamp(distance(bed.xyz, VERTEX) / deep_m, 0.0, 1.0));
		surface = mix(surface, surface * deep_dark, k);
		alpha = mix(opacity, deep_opacity, k);
	}
	ALBEDO = mix(surface, env, env_amount);
	ALPHA = alpha;
	}
}
