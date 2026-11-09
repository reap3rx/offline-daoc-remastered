extends RefCounted
## The client's animations, played more like a modern game's (claude 2026-11-09; owner: "DAoC's animations, while I
## love the style, are just too stiff ... keep the overall style but somehow modernize the feel"). Every pose stays
## the client's; what changes is the motion between them:
##   - curves between the keys (the client's keys come 15 a second, joined with straight lines: a bone's speed changes
##     in a step at every key - the robotic look)
##   - overlap: the parts further out on a limb follow a moment later (the forearm after the upper arm, the hand after
##     the forearm, the head after the neck, a ponytail after the head), so a swing whips through instead of the whole
##     arm moving as one rod
##   - a steadier head while running and walking (the head holds its gaze while the body bobs under it)
## Clips go by group (GROUPS, group_of), each with its own settings. The swings, the styles and the casts' start and
## end are left as they are for now: their hit / release lands on the client's own frame (the server's timing), so
## they get their own settings - with that frame kept where it is - when we come to combat (owner 2026-11-09).
## Fig3Figure.load_figure builds each race's clips through here once (cached per race); tests/clip_compare shows a
## clip as it was and as it is now, side by side.

static var enabled := true                   # (clip_compare builds both ways)

## Per group: overlap (x the delays in DELAY), head_steady (0..1, how much of the head's bob in the world is taken out),
## wrap (the clip loops: the delayed parts come round from its end).
const GROUPS := {
	"move": {"overlap": 1.0, "head_steady": 0.45},
	"idle": {"overlap": 0.7, "head_steady": 0.0},
	"aim": {"overlap": 0.0, "head_steady": 0.0},       # bow / throw / crossbow aim, the casting hold: curves only
	"emote": {"overlap": 0.7, "head_steady": 0.0},
	# reserved for combat (not yet used): "swing", "cast" - with their hit / release frames kept
}

## How far behind each bone follows (seconds, at overlap 1) - more the further out on the limb.
const DELAY := {
	"Bip01 Neck": 0.025, "Bip01 Head": 0.05,
	"Bip01 L Clavicle": 0.02, "Bip01 R Clavicle": 0.02,
	"Bip01 L UpperArm": 0.045, "Bip01 R UpperArm": 0.045,
	"Bip01 L Forearm": 0.09, "Bip01 R Forearm": 0.09,
	"Bip01 L ForeTwist": 0.09, "Bip01 R ForeTwist": 0.09,
	"Bip01 L ForeTwist1": 0.1, "Bip01 R ForeTwist1": 0.1,
	"Bip01 L Hand": 0.12, "Bip01 R Hand": 0.12,
	"Bip01 Ponytail1": 0.1, "Bip01 Ponytail2": 0.16,
	"Bip01 Beard1": 0.08, "Bip01 Beard2": 0.13,
}
const FINGER_DELAY := 0.13
const KEYS_PER_S := 15.0


static func group_of(clip: String) -> String:
	var c := clip.get_slice("/", 1) if clip.contains("/") else clip
	if c in ["run", "walk", "walk_back", "strafe_left", "strafe_right", "swim", "ladder"]:
		return "move"
	if c in ["idle", "sit_idle", "xbow_idle"] or c.begins_with("combat_idle"):
		return "idle"
	if c in ["bow_aim", "throw_aim", "xbow_aim", "cast_mid"] or (c.begins_with("cast_") and c.ends_with("_mid")):
		return "aim"
	if c.begins_with("emote_"):
		return "emote"
	return ""


static func _delay(bone: String) -> float:
	if DELAY.has(bone):
		return float(DELAY[bone])
	if bone.contains(" Finger"):
		return FINGER_DELAY
	return 0.0


