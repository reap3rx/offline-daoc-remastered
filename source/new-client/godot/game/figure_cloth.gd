extends SkeletonModifier3D
## Remastered cloaks and ponytails (owner 2026-11-14: "The cloaks should feel like heavy wool, not super flowy like a flag
## in the wind. Just movement with running ... It should replace the sway on all cloaks ... the equipment
## (weapons/shields/quivers on back) to move a bit when moving around, so they do not look stiff").
## A first version on Godot's spring bones with collision shapes was dropped the same day (owner: "it does not act in a
## realistic way ... clipping bad through the body ... almost seems like it's moving on it's own"): three chains of
## five joints are too few for collision, and it never hung straight. This one is built on limits instead:
## - Only the figure's own movement moves the cloak: its speed ahead swings it back, a start kicks it, strafing and
##   turning swing it to the side. Standing still it hangs as the clip has it.
## - It cannot go into the body: it swings back and to the side from where the clip hangs it, never forward.
## - It moves as one sheet: the three chains (centre, left, right) swing alike, more toward the hem, the hem a beat
##   behind the top (two springs in a row), heavy and well damped.
## - With something on the back (a shield, a slung weapon or bow, a quiver) the joints under it stay put - they keep a
##   third of the clip's own flap and add none - and the hem below it swings free. Player.dress moves that gear out
##   just past the cloak at rest (clear_gear), and it swings a little about its strap (sway_gear).
## Fig3Figure adds one to its skeleton; Sway calls tick from its own pass (after the body's lean and turn), so the node
## does nothing as a modifier itself. Remastered and within Fig3Figure.SWAY_RANGE_M only.

const JOINT_R := 0.04                        # m: the cloth's thickness round a joint (clear_gear, the hair)
const GAP := 0.02                            # m: what the gear clears the cloak by at rest
const SHARE := [0.34, 0.16, 0.24, 0.16, 0.10]    # each joint's part of the swing, top to hem
const RUN_BACK := 0.055                      # rad of swing back per m/s ahead ...
const RUN_BACK_MAX := 0.33                   # ... up to this (on top of what is kept of the run clip's own: enough
                                             # that the heels kicking up behind stay under the hem)
const BACK_MAX := 0.5                        # the most it ever swings back
const SIDE_MAX := 0.3                        # ... or to a side
const START_KICK := 0.07                     # a start's kick back (rad/s per m/s gained)
const STRAFE_SIDE := 0.04                    # rad to the side per m/s sideways
const TURN_SIDE := 0.04                      # rad out of a turn per rad/s ...
const TURN_SIDE_RUN := 0.017                 # ... and per rad/s and m/s ahead
const CLIP_KEEP := 0.5                       # how much of the clip's own flap of the cloak is kept ...
const UNDER_GEAR_CLIP := 0.25                # ... and under the gear
const UNDER_GEAR_SIDE := 0.4                 # ... and of the swing to the side
const GEAR_BACK := 0.1                       # the gear's own swing: this share of the cloak's
const GEAR_SIDE := 0.2

var fig: Node3D                              # the Fig3Figure
var model: Node3D
var cloak_on := false                        # a cloak shows (Fig3Figure._apply_cloak)
var _sk: Skeleton3D
var _chains: Array = []                      # the cloak's chains (C, L, R): their bones, top to bottom
var _cloak_n := 0
var _tail := -1                              # a ponytail's first bone
var _controls: Array[int] = []               # the control bones the chains hang from
var _held := {}                              # cloak bone -> its idle rotation
var _covered: Array = []                     # per chain, per joint: under the gear on the back
var _spines: Array = []                      # the back, for the hair: [bone, a, e (bone space), radius (skeleton units)]
var _gear: Array = []                        # the back gear: {node, bone, base, pivot, box, ax_back, ax_side}
var _swayed := false                         # the gear is off its place (sway_gear)
var _back_s := Vector3(0, 0, -1)             # behind the figure, in the skeleton's space
var _phase := 0.0
# the swing: the top (1) and the hem (2), back and to the side (rad), and their speeds
var _b1 := 0.0
var _b1v := 0.0
var _b2 := 0.0
var _b2v := 0.0
var _s1 := 0.0
var _s1v := 0.0
var _s2 := 0.0
var _s2v := 0.0
var _yaw := INF
var _om := 0.0                               # how fast it turns (rad/s, smoothed; + to its left)
var _vz := 0.0                               # its speed ahead last frame (smoothed)
var _move_w := 0.0                           # 0..1: a moving clip plays (the clip's own flap is held back)
const MOVE_CLIPS := ["run", "walk", "walk_back", "strafe_left", "strafe_right", "idle"]


