extends ClassicWindow
## The Hero panel (owner 2026-11-03: "a GW2 inspired character panel that will have tabs on the left"): the modern
## style's one window for your character, in place of the classic sheets (docs/MODERN_UI.md). The menu bar's HERO and
## SKILLS orbs (and the character / skills / styles / spells keys) open it. Down the left, its pages:
##   EQUIPMENT - your figure with what you wear around it (the paper doll), the backpack beside it and your stats always
##     on the right, so they change as you put things on. Click a slot and the backpack shows only what fits there
##     (a caster's two-handed slot: the staves); click an item then to wear it there, or drag it.
##   SKILLS > SPECIALIZATION / REALM SKILLS - your specializations and abilities on the left, a copy of your quickbars
##     over the training list (train anywhere: spend points, TRAIN), and on the right the spellbook: everything the
##     chosen specialization will teach, in level order - what you know in full colour (drag it onto a bar), what
##     you don't yet greyed with the level that teaches it (HeroInfo.cs "/book").
## Appearance, Dyes and Achievements come later (the owner's list) and slot in under the same column.

const SIZE := Vector2(860, 480)
const NAV_W := 132.0
const HEAD_H := 30.0
const PAD := 8.0
const COL1 := Vector2(NAV_W + 12.0, 196.0)       # x, width: the backpack / specializations column
const COL2 := Vector2(NAV_W + 216.0, 286.0)      # the doll / training column
const PadAssignScript := preload("res://game/input/pad_assign.gd")
const COL3 := Vector2(NAV_W + 512.0, 206.0)      # the stats / spellbook column
const ModernBags := preload("res://game/ui/modern_bags.gd")
const PAGES := [["equipment", "EQUIPMENT", 0], ["skills", "SKILLS", 0], ["spec", "Specialization", 1], ["realm", "Realm Skills", 1]]
const DOLL_LEFT := [21, 26, 29, 25, 28, 22, 24, 33, 35]      # helm, cloak, neck, torso, arms, hands, jewel, L wrist, L ring
const DOLL_RIGHT := [27, 23, 32, 34, 36, 37]                 # legs, feet, waist, R wrist, R ring, mythical
const DOLL_WEAPONS := [10, 11, 12, 13]

var ui: GameUI
var page := "equipment"
var _sub := "spec"                                # the skills page's centre: "spec" / "realm"
var _nav: Control
var _title: Label
var _who: Label
var _body: Control
var filter_slot := -1                             # the equipment slot picked (the backpack shows what fits it)
var _cells: Array = []
var _slots: Array = []
var _filter_label: Label
var _grid: GridContainer
var _stats: RichTextLabel
var _book_spec := -1                              # the spellbook's specialization (its trainable index)
var _train_sel := -1                              # the training list's pick (spec index / realm skill index)
var _book_list: VBoxContainer
var _book_head: Label
var _book_sub: Label
var _train_rows: VBoxContainer
var _train_head: Label
var _train_pts: Label
var _left_specs: VBoxContainer
var _left_abil: VBoxContainer
var _bars: Array = []
var _pending_book := false


func build() -> void:
	closable = true
	var crest := Crest.new()
	crest.position = Vector2(6, 2)
	crest.size = Vector2(28, 28)
	add_child(crest)
	# who you are, where it said HERO (owner 2026-11-09: "<First name> <Last name>, the Level <level> <class>")
	_who = UiArt.label("", 13, UiArt.GOLD_HI)
	_who.position = Vector2(40, 7)
	_who.size = Vector2(440, 20)
	_who.clip_text = true
	add_child(_who)
	_title = UiArt.label("", 9, UiArt.CREAM)                # the page's name, right of it
	_title.position = Vector2(SIZE.x - 34 - 330, 10)
	_title.size = Vector2(330, 14)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(_title)
	var x := UiArt.button("X", Vector2(16, 14), 8)
	x.position = Vector2(SIZE.x - 24, 7)
	x.pressed.connect(hide_window)
	add_child(x)
	_nav = Nav.new()
	_nav.panel = self
	_nav.position = Vector2(PAD, HEAD_H + 6)
	_nav.size = Vector2(NAV_W - PAD, SIZE.y - HEAD_H - 14)
	add_child(_nav)
	_body = Control.new()
	_body.position = Vector2.ZERO
	_body.size = SIZE
	_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_body)
	PlayerData.inventory_changed.connect(_inventory_changed)
	PlayerData.changed.connect(_stats_changed)
	if Server.active:
		Server.book_changed.connect(_book_changed)
		Server.trainer_changed.connect(_trainer_changed)
		Server.skills_changed.connect(_skills_changed)
	tree_exiting.connect(func():
		PlayerData.inventory_changed.disconnect(_inventory_changed)
		PlayerData.changed.disconnect(_stats_changed)
		if Server.active:
			Server.book_changed.disconnect(_book_changed)
			Server.trainer_changed.disconnect(_trainer_changed)
			Server.skills_changed.disconnect(_skills_changed))
	show_page("equipment")


## Open on a page ("equipment", "skills"); the same page again closes it.
func open_page(p: String) -> void:
	if visible and page == p:
		hide_window()
		return
	show_page(p)
	show_window()


func show_page(p: String) -> void:
	if p == "spec" or p == "realm":
		_sub = p
		p = "skills"
	page = p
	for c in _body.get_children():
		c.queue_free()
	_cells.clear()
	_slots.clear()
	_bars.clear()
	_stats = null
	_book_list = null
	_train_rows = null
	match page:
		"equipment":
			_title.text = "EQUIPMENT   [%s]" % Keybinds.text("show_stats")
			_build_equipment()
		"skills":
			_title.text = "SKILLS  -  %s   [%s]" % ["SPECIALIZATION" if _sub == "spec" else "REALM SKILLS", Keybinds.text("show_skills")]
			_build_skills()
	_nav.queue_redraw()


