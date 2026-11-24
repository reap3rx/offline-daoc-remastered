"""Connacht's story quests (claude 2026-11-22, the zone brief in Zone Reviews) - see story_gen.py. Places: zone metres [x, y].

Moved out of story_hib.py with the Connacht rebuild, like Lough Derg:
    python tools/claude-version/story_gen.py story_connacht

Six arcs, 25 quests, one thread: the Voice of the Azure has made a bargain with the Amadan Dubh. The fool-king lends the
Azure Order his court's madness; in return the wicker fires feed the demon gate by Druim Ligen until it opens wide. Every
arc turns up a piece of it - blue-glass beads, azure fire on the moor, wicker cut from the Irewood, a jester at the keep.
Two old quests are folded in: Two Brothers (rowdies) and The Wicker Man (wickerman). The Fianna of Druim Ligen's arcs:
Ardee's Lost Sons, Wind on the Moors, The Demon Gate. The Order of the Rowan's: The Irewood Wakes, The Wicker Fields, The
Fool's Court. Quest givers live in Ardee, Basar, Druim Ligen and the Rowan grove in the Irewood.
"""
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE, RED_WOOD = 1882, 1876, 1347, 1876
M, F, OLD = 337, 365, 362
Z = 207
ZONES = []

z = Zone(Z, 'Connacht', 3, 'hib_connacht')
ZONES.append(z)


def hunt(at, goal, target, count, text=None, give=None, label=None):
    """A kill step on the zone's own monsters (they scale to you)."""
    s = {'type': 'kill', 'zone': Z, 'at': list(at), 'radius': 40, 'goal': goal, 'target': target, 'count': count}
    if text:
        s['text'] = text
    if give:
        s['give'] = {'name': give}
    if label:
        s['label'] = label
    return s


def tk(step, tier):
    step['mob']['tier'] = tier
    return step


def gives(step, name):
    step['give'] = {'name': name}
    return step


def wake(ending, chain):
    ending['wake_event'] = chain
    return ending


# ------------------------------------------------------------------ people
# Ardee
z.npc('aine_mother', 'Aine', [1362, 1262], 'f', 8, idle="My boys. Both my boys. One I put out, one ran after him.")
z.npc('cn_daire', 'Constable Daire', [1355, 1280], 'm', 22, guild='Fianna of Druim Ligen',
      idle="Ardee's quiet. I'd like it to stay quiet. That's the whole job.")
z.npc('cn_eabha', 'Druidess Eabha', [1380, 1290], 'f', 30, model=OLD, guild='Order of the Rowan',
      idle="Rowan over the door, iron under the step. Old ways. They still work.")
# Basar
z.npc('cn_conall', 'Reeve Conall', [1295, 700], 'm', 18, idle="Sheep, salmon and siabra. Basar's three troubles, and two of them are tasty.")
z.npc('cn_gormlaith', 'Seer Gormlaith', [1310, 690], 'f', 32, model=OLD, guild='Order of the Rowan',
      idle="The farmhands laugh in their sleep now. That's not a good sign. It's never a good sign.")
# Druim Ligen
z.npc('fiachra', 'Champion Fiachra', [1176, 70], 'm', 34, guild='Fianna of Druim Ligen',
      idle="My patrol went west. One came back. One's going to burn.")
z.npc('scout_aine', 'Scout Niamh', [1160, 64], 'f', 24, guild='Fianna of Druim Ligen',
      idle="Azure robes, wicker men, and a lot of singing. The west's gone strange.")
z.npc('cn_lorcan', 'Lorcan the Jester', [1170, 75], 'm', 20, model=318, size=40, guild='of Druim Ligen',
      idle="Why did the demon cross the river? To get to the other fire! ...No? Tough crowd.")
# the Irewood
z.npc('cn_ruadhnait', 'Elder Ruadhnait', [330, 820], 'f', 34, model=OLD, guild='Order of the Rowan',
      idle="The wood is old, and slow, and it does not forgive. Neither do I, much.")
z.npc('cn_cluricaun', 'Mac an Ol', [230, 900], 'm', 16, model=318, size=38, guild='a cluricaun, retired',
      idle="Retired. From what? From the lodge, from the cellar, from sobriety. Mostly sobriety.")
# out in the zone - quest givers you come across as you explore (owner 2026-11-23: "the quests are scattered throughout
# the zone as much as we can, so that it brings interest and reason to explore the zone")
z.npc('cn_brona', 'Brona', [1020, 760], 'f', 8, idle="He'd never leave the flock. Never. Not Lochlann.")
z.npc('cn_seanan', 'Old Seanan', [700, 860], 'm', 14, model=OLD, guild='keeper of the rings',
      idle="Seven stones. My father kept them, and his father. Now look at them.")
z.npc('cn_ultan', 'Fennid Ultan', [900, 610], 'm', 26, guild='Fianna of Druim Ligen',
      idle="I watch the tents. The tents watch me. Neither of us likes it.")
z.npc('cn_muadhan', 'Farmer Muadhan', [1365, 545], 'm', 20, idle="My boy laughs in his sleep. Then he gets up and walks.")
z.npc('cn_cuan', 'Ferryman Cuan', [630, 340], 'm', 22, idle="Six crossed this month, all young, all going west. None came back across.")
z.npc('colm_boy', 'Colm', [930, 1100], 'm', 4, size=42, during=['rowdies/colm'])
z.npc('cn_ronan', 'Ronan', [762, 168], 'm', 25, during=['wickerman/ronan'])
z.npc('cn_pookha', 'the Grey Pookha', [1560, 560], 'm', 34, model=414, guild='of no court',
      during=['cn_pookha_bargain/pookha', 'cn_pookha_bargain/bargain'])

# ======================================================================== Ardee's Lost Sons (the road-gang, 4 to 9) - Fianna
a1 = z.item("Market-Stall Bracer", 'bracer', 4, 'finesse', "Ardee's stall-holders wear these to keep their sleeves out of the butter.")
a2 = z.item("Constable's Whistle-Charm", 'gem', 4, 'charm', "Daire's spare whistle. One blast and every dog in Ardee barks.")
z.quest('cn_light_fingers', 'Light Fingers', 4, 'cn_daire',
        "Purses gone from the market, three days running. Nobody sees a thing, and then somebody's a week's wages short.\n\nIt's the villainous youths off the Tir na Nog road - I'd bet my boots. Will you [catch the thieves]? Start at the [stalls]; they always leave something.",
        'catch the thieves',
        "Purses are going missing in Ardee's market. Constable Daire blames the road-gang.",
        [
            search(Z, [1375, 1250], "Search under the cheese-stall in Ardee's market, just north-east of Constable Daire (click the glinting spot)", "a scuffed spot under the cheese-stall", CRATE,
                   "Boot prints in the dust, and a dropped bead - blue glass, cheap and bright. Nobody in Ardee wears blue glass.",
                   give='a blue-glass bead'),
            hunt([820, 1250], "Kill 4 villainous youths at the road-gang's west lookout, about 550 m west of Ardee along the road", 'villainous youth', 4, give='a stolen purse',
                 text="One of them was carrying a purse with an Ardee baker's mark - and a dozen more of those blue beads."),
            end_talk('cn_daire', "Bring the stolen purse to Constable Daire in Ardee's market", "Old Brigid's purse. She'll weep.\n\nAnd these beads... blue glass. The youths are spending them like coin. Somebody's paying them in it. I don't like it, and I don't know why I don't like it.", 'default'),
        ],
        {'default': {'text': "Take this, for your trouble.", 'choice': [a1, a2]}},
        topics={'stalls': "The cheese-stall. Always the cheese-stall. Thieves like cheese."})

