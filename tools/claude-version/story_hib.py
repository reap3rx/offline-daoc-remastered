"""Hibernia's story quests (claude 2026-11-05) - see story_gen.py. Places: zone metres [x, y]."""
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE = 1882, 1876, 1347
M, F = 337, 365
ZONES = []

# ============================================================================================================ Lough Derg
z = Zone(200, 'Lough Derg', 3, 'hib_lough_derg')
ZONES.append(z)
z.npc('eithne', 'Eithne', [675, 194], 'f', 6, idle="He doesn't cry like my baby. He doesn't smell like my baby. He's not my baby.")
z.npc('brid', 'Wise-Woman Brid', [692, 176], 'f', 20, model=362, idle="Brew water in an eggshell in front of a changeling and it'll speak. Ask me how I know.")
z.npc('siofra', 'Siofra of the Blackthorn', [668, 762], 'f', 10, model=603, size=45, during=['changeling/siofra'])
z.npc('fergal', 'Fergal the Fisher', [634, 1140], 'm', 13, idle="Seven years she was my wife. Seven good years.")
z.npc('aoibhe', 'Aoibhe', [624, 1150], 'f', 4, size=40, idle="Mam's coming back. She said she would. She said.")
z.npc('muirne', 'Muirne of the Roane', [1318, 846], 'f', 14, during=['roane/muirne', 'roane/choose'])

it_egg = z.item('Eggshell Charm', 'gem', 7, 'charm', "A brewing eggshell, cracked and bound in silver wire. It made a changeling laugh once.")
it_thorn = z.item('Blackthorn Ring', 'ring', 7, 'might', "A ring of blackthorn wood, hard as iron, thorns turned inward. It doesn't prick. Usually.")
it_cradle2 = z.item("Cradle-Song Sash", 'belt', 7, 'mind', "Embroidered with the words of a Hibernian lullaby, and something under the words, in faerie script.")
it_fae = z.item('Fae-Milk Mantle', 'cloak', 7, 'ward', "Soft as a baby's blanket. It belonged to a faerie child, for a little while.")
z.quest('changeling', 'The Changeling', 7, 'eithne',
        "My son was taken. I know how that sounds. He's in his cradle right now, and he's not him. He's thin, and he's old in the eyes, and he never stops crying, and he never stops eating.\n\nWise-Woman [Brid] says it's a changeling - that the good folk took my Cian and left one of theirs. Will you [find Cian]? Please. Everyone else thinks I'm mad.",
        'find Cian',
        "Eithne believes her baby son was taken by the good folk and a changeling left in his cradle.",
        [
            talk('brid', 'Ask Wise-Woman Brid about changelings',
                 "She's not mad. I brewed water in an eggshell by the cradle and the thing in it sat up and said 'I'm three hundred years old, and I've never seen that.' That's a changeling. Her Cian will be with the blackthorn folk, south of town, where the [fairy fort] is.", kw='fairy fort'),
            reach(200, [666, 734], 'Go to the blackthorn fairy fort in the south', "A ring of blackthorn so thick no light gets through. Pale things move inside it, singing.", r=20),
            kill(200, [691, 748], 'Get past the lunantishee who guard the fort', 'lunantishee', 60163477, [6, 7], 5,
                 text="They don't die - they wither into thorns. The singing stops. Somewhere inside, a baby starts to cry - a human cry."),
            boss(200, [668, 760], 'Defeat the blackthorn warden', "The warden collapses into a heap of black twigs. Behind it, a cradle of woven thorn, and a fat pink baby kicking his legs.",
                 'the Blackthorn Warden', 60158473, 9, "The thorns heave and stand up into a tall, twisted shape. 'The child stays.'",
                 objective='Defeat the Blackthorn Warden', hp=2.0, adds=[(60163477, 'lunantishee', [6, 7])], every=30, count=1),
            L('siofra', talk('siofra', 'Speak with the faerie mother', "Don't take him. Not yet. Please.\n\nThe one in his cradle is MINE. My son. He was born sick - faerie children sometimes are. Only a human mother's milk can save them. Three months at your breast and he'd live. I took hers so mine could have her. I'm sorry. I'm not sorry. I'd do it again. Ask her - will she [nurse him]?", kw='nurse him', give='Cian')),
            choice('eithne', 'Bring Cian home to Eithne',
                   "CIAN. Oh - oh, my love, my lamb -\n\n...She said that? That the other one will die? Without me?\n\nI could [swap them back] tonight. Cian's home, and theirs goes back to the fort, and I never think about it again. Or I could [nurse both], until spring, and then give theirs back to her healthy. I have two arms. I don't know if I have the heart.",
                   [('swap them back', "Tonight, then. I'll leave him at the thorns at dusk. ...I'll not think about it. I'll not.", 'ending:swapped'),
                    ('nurse both', "Both. Until spring. Gods help me, he's ugly and he bites. ...Tell her. Tell her I'll keep him safe.", 'ending:both')]),
        ],
        {'swapped': {'text': "Take this. Brid says it's lucky.", 'tragic': True, 'items': [it_egg], 'choice': [it_thorn, it_cradle2]},
         'both': {'text': "Take this. The faerie mother left it on my step for you, this morning.", 'items': [it_fae], 'choice': [it_thorn, it_cradle2]}},
        topics={'Brid': "Brid lives by the well. She's delivered every baby in this town for forty years. She knows."})

it_skin = z.item('Sealskin Cloak', 'cloak', 14, 'ward', "Grey and silver, softer than any wool. It smells of the sea and it always will.")
it_pearl = z.item("Roane-Pearl Pendant", 'neck', 14, 'mind', "A grey pearl from deep water, the kind the roane give as wedding-gifts.")
it_net2 = z.item("Fergal's Net-Knot Bracer", 'bracer', 14, 'finesse', "A fisherman's bracer, knotted the way only Fergal knots.")
it_skinner = z.item("Skinner's Ring", 'ring', 14, 'might', "Taken from a dergan who skinned the roane for their pelts. Scrub it as you like.")
z.quest('roane', 'The Roane Wife', 14, 'fergal',
        "My wife Muirne was a roane - a seal-woman. Seven years ago I found her skin on the rocks and hid it, and she stayed, and married me, and we had a girl. I told myself she was happy.\n\nA month ago she found the skin in the thatch and went back to the sea. And now Aoibhe says the roane on the north-east shore are being hunted for their skins. Will you [find Muirne]? Aoibhe knows where the [chest] was.",
        'find Muirne',
        "Fergal hid his selkie wife's skin to keep her. She found it and went back to the sea - and now the roane are being hunted.",
        [
            talk('aoibhe', 'Talk to Aoibhe', "Mam's skin was in the chest. In the thatch, in a chest. She found it when the roof leaked. She cried and cried and then she kissed me and went down to the water and didn't come back. Are you going to find her? Tell her the roof's [fixed].", kw='fixed'),
            reach(200, [1185, 1035], 'Go to the north-east shore where the roane gather', "Seals in the shallows - and too many empty, bloody rocks. Something's been hunting here.", r=20),
            kill(200, [1266, 813], 'Hunt down the siabra skin-hunters', 'ghastly siabra', 60161282, [12, 13], 5,
                 text="One carries a sack of sealskins. Not Muirne's. They mention 'the big one, the grey-and-silver' - taken alive to their master."),
            search(200, [1300, 830], "Search the skin-hunters' camp", "a stack of stolen sealskins", CRATE,
                   "A dozen sealskins, salted and stacked. None of them grey-and-silver. A woman's voice, behind the tents, singing in a language like waves."),
            boss(200, [1320, 846], 'Defeat the dergan skinner', "The skinner falls on his own knives. Behind him, a woman with her arms bound, and a grey-and-silver skin across his saddle.",
                 'Maol the Skinner', 30000, 16, "A dergan in an apron of sealskin. 'The grey one's worth twenty. She's mine.'",
                 objective='Defeat Maol the Skinner', hp=2.2, adds=[(60159913, 'dergan fury', [12, 13])], every=30, count=1),
            L('muirne', talk('muirne', 'Talk to Muirne', "Fergal sent you? ...Of course. He's a kind man. He was always a kind man, except for the once.\n\nI loved him, you know. That's the cruel part. I loved him and I loved the sea, and he only gave me the choice of one. Is Aoibhe well? Is the roof [fixed]?", kw='fixed', give="Muirne's sealskin")),
            L('choose', choice('muirne', 'Help Muirne choose',
                   "I could [go home] - with my skin in my own keeping this time, and stay because I choose to. Fergal will have to live with knowing I might leave.\n\nOr I take Aoibhe [into the sea]. She's half roane. She'd learn the water in a summer. Fergal would have the house, and the boat, and the empty bed. Tell me. I've only ever been told.",
                   [('go home', "Home. With my skin under my own pillow. ...He'll learn. We both will.", 'next:home'),
                    ('into the sea', "Then I'll come for her at the next tide. Tell him gently. Tell him she'll wave from the rocks.", 'next:sea')])),
            L('home', end_talk('fergal', 'Return to Fergal', "She's home. She walked in with her skin over her arm and hung it on the peg by the door, where I can see it every day.\n\nShe says that's the bargain. I'd make it a thousand times.", 'home')),
            L('sea', end_talk('fergal', 'Return to Fergal', "She came at the tide and took Aoibhe. I watched from the door. Aoibhe waved.\n\nShe'll wave from the rocks, Muirne said. I'll be on the rocks every morning. Take this. It's from the boat. I won't fish again.", 'sea')),
        ],
        {'home': {'text': "Take this. Muirne says it was meant for a friend of the roane.", 'items': [it_pearl], 'choice': [it_net2, it_skinner]},
         'sea': {'text': "Take this.", 'tragic': True, 'items': [it_skin], 'choice': [it_net2, it_pearl]}},
        topics={'chest': "Ask Aoibhe. She's by the nets. She found it first."})

# ======================================================================================================= Silvermine Mts.
z = Zone(201, 'Silvermine Mountains', 3, 'hib_silvermine')
ZONES.append(z)
z.npc('breasal', 'Breasal the Stonemason', [570, 1074], 'm', 10, idle="My grandfather raised that circle with his own two hands. Now it's walked off.")
z.npc('grainne', 'Grainne', [552, 1093], 'f', 14, idle="Cathal went up the mountain to look for silver. The sheevra found him first.")
z.npc('odhran', 'Ranger Odhran', [580, 1066], 'm', 20, idle="The sheevra mine the east slopes. They take what they need. Lately that includes people.")
z.npc('cathal', 'Cathal', [1450, 1066], 'm', 12, during=['sheevra_mine/cathal'])

