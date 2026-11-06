"""Midgard's story quests (claude 2026-11-05) - see story_gen.py. Places: zone metres [x, y]."""
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE = 1882, 1876, 1347
M, F = 213, 168
ZONES = []

# ======================================================================================================== Vale of Mularn
z = Zone(100, 'Vale of Mularn', 2, 'mid_mularn')
ZONES.append(z)
z.npc('sigrun', 'Sigrun Tovesdottir', [1250, 1301], 'f', 6, idle="Hallvard. You haven't seen a big, slow, kind man called Hallvard? No. Of course not.")
z.npc('grima', 'Old Grima', [1240, 1243], 'f', 20, model=157, idle="The hidden folk are older than the jarls. Older than the gods, some say. Only fools say it loudly.")
z.npc('hallvard', 'Hallvard', [262, 878], 'm', 7, during=['huldra/hallvard', 'huldra/choose'])
z.npc('bjarki', 'Bjarki Houndmaster', [1158, 184], 'm', 14, idle="A good hound is worth three huscarls. Don't tell the huscarls.")
z.npc('bjarki_spring', 'Bjarki Houndmaster', [704, 606], 'm', 14, during=['gormr/decide'])

it_tail = z.item('Huldra-Hair Bracelet', 'bracer', 6, 'charm', "A braid of hair, golden and impossibly fine. It smells of pine and cream.")
it_axe = z.item("Hallvard's Axe-Ring", 'ring', 6, 'might', "An iron ring forged from the head of a woodsman's axe.")
it_birch = z.item('Birch-Bark Sash', 'belt', 6, 'mind', "Huldu work: strips of birch bark woven soft as cloth.")
it_grima = z.item("Grima's Hearth Cloak", 'cloak', 6, 'ward', "Grey wool with a red border. Old Grima's best. She insisted.")
z.quest('huldra', 'The Huldra\'s Bargain', 6, 'sigrun',
        "Hallvard and I are to be wed at midsummer. Or we were. He went into the western woods to cut timber for our house, and came back once, a week ago - singing, smelling of pine and cream - and went straight back out again.\n\nOld [Grima] says it's a huldra. One of the hidden folk. Will you [find Hallvard]? Before midsummer, if you can.",
        'find Hallvard',
        "Sigrun's betrothed went into the western woods to cut timber and came back singing - then went back to the hidden folk.",
        [
            talk('grima', 'Ask Old Grima about the hidden folk',
                 "A huldra. Fair as morning from the front, and a cow's [tail] behind - that's how you know. She'll have a camp in the west, with her kin. If a huldra weds a man under the gods, she loses the tail and becomes a woman. They want that very much. Some of them want it more than they want the man.", kw='tail'),
            reach(100, [450, 930], 'Go into the western woods', "Somewhere ahead, someone is singing - a man, badly, and a woman, beautifully.", r=20),
            kill(100, [330, 862], 'Get past the huldu stalkers', 'huldu stalker', 60162266, [5, 6], 5,
                 text="The hidden folk fade back into the trees, watching. They don't seem to want to fight. They seem to want you to leave."),
            search(100, [270, 870], "Search the huldu camp", "a woodsman's axe, left in a stump", CRATE,
                   "Hallvard's axe, its edge rusting. He hasn't cut a tree in a week. Beyond the tents, in the firelight, a big man sits with a beautiful woman's head on his shoulder."),
            L('hallvard', talk('hallvard', 'Talk to Hallvard',
                 "Sigrun sent you? Oh. Oh, Sigrun.\n\nThis is Ylva. Look at her. She says she'll lose her tail if we wed at the temple, and be a woman, and grow old with me. She cried when she said it. Nobody's ever cried over me. I don't know what to [do].", kw='do')),
            L('choose', choice('hallvard', 'Help Hallvard decide',
                   "I promised Sigrun. I did. But I didn't know there was this. Tell me.\n\nShould I [wed Ylva]? Or should you [break the glamour] and drag me home by the beard? Ylva's father won't let me go easy, if you do.",
                   [('wed Ylva', "...Yes. Yes. Tell Sigrun I'm sorry. Tell her she'll find someone who deserves her. I mean that.", 'next:wed'),
                    ('break the glamour', "Then do it quick, before I change my mind - her father's coming. Gods, look at the size of him.", 'next:break')])),
            L('break', boss(100, [262, 880], "Break the huldra's glamour", "The old hill-man falls. Ylva is gone - only a scent of pine. Hallvard blinks like a man waking up.",
                 'Old Grumme of the Hidden Folk', 60165095, 8, "An old huldu man rises from the fire, horns and all. 'He's promised to my girl. You'll not take him.'",
                 objective='Defeat Old Grumme', hp=2.0, adds=[(60162266, 'huldu stalker', [5, 6])], every=30, count=1)),
            end_talk('sigrun', 'Bring Hallvard home', "He's home. He looks like a man who woke up from a lovely dream into a cold morning, and he says sorry every hour.\n\nI'll take him. Sorry and all. Midsummer's still a month off.", 'home'),
            L('wed', end_talk('sigrun', 'Tell Sigrun', "He's marrying her. A huldra. At the temple, so she can be a woman.\n\nThen I hope she's a better one than me, because I'm going to hate her for the rest of my life. ...No. That's not fair. Take this. It was meant for the wedding.", 'wed')),
        ],
        {'home': {'text': "Take this - for bringing him home.", 'items': [it_axe], 'choice': [it_birch, it_grima]},
         'wed': {'text': "It was meant for the wedding.", 'tragic': True, 'items': [it_tail], 'choice': [it_axe, it_grima]}},
        topics={'Grima': "Old Grima, by the well. She knows every story worth knowing."})

it_gormr = z.item("Gormr's Collar", 'neck', 12, 'finesse', "A wide studded collar, worn smooth by a big dog's neck.")
it_fetish = z.item('Broken Bone-Fetish', 'gem', 12, 'mind', "A vendo shaman's charm, snapped and bound with red thread. The curse is out of it. Mostly.")
it_kennel = z.item("Houndmaster's Belt", 'belt', 12, 'might', "Hung with whistles, leads and treats. Every hound in Mularn knows it.")
it_spring = z.item('Spring-Water Ring', 'ring', 12, 'ward', "Silver from the bottom of a cleansed spring. It is always cold.")
z.quest('gormr', 'The Houndmaster\'s Law', 12, 'bjarki',
        "My hounds went mad in a night. Foaming, howling, gone west into the moor. Gormr led them - my son's dog. My son's dead two winters, and Gormr's all of him I've got.\n\nGormr bit a child before he ran. The jarl's law says a dog that bites a child is killed. I know the law. Will you [find my hounds] and find out what did this? I'll deal with the law after.",
        'find my hounds',
        "Bjarki Houndmaster's hounds went mad and ran west, led by his dead son's dog.",
        [
            reach(100, [760, 640], 'Search the western moor', "Hounds - Bjarki's hounds - roam the heather, foaming at the mouth, savage and lost.", r=20),
            kill(100, [744, 653], 'Put down the worst of the rabid hounds', 'rabid wolfhound', 60165108, [10, 11], 5,
                 text="Every one wears Bjarki's brass tag. Every one had drunk from the same spring - their muzzles are stained with its grey water."),
            search(100, [700, 600], 'Find the fouled spring', "a spring fouled with bones", CRATE,
                   "Bone fetishes, strung on sinew and sunk in the spring - vendo work. The water is grey with curse. Tracks of clawed feet lead north, to the vendo camps.",
                   give='a vendo bone-fetish'),
            boss(100, [604, 422], 'Kill the vendo shaman who cursed the spring', "The bone-singer's chant chokes off. Far to the south, all at once, the howling stops.",
                 'Bone-Singer Grakka', 60167576, 14, "A vendo in a mask of skulls rises out of a pile of bones, rattling and singing. 'Dog-man's dogs! Dog-man's dogs, mad and mine!'",
                 objective='Kill Bone-Singer Grakka', hp=2.2, adds=[(60167594, 'vendo warrior', [11, 12])], every=30, count=1),
            L('decide', choice('bjarki_spring', 'Meet Bjarki at the spring',
                   "The fever's broken. Look at them - lying in the grass like puppies, sorry for themselves. And Gormr. Gormr's here.\n\nHe's himself again. But he bit the Sveinsson girl. The jarl's law is the law: you saw it, so you must say. Do I [keep the law]? Or do we [say nothing], and Gormr was never found?",
                   [('keep the law', "...Yes. I'll do it myself. He's my son's dog. He'll not die by a stranger's hand. Go back to Fort Veldon. I'll follow.", 'next:law'),
                    ('say nothing', "Never found. Lost on the moor. Aye. Aye. Gods forgive us both. Come on, boy. Come on, Gormr.", 'next:spared')])),
            L('law', end_talk('bjarki', 'Return to Fort Veldon', "It's done. He didn't fight. He licked my hand.\n\nThe jarl thanked me for my loyalty. I nearly hit him. Here. Gormr's collar. I can't keep it in the house.", 'law')),
            L('spared', end_talk('bjarki', 'Return to Fort Veldon', "Gormr was never found, if anyone asks. Lost on the moor.\n\nHe's asleep under my bed. Snoring. Here - take something. You've given me back more than a dog.", 'spared')),
        ],
        {'law': {'text': "Gormr's collar. Take it.", 'tragic': True, 'items': [it_gormr], 'choice': [it_fetish, it_kennel]},
         'spared': {'text': "Take something.", 'items': [it_spring], 'choice': [it_fetish, it_kennel]}})

# ========================================================================================================= East Svealand
z = Zone(101, 'East Svealand', 2, 'mid_east_svealand')
ZONES.append(z)
z.npc('gunnhild', 'Gunnhild the Freewoman', [1310, 430], 'f', 10, idle="I wore a collar eleven years. I don't wear anything round my neck now. Not even beads.")
z.npc('orm_thrallmaster', 'Orm the Thrall-Master', [1066, 203], 'm', 14, idle="A thrall's a thrall. Gods made them so. Ask me about their prices, not their feelings.")
z.npc('ketil', 'Ketil', [508, 1004], 'm', 6, during=['thrall_price/ketil', 'thrall_price/choose'])
z.npc('ragna', 'Ragna Farmwife', [240, 578], 'f', 8, idle="We forgot. That's all. One winter we forgot to leave the porridge.")
z.npc('granny_tomte', 'Granny Tomte', [760, 1342], 'f', 10, model=M, size=25, during=['tomte_due/granny'])

