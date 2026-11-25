"""Skona Ravine's story quests (claude 2026-11-25, "Midgard - the plan", round 3) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_skona

Dangerous. The west thread's stronghold: Ulfhamr, the werewolf hold in the middle of the ravine, where the wolfaur headsmen and
the warders gather Fenrir's kin for Hati's host in Raumarik - the zone's siege, for the Wolfsbane Rangers (out of the Stor Gothi's
camp). The Seithkona Circle in the north-east reads the moon, and the moon is afraid. From the south, out of Malmohus, the first
silverscale drakes come creeping up the drake trail.

The zone's two older quests are kept as they were (moonbound, sidhe_maps).

Arcs (recommended levels): The North Woods (28-31), The Seithkona Circle (29-33), Ulfhamr (32-37), The Western Shore (33-36),
The Drake Trail (34-37).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(106, 'Skona Ravine', 'mid_skona', 'story106_skona', {'moonbound', 'sidhe_maps'},
          {'hallgerd', 'ulfrun', 'bard', 'eyvor', 'thorvald'},
          {'Wolfsbane Sachet', 'Moonbound Ring', "Warder's Fang Bracer", "Cub's Blanket Cloak", 'Sidhe Brooch', "Niamh's Token",
           "Scout's Grey Cloak", "Spymaster's Ring"}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157

person('sk_jodur', 'Ranger-Captain Jodur', (618, 568), 'm', 42, model=M, guild='the Wolfsbane Rangers',
       idle="The Rangers have watched the ravine since before the werewolves came. We'll watch it after they're gone.")
person('sk_saga', 'Seithkona Saga', (1352, 268), 'f', 40, model=F, guild='the Seithkona Circle',
       idle="The moon's afraid. You can see it, if you know how to look.")

R, C = "From the Wolfsbane Rangers.", "From the Seithkona Circle."

# ======================================================================== The North Woods (28-31)
n1 = z.item("Wolfsbane Ring", 'ring', 28, 'ward', "A ring of dried wolfsbane under glass.")
n2 = z.item("Skulker-Hide Belt", 'belt', 28, 'finesse', "Grey fur, still bristling.")
z.quest('sk_skulkers', 'Skulkers in the Woods', 28, 'sk_jodur',
        "Werewolf skulkers in the north woods - the hold's scouts. They watch our camp, and they report.\n\nWill you [hunt the skulkers]?",
        'hunt the skulkers',
        "Werewolf skulkers, the werewolf hold's scouts, watch the Rangers' camp from Skona's north woods.",
        [
            hunt((800, 300), "Hunt the werewolf skulkers " + where((800, 300), 'sk_jodur'), 'werewolf skulker', 5),
            end_talk('sk_jodur', "Tell Ranger-Captain Jodur", "Blind for a while. Good. The hold's busier than it's ever been. Something's gathering.", 'default'),
        ],
        {'default': {'text': R, 'choice': [n1, n2]}})

n3 = z.item("Wolverine-Claw Torc", 'neck', 30, 'might', "Three claws, each as long as a finger.")
n4 = z.item("Ranger's Grey Bracer", 'bracer', 30, 'finesse', "Soft grey leather, a ranger's.")
z.quest('sk_wolverines', 'Wolverines', 30, 'eyvor',
        "Young wolverines in the north woods - driven out of the middle of the ravine. The werewolves don't share.\n\nWill you [clear them off the trail]?",
        'clear them off the trail',
        "Young wolverines driven out of Skona's middle by the werewolves block the north woods trail.",
        [
            hunt((700, 450), "Clear the young wolverines " + where((700, 450), 'eyvor'), 'young wolverine', 4),
            hunt((800, 400), "Kill the brush cats", 'brush cat', 3),
            end_talk('eyvor', "Tell Ranger Eyvor", "The trail's open. Everything in the ravine is running from the middle. Everything except the wolves.", 'default'),
        ],
        {'default': {'text': R, 'choice': [n3, n4]}}, requires='sk_skulkers')

# ======================================================================== The Seithkona Circle (29-33)
c1 = z.item("Tree-Frog Charm", 'gem', 29, 'charm', "A little green frog, carved in jade.")
c2 = z.item("Circle-Walker's Belt", 'belt', 29, 'faith', "Embroidered with the moon's phases.")
z.quest('sk_tinglers', 'Bad Dreams', 29, 'sk_saga',
        "The great tinglers in the meadows feed on dreams, and the circle's dreams have been very bad. They've grown fat. They come to the stones at night.\n\nWill you [drive them off]?",
        'drive them off',
        "Great tinglers fat on bad dreams come to the Seithkona Circle's stones at night.",
        [
            hunt((1150, 350), "Drive off the great tinglers " + where((1150, 350), 'sk_saga'), 'great tingler', 4),
            end_talk('sk_saga', "Tell Seithkona Saga", "Better. We'll sleep, a little. The dreams won't stop, though. We all dream the same thing: a wolf running after the moon.", 'default'),
        ],
        {'default': {'text': C, 'choice': [c1, c2]}})

c3 = z.item("Wind-Spirit Veil Charm", 'gem', 31, 'mind', "A veil of nothing. You can feel it move.")
c4 = z.item("Moonlit Bracer", 'bracer', 31, 'faith', "Silver, cold, faintly shining.")
z.quest('sk_wind_spirits', 'The Howling Wind', 31, 'sk_saga',
        "The wind spirits on the eastern heights carry the werewolves' howls to the moon. Every night, louder. The moon hears them.\n\nWill you [silence the wind]?",
        'silence the wind',
        "Wind spirits on Skona's eastern heights carry the werewolves' howls to the moon.",
        [
            hunt((1320, 800), "Silence the wind spirits " + where((1320, 800), 'sk_saga'), 'wind spirit', 5),
            end_talk('sk_saga', "Tell Saga", "Quieter. Now I can hear what they were drowning out.", 'default'),
        ],
        {'default': {'text': C, 'choice': [c3, c4]}}, requires='sk_tinglers')

c5 = z.item("Moon-Stone Pendant", 'neck', 33, 'mind', "A pale stone that darkens a little every night.")
c6 = z.item("Seithkona's Circle Ring", 'ring', 33, 'faith', "Cut from the circle's own stone.")
z.quest('sk_moon_stone', 'The Moon-Stone', 33, 'sk_saga',
        "The circle's moon-stone shows the moon's road. Read it with me - stand at the stone at the circle's heart and look.\n\nWill you [read the stone]?",
        'read the stone',
        "The Seithkona Circle's moon-stone shows the moon's road across the sky.",
        [
            search(Z, P(1365, 250), "Read the moon-stone at the circle's heart", "a pale stone, waist-high", LANTERN,
                   "In the stone the moon runs across the sky, and behind it runs a wolf, gaining. Under the wolf, a hall of ice in the north-west: Raumarik. And in the middle of the ravine, wolves gathering at a hold, to go north."),
            end_talk('sk_saga', "Tell Saga what you saw", "Hati. Fenrir's son, who hunts the moon. When he catches it, the long winter comes. And the hold in our ravine - Ulfhamr - is where his host gathers before it goes north.\n\nGo to Ranger-Captain Jodur. The Rangers mean to break that hold.", 'default'),
        ],
        {'default': {'text': C, 'choice': [c5, c6]}}, requires='sk_wind_spirits')

# ======================================================================== Ulfhamr (32-37)
u1 = z.item("Werewolf-Guard Fang Ring", 'ring', 32, 'might', "A fang set in iron.")
u2 = z.item("Wolfsbane-Stitched Cloak", 'cloak', 32, 'ward', "Grey wool, wolfsbane sewn into the hem.")
z.quest('sk_guards', "The Hold's Guards", 32, 'sk_jodur',
        "The werewolf guards patrol the ground round Ulfhamr. Every one we kill is one less on the walls when the Rangers march.\n\nWill you [thin the guards]?",
        'thin the guards',
        "Werewolf guards patrol the ground round Ulfhamr, the werewolf hold in Skona's middle.",
        [
            hunt((720, 760), "Thin the werewolf guards " + where((720, 760), 'sk_jodur'), 'werewolf guard', 5),
            end_talk('sk_jodur', "Tell Jodur", "Good. The Rangers will hear of it. Every one tells them we can win.", 'default'),
        ],
        {'default': {'text': R, 'choice': [u1, u2]}}, requires='sk_wolverines')

u3 = z.item("Warder's Rune-Bracer", 'bracer', 34, 'faith', "Wolf-runes carved by a werewolf warder.")
u4 = z.item("Ravine Ranger's Belt", 'belt', 34, 'finesse', "Many pouches, all smelling of wolfsbane.")
z.quest('sk_warders', 'The Warders', 34, 'ulfrun',
        "The werewolf warders keep the hold's magic - wards of blood and moonlight. While they stand, the hold can't be broken.\n\nWill you [break the warders]?",
        'break the warders',
        "Werewolf warders keep Ulfhamr's wards of blood and moonlight.",
        [
            hunt((1000, 850), "Break the werewolf warders " + where((1000, 850), 'ulfrun'), 'werewolf warder', 5),
            end_talk('ulfrun', "Tell Seithkona Ulfrun", "The wards are weaker. I felt them give. The hold can be taken now.", 'default'),
        ],
        {'default': {'text': C, 'choice': [u3, u4]}}, requires='sk_guards')

u5 = z.item("Headsman's Axe-Torc", 'neck', 36, 'might', "A tiny axe on a heavy chain.")
u6 = z.item("Wolf-Hunter's Mantle", 'cloak', 36, 'ward', "Rangers' grey, wolf-pelts sewn on.")
u7 = z.item("Hunt-Breaker's Ring", 'ring', 36, 'finesse', "Silver. Wolves hate it.")
z.quest('sk_headsmen', 'The Wolfaur Headsmen', 36, 'sk_jodur',
        "The wolfaur headsmen hunt the south of the ravine for the hold - and they hunt men. They'll lead Hati's host north when it marches.\n\nBring friends. Will you [hunt the headsmen]?",
        'hunt the headsmen',
        "Wolfaur headsmen hunt men in Skona's south for the werewolf hold.",
        [
            hunt((950, 1200), "Hunt the wolfaur headsmen " + where((950, 1200), 'sk_jodur'), 'wolfaur headsman', 4),
            end_talk('sk_jodur', "Tell Jodur", "The hunters hunted. Good. Now - the hold itself.", 'default'),
        ],
        {'default': {'text': R, 'choice': [u5, u6, u7]}}, requires='sk_warders', group=True)

u8 = z.item("Ulfhamr Scout's Ring", 'ring', 37, 'finesse', "Grey iron, very quiet.")
u9 = z.item("Rangers' Oath-Belt", 'belt', 37, 'ward', "The Rangers' belt, given to those who stand with them.")
z.quest('sk_ulfhamr', 'Ulfhamr', 37, 'sk_jodur',
        "Ulfhamr. Go and look at it - count the wolves on the walls, find the gate. Then come back and tell me we can win.\n\nWill you [scout the hold]?",
        'scout the hold',
        "The Wolfsbane Rangers mean to break Ulfhamr, the werewolf hold in Skona's middle.",
        [
            reach(Z, P(800, 640), "Creep up to the ridge above Ulfhamr", "A hold of black logs and bones, wolf-skulls on every post. Howling from inside, and the warden on the gate - a werewolf in a captain's mail.", r=25),
            search(Z, P(820, 660), "Look over the hold's gate", "a post hung with fresh pelts", CRATE,
                   "Wolf-pelts - and men's cloaks, rangers' grey among them. Scratched in the post: 'WHEN THE MOON RUNS RED, NORTH TO HATI.'"),
            end_talk('sk_jodur', "Tell Jodur", "Rangers' cloaks. Then we take it for every one of them.\n\nThe Rangers will march when the ravine is behind us - every skulker, every warder, every headsman broken tells the men they can win. Be there.", 'default'),
        ],
        {'default': {'text': R, 'choice': [u8, u9]}}, requires='sk_headsmen')

# ======================================================================== The Western Shore (33-36)
w1 = z.item("Orm-Scale Ring", 'ring', 33, 'ward', "A green orm's scale, cut round.")
w2 = z.item("Shore-Walker's Cloak", 'cloak', 33, 'ward', "Sea-green, salt-stiff.")
z.quest('sk_orms', 'The Green Orms', 33, 'thorvald',
        "The green orms on the western shore have come up out of the water and onto the paths. They've never done that.\n\nWill you [drive them back]?",
        'drive them back',
        "Green orms have come up out of the water onto the paths of Skona's western shore.",
        [
            hunt((160, 700), "Drive back the green orms " + where((160, 700), 'thorvald'), 'green orm', 5),
            end_talk('thorvald', "Tell Thorvald", "Back in the water. Something in the ravine frightened them. Everything's frightened, this year.", 'default'),
        ],
        {'default': {'text': R, 'choice': [w1, w2]}})

w3 = z.item("Sidhe-Silver Charm", 'gem', 35, 'mind', "A leaf of silver, too fine for Midgard's smiths.")
w4 = z.item("Strand-Ward Bracer", 'bracer', 35, 'ward', "Silver and wood.")
z.quest('sk_sidhe', 'The Strangers on the Strand', 35, 'thorvald',
        "The sidhe on the strand - strangers, from somewhere far off. They've always been odd. Now they shoot at anyone who comes near.\n\nWill you [push them back]?",
        'push them back',
        "The sidhe strangers on Skona's western strand shoot at anyone who comes near.",
        [
            hunt((170, 1000), "Push back the sidhe gaoite " + where((170, 1000), 'thorvald'), 'sidhe gaoite', 4),
            end_talk('thorvald', "Tell Thorvald", "They said something, as they fell back. 'The winter wolf comes, and your moon dies.' Even the strangers know.", 'default'),
        ],
        {'default': {'text': R, 'choice': [w3, w4]}}, requires='sk_orms')

# ======================================================================== The Drake Trail (34-37)
d1 = z.item("Dryad-Blossom Charm", 'gem', 34, 'charm', "A blossom that never wilts.")
d2 = z.item("Greenthumb's Ring", 'ring', 34, 'faith', "Living wood.")
z.quest('sk_dryads', 'The Angry Wood', 34, 'bard',
        "The dryads of the south-east wood have turned on everyone. Something's burning their trees - from the south.\n\nWill you [calm the wood]?",
        'calm the wood',
        "The dryads of Skona's south-east wood have turned on everyone; something from the south burns their trees.",
        [
            hunt((1450, 1250), "Calm the dryad blossoms " + where((1450, 1250), 'bard'), 'dryad blossom', 5),
            end_talk('bard', "Tell Bard", "Calmer. They showed me the burnt trees. Burnt from inside - claws, and fire.", 'default'),
        ],
        {'default': {'text': R, 'choice': [d1, d2]}})

d3 = z.item("Silverscale Drake Torc", 'neck', 37, 'might', "Silver scales on a silver chain.")
d4 = z.item("Drake-Trail Mantle", 'cloak', 37, 'ward', "Scorched at the hem.")
d5 = z.item("Malmohus-Road Belt", 'belt', 37, 'finesse', "A drakulv's belt, the dragon's eye cut off it.")
z.quest('sk_drakes', 'The Drake Trail', 37, 'bard',
        "Young silverscale drakes on the trail up from Malmohus. The dragon's brood, coming north. They'll find the werewolves sooner or later - and I don't know who I'd rather won.\n\nBring friends. Will you [break the drakes]?",
        'break the drakes',
        "Young silverscale drakes come north up Skona's drake trail from Malmohus.",
        [
            hunt((1430, 1270), "Break the young silverscale drakes " + where((1430, 1270), 'bard'), 'young silverscale drake', 3),
            search(Z, P(1440, 1280), "Search the drakes' trail", "a drakulv banner, trampled", CRATE,
                   "A drakulv banner: the dragon's eye over a wolf's skull. Stitched under it: 'The Mother's brood goes before her. Let the wolves and men kill each other, and the brood takes what's left.'"),
            end_talk('bard', "Tell Bard", "Let the wolves and men kill each other. That's their plan. Both threads, one trap. Midgard has to win both.", 'default'),
        ],
        {'default': {'text': R, 'choice': [d3, d4, d5]}}, requires='sk_dryads', group=True)
