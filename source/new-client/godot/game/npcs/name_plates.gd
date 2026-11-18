class_name NamePlates
extends Node
## Overhead names, measured from the owner's recordings of the real client (2026-10-09, LOUGH DERG LEDGER.md
## "Name plates"):
## - font: the client's Minion Pro Bold (ui/fonts/minionpro-bold.ttf) with a dark outline
## - the same range for friendly NPCs and monsters: about 3.3x the camera-to-player distance (NAME_RANGE from the
##   player at the default camera); a name simply appears / disappears there (owner: no fading)
## - a SET size at every distance (owner: names never grow or shrink as you walk up to them)
## - the target's name (left click) is highlighted: bright white
## - friendly NPCs light aqua (sampled 175, 223, 208), monsters in their con colour to you
## - hidden by walls: a wall or corner in front takes the name away, while a name above a wall top stays visible
##   (owner's video: "watch how this npcs name disappears as I leave around the corner")
## The names are drawn flat on the screen over the world, at whole pixels (owner 2026-11-18 bugs doc: "It's blurry on
## lower resolutions ... They get blurred when they're moving"). They were Label3Ds in the 3D scene, so they went
## through the 3D render scale, FSR and TAA like the world and smeared when the camera moved. Walls still hide them: a
## ray from the camera to the name, checked a few times a second, takes the whole name away while a wall, the ground
## or a building is in front (the old ones were clipped pixel by pixel; now a name is either shown or not).

# The name range, same for friend and foe: the owner's recordings showed names appearing at about 3.3x the camera's
# distance - and the owner's camera sits at its farthest, 500 units (the old client's saved [Camera] distance=500.00;
# game.dll clamps it to 50..500), so ~40 m (~1,600 units). The first reading took our own 3.6 m camera instead and gave
# 12 m - about a monster's aggro range (owner 2026-10-14: "I don't see an enemy's nameplate until it's in aggro range").
const NAME_RANGE := 40.0
const EM := 0.018                           # font size, a set fraction of the view height (~19 px at 1080)
const GUILD_SCALE := 0.8
const FRIENDLY := Color8(175, 223, 208)
const OUTLINE := Color(0.02, 0.04, 0.02, 0.9)
const OCCLUDERS := ZoneLoader.LAYER_WALL | ZoneLoader.LAYER_FLOOR | ZoneLoader.LAYER_SCENERY
const RAYS_PER_FRAME := 24                  # wall checks a frame, shared by the names shown
const RECHECK_MS := 120                     # a shown name's wall check is at most this old

var manager: NpcManager
var _font: Font
var _layer: CanvasLayer
var _canvas: Control
var _names: Array = []                      # this frame's names: [dist, Vector2 anchor, name, guild, colour]
var _size := 8
var _ray := PhysicsRayQueryParameters3D.new()
var _rr := 0                                # round robin over the shown names for the wall checks


func _ready() -> void:
	_font = UiArt.font(true, "names")
	_ray.collision_mask = OCCLUDERS
	_layer = CanvasLayer.new()
	_layer.layer = 1                        # over the world, under the WoW-style plates (added after) and the windows
	add_child(_layer)
	_canvas = Control.new()
	_canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.draw.connect(_draw_names)
	_layer.add_child(_canvas)


