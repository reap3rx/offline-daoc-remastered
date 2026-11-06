"""Albion's story quests beyond Camelot Hills (claude 2026-11-05) - see story_gen.py. Places: zone metres [x, y]."""
from story_gen import Zone, talk, reach, search, kill, boss, defend, choice, end_talk, L

BEDROLL, LANTERN, CRATE = 1882, 1876, 1347
ZONES = []

# ====================================================================================================== Salisbury Plains
z = Zone(1, 'Salisbury Plains', 1, 'alb_salisbury_plains')
ZONES.append(z)
z.npc('wenna_ashby', 'Wenna Ashby', [724, 213], 'f', 10, idle="If you're going south, mind the barrows. Nothing good's come out of them yet.")
z.npc('dunstan_carter', 'Dunstan the Carter', [745, 213], 'm', 14, idle="Wheels, axles, horses. Ask me about any of 'em. Don't ask me about the road south.")
z.npc('aled_ashby', 'Aled Ashby', [912, 900], 'm', 12, during=['under_stones/torc'])
z.npc('ysolde_huntington', 'Ysolde Huntington', [238, 1316], 'f', 16, idle="Rhodri says the old stories are for children. Rhodri says a lot of things.")
z.npc('coel_huntsman', 'Coel the Huntsman', [229, 1302], 'm', 18, idle="Good hunting on the plain this year. Too good. Makes a man careless.")
z.npc('rhodri_huntington', 'Rhodri Huntington', [1462, 1226], 'm', 17, during=['white_horse/bridge', 'white_horse/gaze', 'white_horse/rhodri'])

it_tally = z.item("Aled's Tally-Stick Charm", 'gem', 13, 'charm', "A drover's notched tally, every notch a debt paid. Someone has carved one more.")
it_torc = z.item('Torc of the Barrow-King', 'neck', 13, 'might', "Old gold that was never meant to see the sun. It sits warm against the throat.")
it_henge = z.item('Henge-Stone Bracer', 'bracer', 13, 'mind', "A band of blue stone cut from a fallen lintel. It hums faintly at dusk.")
it_drover = z.item("Drover's Oilskin", 'cloak', 13, 'ward', "Waxed against the plain's rain, patched at every seam by someone who cared.")

z.quest('under_stones', 'Under the Stones', 13, 'wenna_ashby',
        "My husband Aled took work guarding a wagon for some 'surveyors' bound south. Good coin, he said - too good, I said. That was nine days ago.\n\nDunstan the [carter] saw them go. I'm not asking you to fight anyone. Just - will you [find Aled]? Find him and tell me what kind of fool I married.",
        'find Aled',
        "Wenna Ashby's husband hired on to guard a wagon of 'surveyors' bound south, and hasn't come home.",
        [
            talk('dunstan_carter', 'Ask Dunstan the carter where the wagon went',
                 "Surveyors my eye. Shovels, rope, picks and a strongbox with nothing in it - you don't carry an empty strongbox to fill with *surveys*. They went south past the [barrows], where the tomb raiders dig. Aled knew. He's not a stupid man; he's a poor one.",
                 kw='barrows'),
            search(1, [376, 1086], "Find the wagon near the tomb raiders' diggings", "an overturned wagon", CRATE,
                   "The wagon's on its side, the horses gone. Aled's tally-stick is jammed in the wheel-spokes, as if he wanted it found - and every barrow round about has been opened.",
                   give="Aled's tally-stick"),
            kill(1, [363, 1103], 'Make the diggers talk', 'tomb raider digger', 12737, [10, 11], 6,
                 text="The last digger talks fast. 'The drover? He wouldn't open the king's barrow. Said it was a grave and that was that. Foreman Brannoc had him trussed and dragged off to the old stones - for the ritual, he said. Laughed when he said it.'"),
            reach(1, [905, 900], 'Go to the great stones', "The ring of stones looms over the plain. Torches - and Aled, bound to a fallen lintel, very much alive and very much shouting.", r=20),
            defend(1, [915, 905], 'Free Aled Ashby', "Aled's ropes are cut. He picks up a digger's shovel and looks almost cheerful about it.",
                   'Aled Ashby', 12738, 12, "Brannoc's crew come running from the barrows. 'The drover's loose! Get him!'",
                   [(12738, 'tomb raider scout', [12, 13])], 'Keep Aled alive while he gets free', model=9, duration=80,
                   then_boss={'tpl': 12734, 'name': 'Foreman Brannoc', 'lv': 15, 'announce': "A big man with a pick shoulders through the stones. 'That's my barrow-king's gold, drover. Mine.'", 'objective': 'Defeat Foreman Brannoc'},
                   thanks="Well. That could have gone worse. Mostly for me."),
            L('torc', choice('aled_ashby', "Speak with Aled at the stones",
                   "Wenna sent you? Of course she did. Listen - before we go. I took this off Brannoc. It's from the king's barrow. Old gold. It would feed us for two winters, and I'd never need to take work from men like him again.\n\nI know what it is. I know where it came from. Tell me straight: do I [put it back], or do we [keep it]?",
                   [('put it back', "...Yes. Yes, that's the answer I was waiting for someone to give me. Take it back to the barrow for me? I can't go near the place again. I'll go home to Wenna.", 'next:return'),
                    ('keep it', "Then it's ours, and the dead can complain to me personally. Go on - tell Wenna I'm coming. I'll be the one walking funny under all this gold.", 'next:kept')])),
            L('return', search(1, [1272, 790], "Return the torc to the barrow-king's grave in the eastern barrows", "the opened barrow", CRATE,
                   "You lay the torc back on the bones of a king nobody remembers. The barrow sighs - you'd swear it - and settles.",
                   take='Torc of the barrow-king')),
            end_talk('wenna_ashby', 'Tell Wenna Ashby', "He's home. Covered in mud, smelling of a wet dog, and home. He told me about the gold - and that you made him put it back.\n\nGood. I'd rather be poor with him than rich with a curse in the house.", 'honest'),
            L('kept', end_talk('wenna_ashby', 'Tell Wenna Ashby', "He's home, and he brought a king's torc into my kitchen. I've hidden it in the flour.\n\nTwo winters, he says. We'll see what the barrows say about it. Thank you - whatever comes of it, you brought him back.", 'gold')),
        ],
        {'honest': {'text': "Aled carved you this - he says every debt deserves its notch.", 'items': [it_tally], 'choice': [it_henge, it_drover]},
         'gold': {'text': "Take something from the barrow too. Aled says if there's a curse, it may as well be spread thin.", 'items': [it_tally], 'choice': [it_torc, it_henge]}},
        topics={'carter': "Dunstan. By the stables. He sees everything that leaves Ludlow, and has an opinion on all of it."},
        )
for st in z.quests[-1]['steps']:                      # the torc is Aled's to give
    if st.get('npc') == 'aled_ashby':
        st['give'] = {'name': 'Torc of the barrow-king'}

it_horn = z.item("Huntington's Horn", 'gem', 18, 'finesse', "A plains hunter's horn. Blow it, and every Huntington within a mile comes running - or used to.")
it_chalk = z.item('Chalk-White Mantle', 'cloak', 18, 'faith', "Pale as the hill figure. It never seems to stain.")
it_gaze = z.item("Basilisk-Eye Ring", 'ring', 18, 'mind', "A grey eye set in silver. Don't stare at it too long.")
it_hide = z.item('Hide of the White Horse', 'belt', 18, 'might', "Soft, white, and strangely cold. The plain has felt emptier since.")
z.quest('white_horse', 'The White Horse', 18, 'ysolde_huntington',
        "My brother Rhodri's gone after the White Horse. The real one - the one the hill-figure was cut for, before Camelot had a name. A lord in Ludlow will pay its weight in silver for the hide.\n\nCoel says the plain's full of giants this year and Rhodri went alone. I don't care about the silver. Will you [bring him back]? Coel can show you his [tracks].",
        'bring him back',
        "Rhodri Huntington went alone onto the giants' plain to hunt the White Horse of Salisbury.",
        [
            talk('coel_huntsman', 'Ask Coel about Rhodri\'s tracks',
                 "He set a snare line east of the old drovers' road, where the horse comes to drink. Ran it right through the giants' grazing. Said giants were slow. Giants are slow - right up until they [aren't].",
                 kw="aren't"),
            search(1, [822, 1196], "Find Rhodri's snare line on the giants' plain", "a snapped snare and a broken spear", CRATE,
                   "The snare's snapped and the spear's in three pieces. Huge prints all round - and a smear of blood leading east."),
            kill(1, [899, 1226], 'Drive off the giants who took him', 'salisbury giant', 12719, [18, 19], 5,
                 text="In the last giant's sack: Rhodri's quiver, empty. Whatever happened to him, he got away. The trail runs east to the old Roman bridge."),
            L('bridge', reach(1, [1458, 1232], 'Follow the trail to the old Roman bridge', "Rhodri's under the bridge arch, white to the knees - grey, rather. A basilisk's glance, half-caught. He's alive, and very cross about it.", r=18)),
            L('gaze', boss(1, [1440, 1240], 'Kill the basilisk that hunts him', "The old basilisk sags and its eyes cloud over. The grey creeping up Rhodri's legs stops, and slowly starts to fade.",
                 'the Old Gazer', 12659, 21, "Something heavy drags itself out of the reeds, and Rhodri swears. 'It followed me. Don't look at its eyes. Don't LOOK at its EYES.'",
                 objective='Kill the Old Gazer', hp=2.4, adds=[(12662, 'basilisk', [15, 16])], every=30, count=1)),
            L('rhodri', choice('rhodri_huntington', 'Talk to Rhodri',
                   "Ysolde sent you, didn't she. Of course.\n\nI saw it, you know. The White Horse. Just before the giants came. It stood there looking at me like it knew my name. I could still have it - it drinks at the giants' pools at dusk. Help me, and the silver's half yours.\n\nOr tell me to [let it be], and I'll limp home and listen to my sister laugh. Or we [hunt it] - now.",
                   [('let it be', "...Yes. All right. I couldn't have loosed anyway, I think. Not with it looking at me. Let's go home.", 'next:spared'),
                    ('hunt it', "Ha! Knew you had the stomach for it. Dusk, by the pools. Don't miss.", 'next:hunt')])),
            L('hunt', kill(1, [798, 1165], 'Hunt the White Horse at dusk', 'the White Horse', 60167890, 19, 1,
                 text="It doesn't run. It only looks at you, and then it's down, and the light on the plain goes strange and flat. Far off on the hill, a crack runs through the chalk.", next='hunted')),
            L('spared', end_talk('ysolde_huntington', 'Return to Ysolde', "He limped in with grey feet and a face like a wet week, and he said he saw it. The White Horse. And let it go.\n\nYou've no idea what that means to this family. Our grandmother used to say we keep the plain, not the other way round.", 'spared')),
            L('hunted', end_talk('ysolde_huntington', 'Return to Ysolde', "The hill-figure cracked last night. Everyone in the camp heard it.\n\nRhodri's got his silver. He sits by the fire with it and doesn't say much. Take your share. I don't want it in my tent.", 'hunted')),
        ],
        {'spared': {'text': "Grandmother's horn. She'd want it to go to someone who listened.", 'items': [it_horn], 'choice': [it_chalk, it_gaze]},
         'hunted': {'text': "Take it and go.", 'tragic': True, 'items': [it_horn], 'choice': [it_hide, it_gaze]}},
        topics={'tracks': "Coel's by the fire. He taught Rhodri to track. He's not happy about how that turned out."})

