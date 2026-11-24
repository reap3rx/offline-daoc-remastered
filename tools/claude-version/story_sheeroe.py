"""The Sheeroe Hills' story quests (claude 2026-11-24, the zone brief in Zone Reviews and the owner's answers) - see story_gen.py.
Places: zone metres [x, y].

Moved out of story_hib.py with the zone's rebuild (its two quests kept, by id):
    python tools/claude-version/story_gen.py story_sheeroe

The south's thread ends here. Lough Gur's lights, the Bog's tower and its lantern-bearer were all Cuuldurach's - the Glimmer King,
the dragon in his ring of stones. The Southern Muster (the Sentinels, Aine's Circle, the Clann and the Keeners under one banner)
has gathered at the Healers' Camp to push into the hills (MusterCampaign.cs). The stories run beside the campaign: what the Glimmer
does to the people it touches, the Azure's last ground (and the young captain who'll stand with the Muster), the Glimmer lords, and
the King's answer to Cliodna's letter (found on the envoy in Lough Gur: "The north for me, the south for you, and Lug between us").
The answer closes the threat (owner: "a somewhat open ending that we can use later if we need, but still being satisfying that you
ended the threat for now"): the bargain is broken - Lug's Host holds Cliodna's forest, the Muster holds the King's hills - but the
King's letter names a third party both of them feared: the Fomorian Eye the goborchend were waking in the Cursed Forest.

Arcs (recommended levels; rewards pay at the player's level; everything from the Healers' Camp):
  The Healers' Camp (45-46; folded in: Elfshot) - the touched, and why the Glimmer wants them
  The Azure's Last Ground (46-48; folded in: The Cleansed Village, GROUP) - Elder Cnoc, the pale horses, Captain Ailill
  The Glimmer Lords (47-49, the Sentinels; GROUP finale: Venlar) - the King's captains, and the army they were raising
  The King's Answer (49-50, Aine's Circle; GROUP: Saumer at the ring) - Cuuldurach's reply to Cliodna
"""
import math
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

CRATE, BEDROLL, LANTERN = 1347, 1882, 1876
M, F, OLD = 337, 365, 362
Z = 216
ZONES = []

z = Zone(Z, 'Sheeroe Hills', 3, 'hib_sheeroe')
ZONES.append(z)
AT, NAMES = {}, {}

MADMAN, SUBVERTER, PALE_HORSE = 60160411, 60165127, 60164831
GLIMMERLING, GLIM_WARD, GLIM_GHOUL, GLIM_GRIEVER, GLIM_STRIKER, GLIM_WARSHADE = 60161430, 60161424, 60161408, 60161409, 60161421, 60161425
GLIM_ARDENT, GLIM_KNIGHT, DEATHWATCHER, GEIST = 60161402, 60161412, 621, 622
AVENGER, BANISHER, CLEANSER = 60158171, 60158172, 60158173
SENTINEL = 60165769
LURIKEEN = 603


def person(id, name, xy, kind, level, **kw):
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
    st = {'type': 'kill', 'zone': Z, 'at': list(xy), 'radius': r, 'goal': goal, 'target': target, 'count': count}
    if text:
        st['text'] = text
    return st


# ------------------------------------------------------------------ people (the Healers' Camp, now the Muster's war camp)
person('bebhinn', 'Healer Bebhinn', (140, 905), 'f', 46, guild="Healers' Camp",
       idle="Elfshot. Every one of them. The glimmer folk's arrows don't kill - they do worse.")
person('lochlann', 'Lochlann', (143, 910), 'm', 44, guild="Healers' Camp", idle="(He stares at nothing and hums the same four notes, over and over.)")
person('elder_cnoc', 'Elder Cnoc', (160, 915), 'm', 52, model=LURIKEEN, size=35, guild='Lurikeen Exiles',
       idle="The Azure took our village in the north. They say they're cleansing it. Of us.")
z.npc('cnoc_village', 'Elder Cnoc', [692, 96], 'm', 52, model=LURIKEEN, size=35, during=['azure_village/home'])
person('sr_maeve', 'Sentinel-Captain Maeve', (145, 880), 'f', 50, guild='the Sentinels of Ceannai',
       idle="I followed the lights from Lough Gur to the bog, and the bog to here. This is where they come from. This is where they stop.")
person('sr_ceallach', 'Druid Ceallach', (155, 890), 'm', 50, guild="Aine's Circle",
       idle="On the lake we thought the lights were Aine. Here you can see what they really are. Look at them long enough and they look back.")
