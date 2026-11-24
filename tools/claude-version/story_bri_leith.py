"""The Valley of Bri Leith's story quests (claude 2026-11-23, the zone brief in Zone Reviews) - see story_gen.py. Places: zone
metres [x, y].

Moved out of story_hib.py with the zone's rebuild, like Lough Derg, Connacht and Silvermine:
    python tools/claude-version/story_gen.py story_bri_leith

Six arcs and a first walk, 27 quests, one thread: Fuamnach has come back. A girl in Brynach - Aideen, which is Etain's own
name - dreams every night of a hall under a hill: Etain, born again. Fuamnach's wind is rising off the Empyrean Heights to blow
her away a second time; the empyreans have turned and hold Keeper Rasa in her own hut; Riocard, a renegade druid, plays the
part the druid Bresal played in the old tale, paid in ore the siog carry off from the Coruscating Mine; and Midir's host rides
out searching for the woman it lost. And the wind blows out of the Cursed Forest: the Faerie Queen's court there promised
Fuamnach her revenge (owner 2026-11-23: "some tie ins with the Empyreans and what's happening in the Cursed Forest", "tie in
some of the Fae threats from other zones" - the Queen's fool is Connacht's Amadan). Two old quests are folded in: Beyond the
Veil (veil) and The Oak-Heart (oak_heart). The Rangers of Druim Cain's arcs: The Miners' Camp, The Collory Road. Muintir
Etaine's: The Oak-Heart, Beyond the Veil, The Girl Who Dreams of a Hall, Fuamnach's Wind.
"""
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE = 1882, 1876, 1347
M, F, OLD = 337, 365, 362
LURI = 318
Z = 206
ZONES = []

z = Zone(Z, 'Valley of Bri Leith', 3, 'hib_bri_leith')
ZONES.append(z)


def hunt(at, goal, target, count, text=None, give=None):
    """A kill step on the zone's own monsters (they scale to you)."""
    s = {'type': 'kill', 'zone': Z, 'at': list(at), 'radius': 40, 'goal': goal, 'target': target, 'count': count}
    if text:
        s['text'] = text
    if give:
        s['give'] = {'name': give}
    return s


def wake(ending, chain):
    ending['wake_event'] = chain
    return ending


# ------------------------------------------------------------------ people
# Brynach (the Wild start)
z.npc('bl_maelan', 'Herder-Chief Maelan', [628, 1098], 'm', 24, guild='Brynach',
      idle="Brynach's been a herders' town since before there were kings. We know the host rides. We just keep the cows in.")
z.npc('bl_fiona', 'Roadwarden Fiona', [600, 1120], 'f', 26, guild='Rangers of Druim Cain',
      idle="The road from Lough Derg to Druim Cain is mine to keep. Lately it's keeping me.")
z.npc('bl_nessa', 'Nessa the Weaver', [612, 1125], 'f', 18, idle="Aideen's sixteen and dreams of a golden hall every night. I wish she'd dream of weaving.")
z.npc('bl_aideen', 'Aideen', [615, 1132], 'f', 14, idle="Do you ever dream of a place so clearly you could find your way round it awake?")
# Caille
z.npc('bl_sarnat', 'Sarnat of Caille', [912, 818], 'f', 34, guild='Muintir Etaine',
      idle="Caille has kept the bargain with the hill for a thousand years. We don't break it. We don't let it be broken.")
# Druim Cain
z.npc('bl_fearghal', 'Ranger-Commander Fearghal', [892, 100], 'm', 36, guild='Rangers of Druim Cain',
      idle="Druim Cain holds the frontier. The Rangers hold everything between it and Lough Derg. Mostly.")
z.npc('muirenn', 'Grandmother Muirenn', [905, 95], 'f', 14, model=OLD, idle="Rian went through the veil at Samhain. He was ten. He's still ten, there.")
z.npc('druid_ennis', 'Druid Ennis', [918, 82], 'm', 30, model=OLD, idle="The grove's oaks are dying. Their heart was stolen.")
# out in the valley - givers met as you explore (owner 2026-11-23: quests "scattered throughout the zone")
z.npc('bl_brogan', 'Brogan the Miner', [430, 240], 'm', 14, model=LURI, guild='Coruscating Mine',
      idle="Forty years I dug that mine. Forty days the siog have had it. They don't even dig properly.")
z.npc('bl_tuathal', 'Herder Tuathal', [560, 1300], 'm', 20, idle="Don't graze the south pasture after dusk. That's not a rule. That's advice from a man with nine fewer cows.")
z.npc('bl_caoimhe', 'Fisher Caoimhe', [1080, 1350], 'f', 22, idle="The fish in Moon Lake come up to look at the moon. So do other things.")
z.npc('bl_maudalin', 'Watch-Sergeant Maudalin', [140, 1300], 'f', 28, guild='Rangers of Druim Cain',
      idle="Giolladhe's Tower watches the west road. The west road watches back.")
z.npc('bl_rasa', 'Keeper Rasa', [1281, 357], 'f', 34, guild='Keeper of the Heights',
      idle="I kept the empyreans for forty years. They were the sky's own children. Then the wind changed.")
z.npc('bl_fionnuala', 'Ranger-Scout Fionnuala', [1420, 1000], 'f', 30, guild='Rangers of Druim Cain',
      idle="Past those stones is the Cursed Forest. I've been in. Once. I don't talk about it.")
z.npc('rian', 'Rian', [266, 946], 'm', 10, size=40, during=['veil/rian'])
z.npc('aoibheann', 'Aoibheann', [448, 450], 'f', 24, during=['oak_heart/aoibheann'])

# ======================================================================== a first walk (the Wild start in Brynach)
z.quest('bl_road_to_caille', 'The Road to Caille', 1, 'bl_maelan',
        "New to Brynach? Welcome. We're herders - cows, sheep, the odd fairy horse when it wanders in.\n\nCaille, up the road north-east, is where the valley's business gets done. Will you [take the wool] to Sarnat there? She'll pay you, and she'll tell you what's what in Bri Leith. Keep to the road. If you hear hooves after dark, get off it.",
        'take the wool',
        "Herder-Chief Maelan in Brynach has wool for Sarnat in Caille, up the road.",
        [
            end_talk('bl_sarnat', "Take Maelan's wool to Sarnat of Caille, about 420 m north-east of Brynach up the road", "Brynach wool! Maelan's the only one who still sends it carded.\n\nYou walked up from Brynach? Then you've seen the valley's easy half. Look around Caille - and out in the valley. There's work everywhere, and most of it has hooves or wings.", 'default'),
        ],
        {'default': {'text': "Here - for the walk.", 'choice': []}})

