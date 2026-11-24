"""The Bog of Cullen's story quests (claude 2026-11-24, the zone brief in Zone Reviews and the owner's answers) - see story_gen.py.
Places: zone metres [x, y].

Moved out of story_hib.py with the zone's rebuild (its two quests kept, by id):
    python tools/claude-version/story_gen.py story_bog_of_cullen

The south's thread, a step further than Lough Gur: here the Glimmer has a foothold. It holds the Gemstone Tower (Cliodna's, empty
since she went north to the Cursed Forest), and the gems in its walls send its lights out over the bog as will-o'-the-wisps. The
siabra guide the lights; the lhiannan-sidhe sings in them; the Order of the Azure has come down the north road to burn the bog, and
its gold paid Steward Conn to clear the Chieftess out of the way; Badb, the battle-crow, has come down on her mound to feed on the
war. The thread: the lights in the tower. At the end, the Glimmer's lantern-bearer at the top of the Gemstone Tower, and beyond
him the road north to the Sheeroe Hills and Cuuldurach himself.

Arcs (recommended levels; rewards pay at the player's level):
  The Two Towns (36-39, the Clann of Alainn Bin)
  The Lhiannan-Sidhe (38-41, the Keeners of Cullen; folded in: The Lhiannan-Sidhe)
  The Keening (40-44, the Keeners; folded in: The Keening, its GROUP finale)
  The Azure Crusade (41-45, the Clann; GROUP finale: the Azure marshal)
  The Gemstone Tower (43-46, the Keeners; Badb, and the GROUP finale: the lantern-bearer)
"""
import math
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

CRATE = 1347
M, F, OLD = 337, 365, 362
Z = 205
ZONES = []

z = Zone(Z, 'Bog of Cullen', 3, 'hib_bog_of_cullen')
ZONES.append(z)
AT, NAMES = {}, {}

WAYGUARD, RAIDER, VENATOR, WATERWALKER, MIREGUARD = 60165995, 60165989, 60165994, 30007, 60165986
CREEPER, CRAWLER, LEECH = 60158591, 60158590, 60164164
WRAITH, BANSHEE = 60158463, 60158249
LHIANNAN = 60163260
GLIMMERLING, GLIM_WARD, GLIM_GHOUL, GLIM_STRIKER, GLIM_WARSHADE = 60161430, 60161424, 60161408, 60161421, 60161425
CRUSADER, CLEANSER, BANISHER, IDOLATER = 60158171, 60158173, 60158172, 60158182
CRONICORN = 60159503


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


# ------------------------------------------------------------------ people
person('fiona_harper', 'Fiona the Harper', (232, 945), 'f', 40, idle="Lorcan wrote me a poem every day for a year. Then he wrote them for someone else.")
person('bc_fergal', 'Turf-Reeve Fergal', (238, 930), 'm', 40, guild='Siopa',
       idle="Siopa's a fort and a turf-yard. The turf keeps Alainn Bin warm. The road keeps the turf moving. The road is my whole job.")
person('bc_tomas', 'Tomas the Peat-Cutter', (480, 1000), 'm', 36, guild='the Turf-Cutters',
       idle="Thirty years cutting turf. You find things. Bog butter. A boot. Last week, a gold collar the size of my head.")
person('sadhbh', 'Old Sadhbh', (1300, 1328), 'f', 48, model=OLD, guild='Keener', idle="I've keened for three chieftains. The banshee keened first, every time.")
person('steward_conn', 'Steward Conn', (1318, 1334), 'm', 46, idle="The Chieftess is well. Perfectly well. Please don't trouble her.")
person('bc_ruairc', 'Captain Ruairc', (1272, 1288), 'm', 48, guild='the Clann of Alainn Bin',
       idle="The Chieftess holds Alainn Bin. I hold everything she can see from her window. Lately, that's less.")
person('bc_brid', 'Keener Brid', (1240, 1250), 'f', 44, guild='the Keeners of Cullen',
       idle="We keen for the dead. Lately we read the lights too. A Keener has to know which lights mean a death.")
z.npc('lorcan_poet', 'Lorcan the Poet', [802, 1146], 'm', 40, during=['lhiannan/lorcan', 'lhiannan/verses'])
NAMES['lorcan_poet'] = 'Lorcan the Poet'
AT['lorcan_poet'] = (802, 1146)
z.npc('banshee_npc', 'the Banshee of Cullen', [1000, 1352], 'f', 55, model=F, during=['keening/banshee'])
NAMES['banshee_npc'] = 'the Banshee of Cullen'
AT['banshee_npc'] = (1000, 1352)

