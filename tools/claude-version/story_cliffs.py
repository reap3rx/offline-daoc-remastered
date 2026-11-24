"""The Cliffs of Moher's story quests (claude 2026-11-24, the zone brief in Zone Reviews) - see story_gen.py. Places: zone metres
[x, y].

Moved out of story_hib.py with the zone's rebuild:
    python tools/claude-version/story_gen.py story_cliffs

Six arcs, 25 quests, one thread: Norse raiders keep landing under the cliffs in thick fog, and nobody sees them coming. Somebody
is bringing them in. The Grey Man - the Fear Liath, the fog that wrecks ships - hides the longships in his fog, and every death
they cause is his: the fetches that walk ahead of the dead are thick on the cliff paths. The cliff dwellers are paid in Norse
silver to keep the coves clear; the koalinth's old pact has been sold to the Norse as a pilot's road through the rocks. And the
fog isn't his own: it was a gift from the east, from a lady of the forest court (Hibernia's northern thread, decided
2026-11-23: the Unseelie Court is behind the north's troubles; the reveal is the Cursed Forest's). Two old quests are folded
in: The Fetch (fetch) and The Seventh Year (koalinth_pact). The Watch of Moher's arcs: Tir Urphost's Troubles, The Cliff
Dwellers, The Northmen. The Seers of Moher's: The Fetch, The Seventh Year, The Grey Man.
"""
import math
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE = 1882, 1876, 1347
M, F, OLD = 337, 365, 362
Z = 203
ZONES = []

z = Zone(Z, 'Cliffs of Moher', 3, 'hib_cliffs_of_moher')
ZONES.append(z)

AT, NAMES = {}, {}


def person(id, name, xy, kind, level, **kw):
    NAMES[id] = name
    AT[id] = tuple(xy)
    z.npc(id, name, list(xy), kind, level, **kw)