func show_window() -> void:
	super.show_window()
	_refresh_who()
	if page == "skills":
		_ask_server()
	_refresh_all()


# ---------------------------------------------------------------- pieces

static func _panel_style(alpha := 0.55) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(0.03, 0.03, 0.035, alpha)
	s.border_color = Color(0.45, 0.37, 0.22, 0.8)
	s.set_border_width_all(1)
	return s


## A framed column with its heading; returns the inner area's top.
func _column(x: float, w: float, y: float, h: float, heading: String, right := "") -> Panel:
	var p := Panel.new()
	p.add_theme_stylebox_override("panel", _panel_style())
	p.position = Vector2(x, y)
	p.size = Vector2(w, h)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_body.add_child(p)
	if heading != "":
		var band := ColorRect.new()
		band.color = Color(0.2, 0.16, 0.09, 0.85)
		band.position = Vector2(1, 1)
		band.size = Vector2(w - 2, 16)
		band.mouse_filter = Control.MOUSE_FILTER_IGNORE
		p.add_child(band)
		var l := UiArt.label(heading, 9, UiArt.GOLD_HI)
		l.position = Vector2(6, 2)
		l.size = Vector2(w - 60, 14)
		p.add_child(l)
		if right != "":
			var r := UiArt.label(right, 8, UiArt.DIM)
			r.position = Vector2(w - 86, 3)
			r.size = Vector2(80, 14)
			r.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			r.name = "Right"
			p.add_child(r)
	return p


func _scroll_list(parent: Control, r: Rect2) -> VBoxContainer:
	var sc := ScrollContainer.new()
	sc.position = r.position
	sc.size = r.size
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	UiArt.themed(sc)
	parent.add_child(sc)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(r.size.x - 10, 0)
	v.add_theme_constant_override("separation", 1)
	sc.add_child(v)
	return v


# ---------------------------------------------------------------- EQUIPMENT

func _build_equipment() -> void:
	var top := HEAD_H + 6
	var h := SIZE.y - top - 10
	# the backpack, filtered by the picked slot
	var bp := _column(COL1.x, COL1.y, top, h, "INVENTORY")
	_filter_label = UiArt.label("", 8, UiArt.CREAM)
	_filter_label.position = Vector2(6, 20)
	_filter_label.size = Vector2(COL1.y - 60, 12)
	_filter_label.clip_text = true
	bp.add_child(_filter_label)
	var all := UiArt.button("ALL", Vector2(40, 13), 7)
	all.position = Vector2(COL1.y - 46, 19)
	all.pressed.connect(func(): pick_slot(-1))
	bp.add_child(all)
	var sc := ScrollContainer.new()
	sc.position = Vector2(4, 36)
	sc.size = Vector2(COL1.y - 6, h - 40)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	UiArt.themed(sc)
	bp.add_child(sc)
	_grid = GridContainer.new()
	_grid.columns = 5
	_grid.add_theme_constant_override("h_separation", 6)
	_grid.add_theme_constant_override("v_separation", 6)
	sc.add_child(_grid)
	for i in PlayerData.SACK * 5:
		var c := HeroCell.new()
		c.panel = self
		c.custom_minimum_size = Vector2(30, 30)
		_grid.add_child(c)
		_cells.append(c)
	# the doll: slots down both sides, the figure between, the weapons under it
	var dp := _column(COL2.x, COL2.y, top, h, "")
	var doll := InventorySheet.DollView.new()
	doll.position = Vector2(50, 10)
	doll.size = Vector2(COL2.y - 100, h - 74)
	dp.add_child(doll)
	doll.build()
	var cell := 34.0
	var gap := (h - 74.0 - DOLL_LEFT.size() * cell) / maxf(1.0, DOLL_LEFT.size() - 1) + cell
	for i in DOLL_LEFT.size():
		_slot(dp, int(DOLL_LEFT[i]), Vector2(8, 10 + i * gap), cell)
	for i in DOLL_RIGHT.size():
		_slot(dp, int(DOLL_RIGHT[i]), Vector2(COL2.y - 8 - cell, 10 + i * gap), cell)
	var wx := (COL2.y - 4 * (cell + 18)) * 0.5
	for i in DOLL_WEAPONS.size():
		_slot(dp, int(DOLL_WEAPONS[i]), Vector2(wx + i * (cell + 18) + 9, h - cell - 18), cell)
		var cap := UiArt.label(["MAIN", "OFF", "TWO-HAND", "RANGED"][i], 7, UiArt.DIM)
		cap.position = Vector2(wx + i * (cell + 18) - 2, h - 16)
		cap.size = Vector2(cell + 22, 10)
		cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		dp.add_child(cap)
	# the stats, always beside the doll
	var st := _column(COL3.x, COL3.y, top, h, "ATTRIBUTES")
	_stats = RichTextLabel.new()
	_stats.bbcode_enabled = true
	_stats.scroll_active = true
	_stats.position = Vector2(6, 20)
	_stats.size = Vector2(COL3.y - 10, h - 24)
	_stats.add_theme_font_override("normal_font", UiArt.font(true))
	_stats.add_theme_font_size_override("normal_font_size", 9)
	_stats.add_theme_color_override("default_color", UiArt.CREAM)
	_stats.mouse_filter = Control.MOUSE_FILTER_PASS
	UiArt.themed(_stats)
	st.add_child(_stats)
	_refresh_all()


