extends Control
## What you just learned (owner 2026-11-16: "when new spells are learned, it can be kind of hard to know ... I'd like an
## announcement type message to appear, kind of under the compass at the top middle of the screen ... with a picture of
## the spell's icon ... They would linger for a bit ... before moving on to the next one ... Same can go with trained
## spells, and new combat styles/abilities learned"), and your new spells on your hotbar ("auto populate new spell
## upgrades of the same line (Ex: Moon Ray, Moon Streak) on the spell bar and replace the weaker versions when learned";
## "the player can always clear them out"; Options > Interface turns it off). A brand-new character's first spells go
## where a controller reaches them: offensive spells on LB + X (then LB + B, LB + A), heals on LB + Y, buffs on LB and the
## d-pad.
##
## What is new is told by name against everything known before (spells of both kinds of list, styles, abilities); the
## lists that arrive as you enter the world are only taken in (WARM_MS), never announced.

const PadAssign := preload("res://game/input/pad_assign.gd")
const WARM_MS := 9000
const SHOW_S := 4.5
const FADE_S := 0.5
const OFFENSIVE_TYPES := ["DirectDamage", "Bolt", "DamageOverTime", "Lifedrain", "DamageShield", "DirectDamageWithDebuff",
		"Mesmerize", "Stun", "SpeedDecrease", "Disease", "Nearsight", "ArmorAbsorptionDebuff", "Taunt", "PetSpell"]
const HEAL_TYPES := ["Heal", "HealOverTime", "SpreadHeal", "CureMezz", "CurePoison", "CureDisease", "Resurrect",
		"PowerTransfer", "OmniHeal"]

var ui: Node
var _known := {}                          # "kind|name" (lower case) -> true: everything seen this session
var _seen_spells := {}                    # name (lower case) -> its entry: spells known before - an upgrade now takes the
										  # old rank's place in the server's list (SpellFamilies), so the old one is only here
var _who := ""
var _warm_until := 0
var _settle_at := 0
var _queue: Array = []                    # [{icon, border, caption, text, note}]
var _box: PanelContainer
var _showing := false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	Server.skills_changed.connect(_on_lists)
	if Server.has_signal("world_entered"):
		Server.world_entered.connect(_rewarm)
	_rewarm()


## Two choices in Options > Interface (owner 2026-11-16: a player may not want new spells put on the bars, but still
## want an upgrade to take its weaker spell's place): new spells into free slots (and a new character's first spells),
## and upgrades over the spells they replace.
static func auto_bar_on() -> bool:
	return not bool(UiArt.load_settings().get_value("interface", "auto_spell_bar_off", false))


static func auto_upgrade_on() -> bool:
	return bool(UiArt.load_settings().get_value("interface", "auto_spell_upgrade", true))


func _rewarm() -> void:
	_known.clear()
	_seen_spells.clear()
	_who = String(Server.selected.get("name", "")) if Server.selected is Dictionary else ""
	_warm_until = Time.get_ticks_msec() + WARM_MS
	_settle_at = _warm_until


func _process(_delta: float) -> void:
	if _settle_at > 0 and Time.get_ticks_msec() >= _settle_at:
		_settle_at = 0
		_take_in(_current())
		_first_spells()
		_upgrade_stale()
	if not _showing and not _queue.is_empty():
		_show(_queue.pop_front())


func _on_lists() -> void:
	var who := String(Server.selected.get("name", "")) if Server.selected is Dictionary else ""
	if who != _who:
		_rewarm()
	var now := _current()
	if Time.get_ticks_msec() < _warm_until:
		_take_in(now)
		return
	var fresh: Array = []
	for e in now:
		if not _known.has(_key(e)):
			fresh.append(e)
	_take_in(now)
	if fresh.is_empty():
		return
	fresh.sort_custom(func(a, b): return int(a.lv) < int(b.lv))
	var bar_notes := _place_on_bars(fresh, auto_upgrade_on(), auto_bar_on())
	for e in fresh:
		_queue.append(_announcement(e, String(bar_notes.get(_key(e), ""))))


static func _key(e: Dictionary) -> String:
	return "%s|%s" % [String(e.kind), String(e.name).to_lower()]


func _take_in(list: Array) -> void:
	for e in list:
		_known[_key(e)] = true
		if String(e.kind) == "spell":
			_seen_spells[String(e.name).to_lower()] = e


