"""Silvermine Mountains' story quests (claude 2026-11-22, the zone brief in Zone Reviews) - see story_gen.py. Places: zone
metres [x, y].

Moved out of story_hib.py with the Silvermine rebuild, like Lough Derg and Connacht:
    python tools/claude-version/story_gen.py story_silvermine

Six arcs, 23 quests, one thread: digging past the old silver, the sheevra broke into a sealed vein of moon-silver. That woke
the stones, let the deamhan out of the deep and brought down the miners' camp. Now the sheevra sell the moon-silver to rogue
druids, who carry it to the Azure Order in Connacht for their fires - the two zones' stories meet there. Two old quests are
folded in: The Walking Stones (walking_stones) and The Sheevra's Miners (sheevra_mine). The Mine-Wardens of Howth's arcs:
Howth's Troubles, The Spraggon Den, The Sheevra's Miners. The Order of the Rowan's (shared with Connacht): The Walking
Stones, The Fallen Camp, The Rogue Druids.
"""
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE = 1882, 1876, 1347
M, F, OLD = 337, 365, 362
Z = 201
ZONES = []

z = Zone(Z, 'Silvermine Mountains', 3, 'hib_silvermine')
ZONES.append(z)


def hunt(at, goal, target, count, text=None, give=None):
    """A kill step on the zone's own monsters (they scale to you)."""
    s = {'type': 'kill', 'zone': Z, 'at': list(at), 'radius': 40, 'goal': goal, 'target': target, 'count': count}
    if text:
        s['text'] = text
    if give:
        s['give'] = {'name': give}
    return s


def gives(step, name):
    step['give'] = {'name': name}
    return step


def wake(ending, chain):
    ending['wake_event'] = chain
    return ending


# ------------------------------------------------------------------ people
# Howth
z.npc('sm_fionnbarr', 'Warden-Captain Fionnbarr', [575, 1086], 'm', 30, guild='Mine-Wardens of Howth',
      idle="Howth and Ardagh pay us in silver to keep the mines safe. Lately we're earning it.")
z.npc('breasal', 'Breasal the Stonemason', [570, 1074], 'm', 10, idle="My grandfather raised that circle with his own two hands. Now it's walked off.")
z.npc('grainne', 'Grainne', [552, 1093], 'f', 14, idle="Cathal went up the mountain to look for silver. The sheevra found him first.")
z.npc('odhran', 'Ranger Odhran', [580, 1066], 'm', 20, idle="The sheevra mine the east slopes. They take what they need. Lately that includes people.")
# Ardagh, the sentinel post, the ranger's post, the miners' cairn
z.npc('sm_maeve', 'Mine-Steward Maeve', [815, 120], 'f', 22, guild='Mine-Wardens of Howth',
      idle="Forty picks, thirty shovels, a dozen lamps. Every one of them stolen this month. Every one.")
z.npc('sm_ailbe', 'Sentinel Ailbe', [520, 615], 'm', 16, guild='Mine-Wardens of Howth',
      idle="The road-gang watches us from the trees. We watch them back. It's a very boring war.")
z.npc('sm_cliodhna', 'Muirne of the Rowan', [500, 1448], 'f', 30, model=OLD, guild='Order of the Rowan',
      idle="Druids who sell the land's own silver to the Azure Order. I taught some of them. I'll unteach them.")
z.npc('sm_ethna', 'Sister Ethna', [1200, 1170], 'f', 26, model=OLD, guild="the Miners' Cairn",
      idle="Forty-one names on the cairn. I say every one of them every night. Some nights they answer.")
# out in the valley - quest givers you come across as you explore (owner 2026-11-23: "the quests are scattered
# throughout the zone as much as we can, so that it brings interest and reason to explore the zone")
z.npc('sm_tadhg', 'Miner Tadhg', [620, 440], 'm', 12, idle="Forty tins. FORTY. That badger eats better than I do.")
z.npc('sm_senan', 'Foreman Senan', [1170, 930], 'm', 18, guild='Mine-Wardens of Howth',
      idle="Keep your head down on this road. They don't miss much, those archers.")
z.npc('sm_fiacc', 'Trapper Fiacc', [1150, 640], 'm', 20, idle="Big as a pony, that badger. I've set traps for him. He eats the traps.")
z.npc('cathal', 'Cathal', [1450, 1066], 'm', 12, during=['sheevra_mine/cathal'])

# ======================================================================== the road to Howth (a Wild start in Ardagh, owner 2026-11-23:
# "It's small, I know, but I kind of wanted that with the Wild zone start, like it's a little barren and you travel to Howth")
z.quest('sm_road_to_howth', 'The Road to Howth', 1, 'sm_maeve',
        "New to Ardagh? It's not much - a mine-steward, a smith and a lot of wind. The Mine-Wardens hold Howth, down the valley, and that's where the work is.\n\nWill you [carry my letter] to Warden-Captain Fionnbarr in Howth? Keep to the road south. The Stone Fields are on your right - don't stop to look at the stones. They look back.",
        'carry my letter',
        "Mine-Steward Maeve in Ardagh has a letter for Warden-Captain Fionnbarr in Howth, down the valley.",
        [
            end_talk('sm_fionnbarr', "Take Maeve's letter to Warden-Captain Fionnbarr in Howth, about 1 km south down the road", "From Maeve? 'Spraggons in the tool-sheds again, send help.' She always says that.\n\nYou walked down from Ardagh on your own? Good. We've need of anyone who can. Look around Howth - there's work for you, and more out in the valley.", 'default'),
        ],
        {'default': {'text': "Here - for the walk.", 'choice': []}})

# ======================================================================== Howth's Troubles (3 to 8) - Mine-Wardens
a1 = z.item("Storekeeper's Key-Ring", 'ring', 3, 'ward', "Every lock in Ardagh's stores. Most of them still work.")
a2 = z.item("Rat-Catcher's Bracer", 'bracer', 3, 'finesse', "Scratched to ribbons. The rats lost.")
z.quest('sm_rats_in_the_stores', 'Rats in the Stores', 3, 'sm_fionnbarr',
        "The miners' stores south of town have rat boys in them - not rats, rat BOYS, those little vermin-men from the south fields. They're eating the miners' flour and chewing the lamp-wicks.\n\nNot the Wardens' proper work, but somebody has to. Will you [clear the stores]?",
        'clear the stores',
        "Rat boys have got into Howth's mining stores.",
        [
            hunt([640, 1160], "Kill 4 rat boys in the stores, about 80 m south-east of Howth", 'rat boy', 4),
            search(Z, [645, 1165], "Search the gnawed sacks in the stores (click the glinting spot)", "a gnawed flour sack", CRATE,
                   "Flour everywhere - and in it, glittering, a pinch of pale silver dust. Not Howth silver. Too pale. It glows a little in the dark.",
                   give='a pinch of pale silver dust'),
            end_talk('sm_fionnbarr', "Report to Warden-Captain Fionnbarr in Howth", "Silver dust in the flour? That's... odd. Rat boys don't mine.\n\nPale, you say. Glows. I've heard old miners talk of silver like that - moon-silver, from deep down where nobody should dig. Probably nothing. Take this.", 'default'),
        ],
        {'default': {'text': "From the Wardens.", 'choice': [a1, a2]}})