# ===================================================================================================== Black Mtns. South
z = Zone(2, 'Black Mountains South', 1, 'alb_black_mtns_south')
ZONES.append(z)
z.npc('wren_piper', 'Wren Piper', [1199, 1103], 'f', 4, model=38, size=40, idle="Pip's always off somewhere. Usually he comes back.")
z.npc('corwen_fisher', 'Old Corwen', [1172, 1088], 'm', 10, idle="The river gives, the river takes. Mostly it takes, this year.")
z.npc('pip_piper', 'Pip Piper', [579, 566], 'm', 2, size=38, during=['singing_bridge/pip'])
z.npc('sister_aldith', 'Sister Aldith', [610, 1082], 'f', 14, idle="Pray for the filidh, if you pray. Somebody must.")
z.npc('hedda_woodcutter', 'Hedda the Woodcutter', [985, 458], 'f', 9, idle="Wood doesn't cut itself. More's the pity.")
z.npc('brother_osric', 'Brother Osric', [1062, 46], 'm', 7, during=['willing_heart/osric'])

it_bell = z.item("Pip's Bell-Charm", 'gem', 5, 'charm', "A little brass bell on a string. It rings on its own when water is near.")
it_river = z.item('River-Stone Ring', 'ring', 5, 'might', "A smooth black pebble, drilled through and set in copper.")
it_reed = z.item('Reed-Woven Sash', 'belt', 5, 'mind', "Goblin work, oddly fine. It smells of the river.")
it_fish = z.item("Fisherman's Mantle", 'cloak', 5, 'ward', "A heavy, patched cloak that once belonged to a man who drowned. Someone has mended it since.")
z.quest('singing_bridge', 'The Singing Bridge', 4, 'wren_piper',
        "Have you seen my brother? He's this tall, and loud, and he's called Pip. He went to the [singing bridge] last night and he's not back.\n\nOur Da drowned crossing there in the winter. Pip says he can hear Da singing from the water at night. He's ten. Will you [find Pip]? Old Corwen knows the bridge.",
        'find Pip',
        "Wren Piper's little brother Pip went to the singing bridge where their father drowned.",
        [
            talk('corwen_fisher', 'Ask Old Corwen about the singing bridge',
                 "The magic bridge, up the river? Aye, it sings. Or the goblins do, on the north end, when they're fishing. Singing at night with voices they've no right to. I've heard my own mother calling from that water, and she's thirty years buried. Pip went up to the [north end], I'd guess.",
                 kw='north end'),
            search(2, [934, 452], 'Search the north end of the magic bridge', "a small satchel", CRATE,
                   "Pip's satchel. Inside: a heel of bread, a wooden whistle, and a drawing of goblins, with an arrow pointing west and 'DA?' in big letters."),
            kill(2, [690, 672], "Deal with the goblin fishermen west of the bridge", 'goblin fisherman', 12171, [4, 5], 5,
                 text="One of the goblins drops a reed whistle. When you blow it, it doesn't sound like a whistle. It sounds like a man calling a boy's name. They took Pip to their singer."),
            boss(2, [575, 560], "Find Pip at the goblins' singing-pool", "The singer's whistles scatter. In the reeds, a very muddy boy is hiding.",
                 'Gobble-Eye the Singer', 12171, 7, "A goblin with a necklace of whistles stands up out of the pool and sings - in a drowned man's voice. 'Pip! Come here, Pip!'",
                 objective='Silence Gobble-Eye the Singer', hp=2.0, adds=[(12235, 'undead goblin fisherman', [4, 5])], every=30, count=1),
            L('pip', talk('pip_piper', 'Talk to Pip',
                 "It wasn't Da. Was it. It was him. With the whistles.\n\nI knew, really. I just wanted to hear it again. Don't tell Wren I cried. Let's go [home].", kw='home')),
            choice('wren_piper', 'Bring Pip home to Wren',
                   "PIP! You horrible - come here. Come HERE.\n\n...What was it? What did he hear? You can tell me [the truth]. Or you can say it was [only the river]. I think I know which he needs. I'm not sure which I do.",
                   [('the truth', "A goblin. Using Da's voice. Gods.\n\nI'm glad you said. I'd rather hate a goblin than wonder for the rest of my life. Thank you.", 'ending:truth'),
                    ('only the river', "The river. Yes. The river does that.\n\nPip's asleep already. He said Da sang him a song before the goblins came. I'm going to let him keep it.", 'ending:river')]),
        ],
        {'truth': {'text': "Pip wants you to have this - it was Da's.", 'items': [it_bell], 'choice': [it_river, it_reed]},
         'river': {'text': "Pip wants you to have this - it was Da's.", 'items': [it_bell], 'choice': [it_reed, it_fish]}},
        topics={'singing bridge': "The magic bridge, up the river to the north. People say it sings. Pip says it sings with Da's voice."})

it_menhir = z.item('Menhir-Chip Amulet', 'neck', 9, 'faith', "A flake of the blood-stone, scrubbed clean and blessed three times. It still feels warm.")
it_scrip = z.item("Osric's Scrip", 'belt', 9, 'ward', "A friar's simple belt and pouch, full of salt and seeds.")
it_sickle = z.item("Sacrificer's Sickle-Pin", 'bracer', 9, 'finesse', "A bronze cloak pin shaped like the filidh's sickle. Melted down, it would be worth little. Worn, it is a warning.")
it_mercy = z.item('Band of Mercy', 'ring', 9, 'mind', "A plain silver ring given to novices of the healers' house.")
z.quest('willing_heart', 'One Willing Heart', 9, 'sister_aldith',
        "Brother Osric is young and kind and thinks that's armour. He went north to preach to the filidh at their standing stone - to turn them from blood. His letters came every week.\n\nThey stopped a fortnight ago. Hedda the woodcutter works up that way. Will you [go north] and see what's become of him?",
        'go north',
        "Brother Osric went north to preach to the filidh at their standing stone, and his letters stopped coming.",
        [
            talk('hedda_woodcutter', 'Ask Hedda the woodcutter about the friar',
                 "The young monk? Saw him a week back, walking with the filidh. Not tied - walking, smiling, talking with them like old friends. Gave me a blessing on his way past. Odd thing is, they were all smiling. Up at the [stones].", kw='stones'),
            search(2, [1080, 140], 'Search the path to the northern standing stone', "a dropped satchel and a torn page", BEDROLL,
                   "An unfinished letter, in a careful hand: 'Sister - they are kind to me. They say the stone does not want blood, only one willing heart, once in a generation. I think I understand them now. I think I am glad.'",
                   give="Osric's last letter"),
            kill(2, [1118, 52], 'Fight through the devout filidh at the stone', 'devout filidh', 12675, [8, 9], 6,
                 text="Garlands of white flowers hang on the menhir. Someone has laid out a friar's habit, folded, on the altar-stone."),
            defend(2, [1052, 40], 'Reach Osric before the rite ends', "The rite is broken. The menhir is only a stone again.",
                   'Brother Osric', 12675, 7, "Osric stands by the stone, garlanded, eyes shut. The filidh begin to chant, and the sickles come out.",
                   [(12675, 'devout filidh', [8, 9])], 'Keep Brother Osric alive', model=9, duration=75,
                   then_boss={'tpl': 12161, 'name': 'Archfilidh Corra', 'lv': 11, 'announce': "A tall woman in white steps out from behind the stone. 'He came to us willing. You have no right.'", 'objective': 'Defeat Archfilidh Corra'},
                   thanks="I... I was going to let them. I was GLAD."),
            L('osric', choice('brother_osric', 'Talk to Brother Osric',
                   "I came to save them and they nearly saved me - that's what it felt like. Being wanted that much.\n\nI don't know what I am now. Sister Aldith will want me [home]. But the filidh who are left - they're frightened now, and lost. Someone kind should [stay] with them. Tell me what to do. I can't trust myself to choose.",
                   [('home', "Home. Yes. I'll walk behind you. Tell her... tell her I'm sorry about the letters.", 'next:home'),
                    ('stay', "Then I'll stay. Not as a sacrifice - as a friar. Take her my letter. All of it. She should know what I nearly did.", 'next:stayed')])),
            L('home', end_talk('sister_aldith', 'Return to Sister Aldith', "He came in, and knelt, and wouldn't get up until I made him. He's sleeping now, in his old cell.\n\nI have read his last letter. I will burn it, I think. He doesn't need to remember being glad.", 'home')),
            L('stayed', end_talk('sister_aldith', 'Return to Sister Aldith', "He stayed. With them. After that.\n\nHe was always braver than me, and stupider. I will pray for him every day, and I will write every week, and if one week he doesn't answer, I am going up there myself.", 'stayed')),
        ],
        {'home': {'text': "Take this, for bringing him back to us.", 'items': [it_menhir], 'choice': [it_scrip, it_mercy]},
         'stayed': {'text': "Take this. He'd want you to have something of his.", 'tragic': True, 'items': [it_menhir], 'choice': [it_scrip, it_sickle]}})

# ===================================================================================================== Black Mtns. North
z = Zone(3, 'Black Mountains North', 1, 'alb_black_mtns_north')
ZONES.append(z)
z.npc('tomas_fell', 'Tomas Fell', [692, 343], 'm', 8, idle="I'm an apprentice. Apprentices do as they're told. Mostly.")
z.npc('mabli', 'Mabli Trewin', [664, 603], 'f', 9, during=['last_shift/mabli', 'last_shift/foreman', 'last_shift/egg'])
z.npc('hrodda', 'Hrodda Alreksdottir', [985, 1030], 'f', 14, idle="Your people think mine are animals. Mine think yours are. Both are mostly right, this season.")
z.npc('captain_mardoc', 'Captain Mardoc', [1016, 1011], 'm', 20, idle="Hill raiders, smugglers, and now red robes. This posting gets better every week.")
z.npc('hrodda_camp', 'Hrodda Alreksdottir', [158, 372], 'f', 14, during=['crimson_bargain/alrek'])

