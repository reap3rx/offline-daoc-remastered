extends SpringBoneSimulator3D
## Remastered cloaks and ponytails (owner 2026-11-14: "Can it be more dynamic where there is actual collision? ... The
## cloaks should feel like heavy wool, not super flowy like a flag in the wind. Just movement with running ... It should
## replace the sway on all cloaks ... the equipment (weapons/shields/quivers on back) to move a bit when moving around,
## so they do not look stiff"). Fig3Figure adds one to its skeleton after Sway; Sway drives it every frame (tick).
## - The cloak's three bone chains (centre, left, right) and a ponytail's hang as springs (Godot's
##   SpringBoneSimulator3D): weight, momentum and drag, pulled back to where the clip has them. The clip's own canned
##   flap of the cloak's control bones is held still while moving - the springs do the moving.
## - They collide with the body: capsules measured from the figure's own meshes (the back, the hips, the thighs, the
##   calves), never fatter than where the cloak hangs at rest - they only stop it going further in.
## - And with what rides on the back (a shield, a slung weapon or bow, a quiver): a shape on the body's side of it - a
##   big sphere under a shield (nearly flat there, letting go below it), a capsule along a weapon - so the cloak stays
##   under it and only the hem below swings out. Player.dress moves that gear out just past the cloak at rest
##   (clear_gear) so the two don't touch standing still or sitting either.
## - The gear itself swings a little about its strap (sway_gear), its shapes with it.
## Remastered and within Fig3Figure.SWAY_RANGE_M only; otherwise everything hangs as the clip has it.

const JOINT_R := 0.04                        # m: a cloak joint's thickness (the cloth round its bone)
const TAIL_R := 0.022                        # m: a ponytail's
const SLAT_R := 0.05                         # m: the level capsules under the gear on the back ...
const SLAT_STEP := 0.07                      # ... and how far apart, up its height
const GAP := 0.02                            # m: what the gear clears the cloak by at rest
# heavy wool (owner: "not super flowy like a flag in the wind"): top of the chain -> the hem (vars: tests tune them)
var STIFF := [10.0, 5.0]
var DRAG := [0.85, 0.75]
var FALL := 0.3                              # the hem's weight (a constant fall, m/s, growing down the chain)
var TAIL_STIFF := [3.0, 1.4]
var TAIL_DRAG := [0.6, 0.45]
var RUN_PUSH := 0.0                          # the air on a run: as if moving this share faster still
const BODY_BONES := ["Bip01 Pelvis", "Bip01 Spine", "Bip01 Spine1", "Bip01 Spine2", "Bip01 L Thigh", "Bip01 R Thigh",
	"Bip01 L Calf", "Bip01 R Calf"]
const MOVE_CLIPS := ["run", "walk", "walk_back", "strafe_left", "strafe_right", "swim", "idle"]

## The simulator measures its joints and shapes in the skeleton's own units (measured 2026-11-14: radii given in
## metres let the cloak through the shield; in the skeleton's units, none); its fall's way is the world's (a fall along
## the skeleton's own down swung the cloak out sideways)
static var units_world := false

var fig: Node3D                              # the Fig3Figure
var model: Node3D
var cloak_on := false                        # a cloak shows (Fig3Figure._apply_cloak)
var _sk: Skeleton3D
var _chains: Array = []                      # per setting: its bones, top to bottom
var _cloak_n := 0                            # settings below this are the cloak's; the rest a ponytail
var _controls := {}                          # cloak control bone -> its idle rotation
var _ctl_w := 0.0
var _body: Array = []                        # the body's collision shapes
var _gear: Array = []                        # the back gear: {node, bone, base, pivot, ax_back, ax_side, col, shape}
var _live := false                           # simulating last frame
var _configured_m := -1.0
var _body_m := -1.0                          # the scale the shapes were made at
var _swayed := false                         # the gear is off its place (sway_gear)
var _back_s := Vector3(0, 0, -1)             # behind the figure, in the skeleton's space
var _yaw := 0.0                              # the figure's facing last frame
var test_lock := false                       # (tests: the joints' settings left as they set them)
var _dt := 0.0                               # the frame time, smoothed
var _dt_set := 1.0 / 120.0                   # ... as the drag was last set for
const REF_FPS := 120.0