a3 = z.item("Lookout's Signal Mirror", 'gem', 5, 'charm', "A scrap of polished silver the lookout used to flash signals. You can see your own nose in it.")
a4 = z.item("Sentinel-Post Belt", 'belt', 5, 'might', "Issue gear from the sentinel post. Ailbe's spare.")
z.quest('sm_sentinel_post', 'The Sentinel Post', 5, 'sm_ailbe',
        "There's a road-gang camped in the trees just west of this post, and they've started robbing miners on the way to work. I hold the post with three men and a dog.\n\nThey've a lookout on a stump who flashes a mirror when we move. Will you [help hold the road]? Take out the youths first, then the lookout - or he'll have them all running.",
        'help hold the road',
        "A road-gang just west of Sentinel Ailbe's post robs miners on their way to work.",
        [
            hunt([420, 640], "Kill 4 villainous youths at the road-gang's camp, about 100 m west of Sentinel Ailbe", 'villainous youth', 4),
            hunt([420, 640], "Defeat the road-gang lookout at the same camp", 'road-gang lookout', 1,
                 text="The lookout drops his mirror. It's silver - pale silver - and on the back is scratched 'from the diggings, for the road'."),
            end_talk('sm_ailbe', "Bring the lookout's mirror to Sentinel Ailbe at the sentinel post", "Pale silver. A road-gang paid in silver from the diggings?\n\nSomebody up east has more silver than sense. Warden-Captain Fionnbarr down in Howth will want to hear of it. Good work.", 'default'),
        ],
        {'default': {'text': "From the post - and from the dog, who likes you.", 'choice': [a3, a4]}})

a5 = z.item("Lunch-Tin Charm", 'gem', 8, 'ward', "A miner's lunch-tin lid, dented by a badger's teeth. It still smells faintly of cheese.")
a6 = z.item("Stinky's Collar Ring", 'ring', 8, 'finesse', "Stinky's own collar, cut down. Somebody once loved that badger. Probably.")
a7 = z.item("Badger-Brush Sash", 'belt', 8, 'might', "Made from Stinky's shed fur. It does not smell of roses.")
z.quest('sm_stinky', 'Stinky', 8, 'sm_tadhg',
        "There's a badger up the hill there, north-west - Stinky, we call him. Huge, filthy and clever. He steals our lunch-tins - dozens of them - and carries them off to his sett.\n\nWe're hungry and we're furious. Will you [deal with Stinky]? And bring back the tins.",
        'deal with Stinky',
        "Stinky, a huge and clever badger, steals the miners' lunch-tins. Miner Tadhg wants them back.",
        [
            hunt([506, 358], "Defeat Stinky, the badger, at his sett about 140 m north-west of Miner Tadhg", 'Stinky', 1),
            search(Z, [510, 362], "Search Stinky's sett (click the glinting spot)", "a heap of lunch-tins", CRATE,
                   "Forty lunch-tins, licked clean. In the bottom of one, a lump of pale silver the size of a thumb - and a miner's name scratched on the lid: Cathal.",
                   give="Cathal's lunch-tin"),
            end_talk('sm_tadhg', "Bring the lunch-tins to Miner Tadhg, south-east of Stinky's sett", "Cathal's tin. Grainne's man, from Howth - the one the sheevra took.\n\nAnd moon-silver in it. Whatever the sheevra have found up east, it's coming down the mountain one pinch at a time. Grainne should have this tin.", 'default'),
        ],
        {'default': {'text': "Take this. The lads send their thanks - and their lunch.", 'choice': [a5, a6, a7]}})

# ======================================================================== The Walking Stones (3 to 10) - Rowan
b1 = z.item("Creeping-Pebble Charm", 'gem', 4, 'charm', "A pebble that inched across your palm while you weren't looking.")
b2 = z.item("Field-Wall Bracer", 'bracer', 4, 'ward', "Dry-stone walling, the farmers' way. Not one stone moved.")
z.quest('sm_creeping_stones', 'Creeping Stones', 4, 'breasal',
        "Before you ask about my grandfather's circle - there's worse. The little stones in the fields north of town creep at night. Farmers find walls fallen and furrows filled in.\n\nWill you [catch the stones] at it? Bring me one. A small one.",
        'catch the stones',
        "Small stones creep across the Stone Fields at night, knocking down walls.",
        [
            hunt([450, 800], "Break 4 small walking rocks in the Stone Fields, about 330 m north-west of Howth", 'small walking rock', 4),
            search(Z, [455, 805], "Pick up a still stone in the Stone Fields (click the glinting spot)", "a still, warm stone", CRATE,
                   "A small stone, warm as a hand. In a crack on its underside, a fleck of pale silver, glowing.",
                   give='a warm stone'),
            end_talk('breasal', "Bring the stone to Breasal the Stonemason in Howth", "Warm. Stones aren't warm.\n\nAnd what's that in the crack? Silver? ...Grandfather used to say the old stones had hearts. I thought he meant it nicely.", 'default'),
        ],
        {'default': {'text': "Take this, for your trouble.", 'choice': [b1, b2]}})