# ======================================================================== The Miners' Camp (12 to 18) - Rangers
a1 = z.item("Brogan's Pick-Charm", 'gem', 12, 'might', "A tiny silver pick on a thong. Every lurikeen miner wears one. Brogan had a spare.")
a2 = z.item("Ore-Cart Bracer", 'bracer', 12, 'ward', "Cart iron, bent round a wrist. It has pushed a lot of ore.")
z.quest('bl_brogans_tools', "Brogan's Tools", 12, 'bl_brogan',
        "The siog took our camp at the Coruscating Mine, west of here. They're carting the ore off - and my tools with it, the thieving little louts.\n\nWill you [get my tools back]? They'll be in the carts by the camp. Knock a few footpads over while you're there.",
        'get my tools back',
        "The siog took the lurikeen miners' camp at the Coruscating Mine. Brogan wants his tools back.",
        [
            hunt([190, 230], "Kill 5 siog footpads round the ore carts, about 240 m west of Brogan", 'siog footpad', 5),
            search(Z, [195, 235], "Search the ore carts (click the glinting spot)", "Brogan's tool-roll", CRATE,
                   "Brogan's tools, rolled in oilcloth. Under them, a lump of the mine's ore - and scratched into it, a little sign like a twist of wind. Not siog work.",
                   give="Brogan's tool-roll"),
            end_talk('bl_brogan', "Bring the tools to Brogan the Miner", "My tools! And - what's this on the ore? That's no mark of ours. Somebody's marking the ore for themselves.\n\nThe siog don't keep anything. They sell it. Somebody is buying our mine one cart at a time.", 'default'),
        ],
        {'default': {'text': "From the Coruscating Mine, with thanks.", 'choice': [a1, a2]}})

a3 = z.item('Glamour-Ring of the Siog', 'ring', 14, 'charm', "Cucugar's glamour-ring, its spell broken. It still makes your fingers itch.")
a4 = z.item("Lamp-Bearer's Belt", 'belt', 14, 'finesse', "A miner's lamp-belt. The lamp is long gone. The belt is very good.")
z.quest('bl_glamoured_miner', 'The Glamoured Miner', 14, 'bl_brogan',
        "Cucugar - my partner - is still up at the mine. Working for them. Digging for the siog with a glazed look and a ring on his finger I've never seen before.\n\nThat's glamour. Will you [bring Cucugar back]? Knock the pillers off him first. Then knock some sense into him. Gently.",
        'bring Cucugar back',
        "Brogan's partner Cucugar digs for the siog under a glamour.",
        [
            hunt([300, 175], "Kill 4 siog pillers at the mine mouth, about 150 m north-west of Brogan", 'siog piller', 4),
            hunt([218, 262], "Subdue Miner Cucugar near the siog camp", 'Miner Cucugar', 1, give="Cucugar's glamour-ring",
                 text="Cucugar sits down hard. The ring slides off his finger and the glaze goes out of his eyes. 'Brogan? Is it Tuesday? Why am I so TIRED?'"),
            end_talk('bl_brogan', "Bring Cucugar's ring to Brogan", "He's sleeping it off in my tent, the great lump. Thank you.\n\nThat ring isn't siog-made. Siog can't do glamours that strong. Somebody gave it to them.", 'default'),
        ],
        {'default': {'text': "Take this, from both of us.", 'choice': [a3, a4]}},
        requires='bl_brogans_tools')

a5 = z.item("Fence's Tally-Stick Charm", 'gem', 16, 'mind', "A siog fence's tally-stick: ore in, silver out. The last notch is very deep.")
a6 = z.item('Ranger-Issue Ring', 'ring', 16, 'might', "A plain ring, issued at Druim Cain to rangers who bring in good word.")
a7 = z.item("Camp-Stalker's Sash", 'belt', 16, 'finesse', "Dark green, for creeping round a siog camp at night.")
z.quest('bl_ore_paid', 'Where the Ore Goes', 16, 'bl_brogan',
        "The siog have a fence at their camp - a big one, with a ledger. If anyone knows who's buying our ore, it's him.\n\nWill you [find the buyer]? The Rangers at Druim Cain will want to know too. Commander Fearghal's been asking.",
        'find the buyer',
        "A siog fence at the camp below the mine knows who buys the stolen ore.",
        [
            hunt([250, 300], "Defeat the siog fence at the siog camp, about 190 m south-west of Brogan", 'siog fence', 1),
            search(Z, [255, 305], "Search the fence's ledger at the siog camp (click the glinting spot)", "the fence's ledger", CRATE,
                   "In a careful siog hand: 'Ore, twelve carts - to the druid at the stones, for wind-charms. Paid in charms.' The stones: the Druid Circle, east of here.",
                   give="the fence's ledger"),
            reach(Z, [400, 400], "Go and look at the Druid Circle from its edge, about 200 m south-east of the siog camp", "Stones on a hill, and druids among them in cloaks of black feathers - and an ore cart, half-unloaded, at the foot of the circle.", r=25),
            end_talk('bl_fearghal', "Take the ledger to Ranger-Commander Fearghal at Druim Cain", "Druids buying stolen ore for wind-charms. Wind-charms! In a valley where the wind's been wrong all year.\n\nThe Muintir in Caille will want this as much as I do. Good work. The Rangers won't forget it.", 'default'),
        ],
        {'default': {'text': "From the Rangers.", 'choice': [a5, a6, a7]}},
        requires='bl_glamoured_miner')

a8 = z.item("Sloithi's Ore-Crown", 'neck', 18, 'might', "A crown of raw ore the siog chief wore. It weighs about as much as a goat.")
a9 = z.item('Mine-Mouth Bracer', 'bracer', 18, 'ward', "Iron from the mine's own gate.")
a10 = z.item('Deep-Seam Ring', 'ring', 18, 'faith', "Silver from the deepest seam, where the lurikeen say the hill sings.")
z.quest('bl_sloithi', 'Sloithi', 18, 'bl_brogan',
        "The siog have a chief - Sloithi - squatting in our camp like it's his. While he's there the camp is theirs.\n\nWill you [throw Sloithi out]? Then I can decide whether we dig again or leave it be.",
        'throw Sloithi out',
        "Sloithi, the siog chief, holds the miners' camp.",
        [
            hunt([261, 310], "Defeat Sloithi at the siog camp", 'Sloithi', 1,
                 text="Sloithi falls among his stolen pots. In his fist, a wind-charm - a twist of yew and scarlet thread - still humming."),
            choice('bl_brogan', "Return to Brogan the Miner",
                   "Sloithi's out. Thank you.\n\nWe can [dig again] - the mine's rich, and the Rangers have promised a guard. Or we [let it rest]. The hill's been singing at night since the siog came. My granny would've said that's the hill telling us to stop.",
                   [('dig again', "Dig again, then. Picks up, lads! And somebody keep an eye on the hill.", 'ending:dig'),
                    ('let it rest', "Rest, then. We'll go and dig in Lough Derg like ordinary people. Bah.", 'ending:rest')]),
        ],
        {'dig': {'text': "From the Coruscating Mine - the first ore of the new seam.", 'choice': [a8, a9, a10]},
         'rest': {'text': "From the Coruscating Mine, closed with thanks.", 'choice': [a8, a9, a10]}},
        requires='bl_ore_paid')

