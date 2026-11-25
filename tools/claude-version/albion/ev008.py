"""Campacorentin Forest's dynamic events (claude 2026-11-24, "Albion - the plan", round 2): the six old chains kept (the two
tower sieges as they were; the bloated nest moved onto the new nest), and two new ones: the zone's set-piece, the Green Knight's
Game (a boss hunt: Morgana's Green Knight rides into the wood by Caer Ulfwych and offers the beheading game, as he did to Gawain),
and the Thorn-Night (the Crimson bleed the thorn's roots by night). Writes the zone's events file.  python ev008.py <in> <out>"""
import json, sys
from evcommon import mkP, R, mob, path, move_stage, shift_levels, random_chain, occupy
Z = 8
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Campacorentin: the deep old forest between Camelot and the Lethantis scholars. Merlin sleeps in a thorn in the deep wood, "
             "where Nimue sealed him, and the wood itself guards his sleep. Morgana wants what he knows of gates; the white dragon in "
             "the south wants him dead. Lethantis's bred ogres hold the south-west, and the Ulfwych Rangers and the Thornwardens hold "
             "everything else they can.")
ch = {c['id']: c for c in d['chains']}
for st in ch['campacorentin_forest_bloated_spiders']['stages']:
    if st['id'] in ('a1', 'a2'):
        move_stage(st, P, (1290, 800))

OAK = mob(12495, "green man", (18, 20), size=55)
FELL = mob(12496, "oaken fellwood", (20, 22))
SAC = mob(12468, "druid sacrificer", (20, 22), guild="the Crimson")
FSAC = mob(12161, "filidh sacrificer", (19, 21), guild="the Crimson")
MIN = mob(12494, "mindless minion", (18, 20))
THORN_W = {"template": 60167630, "model": 38, "equipment": "eab1762c-33e7-4620-9e02-985d820d0369", "guild": "the Thornwardens"}

GREEN = P(1010, 960)
d['chains'].append(random_chain('cf_green_knight', "The Green Knight's Game", [20, 24],
    "A knight all in green, on a green horse, has ridden out of the wood by Caer Ulfwych with an axe on his shoulder...", 'g1', [
    {"id": "g1", "type": "cull", "name": "The Green Men", "objective": "Cut down the Green Knight's green men",
     "announce": "A knight all in green sits his horse at the edge of the wood by Caer Ulfwych. 'Who will trade me a blow for a blow?' Round him, the wood itself stands up - green men, with leaves for faces.",
     "center": GREEN, "radius": 80, "time_s": 1200, "kill": 14, "alive": 6, "mobs": [OAK, OAK, FELL],
     "success": "The green men fall back into the trees. The Green Knight laughs and climbs down from his horse.",
     "fail": "The green men drive the rangers back into the Caer.", "on_success": "g2", "on_fail": "o1", "reward": R(14, 120, 10)},
    {"id": "g2", "type": "boss", "name": "the Green Knight", "objective": "Answer the Green Knight's game",
     "announce": "The Green Knight sets down his axe and bares his neck: 'Strike, then - and in a year and a day, I strike you.' It's a trick. It's always a trick. Bring everyone.",
     "center": GREEN, "radius": 80, "time_s": 1500,
     "boss": {"template": 60161621, "name": "the Green Knight", "level": 26, "size": 66, "pos": GREEN, "health_mult": 4,
              "guild": "of the Green Chapel"},
     "adds": {"every_s": 40, "count": 2, "mobs": [OAK]},
     "success": "The Green Knight falls - and picks up his own head, and laughs, and rides into the wood. 'Well struck. My lady will be disappointed.' A green girdle lies where he stood.",
     "fail": "The Green Knight rides back into the trees, laughing.", "on_success": "end", "on_fail": "o1",
     "reward": R(35, 260, 22, ["nu008_green_girdle", "nu008_green_chapel_ring"], 40)},
    occupy("o1", "The Green Men Hold the Caer Road", "Drive the green men off the road to Caer Ulfwych",
           "The Green Knight's green men have rooted themselves across the road to Caer Ulfwych.", P(1000, 1000), [OAK, FELL],
           {"template": 12496, "name": "green man elder", "level": 22, "health_mult": 2}),
    ]))

THORN = P(1240, 1150)
d['chains'].append(random_chain('cf_thorn_night', 'The Thorn-Night', [20, 24],
    "Red torches in the deep wood, and chanting at the roots of the thorn...", 't1', [
    {"id": "t1", "type": "defend", "name": "The Roots", "objective": "Keep Thornwarden Cerys alive while she seals the roots",
     "announce": "The Crimson are bleeding the thorn's roots tonight! Thornwarden Cerys has gone to seal them - the sacrificers are coming for her!",
     "center": THORN, "radius": 70, "duration_s": 180, "protect": dict(THORN_W, name="Thornwarden Cerys", level=22, pos=THORN, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(1280, 1200), P(1200, 1120), P(1290, 1110)], "mobs": [SAC, FSAC, MIN]},
     "thanks": "\"Sealed. Sleep, old man. Sleep.\"",
     "success": "The roots are sealed - and the one who led the bleeding steps out of the trees, knife red to the wrist.",
     "fail": "Cerys falls, and the roots drink all night.", "on_success": "t2", "on_fail": "end", "reward": R(12, 100, 8)},
    {"id": "t2", "type": "boss", "name": "the Root-Bleeder", "objective": "Defeat the Root-Bleeder",
     "announce": "The Root-Bleeder, a druid in a red robe: 'He'll wake for my Lady. They all do in the end.'",
     "center": THORN, "radius": 70, "time_s": 1200,
     "boss": {"template": 12468, "name": "the Root-Bleeder", "level": 23, "size": 58, "pos": THORN, "health_mult": 3, "guild": "of the Crimson"},
     "adds": {"every_s": 40, "count": 2, "mobs": [MIN]},
     "success": "The Root-Bleeder falls across the roots, and the thorn's flowers close for the night.",
     "fail": "The Root-Bleeder melts into the dark.", "on_success": "end", "on_fail": "end",
     "reward": R(25, 180, 14, ["nu008_root_bleeder_s_knife_ring"], 35)},
    ], time="night"))
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
