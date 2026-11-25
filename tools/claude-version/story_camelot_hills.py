"""Camelot Hills' story quests (claude 2026-11-24, "Albion - the plan" in Zone Reviews) - see story_gen.py. Places: zone metres
[x, y].  python tools/claude-version/story_gen.py story_camelot_hills

Albion's north-west thread begins here, under Camelot's nose: Arthur is gone to Avalon, the Round Table's survivors keep the realm,
and the Crimson - Morgana le Fay's mortal cult - holds its first rite in Mithra's Tomb. The roads are kept busy with bandits the cult
pays, so the Watch looks the other way. At the end a letter in Morgana's hand, addressed to "the Bishop" - Vetusta Abbey, in Black
Mountains South.

The zone's three older quests are kept as they were (by id: tomb_keeps, pilgrims, bell_price).

Arcs (recommended levels; rewards pay at the player's level):
  Cotswold's Troubles (1-5) - the Wardens of Cotswold
  The Camelot Road (4-10) - the Wardens, then the Pendragon's Watch: the Road Gang is paid in red-sealed coin
  After Camlann (8-12) - the Watch: the Difwych brothers, Arthur's huntsmen, still hunting a boar that isn't there
  The Crimson Rite (9-14) - the Watch: Mithra's Tomb (with What the Tomb Keeps and The Pilgrim's Letters)
  The Cracked Door (12-14) - the Watch: demons out of Darkness Falls
"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, '/home/claude/z/geo')
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L, HERE
try:
    import geo
except ImportError:
    geo = None

CRATE, BEDROLL, LANTERN = 1347, 1882, 1876
M, F, OLD = 9, 38, 32
Z = 0
ZONES = []
z = Zone(Z, 'Camelot Hills', 1, 'alb_camelot_hills')
ZONES.append(z)
AT, NAMES = {}, {}


def keep_old():
    """The zone's three older quests, their people and their rewards, as they were."""
    q = json.loads((HERE.parents[1] / 'source/server/GameServer/scripts/storyquests/quests/alb_camelot_hills.json').read_text(encoding='utf-8'))
    spec = json.loads((HERE / 'named_uniques/story000_camelot_hills.json').read_text(encoding='utf-8'))
    old_ids = {'tomb_keeps', 'pilgrims', 'bell_price'}
    for qq in q['quests']:
        if qq['id'] in old_ids:
            for e in qq['endings'].values():
                e['rewards'].setdefault('items', [])
                e['rewards'].setdefault('choice', [])
            z.quests.append(qq)
            z.labels[qq['id']] = {}
    keep_npcs = {n['id'] for n in q['npcs'] if n['id'] in {'maren_hale', 'hob_tanner', 'brother_eadric', 'ysolde_marchant', 'gerrit_woodcutter',
                                                           'elric_home', 'tamsin', 'wren_herald'}}
    for n in q['npcs']:
        if n['id'] in keep_npcs:
            z.npcs.append(n)
            NAMES[n['id']] = n['name']
            AT[n['id']] = tuple(n['pos'][:2])
    old_names = {'Caddoc\'s Lantern Charm', 'Hale Family Signet', "Tombwalker's Girdle", 'Mantle of the Kind Lie',
                 "Weaver's Hopeful Mantle", 'Three-Note Band', 'Waystone Bracer', "Shepherd's Lucky Charm", 'Sheep-Song Sash',
                 "Bell-Wether's Favour"}
    for it in spec['items']:
        if it['name'] in old_names:
            z.items.append(it)


def P(x, y):
    if geo and not geo.dry(Z, x, y, 4):
        n = geo.dry_near(Z, x, y, 60)
        if n:
            return n
    return (x, y)


def person(id, name, xy, kind, level, **kw):
    xy = P(*xy)
    NAMES[id] = name
    AT[id] = tuple(xy)
    z.npc(id, name, list(xy), kind, level, **kw)