func setup(sk: Skeleton3D) -> bool:
	_sk = sk
	var idle: Animation = null
	var anim: AnimationPlayer = fig.get("anim") if fig else null
	if anim and anim.has_animation("idle"):
		idle = anim.get_animation("idle")
	var root: Node = anim.get_node_or_null(anim.root_node) if anim else null
	var base := String(root.get_path_to(sk)) if root else ""
	var hold := func(b: int) -> void:
		var q := sk.get_bone_rest(b).basis.get_rotation_quaternion()
		if idle:
			var ti := idle.find_track(NodePath("%s:%s" % [base, sk.get_bone_name(b)]), Animation.TYPE_ROTATION_3D)
			if ti >= 0:
				q = idle.rotation_track_interpolate(ti, 0.0)
		_held[b] = q
	for side in ["C", "L", "R"]:
		var chain: Array[int] = []
		for n in range(1, 10):
			var b := sk.find_bone("Bip01 %s Cloak%02d" % [side, n])
			if b >= 0:
				chain.append(b)
				hold.call(b)
		if chain.size() < 2:
			continue
		_chains.append(chain)
		var top := sk.get_bone_parent(chain[0])
		if top >= 0 and sk.get_bone_name(top).contains("Cloak"):
			_controls.append(top)
			hold.call(top)
	_cloak_n = _chains.size()
	_tail = sk.find_bone("Bip01 Ponytail1")
	_phase = float(get_instance_id() % 997) * 0.37
	return _cloak_n > 0 or _tail >= 0


## Metres -> the skeleton's own units (its scale up to the figure, which may not be in the tree yet).
func _m() -> float:
	var s := 1.0
	var n: Node = _sk
	while n != null:
		if n is Node3D:
			s *= (n as Node3D).transform.basis.get_scale().y
		if n == fig:
			break
		n = n.get_parent()
	return 1.0 / maxf(s, 1e-5)


# ---------------------------------------------------------------- every frame (Sway)

