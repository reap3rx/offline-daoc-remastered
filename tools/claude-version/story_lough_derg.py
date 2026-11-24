"""Lough Derg's story quests (claude 2026-11-05; the arcs 2026-11-22) - see story_gen.py. Places: zone metres [x, y].

Moved out of story_hib.py with the Lough Derg rebuild, so the zone is one file like its zone build and events:
    python tools/claude-version/story_gen.py story_lough_derg
"""
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

# ------------------------------------------------------------------ the Lough Derg rebuild's story arcs (claude 2026-11-22)
# Owner (Lough Derg plan): "Events that tie into the theme, flare up areas, tell side stories related to quests ... adapt
# the quests and events already there, and be willing to scrap anything that doesn't fit." Six arcs, one per faction of
# the zone build, three to four quests each, linked by one thread: the red-hand silver of Ruadhan, warlord of the island,
# who is buying Mag Mell's troubles until the harvest is in. Old quests folded in (and turned off, QuestCleanup.cs):
# Youth Gone Wrong, Balm Hunt, Rhian's Dyes, Balance of Nature, Beautiful Music, Kylirean's New Armor, Lesser of Two
# Evils, Alastriona's Chest, Riona's Revenge, Regional Distinctions. Kill steps with "target" count the zone build's own
# monsters (they scale to you); "replaces" hides the old quest giver of the same name.

def hunt(at, goal, target, count, text=None, give=None, label=None):
    s = {'type': 'kill', 'zone': 200, 'at': list(at), 'radius': 40, 'goal': goal, 'target': target, 'count': count}
    if text:
        s['text'] = text
    if give:
        s['give'] = {'name': give}
    if label:
        s['label'] = label
    return s


def tk(step, tier):
    """A kill step's spawned monster at a con tier (it scales to you like the zone's own)."""
    step['mob']['tier'] = tier
    return step


def gives(step, name):
    step['give'] = {'name': name}
    return step


def wake(ending, chain):
    ending['wake_event'] = chain
    return ending


def replaces(npc_id):
    next(n for n in z.npcs if n['id'] == npc_id)['replaces'] = True


Z = 200
RED_WOOD = 1876
# ------------------------------------------------------------------ people
z.npc('mandra', 'Mandra', [702, 175], 'f', 4, model=430, size=48,
      idle="Sixteen, and he thinks he knows the world. I was sixteen once. I know exactly what he knows.")
replaces('mandra')
z.npc('dallan', 'Dallan', [455, 380], 'm', 6, size=42, guild='villainous youth', during=['mandras_boy/dallan', 'mandras_boy/choose'])
z.npc('nessa', 'Bonesetter Nessa', [664, 178], 'f', 18, idle="Bites, breaks and bad luck. Mostly bites, this season.")
z.npc('cormac', 'Farmer Cormac', [706, 140], 'm', 12, idle="Turnips. A whole field. Dug up, bitten once each, and dropped.")
z.npc('rhian', 'Rhian the Dyer', [697, 207], 'f', 14, idle="Woad for blue, weld for yellow, madder for red. And for pests - well. You'll see.")
replaces('rhian')
z.npc('orlaith', 'Orlaith the Herbwife', [438, 812], 'f', 22, model=362,
      idle="Glowcaps, dew, mere-weed. Everything worth having grows where the good folk are.")
z.npc('sabha', 'Sabha', [209, 830], 'm', 3, model=112, size=51, idle="Sabha watches the water. Sabha likes fish.")
replaces('sabha')
z.npc('tavie', 'Tavie', [574, 1125], 'f', 16, model=310, idle="A drum's a heart you can hold. Mine was stolen.")
replaces('tavie')
z.npc('lady', 'the Lady of the Mere', [252, 902], 'f', 30, model=603, size=55, guild='the Mere',
      during=['beautiful_music/lady', 'the_ladys_bargain/ask'])
z.npc('cathbad', 'Reeve Cathbad', [714, 214], 'm', 20, idle="Every sack counted in. Every sack counted out. And still the numbers lie.")
z.npc('fereinn', 'Fereinn', [1229, 688], 'm', 19, model=335, guild='an exile',
      idle="Siabra, yes. Not theirs. Not anyone's. Say what you came to say.")
replaces('fereinn')
z.npc('oran', 'Seanchai Oran', [664, 213], 'm', 30, idle="Every barrow has a story. That one's story was 'stay shut'.")
z.npc('riona', 'Riona', [860, 824], 'f', 18, model=327, idle="A month in a siabra pit. Ask me how I am. Go on.")
replaces('riona')
z.npc('ronan', 'Ronan of the Roane', [1180, 1028], 'm', 20, guild='the Roane',
      idle="The lake remembers everything. Lately it remembers blood.")
z.npc('cara', 'Cara the Lorewoman', [602, 1142], 'f', 30, model=362,
      idle="Ask me about anything older than your grandmother. Newer things, ask the market.")
z.npc('lir', 'Captain Lir', [676, 222], 'm', 40, guild='Mag Mell Guard',
      idle="Mag Mell has walls on three sides. The fourth side is the lake. Think about that.")

# ======================================================================== Mandra's Boy (the villainous youth, 4 to 9)
i1 = z.item("Mended-Elbow Bracer", 'bracer', 4, 'finesse', "Cut from the sleeve of a blue coat. Mandra mended that elbow four times.")
i2 = z.item("Mother's Worry-Stone", 'gem', 4, 'faith', "Worn smooth by a thumb, over a great many nights.")
z.quest('youth_gone_wrong', 'Youth Gone Wrong', 4, 'mandra',
        "Oh - you're not one of them. Good. I've no time to talk. Two of the villainous youths came by the hall last night and said they'd be back for my son's [debts]. They said it like a promise.\n\nWill you [stand with me]? Just tonight. Just till they've gone.",
        'stand with me',
        "Mandra's son Dallan has run off with the villainous youths, and the gang has come to collect his debts from her.",
        [
            defend(Z, [706, 168], 'Stand with Mandra behind the hall', "The last of them runs for the trees, shouting that Dallan will hear of this. Mandra sits down hard on the step.",
                   'Mandra', 60167226, 4, "Two figures in gang colours step out from behind the hall, then two more. 'Where's the money, Mandra?'",
                   [(60167680, 'villainous youth', [4, 5])], 'Keep Mandra safe', model=430, duration=60, every=20, count=1,
                   then_boss={'tpl': 60165444, 'name': 'Scab', 'lv': 6, 'hp': 1.6, 'announce': "A big lad with a scabbed lip shoves through. 'Dallan's MY mate. His debts are MY debts.'", 'objective': 'Defeat Scab'},
                   thanks="Thank you. Thank you. They'll not come back tonight."),
            talk('mandra', 'Talk to Mandra', "They called him one of theirs. My Dallan. He's sixteen, and soft, and he cries at lambing.\n\nThey camp in the woods west of the north road. Go and [look] for him. Don't hurt him. Please - whatever he's done, don't hurt him.", kw='look'),
            reach(Z, [445, 395], 'Find the villainous youths\' north camp', "Ragged tents, a fire, a dog. And a boy's blue coat with a mended elbow hung on a branch. Dallan is here, or was.", r=30),
            search(Z, [430, 414], "Search Dallan's corner of the camp", "Dallan's bedroll", BEDROLL,
                   "Under the bedroll, a purse of new silver - more than a boy earns robbing the road in a year. Every coin is stamped with a red hand.",
                   give='a purse of red-hand silver'),
            end_talk('mandra', 'Bring the purse to Mandra', "Red hands. I've never seen coin like it.\n\nHe's alive. He's eating, by the weight of this. ...He's being paid, isn't he? Somebody's paying children to rob the road. Who does that? Who would ever pay for that?", 'default'),
        ],
        {'default': {'text': "Take this. It's not much. You stood behind my hall in the dark for a stranger.", 'choice': [i1, i2]}},
        topics={'debts': "Dallan took their silver and wore their colours. Now they say he owes them, and if he won't pay, I will."})

