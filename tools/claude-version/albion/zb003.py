"""Black Mountains North's zone build (claude 2026-11-24, "Albion - the plan", round 3): Dangerous - yellows and oranges, blues
round Swanton Keep and Snowdonia Station. The north thread's stronghold: the Crimson have taken Dinas Emrys, the hill fort in the
west where Vortigern's tower fell and the red and white dragons fought in the pit beneath it, and the hill-tribes march under
their red cords (the zone's siege). Smugglers carry their goods through the middle forest; the cockatrice brood holds the old mine
hills; howling maidens keen on the crags above Swanton. About 750."""
import sys
sys.path.insert(0, '/home/claude/alb/r1')
from zbcommon import Build
b = Build(3, 'Black Mountains North', 'dangerous', 1.6)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
mem("small bear", "small bear", "blue", roam=350)
mem("bear", "bear", "yellow", roam=350)
mem("forest lion", "forest lion", "yellow", aggro=[50, 400], roam=400)
mem("giant spider", "giant spider", "yellow", aggro=[50, 350], roam=250)
mem("gray warg", "gray warg", "yellow", aggro=[70, 500], roam=450)
mem("emerald snake", "emerald snake", "blue", roam=250)
mem("dryad", "dryad", "yellow", faction="wood", aggro=[50, 350], roam=200)
mem("dryad invert", "dryad invert", "orange", faction="wood", aggro=[60, 400], roam=200)
mem("pixie", "pixie", "blue", faction="wood", aggro=[40, 350], roam=250)
mem("pixie scout", "pixie scout", "yellow", faction="wood", aggro=[50, 400], roam=250)
mem("poacher", "poacher", "blue", faction="smugglers", aggro=[50, 400], roam=250)
mem("forest smuggler", "forest smuggler", "orange", faction="smugglers", guild="the Red Road", aggro=[80, 500], roam=200)
mem("forest tracker", "forest tracker", "orange", faction="smugglers", guild="the Red Road", aggro=[80, 550], roam=350)
mem("forest chief", "forest chief", "red", faction="smugglers", guild="the Red Road", aggro=[90, 550], size=1.15, roam=80,
    guards={"forest smuggler": 2})
mem("enraged cockatrice", "enraged cockatrice", "orange", faction="cockatrices", aggro=[80, 500], roam=250)
mem("ghost miner", "ghost miner", "yellow", faction="dead", aggro=[70, 450], roam=150)
mem("large boulderling", "large boulderling", "yellow", aggro=[60, 400], roam=150)
mem("rock elemental", "rock elemental", "orange", aggro=[80, 450], roam=100)
mem("dragon ant worker", "dragon ant worker", "blue", faction="ants", aggro=[40, 300], roam=250)
mem("dragon ant soldier", "dragon ant soldier", "yellow", faction="ants", aggro=[60, 400], roam=250)
mem("goblin warrior", "goblin warrior", "yellow", faction="goblins", aggro=[70, 450], roam=200)
mem("goblin scout", "goblin scout", "yellow", faction="goblins", aggro=[70, 500], roam=300)
mem("undead druid", "undead druid", "yellow", faction="dead", aggro=[80, 450], roam=150)
mem("undead filidh", "undead filidh", "yellow", faction="dead", aggro=[80, 450], roam=150)
mem("filidh", "filidh", "yellow", faction="crimson", aggro=[70, 450], roam=200)
mem("devout filidh", "devout filidh", "yellow", faction="crimson", aggro=[75, 450], roam=150)
mem("filidh sacrificer", "filidh sacrificer", "orange", faction="crimson", guild="the Crimson", aggro=[85, 500], roam=150)
mem("howling maiden", "howling maiden", "red", aggro=[90, 600], roam=150)
# the hill-tribes and the Crimson at Dinas Emrys (west)
mem("hill warrior", "hill warrior", "orange", faction="hillfolk", guild="the Red-Corded Tribes", aggro=[85, 550], roam=200)
mem("hill guard", "hill guard", "orange", faction="hillfolk", guild="the Red-Corded Tribes", aggro=[85, 550], roam=120)
mem("hill avenger", "hill avenger", "orange", faction="hillfolk", guild="the Red-Corded Tribes", aggro=[85, 550], roam=250)
mem("hill shaman", "hill shaman", "red", faction="hillfolk", guild="the Red-Corded Tribes", aggro=[90, 550], roam=100)
mem("crimson acolyte", "Crimson Initiate", "orange", name="crimson acolyte", size=0.9, faction="crimson", guild="the Crimson",
    aggro=[90, 550], roam=120)
mem("crimson dragon-priest", "Crimson Initiate", "red", name="crimson dragon-priest", faction="crimson", guild="the Crimson",
    aggro=[95, 600], roam=80)
