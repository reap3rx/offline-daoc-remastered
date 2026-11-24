"""The Cursed Forest's story quests (claude 2026-11-24, the zone brief in Zone Reviews and the owner's answers) - see story_gen.py.
Places: zone metres [x, y].

Moved out of story_hib.py with the zone's rebuild:
    python tools/claude-version/story_gen.py story_cursed_forest

The reveal of Hibernia's northern thread (decided 2026-11-23): the Unseelie Court, under Queen Cliodna, is behind the north's
troubles - the geas-bound miners of Silvermine, Connacht's revels, the haunting by Lough Derg, Fuamnach's wind and the changelings
in Bri Leith, the Grey Man's fog on the Cliffs of Moher - and all of it is aimed at one man: King Lug Lamfhota. The bainshees of
Cnoc Aine are already keening for him. Only the King's Host can reach her seat (King Lug's campaign: a General at Druim Cain).
Everything here is for level 45 and up; the forest is Elite.

Four arcs, 15 quests, from the Rangers' Hide on the west shelf (the only quiet ground in the forest):
  The Rangers' Hide (the Rangers, folded in: The Leprechauns' Cages, now the Queen's trappers),
  The Hags and the Suitors (beauty and what's under it), Whispers North (the reveal), The Old Blood (folded in: The
  Goat-Headed Fort - the court's bargain with the goborchend). One faction: the Host of Lug (kin to the realm's soldiers -
  the Rangers of Druim Cain among them).
"""
import math
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE, SATCHEL = 1882, 1876, 1347, 1347
M, F, OLD = 337, 365, 362
Z = 208
ZONES = []

z = Zone(Z, 'Cursed Forest', 3, 'hib_cursed_forest')
ZONES.append(z)

AT, NAMES = {}, {}

THRALL, SUITOR, HAG, WITCH, SIABRA = 60161227, 60166605, 60164285, 60164286, 60161305
BAIN, DOROCHA, MAID, ENVOY, DARK = 60158249, 60160718, 60165087, 60167452, 60167448
GASHER, WOUNDER = 60161461, 60161466
BAIN_MODEL = 1885


def person(id, name, xy, kind, level, **kw):
    NAMES[id] = name
    AT[id] = tuple(xy)
    z.npc(id, name, list(xy), kind, level, **kw)


