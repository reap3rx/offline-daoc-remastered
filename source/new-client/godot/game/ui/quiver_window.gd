extends ClassicWindow
## The quiver (owner 2026-10-26: the old client's quiver - four slots to keep arrows / bolts in and pick which you
## shoot): your inventory's quiver slots 14-17 (eInventorySlot.FirstQuiver..FourthQuiver). Drag ammunition in and out
## as with any slot; double-click or right-click a slot to shoot from it (the server's GamePlayer.SwitchQuiver, by
## /ac quiver N). The slot you shoot from has the gold rim - the server's active quiver, as its inventory packets say.
## Ctrl+Q or /quiver opens it; Shift + mouse wheel (Next / Previous Arrows) changes arrows, even with the bow drawn.

const BODY := Vector2(180, 88)
const FIRST := 14


func build() -> void:
	closable = true
	var title := UiArt.label("QUIVER", 10, UiArt.GOLD_HI)
	title.position = Vector2(8, 4)
	title.size = Vector2(BODY.x - 16, 14)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(title)
	for i in 4:
		var back := Panel.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0.45)
		sb.border_color = Color(0.35, 0.3, 0.22)
		sb.set_border_width_all(1)
		back.add_theme_stylebox_override("panel", sb)
		back.position = Vector2(14 + i * 40, 24)
		back.size = Vector2(32, 32)
		back.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(back)
		var s := QuiverSlot.new()
		s.slot = FIRST + i
		s.position = back.position
		s.size = back.size
		add_child(s)
		var n := UiArt.label("", 8, UiArt.CREAM)
		n.name = "count_%d" % i
		n.position = Vector2(back.position.x - 4, 58)
		n.size = Vector2(40, 10)
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(n)
	var hint := UiArt.label("DOUBLE-CLICK: SHOOT THESE", 7, UiArt.CREAM)
	hint.position = Vector2(8, 70)
	hint.size = Vector2(BODY.x - 16, 10)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(hint)
	set_window_size(BODY)
	PlayerData.inventory_changed.connect(refresh)
	tree_exiting.connect(func():
		if PlayerData.inventory_changed.is_connected(refresh):
			PlayerData.inventory_changed.disconnect(refresh))
	refresh()


func refresh() -> void:
	for c in get_children():
		if c is QuiverSlot:
			(c as QuiverSlot).refresh()
	for i in 4:
		var l := get_node_or_null("count_%d" % i) as Label
		if l:
			var e: Dictionary = PlayerData.entry(FIRST + i)
			l.text = "" if e.is_empty() else "x%d" % int(e.get("count", 1))


## A quiver slot: an inventory slot (drag in / out, delve) whose rim marks the arrows you shoot.
class QuiverSlot extends InventorySheet.EquipSlot:
	func refresh() -> void:
		super.refresh()
		var it := PlayerData.item_at(slot)
		_rim.visible = not it.is_empty() and int(Server.get("active_quiver")) == slot - 13

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and not PlayerData.entry(slot).is_empty() \
				and (event.button_index == MOUSE_BUTTON_RIGHT or (event.button_index == MOUSE_BUTTON_LEFT and event.double_click)):
			Server.command("/ac quiver %d" % (slot - 13))
			accept_event()
			return
		if InventorySheet.click_hold(self, event, slot):
			accept_event()

	func _drop_data(_p: Vector2, data: Variant) -> void:
		if int(data.slot) == slot:
			if InventorySheet.double_clicked():
				Server.command("/ac quiver %d" % (slot - 13))
			return
		PlayerData.move(int(data.slot), slot)
