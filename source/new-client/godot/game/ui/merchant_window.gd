class_name MerchantWindow
extends ClassicWindow
## The shop (owner 2026-11-11: "The old dialogue box and shop window needs a UI update, so it's easier to make choices
## (using the same system our inventory and hero panel use with being able to scroll through them with your mouse").
## One list of everything the merchant sells - every page of the old window at once - scrolled with the mouse wheel
## (or the pad's d-pad), each row the item's icon, name in the colour it cons to you, level and price in coin. A click
## picks an item, a double-click (or BUY) buys it; QTY buys several of a stack. A search box narrows the list.
## Selling: your bags open with the shop (owner 2026-11-11: "automatically open your bag so you can sell easier") -
## right-click an item there, drag it onto this window, or pick it and press the Sell key.
## Chat lines are the server's: "You just bought {item} for {price}.", "{merchant} gives you {price} for {item}."
## Offline (no server): content/items/merchants.json, PlayerData.buy / sell as before.

const SIZE := Vector2(360, 430)
const ROW_H := 30.0
const LIST := Rect2(10, 48, 340, 300)
const COIN_COLORS := {"mithril": Color(0.75, 0.85, 1.0), "platinum": Color(0.85, 0.9, 0.95), "gold": Color(1.0, 0.82, 0.3),
		"silver": Color(0.8, 0.8, 0.82), "copper": Color(0.85, 0.5, 0.3)}

var npc_name := ""
var list_id := ""
var page := 0                                   # (kept for callers: every page shows at once now)
var pages: Array = []                           # [[item id, ...] per page]
var selected := ""
var server_window := -1
var _title: Label
var _search: LineEdit
var _scroll: ScrollContainer
var _list: VBoxContainer
var _price: RichTextLabel
var _purse: RichTextLabel
var _qty: SpinBox
var _buy: Button


func build() -> void:
	closable = true
	_title = UiArt.label("", 11, UiArt.GOLD_HI)
	_title.position = Vector2(14, 6)
	_title.size = Vector2(SIZE.x - 50, 16)
	_title.clip_text = true
	add_child(_title)
	var x := UiArt.button("X", Vector2(16, 14), 8)
	x.position = Vector2(SIZE.x - 24, 6)
	x.pressed.connect(hide_window)
	add_child(x)
	_search = LineEdit.new()
	_search.placeholder_text = "SEARCH"
	_search.position = Vector2(LIST.position.x, 25)
	_search.size = Vector2(150, 18)
	_search.add_theme_font_override("font", UiArt.font(true))
	_search.add_theme_font_size_override("font_size", 9)
	_search.add_theme_color_override("font_color", UiArt.CREAM)
	_search.add_theme_color_override("font_placeholder_color", UiArt.DIM)
	_search.add_theme_stylebox_override("normal", _box(false))
	_search.add_theme_stylebox_override("focus", _box(true))
	_search.text_changed.connect(func(_t: String): _fill())
	_search.text_submitted.connect(func(_t: String): _search.release_focus())
	add_child(_search)
	var hint := UiArt.label("DOUBLE-CLICK TO BUY", 7, UiArt.DIM)
	hint.position = Vector2(LIST.position.x + 156, 29)
	hint.size = Vector2(LIST.size.x - 156, 12)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(hint)
	var back := Panel.new()
	back.add_theme_stylebox_override("panel", _box(false))
	back.position = LIST.position - Vector2(2, 2)
	back.size = LIST.size + Vector2(4, 4)
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(back)
	_scroll = ScrollContainer.new()
	_scroll.position = LIST.position
	_scroll.size = LIST.size
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	UiArt.themed(_scroll)
	add_child(_scroll)
	_list = VBoxContainer.new()
	_list.custom_minimum_size = Vector2(LIST.size.x - 12, 0)
	_list.add_theme_constant_override("separation", 1)
	_scroll.add_child(_list)
	var y := LIST.end.y + 8
	_price = _rich(Vector2(LIST.position.x, y), Vector2(220, 16))
	add_child(_price)
	_qty = SpinBox.new()
	_qty.min_value = 1
	_qty.max_value = 100
	_qty.value = 1
	_qty.prefix = "QTY"
	_qty.position = Vector2(LIST.end.x - 132, y - 2)
	_qty.size = Vector2(68, 20)
	_qty.get_line_edit().add_theme_font_override("font", UiArt.font(true))
	_qty.get_line_edit().add_theme_font_size_override("font_size", 9)
	_qty.get_line_edit().add_theme_stylebox_override("normal", _box(false))
	add_child(_qty)
	_buy = UiArt.button("BUY", Vector2(60, 20), 10)
	_buy.position = Vector2(LIST.end.x - 60, y - 2)
	_buy.pressed.connect(buy_selected)
	add_child(_buy)
	_purse = _rich(Vector2(LIST.position.x, y + 22), Vector2(LIST.size.x, 16))
	add_child(_purse)
	var sell := UiArt.label("SELL: RIGHT-CLICK AN ITEM IN YOUR BAGS, OR DRAG IT HERE", 7, UiArt.DIM)
	sell.position = Vector2(LIST.position.x, SIZE.y - 22)
	sell.size = Vector2(LIST.size.x, 12)
	sell.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(sell)
	PlayerData.changed.connect(_show_purse)
	PlayerData.inventory_changed.connect(_show_purse)