## The figure in range and remastered. v: its speed in its own frame (m/s: z ahead, x to its left), smoothed; fresh:
## the first frame in range, or after a teleport.
func tick(dt: float, v: Vector3, fresh: bool) -> void:
	var f := model.global_basis * Vector3(0, 0, 1)
	var yaw := atan2(f.x, f.z)
	var dy := 0.0 if _yaw == INF else wrapf(yaw - _yaw, -PI, PI)
	_yaw = yaw
	if fresh or absf(dy) > 1.0:                          # (or turned round at once: nothing to swing from)
		_still()
		dy = 0.0
	_om = lerpf(_om, clampf(dy / maxf(dt, 0.001), -8.0, 8.0), 1.0 - exp(-dt * 10.0))
	# a start leaves the cloak behind a moment, a stop lets it fall in sooner - both ways alike (only the gains would
	# add up the speed's own flicker into a steady push: measured, the cloak flew level behind a run)
	var dv := clampf(v.z - _vz, -9.0, 9.0)
	_vz = v.z
	_b1v += dv * START_KICK
	var want_b := clampf(v.z * RUN_BACK, 0.0, RUN_BACK_MAX)
	# to a side: against a strafe, and out of a turn (more at a run); + is to its left
	var want_s := clampf(-v.x * STRAFE_SIDE - _om * (TURN_SIDE + TURN_SIDE_RUN * clampf(v.z, 0.0, 7.0)), -SIDE_MAX, SIDE_MAX)
	# a lighter cloth (owner 2026-11-14: "Heavy wool might be too heavy ... something lighter, like linen"): quick to
	# follow, the hem a beat behind the top and swinging a little past it. In steps of a 60th of a
	# second at most: the same at any frame rate, and a slow frame can't set it shaking
	var sdt := minf(dt, 0.25)
	var steps := ceili(sdt * 60.0)
	var h := sdt / steps
	for _i in steps:
		_b1v += ((want_b - _b1) * 36.0 - _b1v * 7.5) * h
		_b1 += _b1v * h
		if _b1 < 0.0:                                    # (never forward, into the body)
			_b1 = 0.0
			_b1v = maxf(_b1v, 0.0)
		_b2v += ((_b1 - _b2) * 24.0 - _b2v * 5.5) * h
		_b2 += _b2v * h
		if _b2 < 0.0:
			_b2 = 0.0
			_b2v = maxf(_b2v, 0.0)
		_s1v += ((want_s - _s1) * 36.0 - _s1v * 7.5) * h
		_s1 += _s1v * h
		_s2v += ((_s1 - _s2) * 24.0 - _s2v * 5.5) * h
		_s2 += _s2v * h
	_b1 = minf(_b1, BACK_MAX)
	_b2 = minf(_b2, BACK_MAX)
	_s1 = clampf(_s1, -SIDE_MAX, SIDE_MAX)
	_s2 = clampf(_s2, -SIDE_MAX, SIDE_MAX)
	# the figure's ahead and up in the skeleton's space; + about axis_back swings the lower end back, + about fwd
	# to its left
	var to_skel := _sk.global_basis.orthonormalized().inverse() * model.global_basis.orthonormalized()
	var fwd := (to_skel * Vector3(0, 0, 1)).normalized()
	var up := (to_skel * Vector3.UP).normalized()
	var axis_back := up.cross(fwd).normalized()
	if cloak_on:
		var geared := false                              # a broad piece holds some of it still (refresh_gear)
		for cov0 in _covered:
			if (cov0 as Array).has(true):
				geared = true
		# the clip's own flap of the cloak (the run's throws it out level behind, like a flag): only a part kept - the
		# heavy cloth's swing is this one's; under the gear less still
		# (the moving clips only: sitting, lying, a swing or a cast lay the cloak out their own way)
		var cur := String(fig.anim.current_animation) if fig and fig.anim else ""
		_move_w = move_toward(_move_w, 1.0 if cur in MOVE_CLIPS or Fig3Figure.is_stop_clip(cur) else 0.0, dt * 4.0)
		var keep_free := lerpf(1.0, CLIP_KEEP, _move_w)
		var keep_under := lerpf(1.0, UNDER_GEAR_CLIP, _move_w)
		for b in _controls:
			_hold(b, keep_under if geared else keep_free)
		for i in _cloak_n:
			var ch: Array = _chains[i]
			var cov: Array = _covered[i] if i < _covered.size() else []
			# what the joints under the gear give up, the free ones below take (up to twice their own)
			var free_sum := 0.0
			var all_sum := 0.0
			for j in ch.size():
				var sh: float = SHARE[mini(j, SHARE.size() - 1)]
				all_sum += sh
				if not (geared and j < cov.size() and bool(cov[j])):
					free_sum += sh
			var boost := clampf(all_sum * 0.8 / free_sum, 1.0, 2.0) if free_sum > 0.0 and free_sum < all_sum else 1.0
			for j in ch.size():
				var b: int = ch[j]
				var sh: float = SHARE[mini(j, SHARE.size() - 1)]
				var under: bool = geared and j < cov.size() and bool(cov[j])
				var bk := (_b1 if j < 2 else _b2) * sh
				var sd := (_s1 if j < 2 else _s2) * sh
				_hold(b, keep_under if under else keep_free)
				if under:
					bk = 0.0
					sd *= UNDER_GEAR_SIDE
				else:
					bk *= boost
				if absf(bk) > 1e-5 or absf(sd) > 1e-5:
					_turn(b, axis_back, bk, fwd, sd)
	if _tail >= 0:
		_turn(_tail, axis_back, _b2 * 0.8, fwd, _s2 * 1.2)
	var t := Time.get_ticks_msec() / 1000.0
	var stride := sin(t * 10.0 + _phase) * minf(Vector2(v.x, v.z).length(), 7.0) * 0.0025
	sway_gear(_b1 * GEAR_BACK, _s1 * GEAR_SIDE, stride)