it_collar = z.item('Broken-Collar Bracer', 'bracer', 7, 'might', "Iron from a thrall's collar, beaten flat. It was a symbol of one thing. Now it is a symbol of another.")
it_free = z.item("Freedman's Cloak", 'cloak', 7, 'ward', "Grey wool, plain and new. The first thing Ketil ever owned.")
it_runaway = z.item("Runaway's Ring", 'ring', 7, 'finesse', "A ring hidden in a thrall's mouth for three years.")
it_price = z.item('Price-Paid Charm', 'gem', 7, 'charm', "A little silver coin, holed and hung on a thong: the last coin of a thrall's price.")
z.quest('thrall_price', "A Thrall's Price", 7, 'gunnhild',
        "My brother Ketil is a thrall. I bought my own freedom with eleven years of pennies, and I've been saving for his. I'm nearly there.\n\nAnd he RAN. Three days ago. Orm the [thrall-master] says there's a bounty. If he's caught, they'll brand him, and my money won't buy him back for any price. Will you [find Ketil] first?",
        'find Ketil',
        "Gunnhild had nearly saved her brother's thrall-price when he ran away. If he's caught, he'll be branded.",
        [
            talk('orm_thrallmaster', 'Ask Orm the thrall-master about the runaways',
                 "Ketil? Ran with three others. They'll be at the old hideout by the strider pools - runaways always go there first. Then south, to join the roaming thralls - bandits, now, every one. If you find him, there's a [bounty] in it.", kw='bounty'),
            search(101, [918, 512], "Search the runaways' hideout by the pools", "a cut iron collar", CRATE,
                   "Four collars, cut and dropped. On one, scratched with a knife: 'Sorry, sister.' The trail goes south."),
            reach(101, [520, 980], "Follow the trail south to the roaming thralls", "A ragged camp of escaped thralls, armed with stolen axes. They're not friendly.", r=20),
            boss(101, [505, 1000], "Break the roaming thralls' hold", "The bandit leader drops his axe. The others scatter - except one young man, who just sits down in the mud.",
                 'Ulfar Broken-Collar', 60165358, 9, "A big scarred man with a collar still riveted round his neck strides out. 'Another bounty-hunter. We kill bounty-hunters here.'",
                 objective='Defeat Ulfar Broken-Collar', hp=2.0, adds=[(60165358, 'roaming thrall', [6, 7])], every=30, count=1),
            L('ketil', talk('ketil', 'Talk to Ketil', "Gunnhild sent you. Course she did.\n\nShe's been saving eleven years. Eleven years of her life, for me. I couldn't bear it. I thought if I ran, she could spend it on herself for once. I'm not [worth it].", kw='worth it')),
            L('choose', choice('ketil', 'Decide what Ketil does',
                   "If I go back, Orm brands me as a runaway - but Gunnhild can still buy me, if she pays double. If I run north to the mountains, I'm free, but I can never come down. She'd never see me again.\n\nTell me to [go back], or to [run north]. I'll do it. I'm tired of choosing badly.",
                   [('go back', "Back. All right. Branded and bought. At least I'll be bought by my sister.", 'next:back'),
                    ('run north', "North, then. Tell her - tell her to buy a farm. Tell her I'll be thinking of her every day. Every day.", 'next:north')])),
            L('back', end_talk('gunnhild', 'Return to Gunnhild', "He came back. He walked into Orm's yard on his own and held out his arm for the brand.\n\nI paid double. I paid everything. He's free - he's FREE, and he's sitting in my kitchen, and I don't have a penny left. I've never been so rich.", 'back')),
            L('north', end_talk('gunnhild', 'Tell Gunnhild', "North. Free, and gone.\n\nEleven years of pennies, and he ran so I'd keep them. The idiot. The dear, stupid idiot. Here. Take some of them. I can't look at them.", 'north')),
        ],
        {'back': {'text': "Take this - Ketil insisted.", 'items': [it_price], 'choice': [it_collar, it_free]},
         'north': {'text': "Take some of them.", 'tragic': True, 'items': [it_price], 'choice': [it_collar, it_runaway]}},
        topics={'thrall-master': "Orm. North of here, at the thrall pens. He'll be pleased to see you. He's pleased to see anyone who might bring him coin."})

it_spoon = z.item("Tomte's Porridge-Spoon", 'gem', 11, 'charm', "A tiny wooden spoon. Leave it out at Yule, and something will thank you.")
it_cradle = z.item('Cradle-Quilt Cloak', 'cloak', 11, 'ward', "Stitched from a baby's quilt, let out and let out again. It smells of milk and hay.")
it_nisse = z.item("Nisse's Red Cap", 'gem', 11, 'finesse', "A tomte's pointed red cap, absurdly small. It sits in your pack and somehow helps.")
it_barn = z.item('Barn-Beam Bracer', 'bracer', 11, 'might', "Oak from a barn that burned. It is still warm.")
z.quest('tomte_due', "The Tomte's Due", 11, 'ragna',
        "The tomte took my baby. Our farm's tomte - the little grey men who've kept the barn since my grandmother's day. We forgot to leave out their porridge at Yule, one winter. Just one!\n\nSince then they've been stealing, breaking things, joining the tomte raiders in the east. And three nights ago, my Ulf, out of his cradle. Please. Will you [bring him back]?",
        'bring him back',
        "The farm's tomte, angry at being forgotten, stole Ragna's baby from his cradle.",
        [
            reach(101, [900, 640], "Find the tomte raiders' camp in the east", "Tents of patched sacking. Tiny fires. Tomte everywhere, grey-bearded and red-capped, and every one of them armed.", r=20),
            kill(101, [880, 630], 'Fight through the tomte pillagers', 'tomte pillager', 60167133, [8, 9], 6,
                 text="Small, quick, and furious. 'Forgotten!' they shout. 'FORGOTTEN!'"),
            search(101, [930, 630], 'Search the tomte camp', "a tiny cradle-quilt", CRATE,
                   "Ulf's quilt, folded with care. A tomte scrawl: 'TO THE KING. THE KING DECIDES.' The tomte king holds court on the southern shore."),
            reach(101, [750, 1350], "Go to the tomte king's court on the south shore", "A little throne of driftwood on the beach. A cradle beside it. And a very loud baby.", r=20),
            boss(101, [752, 1348], 'Defeat the tomte king', "The tomte king drops his sceptre - a soup ladle - and sits down hard in the sand.",
                 'Tomte-King Nisse Grumblebeard', 60167116, 12, "A tomte in a crown of bent nails leaps onto the throne. 'The big folk FORGOT us! Now they will REMEMBER!'",
                 objective='Defeat Nisse Grumblebeard', hp=2.0, adds=[(60167142, 'tomte skirmisher', [8, 9])], every=25, count=2),
            L('granny', choice('granny_tomte', 'Speak with Granny Tomte',
                   "Enough, enough. He's a fool, the king - he's my son. Listen to me, big one.\n\nWe kept that farm a hundred years. We were forgotten. Forgotten is worse than hated. We took the babe so somebody would remember us - we'd raise him tomte, and he'd remember.\n\nTake him back. But [promise porridge] - for us, every Yule, forever. Or [no promises], and take him by force. We can't stop you. We'll remember that too.",
                   [('promise porridge', "Every Yule. With butter. Ha! Go on, then, take the noisy thing. Tell the farmwife the barn will be swept by morning.", 'next:promise'),
                    ('no promises', "No promises. Then go, and take him, and see how your barn does without us.", 'next:forced')])),
            L('promise', end_talk('ragna', 'Bring Ulf home to Ragna', "ULF. Ulf, my Ulf.\n\nPorridge every Yule, with butter? We'll make it with cream. I don't care. And the barn - the barn's swept. I went out this morning and it's swept, and the cow's milked, and there's a little bundle of herbs on the door.", 'promise')),
            L('forced', end_talk('ragna', 'Bring Ulf home to Ragna', "My baby. Oh, thank you, thank you.\n\nThe barn burned last night. Nobody hurt. Nobody saw it start. Here - take this. We can rebuild. We have Ulf.", 'forced')),
        ],
        {'promise': {'text': "Take this - the tomte left it on the step for you.", 'items': [it_spoon], 'choice': [it_cradle, it_nisse]},
         'forced': {'text': "Take this.", 'tragic': True, 'items': [it_cradle], 'choice': [it_barn, it_nisse]}})

# ========================================================================================================= West Svealand
z = Zone(102, 'West Svealand', 2, 'mid_west_svealand')
ZONES.append(z)
z.npc('asvor', 'Asvor Eyvindsmother', [1388, 1152], 'f', 15, idle="My son swore an oath to wolves. Now the wolves hunt him for breaking it.")
z.npc('halvdan_scout', 'Halvdan the Scout', [1378, 1132], 'm', 18, idle="The blood-fellowship? Raiders with a creed. Worse than raiders without one.")
z.npc('eyvind', 'Eyvind Asvorsson', [1172, 1344], 'm', 14, during=['oathbreaker/eyvind', 'oathbreaker/choose'])
z.npc('gothi_valbrand', 'Gothi Valbrand', [1222, 62], 'm', 24, idle="The gods are listening. Speak carefully.")
z.npc('huscarl_grettir', 'Huscarl Grettir', [1198, 50], 'm', 22, idle="Kolbein was my shield-mate. We don't leave shield-mates.")
z.npc('kolbein', 'Kolbein', [326, 350], 'm', 18, during=['wolf_cord/kolbein', 'wolf_cord/cord'])

it_armring = z.item("Eyvind's Cut Arm-Ring", 'bracer', 15, 'might', "Silver, cut through where an oath was broken. It can never be mended.")
it_oath2 = z.item("Oathbreaker's Cloak", 'cloak', 15, 'finesse', "Ragged and black. Deserters of the blood-fellowship wear them so they can find each other.")
it_huginfel = z.item('Huginfel Hearth-Ring', 'ring', 15, 'ward', "The kind of ring a mother gives a son who came home.")
it_blood = z.item('Blood-Fellowship Torc', 'neck', 15, 'mind', "Taken from a svard of the blodfelag. The inside is stained.")
z.quest('oathbreaker', 'The Oathbreaker', 15, 'asvor',
        "My son Eyvind swore the oath of the blood-fellowship last spring - the blodfelag, raiders who drink each other's blood to bind them. He was sixteen and stupid.\n\nThis winter he tried to leave them. They call deserters 'oathbreakers' and hunt them like wolves. Halvdan the [scout] says they're close. Will you [find Eyvind] before they do?",
        'find Eyvind',
        "Asvor's son swore an oath to the blood-fellowship raiders, then deserted. Now they hunt him.",
        [
            talk('halvdan_scout', 'Ask Halvdan the scout about the hunt',
                 "The blodfelag have henchmen out on the eastern ridge - deserter-hunters. The deserters, the [oathbreakers], hide in the woods south of here. Kill the hunters first, or they'll follow you straight to him.", kw='oathbreakers'),
            kill(102, [1353, 910], 'Kill the blood-fellowship henchmen hunting deserters', 'blodfelag henchman', 60158516, [12, 13], 5,
                 text="One of them carries a list of names. Eyvind's is third. The first two are crossed out."),
            search(102, [1176, 1338], "Search the deserters' hideout in the southern woods", "a cut silver arm-ring", CRATE,
                   "An oath-ring, cut through. Fresh blood on the ground - not much. A voice from the bracken: 'Mother? ...No. Who are you?'"),
            L('eyvind', talk('eyvind', 'Talk to Eyvind', "She sent you. Course she did.\n\nI drank the blood. I swore. And then they burned a farm with the children in it and I couldn't - I couldn't. Now I'm an oathbreaker. That's worse than a murderer, to them. They're [coming].", kw='coming')),
            defend(102, [1172, 1344], 'Protect Eyvind from the blood-fellowship', "The last of the fellowship's hunters lies in the bracken. Eyvind is shaking, but alive.",
                   'Eyvind Asvorsson', 60158514, 14, "Horns in the woods. The blodfelag are here. 'OATHBREAKER!'",
                   [(60158514, 'blodfelag dreng', [14, 15])], 'Keep Eyvind alive', model=M, duration=80,
                   then_boss={'tpl': 60158526, 'name': 'Hrolf Blood-Axe', 'lv': 17, 'announce': "A svard with a blood-red axe strides out. 'You drank my blood, boy. I've come to take it back.'", 'objective': 'Defeat Hrolf Blood-Axe'},
                   thanks="He was my oath-brother. He taught me to hold an axe."),
            L('choose', choice('eyvind', 'Help Eyvind decide',
                   "There are others like me in these woods. Boys who ran. If I go [home], the fellowship will come to Huginfel for me one day. If I stay and lead the [other deserters] north, maybe we can live.\n\nMother would want me home. I know that. What do you think?",
                   [('home', "Home. All right. I'll hang up the axe. And if they come, they come.", 'next:home'),
                    ('other deserters', "Then tell her I'm sorry. Tell her I'm doing something right, for once. Tell her I'll write - I can't write. Tell her I'll learn.", 'next:north')])),
            L('home', end_talk('asvor', 'Return to Asvor', "He's home. He sleeps with the axe under his bed, and he wakes up shouting, and he's HOME.\n\nWhatever comes for him, it'll have to come through me. Here - take this. You brought my boy back.", 'home')),
            L('north', end_talk('asvor', 'Tell Asvor', "Leading the other boys north. My Eyvind. Who couldn't lead a goat to grass.\n\nI'm proud of him. Gods help me, I'm proud of him. Take this. It was meant to be his.", 'north')),
        ],
        {'home': {'text': "You brought my boy back.", 'items': [it_huginfel], 'choice': [it_armring, it_blood]},
         'north': {'text': "It was meant to be his.", 'tragic': True, 'items': [it_huginfel], 'choice': [it_oath2, it_blood]}},
        topics={'scout': "Halvdan. By the gate. He's been watching the ridge for days."})