func _slot(parent: Control, s: int, at: Vector2, cell: float) -> void:
	var back := Panel.new()
	back.add_theme_stylebox_override("panel", ModernBags._box_style())
	back.position = at
	back.size = Vector2(cell, cell)
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(back)
	var w := HeroSlot.new()
	w.slot = s
	w.panel = self
	w.position = at + Vector2(2, 2)
	w.size = Vector2(cell - 4, cell - 4)
	parent.add_child(w)
	_slots.append(w)


## A slot clicked: the backpack shows only what may go there (-1: everything).
func pick_slot(s: int) -> void:
	filter_slot = -1 if s == filter_slot else s
	_refresh_bag()
	for w in _slots:
		w.queue_redraw()


func _fits(it: Dictionary) -> bool:
	if filter_slot < 0:
		return true
	var where: Array = PlayerData.slots_for(it)
	if filter_slot == 11 and Server.active and int(it.get("item_type", 0)) == 10:
		return true                                        # (a one-hander may go in the off hand: the server decides)
	return filter_slot in where


func _refresh_bag() -> void:
	if _cells.is_empty():
		return
	var order: Array = ModernBags.sorted_slots()
	var shown: Array = []
	for s in order:
		var it := PlayerData.item_at(int(s))
		if filter_slot < 0:
			shown.append(s)
		elif not it.is_empty() and _fits(it):
			shown.append(s)
	if filter_slot >= 0:                                   # the ones you can use first
		var ok := shown.filter(func(s): return Server.active or PlayerData.can_use(PlayerData.item_at(int(s))))
		var no := shown.filter(func(s): return not ok.has(s))
		shown = ok + no
	for i in _cells.size():
		var c = _cells[i]
		c.visible = i < shown.size()
		if c.visible:
			c.slot = int(shown[i])
			c.refresh()
			c.modulate = Color.WHITE if Server.active or PlayerData.can_use(PlayerData.item_at(c.slot)) else Color(1.0, 0.45, 0.4, 0.8)
	if _filter_label:
		if filter_slot < 0:
			_filter_label.text = "EVERYTHING, SORTED"
		else:
			var nm := String(PlayerData.SLOT_NAMES.get(filter_slot, "MYTHICAL")).to_upper()
			_filter_label.text = ("FOR %s: %d" % [nm if nm != "" else "MYTHICAL", shown.size()]) if not shown.is_empty() \
					else "NOTHING FOR %s" % (nm if nm != "" else "MYTHICAL")


## "Garrick Ashford, the Level 50 Armsman" (no last name: "Garrick, the Level 50 Armsman").
func _refresh_who() -> void:
	if _who == null:
		return
	var srv: Dictionary = Server.info if Server.active else {}
	var nm := PlayerData.display_name()
	var last := CharacterSheet._word(srv.get("last_name", "")) if not srv.is_empty() else ""
	if last != "" and not nm.ends_with(last):
		nm += " " + last
	var cls := String(PlayerData.character.get("class_name", ""))
	if cls == "":
		cls = String(ClassDb.cls(PlayerData.class_id()).get("name", ""))
	_who.text = "%s, the Level %d %s" % [nm, PlayerData.level, cls] if cls != "" else "%s, the Level %d" % [nm, PlayerData.level]


