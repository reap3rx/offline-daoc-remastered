"""Black Mountains South's zone build (claude 2026-11-24, "Albion - the plan"): Peaceful - the villages of Humberton and Ludlow
between Camelot's north gate and the river, mostly greens and blues. The north-west thread: the Crimson cult has a foothold in the
Church - Dark Bishop Burhoff of Vetusta Abbey is one of them, and his 'dark brethren' keep the abbey (the zone's set-piece: retake
it); the filidh sacrificers hold the standing stone at the head of the pass to Black Mountains North. Tepok's Mine: the goblins dug
into something old, and their drowned dead walk the river. The red dwarves rob the north-east, the Nain dwarves raid the south-west.
About 900."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(2, 'Black Mountains South', 'peaceful', 2.0)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
# critters and wildlife
mem("green snake", "green snake", "grey", roam=250)
mem("water snake", "water snake", "grey", roam=250)
mem("worker ant", "worker ant", "grey", roam=250)
mem("boar piglet", "boar piglet", "grey", roam=250)
mem("black wolf pup", "black wolf pup", "green", roam=350)
mem("bear cub", "bear cub", "green", roam=300)
mem("wild sow", "wild sow", "green", roam=350)
mem("forest snake", "forest snake", "green", roam=300)
mem("snake", "snake", "green", roam=300)
mem("eel", "eel", "green", roam=200)
mem("large ant", "large ant", "green", roam=250)
mem("ant drone", "ant drone", "blue", roam=300)
mem("small bear", "small bear", "green", roam=350)
mem("bear", "bear", "blue", roam=350)
mem("red lion", "red lion", "blue", roam=400)
mem("forest lion", "forest lion", "yellow", roam=400)
mem("black wolf", "black wolf", "blue", roam=450)
mem("small gray wolf", "small gray wolf", "green", roam=400)
mem("giant spider", "giant spider", "blue", roam=250)
mem("spectral hound", "spectral hound", "blue", faction="dead", aggro=[70, 450], roam=350)
mem("rock imp", "rock imp", "blue", roam=150)
mem("slith broodling", "slith broodling", "green", roam=200)
# the goblins of Tepok's Mine and the river
mem("goblin fisherman", "goblin fisherman", "green", faction="goblins", aggro=[60, 400], roam=200)
mem("goblin", "goblin", "blue", faction="goblins", aggro=[70, 450], roam=200)
mem("goblin scout", "goblin scout", "blue", faction="goblins", aggro=[70, 500], roam=300)
mem("goblin lookout", "goblin lookout", "blue", faction="goblins", aggro=[80, 550], roam=60)
mem("goblin shaman", "goblin shaman", "yellow", faction="goblins", aggro=[75, 450], roam=120)
mem("goblin war-boss", "goblin", "yellow", name="goblin war-boss", faction="goblins", aggro=[80, 500], size=1.25, roam=80,
    guards={"goblin": 2})
# the drowned dead (raised out of the river)
mem("undead goblin fisherman", "undead goblin fisherman", "blue", faction="dead", aggro=[85, 450], roam=150)
mem("undead goblin warrior", "undead goblin warrior", "yellow", faction="dead", aggro=[90, 450], roam=150)
mem("weak skeleton", "weak skeleton", "green", faction="dead", aggro=[80, 400], roam=150)
mem("moldy skeleton", "moldy skeleton", "green", faction="dead", aggro=[80, 400], roam=150)
mem("skeleton", "skeleton", "blue", faction="dead", aggro=[85, 450], roam=150)
mem("puny skeleton", "puny skeleton", "green", faction="dead", aggro=[80, 400], roam=150)
# the red dwarves (north-east) and the Nain raiders (south-west)
mem("red dwarf youth", "red dwarf youth", "green", faction="reddwarves", aggro=[70, 400], roam=200)
mem("red dwarf thief", "red dwarf thief", "blue", faction="reddwarves", aggro=[75, 450], roam=250)
mem("red dwarf bandit", "red dwarf bandit", "blue", faction="reddwarves", aggro=[80, 450], roam=200)
mem("red dwarf matron", "red dwarf matron", "yellow", faction="reddwarves", aggro=[80, 450], roam=60)
mem("red dwarf chief", "red dwarf chief", "orange", faction="reddwarves", aggro=[85, 500], size=1.15, roam=50,
    guards={"red dwarf bandit": 2})
mem("dwarf brawler", "dwarf brawler", "green", faction="nain", aggro=[70, 400], roam=200)
mem("dwarf pillager", "dwarf pillager", "blue", faction="nain", aggro=[75, 450], roam=200)
mem("dwarf raider", "dwarf raider", "blue", faction="nain", aggro=[80, 450], roam=250)
# robbers and highwaymen (the river road and the Ludlow road)
mem("young cutpurse", "young cutpurse", "green", faction="bandits", aggro=[60, 400], roam=200)
mem("cutpurse", "cutpurse", "green", faction="bandits", aggro=[65, 400], roam=200)
mem("robber", "robber", "blue", faction="bandits", aggro=[75, 450], roam=200)
mem("highwayman", "highwayman", "yellow", faction="bandits", aggro=[80, 500], roam=150)
mem("bandit", "bandit", "blue", faction="bandits", aggro=[75, 450], roam=200)
mem("young poacher", "young poacher", "green", faction="bandits", aggro=[50, 350], roam=250)
mem("poacher", "poacher", "blue", faction="bandits", aggro=[60, 400], roam=250)
# the Crimson: the filidh sacrificers at the northern stone, Burhoff's dark brethren at Vetusta Abbey
mem("devout filidh", "devout filidh", "blue", faction="crimson", aggro=[85, 500], roam=150)
mem("filidh sacrificer", "filidh sacrificer", "yellow", faction="crimson", aggro=[90, 500], roam=120)
mem("dark brother", "Crimson Initiate", "blue", size=0.9, name="dark brother", faction="crimson", guild="the Brethren of Vetusta", aggro=[90, 500], roam=120)
mem("dark brother-in-arms", "convert guard", "yellow", name="dark brother-in-arms", faction="crimson", guild="the Brethren of Vetusta",
    aggro=[90, 500], roam=100)
for k in ("Dark Bishop Burhoff",):
    pass

b.wild("humberton_fields", 420, 860, 800, 1250, {"boar piglet": 8, "green snake": 8, "wild sow": 10, "black wolf pup": 10, "bear cub": 6})
b.wild("ludlow_fields", 1000, 850, 1450, 1250, {"worker ant": 10, "green snake": 8, "wild sow": 8, "black wolf pup": 8, "large ant": 8, "snake": 6})
b.camp("ludlow_anthill", 892, 1332, 10, {"large ant": 6, "ant drone": 4}, 300)
b.wild("south_road", 650, 1250, 1100, 1500, {"worker ant": 8, "large ant": 6, "small gray wolf": 6, "green snake": 6})
b.wild("abbey_meadows", 350, 1380, 650, 1560, {"wild sow": 6, "bear cub": 4, "green snake": 6})
b.camp("vetusta_abbey", 549, 1500, 14, {"dark brother": 8, "dark brother-in-arms": 3}, 360)
b.patrol("abbey_cloister", [(549, 1500), (600, 1450), (520, 1420), (480, 1470)], {"dark brother": 2})
b.camp("ludlow_graveyard", 1056, 930, 12, {"weak skeleton": 6, "puny skeleton": 4, "skeleton": 3}, 300)
b.wild("ghost_fields", 900, 880, 1350, 1150, {"spectral hound": 8, "moldy skeleton": 6})
b.camp("ludlow_road_cutpurses", 1370, 1080, 10, {"young cutpurse": 5, "cutpurse": 3}, 300)
b.camp("highway_ambush", 1211, 774, 9, {"highwayman": 2, "bandit": 3}, 360)
b.patrol("highway_walk", [(1211, 774), (1100, 820), (980, 860), (1100, 820)], {"bandit": 2})
b.wild("slith_marsh", 1000, 1360, 1150, 1480, {"slith broodling": 8})
# the south-west: lions, the Nain raiders
b.wild("lion_downs", 100, 960, 450, 1500, {"red lion": 12, "small gray wolf": 6, "black wolf": 4})
b.camp("nain_camp", 185, 1300, 14, {"dwarf brawler": 6, "dwarf raider": 4, "dwarf pillager": 3}, 360)
b.patrol("nain_raid", [(185, 1300), (300, 1250), (420, 1180), (300, 1250)], {"dwarf raider": 2, "dwarf brawler": 1})
b.wild("west_hills", 60, 1060, 300, 1400, {"dwarf brawler": 4, "black wolf": 6})
# the river: goblin fishers, the drowned, the robbers' landing
b.wild("river_south_bank", 300, 720, 1300, 820, {"water snake": 10, "eel": 10, "goblin fisherman": 10})
b.camp("singing_pool", 600, 610, 10, {"undead goblin fisherman": 6, "undead goblin warrior": 2}, 360)
b.camp("drowned_reach", 700, 650, 9, {"undead goblin fisherman": 4, "goblin fisherman": 4}, 300)
b.camp("goblin_fishers_west", 420, 640, 9, {"goblin fisherman": 6}, 300)
b.camp("robbers_landing", 537, 760, 10, {"robber": 5, "cutpurse": 3}, 300)
b.wild("river_reeds", 300, 520, 1300, 700, {"eel": 10, "water snake": 8})
# north of the river: forest, spiders, bears, lions, the red dwarves
b.wild("north_forest", 300, 120, 1300, 520, {"giant spider": 18, "small bear": 10, "bear": 6, "forest snake": 12, "forest lion": 4})
for k, (x, y) in enumerate([(920, 300), (780, 220), (1040, 360)]):
    b.camp("spider_nest_%d" % k, x, y, 8, {"giant spider": 4}, 300)
b.camp("red_dwarf_camp", 1349, 440, 14, {"red dwarf youth": 4, "red dwarf thief": 4, "red dwarf bandit": 3, "red dwarf matron": 1,
                                         "red dwarf chief": 1}, 360)
b.wild("red_dwarf_woods", 1100, 250, 1450, 800, {"red dwarf thief": 8, "red dwarf youth": 4, "rock imp": 6, "poacher": 4})
b.camp("rock_imps", 990, 1040, 7, {"rock imp": 5}, 300)
# Tepok's Mine and the goblin camp (north-west)
b.camp("goblin_camp", 209, 140, 16, {"goblin": 8, "goblin scout": 3, "goblin lookout": 3, "goblin shaman": 2, "goblin war-boss": 1}, 360)
b.camp("tepoks_mouth", 135, 85, 9, {"goblin": 4, "goblin lookout": 1}, 300)
b.patrol("goblin_raid", [(209, 140), (300, 280), (420, 420), (300, 280)], {"goblin scout": 2, "goblin": 1})
b.wild("mine_hills", 100, 150, 400, 450, {"young poacher": 6, "black wolf": 6, "small bear": 4})
# the northern stone (the pass to Black Mountains North)
b.camp("northern_stone", 1110, 40, 12, {"devout filidh": 6, "filidh sacrificer": 4}, 360)
b.wild("stone_path", 950, 40, 1250, 200, {"devout filidh": 4, "small bear": 4})

themes = ["Humberton and Ludlow's fields (sows, wolf pups, ants)", "The river (goblin fishers, eels, the drowned)",
          "Tepok's Mine (the goblins)", "Vetusta Abbey (Burhoff's dark brethren)", "The northern stone (filidh sacrificers)",
          "The red dwarves (north-east woods)", "The Nain raiders (south-west)", "Roads (robbers, highwaymen, cutpurses)",
          "The north forest (spiders, bears, lions)"]
notes = ("Albion's plan 2026-11-24 (Zone Reviews, 'Albion - the plan'): Peaceful; Burhoff's Vetusta Abbey the set-piece; about 900 "
         "monsters. Coordinates are zone-local units (metres x 40).")
tiers = {"Dark Bishop Burhoff": "red", "Sacrificer Harish": "orange", "Goblin Lord": "yellow", "Grilk": "orange", "The Great Gobzini": "red",
         "Grilk's bonescraper": "blue", "Grilk's ratmaker": "blue", "Grilk's footscratcher": "blue", "Nain Dwarf": "blue", "Frund": "yellow",
         "Jari": "yellow", "Throatripper": "yellow", "Fusnup": "blue", "Grilo": "blue", "Goblin Storm Shaman": "yellow", "Slith": "blue",
         "Summoner Salizern": "yellow", "Shaman Aslis": "orange", "Agisthil": "yellow", "Brodic": "yellow", "Gundron McCory": "blue",
         "Aldous Wynedd": "blue", "Bouditha Wynedd": "blue", "Welsh hobgoblin": "blue", "Lurking Stranger": "yellow",
         "Vetusta Abbey Bell": "blue"}
factions = {"goblins": {"id": 9421, "aggro": 70}, "dead": {"id": 9422, "aggro": 90}, "reddwarves": {"id": 9423, "aggro": 75},
            "nain": {"id": 9424, "aggro": 75, "enemies": ["reddwarves"]}, "bandits": {"id": 9425, "aggro": 75},
            "crimson": {"id": 9426, "aggro": 95}}
factions["reddwarves"]["enemies"] = ["nain"]
b.write(sys.argv[1], themes, notes, [], tiers, factions)