it_cord = z.item("Haxa's Binding-Cord", 'gem', 20, 'mind', "Plaited from wolf hair and a woman's. Cut now. It still twitches sometimes.")
it_pelt = z.item('Wolf-Brother Pelt', 'cloak', 20, 'finesse', "A sveawolf's grey pelt, freely given.")
it_shield = z.item("Shield-Mate's Ring", 'ring', 20, 'might', "Huscarls who stand together trade rings. Grettir gave you his.")
it_rune = z.item('Gothi Rune-Belt', 'belt', 20, 'faith', "Carved with the runes for 'man' and 'return'.")
z.quest('wolf_cord', 'The Wolf-Cord', 20, 'gothi_valbrand',
        "A huscarl of this keep, Kolbein, vanished on patrol in the west a month ago. Last week a shepherd saw him - running with the sveawolves, on all fours, howling.\n\nThe blood-fellowship's witches, the haxa, bind men to wolf-spirits to make their wolf-warriors. Huscarl [Grettir] was his shield-mate and won't rest. Will you [find Kolbein]? Bring him back a man, if the gods allow it.",
        'find Kolbein',
        "A huscarl vanished on patrol and was seen running on all fours with the wolves. The blood-fellowship's witches bind men to wolf-spirits.",
        [
            talk('huscarl_grettir', 'Ask Huscarl Grettir about the patrol',
                 "We camped by the north bridge. In the night something sang in the woods - a woman's voice. Kolbein got up and walked toward it, and I couldn't wake. I couldn't WAKE. In the morning there were wolf tracks over his [bedroll].", kw='bedroll'),
            reach(102, [510, 390], "Go to the patrol's last camp by the north bridge", "The bedroll's still here, clawed to ribbons. Wolf tracks lead south.", r=20),
            kill(102, [428, 643], 'Hunt the frothing sveawolves', 'frothing sveawolf', 60161138, [18, 19], 5,
                 text="One of them wears a huscarl's arm-ring on its foreleg - Kolbein's. But it isn't Kolbein. It's just a wolf. He's somewhere else."),
            search(102, [450, 572], "Search the old longhouse west of the keep", "a haxa's binding-cord", CRATE,
                   "A cord of plaited hair, wound round a wolf's skull, and the runes for Kolbein's name. A spare. The one that holds him is with the haxa who made it.",
                   give="the haxa's spare cord"),
            boss(102, [319, 342], 'Kill the haxa who bound Kolbein', "The haxa falls. Her wolf-warriors drop their weapons, whimpering. One of them - grey, gaunt, wearing a huscarl's ragged tabard - doesn't run.",
                 'Haxa Grimhild', 20016, 21, "A woman in wolf-skins looks up from her fire and laughs. 'You want the huscarl? He's mine. He likes it.'",
                 objective='Kill Haxa Grimhild', hp=2.4, adds=[(60158532, 'blodfelag wolfwarrior', [18, 19])], every=25, count=2),
            L('kolbein', talk('kolbein', 'Approach Kolbein', "...Grettir? No. No, you smell different.\n\nI remember. I remember the keep, and the mead, and Grettir's terrible singing. I remember it like a story about someone else. The [cord] - she's dead, but it still holds. I can feel it in my chest.", kw='cord')),
            L('cord', choice('kolbein', 'Decide what to do with the wolf-cord',
                   "If you [cut the cord], I'm a man again. The wolf goes out of me and something else goes with it - I don't know what. I'll never run like this again. Never smell the rain coming three valleys off.\n\nOr you [let me run]. Tell Grettir I died well. He'd believe that.",
                   [('cut the cord', "Do it. Do it quick. ... Oh. Oh, gods, I'm cold. Is it always this cold?", 'next:man'),
                    ('let me run', "Thank you. Tell the gothi I'm not sorry. Tell Grettir I'll howl for him on the long nights.", 'next:wolf')])),
            L('man', end_talk('gothi_valbrand', 'Return to the keep', "Kolbein walked through the gate on two feet this morning. Grettir wept like a child.\n\nHe keeps going to the window at night. Standing there, listening. I think he'll do that the rest of his life. But he's ours. The gods were kind, and so were you.", 'man')),
            L('wolf', end_talk('gothi_valbrand', 'Return to the keep', "He chose the wolves.\n\nGrettir hasn't spoken since you told him. Last night we heard howling from the west, long and low, and Grettir went up on the wall and howled back. I said nothing. Take this.", 'wolf')),
        ],
        {'man': {'text': "From the keep, with thanks.", 'items': [it_cord], 'choice': [it_shield, it_rune]},
         'wolf': {'text': "Take this.", 'tragic': True, 'items': [it_cord], 'choice': [it_pelt, it_shield]}},
        topics={'Grettir': "By the gate. He's been standing there a month, as if Kolbein might walk back in."})

# ================================================================================================================= Gotar
z = Zone(103, 'Gotar', 2, 'mid_gotar')
ZONES.append(z)
z.npc('torunn', 'Torunn', [710, 332], 'f', 6, idle="My boy Eilif plays the fiddle. He plays it far too well.")
z.npc('skald_hrafn', 'Old Skald Hrafn', [720, 300], 'm', 20, model=157, idle="Every tune worth playing was stolen from somewhere. Most of the best from water.")
z.npc('eilif', 'Eilif', [392, 1248], 'm', 5, size=40, during=['nacken/eilif', 'nacken/tune'])
z.npc('alfdis', 'Seeress Alfdis', [1245, 870], 'f', 18, idle="I read futures. I couldn't read my own apprentice's heart.")
z.npc('flayer_kolr', 'Flayer Kolr', [1262, 858], 'm', 16, idle="Trolls, witches, gotawitches. I flay what needs flaying.")
z.npc('hild', 'Hild', [985, 1402], 'f', 11, during=['rune_stave/hild'])

it_fiddle = z.item("Nacken's Fiddle-String", 'gem', 7, 'charm', "A single string of silver hair. Pluck it and someone, somewhere, starts to dance.")
it_pool = z.item('Black-Pool Ring', 'ring', 7, 'mind', "Jet from the bottom of the nacken's pool. It is always faintly damp.")
it_bow = z.item("Fiddler's Bow-Bracer", 'bracer', 7, 'finesse', "A strip of horsehair and pine, worn on the wrist the way Eilif wears his.")
it_dance = z.item('Dancing-Green Sash', 'belt', 7, 'might', "Green silk, the kind worn at midsummer dances.")
z.quest('nacken', "The Nacken's Tune", 7, 'torunn',
        "My son Eilif is eleven and plays the fiddle better than any skald in Gotar. He learned it in a summer. From the water, he says - from a man who sits on a stone in the black pool and plays, with his feet in the water.\n\nLast night Eilif went back to pay for the lessons. Old [Hrafn] says the nacken's price is always a life. Will you [find Eilif]?",
        'find Eilif',
        "Torunn's son learned to fiddle from the nacken in the black pool, and has gone back to pay for the lessons.",
        [
            talk('skald_hrafn', 'Ask Old Skald Hrafn about the nacken',
                 "The nacken teaches the best tunes in the world. And there's always one tune at the end - the one that makes people dance till they drop, and drown in his pool. That's how he's paid. He'll be at the black pool in the south-west. Listen for the [fiddle].", kw='fiddle'),
            reach(103, [430, 1300], 'Go to the black pool in the south-west', "Fiddle-music, faint and wild. The wind is dancing - you'd swear it.", r=20),
            kill(103, [459, 1333], "Break the nacken's dancers", 'host of the wind', 60162203, [6, 7], 5,
                 text="The dancing winds blow apart into nothing. The music falters, then starts again, closer to the water."),
            search(103, [400, 1242], 'Search the bank of the black pool', "an empty fiddle-case", CRATE,
                   "Eilif's fiddle-case, open and empty. Small footprints lead right to the water's edge - and stop."),
            boss(103, [392, 1255], 'Face the nacken of the black pool', "The nacken sinks back into the pool, still fiddling, more slowly. On the bank, a small boy coughs up water.",
                 'the Nacken of the Black Pool', 60164357, 9, "A pale man rises from the pool, fiddle under his chin, and smiles. 'He came to pay. Don't be rude.'",
                 objective='Defeat the Nacken', hp=2.0, adds=[(60162203, 'host of the wind', [6, 7])], every=30, count=1),
            L('eilif', talk('eilif', 'Talk to Eilif', "He was nice. He was really nice. He taught me everything. And then he played the last tune and I was dancing in the water and I couldn't stop.\n\nI know it, now. The [tune]. I can still hear it.", kw='tune')),
            L('tune', choice('eilif', 'Help Eilif decide about the tune',
                   "If I play it, people will dance. Kings would pay for that. I'd be the greatest fiddler in Midgard. But they'd dance till they dropped, if I didn't stop. And I don't know if I would.\n\nShould I [burn the fiddle]? Then I'll forget the tune. And all the others. Or should I [keep it], and be careful forever?",
                   [('burn the fiddle', "...Will you hold my hand while it burns? ...Thank you. It's gone. They're all gone. I can't remember a single one.", 'next:burned'),
                    ('keep it', "I'll be careful. I'll be so careful. I'll never play the last one. Never.", 'next:kept')])),
            L('burned', end_talk('torunn', 'Bring Eilif home', "He burned it? His fiddle? He loved that fiddle more than he loves me.\n\nHe can't play a note now. He sat in the kitchen this morning and tried, on his father's old one, and he couldn't. He laughed. He actually laughed. Thank you.", 'burned')),
            L('kept', end_talk('torunn', 'Bring Eilif home', "He's home, and he's playing. Better than ever.\n\nLast night at the hall, everybody danced and nobody wanted to stop. He stopped. He did. I saw his face when he did. I'll be watching him every night of my life.", 'kept')),
        ],
        {'burned': {'text': "Take this, for my boy.", 'items': [it_dance], 'choice': [it_pool, it_bow]},
         'kept': {'text': "Take this, for my boy.", 'tragic': True, 'items': [it_fiddle], 'choice': [it_pool, it_bow]}},
        topics={'Hrafn': "Old Hrafn the skald, by the longhouse. He's heard every story twice."})

