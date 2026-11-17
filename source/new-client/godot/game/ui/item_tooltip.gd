class_name ItemTooltip
extends RefCounted
## Hovering a weapon or armour piece: the client's mini delve box (owner's screenshots of the real client,
## 2026-10-09): the name in the item's con colour (its level against yours), then ItemDb.summary's lines
## ("Staff Weapon / Crush Damage / Dps: 16.5  Spd: 4.6 / Con: 100%  Dur: 100% / Qua: 96%  Bon: 35% / Two-Handed").
## Other items just show their name. The box itself is the tooltip panel (UiArt.tooltip_theme). Right-click opens
## the information window instead (GameUI.show_info).

# item cons as clear colours, like the client's item names (bright green, yellow) - grey / green / blue / yellow /
# orange / red / purple
const CON := {-3: Color8(170, 170, 170), -2: Color8(80, 220, 80), -1: Color8(90, 150, 255), 0: Color8(240, 230, 60),
		1: Color8(255, 150, 40), 2: Color8(255, 60, 60), 3: Color8(200, 110, 255)}

static var _con: Array = []

# Camping supplies (owner 2026-11-11, the server's CampingSupplies): their quality is their colour, whatever your level -
# grey .. purple, as the con colours
const CAMP_TIERS := {
	"Smoky Campfire Kit": -3, "Dented Tin Cookpot": -3, "Woodsman's Campfire Kit": -2, "Iron Cookpot": -2,
	"Traveler's Campfire Kit": -1, "Traveler's Stewpot": -1, "Ranger's Campfire Kit": 0, "Ranger's Cauldron": 0,
	"Hearthstone Campfire Kit": 1, "Hearthkeeper's Cauldron": 1, "Emberforged Campfire Kit": 2,
	"Emberforged Cauldron": 2, "Everburning Campfire Kit": 3, "Feastmaster's Cauldron": 3,
}


## A quality-coloured item's colour (camping supplies), or null.
static func tier_color(it: Dictionary) -> Variant:
	var t = CAMP_TIERS.get(String(it.get("name", "")))
	return CON[int(t)] if t != null else null


static func is_gear(it: Dictionary) -> bool:
	var ot := int(it.get("object_type", 0))
	return ot > 0 and ot <= ItemDb.SHIELD_TYPE


## A Control for _make_custom_tooltip, or null for the plain caption.
static func make(it: Dictionary) -> Control:
	if Server.active and (String(it.get("id", "")).begins_with("srv:") or it.has("detail_key")):
		# the server's delve text (hover: prefetched) - your slot's, or an exchange item's (its detail_key)
		var d := Server.item_lines(it.detail_key if it.has("detail_key") else int(String(it.id).substr(4)))
		if not d.is_empty():
			var cap_col = tier_color(it)
			return card(String(d.caption), d.lines, cap_col if cap_col != null else con_color(int(it.get("level", 0)), PlayerData.level))
	if it.is_empty() or not is_gear(it):
		return null
	return card(String(it.get("name", "")), ItemDb.summary(it), con_color(int(it.get("level", 0)), PlayerData.level))


## A backpack item's hover box beside the one of what you wear in its place (owner 2026-11-04: "the full tool tip ...
## and then the tool tip beside it of what you currently have equipped in that slot"); just its own when that place
## is empty or it isn't worn at all.
static func compare(slot: int) -> Control:
	var it := PlayerData.item_at(slot)
	var own := make(it)
	var worn := worn_slot(it)
	if own == null or worn < 0 or worn == slot:
		return own
	var other := make(PlayerData.item_at(worn))
	if other == null:
		return own
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.add_child(_headed(own, "IN YOUR BAGS", UiArt.DIM))
	var bar := ColorRect.new()
	bar.color = Color(0.55, 0.45, 0.25, 0.7)
	bar.custom_minimum_size = Vector2(1, 0)
	bar.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(bar)
	row.add_child(_headed(other, "EQUIPPED", UiArt.GOLD_HI))
	return row