static func _box(hi: bool) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(0.04, 0.035, 0.03, 0.85)
	s.border_color = UiArt.GOLD_HI if hi else Color(0.45, 0.37, 0.22)
	s.set_border_width_all(1)
	s.content_margin_left = 4
	return s


func _rich(at: Vector2, sz: Vector2) -> RichTextLabel:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.fit_content = false
	r.scroll_active = false
	r.position = at
	r.size = sz
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.add_theme_font_override("normal_font", UiArt.font(true))
	r.add_theme_font_size_override("normal_font_size", 9)
	r.add_theme_color_override("default_color", UiArt.CREAM)
	return r


## Coin as coloured parts: "1g 20s 5c" (the parts that aren't zero).
static func money_bb(copper: int) -> String:
	if copper <= 0:
		return "[color=#%s]0c[/color]" % COIN_COLORS.copper.to_html(false)
	var parts := PlayerData.split_money(copper)
	var out := []
	for k in ["mithril", "platinum", "gold", "silver", "copper"]:
		if int(parts[k]) > 0:
			out.append("[color=#%s]%d%s[/color]" % [(COIN_COLORS[k] as Color).to_html(false), int(parts[k]), k.substr(0, 1)])
	return " ".join(out)


## Where the shop opens: top centre, the whole window on the screen.
func _place_top_center() -> void:
	var area := get_parent_area_size()
	position = Vector2(clampf(floorf((area.x - size.x) * 0.5), 0.0, maxf(0.0, area.x - size.x)), 4.0)


func open_for(merchant: String, items_list: String) -> void:
	server_window = -1
	npc_name = merchant
	list_id = items_list
	pages = []
	for e in ItemDb.merchant_list(items_list):
		var p := int(e[0])
		while pages.size() <= p:
			pages.append([])
		pages[p].append(String(e[2]))
	pages = pages.filter(func(p): return not (p as Array).is_empty())
	_open(merchant)


## The server's merchant: its pages as the MerchantWindow packets brought them - each item a runtime ItemDb entry
## "srvm:<page>:<index>" (its slot on the server is page * 30 + index).
func open_server(merchant: String, server_pages: Dictionary, window_type: int) -> void:
	npc_name = merchant
	list_id = ""
	server_window = window_type
	pages = []
	var keys := server_pages.keys()
	keys.sort()
	for k in keys:
		pages.append(server_pages[k])
	_open(merchant)


func _open(merchant: String) -> void:
	var fresh := not visible
	_title.text = merchant.to_upper()
	if fresh:
		selected = ""
		_search.text = ""
		_qty.value = 1
		_place_top_center()
	_fill()
	show_window()
	if fresh:
		_scroll.scroll_vertical = 0
		_open_bags()


## Your bags with the shop, to sell from (the modern bags; the classic style's inventory sheet).
func _open_bags() -> void:
	var scene := get_tree().current_scene if is_inside_tree() else null
	var ui = scene.get("ui") if scene else null
	if ui == null:
		return
	if ui.get("modern"):
		if ui.bags == null or not ui.bags.visible:
			ui.toggle_bags()
	elif not (ui.right_panel.visible and String(ui.sheet_tab) == "inventory"):
		ui.show_sheet("inventory")


## Kept for callers of the old paged window: every page is in the one list now.
func show_page(_p: int) -> void:
	_fill()


