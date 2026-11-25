"""Cornwall's dynamic events (claude 2026-11-24, "Albion - the plan", round 3): the four old chains kept, and two new ones: the
zone's set-piece, the Eagle Marches (a boss hunt: the Drowned Ninth march out of Cardova behind their legate and their eagle),
and the Bucca Storm (the white storm drives the buccas ashore at the cliff-foot). Writes the zone's events file."""
import json, sys
from evcommon import mkP, R, mob, path, move_stage, shift_levels, random_chain, occupy
Z = 6
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Cornwall: giants' country since Corineus wrestled Gogmagog off its cliffs. The Ghostly Church keeps Gorlois's knights, the "
             "beech woods keep the old fae, and out of the Catacombs of Cardova march the Drowned Ninth, a lost legion the giants have "
             "bound to dig their quarry. Cornwall Station is Albion's hard start: only the moor round it is gentle.")
LEG = mob(12884, "drowned legionnaire", (36, 38), guild="the Drowned Ninth")
CEN = mob(12720, "drowned centurion", (38, 40), guild="the Drowned Ninth")
BUC = mob(12874, "storm-bucca", (24, 26))
MUR = mob(12862, "muryan", (22, 24))
OATH = {"template": 60167630, "model": 28, "equipment": "38762ab0-5f99-47cd-85b0-0bfaa37d71f9", "guild": "the Oath of Corineus"}

ROAD = P(1000, 1240)
d['chains'].append(random_chain('cw_eagle_marches', 'The Eagle Marches', [36, 42],
    "Trumpets under the earth - the Drowned Ninth are marching out of Cardova behind their eagle...", 'e1', [
    {"id": "e1", "type": "cull", "name": "The Column", "objective": "Break the Ninth's marching column",
     "announce": "The Drowned Ninth are marching out of Cardova in full column, eagle at the front, to dig for the giants! Break the column!",
     "center": ROAD, "radius": 90, "time_s": 1200, "kill": 16, "alive": 7, "mobs": [LEG, LEG, CEN],
     "success": "The column breaks - and the eagle-bearer turns to face you, the legate beside him.",
     "fail": "The Ninth march on to the giants' quarry.", "on_success": "e2", "on_fail": "o1", "reward": R(14, 160, 12)},
    {"id": "e2", "type": "boss", "name": "the Aquilifer", "objective": "Defeat the Aquilifer of the Ninth",
     "announce": "The Aquilifer, the eagle-bearer, lifts the gilt eagle high: 'The eagle does not fall while I stand!' A fight for a group.",
     "center": ROAD, "radius": 90, "time_s": 1500,
     "boss": {"template": 12720, "name": "the Aquilifer of the Ninth", "level": 42, "size": 64, "pos": ROAD, "health_mult": 4, "guild": "the Drowned Ninth"},
     "adds": {"every_s": 40, "count": 2, "mobs": [LEG, CEN]},
     "success": "The Aquilifer falls, and the eagle with him. For one night the Ninth lie down along the road.",
     "fail": "The Aquilifer leads the column on.", "on_success": "end", "on_fail": "o1",
     "reward": R(35, 280, 24, ["nu006_aquilifer_s_lion_skin", "nu006_gilt_eagle_feather"], 40)},
    occupy("o1", "The Ninth Hold the Downs Road", "Drive the Ninth off the downs road",
           "The Drowned Ninth have dug in across the downs road, as a legion does.", P(1150, 1180), [LEG, CEN],
           {"template": 12720, "name": "drowned optio", "level": 40, "health_mult": 2}),
    ]))

CLIFF = P(1250, 300)
d['chains'].append(random_chain('cw_bucca_storm', 'The Bucca Storm', [22, 28],
    "A white squall out of a clear sky over the north cliffs - and the buccas are coming up out of the sea with it...", 'b1', [
    {"id": "b1", "type": "defend", "name": "The Cliff-Foot", "objective": "Keep Oath-Keeper Tamsin alive while she lights the storm-beacon",
     "announce": "A white storm is driving the buccas up the north cliffs! Oath-Keeper Tamsin is lighting the old storm-beacon to turn them back.",
     "center": CLIFF, "radius": 70, "duration_s": 180, "protect": dict(OATH, name="Oath-Keeper Tamsin", level=26, pos=CLIFF, health_mult=8, model=38),
     "waves": {"every_s": 24, "count": 3, "from": [P(1220, 260), P(1290, 270), P(1240, 340)], "mobs": [BUC, BUC, MUR]},
     "thanks": "\"Lit! Let the sea see it, and remember.\"",
     "success": "The beacon flares and the squall breaks - and out of the spray comes the bucca who called it.",
     "fail": "Tamsin falls, and the storm takes the cliff.", "on_success": "b2", "on_fail": "end", "reward": R(12, 120, 10)},
    {"id": "b2", "type": "boss", "name": "Bucca Gwidden", "objective": "Defeat Bucca Gwidden",
     "announce": "Bucca Gwidden, the white bucca of the storm: 'The white one in the clouds pays better than your fish-bones.' Bring friends.",
     "center": CLIFF, "radius": 70, "time_s": 1200,
     "boss": {"template": 12874, "name": "Bucca Gwidden", "level": 28, "size": 62, "pos": CLIFF, "health_mult": 3},
     "adds": {"every_s": 40, "count": 2, "mobs": [BUC]},
     "success": "Bucca Gwidden dissolves into spray, and the sea goes calm.", "fail": "Gwidden drives the storm inland.",
     "on_success": "end", "on_fail": "end", "reward": R(25, 200, 16, ["nu006_white_bucca_s_shell"], 35)},
    ]))
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
