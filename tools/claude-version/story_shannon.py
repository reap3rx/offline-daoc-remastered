"""Shannon Estuary's story quests (claude 2026-11-23, the zone brief in Zone Reviews) - see story_gen.py. Places: zone metres
[x, y].

Moved out of story_hib.py with the zone's rebuild, like Lough Derg, Connacht, Silvermine and Bri Leith:
    python tools/claude-version/story_gen.py story_shannon

Six arcs and a first walk, 27 quests, one thread: the well is rising. In the old tale Sinann went to Connla's Well for the
wisdom of the nine hazels, the well rose and drowned her, and its waters became the Shannon. She never forgave it. Now the
sea comes up the river in calm weather, the ants are flooded out of their hills, the drowned walk the strand - and Kaen
Kedger, chief of the eriu, has his druids at the standing stones round the well calling her up, because a drowned river
spirit has promised him the well's wisdom and every eriu clan with it. She doesn't want to give anyone wisdom. She wants to
rise until the estuary is hers. Only Sinann's own blood can sing her back to sleep - and Brehon Aodh's daughter Orla, the
treaty hostage Kedger broke the treaty to keep, is of that line (owner 2026-11-23: "some sort of major happening near
Connla's Well ... something Fae/Druid related, maybe summoning a powerful water spirit ... there are standing stones
surrounding the lake"). Two old quests are folded in: The False Light (false_light) and The Eriu Hostage (eriu_hostage).
The Sentinels of Ceannai's arcs: Daigean Bridge, The Ant Country, The Eriu Hostage. Lucht an Tobair's: The Drowned Strand,
The Sheerie Ring and the Merrow, Connla's Well.
"""
import math
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE = 1882, 1876, 1347
M, F, OLD = 337, 365, 362
Z = 202
ZONES = []

z = Zone(Z, 'Shannon Estuary', 3, 'hib_shannon')
ZONES.append(z)

AT = {}


def at(npc, x, y):
    AT[npc] = (x, y)
    return [x, y]