# ======================================================================== The Two Towns (36-39) - the Clann
o1 = z.item("Turf-Reeve's Tally Ring", 'ring', 36, 'might', "Fergal counts every block of turf that leaves Siopa. This was his old tally-ring.")
o2 = z.item("Wayguard-Iron Bracer", 'bracer', 36, 'ward', "Siabra bog-iron, cold and heavy.")
z.quest('bc_siopa_road', 'The Siopa Road', 36, 'bc_fergal',
        "The siabra have put a post on the Siopa road - wayguards and their hounds, right across it. No turf's gone to Alainn Bin in a week.\n\nThe odd thing: the siabra used to rob the road. Now they just stand on it and turn people back. As if they're keeping it clear for something. Will you [clear the post]?",
        'clear the post',
        "A siabra wayguard post on the Siopa road turns everyone back.",
        [
            kill(Z, (503, 819), "Clear the siabra wayguard post " + where((503, 819), 'bc_fergal'), 'siabra wayguard', WAYGUARD, [36, 37], 5),
            search(Z, (508, 824), "Search the wayguard post", "siabra orders, scratched on a glowing slate", CRATE,
                   "A slate that glows, scratched with siabra marks. Fergal will want to see it: it's a map of the bog with lines drawn from the tower in the middle out to every road."),
            end_talk('bc_fergal', "Bring the slate to Turf-Reeve Fergal", "Lines from the Gemstone Tower to every road. They're not keeping the roads clear. They're keeping them dark - so whatever walks out of that tower at night can walk where it likes.\n\nThe Clann at Alainn Bin should see this. Captain Ruairc.", 'default'),
        ],
        {'default': {'text': "From Siopa.", 'choice': [o1, o2]}})

o3 = z.item("Cullen Gold Collar Charm", 'gem', 37, 'charm', "A link from the gold collar Tomas cut out of the turf. Bronze Age gold, warm as skin.")
o4 = z.item("Peat-Cutter's Belt", 'belt', 37, 'finesse', "Tomas's own. The buckle is a turf-spade.")
z.quest('bc_turf_gold', 'The Cullen Gold', 37, 'bc_tomas',
        "You heard about the collar? Everyone has. The siabra too, it seems - they've come for it twice, and for me with it.\n\nI've buried it again, out in the cuttings. Will you [stand by me] while I dig it up and get it to Alainn Bin? The Chieftess can keep it. I don't want it.",
        'stand by me',
        "Tomas the Peat-Cutter found a gold collar in the turf, and the siabra want it.",
        [
            defend(Z, (480, 1000), "Keep Tomas alive while he digs up the gold " + where((480, 1000), 'bc_tomas'),
                   "Tomas lifts the collar out of the turf. Even in daylight it glows faintly - and he swears it didn't, last week.",
                   'Tomas the Peat-Cutter', 60161797, 38, "Tomas starts to dig. Out of the reeds come siabra raiders, running low.",
                   [(RAIDER, 'siabra raider', [36, 37]), (MIREGUARD, 'siabra mireguard', [37, 38])], 'Keep Tomas alive',
                   model=M, duration=120, every=20, count=3),
            end_talk('bc_ruairc', "Take Tomas and the gold to Captain Ruairc in Alainn Bin", "The Cullen gold. The old kings' hoard - there's more of it under that turf than in Tara.\n\nAnd it glows. Everything out there glows lately. Fergal's slate says the tower. I say the siabra serve something in that tower, and it wants gold - or light, or both.", 'default'),
        ],
        {'default': {'text': "From the Clann.", 'choice': [o3, o4]}},
        requires='bc_siopa_road')

o5 = z.item("Post-Captain's Seal Ring", 'ring', 38, 'mind', "Siabra captains seal their orders with light. This seal still glows.")
o6 = z.item("Stilt-Walker's Boots-Charm", 'gem', 38, 'finesse', "The siabra build their posts on stilts over the water.")
z.quest('bc_siabra_posts', 'The Post-Captains', 38, 'bc_ruairc',
        "Two siabra posts hold the north-west marches - Muroi's and Enan's. Their captains take orders from the tower and pass them on.\n\nWill you [break the posts]? Kill the captains. I want their seals.",
        'break the posts',
        "Captain Ruairc wants the siabra post-captains Muroi and Enan dead.",
        [
            hunt((317, 319), "Kill Muroi, who holds the western siabra post " + where((317, 319), 'bc_ruairc'), 'Muroi'),
            hunt((726, 266), "Kill Enan, who holds the northern siabra post", 'Enan',
                 text="Enan's seal glows. Pressed to wax, it shows a crown of light - not a siabra mark at all."),
            end_talk('bc_ruairc', "Bring the seals to Captain Ruairc", "A crown of light. The Glimmer King's mark - the Azure crusaders on the north road wear it on their banners, crossed out.\n\nSo the siabra have a new king. One causeway left between the marches and the tower: Saemus holds it.", 'default'),
        ],
        {'default': {'text': "From the Clann.", 'choice': [o5, o6]}},
        requires='bc_turf_gold')

o7 = z.item("Causeway-Breaker's Torc", 'neck', 39, 'might', "Bog-oak and bronze, from the causeway's first post.")
o8 = z.item("Lantern-Pole Bracer", 'bracer', 39, 'ward', "Cut from one of the poles that carried the lights.")
z.quest('bc_causeway', 'The Causeway', 39, 'bc_ruairc',
        "The causeway runs from the north marches into the middle of the bog, toward the tower. Saemus holds it with waterwalkers.\n\nAnd Fergal says there are poles along it, in a line, every forty paces - like lamp-posts. Will you [take the causeway]?",
        'take the causeway',
        "Saemus and his waterwalkers hold the causeway to the tower, and there are poles along it like lamp-posts.",
        [
            kill(Z, (522, 560), "Kill the siabra waterwalkers on the causeway " + where((522, 560), 'bc_ruairc'), 'siabra waterwalker', WATERWALKER, [38, 39], 4),
            hunt((522, 547), "Kill Saemus at the head of the causeway", 'Saemus'),
            search(Z, (560, 600), "Look at the poles along the causeway", "a lantern-pole, hung with a glowing bead", CRATE,
                   "Each pole carries a bead of glass with a light in it, and the lights lean toward the tower like flowers toward the sun. A road of lights, for walking on the bog at night."),
            end_talk('bc_ruairc', "Report to Captain Ruairc", "A road of lights. The siabra built a lit road from the marches to the tower. For whom?\n\nThe Keeners will have a word for it. Old Sadhbh, or Brid. Me, I just want to burn it.", 'default'),
        ],
        {'default': {'text': "From the Clann.", 'choice': [o7, o8]}},
        requires='bc_siabra_posts')