# (Two Brothers, folded in: Ruairc's gang is paid in blue glass)
it_sling = z.item("Rowdy's Sling-Bracer", 'bracer', 6, 'finesse', "Every rowdy in Connacht carries a sling. Colm's was the worst-made. He's proud of it.")
it_hearth = z.item('Hearthstone Ring', 'ring', 6, 'ward', "A pebble from Aine's hearth, set in tin.")
it_brother = z.item("Brothers' Cord", 'belt', 6, 'might', "Two cords plaited together. Brothers in Connacht trade them.")
it_mother = z.item("Aine's Shawl", 'cloak', 6, 'mind', "A blue shawl, darned many times by a mother who sat up waiting.")
z.quest('rowdies', 'Two Brothers', 6, 'aine_mother',
        "My husband put our eldest, Ruairc, out of the house last spring for thieving. He went to the rowdies in the west - the gang of youths that rob the road.\n\nNow my little one, Colm, has run off after him. He's nine. He thinks it's an adventure. Will you [find Colm]? And - if you see Ruairc - tell him his mother asks after him.",
        'find Colm',
        "Aine's eldest son was put out of the house and joined the road-gang in the west. Now her youngest has run off after him.",
        [
            kill(Z, [934, 1167], "Kill 5 villainous youths on the road west of Ardee (about 450 m), near the road-gang's camp", 'villainous youth', 60167680, [4, 5], 5,
                 text="'Colm? The little one? He's with Ruairc's lot at the old camp. Ruairc's the boss now.'"),
            reach(Z, [920, 1100], "Find the rowdies' camp at the road-gang's north lookout, about 500 m north-west of Ardee", "A ragged camp of boys and young men. A little lad in a too-big cap is trying very hard to look tough.", r=20),
            boss(Z, [941, 1085], "Defeat the rowdies' leader at the north lookout", "The young man drops his cudgel and sits down in the mud. 'Fine. FINE. Take him home. He's a terrible thief anyway.'",
                 'Ruairc the Rowdy', 60165444, 8, "A tall young man with his mother's eyes steps in front of the little one. 'He's my brother. He stays with me.'",
                 objective='Defeat Ruairc', hp=2.0, adds=[(60165444, 'rowdy', [5, 6])], every=30, count=1),
            L('colm', talk('colm_boy', "Talk to Colm, the little boy at the north lookout", "Ruairc said I could be in the gang! I can throw a stone further than anyone! ...Is Mam cross?\n\nRuairc says he can't come home because Da said. But he wants to. He cries at night. And a man in a blue robe pays him in pretty beads to keep the road busy. Don't tell him I [told].", kw='told')),
            choice('aine_mother', "Go back to Aine in Ardee and tell her about her boys",
                   "COLM. You - come here. Come HERE.\n\n...You saw Ruairc? How did he look? Is he thin? Did he ask after me?\n\nHis father swore he'd never set foot in the house again. If I [bring both home], his father and I will have words, and maybe worse. Or I take [only Colm], and keep the peace, and Ruairc stays out there. Tell me what to do. I've been asking the fire all year.",
                   [('bring both home', "Then go back and tell him his mother says come home. And if his father says a word, his father can sleep in the byre.", 'ending:both'),
                    ('only Colm', "Only Colm. ...Gods forgive me. I'll leave a loaf on the west road every week. Maybe he'll find it.", 'ending:one')]),
        ],
        {'both': {'text': "Take this. Both my boys are home.", 'items': [it_brother], 'choice': [it_sling, it_hearth]},
         'one': {'text': "Take this.", 'tragic': True, 'items': [it_mother], 'choice': [it_sling, it_hearth]}},
        requires='cn_light_fingers')

a3 = z.item("Bead-Man's Satchel Belt", 'belt', 8, 'finesse', "It carried a fortune in blue glass. It carries your things now, which are worth more.")
a4 = z.item("Lookout's Torc", 'neck', 8, 'might', "Twisted bronze off the gang's north lookout. Somebody's grandmother's, probably.")
a5 = z.item("Blue-Glass Ward", 'gem', 8, 'ward', "One of the Azure Order's beads, cracked on purpose. The Rowan say a broken bead can't buy anyone.")
z.quest('cn_the_bead_man', 'The Bead Man', 8, 'cn_daire',
        "Colm told his mother about a man in a blue robe who pays the gang in beads. Blue robe - that's the Azure Order, the fire-worshippers up west. What do they want with Ardee's road?\n\nThe boy says the bead man comes to the gang's north lookout at dusk. Will you [meet the bead man]? Bring him to me if you can. Bring me his satchel if you can't.",
        'meet the bead man',
        "A man in a blue robe pays the road-gang in blue-glass beads. He meets them at their north lookout.",
        [
            reach(Z, [940, 1080], "Go to the road-gang's north lookout, about 500 m north-west of Ardee", "A fire, a pot, three youths pretending not to wait for someone. Up the road, a lantern with a blue glass shade.", r=25),
            tk(kill(Z, [945, 1075], "Kill the bead man's 3 guards at the north lookout", "bead man's bodyguard", 60167680, 7, 3,
                    text="The bodyguards go down. The man with the blue lantern drops it and draws a knife."), 'green'),
            gives(boss(Z, [945, 1070], "Defeat the bead man when he comes to the north lookout", "The bead man folds up in the road. His satchel spills blue glass everywhere - and a folded note.",
                       'the Bead Man', 60158182, 9, "A thin man in a blue robe, smiling with his mouth only. 'The road is ours to keep busy. Who sent you?'",
                       objective='Defeat the Bead Man', hp=1.8, adds=[(60167680, 'villainous youth', [7, 8])], every=30, count=1), "the bead man's note"),
            end_talk('cn_daire', "Bring the bead man's note to Constable Daire in Ardee", "'Keep the road busy. Keep the Fianna looking south. The Voice thanks you.'\n\n...The Voice. That's what the Azure Order calls its high priest. Why would a fire-cult want the Fianna looking south? What's north? Druim Ligen. The gate. Gods.", 'default'),
        ],
        {'default': {'text': "Take this. I'm sending the note to Champion Fiachra tonight.", 'choice': [a3, a4, a5]}},
        requires='rowdies')

a6 = z.item("Road-Boss's Knuckle Ring", 'ring', 9, 'might', "Heavy, cruel and very well made. Like its owner, minus the well made.")
a7 = z.item("Tir na Nog Road Cloak", 'cloak', 9, 'ward', "The road-wardens' grey. Constable Daire had it made for you.")
a8 = z.item("Hedgerow Sash", 'belt', 9, 'finesse', "Woven from hedge-thorn and tough as wire. The gang hid in the hedgerows. Now you know how.")
z.quest('cn_road_gang', 'The Road-Gang', 9, 'cn_daire',
        "No more beads, no more gang - that's my thinking. Their boss sits in the camp by the Tir na Nog road with every lad in Connacht who's lost his way.\n\nThe Fianna will back us. Take friends and [break the gang]. The lads who run, let them run home.",
        'break the gang',
        "Without the bead man's pay the road-gang is shaky. Its boss still holds the camp by the Tir na Nog road.",
        [
            hunt([935, 1165], "Kill 4 rowdies at the road-gang's camp, about 450 m west of Ardee", 'rowdy', 4),
            hunt([935, 1165], "Defeat the road-gang boss in the middle of the gang camp", 'road-gang boss', 1,
                 text="The boss goes down. Half the camp throws down its cudgels; the other half runs for the hills - west, toward the Moors."),
            end_talk('cn_daire', "Return to Constable Daire in Ardee", "The road's quiet. Aine says Ruairc's been seen in the market buying bread with honest coin.\n\nThat's a good day's work. Take this - and keep an ear out. Fiachra says the blue robes are busy on the Moors, too.", 'default'),
        ],
        {'default': {'text': "From Ardee, with thanks.", 'items': [a7], 'choice': [a6, a8]}},
        requires='cn_the_bead_man', group=True)

# ======================================================================== Wind on the Moors (wind ghouls and grave rings, 7 to 12) - Fianna
b1 = z.item("Shepherd's Crook Charm", 'gem', 7, 'charm', "Carved from the head of a scorched crook. It still smells of sheep.")
b2 = z.item("Moor-Wind Bracer", 'bracer', 7, 'finesse', "Leather cured on the Moors. The wind gets into it and never quite leaves.")
z.quest('cn_lost_flock', 'The Lost Flock', 7, 'cn_brona',
        "My Lochlann took the flock up onto the Moors last week, same as every year. The flock came back. He didn't.\n\nThe wind ghouls have been bad since spring - since the night somebody saw a blue fire crossing the heath. Will you [look for Lochlann]? His fold is just west of here, out past the ghoul hollows.",
        'look for Lochlann',
        "Brona's husband, the shepherd Lochlann, went missing on the Moors, where the wind ghouls have grown bold.",
        [
            reach(Z, [900, 760], "Find Lochlann's sheep-fold, about 120 m west of Brona", "A stone fold, its gate open, wool on the thorns. The wind howls in the gaps - and in the howl, voices.", r=25),
            search(Z, [905, 765], "Search the sheep-fold for a sign of Lochlann (click the glinting spot)", "a scorched shepherd's crook", CRATE,
                   "Lochlann's crook, burned at the head - not red-burned, blue-burned, the wood gone glassy. Tracks lead off toward the ghoul hollows.",
                   give="Lochlann's scorched crook"),
            hunt([880, 700], "Kill 5 wind ghouls in the hollow just north-west of the fold", 'wind ghoul', 5,
                 text="The last ghoul blows apart like smoke. In the hollow lies a cloak - Lochlann's - and no Lochlann."),
            end_talk('cn_brona', "Bring the scorched crook to Brona, on the Moors east of the fold", "Blue fire. Like the stories.\n\nHe'd want me to keep the flock going. So I will. Reeve Conall in Basar should hear about that fire - tell him, if you're passing.", 'default'),
        ],
        {'default': {'text': "Take this. It's the best of what we had.", 'choice': [b1, b2]}})

