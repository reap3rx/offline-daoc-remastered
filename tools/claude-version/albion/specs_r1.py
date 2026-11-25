"""Round 1's other item specs (claude 2026-11-24): the reputation quartermasters' stock (rep000, rep002), the new events'
bosses (nu000, nu002) and Vetusta Abbey's camp (va002, with its draughts)."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
from story_gen import Zone, slug
D = '/home/claude/lg/tools/claude-version/named_uniques/'

class Spec(Zone):
    def __init__(self, zone, name, prefix):
        super().__init__(zone, name, 1, 'x')
        self.pfx = prefix
    def prefix(self):
        return self.pfx
    def write_spec(self, fname, extra=None):
        s = {'zone': self.zone, 'region': 1, 'realm': 1, 'prefix': self.pfx, 'story': True, 'items': self.items}
        s.update(extra or {})
        json.dump(s, open(D + fname, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        return ['%s_%s' % (self.pfx, slug(i['name'])) for i in self.items]

r = Spec(0, 'Camelot Hills', 'rep000')
r.item("Friend of Cotswold's Ring", 'ring', 6, 'ward', "Copper, with a sheaf on it. Every Warden has one; now so do you.")
r.item("Hedge-Warden's Belt", 'belt', 6, 'finesse', "A Warden's belt, with a hook for the billhook and a pouch for the tally.")
r.item("Right Hand's Torc", 'neck', 10, 'might', "Bronze, twisted like a hay-rope. Hollis's own design.")
r.item("Cotswold Fold Bracer", 'bracer', 10, 'ward', "Sheepskin and iron. Warm, and it stops a wolf's teeth.")
r.item("Mantle of the Hearthward", 'cloak', 14, 'ward', "Cotswold green, with the village hearth stitched in gold. Only the Hearthwards wear it.")
r.item("Watch-Friend's Ring", 'ring', 8, 'might', "Iron, stamped with Prydwen - Arthur's ship.")
r.item("Watch-Road Belt", 'belt', 8, 'finesse', "The Watch rides every road to Camelot. This belt has done most of them.")
r.item("Sworn Torc of the Watch", 'neck', 12, 'faith', "Silver and blue. Given when a Watch-Friend swears the oath.")
r.item("Round Table Bracer", 'bracer', 12, 'might', "Chased with a ring of twelve seats - and a thirteenth, empty.")
r.item("Mantle of the Shield of Camelot", 'cloak', 16, 'ward', "Pendragon red, with the dragon in gold. Only the Shields of Camelot wear it.")
rep0 = r.write_spec('rep000_camelot_hills.json')

r = Spec(2, 'Black Mountains South', 'rep002')
r.item("Lay Brother's Charm", 'gem', 8, 'faith', "A wooden cross on a cord. The Faithful give one to every friend of the abbey.")
r.item("White Cord of Vetusta", 'belt', 8, 'mind', "The true brothers' cord - white, knotted three times.")
r.item("Psalter-Chain Torc", 'neck', 12, 'faith', "A thin chain that once held a psalter to a lectern.")
r.item("Cloister-Stone Bracer", 'bracer', 12, 'ward', "Set with a chip of the cloister's old stone.")
r.item("Mantle of the Bell-Ringer", 'cloak', 17, 'faith', "White wool, with Vetusta's bell in grey. Only the Bell-Ringers of Vetusta wear it.")
rep2 = r.write_spec('rep002_black_mtns_south.json')

e = Spec(0, 'Camelot Hills', 'nu000')
e.item("Hierophant's Red Cord", 'belt', 15, 'mind', "Won from Hierophant Cadan when the Crimson Rite was broken. Thirteen knots, all burned through.")
e.item("Silver-Bristle Charm", 'gem', 13, 'might', "A silver bristle from Grugyn, the Twrch Trwyth's son, bound in red thread.")
e.item("Door-Breaker's Horn", 'gem', 15, 'ward', "Won from Gorgoth the Door-Breaker. It still smells of brimstone.")
nu0 = e.write_spec('ev000_camelot_hills.json')

e = Spec(2, 'Black Mountains South', 'nu002')
e.item("Drowned Captain's Plume", 'neck', 14, 'might', "A rotted red-dragon plume, from a captain of Mount Badon. It's dry now.")
nu2 = e.write_spec('ev002_black_mtns_south.json')

v = Spec(2, 'Black Mountains South', 'va002')
v.item("Vetusta Bell Cloak", 'cloak', 15, 'faith', "Abbey white, with the bell. Given to those who took Vetusta back.")
v.item("Cloister Key Ring", 'ring', 15, 'ward', "The cloister key, hammered into a ring. The doors have new locks now.")
v.item("White Cord Belt", 'belt', 15, 'mind', "A true brother's cord, given in thanks.")
v.item("Abbey Wall Bracer", 'bracer', 15, 'might', "Banded iron from the abbey gate, rebuilt.")
v.item("Hrodric's Red Cord", 'belt', 17, 'might', "Won from Brother-Captain Hrodric, the Bishop's Sword. The Faithful cut it in two.")
v.item("Red Abbot's Cope-Clasp", 'gem', 17, 'faith', "Won from the Red Abbot when Vetusta held. Burhoff's own clasp.")
EMBLEM = (60 << 9) | (1 << 7) | (0 << 3) | 0
va = v.write_spec('va002_vetusta.json', {'camp': {'cloak': 'va002_vetusta_bell_cloak', 'emblem': EMBLEM, 'draughts': [
    ['Strong_Draught_of_Healing', 'va002_infirmary_draught', 'Infirmary Draught', "Gwladys's own. Bitter, and it works."],
    ['Strong_Draught_of_Power', 'va002_abbey_garden_tonic', 'Abbey Garden Tonic', "Sage and rosemary from the abbey garden, steeped all night."],
    ['CombinedRegens_Draught', 'va002_vetusta_mead', 'Vetusta Mead', "The brothers' mead. Everything comes back a little faster after a cup."]]}})
print(rep0, rep2, nu0, nu2, va, sep='\n')
