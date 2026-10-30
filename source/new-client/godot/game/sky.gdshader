shader_type sky;
render_mode use_half_res_pass;
// DAoC sky dome, drawn from the client's sky_*.dat values (zones/sky/sky.mpk, exported by pipeline/build_sky.py).
// Colours arrive already blended for the time of day and storm level (game/sky_system.gd):
//   canopy rings: zenith, east1..4 / west1..4 from overhead down to the horizon, nadir below; east/west blend by
//   which side of the sky the sun's path is on. Two cloud layers (top, bottom) scroll at the file's tile and speed
//   and are tinted by the cloud colour rings (alpha = cloud cover per ring). Sun disk + glow + flare, moon over its
//   dark backing disk, and stars, using the client's textures.

uniform vec4 canopy_zenith : source_color;
uniform vec4 canopy_east[4];
uniform vec4 canopy_west[4];
uniform vec4 canopy_nadir : source_color;
uniform vec4 cloud_zenith : source_color;
uniform vec4 cloud_east[4];
uniform vec4 cloud_west[4];

uniform sampler2D cloud_top : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D cloud_bot : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D cloud_top2 : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D cloud_bot2 : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 cloud_tiles = vec4(4.0, 5.0, 4.0, 3.0);      // top, bot, top2, bot2
uniform vec4 cloud_speeds = vec4(4.0, 6.0, 5.0, 9.0);     // client values; the client multiplies by 0.001
uniform float storm = 0.0;                                // 0 clear .. 1 full storm: blends to the *2 cloud layers
uniform float cloud_time = 0.0;

uniform sampler2D sun_disk_tex : source_color, filter_linear, repeat_disable;
uniform sampler2D sun_glow_tex : source_color, filter_linear, repeat_disable;
uniform sampler2D sun_flare_tex : source_color, filter_linear, repeat_disable;
uniform sampler2D moon_tex : source_color, filter_linear, repeat_disable;
uniform sampler2D moonback_tex : source_color, filter_linear, repeat_disable;
uniform sampler2D star_tex : source_color, filter_linear, repeat_disable;
uniform vec3 sun_dir = vec3(0.0, 1.0, 0.0);
uniform vec3 moon_dir = vec3(0.0, -1.0, 0.0);
uniform vec4 sun_disk_color : source_color;
uniform vec4 sun_glow_color : source_color;
uniform vec4 sun_flare_color : source_color;
uniform vec4 moon_color : source_color;
uniform vec4 moonback_color : source_color;
uniform vec3 sizes = vec3(15.0, 175.0, 175.0);           // sun disk, glow, flare scale (at distance 1000)
uniform float moon_size = 15.0;
uniform float star_scale = 2.5;
uniform float star_density = 700.0;
uniform float star_visibility = 0.0;

// Remastered clouds (claude 2026-10-30): a slab of cloud 1.2-2.6 km up, ray-marched at half resolution, sunlit from
// above (light marched toward the sun or moon), thicker, lower-lying and darker as a storm builds; lightning lights
// it from inside. The classic two layers stay for reflections and the classic look.
uniform float remaster_clouds = 0.0;
uniform float cloud_cover = 0.4;          // 0 clear .. 1 overcast
uniform float cloud_storm = 0.0;          // darker, denser bellies
uniform vec3 cloud_sun = vec3(1.0);        // the sun's (or moon's) light on the cloud tops
uniform vec3 cloud_light_dir = vec3(0.0, 1.0, 0.0);
uniform vec3 cloud_amb = vec3(0.6, 0.65, 0.75);   // the sky's light on their shaded sides
uniform vec2 cloud_wind = vec2(1.0, 0.35);
uniform float cloud_clock = 0.0;
uniform float flash = 0.0;                 // lightning
uniform float cloud_full = 0.0;            // tests: the clouds in the full resolution pass instead
uniform float cloud_jitter = 1.0;          // tests: 0 = no per-pixel start offset

// per-pixel start offset for the march (interleaved gradient noise): hides the steps' banding
float ign(vec2 uv) {
	vec2 px = floor(uv * vec2(1920.0, 1080.0));
	return mix(0.5, fract(52.9829189 * fract(dot(px, vec2(0.06711056, 0.00583715)) + fract(TIME * 7.13))), cloud_jitter);
}

vec4 ring_color(vec4 zenith, vec4 east[4], vec4 west[4], vec3 dir) {
	// elevation 90 -> 0 degrees spans zenith, ring1 .. ring4; east/west by the side of the sky
	float elev = degrees(asin(clamp(dir.y, -1.0, 1.0)));
	float t = clamp((90.0 - elev) / 22.5, 0.0, 4.0);     // 0 zenith, 1..4 rings
	float side = clamp(dir.x * 0.5 + 0.5, 0.0, 1.0);     // +x is east
	vec4 e = zenith;
	vec4 w = zenith;
	int i = int(floor(t));
	float f = fract(t);
	vec4 e0 = i == 0 ? zenith : east[max(i - 1, 0)];
	vec4 w0 = i == 0 ? zenith : west[max(i - 1, 0)];
	vec4 e1 = east[min(i, 3)];
	vec4 w1 = west[min(i, 3)];
	if (t >= 4.0) {
		e0 = east[3]; e1 = east[3]; w0 = west[3]; w1 = west[3];
	}
	e = mix(e0, e1, f);
	w = mix(w0, w1, f);
	return mix(w, e, side);
}

