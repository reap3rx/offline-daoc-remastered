extends RefCounted
## Floating speech over a talking NPC's head (owner 2026-11-02: the NPC window popping up in the middle of a fight
## "messes with action combat" - "floating chat bubbles instead? Might be a useful system to have developed").
## The server sends "#SAY|<object id>|<name>|<text>" (NpcSpeech.cs) to the players near the speaker: the words float
## over the NPC for a few seconds (longer for longer lines) and go into the chat as an NPC line. A new line from the
## same NPC replaces its old bubble. Usable for anyone's speech: preload("res://game/ui/speech_bubbles.gd").show(view, text).
##
## Drawn flat on the screen over the world, at whole pixels, like the name plates (owner 2026-11-20 bugs doc: "Floating
## speech bubbles need to be built on the same resolution as the UI and overhead names so that the text is readable at
## lower resolutions"): they were Label3Ds in the 3D scene, so they went through the 3D render scale like the world and
## blurred at low resolutions. Each bubble follows its speaker's head (projected every frame), above the name lines.

const EM := 0.017                       # font size, a set fraction of the screen height (as the name plates)
const WRAP_EMS := 18                     # wrap width, in font sizes
const BASE_S := 3.5                      # on screen: this, plus a little per word
const PER_WORD_S := 0.28
const MAX_S := 11.0
const FADE_S := 0.6
const RANGE := 60.0                      # metres: further than this from the camera, a bubble isn't drawn


## color: the words' colour (a yell is red: owner 2026-11-16).
static func show(view: Node3D, text: String, height := 1.8, color := Color(1.0, 0.97, 0.86)) -> void:
	if view == null or not is_instance_valid(view) or text.strip_edges() == "":
		return
	var tree := view.get_tree()
	if tree == null:
		return
	var ov: Overlay = tree.root.get_node_or_null("SpeechBubbles2D")
	if ov == null:
		ov = Overlay.new()
		ov.name = "SpeechBubbles2D"
		tree.root.add_child(ov)
	ov.add(view, _clean(text), height, color)


## "[ready]" keywords stay readable; the server's "X says, " prefix (if any) is dropped - the bubble is over X already.
static func _clean(text: String) -> String:
	var t := text.strip_edges()
	var i := t.find(" says, \"")
	if i > 0 and i < 60 and t.ends_with("\""):
		t = t.substr(i + 8, t.length() - i - 9)
	var y := t.find(" yells, \"")
	if y > 0 and y < 60 and t.ends_with("\""):
		t = t.substr(y + 9, t.length() - y - 10)
	return t


## The screen layer that draws every bubble (one for the game).
class Overlay extends CanvasLayer:
	var _canvas: Control
	var _bubbles: Array = []            # [view weakref, text, height, colour, born ms, life s]

	func _ready() -> void:
		layer = 1                       # with the name plates: over the world, under the windows
		_canvas = Control.new()
		_canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
		_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_canvas.draw.connect(_draw_all)
		add_child(_canvas)

	func add(view: Node3D, text: String, height: float, color: Color) -> void:
		for b in _bubbles.duplicate():
			if b[0].get_ref() == view:   # a new line from the same speaker replaces the old
				_bubbles.erase(b)
		var words := text.split(" ", false).size()
		_bubbles.append([weakref(view), text, height, color, Time.get_ticks_msec(), minf(MAX_S, BASE_S + PER_WORD_S * words)])

	func _process(_d: float) -> void:
		if not _bubbles.is_empty():
			_canvas.queue_redraw()

	func _draw_all() -> void:
		var vp := get_viewport()
		var cam := vp.get_camera_3d() if vp else null
		if cam == null:
			return
		var vp_h := vp.get_visible_rect().size.y
		var size := maxi(10, roundi(EM * vp_h * UiArt.text_scale("bubbles")))
		var font: Font = UiArt.font(true, "bubbles")
		var outline := maxi(4, roundi(size * 0.3))
		var wrap := float(size * WRAP_EMS)
		var lift := EM * vp_h * UiArt.text_scale("names") * 2.6       # above the name and guild lines
		var now := Time.get_ticks_msec()
		for b in _bubbles.duplicate():
			var view = b[0].get_ref()
			var age := (now - int(b[4])) / 1000.0
			if view == null or not is_instance_valid(view) or not view.is_inside_tree() or age > float(b[5]) + FADE_S:
				_bubbles.erase(b)
				continue
			var head: Vector3 = (view as Node3D).global_position + Vector3(0, float(b[2]) + 0.2, 0)
			if cam.is_position_behind(head) or cam.global_position.distance_to(head) > RANGE:
				continue
			var at := cam.unproject_position(head)
			var col: Color = b[3]
			col.a = 1.0 - clampf((age - float(b[5])) / FADE_S, 0.0, 1.0)
			var text: String = b[1]
			# wrapped, centred, its bottom line sitting above the name
			var box := font.get_multiline_string_size(text, HORIZONTAL_ALIGNMENT_CENTER, wrap, size)
			var lines := maxi(1, roundi(box.y / font.get_height(size)))
			var top := Vector2(roundf(at.x - wrap * 0.5), roundf(at.y - lift - box.y + font.get_ascent(size)))
			var shadow := Color(0.05, 0.04, 0.03, 0.95 * col.a)
			_canvas.draw_multiline_string_outline(font, top, text, HORIZONTAL_ALIGNMENT_CENTER, wrap, size, lines, outline, shadow)
			_canvas.draw_multiline_string(font, top, text, HORIZONTAL_ALIGNMENT_CENTER, wrap, size, lines, col)