## A cloak bone under the gear: only a part of the clip's own flap kept.
func _hold(b: int, keep: float) -> void:
	if keep >= 0.999:
		return
	_sk.set_bone_pose_rotation(b, (_held[b] as Quaternion).slerp(_sk.get_bone_pose_rotation(b), keep))


## A bone turned about two axes of the skeleton's space, about its own joint.
func _turn(b: int, axis_back: Vector3, back: float, axis_side: Vector3, side: float) -> void:
	var g := _sk.get_bone_global_pose(b)
	var p := _sk.get_bone_parent(b)
	var pg := _sk.get_bone_global_pose(p) if p >= 0 else Transform3D.IDENTITY
	var ng := Transform3D(Basis(axis_back, back) * Basis(axis_side, side) * g.basis, g.origin)
	_sk.set_bone_pose_rotation(b, (pg.affine_inverse() * ng).basis.get_rotation_quaternion())


func _still() -> void:
	_b1 = 0.0
	_b1v = 0.0
	_b2 = 0.0
	_b2v = 0.0
	_s1 = 0.0
	_s1v = 0.0
	_s2 = 0.0
	_s2v = 0.0
	_om = 0.0
	_vz = 0.0


## Out of range, or the classic look: the cloak and the gear hang as the clip has them.
func rest() -> void:
	_still()
	_yaw = INF
	if _swayed:
		_swayed = false
		for g in _gear:
			if is_instance_valid(g.node):
				(g.node as Node3D).transform = g.base


## After a teleport.
func jumped() -> void:
	_still()


# ---------------------------------------------------------------- the back (for the hair)

## The back's capsules from the figure's own meshes (the armour it wears too): the hair lies outside them.
func refresh_body() -> void:
	_spines.clear()
	if _sk == null or fig == null:
		return
	var frame := _frame()
	if frame.is_empty():
		return
	var pts := _body_points()
	for nm in ["Bip01 Spine", "Bip01 Spine1", "Bip01 Spine2"]:
		var b := _sk.find_bone(nm)
		var c := _child_on_chain(b)
		if b < 0 or c < 0:
			continue
		var a := Vector3.ZERO
		var e := _sk.get_bone_rest(c).origin
		var pp: Array = pts.get(b, [])
		if pp.size() < 12 or a.distance_to(e) < 1e-4:
			continue
		var back_b := (_sk.get_bone_global_rest(b).basis.inverse() * (frame.back as Vector3)).normalized()
		var r := _spread(pp, a, e, back_b)
		if r > 0.0:
			_spines.append([b, a, e, r])


func _child_on_chain(b: int) -> int:
	if b < 0:
		return -1
	var want := {"Bip01 Spine": "Bip01 Spine1", "Bip01 Spine1": "Bip01 Spine2", "Bip01 Spine2": "Bip01 Neck",
		"Bip01 L Thigh": "Bip01 L Calf", "Bip01 R Thigh": "Bip01 R Calf", "Bip01 L Calf": "Bip01 L Foot",
		"Bip01 R Calf": "Bip01 R Foot"}
	var c := _sk.find_bone(String(want.get(_sk.get_bone_name(b), "")))
	return c if c >= 0 and _sk.get_bone_parent(c) == b else -1


