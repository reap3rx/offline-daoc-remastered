"""Llyn Barfog's story quests (claude 2026-11-24, "Albion - the plan", round 4) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_llyn_barfog

The north thread's end: Morgana's seat. Llyn Barfog, the bearded lake, where the Lady's white cattle came up out of the water,
Arthur's horse left its hoof-print in the stone, and Arthur dragged the Afanc out of the lake. Morgana sits at the Gate of Annwn on
the south shore now: her hounds run the hills, cythraul come up through the gate, the Crimson keep her posts and the Ellyll of the
fay wood are her kin. The Knights of the Lake (Sir Bors, and Sir Percival, who marches the Lake Host: AlbionCampaign.cs) and the
Maidens of the Lake (Lunete, the Lady's own) want the lake back. The stories lead up to the campaign and the raid at the Gate.

The zone's two older quests are kept by id (hounds, psalter), brought up to the zone's levels now it is Elite.

Arcs (recommended levels): The Afanc's Shore (44-46), The Hunt of Annwn (45-48), The Lady's Cattle (46-49), The Last Psalm
(46-48), Morgana's Shore (49-54).
"""
from story_gen import talk, reach, search, kill, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN, M, F, OLD

S = Story(7, 'Llyn Barfog', 'alb_llyn_barfog', 'story007_llyn_barfog', set(), set(), set())
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
CRIMSON, HOUND, CYTH = 12075, 12999, 13001

person('lb_bors', 'Sir Bors de Ganis', (868, 806), 'm', 55, model=28, guild='the Knights of the Lake',
       idle="Percival will march when someone gives him the word. Until then, the Lake's knights hold the merchants, and I hold Percival.")
person('lb_lunete', 'Lunete of the Lake', (858, 772), 'f', 54, guild='the Maidens of the Lake',
       idle="My Lady sleeps under the water. She does not sleep well, with Morgana on her shore.")
# the zone's older people (hounds, psalter)
person('nest', 'Nest ferch Rhys', (886, 798), 'f', 40, idle="Have you heard them? At night? Don't listen if you do.")
person('gwion', 'Gwion the Harper', (878, 776), 'm', 42, idle="Every song in this valley ends in the lake. I've tried to write one that doesn't.")
person('teilo', 'Brother Teilo', (890, 796), 'm', 44, idle="Every brother in my house is dead and still walking. I am the only one who stayed dead-tired instead.")
z.npc('iolo', 'Iolo ap Rhys', [838, 1312], 'm', 42, during=['hounds/iolo', 'hounds/horn'])
z.npc('elfodd', 'Abbot Elfodd', [1324, 154], 'm', 46, during=['psalter/abbot', 'psalter/release'])

# ======================================================================== The Afanc's Shore (44-46)
a1 = z.item("Toad-Hide Bracer", 'bracer', 44, 'ward', "Diamond-backed, and still faintly poisonous.")
a2 = z.item("Lake-Knight's Ring", 'ring', 44, 'might', "Plain silver, with a wave cut in it.")
z.quest('lb_toads', 'The Diamondbacks', 44, 'lb_bors',
        "Diamondback toads on the north shore - big as ponies, and they spit. They never came out of the shallows before Morgana came. Now they sit on the road.\n\nWill you [clear the shore]?",
        'clear the shore',
        "Diamondback toads have come up out of the shallows onto Llyn Barfog's north shore.",
        [
            hunt((990, 470), "Kill the diamondback toads " + where((990, 470), 'lb_bors'), 'diamondback toad', 6),
            end_talk('lb_bors', "Tell Sir Bors", "Good. The road's open - and now you've seen the north shore, you've seen why we can't hold it yet.", 'default'),
        ],
        {'default': {'text': "From the Knights of the Lake.", 'choice': [a1, a2]}})

