"""Round 2's other item specs (claude 2026-11-24): reputation stock (rep001, rep008, rep009), the new events' bosses (nu001,
nu008, nu009) and the two forts' camps (gd001 the Giants' Dance, vk009 the Vigil Keep, with their draughts)."""
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
r = Spec(1, 'Salisbury Plains', 'rep001')
r.item("Friend of Amesbury's Ring", 'ring', 16, 'faith', "A plain silver ring with the priory's lily.")
r.item("Grave-Tender's Belt", 'belt', 16, 'ward', "Hung with a trowel and a little bell, for the graves.")
r.item("Keeper of the Graves Torc", 'neck', 21, 'faith', "Silver, worked with 460 tiny knots.")
r.item("Long Knives Bracer", 'bracer', 21, 'might', "Engraved with a feast-table, and a knife laid across it.")
r.item("Mantle of the Mourner", 'cloak', 26, 'faith', "Grey linen and black velvet. Only the Mourners of the Long Knives wear it.")
out += r.write_spec('rep001_salisbury_plains.json')
r = Spec(8, 'Campacorentin Forest', 'rep008')
r.item("Ranger's Leaf-Pin", 'gem', 12, 'finesse', "A bronze oak-leaf. Every friend of the Rangers wears one.")
r.item("Greenway Belt", 'belt', 12, 'might', "A ranger's belt, with loops for arrows and snares.")
r.item("Ulfwych Torc", 'neck', 18, 'might', "Bronze, with the Caer's wolf.")
r.item("Thorn-Keeper's Bracer", 'bracer', 18, 'faith', "Briar-wood, worked with white thorn-flowers.")
r.item("Sleep-Keeper's Ring", 'ring', 18, 'mind', "A ring of thorn, smooth as glass.")
r.item("Mantle of the Greenway Warden", 'cloak', 24, 'finesse', "Forest green. Only the Wardens of the Greenway wear it.")
r.item("Mantle of the Thornwarden", 'cloak', 24, 'faith', "Briar-green and white. Only the Thornwardens of Campacorentin wear it.")
r.item("Thornwarden's Briar Charm", 'gem', 12, 'faith', "A briar-knot, given to the Thornwardens' friends.")
out += r.write_spec('rep008_campacorentin.json')
r = Spec(9, 'Avalon Marsh', 'rep009')
r.item("Marsh-Friend's Ring", 'ring', 14, 'ward', "A reed-ring, dipped in tar. It'll outlast you.")
r.item("Wader's Belt", 'belt', 14, 'finesse', "The Marsh Wardens' belt, with a gaff-hook.")
r.item("Drowned March Torc", 'neck', 20, 'might', "Bog-iron, twisted cold.")
r.item("Mantle of the Drowned March", 'cloak', 26, 'ward', "Marsh-brown. Only the Wardens of the Drowned March wear it.")
r.item("Shore-Keeper's Charm", 'gem', 14, 'faith', "A white pebble from the Isle's shore.")
r.item("Isle-Mist Bracer", 'bracer', 20, 'mind', "Pale silver. It's always slightly damp.")
r.item("Mantle of the Sleeper's Guard", 'cloak', 26, 'faith', "White and grey, with the Isle's tower. Only the Guardians of the Sleeper wear it.")
r.item("Apple-Isle Ring", 'ring', 20, 'faith', "An apple-blossom in white gold.")
out += r.write_spec('rep009_avalon_marsh.json')