## Everything you can use now, with where it belongs: [{kind, id, icon, border, name, lv, line, sort}] - sort is
## "spell" / "song" / "style" / "ability" / "realm".
func _current() -> Array:
	var out: Array = []
	if not Server.active:
		return out
	for li in Server.spell_lines.size():
		var line: Dictionary = Server.spell_lines[li]
		for sp in (line.spells as Array):
			var style := String(sp.get("kind", "spell")) == "style"
			var kind := "style" if style else "spell"
			var ic: Array = Server.skill_icon(kind, int(sp.icon))
			out.append({"kind": kind, "id": "srv:spell:%d:%d" % [li, int(sp.level)], "icon": int(ic[0]),
					"border": int(ic[1]), "name": String(sp.name), "lv": int(sp.level), "line": String(line.name),
					"sort": kind, "sid": int(sp.get("id", 0))})
	var first := PanelSheets._first_skill()
	var style_spec: Dictionary = PadAssign._style_specs()
	for i in Server.skills.size():
		var sk: Dictionary = Server.skills[i]
		var pg := int(sk.page)
		if pg == 0:
			continue
		var kind: String = "ability" if pg in [1, 5, 6] else ("style" if pg == 2 else "spell")
		var ic: Array = Server.skill_icon("icon" if kind == "ability" else kind, int(sk.icon))
		if kind == "ability" and int(ic[0]) < 0:
			continue                                       # (a passive line of text: Weaponry, Dual Wield ...)
		var line := ""
		var sort := kind
		if kind == "ability" and pg == 6:
			sort = "realm"
		elif kind == "style":
			line = String(style_spec.get(String(sk.name), ""))
		elif kind == "spell":
			var spi := int(sk.get("special", 0xFE))
			if pg == 4 or spi == 0xFF:
				sort = "song"
			if spi >= 0 and spi < Server.skills.size() and int(Server.skills[spi].page) == 0:
				line = String(Server.skills[spi].name)
		out.append({"kind": kind, "id": "srv:skill:%d" % (i - first), "icon": int(ic[0]), "border": int(ic[1]),
				"name": String(sk.name), "lv": int(sk.level), "line": line, "sort": sort, "sid": 0})
	return out


# ---------------------------------------------------------------- the hotbar

## The game's data for a listed spell (its type, target, spell group): by the server's id when the name agrees, else by
## name.
static func spell_data(e: Dictionary) -> Dictionary:
	var s := ClassDb.spell(int(e.get("sid", 0)))
	if not s.is_empty() and String(s.get("name", "")) == String(e.name):
		return s
	return ClassDb.spell_by_name(String(e.name))


## Spells of one family are upgrades of each other: the same spell group (Minor Heal, Heal, Major Heal), or - without
## one - the same line, type, target, damage type and area.
static func family(e: Dictionary) -> String:
	var s := spell_data(e)
	if int(s.get("spellgroup", 0)) > 0:
		return "g%d" % int(s.spellgroup)
	if s.is_empty():
		# (a spell the client's tables don't know - a class kit's: its ranks share their line and icon)
		return "%s|icon%d" % [String(e.get("line", "")), int(e.get("icon", 0))] if String(e.get("line", "")) != "" else ""
	return "%s|%s|%s|%d|%s" % [String(e.get("line", "")), String(s.get("type", "")), String(s.get("target", "")),
			int(s.get("damagetype", 0)), "aoe" if int(s.get("radius", 0)) > 0 else "one"]


## New spells onto the bars (each part as its option says): each replaces a weaker spell of its family wherever one sits (every bar, every page);
## one with none takes the first free slot - one a controller reaches first (Pad.bindings), then the rest of the three
## bars' shown pages. Returns key -> a line for its announcement.
func _place_on_bars(fresh: Array, upgrade: bool, add: bool) -> Dictionary:
	var notes := {}
	if not upgrade and not add:
		return notes
	var known_by_name := _seen_spells.duplicate()
	for e in _current():
		if String(e.kind) == "spell":
			known_by_name[String(e.name).to_lower()] = e
	var changed := false
	for e in fresh:
		if String(e.kind) != "spell":
			continue
		var fam := family(e)
		var replaced: Array = []
		if fam != "" and upgrade:
			for pages in [PlayerData.all_slot_pages()]:      # (the keyboard's pages and the controller's)
				for bank in pages:
					for i in (bank as Array).size():
						var q = bank[i]
						if not (q is Dictionary) or String(q.get("kind", "")) != "spell":
							continue
						var old = known_by_name.get(String(q.get("name", "")).to_lower())
						if old == null or String(old.name) == String(e.name) or family(old) != fam or int(old.lv) >= int(e.lv):
							continue
						replaced.append(String(old.name))
						bank[i] = _entry(e)
		if not replaced.is_empty():
			changed = true
			notes[_key(e)] = "Replaces %s on your hotbar." % replaced[0]
			continue
		if not add:
			continue
		# the keyboard's bars and the controller's each get it in their first free slot (they are set up apart)
		var at := _free_slot()
		if at.x >= 0:
			PlayerData.quickbars[at.x][PlayerData.quickbar_bank[at.x]][at.y] = _entry(e)
			changed = true
		var pv := _free_pad_slot()
		if pv.x >= 0:
			PlayerData.pad_bars[pv.x][pv.y] = _entry(e)
			changed = true
		if Pad.active and pv.x >= 0:
			notes[_key(e)] = "Placed on your controller%s." % _where_pad(pv)
		elif at.x >= 0:
			notes[_key(e)] = "Placed on your hotbar (quickbar %d, slot %d)." % [at.x + 1, at.y + 1]
	if changed:
		PlayerData.save_character()
		PlayerData.changed.emit()
	return notes


