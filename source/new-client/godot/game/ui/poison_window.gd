extends ClassicWindow
## The poison bag (owner 2026-10-27): four poisons in two sets - slots 1 + 2, slots 3 + 4. The server puts the active
## set on your weapons by itself whenever the game's poisoning rules allow it (out of combat, Envenom high enough):
## the first of the set on the weapon in your hand, the second on the left-hand weapon (PoisonBag.cs). Drag a poison
## stack from the backpack onto a slot to put it in the bag - it leaves the backpack (owner 2026-10-27: no backpack
## space taken), any number of one poison to a slot; right-click a slot to put its poisons back in the backpack.
## Shift + mouse wheel (Swap Poison Sets) switches sets with a melee weapon out. Ctrl+B or /poisons opens it.

const BODY := Vector2(190, 104)
const NAMES := ["MAIN", "LEFT", "MAIN", "LEFT"]

var _slots: Array = []
var _counts: Array = []
var _sets: Array = []


func build() -> void:
	closable = true
	var title := UiArt.label("POISON BAG", 10, UiArt.GOLD_HI)
	title.position = Vector2(8, 4)
	title.size = Vector2(BODY.x - 16, 14)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(title)
	for s in 2:
		var l := UiArt.label("SET %d" % (s + 1), 8, UiArt.CREAM)
		l.position = Vector2(12 + s * 90, 20)
		l.size = Vector2(76, 10)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(l)
		_sets.append(l)
	for i in 4:
		var x := 14 + i * 40 + (10 if i >= 2 else 0)
		var s := PoisonSlot.new()
		s.index = i
		s.position = Vector2(x, 32)
		s.size = Vector2(32, 32)
		add_child(s)
		_slots.append(s)
		var hand := UiArt.label(NAMES[i], 7, UiArt.CREAM)
		hand.position = Vector2(x - 4, 66)
		hand.size = Vector2(40, 9)
		hand.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(hand)
		var n := UiArt.label("", 8, UiArt.CREAM)
		n.position = Vector2(x - 4, 76)
		n.size = Vector2(40, 10)
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(n)
		_counts.append(n)
	var hint := UiArt.label("DRAG IN - RIGHT-CLICK TAKES OUT", 7, UiArt.CREAM)
	hint.position = Vector2(6, 88)
	hint.size = Vector2(BODY.x - 12, 10)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(hint)
	set_window_size(BODY)
	PlayerData.inventory_changed.connect(refresh)
	tree_exiting.connect(func():
		if PlayerData.inventory_changed.is_connected(refresh):
			PlayerData.inventory_changed.disconnect(refresh))
	refresh()


## The server's poison bag (#AC|poisons, kept in Server.poison_bag): {set, slots: [{model, count, name}]}.
func refresh() -> void:
	var bag: Dictionary = Server.get("poison_bag") if Server.get("poison_bag") is Dictionary else {}
	var active := int(bag.get("set", 0))
	var slots: Array = bag.get("slots", [])
	for s in 2:
		(_sets[s] as Label).add_theme_color_override("font_color", UiArt.GOLD_HI if s == active else UiArt.CREAM)
	for i in 4:
		var e: Dictionary = slots[i] if i < slots.size() else {}
		(_slots[i] as PoisonSlot).show_entry(e, i / 2 == active)
		(_counts[i] as Label).text = ("x%d" % int(e.count)) if not e.is_empty() and int(e.count) > 0 else ""


class PoisonSlot extends Control:
	var index := 0
	var _icon: TextureRect
	var _rim: Panel
	var _back: Panel

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		_back = Panel.new()
		var b := StyleBoxFlat.new()
		b.bg_color = Color(0, 0, 0, 0.45)
		b.border_color = Color(0.35, 0.3, 0.22)
		b.set_border_width_all(1)
		_back.add_theme_stylebox_override("panel", b)
		_back.set_anchors_preset(Control.PRESET_FULL_RECT)
		_back.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(_back)
		_icon = TextureRect.new()
		_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_icon.stretch_mode = TextureRect.STRETCH_SCALE
		_icon.set_anchors_preset(Control.PRESET_FULL_RECT)
		_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(_icon)
		_rim = Panel.new()
		var s := StyleBoxFlat.new()
		s.bg_color = Color(0, 0, 0, 0)
		s.border_color = UiArt.GOLD_HI
		s.set_border_width_all(1)
		_rim.add_theme_stylebox_override("panel", s)
		_rim.set_anchors_preset(Control.PRESET_FULL_RECT)
		_rim.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_rim.visible = false
		add_child(_rim)

	func show_entry(e: Dictionary, active: bool) -> void:
		var n := int(e.get("count", 0))
		var nm := String(e.get("name", "")) if n > 0 else ""
		_icon.texture = ItemDb.icon(Server.item_icon(int(e.get("model", 0)))) if nm != "" else null
		_rim.visible = active and nm != ""
		tooltip_text = "%s x%d - RIGHT-CLICK: BACK TO THE BACKPACK" % [nm.to_upper(), n] if nm != "" else "EMPTY - DRAG A POISON HERE"

	func _can_drop_data(_p: Vector2, data: Variant) -> bool:
		return InventorySheet.is_item(data)

	func _drop_data(_p: Vector2, data: Variant) -> void:
		Server.command("/ac poison set %d %d" % [index + 1, int(data.slot)])

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
			Server.command("/ac poison clear %d" % (index + 1))
			accept_event()
