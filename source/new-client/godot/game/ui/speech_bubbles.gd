extends RefCounted
## Floating speech over a talking NPC's head (owner 2026-11-02: the NPC window popping up in the middle of a fight
## "messes with action combat" - "floating chat bubbles instead? Might be a useful system to have developed").
## The server sends "#SAY|<object id>|<name>|<text>" (NpcSpeech.cs) to the players near the speaker: the words float
## over the NPC for a few seconds (longer for longer lines) and go into the chat as an NPC line. A new line from the
## same NPC replaces its old bubble. Usable for anyone's speech: preload("res://game/ui/speech_bubbles.gd").show(view, text).

const EM := 0.017                       # font size, a set fraction of the screen height (as the name plates)
const WRAP_EMS := 18                     # wrap width, in font sizes
const BASE_S := 3.5                      # on screen: this, plus a little per word
const PER_WORD_S := 0.28
const MAX_S := 11.0
const FADE_S := 0.6


static func show(view: Node3D, text: String, height := 1.8) -> void:
	if view == null or not is_instance_valid(view) or text.strip_edges() == "":
		return
	if view.has_meta("speech_bubble"):
		var old = view.get_meta("speech_bubble")
		if old != null and is_instance_valid(old):
			old.queue_free()
	# a set size on screen at any distance, like the name plates (game/npcs/name_plates.gd): one font pixel = one
	# screen pixel, so a captain forty metres down the road is as readable as one beside you
	var vp := view.get_viewport()
	var vp_h := vp.get_visible_rect().size.y if vp else 1080.0
	var cam := vp.get_camera_3d() if vp else null
	var fov := cam.fov if cam else 70.0
	var size := maxi(10, roundi(EM * vp_h))
	var l := Label3D.new()
	l.text = _clean(text)
	l.font = UiArt.font(true)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.fixed_size = true
	l.pixel_size = 2.0 * tan(deg_to_rad(fov * 0.5)) / vp_h
	l.font_size = size
	l.outline_size = maxi(4, roundi(size * 0.3))
	l.outline_modulate = Color(0.05, 0.04, 0.03, 0.95)
	l.modulate = Color(1.0, 0.97, 0.86)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.width = size * WRAP_EMS
	l.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	l.shaded = false
	l.double_sided = true
	l.no_depth_test = true                 # a shout carries: readable through the trees
	l.render_priority = 2
	l.position = Vector3(0, height + 0.2, 0)
	l.offset = Vector2(0, size * 2.6)       # above the name and guild lines
	view.add_child(l)
	view.set_meta("speech_bubble", l)
	var words := l.text.split(" ", false).size()
	var life := minf(MAX_S, BASE_S + PER_WORD_S * words)
	var tw := l.create_tween()
	tw.tween_interval(life)
	tw.tween_property(l, "modulate:a", 0.0, FADE_S)
	tw.tween_callback(l.queue_free)


## "[ready]" keywords stay readable; the server's "X says, " prefix (if any) is dropped - the bubble is over X already.
static func _clean(text: String) -> String:
	var t := text.strip_edges()
	var i := t.find(" says, \"")
	if i > 0 and i < 60 and t.ends_with("\""):
		t = t.substr(i + 8, t.length() - i - 9)
	return t