it_stave = z.item("Hild's Rune-Stave Charm", 'gem', 14, 'mind', "A splinter of a gotawitch's stave, its blood-runes sanded off. One rune stayed. It means 'sorry'.")
it_seer = z.item("Seeress' Veil", 'cloak', 14, 'faith', "A grey veil, worn by the seers of Gotar when they read the threads.")
it_brand2 = z.item('Unbranded Bracer', 'bracer', 14, 'ward', "A plain leather bracer. Hild wears its twin, over the place a brand would have been.")
it_flay = z.item("Flayer's Hook-Ring", 'ring', 14, 'might', "A troll-flayer's ring, hooked like a skinning knife.")
z.quest('rune_stave', 'The Stolen Rune-Stave', 14, 'alfdis',
        "My apprentice Hild stole my rune-stave - the one with the old blood-runes, the ones I swore never to use - and went south to the gotawitches. To learn what I wouldn't teach her.\n\nThe seers' law is clear. A seer who takes the blood-runes is branded and cast out. Will you [find Hild]? Flayer [Kolr] has seen the gotawitches' runestone.",
        'find Hild',
        "Seeress Alfdis's apprentice stole her rune-stave of forbidden blood-runes and went to the gotawitches.",
        [
            talk('flayer_kolr', 'Ask Flayer Kolr about the gotawitches',
                 "The gotawitches? South, past the woods, at the old runestone. They've seithr orbs floating round it like fireflies - kill those first, or they'll blind you. Your seer's girl went down there two days ago. I didn't stop her. I'm a flayer, not a [nursemaid].", kw='nursemaid'),
            reach(103, [1052, 1272], 'Go south to the gotawitches\' woods', "Lights drift between the trees - orbs of seithr, humming. Beyond them, the runestone glows red.", r=20),
            kill(103, [995, 1422], 'Destroy the seithr orbs', 'seithr orb', 60165740, [9, 10], 5),
            search(103, [990, 1412], 'Search the runestone', "a rune-stave carved with blood-runes", CRATE,
                   "Alfdis's stave, planted in the earth before the stone and hung with fresh blood. Hild's blood, by the size of the cut. The rite's begun.",
                   give="Alfdis's rune-stave"),
            boss(103, [988, 1405], 'Stop the gotawitch rite', "The gotawitch falls, and the runestone's light goes out. A girl sits in the circle with her arms bleeding, crying.",
                 'Gotawitch Svanhvit', 20005, 14, "A gotawitch with a face like a pretty skull steps out of the stone. 'The girl came to me. The blood's half-poured. You're interrupting.'",
                 objective='Defeat Gotawitch Svanhvit', hp=2.2, adds=[(20005, 'gotawitch', [10, 11])], every=30, count=1),
            L('hild', talk('hild', 'Talk to Hild', "She wouldn't teach me. She said I wasn't ready. I wanted to SEE. I wanted to see the real threads, not the pretty ones.\n\nI saw them. I wish I hadn't. Take me back. Let her [brand me]. I deserve it.", kw='brand me')),
            choice('alfdis', 'Bring Hild back to Alfdis',
                   "She's back. And she used them - I can see it in her eyes.\n\nThe law says brand and exile. The law was written by people like me, for girls like her. I could [keep the law]. Or I could [take the blame] - say I taught her, and be branded myself. I'm old. She isn't. Which? I need someone else to say it.",
                   [('keep the law', "Then the law. I'll do it gently. I'll do it myself. She'll go to Myrkwood; I have friends there. Gods forgive me.", 'ending:law'),
                    ('take the blame', "Yes. Yes. It was my stave and my teaching and my fault. I'll go. She'll take my seat. She'll be better than me. She'll have to be.", 'ending:blame')]),
        ],
        {'law': {'text': "Take this. You saved her life, whatever comes.", 'tragic': True, 'items': [it_stave], 'choice': [it_seer, it_flay]},
         'blame': {'text': "Take this. I won't need it where I'm going.", 'items': [it_seer], 'choice': [it_brand2, it_flay]}},
        topics={'Kolr': "Flayer Kolr, by the stables. Rude, but he knows the south woods."})

# ============================================================================================================ Muspelheim
z = Zone(104, 'Muspelheim', 2, 'mid_muspelheim')
ZONES.append(z)
z.npc('dagny', 'Dagny Dagnarsdottir', [1282, 130], 'f', 25, guild='Explorer', idle="My father mapped half of Muspelheim. I mean to map the other half.")
z.npc('hrafnhild', 'Hrafnhild of the Dverge', [585, 1282], 'f', 28, model=M, size=40, idle="Cold-folk. You smell of snow.")
z.npc('dagnar', 'Dagnar the Mapmaker', [598, 1294], 'm', 30, model=157, during=['dagnar/dagnar', 'dagnar/maps'])
z.npc('sven_ashbeard', 'Sven Ashbeard', [1294, 136], 'm', 32, guild='Huscarl', idle="Fire giants took my shield-mates. All of them but one.")
z.npc('ragnvald', 'Ragnvald the Skald', [1256, 1148], 'm', 28, during=['ragnvald/ragnvald'])

it_journal = z.item("Dagnar's Journal-Clasp", 'gem', 25, 'mind', "A brass clasp from a mapmaker's journal, engraved with a compass rose.")
it_chest = z.item('Battered-Chest Belt', 'belt', 25, 'ward', "Leather and brass from a chest that crossed Muspelheim.")
it_forge = z.item("Forgemaster's Bracer", 'bracer', 25, 'might', "Fire-dwarf work. It glows at the edges when you're angry.")
it_compass = z.item('Lodestone Ring', 'ring', 25, 'finesse', "A sliver of lodestone set in silver. It always points home.")
z.quest('dagnar', "The Mapmaker's Chest", 25, 'dagny',
        "My father Dagnar went into Muspelheim three years ago to map it. He never came out. Last month a huscarl told me he'd seen Dagnar's chest by a giants' bridge in the west - battered, lying open.\n\nI want to know what happened. Will you [find the chest]? I'll go mad sitting here another month.",
        'find the chest',
        "Dagny's father went into Muspelheim to map it and never returned. His battered chest has been seen in the west.",
        [
            reach(104, [810, 750], "Go to the giants' bridge in the west", "Charred skeletons patrol the bridge, back and forth, as if guarding something long gone.", r=20),
            kill(104, [834, 666], "Destroy the charred skeletal warriors", 'charred skeletal warrior', 60159105, [23, 24], 5),
            search(104, [452, 812], "Search for Dagnar's battered chest", "a battered chest", CRATE,
                   "Dagnar's chest, burned and scratched, the maps gone. His journal is wedged in the lid. The last entry: 'Going south to the fire-dwarves' mines to trade. The forgemaster wants my maps. I will not give them.'",
                   give="Dagnar's journal"),
            reach(104, [600, 1270], "Go south to the fire-dwarves' mines", "Furnaces roar. Fire-dwarves - dverge - work the forges and watch you sidelong.", r=20),
            talk('hrafnhild', 'Speak with Hrafnhild of the dverge',
                 "The cold-man with the maps? He's alive. Forgemaster Ulvrik keeps him in the furnace-hall, half-blind from the glow, drawing maps for him. Ulvrik means to sell them to the fire giants. The rest of us don't like it. We'll look away while you [deal with him].", kw='deal with him'),
            boss(104, [600, 1300], 'Defeat Forgemaster Ulvrik', "The forgemaster's hammer falls from his hand. In the back of the hall, an old man looks up from a desk of maps.",
                 'Forgemaster Ulvrik', 60160247, 28, "A dverge in a leather apron glowing with heat shoulders out of the furnace-hall. 'The cold-man's mine. His maps are mine.'",
                 objective='Defeat Forgemaster Ulvrik', hp=2.4, adds=[(60160247, 'dverge sparker', [23, 24])], every=25, count=2),
            L('dagnar', talk('dagnar', 'Talk to Dagnar', "Dagny? Dagny sent you? My Dagny? She was fourteen when I left.\n\nI can't see well any more. But I finished them. Every road in Muspelheim, every pass to the giants' halls. The [maps].", kw='maps')),
            L('maps', choice('dagnar', 'Decide what becomes of the maps',
                   "These would let the jarls march an army into Muspelheim - right to the fire giants' doors. War, on their ground for once. Glory, and a great deal of death.\n\nOr fire takes what it's given. [Burn them], and nobody follows my roads. Or [give them to the jarls]. I spent three years and my eyes on them. I can't choose.",
                   [('give them to the jarls', "Then take them. Tell the jarls Dagnar the Mapmaker sends his compliments. And his bill.", 'next:jarls'),
                    ('burn them', "...In the furnace, then. Fire takes what it's given. ...There. Three years. It burns very prettily.", 'next:burned')])),
            L('jarls', end_talk('dagny', 'Return to Dagny', "He's alive. He's ALIVE. He's asleep in my tent and he's grey and blind and ALIVE.\n\nThe jarls' men are already copying the maps. There'll be war in the fire-lands by summer. He says he doesn't mind. I don't believe him.", 'jarls')),
            L('burned', end_talk('dagny', 'Return to Dagny', "He burned them. Three years. He says it was the best thing he ever drew.\n\nHe wants to teach me mapmaking. With his hands on mine, since he can't see. We'll start with Muspelheim, he says. Just the parts no one should follow.", 'burned')),
        ],
        {'jarls': {'text': "Take something. You gave me my father.", 'items': [it_journal], 'choice': [it_forge, it_compass]},
         'burned': {'text': "Take something. You gave me my father.", 'items': [it_journal], 'choice': [it_chest, it_compass]}})