it_ogham = z.item('Ogham-Stick Charm', 'gem', 8, 'mind', "A stick notched with ogham. It reads 'wake', and then, newly carved beneath, 'sleep'.")
it_menhir2 = z.item("Mason's Plumb-Ring", 'ring', 8, 'might', "A mason's plumb-bob, worn as a ring. It always hangs true.")
it_walk = z.item('Walking-Stone Belt', 'belt', 8, 'ward', "Pebbles shed by a walking stone, strung on leather. They shift a little at night.")
it_lough = z.item("Lough-Water Cloak", 'cloak', 8, 'faith', "Damp, always, but never cold.")
z.quest('walking_stones', 'The Walking Stones', 8, 'breasal',
        "My grandfather's stone circle, up on the northern slopes - every stone of it got up and walked off last week. Seven standing stones, gone. Left their sockets like pulled teeth.\n\nThe little walking rocks have been seen west of here. Stones don't walk on their own. Someone woke them. Will you [find the stones]?",
        'find the stones',
        "Breasal's grandfather's stone circle got up and walked away. Someone woke the stones.",
        [
            reach(201, [630, 360], "Go to the empty stone circle in the north", "Seven sockets in the turf, deep and fresh. Tracks - round, heavy, rolling tracks - going south-west.", r=20),
            kill(201, [484, 706], 'Round up the walking stones', 'small walking rock', 60166254, [5, 6], 6,
                 text="They topple, and lie still, and are only stones. But there are fresh ogham marks on every one."),
            search(201, [500, 640], 'Search where the stones gathered', "a freshly carved ogham stick", CRATE,
                   "An ogham stick: 'WAKE AND WALK, IN THE NAME OF GRUGOCH.' Spraggon work - bad spelling and all.",
                   give='an ogham stick'),
            kill(201, [518, 616], "Fight through the spraggonolls", 'spraggonoll', 60166491, [7, 8], 5),
            boss(201, [470, 560], 'Confront the spraggon chief', "Grugoch sits down hard. 'Fine! FINE! They wanted to see the lough anyway! They TOLD me!'",
                 'Chief Grugoch', 60166485, 10, "A spraggon in a crown of pebbles hops onto a boulder. 'My stones! I woke them! They're MINE!'",
                 objective='Defeat Chief Grugoch', hp=2.0, adds=[(60166491, 'spraggonoll', [7, 8])], every=30, count=1),
            choice('breasal', 'Bring the ogham stick to Breasal',
                   "The spraggon said the stones WANTED to walk? To see the lough?\n\nGrandfather used to say they were restless. I thought it was a story.\n\nWith that stick I can [put them to sleep] - back in the circle, standing, forever. Or I could [let them walk] to the lough, and grandfather's circle stands empty. Gods. I'm a mason. I didn't think I'd have to ask stones what they want.",
                   [('put them to sleep', "Back in the circle, then. Sleep well, old ones. You've a job to do.", 'ending:sleep'),
                    ('let them walk', "Then I'll carve 'walk on' on the stick and leave it at the circle. ...They'll be at the lough by midsummer, I'd say. Slow walkers.", 'ending:walk')]),
        ],
        {'sleep': {'text': "Take this, for your trouble.", 'items': [it_ogham], 'choice': [it_menhir2, it_walk]},
         'walk': {'text': "Take this, for your trouble.", 'items': [it_ogham], 'choice': [it_walk, it_lough]}})

it_silver = z.item('Silver-Vein Ring', 'ring', 15, 'might', "Silvermine silver, raw and bright, from a vein no Hibernian has seen in a hundred years.")
it_pick = z.item("Miner's Pick-Bracer", 'bracer', 15, 'ward', "A pick's head, flattened and bent into a bracer.")
it_lamp2 = z.item('Deep-Lamp Pendant', 'neck', 15, 'mind', "A tiny lamp that glows faintly underground.")
it_sheevra = z.item("Sheevra Chief's Belt", 'belt', 15, 'finesse', "Studded with silver nails pulled from the Silvermine rock.")
z.quest('sheevra_mine', "The Sheevra's Miners", 15, 'grainne',
        "My husband Cathal went up the eastern slopes looking for silver. He found the sheevra instead - or they found him. Ranger [Odhran] says they've been taking men to dig for them.\n\nCathal's no fighter. He's barely a miner. Will you [bring him home]?",
        'bring him home',
        "The sheevra have been taking men to work their silver mines. Grainne's husband is one of them.",
        [
            talk('odhran', 'Ask Ranger Odhran about the sheevra',
                 "They've archers on the ridge who'll shoot anything that walks. Get past those and you'll find the miners' tracks east, deep into the hills - the sheevra work their slaves at the far [diggings].", kw='diggings'),
            kill(201, [1153, 744], 'Kill the sheevra archers on the ridge', 'sheevra archer', 60165945, [13, 14], 5),
            search(201, [1162, 762], 'Search the ridge', "a miner's broken pick", CRATE,
                   "A pick with 'CATHAL' scratched on the handle, snapped in two. Chain-marks in the dirt, heading east."),
            reach(201, [1440, 1050], "Find the sheevra's far diggings", "A raw hole in the hillside. Men in chains, hauling rock. Sheevra overseers with whips.", r=20),
            defend(201, [1450, 1060], 'Free the miners', "The sheevra break and run. The miners drop their chains and sit down, laughing and crying.",
                   'Cathal', 60165947, 12, "You strike the first chain off, and every sheevra in the diggings comes running.",
                   [(60165947, 'sheevra miner', [13, 14])], 'Keep Cathal alive', model=M, duration=80,
                   then_boss={'tpl': 60165946, 'name': 'Chieftain Morc', 'lv': 17, 'announce': "A sheevra in a silver helm. 'My diggers. My silver. MINE.'", 'objective': 'Defeat Chieftain Morc'},
                   thanks="Is it over? Is it really?"),
            L('cathal', choice('cathal', 'Talk to Cathal',
                   "I found it, you know. The vein. That's why they kept me. Silver like nobody's seen since my grandfather's day - enough to make Grainne and me rich ten times over.\n\nIf we [claim the vein], the sheevra will come back for it. Every year. We'd need guards and walls and we'd never sleep easy. Or we [collapse the mine], and go home poor, and nobody fights over it ever again.",
                   [('claim the vein', "Then I'll stake it today. Grainne will kill me. And then she'll buy a cow. Ten cows.", 'next:claim'),
                    ('collapse the mine', "...Help me with the props. There. Listen to it go. ...Let's go home.", 'next:collapse')])),
            L('claim', end_talk('grainne', 'Return to Grainne', "He's home, and he's RICH, and he's hired six men with spears to guard a hole in a hill.\n\nThe sheevra will come back. He knows. I know. I married a fool. A rich fool. Here - take a share.", 'claim')),
            L('collapse', end_talk('grainne', 'Return to Grainne', "He brought the mountain down on it. All that silver, and he buried it.\n\nAnd then he came home and slept for two days, and when he woke up he asked me what was for supper, like nothing happened. I've never loved him more.", 'collapse')),
        ],
        {'claim': {'text': "Take a share.", 'items': [it_silver], 'choice': [it_pick, it_sheevra]},
         'collapse': {'text': "Take this.", 'items': [it_lamp2], 'choice': [it_pick, it_sheevra]}},
        topics={'Odhran': "The ranger. He's by the stables. He's been watching the east slopes all season."})

# ======================================================================================================= Shannon Estuary
z = Zone(202, 'Shannon Estuary', 3, 'hib_shannon')
ZONES.append(z)
z.npc('maeve_widow', 'Maeve', [240, 690], 'f', 9, idle="Three years. I still set his place at table.")
z.npc('harbourmaster', 'Harbourmaster Cian', [226, 664], 'm', 18, idle="Ships come in, ships go out. Some don't come back. That's the sea.")
z.npc('niall_ghost', 'the ghost of Captain Niall', [192, 574], 'm', 12, model=M, during=['false_light/niall'])
z.npc('brehon_aodh', 'Brehon Aodh', [980, 1580], 'm', 30, idle="The law is the law. Even when it's ours that broke it.")
z.npc('iasc', 'Iasc the Ferryman', [970, 1572], 'm', 18, idle="Ferry's free, for now. The eriu haven't come down the river yet.")
z.npc('orla', 'Orla', [1006, 1132], 'f', 20, during=['eriu_hostage/orla', 'eriu_hostage/s5', 'eriu_hostage/s6'])

it_light = z.item('False-Light Lantern Charm', 'gem', 10, 'mind', "A little glass ball with a sheerie's light trapped in it. It lies about where it is.")
it_star = z.item('Morning Star Ring', 'ring', 10, 'might', "Carved from the figurehead of a wrecked ship.")
it_drift = z.item('Driftwood Bracer', 'bracer', 10, 'ward', "Silver-grey wood that once walked the shore at night.")
it_widow = z.item("Widow's Shawl", 'cloak', 10, 'faith', "Black wool. Maeve wore it for three years.")
z.quest('false_light', 'The False Light', 10, 'maeve_widow',
        "Three years ago my husband's ship, the Morning Star, went down off the beach in calm weather. Calm! Now the driftwood from her walks the shore at night - it's haunted, the children say.\n\nI'm not a fool. But I'd like to know. Will you [find out] what happened to the Morning Star? The [harbourmaster] might help you, if he's sober.",
        'find out',
        "Maeve's husband's ship sank three years ago in calm weather. Its driftwood now walks the shore at night.",
        [
            kill(202, [262, 725], 'Lay the haunted driftwood to rest', 'haunted driftwood', 60162022, [7, 8], 4,
                 text="On the last piece, carved deep, the ship's name: MORNING STAR. And scratched below it, fresh: 'LIGHTS. FALSE LIGHTS.'"),
            talk('harbourmaster', 'Ask the harbourmaster about the wreck',
                 "False lights? ...Aye, the crew that washed up said they followed a light into the shallows - thought it was the harbour lamp. It wasn't. The moss sheerie on the south shore do that, for sport. Captain Niall's body was never found. The [wreck]'s still on the northern sands.", kw='wreck'),
            search(202, [189, 571], 'Search the wreck on the northern sands', "the Morning Star's figurehead", CRATE,
                   "The figurehead, half-buried. A woman with a star on her brow. Maeve's face - he had it carved like her. Behind it, something pale and wet is standing very still."),
            kill(202, [324, 1109], 'Hunt down the moss sheerie on the south shore', 'moss sheerie', 30002, [8, 9], 5,
                 text="Their lights go out one by one. One is brighter than the rest, bobbing away to the south."),
            boss(202, [330, 1120], 'Put out the false light', "The false light gutters and goes out. On the northern sands, far behind you, something sighs.",
                 'the False Light', 30002, 12, "A sheerie brighter than a harbour lamp rises out of the moss. 'Follow me, sailor. Follow me home.'",
                 objective='Put out the False Light', hp=2.2, adds=[(30002, 'moss sheerie', [8, 9])], every=30, count=1),
            L('niall', talk('niall_ghost', "Go back to the wreck", "You put out the light. Thank you. I've been standing here three years waiting for someone to.\n\nI couldn't go to her. Not with the light still burning - it kept calling me back into the water. Is she well? Does she still set my place at [table]?", kw='table')),
            choice('maeve_widow', 'Tell Maeve what you found',
                   "He's there? On the sand? Niall?\n\nWhat does he want? Did he say?\n\n(He asked you to tell her one of two things. That she should [let him go] - put away the shawl, take down his place, and marry again. Or that she should [wait for him] at the wreck on the long nights, and he'll come.)",
                   [('let him go', "Let him go. ...He would say that. He always wanted me to be happy more than he wanted me. I'll take the shawl off tomorrow. Tonight I'll go and say goodbye.", 'ending:go'),
                    ('wait for him', "On the long nights. At the wreck. ...Then I'll wait. I'm good at waiting. I've had practice.", 'ending:wait')]),
        ],
        {'go': {'text': "Take this. I won't need it now.", 'items': [it_widow], 'choice': [it_star, it_drift]},
         'wait': {'text': "Take this, from the ship.", 'tragic': True, 'items': [it_light], 'choice': [it_star, it_drift]}},
        topics={'harbourmaster': "Cian, on the quay. He's been harbourmaster thirty years. He drinks."})

