extends Node
## Hang and error-flood guard (claude 2026-11-17).
## A helper thread watches two things and closes the game if either goes wrong:
##  - the main loop stops ticking for HANG_SECONDS (the game is frozen), or
##  - errors pour in faster than FLOOD_ERRORS per 10 seconds (an error repeating endlessly).
## Before closing it notes why in user://logs/watchdog.txt and pops a short message.
## Off while a debugger is attached (a breakpoint would look like a hang).
## Test: --watchdog-test=hang or --watchdog-test=flood (with --watchdog-hang=N to shorten the wait).

const HANG_SECONDS := 90.0
const FLOOD_ERRORS := 20000


## Counts every error and warning the engine reports, from any thread.
class ErrorCounter extends Logger:
	var count := 0
	var last := ""
	var lock := Mutex.new()

	func _log_error(function: String, file: String, line: int, code: String, rationale: String, _editor_notify: bool, _error_type: int, _script_backtraces: Array[ScriptBacktrace]) -> void:
		lock.lock()
		count += 1
		if count % 500 == 1:
			last = "%s (%s:%d %s)" % [rationale if rationale != "" else code, file.get_file(), line, function]
		lock.unlock()

	func _log_message(_message: String, _error: bool) -> void:
		pass

	func take() -> Array:
		lock.lock()
		var r := [count, last]
		count = 0
		lock.unlock()
		return r

var _beat_ms: int = 0
var _running := true
var _thread: Thread
var _log_path := ""
var _counter: ErrorCounter
var _hang_ms := int(HANG_SECONDS * 1000.0)
var _test := ""
var _flood := FLOOD_ERRORS


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	process_priority = -1000
	_beat_ms = Time.get_ticks_msec()
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--watchdog-test="):
			_test = a.split("=", true, 1)[1]
		elif a.begins_with("--watchdog-hang="):
			_hang_ms = int(float(a.split("=", true, 1)[1]) * 1000.0)
		elif a.begins_with("--watchdog-flood="):
			_flood = int(a.split("=", true, 1)[1])
		elif a == "--no-watchdog":
			return
	if EngineDebugger.is_active() and _test == "":
		return
	_log_path = ProjectSettings.globalize_path(String(ProjectSettings.get_setting("debug/file_logging/log_path", "user://logs/godot.log")))
	_counter = ErrorCounter.new()
	OS.add_logger(_counter)
	_thread = Thread.new()
	_thread.start(_watch)
	if _test != "":
		get_tree().create_timer(3.0).timeout.connect(_run_test)


func _process(_d: float) -> void:
	_beat_ms = Time.get_ticks_msec()


func _exit_tree() -> void:
	_stop()


func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE:
		_stop()


func _stop() -> void:
	_running = false
	if _counter:
		OS.remove_logger(_counter)
		_counter = null
	if _thread and _thread.is_started():
		_thread.wait_to_finish()
	_thread = null


func _watch() -> void:
	var tick := 0
	while _running:
		OS.delay_msec(1000)
		if not _running:
			return
		var stalled := Time.get_ticks_msec() - _beat_ms
		if stalled > _hang_ms:
			_close("The game stopped responding for %d seconds." % (stalled / 1000))
			return
		tick += 1
		if tick % 10 == 0 and _counter:
			var got: Array = _counter.take()
			if int(got[0]) > _flood:
				_close("An error kept repeating (%d errors in 10 seconds; last: %s)." % [int(got[0]), String(got[1])])
				return


func _close(why: String) -> void:
	var stamp := Time.get_datetime_string_from_system(false, true)
	var note := ProjectSettings.globalize_path("user://logs/watchdog.txt")
	var f := FileAccess.open(note, FileAccess.READ_WRITE) if FileAccess.file_exists(note) else FileAccess.open(note, FileAccess.WRITE)
	if f:
		f.seek_end()
		f.store_line("%s  closed the game: %s  log: %s" % [stamp, why, _log_path])
		f.close()
	if OS.get_name() == "Windows" and _test != "flood-quiet" and _test != "hang-quiet":
		var msg := ("Offline DAoC closed itself. " + why + " Details are in " + note).replace("'", "''")
		OS.create_process("powershell.exe", ["-NoProfile", "-WindowStyle", "Hidden", "-Command",
			"Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('%s','Offline DAoC') | Out-Null" % msg])
	OS.kill(OS.get_process_id())


func _run_test() -> void:
	print("[watchdog] test ", _test, " hang_ms=", _hang_ms)
	if _test.begins_with("hang"):
		var until := Time.get_ticks_msec() + 600000
		while Time.get_ticks_msec() < until:
			pass
	elif _test.begins_with("flood"):
		for i in 400000:
			push_error("[watchdog] flood test line %d" % i)