person('sr_ailill', 'Ailill of the Azure', (132, 888), 'm', 46, model=354, guild='the Order of the Azure (a prisoner of the Muster)',
       idle="Go on. Stare. A crusader in a camp full of the touched. They've fed me better than the Order ever did.")

# ======================================================================== The Healers' Camp (45-46)
it_arrow = z.item('Glimmer-Arrow Pendant', 'neck', 45, 'mind', "A glimmer-glass arrowhead. It points toward the Glimmer King's hosts, wherever they are.")
it_elfshot = z.item("Elfshot Ward", 'gem', 45, 'faith', "A healer's charm against the glimmer folk's arrows.")
it_madman = z.item("Madman's Bracer", 'bracer', 45, 'might', "An elfshot man made this, in his madness. It's very good.")
it_glimmer = z.item("Glimmerling Cloak", 'cloak', 45, 'finesse', "It catches the light and throws it back wrong.")
z.quest('elfshot', 'Elfshot', 45, 'bebhinn',
        "My husband Lochlann was elfshot - struck by a glimmer folk arrow. It doesn't kill. It takes the mind and leaves the man. He hums. That's all.\n\nThe arrows are glimmer-glass. If I had the arrowhead that struck him - the archer's own - I could draw the madness out. Will you [find the archer]? The madmen of the valley all took his arrows.",
        'find the archer',
        "Healer Bebhinn's husband was elfshot by a glimmer archer. With the archer's own arrowhead, she could cure him.",
        [
            kill(Z, (160, 700), "Put the elfshot madmen to rest " + where((160, 700), 'bebhinn'), 'elfshot madman', MADMAN, [45, 46], 5,
                 text="Each one has a glimmer-glass splinter in him. Each splinter points the same way - south, down the valley."),
            search(Z, (165, 712), "Search the madmen's camp", "a glimmer-glass arrowhead", CRATE,
                   "A spent arrowhead, glowing faintly. It tugs southward like a lodestone, down the valley toward the glimmerlings."),
            kill(Z, (180, 1100), "Hunt down the glimmerlings down the valley " + where((180, 1100), 'bebhinn'), 'glimmerling', GLIMMERLING, [45, 46], 5),
            boss(Z, (200, 1150), 'Defeat the glimmer archer', "The archer shatters like a dropped lamp. Among the shards, an arrowhead brighter than the rest.",
                 'Glimmer Archer Saoth', GLIM_WARD, 47, "A tall figure of glimmering glass draws a bow of light. 'More madmen for the King's hills.'",
                 objective='Defeat the Glimmer Archer', hp=2.8, adds=[(GLIMMERLING, 'glimmerling', [45, 46])], every=25, count=2),
            choice('bebhinn', "Bring the archer's arrowhead to Bebhinn",
                   "That's it. The archer's own. I can feel it pulling.\n\nI can [break the arrow] in a healing rite, and draw the madness out of Lochlann. The arrowhead will be gone.\n\nOr - the Muster's captains say an archer's arrowhead points to the Glimmer King's hosts wherever they march. It could save hundreds. They'd want me to [keep it] for them. And Lochlann would hum forever.",
                   [('break the arrow', "Then I'll do it now. ...Lochlann? Lochlann. Look at me. ...He's looking at me.", 'ending:healed'),
                    ('keep it', "...The Muster will have it by morning. I'll sing his four notes with him. He likes it when I do.", 'ending:kept')]),
        ],
        {'healed': {'text': "Take this. Lochlann wants you to have it - he says so. He SAYS so.", 'items': [it_elfshot], 'choice': [it_madman, it_glimmer]},
         'kept': {'text': "Take this.", 'tragic': True, 'items': [it_arrow], 'choice': [it_madman, it_glimmer]}})

