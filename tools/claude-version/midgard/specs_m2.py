"""Midgard round 2's other item specs (claude 2026-11-25): reputation stock (rep102: the Huginfel Shieldwall; rep103: the Nalliten
Runecasters; rep105: the Galplen Woodwards and the Seidr-Folk), the new events' bosses (nu102, nu103, nu105) and the Blood-Hall's
camp (uf102, with its draughts)."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from story_gen import slug
from specs_m1_lib import Spec

out = []
r = Spec(102, 'West Svealand', 'rep102')
r.item("Shield-Friend's Ring", 'ring', 12, 'might', "Iron, stamped with Huginfel's gate.")
r.item("Huginfel Gate Belt", 'belt', 12, 'ward', "Red leather, the Shieldwall's colour.")
r.item("Shieldwall-Sworn Torc", 'neck', 16, 'might', "Bronze, with a linden shield-boss for a clasp.")
r.item("Linden-Shield Bracer", 'bracer', 16, 'ward', "Linden-wood plates on leather, like a little shield.")
r.item("Mantle of the Blood-Hall Breaker", 'cloak', 20, 'ward', "Huginfel red, a broken chain on the back. Only the Breakers wear it.")
out += r.write_spec('rep102_west_svealand.json')
r = Spec(103, 'Gotar', 'rep103')
r.item("Stave-Friend's Charm", 'gem', 14, 'faith', "A little rune-stave on a thong.")
r.item("Rune-Reader's Ring", 'ring', 14, 'mind', "Carved bone, a rune on every side.")
r.item("Carved-Stave Bracer", 'bracer', 18, 'faith', "Rune-staves bound side by side.")
r.item("Nalliten Seer Torc", 'neck', 18, 'mind', "Silver, with a seer's eye.")
r.item("Mantle of the Stave-Keeper", 'cloak', 22, 'faith', "Grey-green, rune-bordered. Only the Keepers of the Staves wear it.")
out += r.write_spec('rep103_gotar.json')
r = Spec(105, 'Myrkwood Forest', 'rep105')
r.item("Woodward-Friend's Ring", 'ring', 24, 'might', "Iron, with the black tree.")
r.item("Galplen Axe Belt", 'belt', 24, 'ward', "A woodward's belt, with an axe-loop.")
r.item("Axe of Galplen Torc", 'neck', 28, 'might', "Iron, with a little silver axe.")
r.item("Black-Tree Bracer", 'bracer', 28, 'ward', "Black leather, the Woodwards' tree in silver.")
r.item("Mantle of the Myrkwood Warden", 'cloak', 32, 'ward', "Woodward green and black. Only the Wardens of the Myrkwood wear it.")
r.item("Seidr-Friend's Charm", 'gem', 24, 'faith', "A bead of amber with a moth in it.")
r.item("Dream-Walker's Ring", 'ring', 24, 'mind', "Moonstone in black iron.")
r.item("Seidr-Thread Bracer", 'bracer', 28, 'faith', "Woven of seidr-thread, cold as moonlight.")
r.item("Mantle of the Volva's Keeper", 'cloak', 32, 'faith', "Grey wool with Groa's nine knots. Only the Volva's Keepers wear it.")
out += r.write_spec('rep105_myrkwood.json')

e = Spec(102, 'West Svealand', 'nu102')
e.item("Storm-Haxa's Frozen Bowl", 'gem', 19, 'mind', "A bowl of blood frozen solid. It never thaws.")
e.item("Blizzard-Rider's Mantle", 'cloak', 19, 'ward', "White fur, rimed with frost.")
out += e.write_spec('ev102_west_svealand.json')
e = Spec(103, 'Gotar', 'nu103')
e.item("Naudr's Scale-Mail Bracer", 'bracer', 22, 'ward', "Red dragon-scale on svartalf iron. Warm.")
e.item("Caravan-Master's Ledger", 'gem', 22, 'mind', "Every page in gold. The last one names Malmohus.")
e.item("Steersman's Bell", 'gem', 19, 'faith', "The wreck's bell, small enough to hold. It's quiet now.")
out += e.write_spec('ev103_gotar.json')
e = Spec(105, 'Myrkwood Forest', 'nu105')
e.item("Blood-Moon Fang", 'neck', 32, 'might', "A fang as long as a dagger, red in moonlight.")
e.item("Red-Moon Mantle", 'cloak', 32, 'ward', "Wolf-fur, dyed by no dye.")
e.item("Ormr's Scale-Robe Sash", 'belt', 31, 'mind', "Red dragon-scale on silk.")
out += e.write_spec('ev105_myrkwood.json')

u = Spec(102, 'West Svealand', 'uf102')
u.item("Blood-Hall Breaker's Cloak", 'cloak', 19, 'ward', "Huginfel red, a broken chain on the back. Given to those who broke the Blood-Hall.")
u.item("Cut-Chain Ring", 'ring', 19, 'might', "A link of thrall-chain, cut and hammered round.")
u.item("Shieldwall Boss Torc", 'neck', 19, 'might', "Iron, with a shield-boss clasp.")
u.item("Thrall-Pen Bracer", 'bracer', 19, 'ward', "Oak from the thrall-pens, banded in iron.")
u.item("Hrolf's Oath-Scarred Pelt", 'cloak', 21, 'finesse', "The jarl's wolf-pelt, cut with his oaths.")
u.item("Haxa-Mother's Steaming Bowl", 'gem', 21, 'mind', "The blood in it steams, and never cools.")
EMBLEM = (62 << 9) | (2 << 7) | (0 << 3) | 0
out += u.write_spec('uf102_blood_hall.json', {'camp': {'cloak': 'uf102_blood_hall_breaker_s_cloak', 'emblem': EMBLEM, 'draughts': [
    ['Strong_Draught_of_Healing', 'uf102_hall_ale', 'Hall Ale', "Unn's own brewing. Better than the Blodfelag ever got."],
    ['Strong_Draught_of_Power', 'uf102_juniper_draught', 'Juniper Draught', "Bitter and clean. It clears the head."],
    ['CombinedRegens_Draught', 'uf102_freedwoman_s_mead', "Freedwoman's Mead", "Brewed by free hands. Everything comes back a little faster after a cup."]]}})
print('\n'.join(out))
