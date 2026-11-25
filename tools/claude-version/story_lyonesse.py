"""Lyonesse's story quests (claude 2026-11-24, "Albion - the plan", round 3) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_lyonesse

Tristan's lost country, drowned by the sea - and the sea is rising again. A white storm out of the south, the old women say:
the white dragon's weather, to drown Cornwall's coast and cut Albion's south off from the north. Storm-callers work the rock
in the north, the cailleach of the old sea-wind keeps her ring in the mire, and the drowned Danaoin live their last day over and
over. The northern undertone: the priests of Arawn at the ruined cathedral have been bought by "a queen in a black crown". At
the end King Meliodas, Tristan's drowned father, tells who drowned Lyonesse the first time.

The zone's two older quests are kept as they were (last_evening, arawn_sacrament).

Arcs (recommended levels): The Remnant (40-44), Tristan's Lay (42-46), The White Storm (44-47), The Drowned Knights (43-50),
The Cailleach (50).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk
from albion_story import Story, CRATE, BEDROLL, LANTERN, M, F, OLD

S = Story(10, 'Lyonesse', 'alb_lyonesse', 'story010_lyonesse', {'last_evening', 'arawn_sacrament'},
          {'wenna_trevose', 'morvah', 'sir_kendric', 'tobin'},
          {"Morvah's Shawl", 'Drowned-Net Belt', 'Salt-Pearl Ring', 'Evening Star Pendant', 'Reliquary Shard', "Kendric's Watch-Cloak",
           'Drowned Knight Signet', "Tobin's Bracer", "Hierophant's Girdle"})
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
KNIGHT, FOOTMAN = 50015, 12016

person('ly_meliot', 'Remnant-Captain Meliot', (1356, 1126), 'm', 48, model=28, guild='the Lyonesse Remnant',
       idle="We're what's left of Lyonesse that can still hold a sword. It isn't much. It's enough.")
person('ly_gwennol', 'Harper Gwennol', (1332, 1142), 'f', 46, guild='the Harpers of Tristan',
       idle="Tristan was the best harper who ever lived. We keep his songs. Somebody must.")

# ======================================================================== The Remnant (40-44)
r1 = z.item("Peallaidh-Scale Bracer", 'bracer', 40, 'ward', "Sea-green scales, sharp at the edges.")
r2 = z.item("Remnant Picket Ring", 'ring', 40, 'might', "Salt-stained iron. The Remnant's own.")
z.quest('ly_peallaidh', 'The North Shore', 40, 'ly_meliot',
        "The peallaidh - the shaggy sea-things - come further up the north shore with every tide. The sea's coming with them.\n\nWill you [push them back]?",
        'push them back',
        "Peallaidh come further up Lyonesse's north shore with every tide.",
        [
            hunt((1268, 628), "Push back the peallaidh " + where((1268, 628), 'ly_meliot'), 'peallaidh', 6),
            end_talk('ly_meliot', "Tell Remnant-Captain Meliot", "Back - for a tide or two. The sea isn't rising by itself, you know. Nothing here does anything by itself.", 'default'),
        ],
        {'default': {'text': "From the Lyonesse Remnant.", 'choice': [r1, r2]}})

r3 = z.item("Bone-Snapper Jaw Charm", 'gem', 43, 'might', "A jaw-bone, wired shut. Still twitches.")
r4 = z.item("Drowned-Field Belt", 'belt', 43, 'ward', "Mud-black leather.")
z.quest('ly_bone_snappers', 'Bone Snappers', 43, 'ly_meliot',
        "Bone snappers in the drowned fields to the west - big as boats, and they eat anything that floats or walks. My scouts won't cross.\n\nWill you [clear the fields]?",
        'clear the fields',
        "Bone snappers hunt the drowned fields of western Lyonesse.",
        [
            hunt((633, 1055), "Kill the bone snappers " + where((633, 1055), 'ly_meliot'), 'bone snapper', 5),
            end_talk('ly_meliot', "Tell Remnant-Captain Meliot", "My scouts will cross now. Some of them, anyway.", 'default'),
        ],
        {'default': {'text': "From the Lyonesse Remnant.", 'choice': [r3, r4]}})

r5 = z.item("Moorlich-Bog Ring", 'ring', 44, 'mind', "Black bog-iron, set with a drowned man's tooth.")
r6 = z.item("Mire-Walker's Mantle", 'cloak', 44, 'ward', "Oiled and black. Mire doesn't stick to it.")
z.quest('ly_moorlich', 'The Moorlich Mire', 44, 'sir_kendric',
        "Moorlich in the mire - drowned things that rose and stayed risen. The priests of Arawn call them up, I think, to keep the mire between us and their cathedral.\n\nWill you [cross the mire]?",
        'cross the mire',
        "Moorlich hold the mire between the Remnant's camp and the ruined cathedral.",
        [
            hunt((906, 728), "Put down the moorlich " + where((906, 728), 'sir_kendric'), 'moorlich', 5),
            end_talk('sir_kendric', "Tell Sir Kendric", "Crossable. Barely. The cathedral's on the far side - you know what waits there.", 'default'),
        ],
        {'default': {'text': "From Sir Kendric.", 'choice': [r5, r6]}})

# ======================================================================== Tristan's Lay (42-46)
t1 = z.item("Tristan's Harp-Peg", 'gem', 42, 'charm', "A harp-peg of black yew, worn smooth by a master's hand.")
t2 = z.item("Goblin-Hoard Ring", 'ring', 42, 'finesse', "From the pygmy goblins' hoard. They had good taste.")
t3 = z.item("Harper's Travelling Cloak", 'cloak', 42, 'charm', "Blue and gold, Lyonesse's colours.")
z.quest('ly_tristans_harp', "Tristan's Harp", 42, 'ly_gwennol',
        "The pygmy goblins of the south have a hoard, and in it - they boast of it - a harp of black yew. If it's Tristan's, it belongs to the Harpers, and to Lyonesse.\n\nWill you [find the harp]?",
        'find the harp',
        "The pygmy goblins of southern Lyonesse boast of a black yew harp in their hoard.",
        [
            hunt((1056, 1240), "Fight through the pygmy goblin tanglers " + where((1056, 1240), 'ly_gwennol'), 'pygmy goblin tangler', 5),
            search(Z, P(1100, 1300), "Search the goblins' hoard", "a heap of shiny drowned things", CRATE,
                   "Under a heap of tarnished cups: a harp of black yew, the strings long gone. Carved on the pillar: a boar, and 'T'.",
                   give="Tristan's harp"),
            choice('ly_gwennol', "Bring the harp to Harper Gwennol", "It's his. It's Tristan's. I can hardly hold it.\n\nI can [restring it], here in the camp, and play his songs for the Remnant - or you can [carry it] to Tintagel, where King Mark's people would weep to see it.",
                   [('restring it', "Then the Remnant will hear Tristan's harp tonight. You'll stay and listen?", 'ending:harp'),
                    ('carry it', "Then carry it gently. Mark wronged him, but Mark's people loved him.", 'ending:mark')]),
        ],
        {'harp': {'text': "From the Harpers of Tristan.", 'items': [t1], 'choice': [t2, t3]},
         'mark': {'text': "From the Harpers of Tristan.", 'items': [t3], 'choice': [t1, t2]}})

t4 = z.item("Black-Sail Ring", 'ring', 45, 'faith', "Black and white enamel, half and half.")
t5 = z.item("Isolde's Pearl", 'gem', 45, 'charm', "A sea-pearl, found in the wreck.")
t6 = z.item("Wreck-Diver's Belt", 'belt', 45, 'finesse', "Weighted, so you sink when you want to.")
z.quest('ly_black_sail', 'The Black Sail', 45, 'ly_gwennol',
        "You know the end of Tristan's lay? Dying, he sent for Isolde. White sails if she was coming, black if not. She came - and his wife told him the sails were black, and he died.\n\nThe ship is in the old harbour in the north-west, the sailors say. Drowned with the rest. Will you [find the ship]?",
        'find the ship',
        "Isolde's ship, the one with the sail that was white, lies drowned in Lyonesse's old harbour.",
        [
            hunt((420, 240), "Get past the drowned sailors in the old harbour " + where((420, 240), 'ly_gwennol'), 'Danaoin sailor', 3),
            search(Z, P(430, 230), "Search the wreck in the harbour", "a wreck with a rotted sail", CRATE,
                   "The sail, what's left of it, is white. Someone painted it black, long ago - the black flakes off under your hand. And there's a pearl caught in the rigging."),
            end_talk('ly_gwennol', "Tell Harper Gwennol", "White. It was always white. She came for him.\n\nI'll put that in the lay. It should have been in it all along.", 'default'),
        ],
        {'default': {'text': "From the Harpers of Tristan.", 'choice': [t4, t5, t6]}},
        requires='ly_tristans_harp')

t7 = z.item("Hamadryad Leaf-Crown", 'gem', 41, 'faith', "A crown of green leaves that never wither.")
t8 = z.item("Heartwood Bracer", 'bracer', 41, 'ward', "Dark heartwood, carved with a tree.")
z.quest('ly_hamadryads', 'The Weeping Wood', 41, 'ly_gwennol',
        "The hamadryads of the east wood used to sing with the Harpers. Now salt-water creeps into their roots and they've gone mad with it.\n\nWill you [quiet the wood]? It's a mercy.",
        'quiet the wood',
        "Salt-water rot drives the hamadryads of eastern Lyonesse mad.",
        [
            hunt((1454, 849), "Quiet the hamadryads " + where((1454, 849), 'ly_gwennol'), 'hamadryad', 5),
            end_talk('ly_gwennol', "Tell Harper Gwennol", "Quiet. I'll sing for them tonight.", 'default'),
        ],
        {'default': {'text': "From the Harpers of Tristan.", 'choice': [t7, t8]}})

t9 = z.item("Gabriel-Hound Collar", 'neck', 45, 'might', "Black iron, with a ring for a chain no one ever held.")
t10 = z.item("Hound-Ward Charm", 'gem', 45, 'faith', "A twist of rowan and iron, against the hounds of the sky.")
z.quest('ly_gabriel_hounds', 'The Gabriel Hounds', 45, 'ly_gwennol',
        "The Gabriel hounds - hounds of the sky, the old songs call them, Annwn's hounds - hunt on the hill in the west. They never came to Lyonesse before. Someone sent them.\n\nWill you [hunt the hounds]? Bring friends.",
        'hunt the hounds',
        "The Gabriel hounds, Annwn's hounds of the sky, hunt on a hill in western Lyonesse.",
        [
            hunt((531, 758), "Hunt the Gabriel hounds " + where((531, 758), 'ly_gwennol'), 'gabriel hound', 3),
            end_talk('ly_gwennol', "Tell Harper Gwennol", "Annwn's hounds, this far south. The priests of Arawn opened a way for them, I'd wager, at someone's asking.", 'default'),
        ],
        {'default': {'text': "From the Harpers of Tristan.", 'choice': [t9, t10]}}, group=True)

t11 = z.item("Witherwoode Splinter", 'gem', 46, 'mind', "Grey wood. It's colder than ice.")
t12 = z.item("Wither-Bark Mantle", 'cloak', 46, 'ward', "Bark-grey, stiff, warm on the inside.")
z.quest('ly_witherwoode', 'The Witherwoode', 46, 'ly_gwennol',
        "In the middle mire the witherwoode stand - dead trees, walking. They grow where the cailleach breathes. They're spreading toward the camp.\n\nWill you [fell the witherwoode]?",
        'fell the witherwoode',
        "The witherwoode, dead walking trees, spread from the cailleach's mire toward the Remnant's camp.",
        [
            hunt((778, 638), "Fell the witherwoode " + where((778, 638), 'ly_gwennol'), 'witherwoode', 3),
            end_talk('ly_gwennol', "Tell Harper Gwennol", "They grow where she breathes. One day someone will have to stop her breathing.", 'default'),
        ],
        {'default': {'text': "From the Harpers of Tristan.", 'choice': [t11, t12]}}, group=True)

# ======================================================================== The White Storm (44-47)
s1 = z.item("Storm-Glass Ring", 'ring', 44, 'mind', "A ring of fused sand from a lightning-strike.")
s2 = z.item("Drowned-Farm Shawl", 'cloak', 44, 'charm', "Homespun, sea-stained. A drowned farmer's wife made it.")
z.quest('ly_last_day', 'The Day the Sea Came', 41, 'wenna_trevose',
        "The drowned folk in the east farms live their last day over and over - you've seen Morvah. But they remember how it ended. If you can get one to stand still long enough...\n\nWill you [ask the drowned]? Gently, if you can.",
        'ask the drowned',
        "The drowned farmers of eastern Lyonesse relive their last day. Wenna Trevose wants to know how it ended.",
        [
            hunt((1151, 784), "Calm the drowned shepherds " + where((1151, 784), 'wenna_trevose'), 'shepherd', 4),
            search(Z, P(1160, 790), "Search a drowned farmhouse", "a farmhouse with the table still laid", CRATE,
                   "A journal, the last page: 'A white storm out of the south, out of a clear sky. No ordinary sea. My husband says there was a beast in the clouds, white as bone.'"),
            end_talk('wenna_trevose', "Tell Wenna Trevose", "A beast in the clouds, white as bone. The storm that drowned Lyonesse wasn't weather.\n\nAnd it's coming back.", 'default'),
        ],
        {'default': {'text': "From Wenna Trevose.", 'choice': [s1, s2]}},
        requires='last_evening')

s3 = z.item("Storm-Caller's Lightning-Rod", 'gem', 44, 'mind', "A twisted iron rod. Your hair stands up when you hold it.")
s4 = z.item("Weatherproof Mantle", 'cloak', 44, 'ward', "Tarred wool. Nothing gets through.")
s5 = z.item("Claw-Mark Bracer", 'bracer', 44, 'might', "Scored with a dragon's claw, deliberately.")
z.quest('ly_storm_callers', 'The Storm-Callers', 44, 'ly_meliot',
        "Robed figures on the rock in the north - storm-callers, the farmers call them - sing up the white storm a little every night. The sea rises a finger's width each time.\n\nWill you [break the singing]?",
        'break the singing',
        "Storm-callers on the north rock sing up a white storm a little every night.",
        [
            hunt((1179, 480), "Kill the storm-callers on the rock " + where((1179, 480), 'ly_meliot'), 'storm-caller', 3),
            search(Z, P(1170, 470), "Search the storm rock", "a rock scored with claw-marks", CRATE,
                   "Claw-marks, deep, in a ring round the rock - a dragon's. And a cairn of pale stones: Dartmoor granite."),
            end_talk('ly_meliot', "Tell Remnant-Captain Meliot", "Dartmoor granite and a dragon's claw. Golestandt drowned Lyonesse. And he means to do it again, to Cornwall.", 'default'),
        ],
        {'default': {'text': "From the Lyonesse Remnant.", 'choice': [s3, s4, s5]}},
        requires='ly_peallaidh')

s6 = z.item("Stormheart Charm", 'gem', 47, 'mind', "The heart of the storm-engine, cracked and quiet.")
s7 = z.item("Calm-Sea Ring", 'ring', 47, 'faith', "Blue glass. The sea is calm in it.")
s8 = z.item("Remnant Captain's Mantle", 'cloak', 47, 'ward', "Lyonesse blue, salt-white at the hem.")
z.quest('ly_storm_controller', 'The Unnatural Storm', 47, 'ly_meliot',
        "The storm-callers were only the voices. The storm itself has a heart - a thing on the rock that the white dragon left behind. Kill it, and the sea stops rising.\n\nWill you [still the storm]? Bring everyone.",
        'still the storm',
        "The white dragon's storm has a heart on the north rock of Lyonesse.",
        [
            hunt((1179, 467), "Destroy the Unnatural Storm Controller " + where((1179, 467), 'ly_meliot'), 'Unnatural Storm Controller', 1,
                 text="The storm-thing shatters. For the first time in a year, the wind drops, and the sea lies flat."),
            end_talk('ly_meliot', "Tell Remnant-Captain Meliot", "The sea's lying flat. I'd forgotten it could.\n\nCornwall's coast is safe - from this, at least. The dragon will try something else.", 'default'),
        ],
        {'default': {'text': "From the Lyonesse Remnant.", 'choice': [s6, s7, s8]}},
        requires='ly_storm_callers', group=True)

# ======================================================================== The Drowned Knights (43-50)
k1 = z.item("Pikeman's Gorget", 'neck', 43, 'might', "Drowned steel, scoured clean.")
k2 = z.item("Drowned Pike-Ring", 'ring', 43, 'finesse', "From a pike's butt-cap.")
z.quest('ly_pike_line', 'The Pike Line', 43, 'sir_kendric',
        "Drowned pikemen hold a line in the south, as they did the day the sea came - still waiting for an enemy who never arrived.\n\nWill you [break the line]?",
        'break the line',
        "Drowned pikemen hold a line in southern Lyonesse, waiting for an enemy.",
        [
            hunt((791, 1096), "Break the drowned pikemen " + where((791, 1096), 'sir_kendric'), 'pikeman', 4),
            end_talk('sir_kendric', "Tell Sir Kendric", "Broken. They'll stand again, I expect. The knights behind them won't let them rest.", 'default'),
        ],
        {'default': {'text': "From Sir Kendric.", 'choice': [k1, k2]}})

k3 = z.item("Drowned Knight's Spur", 'gem', 47, 'might', "Silver, green with age.")
k4 = z.item("Lyonesse Shield-Strap", 'belt', 47, 'ward', "From a knight's shield. Blue and gold, faded.")
k5 = z.item("Knight's Vigil Ring", 'ring', 47, 'faith', "A plain ring, engraved: 'Until the sea goes back.'")
z.quest('ly_drowned_knights', 'The Drowned Knights', 47, 'sir_kendric',
        "The knights of Lyonesse stand guard in the south, round the old castle-mound - the king's guard, drowned with their king. They answer to no one now.\n\nWill you [face the guard]? Bring everyone.",
        'face the guard',
        "The drowned knights of Lyonesse's king guard the old castle-mound in the south.",
        [
            hunt((1219, 1270), "Fight through the drowned footmen " + where((1219, 1270), 'sir_kendric'), 'footman', 3),
            hunt((1225, 1275), "Defeat the drowned knights", 'knight', 3),
            end_talk('sir_kendric', "Tell Sir Kendric", "The king's guard is broken. Then the king himself will come out. He always does, the drowned say, when his guard falls.", 'default'),
        ],
        {'default': {'text': "From Sir Kendric.", 'choice': [k3, k4, k5]}},
        requires='ly_pike_line', group=True)

k6 = z.item("Meliodas's Crown-Ring", 'ring', 50, 'might', "A drowned king's crown, cut into a ring. Seawater drips from it.")
k7 = z.item("Lyonesse Royal Mantle", 'cloak', 50, 'ward', "Blue, with Lyonesse's sun in gold.")
k8 = z.item("Father's Sorrow Torc", 'neck', 50, 'faith', "Meliodas wore it for Tristan.")
k9 = z.item("Tide-Lord's Charm", 'gem', 50, 'mind', "A shell that hums with the tide.")
z.quest('ly_meliodas', 'The Drowned King', 50, 'sir_kendric',
        "King Meliodas of Lyonesse - Tristan's father - drowned with his kingdom. With his guard broken he'll walk out of the castle-mound. He may be the only one who remembers what drowned us.\n\nWill you [face the king]? Make him listen.",
        'face the king',
        "King Meliodas of Lyonesse, Tristan's drowned father, walks out of the castle-mound.",
        [
            reach(Z, P(1210, 1260), "Go to the old castle-mound " + where((1210, 1260), 'sir_kendric'), "Water runs uphill toward the mound. A tall figure in a sea-green crown steps out of it.", r=30),
            boss(Z, P(1220, 1275), "Make King Meliodas listen", "Meliodas kneels in the water. 'A white beast in the clouds,' he says. 'It asked for my harbour and I said no. And now a queen in a black crown buys my priests. Tell my son's friends: the dragon is in Dartmoor, and the queen is at the lake.'",
                 'King Meliodas of Lyonesse', KNIGHT, 51, "King Meliodas, crowned in sea-wrack: 'Who walks in my kingdom? Kneel, or drown.'",
                 adds=[(FOOTMAN, 'drowned guardsman', [48, 49])], every=30, count=2),
            choice('sir_kendric', "Speak with Sir Kendric", "Dartmoor and the lake. The dragon and the queen. Both threads end the same way: at the heart of each of them.\n\nShall we [bury the king] - here, in the mound, with honour? Or [tell the Harpers] all he said, so it goes into the lay?",
                   [('bury the king', "Then he rests. Lyonesse's last king, under Lyonesse's last hill.", 'ending:buried'),
                    ('tell the Harpers', "Then Gwennol will sing it, and every harper in Albion will learn it.", 'ending:lay')]),
        ],
        {'buried': {'text': "From the Lyonesse Remnant.", 'items': [k7], 'choice': [k6, k8, k9]},
         'lay': {'text': "From the Harpers of Tristan.", 'items': [k8], 'choice': [k6, k7, k9]}},
        requires='ly_drowned_knights', group=True)

# ======================================================================== The Cailleach (50)
c1 = z.item("Cailleach's Staff-Head", 'gem', 50, 'mind', "A stone the size of a fist, worn into a face.")
c2 = z.item("Sea-Wind Mantle", 'cloak', 50, 'ward', "Grey as a winter sea. The wind can't touch whoever wears it.")
c3 = z.item("Keeper of Tristan's Lay Ring", 'ring', 50, 'charm', "A harp in gold, very small.")
c4 = z.item("Hag-Stone Torc", 'neck', 50, 'faith', "A holed stone. Look through it and you see true.")
z.quest('ly_cailleach', 'The Cailleach', 50, 'ly_gwennol',
        "In the middle of the mire the cailleach keeps her ring - the old hag of the sea-wind, who was here before Lyonesse and will be here after. She blew the sea in for the white dragon once. She'll do it again for anyone who pays her.\n\nWill you [face the cailleach]? This is the hardest thing in Lyonesse. Bring everyone.",
        'face the cailleach',
        "The cailleach, the old hag of the sea-wind, keeps her ring in the heart of the mire.",
        [
            hunt((757, 846), "Fight through the cailleach's guards " + where((757, 846), 'ly_gwennol'), 'cailleach guard', 3),
            hunt((732, 839), "Fight through the cailleach's priests", 'cailleach priest', 2),
            hunt((737, 842), "Defeat Cailleach Uragaig", 'Cailleach Uragaig', 1,
                 text="The cailleach falls, laughing like a gale. 'The wind will find another mouth,' she says. 'It always does.' Then she's only stones."),
            end_talk('ly_gwennol', "Tell Harper Gwennol", "She's stones. The wind is just wind tonight.\n\nI'll write you into the lay - beside Tristan, if you'll allow it. Lyonesse will remember who stood up for it.", 'default'),
        ],
        {'default': {'text': "From the Harpers of Tristan.", 'choice': [c1, c2, c3, c4]}},
        requires='ly_witherwoode', group=True)
