"""Salisbury Plains' story quests (claude 2026-11-24, "Albion - the plan", round 2) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_salisbury_plains

The south thread arrives: Golestandt's giants have marched north out of Cornwall to take back the Giants' Dance - the ring the
giants first raised, that Merlin carried here and set over the graves of the British lords Hengist murdered at the feast of the
Long Knives. Those graves bind the stones. The giants pay tomb-raiders in Cornish tin to dig them out, and under the great barrow
their own dead are stirring - Gogmagog, the last giant of Albion, among them. The Abbess of Amesbury, who keeps the graves (and
was a queen once), and the Pendragon's Watch hold the line from West Downs. The Bishop's map from Black Mountains South points
here too: Morgana wants Merlin's stones as much as the dragon does.

The zone's two older quests are kept as they were (under_stones, white_horse).

Arcs (recommended levels): The Downs (10-14), The Diggers (12-18), The Long Knives (14-20), The Giants' March (16-22),
The Giants' Dance (22-26, Deadly).
"""
import sys
from story_gen import talk, reach, search, boss, defend, choice, end_talk
from albion_story import Story, CRATE, BEDROLL, LANTERN, M, F, OLD

S = Story(1, 'Salisbury Plains', 'alb_salisbury_plains', 'story001_salisbury_plains', {'under_stones', 'white_horse'},
          {'wenna_ashby', 'dunstan_carter', 'aled_ashby', 'ysolde_huntington', 'coel_huntsman', 'rhodri_huntington'},
          {"Aled's Tally-Stick Charm", 'Torc of the Barrow-King', 'Henge-Stone Bracer', "Drover's Oilskin", "Huntington's Horn",
           'Chalk-White Mantle', 'Basilisk-Eye Ring', 'Hide of the White Horse'})
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
GIANT, STONECALLER, GHOST_KNIGHT, LEGION = 12719, 770006, 12016, 12728

# ------------------------------------------------------------------ people
person('sp_osfrid', 'Watch-Commander Osfrid', (705, 195), 'm', 40, model=28, guild="the Pendragon's Watch",
       idle="Every giant on this plain is walking north. I've counted. I stopped counting.")
person('sp_abbess', 'the Abbess of Amesbury', (738, 188), 'f', 45, guild='the Sisters of Amesbury',
       idle="We tended the graves of the Long Knives for forty years. Now the giants tend them, with spades.")
person('sp_ostler_bryn', 'Bryn the Ostler', (690, 218), 'm', 20, idle="The wild herd's the pride of the Downs. Was.")
person('sp_herbwife_elin', 'Elin the Herbwife', (748, 222), 'f', 24, idle="Stone sheep. Stone hares. Stone shepherd, near enough.")
person('sp_sister_morwen', 'Sister Morwen', (742, 705), 'f', 30, guild='the Sisters of Amesbury',
       idle="The dead on this plain were murdered at a feast. They have reason to be restless.")
person('sp_outrider_cadoc', 'Outrider Cadoc', (760, 712), 'm', 32, guild="the Pendragon's Watch",
       idle="The Watch's picket. Furthest south anyone sane will stand.")

# ======================================================================== The Downs (10-14)
a1 = z.item("Herd-Mare's Halter Ring", 'ring', 10, 'finesse', "Braided horsehair round a copper band.")
a2 = z.item("Downs Rider's Belt", 'belt', 10, 'might', "Taken off a horse-thief. Bryn says it suits you better.")
z.quest('sp_wild_herd', 'The Wild Herd', 10, 'sp_ostler_bryn',
        "The wild herd's run on these downs since before Camelot. Now the Downs Riders are cutting out the best and driving them north to sell.\n\nTheir camp's up by the river in the north. Will you [stop the riders]?",
        'stop the riders',
        "Bandits are driving off the Downs' wild herd from their camp in the north.",
        [
            hunt((820, 200), "Fight off the Downs Riders on the horse-road " + where((820, 200), 'sp_ostler_bryn'), 'bandit', 5),
            hunt((905, 110), "Defeat the Riders' leader at their camp", 'bandit leader', 1,
                 text="The bandit leader falls. Behind the camp, a pen of frightened horses - and a bill of sale, to 'the man with the Cornish tin'."),
            end_talk('sp_ostler_bryn', "Tell Bryn", "Cornish tin? For horses? Who in Cornwall needs that many horses...\n\nNever mind. The herd's free. Thank you.", 'default'),
        ],
        {'default': {'text': "From Bryn.", 'choice': [a1, a2]}})

