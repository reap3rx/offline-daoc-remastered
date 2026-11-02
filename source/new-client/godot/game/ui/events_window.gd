extends ClassicWindow
## The events window (owner 2026-11-02: "a useful tool for me to test events would be having a window that comes up
## when I type /events where I can just click on an event and spawn it in the region I'm in ... available events to
## click on for the zone I'm in, like Salisbury Plains for example, not everywhere in the game").
## /events asks the server (DynamicEventsCommandHandler) for "#EVL|{zone, events:[{id, title, levels, giver, stages,
## state, active}]}"; this window opens with a row for each of your zone's events: START runs it now from its first
## stage (a giver's chain sets off with its party), WAKE makes a timed one a disturbance that starts when someone
## comes near, STOP ends it. The list refreshes after each click.

const BODY := Vector2(420, 300)
const ROW_H := 30.0

var _title: Label
var _rows: VBoxContainer
var _empty: Label


func build() -> void:
	closable = true
	_title = UiArt.label("EVENTS", 10, UiArt.GOLD_HI)
	_title.position = Vector2(8, 4)
	_title.size = Vector2(BODY.x - 16, 14)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_title)
	var scroll := ScrollContainer.new()
	scroll.position = Vector2(8, 24)
	scroll.size = Vector2(BODY.x - 16, BODY.y - 46)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	_rows = VBoxContainer.new()
	_rows.custom_minimum_size = Vector2(BODY.x - 28, 0)
	_rows.add_theme_constant_override("separation", 2)
	scroll.add_child(_rows)
	_empty = UiArt.label("NO EVENTS IN THIS ZONE", 8, UiArt.DIM)
	_empty.position = Vector2(8, 60)
	_empty.size = Vector2(BODY.x - 16, 12)
	_empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty.visible = false
	add_child(_empty)
	var hint := UiArt.label("START: NOW  -  WAKE: WHEN SOMEONE COMES NEAR  -  STOP: END IT", 6, UiArt.DIM)
	hint.position = Vector2(8, BODY.y - 18)
	hint.size = Vector2(BODY.x - 16, 10)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(hint)
	set_window_size(BODY)


## The server's list for your zone: shown, and the window opened.
func receive(json: String) -> void:
	var d = JSON.parse_string(json)
	if not (d is Dictionary):
		return
	_title.text = ("EVENTS - %s" % String(d.get("zone", ""))).to_upper()
	for c in _rows.get_children():
		c.queue_free()
	var list: Array = d.get("events", [])
	_empty.visible = list.is_empty()
	for e in list:
		_rows.add_child(_row(e))
	if not visible:
		show_window()


func _row(e: Dictionary) -> Control:
	var row := Control.new()
	row.custom_minimum_size = Vector2(BODY.x - 28, ROW_H)
	var lv: Array = e.get("levels", [])
	var levels := "" if lv.is_empty() else "  %d-%d" % [int(lv[0]), int(lv[lv.size() - 1])]
	var head := UiArt.label(String(e.get("title", "")) + levels, 8, UiArt.CREAM)
	head.position = Vector2(2, 1)
	head.size = Vector2(232, 12)
	head.clip_text = true
	row.add_child(head)
	var giver := String(e.get("giver", ""))
	var sub := UiArt.label(("%s  -  %s" % [String(e.get("state", "")), "giver: " + giver if giver != "" else "%d stages" % int(e.get("stages", 0))]).to_upper(), 6, UiArt.DIM)
	sub.position = Vector2(2, 14)
	sub.size = Vector2(232, 10)
	sub.clip_text = true
	row.add_child(sub)
	var id := String(e.get("id", ""))
	var active := bool(e.get("active", false))
	var x := 240.0
	var start := UiArt.button("START", Vector2(52, 16), 8)
	start.position = Vector2(x, 4)
	start.disabled = active
	start.pressed.connect(func(): _do("start", id))
	row.add_child(start)
	var wake := UiArt.button("WAKE", Vector2(52, 16), 8)
	wake.position = Vector2(x + 56, 4)
	wake.disabled = active or giver != ""
	wake.pressed.connect(func(): _do("wake", id))
	row.add_child(wake)
	var stop := UiArt.button("STOP", Vector2(52, 16), 8)
	stop.position = Vector2(x + 112, 4)
	stop.disabled = not active
	stop.pressed.connect(func(): _do("stop", id))
	row.add_child(stop)
	return row


func _do(what: String, id: String) -> void:
	Server.command("/events %s %s" % [what, id])
	get_tree().create_timer(1.0).timeout.connect(func():
		if visible:
			Server.command("/events window"))
