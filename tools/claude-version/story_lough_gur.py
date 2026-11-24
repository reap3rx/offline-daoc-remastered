"""Lough Gur's story quests (claude 2026-11-24, the zone brief in Zone Reviews and the owner's answers) - see story_gen.py.
Places: zone metres [x, y].

Moved out of story_hib.py with the zone's rebuild (its two quests kept, by id):
    python tools/claude-version/story_gen.py story_lough_gur

The south's thread (decided 2026-11-23): the Glimmer - Cuuldurach the Glimmer King's spirits out of the Sheeroe Hills - is coming
north through the Bog of Cullen and Lough Gur. Here it is only lights on the lake at night, and the lake people take them for Aine,
the bright goddess of the hill. They are waking everything that sleeps in the lake. The thread: lights on Lough Gur. The cluricauns
stole Tadhg's harp because its old tune kept the lights off the water; the gurites carry touched folk south and sell them; the
Fairy Queen walked into the lights; the Glimmer is wearing the Earl's horse's silver shoes thin before their time - Cuuldurach wants
the sleeping army. At the end, the Glimmer's herald on the crannog in the lake, and with him an envoy of the Unseelie Court: the
two threads meet (owner: "Keep it. I like it").

Arcs (recommended levels; rewards pay at the player's level):
  The Walking Wood (Culraid, the hard start, 1-7) - the Sentinels
  Innis Carthaig's Troubles (28-31, the Sentinels; folded in: The Cluricaun's Harp)
  The Gurite Roads (30-35, the Sentinels; GROUP finale) - the gurites sell the touched to the ursine of Treibh Caillte
  The Touched (31-35, Aine's Circle; folded in: The Amadan's Touch)
  The Sorrowing Wood (33-37, the Circle; GROUP finale: the Melancholic Fairy Queen)
  The Earl Beneath the Lake (34-38, the Circle; GROUP finale: the herald on the crannog)
  The Azure (32-35): Brother Ennis's quests hunt the Glimmer; his last sends you to burn the touched folk's camp - finishing it
  turns the Azure hostile to you (AzureStanding.cs) and wakes the Azure Burning.
"""
import math
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

CRATE, BEDROLL, LANTERN = 1347, 1882, 1876
M, F, OLD = 337, 365, 362
Z = 204
ZONES = []

z = Zone(Z, 'Lough Gur', 3, 'hib_lough_gur')
ZONES.append(z)
AT, NAMES = {}, {}

LARGE_LUCH, GREATER_LUCH, CATCHER, LUCH_HUNTER = 60163146, 60161603, 60163448, 60163452
SAPLING = 60162486
CLURI = 60159264
WAYLAYER, ASSAILER, RAIDER, LOOKOUT = 60161874, 60161866, 60161871, 60161869
URS_THRALL, URS_SORC, TROG = 60167489, 60167488, 60167283
ALP, TOUCHED = 60157767, 60157791
FAIRY, MILITANT, FAR_LIATH = 60163914, 60164025, 60160721
GLIM, WISP, WARSHADE = 60161430, 60161424, 60161425
DULL, WRAITH, STALLION = 60160221, 60158464, 60166634
HOUND = 60159815


def person(id, name, xy, kind, level, **kw):
    NAMES[id] = name
    AT[id] = tuple(xy)
    z.npc(id, name, list(xy), kind, level, **kw)