a3 = z.item("Basilisk-Lid Charm", 'gem', 12, 'mind', "A basilisk's eyelid, dried and set in silver. It's shut. Keep it that way.")
a4 = z.item("Herbwife's Rue Sash", 'belt', 12, 'charm', "Hung with rue against the evil eye. Elin swears by it.")
z.quest('sp_stone_eyed', 'Stone-Eyed', 12, 'sp_herbwife_elin',
        "Stone sheep. I'm not jesting - grey stone, all the way through, standing in the grass with their mouths still chewing. The basilisks have come up from the south.\n\nWill you [hunt the basilisks]? And bring me back an eye. Shut, mind.",
        'hunt the basilisks',
        "Basilisks from the south are turning the Downs' flocks to stone.",
        [
            hunt((700, 600), "Hunt the pseudo basilisks on the middle plain " + where((700, 600), 'sp_herbwife_elin'), 'pseudo basilisk', 6),
            search(Z, P(1255, 275), "Search the basilisk nest in the north-east", "a nest of grey stones", CRATE,
                   "The nest is ringed with stone things - a fox, a hare, a crow mid-flight. And eggs, warm. The basilisks didn't come up the plain. Something drove them."),
            end_talk('sp_herbwife_elin', "Tell Elin", "Drove them? Basilisks don't flee from much.\n\nUnless what's coming is bigger than they are.", 'default'),
        ],
        {'default': {'text': "From Elin.", 'choice': [a3, a4]}})