# ======================================================================== The Lhiannan-Sidhe (38-41) - the Keeners
p1 = z.item("Glowing-Page Charm", 'gem', 39, 'mind', "A page of Lorcan's verse that glows in the dark.")
p2 = z.item("Harper's Wrist-Cord", 'bracer', 39, 'faith', "Fiona's spare harp-strings, braided.")
z.quest('bc_pages', 'Pages in the Reeds', 39, 'fiona_harper',
        "Pages. Lorcan's verse, stuck to the reeds all over the bog - and at night, Keener Brid says, they glow.\n\nBefore I ask anything else of you, will you [gather the pages]? I want to read what he's writing. Even if it's for her.",
        'gather the pages',
        "Pages of Lorcan's verse are stuck to the reeds all over the bog, and they glow at night.",
        [
            search(Z, (560, 800), "Gather the glowing pages from the reeds by the causeway " + where((560, 800), 'fiona_harper'), "pages of verse, faintly glowing", CRATE,
                   "Lorcan's verse, in an old man's hand. Every line is about light: light on water, light in a tower, light that takes away weeping.", give="Lorcan's glowing pages"),
            kill(Z, (600, 760), "Put out the bog lights circling the pages", 'bog light', GLIMMERLING, [38, 39], 4),
            end_talk('fiona_harper', "Bring the pages to Fiona", "He never wrote about light. He wrote about me, and rain, and his mother's kitchen. This is someone else's song in his hand.\n\nThe lhiannan-sidhe is a muse. Something is singing through her. Bring him [home] - whatever it takes.", 'default'),
        ],
        {'default': {'text': "From Fiona.", 'choice': [p1, p2]}})

it_muse = z.item("Muse's Kiss Pendant", 'neck', 40, 'mind', "Cold silver, shaped like lips. It whispers rhymes.")
it_verses = z.item('Burnt-Verse Ring', 'ring', 40, 'faith', "Ash from a burned book of poems, sealed in glass.")
it_siabra = z.item("Wayguard's Bracer", 'bracer', 40, 'might', "Siabra bog-iron, cold and heavy.")
it_creeper = z.item('Bog-Creeper Cloak', 'cloak', 40, 'ward', "Woven from the vines of bog creepers. It moves a little on its own.")
z.quest('lhiannan', 'The Lhiannan-Sidhe', 40, 'fiona_harper',
        "Lorcan was my lover and the finest poet in Cullen. Last spring a lhiannan-sidhe found him - a faerie muse. They give a poet the best verses he'll ever write, and they drink his life to do it.\n\nHe wrote to me last month, from somewhere in the bog. The writing was an old man's. He's thirty. Will you [find Lorcan]?",
        'find Lorcan',
        "A lhiannan-sidhe - a faerie muse who feeds on poets - has taken Fiona's lover into the bog.",
        [
            reach(Z, (570, 810), 'Go into the bog by the siabra causeway', "Siabra watch from the posts. Pages of verse are stuck to the reeds, soaked, the ink running.", r=20),
            kill(Z, (503, 819), 'Fight through the siabra wayguards', 'siabra wayguard', WAYGUARD, [39, 40], 5),
            search(Z, (560, 800), 'Gather the scattered verses', "pages of verse in a shaking hand", CRATE,
                   "Each page better than the last, and each hand older. The last pages are nearly illegible - and nearly perfect.", give="Lorcan's verses"),
            kill(Z, (555, 918), 'Cut through the bog creepers to the east', 'bog creeper', CREEPER, [39, 40], 5),
            L('lorcan', talk('lorcan_poet', 'Find Lorcan', "Fiona sent you. Fiona. I wrote her a hundred poems and none of them were good enough. Now I write for HER, and every one is perfect - she brings the light, and the light brings the words.\n\nShe'll come at dusk. Look at me. I'm thirty. I don't care. Do you understand - every [word]...", kw='word')),
            boss(Z, (800, 1150), 'Drive off the lhiannan-sidhe', "The lhiannan-sidhe falls back, hissing, into the mist, and the light goes with her. Lorcan clutches his chest and breathes like a man surfacing from deep water.",
                 'the Lhiannan-Sidhe', LHIANNAN, 44, "A woman more beautiful than the moon walks out of the mist, lit from inside. 'He is mine. He is my masterpiece. The light says so.'",
                 objective='Drive off the Lhiannan-Sidhe', hp=2.6, adds=[(CREEPER, 'bog creeper', [39, 40])], every=25, count=2),
            L('verses', choice('lorcan_poet', 'Decide what becomes of the verses',
                   "She's not gone. Not while I have the verses. They're hers as much as mine - she lives in them. If I [burn the verses], I'm free, and I'll go back to Fiona and write bad poems and grow old slowly.\n\nIf I [keep them], she'll come back, and I'll die before winter, and they'll sing these in every hall in Hibernia for a thousand years. Choose. Please. I can't.",
                   [('burn the verses', "...They burn so slowly. ...There. I can't remember a line. Not one. Take me to Fiona.", 'next:burned'),
                    ('keep them', "Then I'll keep them. Tell Fiona the best ones are hers. They are. Tell her I'm sorry.", 'next:kept')])),
            L('burned', end_talk('fiona_harper', 'Return to Fiona', "He's home. He's grey and thin and he can't remember a word he wrote - and he wrote me a poem this morning. It's terrible. It's the best thing I've ever read.", 'burned')),
            L('kept', end_talk('fiona_harper', 'Return to Fiona', "He kept them. And he sent me the best ones.\n\nThey're... they're beyond anything. I'll set them to music. I'll play them at his wake, which will be before winter. Take this, and go, before I cry on you.", 'kept')),
        ],
        {'burned': {'text': "Take this. He wanted you to.", 'items': [it_verses], 'choice': [it_siabra, it_creeper]},
         'kept': {'text': "Take this, and go.", 'tragic': True, 'items': [it_muse], 'choice': [it_siabra, it_creeper]}},
        requires='bc_pages')