## Where you wear what this item would replace: the first of its places that holds something (for a weapon the
## main hand and two-hander places too), else -1.
static func worn_slot(it: Dictionary) -> int:
	if it.is_empty() or not is_gear(it):
		return -1
	var places: Array = PlayerData.slots_for(it)
	if places.is_empty():
		return -1
	var tries: Array = places.duplicate()
	if 12 in places or 10 in places:
		for s in [10, 12]:
			if not s in tries:
				tries.append(s)
	for s in tries:
		if not PlayerData.item_at(int(s)).is_empty():
			return int(s)
	return -1


static func _headed(box: Control, caption: String, col: Color) -> Control:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	var l := _line(caption, col)
	l.add_theme_font_size_override("font_size", 9)
	v.add_child(l)
	v.add_child(box)
	return v


## The con step (-3 grey .. 3 purple) of an item / creature level against the player's.
static func con_value(item_level: int, player_level: int) -> int:
	if _con.is_empty():
		con_color(0, 1)
	var row: Array = _con[clampi(player_level, 0, _con.size() - 1)]
	return int(row[item_level]) if item_level >= 0 and item_level < row.size() else 3


static func con_color(item_level: int, player_level: int) -> Color:
	if _con.is_empty():
		# the con table (capnbry concolors, pipeline/build_npcs.py) - the same for every zone
		var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://content/zones/zone200/npcs.json"))
		_con = parsed.get("con", [[]]) if parsed is Dictionary else [[]]
	var row: Array = _con[clampi(player_level, 0, _con.size() - 1)]
	return CON.get(int(row[item_level]) if item_level >= 0 and item_level < row.size() else 3, Color.WHITE)


## A spell / style / ability's hover box (a quickbar slot, a magic / combat sheet row - owner 2026-10-14: "healing and
## damage details don't show up on hover"): the server's delve text (asked when the pointer reached it - not here yet:
## null, the plain name), or in the game's own world SkillInfo's lines.
static func skill(e: Dictionary) -> Control:
	if e.is_empty() or String(e.get("kind", "")) in ["item", "macro", "petcmd"]:
		return null
	if Server.active and String(e.get("id", "")).begins_with("srv:smart:"):   # a smart heal: what it does, then its heal
		var lines: Array = Server.smart_lines(e)
		var d := Server.skill_lines(e)
		if not d.is_empty():
			lines.append(" ")
			lines.append(String(d.caption))
			lines.append_array(d.lines)
		return text_box(String(e.get("name", "")), lines)
	if Server.active:
		var d := Server.skill_lines(e)
		return null if d.is_empty() else text_box(String(d.caption), d.lines)
	return text_box(String(e.get("name", "")), SkillInfo.lines(e))


## A caption over lines of text, the delve box's look.
static func text_box(caption: String, lines: Array) -> Control:
	return card(caption, lines, UiArt.GOLD_HI)


## The hover box as a card (owner 2026-11-16: "tool tips need to be reworked into something more readable and useful
## to the player. Bigger, with the bonuses separated out so they're easier to read. Too cramped and small"): the name
## large in its colour; the delve's own headings ("Magical Bonuses:") as gold section titles over a rule; each bonus
## ("- Strength: 12 pts") a row of its own, the stat on the left and its value lined up on the right in green; every
## other "Name: value" the same in cream ("Dps: 16.5  Spd: 4.6" is two rows); the rest wrapped as written, in the
## server's own case. Its size is the player's (Options > Interface > TEXT AND FONTS: tooltips).
const CARD_W := 270.0
const BONUS := Color(0.55, 0.92, 0.5)
static var _kv := RegEx.create_from_string("^([A-Za-z][A-Za-z0-9 ()'/%.+_-]{0,34}?):\\s*(.+)$")
static var _utility := RegEx.create_from_string("^-?\\d+(\\.\\d+)?\\s*\\|\\s*(.+)$")    # "5.00 | Piercing: 1 pts"
static var _num_first := RegEx.create_from_string("^([+-]?[\\d.,]+%?)\\s+(.+)$")              # "3.0 Base DPS"