## How far the body reaches round a bone's segment (a .. e, bone space): the 75th percentile of its points' distance
## from it - or, given `back`, of how far they reach behind it.
static func _spread(pts: Array, a: Vector3, e: Vector3, back: Vector3) -> float:
	var d := e - a
	var l2 := d.length_squared()
	var vals: Array[float] = []
	for p in pts:
		var t := ((p as Vector3) - a).dot(d) / l2
		if t < 0.08 or t > 0.92:
			continue
		var off := (p as Vector3) - (a + d * t)
		if back == Vector3.ZERO:
			vals.append(off.length())
		else:
			var k := off.dot(back)
			if k > 0.0:
				vals.append(k)
	if vals.size() < 6:
		return 0.0
	vals.sort()
	return vals[int(vals.size() * 0.75)]


# ---------------------------------------------------------------- the meshes' points

static var _pts_cache := {}                  # "<mesh>|<skin>" -> {bone name: Array[Vector3] (bone space)}


## The visible meshes' points by the bone that moves them most (bone space, rest) - the body and its armour, or with
## cloak true the cloak alone.
func _body_points(cloak := false) -> Dictionary:
	var out := {}
	var cloak_meshes := {}
	var hair_meshes := {}
	var parts: Dictionary = fig.get("_meshes")
	for k in parts:
		for mi in parts[k]:
			if String(k).begins_with("cloak"):
				cloak_meshes[mi] = true
			elif String(k).begins_with("hair") or String(k) in ["head", "beard", "moustache"] or String(k).begins_with("fullhelm"):
				hair_meshes[mi] = true
	for n in fig.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi == null or not mi.visible or mi.mesh == null or mi.skin == null:
			continue
		if cloak != cloak_meshes.has(mi) or (not cloak and hair_meshes.has(mi)):
			continue
		var key := "%d|%d" % [mi.mesh.get_rid().get_id(), mi.skin.get_rid().get_id()]
		if not _pts_cache.has(key):
			_pts_cache[key] = _mesh_points(mi, _sk)
		var per: Dictionary = _pts_cache[key]
		for nm in per:
			# (the meshes are bound to "<bone> def" copies of the bones: their points go to the bone itself)
			var src := _sk.find_bone(String(nm))
			var b := _sk.find_bone(String(nm).trim_suffix(" def"))
			if src < 0 or b < 0:
				continue
			if not out.has(b):
				out[b] = []
			if src == b:
				(out[b] as Array).append_array(per[nm])
			else:
				var conv := _sk.get_bone_global_rest(b).affine_inverse() * _sk.get_bone_global_rest(src)
				for p in per[nm]:
					(out[b] as Array).append(conv * (p as Vector3))
	return out


static func _mesh_points(mi: MeshInstance3D, sk: Skeleton3D) -> Dictionary:
	var out := {}
	var skin := mi.skin
	var names: Array[String] = []
	for i in skin.get_bind_count():
		var nm := String(skin.get_bind_name(i))
		if nm == "" and skin.get_bind_bone(i) >= 0:
			nm = sk.get_bone_name(skin.get_bind_bone(i))
		names.append(nm)
	for s in mi.mesh.get_surface_count():
		var arr := mi.mesh.surface_get_arrays(s)
		var vs = arr[Mesh.ARRAY_VERTEX]
		var bs = arr[Mesh.ARRAY_BONES]
		var ws = arr[Mesh.ARRAY_WEIGHTS]
		if vs == null or bs == null or ws == null or (vs as PackedVector3Array).is_empty():
			continue
		var nv := (vs as PackedVector3Array).size()
		var per: int = (bs as PackedInt32Array).size() / nv
		if per <= 0:
			continue
		var step := maxi(1, nv / 2500)
		for v in range(0, nv, step):
			var best := -1
			var bw := 0.0
			for k in per:
				var w: float = ws[v * per + k]
				if w > bw:
					bw = w
					best = bs[v * per + k]
			if best < 0 or best >= names.size():
				continue
			var nm: String = names[best]
			if not out.has(nm):
				out[nm] = []
			(out[nm] as Array).append(skin.get_bind_pose(best) * (vs[v] as Vector3))
	return out