i3 = z.item("Gang-Colour Sash", 'belt', 6, 'finesse', "Blue and grey, the villainous youths' colours. Dallan wore it inside out the day he came home.")
i4 = z.item("Lambing-Night Ring", 'ring', 6, 'ward', "A shepherd's ring, given to whoever sat up all night with the ewes.")
i5 = z.item("Spy's Pebble", 'gem', 6, 'charm', "Dallan's signal: a white pebble on the gatepost meant 'I'm safe'.")
z.quest('mandras_boy', "Mandra's Boy", 6, 'mandra',
        "I asked the guards about the red hand. Nobody knows it, or nobody will say.\n\nBut Dallan will. Go back to the north camp and [talk to him]. Talk, not fight. If the lieutenant's about, he won't say a word, so thin the camp out first.",
        'talk to him',
        "Dallan is being paid in red-hand silver. Mandra wants to know why - and by whom.",
        [
            hunt([432, 408], 'Thin out the recruits at the north camp', 'villainous youth recruit', 4,
                 text="With the recruits scattered, a boy in a blue coat slips away from the fire and waves you into the trees."),
            L('dallan', talk('dallan', 'Talk to Dallan', "You came from Mam. I know. She sends everyone.\n\nI'm not a fool. I know what they are. But listen: the lieutenant gets a purse every week from a man who doesn't talk like us. He talks like the folk across the lake. Red hand on the purse, red hand on his ring. He wants the road kept dangerous. Who'd [pay] for that?", kw='pay')),
            L('choose', choice('dallan', 'Help Dallan decide',
                   "If I go home now, they'll know I talked, and they'll come for Mam again. If I stay inside, I can find out who the man with the ring is.\n\nTell me. Do I [come home], or do I [stay inside]?",
                   [('come home', "...Home, then. Tell her I'm coming. Tell her to hide the good bread.", 'next:home'),
                    ('stay inside', "Right. I'll leave a white pebble on her gatepost every night I'm safe. Tell her to look.", 'next:inside')])),
            L('home', end_talk('mandra', 'Return to Mandra', "He walked in an hour ago, ate everything in the house and fell asleep at the table.\n\nHe says there's a man with a red ring. He says it like it frightens him. It frightens me.", 'home')),
            L('inside', end_talk('mandra', 'Return to Mandra', "He's staying. With them. To spy, he says, like a boy in a story.\n\nThere was a white pebble on the gatepost this morning. I put it in my pocket. I'll keep every one.", 'inside')),
        ],
        {'home': {'text': "He brought this home in his pocket. He wants you to have it.", 'choice': [i3, i4]},
         'inside': {'text': "Take this. For watching over him.", 'choice': [i3, i5]}},
        requires='youth_gone_wrong')

i6 = z.item("Paymaster's Signet", 'ring', 8, 'might', "A plain ring of dark iron, the red hand scraped off it. The weight is still good.")
i7 = z.item("Lieutenant's Bandolier", 'belt', 8, 'finesse', "Corr's, with a dozen little pockets, every one of them empty now.")
z.quest('the_paymaster', 'The Paymaster', 8, 'mandra',
        "Dallan's sent word. The paymaster comes tonight to the east camp, the one on the hill above the north road. Dallan says he'll be there, at the fire, with the lieutenant's hand on his shoulder.\n\nCatch the man with the red ring and we'll know who's buying our road. Will you [go to the east camp]?",
        'go to the east camp',
        "The man who pays the villainous youths in red-hand silver comes tonight to their east camp.",
        [
            reach(Z, [528, 345], 'Go to the villainous youths\' east camp', "The lieutenant's fire. A horse that isn't a Hibernian horse, tied in the trees. Dallan by the fire, pale, and the lieutenant's hand heavy on his shoulder.", r=30),
            boss(Z, [530, 330], 'Defeat Lieutenant Corr', "Corr goes down hard. The horse in the trees is gone - the paymaster rode off the moment the swords came out. Something fell from his saddle.",
                 'Lieutenant Corr', 60165444, 9, "'You brought a friend, Dallan? You brought a FRIEND?'",
                 objective='Defeat Lieutenant Corr', hp=1.9, adds=[(60165444, 'villainous youth thug', [7, 8])], every=30, count=1),
            search(Z, [540, 322], 'Search where the paymaster\'s horse stood', "a dropped saddlebag", CRATE,
                   "Orders, in a careful hand: 'Keep the north road bloody until the harvest is in. Keep the youths angry and paid. - R.' Sealed with a red hand.",
                   give="the paymaster's orders"),
            end_talk('mandra', 'Bring the orders to Mandra', "'Keep the road bloody until the harvest is in.'\n\nWhat happens after the harvest? ...Dallan's safe, at least. He ran all the way home. I'll show these to Reeve Cathbad; he counts everything, he'll know who counts in red hands.", 'default'),
        ],
        {'default': {'text': "Take this, with my thanks. And his.", 'choice': [i6, i7]}},
        requires='mandras_boy')

i8 = z.item("Ringleader's Knuckle-Ring", 'ring', 9, 'might', "Heavy, ugly and effective, like its last owner.")
i9 = z.item("South-Camp Cloak", 'cloak', 9, 'ward', "The ringleader's own cloak, patched with the colours of every gang he broke to make his.")
i10 = z.item("White-Pebble Pendant", 'neck', 9, 'charm', "One of Dallan's white pebbles, bored through and strung. 'I'm safe.'")
z.quest('break_the_gang', 'Breaking the Gang', 9, 'mandra',
        "Without Corr, the youths in the north are lost lambs. Half have gone home already.\n\nThe south camp is different. The ringleader there is a grown man, and cruel, and Dallan says the red-hand silver goes through him first. Break him and the gang breaks. Take friends. Will you [break the gang]?",
        'break the gang',
        "The rowdy ringleader at the south camp holds the villainous youths together - and handles the red-hand silver.",
        [
            hunt([300, 1375], 'Fight through the rowdies at the south camp', 'rowdy', 4),
            hunt([300, 1375], 'Defeat the rowdy ringleader', 'rowdy ringleader', 1,
                 text="The ringleader falls. The camp melts into the woods - and from the high road north comes shouting: the highwaymen who took his silver are out on the road."),
            end_talk('mandra', 'Return to Mandra', "Dallan's home for good. He says the youths are going home too, in ones and twos - the ones with homes. The rest went to Mog, on the high road.\n\nYou gave me back my son. I can't give you anything like that. Take this.", 'default'),
        ],
        {'default': wake({'text': "And Dallan says to watch the high road. Mog's lot will be desperate now.", 'items': [i10], 'choice': [i8, i9]}, 'lough_derg_highway_robbery')},
        requires='the_paymaster', group=True)

