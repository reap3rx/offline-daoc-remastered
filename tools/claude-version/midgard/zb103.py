"""Gotar's zone build (claude 2026-11-24, "Midgard - the plan", round 2): Wild - blues and yellows round Fort Atla and Nalliten,
a few greens near the towns. The south thread: the svartalf traders at their trading post in the west have been turned by the
drakulv missionaries and carry the dragon's word north; drakelings creep up from the southern edge and the seithkonur of the
south-west read red omens in their orbs. The drowned longship off the east shore, the hobgoblins of the south woods, the spirits
of wind and earth, the wolf nippers and wildlings round the north lakes."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from zbcommon import Build
b = Build(103, 'Gotar', 'wild', 4.2)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
mem("wolf nipper", "wolf nipper", "blue", faction="wolves", aggro=[40, 350], roam=300)
mem("wildling", "wildling", "yellow", faction="wolves", guild="the Grey Hames", aggro=[60, 450], roam=200)
mem("coastal wolf", "coastal wolf", "yellow", faction="wolves", aggro=[50, 400], roam=350)
mem("pine imp", "pine imp", "blue", faction="imps", aggro=[30, 300], roam=250)
mem("wood imp", "wood imp", "green", faction="imps", roam=250)
mem("dryad sprout", "dryad sprout", "green", roam=150)
mem("dryad sprig", "dryad sprig", "blue", roam=150)
mem("sapherd", "sapherd", "blue", roam=150)
mem("wild hog", "wild hog", "green", roam=300)
mem("tawny lynx", "tawny lynx", "blue", aggro=[40, 350], roam=300)
mem("smiera-gatto", "smiera-gatto", "green", roam=300)
mem("water snake", "water snake", "blue", roam=200)
mem("water strider", "water strider", "green", roam=200)
mem("green serpent", "green serpent", "green", roam=200)
mem("hobgoblin fish-catcher", "hobgoblin fish-catcher", "blue", faction="hobgoblins", roam=250)
mem("hobgoblin snagger", "hobgoblin snagger", "blue", faction="hobgoblins", aggro=[40, 350], roam=250)
mem("hobgoblin prowler", "hobgoblin prowler", "yellow", faction="hobgoblins", aggro=[50, 400], roam=300)
mem("hobgoblin pincher", "hobgoblin pincher", "blue", faction="hobgoblins", aggro=[40, 350], roam=250)
mem("host of the wind", "host of the wind", "yellow", faction="spirits", aggro=[50, 400], roam=300)
mem("host of the earth", "host of the earth", "yellow", faction="spirits", aggro=[50, 400], roam=200)
mem("wind wisp", "wind wisp", "blue", faction="spirits", roam=300)
mem("drowned soul", "drowned soul", "blue", faction="drowned", aggro=[50, 400], roam=200)
mem("skeletal oarsman", "skeletal oarsman", "yellow", faction="drowned", aggro=[60, 450], roam=150)
mem("skeletal seafarer", "skeletal seafarer", "yellow", faction="drowned", aggro=[60, 450], roam=150)
mem("rattling skeleton", "rattling skeleton", "blue", faction="drowned", aggro=[40, 350], roam=150)
mem("carrion crawler", "carrion crawler", "blue", aggro=[40, 350], roam=200)
mem("carrion eater", "carrion eater", "yellow", aggro=[50, 400], roam=200)
mem("svartalf outcast", "svartalf outcast", "yellow", faction="svartalf", guild="the Scale-Traders", aggro=[60, 450], roam=200)
mem("svartalf guard", "svartalf guard", "yellow", faction="svartalf", guild="the Scale-Traders", aggro=[60, 450], roam=100)
mem("dragon-preacher", "drakulv missionary", "yellow", name="dragon-preacher", faction="svartalf", guild="Gjalpinulva's Missionaries",
    aggro=[60, 450], roam=80, guards={"svartalf guard": 1})
mem("envy drakeling", "envy drakeling", "yellow", faction="brood", aggro=[60, 450], roam=200)
mem("seithkona", "seithkona", "yellow", faction="seith", aggro=[60, 450], roam=120)
mem("gotawitch", "gotawitch", "yellow", faction="seith", aggro=[60, 450], roam=120)
mem("seithr orb", "seithr orb", "blue", faction="seith", aggro=[50, 400], roam=80)
mem("perfidious pook", "perfidious pook", "yellow", aggro=[50, 400], roam=250)
mem("spindly rock crab", "spindly rock crab", "blue", roam=200)

for i, x, y, r in [("fort_atla", 709, 320, 120), ("nalliten", 1240, 864, 100), ("svartalf_post", 487, 698, 45)]:
    b.clear(i, x, y, r, ["wild hog", "wood imp", "pine imp", "dryad sprout", "wolf nipper", "hobgoblin snagger", "water strider",
                         "green serpent", "smiera-gatto", "rattling skeleton"])
    b.S[-1]["block"] = "all"
b.wild("north_lakes", 420, 80, 900, 870, {"wolf nipper": 12, "hobgoblin fish-catcher": 8, "water snake": 6, "wild hog": 6, "hobgoblin snagger": 6,
                                         "water strider": 6, "green serpent": 4})
b.camp("wildling_camp", 640, 560, 12, {"wildling": 5, "wolf nipper": 3}, 420)
b.wild("north_west_woods", 60, 80, 450, 700, {"dryad sprout": 8, "dryad sprig": 8, "sapherd": 8, "smiera-gatto": 6})
b.wild("middle_woods", 100, 380, 1340, 1100, {"pine imp": 10, "wood imp": 10, "tawny lynx": 8, "dryad sprig": 6, "coastal wolf": 4})
b.wild("drowned_shore", 920, 370, 1200, 520, {"drowned soul": 8, "skeletal oarsman": 4, "rattling skeleton": 4})
b.camp("drowned_ship", 1057, 474, 12, {"skeletal oarsman": 3, "skeletal seafarer": 3}, 420)
b.wild("east_coast", 1300, 500, 1600, 1250, {"spindly rock crab": 6, "perfidious pook": 6, "tawny lynx": 4})
b.wild("hobgoblin_woods", 660, 980, 1100, 1440, {"hobgoblin prowler": 8, "hobgoblin pincher": 8})
b.wild("spirit_hills", 160, 1020, 930, 1600, {"host of the wind": 10, "host of the earth": 8, "wind wisp": 8})
b.wild("carrion_vale", 900, 1200, 1500, 1580, {"carrion crawler": 8, "carrion eater": 6})
b.camp("seith_circle", 990, 1420, 10, {"seithkona": 2, "gotawitch": 3, "seithr orb": 3}, 420)
b.camp("seithkona_ring", 120, 1390, 9, {"seithkona": 3}, 420)
b.wild("southern_edge", 700, 1520, 1150, 1630, {"envy drakeling": 6})
b.camp("scale_traders", 520, 760, 12, {"svartalf outcast": 4, "svartalf guard": 2, "dragon-preacher": 1}, 600)
b.wild("trade_road", 300, 760, 900, 1220, {"svartalf outcast": 8})

themes = ["Fort Atla, Nalliten and the svartalf trading post (quiet)", "The north lakes and the wildling camp",
          "The scale-traders on the trade road (the south thread: svartalf turned by the drakulv)", "The drowned longship (east shore)",
          "The hobgoblin woods and the spirit hills (south)", "The seithkonur's circle and the drakelings on the southern edge"]
notes = ("Midgard's plan 2026-11-24, round 2: Wild; the south thread's svartalf scale-traders and drakulv preacher. Coordinates are "
         "zone units (metres x 40).")
tiers = {"Black Rixtas": "orange", "Thraxia": "orange", "Jordande": "orange", "Salix": "yellow", "Vidalf": "yellow", "Twitchclaw": "yellow"}
factions = {"wolves": {"id": 9631, "aggro": 60}, "imps": {"id": 9632, "aggro": 40}, "hobgoblins": {"id": 9633, "aggro": 50},
            "spirits": {"id": 9634, "aggro": 60}, "drowned": {"id": 9635, "aggro": 70}, "svartalf": {"id": 9636, "aggro": 75},
            "brood": {"id": 9637, "aggro": 80}, "seith": {"id": 9638, "aggro": 70}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