b3 = z.item("Stone-Song Torc", 'neck', 6, 'mind', "Seireadan's voice, caught in a ring of granite. It hums when the stones move.")
b4 = z.item("Singer's Pebble Ring", 'ring', 6, 'faith', "Polished smooth by a hundred years of singing.")
z.quest('sm_seireadan', 'The Stone-Singer', 6, 'breasal',
        "The old stories say Seireadan sings to the stones. A creature of the west fields, older than Howth. If anything is waking them, it's that song.\n\nWill you [silence Seireadan]? He haunts the far west, past the lough.",
        'silence Seireadan',
        "Seireadan, an old creature of the west, sings to the stones - and they've started to answer.",
        [
            hunt([168, 923], "Defeat Seireadan, the stone-singer, about 470 m west of Howth", 'Seireadan', 1, give="Seireadan's singing stone",
                 text="Seireadan falls silent, and in the quiet you hear it: the stones are still singing, without him. Something else is calling them now."),
            end_talk('breasal', "Return to Breasal the Stonemason in Howth", "Still singing? Without him?\n\nThen it isn't Seireadan. It's something they're singing TO. Gods. My grandfather's circle walked off last week. I didn't want to believe it was all one thing.", 'default'),
        ],
        {'default': {'text': "Take this.", 'choice': [b3, b4]}},
        requires='sm_creeping_stones')

# (The Walking Stones, folded in)
it_ogham = z.item('Ogham-Stick Charm', 'gem', 8, 'mind', "A stick notched with ogham. It reads 'wake', and then, newly carved beneath, 'sleep'.")
it_menhir2 = z.item("Mason's Plumb-Ring", 'ring', 8, 'might', "A mason's plumb-bob, worn as a ring. It always hangs true.")
it_walk = z.item('Walking-Stone Belt', 'belt', 8, 'ward', "Pebbles shed by a walking stone, strung on leather. They shift a little at night.")
it_lough = z.item("Lough-Water Cloak", 'cloak', 8, 'faith', "Damp, always, but never cold.")
z.quest('walking_stones', 'The Walking Stones', 8, 'breasal',
        "My grandfather's stone circle, up on the northern slopes - every stone of it got up and walked off last week. Seven standing stones, gone. Left their sockets like pulled teeth.\n\nThe little walking rocks have been seen west of here. Stones don't walk on their own. Someone woke them. Will you [find the stones]?",
        'find the stones',
        "Breasal's grandfather's stone circle got up and walked away. Someone woke the stones.",
        [
            reach(Z, [630, 360], "Go to the empty stone circle in the north, about 300 m south-west of Ardagh", "Seven sockets in the turf, deep and fresh. Tracks - round, heavy, rolling tracks - going south-west.", r=20),
            kill(Z, [484, 706], "Break 6 walking stones in the Stone Fields, about 400 m north of Howth", 'small walking rock', 60166254, [5, 6], 6,
                 text="They topple, and lie still, and are only stones. But there are fresh ogham marks on every one."),
            search(Z, [500, 640], "Search where the stones gathered, a little north in the Stone Fields (click the glinting spot)", "a freshly carved ogham stick", CRATE,
                   "An ogham stick: 'WAKE AND WALK, IN THE NAME OF GRUGOCH.' Spraggon work - bad spelling and all. Tied to it, a thread of pale silver wire.",
                   give='an ogham stick'),
            kill(Z, [518, 616], "Kill 5 spraggonolls at the north end of the Stone Fields", 'spraggonoll', 60166491, [7, 8], 5),
            boss(Z, [470, 560], "Defeat the spraggon chief, about 550 m north of Howth", "Grugoch sits down hard. 'Fine! FINE! The silver told me to! It sings! They wanted to see the lough anyway! They TOLD me!'",
                 'Chief Grugoch', 60166485, 10, "A spraggon in a crown of pebbles hops onto a boulder. 'My stones! I woke them! They're MINE!'",
                 objective='Defeat Chief Grugoch', hp=2.0, adds=[(60166491, 'spraggonoll', [7, 8])], every=30, count=1),
            choice('breasal', "Bring the ogham stick to Breasal the Stonemason in Howth",
                   "The spraggon said the stones WANTED to walk? To see the lough? And the silver told him to?\n\nGrandfather used to say they were restless. I thought it was a story.\n\nWith that stick I can [put them to sleep] - back in the circle, standing, forever. Or I could [let them walk] to the lough, and grandfather's circle stands empty. Gods. I'm a mason. I didn't think I'd have to ask stones what they want.",
                   [('put them to sleep', "Back in the circle, then. Sleep well, old ones. You've a job to do.", 'ending:sleep'),
                    ('let them walk', "Then I'll carve 'walk on' on the stick and leave it at the circle. ...They'll be at the lough by midsummer, I'd say. Slow walkers.", 'ending:walk')]),
        ],
        {'sleep': {'text': "Take this, for your trouble.", 'items': [it_ogham], 'choice': [it_menhir2, it_walk]},
         'walk': {'text': "Take this, for your trouble.", 'items': [it_ogham], 'choice': [it_walk, it_lough]}},
        requires='sm_seireadan')

b5 = z.item("Moon-Silver Sliver Pendant", 'neck', 10, 'faith', "The first sliver of moon-silver anyone in Ardagh ever held. It's cold, and it hums, and you can't stop looking at it.")
b6 = z.item("Ring-Warden's Shard Bracer", 'bracer', 10, 'might', "A shard of the ring-stone, bound in leather. It's still a little warm.")
b7 = z.item("Rowan-Bound Belt", 'belt', 10, 'mind', "Muirne's work: rowan bark woven tight. 'Keeps the singing out of your head.'")
z.quest('sm_night_field', 'The Night Field', 10, 'sm_cliodhna',
        "Breasal brought me his warm stone. I know what's in it. Moon-silver - silver from the deep vein under the east mountain, sealed by the old druids a thousand years ago. It sings, and the stones answer.\n\nSomeone has opened the vein. Help me pry the silver out of the stone ring in the fields tonight - it will fight. Will you [stand the night]? Bring a friend.",
        'stand the night',
        "Moon-silver from a sealed vein is waking the stones. Muirne of the Rowan means to pry it out of a stone ring at night.",
        [
            reach(Z, [420, 500], "Go to the stone ring at the north end of the Stone Fields, about 550 m south-west of Ardagh", "A ring of small stones, rocking gently in place like sleepers. In the middle one, a pale light pulses.", r=25),
            defend(Z, [420, 500], "Keep Muirne alive while she pries the silver out of the stones", "The silver comes free with a sound like a bell. Every stone in the ring stops - and the biggest stands up.",
                   'Muirne of the Rowan', 60163820, 12, "Muirne kneels and starts to work. The stones around you begin to grind.",
                   [(60166253, 'small walking rock', [7, 8]), (60166254, 'small walking boulder', [8, 9])], 'Keep Muirne safe', model=F,
                   duration=90, every=25, count=2,
                   then_boss={'tpl': 60167762, 'name': 'the Ring-Warden', 'lv': 12, 'hp': 2.2,
                              'announce': "The ring's oldest stone heaves itself out of the turf. It wants its silver back.",
                              'objective': 'Defeat the Ring-Warden'},
                   thanks="Got it. Got it! Gods, it's cold."),
            end_talk('sm_cliodhna', "Speak to Muirne at the stone ring", "There. Feel it - cold, and singing. This came out of the deep vein, and somebody's selling it by the cartload.\n\nThe sheevra dig in the east. The rogue druids in the hollow have been very rich lately. I'll find out which. Thank you.", 'default'),
        ],
        {'default': wake({'text': "Take this, from the Rowan.", 'items': [b5], 'choice': [b6, b7]}, 'silvermine_stones_walk')},
        requires='walking_stones', group=True)