func _refresh_stats() -> void:
	if _stats == null:
		return
	var c := PlayerData.character
	var srv: Dictionary = Server.info if Server.active else {}
	var gold := "#" + UiArt.GOLD.to_html(false)
	var hi := "#" + UiArt.GOLD_HI.to_html(false)
	var w := func(v) -> String: return CharacterSheet._word(v)
	var lines: Array = []
	var cls := String(w.call(srv.get("profession", ""))) if not srv.is_empty() else String(c.get("class_name", ""))
	if cls == "":
		cls = String(w.call(srv.get("base_class", ""))) if not srv.is_empty() else ""
	var race := String(w.call(srv.get("race_name", ""))) if not srv.is_empty() else String(c.get("race", ""))
	var lvl := "LEVEL %d" % PlayerData.level
	if Server.active and Server.fight_level > 0 and Server.fight_level < PlayerData.level:
		lvl += "  [color=#ff9a40](FIGHTING AT %d)[/color]" % Server.fight_level
	lines.append("[font_size=11][color=%s]%s[/color][/font_size]" % [hi, PlayerData.display_name().to_upper()])
	lines.append("%s  %s %s" % [lvl, race.to_upper(), cls.to_upper()])
	var title := String(w.call(srv.get("title", ""))) if not srv.is_empty() else ""
	if title != "":
		lines.append("[color=#9a9184]%s[/color]" % title.to_upper())
	lines.append("")
	var ws: Dictionary = Server.weapon_stats if Server.active else {}
	var hp := Server.max_hp if Server.active and Server.max_hp > 0 else int(srv.get("max_health", 0))
	var pairs := [["HIT POINTS", str(hp) if hp > 0 else "-"],
			["WEAPON SKILL", str(int(ws.weapon_skill)) if ws.has("weapon_skill") else "-"],
			["WEAPON DAMAGE", "%.1f" % float(ws.weapon_damage) if ws.has("weapon_damage") else "-"],
			["ARMOR FACTOR", str(int(ws.armor_factor)) if ws.has("armor_factor") else "-"]]
	for pr in pairs:
		lines.append("[color=%s]%s[/color]  %s" % [gold, pr[0], pr[1]])
	lines.append("")
	# the eight stats, two to a line (buffed green, lowered red, the class's own gold)
	var names := ["STRENGTH", "CONSTITUTION", "DEXTERITY", "QUICKNESS", "INTELLIGENCE", "PIETY", "EMPATHY", "CHARISMA"]
	if PlayerData.stats.size() == 8:
		var eff: Array = PlayerData.effective_stats()
		var cells: Array = []
		for i in 8:
			var col := "#eee3c7"
			var buff := int(Server.stat_buffs[i]) if Server.active and Server.stat_buffs.size() == 8 else int(eff[i]) - PlayerData.unmodified_stat(i)
			if (i == 1 and Server.active and Server.con_lost > 0) or buff < 0:
				col = "#ff5040"
			elif buff > 0:
				col = "#5aff5a"
			elif i in PlayerData.class_stats:
				col = hi
			cells.append("[color=%s]%s[/color] [color=%s]%d[/color]" % [gold, names[i].substr(0, 3), col, int(eff[i])])
		for i in 4:
			lines.append("%s        %s" % [cells[i], cells[i + 4]])
	lines.append("")
	if Server.active and Server.resists.size() >= 9:
		var rn := ["CRUSH", "SLASH", "THRUST", "HEAT", "COLD", "MATTER", "BODY", "SPIRIT", "ENERGY"]
		lines.append("[color=%s]RESISTS[/color]" % hi)
		for i in range(0, 9, 3):
			lines.append("  ".join(range(i, i + 3).map(func(k): return "[color=%s]%s[/color] %d%%" % [gold, rn[k], int(Server.resists[k])])))
		lines.append("")
	if not srv.is_empty():
		var rl := int(srv.get("realm_level", 0))
		lines.append("[color=%s]REALM RANK[/color]  %dL%d %s" % [gold, rl / 10 + 1, rl % 10, String(w.call(srv.get("realm_title", ""))).to_upper()])
		lines.append("[color=%s]REALM POINTS[/color]  %d" % [gold, PlayerData.realm_points])
		lines.append("[color=%s]REALM SKILL POINTS[/color]  %d" % [gold, int(srv.get("realm_spec_points", 0))])
		if String(w.call(srv.get("guild", ""))) != "":
			lines.append("[color=%s]GUILD[/color]  %s" % [gold, String(w.call(srv.guild)).to_upper()])
		if String(w.call(srv.get("craft_skill", ""))) != "":
			lines.append("[color=%s]CRAFTING[/color]  %s" % [gold, String(w.call(srv.craft_skill)).to_upper()])
	lines.append("[color=%s]ACTIVE WEAPON[/color]  %s" % [gold, {"standard": "STANDARD", "twohand": "TWO HANDED", "ranged": "RANGED"}.get(PlayerData.active_weapon, "-")])
	if Server.active:
		lines.append("[color=%s]WEIGHT[/color]  %d / %d" % [gold, Server.weight_now, Server.weight_max])
	lines.append("[color=%s]MONEY[/color]  %s" % [gold, PlayerData.money_text().to_upper()])
	_stats.text = "\n".join(lines)


func _inventory_changed() -> void:
	if visible and page == "equipment":
		_refresh_bag()
		for w in _slots:
			w.refresh()
		_refresh_stats.call_deferred()


var _stats_at := 0


func _stats_changed() -> void:
	if not visible:
		return
	_refresh_who()
	var now := Time.get_ticks_msec()
	if now - _stats_at < 250:
		return
	_stats_at = now
	if page == "equipment":
		_refresh_stats()


func _refresh_all() -> void:
	if not visible:
		return
	match page:
		"equipment":
			_refresh_bag()
			for w in _slots:
				w.refresh()
			_refresh_stats()
		"skills":
			_fill_left()
			_fill_training()
			_fill_book()
			for b in _bars:
				b.refresh()


# ---------------------------------------------------------------- SKILLS

