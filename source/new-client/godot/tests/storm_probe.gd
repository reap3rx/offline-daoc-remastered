extends Node
## Debug (claude 2026-10-30, weather sounds): a forced storm (--storm=1 --remastered=1): lightning flashes, the thunder
## after each, the wind gusts, the rain beds' volume; 45 s.
var flashes := 0
var thunders := 0
var gusts := 0
var seen := {}


func _ready() -> void:
	var v := get_tree().current_scene
	await get_tree().create_timer(5.0).timeout
	v.sky.lightning.connect(func(s): flashes += 1; print("[storm] flash %.2f at %.1f" % [s, Time.get_ticks_msec() / 1000.0]))
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 45000:
		await get_tree().create_timer(0.2).timeout
		for c in v.audio.get_children():
			if c is AudioStreamPlayer and (c as AudioStreamPlayer).playing and not seen.has(c.get_instance_id()):
				seen[c.get_instance_id()] = true
				var f := String((c as AudioStreamPlayer).stream.resource_path) if (c as AudioStreamPlayer).stream else ""
				var m := String(c.get_meta("file", ""))
				var tag := m if m != "" else "weather"
				if c.get_meta("file", "") == "":
					print("[storm] weather shot at %.1f, %.1f dB" % [Time.get_ticks_msec() / 1000.0, (c as AudioStreamPlayer).volume_db])
				else:
					print("[storm] zone sound %s %.1f dB" % [m, (c as AudioStreamPlayer).volume_db])
	print("[storm] flashes %d, rain %.2f, storm %.2f" % [flashes, v.sky.rain_amount(), v.sky.storm])
	get_tree().quit()