# ======================================================================== The Spraggon Den (8 to 18) - Mine-Wardens
c1 = z.item("Howth-Stamped Pick Charm", 'gem', 9, 'might', "A pick-head stamped HOWTH, shrunk to a charm. Maeve counted it back in.")
c2 = z.item("Tool-Cache Belt", 'belt', 9, 'finesse', "Every loop holds a tool. The spraggons had good taste in belts.")
z.quest('sm_stolen_tools', 'Stolen Tools', 9, 'sm_maeve',
        "Forty picks. Thirty shovels. A dozen lamps. All stolen this month, all from Ardagh's tool-sheds, all at night.\n\nThe spraggons. I know it's the spraggons - they leave droppings everywhere. Their cache is in the west burrows. Will you [find our tools]?",
        'find our tools',
        "Ardagh's mining tools are being stolen by spraggons.",
        [
            hunt([270, 230], "Kill 4 spraggonites at their tool cache, about 550 m west of Ardagh", 'spraggonite', 4),
            search(Z, [275, 235], "Search the tool cache (click the glinting spot)", "a heap of stolen tools", CRATE,
                   "Picks stamped HOWTH, shovels stamped ARDAGH - and a tally scratched on a board: so many picks to 'the shiny men east', so many lamps.",
                   give='a bundle of stamped picks'),
            end_talk('sm_maeve', "Bring the stolen picks to Mine-Steward Maeve in Ardagh", "'The shiny men east'? The sheevra - in their silver mail.\n\nSo the spraggons steal our tools and sell them to the sheevra, and the sheevra dig our silver with our picks. That's almost clever. I hate it.", 'default'),
        ],
        {'default': {'text': "From Ardagh's sheds, with thanks.", 'choice': [c1, c2]}})

c3 = z.item("Tinker's Ledger-Strap Bracer", 'bracer', 12, 'finesse', "The tinker kept his ledger strapped to his arm. You keep your arm.")
c4 = z.item("Brass-Gear Ring", 'ring', 12, 'mind', "A tiny gear from a spraggon contraption. It turns, very slowly, by itself.")
z.quest('sm_tinker', 'The Spraggon Tinker', 12, 'sm_maeve',
        "Somebody among the spraggons can count, and trade, and keep a tally. Spraggons can't do any of that. Somebody's running them.\n\nThere's a tinker at the den mouth - bigger than the rest, with goggles. Will you [catch the tinker]?",
        'catch the tinker',
        "A spraggon tinker at the den mouth runs the tool trade with the sheevra.",
        [
            hunt([160, 520], "Defeat the spraggon tinker at the den mouth, about 720 m north-west of Howth", 'spraggon tinker', 1, give="the tinker's ledger",
                 text="The tinker falls in a clatter of gears. His ledger lists every pick and lamp - paid for in pale silver dust."),
            end_talk('sm_maeve', "Bring the tinker's ledger to Mine-Steward Maeve in Ardagh", "Paid in silver dust. That pale stuff the Wardens keep finding.\n\nThe tinker's just a trader. The den answers to two bosses - one called, I'm not joking, Boss. The other's Sargoth.", 'default'),
        ],
        {'default': {'text': "Take this.", 'choice': [c3, c4]}},
        requires='sm_stolen_tools')

c5 = z.item("Crown-of-Nails Torc", 'neck', 15, 'might', "Boss's crown, beaten flat into a torc. Fewer nails sticking out now. Mostly.")
c6 = z.item("Boss's Pocket-Watch Charm", 'gem', 15, 'charm', "Stolen from a Howth merchant ten years ago. It's never once told the right time.")
z.quest('sm_boss', 'Boss', 15, 'sm_maeve',
        "Boss. A spraggon who named himself Boss. He wears a crown of nails and sits on a throne of stolen buckets in the northern burrow.\n\nHe takes his cut of every pick the den sells. Will you [depose Boss]?",
        'depose Boss',
        "Boss, the spraggon who named himself Boss, takes a cut of the den's stolen-tool trade.",
        [
            hunt([279, 204], "Defeat Boss beside the spraggon tool cache, about 540 m west of Ardagh", 'Boss', 1, give="Boss's crown of nails",
                 text="Boss topples off his bucket-throne. His crown rolls into the dirt. Under the throne, a sack of pale silver dust."),
            end_talk('sm_maeve', "Bring Boss's crown to Mine-Steward Maeve in Ardagh", "A crown of NAILS. Our nails.\n\nOne more. Sargoth, down at the den mouth. The big one. You'll want friends.", 'default'),
        ],
        {'default': {'text': "Take this, and my compliments.", 'choice': [c5, c6]}},
        requires='sm_tinker')

c7 = z.item("Sargoth's Tusk Ring", 'ring', 18, 'might', "A tusk off the biggest spraggon anyone's seen. Polished, it's almost pretty.")
c8 = z.item("Den-Lord's Mantle", 'cloak', 18, 'ward', "Patched from a dozen stolen sacks. Warmer than it looks.")
c9 = z.item("Howth Miners' Token", 'gem', 18, 'faith', "Every miner in Howth chipped in for it. It says 'thank you' in very bad lettering.")
z.quest('sm_sargoth', 'Sargoth', 18, 'sm_maeve',
        "Sargoth rules the den mouth. Every spraggon in the west answers to him, and every stolen pick passes him on the way to the sheevra.\n\nBring friends - lots of them - and [end the den's trade].",
        "end the den's trade",
        "Sargoth rules the Spraggon Den's mouth, and every stolen tool passes him on its way to the sheevra.",
        [
            hunt([160, 520], "Kill 4 spraggonilts at the den mouth, about 720 m north-west of Howth", 'spraggonilt', 4),
            hunt([149, 525], "Defeat Sargoth, just inside the den mouth", 'Sargoth', 1,
                 text="Sargoth falls with a crash that shakes the burrow. Somewhere deep in the den, a lot of spraggons start packing."),
            choice('sm_maeve', "Report to Mine-Steward Maeve in Ardagh",
                   "The den's broken. The tools are coming home in barrow-loads.\n\nThe Wardens say we should [melt the tools] the sheevra touched and forge new ones, clean. The miners say [keep the tools] - a pick's a pick, and silver's silver. What do you think?",
                   [('melt the tools', "Melt them. New picks, clean hands. The smith will be pleased.", 'ending:melted'),
                    ('keep the tools', "Keep them. Miners are practical people. A pick's a pick.", 'ending:kept')]),
        ],
        {'melted': {'text': "Take this, from Ardagh.", 'items': [c9], 'choice': [c7, c8]},
         'kept': {'text': "Take this, from Ardagh.", 'items': [c9], 'choice': [c7, c8]}},
        requires='sm_boss', group=True)

