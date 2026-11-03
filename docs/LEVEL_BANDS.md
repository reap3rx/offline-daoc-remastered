# Zone level bands (2026-11-02)

The owner's request: cohesive levels per zone, the lowest monsters by each race's starting town and higher further
out (across zone lines), the elite zones kept elite, the Shrouded Isles banded the same way, and dungeons moved along
with their zone. `source/server/GameServer/gameutils/LevelBands.cs`, settings in
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
  more (logged at start: e.g. Keltoi Fogou +9, Spindelhalla -6).
- **Dynamic events**: their levels (chains, monsters, givers, guards, bosses) are mapped the same way at load, from
  where they start. The open world's level scaling (zone top level) follows the live levels.

Only realm-less, non-peaceful database monsters are touched: never guards, merchants, bots, pets or event NPCs. A GM
saving a banded monster writes its original level back.

## The bands

| Albion | | Midgard | | Hibernia | |
|---|---|---|---|---|---|
| Camelot Hills | 1-12 | Vale of Mularn | 1-12 | Lough Derg | 1-12 |
| Black Mtns. South | 1-14 | East Svealand | 1-14 | Connacht | 1-14 |
| Campacorentin Forest | 1-18 | Gotar | 1-18 | Silvermine Mts. | 1-20 |
| Avalon Marsh | 1-20 | Myrkwood Forest | 1-24 | Shannon Estuary | 1-22 |
| Salisbury Plains | 10-24 | West Svealand | 10-22 | Valley of Bri Leith | 18-30 |
| Black Mtns. North | 14-28 | Muspelheim | 20-32 | Cliffs of Moher | 24-36 |
| Cornwall | 22-36 | Skona Ravine | 26-40 | Lough Gur | 30-42 |
| Llyn Barfog | 28-42 | Vanern Swamp | 34-48 | Bog of Cullen | 36-48 |
| Lyonesse | 35-50 | Raumarik (elite) | 46-58 | Cursed Forest (elite) | 46-56 |
| Dartmoor (elite) | 46-58 | Malmohus (elite) | 48-60 | Sheeroe Hills (elite) | 48-60 |

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
