# The modern interface (first pass)

Owner (2026-11-02, "User Interface"): a first pass at a GW2-style modern UI that still feels like DAoC - common fonts
and textures, a health orb with arcs for endurance and mana, the events and a quest log pushed into the top right,
scalability and readability, a modern map (zoom, drag, detailed information), the whole thing overriding the original
UI with an options toggle between classic and modern.

**Options > INTERFACE > STYLE: CLASSIC / MODERN** (saved as `interface/style` in `user://settings.cfg`; switches live).

## What the modern style does (`game/ui/modern_hud.gd`)

The HUD is a layer of `GameUI`'s root, so UI SCALE applies to it like the rest, and it shares the sheets, chat, journal,
map, merchant and every other window with the classic style.

| where | what |
|---|---|
| bottom centre | the **health orb** (red glass filling to your health, hit points and percent inside), the **endurance arc** up its left and the **power arc** up its right, the **experience arc** along its bottom, your name and level on a plate under it; the **target plate** over it (name in its con colour, health bar and percent; click it = attack on / off) |
| either side of the orb | **quickbars 1 and 2**, laid flat; a third bar lying flat stacks over the right one; your **effects** above the right bar |
| top left | the **party**: a row per member (you first) with level and class, health bar and a thin power bar; click a member to target them |
| top centre | the compass strip |
| top right | the **event tracker** (EventTracker) and the **quest log** under it: each quest's name and its current goal (the server's journal, or the game's own quests offline) |
| bottom right | the **minimap**: the zone's painted map around you (the area map inside a town or dungeon wing), north up, with quest marks, events, your realm's bots and companions; the wheel zooms it, a click opens the map; the zone's name and the clock over it; the **window buttons** under it (CHAR, INV, SKILLS, STYLES, SPELLS, GROUP, QUESTS, MAP, OPTIONS) |

The classic status, target, mini group and time windows are parked while MODERN is on; switching back to CLASSIC puts
them, the quickbars and the compass back at their saved places.

## The map (both styles, `game/ui/map_window.gd` MapView)

- the wheel zooms about the pointer, up to 6x; the left button drags the zoomed map (a click without a drag still
  opens a zone from a realm map); FOLLOW keeps you centred while zoomed;
- hovering a mark names it: a quest mark's kind, an event's name, stage, time left and level range, a bot or a
  companion.

## Not yet (next passes)

- a modern skin for the sheets (inventory sorting / search, the character sheet, the spellbook) and the chat;
- the quiver, poison and potion bags as HUD buttons; a pet plate by the orb; the raid window;
- art: the orb and plates are drawn (gold rim, dark stone) - a painted orb frame from the client's art would look
  better;
- the minimap in dungeons without an area map falls back to the zone map.

Tests: `new-client/godot/tests/ui_probe.gd` (`livewalk2.ps1 -Probe ui_probe`) shoots the modern HUD with a target
and a party, the zoomed map, and the classic style restored.
