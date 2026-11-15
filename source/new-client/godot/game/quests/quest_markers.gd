class_name QuestMarkers
extends Control
## Quest markers (owner 2026-10-09, a modern addition): a coloured circle on the ground under an NPC's feet -
##   yellow  a quest you can take now (QuestEngine.qualifies: your level, class, race, quests done);
##   green   your current step ends at them (talk to / hand in / finish there);
##   orange  they gave you a quest that is still in progress elsewhere.
## A flat swirling O drawn by a small shader just above the floor (a decal drew a solid square in the owner's game),
## zone-wide for every spawn, re-judged every 2 s and following the NPC as it walks. The same colours mark them on the map window, with the classic step markers in red.

const RANGE_M := 600.0
const COLORS := {"available": Color(1.0, 0.85, 0.15), "turnin": Color(0.3, 1.0, 0.35), "progress": Color(1.0, 0.55, 0.1),
		"task": Color(0.8, 0.35, 1.0), "event": Color(0.35, 0.85, 1.0)}
const MAP_KIND := {"available": "!", "turnin": "?", "progress": "o", "task": "task", "event": "event"}
## "event" (cyan, owner 2026-11-02): someone who'd lead you into a dynamic event if you talk to them (EventTracker.givers).
## "task" (violet, a QOL addition - 1.65 EXCEPTIONS MADE.txt): your /task's target - the kill task's monsters around
## the spot the guard meant, then the guard to return to; a delivery task's receiver. The original gave a direction.

var viewer: Node
var _marked := {}                         # NpcState -> "available" / "turnin" / "progress"
var _decals := {}                         # NpcState -> its ring (MeshInstance3D)
var _holder: Node3D
var _tick := 0.0


func setup(v: Node) -> void:
	viewer = v
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_holder = Node3D.new()
	_holder.name = "QuestCircles"
	_holder.set_meta("fixed_origin", true)            # its rings follow the NPCs' (already shifted) positions: a border
	(viewer as Node).add_child(_holder)               # crossing must not move it too (owner 2026-10-11: quests gone)
	PlayerData.quests_changed.connect(func(): _tick = 0.0)


const RING_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix, fog_disabled;
uniform vec4 color : source_color = vec4(1.0, 0.85, 0.15, 1.0);
void fragment() {
	// an O with an empty middle: a band of three bright arcs, each fading toward its tail, turning (the swirl)
	vec2 v = UV * 2.0 - 1.0;
	float d = length(v);
	float band = clamp(1.0 - abs(d - 0.78) / 0.14, 0.0, 1.0);
	float ang = fract((atan(v.y, v.x) / 6.2831853 + TIME * 0.28) * 3.0);
	float arc = 0.3 + 0.7 * pow(ang, 1.6);
	ALBEDO = color.rgb;
	ALPHA = band * arc * color.a;
}
"""
static var _ring_shader: Shader
var _mats := {}                           # kind -> ShaderMaterial


func _ring_material(kind: String) -> ShaderMaterial:
	if not _mats.has(kind):
		if _ring_shader == null:
			_ring_shader = Shader.new()
			_ring_shader.code = RING_SHADER
		var m := ShaderMaterial.new()
		m.shader = _ring_shader
		m.set_shader_parameter("color", COLORS[kind])
		_mats[kind] = m
	return _mats[kind]


func _process(delta: float) -> void:
	var t_live := Time.get_ticks_usec()
	_process_timed(delta)
	Perf.proc_add("quest markers", Time.get_ticks_usec() - t_live)   # (the live log: process by part, and its hitch lines)


func _process_timed(delta: float) -> void:
	_tick -= delta
	if _tick <= 0.0:
		_tick = 2.0
		_rebuild()
	var cam := get_viewport().get_camera_3d()
	for st in _decals:
		var s: NpcState = st
		var ring: MeshInstance3D = _decals[st]
		ring.position = s.pos + Vector3(0, 0.06, 0)              # just above the floor the NPC stands on
		ring.visible = s.alive and (cam == null or cam.global_position.distance_to(s.pos) < RANGE_M)


func _rebuild() -> void:
	_marked.clear()
	if Server.active:
		_server_rebuild()
		return
	_sync_decals()                       # (no server: no quests - the old standalone game's markers went 2026-11-15)


## 0.36c: the server's quest indicators (ServerWorld: NPCCreate flags / the quest effect) - available yellow, finish
## green, pending (a quest of theirs in progress) orange; a lesson / lore NPC as available.
const SERVER_KIND := {1: "available", 2: "turnin", 4: "available", 8: "available", 16: "progress"}


func _server_rebuild() -> void:
	var marks := []
	if viewer and viewer.npcs:
		for s in viewer.npcs.states:
			var st: NpcState = s
			var k: String = SERVER_KIND.get(int(st.spawn.get("quest", 0)), "")
			if k == "" and String(st.spawn.get("name", "")) in preload("res://game/ui/event_tracker.gd").givers():
				k = "event"
			if st.alive and k != "":
				_marked[st] = k
				marks.append({"at": Vector2(st.pos.x, st.pos.z), "kind": MAP_KIND[k]})
	if viewer and viewer.ui and viewer.ui.map_window:
		viewer.ui.map_window.marks = marks + Server.quest_map_marks()
	_sync_decals()


func _sync_decals() -> void:
	for st in _decals.keys():
		if not _marked.has(st):
			(_decals[st] as Node).queue_free()
			_decals.erase(st)
	for st in _marked:
		var ring: MeshInstance3D = _decals.get(st)
		if ring == null:
			ring = MeshInstance3D.new()
			var quad := PlaneMesh.new()
			quad.size = Vector2(1.5, 1.5)
			ring.mesh = quad
			ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_holder.add_child(ring)
			_decals[st] = ring
		ring.material_override = _ring_material(String(_marked[st]))
