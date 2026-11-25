"""Round 3's other item specs (claude 2026-11-24): reputation stock (rep003, rep006, rep010), the new events' bosses (nu003, nu006,
nu010) and Dinas Emrys's camp (de003, with its draughts)."""
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

out = []
r = Spec(3, 'Black Mountains North', 'rep003')
r.item("Garrison Friend's Ring", 'ring', 16, 'might', "Iron, with Swanton's tower.")
r.item("North March Belt", 'belt', 16, 'ward', "A shieldman's belt, worn on the north road.")
r.item("Snowdonia Shieldman's Torc", 'neck', 23, 'might', "Bronze and grey stone.")
r.item("Mantle of the North March", 'cloak', 30, 'ward', "Mountain grey. Only the Wardens of the North March wear it.")
r.item("Emrys Charm", 'gem', 16, 'mind', "A tiny harp and a dragon, in silver.")
r.item("Dragon-Reader's Bracer", 'bracer', 23, 'mind', "Engraved with Merlin's prophecy of the two dragons.")
r.item("Prophet's Ring", 'ring', 23, 'faith', "Plain gold, with a star.")
r.item("Mantle of the Dragon-Readers", "cloak", 30, "faith", "Red and white. Only the Keepers of Emrys's Fort wear it.")
out += r.write_spec('rep003_black_mtns_north.json')
r = Spec(6, 'Cornwall', 'rep006')
r.item("Tintagel Friend's Ring", 'ring', 20, 'might', "Black and gold, Tintagel's colours.")
r.item("Duke's Road Belt", 'belt', 20, 'ward', "Cornish leather, tooled with a boar.")
r.item("Tintagel Shieldman's Torc", 'neck', 32, 'might', "Bronze, with the cliffs of Tintagel.")
r.item("Mantle of the Duke's Champion", 'cloak', 44, 'ward', "Black and gold. Only the Duke's Champions wear it.")
r.item("Oath-Friend's Charm", 'gem', 20, 'faith', "A wrestler's belt-buckle, in miniature.")
r.item("Giant-Wrestler's Bracer", 'bracer', 32, 'might', "Thick leather and iron, for gripping giants.")
r.item("Corinean Ring", 'ring', 32, 'faith', "Iron, engraved with Corineus's oath.")
r.item("Mantle of the Heir of Corineus", 'cloak', 44, 'faith', "Cornish black, with Corineus's belt in gold.")
out += r.write_spec('rep006_cornwall.json')
r = Spec(10, 'Lyonesse', 'rep010')
r.item("Remnant Friend's Ring", 'ring', 42, 'ward', "Salt-stained silver.")
r.item("Remnant Knight's Belt", 'belt', 42, 'might', "Blue and gold, faded by the sea.")
r.item("Sword of Lyonesse Torc", 'neck', 46, 'might', "A sword and a sun, in gold.")
r.item("Mantle of the Sword of Lyonesse", 'cloak', 50, 'ward', "Lyonesse blue. Only the Swords of Lyonesse wear it.")
r.item("Harp-Friend's Charm", 'gem', 42, 'charm', "A harp, very small, in silver.")
r.item("Harper's Bracer", 'bracer', 46, 'charm', "Worked with Tristan's lay, in tiny letters.")
r.item("Lay-Keeper's Ring", 'ring', 46, 'faith', "Black and white enamel, the two sails.")
r.item("Mantle of Tristan's Lay", 'cloak', 50, 'charm', "Blue and gold. Only the Keepers of Tristan's Lay wear it.")
out += r.write_spec('rep010_lyonesse.json')

e = Spec(3, 'Black Mountains North', 'nu003')
e.item("Fire-Priest's Cord", 'belt', 29, 'mind', "A red cord, knotted once for every fire. Burned through.")
out += e.write_spec('ev003_black_mtns_north.json')
e = Spec(6, 'Cornwall', 'nu006')
e.item("Aquilifer's Lion-Skin", 'cloak', 42, 'might', "The eagle-bearer's lion-skin, sea-stained and old.")
e.item("Gilt Eagle Feather", 'gem', 42, 'faith', "From the eagle of the Ninth.")
e.item("White Bucca's Shell", 'gem', 28, 'mind', "A white shell. Hold it to your ear and hear a storm.")
out += e.write_spec('ev006_cornwall.json')
e = Spec(10, 'Lyonesse', 'nu010')
e.item("Storm-Wyrm's Eye", 'gem', 52, 'mind', "A pale, clouded orb, crackling faintly.")
e.item("White Squall Mantle", 'cloak', 52, 'ward', "Storm-grey. The wind won't touch it.")
e.item("White Sail Ribbon", 'belt', 48, 'charm', "A strip of the white sail, scraped clean of black paint.")
out += e.write_spec('ev010_lyonesse.json')

g = Spec(3, 'Black Mountains North', 'de003')
g.item("Cloak of Emrys's Fort", 'cloak', 28, 'ward', "Grey and red, with the two dragons. Given to those who took Dinas Emrys.")
g.item("Pit-Stone Ring", 'ring', 28, 'mind', "A chip of a silenced pit-stone.")
g.item("Hill-Fort Torc", 'neck', 28, 'might', "Bronze, from the fort's armoury.")
g.item("Garrison Wall Bracer", 'bracer', 28, 'ward', "Iron bands from the rebuilt gate.")
g.item("Dragon-Priestess's Scale", 'gem', 31, 'might', "A red scale from her arm. It's warm.")
g.item("Tribal War-Horn", 'neck', 30, 'might', "A red-corded tribe's horn, its cord cut.")
g.item("Hierarch's Seal", 'gem', 32, 'mind', "Morgana's right hand's seal. Broken.")
EM = (70 << 9) | (1 << 7) | (0 << 3) | 0
out += g.write_spec('de003_dinas_emrys.json', {'camp': {'cloak': 'de003_cloak_of_emrys_s_fort', 'emblem': EM, 'draughts': [
    ['Strong_Draught_of_Healing', 'de003_mountain_draught', 'Mountain Draught', "Brewed from crag-herbs. Bitter as the wind."],
    ['Strong_Draught_of_Power', 'de003_bard_s_honey_tonic', "Bard's Honey Tonic", "Honey and sage. Elffin swears it clears the voice and the head."],
    ['CombinedRegens_Draught', 'de003_emrys_mead', 'Emrys Mead', "The fort's mead. Everything comes back faster after a cup."]]}})
print('\n'.join(out))
