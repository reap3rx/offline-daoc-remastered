"""Vale of Mularn's story quests (claude 2026-11-24, "Midgard - the plan", round 1) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_mularn

The realm's hub, Peaceful, where both threads show their first signs. The hounds go mad round Darkness Falls and the frost in
the great wolf-tracks there never melts (the west thread: Fimbulwinter, out of Raumarik). A dragon-preacher has come to the Vendo
Caverns and the vendo listen to him (the south thread: Gjalpinulva's drakulv, out of Malmohus). Meanwhile Mularn's ordinary
troubles: hobgoblin pranksters, the wood-eater hive, the hidden folk of the western woods.

The zone's two older quests are kept as they were (huldra, gormr).

Arcs (recommended levels): Mularn's Wardens (1-4), The Hive (4-8), The Hidden Folk (3-7), The Hounds (6-10),
The Vendo Caverns (8-11).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(100, 'Vale of Mularn', 'mid_mularn', 'story100_mularn', {'huldra', 'gormr'},
          {'sigrun', 'grima', 'hallvard', 'bjarki', 'bjarki_spring'},
          {'Huldra-Hair Bracelet', "Hallvard's Axe-Ring", 'Birch-Bark Sash', "Grima's Hearth Cloak", "Gormr's Collar", 'Broken Bone-Fetish',
           "Houndmaster's Belt", 'Spring-Water Ring'}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157
PREACHER = 60160115

person('md_ragnhild', 'Huscarl-Captain Ragnhild', (1236, 1308), 'f', 30, model=F, guild="King Eirik's Huscarls",
       idle="Mularn sleeps sound because somebody doesn't. Tonight that's me.")
person('md_ingrith', 'Seeress Ingrith', (1290, 742), 'f', 40, model=OLD, guild='the Volur of Haggerfel',
       idle="The well at Haggerfel shows me things. Lately it shows me snow, and a red eye in the dark.")
person('md_thorvald', 'Warden Thorvald', (1148, 186), 'm', 32, model=M, guild="King Eirik's Huscarls",
       idle="Fort Veldon watches the north road. Lately the north road watches back.")
person('md_eydis', 'Eydis the Go-Between', (438, 1196), 'f', 22, model=F, guild='the Volur of Haggerfel',
       idle="My grandmother married one of the hidden folk. Don't laugh. It's why they talk to me.")

# ======================================================================== Mularn's Wardens (1-4)
w1 = z.item("Prankster's Bell Charm", 'gem', 1, 'charm', "A hobgoblin's bell. It still jingles at the worst moments.")
w2 = z.item("Mularn Watch Ring", 'ring', 1, 'might', "Plain iron, stamped with the hall's mark.")
z.quest('md_pranksters', 'The Pranksters', 1, 'md_ragnhild',
        "Hobgoblins. Little grey things with bells on. They've cut the ropes off the well, painted the shrine, and put a goat on the jarl's roof. Twice.\n\nIt's not war. It's worse - it's embarrassing. Will you [chase them off]?",
        'chase them off',
        "Hobgoblin pranksters are making fools of Mularn.",
        [
            hunt((1100, 1150), "Chase off the hobgoblin pranksters " + where((1100, 1150), 'md_ragnhild'), 'hobgoblin prankster', 5),
            end_talk('md_ragnhild', "Tell Huscarl-Captain Ragnhild", "Good. The goat's still on the roof. One thing at a time.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [w1, w2]}})

w3 = z.item("Ale-Keg Hoop Bracer", 'bracer', 2, 'might', "A barrel hoop, bent round. It held good ale once.")
w4 = z.item("Goblin-Net Sash", 'belt', 2, 'finesse', "Knotted from a water goblin's net. Damp, always.")
z.quest('md_water_goblins', "The Jarl's Ale", 2, 'md_ragnhild',
        "The little water goblins in the meadow ponds have stolen a keg of the jarl's ale. They can't even drink it - it makes them sick. They do it for spite.\n\nWill you [get the keg back]?",
        'get the keg back',
        "Little water goblins stole a keg of the jarl's ale.",
        [
            hunt((1010, 1100), "Drive off the little water goblins " + where((1010, 1100), 'md_ragnhild'), 'little water goblin', 5),
            search(Z, P(985, 1120), "Search the water goblins' stash", "a muddy keg in the reeds", CRATE,
                   "The keg - half empty, and three water goblins asleep in the reeds beside it, looking very sorry for themselves."),
            end_talk('md_ragnhild', "Bring the keg to Ragnhild", "Half empty. The jarl will notice. I'll tell him you drank it - he'll like you better.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [w3, w4]}}, requires='md_pranksters')

w5 = z.item("Vein-Silk Cuff", 'bracer', 3, 'ward', "Spider silk, wound tight. It turns a knife, nearly.")
w6 = z.item("Cellar-Lantern Charm", 'gem', 3, 'mind', "A tiny lantern on a cord. Spiders hate it.")
z.quest('md_spiderlings', 'In the Cellars', 3, 'md_ragnhild',
        "Vein spiderlings in the meadows south of town, hatching by the hundred. Give it a month and they're in the cellars.\n\nWill you [thin them out]?",
        'thin them out',
        "Vein spiderlings are hatching in the meadows south of Mularn.",
        [
            hunt((1150, 1050), "Thin out the vein spiderlings " + where((1150, 1050), 'md_ragnhild'), 'vein spiderling', 6),
            end_talk('md_ragnhild', "Tell Ragnhild", "Fewer. That's all you can ask with spiders - fewer.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [w5, w6]}})

w7 = z.item("Snake-Finder's Ring", 'ring', 4, 'finesse', "A ring of snake-bone. The hobgoblins use them to find more snakes.")
w8 = z.item("Haggerfel Road Cloak", 'cloak', 4, 'ward', "Brown wool, for the road between the two towns.")
z.quest('md_snake_finders', 'The Snake-Finders', 4, 'md_ragnhild',
        "The hobgoblin snake-finders bag up mud snakes and let them loose on the Haggerfel road. Carters have stopped coming.\n\nWill you [clear the road]?",
        'clear the road',
        "Hobgoblin snake-finders loose snakes on the road between Mularn and Haggerfel.",
        [
            hunt((1160, 850), "Stop the hobgoblin snake-finders " + where((1160, 850), 'md_ragnhild'), 'hobgoblin snake-finder', 4),
            end_talk('md_ragnhild', "Tell Ragnhild", "The carters will be glad. Seeress Ingrith in Haggerfel wants to meet you, by the way - she says she saw you in her well.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [w7, w8]}})

# ======================================================================== The Hive (4-8)
h1 = z.item("Wood-Eater Mandible Pin", 'bracer', 4, 'might', "A wood-eater's jaw, made into a pin. It still clicks.")
h2 = z.item("Sawdust Satchel-Belt", 'belt', 4, 'ward', "A woodcutter's belt. Smells of fresh pine and something worse.")
z.quest('md_wood_eaters', 'The Wood-Eaters', 4, 'md_ragnhild',
        "The wood-eaters in the south have eaten the bridge at Jordheim road. The whole bridge. They're eating the fence-posts now.\n\nWill you [push them back]?",
        'push them back',
        "Wood-eaters from the hive in the south are eating Mularn's fences and bridges.",
        [
            hunt((920, 1250), "Push back the wood-eaters " + where((920, 1250), 'md_ragnhild'), 'wood-eater', 6),
            end_talk('md_ragnhild', "Tell Ragnhild", "Back to their hive. Which is growing. Which is a problem for later, and later is getting close.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [h1, h2]}})

h3 = z.item("Hive-Hunter's Chitin Charm", 'gem', 6, 'finesse', "A plate of wood-eater shell, polished.")
h4 = z.item("Alate-Wing Cloak", 'cloak', 6, 'ward', "Stiff, translucent, and somehow warm.")
z.quest('md_hive_hunters', 'Hive Hunters', 6, 'md_ragnhild',
        "The hive sends hunters now, out as far as the meadows. One took a calf yesterday. Wood-eaters don't eat calves. Something's changed down there.\n\nWill you [hunt the hunters]?",
        'hunt the hunters',
        "Wood-eater hunters range out of the hive and take Mularn's calves.",
        [
            hunt((900, 1160), "Hunt the wood-eater hunters " + where((900, 1160), 'md_ragnhild'), 'wood-eater hunter', 3),
            end_talk('md_ragnhild', "Tell Ragnhild", "A new king in the hive, then. A hungry one. Bring friends when you go for him.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [h3, h4]}}, requires='md_wood_eaters')

h5 = z.item("Hive-King's Crown-Plate", 'gem', 8, 'might', "A plate of the hive king's crest. It hums.")
h6 = z.item("Royal-Guard Bracer", 'bracer', 8, 'ward', "Thick chitin, the royal guard's own.")
h7 = z.item("Mularn Hearth Ring", 'ring', 8, 'charm', "Given by the jarl's household, with thanks.")
z.quest('md_hive_king', 'The Hive King', 8, 'md_ragnhild',
        "The new wood-eater king sits in the hive's heart with his royal guard round him. Kill him and the hive goes back to eating trees, not calves.\n\nIt's a job for a few of you. Will you [go into the hive]?",
        'go into the hive',
        "A hungry new king rules the wood-eater hive south of Mularn.",
        [
            hunt((780, 1220), "Bring down the wood-eater king " + where((780, 1220), 'md_ragnhild'), 'wood-eater king', 1, r=60),
            end_talk('md_ragnhild', "Tell Ragnhild", "The jarl wants to give you something. I talked him down from the goat.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [h5, h6, h7]}}, requires='md_hive_hunters', group=True)

# ======================================================================== The Hidden Folk (3-7)
f1 = z.item("Milk-Pail Charm", 'gem', 3, 'charm', "A tiny tin pail. The hidden folk leave these where they've been fed.")
f2 = z.item("Birch-Shadow Sash", 'belt', 3, 'finesse', "Grey-green and hard to see in a wood.")
z.quest('md_lurkers', 'Milk in the Night', 3, 'md_eydis',
        "The huldu lurkers have been stealing milk from the farms. That isn't new - you leave out a bowl, and they leave you alone. But they're taking the pails now, and the cows.\n\nSomething is frightening them. Will you [drive them back]? Gently, if you can.",
        'drive them back',
        "Huldu lurkers have begun stealing pails and cows from the farms by the western woods.",
        [
            hunt((420, 1120), "Drive back the huldu lurkers " + where((420, 1120), 'md_eydis'), 'huldu lurker', 5),
            end_talk('md_eydis', "Tell Eydis", "They're frightened. The hidden folk don't frighten easily. Something in the west is moving.", 'default'),
        ],
        {'default': {'text': "From the Volur of Haggerfel.", 'choice': [f1, f2]}})

f3 = z.item("Outcast's Tail-Ribbon", 'bracer', 4, 'charm', "A ribbon tied round a huldu's tail. She gave it freely.")
f4 = z.item("Hidden-Path Ring", 'ring', 4, 'mind', "Birch-bark, set in silver. You keep seeing paths that weren't there.")
z.quest('md_outcasts', 'The Outcasts', 4, 'md_eydis',
        "The huldu outcasts - the ones their own folk turned out - camp near the farms now. They say they're hiding. From what, they won't say.\n\nThe farmers want them gone. Will you [move them on]? They'll go further west, at least.",
        'move them on',
        "Huldu outcasts, turned out by their own folk, camp near the western farms.",
        [
            hunt((360, 1250), "Move on the huldu outcasts " + where((360, 1250), 'md_eydis'), 'huldu outcast', 4),
            end_talk('md_eydis', "Tell Eydis", "One of them said a word as she went. 'Fimbul.' I hope I heard wrong.", 'default'),
        ],
        {'default': {'text': "From the Volur of Haggerfel.", 'choice': [f3, f4]}}, requires='md_lurkers')

f5 = z.item("White-Stone Ring", 'ring', 7, 'mind', "A pebble from the huldu ring, set in silver. Cold.")
f6 = z.item("Birch-Bark Letter-Charm", 'gem', 7, 'charm', "The hidden folk's letter, folded small. It doesn't open again.")
f7 = z.item("Seeress's Shawl", 'cloak', 7, 'faith', "Grey, with the nine-knot border of Haggerfel's volur.")
z.quest('md_huldu_ring', 'The Ring of White Stones', 7, 'md_ingrith',
        "The hidden folk keep a ring of white stones in the western woods. When they want to speak to us, they leave a letter there - birch-bark. My well says there's one waiting.\n\nThe huldu stalkers guard the ring. Will you [fetch the letter]?",
        'fetch the letter',
        "The hidden folk have left a birch-bark letter at their ring of white stones in the western woods.",
        [
            reach(Z, P(320, 940), "Go to the huldu ring in the western woods", "White stones in a circle, and in the middle a fresh birch with its bark half peeled. The stalkers watch you from the trees.", r=20),
            search(Z, P(270, 930), "Search the ring of white stones", "birch-bark, rolled and tied with hair", CRATE,
                   "The letter is in old runes. Even you can read the last line: 'THE WINTER WALKS. EVEN WE WILL HIDE.'",
                   give="the hidden folk's letter"),
            end_talk('md_ingrith', "Bring the letter to Seeress Ingrith", "'The winter walks.' Fimbulwinter - the winter that comes before the end. The hidden folk have never written to us about anything bigger than cows.\n\nI need to look in the well. Come back - Warden Thorvald at Fort Veldon has hounds that won't stop howling. Go and see him.", 'default'),
        ],
        {'default': {'text': "From the Volur of Haggerfel.", 'choice': [f5, f6, f7]}})

# ======================================================================== The Hounds (6-10)
d1 = z.item("Phantom-Hound Collar", 'neck', 6, 'might', "A collar with no hound in it. It's still warm.")
d2 = z.item("Falls-Mist Cloak", 'cloak', 6, 'ward', "Always slightly damp from Darkness Falls.")
z.quest('md_phantom_hounds', 'Darkness Falls', 6, 'md_thorvald',
        "Phantom hounds at Darkness Falls, in the west. They always ran there - ghosts of hounds, harmless mostly. Now they hunt. They've killed two shepherds.\n\nWill you [lay them]?",
        'lay them',
        "The phantom hounds of Darkness Falls have begun to hunt.",
        [
            hunt((240, 650), "Lay the phantom hounds " + where((240, 650), 'md_thorvald'), 'phantom hound', 5),
            end_talk('md_thorvald', "Tell Warden Thorvald", "They were running from something, not hunting. My own hounds do the same at night now - howl at the north-west and won't stop.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [d1, d2]}})

d3 = z.item("Wolfhound-Tooth Ring", 'ring', 8, 'might', "A fang in a band of iron.")
d4 = z.item("Kennel-Master's Bracer", 'bracer', 8, 'ward', "Scarred leather, bitten many times.")
z.quest('md_wolfhounds', 'Gone Wild', 8, 'md_thorvald',
        "Somebody's wolfhounds - big ones, good hunting dogs - have gone wild on the ridge west of Haggerfel. Rabid. They had masters once.\n\nI hate this job. Will you [do it for me]?",
        'do it for me',
        "Rabid wolfhounds that once had masters run wild on the ridge west of Haggerfel.",
        [
            hunt((740, 600), "Put down the rabid wolfhounds " + where((740, 600), 'md_thorvald'), 'rabid wolfhound', 5),
            end_talk('md_thorvald', "Tell Thorvald", "Thank you. One of them wore a collar from a farm in West Svealand. They came a long way to go mad here.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [d3, d4]}}, requires='md_phantom_hounds')

d5 = z.item("Frost-Track Charm", 'gem', 10, 'mind', "A shard of ice from the great wolf's track. It hasn't melted.")
d6 = z.item("Veldon Watch Mantle", 'cloak', 10, 'ward', "Fort Veldon's grey, with the watch-tower in white.")
d7 = z.item("Howl-Ward Torc", 'neck', 10, 'faith', "Iron and rowan, against the howling.")
z.quest('md_frost_tracks', 'The Frost in the Tracks', 10, 'md_thorvald',
        "The shepherds by Darkness Falls swear they've seen a wolf as big as a horse, walking at moonrise. I'd laugh, but my hounds aren't laughing.\n\nGo up past the falls and [find its tracks]. Look. Don't fight it alone.",
        'find its tracks',
        "Shepherds by Darkness Falls swear they've seen a wolf as big as a horse.",
        [
            reach(Z, P(200, 560), "Climb past Darkness Falls", "Wind off the falls, and the smell of snow, in summer.", r=20),
            search(Z, P(185, 520), "Look for the great wolf's tracks", "a paw-print the size of a shield", CRATE,
                   "Each print is rimed with frost. In the sun. They come down out of the north-west, out of the mountains - from where the winter doesn't end."),
            end_talk('md_thorvald', "Tell Thorvald", "Frost that won't melt. That's Raumarik frost. Gods.\n\nThe Moon-Howler, the shepherds call it. If it comes down to the falls again, the whole vale will need to go out against it.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [d5, d6, d7]}}, requires='md_wolfhounds')

# ======================================================================== The Vendo Caverns (8-11)
v1 = z.item("Bone-Collector's Ring", 'ring', 8, 'mind', "Finger bones on a wire. Not yours, thankfully.")
v2 = z.item("Barrow-Ward Belt", 'belt', 8, 'ward', "Stitched with the barrow-runes the vendo tried to dig past.")
z.quest('md_bone_collectors', 'The Bone-Collectors', 8, 'md_ingrith',
        "The vendo - the wild men of the north caves - have started digging up the old barrows and carrying the bones home. They never did that before.\n\nWill you [stop the digging]?",
        'stop the digging',
        "The vendo of the northern caves are digging up the old barrows.",
        [
            hunt((600, 420), "Stop the vendo bone-collectors " + where((600, 420), 'md_ingrith'), 'vendo bone-collector', 5),
            end_talk('md_ingrith', "Tell Seeress Ingrith", "They were carrying the bones TO someone. The well shows me a man in a red-scaled cloak, at the cave mouth, preaching.", 'default'),
        ],
        {'default': {'text': "From the Volur of Haggerfel.", 'choice': [v1, v2]}})

v3 = z.item("Vendo Fetish-Charm", 'gem', 9, 'faith', "A shaman's fetish. Someone has painted a red eye on it.")
v4 = z.item("Cave-Fur Mantle", 'cloak', 9, 'ward', "Thick and smoky. The vendo know how to keep warm.")
z.quest('md_vendo_shamans', 'The Red Eye', 9, 'md_ingrith',
        "The vendo shamans have painted red eyes on their fetishes - a dragon's eye. Their old spirits are being pushed aside.\n\nWill you [break the shamans]? Bring me a fetish if you can.",
        'break the shamans',
        "The vendo shamans have painted a dragon's red eye on their fetishes.",
        [
            hunt((700, 350), "Break the vendo shamans " + where((700, 350), 'md_ingrith'), 'vendo shaman', 5),
            end_talk('md_ingrith', "Tell Ingrith", "A red eye. Somebody is teaching the vendo to worship a dragon. There is only one dragon in Midgard who wants worshippers.", 'default'),
        ],
        {'default': {'text': "From the Volur of Haggerfel.", 'choice': [v3, v4]}}, requires='md_bone_collectors')

v5 = z.item("Dragon-Tongue's Tract", 'gem', 11, 'mind', "A scrap of red vellum. The words on it squirm.")
v6 = z.item("Preacher-Breaker's Ring", 'ring', 11, 'might', "Iron, plain, and heavy. Thorvald's gift.")
v7 = z.item("Cavemouth Bracer", 'bracer', 11, 'ward', "Rough leather, scorched at the edge.")
z.quest('md_preacher', 'The Dragon-Preacher', 11, 'md_thorvald',
        "Ingrith's well was right. There's a preacher at the Vendo Caverns - red-scaled cloak, voice like honey - telling the vendo that the gods are finished and a mother-dragon will make them kings.\n\nHe has vendo round him. Bring friends, and [silence him].",
        'silence him',
        "A drakulv dragon-preacher at the mouth of the Vendo Caverns tells the vendo the gods are finished.",
        [
            search(Z, P(690, 205), "Search the cave mouth for the preacher's tracts", "red vellum nailed to a post", CRATE,
                   "'THE AESIR ARE OLD. THE WINTER COMES FOR THEM. ONLY THE MOTHER'S FIRE WILL KEEP YOU WARM.' Below it, a dragon's eye."),
            boss(Z, P(700, 175), "Defeat Hrafnkel Dragon-Tongue", "The preacher falls, still smiling. 'She will come for the Vale. She comes for everything.'",
                 'Hrafnkel Dragon-Tongue', PREACHER, 13, "A man in a cloak of red scales steps out of the cave: 'Come to hear the good news? Midgard is dying. Gjalpinulva will hatch the next one.'",
                 objective='Defeat Hrafnkel Dragon-Tongue', hp=2.4, adds=[(60167594, 'vendo warrior', [9, 10])], every=30, count=2),
            end_talk('md_thorvald', "Tell Warden Thorvald", "Gjalpinulva. The dragon of Malmohus. So the south has started talking, while the north starts howling.\n\nHe had a letter on him. Take it to Ingrith.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [v5, v6, v7]}}, requires='md_vendo_shamans', group=True)

v8 = z.item("Well-Water Charm", 'gem', 11, 'faith', "A drop of Haggerfel's well in glass. It shows you nothing. Yet.")
v9 = z.item("Jordheim Courier's Belt", 'belt', 11, 'finesse', "Royal blue, with Eirik's mark.")
z.quest('md_two_signs', 'Two Signs', 11, 'md_ingrith',
        "Thorvald sent you with the preacher's letter? Let me read it. ... It names Malmohus, and the svartalf traders of Gotar who carry the dragon's word north. And it laughs at us: 'the wolf-winter will finish the Aesir, and the mother will warm what's left.'\n\nTwo signs, one letter. Will you [read it with me]? Then we'll decide where it goes.",
        'read it with me',
        "A drakulv preacher's letter names Malmohus, Gotar's svartalf traders and the wolf-winter.",
        [
            choice('md_ingrith', "Decide what to do with the letter",
                   "To [Jordheim], and the King's huscarls march sooner. Or to [the well], and the volur learn what the dragon knows of the winter.",
                   [('Jordheim', "Then ride. The King should know what's coming from both ends.", 'ending:king'),
                    ('the well', "Then sit with me while I read. It'll be a long night.", 'ending:well')]),
        ],
        {'king': {'text': "From the Volur of Haggerfel.", 'items': [v9], 'choice': [v8]},
         'well': {'text': "From the Volur of Haggerfel.", 'items': [v8], 'choice': [v9]}}, requires='md_preacher')
