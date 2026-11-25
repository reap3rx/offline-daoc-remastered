"""Raumarik's story quests (claude 2026-11-25, "Midgard - the plan", round 4) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_raumarik

Elite. The west thread's end: Hati, the wolf that hunts the moon, waits in his howe in the west; his host - the fenrir soldiers, the
winterwolves, the wraiths and wights of the endless winter - holds the north. The trappers' camp is the only warm place in it,
and the King's Host musters there for the King's March (AlbionCampaign.cs / MidgardCampaigns.cs): these quests walk the north
ahead of it and end at Huscarl-Marshal Hallvard.

The zone's two older quests are kept as they were (red_dagger, grani).

Arcs (recommended levels): The Fells (45-47), The Wraith Moor (47-50), The Winterwolf Run (49-51), The Fenrir Camp (51-54).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(108, 'Raumarik', 'mid_raumarik', 'story108_raumarik', {'red_dagger', 'grani'},
          {'einar_trapper', 'sigrid', 'hroald', 'hroald_plain'},
          {'Red Dagger Ring', "Trapper's Snow-Cloak", 'Bounty-Notice Charm', "Bloodnail's Belt", "Grani's Mane-Braid",
           'Fenrir Blood-Bowl Torc', "Breeder's Saddle-Belt", 'Eight-Hoof Ring', "Jarl's Rein-Bracer"}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157

person('rk_steinar', 'Huscarl Steinar', (1120, 890), 'm', 52, model=M, guild="King Eirik's Host",
       idle="The King's Host is coming north. Every one of us who got here first is a scout now.")
person('rk_ylva', 'Seithkona Ylva', (1090, 915), 'f', 50, model=F, guild='the Seithkona Circle',
       idle="Saga sent me north from the Circle to watch the moon from closer. It's closer than I'd like.")

K, C = "From King Eirik's Host.", "From the Seithkona Circle."

# ======================================================================== The Fells (45-47)
f1 = z.item("Icestrider-Shell Bracer", 'bracer', 45, 'ward', "Pale shell, cold as the fells.")
f2 = z.item("Fell-Walker's Ring", 'ring', 45, 'finesse', "Frost-blue iron.")
z.quest('rk_chillers', 'The Icestrider Fells', 45, 'rk_steinar',
        "The icestriders on the north-east fells never troubled anyone. Now they hunt in packs, and Hati's soldiers walk behind them like herdsmen.\n\nWill you [thin them]?",
        'thin them',
        "Icestrider chillers hunt in packs on Raumarik's north-east fells, herded by Hati's soldiers.",
        [
            hunt((1350, 400), "Thin the icestrider chillers " + where((1350, 400), 'rk_steinar'), 'icestrider chiller', 6),
            end_talk('rk_steinar', "Tell Huscarl Steinar", "Thinner. The fells are the first post the March will take. Anything you kill now is one less on the day.", 'default'),
        ],
        {'default': {'text': K, 'choice': [f1, f2]}})

f3 = z.item("Frostweaver's Silk Mantle", 'cloak', 47, 'ward', "Woven ice that never melts.")
f4 = z.item("Winter-Wolf Fang Torc", 'neck', 47, 'might', "A winter wolf's fang on a frozen chain.")
z.quest('rk_frostweavers', 'The Frostweavers', 47, 'rk_steinar',
        "The frostweavers spin ice over the fell paths, and the winter wolves run on it. Break them, and the March will have a road.\n\nWill you [break the frostweavers]?",
        'break the frostweavers',
        "Icestrider frostweavers spin ice over Raumarik's fell paths for the winter wolves.",
        [
            hunt((1300, 520), "Break the icestrider frostweavers " + where((1300, 520), 'rk_steinar'), 'icestrider frostweaver', 4),
            hunt((1250, 590), "Kill the winter wolves", 'winter wolf', 3),
            end_talk('rk_steinar', "Tell Steinar", "A road. Good. Now - the moor, where the dead walk. Ylva will tell you about the moor.", 'default'),
        ],
        {'default': {'text': K, 'choice': [f3, f4]}}, requires='rk_chillers')

# ======================================================================== The Wraith Moor (47-50)
w1 = z.item("Wraith-Shroud Charm", 'gem', 47, 'mind', "A scrap of something that was never cloth.")
w2 = z.item("Moor-Ward Bracer", 'bracer', 47, 'faith', "Silver runes on black iron.")
z.quest('rk_wraiths', 'The Wraith Moor', 47, 'rk_ylva',
        "The windswept wraiths on the moor were men once - men who froze in the first winter. They walk again because Hati calls the winter back.\n\nWill you [lay them down]?",
        'lay them down',
        "The windswept wraiths of Raumarik's moor walk again as Hati calls the winter back.",
        [
            hunt((850, 600), "Lay down the windswept wraiths " + where((850, 600), 'rk_ylva'), 'windswept wraith', 5),
            end_talk('rk_ylva', "Tell Seithkona Ylva", "Down. For a while. Something on the moor keeps them walking.", 'default'),
        ],
        {'default': {'text': C, 'choice': [w1, w2]}}, requires='rk_chillers')

w3 = z.item("Frost-Stone Shard Ring", 'ring', 49, 'mind', "A chip of a frost-stone, faintly humming.")
w4 = z.item("Wight-Bane Belt", 'belt', 49, 'faith', "Rowan and silver.")
w5 = z.item("Moon-Watcher's Mantle", 'cloak', 49, 'ward', "Grey wool, a moon stitched in silver.")
z.quest('rk_wights', 'The Frost-Stones', 49, 'rk_ylva',
        "The chillsome wights guard stones on the moor - frost-stones, Hati's own. They keep the dead walking, and the frore lich keeps the stones.\n\nBring friends. Will you [find the stones]?",
        'find the stones',
        "Chillsome wights and a frore lich guard Hati's frost-stones on Raumarik's moor.",
        [
            hunt((900, 720), "Break the chillsome wights " + where((900, 720), 'rk_ylva'), 'chillsome wight', 4),
            hunt((850, 650), "Break the frore lich", 'frore lich', 1, r=60),
            search(Z, P(855, 660), "Search the frost-stone", "a waist-high stone, rimed white", LANTERN,
                   "Carved in the stone: the moon, in every phase, and behind it a wolf, closer each time. The last carving is fresh: the wolf's jaws closing on a full moon. Under it: 'SOON.'"),
            end_talk('rk_ylva', "Tell Ylva", "Soon. The moon's running closer to him every night. When the King's Host comes, it can't come a night too late.", 'default'),
        ],
        {'default': {'text': C, 'choice': [w3, w4, w5]}}, requires='rk_wraiths', group=True)

# ======================================================================== The Winterwolf Run (49-51)
r1 = z.item("Winterwolf-Hide Bracer", 'bracer', 49, 'ward', "White hide, very warm.")
r2 = z.item("Pack-Breaker's Ring", 'ring', 49, 'might', "Iron, with a wolf's head struck through.")
z.quest('rk_winterwolves', 'The Winterwolf Run', 49, 'einar_trapper',
        "The savage winterwolves run south-west of here, in packs of twenty. I've trapped wolves forty years. These don't take bait. They take trappers.\n\nWill you [thin the packs]?",
        'thin the packs',
        "Savage winterwolves run in great packs on Raumarik's Winterwolf Run.",
        [
            hunt((650, 1000), "Thin the savage winterwolves " + where((650, 1000), 'einar_trapper'), 'savage winterwolf', 6),
            end_talk('einar_trapper', "Tell Einar the Trapper", "Fewer. They run for Hati. There's a Huntsman with them - a winterwolf as big as a horse, that runs the packs for him. Don't go near it without the King's Host.", 'default'),
        ],
        {'default': {'text': K, 'choice': [r1, r2]}}, requires='rk_frostweavers')

r3 = z.item("Frost-Bear Claw Torc", 'neck', 50, 'might', "Three claws, rimed with frost.")
r4 = z.item("Trapper's Fur Mantle", 'cloak', 50, 'ward', "Einar's own work, bear fur and wolf fur.")
z.quest('rk_bears', 'Frost-Bound', 50, 'sigrid',
        "The frost bound bears in the wood south of camp - the cold's in their blood now, and they don't sleep. They come at the camp at night.\n\nWill you [drive them off]?",
        'drive them off',
        "Frost bound bears from the wood south of the trappers' camp come at it in the night.",
        [
            hunt((1050, 1100), "Drive off the frost bound bears " + where((1050, 1100), 'sigrid'), 'frost bound bear', 5),
            end_talk('sigrid', "Tell Sigrid", "Quiet nights, for a while. Thank you.", 'default'),
        ],
        {'default': {'text': K, 'choice': [r3, r4]}})

# ======================================================================== The Fenrir Camp (51-54)
c1 = z.item("Fenrir-Soldier's Ring", 'ring', 51, 'might', "Black iron, a wolf's head.")
c2 = z.item("Camp-Breaker's Belt", 'belt', 51, 'ward', "Heavy, scarred leather.")
z.quest('rk_soldiers', "Hati's Soldiers", 51, 'rk_steinar',
        "The Fenrir Camp in the west - Hati's soldiers, the fenrir, half wolf and half man. They're the last thing between the March and the howe.\n\nWill you [thin the soldiers]?",
        'thin the soldiers',
        "Fenrir soldiers hold the Fenrir Camp in Raumarik's west, the last thing before Hati's Howe.",
        [
            hunt((400, 700), "Thin the fenrir soldiers " + where((400, 700), 'rk_steinar'), 'fenrir soldier', 6),
            end_talk('rk_steinar', "Tell Steinar", "Thinner. The mystics in the camp are what holds it together. They speak for Hati.", 'default'),
        ],
        {'default': {'text': K, 'choice': [c1, c2]}}, requires='rk_winterwolves')

c3 = z.item("Mystic's Moon-Bowl Charm", 'gem', 53, 'mind', "A bowl of black stone. A moon floats in it, even in daylight.")
c4 = z.item("Howe-Watcher's Bracer", 'bracer', 53, 'faith', "Silver and bone, carved with the moon.")
c5 = z.item("King's Scout Mantle", 'cloak', 53, 'ward', "The King's blue under white fur.")
z.quest('rk_mystics', 'The Mystics', 53, 'rk_ylva',
        "The fenrir mystics read the moon for Hati - when she'll run closest, when he can catch her. Break them, and bring me what they read.\n\nBring friends. Will you [break the mystics]?",
        'break the mystics',
        "Fenrir mystics read the moon's road for Hati in the Fenrir Camp.",
        [
            hunt((450, 800), "Break the fenrir mystics " + where((450, 800), 'rk_ylva'), 'fenrir mystic', 3, r=60),
            search(Z, P(455, 805), "Search the mystics' fire", "a bowl of black stone", LANTERN,
                   "In the bowl, the moon - and Hati's jaws, a hand's breadth from her. Scratched on the rim: 'THREE NIGHTS.'"),
            end_talk('rk_ylva', "Tell Ylva", "Three nights. The King's Host can't wait for the King. Go to Steinar - now.", 'default'),
        ],
        {'default': {'text': C, 'choice': [c3, c4, c5]}}, requires='rk_soldiers', group=True)

c6 = z.item("Marshal's Oath-Ring", 'ring', 54, 'ward', "The King's March's oath, in silver.")
c7 = z.item("Howe-Road Belt", 'belt', 54, 'might', "Huscarl's leather, the King's hammer on the buckle.")
z.quest('rk_kings_march', "The King's March", 54, 'rk_steinar',
        "Three nights. Then we march now. Look at the howe from the ridge - see what's waiting - then go to Huscarl-Marshal Hallvard at the camp and give him the word.\n\nWill you [look at the howe]?",
        'look at the howe',
        "King Eirik's Host must march on Hati's Howe within three nights.",
        [
            reach(Z, P(400, 560), "Climb to the ridge above Hati's Howe", "A barrow the size of a hill, snow streaming off it. Wolves sleep in rings round it. And in the mouth of the howe, two eyes, watching the moon.", r=25),
            end_talk('rk_steinar', "Tell Steinar", "Two eyes, watching the moon. Then it's time.\n\nGo to Huscarl-Marshal Hallvard and say the word - [for the King]. The fells, the moor, the run, the camp, then the howe. It all goes back if we stop.", 'default'),
        ],
        {'default': {'text': K, 'choice': [c6, c7]}}, requires='rk_mystics')