it_treaty = z.item('Treaty-Stick Charm', 'gem', 20, 'mind', "An ogham treaty-stick, mended with silver wire.")
it_eriu = z.item('Eriu Fishing-Torc', 'neck', 20, 'might', "Bronze, twisted like rope, the way the eriu make everything.")
it_brehon = z.item("Brehon's Ring", 'ring', 20, 'faith', "A judge's ring. Aodh gave you his spare.")
it_orla = z.item("Orla's Woven Belt", 'belt', 20, 'finesse', "Eriu weaving, taught to Orla in captivity. She's better at it than they are.")
z.quest('eriu_hostage', 'The Eriu Hostage', 20, 'brehon_aodh',
        "Five years ago this town made a treaty with the eriu upriver: our boats keep below the ford, theirs above. My daughter Orla went to them as surety - a hostage, by the old law. She was ten.\n\nLast month someone fished above the ford. Now the eriu say the treaty's broken and the hostage forfeit. Will you [bring Orla home]? Ask [Iasc] the ferryman - I think he knows who broke it.",
        'bring Orla home',
        "Brehon Aodh's daughter has been a hostage with the eriu for five years. Now someone has broken the treaty.",
        [
            talk('iasc', 'Ask Iasc the ferryman about the broken treaty',
                 "I know who fished above the ford. Me. The run was poor below and my children were hungry. I didn't think they'd notice one boat. I didn't think - about Orla. Gods forgive me. The eriu camp's up the [river].", kw='river'),
            kill(202, [1010, 1140], 'Fight through the eriu henters', 'eriu henter', 60160565, [19, 20], 5,
                 text="They fight hard but they don't hate you. 'The law,' one says as he falls. 'Your people broke the law.'"),
            search(202, [1000, 1150], 'Search the eriu war-camp', "a broken treaty-stick", CRATE,
                   "The ogham treaty-stick, snapped clean in two. It was the town's own copy. The eriu will have the other. Beside it, a girl's footprints - free, unchained, pacing."),
            L('orla', talk('orla', 'Find Orla', "Father sent you? Of course he did. He's very proper.\n\nThey've been good to me, you know. Five years. They taught me to weave and to fish and to sing their songs. And now they'll kill me, because the law says so. They don't want to. Their chief will come for me at [dusk].", kw='dusk')),
            boss(202, [1006, 1128], "Stand against the eriu chief", "The eriu chief kneels. 'Then it's done. The law's been answered with blood. Take her.'",
                 'Chief Dorchadh of the Eriu', 60160566, 23, "An old eriu in a cloak of fish-scale. 'I'm sorry, girl. The law is the law.'",
                 objective='Defeat Chief Dorchadh', hp=2.4, adds=[(60160565, 'eriu henter', [19, 20])], every=25, count=2),
            choice('orla', 'Decide with Orla',
                   "He's beaten, but they'll choose another chief by the next moon. And the treaty's still broken.\n\nFather could [renew the treaty] - pay the eriu the old fine for the broken one. It would ruin him. Or we go home and let the eriu come for [war], if they want it. They might not. They might.\n\nWhat should I tell him?",
                   [('renew the treaty', "Then I'll tell him to pay. And I'll go back to them myself, after, to say goodbye properly. They were my family too.", 'next:treaty'),
                    ('war', "War, then. Gods. I'll tell him. He won't like it either way.", 'next:war')]),
            L('treaty', end_talk('brehon_aodh', 'Return to Brehon Aodh', "She's home. And the treaty is renewed - at a price that's cost me my house and two fields.\n\nIasc came to me and wept and offered his boat. I took it, and gave it back to him. The law is satisfied. So am I.", 'treaty')),
            L('war', end_talk('brehon_aodh', 'Return to Brehon Aodh', "She's home. That's what matters.\n\nThe eriu have sent a war-arrow down the river. The town's arming. Orla stands at the window looking upriver, and won't tell me what she's thinking. Here. For bringing her back.", 'war')),
        ],
        {'treaty': {'text': "Take this, with the law's thanks.", 'items': [it_treaty], 'choice': [it_brehon, it_orla]},
         'war': {'text': "For bringing her back.", 'tragic': True, 'items': [it_eriu], 'choice': [it_brehon, it_orla]}},
        topics={'Iasc': "The ferryman, by the river. He hasn't met my eye in a month."})

# ======================================================================================================= Cliffs of Moher
z = Zone(203, 'Cliffs of Moher', 3, 'hib_cliffs_of_moher')
ZONES.append(z)
z.npc('sorcha', 'Sorcha', [664, 514], 'f', 16, idle="I saw myself on the cliffs. Myself. Smiling at me.")
z.npc('lorcan', 'Old Lorcan', [676, 500], 'm', 30, model=362, idle="A fetch at morning means long life. At evening, death. Nobody wants to say which it was.")
z.npc('nuala', 'Nuala the Net-Mender', [672, 498], 'f', 34, idle="Every seventh year the sea takes a child. We call it the sea. It isn't the sea.")
z.npc('fintan', 'Fintan', [168, 1056], 'm', 12, size=42, during=['koalinth_pact/fintan'])

it_fetch = z.item("Fetch-Glass Pendant", 'neck', 18, 'mind', "A little mirror that shows you a moment late. You get used to it.")
it_comb = z.item("Sorcha's Comb-Pin", 'gem', 18, 'charm', "A comb of white bone. The fetch carried it; it is the only thing of hers it took.")
it_bocan = z.item('Bocan-Hide Bracer', 'bracer', 18, 'might', "The bocan are goblins of the cliffs. This one's hide is tough as boot-leather.")
it_cliff = z.item("Cliff-Walker's Cloak", 'cloak', 18, 'ward', "Grey wool, weighted at the hem against the cliff wind.")
z.quest('fetch', 'The Fetch', 18, 'sorcha',
        "Three evenings ago I saw myself on the cliff path. My own face, my own shawl - walking toward me, smiling. Then gone.\n\nA fetch, Old [Lorcan] says. At evening, it means death. I'm twenty-two. Will you [find it]? Find it and - I don't know. Make it stop smiling.",
        'find it',
        "Sorcha saw her own fetch - her double - on the cliffs at evening. An omen of death.",
        [
            talk('lorcan', 'Ask Old Lorcan about fetches',
                 "A fetch is the shape of a death, walking about early. Find it before it finds her, and kill it, and maybe the death goes elsewhere. Maybe. They walk the eastern cliffs where the [bocan] nest - those goblins will warn it you're coming, so deal with them first.", kw='bocan'),
            kill(203, [850, 1200], 'Clear the bocan from the cliff path', 'bocan', 60158578, [15, 16], 5,
                 text="One of them chatters something about 'the smiling lady' going east."),
            reach(203, [1116, 1240], 'Follow the cliff path east', "Fetches drift on the clifftops - pale doubles of the living, wearing borrowed faces. None of them is hers. Yet.", r=20),
            kill(203, [1116, 1246], 'Destroy the drifting fetches', 'fetch', 60160819, [16, 17], 4),
            search(203, [1130, 1252], 'Search the cliff edge', "a white bone comb", CRATE,
                   "Sorcha's comb, still warm. And standing at the very edge of the cliff, looking out to sea: Sorcha. Smiling."),
            boss(203, [1124, 1250], "Destroy Sorcha's fetch", "The fetch stops smiling. For a moment it looks only tired, and very sad, and then it's mist.",
                 "Sorcha's Fetch", 60160819, 20, "It turns. It has her face exactly, and her voice: 'You're early.'",
                 objective="Destroy Sorcha's fetch", model=F, hp=2.2, adds=[(60160819, 'fetch', [16, 17])], every=30, count=1),
            choice('sorcha', 'Return to Sorcha',
                   "Is it gone? It is, isn't it. I can feel it. Like a weight off.\n\nIt said something. Before. I can see it in your face. What did it say?\n\n(The fetch said: 'You can't kill a death. Only move it. Someone else will walk off this cliff by Samhain.' You could tell her [the truth], or [say nothing].)",
                   [('the truth', "...Someone else. In my place. Gods. Then I'll watch the cliff path every evening until Samhain, and turn back whoever I see. I owe them that.", 'ending:truth'),
                    ('say nothing', "Nothing? It just went? ...Then I'm free. I'm free. I'm going to go dancing tonight. Come with me!", 'ending:silent')]),
        ],
        {'truth': {'text': "Take this. It's mine to give, now.", 'items': [it_comb], 'choice': [it_fetch, it_bocan]},
         'silent': {'text': "Take this. And come dancing.", 'tragic': True, 'items': [it_comb], 'choice': [it_cliff, it_bocan]}},
        topics={'Lorcan': "Old Lorcan, by the well. He knows every omen there is, and believes in half of them."})