p3 = z.item("Unlit Muse Ring", 'ring', 41, 'faith', "A muse's ring, with the light gone out of it.")
p4 = z.item("Keener's Reed Belt", 'belt', 41, 'ward', "Brid weaves them from the reeds the lights won't touch.")
z.quest('bc_muse_light', 'Where the Muses Go', 41, 'bc_brid',
        "Fiona's muse isn't the only one. There are lhiannan-sidhe all over the bog this year, and they all sing the same song now - light, light, light. They've found a better patron than poets.\n\nWill you [silence them]? The two that sing loudest are in the reeds by the tower and east of it.",
        'silence them',
        "The lhiannan-sidhe of the bog all sing the Glimmer's song now.",
        [
            kill(Z, (560, 800), "Silence the lhiannan-sidhe in the reeds by the causeway " + where((560, 800), 'bc_brid'), 'lhiannan-sidhe', LHIANNAN, [40, 41], 1),
            kill(Z, (1100, 1000), "Silence the lhiannan-sidhe east of the tower", 'lhiannan-sidhe', LHIANNAN, [40, 41], 1,
                 text="With her last breath she sings one line clear: 'The lantern-bearer keeps the light, the light keeps the tower, the tower keeps the bog.'"),
            end_talk('bc_brid', "Report to Keener Brid", "The lantern-bearer. In the tower.\n\nSadhbh needs to hear this - but not now. Now she's listening to the banshee, and the banshee is keening for the Chieftess.", 'default'),
        ],
        {'default': {'text': "From the Keeners.", 'choice': [p3, p4]}},
        requires='lhiannan')

# ======================================================================== The Keening (40-44) - the Keeners, GROUP finale
k1 = z.item("Keening-Stone Charm", 'gem', 40, 'faith', "A chip of the banshee's stone. It's always cold.")
k2 = z.item("Wraith-Mud Bracer", 'bracer', 40, 'might', "Black iron from the bog, where the drowned dead walk.")
z.quest('bc_keen_heard', 'The Keen', 40, 'sadhbh',
        "Listen. Do you hear it? No - you wouldn't, yet. The banshee of Cullen. She keens on her stone in the bog north of town, for a death in the old families.\n\nThe black wraiths have gathered round her stone. Will you [go to the stone]? Clear them away. I want to hear her plain.",
        'go to the stone',
        "The banshee of Cullen keens on her stone north of Alainn Bin, and the black wraiths have gathered round it.",
        [
            kill(Z, (1004, 1359), "Clear the black wraiths round the keening stones " + where((1004, 1359), 'sadhbh'), 'black wraith', WRAITH, [40, 41], 4),
            reach(Z, (1010, 1350), "Stand by the keening stone and listen", "Far off, a woman keening. And another, nearer, keening wrong - too high, too bright, like a voice through glass.", r=20),
            end_talk('sadhbh', "Report to Old Sadhbh", "Two keeners. One's the banshee of Cullen; I'd know her anywhere. The other's false. Riolda - a banshee that walked into the lights, and keens for whatever they tell her to.\n\nAnd the true one keens for the Chieftess. Who isn't sick.", 'default'),
        ],
        {'default': {'text': "From the Keeners.", 'choice': [k1, k2]}})

k3 = z.item("False-Keener's Veil Charm", 'gem', 42, 'mind', "Riolda's veil, the light gone out of it.")
k4 = z.item("Keener's Black Belt", 'belt', 42, 'faith', "Worn at every keening in Cullen for a hundred years.")
z.quest('bc_riolda', 'Riolda', 42, 'sadhbh',
        "Riolda. A banshee who keens false. She walks the keening ground at night, and wherever she keens, the bog-lights come.\n\nShe'll drown the true keen in hers, and then nobody will know whose death is coming. Will you [silence Riolda]? Only at night. She's not there by day.",
        'silence Riolda',
        "Riolda, a banshee who walked into the lights, keens false on the keening ground at night.",
        [
            hunt((1079, 1279), "Silence Riolda on the keening ground (at night) " + where((1079, 1279), 'sadhbh'), 'Riolda',
                 text="Riolda's keen breaks off. In the silence, clear and far, the true banshee: keening for the Chieftess, and under it a name. Conn."),
            end_talk('sadhbh', "Report to Old Sadhbh", "Conn. The steward.\n\nTwenty years he's served her. ...Look in his room, before I say a word to anyone. Find me proof.", 'default'),
        ],
        {'default': {'text': "From the Keeners.", 'choice': [k3, k4]}},
        requires='bc_keen_heard')