b3 = z.item("Grave-Ring Pendant", 'neck', 9, 'faith', "A chip of the ring-stone, holed and strung. The old dead slept better with it in place.")
b4 = z.item("Barrow-Wight's Girdle", 'belt', 9, 'ward', "Bronze links from a broken grave. You put the bones back. You kept the belt.")
b5 = z.item("Pawn's Grip Ring", 'ring', 9, 'might', "Off a skeleton's finger. It was holding on very tightly.")
z.quest('cn_fallen_rings', 'The Fallen Rings', 9, 'cn_seanan',
        "The grave rings - the circles of standing stones round the barrows - kept the dead down for a thousand years. My family's kept the rings nearly as long. Now the dead walk out of them like it's market day.\n\nSomebody's knocked the ring-stones down. Will you [go to the rings] and find out who? The largest is just west of here.",
        'go to the rings',
        "The dead are walking out of the Moors' old grave rings, and Old Seanan, their keeper, says somebody knocked the stones down.",
        [
            reach(Z, [630, 870], "Go to the largest grave ring, about 70 m west of Old Seanan", "Three of the seven stones are down. Not fallen - pushed, and burned where the hands went.", r=25),
            hunt([630, 870], "Kill 5 skeletal pawns at the grave ring", 'skeletal pawn', 5),
            search(Z, [636, 876], "Search the toppled stone in the grave ring (click the glinting spot)", "a toppled ring-stone", CRATE,
                   "Scorched into the stone's face: a ring of little flames, the Azure Order's sign. And melted into the grass, a blue-glass bead.",
                   give='a blue-scorched chip of stone'),
            end_talk('cn_seanan', "Bring the stone chip to Old Seanan by the grave rings", "The Azure Order's mark. Up here? They burn men in wicker over in the west. What do they want with old bones?\n\nThe ghouls rose the night of the blue fire, and the rings fell the same week. Somebody's stirring the whole Moor. Tell Reeve Conall in Basar.", 'default'),
        ],
        {'default': {'text': "Take this. Put the dead back, and you've earned a dead man's pay.", 'choice': [b3, b4, b5]}})

b6 = z.item("Windaille's Howl-Bracer", 'bracer', 11, 'finesse', "It whistles faintly when you run.")
b7 = z.item("Fire-Carrier's Lantern-Charm", 'gem', 11, 'mind', "The blue shade off the fire-carrier's lantern, cracked and set. It glows when the Azure Order is near.")
z.quest('cn_windaille_and_bas', 'Windaille and Bas', 11, 'cn_conall',
        "Lochlann's boy says the ghouls have a pair of masters - two great ones, called Windaille and Bas, who lair on the high ground above the siabra tents. The boy says the man with the blue lantern goes there at night.\n\nWill you [hunt Windaille and Bas]? Take a friend; they don't fight fair.",
        'hunt Windaille and Bas',
        "Two great ghouls, Windaille and Bas, lead the wind ghouls - and a man with a blue lantern visits them at night.",
        [
            hunt([853, 523], "Defeat Windaille, about 480 m west of Basar, just north-east of the siabra raiders' tents", 'Windaille', 1),
            hunt([853, 523], "Defeat Bas, who keeps close beside Windaille", 'Bas', 1, text="Bas tears apart into a gale and is gone. Where the two of them laired: a lantern, its shade of blue glass."),
            search(Z, [860, 530], "Search the lair where Windaille and Bas stood (click the glinting spot)", "a blue-shaded lantern", LANTERN,
                   "An Azure lantern, its fire still burning blue without oil. Under it, a scrap: 'Carry the fire over the rings each new moon until the Moor is ours.'",
                   give="the fire-carrier's lantern"),
            end_talk('cn_conall', "Bring the blue-shaded lantern to Reeve Conall in Basar", "Every new moon. That's two days off.\n\nSomebody walks this out over the Moor on purpose. Rouses the ghouls, wakes the dead, keeps Basar and the Fianna busy. Two days. Will you be there?", 'default'),
        ],
        {'default': {'text': "Take this - and be there.", 'choice': [b6, b7]}},
        requires='cn_fallen_rings', group=True)

b8 = z.item("Four Winds Cloak", 'cloak', 12, 'ward', "Grey, blue, white and black: a quarter for each wind. The Moor's shepherds bless it.")
b9 = z.item("Fianna Signal-Horn Charm", 'gem', 12, 'might', "A Fianna horn-tip. One note and Druim Ligen hears it.")
b10 = z.item("Rowan-Berry Bracelet", 'bracer', 12, 'faith', "Druidess Eabha sent it from Ardee. 'For the one who put the fire out.'")
z.quest('cn_fire_carrier', 'The Fire-Carrier', 12, 'cn_conall',
        "It's the new moon. If the boy's right, the fire-carrier walks the Moor tonight with his blue lantern, ring to ring.\n\nWait for him at the high stones. Bring friends. And [stop the fire-carrier], before the dead and the ghouls come with him.",
        'stop the fire-carrier',
        "On the new moon an Azure fire-carrier walks the Moor, rousing the ghouls and the dead.",
        [
            reach(Z, [960, 790], "Go to the high stones on the Moors, about 350 m west of Basar, and wait there", "Midnight. The wind drops. Across the heath, a blue light comes walking, and the ghouls rise round it like dogs round a master.", r=25),
            gives(boss(Z, [960, 790], "Defeat the fire-carrier when he comes to the high stones", "The fire-carrier falls and his blue fire gutters out. The ghouls stop. The wind goes back to being wind.",
                       'the Fire-Carrier', 60158182, 13, "A hooded idolater lifts a blazing blue lantern. 'The Voice needs the Moor busy. You'll do as well as sheep.'",
                       objective='Defeat the Fire-Carrier', hp=2.0, adds=[(60167968, 'wind ghoul', [10, 11])], every=25, count=2), "the fire-carrier's brand"),
            choice('cn_conall', "Bring the fire-carrier's brand to Reeve Conall in Basar",
                   "An Azure brand. A fire that burns blue and doesn't need feeding.\n\nThe Fianna will want this - proof that the Azure Order is making war. But the druids in Ardee, the Rowan, say a fire like that should be put out properly, not carried about. Do I send it to [the Fianna], or to [the Rowan]?",
                   [('the Fianna', "Druim Ligen, then. Fiachra can wave it under the high king's nose.", 'ending:fianna'),
                    ('the Rowan', "To Druidess Eabha. She'll know how to kill a fire like that.", 'ending:rowan')]),
        ],
        {'fianna': wake({'text': "Take this - from Basar, and from the Fianna.", 'items': [b8], 'choice': [b9, b10]}, 'connacht_anger_sprites'),
         'rowan': wake({'text': "Take this - from Basar, and from the Rowan.", 'items': [b8], 'choice': [b9, b10]}, 'connacht_anger_sprites')},
        requires='cn_windaille_and_bas', group=True)

# ======================================================================== The Irewood Wakes (13 to 20) - Rowan
c1 = z.item("Withy-Cord Belt", 'belt', 13, 'finesse', "Blue cord off a bundle of stolen withies. The Order of the Rowan took the colour out of it.")
c2 = z.item("Sapling-Heart Bracer", 'bracer', 13, 'ward', "Living bark, gently taken. It grows a little in spring.")
z.quest('cn_angry_wood', 'The Angry Wood', 13, 'cn_ruadhnait',
        "The Irewood is the oldest wood in Connacht, and it's awake. It walks. It strikes. It has never done that in my lifetime.\n\nTrees don't wake for nothing. Something's hurting it. Will you [find the hurt]? Start on the east edge, where the young trees are angriest.",
        'find the hurt',
        "The Irewood has woken and turned on everyone who walks in it. Elder Ruadhnait of the Rowan wants to know why.",
        [
            reach(Z, [420, 560], "Go to the east edge of the Irewood, about 280 m north of Elder Ruadhnait's grove", "Stumps. Dozens of them, fresh-cut, the sap still bleeding. And the saplings round them standing up on their roots.", r=25),
            hunt([400, 600], "Kill 4 irewood saplings at the edge of the wood", 'irewood sapling', 4),
            search(Z, [425, 555], "Search the cut stumps at the wood's edge (click the glinting spot)", "a stack of cut withies", CRATE,
                   "Withies - long, whippy willow and hazel - cut and bundled, ready for weaving. Tied with blue cord. Enough for a wicker man three times the height of a house.",
                   give='a bundle of withies'),
            end_talk('cn_ruadhnait', "Bring the cut withies to Elder Ruadhnait in the Rowan grove, in the Irewood (far west)", "Blue cord. The Azure Order.\n\nThey're cutting my wood to weave their wicker men. The wood knows. The wood will not forgive. And I'm not sure I want it to.", 'default'),
        ],
        {'default': {'text': "Take this. The wood gave it - I asked nicely.", 'choice': [c1, c2]}})