func _frame() -> Dictionary:
	return Player.BodyFrame.of(_sk, model) if model else {}


# ---------------------------------------------------------------- the gear on the back

## Player.dress: a piece on the back moved out just past where the cloak hangs at rest (owner 2026-11-14: "the
## position of the shield on the back can be moved further away from the body ... when a cloak is being worn").
func clear_gear(bone: int, w: Node3D) -> void:
	if w and not w.has_meta("placed_xf"):
		w.set_meta("placed_xf", w.transform)              # (where dress put it: back there without a cloak)
	if not cloak_on or bone < 0 or w == null:
		return
	var frame := _frame()
	if frame.is_empty():
		return
	var back: Vector3 = frame.back
	var shape := _footprint(bone, w, w.transform, frame)
	if shape.is_empty():
		return
	var cloak := _body_points(true)
	var outer := -INF
	var m := _m()
	var reach: float = 0.03 * m
	for b in cloak:
		var g := _sk.get_bone_global_rest(int(b))
		for p in cloak[b]:
			var q: Vector3 = g * (p as Vector3)                      # (skeleton space)
			var rel: Vector3 = q - (shape.centre as Vector3)
			if absf(rel.dot(shape.u)) <= float(shape.hu) + reach and absf(rel.dot(shape.v)) <= float(shape.hv) + reach:
				outer = maxf(outer, q.dot(back))
	# and the cloak's joints, whose thickness the springs keep off it (or they would sit pressed against it)
	var joint_outer := -INF
	for i in _cloak_n:
		for b in _chains[i]:
			var q := _sk.get_bone_global_rest(int(b)).origin
			var rel: Vector3 = q - (shape.centre as Vector3)
			if absf(rel.dot(shape.u)) <= float(shape.hu) + JOINT_R * m and absf(rel.dot(shape.v)) <= float(shape.hv) + JOINT_R * m:
				joint_outer = maxf(joint_outer, q.dot(back) + JOINT_R * m)
	if outer == -INF and joint_outer == -INF:
		return
	var push := maxf(outer + GAP * m, joint_outer + 0.005 * m) - float(shape.inner)
	if push > 0.0:
		w.position += _sk.get_bone_global_rest(bone).basis.inverse() * (back * push)


## A piece's footprint on the back (skeleton space, rest): its middle, the two ways it spreads across the back (u its
## longer) and how far each way, and how far behind the body its inner face is (along frame.back).
func _footprint(bone: int, w: Node3D, xf: Transform3D, frame: Dictionary) -> Dictionary:
	var box := Player._holder_box(w)
	if box.size == Vector3.ZERO:
		return {}
	var back: Vector3 = frame.back
	var g := _sk.get_bone_global_rest(bone) * xf
	var corners: Array[Vector3] = []
	for i in 8:
		corners.append(g * box.get_endpoint(i))
	# its longest edge, flat on the back
	var best := Vector3.ZERO
	for i in 3:
		var ax := Vector3.ZERO
		ax[i] = box.size[i]
		var s := g.basis * ax
		s -= back * s.dot(back)
		if s.length() > best.length():
			best = s
	var u := best.normalized() if best.length() > 1e-6 else (frame.up as Vector3)
	var v := back.cross(u).normalized()
	var lo := Vector3(INF, INF, INF)
	var hi := -lo
	for c in corners:
		var k := Vector3(c.dot(u), c.dot(v), c.dot(back))
		lo = lo.min(k)
		hi = hi.max(k)
	var mid := (lo + hi) * 0.5
	return {"u": u, "v": v, "hu": (hi.x - lo.x) * 0.5, "hv": (hi.y - lo.y) * 0.5, "inner": lo.z, "outer": hi.z,
		"centre": u * mid.x + v * mid.y + back * mid.z}