k5 = z.item("Steward's Ledger Ring", 'ring', 43, 'mind', "The ring Conn sealed the household's accounts with. And other things.")
k6 = z.item("Blue-Wax Charm", 'gem', 43, 'charm', "Azure sealing wax, still bright.")
z.quest('bc_steward_letters', "The Steward's Letters", 43, 'sadhbh',
        "Conn's room is in the Chieftess' hall, and he locks it. He keeps his papers in a box under the floor; the maids know, maids always know.\n\nWill you [search his room] while he's at the market? Quietly.",
        'search his room',
        "Old Sadhbh wants Steward Conn's hidden papers found.",
        [
            search(Z, (1322, 1338), "Search under the floor of Steward Conn's room " + where((1322, 1338), 'sadhbh'), "a box of letters sealed in blue wax", CRATE,
                   "Letters sealed in blue wax - the Order of the Azure's. 'When the Chieftess is gone, your son will hold Alainn Bin, and Alainn Bin will open its gates to the Order and its torches. The bog must burn. Payment enclosed.' And a purse of Azure silver.", give="the Azure letters"),
            end_talk('sadhbh', "Bring the letters to Old Sadhbh", "The Azure. The Azure paid him.\n\nThey want the Chieftess dead so they can burn the bog - with the turf-cutters, and Siopa, and us, if we're in the way. Because of the lights.\n\nRight. Now we stop it. Properly. Bring friends.", 'default'),
        ],
        {'default': {'text': "From the Keeners.", 'choice': [k5, k6]}},
        requires='bc_riolda')

it_keen = z.item("Keener's Veil", 'cloak', 44, 'faith', "Sadhbh's own. She has keened for three chieftains in it.")
it_vial = z.item("Poisoner's Vial Pendant", 'neck', 44, 'mind', "Empty now. The glass is very fine - sidhe glass.")
it_venator = z.item("Venator's Ring", 'ring', 44, 'finesse', "From the hand of a siabra assassin.")
it_wraith = z.item('Black Wraith Bracer', 'bracer', 44, 'might', "The black wraiths of Cullen are the dead who drowned in the bog. This one wore iron.")
it_dana = z.item("Chieftess Dana's Brooch", 'gem', 44, 'charm', "The Chieftess' own brooch, given in thanks.")
z.quest('keening', 'The Keening', 44, 'sadhbh',
        "This is GROUP work, so bring friends you trust.\n\nThe banshee of Cullen has keened under the Chieftess' window every night for a week. The letters say why: Conn poisons her for the Azure. But a poisoner never trusts poison alone.\n\nWill you [find out who] waits to finish it? Start with the [steward]. Let him think we know nothing.",
        'find out who',
        "GROUP. The banshee of Cullen keens nightly for the Chieftess. Steward Conn poisons her for the Azure - and someone waits to finish it.",
        [
            talk('steward_conn', 'Question Steward Conn',
                 "The banshee? Old women's stories. The Chieftess is perfectly well. I see to everything - her food, her wine, her guests. I'd know if anything were wrong.\n\nIf you must poke about, the black wraiths in the bog to the [east] have been bold of late. Go and deal with them. That would actually be useful.", kw='east'),
            kill(Z, (1404, 1285), 'Deal with the black wraiths east of town', 'black wraith', WRAITH, [42, 43], 4,
                 text="Among the wraith-mud, a dropped satchel - a steward's satchel, with a steward's seal."),
            search(Z, (1392, 1300), 'Search the dropped satchel', "a steward's satchel", CRATE,
                   "A vial of sidhe glass, nearly empty. A letter: 'Half in her wine each night. By the dark moon it will look like a wasting. The venator will finish it if it doesn't. - C.'",
                   give="the poisoner's vial"),
            reach(Z, (1010, 1350), "Find the banshee's keening-stone", "A grey woman sits on a stone in the bog, combing her hair, weeping. She looks up at you.", r=20),
            L('banshee', talk('banshee_npc', 'Speak with the banshee', "You hear me. Good. Few do, before.\n\nThe Chieftess' death is close. The steward pours it. And the siabra hunter waits in the bog to the west of my stone, to finish it if the poison is slow - bought with Azure silver, though siabra and Azure hate each other. Stop the [hunter]. I am so tired of keening.", kw='hunter')),
            boss(Z, (990, 1340), 'Kill the siabra assassin in the bog', "The venator dies in the bog-water. Far off, under the Chieftess' window, the keening stops.",
                 'Iuchra the Venator', VENATOR, 48, "A siabra in mud-grey leathers rises out of the bog with a knife in each hand. 'The steward pays well. You'll do for practice.'",
                 objective='Kill Iuchra the Venator', hp=3.0, adds=[(VENATOR, 'siabra venator', [42, 43])], every=25, count=2),
            choice('sadhbh', 'Return to Old Sadhbh',
                   "The keening's stopped. I heard it stop at moonrise. And you have the vial. Conn.\n\nConn, who has served her twenty years. He wanted the chieftainship for his son, and the Azure promised it.\n\nThe Chieftess is too kind. She'll want to [banish him]. The old law says [death] for a poisoner. She'll ask me, and I'll ask you. You've seen more of it than I have.",
                   [('banish him', "Banished. Beyond the Shannon, with nothing but his cloak. ...She'll weep for him. She's like that.", 'ending:banished'),
                    ('death', "The old law, then. I'll keen for him myself. Somebody should.", 'ending:death')]),
        ],
        {'banished': {'text': "From the Chieftess, with her thanks.", 'items': [it_dana], 'choice': [it_keen, it_venator, it_wraith]},
         'death': {'text': "From the Chieftess.", 'tragic': True, 'items': [it_vial], 'choice': [it_keen, it_venator, it_wraith]}},
        topics={'steward': "Conn. He runs the Chieftess' household. He's very calm. Far too calm."}, group=True, requires='bc_steward_letters')

