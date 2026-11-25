"""Malmohus's story quests (claude 2026-11-25, "Midgard - the plan", round 4) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_malmohus

Elite. The south thread's end: Gjalpinulva sleeps in her lair; her drakulv and the svartalf they bought hold every road to the
Wyrm-Temple, where the Hierophant keeps the rite and waits for the other half of her true name. Halla's camp is the Oath's muster
for the Dragon-Oath (AlbionCampaign.cs / MidgardCampaigns.cs): these quests walk the south ahead of it and end at Volva Groa, come
south from Myrkwood with the half-name.

The zone's two older quests are kept (missionary, brought up to the Elite band; svartalf_steel).

Arcs (recommended levels): The Missionary Road (50-53), The Foist (52-55), The Lines (54-56), The Temple Steps (56-59).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(116, 'Malmohus', 'mid_malmohus', 'story116_malmohus', {'missionary', 'svartalf_steel'},
          {'halla', 'bjorn_convert', 'svein_smith'},
          {"Convert's Scale-Pendant", "Halla's Hunting Cloak", "Sacrificer's Knife-Ring", "Bjorn's Prayer-Belt", 'Svartalf-Steel Bracer',
           "Hammerhand's Ring", "Alchemist's Phial-Belt", "Foister's Cloak", 'Bloodbinder Torc'}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157
for q in z.quests:
    if q['id'] == 'missionary':
        q['level'] = 50                    # (brought up to the Elite band)

person('mh_asa', 'Volva Asa', (1015, 505), 'f', 54, model=OLD, guild='the Oath of the Volur',
       idle="The volur came south with the Oath. We'll go home with it, or not at all.")
person('mh_ketil', 'Huscarl Ketil', (995, 515), 'm', 54, model=M, guild="King Eirik's Huscarls",
       idle="The King lent the volur his huscarls. He wants them back. Most of them.")

O, H = "From the Oath of the Volur.", "From King Eirik's Huscarls."

# ======================================================================== The Missionary Road (50-53)
a1 = z.item("Road-Breaker's Ring", 'ring', 50, 'might', "Iron, the volur's knot on it.")
a2 = z.item("Missionary-Robe Sash", 'belt', 50, 'mind', "Red cloth, the dragon's eye cut out of it.")
z.quest('mh_missionaries', 'The Missionary Road', 51, 'mh_ketil',
        "Every missionary who ever walked into Midgard came down the road west of here. They still do - and they still walk back with converts.\n\nWill you [close the road]?",
        'close the road',
        "Drakulv missionaries walk Malmohus's missionary road, north into Midgard and back with converts.",
        [
            hunt((500, 300), "Close the road to the drakulv missionaries " + where((500, 300), 'mh_ketil'), 'drakulv missionary', 6),
            end_talk('mh_ketil', "Tell Huscarl Ketil", "Closed, for a day. The Oath will close it for good. The road's the first post we take.", 'default'),
        ],
        {'default': {'text': H, 'choice': [a1, a2]}})

a3 = z.item("Patrol-Breaker's Bracer", 'bracer', 52, 'ward', "Scale-plated, taken off a drakulv.")
a4 = z.item("Convert's Return Charm", 'gem', 52, 'faith', "A little wooden hammer. Bjorn carved it.")
z.quest('mh_patrols', 'The Patrols', 52, 'bjorn_convert',
        "I walked with the drakulv once. I know their patrols - they walk the north roads in fours, and they take anyone alone. Break them.\n\nWill you [break the patrols]?",
        'break the patrols',
        "Patrolling drakulv walk Malmohus's north roads in fours and take anyone alone.",
        [
            hunt((700, 450), "Break the patrolling drakulv " + where((700, 450), 'bjorn_convert'), 'patrolling drakulv', 6),
            end_talk('bjorn_convert', "Tell Bjorn the Convert", "Good. I prayed to her once. Now I pray she stays asleep.", 'default'),
        ],
        {'default': {'text': H, 'choice': [a3, a4]}}, requires='mh_missionaries')

# ======================================================================== The Foist (52-55)
s1 = z.item("Infiltrator's Shadow Ring", 'ring', 52, 'finesse', "Black glass. You can't see your hand through it.")
s2 = z.item("Foist-Watcher's Cloak", 'cloak', 52, 'ward', "Grey, for lying still.")
z.quest('mh_infiltrators', 'The Infiltrators', 53, 'svein_smith',
        "Svartalf infiltrators creep up to the camp at night - they want my forge-marks, my steel. They sell everything to the drakulv.\n\nWill you [hunt them]?",
        'hunt them',
        "Svartalf infiltrators creep up to Halla's camp at night for the drakulv.",
        [
            hunt((1250, 350), "Hunt the svartalf infiltrators " + where((1250, 350), 'svein_smith'), 'svartalf infiltrator', 5),
            end_talk('svein_smith', "Tell Svein Hammerhand", "Good. Every one is a forge-mark they won't sell.", 'default'),
        ],
        {'default': {'text': H, 'choice': [s1, s2]}})

s3 = z.item("Bloodbinder's Rune-Torc", 'neck', 55, 'mind', "Dragon-runes on dark iron - broken.")
s4 = z.item("Blood-Ward Bracer", 'bracer', 55, 'faith', "The volur's knot over the svartalf's runes.")
s5 = z.item("Scale-Price Ring", 'ring', 55, 'might', "Paid for in scale. Yours now.")
z.quest('mh_bloodbinders', 'The Bloodbinders', 55, 'mh_asa',
        "The svartalf bloodbinders in the foist bind their own blood to the dragon's for her scale. They're her svartalf now - and they keep the foist warded.\n\nBring friends. Will you [break the bloodbinders]?",
        'break the bloodbinders',
        "Svartalf bloodbinders bind their blood to Gjalpinulva's in the Svartalf Foist.",
        [
            hunt((1400, 600), "Break the svartalf bloodbinders " + where((1400, 600), 'mh_asa'), 'svartalf bloodbinder', 3, r=60),
            search(Z, P(1405, 610), "Search the bloodbinders' altar", "a bowl of dark blood and red scale", CRATE,
                   "The blood in the bowl moves on its own. Scratched under it: 'For the Mother's waking. When the Hierophant has her name, every bound drop wakes with her.'"),
            end_talk('mh_asa', "Tell Volva Asa", "Every bound drop wakes with her. The svartalf don't know what they sold. The foist is the second post - the Oath will break it.", 'default'),
        ],
        {'default': {'text': O, 'choice': [s3, s4, s5]}}, requires='mh_infiltrators', group=True)

# ======================================================================== The Lines (54-56)
l1 = z.item("Varg-Scale Belt", 'belt', 54, 'ward', "Scaled varg hide, very tough.")
l2 = z.item("Snarler-Fang Ring", 'ring', 54, 'might', "A varg's fang, set in bronze.")
z.quest('mh_vargs', "The Drakulv's Hounds", 54, 'halla',
        "The scaled vargs - the drakulv breed them, half wolf, half drake. They run the backwoods and the lines. I hunt them, when I can.\n\nWill you [hunt with me]?",
        'hunt with me',
        "The drakulv's scaled vargs, half wolf and half drake, run Malmohus's backwoods.",
        [
            hunt((400, 700), "Hunt the scaled varg snarlers " + where((400, 700), 'halla'), 'scaled varg snarler', 5),
            end_talk('halla', "Tell Halla Bjornsdottir", "Good hunting. I'll make a cloak of the next one.", 'default'),
        ],
        {'default': {'text': H, 'choice': [l1, l2]}}, requires='mh_patrols')

l3 = z.item("Armguard's Scale Bracer", 'bracer', 55, 'ward', "A drakulv armguard's bracer, the scale still warm.")
l4 = z.item("Line-Breaker's Torc", 'neck', 55, 'might', "Iron, hammered flat with an axe-head.")
z.quest('mh_armguards', 'The Armguard Lines', 55, 'mh_ketil',
        "The drakulv dig in across the middle of Malmohus - armguards and axehands. Thin them, and the Oath can take the lines.\n\nWill you [thin the lines]?",
        'thin the lines',
        "Drakulv armguards and axehands dig in across the middle of Malmohus.",
        [
            hunt((550, 850), "Thin the drakulv armguards " + where((550, 850), 'mh_ketil'), 'drakulv armguard', 5),
            hunt((900, 950), "Thin the drakulv axehands", 'drakulv axehand', 3),
            end_talk('mh_ketil', "Tell Ketil", "Thinner. The sacrificers on the lines keep the rite going for the temple. Asa wants to hear about them.", 'default'),
        ],
        {'default': {'text': H, 'choice': [l3, l4]}}, requires='mh_vargs')

l5 = z.item("Sacrificer's Rite-Knife Charm", 'gem', 56, 'mind', "A knife of red scale, the edge dulled now.")
l6 = z.item("Oath-Keeper's Mantle", 'cloak', 56, 'faith', "Volur grey, the Oath's knot on the back.")
l7 = z.item("Rite-Breaker's Ring", 'ring', 56, 'might', "Silver, cut with the volur's runes.")
z.quest('mh_sacrificers', 'The Rite', 56, 'mh_asa',
        "The sacrificers keep the rite burning on the lines - blood and fire, to keep the dragon's sleep light, so she'll wake quick when her name's spoken.\n\nBring friends. Will you [break the rite]?",
        'break the rite',
        "Drakulv sacrificers keep the rite burning on Malmohus's lines to keep Gjalpinulva's sleep light.",
        [
            hunt((900, 900), "Break the drakulv sacrificers " + where((900, 900), 'mh_asa'), 'drakulv sacrificer', 3, r=60),
            search(Z, P(905, 905), "Search the rite-fire", "a scroll in a scale case, half-burnt", CRATE,
                   "The Hierophant's hand: 'The Mother's name is two halves. I have the first. The volva at Galplen has the second - she has fled south with the Oath. When she stands before my temple, I will have it from her.'"),
            end_talk('mh_asa', "Tell Asa", "She's come south. Groa. She brought the half-name to us - and the Hierophant wants her to stand at his temple. Then we'll give him what he wants: Groa at his temple, and the Oath behind her.", 'default'),
        ],
        {'default': {'text': O, 'choice': [l5, l6, l7]}}, requires='mh_armguards', group=True)

# ======================================================================== The Temple Steps (56-59)
t1 = z.item("Protector's Scale Ring", 'ring', 57, 'ward', "Red scale in black iron.")
t2 = z.item("Temple-Step Belt", 'belt', 57, 'might', "Scorched leather, scale-studded.")
z.quest('mh_protectors', 'The Temple Steps', 57, 'mh_ketil',
        "The drakulv protectors hold the temple steps, with their executioners. They're the best the dragon has.\n\nWill you [thin the steps]?",
        'thin the steps',
        "Drakulv protectors and executioners hold the steps of the Wyrm-Temple.",
        [
            hunt((600, 1150), "Thin the drakulv protectors " + where((600, 1150), 'mh_ketil'), 'drakulv protector', 5),
            end_talk('mh_ketil', "Tell Ketil", "Thinner. The disciples in the west of the steps - they're the Hierophant's own. Asa wants them.", 'default'),
        ],
        {'default': {'text': H, 'choice': [t1, t2]}}, requires='mh_sacrificers')

t3 = z.item("Soultrapper's Gem Charm", 'gem', 58, 'mind', "A gem with something moving in it. Don't look too long.")
t4 = z.item("Disciple-Breaker's Bracer", 'bracer', 58, 'faith', "Volur silver over drakulv scale.")
t5 = z.item("Volva's Ward-Mantle", 'cloak', 58, 'ward', "Grey wool, nine knots on the hem.")
z.quest('mh_disciples', "The Hierophant's Disciples", 58, 'mh_asa',
        "The Hierophant's own disciples and soultrappers. They carry his half of the name between them, a syllable each. Break them, and he has only what he carries himself.\n\nBring friends. Will you [break the disciples]?",
        'break the disciples',
        "The Hierophant's disciples and soultrappers carry his half of Gjalpinulva's name.",
        [
            hunt((460, 1240), "Break the drakulv disciples " + where((460, 1240), 'mh_asa'), 'drakulv disciple', 3, r=60),
            hunt((460, 1240), "Break the drakulv soultrappers", 'drakulv soultrapper', 2, r=60),
            end_talk('mh_asa', "Tell Asa", "Broken. He has his half, and nothing else now. Go to Groa.", 'default'),
        ],
        {'default': {'text': O, 'choice': [t3, t4, t5]}}, requires='mh_protectors', group=True)

t6 = z.item("Dragon-Oath Ring", 'ring', 59, 'faith', "The Oath, in silver. You swore it.")
t7 = z.item("Lair-Road Belt", 'belt', 59, 'might', "Huscarl leather, scorched.")
z.quest('mh_oath', 'The Dragon-Oath', 59, 'mh_asa',
        "Look at the temple from the hill - see what's waiting. Then go to Volva Groa, here in the camp, and swear the Oath.\n\nWill you [look at the temple]?",
        'look at the temple',
        "The Oath of the Volur means to march on the Wyrm-Temple, where the Hierophant waits for Gjalpinulva's name.",
        [
            reach(Z, P(1000, 1250), "Climb the hill above the Wyrm-Temple", "A temple cut into the hill, smoke pouring out of its mouth. Drakulv on every step. And south-west, in the dark of the lair, something vast breathing slowly.", r=25),
            end_talk('mh_asa', "Tell Asa", "Breathing slowly. Not for long.\n\nGo to Volva Groa and swear it - say [by the Oath]. The road, the foist, the lines, the steps, then the temple. It all goes back if we stop.", 'default'),
        ],
        {'default': {'text': O, 'choice': [t6, t7]}}, requires='mh_disciples')