## A drag as taken off each frame at REF_FPS, for this frame rate.
func _per_frame(d: float) -> float:
	return 1.0 - pow(1.0 - clampf(d, 0.0, 0.999), _dt_set * REF_FPS)


func setup(sk: Skeleton3D) -> bool:
	_sk = sk
	var idle: Animation = null
	var anim: AnimationPlayer = fig.get("anim") if fig else null
	if anim and anim.has_animation("idle"):
		idle = anim.get_animation("idle")
	var root: Node = anim.get_node_or_null(anim.root_node) if anim else null
	var base := String(root.get_path_to(sk)) if root else ""
	for side in ["C", "L", "R"]:
		var chain: Array[int] = []
		for n in range(1, 10):
			var b := sk.find_bone("Bip01 %s Cloak%02d" % [side, n])
			if b >= 0:
				chain.append(b)
		if chain.size() < 2:
			continue
		_chains.append(chain)
		var top := sk.get_bone_parent(chain[0])
		if top >= 0 and sk.get_bone_name(top).contains("Cloak"):
			var q := sk.get_bone_rest(top).basis.get_rotation_quaternion()
			if idle:
				var ti := idle.find_track(NodePath("%s:%s" % [base, sk.get_bone_name(top)]), Animation.TYPE_ROTATION_3D)
				if ti >= 0:
					q = idle.rotation_track_interpolate(ti, 0.0)
			_controls[top] = q
	_cloak_n = _chains.size()
	var tail: Array[int] = []
	for n in range(1, 10):
		var b := sk.find_bone("Bip01 Ponytail%d" % n)
		if b >= 0:
			tail.append(b)
	if not tail.is_empty():
		_chains.append(tail)
	if _chains.is_empty():
		return false
	setting_count = _chains.size()
	for i in _chains.size():
		var ch: Array = _chains[i]
		set_root_bone(i, int(ch[0]))
		set_end_bone(i, int(ch[ch.size() - 1]))
		set_extend_end_bone(i, true)
		set_end_bone_direction(i, SkeletonModifier3D.BONE_DIRECTION_FROM_PARENT)
		var last := sk.get_bone_rest(int(ch[ch.size() - 1])).origin.length()
		set_end_bone_length(i, last if ch.size() >= 2 else last * 0.8)
		set_individual_config(i, true)
		set_enable_all_child_collisions(i, true)
	active = false
	return true


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


## Metres -> the units the simulator's radii are in.
func _r() -> float:
	return 1.0 if units_world else _m()


func _configure() -> void:
	if test_lock:
		return
	var m := _m()
	if absf(m - _configured_m) < 1e-4 * m:
		return
	for i in _chains.size():
		if get_joint_count(i) <= 0:
			return                                      # (not ready yet: next frame)
	if _body_m > 0.0 and absf(m - _body_m) > 1e-3 * m:
		refresh_body()                                  # (the figure was scaled since: the shapes again)
		refresh_gear()
	_configured_m = m
	for i in _chains.size():
		var tail := i >= _cloak_n
		var n := get_joint_count(i)
		var st: Array = TAIL_STIFF if tail else STIFF
		var dr: Array = TAIL_DRAG if tail else DRAG
		for j in n:
			var u := float(j) / maxf(float(n - 1), 1.0)
			set_joint_radius(i, j, (TAIL_R if tail else JOINT_R) * _r())
			# (the pull back, the drag and the fall are taken a frame at a time: as at REF_FPS whatever the frame rate)
			set_joint_stiffness(i, j, lerpf(float(st[0]), float(st[1]), u) * _dt_set * REF_FPS)
			set_joint_drag(i, j, _per_frame(lerpf(float(dr[0]), float(dr[1]), u)))
			set_joint_gravity(i, j, FALL * u * _r() * _dt_set * REF_FPS)
			set_joint_gravity_direction(i, j, Vector3.DOWN)   # (the world's: measured 2026-11-14)


# ---------------------------------------------------------------- every frame (Sway)