# ======================================================================== The Oak-Heart (14 to 20) - Muintir
b1 = z.item('Dying-Oak Leaf Charm', 'gem', 14, 'faith', "An oak leaf from the grove, gone brown in midsummer.")
b2 = z.item("Grove-Watcher's Ring", 'ring', 14, 'mind', "A ring of plaited oak root.")
z.quest('bl_dying_grove', 'The Dying Grove', 14, 'druid_ennis',
        "Our sacred grove in the western woods is dying. In midsummer, the leaves brown and the bark weeps.\n\nGo and look at the [heart-hollow] in the old oak. Something's wrong there, and my legs won't carry me down that far any more.",
        'heart-hollow',
        "Druid Ennis's sacred grove in the western woods is dying in midsummer.",
        [
            reach(Z, [180, 760], "Go to the sacred grove in the western woods, about 1 km south-west of Druim Cain", "Old oaks, brown in midsummer. The grass round them is grey. Moss sheeries pick at the roots.", r=25),
            hunt([180, 760], "Drive off 5 moss sheeries gnawing the grove's roots", 'moss sheerie', 5),
            search(Z, [185, 765], "Search the heart-hollow of the oldest oak (click the glinting spot)", "the empty heart-hollow", CRATE,
                   "The hollow where the oak-heart lay is empty. Little three-toed prints all round it - siog - and a smell of black feathers."),
            end_talk('druid_ennis', "Return to Druid Ennis at Druim Cain", "Empty. Gods. The oak-heart is gone.\n\nSiog prints and black feathers. The siog steal. Druids in black feathers... I know who wears black feathers. I'll have to ask you to go after it.", 'default'),
        ],
        {'default': {'text': "From the grove, while it lives.", 'choice': [b1, b2]}})

it_acorn = z.item('Oak-Heart Acorn', 'gem', 18, 'faith', "A golden acorn from the heart of a sacred grove. It's warm, like something sleeping.")
it_siog = z.item("Siog Thief's Ring", 'ring', 18, 'finesse', "The siog steal everything that isn't nailed down. This ring was stolen eleven times.")
it_druid = z.item('Renegade Druid Torc', 'neck', 18, 'mind', "A druid's torc, from a druid who forgot what druids are for.")
it_grove = z.item("Grove-Keeper's Mantle", 'cloak', 18, 'ward', "Green and brown, the colours of a grove that lives.")
z.quest('oak_heart', 'The Oak-Heart', 18, 'druid_ennis',
        "The grove's oak-heart has been stolen - a golden acorn that holds the life of every oak in our sacred grove. Without it they'll die by midwinter.\n\nThe siog took it. Siog take everything. But siog don't keep things - they sell them. Find their camp below the Coruscating Mine and you'll find who they sold it to. Will you [find the oak-heart]?",
        'find the oak-heart',
        "The siog stole the golden oak-heart that keeps a sacred grove alive, and sold it on.",
        [
            reach(Z, [250, 300], "Find the siog camp below the Coruscating Mine, about 700 m south-west of Druim Cain", "A camp of stolen things - pots, boots, a church bell, a chicken. Siog everywhere, counting.", r=20),
            hunt([250, 300], "Fight through 5 siog footpads at the camp", 'siog footpad', 5),
            search(Z, [245, 295], "Search the siog's stolen goods (click the glinting spot)", "a ledger of stolen things", CRATE,
                   "In a careful siog hand: 'One golden acorn. Sold to the druids at the stones. Paid: two wind-charms, one goat.' The stones - the Druid Circle, east.",
                   give='the siog ledger'),
            hunt([450, 420], "Fight 4 renegade druids at the Druid Circle", 'renegade druid', 4),
            boss(Z, [445, 440], 'Defeat the renegade archdruid', "The archdruid falls. A young druid in green kneels by the stones, holding the golden acorn, weeping.",
                 'Archdruid Ruadh', 10120, 22, "A druid in a cloak of black feathers raises a staff of thorn. 'The grove is ours to move. Ennis is old and blind - and Riocard pays better.'",
                 objective='Defeat Archdruid Ruadh', hp=2.4, adds=[(10120, 'renegade druid', [20, 21])], every=25, count=2),
            L('aoibheann', talk('aoibheann', 'Talk to the young druid', "I'm Aoibheann. Ennis' apprentice. I - I helped them. I told them where the oak-heart was kept.\n\nRuadh said the old grove was dying anyway and we could plant a new one, away from the keeps and the wars. Riocard promised. I believed them. Take it. Take it back to Ennis. And tell him I'm [sorry].", kw='sorry', give='the oak-heart')),
            choice('druid_ennis', 'Return the oak-heart to Druid Ennis',
                   "The oak-heart! The grove will live!\n\n...Aoibheann. My Aoibheann helped them.\n\nThe druids' law says an apprentice who betrays the grove is [turned out] - cast from the order, forever. Or I could [spare her], and take her back, and watch her every day. She was the best apprentice I ever had. That's why it hurts.",
                   [('spare her', "Then she'll come home, and plant the oak-heart with her own hands, and tend the grove until it forgives her. And I'll forgive her sooner.", 'ending:spared'),
                    ('turned out', "...Then she's no druid. I'll tell her myself. It's the law, and the law is older than my heart.", 'ending:turned_out')]),
        ],
        {'spared': {'text': "Take this, from the grove.", 'items': [it_grove], 'choice': [it_siog, it_druid]},
         'turned_out': {'text': "Take this, from the grove.", 'tragic': True, 'items': [it_acorn], 'choice': [it_siog, it_druid]}},
        requires='bl_dying_grove')

b3 = z.item('Replanted-Oak Bracer', 'bracer', 19, 'ward', "Oak bark, freshly grown. It smells of rain.")
b4 = z.item("Thorn-Hound's Collar Ring", 'ring', 19, 'might', "Cut from a thorn-bound hound's collar. The thorns are dead now.")
z.quest('bl_replanting', 'The Replanting', 19, 'druid_ennis',
        "The oak-heart must go back into the old oak tonight, with a druid singing over it. Riocard's thorn-hounds will smell it.\n\nWill you [guard the planting]? Whoever sings it - Aoibheann or me - needs someone between them and the teeth.",
        'guard the planting',
        "The oak-heart goes back into the sacred grove, and Riocard's thorn-hounds will come for it.",
        [
            defend(Z, [182, 762], "Guard the planting in the sacred grove", "The singing ends. The oak sighs - you hear it - and a green flush runs up its bark into the brown leaves.",
                   'the grove-singer', 60163820, 18, "The singer kneels at the old oak and begins. Out of the woods come thorn-bound hounds, baying.",
                   [(60162144, 'thorn-bound hound', [17, 18])], 'Keep the grove-singer safe', model=F, duration=90, every=25, count=2),
            end_talk('druid_ennis', "Return to Druid Ennis at Druim Cain", "I felt it from here. The grove breathed.\n\nThank you. Now - Riocard. A druid of the stones, paying siog in wind-charms. There's something under this, and it's cold.", 'default'),
        ],
        {'default': {'text': "From the grove, alive again.", 'choice': [b3, b4]}},
        requires='oak_heart')