func _fill() -> void:
	for c in _list.get_children():
		c.queue_free()
	var want := _search.text.strip_edges().to_lower() if _search else ""
	var shown := 0
	for pi in pages.size():
		var ids: Array = pages[pi]
		var first := true
		for id in ids:
			var it := ItemDb.item(String(id))
			if it.is_empty() or (want != "" and not String(it.get("name", "")).to_lower().contains(want)):
				continue
			if first and pages.size() > 1 and want == "":
				var head := UiArt.label("PAGE %d" % (pi + 1), 7, UiArt.DIM)
				head.custom_minimum_size = Vector2(0, 12)
				_list.add_child(head)
			first = false
			var r := ShopRow.new()
			r.window = self
			r.custom_minimum_size = Vector2(LIST.size.x - 12, ROW_H)
			_list.add_child(r)
			r.set_item(String(id))
			shown += 1
	if shown == 0:
		var none := UiArt.label("NOTHING FOR SALE" if want == "" else "NOTHING MATCHES", 9, UiArt.DIM)
		none.custom_minimum_size = Vector2(LIST.size.x - 12, 40)
		none.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		none.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		_list.add_child(none)
	_show_price()
	_show_purse()


func select_item(id: String) -> void:
	selected = id
	for r in _list.get_children():
		if r is ShopRow:
			r.queue_redraw()
	_qty.value = 1
	_show_price()


func _price_text(id: String) -> String:
	var price := int(ItemDb.item(id).get("price", 0))
	# a merchant paid in tokens or seals (Marks of Valor at a tower's quartermaster - the server's window type 2)
	if server_window == 2:
		return "[color=#f0c060]%d TOKENS[/color]" % price
	return money_bb(price)


func _show_price() -> void:
	if _price == null:
		return
	_buy.disabled = selected == ""
	_qty.editable = selected != "" and server_window not in [4, 11]
	_price.text = "" if selected == "" else "COST  " + _price_text(selected)


func _show_purse() -> void:
	if _purse and visible:
		_purse.text = "YOUR PURSE  " + money_bb(PlayerData.total_copper())


func buy_selected() -> void:
	if selected == "":
		return
	var count := int(_qty.value) if _qty else 1
	if Server.active and selected.begins_with("srvm:"):   # the server's merchant: PlayerBuyRequest (page * 30 + index)
		var parts := selected.split(":")
		if server_window in [4, 11]:
			# a house's looks (HousingOutsideMenu / HousingInsideMenu: roof, walls, door, carpets ...) are bought with
			# HouseEdit - the house you are at changes, no item is given
			Server.client.call("HouseEdit", int(parts[1]) * 30 + int(parts[2]))
			return
		var v: Node = Server.viewer()
		if v:
			var r: Vector3 = Server.to_region(Server.current_zone_id(), v.player.global_position)
			Server.client.call("BuyItem", int(r.x), int(r.y), int(parts[1]) * 30 + int(parts[2]), count, maxi(server_window, 0))
		return
	for i in count:
		PlayerData.buy(selected, npc_name)


## The controller's way to buy (owner 2026-11-12: "highlight the items with the plus pad, click a for a context window,
## then it be quantity option and then a buy option"): A on a row - BUY ONE, or HOW MANY... for a second menu of
## amounts; each says what it costs.
func pad_menu(id: String, row: Control) -> void:
	select_item(id)
	var menu = _social_menu()
	if menu == null:
		return
	var price := int(ItemDb.item(id).get("price", 0))
	var back := func():                                    # the pointer back on the row it came from
		if is_instance_valid(row) and row.is_visible_in_tree() and Pad.active:
			Pad.call("_point_at", row)
	var buy := func(n: int):
		_qty.value = n
		buy_selected()
		_qty.value = 1
		back.call()
	var entries := [["BUY ONE  -  " + _cost(price), buy.bind(1)]]
	if server_window not in [4, 11]:
		entries.append(["HOW MANY...", func():
			var amounts := []
			for n in [5, 10, 20, 50, 100]:
				amounts.append(["BUY %d  -  %s" % [n, _cost(price * n)], buy.bind(n)])
			amounts.append(["CANCEL", back])
			menu.open(String(ItemDb.item(id).get("name", "")), amounts)])
	entries.append(["CANCEL", back])
	menu.open(String(ItemDb.item(id).get("name", "")), entries)


func _cost(copper: int) -> String:
	if server_window == 2:
		return "%d TOKENS" % copper
	var p := PlayerData.split_money(copper)
	var out := []
	for k in ["mithril", "platinum", "gold", "silver", "copper"]:
		if int(p[k]) > 0:
			out.append("%d%s" % [int(p[k]), k.substr(0, 1)])
	return " ".join(out) if not out.is_empty() else "FREE"


func _social_menu():
	var v := get_tree().current_scene
	var ui = v.get("ui") if v else null
	return ui.get("social_menu") if ui else null