c3 = z.item("Cellar-Key Ring", 'ring', 15, 'charm', "Mac an Ol's cellar key, bent into a ring. He says he'll never need it again. He'll need it again.")
c4 = z.item("Lodge-Brewer's Apron Cloak", 'cloak', 15, 'ward', "It has stains older than you. Some of them are ale.")
c5 = z.item("Cluricaun Thimble Charm", 'gem', 15, 'finesse', "A thimble of whiskey, frozen in amber. A cluricaun's idea of a keepsake.")
z.quest('cn_cluricaun_lodge', 'The Cluricaun Lodge', 15, 'cn_ruadhnait',
        "The cluricauns know everything that happens in the Irewood. They see it all - usually twice, and through a glass.\n\nOne of them, Mac an Ol, was thrown out of the lodge and lives under a hedge north of here. He might talk, for a price. Will you [ask Mac an Ol]?",
        'ask Mac an Ol',
        "A cluricaun thrown out of the Irewood lodge might know who's cutting the wood - for a price.",
        [
            talk('cn_cluricaun', "Talk to Mac an Ol, the retired cluricaun, about 130 m south-west of Elder Ruadhnait", "Who's cutting the wood? Course I know. Everybody knows. But knowing's thirsty work.\n\nThe brewer's lads took my old cellar, south of the lodge. Every cask in it is mine by rights. Clear 'em out and I'll [tell you everything].", kw='tell you everything'),
            hunt([200, 1040], "Kill 4 cluricauns in the old cellar, about 140 m south of Mac an Ol", 'cluricaun', 4,
                 text="The cellar's yours - or Mac an Ol's. Behind the casks: a cart's wheel ruts, and blue cord snagged on a nail."),
            end_talk('cn_cluricaun', "Return to Mac an Ol, south-west of the Rowan grove", "Ahh. My cellar. My casks. My life's work.\n\nRight. The woodcutter's called Broc. Big lad in Azure blue, cuts by the old oaks on the east edge. Pays the brewer in blue beads to let his carts through the lodge woods. Every bead buys a barrel, see. Never trust a cluricaun with a barrel in sight. Except me.", 'default'),
        ],
        {'default': {'text': "And take this. Don't drink it. Or do. I'm not your mam.", 'choice': [c3, c4, c5]}},
        requires='cn_angry_wood')

c6 = z.item("Woodcutter's Axe-Haft Bracer", 'bracer', 17, 'might', "Cut from Broc's own axe-haft. The wood is sorry about the rest of it.")
c7 = z.item("Order-Tally Charm", 'gem', 17, 'mind', "A notched tally stick from Broc's cart. Forty notches, one cut through.")
z.quest('cn_broc', 'The Woodcutter', 17, 'cn_ruadhnait',
        "Broc. An Azure woodcutter, with men and carts, felling my wood by the old oaks.\n\nI'm too old to swing anything heavier than a sickle. You aren't. Will you [stop Broc]? Find out how much more he means to cut.",
        'stop Broc',
        "Broc the Woodcutter fells the Irewood for the Azure Order's wicker men.",
        [
            hunt([470, 520], "Defeat Broc the Woodcutter at his camp, about 330 m north of Elder Ruadhnait's grove", 'Broc the Woodcutter', 1,
                 text="Broc goes down among his own stumps. The irewoods stand very still round you, watching."),
            search(Z, [478, 515], "Search Broc's cart beside his camp (click the glinting spot)", "a woodcutter's cart", CRATE,
                   "A tally stick with forty notches, and an order in a fine hand: 'Forty cartloads for the great burning. The Voice will repay the wood in fire.'",
                   give="Broc's order-tally"),
            end_talk('cn_ruadhnait', "Bring Broc's tally to Elder Ruadhnait in the Rowan grove", "Forty cartloads. For one fire.\n\nWhat do they mean to burn, that needs a wicker man so large? ...And the wood. The wood's heart is sick. I can feel it from here. Come back to me when you've rested.", 'default'),
        ],
        {'default': {'text': "Take this. The wood remembers who stopped the axe.", 'choice': [c6, c7]}},
        requires='cn_cluricaun_lodge')

c8 = z.item("Heartwood Torc", 'neck', 20, 'faith', "A ring of living heartwood. Ruadhnait grew it round your neck while you slept, which you'll admit is a little alarming.")
c9 = z.item("Blight-Breaker Ring", 'ring', 20, 'might', "A ring of blight-burnt bark, hardened to iron. What hurt the Elder made this strong.")
c10 = z.item("Seedling Mantle", 'cloak', 20, 'ward', "Green as new leaves. It smells of rain after a hot day.")
c11 = z.item("Rowan-Grove Sash", 'belt', 20, 'mind', "The Order of the Rowan's sash, red with berries. They don't give it lightly.")
z.quest('cn_heart_of_the_irewood', 'The Heart of the Irewood', 20, 'cn_ruadhnait',
        "The wood's heart is an elder irewood, older than Ardee. Broc's men poured azure fire into its roots - to make it angry, to keep the Rowan busy, I don't know.\n\nI can plant a seedling of the heart beside it and draw the blight out. It will fight me. Everything in the wood will fight me. Will you [stand with me]? Bring friends.",
        'stand with me',
        "The Irewood's heart, an ancient elder irewood, is poisoned with azure fire. Elder Ruadhnait means to draw the blight out.",
        [
            reach(Z, [300, 700], "Go to the heart of the Irewood, about 120 m north of Elder Ruadhnait's grove", "A clearing round a tree so old it has no shape, only bulk. Its bark burns blue in the cracks. The ground shakes when it breathes.", r=30),
            defend(Z, [300, 700], "Keep Elder Ruadhnait alive while she plants the seedling (the wood attacks in waves)", "The seedling takes. The blue fire in the Elder's bark flickers - and the Elder itself tears up its roots and walks.",
                   'Elder Ruadhnait', 60163820, 20, "Ruadhnait kneels and starts to sing. The whole wood answers - with branches.",
                   [(60168131, 'young irewood', [17, 18]), (60162489, 'irewood sapling', [16, 17])], 'Keep Elder Ruadhnait safe', model=F,
                   duration=120, every=25, count=2,
                   then_boss={'tpl': 60168131, 'name': 'the Blight-Burnt Elder', 'lv': 22, 'hp': 2.4,
                              'announce': "The Elder irewood looms over the clearing, blue fire pouring from its cracks. It does not know friend from foe any more.",
                              'objective': 'Defeat the Blight-Burnt Elder'},
                   thanks="The seedling's in. Now - the old one has to come down. Gently, if you can. You can't."),
            choice('cn_ruadhnait', "Speak to Elder Ruadhnait at the heart of the Irewood",
                   "It's down. The blight is in the dead wood now, not the living.\n\nWe can [burn the blight] - fire against fire, and the Irewood is clean but scarred. Or we can [let it rot] slowly, as wood should, and trust the seedling to outgrow it. Slower. Kinder. Riskier.",
                   [('burn the blight', "Fire against fire. The Azure Order would laugh. Let them.", 'ending:burned'),
                    ('let it rot', "As wood should. The seedling will be a heart in a hundred years. I won't see it. You might.", 'ending:rotted')]),
        ],
        {'burned': wake({'text': "Take this, from the grove.", 'items': [c11], 'choice': [c8, c9, c10]}, 'connacht_streaming_wisps'),
         'rotted': wake({'text': "Take this, from the grove.", 'items': [c11], 'choice': [c8, c9, c10]}, 'connacht_streaming_wisps')},
        requires='cn_broc', group=True)

