"""Dartmoor's story quests (claude 2026-11-24, "Albion - the plan", round 4) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_dartmoor

The south thread's end: Golestandt's lair. The white dragon that fled Vortigern's tower is awake in his lair in the south of the
moor, and every giant of Dartmoor marches to his tune: the Stonecrush dig him a road north, the herdsmen drive the ponies off the
moor, the stonecallers sing in their ring, and the stonelords sit round old Gogmagog's empty throne - Gogmagog, the last giant king
of Albion, whom Corineus threw off the Cornish cliffs - waiting for the dragon to give them a king again: Cormoran of the Mount. Grimspound, the quarry
town that keeps an oath with the giants, is caught in the middle. The Dragon-Watch (Bryn Asquith's slayers; Sir Constantine of
Cornwall marches it: AlbionCampaign.cs) and the Quarry-Oath of Grimspound (Mirela Stonewright, Quarry-Mother Hedda) want the moor
back. The stories lead up to the campaign, the raid on the Giants' Throne, and the dragon.

The zone's two older quests are kept as they were (quarry_oath, dragons_tithe).

Arcs (recommended levels): The Diggings (50-52), The Pony Moor (51-53), The Stonecallers' Ring (54-56), The Pounders' Road
(55-56), The Giants' Throne (57-58).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN, M, F, OLD

S = Story(4, 'Dartmoor', 'alb_dartmoor', 'story004_dartmoor', {'quarry_oath', 'dragons_tithe'},
          {'mirela', 'jory', 'mirela_circle', 'bryn_asquith', 'brother_alun', 'sir_wystan'},
          {'Quarry-Oath Ring', 'Heartstone Pendant', "Jory's Chisel-Pin", 'Granite-Weave Mantle', 'Golestandt Scale Brooch',
           "White Hart Mantle", 'Ash-Grey Signet', "Slayer's Vow-Belt", 'Ember-Heart Bracer'})
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
STONECALLER = 770006

person('dm_hedda', 'Quarry-Mother Hedda', (122, 300), 'f', 56, model=OLD, guild='the Quarry-Oath of Grimspound',
       idle="Seventy years I've kept the oath with the giants. Seventy years they kept it back. Now the dragon sings and they've forgotten every word.")

# ======================================================================== The Diggings (50-52)
d1 = z.item("Excavator's Pick-Pin", 'bracer', 50, 'might', "A pick-head, filed into a bracer-pin.")
d2 = z.item("Dig-Dust Belt", 'belt', 50, 'finesse', "Grey with rock-dust that never quite beats out.")
z.quest('dm_stonecrush', 'The Stonecrush', 50, 'bryn_asquith',
        "The Stonecrush - the giants' diggers, broad as doors - came up the west valley a month ago, and they haven't stopped digging since. Every day closer to Grimspound.\n\nWill you [stop the digging]?",
        'stop the digging',
        "The Stonecrush, the giants' diggers, are digging up Dartmoor's west valley toward Grimspound.",
        [
            hunt((220, 700), "Kill the Stonecrush excavators " + where((220, 700), 'bryn_asquith'), 'Stonecrush excavator', 6),
            end_talk('bryn_asquith', "Tell Bryn Asquith", "Stopped. For today. Tomorrow there'll be more - they don't dig for themselves.", 'default'),
        ],
        {'default': {'text': "From the Dragon-Watch.", 'choice': [d1, d2]}})

d3 = z.item("Survey-Stake Charm", 'gem', 51, 'mind', "A splinter of stake, painted white. White like a dragon.")
d4 = z.item("Rockgrinder's Ring", 'ring', 51, 'might', "Ground smooth from a lump of granite.")
d5 = z.item("Watch-Road Mantle", 'cloak', 51, 'ward', "Dust-grey, with the Watch's red dragon struck through.")
z.quest('dm_road', "The Dragon's Road", 51, 'bryn_asquith',
        "They don't dig for themselves. They dig in a line - north, straight as an arrow, from the dragon's lair toward the moor's edge. A road.\n\nGo up to the dig-head and [see where it goes]. Then tell me I'm wrong.",
        'see where it goes',
        "The Stonecrush are digging a straight road north from Golestandt's lair.",
        [
            hunt((240, 560), "Fight through the Stonecrush rockgrinders " + where((240, 560), 'bryn_asquith'), 'Stonecrush rockgrinder', 4),
            search(Z, P(245, 480), "Search the dig-head", "a survey stake, painted white", CRATE,
                   "A line of white stakes running north, all the way to the edge of the moor - and beyond, toward Cornwall, and Avalon, and Salisbury. Golestandt is building his giants a road to the Giants' Dance."),
            end_talk('bryn_asquith', "Tell Bryn Asquith", "To the Dance. To Salisbury. The giants are marching north on a dragon's road. I wish I'd been wrong.", 'default'),
        ],
        {'default': {'text': "From the Dragon-Watch.", 'choice': [d3, d4, d5]}}, requires='dm_stonecrush')

d6 = z.item("Kez's Crushing Gauntlet", 'bracer', 52, 'might', "Huge. You wear it on your forearm like a bracer, and it still overhangs.")
d7 = z.item("Demolisher's Torc", 'neck', 52, 'ward', "A twist of iron wedges.")
z.quest('dm_kez', 'Kez of the Demolishers', 52, 'bryn_asquith',
        "The Stonecrush have a boss - Kez, down in the south-west digs, with his demolishers. Kill Kez and the digging stops for a season.\n\nIt's a group's fight. Will you [go for Kez]?",
        'go for Kez',
        "Kez leads the Stonecrush demolishers in Dartmoor's south-west digs.",
        [
            hunt((180, 1340), "Bring down Kez " + where((180, 1340), 'bryn_asquith'), 'Kez', 1, r=70),
            end_talk('bryn_asquith', "Tell Bryn Asquith", "Kez is down. The dig's quiet. A season, maybe two. Long enough for the Watch to march.", 'default'),
        ],
        {'default': {'text': "From the Dragon-Watch.", 'choice': [d6, d7]}}, requires='dm_road', group=True)

# ======================================================================== The Pony Moor (51-53)
p1 = z.item("Pony-Hair Charm", 'gem', 51, 'charm', "Rough brown hair, braided with a blue thread.")
p2 = z.item("Herdsman-Hide Bracer", 'bracer', 51, 'ward', "Thick grey hide.")
z.quest('dm_ponies', 'The Ponies of the Moor', 51, 'mirela',
        "The moor ponies were here before Grimspound, before the giants, before anything. The herdsmen are driving them off the north moor - into the lake, some of them - to make room for whatever's coming down the dragon's road.\n\nWill you [stop the herdsmen]?",
        'stop the herdsmen',
        "Granite giant herdsmen are driving the wild ponies off Dartmoor's north moor.",
        [
            hunt((1000, 380), "Stop the granite giant herdsmen " + where((1000, 380), 'mirela'), 'granite giant herdsman', 4),
            end_talk('mirela', "Tell Mirela Stonewright", "The ponies will come back. They always do. It's the giants I'm not sure of.", 'default'),
        ],
        {'default': {'text': "From the Quarry-Oath of Grimspound.", 'choice': [p1, p2]}})

p3 = z.item("Tegbuk's Herd-Staff Charm", 'gem', 53, 'might', "The tip of a giant's herding staff. It's the size of your arm.")
p4 = z.item("Oath-Breaker's Ring", 'ring', 53, 'mind', "Granite, cut by a giant who broke an oath.")
p5 = z.item("Moor-Wind Mantle", 'cloak', 53, 'ward', "Heather-brown, woven by Grimspound's women.")
z.quest('dm_tegbuk', 'Tegbuk', 53, 'mirela',
        "Tegbuk. The herd-chief. He swore the quarry oath with my grandfather - I saw him do it when I was a girl. He's the one sending the herdsmen. He's forgotten every word.\n\nIt needs a group. Will you [remind him]?",
        'remind him',
        "Tegbuk, the giants' herd-chief, who swore the quarry oath with Grimspound, now drives the ponies off the moor.",
        [
            hunt((846, 581), "Bring down Tegbuk " + where((846, 581), 'mirela'), 'Tegbuk', 1, r=70),
            end_talk('mirela', "Tell Mirela Stonewright", "He looked at you, at the end? They say oath-breakers remember, at the end. I hope he did.", 'default'),
        ],
        {'default': {'text': "From the Quarry-Oath of Grimspound.", 'choice': [p3, p4, p5]}}, requires='dm_ponies', group=True)

# ======================================================================== The Stonecallers' Ring (54-56)
s1 = z.item("Stonecaller's Throat-Stone", 'gem', 54, 'mind', "A smooth grey pebble. Hold it to your ear and it hums.")
s2 = z.item("Ring-Stone Belt", 'belt', 54, 'ward', "Grey stones on a leather strap.")
z.quest('dm_stonecallers', 'The Stonecallers', 54, 'dm_hedda',
        "The stonecallers sing to the stones in their ring in the middle valleys. They used to sing the stones awake for the quarry. Now they sing the dragon's song, and the stones listen.\n\nWill you [break the singing]?",
        'break the singing',
        "The granite giant stonecallers sing Golestandt's song in their ring in Dartmoor's middle valleys.",
        [
            hunt((760, 800), "Silence the stonecallers " + where((760, 800), 'dm_hedda'), 'granite giant stonecaller', 5),
            end_talk('dm_hedda', "Tell Quarry-Mother Hedda", "Quiet. For an hour. Do you know what they were singing? I do. I wish I didn't.", 'default'),
        ],
        {'default': {'text': "From the Quarry-Oath of Grimspound.", 'choice': [s1, s2]}})

s3 = z.item("Speaking-Stone Ring", 'ring', 55, 'charm', "It whispers, very faintly, in a voice too big for it.")
s4 = z.item("Dragon's-Song Bracer", 'bracer', 55, 'faith', "Etched with the stonecallers' song - backwards, to undo it.")
z.quest('dm_speaking_stone', 'The Speaking-Stone', 55, 'dm_hedda',
        "In the middle of the ring is the speaking-stone - the giants' oldest. When they swore the quarry oath, they swore it on that stone. If anything still remembers the oath, it does.\n\nWill you [listen to the stone]? Put your hand on it. Don't be afraid of what it says.",
        'listen to the stone',
        "The giants' speaking-stone stands at the heart of the stonecallers' ring.",
        [
            search(Z, P(745, 790), "Put your hand on the speaking-stone", "a tall grey stone, warm to the touch", CRATE,
                   "The stone speaks - in a voice like a furnace door opening: 'GOGMAGOG FELL. HIS BONES STIR UNDER THE PLAIN. THE THRONE IS WARM. A NEW KING SITS IT WHEN THE DRAGON CALLS: CORMORAN OF THE MOUNT.' Then, very small, under it, an old giant's voice: 'the oath, the oath, remember the oath'."),
            end_talk('dm_hedda', "Tell Quarry-Mother Hedda", "Cormoran. Cormoran of the Mount, the biggest of them, who ate Cornwall's cattle when my grandmother was a girl. And under it - the oath, still. Something still remembers.\n\nThat's the dragon's plan, then. He doesn't want a road. He wants a giant king on Gogmagog's throne, and every giant in Albion behind him.", 'default'),
        ],
        {'default': {'text': "From the Quarry-Oath of Grimspound.", 'choice': [s3, s4]}}, requires='dm_stonecallers')

s5 = z.item("Herald's Voice-Stone", 'gem', 56, 'mind', "Black glass, cracked. The voice has gone out of it.")
s6 = z.item("Silent-Ring Torc", 'neck', 56, 'ward', "Grey stone, cool. It doesn't hum.")
s7 = z.item("Oath-Keeper's Mantle", 'cloak', 56, 'faith', "Grimspound's own: grey wool with the quarry-mark in red.")
z.quest('dm_herald', 'The Stone-Herald', 56, 'dm_hedda',
        "The voice in the stone - it comes from the Stone-Herald, the giant who speaks for the dragon. He stands in the ring and sings Golestandt's words into every stone on the moor.\n\nKill the voice and the moor goes quiet. Bring a group. Will you [silence the Herald]?",
        'silence the Herald',
        "The Stone-Herald, the giant who speaks for Golestandt, sings the dragon's words into Dartmoor's stones from the stonecallers' ring.",
        [
            hunt((760, 800), "Silence the Stone-Herald " + where((760, 800), 'dm_hedda'), 'the Stone-Herald', 1, r=70),
            end_talk('dm_hedda', "Tell Quarry-Mother Hedda", "Quiet. The whole moor, quiet. I can hear the ponies.\n\nGo and see Bryn. The Watch has a road to march down now.", 'default'),
        ],
        {'default': {'text': "From the Quarry-Oath of Grimspound.", 'choice': [s5, s6, s7]}}, requires='dm_speaking_stone', group=True)

# ======================================================================== The Pounders' Road (55-56)
r1 = z.item("Outlooker's Eye-Stone", 'gem', 55, 'finesse', "A glassy pebble the giants used as a lens.")
r2 = z.item("Pounder-Fist Bracer", 'bracer', 55, 'might', "Dented, deliberately.")
z.quest('dm_outlookers', 'The Outlookers', 55, 'bryn_asquith',
        "The outlookers watch the south road - the road to the lair and the throne. Nothing gets down it without them knowing, and the pounders come when they shout.\n\nWill you [blind the road]?",
        'blind the road',
        "Granite giant outlookers watch the south road to Golestandt's lair and Gogmagog's throne.",
        [
            hunt((900, 1120), "Kill the granite giant outlookers " + where((900, 1120), 'bryn_asquith'), 'granite giant outlooker', 5),
            end_talk('bryn_asquith', "Tell Bryn Asquith", "Blind. For now. The Watch can use that.", 'default'),
        ],
        {'default': {'text': "From the Dragon-Watch.", 'choice': [r1, r2]}})

r3 = z.item("Knocker's Lamp-Charm", 'gem', 56, 'charm', "A tiny lamp, still lit, that won't go out.")
r4 = z.item("Deep-Seam Ring", 'ring', 56, 'mind', "Tin, from the deepest seam in Dartmoor.")
z.quest('dm_knockers', 'The Knockers', 56, 'mirela',
        "Every miner knows: the knockers knock where the treasure is. Ours knock where the dragon sleeps now - all day, all night, under the south road. They're waking him, or he's waking them.\n\nWill you [quiet the knocking]?",
        'quiet the knocking',
        "The granite knockers knock under Dartmoor's south road, where Golestandt sleeps.",
        [
            hunt((1200, 1150), "Quiet the granite knockers " + where((1200, 1150), 'mirela'), 'granite knocker', 6),
            end_talk('mirela', "Tell Mirela Stonewright", "Quiet. You can hear something else now, under the road. Breathing.", 'default'),
        ],
        {'default': {'text': "From the Quarry-Oath of Grimspound.", 'choice': [r3, r4]}})

# ======================================================================== The Giants' Throne (57-58)
t1 = z.item("Throne-Warden's Seal", 'gem', 57, 'might', "A granite seal, cut with a crown and a dragon.")
t2 = z.item("Stonelord's Girdle", 'belt', 57, 'ward', "Huge links of iron, cut down to fit.")
t3 = z.item("Dragon-Watch Mantle", 'cloak', 57, 'faith', "Red, with a white dragon struck through. The Watch's own.")
z.quest('dm_gorm', 'Gorm Throne-Warden', 57, 'bryn_asquith',
        "Gorm Throne-Warden keeps Gogmagog's throne in the south-east - keeps it warm, the stonecallers say, for the king who's coming. While Gorm stands, nothing gets near it.\n\nYou'll want a group - two, if you can. Will you [face Gorm]?",
        'face Gorm',
        "Gorm Throne-Warden keeps Gogmagog's empty throne in Dartmoor's south-east, waiting for a king.",
        [
            hunt((1310, 1470), "Bring down Gorm Throne-Warden " + where((1310, 1470), 'bryn_asquith'), 'Gorm Throne-Warden', 1, r=70),
            end_talk('bryn_asquith', "Tell Bryn Asquith", "Gorm's down. The throne's open. Go and look at it - I want to know what you see.", 'default'),
        ],
        {'default': {'text': "From the Dragon-Watch.", 'choice': [t1, t2, t3]}}, requires='dm_outlookers', group=True)

t4 = z.item("Gogmagog's Crown-Stone", 'gem', 58, 'might', "A chip of the giants' throne. It's warm.")
t5 = z.item("Watch-Oath Ring", 'ring', 58, 'faith', "Silver, with a dragon in chains.")
t6 = z.item("Quarry-Oath Torc", 'neck', 58, 'ward', "Granite and silver, cut from Grimspound's oldest block.")
z.quest('dm_throne', "The Giants' Throne", 58, 'bryn_asquith',
        "Gorm's gone, and Gogmagog's throne is open. Will you [look at the throne]? Carefully. Then come back and tell me what a giant king's throne looks like with no one on it.",
        'look at the throne',
        "Gogmagog's throne stands empty in Dartmoor's south-east, with Gorm Throne-Warden gone.",
        [
            reach(Z, P(1235, 1410), "Go to the Giants' Throne in the south-east", "A seat of raw granite the height of three men - empty, for now. Beside it the stonelords are cutting a crown out of the living rock, and one of them is the biggest giant you have ever seen: Cormoran, the giant of the Mount, trying it on for size. Far to the west, under the south road, something breathes out, pleased.", r=25),
            choice('bryn_asquith', "Tell Bryn Asquith what you saw",
                   "Cormoran. With a crown. On Gogmagog's throne.\n\nThe dragon's making him a king - the first giant king of Albion since Gogmagog - and every giant on the moor will follow. Sir Constantine has to march, now, before the crown is finished.\n\nWill you go with the [Watch], under Constantine's banner? Or for [Grimspound] - Hedda says the oath-stone remembers, and if Gogmagog is broken, the giants might remember too.",
                   [('Watch', "Then you're the Dragon-Watch's. Constantine's at the town gate. Give him the word.", 'ending:watch'),
                    ('Grimspound', "Then you're the oath's. Hedda will be glad. Constantine's at the town gate - give him the word anyway. The oath needs the Watch.", 'ending:oath')]),
        ],
        {'watch': {'text': "From the Dragon-Watch. Sir Constantine waits at Grimspound: give him the word when you're ready to march.", 'items': [t5], 'choice': [t4, t6]},
         'oath': {'text': "From the Quarry-Oath of Grimspound. Sir Constantine waits at Grimspound: give him the word when you're ready to march.", 'items': [t6], 'choice': [t4, t5]}},
        requires='dm_gorm')
