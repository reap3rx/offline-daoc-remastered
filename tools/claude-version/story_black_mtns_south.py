"""Black Mountains South's story quests (claude 2026-11-24, "Albion - the plan" in Zone Reviews) - see story_gen.py. Places:
zone metres [x, y].  python tools/claude-version/story_gen.py story_black_mtns_south

The Crimson thread runs north out of Camelot Hills to "the Bishop": Dark Bishop Burhoff of Vetusta Abbey, who has filled his
abbey with Morgana's "brothers" and driven the true monks out. The goblins of Tepok's Mine have dug into a cairn of Arthur's dead
from Mount Badon and sell the bones to the Crimson, who raise them in the river. At the end, the Bishop's letters point on:
"the stones of Salisbury" and "the gate in the lake".

The zone's two older quests are kept as they were (singing_bridge, willing_heart).

Arcs (recommended levels):
  Ludlow's Troubles (2-7) - the Pendragon's Watch at Ludlow
  The River Road (5-8) - robbers and highwaymen who let red-corded travellers pass
  Hill and Wood (6-12) - spiders, nain raiders, red dwarves
  What the Goblins Dug (10-14) - Tepok's Mine and the Badon cairn
  The Dark Bishop (10-17) - the Abbey Faithful: retake Vetusta
"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, '/home/claude/z/geo')
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L, HERE
try:
    import geo
except ImportError:
    geo = None

CRATE, BEDROLL, LANTERN = 1347, 1882, 1876
M, F, OLD = 9, 38, 32
Z = 2
ZONES = []
z = Zone(Z, 'Black Mountains South', 1, 'alb_black_mtns_south')
ZONES.append(z)
AT, NAMES = {}, {}


def keep_old():
    """The zone's three older quests, their people and their rewards, as they were."""
    q = json.loads((HERE.parents[1] / 'source/server/GameServer/scripts/storyquests/quests/alb_black_mtns_south.json').read_text(encoding='utf-8'))
    spec = json.loads((HERE / 'named_uniques/story002_black_mtns_south.json').read_text(encoding='utf-8'))
    old_ids = {'singing_bridge', 'willing_heart'}
    for qq in q['quests']:
        if qq['id'] in old_ids:
            for e in qq['endings'].values():
                e['rewards'].setdefault('items', [])
                e['rewards'].setdefault('choice', [])
            z.quests.append(qq)
            z.labels[qq['id']] = {}
    keep_npcs = {'wren_piper', 'corwen_fisher', 'pip_piper', 'sister_aldith', 'hedda_woodcutter', 'brother_osric'}
    for n in q['npcs']:
        if n['id'] in keep_npcs:
            z.npcs.append(n)
            NAMES[n['id']] = n['name']
            AT[n['id']] = tuple(n['pos'][:2])
    old_names = {"Pip's Bell-Charm", 'River-Stone Ring', 'Reed-Woven Sash', "Fisherman's Mantle", 'Menhir-Chip Amulet', "Osric's Scrip",
                 "Sacrificer's Sickle-Pin", 'Band of Mercy'}
    for it in spec['items']:
        if it['name'] in old_names:
            z.items.append(it)


def P(x, y):
    if geo and not geo.dry(Z, x, y, 4):
        n = geo.dry_near(Z, x, y, 60)
        if n:
            return n
    return (x, y)


def person(id, name, xy, kind, level, **kw):
    xy = P(*xy)
    NAMES[id] = name
    AT[id] = tuple(xy)
    z.npc(id, name, list(xy), kind, level, **kw)


