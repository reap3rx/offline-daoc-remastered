"""Salisbury Plains' dynamic events (claude 2026-11-24, "Albion - the plan", round 2): the four old chains kept on the new
layout (the tomb robbers moved to the diggers' camp), two new ones - the Giants' Muster (a line of giants walking north with their
stones) and the Feast-Night (the Long Knives' dead rise at the old feasting-ground) - and the zone's set-piece, the Siege of the
Stones: the giants hold the Giants' Dance until the Sisters' resolve is full; held, the Watch and the Sisters keep a camp in the
ring until Cormoran comes back for it. Writes the zone's events file.   python ev001.py <in json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, move_stage, shift_levels, random_chain, occupy
Z = 1
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("The wide downs of Salisbury, and the Giants' Dance. Golestandt's giants have marched north out of Cornwall to take back "
             "the stones their kind first raised - the ring Merlin set over the graves of the lords Hengist murdered at the feast of the "
             "Long Knives. Their tomb-raiders dig out the dead that bind the stones, and the dead do not like it.")
ch = {c['id']: c for c in d['chains']}
t = ch['salisbury_plains_tomb_robbers']
for st in t['stages']:
    move_stage(st, P, (380, 1080) if st['id'] in ('a1', 'a2') else (200, 1160))
t['hint'] = "Spades ringing in the western fields - the diggers have opened another barrow..."

GIANT = mob(12719, "Salisbury giant", (20, 22), guild="the March of Golestandt")
GRANITE = mob(770007, "granite giant", (23, 25), guild="the March of Golestandt")
BOAR = mob(12699, "huge boar", (18, 20))
PRES = mob(12466, "disturbed presence", (17, 19), model=485)
WAND = mob(12622, "restless lord", (17, 19))
WATCH = {"template": 60167630, "model": 28, "equipment": "38762ab0-5f99-47cd-85b0-0bfaa37d71f9", "guild": "the Pendragon's Watch"}
SISTER = {"template": 60167630, "model": 38, "equipment": "eab1762c-33e7-4620-9e02-985d820d0369", "guild": "the Sisters of Amesbury"}

MARCH = P(760, 1150)
d['chains'].append(random_chain('sp_giants_muster', "The Giants' Muster", [18, 22],
    "The ground shakes on the southern plain - a line of giants is walking north, carrying stones...", 'm1', [
    {"id": "m1", "type": "cull", "name": "The Stone-Line", "objective": "Break the line of giants walking north with their stones",
     "announce": "A line of giants is walking north across the plain toward the Dance, each with a block of Dartmoor granite on its back. Break the line!",
     "center": MARCH, "radius": 90, "time_s": 1200, "kill": 10, "alive": 5, "mobs": [GIANT, GIANT, BOAR],
     "success": "The line breaks and the stones fall in the grass - and the giants' foreman turns back to see why.",
     "fail": "The giants walk on, and the stones reach the Dance.", "on_success": "m2", "on_fail": "o1", "reward": R(12, 100, 8)},
    {"id": "m2", "type": "boss", "name": "Foreman Trebiggan", "objective": "Defeat Foreman Trebiggan",
     "announce": "Foreman Trebiggan, a granite giant with a mason's maul: 'Little bones. Out of the road.' Bring friends.",
     "center": MARCH, "radius": 90, "time_s": 1200,
     "boss": {"template": 770007, "name": "Foreman Trebiggan", "level": 24, "size": 68, "pos": MARCH, "health_mult": 3, "guild": "the March of Golestandt"},
     "adds": {"every_s": 40, "count": 2, "mobs": [GIANT]},
     "success": "Trebiggan falls, and his stones stay where they dropped. The Dance will have to wait for them.",
     "fail": "Trebiggan drives the line on.", "on_success": "end", "on_fail": "o1", "reward": R(25, 180, 14, ["nu001_foreman_s_maul_ring"], 35)},
    occupy("o1", "The Giants Hold the South Road", "Drive the giants off the south road",
           "The giants' line has camped across the south road with its stones and turns back anyone who comes near.", P(700, 1050),
           [GIANT, BOAR], {"template": 12719, "name": "giant road-warden", "level": 22, "health_mult": 2}),
    ]))

FEAST = P(570, 860)
d['chains'].append(random_chain('sp_feast_night', 'The Feast-Night', [16, 20],
    "Lights on the old feasting-ground, and laughter, and then screaming - the Long Knives' night is replaying...", 'f1', [
    {"id": "f1", "type": "defend", "name": "The Feasting-Ground", "objective": "Keep Sister Gwenllian alive while she sings the dead to rest",
     "announce": "On the old feasting-ground the murdered lords are rising, and the Saxon dead with them, to fight the feast again. Sister Gwenllian of Amesbury has gone to sing them down!",
     "center": FEAST, "radius": 70, "duration_s": 180,
     "protect": dict(SISTER, name="Sister Gwenllian", level=18, pos=FEAST, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(540, 830), P(600, 900), P(600, 830)], "mobs": [PRES, WAND, PRES]},
     "thanks": "\"Rest now. The feast is over. It has been over for a long time.\"",
     "success": "The lords lie down - and at the head of the old table, a Saxon shade stands up with a knife in its hand.",
     "fail": "Sister Gwenllian falls, and the feast goes on all night.", "on_success": "f2", "on_fail": "end", "reward": R(12, 90, 8)},
    {"id": "f2", "type": "boss", "name": "the Feast-Master", "objective": "Defeat the Feast-Master",
     "announce": "The Feast-Master, Hengist's steward, raises his cup and his knife: 'Nimed eure saxes!' Bring friends.",
     "center": FEAST, "radius": 70, "time_s": 1200,
     "boss": {"template": 12016, "name": "the Feast-Master", "level": 21, "size": 60, "pos": FEAST, "health_mult": 3},
     "adds": {"every_s": 40, "count": 2, "mobs": [PRES]},
     "success": "The Feast-Master's knife falls into the grass. The feasting-ground is quiet until the next new moon.",
     "fail": "The Feast-Master's shade sits back down at the table, waiting.", "on_success": "end", "on_fail": "end",
     "reward": R(25, 180, 14, ["nu001_feast_master_s_seax_ring"], 35)},
    ], time="night"))

# ------------------------------------------------------------------ the set-piece: the Siege of the Stones
DANCE, STAGING, LANDING = P(921, 930), P(900, 775), P(905, 865)
BOLSTER = {"template": 770001, "name": "Bolster, Herald of Golestandt", "level": 27, "size": 72, "health_mult": 2.5,
           "guild": "Herald of the White Dragon"}
d['chains'].append({
    "id": "sp_dance_assault", "title": "The Siege of the Stones", "levels": [22, 26], "manual": True, "bots": 8, "min_people": 4,
    "bot_min_level": 18, "hint": "Dame Lynet of the Watch is gathering a war band on the downs north of the Giants' Dance.", "rest_s": 15, "start": "s1",
    "giver": dict(WATCH, name="Dame Lynet", level=26, pos=STAGING, health_mult=3, model=38,
                  greet="The giants hold the Dance. The Abbess says the dead under it can't rest while they do, and neither can I. Four at least, bots and all - say [for the stones].",
                  accept="for the stones", reply="Down to the ring! Clear the outer stones, hold the three great arches, and bring down their herald!",
                  busy="Not yet. Rest, and gather.", cooldown_s=120, thanks="The Dance is ours again!", regret="Back to the downs! We'll come again."),
    "guards": [dict(WATCH, name="watchman of Salisbury", level=22, count=2), dict(SISTER, name="sister of Amesbury", level=20, count=1)],
    "stages": [
        {"id": "s1", "type": "cull", "name": "The Outer Stones", "objective": "Clear the giants from the outer stones",
         "announce": "Into the ring! The giants are turning from the stones to meet us!", "center": DANCE, "radius": 90, "time_s": 900,
         "kill": 18, "alive": 7, "mobs": [GIANT, GIANT, GRANITE], "success": "The outer ring is clear. The giants fall back to the great arches.",
         "fail": "The war band is thrown back onto the downs.", "on_success": "s2", "on_fail": "end", "reward": R(15, 140, 10)},
        {"id": "s2", "type": "wards", "name": "The Great Arches", "objective": "Hold the three great arches at once",
         "announce": "The giants are singing at the three great arches to pull them down! Stand under all three at once and the Sisters will sing them still!",
         "center": DANCE, "radius": 90, "wards": [P(905, 915), P(940, 920), P(925, 950)],
         "ward_names": ["the west arch", "the east arch", "the south arch"], "ward_radius": 18, "hold_s": 30, "time_s": 900,
         "alive": 2, "mobs": [GIANT, GRANITE], "reinforce_s": 40, "flag": 466, "flag_name": "banner of the Watch",
         "success": "The arches stand still - and Bolster steps into the ring.", "fail": "The giants drive the war band off the arches.",
         "on_success": "s3", "on_fail": "end", "reward": R(15, 140, 10)},
        {"id": "s3", "type": "boss", "name": "Bolster", "objective": "Defeat Bolster, Herald of Golestandt",
         "announce": "Bolster, Herald of Golestandt, steps between the arches: 'My master remembers raising these stones. Do you remember anything?'",
         "center": DANCE, "radius": 90, "time_s": 1200, "boss": BOLSTER, "adds": {"every_s": 35, "count": 2, "mobs": [GIANT, GRANITE]},
         "success": "Bolster falls across the altar stone. The Watch raises its banner in the Giants' Dance, and the Sisters begin to sing.",
         "fail": "Bolster drives the war band out of the ring.", "on_success": "end", "on_fail": "end",
         "reward": R(35, 260, 22, ["gd001_bolster_s_arm_ring"], 35)}]})
d['chains'].append({
    "id": "sp_dance_return", "title": "Cormoran Comes", "levels": [23, 26], "manual": True, "bots": 8, "bot_min_level": 18,
    "hint": "The ground shakes in the south: Cormoran is coming for the Dance.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Altar Stone", "objective": "Keep Sister Hild alive at the altar stone",
         "announce": "Giants on every side of the Dance! Every giant Golestandt could send. Hold the altar stone!",
         "center": DANCE, "radius": 80, "duration_s": 200, "protect": dict(SISTER, name="Sister Hild", level=24, pos=DANCE, health_mult=5),
         "waves": {"every_s": 22, "count": 4, "from": [P(860, 1000), P(990, 990), P(930, 1040)], "mobs": [GIANT, GRANITE, BOAR]},
         "success": "The first rush breaks - and Cormoran walks into the ring.", "fail": "Sister Hild falls at the altar stone.",
         "on_success": "x2", "on_fail": "end", "reward": R(20, 160, 14)},
        {"id": "x2", "type": "boss", "name": "Cormoran", "objective": "Defeat Cormoran",
         "announce": "Cormoran, the giant of the Mount, ducks under an arch: 'Jack killed my father with a pit and a horn. I've brought no pit.'",
         "center": DANCE, "radius": 80, "time_s": 900,
         "boss": {"template": 770002, "name": "Cormoran", "level": 27, "size": 75, "health_mult": 2.5, "guild": "of the Mount"},
         "adds": {"every_s": 35, "count": 2, "mobs": [GRANITE]},
         "success": "Cormoran falls. The Dance holds - for now.", "fail": "Cormoran takes the Dance back.",
         "on_success": "end", "on_fail": "end", "reward": R(30, 220, 20, ["gd001_cormoran_s_tooth"], 35)}]})

GD = "gd001_"
d['siege'] = {
    "id": "giants_dance", "name": "the Giants' Dance", "enemy": "the March of Golestandt",
    "resolve_name": "The Sisters' resolve", "enemy_name": "The giants' hold", "faction": "sisters_of_amesbury",
    "feeds": {"sp_giants_muster": 20, "sp_feast_night": 10, "salisbury_plains_tomb_robbers": 10, "salisbury_plains_restless_plain": 10,
              "salisbury_plains_basilisk_nest": 5, "salisbury_plains_spriggarn_ambush": 5},
    "feed_default": 5,
    "quests": {"sp_diggers": 10, "sp_what_spade_woke": 10, "sp_paymaster": 15, "sp_long_knives": 15, "sp_footprints": 10,
               "sp_cottrel": 15, "sp_the_dance": 20, "sp_giants_dead": 20},
    "enemy_feeds": {"sp_giants_muster": 20}, "enemy_default": 5, "war_chain": "sp_giants_muster",
    "assault": "sp_dance_assault", "raids": [], "last_raid": "sp_dance_return", "hold_h": 2, "raid_gap_h": [2, 1.5, 1.5],
    "criers": ["sp_abbess", "sp_osfrid"], "bots_go_after_m": 30,
    "open_text": "Hear me! The Watch and the Sisters of Amesbury mean to take back the Giants' Dance! Dame Lynet waits on the downs north of the ring. If no one leads within the half-hour, the Watch goes without you.",
    "taken_text": "The Giants' Dance is ours! The Watch's banner flies over the stones and the Sisters sing for the dead - go and see.",
    "repelled_text": "The attack on the Dance has been thrown back. The giants grow bolder.",
    "raid_text": "The ground shakes in the south: the giants are coming back for the Dance!",
    "held_text": "The giants are thrown back from the stones. The Dance holds.",
    "fall_text": "The Giants' Dance has fallen to Cormoran. The Sisters must rebuild their resolve.",
    "carry_text": "Dame Lynet leads you down off the downs at a run.",
    "carried_cry": "The Watch wouldn't wait any longer - they have stormed {0}!",
    "hostile_tier": "orange", "sites": ["the_dance", "dance_oracle", "dance_ring", "dance_approach"],
    "staging": STAGING, "landing": LANDING, "area": [921, 930, 110],
    "camp_npcs": [
        dict(SISTER, kind="marks", name="Sister Cellarer Hild", level=22, pos=P(900, 920),
             greet="The Sisters' stores, for those who took back the stones and those who keep them.",
             stock=[{"item": GD + "cloak_of_the_dance", "price": 60}, {"item": GD + "trilithon_ring", "price": 40},
                    {"item": GD + "heel_stone_torc", "price": 40}, {"item": GD + "amesbury_grave_bracer", "price": 40},
                    {"item": "tw_strong_draught_of_healing", "price": 2}, {"item": "tw_strong_draught_of_power", "price": 2}]),
        dict(SISTER, kind="coin", name="Sister Infirmarian Nest", level=20, pos=P(940, 940),
             greet="Amesbury's brews, carried out to the stones. Coin, mind - the priory needs a roof.",
             stock=[{"item": GD + "amesbury_draught"}, {"item": GD + "downs_herb_tonic"}, {"item": GD + "dance_mead"}]),
        dict(WATCH, kind="idle", name="watchman of the Dance", level=22, pos=P(915, 950), count=3,
             idle="I never thought I'd stand inside the Giants' Dance. It's colder than you'd think."),
        dict(SISTER, kind="idle", name="Sister Gwenllian", level=20, pos=P(930, 910), idle="Listen. The dead under the stones are quiet tonight."),
    ],
    "holdouts": [
        {"kind": "holdout", "name": "granite giant straggler", "template": 770007, "level": 24, "pos": P(980, 990), "count": 2, "tier": "orange", "respawn_s": 600},
        {"kind": "holdout", "name": "Salisbury giant straggler", "template": 12719, "level": 22, "pos": P(860, 1000), "count": 2, "tier": "yellow", "respawn_s": 300}],
}
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