it_salt = z.item("Mabli's Salt-Pouch", 'gem', 11, 'charm', "Salt for circles, salt for ghosts, salt for supper. Mabli never goes anywhere without it.")
it_lamp = z.item("Miner's Lamp-Ring", 'ring', 11, 'might', "A ring of blackened iron that a ghost wore for two hundred years. It still smells of lamp-oil.")
it_egg = z.item('Cockatrice-Shell Bracer', 'bracer', 11, 'mind', "Speckled shell, set in bronze. Magus Idris was not pleased to see it in your hands.")
it_shift = z.item("Foreman's Belt", 'belt', 11, 'ward', "Thick leather, and a ring of keys to tunnels long fallen in.")
z.quest('last_shift', 'The Last Shift', 10, 'tomas_fell',
        "My master, Magus Idris, wants a cockatrice egg from the old mine in the hills. I was meant to fetch it. I - didn't. I sat in the tavern instead.\n\nAnd Mabli - she's the miller's girl, she's not afraid of anything - she said she'd go for me so I wouldn't lose my place. That was yesterday morning. Please, will you [go after her]? I'll owe you forever. I already owe her forever.",
        'go after her',
        "Mabli Trewin went to the haunted mine for a cockatrice egg, in place of the apprentice too frightened to go.",
        [
            search(3, [604, 556], 'Search the path to the old mine', "a broken ring of salt", CRATE,
                   "A salt circle, scuffed open. Someone sat in it for a long while. Cockatrice tracks all round, and further up, the sound of picks where nobody has dug for two centuries."),
            kill(3, [622, 585], 'Clear the cockatrices from the mine mouth', 'enraged cockatrice', 12086, [10, 11], 4,
                 text="Past the nests, lamplight flickers in the shaft - pale, cold lamplight."),
            L('mabli', talk('mabli', 'Find Mabli in the mine',
                 "Oh, thank the gods - no, keep your voice down. They're not cruel, the miners. They just don't know they're dead. They gave me a pick and told me to dig, and the foreman won't let anyone leave before the [shift bell].",
                 kw='shift bell')),
            L('foreman', boss(3, [660, 610], 'End the last shift', "The ghost foreman lets go of the bell-rope. It rings once, very far away, and the miners lay down their picks and walk into the rock, one after another, going home.",
                 'Foreman Gethin of the Last Shift', 12095, 13, "A great grey man with a lamp comes out of the dark. 'Back to work. No one leaves before the bell.'",
                 objective='Make Foreman Gethin ring the bell', hp=2.2, adds=[(12095, 'ghost miner', [10, 11])], every=30, count=1)),
            L('egg', choice('mabli', 'Talk to Mabli',
                   "I got the egg, you know. Before the miners. Here.\n\nOnly - one of the miners told me what the magus does with them. Grinds the shells for a powder that turns men to stone. He sells it to the hill raiders and to whoever fights them. Both sides.\n\nTomas would lose his place if we [break it]. I'd still be glad. Or we [take it] to the magus and keep our heads down. You choose. I've been brave enough for one week.",
                   [('break it', "Good. Gods, good. I'll tell Tomas myself. If he's worth anything he'll thank us.", 'next:broken'),
                    ('take it', "All right. It's not ours to change, I suppose. Let's get out of here before the bell rings again.", 'next:given')])),
            L('broken', end_talk('tomas_fell', 'Go back to Tomas Fell', "She broke it. She broke it and then she told me why, and then she hit me, which was fair.\n\nThe magus has thrown me out. I'm going to be a miller's boy. I've never been happier.", 'broken')),
            L('given', end_talk('tomas_fell', 'Go back to Tomas Fell', "You brought it! And Mabli! Both! The magus is pleased - he's even smiling.\n\nMabli isn't. She won't tell me why. Here - he says I'm to pay you, from the egg-money.", 'given')),
        ],
        {'broken': {'text': "Mabli says you're to have this.", 'items': [it_salt], 'choice': [it_lamp, it_shift]},
         'given': {'text': "From the egg-money.", 'items': [it_salt], 'choice': [it_egg, it_lamp]}})

it_hill = z.item("Hill-Chief's Torque", 'neck', 15, 'might', "Twisted bronze, scratched with the marks of every chief before Alrek.")
it_crimson = z.item('Crimson-Thread Cloak', 'cloak', 15, 'mind', "Unpicked from an initiate's robe and woven back the other way. The red has dulled to brown.")
it_peace = z.item("Hrodda's Bone Bracer", 'bracer', 15, 'finesse', "Carved with a hill-tribe pattern that means 'guest'.")
it_bounty = z.item("Bounty-Hunter's Belt", 'belt', 15, 'ward', "Captain Mardoc's own. He said you'd earned it. He didn't look at you when he said it.")
z.quest('crimson_bargain', 'The Crimson Bargain', 15, 'hrodda',
        "You will listen to me, because nobody else here will. I am Hrodda, daughter of Alrek, chief of the hill-people west of here.\n\nMen in red robes came to my father's fire this spring. Since then his eyes are red too, and so are his warriors'. They are going to burn this town. I do not love this town. But I love my father, and he would not have done this. Will you [help me]? Ask your [captain] if you don't believe me.",
        'help me',
        "Hrodda, daughter of the hill-chief Alrek, says red-robed priests have bewitched her father and his warriors.",
        [
            talk('captain_mardoc', 'Ask Captain Mardoc about the hill-folk',
                 "The hill-girl? She came in yesterday and the lads laughed at her. I didn't. My scouts have seen red robes among the huts - Crimson initiates, from the south. Whatever they want with the hill-folk, it isn't [peace].", kw='peace'),
            reach(3, [200, 625], "Go to the hill-folk's lands in the west", "Hill warriors stand at their posts without moving, staring east towards the town. Their eyes glow a dull, steady red.", r=20),
            kill(3, [183, 600], 'Break the spell on the hill warriors', 'hill warrior', 12110, [11, 12], 6,
                 text="As each warrior falls the red goes out of their eyes - and in the last one's belt, a scrap of crimson cloth with a sigil stitched on it."),
            search(3, [150, 390], "Search Chief Alrek's huts in the north-west", "a crimson-sealed letter", CRATE,
                   "In a red hand: 'Burn the town by the new moon and the hills are yours forever. Refuse and we take the girl.' Under it, the hill-chief's mark, pressed in blood."),
            boss(3, [145, 365], "Confront the Crimson initiate at Alrek's fire", "The initiate's robes burn up from the hem like paper. Alrek drops to his knees and covers his face.",
                 'Initiate Vael of the Crimson Hand', 12075, 17, "A thin smiling man in red rises from Alrek's own seat. 'The chief is mine, stranger. So are his people. So, soon, are you.'",
                 objective='Defeat Initiate Vael', hp=2.5, adds=[(12105, 'hill avenger', [12, 13])], every=25, count=2),
            L('alrek', choice('hrodda_camp', 'Speak with Hrodda at her father\'s fire',
                   "I followed you. Of course I followed you.\n\nHe's himself again. He knows what he signed. He'll carry it. But your captain has a bounty on his head - he's raided your farms for twenty years. You've earned that bounty.\n\nI won't stop you. I'll only ask you to [spare him]. Or take the [bounty], and I'll know what your people are.",
                   [('spare him', "Then the hills owe you, and the hills remember. Go to your captain. Tell him Alrek's war is over, and Hrodda's word on it.", 'next:spared'),
                    ('bounty', "...I see. Do it quickly, then. And don't come west again.", 'next:bounty')])),
            L('spared', end_talk('captain_mardoc', 'Report to Captain Mardoc', "No bounty, no head, and a hill-girl's word that the raids are done.\n\nYou know what? I'll take that. It's the best deal this post has had in twenty years. Here - from the garrison.", 'peace')),
            L('bounty', end_talk('captain_mardoc', 'Report to Captain Mardoc', "So that's Alrek. Twenty years of raids, and he ends in a sack.\n\nThe girl's gone back to the hills. The lads say she'll make a worse chief than her father ever did. We'll see. Here's your bounty.", 'bounty')),
        ],
        {'peace': {'text': "From the garrison - and Hrodda left this for you at the gate.", 'items': [it_peace], 'choice': [it_hill, it_crimson]},
         'bounty': {'text': "The bounty. All of it.", 'tragic': True, 'items': [it_bounty], 'choice': [it_hill, it_crimson]}},
        topics={'captain': "Mardoc. The only one of your soldiers who looked at me when I spoke."})

# ============================================================================================================== Dartmoor
z = Zone(4, 'Dartmoor', 1, 'alb_dartmoor')
ZONES.append(z)
z.npc('mirela', 'Mirela Stonewright', [143, 323], 'f', 40, idle="Grimspound stands because we keep our oaths. Even the ones we made to giants.")
z.npc('jory', 'Jory Stonewright', [986, 498], 'm', 38, during=['quarry_oath/jory'])
z.npc('mirela_circle', 'Mirela Stonewright', [1286, 830], 'f', 40, during=['quarry_oath/judge'])
z.npc('bryn_asquith', 'Bryn Asquith', [158, 300], 'f', 48, guild='Dragonslayer', idle="Golestandt sleeps. Dragonslayers don't.")
z.npc('brother_alun', 'Brother Alun', [121, 326], 'm', 40, idle="Fire. Fire and a voice in it. Leave me be.")
z.npc('sir_wystan', 'Sir Wystan', [998, 1360], 'm', 47, guild='Dragonslayer', during=['dragons_tithe/wystan'])

