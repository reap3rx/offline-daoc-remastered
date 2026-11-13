extends RefCounted
## Your group on the maps (owner 2026-11-12: "Have them appear as a triangle on your map instead of a green circle, and
## assign each one a different color while in the group, with that triangle color next to their name in the group
## window so you can see where they are. Companions will be a star instead of a triangle"), and your companion's ideas
## (PersonalCompanions.Mind: "#CMARK|region|x|y|z|label" - a place it suggests, a star in a ring until you get there).

const PALETTE := [Color8(80, 170, 255), Color8(255, 150, 60), Color8(195, 120, 255), Color8(255, 95, 160),
		Color8(90, 230, 200), Color8(240, 225, 90), Color8(255, 85, 85), Color8(160, 230, 90)]
const MARK_COLOUR := Color8(255, 120, 220)          # the companion's suggestions: its own colour on the map
const MARK_LIFE_MS := 15 * 60 * 1000

static var mark := {}                                 # {zone, pos (zone metres), label, until}
static var _names := {}                               # name -> oid (the world's NPCs), refreshed now and then
static var _names_at := 0


## A member's colour by their place in the group (you not counted).
static func colour_of(index: int) -> Color:
	return PALETTE[posmod(index, PALETTE.size())]


## The group's rows' colours: row i -> its colour (you: none).
static func row_colour(rows: Array, i: int) -> Color:
	var k := 0
	for j in i:
		if not bool((rows[j] as Dictionary).get("me", false)):
			k += 1
	return colour_of(k)


## The members the world shows (not you): [{pos (zone metres), colour, star, name, oid}].
static func members(tree: SceneTree) -> Array:
	var out := []
	var v = tree.current_scene if tree else null
	var npcs = v.get("npcs") if v else null
	if npcs == null:
		return out
	var rows: Array = PlayerData.group_rows()
	if rows.size() <= 1:
		return out
	var comp := String(PlayerData.get_meta("companion", "")) if PlayerData.has_meta("companion") else ""
	var k := 0
	for m in rows:
		if bool(m.get("me", false)):
			continue
		var col := colour_of(k)
		k += 1
		var name := String(m.get("name", ""))
		var oid := int(m.get("oid", 0))
		if oid == 0:
			oid = _oid_by_name(npcs, name)
		var st = npcs.by_oid.get(oid) if oid != 0 else null
		if st == null:
			continue
		out.append({"pos": st.pos, "colour": col, "star": comp != "" and name == comp, "name": name, "oid": oid})
	return out


## The oids the group's marks stand for (the plain bot dots leave them out).
static func member_oids(tree: SceneTree) -> Dictionary:
	var d := {}
	for m in members(tree):
		d[int(m.oid)] = true
	return d


static func _oid_by_name(npcs, name: String) -> int:
	var now := Time.get_ticks_msec()
	if now - _names_at > 1500:
		_names_at = now
		_names.clear()
		for oid in npcs.by_oid:
			var st = npcs.by_oid[oid]
			if st and st.spawn:
				_names[String(st.spawn.get("name", ""))] = int(oid)
	return int(_names.get(name, 0))


static func draw_triangle(ci: CanvasItem, at: Vector2, r: float, col: Color) -> void:
	var pts := PackedVector2Array([at + Vector2(0, -r), at + Vector2(r * 0.9, r * 0.75), at + Vector2(-r * 0.9, r * 0.75)])
	var outline := PackedVector2Array([at + Vector2(0, -r - 1.3), at + Vector2(r * 0.9 + 1.2, r * 0.75 + 0.8),
			at + Vector2(-r * 0.9 - 1.2, r * 0.75 + 0.8)])
	ci.draw_colored_polygon(outline, Color(0.05, 0.03, 0.0))
	ci.draw_colored_polygon(pts, col)


static func draw_star(ci: CanvasItem, at: Vector2, r: float, col: Color) -> void:
	var outer := PackedVector2Array()
	var inner := PackedVector2Array()
	for i in 10:
		var a := -PI / 2.0 + i * PI / 5.0
		var rr := r if i % 2 == 0 else r * 0.45
		inner.append(at + Vector2(cos(a), sin(a)) * rr)
		outer.append(at + Vector2(cos(a), sin(a)) * (rr + 1.3))
	ci.draw_colored_polygon(outer, Color(0.05, 0.03, 0.0))
	ci.draw_colored_polygon(inner, col)


static func draw_member(ci: CanvasItem, at: Vector2, m: Dictionary, scale := 1.0) -> void:
	if bool(m.star):
		draw_star(ci, at, 5.0 * scale, m.colour)
	else:
		draw_triangle(ci, at, 4.0 * scale, m.colour)


## "#CMARK|region|x|y|z|label": your companion's idea, on the maps.
static func set_mark(line: String) -> void:
	var f := line.substr(7).split("|")
	if f.size() < 5:
		return
	var region := int(f[0])
	var gx := float(f[1])
	var gy := float(f[2])
	var gz := float(f[3])
	var zone := Server.zone_at(region, gx, gy)
	if zone < 0:
		return
	mark = {"zone": zone, "pos": Server.to_local(zone, gx, gy, gz), "label": f[4] if f.size() > 4 else "",
			"until": Time.get_ticks_msec() + MARK_LIFE_MS}


## The mark, while it lasts (gone when it runs out or you get there).
static func live_mark(zone: int, you: Vector3) -> Dictionary:
	if mark.is_empty() or Time.get_ticks_msec() > int(mark.until):
		mark = {}
		return {}
	if int(mark.zone) == zone and Vector2(you.x, you.z).distance_to(Vector2(mark.pos.x, mark.pos.z)) < 25.0:
		mark = {}
		return {}
	return mark if int(mark.zone) == zone else {}


static func draw_mark(ci: CanvasItem, at: Vector2) -> void:
	var pulse := 0.6 + 0.4 * sin(Time.get_ticks_msec() / 300.0)
	ci.draw_circle(at, 9.0, Color(MARK_COLOUR.r, MARK_COLOUR.g, MARK_COLOUR.b, 0.18 * pulse))
	ci.draw_arc(at, 8.0, 0.0, TAU, 24, Color(MARK_COLOUR, 0.9), 1.5)
	draw_star(ci, at, 4.5, MARK_COLOUR)