def where(to, frm):
    """'about 240 m north-west of Sentinel Maeve' (y grows southward)."""
    fx, fy = AT[frm]
    dx, dy = to[0] - fx, to[1] - fy
    d = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(-dy, dx)) % 360
    names = ['east', 'north-east', 'north', 'north-west', 'west', 'south-west', 'south', 'south-east']
    dirn = names[int(((ang + 22.5) % 360) // 45)]
    dist = ('%d m' % (round(d / 10) * 10)) if d < 950 else ('%.1f km' % (d / 1000))
    return 'about %s %s of %s' % (dist, dirn, NAMES[frm])


def hunt(xy, goal, target, count=1, text=None, r=50):
    """Kill the zone's own monster (its named ones are the quests' named foes too)."""
    st = {'type': 'kill', 'zone': Z, 'at': list(xy), 'radius': r, 'goal': goal, 'target': target, 'count': count}
    if text:
        st['text'] = text
    return st


# ------------------------------------------------------------------ people
# Culraid (the hard start)
person('ciaran_bard', 'Ciaran the Bard', (312, 200), 'm', 30, idle="My brother was the better poet. Ask anyone. Ask him - when he's sane.")
person('lg_oisin', 'Woodward Oisin', (304, 182), 'm', 34, guild='Culraid',
       idle="Mind the saplings. They look like saplings. That's the whole trick.")
# Innis Carthaig
person('tadhg_inn', 'Tadhg the Innkeeper', (1190, 1006), 'm', 22, idle="Grandfather's harp hung over the bar sixty years. The luck of the house.")
person('dara', 'Dara the Potboy', (1182, 1002), 'm', 12, idle="I didn't drink anything. Much.")
person('lg_maeve', 'Sentinel Maeve', (1166, 986), 'f', 40, guild='the Sentinels of Ceannai',
       idle="Ceannai sent me south to keep the road. The road keeps getting longer.")
person('lg_colm', 'Ferryman Colm', (1150, 1072), 'm', 30, guild='the Lough Gur Ferry',
       idle="Forty years on this lake and I never once saw it lit from underneath. Until this spring.")
person('lg_eithne', 'Eithne the Miller', (700, 380), 'f', 28, guild='Eithne\'s Mill',
       idle="The luch ate the seed corn, then the thatch, then the cat. I'm not joking about the cat.")
# Aine's Circle (the stone circle north-east of the town) and the touched folk's camp
person('lg_ceallach', 'Druid Ceallach', (1230, 860), 'm', 44, guild="Aine's Circle",
       idle="Aine sits on the shore and combs her hair. Every child here knows that. The lights on the water aren't her.")
person('lg_siofra', 'Druid Siofra', (426, 1112), 'f', 38, guild="Aine's Circle",
       idle="Touched isn't lost. Touched is touched. They need a fire and somebody who listens.")
z.npc('eoin', 'Eoin', [428, 1124], 'm', 30, during=['amadan/eoin'])
NAMES['eoin'] = 'Eoin'
AT['eoin'] = (428, 1124)
z.npc('lg_grainne', 'Grainne', [552, 1316], 'f', 20, during=['lg_taken_girl/grainne'])
NAMES['lg_grainne'] = 'Grainne'
AT['lg_grainne'] = (552, 1316)
z.npc('lg_captive', 'Bound Man', [254, 654], 'm', 26, model=OLD, during=['lg_bear_trade/captive'])
NAMES['lg_captive'] = 'Bound Man'
AT['lg_captive'] = (254, 654)
# the Azure's recruiter, by their camp on the south-east road
person('lg_ennis', 'Brother Ennis', (1470, 1150), 'm', 40, model=354, guild='the Order of the Azure',
       idle="The Order of the Azure has one enemy: the Glimmer. Everything else is a matter of time.")

# ======================================================================== The Walking Wood (Culraid, the hard start, 1-7)
w1 = z.item("Woodward's Twine Belt", 'belt', 3, 'finesse', "Oisin ties up the saplings that walk too far. He has a lot of twine.")
w2 = z.item('Culraid Thatch Ring', 'ring', 3, 'ward', "Plaited from a roof the walking wood tried to pull down.")
z.quest('lg_walking_wood', 'The Walking Wood', 2, 'lg_oisin',
        "You started here? In Culraid? Brave, or nobody told you. Lough Gur eats the careless, and this corner's the only soft bit of it.\n\nFirst lesson: the trees round the village walk. The young ones, the saplings - they come right up to the houses at night and root in the garden. Will you [thin the saplings]? Strike low. They hate that.",
        'thin the saplings',
        "The young trees of the Irewood walk into Culraid at night. Woodward Oisin wants them thinned.",
        [
            kill(Z, (330, 250), "Thin the walking saplings " + where((330, 250), 'lg_oisin'), 'irewood sapling', SAPLING, [2, 3], 5,
                 text="The last one stops, and its leaves go still, and it's only a tree again."),
            search(Z, (360, 300), "Look at the root-ball of a felled sapling", "a sapling's root-ball, still twitching", CRATE,
                   "The roots are pale, and there's a light in them - a faint, cold glow, like moonlight on water. Trees don't glow."),
            end_talk('lg_oisin', "Tell Woodward Oisin", "Glowing? ...They never glowed before this spring. Nothing round the lake did.\n\nWell. You're still alive, which is the first thing Culraid asks of anyone. Here.", 'default'),
        ],
        {'default': {'text': "From Oisin.", 'choice': [w1, w2]}})

w3 = z.item("Luch-Tail Bracer", 'bracer', 5, 'might', "Luch tails, braided. They make a surprisingly good bracer.")
w4 = z.item("Thatcher's Charm", 'gem', 5, 'charm', "A knot of straw from the first roof you saved.")
z.quest('lg_luch_in_the_thatch', 'Luch in the Thatch', 4, 'lg_oisin',
        "Second lesson. The luch - the big mice, big as dogs - are in the thatch again. They nest in it, eat through it, and the roofs come down in the first rain.\n\nThe catchers are worse than the luch: they hunt them and leave the leavings on our doorsteps. Will you [clear the luch]?",
        'clear the luch',
        "Luch are eating Culraid's thatch, and the luch catchers are worse.",
        [
            kill(Z, (240, 120), "Kill the large luch nesting in Culraid's roofs " + where((240, 120), 'lg_oisin'), 'large luch', LARGE_LUCH, [4, 5], 6),
            kill(Z, (420, 150), "Drive off the luch catchers east of the village", 'luch catcher', CATCHER, [5, 6], 3,
                 text="One catcher has a string of luch tails round its neck - and a little bone harp-peg among them."),
            end_talk('lg_oisin', "Tell Woodward Oisin", "A harp-peg. Tadhg, at the inn at Innis Carthaig, lost a harp this spring - the whole lake heard him. The luch must have been through his cellar too.\n\nYou'll be going there sooner or later. Everyone does.", 'default'),
        ],
        {'default': {'text': "From Oisin.", 'choice': [w3, w4]}},
        requires='lg_walking_wood')

w5 = z.item("Lake-Road Boots-Charm", 'gem', 7, 'finesse', "A pebble from the lake road, worn smooth by people leaving Culraid.")
w6 = z.item("Sentinel's Token", 'ring', 7, 'might', "Ceannai's token, given to those who walk the road on their own.")
z.quest('lg_road_to_the_lake', 'The Road to the Lake', 7, 'lg_oisin',
        "Last lesson, and then you're on your own. Innis Carthaig is on the far shore - the only real town on Lough Gur. The Sentinels of Ceannai keep it, and a woman called Maeve keeps them.\n\nThe road runs east through the fields. The greater luch hunt along it. Will you [walk the road]? Go carefully. It gets harder every step you take from here.",
        'walk the road',
        "Woodward Oisin sends you from Culraid along the lake road to Sentinel Maeve in Innis Carthaig.",
        [
            reach(Z, (620, 260), "Take the lake road east out of Culraid", "The fields open out. Far off, the lake shines - and something big moves in the barley.", r=25),
            kill(Z, (660, 300), "Kill the greater luch hunting the road", 'greater luch', GREATER_LUCH, [6, 7], 4),
            end_talk('lg_maeve', "Report to Sentinel Maeve in Innis Carthaig", "From Culraid? On foot? Oisin's work, I suppose. He sends me one a season, and they're always tougher than they look.\n\nWelcome to Lough Gur. You'll find the work finds you here.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [w5, w6]}},
        requires='lg_luch_in_the_thatch')

# ======================================================================== Innis Carthaig's Troubles (28-31) - the Sentinels
i1 = z.item("Miller's Flour-Sack Belt", 'belt', 29, 'ward', "Tough sacking, stitched double. Eithne swears by it.")
i2 = z.item("Granary-Key Ring", 'ring', 29, 'might', "The key to the mill's grain store, made into a ring.")
z.quest('lg_granaries', 'The Granaries', 29, 'lg_maeve',
        "The luch are into the mill on the north road. Eithne the Miller's holding the grain store with a shovel and her temper, and both are running out.\n\nWill you [hold the mill] with her? The hunters come in behind the swarm - big ones, the colour of old straw.",
        'hold the mill',
        "The luch are swarming Eithne's mill on the north road.",
        [
            defend(Z, (700, 380), "Keep Eithne alive while she seals the grain store " + where((700, 380), 'lg_maeve'),
                   "The swarm breaks against the mill door. Eithne slams the bolt home.",
                   'Eithne the Miller', 60161797, 28, "Eithne is nailing boards over the grain store door. 'Keep them OFF me!'",
                   [(GREATER_LUCH, 'greater luch', [28, 29]), (CATCHER, 'luch catcher', [28, 29])], 'Keep Eithne the Miller alive',
                   model=F, duration=120, every=20, count=3),
            kill(Z, (760, 430), "Kill the luch hunters behind the swarm", 'luch hunter', LUCH_HUNTER, [29, 30], 4,
                 text="The hunters wear collars - thin bands of bright metal. Someone put them there."),
            end_talk('lg_maeve', "Report to Sentinel Maeve", "Collars? On luch? ...There's an old story here, about the king of the mice. Luchtigern. I thought it was a story.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [i1, i2]}})

i3 = z.item("Irusan's Claw Torc", 'neck', 30, 'finesse', "In the old story the cat Irusan killed Luchtigern, king of the mice. This is a claw from a cat nearly as big.")
i4 = z.item("Mouse-King's Collar", 'bracer', 30, 'might', "Bright metal, warm to the touch. It glows faintly at night.")
z.quest('lg_luchtigern', 'Luchtigern', 30, 'lg_maeve',
        "Every child at Lough Gur knows the story. Luchtigern, the king of the mice, lived in a cave by the lake, until the great cat Irusan came and killed him.\n\nThe old folk say he's back. A luch the size of a pony, walking the west shore by day, with collared hunters round him. Will you [find Luchtigern]? Kill him if he's real.",
        'find Luchtigern',
        "Luchtigern, the king of the mice in the old story, walks the west shore by day.",
        [
            search(Z, (470, 640), "Look for Luchtigern's trail on the west fields " + where((470, 640), 'lg_maeve'), "a trail of gnawed bones and bright metal", CRATE,
                   "Gnawed bones, and among them a collar like the hunters' - bigger. It glows like the lake does at night."),
            hunt((494, 665), "Kill Luchtigern, the king of the mice (by day, on the west fields)", 'Luchtigern',
                 text="Luchtigern falls. Round his neck, under the fur: a collar of the same bright metal, humming faintly."),
            end_talk('lg_maeve', "Report to Sentinel Maeve", "Bright metal. Glowing. The luch, the saplings in Culraid, the lake. It's all the same light.\n\nThe Circle up on the hill will want to know. Druid Ceallach. Tell him I sent you.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [i3, i4]}},
        requires='lg_granaries')

# The Cluricaun's Harp (kept, by id): the harp's tune kept the lights off the water
it_harp2 = z.item("Inn-Luck Harp Charm", 'gem', 29, 'charm', "A tiny harp of bog-oak. The luck of a house sixty years old is in it.")
it_ale = z.item('Ale-Belly Girdle', 'belt', 29, 'ward', "The cluricaun king's belt. Let out several times.")
it_luch2 = z.item('Luch-Rider Bracer', 'bracer', 29, 'finesse', "Cluricauns ride the giant luch like ponies. This is from a saddle.")
it_cellar = z.item("Cellar-Key Ring", 'ring', 29, 'might', "The key to Tadhg's cellar, made into a ring. It opens other cellars too, you suspect.")
z.quest('cluricaun', "The Cluricaun's Harp", 29, 'tadhg_inn',
        "The cluricauns have been in my cellar every night since spring - drinking, singing, breaking things. I let it go. Every inn has cluricauns.\n\nBut three nights ago they took my grandfather's harp from over the bar. The luck of the house. Since then the ale's gone sour, the roof leaks, and there are lights on the lake at night. Will you [get the harp back]? Dara the [potboy] saw them go.",
        'get the harp back',
        "Cluricauns stole the harp that has hung over Tadhg's bar for sixty years - the luck of the house.",
        [
            talk('dara', 'Ask Dara the potboy what he saw',
                 "They came up out of the cellar riding luch - giant mice! - and one of them had the harp, and they all went north-east singing. I followed a bit. They've a sort of camp out by the luch runs, in the [north-east].", kw='north-east'),
            kill(Z, (1290, 700), "Deal with the cluricauns' luch mounts at the luch runs", 'large luch', LARGE_LUCH, [28, 29], 5),
            search(Z, (1236, 646), 'Search the cluricaun camp', "a trail of spilled ale and a harp string", CRATE,
                   "A harp string, snapped, and a lake of spilled ale. Drunken singing, very close."),
            kill(Z, (1244, 633), 'Fight through the drunken cluricauns', 'cluricaun', CLURI, [28, 29], 5),
            boss(Z, (1240, 630), 'Defeat the cluricaun king', "The cluricaun king sits down, hiccups, and says: 'Fine. Take it. It's ours, though. And play it, ye great lump - play it at the water at night, or the lights'll have the lot of ye.'",
                 'King Fiachra Ale-Belly', CLURI, 31, "A very fat cluricaun with a harp under one arm and a barrel under the other. 'MY harp! Get yer own!'",
                 objective='Defeat King Fiachra', hp=2.2, adds=[(CLURI, 'cluricaun', [28, 29])], every=25, count=2),
            choice('tadhg_inn', 'Bring the harp back to Tadhg',
                   "The harp! Oh, thank the gods - wait. What did he say? That it was THEIRS? And something about the lights?\n\n...Grandfather did say he won it at dice. From a very small man. In a cellar. And he played it every night on the jetty, the old fool, and we laughed at him.\n\nIf it's theirs, I should [give it back]. Or I [keep it], and the cluricauns can sulk. It's been over that bar sixty years.",
                   [('give it back', "Back it goes. I'll leave it in the cellar tonight with a barrel of the good stuff. ...They'll be back for that barrel every week, you know.", 'ending:returned'),
                    ('keep it', "It stays. Sixty years is ownership. ...The ale's already sweeter. Listen to that roof - not a drip.", 'ending:kept')]),
        ],
        {'returned': {'text': "Take something. The cluricauns left this in the cellar for you - I think it's a thank you.", 'items': [it_ale], 'choice': [it_luch2, it_cellar]},
         'kept': {'text': "Take something from behind the bar.", 'items': [it_harp2], 'choice': [it_luch2, it_cellar]}},
        topics={'potboy': "Dara. He's wiping tables. He's always wiping tables."})

i5 = z.item("Jetty-Song Pendant", 'neck', 31, 'faith', "A harp-peg on a cord. Hum the old tune and it hums back.")
i6 = z.item("Lake-Watcher's Cloak", 'cloak', 31, 'ward', "Grey wool, for long nights on the jetty.")
z.quest('lg_harp_tune', "Grandfather's Tune", 31, 'dara',
        "Can I tell you something? Tadhg doesn't listen.\n\nHis grandda played that harp every night on the jetty. The same tune, over and over. Since the harp went, the lights came. I wrote the tune down once - I was learning. Will you [take the tune] to the druids on the hill? They'll know what it is.",
        'take the tune',
        "Dara wrote down the tune Tadhg's grandfather played on the jetty every night - the lights came when it stopped.",
        [
            reach(Z, (1120, 900), "Watch the lake from the north jetty at dusk " + where((1120, 900), 'dara'),
                  "Out on the water, a pale light rises, hangs a moment over the crannog, and sinks. Something under the lake breathes out.", r=20),
            end_talk('lg_ceallach', "Take Dara's tune to Druid Ceallach at the stone circle", "Let me see. ...Oh. Oh, that's old. That's a lulling - a sleep-song. Somebody's grandfather sat on that jetty every night for sixty years singing the lake to sleep, and nobody knew.\n\nAnd now he's dead, and the harp's been gone, and the lake is waking up. And something is waking it on purpose.", 'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [i5, i6]}},
        requires='lg_luchtigern')

# ======================================================================== The Gurite Roads (30-35) - the Sentinels, GROUP finale
g1 = z.item("Toll-Taker's Ring", 'ring', 30, 'finesse', "The gurites charged a toll on the south road. In blood, mostly.")
g2 = z.item("Road-Post Bracer", 'bracer', 30, 'ward', "Iron from the Sentinels' burned road post.")
z.quest('lg_south_road', 'The South Road', 30, 'lg_maeve',
        "The gurites have the south road. They burned our road post on it last month, and the Sentinel who held it isn't talking - he's not anything, any more.\n\nThey don't just rob. People go down that road and don't come out the other end. Will you [take the road post back]?",
        'take the road post back',
        "The gurites burned the Sentinels' post on the south road, and people who take that road vanish.",
        [
            kill(Z, (440, 940), "Kill the gurite waylayers at the burned road post " + where((440, 940), 'lg_maeve'), 'gurite waylayer', WAYLAYER, [30, 31], 6),
            search(Z, (446, 946), "Search the road post", "a ledger of tolls", CRATE,
                   "A gurite ledger. Tolls taken, and next to some names, not a sum but a word: 'south'. Eleven names this month. One of them was a Sentinel.", give='the gurite ledger'),
            end_talk('lg_maeve', "Bring the ledger to Sentinel Maeve", "'South'. They're not killing them. They're carrying them somewhere. The ferryman sees everything that crosses the lake - ask Colm.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [g1, g2]}})

g3 = z.item("Ferryman's Pole-Ring", 'ring', 32, 'might', "Bog-oak and brass, from Colm's old ferry pole.")
g4 = z.item("Bill-of-Sale Charm", 'gem', 32, 'charm', "Kept to remember them by.")
z.quest('lg_carried_south', 'Carried South', 32, 'lg_colm',
        "Gurites. Yes. Three times this spring, at night, a gurite boat crossing the south end of the lake with people in the bottom of it, tied. I didn't stop them. I've a wife.\n\nThey land on the south-east shore and go up the road to their post by the sheerie ring. Will you [follow them]?",
        'follow them',
        "Ferryman Colm saw gurites carrying bound people across the lake to the south-east road.",
        [
            kill(Z, (1466, 1315), "Break the gurite assailers' post on the south-east road " + where((1466, 1315), 'lg_colm'), 'gurite assailer', ASSAILER, [31, 32], 6),
            search(Z, (1475, 1325), "Search the assailers' post", "a strongbox of bright gems", CRATE,
                   "Gems that glow on their own, and a bill of sale scratched on bark: 'Six, to the bear-folk at the cave-mouth west of the lake. Paid in light.'", give='the bark bill of sale'),
            end_talk('lg_maeve', "Bring the bill of sale to Sentinel Maeve", "The bear-folk. The ursine, out of Treibh Caillte - the lost tribe, under the hills. They've been coming up out of the caves all spring, and now I know why. They're buying people. With light.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [g3, g4]}},
        requires='lg_south_road')

g5 = z.item("Cave-Mouth Belt", 'belt', 33, 'finesse', "From the ursine's trading post at the mouth of Treibh Caillte.")
g6 = z.item("Unbound Wrist", 'bracer', 33, 'ward', "The cord that tied him, worn as a promise.")
z.quest('lg_bear_trade', 'The Bear-Folk', 33, 'lg_maeve',
        "The ursine trade at the mouth of Treibh Caillte, on the west shore. If there's anyone still there, I want them back.\n\nWill you [go to the cave-mouth]? The things that come up out of those caves with the bears are no better than the bears.",
        'go to the cave-mouth',
        "The ursine of Treibh Caillte buy the gurites' captives at the cave-mouth on the west shore.",
        [
            kill(Z, (250, 660), "Clear the troglodytes at the mouth of Treibh Caillte " + where((250, 660), 'lg_maeve'), 'troglodyte', TROG, [32, 33], 5),
            L('captive', talk('lg_captive', "Free the bound man at the cave-mouth",
                              "You're not a bear. Good. They took the others down an hour ago. Deep.\n\nThe bears don't eat them. They sit them in the dark, under a lamp that the gurites bring - a lamp full of that light - and the people go quiet, and start to glow, and the bears [kneel] to them. I don't know. I don't know what it is.", kw='kneel')),
            kill(Z, (300, 700), "Kill the ursine thralls guarding the trade-road", 'ursine thrall', URS_THRALL, [32, 33], 5),
            end_talk('lg_maeve', "Bring the bound man home to Sentinel Maeve", "Kneel to them. To people who glow.\n\nThe gurites sell the touched to the bear-folk, and the bear-folk worship the light in them. And whoever pays the gurites in glowing gems is making a church out of my road. It ends at the gurites' camp. All of it.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [g5, g6]}},
        requires='lg_carried_south')

g7 = z.item("Tiomoid's Hill-Ring", 'ring', 34, 'might', "Tiomoid kept the camp's watch. He never slept.")
g8 = z.item("Trefor's Toll-Bag Belt", 'belt', 34, 'finesse', "Trefor kept the gurites' purse. It was heavier than it looked.")
z.quest('lg_gurite_captains', 'The Hill-Captains', 34, 'lg_maeve',
        "Before we go for the camp, I want its legs cut. The gurites have two captains in the hills - Tiomoid keeps their watch, and Trefor keeps their purse.\n\nWill you [hunt them]? Both of them. The camp won't hold without them.",
        'hunt them',
        "Sentinel Maeve wants the gurites' two hill-captains, Tiomoid and Trefor, dead before the camp is stormed.",
        [
            hunt((173, 1352), "Kill Tiomoid, who keeps the gurites' watch in the hills " + where((173, 1352), 'lg_maeve'), 'Tiomoid'),
            hunt((149, 1295), "Kill Trefor, who keeps the gurites' purse", 'Trefor',
                 text="Trefor's purse is full of the glowing gems - and a note: 'Donnan: the herald will pay double for the next ten. Bring them to the crannog.'"),
            end_talk('lg_maeve', "Report to Sentinel Maeve", "The crannog. The island in the lake. The herald. ...Whoever that is, the druids should hear it. After we've burned that camp.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [g7, g8]}},
        requires='lg_bear_trade')

g9 = z.item("Gurite-King's Crown-Ring", 'ring', 35, 'mind', "Donnan's crown was a ring of gurite tolls. This was the best of them.")
g10 = z.item("Mantle of the South Road", 'cloak', 35, 'ward', "The Sentinels' own, for the ones who took the road back.")
g11 = z.item("Hill-Camp Torc", 'neck', 35, 'might', "Bronze, from the gurites' war-chest.")
z.quest('lg_gurite_king', 'The Gurite-King', 35, 'lg_maeve',
        "GROUP work. Bring friends you'd trust with your back.\n\nThe gurite camp in the hills, south-west. Donnan calls himself their king, and he's the one the herald pays. We go in, we bring him down, and the south road is the realm's again.\n\nSay [we go], when you're ready.",
        'we go',
        "GROUP. Storm the gurite camp in the hills and bring down Donnan, the Gurite-King.",
        [
            reach(Z, (240, 1150), "Gather below the gurite camp in the hills " + where((240, 1150), 'lg_maeve'), "Smoke from the camp. Lookouts on the rocks. Somewhere inside, someone is laughing.", r=25),
            boss(Z, (165, 1190), "Defeat Donnan the Gurite-King in his camp",
                 "Donnan goes down on one knee. 'The lights pay better than travellers,' he says, 'and they never ask for change.' Then he doesn't say anything.",
                 'Donnan the Gurite-King', RAIDER, 38, "A gurite in a crown of rings stands up from a chair made of saddles. 'Sentinels. And friends. Good - the herald pays more for the fighting kind.'",
                 objective='Defeat Donnan the Gurite-King', hp=4.0, adds=[(RAIDER, 'gurite raider', [34, 35]), (LOOKOUT, 'gurite lookout', [34, 35])], every=22, count=3),
            choice('lg_maeve', "Report to Sentinel Maeve",
                   "The road is ours. And the gurites who are left? They're on their knees in the camp. Some of them were carried south themselves, once, and came back working for Donnan.\n\nCeannai's law says [hang them]. Mine says [send them north] to the Shannon with nothing - let them start again. You took the camp. You say.",
                   [('hang them', "Hanged, then. The road will be quieter for it. Not better. Quieter.", 'ending:hanged'),
                    ('send them north', "North, then. With nothing but their boots. ...Some will come back to it. Some won't.", 'ending:spared')]),
        ],
        {'hanged': {'text': "From the Sentinels of Ceannai.", 'tragic': True, 'items': [g10], 'choice': [g9, g11]},
         'spared': {'text': "From the Sentinels of Ceannai.", 'items': [g10], 'choice': [g9, g11]}},
        requires='lg_gurite_captains', group=True)

# ======================================================================== The Touched (31-35) - Aine's Circle
it_madness = z.item("Amadan's Straw Crown", 'gem', 33, 'mind', "A crown of straw that the amadan wore. Whoever wears it hears music nobody else can.")
it_verse = z.item('Verse-Book Clasp', 'belt', 33, 'faith', "From Eoin's book of poems. Every page is full, and none of it makes sense, and all of it is beautiful.")
it_gurite = z.item('Gurite Waylayer Ring', 'ring', 33, 'finesse', "Taken off a gurite who robbed travellers on the south road.")
it_alp = z.item("Alp-Luachra Hide Cloak", 'cloak', 33, 'ward', "The alp luachra are newts that crawl into sleepers' mouths. The hide is very good leather.")
t1 = z.item("Wet-Footprint Charm", 'gem', 32, 'faith', "A pebble from the shore where the touched walked in.")
t2 = z.item("Druid's Rush-Belt", 'belt', 32, 'mind', "Siofra plaits them for anyone who sits with the touched a night.")
z.quest('lg_touched_walk', 'The Walkers', 32, 'lg_ceallach',
        "The touched folk - the ones the amadan's touch sent mad - live in a camp in the south-west woods. Druid Siofra keeps them. She sends word: at night they walk down to the lake in a line, singing, toward the lights.\n\nSome of them don't come back. Will you [go to Siofra]?",
        'go to Siofra',
        "The touched folk walk down to the lake at night, singing, toward the lights - and some don't come back.",
        [
            talk('lg_siofra', "Find Druid Siofra at the touched folk's camp " + where((426, 1112), 'lg_ceallach'),
                 "Every night. They get up, and smile, and walk to the water. I hold the ones I can. Something nests in the hollow on the way and gets at the sleepers too - the alp luachra. Clear the [hollow], and then watch the shore.", kw='hollow'),
            kill(Z, (290, 1079), "Clear the alp luachra from the sleeping-hollow", 'alp luachra', ALP, [31, 32], 4),
            kill(Z, (680, 1000), "Put out the lights on the west shore where the touched walk in", 'glimmer light', GLIM, [32, 33], 4,
                 text="Each light, as it goes out, makes a sound like someone sighing in their sleep."),
            end_talk('lg_ceallach', "Report to Druid Ceallach", "They sigh. Of course they sigh - they're not lights, they're lures. Somebody is fishing in Lough Gur, and the touched are the easiest fish.", 'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [t1, t2]}})

z.quest('amadan', "The Amadan's Touch", 33, 'ciaran_bard',
        "My brother Eoin was touched by the amadan - the faerie fool - last autumn. One touch, and he walked into the southern woods laughing and never came out.\n\nHe was the better poet. Everyone said so. I want him back, even mad. Will you [find Eoin]? The road south is thick with gurite, so be careful.",
        'find Eoin',
        "Ciaran's brother, a poet, was touched by the amadan - the faerie fool - and walked laughing into the southern woods.",
        [
            reach(Z, (440, 940), 'Take the road into the southern woods', "Gurite waylayers watch the road from the trees. Further on, someone is laughing.", r=20),
            kill(Z, (465, 948), 'Kill the gurite waylayers on the south road', 'gurite waylayer', WAYLAYER, [32, 33], 5),
            kill(Z, (290, 1079), 'Clear the alp luachra from the sleeping-hollow', 'alp luachra', ALP, [32, 33], 4,
                 text="Under the leaves where they nested: a sleeping man's footprints, many nights over. He sleeps here, sometimes."),
            search(Z, (420, 1118), "Search the touched folk's camp", "a book of poems, rain-soaked", CRATE,
                   "Eoin's book. Every page is full of verse in a dozen hands, all his. The last page: 'The fool says I may go home if someone fetches me. Nobody fetches me. The lights on the lake sing better than I do.'",
                   give="Eoin's book of poems"),
            L('eoin', talk('eoin', 'Talk to Eoin', "Ciaran! No - you're not Ciaran. You smell of the road. Ha!\n\nI'm quite mad, you know. It's lovely. Every word I've written since is better than everything before. The fool won't let me go until somebody beats him at his own game. His game is [hitting].", kw='hitting')),
            boss(Z, (430, 1130), 'Defeat the amadan', "The amadan falls over laughing, and doesn't get up. All around, the touched folk sit down and blink, as if waking.",
                 'the Amadan of the Hollow', TOUCHED, 36, "A ragged man in a straw crown capers out of the trees. 'A new game! A new player! TOUCH!'",
                 objective='Defeat the Amadan', hp=2.5, adds=[(TOUCHED, 'amadan touched', [32, 33])], every=25, count=2),
            choice('ciaran_bard', 'Bring Eoin home to Ciaran in Culraid',
                   "Eoin. EOIN. You're - he's -\n\n...He's sane? He knows me? He's crying. Why is he crying?\n\nHe says the poems stopped when the fool died. He says he's empty. He says he wants to [go back] to the woods with the other touched folk, and look after them. Or I could [keep him home] until he's well. I've waited a year. You decide. I can't trust myself.",
                   [('keep him home', "Then he stays. He'll write again. Plain words, maybe, but his. And I'll be the better poet for once, ha. ...Ha.", 'ending:home'),
                    ('go back', "Then go, brother. Go and look after them. I'll bring you paper every new moon. Whatever you write, I'll read.", 'ending:woods')]),
        ],
        {'home': {'text': "Take something. Eoin wants you to have this.", 'items': [it_verse], 'choice': [it_gurite, it_alp]},
         'woods': {'text': "Take something.", 'tragic': True, 'items': [it_madness], 'choice': [it_gurite, it_alp]}})

t3 = z.item("Siofra's Rowan Charm", 'gem', 34, 'faith', "Rowan berries on red thread. The drowned won't cross it.")
t4 = z.item("Lit-From-Within Bracer", 'bracer', 34, 'ward', "From one of the drowned. The glow went out of it when they were laid to rest.")
z.quest('lg_drowned_return', 'The Drowned Come Back', 34, 'lg_siofra',
        "The ones who walked in and didn't come out - they came out last night. Drowned, and lit from inside like lanterns, and they came for the camp. For the others. They want company.\n\nI'm going to sing them to sleep, the way the old man on the jetty did. Will you [keep them off me] while I sing?",
        'keep them off me',
        "The touched who drowned in the lake walk out again, lit from within, and come for the touched folk's camp.",
        [
            defend(Z, (426, 1112), "Keep Druid Siofra alive while she sings the drowned to sleep",
                   "Siofra's song goes on, and on, and the drowned stop, and lie down in the ferns one by one.",
                   'Druid Siofra', 60163820, 36, "Siofra starts to sing - the jetty tune, Dara's tune. Out of the dark the drowned come walking, glowing.",
                   [(TOUCHED, 'drowned touched', [33, 34]), (GLIM, 'glimmer light', [33, 34])], 'Keep Druid Siofra alive',
                   model=F, duration=150, every=20, count=3),
            end_talk('lg_siofra', "Talk to Druid Siofra", "They're asleep. Properly asleep. The light went out of them when the song took.\n\nSo the song works. Ceallach needs to know - and he needs to know about Lhia. The lhiannan-sidhe on the north shore. She's been teaching the touched new songs. Not ours.", 'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [t3, t4]}},
        requires='lg_touched_walk')

t5 = z.item("Lhia's Mirror Pendant", 'neck', 35, 'mind', "A muse's mirror. In it you look the way you'd like to.")
t6 = z.item("Unsung Ring", 'ring', 35, 'faith', "Silver, with no song on it at all. That's the point.")
z.quest('lg_lhia', 'Lhia', 35, 'lg_ceallach',
        "A lhiannan-sidhe - a faerie muse - on the north shore. Lhia. She's always been there; she takes a poet a generation, and the poet thinks it was worth it.\n\nBut Siofra says she's teaching the touched songs. A muse doesn't teach - she takes. Unless someone's paying her in something better than poets. Will you [stop Lhia]?",
        'stop Lhia',
        "Lhia, the lhiannan-sidhe of the north shore, is teaching the touched folk songs that lead them to the water.",
        [
            hunt((732, 732), "Kill Lhia, the lhiannan-sidhe of the lake shore " + where((732, 732), 'lg_ceallach'), 'Lhia',
                 text="Lhia falls, and her last breath is light - a long thread of it, that drifts out over the lake toward the crannog."),
            end_talk('lg_ceallach', "Report to Druid Ceallach", "Toward the crannog. Everything goes toward the crannog.\n\nThere's a thing on that island, and the lights are its fishing-lines. When we know what it is, we'll go out to it. Not before.", 'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [t5, t6]}},
        requires='lg_drowned_return')

# ======================================================================== The Sorrowing Wood (33-37) - the Circle, GROUP finale
s1 = z.item("Frozen-Tear Charm", 'gem', 33, 'charm', "A fairy's tear, frozen. It never melts.")
s2 = z.item("Mourner's Belt", 'belt', 33, 'finesse', "Grey silk, from a melancholic fairy's girdle.")
z.quest('lg_weeping', 'The Weeping', 33, 'lg_ceallach',
        "The fairies of the south wood have always been sad - they're the melancholic folk, it's in the name. But they weep now. Day and night. You can hear it from the moor road.\n\nAnd they've started taking travellers off that road. Will you [find out why]?",
        'find out why',
        "The melancholic fairies of the Sorrowing Wood weep day and night, and take travellers off the moor road.",
        [
            kill(Z, (600, 1150), "Break the ring of weeping fairies at the wood's edge " + where((600, 1150), 'lg_ceallach'), 'melancholic fairy', FAIRY, [33, 34], 6),
            search(Z, (605, 1155), "Search the weeping ring", "a frozen fairy's tear", CRATE,
                   "A tear, frozen hard. Inside it, very small, the picture of a crowned woman walking away across water toward a light."),
            end_talk('lg_ceallach', "Bring the tear to Druid Ceallach", "Their queen. They're weeping for their queen. She walked into the lights. ...And they've been taking travellers to sit in her chair, because a court without a queen comes apart.", 'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [s1, s2]}})

s3 = z.item("Grainne's Ribbon Bracer", 'bracer', 35, 'ward', "Grainne's hair-ribbon, wound round a bracer. She wanted you to have it.")
s4 = z.item("Empty-Chair Ring", 'ring', 35, 'mind', "Cut from the arm of the fairy queen's chair.")
z.quest('lg_taken_girl', 'The Girl in the Chair', 35, 'tadhg_inn',
        "My niece. Grainne. She went up the moor road to her mother's and she didn't get there. The druids say the fairies take people now.\n\nShe's fourteen. Will you [bring her back]? Please.",
        'bring her back',
        "Tadhg's niece Grainne was taken off the moor road by the fairies of the Sorrowing Wood.",
        [
            kill(Z, (520, 1480), "Fight through the militant fairies at the wood's southern edge", 'militant melancholic fairy', MILITANT, [35, 36], 3),
            L('grainne', talk('lg_grainne', "Find Grainne at the fairy court " + where((552, 1316), 'tadhg_inn'),
                              "I'm the queen now. They said. They put a crown on me and it's cold.\n\nThe real queen went to the lake. A light came for her and she went out on the water after it, and she was smiling, and they all cried. Can I go [home]? I don't want to be a queen.", kw='home')),
            end_talk('tadhg_inn', "Bring Grainne home to Tadhg", "Grainne! Oh, girl. Oh, girl.\n\n...She says the queen walked to the lake after a light. Like the touched folk. Like everyone, this year. What is out there?", 'default'),
        ],
        {'default': {'text': "From Tadhg.", 'choice': [s3, s4]}},
        requires='lg_weeping')

s5 = z.item("Moonstone Circlet Charm", 'gem', 36, 'faith', "A stone from the crown the queen left on her chair.")
s6 = z.item("Far Liath's Grey Cloak", 'cloak', 36, 'ward', "The grey men of the wood wear cloaks of mist. This one held.")
z.quest('lg_queens_light', "The Queen's Light", 36, 'lg_ceallach',
        "If the queen went out on the water, she came back - Siofra's seen her in the wood again, at the heart of the court, shining. Shining is the wrong word for a melancholic fairy.\n\nWill you [follow the queen's trail]? The far liath - the grey men - walk that wood now, and they don't belong to it either.",
        "follow the queen's trail",
        "The Melancholic Fairy Queen walked into the lights and came back shining.",
        [
            kill(Z, (640, 1260), "Kill the far liath walking the Sorrowing Wood " + where((640, 1260), 'lg_ceallach'), 'far liath', FAR_LIATH, [35, 36], 4),
            search(Z, (560, 1330), "Search the empty chair at the heart of the court", "a crown of moonstone, left on the chair", CRATE,
                   "The queen's own crown, left behind. Under it, scratched into the seat: 'He promised the light would stop the weeping. It did.'"),
            end_talk('lg_ceallach', "Report to Druid Ceallach", "'He'. The herald. Whatever sits on the crannog promised a melancholic fairy her sorrow would stop - and the price was everything she was. And her court weeps, and takes children.\n\nShe has to be laid to rest. It'll take more than one of you.", 'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [s5, s6]}},
        requires='lg_taken_girl')

s7 = z.item("Lament-Breaker's Torc", 'neck', 37, 'might', "Moonstone and grey silver. It's quiet. Everything near it is quiet.")
s8 = z.item("Mantle of the Sorrowing Wood", 'cloak', 37, 'ward', "Woven by the fairies after their queen was laid to rest. It's the first thing they've made in years.")
s9 = z.item("Unweeping Ring", 'ring', 37, 'charm', "A melancholic fairy's ring. It used to be wet.")
z.quest('lg_fairy_queen', 'The Melancholic Queen', 37, 'lg_ceallach',
        "GROUP work.\n\nThe Melancholic Fairy Queen sits in the heart of her court again, full of the Glimmer's light, and her court weeps round her. She's old, and strong, and she won't come quietly.\n\nWill you [lay her to rest]? Bring friends. Bring healers.",
        'lay her to rest',
        "GROUP. The Melancholic Fairy Queen sits in the heart of her court, full of the Glimmer's light. Lay her to rest.",
        [
            hunt((546, 1318), "Defeat the Melancholic Fairy Queen in the heart of the Sorrowing Wood " + where((546, 1318), 'lg_ceallach'), 'Melancholic Fairy Queen',
                 text="The queen falls, and the light goes out of her in a long sigh. For the first time in a year the wood is silent - and then, very softly, the fairies start to sing. Not weeping. Singing."),
            choice('lg_ceallach', "Report to Druid Ceallach",
                   "Singing. You can hear it from here.\n\nThe court will need a queen. One of their own, this time. We could [let them choose], and hope the one they choose was never near the lake. Or the Circle could [crown one ourselves] - one we've watched, one we're sure of. That's a kind of taking too.",
                   [('let them choose', "Let them choose. They've had enough taken from them.", 'ending:choose'),
                    ('crown one ourselves', "Then we'll choose. And we'll watch her. And one day they'll weep about that too.", 'ending:crowned')]),
        ],
        {'choose': {'text': "From Aine's Circle and the fairies.", 'items': [s8], 'choice': [s7, s9]},
         'crowned': {'text': "From Aine's Circle.", 'items': [s8], 'choice': [s7, s9]}},
        requires='lg_queens_light', group=True)

# ======================================================================== The Earl Beneath the Lake (34-38) - the Circle, GROUP finale
e1 = z.item("Silver Horseshoe Charm", 'gem', 34, 'charm', "A silver horseshoe worn thin as a leaf. The Earl's horse threw it.")
e2 = z.item("Barrow-Iron Bracer", 'bracer', 34, 'might', "From a dullahan's saddle.")
z.quest('lg_silver_shoes', 'The Silver Shoes', 34, 'lg_ceallach',
        "You know the story. Gearoid Iarla, the Earl, sleeps under Lough Gur with his army, and every seventh year he rides out round the lake on a horse shod with silver. When the shoes wear through he wakes for good.\n\nHe's been riding every night this spring. Every night. His host waits on the west shore for him. Will you [go to the Earl's barrow]? I want to see a shoe.",
        "go to the Earl's barrow",
        "The Earl rides round Lough Gur every night now, not every seventh year - and his host waits on the west shore.",
        [
            kill(Z, (700, 930), "Kill the dullahans at the Earl's barrow on the west shore " + where((700, 930), 'lg_ceallach'), 'dullahan', DULL, [34, 35], 4),
            search(Z, (705, 935), "Search the Earl's barrow", "a silver horseshoe, worn thin", CRATE,
                   "A silver horseshoe, worn as thin as a leaf - a year's riding in a month. The nails glow faintly, the same light as the lake.", give='the silver horseshoe'),
            end_talk('lg_ceallach', "Bring the horseshoe to Druid Ceallach", "Worn thin in a month. Something is riding the Earl - spurring him round and round, to wear the shoes through.\n\nWhen they break, he wakes, and his army with him. A sleeping army under Lough Gur. Whoever wakes it, owns it.", 'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [e1, e2]}})

e3 = z.item("Envoy's Thorn Seal", 'ring', 36, 'mind', "The Unseelie Court's seal: a crowned woman in thorns.")
e4 = z.item("Moor-Walker's Boots-Charm", 'gem', 36, 'finesse', "From the moor, where the envoy waited.")
z.quest('lg_envoy', 'The Envoy', 36, 'lg_maeve',
        "A Sentinel saw something odd on the deamhan moor, south of the lake: a tall pale man in court clothes, standing still among the deamhan as if they were dogs. He's been there a week. Waiting for someone.\n\nI don't like court clothes on a moor. Will you [see who he is]? Mind the deamhan.",
        'see who he is',
        "A pale man in court clothes waits among the deamhan on the moor south of the lake.",
        [
            reach(Z, (1150, 1480), "Find the pale man on the deamhan moor " + where((1150, 1480), 'lg_maeve'), "He stands among the deamhan like a man among dogs. He sees you, and smiles, and puts his hand on his sword.", r=25),
            hunt((1174, 1520), "Kill the unseelie envoy on the moor", 'unseelie envoy',
                 text="On the envoy: a letter, sealed with a crowned woman in thorns. 'From the Queen of the Unseelie Court to Cuuldurach, King of the Glimmer. The north for me, the south for you, and Lug between us. My envoy waits on the moor for your herald's answer.'"),
            end_talk('lg_maeve', "Bring the letter to Sentinel Maeve", "Cliodna. The Unseelie Queen. In the north they say she's behind everything wrong from Connacht to the Cliffs. And she's writing to the Glimmer King.\n\nThe herald. On the crannog. Take this to Ceallach. Then we go out to that island.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [e3, e4]}},
        requires='lg_silver_shoes')

e5 = z.item("Herald's Glass Torc", 'neck', 38, 'mind', "The Glimmer's herald wore light like other men wear cloth. This is what was left.")
e6 = z.item("Mantle of the Lake", 'cloak', 38, 'ward', "Aine's Circle's own, given to those who went out to the crannog.")
e7 = z.item("Lullaby Ring", 'ring', 38, 'faith', "Dara's tune is scratched inside the band.")
z.quest('lg_crannog', 'The Crannog', 38, 'lg_ceallach',
        "GROUP work - the most of it you've done here.\n\nThe herald sits on the crannog - the island in the lake. The lights are his fishing-lines, the Earl's shoes his work, the gurites his paid men, the Queen of the Unseelie Court his correspondent. He is Cuuldurach's voice in the north.\n\nWade out with friends, and say [to the crannog].",
        'to the crannog',
        "GROUP. The Glimmer's herald sits on the crannog in Lough Gur: Cuuldurach's voice in the north.",
        [
            reach(Z, (940, 860), "Wade out to the crannog in the lake " + where((940, 860), 'lg_ceallach'), "The water is warm, and lit from below. On the island, something stands up, and it is made of light.", r=25),
            boss(Z, (949, 874), "Defeat the Glimmer's herald on the crannog",
                 "The herald comes apart into sparks, and the sparks sink, and the lake goes dark - properly dark, for the first time this year. Under the water, very far down, a horse stops stamping.",
                 'Fionnlugh, Herald of the Glimmer', WARSHADE, 40, "A shape of white light turns on the crannog. 'The Glimmer King sends his greetings to Lough Gur. He will come for his army himself, in time. South-east, through the bog, as the light goes. Tell them.'",
                 objective='Defeat Fionnlugh, Herald of the Glimmer', hp=5.0, adds=[(GLIM, 'glimmer light', [36, 37]), (WISP, 'glimmer wisp', [37, 38])], every=20, count=3),
            choice('lg_ceallach', "Report to Druid Ceallach",
                   "The lake's dark. The Earl's asleep. Dara's tune is all we need now, and Dara can play it.\n\nThe herald said south-east, through the bog. The Bog of Cullen. The Keeners there have been seeing lights all year. We should [warn the Keeners] - or we [keep the Circle home] and guard the lake, in case he comes back. The lake is what we're for.",
                   [('warn the Keeners', "Then I'll send word to Old Sadhbh at Alainn Bin. And you - you go too. That's where this goes next.", 'ending:south'),
                    ('keep the Circle home', "Home, then. We'll sing the lake to sleep every night. You'll go south anyway; I can see it.", 'ending:home')]),
        ],
        {'south': {'text': "From Aine's Circle.", 'items': [e6], 'choice': [e5, e7]},
         'home': {'text': "From Aine's Circle.", 'items': [e6], 'choice': [e5, e7]}},
        requires='lg_envoy', group=True)

# ======================================================================== The Azure (32-35): neutral, then hostile
a1 = z.item("Azure Novice's Ring", 'ring', 32, 'faith', "Blue enamel on iron. 'Burn the light.'")
a2 = z.item("Cleanser's Belt", 'belt', 32, 'might', "An Azure cleanser's belt, with loops for torches.")
z.quest('lg_azure_welcome', 'The Order of the Azure', 32, 'lg_ennis',
        "You've seen the lights on the lake. Good. Most people here call them pretty.\n\nThe Order of the Azure has fought the Glimmer since before your grandmother was born. In the south it took the Sheeroe Hills; it will not take Lough Gur. Will you [hunt the lights] for us? They come up off the water on the west shore.",
        'hunt the lights',
        "Brother Ennis of the Order of the Azure wants the Glimmer's lights hunted off the lake.",
        [
            kill(Z, (680, 1000), "Put out the Glimmer's lights on the west shore " + where((680, 1000), 'lg_ennis'), 'glimmer light', GLIM, [32, 33], 6),
            end_talk('lg_ennis', "Report to Brother Ennis", "Six. Good. Six fewer eyes on this lake.\n\nYou'll do. The Order has more work - harder work. Come back when you have the stomach for it.", 'default'),
        ],
        {'default': {'text': "From the Order of the Azure.", 'choice': [a1, a2]}})

a3 = z.item("Azure Wisp-Catcher Bracer", 'bracer', 34, 'ward', "Blue iron, banded. The wisps can't get a grip on it.")
a4 = z.item("Blue Flame Charm", 'gem', 34, 'charm', "A flame that burns blue in a glass bead. Only the Azure know how.")
z.quest('lg_azure_wisps', 'The Wisps of the Crannog', 34, 'lg_ennis',
        "The lights have keepers: wisps, brighter and harder, that come ashore at night near the crannog. Kill a keeper and its lights go out for a week.\n\nWill you [hunt the wisps]? You'll need to be on the north jetty at night. Bring blue fire if you have it. You don't. Bring friends.",
        'hunt the wisps',
        "Brother Ennis wants the Glimmer's wisps hunted on the shore by the crannog.",
        [
            kill(Z, (1000, 820), "Kill the glimmer wisps on the shore by the crannog " + where((1000, 820), 'lg_ennis'), 'glimmer wisp', WISP, [34, 35], 3),
            end_talk('lg_ennis', "Report to Brother Ennis", "Three keepers. The lake will be darker for it.\n\nNow. The real work. Come back when you're ready for it - and don't tell the druids. They're soft about this.", 'default'),
        ],
        {'default': {'text': "From the Order of the Azure.", 'choice': [a3, a4]}},
        requires='lg_azure_welcome')

a5 = z.item("Siofra's Thanks", 'ring', 35, 'faith', "Rush and silver. 'Touched, not lost.'")
a6 = z.item("Torch-Breaker's Bracer", 'bracer', 35, 'might', "You broke the Azure's torch over your knee. This was its iron.")
z.quest('lg_azure_burning', 'The Burning', 35, 'lg_ennis',
        "The Glimmer fishes for the touched, and the touched go in the water and come out lanterns. You've seen it.\n\nSo the Order will take the bait away. Carry this torch to the touched folk's camp in the south-west woods and [light the signal] at its edge, where the trees are dry. My brothers will see it and come. The rest is ours to do.",
        'light the signal',
        "Brother Ennis gives you a torch to light a signal at the touched folk's camp. The Azure mean to burn it.",
        [
            reach(Z, (440, 1100), "Carry the Azure torch to the edge of the touched folk's camp " + where((440, 1100), 'lg_ennis'),
                  "The torch smells of pitch and lamp oil - a lot of lamp oil. Far more than a signal needs.", r=20),
            search(Z, (446, 1106), "Look at the dry trees where the signal is to go", "a ring of oil-soaked brushwood round the camp", CRATE,
                   "Brushwood, soaked in oil, piled in a ring round the whole camp - and a sealed order tucked in it: 'At the signal, fire the ring. What the Glimmer touches is already lost. Let none walk out. - Brother-Captain Ultan.'",
                   give='the Azure order'),
            end_talk('lg_siofra', "Show Druid Siofra the order", "Let none walk out.\n\nThey'd burn them. All of them, in their sleep. Because a light touched them once.\n\nWe go now - into the trees, all of us - and when Ultan's crusaders come, they'll find you instead. The Azure will never forgive this. Good.", 'default'),
        ],
        {'default': {'text': "From Druid Siofra and the touched folk.", 'choice': [a5, a6], 'wake_event': 'lg_azure_burning'}},
        requires='lg_azure_wisps')

if __name__ == '__main__':
    for zz in ZONES:
        errs = zz.check()
        print(zz.name, len(zz.quests), 'quests', len(zz.items), 'items', errs or 'ok')