it_oath = z.item('Quarry-Oath Ring', 'ring', 42, 'ward', "Every quarryman of Grimspound wears one. It is cut from the same block as the giants' standing stone.")
it_heart = z.item('Heartstone Pendant', 'neck', 42, 'might', "A sliver of the giants' heartstone. It grows heavier when you lie.")
it_chisel = z.item("Jory's Chisel-Pin", 'bracer', 42, 'finesse', "A mason's chisel, its edge filed down into a bracer-pin. It still bites.")
it_granite = z.item('Granite-Weave Mantle', 'cloak', 42, 'mind', "Grey cloth that falls in stiff folds like rock. Giants will not strike someone who wears it - or so the story goes.")
z.quest('quarry_oath', 'The Quarry Oath', 42, 'mirela',
        "Grimspound lives because of an oath. Our grandfathers cut stone from the giants' hills, and in return gave the giants a share of every stone cut, and never touched the standing stones in the east.\n\nSomeone has broken it. The heartstone is gone from the eastern circle, and the stonecallers are gathering. Before they come for Grimspound - will you [find the thief]? I think I know where to start. I'm afraid I know.",
        'find the thief',
        "Someone stole the heartstone from the granite giants' standing stones, breaking the oath that keeps Grimspound safe.",
        [
            search(4, [688, 516], "Search the giants' building stores in the west", "a quarryman's chisel", CRATE,
                   "A Grimspound chisel, dropped in the dirt where the heartstone was dragged. Its haft is marked with a J. Mirela's brother is the only J in the quarry."),
            L('jory', talk('jory', "Find Jory Stonewright in the brigands' camp",
                 "Mirela sent you. Course she did.\n\nI sold it. All right? The brigands' captain paid me more silver than Grimspound's seen in ten years. He says once the giants flatten the town, the silver under it is his. I thought he was joking. He wasn't joking. He's got the [heartstone] in his tent.", kw='heartstone')),
            kill(4, [1004, 524], "Fight through the brigands' camp", 'ruthless brigand', 5232525, [40, 41], 5),
            boss(4, [992, 508], "Take back the heartstone from the brigand captain", "Harrow Vane goes down with silver spilling from his purse. In his tent, under a blanket, the heartstone glows like a coal.",
                 'Harrow Vane, Brigand-Captain', 5232525, 45, "A lean man in good boots steps out of the biggest tent. 'Grimspound's stone? It's mine. Bought and paid.'",
                 objective='Defeat Harrow Vane', hp=2.5, adds=[(5232525, 'ruthless brigand', [40, 41])], every=30, count=2),
            defend(4, [1290, 840], "Return the heartstone to the eastern circle", "The heartstone settles into its socket with a sound like a great breath. The stonecallers lower their arms, and turn, and go back into the hills.",
                   'Mirela Stonewright', 770005, 40, "Mirela is waiting at the circle. 'Quickly - they're coming. Hold them while I set it.' Over the ridge: giants.",
                   [(770005, 'granite giant gatherer', [42, 43])], 'Keep Mirela alive while she sets the heartstone', model=38, duration=90,
                   then_boss={'tpl': 770006, 'name': 'Stonecaller Oruk', 'lv': 47, 'announce': "A giant with a voice like a landslide: 'OATH-BREAKERS. THE STONE COMES HOME, AND SO DO YOU.'", 'objective': 'Defeat Stonecaller Oruk'},
                   thanks="It's set. It's set. Oh, gods, my hands."),
            L('judge', choice('mirela_circle', 'Talk to Mirela at the circle',
                   "It's done. And Jory's waiting by the road. He knows what he did.\n\nThe giants have their own way with oath-breakers: they would take him into the hills and he would not come back. Grimspound's way is exile. I can't choose. He's my brother. You choose - give him to [the giants], or to [Grimspound].",
                   [('the giants', "...Yes. It was their stone. It's their right. I'll tell him myself. That much I owe him.", 'ending:giants'),
                    ('Grimspound', "Exile. He'll go west, to the coast, and never come back. It's still more mercy than he showed us. Thank you.", 'ending:exile')])),
        ],
        {'giants': {'text': "The quarry wanted you to have this. And I - I want you to have his chisel. I can't look at it.", 'tragic': True, 'items': [it_oath], 'choice': [it_chisel, it_heart]},
         'exile': {'text': "The quarry's thanks.", 'items': [it_oath], 'choice': [it_heart, it_granite]}})

it_scale = z.item('Golestandt Scale Brooch', 'gem', 48, 'might', "A sliver of dragon scale the size of a thumbnail. It is still warm, weeks later.")
it_hart = z.item("White Hart Mantle", 'cloak', 48, 'ward', "Sir Wystan's own cloak, singed at the hem.")
it_ash = z.item('Ash-Grey Signet', 'ring', 48, 'mind', "A dragonslayer's ring, its stone gone milky from the heat.")
it_vow = z.item("Slayer's Vow-Belt", 'belt', 48, 'finesse', "Every notch a vow. Some of them are crossed out.")
it_ember = z.item('Ember-Heart Bracer', 'bracer', 48, 'faith', "A bracer of blackened bronze that the dragon's breath could not melt.")
z.quest('dragons_tithe', "The Dragon's Tithe", 48, 'bryn_asquith',
        "This is no task for one, so find friends - GROUP work.\n\nMy order sent three slayers to study Golestandt's lair. One came back - Brother Alun, there, who will not stop shaking. One is dead. And Sir Wystan, Alun says, was alive under the rubble when Alun ran.\n\nThe giants on that slope serve the dragon - they bring it a tithe of everything that lives. Will you [go after Wystan]? Ask [Alun] what he saw, if you can bear it.",
        'go after Wystan',
        "GROUP. A dragonslayer was left alive under the rubble of Golestandt's lair; the giants that serve the dragon stand between.",
        [
            talk('brother_alun', 'Ask Brother Alun what happened',
                 "We were careful. We were so careful. The dragon was asleep. And then the giants came - they serve it, they bring it the dead, a [tithe] - and the rubble came down on Wystan and I ran. I RAN.", kw='tithe'),
            reach(4, [880, 1180], "Go to the dragon's road in the south", "The giants watch this road. Cairns line it - each with something that once lived laid on top.", r=20),
            kill(4, [883, 1130], "Kill the giants who watch the dragon's road", 'granite giant outlooker', 770011, [50, 51], 4),
            search(4, [1004, 1372], 'Search the smouldering rubble below the lair', "a scorched shield with a white hart", CRATE,
                   "Sir Wystan's shield. Under it, a gap in the rubble - and a voice, hoarse with smoke: 'Took your time.'"),
            defend(4, [1000, 1362], 'Dig Sir Wystan out of the rubble', "The last stone comes away. Sir Wystan crawls out, burnt and grinning.",
                   'Sir Wystan', 770002, 47, "The rubble shifts under your hands - and the stonelords come down the slope to collect their tithe.",
                   [(770002, 'granite giant pounder', [50, 52])], 'Keep Sir Wystan alive while he is dug out', model=9, duration=100, every=22, count=2,
                   then_boss={'tpl': 770001, 'name': 'Stonelord Gauth, Tithe-Taker', 'lv': 55, 'hp': 2.6, 'announce': "A huge giant with a basket on its back of bones. 'THE SLAYER IS THE DRAGON'S. ALL WHO FALL HERE ARE THE DRAGON'S.'", 'objective': 'Defeat Stonelord Gauth'},
                   thanks="Ha! Ha. Ow. Bryn sent you? Bryn would."),
            L('wystan', choice('sir_wystan', 'Talk to Sir Wystan',
                   "I saw it. Golestandt. Woke while the rocks were falling, looked right at me. Then looked away, and went back to sleep. Like I was a fly.\n\nI cut this off it - a scale - before the rubble. Bryn will want it. With this she'll have the order's council behind her, and they'll march on the lair by spring.\n\nOr you tell her I said [leave it sleeping]. Because it let us go, and I don't think it will twice. Or give her [the scale]. Your choice. I'm too tired.",
                   [('the scale', "Then take it, and tell her I'll be at the front of the line. Gods help us.", 'next:war'),
                    ('leave it sleeping', "Thank you. Tell her it was my word, not yours. She'll hate it less.", 'next:peace')])),
            L('war', end_talk('bryn_asquith', 'Return to Bryn Asquith', "A scale. A real scale. The council will have to listen now.\n\nAnd Wystan alive - Alun stopped shaking when he heard. Take what you like from the armoury. Come spring, we'll need everyone.", 'war')),
            L('peace', end_talk('bryn_asquith', 'Return to Bryn Asquith', "'Leave it sleeping.' From Wystan, of all men.\n\n...He's right, I suppose. He usually isn't. Take what you like. And thank you for bringing him home.", 'peace')),
        ],
        {'war': {'text': "From the order's armoury.", 'items': [it_scale], 'choice': [it_vow, it_ember, it_ash]},
         'peace': {'text': "From the order's armoury.", 'items': [it_hart], 'choice': [it_vow, it_ember, it_ash]}},
        topics={'Alun': "Brother Alun. Over there, by the wall. Be gentle."}, group=True)

# ============================================================================================================== Cornwall
z = Zone(6, 'Cornwall', 1, 'alb_cornwall')
ZONES.append(z)
z.npc('kerra_aldar', 'Kerra Aldar', [1399, 545], 'f', 15, idle="Thirty sheep last spring. Nine now.")
z.npc('tregarth', 'Tregarth the Hunter', [1252, 762], 'm', 24, idle="The moor is wrong this year. Even the wolves know it.")
z.npc('tregarth_den', 'Tregarth the Hunter', [902, 890], 'm', 24, during=['white_wolf/den'])
z.npc('hywel', 'Old Hywel', [1405, 540], 'm', 30, idle="My grandfather's grandfather marched with the legion. Some of it, I think, is still marching.")
z.npc('lt_penhale', 'Lieutenant Penhale', [1416, 546], 'm', 30, idle="Report to the commander if it's official. Report to me if it's strange.")
z.npc('kit', 'Kit Hywel', [554, 1100], 'm', 20, during=['drowned_ninth/kit', 'drowned_ninth/standard'])

