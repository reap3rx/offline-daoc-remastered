"""East Svealand's zone build (claude 2026-11-24, "Midgard - the plan", round 1): Peaceful - wolf country of lakes and rivers,
greens and blues round Audliten, Vasudheim and Dvalin. The west thread: the wolves grow bold - sveawolves and lupines run with
the wildlings, the wolf-hamed wild men, and together they have taken Ulfrstead, the steading by the tomte hills (the zone's fort
to retake). The south thread: drakelings nest at the mouth of Nisse's Lair, fed by a drakulv missionary. The tomte raid the farms
in the south, the dirges walk the old northern roads, the army ants march by Dvalin."""
import sys
sys.path.insert(0, '/home/claude/mid/r1')
from zbcommon import Build
b = Build(101, 'East Svealand', 'peaceful', 5.0)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
mem("rock crab", "rock crab", "green", roam=200)
mem("spindly rock crab", "spindly rock crab", "blue", aggro=[30, 300], roam=200)
mem("soft-shelled crab", "soft-shelled crab", "green", roam=150)
mem("army ant worker", "army ant worker", "green", faction="ants", roam=200)
mem("army ant soldier", "army ant soldier", "blue", faction="ants", aggro=[50, 350], roam=150)
mem("nordic dirge", "nordic dirge", "blue", faction="dead", aggro=[50, 400], roam=250)
mem("roaming dirge", "roaming dirge", "blue", faction="dead", aggro=[50, 400], roam=400)
mem("fragile skeleton", "fragile skeleton", "green", faction="dead", aggro=[30, 300], roam=150)
mem("wayward ghoul", "wayward ghoul", "blue", faction="dead", aggro=[40, 350], roam=200)
mem("dwarf bone skeleton", "dwarf bone skeleton", "yellow", faction="dead", aggro=[60, 400], roam=80)
mem("rugged dwarven pony", "rugged dwarven pony", "green", roam=400)
mem("sveawolf mother", "sveawolf mother", "blue", faction="wolves", aggro=[50, 400], roam=350)
mem("young sveawolf", "young sveawolf", "green", faction="wolves", roam=300)
mem("lupine snarler", "lupine snarler", "blue", faction="wolves", aggro=[60, 450], roam=350)
mem("lupine gnawer", "lupine gnawer", "blue", faction="wolves", aggro=[50, 400], roam=300)
mem("wildling", "wildling", "yellow", faction="wolves", guild="the Grey Hames", aggro=[60, 450], roam=200)
mem("wildling scout", "wildling scout", "blue", faction="wolves", guild="the Grey Hames", aggro=[60, 500], roam=350)
mem("Grey-Hame Warden", "wildling", "red", name="the Grey-Hame Warden", size=1.25, faction="wolves", guild="Chief of the Grey Hames",
    aggro=[80, 550], roam=40, guards={"wildling": 2})
mem("black mauler juvenile", "black mauler juvenile", "blue", aggro=[40, 350], roam=250)
mem("smiera-gatto", "smiera-gatto", "green", roam=300)
mem("green serpent", "green serpent", "green", roam=200)
mem("mud snake", "mud snake", "green", roam=200)
mem("young lynx", "young lynx", "blue", roam=300)
mem("tawny lynx cub", "tawny lynx cub", "green", roam=250)
mem("vein spiderling", "vein spiderling", "green", roam=200)
mem("roaming thrall", "roaming thrall", "blue", faction="thralls", aggro=[40, 350], roam=300)
mem("escaped thrall", "escaped thrall", "blue", faction="thralls", aggro=[40, 350], roam=300)
mem("tomte pillager", "tomte pillager", "blue", faction="tomte", aggro=[50, 400], roam=250)
mem("tomte thug", "tomte thug", "blue", faction="tomte", aggro=[50, 400], roam=250)
mem("tomte skirmisher", "tomte skirmisher", "green", faction="tomte", aggro=[40, 350], roam=300)
mem("tomte aggressor", "tomte aggressor", "yellow", faction="tomte", aggro=[60, 450], roam=200)
mem("envy drakeling", "envy drakeling", "blue", faction="brood", aggro=[50, 400], roam=150)
mem("silverscale drakeling", "silverscale drakeling", "yellow", faction="brood", aggro=[60, 450], roam=120)
mem("dragon-preacher", "drakulv missionary", "yellow", name="dragon-preacher", faction="brood", guild="Gjalpinulva's Missionaries",
    aggro=[60, 450], roam=60)