static func _entry(e: Dictionary) -> Dictionary:
	return {"kind": String(e.kind), "id": String(e.id), "icon": int(e.icon), "border": int(e.border), "name": String(e.name)}


## The controller's slots, in the order a hand reaches them ("qbB_S" bindings, LB's layer before RB's).
static func _pad_order() -> Array:
	var out: Array = []
	var seen := {}
	for layer in ["lb+", "rb+", "lb+rb+", ""]:
		for s in ["x", "y", "b", "a", "up", "right", "down", "left"]:
			var act := String(Pad.bindings.get(layer + s, ""))
			if act.begins_with("qb"):
				var f := act.trim_prefix("qb").split("_")
				var v := Vector2i(int(f[0]) - 1, int(f[1]) - 1)
				if not seen.has(v) and v.x >= 0 and v.x < 3 and v.y >= 0 and v.y < PlayerData.SLOTS:
					seen[v] = true
					out.append(v)
	return out


## The keyboard's first free slot: the three bars' shown pages, bar by bar.
static func _free_slot() -> Vector2i:
	for b in 3:
		for s in PlayerData.SLOTS:
			if (PlayerData.quickbars[b][PlayerData.quickbar_bank[b]][s] as Dictionary).is_empty():
				return Vector2i(b, s)
	return Vector2i(-1, -1)


static func _free_pad_slot() -> Vector2i:
	for v in _pad_order():
		if (PlayerData.pad_bars[v.x][v.y] as Dictionary).is_empty():
			return v
	return Vector2i(-1, -1)


## " (LB + X)": the button that holds that controller slot.
static func _where_pad(at: Vector2i) -> String:
	var id := "qb%d_%d" % [at.x + 1, at.y + 1]
	for k in Pad.bindings:
		if String(Pad.bindings[k]) == id:
			return " (%s)" % Pad.describe(String(k))
	return ""


## A brand-new character (every bar empty, level 1 to 5): its first spells where a controller reaches them.
## A spell on your bars that you no longer have as such - its upgrade replaced it in your list (SpellFamilies, owner
## 2026-11-19: upgrades replace the older spell) - becomes the rank of its family you have now, wherever it sits.
func _upgrade_stale() -> void:
	if not auto_upgrade_on():
		return
	var now := _current()
	var have := {}
	var by_family := {}
	for e in now:
		if String(e.kind) != "spell":
			continue
		have[String(e.name).to_lower()] = true
		var fam := family(e)
		if fam != "" and (not by_family.has(fam) or int(e.lv) > int(by_family[fam].lv)):
			by_family[fam] = e
	var changed := false
	for pages in [PlayerData.all_slot_pages()]:
		for bank in pages:
			for i in (bank as Array).size():
				var q = bank[i]
				if not (q is Dictionary) or String(q.get("kind", "")) != "spell" or have.has(String(q.get("name", "")).to_lower()):
					continue
				var fam := family({"name": String(q.get("name", "")), "sid": 0, "line": "", "icon": int(q.get("icon", 0))})
				if fam == "" or not by_family.has(fam):
					continue
				bank[i] = _entry(by_family[fam])
				changed = true
	if changed:
		PlayerData.save_character()
		PlayerData.changed.emit()


