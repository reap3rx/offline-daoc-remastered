"""East Svealand's story quests (claude 2026-11-24, "Midgard - the plan", round 1) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_east_svealand

Wolf country of lakes and rivers, Peaceful, round Audliten, Vasudheim and Dvalin. The west thread: the wolves grow bold. The
sveawolves and lupines run with the Grey Hames - wild men in wolf-hames, sworn to the Fenris-wolf's children - and together they
have taken Ulfrstead, a steading by the tomte hills (the zone's fort to retake, for the Steading-League). The south thread:
drakelings nest at the mouth of Nisse's Lair, fed by a drakulv missionary on his way north from Gotar.

The zone's two older quests are kept as they were (thrall_price, tomte_due).

Arcs (recommended levels): Audliten's Shore (6-9), The Dirges' Road (8-12), The Tomte (9-12), The Grey Hames (9-14),
Nisse's Lair (12-16).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(101, 'East Svealand', 'mid_east_svealand', 'story101_east_svealand', {'thrall_price', 'tomte_due'},
          {'gunnhild', 'orm_thrallmaster', 'ketil', 'ragna', 'granny_tomte'},
          {'Broken-Collar Bracer', "Freedman's Cloak", "Runaway's Ring", 'Price-Paid Charm', "Tomte's Porridge-Spoon", 'Cradle-Quilt Cloak',
           "Nisse's Red Cap", 'Barn-Beam Bracer'}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157
PREACHER = 60160115

person('es_hallgerd', 'Steading-Reeve Hallgerd', (150, 560), 'f', 34, model=F, guild='the Steading-League',
       idle="Every farm from here to the Gotar road pays into the League. The League keeps the wolves off. Lately the League is failing.")
person('es_brand', 'Huscarl Brand', (1338, 468), 'm', 36, model=M, guild="King Eirik's Huscarls",
       idle="Vasudheim is the King's town. I'd like it to stay that way.")
person('es_ketilbjorn', 'Old Ketilbjorn', (560, 640), 'm', 20, model=OLD, guild='the Steading-League',
       idle="Forty years a shepherd on this moor. Never seen wolves walk with men. Never wanted to.")

# ======================================================================== Audliten's Shore (6-9)
a1 = z.item("Crab-Shell Bracer", 'bracer', 6, 'ward', "Rock-crab shell, lashed on with gut.")
a2 = z.item("Audliten Net-Ring", 'ring', 6, 'finesse', "A fisher's ring, knotted from net-cord and wire.")
z.quest('es_crabs', 'The Shallows', 6, 'es_hallgerd',
        "Rock crabs in the shallows, big as shields. They've taken over the fishing beaches and they pinch the nets to rags.\n\nWill you [clear the shallows]?",
        'clear the shallows',
        "Rock crabs have taken over Audliten's fishing shallows.",
        [
            hunt((420, 800), "Clear the rock crabs from the shallows " + where((420, 800), 'es_hallgerd'), 'rock crab', 6),
            end_talk('es_hallgerd', "Tell Steading-Reeve Hallgerd", "The fishers thank you. The League thanks you. The crabs, I expect, do not.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [a1, a2]}})

a3 = z.item("Ant-Hill Charm", 'gem', 7, 'finesse', "A worker ant in amber.")
a4 = z.item("Furrow-Walker's Belt", 'belt', 7, 'ward', "A farmer's belt, patched many times.")
z.quest('es_ants', 'The Army Ants', 7, 'es_hallgerd',
        "Army ants march out of the south fields by Dvalin and eat a farm bare in a night. The farmers flood the fields to stop them. It doesn't stop them.\n\nWill you [break the march]?",
        'break the march',
        "Army ants march out of the fields by Dvalin and strip the farms.",
        [
            hunt((450, 1200), "Break the army ants' march " + where((450, 1200), 'es_hallgerd'), 'army ant worker', 6),
            end_talk('es_hallgerd', "Tell Hallgerd", "Broken - but there's a mound in the south with soldiers guarding it. Break that and they're done for a year.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [a3, a4]}})

a5 = z.item("Ant-Soldier Mandible Ring", 'ring', 9, 'might', "Big enough to be a ring. Sharp enough to be a weapon.")
a6 = z.item("Dvalin Farmer's Cloak", 'cloak', 9, 'ward', "Brown, waxed, and smelling of rain.")
z.quest('es_ant_mound', 'The Mound', 9, 'es_hallgerd',
        "The ant mound south of Dvalin - a hill of it, crawling. The soldiers guard it. Kill the soldiers and the workers scatter.\n\nWill you [take the mound]?",
        'take the mound',
        "An army ant mound south of Dvalin is guarded by soldier ants.",
        [
            hunt((480, 1290), "Kill the army ant soldiers at the mound " + where((480, 1290), 'es_hallgerd'), 'army ant soldier', 4),
            end_talk('es_hallgerd', "Tell Hallgerd", "Done. The League owes you. And there's harder work coming - talk to Old Ketilbjorn on the moor. He's seen something.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [a5, a6]}}, requires='es_ants')

# ======================================================================== The Dirges' Road (8-12)
d1 = z.item("Dirge-Bell Charm", 'gem', 8, 'faith', "A little bronze bell. It rings once, then never again.")
d2 = z.item("Old-Road Walker's Ring", 'ring', 8, 'mind', "Found on the road. Whose, nobody knows.")
z.quest('es_dirges', 'The Dirges', 8, 'es_brand',
        "The dirges walk the old roads in the north - ghosts that sing, and anyone who listens too long lies down and doesn't get up. More of them every week.\n\nWill you [quiet them]?",
        'quiet them',
        "The nordic dirges, singing ghosts, walk East Svealand's old northern roads in growing numbers.",
        [
            hunt((500, 450), "Quiet the nordic dirges " + where((500, 450), 'es_brand'), 'nordic dirge', 5),
            end_talk('es_brand', "Tell Huscarl Brand", "Quiet. What were they singing? The farmers say it's always the same song now - a winter song.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [d1, d2]}})

d3 = z.item("Ghoul-Ward Torc", 'neck', 10, 'faith', "Rowan wood bound in iron.")
d4 = z.item("Barrow-Road Bracer", 'bracer', 10, 'ward', "Dark leather, scored with warding runes.")
z.quest('es_ghouls', 'Wayward', 10, 'es_brand',
        "Wayward ghouls on the far northern road, digging. Into the old dwarf barrow. Ghouls don't dig - they eat what's left out.\n\nWill you [stop them]?",
        'stop them',
        "Wayward ghouls are digging at the old dwarf barrow on East Svealand's northern road.",
        [
            hunt((570, 180), "Stop the wayward ghouls " + where((570, 180), 'es_brand'), 'wayward ghoul', 3),
            end_talk('es_brand', "Tell Brand", "They were digging toward the barrow. Something in there is calling them. Or something out here wants in.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [d3, d4]}}, requires='es_dirges')

d5 = z.item("Dwarf-Rune Stone", 'gem', 12, 'mind', "A chip of the barrow's runestone. The runes say 'cold'.")
d6 = z.item("Barrow-King's Ring", 'ring', 12, 'might', "A dwarf lord's ring, too big for any finger you have.")
d7 = z.item("Sealed-Door Mantle", 'cloak', 12, 'ward', "Stone-grey, from the barrow's door-hangings.")
z.quest('es_dwarf_barrow', 'The Sealed Barrow', 12, 'es_brand',
        "The dwarf barrow on the northern road is open, and the dwarves inside are up and walking. Bone and old iron.\n\nIt's a job for a few. Will you [go into the barrow]? Find out why they sealed it.",
        'go into the barrow',
        "The old dwarf barrow on East Svealand's northern road is open, and its dead are walking.",
        [
            hunt((709, 213), "Put down the dwarf bone skeletons " + where((709, 213), 'es_brand'), 'dwarf bone skeleton', 4, r=40),
            search(Z, P(715, 205), "Search the barrow's runestone", "a runestone, cracked across", CRATE,
                   "Dwarf runes: 'THE COLD CAME OUT OF THE WEST IN THE YEAR OF THE GREY WOLF. WE SEALED OURSELVES IN. DO NOT OPEN UNTIL SPRING.' Somebody opened it. It is not spring in the west."),
            end_talk('es_brand', "Tell Brand", "'The year of the grey wolf.' They sealed themselves in against a winter. Last time it came. Gods help us.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [d5, d6, d7]}}, requires='es_ghouls', group=True)

# ======================================================================== The Tomte (9-12)
t1 = z.item("Pillager's Sack-Belt", 'belt', 9, 'finesse', "A tomte's swag-sack, cut down into a belt.")
t2 = z.item("Farmhouse Hearth Charm", 'gem', 9, 'charm', "A coal from a hearth the tomte didn't get to.")
z.quest('es_tomte_raiders', 'The Tomte Raiders', 9, 'ragna',
        "The tomte used to keep a farm - sweep the barn, mind the beasts, for a bowl of porridge. These ones don't. These ones raid. They come down from the south hills in gangs.\n\nWill you [drive them off]?",
        'drive them off',
        "Gangs of tomte pillagers raid East Svealand's farms from the southern hills.",
        [
            hunt((800, 1150), "Drive off the tomte pillagers " + where((800, 1150), 'ragna'), 'tomte pillager', 5),
            end_talk('ragna', "Tell Ragna Farmwife", "Off - for now. They were frightened, my husband says. Running from something and robbing as they ran.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [t1, t2]}})

t3 = z.item("Aggressor's Iron Cap", 'gem', 12, 'might', "A tomte's iron cap, small enough to be a charm.")
t4 = z.item("Barn-Watch Bracer", 'bracer', 12, 'ward', "Leather, with a barn-owl stamped on it.")
z.quest('es_tomte_aggressors', 'The Aggressors', 12, 'ragna',
        "The worst of the tomte - aggressors, the farmers call them - have made a camp in the eastern hills. They're the ones who lead the raids.\n\nWill you [break them]?",
        'break them',
        "Tomte aggressors lead the raids on East Svealand's farms from a camp in the eastern hills.",
        [
            hunt((1050, 1000), "Break the tomte aggressors " + where((1050, 1000), 'ragna'), 'tomte aggressor', 3),
            end_talk('ragna', "Tell Ragna", "One of them was carrying a silver scale. Not a fish's. Something bigger, from the south, by Nisse's Lair.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [t3, t4]}}, requires='es_tomte_raiders')

# ======================================================================== The Grey Hames (9-14)
g1 = z.item("Sveawolf-Fur Collar", 'neck', 9, 'ward', "Grey fur, thick enough for any winter. Nearly.")
g2 = z.item("Shepherd's Crook-Ring", 'ring', 9, 'faith', "Iron, bent like a crook.")
z.quest('es_sveawolves', 'Bold Wolves', 9, 'es_ketilbjorn',
        "The sveawolf mothers bring their packs right up to the folds now. In daylight. A wolf doesn't come near men in daylight unless it isn't afraid of them any more.\n\nWill you [teach them fear]?",
        'teach them fear',
        "Sveawolf packs come up to East Svealand's sheepfolds in daylight.",
        [
            hunt((600, 800), "Teach the sveawolf mothers fear " + where((600, 800), 'es_ketilbjorn'), 'sveawolf mother', 5),
            end_talk('es_ketilbjorn', "Tell Old Ketilbjorn", "They'll learn. Or they won't. Either way, I've stopped sleeping.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [g1, g2]}})

g3 = z.item("Lupine-Fang Torc", 'neck', 11, 'might', "Fangs on a leather thong, every one longer than a finger.")
g4 = z.item("Moor-Runner's Belt", 'belt', 11, 'finesse', "Light, quick, and made to run in.")
z.quest('es_lupines', 'The Lupines', 11, 'es_ketilbjorn',
        "Lupines - the big ones, half wolf, half something worse - came over the eastern hills a month ago. They walk on two legs when they think no one's watching.\n\nWill you [hunt them]?",
        'hunt them',
        "Lupines, half wolf and half something worse, came over East Svealand's eastern hills.",
        [
            hunt((1000, 600), "Hunt the lupine snarlers " + where((1000, 600), 'es_ketilbjorn'), 'lupine snarler', 5),
            end_talk('es_ketilbjorn', "Tell Ketilbjorn", "Two legs. I told you. And there are men out there with them - men in wolf-skins, with the heads still on.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [g3, g4]}}, requires='es_sveawolves')

g5 = z.item("Grey-Hame Scrap Charm", 'gem', 12, 'mind', "A scrap of wolf-hame. It smells of blood and frost.")
g6 = z.item("Scout-Hunter's Bracer", 'bracer', 12, 'finesse', "Light leather, for long stalking.")
z.quest('es_grey_hames', 'Men in Wolf-Skins', 12, 'es_hallgerd',
        "Ketilbjorn's men in wolf-skins - the Grey Hames, they call themselves. Wildlings. They swear blood-oaths to the Fenris-wolf's children and run with the packs. Their scouts watch every road.\n\nWill you [blind their scouts]?",
        'blind their scouts',
        "The Grey Hames, wildlings in wolf-hames sworn to Fenrir's children, watch East Svealand's roads.",
        [
            hunt((1150, 500), "Kill the Grey Hame scouts " + where((1150, 500), 'es_hallgerd'), 'wildling scout', 4),
            end_talk('es_hallgerd', "Tell Hallgerd", "Blind - for now. And they've taken a steading. Ulfrstead, by the tomte hills. The family got out. Most of them.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [g5, g6]}}, requires='es_lupines')

g7 = z.item("Ulfrstead Door-Nail Ring", 'ring', 14, 'might', "An iron nail from Ulfrstead's door, bent into a ring.")
g8 = z.item("Hame-Breaker's Mantle", 'cloak', 14, 'ward', "League grey, with the wolf struck through.")
g9 = z.item("League Oath-Torc", 'neck', 14, 'faith', "The Steading-League's oath, twisted in silver.")
z.quest('es_ulfrstead', 'Ulfrstead', 14, 'es_hallgerd',
        "Go to Ulfrstead. Not to fight - to look. Count them. See what they've done to the place. The League won't send its men in blind.\n\nWill you [scout Ulfrstead]?",
        'scout Ulfrstead',
        "The Grey Hames and their wolves have taken Ulfrstead, a steading by the tomte hills.",
        [
            reach(Z, P(760, 580), "Climb the ridge above Ulfrstead", "Smoke from the hall, wolves in the yard, and men in wolf-hames on the walls. Too many to count.", r=25),
            search(Z, P(790, 610), "Search below Ulfrstead's walls", "a wolf-hame nailed over the gate", CRATE,
                   "A wolf's whole skin nailed up like a banner, and burnt into the gate-post: 'FENRIR'S CHILDREN WALK. THE WINTER WALKS WITH THEM.'"),
            end_talk('es_hallgerd', "Tell Hallgerd", "'The winter walks with them.' Then the League takes Ulfrstead back before winter does.\n\nWe need the farms behind us. Every wolf killed, every raid stopped - it all tells the League's men they can win. When they're ready, they'll march. Be there.", 'default'),
        ],
        {'default': {'text': "From the Steading-League.", 'choice': [g7, g8, g9]}}, requires='es_grey_hames')

# ======================================================================== Nisse's Lair (12-16)
n1 = z.item("Envy-Drake Scale Charm", 'gem', 12, 'mind', "Green and gold. It's warm, like something alive.")
n2 = z.item("Lair-Road Belt", 'belt', 12, 'ward', "Scorched at the edges.")
z.quest('es_drakelings', 'Drakelings', 12, 'es_brand',
        "Drakelings at the mouth of Nisse's Lair, in the south. There were always a few. Now there are dozens, and they're not wild - they come when somebody whistles.\n\nWill you [thin them]?",
        'thin them',
        "Drakelings swarm at the mouth of Nisse's Lair in East Svealand's south - and come when someone whistles.",
        [
            hunt((760, 1080), "Thin out the envy drakelings " + where((760, 1080), 'es_brand'), 'envy drakeling', 5),
            end_talk('es_brand', "Tell Huscarl Brand", "Somebody whistles for them. Somebody is feeding them. Find out who.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [n1, n2]}})

n3 = z.item("Silverscale Bracer", 'bracer', 14, 'ward', "Small silver scales, sewn on overlapping.")
n4 = z.item("Brood-Watcher's Ring", 'ring', 14, 'finesse', "Silver, set with a drakeling's eye-stone.")
z.quest('es_silverscales', 'The Silverscales', 14, 'es_brand',
        "The silverscale drakelings - the big ones - guard a nest by Nisse's Lair. The tomte had a scale from it. So the nest is real.\n\nWill you [find the nest]?",
        'find the nest',
        "Silverscale drakelings guard a nest by Nisse's Lair.",
        [
            hunt((990, 1160), "Kill the silverscale drakelings " + where((990, 1160), 'es_brand'), 'silverscale drakeling', 3),
            search(Z, P(1000, 1170), "Search the drakeling nest", "a nest of warm stones and a feeding-trough", CRATE,
                   "A trough - a man-made trough - full of meat, and a cloak-pin shaped like a dragon's eye. Somebody keeps this nest."),
            end_talk('es_brand', "Tell Brand", "A dragon's eye. Thorvald up at Fort Veldon sent word of a preacher with the same mark, in the Vendo Caverns. They're spreading.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [n3, n4]}}, requires='es_drakelings')

n5 = z.item("Wyrm-Tongue's Whistle", 'gem', 16, 'charm', "A bone whistle. The drakelings would come if you blew it. Don't.")
n6 = z.item("Vasudheim Huscarl Mantle", 'cloak', 16, 'ward', "Royal blue, the King's own huscarls.")
n7 = z.item("Brood-Breaker's Torc", 'neck', 16, 'might', "Iron, with a silver scale hammered flat into it.")
z.quest('es_wyrm_tongue', 'The Brood-Keeper', 16, 'es_brand',
        "The nest's keeper comes at dusk to feed them - a drakulv missionary, the farmers say, in a red-scaled cloak, on his way north from Gotar. He'll have his brood round him.\n\nBring friends. Will you [wait for him at dusk]?",
        'wait for him at dusk',
        "A drakulv missionary keeps the drakeling nest by Nisse's Lair on his way north from Gotar.",
        [
            boss(Z, P(990, 1160), "Defeat Ottar Wyrm-Tongue at the nest", "The missionary falls into his own trough. His whistle rolls out of his hand.",
                 'Ottar Wyrm-Tongue', PREACHER, 17, "A man in a red-scaled cloak whistles, and the drakelings come running: 'Little ones. Supper's here.'",
                 objective='Defeat Ottar Wyrm-Tongue', hp=2.4, adds=[(60160533, 'envy drakeling', [13, 14])], every=30, count=2),
            end_talk('es_brand', "Tell Huscarl Brand", "He had a pass on him - svartalf work, from the trading-post in Gotar. The svartalf carry them north and the drakulv ride along.\n\nGotar, then. That's where this road starts.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [n5, n6, n7]}}, requires='es_silverscales', group=True)
