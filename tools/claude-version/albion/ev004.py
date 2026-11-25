"""Dartmoor's dynamic events (claude 2026-11-24, "Albion - the plan", round 4): the three old chains kept and brought up to the
zone's Elite levels, a new one - the Dragon's Breath (Golestandt breathes out under the south road and the moor burns) - and the
Dragon-Watch's campaign: the four valleys' assaults and counters and the raid on the Giants' Throne (Cormoran of the Mount, for two
or three groups), armed by AlbionCampaign.cs. Won, Golestandt's lair opens. Writes the zone's events file."""
import json, sys
from evcommon import mkP, R, mob, shift_levels, random_chain
from evcamp import giver, assault, cull, wards, hold, boss_stage, counter, around
Z = 4
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Dartmoor, Golestandt's moor. The white dragon that fled Vortigern's tower is awake in his lair in the south, and every "
             "giant of the moor marches to his tune: the Stonecrush dig his road north, the stonecallers sing in their ring, and the "
             "stonelords are cutting a crown for Cormoran of the Mount, to sit him on Gogmagog's empty throne. Sir Constantine's "
             "Dragon-Watch means to stop them.")
SHIFT = {"dartmoor_herdsmen_cairn": ([50, 57], 11), "dartmoor_stonecallers": ([50, 57], 5)}
for c in d['chains']:
    if c['id'] in SHIFT:
        lv, sh = SHIFT[c['id']]
        shift_levels(c, lv, sh)

LOOK = {"template": 60167630, "model": 28, "equipment": "38762ab0-5f99-47cd-85b0-0bfaa37d71f9", "guild": "the Dragon-Watch"}
OATH = {"template": 60167630, "model": 32, "equipment": "eab1762c-33e7-4620-9e02-985d820d0369", "guild": "the Quarry-Oath of Grimspound"}
EXC = mob(770008, "Stonecrush excavator", (50, 52), guild="the Stonecrush")
GRI = mob(770016, "Stonecrush rockgrinder", (51, 53), guild="the Stonecrush")
DEM = mob(770015, "Stonecrush demolisher", (52, 54), guild="the Stonecrush")
GIANT = mob(770007, "granite giant", (50, 52), guild="Golestandt's giants")
HERD = mob(770003, "granite giant herdsman", (51, 53), guild="Golestandt's giants")
GATH = mob(770005, "granite giant gatherer", (51, 53), guild="Golestandt's giants")
CALL = mob(770006, "granite giant stonecaller", (52, 54), guild="Golestandt's giants")
SHAPE = mob(770014, "granite giant stoneshaper", (52, 54), guild="Golestandt's giants")
OUT_ = mob(770011, "granite giant outlooker", (53, 55), guild="Golestandt's giants")
POUND = mob(770002, "granite giant pounder", (54, 56), guild="Golestandt's giants")
LORD = mob(770001, "granite giant stonelord", (55, 57), guild="Golestandt's giants")
KNOCK = mob(13072, "granite knocker", (52, 54))