# ======================================================================== The Sheevra's Miners (12 to 26) - Mine-Wardens
d1 = z.item("Silver-Tipped Arrow Charm", 'gem', 13, 'finesse', "An arrowhead of pale silver. The sheevra archers have the best arrows in Hibernia now.")
d2 = z.item("Spoil-Heap Bracer", 'bracer', 13, 'ward', "Dust-grey leather off a sheevra archer. It's been shot at, a lot.")
z.quest('sm_ridge_archers', 'Archers on the Spoil Heaps', 13, 'sm_senan',
        "The sheevra have archers on the spoil heaps just up the road there. They shoot anything that walks - miners, Wardens, a cow last week. Nothing's moved on this road in days.\n\nWill you [clear the spoil heaps]? Bring me one of their arrows. I want to see what they're using.",
        'clear the spoil heaps',
        "Sheevra archers on the spoil heaps shoot at anything on the mine road.",
        [
            hunt([1250, 880], "Kill 5 sheevra archers on the spoil heaps, about 90 m north-east of Foreman Senan", 'sheevra archer', 5, give='a silver-tipped arrow'),
            end_talk('sm_senan', "Bring the sheevra arrow to Foreman Senan on the mine road", "Moon-silver arrowheads. They're tipping ARROWS with it.\n\nThey must have a mountain of the stuff. Grainne in Howth's been asking for help - her Cathal's one of the men they took to dig it.", 'default'),
        ],
        {'default': {'text': "From the Wardens.", 'choice': [d1, d2]}})

# (The Sheevra's Miners, folded in)
it_silver = z.item('Silver-Vein Ring', 'ring', 15, 'might', "Silvermine silver, raw and bright, from a vein no Hibernian has seen in a hundred years.")
it_pick = z.item("Miner's Pick-Bracer", 'bracer', 15, 'ward', "A pick's head, flattened and bent into a bracer.")
it_lamp2 = z.item('Deep-Lamp Pendant', 'neck', 15, 'mind', "A tiny lamp that glows faintly underground.")
it_sheevra = z.item("Sheevra Chief's Belt", 'belt', 15, 'finesse', "Studded with silver nails pulled from the Silvermine rock.")
z.quest('sheevra_mine', "The Sheevra's Miners", 15, 'grainne',
        "My husband Cathal went up the eastern slopes looking for silver. He found the sheevra instead - or they found him. Ranger [Odhran] says they've been taking men to dig for them.\n\nCathal's no fighter. He's barely a miner. Will you [bring him home]?",
        'bring him home',
        "The sheevra have been taking men to work their silver mines. Grainne's husband is one of them.",
        [
            talk('odhran', "Ask Ranger Odhran in Howth about the sheevra",
                 "They've archers on the ridge who'll shoot anything that walks. Get past those and you'll find the miners' tracks east, deep into the hills - the sheevra work their slaves at the far [diggings].", kw='diggings'),
            kill(Z, [1153, 744], "Kill 5 sheevra archers on the ridge, about 650 m north-east of Howth", 'sheevra archer', 60165945, [13, 14], 5),
            search(Z, [1162, 762], "Search the ridge where the archers stood (click the glinting spot)", "a miner's broken pick", CRATE,
                   "A pick with 'CATHAL' scratched on the handle, snapped in two. Chain-marks in the dirt, heading east."),
            reach(Z, [1440, 1050], "Find the sheevra's far diggings, about 840 m east of Howth", "A raw hole in the hillside. Men in chains, hauling rock. Sheevra overseers with whips.", r=20),
            defend(Z, [1450, 1060], "Free the captive miners at the diggings", "The sheevra break and run. The miners drop their chains and sit down, laughing and crying.",
                   'Cathal', 60165947, 12, "You strike the first chain off, and every sheevra in the diggings comes running.",
                   [(60165947, 'sheevra miner', [13, 14])], 'Keep Cathal alive', model=M, duration=80,
                   then_boss={'tpl': 60165946, 'name': 'Chieftain Morc', 'lv': 17, 'announce': "A sheevra in a silver helm. 'My diggers. My silver. MINE.'", 'objective': 'Defeat Chieftain Morc'},
                   thanks="Is it over? Is it really?"),
            L('cathal', choice('cathal', "Talk to Cathal, the freed miner",
                   "I found it, you know. The vein. That's why they kept me. Silver like nobody's seen since my grandfather's day - and below it, the pale stuff, the moon-silver, singing in the rock. Enough to make Grainne and me rich ten times over.\n\nIf we [claim the vein], the sheevra will come back for it. Every year. We'd need guards and walls and we'd never sleep easy. Or we [collapse the mine], and go home poor, and nobody fights over it ever again.",
                   [('claim the vein', "Then I'll stake it today. Grainne will kill me. And then she'll buy a cow. Ten cows.", 'next:claim'),
                    ('collapse the mine', "...Help me with the props. There. Listen to it go. ...Let's go home.", 'next:collapse')])),
            L('claim', end_talk('grainne', "Return to Grainne in Howth", "He's home, and he's RICH, and he's hired six men with spears to guard a hole in a hill.\n\nThe sheevra will come back. He knows. I know. I married a fool. A rich fool. Here - take a share.", 'claim')),
            L('collapse', end_talk('grainne', "Return to Grainne in Howth", "He brought the mountain down on it. All that silver, and he buried it.\n\nAnd then he came home and slept for two days, and when he woke up he asked me what was for supper, like nothing happened. I've never loved him more.", 'collapse')),
        ],
        {'claim': {'text': "Take a share.", 'items': [it_silver], 'choice': [it_pick, it_sheevra]},
         'collapse': {'text': "Take this.", 'items': [it_lamp2], 'choice': [it_pick, it_sheevra]}},
        topics={'Odhran': "The ranger. He's by the stables. He's been watching the east slopes all season."},
        requires='sm_ridge_archers')