it_crook = z.item("Shepherd's Crook-Pin", 'gem', 17, 'charm', "A little silver crook. Kerra's mother wore it, and her mother.")
it_fang = z.item('White Fang Necklace', 'neck', 17, 'finesse', "A long white canine on a leather thong. It was hard won.")
it_moor = z.item('Moor-Grass Cloak', 'cloak', 17, 'ward', "Woven of Cornish wool and dyed the colour of the moor in autumn.")
it_stalk = z.item("Stalker-Bone Ring", 'ring', 17, 'might', "Carved from a death stalker's bone. Cold to wear.")
z.quest('white_wolf', 'The White She-Wolf', 17, 'kerra_aldar',
        "Wolves took my flock - a few at a time, all spring, then twenty in one night. A white she-wolf leads them. I've seen her on the ridge, watching the fold.\n\nI want her dead. I want her hide on my floor. Will you [hunt her]? Tregarth the hunter knows the moor - he'll tell you where she dens, even if he won't like it.",
        'hunt her',
        "Kerra Aldar wants the white she-wolf that led the pack against her flock hunted down.",
        [
            search(6, [1352, 498], "Look over Kerra's ruined sheepfold", "a bloodied shepherd's crook", CRATE,
                   "The fold's torn open. But the tracks are wrong for hunting wolves - they come in running, from the west, as if something were driving them."),
            talk('tregarth', 'Ask Tregarth the hunter about the white wolf',
                 "The white bitch? I know her. She's been on this moor eight years and never touched a sheep till this spring. Something's pushing the packs east - the [death stalkers] are out of the woods and hungry. Kill a few of those and see where the wolves go.", kw='death stalkers'),
            kill(6, [853, 882], 'Hunt the death stalkers on the western moor', 'death stalker', 12823, [17, 18], 4,
                 text="Gorged, every one of them - and in the last one's den, a pile of small white bones. Wolf cubs. The she-wolf's den is close."),
            reach(6, [910, 897], "Find the white she-wolf's den", "She's there. Thin as a rake, white fur gone grey with mud, standing over two cubs - all that's left of her litter. She doesn't run. She just watches you.", r=15),
            L('den', choice('tregarth_den', 'Decide with Tregarth',
                   "There she is. Followed you up.\n\nShe took Kerra's sheep, right enough. And she took them because the stalkers took her cubs and there was nothing else on the moor. Now the stalkers are dealt with. She'll go back west, or I'm no hunter.\n\nKerra asked for her hide. I won't do it for you. [Kill her], or [let her go].",
                   [('kill her', "...Your call. Make it clean, at least.", 'next:hunt'),
                    ('let her go', "Good. Go tell Kerra. She'll shout. Let her shout. She'll understand by spring.", 'next:mercy')])),
            L('hunt', kill(6, [912, 900], 'Kill the white she-wolf', 'the white she-wolf', 12829, 18, 1,
                 text="She doesn't fight much. The cubs run off into the heather.", next='revenge')),
            L('mercy', end_talk('kerra_aldar', 'Tell Kerra Aldar', "You LET HER GO? I asked for -\n\n...Death stalkers. Her own cubs. Gods. Tregarth told me the same and I wouldn't hear it.\n\nFine. FINE. If a single sheep goes missing, I'm coming to find you. Here - for the stalkers, if not the wolf.", 'mercy')),
            L('revenge', end_talk('kerra_aldar', 'Tell Kerra Aldar', "She's dead? Good. Good.\n\nThen why do I feel like this. Tregarth told me why she came. I wish he hadn't. Here. Take your reward and the hide - I don't want it on my floor after all.", 'revenge')),
        ],
        {'mercy': {'text': "For the stalkers, if not the wolf.", 'items': [it_crook], 'choice': [it_moor, it_stalk]},
         'revenge': {'text': "Take it. Take all of it.", 'tragic': True, 'items': [it_crook], 'choice': [it_fang, it_stalk]}})

it_eagle = z.item('Eagle of the Ninth', 'neck', 24, 'might', "A legion's bronze eagle, small enough now to wear. It was carried into the marsh four hundred years ago.")
it_heather = z.item("Kit's Heather Wreath", 'gem', 24, 'charm', "A wreath of dried heather, bound with red thread. It does not crumble.")
it_legion = z.item('Legionary Cingulum', 'belt', 24, 'ward', "A soldier's belt of bronze plates. The leather is new; the bronze is very old.")
it_aquila = z.item("Standard-Bearer's Cape", 'cloak', 24, 'faith', "A wolfskin cape, of the kind a legion's standard-bearer wore over his helm.")
z.quest('drowned_ninth', 'The Drowned Ninth', 24, 'hywel',
        "Every autumn the drowned legion marches the old road south - ghosts, skeletons, whatever they are. Every autumn somebody from my family lays a wreath on their road. My grandfather's grandfather was one of them, so they say.\n\nThis year my grandson Kit laid it. He didn't come back. The [lieutenant] says it's not army business. Will you [find Kit]?",
        'find Kit',
        "Old Hywel's grandson Kit laid a wreath on the road where the drowned legion marches, and did not come home.",
        [
            talk('lt_penhale', 'Ask Lieutenant Penhale about the legion',
                 "Not official business, no. But I've read the old reports. The Ninth went into the marshes after a raiding king and never came out. They march the old road south every year, back to the barrow where their [centurion] lies. Anyone on the road goes with them.", kw='centurion'),
            reach(6, [1340, 1222], "Walk the legion's old road south", "The road is churned by hundreds of feet that left no prints. Skeletons in rusted mail stand guard along it, still at attention.", r=20),
            kill(6, [1352, 1272], 'Break the legion\'s rearguard', 'skeletal legionnaire', 12884, [20, 21], 6),
            search(6, [1366, 1292], "Search the legion's camp", "a trampled heather wreath", CRATE,
                   "Kit's wreath, trodden flat. The tracks of the legion lead west across the moor - to the barrow of the giant dead.",
                   give="Kit's wreath"),
            reach(6, [560, 1090], "Follow the legion west to the great barrow", "A giant skeleton stands at the barrow mouth holding a legion's eagle - and beside it, in a red cloak, a pale young man holding the standard pole. Kit.", r=20),
            boss(6, [548, 1106], "Defeat the legion's centurion", "The centurion's bones fall into a heap. The legionaries stop where they stand and kneel, waiting for an order.",
                 'Centurion of the Drowned Ninth', 12688, 27, "The giant turns. 'Standard-bearer! Hold the line!' Kit doesn't move. The legion does.",
                 objective='Defeat the Centurion', hp=2.4, adds=[(12884, 'skeletal legionnaire', [20, 21])], every=25, count=2),
            L('kit', talk('kit', 'Talk to Kit',
                 "I couldn't put it down. The standard. I tried. They needed someone to carry it and I was there and I just... couldn't put it down.\n\nIt's lighter now. They're waiting. They're waiting for someone to tell them [what to do].", kw='what to do')),
            L('standard', choice('kit', "Decide what becomes of the legion's standard",
                   "The standard - the eagle. If we [lay it to rest] in the barrow with the centurion, I think they'll sleep. All of them. No more marching.\n\nOr we [bring it home]. Grandfather would - gods, he'd weep. The Eagle of the Ninth, in our house. It's ours too, isn't it? Our family's?",
                   [('lay it to rest', "You're right. You're right. Here - help me. ... There. Listen. Do you hear that? Nothing. Nothing at all.", 'next:rest'),
                    ('bring it home', "Grandfather will never believe it. Come on. Let's go before they change their minds.", 'next:home')])),
            L('rest', end_talk('hywel', 'Bring Kit home to Old Hywel', "He's home. And the legion's asleep - he says you laid the eagle down with them.\n\nFour hundred years, that road. My family will still lay a wreath, mind. Out of respect. But we won't be going to find anyone.", 'rest')),
            L('home', end_talk('hywel', 'Bring Kit home to Old Hywel', "The Eagle of the Ninth. In my house.\n\n...I heard marching last night, you know. Faint. Coming up the road from the marsh, where it's never come before. Kit hears it too. Take something, quick, before I change my mind about all of this.", 'home')),
        ],
        {'rest': {'text': "Kit made this for you.", 'items': [it_heather], 'choice': [it_legion, it_aquila]},
         'home': {'text': "Take something.", 'tragic': True, 'items': [it_heather], 'choice': [it_eagle, it_legion]}},
        topics={'lieutenant': "Penhale. Young. Reads too much. He might listen."})

# =========================================================================================================== Llyn Barfog
z = Zone(7, 'Llyn Barfog', 1, 'alb_llyn_barfog')
ZONES.append(z)
z.npc('nest', 'Nest ferch Rhys', [886, 798], 'f', 18, idle="Have you heard them? At night? Don't listen if you do.")
z.npc('gwion', 'Gwion the Harper', [878, 776], 'm', 22, idle="Every song in this valley ends in the lake. I've tried to write one that doesn't.")
z.npc('iolo', 'Iolo ap Rhys', [838, 1312], 'm', 20, during=['hounds/iolo', 'hounds/horn'])
z.npc('teilo', 'Brother Teilo', [890, 796], 'm', 24, idle="Every brother in my house is dead and still walking. I am the only one who stayed dead-tired instead.")
z.npc('elfodd', 'Abbot Elfodd', [1324, 154], 'm', 30, during=['psalter/abbot', 'psalter/release'])

