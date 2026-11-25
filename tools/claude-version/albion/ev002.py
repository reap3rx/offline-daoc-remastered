"""Black Mountains South's dynamic events (claude 2026-11-24, "Albion - the plan"): the four old chains moved onto the new
layout (the goblin fishers to the drowned reach, the highwaymen to the Ludlow cut, the spiders to the north forest), a new
one - the Badon Dead (Arthur's drowned spearmen rise at Huw's ferry) - and the zone's set-piece, Vetusta Abbey: a fort to
retake (ZoneSiege), fed by the zone's events and quests; held, the Abbey Faithful keep a camp in the abbey yard until the
Red Abbot comes back for it. Writes the zone's events file.   python ev002.py <in zone002 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, move_stage, shift_levels, random_chain, occupy
Z = 2
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("The southern Black Mountains: Humberton keep and Ludlow town, the river and its goblin fishers, and Vetusta Abbey "
             "in the south - where Bishop Burhoff has filled the cloister with red-corded brothers and driven the true monks out. "
             "The goblins of Tepok's Mine have dug into a cairn of Arthur's dead from Mount Badon, and somebody is buying the bones.")
ch = {c['id']: c for c in d['chains']}

f = ch['black_mountains_south_goblin_fishers']
f['title'] = 'The Drowned Nets'
f['hint'] = "Nets across the river at the drowned reach - and the fishermen in them aren't breathing..."
for st in f['stages']:
    move_stage(st, P, (430, 660) if st['id'] in ('a1', 'a2') else (446, 779))

h = ch['black_mountains_south_highway_robbery']
g1 = h['stages'][0]
g1['path'] = path(P, (593, 1040), (900, 900)) + path(P, (900, 900), (1205, 780))
for st in h['stages']:
    move_stage(st, P, (1205, 780) if st['id'] in ('g2', 'g3') else (1000, 850))
h['giver']['guild'] = "the Pendragon's Watch"
for gd in h['guards']:
    gd['guild'] = "the Pendragon's Watch"
h['giver']['greet'] = "Black Tom and his highwaymen robbed the Ludlow coach again - and they let a cart of red-corded monks go by untouched. I know where they camp. Ride with me and we'll end it. Tell me when you're [ready]."

s = ch['black_mountains_south_spider_hollow']
for st in s['stages']:
    move_stage(st, P, (760, 280) if st['id'] in ('a1', 'a2') else (754, 394))

# ------------------------------------------------------------------ new: the Badon Dead
SPEAR = mob(12728, "drowned spearman of Badon", (10, 12), size=50)
UGW = mob(12635, "undead goblin warrior", (10, 11))
FERRY = P(720, 790)
d['chains'].append(random_chain('bs_badon_dead', 'The Badon Dead', [10, 13],
    "Mist on the river at Huw's ferry, and the sound of marching under the water...", 'b1', [
    {"id": "b1", "type": "defend", "name": "Huw's Ferry", "objective": "Keep Nest, Huw's wife, alive at the ferry",
     "announce": "Arthur's dead from Mount Badon are walking up out of the river at Huw's ferry - raised in rotted mail, with their spears still in their hands!",
     "center": FERRY, "radius": 70, "duration_s": 180,
     "protect": {"name": "Nest the Ferry-Wife", "level": 11, "pos": FERRY, "health_mult": 8},
     "waves": {"every_s": 25, "count": 3, "from": [P(700, 740), P(760, 760), P(680, 770)], "mobs": [SPEAR, SPEAR, UGW]},
     "thanks": "\"Thirty years married to a ferryman and I never once had to fight the river.\"",
     "success": "The drowned fall back into the river - all but one, who wades out with a captain's plume rotting on his helm.",
     "fail": "Nest falls, and the drowned march up the bank.", "on_success": "b2", "on_fail": "o1", "reward": R(12, 90, 8)},
    {"id": "b2", "type": "boss", "name": "the Drowned Captain of Badon", "objective": "Lay the Drowned Captain of Badon to rest",
     "announce": "The Drowned Captain of Badon raises a red-dragon shield: 'Form on me! The Saxon is at the river!' He doesn't know you. Bring friends.",
     "center": FERRY, "radius": 70, "time_s": 1200,
     "boss": {"template": 12884, "name": "the Drowned Captain of Badon", "level": 14, "size": 60, "pos": FERRY, "health_mult": 3},
     "adds": {"every_s": 40, "count": 2, "mobs": [SPEAR]},
     "success": "The captain sinks to his knees in the shallows. 'Badon,' he says. 'Did we hold?' And then he is only bones.",
     "fail": "The drowned captain leads his men up onto the road.", "on_success": "end", "on_fail": "o1",
     "reward": R(25, 180, 14, ["nu002_drowned_captain_s_plume"], 35)},
    occupy("o1", "The Drowned Hold the River Road", "Drive the drowned spearmen off the river road",
           "The drowned of Badon have formed a shield-wall on the river road, and turn back anyone who passes.", P(700, 860),
           [SPEAR, UGW], {"template": 12728, "name": "drowned shield-wall leader", "level": 13, "health_mult": 2}),
    ]))

# ------------------------------------------------------------------ the set-piece: Vetusta Abbey
BRO = mob(12284, "dark brother", (13, 15), guild="the Brethren of Vetusta")
ARMS = mob(12328, "dark brother-in-arms", (14, 16), guild="the Brethren of Vetusta")
INI = mob(12075, "crimson initiate", (14, 16), guild="the Crimson")
SAC = mob(12161, "filidh sacrificer", (14, 15), guild="the Crimson")
FAITH = {"template": 60167630, "model": 32, "equipment": "eab1762c-33e7-4620-9e02-985d820d0369", "guild": "the Abbey Faithful"}
WATCH = {"template": 60167625, "model": 27, "equipment": "afbf0cbc-36a3-4471-b32a-057ae99619db", "guild": "the Pendragon's Watch"}
ABBEY, YARD = P(549, 1500), P(560, 1470)
STAGING = P(600, 1370)
d['chains'].append({
    "id": "bs_vetusta_assault", "title": "Retake Vetusta Abbey", "levels": [13, 17], "manual": True, "bots": 8, "min_people": 4,
    "bot_min_level": 10, "hint": "Brother-Knight Gerent is gathering the Abbey Faithful on the road above Vetusta.", "rest_s": 15, "start": "v1",
    "giver": dict(FAITH, name="Brother-Knight Gerent", level=17, pos=STAGING, health_mult=3, model=28,
                  greet="Vetusta's bell has rung and the brothers are coming home - but the Bishop's men still hold the cloister. Four at least, bots and all, and when you're ready, say [for Vetusta].",
                  accept="for Vetusta", reply="Down to the abbey! Through the yard, hold the three doors, and the abbey is ours!",
                  busy="Not yet. The brothers are still coming down out of the hills. Rest, and gather.", cooldown_s=120,
                  thanks="Vetusta is ours! Ring the bell!", regret="Back up the road! We'll come again."),
    "guards": [dict(WATCH, name="Watchman of Humberton", level=14, count=2), dict(FAITH, name="brother of Vetusta", level=13, count=2)],
    "stages": [
        {"id": "v1", "type": "cull", "name": "The Abbey Yard", "objective": "Clear the Bishop's brothers from the abbey yard",
         "announce": "Into the yard! The Bishop's brothers are coming out of the cloister to meet us!", "center": YARD, "radius": 70,
         "time_s": 900, "kill": 20, "alive": 8, "mobs": [BRO, BRO, ARMS, INI],
         "success": "The yard is ours. The red-corded brothers fall back to the doors.", "fail": "The Faithful are thrown back up the road.",
         "on_success": "v2", "on_fail": "end", "reward": R(14, 120, 10)},
        {"id": "v2", "type": "wards", "name": "The Three Doors", "objective": "Hold the chapel, cloister and bell-tower doors at once",
         "announce": "The Bishop's men hold three doors - the chapel, the cloister and the bell tower. Stand on all three at once and the Faithful will bar them!",
         "center": ABBEY, "radius": 80, "wards": [P(520, 1490), P(575, 1515), P(555, 1460)],
         "ward_names": ["the chapel door", "the cloister door", "the bell-tower door"], "ward_radius": 20, "hold_s": 30, "time_s": 900,
         "alive": 2, "mobs": [BRO, ARMS], "reinforce_s": 40, "flag": 466, "flag_name": "banner of Vetusta",
         "success": "The doors are barred - and out of the crypt stair comes the Bishop's sword.", "fail": "The doors hold. The Faithful fall back.",
         "on_success": "v3", "on_fail": "end", "reward": R(14, 120, 10)},
        {"id": "v3", "type": "boss", "name": "Brother-Captain Hrodric", "objective": "Defeat Brother-Captain Hrodric, the Bishop's Sword",
         "announce": "Brother-Captain Hrodric, the Bishop's Sword, red cord over his mail: 'The Lady gave this abbey to my master. I give it to no one.'",
         "center": ABBEY, "radius": 80, "time_s": 1200,
         "boss": {"template": 12328, "name": "Brother-Captain Hrodric", "level": 18, "size": 62, "health_mult": 2.5, "guild": "the Bishop's Sword"},
         "adds": {"every_s": 35, "count": 3, "mobs": [ARMS, INI]},
         "success": "Hrodric falls on the chapel steps. Vetusta's bell rings out over the mountains, and the Abbey Faithful come home.",
         "fail": "Hrodric drives the Faithful out of the yard.", "on_success": "end", "on_fail": "end",
         "reward": R(35, 240, 20, ["va002_hrodric_s_red_cord"], 35)}]})
d['chains'].append({
    "id": "bs_vetusta_return", "title": "The Red Abbot", "levels": [14, 17], "manual": True, "bots": 8, "bot_min_level": 10,
    "hint": "Red torches on the road from Ludlow: the Red Abbot has come for Vetusta.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Chapel Steps", "objective": "Keep Sacristan Hywel alive on the chapel steps",
         "announce": "The Red Abbot's brothers are at the gate! Every red cord in the mountains. Hold the chapel steps!",
         "center": ABBEY, "radius": 70, "duration_s": 200,
         "protect": dict(FAITH, name="Sacristan Hywel", level=16, pos=ABBEY, health_mult=5),
         "waves": {"every_s": 22, "count": 4, "from": [P(610, 1520), P(500, 1530), P(560, 1420)], "mobs": [BRO, ARMS, INI, SAC]},
         "success": "The first rush breaks - and the Red Abbot walks through the gate.", "fail": "Sacristan Hywel falls on the steps.",
         "on_success": "x2", "on_fail": "end", "reward": R(20, 140, 14)},
        {"id": "x2", "type": "boss", "name": "the Red Abbot", "objective": "Defeat the Red Abbot",
         "announce": "The Red Abbot, in Burhoff's own cope: 'The Bishop sends his blessing. All of it.'",
         "center": ABBEY, "radius": 70, "time_s": 900,
         "boss": {"template": 12075, "name": "the Red Abbot", "level": 18, "size": 62, "health_mult": 2.5, "guild": "of the Crimson"},
         "adds": {"every_s": 35, "count": 3, "mobs": [ARMS, SAC]},
         "success": "The Red Abbot falls. Vetusta holds - for now.", "fail": "The Red Abbot takes Vetusta back.",
         "on_success": "end", "on_fail": "end", "reward": R(30, 200, 20, ["va002_red_abbot_s_cope_clasp"], 35)}]})

QM = "va002_"
d['siege'] = {
    "id": "vetusta", "name": "Vetusta Abbey", "enemy": "the Bishop's brothers",
    "resolve_name": "The Faithful's resolve", "enemy_name": "The Bishop's hold", "faction": "abbey_faithful",
    "feeds": {"bs_badon_dead": 15, "black_mountains_south_highway_robbery": 10, "black_mountains_south_goblin_fishers": 10,
              "black_mountains_south_red_dwarf_raid": 5, "black_mountains_south_spider_hollow": 5},
    "feed_default": 5,
    "quests": {"bs_camlann_dead": 10, "bs_robbers_landing": 10, "bs_highway": 10, "bs_bishops_letters": 20, "bs_bells_of_vetusta": 25,
               "bs_badon_cairn": 15, "willing_heart": 10},
    "enemy_feeds": {"bs_badon_dead": 15}, "enemy_default": 5, "war_chain": "bs_badon_dead",
    "assault": "bs_vetusta_assault", "raids": [], "last_raid": "bs_vetusta_return", "hold_h": 2, "raid_gap_h": [2, 1.5, 1.5],
    "criers": ["bs_prior_anselm", "bs_reeve_gwenda"], "bots_go_after_m": 30,
    "open_text": "Hear me! The Abbey Faithful mean to take Vetusta back from the Bishop's brothers! Brother-Knight Gerent waits on the road above the abbey. If no one leads within the half-hour, the Faithful go without you.",
    "taken_text": "Vetusta is ours! The bell rings again over the mountains, and the Faithful keep the abbey yard - go and see.",
    "repelled_text": "The Faithful have been thrown back from Vetusta. The Bishop's brothers grow bolder.",
    "raid_text": "Red torches on the Ludlow road: the Bishop's brothers are coming back for Vetusta!",
    "held_text": "The red-corded brothers are thrown back from the gate. Vetusta holds.",
    "fall_text": "Vetusta has fallen to the Red Abbot. The bell is bound again, and the Faithful must rebuild their resolve.",
    "carry_text": "Brother-Knight Gerent leads you down the abbey road at a run.",
    "carried_cry": "The Faithful wouldn't wait any longer - they have stormed {0}!",
    "hostile_tier": "yellow", "sites": ["vetusta_abbey", "abbey_cloister"],
    # the abbey's own people and the farm's guards come back only when the abbey is retaken
    "held_only": ["Brother Darren", "Brother Don", "Brother Tanis", "Sir Lukas", "Sister Deane", "Zenob Mra", "Veteran Guard", "veteran guard"],
    "held_only_m": 120,
    "staging": STAGING, "landing": YARD, "area": [549, 1500, 100],
    "camp_npcs": [
        dict(FAITH, kind="marks", name="Cellarer Bede", level=16, pos=P(530, 1480),
             greet="The abbey's own stock, for those who took it back and those who keep it.",
             stock=[{"item": QM + "vetusta_bell_cloak", "price": 60}, {"item": QM + "cloister_key_ring", "price": 40},
                    {"item": QM + "white_cord_belt", "price": 40}, {"item": QM + "abbey_wall_bracer", "price": 40},
                    {"item": "tw_strong_draught_of_healing", "price": 2}, {"item": "tw_strong_draught_of_power", "price": 2}]),
        dict(FAITH, kind="coin", name="Infirmarian Gwladys", model=38, level=14, pos=P(565, 1485),
             greet="The infirmary's open again. Brews from the abbey garden. Coin, mind - the roof needs mending.",
             stock=[{"item": QM + "infirmary_draught"}, {"item": QM + "abbey_garden_tonic"}, {"item": QM + "vetusta_mead"}]),
        dict(FAITH, kind="idle", name="brother of Vetusta", level=12, pos=P(545, 1510), count=3,
             idle="Three months on the road with nothing but our habits. It's good to sleep under a roof."),
        dict(FAITH, kind="idle", name="Brother Porter Wyn", level=14, pos=P(540, 1492), idle="The bell rings the hours again. Listen."),
    ],
    "holdouts": [
        {"kind": "holdout", "name": "red-corded brother", "template": 12284, "level": 15, "pos": P(600, 1560), "count": 3, "tier": "yellow", "respawn_s": 300},
        {"kind": "holdout", "name": "Bishop's crypt-guard", "template": 12328, "level": 16, "pos": P(538, 1578), "count": 2, "tier": "orange", "respawn_s": 600}],
}
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