func _first_spells() -> void:
	if not auto_bar_on() or int(Server.selected.get("level", 1)) > 5:
		return
	for bank in PlayerData.all_slot_pages():
		for q in bank:
			if q is Dictionary and not (q as Dictionary).is_empty():
				return
	var spots := {"offense": ["lb+x", "lb+b", "lb+a"], "heal": ["lb+y"], "buff": ["lb+up", "lb+right", "lb+down", "lb+left"]}
	var placed := 0
	var list := _current().filter(func(e): return String(e.kind) == "spell")
	list.sort_custom(func(a, b): return int(a.lv) < int(b.lv))
	for e in list:
		var s := spell_data(e)
		var t := String(s.get("type", ""))
		var role := "buff"
		if t in HEAL_TYPES:
			role = "heal"
		elif String(s.get("target", "")).to_lower() == "enemy" or t in OFFENSIVE_TYPES:
			role = "offense"
		var pv := Vector2i(-1, -1)                         # the controller: by role, where a thumb reaches it
		for input in spots[role]:
			var v: Vector2i = Pad.slot_for_input(input)
			if v.x >= 0 and (PlayerData.pad_bars[v.x][v.y] as Dictionary).is_empty():
				pv = v
				break
		if pv.x < 0:
			pv = _free_pad_slot()
		var at := _free_slot()                             # the keyboard: its first free slot
		if pv.x < 0 and at.x < 0:
			break
		if pv.x >= 0:
			PlayerData.pad_bars[pv.x][pv.y] = _entry(e)
		if at.x >= 0:
			PlayerData.quickbars[at.x][PlayerData.quickbar_bank[at.x]][at.y] = _entry(e)
		placed += 1
	if placed > 0:
		print("[learned] %d first spell(s) placed on the bars" % placed)
		PlayerData.save_character()
		PlayerData.changed.emit()


# ---------------------------------------------------------------- the announcement

func _announcement(e: Dictionary, note: String) -> Dictionary:
	var name := String(e.name)
	var line := String(e.get("line", ""))
	var caption := "NEW SPELL"
	var text := ""
	match String(e.sort):
		"spell":
			text = ("You've learned %s in the %s spell line." % [name, line]) if line != "" else "You've learned %s." % name
		"song":
			caption = "NEW SONG"
			text = ("You've learned the song %s in %s." % [name, line]) if line != "" else "You've learned the song %s." % name
		"style":
			caption = "NEW STYLE"
			text = ("You've learned the %s style in %s." % [name, line]) if line != "" else "You've learned the %s style." % name
		"realm":
			caption = "NEW REALM ABILITY"
			text = "You've learned the %s realm ability." % name
		_:
			caption = "NEW ABILITY"
			text = "You've learned the %s ability." % name
	return {"icon": int(e.icon), "border": int(e.border), "caption": caption, "text": text, "note": note}


func _show(a: Dictionary) -> void:
	_showing = true
	if _box and is_instance_valid(_box):
		_box.queue_free()
	_box = PanelContainer.new()
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.05, 0.045, 0.04, 0.82)
	bg.border_color = UiArt.GOLD.darkened(0.25)
	bg.set_border_width_all(1)
	bg.set_corner_radius_all(4)
	bg.content_margin_left = 10
	bg.content_margin_right = 14
	bg.content_margin_top = 7
	bg.content_margin_bottom = 7
	_box.add_theme_stylebox_override("panel", bg)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box.add_child(row)
	var pic := Control.new()
	pic.custom_minimum_size = Vector2(34, 34)
	pic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	for t in [ItemDb.icon(int(a.icon)), ItemDb.border(int(a.border)) if int(a.border) >= 0 else null]:
		if t == null:
			continue
		var tr := TextureRect.new()
		tr.texture = t
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_SCALE
		tr.size = Vector2(34, 34)
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		pic.add_child(tr)
	row.add_child(pic)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 1)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(col)
	col.add_child(UiArt.label(String(a.caption), 8, UiArt.GOLD_HI))
	var main := UiArt.label(String(a.text), 11, UiArt.CREAM)
	main.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	main.add_theme_constant_override("outline_size", 2)
	col.add_child(main)
	if String(a.note) != "":
		col.add_child(UiArt.label(String(a.note), 8, UiArt.DIM))
	add_child(_box)
	_box.modulate.a = 0.0
	_place.call_deferred()
	var tw := _box.create_tween()
	tw.tween_property(_box, "modulate:a", 1.0, FADE_S * 0.5)
	tw.tween_interval(SHOW_S)
	tw.tween_property(_box, "modulate:a", 0.0, FADE_S)
	tw.tween_callback(func():
		_box.queue_free()
		_showing = false)


## Centred a little under the compass (or near the top when it is closed).
func _place() -> void:
	if _box == null or not is_instance_valid(_box):
		return
	var a: Vector2 = ui.area() if ui and ui.has_method("area") else get_viewport_rect().size
	var top := a.y * 0.085
	if ui and ui.get("windows") is Dictionary and (ui.windows as Dictionary).has("compass"):
		var comp: Control = ui.windows["compass"]
		if is_instance_valid(comp) and comp.is_visible_in_tree():
			var r := comp.get_global_rect()
			top = (r.end.y - get_global_rect().position.y) / maxf(get_global_transform().get_scale().y, 0.01) + 10.0
	_box.reset_size()
	_box.position = Vector2((a.x - _box.size.x) * 0.5, top)