it_koal = z.item('Koalinth-Scale Token', 'gem', 36, 'mind', "A blue-green scale, pierced and hung on a cord. The koalinth give them to children they claim.")
it_pact = z.item("Pact-Breaker's Ring", 'ring', 36, 'might', "Cut from the koalinth tide-caller's own hand.")
it_tide = z.item('Tide-Caller Mantle', 'cloak', 36, 'faith', "Woven of kelp and something finer. Water runs off it like off a seal.")
it_spear = z.item("Spearman's Bracer", 'bracer', 36, 'finesse', "Cliff-dweller work, bone and sinew.")
z.quest('koalinth_pact', 'The Seventh Year', 36, 'nuala',
        "Every seventh year, a child of this village is lost to the sea. Swept off the rocks. We mourn them and we say it's the sea.\n\nThis is the seventh year, and last night my son Fintan was gone from his bed. Wet footprints on the floor - not his. Webbed. Will you [find Fintan]? Start at the old fishing camp on the west cliffs. That's where the last one went.",
        'find Fintan',
        "Every seventh year a child of Nuala's village is lost to the sea. This year it was her son - and the footprints were webbed.",
        [
            reach(203, [215, 630], 'Go to the old fishing camp on the west cliffs', "The camp's been empty for years. On the door of the hut, scratched faintly: seven lines, and then seven more, and then seven more.", r=20),
            kill(203, [191, 828], 'Fight through the cliff dweller spearmen', 'cliff dweller spearman', 60159247, [36, 37], 5,
                 text="The cliff dwellers fight like men defending something. When the last one falls, he says: 'The pact. You'll break the pact.'"),
            search(203, [212, 636], "Search the fishing camp's hut", "a koalinth-scale token", CRATE,
                   "A child's token, on a cord: a blue-green scale. Under the floorboards, a ledger in a careful hand - the village elders' hand. A name every seven years. And next to each: 'Good fishing.'",
                   give="the elders' ledger"),
            kill(203, [172, 1047], 'Fight through the koalinth on the southern rocks', 'koalinth slinker', 60162948, [35, 36], 5),
            boss(203, [160, 1060], 'Defeat the koalinth tide-caller', "The tide-caller falls back into the surf. On the rocks behind it, a boy in a koalinth's cloak blinks at you.",
                 'Tide-Caller Mairgread', 60162948, 40, "A koalinth with a crown of shells rises from the waves. 'The pact is old. The pact is fair. The boy is ours.'",
                 objective='Defeat the Tide-Caller', hp=2.5, adds=[(60162948, 'koalinth slinker', [35, 36])], every=25, count=2),
            L('fintan', talk('fintan', 'Talk to Fintan', "They were nice to me. They said I'd learn to breathe water. They said the other children did. Is Mam angry? Can I go [home]?", kw='home')),
            choice('nuala', 'Bring Fintan home to Nuala',
                   "FINTAN. Oh, my love.\n\n...And this? A ledger? In Old Eoghan's hand? 'Good fishing'?\n\nThey SOLD them. Every seventh year. My grandmother's sister - she's in here. I could [expose the elders] in front of the whole village. Or I could [burn the ledger], and keep my son, and keep the peace. They're old men. Half of them are dying.",
                   [('expose the elders', "In front of everyone. At the harbour, at noon. Let them look at every mother in this village and explain.", 'ending:exposed'),
                    ('burn the ledger', "Into the fire. ...There. My son's home. The rest is the sea's business. I'll keep it that way. Gods forgive me.", 'ending:burned')]),
        ],
        {'exposed': {'text': "Take something. The village owes you more than it can pay.", 'items': [it_pact], 'choice': [it_tide, it_spear]},
         'burned': {'text': "Take something. And don't speak of it.", 'tragic': True, 'items': [it_koal], 'choice': [it_tide, it_spear]}})

# ============================================================================================================= Lough Gur
z = Zone(204, 'Lough Gur', 3, 'hib_lough_gur')
ZONES.append(z)
z.npc('tadhg_inn', 'Tadhg the Innkeeper', [1190, 1006], 'm', 22, idle="Grandfather's harp hung over the bar sixty years. The luck of the house. Gone.")
z.npc('dara', 'Dara the Potboy', [1182, 1002], 'm', 12, idle="I didn't drink anything. Much.")
z.npc('ciaran_bard', 'Ciaran the Bard', [312, 200], 'm', 30, idle="My brother was the better poet. Ask anyone. Ask him - when he's sane.")
z.npc('eoin', 'Eoin', [428, 1124], 'm', 30, during=['amadan/eoin'])

it_harp2 = z.item("Inn-Luck Harp Charm", 'gem', 23, 'charm', "A tiny harp of bog-oak. The luck of a house sixty years old is in it.")
it_ale = z.item('Ale-Belly Girdle', 'belt', 23, 'ward', "The cluricaun king's belt. Let out several times.")
it_luch2 = z.item('Luch-Rider Bracer', 'bracer', 23, 'finesse', "Cluricauns ride the giant luch like ponies. This is from a saddle.")
it_cellar = z.item("Cellar-Key Ring", 'ring', 23, 'might', "The key to Tadhg's cellar, made into a ring. It opens other cellars too, you suspect.")
z.quest('cluricaun', "The Cluricaun's Harp", 23, 'tadhg_inn',
        "The cluricauns have been in my cellar every night since spring - drinking, singing, breaking things. I let it go. Every inn has cluricauns.\n\nBut three nights ago they took my grandfather's harp from over the bar. The luck of the house. Since then the ale's gone sour and the roof leaks. Will you [get the harp back]? Dara the [potboy] saw them go.",
        'get the harp back',
        "Cluricauns stole the harp that has hung over Tadhg's bar for sixty years - the luck of the house.",
        [
            talk('dara', 'Ask Dara the potboy what he saw',
                 "They came up out of the cellar riding luch - giant mice! - and one of them had the harp, and they all went north-east singing. I followed a bit. They've a sort of camp out past the luch runs, in the [north-east].", kw='north-east'),
            kill(204, [1290, 700], 'Deal with the cluricauns\' luch mounts', 'large luch', 60163146, [20, 21], 5),
            search(204, [1236, 646], 'Search the cluricaun camp', "a trail of spilled ale and a harp string", CRATE,
                   "A harp string, snapped, and a lake of spilled ale. Drunken singing, very close."),
            kill(204, [1244, 633], 'Fight through the drunken cluricauns', 'cluricaun', 60159264, [21, 22], 5),
            boss(204, [1240, 630], 'Defeat the cluricaun king', "The cluricaun king sits down, hiccups, and says: 'Fine. Take it. It's ours, though. Ask the innkeeper's grandda.'",
                 'King Fiachra Ale-Belly', 60159264, 26, "A very fat cluricaun with a harp under one arm and a barrel under the other. 'MY harp! Get yer own!'",
                 objective='Defeat King Fiachra', hp=2.2, adds=[(60159264, 'cluricaun', [21, 22])], every=25, count=2, ),
            choice('tadhg_inn', 'Bring the harp back to Tadhg',
                   "The harp! Oh, thank the gods - wait. What did he say? That it was THEIRS?\n\n...Grandfather did say he won it at dice. From a very small man. In a cellar. I thought it was a story.\n\nIf it's theirs, I should [give it back]. The luck of the house goes with it. Or I [keep it], and the cluricauns can sulk. It's been over that bar sixty years.",
                   [('give it back', "Back it goes. I'll leave it in the cellar tonight with a barrel of the good stuff. ...They'll be back for that barrel every week, you know.", 'ending:returned'),
                    ('keep it', "It stays. Sixty years is ownership. ...The ale's already sweeter. Listen to that roof - not a drip.", 'ending:kept')]),
        ],
        {'returned': {'text': "Take something. The cluricauns left this in the cellar for you - I think it's a thank you.", 'items': [it_ale], 'choice': [it_luch2, it_cellar]},
         'kept': {'text': "Take something from behind the bar.", 'items': [it_harp2], 'choice': [it_luch2, it_cellar]}},
        topics={'potboy': "Dara. He's wiping tables. He's always wiping tables."})

it_madness = z.item("Amadan's Straw Crown", 'gem', 33, 'mind', "A crown of straw that the amadan wore. Whoever wears it hears music nobody else can.")
it_verse = z.item('Verse-Book Clasp', 'belt', 33, 'faith', "From Eoin's book of poems. Every page is full, and none of it makes sense, and all of it is beautiful.")
it_gurite = z.item('Gurite Waylayer Ring', 'ring', 33, 'finesse', "Taken off a gurite who robbed travellers on the south road.")
it_alp = z.item("Alp-Luachra Hide Cloak", 'cloak', 33, 'ward', "The alp luachra are newts that crawl into sleepers' mouths. The hide is very good leather.")
z.quest('amadan', "The Amadan's Touch", 33, 'ciaran_bard',
        "My brother Eoin was touched by the amadan - the faerie fool - last autumn. One touch, and he walked into the southern woods laughing and never came out.\n\nHe was the better poet. Everyone said so. I want him back, even mad. Will you [find Eoin]? The road south is thick with gurite, so be careful.",
        'find Eoin',
        "Ciaran's brother, a poet, was touched by the amadan - the faerie fool - and walked laughing into the southern woods.",
        [
            reach(204, [440, 940], 'Take the road into the southern woods', "Gurite waylayers watch the road from the trees. Further on, someone is laughing.", r=20),
            kill(204, [465, 948], 'Kill the gurite waylayers on the south road', 'gurite waylayer', 60161874, [30, 31], 5),
            kill(204, [290, 1079], 'Clear the alp luachra from the sleeping-hollow', 'alp luachra', 60157767, [30, 31], 4,
                 text="Under the leaves where they nested: a sleeping man's footprints, many nights over. He sleeps here, sometimes."),
            search(204, [420, 1118], 'Search the touched folk\'s camp', "a book of poems, rain-soaked", CRATE,
                   "Eoin's book. Every page is full of verse in a dozen hands, all his. The last page: 'The fool says I may go home if someone fetches me. Nobody fetches me.'",
                   give="Eoin's book of poems"),
            L('eoin', talk('eoin', 'Talk to Eoin', "Ciaran! No - you're not Ciaran. You smell of the road. Ha!\n\nI'm quite mad, you know. It's lovely. Every word I've written since is better than everything before. The fool won't let me go until somebody beats him at his own game. His game is [hitting].", kw='hitting')),
            boss(204, [430, 1130], 'Defeat the amadan', "The amadan falls over laughing, and doesn't get up. All around, the touched folk sit down and blink, as if waking.",
                 'the Amadan of the Hollow', 60157791, 36, "A ragged man in a straw crown capers out of the trees. 'A new game! A new player! TOUCH!'",
                 objective='Defeat the Amadan', hp=2.5, adds=[(60157791, 'amadan touched', [29, 30])], every=25, count=2),
            choice('ciaran_bard', 'Bring Eoin home to Ciaran',
                   "Eoin. EOIN. You're - he's -\n\n...He's sane? He knows me? He's crying. Why is he crying?\n\nHe says the poems stopped when the fool died. He says he's empty. He says he wants to [go back] to the woods with the other touched folk, and look after them. Or I could [keep him home] until he's well. I've waited a year. You decide. I can't trust myself.",
                   [('keep him home', "Then he stays. He'll write again. Plain words, maybe, but his. And I'll be the better poet for once, ha. ...Ha.", 'ending:home'),
                    ('go back', "Then go, brother. Go and look after them. I'll bring you paper every new moon. Whatever you write, I'll read.", 'ending:woods')]),
        ],
        {'home': {'text': "Take something. Eoin wants you to have this.", 'items': [it_verse], 'choice': [it_gurite, it_alp]},
         'woods': {'text': "Take something.", 'tragic': True, 'items': [it_madness], 'choice': [it_gurite, it_alp]}})

