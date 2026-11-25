"""West Svealand's story quests (claude 2026-11-24, "Midgard - the plan", round 2) - see story_gen.py and albion_story.py.
Places: zone metres [x, y].  python tools/claude-version/story_gen.py story_west_svealand

Wild, Dangerous in the west. The west thread: the Blodfelag, the blood-fellowship, swear blood-oaths to the Fenris-wolf's
children. Their thralls lose their minds, their windcallers bring snow down in summer, their haxa read Raumarik's frost in bowls of
blood, and their Blood-Hall in the west is the zone's siege (for the Huginfel Shieldwall). In the south-west a gully has frozen
over and will not thaw. The south thread brushes the svartalf hunters of the southern road, who carry drakulv passes.

The zone's two older quests are kept as they were (oathbreaker, wolf_cord).

Arcs (recommended levels): The Thrall Road (10-13), The Skogsfru Wood (12-15), The Frozen Gully (15-18), The Blodfelag (14-20),
The Svartalf Road (14-16).
"""
from story_gen import talk, reach, search, boss, defend, choice, end_talk, L
from albion_story import Story, CRATE, BEDROLL, LANTERN

S = Story(102, 'West Svealand', 'mid_west_svealand', 'story102_west_svealand', {'oathbreaker', 'wolf_cord'},
          {'asvor', 'halvdan_scout', 'eyvind', 'gothi_valbrand', 'huscarl_grettir', 'kolbein'},
          {"Eyvind's Cut Arm-Ring", "Oathbreaker's Cloak", 'Huginfel Hearth-Ring', 'Blood-Fellowship Torc', "Haxa's Binding-Cord",
           'Wolf-Brother Pelt', "Shield-Mate's Ring", 'Gothi Rune-Belt'}, realm=2)
z, P, person, where, hunt, Z = S.z, S.P, S.person, S.where, S.hunt, S.Z
ZONES = [z]
M, F, OLD = 213, 168, 157

person('ws_sigvaldi', 'Shield-Captain Sigvaldi', (1392, 1150), 'm', 34, model=M, guild='the Huginfel Shieldwall',
       idle="The Shieldwall holds Huginfel. Lately it holds it facing west.")
person('ws_ragnfrid', 'Ragnfrid Wolf-Widow', (150, 700), 'f', 30, model=F, guild='the Huginfel Shieldwall',
       idle="The last farm before the Blodfelag's country. My husband said we'd never leave it. He was right, in his way.")

