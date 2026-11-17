// The new trees' shared parts (TreeSwap): the sway - the higher up, the more it moves, each tree its own phase from
// where it stands, as strong as the weather's wind (the world's own wind_strength) - and the canopy light, as the
// original trees had it (NifMaterials FOLIAGE): the whole sun with a rounded shade, never black.
global uniform float wind_strength;
global uniform float foliage_light;
global uniform float remaster_fx;
vec3 tree_sway(vec3 v, vec3 at, float h, float t) {
	float k = clamp(v.y / max(h, 1.0), 0.0, 1.2);
	k *= k;
	float ph = dot(at.xz, vec2(0.031, 0.047));
	vec2 s = vec2(sin(t * 0.83 + ph) + 0.35 * sin(t * 1.9 + ph * 2.1), cos(t * 0.67 + ph * 1.3)) * 0.012 * h * k;
	return vec3(s.x, 0.0, s.y) * (0.4 + wind_strength);
}
float canopy_shade(vec3 n, vec3 l) {
	return mix(0.85, 0.45 + 0.8 * clamp((dot(n, l) + 0.4) / 1.4, 0.0, 1.0), max(foliage_light * remaster_fx, 0.6));
}
// a cut-out's alpha raised with the mip level (far leaves don't thin into sticks) and sharpened to the pixel
float cutout(float a, float lod, float cut) {
	a *= 1.0 + max(lod, 0.0) * 0.22;
	return clamp((a - cut) / max(fwidth(a), 0.0001) + 0.5, 0.0, 1.0);
}
