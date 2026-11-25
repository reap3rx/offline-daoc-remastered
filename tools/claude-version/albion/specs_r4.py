"""Round 4's other item specs (claude 2026-11-24): reputation stock (rep004, rep007), the new events' bosses (nu004, nu007), and
the two campaigns' camps and raid drops (lb007: the Lake Host's quartermaster and Morgana's raid; dm004: the Dragon-Watch's
quartermaster and the Giants' Throne)."""
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
r = Spec(7, 'Llyn Barfog', 'rep007')
r.item("Lake-Friend's Ring", 'ring', 45, 'might', "Silver, with a wave.")
r.item("Shore-Knight's Belt", 'belt', 45, 'ward', "Blue leather, white-stitched.")
r.item("Knight of the Lake's Torc", 'neck', 50, 'might', "A sword rising out of water, in silver.")
r.item("Mantle of the Lady's Champion", 'cloak', 55, 'ward', "White and lake-blue. Only the Lady's Champions wear it.")
r.item("Maiden-Friend's Charm", 'gem', 45, 'faith', "A drop of lake-water in glass.")
r.item("White-Cattle Bracer", 'bracer', 50, 'faith', "Soft white hide, freely given.")
r.item("Lady's Ring", 'ring', 50, 'charm', "Cold silver. It's always a little wet.")
r.item("Mantle of the Lake's Daughter", 'cloak', 55, 'faith', "Green and silver. Only the Lake's Daughters wear it.")
out += r.write_spec('rep007_llyn_barfog.json')
r = Spec(4, 'Dartmoor', 'rep004')
r.item("Watch-Friend's Ring", 'ring', 50, 'might', "Iron, with a red dragon struck through.")
r.item("Slayer's Road Belt", 'belt', 50, 'ward', "Scorched leather.")
r.item("Dragon-Watch Torc", 'neck', 55, 'might', "Iron and red enamel.")
r.item("Mantle of the Dragon's Bane", 'cloak', 60, 'ward', "Red, scorched at the hem on purpose. Only the Dragon's Banes wear it.")
r.item("Oath-Friend's Stone", 'gem', 50, 'faith', "A chip of Grimspound granite with the quarry-mark.")
r.item("Quarry-Cut Bracer", 'bracer', 55, 'ward', "Granite plates on leather. Heavy, and worth it.")
r.item("Stonewright's Ring", 'ring', 55, 'mind', "A mason's ring, cut from a single stone.")
r.item("Mantle of the Oath-Keeper", 'cloak', 60, 'faith', "Grey wool with the quarry-mark in red. Only Grimspound's Oath-Keepers wear it.")
out += r.write_spec('rep004_dartmoor.json')

e = Spec(7, 'Llyn Barfog', 'nu007')
e.item("Camlann Shade's Gorget", 'neck', 51, 'ward', "Black mail, cold, still dented where a sword went through.")
out += e.write_spec('ev007_llyn_barfog.json')
e = Spec(4, 'Dartmoor', 'nu004')
e.item("Ember-Keeper's Coal", 'gem', 57, 'might', "A coal from Gurt's back. It never quite goes out.")
out += e.write_spec('ev004_dartmoor.json')

g = Spec(7, 'Llyn Barfog', 'lb007')
for n, s, l, k, lore in [
        ("Mantle of the Lake Host", 'cloak', 52, 'ward', "Lake-blue with a white border. Given to those who marched with the Lake Host."),
        ("Gate-Warden's Torc", 'neck', 52, 'might', "Silver, with a shut gate."),
        ("Girdle of the Bearded Lake", 'belt', 52, 'finesse', "Woven of lake-reed and silver wire."),
        ("Ring of the Shut Gate", 'ring', 52, 'mind', "A black ring, closed by a silver bar."),
        ("Afanc-Hide Bracer", 'bracer', 52, 'ward', "Thick grey hide from the beast Arthur killed - twice, now."),
        ("Tear of the Lady", 'gem', 52, 'faith', "A drop of the lake that never dries."),
        ("Morgana's Black Crown", 'neck', 55, 'mind', "A circlet of black iron. It whispers about doors."),
        ("Mordred's Wrath", 'bracer', 55, 'might', "Black mail from Camlann, still cold."),
        ("Afanc-Tooth Charm", 'gem', 55, 'finesse', "A tooth as long as a dagger.")]:
    g.item(n, s, l, k, lore)
out += g.write_spec('lb007_llyn_barfog.json')
g = Spec(4, 'Dartmoor', 'dm004')
for n, s, l, k, lore in [
        ("Mantle of the Dragon-Watch", 'cloak', 56, 'ward', "Red, with a white dragon struck through. Given to those who marched with the Watch."),
        ("Throne-Breaker's Torc", 'neck', 56, 'might', "Granite and iron, from the throne-step."),
        ("Giant's Girdle", 'belt', 56, 'might', "A giant's bracelet, worn as a belt."),
        ("Ring of Grimspound", 'ring', 56, 'faith', "The quarry-mark, in silver."),
        ("Granite Bracer", 'bracer', 56, 'ward', "Cut from the Giants' Throne itself."),
        ("Dragon's-Eye Jewel", 'gem', 56, 'mind', "Yellow and slit-pupilled. It blinks."),
        ("Cormoran's Crown-Shard", 'gem', 60, 'might', "Half of a granite crown. Heavy as guilt."),
        ("Throne-Step Mantle", 'cloak', 60, 'ward', "Grey as the throne-step, and as hard.")]:
    g.item(n, s, l, k, lore)
out += g.write_spec('dm004_dartmoor.json')
print('\n'.join(out))