## The figure in range and remastered: simulating, the controls held while it moves, the run's air, the gear's swing.
## vel: the figure's smoothed speed (world, m/s); back / side / bob: the gear's swing (rad).
func tick(dt: float, vel: Vector3, back: float, side: float, bob: float) -> void:
	# the springs' drag is taken off once a frame: kept to what it is at REF_FPS whatever the frame rate (measured
	# 2026-11-14: at 60 fps a turn swung the hem 1.1 m, at 165 fps 0.4 m)
	_dt = lerpf(_dt, clampf(dt, 1.0 / 400.0, 0.1), 0.05) if _dt > 0.0 else clampf(dt, 1.0 / 400.0, 0.1)
	if absf(_dt / _dt_set - 1.0) > 0.08:
		_dt_set = _dt
		_configured_m = -1.0
	_configure()
	var want := cloak_on or _chains.size() > _cloak_n
	var f := model.global_basis * Vector3(0, 0, 1) if model else Vector3(0, 0, 1)
	var yaw := atan2(f.x, f.z)
	var snap := absf(wrapf(yaw - _yaw, -PI, PI)) > 1.0      # (turned round at once: a snap of the facing)
	_yaw = yaw
	if want and (not _live or snap):
		reset()                                         # (from where the clip has it now: no leap from the last time)
	_live = want
	active = want
	var cur := String(fig.anim.current_animation) if fig and fig.anim else ""
	var moving := cur in MOVE_CLIPS or Fig3Figure.is_stop_clip(cur)
	_ctl_w = move_toward(_ctl_w, 1.0 if cloak_on and moving else 0.0, dt * 4.0)
	if _ctl_w > 0.0:
		for b in _controls:
			_sk.set_bone_pose_rotation(int(b), _sk.get_bone_pose_rotation(int(b)).slerp(_controls[b] as Quaternion, _ctl_w))
	external_force = -vel * RUN_PUSH * _r() * _dt_set * REF_FPS   # (the world's way, the skeleton's units, as the fall)
	sway_gear(back, side, bob)


## Out of range, or the classic look: the cloak and the gear hang as the clip has them.
func rest() -> void:
	if _live:
		_live = false
		active = false
	if _swayed:
		_swayed = false
		for g in _gear:
			if is_instance_valid(g.node):
				(g.node as Node3D).transform = g.base
				_place_col(g, g.base)


## After a teleport: from where the clip has it now.
func jumped() -> void:
	if _live:
		reset()


# ---------------------------------------------------------------- the body