def where(to, frm):
    """'about 240 m north-west of Brehon Aodh' (y grows southward)."""
    fx, fy = AT[frm][0], AT[frm][1]
    dx, dy = to[0] - fx, to[1] - fy
    d = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(-dy, dx)) % 360
    names = ['east', 'north-east', 'north', 'north-west', 'west', 'south-west', 'south', 'south-east']
    dirn = names[int(((ang + 22.5) % 360) // 45)]
    dist = ('%d m' % (round(d / 10) * 10)) if d < 950 else ('%.1f km' % (d / 1000))
    return 'about %s %s of %s' % (dist, dirn, NAMES[frm])


NAMES = {}


def person(id, name, xy, kind, level, **kw):
    NAMES[id] = name
    z.npc(id, name, at(id, *xy), kind, level, **kw)


def hunt(xy, goal, target, count, text=None, give=None):
    """A kill step on the zone's own monsters (they scale to you)."""
    s = {'type': 'kill', 'zone': Z, 'at': list(xy), 'radius': 40, 'goal': goal, 'target': target, 'count': count}
    if text:
        s['text'] = text
    if give:
        s['give'] = {'name': give}
    return s


def wake(ending, chain):
    ending['wake_event'] = chain
    return ending


# ------------------------------------------------------------------ people
# Connla (the Wild start)
person('harbourmaster', 'Harbourmaster Cian', (226, 664), 'm', 18, guild='Connla',
       idle="Ships come in, ships go out. Some don't come back. That's the sea. Lately it's the river too, and that's not right.")
person('maeve_widow', 'Maeve', (240, 690), 'f', 9, idle="Three years. I still set his place at table.")
person('sh_ciar', 'Ciar the Fili', (252, 668), 'f', 30, guild='Lucht an Tobair',
       idle="The river tastes of salt as far up as the bridge. Rivers don't do that. Not unless something is pushing the sea up them.")
z.npc('niall_ghost', 'the ghost of Captain Niall', at('niall_ghost', 192, 574), 'm', 12, model=M, during=['false_light/niall'])
NAMES['niall_ghost'] = 'the ghost of Captain Niall'
# Ceannai (the Sentinels' town on the south road)
person('brehon_aodh', 'Brehon Aodh', (980, 1580), 'm', 30, guild='Ceannai',
       idle="The law is the law. Even when it's ours that broke it.")
person('iasc', 'Iasc the Ferryman', (970, 1572), 'm', 18, idle="Ferry's free, for now. The eriu haven't come down the river yet.")
person('sh_fionn', 'Captain Fionn', (992, 1575), 'm', 34, guild='Sentinels of Ceannai',
       idle="The Sentinels keep the south road and the treaty. The treaty's broken. So now we just keep the road.")
z.npc('orla', 'Orla', at('orla', 1006, 1132), 'f', 20, during=['eriu_hostage/orla', 'eriu_hostage/s5', 'eriu_hostage/s6', 'sh_orla_at_the_well/s1'])
NAMES['orla'] = 'Orla'
# out in the estuary - givers met as you explore
person('sh_tadhg', 'Old Tadhg', (640, 535), 'm', 12, guild="Fishers' Post",
       idle="I've fished under Daigean Bridge sixty years. First year I've ever had to pay to do it.")
person('sh_bebhinn', 'Bebhinn the Seanchai', (585, 762), 'f', 22, guild='Hy Brasil camp',
       idle="Everything that happens on this river has happened before, in a story. The trick is knowing which story.")
person('sh_murchadh', 'Bosun Murchadh', (228, 990), 'm', 20, guild="Sailors' Pier",
       idle="The merrow used to trade with us off the pier. Fish for knives. They've stopped coming up.")
person('sh_ruairi', 'Sentinel-Scout Ruairi', (800, 880), 'm', 24, guild='Sentinels of Ceannai',
       idle="The ants don't wander. Ants never wander. Something drove them out.")
person('sh_ceallach', 'Fili Ceallach', (1560, 640), 'm', 32, model=OLD, guild='Lucht an Tobair',
       idle="Nine hazels round the well, and every one of them dropping nuts out of season. The well is awake.")

# ======================================================================== a first walk (the Wild start in Connla)
z.quest('sh_welcome_to_connla', 'The Salt in the Barrels', 2, 'harbourmaster',
        "New off the boat? Welcome to Connla - best port in Hibernia, whatever they tell you in Mag Mell.\n\nDo me a kindness. The fishers' post up at Daigean Bridge sent down three barrels of river eels, and every one of them's pickled in salt water. River water. Will you [ask Tadhg] what's going on up there? Follow the strand north, then the river east. He's the old one with the nets.",
        'ask Tadhg',
        "Harbourmaster Cian in Connla wants to know why the river eels from Daigean Bridge came down tasting of the sea.",
        [
            end_talk('sh_tadhg', "Ask Old Tadhg at the fishers' post by Daigean Bridge, " + where((640, 535), 'harbourmaster'),
                     "Salt? Aye. Sixty years I've fished here and the river's been sweet as milk. This month it's salt as far up as the bridge, and the eels are coming up dead.\n\nAnd that's not the worst of it. Runaway lads from Connla have put a chain across the bridge and charge a toll to cross. Have a look round. There's work here for anyone with a sword.", 'default'),
        ],
        {'default': {'text': "Here - Cian said you'd want paying.", 'choice': []}})

# ======================================================================== Daigean Bridge (5 to 11) - Sentinels
a1 = z.item("Toll-Chain Bracer", 'bracer', 5, 'might', "A link of the chain the runaways put across the bridge, beaten into a bracer.")
a2 = z.item("Fisher's Knot Ring", 'ring', 5, 'finesse', "Tadhg ties a fisher's knot in copper wire for anyone who helps him.")
z.quest('sh_toll', 'The Toll at Daigean Bridge', 5, 'sh_tadhg',
        "Those lads up the bridge road - Connla's runaways, villainous youths and rowdies - want a copper a crossing, and two for a fish. From ME.\n\nWill you [break the toll]? Knock a few of them about. Not too hard. Some of them are somebody's sons.",
        'break the toll',
        "Connla's runaways have put a toll on Daigean Bridge.",
        [
            hunt([590, 470], "Drive off 6 villainous youths at the toll chain on the bridge road, " + where((590, 470), 'sh_tadhg'), 'villainous youth', 6,
                 text="They scatter, shouting. One drops a purse heavy with tolls - and something else, a little sack that smells of nuts."),
            end_talk('sh_tadhg', "Return to Old Tadhg", "Ha! Did you see them run?\n\nWhat's in the sack? ...Hazelnuts. In this season? There's no hazel near the bridge bears this early. These come from a long way east. From the well, I'd say. Somebody's paying those lads in more than tolls.", 'default'),
        ],
        {'default': {'text': "From the fishers' post.", 'choice': [a1, a2]}})

a3 = z.item("Runaway's Pledge Charm", 'gem', 7, 'charm', "A lead token the runaways swear on. Breandan's sons all wear one.")
a4 = z.item("Rowdy's Belt", 'belt', 7, 'might', "Studded, loud, and slightly too big. Like the rowdy who wore it.")
z.quest('sh_runaway_sons', "Somebody's Sons", 7, 'harbourmaster',
        "Tadhg sent word. Runaways at the bridge - and I'll wager half of them are Connla boys. My sister's boy Colm ran off at midsummer.\n\nWill you [find Colm]? He's sixteen, red hair, mouth like a gull. Knock the rowdies round him down and tell him his mother's frantic.",
        'find Colm',
        "Harbourmaster Cian's nephew Colm ran off to join the runaways at Daigean Bridge.",
        [
            hunt([545, 430], "Fight through 5 rowdies on the road to the bridge, " + where((545, 430), 'harbourmaster'), 'rowdy', 5),
            search(Z, [482, 387], "Search the runaways' den (click the glinting spot)", "Colm's satchel", CRATE,
                   "A satchel with a name stitched inside it - COLM - and a scrap of paper: 'Breandan says the eriu pay a silver a sack for anyone who'll carry nuts north. Easy money. Back by harvest. Don't tell Mam.'",
                   give="Colm's note"),
            end_talk('harbourmaster', "Take Colm's note back to Harbourmaster Cian", "Carrying nuts for the eriu? For a silver a sack? The little fool.\n\nBreandan. I know that name - he ran off from the docks five years back. If he's taking eriu silver, the Sentinels need to hear of it. Thank you for this.", 'default'),
        ],
        {'default': {'text': "From Connla.", 'choice': [a3, a4]}},
        requires='sh_toll')

a5 = z.item('Hazel-Sack Ring', 'ring', 9, 'mind', "Woven from the drawstring of a smuggler's sack. It smells faintly of the well.")
a6 = z.item("Sentinel's Courier Bracer", 'bracer', 9, 'ward', "Plain leather, Ceannai-stamped. Couriers on the south road wear them.")
z.quest('sh_hazel_smuggler', 'Nuts for the North', 9, 'sh_tadhg',
        "Colm came home - his uncle dragged him by the ear - but the nuts keep coming over the bridge. Somebody at the toll camp keeps the tally.\n\nWill you [find the tally]? The Sentinels at Ceannai would give a lot to know who's buying hazelnuts from the well.",
        'find the tally',
        "Somebody is smuggling hazelnuts from Connla's Well north over Daigean Bridge.",
        [
            hunt([590, 470], "Defeat the toll-keeper at the toll chain on the bridge road, " + where((590, 470), 'sh_tadhg'), 'toll-keeper', 1),
            search(Z, [595, 475], "Search the toll camp (click the glinting spot)", "the toll camp's tally", CRATE,
                   "A tally-stick and a strip of birch-bark in eriu ogham: 'Kedger's nuts. North to the buyers, silver back south. The well-callers want the price high - the more nuts are taken, the louder the well cries.'",
                   give="the eriu tally"),
            end_talk('sh_fionn', "Take the tally to Captain Fionn at Ceannai, far to the south", "Kedger. Kaen Kedger, chief of the eriu - the same eriu we have a treaty with.\n\n'The louder the well cries.' I don't like that. I'll send to the filid. Lucht an Tobair keep the well; they'll know what it means. You've done the Sentinels a service.", 'default'),
        ],
        {'default': {'text': "From the Sentinels of Ceannai.", 'choice': [a5, a6]}},
        requires='sh_runaway_sons')

a7 = z.item("Breandan's Chain", 'neck', 11, 'might', "The toll-master's chain of office. He made it himself, from the toll chain.")
a8 = z.item("Bridge-Warden's Ring", 'ring', 11, 'ward', "Old Tadhg's father kept the bridge. This was his ring.")
a9 = z.item("Turncoat's Sash", 'belt', 11, 'finesse', "Breandan's sash: Connla green on one side, eriu brown on the other.")
z.quest('sh_toll_master', 'Breandan', 11, 'sh_tadhg',
        "Breandan himself's come down to the bridge. He calls himself the Toll-Master now, and he's got the rowdies building a gate.\n\nWill you [deal with Breandan]? Then we'll see what's to be done with the lads.",
        'deal with Breandan',
        "Breandan, Connla's runaway leader and the eriu's smuggler, holds Daigean Bridge.",
        [
            hunt([545, 430], "Kill 4 rowdies at the new gate, " + where((545, 430), 'sh_tadhg'), 'rowdy', 4),
            boss(Z, [590, 470], "Defeat Breandan the Toll-Master", "Breandan goes down on the bridge planks. 'They said it was only nuts,' he says. 'Only nuts! What harm's in nuts?'",
                 'Breandan the Toll-Master', 60165444, 12, "A big young man with a chain round his neck steps out of the toll hut. 'Two coppers to cross. Three for you.'",
                 objective='Defeat Breandan the Toll-Master', hp=2.2, adds=[(60165444, 'rowdy', [9, 10])], every=25, count=2),
            choice('sh_tadhg', "Return to Old Tadhg",
                   "So that's Breandan beaten. The lads are sitting on the bank like wet cats.\n\nThe Sentinels want them all [sent to Ceannai] to work off the tolls on the south road. Or we [send them home] to their mothers in Connla and say no more about it. They're boys. Mostly.",
                   [('sent to Ceannai', "Ceannai it is. A year on the south road never killed anyone. Well. Not often.", 'ending:ceannai'),
                    ('send them home', "Home, then. Colm's mother will do worse to them than the Sentinels ever could.", 'ending:home')]),
        ],
        {'ceannai': {'text': "From the fishers' post, and the bridge that's free again.", 'choice': [a7, a8, a9]},
         'home': {'text': "From the fishers' post, and the bridge that's free again.", 'choice': [a7, a8, a9]}},
        requires='sh_hazel_smuggler')

# ======================================================================== The Drowned Strand (8 to 14) - Lucht an Tobair
b1 = z.item('Salt-Crust Charm', 'gem', 8, 'faith', "River water, boiled down. What's left is sea salt.")
b2 = z.item("Fili's Reed Bracer", 'bracer', 8, 'mind', "Marsh reed woven tight, the way the filid do it.")
z.quest('sh_salt_river', 'Salt in the River', 8, 'sh_ciar',
        "Tadhg's eels died of salt. I've tasted the river from Connla to the bridge, and it's the sea, all the way up. In calm weather!\n\nLucht an Tobair keep Connla's Well, where the river is born. If the sea is coming up the river, something at the source is pulling it. Will you [walk the strand] with me - well, for me - and see what the tide has brought ashore?",
        'walk the strand',
        "Ciar the Fili wants to know why the sea is running up the river in calm weather.",
        [
            hunt([230, 400], "Break 5 sandmen on the strand, " + where((230, 400), 'sh_ciar'), 'sandman', 5,
                 text="The sandmen fall apart into wet sand - salt, through and through. They were made from the seabed."),
            search(Z, [190, 575], "Search the wreck sands (click the glinting spot)", "a sailor's bell", CRATE,
                   "A ship's bell, green with weed, half-buried. Engraved on it: MORNING STAR. When the wind blows across it, it tolls - very faintly - by itself.",
                   give="the Morning Star's bell"),
            end_talk('sh_ciar', "Bring the bell to Ciar the Fili in Connla", "The Morning Star. Maeve's husband's ship - it went down three years ago in calm weather. Calm weather, and a tide that came out of nowhere.\n\nThree years. This has been going on for three years and we didn't see it. Talk to Maeve. She'll know more than she's said.", 'default'),
        ],
        {'default': {'text': "From Lucht an Tobair.", 'choice': [b1, b2]}})

it_light = z.item('False-Light Lantern Charm', 'gem', 10, 'mind', "A little glass ball with a sheerie's light trapped in it. It lies about where it is.")
it_star = z.item('Morning Star Ring', 'ring', 10, 'might', "Carved from the figurehead of a wrecked ship.")
it_drift = z.item('Driftwood Bracer', 'bracer', 10, 'ward', "Silver-grey wood that once walked the shore at night.")
it_widow = z.item("Widow's Shawl", 'cloak', 10, 'faith', "Black wool. Maeve wore it for three years.")
z.quest('false_light', 'The False Light', 10, 'maeve_widow',
        "Three years ago my husband's ship, the Morning Star, went down off the beach in calm weather. Calm! Now the driftwood from her walks the shore at night - it's haunted, the children say.\n\nI'm not a fool. But I'd like to know. Will you [find out] what really happened to the Morning Star?",
        'find out',
        "Maeve's husband's ship sank three years ago in calm weather. Its driftwood now walks the shore at night.",
        [
            hunt([190, 575], "Lay the haunted driftwood to rest on the wreck sands, " + where((190, 575), 'maeve_widow'), 'haunted driftwood', 4,
                 text="On the last piece, carved deep, the ship's name: MORNING STAR. And scratched below it, fresh: 'LIGHTS. FALSE LIGHTS. AND THE WATER CAME UP.'"),
            talk('harbourmaster', 'Ask the harbourmaster about the wreck',
                 "False lights? ...Aye, the crew that washed up said they followed a light into the shallows - thought it was the harbour lamp. And then the sea came up under them like a hand. The moss sheeries on the south shore lead sailors astray, for sport. Captain Niall's body was never found. The [wreck] is still out on the northern sands.", kw='wreck'),
            search(Z, [189, 571], 'Search the wreck on the northern sands', "the Morning Star's figurehead", CRATE,
                   "The figurehead, half-buried. A woman with a star on her brow. Maeve's face - he had it carved like her. Behind it, something pale and wet is standing very still."),
            kill(Z, [324, 1109], 'Hunt down the moss sheeries at the sheerie ring, ' + where((324, 1109), 'maeve_widow'), 'moss sheerie', 30002, [8, 9], 5,
                 text="Their lights go out one by one. One is brighter than the rest, bobbing away to the south."),
            boss(Z, [330, 1120], 'Put out the false light', "The false light gutters and goes out. On the northern sands, far behind you, something sighs.",
                 'the False Light', 30002, 12, "A sheerie brighter than a harbour lamp rises out of the moss. 'Follow me, sailor. Follow me home. The water's rising - you'll want to be home.'",
                 objective='Put out the False Light', hp=2.2, adds=[(30002, 'moss sheerie', [8, 9])], every=30, count=1),
            L('niall', talk('niall_ghost', "Go back to the wreck", "You put out the light. Thank you. I've been standing here three years waiting for someone to.\n\nIt wasn't only the light, you know. The sea came up under us in a dead calm, as if something under the river had breathed in. Tell Maeve - tell her [I'm sorry]. Tell her what she likes.", kw="I'm sorry")),
            choice('maeve_widow', 'Tell Maeve what you found',
                   "He's there? On the sand? Niall?\n\nWhat does he want? Did he say?\n\n(He asked you to tell her one of two things. That she should [let him go] - put away the shawl, take down his place, and marry again. Or that she should [wait for him] at the wreck on the long nights, and he'll come.)",
                   [('let him go', "Let him go. ...He would say that. He always wanted me to be happy more than he wanted me. I'll take the shawl off tomorrow. Tonight I'll go and say goodbye.", 'ending:go'),
                    ('wait for him', "On the long nights. At the wreck. ...Then I'll wait. I'm good at waiting. I've had practice.", 'ending:wait')]),
        ],
        {'go': {'text': "Take this. I won't need it now.", 'items': [it_widow], 'choice': [it_star, it_drift]},
         'wait': {'text': "Take this, from the ship.", 'tragic': True, 'items': [it_light], 'choice': [it_star, it_drift]}},
        topics={'harbourmaster': "Cian, on the quay. He's been harbourmaster thirty years. He drinks."},
        requires='sh_salt_river')

b3 = z.item("Drowned Sailor's Earring", 'gem', 12, 'charm', "A gold earring, the kind sailors wear to pay for their own burial.")
b4 = z.item('Night-Watch Bracer', 'bracer', 12, 'might', "A watchman's bracer from Connla's docks, salt-stained.")
b5 = z.item('Tide-Mark Ring', 'ring', 12, 'faith', "A ring with a tide-line etched round it. The line is higher than it should be.")
z.quest('sh_drowned_watch', 'The Drowned Watch', 12, 'sh_ciar',
        "Niall isn't the only one walking. Every night now, more of them come up out of the shallows on the strand - drowned sailors, all the river's dead for a hundred years. They don't come to haunt. They come up looking inland, like men running from a flood.\n\nWill you [keep the watch] on the strand tonight? Lay them down. And find out what they're running from.",
        'keep the watch',
        "Drowned sailors walk out of the shallows on the strand at night, as if running from a flood.",
        [
            hunt([150, 470], "Lay 6 drowned sailors to rest on the strand at night, " + where((150, 470), 'sh_ciar'), 'drowned sailor', 6,
                 text="The last one grips your arm before it falls. 'It's rising,' it says, in a voice full of water. 'She's rising. Get to high ground.'"),
            reach(Z, [300, 640], "Climb the dune above Connla and look east up the river", "Moonlight on the river - and far off to the east, where Connla's Well should be, a glow on the water like a drowned lantern.", r=25),
            end_talk('sh_ciar', "Return to Ciar the Fili", "'She's rising.' The drowned said she.\n\nThere's only one she the river has ever had. Sinann. Gods. The old tale - she went to the well for its wisdom, and it drowned her, and she became the river. If the dead are running from her, she's waking.", 'default'),
        ],
        {'default': {'text': "From Lucht an Tobair.", 'choice': [b3, b4, b5]}},
        requires='false_light')

b6 = z.item('Morning Star Bell-Clapper', 'neck', 14, 'faith', "The clapper of the Morning Star's bell, on a cord. It rang for the drowned.")
b7 = z.item("Bell-Ringer's Cloak", 'cloak', 14, 'ward', "Grey and heavy, for standing on a cold quay all night.")
b8 = z.item('Ebb-Tide Belt', 'belt', 14, 'finesse', "Sealskin, from the sailors' pier.")
z.quest('sh_tide_bell', 'The Tide-Bell', 14, 'sh_ciar',
        "The old filid hung a bell on the quay to ring the tide back - and the Morning Star's bell was cast from the same bronze. If I can hang it on the quay and ring the old peal, the sea may fall back down the river where it belongs. For a while.\n\nBut the drowned will come for it. They want to go home, and the bell sends them back to sleep. Will you [guard the bell]?",
        'guard the bell',
        "Ciar the Fili will ring the Morning Star's bell on Connla's quay to send the tide back down the river.",
        [
            defend(Z, [165, 690], "Guard Ciar the Fili on the quay while she rings the bell", "The peal ends. The river shivers - and slowly, slowly, the water along the quay goes down a hand's breadth.",
                   'Ciar the Fili', 60163820, 14, "Ciar hangs the bell from the old post and begins the peal. Out of the shallows come the drowned, reaching for it.",
                   [(60160165, 'drowned sailor', [12, 13])], 'Keep Ciar the Fili safe', model=F, duration=90, every=20, count=2),
            end_talk('sh_ciar', "Talk to Ciar the Fili", "It's down. A hand. Only a hand - but it's down.\n\nThe bell only buys time. Whatever is pushing the sea up the river is at the well. The Sentinels say the eriu have druids at the standing stones there. I'm going to need you again, I think. Not yet. When you're stronger.", 'default'),
        ],
        {'default': {'text': "From Lucht an Tobair, and the quay.", 'choice': [b6, b7, b8]}},
        requires='sh_drowned_watch')

# ======================================================================== The Ant Country (15 to 21) - Sentinels
c1 = z.item('Ant-Chitin Bracer', 'bracer', 15, 'ward', "Shaped from a giant ant's foreleg. Harder than iron and much lighter.")
c2 = z.item("Scout's Compass Charm", 'gem', 15, 'mind', "A Sentinel scout's lodestone, in a twist of wire.")
z.quest('sh_flooded_hills', 'Flooded Out', 15, 'sh_ruairi',
        "The giant ants are all over the south road. Ants don't wander - they keep to their hills. Something drove them out.\n\nWill you [look at the hills]? The nearest is north-east of here. Kill what you must and look inside.",
        'look at the hills',
        "Sentinel-Scout Ruairi wants to know what drove the giant ants out of their hills.",
        [
            hunt([990, 750], "Kill 5 giant ants round the ant hill, " + where((990, 750), 'sh_ruairi'), 'giant ant', 5),
            search(Z, [992, 752], "Look into the ant hill (click the glinting spot)", "a flooded tunnel", CRATE,
                   "The tunnel is full of water - salt water, a long way from the sea. Drowned ant larvae float in it. Something welled up from underneath, through the rock."),
            end_talk('sh_ruairi', "Return to Sentinel-Scout Ruairi", "Salt water. Under an ant hill. In the middle of the country.\n\nThen the ants aren't the trouble - they're running from it, same as us. But they're running onto the south road, and the road's ours to keep. We'll need to thin them.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [c1, c2]}})

c3 = z.item('Mandible Ring', 'ring', 17, 'might', "An ant soldier's mandible tip, set in bronze. Still sharp.")
c4 = z.item("Road-Keeper's Belt", 'belt', 17, 'ward', "The belt of a Sentinel who keeps the south road clear.")
z.quest('sh_ant_soldiers', 'The Soldiers', 17, 'sh_ruairi',
        "The ants have soldiers now - big ones, guarding the hills like Sentinels on a gate. They're marching. Workers carry the larvae, soldiers walk alongside.\n\nWill you [break the march]? If the soldiers fall, the workers scatter, and the road's clear for a while.",
        'break the march',
        "Ant soldiers are guarding the ants' march out of their flooded hills.",
        [
            hunt([900, 960], "Kill 3 ant soldiers by the great hill, " + where((900, 960), 'sh_ruairi'), 'ant soldier', 3),
            hunt([800, 1100], "Scatter 6 ant workers in the ant country", 'ant worker', 6,
                 text="The workers drop what they carry and run - every one of them north-west, away from the east. Away from the well."),
            end_talk('sh_ruairi', "Return to Sentinel-Scout Ruairi", "North-west, every one of them. Away from the well.\n\nThe filid say the well's rising. The ants knew it before any of us. Good work.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [c3, c4]}},
        requires='sh_flooded_hills')

c5 = z.item("Hill-Scout's Torc", 'neck', 19, 'finesse', "Bronze, light and plain. Scouts don't like anything that clinks.")
c6 = z.item('Lost-Patrol Ring', 'ring', 19, 'faith', "Found on the floor of the great hill. It belonged to a Sentinel.")
c7 = z.item("Tunnel-Crawler's Bracer", 'bracer', 19, 'ward', "Scuffed to the bone from crawling.")
z.quest('sh_hill_scouts', 'The Lost Patrol', 19, 'sh_ruairi',
        "Three of my scouts went into the great hill a week ago to see where the water comes from. They haven't come out.\n\nWill you [find my scouts]? The great hill is south-east of here, the biggest of them. Mind the soldiers.",
        'find my scouts',
        "Three Sentinel scouts went into the great ant hill and haven't come out.",
        [
            hunt([930, 990], "Fight through 4 giant ants at the great hill, " + where((930, 990), 'sh_ruairi'), 'giant ant', 4),
            search(Z, [935, 995], "Search the mouth of the great hill (click the glinting spot)", "a Sentinel's map", CRATE,
                   "A scout's map, scrawled in haste: the tunnels run east, under the ant country, all the way to Connla's Well. 'The water comes from the well. The Queen guards the way. Too many soldiers. Going back.' The last line is blotted.",
                   give="the scouts' map"),
            end_talk('sh_ruairi', "Bring the map to Sentinel-Scout Ruairi", "The tunnels run to the well. Of course they do.\n\nAnd the Old Queen guards them. She's been in that hill longer than Ceannai's been a town. If my scouts are anywhere, they're past her.", 'default'),
        ],
        {'default': {'text': "From the Sentinels.", 'choice': [c5, c6, c7]}},
        requires='sh_ant_soldiers')

c8 = z.item("Old Queen's Crown-Plate", 'neck', 21, 'might', "A plate of the Old Queen's head-carapace, hung on a chain.")
c9 = z.item('Royal Jelly Charm', 'gem', 21, 'charm', "Amber, with a drop of something golden inside.")
c10 = z.item('Hive-Heart Cloak', 'cloak', 21, 'ward', "Spun from ant silk. It doesn't tear.")
z.quest('sh_old_queen', 'The Old Queen', 21, 'sh_ruairi',
        "The Old Queen sits in the great hill, with her soldiers round her. While she's there nobody gets into the tunnels - not my scouts, not anyone.\n\nThis is GROUP work. Will you [face the Old Queen]?",
        'face the Old Queen',
        "The Old Queen of the giant ants holds the great hill, and the tunnels to the well beneath it.",
        [
            hunt([930, 990], "Defeat the Old Queen at the great hill, " + where((930, 990), 'sh_ruairi'), 'The Old Queen', 1,
                 text="The Old Queen goes down. Behind her, deep in the hill, three voices are shouting for help - and under them, very faint, the sound of water rising."),
            choice('sh_ruairi', "Return to Sentinel-Scout Ruairi",
                   "You found them! All three, half-drowned but alive. Thank the gods.\n\nNow - the hill. We can [seal the tunnels], and the ants will settle and the road will be quiet, but we'll have no way under to the well. Or we [keep them open], and post Sentinels at the mouth, and use them. A way under the well might be worth a lot, soon.",
                   [('seal the tunnels', "Sealed, then. Quiet road, quiet ants. I'll take that.", 'ending:sealed'),
                    ('keep them open', "Open, then. I'll put two scouts on the mouth. If the eriu want the well, they'll have to watch their feet.", 'ending:open')]),
        ],
        {'sealed': {'text': "From the Sentinels - and three scouts who owe you their lives.", 'choice': [c8, c9, c10]},
         'open': {'text': "From the Sentinels - and three scouts who owe you their lives.", 'choice': [c8, c9, c10]}},
        group=True, requires='sh_hill_scouts')

# ======================================================================== The Sheerie Ring and the Merrow (16 to 22) - Lucht an Tobair
d1 = z.item('Moss-Light Charm', 'gem', 16, 'mind', "A moss sheerie's light, given freely. It doesn't lie.")
d2 = z.item("Dancer's Anklet Bracer", 'bracer', 16, 'finesse', "Bells and moss. It jingles when you're about to be hit.")
z.quest('sh_failing_dance', 'The Failing Dance', 16, 'sh_bebhinn',
        "Every story about this river says the same thing: the sheeries dance in their ring in the south-west, and while they dance, the river sleeps. It's not a pretty story. It's a lullaby, and they've been singing it for a thousand years.\n\nThey've stopped. Will you [go and see why]? Carefully. A sheerie that isn't dancing is a sheerie that's angry.",
        'go and see why',
        "Bebhinn the Seanchai says the sheeries' dance keeps the river asleep, and the dance has stopped.",
        [
            reach(Z, [330, 1120], "Go to the sheerie ring, " + where((330, 1120), 'sh_bebhinn'), "A ring of moss and toadstools, trampled flat. The sheeries drift round it without dancing, their lights dim. Three of them are lying on the ground, wet through - as if they'd been rained on from below.", r=25),
            hunt([330, 1120], "Drive off 5 moss sheeries that set on you", 'moss sheerie', 5),
            end_talk('sh_bebhinn', "Return to Bebhinn the Seanchai", "Rained on from below. The well's water is coming up through the ground even there.\n\nThe ring-dancers - the old ones who lead the dance - have turned on the others. They say there's no point dancing if the river's waking anyway. We have to change their minds.", 'default'),
        ],
        {'default': {'text': "From the Hy Brasil camp.", 'choice': [d1, d2]}})

d3 = z.item("Ring-Dancer's Circlet", 'neck', 18, 'charm', "Toadstool and silver wire. You feel like dancing. You don't.")
d4 = z.item('Lullaby Ring', 'ring', 18, 'faith', "It hums the sheeries' tune if you hold it to your ear.")
z.quest('sh_ring_dancers', 'The Ring-Dancers', 18, 'sh_bebhinn',
        "The ring-dancers have stopped the dance on purpose. They want to be on the right side when the river wakes.\n\nWill you [stop the ring-dancers]? With them gone the young sheeries might dance again. They're simple things. They like a tune.",
        'stop the ring-dancers',
        "The ring-dancers have stopped the sheeries' lullaby to curry favour with the waking river.",
        [
            hunt([300, 1090], "Defeat 3 ring-dancers at the sheerie ring at night, " + where((300, 1090), 'sh_bebhinn'), 'ring-dancer', 3,
                 text="The last ring-dancer gutters out. 'She promised,' it whispers. 'She promised us the whole river to dance on.'"),
            end_talk('sh_bebhinn', "Return to Bebhinn the Seanchai", "She promised. Sinann, it has to be - the river has no other she.\n\nThe young ones are dancing again, a little. It won't hold her long. The merrow off the sailors' pier know the river's bottom better than anyone. They'll know what's coming up it.", 'default'),
        ],
        {'default': {'text': "From the Hy Brasil camp.", 'choice': [d3, d4]}},
        requires='sh_failing_dance')

d5 = z.item("Kirwyn's Trident Ring", 'ring', 20, 'might', "A merrow's ring, shaped like a trident. Kirwyn gave it freely, in the end.")
d6 = z.item('Merrow-Scale Bracer', 'bracer', 20, 'ward', "Green scales that shine like wet stone.")
d7 = z.item("Pier-Trader's Belt", 'belt', 20, 'finesse', "Sailors' leather, merrow-stitched. The old trade.")
z.quest('sh_kirwyn', 'Kirwyn of the Merrow', 20, 'sh_murchadh',
        "The merrow used to come up off the pier to trade - fish for knives, pearls for rope. Kirwyn, their chief, would sit on the end of the pier and drink our ale. They've stopped.\n\nNow they attack the boats. Will you [find Kirwyn]? Something has frightened them, or something has bought them.",
        'find Kirwyn',
        "Bosun Murchadh's old trading partners, the merrow, have turned on the boats.",
        [
            hunt([120, 865], "Fight off 4 merrow round Merrow Island, " + where((120, 865), 'sh_murchadh'), 'merrow', 4),
            hunt([256, 990], "Subdue Kirwyn of the merrow near the pier", 'Kirwyn', 1,
                 text="Kirwyn sinks to the sand, gasping. 'Enough! Enough. We didn't want to. She's coming up the river from the well, and she drowns everything that won't serve her. We serve, or we drown. We're merrow. We can drown.'"),
            end_talk('sh_murchadh', "Return to Bosun Murchadh", "Merrow afraid of drowning. I never thought I'd hear it.\n\nKirwyn told me more, after, over the ale. Go and ask the seanchai what he said - it was about the well, and the old story, and it went over my head.", 'default'),
        ],
        {'default': {'text': "From the sailors' pier.", 'choice': [d5, d6, d7]}},
        requires='sh_ring_dancers')

d8 = z.item('Hazel-Wood Torc', 'neck', 22, 'mind', "Hazel wood, from the nine trees round the well. It's said to make you wiser. It doesn't, but it's very nice.")
d9 = z.item("Seanchai's Story-Cloak", 'cloak', 22, 'charm', "Every patch on it is a story. Bebhinn knows them all.")
d10 = z.item('Deep-Water Charm', 'gem', 22, 'faith', "A pearl from the bottom of the well. It's very cold.")
z.quest('sh_under_the_well', 'What Lies Under the Well', 22, 'sh_bebhinn',
        "Kirwyn told Murchadh, and Murchadh told me: under Connla's Well there's a hollow, where the water first came up when it drowned Sinann. That's where she sleeps. And the eriu have druids at the stones round the well - well-callers - singing down into it.\n\nWill you [go to the well] and see? Take this sprig of sheerie moss. If she's awake, it'll go grey.",
        'go to the well',
        "The merrow say Sinann sleeps in a hollow under Connla's Well, and eriu druids are singing her awake.",
        [
            reach(Z, [1225, 690], "Go to the standing stones on the west side of Connla's Well, " + where((1225, 690), 'sh_bebhinn'), "Standing stones round a still, glassy pool, nine hazels hanging over it. The water is too high - it's lapping the stones' feet. The sheerie moss in your hand goes grey.", r=30),
            hunt([1225, 690], "Drive off 3 eriu well-callers at the western stones", 'eriu well-caller', 3,
                 text="As the last well-caller falls, the pool heaves - once - like something turning over in its sleep."),
            end_talk('sh_bebhinn', "Return to Bebhinn the Seanchai", "Grey. The moss went grey.\n\nShe's awake, then. Or nearly. Go to the filid at the well - Ceallach keeps the hermitage on the east shore. This is Lucht an Tobair's work now, and yours if you'll have it.", 'default'),
        ],
        {'default': {'text': "From the Hy Brasil camp, and every story I know.", 'choice': [d8, d9, d10]}},
        requires='sh_kirwyn')

# ======================================================================== The Eriu Hostage (20 to 27) - Sentinels
it_treaty = z.item('Treaty-Stick Charm', 'gem', 20, 'mind', "An ogham treaty-stick, mended with silver wire.")
it_eriu = z.item('Eriu Fishing-Torc', 'neck', 20, 'might', "Bronze, twisted like rope, the way the eriu make everything.")
it_brehon = z.item("Brehon's Ring", 'ring', 20, 'faith', "A judge's ring. Aodh gave you his spare.")
it_orla = z.item("Orla's Woven Belt", 'belt', 20, 'finesse', "Eriu weaving, taught to Orla in captivity. She's better at it than they are.")
z.quest('eriu_hostage', 'The Eriu Hostage', 20, 'brehon_aodh',
        "Five years ago this town made a treaty with the eriu upriver: our boats keep below the ford, theirs above. My daughter Orla went to them as surety - a hostage, by the old law. She was ten.\n\nLast month someone fished above the ford. Now the eriu say the treaty's broken, and the law says a broken treaty is paid for with the hostage's life. Will you [bring Orla home]?",
        'bring Orla home',
        "Brehon Aodh's daughter has been a hostage with the eriu for five years. Now someone has broken the treaty.",
        [
            talk('iasc', 'Ask Iasc the ferryman about the broken treaty',
                 "I know who fished above the ford. Me. The run was poor below and my children were hungry. I didn't think they'd notice one boat. I didn't think - about Orla. Gods forgive me.\n\nBut listen - the eriu came for me before I'd even pulled the net. As if they'd been waiting for someone to do it. Their hunting camp's up the [river].", kw='river'),
            kill(Z, [1010, 1140], "Fight through the eriu henters, " + where((1010, 1140), 'brehon_aodh'), 'eriu henter', 60160565, [19, 20], 5,
                 text="They fight hard but they don't hate you. 'The law,' one says as he falls. 'Your people broke the law. Kedger said they would.'"),
            search(Z, [1000, 1150], 'Search the eriu hunting camp', "a broken treaty-stick", CRATE,
                   "The ogham treaty-stick, snapped clean in two. It was the town's own copy. Beside it, a girl's footprints - free, unchained, pacing - and a sack of hazelnuts from the well."),
            L('orla', talk('orla', 'Find Orla', "Father sent you? Of course he did. He's very proper.\n\nThey've been good to me, you know. Five years. They taught me to weave and to fish and to sing their songs. And now they'll kill me, because the law says so - except it isn't the law. Kaen Kedger wanted the treaty broken. He wanted me. He keeps asking me to sing to the [well].", kw='well')),
            boss(Z, [1006, 1128], "Stand against the eriu chief of the hunting camp", "The eriu chief kneels. 'Then it's done. The law's been answered with blood. Take her - before Kedger hears.'",
                 'Chief Dorchadh of the Eriu', 60160566, 23, "An old eriu in a cloak of fish-scale. 'I'm sorry, girl. The law is the law - and Kedger is the chief of chiefs now.'",
                 objective='Defeat Chief Dorchadh', hp=2.4, adds=[(60160565, 'eriu henter', [19, 20])], every=25, count=2),
            choice('orla', 'Decide with Orla',
                   "He's beaten, but Kedger will send others. And the treaty's still broken.\n\nFather could [renew the treaty] - pay the eriu the old fine for the broken one. It would ruin him. Or we go home and let the eriu come for [war]. Either way - Kedger wants me for something at the well. I don't know what. I'm frightened of it.",
                   [('renew the treaty', "Then I'll tell him to pay. And I'll go back to them myself, after, to say goodbye properly. They were my family too.", 'next:treaty'),
                    ('war', "War, then. Gods. I'll tell him. He won't like it either way.", 'next:war')]),
            L('treaty', end_talk('brehon_aodh', 'Return to Brehon Aodh', "She's home. And the treaty is renewed - at a price that's cost me my house and two fields.\n\nIasc came to me and wept and offered his boat. I took it, and gave it back to him. The law is satisfied. I am not. Kedger wanted her for something. I want to know what.", 'treaty')),
            L('war', end_talk('brehon_aodh', 'Return to Brehon Aodh', "She's home. That's what matters.\n\nThe eriu have sent a war-arrow down the river. The town's arming. Orla stands at the window looking upriver, toward the well, and won't tell me what she's thinking. Here.", 'war')),
        ],
        {'treaty': {'text': "Take this, with the law's thanks.", 'items': [it_treaty], 'choice': [it_brehon, it_orla]},
         'war': {'text': "For bringing her back.", 'tragic': True, 'items': [it_eriu], 'choice': [it_brehon, it_orla]}},
        topics={'Iasc': "The ferryman, by the river. He hasn't met my eye in a month."})

e1 = z.item('War-Arrow Charm', 'gem', 22, 'might', "The head of the eriu war-arrow, snapped off and kept.")
e2 = z.item("Sentinel's Watch Bracer", 'bracer', 22, 'ward', "Ceannai-stamped. A Sentinel on watch wears one on each wrist.")
z.quest('sh_war_arrow', 'The War-Arrow', 22, 'sh_fionn',
        "Treaty or no treaty, Kedger has sent the war-arrow round the clans. Eriu waylayers on the south road - three carts gone this week.\n\nWill you [clear the south road]? And if you find a waylayer carrying orders, bring them to me.",
        'clear the south road',
        "Kaen Kedger has sent the war-arrow round the eriu clans, and waylayers hold the south road.",
        [
            hunt([840, 1330], "Kill 4 eriu waylayers on the south road, " + where((840, 1330), 'sh_fionn'), 'eriu waylayer', 4),
            search(Z, [845, 1335], "Search the waylayers' camp (click the glinting spot)", "Kedger's orders", CRATE,
                   "Birch-bark, eriu ogham: 'Hold the road. Let nothing north to Connla's Well. The well-callers need three more nights. When she rises, the river is ours, every clan is mine, and the Sentinels drown in their own town.'",
                   give="Kedger's orders"),
            end_talk('sh_fionn', "Bring the orders to Captain Fionn", "'When she rises.' The filid keep saying it too. She - the river. Sinann.\n\nKedger isn't fighting a war with us. He's waiting for a flood to fight it for him. Then we don't wait. Kedger has three captains in the woods. We start with them.", 'default'),
        ],
        {'default': {'text': "From the Sentinels of Ceannai.", 'choice': [e1, e2]}},
        requires='eriu_hostage')

e3 = z.item("Danderpaw's Claw Ring", 'ring', 24, 'might', "Danderpaw's claw, set in bronze.")
e4 = z.item("Nasco's Net-Weight Charm", 'gem', 24, 'mind', "A stone net-weight carved with Nasco's mark.")
e5 = z.item("Solas's Watch-Cloak", 'cloak', 24, 'finesse', "The cloak of the eriu who watched the south road. It's the colour of dusk.")
z.quest('sh_lieutenants', "Kedger's Captains", 24, 'sh_fionn',
        "Kedger's three captains: Danderpaw in his den by the eastern border, Nasco at his post in the west woods, Solas on the watch just north of town.\n\nWill you [break the captains]? Without them the clans can't hold the woods, and Kedger is alone in his war-camp.",
        'break the captains',
        "Kaen Kedger's three captains hold the eriu woods.",
        [
            hunt([912, 1509], "Defeat Solas at the south watch, " + where((912, 1509), 'sh_fionn'), 'Solas', 1),
            hunt([666, 1512], "Defeat Nasco at his post in the west woods, " + where((666, 1512), 'sh_fionn'), 'Nasco', 1),
            hunt([1282, 1539], "Defeat Danderpaw in his den by the eastern border, " + where((1282, 1539), 'sh_fionn'), 'Danderpaw', 1,
                 text="Danderpaw falls. 'Too late,' he laughs. 'Kedger has the well-callers. He doesn't need us any more. He doesn't need anyone.'"),
            end_talk('sh_fionn', "Return to Captain Fionn", "All three. Then Kedger's woods are open.\n\nHe's in his war-camp now, with his huscarls. The Sentinels can take it - not today, but soon, if Ceannai's resolve holds. Before that, I want eyes on that camp.", 'default'),
        ],
        {'default': {'text': "From the Sentinels of Ceannai.", 'choice': [e3, e4, e5]}},
        requires='sh_war_arrow')

e6 = z.item("Palisade-Scout's Ring", 'ring', 25, 'finesse', "A plain ring with a notch for every palisade post counted.")
e7 = z.item('Totem-Splinter Torc', 'neck', 25, 'mind', "A splinter of a clan totem, bound in bronze. It mutters.")
z.quest('sh_war_camp_scout', 'Eyes on the War-Camp', 25, 'sh_fionn',
        "Kedger's war-camp is in the woods north-east of here - a palisade, archers on platforms, and clan totems the kedgers chant at. Every totem standing makes the eriu stronger, the filid say.\n\nWill you [scout the war-camp]? Count the huscarls, and look at those totems.",
        'scout the war-camp',
        "Captain Fionn wants Kaen Kedger's war-camp scouted before the Sentinels move on it.",
        [
            reach(Z, [1180, 1130], "Scout the war-camp's gate, " + where((1180, 1130), 'sh_fionn'), "A palisade of sharpened logs, archers on the platforms, and beyond it clan totems carved with drowned faces. Huscarls at the gate. Too many.", r=30),
            hunt([1320, 1180], "Silence 3 eriu kedgers chanting at the totem ring", 'eriu kedger', 3,
                 text="The chanting falters. One of the totems has a woman's face carved on it, with water pouring from her mouth. Sinann."),
            end_talk('sh_fionn', "Report to Captain Fionn", "Totems to Sinann. He's raising her with his whole clan behind him.\n\nThen we take the camp. Every Sentinel, every friend of Ceannai's. Win the estuary's resolve - its battles and its people - and we'll storm it. And you'll be at the front.", 'default'),
        ],
        {'default': {'text': "From the Sentinels of Ceannai.", 'choice': [e6, e7]}},
        requires='sh_lieutenants')

e8 = z.item("Kedger's Fish-Scale Mantle", 'cloak', 27, 'ward', "Kaen Kedger's mantle of office: ten thousand fish scales, sewn one by one.")
e9 = z.item('Chief-of-Chiefs Torc', 'neck', 27, 'might', "Gold and river-pearl. The eriu clans would follow whoever wore it. Nobody will.")
e10 = z.item("Well-Caller's Staff Charm", 'gem', 27, 'mind', "The head of a well-caller's staff. It drips, always.")
e11 = z.item("Huscarl's Arm-Ring", 'bracer', 27, 'might', "Bronze, heavy, and stamped with a leaping salmon.")
z.quest('sh_kaen_kedger', 'Kaen Kedger', 27, 'sh_fionn',
        "This is it. Kaen Kedger, chief of the eriu, in his longhouse in the war-camp. Orla says he's been singing to the well every night through the totems.\n\nThis is GROUP work. Will you [face Kaen Kedger]?",
        'face Kaen Kedger',
        "Kaen Kedger, chief of the eriu, waits in his war-camp longhouse.",
        [
            hunt([1260, 1120], "Fight through 2 eriu huscarls in the war-camp, " + where((1260, 1120), 'sh_fionn'), 'eriu huscarl', 2),
            boss(Z, [1262, 1118], "Defeat Kaen Kedger in his longhouse", "Kaen Kedger falls among his totems. 'Fool,' he gasps. 'It doesn't matter now. She's awake. She doesn't need me any more. She never did.'",
                 'Kaen Kedger', 60160566, 28, "Kaen Kedger rises from a throne of driftwood, a fish-scale cloak on his shoulders. 'The river is ours. It was always ours. She promised.'",
                 objective='Defeat Kaen Kedger', hp=2.6, adds=[(60160565, 'eriu huscarl', [26, 27])], every=25, count=2),
            choice('sh_fionn', "Return to Captain Fionn",
                   "Kedger down. The clans are leaderless.\n\nThe brehon says we [make a new treaty] with whoever leads the clans next, and give them back the river above the ford. The Sentinels say we [push them back] across the border and keep the river for Ceannai. Aodh won't decide. He says you've earned it.",
                   [('make a new treaty', "A new treaty, then. Aodh will be glad. Orla will be gladder.", 'ending:treaty'),
                    ('push them back', "Back across the border. The Sentinels will hold the river. Let's hope we hold it better than the eriu did.", 'ending:push')]),
        ],
        {'treaty': {'text': "From the Sentinels, and from Ceannai.", 'items': [e8], 'choice': [e9, e10, e11]},
         'push': {'text': "From the Sentinels, and from Ceannai.", 'items': [e8], 'choice': [e9, e10, e11]}},
        group=True, requires='sh_war_camp_scout')

# ======================================================================== Connla's Well (24 to 30) - Lucht an Tobair
f1 = z.item("Hazel-Gatherer's Ring", 'ring', 24, 'mind', "A ring of plaited hazel twig. It never dries out.")
f2 = z.item('Nine-Hazel Charm', 'gem', 24, 'faith', "Nine hazelnuts on a cord. They rattle when the well stirs.")
z.quest('sh_hazel_thieves', 'The Hazel Thieves', 24, 'sh_ceallach',
        "The nine hazels are dropping their nuts out of season, and the eriu fisceres gather them by the sackful and sell them north. Every nut taken from the well is a little of its wisdom gone - and the more is taken, the angrier the well grows.\n\nWill you [stop the thieves]? Then the hazel sprites may calm.",
        'stop the thieves',
        "Eriu fisceres are stripping the hazels round Connla's Well.",
        [
            hunt([1215, 410], "Drive off 6 eriu fisceres at their nets north of the well, " + where((1215, 410), 'sh_ceallach'), 'eriu fiscere', 6),
            hunt([1530, 820], "Calm 4 hazel sprites in the hazel grove (they won't calm any other way)", 'hazel sprite', 4,
                 text="The sprites scatter like leaves. Under the hazels, the ground is soaked - well-water, welling up through the roots."),
            end_talk('sh_ceallach', "Return to Fili Ceallach", "The roots are drowning. The trees that gave the well its wisdom are drowning in it.\n\nShe's doing it on purpose, you know. Sinann. She went to these trees for wisdom and they drowned her. Now she's drowning them back.", 'default'),
        ],
        {'default': {'text': "From Lucht an Tobair.", 'choice': [f1, f2]}})

f3 = z.item("Stone-Singer's Torc", 'neck', 26, 'faith', "Taken from a well-caller. The ogham on it is a lullaby turned backwards.")
f4 = z.item('Standing-Stone Bracer', 'bracer', 26, 'ward', "Grey stone, cut thin as leather. It shouldn't bend. It does.")
f5 = z.item('Ripple-Ring', 'ring', 26, 'mind', "A ring that leaves ripples in the air when you move your hand.")
z.quest('sh_well_callers', 'The Well-Callers', 26, 'sh_ceallach',
        "The eriu well-callers stand at the stones round the pool every night, singing her up. Kedger set them there, and they stay whether he lives or not.\n\nWill you [silence the stones]? All four sides: west, north, east and south. If they wake together, the well wakes with them.",
        'silence the stones',
        "Eriu well-callers sing at the standing stones round Connla's Well, calling Sinann up.",
        [
            hunt([1225, 690], "Silence 3 eriu well-callers at the western stones, " + where((1225, 690), 'sh_ceallach'), 'eriu well-caller', 3),
            hunt([1480, 680], "Drive off 2 well-water elementals at the eastern stones", 'well-water elemental', 2),
            hunt([1300, 775], "Break the drowned-river elemental at the southern stones", 'drowned-river elemental', 1,
                 text="The elemental collapses into a wave and runs back into the pool. The water is higher than it was an hour ago."),
            end_talk('sh_ceallach', "Return to Fili Ceallach", "Higher. Even with the callers quiet, it's higher.\n\nShe doesn't need them any more. She's nearly up. There's one thing in all the old stories that ever sang her to sleep - her own blood. And there's a girl in Ceannai who is of Sinann's line. The brehon's daughter. Kedger knew it. That's why he wanted her.", 'default'),
        ],
        {'default': {'text': "From Lucht an Tobair.", 'choice': [f3, f4, f5]}},
        requires='sh_hazel_thieves')

f6 = z.item("Arracht's Fang", 'gem', 27, 'might', "A fang as long as your forearm. The great ollipheist won't miss it. It has hundreds.")
f7 = z.item('Serpent-Skin Belt', 'belt', 27, 'finesse', "Ollipheist hide. It's never quite still.")
f8 = z.item('Upriver Ring', 'ring', 27, 'ward', "Found in Arracht's coils. Whoever wore it went upriver and didn't come back.")
z.quest('sh_serpent_upriver', 'The Serpent Upriver', 27, 'sh_bebhinn',
        "Arracht, the great ollipheist of the south-west shore, has started swimming upriver toward the well. The old stories say the serpents came out of the well with the river, and they go home to it when the river wakes.\n\nThe ollipheist shore is the worst of the estuary, by the Lough Gur border. Will you [find Arracht's trail]? Take friends.",
        "find Arracht's trail",
        "Arracht, the great ollipheist, is swimming upriver toward Connla's Well.",
        [
            hunt([360, 1470], "Kill 4 ollipheists at the serpent pool on the south-west shore, " + where((360, 1470), 'sh_bebhinn'), 'ollipheist', 4),
            hunt([470, 1580], "Defeat the elder ollipheist in the deep reeds", 'elder ollipheist', 1,
                 text="The elder ollipheist thrashes and goes still. In the reeds beyond it, a trail of flattened stems as wide as a cart heads north-east - toward the river, toward the well. Arracht is on the move."),
            end_talk('sh_bebhinn', "Return to Bebhinn the Seanchai", "On the move. Then the Lucht an Tobair will be hunting him along the shore - you'll hear the call when they do.\n\nGo to the brehon's daughter now. If anyone can sing the river down, it's her.", 'default'),
        ],
        {'default': wake({'text': "From the Hy Brasil camp.", 'choice': [f6, f7, f8]}, 'shannon_serpent_upriver')},
        requires='sh_well_callers')

f9 = z.item("Orla's Song-Ring", 'ring', 28, 'charm', "Orla's ring. She says it sings the low part.")
f10 = z.item('Ceannai Lullaby Torc', 'neck', 28, 'faith', "Silver from Ceannai, with a lullaby engraved round it in ogham.")
z.quest('sh_orla_at_the_well', 'The Brehon\'s Daughter', 28, 'brehon_aodh',
        "The filid want Orla at the well. To sing. To sing to that - thing - the river. My daughter.\n\nShe wants to go. She says she's been dreaming of the water for five years, and now she knows why. Will you [take her to the well]? And bring her home. Bring her home again.",
        'take her to the well',
        "Orla, of Sinann's line, will sing at Connla's Well to quiet the rising river.",
        [
            talk('orla', "Talk to Orla, who is waiting at the old eriu hunting camp, " + where((1006, 1132), 'brehon_aodh'),
                 "Father's told you, then. Don't look like that. I'm not afraid. Well. I am. But the eriu taught me their songs, and Mother taught me ours, and Ceallach says between them I have the whole lullaby.\n\nWhen you're [ready], I'll go up to the well.", kw='ready'),
            defend(Z, [1350, 600], "Guard Orla at the northern stones while she sings", "Orla's song ends. The pool goes flat and still - and then, very slowly, it begins to rise again, and a woman's shape stands up out of it, made of water.",
                   'Orla', 60163820, 26, "Orla stands at the northern stones and sings down into the pool. The water answers - and so does everything in it.",
                   [(60167807, 'well-water elemental', [25, 26]), (60161154, 'hazel sprite', [24, 25])], 'Keep Orla safe while she sings', model=F, duration=100, every=20, count=2),
            end_talk('sh_ceallach', "Bring Orla to Fili Ceallach", "She held it. For a minute, she held the whole river still.\n\nAnd then Sinann stood up. She heard her own blood singing and she came up to see who it was. She won't go back down now. Not without a fight - a hard one. Orla's safe. Take her home first.", 'default'),
        ],
        {'default': {'text': "From Ceannai, and from a father.", 'choice': [f9, f10]}},
        requires='sh_serpent_upriver')

f11 = z.item("Sinann's Tear", 'gem', 30, 'faith', "A drop of the river that never dries. Sinann wept it when she understood.")
f12 = z.item('Drowned-Hazel Cloak', 'cloak', 30, 'mind', "Leaves of the nine hazels, green again, woven into grey wool.")
f13 = z.item("Well-Keeper's Torc", 'neck', 30, 'ward', "The torc of the Lucht an Tobair, given to those who kept the well.")
f14 = z.item('River-Mouth Ring', 'ring', 30, 'might', "Silver and green, the colours of the river where it meets the sea.")
z.quest('sh_sinann', 'Sinann', 30, 'sh_ceallach',
        "Sinann stands at the northern stones of Connla's Well, the river pouring out of her, and the water rises every hour. She drowned for the well's wisdom. She means to drown the estuary for it.\n\nThis is GROUP work - the hardest in the estuary. Bring the best you know. Will you [face Sinann]?",
        'face Sinann',
        "Sinann, the drowned spirit of the river, has risen at Connla's Well.",
        [
            reach(Z, [1350, 605], "Go to the northern stones of Connla's Well, " + where((1350, 605), 'sh_ceallach'), "A woman made of the river stands among the stones, nine hazels bowing over her. 'I came for wisdom,' she says, 'and the well gave me water. A thousand years of water. Now I will give it back.'", r=30),
            hunt([1350, 575], "Defeat Sinann at the northern stones", 'Sinann', 1,
                 text="Sinann breaks like a wave on a rock - and for a moment, in the spray, there is a young woman with wet hair, looking very surprised, and then only water, falling back into the pool."),
            choice('sh_ceallach', "Return to Fili Ceallach",
                   "The water's going down. All the way down the river to the sea. Listen - you can hear the estuary breathe out.\n\nShe'll gather again. She's the river; she can't not be. Lucht an Tobair can [lay her to rest] - sing her into the deep hollow under the well and seal it, so she sleeps for a thousand years. Or we can [give her the wisdom] she came for - a hazelnut from each of the nine trees, dropped into the well - and hope a wise river is a kinder one.",
                   [('lay her to rest', "To rest, then. Orla will sing it with us. Sleep, Sinann. Sleep well, at last.", 'ending:rest'),
                    ('give her the wisdom', "Nine nuts, then, into the well. ...Look. The water's gone clear. I think she's laughing.", 'ending:wisdom')]),
        ],
        {'rest': {'text': "Take these. From the well, the Lucht an Tobair, and a river that's sleeping.", 'items': [f11], 'choice': [f12, f13, f14]},
         'wisdom': {'text': "Take these. From the well, the Lucht an Tobair, and a river that's thinking.", 'items': [f11], 'choice': [f12, f13, f14]}},
        group=True, requires='sh_orla_at_the_well')