it_lay = z.item("Ragnvald's Lay-Harp Charm", 'gem', 32, 'charm', "A tiny bronze harp. The song it stands for is either true or famous. Not both.")
it_ash = z.item('Ashbeard Ring', 'ring', 32, 'might', "A huscarl's ring, scorched black by giant-fire.")
it_giant = z.item('Fire-Giant Thane Belt', 'belt', 32, 'ward', "Broad enough for two men. Cut down, it fits one very well.")
it_cinder = z.item('Cinder-Silk Cloak', 'cloak', 32, 'mind', "A cloak that cannot burn. The fire giants weave it from something they will not name.")
z.quest('ragnvald', 'The Lay of Ragnvald', 32, 'sven_ashbeard',
        "This is GROUP work, friend. Bring axes.\n\nThe fire giants took my patrol. Eight huscarls. I was the only one who got out. The skald who marched with us, Ragnvald, was taken alive - they keep skalds, to sing for their thanes.\n\nHe's the only one who knows how my shield-mates died. I need him alive. I need the [song]. Will you [get him back]?",
        'get him back',
        "GROUP. Fire giants captured a huscarl patrol's skald. Sven Ashbeard, the only survivor, needs him alive.",
        [
            reach(104, [1320, 560], "Go to the fire giants' lookout posts in the east", "Giants on the ridges, watching the plain. They haven't seen you. Yet.", r=20),
            kill(104, [1324, 567], 'Kill the fire giant lookouts', 'fire giant lookout', 60160878, [28, 29], 4),
            search(104, [1340, 588], 'Search the lookout post', "a skald's harp, strings snapped", CRATE,
                   "Ragnvald's harp. Scratched into the frame in his hand: 'Taken south to the thane's camp. Still singing.' Under it, much smaller: 'Tell Sven I'm sorry.'",
                   give="Ragnvald's harp"),
            kill(104, [1221, 1012], "Cut through the flaming raukomaz on the road south", 'flaming raukomaz', 60160903, [29, 30], 5),
            defend(104, [1256, 1148], "Free Ragnvald from the fire giants' camp", "The giants fall back to their fires. Ragnvald sits in the ash and doesn't look at you.",
                   'Ragnvald the Skald', 60160879, 28, "Ragnvald is chained to a stake, singing hoarsely to a ring of giants. They turn as you come in.",
                   [(60160879, 'fire giant scout', [29, 30])], 'Keep Ragnvald alive', model=M, duration=100, every=22, count=2,
                   then_boss={'tpl': 60160881, 'name': 'Thane Surtling', 'lv': 34, 'hp': 2.8, 'announce': "A fire giant in iron and flame. 'The skald sings for ME. Find your own.'", 'objective': 'Defeat Thane Surtling'},
                   thanks="Sven's alive? Sven? Gods. Then he'll want to know."),
            L('ragnvald', talk('ragnvald', 'Talk to Ragnvald', "I've written the lay, you know. 'The Last Stand of Ashbeard's Eight.' Eight huscarls holding the pass against the giants, to the last man. It's the best thing I've ever made.\n\nIt isn't true. I led them into the ambush. To save myself - I bargained. I bargained with the [giants].", kw='giants')),
            choice('sven_ashbeard', 'Bring Ragnvald to Sven Ashbeard',
                   "Ragnvald. Alive. And he's told you something - I can see it on your face.\n\nHe sold us. Didn't he. ...Then you choose, because I can't. [The truth], and he's outlawed and my men died for nothing. Or [let the song stand], and the lay goes round every hall in Midgard, and my shield-mates are heroes forever. And he walks free.",
                   [('the truth', "The truth. Aye. My men deserve the truth, even if the truth is a coward. ...Get out of my sight, skald. Run. The jarls will hear it before nightfall.", 'ending:truth'),
                    ('let the song stand', "Heroes forever. Let him sing it, then. Let him sing it every night, and know. That's punishment enough. It'll have to be.", 'ending:song')]),
        ],
        {'truth': {'text': "Take something from the giants' hoard. You earned it more than I did.", 'tragic': True, 'items': [it_ash], 'choice': [it_giant, it_cinder]},
         'song': {'text': "Take something from the giants' hoard.", 'items': [it_lay], 'choice': [it_giant, it_cinder]}},
        topics={'song': "What he saw. How they died. I was knocked down in the first rush and woke up alone."}, group=True)

# ======================================================================================================== Myrkwood Forest
z = Zone(105, 'Myrkwood Forest', 2, 'mid_myrkwood')
ZONES.append(z)
z.npc('ottar', 'Ottar Woodcutter', [1100, 640], 'm', 12, idle="I cut trees. That's all. That's all I ever did.")
z.npc('sunniva', 'Sunniva', [1112, 646], 'f', 4, size=40, idle="(She opens her mouth, and nothing comes out. Tears roll down her face, silently, and she points west.)")
z.npc('asgerd', 'Asgerd', [1122, 612], 'f', 16, idle="My husband hasn't slept a night through since winter. Something rides him.")
z.npc('grimkel', 'Grimkel the Sleepless', [1130, 618], 'm', 16, idle="Hoofbeats. Every night. On my chest.")

it_heart2 = z.item('Willow-Heart Pendant', 'neck', 13, 'faith', "A knot of willow heartwood. It hums when it rains.")
it_sap = z.item("Weeping-Sap Ring", 'ring', 13, 'mind', "Amber from a weeping willow, a single tear inside.")
it_wood = z.item("Woodcutter's Belt", 'belt', 13, 'might', "Ottar's own. He won't need it any more.")
it_voice = z.item('Sunniva\'s Ribbon', 'gem', 13, 'charm', "A child's hair ribbon. Sunniva sang the day she gave it to you.")
z.quest('willow_voice', "The Willow's Voice", 13, 'ottar',
        "I felled a willow in the western wood this spring. A big old weeper. The next morning my daughter Sunniva woke and couldn't speak. She cries all day - no sound, just tears.\n\nThe seeress says the willows took her voice in payment. I'd give them anything. I'd give them my axe. Will you [help her]? Talk to her if you like. She can't answer.",
        'help her',
        "Ottar felled an old willow, and the next morning his daughter woke unable to speak, only weep.",
        [
            talk('sunniva', 'Talk to Sunniva', "(She takes your hand and presses something into it: a willow leaf, still green. Then she points west, toward the weeping grove, and shakes her head hard, and points again.)", give='a green willow leaf'),
            reach(105, [680, 640], 'Go to the weeping willow grove in the west', "The willows weep sap like rain. Under the sound of it, very faintly, a little girl's voice humming.", r=20),
            kill(105, [640, 611], 'Fight through the weeping willows', 'weeping willow', 60167842, [11, 12], 5,
                 text="Each one that falls stops humming. The humming moves deeper in."),
            search(105, [700, 660], "Find the stump of the willow Ottar felled", "a stump, still weeping sap", CRATE,
                   "Ottar's axe-marks, clean and deep. The sap has run down the stump and set in shapes like letters: GIVE BACK WHAT WAS TAKEN."),
            boss(105, [690, 650], 'Face the Elder Willow', "The Elder Willow bows, groaning, to the ground. In the hollow of its trunk lies a little knot of heartwood that sings in a child's voice.",
                 'the Elder Willow', 60167842, 16, "The biggest willow in the grove opens eyes of knotted bark. 'THE AXE-MAN TOOK OUR SISTER. WE TOOK HIS DAUGHTER'S SONG.'",
                 objective='Defeat the Elder Willow', hp=2.4, adds=[(60167086, 'tingler', [11, 12])], every=30, count=1),
            choice('ottar', "Bring the singing heartwood to Ottar",
                   "That's - that's her voice. In the wood. Gods.\n\nThe seeress says I can [plant the heartwood] at the stump, and swear never to fell a tree again, and the voice comes home. I'd have to find other work. I'm forty. I've only ever cut trees.\n\nOr I [burn it] in the hearth, and the voice comes home tonight, and the willows remember us forever.",
                   [('plant the heartwood', "Then I'll plant it. And swear. And learn to - I don't know. Keep bees. Sunniva always wanted bees.", 'ending:planted'),
                    ('burn it', "Burn it. Tonight. I want to hear her laugh tonight, not next spring. Let the trees remember.", 'ending:burned')]),
        ],
        {'planted': {'text': "She sang this morning. Take this - she wants you to.", 'items': [it_voice], 'choice': [it_heart2, it_sap]},
         'burned': {'text': "She talks now. Doesn't stop. The willows by the house have started to lean toward it. Take this.", 'tragic': True, 'items': [it_voice], 'choice': [it_wood, it_sap]}})

it_bridle = z.item('Hair-Bridle Bracer', 'bracer', 17, 'finesse', "Braided from a mare's mane - a nightmare's. It twitches when you sleep.")
it_mare = z.item("Mare-Queen's Veil", 'cloak', 17, 'mind', "Black gauze, cold as midnight.")
it_sleep = z.item('Dreamless Ring', 'ring', 17, 'ward', "Whoever wears it sleeps without dreams. Some think that a blessing.")
it_hoof = z.item('Hoofprint Pendant', 'neck', 17, 'might', "A horseshoe of black iron, small as a coin.")
z.quest('mora', 'Hoofbeats in the Night', 17, 'asgerd',
        "My Grimkel hasn't slept a night since winter. Something rides him - a mora, the old women say. A night-mare. It sits on his chest and he can't breathe, can't wake. He's wasting.\n\nThe moras dance in the southern wood, by the old shrine. Will you [stop it]? Ask [Grimkel] what he sees, if he's awake enough to tell you.",
        'stop it',
        "Something rides Asgerd's husband every night - a mora, a night-mare - and he is wasting away.",
        [
            talk('grimkel', 'Ask Grimkel what he sees',
                 "A woman. Pale. Riding a black horse that's also her. Every night, on my chest, galloping. She says I'm hers. She has a [bridle] of hair - my hair. She cut it while I slept.", kw='bridle'),
            reach(105, [835, 1350], "Go to the moras' dancing grounds in the south", "Women dance in a ring, too light on their feet - and some of them have hooves.", r=20),
            kill(105, [840, 1360], 'Break the mora dance', 'mora dancer', 60164160, [14, 15], 6,
                 text="They dissolve into black mist. The ring breaks open. Riders on black horses circle further in."),
            search(105, [848, 1356], 'Search the centre of the ring', "a bridle of braided hair", CRATE,
                   "A bridle of braided hair - several bridles. Each a different colour. One is grey-brown, like Grimkel's.",
                   give="Grimkel's hair-bridle"),
            boss(105, [838, 1352], 'Defeat the Mare-Queen', "The Mare-Queen's horse-half crumbles into ash, then her woman-half. Every bridle in the ring goes limp.",
                 'the Mare-Queen', 60164161, 19, "A rider on a horse that is also herself gallops out of the dark. 'Give me back my reins!'",
                 objective='Defeat the Mare-Queen', hp=2.4, adds=[(60164161, 'mora rider', [15, 16])], every=30, count=1),
            choice('asgerd', "Bring the bridle back to Asgerd",
                   "Is that his? His hair, in a bridle?\n\nThe old women say whoever holds the bridle can ride the mora's dreams - into anyone's sleep. Grimkel wants it. He wants to ride into the dreams of the man who cheated him at the spring fair. He's never been like this.\n\n[Burn it]. Please. Or [give it to him], if you think he's earned his revenge. I can't stop him.",
                   [('burn it', "Thank you. Oh, thank you. ...Listen. He's snoring. He's SNORING.", 'ending:burned'),
                    ('give it to him', "...So be it. He's sleeping now. Smiling. I don't like the smile.", 'ending:given')]),
        ],
        {'burned': {'text': "Take this. We'll both sleep tonight.", 'items': [it_sleep], 'choice': [it_mare, it_hoof]},
         'given': {'text': "Take this.", 'tragic': True, 'items': [it_bridle], 'choice': [it_mare, it_hoof]}},
        topics={'Grimkel': "He's by the hall. Sitting up. He won't lie down any more."})

# ========================================================================================================== Skona Ravine
z = Zone(106, 'Skona Ravine', 2, 'mid_skona')
ZONES.append(z)
z.npc('hallgerd', 'Hallgerd Rindasdottir', [1170, 812], 'f', 26, idle="My husband Bard was bitten at the new moon. The full moon's in nine days.")
z.npc('ulfrun', 'Seithkona Ulfrun', [1182, 796], 'f', 34, idle="Wolfsbane and warder's blood. I've seen it work. Once.")
z.npc('bard', 'Bard', [632, 1228], 'm', 28, during=['moonbound/bard', 'moonbound/cure'])
z.npc('eyvor', 'Ranger Eyvor', [604, 588], 'f', 34, idle="Sidhe in Skona. Sidhe! Three days' march from the jarl's hall.")
z.npc('thorvald', 'Thorvald', [162, 1100], 'm', 34, during=['sidhe_maps/thorvald', 'sidhe_maps/maps'])

