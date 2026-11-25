"""Muspelheim's story quests (claude 2026-11-25, "Midgard - the plan", round 3) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_muspelheim

Dangerous. The south thread's forge: Gjalpinulva's drakulv keep a hatchery in the wyrm hills, warming the dragon's fire-wyrm brood
for the day she wakes; renegade dverge in the south sell them fire-salt; the fire giants of the east hate the dragon's kin and burn
anything that comes near. The givers: the King's huscarls at Brika's camp (the way in from the Vale) and the dverge of Khizil's
forge in the south.

The zone's two older quests are kept as they were (dagnar, ragnvald).

Arcs (recommended levels): The Way In (19-21), The Ash Road (20-23), The Fire-Sellers (23-25), The Old Battlefield (22-25),
The Hatchery (25-28).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(104, 'Muspelheim', 'mid_muspelheim', 'story104_muspelheim', {'dagnar', 'ragnvald'},
          {'dagny', 'hrafnhild', 'dagnar', 'sven_ashbeard', 'ragnvald'},
          {"Dagnar's Journal-Clasp", 'Battered-Chest Belt', "Forgemaster's Bracer", 'Lodestone Ring', "Ragnvald's Lay-Harp Charm",
           'Ashbeard Ring', 'Fire-Giant Thane Belt', 'Cinder-Silk Cloak'}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157

person('mu_hallkel', 'Huscarl Hallkel', (1275, 145), 'm', 36, model=M, guild="King Eirik's Huscarls",
       idle="Muspelheim. The King sends us here when he's cross with us. Lately he sends us here because of the smoke.")
person('mu_thrain', 'Forge-Master Thrain', (578, 1322), 'm', 40, model=OLD, guild='the Forge of Khizil',
       idle="Every fire in Muspelheim is a dverge's business. Lately someone's selling ours.")

H, K = "From King Eirik's Huscarls.", "From the Forge of Khizil."

# ======================================================================== The Way In (19-21)
a1 = z.item("Ember-Ward Ring", 'ring', 19, 'ward', "Iron, blackened. It's cool to the touch, even here.")
a2 = z.item("Hound-Hide Belt", 'belt', 19, 'finesse', "Scorched hide, oddly supple.")
z.quest('mu_hounds', 'The Noxious Hounds', 19, 'mu_hallkel',
        "The noxious hounds come up to the camp every night - sulphur on their breath, and they don't mind fire. Not at all.\n\nWill you [drive them off]?",
        'drive them off',
        "Noxious hounds come up to Brika's camp every night in Muspelheim.",
        [
            hunt((1150, 450), "Drive off the noxious hounds " + where((1150, 450), 'mu_hallkel'), 'noxious hound', 5),
            end_talk('mu_hallkel', "Tell Huscarl Hallkel", "Quieter. Thank you. Now you've seen the place, you'll want to know why we're here.", 'default'),
        ],
        {'default': {'text': H, 'choice': [a1, a2]}})

a3 = z.item("Vent-Steam Charm", 'gem', 21, 'mind', "A glass bead with steam curling inside it.")
a4 = z.item("Firecat Fang Torc", 'neck', 21, 'might', "Fangs that glow faintly red.")
z.quest('mu_vents', 'Smoke Over the Vale', 21, 'mu_hallkel',
        "The smoke over Muspelheim has turned black, and it drifts down over the Vale. The vapor wraiths at the vents east of here are stirring the fires - and the firecats run before them.\n\nWill you [clear the vents]?",
        'clear the vents',
        "Vapor wraiths stir Muspelheim's fires at the vents; black smoke drifts down over the Vale.",
        [
            hunt((1380, 450), "Clear the vapor wraiths at the vents " + where((1380, 450), 'mu_hallkel'), 'vapor wraith', 3),
            hunt((1350, 480), "Kill the firecats", 'firecat', 3),
            end_talk('mu_hallkel', "Tell Hallkel", "The vents settle. But the black smoke isn't from them - it's from the hills to the west. Something's burning there that never burned before.\n\nForge-Master Thrain at the dverge hold in the south will know. Dverge know every fire.", 'default'),
        ],
        {'default': {'text': H, 'choice': [a3, a4]}}, requires='mu_hounds')

# ======================================================================== The Ash Road (20-23)
r1 = z.item("Ash-Road Cloak", 'cloak', 20, 'ward', "Grey with ash that never shakes out.")
r2 = z.item("Ashmonger's Ring", 'ring', 20, 'mind', "A ring of fused ash.")
z.quest('mu_ashmongers', 'The Ash Road', 20, 'mu_thrain',
        "The ash road from our hold runs north through the ashmongers' country. They never troubled the caravans before. Now they attack everything.\n\nWill you [clear the road]?",
        'clear the road',
        "Ashmongers attack every caravan on Muspelheim's ash road.",
        [
            hunt((620, 1060), "Clear the ashmongers from the ash road " + where((620, 1060), 'mu_thrain'), 'ashmonger', 5),
            end_talk('mu_thrain', "Tell Forge-Master Thrain", "Good. The ash-folk are restless because the fires moved. Fires don't move. Someone moved them.", 'default'),
        ],
        {'default': {'text': K, 'choice': [r1, r2]}})

r3 = z.item("Soot-Black Bracer", 'bracer', 21, 'ward', "Leather blackened in soot. Fire slides off it.")
r4 = z.item("Flame-Thrower's Charm", 'gem', 21, 'mind', "A little pot of something that burns without fuel.")
z.quest('mu_soot', 'The Soot-Folk', 21, 'mu_thrain',
        "The soot harvesters and flame throwers in the western ash fields used to trade soot to us for iron. Now they throw fire at our carts.\n\nWill you [quiet the ash fields]?",
        'quiet the ash fields',
        "The soot harvesters and flame throwers of Muspelheim's ash fields throw fire at the dverge carts.",
        [
            hunt((260, 1000), "Quiet the soot harvesters " + where((260, 1000), 'mu_thrain'), 'soot harvester', 4),
            hunt((250, 1100), "Quiet the flame throwers", 'flame thrower', 3),
            end_talk('mu_thrain', "Tell Thrain", "Quiet. One of them had a pouch of fire-salt on it - our fire-salt, from our forge. Somebody's selling it.", 'default'),
        ],
        {'default': {'text': K, 'choice': [r3, r4]}}, requires='mu_ashmongers')

r5 = z.item("Sulphur-Crust Ring", 'ring', 22, 'might', "Yellow crust over iron. It smells.")
r6 = z.item("Ant-Queen's Belt", 'belt', 22, 'finesse', "Chitin plates, jointed.")
z.quest('mu_ants', 'The Sulphur Pits', 22, 'mu_thrain',
        "We take sulphur from the pits in the west. The fire ants have dug into them, and they bite through iron boots.\n\nWill you [clear the pits]?",
        'clear the pits',
        "Fire ants have dug into the dverge sulphur pits in Muspelheim's west.",
        [
            hunt((320, 680), "Clear the fire ant workers " + where((320, 680), 'mu_thrain'), 'fire ant worker', 5),
            hunt((320, 660), "Kill the fire ant gatherers", 'fire ant gatherer', 3),
            end_talk('mu_thrain', "Tell Thrain", "The pits are ours again. Good. We'll need the sulphur - there's trouble coming.", 'default'),
        ],
        {'default': {'text': K, 'choice': [r5, r6]}})

# ======================================================================== The Fire-Sellers (23-25)
s1 = z.item("Fire-Salt Pouch Charm", 'gem', 23, 'mind', "A pouch of red salt. It's warm.")
s2 = z.item("Turncoat's Bracer", 'bracer', 23, 'finesse', "Dverge-work, the forge-mark scratched off.")
z.quest('mu_sparkers', 'The Fire-Sellers', 23, 'mu_thrain',
        "Some of our own - dverge who left the forge - camp south of the hold and call themselves the fire-sellers. They sell our fire-salt. To whom, I want to know.\n\nWill you [break their camp]?",
        'break their camp',
        "Renegade dverge, the fire-sellers, camp south of Khizil's hold and sell the forge's fire-salt.",
        [
            hunt((560, 1500), "Break the dverge sparkers " + where((560, 1500), 'mu_thrain'), 'dverge sparker', 4),
            search(Z, P(570, 1510), "Search the fire-sellers' camp", "a strongbox under a tarp", CRATE,
                   "Gold, a great deal of it, and a tally: 'Fire-salt, forty sacks, to the brood-priests in the wyrm hills. To keep the Mother's eggs warm.'"),
            end_talk('mu_thrain', "Bring the tally to Thrain", "'The Mother's eggs.' Gjalpinulva. The dragon under Malmohus. They're selling our fire to keep a dragon's brood warm.\n\nI need the ones who sold it.", 'default'),
        ],
        {'default': {'text': K, 'choice': [s1, s2]}}, requires='mu_ants')

s3 = z.item("Igniter's Torch-Ring", 'ring', 25, 'might', "A ring with a tiny flame trapped in the stone.")
s4 = z.item("Khizil Forge Mantle", 'cloak', 25, 'ward', "Forge-black, Khizil's hammer on the back.")
s5 = z.item("Crackler's Blast-Belt", 'belt', 25, 'finesse', "Hung with little clay pots. Empty, now.")
z.quest('mu_igniters', 'The Ringleaders', 25, 'mu_thrain',
        "The igniters and cracklers - they're the ringleaders. Bring friends; they throw fire like rain.\n\nWill you [bring them to account]?",
        'bring them to account',
        "Renegade dverge igniters and cracklers lead the fire-sellers south of Khizil's hold.",
        [
            hunt((570, 1540), "Bring down the dverge igniters " + where((570, 1540), 'mu_thrain'), 'dverge igniter', 2, r=60),
            hunt((570, 1540), "Bring down the dverge cracklers", 'dverge crackler', 2, r=60),
            end_talk('mu_thrain', "Tell Thrain", "Done. The forge won't sell another grain. But they've sold forty sacks already - the hatchery in the wyrm hills is warm enough. Hallkel's huscarls need to see it.", 'default'),
        ],
        {'default': {'text': K, 'choice': [s3, s4, s5]}}, requires='mu_sparkers', group=True)

# ======================================================================== The Old Battlefield (22-25)
o1 = z.item("Bone-Ash Ring", 'ring', 22, 'ward', "Pale grey, light as nothing.")
o2 = z.item("Burnt Sentry's Belt", 'belt', 22, 'might', "Rusted plates on a scorched strap.")
z.quest('mu_sentries', 'The Burnt Sentries', 22, 'ragnvald',
        "The middle of Muspelheim was a battlefield once - the dead still stand their watch there, burnt black. They've begun marching.\n\nWill you [put them down]?",
        'put them down',
        "The burnt dead of Muspelheim's old battlefield have begun marching.",
        [
            hunt((700, 700), "Put down the burnt skeletal sentries " + where((700, 700), 'ragnvald'), 'burnt skeletal sentry', 5),
            end_talk('ragnvald', "Tell Ragnvald the Skald", "Marching. The dead of an old war don't march without a reason.", 'default'),
        ],
        {'default': {'text': H, 'choice': [o1, o2]}})

o3 = z.item("Old-War Banner Charm", 'gem', 25, 'faith', "A scrap of a banner. A dragon, crossed out.")
o4 = z.item("Charred Warrior's Bracer", 'bracer', 25, 'might', "Iron, warped by an old, terrible heat.")
z.quest('mu_old_war', 'The Old War', 25, 'ragnvald',
        "I'm a skald. I want the song of the old war - who these dead were, and who burned them. The charred warriors hold the middle of the field.\n\nWill you [find out]?",
        'find out',
        "Charred warriors hold the middle of Muspelheim's old battlefield; nobody remembers the war.",
        [
            hunt((800, 650), "Fight through the charred skeletal warriors " + where((800, 650), 'ragnvald'), 'charred skeletal warrior', 4),
            search(Z, P(810, 660), "Search the old battlefield", "a cairn of burnt shields", CRATE,
                   "The shields all bear the same mark: a dragon, struck through with a spear. A rune-stone in the cairn: 'Here the hosts of Midgard held the Wyrm-Mother's brood. Here they burned. Here she slept.'"),
            end_talk('ragnvald', "Tell Ragnvald", "The Wyrm-Mother. Gjalpinulva. They fought her brood here, long ago, and she went to sleep under Malmohus after. The dead march because the brood is back.\n\nThat's the song. I'd rather it ended differently this time.", 'default'),
        ],
        {'default': {'text': H, 'choice': [o3, o4]}}, requires='mu_sentries')

# ======================================================================== The Hatchery (25-28)
w1 = z.item("Wyrm-Scale Bracer", 'bracer', 25, 'ward', "A fire wyrm's scale, still warm.")
w2 = z.item("Hill-Fire Ring", 'ring', 25, 'mind', "Red stone set in black iron.")
z.quest('mu_wyrms', 'The Wyrm Hills', 25, 'mu_hallkel',
        "The young fire wyrms in the northern hills have never been so many. They're being bred. We need to get close to the hatchery - and the wyrms are in the way.\n\nWill you [thin them out]?",
        'thin them out',
        "Young fire wyrms swarm Muspelheim's northern hills, bred at a hatchery.",
        [
            hunt((550, 280), "Thin out the young fire wyrms " + where((550, 280), 'mu_hallkel'), 'young fire wyrm', 5),
            end_talk('mu_hallkel', "Tell Hallkel", "Thinner. And they're all young - a single brood. Somebody's keeping a dragon's nursery up there.", 'default'),
        ],
        {'default': {'text': H, 'choice': [w1, w2]}}, requires='mu_vents')

w3 = z.item("Cinder-Drake Fang Torc", 'neck', 27, 'might', "A great drake's fang, black and red.")
w4 = z.item("Brood-Breaker's Belt", 'belt', 27, 'ward', "Thick, scorched, still whole.")
z.quest('mu_cinder_drakes', 'The Cinder Drakes', 27, 'mu_hallkel',
        "The cinder drakes guard the hatchery's eastern flank - grown wyrms, the brood's elders. Bring friends.\n\nWill you [break the nest]?",
        'break the nest',
        "Cinder drakes guard the eastern flank of the dragon's hatchery in Muspelheim's wyrm hills.",
        [
            hunt((948, 336), "Break the cinder drakes' nest " + where((948, 336), 'mu_hallkel'), 'cinder drake', 3, r=50),
            end_talk('mu_hallkel', "Tell Hallkel", "The flank's open. Now the hatchery itself.", 'default'),
        ],
        {'default': {'text': H, 'choice': [w3, w4]}}, requires='mu_wyrms', group=True)

w5 = z.item("Brood-Egg Shard Charm", 'gem', 28, 'mind', "A shard of a dragon's egg, warm as a hearth.")
w6 = z.item("Hatchery-Breaker's Mantle", 'cloak', 28, 'ward', "The King's blue, scorched and proud of it.")
w7 = z.item("Brood-Priest's Ring", 'ring', 28, 'faith', "Red scale on gold. Taken off a priest.")
z.quest('mu_hatchery', 'The Hatchery', 28, 'mu_hallkel',
        "The hatchery. The brood-priests keep it, with their brood-keepers. Kill the keepers, get into the warming-pits, and see what they're hatching.\n\nBring friends. Will you [raid the hatchery]?",
        'raid the hatchery',
        "Gjalpinulva's drakulv keep a hatchery in Muspelheim's wyrm hills, warming the dragon's brood.",
        [
            hunt((760, 300), "Kill the drakulv brood-keepers " + where((760, 300), 'mu_hallkel'), 'drakulv brood-keeper', 3, r=50),
            hunt((760, 300), "Kill the drakulv brood-priests", 'drakulv brood-priest', 2, r=50),
            search(Z, P(765, 305), "Search the warming-pits", "eggs as big as shields, in the lava", CRATE,
                   "A dozen eggs in the lava, and the brood-priests' rite on a slab: 'When the Hierophant speaks the Mother's whole name in Malmohus, the brood wakes with her. Keep them warm till then.'"),
            end_talk('mu_hallkel', "Tell Hallkel", "The whole name. Galplen's volva has the other half - so the priests in Myrkwood said. If the Hierophant gets it, the Mother wakes, and this brood with her.\n\nThe Hatch-Mother still keeps the pits. And the Brood-Sire ranges the hills - you'll see it when it comes. Midgard will need everyone, when it comes.", 'default'),
        ],
        {'default': {'text': H, 'choice': [w5, w6, w7]}}, requires='mu_cinder_drakes', group=True)