a3 = z.item("Hatchling-Tooth Charm", 'gem', 45, 'might', "A tooth the length of a finger. From a hatchling.")
a4 = z.item("Carn March Belt", 'belt', 45, 'finesse', "Stamped with a hoof-print.")
a5 = z.item("Shore-Watch Mantle", 'cloak', 45, 'ward', "Lake-blue, with a knight's white border.")
z.quest('lb_hatchlings', "The Afanc's Brood", 45, 'lb_bors',
        "Arthur dragged the Afanc out of this lake with chains and oxen, and that was the end of it - so the story goes. Then why are there afanc hatchlings on the north shore?\n\nSomething is breeding them. Will you [find out what]?",
        'find out what',
        "Afanc hatchlings are breeding on Llyn Barfog's north shore - and the Afanc was killed long ago.",
        [
            hunt((960, 520), "Kill the afanc hatchlings " + where((960, 520), 'lb_bors'), 'afanc hatchling', 5),
            search(Z, P(1060, 340), "Search Carn March Arthur, the hoof-stone in the northern hills", "a stone with a hoof-print, under a red chain", CRATE,
                   "Arthur's horse left its hoof-print here when he dragged the Afanc out. Someone has chained a Crimson ward-stone over the print, and written on it: 'What the King took out, the Queen puts back.'"),
            end_talk('lb_bors', "Tell Sir Bors", "'What the King took out, the Queen puts back.' She's raising the Afanc. Gods. Percival needs to hear this.", 'default'),
        ],
        {'default': {'text': "From the Knights of the Lake.", 'choice': [a3, a4, a5]}}, requires='lb_toads')

a6 = z.item("Gatekeeper's Red Key", 'gem', 46, 'mind', "A red key under a little crown. It opens nothing you can find.")
a7 = z.item("Ward-Breaker's Bracer", 'bracer', 46, 'might', "Iron, dented from breaking stones.")
z.quest('lb_gatekeeper', 'The Ward on the Shore', 46, 'lb_bors',
        "The Crimson keep a post on the Afanc's shore, and a gatekeeper who chains wards over every stone Arthur ever touched. Break him and the shore is ours to march on.\n\nIt's not a one-sword job. Will you [break the post]?",
        'break the post',
        "A Crimson gatekeeper keeps Morgana's post on the Afanc's shore.",
        [
            boss(Z, P(1000, 520), "Defeat the Crimson gatekeeper on the Afanc's shore", "The gatekeeper falls across his own ward-stones, and the red chains go slack.",
                 'Gatekeeper Hywel Redkey', CRIMSON, 50, "A man in crimson with a ring of red keys steps out of the post: 'Every door has a keeper. This one's mine.'",
                 objective='Defeat Gatekeeper Hywel Redkey', hp=3, adds=[(CRIMSON, 'crimson acolyte', [46, 47])], every=30, count=2),
            end_talk('lb_bors', "Tell Sir Bors", "The ward's broken. Now when the Host marches, it has a shore to stand on. Percival thanks you - I thank you louder.", 'default'),
        ],
        {'default': {'text': "From the Knights of the Lake.", 'choice': [a6, a7]}}, requires='lb_hatchlings', group=True)