# ======================================================================== The Hill War (the hill pests, 3 to 8)
h1 = z.item("Balm-Tin Charm", 'gem', 3, 'faith', "Nessa's old balm tin. It still smells of mudman and mint.")
h2 = z.item("Rat-Tail Lace", 'bracer', 3, 'finesse', "Don't ask what the lace is made of.")
z.quest('balm_hunt', 'Balm Hunt', 3, 'nessa',
        "Cormac's boy came in with a bite on his leg the size of my hand. Rat boy, he says, up by the spring. It's gone angry.\n\nI can draw it with a balm, but I need two things I don't keep: [mud] from a mudman, and a rat boy's tail. Will you [fetch them]?",
        'fetch them',
        "Farmer Cormac's son was bitten by rat boys at the spring. Bonesetter Nessa needs the makings of a balm.",
        [
            hunt([912, 175], 'Take a tail from a rat boy at the hideout', 'rat boy', 2, give='a rat boy tail',
                 text="A tail. A sorry thing. Nessa said any one would do."),
            hunt([1088, 162], "Scrape mud from a mudman by the curmudgeons' store", 'mudman', 1, give='a lump of mudman mud',
                 text="The mudman slumps into a heap that's mostly mud. You take a handful. It's warm, and it twitches."),
            end_talk('nessa', 'Bring the makings to Nessa', "Good. Hold his leg. ...There. The swelling's going already.\n\nTadhg says it wasn't just rat boys at the spring. The spraggons and the lucradans were there too, all three at each other's throats. Over water, he says. Tell his father.", 'default'),
        ],
        {'default': {'text': "Take this. And wash your hands before you eat anything.", 'choice': [h1, h2]}},
        topics={'mud': "Mudman mud has a bit of the curmudgeons' magic in it. Draws poison like nothing else. They shamble round the store east of town."})

h3 = z.item("Woad-Blue Gloves Charm", 'gem', 5, 'charm', "Rhian's dyeing gloves, shrunk to a charm. Still blue. Always blue.")
h4 = z.item("Three-Pot Belt", 'belt', 5, 'might', "Hooks for three dye-pots: blue, yellow and red.")
z.quest('three_kinds_of_trouble', 'Three Kinds of Trouble', 5, 'cormac',
        "My fields are ruined. Not robbed - ruined. Dug, trampled, every turnip bitten once and dropped.\n\nNessa says the pests are fighting up at the spring, and I say they're fighting through my field to get there. Rhian the dyer has an idea about [marking] them. Daft, but I've none better. Will you [help Rhian]?",
        'help Rhian',
        "Something crosses Cormac's fields every night. Rhian the dyer means to find out what, with dye.",
        [
            talk('rhian', 'Ask Rhian about her plan', "Cormac thinks I'm daft. I'm not. Wild lucradans moult in autumn - hair everywhere. Spraggonolls carry bone charms. Rat boys, well, rat boys I can find by the smell.\n\nBring me lucradan hair and a spraggon charm and I'll brew a [dye] that clings to whatever made it. Splash the furrows, and in the morning we'll see whose feet are what colour.", kw='dye'),
            hunt([488, 88], 'Gather hair from wild lucradans at the warren', 'wild lucradan', 2, give='a fistful of lucradan hair'),
            hunt([825, 100], 'Take a bone charm from a spraggonoll at the den', 'spraggonoll', 2, give='a spraggonoll bone charm'),
            talk('rhian', 'Bring the makings to Rhian', "There. Three pots: blue for the lucradans, yellow for the spraggons, red for the rat boys. Off you go - splash Cormac's [furrows] and leave it a while.", kw='furrows'),
            search(Z, [714, 126], "Splash the furrows in Cormac's field", "a dye-pot in the furrows", CRATE,
                   "By the time you come back, the field is a mess of colour: blue prints, yellow prints, red prints - all of them heading not into the field but through it, north, towards the spring. And over the lot, the broad flat prints of something heavy that took no dye at all. It came from the east."),
            end_talk('cormac', 'Tell Cormac what you saw', "They're not raiding me. They're crossing me - all three, going for the spring.\n\nAnd something else coming from the east after them. Something with flat feet. I don't like the sound of that at all.", 'default'),
        ],
        {'default': {'text': "Take this, from Rhian and me. Proof that the daft idea worked.", 'choice': [h3, h4]}},
        topics={'marking': "She wants to dye them. The raiders. So we know which of them comes down the hill at night. I said daft."},
        requires='balm_hunt')

h5 = z.item("Ditch-Spade Bracer", 'bracer', 7, 'might', "Beaten from the blade of a curmudgeon's ditch-spade.")
h6 = z.item("Spring-Water Phial", 'neck', 7, 'mind', "Filled at the spring the morning it ran full again.")
z.quest('the_spring_runs_dry', 'The Spring Runs Dry', 7, 'cormac',
        "I walked up to the spring this morning. It's a trickle. Forty years it's run full, and now it's a trickle. No wonder they're killing each other for it.\n\nSprings don't stop. Somebody's stopped it. Will you [find out who]?",
        'find out who',
        "The hill spring north of Mag Mell has nearly run dry, and the three pest tribes are at war over what's left.",
        [
            reach(Z, [700, 115], 'Go to the spring in the hills', "The basin is half dry, the mud around it churned by a hundred small feet. And a new ditch, neatly dug, leading east from the rock.", r=20),
            search(Z, [732, 118], 'Search the new ditch', "a ditch-spade", CRATE,
                   "A curmudgeon-made spade, left in the ditch. Its handle is carved with a little round scowling face: the mark of Grogan's people.",
                   give='a curmudgeon ditch-spade'),
            reach(Z, [985, 150], 'Follow the ditch east', "The ditch runs east under the hill, straight to the curmudgeons' store - where a dam of packed mud holds the stolen water in a pond for their mill wheel. Flat-footed mudmen splash along its top.", r=25),
            boss(Z, [990, 152], 'Break the curmudgeons\' dam', "Clabber tumbles off his dam. One good kick and the mud gives way; the water rushes back down the ditch towards the spring.",
                 'Clabber the Ditch-Digger', 60159548, 8, "A curmudgeon in a mud-caked apron stands up on the dam. 'MY water! Dug it MYSELF!'",
                 objective='Defeat Clabber the Ditch-Digger', hp=1.8, adds=[(60164275, 'mudman', [6, 7])], every=30, count=1),
            choice('cormac', 'Return to Cormac', "The spring's running! I heard it from the house.\n\nAnd the pests are still up there, all three, and no less angry for it. They've had a taste of war now. I could [leave them be] - they'll settle, once there's water enough. Or the lads and I could [drive them off] the hill while they're tired.",
                   [('leave them be', "Leave them be. ...Aye. They were here before the turnips.", 'ending:peace'),
                    ('drive them off', "Then I'll tell the lads. Keep your head down - you'll hear it from the house.", 'ending:war')]),
        ],
        {'peace': {'text': "Take this. And thank you for the water. I never thought to say that to anyone.", 'choice': [h5, h6]},
         'war': wake({'text': "Take this. And stay clear of the spring for a while - or don't, if you like a fight.", 'choice': [h5, h6]}, 'lough_derg_hill_war')},
        requires='three_kinds_of_trouble')