# ======================================================================== The Wicker Fields (20 to 30) - Rowan
d1 = z.item("Recruiter's List-Case Belt", 'belt', 21, 'finesse', "A leather tube for rolled lists. The list in it is ash now.")
d2 = z.item("Azure-Stitch Bracer", 'bracer', 21, 'mind', "Unpicked from an acolyte's robe. Blue thread holds a ward better than most.")
z.quest('cn_blue_robes', 'Blue Robes', 21, 'cn_cuan',
        "Four lads from Ardee and two girls from Basar - I rowed them all across this month. Going west, they said, to find work. Nobody finds work in the west.\n\nThe Azure Order recruits at their camp just up the river from here. Go and [see who's joined], and find their list if they keep one.",
        "see who's joined",
        "Young people from Ardee and Basar are going west to join the Azure Order.",
        [
            reach(Z, [570, 300], "Go to the Azure Order's camp, about 70 m north-west of Ferryman Cuan", "Blue tents, a fire burning without smoke, and a dozen young faces in new blue robes, chanting. Some of them you've seen in Ardee's market.", r=25),
            hunt([556, 274], "Kill 5 azure acolytes at the camp", 'azure acolyte', 5,
                 text="The acolytes scatter. The new recruits run with them - or run home. You can't tell which."),
            search(Z, [560, 282], "Search the recruiter's tent in the middle of the camp (click the glinting spot)", "the recruiter's writing-box", CRATE,
                   "A list of names, each with a village and a price in beads. At the bottom: 'Enough hands for the great burning. The Voice wants them by the new moon after next.'",
                   give="the recruiter's list"),
            end_talk('cn_cuan', "Bring the recruiter's list to Ferryman Cuan by the river", "Dara. Ciaran. The miller's girl. I rowed every one of them across.\n\n'The great burning.' They're building something enormous out there. Druidess Eabha in Ardee has to see this - take her word of it, if you're going that way.", 'default'),
        ],
        {'default': {'text': "Take this. I'll be rowing them home, if I can.", 'choice': [d1, d2]}})

d3 = z.item("Withe-Bark Ring", 'ring', 23, 'might', "From the oldest wickerman. It's still warm. It's always going to be warm.")
d4 = z.item("Phantom-Ash Charm", 'gem', 23, 'faith', "Ash from a wicker that walked. The Rowan say it remembers who burned in it.")
z.quest('cn_withe', 'The Oldest Wicker', 23, 'cn_eabha',
        "The phantom wickermen are the ghosts of the burnings - each one a wicker man that burned with someone inside. The oldest is called Withe. He walks the north bank of the river past the fields and the others follow him.\n\nPut Withe down and the rest lose their way for a while. Will you [lay Withe to rest]?",
        'lay Withe to rest',
        "Withe, the oldest of the phantom wickermen, leads the rest. He walks the north bank of the river past the Wicker Fields.",
        [
            reach(Z, [880, 110], "Find Withe, the oldest wicker man, on the river's north bank, about 300 m west of Druim Ligen", "A wicker giant, blackened, still smouldering in the wet grass. It turns slowly towards you.", r=30),
            hunt([880, 110], "Defeat Withe", 'Withe', 1,
                 text="Withe sags and folds down into charred withies. For a moment, something inside it looks out at you - grateful, you think - and then it's just wicker."),
            end_talk('cn_eabha', "Return to Druidess Eabha in Ardee", "Withe's down. The wickermen will wander a few nights without him.\n\nFiachra's sent word from Druim Ligen - a patrol of his was taken by the Order, and one of them is meant for the next wicker. Go to him. Now.", 'default'),
        ],
        {'default': {'text': "Take this. And hurry.", 'choice': [d3, d4]}},
        requires='cn_blue_robes')

# (The Wicker Man, folded in)
it_wicker = z.item('Wicker-Ash Charm', 'gem', 27, 'mind', "Ash from a wicker man that never burned its captive.")
it_azure = z.item("Azure Robe-Clasp", 'belt', 27, 'faith', "The clasp of an Azure Order robe. Ronan kept his.")
it_champion = z.item("Champion's Ring", 'ring', 27, 'might', "Fiachra's own. The Champions of Connacht give them for valour.")
it_patrol = z.item('Patrol-Spear Bracer', 'bracer', 27, 'finesse', "The haft of a patrol's spear, cut down and bound.")
z.quest('wickerman', 'The Wicker Man', 27, 'fiachra',
        "My patrol went west to watch the Azure Order - the idolaters in blue who've been gathering by the old stones. One man came back. He says the rest are dead, except Ronan.\n\nThey've built a wicker man. At the next moon, Ronan goes inside it and they set it alight. Scout [Niamh] has seen their camp. Will you [save Ronan]?",
        'save Ronan',
        "The Azure Order captured a patrol from the keep; the last survivor is to be burned in a wicker man.",
        [
            talk('scout_aine', "Ask Scout Niamh at Druim Ligen about the Azure camp",
                 "They've idolaters chanting at the stones, west and north. Past them, a wicker man three times my height. Haunted, too - the old wickermen they've burned walk about at night. Go through the [idolaters] first. They'll raise the alarm otherwise.", kw='idolaters'),
            kill(Z, [684, 197], "Kill 5 azure idolaters at the farther wicker circle, about 500 m west of Druim Ligen", 'azure idolater', 60158182, [24, 25], 5),
            search(Z, [700, 192], "Search the idolaters' altar beside that circle (click the glinting spot)", "a patrol's broken spear", CRATE,
                   "A Connacht patrol spear, snapped and laid on the altar as an offering. A blue robe folded beside it - a new one, a recruit's - with Ronan's name pinned to it."),
            kill(Z, [788, 153], "Destroy 4 phantom wickermen at the nearer wicker circle, about 400 m west of Druim Ligen", 'phantom wickerman', 60164910, [26, 27], 4),
            defend(Z, [762, 168], "Free Ronan from the wicker man at the nearer circle", "The idolaters scatter. Ronan climbs down from the wicker man, coughing, a blue robe still over his arm.",
                   'Ronan', 60158182, 25, "You hack at the wicker. Ronan yells from inside. Every idolater on the hill turns.",
                   [(60158182, 'azure idolater', [25, 26])], 'Keep Ronan alive', model=M, duration=90,
                   then_boss={'tpl': 60167712, 'name': 'Maelgwn, Voice of the Azure', 'lv': 30, 'announce': "A tall idolater in deep blue. 'The fire wanted him. It will have you instead.'", 'objective': 'Defeat Maelgwn'},
                   thanks="I'm out. I'm out. I'm OUT."),
            L('ronan', choice('cn_ronan', "Talk to Ronan at the nearer wicker circle",
                   "They gave me this robe. Said I could take it and live, if I'd join. I didn't. But I could have. I thought about it.\n\nWith it, I could walk into any Azure camp in Hibernia. Find out what they're planning. Tell the Champions. If I [go undercover], nobody can know - not even my mother. Or I [come home], burn the robe, and forget the whole thing.",
                   [('go undercover', "Then I'm dead, as far as anyone knows. Tell Fiachra the truth. Only Fiachra.", 'next:spy'),
                    ('come home', "Home. Gods, yes. And the robe goes in the first fire I see.", 'next:home')])),
            L('spy', end_talk('fiachra', "Report to Champion Fiachra at Druim Ligen", "He's gone into the Azure, wearing their robe. His mother's been told he died a hero.\n\nGods. He's braver than I am. If word comes, it'll come to me. Take this - and say nothing to anyone.", 'spy')),
            L('home', end_talk('fiachra', "Report to Champion Fiachra at Druim Ligen", "Ronan's home. He burned the robe in the courtyard, and the whole keep cheered.\n\nOne man from six. It's not a victory. But it's one man. Take this.", 'home')),
        ],
        {'spy': {'text': "Say nothing to anyone.", 'items': [it_azure], 'choice': [it_champion, it_patrol]},
         'home': {'text': "Take this.", 'items': [it_wicker], 'choice': [it_champion, it_patrol]}},
        topics={'Niamh': "My best scout. By the gate."}, requires='cn_withe')

d5 = z.item("Fire-Chant Scroll Case", 'belt', 28, 'mind', "It held the Order's fire-chant. Ruadhnait burned the scroll and gave you the case. 'The case did nothing wrong.'")
d6 = z.item("Idolater's Ember Ring", 'ring', 28, 'finesse', "A blue ember sealed in glass. The Rowan put it out; the glass kept the colour.")
d7 = z.item("Rowan-Thorn Bracer", 'bracer', 28, 'ward', "Rowan wood and blackthorn, bound with red thread. Fire won't take it.")
z.quest('cn_names_for_the_fire', 'Names for the Fire', 28, 'cn_eabha',
        "Maelgwn was only a Voice - one of the Order's lesser priests. The Voice of the Azure, their high priest, still lives, and the great burning is still coming.\n\nThe idolaters at the circles chant from scrolls. Bring me one of their [fire-chants] and Elder Ruadhnait can read what they mean to burn.",
        'fire-chants',
        "The great burning is still coming. Druidess Eabha wants the idolaters' fire-chant read.",
        [
            hunt([690, 200], "Kill 5 azure idolaters at the farther wicker circle, about 500 m west of Druim Ligen, for their fire-chant", 'azure idolater', 5, give='a fire-chant scroll'),
            talk('cn_ruadhnait', "Take the fire-chant scroll to Elder Ruadhnait in the Rowan grove, in the Irewood (far west)", "Old words. Older than the Order, older than me.\n\nIt's not a chant to a god. It's a chant to a door. 'Burn the wood, burn the hands, and the gate in the north opens wide for the fool-king's friends.' The [demon gate] at Druim Ligen. They're feeding it.", kw='demon gate'),
            end_talk('cn_eabha', "Return to Druidess Eabha in Ardee", "Feeding the gate. With fire. With people.\n\nThe great burning is south of the river, past the fields - the Order's biggest wicker. Ruadhnait says the new moon is in three days. We'll need everyone.", 'default'),
        ],
        {'default': {'text': "Take this. You'll need it more than I will.", 'choice': [d5, d6, d7]}},
        requires='wickerman')

