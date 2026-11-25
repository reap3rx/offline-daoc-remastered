"""Llyn Barfog's zone build (claude 2026-11-24, "Albion - the plan", round 4): Elite - Morgana's seat, nothing below orange while
her host holds the lake. The north thread's end: Morgana le Fay sits at the Gate of Annwn on the south shore, where Arthur dragged
the Afanc out of the water; her hounds of Annwn run the hills, cythraul come up through the gate, the Crimson keep her posts round
the shore, and the Ellyll of the south-west wood are her fay kin. The Lake Host's campaign (AlbionCampaign.cs) takes the shores back
one at a time - the Afanc's Shore, the Bwgan Hills, the Western Shore, the Fay Wood - then the Gate (MorganaRaid.cs). Won, every
site but the pockets is swept. The Wrath of Mordred and the Legendary Afanc are hers now: they wait at the Gate, in her raid, and
are kept out of the world. About 560."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(7, 'Llyn Barfog', 'elite', 1.5)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
# the lake's own beasts (the pockets keep some)
mem("lake adder", "lake adder", "orange", faction="lake", aggro=[70, 450], roam=250)
mem("diamondback toad", "diamondback toad", "orange", faction="lake", aggro=[80, 500], roam=200)
mem("bearded gorger", "bearded gorger", "red", faction="lake", aggro=[90, 550], roam=150)
mem("afanc hatchling", "afanc hatchling", "orange", faction="lake", aggro=[85, 500], roam=200)
mem("black bear", "black bear", "orange", aggro=[70, 450], roam=350)
mem("huge boar", "huge boar", "orange", aggro=[70, 450], roam=350)
mem("bwgan", "bwgan", "orange", faction="bwgan", aggro=[75, 500], roam=250)
mem("bwgan hunter", "bwgan hunter", "orange", faction="bwgan", aggro=[80, 550], roam=350)
mem("bwgwl", "bwgwl", "red", faction="bwgan", aggro=[85, 550], roam=150)
mem("cyclops", "cyclops", "red", aggro=[85, 550], roam=200)
mem("undead monk", "undead monk", "orange", faction="dead", aggro=[80, 500], roam=120)
mem("skeletal legionnaire", "skeletal legionnaire", "orange", name="legionary of the pact", faction="dead", aggro=[85, 500], roam=120)
# Morgana's host
mem("hound of Annwn", "cwn annwn", "orange", name="hound of Annwn", faction="annwn", guild="the Hunt of Annwn", aggro=[90, 650], roam=450)
mem("cythraul", "cythraul", "orange", faction="annwn", aggro=[90, 600], roam=250)
mem("wicked cythraul", "wicked cythraul", "red", faction="annwn", aggro=[95, 600], roam=200)
mem("gwr-drwgiaid", "gwr-drwgiaid", "orange", faction="annwn", aggro=[85, 550], roam=300)
mem("crimson acolyte", "Crimson Initiate", "orange", name="crimson acolyte", size=0.9, faction="crimson", guild="the Crimson",
    aggro=[90, 600], roam=120)
mem("crimson gatekeeper", "Crimson Initiate", "red", name="crimson gatekeeper", faction="crimson", guild="the Crimson",
    aggro=[95, 650], roam=80)
mem("guardian of Morgana", "Crimson Initiate", "red", name="guardian of Morgana", model=1900, faction="crimson",
    guild="Morgana's Guard", aggro=[95, 650], roam=100)
mem("necromancer", "necromancer", "red", faction="crimson", guild="the Crimson", aggro=[95, 650], roam=60)
mem("fay knight", "Crimson Initiate", "red", name="fay knight", model=1900, size=1.1, faction="crimson", guild="Morgana's Guard",
    aggro=[95, 650], roam=120)
# her posts round the shore - each with a captain (named purple-ish reds) the Host must break
mem("Gate-Captain Branwen", "Crimson Initiate", "purple", name="Gate-Captain Branwen", model=1900, size=1.2, faction="crimson",
    guild="Morgana's Guard", aggro=[95, 700], roam=40, guards={"guardian of Morgana": 2})
mem("Huntsman of Annwn", "cwn annwn", "purple", name="the Huntsman of Annwn", model=24, size=1.3, faction="annwn",
    guild="Master of the Hunt", aggro=[95, 700], roam=300, guards={"hound of Annwn": 3})

# ---- the pockets (Morgana's victims and the lake's own: they stay when the Host wins)
b.wild("pocket_north_hills", 180, 100, 1050, 300, {"bwgan": 8, "bwgan hunter": 4, "huge boar": 6, "cyclops": 3})
b.camp("pocket_bwgwl_rocks", 875, 161, 9, {"bwgwl": 5}, 420)
b.wild("pocket_east_woods", 1150, 700, 1470, 1400, {"black bear": 14, "huge boar": 6})
b.camp("pocket_monastery", 1300, 185, 9, {"undead monk": 6, "skeletal legionnaire": 4}, 420)
# ---- the Afanc's Shore (cp1)
b.camp("cp1_garrison", 1000, 520, 16, {"crimson gatekeeper": 1, "crimson acolyte": 4, "hound of Annwn": 3}, 360)
b.wild("cp1_shore", 820, 420, 1150, 620, {"diamondback toad": 10, "afanc hatchling": 6, "hound of Annwn": 6, "crimson acolyte": 4})
b.wild("hobgoblin_ridge", 1050, 240, 1320, 700, {"gwr-drwgiaid": 8, "hound of Annwn": 6})
# ---- the Bwgan Hills (cp2)
b.camp("cp2_garrison", 560, 430, 16, {"crimson gatekeeper": 1, "crimson acolyte": 3, "cythraul": 3, "necromancer": 1}, 360)
b.wild("cp2_hills", 380, 300, 760, 560, {"cythraul": 10, "crimson acolyte": 8, "bwgan": 6, "diamondback toad": 6})
b.camp("bwgan_camp", 470, 400, 9, {"bwgan": 4, "bwgan hunter": 2}, 300)
# ---- the Western Shore (cp3)
b.camp("cp3_garrison", 260, 820, 16, {"guardian of Morgana": 2, "crimson acolyte": 3, "wicked cythraul": 2}, 360)
b.wild("cp3_shore", 150, 600, 390, 1100, {"diamondback toad": 10, "bearded gorger": 4, "gwr-drwgiaid": 6, "cythraul": 6})
b.camp("west_hounds", 300, 1000, 12, {"Huntsman of Annwn": 1}, 1200)
b.wild("lake_south_west", 380, 1100, 650, 1180, {"lake adder": 10, "diamondback toad": 6})
# ---- the Fay Wood (cp4)
b.camp("cp4_garrison", 500, 1300, 16, {"guardian of Morgana": 2, "fay knight": 2, "wicked cythraul": 2}, 360)
b.wild("cp4_wood", 250, 1220, 700, 1450, {"fay knight": 6, "wicked cythraul": 6, "hound of Annwn": 8, "gwr-drwgiaid": 6})
# ---- the Gate of Annwn (the raid's place) and the south shore
b.wild("south_shore", 650, 1150, 1100, 1450, {"hound of Annwn": 10, "cythraul": 10, "crimson acolyte": 8, "lake adder": 8})
b.camp("gate_guard", 870, 1300, 12, {"Gate-Captain Branwen": 1, "fay knight": 2}, 1200)
b.wild("east_shore", 980, 850, 1150, 1150, {"lake adder": 10, "diamondback toad": 6, "hound of Annwn": 4})
# the Gate itself stays clear for her raid; she keeps her champion and her beast there, out of the world
b.clear("the_gate", 760, 1230, 70, ["hound of Annwn", "cythraul", "crimson acolyte", "lake adder", "Gate-Captain Branwen", "fay knight"])
b.clear("mordred_bound", 1120, 1119, 60, ["Wrath of Mordred"])
b.clear("afanc_bound", 948, 525, 120, ["Legendary Afanc"])
# the merchants on the east shore, the stables at the east gate and Sir Percival's muster stay quiet
b.clear("merchants", 885, 780, 90, ["lake adder", "spiny eel", "diamondback toad", "black bear", "hound of Annwn", "gwr-drwgiaid"])
b.S[-1]["block"] = "all"
b.clear("east_gate", 1510, 640, 70, ["renegade guard", "black bear", "huge boar"])
b.S[-1]["block"] = "all"

themes = ["The merchants on the east shore (the Lake Host's muster)", "The Afanc's Shore (north)", "The Bwgan Hills (north-west)",
          "The Western Shore and the Huntsman of Annwn", "The Fay Wood (south-west, the Ellyll)", "The Gate of Annwn (south shore - the raid)",
          "The monastery and the north hills (pockets)"]
notes = ("Albion's plan 2026-11-24, round 4: Elite - Morgana's seat; nothing below orange while her host holds the lake; the Lake "
         "Host's campaign (AlbionCampaign.cs) and her raid at the Gate (MorganaRaid.cs). Coordinates are zone units (metres x 40).")
tiers = {"Ellyll guard": "red", "Ellyll sage": "red", "Ellyll windchaser": "red", "Ellyll froglord": "red", "Ellyl champion": "red",
         "Ellyll Seer": "red", "Welsh hobgoblin": "orange", "Evocatus praetorii": "red", "Llyn Cythraul": "red",
         "Siemus Tracksniffer": "red", "Sir Dillus": "red", "King of the Barfog Hills": "purple", "Fester": "purple",
         "Mouth": "purple", "Teazanodwc": "purple", "frenzied feeder": "red", "needletooth devourer": "red"}
factions = {"lake": {"id": 9491, "aggro": 75}, "bwgan": {"id": 9492, "aggro": 75}, "dead": {"id": 9493, "aggro": 85},
            "annwn": {"id": 9494, "aggro": 95}, "crimson": {"id": 9495, "aggro": 95}}
b.write(sys.argv[1], themes, notes, ["Ellyll guard", "Ellyll sage", "Ellyll windchaser", "Ellyll froglord", "Ellyl champion"], tiers, factions)
