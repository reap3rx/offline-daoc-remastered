"""Avalon Marsh's story quests (claude 2026-11-24, "Albion - the plan", round 2) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_avalon_marsh

The marsh round the Isle where Arthur sleeps. Both threads want the Sleeper. Golestandt's giants are laying a causeway of
Cornish granite across the west marsh toward the Isle, with the Marsh Lord's leave; and Morgana's people cross by night in the
black barge that carried Arthur to Avalon, rowed by the drowned dead of the shore chapel, for whoever bears the key and crown.
In the north-west the Drowned Vigil still holds its keep - the zone's fort to retake. At the end, Morgause of Orkney, Morgana's
sister and Mordred's mother, comes to the shore herself.

The zone's two older quests are kept as they were (bog_king, vigil).

Arcs (recommended levels): The North Marsh (6-12), The Isle (11-16), The Giants' Causeway (14-23, Deadly toward Cornwall),
The Drowned Vigil (19-21), The Way to the Isle (24).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk
from albion_story import Story, CRATE, BEDROLL, LANTERN, M, F, OLD

S = Story(9, 'Avalon Marsh', 'alb_avalon_marsh', 'story009_avalon_marsh', {'bog_king', 'vigil'},
          {'tilda_hael', 'warden_brec', 'dai_morrow', 'squire_hamon', 'sir_baldwin', 'last_vigil'},
          {'Reed Crown Circlet', "Bog-King's Ring", 'Lily-Pad Mantle', "Marsh-Warden's Belt", 'Signet of the Vigil', 'Banner of the Vigil',
           "Corentin's Sword-Belt", 'Relief-Bell Charm'})
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
INITIATE, CORNISH, GHOUL_KNIGHT = 12075, 12840, 12018

# ------------------------------------------------------------------ people
person('am_maelor', 'Warden-Captain Maelor', (1376, 356), 'm', 36, model=28, guild='the Marsh Wardens',
       idle="Adribard's Retreat is dry, mostly. That's the best I can say for it.")
person('am_argante', 'Lady Argante', (952, 470), 'f', 44, guild='the Keepers of the Isle',
       idle="Three queens carried the King across that water. I was there. I keep the shore.")

# ======================================================================== The North Marsh (6-12)
n1 = z.item("Bog-Net Bracer", 'bracer', 6, 'might', "Cut from a bogman's net. It still smells of fish.")
n2 = z.item("Retreat Warden's Belt", 'belt', 6, 'ward', "Marsh Warden issue, waxed against the damp.")
z.quest('am_bog_nets', "The Bogmen's Nets", 6, 'am_maelor',
        "Bogmen. Usually they keep to themselves and their fish. This month they've been stringing nets across the channels south of the Retreat and taking whoever paddles into them.\n\nWill you [cut the nets]? Thin the bogmen while you're at it.",
        'cut the nets',
        "Bogmen are stringing nets across the channels south of Adribard's Retreat.",
        [
            hunt((1300, 500), "Drive off the bogmen in the channels " + where((1300, 500), 'am_maelor'), 'bogman', 5),
            search(Z, P(1250, 560), "Cut the bogmen's nets", "a net strung across the channel", CRATE,
                   "You cut the nets. Tangled in one: a little crown of reeds, the kind the bogmen weave for someone they bow to."),
            end_talk('am_maelor', "Tell Warden-Captain Maelor", "A reed crown. They've got a king again, have they? Tilda Hael in Caer Witrin had trouble with that.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [n1, n2]}})

n3 = z.item("Bloody-Bones Knuckle Charm", 'gem', 10, 'might', "Don't ask whose knuckle.")
n4 = z.item("Drowned Bell-Rope Belt", 'belt', 10, 'faith', "From the bell of a church the marsh swallowed.")
z.quest('am_drowned_church', 'The Drowned Church', 10, 'am_maelor',
        "There was a church in the middle marsh once - the marsh ate it a hundred years ago. Its dead have started walking: bloody-bones, the locals call the worst of them.\n\nWill you [put them down]?",
        'put them down',
        "The dead of a drowned church walk the middle marsh.",
        [
            hunt((821, 650), "Put down the bloody-bones " + where((821, 650), 'am_maelor'), 'bloody-bones', 4),
            hunt((1151, 577), "Lay the decayed dead to rest", 'decayed zombie', 4),
            end_talk('am_maelor', "Tell Warden-Captain Maelor", "The marsh is restless. The Lady on the shore says it's because of who's been crossing to the Isle.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [n3, n4]}})

n5 = z.item("Wisp-Glass Ring", 'ring', 9, 'charm', "A trapped wisp-light, very faint, inside a glass bead.")
n6 = z.item("Reed-Cutter's Sash", 'belt', 9, 'finesse', "Woven from marsh reeds by Warden Brec's wife.")
z.quest('am_wisps', 'Lights over the Water', 9, 'warden_brec',
        "Will o' wisps over the south pools. They lead fishermen out onto soft ground and leave them there.\n\nWill you [put out the lights]? Kill enough and the rest go dim.",
        'put out the lights',
        "Will o' wisps lead fishermen to their deaths in the south pools.",
        [
            hunt((673, 1491), "Put out the will o' wisps " + where((673, 1491), 'warden_brec'), "will o' wisp", 5),
            end_talk('warden_brec', "Tell Warden Brec", "Quieter nights for the fishermen. Thank you.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [n5, n6]}})

n7 = z.item("Scrag-Hide Bracer", 'bracer', 12, 'ward', "Tough, warty and surprisingly comfortable.")
n8 = z.item("Scraek's Tooth Charm", 'gem', 12, 'might', "Scraek had a lot of teeth. Now he has one fewer.")
z.quest('am_scrags', 'Scrags in the Reeds', 12, 'warden_brec',
        "Scrags in the southern reeds, and a big one called Scraek in the middle marsh who leads them. They've started raiding the fishing huts.\n\nWill you [deal with the scrags]?",
        'deal with the scrags',
        "Scrags led by Scraek are raiding the fishing huts in the south.",
        [
            hunt((1117, 1419), "Clear the scrags in the southern reeds " + where((1117, 1419), 'warden_brec'), 'scrag', 5),
            hunt((1120, 1038), "Kill Scraek", 'Scraek', 1),
            end_talk('warden_brec', "Tell Warden Brec", "Scraek, dead? The fishermen will name a boat after you.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [n7, n8]}})

# ======================================================================== The Isle (11-16)
i1 = z.item("Mist-Sprite Veil", 'cloak', 11, 'charm', "So fine you can see through it. The mist sticks to it.")
i2 = z.item("Isle-Shore Pebble Ring", 'ring', 11, 'faith', "A white pebble from the Isle's shore, set in silver.")
z.quest('am_mists', 'The Thickening Mist', 11, 'am_argante',
        "The mist round the Isle has thickened, and the sprites in it have turned sharp. The mist is the Isle's guard - it only thickens when someone tries to cross who shouldn't.\n\nWill you [walk the shore]? Thin the sprites, and look at the landing.",
        'walk the shore',
        "The mist round the Isle of Avalon has thickened, which means someone is trying to cross.",
        [
            hunt((801, 527), "Thin the mist sprites " + where((801, 527), 'am_argante'), 'mist sprite', 5),
            search(Z, P(1095, 478), "Search the landing on the Isle's shore", "a stone landing-stage", CRATE,
                   "Keel-marks in the mud, fresh. A long, narrow boat has been drawn up here - and the rope-post is tied with a red cord."),
            end_talk('am_argante', "Tell Lady Argante", "A long, narrow boat. There is only one boat that crosses to the Isle, and it is black, and it carried the King.\n\nSomeone is using the barge.", 'default'),
        ],
        {'default': {'text': "From the Keepers of the Isle.", 'choice': [i1, i2]}},
        topics={'queens': "Three queens took Arthur to Avalon in the black barge: the Queen of Northgales, the Queen of the Waste Lands - and Morgan le Fay. Yes. She was one of them. That is what frightens me."})

i3 = z.item("Barge-Oar Bracer", 'bracer', 14, 'might', "Black wood, salt-white at the grip.")
i4 = z.item("Chapel-Register Clasp", 'gem', 14, 'mind', "From the chapel's register of the dead. Argante kept the book.")
i5 = z.item("Page's Black Ribbon", 'belt', 14, 'faith', "The pages of the shore chapel wore black for the King.")
z.quest('am_black_barge', 'The Black Barge', 14, 'am_argante',
        "The barge is rowed by the dead of the shore chapel - the knights and pages who kept vigil for the King and drowned at their posts. They row for the Keepers. But they're rowing for someone else now.\n\nWill you [go to the chapel]? Find out who they row for.",
        'go to the chapel',
        "The black barge that carried Arthur to Avalon is being rowed for someone else by the dead of the shore chapel.",
        [
            hunt((1257, 1023), "Get past the phantom pages " + where((1257, 1023), 'am_argante'), 'phantom page', 4),
            search(Z, P(1040, 1205), "Read the shore chapel's register", "a register in the chapel's ruin", CRATE,
                   "The last pages, in a new hand: 'The barge goes out at the new moon for whoever bears the key and the crown, by order of the Lady of the Lake's sister.' And a list of crossings - eleven of them.",
                   give="the chapel register"),
            end_talk('am_argante', "Bring the register to Lady Argante", "'The Lady of the Lake's sister.' Morgana has bound the barge's dead to her seal. Eleven crossings. Eleven of her people have stood on the Isle where the King sleeps.\n\nGod help us if one of them reaches him.", 'default'),
        ],
        {'default': {'text': "From the Keepers of the Isle.", 'choice': [i3, i4, i5]}},
        requires='am_mists')

i6 = z.item("Fiedel's Tarnished Spur", 'gem', 24, 'might', "Silver gone black. He was a good knight, once.")
i7 = z.item("Aryon's Broken Oath-Ring", 'ring', 24, 'faith', "Snapped clean in two, and mended with gold.")
i8 = z.item("Shore-Vigil Mantle", 'cloak', 24, 'ward', "Black, with the Isle's white tower. The Keepers' own.")
z.quest('am_fallen_paladins', 'The Fallen Paladins', 24, 'am_argante',
        "The barge's dead won't stop rowing while their captains hold them to Morgana's seal: Sir Fiedel and the Dread Lord Aryon, who were paladins of the King once. They fell when the vigil drowned and got up again under her hand.\n\nWill you [free the chapel]? Bring your strongest. They were the best of us.",
        'free the chapel',
        "Two fallen paladins hold the dead of the shore chapel to Morgana's seal.",
        [
            hunt((1032, 1215), "Cut through the ghostly knights at the shore chapel " + where((1032, 1215), 'am_argante'), 'ghostly knight', 3),
            hunt((1028, 1181), "Defeat Undead Knight Fiedel", 'Undead Knight Fiedel', 1),
            hunt((1025, 1225), "Defeat Dread Lord Aryon", 'Dread Lord Aryon', 1,
                 text="Aryon kneels in the water. 'Tell the King,' he says, 'we kept the vigil as long as we could.'"),
            end_talk('am_argante', "Tell Lady Argante", "They're free. The barge will row for the Keepers again, and only for us.\n\nI'll tell the King myself, when he wakes. He'll want to know.", 'default'),
        ],
        {'default': {'text': "From the Keepers of the Isle.", 'choice': [i6, i7, i8]}},
        requires='am_black_barge', group=True)

# ======================================================================== The Giants' Causeway (14-23) - Deadly toward Cornwall
c1 = z.item("Shambler-Moss Bracer", 'bracer', 14, 'ward', "Thick green moss on leather. It never dries out.")
c2 = z.item("Granite-Dust Charm", 'gem', 14, 'might', "Pink-grey dust in a glass vial. Dartmoor granite.")
z.quest('am_shamblers', 'The Shambling Road', 14, 'warden_brec',
        "Shamblers in the south-west - walking heaps of marsh. They've always been there. But now they walk in lines, and they carry things.\n\nWill you [follow the shamblers]?",
        'follow the shamblers',
        "The shamblers of the south-west marsh walk in lines, carrying things.",
        [
            hunt((353, 1110), "Break up the shambler lines " + where((353, 1110), 'warden_brec'), 'shambler', 6),
            search(Z, P(340, 1120), "Look at what the shamblers carried", "a heap of dropped stones", CRATE,
                   "Blocks of grey granite flecked with pink, dressed square. The shamblers were carrying them east, toward the Isle."),
            end_talk('warden_brec', "Tell Warden Brec", "Granite? We've no granite in the marsh. That's Cornwall's - or further.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [c1, c2]}})

c3 = z.item("Giant-Wolf Pelt Mantle", 'cloak', 16, 'ward', "Grey and huge. It drags on the ground even after Brec's wife cut it down.")
c4 = z.item("Wolf-Fang Torc", 'neck', 16, 'might', "Three fangs, each as long as a finger.")
z.quest('am_giant_wolves', 'Wolves of the West Marsh', 16, 'warden_brec',
        "Giant wolves on the west marsh - out of Cornwall, I'd guess, driven ahead of something bigger. They've taken two of my wardens.\n\nWill you [hunt the wolves]?",
        'hunt the wolves',
        "Giant wolves, driven out of Cornwall, are hunting the west marsh.",
        [
            hunt((369, 644), "Hunt the giant wolves " + where((369, 644), 'warden_brec'), 'giant wolf', 5),
            end_talk('warden_brec', "Tell Warden Brec", "Driven ahead of something bigger. I keep coming back to that.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [c3, c4]}})

c5 = z.item("Mist-Monster Eye", 'gem', 18, 'mind', "A pale, clouded orb. It looks back.")
c6 = z.item("Fog-Walker's Belt", 'belt', 18, 'finesse', "Hung with bells so your friends can find you in the fog.")
z.quest('am_mist_monsters', 'What Walks in the Fog', 18, 'am_maelor',
        "On the far west marsh the fog never lifts, and something walks in it. Mist monsters, the old fishermen say. Nobody who goes in to look comes back to say more.\n\nWill you [go into the fog]? Bring friends who can find you.",
        'go into the fog',
        "Mist monsters walk the fog of the far west marsh.",
        [
            hunt((191, 569), "Kill the mist monsters " + where((191, 569), 'am_maelor'), 'mist monster', 3),
            end_talk('am_maelor', "Tell Warden-Captain Maelor", "You came back. That's more than most. What did you see?\n\n...Giants' footprints, going east. In the fog. Of course.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [c5, c6]}},
        group=True)

c7 = z.item("Causeway Kerb-Stone Ring", 'ring', 20, 'might', "Cut from the giants' kerb-stone. Heavy.")
c8 = z.item("Marsh-Warden's Wading Mantle", 'cloak', 20, 'ward', "Oiled wool to the knee. The wardens swear by it.")
c9 = z.item("Brec's Lucky Charm", 'gem', 20, 'charm', "Brec's own, a pierced shell. He says he won't need luck now.")
z.quest('am_causeway', "The Giants' Causeway", 20, 'warden_brec',
        "My wardens found it in the south-west: a road, of dressed granite, laid across the marsh. Built by giants - Cornish giants, out of the west. And it points at the Isle.\n\nWill you [break the causeway]? Kill the builders. Tip the stones into the mire.",
        'break the causeway',
        "Cornish giants are laying a granite causeway across the south-west marsh toward the Isle.",
        [
            hunt((260, 1080), "Kill the giants building the causeway " + where((260, 1080), 'warden_brec'), 'Cornish giant', 2),
            search(Z, P(200, 1110), "Tip the causeway's kerb-stones into the mire", "a granite kerb-stone, half-laid", CRATE,
                   "The stone goes over with a heave and a sucking splash. Carved on its underside: a dragon's claw, and 'For the Sleeper.'"),
            end_talk('warden_brec', "Tell Warden Brec", "'For the Sleeper.' A road to the King, so the giants can walk to him dry-shod.\n\nThe Lady on the shore must hear this.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [c7, c8, c9]}},
        requires='am_shamblers')

c10 = z.item("Marsh Lord's Sceptre-Ring", 'ring', 23, 'mind', "A ring of black bog-oak, from his reed sceptre.")
c11 = z.item("Mire-Crown Torc", 'neck', 23, 'might', "Twisted bog-iron. He wore it as a crown.")
c12 = z.item("Peat-Black Mantle", 'cloak', 23, 'ward', "Smells of peat smoke, always.")
z.quest('am_marsh_lord', 'The Marsh Lord', 23, 'warden_brec',
        "The giants couldn't lay a road through the mire without the mire's leave. The Marsh Lord gave it - the old thing that rules the deep bog in the far south-west. The bogmen whisper he was paid in Cornish tin.\n\nWill you [end the Marsh Lord]? He's old and he's strong. Take everyone.",
        'end the Marsh Lord',
        "The Marsh Lord sold the giants the way across the mire for Cornish tin.",
        [
            hunt((644, 986), "Break the mud golems that guard the mire road " + where((644, 986), 'warden_brec'), 'mud golem', 3),
            hunt((298, 1358), "Defeat the Marsh Lord", 'Marsh Lord', 1,
                 text="The Marsh Lord sinks into his bog with a long, wet sigh. Tin ingots tumble out of the mud where he lay."),
            end_talk('warden_brec', "Tell Warden Brec", "Tin. He sold the King's marsh for tin.\n\nWithout him, the mire won't hold their road. You've bought the Isle time.", 'default'),
        ],
        {'default': {'text': "From the Marsh Wardens.", 'choice': [c10, c11, c12]}},
        requires='am_causeway', group=True)

# ======================================================================== The Drowned Vigil (19-21)
v1 = z.item("Ghoul-Court Seal", 'gem', 19, 'mind', "The seal of the Vigil's court, gone green.")
v2 = z.item("Footman's Rusted Bracer", 'bracer', 19, 'ward', "Rusted through in places. Still turns a blade.")
z.quest('am_ghoul_court', 'The Ghoul Court', 19, 'squire_hamon',
        "The Vigil's dead hold court in the north-west marsh - ghoul footmen drilling on the old parade ground as if nothing's changed in three hundred years.\n\nI want to know what they're guarding. Will you [scout the court]?",
        'scout the court',
        "The Drowned Vigil's ghoul footmen drill on their old parade ground in the north-west.",
        [
            hunt((371, 382), "Fight through the ghoul footmen " + where((371, 382), 'squire_hamon'), 'ghoul footman', 4),
            search(Z, P(410, 330), "Search the Vigil's walls", "a wall of drowned stone", CRATE,
                   "Behind the walls, the Vigil's keep - and on its tower, still flying after three hundred years, a banner. Grey, with a white tower. The Vigil's colours."),
            end_talk('squire_hamon', "Tell Squire Hamon", "Their banner still flies. Sir Corentin would have given anything to see it.\n\nIf we could take it down - take the keep back - the Vigil could rest.", 'default'),
        ],
        {'default': {'text': "From Squire Hamon.", 'choice': [v1, v2]}})

v3 = z.item("Vigil-Tower Ring", 'ring', 21, 'faith', "The Vigil's white tower, cut in grey stone.")
v4 = z.item("Drowned Keep Torc", 'neck', 21, 'might', "Green bronze, from the keep's chapel.")
v5 = z.item("Relief-Watch Mantle", 'cloak', 21, 'ward', "Grey wool. Worn by those who came to relieve the Vigil.")
z.quest('am_vigil_banner', "The Vigil's Banner", 21, 'squire_hamon',
        "The Vigil drowned at its posts because nobody came to relieve them. Somebody should. Bring down their banner from the keep, and they'll know they've been relieved.\n\nWill you [bring down the banner]? The keep is full of them. You'll need a group.",
        'bring down the banner',
        "Squire Hamon wants the Drowned Vigil's banner brought down from their keep, so they know they've been relieved.",
        [
            hunt((400, 300), "Cut through the ghoul knights in the keep " + where((400, 300), 'squire_hamon'), 'ghoul knight', 4),
            hunt((360, 240), "Defeat a ghoul lord of the Vigil", 'ghoul lord', 1),
            search(Z, P(358, 232), "Bring down the banner from the tower", "the Vigil's banner, still flying", CRATE,
                   "The banner comes down in your hands, damp and heavy. Across the keep, for a moment, every ghoul stands still and looks up.",
                   give="the Vigil's banner"),
            end_talk('squire_hamon', "Bring the banner to Squire Hamon", "Relieved. After three hundred years.\n\nThey won't all rest yet - they're too used to standing. But the Marsh Wardens could take that keep now, with enough hands.", 'default'),
        ],
        {'default': {'text': "From Squire Hamon.", 'choice': [v3, v4, v5]}},
        requires='am_ghoul_court', group=True)

# ======================================================================== The Way to the Isle (24)
w1 = z.item("Argante's Pearl", 'gem', 24, 'faith', "A pearl from the Isle's shore. It glows at dusk.")
w2 = z.item("Orkney Queen's Circlet-Ring", 'ring', 24, 'mind', "Cut from Morgause's circlet. It's colder than metal should be.")
w3 = z.item("Keeper of the Isle's Mantle", 'cloak', 24, 'ward', "White and grey, with the Isle's tower. Argante's gift.")
w4 = z.item("Sleeper's Guard Torc", 'neck', 24, 'might', "Given to those who stood between the King and his enemies.")
z.quest('am_way_to_isle', 'The Way to the Isle', 24, 'am_argante',
        "The barge is free and the causeway's broken - and that has made her angry. Morgause of Orkney is coming to the shore herself: Morgana's sister, Mordred's mother. She'll try to cross by force.\n\nWill you [stand on the shore] with me? Bring everyone. This is the King's last door.",
        'stand on the shore',
        "Morgause of Orkney, Morgana's sister, comes to force a crossing to the Isle where Arthur sleeps.",
        [
            reach(Z, P(1095, 470), "Go to the Isle's landing " + where((1095, 470), 'am_argante'), "The mist parts. Red torches on the water, coming closer.", r=30),
            defend(Z, (1100, 465), "Keep Lady Argante alive on the landing",
                   "The Crimson break on the shore - and a tall woman in a black crown steps out of the mist.",
                   'Lady Argante', 60167630, 24, "Argante raises her hands and the mist thickens round the landing. 'Hold them! They must not set foot on the Isle!'",
                   [(INITIATE, 'crimson initiate', [22, 23]), (GHOUL_KNIGHT, 'drowned oarsman', [22, 23])], 'Keep Lady Argante alive',
                   model=F, duration=120,
                   then_boss={'tpl': INITIATE, 'name': 'Morgause of Orkney', 'lv': 25,
                              'announce': "Morgause of Orkney, in a black crown: 'My son is dead because of that man. Let me see him sleep. Only for a moment.'"}),
            choice('am_argante', "Speak with Lady Argante on the shore",
                   "She's gone - back into the mist. Not dead. Her kind never quite are.\n\nThe King sleeps safe tonight. But his enemies know the way now: Morgana at the lake of Llyn Barfog, and the white dragon in Dartmoor. Shall I [ring the shore-bell], so every Keeper and Warden knows the Isle held? Or do we [keep it quiet], and let them wonder?",
                   [('ring the shore-bell', "Then ring it. Let them hear it in Camelot.", 'ending:rung'),
                    ('keep it quiet', "Then the Isle keeps its own counsel, as it always has.", 'ending:quiet')]),
        ],
        {'rung': {'text': "From the Keepers of the Isle.", 'items': [w3], 'choice': [w1, w2, w4]},
         'quiet': {'text': "From the Keepers of the Isle.", 'items': [w1], 'choice': [w2, w3, w4]}},
        requires='am_fallen_paladins', group=True)
