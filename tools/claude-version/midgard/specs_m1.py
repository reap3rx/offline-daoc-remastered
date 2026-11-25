"""Midgard round 1's other item specs (claude 2026-11-24): reputation stock (rep100: the Volur of Haggerfel and King Eirik's
Huscarls; rep101: the Steading-League), the new events' bosses (nu100, nu101) and Ulfrstead's camp (uf101, with its draughts)."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
from story_gen import Zone, slug
D = '/home/claude/lg/tools/claude-version/named_uniques/'

class Spec(Zone):
    def __init__(self, zone, name, prefix):
        super().__init__(zone, name, 2, 'x')
        self.pfx = prefix
    def prefix(self):
        return self.pfx
    def write_spec(self, fname, extra=None):
        s = {'zone': self.zone, 'region': 100, 'realm': 2, 'prefix': self.pfx, 'story': True, 'items': self.items}
        s.update(extra or {})
        json.dump(s, open(D + fname, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        return ['%s_%s' % (self.pfx, slug(i['name'])) for i in self.items]

out = []
r = Spec(100, 'Vale of Mularn', 'rep100')
r.item("Huscarl-Friend's Ring", 'ring', 5, 'might', "Iron, with Eirik's hammer.")
r.item("Jordheim Road Belt", 'belt', 5, 'ward', "Royal blue leather.")
r.item("Shield of Jordheim Torc", 'neck', 10, 'might', "Silver twisted round iron.")
r.item("Eirik's Bracer", 'bracer', 10, 'ward', "The King's mark, worked in silver.")
r.item("Mantle of Eirik's Champion", 'cloak', 16, 'ward', "Royal blue and gold. Only the King's Champions wear it.")
r.item("Seer-Friend's Charm", 'gem', 5, 'faith', "A tiny silver well-bucket.")
r.item("Well-Reader's Ring", 'ring', 10, 'mind', "Silver, set with a drop of well-water in glass.")
r.item("Nine-Knot Bracer", 'bracer', 10, 'faith', "Knotted nine times, the volur's way.")
r.item("Mantle of the Well-Keeper", 'cloak', 16, 'faith', "Grey, with the nine-knot border. Only the Keepers of the Well wear it.")
out += r.write_spec('rep100_mularn.json')
r = Spec(101, 'East Svealand', 'rep101')
r.item("League-Friend's Ring", 'ring', 8, 'might', "Iron, stamped with the League's sheaf.")
r.item("Steading Belt", 'belt', 8, 'ward', "Plain, strong, farm-made.")
r.item("League Spearman's Torc", 'neck', 12, 'might', "Bronze, with a sheaf and a spear.")
r.item("Fold-Keeper's Bracer", 'bracer', 12, 'ward', "Leather, bitten by wolves and still whole.")
r.item("Mantle of the Wolf-Breaker", 'cloak', 16, 'ward', "League grey, the wolf struck through. Only the Wolf-Breakers wear it.")
out += r.write_spec('rep101_east_svealand.json')

e = Spec(100, 'Vale of Mularn', 'nu100')
e.item("Moon-Howler's Frost Fang", 'gem', 13, 'might', "A fang rimed with frost that never melts.")
e.item("Moonrise Mantle", 'cloak', 13, 'ward', "Grey wolf-fur, pale as moonlight.")
e.item("Red-Eye Fetish", 'gem', 12, 'mind', "The shaman's fetish, the red eye scrubbed half off.")
out += e.write_spec('ev100_mularn.json')
e = Spec(101, 'East Svealand', 'nu101')
e.item("Vargeir's Wolf-Hame", 'cloak', 14, 'finesse', "A wolf's whole skin, the jaws for a hood. Taken off a farmer's son.")
e.item("Brood-Mother's Scale", 'gem', 15, 'ward', "A silver scale as big as a hand.")
out += e.write_spec('ev101_east_svealand.json')

u = Spec(101, 'East Svealand', 'uf101')
u.item("Ulfrstead Steading Cloak", 'cloak', 14, 'ward', "League grey, with the steading's door. Given to those who took Ulfrstead back.")
u.item("Hall-Door Ring", 'ring', 14, 'might', "The hall door's old latch, hammered into a ring.")
u.item("League Spear Torc", 'neck', 14, 'might', "Bronze, from the League's armoury.")
u.item("Byre-Beam Bracer", 'bracer', 14, 'ward', "Oak from the byre the wolves broke into.")
u.item("Ulfar's Grey Hame", 'cloak', 16, 'finesse', "The Hame-Jarl's grey wolf-skin. The League cut the head off it.")
u.item("Hame-Mother's Bell Necklace", 'neck', 16, 'faith', "Farm-bells on a cord, from every farm she raided.")
EMBLEM = (61 << 9) | (1 << 7) | (0 << 3) | 0
out += u.write_spec('uf101_ulfrstead.json', {'camp': {'cloak': 'uf101_ulfrstead_steading_cloak', 'emblem': EMBLEM, 'draughts': [
    ['Strong_Draught_of_Healing', 'uf101_moor_ale', 'Moor Ale', "Thordis's own. Heals more than it should."],
    ['Strong_Draught_of_Power', 'uf101_lingonberry_tonic', 'Lingonberry Tonic', "Tart and sharp. It clears the head."],
    ['CombinedRegens_Draught', 'uf101_steading_mead', 'Steading Mead', "The steading's mead. Everything comes back a little faster after a cup."]]}})
print('\n'.join(out))