# ======================================================================== The Azure Crusade (41-45) - the Clann, GROUP finale
c1 = z.item("Crossed-Crown Ring", 'ring', 41, 'might', "The Azure wear the Glimmer King's crown crossed out. So do you, now.")
c2 = z.item("Torch-Bearer's Bracer", 'bracer', 41, 'ward', "Scorched blue iron.")
z.quest('bc_azure_march', 'The Azure March', 41, 'bc_ruairc',
        "The Order of the Azure has come down the north road from the Sheeroe Hills. Crusaders, cleansers, banners with a crown crossed out. They say they're here for the lights.\n\nThey're burning turf-cutters' huts as they come. Will you [stop the march]? The north road, before they reach the cuttings.",
        'stop the march',
        "The Order of the Azure marches down the north road, burning turf-cutters' huts.",
        [
            kill(Z, (1050, 300), "Break the Azure crusaders on the north road " + where((1050, 300), 'bc_ruairc'), 'azure crusader', CRUSADER, [41, 42], 6),
            end_talk('bc_ruairc', "Report to Captain Ruairc", "They fight like men who've already won. ...The Glimmer took the Sheeroe Hills from them. They mean to burn the bog to keep it from taking this too, and they don't much care who's standing on it.", 'default'),
        ],
        {'default': {'text': "From the Clann.", 'choice': [c1, c2]}})

c3 = z.item("Pitch-Black Charm", 'gem', 42, 'charm', "A lump of the Azure's pitch, set in silver. It still smells of smoke.")
c4 = z.item("Banisher's Belt", 'belt', 42, 'mind', "An Azure banisher's belt, hung with blue glass.")
z.quest('bc_pyre', 'The Pyre', 42, 'bc_ruairc',
        "The Azure have built a pyre on the north edge of the bog - barrels of pitch, and their banishers praying over it. When it's lit, the fire goes into the peat, and peat burns for years. Underground. The whole bog.\n\nWill you [break the pyre]? Kill the banishers. Spill the pitch into the water.",
        'break the pyre',
        "The Azure have built a pyre of pitch on the bog's north edge - lit, it would set the peat burning for years.",
        [
            kill(Z, (980, 330), "Kill the azure banishers at the pyre " + where((980, 330), 'bc_ruairc'), 'azure banisher', BANISHER, [42, 43], 3),
            search(Z, (985, 335), "Spill the pitch barrels into the bog", "barrels of Azure pitch", CRATE,
                   "The pitch glugs out into the black water and lies there. On the barrels, an order: 'Marshal Cathbarr: when the steward's work is done, fire the bog from the north. Alainn Bin will open its gates.'"),
            end_talk('bc_ruairc', "Report to Captain Ruairc", "'When the steward's work is done.' Conn. The Keeners were right.\n\nMarshal Cathbarr. He sits in the Azure camp on the north road with his banners. One more push and we go for him.", 'default'),
        ],
        {'default': {'text': "From the Clann.", 'choice': [c3, c4]}},
        requires='bc_azure_march')

c5 = z.item("Idol-Breaker's Ring", 'ring', 43, 'faith', "The idolaters carry little crowns of light to burn. This is one, broken.")
c6 = z.item("Cleanser's Smoke-Cloak", 'cloak', 43, 'ward', "It smells of smoke for ever.")
z.quest('bc_cleansers', 'The Cleansers', 43, 'bc_ruairc',
        "Before we go for Cathbarr: his cleansers and idolaters are out in the eastern bog, hunting siabra and burning the reeds. The bears are fleeing into the turf-cutters' camps.\n\nWill you [thin them]? Cleansers and idolaters. Then we go.",
        'thin them',
        "The Azure's cleansers and idolaters are burning the reeds of the eastern bog.",
        [
            kill(Z, (1050, 420), "Kill the azure cleansers burning the reeds " + where((1050, 420), 'bc_ruairc'), 'azure cleanser', CLEANSER, [42, 43], 5),
            kill(Z, (1100, 250), "Kill the azure idolaters", 'azure idolater', IDOLATER, [42, 43], 4,
                 text="Overhead, a black crow, bigger than an eagle, circling the smoke. Badb. The battle-crow came down when the burning started."),
            end_talk('bc_ruairc', "Report to Captain Ruairc", "Badb. If she's circling, the fighting's not over. She always knows.\n\nRight. Cathbarr. Bring friends.", 'default'),
        ],
        {'default': {'text': "From the Clann.", 'choice': [c5, c6]}},
        requires='bc_pyre')