h7 = z.item("Bigfist Gauntlet-Charm", 'gem', 8, 'might', "A spraggon's knuckle-guard, far too big for any spraggon.")
h8 = z.item("Hill King's Crown-Ring", 'ring', 8, 'charm', "Grubb's pebble crown, the best pebble kept.")
h9 = z.item("Truce-Keeper's Cloak", 'cloak', 8, 'ward', "Rhian dyed it three colours, so nobody on the hill could call it theirs.")
z.quest('grubbs_truce', "Grubb's Truce", 8, 'cormac',
        "There's a spraggon up there calls himself Grubb Bigfist. King of the hill, he says, and now the spring's running he won't let the others near it.\n\nThe rat boys and the lucradans would go home if he let them drink. Will you [deal with Grubb]?",
        'deal with Grubb',
        "Grubb Bigfist the spraggon holds the spring and won't share it, and the hill war goes on.",
        [
            reach(Z, [700, 118], 'Go to the spring', "Grubb's spraggons hold the spring. The rat boys and lucradans watch from the rocks, thirsty and furious.", r=25),
            boss(Z, [704, 110], 'Defeat Grubb Bigfist', "Grubb sits down in the spring with a splash and bursts into tears. The rat boys and lucradans creep down to drink, warily, and nobody bites anybody.",
                 'Grubb Bigfist', 60166491, 9, "'Grubb's water! Grubb's hill! Grubb's EVERYTHING!'",
                 objective='Defeat Grubb Bigfist', hp=2.0, adds=[(60166472, 'spraggon', [6, 7])], every=25, count=2),
            end_talk('cormac', 'Return to Cormac', "Quiet up there tonight. First quiet night since spring.\n\nThat ditch-spade's hanging over my door now. A reminder: when the little folk fight, look for who's stealing their water. Clabber said a man paid him for the mill. A man with a red ring.", 'default'),
        ],
        {'default': {'text': "Take this, with the thanks of every turnip I'll ever grow.", 'items': [h9], 'choice': [h7, h8]}},
        requires='the_spring_runs_dry')

# ======================================================================== The Alchemist's Garden (the fae, 8 to 13)
f1 = z.item("Lily-Dew Phial", 'neck', 8, 'mind', "Never empty, never quite full. Smells of white lilies.")
f2 = z.item("Thief's Petal Charm", 'gem', 8, 'charm', "A petal from a mere sprite. It curls away from your fingers.")
z.quest('dew_from_the_mere', 'Dew from the Mere', 8, 'orlaith',
        "Ailbhe gathers my glowcaps; that's the easy work. What I need now is dew from the mere in the west - the fae lake - gathered off the lily-pads before the sun's on them.\n\nIt's the best thing there is for a fever, and the good folk guard it like gold. Will you [gather the dew]?",
        'gather the dew',
        "Orlaith the herbwife needs dew from the fae mere, and the fae don't share.",
        [
            reach(Z, [256, 908], 'Go to the mere in the west', "Still water, white lilies, and a silence that feels like being watched. Out on the mere, tall pale shapes stand knee-deep, guarding something.", r=25),
            search(Z, [262, 906], 'Gather dew from the lily-pads', "dew on the lily-pads", RED_WOOD,
                   "You fill the phial drop by drop. The watching shapes turn your way, all at once.", give='a phial of mere-dew'),
            tk(kill(Z, [262, 910], 'Fend off the mere sprites', 'mere sprite', 30001, 9, 4,
                    text="The last sprite bursts into a shower of petals. Out on the water a woman's voice says, very clearly: 'Thief.'"), 'blue'),
            end_talk('orlaith', 'Bring the dew to Orlaith', "'Thief.' She said that? ...Ach.\n\nThey always want paying. That's the trouble with the good folk: they never give, they only lend, and the interest is murder.", 'default'),
        ],
        {'default': {'text': "Take this - and don't go back to the mere alone for a while.", 'choice': [f1, f2]}},
        requires='changeling')

f3 = z.item("Go-Between's Scale", 'gem', 10, 'faith', "Sabha shed it on purpose. You're nearly sure of that.")
f4 = z.item("Trout-Leather Bracer", 'bracer', 10, 'finesse', "Supple, silver and faintly fishy.")
z.quest('balance_of_nature', 'Balance of Nature', 10, 'orlaith',
        "There's a creature lives by the mere - Sabha, the fishers call it. Harmless. A go-between, my mother said.\n\nIf the Lady wants paying, Sabha will know the price. Take it a [fish] - it likes fish - and ask. Will you [speak to Sabha]?",
        'speak to Sabha',
        "The Lady of the Mere calls you a thief. Sabha, the go-between by the mere, will know her price.",
        [
            search(Z, [246, 908], 'Find a fish on the mere shore', "a fisher's trap", CRATE,
                   "One fat trout, still kicking. You leave a coin in the trap. It seems only fair, given the day you're having.", give='a fresh trout'),
            talk('sabha', 'Give Sabha the fish', "Fish. Good fish. Sabha says thank you.\n\nThe Lady is angry. Her dew was taken. Price is music. The Lady has not heard music since the [drum] of Tir na mBeo stopped playing at the water. Drum is stolen. Bring the drum, play the drum - Lady forgives.", kw='drum', take='a fresh trout'),
            end_talk('orlaith', 'Return to Orlaith', "Music. Of course it's music.\n\nTavie of Tir na mBeo used to drum by the mere every midsummer, and the fae came out of the lilies to listen. Her drum went missing in the spring. Go and see her - she's in Tir na mBeo, by the inn.", 'default'),
        ],
        {'default': {'text': "Take this, for your trouble with the fish.", 'choice': [f3, f4]}},
        topics={'fish': "Fresh, mind. From the shore, not the market. Sabha can tell."},
        requires='dew_from_the_mere')

f5 = z.item("Old Drumhead Charm", 'gem', 12, 'mind', "The split drumhead, cut round and bound in brass. It hums when it's struck.")
f6 = z.item("Midsummer Sash", 'belt', 12, 'charm', "Tavie wore it every midsummer for twenty years.")
f7 = z.item("Cured-Hide Bracer", 'bracer', 12, 'ward', "Curmudgeon-cured. Stinks for a month, lasts a hundred years.")
z.quest('beautiful_music', 'Beautiful Music', 12, 'tavie',
        "My drum! My beautiful drum. Sprites took it - little red angry things, [anger sprites], came in the window, took it and laughed.\n\nI've heard it since, out east of the fae woods, somebody beating it badly. Will you [find my drum]?",
        'find my drum',
        "Tavie's drum was stolen by anger sprites. The Lady of the Mere wants to hear it played again.",
        [
            gives(tk(kill(Z, [780, 905], 'Hunt down the anger sprites', 'anger sprite', 60159273, 11, 5,
                          text="One of them drops what it was beating on: a goatskin drum, split clean across."), 'green'), "Tavie's split drum"),
            talk('tavie', 'Bring the drum to Tavie', "Split. They've split it. ...It'll mend. It needs a new head.\n\nCurmudgeon-cured hide is the best there is, I hate to say. Their trappers cure it with something that stinks for a month and lasts a hundred years. Bring me a [hide].", kw='hide'),
            hunt([1538, 988], 'Take a cured hide from a curmudgeon trapper in the east valley', 'curmudgeon trapper', 2, give='a curmudgeon-cured hide'),
            talk('tavie', 'Bring the hide to Tavie', "There. Listen to that! ...Now, the Lady.\n\nI'll play at the mere, but I'll not go alone. The fae in the west aren't what they were. Meet me by the [water].", kw='water'),
            defend(Z, [258, 910], 'Keep Tavie safe while she plays', "The drumming rolls out over the water. One by one the sprites stop and sit down in the reeds to listen. Out on the mere, a tall pale woman stands up from the lilies.",
                   'Tavie', 60167226, 12, "Tavie sits on a stone and starts to play. The water shivers, and the sprites come in a rush.",
                   [(30001, 'mere sprite', [11, 12])], 'Keep Tavie safe', model=310, duration=90, every=20, count=2, froms=[[272, 914], [244, 918]],
                   thanks="Did you hear it? Did you hear how the water answered?"),
            L('lady', talk('lady', 'Speak with the Lady of the Mere', "Twenty summers without the drum.\n\nYou took my dew, and you brought me music. The debt is paid. Tell your herbwife the mere is not her garden. She may take what she is [given]. No more.", kw='given')),
            end_talk('tavie', 'Return to Tavie', "She smiled at me. The Lady of the Mere smiled at ME.\n\nI'll play every midsummer now till I'm dead. Take this - for the hide, and the walk, and the company.", 'default'),
        ],
        {'default': {'text': "Take this. Something to remember the music by.", 'items': [f5], 'choice': [f6, f7]}},
        topics={'anger sprites': "Born of a bad temper, my granny said. They gather wherever someone's been cruel - lately that's the east, by the Dergan camps."},
        requires='balance_of_nature')

