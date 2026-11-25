"""Lyonesse's dynamic events (claude 2026-11-24, "Albion - the plan", round 3): the four old chains kept, and two new ones: the
zone's set-piece, the White Storm (a boss hunt: the storm-wyrm, the white dragon's weather given a body, comes ashore on the north
rock), and the Black Sail (night: Isolde's ghost-ship comes in to the old harbour). Writes the zone's events file."""
import json, sys
from evcommon import mkP, R, mob, path, move_stage, shift_levels, random_chain, occupy
Z = 10
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Lyonesse, Tristan's country, drowned by the sea - and the sea is rising again under a white storm out of the south, the "
             "white dragon's weather. The drowned folk live their last day over and over, the priests of Arawn bargain at the ruined "
             "cathedral, and the cailleach keeps her ring in the mire. Only the Remnant's camp on the south-east rise is quiet.")
PEAL = mob(12974, "storm-peallaidh", (44, 46))
CALLER = mob(12075, "storm-caller", (45, 47), guild="the White Wind")
SAILOR = mob(12952, "drowned sailor", (44, 46))
REMNANT = {"template": 60167630, "model": 28, "equipment": "38762ab0-5f99-47cd-85b0-0bfaa37d71f9", "guild": "the Lyonesse Remnant"}
HARPER = {"template": 60167630, "model": 38, "equipment": "eab1762c-33e7-4620-9e02-985d820d0369", "guild": "the Harpers of Tristan"}

ROCK = P(1190, 520)
d['chains'].append(random_chain('ly_white_storm', 'The White Storm', [46, 50],
    "A white storm out of a clear sky over the north rock - and something is moving inside it...", 'w1', [
    {"id": "w1", "type": "cull", "name": "The Storm-Line", "objective": "Break the storm-callers and the sea-things on the north rock",
     "announce": "The white storm has come ashore on the north rock, and the storm-callers are singing it bigger! Break them!",
     "center": ROCK, "radius": 90, "time_s": 1200, "kill": 14, "alive": 6, "mobs": [PEAL, PEAL, CALLER],
     "success": "The singing stops - and the storm draws itself together into a shape, white as bone, with wings.",
     "fail": "The storm rolls inland over Lyonesse.", "on_success": "w2", "on_fail": "o1", "reward": R(14, 180, 14)},
    {"id": "w2", "type": "boss", "name": "the Storm-Wyrm", "objective": "Bring down the Storm-Wyrm",
     "announce": "The Storm-Wyrm - the white dragon's weather given a body - coils over the rock. It's a fight for a group, and more.",
     "center": ROCK, "radius": 90, "time_s": 1500,
     "boss": {"template": 12959, "name": "the Storm-Wyrm", "level": 52, "size": 75, "pos": ROCK, "health_mult": 4, "model": 105,
              "guild": "the White Dragon's Weather"},
     "adds": {"every_s": 40, "count": 2, "mobs": [PEAL, CALLER]},
     "success": "The Storm-Wyrm tears apart into rain, and the rain is only rain. Far to the south, a dragon screams.",
     "fail": "The Storm-Wyrm rolls inland, and the sea rises behind it.", "on_success": "end", "on_fail": "o1",
     "reward": R(35, 320, 26, ["nu010_storm_wyrm_s_eye", "nu010_white_squall_mantle"], 40)},
    occupy("o1", "The Storm Holds the North Shore", "Drive the storm's creatures off the north shore",
           "The white storm's creatures have come ashore and hold the north shore.", P(1250, 620), [PEAL, CALLER],
           {"template": 12974, "name": "storm-tossed peallaidh", "level": 48, "health_mult": 2}),
    ]))

HARBOUR = P(430, 250)
d['chains'].append(random_chain('ly_black_sail_night', 'The Black Sail', [44, 48],
    "A ship with a sail half black, half white, is coming in to the old harbour - and it's crewed by the drowned...", 'b1', [
    {"id": "b1", "type": "defend", "name": "The Harbour", "objective": "Keep Harper Morwenna alive while she sings the ship in",
     "announce": "Isolde's ghost-ship is coming in to the old harbour, as it does once a year! Harper Morwenna of the Harpers has gone to sing it in - and its drowned crew will take her for an enemy.",
     "center": HARBOUR, "radius": 70, "duration_s": 180, "protect": dict(HARPER, name="Harper Morwenna", level=46, pos=HARBOUR, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(400, 220), P(460, 270), P(400, 280)], "mobs": [SAILOR, SAILOR]},
     "thanks": "\"She's in. She's always in, in the song. Now she's in, in the world.\"",
     "success": "The ship grinds onto the sand - and its drowned captain steps down, still waiting for Tristan.",
     "fail": "Morwenna falls, and the ship sails out again.", "on_success": "b2", "on_fail": "end", "reward": R(12, 160, 12)},
    {"id": "b2", "type": "boss", "name": "the Black Sail's Captain", "objective": "Lay the Black Sail's captain to rest",
     "announce": "The ship's captain, drowned three hundred years: 'Is he alive? She bade me hurry. Is he alive?' He won't hear the answer. Bring friends.",
     "center": HARBOUR, "radius": 70, "time_s": 1200,
     "boss": {"template": 12952, "name": "the Black Sail's Captain", "level": 48, "size": 60, "pos": HARBOUR, "health_mult": 3},
     "adds": {"every_s": 40, "count": 2, "mobs": [SAILOR]},
     "success": "The captain sinks to his knees on the sand. 'Tell her I hurried,' he says. The ship is gone at dawn.",
     "fail": "The ship sails out on the tide.", "on_success": "end", "on_fail": "end",
     "reward": R(25, 240, 18, ["nu010_white_sail_ribbon"], 35)},
    ], time="night"))
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