it_horn2 = z.item('Horn of the Hunt', 'gem', 21, 'finesse', "A small, curling horn of black bone. The hounds know whoever carries it.")
it_annwn = z.item('Cwn Annwn Collar', 'neck', 21, 'might', "A red leather collar with a silver bell. The bell does not ring.")
it_harp = z.item("Harper's Cord", 'belt', 21, 'mind', "Strung with old harp strings, each one tuned.")
it_nest = z.item("Nest's Shawl", 'cloak', 21, 'ward', "Thick Welsh wool, red and black. She made it for Iolo's wedding gift.")
z.quest('hounds', 'The Hounds of Annwn', 21, 'nest',
        "My husband Iolo heard the hounds of Annwn three nights ago. The white hounds with red ears. Whoever hears them dies within the year - everybody knows that.\n\nIolo isn't one to wait for it. He took his spear and went to hunt them, to break the doom. Gwion the [harper] knows the old stories. Will you [go after Iolo]?",
        'go after Iolo',
        "Iolo heard the hounds of Annwn - a death omen - and went to hunt them rather than wait to die.",
        [
            talk('gwion', 'Ask Gwion the harper about the hounds',
                 "The Cwn Annwn hunt from the old stones south of here, on the slopes. Their master is a huntsman of the Otherworld. The story goes, if a living man blows the huntsman's horn, the hunt passes him by - but the doom must fall on someone. They always find someone. Iolo will go to the [stones].", kw='stones'),
            kill(7, [915, 1185], 'Hunt the hounds of Annwn on the slopes', 'cwn annwn', 12999, [19, 20], 5,
                 text="They don't bleed. They fade, like breath on cold glass. Further south, a horn calls."),
            search(7, [868, 1342], 'Search the old stones in the south', "a dropped hunting spear", CRATE,
                   "Iolo's spear, the shaft bitten through. A trail of blood to the west - and the hunt's horn calling again, very close."),
            boss(7, [840, 1320], "Defeat the huntsman of Annwn", "The huntsman lowers his horn and looks at you a long while. Then he and his hounds are gone, and only the horn lies on the grass.",
                 "Gwyn's Huntsman", 13001, 24, "A tall grey figure rides out of nothing on a horse of mist, the white hounds at its heels. It lifts a horn.",
                 objective="Defeat Gwyn's Huntsman", hp=2.4, adds=[(12999, 'cwn annwn', [19, 20])], every=25, count=2),
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

it_psalter = z.item("Abbot's Psalter Charm", 'gem', 28, 'faith', "A single vellum page in a silver case. The psalm on it is for the dead.")
it_vigil = z.item('Vigil Cloak', 'cloak', 28, 'ward', "A monk's heavy brown cloak. Ghosts of soldiers once stood watch over it.")
it_evoc = z.item("Evocatus' Ring", 'ring', 28, 'might', "A veteran soldier's ring, bearing the mark of a legion long gone.")
it_quill = z.item("Copyist's Bracer", 'bracer', 28, 'mind', "Ink-stained leather. The abbey's copyists wore them for three hundred years.")
z.quest('psalter', 'The Last Psalm', 28, 'teilo',
        "I'm the last brother of the abbey in the north - the last living one. Thirty years ago our abbot made a pact with the ghosts of an old legion: they would guard our house from raiders. They did. They guarded it from everything.\n\nThis winter my brothers died one by one, and rose again, and went back to their prayers. I ran. I am not proud of it. Will you [go to the abbey]? The abbot's psalter holds the pact. Perhaps it holds a way out.",
        'go to the abbey',
        "Brother Teilo's abbey made a pact with the ghosts of a Roman legion, and now his dead brothers walk.",
        [
            reach(7, [1260, 236], 'Climb the road to the abbey in the north', "The abbey bell is ringing for vespers. Hooded monks walk the cloister in pairs. None of them cast a shadow.", r=20),
            kill(7, [1312, 177], "Free the dead brothers of the abbey", 'undead monk', 13034, [26, 27], 6,
                 text="Each one says 'thank you' as it falls."),
            search(7, [1332, 162], "Find the abbot's psalter", "a chained psalter on a lectern", CRATE,
                   "The pact is written in the margin of the psalm for the dead: 'Guard this house until the last brother leaves it.' And Teilo left.",
                   give="the abbot's psalter"),
            L('abbot', talk('elfodd', 'Speak with the ghost of Abbot Elfodd',
                 "You have the psalter. Good. I made the pact. I meant it for our protection. The legion took it to the letter, as soldiers do - the last brother left, so the house is theirs, and so are we.\n\nTheir veteran, Decimus, holds the pact. Break him, and I can [read the last psalm].", kw='read the last psalm')),
            boss(7, [1318, 172], "Defeat Decimus, keeper of the pact", "The old soldier salutes you as he fades. 'Relieved. At last.'",
                 'Evocatus Decimus', 13010, 30, "An old soldier in a red cloak plants himself in the cloister. 'This house is under guard. Stand down.'",
                 objective='Defeat Evocatus Decimus', hp=2.5, adds=[(13034, 'undead monk', [26, 27])], every=30, count=2),
            L('release', choice('elfodd', 'Choose with the abbot',
                   "Now I can read it - the last psalm, and every brother here goes to his rest, myself among them. The abbey will stand empty, and the raiders will come, and the valley will have no one to shelter it.\n\nOr we [keep watch], the dead brothers and I, without the legion - and the valley keeps its shelter. Teilo would have to live with that. Tell me: do I [read the psalm]?",
                   [('read the psalm', "Then listen. ... It's been a long time since I could hear myself sing.", 'next:rest'),
                    ('keep watch', "Then we watch. Tell Teilo we are not angry. Tell him to visit, if he can bear it.", 'next:watch')])),
            L('rest', end_talk('teilo', 'Return to Brother Teilo', "I heard them. All the way down here. Singing - all of them, the old psalm. And then the bell stopped.\n\nI'll go back in the spring and sweep the chapel. Somebody should.", 'rest')),
            L('watch', end_talk('teilo', 'Return to Brother Teilo', "They're keeping watch. Still. Without the legion.\n\nI'll visit. I'll bring bread they can't eat and news they can't use. I suppose that's what brothers are for.", 'watch')),
        ],
        {'rest': {'text': "Take this, from the abbey.", 'items': [it_psalter], 'choice': [it_evoc, it_quill]},
         'watch': {'text': "Take this, from the abbey.", 'tragic': True, 'items': [it_psalter], 'choice': [it_vigil, it_evoc]}})

# ================================================================================================= Campacorentin Forest
z = Zone(8, 'Campacorentin Forest', 1, 'alb_campacorentin')
ZONES.append(z)
z.npc('elowen', 'Dame Elowen Marsh', [970, 878], 'f', 25, idle="I'm old. Old women are allowed to sit and look at the road.")
z.npc('robin', 'Robin the Page', [1162, 706], 'm', 6, during=['page/road', 'page/robin', 'page/sword', 'page/knight', 'page/letter'])
z.npc('ivo_penrose', 'Scholar Ivo Penrose', [340, 160], 'm', 18, idle="The Lethantis Association does excellent work. Write that down. They read everything.")
z.npc('esras', 'Esras the Hermit', [152, 902], 'm', 20, during=['heretic/hermit', 'heretic/hunters', 'heretic/proof'])

it_page = z.item("Page's Ribbon", 'gem', 7, 'charm', "A faded blue ribbon, tied round a lock of hair.")
it_faithful = z.item('Ring of the Faithful Page', 'ring', 7, 'might', "A boy's ring, too small for most fingers. It fits yours.")
it_aldric = z.item("Aldric's Broken Spur", 'bracer', 7, 'finesse', "A knight's spur, snapped. He ran.")
it_letter = z.item('Sealed-Letter Sash', 'belt', 7, 'mind', "Blue silk embroidered with a page's careful letters.")
z.quest('page', 'A Letter Never Delivered', 7, 'elowen',
        "When I was a girl, a page called Robin went to the war with his knight, Sir Aldric. He promised to come back with a letter for me. He never did.\n\nNow the woodsmen say a phantom page walks the east road, asking for a lady called Elowen. Sixty years. I'm too old to walk that road. Will you [find him] for me?",
        'find him',
        "Dame Elowen's sweetheart Robin went to war sixty years ago as a knight's page. A phantom page now walks the east road asking for her.",
        [
            L('road', reach(8, [1152, 702], 'Walk the east road', "A pale boy in a page's tabard stands in the road. 'Pardon - have you seen my lady? Her name is Elowen.'", r=15)),
            L('robin', talk('robin', 'Talk to the phantom page',
                 "Elowen? You know her? Oh - oh, good. I've a letter for her. Only my knight, Sir Aldric - he went off the road when the raiders came, and he took my sword, and I can't leave without my [sword]. A page doesn't.", kw='sword')),
            L('sword', search(8, [1180, 732], "Find Robin's sword along the road", "a small rusted sword", CRATE,
                   "A boy's short sword, rusted to the scabbard. The scabbard is lined with an old blood-stain. The page was stabbed in the back, and his sword hidden here.")),
            L('knight', boss(8, [1204, 700], "Face Sir Aldric", "Sir Aldric falls and does not get up. Robin comes and stands over him for a while.",
                 'Sir Aldric the Faithless', 12485, 9, "A ghostly knight walks out of the trees. 'The boy saw me run. The boy would have told. I had to.'",
                 objective='Defeat Sir Aldric', hp=2.0, adds=[(12499, 'phantom page', [4, 5])], every=30, count=1)),
            L('letter', talk('robin', 'Give Robin back his sword',
                 "My sword. Thank you. I'm free to go now. I - would you take the [letter]? I don't think I can go into the town. I don't think I'm meant to.", kw='letter', give="Robin's letter")),
            choice('elowen', 'Give Dame Elowen the letter',
                   "His letter. His hand - look, he never could make a proper 'E'.\n\n'Wait for me.' That's all it says. 'Wait for me.' Well. I did.\n\nHe's still out there, isn't he. On the road. Should I [go to him]? Or should I [stay], and keep his letter, and let a boy go home?",
                   [('go to him', "Then help me to the gate, and no further. I can manage the rest. I've waited sixty years; I can manage a little walk.", 'ending:went'),
                    ('stay', "Yes. He's waited long enough. Let him go home. I'll keep this under my pillow, and that will do.", 'ending:stayed')]),
        ],
        {'went': {'text': "Take these. I won't need them.", 'tragic': True, 'items': [it_page], 'choice': [it_faithful, it_letter]},
         'stayed': {'text': "Take something, for him.", 'items': [it_page], 'choice': [it_faithful, it_aldric]}})

it_brand = z.item('Lethantis Brand-Ring', 'ring', 15, 'mind', "An iron ring with the Association's mark. Taken from a dead man who meant to kill an old one.")
it_heresy = z.item("Heretic's Satchel", 'belt', 15, 'faith', "A hermit's scrip, full of notes in a tiny hand.")
it_ogre = z.item('Ogre-Hide Wrap', 'cloak', 15, 'might', "Rough green hide. An ogre wore it before you; a Lethantis mage made the ogre.")
it_seeker = z.item("Seeker's Bracer", 'bracer', 15, 'finesse', "Light, quiet, and made for following people.")
z.quest('heretic', 'The Heretic of the Wood', 15, 'ivo_penrose',
        "My old master Esras was branded a heretic and driven out by the Association. He claimed the wood ogres in the south were bred - made - by Lethantis mages, as guards. Nonsense, of course. Officially.\n\nHe's hiding somewhere in the western swamps. I need his notes before the Association's seekers find him - I mean, so I can refute them properly. Will you [find Esras]? Discreetly.",
        'find Esras',
        "The hermit Esras claims the wood ogres were bred by Lethantis mages. His old student wants his notes - before the Association's seekers find him.",
        [
            kill(8, [604, 1022], 'Find out what the wood ogres are', 'wood ogre scourge', 12630, [13, 14], 5,
                 text="On the last one's shoulder, under the warpaint: a brand, old and neat. The Lethantis mark."),
            search(8, [612, 1046], "Search the ogres' camp", "a brand-iron", CRATE,
                   "A mage's branding iron, its haft carved with the Association's sigil and a number: 314.", give='a Lethantis brand-iron'),
            L('hermit', talk('esras', 'Find the hermit in the western swamps',
                 "Ivo sent you? Ivo. Ha. Good boy, frightened of everything.\n\nYou've seen the brands. Then you know. They made the ogres - bred them from captive giants and wild men - to guard the old tower lands. Then they let them go wild when the work was done. Ogres who remember being something else. I have the [proof] here.", kw='proof')),
            L('hunters', defend(8, [150, 905], "Protect Esras from the Association's seekers", "The last seeker falls in the mud. Esras sits down hard and laughs until he coughs.",
                   'Esras the Hermit', 12498, 18, "Robed figures step out of the reeds. 'Esras. You were warned.'",
                   [(12498, 'Lethantis seeker', [13, 14])], 'Keep Esras alive', model=9, duration=80, thanks="Ivo didn't send them. Did he? ...No. No, he wouldn't.")),
            L('proof', choice('esras', 'Decide what becomes of the proof',
                   "Here it is. Thirty years of notes. Take it to Ivo and he'll take it to the Crown, and the Association will burn - and every ogre in this forest will be hunted down as a crime to be hidden.\n\nOr [burn it]. The ogres live as they are. The mages keep their secret. I stay a madman. Or [take it to Ivo]. I'm too old to choose any more.",
                   [('take it to Ivo', "Go on, then. Tell him I forgive him for being frightened.", 'next:truth'),
                    ('burn it', "...There it goes. Thirty years. It burns like any other paper. Go and tell Ivo I'm a madman after all.", 'next:burned')])),
            L('truth', end_talk('ivo_penrose', 'Bring the notes to Ivo Penrose', "He was right. Every word. Gods help me, I told them where to look for him.\n\nI'll take this to the Crown myself. And then I'll go and find him and say sorry. Here - take this, and don't stay in town too long.", 'truth')),
            L('burned', end_talk('ivo_penrose', 'Tell Ivo Penrose', "Burned? All of it? Well - I suppose that settles the matter. A madman's ravings.\n\nYou're looking at me as if you know something. Don't tell me. Here. For your discretion.", 'burned')),
        ],
        {'truth': {'text': "Take this, and don't stay in town too long.", 'items': [it_brand], 'choice': [it_heresy, it_seeker]},
         'burned': {'text': "For your discretion.", 'tragic': True, 'items': [it_brand], 'choice': [it_ogre, it_seeker]}})

# ========================================================================================================= Avalon Marsh
z = Zone(9, 'Avalon Marsh', 1, 'alb_avalon_marsh')
ZONES.append(z)
z.npc('tilda_hael', 'Tilda Hael', [471, 921], 'f', 8, idle="If you see a fisherman with a mole shaped like a crown, kindly drag him home by the ear.")
z.npc('warden_brec', 'Marsh-Warden Brec', [492, 932], 'm', 15, idle="Bogmen don't hurt you if you don't hurt them. Mostly.")
z.npc('dai_morrow', 'Dai Morrow', [806, 1116], 'm', 8, during=['bog_king/dai', 'bog_king/crown'])
z.npc('squire_hamon', 'Squire Hamon', [946, 481], 'm', 15, idle="My knight died in the north marsh. A squire without a knight is just a boy with a sword.")
z.npc('sir_baldwin', 'Sir Baldwin the Elder', [1376, 344], 'm', 30, idle="I was a knight of the Vigil once. Long before they drowned.")
z.npc('last_vigil', 'Sir Edric of the Vigil', [356, 226], 'm', 20, during=['vigil/oath'])

it_reed2 = z.item('Reed Crown Circlet', 'gem', 9, 'charm', "A circlet of woven reeds. The bogmen made it for a king.")
it_frog = z.item("Bog-King's Ring", 'ring', 9, 'might', "Bone and black amber. Too large for a man's hand; it fits anyway.")
it_lily = z.item('Lily-Pad Mantle', 'cloak', 9, 'ward', "Green and slick and strangely warm. The bogmen are better weavers than they look.")
it_mud = z.item("Marsh-Warden's Belt", 'belt', 9, 'finesse', "Brec's spare. It has a pocket for everything.")
z.quest('bog_king', 'The Bog King', 9, 'tilda_hael',
        "My Dai is a fisherman, and a poor one, and the gentlest man in Avalon. Three days ago the bogmen came and took him off in his own boat - singing! - and they bowed to him.\n\nHe's got a birthmark like a little crown. The Warden says that's why. Will you [bring Dai home]? Brec the [warden] knows where they've taken him.",
        'bring Dai home',
        "Bogmen carried off Tilda Hael's betrothed, a fisherman with a crown-shaped birthmark, and bowed to him.",
        [
            talk('warden_brec', 'Ask the marsh-warden about the bogmen',
                 "Crown-mark, eh? The bogmen have a story about a king who'll come out of the water marked like that. They've been waiting a long while. They'll have him at the bog [towers] in the south.", kw='towers'),
            kill(9, [868, 1040], "Get past the bogman gatherers", 'bogman gatherer', 12005, [8, 9], 5,
                 text="They fight half-heartedly and keep looking south, towards the towers, as if afraid you'll interrupt something."),
            reach(9, [800, 1112], 'Find Dai at the bog towers', "Dai Morrow sits on a throne of reeds and driftwood, wearing a crown of lilies, eating something unidentifiable from a shell. He looks happier than any man you've ever seen.", r=15),
            L('dai', talk('dai_morrow', 'Talk to Dai Morrow',
                 "Oh! Hello! Did Tilda send you? She would. Isn't this mad?\n\nThey bow to me. They bring me fish - good fish, better than I ever caught. They listen when I talk. Nobody's ever listened when I talk. I've never been [anything], you understand. Here I'm a king.", kw='anything')),
            L('crown', choice('dai_morrow', 'Decide what Dai should do',
                   "Tilda's a good woman. Too good for me, everybody said so. Maybe she'd be better off.\n\nI don't know. You tell me. [Come home], or [stay] here and be a king of frogs and mud. I'll do whatever you say. I always do whatever people say. Except here.",
                   [('come home', "Right. Yes. Home. They won't like it - hold on, they REALLY won't like it -", 'next:escape'),
                    ('stay', "Really? You think so? Then tell Tilda... tell her I'm sorry. And I'm happy. Both at once. Is that allowed?", 'next:king')])),
            L('escape', defend(9, [790, 1150], 'Get Dai out of the bog', "The bogmen fall back into the water. Dai takes his crown off, looks at it, and puts it in his pocket.",
                   'Dai Morrow', 12008, 8, "The bogmen howl. 'The king is leaving! The king is leaving!'",
                   [(12007, 'bogman hunter', [9, 10])], 'Keep Dai alive', model=9, duration=75,
                   then_boss={'tpl': 12004, 'name': 'Bog-Mother Sloe', 'lv': 12, 'announce': "A huge old bogwoman rises out of the mere. 'MY king. MINE. Leave him!'", 'objective': 'Defeat Bog-Mother Sloe'},
                   thanks="That was horrible. I'm keeping the crown.")),
            L('home', end_talk('tilda_hael', 'Bring Dai home to Tilda', "DAI MORROW. You absolute -\n\nHe's asleep. He kept the crown, the fool. He says they listened to him. I listen to him! I'll listen better. Here, take something, before I cry.", 'home')),
            L('king', end_talk('tilda_hael', 'Tell Tilda Hael', "He's... staying. As a king. Of the bogmen.\n\nYou know, I always knew he'd leave me. I just thought it'd be for a woman. Not for - frogs. Take this. It was meant for him.", 'king')),
        ],
        {'home': {'text': "Take something, before I cry.", 'items': [it_reed2], 'choice': [it_frog, it_mud]},
         'king': {'text': "It was meant for him.", 'tragic': True, 'items': [it_reed2], 'choice': [it_lily, it_mud]}})

it_vig = z.item('Signet of the Vigil', 'ring', 18, 'ward', "The ring of a drowned order of knights. Their oath is engraved inside: 'Until relieved.'")
it_ban = z.item('Banner of the Vigil', 'cloak', 18, 'might', "The order's banner, cut down to a cloak. It is still wet, months later.")
it_cor = z.item("Corentin's Sword-Belt", 'belt', 18, 'finesse', "A good knight's belt, worn smooth where the sword rode.")
it_relief = z.item('Relief-Bell Charm', 'gem', 18, 'faith', "A tiny bronze bell, the kind that rang the changing of the watch.")
z.quest('vigil', 'Until Relieved', 18, 'squire_hamon',
        "My knight, Sir Corentin, led a patrol into the north marsh to find the old Order of the Vigil. They held these marshes three hundred years ago and drowned in them, still at their posts. Corentin found them. They killed him.\n\nI want to finish what he started. Old Sir [Baldwin] in the abbey town knows the Vigil's story. Will you [help me]?",
        'help me',
        "Squire Hamon's knight died seeking the drowned Order of the Vigil in the north marsh.",
        [
            talk('sir_baldwin', 'Ask old Sir Baldwin about the Vigil',
                 "The Vigil? Gods, I haven't heard that name in fifty years. I was the last squire they took before the marsh rose. They swore to hold the north marsh 'until relieved'. Nobody came to relieve them. The war moved on, and they drowned still standing their [watch].", kw='watch'),
            reach(9, [396, 420], 'Go into the north marsh', "Torches burn on poles in the water. Figures in rotten plate stand guard at every one.", r=20),
            kill(9, [371, 383], "Break through the Vigil's footmen", 'ghoul footman', 12017, [16, 17], 6),
            search(9, [352, 252], 'Find Sir Corentin', "Sir Corentin's body", BEDROLL,
                   "Sir Corentin lies with his sword still in hand and three dead ghouls around him. He died well. His signet is still on his finger.",
                   give="Corentin's signet"),
            boss(9, [362, 218], "Defeat the Ghoul Lord of the Vigil", "The Ghoul Lord kneels in the water. 'Are you... our relief?'",
                 'Lord-Commander of the Vigil', 12019, 21, "A great ghoul in a captain's plate raises a black sword. 'HALT. None pass the Vigil.'",
                 objective='Defeat the Lord-Commander', hp=2.4, adds=[(12018, 'ghoul knight', [17, 18])], every=25, count=2),
            L('oath', choice('last_vigil', 'Speak to the last knight of the Vigil',
                   "Three hundred years at our posts. We could not leave. We are sworn, until relieved.\n\nYou could speak the words - Sir Baldwin will have taught the squire, and the squire you. 'I relieve you.' Then we sleep. Or take our [banner] to Camelot, so they remember we held. But then we stand here until someone else comes.\n\nWill you [relieve us]?",
                   [('relieve us', "...Relieved. Relieved. Thank you. Thank you. Watch - watch is - ended.", 'next:relieved'),
                    ('banner', "Take it. Let them know. We will hold. We have always held.", 'next:banner')])),
            L('relieved', end_talk('squire_hamon', 'Return to Squire Hamon', "You relieved them? All of them? Sir Corentin would've - he'd have wept. He was soft like that.\n\nI'll take his signet to his mother. And then I suppose I'll find another knight. Here - from his things.", 'relieved')),
            L('banner', end_talk('squire_hamon', 'Return to Squire Hamon', "The banner of the Vigil. In Camelot. Sir Corentin would have been proud.\n\n...They're still standing there, though. Aren't they. Still holding. Waiting. Here - from his things.", 'banner')),
        ],
        {'relieved': {'text': "From Sir Corentin's things.", 'items': [it_relief], 'choice': [it_vig, it_cor]},
         'banner': {'text': "From Sir Corentin's things.", 'tragic': True, 'items': [it_relief], 'choice': [it_ban, it_cor]}},
        topics={'Baldwin': "Sir Baldwin the Elder, in the abbey town east. He's ancient. He was a squire of the Vigil, if you can believe it."})

# ============================================================================================================== Lyonesse
z = Zone(10, 'Lyonesse', 1, 'alb_lyonesse')
ZONES.append(z)
z.npc('wenna_trevose', 'Wenna Trevose', [1340, 1132], 'f', 38, guild="Castaways' Camp", idle="The sea took Lyonesse in a night. It didn't take everyone. It didn't let anyone go, either.")
z.npc('morvah', 'Morvah Trevose', [403, 258], 'f', 30, during=['last_evening/morvah', 'last_evening/evening'])
z.npc('sir_kendric', 'Sir Kendric', [1347, 1138], 'm', 48, guild="Castaways' Camp", idle="I watch for the Arawnites. One of us has to.")
z.npc('tobin', 'Tobin', [928, 1046], 'm', 30, during=['arawn_sacrament/tobin'])

it_shawl = z.item("Morvah's Shawl", 'cloak', 40, 'ward', "Folded neatly, as if for a stranger. It smells of salt and summer evenings.")
it_net = z.item('Drowned-Net Belt', 'belt', 40, 'finesse', "Knotted from a net that has been mended every evening for a thousand years.")
it_salt2 = z.item('Salt-Pearl Ring', 'ring', 40, 'mind', "A pearl from the drowned land. It is always wet.")
it_eve = z.item('Evening Star Pendant', 'neck', 40, 'faith', "Silver, set with a pale stone that glows at dusk.")
z.quest('last_evening', 'The Last Evening of Lyonesse', 40, 'wenna_trevose',
        "The drowned of Lyonesse - the danaoin - live their last day over and over. Sowing, fishing, mending nets. Waiting for an evening that never comes.\n\nMy sister Morvah wandered off a month ago. Yesterday I saw her from the hill - working the nets with the drowned on the north-west strand. Doing what they do. She didn't know me. Will you [bring her back]?",
        'bring her back',
        "Wenna Trevose's sister has begun living the drowned folk's endless last day.",
        [
            reach(10, [1268, 1094], 'Cross the drowned meadows west of the camp', "Pale spirits drift over the meadow - peallaidh, the drowned land's restless dead. They hum as they go, the same four notes over and over.", r=20),
            kill(10, [1264, 1094], "Lay the meadow's restless dead to rest", 'peallaidh', 12974, [38, 39], 5,
                 text="As each one fades it sighs, very softly: 'Is it evening yet?' The humming goes on, far off to the north-west, toward the strand."),
            search(10, [398, 276], "Search the path down to the north-west strand", "a woman's shawl, neatly folded", BEDROLL,
                   "Morvah's shawl, folded and left on a stone - the way the drowned leave their things before the tide comes. Below, on the strand, a woman sits mending nets among the drowned sailors."),
            L('morvah', talk('morvah', 'Find Morvah on the strand',
                 "Mind the nets, please. They must be mended by evening.\n\nWenna? I... I had a sister called Wenna. If I stop, you see, the day ends. And when the day ends, the water comes. They don't want the water to come again. I don't want it to come for them. Do you understand? It's nearly [evening].", kw='evening')),
            defend(10, [403, 258], "Stand with Morvah as the day breaks", "The drowned sailors stand still in the surf. The sky goes red, then gold, then dark. For the first time in a thousand years, it is evening in Lyonesse.",
                   'Morvah Trevose', 12952, 30, "You take the needle from Morvah's hand. Every danaoin on the strand turns its head.",
                   [(12952, 'danaoin sailor', [41, 43])], 'Keep Morvah alive', model=38, duration=100, every=22, count=2,
                   then_boss={'tpl': 12953, 'name': 'the Drowned Reeve', 'lv': 45, 'announce': "A drowned man in a reeve's chain stalks up out of the waves. 'THE DAY IS NOT DONE. THE NETS ARE NOT MENDED.'", 'objective': 'Defeat the Drowned Reeve'},
                   thanks="It's evening. Look. It's evening."),
            L('evening', choice('morvah', 'Talk to Morvah',
                   "It's evening. They're going to sleep - all of them, all along the strand. They aren't afraid any more.\n\nWenna. I remember Wenna now. But someone has to stay and mend the nets, or tomorrow it starts again. I could [stay], and they'd sleep every night from now on. Or I could [come home], and they'd wake tomorrow and never know.",
                   [('come home', "Then take me home. Before I change my mind. Before the morning.", 'next:home'),
                    ('stay', "Tell Wenna I remembered her. Tell her I'm the ferrywoman of Lyonesse now. Tell her to come to the strand at evening, sometimes.", 'next:stayed')])),
            L('home', end_talk('wenna_trevose', 'Return to the castaways\' camp', "She's here. She's asleep in my tent, holding my hand like when we were small.\n\nShe said the drowned will wake tomorrow and never know they had an evening. I said that's not our trouble. I hope I'm right.", 'home')),
            L('stayed', end_talk('wenna_trevose', 'Return to the castaways\' camp', "She stayed. She remembered me, and she stayed.\n\nI went up the hill at dusk and looked. The strand was quiet. And there was one lantern, down at the water, mending nets. I'll go every evening.", 'stayed')),
        ],
        {'home': {'text': "Take something. You've given me back my sister.", 'items': [it_eve], 'choice': [it_net, it_salt2]},
         'stayed': {'text': "She'd want you to have this.", 'tragic': True, 'items': [it_shawl], 'choice': [it_net, it_salt2]}})

it_arawn = z.item('Reliquary Shard', 'gem', 46, 'mind', "A shard of black glass from an Arawnite reliquary. Something moves inside it.")
it_kendric = z.item("Kendric's Watch-Cloak", 'cloak', 46, 'ward', "A knight's travelling cloak, salt-stained from the Lyonesse wind.")
it_drowned = z.item('Drowned Knight Signet', 'ring', 46, 'might', "The ring of a knight of Lyonesse. He drowned with his king.")
it_tobin = z.item("Tobin's Bracer", 'bracer', 46, 'finesse', "A squire's bracer. Tobin insisted.")
it_hier = z.item("Hierophant's Girdle", 'belt', 46, 'faith', "Bone and black silk, taken from a priest of Arawn. Scrubbed, and blessed, and still not quite clean.")
z.quest('arawn_sacrament', 'The Sacrament of Arawn', 46, 'sir_kendric',
        "This is work for a GROUP - gather friends before you go.\n\nThe priests of Arawn are gathering at the ruined cathedral in the south. My squire Tobin went to scout and didn't come back. Under the cathedral, the old knights of Lyonesse lie drowned with their king. The Arawnites mean to wake them - as theirs.\n\nWill you [go after Tobin]? Their grove on the eastern cliffs will tell you what they intend.",
        'go after Tobin',
        "GROUP. The priests of Arawn mean to raise Lyonesse's drowned knights at the ruined cathedral, and Sir Kendric's squire went to scout them.",
        [
            reach(10, [1420, 760], "Find the Arawnites' grove on the eastern cliffs", "Arawnite shamanesses dance around a fire of bones. A sealed scroll hangs from a stake in the middle.", r=20),
            kill(10, [1433, 742], 'Scatter the Arawnite shamanesses', 'arawnite shamaness', 12930, [44, 45], 5),
            search(10, [1442, 760], 'Take the orders from the grove', "orders sealed with Arawn's mark", CRATE,
                   "'At the ruined cathedral, on the dark of the moon. The squire will do. His blood will wake the knights, and they will kneel to Arawn.'",
                   give="the Arawnite orders"),
            kill(10, [1216, 1275], "Cut down the drowned footmen guarding the southern road", 'footman', 12957, [45, 46], 5,
                 text="They wear the drowned king's colours, but their eyes are already Arawn's."),
            reach(10, [930, 1050], 'Go to the ruined cathedral', "Priests in black kneel among the broken pillars. Tobin is tied to the altar-stone, white-faced and very angry.", r=20),
            boss(10, [930, 1050], 'Stop the sacrament', "The hierophant collapses across the altar. Under the floor, something that was stirring goes still again.",
                 'Hierophant Morcant of Arawn', 12977, 51, "A priest in a mask of bone rises from the altar. 'You are too late, and also just in time - Arawn accepts all blood.'",
                 objective='Defeat Hierophant Morcant', hp=3.0, adds=[(12977, 'priest of arawn', [47, 48])], every=25, count=2),
            L('tobin', talk('tobin', 'Untie Tobin', "About time! - sorry. Sorry. Thank you.\n\nThere's a reliquary under the altar, sir - I mean, friend. Black glass. It's what wakes them. Sir Kendric needs to [see it].", kw='see it', give="the black reliquary")),
            choice('sir_kendric', 'Bring Tobin and the reliquary to Sir Kendric',
                   "Tobin! Thank every god there is.\n\nAnd that - that's the reliquary? With it, a knight of Albion could wake the drowned knights of Lyonesse. As OURS. Two hundred knights for the realm's wars.\n\nOr we [shatter it], and they sleep forever. I know which I should choose. I don't trust myself. You decide: [wake them for Albion], or shatter it.",
                   [('shatter it', "Yes. Yes. Let the dead keep their own. ... There. Did you feel that? Like a held breath going out.", 'ending:shattered'),
                    ('wake them for Albion', "Then I'll keep it, and I'll keep it well, and gods help me if I'm wrong. Tobin, don't look at me like that.", 'ending:kept')]),
        ],
        {'shattered': {'text': "From the camp. You've earned more than we have.", 'items': [it_kendric], 'choice': [it_drowned, it_tobin, it_hier]},
         'kept': {'text': "From the camp.", 'tragic': True, 'items': [it_arawn], 'choice': [it_drowned, it_tobin, it_hier]}},
        group=True)