# ======================================================================== The Hunt of Annwn (45-48) - the older quest, brought up
it_horn2 = z.item('Horn of the Hunt', 'gem', 45, 'finesse', "A small, curling horn of black bone. The hounds know whoever carries it.")
it_annwn = z.item('Cwn Annwn Collar', 'neck', 45, 'might', "A red leather collar with a silver bell. The bell does not ring.")
it_harp = z.item("Harper's Cord", 'belt', 45, 'mind', "Strung with old harp strings, each one tuned.")
it_nest = z.item("Nest's Shawl", 'cloak', 45, 'ward', "Thick Welsh wool, red and black. She made it for Iolo's wedding gift.")
z.quest('hounds', 'The Hounds of Annwn', 45, 'nest',
        "My husband Iolo heard the hounds of Annwn three nights ago. The white hounds with red ears. Whoever hears them dies within the year - everybody knows that.\n\nIolo isn't one to wait for it. He took his spear and went to hunt them, to break the doom. Gwion the [harper] knows the old stories. Will you [go after Iolo]?",
        'go after Iolo',
        "Iolo heard the hounds of Annwn - a death omen - and went to hunt them rather than wait to die.",
        [
            talk('gwion', 'Ask Gwion the harper about the hounds',
                 "The Cwn Annwn hunt from the old stones south of here, on the slopes. Their master is a huntsman of the Otherworld. The story goes, if a living man blows the huntsman's horn, the hunt passes him by - but the doom must fall on someone. They always find someone. Iolo will go to the [stones].", kw='stones'),
            kill(7, [915, 1185], 'Hunt the hounds of Annwn on the slopes', 'cwn annwn', HOUND, [44, 45], 5,
                 text="They don't bleed. They fade, like breath on cold glass. Further south, a horn calls."),
            search(7, [868, 1342], 'Search the old stones in the south', "a dropped hunting spear", CRATE,
                   "Iolo's spear, the shaft bitten through. A trail of blood to the west - and the hunt's horn calling again, very close."),
            boss(7, [840, 1320], "Defeat the huntsman of Annwn", "The huntsman lowers his horn and looks at you a long while. Then he and his hounds are gone, and only the horn lies on the grass.",
                 "Gwyn's Huntsman", CYTH, 48, "A tall grey figure rides out of nothing on a horse of mist, the white hounds at its heels. It lifts a horn.",
                 objective="Defeat Gwyn's Huntsman", hp=2.4, adds=[(HOUND, 'cwn annwn', [44, 45])], every=25, count=2),
            L('iolo', talk('iolo', 'Find Iolo', "You came for me? Nest sent you. Course she did.\n\nI heard it, you know. In the howling. My own name. They've marked me. I'm marked. Unless the [horn]...", kw='horn')),
            L('horn', choice('iolo', 'Decide what to do with the horn',
                   "If I blow it, the hunt passes me by - and the doom falls on whoever's near. On you, maybe. I won't do that.\n\nIf YOU [blow it], it falls on you. Gods, don't. Or we [break it], and I take what's coming. A year. A year is something.",
                   [('blow it', "No - you - ...\n\nListen. They're going. Far off. They're running the other way. They know your name now, friend. I'm sorry. I'm so sorry, and so grateful I can't stand up.", 'next:blown'),
                    ('break it', "Yes. Yes. A year with Nest. That's more than most men get. Come on, help me up.", 'next:broken')])),
            L('blown', end_talk('nest', 'Bring Iolo home to Nest', "He's home, and he says the doom is gone - and he won't tell me where it went.\n\nI can guess. Thank you. I don't know what else to say. Take this. Be careful at night.", 'blown')),
            L('broken', end_talk('nest', 'Bring Iolo home to Nest', "A year. He told me. He broke the horn and he chose a year with me, and he's smiling like a boy about it.\n\nI'll make it the best year of his life. Here. For bringing him home to have it.", 'broken')),
        ],
        {'blown': {'text': "Take this. Be careful at night.", 'items': [it_horn2], 'choice': [it_annwn, it_harp]},
         'broken': {'text': "For bringing him home.", 'tragic': True, 'items': [it_nest], 'choice': [it_annwn, it_harp]}},
        topics={'harper': "Gwion. He sits by the smithy, playing to anyone who'll stand still."})

h1 = z.item("Huntsman's Grey Mantle", 'cloak', 48, 'ward', "Grey as mist, and as hard to hold.")
h2 = z.item("Annwn-Bone Ring", 'ring', 48, 'finesse', "White bone that is cold to the touch, always.")
h3 = z.item("Red-Ear Torc", 'neck', 48, 'might', "Twisted from a hound's red-dyed leash.")
z.quest('lb_huntsman', 'Master of the Hunt', 48, 'gwion',
        "Gwyn's huntsman was one rider of the hunt. The hunt's MASTER rides the western shore now - the Huntsman of Annwn, Morgana's own, with his pack. While he rides, every night in this valley is a doom for someone.\n\nThis needs a group, and courage. Will you [end the hunt]?",
        'end the hunt',
        "The Huntsman of Annwn, master of Morgana's hounds, rides Llyn Barfog's western shore.",
        [
            hunt((300, 1000), "Bring down the Huntsman of Annwn " + where((300, 1000), 'gwion'), 'the Huntsman of Annwn', 1, r=70),
            end_talk('gwion', "Tell Gwion the Harper", "No horn tonight. No horn for a long while.\n\nI'll write it. A song about the valley that doesn't end in the lake. You've given me the ending.", 'default'),
        ],
        {'default': {'text': "From Gwion the Harper.", 'choice': [h1, h2, h3]}}, requires='hounds', group=True)