def where(to, frm):
    fx, fy = AT[frm]
    dx, dy = to[0] - fx, to[1] - fy
    d = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(-dy, dx)) % 360
    names = ['east', 'north-east', 'north', 'north-west', 'west', 'south-west', 'south', 'south-east']
    dirn = names[int(((ang + 22.5) % 360) // 45)]
    dist = ('%d m' % (round(d / 10) * 10)) if d < 950 else ('%.1f km' % (d / 1000))
    return 'about %s %s of %s' % (dist, dirn, NAMES[frm])


def hunt(xy, goal, target, count=1, text=None, r=50):
    st = {'type': 'kill', 'zone': Z, 'at': list(P(*xy)), 'radius': r, 'goal': goal, 'target': target, 'count': count}
    if text:
        st['text'] = text
    return st


keep_old()

GRAY_WOLF, BLACK_WOLF, SPRITELING, SPRIGGARN, SPRIG_ELDER = 12488, 12137, 12387, 12401, 12226
CUTPURSE, YOUNG_CUT, BANDIT, HENCH, LIEUT, THAUM, LEADER = 12076, 12567, 12447, 12308, 12311, 10108, 12310
ACOLYTE, INITIATE, UFILIDH, ZOMBIE, SKELETON = 12284, 12075, 12620, 12585, 12368
MANES, GRUMOZ, ANT_WORKER, ANT_SOLDIER, ANT_QUEEN = 12370, 12359, 12082, 12339, 12338
GUARD = 12964

# ------------------------------------------------------------------ people
# Cotswold
person('ch_warden_hollis', 'Warden Hollis', (318, 690), 'm', 30, guild='the Wardens of Cotswold',
       idle="Camelot's walls are an hour's walk. You'd think that would keep the trouble off. It doesn't.")
person('ch_goodwife_ada', 'Goodwife Ada', (292, 676), 'f', 18, idle="Three lambs this week. Three. The wolves never came this close when the King was alive.")
person('ch_miller_bran', 'Bran the Miller', (262, 760), 'm', 22, idle="The wheel's stopped. You hear that? Nothing. That's my living, not turning.")
person('ch_reeve_tobias', 'Reeve Tobias', (336, 716), 'm', 26, guild='the Wardens of Cotswold',
       idle="Half the harvest's in, the other half's walking off into the hills on little green legs.")
# Gronyr's Farm and the north road
person('ch_forester_odo', 'Forester Odo', (560, 420), 'm', 30, idle="These were the King's woods. They still are, as far as I'm concerned.")
person('ch_gronyr', 'Gronyr the Farmer', (640, 610), 'm', 28, idle="My grandfather's grandfather ploughed this field. The ants say otherwise.")
# Prydwen Keep (the Pendragon's Watch)
person('ch_captain_bonswell', 'Watch-Captain Elidyr', (642, 1150), 'm', 45, guild="the Pendragon's Watch",
       idle="Every road to Camelot is my road. I'd like them back.")
person('ch_sir_jerem', 'Sir Bedwyr', (628, 1168), 'm', 41, model=254, guild='Knight of the Round Table',
       idle="I sat three places down from Sir Kay. He never let me forget it. Now there's no one to forget it to.")
# the eastern hamlet
person('ch_brother_willem', 'Brother Idris', (990, 808), 'm', 24, guild='the Church of Albion',
       idle="I bless the dead in the barrow fields every Sunday. This year they've started answering.")
person('ch_sage_nelson', 'Sage Tegid', (1004, 798), 'm', 35, idle="Old Rome built that tomb for Mithras. Old Rome didn't build it to be used by these people.")
# the camp below Darkness Falls
person('ch_lady_aelawen', 'Lady Enid', (915, 1262), 'f', 44, guild="the Pendragon's Watch",
       idle="The door to Darkness Falls is held. Mostly. Things get round it.")
person('ch_sir_barcroft', 'Sir Barwick', (906, 1272), 'm', 38, model=28, guild="the Pendragon's Watch",
       idle="Barwick. Not Berwick. I've corrected three demons on it.")

# ======================================================================== Cotswold's Troubles (1-5) - the Wardens of Cotswold
c1 = z.item("Shepherd's Crook-Pin", 'gem', 2, 'charm', "A brass pin shaped like a crook. Ada's late husband wore it.")
c2 = z.item("Fleece-Lined Bracer", 'bracer', 2, 'ward', "Soft inside, tough outside. Cotswold makes them for its own.")
z.quest('ch_wolves_at_the_fold', 'Wolves at the Fold', 2, 'ch_goodwife_ada',
        "Three lambs this week. The grey wolves come down off the downs at dusk and take them right out of the fold, bold as you like.\n\nWarden Hollis says he can't spare a man. Will you [watch the fold] tonight? Thin the pups out on the fields and follow them home.",
        'watch the fold',
        "Grey wolves are taking Goodwife Ada's lambs from the fold outside Cotswold.",
        [
            hunt((440, 720), "Thin out the wolf pups on the fields " + where((440, 720), 'ch_goodwife_ada'), 'gray wolf pup', 6),
            search(Z, P(330, 400), "Follow the tracks north to the wolves' den", "a den under a fallen oak", BEDROLL,
                   "Bones. Lots of them, and fresh. And a tuft of grey fur on the root - the old she-wolf's, by the size of it."),
            boss(Z, P(330, 395), "Drive off the old she-wolf", "The she-wolf drops at the mouth of her den. The downs go quiet.",
                 'Old Greymuzzle', GRAY_WOLF, 4, "A grey wolf as big as a pony comes out of the dark under the oak, and she isn't afraid of you."),
            end_talk('ch_goodwife_ada', "Tell Goodwife Ada", "Old Greymuzzle? She's been the terror of the downs since I was a girl. And you just walked up and... well.\n\nMy husband's pin. He'd want someone brave to have it.", 'default'),
        ],
        {'default': {'text': "From Goodwife Ada.", 'choice': [c1, c2]}})

c3 = z.item("Mill-Wheel Ring", 'ring', 3, 'might', "Forged from a broken pin of Bran's wheel.")
c4 = z.item("River-Reed Sash", 'belt', 3, 'charm', "Woven by the sprites. It smells faintly of the river.")
z.quest('ch_still_wheel', 'The Still Wheel', 3, 'ch_miller_bran',
        "My wheel's stopped. Not broken - stopped. Something's jammed the race, and every time I clear it, it's jammed again by morning.\n\nIt's the sprites. Little blue things from the river, all giggling. Will you [clear the race]? And if you find the pin they stole off the wheel, I'll owe you a sack of flour.",
        'clear the race',
        "River sprites keep jamming Bran the Miller's wheel outside Cotswold.",
        [
            hunt((420, 1080), "Chase the spritelings out of the reeds " + where((420, 1080), 'ch_miller_bran'), 'river spriteling', 6),
            search(Z, P(470, 1210), "Search the sprites' pool down the river", "a pool full of shiny things", CRATE,
                   "Buttons, a spoon, three thimbles - and Bran's iron wheel-pin, polished up like a jewel. Tiny wet footprints lead back upstream.", give="Bran's wheel-pin"),
            hunt((289, 902), "Deal with Thwori, the sprite who leads them, upstream on the west bank", 'Thwori', 1,
                 text="Thwori squeals and splashes away, and the other sprites follow. The race runs clear."),
            end_talk('ch_miller_bran', "Bring the pin back to Bran", "There she goes - hear that? That's the sound of bread.\n\nPolished my pin, did they? Cheeky little beggars.", 'default'),
        ],
        {'default': {'text': "From Bran.", 'choice': [c3, c4]}})

c5 = z.item("Sickle-Hook Belt", 'belt', 4, 'finesse', "A harvester's belt with a hook for the sickle. Tobias insists.")
c6 = z.item("Brownie's Button", 'gem', 4, 'charm', "A wooden button with a face carved on it. It winks sometimes.")
c7 = z.item("Reeve's Tally Ring", 'ring', 4, 'ward', "Notched for every sheaf. Tobias counts everything.")
z.quest('ch_little_green_legs', 'Little Green Legs', 4, 'ch_reeve_tobias',
        "Half the harvest's in and the other half's walking off into the hills. Spriggarns. They come down at night, steal the sheaves and the sickles both, and dance on the stubble.\n\nWill you [find the harvest]? Their rings are in the hills east of here. Bring back what you can - and make them think twice.",
        'find the harvest',
        "Spriggarns are stealing Cotswold's harvest and carrying it off to their rings in the hills.",
        [
            hunt((700, 800), "Teach the spriggarns in the hills a lesson " + where((700, 800), 'ch_reeve_tobias'), 'spriggarn', 6),
            search(Z, P(860, 760), "Search the spriggarn ring for the stolen sickles", "a ring of trampled sheaves", CRATE,
                   "Sickles, a dozen, hung in a circle on a hawthorn like bells - and the sheaves trampled into a dancing floor."),
            choice('ch_reeve_tobias', "Tell Reeve Tobias what you found",
                   "Dancing on it? Our bread? ...Brownies used to leave a sheaf out for the little folk at every harvest. My grandmother did. We stopped when the King died - there didn't seem much to thank anyone for.\n\nDo we [leave a sheaf] out for them again, or [drive them off] for good?",
                   [('leave a sheaf', "A sheaf it is. One, at the edge of the field. And if they take a second, they'll hear from me.", 'ending:gift'),
                    ('drive them off', "Then we'll burn the hawthorn. They'll find somewhere else to dance.", 'ending:drive')]),
        ],
        {'gift': {'text': "The little folk leave something on the doorstep the next morning.", 'items': [c6], 'choice': [c5, c7]},
         'drive': {'text': "From the Wardens.", 'choice': [c5, c7]}},
        requires='ch_still_wheel')

c8 = z.item("Anthill Amber Charm", 'gem', 5, 'mind', "A bead of amber from the dragon ants' mound. There's a tiny ant inside.")
c9 = z.item("Ploughman's Mantle", 'cloak', 5, 'ward', "Heavy brown wool. Gronyr's family has worn it for generations.")
z.quest('ch_ants_in_the_furrow', 'Ants in the Furrow', 5, 'ch_gronyr',
        "Dragon ants. You've seen them? Big as dogs, and they've come over the ridge into my east field. They take the seed straight out of the furrow.\n\nThe workers I can live with. But somewhere up on the ridge there's a queen, and while she's laying there'll be no end of them. Will you [find the queen]?",
        'find the queen',
        "Dragon ants from the eastern ridge are raiding Gronyr's farm.",
        [
            hunt((1050, 560), "Kill the dragon ant workers on the ridge " + where((1050, 560), 'ch_gronyr'), 'dragon ant worker', 8),
            hunt((1180, 520), "Kill the dragon ant queen in her mound", 'dragon ant queen', 1,
                 text="The queen goes down in a heap of legs. Her soldiers mill about, lost."),
            end_talk('ch_gronyr', "Tell Gronyr", "Gone? The queen? ...My grandfather's grandfather would've bought you a drink. I'll buy you two.", 'default'),
        ],
        {'default': {'text': "From Gronyr.", 'choice': [c8, c9]}})

p1 = z.item("Snare-Wire Bracer", 'bracer', 3, 'finesse', "Twisted from the poachers' own wire.")
p2 = z.item("Forester's Acorn", 'gem', 3, 'charm', "A brass acorn. Odo hands them out to anyone who helps.")
z.quest('ch_kings_deer', "The King's Deer", 3, 'ch_forester_odo',
        "The north woods were the King's own hunting. Nobody's said otherwise since he went - so the poachers decided nobody minds.\n\nThey've strung snares from the road to the heath. Will you [cut the snares]? And send the poachers home with a flea in their ear.",
        'cut the snares',
        "Poachers are snaring in the King's woods north of Cotswold.",
        [
            search(Z, P(600, 360), "Cut the poachers' snares by the north road " + where((600, 360), 'ch_forester_odo'), "a wire snare in the bracken", CRATE,
                   "A snare, and another, and another - a dozen in a line. You cut them all."),
            hunt((650, 330), "Drive off the young poachers at their camp", 'young poacher', 4),
            end_talk('ch_forester_odo', "Tell Forester Odo", "Cut, all of them? Good. Arthur's not here to mind his deer. So I mind them.", 'default'),
        ],
        {'default': {'text': "From Forester Odo.", 'choice': [p1, p2]}})

# ======================================================================== The Camelot Road (4-10)
r1 = z.item("Purse-Snatcher's Ring", 'ring', 6, 'finesse', "Taken back from a cutpurse. It's had several owners, none of them honest.")
r2 = z.item("Tithe-Bearer's Belt", 'belt', 6, 'faith', "The tithe purse hung from it all the way to Camelot. Now it's yours.")
z.quest('ch_kings_road', "Cutpurses on the King's Road", 6, 'ch_warden_hollis',
        "The road from here to Camelot used to be the safest in Albion. Now a gang of cutpurses works it - children, half of them, and the other half ought to know better.\n\nLast night they took the parish tithe from Brother Idris's boy. Will you [clear the road]? The gang camps in the hills east of the crossroads.",
        'clear the road',
        "A gang of cutpurses robs travellers on the road to Camelot. They took the parish tithe.",
        [
            hunt((560, 820), "Clear the cutpurses on the Camelot road " + where((560, 820), 'ch_warden_hollis'), 'cutpurse', 5),
            hunt((840, 990), "Break up the gang's camp in the hills", 'young cutpurse', 4),
            boss(Z, P(845, 1000), "Defeat the gang's lieutenant", "The lieutenant falls. In his coat: the tithe purse - and a second purse, full of new silver.",
                 'Hob Crowley', LIEUT, 8, "A broad man with a short sword steps out of the trees. 'That's my road, friend. My road, my tax.'"),
            end_talk('ch_warden_hollis', "Return the tithe to Warden Hollis", "The tithe, thank God. And this other purse... new silver, every coin. Stamped with a red seal I don't know.\n\nCutpurses don't carry new silver. Somebody's paying them.", 'default'),
        ],
        {'default': {'text': "From the Wardens of Cotswold.", 'choice': [r1, r2]}})

r3 = z.item("Red-Seal Signet", 'ring', 8, 'mind', "The red seal, filed flat. It doesn't stain your finger any more. Much.")
r4 = z.item("Thaumaturge's Charm", 'gem', 8, 'mind', "A hedge-wizard's charm. It smells of burnt feathers.")
r5 = z.item("Watchman's Bracer", 'bracer', 8, 'might', "Issued at Prydwen Keep. It's never been polished, which is how you know it's been used.")
z.quest('ch_red_seal', 'The Red Seal', 8, 'ch_captain_bonswell',
        "Hollis sent you with this purse? Good. Look at the seal - a red key under a crown. I've seen it twice: on a dead smuggler, and on a letter I wasn't meant to read.\n\nThe bandits on the eastern ridge have a hedge-wizard with them - a thaumaturge. If anyone keeps their accounts, it's him. Will you [find his accounts]?",
        'find his accounts',
        "Watch-Captain Elidyr of Prydwen Keep thinks the bandits are being paid - in silver stamped with a red seal.",
        [
            hunt((985, 535), "Fight through the bandits on the eastern ridge " + where((985, 535), 'ch_captain_bonswell'), 'bandit', 6),
            boss(Z, P(990, 540), "Defeat the gang's thaumaturge", "The thaumaturge's satchel spills open: a ledger, in a neat hand.",
                 'Hollin the Hexer', THAUM, 9, "A thin man in a feathered cloak shrieks a curse and the air goes sour. 'Nobody reads my books!'"),
            search(Z, P(995, 530), "Read the thaumaturge's ledger", "a ledger in a neat hand", CRATE,
                   "'Paid: to keep the Watch busy on the roads, forty marks. Paid: to keep away from the tomb on the eastern hill, twenty marks. Received of the Crimson, by the hand of the Warden of the Tomb.'",
                   give="the thaumaturge's ledger"),
            end_talk('ch_captain_bonswell', "Bring the ledger to Watch-Captain Elidyr", "'Keep the Watch busy on the roads.' So all this - the cutpurses, the robberies - it's a curtain. And behind it, the old Roman tomb on the eastern hill.\n\nThe Crimson. I don't know the name. I don't like it.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [r3, r4, r5]}},
        requires='ch_kings_road')

r6 = z.item("Old Fort Keystone", 'gem', 10, 'ward', "A chip of the old fort's keystone. Elidyr kept the rest for the new gate.")
r7 = z.item("Red-Handed Gauntlet-Ring", 'ring', 10, 'might', "Gamwell's ring. He earned the name honestly, at least.")
r8 = z.item("Prydwen Cloak", 'cloak', 10, 'ward', "Watch blue, with Arthur's ship Prydwen stitched in silver at the shoulder.")
z.quest('ch_old_fort', 'The Old Fort', 10, 'ch_captain_bonswell',
        "The gang's master has a name now: Gamwell the Red-Handed, and he holds the old fort south of the river. Kill him and the curtain comes down.\n\nHe's no cutpurse - he fought at Camlann, they say, on the wrong side. Will you [take the fort]? Bring friends if you have them. I'll have men on the bridge.",
        'take the fort',
        "Gamwell the Red-Handed, master of the Camelot Road Gang, holds the old fort south of the river.",
        [
            reach(Z, P(760, 1310), "Cross the river south of Prydwen Keep", "The bridge is held by Elidyr's men. Beyond it, on the hill, the old fort's walls - and smoke.", r=25),
            hunt((948, 1420), "Fight into the old fort " + where((948, 1420), 'ch_captain_bonswell'), 'bandit henchman', 4),
            boss(Z, P(950, 1425), "Defeat Gamwell the Red-Handed", "Gamwell goes down on one knee. 'Camlann,' he says, 'was the last honest fight I saw.' Then nothing.",
                 'Gamwell the Red-Handed', LEADER, 11, "A grey-bearded man in old mail draws a sword with a broken crown on the pommel. 'Mordred paid better than Arthur, and so does she.'",
                 adds=[(BANDIT, 'bandit', [9, 10])], every=30, count=2),
            end_talk('ch_captain_bonswell', "Report to Watch-Captain Elidyr", "'So does she.' Not he. She.\n\nThe roads are ours again. And the curtain's down - so now we can see what's behind it on the eastern hill.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'items': [r8], 'choice': [r6, r7]}},
        requires='ch_red_seal')

# ======================================================================== After Camlann (8-12) - the Difwych brothers
a1 = z.item("Huntsman's Horn-Charm", 'gem', 9, 'finesse', "A little horn of yellowed bone. Blow it and dogs prick up their ears a mile off.")
a2 = z.item("Hound-Leash Belt", 'belt', 9, 'might', "Plaited leather, chewed at one end.")
z.quest('ch_arthurs_huntsmen', "Arthur's Huntsmen", 9, 'ch_sir_jerem',
        "You've heard of the hunt for the Twrch Trwyth? The great boar - a king turned into a beast - that Arthur chased from Ireland across all Wales. Three of the huntsmen were brothers: Cilydd, Cyfer and Cyfwlch Difwych. Best hound-men in Albion.\n\nAfter Camlann they didn't come home. They're in the eastern hills, with their hounds, and they kill anyone who comes near. Will you [find the brothers]? I want to know what they've become.",
        'find the brothers',
        "Sir Bedwyr of Prydwen Keep asks you to find the Difwych brothers, Arthur's huntsmen, who went wild after Camlann.",
        [
            hunt((1300, 520), "Kill the Difwych hounds in the eastern hills " + where((1300, 520), 'ch_sir_jerem'), 'hound of the Difwych', 5),
            search(Z, P(1270, 330), "Search the brothers' hunting camp", "a camp of skins and old spears", BEDROLL,
                   "Boar spears, all of them notched with the same mark - a boar's head. A map of Wales scratched on a hide, with a trail across it, and the trail goes round and round."),
            hunt((1283, 749), "Face Cilydd Difwych", 'Cilydd Difwych', 1,
                 text="Cilydd falls. 'The boar,' he says. 'We'll have him at the river. Tell Arthur.'"),
            end_talk('ch_sir_jerem', "Tell Sir Bedwyr", "Still hunting the boar. The Twrch Trwyth went into the sea off Cornwall years ago - Arthur let him go.\n\nThey never heard the hunt was over. No one ever came to tell them.", 'default'),
        ],
        {'default': {'text': "From Sir Bedwyr.", 'choice': [a1, a2]}})

a3 = z.item("Twrch Trwyth Tusk", 'neck', 12, 'might', "A sliver of the great boar's tusk, kept by the Difwych for twenty years.")
a4 = z.item("Round Table Ribbon", 'gem', 12, 'faith', "A strip of blue from Sir Bedwyr's surcoat. He tore it off himself.")
a5 = z.item("Last Hunt Mantle", 'cloak', 12, 'ward', "Boar-hide, trimmed with the brothers' colours.")
z.quest('ch_hunt_never_ended', 'The Hunt That Never Ended', 12, 'ch_sir_jerem',
        "Cyfwlch was the eldest. He had Arthur's horn - the horn that called the hunt in and sent it out. If anyone can still reach them, it's that horn.\n\nTake my word to him: the hunt is over, the King is gone, and the Round Table would have them back. Will you [take the word]? And if he won't hear it... do what you must.",
        'take the word',
        "Sir Bedwyr sends you to Cyfwlch Difwych, eldest of the brothers, with word that the hunt is over.",
        [
            hunt((1325, 550), "Get past Cyfer Difwych", 'Cyfer Difwych', 1, text="Cyfer drops his spear. 'Brother,' he calls. 'Brother, someone's come from Camelot.'"),
            hunt((1251, 314), "Face Cyfwlch Difwych, eldest of the brothers", 'Cyfwlch Difwych', 1,
                 text="Cyfwlch sinks down against a stone, the old horn still on its cord round his neck."),
            choice('ch_sir_jerem', "Tell Sir Bedwyr how it ended",
                   "He wouldn't hear it. No. They never could hear anything but the hunt.\n\nYou have the horn? Then you have a choice. We can [blow the horn] - the old call that brings the hunt home - and let the hills hear it. Or [keep the horn] at Prydwen, and remember them the way they were.",
                   [('blow the horn', "Then blow it. Long and low, the way Cyfwlch did.\n\n...Hear the hounds? They've stopped. All over the hills. They've stopped.", 'ending:home'),
                    ('keep the horn', "Then it goes on the wall above the gate, and every knight who rides out will touch it for luck.", 'ending:wall')]),
        ],
        {'home': {'text': "The hunt is home.", 'items': [a3], 'choice': [a4, a5]},
         'wall': {'text': "From Sir Bedwyr.", 'items': [a4], 'choice': [a3, a5]}},
        requires='ch_arthurs_huntsmen')

# ======================================================================== The Crimson Rite (9-14) - Mithra's Tomb
t1 = z.item("Acolyte's Red Cord", 'belt', 11, 'mind', "A red silk cord, knotted thirteen times. Idris burned the knots out.")
t2 = z.item("Barrow-Blessed Ring", 'ring', 11, 'faith', "Brother Idris blessed it on the barrow fields. It's warm.")
z.quest('ch_red_robes', 'Red Robes on the Hill', 11, 'ch_brother_willem',
        "I bless the dead in the barrow fields every Sunday. This spring, men in red robes started coming out of the old Roman tomb at night, and the dead started getting up.\n\nI'm a priest, not a soldier. Will you [go to the tomb]? See who they are. Sage Tegid might know their sign.",
        'go to the tomb',
        "Men in red robes come out of Mithra's Tomb at night, and the dead of the barrow fields are walking.",
        [
            hunt((1300, 990), "Kill the red-robed acolytes at the tomb mouth " + where((1300, 990), 'ch_brother_willem'), 'crimson acolyte', 5,
                 text="One acolyte carries a knife of black stone with a red-key hilt."),
            talk('ch_sage_nelson', "Show the knife to Sage Tegid",
                 "A red key under a crown. The Crimson. They're old - older than Arthur. They worshipped what lives under the hill, and they called it by a woman's name.\n\nIn my grandmother's day that name was [Morgana].", kw='Morgana'),
            end_talk('ch_brother_willem', "Tell Brother Idris", "Morgana le Fay. The King's own sister. Under Camelot's nose, in a Roman tomb.\n\nGod help us. Well. He has so far.", 'default'),
        ],
        {'default': {'text': "From Brother Idris.", 'choice': [t1, t2]}},
        topics={'morgana': "Arthur's half-sister. A healer once, they say - she was one of the queens who carried him to Avalon. And then something changed."})

t3 = z.item("Rite-Stone Shard", 'gem', 12, 'mind', "A shard of one of the rite stones. It's quiet now.")
t4 = z.item("Gravedigger's Girdle", 'belt', 12, 'ward', "Brother Idris's spare. He's been digging a lot of graves again.")
t5 = z.item("Barrow-Field Bracer", 'bracer', 12, 'might', "Bronze, very old, found in a broken barrow.")
z.quest('ch_dead_wont_lie', "The Dead Won't Lie Still", 12, 'ch_brother_willem',
        "The rite raises them, Tegid says - the dead in the barrows answer the call from the tomb. There are three stones, marked with the red key, set in the barrow fields to carry the call.\n\nWill you [break the stones]? And lay to rest whatever's guarding them.",
        'break the stones',
        "Three rite stones in the barrow fields carry the Crimson's call to the dead. Brother Idris wants them broken.",
        [
            search(Z, P(1000, 1000), "Break the first rite stone " + where((1000, 1000), 'ch_brother_willem'), "a stone marked with a red key", CRATE,
                   "The stone cracks down the middle, and the red key fades like a bruise."),
            hunt((1100, 1150), "Destroy the undead filidh guarding the barrow ring", 'undead filidh', 3),
            search(Z, P(1110, 1160), "Break the second rite stone", "a stone marked with a red key", CRATE,
                   "The second stone breaks. Somewhere under the hill, someone screams in anger."),
            hunt((1255, 1060), "Lay the rotting dead at the rite to rest", 'rotting zombie', 2),
            search(Z, P(1260, 1065), "Break the third rite stone", "a stone marked with a red key", CRATE,
                   "The third stone splits, and every dead thing in the barrow fields falls down where it stands."),
            end_talk('ch_brother_willem', "Tell Brother Idris", "They've lain down. All of them. I'll bury them again on Sunday - properly.\n\nThe rite's broken. Whoever leads it will know.", 'default'),
        ],
        {'default': {'text': "From Brother Idris.", 'choice': [t3, t4, t5]}},
        requires='ch_red_robes')

t6 = z.item("Tomb-Warden's Key", 'neck', 14, 'mind', "An iron key on a chain. It opens nothing any more.")
t7 = z.item("Lady Enid's Favour", 'gem', 14, 'faith', "A blue ribbon, given to those who serve the realm well.")
t8 = z.item("Crimson-Bane Ring", 'ring', 14, 'might', "Cut from the warden's own signet. The red key's been scratched out.")
t9 = z.item("Mithras-Stone Mantle", 'cloak', 14, 'ward', "Dark red, Roman-cut, taken from the tomb. Idris blessed it twice to be sure.")
z.quest('ch_tomb_warden', 'The Tomb-Warden', 14, 'ch_brother_willem',
        "The ledger named him - 'the Warden of the Tomb'. Brother Malgwyn, he calls himself. He was one of ours once, a brother of the Church.\n\nHe'll be at the tomb mouth with his best. You'll want friends. Will you [face the Warden]? Bring me whatever he carries.",
        'face the Warden',
        "Brother Malgwyn, Warden of the Tomb, leads the Crimson's rite at Mithra's Tomb.",
        [
            hunt((1330, 995), "Fight through the crimson initiates at the tomb mouth " + where((1330, 995), 'ch_brother_willem'), 'crimson initiate', 3),
            boss(Z, P(1335, 990), "Defeat Brother Malgwyn, Warden of the Tomb", "Malgwyn falls across the tomb's threshold. A letter, sealed with the red key, slides out of his sleeve.",
                 'Brother Malgwyn', INITIATE, 15, "A man in red robes over a monk's habit stands in the tomb mouth. 'The Lady keeps her promises. Do you know what she promised me? I'll show you.'",
                 adds=[(ACOLYTE, 'crimson acolyte', [12, 13])], every=25, count=2),
            search(Z, P(1338, 985), "Read the letter in Malgwyn's sleeve", "a letter sealed with a red key", CRATE,
                   "'Malgwyn - the Tomb is done with. Go north to the Bishop. The Mountains are ready, and the gate in the lake will open at midsummer. M.' The hand is fine, and the M is drawn like a crown.",
                   give="Morgana's letter"),
            end_talk('ch_lady_aelawen', "Take the letter to Lady Enid at the camp below Darkness Falls",
                     "'Go north to the Bishop.' North of Camelot there is one bishop: Burhoff, of Vetusta Abbey, in the Black Mountains. A holy man, we're told.\n\nAnd 'the gate in the lake'... The Round Table must see this. You've done Albion a service today, whatever comes of it.", 'default'),
        ],
        {'default': {'text': "From Lady Enid, in the Round Table's name.", 'items': [t7], 'choice': [t6, t8, t9]}},
        requires='ch_dead_wont_lie', group=True)

# ======================================================================== The Cracked Door (12-14)
d1 = z.item("Brimstone Charm", 'gem', 13, 'charm', "A lump of yellow stone from Darkness Falls' mouth. It never quite cools.")
d2 = z.item("Barwick's Spare Gauntlet-Ring", 'ring', 13, 'might', "Sir Barwick had it made from his old gauntlet. 'Not Berwick,' it says inside.")
d3 = z.item("Doorward's Belt", 'belt', 13, 'ward', "Worn by those who've held Darkness Falls' door.")
z.quest('ch_cracked_door', 'The Cracked Door', 13, 'ch_sir_barcroft',
        "The door to Darkness Falls is held. The Watch holds it. But it's cracked - demons come out round the edges, little ones at first, and every month bigger ones.\n\nThere's one at the mouth called Fielath. He's learned our names. Will you [hold the door] with us? Kill the manes that come out, and see Fielath off.",
        'hold the door',
        "Demons are getting round the Watch at the mouth of Darkness Falls.",
        [
            hunt((1265, 1340), "Kill the manes demons at Darkness Falls' mouth " + where((1265, 1340), 'ch_sir_barcroft'), 'manes demon', 6),
            hunt((1257, 1315), "See Fielath off", 'Fielath', 1, text="Fielath bursts like a coal in a fire. 'BARCROFT,' it howls as it goes. 'BERWICK!'"),
            end_talk('ch_sir_barcroft', "Tell Sir Barwick", "He called me Berwick? Even dying. Demons.\n\nThe door holds another month. Thank you.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [d1, d2, d3]}})

# ======================================================================== The south bank and the west bank
g1 = z.item("Filidh Song-Torc", 'neck', 10, 'mind', "A thin gold torc. It hums the same three notes, over and over.")
g2 = z.item("Oak-Leaf Mantle", 'cloak', 10, 'faith', "Green wool, stitched with oak leaves. The filidh's colour.")
g3 = z.item("Merlin's Riddle-Ring", 'ring', 10, 'mind', "Engraved inside: 'Where the thorn grows, the threads meet.'")
z.quest('ch_grove_below', 'The Grove Below the River', 10, 'ch_lady_aelawen',
        "There's a grove of filidh on the south bank - the old singers, who kept the songs before the Church came. They kept Merlin's songs too, they say. They've always kept to themselves.\n\nThis spring they've started turning travellers away with spears. Their leader is a woman called Aithne Con. Will you [go to the grove]? I'd rather know why than fight them.",
        'go to the grove',
        "The filidh of the south bank have turned hostile. Lady Enid wants to know why.",
        [
            hunt((850, 1500), "Get past the filidh on the paths " + where((850, 1500), 'ch_lady_aelawen'), 'filidh', 4),
            hunt((733, 1514), "Face Aithne Con, who leads the grove", 'Aithne Con', 1,
                 text="Aithne Con lowers her staff. 'We sing what Merlin sang: when the King sleeps, the Lady wakes. She has woken. We will not let her singers through our grove.'"),
            choice('ch_lady_aelawen', "Tell Lady Enid what Aithne said",
                   "'When the King sleeps, the Lady wakes.' Morgana again. So the filidh aren't our enemies - they're guarding their grove against the Crimson.\n\nShall I [send them word] that the Watch stands with them? Or do we [leave them be]? They have no love for Camelot.",
                   [('send them word', "Then I'll send a knight with bread and no spears. Merlin's riddle came back with her answer: 'Where the thorn grows, the threads meet.' Campacorentin has a thorn.", 'ending:allies'),
                    ('leave them be', "Then they hold their grove and we hold our roads, and neither of us lets the Crimson pass.", 'ending:apart')]),
        ],
        {'allies': {'text': "The filidh send a gift.", 'items': [g3], 'choice': [g1, g2]},
         'apart': {'text': "From Lady Enid.", 'choice': [g1, g2, g3]}})

k1 = z.item("Cronker's Knuckle", 'gem', 13, 'might', "Big as your fist. Hollis wanted it as proof.")
k2 = z.item("Bridge-Toll Belt", 'belt', 13, 'ward', "Hung with the coins Cronker took from travellers. Hollis returned the rest.")
z.quest('ch_cronker', 'Cronker of the West Bank', 13, 'ch_warden_hollis',
        "There's something on the west bank the cutpurses won't go near - a great brute the farmers call Cronker. It's been there longer than the Wardens have, and it's always kept to the river.\n\nNow it's coming up into the fields at night. Will you [hunt Cronker]? Take friends. It doesn't go down easy.",
        'hunt Cronker',
        "The brute called Cronker has started coming up from the west bank into Cotswold's fields.",
        [
            reach(Z, P(330, 1060), "Find Cronker's trail on the west bank " + where((330, 1060), 'ch_warden_hollis'), "Prints the size of millstones, going south along the bank.", r=30),
            hunt((320, 1100), "Kill Cronker", 'Cronker', 1, text="Cronker crashes down in the shallows, and the river runs brown for an hour."),
            end_talk('ch_warden_hollis', "Tell Warden Hollis", "Cronker. Dead. My father wouldn't believe it.\n\nThe Wardens owe you, friend. More than once now.", 'default'),
        ],
        {'default': {'text': "From the Wardens of Cotswold.", 'choice': [k1, k2]}}, group=True)
