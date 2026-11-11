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
			var sbox := VBoxContainer.new()
			sbox.add_theme_constant_override("separation", -1)
			var cap_col = tier_color(it)
			sbox.add_child(_line(String(d.caption), cap_col if cap_col != null else con_color(int(it.get("level", 0)), PlayerData.level)))
			for l in d.lines:
				if String(l).strip_edges() != "":
					sbox.add_child(_line(String(l), UiArt.CREAM))
			return sbox
	if it.is_empty() or not is_gear(it):
		return null
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", -1)
	box.add_child(_line(String(it.get("name", "")), con_color(int(it.get("level", 0)), PlayerData.level)))
	for l in ItemDb.summary(it):
		box.add_child(_line(l, UiArt.CREAM))
	return box


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
	if Server.active:
		var d := Server.skill_lines(e)
		return null if d.is_empty() else text_box(String(d.caption), d.lines)
	return text_box(String(e.get("name", "")), SkillInfo.lines(e))


## A caption over lines of text, the delve box's look.
static func text_box(caption: String, lines: Array) -> Control:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", -1)
	box.add_child(_line(caption, UiArt.GOLD_HI))
	for l in lines:
		if String(l).strip_edges() != "":
			box.add_child(_line(String(l), UiArt.CREAM))
	return box


static func _line(text: String, col: Color) -> Label:
	var l := UiArt.label(text, 13, col)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
