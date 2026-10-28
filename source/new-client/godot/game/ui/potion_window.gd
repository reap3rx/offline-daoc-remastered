extends ClassicWindow
## The potion bag (owner 2026-10-27): sixteen more inventory slots for potions only, so they don't take backpack
## space - the server's PotionBag (the saddlebag slots 80-95). Drag potions in and out as with any slot, drag one to
## the quickbar to drink it from there, or double-click it here. Ctrl+P or /potions opens it.

const BODY := Vector2(180, 206)
const FIRST := 80
const COUNT := 16


func build() -> void:
	closable = true
	var title := UiArt.label("POTION BAG", 10, UiArt.GOLD_HI)
	title.position = Vector2(8, 4)
	title.size = Vector2(BODY.x - 16, 14)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(title)
	for i in COUNT:
		var back := Panel.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0.45)
		sb.border_color = Color(0.35, 0.3, 0.22)
		sb.set_border_width_all(1)
		back.add_theme_stylebox_override("panel", sb)
		back.position = Vector2(14 + (i % 4) * 40, 24 + (i / 4) * 40)
		back.size = Vector2(32, 32)
		back.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(back)
		var s := PotionSlot.new()
		s.slot = FIRST + i
		s.position = back.position
		s.size = back.size
		add_child(s)
	var hint := UiArt.label("POTIONS ONLY - DOUBLE-CLICK: DRINK", 7, UiArt.CREAM)
	hint.position = Vector2(8, 188)
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
		if c is PotionSlot:
			(c as PotionSlot).refresh()


## A potion bag slot: an inventory slot (drag in / out, onto the quickbar, delve); double-click drinks it.
class PotionSlot extends InventorySheet.EquipSlot:
	func refresh() -> void:
		super.refresh()
		_rim.visible = PlayerData.selected_slot == slot and not PlayerData.item_at(slot).is_empty()
		if PlayerData.item_at(slot).is_empty():
			tooltip_text = "EMPTY - DRAG A POTION HERE"

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT \
				and event.double_click and not PlayerData.entry(slot).is_empty():
			Server.use("srv:%d" % slot)
			accept_event()
			return
		if InventorySheet.click_hold(self, event, slot):
			accept_event()
			return
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT \
				and not PlayerData.entry(slot).is_empty():
			PlayerData.select_slot(slot)                    # then Shift+I (delve) / U (use), as the client
			accept_event()

	func _drop_data(_p: Vector2, data: Variant) -> void:
		if int(data.slot) == slot:
			if InventorySheet.double_clicked():
				Server.use("srv:%d" % slot)
			return
		PlayerData.move(int(data.slot), slot)
