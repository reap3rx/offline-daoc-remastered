"""Vale of Mularn's zone build (claude 2026-11-24, "Midgard - the plan", round 1): Peaceful - the realm's hub, greens and blues
round Mularn, Haggerfel and Fort Veldon, a few yellows at the edges. Both threads show their first signs: the hounds go mad
round Darkness Falls (the wolves of the west), and a dragon-preacher has come to the Vendo Caverns (the drakulv of the south).
The hidden folk keep the western woods, the wood-eaters their hive in the south."""
import sys
sys.path.insert(0, '/home/claude/mid/r1')
from zbcommon import Build
b = Build(100, 'Vale of Mularn', 'peaceful', 3.5)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
mem("small hill cat", "small hill cat", "green", roam=300)
mem("hill cat", "hill cat", "blue", aggro=[30, 300], roam=300)
mem("little water goblin", "little water goblin", "green", faction="goblins", roam=200)
mem("hobgoblin prankster", "hobgoblin prankster", "green", faction="goblins", aggro=[30, 300], roam=250)
mem("hobgoblin snake-finder", "hobgoblin snake-finder", "green", faction="goblins", roam=250)
mem("mud snake", "mud snake", "green", roam=200)
mem("vein spiderling", "vein spiderling", "green", roam=200)
mem("vein spider", "vein spider", "blue", aggro=[30, 300], roam=200)
mem("wild hog", "wild hog", "green", roam=300)
mem("young lynx", "young lynx", "blue", roam=300)
mem("black mauler cub", "black mauler cub", "green", roam=250)
mem("meandering spirit", "meandering spirit", "blue", faction="dead", aggro=[30, 300], roam=200)
mem("hill person", "hill person", "blue", faction="hillfolk", aggro=[40, 350], roam=250)
mem("young grendelorm", "young grendelorm", "blue", roam=200)
mem("wood-eater", "wood-eater", "green", faction="hive", aggro=[30, 300], roam=200)
mem("wood-eater alate", "wood-eater alate", "blue", faction="hive", aggro=[40, 350], roam=250)
mem("wood-eater soldier", "wood-eater soldier", "blue", faction="hive", aggro=[50, 350], roam=150)
mem("wood-eater worker", "wood-eater worker", "green", faction="hive", roam=150)
mem("wood-eater hunter", "wood-eater hunter", "blue", faction="hive", aggro=[50, 400], roam=250)
mem("wood-eater royal guard", "wood-eater royal guard", "yellow", faction="hive", aggro=[60, 400], roam=60)
mem("wood-eater king", "wood-eater king", "yellow", faction="hive", aggro=[60, 400], size=1.2, roam=40, guards={"wood-eater royal guard": 2})
mem("huldu stalker", "huldu stalker", "blue", faction="huldu", aggro=[40, 350], roam=250)
mem("huldu hunter", "huldu hunter", "blue", faction="huldu", aggro=[40, 350], roam=250)
mem("huldu lurker", "huldu lurker", "green", faction="huldu", roam=200)
mem("huldu outcast", "huldu outcast", "green", faction="huldu", roam=200)
mem("phantom hound", "phantom hound", "blue", faction="hounds", aggro=[50, 400], roam=350)
mem("rabid wolfhound", "rabid wolfhound", "yellow", faction="hounds", aggro=[60, 450], roam=400)
mem("vendo warrior", "vendo warrior", "blue", faction="vendo", aggro=[50, 400], roam=200)
mem("vendo shaman", "vendo shaman", "blue", faction="vendo", aggro=[50, 400], roam=150)
mem("vendo bone-collector", "vendo bone-collector", "blue", faction="vendo", aggro=[50, 400], roam=250)
mem("vendo stalker", "vendo stalker", "yellow", faction="vendo", aggro=[60, 450], roam=250)
mem("vendo flayer", "vendo flayer", "yellow", faction="vendo", aggro=[60, 450], roam=100)
mem("hobyah", "hobyah", "blue", faction="vendo", aggro=[40, 400], roam=250)
mem("dragon-preacher", "drakulv missionary", "yellow", name="dragon-preacher", faction="vendo", guild="Gjalpinulva's Missionaries",
    aggro=[60, 450], roam=60, guards={"vendo flayer": 1})