# ======================================================================== The Lady's Cattle (46-49)
c1 = z.item("White-Hide Bracer", 'bracer', 46, 'faith', "White as milk, soft as moss. Lake-cattle hide, freely given.")
c2 = z.item("Herd-Bell Charm", 'gem', 46, 'charm', "A small bronze bell. It rings only near water.")
z.quest('lb_cattle', "The Lady's Cattle", 46, 'lb_lunete',
        "Do you know why this is the bearded lake? A maiden came up out of it with white cattle, and gave them to the farmers of the valley - and when a greedy man would have slaughtered one, she called them home under the water.\n\nThe bwgan have driven off the last of her herd, to feed Morgana's hounds. Will you [find the herd]?",
        'find the herd',
        "The bwgan of the north-west hills have driven off the Lady of the Lake's white cattle to feed Morgana's hounds.",
        [
            hunt((470, 400), "Drive off the bwgan hunters " + where((470, 400), 'lb_lunete'), 'bwgan hunter', 3),
            search(Z, P(500, 380), "Search the bwgan pens", "a broken pen, white hairs caught on the rails", CRATE,
                   "Empty. White hairs on every rail, and tracks going north into the hills - big tracks, bigger than any bwgan's, walking beside the cattle."),
            end_talk('lb_lunete', "Tell Lunete of the Lake", "North, into the hills. With something big walking beside them. I know who that is. Everyone in this valley knows who that is.", 'default'),
        ],
        {'default': {'text': "From the Maidens of the Lake.", 'choice': [c1, c2]}})

c3 = z.item("Cythraul-Horn Charm", 'gem', 47, 'mind', "A black horn tip. It smells of burnt stone.")
c4 = z.item("Lake-Maiden's Ring", 'ring', 47, 'faith', "Silver, cold, and always a little wet.")
z.quest('lb_cythraul', 'Up Through the Gate', 47, 'lb_lunete',
        "The cythraul are Annwn's - demons of the deep places. They come up through Morgana's gate a few at a time, and walk the bwgan hills looking for anything alive.\n\nWill you [send them back]?",
        'send them back',
        "Cythraul, demons of Annwn, come up through Morgana's gate and walk Llyn Barfog's north-west hills.",
        [
            hunt((560, 430), "Send the cythraul back " + where((560, 430), 'lb_lunete'), 'cythraul', 6),
            end_talk('lb_lunete', "Tell Lunete of the Lake", "Back where they came from. My Lady felt every one go. She says thank you, which she does not say often.", 'default'),
        ],
        {'default': {'text': "From the Maidens of the Lake.", 'choice': [c3, c4]}})

c5 = z.item("Hill-King's Crown-Shard", 'gem', 49, 'might', "A shard of rough gold. The King of the Barfog Hills wore it as a crown.")
c6 = z.item("White Cow's Bell-Collar", 'neck', 49, 'faith', "A bronze bell on a white leather collar.")
c7 = z.item("Lake-Herder's Mantle", 'cloak', 49, 'ward', "Green wool, smelling faintly of rain and cattle.")
z.quest('lb_hill_king', 'The King of the Barfog Hills', 49, 'lb_lunete',
        "The King of the Barfog Hills. He's no king - a great beast of the northern hills that calls itself one - but Morgana has bought him with the Lady's own cattle, and he keeps the last white cow in his den.\n\nIt's a fight for a group. Will you [bring her home]?",
        'bring her home',
        "The King of the Barfog Hills keeps the Lady of the Lake's last white cow in his den in the northern hills.",
        [
            hunt((682, 247), "Bring down the King of the Barfog Hills " + where((682, 247), 'lb_lunete'), 'King of the Barfog Hills', 1, r=70),
            choice('lb_lunete', "Tell Lunete of the Lake",
                   "She's alive? The last of them. I can [call her home], under the water, where Morgana can't reach her - and the valley will never see the white cattle again. Or she can go to [the farmers], to Gwartheg Yllyn at the east gate, and the herd can begin again on the land, the way my Lady meant it.",
                   [('call her home', "Then she goes home. Listen - you'll hear her bell under the water on still nights.", 'ending:home'),
                    ('the farmers', "Then the valley has its cattle again. My Lady will be glad - she always liked farmers better than kings.", 'ending:farm')]),
        ],
        {'home': {'text': "From the Maidens of the Lake.", 'items': [c6], 'choice': [c5, c7]},
         'farm': {'text': "From the Maidens of the Lake.", 'items': [c7], 'choice': [c5, c6]}}, requires='lb_cattle', group=True)

