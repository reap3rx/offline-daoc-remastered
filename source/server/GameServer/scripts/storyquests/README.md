# Story quests

Hand-written quests that send you out of town into the corners of each zone (owner 2026-11-05: "quality of quests over
quantity ... someone who's worried about their reckless brother who has gone missing ... some good outcomes, some
tragic outcomes"). They sit beside the dynamic events: events are public and happen to the world, story quests are
yours. A quest's fights can be set-pieces built from the event stages (`encounter` steps), run for you and your group
only.

## A quest file

`quests/<realm>_<zone>.json` (built into the server; a file of the same name in `runtime/server/story-quests/`
replaces it without a rebuild):

- `npcs`: the people - `id`, `zone`, `pos` ([x, y] zone metres), `name`, `model` or `template`, `level`, `guild`,
  `idle` (said on a click when they have nothing for you), `during` (["quest/step", ...]: there only while someone is
  on one of those steps - a herald, a son come home), `hostile`.
- `quests`: `id`, `title`, `level` (`min_level`, default level - 3), `giver` (an npc id), `offer` (what they say on a
  click, with [keywords]), `accept` (the keyword that takes it), `topics` (other keywords: their answers), `summary`
  (the journal line), `group` (a group's quest: GROUP in the log and the giver says so; spawned monsters grow +15% a
  person, at most double), `requires` (a quest id), `classes`, `kind` ("epic" later).
- `steps`, in order (`next` jumps, `ending` finishes):

  | type | you | keys |
  | --- | --- | --- |
  | `talk` | speak to `npc` (a click; with `keyword`, answer it) | `say` |
  | `reach` | come within `radius` m of `at` | `text` |
  | `search` | click the `clue` (an object only you see there) at `at` | `clue` {name, model}, `text` |
  | `kill` | defeat `count`: monsters spawned for you around `at` (`mob`), or ones already there by name (`target`) | |
  | `encounter` | win a chain of dynamic-event `stages` (boss, defend, cull) that starts when you come within `wake_m` of `at` | `stages` |
  | `choice` | answer `npc` with one of `options` (each: `keyword`, `say`, `next` or `ending`) | `say` |

  Any step can `give` a story item ({name}: kept in the quest, shown in the journal; {id}: a real item).
- `endings`: `text`, `tragic`, `rewards` (default: the quest's `rewards`).
- `rewards`: `xp_pct` (of a level at the quest's level; well past it, a tenth), `copper_per_level`, `marks` (Marks of
  Valor), `items` (ids), `choice` (pick one: the turn-in NPC names them in [brackets]).

Places are filled with heights by `tools/claude-version/story_quests_fill_z.py <file>` (outdoors from the client's
height grid, in dungeons from the nearest NPC spawn).

## Rewards

A spec of items per zone, in the named_uniques format: `tools/claude-version/named_uniques/storyNNN_<zone>.json`
(name, base slot, level, bonuses, lore, `scaled` for level versions). `python tools/claude-version/story_items.py
<spec>` writes the full rows to `items/<spec>.json`; the server adds them to its database at every start
(`StoryItemsUpdate`). A reward comes in the version for your level (as event rewards do).

## In game

- Givers wear the yellow `!`; whoever your current step needs, the green `?`. The journal shows the step's goal, the
  map and minimap its place (the minimap's rim points to it when it's off the edge).
- `/storyquest list | start <id> [step] | step <id> <step> | done <id> | reset <id> | reload` (testing).

## Written short

Most zones' quests (every zone with dynamic events, beyond Camelot Hills) are written as Python with the helpers in
`tools/claude-version/story_gen.py` - `story_alb.py`, `story_mid.py`, `story_hib.py` - which writes each zone's
quest file and reward spec and checks them (people, steps, endings, keywords, reward ids). Then `story_items.py` on
each spec and `story_quests_fill_z.py` on each quest file, as above:

    python tools/claude-version/story_gen.py story_alb story_mid story_hib