# ======================================================================== The Thrall Road (10-13)
t1 = z.item("Thrall-Chain Bracer", 'bracer', 10, 'ward', "A broken shackle, padded and worn on the arm.")
t2 = z.item("Huginfel Gate Ring", 'ring', 10, 'might', "Iron, stamped with Huginfel's gate.")
z.quest('ws_thralls', 'Mindless', 10, 'ws_sigvaldi',
        "The Blodfelag take thralls from the farms - and something takes their minds. They wander the road east of here, empty, and attack anything that moves.\n\nThey were our neighbours. Will you [give them rest]?",
        'give them rest',
        "The Blodfelag's mindless thralls wander West Svealand's eastern road, attacking anything that moves.",
        [
            hunt((1300, 700), "Give the mindless thralls rest " + where((1300, 700), 'ws_sigvaldi'), 'mindless thrall', 5),
            end_talk('ws_sigvaldi', "Tell Shield-Captain Sigvaldi", "Rest. That's what we can give them now. I hate it.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [t1, t2]}})

t3 = z.item("Oath-Cut Belt", 'belt', 11, 'finesse', "A belt cut from an oathbreaker's own. He won't need it.")
t4 = z.item("Shieldwall Shoulder-Cloak", 'cloak', 11, 'ward', "Huginfel red, with the shieldwall's boss.")
z.quest('ws_oathbreakers', 'The Oathbreakers', 11, 'ws_sigvaldi',
        "The Blodfelag oathbreakers - men who broke their oaths to their jarls and swore new ones in blood - camp west of town and raid the thrall road.\n\nWill you [break their camp]?",
        'break their camp',
        "Blodfelag oathbreakers camp west of Huginfel and raid the thrall road.",
        [
            hunt((1250, 941), "Break the oathbreakers' camp " + where((1250, 941), 'ws_sigvaldi'), 'blodfelag oathbreaker', 6),
            end_talk('ws_sigvaldi', "Tell Sigvaldi", "Broken. They'll go west, to their own country. Everything goes west now.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [t3, t4]}}, requires='ws_thralls')

t5 = z.item("Blood-Oath Scroll Charm", 'gem', 13, 'mind', "A strip of the oath-scroll, the blood gone brown.")
t6 = z.item("Henchman-Breaker's Ring", 'ring', 13, 'might', "Heavy iron. Sigvaldi's gift.")
z.quest('ws_henchmen', 'The Blood-Oath', 13, 'ws_sigvaldi',
        "The henchmen carry the Blodfelag's oaths written out - who swore, and to what. Bring me one. I want to know what my neighbours were sold to.\n\nWill you [take an oath-scroll]?",
        'take an oath-scroll',
        "Blodfelag henchmen carry written blood-oaths along West Svealand's thrall road.",
        [
            hunt((1350, 920), "Kill the blodfelag henchmen " + where((1350, 920), 'ws_sigvaldi'), 'blodfelag henchman', 4),
            search(Z, P(1250, 960), "Search the oathbreakers' camp for an oath-scroll", "a scroll in a wolf-skin case", BEDROLL,
                   "The oath, in blood: 'I give my blood to the Wolf's children. When the long winter comes, I will run with them. When the Wolf breaks his chain, I will hold the door open.'",
                   give="a blood-oath scroll"),
            end_talk('ws_sigvaldi', "Bring the scroll to Sigvaldi", "'When the Wolf breaks his chain.' Fenrir. They're swearing to Fenrir's children - to the end of the world.\n\nHuscarl Grettir at Vindsaul Faste needs to see this. And the gothi.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [t5, t6]}}, requires='ws_oathbreakers')

# ======================================================================== The Skogsfru Wood (12-15)
s1 = z.item("Wind-Sprite Feather", 'gem', 12, 'finesse', "It drifts upward if you let it go.")
s2 = z.item("Gothi's Ward-Cord", 'belt', 12, 'faith', "Nine knots, nine runes.")
z.quest('ws_wind_sprites', 'An Ill Wind', 12, 'gothi_valbrand',
        "The wind sprites of the middle wood have always been playful - a hat blown off, a fire blown out. Now they blow cold. Ice on the barley in summer.\n\nWill you [calm them]?",
        'calm them',
        "The wind sprites of West Svealand's middle wood have begun blowing cold in summer.",
        [
            hunt((900, 700), "Calm the wind sprites " + where((900, 700), 'gothi_valbrand'), 'wind sprite', 6),
            end_talk('gothi_valbrand', "Tell Gothi Valbrand", "Calmer. But they're not making the cold, only carrying it. It comes from the west.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [s1, s2]}})

s3 = z.item("She-Wolf Fang Torc", 'neck', 14, 'might', "A she-wolf's fangs on a twist of iron.")
s4 = z.item("Woodland Stalker's Bracer", 'bracer', 14, 'finesse', "Soft leather, for silent walking.")
z.quest('ws_she_wolves', 'The She-Wolves', 14, 'huscarl_grettir',
        "Bloodthirsty she-wolves in the middle wood, killing for the pleasure of it. Wolves don't do that. Not ordinary wolves.\n\nWill you [hunt them]?",
        'hunt them',
        "Bloodthirsty she-wolves kill for pleasure in West Svealand's middle wood.",
        [
            hunt((950, 600), "Hunt the bloodthirsty she-wolves " + where((950, 600), 'huscarl_grettir'), 'bloodthirsty she-wolf', 4),
            end_talk('huscarl_grettir', "Tell Huscarl Grettir", "Not ordinary wolves. The Blodfelag feed them. On what, I don't want to know.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [s3, s4]}})

s5 = z.item("Wood-Wife's Leaf Ring", 'ring', 15, 'charm', "A ring of living leaf. It stays green.")
s6 = z.item("Skogsfru Bark Mantle", 'cloak', 15, 'ward', "Birch-bark, soft as cloth.")
z.quest('ws_skogsfru', 'The Wood-Wives', 15, 'gothi_valbrand',
        "The skogsfru - the wood-wives, lovely from the front and hollow as a dead tree behind - have left their groves and come out onto the roads. They lure travellers in and nobody comes out.\n\nThey're fleeing something too. Will you [drive them back]?",
        'drive them back',
        "The skogsfru, the hollow-backed wood-wives, have come out of their groves onto West Svealand's roads.",
        [
            hunt((650, 300), "Drive the skogsfru back into their grove " + where((650, 300), 'gothi_valbrand'), 'skogsfru', 4),
            end_talk('gothi_valbrand', "Tell Gothi Valbrand", "One of them spoke as she died. 'The winter comes through the trees.' Even the wood-wives are afraid.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [s5, s6]}}, requires='ws_wind_sprites')

# ======================================================================== The Frozen Gully (15-18)
f1 = z.item("Never-Thaw Ice Charm", 'gem', 15, 'mind', "A chip of the gully's ice in a silver cage. It hasn't melted.")
f2 = z.item("Wolf-Widow's Shawl", 'cloak', 15, 'ward', "Ragnfrid's own, grey and heavy.")
z.quest('ws_frozen_gully', 'The Frozen Gully', 15, 'ws_ragnfrid',
        "There's a gully in the south-west where my husband watered the sheep. It froze over in midsummer, and it hasn't thawed. He went to look. He didn't come back.\n\nWill you [go and look]? Carefully.",
        'go and look',
        "A gully in West Svealand's south-west froze over in midsummer and hasn't thawed.",
        [
            reach(Z, P(380, 1460), "Go to the frozen gully in the south-west", "Snow on the ground in summer. Your breath smokes. The light down in the gully moves like something alive.", r=25),
            search(Z, P(360, 1480), "Search the gully's edge", "a shepherd's crook, frozen into the ice", CRATE,
                   "Ragnfrid's husband's crook, and under the clear ice, his face - peaceful, as if asleep. The ice isn't water. It's colder than water can be."),
            end_talk('ws_ragnfrid', "Tell Ragnfrid", "So that's where he is. Thank you. I'd rather know.\n\nIt's spreading. Every week it's a little further up the hill. Something in there is making winter.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [f1, f2]}})

f3 = z.item("Cold-Light Lantern Charm", 'gem', 17, 'mind', "A tiny lantern. It glows blue and gives no heat.")
f4 = z.item("Frost-Ward Bracer", 'bracer', 17, 'ward', "Fur-lined iron.")
z.quest('ws_cold_lights', 'Cold Lights', 17, 'ws_ragnfrid',
        "The lights in the gully - cold lights, the old folk called them - lead men down onto the ice. Like they led him.\n\nWill you [put them out]?",
        'put them out',
        "Cold lights lead men down onto the never-thawing ice of the frozen gully.",
        [
            hunt((330, 1500), "Put out the cold lights " + where((330, 1500), 'ws_ragnfrid'), 'cold light', 3),
            end_talk('ws_ragnfrid', "Tell Ragnfrid", "Out. For now. There are other things down there - small white things, and a colt made of frost.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [f3, f4]}}, requires='ws_frozen_gully')

f5 = z.item("Frost-Colt Mane Torc", 'neck', 18, 'might', "Braided white hair that crackles like frost.")
f6 = z.item("Snow-Imp's Cap Charm", 'gem', 18, 'charm', "A little white cap. It's always cold inside.")
f7 = z.item("Gully-Walker's Mantle", 'cloak', 18, 'ward', "Fur and wool, for walking on ice that isn't ice.")
z.quest('ws_snow_imps', 'The Things in the Snow', 18, 'ws_ragnfrid',
        "Snow imps and frost colts. Things out of the far north - out of Raumarik, where my grandmother said the winter never ends. They're here. In summer.\n\nIt's a job for a few. Will you [clear the gully]?",
        'clear the gully',
        "Snow imps and frost colts out of the far north have made the frozen gully their den.",
        [
            hunt((340, 1490), "Clear the snow imps from the gully " + where((340, 1490), 'ws_ragnfrid'), 'snow imp', 4),
            hunt((320, 1520), "Bring down the frosty colts " + where((320, 1520), 'ws_ragnfrid'), 'frosty colt', 3),
            end_talk('ws_ragnfrid', "Tell Ragnfrid", "Raumarik things, in my husband's gully. The Blodfelag's windcallers pray to the north every night. I think it listens.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [f5, f6, f7]}}, requires='ws_cold_lights', group=True)

# ======================================================================== The Blodfelag (14-20)
b1 = z.item("Warhound-Collar Torc", 'neck', 14, 'might', "Spiked, and too heavy for anything but a Blodfelag hound.")
b2 = z.item("Wolf-Widow's Ring", 'ring', 14, 'faith', "Ragnfrid's husband's ring. She wants you to have it.")
z.quest('ws_warhounds', 'The Warhounds', 14, 'ws_ragnfrid',
        "The Blodfelag's warhounds come round my farm every night now, testing the fence. One night the fence won't hold.\n\nWill you [kill the hounds]?",
        'kill the hounds',
        "The Blodfelag's warhounds test the fences of the last farm before their country.",
        [
            hunt((500, 950), "Kill the blodfelag warhounds " + where((500, 950), 'ws_ragnfrid'), 'blodfelag warhound', 5),
            end_talk('ws_ragnfrid', "Tell Ragnfrid", "Quiet nights, for a while. Thank you.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [b1, b2]}})

b3 = z.item("Windcaller's Bone Whistle", 'gem', 17, 'mind', "Blow it and the air goes cold. Don't.")
b4 = z.item("Snow-Ward Belt", 'belt', 17, 'ward', "Thick wool, rune-stitched against the cold.")
z.quest('ws_windcallers', 'The Windcallers', 17, 'huscarl_grettir',
        "The Blodfelag's windcallers stand on the hills by their hall and sing to the north wind. And it comes. Snow in the barley, ice on the wells.\n\nWill you [silence them]?",
        'silence them',
        "The Blodfelag's windcallers sing the north wind down onto West Svealand's summer fields.",
        [
            hunt((440, 780), "Silence the blodfelag windcallers " + where((440, 780), 'huscarl_grettir'), 'blodfelag windcaller', 4),
            end_talk('huscarl_grettir', "Tell Huscarl Grettir", "Silenced. And the wind dropped as they fell - Valbrand felt it from here.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [b3, b4]}}, requires='ws_warhounds')

b5 = z.item("Wolfwarrior's Pelt-Mantle", 'cloak', 19, 'might', "A whole wolf-pelt, jaws for a hood.")
b6 = z.item("Berserk-Breaker's Ring", 'ring', 19, 'ward', "Grettir's gift: plain iron, very heavy.")
b7 = z.item("Blood-Hall Spear Torc", 'neck', 19, 'finesse', "Iron, with a broken spear-head hung from it.")
z.quest('ws_wolfwarriors', 'Wolf-Warriors', 19, 'huscarl_grettir',
        "The wolfwarriors - Blodfelag berserkers who wear the wolf - camp in the north-west, by the haxa's circle. They're the ones who'll lead when the Blodfelag march.\n\nBring friends. Will you [break the wolfwarriors]?",
        'break the wolfwarriors',
        "Blodfelag wolfwarriors, berserkers who wear the wolf, camp in West Svealand's north-west.",
        [
            hunt((400, 380), "Break the blodfelag wolfwarriors " + where((400, 380), 'huscarl_grettir'), 'blodfelag wolfwarrior', 4),
            end_talk('huscarl_grettir', "Tell Grettir", "Good. Now the haxa - the blood-witches who read for them. That's where their orders come from.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [b5, b6, b7]}}, requires='ws_windcallers', group=True)

b8 = z.item("Frozen Blood-Bowl Charm", 'gem', 20, 'mind', "A shard of the haxa's bowl, the blood in it still frozen.")
b9 = z.item("Haxa-Bane Bracer", 'bracer', 20, 'faith', "Rowan wood and iron.")
b10 = z.item("Vindsaul Huscarl Mantle", 'cloak', 20, 'ward', "The King's blue, from the frontier keep.")
z.quest('ws_haxa', 'The Haxa', 20, 'gothi_valbrand',
        "The haxa - the Blodfelag's blood-witches - keep a circle in the north-west. They read the future in bowls of blood, and the Blodfelag do what they say.\n\nBring friends. Will you [break the circle]? And bring me what they read.",
        'break the circle',
        "The Blodfelag's haxa read the future in bowls of blood in a circle in West Svealand's north-west.",
        [
            hunt((320, 330), "Break the blodfelag haxa " + where((320, 330), 'gothi_valbrand'), 'blodfelag haxa', 3, r=40),
            search(Z, P(325, 340), "Search the haxa's circle", "a bowl of blood, frozen solid", CRATE,
                   "The blood in the bowl froze in a pattern - a wolf's head, jaws open over a moon. Scratched into the bowl's rim: 'RAUMARIK. THE HOST GATHERS. HATI HUNTS THE MOON.'"),
            end_talk('gothi_valbrand', "Tell Gothi Valbrand", "Hati. The wolf that hunts the moon - Fenrir's own son. When he catches it, the long winter begins.\n\nAnd his host gathers in Raumarik. The Blodfelag are only the first of them. Go and see Sigvaldi; the Shieldwall means to take the Blood-Hall.", 'default'),
        ],
        {'default': {'text': "From King Eirik's Huscarls.", 'choice': [b8, b9, b10]}}, requires='ws_wolfwarriors', group=True)

b11 = z.item("Shieldwall Oath-Ring", 'ring', 20, 'might', "The Shieldwall's oath ring: an oath you keep.")
b12 = z.item("Blood-Hall Scout's Belt", 'belt', 20, 'finesse', "Dark leather, for creeping close.")
z.quest('ws_blood_hall', 'The Blood-Hall', 20, 'ws_sigvaldi',
        "The Blodfelag's Blood-Hall, in the west. Every thrall they've taken went through its doors. The Shieldwall means to take it.\n\nGo and [scout the hall]. Count them. Then come back and tell me we can win.",
        'scout the hall',
        "The Huginfel Shieldwall means to take the Blodfelag's Blood-Hall in West Svealand's west.",
        [
            reach(Z, P(520, 760), "Climb the ridge above the Blood-Hall", "A long hall roofed with turf, a wolf's skull over the door, and snow on the roof in summer. The windcallers' song comes up from inside.", r=25),
            search(Z, P(500, 780), "Look over the Blood-Hall's yard", "a post hung with chains", CRATE,
                   "Thralls' chains, dozens of them, and fresh blood frozen on the post. Warhounds in the yard, and a warden in black mail at the door."),
            end_talk('ws_sigvaldi', "Tell Sigvaldi", "Dozens. Then we take it back for every one of them.\n\nThe Shieldwall will march when the farms are behind us - every Blodfelag broken, every thrall freed, tells the men they can win. Be there.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [b11, b12]}}, requires='ws_henchmen')

# ======================================================================== The Svartalf Road (14-16)
r1 = z.item("Svartalf Hunter's Ring", 'ring', 14, 'finesse', "Dark iron, dwarf-work gone wrong.")
r2 = z.item("Southern Road Cloak", 'cloak', 14, 'ward', "Dust-brown, for long roads.")
z.quest('ws_svartalf_hunters', 'The Southern Road', 14, 'eyvind',
        "Svartalf hunters on the southern road. They used to trade - furs for iron, honest enough. Now they hunt travellers and say the dragon will pay them in gold.\n\nWill you [clear the road]?",
        'clear the road',
        "Svartalf hunters on West Svealand's southern road hunt travellers for the dragon's gold.",
        [
            hunt((900, 1450), "Clear the svartalf hunters " + where((900, 1450), 'eyvind'), 'svartalf hunter', 5),
            end_talk('eyvind', "Tell Eyvind", "'The dragon will pay.' Which dragon? Midgard's only got one that wants paying.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [r1, r2]}})

r3 = z.item("Chanter's Scale-Pin", 'gem', 16, 'mind', "A red scale pinned like a brooch.")
r4 = z.item("Drakulv-Pass Belt", 'belt', 16, 'finesse', "The pass's leather case, made into a belt.")
z.quest('ws_svartalf_chanters', 'The Chanters', 16, 'eyvind',
        "The svartalf chanters camp on the southern road and sing the hunters on. Break them, and see what they're carrying.\n\nWill you [break the camp]?",
        'break the camp',
        "Svartalf chanters camp on West Svealand's southern road and sing their hunters on.",
        [
            hunt((1015, 1390), "Break the svartalf chanters " + where((1015, 1390), 'eyvind'), 'svartalf chanter', 3),
            search(Z, P(1020, 1395), "Search the chanters' camp", "a leather case under a bedroll", BEDROLL,
                   "A drakulv pass, stamped with a dragon's eye, good for 'the svartalf traders of Gotar and all who carry the Mother's word'."),
            end_talk('eyvind', "Tell Eyvind", "Gotar. The svartalf trading post in Gotar - that's where the dragon's road runs north from.", 'default'),
        ],
        {'default': {'text': "From the Huginfel Shieldwall.", 'choice': [r3, r4]}}, requires='ws_svartalf_hunters')
