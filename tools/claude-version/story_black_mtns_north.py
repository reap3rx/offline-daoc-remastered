"""Black Mountains North's story quests (claude 2026-11-24, "Albion - the plan", round 3) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_black_mtns_north

The north thread's stronghold. The Crimson hold Dinas Emrys, the hill fort in the west where Vortigern's tower kept falling until
the boy Merlin Emrys showed the king why: two dragons, red and white, fighting in a pool beneath it. The white was beaten and fled
south - Golestandt. Morgana's people have dug the pit open again, because the dragons came up out of Annwn, and the way they came
is a door. The hill-tribes march under red cords, smugglers run Badon's bones up the Red Road, and the bard Taliesin, who keeps
Merlin's prophecies, wants the fort back before the door opens. At the end: "the gate of Annwn at Llyn Barfog, where Arthur slew
the Afanc".

The zone's two older quests are kept as they were (last_shift, crimson_bargain).

Arcs (recommended levels): The Slopes (16-19), The Red Road (18-22), The Bard's Errands (18-26), The Red-Corded Tribes (23-25),
Dinas Emrys (27-30).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk
from albion_story import Story, CRATE, BEDROLL, LANTERN, M, F, OLD

S = Story(3, 'Black Mountains North', 'alb_black_mtns_north', 'story003_black_mtns_north', {'last_shift', 'crimson_bargain'},
          {'tomas_fell', 'mabli', 'hrodda', 'captain_mardoc', 'hrodda_camp'},
          {"Mabli's Salt-Pouch", "Miner's Lamp-Ring", 'Cockatrice-Shell Bracer', "Foreman's Belt", "Hill-Chief's Torque", 'Crimson-Thread Cloak',
           "Hrodda's Bone Bracer", "Bounty-Hunter's Belt"})
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]

person('bn_rhydderch', 'Castellan Rhydderch', (700, 332), 'm', 44, model=28, guild='the Snowdonia Garrison',
       idle="Swanton holds the north road. Dinas Emrys holds the west. One of those is ours.")
person('bn_taliesin', 'Taliesin the Bard', (998, 1018), 'm', 50, guild='the Emrys Circle',
       idle="I sang at Arthur's court. I'll sing at his waking, if I live. That's what bards are for.")

# ======================================================================== The Slopes (16-19)
a1 = z.item("Warg-Pelt Bracer", 'bracer', 16, 'ward', "Grey and coarse. Warm in the wind off the crags.")
a2 = z.item("Garrison Picket Ring", 'ring', 16, 'might', "Every picket on the west road wears one.")
z.quest('bn_wargs', 'Wargs on the West Road', 16, 'bn_rhydderch',
        "Grey wargs on the west road - more of them every week, and bolder. They run down my pickets in pairs.\n\nWill you [thin the wargs]?",
        'thin the wargs',
        "Grey wargs are running down the garrison's pickets on the west road.",
        [
            hunt((400, 850), "Thin the gray wargs on the west road " + where((400, 850), 'bn_rhydderch'), 'gray warg', 6),
            end_talk('bn_rhydderch', "Tell Castellan Rhydderch", "Good. The wargs used to keep to the high crags. Something's driven them down. Something in the west.", 'default'),
        ],
        {'default': {'text': "From the Snowdonia Garrison.", 'choice': [a1, a2]}})

a3 = z.item("Cockatrice-Quill Charm", 'gem', 17, 'mind', "A stiff red quill. Don't look at it too long.")
a4 = z.item("Mine-Hill Belt", 'belt', 17, 'ward', "Tomas's own. He says he's done with the hills.")
z.quest('bn_beaked_brood', 'The Beaked Brood', 17, 'tomas_fell',
        "Enraged cockatrices all over the mine hills, and a big cock-bird called Trimbeak who leads them. They turn a man's blood to stone with a look.\n\nWill you [break the brood]?",
        'break the brood',
        "Enraged cockatrices led by Trimbeak hold the old mine hills.",
        [
            hunt((550, 550), "Kill the enraged cockatrices " + where((550, 550), 'tomas_fell'), 'enraged cockatrice', 5),
            hunt((649, 628), "Kill Trimbeak", 'Trimbeak', 1),
            end_talk('tomas_fell', "Tell Tomas Fell", "Trimbeak, dead. His three brothers will want words with you. Glim, Slim and Grim, the miners call them.", 'default'),
        ],
        {'default': {'text': "From Tomas Fell.", 'choice': [a3, a4]}})

a5 = z.item("Three-Beak Torc", 'neck', 19, 'might', "Three beaks, gilded, on a bronze torc.")
a6 = z.item("Stone-Gaze Bracer", 'bracer', 19, 'ward', "Its owner never once turned to stone.")
a7 = z.item("Brood-Breaker's Cloak", 'cloak', 19, 'finesse', "Red feathers stitched in a pattern only the miners understand.")
z.quest('bn_three_beaks', 'Glimbeak, Slimbeak and Grimbeak', 19, 'tomas_fell',
        "Trimbeak's three brothers roost on the beak rocks north of the mine. While they live, the brood comes back.\n\nWill you [finish the brothers]? Bring friends who don't mind being stared at.",
        'finish the brothers',
        "Trimbeak's three brothers roost on the beak rocks north of the old mine.",
        [
            hunt((859, 455), "Kill Glimbeak " + where((859, 455), 'tomas_fell'), 'Glimbeak', 1),
            hunt((861, 365), "Kill Slimbeak", 'Slimbeak', 1),
            hunt((860, 452), "Kill Grimbeak", 'Grimbeak', 1),
            end_talk('tomas_fell', "Tell Tomas Fell", "All three. The hills are yours, friend. The miners will go back in the spring.", 'default'),
        ],
        {'default': {'text': "From Tomas Fell.", 'choice': [a5, a6, a7]}},
        requires='bn_beaked_brood', group=True)

# ======================================================================== The Red Road (18-22)
r1 = z.item("Smuggler's Hidden-Pocket Belt", 'belt', 18, 'finesse', "Seven hidden pockets. You've found five.")
r2 = z.item("Red-Road Ring", 'ring', 18, 'might', "A plain iron ring, worn by the garrison on the Red Road.")
z.quest('bn_red_road', 'The Red Road', 18, 'captain_mardoc',
        "The forest road from Snowdonia Station to the west - the smugglers call it the Red Road, for the cords. They run carts up it at night, west to the hill fort.\n\nWill you [stop a cart]? I want to know what's in them.",
        'stop a cart',
        "Smugglers run carts west along the forest road at night.",
        [
            hunt((900, 700), "Fight through the forest smugglers " + where((900, 700), 'captain_mardoc'), 'forest smuggler', 5),
            search(Z, P(880, 690), "Search a smugglers' cart", "a cart under a tarpaulin", CRATE,
                   "Sacks of bones - big, old, wrapped in rotted mail - and a tally: 'Badon, by the Bishop's leave. To Dinas Emrys, for the pit.'"),
            end_talk('captain_mardoc', "Tell Captain Mardoc", "Badon's bones. The Abbey in the south was sending them north - and they're still coming, Bishop or no Bishop.\n\nTo Dinas Emrys. What does a pit want with Arthur's dead?", 'default'),
        ],
        {'default': {'text': "From the Snowdonia Garrison.", 'choice': [r1, r2]}})

r3 = z.item("Tracker's Leaf-Cloak", 'cloak', 20, 'finesse', "Green and brown, sewn with real leaves that never wither.")
r4 = z.item("Snare-Wire Ring", 'ring', 20, 'finesse', "Twisted from a tracker's snare.")
z.quest('bn_trackers', 'Trackers in the Trees', 20, 'captain_mardoc',
        "The smugglers have trackers - woodsmen who know every path - and they've been picking off my patrols from the trees.\n\nWill you [hunt the hunters]?",
        'hunt the hunters',
        "The smugglers' trackers are picking off the garrison's patrols from the trees.",
        [
            hunt((1020, 757), "Hunt the forest trackers " + where((1020, 757), 'captain_mardoc'), 'forest tracker', 5),
            end_talk('captain_mardoc', "Tell Captain Mardoc", "My patrols can walk the road again. Now for the one who sends them.", 'default'),
        ],
        {'default': {'text': "From the Snowdonia Garrison.", 'choice': [r3, r4]}},
        requires='bn_red_road')

r5 = z.item("Forest Chief's Antler Torc", 'neck', 22, 'might', "Antler and bronze. He wore it like a crown.")
r6 = z.item("Ledger-Lock Charm", 'gem', 22, 'mind', "The lock off the chief's ledger. The key's gone.")
r7 = z.item("Red Road Breaker's Mantle", 'cloak', 22, 'ward', "Garrison grey. Mardoc's gift.")
z.quest('bn_forest_chief', 'The Forest Chief', 22, 'captain_mardoc',
        "The smugglers' master calls himself the Forest Chief. His den's in the north woods. Kill him and the Red Road closes.\n\nWill you [close the road]? Bring friends.",
        'close the road',
        "The Forest Chief runs the smugglers of the Red Road from his den in the north woods.",
        [
            hunt((904, 570), "Defeat the Forest Chief " + where((904, 570), 'captain_mardoc'), 'forest chief', 1),
            search(Z, P(906, 575), "Search the Forest Chief's den", "a ledger in a locked box", CRATE,
                   "'Delivered to the Pit-Warden at Dinas Emrys: bones of Badon, forty sacks; hill-tribe tithe, paid in red cord. The Lady wants the pit open by the turning of the year.'"),
            end_talk('captain_mardoc', "Bring the ledger to Captain Mardoc", "The Pit-Warden. The Lady. By the turning of the year.\n\nThe Castellan has to see this. And the bard.", 'default'),
        ],
        {'default': {'text': "From the Snowdonia Garrison.", 'choice': [r5, r6, r7]}},
        requires='bn_trackers', group=True)

# ======================================================================== The Bard's Errands (18-26)
b1 = z.item("Prophecy-Stone Ring", 'ring', 18, 'mind', "A pebble scratched with ogham. Taliesin read it aloud once and wouldn't again.")
b2 = z.item("Bard's Satchel-Strap", 'belt', 18, 'charm', "Taliesin's spare. It's carried a hundred songs.")
z.quest('bn_prophets_graves', "The Prophet's Graves", 18, 'bn_taliesin',
        "The druids in the old graves south of the hill country were Merlin's own students. They were buried with stones carved with his prophecies. Now they walk, and the stones are being taken.\n\nWill you [visit the graves]?",
        'visit the graves',
        "Merlin's students walk from their graves, and their prophecy-stones are being taken.",
        [
            hunt((495, 1017), "Lay the undead druids to rest " + where((495, 1017), 'bn_taliesin'), 'undead druid', 5),
            search(Z, P(498, 1020), "Search the graves for prophecy-stones", "a grave with its stone pulled up", CRATE,
                   "One stone left, missed by whoever took the others. Ogham: 'Under Emrys's fort the red and the white; under them, the door they came by.'"),
            end_talk('bn_taliesin', "Bring the stone to Taliesin", "'The door they came by.' The dragons came up out of Annwn, child. Everyone forgot that part of the story. Morgana didn't.", 'default'),
        ],
        {'default': {'text': "From the Emrys Circle.", 'choice': [b1, b2]}})

b3 = z.item("Unknotted Cord", 'belt', 21, 'faith', "A red cord with every knot burned out of it.")
b4 = z.item("South Woods Bracer", 'bracer', 21, 'ward', "Mossy leather. Smells of the south woods.")
z.quest('bn_red_cords_south', 'Red Cords in the South Woods', 21, 'bn_taliesin',
        "Filidh in the south woods have taken the red cord - sacrificers, feeding the pit from a distance with what they bleed. Every song I know says that's how you wake a door.\n\nWill you [stop the bleeding]?",
        'stop the bleeding',
        "Red-corded filidh sacrificers in the south woods feed the pit at Dinas Emrys.",
        [
            hunt((968, 1393), "Kill the filidh sacrificers " + where((968, 1393), 'bn_taliesin'), 'filidh sacrificer', 5),
            end_talk('bn_taliesin', "Tell Taliesin", "Good. Every drop they don't spill is a day the door stays shut.", 'default'),
        ],
        {'default': {'text': "From the Emrys Circle.", 'choice': [b3, b4]}})

b5 = z.item("Warm Green Cloak", 'cloak', 25, 'charm', "Green wool, lined. The Cauld Lad wore it for a moment and was warm.")
b6 = z.item("Brownie's Hob-Nail Ring", 'ring', 25, 'finesse', "A hob-nail bent into a ring.")
b7 = z.item("Lullaby Charm", 'gem', 25, 'mind', "Taliesin's lullaby, written very small on a scrap of vellum.")
z.quest('bn_cauld_lad', 'The Cauld Lad', 25, 'bn_taliesin',
        "There's a ghost in the woods by the Station - the Cauld Lad, they call him, a brownie-lad who died of cold a hundred years ago. He's always been harmless. This year he's frozen two travellers solid.\n\nThe old songs say you lay a brownie with a gift of clothes. Will you [lay the Cauld Lad]? You may have to make him hold still first.",
        'lay the Cauld Lad',
        "The Cauld Lad, a brownie ghost near Snowdonia Station, has started freezing travellers.",
        [
            search(Z, P(1010, 1000), "Take a green cloak from the Station's stores " + where((1010, 1000), 'bn_taliesin'), "a chest of spare clothes", CRATE,
                   "A good green cloak, lined with wool. Warm.", give="a warm green cloak"),
            hunt((1125, 948), "Make the Cauld Lad hold still", 'Cauld Lad', 1,
                 text="The Cauld Lad stops. You put the cloak round him. 'Wee lad, wee lad,' he whispers, 'and no more work for me' - and he's gone."),
            end_talk('bn_taliesin', "Tell Taliesin", "Gone, and warm. That's a better end than most get.\n\nSomething in the west woke the cold in him. Everything comes back to that fort.", 'default'),
        ],
        {'default': {'text': "From the Emrys Circle.", 'choice': [b5, b6, b7]}}, group=True)

b8 = z.item("Necromancer's Bone-Clasp", 'gem', 26, 'mind', "A finger-bone clasp. It twitches.")
b9 = z.item("Cairn-Stone Bracer", 'bracer', 26, 'ward', "Set with a stone from the necromancers' cairn.")
b10 = z.item("Letter-Seal Ring", 'ring', 26, 'faith', "Morgana's seal, struck through with a knife.")
z.quest('bn_necromancers', "The Necromancers' Cairn", 26, 'bn_taliesin',
        "Two necromancers keep a cairn in the far south-west - not Arawn's men, Morgana's. They write to the Pit-Warden. If anyone knows what's under the fort, they do.\n\nWill you [break the cairn]? Bring friends.",
        'break the cairn',
        "Two of Morgana's necromancers keep a cairn in the far south-west.",
        [
            hunt((290, 1234), "Kill the necromancers at the cairn " + where((290, 1234), 'bn_taliesin'), 'necromancer', 2),
            search(Z, P(292, 1230), "Search the necromancers' cairn", "a letter weighted with a stone", CRATE,
                   "'Pit-Warden - the pit under Emrys's fort is only the near end. The far end is the gate in the lake at Llyn Barfog, where Arthur slew the Afanc. Open the near end and the far end follows. M.'",
                   give="the necromancers' letter"),
            end_talk('bn_taliesin', "Bring the letter to Taliesin", "Llyn Barfog. Her own lake, where she sits. The near end and the far end.\n\nThe fort has to be taken back. Tell the Castellan.", 'default'),
        ],
        {'default': {'text': "From the Emrys Circle.", 'choice': [b8, b9, b10]}},
        requires='bn_red_cords_south', group=True)

b11 = z.item("Howling Maiden's Veil", 'cloak', 24, 'faith', "Grey gauze. It sings faintly in the wind.")
b12 = z.item("Crag-Walker's Torc", 'neck', 24, 'might', "Silver, cold as the crags.")
z.quest('bn_howling_maidens', 'The Howling Maidens', 24, 'bn_rhydderch',
        "On the crags above Swanton, the howling maidens keen every night. They used to keen for the dead. Now they keen for whoever walks the crags - and they come down to make sure.\n\nWill you [quiet the crags]? Bring friends.",
        'quiet the crags',
        "The howling maidens on the crags above Swanton Keep have started coming down for the living.",
        [
            hunt((827, 294), "Quiet the howling maidens " + where((827, 294), 'bn_rhydderch'), 'howling maiden', 3),
            end_talk('bn_rhydderch', "Tell Castellan Rhydderch", "Quiet. First quiet night on the crags this year. Thank you.", 'default'),
        ],
        {'default': {'text': "From the Snowdonia Garrison.", 'choice': [b11, b12]}}, group=True)

# ======================================================================== The Red-Corded Tribes (23-25)
h1 = z.item("Cut Red Cord", 'belt', 23, 'might', "A tribesman's cord, cut through. He thanked you for it.")
h2 = z.item("Hill-Shaman's Rattle-Charm", 'gem', 23, 'mind', "Seeds in a gourd. It rattles a warning.")
z.quest('bn_red_tribes', 'The Red-Corded Tribes', 23, 'hrodda',
        "The tribes march under red cords now - all of them, my father's warriors too. The shamans tie the cords and say the words.\n\nKill the shamans and the cords loosen. Will you [cut the cords]?",
        'cut the cords',
        "The hill-tribes march under red cords tied by their shamans.",
        [
            hunt((200, 700), "Fight through the red-corded hill warriors " + where((200, 700), 'hrodda'), 'hill warrior', 5),
            hunt((134, 605), "Kill the hill shamans who tie the cords", 'hill shaman', 2),
            end_talk('hrodda', "Tell Hrodda", "Some of them have taken the cords off already. I saw my cousin weep. Now - my father.", 'default'),
        ],
        {'default': {'text': "From Hrodda.", 'choice': [h1, h2]}},
        requires='crimson_bargain')

h3 = z.item("Alrek's Chief-Ring", 'ring', 25, 'might', "Gold, heavy, very old. The chiefs of the hills have worn it for twenty generations.")
h4 = z.item("Hill-Daughter's Mantle", 'cloak', 25, 'ward', "Woven by Hrodda herself, red cord unpicked from the hem.")
h5 = z.item("Freed Chief's Torc", 'neck', 25, 'faith', "Alrek gave it you, or Hrodda did. Either way it's yours.")
z.quest('bn_hill_chief', 'Hill Chief Alrek', 25, 'hrodda',
        "My father stands on the hill by the fort with the red cord round his throat. The Crimson tied it themselves. He doesn't know me.\n\nBeat him down - don't kill him if you can help it - and I'll come up behind you and cut it. Will you [face my father]? Bring friends. He was the best fighter in the hills.",
        'face my father',
        "Hill Chief Alrek stands by Dinas Emrys bound by a red cord the Crimson tied themselves.",
        [
            hunt((143, 361), "Beat Hill Chief Alrek down " + where((143, 361), 'hrodda'), 'Hill Chief Alrek', 1,
                 text="Alrek falls to his knees. Hrodda runs in with her knife and cuts the cord at his throat."),
            choice('hrodda', "Speak with Hrodda at Snowdonia Station", "He's breathing. He knows me. He's - crying, I think.\n\nI can [take him home], to the high hills, and the tribes will follow him away from this place. Or he can [stand with the garrison] when they come for the fort - he knows every stone of it.",
                   [('take him home', "Home, then. The tribes go with us. That's a hundred spears the Crimson won't have.", 'ending:home'),
                    ('stand with the garrison', "Then the Alrek of the hills fights for Albion again. The Castellan will want to hear it.", 'ending:fight')]),
        ],
        {'home': {'text': "From Hrodda and her father.", 'items': [h4], 'choice': [h3, h5]},
         'fight': {'text': "From Hill Chief Alrek.", 'items': [h3], 'choice': [h4, h5]}},
        requires='bn_red_tribes', group=True)

# ======================================================================== Dinas Emrys (27-30)
d1 = z.item("Emrys Gate-Stone Ring", 'ring', 27, 'might', "A chip of the fort's gate, set in iron.")
d2 = z.item("Hill-Fort Bracer", 'bracer', 27, 'ward', "Garrison-made, for the assault on the fort.")
d3 = z.item("Dragon-Priest's Stole", 'cloak', 27, 'mind', "Red silk embroidered with a dragon, unpicked at the eyes.")
z.quest('bn_dinas_emrys', 'Dinas Emrys', 27, 'bn_rhydderch',
        "The bard's told me what's under that fort, and the smugglers' ledger tells me when. We can't take it alone - but we can bleed it, and when the garrison's ready, every red cord you've cut will count.\n\nWill you [break the gate]? Bring the strongest friends you have.",
        'break the gate',
        "The Crimson hold Dinas Emrys, the hill fort over the dragons' pit.",
        [
            hunt((230, 420), "Break the hill guards at the fort's gate " + where((230, 420), 'bn_rhydderch'), 'hill guard', 4),
            hunt((160, 360), "Cut down the crimson acolytes inside the walls", 'crimson acolyte', 4),
            search(Z, P(150, 350), "Look down into the pit", "the edge of a great pit", CRATE,
                   "The pit goes down further than the light. Red stone on one wall, white on the other - scales, as big as shields, fused into the rock. At the bottom, very far down, something glows."),
            end_talk('bn_rhydderch', "Tell Castellan Rhydderch", "Scales. Red and white. So the tale's true.\n\nThe garrison will take that fort, and soon. When we do, you'll be there.", 'default'),
        ],
        {'default': {'text': "From the Snowdonia Garrison.", 'choice': [d1, d2, d3]}},
        requires='bn_forest_chief', group=True)

d4 = z.item("Red Dragon Scale", 'gem', 30, 'might', "A scale from the red dragon of Vortigern's tower. Warm, always.")
d5 = z.item("White Dragon Scale", 'gem', 30, 'mind', "A scale from the white dragon - Golestandt's. It's cold enough to burn.")
d6 = z.item("Taliesin's Harp-String Ring", 'ring', 30, 'faith', "A harp-string wound into a ring. It hums when danger's near.")
d7 = z.item("Mantle of Emrys's Fort", 'cloak', 30, 'ward', "Grey and red, with the dragons. Given to those who closed the pit.")
z.quest('bn_dragons_pit', "The Dragons' Pit", 30, 'bn_taliesin',
        "The Pit-Warden stands at the edge of the pit, singing it open. When the door opens here, the far end opens at Llyn Barfog, and Annwn walks into Albion.\n\nI'll come with you. Bards don't fight, but they can sing a door shut. Will you [close the pit]? Bring everyone.",
        'close the pit',
        "The Pit-Warden sings the dragons' pit under Dinas Emrys open, a door to Annwn.",
        [
            reach(Z, P(150, 345), "Go to the edge of the dragons' pit " + where((150, 345), 'bn_taliesin'), "The singing comes up out of the pit like heat. The Pit-Warden turns.", r=25),
            hunt((130, 330), "Defeat the Pit-Warden of Dinas Emrys", 'the Pit-Warden of Dinas Emrys', 1,
                 text="The Pit-Warden falls. Taliesin's voice rises over the pit - and slowly, the glow at the bottom goes out."),
            choice('bn_taliesin', "Speak with Taliesin at the pit's edge", "It's shut. This end. The far end is in Morgana's own lake, and she'll have felt it close.\n\nTwo scales broke loose from the walls when the song took hold: one red, one white. Take [the red] - Albion's dragon - or [the white], to know your enemy. I'll keep the other.",
                   [('the red', "The red. Uther's dragon, and Arthur's. Wear it well.", 'ending:red'),
                    ('the white', "The white. Cold, isn't it? That's Golestandt. Remember the cold when you meet him.", 'ending:white')]),
        ],
        {'red': {'text': "From the dragons' pit.", 'items': [d4], 'choice': [d6, d7]},
         'white': {'text': "From the dragons' pit.", 'items': [d5], 'choice': [d6, d7]}},
        requires='bn_dinas_emrys', group=True,
        topics={'taliesin': "He smiles. 'I was Gwion once, and a grain of wheat, and a salmon, and a wren. Now I'm an old man with a harp. It's been a long life.'"})
