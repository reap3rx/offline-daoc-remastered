extends ClassicWindow
## The modern inventory (owner 2026-11-02: "a modern inventory that auto sorts based on item type and value and wallet
## that contains things like our new event currency, Seals from DF and any other currencies that are in the game").
## Opens from the modern menu bar and the inventory key while STYLE is MODERN (docs/MODERN_UI.md):
##   - the backpack's 40 places as one grid, sorted - weapons, shields, armour, jewellery, ammunition,
##     poisons, crafting, the rest; inside each, the higher level / better quality first. Each square is still the
##     item's own backpack place: drag, double-click or right-click to equip (owner 2026-11-04; what can't be worn is
##     selected instead, then Shift+I / U), as on the classic rows; a search box dims what doesn't match;
##   - what you wear is in the Hero panel (owner 2026-11-04: "get rid of that and only be bags");
##   - bottom: the wallet - your coins, realm points and every currency the game uses (Marks of Valor, the Darkness
##     Falls seals, aurulite, Atlantean glass, dragon scales ...). The server keeps them off the backpack altogether
##     (PlayerWallet.cs, 2026-11-03) and tells us the counts as a "#WAL|" line; any still in the backpack (offline, or
##     an old stack the server hasn't moved yet) are counted too and stay out of the grid.

const SIZE := Vector2(280, 300)
const CELL := 32.0
const COLS := 8
const GRID_X := 12.0
const GRID_Y := 46.0
# the currencies (by name: the client only hears an item's name) - GameItemCurrencyMerchant's MoneyKeys and the event
# merchant's mark (ItemTemplate: event_mark, DiamondSeal, SapphireSeal, EmeraldSeal, aurulite, atlanteanglass,
# dragonscales ...)
const CURRENCIES := ["mark of valor", "daemon diamond seal", "daemon sapphire seal", "daemon emerald seal",
		"fiery diamond seal", "free daemon emerald seal", "cleansed diamond seal", "aurulite", "atlantean glass",
		"dragon scales", "blood seal", "glowing dreaded seal", "sanguine dreaded seal", "lambent dreaded seal",
		"fulgent dreaded seal", "effulgent dreaded seal", "brilliant dreaded seal", "radiant dreaded seal"]
const COINS := [["mithril", "M", Color(0.75, 0.85, 1.0)], ["platinum", "P", Color(0.85, 0.9, 0.95)],
		["gold", "G", Color(1.0, 0.82, 0.3)], ["silver", "S", Color(0.8, 0.8, 0.82)], ["copper", "C", Color(0.85, 0.5, 0.3)]]
const SORT_ORDER := ["WEAPONS", "SHIELDS", "ARMOUR", "JEWELLERY", "AMMUNITION", "POISONS", "CRAFTING", "OTHER"]

static var server_wallet := {}                 # currency name -> count (PlayerWallet.cs "#WAL|" line)
static var _open: Array = []                    # the open bag windows (to refresh when the wallet changes)
var _cells: Array = []
var _search: LineEdit
var _wallet: RichTextLabel
var _weight: Label
var _sorted_by: Label