func _can_drop_data(_pos: Vector2, data: Variant) -> bool:
	return InventorySheet.is_item(data) and PlayerData.is_backpack(int(data.slot))


func _drop_data(_pos: Vector2, data: Variant) -> void:
	PlayerData.sell(int(data.slot), npc_name)


class ShopRow extends Control:
	var window: MerchantWindow
	var item_id := ""
	var _hover := false

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP

	func set_item(id: String) -> void:
		item_id = id
		tooltip_text = String(ItemDb.item(id).get("name", "")).to_upper()
		queue_redraw()

	func _draw() -> void:
		var it := ItemDb.item(item_id)
		if it.is_empty():
			return
		var sel := window != null and window.selected == item_id
		draw_rect(Rect2(Vector2.ZERO, size), Color(1.0, 0.8, 0.35, 0.16) if sel else (Color(1, 1, 1, 0.05) if _hover else Color(0, 0, 0, 0.18)))
		if sel:
			draw_rect(Rect2(Vector2.ZERO, size), UiArt.GOLD_HI, false, 1.0)
		var tex := ItemDb.icon(int(it.get("icon", 0)))
		if tex:
			draw_texture_rect(tex, Rect2(3, 2, size.y - 4, size.y - 4), false)
		var f := UiArt.font(true)
		var thin := UiArt.font(false)
		var lvl := int(it.get("level", 0))
		var col: Color = ItemTooltip.con_color(lvl, PlayerData.level) if lvl > 0 else UiArt.CREAM
		var x := size.y + 4
		draw_string(f, Vector2(x, 13), String(it.get("name", "")).to_upper(), HORIZONTAL_ALIGNMENT_LEFT, size.x - x - 96, 9, col)
		if lvl > 0:
			draw_string(thin, Vector2(x, 25), "LEVEL %d" % lvl, HORIZONTAL_ALIGNMENT_LEFT, 80, 7, UiArt.DIM)
		# the price, right: its coins in their colours
		var price := int(it.get("price", 0))
		var parts: Array = []
		if window and window.server_window == 2:
			parts = [["%d TOKENS" % price, Color(0.94, 0.75, 0.38)]]
		else:
			var p := PlayerData.split_money(price)
			for k in ["mithril", "platinum", "gold", "silver", "copper"]:
				if int(p[k]) > 0:
					parts.append(["%d%s" % [int(p[k]), k.substr(0, 1)], COIN_COLORS[k]])
			if parts.is_empty():
				parts = [["0c", COIN_COLORS.copper]]
		var right := size.x - 6
		for i in range(parts.size() - 1, -1, -1):
			var s := String(parts[i][0])
			var w := thin.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, 8).x
			right -= w
			draw_string(thin, Vector2(right, 19), s, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, parts[i][1])
			right -= 4

	func pad_actions() -> Array:
		return [["a", "BUY...", func(): window.pad_menu(item_id, self)], ["x", "INFORMATION", func(): _info()]]

	func _info() -> void:
		window.select_item(item_id)
		PlayerData.delve_id = item_id
		PlayerData.selected_slot = -1
		PlayerData.summary.emit(ItemDb.item(item_id))

	func _make_custom_tooltip(_for_text: String) -> Object:          # weapons / armour: the mini delve box
		return ItemTooltip.make(ItemDb.item(item_id)) if item_id != "" else null

	func _notification(what: int) -> void:
		if what == NOTIFICATION_MOUSE_ENTER:
			_hover = true
			queue_redraw()
			# the pad's d-pad walks the list: the row it lands on scrolls into view
			if Pad.active and window:
				window._scroll.ensure_control_visible(self)
		elif what == NOTIFICATION_MOUSE_EXIT:
			_hover = false
			queue_redraw()

	func _gui_input(event: InputEvent) -> void:
		if item_id == "" or not (event is InputEventMouseButton and event.pressed):
			return
		# the wheel scrolls the list (a row stops the mouse - the pad needs it to - so it hands the wheel on)
		if event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			window._scroll.scroll_vertical += int(ROW_H * 2) * (-1 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1)
			accept_event()
			return
		if event.button_index == MOUSE_BUTTON_LEFT:
			window.select_item(item_id)
			if event.double_click:
				window.buy_selected()
			accept_event()
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			window.select_item(item_id)                    # its standard information; then Shift+I = delve
			PlayerData.delve_id = item_id
			PlayerData.selected_slot = -1
			PlayerData.summary.emit(ItemDb.item(item_id))
			accept_event()
