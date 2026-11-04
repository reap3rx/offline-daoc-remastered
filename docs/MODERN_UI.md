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
| bottom centre | the **health orb** (red glass filling to your health, hit points and percent inside), the **endurance arc** up its left and the **power arc** up its right, the **experience arc** along its bottom, your name and level on a plate under it - with, in orange brackets, the level you fight your target at while scaled down to it (`L11 (10)`); the **target plate** over it (name in its con colour, health bar and percent; click it = attack on / off) |
| either side of the orb | **quickbars 1 and 2**, laid flat; a third bar lying flat stacks over the right one; your **effects** above the right bar |
| top left | the **menu bar** - no backing, as GW2's: the sheets' own orbs from control.bmp (HERO and SKILLS - both the Hero panel - and group; lit while open, cyan on hover, name and key on hover), then inventory, quest journal, map and options in the same stone; the **party** under it: a row per member (you first) with level and class, health bar and a thin power bar; click a member to target them |
| top centre | the compass strip |
| top right | the **event tracker** (EventTracker) and the **quest log** under it: each quest's name and its current goal (the server's journal, or the game's own quests offline) |
| bottom right | the **minimap**: the zone's painted map around you (the area map inside a town or dungeon wing), north up, with quest marks, events, your realm's bots and companions; the wheel zooms it, a click opens the map; the zone's name and the clock over it |
| sheets | the Hero panel (below) takes the character, skills, styles and spells sheets; the group sheet still opens beside the party (the same orb again closes it), its painted orbs covered by a title band |
| inventory | the **modern bags** (`game/ui/modern_bags.gd`): only the bags (owner 2026-11-04 - what you wear is in the Hero panel); the backpack as one grid sorted weapons, shields, armour, jewellery, ammunition, poisons, crafting, the rest - higher level and quality first inside each (the client hears no prices, so level and quality stand for value); every square is still its own backpack place (drag, double-click or **right-click to equip** - what can't be worn is selected instead, then Shift+I / U); a search box dims what doesn't match; the **wallet** under it: coins, realm points and every currency (Marks of Valor, the Darkness Falls seals, aurulite, Atlantean glass, dragon scales ...), which leave the grid |

The classic status, target, mini group and time windows are parked while MODERN is on; switching back to CLASSIC puts
them, the quickbars and the compass back at their saved places.

## The wallet (server: `gameutils/PlayerWallet.cs`)

Owner 2026-11-03: "I want inventory to not be a pain and currencies taking slots tend to be just that". Every currency
the game pays in - Marks of Valor (`event_mark`), the Darkness Falls daemon seals (`DiamondSeal`, `SapphireSeal`,
`EmeraldSeal`, `Fiery_Diamond_Seal`, `FreeEmeraldSeal`), `BloodSeal`, `aurulite`, `atlanteanglass`, `dragonscales` -
goes into the character's wallet instead of a backpack slot: whatever lands in the backpack (loot, event rewards, a
trade, an old character's stacks at login) moves there a moment later ("7 Marks of Valor into your wallet."). The
currency merchants (`GameItemCurrencyMerchant` - the event mark, DF seal and ToA merchants - and the keep guard
merchants) take their price from the backpack first, then the wallet. It is kept on the character
(`DOLCharactersXCustomParam` "wallet"), sent to the new client as a `#WAL|` line and shown in the modern inventory's
wallet; `/wallet` lists it in the chat (either style). There is no way to take a currency back out as an item yet
(trading currencies between characters would need it).

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

## The Hero panel (`game/ui/hero_panel.gd`, owner 2026-11-03)

"A GW2 inspired character panel that will have tabs on the left": one window (HERO orb / the character key, SKILLS orb /
the skills, styles and spells keys; Esc closes it) with its pages down the left:

- **EQUIPMENT** - the backpack (sorted as the bags), your figure with every slot around it and the weapons under it, and
  the **attributes** always on the right (level - and the level you fight at -, hit points, weapon skill and damage,
  armour factor, the eight stats coloured buffed / lowered / class, resists, realm rank and points, guild, crafting,
  weapon set, weight, money), so they change as you equip. **Click a slot** and the backpack shows only what fits it
  (offline: what you can't use is red, at the end); click (or right-click) an item then to wear it there; with no slot picked a right-click wears it where it goes; ALL shows everything again.
- **SKILLS > Specialization** - your specializations and abilities on the left (as the classic sheet), a **copy of your
  three quickbars** (the same slots, with their page arrows: drop a skill here and it's on the bar), the **training
  list** (level, next cost; click a line, TRAIN - anywhere, `allow_train_anywhere`), and the **spellbook** on the right:
  everything the picked specialization will teach, grouped (abilities, styles, each spell line - baseline lines marked
  BASE, their spells by character level), in level order. **Known: full colour, drag it onto a bar, double-click to use,
  right-click for its information. Not yet: greyed, the level that teaches it on hover.**
- **SKILLS > Realm Skills** - the realm abilities to train (cost, greyed when you can't yet), the quickbars and spellbook
  as above.
- Later, the owner's list: Appearance and Dyes (under Equipment), Achievements.

An NPC trainer opens the panel on Specialization in the modern style (the classic training window in the classic one).
The server's part (`gameutils/HeroInfo.cs`): `/book` answers `#BOOK|` lines - every trainable spec's abilities, styles and
spells with the level that teaches them and whether you have it (the trainer window's own lists leave out baseline lines);
`#ELV|n` is the level you fight your target at (LevelScaling), sent when it changes (checked each second).

## Scaling the windows (owner 2026-11-03)

"Scalable individual elements by clicking on a corner and dragging, ensuring it stays in ratio" - in the modern style the
Hero panel, the bags, the big map, the journal and the events window have a **grip in their bottom right corner**: drag it
and the whole window scales (0.6x - 2.2x), its shape kept; the **minimap** has its grip in its top left corner (it grows
up and left). Kept in `user://settings.cfg [modern_zoom]`; the classic style puts every window back to its own size. The
rest of the HUD follows UI SCALE.

## Action combat additions (owner 2026-11-03)

- **Options > CONTROLS > ACTION COMBAT CURSOR KEY: HOLD / TOGGLE.** Toggle: a press brings the cursor out, the next
  hides it. Either way a window that wants the pointer (bags, Hero, the big map, journal, options, a merchant ...) brings
  it out as it opens and gives it back when the last one closes - unless you pressed the key meanwhile.
- The combat HUD's layout, the over-the-shoulder camera (side, height) and **the action camera's distance** are kept **per
  character, on the server** (owner: "as portable as possible, so probably server side"): the character's
  `DOLCharactersXCustomParam` "cfg:action_hud" (`v1;side;up;distance;shown parts;lights x;y;flash x;y`), stored with
  `/clientcfg set` a second after a change and sent back at login as `#CFG|action_hud|...` (HeroInfo.cs) - so it moves
  with the database. A copy stays in `user://char_settings/<name>.cfg` for offline play; a character with neither starts
  from the shared settings. The classic camera keeps its own distance.

## Not yet (next passes)

- Appearance / Dyes / Achievements pages in the Hero panel; a modern skin for the chat;
- drawn maps for capitals and dungeon levels; our own names for places the painted maps don't name;
- the quiver, poison and potion bags as HUD buttons; a pet plate by the orb; the raid window;
- art: the orb and plates are drawn (gold rim, dark stone) - a painted orb frame from the client's art would look
  better;
- the minimap in dungeons without an area map falls back to the zone map.

Tests: `new-client/godot/tests/ui_probe.gd` (`livewalk2.ps1 -Probe ui_probe`) shoots the modern HUD with a target
and a party, the zoomed map, and the classic style restored; `tests/hero_probe.gd` the Hero panel's pages, the effective
level and the scaled windows.