# ---------------------------------------------------------------- the Dragon's Breath: the moor burns along the south road
ROAD = P(880, 1180)
d['chains'].append(random_chain('dm_dragons_breath', "The Dragon's Breath", [52, 56],
    "Smoke out of the ground along the south road - Golestandt is breathing out in his sleep, and the moor is burning...", 'b1', [
    {"id": "b1", "type": "defend", "name": "The Burning Road", "objective": "Keep Quarry-Warden Tamsin alive while she stops the vents",
     "announce": "Golestandt breathed out under the south road, and the moor is on fire! Quarry-Warden Tamsin is stopping the vents with Grimspound stone - and the giants are coming to keep them open!",
     "center": ROAD, "radius": 70, "duration_s": 200, "protect": dict(OATH, name="Quarry-Warden Tamsin", level=54, pos=ROAD, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": around(P, (880, 1180)), "mobs": [OUT_, POUND, KNOCK]},
     "thanks": "\"Stopped. Every one. He'll have to breathe somewhere else.\"",
     "success": "The last vent is stopped - and the giant who was feeding them comes down off the ridge.",
     "fail": "Tamsin falls, and the road burns till dawn.", "on_success": "b2", "on_fail": "end", "reward": R(14, 180, 12)},
    {"id": "b2", "type": "boss", "name": "Ember-Keeper Gurt", "objective": "Defeat Ember-Keeper Gurt",
     "announce": "A giant with a back full of smouldering coals: 'The dragon's breath is holy. You put it OUT?' Bring friends.",
     "center": ROAD, "radius": 70, "time_s": 1200,
     "boss": {"template": 770002, "name": "Ember-Keeper Gurt", "level": 57, "size": 70, "pos": ROAD, "health_mult": 4,
              "guild": "Keeper of the Dragon's Breath"},
     "adds": {"every_s": 40, "count": 2, "mobs": [POUND, OUT_]},
     "success": "Gurt goes down, and the coals on his back go out one by one.", "fail": "Gurt relights the vents.",
     "on_success": "end", "on_fail": "end", "reward": R(28, 300, 20, ["nu004_ember_keeper_s_coal"], 40)},
    ]))

# ---------------------------------------------------------------- the Dragon-Watch's campaign
CP = {1: P(230, 720), 2: P(960, 380), 3: P(760, 800), 4: P(1060, 1180)}
SEAT = P(1240, 1420)
LV = {1: [50, 53], 2: [51, 54], 3: [52, 55], 4: [53, 56]}
WATCH = [dict(LOOK, name="dragonslayer of the Watch", level=53, count=3)]
PREFIX = "dm_cp"
d['chains'].append(assault(PREFIX, 1, "The Dragon-Watch at the Stonecrush Diggings", LV[1], 6,
    "The Banner-Warden is forming the Dragon-Watch up for the Stonecrush Diggings.",
    giver(LOOK, "Banner-Warden Eluned", 55, P(180, 480),
          "The Stonecrush Diggings - the dragon's road, in the west valley. Six at least, and say [forward].",
          "forward", "Down to the diggings! Break the Stonecrush - then their boss!",
          "The Dragon-Watch holds the diggings - and the next thirty minutes are ours.", "Back to Grimspound! We'll go again."), WATCH, [
    cull("Break the Diggings", "Break the Stonecrush at the diggings", "The Dragon-Watch is at the diggings! Break the Stonecrush!",
         CP[1], [EXC, GRI, CALL], 24, "s2"),
    boss_stage("s2", "Dig-Boss Krag", "Dig-Boss Krag, a Stonecrush the size of a cottage: 'The road goes north. Through you, if it has to.'",
               CP[1], {"template": 770015, "name": "Dig-Boss Krag", "level": 56, "size": 70, "health_mult": 4, "guild": "of the Stonecrush"},
               [EXC, GRI], "Krag falls into his own trench. The dragon's road stops here.")], bot_min=50))
d['chains'].append(assault(PREFIX, 2, "The Dragon-Watch on the Pony Moor", LV[2], 6,
    "Sir Garrod is forming the Dragon-Watch up for the Pony Moor.",
    giver(LOOK, "Sir Garrod", 56, P(700, 330),
          "The Pony Moor. The herdsmen hold it, and they've built cairns to the dragon on every rise. Six at least, and say [forward].",
          "forward", "Up onto the moor! Stand on the three cairns while we pull them down - then the herd-master!",
          "The Dragon-Watch holds the Pony Moor.", "Back down! We'll go again."), WATCH, [
    cull("Break the Pony Moor", "Break the giants on the Pony Moor", "The Dragon-Watch is on the Pony Moor! Break the herdsmen!",
         CP[2], [GIANT, HERD, CALL], 26, "s2"),
    wards("s2", "The Dragon-Cairns", "Hold the three dragon-cairns at once while the Watch pulls them down",
          "Three dragon-cairns on the moor's rises sing to Golestandt - stand on all three at once while the Watch pulls them down!",
          CP[2], [P(920, 350), P(1000, 360), P(960, 420)], ["the north cairn", "the east cairn", "the south cairn"], [GIANT, HERD], "s3",
          "pennant of the Watch"),
    boss_stage("s3", "Herd-Master Bodrugan", "Herd-Master Bodrugan, with a pony under each arm: 'The moor is the dragon's. So is everything on it.'",
               CP[2], {"template": 770003, "name": "Herd-Master Bodrugan", "level": 57, "size": 72, "health_mult": 4.5, "guild": "of Golestandt's giants"},
               [HERD, GIANT], "Bodrugan falls, and the ponies scatter, free.")], bot_min=50))
d['chains'].append(assault(PREFIX, 3, "The Dragon-Watch at the Stonecallers' Ring", LV[3], 6,
    "Dame Ysolt is forming the Dragon-Watch up for the Stonecallers' Ring.",
    giver(LOOK, "Dame Ysolt", 56, P(600, 640),
          "The Stonecallers' Ring. We take it, and Quarry-Mother Hedda's people put the quarry-oath back on the speaking-stone - and the giants will come for her. Six at least, and say [forward].",
          "forward", "Into the ring! Break the callers - then keep Hedda's people alive!", "The Dragon-Watch holds the ring.",
          "Out of the ring! We'll go again."), WATCH, [
    cull("Break the Ring", "Break the stonecallers' ring", "The Dragon-Watch is at the ring! Break the stonecallers!",
         CP[3], [CALL, GATH, SHAPE], 26, "s2"),
    hold("s2", "The Oath-Stone", "Keep Oath-Cutter Peran alive while he cuts the oath back into the speaking-stone",
         "Oath-Cutter Peran is cutting the quarry-oath back into the speaking-stone - and the giants are coming to stop him!",
         CP[3], dict(OATH, name="Oath-Cutter Peran", level=54, health_mult=8), around(P, (760, 800)), [GATH, SHAPE, CALL], "s3",
         "\"It's cut. The stone remembers. Whether the giants do...\""),
    boss_stage("s3", "Song-Mother Ysgawen", "Song-Mother Ysgawen, the oldest stonecaller, singing so the stones shake: 'The stone remembers? Then I'll make it forget.'",
               CP[3], {"template": 770006, "name": "Song-Mother Ysgawen", "level": 58, "size": 72, "health_mult": 4.5, "guild": "of Golestandt's giants"},
               [CALL, SHAPE], "Ysgawen's song breaks in the middle of a word. The ring is silent.")], bot_min=50))
d['chains'].append(assault(PREFIX, 4, "The Dragon-Watch on the Pounders' Road", LV[4], 8,
    "Sir Constantine's own squire is forming the Dragon-Watch up for the Pounders' Road.",
    giver(LOOK, "Squire Kenwyn", 55, P(880, 1000),
          "The Pounders' Road - the south road, to the throne and the lair. The knockers have dug traps under it. Eight at least, and say [forward].",
          "forward", "Down the road! Stand on the knockers' shafts while we cave them in - then the pound-master!",
          "The Dragon-Watch holds the Pounders' Road - the throne is in sight.", "Back up the road! We'll go again."), WATCH, [
    cull("Break the Pounders' Road", "Break the giants on the south road", "The Dragon-Watch is on the Pounders' Road! Break the pounders!",
         CP[4], [OUT_, POUND, KNOCK], 28, "s2"),
    wards("s2", "The Knockers' Shafts", "Stand on the three knockers' shafts at once while the Watch caves them in",
          "Three knocker-shafts under the road - stand on all three at once while the Watch caves them in!",
          CP[4], [P(1020, 1150), P(1100, 1160), P(1060, 1220)], ["the west shaft", "the east shaft", "the deep shaft"], [KNOCK, POUND], "s3",
          "pennant of the Watch"),
    boss_stage("s3", "Pound-Master Trehan", "Pound-Master Trehan, his fists wrapped in chain: 'Cormoran's crowned at moonrise. You'll be under the throne's feet.'",
               CP[4], {"template": 770002, "name": "Pound-Master Trehan", "level": 59, "size": 75, "health_mult": 5, "guild": "of Golestandt's giants"},
               [POUND, OUT_], "Trehan falls across the road. South-east, on the throne-hill, a horn blows - the giants know.")], bot_min=50))

BW = dict(LOOK, name="Banner-Warden of the Watch", level=55)
d['chains'].append(counter(PREFIX, 1, "the Stonecrush Diggings", "the giants", LV[1], CP[1], BW, around(P, (230, 720)), [EXC, GRI, DEM], bot_min=50, title="The Giants Strike Back at The Stonecrush Diggings"))
d['chains'].append(counter(PREFIX, 2, "the Pony Moor", "the giants", LV[2], CP[2], BW, around(P, (960, 380)), [GIANT, HERD, CALL], bot_min=50, title="The Giants Strike Back at The Pony Moor"))
d['chains'].append(counter(PREFIX, 3, "the Stonecallers' Ring", "the giants", LV[3], CP[3], BW, around(P, (760, 800)), [CALL, GATH, SHAPE], bot_min=50, title="The Giants Strike Back at The Stonecallers' Ring"))
d['chains'].append(counter(PREFIX, 4, "the Pounders' Road", "the giants", LV[4], CP[4], BW, around(P, (1060, 1180)), [OUT_, POUND, KNOCK], bot_min=50, title="The Giants Strike Back at The Pounders' Road"))

# ---------------------------------------------------------------- the raid: the Giants' Throne (two or three groups)
d['chains'].append({
    "id": "dm_giants_throne", "title": "The Giants' Throne", "levels": [54, 58], "manual": True, "bots": 14, "bot_min_level": 52,
    "min_people": 8, "hint": "Sir Constantine himself is gathering the Dragon-Watch below the Giants' Throne.", "rest_s": 15, "start": "t1",
    "giver": giver(LOOK, "Sir Constantine", 62, P(1100, 1330),
                   "The Giants' Throne. Cormoran sits it at moonrise, crowned, and the dragon calls every giant in Albion to him. Two groups at least - eight, bots and all - three if you can. Then say [for Albion].",
                   "for Albion", "For Albion! Stay off his feet - and when the stonelords come, kill them first!",
                   "Cormoran is down. There's no king on the throne - and Golestandt's lair stands open.", "Back! Back down the road! We'll come again.",
                   hp=8, size=58),
    "guards": [dict(LOOK, name="dragonslayer of the Watch", level=55, count=4)],
    "stages": [
        {"id": "t1", "type": "boss", "name": "Cormoran of the Mount", "objective": "Defeat Cormoran of the Mount",
         "announce": "Cormoran of the Mount stands up from Gogmagog's throne, a crown of raw granite on his head, and the moor shakes: 'KING. I AM KING. THE DRAGON SAYS SO.'",
         "center": SEAT, "radius": 90, "time_s": 2400,
         "boss": {"template": 770001, "name": "Cormoran of the Mount", "level": 62, "size": 120, "health_mult": 14, "guild": "King of the Giants"},
         "adds": {"every_s": 50, "count": 3, "mobs": [LORD, POUND, CALL]},
         "success": "Cormoran falls like a hillside, and the granite crown breaks in two on the throne-step. The stonelords look at it - and walk away. Far to the west, under the south road, Golestandt roars, and the whole moor hears it.",
         "fail": "Cormoran drives the Dragon-Watch from the throne.", "on_success": "end", "on_fail": "end",
         "reward": {"xp_pct": 55, "copper_per_level": 550, "tokens": 55,
                    "items": [{"id": "dm004_cormoran_s_crown_shard", "gold_chance": 60, "silver_chance": 25},
                              {"id": "dm004_throne_step_mantle", "gold_chance": 60, "silver_chance": 25}]}}]})

json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
