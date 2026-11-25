"""Muspelheim's dynamic events (claude 2026-11-25, "Midgard - the plan", round 3): the four old chains kept, two new - the zone's
set-piece, the Brood-Sire (a boss hunt: the hatchery's great fire wyrm ranges the wyrm hills; its hatchlings swarm first: the south
thread) and the Forge-Fire (the fire giants come down on Khizil's forge for the dverge who sold the brood fire; the forge-master holds
the bellows).
Writes the zone's events file.   python ev104.py <in zone104 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, random_chain, occupy
Z = 104
P0 = mkP(Z)
import geo
def P(x, y):
    # (the grid's lava level, 79.4, wrongly floods Khizil's hold - the dverge stand there in game: take the ground there)
    try:
        return P0(x, y)
    except AssertionError:
        return [x, y, round(geo.h(Z, x, y), 1)]
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Muspelheim: the realm of fire beyond the Vale, with Brika's camp at the way in and the dverge forge of Khizil in the "
             "south. Gjalpinulva's drakulv keep a hatchery in the wyrm hills, warming the dragon's fire-wyrm brood for the day she "
             "wakes; renegade dverge sell them fire-salt; the fire giants of the east hate the dragon's kin and burn everything near.")
WYRM = mob(20022, "young fire wyrm", (24, 26), guild="of the Brood")
HATCH = mob(20022, "fire-wyrm hatchling", (22, 24), guild="of the Brood")
KEEP = mob(60160116, "drakulv brood-keeper", (24, 26), guild="Gjalpinulva's Hatchery")
GIANT = mob(60160878, "fire giant lookout", (25, 27), guild="of the fire giants")
SCOUT = mob(60160879, "fire giant scout", (25, 27), guild="of the fire giants")
DVERGE = {"template": 60157473, "model": 185, "guild": "the Forge of Khizil"}

# ------------------------------------------------------------------ the set-piece: the Brood-Sire (a boss hunt)
HILLS = P(600, 300)
d['chains'].append(random_chain('mu_brood_sire', 'The Brood-Sire', [25, 28],
    "Smoke boiling up from the wyrm hills, and a roar that shakes the ash off the rocks...", 'b1', [
    {"id": "b1", "type": "cull", "name": "The Hatchlings", "objective": "Break the swarm of hatchlings boiling out of the wyrm hills",
     "announce": "The hatchery's brood is loose in the wyrm hills! Break the hatchlings before they reach Brika's camp!",
     "center": HILLS, "radius": 90, "time_s": 900, "kill": 14, "alive": 6, "mobs": [HATCH, HATCH, WYRM, KEEP],
     "success": "The hatchlings break - and over the hills comes their sire, wings open, the air shimmering round it.",
     "fail": "The hatchlings scatter over the hills, and their sire comes for them.", "on_success": "b2", "on_fail": "end",
     "reward": R(12, 140, 10)},
    {"id": "b2", "type": "boss", "name": "the Brood-Sire", "objective": "Hunt down the Brood-Sire",
     "announce": "The Brood-Sire: a fire wyrm the size of a longhouse, the brood's father, lava dripping from its jaws. It ranges the wyrm hills - hunt it down. A fight for many: bring friends.",
     "center": HILLS, "radius": 130, "time_s": 1500,
     "path": [P(600, 300), P(450, 250), P(330, 330), P(500, 420), P(760, 380), P(950, 300), P(800, 220), P(600, 300)],
     "boss": {"template": 60159218, "name": "the Brood-Sire", "level": 29, "size": 95, "pos": HILLS, "health_mult": 4,
              "guild": "Father of the Brood"},
     "adds": {"every_s": 40, "count": 2, "mobs": [WYRM, HATCH]},
     "success": "The Brood-Sire falls in the ash, and its fire goes out. In the hatchery, the eggs go quiet.",
     "fail": "The Brood-Sire flies back to the hatchery, and the hills burn.", "on_success": "end", "on_fail": "end",
     "reward": R(30, 260, 22, ["nu104_brood_sire_s_ember_heart", "nu104_wyrm_wing_mantle"], 40)},
    ]))

# ------------------------------------------------------------------ the Forge-Fire
FORGE = P(560, 1360)
d['chains'].append(random_chain('mu_forge_fire', 'The Forge-Fire', [23, 26],
    "Giants' horns from the east, and the dverge banging their gongs at Khizil's hold...", 'f1', [
    {"id": "f1", "type": "defend", "name": "The Bellows", "objective": "Keep Bellows-Master Durin alive at Khizil's forge",
     "announce": "The fire giants have come down on Khizil's forge - they blame every dverge for the fire sold to the brood! Bellows-Master Durin won't leave the bellows - keep him alive!",
     "center": FORGE, "radius": 70, "duration_s": 180, "protect": dict(DVERGE, name="Bellows-Master Durin", level=25, pos=FORGE, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(640, 1330), P(600, 1270), P(660, 1400)], "mobs": [GIANT, SCOUT]},
     "thanks": "\"The giants think we're all fire-sellers. We're not. But they don't ask.\"",
     "success": "The giants fall back - all but one, in a crown of black iron, who strides up to the forge himself.",
     "fail": "Durin falls, and the giants smash the bellows.", "on_success": "f2", "on_fail": "end", "reward": R(12, 130, 10)},
    {"id": "f2", "type": "boss", "name": "Jarl Surtling", "objective": "Defeat Jarl Surtling of the fire giants",
     "announce": "Jarl Surtling, a fire giant in a crown of black iron: 'The dragon's brood is warmed by your fire, little smiths. We'll put it out.'",
     "center": FORGE, "radius": 80, "time_s": 1200,
     "boss": {"template": 60160877, "name": "Jarl Surtling", "level": 28, "size": 70, "pos": FORGE, "health_mult": 3, "guild": "of the fire giants"},
     "adds": {"every_s": 40, "count": 2, "mobs": [GIANT]},
     "success": "Surtling falls at the forge's door. The dverge put out the fire on his beard, out of courtesy.",
     "fail": "Surtling smashes the forge and walks back east.", "on_success": "end", "on_fail": "end",
     "reward": R(25, 220, 18, ["nu104_surtling_s_iron_crown"], 35)},
    ]))
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