d3 = z.item("Scar-Nose's Silver Collar", 'neck', 19, 'might', "A war-badger's collar, sheevra silver. It was made for a neck much thicker than yours.")
d4 = z.item("Badger-Hide Bracer", 'bracer', 19, 'ward', "Thick, scarred and nearly arrow-proof.")
z.quest('sm_scar_nose', 'Scar-Nose', 19, 'sm_fiacc',
        "The sheevra keep a war-badger - Scar-nose, they call him - big as a pony and trained to run down any miner who escapes. He hunts these pastures now, just east of here.\n\nI found what was left of one of those miners last week. Will you [hunt Scar-nose]?",
        'hunt Scar-nose',
        "Scar-nose, the sheevra's war-badger, runs down escaped miners on the High Pastures.",
        [
            hunt([1230, 609], "Defeat Scar-nose, who prowls about 90 m east of Trapper Fiacc", 'Scar-nose', 1, give="Scar-nose's collar",
                 text="Scar-nose goes down at last. His collar is sheevra silver, stamped with a chieftain's mark: Dergal."),
            end_talk('sm_fiacc', "Bring Scar-nose's collar to Trapper Fiacc on the High Pastures", "Dergal's mark. Chieftain Dergal - he holds the main working in the east, they say. His overseer, Camlin, runs the diggings.\n\nWarden-Captain Fionnbarr in Howth will want this collar. Tell him the pastures are safe to cross again.", 'default'),
        ],
        {'default': {'text': "Take this. The pastures thank you.", 'choice': [d3, d4]}})

d5 = z.item("Overseer's Whip-Handle Charm", 'gem', 23, 'charm', "Camlin's whip, the lash cut off. The handle's all that's left. That's enough.")
d6 = z.item("Tally-Keeper's Belt", 'belt', 23, 'mind', "Camlin kept his tallies on a belt of notched leather. Every notch a cartload.")
d7 = z.item("Freed-Miner's Bracer", 'bracer', 23, 'finesse', "The miners Camlin worked gave it to you. They made it from his chains.")
z.quest('sm_overseer', 'The Overseer', 23, 'sm_fionnbarr',
        "Overseer Camlin works the slaves at the far diggings and keeps the sheevra's tallies. Cathal says he goes down to the workings every evening to count the silver.\n\nCatch him at the workings, away from Dergal's huts. Will you [catch Camlin]? Bring me his tallies.",
        'catch Camlin',
        "Overseer Camlin keeps the sheevra's silver tallies and visits the far workings every evening.",
        [
            reach(Z, [1420, 1090], "Go to the far mine workings, about 820 m east of Howth", "Sheevra miners stacking pale ore by lamplight - and an overseer in silver with a whip and a tally-board.", r=25),
            gives(boss(Z, [1425, 1095], "Defeat Overseer Camlin at the far workings", "Camlin falls, wounded, and crawls off into the dark toward the main working. His tally-board stays where it fell.",
                       'Overseer Camlin', 60164801, 24, "'Howth scum? At MY workings?' The overseer snaps his whip.",
                       objective="Defeat Overseer Camlin at the far workings", hp=2.2, adds=[(60165947, 'sheevra miner', [21, 22])], every=30, count=2), "Camlin's tally-board"),
            end_talk('sm_fionnbarr', "Bring the overseer's tally to Warden-Captain Fionnbarr in Howth", "'Moon-silver: forty carts to the druids of the hollow. Paid in blue beads.'\n\nBlue beads. That's the Azure Order's coin - they burn men in wicker over in Connacht. What does a fire-cult want with forty carts of silver?", 'default'),
        ],
        {'default': {'text': "Take this.", 'choice': [d5, d6, d7]}},
        requires='sm_scar_nose')

d8 = z.item("Dergal's Silver Torc", 'neck', 26, 'might', "The war-chief's torc, sheevra silver. Ardagh's smiths say it's the finest they've seen.")
d9 = z.item("Mine-Warden's Mantle", 'cloak', 26, 'ward', "Grey with a silver pick. The Wardens give these to their own.")
d10 = z.item("Lake-Camp Banner Ring", 'ring', 26, 'finesse', "A ring cut from the sheevra lake camp's banner-pole.")
d11 = z.item("Ardagh's Thanks", 'gem', 26, 'faith', "Every miner in Ardagh put a coin in for it. It's mostly coins.")
z.quest('sm_chieftain_dergal', 'Chieftain Dergal', 26, 'sm_fionnbarr',
        "Dergal is mustering his war-band at the lake camp below the mines, to march on Howth before we march on him.\n\nWe hit him there, in the open, before he's ready. Every Warden I have, and every friend you have. Will you [break the muster]?",
        'break the muster',
        "Chieftain Dergal is mustering the sheevra war-band at the lake camp to march on Howth.",
        [
            hunt([1120, 1020], "Kill 4 sheevra swordsmen at the lake camp, about 525 m east of Howth", 'sheevra swordsman', 4),
            boss(Z, [1125, 1015], "Defeat Chieftain Dergal when he comes to the lake camp", "Dergal staggers, roars, and is dragged off by his guards toward the main working, bleeding. The muster breaks.",
                 'Chieftain Dergal', 60159138, 27, "Chieftain Dergal in silver mail: 'Howth's diggers come to ME? Good. Saves me the walk.'",
                 objective="Defeat Chieftain Dergal when he comes to the lake camp", hp=2.6, adds=[(60165949, 'sheevra swordsman', [23, 24]), (60165945, 'sheevra archer', [23, 24])], every=25, count=2),
            end_talk('sm_fionnbarr', "Return to Warden-Captain Fionnbarr in Howth", "He ran. Dragged off by his own guards, bleeding like a stuck pig.\n\nThe muster's broken, the valley's with us. When Howth's ready, we take the mine itself. Take this - and get some sleep.", 'default'),
        ],
        {'default': {'text': "From the Mine-Wardens of Howth.", 'items': [d9], 'choice': [d8, d10, d11]}},
        requires='sm_overseer', group=True)

