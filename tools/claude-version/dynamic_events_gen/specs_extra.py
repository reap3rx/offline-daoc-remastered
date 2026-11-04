# One more event chain for every classic zone but the Valley of Bri Leith (owner 2026-11-04: "add 1 more event chain
# to each zone, and making sure there are at least one that's near the starting zones that are lower level"). The
# starting hubs (Cotswold, Mularn, Mag Mell) each get a giver who leads new characters out of town against the
# zone's weakest monsters. Same keys as specs.py; built into the existing zone files by gen_extra.py.
X = {}

# ---------------- Albion ----------------
X[0] = [dict(kind='giver', id='orchard_spriggarn', title='The Orchard Raiders', foes=['spriggarn', 'spriggarn elder'],
             boss=('Old Knotbark', 'spriggarn elder'), place='the spriggarn thicket', town='Cotswold',
             giver=('Guardsman Pell', 'Cotswold Watch',
                    "Spriggarn have been stripping the Cotswold orchards bare, and the farmers' children are afraid to go out. I could use a few new swords. Will you come? Tell me when you're [ready]."),
             why="Guardsman Pell leads a few of Cotswold's newest adventurers out against the spriggarn.")]
X[1] = [dict(kind='camp', id='basilisk_nest', title='The Basilisk Nest', foes=['pseudo basilisk', 'basilisk'],
             boss=('The Stone-Eyed Mother', 'aged basilisk'), place='the basilisk nest',
             hint='Grazing flocks have been found turned to stone...',
             why="Basilisks are nesting on the downs, and the shepherds keep finding their flocks frozen in stone. Break the nest.")]
X[2] = [dict(kind='camp', id='spider_hollow', title='The Spider Hollow', foes=['giant spider'],
             boss=('The Brood-Mother', 'giant spider'), place='the spider hollow',
             hint='The woods are strung thick with webs...',
             why="Giant spiders have strung the woods so thick a cart can't pass, and two woodcutters never came home. Burn out their hollow.")]
X[3] = [dict(kind='defend', id='warg_pack', title='The Warg Pack', foes=['gray warg', 'forest lion'],
             boss=('Greyfang', 'gray warg'), place="the wargs' lair",
             protect=('Shepherd Hywel', 'gathering his scattered flock'),
             hint='Wolves howl above the high pastures...',
             why="Greyfang's wargs have scattered Hywel's flock across the hills. He's going after his sheep - keep the pack off him.")]
X[4] = [dict(kind='camp', id='pounders', title='The Pounders of the Moor', foes=['granite giant outlooker', 'granite giant pounder'],
             boss=('Thunderfist', 'granite giant stonelord'), place="the giants' quarry",
             hint='The ground shakes with blows across the moor...',
             why="The granite giants have opened a quarry on the moor, and their pounding has brought down the old tor. Stop them before they take the rest.")]
X[6] = [dict(kind='defend', id='beech_wood', title='The Beech Wood Wakes', foes=['elder beech'],
             boss=('The Old Beech', 'aged beech'), place='the heart of the beech wood',
             protect=('Woodcutter Jory', 'marking the old trees for the mill'),
             hint='The beech wood creaks though there is no wind...',
             why="Woodcutter Jory has come to mark the old beeches for felling, and the beeches have noticed. Keep them off him.")]
X[7] = [dict(kind='camp', id='adder_shallows', title='The Adder Shallows', foes=['lake adder'],
             boss=('The Lake Wyrm', 'lake adder'), place='the adder shallows',
             hint='The shallows of the lake are boiling with snakes...',
             why="The lake adders have swarmed in the shallows, and no one can draw water or cross the ford. Clear them out.")]
X[8] = [dict(kind='camp', id='bloated_spiders', title='The Bloated Nest', foes=['bloated spider', 'large bloated spider'],
             boss=('The Bloated Queen', 'large bloated spider'), place='the bloated nest',
             hint='Webs as thick as sailcloth hang between the oaks...',
             why="A nest of bloated spiders has grown in the forest, fat on the deer - and lately on travellers. Burn it out.")]
X[9] = [dict(kind='camp', id='leapers_pool', title="The Leapers' Pool", foes=['water leaper', 'giant water leaper'],
             boss=('Grandfather Leaper', 'giant water leaper'), place="the leapers' pool",
             hint='Something drags the marsh-men under at the dark pool...',
             why="Water leapers have taken the dark pool in the marsh, and they pull down anyone who comes to fish it. End them.")]
