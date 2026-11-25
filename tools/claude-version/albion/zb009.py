"""Avalon Marsh's zone build (claude 2026-11-24, "Albion - the plan"): Wild - greens and blues round Adribard's Retreat in the
north-east, blues and yellows through the middle marsh and round the Isle's crossing - turning Deadly toward Cornwall in the
west: the Drowned Vigil's ghouls hold their old keep in the north-west (the zone's fort to retake), giant wolves and mist monsters
roam the west marsh, and Golestandt's giants are laying a causeway of Cornish granite across the south-west toward the Isle where
Arthur sleeps. The Marsh Lord, who sold them the way, is the purple. About 950."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(9, 'Avalon Marsh', 'wild', 1.35)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
# the north-east round Adribard's Retreat (grey / green)
for k in ["swamp rat", "creeping crud", "scrawny bogman", "slough serpent", "slime lizard", "carrion crab", "scum toad", "muck snake",
          "mud worm", "impling", "puny skeleton", "outcast rogue"]:
    mem(k, k, "grey" if k in ("slough serpent", "scum toad", "mud worm", "impling") else "green", roam=250)
mem("river spriteling", "river spriteling", "green", roam=250)
mem("river drake hatchling", "river drake hatchling", "green", roam=250)
mem("swamp slime", "swamp slime", "green", roam=150)
mem("giant frog", "giant frog", "blue", roam=250)
mem("spiny eel", "spiny eel", "blue", roam=200)
# the bogmen (north and middle)
mem("bogman", "bogman", "blue", faction="bogmen", aggro=[50, 350], roam=250)
mem("bogman grappler", "bogman grappler", "blue", faction="bogmen", aggro=[60, 400], roam=250)
mem("bogman gatherer", "bogman gatherer", "blue", faction="bogmen", aggro=[60, 400], roam=300)
mem("bogman fisher", "bogman fisher", "yellow", faction="bogmen", aggro=[60, 400], roam=250)
mem("bogman trapper", "bogman trapper", "yellow", faction="bogmen", aggro=[70, 450], roam=200)
mem("bogman hunter", "bogman hunter", "yellow", faction="bogmen", aggro=[75, 450], roam=250)
# the middle marsh (blue / yellow)
mem("mist sprite", "mist sprite", "blue", faction="isle", aggro=[50, 400], roam=250)
mem("river racer", "river racer", "blue", roam=250)
mem("rot worm", "rot worm", "blue", roam=200)
mem("death grip vines", "death grip vines", "yellow", aggro=[60, 300], roam=0)
mem("bloody-bones", "bloody-bones", "yellow", faction="dead", aggro=[70, 450], roam=250)
mem("decayed zombie", "decayed zombie", "blue", faction="dead", aggro=[60, 400], roam=150)
mem("putrid zombie", "putrid zombie", "blue", faction="dead", aggro=[60, 400], roam=150)
mem("water leaper", "water leaper", "yellow", aggro=[60, 450], roam=250)
mem("scrag", "scrag", "yellow", faction="scrags", aggro=[70, 450], roam=250)
mem("scragling", "scragling", "blue", faction="scrags", aggro=[60, 400], roam=250)
mem("marsh scrag", "marsh scrag", "yellow", faction="scrags", aggro=[75, 450], roam=250)
mem("will o' wisp", "will o' wisp", "yellow", aggro=[50, 400], roam=300)
mem("marsh worm", "marsh worm", "yellow", aggro=[60, 400], roam=200)
mem("pixie", "pixie", "blue", faction="isle", aggro=[40, 350], roam=250)
# the shore chapel's dead knights (south-middle)
mem("phantom page", "phantom page", "blue", faction="shore_knights", aggro=[60, 400], roam=200)
mem("phantom squire", "phantom squire", "yellow", faction="shore_knights", aggro=[70, 450], roam=200)
mem("ghostly knight", "ghostly knight", "orange", faction="shore_knights", aggro=[80, 500], roam=150)
# the west - Deadly toward Cornwall
mem("shambler", "shambler", "yellow", faction="causeway", aggro=[70, 450], roam=200)
mem("mud golem", "mud golem", "orange", faction="causeway", aggro=[80, 500], roam=100)
mem("giant water leaper", "giant water leaper", "orange", aggro=[80, 500], roam=250)
mem("giant wolf", "giant wolf", "orange", aggro=[80, 550], roam=450)
mem("black bear", "black bear", "orange", aggro=[60, 450], roam=350)
mem("mist monster", "mist monster", "red", aggro=[85, 550], roam=250)
mem("quicksand", "quicksand", "orange", aggro=[90, 200], roam=0)
mem("wood ogre scourge", "wood ogre scourge", "orange", faction="ogres", aggro=[80, 500], roam=200)
mem("wood ogre seer", "wood ogre seer", "orange", faction="ogres", aggro=[80, 500], roam=120)
mem("wood ogre berserker", "wood ogre berserker", "red", faction="ogres", aggro=[85, 550], roam=200)
# the Drowned Vigil (north-west keep)
mem("ghoul footman", "ghoul footman", "orange", faction="vigil", guild="the Drowned Vigil", aggro=[85, 550], roam=150)
mem("ghoul knight", "ghoul knight", "orange", faction="vigil", guild="the Drowned Vigil", aggro=[85, 550], roam=200)
mem("ghoul lord", "ghoul lord", "red", faction="vigil", guild="the Drowned Vigil", aggro=[90, 600], roam=100,
    guards={"ghoul knight": 1})
# the giants' causeway (south-west)
mem("Cornish giant", "Cornish giant", "red", faction="giants", guild="the March of Golestandt", aggro=[90, 650], roam=200)
mem("granite giant herdsman", "granite giant herdsman", "red", faction="giants", guild="the March of Golestandt", aggro=[90, 650],
    roam=150)

# --- the north-east round Adribard's Retreat (gentle)
b.wild("retreat_shallows", 880, 130, 1600, 620, {"swamp rat": 20, "creeping crud": 20, "scrawny bogman": 16, "slough serpent": 12,
                                                 "slime lizard": 10, "carrion crab": 10, "scum toad": 10, "muck snake": 8, "mud worm": 6,
                                                 "impling": 6, "puny skeleton": 6, "outcast rogue": 6, "river spriteling": 10,
                                                 "river drake hatchling": 8, "swamp slime": 14})
b.wild("retreat_bog", 840, 140, 1600, 880, {"bogman": 26, "bogman grappler": 16, "spiny eel": 14, "giant frog": 8})
# --- the middle marsh and the Isle's crossing
b.wild("isle_mists", 550, 240, 1400, 900, {"mist sprite": 30, "rot worm": 20, "river racer": 14, "bloody-bones": 10, "death grip vines": 10,
                                          "bogman gatherer": 16})
b.camp("isle_shore", 1104, 470, 10, {"mist sprite": 6, "pixie": 2}, 300)
b.camp("bog_village", 886, 1028, 12, {"bogman gatherer": 5, "bogman trapper": 3, "bogman hunter": 2}, 300)
b.wild("east_dead", 900, 540, 1300, 900, {"decayed zombie": 10, "putrid zombie": 10})
# --- the south-middle: the shore chapel and the leapers
b.wild("south_marsh", 640, 900, 1400, 1540, {"bogman fisher": 16, "water leaper": 16, "scragling": 8, "death grip vines": 10,
                                            "will o' wisp": 10, "marsh worm": 8, "pixie": 6})
b.camp("leapers_pool", 979, 1300, 10, {"water leaper": 6}, 300)
b.camp("scrag_hollow", 1117, 1419, 10, {"scrag": 6, "scragling": 3}, 300)
b.camp("shore_chapel", 1032, 1215, 10, {"ghostly knight": 4, "phantom squire": 3}, 420)
b.wild("chapel_yard", 920, 820, 1470, 1250, {"phantom page": 12, "phantom squire": 4})
# --- round Caer Witrin (a blue pocket in the west)
b.wild("witrin_fields", 380, 820, 600, 1020, {"marsh scrag": 10, "scragling": 6, "bloody-bones": 6})
# --- the west: Deadly toward Cornwall
b.wild("wolf_marsh", 180, 430, 620, 840, {"giant wolf": 22, "black bear": 8})
b.camp("mist_monsters", 191, 569, 10, {"mist monster": 6}, 420)
b.camp("quicksand_bank", 556, 545, 9, {"quicksand": 6}, 600)
b.camp("leaper_deeps", 689, 624, 10, {"giant water leaper": 6}, 360)
b.wild("shambler_road", 170, 1000, 800, 1460, {"shambler": 34, "marsh scrag": 10, "death grip vines": 8})
b.camp("mud_golems", 644, 986, 9, {"mud golem": 5}, 360)
b.camp("ogre_edge", 75, 990, 12, {"wood ogre scourge": 4, "wood ogre seer": 2, "wood ogre berserker": 2}, 420)
for k, (x, y) in enumerate([(130, 1160), (260, 1080), (400, 1230)]):
    b.camp("giants_causeway_%d" % k, x, y, 10, {"Cornish giant": 2, "granite giant herdsman": 1, "shambler": 2}, 480)
# --- the Drowned Vigil's keep (north-west) - the fort to retake
b.wild("vigil_marsh", 180, 75, 560, 440, {"ghoul footman": 16, "ghoul knight": 14})
b.camp("vigil_keep", 360, 240, 14, {"ghoul lord": 3, "ghoul knight": 6, "ghoul footman": 4}, 420)
b.camp("vigil_walls", 410, 330, 10, {"ghoul footman": 6}, 360)

themes = ["The shallows round Adribard's Retreat", "The bogmen", "The middle marsh and the Isle's crossing (mist sprites)",
          "The shore chapel's dead knights", "The Drowned Vigil's keep (the fort to retake) - Deadly",
          "The west marsh toward Cornwall (wolves, mist monsters, shamblers) - Deadly", "The giants' causeway of Cornish granite"]
notes = ("Albion's plan 2026-11-24, round 2: Wild, Deadly toward Cornwall; the south thread's giants build a road to the Isle where "
         "Arthur sleeps, and the north thread's Crimson cross to it by night. Coordinates are zone units (metres x 40).")
tiers = {"Dooben": "yellow", "Marsh Lord": "purple", "Undead Knight Fiedel": "red", "Borwyr the Cursed": "yellow", "Vagdush": "orange",
         "Dread Lord Aryon": "red", "Scraek": "yellow"}
factions = {"bogmen": {"id": 9451, "aggro": 50}, "isle": {"id": 9452, "aggro": 45}, "dead": {"id": 9453, "aggro": 80},
            "scrags": {"id": 9454, "aggro": 75}, "shore_knights": {"id": 9455, "aggro": 85}, "causeway": {"id": 9456, "aggro": 80},
            "ogres": {"id": 9457, "aggro": 85}, "vigil": {"id": 9458, "aggro": 95}, "giants": {"id": 9459, "aggro": 90}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