func _build_skills() -> void:
	var top := HEAD_H + 6
	var h := SIZE.y - top - 10
	# left: the specializations and the abilities (as the classic skills sheet)
	var lp := _column(COL1.x, COL1.y, top, 150, "SPECIALIZATIONS", "PTS")
	_left_specs = _scroll_list(lp, Rect2(4, 20, COL1.y - 6, 126))
	var ap := _column(COL1.x, COL1.y, top + 156, h - 156, "ABILITIES")
	_left_abil = _scroll_list(ap, Rect2(4, 20, COL1.y - 6, h - 180))
	# centre: your quickbars, then the training list
	var bars := _column(COL2.x, COL2.y, top, 104, "QUICKBARS")
	# Action Combat's style picks, above the bars (owner 2026-11-09: "I'd like the button to be up above the
	# quickbars in the Hero window")
	var acs := UiArt.button("ACTION COMBAT STYLES", Vector2(150, 14), 8)
	acs.position = Vector2(COL2.y - 154, 2)
	acs.tooltip_text = "Pick which style each action-combat move fires"
	acs.pressed.connect(func(): PlayerData.window_toggle.emit("ac_styles"))
	bars.add_child(acs)

	for b in 3:
		var row := MirrorBar.new()
		row.bar = b
		row.panel = self
		row.position = Vector2(4, 20 + b * 27)
		row.size = Vector2(COL2.y - 8, 26)
		bars.add_child(row)
		row.build()
		_bars.append(row)
	var tp := _column(COL2.x, COL2.y, top + 110, h - 110, "SPECIALIZATIONS" if _sub == "spec" else "REALM SKILLS")
	_train_pts = UiArt.label("", 9, UiArt.GOLD_HI)
	_train_pts.position = Vector2(COL2.y - 96, 2)
	_train_pts.size = Vector2(90, 14)
	_train_pts.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	tp.add_child(_train_pts)
	_train_rows = _scroll_list(tp, Rect2(4, 20, COL2.y - 6, h - 110 - 50))
	var train := UiArt.button("TRAIN", Vector2(80, 18), 10)
	train.position = Vector2(COL2.y - 88, h - 110 - 26)
	train.pressed.connect(_train)
	tp.add_child(train)
	var hint := UiArt.label("CLICK A LINE, THEN TRAIN" if _sub == "spec" else "CLICK A SKILL, THEN TRAIN", 7, UiArt.DIM)
	hint.position = Vector2(6, h - 110 - 22)
	hint.size = Vector2(160, 12)
	tp.add_child(hint)
	# right: the spellbook
	var bk := _column(COL3.x, COL3.y, top, h, "")
	_book_head = UiArt.label("", 10, UiArt.GOLD_HI)
	_book_head.position = Vector2(6, 3)
	_book_head.size = Vector2(COL3.y - 140, 14)
	_book_head.clip_text = true
	bk.add_child(_book_head)
	# the controller (owner 2026-11-10 - PadAssign): press its buttons for a slot, then pick the skill
	var pad := UiArt.button("ASSIGN TO CONTROLLER", Vector2(124, 14), 7)
	pad.position = Vector2(COL3.y - 128, 2)
	pad.tooltip_text = "Press the controller buttons for a slot, then pick the skill to put there"
	pad.pressed.connect(func(): PadAssignScript.start(ui))
	bk.add_child(pad)
	_book_sub = UiArt.label("", 8, UiArt.DIM)
	_book_sub.position = Vector2(6, 17)
	_book_sub.size = Vector2(COL3.y - 12, 12)
	bk.add_child(_book_sub)
	_book_list = _scroll_list(bk, Rect2(4, 32, COL3.y - 6, h - 36))
	if visible:
		_ask_server()
	_refresh_all()


## The server's lists for this page: the spellbook and the trainer's (specializations to train, realm skills).
func _ask_server() -> void:
	if not Server.active or Server.client == null:
		return
	Server.request_book()
	_quiet_trainer = Time.get_ticks_msec() + 3000
	Server.client.call("TrainWindow")


var _quiet_trainer := 0


## The server's trainer window arrived: ours if we asked (else an NPC trainer was talked to - GameUI opens us).
func asked_trainer() -> bool:
	return Time.get_ticks_msec() < _quiet_trainer


func _fill_left() -> void:
	if _left_specs == null or not is_instance_valid(_left_specs):
		return
	for l in [_left_specs, _left_abil]:
		for c in l.get_children():
			c.queue_free()
	if Server.active:
		PanelSheets._server_skills([_left_specs, _left_abil])
	else:
		PanelSheets._skills([_left_specs, _left_abil])


func _specs() -> Array:
	return Server.book.specs if Server.active else []


func _fill_training() -> void:
	if _train_rows == null or not is_instance_valid(_train_rows):
		return
	for c in _train_rows.get_children():
		c.queue_free()
	if _sub == "spec":
		_train_pts.text = "POINTS  %d" % (int(Server.book.points) if Server.active else PlayerData.spec_points())
		for sp in _specs():
			var lv := int(sp.level)
			var idx := int(sp.index)
			var row := _pick_row(String(sp.name).to_upper(), str(lv), "NEXT: %d" % (lv + 1),
					lv >= PlayerData.level, idx == _book_spec, func():
						_train_sel = idx
						_book_spec = idx
						_fill_training()
						_fill_book())
			_train_rows.add_child(row)
		if _specs().is_empty():
			_train_rows.add_child(UiArt.label("ASKING THE SERVER..." if Server.active else "TRAINING NEEDS THE SERVER", 8, UiArt.DIM))
	else:
		_train_pts.text = "POINTS  %d" % Server.ra_points
		for ra in Server.realm_abilities:
			var nm := String(ra.name)
			var ok := bool(ra.get("available", not nm.begins_with("[")))
			var idx := int(ra.index)
			var row := _pick_row(nm.trim_prefix("[").trim_suffix("]").to_upper(), str(int(ra.level)), "COST: %d" % int(ra.cost),
					not ok, idx == _train_sel, func():
						_train_sel = idx
						_fill_training())
			_train_rows.add_child(row)
		if Server.realm_abilities.is_empty():
			_train_rows.add_child(UiArt.label("ASKING THE SERVER..." if Server.active else "TRAINING NEEDS THE SERVER", 8, UiArt.DIM))