d8 = z.item("Great-Wicker Ash Mantle", 'cloak', 30, 'ward', "Grey with ash from the great burning that never was. The Rowan wove a rowan-berry border into it.")
d9 = z.item("Hand of the Voice Signet", 'ring', 30, 'mind', "Sciathan's ring: a blue flame on silver. The Rowan cracked the flame.")
d10 = z.item("Captive's Rope Belt", 'belt', 30, 'finesse', "The rope that bound the Ardee farmers, cut and plaited by the farmers themselves.")
d11 = z.item("Druidess's Rowan Torc", 'neck', 30, 'faith', "Eabha's own torc of rowan and bronze. She says she has another. She doesn't.")
z.quest('cn_great_burning', 'The Great Burning', 30, 'cn_eabha',
        "Tonight. The great wicker stands south of the river, past the fields, and they've filled it with farmers from Ardee and Basar. When it burns, the gate at Druim Ligen opens.\n\nThe Fianna can't spare a man from the gate tonight. It's us. Bring every friend you have and [stop the burning].",
        'stop the burning',
        "The Azure Order's great burning is tonight: a vast wicker man full of Ardee and Basar's farmers, to open the demon gate.",
        [
            reach(Z, [790, 335], "Go to the great wicker south of the river, about 470 m south-west of Druim Ligen", "A wicker man taller than any tree, packed with people. Idolaters chant in rings round it, torches high. Someone inside is screaming your name - the miller's girl, from the list.", r=30),
            defend(Z, [784, 325], "Cut the captives loose from the great wicker and keep them alive", "The last captive tumbles out of the wicker and runs. The torches go down onto the empty wicker - and out of the smoke steps a tall man in a burning mask.",
                   'freed farmer', 60167226, 26, "You hack at the wicker. Idolaters come at you from every ring.",
                   [(60158182, 'azure idolater', [27, 28]), (60164910, 'phantom wickerman', [28, 29])], 'Keep the freed farmers alive', model=M,
                   duration=120, every=25, count=3,
                   then_boss={'tpl': 60167712, 'name': 'Sciathan, Hand of the Voice', 'lv': 32, 'hp': 2.4,
                              'announce': "'You took the hands. Then you will be the wood.' Sciathan, Hand of the Voice of the Azure, raises his torch.",
                              'objective': 'Defeat Sciathan'},
                   thanks="Home! We're going home!"),
            search(Z, [784, 325], "Search the ashes of the great wicker (click the glinting spot)", "a scorched letter-case", CRATE,
                   "A letter in blue ink, sealed with a black fool's-cap: 'To the Voice, from the Amadan Dubh. My court's madness is yours, as agreed. Feed my gate and I will open it for you, and Connacht will burn blue.'",
                   give="the Amadan Dubh's letter"),
            end_talk('cn_eabha', "Bring the scorched letter to Druidess Eabha in Ardee", "The Amadan Dubh. The fool-king of the north-east woods.\n\nSo that's the bargain: the fool lends the Order his madness - the Touched, the revels, the jester's tricks - and the Order's fires feed the gate he means to open. The Voice himself fled into the Wicker Fields. When the Rowan are strong enough, we'll go and get him.", 'default'),
        ],
        {'default': wake({'text': "Take these. You saved forty people tonight. The Rowan won't forget it.", 'items': [d8], 'choice': [d9, d10, d11]}, 'connacht_wickermen')},
        requires='cn_names_for_the_fire', group=True)

# ======================================================================== The Fool's Court (28 to 38) - Rowan
e1 = z.item("Laughing Cap Charm", 'gem', 29, 'charm', "A farmhand's cap with a blue bead sewn in the band. It giggles when you're not looking.")
e2 = z.item("Sleepwalker's Bracer", 'bracer', 29, 'finesse', "The Touched move like dancers. Something of that stays in the leather.")
z.quest('cn_the_touched', 'The Touched', 29, 'cn_muadhan',
        "My boy gets up in the night and walks north-east, laughing. Most nights he's back at dawn, scratched and smiling. Some of the other lads don't come back at all.\n\nSeer Gormlaith says the ones who don't are the Touched - the Amadan's folk. Will you [follow the laughter] into the Fool's Court and see what it is that touches them? It's just up there, in the spiral trees.",
        'follow the laughter',
        "Farmer Muadhan's boy sleepwalks into the Fool's Court, laughing. Some who go become the Amadan's Touched.",
        [
            reach(Z, [1400, 470], "Go to the edge of the Fool's Court, in the spiral trees about 80 m north of Farmer Muadhan", "The trees here grow in spirals. Somewhere ahead, pipes and laughter. The laughter doesn't stop for breath.", r=30),
            hunt([1450, 420], "Kill 5 amadan touched at the Fool's Court", 'amadan touched', 5,
                 text="One of the Touched falls and laughs as he goes. In his hand: a farmhand's cap, a blue bead sewn into the band."),
            search(Z, [1455, 415], "Search where the Touched danced, in the middle of the court (click the glinting spot)", "a farmhand's cap", CRATE,
                   "A Basar cap with a blue-glass bead sewn in. The Azure Order's bead, in the fool-king's court. Somebody's sewing them into caps for the sleepwalkers.",
                   give="a farmhand's cap with a blue bead"),
            end_talk('cn_muadhan', "Bring the farmhand's cap to Farmer Muadhan, about 140 m north-east of Basar", "A bead in the band. My own boy's cap - I sewed that band.\n\nSo that's how they find them: the bead calls, the sleeper walks. I'm burning every cap on this farm. Tell Seer Gormlaith in Basar - she'll know what it means.", 'default'),
        ],
        {'default': {'text': "Take this. Wear it backwards, and the court won't call you.", 'choice': [e1, e2]}})

e3 = z.item("Famine's Gnawed Torc", 'neck', 32, 'might', "Famine chewed on it for a century. It tastes of nothing now.")
e4 = z.item("Alp-Skin Belt", 'belt', 32, 'ward', "The alp luachra eat from inside. Their skins keep things out. Funny, that.")
e5 = z.item("Feast-Table Ring", 'ring', 32, 'charm', "A napkin ring from the Fool's Court, carved with laughing mouths.")
z.quest('cn_famines_feast', "Famine's Feast", 32, 'cn_gormlaith',
        "The Touched who never come home aren't kept for dancing. They're kept for the feast - Famine's feast. Famine is the fool-king's steward; he eats, and his guests starve, and the alp luachra sit inside them and eat too.\n\nThere are Basar folk at that table. Will you [end the feast]?",
        'end the feast',
        "Famine, the Amadan's steward, keeps a feast where the Touched starve. There are Basar folk at the table.",
        [
            hunt([1420, 300], "Kill 4 alp luachra round the revel, about 400 m north of Basar", 'alp luachra', 4),
            hunt([1482, 483], "Defeat Famine, at the Fool's Court about 280 m north-east of Basar", 'Famine', 1,
                 text="Famine falls across his own table. The guests blink, and look at their empty plates, and begin - very slowly - to cry."),
            end_talk('cn_gormlaith', "Return to Seer Gormlaith in Basar", "Seven of ours came home. Seven. Thin as rakes and laughing at nothing, but home.\n\nThe Amadan Dubh will know. A grey pookha came to my door last night and asked for you by name. Pookhas don't come to doors. Be careful.", 'default'),
        ],
        {'default': {'text': "Take this. And eat something.", 'choice': [e3, e4, e5]}},
        requires='cn_the_touched')