func build() -> void:
	closable = true
	var title := UiArt.label("INVENTORY", 11, UiArt.GOLD_HI)
	title.position = Vector2(14, 6)
	title.size = Vector2(200, 16)
	add_child(title)
	var x := UiArt.button("X", Vector2(16, 14), 8)
	x.position = Vector2(SIZE.x - 24, 6)
	x.pressed.connect(hide_window)
	add_child(x)
	_weight = UiArt.label("", 8, UiArt.CREAM)
	_weight.position = Vector2(GRID_X + 60, GRID_Y + 5 * CELL + 4)
	_weight.size = Vector2(COLS * CELL - 60, 12)
	_weight.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_weight.tooltip_text = "WEIGHT CARRIED / CARRYING CAPACITY"
	_weight.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_weight)
	_search = LineEdit.new()
	_search.placeholder_text = "SEARCH"
	_search.position = Vector2(GRID_X, 25)
	_search.size = Vector2(130, 16)
	_search.add_theme_font_override("font", UiArt.font(true))
	_search.add_theme_font_size_override("font_size", 9)
	_search.add_theme_color_override("font_color", UiArt.CREAM)
	_search.add_theme_color_override("font_placeholder_color", UiArt.DIM)
	_search.add_theme_stylebox_override("normal", _box_style())
	_search.add_theme_stylebox_override("focus", _box_style(true))
	_search.text_changed.connect(func(_t: String): refresh())
	_search.text_submitted.connect(func(_t: String): _search.release_focus())
	add_child(_search)
	_sorted_by = UiArt.label("SORTED BY TYPE, LEVEL", 7, UiArt.DIM)
	_sorted_by.position = Vector2(GRID_X + 134, 27)
	_sorted_by.size = Vector2(COLS * CELL - 134, 12)
	_sorted_by.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(_sorted_by)
	for i in PlayerData.SACK * 5:
		var c := BagCell.new()
		c.position = Vector2(GRID_X + (i % COLS) * CELL, GRID_Y + (i / COLS) * CELL)
		c.size = Vector2(CELL - 2, CELL - 2)
		add_child(c)
		_cells.append(c)
	var wl := UiArt.label("WALLET", 8, UiArt.DIM)
	wl.position = Vector2(GRID_X, GRID_Y + 5 * CELL + 4)
	wl.size = Vector2(80, 12)
	add_child(wl)
	_wallet = RichTextLabel.new()
	_wallet.bbcode_enabled = true
	_wallet.fit_content = false
	_wallet.scroll_active = true
	_wallet.position = Vector2(GRID_X, GRID_Y + 5 * CELL + 17)
	_wallet.size = Vector2(COLS * CELL, SIZE.y - (GRID_Y + 5 * CELL + 17) - 10)
	_wallet.add_theme_font_override("normal_font", UiArt.font(true))
	_wallet.add_theme_font_size_override("normal_font_size", 9)
	_wallet.add_theme_color_override("default_color", UiArt.CREAM)
	_wallet.mouse_filter = Control.MOUSE_FILTER_PASS
	UiArt.themed(_wallet)
	add_child(_wallet)
	PlayerData.inventory_changed.connect(refresh)
	PlayerData.changed.connect(_refresh_wallet)
	tree_exiting.connect(func():
		PlayerData.inventory_changed.disconnect(refresh)
		PlayerData.changed.disconnect(_refresh_wallet))
	refresh()


static func receive_wallet(text: String) -> void:
	var parsed = JSON.parse_string(text)
	server_wallet = parsed if parsed is Dictionary else {}
	for w in _open:
		if is_instance_valid(w):
			w._refresh_wallet()


func _enter_tree() -> void:
	_open.append(self)


func _exit_tree() -> void:
	_open.erase(self)


static func _box_style(hi := false) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(0.04, 0.035, 0.03, 0.85)
	s.border_color = UiArt.GOLD_HI if hi else Color(0.45, 0.37, 0.22)
	s.set_border_width_all(1)
	s.content_margin_left = 4
	return s


func show_window() -> void:
	super.show_window()
	refresh()


static func is_currency(it: Dictionary) -> bool:
	return String(it.get("name", "")).to_lower() in CURRENCIES


## The sort group of an item (SORT_ORDER), from its object type (eObjectType).
static func group_of(it: Dictionary) -> int:
	var ot := int(it.get("object_type", 0))
	if (ot >= 1 and ot <= 28) or ot == 45:
		return 0
	if ot == 42:
		return 1
	if ot >= 31 and ot <= 38:
		return 2
	if ot == 41 or int(it.get("item_type", 0)) in [24, 29, 32, 33, 34, 35, 36]:
		return 3
	if ot == 43 or ot == 44:
		return 4
	if ot == 46:
		return 5
	if ot == 47 or ot == 48:
		return 6
	return 7


