"""Cornwall's story quests (claude 2026-11-24, "Albion - the plan", round 3) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_cornwall

Albion's HARD START, at Cornwall Station. Three short quests on the moor walk a new character round the Station; after that
everything is Deadly. Cornwall is giants' country - Corineus wrestled Gogmagog off its cliffs, and his oath-keepers still
stand against giants - and now Golestandt's quarry-giants come up from Dartmoor's edge. The Ghostly Church keeps Gorlois's
knights, who died the night Uther came to Tintagel wearing their duke's face. Out of the Catacombs of Cardova march the Drowned
Ninth, a lost legion the giants have bound to dig their quarry; free their eagle and they rest. At the end, Cirfans, the great
drake of the west, guards the quarry road to Dartmoor.

The zone's two older quests are kept as they were (white_wolf, drowned_ninth).

Arcs (recommended levels): The Moor (2-7, the hard start), Gorlois's Men (12-18), The Old Fae of Cornwall (20-31),
The Drowned Ninth (24-38), The Giants' Road (34-44).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk
from albion_story import Story, CRATE, BEDROLL, LANTERN, M, F, OLD

S = Story(6, 'Cornwall', 'alb_cornwall', 'story006_cornwall', {'white_wolf', 'drowned_ninth'},
          {'kerra_aldar', 'tregarth', 'tregarth_den', 'hywel', 'lt_penhale', 'kit'},
          {"Shepherd's Crook-Pin", 'White Fang Necklace', 'Moor-Grass Cloak', 'Stalker-Bone Ring', 'Eagle of the Ninth', "Kit's Heather Wreath",
           'Legionary Cingulum', "Standard-Bearer's Cape"})
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
CENTURION, LEGION = 12720, 12728

person('cw_gerens', 'Oath-Keeper Gerens', (1392, 524), 'm', 46, guild='the Oath of Corineus',
       idle="Corineus wrestled the last giant off these cliffs. We swore we'd do it again if we had to. We have to.")
person('cw_jory', 'Sergeant Jory', (1418, 520), 'm', 32, model=28, guild='the Men of Tintagel',
       idle="New to Cornwall? Stay on the moor till you can hold a sword. Then stay on the moor anyway.")

# ======================================================================== The Moor (2-7) - the hard start
m1 = z.item("Moor-Walker's Ring", 'ring', 5, 'ward', "Plain bronze. Every new face at the Station gets one.")
m2 = z.item("Heather Sash", 'belt', 5, 'charm', "Woven heather, dyed purple.")
z.quest('cw_moor_bears', 'Bears on the Moor', 2, 'cw_jory',
        "Welcome to the hardest corner of Albion. You'll want to start small. The young brown bears raid the Station's bins at night.\n\nWill you [chase off the bears]? Stay on the moor near the Station - nowhere else is safe for you yet.",
        'chase off the bears',
        "Young brown bears raid Cornwall Station's stores. A first task for a new arrival.",
        [
            hunt((1420, 450), "Chase off the young brown bears near the Station " + where((1420, 450), 'cw_jory'), 'young brown bear', 4),
            end_talk('cw_jory', "Tell Sergeant Jory", "Good. You're still alive. That's the first lesson of Cornwall.", 'default'),
        ],
        {'default': {'text': "From the Men of Tintagel.", 'choice': [m1, m2]}})

m3 = z.item("Spider-Silk Wristwrap", 'bracer', 5, 'finesse', "Cliff-spider silk. Sticky, then not.")
m4 = z.item("Cliff-Edge Charm", 'gem', 5, 'charm', "A sea-polished pebble from the cliff foot.")
z.quest('cw_spiderlings', 'Spiderlings on the Cliffs', 4, 'cw_jory',
        "Cliff spiderlings come up from the sea-cliffs north of the Station and spin over the paths. Small ones, for now. Their mothers live further west - don't go there.\n\nWill you [clear the paths]?",
        'clear the paths',
        "Cliff spiderlings spin webs over the paths north of Cornwall Station.",
        [
            hunt((1300, 330), "Clear the cliff spiderlings " + where((1300, 330), 'cw_jory'), 'cliff spiderling', 5),
            end_talk('cw_jory', "Tell Sergeant Jory", "Paths are clear. You're learning. Lieutenant Penhale has something for you.", 'default'),
        ],
        {'default': {'text': "From the Men of Tintagel.", 'choice': [m3, m4]}},
        requires='cw_moor_bears')

m5 = z.item("Penhale's Spare Bracer", 'bracer', 7, 'might', "Dented, polished, reliable.")
m6 = z.item("Station Watchman's Belt", 'belt', 7, 'ward', "The Men of Tintagel's own belt.")
m7 = z.item("Moor-Wolf Fang", 'neck', 7, 'might', "Your first proper trophy in Cornwall.")
z.quest('cw_moor_wolves', 'The Watch on the Moor', 7, 'lt_penhale',
        "Moor wolves hunt in packs round the Station at dusk. They've learned we're soft-hearted. Teach them otherwise and you've earned your place at our fire.\n\nWill you [stand the watch]? Then see Oath-Keeper Gerens - he'll tell you what Cornwall's really about.",
        'stand the watch',
        "Moor wolves hunt round Cornwall Station at dusk.",
        [
            hunt((1350, 500), "Drive off the moor wolves " + where((1350, 500), 'lt_penhale'), 'moor wolf', 4),
            end_talk('lt_penhale', "Tell Lieutenant Penhale", "That'll do. Welcome to Cornwall. Gerens is by the well - go and hear about giants.", 'default'),
        ],
        {'default': {'text': "From the Men of Tintagel.", 'items': [m7], 'choice': [m5, m6]}},
        requires='cw_spiderlings')

# ======================================================================== Gorlois's Men (12-18)
g1 = z.item("Cliff-Spider Fang Ring", 'ring', 12, 'finesse', "Hollow, venom long dried.")
g2 = z.item("Web-Cloak", 'cloak', 12, 'ward', "Grey silk over wool. It sheds rain.")
z.quest('cw_cliff_spiders', 'The Spider Mothers', 12, 'cw_jory',
        "The spiderlings' mothers nest on the cliff tops west of here. Big as ponies. They're coming closer to the Station every season.\n\nWill you [break the nests]?",
        'break the nests',
        "Cliff spiders nest on the cliff tops west of Cornwall Station.",
        [
            hunt((950, 420), "Kill the cliff spiders " + where((950, 420), 'cw_jory'), 'cliff spider', 5),
            end_talk('cw_jory', "Tell Sergeant Jory", "The nests are broken? You're not new any more.", 'default'),
        ],
        {'default': {'text': "From the Men of Tintagel.", 'choice': [g1, g2]}})

g3 = z.item("Gorlois's Boar Ring", 'ring', 16, 'might', "The boar of Cornwall, Gorlois's sign.")
g4 = z.item("Ghostly Church Bell-Clapper Charm", 'gem', 16, 'faith', "It rings, very faintly, at midnight.")
g5 = z.item("Duke's Man Mantle", 'cloak', 16, 'ward', "Cornish black and gold.")
z.quest('cw_gorlois_men', "Gorlois's Men", 16, 'lt_penhale',
        "The church on the cliff tops is haunted - every child in Cornwall knows that. They're Duke Gorlois's knights. The night Uther came to Tintagel wearing Gorlois's face - Merlin's doing - they died defending a duke who wasn't there.\n\nThey've started coming out. Will you [go to the church]? Tell them the truth, if they'll hear it.",
        'go to the church',
        "The ghosts of Duke Gorlois's knights have started coming out of the Ghostly Church.",
        [
            hunt((1196, 372), "Get past the ghostly clerics " + where((1196, 372), 'lt_penhale'), 'ghostly cleric', 3),
            hunt((1191, 376), "Face Brother Jarrel, the church's dead priest", 'Brother Jarrel', 1,
                 text="Brother Jarrel lowers his hands. 'The duke came home that night. We saw him. We let him in.' He looks at you. 'It wasn't him, was it?'"),
            end_talk('lt_penhale', "Tell Lieutenant Penhale", "He knows now. That's all any of them ever wanted - to know.\n\nThey say Merlin was sorry for that night. Not sorry enough.", 'default'),
        ],
        {'default': {'text': "From the Men of Tintagel.", 'choice': [g3, g4, g5]}},
        requires='cw_cliff_spiders')

# ======================================================================== The Old Fae of Cornwall (20-31)
f1 = z.item("Muryan's Thimble Ring", 'ring', 20, 'charm', "A thimble, very small. The muryan who wore it was smaller.")
f2 = z.item("Tricker's Patchwork Sash", 'belt', 20, 'finesse', "A hundred stolen scraps.")
z.quest('cw_muryans', 'The Shrinking Folk', 20, 'cw_gerens',
        "The muryans are the old fae of Cornwall - every year a little smaller, till they're ants. This year they've turned spiteful. Their trickster says the giants promised to make them big again.\n\nWill you [break the mound]? And catch the trickster.",
        'break the mound',
        "The muryans, Cornwall's shrinking fae, have sided with the giants.",
        [
            hunt((985, 844), "Break the muryans at their mound " + where((985, 844), 'cw_gerens'), 'muryan', 5),
            hunt((1330, 924), "Catch the muryan trickster", 'muryan trickster', 1,
                 text="The trickster squeaks: 'The giants were here first! Before Corineus! They'll make us big again!'"),
            end_talk('cw_gerens', "Tell Oath-Keeper Gerens", "Giants promising things. Corineus heard the same promises, and threw the one who made them off a cliff.", 'default'),
        ],
        {'default': {'text': "From the Oath of Corineus.", 'choice': [f1, f2]}})

f3 = z.item("Bucca's Fish-Bone Charm", 'gem', 23, 'mind', "The buccas leave fish-bones for luck. This one didn't work for them.")
f4 = z.item("Storm-Bucca's Bracer", 'bracer', 23, 'ward', "Wet, always, as though from the sea.")
z.quest('cw_buccas', 'The Bucca Storm', 23, 'cw_gerens',
        "The buccas - the sea-spirits of the fishermen - have come inland and they're angry. A storm's driving them out of the sea, they say, a white storm out of Lyonesse that isn't natural.\n\nWill you [calm the buccas]? The only way they'll listen is after a beating.",
        'calm the buccas',
        "The buccas, the fishermen's sea-spirits, have been driven inland by an unnatural storm from Lyonesse.",
        [
            hunt((1136, 929), "Beat the buccas into listening " + where((1136, 929), 'cw_gerens'), 'bucca', 5),
            end_talk('cw_gerens', "Tell Oath-Keeper Gerens", "A white storm out of Lyonesse. The white dragon's weather, the old women would say. I used to laugh at them.", 'default'),
        ],
        {'default': {'text': "From the Oath of Corineus.", 'choice': [f3, f4]}})

f5 = z.item("Den Mother's Pelt", 'cloak', 26, 'ward', "Grey, huge, thick enough to sleep in the snow.")
f6 = z.item("Pack-Leader Tooth Torc", 'neck', 26, 'might', "Three yellow teeth on a torc.")
z.quest('cw_wolf_dens', 'The Wolf Dens', 26, 'kerra_aldar',
        "The white she-wolf's gone, but her pack has den mothers in the middle moor, and they breed faster than we can kill.\n\nWill you [clear the dens]?",
        'clear the dens',
        "The moor wolves' den mothers breed in the middle moor.",
        [
            hunt((910, 896), "Kill the moor den mothers " + where((910, 896), 'kerra_aldar'), 'moor den mother', 2),
            hunt((913, 783), "Kill the moor pack leaders", 'moor pack leader', 3),
            end_talk('kerra_aldar', "Tell Kerra Aldar", "My flocks will see the spring. Thank you.", 'default'),
        ],
        {'default': {'text': "From Kerra Aldar.", 'choice': [f5, f6]}},
        requires='white_wolf')

f7 = z.item("Beech-Heart Ring", 'ring', 28, 'faith', "Smooth beech-heart, warm to the touch.")
f8 = z.item("Old Beech Mantle", 'cloak', 28, 'ward', "Bark-brown, lined with beech-leaf green.")
z.quest('cw_old_beeches', 'The Old Beeches', 28, 'cw_gerens',
        "The beeches of the east wood are older than Corineus. The giants have been singing to them - and now the oldest have woken, and they walk west to join the giants.\n\nWill you [fell the old beeches]? It grieves me to ask.",
        'fell the old beeches',
        "The oldest beeches of Cornwall have woken to the giants' singing.",
        [
            hunt((1490, 975), "Fell the aged beeches " + where((1490, 975), 'cw_gerens'), 'aged beech', 2),
            hunt((1100, 800), "Fell the elder beeches walking west", 'elder beech', 4),
            end_talk('cw_gerens', "Tell Oath-Keeper Gerens", "Felled. We'll plant again where they stood. Corineus planted the first of them, they say.", 'default'),
        ],
        {'default': {'text': "From the Oath of Corineus.", 'choice': [f7, f8]}},
        requires='cw_muryans')

f9 = z.item("Rooter-Tusk Bracer", 'bracer', 31, 'might', "Ivory, cracked, bound in bronze.")
f10 = z.item("Downs-Digger's Belt", 'belt', 31, 'ward', "Thick leather. It smells of turned earth.")
z.quest('cw_rooters', 'The Rooters Dig', 31, 'cw_gerens',
        "Giant rooters - great boars - turning up the southern downs. They're not hunting, they're digging, in lines. The giants have them clearing ground.\n\nWill you [stop the dig]?",
        'stop the dig',
        "Giant rooters dig the southern downs in lines, clearing ground for the giants.",
        [
            hunt((711, 1203), "Kill the giant rooters " + where((711, 1203), 'cw_gerens'), 'giant rooter', 6),
            end_talk('cw_gerens', "Tell Oath-Keeper Gerens", "Clearing ground for a road. The giants' road from Dartmoor. I knew it.", 'default'),
        ],
        {'default': {'text': "From the Oath of Corineus.", 'choice': [f9, f10]}})

# ======================================================================== The Drowned Ninth (24-38)
n1 = z.item("Legionary's Bronze Phalera", 'gem', 33, 'might', "A bronze medal, green with age. For valour.")
n2 = z.item("Marching-Road Bracer", 'bracer', 33, 'ward', "Iron and leather, Roman-made.")
n3 = z.item("Giant-Rune Shard", 'gem', 33, 'mind', "A shard of rune-stone, cracked across the middle.")
z.quest('cw_ninth_road', "The Ninth's Road", 33, 'hywel',
        "Kit came home - thanks to you. But the Ninth still march. Every night, out of Cardova and along the road to the old fort, and back.\n\nWhy do they march? Will you [find out]?",
        'find out',
        "The Drowned Ninth march every night from the Catacombs of Cardova to the old Roman fort and back.",
        [
            hunt((950, 1240), "Fight the legionnaires on the marching road " + where((950, 1240), 'hywel'), 'skeletal legionnaire', 5),
            search(Z, P(950, 1245), "Search a fallen legionnaire", "a legionnaire's armour, empty", CRATE,
                   "Under the breastplate, scratched into the bone: a giant's rune. 'DIG.' Someone has bound the Ninth to work."),
            end_talk('hywel', "Tell Old Hywel", "Bound to dig? By giants? My grandfather said the Ninth marched into the mist two hundred years ago looking for a quarry they'd been promised.\n\nThey found it.", 'default'),
        ],
        {'default': {'text': "From Old Hywel.", 'choice': [n1, n2, n3]}},
        requires='drowned_ninth')

n4 = z.item("Favius's Vine-Staff Ring", 'ring', 36, 'might', "From a centurion's vine-staff. He used it on his men, not his enemies.")
n5 = z.item("Old Fort Mantle", 'cloak', 36, 'ward', "Roman red, faded nearly pink.")
z.quest('cw_favius', 'Centurion Favius', 36, 'hywel',
        "The Ninth's centurion, Favius, holds the old fort in the south-east and drives them out every night. He's the one the giants bound first.\n\nWill you [break Favius]? Bring friends.",
        'break Favius',
        "Centurion Favius drives the Drowned Ninth out of the old Roman fort every night.",
        [
            hunt((1350, 1262), "Fight into the old Roman fort " + where((1350, 1262), 'hywel'), 'skeletal legionnaire', 4),
            hunt((1350, 1258), "Defeat Centurion Favius", 'Centurion Favius', 1,
                 text="Favius falls. 'The eagle,' he rasps. 'They took the eagle into Cardova. While they have it, we march.'"),
            end_talk('hywel', "Tell Old Hywel", "The eagle. The legion's standard. As long as the giants hold it, the Ninth are theirs.", 'default'),
        ],
        {'default': {'text': "From Old Hywel.", 'choice': [n4, n5]}},
        requires='cw_ninth_road', group=True)

n6 = z.item("Aquila Feather", 'gem', 38, 'faith', "A gilt feather from the eagle of the Ninth. It's warm.")
n7 = z.item("Legate's Signet", 'ring', 38, 'mind', "Gold and carnelian, the legion's number cut in it.")
n8 = z.item("Ninth's Rest Mantle", 'cloak', 38, 'ward', "Roman red, with a white eagle. Given to whoever brought the Ninth home.")
z.quest('cw_eagle', 'The Eagle of the Ninth', 38, 'cw_gerens',
        "Favius told you: the giants hold the Ninth's eagle in the mouth of Cardova, and the legate guards it for them. Bring back the eagle and the Ninth can lie down.\n\nWill you [take back the eagle]? Bring everyone.",
        'take back the eagle',
        "The giants hold the Drowned Ninth's eagle at the mouth of the Catacombs of Cardova.",
        [
            reach(Z, P(800, 1250), "Go to the mouth of Cardova " + where((800, 1250), 'cw_gerens'), "The catacombs breathe cold. Torches, and the glint of gold on a pole.", r=30),
            boss(Z, P(795, 1262), "Defeat the Legate of the Ninth", "The legate falls, and the eagle with him. Along the marching road, every legionnaire stops, and turns, and sits down.",
                 'the Legate of the Ninth', CENTURION, 40, "The legate of the Ninth raises the eagle on its pole: 'Legio IX Hispana! To me!' Behind him, the dead stand to.",
                 adds=[(LEGION, 'skeletal legionnaire', [36, 37])], every=30, count=2),
            end_talk('cw_gerens', "Bring the eagle to Oath-Keeper Gerens", "The eagle of the Ninth. Two hundred years.\n\nWe'll bury it with honour at the Station. They were soldiers. They deserve that much.", 'default'),
        ],
        {'default': {'text': "From the Oath of Corineus.", 'choice': [n6, n7, n8]}},
        requires='cw_favius', group=True)

n9 = z.item("Giant-Grave Torc", 'neck', 34, 'might', "Huge, cut down, still too heavy.")
n10 = z.item("Captured-Soul Lantern Charm", 'gem', 34, 'faith', "A lantern-glass. Something grateful lived in it once.")
z.quest('cw_giant_graves', 'The Giant Graves', 34, 'cw_gerens',
        "In the west, the giants' own graves - the ones Corineus filled. Their skeletons are standing up, and they keep souls in cages round them.\n\nWill you [free the captured souls]? Their keeper, Aricoer, is no friend to anyone.",
        'free the captured souls',
        "Giant skeletons in the western graves keep captured souls in cages.",
        [
            hunt((548, 1106), "Break the giant skeletons " + where((548, 1106), 'cw_gerens'), 'giant skeleton', 3),
            hunt((485, 1024), "Defeat Aricoer, keeper of the souls", 'Aricoer', 1),
            end_talk('cw_gerens', "Tell Oath-Keeper Gerens", "Freed. Corineus would be glad. He hated cages.", 'default'),
        ],
        {'default': {'text': "From the Oath of Corineus.", 'choice': [n9, n10]}}, group=True)

# ======================================================================== The Giants' Road (34-44)
q1 = z.item("Quarry-Giant's Chisel Ring", 'ring', 40, 'might', "A chisel-tip, bent round. It cut granite once.")
q2 = z.item("Stoneshaper's Belt", 'belt', 40, 'ward', "Granite plates on leather.")
q3 = z.item("Corinean Oath-Torc", 'neck', 40, 'faith', "Iron and gold, the oath-keepers' sign.")
z.quest('cw_quarry_road', 'The Quarry Road', 40, 'cw_gerens',
        "The giants have cut a road in the far south-west, down to Dartmoor - the quarry road. Every stone that went to Salisbury went up it. Every giant that comes north walks it.\n\nWill you [break the road]? Bring the strongest friends you have.",
        'break the road',
        "Golestandt's quarry-giants hold the road from Dartmoor in the far south-west.",
        [
            hunt((200, 1400), "Fight the quarry-giants on the road " + where((200, 1400), 'cw_gerens'), 'Cornish quarry-giant', 2),
            hunt((210, 1390), "Defeat the granite giant stoneshapers", 'granite giant stoneshaper', 1),
            search(Z, P(195, 1410), "Search the giants' road-camp", "a giants' cairn of marked stones", CRATE,
                   "Marked stones, a giant's tally: so many for the Dance, so many for the causeway in the marsh, so many for 'the Sleeper's door'. At the bottom, a claw-mark, and one word in Albion: 'Dartmoor.'"),
            end_talk('cw_gerens', "Tell Oath-Keeper Gerens", "Dartmoor. That's where it all comes from. The dragon in his lair, and his giants quarrying the moor to build his roads.\n\nCorineus would have gone south. So should we, one day.", 'default'),
        ],
        {'default': {'text': "From the Oath of Corineus.", 'choice': [q1, q2, q3]}},
        requires='cw_giant_graves', group=True)

q4 = z.item("Cirfans' Scale", 'gem', 44, 'might', "A drake-scale the size of a buckler, cut down to a charm.")
q5 = z.item("Heir of Corineus Mantle", 'cloak', 44, 'ward', "Cornish black, with Corineus's wrestling-belt in gold.")
q6 = z.item("Drake-Fire Ring", 'ring', 44, 'mind', "Red-gold. It never cools.")
q7 = z.item("Great Drake's Tooth", 'neck', 44, 'might', "As long as your forearm.")
z.quest('cw_cirfans', 'Cirfans', 44, 'cw_gerens',
        "Cirfans, the great drake of the west, sits over the quarry road where it turns south. The giants feed him. He's the white dragon's own blood, they say - a grandchild.\n\nIf he falls, the road is ours. Will you [face Cirfans]? Everyone you can find.",
        'face Cirfans',
        "Cirfans, the great drake of the west and Golestandt's grandchild, guards the quarry road.",
        [
            hunt((112, 1253), "Defeat Cirfans, the great drake of the west " + where((112, 1253), 'cw_gerens'), 'Cirfans', 1,
                 text="Cirfans falls across the road, and the earth shakes - and far to the south, something enormous roars."),
            choice('cw_gerens', "Speak with Oath-Keeper Gerens", "You heard that? That was Golestandt. He felt his grandchild die.\n\nWe can [carve the oath] on Cirfans' bones, so every giant who walks this road reads it. Or [send the head to Tintagel], so the whole of Cornwall knows the oath still holds.",
                   [('carve the oath', "Then carve it deep. 'Corineus threw the last one off the cliff. We are still here.'", 'ending:oath'),
                    ('send the head to Tintagel', "Then it goes to Tintagel on a cart, and every village will turn out to see it pass.", 'ending:tintagel')]),
        ],
        {'oath': {'text': "From the Oath of Corineus.", 'items': [q5], 'choice': [q4, q6, q7]},
         'tintagel': {'text': "From the Men of Tintagel.", 'items': [q4], 'choice': [q5, q6, q7]}},
        requires='cw_quarry_road', group=True)