c7 = z.item("Marshal's Blue Torc", 'neck', 45, 'might', "Cathbarr's torc of blue enamel, cracked.")
c8 = z.item("Mantle of Alainn Bin", 'cloak', 45, 'ward', "The Clann's own, for those who broke the Azure on the north road.")
c9 = z.item("Crow-Feather Charm", 'gem', 45, 'charm', "A feather Badb dropped over the battle. It's warm.")
z.quest('bc_marshal', 'Marshal Cathbarr', 45, 'bc_ruairc',
        "GROUP work.\n\nMarshal Cathbarr of the Order of the Azure, in his camp on the north road, with his banners and his crusaders. He paid a steward to poison a chieftess so he could burn the bog.\n\nWe go in, we break him, the Azure go back to the hills. Say [for Alainn Bin] when your friends are ready.",
        'for Alainn Bin',
        "GROUP. Break Marshal Cathbarr of the Azure in his camp on the north road.",
        [
            reach(Z, (1080, 260), "Gather below the Azure camp on the north road " + where((1080, 260), 'bc_ruairc'), "Blue banners with the crown crossed out. Somewhere a man is preaching about fire.", r=25),
            boss(Z, (1120, 160), "Defeat Marshal Cathbarr in the Azure camp",
                 "Cathbarr falls among his banners. 'You'll wish we'd burned it,' he says. 'When the Glimmer King comes down out of the hills - you'll wish.' Above, the great crow circles once, and goes back to her mound.",
                 'Marshal Cathbarr', BANISHER, 50, "A tall man in blue enamel turns from his pyre-plans. 'Lantern-lovers. The Glimmer will thank you. Then it'll take your eyes.'",
                 objective='Defeat Marshal Cathbarr', hp=4.5, adds=[(CRUSADER, 'azure crusader', [43, 44]), (CLEANSER, 'azure cleanser', [43, 44])], every=22, count=3),
            choice('bc_ruairc', "Report to Captain Ruairc",
                   "The Azure are pulling back up the north road. Some of them - the young ones - want to stay. They say they hate the Glimmer as much as we do, and they're not wrong.\n\nWe could [take them in], under the Clann's eye. Or we [send them north] with the rest. Your call. You broke their marshal.",
                   [('take them in', "Then they stay. Under the Clann's eye, and no torches. ...We'll see if a crusader can learn to cut turf.", 'ending:taken'),
                    ('send them north', "North, then. Every one. Let the Order keep its zealots.", 'ending:sent')]),
        ],
        {'taken': {'text': "From the Clann of Alainn Bin.", 'items': [c8], 'choice': [c7, c9]},
         'sent': {'text': "From the Clann of Alainn Bin.", 'items': [c8], 'choice': [c7, c9]}},
        requires='bc_cleansers', group=True)

# ======================================================================== The Gemstone Tower (43-46) - the Keeners; Badb; GROUP finale
g1 = z.item("Bog-Light Lantern Charm", 'gem', 43, 'mind', "A dead bog-light in a glass bead. It flickers when the Glimmer is near.")
g2 = z.item("Wisp-Reader's Ring", 'ring', 43, 'faith', "Brid reads the lights by the colour. This ring helps.")
z.quest('bc_tower_lights', 'Reading the Lights', 43, 'bc_brid',
        "The bog-lights - the will-o'-the-wisps that lead travellers off the path. Every Keener reads them: a light over the water means a death. This year they all come from one place, and they all go back to it.\n\nWill you [hunt the bog-lights] at night? I want to see what they carry back.",
        'hunt the bog-lights',
        "The bog-lights all come from the Gemstone Tower and go back to it.",
        [
            kill(Z, (700, 900), "Put out the bog-lights near the tower, at night " + where((700, 900), 'bc_brid'), 'bog light', GLIMMERLING, [42, 43], 6,
                 text="Each light, as it goes out, drops something: a speck of bright stone, like a chip off a gem."),
            end_talk('bc_brid', "Bring the bright chips to Keener Brid", "Gem-chips. From the Gemstone Tower's walls. The lights are pieces of the tower walking about.\n\nThe tower was Cliodna's, the northern queen's - she left it this spring. Something else moved in, and the gems in the walls answer to it now.", 'default'),
        ],
        {'default': {'text': "From the Keeners.", 'choice': [g1, g2]}})