it_bane = z.item('Wolfsbane Sachet', 'gem', 28, 'faith', "Dried wolfsbane in a linen bag. Werewolves will not come near it.")
it_moon = z.item('Moonbound Ring', 'ring', 28, 'might', "Silver, of course. It grows warm near the full moon.")
it_warder = z.item("Warder's Fang Bracer", 'bracer', 28, 'finesse', "A werewolf warder's fangs, set in leather.")
it_cub = z.item("Cub's Blanket Cloak", 'cloak', 28, 'ward', "A child's blanket, let out into a cloak. Small hands mended it.")
z.quest('moonbound', 'Moonbound', 28, 'hallgerd',
        "My husband Bard was bitten by a werewolf at the new moon. When the moon's full, he'll change - and stay changed. He ran into the ravine so he wouldn't hurt me.\n\nSeithkona [Ulfrun] knows a cure. One cure. Will you [help Bard]? Nine days. We have nine days.",
        'help Bard',
        "Hallgerd's husband was bitten by a werewolf and fled into the ravine. A cure exists, if it can be made before the full moon.",
        [
            talk('ulfrun', 'Ask Seithkona Ulfrun about the cure',
                 "Wolfsbane from the old grove the ra guard, west of here - that's the first part. And the blood of a werewolf warder, for the second. Mix them by moonlight and it's one dose. Only one. I'll not lie to you about that. Bring me the [wolfsbane] and the blood and I'll brew it.", kw='wolfsbane'),
            kill(106, [735, 740], 'Fight through the ra guarding the wolfsbane grove', 'ra of pine', 60165100, [28, 29], 4),
            search(106, [640, 580], 'Gather wolfsbane from the old grove', "a patch of wolfsbane", CRATE,
                   "Purple hoods, nodding in the ash. You gather an armful.", give='a bundle of wolfsbane'),
            kill(106, [1024, 936], "Take the blood of werewolf warders", 'werewolf warder', 60167872, [27, 28], 5,
                 text="You fill Ulfrun's flask. On the last warder's belt: a child's wooden doll."),
            reach(106, [630, 1225], "Find Bard at the were-hut in the south-west", "Bard is here. Half-changed: hair on his arms, teeth too long. And curled up beside him, asleep, a little girl with ears too pointed.", r=18),
            L('bard', talk('bard', 'Talk to Bard', "Hallgerd sent you. I knew she would.\n\nThat's Ylfa. They bit her a year ago. She's been living with them. She's eight. She found me the first night and stayed. She thinks I'm her father now. The pack's [coming] for her.", kw='coming')),
            defend(106, [632, 1228], 'Protect Bard and the girl', "The pack falls back into the ravine. Bard is bleeding, grinning, and still mostly himself.",
                   'Bard', 60167872, 28, "Howls in the ravine. The pack knows you're here.",
                   [(60167872, 'werewolf warder', [27, 28])], 'Keep Bard alive', model=M, duration=90, every=22, count=2,
                   then_boss={'tpl': 60168002, 'name': 'Grimfang, Wolfaur Headsman', 'lv': 32, 'announce': "A huge wolfaur with an executioner's axe. 'The cub is the pack's. And so are you, bitten one.'", 'objective': 'Defeat Grimfang'},
                   thanks="I'm still me. For a few more days."),
            L('cure', choice('bard', 'Decide who takes the cure',
                   "One dose. Ulfrun was clear.\n\nI could [drink it], and go home to Hallgerd, and Ylfa goes back to the pack - or into the ravine alone. Or [Ylfa drinks it]. She's eight. She could go home - she has a mother in Skona, she told me. And I'd stay what I'm becoming.\n\nYou choose. I can't. Every time I try, I see her face.",
                   [('drink it', "...Forgive me, little one. ...It's bitter. Gods, it's bitter. Take me home before I change my mind.", 'next:bard'),
                    ('Ylfa drinks it', "Yes. Here, little one. Drink. ...There. Take her home. Tell Hallgerd I love her. Tell her not to come looking at the full moon.", 'next:child')])),
            L('bard', end_talk('hallgerd', 'Return to Hallgerd', "He's home. Cured. Ulfrun says it took.\n\nHe told me about the girl. He goes to the edge of the ravine at night and listens. He'll do that for the rest of his life, I think. But he's home.", 'bard')),
            L('child', end_talk('hallgerd', 'Return to Hallgerd', "You brought me a child, and not my husband.\n\nHer mother came from Skona village this morning and fell on her knees in the mud. I watched. I couldn't hate either of them. On the full moon I'll go to the ravine's edge. He told me not to. I'm going anyway.", 'child')),
        ],
        {'bard': {'text': "Take this, with my thanks.", 'items': [it_bane], 'choice': [it_moon, it_warder]},
         'child': {'text': "Take this. The girl made it for you.", 'tragic': True, 'items': [it_cub], 'choice': [it_moon, it_warder]}},
        topics={'Ulfrun': "The seithkona. She's just over there, by the fire. She's done this before."})

it_brooch = z.item('Sidhe Brooch', 'gem', 34, 'mind', "Hibernian silver, worked in a knot that never ends.")
it_niamh = z.item("Niamh's Token", 'neck', 34, 'faith', "A pendant of green glass, warm as a hand.")
it_scout = z.item("Scout's Grey Cloak", 'cloak', 34, 'finesse', "Grey as Skona fog. A scout can lie still in it for a day.")
it_spy = z.item("Spymaster's Ring", 'ring', 34, 'might', "The jarl's spymasters wear these. Thorvald gave you his.")
z.quest('sidhe_maps', "The Sidhe's Maps", 34, 'eyvor',
        "There are sidhe in Skona. A camp of them in the far west - Hibernian druids, three days from the jarl's hall. I sent my best scout, Thorvald, to watch them. That was a month ago.\n\nHe's sent no word. Either they caught him or he's found something worth the silence. Will you [find Thorvald]?",
        'find Thorvald',
        "A Midgard scout sent to watch a sidhe camp in western Skona has sent no word in a month.",
        [
            reach(106, [390, 960], 'Head west through the timber-cat woods', "Big cats in the undergrowth. And on a tree, a ranger's mark, scratched fresh: Thorvald's sign.", r=20),
            kill(106, [388, 945], 'Get past the timber cats', 'timber cat', 60167077, [33, 34], 4),
            search(106, [210, 1060], "Search Thorvald's last watch-post", "a scout's cloak, pinned with a Hibernian brooch", CRATE,
                   "Thorvald's cloak, folded, with a sidhe brooch pinned to it - a gift, not a trophy. The post hasn't been used in weeks. He's gone in."),
            kill(106, [140, 1023], "Fight through the sidhe camp's outer guard", 'sidhe gaoite', 60166006, [34, 35], 5),
            L('thorvald', talk('thorvald', 'Find Thorvald in the sidhe camp', "Gods, keep your voice down - you're from Eyvor? ...Listen.\n\nI got in. I got close to one of their seers, Niamh. Close. She trusted me. She showed me their maps - every road from here to the jarl's hall, every ford, every weak wall. I have them. I was waiting for a chance to run. Then she - then I started to [care].", kw='care')),
            boss(106, [160, 1110], "Fight the sidhe druid who comes for Thorvald", "The druid falls. Behind the tents, a woman in green stands very still, looking at Thorvald.",
                 'Draoi Fionnbarr', 60166005, 37, "A sidhe druid steps out of the trees, staff burning green. 'My sister trusted you, Northman. Give back what you stole.'",
                 objective='Defeat Draoi Fionnbarr', hp=2.5, adds=[(60166006, 'sidhe gaoite', [34, 35])], every=30, count=2),
            L('maps', choice('thorvald', 'Decide what becomes of the sidhe maps',
                   "That was her brother. And that's her, watching us.\n\nThe maps would save Midgard - with them the jarl knows every road Hibernia means to use. Eyvor will make me a hero. And Niamh will know what I was. [Take the maps].\n\nOr I [give them back]. To her. I go home with nothing, and Eyvor knows I failed, and Niamh knows I chose her. I can't. You do it.",
                   [('take the maps', "...Then let's go. Don't look back at her. I'm not going to.", 'next:taken'),
                    ('give them back', "Then I'll walk them over to her myself. ... She took them. She didn't say anything. Let's go home.", 'next:returned')])),
            L('taken', end_talk('eyvor', 'Return to Ranger Eyvor', "The sidhe maps. All of them. The jarl will give Thorvald a hall for this.\n\nHe hasn't said a word since he got back. He sits looking west. Here - from the jarl's purse.", 'taken')),
            L('returned', end_talk('eyvor', 'Return to Ranger Eyvor', "He gave them back. He had the maps of half Hibernia's war in his hands and he gave them back to a sidhe witch.\n\nI should have him whipped. I won't. I've been in love too. Here - take something. Don't tell the jarl.", 'returned')),
        ],
        {'taken': {'text': "From the jarl's purse.", 'tragic': True, 'items': [it_spy], 'choice': [it_scout, it_brooch]},
         'returned': {'text': "Don't tell the jarl.", 'items': [it_niamh], 'choice': [it_scout, it_brooch]}})

# ========================================================================================================= Vanern Swamp
z = Zone(107, 'Vanern Swamp', 2, 'mid_vanern')
ZONES.append(z)
z.npc('thorgunna', 'Thorgunna', [1200, 1150], 'f', 36, idle="My Alf drowned in the swamp four winters ago. He came to my door last night.")
z.npc('clay_boy', 'the Clay Boy', [702, 942], 'm', 20, size=35, during=['clay_child/boy'])
z.npc('gunnvor', 'Runemistress Gunnvor', [1210, 1140], 'f', 48, idle="My brother went into the hagbui barrows for a sword. The hagbui keep what goes in.")

