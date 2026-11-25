"""Myrkwood Forest's zone build (claude 2026-11-24, "Midgard - the plan", round 2): Deadly - Midgard's HARD START at Galplen.
Oranges and reds everywhere, blues and yellows only on Galplen's doorstep, and named purples. The dark forest where the threads cross:
the werewolves of the west wood (the Fenris-wolf's kin) and the drakulv missionaries camped with the svartalf in the south both
hunt the same old seer, the volva who sits in the willow-wood west of Galplen and knows how each of them ends. The weeping willows
and tinglers, the arachite brood, the mora that ride men's dreams in the south, the decaying trolls, the worgs."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from zbcommon import Build
b = Build(105, 'Myrkwood Forest', 'deadly', 3.6)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
mem("myrkcat", "myrkcat", "yellow", aggro=[50, 400], roam=300)
mem("giant bull frog", "giant bull frog", "blue", roam=200)
mem("carrion eater", "carrion eater", "yellow", aggro=[50, 400], roam=200)
mem("hog-nose slither", "hog-nose slither", "orange", aggro=[60, 450], roam=200)
mem("venomspitter", "venomspitter", "orange", aggro=[60, 450], roam=200)
mem("weeping willow", "weeping willow", "orange", faction="willows", aggro=[70, 400], roam=20)
mem("shrieking willow", "shrieking willow", "red", faction="willows", aggro=[80, 450], roam=20)
mem("tingler", "tingler", "orange", faction="tinglers", aggro=[70, 450], roam=200)
mem("great tingler", "great tingler", "red", faction="tinglers", aggro=[80, 500], roam=150)
mem("arachite greensilk", "arachite greensilk", "orange", faction="arachite", aggro=[70, 450], roam=200)
mem("arachite shadowslinker", "arachite shadowslinker", "orange", faction="arachite", aggro=[70, 450], roam=200)
mem("arachite weblasher", "arachite weblasher", "orange", faction="arachite", aggro=[70, 450], roam=150)
mem("arachite priest", "arachite priest", "red", faction="arachite", aggro=[80, 500], roam=80)
mem("death spider", "death spider", "red", faction="arachite", aggro=[80, 500], roam=150)
mem("haunt", "haunt", "orange", faction="dead", aggro=[70, 450], roam=200)
mem("myrk shadow", "myrk shadow", "orange", faction="dead", aggro=[70, 450], roam=200)
mem("undead woodcarver", "undead woodcarver", "orange", faction="dead", aggro=[70, 450], roam=150)
mem("undead explorer", "undead explorer", "yellow", faction="dead", aggro=[60, 450], roam=200)
mem("brittle skeleton", "brittle skeleton", "yellow", faction="dead", aggro=[60, 400], roam=150)
mem("decaying norseman", "decaying norseman", "orange", faction="dead", aggro=[70, 450], roam=150)
mem("decaying troll", "decaying troll", "red", faction="trolls", aggro=[80, 500], roam=150)
mem("corpse eater", "corpse eater", "orange", aggro=[70, 450], roam=200)
mem("mora dancer", "mora dancer", "orange", faction="mora", aggro=[70, 450], roam=200)
mem("mora rider", "mora rider", "red", faction="mora", aggro=[80, 500], roam=300)
mem("dark hound", "dark hound", "orange", faction="mora", aggro=[70, 500], roam=350)
mem("soul sinker", "soul sinker", "orange", faction="mora", aggro=[70, 450], roam=200)
mem("gray worg", "gray worg", "orange", faction="wolves", aggro=[70, 500], roam=350)
mem("ridgeback worg", "ridgeback worg", "red", faction="wolves", aggro=[80, 500], roam=350)
mem("werewolf", "werewolf", "red", faction="wolves", guild="Fenrir's Kin", aggro=[80, 550], roam=250)
mem("minor werewolf noble", "minor werewolf noble", "red", faction="wolves", guild="Fenrir's Kin", aggro=[80, 550], roam=150)
mem("svartalf watcher", "svartalf watcher", "orange", faction="drakulv", guild="the Scale-Traders", aggro=[70, 500], roam=150)
mem("svartalf predator", "svartalf predator", "red", faction="drakulv", guild="the Scale-Traders", aggro=[80, 550], roam=200)
mem("svartalf sorcerer", "svartalf sorcerer", "red", faction="drakulv", guild="the Scale-Traders", aggro=[80, 550], roam=100)
mem("dragon-preacher", "drakulv missionary", "red", name="dragon-preacher", faction="drakulv", guild="Gjalpinulva's Missionaries",
    aggro=[80, 550], roam=80)
mem("Wyrm-Deacon Bersi", "drakulv missionary", "purple", name="Wyrm-Deacon Bersi", size=1.25, faction="drakulv",
    guild="First of the Missionaries", aggro=[90, 600], roam=40, guards={"svartalf sorcerer": 1, "dragon-preacher": 1})
mem("Ulfhedinn Grimolf", "werewolf", "purple", name="Ulfhedinn Grimolf", size=1.35, faction="wolves", guild="Lord of the West Wood",
    aggro=[90, 600], roam=60, guards={"werewolf": 2})

for i, x, y, r in [("galplen", 1091, 627, 120), ("gna_faste", 855, 912, 70), ("volva_hut", 620, 520, 40)]:
    b.clear(i, x, y, r, ["myrkcat", "giant bull frog", "hog-nose slither", "weeping willow", "tingler", "haunt", "carrion eater"])
    b.S[-1]["block"] = "all"
b.wild("galplen_outskirts", 930, 420, 1330, 760, {"myrkcat": 8, "giant bull frog": 8, "carrion eater": 6})
b.wild("eastern_marsh", 1360, 480, 1600, 900, {"hog-nose slither": 6, "venomspitter": 4})
b.wild("willow_wood", 390, 360, 880, 900, {"weeping willow": 18, "haunt": 8})
b.wild("north_ridge", 330, 40, 1450, 300, {"haunt": 8, "arachite greensilk": 8, "undead woodcarver": 6})
b.wild("dead_hills", 1000, 230, 1600, 420, {"undead woodcarver": 8, "brittle skeleton": 6, "undead explorer": 6, "corpse eater": 4})
b.wild("tingler_hollows", 70, 420, 660, 880, {"tingler": 10, "great tingler": 4})
b.camp("arachite_nest", 260, 560, 14, {"arachite priest": 2, "arachite weblasher": 3, "arachite shadowslinker": 3}, 600)
b.wild("arachite_west", 70, 440, 450, 720, {"arachite shadowslinker": 6, "arachite weblasher": 4, "death spider": 3})
b.wild("worg_run", 590, 850, 900, 1160, {"gray worg": 8, "ridgeback worg": 4})
b.wild("werewolf_wood", 200, 950, 570, 1200, {"werewolf": 6, "minor werewolf noble": 3, "gray worg": 4})
b.camp("werewolf_lord", 380, 1090, 12, {"Ulfhedinn Grimolf": 1}, 1200)
b.wild("troll_barrows", 740, 880, 1520, 1390, {"decaying troll": 6, "decaying norseman": 5, "myrk shadow": 8, "venomspitter": 4})
b.wild("mora_south", 660, 1190, 1280, 1560, {"mora dancer": 10, "mora rider": 5, "dark hound": 6, "soul sinker": 5})
b.wild("shrieking_grove", 360, 1340, 600, 1530, {"shrieking willow": 6})
b.wild("svartalf_south", 930, 1260, 1560, 1420, {"svartalf watcher": 6, "svartalf predator": 2})
b.camp("missionary_camp", 1100, 1320, 12, {"Wyrm-Deacon Bersi": 1, "svartalf watcher": 3}, 1200)

themes = ["Galplen (the HARD START) and Gna Faste", "The willow-wood and the volva's hut (west of Galplen)",
          "The tinglers and the arachite nest (west)", "The werewolves of the west wood and Ulfhedinn Grimolf",
          "The troll barrows and the worg run (middle)", "The mora of the south", "The missionaries' camp with the svartalf (south-east)"]
notes = ("Midgard's plan 2026-11-24, round 2: Deadly - the HARD START at Galplen; the threads cross (werewolves and drakulv both "
         "hunt the volva). Coordinates are zone units (metres x 40).")
tiers = {"Tingler Webmother": "purple", "Baron Falwur": "red", "Anakol": "red", "Noble Werewolf Alina": "red", "Priest Thaxtix": "red",
         "Priestess Araxia": "red", "Great Worg": "red", "Haglion's minion": "orange", "minion of Haglion": "orange", "Sorrow": "red"}
factions = {"willows": {"id": 9651, "aggro": 70}, "tinglers": {"id": 9652, "aggro": 80}, "arachite": {"id": 9653, "aggro": 85},
            "dead": {"id": 9654, "aggro": 85}, "trolls": {"id": 9655, "aggro": 85}, "mora": {"id": 9656, "aggro": 85},
            "wolves": {"id": 9657, "aggro": 90}, "drakulv": {"id": 9658, "aggro": 90}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
