"""Midgard round 3's other item specs (claude 2026-11-25): reputation stock (rep104: the Forge of Khizil; rep106: the Wolfsbane
Rangers and the Seithkona Circle; rep107: the Wardens of Vanern), the new events' bosses (nu104, nu106, nu107) and the camps of
Ulfhamr and Hrafnsholm (uf106, uf107, with their draughts)."""
import sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from specs_m1_lib import Spec

out = []
r = Spec(104, 'Muspelheim', 'rep104')
r.item("Forge-Friend's Ring", 'ring', 20, 'might', "Dverge iron, Khizil's hammer stamped in it.")
r.item("Khizil Smith Belt", 'belt', 20, 'ward', "Forge-leather, scorched and supple.")
r.item("Hammer of Khizil Torc", 'neck', 24, 'might', "A tiny hammer on a heavy chain.")
r.item("Anvil-Iron Bracer", 'bracer', 24, 'ward', "Iron from the forge's oldest anvil.")
r.item("Mantle of the Forge-Fire", 'cloak', 28, 'ward', "Forge-black, embroidered in red. Only the Keepers of the Forge-Fire wear it.")
out += r.write_spec('rep104_muspelheim.json')
r = Spec(106, 'Skona Ravine', 'rep106')
r.item("Ranger-Friend's Ring", 'ring', 30, 'finesse', "Grey iron with a sprig of wolfsbane.")
r.item("Wolfsbane Belt", 'belt', 30, 'ward', "Rangers' grey, wolfsbane sewn in.")
r.item("Wolfsbane-Sworn Torc", 'neck', 34, 'might', "Silver twisted with wolfsbane stems.")
r.item("Grey Ranger Bracer", 'bracer', 34, 'finesse', "Soft grey leather, a ranger's.")
r.item("Mantle of the Ulfhamr Breaker", 'cloak', 38, 'ward', "Rangers' grey, a broken wolf-skull on the back. Only the Breakers wear it.")
r.item("Circle-Friend's Charm", 'gem', 30, 'faith', "A pale stone on a silver thread.")
r.item("Moon-Reader's Ring", 'ring', 30, 'mind', "Moonstone, cut in a crescent.")
r.item("Moon-Phase Bracer", 'bracer', 34, 'faith', "Silver plates, one for each phase.")
r.item("Mantle of the Moon-Stone", 'cloak', 38, 'faith', "White wool, the moon's road stitched in silver. Only the Keepers of the Moon-Stone wear it.")
out += r.write_spec('rep106_skona.json')
r = Spec(107, 'Vanern Swamp', 'rep107')
r.item("Warden-Friend's Ring", 'ring', 38, 'might', "Bog-iron, the Wardens' raven on it.")
r.item("Bog-Iron Belt", 'belt', 38, 'ward', "Heavy, black, rust-proof.")
r.item("Raven of Vanern Torc", 'neck', 42, 'might', "A black iron raven on a chain.")
r.item("Rowan-Ward Bracer", 'bracer', 42, 'ward', "Rowan wood and silver, against the dead.")
r.item("Mantle of Hrafnsholm", 'cloak', 46, 'ward', "Grey and black, the raven the right way up. Only the Holders of Hrafnsholm wear it.")
out += r.write_spec('rep107_vanern.json')

e = Spec(104, 'Muspelheim', 'nu104')
e.item("Brood-Sire's Ember Heart", 'gem', 29, 'might', "A coal from the wyrm's heart. It never goes out.")
e.item("Wyrm-Wing Mantle", 'cloak', 29, 'ward', "Wyrm-hide, thin as cloth, hot to the touch.")
e.item("Surtling's Iron Crown", 'neck', 28, 'might', "A fire giant's crown, small enough now to wear at the throat.")
out += e.write_spec('ev104_muspelheim.json')
e = Spec(106, 'Skona Ravine', 'nu106')
e.item("Moon-Caller's Hide", 'cloak', 36, 'mind', "Werewolf hide cut with the moon's phases.")
out += e.write_spec('ev106_skona.json')
e = Spec(107, 'Vanern Swamp', 'nu107')
e.item("Hrimgrim's Ice Horn", 'gem', 46, 'mind', "A horn of ice that never melts. Don't blow it.")
out += e.write_spec('ev107_vanern.json')

def camp(zone, name, pfx, fname, items, cloak, draughts, emblem):
    u = Spec(zone, name, pfx)
    for it in items:
        u.item(*it)
    return u.write_spec(fname, {'camp': {'cloak': cloak, 'emblem': emblem, 'draughts': draughts}})

out += camp(106, 'Skona Ravine', 'uf106', 'uf106_ulfhamr.json', [
    ("Ulfhamr Breaker's Cloak", 'cloak', 36, 'ward', "Rangers' grey, a broken wolf-skull on the back. Given to those who broke Ulfhamr."),
    ("Moon-Stone Ring", 'ring', 36, 'mind', "A chip of the hold's cracked moon-stone."),
    ("Wolfsbane Torc", 'neck', 36, 'might', "Silver twisted with dried wolfsbane."),
    ("Hold-Gate Bracer", 'bracer', 36, 'ward', "Black logs from the hold's gate, banded in iron."),
    ("Ulfgrim's Skull Helm", 'neck', 38, 'might', "The jarl's wolf-skull helm, cut down to a pendant."),
    ("Moon-Mother's White Pelt", 'cloak', 38, 'finesse', "White as the moon she hunted.")],
    'uf106_ulfhamr_breaker_s_cloak', [
    ['Strong_Draught_of_Healing', 'uf106_ranger_s_ale', "Ranger's Ale", "Gro's own. Better than it smells."],
    ['Strong_Draught_of_Power', 'uf106_wolfsbane_tonic', 'Wolfsbane Tonic', "Bitter. Harmless to men. Mostly."],
    ['CombinedRegens_Draught', 'uf106_moonlit_mead', 'Moonlit Mead', "Brewed under the moon. Everything comes back a little faster after a cup."]],
    (63 << 9) | (3 << 7) | (0 << 3) | 0)
out += camp(107, 'Vanern Swamp', 'uf107', 'uf107_hrafnsholm.json', [
    ("Hrafnsholm Raven Cloak", 'cloak', 45, 'ward', "The Wardens' raven, the right way up. Given to those who took Hrafnsholm back."),
    ("Rune-Chain Ring", 'ring', 45, 'mind', "A link of the jotun's chain, the runes ground off."),
    ("Watch-Hold Torc", 'neck', 45, 'might', "Bog-iron, the hold's tower on it."),
    ("Barrow-Breaker Bracer", 'bracer', 45, 'ward', "Rowan and iron, against the dead."),
    ("Hrafnkel's Barrow-Gold", 'gem', 47, 'might', "Three-hundred-year-old gold, cold to the touch."),
    ("Bergelmir's Broken Chain", 'belt', 47, 'ward', "The jotun's chain, broken. He'd want you to have it.")],
    'uf107_hrafnsholm_raven_cloak', [
    ['Strong_Draught_of_Healing', 'uf107_bog_ale', 'Bog Ale', "Hallveig's own. Brown, and better than it looks."],
    ['Strong_Draught_of_Power', 'uf107_rowan_water', 'Rowan Water', "Clean and bitter. The dead hate it."],
    ['CombinedRegens_Draught', 'uf107_warden_s_mead', "Warden's Mead", "The Wardens' mead. Everything comes back a little faster after a cup."]],
    (64 << 9) | (1 << 7) | (0 << 3) | 0)
print(' '.join(out))