# ======================================================================== The Last Psalm (46-48) - the older quest, brought up
it_psalter = z.item("Abbot's Psalter Charm", 'gem', 47, 'faith', "A single vellum page in a silver case. The psalm on it is for the dead.")
it_vigil = z.item('Vigil Cloak', 'cloak', 47, 'ward', "A monk's heavy brown cloak. Ghosts of soldiers once stood watch over it.")
it_evoc = z.item("Evocatus' Ring", 'ring', 47, 'might', "A veteran soldier's ring, bearing the mark of a legion long gone.")
it_quill = z.item("Copyist's Bracer", 'bracer', 47, 'mind', "Ink-stained leather. The abbey's copyists wore them for three hundred years.")
z.quest('psalter', 'The Last Psalm', 47, 'teilo',
        "I'm the last brother of the abbey in the north - the last living one. Thirty years ago our abbot made a pact with the ghosts of an old legion: they would guard our house from raiders. They did. They guarded it from everything.\n\nThis winter my brothers died one by one, and rose again, and went back to their prayers. I ran. I am not proud of it. Will you [go to the abbey]? The abbot's psalter holds the pact. Perhaps it holds a way out.",
        'go to the abbey',
        "Brother Teilo's abbey made a pact with the ghosts of a Roman legion, and now his dead brothers walk.",
        [
            reach(7, [1260, 236], 'Climb the road to the abbey in the north', "The abbey bell is ringing for vespers. Hooded monks walk the cloister in pairs. None of them cast a shadow.", r=20),
            kill(7, [1312, 177], "Free the dead brothers of the abbey", 'undead monk', 13034, [45, 46], 6,
                 text="Each one says 'thank you' as it falls."),
            search(7, [1332, 162], "Find the abbot's psalter", "a chained psalter on a lectern", CRATE,
                   "The pact is written in the margin of the psalm for the dead: 'Guard this house until the last brother leaves it.' And Teilo left.",
                   give="the abbot's psalter"),
            L('abbot', talk('elfodd', 'Speak with the ghost of Abbot Elfodd',
                 "You have the psalter. Good. I made the pact. I meant it for our protection. The legion took it to the letter, as soldiers do - the last brother left, so the house is theirs, and so are we.\n\nTheir veteran, Decimus, holds the pact. Break him, and I can [read the last psalm].", kw='read the last psalm')),
            boss(7, [1318, 172], "Defeat Decimus, keeper of the pact", "The old soldier salutes you as he fades. 'Relieved. At last.'",
                 'Evocatus Decimus', 13010, 49, "An old soldier in a red cloak plants himself in the cloister. 'This house is under guard. Stand down.'",
                 objective='Defeat Evocatus Decimus', hp=2.5, adds=[(13034, 'undead monk', [45, 46])], every=30, count=2),
            L('release', choice('elfodd', 'Choose with the abbot',
                   "Now I can read it - the last psalm, and every brother here goes to his rest, myself among them. The abbey will stand empty, and the raiders will come, and the valley will have no one to shelter it.\n\nOr we [keep watch], the dead brothers and I, without the legion - and the valley keeps its shelter. Teilo would have to live with that. Tell me: do I [read the psalm]?",
                   [('read the psalm', "Then listen. ... It's been a long time since I could hear myself sing.", 'next:rest'),
                    ('keep watch', "Then we watch. Tell Teilo we are not angry. Tell him to visit, if he can bear it.", 'next:watch')])),
            L('rest', end_talk('teilo', 'Return to Brother Teilo', "I heard them. All the way down here. Singing - all of them, the old psalm. And then the bell stopped.\n\nI'll go back in the spring and sweep the chapel. Somebody should.", 'rest')),
            L('watch', end_talk('teilo', 'Return to Brother Teilo', "They're keeping watch. Still. Without the legion.\n\nI'll visit. I'll bring bread they can't eat and news they can't use. I suppose that's what brothers are for.", 'watch')),
        ],
        {'rest': {'text': "Take this, from the abbey.", 'items': [it_psalter], 'choice': [it_evoc, it_quill]},
         'watch': {'text': "Take this, from the abbey.", 'tragic': True, 'items': [it_psalter], 'choice': [it_vigil, it_evoc]}})