b5 = z.item("Ruadh's Black-Feather Cloak", 'cloak', 20, 'mind', "Black feathers, every one from a crow that was paid to give it.")
b6 = z.item('Wind-Charm Pendant', 'neck', 20, 'charm', "A broken wind-charm, yew and scarlet thread. It doesn't hum any more.")
b7 = z.item("Caille Courier's Belt", 'belt', 20, 'finesse', "The Muintir's couriers wear these between Caille and the hill.")
z.quest('bl_ruadhs_letters', "Ruadh's Letters", 20, 'druid_ennis',
        "Ruadh kept a satchel. If he wrote to Riocard, the letters will be at the Circle still.\n\nWill you [fetch the satchel]? Then take what you find to Sarnat in Caille. If this is what I think it is, it's the Muintir's business more than mine.",
        'fetch the satchel',
        "Archdruid Ruadh's satchel, left at the Druid Circle, may say what Riocard wants.",
        [
            hunt([450, 420], "Kill 4 renegade druids at the Druid Circle", 'renegade druid', 4),
            search(Z, [440, 430], "Search for Ruadh's satchel at the Druid Circle (click the glinting spot)", "Ruadh's satchel", CRATE,
                   "Letters, in Riocard's hand: 'The Lady of the Wind will have her rival. The ore buys the charms; the charms raise the wind; the wind finds the girl. The Queen in the forest keeps her word.' Signed with a twist of wind.",
                   give="Ruadh's letters"),
            end_talk('bl_sarnat', "Take Ruadh's letters to Sarnat of Caille", "'The Lady of the Wind will have her rival.'\n\nGods. Fuamnach. Midir's first wife - the one who turned Etain into a fly and blew her across Ireland. And 'the girl'.\n\nIf Fuamnach has woken, then somewhere in this valley Etain has been born again. And the Queen in the Cursed Forest is helping her. Thank you. I have a great deal to do.", 'default'),
        ],
        {'default': {'text': "From the Muintir, with my thanks.", 'choice': [b5, b6, b7]}},
        requires='bl_replanting')

# ======================================================================== Beyond the Veil (16 to 24) - Muintir
it_veil = z.item('Veil-Thread Bracelet', 'bracer', 16, 'mind', "A thread from the veil between worlds. It's very hard to see.")
it_fruit = z.item("Otherworld Apple Charm", 'gem', 16, 'charm', "An apple from beyond the veil, cast in gold. Don't eat it. It's gold.")
it_seven = z.item('Seven-Year Ring', 'ring', 16, 'ward', "Rian's ring. It fit him when he was ten.")
it_wisp = z.item('Wisp-Light Cloak', 'cloak', 16, 'finesse', "It glimmers faintly, like a veil wisp at the edge of sight.")
z.quest('veil', 'Beyond the Veil', 16, 'muirenn',
        "My grandson Rian went through the veil at Samhain. The veil wisps lit the way and he followed them into the Otherworld, laughing.\n\nIt's thin there still, in the west of the valley. The druids say a strong arm could reach through and pull him back. Will you [bring Rian home]? He's ten. He's always been ten, there.",
        'bring Rian home',
        "Grandmother Muirenn's grandson followed the veil wisps into the Otherworld at Samhain.",
        [
            reach(Z, [380, 920], "Go to the thin place in the west of the valley, about 940 m south-west of Druim Cain", "Lights drift through the air - veil wisps - and between them, now and then, a glimpse of somewhere else: golden, endless, singing.", r=20),
            hunt([380, 920], "Scatter 5 veil wisps at the thin place", 'veil wisp', 5,
                 text="As they go out, the glimpses of the Otherworld get clearer."),
            search(Z, [360, 930], 'Search the edge of the veil (click the glinting spot)', "a small boy's shoe", CRATE,
                   "Rian's shoe. Half of it is here, and half of it is somewhere else, and it is very hard to look at."),
            hunt([380, 920], "Break 2 empyrean orbs that hold the veil open", 'empyrean orb', 2),
            boss(Z, [270, 950], 'Defeat the Keeper of the Veil', "The keeper unravels into light. The veil tears open for a moment, and a small boy tumbles out of it into the grass.",
                 'Keeper of the Veil', 60160478, 16, "A tall shape of pale light stands between you and the gap. 'What passes the veil stays. That is the rule.'",
                 objective='Defeat the Keeper of the Veil', hp=2.2, adds=[(60167560, 'veil wisp', [11, 12])], every=30, count=1),
            L('rian', talk('rian', 'Talk to Rian', "Is it time to go home? I was only gone a day. Wasn't I?\n\nI ate some apples. They were very good. The lady said if I ate them I'd have to [stay], but I could visit. And the riders kept asking me if I'd seen a lady with red hair. I hadn't.", kw='stay')),
            choice('muirenn', 'Bring Rian home to Muirenn at Druim Cain',
                   "Rian! Rian - you're - oh.\n\nHe's ten. Still ten. And he ate their fruit. The druids say if he crosses back for good, every year he spent there catches up with him by morning. He'll wake up seventeen. His childhood gone in a night.\n\nOr he can [go back], and stay ten forever, and visit me at Samhain. I can't choose. [Bring him back], or let him go.",
                   [('bring him back', "Then he'll be seventeen tomorrow. And he'll be here. I'll teach him what he missed. ...I'll teach him fast.", 'ending:home'),
                    ('go back', "Go on, my love. Go back to your apples. Come and see me at Samhain. I'll keep a candle in the window.", 'ending:veil')]),
        ],
        {'home': {'text': "Take this. It won't fit him tomorrow.", 'items': [it_seven], 'choice': [it_veil, it_wisp]},
         'veil': {'text': "Take this.", 'tragic': True, 'items': [it_fruit], 'choice': [it_veil, it_wisp]}})

c1 = z.item('Trampled-Fence Bracer', 'bracer', 20, 'ward', "Fence-iron from Tuathal's pasture, bent by a fairy horse.")
c2 = z.item('Scarlet-Thread Charm', 'gem', 20, 'charm', "A scarlet thread off a rider's sleeve, knotted round a hoof-nail.")
z.quest('bl_host_searching', 'The Host Is Searching', 20, 'bl_tuathal',
        "Fairy horses came through my pasture last night - right through the fence - and the riders on them looked into every byre and under every cart. Searching.\n\nWill you [follow them]? Knock a few of the horses off my grass, and see where the riders go. And what they're looking for.",
        'follow them',
        "Midir's host is riding through the pastures, searching every byre.",
        [
            hunt([480, 1450], "Drive off 5 faerie horses on Tuathal's grazing, about 160 m south of Tuathal", 'faerie horse', 5),
            search(Z, [500, 1460], "Search the trampled fence for sign of the riders (click the glinting spot)", "a scarlet thread on a fence-nail", CRATE,
                   "A scarlet thread, caught on a nail - from a rider's sleeve. Every rider of the host wears a scarlet thread. Like a sign. Like mourning.",
                   give='a scarlet thread'),
            reach(Z, [620, 1420], "Watch the riders' camp from cover, about 120 m east", "Riders in green and gold round a fire that burns without smoke. One says it plainly, in the old tongue: 'She is in the valley again. The fly has come home. Find her before the wind does.'", r=25),
            end_talk('bl_tuathal', "Return to Herder Tuathal", "'The fly has come home'? ...That's the old story. Etain, that Midir loved, turned into a scarlet fly.\n\nThey think she's here. In Bri Leith. Gods help whoever she is.", 'default'),
        ],
        {'default': {'text': "From my pasture, what's left of it.", 'choice': [c1, c2]}},
        requires='veil')

