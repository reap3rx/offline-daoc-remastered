"""Muspelheim's zone build (claude 2026-11-25, "Midgard - the plan", round 3): Dangerous - yellows and oranges everywhere, reds in
the fire giants' east and round the hatchery. The south thread's forge: Gjalpinulva's drakulv keep a hatchery in the wyrm hills of
the north, where her fire-wyrm brood is warmed in the lava and fed; renegade dverge in the south sell them fire; the fire giants of
the east, who hate the dragon's kin, burn anything that comes near. The skeletons of the middle are the dead of an old war; the
fire ants, crabs and ash-folk of the west are the realm's own. The zone's set-piece is a hunt: the Brood-Sire, the hatchery's
great fire wyrm, ranges the hills."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from zbcommon import Build
b = Build(104, 'Muspelheim', 'dangerous', 4.0)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
D = "Gjalpinulva's Hatchery"
# the west: the realm's own
mem("fire ant scavenger", "fire ant scavenger", "blue", faction="ants", roam=200)
mem("fire ant worker", "fire ant worker", "blue", faction="ants", aggro=[40, 300], roam=150)
mem("fire ant gatherer", "fire ant gatherer", "yellow", faction="ants", aggro=[50, 350], roam=150)
mem("sulphur crab", "sulphur crab", "blue", roam=150)
mem("soot harvester", "soot harvester", "yellow", faction="ash", aggro=[50, 400], roam=200)
mem("flame thrower", "flame thrower", "yellow", faction="ash", aggro=[60, 400], roam=150)
mem("ashen spirit", "ashen spirit", "yellow", faction="ash", aggro=[60, 400], roam=200)
mem("fire flower", "fire flower", "blue", aggro=[30, 250], roam=0)
mem("ashmonger", "ashmonger", "yellow", faction="ash", aggro=[60, 400], roam=250)
mem("lava lizard", "lava lizard", "blue", roam=250)
mem("fire toad", "fire toad", "yellow", roam=200)
mem("firecat", "firecat", "orange", aggro=[70, 450], roam=350)
mem("noxious hound", "noxious hound", "yellow", aggro=[60, 450], roam=350)
# the middle: the dead of an old war
mem("burnt skeletal sentry", "burnt skeletal sentry", "yellow", faction="dead", aggro=[60, 400], roam=100)
mem("charred skeletal warrior", "charred skeletal warrior", "orange", faction="dead", aggro=[70, 450], roam=150)
mem("seared skeleton", "seared skeleton", "orange", faction="dead", aggro=[70, 450], roam=150)
mem("mephitic ghoul", "mephitic ghoul", "orange", faction="dead", aggro=[70, 450], roam=200)
mem("fire phantom", "fire phantom", "orange", faction="dead", aggro=[70, 450], roam=200)
# the north: the wyrm hills and the hatchery
mem("young fire wyrm", "young fire wyrm", "orange", faction="brood", guild="of the Brood", aggro=[70, 500], roam=250)
mem("cinder drake", "cinder drake", "red", faction="brood", guild="of the Brood", aggro=[80, 550], roam=150)
mem("brood-keeper", "drakulv protector", "orange", name="drakulv brood-keeper", faction="brood", guild=D, aggro=[70, 500], roam=100)
mem("brood-priest", "drakulv sacrificer", "red", name="drakulv brood-priest", faction="brood", guild=D, aggro=[80, 550], roam=60)
mem("Hatch-Mother Ingrid", "drakulv sacrificer", "red", name="Hatch-Mother Ingrid", size=1.2, faction="brood", guild="Keeper of the Hatchery",
    aggro=[85, 600], roam=40, guards={"brood-keeper": 2})
mem("vapor wraith", "vapor wraith", "orange", aggro=[70, 450], roam=150)
# the south: renegade dverge who sell the drakulv fire
mem("dverge sparker", "dverge sparker", "yellow", faction="dverge", guild="the Fire-Sellers", aggro=[60, 400], roam=150)
mem("dverge igniter", "dverge igniter", "orange", faction="dverge", guild="the Fire-Sellers", aggro=[70, 450], roam=100)
mem("dverge crackler", "dverge crackler", "orange", faction="dverge", guild="the Fire-Sellers", aggro=[70, 450], roam=100)
# the east: the fire giants
mem("fire giant lookout", "fire giant lookout", "orange", faction="giants", aggro=[80, 600], roam=250)
mem("fire giant scout", "fire giant scout", "orange", faction="giants", aggro=[80, 600], roam=350)
mem("fire giant watchman", "fire giant watchman", "red", faction="giants", aggro=[85, 600], roam=150)
mem("fire giant guard", "fire giant guard", "red", faction="giants", aggro=[85, 600], roam=60)
mem("flaming raukomaz", "flaming raukomaz", "orange", faction="flame", aggro=[70, 450], roam=200)
mem("magmatasm", "magmatasm", "orange", faction="flame", aggro=[70, 450], roam=150)
mem("pyrotasm", "pyrotasm", "red", faction="flame", aggro=[80, 500], roam=100)

for i, x, y, r in [("brika_camp", 1290, 125, 80), ("dverge_hold", 570, 1315, 90), ("ragnvald_cairn", 1256, 1148, 40)]:
    b.clear(i, x, y, r, list(m.keys()))
    b.S[-1]["block"] = "all"
b.wild("ant_hills", 160, 540, 470, 860, {"fire ant scavenger": 6, "fire ant worker": 6, "fire ant gatherer": 5, "sulphur crab": 4})
b.wild("sulphur_flats", 160, 300, 470, 540, {"sulphur crab": 6, "fire flower": 4, "lava lizard": 4})
b.wild("ash_fields", 150, 860, 400, 1450, {"soot harvester": 8, "flame thrower": 6, "ashen spirit": 5, "fire flower": 4})
b.wild("ash_road", 380, 900, 880, 1250, {"ashmonger": 10, "noxious hound": 6, "fire toad": 4, "lava lizard": 3})
b.wild("old_battlefield", 420, 450, 1000, 900, {"burnt skeletal sentry": 8, "charred skeletal warrior": 8, "seared skeleton": 6,
                                               "mephitic ghoul": 5, "fire phantom": 3})
b.wild("wyrm_hills", 260, 170, 1240, 480, {"young fire wyrm": 10, "firecat": 4, "noxious hound": 4})
b.camp("hatchery", 760, 300, 16, {"Hatch-Mother Ingrid": 1, "brood-priest": 2, "brood-keeper": 3, "young fire wyrm": 3}, 900)
b.camp("cinder_nest", 948, 336, 12, {"cinder drake": 3, "young fire wyrm": 2}, 600)
b.wild("vapor_vents", 1290, 380, 1480, 520, {"vapor wraith": 4, "firecat": 2})
b.wild("giant_marches", 1050, 300, 1500, 600, {"fire giant lookout": 6, "fire giant scout": 3, "noxious hound": 3})
b.camp("giant_watch", 1420, 960, 14, {"fire giant watchman": 2, "fire giant guard": 2, "fire giant lookout": 2}, 900)
b.wild("burning_east", 1020, 620, 1480, 1380, {"flaming raukomaz": 10, "magmatasm": 3, "noxious hound": 4, "firecat": 3})
b.camp("pyre", 1126, 999, 12, {"pyrotasm": 3, "magmatasm": 2}, 900)
b.wild("fire_sellers", 500, 1420, 640, 1580, {"dverge sparker": 5, "dverge igniter": 2, "dverge crackler": 2})

themes = ["Brika's camp in the north-east (the way in from the Vale)", "The ant hills, sulphur flats and ash fields (west)",
          "The old battlefield of the burnt dead (middle)", "The wyrm hills and Gjalpinulva's hatchery (north) - the Brood-Sire's hunt",
          "The fire giants' marches and the burning east", "The dverge hold of Khizil and the fire-sellers (south)"]
notes = ("Midgard's plan 2026-11-25, round 3: Dangerous; the south thread's hatchery, where the dragon's fire-wyrm brood is warmed; "
         "the set-piece is the Brood-Sire's hunt. Coordinates are zone units (metres x 40).")
tiers = {"Young Wyrm Lord": "purple", "Konung Botolf Redhands": "red", "Lord Fire": "red", "Charred Skeletal Commander": "red",
         "Spirit of Flames": "red", "Sinyr": "red", "maghemoth": "red", "Coal": "orange", "Eld": "orange", "Brimstone": "orange",
         "Sulphine": "orange", "Bright Flame": "orange", "Gokstorm": "orange", "Grogak": "orange", "Bjame": "orange", "Armard": "orange",
         "Olash": "orange", "Sentry Incin": "orange", "Shade of Gunnar": "orange", "Seer of Ancient Dawning": "red"}
factions = {"ants": {"id": 9641, "aggro": 40}, "ash": {"id": 9642, "aggro": 70}, "dead": {"id": 9643, "aggro": 80},
            "brood": {"id": 9644, "aggro": 90, "enemies": ["giants"]}, "dverge": {"id": 9645, "aggro": 75}, "giants": {"id": 9646, "aggro": 90, "enemies": ["brood"]},
            "flame": {"id": 9647, "aggro": 80}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