f8 = z.item("Meadowsweet Mantle", 'cloak', 13, 'faith', "Embroidered with foxglove and meadowsweet, for the bees.")
f9 = z.item("Drowned-Lily Circlet Charm", 'gem', 13, 'mind', "A lily from the bottom of a silent mere. It never opens.")
f10 = z.item("Herbwife's Satchel-Belt", 'belt', 13, 'charm', "Orlaith's own. A pocket for everything, and one for dew.")
f11 = z.item("Mere-Guard Bracer", 'bracer', 13, 'might', "Pale as bone and cold as deep water.")
z.quest('the_ladys_bargain', "The Lady's Bargain", 13, 'orlaith',
        "'Only what she's given.' Hah.\n\nA fever went through Tir na mBeo last week, and do you know how much dew she's given me? None. Children are sick and she sits on her lilies.\n\nI need that dew. How you get it is up to you. Will you [get the dew]?",
        'get the dew',
        "A fever in Tir na mBeo, and only the mere's dew will cure it. The Lady of the Mere won't give it.",
        [
            choice('orlaith', 'Decide how to get the dew', "So. Do you [take it] - with friends at your back, past her guardians and her - or do you go and [ask the Lady], and see what she wants this time?",
                   [('take it', "Then take friends. She's older than this town, and she won't go quietly.", 'next:take'),
                    ('ask the Lady', "Ask, then. Mind she doesn't ask for your name.", 'next:ask')]),
            L('take', hunt([215, 862], 'Fight past the mere guardians', 'mere guardian', 3)),
            hunt([200, 862], 'Defeat the Lady of the Mere', 'Lady of the Mere', 1, give="the Lady's dew",
                 text="The Lady sinks into the mere without a sound, and the lilies close over her. The dew is yours. Nothing on the water moves."),
            end_talk('orlaith', 'Bring the dew to Orlaith', "Enough for every child in Tir na mBeo, and to spare.\n\n...It's very quiet out at the mere now, Ailbhe says. No singing at all. I suppose that's the price. I suppose I'll get used to it.", 'took', label='took'),
            L('ask', talk('lady', 'Ask the Lady of the Mere', "Sick children. ...I am not cruel. I am old, and I have been robbed.\n\nVery well. Dew for the sick, every season, for as long as the herbwife plants foxglove and meadowsweet on my shore, for the bees. A [bargain].", kw='bargain', give="the Lady's dew")),
            end_talk('orlaith', 'Bring the dew to Orlaith', "Foxglove and meadowsweet. For the bees.\n\nThat's all she wanted? A garden for the bees? Twenty years I've been stealing from her. ...Here. And send me your fevers, any time.", 'asked'),
        ],
        {'took': {'text': "Take this. It's yours, I suppose. All of it's yours.", 'tragic': True, 'items': [f9], 'choice': [f10, f11]},
         'asked': {'text': "Take this. The Lady left it on my doorstep. With a bee on it.", 'items': [f8], 'choice': [f10, f11]}},
        requires='beautiful_music', group=True)

# ======================================================================== The Stolen Harvest (the curmudgeons, 9 to 14)
c1 = z.item("Reeve's Tally-Stick Charm", 'gem', 9, 'mind', "Notched for every sack. The last notch is yours.")
c2 = z.item("Clay-Caked Bracer", 'bracer', 9, 'ward', "The clay won't come off. Cathbad says it's lucky.")
z.quest('short_measures', 'Short Measures', 9, 'cathbad',
        "Forty sacks of barley in that granary at harvest. Thirty-one now. No door forced, no lock broken.\n\nGuardian Fionn says curmudgeons. I say curmudgeons can't walk through walls. Will you [look into it]?",
        'look into it',
        "Barley is vanishing from Mag Mell's granary without a lock broken. Reeve Cathbad wants to know how.",
        [
            search(Z, [722, 226], 'Search the granary', "the granary floor", CRATE,
                   "Under the last row of sacks, a hole - not dug from inside, but from below. The earth around it is wet clay, and it smells of the marsh.",
                   give='a lump of wet clay'),
            reach(Z, [1060, 170], "Follow the tunnel's line east", "The clay trail ends at the curmudgeons' store. Harvesters are packing barley sacks into carts - Mag Mell's sacks, with the reeve's own mark on them.", r=30),
            hunt([1088, 162], 'Drive off the curmudgeon harvesters', 'curmudgeon harvester', 4),
            search(Z, [1096, 156], 'Search the carts', "a cart's tally-board", CRATE,
                   "A board of notches: sacks in, sacks out. The 'out' notches are marked with a little red hand.",
                   give="the curmudgeons' tally-board"),
            end_talk('cathbad', 'Bring the tally-board to Cathbad', "Tunnels. Mudmen dig through clay like it's water.\n\nAnd a red hand on the tally. Mandra's lad talked about a red hand. I'm starting to think someone's buying our harvest and our troubles both.", 'default'),
        ],
        {'default': {'text': "Take this. You've a reeve's eye for a short measure.", 'choice': [c1, c2]}})

c3 = z.item("Watchman's Studded Belt", 'belt', 10, 'might', "Studded with mudman chert. Kylirean is very proud of it.")
c4 = z.item("Cadger-Skin Bracer", 'bracer', 10, 'finesse', "Wolf-skin, the fur turned in. Warm on a night watch.")
c5 = z.item("Tharl's Trap-Chain Charm", 'gem', 10, 'charm', "A link from Tharl's trap-chain. It still snaps shut on its own sometimes.")
z.quest('the_watchs_new_armour', "The Watch's New Armour", 10, 'cathbad',
        "I'm putting a watch on the next cart, and the watch needs armour. Kylirean the armourer will stitch it if he has the [makings] - and he's fussy.\n\nBring him the makings, then ride with the cart. Will you [outfit the watch]?",
        'outfit the watch',
        "Reeve Cathbad's watch will guard the next grain cart, once Kylirean the armourer has the makings of their armour.",
        [
            hunt([420, 80], 'Take skins from lough wolves in the northern hills', 'lough wolf', 3, give='lough wolf skins'),
            hunt([1088, 162], "Break chert from mudmen by the curmudgeons' store", 'mudman', 2, give='mudman chert'),
            talk('cathbad', 'Bring the makings to Cathbad', "Kylirean grumbled and sewed all night, and the watch looks like a watch now.\n\nThe cart goes out by the old mill road. Meet it at the [mill].", kw='mill', take='lough wolf skins'),
            gives(defend(Z, [830, 755], 'Guard the grain cart on the mill road', "Tharl drops with a curse. In his belt pouch: a note in siabra script, and a wax seal - a red hand.",
                         "the reeve's grain cart", 60158958, 12, "Curmudgeons boil up out of the ditches on both sides of the road. 'GRAIN!'",
                         [(60159539, 'curmudgeon harvester', [9, 10])], 'Keep the grain cart safe', model=413, duration=90, every=20, count=2,
                         then_boss={'tpl': 60159548, 'name': 'Tharl the Trapper', 'lv': 12, 'hp': 2.0, 'announce': "A curmudgeon with a trap-chain over his shoulder steps out of the hedge. 'That's MY cart. Paid for.'", 'objective': 'Defeat Tharl the Trapper'},
                         thanks="The carter wipes his face. 'Never again. Never, ever again.'"), "Tharl's note"),
            end_talk('cathbad', 'Bring the note to Cathbad', "Siabra script. I can't read it. Nobody in Mag Mell can.\n\nThere's a siabra exile on the east shore who sells what he knows, they say in Tir na mBeo. A siabra. Gods help us.", 'default'),
        ],
        {'default': {'text': "Take this. Kylirean made one extra. For the watch's best.", 'choice': [c3, c4, c5]}},
        topics={'makings': "Lough wolf skins for the jerkins. Mudman chert for the studs - there's good flint in them, if you break them right."},
        requires='short_measures')

