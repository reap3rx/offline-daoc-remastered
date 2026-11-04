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

   A `defend` stage with `"protect_leader": true` protects the giver instead of a spawned NPC: they walk to its
   `center` (the party with them) and, with `"flag": <item model>` (`flag_name`), plant a banner there that stands
   until the party goes home. A defend's protected NPC stays a little after a win to thank you (`thanks`); a giver
   has the last word when the chain ends (`thanks` / `regret` on the giver, a default otherwise).

   | `occupy` | drive out a garrison that holds a place (no time limit; the fallen are replaced every `reinforce_s` while nobody presses them) | `mobs`, `count`, `boss` (their leader), `displace_m` (the realm's NPCs that near are driven off until the chain is won), `health_mult` |

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

## When an event fails

(Owner 2026-11-02: failure should have "real world consequence" - GW2's Queensdale bandits taking the pipes.) Every
chain's boss, march and hold leads, when lost, to `o1`: an `occupy` stage on the way to the nearest town (its monsters
and a leader hold the road, a red area on the map, until driven out), then `o2`: a `defend` while a roadwarden (or
someone of the chain's own) sets the place right - lost, they hold it again. Occupations outlast a restart
(`runtime/server/dynamic-events-state.json`). Built by `tools/claude-version/dynamic_events_gen/occupations.py`
(hand-written words for some chains in its CUSTOM, the rest from the chain's monsters and the town's name).

## Towers

A pilot of two guard towers per realm (`dynamic_events_gen/towers.py`): every hour and a half or so the tower is
attacked (`t1`, defend its sergeant for four minutes); nobody comes within ten minutes of the alarm (`auto_fail_s`)
or the sergeant falls, and it is captured (`c1`: its guards and quartermaster gone, an elite garrison and captain hold
it - a group's fight); retaken, it must be held while they counter-attack (`c2`). While the realm holds it, a
quartermaster (`merchant`, `EventTokenMerchant.cs`) sells for Marks of Valor: armour of each of the realm's types and
its weapons at the tower's level, the tower's own cloak, potions and respec stones (`tools/claude-version/tower_stock.py`).

## Marks of Valor

Every stage won pays Marks of Valor (`event_mark`) to players: `reward.tokens` at gold (silver 70%, bronze 40%), or a
quarter of `xp_pct` when not set. Occupations and towers pay more.

## The classic zones

Every classic PvE zone had two or three chains (2026-11-02; one more each since 2026-11-04, below): one camp (`cull` then `boss`), one `defend` (a local
to keep alive, then their attackers' camp and its leader), and, where the zone has a guarded town, a giver who leads
an `escort` out of town to a camp. They were built by `tools/claude-version/dynamic_events_gen/`: `specs.py` is
the hand-written part (foes, bosses, people, places, lore) and `gen.py` fills in the rest from the database (the
monsters' templates and levels, where they live, the towns' guards for givers and their parties) and the client's
terrain (dry, gentle ground away from towns and buildings; an A* road for escorts, no deep water or cliffs). Edit a
spec and run it again, or edit the zone's JSON by hand.

## One more per zone (2026-11-04)

Every classic zone but the Valley of Bri Leith got one more chain (owner: "add 1 more event chain to each zone, and
making sure there are at least one that's near the starting zones that are lower level"): `dynamic_events_gen/specs_extra.py`,
built into the zone files by `gen_extra.py` (the chains already there are left alone; the new one keeps clear of their
places and gets its occupation stages and a unique reward like the rest). The three starting zones' new chains are
givers in the hub towns - Guardsman Pell in Cotswold (spriggarn in the orchards), Viking Gudrun in Mularn (hobgoblin
pranksters), Guardian Niamh in Mag Mell (the opened barrow) - against the zone's weakest monsters, for new characters;
Silvermine's walking rocks are another low one near the start.

## How a chain starts

- **On its own** (no `giver`): after `first_delay_s`, then every `interval_s`, it becomes a disturbance: the map and
  the tracker show its `hint` ("A cold wind is rising over the southern lake..."). It starts when a player or a bot
  comes within `wake_m` of its first stage (default: that stage's radius + 60 m).
- **From a giver** (`giver`: an NPC with `greet`, `accept`, `reply`, `busy`, `cooldown_s`): they stand at `pos` with
  a cyan ring under their feet and a cyan marker on the map. Talk to them and answer the bracketed keyword and they
  set out with their `guards` (who follow them and fight the chain's monsters). A bot that comes by accepts too.

## Levels

`levels` is who the chain is meant for, and it stays that way: its monsters, boss, giver and guards come at their
own levels whoever turns up. What grows is the size of it: more monsters at once, bigger waves, more boss health
with more people - gently (owner 2026-11-02, after a full group was overrun at the Bri Leith tower siege: alone
you should be overwhelmed, a half group should find it a challenge, a full group little difficulty). The base
numbers (`alive`, `waves.count`, `adds.count`, an ambush's `count`) are for one or two people; four see about half as
many again, eight twice as many, never more. A defend stage's next wave waits while two waves' worth still stand,
so they don't pile up on a group that is holding. An occupation's garrison (`count`) is three fifths for a pair,
the full count for a group. Anyone above its top level is scaled down to that level + 1 against its monsters
(`gameutils/LevelScaling.cs`: less damage out, more in - bots too), as in GW2; lower players are not lifted.
Rewards are a share of your own level's experience and money; reward items (`items`) come in the version for your
level: `named_uniques.py` makes level versions (`<id>_l10` ... `_l50`) of every item marked `"scaled": true`.

The giver and their guards support, they don't carry: half damage to the event's monsters and half damage from them,
so they hold out long enough for you to see they're in trouble.

## Scaling down in the open world

The same rule away from events, per monster: above a monster's level + 3 you fight as that level (docs/LEVEL_BANDS.md).
Kills like that pay a tenth of their experience; their drops are the area's, as if you were that level. An event's
monsters and rewards pay in full.

## Bots

Autonomous bots within about a zone of an event (running, resting, a disturbance or a giver) usually go and help
(six to an event); they are paid in experience and money like players, and wake disturbances and accept givers. A bot
stays with its event until the chain is over - through the rests between stages and along a march - fighting its
nearest monster and recovering in between (`AutonomousWorldBotController.RefreshEventCamp`).

## In game

- `/events` opens the events window (new client): your zone's events, each with START, WAKE and STOP. Typed:
  `/events list`; `/events start <id> [stage]` (at a later stage, to test it), `/events stop <id>`, `/events wake <id>`
  (a disturbance now).
- Event NPCs speak in bubbles over their heads (`#SAY|` lines, `NpcSpeech.cs`); clicking a giver opens the NPC window.
- The server sends the zone's events to the new client every 2 s (`#EV|` lines). The tracker (top right) shows the
  ones you are at; the map shows all of them. An event's monsters carry its title under their name.

## Contribution

Damage to the event's monsters and kills count. Gold: at least half the best share; silver: at least 15%; bronze:
anyone who took part or stood in the area for 15 s. Gold gets the full reward, silver 70%, bronze 40%.