## The clip rebuilt (a new Animation; `a` is left as it is and kept on it as meta "raw").
static func build(a: Animation, clip: String, sk: Skeleton3D, on := enabled) -> Animation:
	var group := group_of(clip)
	var looped := a.loop_mode != Animation.LOOP_NONE
	var st: Dictionary = GROUPS.get(group, {}) if on else {}
	var overlap := float(st.get("overlap", 0.0))
	var steady := float(st.get("head_steady", 0.0))
	var b := Animation.new()
	b.length = a.length
	b.loop_mode = a.loop_mode
	b.step = a.step
	# the keys: 15 a second as the client's. A looping clip's up to, not at, its end - a looping cubic track wraps from
	# its last key back to the first, and a key at the very end is the first one again with no time between them: the
	# curve through it divides by that zero and throws the bones about once a loop (owner 2026-11-05: bow_aim)
	var n := maxi(1, int(ceil(a.length * KEYS_PER_S - 0.01)))
	var times: Array[float] = []
	for i in n + 1:
		var tm := i / KEYS_PER_S
		if looped:
			if i == 0 or tm < a.length - 0.02:
				times.append(tm)
		elif tm < a.length - 0.02:
			times.append(tm)
	if not looped:
		times.append(a.length)
	# rotation tracks by bone (for the head's chain)
	var rot_track := {}
	for t in a.get_track_count():
		if a.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			rot_track[String(a.track_get_path(t).get_concatenated_subnames())] = t
	var sample := func(bone: String, tm: float) -> Quaternion:
		if not rot_track.has(bone):
			var bi := sk.find_bone(bone) if sk else -1
			return sk.get_bone_rest(bi).basis.get_rotation_quaternion() if bi >= 0 else Quaternion.IDENTITY
		var tr: int = rot_track[bone]
		if a.track_get_key_count(tr) <= 1:
			return a.rotation_track_interpolate(tr, 0.0)
		var tt := tm - _delay(bone) * overlap
		tt = fposmod(tt, a.length) if looped else maxf(tt, 0.0)
		return a.rotation_track_interpolate(tr, tt)
	# the head held steadier: its turn in the world (through its chain) pulled toward its average over the clip
	var head_new := {}
	if steady > 0.0 and sk and rot_track.has("Bip01 Head"):
		var chain: Array[String] = []
		var hb := sk.find_bone("Bip01 Head")
		var p := sk.get_bone_parent(hb)
		while p >= 0:
			chain.push_front(sk.get_bone_name(p))
			p = sk.get_bone_parent(p)
		var worlds: Array[Quaternion] = []
		var parents: Array[Quaternion] = []
		var acc := Vector4.ZERO
		var ref := Quaternion.IDENTITY
		for tm in times:
			var q := Quaternion.IDENTITY
			for bn in chain:
				q = q * (sample.call(bn, tm) as Quaternion)
			var w: Quaternion = q * (sample.call("Bip01 Head", tm) as Quaternion)
			if worlds.is_empty():
				ref = w
			if ref.dot(w) < 0.0:
				w = -w
			worlds.append(w)
			parents.append(q)
			acc += Vector4(w.x, w.y, w.z, w.w)
		acc = acc.normalized()
		var mean := Quaternion(acc.x, acc.y, acc.z, acc.w)
		for i in times.size():
			var target := worlds[i].slerp(mean, steady)
			head_new[i] = (parents[i].inverse() * target).normalized()
	for t in a.get_track_count():
		var ty := a.track_get_type(t)
		var nt := b.add_track(ty)
		b.track_set_path(nt, a.track_get_path(t))
		b.track_set_enabled(nt, a.track_is_enabled(t))
		b.track_set_interpolation_loop_wrap(nt, a.track_get_interpolation_loop_wrap(t))
		var single := a.track_get_key_count(t) <= 1
		var bone := String(a.track_get_path(t).get_concatenated_subnames())
		match ty:
			Animation.TYPE_POSITION_3D:
				for tm in ([0.0] if single else times):
					b.position_track_insert_key(nt, tm, a.position_track_interpolate(t, tm))
			Animation.TYPE_ROTATION_3D:
				if single:
					b.rotation_track_insert_key(nt, 0.0, a.rotation_track_interpolate(t, 0.0))
				else:
					for i in times.size():
						var q: Quaternion = head_new[i] if bone == "Bip01 Head" and head_new.has(i) else sample.call(bone, times[i])
						b.rotation_track_insert_key(nt, times[i], q)
			Animation.TYPE_SCALE_3D:
				for tm in ([0.0] if single else times):
					b.scale_track_insert_key(nt, tm, a.scale_track_interpolate(t, tm))
			Animation.TYPE_BLEND_SHAPE:
				for tm in ([0.0] if single else times):
					b.blend_shape_track_insert_key(nt, tm, a.blend_shape_track_interpolate(t, tm))
			_:
				for k in a.track_get_key_count(t):
					b.track_insert_key(nt, a.track_get_key_time(t, k), a.track_get_key_value(t, k), a.track_get_key_transition(t, k))
		b.track_set_interpolation_type(nt, Animation.INTERPOLATION_CUBIC if ty in [Animation.TYPE_POSITION_3D,
				Animation.TYPE_ROTATION_3D, Animation.TYPE_SCALE_3D, Animation.TYPE_BLEND_SHAPE] else a.track_get_interpolation_type(t))
	b.set_meta("smooth", true)
	b.set_meta("raw", a)
	return b