p1 = z.item("Legion-Pact Signet", 'ring', 48, 'might', "Bronze, with an eagle and a cross scratched over it.")
p2 = z.item("Cloister-Stone Bracer", 'bracer', 48, 'ward', "Grey, cold, and heavier than it looks.")
z.quest('lb_legion', 'The Legion of the Pact', 48, 'teilo',
        "The abbot's pact is broken, one way or the other - but the legion's dead didn't all go with Decimus. Some still march round the abbey walls, and they've begun stopping travellers on the north road.\n\nWill you [relieve the watch]? Soldiers like to be relieved.",
        'relieve the watch',
        "The dead legionaries of the abbey's broken pact still march round its walls and stop travellers on the north road.",
        [
            hunt((1290, 200), "Relieve the legionaries of the pact " + where((1290, 200), 'teilo'), 'legionary of the pact', 5),
            end_talk('teilo', "Tell Brother Teilo", "Relieved. That's the word Decimus used, isn't it? I hope it's the word they all use.", 'default'),
        ],
        {'default': {'text': "From Brother Teilo.", 'choice': [p1, p2]}}, requires='psalter')

# ======================================================================== Morgana's Shore (49-54)
m1 = z.item("Crimson Letter-Case", 'gem', 49, 'mind', "Red leather, sealed with a red key under a crown.")
m2 = z.item("Acolyte's Red Cord", 'belt', 49, 'finesse', "A red cord, cut. It doesn't bind anyone now.")
z.quest('lb_letters', 'The Still Night', 49, 'lb_lunete',
        "The Crimson in the bwgan hills carry letters to and from the Gate. If we knew what Morgana waits for, we'd know how long we have.\n\nWill you [take a letter]?",
        'take a letter',
        "Crimson acolytes carry Morgana's letters between the bwgan hills and the Gate of Annwn.",
        [
            hunt((560, 430), "Kill the crimson acolytes carrying letters " + where((560, 430), 'lb_lunete'), 'crimson acolyte', 6),
            search(Z, P(580, 440), "Search the Crimson post for letters", "a red satchel under a bedroll", BEDROLL,
                   "One letter, in Morgana's own hand: 'The Gate opens on the night the lake is still. The Afanc wakes first. Mordred walks second. Then I walk Annwn's dead into Camelot.'",
                   give="Morgana's letter"),
            end_talk('lb_lunete', "Bring the letter to Lunete of the Lake", "The night the lake is still. It's never still - my Lady keeps it moving, every night, to keep that gate shut. She's tiring.\n\nSo we haven't long. Percival has to march.", 'default'),
        ],
        {'default': {'text': "From the Maidens of the Lake.", 'choice': [m1, m2]}})

m3 = z.item("Fay-Knight's Gorget", 'neck', 51, 'ward', "Green steel, worked like leaves. It hums.")
m4 = z.item("Ellyll-Thorn Bracer", 'bracer', 51, 'finesse', "Bark and thorn, grown, not made.")
m5 = z.item("Glamour-Broken Ring", 'ring', 51, 'mind', "It looked like gold. It's tin. That's the point.")
z.quest('lb_fay_knights', 'The Fay Wood', 51, 'lb_bors',
        "Morgana is a fay - half of her is - and the Ellyll of the south-west wood are her kin. Her fay knights ride out of that wood in green steel, and cut down anything that comes near the Gate from the west.\n\nA group's work. Will you [ride into the wood]?",
        'ride into the wood',
        "Morgana's fay knights ride out of the Ellyll wood in Llyn Barfog's south-west and guard the Gate from the west.",
        [
            hunt((500, 1300), "Cut down Morgana's fay knights " + where((500, 1300), 'lb_bors'), 'fay knight', 4),
            end_talk('lb_bors', "Tell Sir Bors", "Green steel and glamour. Strip the glamour and they bleed like anyone. Good.", 'default'),
        ],
        {'default': {'text': "From the Knights of the Lake.", 'choice': [m3, m4, m5]}}, requires='lb_letters', group=True)

