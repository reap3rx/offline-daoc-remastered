"""West Svealand's zone build (claude 2026-11-24, "Midgard - the plan", round 2): Wild - blues and yellows round Huginfel and on
the eastern meadows, the skogsfru wood in the middle - and Dangerous in the west, the Blodfelag's country. The west thread: the
Blodfelag, the 'blood-fellowship', swear blood-oaths to the Fenris-wolf's children; their windcallers bring snow down off the
mountains in summer, and their hall in the west, the Blood-Hall, is the zone's siege. In the south-west corner a gully has frozen
over and will not thaw. The south thread brushes the svartalf hunters on the southern road."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from zbcommon import Build
b = Build(102, 'West Svealand', 'wild', 3.2)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
B = "the Blodfelag"
mem("grass cat", "grass cat", "green", roam=300)
mem("grass viper", "grass viper", "blue", aggro=[30, 300], roam=200)
mem("ribbon toad", "ribbon toad", "blue", roam=200)
mem("black mauler", "black mauler", "blue", aggro=[40, 350], roam=300)
mem("large sveawolf", "large sveawolf", "blue", faction="wolves", aggro=[50, 400], roam=350)
mem("grizzled sveawolf", "grizzled sveawolf", "blue", faction="wolves", aggro=[50, 400], roam=350)
mem("bloodthirsty she-wolf", "bloodthirsty she-wolf", "yellow", faction="wolves", aggro=[60, 450], roam=350)
mem("lake serpent", "lake serpent", "blue", roam=200)
mem("water sprite", "water sprite", "blue", faction="sprites", roam=250)
mem("wind sprite", "wind sprite", "blue", faction="sprites", aggro=[40, 350], roam=300)
mem("skogsfru", "skogsfru", "yellow", faction="sprites", aggro=[50, 400], roam=200)
mem("savage lynx", "savage lynx", "yellow", aggro=[50, 400], roam=300)
mem("minor fideal", "minor fideal", "yellow", faction="sprites", aggro=[50, 400], roam=200)
mem("shadow", "shadow", "blue", faction="dead", aggro=[50, 400], roam=200)
mem("sanguinite ghoul", "sanguinite ghoul", "yellow", faction="dead", aggro=[50, 400], roam=200)
mem("mindless thrall", "mindless thrall", "blue", faction="blodfelag", guild=B, aggro=[50, 400], roam=200)
mem("blodfelag oathbreaker", "blodfelag oathbreaker", "blue", faction="blodfelag", guild=B, aggro=[50, 400], roam=250)
mem("blodfelag henchman", "blodfelag henchman", "blue", faction="blodfelag", guild=B, aggro=[50, 400], roam=200)
mem("blodfelag warhound", "blodfelag warhound", "yellow", faction="blodfelag", guild=B, aggro=[60, 450], roam=300)
mem("blodfelag dreng", "blodfelag dreng", "yellow", faction="blodfelag", guild=B, aggro=[60, 450], roam=200)
mem("blodfelag partisan", "blodfelag partisan", "yellow", faction="blodfelag", guild=B, aggro=[60, 450], roam=250)
mem("blodfelag windcaller", "blodfelag windcaller", "orange", faction="blodfelag", guild=B, aggro=[70, 500], roam=150)
mem("blodfelag svard", "blodfelag svard", "orange", faction="blodfelag", guild=B, aggro=[70, 500], roam=150)
mem("blodfelag wolfwarrior", "blodfelag wolfwarrior", "orange", faction="blodfelag", guild=B, aggro=[70, 500], roam=200)
mem("blodfelag haxa", "blodfelag haxa", "orange", faction="blodfelag", guild=B, aggro=[70, 500], roam=100)
mem("frothing sveawolf", "frothing sveawolf", "orange", faction="wolves", aggro=[70, 500], roam=350)
mem("rabid sveawolf", "rabid sveawolf", "yellow", faction="wolves", aggro=[60, 450], roam=350)
mem("phantom wolf", "phantom wolf", "orange", faction="wolves", aggro=[70, 500], roam=300)
mem("Blood-Warden Ketil", "blodfelag svard", "red", name="Blood-Warden Ketil", size=1.2, faction="blodfelag", guild="Warden of the Blood-Hall",
    aggro=[80, 550], roam=40, guards={"blodfelag svard": 2})
mem("svartalf hunter", "svartalf hunter", "yellow", faction="svartalf", aggro=[60, 450], roam=250)
mem("svartalf chanter", "svartalf chanter", "yellow", faction="svartalf", aggro=[60, 450], roam=120)
mem("frosty colt", "frosty colt", "orange", faction="frost", aggro=[60, 450], roam=200)
mem("cold light", "cold light", "orange", faction="frost", aggro=[70, 500], roam=150)
mem("snow imp", "snow imp", "orange", faction="frost", aggro=[70, 500], roam=200)

for i, x, y, r in [("huginfel", 1404, 1166, 120), ("vindsaul_faste", 1217, 40, 110), ("larsson_stable", 130, 692, 40)]:
    b.clear(i, x, y, r, ["grass cat", "grass viper", "ribbon toad", "blodfelag oathbreaker", "blodfelag henchman", "mindless thrall",
                         "large sveawolf", "black mauler", "lake serpent"])
    b.S[-1]["block"] = "all"
b.wild("east_meadows", 1100, 250, 1620, 1420, {"grass cat": 10, "grass viper": 8, "ribbon toad": 8, "black mauler": 8, "large sveawolf": 6,
                                             "water sprite": 4})
b.wild("eastern_shore", 1500, 200, 1630, 900, {"lake serpent": 8})
b.camp("oathbreaker_camp", 1250, 950, 12, {"blodfelag oathbreaker": 5, "blodfelag henchman": 3, "mindless thrall": 4}, 360)
b.wild("thrall_road", 1150, 500, 1450, 1000, {"mindless thrall": 6, "blodfelag oathbreaker": 6, "blodfelag henchman": 4})
b.wild("skogsfru_wood", 700, 300, 1150, 1250, {"skogsfru": 10, "wind sprite": 12, "savage lynx": 8, "bloodthirsty she-wolf": 6,
                                             "grizzled sveawolf": 6, "minor fideal": 4})
b.camp("skogsfru_grove", 650, 280, 12, {"skogsfru": 4, "wind sprite": 3}, 420)
b.wild("ghoul_hollow", 1290, 1150, 1600, 1410, {"shadow": 10, "sanguinite ghoul": 3})
b.wild("blodfelag_lands", 150, 220, 700, 1250, {"blodfelag dreng": 10, "blodfelag warhound": 10, "blodfelag partisan": 6,
                                              "rabid sveawolf": 8, "frothing sveawolf": 6, "phantom wolf": 5, "blodfelag windcaller": 4})
b.camp("blood_hall", 420, 820, 16, {"Blood-Warden Ketil": 1, "blodfelag svard": 3, "blodfelag windcaller": 3, "blodfelag dreng": 3}, 600)
b.camp("blood_hall_yard", 470, 870, 12, {"blodfelag dreng": 3, "blodfelag warhound": 4}, 420)
b.camp("wolfwarrior_camp", 400, 380, 12, {"blodfelag wolfwarrior": 5, "frothing sveawolf": 3}, 420)
b.camp("haxa_circle", 320, 330, 9, {"blodfelag haxa": 3}, 600)
b.wild("svartalf_road", 320, 1300, 1460, 1540, {"svartalf hunter": 8, "savage lynx": 4, "minor fideal": 4})
b.camp("svartalf_camp", 1015, 1390, 10, {"svartalf chanter": 3, "svartalf hunter": 3}, 420)
b.camp("frozen_gully", 330, 1500, 12, {"frosty colt": 3, "cold light": 3, "snow imp": 3}, 600)

themes = ["Huginfel, Vindsaul Faste and the eastern meadows (Wild)", "The thrall road and the oathbreakers' camp",
          "The skogsfru wood (the middle)", "The Blodfelag's country and the Blood-Hall (west: Dangerous - the siege)",
          "The frozen gully (south-west: summer frost that won't thaw)", "The svartalf road (south)"]
notes = ("Midgard's plan 2026-11-24, round 2: Wild, Dangerous round the Blodfelag camp; the west thread's blood-oath cult and the "
         "Blood-Hall siege. Coordinates are zone units (metres x 40).")
tiers = {"Giant Lemer": "orange", "Growling Ghost": "orange", "Pawper": "orange", "Fridgeir Gestsson": "orange", "Golga": "yellow",
         "Old Smoke": "yellow", "Modervarg": "yellow"}
factions = {"wolves": {"id": 9621, "aggro": 70}, "sprites": {"id": 9622, "aggro": 50}, "dead": {"id": 9623, "aggro": 70},
            "blodfelag": {"id": 9624, "aggro": 85}, "svartalf": {"id": 9625, "aggro": 70}, "frost": {"id": 9626, "aggro": 85}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
