# (no class_name: preloaded where used - new scripts are not in the class cache)
extends Node
## Light watch (owner 2026-11-15, the "exposure glitch": the picture's brightness stuttering in and out, too brief to
## catch on video, in the middle of zones as well as at their borders). Twice a second the finished picture is
## copied back from the graphics card without waiting for it (texture_get_data_async: no stall) and its brightness
## measured on a 64 x 36 grid. When it jumps while the camera holds still - so not a turn toward the sky or a cloak
## filling the screen - the jump is written to user://light_watch.log with what the lighting was doing (the zone's
## look and its blend, ambient and sun light, exposure, bloom, haze, storm, lightning) over the seconds before, and
## the pictures before and after are saved beside it (user://light_watch/). /lightlog writes the same on demand: type
## it just after you see a flicker (the last 30 s are kept).

const SAMPLE_S := 0.5
const KEEP := 1800                               # frames of lighting values kept (about 30 s)
const JUMP := 0.10                               # a 10% change of the whole picture's brightness in one sample
const STILL_DEG := 4.0                           # the camera turned less than this between the samples
const STILL_M := 1.0                             # and moved less than this
const MAX_REPORTS := 20                          # per session (a storm's lightning is not 200 reports)

var sky: SkySystem
var _rows: Array = []                            # per frame: [msec, values ...] - a ring of KEEP
var _head := 0
var _next := 0.0
var _pending := false
var _last := {}                                  # the previous sample: lum, yaw, pitch, pos, data, w, h, fmt, msec
var _reports := 0
var _off := false
var _born := 0                                   # (no reports in the first 10 s of a world: the loading screen going)
static var _instance: Node

const COLS := ["zone", "look_mix", "ambient", "sun", "exposure", "glow", "haze", "storm", "flash", "ae_scale",
		"yaw", "pitch", "x", "y", "z"]


func _ready() -> void:
	_instance = self
	_born = Time.get_ticks_msec()
	process_priority = 1000                      # (after the sky has set this frame's light)


static func report_now(why := "asked for (/lightlog)") -> String:
	if _instance == null:
		return "The light watch is not running (Remastered Lighting only)."
	return _instance._write(why, {}, {})


func _process(delta: float) -> void:
	if sky == null or not is_instance_valid(sky) or not sky.remastered or sky.environment == null:
		return
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var env := sky.environment
	var rot := cam.global_rotation
	var p := cam.global_position
	var row := [Time.get_ticks_msec(), int(sky.zone.info.get("id", -1)) if sky.zone else -1, SkySystem._look_mix,
			env.ambient_light_energy, sky.sun.light_energy if sky.sun else 0.0, env.tonemap_exposure, env.glow_intensity,
			env.volumetric_fog_density, sky.storm, float(sky.get("_flash")), SkySystem._t("aescale", 0.25),
			rad_to_deg(rot.y), rad_to_deg(rot.x), p.x, p.y, p.z]
	if _rows.size() < KEEP:
		_rows.append(row)
	else:
		_rows[_head] = row
		_head = (_head + 1) % KEEP
	if _off:
		return
	_next -= delta
	if _next > 0.0 or _pending:
		return
	_next = SAMPLE_S
	var tex := get_viewport().get_texture()
	if tex == null:
		return
	var rid := RenderingServer.texture_get_rd_texture(tex.get_rid())
	if not rid.is_valid():
		_off = true
		return
	_pending = true
	var at := {"yaw": rad_to_deg(rot.y), "pitch": rad_to_deg(rot.x), "pos": p, "msec": Time.get_ticks_msec()}
	RenderingServer.call_on_render_thread(func():
		var rd := RenderingServer.get_rendering_device()
		var f := rd.texture_get_format(rid) if rd else null
		if rd == null or f == null:
			_failed.call_deferred()
			return
		at.w = f.width
		at.h = f.height
		at.fmt = f.format
		if rd.texture_get_data_async(rid, 0, func(data: PackedByteArray): _arrived.call_deferred(data, at)) != OK:
			_failed.call_deferred())


func _failed() -> void:
	_pending = false
	_off = true
	push_warning("light watch: the picture could not be read back - off for this session")


