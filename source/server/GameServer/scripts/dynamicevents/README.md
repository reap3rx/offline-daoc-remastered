# Dynamic events

GW2-style events: they start on their own, run as chains whose outcome decides what happens next, credit everyone
who takes part, and scale with the people there. A zone's events are one JSON file; the code never changes per zone.

## Adding events to a zone

1. Copy `zones/zone206_valley_of_bri_leith.json` to `zones/zoneNNN_<name>.json` and set `zone`, `region`, `name`
   and `lore`.
2. Write the chains. Each stage is one of four types, given its own text, monsters and places:

   | Type | The players must | Keys |
   | --- | --- | --- |
   | `cull` | defeat `kill` monsters in the area within `time_s` (`alive` about at once) | `mobs` |
   | `defend` | keep `protect` alive for `duration_s` while `waves` come for it | `protect`, `waves` (`from`: where they come from) |
   | `boss` | defeat `boss` within `time_s`; `adds` join while it fights | `boss`, `adds` |
   | `escort` | go with the chain's giver along `path`; they walk only while someone is with them | `path`, `ambushes` (`at`: the path point, `say`) |

   A `defend` stage with `"protect_leader": true` protects the giver instead of a spawned NPC.

   `on_success` / `on_fail` name the next stage (or `end`); `rest_s` (default 30) is the breather before it.
   `reward`: `xp_pct` (of a level, at gold), `copper_per_level`, and `items`, each with gold and silver chances.
3. Places are zone metres, as the new client's map shows them: `center`, `pos`, `from`, `path` are `[x, y]`.
   `python tools/claude-version/dynamic_events_fill_z.py <file>` adds the ground height to each.
4. Monsters are `NpcTemplate` ids (look, gear, spells) with your own `name`, `level` range and `size`, so the same
   template can be a different creature in another zone.
5. Unique drops for the zone's named monsters and its event bosses: `tools/claude-version/named_uniques/` (one spec
   per zone, applied with `named_uniques.py --apply` while the server is closed).
6. Build the server (the JSON is embedded). A file in `runtime/server/dynamic-events/` replaces the built-in one for
   its zone without a rebuild.

## The classic zones

Every classic PvE zone has two or three chains (2026-11-02): one camp (`cull` then `boss`), one `defend` (a local
to keep alive, then their attackers' camp and its leader), and, where the zone has a guarded town, a giver who leads
an `escort` out of town to a camp. They were built by `tools/claude-version/dynamic_events_gen/`: `specs.py` is
the hand-written part (foes, bosses, people, places, lore) and `gen.py` fills in the rest from the database (the
monsters' templates and levels, where they live, the towns' guards for givers and their parties) and the client's
terrain (dry, gentle ground away from towns and buildings; an A* road for escorts, no deep water or cliffs). Edit a
spec and run it again, or edit the zone's JSON by hand.

## How a chain starts

- **On its own** (no `giver`): after `first_delay_s`, then every `interval_s`, it becomes a disturbance: the map and
  the tracker show its `hint` ("A cold wind is rising over the southern lake..."). It starts when a player or a bot
  comes within `wake_m` of its first stage (default: that stage's radius + 60 m).
- **From a giver** (`giver`: an NPC with `greet`, `accept`, `reply`, `busy`, `cooldown_s`): they stand at `pos` with
  a cyan ring under their feet and a cyan marker on the map. Talk to them and answer the bracketed keyword and they
  set out with their `guards` (who follow them and fight the chain's monsters). A bot that comes by accepts too.

## Levels

`levels` is who the chain is meant for. Its monsters come at that level, or, when the players and bots taking part
are higher, just under theirs (the middle of their levels); bosses two above. Rewards are a share of your level's
experience and money by your level; reward items (`items`) come in the version for your level: `named_uniques.py`
makes level versions (`<id>_l10` ... `_l50`) of every item marked `"scaled": true`.

## Scaling down

A player far above a zone fights its ordinary monsters as if only five levels above them (`gameutils/LevelScaling.cs`):
less damage out, more in. Kills like that pay a tenth of their experience and keep one drop in five. An event's
monsters pay in full and its rewards are paid at your level, so events are where an outleveled zone still pays.

## Bots

Autonomous bots within about a zone of an event (running, resting, a disturbance or a giver) usually go and help
(six to an event); they are paid in experience and money like players, and wake disturbances and accept givers.

## In game

- `/events` lists the zone's events; `/events start <id>` and `/events stop <id>` run one now, `/events wake <id>`
  makes it a disturbance now (for testing).
- The server sends the zone's events to the new client every 2 s (`#EV|` lines). The tracker (top right) shows the
  ones you are at; the map shows all of them. An event's monsters carry its title under their name.

## Contribution

Damage to the event's monsters and kills count. Gold: at least half the best share; silver: at least 15%; bronze:
anyone who took part or stood in the area for 15 s. Gold gets the full reward, silver 70%, bronze 40%.
