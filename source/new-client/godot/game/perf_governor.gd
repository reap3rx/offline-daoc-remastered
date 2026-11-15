extends Node
## Autoload "Perf": holds the frame rate on a target by trading detail for speed as the scene gets busy (owner
## 2026-10-10: full-quality textures and animation in a quiet town like Connla with 10-20 bots, much more aggressive
## savings in a dragon raid with 200-300 bots casting around you; 40+ fps). Every half second the smoothed frame
## time is compared with the target and one "load" level (0 = full detail .. 1 = most saving) moves up fast when
## below target and down slowly when comfortably above (hysteresis, no flicker). The level drives:
##   - how far NPCs animate every frame (Npc._animate_lod distances x anim_range),
##   - NPC shadow distance (npc_shadow_m),
##   - spell / effect particle density (particle_ratio, GPUParticles3D.amount_ratio),
##   - texture detail (the viewport's mipmap bias: sharp skins up close in town, softer in a crowd).
## No upscaler (owner 2026-10-10: native only for now).
## Two dials, not one (owner 2026-10-11: "if the gpu isn't under load why smudge my textures?"): the graphics card's own
## time per frame is measured (RenderingServer's GPU timer). When the frame is slow but the card finishes well inside
## it, the CPU is the limit - only the CPU savings rise (animation, skeleton budget, effect count, sounds, character
## shadow distance - each caster is drawn again per shadow split); texture sharpness and particles stay full. When the card is the limit, the GPU savings rise. A busy scene
## that is slow on both gets both.

const TARGETS := [0, 30, 40, 50, 60, 75, 90, 120, 144]

var target_fps := 60                       # 0 = off: brute force, no culling or level of detail anywhere
var brute := false                         # target_fps == 0 (read by Npc / NpcManager / SpellFx)
var level := 0.0                           # the larger of the two dials (tests read it)
var cpu_level := 0.0                       # 0 full detail .. 1 most saving: what costs the CPU
var gpu_level := 0.0                       # ...and what costs the graphics card
var fps := 60.0                            # smoothed
var gpu_ms := 0.0                          # the graphics card's time a frame (smoothed)

# what the level means right now (read by Npc / SpellFx every so often)
var anim_range := 1.0                      # x the NPC animation LOD distances
var npc_shadow_m := 60.0                   # NPCs beyond this cast no shadow
var anim_budget := 60                      # skeleton updates per frame beyond 8 m (Npc._animate_lod)
var particle_ratio := 1.0
var fx_range := 80.0                       # spell effects beyond this (metres from the camera) are not drawn
var max_effects := 300                     # spell effects alive at once (the nearest are kept)
var gather_range := 80.0                   # other casters' hand glows (the long-lived effects) only this close
var voices := 48                           # sounds at once (CharacterSounds)
# the characters themselves (owner 2026-11-14: "some sort of solution to disable some of these expensive effects on
# characters when many are in the screen, up to the point where the player is the only one"; measured: 0.37 ms a
# figure a frame - 98 in view ran at 24 fps with every other saving already at its most). The views on screen are
# ranked by distance (NpcManager: your target and group first); as the CPU level rises, from the farthest in:
const FULL_N := 12                         # the nearest this many keep everything, whatever the load
const NO_LIMIT := 1 << 20
var sway_n := NO_LIMIT                     # ranks from this on lose the sway, cloak / gear swing, hair, feet, look
var pose_from := NO_LIMIT                  # ranks from this on are posed less often ...
var pose_step := 1.0 / 30.0                # ... this far apart (seconds: 30 down to 20 poses a second)

var gpu_vendor := ""
var gpu_name := ""
var _t := 0.0
var _cpu_good := 0.0
var _gpu_good := 0.0
var _frame_ms := 16.7
var _gpu_on := false
var _gpu_left := 0.0


func _ready() -> void:
	gpu_vendor = RenderingServer.get_video_adapter_vendor()
	gpu_name = RenderingServer.get_video_adapter_name()
	load_settings()


