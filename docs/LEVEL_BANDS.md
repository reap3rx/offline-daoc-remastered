# Zone level bands (2026-11-02)

The owner's request: cohesive levels per zone, the lowest monsters by the starting town and higher further out
(across zone lines), the elite zones kept elite, the Shrouded Isles banded the same way, and dungeons moved along
with their zone. One starting hub per realm, as in the modern game: **Cotswold**, **Mularn**, **Mag Mell** - every new
character (and every new bot) starts there (`starts` in the settings; StartupLocations uses them in place of the
race towns, which stay as towns). Two paths out of the hub at 6-16, then one climb to the realm's dragon zone, with a
hard dead end off a low zone on the way (Llyn Barfog, Raumarik, Sheeroe Hills next to Mag Mell's own zone). `source/server/GameServer/gameutils/LevelBands.cs`, settings in
`gameutils/data/level_bands.json` (embedded; a copy at `runtime/server/level-bands.json` overrides it - set
`"enabled": false` there to turn it off).

## How a monster's level is worked out

Nothing in the database changes. When an outdoor monster spawns (and each respawn) its original level is mapped:

- **Band**: its zone's `[min, max]`.
- **Place in the band**: 65% (`gradient_weight`) how far it stands from the nearest starting town of its region
  (`anchors`, from the server's StartupLocation table) - 0 at the zone's nearest point to a town, 1 at its farthest -
  and 35% where its original level ranked among the zone's monsters, so camps keep their order. Elite zones
  (`"gradient": false`) go by rank alone.
- **Named / bosses**: an original level more than `boss_margin` (8) over the zone's 90th percentile sits up to
  `boss_extra_max` (6) levels over the band. Level 60 and up (raid monsters) is left alone.
- **Dungeons** entered from a banded zone move by as much as the zone moved at the entrance when that is 5 levels or
  more (logged at start). Not the capitals, Darkness Falls (its own ladder for every level), Stonehenge Barrows nor
  the SI end dungeons (`dungeon_exclude`).
- **Dynamic events**: their levels (chains, monsters, givers, guards, bosses) are mapped the same way at load, from
  where they start; their reward items come at the taker's level as before.
- **Loot** follows: random drops and money are made at the monster's live level; a named drop with level versions
  (`<id>_lNN`) comes in the version for the monster's live level; period trinkets and quest pieces stay what they are.

## Scaling down (gameutils/LevelScaling.cs)

Against any ordinary monster you fight as at most **its level + 3**, wherever you are (owner: "only +2 or +3
effective levels no matter where they go ... content is easy, but not trivial"): above that, your damage to it is
(cap / your level)^2 of normal (a level 50 among level 22s: a quarter) and its damage to you (your level / cap)^1.5
(the same: 2.8 times). Lower players are not lifted. Scaled kills pay a tenth of their experience; their drops are
the area's and come as if you were the capped level (no grey-con nothing). Events' monsters: at least the event's
top level + 1.

Only realm-less, non-peaceful database monsters are touched: never guards, merchants, bots, pets or event NPCs. A GM
saving a banded monster writes its original level back.

## The bands

| Albion (from Cotswold) | | Midgard (from Mularn) | | Hibernia (from Mag Mell) | |
|---|---|---|---|---|---|
| Camelot Hills | 1-10 | Vale of Mularn | 1-10 | Shannon Estuary (Mag Mell's zone) | 1-10 |
| Salisbury Plains | 8-16 | East Svealand | 6-16 | Silvermine Mts. | 6-16 |
| Black Mtns. South | 8-16 | West Svealand | 10-20 | Lough Gur | 6-16 |
| Campacorentin Forest | 14-22 | Gotar | 12-22 | Lough Derg (Tir na mBeo) | 12-22 |
| Black Mtns. North | 18-28 | Muspelheim | 18-28 | Connacht (Ardee, the housing gate) | 18-28 |
| Avalon Marsh | 22-32 | Myrkwood Forest | 22-32 | Cliffs of Moher | 24-34 |
| Llyn Barfog | 28-38 | Skona Ravine | 28-38 | Valley of Bri Leith | 28-38 |
| Cornwall | 34-44 | Vanern Swamp | 36-46 | Bog of Cullen | 36-46 |
| Lyonesse | 42-52 | Raumarik | 44-54 | Sheeroe Hills | 42-52 |
| Dartmoor (elite) | 50-60 | Malmohus (elite) | 50-60 | Cursed Forest (elite) | 50-60 |

(The zone names are the client's zone table's: in this data Mag Mell and the Tir na Nog teleporter stand in zone 202
"Shannon Estuary", Tir na mBeo in zone 200 "Lough Derg".)

| Avalon (SI) | | Aegir (SI) | | Hy Brasil (SI) | |
|---|---|---|---|---|---|
| Isle of Glass | 1-20 | Aegir's Landing | 1-20 | Domnann | 1-20 |
| Avalon Isle | 18-32 | Munin Sound | 18-32 | Caillte Garran | 16-30 |
| Dales of Devwy | 28-40 | Gripklosa Mountains | 28-42 | Vigilant Rock | 26-40 |
| Aldland | 34-46 | Delling Crater | 34-48 | Allta Fearann | 34-46 |
| Caldey | 38-50 | Faraheim | 40-52 | Vale of Balor | 40-52 |
| Inishail Island | 42-52 | Modernagrav | 44-56 | World's End | 44-56 |
| Gwyddneau (elite) | 48-60 | Iarnwood (elite) | 48-60 | Cothrom Gorge (elite) | 48-60 |

Not banded: the old frontier zones (Forest Sauvage, Snowdonia, Pennine Mountains, Hadrian's Wall; Uppland, Yggdra
Forest, Jamtland Mountains, Odin's Gate; Mount Collory, Cruachan Gorge, Breifine, Emain Macha), the capitals and the
housing zones.

## Playing together (2026-11-02)

- **Open tapping.** Everyone who does a real share of the work on a monster (a twentieth of its health) gets the
  whole kill's experience, grouped or not; less than that scales up to it. Loot still goes to the one who did most.
- **Chants reach everyone.** A pulsing chant that helps - a Paladin's, Warden's, Bard's, Skald's, Minstrel's speed,
  endurance, resists, heals - takes in every player and bot of the realm within standard spell range (1500) of the
  chanter, grouped or not, and their pets. Stronger chants of a kind win: a Bard's speed sets a Warden's aside
  while it lasts, a low Bard's gives way to a higher Warden's.
- **Out of combat you recover fast** (GW2-style): a player or bot who hasn't fought for a few seconds refills health
  and power in about 12 seconds whatever their level (sitting, 6), endurance in about 6 (walking too; not
  sprinting). In a fight the classic numbers stand.