vec4 sprite(sampler2D tex, vec3 dir, vec3 center, float size) {
	// a camera-facing billboard on the sky sphere, size in the client's units at distance 1000
	vec3 c = normalize(center);
	float d = dot(dir, c);
	if (d <= 0.0) return vec4(0.0);
	vec3 up = abs(c.y) > 0.99 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
	vec3 right = normalize(cross(up, c));
	vec3 up2 = cross(c, right);
	vec3 p = dir / d - c;                                // point on the plane tangent to the sky at the centre
	vec2 uv = vec2(dot(p, right), dot(p, up2)) * (1000.0 / size) * 0.5 + 0.5;
	if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) return vec4(0.0);
	return texture(tex, uv);
}

float hash(vec3 p) {
	return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
}

float h21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vn2(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y);
}

float fbm2(vec2 p) {
	float s = 0.0;
	float a = 0.5;
	for (int i = 0; i < 5; i++) {
		s += a * vn2(p);
		p = p * 2.03 + vec2(17.1, 9.2);
		a *= 0.5;
	}
	return s / 0.97;
}

float h31(vec3 p) {
	p = fract(p * 0.3183099 + 0.1) * 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float vn3(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = mix(mix(h31(i), h31(i + vec3(1.0, 0.0, 0.0)), f.x), mix(h31(i + vec3(0.0, 1.0, 0.0)), h31(i + vec3(1.0, 1.0, 0.0)), f.x), f.y);
	float b = mix(mix(h31(i + vec3(0.0, 0.0, 1.0)), h31(i + vec3(1.0, 0.0, 1.0)), f.x), mix(h31(i + vec3(0.0, 1.0, 1.0)), h31(i + vec3(1.0, 1.0, 1.0)), f.x), f.y);
	return mix(a, b, f.z);
}

const float CLOUD_LO = 1200.0;
const float CLOUD_HI = 2600.0;

// cloud density at a point (metres from the eye): a weather map of billows (2D) shaped by height, eroded by 3D detail
float cloud_density(vec3 p, bool detail) {
	float ht = (p.y - CLOUD_LO) / (CLOUD_HI - CLOUD_LO);
	if (ht < 0.0 || ht > 1.0) return 0.0;
	vec2 q = p.xz * 0.00032 + cloud_wind * cloud_clock * 0.004 + vec2(37.37, 91.71);
	float base = fbm2(q);
	float thr = mix(0.66, 0.30, cloud_cover);
	float shape = smoothstep(thr, thr + 0.22, base);
	// flat bellies, rounded tops; storm clouds reach higher
	float top = mix(0.55, 0.95, cloud_storm);
	float profile = smoothstep(0.0, 0.12, ht) * (1.0 - smoothstep(top * shape, top * shape + 0.25, ht));
	float d = shape * profile;
	if (d <= 0.0 || !detail) return d;
	float det = vn3(p * 0.0035 + vec3(cloud_wind.x, 0.1, cloud_wind.y) * cloud_clock * 0.02 + vec3(13.7, 5.3, 29.1));
	det = det * 0.65 + vn3(p * 0.011 + vec3(71.3, 3.9, 47.7)) * 0.35;
	return clamp(d - (1.0 - det) * 0.45 * (1.0 - d * 0.6), 0.0, 1.0);
}

// the cloud layer seen along dir: premultiplied colour and coverage
vec4 clouds(vec3 dir, float jitter) {
	if (dir.y < 0.01) return vec4(0.0);
	float t0 = CLOUD_LO / dir.y;
	float t1 = min(CLOUD_HI / dir.y, t0 + 7000.0);
	const int STEPS = 24;
	float dt = (t1 - t0) / float(STEPS);
	vec3 L = normalize(cloud_light_dir);
	float mu = dot(dir, L);
	float phase = 0.6 + 0.9 * pow(max(mu, 0.0), 6.0);         // brighter toward the sun (forward scattering)
	float sigma = mix(0.010, 0.022, cloud_storm);
	float tr = 1.0;
	vec3 acc = vec3(0.0);
	for (int i = 0; i < STEPS; i++) {
		vec3 p = dir * (t0 + (float(i) + jitter) * dt);
		float d = cloud_density(p, true);
		if (d < 0.01) continue;
		// light reaching this point: two samples toward the light
		float ld = cloud_density(p + L * 180.0, false) + cloud_density(p + L * 520.0, false) * 1.4;
		float sun_t = exp(-ld * mix(2.2, 3.5, cloud_storm));
		float ht = (p.y - CLOUD_LO) / (CLOUD_HI - CLOUD_LO);
		vec3 lit = cloud_sun * sun_t * phase + cloud_amb * (0.45 + 0.55 * ht);
		lit *= 1.0 - 0.55 * cloud_storm * (1.0 - ht);              // dark storm bellies
		lit += vec3(0.75, 0.8, 1.0) * flash * (0.4 + d);
		float a = 1.0 - exp(-sigma * d * dt);
		acc += tr * a * lit;
		tr *= 1.0 - a;
		if (tr < 0.02) break;
	}
	float fade = smoothstep(0.01, 0.09, dir.y);                  // into the haze at the horizon
	return vec4(acc * fade, (1.0 - tr) * fade);
}

void sky() {
	vec3 dir = EYEDIR;
	if (AT_HALF_RES_PASS) {
		if (remaster_clouds > 0.5 && cloud_full < 0.5) {
			vec4 c = clouds(dir, ign(SCREEN_UV));
			COLOR = c.rgb;
			ALPHA = c.a;
		} else {
			COLOR = vec3(0.0);
			ALPHA = 0.0;
		}
	} else {                                             // (the full pass: no 'return' in a sky shader)
	vec3 col;
	if (dir.y >= 0.0) {
		col = ring_color(canopy_zenith, canopy_east, canopy_west, dir).rgb;
	} else {
		col = mix(canopy_east[3].rgb * 0.5 + canopy_west[3].rgb * 0.5, canopy_nadir.rgb, clamp(-dir.y * 3.0, 0.0, 1.0));
	}

	// stars, faded in at night under clear skies
	if (star_visibility > 0.001 && dir.y > 0.0) {
		// grid sized so the expected star count matches the file's max_stars: a unit sphere through a grid of
		// `cells` per unit crosses about 2*pi*1.5*cells^2 cells on the visible half, and half of them hold a star
		// (the first version used sqrt(max_stars)*2 and showed ~12x too many, owner 2026-10-09)
		float cells = sqrt(star_density / 4.7);
		vec3 g = floor(dir * cells);
		float h = hash(g);
		if (h > 0.5) {
			vec3 star = normalize((g + vec3(hash(g + 1.3), hash(g + 2.7), hash(g + 5.1))) / cells);
			vec4 s = sprite(star_tex, dir, star, star_scale);
			col += s.rgb * s.a * star_visibility * (0.5 + h * 0.5);
		}
	}

	// moon over its dark backing disk
	vec4 mb = sprite(moonback_tex, dir, moon_dir, moon_size);
	col = mix(col, moonback_color.rgb * mb.rgb, mb.a * moonback_color.a * star_visibility);
	vec4 mn = sprite(moon_tex, dir, moon_dir, moon_size);
	col += mn.rgb * moon_color.rgb * mn.a * moon_color.a * max(star_visibility, 0.15);

	// sun glow, flare and disk (additive, alpha = strength from the file)
	vec4 gl = sprite(sun_glow_tex, dir, sun_dir, sizes.y);
	col += gl.rgb * sun_glow_color.rgb * gl.a * sun_glow_color.a;
	vec4 fl = sprite(sun_flare_tex, dir, sun_dir, sizes.z);
	col += fl.rgb * sun_flare_color.rgb * fl.a * sun_flare_color.a;
	vec4 sd = sprite(sun_disk_tex, dir, sun_dir, sizes.x);
	col += sd.rgb * sun_disk_color.rgb * sd.a * sun_disk_color.a;

	// clouds: two layers projected on a flat ceiling, tinted and faded by the cloud colour rings (remastered: the
	// ray-marched clouds from the half resolution pass, over everything but the reflections' cube map)
	bool new_clouds = remaster_clouds > 0.5 && !AT_CUBEMAP_PASS;
	if (new_clouds) {
		vec4 hc = HALF_RES_COLOR;
		if (cloud_full > 0.5) {
			hc = clouds(dir, ign(SCREEN_UV));
		}
		col = col * (1.0 - hc.a) + hc.rgb;
		col += vec3(0.45, 0.5, 0.65) * flash * 0.25 * max(dir.y, 0.0);
	}
	if (dir.y > 0.0 && !new_clouds) {
		vec2 base = dir.xz / (dir.y + 0.12);
		vec4 cc = ring_color(cloud_zenith, cloud_east, cloud_west, dir);
		float t = cloud_time * 0.001;
		vec4 top = mix(texture(cloud_top, base / cloud_tiles.x * 0.5 + vec2(t * cloud_speeds.x, 0.0)),
				texture(cloud_top2, base / cloud_tiles.z * 0.5 + vec2(t * cloud_speeds.z, 0.0)), storm);
		vec4 bot = mix(texture(cloud_bot, base / cloud_tiles.y * 0.5 + vec2(t * cloud_speeds.y, t * cloud_speeds.y * 0.3)),
				texture(cloud_bot2, base / cloud_tiles.w * 0.5 + vec2(t * cloud_speeds.w, t * cloud_speeds.w * 0.3)), storm);
		float a_top = dot(top.rgb, vec3(0.333)) * top.a * cc.a;
		float a_bot = dot(bot.rgb, vec3(0.333)) * bot.a * cc.a;
		col = mix(col, cc.rgb * top.rgb * 1.2, clamp(a_top, 0.0, 1.0));
		col = mix(col, cc.rgb * bot.rgb * 1.2, clamp(a_bot, 0.0, 1.0));
	}
	COLOR = col;
}
}
