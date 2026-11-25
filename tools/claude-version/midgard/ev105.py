"""Myrkwood Forest's dynamic events (claude 2026-11-25, "Midgard - the plan", round 2): the five old chains kept, two new - the
zone's set-piece, the Blood-Moon (a boss hunt: at night under a red moon the Blood-Moon Wolf, Hati's own get, runs the west wood
with the worgs: the west thread) and the Seer-Hunt (where the threads cross: werewolves and drakulv come for Volva Groa's hut on
the same night, and her apprentice holds the door; a wyrm-priest comes after).
Writes the zone's events file.   python ev105.py <in zone105 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, random_chain, occupy
Z = 105
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Myrkwood Forest: Galplen and Gna Faste in a dark, deadly wood - Midgard's hard start. Where the threads cross: the "
             "werewolves of the west wood, Fenrir's kin, answer to Hati in Raumarik; the drakulv missionaries camped with the svartalf in "
             "the south answer to the Hierophant in Malmohus; and both hunt Volva Groa, the old seer in the willow-wood, who knows how "
             "Hati ends and the other half of the dragon's true name.")
WORG = mob(60161576, "gray worg", (25, 27), guild="running with Fenrir's Kin")
RIDGE = mob(60165311, "ridgeback worg", (27, 29), guild="running with Fenrir's Kin")
WERE = mob(60167849, "werewolf", (27, 29), guild="Fenrir's Kin")
WATCH = mob(60166670, "svartalf watcher", (25, 27), guild="the Scale-Traders")
PRED = mob(60166666, "svartalf predator", (27, 29), guild="the Scale-Traders")
SEER = {"template": 60157473, "model": 168, "guild": "the Seidr-Folk"}

# ------------------------------------------------------------------ the set-piece: the Blood-Moon (a boss hunt)
RUN = P(700, 1000)
d['chains'].append(random_chain('mw_blood_moon', 'The Blood-Moon', [26, 30],
    "The moon rises red over Myrkwood, and every worg in the wood begins to howl...", 'm1', [
    {"id": "m1", "type": "cull", "name": "The Howling Packs", "objective": "Break the worg packs running under the red moon",
     "announce": "A blood-moon over Myrkwood! The worgs are running in the middle wood - break the packs before they reach Gna Faste!",
     "center": RUN, "radius": 90, "time_s": 900, "kill": 14, "alive": 6, "mobs": [WORG, WORG, RIDGE],
     "success": "The packs break - and out of the west wood, under the red moon, comes the thing they were howling for.",
     "fail": "The packs run howling to the walls of Gna Faste.", "on_success": "m2", "on_fail": "end", "reward": R(12, 140, 10)},
    {"id": "m2", "type": "boss", "name": "the Blood-Moon Wolf", "objective": "Hunt down the Blood-Moon Wolf",
     "announce": "The Blood-Moon Wolf - a werewolf as tall as a longhouse door, its fur red in the moonlight: Hati's own get, out of Raumarik. It runs the west wood - hunt it down. A fight for the whole forest: bring friends.",
     "center": RUN, "radius": 120, "time_s": 1500,
     "path": [P(700, 1000), P(560, 1080), P(420, 1000), P(330, 1130), P(500, 1180), P(700, 1000)],
     "boss": {"template": 60167849, "name": "the Blood-Moon Wolf", "level": 32, "size": 90, "pos": RUN, "health_mult": 4,
              "guild": "Get of Hati"},
     "adds": {"every_s": 40, "count": 2, "mobs": [WERE, RIDGE]},
     "success": "The Blood-Moon Wolf falls, and the moon goes white again. Far to the north-west, in Raumarik, something howls in answer.",
     "fail": "The Blood-Moon Wolf runs back into the west wood, and the moon stays red till dawn.", "on_success": "end", "on_fail": "end",
     "reward": R(32, 280, 22, ["nu105_blood_moon_fang", "nu105_red_moon_mantle"], 40)},
    ], time="night"))

# ------------------------------------------------------------------ the Seer-Hunt (where the threads cross)
HUT = P(640, 540)
d['chains'].append(random_chain('mw_seer_hunt', 'The Seer-Hunt', [26, 30],
    "Wolves howling west of Galplen, and svartalf lanterns in the willow-wood - both coming for the volva's hut...", 's1', [
    {"id": "s1", "type": "defend", "name": "The Volva's Door", "objective": "Keep Hallveig, Groa's apprentice, alive at the volva's door",
     "announce": "Werewolves from the west and svartalf from the south are both coming for Volva Groa's hut tonight! Her apprentice Hallveig holds the door - keep her alive!",
     "center": HUT, "radius": 70, "duration_s": 200, "protect": dict(SEER, name="Hallveig the Apprentice", level=28, pos=HUT, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(560, 600), P(720, 600), P(600, 460)], "mobs": [WERE, WATCH, PRED, WORG]},
     "thanks": "\"Groa saw this night years ago. She said someone would come. I didn't believe her.\"",
     "success": "Wolves and svartalf both fall back - and a wyrm-priest in red scale walks out of the willows, alone, smiling.",
     "fail": "Hallveig falls at the door, and Groa has to flee into the willows.", "on_success": "s2", "on_fail": "end", "reward": R(14, 150, 12)},
    {"id": "s2", "type": "boss", "name": "Wyrm-Priest Ormr", "objective": "Defeat Wyrm-Priest Ormr",
     "announce": "Wyrm-Priest Ormr, a drakulv in robes of red scale: 'The wolves want her end. We only want her words. Stand aside, and she lives.'",
     "center": HUT, "radius": 80, "time_s": 1200,
     "boss": {"template": 60160115, "name": "Wyrm-Priest Ormr", "level": 31, "size": 65, "pos": HUT, "health_mult": 3, "guild": "of Gjalpinulva's Missionaries"},
     "adds": {"every_s": 40, "count": 2, "mobs": [WATCH]},
     "success": "Ormr falls in the volva's garden. Groa comes to the door and looks at him for a long time. 'He'd have killed me, after,' she says.",
     "fail": "Ormr drives you off, and the volva's hut burns.", "on_success": "end", "on_fail": "end",
     "reward": R(28, 240, 20, ["nu105_ormr_s_scale_robe_sash"], 35)},
    ]))
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
