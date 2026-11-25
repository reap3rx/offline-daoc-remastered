"""Vanern Swamp's story quests (claude 2026-11-25, "Midgard - the plan", round 3) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_vanern

Deadly. The west thread's dead: as the long winter comes, the hagbui - the barrow-dead of Vanern's old thanes - have risen and taken
Hrafnsholm, the watch-hold on the north-west ridge, and chained a jotun in its yard to work their forge: the zone's fort to retake,
for the Wardens of Vanern (out of their camp in the south-east). The jotun outcasts of the north have made a pact with Raumarik's
frost; the broken jotun of the west were the hagbui's earlier slaves.

The zone's two older quests are kept as they were (clay_child, barrow_brother).

Arcs (recommended levels): The Mud Flats (36-39), The Clay Pits (38-40), The Broken Jotun (40-42), The Jotun Outcasts (42-44),
The Spider Wood (43-45), Hrafnsholm (41-46).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(107, 'Vanern Swamp', 'mid_vanern', 'story107_vanern', {'clay_child', 'barrow_brother'},
          {'thorgunna', 'clay_boy', 'gunnvor'},
          {'Clay-Child Charm', 'Clay Jotun Bracer', "Swamp-Mother's Shawl", "Shaper's Ring", 'Leg-Biter Hilt-Ring', 'Barrow-Dark Cloak',
           "Ketil's Rune-Belt", 'Hagbui Thane Torc', "Runemistress' Bracer"}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157

person('vn_steinunn', 'Warden-Captain Steinunn', (1240, 1110), 'f', 48, model=F, guild='the Wardens of Vanern',
       idle="The Wardens held Hrafnsholm for three hundred years. We lost it in a night. To the dead.")
person('vn_gisli', 'Huscarl Gisli', (1222, 1098), 'm', 46, model=M, guild="King Eirik's Huscarls",
       idle="The King sent twelve of us. Vanern's had eleven so far.")

V, H = "From the Wardens of Vanern.", "From King Eirik's Huscarls."

# ======================================================================== The Mud Flats (36-39)
m1 = z.item("Mud-Crab Shell Bracer", 'bracer', 36, 'ward', "Crab-shell plates, lacquered black.")
m2 = z.item("Swamp-Warden's Ring", 'ring', 36, 'might', "Bog-iron, the Wardens' raven on it.")
z.quest('vn_crabs', 'The Mud Flats', 36, 'vn_steinunn',
        "Welcome to Vanern. The mud crab warriors come up the flats to the camp every night. They're the least of our troubles - start there.\n\nWill you [clear the flats]?",
        'clear the flats',
        "Mud crab warriors come up Vanern's mud flats to the Wardens' camp every night.",
        [
            hunt((1350, 1250), "Clear the mud crab warriors " + where((1350, 1250), 'vn_steinunn'), 'mud crab warrior', 5),
            end_talk('vn_steinunn', "Tell Warden-Captain Steinunn", "Good. You'll live long enough to be useful, maybe.", 'default'),
        ],
        {'default': {'text': V, 'choice': [m1, m2]}})

m3 = z.item("Viper-Fang Torc", 'neck', 38, 'might', "Two fangs, still faintly wet.")
m4 = z.item("Reed-Walker's Belt", 'belt', 38, 'finesse', "Woven reeds over leather.")
z.quest('vn_vipers', 'The Reed Road', 38, 'vn_steinunn',
        "The forest vipers on the reed road west of camp - every runner we send to the King gets bitten. Clear the road.\n\nWill you [clear the reed road]?",
        'clear the reed road',
        "Forest vipers bite every runner on Vanern's reed road.",
        [
            hunt((950, 1300), "Clear the forest vipers " + where((950, 1300), 'vn_steinunn'), 'forest viper', 5),
            end_talk('vn_steinunn', "Tell Steinunn", "The road's open. The runner can go to Jordheim. Not that the King has anyone left to send.", 'default'),
        ],
        {'default': {'text': V, 'choice': [m3, m4]}}, requires='vn_crabs')

# ======================================================================== The Clay Pits (38-40)
c1 = z.item("Clay-Jotun Knuckle Ring", 'ring', 39, 'might', "A ring of fired clay, very hard.")
c2 = z.item("Pit-Digger's Belt", 'belt', 39, 'ward', "Mud-caked, iron-buckled.")
z.quest('vn_clay_pits', 'The Clay Pits', 39, 'gunnvor',
        "The clay jotun in the middle of the swamp were always quiet - the swamp's own, made of its mud. Now they're angry, and someone's been digging in their pits.\n\nWill you [look into it]?",
        'look into it',
        "The clay jotun in the middle of Vanern Swamp have turned angry; someone has been digging in their pits.",
        [
            hunt((650, 950), "Fight through the clay jotun " + where((650, 950), 'gunnvor'), 'clay jotun', 4),
            search(Z, P(640, 960), "Search the dug-up pit", "a broken chain half-buried in the clay", CRATE,
                   "Black iron chains, carved with barrow-runes - the hagbui's. They've been digging clay jotun out of the pits, and dragging them north-west in chains."),
            end_talk('gunnvor', "Tell Runemistress Gunnvor", "Barrow-runes. The hagbui. They're taking slaves - jotun, to work their forge in Hrafnsholm. The dead don't need forges unless they mean war.", 'default'),
        ],
        {'default': {'text': V, 'choice': [c1, c2]}})

# ======================================================================== The Broken Jotun (40-42)
b1 = z.item("Broken-Chain Bracer", 'bracer', 40, 'might', "A cut length of hagbui chain, worn as a bracer.")
b2 = z.item("Jotun-Tear Charm", 'gem', 40, 'mind', "A grey stone. They say it's a jotun's tear.")
z.quest('vn_broken_jotun', 'The Broken Ones', 40, 'vn_gisli',
        "The broken jotun in the west - they were the hagbui's slaves before. Worked till they broke, then thrown out. They're mad with it, and they kill anything that moves.\n\nWill you [put them out of their misery]?",
        'put them out of their misery',
        "The broken jotun of Vanern's west, the hagbui's worn-out slaves, kill anything that moves.",
        [
            hunt((250, 850), "Put down the broken jotun " + where((250, 850), 'vn_gisli'), 'broken jotun', 4),
            end_talk('vn_gisli', "Tell Huscarl Gisli", "Mercy, of a sort. If that's what the hagbui do to their slaves, I'd rather not think about the one in the yard at Hrafnsholm.", 'default'),
        ],
        {'default': {'text': H, 'choice': [b1, b2]}}, requires='vn_clay_pits')

b3 = z.item("Crippled Giant's Ring", 'ring', 42, 'ward', "A ring big enough for a thumb. A jotun's little finger, once.")
b4 = z.item("Rune-Lifted Mantle", 'cloak', 42, 'faith', "Grey, with Gunnvor's runes of unbinding.")
z.quest('vn_crippled', 'The Crippled Jotun', 42, 'gunnvor',
        "The crippled jotun in the west still wear their chains - and the chains still hold the hagbui's runes. While they wear them, the hagbui can call them back. Break them free, the only way left.\n\nWill you [free them]?",
        'free them',
        "Vanern's crippled jotun still wear the hagbui's runed chains.",
        [
            hunt((200, 950), "Free the crippled jotun " + where((200, 950), 'gunnvor'), 'crippled jotun', 3),
            end_talk('gunnvor', "Tell Gunnvor", "Free. The runes broke with them - I felt it from here. Now we know how the hagbui hold their slaves. That's how we'll free the one in their yard.", 'default'),
        ],
        {'default': {'text': V, 'choice': [b3, b4]}}, requires='vn_broken_jotun')

# ======================================================================== The Jotun Outcasts (42-44)
o1 = z.item("Orm-Runner's Whip-Belt", 'belt', 42, 'finesse', "A jotun's whip, cut down to a belt.")
o2 = z.item("Enslaved Orm Scale Charm", 'gem', 42, 'ward', "A dull green scale, scarred by a harness.")
z.quest('vn_orm_runners', 'The Enslaved Orms', 42, 'vn_gisli',
        "The jotun outcasts in the north drive enslaved orms - harnessed, whipped, run till they drop. They're hauling something north-west.\n\nWill you [free the orms]?",
        'free the orms',
        "Jotun outcasts drive enslaved orms north-west across Vanern's north.",
        [
            hunt((650, 200), "Free the large enslaved orm runners " + where((650, 200), 'vn_gisli'), 'large enslaved orm runner', 5),
            end_talk('vn_gisli', "Tell Gisli", "They were hauling ice. Ice, in summer, out of the north-west - from Raumarik. The outcasts are building something.", 'default'),
        ],
        {'default': {'text': H, 'choice': [o1, o2]}}, requires='vn_broken_jotun')

o3 = z.item("Outcast's Frost-Torc", 'neck', 44, 'might', "Iron rimed with frost that never melts.")
o4 = z.item("Ice-Hauler's Bracer", 'bracer', 44, 'ward', "Fur over iron.")
o5 = z.item("King's Huscarl Mantle", 'cloak', 44, 'ward', "The King's blue, heavy wool. Gisli's spare.")
z.quest('vn_outcasts', 'The Outcasts', 44, 'vn_gisli',
        "The jotun outcasts themselves. They're building a road of ice to Raumarik. I want to know why. Bring friends - they're jotun.\n\nWill you [break the outcasts]?",
        'break the outcasts',
        "Jotun outcasts in Vanern's north are building a road of ice toward Raumarik.",
        [
            hunt((680, 200), "Break the jotun outcasts " + where((680, 200), 'vn_gisli'), 'jotun outcast', 3, r=60),
            search(Z, P(690, 210), "Search the outcasts' camp", "an ice-block carved with runes", CRATE,
                   "Carved deep in the ice: 'When Hati catches the moon, the long winter comes, and the jotun walk south on the ice behind him. The barrow-dead will open the door.'"),
            end_talk('vn_gisli', "Tell Gisli", "The barrow-dead will open the door. The hagbui and the jotun - they're both waiting for Hati and the winter. Hrafnsholm is the door.\n\nSteinunn needs to hear this.", 'default'),
        ],
        {'default': {'text': H, 'choice': [o3, o4, o5]}}, requires='vn_orm_runners', group=True)

# ======================================================================== The Spider Wood (43-45)
s1 = z.item("Spider-Silk Mantle", 'cloak', 43, 'ward', "Grey silk, very strong.")
s2 = z.item("Rune-Thread Ring", 'ring', 43, 'mind', "Spider-silk wound round a rune-stone.")
z.quest('vn_spiders', 'Silk for the Runes', 43, 'gunnvor',
        "To break the hagbui's runes I need rune-thread - forest spider silk, the strongest in Midgard. The spiders won't give it gladly.\n\nWill you [gather silk]?",
        'gather silk',
        "Gunnvor needs forest spider silk from Vanern's north-east to break the hagbui's runes.",
        [
            hunt((1350, 400), "Gather silk from the forest spiders " + where((1350, 400), 'gunnvor'), 'forest spider', 5),
            end_talk('gunnvor', "Bring the silk to Gunnvor", "Good silk. I'll spin rune-thread from it - enough to bind the dead back into their barrows, if it comes to it.", 'default'),
        ],
        {'default': {'text': V, 'choice': [s1, s2]}}, requires='vn_crippled')

# ======================================================================== Hrafnsholm (41-46)
h1 = z.item("Barrow-Breaker's Ring", 'ring', 41, 'faith', "Silver, against the dead.")
h2 = z.item("Berserker-Bane Belt", 'belt', 41, 'might', "Heavy leather, iron-studded.")
z.quest('vn_berserkers', 'The Hagbui Berserkers', 41, 'vn_steinunn',
        "The hagbui berserkers roam the ground below Hrafnsholm - dead men who fight like they want to die again. Every one we break is one less on the walls.\n\nWill you [break the berserkers]?",
        'break the berserkers',
        "Hagbui berserkers roam the ground below Hrafnsholm, the Wardens' lost watch-hold.",
        [
            hunt((350, 500), "Break the hagbui berserkers " + where((350, 500), 'vn_steinunn'), 'hagbui berserker', 5),
            end_talk('vn_steinunn', "Tell Steinunn", "Good. Every one tells the Wardens we can take the hold back.", 'default'),
        ],
        {'default': {'text': V, 'choice': [h1, h2]}}, requires='vn_vipers')

h3 = z.item("Spiritmaster's Bone Charm", 'gem', 43, 'mind', "A finger-bone, wound with rune-thread.")
h4 = z.item("Barrow-Ward Bracer", 'bracer', 43, 'faith', "Rowan and silver, against the dead.")
z.quest('vn_spiritmasters', 'The Spiritmasters', 43, 'gunnvor',
        "The hagbui spiritmasters raise the dead of the barrows. While they stand, every hagbui we break gets up again.\n\nWill you [break the spiritmasters]?",
        'break the spiritmasters',
        "Hagbui spiritmasters raise the dead of Vanern's barrows.",
        [
            hunt((250, 480), "Break the hagbui spiritmasters " + where((250, 480), 'gunnvor'), 'hagbui spiritmaster', 3),
            hunt((300, 450), "Break the hagbui shamans", 'hagbui shaman', 2),
            end_talk('gunnvor', "Tell Gunnvor", "The dead will stay down now. Mostly.", 'default'),
        ],
        {'default': {'text': V, 'choice': [h3, h4]}}, requires='vn_berserkers')

h5 = z.item("Runemaster's Black Torc", 'neck', 46, 'mind', "Black iron, cold, carved with barrow-runes - now broken.")
h6 = z.item("Hrafnsholm Warden's Mantle", 'cloak', 46, 'ward', "The Wardens' raven, black on grey.")
h7 = z.item("Thane-Breaker's Ring", 'ring', 46, 'might', "A hagbui thane's ring, the runes ground off.")
z.quest('vn_runemasters', 'The Runemasters', 46, 'vn_steinunn',
        "The hagbui runemasters keep the jotun's chains in Hrafnsholm's yard, and the thanes guard them. Break them, and the dead lose their slave.\n\nBring friends. Will you [break the runemasters]?",
        'break the runemasters',
        "Hagbui runemasters and thanes keep the chained jotun in Hrafnsholm's yard.",
        [
            hunt((240, 250), "Break the hagbui runemasters " + where((240, 250), 'vn_steinunn'), 'hagbui runemaster', 2, r=50),
            hunt((240, 250), "Break the hagbui thanes", 'hagbui thane', 2, r=50),
            end_talk('vn_steinunn', "Tell Steinunn", "Broken. The chains will be weaker. When we take the hold, Gunnvor can free the jotun - or the hagbui will turn him on us.", 'default'),
        ],
        {'default': {'text': V, 'choice': [h5, h6, h7]}}, requires='vn_spiritmasters', group=True)

h8 = z.item("Watch-Hold Scout's Ring", 'ring', 45, 'finesse', "Bog-iron, the Wardens' raven.")
h9 = z.item("Wardens' Oath-Belt", 'belt', 45, 'ward', "The Wardens' belt, given to those who stand with them.")
z.quest('vn_hrafnsholm', 'Hrafnsholm', 45, 'vn_steinunn',
        "Hrafnsholm. Our hold, three hundred years. Go and look at it - count the dead on the walls, find the gate. Then come back and tell me we can take it back.\n\nWill you [scout the hold]?",
        'scout the hold',
        "The Wardens of Vanern mean to take back Hrafnsholm, their watch-hold, from the hagbui.",
        [
            reach(Z, P(420, 160), "Climb to the ridge above Hrafnsholm", "The old watch-hold, its timbers black with frost in summer. Dead men on the walls, unmoving. In the yard, a jotun in chains, hammering at a forge - and the forge-fire is blue and cold.", r=25),
            search(Z, P(400, 180), "Look over the hold's gate", "the Wardens' old banner, torn", CRATE,
                   "The Wardens' raven banner, torn and nailed upside down. Under it, carved in ice: 'WE OPEN THE DOOR FOR THE WINTER. HATI COMES.'"),
            end_talk('vn_steinunn', "Tell Steinunn", "They nailed our banner upside down. Then we take it back for every Warden who held it.\n\nThe Wardens will march when the swamp is behind us - every berserker, every spiritmaster, every runemaster broken tells them they can win. Be there.", 'default'),
        ],
        {'default': {'text': V, 'choice': [h8, h9]}}, requires='vn_berserkers')