mem("necromancer", "necromancer", "red", faction="crimson", guild="the Crimson", aggro=[95, 600], roam=60)
mem("Pit-Warden of Dinas Emrys", "Crimson Initiate", "purple", name="the Pit-Warden of Dinas Emrys", faction="crimson",
    guild="Keeper of the Dragons' Pit", aggro=[95, 650], size=1.3, roam=30, guards={"crimson dragon-priest": 2})

b.wild("swanton_slopes", 520, 150, 950, 480, {"small bear": 14, "emerald snake": 8, "dragon ant worker": 8, "poacher": 6})
b.camp("ant_knoll", 790, 670, 8, {"dragon ant worker": 4, "dragon ant soldier": 4}, 300)
b.camp("maiden_crags", 827, 294, 9, {"howling maiden": 5}, 600)
b.wild("cockatrice_hills", 180, 320, 940, 840, {"enraged cockatrice": 18, "gray warg": 10, "forest lion": 8, "goblin scout": 6})
b.camp("old_mine", 659, 608, 9, {"ghost miner": 6}, 300)
b.camp("beak_rocks", 860, 420, 9, {"enraged cockatrice": 4}, 420)
b.camp("goblin_hollow", 470, 720, 10, {"goblin warrior": 6, "goblin scout": 3}, 300)
b.wild("red_road", 610, 370, 1350, 1100, {"forest smuggler": 16, "forest tracker": 16, "bear": 10, "large boulderling": 6})
b.camp("smugglers_den", 904, 570, 12, {"forest chief": 1, "forest smuggler": 4, "forest tracker": 2}, 600)
b.camp("rock_hollow", 1119, 760, 8, {"rock elemental": 5}, 420)
b.wild("snowdonia_woods", 900, 900, 1300, 1250, {"small bear": 10, "bear": 8, "giant spider": 8, "pixie": 6})
b.wild("south_woods", 330, 780, 1300, 1630, {"giant spider": 24, "forest lion": 18, "bear": 14, "dryad": 10, "pixie scout": 8,
                                             "undead druid": 10, "small bear": 10})
b.camp("dryad_ring", 816, 1200, 9, {"dryad": 4, "dryad invert": 3}, 300)
b.camp("druid_graves", 495, 1017, 10, {"undead druid": 5, "undead filidh": 3}, 300)
b.wild("filidh_south", 260, 1200, 1400, 1630, {"filidh": 12, "devout filidh": 10, "filidh sacrificer": 10})
b.camp("sacrificers_ring", 968, 1393, 11, {"filidh sacrificer": 5, "devout filidh": 3}, 360)
b.wild("warg_west", 80, 660, 560, 1110, {"gray warg": 14, "hill avenger": 8})
# --- Dinas Emrys, the Crimson's hill fort (the siege)
b.wild("hill_country", 60, 300, 320, 1160, {"hill warrior": 18, "hill guard": 10, "hill avenger": 10, "hill shaman": 4})
b.camp("dinas_emrys", 160, 360, 16, {"crimson acolyte": 6, "hill guard": 4, "hill warrior": 4, "crimson dragon-priest": 2}, 420)
b.camp("dinas_gate", 230, 420, 10, {"hill guard": 4, "hill warrior": 2}, 360)
b.camp("dragons_pit", 130, 330, 8, {"Pit-Warden of Dinas Emrys": 1}, 1800)
b.camp("necromancers_cairn", 290, 1234, 9, {"necromancer": 2, "undead druid": 3}, 600)

themes = ["Swanton Keep's slopes", "The cockatrice hills and the old mine", "The Red Road (smugglers and trackers)",
          "The south woods and the filidh", "Dinas Emrys - the Crimson's hill fort, and the hill-tribes under red cords (the siege)"]
notes = ("Albion's plan 2026-11-24, round 3: Dangerous; the north thread's stronghold at Dinas Emrys, where Vortigern's tower fell and "
         "the dragons fought. Coordinates are zone units (metres x 40).")
tiers = {"Trimbeak": "orange", "Mystic Ulfwag": "orange", "Erick Redbeard": "yellow", "Heretic Elam": "orange", "Hill Chief Alrek": "red",
         "Cauld Lad": "red", "Crimson Initiate": "red", "Glimbeak": "orange", "Slimbeak": "orange", "Grimbeak": "orange",
         "Amano": "yellow", "Arawnite Messenger": "orange", "King Smugluk": "orange", "Mootang": "yellow"}
factions = {"wood": {"id": 9461, "aggro": 50}, "smugglers": {"id": 9462, "aggro": 80}, "cockatrices": {"id": 9463, "aggro": 80},
            "dead": {"id": 9464, "aggro": 80}, "ants": {"id": 9465, "aggro": 45}, "goblins": {"id": 9466, "aggro": 75},
            "crimson": {"id": 9467, "aggro": 95}, "hillfolk": {"id": 9468, "aggro": 85}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