def where(to, frm):
    fx, fy = AT[frm]
    dx, dy = to[0] - fx, to[1] - fy
    d = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(-dy, dx)) % 360
    names = ['east', 'north-east', 'north', 'north-west', 'west', 'south-west', 'south', 'south-east']
    dirn = names[int(((ang + 22.5) % 360) // 45)]
    dist = ('%d m' % (round(d / 10) * 10)) if d < 950 else ('%.1f km' % (d / 1000))
    return 'about %s %s of %s' % (dist, dirn, NAMES[frm])


def hunt(xy, goal, target, count=1, text=None, r=50):
    st = {'type': 'kill', 'zone': Z, 'at': list(P(*xy)), 'radius': r, 'goal': goal, 'target': target, 'count': count}
    if text:
        st['text'] = text
    return st


keep_old()

CRATE_=CRATE
ACOLYTE, INITIATE, BANDIT = 12284, 12075, 12447

# ------------------------------------------------------------------ people
person('bs_reeve_gwenda', 'Reeve Gwenda', (1190, 1125), 'f', 30, guild="the Pendragon's Watch",
       idle="Ludlow sent forty men to Camlann. Eleven came home. The other twenty-nine are in the graveyard, and they won't stay there.")
person('bs_ferryman_huw', 'Huw the Ferryman', (720, 800), 'm', 24, idle="I've ferried the living across this river thirty years. Lately the dead want a ride.")
person('bs_sergeant_mabyn', 'Sergeant Mabyn', (522, 1000), 'm', 36, guild="the Pendragon's Watch",
       idle="Humberton keep. Four walls, one gate and nowhere near enough men.")
person('bs_prior_anselm', 'Prior Anselm', (648, 1096), 'old', 40, guild='the Abbey Faithful',
       idle="Vetusta's bell has rung the hours for three hundred years. It hasn't rung since the Bishop's new brothers came.")
person('bs_brother_teilo', 'Brother Teilo', (660, 1088), 'm', 22, guild='the Abbey Faithful',
       idle="They threw us out with nothing but our habits. I kept my psalter. I'll have the abbey back too.")
person('bs_scout_elowen', 'Scout Morfudd', (520, 44), 'f', 32, guild="the Pendragon's Watch",
       idle="Goblins I can count. What the goblins are carrying out of that mine, I don't like.")

# ======================================================================== Ludlow's Troubles (2-7)
l1 = z.item("Anthill Pebble Ring", 'ring', 2, 'ward', "A pebble the ants polished smooth, set in copper.")
l2 = z.item("Ludlow Gardener's Sash", 'belt', 2, 'charm', "Green and patched. Ludlow wastes nothing.")
z.quest('bs_ants_in_ludlow', 'Ants in the Cabbages', 2, 'bs_reeve_gwenda',
        "Ants. The size of cats, in my cabbages. They come up from a hill south of the road and strip a field in a night.\n\nI can't spare the Watch for ants. Will you [stop the ants]? Break up their hill and they'll go somewhere else.",
        'stop the ants',
        "Giant ants from a hill south of Ludlow are stripping the fields.",
        [
            hunt((1150, 1000), "Kill the ants in Ludlow's fields " + where((1150, 1000), 'bs_reeve_gwenda'), 'large ant', 6),
            hunt((892, 1332), "Break up the anthill south of the road", 'ant drone', 3),
            end_talk('bs_reeve_gwenda', "Tell Reeve Gwenda", "Cabbages. Saved. You'd laugh, but that's half of Ludlow's winter.", 'default'),
        ],
        {'default': {'text': "From Reeve Gwenda.", 'choice': [l1, l2]}})

l3 = z.item("Camlann Mourning Band", 'ring', 4, 'faith', "Black iron. Every family in Ludlow that lost a son at Camlann wears one.")
l4 = z.item("Sexton's Spade-Pin", 'gem', 4, 'might', "A little iron spade. The sexton gave you his own.")
l5 = z.item("Grave-Dust Bracer", 'bracer', 4, 'ward', "It never quite comes clean.")
z.quest('bs_camlann_dead', 'The Men Who Came Home', 4, 'bs_reeve_gwenda',
        "Ludlow sent forty men to Camlann with the King. Twenty-nine came home in carts, and we buried them in the graveyard north of the road.\n\nThis month they've started getting up. Bones walking among the stones, and hounds that aren't there howling in the fields. Will you [go to the graveyard]? Find out who's waking them.",
        'go to the graveyard',
        "The Camlann dead of Ludlow are rising from their graves.",
        [
            hunt((1056, 930), "Lay the risen dead in Ludlow graveyard to rest " + where((1056, 930), 'bs_reeve_gwenda'), 'weak skeleton', 5),
            hunt((1100, 1000), "Kill the spectral hounds in the fields", 'spectral hound', 3),
            search(Z, P(1060, 925), "Search the graves that were opened", "an opened grave with a red cord on the stone", CRATE,
                   "Every opened grave has a red cord knotted round its headstone, thirteen knots each. Someone came at night, and tied them, and went away."),
            end_talk('bs_reeve_gwenda', "Show the red cord to Reeve Gwenda",
                     "Thirteen knots. The new brothers up at Vetusta wear cords like this round their waists. Red ones.\n\nPrior Anselm is in Humberton - they threw him out of his own abbey. He'll know what it means.", 'default'),
        ],
        {'default': {'text': "From Reeve Gwenda, for Ludlow's dead.", 'choice': [l3, l4, l5]}})

l6 = z.item("Ferryman's Coin", 'gem', 7, 'charm', "A coin with a hole in it. Huw says it pays your passage, one way or the other.")
l7 = z.item("Drowned Man's Ring", 'ring', 7, 'mind', "Found in the river. Huw blessed it, then thought better and blessed it again.")
l8 = z.item("River-Weed Mantle", 'cloak', 7, 'ward', "Dried and woven. Smells of the river, faintly, always.")
z.quest('bs_drowned_reach', 'The Drowned Reach', 7, 'bs_ferryman_huw',
        "The goblins fish this river. Fished, I should say - the drowned ones are getting up out of it now, still holding their nets. Grey and wet and walking.\n\nThe river doesn't do that by itself. Will you [search the reach]? Upstream, where the water's slow and deep.",
        'search the reach',
        "Drowned goblin fishermen are rising from the river. Huw the Ferryman wants to know why.",
        [
            hunt((700, 650), "Put down the drowned fishermen in the reach " + where((700, 650), 'bs_ferryman_huw'), 'undead goblin fisherman', 5),
            search(Z, P(690, 640), "Search the riverbed in the slow water", "a black stone on the riverbed", CRATE,
                   "A black stone sunk in the mud, a red key on it, and round it a ring of bones - not goblin bones. Old, big, and wrapped in rotted mail."),
            hunt((600, 610), "Kill the drowned warriors at the singing pool", 'undead goblin warrior', 2),
            end_talk('bs_ferryman_huw', "Tell Huw what you found",
                     "Men's bones in mail, at the bottom of my river? There's no battlefield on this river.\n\n...Unless someone carried them here. From somewhere else.", 'default'),
        ],
        {'default': {'text': "From Huw.", 'choice': [l6, l7, l8]}},
        requires='bs_camlann_dead')

l9 = z.item("Marsh-Scale Belt", 'belt', 6, 'finesse', "Slith scale, green and gold.")
l10 = z.item("Reed-Mother's Eye", 'gem', 6, 'mind', "A slith's eye, set in silver. It still blinks, occasionally.")
z.quest('bs_mother_of_marsh', 'The Mother of the Marsh', 6, 'bs_reeve_gwenda',
        "There's a marsh south of Ludlow, and something in it laying eggs. The slith broodlings come up into the road at dusk now.\n\nThe mother's called Slith - the old women named her. Will you [go to the marsh]?",
        'go to the marsh',
        "Slith broodlings from the marsh south of Ludlow are coming up into the road.",
        [
            hunt((1080, 1420), "Kill the slith broodlings in the marsh " + where((1080, 1420), 'bs_reeve_gwenda'), 'slith broodling', 6),
            hunt((1064, 1397), "Kill Slith, the mother of the marsh", 'Slith', 1, text="Slith thrashes once in the reeds, and lies still."),
            end_talk('bs_reeve_gwenda', "Tell Reeve Gwenda", "The old women'll be disappointed. They liked having a monster.", 'default'),
        ],
        {'default': {'text': "From Ludlow.", 'choice': [l9, l10]}})

# ======================================================================== The River Road (5-8)
r1 = z.item("Landing-Stage Ring", 'ring', 6, 'might', "Hammered from a robber's iron mooring ring.")
r2 = z.item("Ferry-Rope Belt", 'belt', 6, 'finesse', "Tarred rope. Huw's own.")
z.quest('bs_robbers_landing', "Robbers' Landing", 6, 'bs_ferryman_huw',
        "Robbers have taken the old landing west of my ferry. They wait for the boats and take everything - and the strange thing is, they let some folk by.\n\nWill you [clear the landing]? And find out who they let pass.",
        'clear the landing',
        "Robbers have taken the old landing on the river west of the ferry.",
        [
            hunt((537, 760), "Clear the robbers from the landing " + where((537, 760), 'bs_ferryman_huw'), 'robber', 5),
            search(Z, P(540, 755), "Search the robbers' lean-to", "a lean-to of oars and sailcloth", CRATE,
                   "A note, scrawled: 'Them as wears the red cord, let by. The Bishop pays.'"),
            end_talk('bs_ferryman_huw', "Tell Huw", "'The Bishop pays.' Robbers, paid by a bishop. I've lived too long.", 'default'),
        ],
        {'default': {'text': "From Huw.", 'choice': [r1, r2]}})

r3 = z.item("Highwayman's Mask-Pin", 'gem', 8, 'finesse', "A little silver mask. Very dashing. Very stolen.")
r4 = z.item("Watch Courier's Bracer", 'bracer', 8, 'ward', "Recovered from the ambush. The courier won't need it.")
r5 = z.item("Ludlow Road Mantle", 'cloak', 8, 'charm', "Dusty brown. The road's own colour.")
z.quest('bs_highway', 'The Ludlow Highway', 8, 'bs_sergeant_mabyn',
        "My couriers to Ludlow aren't arriving. The road north-east of the town goes through a cut, and there's a gang of highwaymen in it.\n\nThe last courier was carrying my report on the abbey. Will you [find my courier]? Or what's left of him.",
        'find my courier',
        "Watch couriers on the Ludlow road are being ambushed by highwaymen.",
        [
            hunt((1100, 820), "Clear the bandits on the highway " + where((1100, 820), 'bs_sergeant_mabyn'), 'bandit', 4),
            hunt((1211, 774), "Kill the highwaymen in the cut", 'highwayman', 2),
            search(Z, P(1215, 780), "Search the ambush for the courier's satchel", "a Watch satchel, slit open", CRATE,
                   "The courier's report is gone. In its place, a red cord with thirteen knots - left on purpose."),
            end_talk('bs_sergeant_mabyn', "Tell Sergeant Mabyn", "They took my report on the abbey and left me a calling card. The Bishop wants me to know he knows.\n\nWell. Now I know too.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [r3, r4, r5]}},
        requires='bs_robbers_landing')

# ======================================================================== Hill and Wood (5-12)
h1 = z.item("Spider-Silk Wrap", 'bracer', 5, 'finesse', "Strong as wire and light as nothing.")
h2 = z.item("Messenger's Thanks", 'gem', 5, 'charm', "A Watch button. The messenger insisted.")
z.quest('bs_webs', 'Webs over the North Road', 5, 'bs_sergeant_mabyn',
        "A messenger from the northern outpost left four days ago and never arrived. The forest north of the river is full of giant spiders.\n\nWill you [search the forest]? Spiders keep what they catch. He might still be alive.",
        'search the forest',
        "A Watch messenger went missing in the spider-ridden forest north of the river.",
        [
            hunt((700, 300), "Kill the giant spiders in the north forest " + where((700, 300), 'bs_sergeant_mabyn'), 'giant spider', 6),
            search(Z, P(760, 260), "Search the webs for the messenger", "a man-sized cocoon", CRATE,
                   "You cut the cocoon open. Inside, the messenger - grey, half-starved and very much alive. 'Water,' he croaks. 'And tell the sergeant... goblins. Carrying bones south.'"),
            end_talk('bs_sergeant_mabyn', "Tell Sergeant Mabyn", "Alive! God be thanked. Bones south... from the mine? Scout Morfudd's at the northern outpost. She'll want to hear it.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [h1, h2]}})

h3 = z.item("Nain-Iron Ring", 'ring', 10, 'might', "Dwarf-work. Too heavy for its size.")
h4 = z.item("Frund's Beard-Clasp", 'gem', 10, 'ward', "Gold. Frund was very proud of his beard.")
h5 = z.item("Hearth-Stone Belt", 'belt', 10, 'ward', "Set with a chip of the nain's hearth.")
z.quest('bs_nain_raids', 'The Nain Raids', 10, 'bs_sergeant_mabyn',
        "Dwarves. Nain, they call themselves - not like the pilgrims in Camelot Hills; these came down out of the west hills this spring and they've been raiding Humberton's farms ever since.\n\nTheir war-leader is called Frund. Will you [stop the raids]?",
        'stop the raids',
        "Nain dwarves from the west hills are raiding Humberton's farms.",
        [
            hunt((300, 1250), "Fight off the nain raiders on the west road " + where((300, 1250), 'bs_sergeant_mabyn'), 'dwarf raider', 5),
            hunt((215, 1264), "Defeat Frund, the nain war-leader", 'Frund', 1,
                 text="Frund falls. 'Red-hand men burned our halls,' he gasps. 'We only took back what we lost.'"),
            choice('bs_sergeant_mabyn', "Tell Sergeant Mabyn what Frund said",
                   "Red-hand men burned their halls? The Crimson, again - driving the nain onto us, to keep my men busy. The same trick they played in Camelot Hills.\n\nWe could [make peace] with the nain - send them grain and an apology. Or [hold the line]; raiders are raiders.",
                   [('make peace', "Grain and an apology. And maybe one day an axe on our side when the Crimson come.", 'ending:peace'),
                    ('hold the line', "Then the west road stays guarded. Thank you for Frund, at least.", 'ending:line')]),
        ],
        {'peace': {'text': "The nain send a gift down from the hills.", 'items': [h3], 'choice': [h4, h5]},
         'line': {'text': "From the Pendragon's Watch.", 'choice': [h3, h4, h5]}})

h6 = z.item("Red Dwarf Earring", 'gem', 12, 'finesse', "Taken from Agisthil's ear. He had several.")
h7 = z.item("Thief-Catcher's Bracer", 'bracer', 12, 'might', "Ludlow's reward to whoever stopped the thieving.")
z.quest('bs_red_dwarves', 'Red Dwarves of the East Wood', 12, 'bs_reeve_gwenda',
        "Red dwarves in the east woods - thieves, every one. They take tools, pots, anything metal. Now they've taken the church bell's clapper, and Ludlow can't ring for its dead.\n\nTheir camp's in the far north-east, and their chief is Agisthil. Will you [get the clapper back]?",
        'get the clapper back',
        "Red dwarf thieves from the east woods stole Ludlow church's bell clapper.",
        [
            hunt((1250, 600), "Fight through the red dwarf thieves in the east woods " + where((1250, 600), 'bs_reeve_gwenda'), 'red dwarf thief', 6),
            hunt((1347, 432), "Defeat Agisthil at the red dwarf camp", 'Agisthil', 1),
            search(Z, P(1350, 445), "Search the camp for the clapper", "a heap of stolen metal", CRATE,
                   "Pots, nails, horseshoes - and the iron clapper of Ludlow's bell, wrapped in a red cord. Somebody paid them to take it.", give="Ludlow's bell clapper"),
            end_talk('bs_reeve_gwenda', "Return the clapper to Reeve Gwenda", "Our bell! Now Ludlow can ring for its dead again - and lay them down properly.\n\nSomebody doesn't want bells rung in these mountains. I wonder why.", 'default'),
        ],
        {'default': {'text': "From Ludlow.", 'choice': [h6, h7]}})

# ======================================================================== What the Goblins Dug (10-14)
g1 = z.item("Goblin Pick-Head Charm", 'gem', 11, 'might', "A tiny pick, goblin-forged. Badly.")
g2 = z.item("Lookout's Spyglass Belt", 'belt', 11, 'finesse', "The glass is cracked. The belt is fine.")
z.quest('bs_goblins_north', 'Bones Going South', 11, 'bs_scout_elowen',
        "The goblins of Tepok's Mine have been coming out at night with sacks. Heavy sacks. They carry them south to the river and come back with silver.\n\nWill you [stop a sack]? Kill their scouts on the raid path and see what they're carrying.",
        'stop a sack',
        "The goblins of Tepok's Mine carry heavy sacks south to the river by night.",
        [
            hunt((300, 280), "Kill the goblin scouts on the raid path " + where((300, 280), 'bs_scout_elowen'), 'goblin scout', 4),
            search(Z, P(305, 285), "Open a goblin's sack", "a heavy sack, dropped in the bracken", CRATE,
                   "Bones. A man's - big, old, and with a rusted torc round the neck. A brooch in the sack: a red dragon on a field of gold."),
            end_talk('bs_scout_elowen', "Show the brooch to Scout Morfudd",
                     "The red dragon. That's Arthur's. That's the badge his men wore at Mount Badon, before any of us were born.\n\nThe goblins have dug into a cairn of Arthur's dead.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [g1, g2]}},
        topics={'mount badon': "Arthur's great victory, twelve battles in. The Saxons broke and there was peace for a generation."})

g3 = z.item("Badon Torc", 'neck', 13, 'might', "Bronze, very old, from the cairn. Morfudd says you'll honour it.")
g4 = z.item("Red Dragon Brooch", 'gem', 13, 'faith', "Arthur's badge, from Mount Badon.")
g5 = z.item("Grilk's Toll Ring", 'ring', 13, 'finesse', "Grilk charged everyone a toll to enter the mine. Now he doesn't.")
z.quest('bs_badon_cairn', 'What the Goblins Dug', 13, 'bs_scout_elowen',
        "The goblins broke into the cairn and found it full - Arthur's men from Badon, buried with their arms. Somebody's buying the bones. And the drowned in the river, Huw says, wear old mail.\n\nGrilk leads the diggers. Will you [close the cairn]? Kill Grilk and see what's left in the mine mouth.",
        'close the cairn',
        "The goblins of Tepok's Mine have broken into a cairn of Arthur's dead from Mount Badon and sell the bones.",
        [
            hunt((209, 140), "Fight into the goblin camp " + where((209, 140), 'bs_scout_elowen'), 'goblin', 6),
            hunt((106, 140), "Defeat Grilk, who leads the diggers", 'Grilk', 1),
            search(Z, P(135, 85), "Search the mine mouth", "a cart of bones, and a ledger", CRATE,
                   "A cart of bones, sorted and labelled, and a goblin ledger in a very human hand: 'Bones of Badon, by the cart, to the river. For the Bishop: these remember how to fight.'"),
            choice('bs_scout_elowen', "Tell Scout Morfudd what you found",
                   "'These remember how to fight.' He's raising an army from Arthur's own dead. God.\n\nWe can [rebury them] in the cairn, and seal it. Or [carry them to Ludlow] and lay them in holy ground beside the Camlann men.",
                   [('rebury them', "Back to the cairn, and stones over the door. They'll rest where they fell.", 'ending:cairn'),
                    ('carry them to Ludlow', "Ludlow's bell will ring for them. Gwenda will see to it.", 'ending:ludlow')]),
        ],
        {'cairn': {'text': "From the Pendragon's Watch.", 'items': [g3], 'choice': [g4, g5]},
         'ludlow': {'text': "Ludlow rings its bell for Badon's dead.", 'items': [g4], 'choice': [g3, g5]}},
        requires='bs_goblins_north')

g6 = z.item("Gobzini's Conjuring Ring", 'ring', 14, 'mind', "It still sparks when you snap your fingers.")
g7 = z.item("Goblin Lord's Belt", 'belt', 14, 'might', "Far too big for a goblin. He wore it anyway.")
g8 = z.item("Watch-Captain's Mantle", 'cloak', 14, 'ward', "Watch blue, with a goblin-sized hole in the hem.")
z.quest('bs_gobzini', 'The Great Gobzini', 14, 'bs_scout_elowen',
        "One goblin knows the price of bones better than the rest: the Great Gobzini, a conjurer, who sits in the far north corner of the hills and does the Bishop's bargaining. The Goblin Lord does what he says.\n\nWill you [end the trade]? You'll want friends - he's no fool.",
        'end the trade',
        "The Great Gobzini, a goblin conjurer, bargains the bones of Badon to the Bishop.",
        [
            hunt((108, 160), "Defeat the Goblin Lord " + where((108, 160), 'bs_scout_elowen'), 'Goblin Lord', 1),
            hunt((74, 18), "Defeat the Great Gobzini", 'The Great Gobzini', 1,
                 text="Gobzini goes up in a puff of green smoke and doesn't come down."),
            end_talk('bs_scout_elowen', "Tell Scout Morfudd", "No Gobzini, no bargain. The trade's done. Now it's only the Bishop.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [g6, g7, g8]}},
        requires='bs_badon_cairn', group=True)

# ======================================================================== The Dark Bishop (10-17) - the Abbey Faithful
v1 = z.item("Salizern's Focus", 'gem', 10, 'mind', "A summoner's crystal. Cold, now.")
v2 = z.item("Humberton Guard's Ring", 'ring', 10, 'might', "Iron, plain, given to every man on the keep's walls.")
z.quest('bs_summoner', 'The Summoner in the West Field', 10, 'bs_sergeant_mabyn',
        "There's a man in the field west of Humberton who calls things up out of the ground. Salizern, he calls himself. He came the week the new brothers came to Vetusta.\n\nWill you [deal with him]? Bring me whatever he carries.",
        'deal with him',
        "A summoner called Salizern calls things up in the field west of Humberton.",
        [
            hunt((316, 1041), "Defeat Summoner Salizern " + where((316, 1041), 'bs_sergeant_mabyn'), 'Summoner Salizern', 1),
            end_talk('bs_sergeant_mabyn', "Tell Sergeant Mabyn", "He carried a red cord too? Of course he did. Every rat in these mountains wears one.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [v1, v2]}})

v3 = z.item("Prior's Psalter-Clasp", 'gem', 12, 'faith', "Brass, worn smooth by the Prior's thumb.")
v4 = z.item("Cloister Cord", 'belt', 12, 'faith', "A plain white cord - the true brothers' - to replace the red.")
v5 = z.item("Abbey Gatekeeper's Ring", 'ring', 12, 'ward', "The gatekeeper's ring. He didn't open the gate in time.")
z.quest('bs_bishops_letters', "The Bishop's Letters", 12, 'bs_prior_anselm',
        "Bishop Burhoff came to us two years ago, a good man, we thought. Then this spring he brought in new brothers who wore red cords. In a month they had the abbey, and we had the road.\n\nIf the Bishop is in league with someone, it'll be in his letters - he keeps a writing-desk in the cloister. Will you [find the letters]?",
        'find the letters',
        "Prior Anselm, driven out of Vetusta Abbey, thinks Bishop Burhoff's letters will show who he serves.",
        [
            hunt((520, 1420), "Fight through the dark brothers in the cloister " + where((520, 1420), 'bs_prior_anselm'), 'dark brother', 5),
            search(Z, P(600, 1450), "Search the Bishop's writing-desk", "a writing-desk in the cloister", CRATE,
                   "Letters, in the fine crowned hand you know from Mithra's Tomb: 'Burhoff - Malgwyn is lost. Gather what Badon gives you. When the stones of Salisbury wake, march. M.'",
                   give="the Bishop's letters"),
            end_talk('bs_prior_anselm', "Bring the letters to Prior Anselm",
                     "M. Morgana. In our abbey. Under our bell.\n\n'When the stones of Salisbury wake'... I don't know what that means, and I don't want to. We must take Vetusta back before it does.", 'default'),
        ],
        {'default': {'text': "From the Abbey Faithful.", 'choice': [v3, v4, v5]}})

v6 = z.item("Bell-Rope Bracer", 'bracer', 14, 'might', "Cut from the old bell-rope when it was replaced.")
v7 = z.item("Tower-Stair Mantle", 'cloak', 14, 'faith', "Grey wool, dusty from the bell-tower stair.")
v8 = z.item("Vetusta Bell Charm", 'gem', 14, 'charm', "A tiny bronze bell. It rings true.")
z.quest('bs_bells_of_vetusta', 'The Bells of Vetusta', 14, 'bs_brother_teilo',
        "The Prior says the bell won't ring because they've bound it. If the bell rings, every true brother hiding in these hills will know the abbey's ours again - and the Bishop's men will know too.\n\nI'll ring it. Will you [guard the tower] while I do? It'll take a while to cut the cords.",
        'guard the tower',
        "Brother Teilo means to ring Vetusta's bound bell and call the true brothers home.",
        [
            hunt((549, 1500), "Clear the dark brothers-in-arms from the abbey yard " + where((549, 1500), 'bs_brother_teilo'), 'dark brother-in-arms', 3),
            defend(Z, (555, 1495), "Keep Brother Teilo alive while he cuts the bell free",
                   "The bell swings, and rings - once, twice, and then a long peal across the mountains.",
                   'Brother Teilo', 12964, 14, "Teilo throws off his cloak and starts sawing at the red cords. 'Hold the stair! They're coming!'",
                   [(ACOLYTE, 'dark brother', [12, 13]), (INITIATE, 'crimson initiate', [13, 14])], 'Keep Brother Teilo alive', model=M, duration=90),
            end_talk('bs_prior_anselm', "Tell Prior Anselm", "I heard it. All of Humberton heard it. Brothers are coming down out of the hills already.\n\nThe Bishop heard it too.", 'default'),
        ],
        {'default': {'text': "From the Abbey Faithful.", 'choice': [v6, v7, v8]}},
        requires='bs_bishops_letters', group=True)

v9 = z.item("Burhoff's Crozier-Ring", 'ring', 17, 'faith', "Cut from the head of the Bishop's crozier. The red key's been filed off.")
v10 = z.item("Bell-Ringer of Vetusta's Mantle", 'cloak', 17, 'ward', "White wool. Prior Anselm stitched the abbey's bell on it himself.")
v11 = z.item("Morgana's Seal, Broken", 'neck', 17, 'mind', "Her seal, snapped in two and set on a chain. Wear it as a promise.")
v12 = z.item("Abbey Smith's Gauntlet-Ring", 'ring', 17, 'might', "Vetusta's smith made it the day the abbey was retaken.")
z.quest('bs_dark_bishop', 'The Dark Bishop', 17, 'bs_prior_anselm',
        "The bell's rung and the brothers are home - but Burhoff still holds the crypt below the abbey's south wall, with his best.\n\nThis ends it. Will you [face the Bishop]? Bring as many friends as will come.",
        'face the Bishop',
        "Dark Bishop Burhoff still holds the crypt below Vetusta Abbey.",
        [
            reach(Z, P(545, 1560), "Go down to the crypt below the abbey's south wall " + where((545, 1560), 'bs_prior_anselm'),
                  "The crypt stairs are wet, and you can hear chanting below.", r=25),
            hunt((541, 1598), "Defeat Dark Bishop Burhoff", 'Dark Bishop Burhoff', 1,
                 text="Burhoff falls against the altar. 'She'll come,' he says. 'Through the gate in the lake. And the giants will dance for her on Salisbury Plain.'"),
            search(Z, P(538, 1600), "Search the Bishop's altar", "an altar with a red key", CRATE,
                   "A map of Salisbury Plain, with a ring of stones drawn on it in red. And written beside it: 'The Giants' Dance. Merlin built it. Merlin's stones will open for me.'",
                   give="the Bishop's map"),
            end_talk('bs_prior_anselm', "Bring the map to Prior Anselm",
                     "The Giants' Dance - the stones at Salisbury, that Merlin raised over the dead of Britain. She means to use them.\n\nVetusta is ours again, and you gave it back to us. Carry this map to the Watch on Salisbury Plain. And come home when you can; the bell will ring for you.", 'default'),
        ],
        {'default': {'text': "From the Abbey Faithful, with the bell's blessing.", 'items': [v10], 'choice': [v9, v11, v12]}},
        requires='bs_bells_of_vetusta', group=True)