func _process(_delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	_process_inner(_delta)
	_canvas.queue_redraw()
	Perf.proc_add("name plates", Time.get_ticks_usec() - t0)   # (the live log: process by part)


var _companion_names := true
var _group_oids := {}


func _process_inner(_delta: float) -> void:
	_names.clear()
	_companion_names = UiArt.bot_option("names_companions")
	_group_oids.clear()
	if Server.active:
		for m in Server.group_members:
			_group_oids[int(m.get("oid", 0))] = true
	var cam := get_viewport().get_camera_3d()
	if manager == null or cam == null or manager.player == null:
		return
	var vp := get_viewport().get_visible_rect().size
	_size = maxi(8, roundi(EM * vp.y * UiArt.text_scale("names")))   # (Options: its text size)
	var pp := manager.player.global_position
	var eye := cam.global_position
	var space := cam.get_world_3d().direct_space_state
	var now := Time.get_ticks_msec()
	var shown: Array = []
	for i in manager.active:
		var n: Npc = manager.active[i]
		if not is_instance_valid(n):
			continue
		var targeted := n == manager.target
		var d := Vector2(n.global_position.x - pp.x, n.global_position.z - pp.z).length()
		var show := n.visible and n.state.alive and (targeted or (d <= NAME_RANGE
				and not int(n.spawn.flags) & (Npc.FLAG_DONTSHOWNAME | Npc.FLAG_CANTTARGET)))
		# Options > COMPANION NAMES in the server's game: your companions are your group's other members (owner
		# 2026-10-15 UI audit - the toggle only reached the offline bots)
		if show and not targeted and not _companion_names and _group_oids.has(int(n.spawn.get("oid", 0))):
			show = false
		if show and bool(n.get_meta("hp_plate", false)):     # a nameplate (HealthPlates) shows the name already
			show = false
		if not show:
			if n.has_meta("name_seen_at"):
				n.remove_meta("name_seen_at")             # (shown again later: checked again before it's drawn)
			continue
		var head := n.global_position + Vector3(0, n.height + 0.2, 0)
		if cam.is_position_behind(head):
			continue
		var at := cam.unproject_position(head)
		if at.x < -300 or at.y < -60 or at.x > vp.x + 300 or at.y > vp.y + 200:
			continue
		shown.append([n, head])
	# the wall checks: a name just come into view first (so it never shows through a wall for a frame), then the
	# oldest of the rest, round robin, up to the frame's budget
	var rays := 0
	for e in shown:
		var n: Npc = e[0]
		if not n.has_meta("name_seen_at"):
			_check(n, eye, e[1], space, now)
			rays += 1
	if shown.size() > 0:
		var k := 0
		while rays < RAYS_PER_FRAME and k < shown.size():
			var e: Array = shown[(_rr + k) % shown.size()]
			k += 1
			if now - int(e[0].get_meta("name_seen_at", 0)) >= RECHECK_MS:
				_check(e[0], eye, e[1], space, now)
				rays += 1
		_rr = (_rr + k) % shown.size()
	for e in shown:
		var n: Npc = e[0]
		if bool(n.get_meta("name_hidden", false)):
			continue
		var col: Color = Color.WHITE if n == manager.target else (FRIENDLY if n.is_friendly() else n.con_color(PlayerData.level))
		var guild := String(n.spawn.get("guild", ""))
		_names.append([eye.distance_squared_to(e[1]), cam.unproject_position(e[1]), String(n.spawn.name),
				"<%s>" % guild if guild != "" else "", col])
	_names.sort_custom(func(a, b): return float(a[0]) > float(b[0]))   # farther first: the near ones on top


## Is a wall, the ground or a building between the camera and this name?
func _check(n: Npc, eye: Vector3, head: Vector3, space: PhysicsDirectSpaceState3D, now: int) -> void:
	var to := head
	var gap := head - eye
	if gap.length() > 0.5:
		to = head - gap.normalized() * 0.35                 # (not the ledge or the floor the name hangs over)
	_ray.from = eye
	_ray.to = to
	n.set_meta("name_hidden", not space.intersect_ray(_ray).is_empty())
	n.set_meta("name_seen_at", now)


## The name over the guild line, centred on the head and set on whole pixels (no smear as they move).
func _draw_names() -> void:
	var guild_px := roundi(_size * GUILD_SCALE)
	for e in _names:
		var at: Vector2 = e[1]
		var bottom := roundf(at.y)
		var col: Color = e[4]
		if String(e[3]) != "":
			bottom = _line(String(e[3]), roundf(at.x), bottom, guild_px, col)
		_line(String(e[2]), roundf(at.x), bottom, _size, col)


## One line of text whose box sits on `bottom`; returns the top of its box (where the line over it sits).
func _line(text: String, cx: float, bottom: float, px: int, col: Color) -> float:
	var w := _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, px).x
	var base := Vector2(roundf(cx - w * 0.5), bottom - roundf(_font.get_descent(px)))
	var outline := maxi(3, roundi(px * 0.18))
	var oc := OUTLINE
	oc.a *= col.a
	_canvas.draw_string_outline(_font, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, px, outline, oc)
	_canvas.draw_string(_font, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, px, col)
	return bottom - roundf(_font.get_height(px))