static func card(caption: String, lines: Array, cap_col: Color) -> Control:
	var k := UiArt.text_scale("tooltips")
	var w := CARD_W * k
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", roundi(2 * k))
	box.custom_minimum_size = Vector2(w, 0)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(_text(caption, 16, cap_col, true, w))
	var first := true
	var section := ""
	for raw in lines:
		var line := String(raw).strip_edges()
		if line == "":
			continue
		if line.begins_with("--- Technical"):
			break                                          # (a GM's technical dump: the information window has it)
		# a heading: "Magical Bonuses:", "Damage Modifiers:" ...
		if line.ends_with(":") and line.length() <= 40 and line.count(":") == 1:
			section = line.to_lower()
			box.add_child(_gap(4 if first else 7))
			box.add_child(_text(line.trim_suffix(":").to_upper(), 10, UiArt.GOLD, true, w))
			var rule := ColorRect.new()
			rule.color = Color(0.55, 0.45, 0.25, 0.6)
			rule.custom_minimum_size = Vector2(w, 1)
			rule.mouse_filter = Control.MOUSE_FILTER_IGNORE
			box.add_child(rule)
			first = false
			continue
		# the item's maker line before any section ("Atlas ROG | Ranger"): small and dim under the name
		if section == "" and first and line.contains(" | ") and not _utility.search(line):
			box.add_child(_text(line, 10, UiArt.DIM, false, w))
			continue
		if first:
			box.add_child(_gap(3))
			first = false
		# a bonus: "- Strength: 12 pts", "5.00 | Piercing: 1 pts" (the utility number dropped), "+ 5 Constitution"
		var listed := false
		var um := _utility.search(line)
		if um:
			line = um.get_string(2).strip_edges()
			listed = true
		elif line.begins_with("- ") or line.begins_with("+ ") or line.begins_with("* "):
			line = line.substr(2).strip_edges()
			listed = true
		var magic := listed and (section.contains("bonus") or section.contains("resist") or um != null)
		var vcol := BONUS if magic else UiArt.CREAM
		var parts := [line]
		if not listed and line.contains("  "):
			parts = Array(line.split("  ", false)).map(func(x): return String(x).strip_edges())
		for part in parts:
			var m := _kv.search(String(part))
			if m and m.get_string(2).length() <= 24:
				box.add_child(_pair(m.get_string(1), m.get_string(2), UiArt.CREAM if listed else UiArt.DIM, vcol, w))
				continue
			var nm: RegExMatch = _num_first.search(String(part)) if listed else null
			if nm and nm.get_string(2).length() <= 26:
				box.add_child(_pair(nm.get_string(2), nm.get_string(1), UiArt.CREAM, vcol, w))
				continue
			box.add_child(_text(String(part), 12, vcol if listed else UiArt.CREAM, false, w))
	return box


static func _text(t: String, px: int, col: Color, bold: bool, w: float) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_override("font", UiArt.font(bold, "tooltips"))
	l.add_theme_font_size_override("font_size", UiArt.tsize(px, "tooltips"))
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_shadow_color", UiArt.SHADOW)
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(w, 0)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiArt.themed(l)
	return l


static func _pair(key: String, value: String, kcol: Color, vcol: Color, w: float) -> Control:
	var row := HBoxContainer.new()
	row.custom_minimum_size = Vector2(w, 0)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var a := _text(key, 12, kcol, false, 0.0)
	a.autowrap_mode = TextServer.AUTOWRAP_OFF
	a.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(a)
	var b := _text(value, 12, vcol, true, 0.0)
	b.autowrap_mode = TextServer.AUTOWRAP_OFF
	b.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(b)
	return row


static func _gap(px: float) -> Control:
	var g := Control.new()
	g.custom_minimum_size = Vector2(0, px * UiArt.text_scale("tooltips"))
	g.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return g


static func _line(text: String, col: Color) -> Label:
	var l := UiArt.label(text, 13, col)
	l.add_theme_font_override("font", UiArt.font(true, "tooltips"))
	l.add_theme_font_size_override("font_size", UiArt.tsize(13, "tooltips"))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
