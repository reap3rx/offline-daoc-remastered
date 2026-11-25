"""Cornwall's zone build (claude 2026-11-24, "Albion - the plan", round 3): Deadly, and Albion's HARD START at Cornwall Station -
blues and yellows only on the moor round the Station, oranges and reds everywhere else, purples in the west. The south thread's
homeland: Cornwall is giants' country (Corineus threw Gogmagog off its cliffs), and Golestandt's Cornish giants come up from
Dartmoor's edge in the south-west with the great drakes of the west; the beech woods and their muryans and buccas are the old
Cornish fae; and out of the Catacombs of Cardova march the Drowned Ninth - a lost legion the giants have bound to dig their
quarry. Cirfans, the great drake of the west, is the purple. About 650."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(6, 'Cornwall', 'deadly', 1.6)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
# the moor round Cornwall Station (the hard start's gentle edge)
mem("young brown bear", "young brown bear", "blue", roam=350)
mem("cliff spiderling", "cliff spiderling", "blue", aggro=[40, 300], roam=250)
mem("moor wolf", "moor wolf", "yellow", faction="moor", aggro=[60, 450], roam=450)
mem("brown bear", "brown bear", "yellow", roam=350)
mem("cliff spider", "cliff spider", "orange", aggro=[70, 450], roam=250)
# the ghostly church (north)
mem("ghostly cleric", "ghostly cleric", "orange", faction="church", aggro=[80, 500], roam=120)
mem("ghostly paladin", "ghostly paladin", "red", faction="church", aggro=[85, 550], roam=120)
# the beech woods and the Cornish fae (middle)
mem("elder beech", "elder beech", "orange", faction="fae", aggro=[60, 400], roam=60)
mem("aged beech", "aged beech", "red", faction="fae", aggro=[70, 450], roam=40)
mem("muryan", "muryan", "orange", faction="fae", aggro=[70, 450], roam=250)
mem("bucca", "bucca", "orange", faction="fae", aggro=[75, 450], roam=250)
mem("muryan trickster", "muryan trickster", "orange", faction="fae", aggro=[75, 450], roam=60)
mem("black bear", "black bear", "orange", roam=350)
mem("forest cat", "forest cat", "orange", aggro=[70, 450], roam=400)
mem("death stalker", "death stalker", "orange", aggro=[80, 550], roam=350)
mem("moor pack leader", "moor pack leader", "orange", faction="moor", aggro=[80, 550], roam=350)
mem("moor den mother", "moor den mother", "red", faction="moor", aggro=[85, 550], roam=200)
# the south: rooters, boogeys, the Drowned Ninth out of Cardova
mem("giant rooter", "giant rooter", "orange", aggro=[70, 500], roam=350)
mem("moor boogey", "moor boogey", "red", aggro=[85, 550], roam=250)
mem("greater boogey", "greater boogey", "red", aggro=[90, 600], roam=250)
mem("skeletal legionnaire", "skeletal legionnaire", "orange", faction="ninth", guild="the Drowned Ninth", aggro=[85, 550], roam=150)
mem("skeletal centurion", "skeletal centurion", "red", faction="ninth", guild="the Drowned Ninth", aggro=[90, 600], roam=100,
    guards={"skeletal legionnaire": 2})
mem("giant skeleton", "giant skeleton", "red", faction="ninth", aggro=[90, 600], roam=200)
mem("captured soul", "captured soul", "orange", faction="ninth", aggro=[70, 400], roam=100)
# the west: the giants and the great drakes
mem("Cornish quarry-giant", "Cornish giant", "red", name="Cornish quarry-giant", faction="giants", guild="the March of Golestandt",
    aggro=[90, 650], roam=200)
mem("granite giant stoneshaper", "granite giant stoneshaper", "red", faction="giants", guild="the March of Golestandt",
    aggro=[95, 650], roam=120)

b.wild("station_moor", 1230, 150, 1620, 780, {"young brown bear": 22, "moor wolf": 20, "brown bear": 16, "cliff spiderling": 10})
b.wild("cliff_tops", 800, 250, 1230, 560, {"cliff spiderling": 12, "cliff spider": 12, "moor wolf": 8, "brown bear": 8})
b.camp("ghostly_church", 1196, 372, 10, {"ghostly cleric": 4, "ghostly paladin": 3}, 420)
b.wild("beech_wood", 520, 560, 1540, 1000, {"elder beech": 26, "muryan": 22, "black bear": 18, "forest cat": 12, "death stalker": 10})
b.camp("muryan_mound", 985, 844, 10, {"muryan": 6}, 300)
b.camp("trickster_knoll", 1330, 924, 5, {"muryan trickster": 1}, 600)
b.camp("bucca_hollow", 1136, 929, 10, {"bucca": 6}, 360)
b.wild("bucca_dells", 950, 720, 1430, 1140, {"bucca": 12, "moor pack leader": 8, "black bear": 8})
b.camp("wolf_dens", 910, 896, 10, {"moor den mother": 2, "moor pack leader": 4}, 420)
b.camp("old_beeches", 1490, 975, 9, {"aged beech": 4}, 600)
b.wild("rooter_downs", 310, 1000, 1540, 1500, {"giant rooter": 34, "moor boogey": 8, "black bear": 6})
b.camp("boogey_edge", 700, 1430, 12, {"greater boogey": 4, "moor boogey": 2}, 420)
b.camp("cardova_road", 800, 1230, 12, {"skeletal legionnaire": 6, "skeletal centurion": 1}, 420)
b.camp("roman_fort", 1350, 1262, 12, {"skeletal legionnaire": 6, "skeletal centurion": 1}, 420)
b.patrol("the_ninth_marches", [(1350, 1262), (1150, 1250), (950, 1240), (800, 1230), (950, 1240), (1150, 1250)],
         {"skeletal legionnaire": 3, "skeletal centurion": 1})
b.wild("giant_graves", 430, 930, 700, 1330, {"giant skeleton": 10, "captured soul": 4})
b.camp("giants_quarry_road", 200, 1400, 14, {"Cornish quarry-giant": 3, "granite giant stoneshaper": 2}, 600)
b.camp("giants_edge", 110, 1000, 12, {"Cornish quarry-giant": 2}, 600)

themes = ["The moor round Cornwall Station (the hard start's gentle edge)", "The cliff tops and the ghostly church",
          "The beech woods and the Cornish fae (muryans, buccas)", "The rooter downs and the boogeys",
          "The Drowned Ninth, marching out of the Catacombs of Cardova", "The west: Golestandt's giants and the great drakes"]
notes = ("Albion's plan 2026-11-24, round 3: Deadly and the HARD START (Cornwall Station); the south thread's homeland, the Drowned "
         "Ninth out of Cardova. Coordinates are zone units (metres x 40).")
tiers = {"Cornwall Drake": "red", "Cornish frog": "yellow", "Cornwall hunter": "orange", "Kalnraw": "red", "Addard Yarley": "red",
         "Cornish hen": "orange", "Tusker": "red", "Cirfans": "purple", "Brother Jarrel": "orange", "Aricoer": "red",
         "Centurion Favius": "red", "Yog": "red", "Cornish giant": "red"}
factions = {"moor": {"id": 9471, "aggro": 75}, "church": {"id": 9472, "aggro": 85}, "fae": {"id": 9473, "aggro": 65},
            "ninth": {"id": 9474, "aggro": 95}, "giants": {"id": 9475, "aggro": 90}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