def where(to, frm):
    """'about 240 m north-west of Ranger Teague' (y grows southward)."""
    fx, fy = AT[frm]
    dx, dy = to[0] - fx, to[1] - fy
    d = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(-dy, dx)) % 360
    names = ['east', 'north-east', 'north', 'north-west', 'west', 'south-west', 'south', 'south-east']
    dirn = names[int(((ang + 22.5) % 360) // 45)]
    dist = ('%d m' % (round(d / 10) * 10)) if d < 950 else ('%.1f km' % (d / 1000))
    return 'about %s %s of %s' % (dist, dirn, NAMES[frm])


def hunt(xy, goal, target, count=1, text=None, r=50):
    """Kill the zone's own monster (the zone build's named purples are the quests' named foes too: one of each, not two)."""
    st = {'type': 'kill', 'zone': Z, 'at': list(xy), 'radius': r, 'goal': goal, 'target': target, 'count': count}
    if text:
        st['text'] = text
    return st


# ------------------------------------------------------------------ people (the Rangers' Hide, on the west shelf)
person('teague', 'Ranger Teague', (160, 700), 'm', 52, guild='Rangers of Druim Cain',
       idle="You can't see twenty paces in this fog. That's the point of it. She doesn't want anyone seeing anything.")
person('druid_mor', 'Druid Mor', (166, 706), 'f', 56, guild='Rangers of Druim Cain',
       idle="The fog isn't weather. It's a glamour, laid over the whole forest. Somebody very old is holding it up.")
person('cf_ailbhe', 'Seer Ailbhe of the Host', (154, 694), 'f', 54, guild='the Host of Lug',
       idle="The King sent me to listen. Everything the court whispers, the trees whisper after it. If you know how to hear.")
person('cf_cormac', 'Cormac the Thrall', (172, 692), 'm', 40, model=OLD,
       idle="I was a miner in Silvermine. Then a lady smiled at me. That's all I remember until the rangers cut me loose.")
z.npc('seamus', 'Seamus the Leprechaun', [300, 860], 'm', 40, model=603, size=30, during=['leprechaun/seamus', 'leprechaun/gold'])
NAMES['seamus'] = 'Seamus the Leprechaun'
AT['seamus'] = (300, 860)
z.npc('oisin', 'Oisin the Druid', [912, 1392], 'm', 50, during=['goborchend/oisin'])
NAMES['oisin'] = 'Oisin the Druid'
AT['oisin'] = (912, 1392)
z.npc('cf_niall', 'Niall the Suitor', [520, 430], 'm', 46, model=446, during=['cf_grey_suitor/niall'])
NAMES['cf_niall'] = 'Niall the Suitor'
AT['cf_niall'] = (520, 430)

# ======================================================================== The Rangers' Hide (45 to 47) - Rangers / the Host
a1 = z.item("Fog-Walker's Belt", 'belt', 45, 'finesse', "Rangers' leather, with a rope knotted every pace: you count the knots to find your way back.")
a2 = z.item('Rowan-Thorn Charm', 'gem', 45, 'faith', "A rowan thorn in silver. The court's glamours slide off it.")
z.quest('cf_into_the_fog', 'Into the Fog', 45, 'teague',
        "So you came down off the shelf and lived. Good start. The Rangers have kept this hide for a month, and in a month we haven't seen the far side of the forest once.\n\nThe court's riders hunt the shelf at night. Will you [scout the shelf] with me? I want to know how many there are.",
        'scout the shelf',
        "The Rangers' Hide on the west shelf is all the Host has inside the Cursed Forest.",
        [
            reach(Z, (180, 980), "Scout the southern shelf, " + where((180, 980), 'teague'),
                  "Hoofprints in the moss - big ones, unshod, and they don't sink in. Whatever rides here weighs nothing at all.", r=25),
            kill(Z, (200, 900), "Drive off the far dorocha hunting the shelf", 'far dorocha', DOROCHA, [47, 48], 4,
                 text="The last rider comes apart into black mist as it falls. On its saddle-cloth: a woman's crowned head, stitched in green."),
            end_talk('teague', "Report to Ranger Teague", "A crowned woman, on the saddle-cloth. The court's riders have worn the Faerie Queen's colours a hundred years.\n\nBut the seer from the Host - Ailbhe - says it isn't the Faerie Queen any more. She says there's a new queen, and she wants a word with whoever came back from out there alive.", 'default'),
        ],
        {'default': {'text': "From the Rangers.", 'choice': [a1, a2]}})

a3 = z.item("Thrall-Breaker's Ring", 'ring', 46, 'might', "Cut from the iron collar of a geas-bound miner. He asked you to keep it.")
a4 = z.item('Unbound Bracer', 'bracer', 46, 'ward', "Plain iron, no rune on it. Cormac says that's the point.")
z.quest('cf_thralls', 'The Geas-Bound', 46, 'cf_cormac',
        "Those men the court has working the Hollow Road - the thralls with the dead eyes - they're miners. Silvermine men. Coruscating Mine. The same lady smiled at all of us.\n\nEach one wears a geas-token. Break the man and you break the token. Will you [free them]? It's the only way. I'm sorry.",
        'free them',
        "The court's thralls on the Hollow Road are geas-bound miners from Silvermine.",
        [
            kill(Z, (400, 1060), "Break 6 court thralls on the Hollow Road, " + where((400, 1060), 'cf_cormac'), 'court thrall', THRALL, [47, 48], 6,
                 text="Each one says a name as it dies - a real name, its own - and smiles, and is gone."),
            search(Z, (440, 1100), "Search the thralls' camp", "a heap of geas-tokens", CRATE,
                   "Clay tokens, each stamped with a woman's crowned head and a name. Dozens of names. You know one: the overman at the Coruscating Mine, who swore the unseelie came out of the deep on their own.", give='a geas-token'),
            end_talk('cf_cormac', "Bring the geas-token to Cormac", "That's the overman's. He sold us. Or she bought him - it comes to the same.\n\nSo it was never the mine that went wrong. It was her. All of it, her.", 'default'),
        ],
        {'default': {'text': "From Cormac.", 'choice': [a3, a4]}},
        requires='cf_into_the_fog')

it_gold = z.item('Crock-of-Gold Charm', 'gem', 46, 'charm', "A single gold coin from a leprechaun's crock. It's always there when you check.")
it_cage = z.item('Iron-Cage Bracer', 'bracer', 46, 'might', "Cold iron from a leprechaun cage. Fae folk flinch from it.")
it_poach = z.item("Trapper's Cloak", 'cloak', 46, 'finesse', "Dull green and very quiet. The Queen's trappers wore them.")
it_cobble = z.item("Cobbler's Ring", 'ring', 46, 'mind', "Leprechauns are cobblers, really. This is a ring of shoe-leather and silver tacks.")
z.quest('leprechaun', "The Leprechauns' Cages", 46, 'teague',
        "The court's trappers are catching leprechauns. Cages of cold iron, so the little folk can't vanish. The Queen keeps them in her hall - a caged leprechaun is luck, and she's buying all the luck in Hibernia.\n\nA caged leprechaun dies in a month. Will you [free them]? The trappers work the woods below the shelf.",
        'free them',
        "The Unseelie Queen's trappers are catching leprechauns in cold-iron cages.",
        [
            kill(Z, (300, 860), "Kill the Queen's trappers", "Queen's trapper", THRALL, [47, 48], 5),
            search(Z, (300, 860), "Search the trappers' camp", "a row of cold-iron cages", CRATE,
                   "Six cages. Five empty, the leprechauns already dead. In the last, a very small, very angry man in a green coat."),
            L('seamus', talk('seamus', 'Free the last leprechaun', "OUT. Get me OUT. ...Ahh. Thank you.\n\nSeamus is the name. The others - well. You saw. The trapper-chief has their gold, all five crocks - the Queen pays in it - hidden in the old cave to the west. He'll be back for me. Unless you get there [first].", kw='first')),
            kill(Z, (230, 720), "Drive the court's hounds from the cave", 'finliath', 60160859, [47, 48], 4,
                 text="In the cave: five crocks of gold, half-buried. And footsteps behind you."),
            boss(Z, (232, 724), "Defeat the trapper-chief", "Brannagh falls among the gold.",
                 'Brannagh the Trapper', THRALL, 49, "A big man with an iron net over his shoulder and a crowned head on his collar. 'The Queen pays in luck, stranger. Five crocks. Five little dead men. She'll want yours too.'",
                 objective='Defeat Brannagh', hp=2.6, adds=[(THRALL, "Queen's trapper", [47, 48])], every=25, count=2),
            L('gold', choice('seamus', 'Talk to Seamus',
                   "Five crocks. My cousins' gold.\n\nLeprechaun gold's for leprechauns. Without a leprechaun it goes back into the earth in a year and a day. But you could [take the gold] - all of it - and be rich for a year and a day. Fair's fair, you saved me.\n\nOr let me [bury it with them]. My cousins. They'd like that.",
                   [('take the gold', "Then it's yours, and good luck to you. Spend it fast. ...Mind, every coin you spend, somebody remembers who it belonged to.", 'next:gold'),
                    ('bury it with them', "...You're a strange one. Thank you. I'll sing them down. Go on back to Teague. I'll be along.", 'next:buried')])),
            L('gold', end_talk('teague', 'Return to Ranger Teague', "The trappers are done, and you came back with your pockets clinking.\n\nI won't ask. Seamus came by and said you'd earned it. He didn't look happy about it. Take this, from the rangers.", 'gold')),
            L('buried', end_talk('teague', 'Return to Ranger Teague', "The trappers are done. And Seamus came by and told me what you did with the gold.\n\nThe little folk will remember. That's worth more than gold, in this forest. Take this, from the rangers.", 'buried')),
        ],
        {'gold': {'text': "From the rangers.", 'items': [it_gold], 'choice': [it_cage, it_poach]},
         'buried': {'text': "From the rangers.", 'items': [it_cobble], 'choice': [it_cage, it_poach]}},
        requires='cf_into_the_fog')

a5 = z.item("Hide-Keeper's Torc", 'neck', 47, 'ward', "The Rangers' own torc, for whoever held the hide on a bad night.")
a6 = z.item('Black-Mist Charm', 'gem', 47, 'mind', "A wisp of a dorocha's mist, caught in glass. It's always trying to get out.")
z.quest('cf_riders', 'The Host of the Air', 47, 'teague',
        "Fear Dubh knows we're here. He's the court's huntsman - the black rider - and his dorocha are coming for the hide tonight. I can hear the horns.\n\nWill you [hold the hide] with us?",
        'hold the hide',
        "Fear Dubh's dorocha are coming for the Rangers' Hide.",
        [
            defend(Z, (160, 720), "Keep Ranger Teague alive at the hide", "The riders break off and go back into the fog. Somewhere east, a horn - not a hunting horn. A summons.",
                   'Ranger Teague', 60163820, 50, "Hooves that make no sound on the moss. The dorocha come out of the fog at a gallop.",
                   [(DOROCHA, 'far dorocha', [47, 48]), (60160859, 'finliath', [47, 48])], 'Keep Teague alive', model=M, duration=120, every=20, count=3),
            end_talk('teague', "Talk to Ranger Teague", "Held. Barely.\n\nThat horn at the end - that was the court calling them home. Something's happening at the Queen's Seat. Ailbhe will want to hear it.", 'default'),
        ],
        {'default': {'text': "From the Rangers.", 'choice': [a5, a6]}},
        requires='cf_into_the_fog')

# ======================================================================== The Hags and the Suitors (46 to 48) - the Host's seer
b1 = z.item("Suitor's Ring", 'ring', 46, 'charm', "A betrothal ring. The woman it was meant for never existed.")
b2 = z.item('Glass-Heart Charm', 'gem', 46, 'mind', "A heart of green glass. It beats, faintly, when someone lies to you.")
z.quest('cf_suitors', 'The Suitors', 46, 'cf_ailbhe',
        "In the glade to the north there are men who walk in circles. They came courting the Queen's maids - beautiful women, they say, the most beautiful in Hibernia - and they never left. Now they're spirits, and still courting.\n\nWill you [go to the glade]? I want to know who they were courting.",
        'go to the glade',
        "The suitor spirits in the north glade were lured into the forest by the Queen's maids.",
        [
            kill(Z, (500, 440), "Lay 5 suitor spirits to rest in the glade, " + where((500, 440), 'cf_ailbhe'), 'suitor spirit', SUITOR, [47, 48], 5,
                 text="Each says the same thing as it fades: 'Aoibhinn. Her name is Aoibhinn. Isn't she beautiful?'"),
            search(Z, (530, 410), "Search the glade's heart", "a mirror of black water", LANTERN,
                   "A pool, perfectly still. In it a woman of impossible beauty smiles at you - and as you watch, the smile stays and the face behind it rots to bone and leather. A hag. She was always a hag."),
            end_talk('cf_ailbhe', "Tell Seer Ailbhe what you saw", "A hag, under the beauty. All the Queen's maids are like that - the mummy hags of the barrows are what's under their glamour.\n\nLady Aoibhinn of the Thorns. I know that name. She's the Queen's own lady. The Queen's - not the Faerie Queen's. There's someone new on that seat.", 'default'),
        ],
        {'default': {'text': "From the Host.", 'choice': [b1, b2]}})

b3 = z.item("Barrow-Wight's Belt", 'belt', 47, 'might', "Bound with mummy-wrappings. Clean ones. Mostly.")
b4 = z.item("Hag-Bane Bracer", 'bracer', 47, 'faith', "Iron, with a hag-stone set in it: look through the hole and you see what's really there.")
z.quest('cf_barrows', 'Mother Carrion', 47, 'cf_ailbhe',
        "The hags have barrows in the south-west. Under the glamour they're dead things - mummies, wrapped, a thousand years old - and the oldest of them is Mother Carrion. The maids go to her to have their faces put back on.\n\nWill you [break the barrows]? Bring me a hag-stone if you find one - I'll show you what to do with it.",
        'break the barrows',
        "The Queen's maids are mummy hags under their glamour; Mother Carrion keeps the barrows.",
        [
            kill(Z, (600, 1300), "Break 6 mummy hags at the barrows, " + where((600, 1300), 'cf_ailbhe'), 'mummy hag', HAG, [47, 48], 6),
            search(Z, (620, 1330), "Search Mother Carrion's barrow", "a hag-stone on a thong", CRATE,
                   "A stone with a hole worn through it. Look through it at the barrows and they're full of lovely sleeping women. Look again without it: wrappings, and teeth.", give='a hag-stone'),
            end_talk('cf_ailbhe', "Bring the hag-stone to Seer Ailbhe", "Good. Look at me through it. ...Still me? Good.\n\nNow you can see the court as it is. Keep it. You'll need it at the Seat - if the Host ever gets you there.", 'default'),
        ],
        {'default': {'text': "From the Host.", 'choice': [b3, b4]}},
        requires='cf_suitors')

b5 = z.item("Unbetrothed Torc", 'neck', 48, 'charm', "Niall's betrothal torc, never given. He wanted someone to wear it.")
b6 = z.item("Grey Suitor's Cloak", 'cloak', 48, 'ward', "Mist-grey, and very old. It still smells of somebody's perfume.")
z.quest('cf_grey_suitor', 'The Grey Suitor', 48, 'cf_ailbhe',
        "The first suitor - the Grey Suitor - has been courting in that glade for three hundred years, and he keeps the others there. One of them still remembers he's alive: Niall, a lad from Druim Cain. He's half-spirit now.\n\nWill you [go for Niall]?",
        'go for Niall',
        "The Grey Suitor keeps the suitor spirits in the glade; one, Niall, is still half alive.",
        [
            L('niall', talk('cf_niall', "Find Niall in the glade, " + where((520, 430), 'cf_ailbhe'),
                            "You can see me? Nobody can see me. ...She's so beautiful. I know what she is. I still love her. The Grey Suitor says we all will, forever. He's [coming].", kw='coming')),
            hunt((520, 420), "Defeat the Grey Suitor in the glade (a tall grey man in three hundred years of finery, with his suitors round him)",
                 'The Grey Suitor', text="The Grey Suitor bows - courtly to the last - and fades. 'She'll come to us,' he says. 'One day she'll come.'"),
            choice('cf_niall', 'Talk to Niall',
                   "He's gone. They're all going quiet. I can feel it.\n\nI could [go home] - what's left of me - to Druim Cain. I'd be a ghost in my mother's house. Or I could [stay and watch] - here, where I can see her hall. Somebody should, when the Host comes. I'd tell you what I see.",
                   [('go home', "Home, then. Tell my mother I'm coming the long way.", 'ending:home'),
                    ('stay and watch', "Then I'll watch. When the Host comes to the Seat, I'll be in the trees. Look for me.", 'ending:watch')]),
        ],
        {'home': {'text': "From the Host.", 'items': [b5], 'choice': [b6]},
         'watch': {'text': "From the Host.", 'tragic': True, 'items': [b6], 'choice': [b5]}},
        requires='cf_barrows')

# ======================================================================== Whispers North (47 to 49) - the reveal
c1 = z.item("Envoy's Seal-Ring", 'ring', 47, 'mind', "The court's seal: a crowned woman. Every letter north was sealed with it.")
c2 = z.item("Courier's Bracer", 'bracer', 47, 'finesse', "A courier's arm-guard, slit for carrying letters.")
z.quest('cf_letters', 'Letters North', 47, 'cf_ailbhe',
        "The court sends envoys north - out of the forest, through Bri Leith, by night. One went into the Black Wraiths' ring with a satchel and didn't come out. The wraiths keep things.\n\nWill you [find the satchel]?",
        'find the satchel',
        "A court envoy's satchel was lost in the Black Wraiths' ring.",
        [
            kill(Z, (860, 400), "Break 5 black wraiths in the ring, " + where((860, 400), 'cf_ailbhe'), 'black wraith', 60158464, [47, 48], 5),
            search(Z, (870, 410), "Search the ring for the envoy's satchel", "a courier's satchel", CRATE,
                   "Letters, sealed with a crowned woman. To an overman at the Coruscating Mine: 'More hands.' To a Lord of Misrule in Connacht: 'Keep them dancing.' To Fuamnach, in Bri Leith: 'The wind, sister. The wind.' To the Grey Man of Moher: 'The fog is my gift. Use it.' Every one signed: C.", give="the court's letters"),
            end_talk('cf_ailbhe', "Bring the letters to Seer Ailbhe", "C.\n\nCliodna. The Queen of the Unseelie Court. She's moved her court here, into the Faerie Queen's old seat - and every trouble in the north in the last year is her hand.\n\nThe mines. The revels. The wind. The fog. It's all one thing, and it's all pointed south. At Tara. At the King.", 'default'),
        ],
        {'default': {'text': "From the Host.", 'choice': [c1, c2]}},
        requires='cf_suitors')

c3 = z.item("Siabra-Lord's Torc", 'neck', 48, 'might', "Elven silver, black with the court's tarnish. It was a gift from King Lug, once.")
c4 = z.item("Turncoat's Belt", 'belt', 48, 'finesse', "Lug's green on one side, the court's black on the other. Dorchu wore it either way.")
z.quest('cf_siabra', 'The Siabra-Lord', 48, 'cf_ailbhe',
        "The corrupted siabra in the south-east hollow were elves of the King's own court, once. Their lord, Dorchu, went over to Cliodna - and he knows the way to her seat.\n\nWill you [go to the hollow]? Bring me what he carries.",
        'go to the hollow',
        "Dorchu the Siabra-Lord, once of King Lug's court, went over to the Unseelie Queen.",
        [
            kill(Z, (1150, 1160), "Break 6 corrupted siabra in the hollow, " + where((1150, 1160), 'cf_ailbhe'), 'corrupted siabra', SIABRA, [47, 48], 6),
            hunt((1150, 1150), "Defeat Dorchu the Siabra-Lord in the heart of the hollow", 'Dorchu the Siabra-Lord',
                 text="Dorchu falls. 'Tell Lug,' he says. 'Tell him I was right. She's going to win.'"),
            search(Z, (1160, 1145), "Search Dorchu's body", "a folded map", CRATE,
                   "A map of the forest, in elven ink: the Hollow Road, the Ford, the Hag-Wood, the Thorn Gate - and past it, the Seat. Four strongholds between the King and the Queen.", give="Dorchu's map"),
            end_talk('cf_ailbhe', "Bring the map to Seer Ailbhe", "Four strongholds. That's what the Host would have to break, one by one, and hold, all the way in.\n\nGeneral Fergna at Druim Cain needs this. Not yet - there's one more thing I need to know first. The bainshees.", 'default'),
        ],
        {'default': {'text': "From the Host.", 'choice': [c3, c4]}},
        requires='cf_letters')

c5 = z.item("Keener's Veil", 'cloak', 49, 'faith', "Grey as ash. Wear it and the bainshees' wail is only a sound.")
c6 = z.item('Cnoc Aine Charm', 'gem', 49, 'mind', "A pebble from the bainshees' hill. It's cold, and it hums one note.")
z.quest('cf_keener', 'The Keening', 49, 'cf_ailbhe',
        "A bainshee keens for one family's dead before they die. On Cnoc Aine, the hill to the north-east, they're keening every night - all of them, together - and the Keener leads them.\n\nI need to hear whose name they're keening. Will you [take me up the hill]?",
        'take me up the hill',
        "On Cnoc Aine the bainshees keen every night for someone who hasn't died yet.",
        [
            kill(Z, (1170, 400), "Clear the bainshees from the slopes of Cnoc Aine, " + where((1170, 400), 'cf_ailbhe'), 'bainshee', BAIN, [48, 49], 5, model=BAIN_MODEL),
            defend(Z, (1180, 380), "Keep Seer Ailbhe alive while she listens", "The keening stops. In the silence, Ailbhe says the name. Then she says it again, because she can't believe it.",
                   'Seer Ailbhe', 60163820, 52, "Ailbhe kneels on the hilltop and closes her eyes. The bainshees come out of the fog, wailing.",
                   [(BAIN, 'bainshee', [48, 49])], 'Keep Ailbhe alive', model=F, duration=120, every=20, count=3),
            hunt((1180, 380), "Silence the Keener of Cnoc Aine on the hilltop", 'The Keener of Cnoc Aine',
                 text="The Keener falls silent at last - and for the first time in a month, the hill is quiet."),
            end_talk('cf_ailbhe', "Talk to Seer Ailbhe", "Lug.\n\nThey're keening Lug Lamfhota. The King. Every bainshee in the forest, every night.\n\nA bainshee never keens wrong. Unless someone is making the keening true - and that's what all of it is for. The mines, the revels, the fog: the court is breaking the north so the King has to come north himself. Into her forest. To his death.", 'default'),
        ],
        {'default': {'text': "From the Host.", 'choice': [c5, c6]}},
        requires='cf_siabra')

c7 = z.item("Thorn-Lady's Brooch", 'gem', 50, 'charm', "A brooch of black thorns. Lady Aoibhinn wore it over her heart, where the hag's heart was.")
c8 = z.item("Lug's Promise", 'ring', 50, 'might', "A plain gold ring from the King's own treasury: given to those who carried the word of the plot to Tara.")
c9 = z.item('Mantle of the Watchful', 'cloak', 50, 'ward', "The Host's green, for the ones who saw it coming.")
z.quest('cf_lady_aoibhinn', 'The Lady of the Thorns', 50, 'cf_ailbhe',
        "This is GROUP work, and hard.\n\nLady Aoibhinn of the Thorns is the Queen's own lady. She stands at the Seat, in front of Cliodna's chair, and she knows the whole of it. I want her answer - and I want the court to know we're coming.\n\nWill you [go to the Seat]? Take the hag-stone. Look at her through it.",
        'go to the Seat',
        "GROUP. Lady Aoibhinn of the Thorns, the Unseelie Queen's own lady, knows the whole of the court's plot.",
        [
            reach(Z, (1290, 650), "Go to the edge of the Queen's Seat, " + where((1290, 650), 'cf_ailbhe'),
                  "An empty chair of black thorn on a mound of white stones, and in front of it, a lady in green so beautiful your eyes water. Through the hag-stone: a mummy, smiling.", r=25),
            hunt((1320, 645), "Defeat Lady Aoibhinn of the Thorns before the Queen's chair", 'Lady Aoibhinn of the Thorns',
                 text="'The Queen is out walking,' Lady Aoibhinn says as she falls into her wrappings and her bones. 'She'll be sorry she missed you.' The chair behind her is empty - but it's warm."),
            choice('cf_ailbhe', 'Return to Seer Ailbhe',
                   "She's dead, and the chair was empty, and warm. Cliodna knows we know.\n\nThere's only one way to that chair with her in it: the King's Host, stronghold by stronghold, the way Dorchu's map shows. General Fergna is at Druim Cain. Any champion of the realm can give him the word.\n\nI'm going to Tara myself, to tell the King to his face not to come north. Will you [carry the map] to the General, so the Host can march? Or [come to Tara] with me, and tell the King what you saw?",
                   [('carry the map', "Then go. Druim Cain, the General. And when the Host goes in - go with it.", 'ending:host'),
                    ('come to Tara', "Then we'll ride tonight. The King should hear it from someone who's seen her chair.", 'ending:tara')]),
        ],
        {'host': {'text': "From the Host.", 'items': [c9], 'choice': [c7, c8]},
         'tara': {'text': "From the King's own hand.", 'items': [c8], 'choice': [c7, c9]}},
        group=True, requires='cf_keener')

# ======================================================================== The Old Blood (48 to 50) - Druid Mor
d1 = z.item("Fomor-Rune Bracer", 'bracer', 48, 'mind', "Copied runes, burned into leather. Mor says they're harmless copied. Mor says.")
d2 = z.item('Goat-Skull Charm', 'gem', 48, 'might', "A goborchend's little skull-charm. It bleats at night.")
z.quest('cf_old_runes', 'The Old Runes', 48, 'druid_mor',
        "The goborchend in the south have been quiet a hundred years. Now they're carving runes - Fomorian runes, the old blood's - on every tree round their fort. Someone taught them. Someone reminded them what they are.\n\nWill you [copy the runes] for me?",
        'copy the runes',
        "The goborchend have begun carving Fomorian runes round their fort in the south.",
        [
            kill(Z, (880, 1360), "Break the goborchend guarding the carved trees", 'goborchend gasher', GASHER, [48, 49], 4),
            search(Z, (870, 1340), "Copy the runes on the oldest tree", "runes cut into an oak", LANTERN,
                   "An eye, closed - and beside it, fresh-cut, a crowned woman's head. The goborchend's runes are old. The crown is new.", give='a rubbing of the runes'),
            end_talk('druid_mor', "Bring the rubbing to Druid Mor", "A closed eye. The Fomorian eye - Balor's kind. And the Queen's crown beside it.\n\nShe's made a bargain with them. Their eye for her war. Gods help us. They'll want a druid's blood for the waking - and my brother Oisin went south yesterday to look.", 'default'),
        ],
        {'default': {'text': "From the druids.", 'choice': [d1, d2]}})

it_horn3 = z.item('Goborchend Horn Torc', 'neck', 50, 'might', "Twisted goat-horn, bound in bronze. The goborchend wear their horns as trophies; you wear theirs.")
it_bloodstone = z.item("Bloodhorn's Altar-Stone", 'gem', 50, 'mind', "A chip from a goborchend altar. Druid Mor cleansed it. It's still red.")
it_oisin = z.item("Oisin's Druid-Cloak", 'cloak', 50, 'faith', "Green and brown and full of pockets.")
it_fomor = z.item('Fomorian-Bone Bracer', 'bracer', 50, 'ward', "The goborchend are of the old Fomorian blood. Their bones are heavy and hard.")
it_fort = z.item("Fort-Breaker's Ring", 'ring', 50, 'finesse', "Given to whoever first broke into a goborchend fort.")
z.quest('goborchend', 'The Goat-Headed Fort', 50, 'druid_mor',
        "This is GROUP work, and hard. Bring the best you know.\n\nThe goborchend have Oisin. At the dark of the moon they'll pour his blood on their altar to wake the eye - the Queen's bargain, paid in my brother.\n\nWill you [go after Oisin]?",
        'go after Oisin',
        "GROUP. The goborchend have captured a druid to wake a Fomorian eye - the Unseelie Queen's bargain.",
        [
            reach(Z, (880, 1360), "Go to the goborchend fort in the south", "Goat-skulls on poles. A wall of black stone. Inside, chanting, low and terrible - and a woman's voice, sweet as honey, joining in.", r=20),
            kill(Z, (904, 1425), 'Break the goborchend gashers on the wall', 'goborchend gasher', GASHER, [48, 49], 5),
            kill(Z, (895, 1402), 'Cut down the goborchend wounders in the yard', 'goborchend wounder', WOUNDER, [49, 50], 4),
            search(Z, (920, 1395), "Search the fort's altar", "a blood-stained altar", CRATE,
                   "The altar's carved with Fomorian runes, and a crown. An eye, a huge closed eye - and a crowned woman holding the lid."),
            boss(Z, (912, 1392), 'Defeat Bloodhorn before the rite', "Bloodhorn falls across his own altar. Under it, something huge and old stops stirring.",
                 'Bloodhorn, Goborchend Chieftain', WOUNDER, 52, "A goborchend twice the height of the others, horns dripping. 'The Queen promised us the eye. The druid's blood opens it. Your blood will do as well.'",
                 objective='Defeat Bloodhorn', hp=3.2, adds=[(GASHER, 'goborchend gasher', [48, 49])], every=25, count=2),
            L('oisin', talk('oisin', 'Free Oisin', "Mor sent you? Of course. She's the clever one.\n\nThe eye - they were trying to open a Fomorian eye, under the fort. Asleep. The Queen wanted it open and looking south. Mor needs to know. She'll need to choose what to [do] about it.", kw='do')),
            choice('druid_mor', 'Return to Druid Mor',
                   "Oisin's alive. Thank every god.\n\nAnd under the fort - an eye. Oisin says it can be [sealed] forever - the druids' great rite, and it will cost me most of my power. Or [left sleeping], and watched, and studied - and perhaps turned on the Queen, one day. The Council would like that. I wouldn't.",
                   [('sealed', "Then I'll seal it. Tomorrow. Oisin will help. ...I'll be a hedge-druid after, curing warts. I think I'll like it.", 'ending:sealed'),
                    ('left sleeping', "Watched, then. Studied. Gods help us if anyone ever wakes it on purpose.", 'ending:watched')]),
        ],
        {'sealed': {'text': "From the druids.", 'items': [it_oisin], 'choice': [it_horn3, it_fomor, it_fort]},
         'watched': {'text': "From the druids.", 'tragic': True, 'items': [it_bloodstone], 'choice': [it_horn3, it_fomor, it_fort]}},
        group=True, requires='cf_old_runes')

d3 = z.item("Rider's-Bane Torc", 'neck', 49, 'ward', "Fear Dubh's bridle-iron, twisted into a torc.")
d4 = z.item("Huntsman's Horn Charm", 'gem', 49, 'finesse', "A sliver of Fear Dubh's horn. Blow it and the court's hounds flinch.")
z.quest('cf_fear_dubh', 'The Black Rider', 49, 'teague',
        "Fear Dubh rides out from the Ford every night and every night he comes closer to the hide. The Host can't march in while he hunts the shelf.\n\nWill you [ride him down]? He keeps to the woods south-east of the Ford. Bring friends - he doesn't hunt alone.",
        'ride him down',
        "Fear Dubh, the court's black huntsman, hunts the Rangers from the Ford of Sorrows.",
        [
            kill(Z, (780, 1040), "Break the court's riders on the way to the Ford, " + where((780, 1040), 'teague'), 'far dorocha', DOROCHA, [48, 49], 4),
            hunt((840, 1080), "Defeat Fear Dubh, the black rider, south-east of the Ford", 'Fear Dubh', r=120,
                 text="Fear Dubh's horse goes out from under him like smoke, and he follows it."),
            end_talk('teague', "Report to Ranger Teague", "The black rider's down. For tonight, anyway - nothing of hers stays dead long in this fog.\n\nBut the shelf's ours. When the Host comes through the Forest Gate, it'll have a road to the Hollow Road. That's your doing.", 'default'),
        ],
        {'default': {'text': "From the Rangers.", 'choice': [d3, d4]}},
        requires='cf_riders')

if __name__ == '__main__':
    print(z.check() if hasattr(z, 'check') else 'ok')