for i, x, y, r in [("audliten", 137, 572, 120), ("vasudheim", 1350, 477, 130), ("dvalin", 108, 1316, 110), ("averrson_farm", 310, 1220, 60)]:
    b.clear(i, x, y, r, ["rock crab", "smiera-gatto", "young sveawolf", "wildling", "wildling scout", "lupine snarler", "lupine gnawer",
                         "army ant worker", "green serpent", "mud snake"])
    b.S[-1]["block"] = "all"
b.wild("the_shallows", 300, 700, 1250, 1350, {"rock crab": 12, "spindly rock crab": 6, "soft-shelled crab": 4})
b.wild("ant_fields", 250, 1080, 750, 1450, {"army ant worker": 10})
b.camp("ant_mound", 480, 1290, 12, {"army ant soldier": 4, "army ant worker": 4}, 300)
b.wild("dirge_road", 250, 150, 1000, 600, {"nordic dirge": 10, "roaming dirge": 6, "fragile skeleton": 6, "wayward ghoul": 3,
                                           "rugged dwarven pony": 4})
b.camp("dwarf_barrow", 709, 213, 9, {"dwarf bone skeleton": 4}, 420)
b.wild("wolf_moor", 450, 600, 1100, 1000, {"sveawolf mother": 8, "young sveawolf": 6, "lupine snarler": 5, "black mauler juvenile": 6,
                                           "smiera-gatto": 6})
b.wild("east_hills", 950, 150, 1560, 950, {"young lynx": 6, "tawny lynx cub": 6, "green serpent": 8, "mud snake": 4, "vein spiderling": 4,
                                           "lupine gnawer": 4, "wildling scout": 3})
b.camp("ulfrstead", 830, 640, 16, {"Grey-Hame Warden": 1, "wildling": 4, "lupine snarler": 4}, 600)
b.camp("ulfrstead_yard", 870, 700, 12, {"wildling": 3, "lupine gnawer": 3}, 420)
b.wild("thrall_road", 300, 850, 900, 1080, {"roaming thrall": 6, "escaped thrall": 4})
b.wild("tomte_hills", 550, 980, 1200, 1400, {"tomte pillager": 10, "tomte thug": 8, "tomte skirmisher": 6, "tomte aggressor": 3})
b.camp("drakeling_nest", 990, 1160, 10, {"silverscale drakeling": 3, "envy drakeling": 4, "dragon-preacher": 1}, 600)
b.wild("lair_road", 700, 1300, 1150, 1500, {"envy drakeling": 4, "spindly rock crab": 4})

themes = ["Audliten, Vasudheim and Dvalin (quiet)", "The dirges' road and the dwarf barrow (north)",
          "The wolf moor and Ulfrstead, taken by the Grey Hames (the fort to retake)", "The shallows and the ant fields",
          "The tomte hills (south)", "Nisse's Lair and the drakeling nest (south: the dragon's first brood)"]
notes = ("Midgard's plan 2026-11-24, round 1: Peaceful; the west thread's wolves grow bold (Ulfrstead, the fort to retake), the "
         "south thread's drakelings at Nisse's Lair. Coordinates are zone units (metres x 40).")
tiers = {"Envy Drake Dorga": "yellow", "Queen Major": "yellow", "Flayer Fali": "yellow"}
factions = {"ants": {"id": 9611, "aggro": 50}, "dead": {"id": 9612, "aggro": 60}, "wolves": {"id": 9613, "aggro": 75},
            "thralls": {"id": 9614, "aggro": 50}, "tomte": {"id": 9615, "aggro": 60}, "brood": {"id": 9616, "aggro": 80}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