## Backpack places, sorted: filled ones by group, level (high first), quality, name; then the empty ones.
static func sorted_slots() -> Array:
	var full: Array = []
	var empty: Array = []
	for s in range(PlayerData.BACKPACK, PlayerData.BACKPACK_END + 1):
		var it := PlayerData.item_at(s)
		if it.is_empty():
			empty.append(s)
		elif not is_currency(it):
			full.append([group_of(it), -int(it.get("level", 0)), -int(it.get("quality", 0)), String(it.get("name", "")).to_lower(), s])
	full.sort()
	return full.map(func(r): return int(r[4])) + empty


func refresh() -> void:
	if not visible or _cells.is_empty():
		return
	var order := sorted_slots()
	var q := _search.text.strip_edges().to_lower() if _search else ""
	for i in _cells.size():
		var c: BagCell = _cells[i]
		c.visible = i < order.size()
		if not c.visible:
			continue
		c.slot = int(order[i])
		c.refresh()
		var it := PlayerData.item_at(c.slot)
		c.modulate.a = 1.0 if q == "" or it.is_empty() or String(it.get("name", "")).to_lower().contains(q) else 0.25
	if Server.active:
		_weight.text = "WEIGHT %d / %d" % [Server.weight_now, Server.weight_max] if Server.weight_max >= 0 else ""
	elif PlayerData.stats.size() >= 8:
		_weight.text = "WEIGHT %d / %d" % [PlayerData.inventory_weight(), maxi(int(PlayerData.effective_stats()[0]), int(PlayerData.stats[0]))]
	_refresh_wallet()


func _refresh_wallet() -> void:
	if _wallet == null or not visible:
		return
	var parts: Array = []
	for c in COINS:
		parts.append("[color=#%s]%d %s[/color]" % [(c[2] as Color).to_html(false), int(PlayerData.money.get(c[0], 0)), c[1]])
	var line1 := "   ".join(parts) + "      [color=#c9a85a]%s REALM POINTS[/color]" % _thousands(PlayerData.realm_points)
	var held := {}
	for n in server_wallet:
		held[String(n)] = int(server_wallet[n])
	for s in range(PlayerData.BACKPACK, PlayerData.BACKPACK_END + 1):
		var it := PlayerData.item_at(s)
		if not it.is_empty() and is_currency(it):
			var n := String(it.get("name", ""))
			held[n] = int(held.get(n, 0)) + int(PlayerData.entry(s).get("count", 1))
	var cur: Array = []
	var names := held.keys()
	names.sort()
	for n in names:
		cur.append("%s [color=#ffd873]%s[/color]" % [String(n).to_upper(), _thousands(int(held[n]))])
	_wallet.text = line1 + "\n" + ("[color=#9a9184]NO OTHER CURRENCIES YET[/color]" if cur.is_empty() else "    ".join(cur))


static func _thousands(n: int) -> String:
	var s := str(absi(n))
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return ("-" if n < 0 else "") + s + out