func load_settings() -> void:
	var cfg := UiArt.load_settings()
	target_fps = int(cfg.get_value("performance", "target_fps", 60))
	_apply()


func set_option(key: String, value) -> void:
	match key:
		"target_fps": target_fps = int(value)
	_apply()


func _process(delta: float) -> void:
	_proc_frames += 1
	# the frame that just ended (its parts and steps were gathered since this ran last), by the clock: the engine's
	# delta stops growing at eight physics ticks (a 308 ms frame came as 139)
	var now_us := Time.get_ticks_usec()
	var real := (now_us - _hitch_at) / 1000000.0 if _hitch_at > 0 else delta
	_hitch_at = now_us
	_h_process = _phase_process                    # (the frame that just ended: its phases)
	_h_physics = _phase_physics
	_phase_process = 0
	_phase_physics = 0
	if real * 1000.0 >= HITCH_MS and Server.playing:
		_hitch(real)
	_hparts.clear()
	_notes.clear()
	_dms.clear()
	_frame_ms = lerpf(_frame_ms, delta * 1000.0, 0.1)
	var vp := get_viewport()
	if vp and not _gpu_on:
		RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
		_gpu_on = true
	_gpu_left -= delta
	if vp and _gpu_left <= 0.0:
		# once a second: each read makes the CPU wait for the render thread (Godot warns of it every frame)
		_gpu_left = 1.0
		var g := RenderingServer.viewport_get_measured_render_time_gpu(vp.get_viewport_rid())
		if g > 0.0:
			gpu_ms = g if gpu_ms <= 0.0 else lerpf(gpu_ms, g, 0.5)
	_t += delta
	_log_t += delta
	_phys_max = maxf(_phys_max, Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0)
	_proc_max = maxf(_proc_max, Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
	_slow = _slow + 1 if delta > 0.05 else _slow
	if _log_t >= 2.0:
		_log_t = 0.0
		_live_log()
	if _t < 0.5:
		return
	_t = 0.0
	fps = 1000.0 / maxf(_frame_ms, 0.1)
	if target_fps <= 0:
		if level != 0.0 or cpu_level != 0.0 or gpu_level != 0.0:
			cpu_level = 0.0
			gpu_level = 0.0
			level = 0.0
			_apply()
		return
	var target_ms := 1000.0 / target_fps
	var behind := fps < target_fps * 0.95
	# whose fault is a slow frame: the card is the limit when its own work nearly fills the frame or the target
	var gpu_bound := gpu_ms > 0.0 and (gpu_ms >= _frame_ms * 0.85 or gpu_ms >= target_ms * 0.9)
	var cpu_bound := gpu_ms <= 0.0 or gpu_ms < _frame_ms * 0.85            # (no GPU timer: treat as the CPU)
	var step := 0.15 if fps < target_fps * 0.75 else 0.06
	var changed := false
	if behind and cpu_bound:
		cpu_level = minf(cpu_level + step, 1.0)
		_cpu_good = 0.0
		changed = true
	elif cpu_level > 0.0 and (fps > target_fps * 1.2 or not behind):
		_cpu_good += 0.5
		if _cpu_good >= 3.0 and fps > target_fps * 1.2:
			cpu_level = maxf(cpu_level - 0.04, 0.0)
			changed = true
	if behind and gpu_bound:
		gpu_level = minf(gpu_level + step, 1.0)
		_gpu_good = 0.0
		changed = true
	elif gpu_level > 0.0:
		# the card has room (its work well inside the target): give its detail back - even while the frame is slow
		# for another reason; textures never stay smudged for a CPU-bound crowd
		var roomy := gpu_ms > 0.0 and gpu_ms < target_ms * 0.6
		if roomy or fps > target_fps * 1.2:
			_gpu_good += 0.5
			if _gpu_good >= (1.5 if roomy else 3.0):
				gpu_level = maxf(gpu_level - (0.08 if roomy else 0.04), 0.0)
				changed = true
		else:
			_gpu_good = 0.0
	if changed:
		level = maxf(cpu_level, gpu_level)
		_apply()


## Level 0 is full quality (a quiet town keeps every effect, shadow and animation); the cuts grow drastic toward
## level 1 (owner 2026-10-10: 60 fps matters more than detail in a 200-300 bot raid - far spell effects off, the
## nearest kept, distant bots animating slowly).
## Live performance log (owner 2026-10-11: "check my live performance tracking" - there was none): every 2 s one line in
## user://perf_live.log - fps, the frame's script process and physics times (worst in the 2 s), frames over 50 ms,
## the graphics card's time, draw calls, objects / nodes, video memory, the detail levels, the NPCs drawn and the bots
## run in this game. Kept short (rolled over at 2 MB).
var _log_t := 0.0
var _phys := {}                                  # part -> microseconds in physics ticks since the last line
var _phys_ticks := 0


func phys_add(part: String, usec: int) -> void:
	_phys[part] = int(_phys.get(part, 0)) + usec
	_hparts["physics " + part] = int(_hparts.get("physics " + part, 0)) + usec
	frame_parts["phys " + part] = int(frame_parts.get("phys " + part, 0)) + usec


## The frame's main-thread time by part (owner 2026-10-14: Tir na Nog 40 fps CPU-bound with 200 NPCs - which part?):
## the live log's "process a frame by part"; what's left of the process time is everything else (the NPC views'
## threaded posing waited on, engine work). Main thread only.
var _proc := {}
var _proc_frames := 0


var _proc_peak := {}                             # part -> its longest single call since the last line (a hitch)


var frame_parts := {}                            # the same, since a probe last took it (tests/walk_perf: per slow frame)


func proc_add(part: String, usec: int) -> void:
	_proc[part] = int(_proc.get(part, 0)) + usec
	frame_parts[part] = int(frame_parts.get(part, 0)) + usec
	_hparts[part] = int(_hparts.get(part, 0)) + usec
	if dmark_on:
		_dm.call_deferred(part)
	if usec > int(_proc_peak.get(part, 0)):
		_proc_peak[part] = usec


## Hitches by name (the health check, 2026-11-14: a frame of 100 ms or longer about 70 times an hour in play, a fifth
## of them with no cause in the log). Every long single step on the main thread is noted with what it was
## (note_us: a view's figure, a packet, a zone placed ...); a frame that took HITCH_MS or longer writes one "[hitch]"
## line to the live log: its length, the parts and steps that ran in it, what is left unexplained, and the shader
## pipelines and scene nodes that came since the last line.
const HITCH_MS := 60.0
const NOTE_US := 2500
var _hparts := {}                                # this frame's parts (proc_add)
var _notes: Array = []                           # this frame's long steps: [label, usec]
var _hitch_at := 0                               # when the last frame began (ticks usec)
var _h_process := 0
var _hitch_vram := 0.0
var _h_physics := 0
var _hitch_lines := 0                            # written since the last live line (never a flood)
var _hitch_nodes := 0.0
var _hitch_pipes := -1
var hitches: Array = []                          # the last ones, for probes (tests): [ms, text]


## What the worker threads were given lately (a view's files, a zone to build): a frame can wait on the graphics card
## taking what they loaded, with nothing of the frame's own to show for it.
var _bg: Array = []                              # [msec, label]

func background(label: String) -> void:
	_bg.append([Time.get_ticks_msec(), label])
	if _bg.size() > 12:
		_bg.pop_front()


func note_us(label: String, usec: int) -> void:
	if usec >= NOTE_US and _notes.size() < 24:
		_notes.append([label, usec])


## The same, timed from `since` (Time.get_ticks_usec()); returns now, for the next step.
func note(label: String, since: int) -> int:
	var now := Time.get_ticks_usec()
	note_us(label, now - since)
	return now


## Where a frame's time went, by the engine's own phases: a node that runs last in each (PerfTail) marks their ends.
## process = every node's _process; physics = the physics ticks; the rest = drawing, timers, signals, waiting.
class PerfTail extends Node:
	var perf: Node
	func _process(_d: float) -> void:
		perf.set("_phase_process", Time.get_ticks_usec() - int(perf.get("_hitch_at")))
		perf.set("_t_tail_proc", Time.get_ticks_usec())
		perf.set("_t_first_physf", 0)
		perf.call_deferred("_on_deferred")
	func _physics_process(_d: float) -> void:
		perf.set("_phase_physics", int(perf.get("_phase_physics")) + Time.get_ticks_usec() - int(perf.get("_phys_at")))
		perf.set("_t_tail_phys", Time.get_ticks_usec())

# the gaps between the phases (what "rest" is made of): after the nodes' process until the next frame's first physics
# tick (timers, deferred calls, the draw); from the last physics tick's nodes to the process signal (the physics step
# and its signals); from the process signal to the first node (coroutines that waited for the frame)
var _t_tail_proc := 0
var _t_first_physf := 0
var _t_tail_phys := 0
var _t_procf := 0

## --dmark (a test): a deferred marker after every timed part, so a long deferred call shows between two of them.
var dmark_on := OS.get_cmdline_user_args().has("--dmark")
var _dms: Array = []

func _dm(part: String) -> void:
	_dms.append([part, Time.get_ticks_usec()])

var _t_deferred := 0
var _t_predraw := 0
var _t_postdraw := 0

func _on_deferred() -> void:
	_t_deferred = Time.get_ticks_usec()

func _on_pre_draw() -> void:
	_t_predraw = Time.get_ticks_usec()

func _on_post_draw() -> void:
	_t_postdraw = Time.get_ticks_usec()


func _on_physics_frame() -> void:
	if _t_first_physf == 0:
		_t_first_physf = Time.get_ticks_usec()

func _on_process_frame() -> void:
	_t_procf = Time.get_ticks_usec()

var _phase_process := 0
var _phase_physics := 0
var _phys_at := 0
var _tail: Node = null


func _phase_tick() -> void:
	_phys_at = Time.get_ticks_usec()
	if _tail == null:
		_tail = PerfTail.new()
		_tail.set("perf", self)
		_tail.process_priority = 1 << 20
		_tail.process_physics_priority = 1 << 20
		get_tree().root.add_child.call_deferred(_tail)
		get_tree().physics_frame.connect(_on_physics_frame)
		get_tree().process_frame.connect(_on_process_frame)
		RenderingServer.frame_pre_draw.connect(_on_pre_draw)
		RenderingServer.frame_post_draw.connect(_on_post_draw)


func _hitch(delta: float) -> void:
	var ms := delta * 1000.0
	var known := 0
	var parts := ""
	var keys := _hparts.keys()
	keys.sort_custom(func(a, b): return int(_hparts[a]) > int(_hparts[b]))
	for k in keys:
		if String(k).begins_with("slow packet"):
			continue                                   # (inside "server packets")
		known += int(_hparts[k])
		if int(_hparts[k]) >= 1000:
			parts += "%s %.0f, " % [k, int(_hparts[k]) / 1000.0]
	var steps := ""
	_notes.sort_custom(func(a, b): return int(a[1]) > int(b[1]))
	for e in _notes:
		steps += "%s %.0f, " % [e[0], int(e[1]) / 1000.0]
	var pipes := 0
	for k in [RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_DRAW, RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_SPECIALIZATION,
			RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_SURFACE, RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_MESH]:
		pipes += int(RenderingServer.get_rendering_info(k))
	var nodes := Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	# (the engine's own count of the frame: scripts and nodes in process, the physics ticks; what is in neither was
	# spent drawing or waiting for the render thread - a shader being compiled)
	var text := "%.0f ms | parts: %s| steps: %s| unexplained %.0f ms | phases: process %.0f physics %.0f rest %.0f | pipelines +%d | nodes %+d" % [ms,
			parts if parts != "" else "none ", steps if steps != "" else "none ",
			maxf(0.0, ms - known / 1000.0 - 1000.0 / maxf(fps, 1.0)),
			_h_process / 1000.0, _h_physics / 1000.0, maxf(0.0, ms - (_h_process + _h_physics) / 1000.0),
			(pipes - _hitch_pipes) if _hitch_pipes >= 0 else 0, int(nodes - _hitch_nodes)]
	if _t_tail_proc > 0 and _t_procf > _t_tail_proc:
		var first_next := _t_first_physf if _t_first_physf > _t_tail_proc else _t_procf
		text += " | gaps: after process (draw, timers, deferred) %.0f, physics step and signals %.0f, before process (coroutines) %.0f" % [
				(first_next - _t_tail_proc) / 1000.0,
				(_t_procf - _t_tail_phys) / 1000.0 if _t_tail_phys > _t_tail_proc else 0.0,
				(Time.get_ticks_usec() - _t_procf) / 1000.0]
	if _t_deferred > _t_tail_proc and _t_predraw > _t_tail_proc and _t_postdraw > _t_tail_proc:
		text += " | after process: deferred calls %.0f, timers / tweens / freed nodes %.0f, the draw %.0f, after the draw %.0f" % [
				(_t_deferred - _t_tail_proc) / 1000.0, (_t_predraw - _t_deferred) / 1000.0, (_t_postdraw - _t_predraw) / 1000.0,
				((_t_first_physf if _t_first_physf > _t_postdraw else _t_procf) - _t_postdraw) / 1000.0]
	if dmark_on and _dms.size() > 0:
		var prev_t := _t_tail_proc
		var prev_l := "the end of process"
		var worst := 0
		var where := ""
		for e in _dms:
			if int(e[1]) - prev_t > worst:
				worst = int(e[1]) - prev_t
				where = "after '%s' was queued and before '%s'" % [prev_l, e[0]]
			prev_t = int(e[1])
			prev_l = String(e[0])
		text += " | longest deferred stretch %.0f ms: %s" % [worst / 1000.0, where]
	text += " | vram %+d MB" % int((Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) - _hitch_vram) / 1048576.0)
	var lately := ""
	var now_ms := Time.get_ticks_msec()
	for e in _bg:
		if now_ms - int(e[0]) < 20000:
			lately += "%s (%d ms ago), " % [e[1], now_ms - int(e[0])]
	if lately != "":
		text += " | workers: " + lately
	_hitch_pipes = pipes
	_hitch_nodes = nodes
	hitches.append([ms, text])
	if hitches.size() > 200:
		hitches.pop_front()
	_hitch_lines += 1
	if _hitch_lines > 6:
		return
	var path := "user://perf_live.log"
	var f := FileAccess.open(path, FileAccess.READ_WRITE) if FileAccess.file_exists(path) else FileAccess.open(path, FileAccess.WRITE)
	if f:
		f.seek_end()
		f.store_line("[hitch] %s %s" % [Time.get_time_string_from_system(), text])
		f.close()