## A cloak put on or taken off (or shown / hidden) after the gear was dressed: the gear moved out for it, or back.
func cloak_changed() -> void:
	for g in _gear:
		var w = g.node
		if is_instance_valid(w):
			(w as Node3D).transform = (w as Node3D).get_meta("placed_xf", g.base)
			clear_gear(int(g.bone), w)
	refresh_gear()


## The gear on the back, after Player.dress put it there: the strap each piece swings about, and which of the cloak's
## joints are under it.
func refresh_gear() -> void:
	_gear.clear()
	_covered.clear()
	if _sk == null:
		return
	var frame := _frame()
	if frame.is_empty():
		return
	_back_s = frame.back
	var back := (frame.back as Vector3)
	var up := (frame.up as Vector3)
	var bottom := INF                                   # the lowest the gear reaches (along up, skeleton space)
	for at in _sk.get_children():
		if not (at is BoneAttachment3D) or at.get_child_count() == 0 or at.is_queued_for_deletion():
			continue                                     # (the last dress's, going)
		var bn := String((at as BoneAttachment3D).bone_name)
		if not (bn.ends_with(" Back") or at.has_meta("back_gear")):
			continue
		var w := at.get_child(0) as Node3D
		var bone := _sk.find_bone(bn)
		if w == null or bone < 0:
			continue
		var fp := _footprint(bone, w, w.transform, frame)
		if fp.is_empty():
			continue
		var to_bone := _sk.get_bone_global_rest(bone).affine_inverse()       # (skeleton space -> the bone's)
		var tb := to_bone.basis
		var reach := absf((fp.u as Vector3).dot(up)) * float(fp.hu) + absf((fp.v as Vector3).dot(up)) * float(fp.hv)
		# a broad piece (a shield) holds the cloak under it still; a long one (a slung weapon, a bow, a quiver) rides
		# on the cloak instead - pinned under a spear the whole cloak hung dead and the heels came through it
		# (owner 2026-11-14, later: the shield too - "if the cloak is stiff, you see the feet clipping through the cloak
		# when she runs. So if the shield rotates to move with the cloak when it lifts up, it would not clip")
		var long_ := true
		var low := (fp.centre as Vector3).dot(up) - reach
		if not long_:
			bottom = minf(bottom, low)
		var ride := -1                                   # the centre chain's joint about level with its lower end
		if long_ and _cloak_n > 0:
			var ch: Array = _chains[0]
			ride = ch.size() - 1
			for k in range(1, ch.size()):
				if _sk.get_bone_global_rest(int(ch[k])).origin.dot(up) <= low:
					ride = k
					break
		# the strap: the top of the piece, at its middle
		var top := (fp.centre as Vector3) + up * reach
		_gear.append({"node": w, "bone": bone, "base": w.transform, "pivot": to_bone * top, "box": Player._holder_box(w),
			"ax_back": (tb * back.cross(up)).normalized(), "ax_side": (tb * back).normalized(), "ride": ride})
	var m := _m()
	for i in _cloak_n:
		var cov := []
		for b in _chains[i]:
			# a joint moves the cloth below it: under the gear if that cloth still is (3 cm to spare)
			cov.append(_sk.get_bone_global_rest(int(b)).origin.dot(up) > bottom + 0.03 * m)
		_covered.append(cov)


