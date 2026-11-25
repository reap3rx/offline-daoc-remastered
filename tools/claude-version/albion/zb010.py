"""Lyonesse's zone build (claude 2026-11-24, "Albion - the plan", round 3): Deadly - Tristan's lost country, drowned by the sea,
oranges and reds everywhere, purples at its heart. The south thread with a northern undertone: an unnatural storm is drowning
the coast again (the white dragon's weather, to cut Albion's south off); the drowned Danaoin live their last day over and over;
the priests of Arawn bargain at the ruined cathedral; and the cailleach, the hag of the old sea-wind, is the purple. Only the
Trevose camp on the south-east rise is quiet. About 650."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(10, 'Lyonesse', 'deadly', 2.2)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
mem("peallaidh", "peallaidh", "orange", faction="sea", aggro=[75, 500], roam=250)
mem("freybug", "freybug", "orange", aggro=[80, 500], roam=300)
mem("giant lizard", "giant lizard", "orange", aggro=[70, 450], roam=250)
mem("hamadryad", "hamadryad", "orange", faction="wood", aggro=[60, 450], roam=200)
mem("witherwoode", "witherwoode", "red", faction="wood", aggro=[80, 500], roam=80)
mem("moorlich", "moorlich", "red", faction="mire", aggro=[85, 550], roam=250)
mem("bone snapper", "bone snapper", "red", aggro=[85, 550], roam=300)
mem("cailleach priest", "cailleach priest", "red", faction="cailleach", aggro=[90, 600], roam=100)
mem("cailleach guard", "cailleach guard", "red", faction="cailleach", aggro=[90, 600], roam=100)
mem("pygmy goblin", "pygmy goblin", "orange", faction="goblins", aggro=[75, 500], roam=250)
mem("pygmy goblin tangler", "pygmy goblin tangler", "orange", faction="goblins", aggro=[80, 500], roam=200)
mem("dunter", "dunter", "orange", aggro=[80, 500], roam=150)
mem("fitful bwca", "fitful bwca", "orange", aggro=[70, 450], roam=200)
mem("gabriel hound", "gabriel hound", "red", faction="hounds", aggro=[90, 650], roam=450)
# the drowned folk of Lyonesse (east and south) - living their last day
mem("shepherd", "shepherd", "orange", faction="drowned", guild="of drowned Lyonesse", aggro=[60, 450], roam=250)
mem("farmer", "farmer", "orange", faction="drowned", guild="of drowned Lyonesse", aggro=[60, 450], roam=250)
mem("townsman", "townsman", "orange", faction="drowned", guild="of drowned Lyonesse", aggro=[60, 450], roam=200)
mem("archer", "archer", "red", faction="drowned", guild="of drowned Lyonesse", aggro=[80, 550], roam=200)
mem("pikeman", "pikeman", "red", faction="drowned_knights", guild="of drowned Lyonesse", aggro=[85, 550], roam=150)
mem("footman", "footman", "red", faction="drowned_knights", guild="of drowned Lyonesse", aggro=[85, 550], roam=150)
mem("knight", "knight", "red", faction="drowned_knights", guild="of drowned Lyonesse", aggro=[90, 600], roam=150)
mem("storm-caller", "Crimson Initiate", "red", name="storm-caller", faction="storm", guild="the White Wind", aggro=[90, 600], roam=100)

b.wild("north_shore", 1000, 230, 1500, 700, {"peallaidh": 34, "freybug": 6, "giant lizard": 6})
b.camp("storm_rock", 1179, 467, 10, {"storm-caller": 3, "peallaidh": 4}, 600)
b.wild("hamadryad_wood", 1180, 500, 1610, 1280, {"hamadryad": 26})
b.wild("the_mire", 500, 350, 1230, 990, {"moorlich": 22, "bone snapper": 10})
b.camp("witherwoode", 778, 638, 12, {"witherwoode": 6}, 600)
b.camp("cailleach_ring", 750, 840, 12, {"cailleach priest": 4, "cailleach guard": 4}, 900)
b.wild("drowned_fields", 100, 150, 1100, 1490, {"bone snapper": 28, "archer": 10, "fitful bwca": 6})
b.camp("hound_hill", 531, 758, 9, {"gabriel hound": 4}, 600)
b.wild("drowned_farms", 970, 600, 1390, 1240, {"shepherd": 14, "farmer": 12, "townsman": 6})
b.wild("goblin_south", 845, 1260, 1600, 1450, {"pygmy goblin tangler": 16, "pygmy goblin": 10})
b.camp("dunter_tower", 1355, 1195, 9, {"dunter": 5}, 420)
b.camp("drowned_knights", 1219, 1270, 12, {"knight": 5, "footman": 5}, 600)
b.camp("pike_line", 791, 1096, 9, {"pikeman": 4}, 420)
# the Remnant's camp on the south-east rise stays quiet
b.clear("remnant_camp", 1345, 1135, 90, ["shepherd", "farmer", "townsman", "hamadryad", "pygmy goblin", "pygmy goblin tangler", "dunter",
                                          "knight", "footman", "bone snapper", "archer"])
b.S[-1]["block"] = "all"

themes = ["The north shore and the storm rock (peallaidh, the storm-callers)", "The hamadryad wood (east)",
          "The mire and the cailleach's ring (Deadly heart)", "The drowned fields (bone snappers, archers)",
          "Drowned Lyonesse's folk and knights", "The ruined cathedral (priests of Arawn)"]
notes = ("Albion's plan 2026-11-24, round 3: Deadly; Tristan's lost country, drowned again by an unnatural storm; the priests of "
         "Arawn at the cathedral. Coordinates are zone units (metres x 40).")
tiers = {"Danaoin clerk": "orange", "Arawnite shamaness": "red", "Danaoin fisherman": "orange", "Danaoin sailor": "orange",
         "Danaoin soldier": "red", "Danaoin farmer": "orange", "Priest of Arawn": "red", "Knight": "red", "Arawnite warrior": "red",
         "Unnatural Storm Controller": "purple", "Cailleach Uragaig": "purple"}
factions = {"sea": {"id": 9481, "aggro": 75}, "wood": {"id": 9482, "aggro": 60}, "mire": {"id": 9483, "aggro": 85},
            "cailleach": {"id": 9484, "aggro": 95}, "goblins": {"id": 9485, "aggro": 80}, "hounds": {"id": 9486, "aggro": 95},
            "drowned": {"id": 9487, "aggro": 70}, "drowned_knights": {"id": 9488, "aggro": 90}, "storm": {"id": 9489, "aggro": 95}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