func _physics_process(_delta: float) -> void:
	_phase_tick()
	_phys_ticks += 1
var _phys_max := 0.0
var _proc_max := 0.0
var _slow := 0


func _live_log() -> void:
	var path := "user://perf_live.log"
	var f: FileAccess
	if FileAccess.file_exists(path) and FileAccess.open(path, FileAccess.READ).get_length() > 2_000_000:
		DirAccess.rename_absolute(ProjectSettings.globalize_path(path), ProjectSettings.globalize_path("user://perf_live.old.log"))
	f = FileAccess.open(path, FileAccess.READ_WRITE) if FileAccess.file_exists(path) else FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return
	f.seek_end()
	var scene := get_tree().current_scene
	var npcs = scene.get("npcs") if scene else null
	var drawn: int = (npcs.active as Dictionary).size() if npcs is NpcManager else -1
	var bots := -1
	var parts := ""
	var n := maxi(_phys_ticks, 1)
	for k in _phys:
		parts += "%s %.2f, " % [k, int(_phys[k]) / 1000.0 / n]
	if WorldLink.bots and WorldLink.bots.has_method("BotCount"):
		bots = int(WorldLink.bots.call("BotCount"))
		parts += String(WorldLink.bots.call("PhysReport"))
	parts = "%d ticks: %s" % [_phys_ticks, parts]
	_phys.clear()
	_phys_ticks = 0
	var fparts := ""
	var fn := maxi(_proc_frames, 1)
	for k in _proc:
		fparts += "%s %.2f (peak %.0f), " % [k, int(_proc[k]) / 1000.0 / fn, int(_proc_peak.get(k, 0)) / 1000.0]
	parts += " | process a frame by part (ms): " + fparts
	_proc.clear()
	_proc_peak.clear()
	_proc_frames = 0
	_hitch_lines = 0
	_hitch_nodes = Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	_hitch_vram = Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)
	f.store_line(("[host] " if DisplayServer.get_name() == "headless" else "[game] ") + "%s fps %.0f | process %.1f max %.1f ms | physics %.1f max %.1f ms | slow frames %d | gpu %.1f ms | draws %d objs %d nodes %d | vram %d MB | cpu lvl %.2f gpu lvl %.2f | npcs drawn %d | bots %d" % [
		Time.get_time_string_from_system(), Engine.get_frames_per_second(),
		Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0, _proc_max,
		Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0, _phys_max, _slow, gpu_ms,
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		Performance.get_monitor(Performance.OBJECT_NODE_COUNT), Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
		cpu_level, gpu_level, drawn, bots] + _pipelines() + " | physics a tick by part (ms): " + parts)
	f.close()
	_phys_max = 0.0
	_proc_max = 0.0
	_slow = 0