e6 = z.item("Dorbal's Horn Charm", 'gem', 35, 'might', "Dorbal's horn - what the pookha didn't take.")
e7 = z.item("Pookha-Hair Bracer", 'bracer', 35, 'finesse', "Grey hair, plaited. The pookha gave it, so it's probably cursed. Probably only a little.")
e8 = z.item("Broken-Bargain Ring", 'ring', 35, 'faith', "A pookha's promise, broken. It's iron now. Pookhas hate iron.")
z.quest('cn_pookha_bargain', "A Pookha's Bargain", 35, 'cn_gormlaith',
        "The grey pookha says he serves no court and wants to see the fool-king fall. He'll show you the way into the Amadan Dubh's hall - for a price.\n\nPookhas lie. Pookhas also keep bargains, to the letter. Will you [hear the pookha]? He waits on the east edge of the court.",
        'hear the pookha',
        "A grey pookha offers the way to the Amadan Dubh's hall - for a price.",
        [
            L('pookha', talk('cn_pookha', "Talk to the Grey Pookha, east of the Fool's Court (about 270 m east of Basar)", "You came. Good. The fool-king's hall moves - you'll never find it on your own.\n\nMy price: the horn of Dorbal, the fool-king's huntsman. He took something of mine, long ago. Bring me his [horn], and I'll take you to the hall.", kw='horn')),
            hunt([1487, 185], "Defeat Dorbal, about 330 m east of Druim Ligen, for his horn", 'Dorbal', 1, give="Dorbal's horn"),
            L('bargain', choice('cn_pookha', "Bring the horn to the Grey Pookha, east of the Fool's Court",
                   "Dorbal's horn. Oh, lovely. Give it here.\n\nWith it I can call the hunt - and I'll call it on the fool-king, as promised. Or you could keep it, and I'll still show you the hall, because I want him gone. But then I'll owe you, and you'll owe me, and pookhas collect. Do you [keep the bargain], or [break the bargain]?",
                   [('keep the bargain', "A deal's a deal. Follow the hoofprints north. The hall is where they stop.", 'ending:kept'),
                    ('break the bargain', "...Broken. Well. I'll show you anyway. And one day I'll come for what you owe.", 'ending:broken')])),
        ],
        {'kept': {'text': "And a gift, for an honest dealer.", 'choice': [e7, e8]},
         'broken': {'text': "Keep the horn, then.", 'items': [e6], 'choice': [e7, e8]}},
        requires='cn_famines_feast')

e9 = z.item("Fool-King's Bargain-Knot", 'neck', 38, 'mind', "Blue cord and black, knotted together. The bargain, undone. It hums when you're lied to.")
e10 = z.item("Black Jester's Motley Cloak", 'cloak', 38, 'ward', "Black and blue diamonds, the colours of the bargain. The bells have been taken off.")
e11 = z.item("Court-Breaker's Bracer", 'bracer', 38, 'might', "Iron, plain and heavy. Nothing in the Fool's Court can bear to touch it.")
e12 = z.item("Rowan-Crowned Torc", 'neck', 38, 'faith', "A torc woven with fresh rowan, never wilting. The Order's highest thanks.")
z.quest('cn_fool_kings_bargain', "The Fool-King's Bargain", 38, 'cn_gormlaith',
        "The Amadan Dubh holds the other end of the Voice's bargain. While he lives, the bargain holds, and the gate will open.\n\nThe pookha's shown you the way. Take every friend you have, go into the fool-king's hall, and [break the bargain]. The Amadan Dubh dies, or he laughs at all of us forever.",
        'break the bargain',
        "The Amadan Dubh, the fool-king of the north-east woods, holds the other end of the Azure Order's bargain.",
        [
            reach(Z, [1480, 330], "Go to the fool-king's hall, about 400 m south-east of Druim Ligen", "Trees bent into a hall, a floor of moss, a throne of antlers. Laughter from every side, and none of it is funny.", r=30),
            hunt([1463, 157], "Defeat the Touched, the fool-king's champion, about 300 m east of Druim Ligen", 'Touched', 1),
            hunt([1492, 312], "Defeat the Amadan Dubh in his hall", 'Amadan Dubh', 1,
                 text="The Amadan Dubh stops laughing. He falls without a sound, and the whole court goes quiet - quiet enough to hear a knot of blue and black cord slip from his fingers."),
            search(Z, [1498, 318], "Take up the bargain-knot where the Amadan Dubh fell (click the glinting spot)", "a knot of blue and black cord", CRATE,
                   "The bargain itself, knotted in cord: blue for the Voice, black for the fool-king. With one hand gone, it's already coming loose.",
                   give='the bargain-knot'),
            choice('cn_gormlaith', "Bring the bargain-knot to Seer Gormlaith in Basar",
                   "The bargain-knot. With the fool-king dead, half of it is just string.\n\nThe other half still binds the Voice to the gate. If I [burn the knot], the Voice loses the gate for good. If I [keep the knot], I can follow the thread to wherever the Voice hides, and the Rowan will know where to strike. Burn it, or keep it?",
                   [('burn the knot', "Burn it. Let the Voice feel his gate go cold.", 'ending:burned'),
                    ('keep the knot', "Keep it. The thread runs west, to the Wicker Fields. I'll tell Eabha.", 'ending:kept')]),
        ],
        {'burned': wake({'text': "Take these, with the Rowan's thanks. Basar sleeps tonight.", 'items': [e12], 'choice': [e9, e10, e11]}, 'connacht_fools_revel'),
         'kept': wake({'text': "Take these, with the Rowan's thanks. Basar sleeps tonight.", 'items': [e12], 'choice': [e9, e10, e11]}, 'connacht_fools_revel')},
        requires='cn_pookha_bargain', group=True)

# ======================================================================== The Demon Gate (25 to 40) - Fianna
f1 = z.item("Raid-Ledger Satchel Belt", 'belt', 25, 'finesse', "The siabra captain kept her accounts in this. The Fianna keep it now, empty, as a reminder.")
f2 = z.item("Siabra Tent-Peg Bracer", 'bracer', 25, 'might', "Bone pegs, lashed together. The raiders' tents won't stand again.")
z.quest('cn_raider_tents', "Raiders' Tents", 25, 'cn_ultan',
        "Siabra raiders, in those tents just west of here. They raid Basar's river, they raid the north road, and they never seem short of coin. Champion Fiachra posted me here to watch them.\n\nHe wants to know who pays them. Will you [raid the raiders]? Their captain's tent has a ledger, if you can get to it.",
        'raid the raiders',
        "Siabra raiders camp near the demon gate and never seem short of coin. The Fianna want to know who pays them.",
        [
            hunt([810, 570], "Kill 5 siabra raiders at their tents, about 100 m west of Fennid Ultan", 'siabra raider', 5),
            search(Z, [815, 575], "Search the raid-captain's tent (click the glinting spot)", "a siabra raid-ledger", CRATE,
                   "A ledger in the siabra hand: raids on Basar, raids on the north road, and every one paid for in blue-glass beads. 'Keep the Fianna on the river, away from the gate.'",
                   give='the raid-ledger'),
            end_talk('cn_ultan', "Bring the raid-ledger to Fennid Ultan, on the rise east of the tents", "Beads again. The Azure Order pays the gang in Ardee, the fire-carrier on the Moors, now the siabra.\n\nAnd every one of them is told the same thing: keep the Fianna busy. Away from the gate. This goes to Fiachra at Druim Ligen tonight.", 'default'),
        ],
        {'default': {'text': "Take this. Good work.", 'choice': [f1, f2]}})

f3 = z.item("Gate-Glass Pendant", 'neck', 30, 'mind', "Fused blue glass from the gate's stones. It's cold. Fire-glass shouldn't be cold.")
f4 = z.item("Watch-Post Cloak", 'cloak', 30, 'ward', "The Fianna's gate-watch cloak, grey and heavy. It's seen a lot of bad nights.")
f5 = z.item("Manes-Fang Ring", 'ring', 30, 'finesse', "A manes demon's tooth, in an iron band. It still tries to bite.")
z.quest('cn_watch_on_the_gate', 'The Watch on the Gate', 30, 'fiachra',
        "The demon gate south-west of the keep has smouldered for a hundred years. The Fianna watch it. That's what we're for.\n\nLately it doesn't smoulder. It burns - and it burns blue. Will you [go to the gate] and tell me why?",
        'go to the gate',
        "The demon gate by Druim Ligen has begun to burn blue.",
        [
            reach(Z, [990, 400], "Go to the demon gate, about 380 m south-west of Druim Ligen", "A ring of scorched stone, the air above it shaking. The fire inside is blue now, not red, and things move in it.", r=30),
            hunt([990, 400], "Kill 6 manes demons at the gate", 'manes demon', 6),
            search(Z, [985, 392], "Search the gate's stones (click the glinting spot)", "the gate-stones", CRATE,
                   "Blue glass, fused into the stones in streaks - as if someone had poured burning beads into the gate. Fed it. Not once: dozens of times.",
                   give='a lump of fused gate-glass'),
            end_talk('fiachra', "Bring the gate-glass to Champion Fiachra at Druim Ligen", "Somebody's feeding the gate. With the same blue glass they pay their rabble in.\n\nAnd somebody tells them when my watch changes - every raid comes the moment my sentinels swap. There's a mouth in this keep. Find it.", 'default'),
        ],
        {'default': {'text': "Take this. And watch your back in the keep.", 'choice': [f3, f4, f5]}},
        requires='cn_raider_tents')

