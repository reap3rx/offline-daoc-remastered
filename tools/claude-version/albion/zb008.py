"""Campacorentin Forest's zone build (claude 2026-11-24, "Albion - the plan"; owner: "a blend of Wild and Dangerous ... it can
hold the Wild rating"): Wild - greens and blues round Campacorentin Station and Lethantis in the north-west, blues and yellows
through the middle and round Caer Ulfwych - and a Dangerous deep wood in the south-east: Merlin's thorn, where Nimue sealed him,
and the druids' way down to it from Keltoi Fogou. The wood itself guards the thorn (fellwoods and oak men wake), the Crimson's
sacrificers feed its roots blood to open it for Morgana, and the Lethantis-bred wood ogres hold the south-west. The Thornwood
Ancient is the purple. About 950."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(8, 'Campacorentin Forest', 'wild', 1.22)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
# the north-west (Station and Lethantis) - green and blue
mem("dappled lynx cub", "dappled lynx cub", "grey", roam=250)
mem("dryad twig", "dryad twig", "green", roam=200)
mem("gray wolf pup", "gray wolf pup", "green", roam=300)
mem("small gray wolf", "small gray wolf", "green", roam=350)
mem("dappled lynx", "dappled lynx", "green", roam=350)
mem("giant spider", "giant spider", "green", roam=250)
mem("forest snake", "forest snake", "green", roam=250)
mem("tree spider", "tree spider", "green", roam=250)
mem("scrawny red lion", "scrawny red lion", "green", roam=350)
mem("gray wolf", "gray wolf", "blue", roam=400)
mem("young boar", "young boar", "blue", roam=350)
mem("small bear", "small bear", "blue", roam=350)
mem("poacher", "poacher", "blue", faction="bandits", aggro=[50, 350], roam=250)
# the sylvan goblins (all through the north and middle)
mem("sylvan goblin whelp", "sylvan goblin whelp", "green", faction="goblins", aggro=[50, 350], roam=250)
mem("sylvan goblin", "sylvan goblin", "blue", faction="goblins", aggro=[60, 400], roam=250)
mem("sylvan goblin hunter", "sylvan goblin hunter", "blue", faction="goblins", aggro=[70, 450], roam=350)
mem("sylvan goblin warrior", "sylvan goblin warrior", "yellow", faction="goblins", aggro=[75, 450], roam=200)
# the fae and the waking wood (north-east)
mem("spriggarn", "spriggarn", "blue", faction="fae", aggro=[50, 350], roam=250)
mem("spriggarn elder", "spriggarn elder", "blue", faction="fae", aggro=[50, 350], roam=200)
mem("spriggarn waylayer", "spriggarn waylayer", "yellow", faction="fae", aggro=[70, 450], roam=200)
mem("spriggarn howler", "spriggarn howler", "orange", faction="fae", aggro=[80, 500], roam=100)
mem("tree spirit", "tree spirit", "blue", faction="wood", aggro=[50, 350], roam=200)
mem("oak man", "oak man", "yellow", faction="wood", aggro=[60, 400], roam=150)
mem("oaken fellwood", "oaken fellwood", "orange", faction="wood", aggro=[70, 450], roam=80)
mem("dryad", "dryad", "blue", faction="wood", aggro=[40, 350], roam=200)
mem("dryad invert", "dryad invert", "yellow", faction="wood", aggro=[60, 400], roam=200)
mem("brownie", "brownie", "grey", roam=300)
mem("brownie nomad", "brownie nomad", "blue", faction="fae", aggro=[30, 300], roam=300)
mem("pixie scout", "pixie scout", "yellow", faction="pixies", aggro=[60, 400], roam=250)
mem("pixie", "pixie", "blue", faction="pixies", aggro=[50, 350], roam=250)
# the middle wood round Caer Ulfwych (blue / yellow) and the restless dead
mem("forest bear", "forest bear", "blue", roam=350)
mem("bloated spider", "bloated spider", "yellow", aggro=[60, 400], roam=250)
mem("wandering spirit", "wandering spirit", "yellow", faction="dead", aggro=[60, 450], roam=250)
mem("fading spirit", "fading spirit", "blue", faction="dead", aggro=[50, 400], roam=250)
mem("spirit", "spirit", "blue", faction="dead", aggro=[50, 400], roam=250)
mem("weak skeleton", "weak skeleton", "green", faction="dead", aggro=[60, 400], roam=150)
mem("rotting zombie", "rotting zombie", "blue", faction="dead", aggro=[70, 400], roam=150)
mem("undead filidh", "undead filidh", "blue", faction="dead", aggro=[70, 400], roam=150)
mem("undead druid", "undead druid", "yellow", faction="dead", aggro=[75, 450], roam=150)
mem("devout filidh", "devout filidh", "yellow", faction="filidh", aggro=[60, 400], roam=150)
mem("bandit", "bandit", "blue", faction="bandits", guild="the Greenway Robbers", aggro=[70, 450], roam=200)
# the west and the swamps (green / blue)
mem("will o' wisp", "will o' wisp", "yellow", aggro=[50, 400], roam=300)
mem("swamp rat", "swamp rat", "green", roam=250)
mem("swamp slime", "swamp slime", "green", roam=150)
mem("creeping crud", "creeping crud", "green", roam=150)
mem("snake", "snake", "green", roam=250)
mem("forest lion", "forest lion", "blue", aggro=[50, 400], roam=400)
# the wood ogres (south-west, yellow / orange)
mem("wood ogre mystic", "wood ogre mystic", "yellow", faction="ogres", aggro=[75, 500], roam=150)
mem("wood ogre scourge", "wood ogre scourge", "yellow", faction="ogres", aggro=[80, 500], roam=200)
mem("wood ogre seer", "wood ogre seer", "orange", faction="ogres", aggro=[80, 500], roam=120)
mem("wood ogre berserker", "wood ogre berserker", "orange", faction="ogres", aggro=[85, 550], roam=200)
# the south (cats, bears, the faerie meadow)
mem("forest bear cub", "forest bear cub", "blue", roam=300)
mem("forest cat", "forest cat", "yellow", aggro=[60, 450], roam=400)
mem("faerie bell-wether", "faerie bell-wether", "blue", faction="pixies", aggro=[50, 350], roam=200)
# the deep wood (south-east, Dangerous) - the druids' way and Merlin's thorn
mem("faerie wolf-crier", "faerie wolf-crier", "yellow", faction="pixies", aggro=[60, 400], roam=250)
mem("filidh sacrificer", "filidh sacrificer", "orange", faction="crimson", guild="the Crimson", aggro=[85, 500], roam=150)
mem("druid sacrificer", "druid sacrificer", "orange", faction="crimson", guild="the Crimson", aggro=[85, 500], roam=150)
mem("mindless minion", "mindless minion", "yellow", faction="crimson", aggro=[80, 450], roam=200)
mem("druid", "druid", "orange", faction="druids", guild="the Druids of the Fogou", aggro=[80, 500], roam=150)
mem("druid seer", "druid seer", "yellow", faction="druids", guild="the Druids of the Fogou", aggro=[75, 450], roam=200)
mem("disturbed presence", "disturbed presence", "orange", faction="dead", aggro=[80, 450], roam=200, model=485)
mem("thorn-warden fellwood", "gnarled fellwood", "red", name="thorn-warden fellwood", faction="wood", guild="the Thornwood",
    aggro=[90, 600], roam=60)
mem("Thornwood Ancient", "knotted fellwood", "purple", name="the Thornwood Ancient", faction="wood", guild="Keeper of Merlin's Sleep",
    aggro=[95, 650], size=1.5, roam=30, guards={"thorn-warden fellwood": 2})

# --- the north-west, round the Station and Lethantis
b.wild("station_glades", 150, 50, 560, 420, {"dappled lynx cub": 14, "dryad twig": 12, "gray wolf pup": 14, "giant spider": 10,
                                            "small gray wolf": 10, "forest snake": 6})
b.wild("west_wood", 10, 420, 520, 1300, {"dappled lynx": 22, "scrawny red lion": 16, "tree spider": 14, "forest snake": 10,
                                        "sylvan goblin whelp": 10})
b.wild("west_swamps", 100, 900, 330, 1430, {"swamp rat": 10, "swamp slime": 10, "creeping crud": 12, "snake": 10})
b.camp("wisp_hollow", 454, 971, 10, {"will o' wisp": 8}, 300)
# --- the north road and the goblins
b.wild("north_road", 480, 60, 1000, 620, {"gray wolf": 20, "sylvan goblin": 26, "small gray wolf": 8, "poacher": 12, "sylvan goblin hunter": 10})
b.camp("tree_spirits", 887, 280, 10, {"tree spirit": 6, "spriggarn elder": 2}, 300)
b.camp("spriggarn_knoll", 962, 353, 9, {"spriggarn elder": 5, "spriggarn": 3}, 300)
b.camp("waylayers", 945, 179, 9, {"spriggarn waylayer": 5}, 300)
b.camp("goblin_war_camp", 896, 432, 12, {"sylvan goblin warrior": 6, "sylvan goblin hunter": 3, "sylvan goblin": 3}, 300)
# --- the north-east: the waking wood
b.wild("oakwood", 1170, 80, 1570, 570, {"oak man": 28, "small bear": 10, "young boar": 12, "spriggarn": 12, "dryad": 10})
b.camp("howlers", 1232, 139, 8, {"spriggarn howler": 4}, 360)
b.camp("fellwood_grove", 1501, 246, 9, {"oaken fellwood": 5}, 420)
b.camp("dryad_ring", 1070, 541, 9, {"dryad invert": 6}, 300)
# --- the middle wood round Caer Ulfwych
b.wild("middle_wood", 600, 450, 1300, 1050, {"forest bear": 30, "sylvan goblin": 16, "sylvan goblin warrior": 20, "bloated spider": 14,
                                            "brownie": 10, "brownie nomad": 10, "wandering spirit": 10, "fading spirit": 10})
b.camp("pixie_glade", 928, 751, 9, {"pixie scout": 5, "pixie": 3}, 300)
b.camp("filidh_barrows", 819, 598, 9, {"undead filidh": 6, "spirit": 3}, 300)
b.camp("druid_barrow", 1052, 816, 10, {"undead druid": 5, "undead filidh": 2}, 300)
b.camp("old_graves", 766, 928, 9, {"weak skeleton": 6}, 300)
b.camp("greenway_robbers", 1126, 784, 10, {"bandit": 6}, 300)
b.camp("restless_dead", 1088, 1068, 8, {"rotting zombie": 5}, 300)
b.camp("filidh_ring", 1242, 953, 10, {"devout filidh": 6}, 300)
b.camp("bloated_nest", 1290, 800, 10, {"bloated spider": 6}, 300)
# --- the wood ogres (south-west)
b.wild("ogre_wood", 510, 900, 750, 1210, {"wood ogre scourge": 16, "wood ogre mystic": 12})
b.camp("ogre_seers", 679, 1108, 10, {"wood ogre seer": 5, "wood ogre mystic": 2}, 360)
b.camp("ogre_berserkers", 560, 1020, 9, {"wood ogre berserker": 4}, 360)
# --- the south
b.wild("south_glades", 600, 1380, 1250, 1570, {"forest cat": 16, "forest bear cub": 14, "forest lion": 10, "faerie bell-wether": 10})
b.wild("lion_south", 140, 1400, 600, 1530, {"forest lion": 14, "snake": 6})
# --- the deep wood (Dangerous): the druids' way and Merlin's thorn
b.wild("deep_wood", 1150, 850, 1560, 1440, {"faerie wolf-crier": 14, "mindless minion": 14, "druid seer": 12, "disturbed presence": 14,
                                           "bloated spider": 8})
b.camp("sacrificers_glade", 1368, 1299, 12, {"druid sacrificer": 5, "filidh sacrificer": 3, "mindless minion": 2}, 360)
b.camp("fogou_druids", 1440, 1340, 12, {"druid": 6, "druid seer": 2}, 360)
b.camp("filidh_east", 1470, 942, 10, {"filidh sacrificer": 5}, 360)
b.camp("merlins_thorn", 1300, 1180, 8, {"Thornwood Ancient": 1}, 1800)
b.camp("thorn_ring", 1300, 1180, 18, {"thorn-warden fellwood": 3, "disturbed presence": 4}, 600, ring=[200, 700])

themes = ["The north-west glades round Campacorentin Station and Lethantis", "The sylvan goblins of the north road",
          "The waking wood (oak men, fellwoods, spriggarns)", "The middle wood round Caer Ulfwych (bears, spiders, the restless dead)",
          "The Lethantis-bred wood ogres (south-west)", "The deep wood - Dangerous: the druids' way, the Crimson's sacrificers, Merlin's thorn"]
notes = ("Albion's plan 2026-11-24, round 2: Wild with a Dangerous deep wood (owner: 'a blend of Wild and Dangerous'); both threads "
         "cross at Merlin's thorn. Coordinates are zone units (metres x 40).")
tiers = {"Aonghas Prirerd": "orange", "Elithralia Nodith": "red", "Oaken Knight": "orange", "Elder Fellwood": "orange",
         "Grizzletooth": "orange", "Heretical Hermit": "yellow", "Thornpaw": "orange", "Pixie Queen": "red", "Green Witch": "orange",
         "Ciraron Webweaver": "orange", "Granddaddy Longlegs": "orange", "Ormgarth": "yellow", "Sirelian": "orange",
         "Urfgrat the Green": "orange"}
factions = {"goblins": {"id": 9441, "aggro": 70}, "fae": {"id": 9442, "aggro": 50}, "wood": {"id": 9443, "aggro": 60},
            "pixies": {"id": 9444, "aggro": 55}, "dead": {"id": 9445, "aggro": 80}, "filidh": {"id": 9446, "aggro": 60},
            "bandits": {"id": 9447, "aggro": 75}, "ogres": {"id": 9448, "aggro": 85}, "crimson": {"id": 9449, "aggro": 95},
            "druids": {"id": 9450, "aggro": 85}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