# ========================================================================================================= Bog of Cullen
z = Zone(205, 'Bog of Cullen', 3, 'hib_bog_of_cullen')
ZONES.append(z)
z.npc('fiona_harper', 'Fiona the Harper', [232, 945], 'f', 40, idle="Lorcan wrote me a poem every day for a year. Then he wrote them for someone else.")
z.npc('lorcan_poet', 'Lorcan the Poet', [802, 1146], 'm', 40, during=['lhiannan/lorcan', 'lhiannan/verses'])
z.npc('sadhbh', 'Old Sadhbh', [1300, 1328], 'f', 48, model=362, guild='Keener', idle="I've keened for three chieftains. The banshee keened first, every time.")
z.npc('steward_conn', 'Steward Conn', [1318, 1334], 'm', 46, idle="The Chieftess is well. Perfectly well. Please don't trouble her.")
z.npc('banshee_npc', 'the Banshee of Cullen', [1000, 1352], 'f', 55, model=F, during=['keening/banshee'])

it_muse = z.item("Muse's Kiss Pendant", 'neck', 42, 'mind', "Cold silver, shaped like lips. It whispers rhymes.")
it_verses = z.item('Burnt-Verse Ring', 'ring', 42, 'faith', "Ash from a burned book of poems, sealed in glass.")
it_siabra = z.item("Wayguard's Bracer", 'bracer', 42, 'might', "Siabra bog-iron, cold and heavy.")
it_creeper = z.item('Bog-Creeper Cloak', 'cloak', 42, 'ward', "Woven from the vines of bog creepers. It moves a little on its own.")
z.quest('lhiannan', 'The Lhiannan-Sidhe', 42, 'fiona_harper',
        "Lorcan was my lover and the finest poet in Cullen. Last spring a lhiannan-sidhe found him - a faerie muse. They give a poet the best verses he'll ever write, and they drink his life to do it.\n\nHe wrote to me last month, from somewhere in the bog. The writing was an old man's. He's thirty. Will you [find Lorcan]?",
        'find Lorcan',
        "A lhiannan-sidhe - a faerie muse who feeds on poets - has taken Fiona's lover into the bog.",
        [
            reach(205, [570, 810], 'Go into the bog by the siabra tower', "Siabra watch from the tower. Pages of verse are stuck to the reeds, soaked, the ink running.", r=20),
            kill(205, [503, 819], 'Fight through the siabra wayguards', 'siabra wayguard', 60165995, [42, 43], 5),
            search(205, [560, 800], 'Gather the scattered verses', "pages of verse in a shaking hand", CRATE,
                   "Each page better than the last, and each hand older. The last pages are nearly illegible - and nearly perfect.", give="Lorcan's verses"),
            kill(205, [555, 918], 'Cut through the bog creepers to the east', 'bog creeper', 60158591, [42, 43], 5),
            L('lorcan', talk('lorcan_poet', 'Find Lorcan', "Fiona sent you. Fiona. I wrote her a hundred poems and none of them were good enough. Now I write for HER, and every one is perfect.\n\nShe'll come at dusk. Look at me. I'm thirty. I don't care. I don't care. Do you understand - every [word]...", kw='word')),
            boss(205, [800, 1150], 'Drive off the lhiannan-sidhe', "The lhiannan-sidhe falls back, hissing, into the mist. Lorcan clutches his chest and breathes like a man surfacing from deep water.",
                 'the Lhiannan-Sidhe', 60163259, 46, "A woman more beautiful than the moon walks out of the mist. 'He is mine. He is my masterpiece.'",
                 objective='Drive off the Lhiannan-Sidhe', hp=2.6, adds=[(60158591, 'bog creeper', [42, 43])], every=25, count=2),
            L('verses', choice('lorcan_poet', 'Decide what becomes of the verses',
                   "She's not gone. Not while I have the verses. They're hers as much as mine - she lives in them. If I [burn the verses], I'm free, and I'll go back to Fiona and write bad poems and grow old slowly.\n\nIf I [keep them], she'll come back, and I'll die before winter, and they'll sing these in every hall in Hibernia for a thousand years. Choose. Please. I can't.",
                   [('burn the verses', "...They burn so slowly. ...There. I can't remember a line. Not one. Take me to Fiona.", 'next:burned'),
                    ('keep them', "Then I'll keep them. Tell Fiona the best ones are hers. They are. Tell her I'm sorry.", 'next:kept')])),
            L('burned', end_talk('fiona_harper', 'Return to Fiona', "He's home. He's grey and thin and he can't remember a word he wrote - and he wrote me a poem this morning. It's terrible. It's the best thing I've ever read.", 'burned')),
            L('kept', end_talk('fiona_harper', 'Return to Fiona', "He kept them. And he sent me the best ones.\n\nThey're... they're beyond anything. I'll set them to music. I'll play them at his wake, which will be before winter. Take this, and go, before I cry on you.", 'kept')),
        ],
        {'burned': {'text': "Take this. He wanted you to.", 'items': [it_verses], 'choice': [it_siabra, it_creeper]},
         'kept': {'text': "Take this, and go.", 'tragic': True, 'items': [it_muse], 'choice': [it_siabra, it_creeper]}})

it_keen = z.item("Keener's Veil", 'cloak', 50, 'faith', "Sadhbh's own. She has keened for three chieftains in it.")
it_vial = z.item('Poisoner\'s Vial Pendant', 'neck', 50, 'mind', "Empty now. The glass is very fine - sidhe glass.")
it_venator = z.item("Venator's Ring", 'ring', 50, 'finesse', "From the hand of a siabra assassin.")
it_wraith = z.item('Black Wraith Bracer', 'bracer', 50, 'might', "The black wraiths of Cullen are the dead who drowned in the bog. This one wore iron.")
it_dana = z.item("Chieftess Dana's Brooch", 'gem', 50, 'charm', "The Chieftess' own brooch, given in thanks.")
z.quest('keening', 'The Keening', 50, 'sadhbh',
        "This is GROUP work, so bring friends you trust.\n\nThe banshee of Cullen has keened under the Chieftess' window every night for a week. A banshee keens for a death in the old families. But nobody is sick. Nobody is old. Nobody's dying.\n\nWhen a banshee keens for a death that hasn't come, it's because someone means to make it come. Will you [find out who]? Start with the [steward]. He's too calm.",
        'find out who',
        "GROUP. The banshee of Cullen keens nightly for the Chieftess - who isn't sick. Someone means her death.",
        [
            talk('steward_conn', 'Question Steward Conn',
                 "The banshee? Old women's stories. The Chieftess is perfectly well. I see to everything - her food, her wine, her guests. I'd know if anything were wrong.\n\nIf you must poke about, the black wraiths in the bog to the [east] have been bold of late. Go and deal with them. That would actually be useful.", kw='east'),
            kill(205, [1404, 1285], 'Deal with the black wraiths east of town', 'black wraith', 60158463, [48, 49], 4,
                 text="Among the wraith-mud, a dropped satchel - a steward's satchel, with a steward's seal."),
            search(205, [1392, 1300], 'Search the dropped satchel', "a steward's satchel", CRATE,
                   "A vial of sidhe glass, nearly empty. A letter: 'Half in her wine each night. By the dark moon it will look like a wasting. The venator will finish it if it doesn't. - C.'",
                   give="the poisoner's vial"),
            reach(205, [1010, 1350], "Find the banshee's keening-stone", "A grey woman sits on a stone in the bog, combing her hair, weeping. She looks up at you.", r=20),
            L('banshee', talk('banshee_npc', 'Speak with the banshee', "You hear me. Good. Few do, before.\n\nThe Chieftess' death is close. The steward pours it. And the siabra hunter waits in the bog to the west of my stone, to finish it if the poison is slow. Stop the [hunter]. I am so tired of keening.", kw='hunter')),
            boss(205, [990, 1340], 'Kill the siabra assassin in the bog', "The venator dies in the bog-water. Far off, under the Chieftess' window, the keening stops.",
                 'Iuchra the Venator', 60165994, 54, "A siabra in mud-grey leathers rises out of the bog with a knife in each hand. 'The steward pays well. You'll do for practice.'",
                 objective='Kill Iuchra the Venator', hp=3.0, adds=[(60165994, 'siabra venator', [47, 48])], every=25, count=2),
            choice('sadhbh', 'Return to Old Sadhbh',
                   "The keening's stopped. I heard it stop at moonrise. And you have the vial. Conn.\n\nConn, who has served her twenty years. He wanted the chieftainship for his son - it's in his letters.\n\nThe Chieftess is too kind. She'll want to [banish him]. The old law says [death] for a poisoner. She'll ask me, and I'll ask you. You've seen more of it than I have.",
                   [('banish him', "Banished. Beyond the Shannon, with nothing but his cloak. ...She'll weep for him. She's like that.", 'ending:banished'),
                    ('death', "The old law, then. I'll keen for him myself. Somebody should.", 'ending:death')]),
        ],
        {'banished': {'text': "From the Chieftess, with her thanks.", 'items': [it_dana], 'choice': [it_keen, it_venator, it_wraith]},
         'death': {'text': "From the Chieftess.", 'tragic': True, 'items': [it_vial], 'choice': [it_keen, it_venator, it_wraith]}},
        topics={'steward': "Conn. He runs the Chieftess' household. He's very calm. Far too calm."}, group=True)