func _pick_row(name: String, level: String, next: String, dim: bool, picked: bool, on_pick: Callable) -> Control:
	var row := Button.new()
	row.flat = true
	row.focus_mode = Control.FOCUS_NONE
	row.custom_minimum_size = Vector2(COL2.y - 18, 17)
	for k in ["normal", "hover", "pressed", "focus"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(1.0, 0.8, 0.35, 0.16 if picked else (0.07 if k == "hover" else 0.0))
		row.add_theme_stylebox_override(k, sb)
	row.pressed.connect(on_pick)
	var col := UiArt.GOLD_HI if picked else (UiArt.DIM if dim else UiArt.CREAM)
	for part in [[name, 4.0, 150.0, HORIZONTAL_ALIGNMENT_LEFT], [level, 156.0, 24.0, HORIZONTAL_ALIGNMENT_RIGHT],
			[next, 190.0, 72.0, HORIZONTAL_ALIGNMENT_LEFT]]:
		var l := UiArt.label(String(part[0]), 9, col)
		l.position = Vector2(float(part[1]), 1)
		l.size = Vector2(float(part[2]), 15)
		l.horizontal_alignment = part[3]
		l.clip_text = true
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(l)
	return row


func _train() -> void:
	if not Server.active or Server.client == null or _train_sel < 0:
		return
	if _sub == "spec":
		for sp in _specs():
			if int(sp.index) == _train_sel:
				Server.client.call("TrainSpec", int(sp.index), int(sp.level) + 1)
	else:
		for ra in Server.realm_abilities:
			if int(ra.index) == _train_sel:
				Server.train_realm_ability(_train_sel, int(ra.level) + 1)
	get_tree().create_timer(0.6).timeout.connect(_ask_server)


## Your usable skills by name, as the quickbars take them: name|kind -> the drag data (PanelSheets' ids).
func _usable() -> Dictionary:
	var out := {}
	if not Server.active:
		return out
	var first := PanelSheets._first_skill()
	for i in Server.skills.size():
		var sk: Dictionary = Server.skills[i]
		var pg := int(sk.page)
		if pg == 0:
			continue
		var kind: String = "ability" if pg in [1, 5, 6] else ("style" if pg == 2 else "spell")
		var ic: Array = Server.skill_icon("icon" if kind == "ability" else kind, int(sk.icon))
		out[String(sk.name).to_lower()] = {"kind": kind, "id": "srv:skill:%d" % (i - first), "icon": int(ic[0]),
				"border": int(ic[1]), "name": String(sk.name)}
	for li in Server.spell_lines.size():
		for sp in (Server.spell_lines[li].spells as Array):
			var kind := "style" if String(sp.get("kind", "spell")) == "style" else "spell"
			var ic2: Array = Server.skill_icon(kind, int(sp.icon))
			out[String(sp.name).to_lower()] = {"kind": kind, "id": "srv:spell:%d:%d" % [li, int(sp.level)], "icon": int(ic2[0]),
					"border": int(ic2[1]), "name": String(sp.name)}
	return out


func _fill_book() -> void:
	if _book_list == null or not is_instance_valid(_book_list):
		return
	for c in _book_list.get_children():
		c.queue_free()
	var specs := _specs()
	if specs.is_empty():
		_book_head.text = "SPELLBOOK"
		_book_sub.text = "ASKING THE SERVER..." if Server.active else "THE SPELLBOOK NEEDS THE SERVER"
		return
	var spec: Dictionary = {}
	for sp in specs:
		if int(sp.index) == _book_spec:
			spec = sp
	if spec.is_empty():                                    # your highest that teaches anything (Stealth teaches nothing)
		for sp in specs:
			if not (sp.skills as Array).is_empty() and (spec.is_empty() or int(sp.level) > int(spec.level)):
				spec = sp
	if spec.is_empty():
		spec = specs[0]
	_book_spec = int(spec.index)
	_book_head.text = String(spec.name).to_upper()
	var known := (spec.skills as Array).filter(func(k): return bool(k.have)).size()
	_book_sub.text = "LEVEL %d NOW  -  %d OF %d KNOWN" % [int(spec.level), known, (spec.skills as Array).size()]
	var use := _usable()
	# the smart heals (Server.smart_heal_entries) head the book of the specialization whose heals they cast
	var smart: Array = Server.smart_heal_entries()
	var names := {}
	for k in spec.skills:
		names[String(k.name)] = true
	if smart.any(func(s): return names.has(String(s.casts))):
		# two short lines, clipped to the column (owner 2026-11-13: one long line pushed the scroll bar out of the window)
		for t in [["AUTOMATIC HEALS", UiArt.GOLD], ["YOUR BEST OF EACH, ON WHOEVER NEEDS IT MOST", UiArt.DIM]]:
			var sl := UiArt.label(String(t[0]), 8, t[1])
			sl.custom_minimum_size = Vector2(COL3.y - 20, 12)
			sl.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
			sl.clip_text = true
			sl.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
			_book_list.add_child(sl)
		for s in smart:
			var srow := BookRow.new()
			srow.setup(s, 0, true, true, COL3.y - 20, String(s.smart).to_upper())
			_book_list.add_child(srow)
	var group := ""
	for k in spec.skills:
		var g := String(k.group)
		if g != group:
			group = g
			var gl := UiArt.label(g.to_upper(), 8, UiArt.GOLD)
			gl.custom_minimum_size = Vector2(COL3.y - 20, 14)
			gl.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
			_book_list.add_child(gl)
		var data: Dictionary = use.get(String(k.name).to_lower(), {})
		if data.is_empty():
			var ik: String = {"ability": "icon", "style": "style"}.get(String(k.kind), "spell")
			var ic: Array = Server.skill_icon(ik, int(k.icon))
			data = {"kind": String(k.kind) if String(k.kind) != "song" else "spell", "id": "", "icon": int(ic[0]),
					"border": int(ic[1]), "name": String(k.name)}
		var row := BookRow.new()
		row.setup(data, int(k.level), bool(k.have), String(k.group).ends_with("(BASE)"), COL3.y - 20)
		_book_list.add_child(row)
	if specs.size() > 0 and _train_sel < 0 and _sub == "spec":
		_train_sel = _book_spec


func _book_changed() -> void:
	if visible and page == "skills":
		_fill_training()
		_fill_book()
		_fill_left()


func _trainer_changed() -> void:
	if visible and page == "skills" and _sub == "realm":
		_fill_training()


func _skills_changed() -> void:
	if visible and page == "skills" and not _pending_book:
		_pending_book = true                              # (a new skill: the book again, once the lists settle)
		get_tree().create_timer(0.8).timeout.connect(func():
			_pending_book = false
			if visible and page == "skills":
				_fill_left()
				Server.request_book())


# ---------------------------------------------------------------- the inner parts

## The crossed sword and shield in the corner (GW2's Hero crest, in the client's gold).
class Crest extends Control:
	func _draw() -> void:
		var c := size * 0.5
		var g := UiArt.GOLD
		draw_line(c + Vector2(-9, 9), c + Vector2(9, -10), Color(0.75, 0.75, 0.8), 2.5, true)
		draw_line(c + Vector2(-6, 2), c + Vector2(-2, 6), g, 2.0, true)
		var shield := PackedVector2Array([c + Vector2(-2, -8), c + Vector2(9, -8), c + Vector2(9, 1), c + Vector2(3.5, 8),
				c + Vector2(-2, 1)])
		draw_colored_polygon(shield, Color(0.35, 0.3, 0.22))
		draw_polyline(shield + PackedVector2Array([shield[0]]), g, 1.5, true)


## The page list down the left: gold page names, their sub-pages under them; the open one lit.
class Nav extends Control:
	var panel
	const ROW := 22.0
	var _hover := -1

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	# each page a row of its own (owner 2026-11-12: the controller couldn't reach Specialization / Realm Skills - the
	# column was one element to it): the rows take the clicks, the column draws them
	func _ready() -> void:
		for i in PAGES.size():
			var r := NavRow.new()
			r.nav = self
			r.index = i
			r.position = Vector2(0, i * ROW)
			r.size = Vector2(size.x - 2, ROW)
			add_child(r)

	func _rows() -> Array:
		return PAGES

	func pick(i: int) -> void:
		if i >= 0 and i < PAGES.size():
			panel.show_page(String(PAGES[i][0]) if String(PAGES[i][0]) != "skills" else panel._sub)
			if panel.page == "skills":
				panel._ask_server()

	func hover(i: int) -> void:
		if i != _hover:
			_hover = i
			queue_redraw()

	func _draw() -> void:
		var f := UiArt.font(true)
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.03, 0.03, 0.035, 0.45))
		draw_line(Vector2(size.x - 1, 0), Vector2(size.x - 1, size.y), Color(0.45, 0.37, 0.22, 0.8), 1.0)
		for i in PAGES.size():
			var id := String(PAGES[i][0])
			var sub := int(PAGES[i][2]) == 1
			var on: bool = panel.page == id or (panel.page == "skills" and (id == "skills" or (sub and panel._sub == id)))
			var y := i * ROW
			if on and (sub or id == "equipment"):
				draw_rect(Rect2(0, y + 2, size.x - 2, ROW - 4), Color(1.0, 0.8, 0.35, 0.13))
				draw_rect(Rect2(0, y + 2, 3, ROW - 4), UiArt.GOLD_HI)
			elif i == _hover:
				draw_rect(Rect2(0, y + 2, size.x - 2, ROW - 4), Color(1, 1, 1, 0.05))
			var col := UiArt.GOLD_HI if on else (UiArt.CREAM if i == _hover else (UiArt.GOLD if not sub else UiArt.DIM))
			var txt := String(PAGES[i][1])
			var fs := 8 if sub else 10
			draw_string_outline(f, Vector2(22 if sub else 8, y + 15), txt.to_upper() if not sub else txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 2, Color(0, 0, 0, 0.8))
			draw_string(f, Vector2(22 if sub else 8, y + 15), txt.to_upper() if not sub else txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)