h1 = z.item("Subverter's Glass Ring", 'ring', 45, 'mind', "A ring of glimmer-glass, taken from a raging subverter's hand. It hums, faintly.")
h2 = z.item("Healer's Knotted Belt", 'belt', 45, 'ward', "Every knot a patient. Bebhinn ran out of rope.")
z.quest('sh_subverters', 'The Raging', 45, 'bebhinn',
        "Not all of them only hum. Some of the elfshot - the ones struck twice, three times - go wild. Raging. They come down the valley at night and they don't stop, not for steel, not for fire.\n\nThe odd thing: they never come for the camp. They walk past it. South-east, always south-east. Will you [stop the raging] and find out what drives them?",
        'stop the raging',
        "Raging subverters walk past the Healers' Camp at night, always south-east.",
        [
            kill(Z, (250, 1080), "Stop the raging subverters on the valley floor " + where((250, 1080), 'bebhinn'), 'raging subverter', SUBVERTER, [45, 46], 5,
                 text="Every one of them has a glimmer-glass splinter behind the eyes - and every splinter is warm."),
            search(Z, (255, 1085), "Search where the subverters fell", "a cluster of warm glimmer-glass", CRATE,
                   "Splinters of glimmer-glass, and inside each, very faint, a light - as if the madness were burning in there like oil in a lamp."),
            end_talk('bebhinn', "Bring the glass to Healer Bebhinn",
                     "Lamps. Gods help us. They aren't madmen - they're lamps. Every mind the Glimmer takes, it burns. And they walk south-east so they can burn where he wants them.\n\nCeallach of the Circle came down from Lough Gur with the Muster. He says he's heard Lochlann's four notes before - on the lake. Talk to him.",
                     'default'),
        ],
        {'default': {'text': "From the Healers' Camp.", 'choice': [h1, h2]}},
        requires='elfshot')

