"""Malmohus's zone build (claude 2026-11-25, "Midgard - the plan", round 4): Elite - Gjalpinulva's seat, nothing below orange
while the drakulv hold the south. The south thread's end: the dragon sleeps under Malmohus, and her drakulv - missionaries,
armguards, axehands, sacrificers, protectors, executioners - and the svartalf they bought hold every road to her Wyrm-Temple, where
the Hierophant waits for the second half of her name. The Volur's Oath marches from Halla's camp (AlbionCampaign.cs, the Dragon-Oath)
and takes the south back a post at a time - the Missionary Road, the Svartalf Foist, the Armguard Lines, the Temple Steps - then the
Wyrm-Temple (HierophantRaid.cs). Won, every site but the pockets is swept, and Gjalpinulva can be fought (sealed until then)."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from zbcommon import Build
b = Build(116, 'Malmohus', 'elite', 4.0)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
DK, SV = "Gjalpinulva's Drakulv", "the Scale-Traders"
# the south's own (the pockets keep them)
mem("scaled varg yearling", "scaled varg yearling", "orange", faction="varg", aggro=[70, 450], roam=250)
mem("scaled varg snarler", "scaled varg snarler", "orange", faction="varg", aggro=[85, 550], roam=300)
mem("enraged mara", "enraged mara", "red", aggro=[85, 550], roam=250)
mem("venomous tree crawler", "venomous tree crawler", "red", aggro=[85, 550], roam=150)
mem("backwoods marodor", "backwoods marodor", "orange", aggro=[80, 500], roam=250)
# the drakulv
mem("drakulv missionary", "drakulv missionary", "orange", faction="drakulv", guild=DK, aggro=[90, 600], roam=200)
mem("patrolling drakulv", "patrolling drakulv", "orange", faction="drakulv", guild=DK, aggro=[90, 600], roam=400)
mem("drakulv armguard", "drakulv armguard", "orange", faction="drakulv", guild=DK, aggro=[90, 650], roam=200)
mem("drakulv axehand", "drakulv axehand", "orange", faction="drakulv", guild=DK, aggro=[90, 650], roam=200)
mem("drakulv sacrificer", "drakulv sacrificer", "red", faction="drakulv", guild=DK, aggro=[95, 650], roam=120)
mem("drakulv attendant", "drakulv attendant", "orange", faction="drakulv", guild=DK, aggro=[90, 650], roam=150)
mem("drakulv protector", "drakulv protector", "red", faction="drakulv", guild=DK, aggro=[95, 650], roam=120)
mem("drakulv executioner", "drakulv executioner", "red", faction="drakulv", guild=DK, aggro=[95, 700], roam=100)
mem("drakulv disciple", "drakulv disciple", "red", faction="drakulv", guild="the Hierophant's Disciples", aggro=[95, 700], roam=80)
mem("drakulv soultrapper", "drakulv soultrapper", "red", faction="drakulv", guild="the Hierophant's Disciples", aggro=[95, 700], roam=80)
# the svartalf they bought
mem("svartalf infiltrator", "svartalf infiltrator", "orange", faction="drakulv", guild=SV, aggro=[85, 600], roam=250)
mem("svartalf foister", "svartalf foister", "orange", faction="drakulv", guild=SV, aggro=[90, 600], roam=200)
mem("svartalf bloodbinder", "svartalf bloodbinder", "red", faction="drakulv", guild=SV, aggro=[95, 650], roam=120)
mem("Scale-Lord Kariig", "svartalf bloodbinder", "purple", name="Scale-Lord Kariig", size=1.2, faction="drakulv", guild="Lord of the Svartalf Foist",
    aggro=[95, 700], roam=40, guards={"svartalf foister": 2})
mem("Temple-Warden Brandr", "drakulv executioner", "purple", name="Temple-Warden Brandr", size=1.25, faction="drakulv", guild="Warden of the Wyrm-Temple",
    aggro=[95, 700], roam=40, guards={"drakulv protector": 2})

# ---- the pockets (the south's own: they stay when the Oath wins)
b.camp("pocket_yearlings", 855, 255, 12, {"scaled varg yearling": 8}, 420)
b.wild("pocket_mara", 970, 1050, 1360, 1500, {"enraged mara": 4, "scaled varg snarler": 6})
b.camp("pocket_crawlers", 180, 1340, 10, {"venomous tree crawler": 3}, 600)
b.wild("pocket_backwoods", 160, 560, 500, 760, {"backwoods marodor": 6, "scaled varg snarler": 4})
# ---- the Missionary Road (cp1)
b.camp("cp1_garrison", 600, 300, 16, {"drakulv sacrificer": 1, "drakulv missionary": 4, "patrolling drakulv": 3}, 360)
b.wild("cp1_road", 215, 100, 890, 550, {"drakulv missionary": 10, "patrolling drakulv": 10, "backwoods marodor": 4})
# ---- the Svartalf Foist (cp2)
b.camp("cp2_garrison", 1350, 500, 16, {"svartalf bloodbinder": 1, "svartalf foister": 4, "svartalf infiltrator": 3}, 360)
b.wild("cp2_foist", 1050, 100, 1510, 940, {"svartalf foister": 10, "svartalf infiltrator": 8, "svartalf bloodbinder": 4, "patrolling drakulv": 4})
b.camp("foist_hall", 1460, 820, 12, {"Scale-Lord Kariig": 1}, 1200)
# ---- the Armguard Lines (cp3)
b.camp("cp3_garrison", 750, 850, 16, {"drakulv sacrificer": 1, "drakulv armguard": 4, "drakulv axehand": 2}, 360)
b.wild("cp3_lines", 110, 600, 1300, 1050, {"drakulv armguard": 14, "drakulv axehand": 8, "drakulv sacrificer": 4, "scaled varg snarler": 6})
# ---- the Temple Steps (cp4)
b.camp("cp4_garrison", 700, 1200, 16, {"drakulv executioner": 1, "drakulv protector": 3, "drakulv attendant": 3}, 360)
b.wild("cp4_steps", 150, 1060, 960, 1500, {"drakulv protector": 8, "drakulv executioner": 4, "drakulv attendant": 8, "drakulv axehand": 4})
b.camp("disciples", 460, 1240, 12, {"drakulv disciple": 3, "drakulv soultrapper": 2}, 600)
# ---- the Wyrm-Temple (the raid's place) and Gjalpinulva's lair
b.camp("temple_guard", 980, 1320, 12, {"Temple-Warden Brandr": 1, "drakulv attendant": 2}, 1200)
b.clear("wyrm_temple", 900, 1380, 60, list(m.keys()))
b.clear("gjalpinulva_lair", 517, 1370, 70, list(m.keys()))
# Halla's camp (the Dragon-Oath musters there) stays quiet
b.clear("hallas_camp", 1000, 500, 90, list(m.keys()))
b.S[-1]["block"] = "all"

themes = ["Halla's camp (the Dragon-Oath musters there)", "The Missionary Road (north)", "The Svartalf Foist (east) and Scale-Lord Kariig",
          "The Armguard Lines (middle)", "The Temple Steps (south)", "The Wyrm-Temple (south - the raid) and Gjalpinulva's lair (south-west)",
          "The varg yearlings, the mara, the backwoods (pockets)"]
notes = ("Midgard's plan 2026-11-25, round 4: Elite - Gjalpinulva's seat; nothing below orange while the drakulv hold the south; the "
         "Dragon-Oath (AlbionCampaign.cs) and the Hierophant's raid at the Wyrm-Temple (HierophantRaid.cs); the dragon sealed until "
         "it is won. Coordinates are zone units (metres x 40).")
tiers = {"Yar": "purple", "Kleng": "red", "Burr": "red", "Arnulv": "red", "Gunnolf": "red", "Kariig": "red", "Bjornvarg": "red",
         "Steinolf": "red", "Hrolleif": "red", "Ulf": "red", "Eiorharn": "red", "Geirolf": "red", "Eildird": "red", "Ingardild": "red",
         "Ljornrn": "red", "Desukva": "red", "Rana": "red", "Wyulv": "red", "Esulv": "red", "hunter's pet": "orange",
         "svartalf dark forester": "orange", "swarm of flies": "orange"}
factions = {"varg": {"id": 9691, "aggro": 80}, "drakulv": {"id": 9692, "aggro": 95}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