## The gear swings a little about its strap: back as the run starts (back), to a side through a turn (side) and with
## the stride (bob).
func sway_gear(back: float, side: float, bob: float) -> void:
	_swayed = not _gear.is_empty()
	for g in _gear:
		var w = g.node
		if not is_instance_valid(w):
			continue
		var r := Basis(g.ax_back as Vector3, back) * Basis(g.ax_side as Vector3, side + bob)
		if int(g.ride) > 0 and cloak_on:
			# riding on the cloak: turned as the cloak is, from where it hangs at rest, down to the piece's lower end
			var ch: Array = _chains[0]
			var k := int(g.ride)
			var p0 := _sk.get_bone_parent(int(ch[0]))
			var ig := _sk.get_bone_global_pose(p0) if p0 >= 0 else Transform3D.IDENTITY
			if p0 >= 0 and _held.has(p0):                 # (the control bone as it rests, from its own parent)
				var pp := _sk.get_bone_parent(p0)
				ig = (_sk.get_bone_global_pose(pp) if pp >= 0 else Transform3D.IDENTITY) \
						* Transform3D(Basis(_held[p0] as Quaternion), _sk.get_bone_pose_position(p0))
			var itop := Vector3.ZERO
			for j in k + 1:
				ig = ig * Transform3D(Basis(_held[int(ch[j])] as Quaternion), _sk.get_bone_pose_position(int(ch[j])))
				if j == 0:
					itop = ig.origin
			var idle_dir := ig.origin - itop
			var cur_dir := _sk.get_bone_global_pose(int(ch[k])).origin - _sk.get_bone_global_pose(int(ch[0])).origin
			if idle_dir.length() > 1e-5 and cur_dir.length() > 1e-5:
				# about where the cloak hangs from (not the piece's own top: a spear turned about its tip threw its
				# lower end far out from the back - owner 2026-11-14), so the piece stays lying on the cloak
				var bg := _sk.get_bone_global_pose(int(g.bone))
				var bb := bg.basis.orthonormalized()
				r = bb.inverse() * Basis(Quaternion(idle_dir.normalized(), cur_dir.normalized())) * bb
				var cp: Vector3 = bg.affine_inverse() * _sk.get_bone_global_pose(int(ch[0])).origin
				(w as Node3D).transform = Transform3D(r, cp - r * cp) * (g.base as Transform3D)
				continue
		var piv: Vector3 = g.pivot
		(w as Node3D).transform = Transform3D(r, piv - r * piv) * (g.base as Transform3D)


# ---------------------------------------------------------------- for the hair (Fig3Figure.HairCollide)

## The back's and the cloak's capsules as they are now (after Sway's pass), world: [a, b, radius m]. The hair lies
## outside them.
func hair_capsules() -> Array:
	var out := []
	var xf := _sk.global_transform
	var m := _m()
	for s in _spines:
		var g := xf * _sk.get_bone_global_pose(int(s[0]))
		out.append([g * (s[1] as Vector3), g * (s[2] as Vector3), float(s[3]) / m])
	if cloak_on:
		for i in _cloak_n:
			var prev := Vector3.INF
			var before := Vector3.INF
			for b in _chains[i]:
				var p := xf * _sk.get_bone_global_pose(int(b)).origin
				if prev != Vector3.INF:
					out.append([prev, p, JOINT_R + 0.02])
				before = prev
				prev = p
			if before != Vector3.INF:
				out.append([prev, prev + (prev - before), JOINT_R + 0.02])
	return out


## The gear on the back as boxes, world: [middle, x, y, z (z outward, behind the figure), half sizes (m)]. The hair
## lies over them.
func hair_boxes() -> Array:
	var out := []
	var back_w := (_sk.global_basis * _back_s).normalized()
	for g in _gear:
		var w = g.node
		if not is_instance_valid(w) or not (w as Node3D).is_visible_in_tree():
			continue
		var box: AABB = g.box
		var gx := (w as Node3D).global_transform
		var dirs: Array[Vector3] = []
		var halfs: Array[float] = []
		for i in 3:
			var unit := Vector3.ZERO
			unit[i] = box.size[i] * 0.5
			var e := gx.basis * unit
			halfs.append(e.length())
			dirs.append(e.normalized() if e.length() > 1e-6 else Vector3.ZERO)
		var zi := 0
		for i in 3:
			if absf(dirs[i].dot(back_w)) > absf(dirs[zi].dot(back_w)):
				zi = i
		var z := dirs[zi] if dirs[zi].dot(back_w) >= 0.0 else -dirs[zi]
		var xi := (zi + 1) % 3
		var yi := (zi + 2) % 3
		out.append([gx * box.get_center(), dirs[xi], dirs[yi], z, Vector3(halfs[xi], halfs[yi], halfs[zi] + 0.01)])
	return out