c6 = z.item("Exile's Ring", 'ring', 12, 'mind', "Siabra silver, turned so the stone faces in. Fereinn's people will know what it means.")
c7 = z.item("Courier's Satchel-Belt", 'belt', 12, 'finesse', "It carried plans for a war. Now it carries your lunch.")
c8 = z.item("Reeve's Seal Pendant", 'neck', 12, 'faith', "Cathbad's own seal, the barley sheaf. 'Show it at any granary in Hibernia.'")
z.quest('lesser_of_two_evils', 'The Lesser of Two Evils', 12, 'cathbad',
        "Fereinn, the exile is called. He lives alone on the east shore, hated by both sides, which I suppose recommends him.\n\nTake him Tharl's note. Will you [find Fereinn]?",
        'find Fereinn',
        "A siabra exile on the east shore can read Tharl's note - for a price.",
        [
            talk('fereinn', 'Find Fereinn on the east shore', "Tharl's hand. Dergan wax.\n\nI'll read it. Not for coin - for a courtesy. A curmudgeon courier carries the next note of this kind today, on the shore road. Bring me his [plans], and I'll read you both.", kw='plans'),
            gives(tk(kill(Z, [1222, 722], 'Stop the curmudgeon courier on the shore road', 'curmudgeon courier', 60159533, 13, 1,
                          text="The courier squeals and drops a satchel."), 'blue'), "the courier's plans"),
            choice('fereinn', 'Bring the plans to Fereinn', "Here is what they say. The curmudgeons sell your barley to the Dergan war camp. The camp feeds an army for the island. The one who pays is the warlord's quartermaster, and he signs with a red hand.\n\nNow. I could [keep the plans] - they're worth a great deal to the siabra who hate the warlord, my own people, and you'd have my friendship. Or you [take them] to your reeve, and I've done you a kindness for nothing. Choose.",
                   [('keep the plans', "Then you have a friend on the east shore. Few can say that. None of them are siabra.", 'next:siabra'),
                    ('take them', "As you like. Kindness is a habit I'm trying to keep.", 'next:reeve')]),
            L('siabra', end_talk('cathbad', 'Return to Cathbad', "You gave them to a siabra?\n\n...Well. He told you the truth, which is more than the curmudgeons ever did. The enemy of my enemy. I'll sleep badly.", 'siabra')),
            L('reeve', end_talk('cathbad', 'Return to Cathbad', "The warlord's quartermaster. Feeding an army on Mag Mell barley.\n\nI'll take this to Guardian Fionn tonight. You've done Mag Mell a great service.", 'reeve')),
        ],
        {'siabra': {'text': "Take this anyway. You found the truth, whoever has the paper.", 'items': [c6], 'choice': [c7, c8]},
         'reeve': {'text': "Take this. It opens doors at any granary in the realm.", 'items': [c8], 'choice': [c6, c7]}},
        requires='the_watchs_new_armour')

c9 = z.item("Cruiach-Hide Cloak", 'cloak', 14, 'ward', "Alastriona's stolen hide, won back from Hughar. She says you've earned it more than she has.")
c10 = z.item("Poacher's Ledger-Charm", 'gem', 14, 'mind', "The ledger's brass clasp. Every sack, every coin.")
c11 = z.item("Hughar's Snare-Ring", 'ring', 14, 'finesse', "A loop of poacher's wire, twisted into a ring.")
z.quest('hughars_ledger', "Hughar's Ledger", 14, 'cathbad',
        "The curmudgeons' go-between is Hughar the poacher - the one with the cruiach daemon hide that Alastriona swears was hers.\n\nHe keeps the ledger: every sack, every coin, every red hand. Bring me that ledger and Guardian Fionn can take it to the High King. Take friends. Hughar's no fool. Will you [take the ledger]?",
        'take the ledger',
        "Hughar the poacher keeps the curmudgeons' ledger of every sack sold across the lake.",
        [
            hunt([1538, 988], 'Fight through the poachers in the east valley', 'curmudgeon poacher', 3),
            hunt([1529, 975], 'Defeat Hughar', 'Hughar', 1, give="Hughar's ledger",
                 text="Hughar goes down hard. In his pack: a fat ledger, a stolen cruiach daemon hide, and a purse of red-hand silver."),
            end_talk('cathbad', 'Bring the ledger to Cathbad', "Every sack. Every coin. Three seasons of it, and all of it going across the lake to the Dergans.\n\nThey're not raiding us. They're provisioning. You don't provision for a raid. You provision for a war.", 'default'),
        ],
        {'default': {'text': "Take this. And this - Alastriona says the hide is yours now.", 'items': [c9], 'choice': [c10, c11]}},
        requires='lesser_of_two_evils', group=True)

# ======================================================================== Who Woke the Barrow? (the haunted, 10 to 16)
b1 = z.item("Seal-Stone Shard", 'gem', 10, 'faith', "A chip of the barrow's cracked seal-stone. Cold, always.")
b2 = z.item("Barrow-Bone Bracer", 'bracer', 10, 'might', "Bound from the arm-bones of a skeletal pawn. They've stopped moving. Mostly.")
z.quest('bones_on_the_road', 'Bones on the Road', 10, 'oran',
        "Skeletons on the north road at night. The roadwardens have lost two good men to them.\n\nNow - the dead in that barrow have lain quiet for three hundred years. The dead don't [wake] on their own. Will you [go to the barrow]?",
        'go to the barrow',
        "The dead of the old barrow by Mag Mell walk the roads at night. Seanchai Oran says the dead don't wake on their own.",
        [
            hunt([925, 292], 'Put down the skeletal pawns at the barrow', 'skeletal pawn', 3),
            search(Z, [930, 284], "Examine the barrow's seal-stone", "the barrow's seal-stone", CRATE,
                   "The great stone over the barrow door has been cracked - not by frost, not by age. Chisel marks, fresh ones. And pressed into the clay round the crack, the mark of a ring: a hand.",
                   give="a clay print of a ring"),
            end_talk('oran', 'Bring the ring-print to Oran', "Someone opened it. On purpose.\n\nThe Parthanan farm folk saw lights in the Grey Wood before the bones came. Rest tonight. Tomorrow we look there.", 'default'),
        ],
        {'default': {'text': "Take this. Old things for an old business.", 'choice': [b1, b2]}},
        topics={'wake': "Not by themselves. Someone has to call them, or let them out. That's the old law, and the old law's never been wrong yet."})

