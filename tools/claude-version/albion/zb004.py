"""Dartmoor's zone build (claude 2026-11-24, "Albion - the plan", round 4): Elite - Golestandt's lair, nothing below orange while
the giants hold the moor. The south thread's end: the white dragon is awake in his lair in the south, and every giant of the moor
marches to his tune - the Stonecrush dig his road in the west, the herdsmen drive the ponies off the north moor, the stonecallers
keep their ring in the middle valleys, the pounders and outlookers hold the road south, and the stonelords sit round old
Gogmagog's empty throne in the south-east, waiting for a king. The Dragon-Watch's campaign (AlbionCampaign.cs) takes the moor back
a valley at a time - the Stonecrush Diggings, the Pony Moor, the Stonecallers' Ring, the Pounders' Road - then the Giants' Throne.
Won, every site but the pockets is swept and Golestandt's lair is open. About 520."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(4, 'Dartmoor', 'elite', 1.6)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
G = "Golestandt's giants"
mem("dartmoor pony", "dartmoor pony", "orange", aggro=[30, 300], roam=450)
mem("ruthless brigand", "ruthless brigand", "orange", faction="brigands", guild="Vane's Brigands", aggro=[80, 550], roam=200)
mem("granite knocker", "granite knocker", "orange", faction="knockers", aggro=[80, 500], roam=200)
mem("Stonecrush excavator", "Stonecrush excavator", "orange", faction="stonecrush", guild="the Stonecrush", aggro=[80, 500], roam=200)
mem("Stonecrush rockgrinder", "Stonecrush rockgrinder", "orange", faction="stonecrush", guild="the Stonecrush", aggro=[85, 550], roam=200)
mem("Stonecrush demolisher", "Stonecrush demolisher", "red", faction="stonecrush", guild="the Stonecrush", aggro=[90, 550], roam=150)
mem("granite giant", "granite giant", "orange", faction="giants", guild=G, aggro=[75, 550], roam=300)
mem("granite giant herdsman", "granite giant herdsman", "orange", faction="giants", guild=G, aggro=[80, 550], roam=350)
mem("granite giant gatherer", "granite giant gatherer", "orange", faction="giants", guild=G, aggro=[80, 550], roam=300)
mem("granite giant stoneshaper", "granite giant stoneshaper", "orange", faction="giants", guild=G, aggro=[85, 550], roam=250)
mem("granite giant stonecaller", "granite giant stonecaller", "red", faction="giants", guild=G, aggro=[90, 600], roam=150)
mem("granite giant outlooker", "granite giant outlooker", "orange", faction="giants", guild=G, aggro=[90, 700], roam=200)
mem("granite giant pounder", "granite giant pounder", "red", faction="giants", guild=G, aggro=[90, 600], roam=250)
mem("granite giant stonelord", "granite giant stonelord", "red", faction="giants", guild=G, aggro=[95, 650], roam=150)
mem("granite giant stonemender", "granite giant stonemender", "red", faction="giants", guild=G, aggro=[95, 600], roam=80)
mem("granite giant reinforcer", "granite giant reinforcer", "red", faction="giants", guild=G, aggro=[95, 600], roam=80)
mem("granite giant elder", "granite giant elder", "red", faction="giants", guild="the Throne's Elders", aggro=[95, 650], roam=60)
mem("granite giant oracle", "granite giant oracle", "red", faction="giants", guild="the Throne's Elders", aggro=[95, 650], roam=60)
# the moor's two named giants of the campaign
mem("the Stone-Herald", "granite giant stonecaller", "purple", name="the Stone-Herald", size=1.35, faction="giants",
    guild="Voice of Golestandt", aggro=[95, 700], roam=40, guards={"granite giant stonecaller": 2})
mem("Gorm Throne-Warden", "granite giant stonelord", "purple", name="Gorm Throne-Warden", size=1.4, faction="giants",
    guild="Keeper of Gogmagog's Throne", aggro=[95, 700], roam=40, guards={"granite giant stonelord": 2})

# ---- the pockets (they stay when the Watch wins)
b.wild("pocket_north_lake", 1100, 130, 1450, 330, {"dartmoor pony": 8, "granite giant herdsman": 3, "granite giant": 3})
b.camp("pocket_stonemenders", 1383, 779, 9, {"granite giant stonemender": 3}, 600)
# ---- the Stonecrush Diggings (cp1, the west)
b.camp("cp1_garrison", 230, 720, 16, {"Stonecrush rockgrinder": 3, "Stonecrush excavator": 3, "granite giant stonecaller": 1}, 360)
b.wild("cp1_diggings", 90, 450, 310, 1200, {"Stonecrush excavator": 12, "Stonecrush rockgrinder": 10})
b.wild("west_south_digs", 90, 1200, 340, 1400, {"Stonecrush demolisher": 6, "Stonecrush rockgrinder": 4})
b.camp("reinforcers", 199, 1007, 9, {"granite giant reinforcer": 3}, 600)
b.wild("grimspound_road", 90, 150, 300, 450, {"Stonecrush excavator": 6, "dartmoor pony": 4})
# ---- the Pony Moor (cp2, the north)
b.camp("cp2_garrison", 960, 380, 16, {"granite giant herdsman": 2, "granite giant": 3, "granite giant stonecaller": 1}, 360)
b.wild("cp2_moor", 650, 150, 1250, 520, {"granite giant": 10, "granite giant herdsman": 4, "dartmoor pony": 8})
b.camp("brigand_camp", 1004, 524, 10, {"ruthless brigand": 6}, 300)
# ---- the Stonecallers' Ring (cp3, the middle valleys)
b.camp("cp3_garrison", 760, 800, 16, {"the Stone-Herald": 1, "granite giant gatherer": 3}, 900)
b.wild("cp3_ring", 400, 500, 1100, 950, {"granite giant gatherer": 14, "granite giant stonecaller": 8, "granite giant stoneshaper": 8})
b.patrol("middle_giants", [(500, 900), (750, 1000), (1000, 950), (1250, 880)], {"granite giant stoneshaper": 2, "granite giant outlooker": 1})
b.wild("east_valley", 1280, 450, 1500, 1100, {"granite giant stoneshaper": 6, "granite giant gatherer": 6})
# ---- the Pounders' Road (cp4, the south)
b.camp("cp4_garrison", 1060, 1180, 16, {"granite giant outlooker": 3, "granite giant pounder": 3}, 360)
b.wild("cp4_road", 600, 1000, 1250, 1350, {"granite giant outlooker": 10, "granite giant pounder": 10})
b.wild("knockers_hollow", 1016, 1040, 1425, 1300, {"granite knocker": 10})
# ---- the Giants' Throne (the raid's place) and the elders
b.wild("throne_court", 1120, 1330, 1460, 1560, {"granite giant stonelord": 8, "granite giant pounder": 4})
b.camp("throne_guard", 1310, 1470, 10, {"Gorm Throne-Warden": 1}, 1200)
b.camp("elders", 1405, 1490, 9, {"granite giant elder": 2, "granite giant oracle": 2}, 900)
b.clear("the_throne", 1240, 1420, 60, ["granite giant stonelord", "granite giant pounder"])
# Grimspound stays quiet
b.clear("grimspound", 135, 315, 90, ["Stonecrush excavator", "Stonecrush rockgrinder", "dartmoor pony", "Dartmoor pony"])
b.S[-1]["block"] = "all"

themes = ["Grimspound (the Dragon-Watch's muster)", "The Stonecrush Diggings (west)", "The Pony Moor (north)",
          "The Stonecallers' Ring (the middle valleys)", "The Pounders' Road and the knockers' hollow (south)",
          "The Giants' Throne (south-east - the raid)", "Golestandt's lair (south: sealed until the Watch holds the moor)"]
notes = ("Albion's plan 2026-11-24, round 4: Elite - Golestandt's lair; nothing below orange while the giants hold the moor; the "
         "Dragon-Watch's campaign (AlbionCampaign.cs) and the Giants' Throne raid; Golestandt sealed until it's won. Coordinates are "
         "zone units (metres x 40).")
tiers = {"Tegbuk": "red", "Trahern": "red", "Borimo": "red", "Agidad": "red", "Brannoc": "red", "Kez": "red",
         "Moran the Mighty": "purple", "Dartmoor pony": "orange"}
factions = {"giants": {"id": 9501, "aggro": 95}, "stonecrush": {"id": 9502, "aggro": 85}, "knockers": {"id": 9503, "aggro": 80},
            "brigands": {"id": 9504, "aggro": 85, "enemies": ["giants"]}}
b.write(sys.argv[1], themes, notes, ["Golestandt"], tiers, factions)