# ======================================================================== The Fallen Camp (18 to 30) - Rowan
e1 = z.item("Miner's Tally-Stick Charm", 'gem', 19, 'mind', "Forty-one notches, one for every miner. Ethna carved a forty-second for you.")
e2 = z.item("Cold-Light Bracer", 'bracer', 19, 'faith', "It glows faintly blue at night, like the camp.")
z.quest('sm_gray_miners', 'The Gray Miners', 19, 'sm_ethna',
        "The gray spectres at the Fallen Camp are the miners who died when the east shaft fell in. Forty-one of them. They walk the tents still, looking for the way out.\n\nSomething keeps them from resting. Will you [go to the camp] and find out what?",
        'go to the camp',
        "The gray spectres of the Fallen Camp are miners who died in a collapse. Something keeps them from resting.",
        [
            reach(Z, [1500, 1480], "Go to the Fallen Camp, about 430 m south-east of the Miners' Cairn", "Tents still standing, rotted grey. Lamps still lit, burning cold blue. Gray shapes at the tent-flaps, turning towards you.", r=30),
            hunt([1530, 1500], "Kill 5 gray spectres among the miners' tents at the Fallen Camp", 'gray spectre', 5),
            search(Z, [1535, 1505], "Search the foreman's tent at the Fallen Camp (click the glinting spot)", "the foreman's tally-book", CRATE,
                   "The last entry, in a shaking hand: 'Broke through below the old seal. Pale silver, singing. Then the deep wind came up the shaft.'",
                   give="the foreman's tally-book"),
            end_talk('sm_ethna', "Bring the foreman's tally-book to Sister Ethna at the Miners' Cairn", "'Below the old seal.' They broke the druids' seal.\n\nSo the collapse wasn't an accident. They opened something, and it closed the mountain on them. Gods keep them.", 'default'),
        ],
        {'default': {'text': "Take this. And say their names, if you can.", 'choice': [e1, e2]}})

e3 = z.item("Seal-Stone Fragment Ring", 'ring', 23, 'ward', "A chip of the druids' seal. Ogham runs round it: 'shut'.")
e4 = z.item("Bone-Dust Pouch Belt", 'belt', 23, 'faith', "The miners' bones, gathered and buried. You kept the pouch you carried them in.")
z.quest('sm_bones_of_the_camp', 'Bones of the Camp', 23, 'sm_ethna',
        "The miners' bones walk with the spectres - you saw them. They want burying, and the spectres won't rest until they are.\n\nGather what you can, and then [find the seal] at the collapsed shaft. If the druids' seal is broken, I want to see it.",
        'find the seal',
        "The Fallen Camp's dead want burying, and Sister Ethna wants to see the broken seal.",
        [
            hunt([1530, 1500], "Kill 5 skeletal pawns (the miners' bones) among the tents at the Fallen Camp", "miner's bones", 5, give="a pouch of miners' bones"),
            search(Z, [1300, 1260], "Search the collapsed shaft, about 135 m south-east of the Miners' Cairn (click the glinting spot)", "a cracked seal-stone", CRATE,
                   "A great slab carved with ogham, split clean down the middle. Picks did that. On the far side, cold light and a smell of storms.",
                   give='a fragment of the seal-stone'),
            end_talk('sm_ethna', "Return to Sister Ethna at the Miners' Cairn", "Split by picks. Sheevra picks.\n\nThe bones are buried; forty-one names said. But that seal held something in, and it's out now. The deamhan on the heights - they came up that shaft.", 'default'),
        ],
        {'default': {'text': "Take this.", 'choice': [e3, e4]}},
        requires='sm_gray_miners')

e5 = z.item("Deamhan-Stone Bracer", 'bracer', 27, 'might', "Hacked off a deamhan creig. It's still angry.")
e6 = z.item("Storm-Glass Pendant", 'neck', 27, 'mind', "Lightning, caught in glass when a mephit died. It crackles.")
e7 = z.item("Heights Wanderer's Cloak", 'cloak', 27, 'ward', "Grey and heavy, for the sleet. You'll want it up there.")
z.quest('sm_up_the_shaft', 'Up the Shaft', 27, 'sm_ethna',
        "The deamhan pour out of the collapsed shaft every night, stone and storm. The Rowan say they guard what's below - whatever the sheevra woke.\n\nWill you [hold the shaft] long enough for me to see down it?",
        'hold the shaft',
        "Deamhan pour out of the collapsed shaft. Sister Ethna wants to see what they guard.",
        [
            hunt([1300, 1260], "Kill 4 deamhan creig at the collapsed shaft, about 135 m south-east of the Miners' Cairn", 'deamhan creig', 4),
            hunt([1300, 1260], "Kill 2 mountain mephits at the collapsed shaft", 'mountain mephit', 2),
            end_talk('sm_ethna', "Return to Sister Ethna at the Miners' Cairn", "I looked. I wish I hadn't.\n\nDown in the vein, something big, wrapped round the moon-silver like a dragon round gold. It's been feeding on it. The sheevra dig AROUND it. It lets them, because it's growing.", 'default'),
        ],
        {'default': {'text': "Take this. You'll need it for what comes next.", 'choice': [e5, e6, e7]}},
        requires='sm_bones_of_the_camp')

e8 = z.item("Vein-Heart Torc", 'neck', 30, 'faith', "Moon-silver from the Thing's own heart, quieted. Ethna blessed it. It sings softly now, a lullaby.")
e9 = z.item("Deep-Seal Ring", 'ring', 30, 'ward', "Carved from the new seal-stone, ogham and all: 'sleep'.")
e10 = z.item("Thing-Slayer's Bracer", 'bracer', 30, 'might', "Stone from the Thing's hide. Nothing in the valley will touch you while you wear it. Nothing alive.")
e11 = z.item("Forty-One Names Cloak", 'cloak', 30, 'mind', "Embroidered with the names of the miners of the Fallen Camp. Ethna stitched every one.")
z.quest('sm_thing_in_the_vein', 'The Thing in the Vein', 30, 'sm_ethna',
        "It's growing, and the mountain groans with it. If it keeps feeding, it'll come up the shaft and down the valley, and Howth will be a memory.\n\nBring everyone you can. Go down to the sealed vein and [kill the Thing]. Then we seal it properly - or we don't.",
        'kill the Thing',
        "A deamhan lord, the Thing in the Vein, feeds on the moon-silver at the bottom of the broken seal.",
        [
            reach(Z, [1350, 1330], "Go down to the sealed vein, about 220 m south-east of the Miners' Cairn", "A cavern of pale light. Moon-silver everywhere, veins of it singing in the walls - and coiled round the brightest seam, something vast and stony that opens its eyes.", r=30),
            hunt([1350, 1330], "Kill the Thing in the Vein", 'the Thing in the Vein', 1,
                 text="The Thing in the Vein shudders and goes still, and the singing in the walls drops to a murmur. The gray lights at the Fallen Camp go out, one by one."),
            choice('sm_ethna', "Return to Sister Ethna at the Miners' Cairn",
                   "The Thing is dead. The miners are resting - I felt them go.\n\nThe vein's still there. I can [seal the vein] again, the old way, and the moon-silver sleeps for another thousand years. Or Howth can [mine the vein] - carefully, with the Rowan watching - and be rich. The Rowan say seal it. The Wardens say mine it. You went down there. You choose.",
                   [('seal the vein', "Sealed, then. Sleep. All of you, sleep.", 'ending:sealed'),
                    ('mine the vein', "Carefully, then. Very carefully. And the Rowan watch every cart.", 'ending:mined')]),
        ],
        {'sealed': wake({'text': "Take these, with the Rowan's thanks and forty-one others'.", 'items': [e11], 'choice': [e8, e9, e10]}, 'silvermine_deep_wind'),
         'mined': wake({'text': "Take these, with the Rowan's thanks and forty-one others'.", 'items': [e11], 'choice': [e8, e9, e10]}, 'silvermine_deep_wind')},
        requires='sm_up_the_shaft', group=True)