c3 = z.item("Rider's Green-Gold Belt", 'belt', 22, 'finesse', "Green leather worked with gold. It belonged to someone who's been riding for a thousand years.")
c4 = z.item("Host-Message Ring", 'ring', 22, 'mind', "The ring the rider carried his message in. It's hollow, and it hums.")
c5 = z.item('Fairy-Steed Bridle Charm', 'gem', 22, 'charm', "Silver bells on a green bridle. They ring when nothing moves them.")
z.quest('bl_midirs_rider', "Midir's Rider", 22, 'bl_tuathal',
        "The riders of Bri Leith carry messages between them in hollow rings. Take one, and we'll know what they know.\n\nWill you [take a rider's ring]? Mind - they don't go down easy, and they don't ride alone. Then take what you find to Sarnat in Caille; she reads their tongue.",
        "take a rider's ring",
        "Midir's riders carry messages in hollow rings.",
        [
            hunt([670, 1450], "Defeat 2 riders of Bri Leith at their camp, about 200 m south-east of Tuathal", 'rider of Bri Leith', 2, give="a rider's hollow ring",
                 text="The last rider falls with a sound like a harp-string breaking. A hollow ring rolls out of his glove."),
            end_talk('bl_sarnat', "Take the hollow ring to Sarnat of Caille", "'Seek her where the scarlet fly rests. The wind is rising - Fuamnach is awake.'\n\nSo Midir knows too. His host isn't hunting her. It's trying to find her first.", 'default'),
        ],
        {'default': {'text': "From the Muintir.", 'choice': [c3, c4, c5]}},
        requires='bl_host_searching')

c6 = z.item("Blademaster's Riding Gauntlet", 'bracer', 24, 'might', "Twenty years in the host's saddle wore it thin. It's still a fine gauntlet.")
c7 = z.item("Mortal Champion's Torc", 'neck', 24, 'finesse', "The torc he wore when the host took him. It's out of fashion by about twenty years.")
z.quest('bl_blademaster', 'The Blademaster', 24, 'bl_tuathal',
        "There's a man rides with the host - a mortal, a blademaster, carried off twenty years ago at a fair. My father knew him. He fights for them now and doesn't know his own name.\n\nWill you [bring him round]? Beat him, and the host's hold on him might break. Mind Mikka, their champion - he's never far off.",
        'bring him round',
        "A mortal blademaster, carried off by Midir's host twenty years ago, rides with them still.",
        [
            hunt([645, 1367], "Defeat The Blademaster on the pastures, about 110 m south-east of Tuathal - stay clear of Mikka", 'The Blademaster', 1,
                 text="The Blademaster lowers his sword and looks at his hands. 'Twenty years? It was a day. One dance. ...Tell my mother I'm sorry. No - she'll be dead. Gods.'"),
            end_talk('bl_tuathal', "Return to Herder Tuathal", "He knew you? He spoke? Then he's free, or near enough.\n\nHe'll go back to them, mind. Twenty years in that saddle - there's nothing for him here now. But he'll go back knowing his own name. That's something.", 'default'),
        ],
        {'default': {'text': "From my father's old friend - he left this for whoever freed him.", 'choice': [c6, c7]}},
        requires='bl_midirs_rider')

# ======================================================================== The Girl Who Dreams of a Hall (20 to 30) - Muintir
d1 = z.item('Golden-Hall Dream Charm', 'gem', 20, 'mind', "Aideen's drawing of the hall she dreams of, folded small. The doors are exactly right.")
d2 = z.item('Wing-Scale Ring', 'ring', 20, 'charm', "A single scarlet wing-scale, set in silver. It's warm.")
z.quest('bl_aideens_dreams', "Aideen's Dreams", 20, 'bl_nessa',
        "My Aideen dreams of a golden hall under a hill, and a lake with the moon in it, and a man with yellow hair who calls her by another name. Every night.\n\nSarnat in Caille says it's nothing. Sarnat looked very pale when she said it. Will you [talk to Aideen]? She'll tell a stranger more than her mother.",
        'talk to Aideen',
        "Nessa's daughter Aideen dreams every night of a golden hall under a hill.",
        [
            talk('bl_aideen', "Talk to Aideen in Brynach", "The lake's the one past the pastures - Moon Lake. I've never been. But I know there's a [stone] on the shore with a hole in it, and I used to sit in the hole. I KNOW that. How do I know that?", kw='stone'),
            reach(Z, [1080, 1350], "Go to the shore of Moon Lake, about 540 m south-east of Brynach", "A grey stone on the shore, with a hole worn through it - exactly a girl's size. The moon is on the water just as she said.", r=25),
            search(Z, [1085, 1345], "Search the holed stone on the shore (click the glinting spot)", "a scarlet wing-scale", CRATE,
                   "In the hollow of the stone, a single scarlet scale off an insect's wing - much bigger than any insect's. It's warm as a hand.",
                   give='a scarlet wing-scale'),
            end_talk('bl_sarnat', "Take the wing-scale to Sarnat of Caille", "Scarlet. Warm.\n\nIt's her. Aideen - it's Etain's own name, in the old tongue. Etain, born a third time, in Brynach of all places, to a weaver.\n\nAnd Fuamnach's wind is rising. Don't tell Nessa. Not yet.", 'default'),
        ],
        {'default': {'text': "From the Muintir. And keep this between us.", 'choice': [d1, d2]}},
        requires='bl_ruadhs_letters')

d3 = z.item('Menhir-Shelter Bracer', 'bracer', 22, 'ward', "Stone dust from the lake's menhir, bound in leather. Wind doesn't seem to reach you as hard.")
d4 = z.item("Wrath-Sprite's Ember Ring", 'ring', 22, 'might', "A wrath sprite's spark, gone dim and warm.")
d5 = z.item('Gale-Torn Belt', 'belt', 22, 'finesse', "Shredded by a wind out of a clear sky.")
z.quest('bl_scarlet_fly', 'Where the Fly Rests', 22, 'bl_caoimhe',
        "There's a scarlet fly on the lake menhir, every night this month. A fly the size of a sparrow. And every night a cold wind comes down off the Heights hunting along the shore, and the wrath sprites go mad in it.\n\nWill you [keep the sprites off] the menhir tonight? I don't know what that fly is. I know it's frightened.",
        'keep the sprites off',
        "A scarlet fly shelters on Moon Lake's menhir each night while a cold wind hunts the shore.",
        [
            hunt([1180, 1250], "Kill 5 wrath sprites by the lake menhir, about 140 m north-east of Fisher Caoimhe", 'wrath sprite', 5),
            reach(Z, [1200, 1230], "Stand by the menhir as the wind comes", "The wind comes down off the Heights out of a clear sky and goes along the shore like a hand searching. It passes over the menhir - and passes on. On the stone, a scarlet fly folds its wings.", r=25),
            end_talk('bl_caoimhe', "Return to Fisher Caoimhe", "It missed her. The wind missed her. ...Her? Why did I say her?\n\nThe Muintir would want to know of this. Sarnat in Caille.", 'default'),
        ],
        {'default': {'text': "From the lake. Thank you.", 'choice': [d3, d4, d5]}},
        requires='bl_aideens_dreams')

