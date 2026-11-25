"""Gotar's story quests (claude 2026-11-25, "Midgard - the plan", round 2) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_gotar

Wild. The south thread's road: Gjalpinulva's drakulv cult buys the svartalf outcasts with dragon-scale and gold, and their
scale-traders camp on the trade road beside the old svartalf post, a dragon-preacher with them. The drowned ship off the east shore
was carrying scale north. Envy drakelings creep up from the south, and the seithkona at the circle read the dragon waking.
The west thread brushes the north lakes (the wildlings are running from something in the west).

The zone's two older quests are kept as they were (nacken, rune_stave).

Arcs (recommended levels): The North Lakes (12-14), The Drowned Ship (14-17), The Scale-Traders (15-20), The Spirit Hills (16-18),
The Seith Circle (18-22).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(103, 'Gotar', 'mid_gotar', 'story103_gotar', {'nacken', 'rune_stave'},
          {'torunn', 'skald_hrafn', 'eilif', 'alfdis', 'flayer_kolr', 'hild'},
          {"Nacken's Fiddle-String", 'Black-Pool Ring', "Fiddler's Bow-Bracer", 'Dancing-Green Sash', "Hild's Rune-Stave Charm",
           "Seeress' Veil", 'Unbranded Bracer', "Flayer's Hook-Ring"}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157

person('gt_hallbjorn', 'Huscarl Hallbjorn', (700, 335), 'm', 32, model=M, guild="King Eirik's Huscarls",
       idle="Fort Atla's the King's. Everything south of it is anybody's.")
person('gt_runa', 'Runecaster Runa', (1232, 878), 'f', 30, model=F, guild='the Nalliten Runecasters',
       idle="The staves say the same thing every night. Fire under the ground, in the south.")

# ======================================================================== The North Lakes (12-14)
n1 = z.item("Nipper-Tooth Ring", 'ring', 12, 'might', "A ring of wolf-pup teeth. Fort Atla's soldiers wear them for luck.")
n2 = z.item("Lakeshore Belt", 'belt', 12, 'finesse', "Fish-leather, very supple.")
z.quest('gt_nippers', 'Wolf Nippers', 12, 'gt_hallbjorn',
        "The wolf nippers on the north lakes have grown bold - whole packs coming down to the fort's walls at dusk. Something's pushing them out of the west.\n\nWill you [thin the packs]?",
        'thin the packs',
        "Wolf nippers have grown bold on Gotar's north lakes, pushed out of the west.",
        [
            hunt((650, 400), "Thin the wolf nipper packs " + where((650, 400), 'gt_hallbjorn'), 'wolf nipper', 6),
            end_talk('gt_hallbjorn', "Tell Huscarl Hallbjorn", "Fewer. They're running from the west - from Svealand, where the snow came in summer.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [n1, n2]}})

n3 = z.item("Fish-Catcher's Net Charm", 'gem', 13, 'charm', "A knot of hobgoblin net. Lucky, they say.")
n4 = z.item("Fort Atla Gate Bracer", 'bracer', 13, 'ward', "Iron, the fort's mark on it.")
z.quest('gt_hobgoblins', 'The Fish-Catchers', 13, 'gt_hallbjorn',
        "The hobgoblins on the lakes cut the fort's nets and steal the catch. Not the worst thing in Gotar, but the men are hungry.\n\nWill you [drive them off]?",
        'drive them off',
        "Hobgoblin fish-catchers cut Fort Atla's nets on Gotar's north lakes.",
        [
            hunt((700, 500), "Drive off the hobgoblin fish-catchers " + where((700, 500), 'gt_hallbjorn'), 'hobgoblin fish-catcher', 5),
            end_talk('gt_hallbjorn', "Tell Hallbjorn", "Fish for supper. You're popular in the barracks.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [n3, n4]}}, requires='gt_nippers')

n5 = z.item("Wildling's Bone Torc", 'neck', 14, 'might', "Bone and sinew, wildling-work.")
n6 = z.item("Lake-Hunter's Mantle", 'cloak', 14, 'ward', "Reed-grey, for lying still by the water.")
z.quest('gt_wildlings', 'The Wildlings', 14, 'gt_hallbjorn',
        "Wildlings have made camp by the lakes. They've never come this far east. Break the camp - and if one will talk, ask why.\n\nWill you [break the camp]?",
        'break the camp',
        "Wildlings have camped on Gotar's north lakes, further east than they have ever come.",
        [
            hunt((640, 560), "Break the wildling camp " + where((640, 560), 'gt_hallbjorn'), 'wildling', 4),
            search(Z, P(645, 565), "Search the wildling camp", "a hide drawn with charcoal", BEDROLL,
                   "A crude drawing: a great wolf with its jaws open over a moon, and the wildlings running away from it, east."),
            end_talk('gt_hallbjorn', "Tell Hallbjorn", "A wolf eating the moon. That's the Blodfelag's story, out of West Svealand. If even the wildlings are running from it...", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [n5, n6]}}, requires='gt_hobgoblins')

# ======================================================================== The Drowned Ship (14-17)
d1 = z.item("Drowned Bell Charm", 'gem', 14, 'mind', "A ship's bell no bigger than a thumb. It rings by itself at night.")
d2 = z.item("Salt-Stiff Belt", 'belt', 14, 'finesse', "Cut from the ship's rigging.")
z.quest('gt_drowned_souls', 'The Drowned', 14, 'skald_hrafn',
        "A ship went down off the east shore last winter. Now its drowned walk the beach every night, looking for land they can't reach.\n\nWill you [give them rest]?",
        'give them rest',
        "The drowned of a wrecked ship walk Gotar's east shore every night.",
        [
            hunt((1060, 440), "Give the drowned souls rest " + where((1060, 440), 'skald_hrafn'), 'drowned soul', 5),
            end_talk('skald_hrafn', "Tell Old Skald Hrafn", "Rest, then. I'll make them a verse. Every drowned man deserves a verse.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [d1, d2]}})

d3 = z.item("Oarsman's Grip Bracer", 'bracer', 16, 'might', "Worn smooth by a dead man's rowing.")
d4 = z.item("Ship-Wreck Ring", 'ring', 16, 'ward', "Green bronze, from the ship's fittings.")
d5 = z.item("Scale-Cargo Pendant", 'neck', 16, 'mind', "A red scale, hot to the touch, on a ship's chain.")
z.quest('gt_drowned_ship', 'What the Ship Carried', 16, 'skald_hrafn',
        "The ship's oarsmen still row, out there on the wreck, though the ship goes nowhere. I want to know where she was going - and what she carried, that the sea wouldn't let her keep.\n\nBring friends. Will you [board the wreck]?",
        'board the wreck',
        "The skeletal crew of a wreck off Gotar's east shore still row; nobody knows what the ship was carrying.",
        [
            hunt((1057, 474), "Fight through the skeletal crew " + where((1057, 474), 'skald_hrafn'), 'skeletal oarsman', 3, r=40),
            hunt((1057, 474), "Bring down the skeletal seafarers", 'skeletal seafarer', 3, r=40),
            search(Z, P(1062, 470), "Search the wreck's hold", "a chest in the flooded hold", CRATE,
                   "The chest is full of dragon-scales - red, and warm, every one. A tally-stick in svartalf runes: 'For the Mother's priests in the north. Paid in gold at the Gotar post.'"),
            end_talk('skald_hrafn', "Tell Old Skald Hrafn", "Dragon-scale. Shipped north, to 'the Mother's priests'. There's only one dragon in Midgard old enough to be anyone's mother - Gjalpinulva, under Malmohus.\n\nRunecaster Runa at Nalliten will want to know. The staves have been saying 'fire in the south' for a month.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [d3, d4, d5]}}, requires='gt_drowned_souls', group=True)

# ======================================================================== The Scale-Traders (15-20)
s1 = z.item("Svartalf Outcast's Ring", 'ring', 15, 'finesse', "Black iron, filed thin.")
s2 = z.item("Trade-Road Cloak", 'cloak', 15, 'ward', "Road-dust grey, with deep pockets.")
z.quest('gt_outcasts', 'The Trade Road', 15, 'gt_runa',
        "The svartalf outcasts on the trade road used to sell iron. Now they sell scale - and they've started taking travellers, for 'the Mother'.\n\nWill you [clear the road]?",
        'clear the road',
        "Svartalf outcasts on Gotar's trade road sell dragon-scale and take travellers for 'the Mother'.",
        [
            hunt((600, 950), "Clear the svartalf outcasts from the trade road " + where((600, 950), 'gt_runa'), 'svartalf outcast', 6),
            end_talk('gt_runa', "Tell Runecaster Runa", "'The Mother.' The staves called her that too. The dragon's waking, and she's buying friends.", 'default'),
        ],
        {'default': {'text': "From the Nalliten Runecasters.", 'choice': [s1, s2]}}, requires='gt_drowned_ship')

s3 = z.item("Scale-Trader's Ledger Charm", 'gem', 17, 'mind', "A page of the ledger, folded small. The numbers are all in gold.")
s4 = z.item("Runecaster's Stave-Belt", 'belt', 17, 'faith', "A belt hung with little rune-staves.")
z.quest('gt_scale_guards', 'The Scale-Traders', 17, 'gt_runa',
        "The scale-traders camp beside the old svartalf post, under guard. Their ledger will tell us who's buying and who's selling.\n\nWill you [take the ledger]?",
        'take the ledger',
        "Svartalf scale-traders camp under guard beside the old svartalf post on Gotar's trade road.",
        [
            hunt((520, 760), "Break the scale-traders' guards " + where((520, 760), 'gt_runa'), 'svartalf guard', 2, r=40),
            search(Z, P(515, 755), "Search the scale-traders' camp", "a ledger in a scale-bound cover", CRATE,
                   "Every page: scale sold north, gold paid south. The buyers: 'the drakulv of Malmohus, by the Hierophant's word'. And at the end, in a different hand: 'Myrkwood. The old volva at Galplen knows the Mother's name. See to her.'"),
            end_talk('gt_runa', "Tell Runecaster Runa", "The Hierophant. The drakulv have a high priest now. And they're after a volva in Myrkwood - an old seer who knows the dragon's true name.\n\nThat's a name you don't let a cult take. Kill their preacher, then get word to Galplen.", 'default'),
        ],
        {'default': {'text': "From the Nalliten Runecasters.", 'choice': [s3, s4]}}, requires='gt_outcasts')

s5 = z.item("Preacher's Scale Torc", 'neck', 20, 'mind', "Dragon-scale on red cord. It's warm.")
s6 = z.item("Nalliten Rune-Ward Bracer", 'bracer', 20, 'faith', "Carved with Runa's ward-runes.")
s7 = z.item("Unburnt Mantle", 'cloak', 20, 'ward', "It doesn't scorch, even in the preacher's fire.")
z.quest('gt_preacher', 'The Dragon-Preacher', 20, 'gt_runa',
        "The dragon-preacher at the scale-traders' camp - he's the one who turned the outcasts. Without him, they're just traders again.\n\nBring friends. Will you [silence the preacher]?",
        'silence the preacher',
        "A dragon-preacher turned the svartalf outcasts of Gotar's trade road to the drakulv cult.",
        [
            hunt((520, 760), "Silence the dragon-preacher " + where((520, 760), 'gt_runa'), 'dragon-preacher', 1, r=40),
            end_talk('gt_runa', "Tell Runa", "Silenced. The camp will scatter. But the scale-caravans still run up the road - you'll see one, sooner or later. The Huscarls will want a hand when you do.", 'default'),
        ],
        {'default': {'text': "From the Nalliten Runecasters.", 'choice': [s5, s6, s7]}}, requires='gt_scale_guards', group=True)

# ======================================================================== The Spirit Hills (16-18)
h1 = z.item("Wind-Host Feather Charm", 'gem', 16, 'mind', "A grey feather that won't lie still.")
h2 = z.item("Earth-Host Stone Ring", 'ring', 16, 'ward', "A ring of plain stone, very heavy.")
z.quest('gt_hosts', 'The Restless Hosts', 16, 'eilif',
        "The hosts of the hills - wind and earth - have always been here. But they're restless. They're attacking anything that walks the hills.\n\nWill you [quiet them]?",
        'quiet them',
        "The hosts of wind and earth in Gotar's southern hills have grown restless.",
        [
            hunt((500, 1250), "Quiet the hosts of the wind " + where((500, 1250), 'eilif'), 'host of the wind', 4),
            hunt((600, 1350), "Quiet the hosts of the earth", 'host of the earth', 3),
            end_talk('eilif', "Tell Eilif", "Quieter. They're restless because the ground is warm. The ground's never warm, here.", 'default'),
        ],
        {'default': {'text': "From the Nalliten Runecasters.", 'choice': [h1, h2]}})

h3 = z.item("Pook-Trick Ring", 'ring', 17, 'charm', "It turns on your finger when you're not looking.")
h4 = z.item("Coast-Walker's Belt", 'belt', 17, 'finesse', "Crab-shell plates on sealskin.")
z.quest('gt_pooks', 'Pooks on the Coast', 17, 'flayer_kolr',
        "The perfidious pooks on the east coast have been luring travellers off the cliffs. Used to be pranks. Now they want blood.\n\nWill you [hunt them]?",
        'hunt them',
        "The perfidious pooks of Gotar's east coast lure travellers off the cliffs.",
        [
            hunt((1450, 850), "Hunt the perfidious pooks " + where((1450, 850), 'flayer_kolr'), 'perfidious pook', 5),
            end_talk('flayer_kolr', "Tell Flayer Kolr", "Good. Pooks I can skin. Dragons I can't.", 'default'),
        ],
        {'default': {'text': "From the Nalliten Runecasters.", 'choice': [h3, h4]}})

h5 = z.item("Carrion-Bane Bracer", 'bracer', 18, 'might', "Iron studs, for knocking carrion-eaters off.")
h6 = z.item("Warm-Earth Pendant", 'neck', 18, 'mind', "A stone from the vale. It's warm in your hand.")
z.quest('gt_carrion', 'The Warm Vale', 18, 'eilif',
        "Carrion eaters gather in the south-east vale. They're feeding on something that died there - big things, all burnt.\n\nWill you [go and look]?",
        'go and look',
        "Carrion eaters gather over something burnt in Gotar's south-east vale.",
        [
            hunt((1200, 1400), "Clear the carrion eaters " + where((1200, 1400), 'eilif'), 'carrion eater', 4),
            search(Z, P(1180, 1420), "Search the burnt ground", "a scorched elk carcass", CRATE,
                   "Elk and bear, all burnt from the inside, and the earth under them glassy. Small clawed tracks lead south, toward Myrkwood and Malmohus."),
            end_talk('eilif', "Tell Eilif", "Burnt from inside. Drakelings. They're coming up from the south. Hild at the seith circle will know more.", 'default'),
        ],
        {'default': {'text': "From the Nalliten Runecasters.", 'choice': [h5, h6]}}, requires='gt_hosts')

# ======================================================================== The Seith Circle (18-22)
c1 = z.item("Envy-Scale Ring", 'ring', 19, 'might', "A drakeling's scale, green-gold.")
c2 = z.item("Drake-Hunter's Mantle", 'cloak', 19, 'ward', "Scorched at the hem.")
z.quest('gt_drakelings', 'Envy Drakelings', 19, 'hild',
        "Envy drakelings on the southern edge. They covet everything - gold, fire, the light itself - and they eat what they can't take.\n\nWill you [drive them back]?",
        'drive them back',
        "Envy drakelings creep up Gotar's southern edge from Myrkwood and Malmohus.",
        [
            hunt((900, 1580), "Drive back the envy drakelings " + where((900, 1580), 'hild'), 'envy drakeling', 5),
            end_talk('hild', "Tell Hild", "Back. For now. The dragon's spawn don't come north on their own. Something called them.", 'default'),
        ],
        {'default': {'text': "From the Nalliten Runecasters.", 'choice': [c1, c2]}}, requires='gt_carrion')

c3 = z.item("Gotawitch's Bone Charm", 'gem', 21, 'mind', "Knucklebones on a thong. They click when trouble's coming.")
c4 = z.item("Seith-Breaker's Bracer", 'bracer', 21, 'faith', "Rowan and silver.")
c5 = z.item("Circle-Stone Ring", 'ring', 21, 'ward', "A ring cut from the circle's stone.")
z.quest('gt_gotawitches', 'The Turned Circle', 21, 'hild',
        "Half the seithkona at the circle have turned - they sing to the dragon now, with the gotawitches. They called the drakelings.\n\nBring friends. Will you [break the turned circle]?",
        'break the turned circle',
        "Half the seithkona at Gotar's seith circle have turned to singing for the dragon, with the gotawitches.",
        [
            hunt((990, 1420), "Break the gotawitches " + where((990, 1420), 'hild'), 'gotawitch', 3, r=40),
            hunt((990, 1420), "Break the turned seithkona", 'seithkona', 2, r=40),
            search(Z, P(995, 1425), "Search the circle's stone", "a seith-staff laid on the stone", LANTERN,
                   "The staff is carved with the dragon's long coils, and at the head, a name half-scraped away: GJALP- ... and then, 'the volva at Galplen keeps the rest'."),
            end_talk('hild', "Tell Hild", "They were trying to finish the name. To call her by it - a dragon called by her true name wakes all the way.\n\nThe volva in Myrkwood. Everyone wants her. Go to Galplen - and go carefully. Myrkwood isn't Gotar.", 'default'),
        ],
        {'default': {'text': "From the Nalliten Runecasters.", 'choice': [c3, c4, c5]}}, requires='gt_drakelings', group=True)