m6 = z.item("Branwen's Gate-Seal", 'gem', 53, 'might', "A seal of black glass. The Gate's mark is on it - an open hand.")
m7 = z.item("Gate-Captain's Belt", 'belt', 53, 'ward', "Black leather with a red key for a buckle.")
m8 = z.item("Knight of the Lake's Mantle", 'cloak', 53, 'faith', "White and blue, the Lake's own. Sir Bors's gift.")
z.quest('lb_branwen', 'The Gate-Captain', 53, 'lb_bors',
        "Gate-Captain Branwen holds the south shore for Morgana. She chose this - she was a knight of the Lake once, before Morgana made her promises. Whatever the Host does, it does nothing while Branwen holds the shore.\n\nBring a group. Will you [face Branwen]?",
        'face Branwen',
        "Gate-Captain Branwen, a knight of the Lake turned to Morgana, holds the south shore before the Gate of Annwn.",
        [
            hunt((870, 1300), "Defeat Gate-Captain Branwen " + where((870, 1300), 'lb_bors'), 'Gate-Captain Branwen', 1, r=70),
            end_talk('lb_bors', "Tell Sir Bors", "She was a good knight. Better than me, once.\n\nThe shore is open. Go and see Lunete - she's been looking at the lake all day, and she won't say why.", 'default'),
        ],
        {'default': {'text': "From the Knights of the Lake.", 'choice': [m6, m7, m8]}}, requires='lb_fay_knights', group=True)

m9 = z.item("Lady's Promise", 'gem', 54, 'faith', "A drop of lake-water in crystal. It never dries.")
m10 = z.item("Sword-Oath Ring", 'ring', 54, 'might', "Silver, with a sword rising out of water.")
m11 = z.item("Old-Ways Torc", 'neck', 54, 'charm', "A torc of twisted reed and silver.")
z.quest('lb_lady', 'The Lady of the Lake', 54, 'lb_lunete',
        "Come to the shore with me. Near the Gate - not too near. The lake went still at noon, and it hasn't moved since.\n\nMy Lady is waiting for you. Will you [come to the shore]?",
        'come to the shore',
        "Llyn Barfog has gone still, and the Lady of the Lake waits on the south shore.",
        [
            reach(Z, P(700, 1170), "Go to the south shore, near the Gate of Annwn", "The water is flat as glass. A woman stands on it - not in it, ON it - in white, with water running from her hair. Behind her, on the far shore, the Gate is a black arch, and there is something moving in it.", r=25),
            choice('lb_lunete', "Hear the Lady of the Lake",
                   "(Lunete speaks for her; the Lady's lips do not move.)\n\n'I gave Arthur his sword. I took it back. I held this gate shut for him, and after him, and I am tired. Morgana is my sister in craft, and she will win if no one stands with me.\n\n'Swear to the [sword], and stand with my knights when Percival marches. Or keep [the old ways], and stand with my maidens. Either way - stand.'",
                   [('sword', "'Then you are a knight of the Lake, whatever your arms. Go to Percival.'", 'ending:sword'),
                    ('the old ways', "'Then you are my maidens' friend, whatever your name. Go to Percival - he needs the old ways too.'", 'ending:ways')]),
        ],
        {'sword': {'text': "From the Lady of the Lake. Sir Percival waits at the merchants: give him the word when you're ready to march.", 'items': [m10], 'choice': [m9, m11]},
         'ways': {'text': "From the Lady of the Lake. Sir Percival waits at the merchants: give him the word when you're ready to march.", 'items': [m11], 'choice': [m9, m10]}},
        requires='lb_branwen')
