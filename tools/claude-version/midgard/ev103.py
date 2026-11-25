"""Gotar's dynamic events (claude 2026-11-25, "Midgard - the plan", round 2): the four old chains kept, two new - the zone's
set-piece, the Scale-Caravan (a boss hunt: a drakulv scale-caravan runs up the trade road to the svartalf post, and its master walks
with it: the south thread) and the Drowned Bell (at night the wreck's bell rings and the drowned come ashore after their steersman).
Writes the zone's events file.   python ev103.py <in zone103 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, random_chain, occupy
Z = 103
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Gotar: Fort Atla on the north lakes and Nalliten on the east, wild country between. Gjalpinulva's drakulv buy the "
             "svartalf outcasts with scale and gold, and their scale-traders camp on the trade road by the old svartalf post with a "
             "dragon-preacher. A wreck off the east shore was carrying scale north; envy drakelings creep up from the south, and half "
             "the seithkona at the circle sing for the dragon now.")
OUT_ = mob(60166664, "svartalf outcast", (15, 17), guild="the Scale-Traders")
GUARD = mob(60166659, "svartalf guard", (16, 18), guild="the Scale-Traders")
ENVY = mob(60160533, "envy drakeling", (16, 18), guild="drawn to the scale")
SOUL = mob(60160165, "drowned soul", (14, 16), guild="of the wreck")
OARS = mob(60166175, "skeletal oarsman", (15, 17), guild="of the wreck")
HUSCARL = {"template": 60157473, "model": 160, "equipment": "SvasudGuard", "guild": "King Eirik's Huscarls"}
SKALD = {"template": 60157473, "model": 157, "guild": "King Eirik's Huscarls"}

# ------------------------------------------------------------------ the set-piece: the Scale-Caravan (a boss hunt)
ROAD_S, POST = P(820, 1180), P(500, 720)
d['chains'].append(random_chain('gt_scale_caravan', 'The Scale-Caravan', [17, 21],
    "Wagon-bells on the trade road - a scale-caravan is coming up from the south...", 'c1', [
    {"id": "c1", "type": "cull", "name": "The Outriders", "objective": "Break the caravan's svartalf outriders on the trade road",
     "announce": "A drakulv scale-caravan is coming up Gotar's trade road from the south! Huscarl Hallbjorn wants it stopped - break its outriders!",
     "center": ROAD_S, "radius": 90, "time_s": 900, "kill": 14, "alive": 6, "mobs": [OUT_, OUT_, GUARD],
     "success": "The outriders break - and the caravan whips its beasts on, north toward the svartalf post, with its master walking beside it.",
     "fail": "The outriders drive you off the road, and the caravan rolls on north.", "on_success": "c2", "on_fail": "end",
     "reward": R(12, 120, 10)},
    {"id": "c2", "type": "boss", "name": "Scale-Master Naudr", "objective": "Hunt down Scale-Master Naudr on the trade road",
     "announce": "Scale-Master Naudr, a svartalf in mail of red dragon-scale, walking beside his wagons up the road: 'The Mother pays in gold. What do you pay in?' He walks the road between his wagons and the svartalf post - hunt him down. Bring friends.",
     "center": ROAD_S, "radius": 110, "time_s": 1500,
     "path": path(P, (820, 1180), (650, 980)) + path(P, (650, 980), (500, 720)) + path(P, (500, 720), (820, 1180)),
     "boss": {"template": 60166659, "name": "Scale-Master Naudr", "level": 22, "size": 70, "pos": ROAD_S, "health_mult": 4,
              "guild": "of the Scale-Traders"},
     "adds": {"every_s": 40, "count": 2, "mobs": [GUARD, ENVY]},
     "success": "Naudr falls in the road, and his wagons stop. They're full of dragon-scale - warm, every one - and a letter bound for Malmohus.",
     "fail": "Naudr gets his wagons to the svartalf post, and the scale goes north.", "on_success": "end", "on_fail": "end",
     "reward": R(30, 240, 20, ["nu103_naudr_s_scale_mail_bracer", "nu103_caravan_master_s_ledger"], 40)},
    ]))

# ------------------------------------------------------------------ the Drowned Bell
SHORE = P(1040, 440)
d['chains'].append(random_chain('gt_drowned_bell', 'The Drowned Bell', [15, 18],
    "A bell ringing out at sea, where no ship floats - the wreck is calling its crew...", 'b1', [
    {"id": "b1", "type": "defend", "name": "The Skald's Verse", "objective": "Keep Skald Ingvild alive while she sings the drowned to rest",
     "announce": "The wreck's bell is ringing and the drowned are coming ashore! Skald Ingvild of Fort Atla is on the beach singing them to rest - keep her alive!",
     "center": SHORE, "radius": 70, "duration_s": 180, "protect": dict(SKALD, name="Skald Ingvild", level=17, pos=SHORE, health_mult=8, model=168),
     "waves": {"every_s": 24, "count": 3, "from": [P(1080, 470), P(1000, 420), P(1060, 400)], "mobs": [SOUL, OARS]},
     "thanks": "\"Every drowned man deserves a verse. Even the ones who row for dragons.\"",
     "success": "The drowned lie down in the surf one by one - all but the last, who walks up out of the sea with the ship's wheel still in his hands.",
     "fail": "Ingvild falls, and the drowned walk inland.", "on_success": "b2", "on_fail": "end", "reward": R(12, 110, 8)},
    {"id": "b2", "type": "boss", "name": "the Drowned Steersman", "objective": "Defeat the Drowned Steersman",
     "announce": "The Drowned Steersman, weed in his ribs, a red scale nailed to his wheel: 'We carried her scale. We were promised the shore.'",
     "center": SHORE, "radius": 80, "time_s": 1200,
     "boss": {"template": 60166181, "name": "the Drowned Steersman", "level": 19, "size": 65, "pos": SHORE, "health_mult": 3, "guild": "of the wreck"},
     "adds": {"every_s": 40, "count": 2, "mobs": [SOUL]},
     "success": "The Steersman falls, and the bell out at sea stops ringing.", "fail": "The Steersman walks back into the sea, and the bell rings on.",
     "on_success": "end", "on_fail": "end", "reward": R(25, 200, 16, ["nu103_steersman_s_bell"], 35)},
    ], time="night"))
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
