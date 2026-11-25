"""Vanern Swamp's zone build (claude 2026-11-25, "Midgard - the plan", round 3): Deadly - oranges and reds everywhere, a few
yellows on the mud flats by the wardens' camp. The west thread's dead: as the long winter comes, the hagbui - the barrow-dead of
Vanern's old thanes - have risen and taken Hrafnsholm, the watch-hold on the north-west ridge, and chained a jotun in its yard to
work their forge; the zone's fort to retake, for the Wardens of Vanern. The jotun outcasts of the north drive enslaved orms; the
broken and crippled jotun of the west were the hagbui's earlier slaves; the clay jotun in the middle are the swamp's own."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from zbcommon import Build
b = Build(107, 'Vanern Swamp', 'deadly', 5.0)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
H = "the Hagbui"
mem("mud frog", "mud frog", "yellow", roam=200)
mem("mud crab", "mud crab", "yellow", aggro=[50, 400], roam=150)
mem("mud crab warrior", "mud crab warrior", "orange", aggro=[70, 450], roam=150)
mem("forest viper", "forest viper", "orange", aggro=[70, 450], roam=250)
mem("forest spider", "forest spider", "orange", faction="spiders", aggro=[75, 500], roam=200)
mem("forest spider queen", "forest spider queen", "red", faction="spiders", aggro=[85, 550], roam=60, guards={"forest spider": 2})
mem("black orm", "black orm", "orange", faction="orms", aggro=[70, 450], roam=200)
mem("small black orm", "small black orm", "orange", faction="orms", aggro=[70, 450], roam=200)
mem("reincarnate orm", "reincarnate orm", "orange", faction="hagbui", aggro=[75, 500], roam=200)
mem("large enslaved orm runner", "large enslaved orm runner", "orange", faction="jotun", aggro=[70, 450], roam=200)
mem("jotun outcast", "jotun outcast", "red", faction="jotun", aggro=[85, 600], roam=200)
mem("clay jotun", "clay jotun", "orange", faction="clay", aggro=[75, 500], roam=150)
mem("clay jotun guard", "clay jotun guard", "red", faction="clay", aggro=[85, 550], roam=60)
mem("broken jotun", "broken jotun", "orange", aggro=[70, 450], roam=150)
mem("crippled jotun", "crippled jotun", "orange", aggro=[70, 450], roam=80)
mem("hagbui berserker", "hagbui berserker", "orange", faction="hagbui", guild=H, aggro=[80, 550], roam=250)
mem("hagbui shaman", "hagbui shaman", "orange", faction="hagbui", guild=H, aggro=[80, 550], roam=150)
mem("hagbui spiritmaster", "hagbui spiritmaster", "orange", faction="hagbui", guild=H, aggro=[80, 550], roam=150)
mem("hagbui runemaster", "hagbui runemaster", "red", faction="hagbui", guild=H, aggro=[85, 550], roam=100)
mem("hagbui guard", "hagbui guard", "orange", faction="hagbui", guild=H, aggro=[80, 550], roam=80)
mem("hagbui thane", "hagbui thane", "red", faction="hagbui", guild=H, aggro=[85, 600], roam=150)
mem("Barrow-Thane Hrodgeir", "hagbui thane", "red", name="Barrow-Thane Hrodgeir", size=1.2, faction="hagbui", guild="Warden of Hrafnsholm",
    aggro=[90, 600], roam=40, guards={"hagbui guard": 2})

b.clear("vanern_camp", 1230, 1120, 90, list(m.keys()))
b.S[-1]["block"] = "all"
b.wild("mud_flats", 900, 820, 1580, 1560, {"mud frog": 10, "mud crab": 8, "mud crab warrior": 8, "forest viper": 6})
b.wild("south_reeds", 180, 1150, 900, 1540, {"forest viper": 8, "mud frog": 6})
b.wild("clay_pits", 490, 820, 840, 1140, {"clay jotun": 8})
b.camp("clay_hall", 672, 1037, 12, {"clay jotun guard": 2, "clay jotun": 2}, 900)
b.wild("jotun_west", 90, 640, 450, 1170, {"broken jotun": 6, "crippled jotun": 4})
b.wild("hagbui_lands", 60, 380, 700, 650, {"hagbui berserker": 8, "hagbui spiritmaster": 4, "hagbui shaman": 3, "reincarnate orm": 4})
b.wild("barrow_ridge", 40, 50, 650, 380, {"reincarnate orm": 4, "hagbui berserker": 4, "hagbui thane": 2})
b.camp("hrafnsholm", 240, 250, 16, {"Barrow-Thane Hrodgeir": 1, "hagbui runemaster": 2, "hagbui thane": 2}, 900)
b.camp("hrafnsholm_yard", 300, 300, 12, {"hagbui guard": 3, "hagbui berserker": 3}, 600)
b.wild("jotun_camp", 560, 90, 810, 320, {"jotun outcast": 5, "large enslaved orm runner": 6})
b.wild("black_orm_bog", 860, 100, 1500, 420, {"black orm": 8, "small black orm": 6})
b.wild("orm_east", 1070, 420, 1570, 1000, {"small black orm": 6, "forest viper": 4})
b.wild("spider_wood", 1100, 90, 1610, 680, {"forest spider": 10})
b.camp("spider_queen", 1478, 170, 12, {"forest spider queen": 1, "forest spider": 2}, 900)

themes = ["The wardens' camp in the south-east, and the mud flats", "The clay jotun pits (middle) and the broken jotun of the west",
          "The hagbui lands and Hrafnsholm, the watch-hold they took (north-west) - the fort to retake",
          "The jotun outcasts' camp and their enslaved orms (north)", "The black orm bog and the spider wood (north-east)"]
notes = ("Midgard's plan 2026-11-25, round 3: Deadly; the west thread's risen barrow-dead hold Hrafnsholm with a chained jotun - "
         "the fort to retake. Coordinates are zone units (metres x 40).")
tiers = {"jotun overlord": "red", "jotun despot": "red", "Ulfketill": "purple", "Jango": "purple", "Rottild the Traitor": "red",
         "Valthjof": "red", "Freyana": "red", "Mista": "orange", "Noma Rindasdottir": "orange", "dark seithkona": "orange",
         "dark seithkona initiate": "orange", "clay jotun retainer": "orange", "clay jotun runner": "orange", "hagbui herald": "orange",
         "hagbui squire": "orange", "hagbui swordbearer": "orange", "hagbui forge tender": "orange", "hagbui page": "orange"}
factions = {"spiders": {"id": 9671, "aggro": 85}, "orms": {"id": 9672, "aggro": 80}, "jotun": {"id": 9673, "aggro": 90, "enemies": ["hagbui"]},
            "clay": {"id": 9674, "aggro": 80}, "hagbui": {"id": 9675, "aggro": 95, "enemies": ["jotun"]}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