X[10] = [dict(kind='defend', id='black_hound', title='The Black Hound of Lyonesse', foes=['gabriel hound', 'pygmy goblin'],
              boss=('The Black Hound', 'gabriel hound'), place="the hounds' den",
              protect=('Shepherd Elowen', 'driving her flock to the fold'),
              hint='Hounds bay across the drowned land at dusk...',
              why="The Gabriel hounds are hunting on the moor tonight, and Elowen is still out with her flock. Keep them off her.")]

# ---------------- Midgard ----------------
X[100] = [dict(kind='giver', id='hobgoblin_pranks', title='The Hobgoblin Pranksters', foes=['hobgoblin snake-finder', 'hobgoblin prankster'],
               boss=('Snaggletooth', 'hobgoblin prankster'), place="the hobgoblins' burrow", town='Mularn',
               giver=('Viking Gudrun', 'Mularn Watch',
                      "The hobgoblins have been stealing from every house in Mularn - and putting snakes in the beds. It's time they learned. I'm taking some of our new warriors out to their burrow. Coming? Tell me when you're [ready]."),
               why="Viking Gudrun leads Mularn's newest warriors out to the hobgoblins' burrow.")]
X[101] = [dict(kind='camp', id='army_ants', title='The Army Ant March', foes=['army ant worker', 'army ant soldier'],
               boss=('The Ant Queen', 'army ant soldier'), place='the ant hill',
               hint='The fields are moving with ants...',
               why="The army ants are on the march out of their hill and stripping the farms in their way. Destroy the hill.")]
X[102] = [dict(kind='defend', id='svartalf_cairn', title="The Svartalf Hunt", foes=['svartalf hunter', 'svartalf chanter'],
               boss=('Ulfhild the Svartalf', 'svartalf chanter'), place="the svartalf camp",
               protect=('Skald Bersi', 'singing the old wards over the cairn'),
               hint='Dark elves have been seen near the old cairn...',
               why="Skald Bersi is renewing the wards on the old cairn, and the svartalfar want what is buried there. Keep them off him.")]
X[103] = [dict(kind='camp', id='pine_imps', title='The Imp Revel', foes=['wood imp', 'pine imp'],
               boss=('Kvist the Imp-King', 'pine imp'), place="the imps' revel",
               hint='Shrill laughter and smoke come from the pines...',
               why="The imps are holding a revel in the pines and setting fire to anything that will burn. Break it up.")]
X[104] = [dict(kind='defend', id='fire_ants', title='The Fire Ant Swarm', foes=['fire ant gatherer', 'fire ant worker', 'fire ant scavenger'],
               boss=('The Ember Queen', 'fire ant gatherer'), place='the fire ant mound',
               protect=('Dverge Brokk', 'tapping a vein of fire-iron'),
               hint='The ash is crawling with fire ants...',
               why="Brokk the dverge has found a vein of fire-iron, right beside a fire ant mound. Keep the swarm off him until it's out.")]
X[105] = [dict(kind='camp', id='mora_riders', title='The Mora Riders', foes=['mora dancer', 'mora rider'],
               boss=('The Mora Mother', 'mora rider'), place="the mora's ring",
               hint='Riders are seen in the forest at night, and sleepers wake exhausted...',
               why="The mora are riding the sleepers of Myrkwood every night from their dancing ring. Break the ring.")]
X[106] = [dict(kind='camp', id='wolfaur_headsmen', title='The Wolfaur Headsmen', foes=['wolfaur headsman'],
               boss=('Grimjaw the Headsman', 'wolfaur headsman'), place="the headsmen's block",
               hint='Severed heads mark a path into the ravine...',
               why="The wolfaur headsmen have set up their block in the ravine and taken a hunting party's heads. End them.")]
X[107] = [dict(kind='camp', id='black_orms', title='The Black Orm Wallow', foes=['small black orm', 'black orm'],
               boss=('The Great Black Orm', 'black orm'), place='the orm wallow',
               hint='The swamp heaves where the black orms wallow...',
               why="The black orms have made a wallow on the causeway, and the causeway is sinking. Drive them out.")]
X[108] = [dict(kind='camp', id='frost_bears', title='The Frost-Bound Bears', foes=['frost bound bear', 'savage winterwolf'],
               boss=('Ironpelt', 'frost bound bear'), place='the frozen den',
               hint='Bears and winterwolves hunt together on the ice...',
               why="Ironpelt and the frost-bound bears hunt with the winterwolves now, and nothing on the ice is safe. Break their den.")]