d6 = z.item("Lusmorebane's Foxglove Crown", 'neck', 25, 'charm', "Foxgloves that never wilt, woven by the changelings' king. Lusmore was the man they gave a hump to. This was the one who did it.")
d7 = z.item("Aideen's Ribbon Bracer", 'bracer', 25, 'ward', "Aideen's scarlet ribbon, wrapped round a bracer. She insisted.")
d8 = z.item('Cradle-Ash Ring', 'ring', 25, 'faith', "Cut from the changelings' cradle, burned and scrubbed clean.")
z.quest('bl_fair_swap', 'Fair Swap', 25, 'bl_nessa',
        "Last night something came to Aideen's bed and tried to put something else in it. Something that looked like her. I screamed and it ran - east, to the Hollow past the lake where the mad changelings live.\n\nThey want her. They'll come back. Will you [go to the Hollow] and make them stop?",
        'go to the Hollow',
        "The mad changelings tried to swap Aideen for one of their own.",
        [
            hunt([1495, 1535], "Kill 6 mad changelings at the changeling den, about 950 m east of Brynach", 'mad changeling', 6),
            hunt([1490, 1531], "Defeat Lusmorebane, king of the Hollow", 'Lusmorebane', 1,
                 text="Lusmorebane cackles as he falls. 'Paid for! The Lady of the Wind paid for her! Blow her away, blow her away...'"),
            search(Z, [1500, 1540], "Search the changelings' cradle in the den (click the glinting spot)", "a scarlet ribbon in the cradle", CRATE,
                   "In a cradle of thorns: a doll made to look exactly like Aideen, and tied round its neck, one of Aideen's own scarlet ribbons.",
                   give="Aideen's ribbon"),
            end_talk('bl_nessa', "Return to Nessa the Weaver in Brynach", "Her ribbon. They had her ribbon.\n\n'The Lady of the Wind paid for her.' What lady? What wind? Why my daughter?\n\n...Sarnat knows. I can see it on her. Go and ask her. Make her tell you.", 'default'),
        ],
        {'default': {'text': "Take this. From both of us - she wanted you to have the bracer.", 'choice': [d6, d7, d8]}},
        requires='bl_scarlet_fly')

d9 = z.item("Riocard's Yew Wand", 'gem', 28, 'mind', "Riocard's wand, broken or not as you chose. Yew, bound in scarlet thread, still faintly cold.")
d10 = z.item("Bresal's-Heir Torc", 'neck', 28, 'faith', "Riocard's torc. He thought he was the heir of Bresal the druid. He was right, unfortunately.")
d11 = z.item('Circle-Breaker Ring', 'ring', 28, 'might', "A shard of the binding-stone, set in bronze.")
z.quest('bl_riocards_binding', "Riocard's Binding", 28, 'bl_sarnat',
        "Riocard has bound Aideen somehow - a binding so the wind can find her wherever she runs. That's how Bresal did it in the old tale, for Fuamnach the first time.\n\nIt'll be at the Circle, in a binding-stone. Bring friends. Will you [break the binding]?",
        'break the binding',
        "Riocard, the renegade druid at the Circle, has bound Aideen so Fuamnach's wind can find her.",
        [
            hunt([450, 420], "Kill 6 renegade druids at the Druid Circle", 'renegade druid', 6),
            hunt([455, 425], "Defeat Riocard, the renegade druid", 'Riocard', 1,
                 text="Riocard falls among his stones. 'The Queen promised her... the Queen promised ME... a seat in the forest court...'"),
            search(Z, [450, 415], "Search the binding-stone in the middle of the Circle (click the glinting spot)", "a yew wand bound in scarlet", CRATE,
                   "A yew wand, bound with scarlet thread, set upright in a hole in the stone. It's ice-cold, and it points - always - toward Brynach.",
                   give="Riocard's yew wand"),
            choice('bl_sarnat', "Bring the yew wand to Sarnat of Caille",
                   "The binding. Gods, it's still pointing at her.\n\nWe can [break the wand] - and the wind loses her, for good. Or we [keep the wand], bound as it is, and use it: it points to her for Fuamnach, but it can point Fuamnach to US. We'd know where she'll come. It's a terrible risk.",
                   [('break the wand', "Broken. Feel that? The air's warmer already. She's safe from the wind, at least.", 'ending:broken'),
                    ('keep the wand', "Kept, then. Wrapped in rowan, in my strongbox. When Fuamnach comes, we'll know. Gods help us if we're wrong.", 'ending:kept')]),
        ],
        {'broken': {'text': "From the Muintir.", 'choice': [d9, d10, d11]},
         'kept': {'text': "From the Muintir.", 'choice': [d9, d10, d11]}},
        requires='bl_fair_swap')

d12 = z.item("Etain's Third-Life Cloak", 'cloak', 30, 'faith', "Scarlet and gold. Aideen wove it for you herself, whichever she chose.")
d13 = z.item('Hall-Under-the-Hill Ring', 'ring', 30, 'charm', "Gold, warm, and humming with music.")
d14 = z.item("Weaver's-Daughter Belt", 'belt', 30, 'finesse', "Brynach weaving, Nessa's best. Undyed, like a herder's.")
z.quest('bl_hall_under_the_hill', 'The Hall Under the Hill', 30, 'bl_aideen',
        "Sarnat told me. Everything. I'm Etain - I was. A thousand years ago, and another life after that.\n\nThe riders came last night, to the edge of Brynach, and waited. They want me to come home - to Midir, under the hill. Mam wants me to stay. Will you [walk with me] to the riders? I need to see them before I choose.",
        'walk with me',
        "Aideen, Etain born again, must choose between Midir's hall under the hill and her mortal life.",
        [
            reach(Z, [670, 1440], "Walk with Aideen to the riders' camp in the pastures, about 330 m south of Brynach", "The riders kneel as you come. The fire without smoke burns higher. One of them - yellow-haired, crowned - gets up, and Aideen's hand goes tight on your arm.", r=25),
            choice('bl_aideen', "Talk to Aideen in Brynach",
                   "That was him. Midir. He looked at me like - like I'd been gone a day.\n\nIf I [go under the hill], I'm Etain, and I'm home, and Mam loses me. If I [stay in Brynach], I'm Aideen, and I weave, and I grow old, and he waits again. He's good at waiting. Tell me which.",
                   [('go under the hill', "Then I'll go. At midsummer, from the lake stone. I'll come back at Samhain to see Mam - that's allowed. ...Tell her I chose it. Don't let her think I was taken.", 'ending:hill'),
                    ('stay in Brynach', "Then I'm Aideen. I'll weave. And when I'm old, if he's still waiting, maybe. ...Thank you. Mam's going to cry either way.", 'ending:stay')]),
        ],
        {'hill': {'text': "Take this. I made it for whoever helped me choose.", 'items': [d12], 'choice': [d13, d14]},
         'stay': {'text': "Take this. I made it for whoever helped me choose.", 'items': [d12], 'choice': [d13, d14]}},
        requires='bl_riocards_binding')

# ======================================================================== The Collory Road (25 to 35) - Rangers
e1 = z.item("Waylayer's Mask Charm", 'gem', 25, 'finesse', "A siog waylayer's face-mask. It smells of old cheese and older fear.")
e2 = z.item("Road-Ranger's Ring", 'ring', 25, 'might', "Issued at Druim Cain to rangers who keep the road open.")
z.quest('bl_waylayers', 'Waylayers on the Road', 25, 'bl_fearghal',
        "Siog waylayers are hitting carts on the Collory road between here and Caille, from the rocks west of the road. We've lost three carts and two rangers.\n\nWill you [clear the rocks]? Then look round for my rangers' arrows - I want to know where they made their stand.",
        'clear the rocks',
        "Siog waylayers are hitting carts on the Collory road from the rocks west of it.",
        [
            hunt([760, 260], "Kill 6 siog waylayers at the rocks west of the Collory road, about 220 m south-west of Druim Cain", 'siog waylayer', 6),
            search(Z, [765, 265], "Search the ambush rocks for the rangers' last stand (click the glinting spot)", "a quiver of ranger arrows", CRATE,
                   "A quiver of Druim Cain arrows, every one shot. Behind the rocks, a waylayer's purse - paid in wind-charms, like the ore.",
                   give='a ranger quiver'),
            end_talk('bl_fearghal', "Return to Ranger-Commander Fearghal at Druim Cain", "Every arrow shot. They died well.\n\nWind-charms again. The same coin as the ore. Somebody's paying for this whole valley in wind.", 'default'),
        ],
        {'default': {'text': "From the Rangers.", 'choice': [e1, e2]}})