# ================================================================================================= Valley of Bri Leith
z = Zone(206, 'Valley of Bri Leith', 3, 'hib_bri_leith')
ZONES.append(z)
z.npc('muirenn', 'Grandmother Muirenn', [905, 95], 'f', 14, model=362, idle="Rian went through the veil at Samhain. He was ten. He's still ten, there.")
z.npc('rian', 'Rian', [266, 946], 'm', 10, size=40, during=['veil/rian'])
z.npc('druid_ennis', 'Druid Ennis', [918, 82], 'm', 30, idle="The grove's oaks are dying. Their heart was stolen.")
z.npc('ailbhe', 'Ailbhe', [448, 450], 'f', 24, during=['oak_heart/ailbhe'])

it_veil = z.item('Veil-Thread Bracelet', 'bracer', 14, 'mind', "A thread from the veil between worlds. It's very hard to see.")
it_fruit = z.item("Otherworld Apple Charm", 'gem', 14, 'charm', "An apple from beyond the veil, cast in gold. Don't eat it. It's gold.")
it_seven = z.item('Seven-Year Ring', 'ring', 14, 'ward', "Rian's ring. It fit him when he was ten.")
it_wisp = z.item('Wisp-Light Cloak', 'cloak', 14, 'finesse', "It glimmers faintly, like a veil wisp at the edge of sight.")
z.quest('veil', 'Beyond the Veil', 14, 'muirenn',
        "My grandson Rian went through the veil at Samhain. The veil wisps lit the way and he followed them into the Otherworld, laughing.\n\nIt's thin there still, in the west of the valley. The druids say a strong arm could reach through and pull him back. Will you [bring Rian home]? He's ten. He's always been ten, there.",
        'bring Rian home',
        "Grandmother Muirenn's grandson followed the veil wisps into the Otherworld at Samhain.",
        [
            reach(206, [400, 900], 'Go to the thin place in the west of the valley', "Lights drift through the air - veil wisps - and between them, now and then, a glimpse of somewhere else: golden, endless, singing.", r=20),
            kill(206, [381, 916], 'Scatter the veil wisps', 'veil wisp', 60167560, [11, 12], 5,
                 text="As they go out, the glimpses of the Otherworld get clearer."),
            search(206, [360, 930], 'Search the edge of the veil', "a small boy's shoe", CRATE,
                   "Rian's shoe. Half of it is here, and half of it is somewhere else, and it is very hard to look at."),
            kill(206, [259, 961], 'Break the empyrean orbs that hold the veil open', 'empyrean orb', 60160471, [11, 12], 4),
            boss(206, [270, 950], 'Defeat the Keeper of the Veil', "The keeper unravels into light. The veil tears open for a moment, and a small boy tumbles out of it into the grass.",
                 'Keeper of the Veil', 60160478, 16, "A tall shape of pale light stands between you and the gap. 'What passes the veil stays. That is the rule.'",
                 objective='Defeat the Keeper of the Veil', hp=2.2, adds=[(60167560, 'veil wisp', [11, 12])], every=30, count=1),
            L('rian', talk('rian', 'Talk to Rian', "Is it time to go home? I was only gone a day. Wasn't I?\n\nI ate some apples. They were very good. The lady said if I ate them I'd have to [stay], but I could visit.", kw='stay')),
            choice('muirenn', 'Bring Rian home to Muirenn',
                   "Rian! Rian - you're - oh.\n\nHe's ten. Still ten. And he ate their fruit. The druids say if he crosses back for good, every year he spent there catches up with him by morning. He'll wake up seventeen. His childhood gone in a night.\n\nOr he can [go back], and stay ten forever, and visit me at Samhain. I can't choose. [Bring him back], or let him go.",
                   [('bring him back', "Then he'll be seventeen tomorrow. And he'll be here. I'll teach him what he missed. ...I'll teach him fast.", 'ending:home'),
                    ('go back', "Go on, my love. Go back to your apples. Come and see me at Samhain. I'll keep a candle in the window.", 'ending:veil')]),
        ],
        {'home': {'text': "Take this. It won't fit him tomorrow.", 'items': [it_seven], 'choice': [it_veil, it_wisp]},
         'veil': {'text': "Take this.", 'tragic': True, 'items': [it_fruit], 'choice': [it_veil, it_wisp]}})

it_acorn = z.item('Oak-Heart Acorn', 'gem', 28, 'faith', "A golden acorn from the heart of a sacred grove. It's warm, like something sleeping.")
it_siog = z.item("Siog Thief's Ring", 'ring', 28, 'finesse', "The siog steal everything that isn't nailed down. This ring was stolen eleven times.")
it_druid = z.item('Renegade Druid Torc', 'neck', 28, 'mind', "A druid's torc, from a druid who forgot what druids are for.")
it_grove = z.item("Grove-Keeper's Mantle", 'cloak', 28, 'ward', "Green and brown, the colours of a grove that lives.")
z.quest('oak_heart', 'The Oak-Heart', 28, 'druid_ennis',
        "The grove's oak-heart has been stolen - a golden acorn that holds the life of every oak in our sacred grove. Without it they'll die by midwinter.\n\nThe siog took it. Siog take everything. But siog don't keep things - they sell them. Find their camp west of the valley and you'll find who they sold it to. Will you [find the oak-heart]?",
        'find the oak-heart',
        "The siog stole the golden oak-heart that keeps a sacred grove alive, and sold it on.",
        [
            reach(206, [510, 630], "Find the siog camp in the west", "A camp of stolen things - pots, boots, a church bell, a chicken. Siog everywhere, counting.", r=20),
            kill(206, [500, 620], 'Fight through the siog seekers', 'siog seeker', 60166076, [27, 28], 5),
            search(206, [452, 632], "Search the siog's stolen goods", "a ledger of stolen things", CRATE,
                   "In a careful siog hand: 'One golden acorn. Sold to the druids at the stones, north. Paid: two silver, one goat.' The druids at the stones - renegades.",
                   give='the siog ledger'),
            kill(206, [458, 448], 'Fight the renegade druids at the stones', 'druid', 10120, [25, 26], 4),
            boss(206, [445, 458], 'Defeat the renegade archdruid', "The archdruid falls. A young druid in green kneels by the stones, holding the golden acorn, weeping.",
                 'Archdruid Ruadh', 10120, 31, "A druid in a cloak of black feathers raises a staff of thorn. 'The grove is ours to move. Ennis is old and blind.'",
                 objective='Defeat Archdruid Ruadh', hp=2.4, adds=[(10120, 'druid', [25, 26])], every=25, count=2),
            L('ailbhe', talk('ailbhe', 'Talk to the young druid', "I'm Ailbhe. Ennis' apprentice. I - I helped them. I told them where the oak-heart was kept.\n\nRuadh said the old grove was dying anyway and we could plant a new one in the west, away from the keeps and the wars. I believed him. Take it. Take it back to Ennis. And tell him I'm [sorry].", kw='sorry', give='the oak-heart')),
            choice('druid_ennis', 'Return the oak-heart to Druid Ennis',
                   "The oak-heart! The grove will live!\n\n...Ailbhe. My Ailbhe helped them.\n\nThe druids' law says an apprentice who betrays the grove is [turned out] - cast from the order, forever. Or I could [spare her], and take her back, and watch her every day. She was the best apprentice I ever had. That's why it hurts.",
                   [('spare her', "Then she'll come home, and plant the oak-heart with her own hands, and tend the grove until it forgives her. And I'll forgive her sooner.", 'ending:spared'),
                    ('turned out', "...Then she's no druid. I'll tell her myself. It's the law, and the law is older than my heart.", 'ending:turned_out')]),
        ],
        {'spared': {'text': "Take this, from the grove.", 'items': [it_grove], 'choice': [it_siog, it_druid]},
         'turned_out': {'text': "Take this, from the grove.", 'tragic': True, 'items': [it_acorn], 'choice': [it_siog, it_druid]}})

# ============================================================================================================== Connacht
z = Zone(207, 'Connacht', 3, 'hib_connacht')
ZONES.append(z)
z.npc('aine_mother', 'Aine', [1362, 1262], 'f', 8, idle="My boys. Both my boys. One I put out, one ran after him.")
z.npc('colm_boy', 'Colm', [930, 1100], 'm', 4, size=42, during=['rowdies/colm'])
z.npc('fiachra', 'Champion Fiachra', [1176, 70], 'm', 34, idle="My patrol went west. One came back. One's going to burn.")
z.npc('scout_aine', 'Scout Niamh', [1160, 64], 'f', 24, idle="Azure robes, wicker men, and a lot of singing. The west's gone strange.")
z.npc('ronan', 'Ronan', [762, 168], 'm', 25, during=['wickerman/ronan'])

it_sling = z.item("Rowdy's Sling-Bracer", 'bracer', 6, 'finesse', "Every rowdy in Connacht carries a sling. Colm's was the worst-made. He's proud of it.")
it_hearth = z.item('Hearthstone Ring', 'ring', 6, 'ward', "A pebble from Aine's hearth, set in tin.")
it_brother = z.item("Brothers' Cord", 'belt', 6, 'might', "Two cords plaited together. Brothers in Connacht trade them.")
it_mother = z.item("Aine's Shawl", 'cloak', 6, 'mind', "A blue shawl, darned many times by a mother who sat up waiting.")
z.quest('rowdies', 'Two Brothers', 6, 'aine_mother',
        "My husband put our eldest, Ruairc, out of the house last spring for thieving. He went to the rowdies in the west - the gang of youths that rob the road.\n\nNow my little one, Colm, has run off after him. He's nine. He thinks it's an adventure. Will you [find Colm]? And - if you see Ruairc - tell him his mother asks after him.",
        'find Colm',
        "Aine's eldest son was put out of the house and joined the road-gang in the west. Now her youngest has run off after him.",
        [
            kill(207, [934, 1167], 'Deal with the villainous youths on the road', 'villainous youth', 60167680, [4, 5], 5,
                 text="'Colm? The little one? He's with Ruairc's lot at the old camp. Ruairc's the boss now.'"),
            reach(207, [920, 1100], "Find the rowdies' camp", "A ragged camp of boys and young men. A little lad in a too-big cap is trying very hard to look tough.", r=20),
            boss(207, [941, 1085], "Face the rowdies' leader", "The young man drops his cudgel and sits down in the mud. 'Fine. FINE. Take him home. He's a terrible thief anyway.'",
                 'Ruairc the Rowdy', 60165444, 8, "A tall young man with his mother's eyes steps in front of the little one. 'He's my brother. He stays with me.'",
                 objective='Defeat Ruairc', hp=2.0, adds=[(60165444, 'rowdy', [5, 6])], every=30, count=1),
            L('colm', talk('colm_boy', 'Talk to Colm', "Ruairc said I could be in the gang! I can throw a stone further than anyone! ...Is Mam cross?\n\nRuairc says he can't come home because Da said. But he wants to. He told me. He cries at night. Don't tell him I [told].", kw='told')),
            choice('aine_mother', 'Bring Colm home to Aine',
                   "COLM. You - come here. Come HERE.\n\n...You saw Ruairc? How did he look? Is he thin? Did he ask after me?\n\nHis father swore he'd never set foot in the house again. If I [bring both home], his father and I will have words, and maybe worse. Or I take [only Colm], and keep the peace, and Ruairc stays out there. Tell me what to do. I've been asking the fire all year.",
                   [('bring both home', "Then go back and tell him his mother says come home. And if his father says a word, his father can sleep in the byre.", 'ending:both'),
                    ('only Colm', "Only Colm. ...Gods forgive me. I'll leave a loaf on the west road every week. Maybe he'll find it.", 'ending:one')]),
        ],
        {'both': {'text': "Take this. Both my boys are home.", 'items': [it_brother], 'choice': [it_sling, it_hearth]},
         'one': {'text': "Take this.", 'tragic': True, 'items': [it_mother], 'choice': [it_sling, it_hearth]}})