b3 = z.item("Red-Wax Candle Charm", 'gem', 12, 'mind', "A stub of red wax, stamped with a hand. It won't light. You've tried.")
b4 = z.item("Grey Wood Mantle", 'cloak', 12, 'ward', "Woven from the grey moss of the haunted wood. It keeps the mist off - and some of the cold.")
b5 = z.item("Hayrick Belt", 'belt', 12, 'finesse', "The farmhand who hid the saddlebag gave you this, and wouldn't look at you.")
z.quest('lights_in_the_grey_wood', 'Lights in the Grey Wood', 12, 'oran',
        "The Parthanan farmers say there were lights in the haunted wood - red ones - and singing that wasn't siabra singing.\n\nGo and [look]. By day, if you've any sense. The Grey Wood's bad enough by daylight.",
        'look',
        "Red lights and strange singing in the haunted Grey Wood came before the dead walked.",
        [
            reach(Z, [1380, 300], 'Go to the edge of the haunted wood', "Grey trees, grey moss, and a mist that never quite lifts. On the stumps: candle-ends of red wax, dozens of them, in a ring.", r=30),
            search(Z, [1394, 292], 'Search the ring of candles', "a ring of red candles", RED_WOOD,
                   "Red wax, stamped with the same hand. And a scrap of paper: 'Every night you sing, the dead walk further. Sing until they reach Mag Mell.'",
                   give='a scrap of the summoning'),
            tk(kill(Z, [1394, 292], 'Drive off the mist wraiths', 'mist wraith', 60160936, 13, 4,
                    text="The wraiths come apart like cobweb. Behind them, in the mud, boot prints going south - towards the farm."), 'blue'),
            reach(Z, [1300, 478], 'Follow the trail to the Parthanan farm road', "The farm road. Fresh hoofprints, and a farmhand who will not look you in the eye.", r=30),
            search(Z, [1312, 468], 'Search the farm', "a saddlebag in a hayrick", CRATE,
                   "A letter in a careful hand: 'To the Summoner. Keep the barrow open until the harvest is in. Your fee waits at the outpost. - R.' The red hand again.",
                   give='the letter to the Summoner'),
            end_talk('oran', 'Bring the letter to Oran', "'Keep the barrow open until the harvest is in.' The same words as the gang's orders, Mandra says. The same R.\n\nSomeone wants Mag Mell busy - busy with bandits, busy with bones, busy with curmudgeons - until the harvest is in. And the Summoner will sing tonight. Listen.", 'default'),
        ],
        {'default': wake({'text': "Take this. And stay indoors after dark, unless you mean to do something about it.", 'choice': [b3, b4, b5]}, 'lough_derg_summoners_muster')},
        requires='bones_on_the_road')

b6 = z.item("Dergal's Runed Mantle", 'cloak', 14, 'mind', "Stitched from Dergal's vest. The runes still smoulder faintly - binding, and unbinding.")
b7 = z.item("Pit-Chain Bracer", 'bracer', 14, 'might', "A link of the chain that held Riona. She wanted it gone. You wanted it kept.")
b8 = z.item("Riona's Vengeance Ring", 'ring', 14, 'finesse', "Riona wore it in the pit, hidden in her mouth. She says it kept her sane.")
z.quest('rionas_revenge', "Riona's Revenge", 14, 'riona',
        "You're the one who found the letter? Then hear me.\n\nThe siabra at the outpost on the east shore took me and kept me a month in a pit. Their chieftain, Dergal, wears a vest of runes - and every night a man in a grey hood came, and Dergal paid him in red-hand silver. The Summoner.\n\nI want Dergal dead, and I want that vest. Will you [take my revenge]?",
        'take my revenge',
        "Riona was held by the siabra at the Dergan outpost, where Chieftain Dergal paid the Summoner.",
        [
            hunt([1462, 750], 'Cut through the siabra at the Dergan outpost', 'siabra', 3),
            gives(boss(Z, [1470, 742], 'Defeat Chieftain Dergal', "Dergal falls. His runed vest smoulders; the runes match the marks on the barrow stone - binding runes, and unbinding.",
                       'Chieftain Dergal', 30000, 16, "A siabra in a vest stitched with burning runes: 'The pit girl sent you? I should have kept her longer.'",
                       objective='Defeat Chieftain Dergal', hp=2.2, adds=[(60161282, 'ghastly siabra', [13, 14])], every=30, count=1), "Dergal's runed vest"),
            end_talk('riona', 'Bring the vest to Riona', "Dead. Good.\n\nThose are unbinding runes - the same that cracked your barrow. Dergal taught the Summoner, and paid him. And Dergal was paid by the island. ...Here. Wear it, if you can stand the smell.", 'default'),
        ],
        {'default': {'text': "Take it. It was always meant for someone who'd use it better than he did.", 'items': [b6], 'choice': [b7, b8]}},
        requires='lights_in_the_grey_wood')

b9 = z.item("Summoner's Signet", 'ring', 16, 'mind', "A red hand on lake-blue enamel: the seal of Clan Derg. The hand has been chiselled off.")
b10 = z.item("Barrow-Song Pendant", 'neck', 16, 'faith', "The Summoner's last note, caught in a bead of grey glass.")
b11 = z.item("Gravewarden's Girdle", 'belt', 16, 'ward', "The barrow's old guardians wore these. One of them gave it back.")
z.quest('the_summoner', 'The Summoner', 16, 'oran',
        "We know what he is now, and who pays him. The Summoner works at the barrow by night, singing the dead up.\n\nRiona says he'll run when he hears his paymaster's dead - unless someone stops him first. Bring friends, go to the barrow, and [end it].",
        'end it',
        "The Summoner sings the dead out of the old barrow by Mag Mell, in the pay of the island.",
        [
            reach(Z, [925, 300], 'Go to the old barrow', "The barrow door stands open. Inside, a man in a grey hood, singing, and the dead climbing up round him.", r=30),
            gives(boss(Z, [925, 292], 'Defeat the Summoner', "The Summoner falls. The song breaks off mid-note, and every skeleton in the barrow lies down at once, like tired men. On his hand, a heavy signet: a red hand on lake-blue enamel.",
                       'the Summoner', 60166617, 18, "The singing stops. 'The bones are mine. The road is mine. Mag Mell will be the warlord's.' The dead turn towards you.",
                       objective='Defeat the Summoner', hp=2.5, adds=[(60166177, 'risen pawn', [14, 15]), (60166174, 'risen minion', [15, 16])], every=25, count=2), "the Summoner's signet"),
            end_talk('oran', 'Bring the signet to Oran', "A red hand on lake blue.\n\nThat's the seal of Clan Derg, the old warlords of the lake. I thought them a story. A warlord, with coin enough to buy bandits and curmudgeons and the dead? ...Take this to the roane. The lake's going red.", 'default'),
        ],
        {'default': {'text': "Take this. The barrow's quiet. That's your doing.", 'items': [b9], 'choice': [b10, b11]}},
        requires='rionas_revenge', group=True)