e3 = z.item("Tower-Watch Bracer", 'bracer', 27, 'ward', "From Giolladhe's Tower's own watch. Dented on every side.")
e4 = z.item("Rage-Wolf Pelt Cloak", 'cloak', 27, 'might', "A rage wolf's pelt. It still bristles in a fight.")
e5 = z.item("Hunting-Horn Charm", 'gem', 27, 'charm', "A Wild Hunt horn, cracked. It still sounds, very faintly, if you listen.")
z.quest('bl_tower_horns', 'Horns at the Tower', 27, 'bl_maudalin',
        "The Wild Hunt's horns are sounding round Giolladhe's Tower every night, and the rage wolves run with them. They're marking the tower for something.\n\nWill you [thin the wolves]? Then come back to me. If they're marking us, I want to know what for.",
        'thin the wolves',
        "The Wild Hunt's horns sound round Giolladhe's Tower, and the rage wolves run with them.",
        [
            hunt([300, 1500], "Kill 3 rage wolves at their run, about 260 m south-east of the tower", 'rage wolf', 3),
            hunt([300, 1450], "Kill 4 faerie steeds near the run", 'faerie steed', 4),
            end_talk('bl_maudalin', "Return to Watch-Sergeant Maudalin at Giolladhe's Tower", "Fewer wolves. Good. And I found this while you were out: a horn-sign cut in the tower door. Riders' sign, Midir's - 'Not here. Search east.'\n\nSo the Hunt isn't after the tower. It's searching. Same as everyone this year.", 'default'),
        ],
        {'default': {'text': "From the tower's stores.", 'choice': [e3, e4, e5]}})

e6 = z.item("Mikka's Champion Torc", 'neck', 30, 'might', "The host's champion wore this a thousand years. You've been warned: it's heavy.")
e7 = z.item("Host-Champion's Bracer", 'bracer', 30, 'finesse', "Gold and green, with a scarlet thread round the wrist.")
e8 = z.item('Unhorsed Ring', 'ring', 30, 'might', "A ring Mikka dropped when you put him in the grass.")
z.quest('bl_mikka', "The Host's Champion", 30, 'bl_maudalin',
        "Mikka. The host's champion. He rides the pastures south of here and he's put eleven rangers in the ground this year alone - for sport, between searches.\n\nThis is GROUP work. Will you [put Mikka down]? Not for good - he's sidhe, he'll be back. But long enough that the road breathes.",
        'put Mikka down',
        "Mikka, champion of Midir's host, kills rangers on the pastures for sport.",
        [
            hunt([678, 1367], "Defeat Mikka, the host's champion, on the pastures, about 560 m east of the tower", 'Mikka', 1,
                 text="Mikka falls laughing. 'Well struck, mortal. Tell your Rangers - the host is not their enemy this year. The wind is. Look east.'"),
            end_talk('bl_fearghal', "Report to Ranger-Commander Fearghal at Druim Cain", "Mikka down! Eleven rangers, and you put him in the grass.\n\n'The wind is. Look east.' East is the Cursed Forest. Ronan's scouts say the border's thick with the Queen's people. I don't like any of this.", 'default'),
        ],
        {'default': {'text': "From the Rangers - and eleven of them who'd thank you.", 'choice': [e6, e7, e8]}},
        group=True, requires='bl_tower_horns')

e9 = z.item("Forest-Gate Scout's Belt", 'belt', 33, 'finesse', "Rowan-marked, so the Queen's people won't touch the wearer. Mostly.")
e10 = z.item("Wraith-Ward Bracer", 'bracer', 33, 'ward', "Iron and rowan, against things that come out of the dark.")
e11 = z.item('Border-Stone Charm', 'gem', 33, 'faith', "A chip off the Forest Gate's stones. It hums near the Cursed Forest.")
z.quest('bl_road_east', 'The Road East', 33, 'bl_fearghal',
        "Scout Fionnuala is down on the east border, where the old road went into the Cursed Forest. It's been shut for years - the Queen's people hold the gate stones.\n\nWill you [go to Fionnuala] and see how thick they are? If we're going to open that gate, I need to know what it costs.",
        'go to Fionnuala',
        "Ranger-Commander Fearghal wants to know what it would take to open the Forest Gate on the Cursed Forest border.",
        [
            talk('bl_fionnuala', "Find Ranger-Scout Fionnuala on the east border", "You came the long way. Good - the short way's through them.\n\nLook: black wraiths among the stones, poachers who never come back to their villages, and the far dorocha watching. Thin them, and I'll see what moves. [Ready]?", kw='ready'),
            hunt([1540, 990], "Kill 4 black wraiths among the gate stones, about 120 m east of Fionnuala", 'black wraith', 4),
            end_talk('bl_fearghal', "Report to Ranger-Commander Fearghal at Druim Cain", "Wraiths, poachers and the Dark Man watching. A war band could do it - four at least, and a druid to wake a ward.\n\nWe'll muster when the valley's ready. When the Rangers' resolve is up, we go. Thank you.", 'default'),
        ],
        {'default': {'text': "From the Rangers.", 'choice': [e9, e10, e11]}},
        requires='bl_mikka')

# ======================================================================== Fuamnach's Wind (28 to 40) - Muintir
f1 = z.item('Empyrean Shard Charm', 'gem', 28, 'mind', "A shard of an empyrean sentinel. Sky-blue, and it whistles in the wind.")
f2 = z.item('Cold-Wind Ring', 'ring', 28, 'faith', "Frost forms on it, even in summer.")
z.quest('bl_heights_watch', 'Wind off the Heights', 28, 'bl_sarnat',
        "The wind comes off the Empyrean Heights, north-east. The empyreans live up there - the sky's own children, Keeper Rasa used to say. Rasa hasn't come down to Caille in a month.\n\nWill you [go up the Heights] and see? Carefully. The empyreans used to be gentle.",
        'go up the Heights',
        "Fuamnach's wind comes off the Empyrean Heights, and Keeper Rasa hasn't been seen in a month.",
        [
            hunt([1250, 800], "Kill 6 empyrean sentinels on the lower Heights, about 350 m east of Caille", 'empyrean sentinel', 6),
            search(Z, [1400, 700], "Search the guardian stones on the Heights (click the glinting spot)", "a frost-carved stone", CRATE,
                   "Frost on the stone in midsummer, carved by the wind itself: a long, cruel F. And the wind round the stones comes, very clearly, from the east - from the Cursed Forest.",
                   give='a sketch of the frost-carving'),
            end_talk('bl_sarnat', "Return to Sarnat of Caille", "F. Fuamnach signs her wind.\n\nAnd it blows out of the Cursed Forest. The Queen has taken her in, then. Rasa - find Rasa. Her hut is high on the Heights. If anyone can turn the empyreans back, she can.", 'default'),
        ],
        {'default': {'text': "From the Muintir.", 'choice': [f1, f2]}},
        requires='bl_aideens_dreams')

