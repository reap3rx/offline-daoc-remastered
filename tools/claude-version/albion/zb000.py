"""Camelot Hills' zone build (claude 2026-11-24, "Albion - the plan" in Zone Reviews; owner: "allow you to make most of the
decisions"): Peaceful - the realm's heartland round Cotswold, Camelot's gate and Prydwen Keep, mostly greens and blues. The
north-west thread's first signs: the Crimson cult works in Mithra's Tomb under Camelot's nose (the tomb mouth is the zone's hot
spot, yellows), and the dwarven 'pilgrims' on the north road are its converts. Bandits are gathered into three camps (the Camelot
road, the eastern ridge, the old fort south of the river) instead of being everywhere. The Difwych brothers - Arthur's huntsmen
gone wild after Camlann - hunt the eastern hills with their hounds. Demons creep out of Darkness Falls' mouth. About 950."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(0, 'Camelot Hills', 'peaceful', 1.45)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
# critters and wildlife
mem("brownie", "brownie", "grey", roam=300)
mem("small snake", "small snake", "grey", roam=250)
mem("boar piglet", "boar piglet", "grey", roam=250)
mem("gray wolf pup", "gray wolf pup", "green", roam=350)
mem("wild sow", "wild sow", "green", roam=350)
mem("young boar", "young boar", "green", roam=350)
mem("snake", "snake", "green", roam=300)
mem("grass snake", "grass snake", "green", roam=300)
mem("giant frog", "giant frog", "green", roam=300)
mem("small bear", "small bear", "green", roam=350)
mem("bear", "bear", "blue", roam=350)
mem("gray wolf", "gray wolf", "blue", roam=450)
mem("black wolf", "black wolf", "blue", roam=450)
mem("emerald snake", "emerald snake", "blue", roam=300)
mem("adder", "adder", "blue", roam=300)
mem("plague spider", "plague spider", "blue", roam=250)
mem("river spriteling", "river spriteling", "green", roam=250)
mem("river sprite", "river sprite", "blue", roam=250)
mem("river drake hatchling", "river drake hatchling", "green", roam=250)
mem("river drakeling", "river drakeling", "blue", roam=250)
mem("boulderling", "boulderling", "blue", roam=150)
# the fae (spriggarns and the faerie ring north of the lake)
mem("spriggarn", "spriggarn", "green", faction="spriggarns", aggro=[40, 300], roam=300)
mem("spriggarn elder", "spriggarn elder", "blue", faction="spriggarns", aggro=[50, 350], roam=200)
mem("brownie nomad", "brownie nomad", "green", faction="spriggarns", aggro=[30, 250], roam=350)
mem("faerie mischief-maker", "faerie mischief-maker", "green", faction="faeries", aggro=[40, 300], roam=200)
mem("faerie wolf-crier", "faerie wolf-crier", "blue", faction="faeries", aggro=[50, 350], roam=200)
mem("faerie bell-wether", "faerie bell-wether", "blue", faction="faeries", aggro=[50, 350], roam=150)
# the ants of the north-east hills
mem("dragon ant worker", "dragon ant worker", "green", faction="ants", aggro=[30, 300], roam=250)
mem("dragon ant soldier", "dragon ant soldier", "blue", faction="ants", aggro=[60, 400], roam=250)
mem("dragon ant drone", "dragon ant drone", "blue", faction="ants", aggro=[50, 350], roam=300)
mem("dragon ant queen", "dragon ant queen", "yellow", faction="ants", aggro=[80, 400], size=1.3, roam=30,
    guards={"dragon ant soldier": 2})
# the bandits
mem("young cutpurse", "young cutpurse", "green", faction="bandits", guild="the Camelot Road Gang", aggro=[60, 400], roam=200)
mem("cutpurse", "cutpurse", "green", faction="bandits", guild="the Camelot Road Gang", aggro=[60, 400], roam=200)
mem("bandit", "bandit", "green", faction="bandits", guild="the Camelot Road Gang", aggro=[70, 450], roam=200)
mem("bandit henchman", "bandit henchman", "blue", faction="bandits", guild="the Camelot Road Gang", aggro=[75, 450], roam=200)
mem("bandit thaumaturge", "bandit thaumaturge", "blue", faction="bandits", guild="the Camelot Road Gang", aggro=[75, 450], roam=150)
mem("bandit lieutenant", "bandit lieutenant", "yellow", faction="bandits", guild="the Camelot Road Gang", aggro=[80, 500], roam=150,
    guards={"bandit henchman": 1})
mem("bandit leader", "bandit leader", "orange", faction="bandits", guild="the Camelot Road Gang", aggro=[85, 500], size=1.15, roam=60,
    guards={"bandit lieutenant": 1, "bandit thaumaturge": 1})
mem("young poacher", "young poacher", "green", faction="bandits", aggro=[50, 350], roam=250)
# the Difwych brothers' hunt (east)
mem("hound of the Difwych", "black wolf", "blue", name="hound of the Difwych", faction="difwych", aggro=[80, 500], roam=350)
mem("Difwych huntsman", "bandit henchman", "blue", name="Difwych huntsman", faction="difwych", guild="the Difwych Hunt",
    aggro=[80, 500], roam=200)
# the restless dead round Mithra's Tomb and the barrow fields
mem("puny skeleton", "puny skeleton", "green", faction="dead", aggro=[80, 400], roam=150)
mem("skeleton", "skeleton", "blue", faction="dead", aggro=[85, 450], roam=150)
mem("large skeleton", "large skeleton", "blue", faction="dead", aggro=[85, 450], roam=150)
mem("decayed zombie", "decayed zombie", "green", faction="dead", aggro=[80, 400], roam=150)
mem("putrid zombie", "putrid zombie", "blue", faction="dead", aggro=[85, 450], roam=150)
mem("rotting zombie", "rotting zombie", "yellow", faction="dead", aggro=[90, 450], roam=120)
mem("spirit", "spirit", "blue", faction="dead", aggro=[60, 400], roam=300)
mem("undead filidh", "undead filidh", "yellow", faction="dead", aggro=[90, 500], roam=150)
# the Crimson cult at Mithra's Tomb (the north-west thread's first sign)
mem("crimson acolyte", "Crimson Initiate", "blue", size=0.9, name="crimson acolyte", faction="crimson", guild="the Crimson", aggro=[90, 500], roam=120)
mem("crimson initiate", "Crimson Initiate", "yellow", name="crimson initiate", faction="crimson", guild="the Crimson", aggro=[90, 550], roam=100)
mem("crimson tomb-warden", "Crimson Initiate", "orange", name="crimson tomb-warden", faction="crimson", guild="the Crimson",
    aggro=[95, 550], size=1.15, roam=60, guards={"crimson acolyte": 2})
mem("convert guard", "convert guard", "blue", faction="converts", aggro=[60, 400], roam=80)
# Darkness Falls' mouth
mem("manes demon", "manes demon", "yellow", faction="demons", aggro=[100, 500], roam=150)
mem("grumoz demon", "grumoz demon", "orange", faction="demons", aggro=[100, 550], roam=120)
# the filidh of the south bank
mem("filidh", "filidh", "blue", faction="filidh", aggro=[50, 400], roam=200)
mem("devout filidh", "devout filidh", "yellow", faction="filidh", aggro=[60, 450], roam=150)
# named, re-tiered (kept in place): see tiers
# --- Cotswold, the Camelot gate and the west bank (calm)
b.wild("cotswold_fields", 330, 560, 560, 860, {"brownie": 8, "small snake": 6, "gray wolf pup": 10, "wild sow": 10, "boar piglet": 6})
b.wild("gate_meadows", 120, 560, 300, 640, {"brownie": 4, "small snake": 4, "boar piglet": 4})
b.wild("west_bank", 230, 860, 420, 1150, {"wild sow": 6, "gray wolf pup": 6, "giant frog": 8, "snake": 6})
b.wild("river_reeds", 250, 950, 560, 1260, {"river spriteling": 14, "river drake hatchling": 10, "giant frog": 6})
b.camp("sprite_pool", 470, 1220, 10, {"river sprite": 4, "river drakeling": 3}, 300)
b.camp("drake_bank", 520, 1080, 9, {"river drakeling": 3, "river drake hatchling": 3}, 300)
b.wild("north_west_downs", 80, 150, 450, 520, {"gray wolf pup": 10, "wild sow": 8, "small bear": 6, "small snake": 6, "brownie": 6})
# --- the north road, Nob's Stable and the faerie ring (calm to contested)
b.wild("north_road", 450, 250, 800, 560, {"wild sow": 8, "young boar": 8, "snake": 8, "small bear": 6, "gray wolf": 4})
b.camp("faerie_ring", 655, 440, 12, {"faerie mischief-maker": 6, "faerie wolf-crier": 2, "faerie bell-wether": 2}, 300)
b.wild("faerie_meadow", 560, 420, 840, 620, {"faerie mischief-maker": 6, "faerie wolf-crier": 4, "brownie": 6})
b.camp("pilgrims_camp", 725, 240, 10, {"convert guard": 4}, 300)
b.wild("north_heath", 800, 80, 1150, 300, {"gray wolf": 6, "black wolf": 4, "small bear": 6, "young boar": 6})
b.camp("woodcutters_poachers", 650, 330, 8, {"young poacher": 4}, 300)
# --- the middle hills: spriggarn and brownie country, the Camelot road gang
b.wild("spriggarn_hills", 560, 650, 960, 1050, {"spriggarn": 26, "spriggarn elder": 10, "brownie nomad": 8, "snake": 6, "plague spider": 6})
for k, (x, y) in enumerate([(700, 800), (860, 760), (800, 940)]):
    b.camp("spriggarn_ring_%d" % k, x, y, 7, {"spriggarn": 4, "spriggarn elder": 2}, 300)
b.wild("meadows_east", 900, 650, 1150, 900, {"young boar": 6, "small bear": 6, "emerald snake": 8, "giant frog": 6})
b.camp("road_gang", 840, 990, 12, {"young cutpurse": 6, "cutpurse": 4, "bandit": 2, "bandit lieutenant": 1}, 300)
b.patrol("road_gang_walk", [(840, 990), (700, 900), (560, 820), (420, 760), (560, 820), (700, 900)], {"cutpurse": 2, "young cutpurse": 1})
# --- the eastern ridge: ants, the Difwych hunt, the ridge bandits (contested)
b.wild("ant_hills", 960, 280, 1380, 860, {"dragon ant worker": 20, "dragon ant soldier": 10, "dragon ant drone": 6})
b.camp("ant_queen_mound", 1180, 520, 10, {"dragon ant queen": 1, "dragon ant worker": 4}, 600)
b.camp("ridge_bandits", 985, 535, 12, {"bandit": 6, "bandit henchman": 3, "bandit thaumaturge": 2, "bandit lieutenant": 1}, 300)
b.wild("difwych_hills", 1220, 260, 1600, 780, {"hound of the Difwych": 10, "black wolf": 6, "gray wolf": 6, "adder": 6})
for k, (x, y) in enumerate([(1283, 749), (1325, 550), (1251, 314)]):
    b.camp("difwych_hunt_%d" % k, x + 20, y + 15, 7, {"Difwych huntsman": 2, "hound of the Difwych": 2}, 360)
# --- the barrow fields and Mithra's Tomb (the zone's hot spot)
b.wild("barrow_fields", 900, 950, 1300, 1250, {"puny skeleton": 10, "decayed zombie": 10, "skeleton": 8, "large skeleton": 6, "spirit": 8,
                                               "putrid zombie": 6})
b.camp("tomb_mouth", 1330, 995, 12, {"crimson acolyte": 6, "crimson initiate": 3, "crimson tomb-warden": 1}, 360)
b.camp("tomb_rite", 1255, 1060, 9, {"crimson acolyte": 3, "undead filidh": 2, "rotting zombie": 2}, 360)
b.patrol("tomb_watch", [(1330, 995), (1260, 900), (1180, 860), (1260, 900)], {"crimson acolyte": 2})
b.wild("tomb_hills", 1300, 860, 1620, 1250, {"undead filidh": 6, "spirit": 6, "rotting zombie": 4, "emerald snake": 4})
b.camp("barrow_ring", 1100, 1150, 8, {"large skeleton": 3, "putrid zombie": 2, "undead filidh": 1}, 300)
# --- Darkness Falls' mouth (hot, small)
b.camp("df_mouth", 1265, 1340, 10, {"manes demon": 6, "grumoz demon": 1}, 300)
b.wild("df_spill", 1150, 1250, 1400, 1420, {"manes demon": 4, "boulderling": 6})
b.wild("boulder_downs", 920, 1080, 1350, 1280, {"boulderling": 10, "young boar": 4})
# --- Prydwen Keep and the river crossing (calm)
b.wild("prydwen_fields", 560, 1080, 900, 1280, {"wild sow": 6, "young boar": 6, "snake": 6, "gray wolf pup": 4, "small bear": 4})
# --- south of the river: the filidh's grove, bears, the old fort's bandits (contested)
b.wild("south_bank", 300, 1380, 1100, 1630, {"bear": 10, "small bear": 8, "grass snake": 10, "adder": 6, "brownie nomad": 8})
b.camp("filidh_grove", 736, 1521, 12, {"filidh": 6, "devout filidh": 3}, 360)
b.wild("filidh_paths", 600, 1430, 1100, 1600, {"filidh": 8})
b.camp("old_fort", 948, 1420, 14, {"bandit": 6, "bandit henchman": 4, "bandit thaumaturge": 2, "bandit leader": 1}, 360)
b.patrol("old_fort_road", [(948, 1420), (820, 1360), (700, 1320), (820, 1360)], {"bandit": 2, "bandit henchman": 1})

themes = ["Cotswold's fields (wolves, sows, brownies)", "The river (sprites, drakes, frogs)", "The fae (spriggarns, the faerie ring)",
          "The Camelot Road Gang (cutpurses, bandits, the old fort)", "The eastern ridge (ants, the Difwych hunt)",
          "Mithra's Tomb (the Crimson cult, the restless dead)", "Darkness Falls' mouth (demons)", "The south bank (filidh, bears)",
          "The north road (the dwarven pilgrims)"]
notes = ("Albion's plan 2026-11-24 (Zone Reviews, 'Albion - the plan'): Peaceful; the Crimson cult's first rite at Mithra's Tomb; "
         "about 950 monsters. Coordinates are zone-local units (metres x 40).")
tiers = {"Cronker": "yellow", "Thwori": "blue", "Lady Leana": "blue", "Ygwrch Gyrg": "blue", "Mulgrut Maggot": "blue",
         "Hugrath Wormly": "yellow", "Aithne Con": "yellow", "Fielath": "orange", "Weakened demon": "yellow",
         "Cilydd Difwych": "yellow", "Cyfer Difwych": "yellow", "Cyfwlch Difwych": "orange", "Dwarven Priest": "blue"}
factions = {"spriggarns": {"id": 9401, "aggro": 40}, "faeries": {"id": 9402, "aggro": 45}, "ants": {"id": 9403, "aggro": 40},
            "bandits": {"id": 9404, "aggro": 80}, "difwych": {"id": 9405, "aggro": 85}, "dead": {"id": 9406, "aggro": 90},
            "crimson": {"id": 9407, "aggro": 95}, "converts": {"id": 9408, "aggro": 60}, "demons": {"id": 9409, "aggro": 100},
            "filidh": {"id": 9410, "aggro": 55}}
b.write(sys.argv[1], themes, notes, ["Dwarven Priest"], tiers, factions)