class NavRow extends Control:
	var nav
	var index := 0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			nav.pick(index)
			accept_event()

	func _notification(what: int) -> void:
		if what == NOTIFICATION_MOUSE_ENTER:
			nav.hover(index)
		elif what == NOTIFICATION_MOUSE_EXIT and nav._hover == index:
			nav.hover(-1)


## A slot on the Hero doll: a click picks it (the backpack shows what fits), a drag or double-click as everywhere.
class HeroSlot extends InventorySheet.EquipSlot:
	var panel

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT and not event.double_click:
			panel.pick_slot(slot)
			accept_event()
			return
		super._gui_input(event)

	func _draw() -> void:
		if panel and panel.filter_slot == slot:
			draw_rect(Rect2(Vector2(-2, -2), size + Vector2(4, 4)), UiArt.GOLD_HI, false, 2.0)
		if PlayerData.item_at(slot).is_empty():
			var nm := String(PlayerData.SLOT_NAMES.get(slot, "")).to_upper()
			var f := UiArt.font(true)
			draw_string(f, Vector2(0, size.y * 0.5 + 3), nm.substr(0, 6), HORIZONTAL_ALIGNMENT_CENTER, size.x, 6, Color(0.6, 0.57, 0.52, 0.6))


## A backpack square on the Hero page: with a slot picked, one click (or a right-click) wears the item there; with
## none, a right-click wears it where it goes (the bags' own rule).
class HeroCell extends ModernBags.BagCell:
	var panel

	func _gui_input(event: InputEvent) -> void:
		if panel and panel.filter_slot >= 0 and event is InputEventMouseButton and event.pressed \
				and (event.button_index == MOUSE_BUTTON_RIGHT or (event.button_index == MOUSE_BUTTON_LEFT and not event.double_click)) \
				and not PlayerData.entry(slot).is_empty():
			PlayerData.move(slot, panel.filter_slot)
			accept_event()
			return
		super._gui_input(event)


