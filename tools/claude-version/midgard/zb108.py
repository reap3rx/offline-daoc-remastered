"""Raumarik's zone build (claude 2026-11-25, "Midgard - the plan", round 4): Elite - Hati's seat, nothing below orange while his
host holds the north. The west thread's end: Hati, the wolf that hunts the moon - Fenrir's son - waits in his howe in the west for
the moon to run close enough to catch; his host holds Raumarik: the fenrir soldiers and their mystics, the savage winterwolves, the
wraiths and wights of the endless winter, the icestriders of the north-east fells. King Eirik's Host marches from the trappers' camp
(AlbionCampaign.cs, the King's March) and takes the north back a post at a time - the Icestrider Fells, the Wraith Moor, the
Winterwolf Run, the Fenrir Camp - then Hati's Howe (HatiRaid.cs). Won, every site but the pockets is swept."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from zbcommon import Build
b = Build(108, 'Raumarik', 'elite', 4.2)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
HH = "Hati's Host"
# the north's own (the pockets keep them)
mem("frost bound bear", "frost bound bear", "orange", aggro=[70, 450], roam=300)
mem("frigid broadleaf", "frigid broadleaf", "red", aggro=[80, 450], roam=20)
mem("sleipneirsson", "sleipneirsson", "orange", aggro=[60, 450], roam=400)
mem("frost stallion", "frost stallion", "orange", aggro=[60, 450], roam=400)
mem("mature wyvern", "mature wyvern", "red", aggro=[85, 550], roam=300)
mem("dire wolverine", "dire wolverine", "red", aggro=[85, 550], roam=250)
mem("bounty hunter", "bounty hunter", "orange", faction="daggers", guild="the Red Daggers", aggro=[80, 500], roam=150)
mem("bounty hunter leader", "bounty hunter leader", "red", faction="daggers", guild="the Red Daggers", aggro=[85, 550], roam=80)
mem("undead soldier", "undead soldier", "orange", faction="winter", aggro=[80, 500], roam=100)
mem("frost cyclops", "frost cyclops", "red", aggro=[90, 600], roam=150)
mem("icestrider chiller", "icestrider chiller", "orange", faction="ice", aggro=[75, 500], roam=250)
mem("icestrider frostweaver", "icestrider frostweaver", "orange", faction="ice", aggro=[75, 500], roam=200)
mem("icestrider interceptor", "icestrider interceptor", "red", faction="ice", aggro=[85, 550], roam=250)
# Hati's host
mem("fenrir soldier", "fenrir soldier", "orange", faction="host", guild=HH, aggro=[90, 650], roam=200)
mem("fenrir mystic", "fenrir mystic", "red", faction="host", guild=HH, aggro=[95, 650], roam=100)
mem("greater fenrir", "greater fenrir", "red", faction="host", guild=HH, aggro=[95, 700], roam=150)
mem("savage winterwolf", "savage winterwolf", "orange", faction="host", guild=HH, aggro=[90, 650], roam=400)
mem("winter wolf", "winter wolf", "orange", faction="host", guild=HH, aggro=[85, 600], roam=350)
mem("windswept wraith", "windswept wraith", "orange", faction="winter", guild="of the endless winter", aggro=[90, 600], roam=250)
mem("chillsome wight", "chillsome wight", "orange", faction="winter", guild="of the endless winter", aggro=[90, 600], roam=200)
mem("frore lich", "frore lich", "red", faction="winter", guild="of the endless winter", aggro=[95, 650], roam=100)
mem("Fang-Captain of Hati", "greater fenrir", "purple", name="Fang-Captain of Hati", size=1.2, faction="host", guild="Captain of Hati's Host",
    aggro=[95, 700], roam=40, guards={"fenrir soldier": 2})
mem("Hati's Huntsman", "savage winterwolf", "purple", name="Hati's Huntsman", size=1.4, faction="host", guild="Master of the Moon-Hunt",
    aggro=[95, 700], roam=350, guards={"savage winterwolf": 3})

# ---- the pockets (the north's own: they stay when the Host wins)
b.wild("pocket_frost_wood", 890, 950, 1190, 1430, {"frost bound bear": 14})
b.camp("pocket_broadleaf", 1288, 1001, 12, {"frigid broadleaf": 4}, 600)
b.wild("pocket_sleipnir_plain", 190, 150, 880, 420, {"sleipneirsson": 6, "frost stallion": 4, "mature wyvern": 3})
b.camp("pocket_red_dagger", 910, 1120, 12, {"bounty hunter leader": 1, "bounty hunter": 5}, 600)
b.camp("pocket_cyclops", 232, 1372, 12, {"frost cyclops": 3}, 900)
b.camp("pocket_undead", 435, 1245, 9, {"undead soldier": 6}, 420)
b.wild("pocket_wolverines", 200, 1000, 500, 1400, {"dire wolverine": 4})
# ---- the Icestrider Fells (cp1)
b.camp("cp1_garrison", 1300, 471, 16, {"fenrir mystic": 1, "fenrir soldier": 4, "winter wolf": 3}, 360)
b.wild("cp1_fells", 1130, 170, 1600, 700, {"icestrider chiller": 10, "icestrider frostweaver": 8, "icestrider interceptor": 3, "winter wolf": 5})
# ---- the Wraith Moor (cp2)
b.camp("cp2_garrison", 850, 650, 16, {"frore lich": 1, "fenrir soldier": 3, "chillsome wight": 3}, 360)
b.wild("cp2_moor", 620, 430, 1100, 900, {"windswept wraith": 10, "chillsome wight": 8, "frore lich": 3})
# ---- the Winterwolf Run (cp3)
b.camp("cp3_garrison", 650, 1100, 16, {"greater fenrir": 1, "savage winterwolf": 4, "fenrir soldier": 2}, 360)
b.wild("cp3_run", 520, 900, 810, 1450, {"savage winterwolf": 12, "windswept wraith": 4})
b.camp("moon_hunt", 700, 1300, 12, {"Hati's Huntsman": 1}, 1200)
# ---- the Fenrir Camp (cp4)
b.camp("cp4_garrison", 450, 800, 16, {"greater fenrir": 1, "fenrir mystic": 2, "fenrir soldier": 4}, 360)
b.wild("cp4_camp", 200, 450, 620, 1000, {"fenrir soldier": 12, "fenrir mystic": 4, "savage winterwolf": 6})
# ---- Hati's Howe (the raid's place)
b.camp("howe_guard", 380, 560, 12, {"Fang-Captain of Hati": 1, "fenrir mystic": 2}, 1200)
b.clear("hatis_howe", 320, 600, 60, list(m.keys()))
# the trappers' camp (the King's March musters there) stays quiet
b.clear("trappers_camp", 1100, 900, 90, list(m.keys()))
b.S[-1]["block"] = "all"

themes = ["The trappers' camp (the King's March musters there)", "The Icestrider Fells (north-east)", "The Wraith Moor (middle)",
          "The Winterwolf Run (south-west) and Hati's Huntsman", "The Fenrir Camp (west)", "Hati's Howe (west - the raid)",
          "The frost wood, the Sleipnir plain, the Red Daggers, the cyclops (pockets)"]
notes = ("Midgard's plan 2026-11-25, round 4: Elite - Hati's seat; nothing below orange while his host holds the north; the King's "
         "March (AlbionCampaign.cs) and Hati's raid at his howe (HatiRaid.cs). Coordinates are zone units (metres x 40).")
tiers = {"Wretch of Winter": "purple", "Raumarik Revenant": "purple", "Hugi": "purple", "Loken": "purple", "Oona": "purple",
         "Hagall the Red Dagger": "red", "Runil": "red", "Red Hagen": "red", "Red Dagger": "red", "fylgja": "red",
         "enhorning": "red", "Servant of Kelic": "red", "wolf of loki": "red", "white wolf": "orange", "savage wyvern": "red",
         "Runemistress Shayla": "red", "Undead Patrol": "orange"}
factions = {"ice": {"id": 9681, "aggro": 80}, "host": {"id": 9682, "aggro": 95}, "winter": {"id": 9683, "aggro": 90},
            "daggers": {"id": 9684, "aggro": 85}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
