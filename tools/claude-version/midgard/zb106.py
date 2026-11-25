"""Skona Ravine's zone build (claude 2026-11-25, "Midgard - the plan", round 3): Dangerous - yellows and oranges, reds in the
werewolves' hold. The west thread's stronghold: Ulfhamr, the werewolf hold in the middle of the ravine, where the wolfaur headsmen
and the werewolf warders gather Fenrir's kin for Hati's host - the zone's siege, for the Wolfsbane Rangers. The Seithkona Circle in
the north-east watches the moon; the sidhe on the western shore and the dryads of the south-east are old and keep to themselves;
and from the south, out of Malmohus, the first silverscale drakes are creeping in."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from zbcommon import Build
b = Build(106, 'Skona Ravine', 'dangerous', 4.3)
m = b.members
def mem(k, frm, tier, **kw): m[k] = dict({"from": frm, "tier": tier}, **kw)
W = "Fenrir's Kin"
mem("wood rat", "wood rat", "blue", roam=200)
mem("brush cat", "brush cat", "yellow", aggro=[50, 400], roam=350)
mem("tree spirit", "tree spirit", "yellow", faction="wood", aggro=[50, 400], roam=150)
mem("woodland badger", "woodland badger", "blue", roam=200)
mem("timberland badger", "timberland badger", "yellow", aggro=[60, 400], roam=200)
mem("timber cat", "timber cat", "orange", aggro=[70, 450], roam=350)
mem("battle-scarred mauler", "battle-scarred mauler", "orange", aggro=[70, 450], roam=300)
mem("young wolverine", "young wolverine", "yellow", aggro=[60, 450], roam=300)
mem("callow wolverine", "callow wolverine", "orange", aggro=[70, 450], roam=300)
mem("wolverine", "wolverine", "red", aggro=[80, 500], roam=250)
mem("giant tree frog", "giant tree frog", "blue", roam=200)
mem("great tingler", "great tingler", "orange", aggro=[70, 450], roam=200)
mem("wind spirit", "wind spirit", "yellow", faction="wood", aggro=[60, 400], roam=250)
mem("moss maiden", "moss maiden", "orange", faction="wood", aggro=[70, 450], roam=150)
mem("green orm", "green orm", "orange", aggro=[70, 450], roam=200)
mem("sidhe gaoite", "sidhe gaoite", "orange", faction="sidhe", aggro=[70, 450], roam=150)
mem("sidhe draoi", "sidhe draoi", "red", faction="sidhe", aggro=[80, 500], roam=80)
mem("whispering willow", "whispering willow", "orange", faction="wood", aggro=[70, 400], roam=20)
mem("elder skogsfru", "elder skogsfru", "orange", faction="wood", aggro=[70, 450], roam=150)
mem("dryad blossom", "dryad blossom", "yellow", faction="dryads", aggro=[50, 400], roam=150)
mem("dryad greenthumb", "dryad greenthumb", "orange", faction="dryads", aggro=[70, 450], roam=150)
mem("treekeep", "treekeep", "red", faction="dryads", aggro=[80, 500], roam=60)
mem("young silverscale drake", "young silverscale drake", "orange", faction="drakes", guild="out of Malmohus", aggro=[75, 500], roam=250)
mem("werewolf", "werewolf", "yellow", faction="wolves", guild=W, aggro=[60, 450], roam=300)
mem("werewolf skulker", "werewolf skulker", "yellow", faction="wolves", guild=W, aggro=[60, 450], roam=300)
mem("werewolf guard", "werewolf guard", "orange", faction="wolves", guild=W, aggro=[75, 500], roam=150)
mem("werewolf warder", "werewolf warder", "orange", faction="wolves", guild=W, aggro=[75, 500], roam=150)
mem("wolfaur headsman", "wolfaur headsman", "orange", faction="wolves", guild=W, aggro=[80, 550], roam=300)
mem("werewolf lieutenant", "werewolf lieutenant", "red", faction="wolves", guild=W, aggro=[85, 550], roam=100)
mem("Hold-Warden Vargbjorn", "werewolf captain", "red", name="Hold-Warden Vargbjorn", size=1.2, faction="wolves", guild="Warden of Ulfhamr",
    aggro=[90, 600], roam=40, guards={"werewolf guard": 2})

for i, x, y, r in [("stor_gothi_camp", 604, 580, 70), ("tradande_camp", 1175, 805, 60), ("seithkona_circle", 1363, 256, 80),
                   ("bard_rest", 632, 1228, 35), ("thorvald_rest", 162, 1100, 35)]:
    b.clear(i, x, y, r, list(m.keys()) + ["seithkona"])
    b.S[-1]["block"] = "all"
b.wild("north_woods", 330, 80, 1220, 540, {"wood rat": 8, "brush cat": 8, "werewolf skulker": 6, "tree spirit": 5, "young wolverine": 4})
b.wild("frog_meadows", 940, 90, 1520, 560, {"giant tree frog": 8, "great tingler": 4, "brush cat": 4})
b.wild("wind_heights", 1200, 560, 1500, 1040, {"wind spirit": 8, "young wolverine": 3})
b.wild("east_edge", 1500, 370, 1620, 680, {"werewolf": 5})
b.wild("werewolf_lands", 560, 600, 1150, 960, {"werewolf guard": 6, "werewolf warder": 6, "wolfaur headsman": 4, "callow wolverine": 3})
b.camp("ulfhamr", 920, 720, 16, {"Hold-Warden Vargbjorn": 1, "werewolf lieutenant": 2, "werewolf warder": 3}, 900)
b.camp("ulfhamr_yard", 860, 800, 12, {"werewolf guard": 4, "wolfaur headsman": 2}, 600)
b.wild("headsmen_hunt", 660, 960, 1300, 1500, {"wolfaur headsman": 6, "moss maiden": 6, "woodland badger": 6, "wolverine": 3})
b.wild("timberland", 300, 380, 640, 1220, {"timber cat": 8, "timberland badger": 8, "battle-scarred mauler": 4})
b.wild("west_shore", 80, 190, 250, 1330, {"green orm": 8})
b.wild("sidhe_strand", 90, 840, 260, 1390, {"sidhe gaoite": 6})
b.camp("sidhe_ring", 165, 1150, 10, {"sidhe draoi": 2, "sidhe gaoite": 2}, 900)
b.wild("whispering_grove", 50, 1230, 620, 1580, {"whispering willow": 6, "elder skogsfru": 6})
b.wild("dryad_wood", 1320, 1050, 1570, 1550, {"dryad blossom": 6, "dryad greenthumb": 4})
b.camp("treekeep_grove", 1450, 1500, 12, {"treekeep": 2, "dryad greenthumb": 2}, 900)
b.wild("drake_trail", 1300, 1150, 1560, 1400, {"young silverscale drake": 4})

themes = ["The Seithkona Circle (north-east), the Stor Gothi's camp and Tradande's camp", "The north woods and the frog meadows",
          "Ulfhamr, the werewolf hold (middle) - the siege", "The wolfaur headsmen's hunting grounds (south)",
          "The timberland and the sidhe of the western shore", "The whispering grove (south-west) and the dryad wood (south-east)",
          "The drake trail out of Malmohus (south-east)"]
notes = ("Midgard's plan 2026-11-25, round 3: Dangerous; the west thread's werewolf stronghold, Ulfhamr, is the siege. Coordinates "
         "are zone units (metres x 40).")
tiers = {"werewolf captain": "red", "Captain Gruff": "red", "Werewolf Shaman": "red", "werewolf courier": "orange",
         "Mokerkialfi": "purple", "Storslange": "purple", "Nagoltooth": "red", "Cargila": "red", "Fjalar": "red", "Galar": "red",
         "Askafroa": "red", "Leildolf": "red", "Zrit-Zrit": "red", "Stripe": "red", "Thasior": "orange", "Vindvasen": "orange",
         "Furf": "orange", "Pellinistra": "orange", "Lasaer": "orange", "Krrrck": "orange", "wolfaur gladiator": "red"}
factions = {"wood": {"id": 9661, "aggro": 60}, "sidhe": {"id": 9662, "aggro": 80}, "dryads": {"id": 9663, "aggro": 70},
            "drakes": {"id": 9664, "aggro": 85, "enemies": ["wolves"]}, "wolves": {"id": 9665, "aggro": 90, "enemies": ["drakes"]}}
b.write(sys.argv[1], themes, notes, [], tiers, factions)