h3 = z.item("Four-Note Torc", 'neck', 46, 'faith', "Ceallach strung a bead for every note of the King's call, and broke the last one.")
h4 = z.item("Counter-Song Charm", 'gem', 46, 'charm', "A druid's charm, sung over. It hums a fifth note, out of tune with the four.")
z.quest('sh_four_notes', 'Four Notes', 46, 'sr_ceallach',
        "Lochlann's four notes. I heard them on Lough Gur, from the lights over the crannog. It's a call - the Glimmer King's call - and the touched walk to it.\n\nA call can be answered with another song. I can sing one - a counter-song, the Circle's - out on the west ridge where the touched walk. But the Glimmer will hear me singing, and come. Will you [guard the song]?",
        'guard the song',
        "The Glimmer King's call is four notes - and Druid Ceallach can sing a counter-song on the west ridge.",
        [
            reach(Z, (420, 620), "Go out onto the west ridge " + where((420, 620), 'sr_ceallach'),
                  "The valley glows. Far off, a line of the touched walks south-east, humming, in step.", r=25),
            defend(Z, (420, 620), "Keep Ceallach alive while he sings the counter-song",
                   "The counter-song ends on a fifth note, out of tune with the four. Along the ridge the walking touched stop - and one by one they sit down in the grass, and weep, and are themselves.",
                   'Druid Ceallach', SENTINEL, 50, "Ceallach begins to sing. Every light in the valley turns toward him.",
                   [(GLIM_WARD, 'glimmer ward', [46, 47]), (GLIM_ARDENT, 'glimmer ardent', [46, 47])], 'Keep Ceallach alive',
                   model=M, duration=150, every=22, count=3),
            end_talk('sr_ceallach', "Walk back to the camp with Druid Ceallach",
                     "It works. Not for long, and not for all - but it works. The call can be broken.\n\nSo he can be fought. That's what the Muster needed to hear. Maeve will want you - she's been reading what the Glimmer's captains carry.",
                     'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [h3, h4]}},
        requires='sh_subverters')

# ======================================================================== The Azure's Last Ground (46-48) - Elder Cnoc, Ailill
it_lurikeen = z.item('Lurikeen Hearth-Charm', 'gem', 47, 'charm', "A little clay figure of a hearth, made by lurikeen children.")
it_cleanse = z.item("Cleanser's Torc", 'neck', 47, 'mind', "An Azure cleanser's torc. Every link has a name scratched into it - the names of the cleansed.")
it_pale = z.item('Pale Horse Bracer', 'bracer', 47, 'might', "Leather from a pale horse of the hills. It never quite warms.")
it_exile = z.item("Exile's Cloak", 'cloak', 47, 'ward', "Grey and patched. Cnoc wore it for a year.")
it_ledger2 = z.item("Inquisitor's Ring", 'ring', 47, 'finesse', "Taken from the Azure inquisitor who held the village.")
z.quest('azure_village', 'The Cleansed Village', 47, 'elder_cnoc',
        "This is GROUP work. The Azure Order are many, and they don't fear death.\n\nThey took our village in the northern hills. 'Cleansing', they call it. Of fae blood. Of us. We fled with what we could carry. Some didn't flee fast enough.\n\nWill you [take back the village]? Some of ours may still be alive inside.",
        'take back the village',
        "GROUP. The Azure Order took a lurikeen village in the northern hills to 'cleanse' it.",
        [
            reach(Z, (690, 210), "Go to the lurikeen village in the north " + where((690, 210), 'elder_cnoc'),
                  "Lurikeen huts, painted over with blue sigils. Azure cleansers walk between them with censers, chanting.", r=20),
            kill(Z, (700, 220), 'Drive out the azure cleansers', 'azure cleanser', CLEANSER, [47, 48], 5),
            search(Z, (690, 100), "Search the elder's hut", "an Azure ledger", CRATE,
                   "A ledger of names: lurikeen, and beside each, 'cleansed' - or 'held'. Seven names say 'held'. The pale horses carry them east, to the pastures.",
                   give='the Azure ledger'),
            kill(Z, (1380, 200), 'Kill the pale horses that carry the prisoners east', 'pale horse', PALE_HORSE, [48, 49], 4),
            boss(Z, (700, 215), 'Defeat the Azure inquisitor', "The inquisitor falls. From a locked hut, seven small voices start calling all at once.",
                 'Inquisitor Cathal of the Azure', BANISHER, 50, "An Azure banisher in a mask of blue glass. 'The fae taint must be cleansed. All of it. Including whoever shelters it.'",
                 objective='Defeat the Inquisitor', hp=3.2, adds=[(CLEANSER, 'azure cleanser', [47, 48])], every=25, count=2),
            L('home', choice('cnoc_village', 'Speak with Elder Cnoc in the village',
                   "Seven. Seven of ours alive. And the village is ours again.\n\nBut the Azure will come back. They always come back. We could [rebuild] here - make walls, and fight. Or we could [go west], to the Valley of Bri Leith, and start again where the Azure don't go. The village will be empty. My grandfather built that hut.",
                   [('rebuild', "Then we rebuild. Walls first. And this time, a watch-tower. Thank you. The lurikeen of Sheeroe will not forget.", 'ending:rebuild'),
                    ('go west', "West, then. We'll take what we can carry. Again. ...But together, this time. All of us.", 'ending:west')])),
        ],
        {'rebuild': {'text': "From the village.", 'items': [it_lurikeen], 'choice': [it_cleanse, it_pale, it_ledger2]},
         'west': {'text': "Take this. I won't need it in the west.", 'tragic': True, 'items': [it_exile], 'choice': [it_cleanse, it_pale, it_ledger2]}},
        group=True)

a1 = z.item("Pale Pasture Halter-Ring", 'ring', 46, 'finesse', "From a pale horse's halter. Lurikeen-sized.")
a2 = z.item("Pen-Breaker's Bracer", 'bracer', 46, 'might', "The pen's bar, beaten into a bracer by a grateful smith.")
z.quest('sh_pale_pastures', 'The Pale Pastures', 46, 'elder_cnoc',
        "The ledger said 'held'. Held where? I sent my grandson to follow the pale horses. He came back. He says there's a pen in the pastures in the north-east, and more of ours in it than the ledger knew - and they're not only ours. Touched men, from this valley.\n\nThe Azure keep them to burn. Will you [break the pen]?",
        'break the pen',
        "The Azure keep lurikeen and touched folk in a pen in the Pale Pastures, to burn.",
        [
            kill(Z, (1380, 200), "Kill the pale horses guarding the pen " + where((1380, 200), 'elder_cnoc'), 'pale horse', PALE_HORSE, [46, 47], 4),
            search(Z, (1400, 215), "Break open the pen", "a pen of blue-painted stakes", CRATE,
                   "The bar comes off. Lurikeen, and two touched men humming four notes, and a list nailed to the post: 'For the pyres of the Azure March, when the Inquisitor gives the word.'"),
            defend(Z, (1400, 215), "Keep the freed prisoners' guide alive while they get clear",
                   "The last of the prisoners slips over the ridge and away west, toward the camp.",
                   'Cnoc\'s grandson Dorc', SENTINEL, 40, "Azure banishers come over the ridge with torches.",
                   [(BANISHER, 'azure banisher', [46, 47]), (CLEANSER, 'azure cleanser', [46, 47])], 'Keep Dorc alive',
                   model=LURIKEEN, duration=120, every=22, count=3),
            end_talk('elder_cnoc', "Report to Elder Cnoc",
                     "All of them home. All of them.\n\n'When the Inquisitor gives the word.' There's an Azure man in this camp - the Muster caught him on the march. Ailill. He's been asking to talk to whoever broke that pen. I'd rather spit on him. But talk to him.",
                     'default'),
        ],
        {'default': {'text': "From the lurikeen exiles.", 'choice': [a1, a2]}},
        requires='azure_village')

a3 = z.item("Doubter's Blue Torc", 'neck', 47, 'faith', "Ailill's own torc, the crown crossed out. He gave it up.")
a4 = z.item("Pitch-Cart Belt", 'belt', 47, 'ward', "Leather from the Inquisitor's pitch-carts. Smells of smoke.")
z.quest('sh_young_captain', 'The Young Captain', 47, 'sr_ailill',
        "You broke the pen. Good. I mean that.\n\nI was a captain on the march. The Grand Inquisitor has decided the touched are the Glimmer's lamps - which they are - and so the Healers' Valley must burn, with every madman in it, and the healers too if they won't leave. The pitch-carts are already on the ridge road. I said no. That's why I'm here.\n\nWill you [stop the carts]? I'll tell you where they are. I can't go myself - nobody here would let me, and they'd be right.",
        'stop the carts',
        "Ailill of the Azure says the Grand Inquisitor means to burn the Healers' Valley, touched folk and all.",
        [
            kill(Z, (560, 560), "Kill the Azure banishers with the pitch-carts on the ridge road " + where((560, 560), 'sr_ailill'), 'azure banisher', BANISHER, [47, 48], 5),
            search(Z, (565, 565), "Search the pitch-carts", "an order in the Grand Inquisitor's hand", CRATE,
                   "'Burn the valley from the ridge down. Then the Muster's camp, with whatever is in it. The Glimmer will have no lamps, and the south no friends of the fae. - the Grand Inquisitor.'",
                   give="the Inquisitor's order"),
            end_talk('sr_ailill', "Bring the order to Ailill",
                     "\"The Muster's camp, with whatever is in it.\" He'd have burned me with you.\n\nListen. The Order is wrong. I know that now. But the Glimmer King is still the enemy, and he's still in his ring. When the Muster takes the march and the Inquisitor falls - and he will fall to you - I'll gather whoever will follow me. Not the Order. Just the ones who came here to fight the Glimmer and still want to. When you go for the King, we go with you.",
                     'default'),
        ],
        {'default': {'text': "From Ailill.", 'choice': [a3, a4]}},
        requires='sh_pale_pastures')

a5 = z.item("Dsaldor's Enamel Bracer", 'bracer', 48, 'might', "Blue enamel, the crown crossed out. Dsaldor's own.")
a6 = z.item("Coseal's Censer Ring", 'ring', 48, 'mind', "A tiny censer on a ring. It still smokes, faintly.")
a7 = z.item("Thror's Pyre-Cloak", 'cloak', 48, 'ward', "Singed at the hem from a hundred pyres.")
z.quest('sh_azure_captains', "The Inquisitor's Captains", 48, 'elder_cnoc',
        "GROUP work. Ailill says the Inquisitor's three captains - Dsaldor, Coseal and Thror - are the ones who light the pyres. Without them the Order can only preach.\n\nThey hold the march with the Inquisitor. Will you [break the captains]? Bring friends. Lots of friends.",
        'break the captains',
        "GROUP. The Grand Inquisitor's three captains, Dsaldor, Coseal and Thror, light the Azure's pyres.",
        [
            hunt((756, 476), "Defeat Azure Dsaldor on the march " + where((756, 476), 'elder_cnoc'), 'Azure Dsaldor'),
            hunt((1076, 506), "Defeat Azure Thror", 'Azure Thror'),
            hunt((1197, 493), "Defeat Azure Coseal", 'Azure Coseal',
                 text="Coseal falls among his censers. 'Ailill,' he says. 'Ailill told you. Tell the boy - the Inquisitor will burn him first.'"),
            end_talk('elder_cnoc', "Report to Elder Cnoc",
                     "Three pyre-lighters gone. The lurikeen of the north will sleep tonight.\n\nThe Inquisitor's still on the march, with his pyres. That's for the whole Muster - the captains will call for it. And when he falls, I suppose Ailill gets his chance. ...I hope he takes it.",
                     'default'),
        ],
        {'default': {'text': "From the lurikeen exiles.", 'choice': [a5, a6, a7]}},
        requires='sh_young_captain', group=True)

# ======================================================================== The Glimmer Lords (47-49) - the Sentinels
g1 = z.item("Lord Orist's Glass Belt", 'belt', 47, 'finesse', "It throws the light back wrong, like all their glass.")
g2 = z.item("Mianed's Upland Ring", 'ring', 47, 'mind', "Cold, and very bright.")
z.quest('sh_lords_west', 'The Lords of the West', 47, 'sr_maeve',
        "The Glimmer's host has lords - ten of them, named, each holding a stronghold. Kill the lord and the host there falls apart. I've seen it twice now.\n\nOrist holds the valley just north of this camp, and Mianed holds the upland. Will you [hunt the lords]? I want whatever they carry.",
        'hunt the lords',
        "Sentinel-Captain Maeve wants the Glimmer lords Orist and Mianed dead.",
        [
            hunt((172, 630), "Defeat Glimmer Orist in the valley " + where((172, 630), 'sr_maeve'), 'Glimmer Orist'),
            hunt((253, 142), "Defeat Glimmer Mianed on the upland", 'Glimmer Mianed',
                 text="Mianed comes apart into light. Where he stood, a slate of glimmer-glass, scratched with names."),
            end_talk('sr_maeve', "Bring the slate to Sentinel-Captain Maeve",
                     "Names. Not glimmer names - ours. 'Gearoid Iarla. Rider of the third rank.' 'Gearoid Iarla. Spear of the north shore.' It's a roll. The Earl's sleeping army, under Lough Gur.\n\nThat's what the silver shoes were for. The King wanted the Earl's host - for this war, for these hills. The Glimmer lords were to lead it.",
                     'default'),
        ],
        {'default': {'text': "From the Sentinels of Ceannai.", 'choice': [g1, g2]}})

g3 = z.item("Kelegur's Shining Torc", 'neck', 48, 'might', "It shines whether there's light or not.")
g4 = z.item("Zeit's Griever Bracer", 'bracer', 48, 'ward', "Made from a griever's shell. It moans in the wind.")
g5 = z.item("Meldun's Muster-Roll Ring", 'ring', 48, 'mind', "A ring with a list engraved inside it. Every name crossed out.")
z.quest('sh_lords_middle', 'The Lords of the Valleys', 48, 'sr_maeve',
        "GROUP work. Three lords hold the west of the middle valleys together - Kelegur, Zeit and Meldun - close enough to come to each other's aid. They were to be the Earl's captains.\n\nWill you [take the three]? Together, or they'll take you.",
        'take the three',
        "GROUP. The Glimmer lords Kelegur, Zeit and Meldun hold the west of the middle valleys together.",
        [
            hunt((460, 557), "Defeat Glimmer Kelegur " + where((460, 557), 'sr_maeve'), 'Glimmer Kelegur'),
            hunt((444, 679), "Defeat Glimmer Zeit", 'Glimmer Zeit'),
            hunt((430, 645), "Defeat Glimmer Meldun", 'Glimmer Meldun', r=60),
            end_talk('sr_maeve', "Report to Sentinel-Captain Maeve",
                     "Three captains with no army to lead. The Earl sleeps on, under his lake - and I'll ride round it myself every seventh year and count his horseshoes if I have to.\n\nTwo more lords in the middle valleys, Arios and Xaquira. They're not captains. Ceallach says they're keepers - of what, he won't say till he's sure.",
                     'default'),
        ],
        {'default': {'text': "From the Sentinels of Ceannai.", 'choice': [g3, g4, g5]}},
        requires='sh_lords_west', group=True)

g6 = z.item("Arios's Lamp-Glass Charm", 'gem', 48, 'charm', "A sliver of a Glimmer lamp. It still remembers being lit.")
g7 = z.item("Xaquira's Light-Woven Belt", 'belt', 48, 'finesse', "Woven, somehow, out of light. It is warm.")
z.quest('sh_lords_keepers', 'The Keepers of the Lamps', 48, 'sr_ceallach',
        "Arios and Xaquira. The middle valleys' last two lords. They don't fight like the others - they hang back, and the lights gather round them. I think they keep the King's lamps: the touched folk the Glimmer has burned. Every light in these hills.\n\nWill you [put out the keepers]? If I'm right, the hills will be darker for it.",
        'put out the keepers',
        "Druid Ceallach thinks the Glimmer lords Arios and Xaquira keep the King's lamps.",
        [
            hunt((753, 903), "Defeat Glimmer Xaquira " + where((753, 903), 'sr_ceallach'), 'Glimmer Xaquira'),
            hunt((1046, 813), "Defeat Glimmer Arios", 'Glimmer Arios',
                 text="Arios goes out like a candle, and for a breath the whole valley around him goes dark - then the lights come back, but fewer."),
            end_talk('sr_ceallach', "Report to Druid Ceallach",
                     "Fewer. You saw it. Fewer lights.\n\nThe lights aren't the King. They're the King's - and they can be taken from him. But the last of them gather in his son's hollow, and the hollow's door is kept by Venlar, in the east. Maeve has the Sentinels ready for that one.",
                     'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [g6, g7]}},
        requires='sh_lords_middle')

g8 = z.item("Venlar's Gate-Key Torc", 'neck', 49, 'mind', "A key of light, bent into a torc. It opens nothing now.")
g9 = z.item("Mantle of the Ceannai Sentinels", 'cloak', 49, 'ward', "The Sentinels' own, for those who broke the King's guard.")
g10 = z.item("Lord-Breaker's Bracer", 'bracer', 49, 'might', "Ten lords. Ten notches.")
z.quest('sh_venlar', 'The Gate-Keeper', 49, 'sr_maeve',
        "GROUP work, the hardest yet. Venlar holds the East Valley for the King - his guard-lord, the one who keeps the way to the Prince's Hollow. Deathwatchers and geists all round him, and knights.\n\nWill you [go for Venlar]? Bring everyone. The Sentinels will be at your back.",
        'go for Venlar',
        "GROUP. Glimmer Venlar, the King's guard-lord, holds the East Valley and the way to the Prince's Hollow.",
        [
            reach(Z, (1480, 600), "Go up the East Valley " + where((1480, 600), 'sr_maeve'),
                  "The East Valley is one long glow. Everything in it is watching you.", r=30),
            hunt((1520, 573), "Defeat Glimmer Venlar", 'Glimmer Venlar',
                 text="Venlar drops to one knee, burning out. 'The Prince waits,' he says. 'He was told you'd come. He has a letter for you.'"),
            end_talk('sr_maeve', "Report to Sentinel-Captain Maeve",
                     "A letter. For us? ...No. Not for us. Ceallach thinks he knows what it is. He's gone very quiet.\n\nTen lords. I've lost count of the Sentinels it took to follow the lights this far. Thank you.",
                     'default'),
        ],
        {'default': {'text': "From the Sentinels of Ceannai.", 'items': [g9], 'choice': [g8, g10]}},
        requires='sh_lords_keepers', group=True)

# ======================================================================== The King's Answer (49-50) - Aine's Circle
k1 = z.item("Zanllvi's Sealing-Wax Ring", 'ring', 49, 'finesse', "The wax on it is gold, and still soft.")
k2 = z.item("Answer-Bearer's Belt", 'belt', 49, 'mind', "The courier's belt. It carried the King's answer as far as the hollow.")
z.quest('sh_answer', "The King's Answer", 49, 'sr_ceallach',
        "In Lough Gur we took a letter off the Unseelie envoy: 'The north for me, the south for you, and Lug between us.' Cliodna, writing to the Glimmer King. The envoy waited on the moor for the King's answer - and it never came, because we killed the herald who carried it.\n\nThe King would have written it again, and sent it by a surer hand. His son's. Venlar says the Prince has a letter. Will you [find the answer]? Zanllvi guards the road to the hollow.",
        'find the answer',
        "Druid Ceallach thinks the Glimmer King's answer to Cliodna's letter lies in the Prince's Hollow.",
        [
            hunt((712, 1154), "Defeat Glimmer Zanllvi on the road to the hollow " + where((712, 1154), 'sr_ceallach'), 'Glimmer Zanllvi'),
            search(Z, (905, 1235), "Search the Prince's Hollow", "a letter sealed in gold wax", CRATE,
                   "'To the Queen in the north, from the King in the south. Agreed: the north for you, the south for me, and Lug between us. "
                   "But hear this. Your goborchend dig in your forest for the Eye, and I will not share Ireland with Balor's kind. When Lug falls, "
                   "shut the Eye - or I will shut it, and you with it. My son carries this, and my son does not lose letters. - C.'",
                   give="the King's answer"),
            end_talk('sr_ceallach', "Bring the King's answer to Druid Ceallach",
                     "'Lug between us.' The whole year - the mines, the revels, the wind, the fog, the lights on the lake, the tower in the bog - one bargain. Two kings of the sidhe carving Ireland in half, and our King in the middle.\n\nAnd 'the Eye'. The Fomorian eye the goborchend were waking in the Cursed Forest. Cliodna was digging it up - and even the Glimmer King was afraid of it.\n\nOne more lord stands at the King's ring. Then we know where we are.",
                     'default'),
        ],
        {'default': {'text': "From Aine's Circle.", 'choice': [k1, k2]}},
        requires='sh_venlar')

k3 = z.item("Saumer's Ring-Stone Charm", 'gem', 50, 'charm', "A chip from the ring of stones. It is warm, and very old.")
k4 = z.item("Lightbreaker's Bracer", 'bracer', 50, 'might', "For the one who broke the last of the King's lords.")
z.quest('sh_saumer', 'The Ring of Stones', 50, 'sr_maeve',
        "GROUP work - and as hard as anything short of the King himself.\n\nSaumer. The oldest of the lords, and the strongest. He waits at the western edge of the King's ring, in the south. With him dead, there's nothing left between the Muster and the King but the King.\n\nWill you [face Saumer]? Bring every friend you have.",
        'face Saumer',
        "GROUP. Glimmer Saumer, the oldest of the Glimmer lords, guards the edge of the King's ring.",
        [
            hunt((827, 1515), "Defeat Glimmer Saumer by the King's ring " + where((827, 1515), 'sr_maeve'), 'Glimmer Saumer',
                 text="Saumer falls, and for a moment, far off to the east among the stones, something enormous lifts its head and looks your way."),
            end_talk('sr_maeve', "Report to Sentinel-Captain Maeve",
                     "He looked at you? He looked at you. Gods.\n\nThe Muster's ready. Ceallach wants to talk to you first - he's decided something about that letter.",
                     'default'),
        ],
        {'default': {'text': "From the Sentinels of Ceannai.", 'choice': [k3, k4]}},
        requires='sh_answer', group=True)

k5 = z.item("Mantle of the King's Answer", 'cloak', 50, 'faith', "Aine's Circle's own, for the one who read the King's answer and knew what to do with it.")
k6 = z.item("Unlit Lantern Torc", 'neck', 50, 'mind', "A Glimmer lamp, put out for good, bound in silver.")
k7 = z.item("Ring of the Broken Bargain", 'ring', 50, 'finesse', "Two seals - a crowned woman, a crowned man - cut in half and set together.")
z.quest('sh_broken_bargain', 'The Broken Bargain', 50, 'sr_ceallach',
        "Here's where we are.\n\nCliodna's north is broken - the King's Host holds her forest when it marches, and she has to rebuild herself every time. The Glimmer King's south is breaking - his lords are dead, and the Muster can take his son's hollow and open his ring. The bargain is over. Neither of them has half of anything.\n\nBut the letter. 'The Eye.' Something both of them feared enough to put in writing. What we do with the letter matters. Will you [hear me out]?",
        'hear me out',
        "The bargain between the Unseelie Queen and the Glimmer King is broken - but the King's letter names the Fomorian Eye.",
        [
            reach(Z, (300, 1000), "Walk with Druid Ceallach down the valley, away from the camp " + where((300, 1000), 'sr_ceallach'),
                  "The valley is darker than it was. Behind you, in the camp, someone is singing - Lochlann's four notes, with a fifth at the end.", r=25),
            choice('sr_ceallach', "Decide what becomes of the King's answer",
                   "Two choices, and I can't make this one.\n\nWe [send it to Tara]. The King should know what was bargained over his head - and the druids of Tara should know that something under the Cursed Forest frightens dragons. They'll watch for it. Maybe too late; maybe not.\n\nOr we [burn it]. Here, tonight. Nobody learns there's an Eye, nobody goes digging for it out of greed or curiosity, and maybe it sleeps another thousand years. Maybe.",
                   [('send it to Tara', "Then a rider leaves tonight. The King will read it, and the druids will watch the north. Whatever wakes there, it won't wake unseen.\n\nThe threat in the south is ended - for now. Go and finish it: the Muster's going for the hollow, and then the ring. Whatever comes after, it comes after.", 'ending:tara'),
                    ('burn it', "...There. Gold wax burns blue. Did you know that? Nobody will ever read it again.\n\nThe threat in the south is ended - for now. Go and finish it: the Muster's going for the hollow, and then the ring. And if something ever opens its eye in that forest, we'll be the only two in Ireland who aren't surprised.", 'ending:burned')]),
        ],
        {'tara': {'text': "From Aine's Circle.", 'items': [k5], 'choice': [k6, k7]},
         'burned': {'text': "From Aine's Circle.", 'items': [k5], 'choice': [k6, k7]}},
        requires='sh_saumer')

if __name__ == '__main__':
    for zz in ZONES:
        errs = zz.check()
        print(zz.name, len(zz.quests), 'quests', len(zz.items), 'items', errs or 'ok')