## Capsules round the back, the hips and the legs, from the figure's own meshes (the armour it wears too) - each no
## fatter than leaves the cloak room where it hangs at rest.
func refresh_body() -> void:
	if is_inside_tree() and OS.get_thread_caller_id() != OS.get_main_thread_id():
		refresh_body.call_deferred()                    # (a figure dressed on a worker thread, already shown)
		return
	for c in _body:
		if is_instance_valid(c):
			remove_child(c)
			c.queue_free()
	_body.clear()
	if _sk == null or fig == null:
		return
	var pts := _body_points()
	var frame := _frame()
	if frame.is_empty():
		return
	var m := _m()
	_body_m = m
	var cloak_pts: Array[Vector3] = []                  # the cloak's joints at rest (skeleton space), its top left out
	for i in _cloak_n:
		var ch: Array = _chains[i]
		for k in range(1, ch.size()):
			cloak_pts.append(_sk.get_bone_global_rest(int(ch[k])).origin)
		var lg := _sk.get_bone_global_rest(int(ch[ch.size() - 1]))
		var pg := _sk.get_bone_global_rest(int(ch[ch.size() - 2]))
		cloak_pts.append(lg.origin + (lg.origin - pg.origin))
	var pairs := []                                     # [bone, a, b (bone space), back-only]
	for nm in ["Bip01 Spine", "Bip01 Spine1", "Bip01 Spine2"]:
		var b := _sk.find_bone(nm)
		var c := _child_on_chain(b)
		if b >= 0 and c >= 0:
			pairs.append([b, Vector3.ZERO, _sk.get_bone_rest(c).origin, true])
	var pel := _sk.find_bone("Bip01 Pelvis")
	var lt := _sk.find_bone("Bip01 L Thigh")
	var rt := _sk.find_bone("Bip01 R Thigh")
	if pel >= 0 and lt >= 0 and rt >= 0:
		var inv := _sk.get_bone_global_rest(pel).affine_inverse()
		pairs.append([pel, inv * _sk.get_bone_global_rest(lt).origin, inv * _sk.get_bone_global_rest(rt).origin, true])
	for side in ["L", "R"]:
		for nm in ["Bip01 %s Thigh" % side]:          # (not the calves: kicking up behind on the run they knocked the hem
			                                                # out sideways - measured 2026-11-14)
			var b := _sk.find_bone(nm)
			var c := _child_on_chain(b)
			if b >= 0 and c >= 0:
				pairs.append([b, Vector3.ZERO, _sk.get_bone_rest(c).origin, false])
	for p in pairs:
		var b: int = p[0]
		var a: Vector3 = p[1]
		var e: Vector3 = p[2]
		var pp: Array = pts.get(b, [])
		if pp.size() < 12 or a.distance_to(e) < 1e-4:
			continue
		var g := _sk.get_bone_global_rest(b)
		var back_b := (g.basis.inverse() * (frame.back as Vector3)).normalized()
		# (a little inside the body's surface: they only keep the cloak from going in, never hold it off the body - at
		# full size they held the hem 10 cm out and wide)
		var r := _spread(pp, a, e, back_b if bool(p[3]) else Vector3.ZERO) * (0.9 if bool(p[3]) else 0.8)
		# no fatter than leaves the cloak's joints their room where it hangs at rest
		var room := INF
		var inv := g.affine_inverse()
		for cp in cloak_pts:
			room = minf(room, _seg_dist(inv * cp, a, e))
		if room < INF:
			r = minf(r, (room - JOINT_R * m) * 0.95)
		if r <= 0.01 * m:
			continue
		var col := SpringBoneCollisionCapsule3D.new()
		add_child(col)
		col.bone = b
		col.position_offset = (a + e) * 0.5
		col.rotation_offset = Quaternion(Vector3.UP, (e - a).normalized())
		col.radius = r / m * _r()
		col.height = (a.distance_to(e) + 2.0 * r) / m * _r()
		_body.append(col)


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


static func _seg_dist(p: Vector3, a: Vector3, e: Vector3) -> float:
	var d := e - a
	var t := clampf((p - a).dot(d) / maxf(d.length_squared(), 1e-12), 0.0, 1.0)
	return p.distance_to(a + d * t)


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