## A copy of one quickbar: its ten slots (the same slots - drop a skill here and it's on the bar) and its page.
class MirrorBar extends Control:
	var bar := 0
	var panel
	var _slots: Array = []
	var _page: Label

	func build() -> void:
		var tag := UiArt.label("%d" % (bar + 1), 9, UiArt.GOLD_HI)
		tag.position = Vector2(0, 5)
		tag.size = Vector2(12, 14)
		add_child(tag)
		var prev := UiArt.button("<", Vector2(12, 22), 8)
		prev.position = Vector2(12, 2)
		prev.pressed.connect(func(): _bank(-1))
		add_child(prev)
		_page = UiArt.label("", 7, UiArt.CREAM)
		_page.position = Vector2(24, 7)
		_page.size = Vector2(12, 12)
		_page.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(_page)
		var nxt := UiArt.button(">", Vector2(12, 22), 8)
		nxt.position = Vector2(36, 2)
		nxt.pressed.connect(func(): _bank(1))
		add_child(nxt)
		for i in 10:
			var back := Panel.new()
			back.add_theme_stylebox_override("panel", ModernBags._box_style())
			back.position = Vector2(52 + i * 22.5, 1)
			back.size = Vector2(22, 22)
			back.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(back)
			var s := Quickbar.QuickSlot.new()
			s.bar = bar
			s.slot = i
			s.position = back.position + Vector2(1, 1)
			s.size = Vector2(20, 20)
			add_child(s)
			s._key.visible = false                          # (the key names don't fit; the bars on screen show them)
			_slots.append(s)
		PlayerData.changed.connect(refresh)
		tree_exiting.connect(func(): PlayerData.changed.disconnect(refresh))
		refresh()

	func bar_tooltip() -> String:
		return "QUICKBAR %d" % (bar + 1)

	func _bank(d: int) -> void:
		var ui: GameUI = panel.ui
		if ui and bar < ui.quickbars.size():
			ui.quickbars[bar].set_bank(PlayerData.quickbar_bank[bar] + d)
		refresh()

	func refresh() -> void:
		if _page:
			_page.text = str(PlayerData.quickbar_bank[bar] + 1)
		for s in _slots:
			s.refresh()


## One spellbook line: the icon, the name, the level that teaches it. Known: full colour, drag onto a bar,
## double-click to use, right-click for its information; not yet: greyed.
class BookRow extends Control:
	var data := {}
	var have := false

	func setup(d: Dictionary, level: int, known: bool, base: bool, w: float, right := "") -> void:
		data = d
		have = known
		custom_minimum_size = Vector2(w, 20)
		mouse_filter = Control.MOUSE_FILTER_STOP
		var ic := TextureRect.new()
		ic.texture = ItemDb.icon(int(d.get("icon", 0)))
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_SCALE
		ic.position = Vector2(2, 1)
		ic.size = Vector2(18, 18)
		ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(ic)
		if int(d.get("border", -1)) >= 0:
			var b := TextureRect.new()
			b.texture = ItemDb.border(int(d.border))
			b.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			b.stretch_mode = TextureRect.STRETCH_SCALE
			b.position = ic.position
			b.size = ic.size
			b.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(b)
		var l := UiArt.label(String(d.get("name", "")).to_upper(), 8, UiArt.CREAM if known else UiArt.DIM)
		l.position = Vector2(26, 3)
		l.size = Vector2(w - 56, 14)
		l.clip_text = true
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(l)
		var lv := UiArt.label(right if right != "" else ("L%d" if base else "%d") % level, 8, UiArt.GOLD if known else UiArt.DIM)
		lv.position = Vector2(w - 30, 3)
		lv.size = Vector2(26, 14)
		lv.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		lv.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(lv)
		if not known:
			ic.modulate = Color(0.35, 0.35, 0.35, 0.9)          # greyed until learned (the owner: the reverse of the old window)
		if right != "":
			lv.position.x -= 14
			lv.size.x += 14
		tooltip_text = String(d.get("name", "")).to_upper() + ("" if known else
				("\nLEARNED AT LEVEL %d" if base else "\nLEARNED AT %d IN THIS SPECIALIZATION") % level)

	func _notification(what: int) -> void:
		if what == NOTIFICATION_MOUSE_ENTER and Server.active and have and String(data.get("id", "")) != "":
			Server.prefetch_skill(data)

	func _make_custom_tooltip(for_text: String) -> Object:
		if have and String(data.get("id", "")) != "":
			return ItemTooltip.skill(data)
		var l := UiArt.label(for_text, 9, UiArt.CREAM)
		return l

	## The pad's buttons on a spellbook line (Pad): A uses it, X tells what it is, Y puts it on a controller button.
	func pad_actions() -> Array:
		if not have or String(data.get("id", "")) == "":
			return []
		var hero = get_parent()
		while hero and not (hero is ClassicWindow):
			hero = hero.get_parent()
		return [["a", "USE", func(): PlayerData.use_skill.emit(data)], ["x", "INFO", func(): PlayerData.skill_info.emit(data)],
				["y", "ASSIGN", func(): PadAssignScript.start(hero.get("ui") if hero else null, data)]]

	func _get_drag_data(_pos: Vector2) -> Variant:
		if not have or String(data.get("id", "")) == "":
			return null
		var prev := TextureRect.new()
		prev.texture = ItemDb.icon(int(data.icon))
		prev.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		prev.size = Vector2(32, 32) * get_global_transform().get_scale()
		set_drag_preview(prev)
		return data.duplicate()

	func _gui_input(event: InputEvent) -> void:
		if not have or String(data.get("id", "")) == "":
			return
		if event is InputEventMouseButton and event.pressed and event.double_click and event.button_index == MOUSE_BUTTON_LEFT:
			PlayerData.use_skill.emit(data)
		elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
			PlayerData.skill_info.emit(data)
			accept_event()