## Shader pipelines the renderer had to build since the last line (owner 2026-10-28: Camelot stutters walking around
## - a frame waits while the render thread compiles one; the shader cache makes a second visit cheaper).
var _pipe_last := {}


func _pipelines() -> String:
	var out := ""
	for k in [["draw", RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_DRAW],
			["specialization", RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_SPECIALIZATION],
			["surface", RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_SURFACE],
			["mesh", RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_MESH]]:
		var n := int(RenderingServer.get_rendering_info(k[1]))
		var d := n - int(_pipe_last.get(k[0], n))
		_pipe_last[k[0]] = n
		if d > 0:
			out += " %s %d" % [k[0], d]
	return " | pipelines built:" + (out if out != "" else " none")


func _apply() -> void:
	brute = target_fps <= 0
	var c := cpu_level
	var g := gpu_level
	var both := maxf(c, g)                                  # effects cost both (scripts + particles)
	# the CPU's savings
	anim_range = lerpf(1.0, 0.15, c)
	anim_budget = int(lerpf(60.0, 8.0, c))
	voices = int(lerpf(48.0, 16.0, c))
	max_effects = int(lerpf(300.0, 30.0, sqrt(both)))
	fx_range = lerpf(80.0, 10.0, sqrt(both))
	gather_range = lerpf(80.0, 6.0, sqrt(both))
	npc_shadow_m = lerpf(60.0, 8.0, both)                   # shadows cost both: each caster drawn again per split
	# the polish goes first (level 0.1 - 0.5: from the 64th nearest in to the 12th), then the pose rate (0.35 - 0.7,
	# the same way, at 30 a second), then that rate falls to 20 (0.7 - 1)
	sway_n = NO_LIMIT if c < 0.1 else maxi(FULL_N, int(lerpf(64.0, FULL_N, clampf((c - 0.1) / 0.4, 0.0, 1.0))))
	pose_from = NO_LIMIT if c < 0.35 else maxi(FULL_N, int(lerpf(64.0, FULL_N, clampf((c - 0.35) / 0.35, 0.0, 1.0))))
	pose_step = 1.0 / lerpf(30.0, 20.0, clampf((c - 0.7) / 0.3, 0.0, 1.0))
	# the graphics card's savings only
	particle_ratio = lerpf(1.0, 0.25, g)
	var vp := get_viewport()
	if vp:
		vp.texture_mipmap_bias = lerpf(0.0, 1.5, g * g)      # gentle at first, steep under heavy load
