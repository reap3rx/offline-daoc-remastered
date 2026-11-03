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
| top left | the **menu bar** - no backing, as GW2's: the sheets' own orbs from control.bmp (character, skills, combat styles, spells, group; lit while open, cyan on hover, name and key on hover), then inventory, quest journal, map and options in the same stone; the **party** under it: a row per member (you first) with level and class, health bar and a thin power bar; click a member to target them |
| top centre | the compass strip |
| top right | the **event tracker** (EventTracker) and the **quest log** under it: each quest's name and its current goal (the server's journal, or the game's own quests offline) |
| bottom right | the **minimap**: the zone's painted map around you (the area map inside a town or dungeon wing), north up, with quest marks, events, your realm's bots and companions; the wheel zooms it, a click opens the map; the zone's name and the clock over it |
| sheets | open beside the party from the menu bar (the same orb again closes it); the panel's painted orbs are covered by a title band with a close cross |
| inventory | the **modern bags** (`game/ui/modern_bags.gd`): what you wear on the left; the backpack as one grid sorted weapons, shields, armour, jewellery, ammunition, poisons, crafting, the rest - higher level and quality first inside each (the client hears no prices, so level and quality stand for value); every square is still its own backpack place (drag, double-click to equip, right-click then Shift+I / U); a search box dims what doesn't match; the **wallet** under it: coins, realm points and every currency (Marks of Valor, the Darkness Falls seals, aurulite, Atlantean glass, dragon scales ...), which leave the grid |

The classic status, target, mini group and time windows are parked while MODERN is on; switching back to CLASSIC puts
them, the quickbars and the compass back at their saved places.

## The map (`game/ui/map_window.gd`)

Modern style: the map opens big in the middle of the screen (WoW's), with a log beside it - the zone's events
(running, resting, waiting, someone asking for help, with stage, time left and levels; click one to look at it on the
map) and your quests with their current goal. Both styles:

- the wheel zooms about the pointer, up to 6x; the left button drags the zoomed map (a click without a drag still
  opens a zone from a realm map); FOLLOW keeps you centred while zoomed;
- hovering a mark names it: a quest mark's kind, an event's name, stage, time left and level range, a bot or a
  companion;
- **sharp when zoomed in**: past about 1.3x the painted map fades into the zone drawn from straight above (every tree,
  path, house and stream where it really is), fully from 2.5x; the painted map's names and markers stay on top at one
  size however far in you are. The minimap does the same.

### The drawn zones (owner 2026-11-02: "making the maps more high-rez, since there are no official ones")

- `godot/tests/map_render.gd`: the offline zone viewer with an orthographic camera straight down, mid-afternoon sun
  (shadows give the hills and trees their shape), no fog, no interface; 8 x 8 tiles of 1024 px stitched, saved as
  `content/maps/render/z<zone>.jpg` (4096 px, about 0.4 m a pixel). About 15 s a zone.
- `pipeline/render_maps.ps1`: every outdoor zone with a whole-zone painted map (67 of them: the three realms, the
  frontiers, the battlegrounds), skipping those already drawn (`-redo` draws them all again). Capitals and dungeons keep
  their painted maps (their map shows part of a zone).
- `pipeline/build_map_labels.py`: lifts the painted map's white names and markers (with their black edge) and the
  yellow arrows to the next zones into `z<zone>_labels.png`, and each one's box into `z<zone>_labels.json`.
- About 410 MB for all of them (content, not in git): run the two scripts after a zone changes.

## Not yet (next passes)

- a real wallet (currencies off the backpack, on the server);
- a modern skin for the character sheet, the spellbook and the chat;
- drawn maps for capitals and dungeon levels; our own names for places the painted maps don't name;
- the quiver, poison and potion bags as HUD buttons; a pet plate by the orb; the raid window;
- art: the orb and plates are drawn (gold rim, dark stone) - a painted orb frame from the client's art would look
  better;
- the minimap in dungeons without an area map falls back to the zone map.

Tests: `new-client/godot/tests/ui_probe.gd` (`livewalk2.ps1 -Probe ui_probe`) shoots the modern HUD with a target
and a party, the zoomed map, and the classic style restored.