f6 = z.item("Jester's Bell Charm", 'gem', 34, 'charm', "One bell from Lorcan's cap. It doesn't ring any more. You made sure.")
f7 = z.item("Turncoat's Belt", 'belt', 34, 'finesse', "Reversible: Fianna green on one side, fool's motley on the other.")
f8 = z.item("Keep-Watch Bracer", 'bracer', 34, 'might', "Druim Ligen's gate-watch bracer. Fiachra's sentinels saluted when you put it on.")
z.quest('cn_jester', 'The Jester at the Keep', 34, 'fiachra',
        "A mouth in my keep. Somebody who knows when the watch changes and laughs about it.\n\nWe've a jester, Lorcan, who came last winter and makes the lads laugh. Too much. A jester sees everything and nobody sees him. Will you [watch the jester]? Talk to him. Search his things. Follow him if he goes out.",
        'watch the jester',
        "Somebody in Druim Ligen tells the demons when the watch changes. Fiachra suspects the keep's new jester.",
        [
            L('lorcan', talk('cn_lorcan', "Talk to Lorcan the Jester at Druim Ligen", "A hero! At my feet! Why did the hero cross the keep? To get to the jester! Ha!\n\nAsk me anything. I know a thousand jokes and one [secret]. The secret's the funniest.", kw='secret')),
            search(Z, [1182, 90], "Search the jester's corner, just south of Champion Fiachra (click the glinting spot)", "the jester's motley bag", CRATE,
                   "Under the bells and the juggling balls: a letter in a fool's scrawl. 'Watch changes at the third bell. Tell Juliy, Juliy tells the gate. The Amadan sends his love.'",
                   give="the jester's letter"),
            hunt([1216, 449], "Defeat Juliy the Jester, on the hill about 260 m north of Basar", 'Juliy the Jester', 1,
                 text="Juliy falls with a jingle of bells. In his pouch: the watch-roster for the whole month, in Lorcan's hand."),
            choice('fiachra', "Report to Champion Fiachra at Druim Ligen",
                   "Lorcan. The fool-king's man, in my own hall, eating my bread.\n\nI could [hang him] from the gate-tower, and every fool in the north will know what Druim Ligen does to spies. Or I could [turn him]: keep him, feed the court false watch-times, and spring a trap at the gate. What do you say?",
                   [('hang him', "Hang him. And ring the third bell while he goes.", 'ending:hanged'),
                    ('turn him', "Turn him. He'll laugh for us now, or not at all.", 'ending:turned')]),
        ],
        {'hanged': {'text': "Take this. A hard thing done right.", 'items': [f6], 'choice': [f7, f8]},
         'turned': {'text': "Take this. A clever thing done right.", 'items': [f7], 'choice': [f6, f8]}},
        requires='cn_watch_on_the_gate')

f9 = z.item("Gate-Lord's Iron Torc", 'neck', 40, 'might', "Wrought from the gate-lord's chain. It's cold and heavy and it doesn't care.")
f10 = z.item("Druim Ligen Champion's Mantle", 'cloak', 40, 'ward', "Green, with a silver fian-ring. Fiachra said you'd earned the green. Then he said it again, louder.")
f11 = z.item("Ember-Quench Ring", 'ring', 40, 'mind', "Blue fire, sealed in iron and drowned. Druidess Eabha sent it from Ardee.")
f12 = z.item("Fian-Oath Bracer", 'bracer', 40, 'finesse', "Bound with the old fian oath: never refuse a fight, never refuse a guest. One of those is easier.")
z.quest('cn_close_the_gate', 'Close the Gate', 40, 'fiachra',
        "The bargain's broken, the jester's dealt with, and the fires are going out. But the gate's been fed so long that what's behind it is awake.\n\nThe Gate-Keeper - the thing that holds the gate from the other side - is coming through. If it comes through, it stays. Bring the best you have and [close the gate].",
        'close the gate',
        "The demon gate has been fed so long that its Gate-Keeper is coming through.",
        [
            reach(Z, [990, 400], "Go to the demon gate, about 380 m south-west of Druim Ligen", "The gate is wide open, a wound of blue fire. Something enormous is pulling itself through it, a claw at a time.", r=30),
            gives(boss(Z, [995, 395], "Defeat the Gate-Keeper when it comes through the gate", "The Gate-Keeper falls back through its own door, and the fire goes from blue to red to grey. The gate is just stones again. For now.",
                       'Ghastrach the Gate-Keeper', 12359, 40, "'The fool promised. The fires promised. You are not what was promised.' Ghastrach the Gate-Keeper steps into Connacht.",
                       objective='Defeat Ghastrach the Gate-Keeper', hp=2.6, adds=[(10107, 'manes demon', [36, 38]), (12359, 'grumoz demon', [37, 39])], every=25, count=2), "the gate-keeper's chain"),
            end_talk('fiachra', "Bring the gate-chain to Champion Fiachra at Druim Ligen", "Grey stones. I've not seen that gate grey in my whole life.\n\nThe Fianna will watch it - we always will. But tonight we watch a gate, not a door. Take this. And come and drink with us; the third bell's for you.", 'default'),
        ],
        {'default': wake({'text': "From the Fianna of Druim Ligen.", 'items': [f10], 'choice': [f9, f11, f12]}, 'connacht_gate_stirs')},
        requires='cn_jester', group=True)

# ======================================================================== an easter egg: the Salmon of Knowledge
# (owner 2026-11-22: "easter eggs in each zone, big or small unique things") - an old poet fishing a quiet bend of the river
# below Basar, as Finnegas fished the Boyne for seven years before young Fionn burned his thumb on the salmon.
z.npc('cn_finnegas', 'Finnegas the Poet', [1415, 1028], 'm', 40, model=OLD, guild='a poet, fishing',
      idle="Seven years I've sat by this water. Seven. Don't tell anyone; they'll want to sit here too.")
x1 = z.item("Thumb of Knowledge", 'ring', 10, 'mind', "Burned, a little, on one side. Put your thumb to it when you don't know what to do. It doesn't always help.")
x2 = z.item("Poet's Hazel Charm", 'gem', 10, 'faith', "Nine hazelnuts of wisdom fell into the well where the salmon was born. This is one of the shells.")
z.quest('cn_salmon_of_knowledge', 'The Salmon of Knowledge', 10, 'cn_finnegas',
        "Hush. Hush! There - did you see it? Silver, with spots like a scatter of stars. The Salmon of Knowledge. Who eats it knows everything there is to know.\n\nMy knees aren't what they were. Will you [catch it for me]? Don't eat it. Whatever you do, don't you eat it.",
        'catch it for me',
        "An old poet by the river below Basar has spent seven years fishing for the Salmon of Knowledge.",
        [
            search(Z, [1424, 1030], "Catch the salmon in the river bend a few steps east of Finnegas (click the glinting spot by the water)", "a silver salmon in the shallows", CRATE,
                   "Your hands close on something cold and silver and furious. It looks at you. You'd swear it looks at you.",
                   give='the Salmon of Knowledge'),
            talk('cn_finnegas', "Bring the salmon to Finnegas the Poet, by the river south of Basar", "Oh. Oh, look at it. Seven years.\n\nI'll cook it now. You watch the fire for me while I find the salt - and mind, if a blister rises on the skin, press it down. Don't [taste] it.", kw='taste'),
            choice('cn_finnegas', "Mind the fire for Finnegas, then tell him what you know",
                   "...You burned your thumb on it, didn't you. And you put your thumb in your mouth. Of course you did. They all do. Fionn did.\n\nWell. It's yours now, all of it - the knowing. Or some of it. Tell me true: do you [know everything] now, or do you [know nothing at all]?",
                   [('know everything', "Then you know I'll be fishing another seven years. Go on. Take these, and stop looking at me like that.", 'ending:wise'),
                    ('know nothing at all', "Ha! The first honest answer anyone's given by this river. That's the start of wisdom. Take these.", 'ending:honest')]),
        ],
        {'wise': {'text': "Take these.", 'choice': [x1, x2]}, 'honest': {'text': "Take these.", 'items': [x2], 'choice': [x1]}})