## Brightness of the picture on a 64 x 36 grid (8-bit RGBA / BGRA only: anything else turns the watch off).
func _arrived(data: PackedByteArray, at: Dictionary) -> void:
	_pending = false
	var w := int(at.w)
	var h := int(at.h)
	var fmt := int(at.fmt)
	var bgra := fmt in [RenderingDevice.DATA_FORMAT_B8G8R8A8_UNORM, RenderingDevice.DATA_FORMAT_B8G8R8A8_SRGB]
	if not (bgra or fmt in [RenderingDevice.DATA_FORMAT_R8G8B8A8_UNORM, RenderingDevice.DATA_FORMAT_R8G8B8A8_SRGB]) \
			or data.size() < w * h * 4:
		_off = true
		push_warning("light watch: picture format %d not read - off for this session" % fmt)
		return
	var sum := 0.0
	for gy in 36:
		var row := (int((gy + 0.5) * h / 36.0)) * w * 4
		for gx in 64:
			var i := row + int((gx + 0.5) * w / 64.0) * 4
			var r := data[i + 2] if bgra else data[i]
			var b := data[i] if bgra else data[i + 2]
			sum += 0.2126 * r + 0.7152 * data[i + 1] + 0.0722 * b
	at.lum = sum / (64.0 * 36.0 * 255.0)
	if _last.is_empty():
		print("[light watch] reading the picture back: %d x %d, format %d, brightness %.3f" % [w, h, fmt, float(at.lum)])
	at.data = data
	at.bgra = bgra
	if not _last.is_empty() and _reports < MAX_REPORTS and Time.get_ticks_msec() - _born > 10000:
		var prev: Dictionary = _last
		var turned := maxf(absf(angle_difference(deg_to_rad(float(at.yaw)), deg_to_rad(float(prev.yaw)))),
				absf(deg_to_rad(float(at.pitch) - float(prev.pitch))))
		var moved := (at.pos as Vector3).distance_to(prev.pos)
		var change := (float(at.lum) - float(prev.lum)) / maxf(float(prev.lum), 0.02)
		if absf(change) >= JUMP and rad_to_deg(turned) < STILL_DEG and moved < STILL_M:
			_write("the picture went %s by %d%% in %d ms with the camera still" % ["brighter" if change > 0 else "darker",
					roundi(absf(change) * 100.0), int(at.msec) - int(prev.msec)], prev, at)
	_last = at


## The report: the lighting values over the last seconds (each tenth frame, every frame in the last second) and
## the two pictures. Returns where it went.
func _write(why: String, before: Dictionary, after: Dictionary) -> String:
	_reports += 1
	var stamp := Time.get_datetime_string_from_system().replace(":", "-")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://light_watch"))
	var path := "user://light_watch.log"
	var f := FileAccess.open(path, FileAccess.READ_WRITE) if FileAccess.file_exists(path) else FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return "Could not write user://light_watch.log."
	f.seek_end()
	f.store_line("==== %s  %s" % [stamp, why])
	if not before.is_empty():
		f.store_line("brightness %.3f -> %.3f" % [float(before.lum), float(after.lum)])
	f.store_line("ms_ago " + " ".join(COLS))
	var now := Time.get_ticks_msec()
	var n := _rows.size()
	for k in n:
		var r: Array = _rows[(_head + k) % n]
		var ago := now - int(r[0])
		if ago > 1000 and k % 10 != 0:
			continue
		var cells := ["%6d" % ago]
		for v in r.slice(1):
			cells.append(("%.3f" % v) if v is float else str(v))
		f.store_line(" ".join(cells))
	f.close()
	var shots := []
	for pair in [["before", before], ["after", after], ["now", _last if before.is_empty() else {}]]:
		var s: Dictionary = pair[1]
		if s.is_empty() or not s.has("data"):
			continue
		var file := "user://light_watch/%s_%s.jpg" % [stamp, pair[0]]
		shots.append(file)
		var data: PackedByteArray = s.data
		var w := int(s.w)
		var h := int(s.h)
		var bgra := bool(s.bgra)
		WorkerThreadPool.add_task(func():
			var d := data.duplicate()
			if bgra:
				for i in range(0, d.size() - 3, 4):
					var t := d[i]
					d[i] = d[i + 2]
					d[i + 2] = t
			var img := Image.create_from_data(w, h, false, Image.FORMAT_RGBA8, d)
			img.resize(w / 2, h / 2)
			img.save_jpg(ProjectSettings.globalize_path(file), 0.85), true, "light watch picture")
	return "Light report written to %s%s." % [ProjectSettings.globalize_path(path),
			(" with pictures in " + ProjectSettings.globalize_path("user://light_watch")) if not shots.is_empty() else ""]