it_wicker = z.item('Wicker-Ash Charm', 'gem', 27, 'mind', "Ash from a wicker man that never burned its captive.")
it_azure = z.item("Azure Robe-Clasp", 'belt', 27, 'faith', "The clasp of an Azure Order robe. Ronan kept his.")
it_champion = z.item("Champion's Ring", 'ring', 27, 'might', "Fiachra's own. The Champions of Connacht give them for valour.")
it_patrol = z.item('Patrol-Spear Bracer', 'bracer', 27, 'finesse', "The haft of a patrol's spear, cut down and bound.")
z.quest('wickerman', 'The Wicker Man', 27, 'fiachra',
        "My patrol went west to watch the Azure Order - the idolaters in blue who've been gathering by the old stones. One man came back. He says the rest are dead, except Ronan.\n\nThey've built a wicker man. At the next moon, Ronan goes inside it and they set it alight. Scout [Niamh] has seen their camp. Will you [save Ronan]?",
        'save Ronan',
        "The Azure Order captured a patrol from the keep; the last survivor is to be burned in a wicker man.",
        [
            talk('scout_aine', 'Ask Scout Niamh about the Azure camp',
                 "They've idolaters chanting at the stones, west and north. Past them, a wicker man three times my height. Haunted, too - the old wickermen they've burned walk about at night. Go through the [idolaters] first. They'll raise the alarm otherwise.", kw='idolaters'),
            kill(207, [684, 197], 'Silence the azure idolaters', 'azure idolater', 60158182, [24, 25], 5),
            search(207, [700, 192], "Search the idolaters' altar", "a patrol's broken spear", CRATE,
                   "A Connacht patrol spear, snapped and laid on the altar as an offering. A blue robe folded beside it - a new one, a recruit's - with Ronan's name pinned to it."),
            kill(207, [788, 153], 'Destroy the phantom wickermen', 'phantom wickerman', 60164910, [26, 27], 4),
            defend(207, [762, 168], 'Free Ronan from the wicker man', "The idolaters scatter. Ronan climbs down from the wicker man, coughing, a blue robe still over his arm.",
                   'Ronan', 60158182, 25, "You hack at the wicker. Ronan yells from inside. Every idolater on the hill turns.",
                   [(60158182, 'azure idolater', [25, 26])], 'Keep Ronan alive', model=M, duration=90,
                   then_boss={'tpl': 60167712, 'name': 'Maelgwn, Voice of the Azure', 'lv': 30, 'announce': "A tall idolater in deep blue. 'The fire wanted him. It will have you instead.'", 'objective': 'Defeat Maelgwn'},
                   thanks="I'm out. I'm out. I'm OUT."),
            L('ronan', choice('ronan', 'Talk to Ronan',
                   "They gave me this robe. Said I could take it and live, if I'd join. I didn't. But I could have. I thought about it.\n\nWith it, I could walk into any Azure camp in Hibernia. Find out what they're planning. Tell the Champions. If I [go undercover], nobody can know - not even my mother. Or I [come home], burn the robe, and forget the whole thing.",
                   [('go undercover', "Then I'm dead, as far as anyone knows. Tell Fiachra the truth. Only Fiachra.", 'next:spy'),
                    ('come home', "Home. Gods, yes. And the robe goes in the first fire I see.", 'next:home')])),
            L('spy', end_talk('fiachra', 'Report to Champion Fiachra', "He's gone into the Azure, wearing their robe. His mother's been told he died a hero.\n\nGods. He's braver than I am. If word comes, it'll come to me. Take this - and say nothing to anyone.", 'spy')),
            L('home', end_talk('fiachra', 'Report to Champion Fiachra', "Ronan's home. He burned the robe in the courtyard, and the whole keep cheered.\n\nOne man from six. It's not a victory. But it's one man. Take this.", 'home')),
        ],
        {'spy': {'text': "Say nothing to anyone.", 'items': [it_azure], 'choice': [it_champion, it_patrol]},
         'home': {'text': "Take this.", 'items': [it_wicker], 'choice': [it_champion, it_patrol]}},
        topics={'Niamh': "My best scout. By the gate."})

# ========================================================================================================= Cursed Forest
z = Zone(208, 'Cursed Forest', 3, 'hib_cursed_forest')
ZONES.append(z)
z.npc('teague', 'Ranger Teague', [380, 742], 'm', 52, guild="Rangers' Camp", idle="The forest's cursed. The poachers make it worse.")
z.npc('seamus', 'Seamus the Leprechaun', [500, 772], 'm', 40, model=603, size=30, during=['leprechaun/seamus', 'leprechaun/gold'])
z.npc('druid_mor', 'Druid Mor', [386, 748], 'f', 56, guild="Rangers' Camp", idle="The goborchend have my brother Oisin. They'll have his blood at the dark of the moon.")
z.npc('oisin', 'Oisin the Druid', [912, 1392], 'm', 50, during=['goborchend/oisin'])

it_gold = z.item('Crock-of-Gold Charm', 'gem', 50, 'charm', "A single gold coin from a leprechaun's crock. It's always there when you check.")
it_cage = z.item('Iron-Cage Bracer', 'bracer', 50, 'might', "Cold iron from a leprechaun cage. Fae folk flinch from it.")
it_poach = z.item("Poacher's Cloak", 'cloak', 50, 'finesse', "Dull green and very quiet.")
it_cobble = z.item('Cobbler\'s Ring', 'ring', 50, 'mind', "Leprechauns are cobblers, really. This is a ring of shoe-leather and silver tacks.")
z.quest('leprechaun', 'The Leprechauns\' Cages', 50, 'teague',
        "Poachers in the forest are catching leprechauns. Cages of cold iron, so the little folk can't vanish. They sell them to lords who think a caged leprechaun means gold forever.\n\nIt doesn't. A caged leprechaun dies in a month. Will you [free them]? The poachers camp in the middle of the forest.",
        'free them',
        "Poachers are catching leprechauns in cold-iron cages to sell to greedy lords.",
        [
            kill(208, [491, 758], 'Kill the forest poachers', 'forest poacher', 60161034, [50, 51], 5),
            search(208, [500, 772], "Search the poachers' camp", "a row of cold-iron cages", CRATE,
                   "Six cages. Five empty, the leprechauns already dead. In the last, a very small, very angry man in a green coat."),
            L('seamus', talk('seamus', 'Free the last leprechaun', "OUT. Get me OUT. ...Ahh. Thank you. Thank you.\n\nSeamus is the name. The others - well. You saw. The poachers' chief has their gold, all five crocks, buried under the cave bears' den to the west. He'll be back for me. Unless you get there [first].", kw='first')),
            kill(208, [320, 669], "Drive the cave bears from their den", 'unearthed cave bear', 60167436, [49, 50], 5,
                 text="Under the den: five crocks of gold, half-buried. And footsteps behind you."),
            boss(208, [326, 672], 'Defeat the poachers\' chief', "Brannagh falls into his own pit, among the gold.",
                 'Brannagh the Poacher-Chief', 60161034, 55, "A big man with an iron net over his shoulder. 'That's MY gold, stranger. Five crocks. Five little dead men. Worth every one.'",
                 objective='Defeat Brannagh', hp=2.6, adds=[(60161034, 'forest poacher', [50, 51])], every=25, count=2),
            L('gold', choice('seamus', 'Talk to Seamus',
                   "Five crocks. My cousins' gold.\n\nLeprechaun gold's for leprechauns. Without a leprechaun it goes back into the earth in a year and a day. But you could [take the gold] - all of it - and be rich for a year and a day. Fair's fair, you saved me.\n\nOr let me [bury it with them]. My cousins. They'd like that.",
                   [('take the gold', "Then it's yours, and good luck to you. Spend it fast. ...Mind, every coin you spend, somebody remembers who it belonged to.", 'next:gold'),
                    ('bury it with them', "...You're a strange one. Thank you. I'll sing them down. Go on back to Teague. I'll be along.", 'next:buried')])),
            L('gold', end_talk('teague', 'Return to Ranger Teague', "The poachers are done, and you came back with your pockets clinking.\n\nI won't ask. Seamus came by and said you'd earned it. He didn't look happy about it. Take this, from the rangers.", 'gold')),
            L('buried', end_talk('teague', 'Return to Ranger Teague', "The poachers are done. And Seamus came by and told me what you did with the gold.\n\nThe little folk will remember. That's worth more than gold, in this forest. Take this, from the rangers.", 'buried')),
        ],
        {'gold': {'text': "From the rangers.", 'items': [it_gold], 'choice': [it_cage, it_poach]},
         'buried': {'text': "From the rangers.", 'items': [it_cobble], 'choice': [it_cage, it_poach]}})