def where(to, frm):
    """'about 240 m north-west of Watch-Captain Aodhan' (y grows southward)."""
    fx, fy = AT[frm]
    dx, dy = to[0] - fx, to[1] - fy
    d = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(-dy, dx)) % 360
    names = ['east', 'north-east', 'north', 'north-west', 'west', 'south-west', 'south', 'south-east']
    dirn = names[int(((ang + 22.5) % 360) // 45)]
    dist = ('%d m' % (round(d / 10) * 10)) if d < 950 else ('%.1f km' % (d / 1000))
    return 'about %s %s of %s' % (dist, dirn, NAMES[frm])


def hunt(xy, goal, target, count, text=None, give=None):
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
person('cm_aodhan', 'Watch-Captain Aodhan', (805, 388), 'm', 36, guild='the Watch of Moher',
       idle="From the top of this tower you can see thirty miles of sea. On a clear day. We haven't had a clear day in a month.")
person('cm_gormlaith', 'Seer Gormlaith', (658, 522), 'f', 34, model=OLD, guild='the Seers of Moher',
       idle="I read omens for a living. This month the omens are reading me.")
person('sorcha', 'Sorcha', (664, 514), 'f', 16, idle="I saw myself on the cliffs. Myself. Smiling at me.")
person('lorcan', 'Old Lorcan', (676, 500), 'm', 30, model=OLD,
       idle="A fetch at morning means long life. At evening, death. Nobody wants to say which it was.")
person('nuala', 'Nuala the Net-Mender', (672, 498), 'f', 34,
       idle="Every seventh year the sea takes a child. We call it the sea. It isn't the sea.")
z.npc('fintan', 'Fintan', [168, 1056], 'm', 12, size=42, during=['koalinth_pact/fintan'])
NAMES['fintan'] = 'Fintan'
AT['fintan'] = (168, 1056)
person('cm_dubhdara', 'Fisher Dubhdara', (240, 560), 'm', 26,
       idle="I hid in the rocks when they came. I'm still hiding, if I'm honest. I just do it standing up now.")
person('cm_muadhan', 'Seer Muadhan', (600, 1000), 'm', 32, guild='the Seers of Moher',
       idle="The stones of the circle used to hum. Now they hiss. Stones shouldn't hiss.")
person('cm_conall', 'Watchman Conall', (1220, 260), 'm', 28, guild='the Watch of Moher',
       idle="The lurikeen who lived in those huts were friends of mine. The bocan ate them. Or worse.")

# ======================================================================== Tir Urphost's Troubles (24 to 27) - Watch
a1 = z.item("Roadwarden's Bracer", 'bracer', 24, 'ward', "The Watch gives one to anyone who keeps the Connacht road open.")
a2 = z.item('Bocan-Tooth Charm', 'gem', 24, 'might', "A bocan's tooth on a cord. It still tries to bite.")
z.quest('cm_connacht_road', 'The Road from Connacht', 24, 'cm_aodhan',
        "Welcome to the edge of the world. The road from Connacht is the only road we have, and the bocan from the lurikeen huts have been sitting on it.\n\nWill you [clear the road]? Watchman Conall is out at the huts. He'll tell you how bad it is.",
        'clear the road',
        "Bocan from the old lurikeen huts are waylaying the Connacht road.",
        [
            hunt((1300, 500), "Drive off 5 bocan on the Connacht road, " + where((1300, 500), 'cm_aodhan'), 'bocan', 5),
            end_talk('cm_conall', "Report to Watchman Conall at the lurikeen huts, " + where(AT['cm_conall'], 'cm_aodhan'),
                     "Road's clear? Good. The bocan will be back, they always are.\n\nBut that's not what I'm watching. Look west, past the town. See the fog sitting on the sea? It's sat there for a month. No wind moves it. And things come out of it.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [a1, a2]}})

a3 = z.item("Fog-Lantern Ring", 'ring', 25, 'mind', "A ring with a chip of lantern-glass. It glows faintly in fog.")
a4 = z.item("Field-Warden's Belt", 'belt', 25, 'finesse', "Plain leather, with a bone whistle for calling the watch.")
z.quest('cm_phantoms', 'Phantoms in the Fields', 25, 'cm_conall',
        "The fog phantoms come up off the sea at night and drift across the fields. They don't do much. They don't need to: nobody will go out to the barley.\n\nWill you [thin them out]? And see where they're coming from.",
        'thin them out',
        "Fog phantoms drift over Tir Urphost's fields from the sea.",
        [
            hunt((950, 450), "Break 5 fog phantoms in the fields, " + where((950, 450), 'cm_conall'), 'fog phantom', 5,
                 text="Every one of them drifts west as it fades - toward the cliffs, toward the sea."),
            reach(Z, (470, 330), "Follow the fog west to the cliff edge, " + where((470, 330), 'cm_conall'),
                  "Below you the cliffs drop to the sea. The fog sits on the water like wool, and somewhere in it, very faintly, oars.", r=25),
            end_talk('cm_aodhan', "Tell Watch-Captain Aodhan what you heard", "Oars. In the fog. Under the cliffs.\n\nThere's nothing out there to row. Not ours, anyway.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [a3, a4]}},
        requires='cm_connacht_road')

a5 = z.item('Salvaged Axe-Head Charm', 'gem', 26, 'might', "A Norse axe-head, found in a Hibernian fishing hut.")
a6 = z.item("Fisher's Oilskin Cloak", 'cloak', 26, 'ward', "Stiff with salt. It has kept a lot of rain off a lot of fishermen.")
z.quest('cm_missing_crew', 'The Empty Camp', 26, 'cm_aodhan',
        "There's a fishing camp in the middle cove, under the cliffs. Five men. They haven't come up for their bread in a week.\n\nWill you [go down to the cove]? Take the ravine path. There's a fisher hiding in the rocks there - Dubhdara - he sent up a boy with word. Talk to him.",
        'go down to the cove',
        "A fishing crew in the middle cove under the cliffs has vanished.",
        [
            talk('cm_dubhdara', "Find Fisher Dubhdara in the rocks of the middle cove, " + where(AT['cm_dubhdara'], 'cm_aodhan'),
                 "They came out of the fog. Big men. Shields. They took Breasal and Colm and the others and put them in the boats. I hid. Gods forgive me, I [hid].", kw='hid'),
            search(Z, (210, 630), "Search the empty fishing camp (click the glinting spot)", "a Norse axe-head", CRATE,
                   "A broken axe-head, northern work, sunk in the door-post. Raven runes on the cheek. These weren't pirates. These were Norse."),
            end_talk('cm_aodhan', "Bring the axe-head to Watch-Captain Aodhan", "Raven runes. Norse.\n\nMidgard's longships, on our coast, and the watchtower never saw a sail. How? We see thirty miles on a clear day.\n\nOn a clear day.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [a5, a6]}},
        requires='cm_phantoms')

a7 = z.item("Watchtower Torc", 'neck', 27, 'faith', "Bronze, with the watchtower worked into the clasp.")
a8 = z.item('Beacon-Keeper Bracer', 'bracer', 27, 'ward', "Scorched round the cuff by a hundred lightings of the beacon.")
z.quest('cm_first_sail', 'The First Sail', 27, 'cm_aodhan',
        "I want to see them with my own eyes. Tonight I'll keep the beacon burning at the top of the tower and watch the fog. If they come up the watchtower road, I'll need someone between them and the beacon.\n\nWill you [keep the beacon] with me?",
        'keep the beacon',
        "Watch-Captain Aodhan will watch for the Norse from the top of Moher Watchtower.",
        [
            defend(Z, (800, 380), "Keep the beacon-keeper alive at the watchtower", "The raiders break off and melt back into the fog toward the cliffs. Out at sea, for one moment, the fog opens: a longship, a raven sail - and on its prow a tall grey shape that isn't a man.",
                   'the beacon-keeper', 60163820, 26, "The beacon roars up. Out of the fog on the watchtower road come Norsemen with axes.",
                   [(60167667, 'Norse raider', [25, 26]), (60167654, 'Norse bowman', [25, 26])], 'Keep the beacon-keeper safe', model=M, duration=100, every=20, count=2),
            end_talk('cm_aodhan', "Talk to Watch-Captain Aodhan", "You saw it too. Grey. Tall. Standing on their prow like a figurehead, and the fog wrapped round the ship like a cloak.\n\nThe Seers in town will know what that was. I'd rather not, but we'd better.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [a7, a8]}},
        requires='cm_missing_crew')

# ======================================================================== The Fetch (25 to 29) - Seers
it_fetch = z.item("Fetch-Glass Pendant", 'neck', 25, 'mind', "A little mirror that shows you a moment late. You get used to it.")
it_comb = z.item("Sorcha's Comb-Pin", 'gem', 25, 'charm', "A comb of white bone. The fetch carried it; it is the only thing of hers it took.")
it_bocan = z.item('Bocan-Hide Bracer', 'bracer', 25, 'might', "The bocan are goblins of the cliffs. This one's hide is tough as boot-leather.")
it_cliff = z.item("Cliff-Walker's Cloak", 'cloak', 25, 'ward', "Grey wool, weighted at the hem against the cliff wind.")
z.quest('fetch', 'The Fetch', 25, 'sorcha',
        "Three evenings ago I saw myself on the cliff path. My own face, my own shawl - walking toward me, smiling. Then gone.\n\nA fetch, Old [Lorcan] says. At evening, it means death. I'm twenty-two years old. Will you [find it]? Find it before it finds me.",
        'find it',
        "Sorcha saw her own fetch - her double - on the cliffs at evening. An omen of death.",
        [
            talk('lorcan', 'Ask Old Lorcan about fetches',
                 "A fetch is the shape of a death, walking about early. Find it before it finds her, and kill it, and maybe the death goes elsewhere. Maybe. They walk the eastern cliff path where the [bocan] are.", kw='bocan'),
            hunt((850, 1180), "Clear the bocan from the eastern cliff path, " + where((850, 1180), 'sorcha'), 'bocan', 5,
                 text="One of them chatters something about 'the smiling lady' going east."),
            reach(Z, (1116, 1240), 'Follow the cliff path east', "Fetches drift on the cliff tops - pale doubles of the living, wearing borrowed faces. None of them is hers. Yet.", r=20),
            hunt((1116, 1246), 'Destroy 4 drifting fetches', 'fetch', 4),
            search(Z, (1130, 1252), 'Search the cliff edge', "a white bone comb", CRATE,
                   "Sorcha's comb, still warm. And standing at the very edge of the cliff, looking out to sea: Sorcha. Smiling."),
            boss(Z, (1124, 1250), "Destroy Sorcha's fetch", "The fetch stops smiling. For a moment it looks only tired, and very sad, and then it's mist.",
                 "Sorcha's Fetch", 60160819, 27, "It turns. It has her face exactly, and her voice: 'You're early.'",
                 objective="Destroy Sorcha's fetch", model=F, hp=2.2, adds=[(60160819, 'fetch', [24, 25])], every=30, count=1),
            choice('sorcha', 'Return to Sorcha',
                   "Is it gone? It is, isn't it. I can feel it. Like a weight off.\n\nIt said something. Before. I can see it in your face. What did it say?\n\n(The fetch said: 'You can't kill a death. Only move it.' You could tell her [the truth], or [say nothing].)",
                   [('the truth', "...Someone else. In my place. Gods. Then I'll watch the cliff path every evening until Samhain, and turn back whoever I see. I owe them that.", 'ending:truth'),
                    ('say nothing', "Nothing? It just went? ...Then I'm free. I'm free. I'm going to go dancing tonight. Come with me!", 'ending:silent')]),
        ],
        {'truth': {'text': "Take this. It's mine to give, now.", 'items': [it_comb], 'choice': [it_fetch, it_bocan]},
         'silent': {'text': "Take this. And come dancing.", 'tragic': True, 'items': [it_comb], 'choice': [it_cliff, it_bocan]}},
        topics={'Lorcan': "Old Lorcan, by the well. He knows every omen there is, and believes in half of them."})

b1 = z.item("Seer's Mirror Ring", 'ring', 26, 'mind', "A ring set with a tiny mirror. Seers use them to catch fetches looking.")
b2 = z.item('Omen-Knot Belt', 'belt', 26, 'faith', "Knotted with the seven omens. You can untie one, once.")
z.quest('cm_fetches_everywhere', 'A Death for Every Fetch', 26, 'cm_gormlaith',
        "Sorcha's fetch wasn't the only one. There are dozens on the cliff path now. A fetch walks before a death - so dozens of deaths are coming, and soon.\n\nWill you [catch a fetch] for me? I need to see whose faces they wear. Bring me their glass - the little shine they leave when they break.",
        'catch a fetch',
        "Seer Gormlaith wants to know whose faces the fetches on the cliff path are wearing.",
        [
            hunt((1120, 1245), "Break 5 fetches on the fetch ledge at night, " + where((1120, 1245), 'cm_gormlaith'), 'fetch', 5, give='fetch-glass',
                 text="In the shine each one leaves, a face: a watchman, a fisher, a watchman, a watchman. All men of the coast."),
            end_talk('cm_gormlaith', "Bring the fetch-glass to Seer Gormlaith", "Watchmen. Fishers. The men who stand on this coast.\n\nThe deaths aren't coming to Tir Urphost. They're coming to the coves. And the fetches are walking there first, like hounds sent ahead.", 'default'),
        ],
        {'default': {'text': "From the Seers.", 'choice': [b1, b2]}},
        requires='fetch')

b3 = z.item("Cairn-Stone Charm", 'gem', 27, 'faith', "A pebble from the Grey Man's cairn. It is always damp.")
b4 = z.item("Fetch-Follower's Bracer", 'bracer', 27, 'finesse', "Soft leather, for walking quietly behind things that shouldn't know you're there.")
z.quest('cm_whose_death', 'Where the Fetches Go', 27, 'cm_gormlaith',
        "Follow them. Not the fetches on the path - the ones that walk west at night, toward the cliffs over the coves. Where they gather, something is calling them.\n\nWill you [follow the fetches]?",
        'follow the fetches',
        "The fetches walk west at night, toward the cliffs over the coves. Something is calling them.",
        [
            reach(Z, (395, 455), "Follow the fetches west to a cairn on the cliff top, " + where((395, 455), 'cm_gormlaith'),
                  "A cairn of grey stones on the cliff edge, wet in dry weather. The fetches stand round it like a congregation, facing the sea.", r=25),
            hunt((395, 455), "Break 3 fetches at the cairn", 'fetch', 3),
            search(Z, (398, 458), "Search the cairn (click the glinting spot)", "a grey fleece", CRATE,
                   "Tucked into the stones: a hank of grey fleece, wet as seaweed, cold as the sea. It smells of salt - and, underneath, of rotting roses.",
                   give='the grey fleece'),
            end_talk('cm_gormlaith', "Bring the fleece to Seer Gormlaith", "A grey fleece. On a cairn. With the fetches round it.\n\nThe Fear Liath. The Grey Man - the fog that comes in off the sea and wrecks ships on the rocks. My grandmother's stories. I never believed my grandmother's stories.", 'default'),
        ],
        {'default': {'text': "From the Seers.", 'choice': [b3, b4]}},
        requires='cm_fetches_everywhere')

b5 = z.item("Grey Man's Fleece Mantle", 'cloak', 29, 'mind', "Woven from the grey fleece, cleansed by the Seers. It still smells faintly of roses.")
b6 = z.item('Fear Liath Ward', 'neck', 29, 'ward', "A Seers' ward against the Grey Man. It works on fog, mostly.")
b7 = z.item('Seventh-Omen Ring', 'ring', 29, 'charm', "The seventh omen is 'the one you didn't see coming'. This ring is for that one.")
z.quest('cm_grey_cairn', 'The Grey Man', 29, 'cm_gormlaith',
        "If it's the Grey Man, the stories say he can be named. Name a fog spirit and he has to listen. But to name him you need to stand in his fog when it's thickest, at the moor's heart, and speak through his wraiths.\n\nWill you [go to the moor]? Seer Muadhan will help. He knows the old words.",
        'go to the moor',
        "Seer Gormlaith means to name the Grey Man, the fog spirit of the cliffs.",
        [
            talk('cm_muadhan', "Find Seer Muadhan near the stone circle on the moor, " + where(AT['cm_muadhan'], 'cm_gormlaith'),
                 "The Grey Man. Yes. I've felt him on the moor every night. When you're ready, go into the fog at the moor's heart and [call his name] - Fear Liath - and I'll hold the words.", kw='call his name'),
            hunt((790, 1140), "Break the wraiths at the moor's heart, " + where((790, 1140), 'cm_muadhan'), 'mist wraith', 4,
                 text="As the last wraith fades a voice comes out of the fog, everywhere at once: 'Who calls the Fear Liath? I hear you. I have a bargain to keep, and a lady to please. Go home.'"),
            end_talk('cm_muadhan', "Tell Seer Muadhan what the fog said", "'A lady to please.' He serves someone.\n\nThe Grey Man is old and proud and serves no one. Unless someone gave him something he couldn't refuse. Go back to Gormlaith. This is bigger than our coast.", 'default'),
        ],
        {'default': {'text': "From the Seers.", 'choice': [b5, b6, b7]}},
        requires='cm_whose_death')

# ======================================================================== The Seventh Year (27 to 32) - Seers
c1 = z.item("Net-Mender's Ring", 'ring', 27, 'finesse', "Nuala's spare. She mends nets with it on.")
c2 = z.item('Tide-Pool Charm', 'gem', 27, 'faith', "A shell from the tide pools. Put it to your ear and the sea says your name.")
z.quest('cm_tide_pools', 'Cut Nets', 27, 'nuala',
        "The koalinth on the south-west rocks have been cutting our nets. They never did that. They take a child every seventh year - Gods help us - but they never touched the nets.\n\nWill you [go to the rocks]? Something's changed down there.",
        'go to the rocks',
        "The koalinth have started cutting the village's nets on the south-west rocks.",
        [
            hunt((140, 945), "Drive off 5 koalinth slinkers at the koalinth landing, " + where((140, 945), 'nuala'), 'koalinth slinker', 5,
                 text="Among the cut nets: a coil of Norse rope, tarred, tied in a sea-knot no Hibernian uses."),
            end_talk('nuala', "Bring the rope to Nuala", "Norse rope. On the koalinth rocks.\n\nThe koalinth don't trade. Not with us. Somebody's been talking to them. And this is the seventh year.", 'default'),
        ],
        {'default': {'text': "From the village.", 'choice': [c1, c2]}})

it_koal = z.item('Koalinth-Scale Token', 'gem', 30, 'mind', "A blue-green scale, pierced and hung on a cord. The koalinth give them to children they claim.")
it_pact = z.item("Pact-Breaker's Ring", 'ring', 30, 'might', "Cut from the koalinth tide-caller's own hand.")
it_tide = z.item('Tide-Caller Mantle', 'cloak', 30, 'faith', "Woven of kelp and something finer. Water runs off it like off a seal.")
it_spear = z.item("Spearman's Bracer", 'bracer', 30, 'finesse', "Cliff-dweller work, bone and sinew.")
z.quest('koalinth_pact', 'The Seventh Year', 30, 'nuala',
        "Every seventh year, a child of this village is lost to the sea. Swept off the rocks. We mourn them and we say it's the sea.\n\nThis is the seventh year, and last night my son Fintan was gone from his bed. The footprints on the floor were webbed. Will you [find Fintan]?",
        'find Fintan',
        "Every seventh year a child of Nuala's village is lost to the sea. This year it was her son - and the footprints were webbed.",
        [
            reach(Z, (215, 630), "Go to the old fishing camp in the middle cove, " + where((215, 630), 'nuala'),
                  "The camp's empty - the Norse took the crew. On the door of the hut, scratched faintly: seven lines, and then seven more, and then seven more.", r=20),
            hunt((360, 1000), "Fight through the cliff dweller spearmen at their nets on the south cliff tops", 'cliff dweller spearman', 5,
                 text="The cliff dwellers fight like men defending something. When the last one falls, he says: 'The pact. You'll break the pact. The Norse paid for it.'"),
            search(Z, (212, 636), "Search the fishing camp's hut", "a koalinth-scale token", CRATE,
                   "A child's token, on a cord: a blue-green scale. Under the floorboards, a ledger in a careful hand - the village elders' hand. A name every seven years. And next to each: 'Good fishing.'",
                   give="the elders' ledger"),
            hunt((172, 1047), 'Fight through 5 koalinth slinkers on the southern rocks', 'koalinth slinker', 5),
            boss(Z, (160, 1060), 'Defeat the koalinth tide-caller', "The tide-caller falls back into the surf. On the rocks behind it, a boy in a koalinth's cloak blinks at you.",
                 'Tide-Caller Mairgread', 60162948, 33, "A koalinth with a crown of shells rises from the waves. 'The pact is old. The pact is fair. The boy is ours.'",
                 objective='Defeat the Tide-Caller', hp=2.5, adds=[(60162948, 'koalinth slinker', [29, 30])], every=25, count=2),
            L('fintan', talk('fintan', 'Talk to Fintan', "They were nice to me. They said I'd learn to breathe water. They said the other children did. And the big men with the raven sail said I'd row for them, after. Is Mam angry? Can I go [home]?", kw='home')),
            choice('nuala', 'Bring Fintan home to Nuala',
                   "FINTAN. Oh, my love.\n\n...And this? A ledger? In Old Eoghan's hand? 'Good fishing'?\n\nThey SOLD them. Every seventh year. My grandmother's sister - she's in here. I could [expose the elders] in front of the whole village. Or I could [burn the ledger] and have my son home and say nothing.",
                   [('expose the elders', "In front of everyone. At the harbour, at noon. Let them look at every mother in this village and explain.", 'ending:exposed'),
                    ('burn the ledger', "Into the fire. ...There. My son's home. The rest is the sea's business. I'll keep it that way. Gods forgive me.", 'ending:burned')]),
        ],
        {'exposed': {'text': "Take something. The village owes you more than it can pay.", 'items': [it_pact], 'choice': [it_tide, it_spear]},
         'burned': {'text': "Take something. And don't speak of it.", 'tragic': True, 'items': [it_koal], 'choice': [it_tide, it_spear]}},
        requires='cm_tide_pools')

c3 = z.item("Sea-Stack Bracer", 'bracer', 31, 'ward', "Barnacled stone, ground smooth. Waves have been trying to break it for a thousand years.")
c4 = z.item("Pilot's Knot Charm", 'gem', 31, 'mind', "A sea-knot in tarred rope. It shows the way through rocks, if you can read it.")
z.quest('cm_pact_sold', 'The Pilots', 31, 'nuala',
        "Fintan keeps talking about the big men with the raven sail. He says the koalinth were to teach him the way through the rocks - so he could steer for the Norse.\n\nThey're selling the sea-road. The koalinth know every rock on this coast. Will you [break the pilots]? There's a tidecaller at the sea-stacks in the far south who teaches them.",
        'break the pilots',
        "The koalinth are teaching the Norse the way through the rocks of the coast.",
        [
            hunt((122, 1377), "Defeat the koalinth tidecaller at the sea-stacks, " + where((122, 1377), 'nuala'), 'koalinth tidecaller', 1,
                 text="On the tidecaller's belt: a chart of the coast in Norse runes, every rock marked, and a grey thread tied round it like a ribbon."),
            end_talk('nuala', "Bring the chart to Nuala", "A pilot's chart. With a grey thread on it.\n\nThe Seers in town are saying 'Grey Man'. Old women's stories. ...Show this to Gormlaith. I'm keeping my son inside.", 'default'),
        ],
        {'default': {'text': "From the village.", 'choice': [c3, c4]}},
        requires='koalinth_pact')

c5 = z.item("Brarn's Shell Crown", 'neck', 32, 'faith', "Brarn's crown of shells. It hums with the tide.")
c6 = z.item('Koalinth Chief-Ring', 'ring', 32, 'might', "A heavy ring of sea-gold.")
c7 = z.item('Rock-Road Cloak', 'cloak', 32, 'finesse', "Sealskin, grey-green. It's never quite dry.")
z.quest('cm_brarn', 'Brarn', 32, 'nuala',
        "Brarn is the koalinth chief on the rocks south of here. He made the pact with the elders long ago, and now he's sold it to the Norse.\n\nWill you [face Brarn]? Ask him who sold it. Then do what you think is right.",
        'face Brarn',
        "Brarn, chief of the koalinth, has sold the sea-road to the Norse.",
        [
            hunt((194, 1248), "Defeat Brarn on the southern rocks, " + where((194, 1248), 'nuala'), 'Brarn', 1,
                 text="Brarn sinks onto the rocks. 'The grey one came out of the fog. He said the pact was his to sell, because the sea is his when the fog is on it. He said a lady in the east would make him a king of fogs. What could we do?'"),
            choice('nuala', "Return to Nuala",
                   "Brarn's beaten. The koalinth will be leaderless for a season.\n\nThe village can [end the pact] - no more children, no more 'good fishing', and the koalinth our enemies forever. Or [make a new pact] with whoever leads them next: the sea-road closed to the Norse, the children kept at home, and the fish we always had.",
                   [('end the pact', "Ended, then. Let them be our enemies. At least they'll be honest ones.", 'ending:ended'),
                    ('make a new pact', "A new one. Written down. In front of everyone. I'll write it myself.", 'ending:new')]),
        ],
        {'ended': {'text': "From the village.", 'choice': [c5, c6, c7]},
         'new': {'text': "From the village.", 'choice': [c5, c6, c7]}},
        requires='cm_pact_sold')

# ======================================================================== The Cliff Dwellers (29 to 34) - Watch
d1 = z.item("Cliff-Top Bracer", 'bracer', 29, 'might', "Cliff dweller work: bone and hide, stitched with gut.")
d2 = z.item("Watchman's Whistle Charm", 'gem', 29, 'finesse', "A bone whistle. Every watchman on the cliffs carries one.")
z.quest('cm_dweller_raids', 'Raiders on the Cliff Tops', 29, 'cm_aodhan',
        "The cliff dwellers have come out of the ravine and onto the plateau. Three farms burned last week. They never came this far inland before.\n\nWill you [push them back]? And look at what they're carrying. Cliff dwellers don't burn farms for fun.",
        'push them back',
        "The cliff dwellers have come up out of the ravine and are burning farms on the plateau.",
        [
            hunt((450, 700), "Drive back 6 cliff dwellers in the ravine, " + where((450, 700), 'cm_aodhan'), 'cliff dweller', 6,
                 text="One of them carries a purse: northern silver, Norse coins with a raven stamped on them."),
            end_talk('cm_aodhan', "Bring the purse to Watch-Captain Aodhan", "Norse silver. In a cliff dweller's purse.\n\nThey're not raiding for themselves. They're clearing the way.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [d1, d2]}},
        requires='cm_first_sail')

d3 = z.item("Lookout's Ring", 'ring', 30, 'mind', "A ring with a notch for sighting along. Cliff dweller lookouts use them.")
d4 = z.item('Raven-Coin Belt', 'belt', 30, 'charm', "A belt hung with Norse coins, taken from cliff dweller purses.")
z.quest('cm_norse_silver', 'Paid in Silver', 30, 'cm_aodhan',
        "If the Norse are paying the cliff dwellers, someone keeps the tally. They have a lookout on the cliffs north of the ravine.\n\nWill you [find the tally]? I want to know what they're being paid for.",
        'find the tally',
        "The Norse are paying the cliff dwellers in silver. Somebody keeps the tally.",
        [
            hunt((340, 520), "Defeat the cliff dweller elder at the lookout, " + where((340, 520), 'cm_aodhan'), 'cliff dweller elder', 1),
            search(Z, (345, 525), "Search the lookout (click the glinting spot)", "a tally of knots", CRATE,
                   "A knotted cord: so many silver for the coves kept clear, so many for the watchtower road, so many for 'lights on the cliffs when the fog man calls'. And one big knot, for Whelihan's word.",
                   give='the tally-cord'),
            end_talk('cm_aodhan', "Bring the tally to Watch-Captain Aodhan", "'Lights on the cliffs when the fog man calls.' The wreckers' lights. And 'Whelihan's word'.\n\nChief Whelihan. Their chief sold us. I want him.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [d3, d4]}},
        requires='cm_dweller_raids')

d5 = z.item("Spear-Breaker's Bracer", 'bracer', 31, 'ward', "Bound tight round the forearm, for catching spear-shafts.")
d6 = z.item('Nets-of-the-Cliff Charm', 'gem', 31, 'finesse', "A knot from a cliff dweller's net, the kind they use to drop on you from above.")
z.quest('cm_spearmen', 'The Nets', 31, 'cm_aodhan',
        "Before Whelihan, his spearmen. They hold the nets on the south cliff tops - where they catch whoever climbs up from the koalinth rocks.\n\nWill you [break the nets]? Then Whelihan has nobody between him and us.",
        'break the nets',
        "Chief Whelihan's spearmen hold the nets on the south cliff tops.",
        [
            hunt((360, 1000), "Break 5 cliff dweller spearmen at the nets, " + where((360, 1000), 'cm_aodhan'), 'cliff dweller spearman', 5),
            hunt((360, 1000), "Defeat the cliff dweller elder at the nets", 'cliff dweller elder', 1),
            end_talk('cm_aodhan', "Return to Watch-Captain Aodhan", "The nets are down. Now Whelihan.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [d5, d6]}},
        requires='cm_norse_silver')

d7 = z.item("Whelihan's Chief-Torc", 'neck', 34, 'might', "The torc of the cliff dwellers' chief. It's heavier than it looks.")
d8 = z.item('Cliff-Hold Mantle', 'cloak', 34, 'ward', "Hides stitched together the way the cliff dwellers do it. Warm as a house.")
d9 = z.item("Sold-Word Ring", 'ring', 34, 'charm', "A ring with a raven on it, from a chief who sold his word.")
z.quest('cm_whelihan', 'Chief Whelihan', 34, 'cm_aodhan',
        "Chief Whelihan sold the coast for Norse silver. He's at his hold above the ravine with his best around him.\n\nThis is GROUP work. Will you [face Whelihan]? Bring him to the Watch alive if you can. Dead if you must.",
        'face Whelihan',
        "Chief Whelihan of the cliff dwellers sold the coast to the Norse.",
        [
            hunt((400, 780), "Break the cliff dweller elder at the hold, " + where((400, 780), 'cm_aodhan'), 'cliff dweller elder', 1),
            hunt((646, 789), "Defeat Chief Whelihan above the ravine", 'Chief Whelihan', 1,
                 text="Whelihan goes down on one knee. 'Silver? You think I did it for silver? The grey man came out of the fog and said our people would drown, every one, unless we kept the coves for his friends. I kept my people alive. What did you keep?'"),
            choice('cm_aodhan', "Return to Watch-Captain Aodhan",
                   "Whelihan's beaten. His people will scatter without him.\n\nWe can [hang him] at the watchtower as a warning to the next chief. Or [send him back] to his people with a message: the Watch will protect the cliff dwellers from the Grey Man too, if they stop selling the coast.",
                   [('hang him', "Hanged, then. The next chief will think twice. Gods, I hate this coast sometimes.", 'ending:hanged'),
                    ('send him back', "Back, then. With the message. If he keeps it, we've an ally. If he doesn't, I'll hang him myself.", 'ending:sent')]),
        ],
        {'hanged': {'text': "From the Watch.", 'tragic': True, 'items': [d7], 'choice': [d8, d9]},
         'sent': {'text': "From the Watch.", 'items': [d7], 'choice': [d8, d9]}},
        group=True, requires='cm_spearmen')

# ======================================================================== The Northmen (30 to 35) - Watch
e1 = z.item("Stockade-Scout's Ring", 'ring', 30, 'finesse', "A ring with a notch for every stake counted.")
e2 = z.item('Raven-Rune Charm', 'gem', 30, 'mind', "A raven rune, cut from a Norse shield.")
z.quest('cm_longphort_scout', 'The Longphort', 30, 'cm_aodhan',
        "The Norse have a camp in the north-west cove - a longphort, the old stories call them: a ship-fort, beached longships behind a stockade. They mean to stay.\n\nWill you [scout the longphort]? From the cliff top first. Then get close enough to count the bowmen.",
        'scout the longphort',
        "The Norse have built a longphort, a fortified ship-camp, in the north-west cove.",
        [
            reach(Z, (300, 250), "Look down on the longphort from the cliff top, " + where((300, 250), 'cm_aodhan'),
                  "Below: a stockade of sharpened logs, three longships drawn up on the shingle, smoke from a long hall. And Hibernians in chains carrying water from the stream.", r=30),
            hunt((240, 330), "Kill 4 Norse bowmen at the stockade gate", 'Norse bowman', 4),
            end_talk('cm_aodhan', "Report to Watch-Captain Aodhan", "Thralls. Our people. In chains.\n\nThe Watch will burn that longphort if it's the last thing we do. But first - the thralls.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [e1, e2]}},
        requires='cm_first_sail')

e3 = z.item("Thrall-Chain Bracer", 'bracer', 31, 'ward', "A link of thrall-chain, broken and beaten into a bracer.")
e4 = z.item("Freed Man's Belt", 'belt', 31, 'charm', "Breasal the fisher's own belt. He gave it to you when you cut his chain.")
z.quest('cm_thralls', 'The Thralls', 31, 'cm_dubhdara',
        "Breasal. Colm. The others. They're in the longphort, in chains. I saw them carrying water.\n\nI hid once. I won't hide again. Will you [free them]? I'll show you the stream where they fetch water - they're guarded, but not well.",
        'free them',
        "The fishing crew taken from the middle cove are thralls in the Norse longphort.",
        [
            hunt((200, 340), "Kill 5 Norse raiders guarding the water-carriers on the shingle, " + where((200, 340), 'cm_dubhdara'), 'Norse raider', 5),
            search(Z, (215, 360), "Break the thralls' fetters (click the glinting spot)", "the thralls' fetters", CRATE,
                   "The chains fall away. Breasal grips your arm. 'There's a skald in the camp, the jarl's singer. He sings every night about the grey man who brought them here. He knows everything.'"),
            end_talk('cm_dubhdara', "Bring the news to Fisher Dubhdara", "Breasal! Colm! ...All of them. All five.\n\nA skald who sings about the grey man. The Watch-Captain will want that singer.", 'default'),
        ],
        {'default': {'text': "From the coves.", 'choice': [e3, e4]}},
        requires='cm_longphort_scout')

e5 = z.item("Skald's Harp-Peg Charm", 'gem', 33, 'charm', "A harp peg of walrus ivory. It remembers every saga it ever held tight.")
e6 = z.item("Saga-Teller's Ring", 'ring', 33, 'mind', "A Norse ring, engraved with the first line of a saga that hasn't finished yet.")
e7 = z.item('Raven-Banner Cloak', 'cloak', 33, 'ward', "Cut from the longphort's banner. The raven looks the other way now.")
z.quest('cm_skald', "The Skald's Saga", 33, 'cm_aodhan',
        "The jarl's skald. If he sings about the grey man, he knows the bargain - who made it, and what for.\n\nWill you [bring me the saga]? The skald keeps by the beached ships. Take his harp, or his life, or both. I want the words.",
        'bring me the saga',
        "Jarl Hrafn's skald sings every night of the grey man who brought the Norse to the Cliffs.",
        [
            hunt((140, 300), "Kill 3 Norse huscarls by the beached longships, " + where((140, 300), 'cm_aodhan'), 'Norse huscarl', 3),
            boss(Z, (145, 290), "Defeat Thorgeir the Skald", "Thorgeir drops his harp. 'Kill me, then. The saga's already sung. The grey man came to Hrafn's hall in a fog that walked across the sea from the east. He said: a lady of the forest court gives you this coast, and asks only that you keep Lug's people busy.'",
                 'Thorgeir the Skald', 60166154, 35, "The jarl's skald puts down his harp and picks up an axe. 'Every saga needs a death in the middle.'",
                 objective='Defeat Thorgeir the Skald', hp=2.4, adds=[(60159139, 'Norse huscarl', [31, 32])], every=25, count=2),
            end_talk('cm_aodhan', "Bring the saga to Watch-Captain Aodhan", "'A lady of the forest court.' 'Keep Lug's people busy.'\n\nThis was never about our coast. Someone in the east is bleeding the realm at the edges. I'll send to Tir na nOg. You - take this. And when the Watch goes for the longphort, be with us.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [e5, e6, e7]}},
        requires='cm_thralls')

e8 = z.item("Jarl's Arm-Ring", 'bracer', 35, 'might', "Thick gold, taken from Jarl Hrafn's own high seat.")
e9 = z.item('Longphort-Breaker Torc', 'neck', 35, 'might', "Iron and bronze, given to whoever broke into the longphort first.")
z.quest('cm_raven_banner', 'The Raven Banner', 35, 'cm_aodhan',
        "Before the Watch attacks, I want their banner. A Norse war-band that loses its banner loses its luck - they believe it, and that's enough.\n\nWill you [take the banner]? It flies over the jarl's hall in the longphort.",
        'take the banner',
        "Watch-Captain Aodhan wants the Norse raven banner from the longphort before the attack.",
        [
            hunt((190, 250), "Fight through the Norse hersir at the jarl's hall, " + where((190, 250), 'cm_aodhan'), 'Norse hersir', 1),
            search(Z, (195, 255), "Cut down the raven banner (click the glinting spot)", "the raven banner", CRATE,
                   "The banner comes down: a black raven on red wool. Somewhere in the longphort a horn blows, and blows, and blows.",
                   give='the raven banner'),
            end_talk('cm_aodhan', "Bring the banner to Watch-Captain Aodhan", "Their raven, in the dust. They'll know it in every longship on the coast by tonight.\n\nNow we burn the longphort. Watch-Sergeant Aedan is gathering the war band on the cliff top. Go with him.", 'default'),
        ],
        {'default': {'text': "From the Watch.", 'choice': [e8, e9]}},
        requires='cm_skald')

# ======================================================================== The Grey Man (31 to 35) - Seers
f1 = z.item('Rift-Shard Charm', 'gem', 31, 'mind', "A shard of solid air from the distorters' rift. It's lighter than nothing.")
f2 = z.item("Distorter-Hide Bracer", 'bracer', 31, 'ward', "It bends the light a little around your wrist.")
z.quest('cm_rift', 'The Rift', 31, 'cm_gormlaith',
        "The Grey Man is a sea-fog. But this fog doesn't come off the sea - it comes from the east, over the rift where the moheran distorters live. Something is coming through.\n\nWill you [go to the rift]? Bring me some of the fog. I know, I know. Do your best.",
        'go to the rift',
        "Seer Gormlaith thinks the Grey Man's fog is coming through the distorters' rift in the east.",
        [
            hunt((1240, 520), "Drive off 5 moheran distorters at the rift, " + where((1240, 520), 'cm_gormlaith'), 'moheran distorter', 5),
            search(Z, (1245, 525), "Catch the fog in the rift (click the glinting spot)", "a jar of grey fog", CRATE,
                   "The fog pours through the rift from somewhere else, cold and thick. It smells of the sea - and under it, rotting roses. The same smell as the fleece.",
                   give='a jar of fog'),
            end_talk('cm_gormlaith', "Bring the fog to Seer Gormlaith", "Rotting roses. Again.\n\nThis isn't sea-fog. It's a forest fog, a fae fog, and it's being poured into the Grey Man like wine into a cup. Who came through the rift with it? Someone must have.", 'default'),
        ],
        {'default': {'text': "From the Seers.", 'choice': [f1, f2]}},
        requires='cm_grey_cairn')

f3 = z.item("Aoife's Thorn Ring", 'ring', 33, 'charm', "A ring of twisted thorn, cold as frost. Aoife's.")
f4 = z.item('Court-Silk Belt', 'belt', 33, 'mind', "Grey-green silk, finer than any weaver in Hibernia could make.")
z.quest('cm_aoife', 'The Lady from the Rift', 33, 'cm_gormlaith',
        "Watchman Conall saw a woman by the inland cliffs, east of the rift - tall, pale, in grey-green silk, walking on the fog as if it were a road.\n\nWill you [find her]? Be careful. If she came through the rift, she isn't from here.",
        'find her',
        "A pale woman in grey-green silk walks on the fog by the inland cliffs.",
        [
            hunt((1145, 987), "Defeat Aoife on the inland cliffs, " + where((1145, 987), 'cm_gormlaith'), 'Aoife', 1,
                 text="Aoife laughs as she falls. 'You think I'm the lady? I'm her lady's maid's maid. My queen lends her fog to the Grey Man as she lent her wind to Fuamnach. She lends. She never gives. Go home, little mortal. The forest is waiting for you.'"),
            end_talk('cm_gormlaith', "Tell Seer Gormlaith what Aoife said", "'My queen.' 'The forest.' 'As she lent her wind to Fuamnach' - that's Bri Leith's story.\n\nThere's only one forest in Hibernia with a queen in it, and nobody comes back from there. We're a long way from it here. But it isn't a long way from us.", 'default'),
        ],
        {'default': {'text': "From the Seers.", 'choice': [f3, f4]}},
        requires='cm_rift')

f5 = z.item('Hissing-Stone Torc', 'neck', 34, 'faith', "A sliver of the circle's stone, quiet again.")
f6 = z.item("Circle-Warden's Bracer", 'bracer', 34, 'ward', "Granite-grey, cut with the circle's ogham.")
z.quest('cm_fog_stone', 'The Hissing Stones', 34, 'cm_muadhan',
        "The stones of the circle are hissing. Someone has set a stone among them that doesn't belong - a fog-stone, I think, to anchor the Grey Man here.\n\nThe circle's guardians won't let anyone near. Will you [break the guardians]? Then find the stone that hisses.",
        'break the guardians',
        "Someone has set a fog-stone in the stone circle on the moor to anchor the Grey Man.",
        [
            hunt((515, 1040), "Break 3 vehement guardians at the stone circle, " + where((515, 1040), 'cm_muadhan'), 'vehement guardian', 3),
            search(Z, (520, 1045), "Find the stone that hisses (click the glinting spot)", "the fog-stone", CRATE,
                   "One stone isn't granite: it's grey-green, cold, wet, carved with a crown of thorns. Fog seeps out of it like breath.",
                   give='the fog-stone'),
            end_talk('cm_muadhan', "Bring the fog-stone to Seer Muadhan", "A crown of thorns. The Unseelie's mark, the old books say.\n\nWith this out of the circle, the Grey Man's thinner than he's been in a month. He'll be at his cairn, gathering himself. If you're going to face him, it's now.", 'default'),
        ],
        {'default': {'text': "From the Seers.", 'choice': [f5, f6]}},
        requires='cm_aoife')

f7 = z.item("Fear Liath's Grey Mantle", 'cloak', 35, 'mind', "The Grey Man's own mantle of fog, caught and woven. It's lighter than it should be.")
f8 = z.item('Clear-Weather Ring', 'ring', 35, 'faith', "Since you wore it, it hasn't rained on you once.")
f9 = z.item('Wrecker-Bane Torc', 'neck', 35, 'might', "Given to whoever ended the wrecking of the Cliffs of Moher.")
f10 = z.item('Thorn-Crown Charm', 'gem', 35, 'charm', "A chip of the fog-stone's thorn crown, cleansed. It still points east.")
z.quest('cm_grey_man', 'The Fear Liath', 35, 'cm_gormlaith',
        "The Grey Man is at his cairn on the cliff top above the coves, thin and angry, trying to pull his fog back together.\n\nThis is GROUP work - the hardest on the Cliffs. Bring the best you know. Will you [face the Grey Man]?",
        'face the Grey Man',
        "The Grey Man, the fog spirit who brings the Norse to the Cliffs, waits at his cairn.",
        [
            reach(Z, (395, 455), "Go to the Grey Man's cairn on the cliff top, " + where((395, 455), 'cm_gormlaith'),
                  "The fog is thin today, and you can see him: a tall grey shape, a man made of sea-fog, standing on the cairn with his back to you, looking east.", r=30),
            hunt((393, 461), "Defeat the Grey Man at his cairn", 'Grey Man', 1,
                 text="The Grey Man comes apart like fog in sunlight. Before he goes he says, quite calmly: 'She'll lend it to someone else. She always does. The Queen in the forest never runs short of fog.'"),
            choice('cm_gormlaith', "Return to Seer Gormlaith",
                   "The fog's lifting. For the first time in a month I can see the sea.\n\nThe Grey Man will gather again - he's the sea-fog, he can't not be. The Seers can [bind him] to the cairn with the fog-stone's own magic, so he serves this coast and warns us of ships. Or we [scatter him] to the open sea, and let him be an ordinary fog again, wrecking whoever he likes far from here.",
                   [('bind him', "Bound, then. A fog that warns of ships. My grandmother would be proud.", 'ending:bound'),
                    ('scatter him', "Scattered. Far out to sea. Gods help whoever sails there.", 'ending:scattered')]),
        ],
        {'bound': {'text': "Take these. From the Seers, and a coast that can see.", 'items': [f7], 'choice': [f8, f9, f10]},
         'scattered': {'text': "Take these. From the Seers, and a coast that can see.", 'items': [f7], 'choice': [f8, f9, f10]}},
        group=True, requires='cm_fog_stone')