e = Spec(1, 'Salisbury Plains', 'nu001')
e.item("Foreman's Maul-Ring", 'ring', 24, 'might', "A ring of granite, cut from Trebiggan's maul-head.")
e.item("Feast-Master's Seax-Ring", 'ring', 21, 'finesse', "From the hilt of a Saxon knife. It's cold.")
out += e.write_spec('ev001_salisbury_plains.json')
e = Spec(8, 'Campacorentin Forest', 'nu008')
e.item("Green Girdle", 'belt', 26, 'ward', "Green silk, worked with gold. Gawain wore one like it, and lived.")
e.item("Green Chapel Ring", 'ring', 26, 'might', "A ring of holly-wood that stays green all winter.")
e.item("Root-Bleeder's Knife-Ring", 'ring', 23, 'mind', "From a sacrificer's knife. Elaine washed it in the stream.")
out += e.write_spec('ev008_campacorentin.json')
e = Spec(9, 'Avalon Marsh', 'nu009')
e.item("Oarsmaster's Ring", 'ring', 22, 'might', "Salt-white bronze, from the oar of the black barge.")
out += e.write_spec('ev009_avalon_marsh.json')

g = Spec(1, 'Salisbury Plains', 'gd001')
g.item("Cloak of the Dance", 'cloak', 24, 'ward', "Grey, with the ring of stones in white. Given to those who took back the Dance.")
g.item("Trilithon Ring", 'ring', 24, 'might', "Three stones, two standing and one across.")
g.item("Heel-Stone Torc", 'neck', 24, 'faith', "With a chip of the heel stone set in the clasp.")
g.item("Amesbury Grave Bracer", 'bracer', 24, 'ward', "The Sisters' work, linen over leather.")
g.item("Bolster's Arm-Ring", 'bracer', 26, 'might', "Won from Bolster, Herald of Golestandt. A man could wear it as a belt.")
g.item("Cormoran's Tooth", 'gem', 26, 'might', "Won from Cormoran when the Dance held. As long as your hand.")
EM = (40 << 9) | (1 << 7) | (0 << 3) | 0
out += g.write_spec('gd001_giants_dance.json', {'camp': {'cloak': 'gd001_cloak_of_the_dance', 'emblem': EM, 'draughts': [
    ['Strong_Draught_of_Healing', 'gd001_amesbury_draught', 'Amesbury Draught', "The Sisters' own. It tastes of lavender."],
    ['Strong_Draught_of_Power', 'gd001_downs_herb_tonic', 'Downs Herb Tonic', "Chalk-downs thyme, steeped in spring water."],
    ['CombinedRegens_Draught', 'gd001_dance_mead', 'Dance Mead', "Brewed for midsummer at the stones. Everything comes back faster after a cup."]]}})
v = Spec(9, 'Avalon Marsh', 'vk009')
v.item("Cloak of the Relief", 'cloak', 22, 'ward', "Marsh-brown, with the Vigil's white tower. Given to those who relieved the Vigil.")
v.item("Vigil Tower Ring", 'ring', 22, 'faith', "The white tower in grey stone.")
v.item("Drowned Plate Bracer", 'bracer', 22, 'might', "Cut from the Vigil's armour, scoured clean.")
v.item("Marsh Warden's Torc", 'neck', 22, 'ward', "Bog-iron, twisted by the Wardens' smith.")
v.item("Vrask's Gorget", 'neck', 25, 'might', "Won from Ghoul-Marshal Vrask. Still damp inside.")
v.item("Lord-Commander's Seal", 'gem', 25, 'faith', "Won from the Drowned Lord-Commander when the keep held.")
EM = (52 << 9) | (1 << 7) | (0 << 3) | 0
out += v.write_spec('vk009_vigil_keep.json', {'camp': {'cloak': 'vk009_cloak_of_the_relief', 'emblem': EM, 'draughts': [
    ['Strong_Draught_of_Healing', 'vk009_apple_isle_draught', 'Apple-Isle Draught', "From Caer Witrin's orchards. Sharp and sweet."],
    ['Strong_Draught_of_Power', 'vk009_marsh_tonic', 'Marsh Tonic', "Bitter. Brec swears it clears the head."],
    ['CombinedRegens_Draught', 'vk009_witrin_cider', 'Witrin Cider', "Caer Witrin's best. Everything comes back faster after a cup."]]}})
print('\n'.join(out))
