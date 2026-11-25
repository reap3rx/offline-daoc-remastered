"""Salisbury Plains' zone build (claude 2026-11-24, "Albion - the plan"; owner: "make it more dangerous/deadly near Stonehenge
Barrows ... use assets/plot ideas that tie in the dungeons"): Wild - blues and yellows on the downs round West Downs, a few greens
by the town - and Deadly round the Giants' Dance (Stonehenge) and the south-east barrows: Golestandt's giants have marched north
from Cornwall to take back the stones their kind first raised, the tomb-raiders they pay in Cornish tin dig out the graves of
the Long Knives that bind the Dance, and the giants' own dead stir under the great barrow. Gogmagog's bones are the purple.
About 950."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(1, 'Salisbury Plains', 'wild', 1.12)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
# the downs (north: round West Downs, mostly blue)
mem("grass snake", "grass snake", "green", roam=300)
mem("young boar", "young boar", "green", roam=350)
mem("spirit", "spirit", "green", roam=250)
mem("brownie grassrunner", "brownie grassrunner", "green", roam=300)
mem("wild mare", "wild mare", "blue", roam=500)
mem("wild stallion", "wild stallion", "blue", roam=500)
mem("wild boar", "wild boar", "blue", roam=400)
mem("bear", "bear", "blue", roam=350)
mem("carrion drake", "carrion drake", "blue", aggro=[50, 400], roam=350)
mem("brownie nomad", "brownie nomad", "blue", faction="brownies", aggro=[30, 300], roam=350)
mem("fading spirit", "fading spirit", "blue", roam=250)
mem("river racer", "river racer", "blue", roam=250)
# the middle plain (blue / yellow)
mem("red adder", "red adder", "blue", roam=300)
mem("grove nymph", "grove nymph", "blue", faction="nymphs", aggro=[40, 350], roam=250)
mem("brownie rover", "brownie rover", "yellow", faction="brownies", aggro=[40, 350], roam=350)
mem("young bear", "young bear", "blue", roam=350)
mem("pseudo basilisk", "pseudo basilisk", "yellow", aggro=[50, 400], roam=300)
mem("basilisk", "basilisk", "yellow", aggro=[60, 450], roam=300)
mem("wandering spirit", "wandering spirit", "yellow", faction="long_knives", aggro=[60, 450], roam=250)
mem("disturbed presence", "disturbed presence", "yellow", faction="long_knives", aggro=[70, 450], roam=200, model=485)
mem("black dog", "black dog", "yellow", aggro=[70, 500], roam=400)
mem("wind mephit", "wind mephit", "yellow", aggro=[60, 450], roam=350)
mem("young brown bear", "young brown bear", "yellow", roam=350)
# the druids and filidh (west) - the Crimson's thread, faintly
mem("filidh", "filidh", "blue", faction="filidh", aggro=[50, 400], roam=200)
mem("devout filidh", "devout filidh", "blue", faction="filidh", aggro=[60, 400], roam=150)
mem("filidh sacrificer", "filidh sacrificer", "yellow", faction="filidh", aggro=[80, 450], roam=120)
mem("undead druid", "undead druid", "yellow", faction="long_knives", aggro=[80, 450], roam=150)
mem("druid seer", "druid seer", "blue", faction="filidh", aggro=[50, 400], roam=200)
# bandits (north) and slavers (north-east)
mem("bandit", "bandit", "blue", faction="bandits", guild="the Downs Riders", aggro=[70, 450], roam=200)
mem("bandit henchman", "bandit henchman", "yellow", faction="bandits", guild="the Downs Riders", aggro=[75, 450], roam=200)
mem("bandit thaumaturge", "bandit thaumaturge", "yellow", faction="bandits", guild="the Downs Riders", aggro=[75, 450], roam=150)
mem("bandit lieutenant", "bandit lieutenant", "yellow", faction="bandits", guild="the Downs Riders", aggro=[80, 500], roam=150)
mem("bandit leader", "bandit leader", "orange", faction="bandits", guild="the Downs Riders", aggro=[85, 500], size=1.15, roam=60,
    guards={"bandit lieutenant": 1, "bandit thaumaturge": 1})
mem("slaver", "slaver", "yellow", faction="slavers", guild="Cottrel's Company", aggro=[80, 500], roam=150)
# the tomb-raiders (west diggers, east raiders, south-east mercenaries at the great barrow)
mem("tomb raider digger", "tomb raider digger", "blue", faction="raiders", aggro=[70, 450], roam=200)
mem("tomb raider scout", "tomb raider scout", "yellow", faction="raiders", aggro=[75, 500], roam=300)
mem("tomb raider", "tomb raider", "yellow", faction="raiders", aggro=[80, 500], roam=200)
mem("mercenary tomb raider", "mercenary tomb raider", "orange", faction="raiders", aggro=[85, 550], roam=150)
mem("green ghast", "green ghast", "yellow", faction="long_knives", aggro=[80, 450], roam=200)
# the giants' march (south) - orange and red near the Dance
mem("huge boar", "huge boar", "yellow", faction="giants", aggro=[60, 450], roam=400)
mem("aged basilisk", "aged basilisk", "orange", aggro=[70, 500], roam=300)
mem("Salisbury giant", "Salisbury giant", "orange", faction="giants", guild="the March of Golestandt", aggro=[80, 600], roam=300)
mem("Cornish stone-bearer", "Cornish giant", "red", name="Cornish stone-bearer", faction="giants", guild="the March of Golestandt",
    aggro=[90, 650], roam=200)
mem("granite giant", "granite giant", "red", faction="giants", guild="the March of Golestandt", aggro=[90, 650], roam=150)
mem("granite giant oracle", "granite giant oracle", "red", faction="giants", guild="the March of Golestandt", aggro=[95, 650], size=1.15,
    roam=60, guards={"granite giant": 2})
# the giants' dead under the great barrow (south-east, Deadly)
mem("giant skeleton", "giant skeleton", "red", faction="giants_dead", aggro=[90, 600], roam=200)
mem("skeletal legionnaire", "small skeletal legionnaire", "orange", faction="giants_dead", aggro=[85, 550], roam=150)
mem("bones of Gogmagog", "giant skeleton", "purple", name="the bones of Gogmagog", faction="giants_dead", guild="the Last Giant of Albion",
    aggro=[95, 700], size=1.7, roam=40, guards={"giant skeleton": 3})
# the spriggarns (far south-west corner)
mem("spriggarn waylayer", "spriggarn waylayer", "orange", faction="spriggarns", aggro=[80, 500], roam=200)
mem("spriggarn ambusher", "spriggarn ambusher", "orange", faction="spriggarns", aggro=[80, 500], roam=200)
mem("spriggarn howler", "spriggarn howler", "red", faction="spriggarns", aggro=[85, 550], roam=100)
mem("escaped bandit", "escaped bandit", "orange", faction="escaped", aggro=[80, 550], roam=250)
mem("escaped bandit leader", "escaped bandit leader", "red", faction="escaped", aggro=[90, 600], roam=60, guards={"escaped bandit": 2})

# --- the downs round West Downs (gentle-ish, Wild)
b.wild("town_downs", 520, 80, 950, 380, {"grass snake": 14, "young boar": 12, "spirit": 10, "brownie grassrunner": 12, "wild mare": 8})
b.wild("horse_downs", 200, 120, 1050, 600, {"wild mare": 22, "wild stallion": 26, "wild boar": 22, "brownie nomad": 14, "fading spirit": 10,
                                           "bear": 8, "grass snake": 8})
b.wild("carrion_heath", 80, 60, 360, 330, {"carrion drake": 16, "bear": 8, "young boar": 6})
b.wild("river_north", 1000, 10, 1270, 360, {"river racer": 16, "wild boar": 8, "grass snake": 6})
b.camp("downs_riders", 905, 110, 14, {"bandit": 7, "bandit henchman": 4, "bandit thaumaturge": 2, "bandit leader": 1}, 360)
b.patrol("downs_riders_walk", [(905, 110), (820, 200), (700, 280), (820, 200)], {"bandit": 2, "bandit henchman": 1})
b.camp("cottrels_pens", 1432, 389, 10, {"slaver": 6}, 360)
# --- the west: filidh and druids, the diggers' fields
b.wild("filidh_west", 100, 240, 700, 420, {"filidh": 14, "devout filidh": 8, "druid seer": 6})
b.camp("sacrificers_stones", 259, 365, 10, {"filidh sacrificer": 5, "undead druid": 2}, 360)
b.wild("diggers_fields", 245, 720, 620, 1190, {"tomb raider digger": 24, "green ghast": 12, "wandering spirit": 6})
b.camp("diggers_camp", 363, 1103, 12, {"tomb raider digger": 6, "tomb raider scout": 2}, 300)
# --- the middle plain (Wild: blue and yellow)
b.wild("middle_plain", 380, 380, 1380, 1000, {"grove nymph": 36, "red adder": 26, "pseudo basilisk": 26, "wild boar": 20, "brownie rover": 22,
                                             "young bear": 12, "wandering spirit": 10, "disturbed presence": 14})
b.camp("nymph_grove", 907, 621, 10, {"grove nymph": 6}, 300)
b.camp("basilisk_nest", 1259, 268, 10, {"basilisk": 4, "pseudo basilisk": 3}, 300)
b.wild("east_ridge", 1100, 300, 1400, 950, {"tomb raider scout": 12, "tomb raider": 14, "black dog": 6, "basilisk": 10})
b.camp("raiders_east", 1272, 796, 12, {"tomb raider": 5, "tomb raider scout": 3}, 300)
b.wild("mephit_downs", 40, 600, 600, 1430, {"wind mephit": 26, "young brown bear": 10, "red adder": 8})
b.wild("long_knives_field", 450, 700, 900, 1000, {"disturbed presence": 14, "wandering spirit": 10})
# --- the giants' march (south: orange, red by the Dance)
b.wild("giants_march", 420, 1050, 1350, 1440, {"Salisbury giant": 22, "huge boar": 22, "aged basilisk": 14, "young brown bear": 8,
                                              "wind mephit": 8})
for k, (x, y) in enumerate([(545, 1360), (766, 1388), (943, 1420), (1035, 1322)]):
    b.camp("giant_camp_%d" % k, x, y, 10, {"Salisbury giant": 3, "huge boar": 2}, 420)
# --- the Giants' Dance (Stonehenge) - Deadly
b.wild("dance_approach", 760, 780, 1120, 1080, {"Salisbury giant": 10, "basilisk": 8, "disturbed presence": 8})
b.camp("the_dance", 921, 930, 16, {"granite giant": 4, "Cornish stone-bearer": 3, "Salisbury giant": 4}, 480)
b.camp("dance_oracle", 960, 985, 6, {"granite giant oracle": 1}, 900)
b.patrol("dance_ring", [(880, 880), (970, 880), (990, 960), (920, 1000), (860, 960)], {"Salisbury giant": 2, "Cornish stone-bearer": 1})
# --- the great barrow (south-east) - Deadly
b.wild("barrow_downs", 1150, 1070, 1450, 1445, {"giant skeleton": 16, "mercenary tomb raider": 14, "skeletal legionnaire": 10})
b.camp("great_barrow", 1290, 1372, 10, {"bones of Gogmagog": 1}, 1800)
b.camp("barrow_dig", 1283, 1259, 12, {"mercenary tomb raider": 6, "tomb raider": 3}, 360)
# --- the far south-west and south
b.camp("spriggarn_hollow", 83, 1490, 10, {"spriggarn waylayer": 4, "spriggarn ambusher": 4, "spriggarn howler": 2}, 360)
b.camp("escaped_bandits", 630, 1470, 10, {"escaped bandit leader": 1, "escaped bandit": 3}, 600)

themes = ["The downs round West Downs (horses, boars, brownies)", "The filidh and druids of the west", "The Downs Riders and Cottrel's slavers",
          "The tomb-raiders and the graves of the Long Knives", "The middle plain (nymphs, basilisks, adders)",
          "The giants' march from Cornwall", "The Giants' Dance (Stonehenge) - Deadly", "The great barrow and Gogmagog's bones - Deadly"]
notes = ("Albion's plan 2026-11-24, round 2: Wild, Deadly round the Giants' Dance and the great barrow (owner: 'more dangerous/deadly "
         "near Stonehenge Barrows'); the south thread - Golestandt's giants take back the stones. Coordinates are zone units (metres x 40).")
tiers = {"Abagu": "yellow", "Growler": "blue", "Slythcur": "yellow", "Water Spider Gleek": "red", "White Horse": "orange",
         "Kedalinde Teanidd": "blue", "Berik Liglim": "red", "Celain Elrich": "red", "Cynewulf the Ghostwalker": "orange",
         "Halena Edulan": "yellow", "Kearcs": "yellow", "Lonry Aetheoc": "yellow", "Slave Master Cottrel": "orange", "Tuka": "orange",
         "Veviel": "yellow", "Zelsania Nodith": "yellow", "Archdruid Glasan": "red"}
factions = {"brownies": {"id": 9431, "aggro": 35}, "nymphs": {"id": 9432, "aggro": 40}, "long_knives": {"id": 9433, "aggro": 80},
            "filidh": {"id": 9434, "aggro": 55}, "bandits": {"id": 9435, "aggro": 80}, "slavers": {"id": 9436, "aggro": 85},
            "raiders": {"id": 9437, "aggro": 80}, "giants": {"id": 9438, "aggro": 90}, "giants_dead": {"id": 9439, "aggro": 95},
            "spriggarns": {"id": 9440, "aggro": 85}, "escaped": {"id": 9430, "aggro": 85}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