X[116] = [dict(kind='camp', id='svartalf_foisters', title='The Svartalf Foisters', foes=['svartalf infiltrator', 'svartalf foister'],
               boss=('Bloodbinder Hrok', 'svartalf bloodbinder'), place="the foisters' hideout",
               hint='Svartalfar slip between the drakulv camps...',
               why="Svartalf foisters are selling Midgard's patrol routes to the drakulv. Take their hideout.")]

# ---------------- Hibernia ----------------
X[200] = [dict(kind='giver', id='barrow_bones', title='The Bones by Mag Mell', foes=['skeletal pawn', 'skeletal minion'],
               boss=('The Bone Steward', 'skeletal minion'), place='the old barrow', town='Mag Mell',
               giver=('Guardian Niamh', 'Mag Mell Guard',
                      "The old barrow outside Mag Mell has opened, and the dead have been walking the fields at night. I'll not ask farmers to face them. Will you come with me and put them back? Say when you're [ready]."),
               why="Guardian Niamh leads Mag Mell's newest adventurers out to the opened barrow.")]
X[201] = [dict(kind='defend', id='walking_rocks', title='The Walking Rocks', foes=['small walking rock', 'small walking boulder'],
               boss=('The Grinding Stone', 'walking rock'), place='the rockfall',
               protect=('Miner Fiach', 'clearing the blocked adit'),
               hint='Stones roll uphill in the lower passes...',
               why="Miner Fiach is digging out the blocked adit, and the rocks of the rockfall have got up to stop him. Keep them off.")]
X[202] = [dict(kind='camp', id='sandmen', title='The Sandmen of the Strand', foes=['sand crab', 'sandman'],
               boss=('The Tide-Turned', 'sandman'), place='the strand',
               hint='The sand of the strand is walking...',
               why="The sandmen have risen along the strand and drag fishermen into the dunes. Break them back into sand.")]
X[203] = [dict(kind='camp', id='koalinth_raid', title='The Koalinth Landing', foes=['koalinth slinker', 'tidal sheerie'],
               boss=('Koalinth Tidecaller', 'koalinth slinker'), place='the koalinth landing',
               hint='Strange boats have come ashore below the cliffs...',
               why="The koalinth have come ashore below the cliffs and are building a landing. Throw them back into the sea.")]
X[204] = [dict(kind='defend', id='gurite_ferry', title="The Ferryman's Crossing", foes=['gurite assailer', 'gurite waylayer'],
               boss=('Gurite Captain Orlagh', 'gurite seeker'), place='the gurite camp',
               protect=('Ferryman Colm', 'caulking his ferry'),
               hint='Gurites watch the ferry crossing...',
               why="Ferryman Colm's boat is the only way across, and the gurites mean to sink it. Keep them off him while he patches it.")]
X[205] = [dict(kind='camp', id='siabra_raiders', title='The Siabra Raiders', foes=['siabra raider', 'siabra mireguard'],
               boss=('The Mirelord', 'siabra venator'), place="the raiders' camp",
               hint='Siabra raiders have dug in on the bog road...',
               why="Siabra raiders have made a camp on the bog road and rob every traveller between Siopa and Alainn Bin. Clear it.")]
X[207] = [dict(kind='camp', id='anger_sprites', title='The Wrathful Sprites', foes=['anger sprite', 'lunantishee'],
               boss=('The Wrathful One', 'anger sprite'), place="the sprites' blackthorn",
               hint='Shrieks of rage come from a blackthorn thicket...',
               why="Anger sprites have woken the lunantishee in the blackthorn, and nothing that walks near it comes back sane. Cut it down.")]
X[208] = [dict(kind='camp', id='cave_bears', title='The Unearthed', foes=['unearthed cave bear'],
               boss=('The Unearthed Sow', 'unearthed cave bear'), place='the open cave',
               hint='Something huge has dug its way up out of the earth...',
               why="The cave bears dug up from under the cursed forest have made a den in the open, and they are hungry. Kill them.")]
X[216] = [dict(kind='defend', id='hill_beacon', title='The Hill Beacon', foes=['glimmer striker', 'glimmer griever'],
               boss=('The Glimmer Warlord', 'glimmer warshade'), place='the glimmer camp',
               protect=('Druid Saoirse', 'relighting the hill beacon'),
               hint='The beacon on the hill has gone dark...',
               why="Druid Saoirse is relighting the beacon the glimmer put out, and they are coming back for it. Keep them off her.")]