g3 = z.item("Ward-Shard Bracer", 'bracer', 44, 'ward', "From a glimmer ward, the tower's door-keepers.")
g4 = z.item("Three-Gem Belt", 'belt', 44, 'finesse', "Three chips of the tower's great gems, set in leather.")
z.quest('bc_three_gems', 'The Three Gems', 44, 'bc_brid',
        "Three great gems in the tower's walls - green, white and red. The old tales say Cliodna set them there to watch the bog. Now they shine.\n\nWill you [look at the gems]? Get close. The wards at the gate will try to stop you.",
        'look at the gems',
        "The three great gems in the Gemstone Tower's walls shine with the Glimmer's light.",
        [
            kill(Z, (820, 1040), "Kill the glimmer wards at the tower gate " + where((820, 1040), 'bc_brid'), 'glimmer ward', GLIM_WARD, [43, 44], 4),
            search(Z, (870, 965), "Look at the great gems in the tower's walls", "the three great gems, shining", CRATE,
                   "Green, white and red, each as big as a head, each blazing. Inside each, like a fly in amber, a little shape of light: a crowned man. Watching the bog."),
            end_talk('bc_brid', "Report to Keener Brid", "A crowned man. Cuuldurach - the Glimmer King, the dragon in the Sheeroe Hills. He's looking out of Cliodna's gems.\n\nBreak the gems and he's blind here. But they're kept, and the keeper is the lantern-bearer the muses sang about. That's for many hands. And Badb - Badb sits on her mound by the gate, and nothing passes her when she's hungry.", 'default'),
        ],
        {'default': {'text': "From the Keeners.", 'choice': [g3, g4]}},
        requires='bc_tower_lights')

g5 = z.item("Battle-Crow's Pinion Torc", 'neck', 45, 'might', "A pinion feather of Badb's, bound in bronze.")
g6 = z.item("Cronicorn Horn Ring", 'ring', 45, 'finesse', "Badb's unicorns are black, and very old.")
z.quest('bc_badb', 'The Crow on the Mound', 45, 'sadhbh',
        "GROUP work - real war-band work.\n\nBadb. The battle-crow, the war-goddess's sister. She's come down on the mound by the tower because she smells war, and she's right: Azure, Glimmer, siabra, us. She feeds on it. While she sits there nobody reaches the tower gate.\n\nWill you [face Badb]? Bring everyone. A Keener will keen for whoever she takes.",
        'face Badb',
        "GROUP. Badb, the battle-crow, sits on her mound by the Gemstone Tower and feeds on the war.",
        [
            hunt((781, 787), "Defeat Badb, the battle-crow, on her mound by the tower " + where((781, 787), 'sadhbh'), 'Badb',
                 text="Badb comes down out of the air as a woman, and stands, and laughs. 'Well fought. I'll come back when you've a better war.' Then she is a crow again, and gone."),
            end_talk('sadhbh', "Report to Old Sadhbh", "She'll be back. She always is. But not for a while.\n\nThe gate's open. Brid's waiting.", 'default'),
        ],
        {'default': {'text': "From the Keeners.", 'choice': [g5, g6]}},
        requires='bc_three_gems', group=True)

g7 = z.item("Lantern-Bearer's Glass Torc", 'neck', 46, 'mind', "The lantern-bearer's lamp, broken and bound. Dark now.")
g8 = z.item("Mantle of the Keen", 'cloak', 46, 'ward', "The Keeners' own, for those who put out the tower's light.")
g9 = z.item("Dark-Gem Ring", 'ring', 46, 'faith', "A chip of the red gem, dark.")
z.quest('bc_lantern_bearer', 'The Lantern-Bearer', 46, 'bc_brid',
        "GROUP work, the last of it here.\n\nThe lantern-bearer keeps the light, the light keeps the tower, the tower keeps the bog. Kill the keeper and the gems go dark, and Cuuldurach is blind in Cullen.\n\nSay [into the tower] when your friends are ready.",
        'into the tower',
        "GROUP. The Glimmer's lantern-bearer keeps the light at the top of the Gemstone Tower.",
        [
            reach(Z, (860, 1000), "Climb into the Gemstone Tower " + where((860, 1000), 'bc_brid'), "The walls are warm. The great gems blaze. Somewhere above, someone is humming a song you've heard in Lough Gur.", r=25),
            boss(Z, (878, 972), "Defeat the Glimmer's lantern-bearer at the top of the tower",
                 "The lantern-bearer's lamp cracks, and one by one the great gems go dark - green, white, red. Out over the bog, every light goes out at once.",
                 'Lochru the Lantern-Bearer', GLIM_WARSHADE, 50, "A tall shape of light lifts a lamp. 'You put out a herald on a lake. You will not put out the King's own lantern.'",
                 objective='Defeat Lochru the Lantern-Bearer', hp=5.0, adds=[(GLIM_STRIKER, 'glimmer striker', [45, 46]), (GLIMMERLING, 'glimmerling', [44, 45])], every=20, count=3),
            choice('bc_brid', "Report to Keener Brid",
                   "Dark. The whole bog, dark, the way it should be at night. I could weep.\n\nThe tower is ours now - the Keeners'. We could [break the gems] so nothing can ever look through them again. Or we [keep the gems] and learn to look back through them - north, into the Sheeroe Hills, at him.",
                   [('break the gems', "Broken, then. Nobody looks through Cliodna's eyes again. Nobody.", 'ending:broken'),
                    ('keep the gems', "Kept. And one night soon a Keener will look north through the red one - and the Glimmer King will look back.", 'ending:kept')]),
        ],
        {'broken': {'text': "From the Keeners of Cullen.", 'items': [g8], 'choice': [g7, g9]},
         'kept': {'text': "From the Keeners of Cullen.", 'items': [g8], 'choice': [g7, g9]}},
        requires='bc_badb', group=True)

if __name__ == '__main__':
    for zz in ZONES:
        errs = zz.check()
        print(zz.name, len(zz.quests), 'quests', len(zz.items), 'items', errs or 'ok')