## The gear on the back, after Player.dress put it there: each piece's shape the cloak stays under, and the strap it
## swings about.
func refresh_gear() -> void:
	if is_inside_tree() and OS.get_thread_caller_id() != OS.get_main_thread_id():
		refresh_gear.call_deferred()
		return
	for g in _gear:
		for cs in g.cols:
			if is_instance_valid(cs[0]):
				remove_child(cs[0])
				(cs[0] as Node).queue_free()
	_gear.clear()
	if _sk == null:
		return
	var frame := _frame()
	if frame.is_empty():
		return
	_back_s = frame.back
	var m := _m()
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
		var back := (frame.back as Vector3)
		var up := (frame.up as Vector3)
		# the strap: the top of the piece, at its middle
		var top := (fp.centre as Vector3) + up * absf((fp.u as Vector3).dot(up)) * float(fp.hu) + up * absf((fp.v as Vector3).dot(up)) * float(fp.hv)
		var entry := {"node": w, "bone": bone, "base": w.transform, "pivot": to_bone * top, "box": Player._holder_box(w),
			"ax_back": (tb * back.cross(up)).normalized(), "ax_side": (tb * back).normalized(), "cols": []}
		# the shapes on the body's side of it (skeleton space): their front at its inner face
		var face := (fp.centre as Vector3) + back * (float(fp.inner) - (fp.centre as Vector3).dot(back))
		var u := (fp.u as Vector3)
		var v := (fp.v as Vector3)
		var hu := float(fp.hu)
		var hv := float(fp.hv)
		# under it, slats: level capsules stacked up its height, each as wide as the piece is there, their fronts at its
		# inner face - flat where it is, and pushing the cloak only toward the body (and a little up or down), never
		# sideways (a sphere under a shield worn to one side pushed the whole cloak over to the other)
		var right := (frame.right as Vector3)
		var oval := hu < hv * 1.8                                         # (a shield; else a long piece: a box)
		var inside := func(q: Vector3) -> bool:
			var a := (q - face).dot(u) / maxf(hu, 1e-6)
			var b := (q - face).dot(v) / maxf(hv, 1e-6)
			return a * a + b * b <= 1.0 if oval else (absf(a) <= 1.0 and absf(b) <= 1.0)
		var reach_x := absf(u.dot(right)) * hu + absf(v.dot(right)) * hv
		var reach_y := absf(u.dot(up)) * hu + absf(v.dot(up)) * hv
		var rs := SLAT_R * m
		var step := SLAT_STEP * m
		var shapes := []                                                   # [collider, skeleton-space transform]
		var y := -reach_y + step * 0.5
		while y < reach_y:
			var lo := INF
			var hi := -INF
			for k in 33:
				var x := lerpf(-reach_x, reach_x, float(k) / 32.0)
				if inside.call(face + right * x + up * y):
					lo = minf(lo, x)
					hi = maxf(hi, x)
			if hi >= lo:
				var mid := face + right * ((lo + hi) * 0.5) + up * y + back * rs
				var cp := SpringBoneCollisionCapsule3D.new()
				cp.radius = rs / m * _r()
				cp.height = (hi - lo + 2.0 * rs) / m * _r()
				shapes.append([cp, Transform3D(Basis(Quaternion(Vector3.UP, right)), mid)])
			y += step
		for s in shapes:
			var col: SpringBoneCollision3D = s[0]
			add_child(col)
			col.bone = bone
			# the shape in the piece's frame: bone space, then undone by its placement (it swings with the piece)
			(entry.cols as Array).append([col, (w.transform as Transform3D).affine_inverse() * (to_bone * (s[1] as Transform3D))])
		_place_col(entry, w.transform)
		_gear.append(entry)


func _place_col(g: Dictionary, xf: Transform3D) -> void:
	for cs in g.cols:
		var col = cs[0]
		if not is_instance_valid(col):
			continue
		var s: Transform3D = xf * (cs[1] as Transform3D)
		(col as SpringBoneCollision3D).position_offset = s.origin
		(col as SpringBoneCollision3D).rotation_offset = s.basis.get_rotation_quaternion()


## The gear swings a little about its strap: back as the run starts or stops (back), side to side through a turn
## (side) and with the stride (bob) - its shape with it.
func sway_gear(back: float, side: float, bob: float) -> void:
	_swayed = not _gear.is_empty()
	for g in _gear:
		var w = g.node
		if not is_instance_valid(w):
			continue
		var r := Basis(g.ax_back as Vector3, back) * Basis(g.ax_side as Vector3, side + bob)
		var piv: Vector3 = g.pivot
		var xf := Transform3D(r, piv - r * piv) * (g.base as Transform3D)
		(w as Node3D).transform = xf
		_place_col(g, xf)


# ---------------------------------------------------------------- for the hair (Fig3Figure.HairCollide)

## The back's and the cloak's capsules as they are now (in the skeleton's modifier pass, after the springs), world:
## [a, b, radius m]. The hair lies outside them.
func hair_capsules() -> Array:
	var out := []
	var xf := _sk.global_transform
	var m := _m()
	for col in _body:
		if not is_instance_valid(col) or not (col is SpringBoneCollisionCapsule3D) or not _sk.get_bone_name(col.bone).contains("Spine"):
			continue
		var g := xf * _sk.get_bone_global_pose(col.bone) * Transform3D(Basis(col.rotation_offset), col.position_offset)
		var r: float = col.radius / _r()
		var half := maxf(col.height / _r() * 0.5 - r, 0.0) * m
		out.append([g * Vector3(0, -half, 0), g * Vector3(0, half, 0), r])
	if cloak_on and _live:
		for i in _cloak_n:
			var ch: Array = _chains[i]
			var prev := Vector3.INF
			var before := Vector3.INF
			for b in ch:
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
