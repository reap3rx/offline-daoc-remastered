# Dynamic events

GW2-style events: they start on their own, run as chains whose outcome decides what happens next, credit everyone
who takes part, and scale with the people there. A zone's events are one JSON file; the code never changes per zone.

## Adding events to a zone

1. Copy `zones/zone206_valley_of_bri_leith.json` to `zones/zoneNNN_<name>.json` and set `zone`, `region`, `name`
   and `lore`.
2. Write the chains. Each stage is one of three types, given its own text, monsters and places:

   | Type | The players must | Keys |
   | --- | --- | --- |
   | `cull` | defeat `kill` monsters in the area within `time_s` (`alive` about at once) | `mobs` |
   | `defend` | keep `protect` alive for `duration_s` while `waves` come for it | `protect`, `waves` (`from`: where they come from) |
   | `boss` | defeat `boss` within `time_s`; `adds` join while it fights | `boss`, `adds` |

   `on_success` / `on_fail` name the next stage (or `end`). `reward`: `xp_pct` (of a level, at gold),
   `copper_per_level`, and an optional `item` with gold and silver chances.
3. Places are zone metres, as the new client's map shows them: `center`, `pos`, `from` are `[x, y]`.
   `python tools/claude-version/dynamic_events_fill_z.py <file>` adds the ground height to each.
4. Monsters are `NpcTemplate` ids (look, gear, spells) with your own `name`, `level` range and `size`, so the same
   template can be a different creature in another zone.
5. Unique drops for the zone's named monsters and its event bosses: `tools/claude-version/named_uniques/` (one spec
   per zone, applied with `named_uniques.py --apply` while the server is closed).
6. Build the server (the JSON is embedded). A file in `runtime/server/dynamic-events/` replaces the built-in one for
   its zone without a rebuild.

## In game

- `/events` lists the zone's events; `/events start <id>` and `/events stop <id>` run one now (for testing).
- The server sends the zone's events to the new client every 2 s (`#EV|` lines). The tracker (top right) shows the
  ones you are at; the map shows all of them.

## Contribution

Damage to the event's monsters and kills count. Gold: at least half the best share; silver: at least 15%; bronze:
anyone who took part or stood in the area for 15 s. Gold gets the full reward, silver 70%, bronze 40%.