# ======================================================================== The Rogue Druids (20 to 28) - Rowan
f1 = z.item("Moon-Dust Satchel Belt", 'belt', 21, 'mind', "A druid's satchel. The moon-silver dust in its seams still glitters.")
f2 = z.item("Turned Druid's Ring", 'ring', 21, 'faith', "A Rowan ring, its berries scraped off. Muirne wept when she saw it.")
z.quest('sm_druid_stones', 'The Druid Stones', 21, 'sm_cliodhna',
        "Druids I trained are in the hollow south of here, at the old stones, working moon-silver into something. They don't answer my letters.\n\nGo and see. If they fight, [bring their satchels] - I want to know what they're making.",
        'bring their satchels',
        "Rogue druids in the hollow are working moon-silver at the old stones.",
        [
            hunt([820, 1470], "Kill 5 rogue druids at the druid stones, about 320 m east of Muirne's post", 'rogue druid', 5, give="a rogue druid's satchel"),
            end_talk('sm_cliodhna', "Bring the druids' satchel to Muirne of the Rowan, about 350 m south of Howth", "Moon-silver, ground to dust. And blue-glass beads - the Azure Order's coin.\n\nThey're grinding it fine enough to burn. Fire that burns silver... Nictol would know. He was the best of us once. He lives alone in the south-west now, and he's gone strange.", 'default'),
        ],
        {'default': {'text': "Take this.", 'choice': [f1, f2]}},
        requires='sm_night_field')

f3 = z.item("Hermit's Hazel Staff-Charm", 'gem', 24, 'faith', "A knot of Nictol's staff. It was a good staff once.")
f4 = z.item("Unkempt Mantle", 'cloak', 24, 'ward', "Nictol's cloak, cleaned. Three times. It's still not entirely clean.")
z.quest('sm_nictol', 'Nictol the Unkempt', 24, 'sm_cliodhna',
        "Nictol taught me the rowan rites. Now he lives in a hut of bones in the south-west and talks to the moon.\n\nHe won't talk to me. He might talk to you - or he might fight. Either way, [find what Nictol knows].",
        'find what Nictol knows',
        "Nictol the Unkempt, once the best of the Rowan, lives alone in the south-west and has gone strange.",
        [
            hunt([122, 1597], "Defeat Nictol the Unkempt at his hut, about 400 m west of Muirne", 'Nictol the Unkempt', 1,
                 text="Nictol falls back against his hut, laughing and weeping. 'Moon-silver, moon-silver, burns blue, burns BLUE!'"),
            search(Z, [125, 1590], "Search Nictol's hut (click the glinting spot)", "Nictol's letters", CRATE,
                   "Letters from 'the Broker': 'Grind it, and we'll carry it. The Voice of the Azure pays in beads. Silver fire opens the gate in Connacht faster than wood.'",
                   give="the Broker's letters"),
            end_talk('sm_cliodhna', "Bring Nictol's letters to Muirne of the Rowan, about 350 m south of Howth", "'Silver fire opens the gate in Connacht faster than wood.'\n\nThe Voice of the Azure. In Connacht they burn men in wicker to feed a demon gate - Druidess Eabha writes of it. And our silver is making their fires burn hotter. The Broker. I want the Broker.", 'default'),
        ],
        {'default': {'text': "Take this.", 'choice': [f3, f4]}},
        requires='sm_druid_stones')

f5 = z.item("Broker's Ledger Case", 'belt', 28, 'mind', "The Broker's accounts. Every cart to Connacht, every bead paid. The Rowan sent a copy to Ardee.")
f6 = z.item("Blue-Bead Breaker Ring", 'ring', 28, 'might', "A ring of crushed blue beads, set in silver. The Azure Order's coin, made worthless.")
f7 = z.item("Rowan-and-Silver Torc", 'neck', 28, 'faith', "Moon-silver, quieted, woven with rowan. Muirne's own making.")
z.quest('sm_moon_silver_broker', 'The Moon-Silver Broker', 28, 'sm_cliodhna',
        "The Broker keeps a camp in the far south of the hollow, with druids to guard him and a cart-road to Connacht.\n\nBring friends. [Stop the Broker], and every cart of moon-silver stops with him.",
        'stop the Broker',
        "The Moon-Silver Broker sends moon-silver from the sheevra to the Azure Order in Connacht.",
        [
            hunt([900, 1560], "Defeat the Moon-Silver Broker at his camp, about 415 m east of Muirne", 'the Moon-Silver Broker', 1, give="the Broker's ledger",
                 text="The Broker falls among his carts. His ledger lists every load: from the sheevra, through the hollow, to 'the Voice, in the Wicker Fields of Connacht'."),
            end_talk('sm_cliodhna', "Bring the broker's ledger to Muirne of the Rowan, about 350 m south of Howth", "The Wicker Fields. The Voice of the Azure himself.\n\nThe trail leaves our valley here. I'm sending this to Druidess Eabha in Ardee - the Rowan in Connacht will want it. And you, if you've the stomach for fire.", 'default'),
        ],
        {'default': wake({'text': "Take this, from the Rowan.", 'items': [f5], 'choice': [f6, f7]}, 'silvermine_moon_silver_convoy')},
        requires='sm_nictol', group=True)