it_horn3 = z.item('Goborchend Horn Torc', 'neck', 56, 'might', "Twisted goat-horn, bound in bronze. The goborchend wear their horns as trophies; you wear theirs.")
it_bloodstone = z.item('Bloodhorn\'s Altar-Stone', 'gem', 56, 'mind', "A chip from a goborchend altar. Druid Mor cleansed it. It's still red.")
it_oisin = z.item("Oisin's Druid-Cloak", 'cloak', 56, 'faith', "Green and brown and full of pockets.")
it_fomor = z.item('Fomorian-Bone Bracer', 'bracer', 56, 'ward', "The goborchend are of the old Fomorian blood. Their bones are heavy and hard.")
it_fort = z.item("Fort-Breaker's Ring", 'ring', 56, 'finesse', "Given to whoever first broke into a goborchend fort.")
z.quest('goborchend', 'The Goat-Headed Fort', 56, 'druid_mor',
        "This is GROUP work, and hard. Bring the best you know.\n\nThe goborchend - goat-headed, Fomorian blood - have a fort in the south of the forest. They have my brother Oisin, a druid. At the dark of the moon they'll pour his blood on their altar to wake something old.\n\nWill you [go after Oisin]?",
        'go after Oisin',
        "GROUP. The goat-headed goborchend have captured a druid to wake something old with his blood.",
        [
            reach(208, [880, 1360], "Go to the goborchend fort in the south", "Goat-skulls on poles. A wall of black stone. Inside, chanting, low and terrible.", r=20),
            kill(208, [904, 1425], 'Break the goborchend gashers on the wall', 'goborchend gasher', 60161461, [52, 53], 5),
            kill(208, [895, 1402], 'Cut down the goborchend wounders in the yard', 'goborchend wounder', 60161466, [53, 54], 4),
            search(208, [920, 1395], "Search the fort's altar", "a blood-stained altar", CRATE,
                   "The altar's carved with Fomorian runes. Mor would read them; you can only see the shape of them: an eye. A huge, closed eye."),
            boss(208, [912, 1392], 'Defeat Bloodhorn before the rite', "Bloodhorn falls across his own altar. Under it, something huge and old stops stirring.",
                 'Bloodhorn, Goborchend Chieftain', 60161466, 60, "A goborchend twice the height of the others, horns dripping. 'The druid's blood opens the eye. Your blood will do as well.'",
                 objective='Defeat Bloodhorn', hp=3.2, adds=[(60161461, 'goborchend gasher', [52, 53])], every=25, count=2),
            L('oisin', talk('oisin', 'Free Oisin', "Mor sent you? Of course. She's the clever one.\n\nThe eye - they were trying to open Balor's eye. Or one like it. Under the fort. Asleep. Mor needs to know. She'll need to choose what to [do] about it.", kw='do')),
            choice('druid_mor', 'Return to Druid Mor',
                   "Oisin's alive. Thank every god.\n\nAnd under the fort - an eye. A Fomorian eye, sleeping. Oisin says it can be [sealed] forever - the druids' great rite, and it will cost me most of my power. Or [left sleeping], and watched, and studied - and perhaps used, one day, against Albion or Midgard. The Council would like that. I wouldn't.",
                   [('sealed', "Then I'll seal it. Tomorrow. Oisin will help. ...I'll be a hedge-druid after, curing warts. I think I'll like it.", 'ending:sealed'),
                    ('left sleeping', "Watched, then. Studied. Gods help us if anyone ever wakes it on purpose.", 'ending:watched')]),
        ],
        {'sealed': {'text': "From the druids.", 'items': [it_oisin], 'choice': [it_horn3, it_fomor, it_fort]},
         'watched': {'text': "From the druids.", 'tragic': True, 'items': [it_bloodstone], 'choice': [it_horn3, it_fomor, it_fort]}},
        group=True)

# ========================================================================================================= Sheeroe Hills
z = Zone(216, 'Sheeroe Hills', 3, 'hib_sheeroe')
ZONES.append(z)
z.npc('bebhinn', 'Healer Bebhinn', [300, 800], 'f', 40, guild="Healers' Camp", idle="Elfshot. Every one of them. The glimmer folk's arrows don't kill - they do worse.")
z.npc('lochlann', 'Lochlann', [304, 806], 'm', 38, guild="Healers' Camp", idle="(He stares at nothing and hums the same four notes, over and over.)")
z.npc('elder_cnoc', 'Elder Cnoc', [600, 150], 'm', 52, model=603, size=35, guild='Lurikeen Exiles', idle="The Azure took our village. They say they're cleansing it. Of us.")
z.npc('cnoc_village', 'Elder Cnoc', [692, 96], 'm', 52, model=603, size=35, during=['azure_village/home'])

it_arrow = z.item('Glimmer-Arrow Pendant', 'neck', 42, 'mind', "A glimmer-glass arrowhead. It points toward the Glimmer King's hosts, wherever they are.")
it_elfshot = z.item("Elfshot Ward", 'gem', 42, 'faith', "A healer's charm against the glimmer folk's arrows.")
it_madman = z.item('Madman\'s Bracer', 'bracer', 42, 'might', "An elfshot man made this, in his madness. It's very good.")
it_glimmer = z.item("Glimmerling Cloak", 'cloak', 42, 'finesse', "It catches the light and throws it back wrong.")
z.quest('elfshot', 'Elfshot', 42, 'bebhinn',
        "My husband Lochlann was elfshot - struck by a glimmer folk arrow. It doesn't kill. It takes the mind and leaves the man. He hums. That's all.\n\nThe arrows are glimmer-glass. If I had the arrowhead that struck him - the archer's own - I could draw the madness out. Will you [find the archer]? The madmen of the hills all took his arrows.",
        'find the archer',
        "Healer Bebhinn's husband was elfshot by a glimmer archer. With the archer's own arrowhead, she could cure him.",
        [
            kill(216, [375, 711], 'Put the elfshot madmen to rest', 'elfshot madman', 44002, [37, 38], 5,
                 text="Each one has a glimmer-glass splinter in him. Each splinter points the same way - west."),
            search(216, [365, 720], "Search the madmen's camp", "a glimmer-glass arrowhead", CRATE,
                   "A spent arrowhead, glowing faintly. It tugs westward like a lodestone, toward the glimmerlings' hills."),
            kill(216, [171, 788], 'Hunt down the glimmerlings', 'glimmerling', 44024, [38, 39], 5),
            boss(216, [190, 780], 'Defeat the glimmer archer', "The archer shatters like a dropped lamp. Among the shards, an arrowhead brighter than the rest.",
                 'Glimmer Archer Saoth', 44038, 45, "A tall figure of glimmering glass draws a bow of light. 'More madmen for the King's hills.'",
                 objective='Defeat the Glimmer Archer', hp=2.6, adds=[(44024, 'glimmerling', [38, 39])], every=25, count=2),
            choice('bebhinn', "Bring the archer's arrowhead to Bebhinn",
                   "That's it. The archer's own. I can feel it pulling.\n\nI can [break the arrow] in a healing rite, and draw the madness out of Lochlann. The arrowhead will be gone.\n\nOr - the Fianna came by this morning. They say an archer's arrowhead points to the Glimmer King's hosts wherever they march. It could save hundreds. They'd want me to [keep it] for them. And Lochlann would hum forever.",
                   [('break the arrow', "Then I'll do it now. ...Lochlann? Lochlann. Look at me. ...He's looking at me.", 'ending:healed'),
                    ('keep it', "...The Fianna will have it by morning. I'll sing his four notes with him. He likes it when I do.", 'ending:kept')]),
        ],
        {'healed': {'text': "Take this. Lochlann wants you to have it - he says so. He SAYS so.", 'items': [it_elfshot], 'choice': [it_madman, it_glimmer]},
         'kept': {'text': "Take this.", 'tragic': True, 'items': [it_arrow], 'choice': [it_madman, it_glimmer]}})

it_lurikeen = z.item('Lurikeen Hearth-Charm', 'gem', 52, 'charm', "A little clay figure of a hearth, made by lurikeen children.")
it_cleanse = z.item("Cleanser's Torc", 'neck', 52, 'mind', "An Azure cleanser's torc. Every link has a name scratched into it - the names of the cleansed.")
it_pale = z.item('Pale Horse Bracer', 'bracer', 52, 'might', "Leather from a pale horse of the hills. It never quite warms.")
it_exile = z.item("Exile's Cloak", 'cloak', 52, 'ward', "Grey and patched. Cnoc wore it for a year.")
it_ledger2 = z.item("Inquisitor's Ring", 'ring', 52, 'finesse', "Taken from the Azure inquisitor who held the village.")
z.quest('azure_village', 'The Cleansed Village', 52, 'elder_cnoc',
        "This is GROUP work. The Azure Order are many, and they don't fear death.\n\nThey took our village in the northern hills. 'Cleansing', they call it. Of fae blood. Of us. We fled with what we could carry. Some didn't flee fast enough.\n\nWill you [take back the village]? Some of ours may still be alive inside.",
        'take back the village',
        "GROUP. The Azure Order took a lurikeen village in the northern hills to 'cleanse' it.",
        [
            reach(216, [690, 210], "Go to the lurikeen village in the north", "Lurikeen huts, painted over with blue sigils. Azure cleansers walk between them with censers, chanting.", r=20),
            kill(216, [700, 220], 'Drive out the azure cleansers', 'azure cleanser', 44008, [47, 48], 5),
            search(216, [690, 100], "Search the elder's hut", "an Azure ledger", CRATE,
                   "A ledger of names: lurikeen, and beside each, 'cleansed' - or 'held'. Seven names say 'held'. The pale horses carry them east, to the inquisitor's camp.",
                   give='the Azure ledger'),
            kill(216, [1000, 375], 'Kill the pale horses that carry the prisoners east', 'pale horse', 44001, [50, 51], 4),
            boss(216, [700, 215], 'Defeat the Azure inquisitor', "The inquisitor falls. From a locked hut, seven small voices start calling all at once.",
                 'Inquisitor Ceallach of the Azure', 44007, 56, "An Azure banisher in a mask of blue glass. 'The fae taint must be cleansed. All of it. Including whoever shelters it.'",
                 objective='Defeat the Inquisitor', hp=3.0, adds=[(44008, 'azure cleanser', [47, 48])], every=25, count=2),
            L('home', choice('cnoc_village', 'Speak with Elder Cnoc in the village',
                   "Seven. Seven of ours alive. And the village is ours again.\n\nBut the Azure will come back. They always come back. We could [rebuild] here - make walls, and fight. Or we could [go west], to the Valley of Bri Leith, and start again where the Azure don't go. The village will be empty. My grandfather built that hut.",
                   [('rebuild', "Then we rebuild. Walls first. And this time, a watch-tower. Thank you. The lurikeen of Sheeroe will not forget.", 'ending:rebuild'),
                    ('go west', "West, then. We'll take what we can carry. Again. ...But together, this time. All of us.", 'ending:west')])),
        ],
        {'rebuild': {'text': "From the village.", 'items': [it_lurikeen], 'choice': [it_cleanse, it_pale, it_ledger2]},
         'west': {'text': "Take this. I won't need it in the west.", 'tragic': True, 'items': [it_exile], 'choice': [it_cleanse, it_pale, it_ledger2]}},
        group=True)