a5 = z.item("Carrion-Drake Fang", 'neck', 11, 'might', "A curved fang on a thong. Slythcur had a lot of them; this was the biggest.")
a6 = z.item("Heath-Walker's Bracer", 'bracer', 11, 'ward', "Scuffed leather. The heath is hard on everything.")
z.quest('sp_carrion', 'Carrion on the Wind', 11, 'sp_osfrid',
        "Carrion drakes on the north-west heath - more every week, and one big brute they call Slythcur. They follow the giants, my outriders say. Where giants walk, things die, and the drakes eat well.\n\nThin them, will you? [Clear the heath].",
        'clear the heath',
        "Carrion drakes gather on the north-west heath, following the giants' march.",
        [
            hunt((230, 188), "Thin the carrion drakes on the heath " + where((230, 188), 'sp_osfrid'), 'carrion drake', 6),
            hunt((304, 311), "Kill Slythcur", 'Slythcur', 1),
            end_talk('sp_osfrid', "Report to Watch-Commander Osfrid", "Good. Now they'll have to follow the giants a bit hungrier.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [a5, a6]}})

a7 = z.item("Nymph's Willow Ring", 'ring', 13, 'charm', "A willow twig grown into a ring. It's still alive.")
a8 = z.item("Veviel's Dew-Sash", 'belt', 13, 'mind', "Always damp, always cool.")
a9 = z.item("Grove-Pact Bracer", 'bracer', 13, 'ward', "Carved with a nymph's mark. They won't touch whoever wears it.")
z.quest('sp_nymphs', "The Grove Nymphs' Bargain", 13, 'sp_abbess',
        "The grove nymphs of the middle plain never bothered anyone. This year they're striking at travellers. A woman called Veviel leads them.\n\nThe nymphs remember the plain before the stones. Will you [speak with Veviel]? By whatever means she'll allow.",
        'speak with Veviel',
        "The grove nymphs of the middle plain have turned hostile. The Abbess wants to know why.",
        [
            hunt((700, 650), "Get past the grove nymphs " + where((700, 650), 'sp_abbess'), 'grove nymph', 5),
            hunt((460, 647), "Face Veviel", 'Veviel', 1,
                 text="Veviel sinks into the grass. 'The ground shakes,' she whispers. 'The old ones are coming home to their stones. We only wanted them to pass us by.'"),
            choice('sp_abbess', "Tell the Abbess what Veviel said",
                   "'The old ones are coming home to their stones.' The giants. The nymphs are frightened, as we all are.\n\nShall I [send them word] that Amesbury will shelter their grove? Or [let them be]? Fear makes poor neighbours either way.",
                   [('send them word', "Then Sister Morwen will take them bread and willow-water. Frightened things can be friends.", 'ending:friends'),
                    ('let them be', "Then we'll go round their grove, and they'll go round us.", 'ending:apart')]),
        ],
        {'friends': {'text': "The nymphs send a gift.", 'items': [a9], 'choice': [a7, a8]},
         'apart': {'text': "From the Sisters of Amesbury.", 'choice': [a7, a8, a9]}})

# ======================================================================== The Diggers (12-18)
d1 = z.item("Digger's Spade-Ring", 'ring', 14, 'might', "Bent from a spade-edge. It's dug its last grave.")
d2 = z.item("Barrow-Map Sash", 'belt', 14, 'mind', "Stitched from the diggers' own map. The barrows are marked in red.")
z.quest('sp_diggers', 'Spades on the Plain', 14, 'sp_osfrid',
        "Tomb-raiders in the western fields - dozens, with spades and carts. They're opening the barrows one by one. Those are the graves of the Long Knives, and the Abbess is beside herself.\n\nWill you [break the diggers]? And find out who's paying them.",
        'break the diggers',
        "Tomb-raiders are opening the barrows in the western fields.",
        [
            hunt((420, 950), "Drive off the diggers in the western fields " + where((420, 950), 'sp_osfrid'), 'tomb raider digger', 6),
            search(Z, P(365, 1108), "Search the diggers' camp", "a cart of grave-goods", CRATE,
                   "Gold torcs, a broken crown, finger-bones still wearing rings. And a pay-chit: 'Forty ingots of Cornish tin, for every barrow opened to the bottom. Bring the bones to the stones.'"),
            end_talk('sp_osfrid', "Show Osfrid the pay-chit", "Cornish tin, paid by the barrow. 'Bring the bones to the stones.'\n\nThat's not grave-robbing. Robbers keep the gold. Somebody wants the dead moved.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [d1, d2]}})

d3 = z.item("Ghast-Ward Charm", 'gem', 15, 'faith', "Blessed by the Abbess, against the restless dead.")
d4 = z.item("Ghostwalker's Lantern-Ring", 'ring', 15, 'mind', "Cynewulf's own ring. It glows in the presence of ghosts.")
d5 = z.item("Long Knives Mourning Band", 'bracer', 15, 'ward', "Black linen, embroidered with 460 white stitches.")
z.quest('sp_what_spade_woke', 'What the Spade Woke', 15, 'sp_abbess',
        "Under these barrows lie four hundred and sixty lords of Britain. Hengist the Saxon invited them to a peace-feast here, on the plain, and at a word his men drew knives and murdered them all. Merlin raised the Giants' Dance over their graves.\n\nThe diggers have woken them. Green ghasts walk the western fields, and a man called Cynewulf - a Saxon, a 'ghostwalker' - walks with them. Will you [lay them down]?",
        'lay them down',
        "The diggers have woken the murdered lords of the Long Knives. A Saxon ghostwalker leads the ghasts.",
        [
            hunt((462, 1098), "Lay the green ghasts in the western fields to rest " + where((462, 1098), 'sp_abbess'), 'green ghast', 5),
            hunt((637, 1060), "Stop Cynewulf the Ghostwalker", 'Cynewulf the Ghostwalker', 1,
                 text="Cynewulf falls. 'My grandfather's grandfather held a knife at that feast,' he says. 'I came to say sorry. They didn't want to hear it.'"),
            end_talk('sp_abbess', "Tell the Abbess", "He came to apologise. Four hundred years too late, and to the wrong people.\n\nThe ghasts are down. But the graves are open, and the dead won't stay down while they are.", 'default'),
        ],
        {'default': {'text': "From the Sisters of Amesbury.", 'choice': [d3, d4, d5]}},
        requires='sp_diggers')

d6 = z.item("Cornish Tin Ingot-Ring", 'ring', 17, 'might', "Hammered from one of the giants' pay-ingots.")
d7 = z.item("Raider-Captain's Cloak", 'cloak', 17, 'finesse', "Grey and brown, made for lying flat in long grass.")
d8 = z.item("Paymaster's Ledger-Clasp", 'gem', 17, 'mind', "The clasp off the raiders' pay-ledger.")
z.quest('sp_paymaster', "The Raiders' Paymaster", 17, 'sp_osfrid',
        "The diggers in the west are only labour. The raiders on the eastern ridge are the ones who carry the tin. Their scouts watch every road.\n\nWill you [follow the tin]? Fight through the scouts, break the eastern camp, and bring me their ledger.",
        'follow the tin',
        "The tomb-raiders' camp on the eastern ridge carries the Cornish tin that pays the diggers.",
        [
            hunt((882, 658), "Fight through the tomb-raider scouts " + where((882, 658), 'sp_osfrid'), 'tomb raider scout', 4),
            hunt((1272, 796), "Break the raiders' camp on the eastern ridge", 'tomb raider', 4),
            search(Z, P(1275, 800), "Search the raiders' camp for the ledger", "an iron-bound chest", CRATE,
                   "The ledger, in a careful hand: 'Received of Bolster, herald of the Wrath of Golestandt: tin, 900 ingots. Delivered to the stones: the bones of 212 lords. Remaining: 248. The dragon is patient. The giants are not.'",
                   give="the raiders' ledger"),
            end_talk('sp_osfrid', "Bring the ledger to Osfrid", "Golestandt. The dragon of Dartmoor - awake? I'd hoped that was a nursery tale.\n\nHe wants the dead out from under the stones. Two hundred and forty-eight left. We'd better be quick.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [d6, d7, d8]}},
        requires='sp_diggers')

# ======================================================================== The Long Knives (14-20)
k1 = z.item("Ambrosius's Ring", 'ring', 19, 'faith', "A plain gold ring with a red dragon. Ambrosius Aurelianus, Arthur's uncle, raised the stones for the murdered lords.")
k2 = z.item("Feast-Hall Torc", 'neck', 19, 'might', "Bronze, very old. Its owner was wearing it the night of the feast.")
k3 = z.item("Amesbury Shroud-Mantle", 'cloak', 19, 'ward', "Grey linen, sewn by the Sisters. It's warmer than it looks.")
z.quest('sp_long_knives', 'The Night of the Long Knives', 19, 'sp_sister_morwen',
        "The dead of the feast are walking the fields by night - not the ghasts the diggers woke. The old ones. Lords, still in their feast-clothes, looking for the men who killed them.\n\nThe Abbess says they must be told it's over. That Hengist is long dead and his sons with him. Will you [tell the dead]? They may not listen.",
        'tell the dead',
        "The murdered lords of the Long Knives walk the plain at night. Sister Morwen wants them told the war is over.",
        [
            hunt((600, 820), "Calm the disturbed dead on the field of the feast " + where((600, 820), 'sp_sister_morwen'), 'disturbed presence', 5),
            search(Z, P(560, 860), "Search the old feasting-ground", "a ring of sunken stones", CRATE,
                   "Under the turf, the stones of a long table. At its head, a cup - and in the cup, a ring with a red dragon on it."),
            boss(Z, P(565, 855), "Face the shade that rises at the table's head", "The Saxon shade breaks apart, and the field goes still. For the first time in four hundred years, nobody is waiting for the feast to end.",
                 'the Shade of Hengist', GHOST_KNIGHT, 20, "A tall shade in Saxon mail stands up at the head of the table. 'Nimed eure saxes!' it roars - draw your knives - and the dead rise round you.",
                 adds=[(12399, 'restless lord', [17, 18])], every=25, count=2),
            choice('sp_sister_morwen', "Tell Sister Morwen", "Hengist's shade. Still giving the word, after all this time.\n\nThe ring - Ambrosius's, the Abbess will say. Do we [bury the ring] with the lords, so they know they were avenged? Or do you [carry it] for them, to the stones?",
                   [('bury the ring', "Then it goes back in the ground, and the lords rest. Bless you.", 'ending:buried'),
                    ('carry it', "Then carry it well. The stones will know it.", 'ending:carried')]),
        ],
        {'buried': {'text': "From the Sisters of Amesbury.", 'items': [k3], 'choice': [k2]},
         'carried': {'text': "Ambrosius's ring goes with you.", 'items': [k1], 'choice': [k2, k3]}},
        requires='sp_what_spade_woke')

k4 = z.item("Mephit-Glass Charm", 'gem', 16, 'charm', "A bead of glass the wind mephits leave behind. It hums in a breeze.")
k5 = z.item("Windbreak Mantle", 'cloak', 16, 'ward', "Heavy felt. The plain's wind can't find a way in.")
z.quest('sp_mephits', 'Wind Over the Barrows', 16, 'sp_outrider_cadoc',
        "Wind mephits - little storm-devils - pour over the south-west downs and scour the barrows bare. The giants called them, the Abbess thinks: to blow the turf off the graves.\n\nWill you [still the wind]? Kill enough and the rest lose heart.",
        'still the wind',
        "Wind mephits are scouring the turf off the south-west barrows.",
        [
            hunt((400, 1000), "Kill the wind mephits on the south-west downs " + where((400, 1000), 'sp_outrider_cadoc'), 'wind mephit', 7),
            end_talk('sp_outrider_cadoc', "Tell Outrider Cadoc", "Quieter already. I can hear myself think. Mostly I'm thinking about giants.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [k4, k5]}})

# ======================================================================== The Giants' March (16-22)
g1 = z.item("Dartmoor Granite Chip", 'gem', 16, 'might', "Grey granite flecked with pink. It doesn't come from anywhere near here.")
g2 = z.item("Giant-Track Bracer", 'bracer', 16, 'ward', "Cadoc's own. He says he won't need it where he's going: anywhere else.")
z.quest('sp_footprints', 'Footprints Like Ponds', 16, 'sp_outrider_cadoc',
        "Giants. Salisbury's own we've always had - big, slow, keep to the south. These are different. They walk in lines, north, and they carry stones.\n\nWill you [scout their camps]? Kill a few if you must. I want to know where they came from.",
        'scout their camps',
        "Lines of giants are marching north across the plain, carrying stones.",
        [
            hunt((800, 1150), "Thin the giants on the southern plain " + where((800, 1150), 'sp_outrider_cadoc'), 'Salisbury giant', 3),
            search(Z, P(770, 1390), "Search a giants' camp", "a giant's cooking-pit", CRATE,
                   "Bones of whole oxen. And stacked by the fire, blocks of grey granite flecked with pink - Dartmoor granite, from three hundred miles south, carried here on their backs."),
            end_talk('sp_outrider_cadoc', "Tell Outrider Cadoc", "Dartmoor. They walked here from Dartmoor, carrying stones. To build what?\n\n...To mend the Dance. Or to take it home.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [g1, g2]}})

g3 = z.item("Boar-Herd's Tusk", 'neck', 18, 'might', "From the biggest of the giants' swine.")
g4 = z.item("Huntington Hunting Belt", 'belt', 18, 'finesse', "Coel's family has hunted the south downs for six generations.")
z.quest('sp_giants_swine', "The Giants' Swine", 18, 'coel_huntsman',
        "The giants drove herds of huge boars up with them - their larder on the hoof. The swine are rooting up every field from here to the river.\n\nCut down the herd and the giants go hungry. Hungry giants are slower. Will you [hunt the herd]?",
        'hunt the herd',
        "The giants' herds of huge boars are rooting up the south downs.",
        [
            hunt((838, 1248), "Hunt the giants' huge boars " + where((838, 1248), 'coel_huntsman'), 'huge boar', 6),
            end_talk('coel_huntsman', "Tell Coel", "That's a winter's bacon for the whole village. And a few hungry giants. I'll take that trade.", 'default'),
        ],
        {'default': {'text': "From Coel.", 'choice': [g3, g4]}})

g5 = z.item("Broken-Manacle Bracer", 'bracer', 21, 'might', "Giant-sized iron, cut down. The man who wore it was free for three weeks.")
g6 = z.item("Runaway's Cloak", 'cloak', 21, 'finesse', "Patched from sacking. It kept a man alive in the open all winter.")
z.quest('sp_runaways', 'The Men Who Ran South', 21, 'sp_outrider_cadoc',
        "Bandits in the far south - desperate ones, who fight like cornered dogs. Escaped, the locals say. From what, nobody knows.\n\nWill you [find out]? Don't expect them to talk.",
        'find out',
        "Escaped bandits in the far south fight like cornered dogs. Nobody knows what they escaped from.",
        [
            hunt((630, 1470), "Fight through the escaped bandits " + where((630, 1470), 'sp_outrider_cadoc'), 'escaped bandit', 3),
            hunt((617, 1477), "Defeat the escaped bandits' leader", 'escaped bandit leader', 1),
            search(Z, P(625, 1470), "Search their camp", "a heap of chains", CRATE,
                   "Manacles - giant-sized, cut down with a file. A scratched note: 'Cottrel sold us to the stone-men. We dug round the stones' feet till our hands bled. Never again.'"),
            end_talk('sp_outrider_cadoc', "Tell Outrider Cadoc", "Cottrel. The slave master in the north-east. He's selling men to the giants as diggers.\n\nThe Commander will want to hear this.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [g5, g6]}})

g7 = z.item("Cottrel's Key-Ring", 'ring', 21, 'finesse', "Every lock in his pens. All open now.")
g8 = z.item("Freedman's Torc", 'neck', 21, 'faith', "Plaited from cut rope by the people you freed.")
g9 = z.item("Slaver-Bane Mantle", 'cloak', 21, 'ward', "Osfrid had it made for whoever closed Cottrel's pens.")
z.quest('sp_cottrel', 'Slave Master Cottrel', 21, 'sp_osfrid',
        "Cottrel keeps pens in the far north-east, and he's been selling men to the giants to dig round the Dance. Every one of them was somebody's son.\n\nWill you [close the pens]? Bring friends. Cottrel's company are no farm-boys.",
        'close the pens',
        "Slave Master Cottrel sells captives to the giants as diggers from his pens in the far north-east.",
        [
            hunt((1432, 389), "Break Cottrel's company " + where((1432, 389), 'sp_osfrid'), 'slaver', 4),
            hunt((1439, 380), "Defeat Slave Master Cottrel", 'Slave Master Cottrel', 1,
                 text="Cottrel goes down among his own chains. 'The tin was good,' he says. 'Better than Camelot's silver.'"),
            choice('sp_osfrid', "Tell Watch-Commander Osfrid", "The pens are open? Good. There are eleven men in them, the outriders say.\n\nWe can [send them to Amesbury] - the Sisters will mend them. Or [send them to Camelot], to tell the Round Table what's on this plain. Witnesses are worth an army.",
                   [('send them to Amesbury', "Then the Abbess will have them. She's good with broken things.", 'ending:amesbury'),
                    ('send them to Camelot', "Then Camelot will hear it from men with giant-sized scars. They'll listen.", 'ending:camelot')]),
        ],
        {'amesbury': {'text': "The freed men send something.", 'items': [g8], 'choice': [g7, g9]},
         'camelot': {'text': "From the Pendragon's Watch.", 'items': [g9], 'choice': [g7, g8]}},
        requires='sp_runaways', group=True)

# ======================================================================== The Giants' Dance (22-26) - Deadly
h1 = z.item("Heel-Stone Bracer", 'bracer', 22, 'ward', "Set with a chip of the heel stone. It's cold at midsummer.")
h2 = z.item("Merlin's Mark Charm", 'gem', 22, 'mind', "Merlin's sign, copied from the stones: a star in a ring.")
z.quest('sp_the_dance', "The Giants' Dance", 22, 'sp_osfrid',
        "The giants hold the Dance itself now - granite giants out of Dartmoor, bigger than anything Salisbury ever grew. The Abbess says Merlin bound the stones with a mark on the heel stone.\n\nWill you [go to the Dance]? See the mark. Don't stay to fight what you can't.",
        'go to the Dance',
        "Granite giants from Dartmoor hold the Giants' Dance. Merlin's binding mark is on the heel stone.",
        [
            reach(Z, P(905, 860), "Reach the Giants' Dance " + where((905, 860), 'sp_osfrid'), "The stones rise over you, and giants walk between them like men among chairs.", r=30),
            hunt((900, 960), "Cut down the giants at the outer ring", 'Salisbury giant', 3),
            search(Z, P(940, 870), "Find Merlin's mark on the heel stone", "a stone with a mark worn almost smooth", CRATE,
                   "A star in a ring, worn nearly smooth - and scored across it, fresh, two marks: a claw like a dragon's, and a key under a crown, in red. Both of them want the stones."),
            end_talk('sp_osfrid', "Tell Osfrid", "A key under a crown. The Crimson - Morgana's - here too? The dragon wants his giants' stones back, and Morgana wants Merlin's ring for something of her own.\n\nAnd we're in the middle.", 'default'),
        ],
        {'default': {'text': "From the Pendragon's Watch.", 'choice': [h1, h2]}},
        requires='sp_paymaster')

h3 = z.item("Great Barrow Torc", 'neck', 24, 'might', "Gold, giant-sized, cut down to fit a man's neck. It still weighs like a millstone.")
h4 = z.item("Liglim's Mattock-Ring", 'ring', 24, 'finesse', "The raiders' master carried a gold mattock. This was its ring.")
h5 = z.item("Barrow-Dark Mantle", 'cloak', 24, 'ward', "Black wool that drinks the light. Made for barrows.")
z.quest('sp_giants_dead', "The Giants' Dead", 24, 'sp_abbess',
        "The great barrow in the south-east isn't a lord's grave. It's older than the feast - older than Merlin. The giants who first raised the stones are buried there, and the raiders have opened it to the bottom.\n\nWhat comes out of a giant's grave? Will you [go and see]? Take friends. Take many.",
        'go and see',
        "Tomb-raiders have opened the great barrow in the south-east - the grave of the giants who first raised the stones.",
        [
            hunt((1283, 1259), "Fight through the mercenary tomb-raiders at the dig " + where((1283, 1259), 'sp_abbess'), 'mercenary tomb raider', 3),
            hunt((1300, 1200), "Put down the giant skeletons risen from the barrow", 'giant skeleton', 3),
            hunt((1290, 1372), "Defeat Berik Liglim, master of the dig", 'Berik Liglim', 1,
                 text="Berik Liglim falls by the barrow mouth. Below, in the dark, something enormous turns over in its sleep."),
            end_talk('sp_abbess', "Tell the Abbess", "Something enormous. Yes. The Sisters have a name for what sleeps under the great barrow: Gogmagog, the last giant of Albion, that Corineus threw into the sea at Cornwall. They brought his bones home.\n\nGod keep him sleeping.", 'default'),
        ],
        {'default': {'text': "From the Sisters of Amesbury.", 'choice': [h3, h4, h5]}},
        requires='sp_the_dance', group=True)

h6 = z.item("Stone-Caller's Chant-Stone", 'gem', 26, 'mind', "A smooth grey pebble the oracle sang to. It still hums.")
h7 = z.item("Abbess's Ring", 'ring', 26, 'faith', "A queen's ring, plainly made. The Abbess wore it under her glove for forty years.")
h8 = z.item("Dance-Warden's Mantle", 'cloak', 26, 'ward', "Grey and red, Merlin's star at the shoulder. Given to those who held the Dance.")
h9 = z.item("Granite-Breaker Gauntlet-Ring", 'ring', 26, 'might', "Cut from a granite giant's knuckle-guard.")
z.quest('sp_stonecaller', 'The Stone-Caller', 26, 'sp_abbess',
        "The giants' oracle - the stone-caller - stands at the heart of the Dance and sings to the stones. Every night they lean a little further toward the south. When they fall, the giants will carry them home, and Merlin's binding with them.\n\nYou've done everything we asked. This is the last of it. Will you [silence the stone-caller]?",
        'silence the stone-caller',
        "The giants' stone-caller sings the Giants' Dance loose from Merlin's binding, to carry it south.",
        [
            reach(Z, P(915, 900), "Go into the heart of the Dance " + where((915, 900), 'sp_abbess'), "The singing fills the ring. The stones are leaning.", r=25),
            boss(Z, P(925, 935), "Silence Clochfaen the Stone-Caller", "Clochfaen falls among the stones, and the singing stops. Very slowly, the leaning stones settle back.",
                 'Clochfaen the Stone-Caller', STONECALLER, 27, "A giant robed in lichen turns from the stones, still singing. 'Little bones. The Dragon remembers when these stones were ours. So do we.'",
                 adds=[(GIANT, 'Salisbury giant', [24, 25])], every=30, count=1),
            search(Z, P(930, 940), "Search the stone-caller's place", "a granite tablet, freshly carved", CRATE,
                   "Giant-runes, and under them in plain Albion, as if for you: 'The White Dragon wakes in Dartmoor. Merlin's tower fell, and the red fought the white, and the white was beaten. Now the white remembers. The stones are his. Then the Sleeper.'",
                   give="the stone-caller's tablet"),
            choice('sp_abbess', "Bring the tablet to the Abbess",
                   "'Then the Sleeper.' He means Arthur, on Avalon. First the stones, then the king.\n\nI was a queen once. I know what a dragon's patience costs. Shall I [send to Camelot] with this, so the Round Table makes ready? Or will you [keep the tablet] and carry the warning yourself, south?",
                   [('send to Camelot', "Then Camelot will have it by the new moon. Thank you - for the dead, and for the living.", 'ending:camelot'),
                    ('keep the tablet', "Then carry it into the marsh, toward Avalon. Someone there will need to read it.", 'ending:south')]),
        ],
        {'camelot': {'text': "From the Abbess of Amesbury.", 'items': [h7], 'choice': [h6, h8, h9]},
         'south': {'text': "From the Abbess of Amesbury.", 'items': [h8], 'choice': [h6, h7, h9]}},
        requires='sp_the_dance', group=True,
        topics={'queen': "She smiles. 'A long time ago. It's not a thing I talk about. Ask Sir Bedwyr at Prydwen, if you must - he knew me then.'"})