f3 = z.item("Keeper's Sky-Blue Belt", 'belt', 31, 'faith', "Rasa's own. Sky-blue, embroidered with clouds.")
f4 = z.item('Freed-Keeper Bracer', 'bracer', 31, 'ward', "From the door of Rasa's hut, where she held out a month.")
f5 = z.item('Empyrean-Song Torc', 'neck', 31, 'mind', "Rasa hums the empyreans' song into it. It hums it back.")
z.quest('bl_keepers_hut', "The Keeper's Hut", 31, 'bl_sarnat',
        "Rasa's hut is high on the Heights, north-east. If the empyreans have turned, she's trapped up there with them.\n\nWill you [find Rasa]? Bring friends - the Heights are hard going.",
        'find Rasa',
        "Keeper Rasa is trapped in her hut on the Heights by the empyreans she kept.",
        [
            reach(Z, [1250, 400], "Climb to Keeper Rasa's hut on the Empyrean Heights, about 570 m north-east of Caille", "A small stone hut, its door barred from inside. Empyrean keepers circle it like hawks - and from inside, a woman's voice, hoarse, singing.", r=30),
            hunt([1320, 420], "Kill 5 empyrean keepers circling the hut", 'empyrean keeper', 5),
            end_talk('bl_rasa', "Talk to Keeper Rasa in her hut", "You came. A month I've sung at the door to keep them out. My own empyreans. The sky's children.\n\nIt's not them. It's the wind that's in them - her wind, Fuamnach's, blowing out of the Queen's forest. I can turn them back, one by one, if you break her lieutenants. Stay a while. I'll tell you how.", 'default'),
        ],
        {'default': {'text': "Take these. I've had a month to sort my things.", 'choice': [f3, f4, f5]}},
        requires='bl_heights_watch')

f6 = z.item("Hru's Stone-Guard Ring", 'ring', 34, 'might', "From Guardian Hru's own stones. It's heavier than a ring should be.")
f7 = z.item('Wind-Freed Bracer', 'bracer', 34, 'ward', "An empyrean bracer, Fuamnach's wind sung out of it.")
z.quest('bl_hru', 'Guardian Hru', 34, 'bl_rasa',
        "Hru was the gentlest of my guardians. Now he holds the guardian stones for her, south of here, and the wind blows through him like a flute.\n\nWill you [break Hru's hold]? Beat him down, and I'll sing the wind out of him from here.",
        "break Hru's hold",
        "Guardian Hru holds the guardian stones for Fuamnach.",
        [
            hunt([1428, 856], "Defeat Guardian Hru at the guardian stones, about 520 m south of Rasa's hut", 'Guardian Hru', 1,
                 text="Hru goes down, and up on the Heights you hear Rasa singing. The wind goes out of him with a sigh, and he stands, blinking, gentle."),
            end_talk('bl_rasa', "Return to Keeper Rasa", "I felt him come back. Thank you.\n\nNiy is next - and Niy is the strong one.", 'default'),
        ],
        {'default': {'text': "From the Heights.", 'choice': [f6, f7]}},
        requires='bl_keepers_hut')

f8 = z.item("Overseer Niy's Crest", 'neck', 37, 'faith', "Niy's crest of office. The wind still whistles through it, but it's only wind now.")
f9 = z.item('Eye-of-the-Ridge Ring', 'ring', 37, 'mind', "Niy saw the whole valley from that ridge. So does this ring, a little.")
f10 = z.item('Ridge-Wind Cloak', 'cloak', 37, 'finesse', "It flaps in a wind that isn't blowing.")
z.quest('bl_niy', 'Niy the Overseer', 37, 'bl_rasa',
        "Niy the Overseer holds the eastern ridge, the one that looks into the Cursed Forest. Her wind goes through him first.\n\nThis is GROUP work. Will you [break Niy]? While he stands, I can't reach the others.",
        'break Niy',
        "Niy the Overseer holds the eastern ridge for Fuamnach.",
        [
            hunt([1506, 395], "Defeat Niy the Overseer on the eastern ridge, about 230 m east of Rasa's hut", 'Niy the Overseer', 1,
                 text="Niy falls on the ridge. Beyond it, the Cursed Forest is black to the horizon - and above the Heights, the wind howls a woman's name: hers."),
            end_talk('bl_rasa', "Return to Keeper Rasa", "Niy's free. Now she's alone up there, at the Eye of the Wind, on the highest point of the Heights.\n\nShe'll know you're coming. She'll want you to come.", 'default'),
        ],
        {'default': {'text': "From the Heights.", 'choice': [f8, f9, f10]}},
        group=True, requires='bl_hru')

f11 = z.item("Fuamnach's Rowan Rod", 'gem', 40, 'faith', "The rod Fuamnach struck Etain with, a thousand years ago. Rowan. Rasa says the rowan was always meant to be on our side.")
f12 = z.item('Eye-of-the-Wind Cloak', 'cloak', 40, 'mind', "Grey as a storm, and very still.")
f13 = z.item("Jealous Wife's Ring", 'ring', 40, 'charm', "Gold, with a scarlet stone that never stops moving.")
f14 = z.item('Stilled-Wind Bracer', 'bracer', 40, 'ward', "The wind can't get past it.")
z.quest('bl_fuamnach', 'Fuamnach', 40, 'bl_rasa',
        "Fuamnach is at the Eye of the Wind, the highest point of the Heights, north-east of here. Twice she drove Etain out. She will not do it a third time.\n\nThis is GROUP work - the hardest in the valley. Bring the best you know. Will you [face Fuamnach]?",
        'face Fuamnach',
        "Fuamnach, Midir's jealous first wife, waits at the Eye of the Wind on the highest point of the Heights.",
        [
            reach(Z, [1490, 190], "Climb to the Eye of the Wind, about 270 m north-east of Rasa's hut", "A ring of stones on the summit, and in it a woman in grey with a rowan rod, the wind pouring off her toward Brynach. 'Again?' she says. 'Every time, someone. And every time, the Queen will lend me another wind.'", r=30),
            hunt([1520, 170], "Defeat Fuamnach at the Eye of the Wind", 'Fuamnach', 1,
                 text="Fuamnach falls, and the wind falls with her - all of it, all at once, so the silence rings. Far east, over the Cursed Forest, something laughs."),
            choice('bl_rasa', "Return to Keeper Rasa",
                   "It's still. The whole valley's still.\n\nShe'll come back - she always comes back, while the Queen lends her wind. I can [scatter her] to the four winds, so it takes her a thousand years to gather herself again. Or I can [bind her] here, in the stones of the Eye, where I can watch her. Watched, she can't hide in the Queen's forest. Scattered, she can't hurt Aideen.",
                   [('scatter her', "Scattered, then. A thousand years. Aideen will be dust - happy, I hope - before she's whole again.", 'ending:scatter'),
                    ('bind her', "Bound, then. I'll sit with her. Someone has to. And if the Queen comes for her, we'll know.", 'ending:bind')]),
        ],
        {'scatter': {'text': "Take these. From the Heights, the Muintir, and a girl in Brynach who'll never know your name.", 'items': [f11], 'choice': [f12, f13, f14]},
         'bind': {'text': "Take these. From the Heights, the Muintir, and a girl in Brynach who'll never know your name.", 'items': [f11], 'choice': [f12, f13, f14]}},
        group=True, requires='bl_niy')