## One square of the grid: an item's icon with its stack count, standing for its own backpack place.
class BagCell extends Control:
	var slot := 40
	var _icon: TextureRect
	var _count: Label
	var _hi: Panel
	var _bs: StyleBoxFlat
	var _dragged_slot := -1

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		var back := Panel.new()
		_bs = StyleBoxFlat.new()
		_bs.bg_color = Color(0.04, 0.035, 0.03, 0.85)
		_bs.border_color = Color(0.45, 0.37, 0.22)
		_bs.set_border_width_all(1)
		back.add_theme_stylebox_override("panel", _bs)
		back.set_anchors_preset(Control.PRESET_FULL_RECT)
		back.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(back)
		_icon = TextureRect.new()
		_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_icon.stretch_mode = TextureRect.STRETCH_SCALE
		_icon.position = Vector2(2, 2)
		_icon.size = Vector2(26, 26)
		_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(_icon)
		_count = UiArt.label("", 7, UiArt.CREAM)
		_count.position = Vector2(0, 19)
		_count.size = Vector2(28, 10)
		_count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		_count.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 1))
		_count.add_theme_constant_override("shadow_offset_x", 1)
		_count.add_theme_constant_override("shadow_offset_y", 1)
		_count.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(_count)
		_hi = Panel.new()
		var st := StyleBoxFlat.new()
		st.bg_color = Color(1.0, 0.8, 0.35, 0.12)
		st.border_color = UiArt.GOLD_HI
		st.set_border_width_all(1)
		_hi.add_theme_stylebox_override("panel", st)
		_hi.set_anchors_preset(Control.PRESET_FULL_RECT)
		_hi.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_hi.visible = false
		add_child(_hi)

	func refresh() -> void:
		var e := PlayerData.entry(slot)
		var it := PlayerData.item_at(slot)
		_icon.texture = ItemDb.icon(int(it.get("icon", 0))) if not it.is_empty() else null
		var n := int(e.get("count", 1)) if not e.is_empty() else 0
		_count.text = str(n) if n > 1 else ""
		_hi.visible = PlayerData.selected_slot == slot and not e.is_empty()
		tooltip_text = String(it.get("name", "")).to_upper()
		# armour and weapons framed in the colour they con to you (owner 2026-11-04)
		var gear := not it.is_empty() and not PlayerData.slots_for(it).is_empty()
		_bs.border_color = ItemTooltip.con_color(int(it.get("level", 0)), PlayerData.level) if gear else Color(0.45, 0.37, 0.22)
		# camping supplies framed in their quality's colour, grey .. purple (owner 2026-11-11)
		var tier = ItemTooltip.tier_color(it) if not it.is_empty() else null
		if tier != null:
			_bs.border_color = tier
		_bs.set_border_width_all(2 if gear or tier != null else 1)

	func _get_drag_data(_p: Vector2) -> Variant:
		_dragged_slot = slot
		return InventorySheet.drag_data(slot, self)

	func _can_drop_data(_p: Vector2, data: Variant) -> bool:
		var ok := InventorySheet.is_item(data)
		_hi.visible = ok and int(data.slot) != slot
		return ok

	func _drop_data(_p: Vector2, data: Variant) -> void:
		if int(data.slot) == slot:
			if InventorySheet.double_clicked():
				PlayerData.equip(slot)
			return
		PlayerData.move(int(data.slot), slot)

	func _notification(what: int) -> void:
		if what == NOTIFICATION_MOUSE_ENTER and Server.active:
			Server.prefetch_item(slot)
			var worn := ItemTooltip.worn_slot(PlayerData.item_at(slot))
			if worn >= 0:
				Server.prefetch_item(worn)                     # (what you wear there, for the comparison)
		if what == NOTIFICATION_MOUSE_EXIT or what == NOTIFICATION_DRAG_END:
			_hi.visible = PlayerData.selected_slot == slot and not PlayerData.entry(slot).is_empty()
		if what == NOTIFICATION_DRAG_END and _dragged_slot >= 0:
			var from := _dragged_slot
			_dragged_slot = -1
			if not get_viewport().gui_is_drag_successful() and not InventorySheet.over_window(get_viewport()):
				var scene := get_tree().current_scene
				var ui = scene.get("ui") if scene else null
				if ui and ui.has_signal("item_dropped_on_world"):
					ui.item_dropped_on_world.emit(from, get_viewport().get_mouse_position())

	func _make_custom_tooltip(_for_text: String) -> Object:
		return ItemTooltip.compare(slot)

	## The pad's buttons on this item (Pad).
	func pad_actions() -> Array:
		return Pad.item_actions(slot)

	func _gui_input(event: InputEvent) -> void:
		if InventorySheet.click_hold(self, event, slot):
			accept_event()
			return
		if event is InputEventMouseButton and event.pressed and not PlayerData.entry(slot).is_empty():
			if event.button_index == MOUSE_BUTTON_RIGHT:
				# right-click wears it (owner 2026-11-04); what can't be worn is picked instead (then Shift+I / U)
				if PlayerData.slots_for(PlayerData.item_at(slot)).is_empty():
					PlayerData.select_slot(slot)
				else:
					PlayerData.equip(slot)
				accept_event()
			elif event.button_index == MOUSE_BUTTON_LEFT and event.double_click:
				PlayerData.equip(slot)
				accept_event()
