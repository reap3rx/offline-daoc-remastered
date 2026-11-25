"""Campacorentin Forest's story quests (claude 2026-11-24, "Albion - the plan", round 2) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_campacorentin

Where the two threads cross. Merlin sleeps in a thorn in the deep wood, where Nimue sealed him, and the wood itself guards his
sleep. Morgana wants what he knows of gates: her Crimson sacrificers feed the thorn's roots blood to open it, her Green Witch
works the middle wood, and her champion Accolon of Gaul - who once fought Arthur with a stolen Excalibur - comes to break the
thorn. And Merlin knows the dragon: as a boy he showed Vortigern the red and white dragons under the tower, and the white one,
beaten then, is Golestandt. Lethantis's mages bred the wood ogres (the old heretic Esras was right), and the Thornwardens and
the Ulfwych Rangers hold the forest.

The zone's two older quests are kept as they were (page, heretic).

Arcs (recommended levels): The Station Road (6-10), The Bred Ogres (12-16), Caer Ulfwych (12-15), The Waking Wood (18-20),
Merlin's Thorn (20-24, the Dangerous deep wood).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk
from albion_story import Story, CRATE, BEDROLL, LANTERN, M, F, OLD

S = Story(8, 'Campacorentin Forest', 'alb_campacorentin', 'story008_campacorentin', {'page', 'heretic'},
          {'elowen', 'robin', 'ivo_penrose', 'esras'},
          {"Page's Ribbon", 'Ring of the Faithful Page', "Aldric's Broken Spur", 'Sealed-Letter Sash', 'Lethantis Brand-Ring',
           "Heretic's Satchel", 'Ogre-Hide Wrap', "Seeker's Bracer"})
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
OGRE_LORD, KNIGHT, DRUID_SAC, FILIDH_SAC, WOOD_OGRE = 12627, 12967, 12468, 12161, 12630

# ------------------------------------------------------------------ people
person('cf_ifan', 'Station-Warden Ifan', (264, 282), 'm', 26, guild='the Ulfwych Rangers',
       idle="Campacorentin Station. Last warm fire before the wood swallows you.")
person('cf_tewdwr', 'Archivist Tewdwr', (348, 168), 'old', 35, guild='the Lethantis Association',
       idle="The Association keeps every book in Albion worth keeping. And a few that aren't.")
person('cf_gwion', 'Ranger-Captain Gwion', (952, 880), 'm', 38, model=28, guild='the Ulfwych Rangers',
       idle="Caer Ulfwych holds the middle of the wood. The edges hold themselves, mostly.")
person('cf_elaine', 'Thornwarden Elaine', (940, 900), 'f', 40, guild='the Thornwardens',
       idle="We keep the old man's sleep. It's harder than it sounds.")
person('cf_alun', 'Forester Alun', (1525, 412), 'm', 30, idle="The trees have started moving at night. Not swaying. Moving.")

# ======================================================================== The Station Road (6-10)
s1 = z.item("Snare-Cutter's Ring", 'ring', 6, 'finesse', "Iron, from a poacher's wire-cutters.")
s2 = z.item("Ranger's Acorn Charm", 'gem', 6, 'charm', "A bronze acorn. Every Ulfwych ranger has one.")
z.quest('cf_poachers', "Poachers in the King's Wood", 6, 'cf_ifan',
        "This was a king's forest. Uther hunted here. Now poachers string snares from the north road to the middle wood and nobody stops them.\n\nWill you [stop the poachers]? Rangers can't be everywhere.",
        'stop the poachers',
        "Poachers are snaring the king's forest north of the middle wood.",
        [
            hunt((780, 513), "Drive off the poachers on the north road " + where((780, 513), 'cf_ifan'), 'poacher', 5),
            end_talk('cf_ifan', "Tell Station-Warden Ifan", "Good. The deer will thank you. The rangers do too.", 'default'),
        ],
        {'default': {'text': "From the Ulfwych Rangers.", 'choice': [s1, s2]}})

s3 = z.item("Goblin-Tooth Bracer", 'bracer', 7, 'might', "Studded with sylvan goblin teeth. They had plenty.")
s4 = z.item("Whelp-Catcher's Belt", 'belt', 7, 'finesse', "Hung with little nets. Ifan's idea of a joke.")
z.quest('cf_whelps', 'Sylvan Goblins', 7, 'cf_ifan',
        "Sylvan goblins. Green, quick and thieving. Their whelps raid the Station's stores, and last week they took a satchel from an Association courier.\n\nWill you [find the satchel]? The Archivist's frantic about it.",
        'find the satchel',
        "Sylvan goblins stole a Lethantis courier's satchel near Campacorentin Station.",
        [
            hunt((600, 400), "Chase down the sylvan goblin whelps " + where((600, 400), 'cf_ifan'), 'sylvan goblin whelp', 6),
            search(Z, P(755, 409), "Search the goblins' den", "a den of stolen things", CRATE,
                   "Spoons, boots, a lute - and the courier's satchel, chewed. The scroll-case inside is empty.", give="the courier's satchel"),
            end_talk('cf_ifan', "Bring the satchel to Ifan", "Empty? The Archivist won't like that. Take it to him anyway - he'll want to know.", 'default'),
        ],
        {'default': {'text': "From the Ulfwych Rangers.", 'choice': [s3, s4]}})

s5 = z.item("Prophecy-Page Sash", 'belt', 9, 'mind', "Stitched with a copy of the page. Tewdwr insisted.")
s6 = z.item("Red-and-White Ring", 'ring', 9, 'mind', "Two dragons, one red, one white, coiled round each other.")
s7 = z.item("Lethantis Reading-Charm", 'gem', 9, 'mind', "It makes small writing larger. Mostly.")
z.quest('cf_scroll', 'The Missing Page', 9, 'cf_tewdwr',
        "The satchel was carrying a page of Merlin's prophecies - one of the oldest we have. The goblins will have taken it to their war camp; they think writing is magic.\n\nThey're not wrong. Will you [recover the page]?",
        'recover the page',
        "A page of Merlin's prophecies was taken by the sylvan goblins to their war camp.",
        [
            hunt((1046, 560), "Fight through the sylvan goblin hunters " + where((1046, 560), 'cf_tewdwr'), 'sylvan goblin hunter', 4),
            hunt((896, 432), "Break the goblins' war camp", 'sylvan goblin warrior', 3),
            search(Z, P(900, 436), "Search the war camp for the page", "a goblin shrine of paper", CRATE,
                   "The page, pinned to a stick and painted round with goblin-marks. Merlin's hand: 'The red dragon and the white fought under Vortigern's tower, and the white was beaten and fled into the south. It sleeps, but not forever.'",
                   give="Merlin's page"),
            end_talk('cf_tewdwr', "Bring the page to Archivist Tewdwr", "'Fled into the south.' Every scholar's read this page. None of us thought to ask where.\n\nDartmoor. The dragon on Dartmoor is the white dragon of Vortigern's tower. Golestandt.", 'default'),
        ],
        {'default': {'text': "From the Lethantis Association.", 'choice': [s5, s6, s7]}},
        requires='cf_whelps')

s8 = z.item("Wisp-Lantern Charm", 'gem', 10, 'charm', "A lantern-glass the wisps tried to steal. It glows faintly blue.")
s9 = z.item("Swamp-Walker's Belt", 'belt', 10, 'ward', "Waxed against the wet.")
z.quest('cf_wisps', 'Lights in the Western Swamps', 10, 'cf_ifan',
        "Will o' wisps in the western swamps, leading travellers off the path. Two of the Station's woodcutters went after the lights last month and came back raving about a hermit in the bog.\n\nWill you [put out the lights]?",
        'put out the lights',
        "Will o' wisps lure travellers into the western swamps.",
        [
            hunt((454, 971), "Put out the will o' wisps " + where((454, 971), 'cf_ifan'), "will o' wisp", 5),
            end_talk('cf_ifan', "Tell Ifan", "A hermit in the bog... The Association drove a man out years ago. Scholar Ivo might know more.", 'default'),
        ],
        {'default': {'text': "From the Ulfwych Rangers.", 'choice': [s8, s9]}})

# ======================================================================== The Bred Ogres (12-16)
o1 = z.item("Ogre-Tusk Torc", 'neck', 12, 'might', "Wood ogre tusk, bound in brass.")
o2 = z.item("Westwood Road Bracer", 'bracer', 12, 'ward', "Rangers' issue. Every one has a dent.")
z.quest('cf_ogre_road', 'Ogres on the Westwood Road', 12, 'cf_gwion',
        "Wood ogres in the south-west have come up onto the Westwood road - scourges, the big ones with the clubs. They've never come so far north.\n\nWill you [clear the road]?",
        'clear the road',
        "Wood ogre scourges have come up from the south-west onto the Westwood road.",
        [
            hunt((578, 1001), "Drive the wood ogre scourges off the road " + where((578, 1001), 'cf_gwion'), 'wood ogre scourge', 5),
            end_talk('cf_gwion', "Tell Ranger-Captain Gwion", "Good. Ogres don't usually move without a reason. I'd like to know it.", 'default'),
        ],
        {'default': {'text': "From the Ulfwych Rangers.", 'choice': [o1, o2]}})

o3 = z.item("Brand-Scar Ring", 'ring', 14, 'mind', "The Lethantis brand, cut from an ogre's harness.")
o4 = z.item("Seer-Bone Charm", 'gem', 14, 'mind', "An ogre seer's bone fetish. It rattles when it's nervous.")
o5 = z.item("Truth-Teller's Mantle", 'cloak', 14, 'faith', "Gwion's gift, for those who don't flinch from the truth.")
z.quest('cf_ogre_seers', 'What the Seers Sing', 14, 'cf_gwion',
        "The ogre seers in the south-west sing to the others, and the others follow. If anything's moving them, it's the seers.\n\nWill you [silence the seers]? And look at their harness. Something's been nagging at me.",
        'silence the seers',
        "Wood ogre seers in the south-west are driving the ogres north. Gwion has a suspicion.",
        [
            hunt((679, 1108), "Silence the wood ogre seers " + where((679, 1108), 'cf_gwion'), 'wood ogre seer', 3),
            search(Z, P(680, 1110), "Look at the seers' harness", "an ogre's harness", CRATE,
                   "Burned into the leather, very old: the Lethantis Association's seal. And a number. These ogres were made, and counted."),
            choice('cf_gwion', "Tell Ranger-Captain Gwion", "The Association's seal. The old hermit, Esras - they called him a heretic for saying this.\n\nI can [tell the rangers] - every one of them - and let Lethantis answer for it. Or we [keep it quiet] and I take it to the Archivist privately. The rangers would burn the Station.",
                   [('tell the rangers', "Then they'll know. Lethantis will have to answer.", 'ending:told'),
                    ('keep it quiet', "Then it's between us and Tewdwr. I hope he's worth it.", 'ending:quiet')]),
        ],
        {'told': {'text': "From the Ulfwych Rangers.", 'items': [o5], 'choice': [o3, o4]},
         'quiet': {'text': "From the Ulfwych Rangers.", 'choice': [o3, o4, o5]}},
        requires='cf_ogre_road')

o6 = z.item("Bred-King's Crown-Ring", 'ring', 16, 'might', "The ogre-lord's iron crown, cut into a ring. Stamped with a number.")
o7 = z.item("Berserker-Hide Bracer", 'bracer', 16, 'might', "Ogre-hide, tough as bark.")
o8 = z.item("Ulfwych Ranger's Cloak", 'cloak', 16, 'finesse', "Forest green. The Rangers' own.")
z.quest('cf_bred_king', 'The Bred-King', 16, 'cf_gwion',
        "The seers sang for someone. The ogres have a lord now - Gorrak, they call him, the Bred-King, bigger than any ogre has a right to be. He's gathering the berserkers in the far south-west.\n\nWill you [end the Bred-King]? Bring a group.",
        'end the Bred-King',
        "Gorrak the Bred-King gathers the wood ogre berserkers in the far south-west.",
        [
            hunt((560, 1020), "Break the wood ogre berserkers " + where((560, 1020), 'cf_gwion'), 'wood ogre berserker', 3),
            boss(Z, P(600, 1060), "Defeat Gorrak the Bred-King", "Gorrak falls. On his iron crown, a number: 1. The first of them.",
                 'Gorrak the Bred-King', OGRE_LORD, 17, "An ogre twice the size of the others rises from a throne of logs. 'Made us,' it rumbles. 'Left us. Now we take the wood.'",
                 adds=[(WOOD_OGRE, 'wood ogre scourge', [14, 15])], every=30, count=2),
            end_talk('cf_gwion', "Tell Ranger-Captain Gwion", "'Made us. Left us.' That's the saddest thing I've heard an ogre say.\n\nThe road's safe. Thank you.", 'default'),
        ],
        {'default': {'text': "From the Ulfwych Rangers.", 'choice': [o6, o7, o8]}},
        requires='cf_ogre_seers', group=True)

# ======================================================================== Caer Ulfwych (12-15)
u1 = z.item("Webweaver's Silk Sash", 'belt', 15, 'finesse', "Spider-silk, finer than anything a loom makes.")
u2 = z.item("Bloated-Spider Fang Ring", 'ring', 15, 'might', "Hollow, and still faintly poisonous. Handle with care.")
z.quest('cf_spiders', 'The Bloated Nest', 15, 'cf_gwion',
        "Bloated spiders east of the Caer - and their mother, Ciraron the Webweaver, whom the rangers won't go near. She's webbed the east road shut.\n\nWill you [open the road]?",
        'open the road',
        "Bloated spiders and their mother Ciraron have webbed shut the road east of Caer Ulfwych.",
        [
            hunt((1290, 800), "Kill the bloated spiders " + where((1290, 800), 'cf_gwion'), 'bloated spider', 6),
            hunt((1282, 720), "Kill Ciraron the Webweaver", 'Ciraron Webweaver', 1),
            end_talk('cf_gwion', "Tell Ranger-Captain Gwion", "Ciraron? Dead? The rangers will drink to you tonight. I'll pay.", 'default'),
        ],
        {'default': {'text': "From the Ulfwych Rangers.", 'choice': [u1, u2]}})

u3 = z.item("Thornwarden's Briar Ring", 'ring', 12, 'faith', "A ring of living briar. It never pricks the one who wears it.")
u4 = z.item("Druid-Barrow Torc", 'neck', 12, 'mind', "From the old druids' barrow. They'd want it used.")
z.quest('cf_druid_barrow', "The Druids Who Don't Rest", 12, 'cf_elaine',
        "There's a barrow east of the Caer where the old druids lie - the ones who first kept the thorn. They've started walking.\n\nWhen the keepers walk, something's wrong with what they kept. Will you [go to the barrow]?",
        'go to the barrow',
        "The old druids who first kept Merlin's thorn walk from their barrow east of Caer Ulfwych.",
        [
            hunt((1052, 816), "Lay the undead druids to rest " + where((1052, 816), 'cf_elaine'), 'undead druid', 5),
            search(Z, P(1055, 820), "Search the druid barrow", "a carved stone at the barrow's heart", CRATE,
                   "Ogham, worn but readable: 'Nimue of the Lake sealed the Old Man in the thorn of the deep wood, at his own asking or against it - we were not told. We keep his sleep. Let none wake him who would use him.'"),
            end_talk('cf_elaine', "Tell Thornwarden Elaine", "'Let none wake him who would use him.' That's our whole creed in a line.\n\nIf the keepers are restless, someone is trying. I need to know who.", 'default'),
        ],
        {'default': {'text': "From the Thornwardens.", 'choice': [u3, u4]}},
        topics={'nimue': "The Lady of the Lake's maiden - some say the Lady herself. Merlin taught her everything. She used it to seal him in a thorn. Whether he asked her to, nobody knows."})

# ======================================================================== The Waking Wood (18-20)
w1 = z.item("Fellwood Heart-Ring", 'ring', 18, 'ward', "A ring of heartwood, warm as skin.")
w2 = z.item("Oak-Man's Bark Bracer", 'bracer', 18, 'ward', "Bark that grew back after the blow that cut it.")
w3 = z.item("Forester's Axe-Charm", 'gem', 18, 'might', "A tiny bronze axe. Alun swears it keeps the trees polite.")
z.quest('cf_waking_wood', 'The Waking Wood', 18, 'cf_alun',
        "The oak men are walking. The fellwoods too - the great trees with faces. They're moving south, toward the deep wood, and they flatten whatever's in the way.\n\nThe old one, the Elder Fellwood, leads them. Will you [stop the Elder]? I don't know if it can be stopped.",
        'stop the Elder',
        "The oak men and fellwoods of the north-east are marching south toward the deep wood.",
        [
            hunt((1350, 300), "Cut down the walking oak men " + where((1350, 300), 'cf_alun'), 'oak man', 5),
            hunt((1154, 462), "Face the Elder Fellwood", 'Elder Fellwood', 1,
                 text="The Elder Fellwood shudders and roots itself where it stands. 'The Old Man's sleep is troubled,' it creaks. 'The wood goes to guard him.'"),
            end_talk('cf_alun', "Tell Forester Alun", "Guard him? Who - the Old Man in the thorn? So the trees know too.\n\nThe Thornwardens at the Caer should hear this.", 'default'),
        ],
        {'default': {'text': "From Alun.", 'choice': [w1, w2, w3]}})

w4 = z.item("Queen's Thistle Crown", 'gem', 20, 'charm', "A circlet of thistledown, small enough for a pixie. It fits on a finger.")
w5 = z.item("Pixie-Dust Sash", 'belt', 20, 'finesse', "It sparkles. It won't stop sparkling.")
w6 = z.item("Fae-Ward Mantle", 'cloak', 20, 'ward', "Iron thread through the weave. The fae hate it.")
z.quest('cf_pixie_queen', "The Pixie Queen's Price", 20, 'cf_elaine',
        "The pixies of the south glades are stealing the Thornwardens' charms - the ones we hang on the thorn to keep its sleep sweet. Their Queen sends them. Someone paid her.\n\nWill you [go to the Pixie Queen]? Pixies are small. Their Queen is not. Bring friends.",
        'go to the Pixie Queen',
        "The Pixie Queen of the south glades sends her pixies to steal the charms that keep Merlin's sleep.",
        [
            hunt((928, 751), "Catch the pixie thieves " + where((928, 751), 'cf_elaine'), 'pixie scout', 4),
            hunt((834, 1466), "Face the Pixie Queen", 'Pixie Queen', 1,
                 text="The Pixie Queen crumples into a heap of thistledown. In it, a red-wax seal: a key under a crown."),
            end_talk('cf_elaine', "Bring the seal to Thornwarden Elaine", "A key under a crown. The Crimson - Morgana's own. She's been loosening his sleep one charm at a time.", 'default'),
        ],
        {'default': {'text': "From the Thornwardens.", 'choice': [w4, w5, w6]}},
        requires='cf_druid_barrow', group=True)

w7 = z.item("Witch's Green Glass Ring", 'ring', 20, 'mind', "Green glass that never quite reflects your face.")
w8 = z.item("Hedge-Witch's Belt", 'belt', 20, 'charm', "Pouches of herbs, mostly harmless.")
z.quest('cf_green_witch', 'The Green Witch', 20, 'cf_gwion',
        "There's a woman in the eastern deep wood they call the Green Witch. The rangers won't pass her hut. Lately she's had visitors: men in red robes.\n\nWill you [visit the witch]?",
        'visit the witch',
        "The Green Witch of the eastern deep wood has had visitors in red robes.",
        [
            hunt((1394, 993), "Confront the Green Witch " + where((1394, 993), 'cf_gwion'), 'Green Witch', 1),
            search(Z, P(1396, 990), "Search the witch's hut", "a hut hung with green glass", CRATE,
                   "A letter, sealed with the key and crown: 'Sister - my Green Knight rides to the Caer to test their courage, as he tested Gawain's. While their eyes are on him, Accolon goes to the thorn. M.'"),
            end_talk('cf_gwion', "Bring the letter to Gwion", "Accolon. Accolon of Gaul - the knight who fought Arthur with a stolen Excalibur, at Morgana's bidding. He's long dead.\n\nAnd this Green Knight... I'll double the watch at the Caer.", 'default'),
        ],
        {'default': {'text': "From the Ulfwych Rangers.", 'choice': [w7, w8]}})

# ======================================================================== Merlin's Thorn (20-24) - the deep wood
t1 = z.item("Blood-Root Bracer", 'bracer', 21, 'might', "Root-bark, stained dark. Elaine washed it three times.")
t2 = z.item("Sacrificer's Knife-Ring", 'ring', 21, 'mind', "Cut from a sacrificer's blade. It won't cut anything now.")
z.quest('cf_blood_roots', 'Blood on the Roots', 21, 'cf_elaine',
        "Sacrificers in the deep wood - druids turned to the Crimson, and filidh with them. They bleed things over the roots that run to the thorn. The roots drink it, and the thorn loosens.\n\nWill you [stop the bleeding]?",
        'stop the bleeding',
        "Crimson sacrificers in the deep wood feed blood to the roots of Merlin's thorn.",
        [
            hunt((1368, 1299), "Kill the druid sacrificers " + where((1368, 1299), 'cf_elaine'), 'druid sacrificer', 4),
            hunt((1470, 942), "Kill the filidh sacrificers on the eastern ridge", 'filidh sacrificer', 3),
            search(Z, P(1365, 1290), "Search the sacrificers' altar", "a stone channel into the roots", CRATE,
                   "A channel cut in the stone, running red down into the roots. And painted on the altar: a key under a crown."),
            end_talk('cf_elaine', "Tell Thornwarden Elaine", "The roots will heal, given time. But she'll try the front door next. The druids' way - under the Fogou.", 'default'),
        ],
        {'default': {'text': "From the Thornwardens.", 'choice': [t1, t2]}},
        requires='cf_pixie_queen')

t3 = z.item("Fogou-Stone Charm", 'gem', 22, 'faith', "A smooth stone from the Fogou's mouth. Warm, always.")
t4 = z.item("Elithralia's Ring", 'ring', 22, 'mind', "She was a Thornwarden once. Elaine wants you to have it.")
t5 = z.item("Druids' Way Mantle", 'cloak', 22, 'ward', "Earth-brown, for walking under roots.")
z.quest('cf_druids_way', "The Druids' Way", 22, 'cf_elaine',
        "The Druids of the Fogou keep the old way under the roots - from Keltoi Fogou to the thorn. Their archdruid, Elithralia, was one of us once. If she's opened the way to the Crimson, Morgana's people can walk right up to him.\n\nWill you [close the way]? Bring a group.",
        'close the way',
        "The Druids of the Fogou keep a way under the roots from Keltoi Fogou to Merlin's thorn.",
        [
            hunt((1440, 1340), "Fight through the Druids of the Fogou " + where((1440, 1340), 'cf_elaine'), 'druid', 4),
            hunt((1459, 1333), "Face Elithralia Nodith", 'Elithralia Nodith', 1,
                 text="Elithralia falls. 'He'd want to wake,' she says. 'Anyone would. I only opened the door.'"),
            search(Z, P(1505, 1352), "Search the Fogou's mouth", "a low passage under the roots", CRATE,
                   "The passage runs north-west under the roots, toward the thorn. Fresh boot-prints in the mud, heavy, armoured - and a red cord, dropped."),
            end_talk('cf_elaine', "Tell Thornwarden Elaine", "Armoured boots, going to the thorn. Accolon's already inside the wood.\n\nThere's no more time.", 'default'),
        ],
        {'default': {'text': "From the Thornwardens.", 'choice': [t3, t4, t5]}},
        requires='cf_blood_roots', group=True)

t6 = z.item("Merlin's Thorn Twig", 'gem', 24, 'mind', "A twig from the thorn. Its flowers never close.")
t7 = z.item("Accolon's Broken Scabbard-Ring", 'ring', 24, 'might', "From the scabbard of a sword that wasn't his.")
t8 = z.item("Thornwarden's Mantle", 'cloak', 24, 'faith', "Briar-green and white. Only the Thornwardens' friends wear it.")
t9 = z.item("Prophet's Star Torc", 'neck', 24, 'mind', "Merlin's star, worked in silver. It turned up on the thorn when the fight was over.")
z.quest('cf_merlins_thorn', "Merlin's Thorn", 24, 'cf_elaine',
        "Accolon is at the thorn. I'm going there to sing the old man's sleep shut again before he can break it, and I need you to keep me alive while I do it. Bring everyone you trust.\n\nWill you [come to the thorn]?",
        'come to the thorn',
        "Accolon of Gaul has come to break Merlin's thorn. Thornwarden Elaine goes to sing it shut.",
        [
            reach(Z, P(1270, 1160), "Go to Merlin's thorn in the deep wood " + where((1270, 1160), 'cf_elaine'), "A great thorn-tree, white with flowers in every season. Something breathes inside it, slow.", r=30),
            defend(Z, (1280, 1165), "Keep Thornwarden Elaine alive while she sings",
                   "Elaine's song settles over the thorn like snow - and an armoured knight steps out of the trees.",
                   'Thornwarden Elaine', 60167630, 24, "Elaine kneels at the thorn and begins to sing. From the roots, the Crimson's sacrificers come running.",
                   [(DRUID_SAC, 'druid sacrificer', [22, 23]), (FILIDH_SAC, 'filidh sacrificer', [21, 22])], 'Keep Thornwarden Elaine alive',
                   model=F, duration=120,
                   then_boss={'tpl': KNIGHT, 'name': 'Accolon of Gaul', 'lv': 25,
                              'announce': "Accolon of Gaul, pale as a drowned man, draws a sword that glitters too brightly. 'My lady sends her regards to the old man. And to you.'"}),
            choice('cf_elaine', "Speak with Thornwarden Elaine at the thorn",
                   "It's done. He sleeps. But - listen. He's talking in his sleep. He knows we're here.\n\n'Two dragons,' he says. 'The white wakes in the south. My lady Morgan wants the gate in the lake.' We can [let him sleep] - that's our oath - or you can [ask him one question]. Just one.",
                   [('let him sleep', "Then sleep, old man. We'll keep the wood.", 'ending:sleep'),
                    ('ask him one question', "Ask, then. Quickly.\n\n...He says: 'The white dragon cannot be killed by steel alone. Seek the Afanc's lake and the giants' quarry - and do not let my sister-in-craft reach the Sleeper first.' Then nothing.", 'ending:asked')]),
        ],
        {'sleep': {'text': "From the Thornwardens.", 'items': [t8], 'choice': [t6, t7, t9]},
         'asked': {'text': "From the thorn itself.", 'items': [t9], 'choice': [t6, t7, t8]}},
        requires='cf_druids_way', group=True)
