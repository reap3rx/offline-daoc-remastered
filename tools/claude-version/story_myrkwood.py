"""Myrkwood Forest's story quests (claude 2026-11-25, "Midgard - the plan", round 2) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_myrkwood

Deadly, and Midgard's HARD START at Galplen: three short quests on Galplen's doorstep (frogs, myrkcats, carrion eaters) walk a
new character round the town; after that everything is the zone's own level. Where the threads cross: the werewolves of the west
wood (Fenrir's kin, who answer to Hati in Raumarik) and the drakulv missionaries camped with the svartalf in the south (who answer
to the Hierophant in Malmohus) both hunt the same old seer - Volva Groa in the willow-wood, who knows how each of them ends, and
the second half of the dragon's true name.

The zone's two older quests are kept as they were (willow_voice, mora).

Arcs (recommended levels): Galplen's Doorstep (2-7, the hard start), The Willow-Wood and the Volva (23-26), The Dead of the
Barrows (25-28), The West Wood (27-31), The Missionaries (28-32).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(105, 'Myrkwood Forest', 'mid_myrkwood', 'story105_myrkwood', {'willow_voice', 'mora'},
          {'ottar', 'sunniva', 'asgerd', 'grimkel'},
          {'Willow-Heart Pendant', 'Weeping-Sap Ring', "Woodcutter's Belt", "Sunniva's Ribbon", 'Hair-Bridle Bracer',
           "Mare-Queen's Veil", 'Dreamless Ring', 'Hoofprint Pendant'}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157

person('mw_brand', 'Woodward Brand', (1105, 600), 'm', 30, model=M, guild='the Galplen Woodwards',
       idle="New to Myrkwood? Stay near the town till you can hold an axe. Then stay near the town anyway.")
person('mw_thora', 'Woodward-Captain Thora', (1080, 615), 'f', 44, model=F, guild='the Galplen Woodwards',
       idle="The Woodwards keep the roads open. Lately, the roads keep closing.")
person('mw_groa', 'Volva Groa', (620, 520), 'f', 50, model=OLD, guild='the Seidr-Folk',
       idle="Sit, if you like. Everyone comes to the volva in the end. Wolves and priests too.")
person('mw_kalf', 'Woodward Kalf', (850, 920), 'm', 34, model=M, guild='the Galplen Woodwards',
       idle="Gna Faste was a watch-tower once. Now it's where we watch the south.")

# ======================================================================== Galplen's Doorstep (2-7) - the hard start
h1 = z.item("Woodward's Token Ring", 'ring', 5, 'ward', "Plain iron. Every new face at Galplen gets one.")
h2 = z.item("Frog-Skin Sash", 'belt', 5, 'charm', "Green, and still faintly damp.")
z.quest('mw_frogs', 'Frogs in the Well', 2, 'mw_brand',
        "Welcome to the darkest corner of Midgard. You'll want to start small. The giant bull frogs from the marsh get into the town's well-stream and foul it.\n\nWill you [chase off the frogs]? Stay close to town - nowhere else in Myrkwood is safe for you yet.",
        'chase off the frogs',
        "Giant bull frogs foul Galplen's well-stream. A first task for a new arrival.",
        [
            hunt((1180, 530), "Chase off the giant bull frogs near Galplen " + where((1180, 530), 'mw_brand'), 'giant bull frog', 4),
            end_talk('mw_brand', "Tell Woodward Brand", "Good. You're still alive. That's the first lesson of Myrkwood.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'choice': [h1, h2]}})

h3 = z.item("Myrkcat Whisker Charm", 'gem', 5, 'finesse', "Long black whiskers bound in silver wire.")
h4 = z.item("Lantern-Bearer's Bracer", 'bracer', 5, 'ward', "Soot-black leather.")
z.quest('mw_myrkcats', 'Eyes in the Dark', 4, 'mw_brand',
        "Myrkcats stalk the town's edge at night - you see their eyes in the dark, then you don't see your goats. Small ones, near the town. The big ones live deeper in. Don't go there.\n\nWill you [hunt the myrkcats]?",
        'hunt the myrkcats',
        "Myrkcats stalk Galplen's edge at night and take the goats.",
        [
            hunt((1000, 500), "Hunt the myrkcats near Galplen " + where((1000, 500), 'mw_brand'), 'myrkcat', 4),
            end_talk('mw_brand', "Tell Woodward Brand", "Goats are safe. You're learning. The Captain has something for you.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'choice': [h3, h4]}}, requires='mw_frogs')

h5 = z.item("Thora's Spare Axe-Belt", 'belt', 7, 'might', "Worn, mended, reliable.")
h6 = z.item("Galplen Watch-Cloak", 'cloak', 7, 'ward', "Woodward green, with a black tree on the back.")
h7 = z.item("Carrion-Feather Torc", 'neck', 7, 'might', "Your first proper trophy in Myrkwood.")
z.quest('mw_carrion', 'Carrion on the Road', 7, 'mw_thora',
        "Carrion eaters gather on the east road, where travellers die. They've learned to wait for the next one. Teach them otherwise and you've earned a place at our fire.\n\nWill you [clear the road]? Then come back - I'll tell you what Myrkwood's really about.",
        'clear the road',
        "Carrion eaters wait on Galplen's east road for the next traveller to die.",
        [
            hunt((1250, 700), "Drive off the carrion eaters " + where((1250, 700), 'mw_thora'), 'carrion eater', 4),
            end_talk('mw_thora', "Tell Woodward-Captain Thora", "That'll do. Welcome to Myrkwood.\n\nHere's what it's about: there's an old volva in the willow-wood west of town, Groa. Wolves and priests both want her. When you're strong enough, she's who we protect.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'items': [h7], 'choice': [h5, h6]}}, requires='mw_myrkcats')

# ======================================================================== The Willow-Wood and the Volva (23-26)
w1 = z.item("Willow-Bark Bracer", 'bracer', 23, 'ward', "Bark that still weeps sap.")
w2 = z.item("Haunt-Ward Charm", 'gem', 23, 'faith', "A rune-stone wrapped in red thread.")
z.quest('mw_haunts', 'The Willow Road', 23, 'mw_thora',
        "The road to the volva's hut runs through the willow-wood, and the haunts walk it. Groa sends for supplies and nobody will carry them.\n\nWill you [clear the road]?",
        'clear the road',
        "Haunts walk the willow-wood road between Galplen and the volva's hut.",
        [
            hunt((800, 560), "Clear the haunts from the willow road " + where((800, 560), 'mw_thora'), 'haunt', 4),
            reach(Z, P(640, 530), "Carry the supplies to the volva's hut", "A hut of turf and willow, smoke curling from the roof. An old woman watches you from the door as if she knew you were coming.", r=30),
            end_talk('mw_groa', "Speak with Volva Groa", "There you are. You took longer than I saw. Sit down.\n\nYou'll want to know why everyone's hunting an old woman. Bring me something first, and I'll tell you.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'choice': [w1, w2]}}, requires='mw_carrion')

w3 = z.item("Weeping-Heart Ring", 'ring', 24, 'mind', "Willow-wood, the grain like tear-tracks.")
w4 = z.item("Volva's Herb-Belt", 'belt', 24, 'faith', "Hung with little bags of bitter herbs.")
z.quest('mw_willows', 'Willow-Heart', 24, 'mw_groa',
        "The weeping willows grow toward my hut a little every year. They want what I know, like everyone. Cut me a willow-heart - the wood at the centre - and I'll burn it, and they'll remember their place.\n\nWill you [cut a willow-heart]?",
        'cut a willow-heart',
        "The weeping willows of Myrkwood grow toward the volva's hut.",
        [
            hunt((700, 650), "Fell the weeping willows " + where((700, 650), 'mw_groa'), 'weeping willow', 5),
            end_talk('mw_groa', "Bring the willow-heart to Volva Groa", "Good. Now listen.\n\nI see how things end. The wolves want me because I see how Hati ends - the wolf that hunts the moon, Fenrir's son, in Raumarik. The priests want me because I know the rest of the dragon's name. Gjalpinulva. Her true name, the one that wakes her. They have half.", 'default'),
        ],
        {'default': {'text': "From the Seidr-Folk.", 'choice': [w3, w4]}}, requires='mw_haunts')

w5 = z.item("Tingler-Silk Mantle", 'cloak', 26, 'ward', "Shimmering, and faintly sticky.")
w6 = z.item("Seidr Thread-Ring", 'ring', 26, 'mind', "A ring of spun seidr, cold as moonlight.")
z.quest('mw_tinglers', 'Tinglers in the Hollows', 26, 'mw_groa',
        "The tinglers in the western hollows feed on fear. There's a lot of fear in Myrkwood now, and they've grown fat on it. They come to my door at night.\n\nWill you [hunt them]?",
        'hunt them',
        "Tinglers in Myrkwood's western hollows have grown fat on the forest's fear.",
        [
            hunt((350, 650), "Hunt the tinglers " + where((350, 650), 'mw_groa'), 'tingler', 5),
            end_talk('mw_groa', "Tell Volva Groa", "Fewer. Fear's the coin of the times, I'm afraid. Wolves and dragons both deal in it.", 'default'),
        ],
        {'default': {'text': "From the Seidr-Folk.", 'choice': [w5, w6]}}, requires='mw_willows')

# ======================================================================== The Dead of the Barrows (25-28)
d1 = z.item("Barrow-Iron Ring", 'ring', 25, 'might', "Cold iron, out of a dead man's hoard.")
d2 = z.item("Grave-Ward Belt", 'belt', 25, 'faith', "Rune-stitched against the walking dead.")
z.quest('mw_norsemen', 'The Barrow-Dead', 25, 'mw_kalf',
        "The decaying norsemen have come out of the barrows south of Gna Faste. The dead don't walk in Myrkwood without a reason. Something's waking them.\n\nWill you [put them down]?",
        'put them down',
        "Decaying norsemen have come out of the barrows south of Gna Faste.",
        [
            hunt((1000, 1050), "Put down the decaying norsemen " + where((1000, 1050), 'mw_kalf'), 'decaying norseman', 4),
            end_talk('mw_kalf', "Tell Woodward Kalf", "Down. But they keep coming. The barrows are warm, Kalf says - me, I mean. I'm Kalf. They're warm.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'choice': [d1, d2]}})

d3 = z.item("Myrk-Shadow Veil Charm", 'gem', 27, 'mind', "A scrap of shadow that doesn't fade in daylight.")
d4 = z.item("Barrow-Warm Bracer", 'bracer', 27, 'ward', "Bronze, still warm from the barrow.")
z.quest('mw_shadows', 'Warm Barrows', 27, 'mw_kalf',
        "The myrk shadows guard the barrows - and the barrows are warm. Get past them and look inside one. I want to know why the ground's warm.\n\nWill you [look inside]?",
        'look inside',
        "Myrk shadows guard Myrkwood's barrows, and the barrows are warm.",
        [
            hunt((1150, 1100), "Get past the myrk shadows " + where((1150, 1100), 'mw_kalf'), 'myrk shadow', 4),
            search(Z, P(1160, 1110), "Search inside a barrow", "a burial chamber, its stones scorched", CRATE,
                   "The dead man's hoard is gone, and the walls are scorched in long claw-marks. Drakelings, digging for gold. The svartalf in the south pay the drakulv in grave-gold."),
            end_talk('mw_kalf', "Tell Kalf", "Grave-robbing drakelings, digging gold for the cult. And the dead wake angry. The missionaries camp in the south-east - Captain Thora will want to hear.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'choice': [d3, d4]}}, requires='mw_norsemen')

# ======================================================================== The West Wood (27-31)
f1 = z.item("Worg-Hide Mantle", 'cloak', 27, 'ward', "Grey worg-hide, thick and rank.")
f2 = z.item("Worg-Tooth Ring", 'ring', 27, 'might', "A great worg tooth bound in iron.")
z.quest('mw_worgs', 'The Worg Run', 27, 'mw_thora',
        "The worgs in the middle wood run with the werewolves now. They scout for them - every pack we see, there's a werewolf a mile behind.\n\nWill you [break the packs]?",
        'break the packs',
        "Gray worgs in Myrkwood's middle wood scout for the werewolves of the west wood.",
        [
            hunt((750, 1000), "Break the gray worg packs " + where((750, 1000), 'mw_thora'), 'gray worg', 5),
            end_talk('mw_thora', "Tell Captain Thora", "Broken. Now they're blind. Groa says they're coming for her soon - before the next full moon.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'choice': [f1, f2]}}, requires='mw_willows')

f3 = z.item("Fenris-Kin Fang Torc", 'neck', 29, 'might', "A werewolf's fang, longer than your finger.")
f4 = z.item("Moon-Ward Bracer", 'bracer', 29, 'faith', "Silver, worked with Groa's runes.")
f5 = z.item("Wolf-Breaker's Belt", 'belt', 29, 'finesse', "Studded with silver.")
z.quest('mw_werewolves', "Fenrir's Kin", 29, 'mw_groa',
        "The werewolves of the west wood call themselves Fenrir's kin. They answer to Hati, in Raumarik, and Hati wants to know how he ends - so he can change it.\n\nBring friends. Will you [hunt the werewolves]?",
        'hunt the werewolves',
        "The werewolves of Myrkwood's west wood, Fenrir's kin, hunt the volva for Hati in Raumarik.",
        [
            hunt((380, 1050), "Hunt the werewolves of the west wood " + where((380, 1050), 'mw_groa'), 'werewolf', 3),
            hunt((380, 1050), "Bring down the werewolf nobles", 'minor werewolf noble', 2),
            search(Z, P(400, 1060), "Search the werewolf den", "a moon-carved bone", CRATE,
                   "A wolf's shoulder-blade carved with the moon in every phase, and the last one gnawed away. Scratched under it: 'THE SEER SAYS HOW HATI ENDS. TAKE HER TO RAUMARIK BEFORE THE WINTER.'"),
            end_talk('mw_groa', "Tell Volva Groa", "Raumarik, before the winter. And Hati asks me how he ends. Well. I'll tell you instead, when the time comes - you'll be the one there.", 'default'),
        ],
        {'default': {'text': "From the Seidr-Folk.", 'choice': [f3, f4, f5]}}, requires='mw_worgs', group=True)

f6 = z.item("Mora-Dream Ring", 'ring', 30, 'mind', "Wear it to sleep. You won't dream.")
f7 = z.item("Dark-Hound Collar Torc", 'neck', 30, 'might', "Black iron spikes.")
z.quest('mw_mora_dancers', 'The Night-Riders', 30, 'asgerd',
        "The mora dance in the south now - not just riding men's dreams but dancing in the open, with dark hounds round them. They're stirred up.\n\nWill you [break the dance]?",
        'break the dance',
        "The mora dance openly in Myrkwood's south, with dark hounds round them.",
        [
            hunt((950, 1350), "Break the mora dancers " + where((950, 1350), 'asgerd'), 'mora dancer', 4),
            hunt((950, 1400), "Kill the dark hounds", 'dark hound', 3),
            end_talk('asgerd', "Tell Asgerd", "Quiet. I slept last night - first time in a month. Thank you.", 'default'),
        ],
        {'default': {'text': "From the Seidr-Folk.", 'choice': [f6, f7]}}, requires='mora')

# ======================================================================== The Missionaries (28-32)
m1 = z.item("Watcher's Dark-Iron Ring", 'ring', 28, 'finesse', "Svartalf dark-iron.")
m2 = z.item("South-Road Woodward Cloak", 'cloak', 28, 'ward', "Green and black, the Woodwards' colours.")
z.quest('mw_watchers', 'The Watchers', 28, 'mw_kalf',
        "Svartalf watchers in the south, between Gna Faste and the missionaries' camp. They watch the volva's road, and they report to the camp.\n\nWill you [blind the watchers]?",
        'blind the watchers',
        "Svartalf watchers in Myrkwood's south watch the volva's road for the drakulv missionaries.",
        [
            hunt((1200, 1330), "Blind the svartalf watchers " + where((1200, 1330), 'mw_kalf'), 'svartalf watcher', 5),
            end_talk('mw_kalf', "Tell Woodward Kalf", "Blind. Now they'll have to come in person. Good - I'd rather see them coming.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'choice': [m1, m2]}}, requires='mw_shadows')

m3 = z.item("Predator's Hook-Bracer", 'bracer', 31, 'might', "A svartalf predator's hooked bracer.")
m4 = z.item("Missionary-Scale Pendant", 'neck', 31, 'mind', "A red dragon-scale, warm on the skin.")
m5 = z.item("Woodward-Captain's Ring", 'ring', 31, 'ward', "Thora's own ring. She has another.")
z.quest('mw_missionaries', "The Missionaries' Orders", 31, 'mw_thora',
        "The missionaries' camp in the south-east. A Wyrm-Deacon leads them, with svartalf predators for his hunters. Break the predators and get me their orders.\n\nBring friends. Will you [take the orders]?",
        'take the orders',
        "Gjalpinulva's missionaries camp in Myrkwood's south-east, with svartalf predators for hunters.",
        [
            hunt((1250, 1350), "Break the svartalf predators " + where((1250, 1350), 'mw_thora'), 'svartalf predator', 2),
            search(Z, P(1110, 1330), "Search the edge of the missionaries' camp", "a scroll-case marked with a dragon's eye", BEDROLL,
                   "Orders, in the Hierophant's hand: 'Bring the volva to Malmohus alive. With her half of the name and ours, the Mother wakes. Let the wolves have the north; we shall have everything.'"),
            end_talk('mw_thora', "Tell Woodward-Captain Thora", "The Hierophant, in Malmohus. They mean to wake Gjalpinulva with Groa's half of the name - and the wolves mean to drag her to Hati.\n\nWe hold Galplen, and we keep Groa. Everything past Myrkwood - Raumarik, Malmohus - is a war for the King's huscarls. But it starts here.", 'default'),
        ],
        {'default': {'text': "From the Galplen Woodwards.", 'choice': [m3, m4, m5]}}, requires='mw_watchers', group=True)