it_clay = z.item('Clay-Child Charm', 'gem', 40, 'charm', "A little clay figure, fingerprints still on it. Small fingerprints.")
it_jotun = z.item('Clay Jotun Bracer', 'bracer', 40, 'might', "Fired clay, hard as iron. It came from something that was nearly alive.")
it_swamp = z.item("Swamp-Mother's Shawl", 'cloak', 40, 'ward', "Thorgunna's shawl. She wore it to the ford every year.")
it_leirr = z.item("Shaper's Ring", 'ring', 40, 'mind', "Taken from the hand of a clay jotun shaper. Everything you touch, for a moment, seems soft.")
z.quest('clay_child', 'The Clay Child', 40, 'thorgunna',
        "My son Alf drowned at the western ford four winters ago. Last night something knocked at my door and called me Mother. It looked like Alf. It was made of mud. Clay. It had his face.\n\nI screamed and slammed the door. It went away crying. Will you [find out what it is]? I can't sleep. I can't stop hearing it cry.",
        'find out what it is',
        "Something made of clay, with her drowned son's face, knocked at Thorgunna's door and called her Mother.",
        [
            reach(107, [1050, 1110], 'Go to the western ford where Alf drowned', "Small footprints in the mud. Clay footprints - they dry and crumble as you watch. They lead west.", r=20),
            kill(107, [935, 1400], 'Cut through the forest vipers on the trail', 'forest viper', 60161042, [39, 40], 5),
            reach(107, [690, 930], "Follow the trail to the clay jotuns' camp", "Clay jotuns, huge and slow, shaping figures from the swamp mud. Among the half-made giants, a small clay boy sits alone.", r=20),
            kill(107, [656, 985], 'Fight through the clay jotuns', 'clay jotun', 60159228, [40, 41], 5),
            L('boy', talk('clay_boy', 'Approach the clay boy', "Are you from Mother? Did she send you?\n\nThe shaper made me out of the ford-mud. Where the boy fell in. He said the mud remembered the boy, so I do too. I remember Mother's soup. And her hands. I went to see her and she [screamed].", kw='screamed')),
            boss(107, [700, 940], 'Defeat the clay jotun shaper', "The shaper slumps into a heap of wet clay. The little clay boy watches it with wide clay eyes.",
                 'Leirr the Shaper', 60159231, 46, "A clay jotun with long fingers rises from its work. 'That one is mine. I made it from a drowned thing. It is for the army.'",
                 objective='Defeat Leirr the Shaper', hp=2.6, adds=[(60159228, 'clay jotun', [40, 41])], every=25, count=2),
            choice('thorgunna', 'Bring the clay boy to Thorgunna',
                   "It's - he's - it's standing behind you. In the rain. And he's crumbling a little, at the edges.\n\nIt isn't Alf. I know that. But it remembers my soup. It remembers my hands.\n\nIf I [take him in], he'll fall apart at the next big rain - Ulf the seer says a month, maybe two. I'd have him a month. Or I [send him back] to the swamp, and the mud, and don't have to watch it happen again.",
                   [('take him in', "Come here. Come in. Mind the step. ...There. He's sitting by the fire. He's drying out. He says it's warm.", 'ending:kept'),
                    ('send him back', "Go back. Go back to the ford. I'm sorry. I'm sorry. I can't. ...He's going. He's not crying. That's worse.", 'ending:sent')]),
        ],
        {'kept': {'text': "Take this. He made it for you, while he could.", 'tragic': True, 'items': [it_clay], 'choice': [it_jotun, it_leirr]},
         'sent': {'text': "Take this. I can't look at it.", 'tragic': True, 'items': [it_swamp], 'choice': [it_jotun, it_leirr]}})

it_legbiter = z.item('Leg-Biter Hilt-Ring', 'ring', 50, 'might', "The pommel-ring of an ancient sword, worn now as a ring. It hums when blood is spilled.")
it_barrow = z.item('Barrow-Dark Cloak', 'cloak', 50, 'ward', "The hagbui sleep in cloaks like this. You don't.")
it_ketil = z.item("Ketil's Rune-Belt", 'belt', 50, 'faith', "A belt carved with the runes of a family that went into the dark and came out.")
it_hagbui = z.item('Hagbui Thane Torc', 'neck', 50, 'mind', "Barrow-gold. Cold enough to make your teeth ache.")
it_runem = z.item("Runemistress' Bracer", 'bracer', 50, 'finesse', "Gunnvor's own. Rune-carved and spell-hard.")
z.quest('barrow_brother', 'The Unburied Thane', 50, 'gunnvor',
        "This is GROUP work. The hagbui are draugr - barrow-dead - and their thane is old and terrible.\n\nMy brother Ketil went into the hagbui barrows in the north-west for our grandfather's sword, Leg-Biter, buried with the thane who killed him. Ketil didn't come out. Last week my seeing-stones showed him walking among the hagbui. Dead. Still walking.\n\nWill you [go into the barrows]?",
        'go into the barrows',
        "GROUP. Runemistress Gunnvor's brother went into the hagbui barrows for an ancestral sword and now walks among the draugr.",
        [
            reach(107, [245, 370], "Go to the hagbui barrows in the north-west", "Barrow-mounds steaming in the cold. The dead walk between them, armed and patient.", r=20),
            kill(107, [238, 366], 'Cut down the hagbui berserkers', 'hagbui berserker', 60161914, [48, 49], 5),
            kill(107, [246, 327], 'Break the hagbui spiritmasters', 'hagbui spiritmaster', 60161919, [46, 47], 4,
                 text="Among them, one draugr wears a living man's ring - Gunnvor's family rune. Ketil, or what's left. He watches you and doesn't come closer."),
            search(107, [272, 360], "Search the thane's barrow", "a runestone at the barrow mouth", CRATE,
                   "'Here lies Ulfhedinn, who slew Gunnar Leg-Biter's-Bearer and took his sword into the dark. Who takes it out takes his place.' Ketil took it out. That's why he walks."),
            boss(107, [272, 350], 'Defeat Thane Ulfhedinn the Unburied', "The thane falls, and the sword Leg-Biter clatters onto the barrow stones. Every hagbui on the mounds stops and turns towards it.",
                 'Thane Ulfhedinn the Unburied', 60161921, 55, "The barrow opens. Something huge and dead in rotten mail climbs out, an empty scabbard at its hip. 'WHO HOLDS MY SWORD?'",
                 objective='Defeat Thane Ulfhedinn', hp=3.0, adds=[(60161914, 'hagbui berserker', [48, 49])], every=25, count=2),
            choice('gunnvor', 'Return to Runemistress Gunnvor',
                   "You've seen him. Ketil. And the sword.\n\nThe runes say whoever bears Leg-Biter out of the barrow takes the thane's place, so Ketil walks. If I [burn the barrows], the hagbui burn - all of them, Ketil too, his soul with them. They'll never walk again.\n\nOr we [bury him with honour] - sword and all, in the thane's own barrow. He'll be the new thane. The hagbui will walk on. But he'll be Ketil, in a way. I can't. Tell me.",
                   [('burn the barrows', "Then I'll carve the fire-runes myself. Tonight. ... Goodbye, Ketil. You always were the brave one.", 'ending:burned'),
                    ('bury him with honour', "Then he'll be thane. Thane of the barrows. Our grandfather would laugh. ...I'll visit him. Once a year. With mead he can't drink.", 'ending:thane')]),
        ],
        {'burned': {'text': "Take something from my grandfather's hoard.", 'tragic': True, 'items': [it_legbiter], 'choice': [it_barrow, it_ketil, it_runem]},
         'thane': {'text': "Take something from my grandfather's hoard.", 'items': [it_hagbui], 'choice': [it_barrow, it_ketil, it_runem]}},
        group=True)

# ============================================================================================================== Raumarik
z = Zone(108, 'Raumarik', 2, 'mid_raumarik')
ZONES.append(z)
z.npc('einar_trapper', 'Einar the Trapper', [1100, 902], 'm', 48, model=157, guild="Trapper's Camp", idle="I've trapped this valley forty years. Never caught anything like her.")
z.npc('sigrid', 'Sigrid', [1106, 906], 'f', 48, guild='Red Dagger', idle="Don't stand between me and the door. Habit.")
z.npc('hroald', 'Hroald Horse-Breeder', [1094, 896], 'm', 52, guild="Trapper's Camp", idle="Sleipnir's get still run wild in the west. Eight legs, and the gods' own blood.")
z.npc('hroald_plain', 'Hroald Horse-Breeder', [404, 622], 'm', 52, during=['grani/free'])

it_dagger = z.item('Red Dagger Ring', 'ring', 50, 'finesse', "A plain ring with a single red stone. Every Red Dagger wears one. Sigrid doesn't, now.")
it_snow = z.item("Trapper's Snow-Cloak", 'cloak', 50, 'ward', "White fur, thick enough to sleep in.")
it_bounty2 = z.item('Bounty-Notice Charm', 'gem', 50, 'mind', "Sigrid's own bounty notice, folded small. She laughs every time she sees it.")
it_hagall = z.item("Bloodnail's Belt", 'belt', 50, 'might', "Hung with the sheaths of a dozen knives. Empty, now.")
z.quest('red_dagger', 'Out of the Red Daggers', 50, 'einar_trapper',
        "Two nights ago a woman came to my fire half-dead of cold with a knife in her side. Sigrid. A Red Dagger - an assassin, one of Hagall's.\n\nShe wants out. Nobody gets out of the Red Daggers. Hagall's put bounty hunters on her trail, and they're close. I'm old, and I've got one bow. Will you [help her]?",
        'help her',
        "A Red Dagger assassin wants out of the guild; her old master has set bounty hunters on her trail.",
        [
            talk('sigrid', 'Talk to Sigrid', "Einar asked you? Kind of him. Stupid, but kind.\n\nI've killed eleven people for Hagall. The twelfth was a child. I said no. You don't say no to [Hagall].", kw='Hagall'),
            kill(108, [790, 1040], "Kill the bounty hunters on Sigrid's trail", 'bounty hunter', 60158666, [50, 51], 4,
                 text="Hard men, well paid. The last one carries a bounty notice."),
            search(108, [790, 1048], "Search the bounty hunters' camp", "a bounty notice", CRATE,
                   "'Sigrid of the Red Daggers. Alive: 500 gold. Dead: 600.' Signed with a red thumbprint. Hagall would rather have her dead.",
                   give="Sigrid's bounty notice"),
            defend(108, [1104, 904], "Defend the trapper's camp when the Red Daggers come", "The Red Daggers melt back into the snow. Sigrid wipes her knife and doesn't look at the bodies.",
                   'Sigrid', 60165226, 48, "Shapes in the snow - red-masked, silent. Hagall's sent his own.",
                   [(60165226, 'Red Dagger', [47, 48])], 'Keep Sigrid alive', model=F, duration=100, every=22, count=2,
                   then_boss={'tpl': 60165226, 'name': "Bloodnail, Hagall's Second", 'lv': 53, 'hp': 2.6, 'announce': "A tall Red Dagger with nails painted red. 'Sigrid. Hagall says come home, or come home in pieces.'", 'objective': 'Defeat Bloodnail'},
                   thanks="That was Bloodnail. He taught me. Gods, he taught me everything."),
            choice('sigrid', 'Talk to Sigrid',
                   "Hagall will send more. He'll never stop.\n\nI could [go back] - into the camp, alone, at night. I know every guard. I could kill him. I probably wouldn't come out. Or I [disappear] south, a new name, a new face, and spend my life looking over my shoulder.\n\nYou've bled for me. You choose.",
                   [('go back', "Then I'll go tonight. Einar, keep the fire lit. If I'm not back by spring, burn my things.", 'ending:back'),
                    ('disappear', "South, then. A fishing village. I'll learn to mend nets. I'll be terrible at it. Thank you.", 'ending:gone')]),
        ],
        {'back': {'text': "Take this. I won't need it.", 'tragic': True, 'items': [it_dagger], 'choice': [it_snow, it_hagall]},
         'gone': {'text': "Take this.", 'items': [it_bounty2], 'choice': [it_snow, it_hagall]}})