# Mularn, Haggerfel, Fort Veldon and the Jordheim road stay quiet
for i, x, y, r in [("mularn", 1245, 1320, 120), ("haggerfel", 1300, 750, 110), ("fort_veldon", 1155, 170, 100), ("jordheim_gate", 1230, 1500, 70)]:
    b.clear(i, x, y, r, ["small hill cat", "hill cat", "hobgoblin prankster", "little water goblin", "mud snake", "vein spiderling", "wild hog"])
    b.S[-1]["block"] = "all"
b.wild("mularn_meadows", 900, 950, 1500, 1460, {"small hill cat": 14, "hobgoblin prankster": 10, "little water goblin": 8, "mud snake": 6,
                                              "vein spiderling": 6, "hobgoblin snake-finder": 4})
b.wild("haggerfel_fields", 950, 420, 1500, 950, {"wild hog": 8, "young lynx": 8, "black mauler cub": 6, "hobgoblin snake-finder": 6,
                                               "meandering spirit": 4, "small hill cat": 6})
b.wild("wood_eater_reach", 700, 1050, 1100, 1460, {"wood-eater": 12, "wood-eater alate": 4, "wood-eater hunter": 3})
b.camp("wood_eater_hive", 860, 1260, 12, {"wood-eater soldier": 4, "wood-eater worker": 5}, 300)
b.camp("hive_throne", 780, 1220, 9, {"wood-eater king": 1}, 900)
b.wild("huldu_woods", 150, 800, 650, 1350, {"huldu stalker": 10, "huldu hunter": 10, "huldu lurker": 6, "huldu outcast": 4})
b.camp("huldu_ring", 270, 930, 10, {"huldu stalker": 3, "huldu hunter": 2}, 300)
b.wild("middle_hills", 350, 350, 950, 950, {"hill person": 12, "small hill cat": 8, "vein spider": 8, "young grendelorm": 10, "hill cat": 6})
b.wild("hound_ridge", 600, 300, 880, 840, {"rabid wolfhound": 7, "phantom hound": 6})
b.camp("darkness_falls", 230, 640, 10, {"phantom hound": 5}, 300)
b.wild("vendo_hills", 450, 220, 1050, 700, {"vendo warrior": 6, "vendo shaman": 6, "vendo bone-collector": 6, "vendo stalker": 3, "hobyah": 5})
b.camp("vendo_mouth", 700, 175, 12, {"vendo flayer": 2, "vendo shaman": 2, "dragon-preacher": 1}, 420)
b.wild("lake_shore", 150, 150, 600, 620, {"young grendelorm": 6, "little water goblin": 6, "mud snake": 4})

themes = ["Mularn, Haggerfel and the Jordheim road (quiet)", "The huldu woods (west, the hidden folk)", "The wood-eater hive (south)",
          "Darkness Falls and the hound ridge (the wolves' first sign)", "The Vendo Caverns (north: a dragon-preacher at the mouth)",
          "The middle hills and the lake"]
notes = ("Midgard's plan 2026-11-24, round 1: Peaceful - the hub; both threads' first signs (the hounds at Darkness Falls, the "
         "dragon-preacher at the Vendo Caverns). Coordinates are zone units (metres x 40).")
tiers = {"Vasa": "blue", "Gors": "blue", "Rasczel": "yellow", "Vrede": "yellow"}
factions = {"goblins": {"id": 9601, "aggro": 40}, "dead": {"id": 9602, "aggro": 60}, "hillfolk": {"id": 9603, "aggro": 50},
            "hive": {"id": 9604, "aggro": 50}, "huldu": {"id": 9605, "aggro": 50}, "hounds": {"id": 9606, "aggro": 80},
            "vendo": {"id": 9607, "aggro": 70}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