# ======================================================================== The Red Lake (the Dergans and siabra, 15 to 19)
r1 = z.item("War-Stone Pendant", 'neck', 15, 'might', "An uncut stone from the lake bed, the warlord's name scratched out.")
r2 = z.item("Lorewoman's Ogham Bracer", 'bracer', 15, 'mind', "Cara carved it with the old names of the lake, before it was red.")
z.quest('what_the_roane_saw', 'What the Roane Saw', 15, 'ronan',
        "Muirne says you're a friend of the roane. Then hear what the roane see from the water.\n\nBoats cross to the island every night. Barley going over, men coming back. The Dergans are gathering under a warlord, and they hunt us because we see too much. Will you [learn what they are]? The lorewoman in Tir na mBeo knows the old stories.",
        'learn what they are',
        "The roane see boats crossing to Dergan Island every night. Cara the lorewoman knows the old stories of the Dergans.",
        [
            talk('cara', 'Ask Cara the Lorewoman about the Dergans', "Dergans. Siabra, of the unseelie court, that came through the Veil when the elves and lurikeens did, and never went home. Here they took the lake's name: Clan Derg, the red lake.\n\nTheir warlords cut their oaths on [war-stones] - uncut stones from the lake bed, carried by their furies. Bring me one and I'll read it for you.", kw='war-stones'),
            hunt([1362, 1262], 'Take a war-stone from a dergan fury', 'dergan fury', 2, give='an uncut war-stone'),
            talk('cara', 'Bring the war-stone to Cara', "An oath-stone, cut with a warlord's name: Ruadhan. Ruadhan of the Red Hand.\n\n...R. The letters signed 'R.' He's on the island, and he's sworn to take the lake shore 'when the harvest is in'. Tell the [roane].", kw='roane'),
            end_talk('ronan', 'Return to Ronan of the Roane', "Ruadhan.\n\nThe roane will watch the war camp for you, from the water. Go when you're ready. And take this - from Muirne.", 'default'),
        ],
        {'default': {'text': "From Muirne, with the roane's thanks.", 'choice': [r1, r2]}},
        requires='roane')

r3 = z.item("Muster-Roll Satchel Belt", 'belt', 16, 'finesse', "It held the war camp's muster roll. You've kept the satchel.")
r4 = z.item("Palisade-Stake Bracer", 'bracer', 16, 'might', "Cut from the war camp's palisade, the night you slipped through it.")
r5 = z.item("Roane-Watcher's Cloak", 'cloak', 16, 'ward', "Grey as a seal's back. The roane gave it to those who watch for them.")
z.quest('the_war_camp', 'Scouting the War Camp', 16, 'ronan',
        "The war camp on the south shore is where Ruadhan's bands muster before they cross.\n\nGet close. Count them. Find out when they march. Will you [scout the camp]?",
        'scout the camp',
        "Ruadhan's war bands muster at the Dergan war camp on the south shore.",
        [
            reach(Z, [1262, 1118], 'Reach the high ground north of the war camp', "Below you: tents for a hundred, cookfires, siabra archers on the palisade - and Mag Mell's barley sacks piled under oilcloth.", r=20),
            reach(Z, [1338, 1188], "Circle round to the camp's east side", "The training ground beyond is busy: recruits drilling in lines, sergeants shouting in the siabra tongue. More than a war band. An army.", r=20),
            hunt([1295, 1160], 'Thin the furies guarding the war tent', 'dergan fury', 3),
            search(Z, [1302, 1152], 'Search the war tent', "the war tent's muster roll", CRATE,
                   "A muster roll: bands, numbers and a date, written in common so the curmudgeons can read it. 'Muster at the outpost. Cross when the harvest is in.' The harvest is in next week.",
                   give='the muster roll'),
            end_talk('ronan', 'Return to Ronan', "Next week.\n\nTake it to the captain in Mag Mell. And thank you. The roane don't forget. ...Listen - the war bands are already moving on the east edge. They know someone was in the camp.", 'default'),
        ],
        {'default': wake({'text': "Take this. You've a roane's eyes now.", 'choice': [r3, r4, r5]}, 'lough_derg_dergan_war_bands')},
        requires='what_the_roane_saw')

r6 = z.item("Quartermaster's Sash", 'belt', 18, 'charm', "Every pocket held a red-hand coin. Lir had them melted for the widows' fund.")
r7 = z.item("Outpost-Fire Ring", 'ring', 18, 'mind', "Snatched out of the fire with the orders. It's still warm.")
r8 = z.item("Mag Mell Guard Bracer", 'bracer', 18, 'might', "Captain Lir's own issue. 'You've earned the green.'")
z.quest('orders_from_the_outpost', 'Orders from the Outpost', 18, 'lir',
        "So the roane were right, and the reeve, and old Oran, and a boy from a bandit camp. Ruadhan's been buying our troubles for a year.\n\nBefore I can move the guard, I need his orders in his own hand. The outpost on the east shore carries them to the war bands. Will you [take the orders]?",
        'take the orders',
        "Captain Lir needs Ruadhan's own orders before he can move the guard. The Dergan outpost carries them.",
        [
            hunt([1462, 750], 'Silence the whistlers who watch the outpost road', 'whistler', 2),
            gives(boss(Z, [1462, 756], 'Defeat the Dergan quartermaster', "The quartermaster falls before the fire catches. In his satchel: Ruadhan's orders, sealed in red.",
                       'Quartermaster Fiachna', 60159917, 19, "A Dergan in a quartermaster's sash snatches up a satchel. 'Burn the orders! BURN them!'",
                       objective='Defeat Quartermaster Fiachna', hp=2.2, adds=[(60159913, 'dergan fury', [16, 17])], every=30, count=1), "Ruadhan's orders"),
            end_talk('lir', 'Bring the orders to Captain Lir', "'Hold the island against all comers. When the harvest is in, cross and take Mag Mell's granary, then the town.' Signed: Ruadhan, warlord of the Red Lake.\n\nWell. Now I can move.", 'default'),
        ],
        {'default': {'text': "Take this, and the realm's thanks. You'll have more than that before we're done.", 'choice': [r6, r7, r8]}},
        requires='the_war_camp')

r9 = z.item("Roane-Song Pearl", 'neck', 19, 'faith', "The last captive sang into it as she went into the water. You can still hear it, very faintly.")
r10 = z.item("Pen-Key Ring", 'ring', 19, 'finesse', "The key to the roane pens, bent into a ring. Nobody will use it again.")
r11 = z.item("Slavemaster's Bane", 'gem', 19, 'might', "Cuan's whip-handle, broken in two and bound with sealskin.")
r12 = z.item("Red Lake Mantle", 'cloak', 19, 'ward', "Lake-blue, with a red hand torn from it. Worn by those who broke the warlord's hold.")
z.quest('the_roane_captives', 'The Roane Captives', 19, 'ronan',
        "One thing more, before your captain sails.\n\nRuadhan keeps roane in pens on the island's south shore. Our skins are his treasury. If the island is stormed, the guards will kill them first. Will you [free the captives] before then? Take friends. The island is his.",
        'free the captives',
        "Ruadhan keeps roane captive in pens on Dergan Island's south shore.",
        [
            reach(Z, [1068, 1492], "Reach the pens on the island's south shore", "Pens of driftwood and net, and grey shapes inside them that turn their heads to watch you. A sergeant shouts.", r=25),
            defend(Z, [1062, 1486], 'Free the roane and hold the pens', "The pens are open. Roane slip into the water one by one, grey heads in the waves, and the last of them turns and sings something you'll never forget.",
                   'roane captive', 60167226, 16, "You cut the first net. Every Dergan on the south shore comes running.",
                   [(60159913, 'dergan sergeant', [18, 19])], 'Keep the roane captives safe', model=365, duration=120, every=25, count=2,
                   then_boss={'tpl': 60159917, 'name': 'Slavemaster Cuan', 'lv': 21, 'hp': 2.4, 'announce': "A Dergan with a sealskin whip wades out of the shallows. 'My stock. MY treasury.'", 'objective': 'Defeat Slavemaster Cuan'},
                   thanks="The roane captive presses your hand, once, and is gone into the water."),
            end_talk('ronan', 'Return to Ronan', "Every one of them. Every one.\n\nRuadhan will know by morning. Tell your captain to be quick - and when the island is stormed, the roane will carry anyone who asks across the water. That's a promise.", 'default'),
        ],
        {'default': {'text': "Take this. The roane have long memories, and you're in all of them now.", 'items': [r12], 'choice': [r9, r10, r11]}},
        requires='orders_from_the_outpost', group=True)