it_grani = z.item("Grani's Mane-Braid", 'gem', 54, 'finesse', "Eight braids of grey mane, one for each leg. The gods' own horse-blood.")
it_fenrir = z.item('Fenrir Blood-Bowl Torc', 'neck', 54, 'mind', "Beaten from the fenrir's blood-bowl. Scrubbed. Scrubbed again.")
it_saddle = z.item("Breeder's Saddle-Belt", 'belt', 54, 'ward', "Hroald's own, from forty years of riding.")
it_stallion = z.item('Eight-Hoof Ring', 'ring', 54, 'might', "A ring of eight tiny silver hooves.")
it_rein = z.item("Jarl's Rein-Bracer", 'bracer', 54, 'faith', "The bracer of a jarl's horse-master.")
z.quest('grani', "Sleipnir's Get", 54, 'hroald',
        "GROUP work, this - the fenrir are no joke.\n\nThe sleipneirsson - Sleipnir's get, eight-legged, the gods' own blood - run wild on the western plain. There's a foal among them this year, grey as smoke. I've watched it all summer.\n\nThe fenrir have seen it too. They want its blood for some rite. Will you [save the foal]?",
        'save the foal',
        "GROUP. The fenrir hunt a foal of Sleipnir's line on the western plain for its blood.",
        [
            reach(108, [420, 640], 'Go to the western plain', "Eight-legged horses graze in the snow, wary. The foal is easy to spot: smaller, greyer, and never far from its mother.", r=20),
            kill(108, [575, 815], 'Kill the fenrir soldiers stalking the herd', 'fenrir soldier', 60160797, [52, 53], 5),
            search(108, [520, 700], 'Search the fenrir hunting camp', "a fenrir blood-bowl", CRATE,
                   "A great bowl of black iron, carved with wolves. Runes round the rim: 'The blood of the eight-legged makes the wolf a god.'"),
            defend(108, [400, 630], 'Protect the foal', "The fenrir break and flee. The foal stands trembling beside its mother - and then, very carefully, comes over to sniff your hand.",
                   'Grani, Sleipnir\'s foal', 60166226, 50, "Howls on every side. The fenrir come for the foal in a ring.",
                   [(60160797, 'fenrir soldier', [52, 53])], "Keep the foal alive", duration=110, every=22, count=2,
                   then_boss={'tpl': 60160797, 'name': 'Fenrir Bloodseer', 'lv': 57, 'hp': 3.0, 'announce': "A fenrir in a wolf-skull mask, holding a knife of bone. 'The foal's blood is ours. Wolves will be gods.'", 'objective': 'Defeat the Fenrir Bloodseer'}),
            L('free', choice('hroald_plain', 'Talk to Hroald on the plain',
                   "Look at him. Look at him. He likes you.\n\nThe jarl would give me a hall for this foal - broken to the saddle, he'd carry a jarl to war like the gods' own. I've wanted to [tame him] my whole life.\n\nOr we [set him free]. He'll run with his mother, and nobody will ever ride him, and someday some other fenrir will come. Your choice. You saved him.",
                   [('tame him', "Then I'll be gentle. I swear on my mother. He'll be the finest horse in Midgard.", 'ending:tamed'),
                    ('set him free', "...Go on, then. Go on. Run. ... Look at him go. Gods. Look at him go.", 'ending:free')])),
        ],
        {'tamed': {'text': "Take something. The jarl will pay me back tenfold.", 'items': [it_rein], 'choice': [it_fenrir, it_saddle, it_stallion]},
         'free': {'text': "Take something.", 'items': [it_grani], 'choice': [it_fenrir, it_saddle, it_stallion]}},
        group=True)

# ============================================================================================================== Malmohus
z = Zone(116, 'Malmohus', 2, 'mid_malmohus')
ZONES.append(z)
z.npc('halla', 'Halla Bjornsdottir', [1000, 502], 'f', 40, guild="Hunters' Camp", idle="My brother found a god in Malmohus. A dragon one.")
z.npc('bjorn_convert', 'Bjorn the Convert', [662, 280], 'm', 36, during=['missionary/bjorn'])
z.npc('svein_smith', 'Svein Hammerhand', [1006, 494], 'm', 50, guild="Hunters' Camp", idle="Svartalfar forging Norse steel. My steel, near enough.")

it_scale2 = z.item("Convert's Scale-Pendant", 'neck', 40, 'faith', "A dragon scale on a cord, the drakulv's holy sign. Bjorn wore it.")
it_halla = z.item("Halla's Hunting Cloak", 'cloak', 40, 'finesse', "Bearskin, from a bear Halla killed at fourteen.")
it_sacr = z.item("Sacrificer's Knife-Ring", 'ring', 40, 'might', "A drakulv sacrificer's ring, its blade-edge filed down.")
it_bjorn = z.item("Bjorn's Prayer-Belt", 'belt', 40, 'mind', "Knotted with prayers to a dragon. Bjorn says the knots still work, whoever you pray to.")
z.quest('missionary', 'The Dragon\'s Missionary', 40, 'halla',
        "My brother Bjorn came to Malmohus to hunt with me. Then the drakulv missionaries got to him - the dragon-worshippers. He's taken their scale and their name. He preaches with them in the northern tents.\n\nHe's soft-hearted. They found the soft place and pressed. Will you [find Bjorn]? Talk to him. He won't listen to me.",
        'find Bjorn',
        "Halla's brother has joined the drakulv dragon-worshippers and preaches with their missionaries.",
        [
            reach(116, [640, 290], "Go to the drakulv missionaries' tents in the north", "Drakulv in robes preach to the air, and a few ragged Norse listen, nodding.", r=20),
            kill(116, [658, 271], 'Scatter the drakulv missionaries', 'drakulv missionary', 60160115, [37, 38], 5,
                 text="A big Norseman in drakulv robes stands among the fallen, praying for them."),
            L('bjorn', talk('bjorn_convert', 'Talk to Bjorn', "Halla sent you. She worries.\n\nYou don't understand. The dragon is real. She sleeps under the ice in the south and dreams the world. The drakulv were kind to me when nobody else was. They said I could matter. They're taking me south for the [great rite] at the next moon.", kw='great rite')),
            kill(116, [600, 520], 'Ambush the drakulv patrol bound for the rite', 'patrolling drakulv', 60164855, [39, 40], 5,
                 text="One carries orders for the rite: a sacrifice. A Norse convert, 'big and willing'. They mean Bjorn."),
            boss(116, [615, 505], "Confront the drakulv preacher who claimed Bjorn", "The preacher falls. Bjorn, who followed you, stands looking at the orders in his hands.",
                 'Preacher Vrakulv', 60160115, 44, "A drakulv in a mitre of scales. 'The big one is promised. The dragon is hungry. You are... also acceptable.'",
                 objective='Defeat Preacher Vrakulv', hp=2.5, adds=[(60164855, 'patrolling drakulv', [39, 40])], every=25, count=2),
            choice('halla', 'Bring Bjorn back to Halla',
                   "He's here. And he knows, now. He read the orders.\n\nHe still wears the scale. He says the dragon isn't the drakulv's fault - that something is really there, under the ice. I don't care what he believes. I care that he's alive.\n\nShould I [take the scale] from him? Or [let him keep it], and pray to his dragon by himself?",
                   [('take the scale', "Here, Bjorn. Give it here. ...He gave it to me. He's crying. I'm crying. It's ugly. Here - take it. I don't want it near him.", 'ending:taken'),
                    ('let him keep it', "Then he'll keep it. He can pray to the moon for all I care, as long as he does it here, with me. Thank you.", 'ending:kept')]),
        ],
        {'taken': {'text': "Take it. And this.", 'items': [it_scale2], 'choice': [it_halla, it_sacr]},
         'kept': {'text': "Take this, for bringing him back.", 'items': [it_halla], 'choice': [it_sacr, it_bjorn]}})

it_svart = z.item('Svartalf-Steel Bracer', 'bracer', 50, 'might', "Norse steel, svartalf-forged. Better than Svein's. Don't tell him.")
it_forge2 = z.item("Hammerhand's Ring", 'ring', 50, 'ward', "Svein's mark, the hammer and anvil, stamped in silver.")
it_alch = z.item('Alchemist\'s Phial-Belt', 'belt', 50, 'mind', "A svartalf alchemist's belt, hung with empty phials.")
it_foist = z.item("Foister's Cloak", 'cloak', 50, 'finesse', "A svartalf foister's cloak: it makes whatever you carry look like something else.")
it_bind = z.item('Bloodbinder Torc', 'neck', 50, 'faith', "A svartalf bloodbinder's torc. Something written inside it keeps trying to be read.")
z.quest('svartalf_steel', 'Forged in Darkness', 50, 'svein_smith',
        "GROUP work. Svartalfar aren't fools, and they don't fight fair.\n\nSomeone's forging blades stamped with my mark - the hammer and anvil - and selling them to the drakulv. Good blades, too good. The svartalfar in the east have a forge in the north-east hills.\n\nI want it shut. I want to know who's been [selling my mark]. Will you [shut the forge]?",
        'shut the forge',
        "GROUP. Someone is forging blades with Svein Hammerhand's mark and selling them to the drakulv - from a svartalf forge in the north-east.",
        [
            kill(116, [1291, 421], 'Kill the svartalf infiltrators on the eastern road', 'svartalf infiltrator', 55003, [46, 47], 5,
                 text="One carries a drakulv purse and a letter: 'Thirty more blades by the new moon. The smith's mark, as before. -E.'"),
            kill(116, [1380, 470], 'Break the svartalf foisters', 'svartalf foister', 55004, [48, 49], 5),
            search(116, [1470, 150], 'Search the svartalf forge in the north-east', "a crate of blades stamped with a hammer and anvil", CRATE,
                   "Thirty blades. Svein's mark on every one. And a ledger: 'E.' has been paid in svartalf gold for each - E, for Egil, Svein's own apprentice.",
                   give="the forger's ledger"),
            boss(116, [1460, 160], 'Defeat the svartalf forgemaster', "The forge's fires gutter out. Behind the anvil, a young Norse smith in a leather apron raises his hands.",
                 'Forgemaster Dvalinn the Black', 55002, 54, "A svartalf in a mask of soot steps out of the forge-smoke, hammer smoking. 'Northmen. You've cost me a customer.'",
                 objective='Defeat Forgemaster Dvalinn', hp=3.0, adds=[(55004, 'svartalf foister', [48, 49])], every=25, count=2),
            choice('svein_smith', 'Return to Svein Hammerhand',
                   "Egil. My Egil. I taught him to hold tongs. I was going to leave him the forge.\n\nHe's outside, waiting. He says the svartalfar threatened his mother. He says he was going to tell me. Maybe it's true.\n\nThe jarl hangs men who sell steel to the enemy. I could [hand him over]. Or [forgive him], and he works my forge for nothing till he's grey, and I watch him every day. You've seen the ledger. You choose.",
                   [('hand him over', "...The jarl's men are already coming up the road. I'll walk him down myself. Leave me alone a while after.", 'ending:law'),
                    ('forgive him', "Forgiven. Not forgotten. He'll work till his arms fall off. ...Thank you. I didn't want to be the man who hanged his own boy.", 'ending:forgiven')]),
        ],
        {'law': {'text': "Take something from the forge. I can't look at any of it.", 'tragic': True, 'items': [it_forge2], 'choice': [it_svart, it_alch, it_foist, it_bind]},
         'forgiven': {'text': "Take something from the forge.", 'items': [it_forge2], 'choice': [it_svart, it_alch, it_foist, it_bind]}},
        topics={'selling my mark': "My hammer and anvil. Only one man in Midgard has the right to stamp it, and he's standing in front of you."}, group=True)
