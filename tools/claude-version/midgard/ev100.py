"""Vale of Mularn's dynamic events (claude 2026-11-24, "Midgard - the plan", round 1): the five old chains kept, and two new -
the zone's set-piece, the Moon-Howler (a boss hunt at night round Darkness Falls: a wolf as big as a horse, frost in its tracks,
the west thread's first sign), and the Red-Eye Sermon (a seeress breaks the dragon-preacher's sermon at the Vendo Caverns: the
south thread's). Writes the zone's events file.   python ev100.py <in zone100 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, random_chain, occupy
Z = 100
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("The Vale of Mularn: Mularn, Haggerfel and Fort Veldon, the hidden folk in the western woods and the wood-eaters' hive "
             "in the south. Two signs have come to the vale at once: hounds that howl at the north-west, where a wolf as big as a horse "
             "leaves frost in its tracks, and a dragon-preacher at the Vendo Caverns, teaching the vendo to paint a red eye.")
HOUND = mob(60164906, "phantom hound", (8, 10), guild="running before the winter")
WOLFH = mob(60165108, "rabid wolfhound", (9, 11))
VW = mob(60167594, "vendo warrior", (8, 10), guild="the Red Eye")
VS = mob(60167590, "vendo shaman", (9, 10), guild="the Red Eye")
SEER = {"template": 60157473, "model": 157, "guild": "the Volur of Haggerfel"}
HUSCARL = {"template": 60157473, "model": 160, "equipment": "SvasudGuard", "guild": "King Eirik's Huscarls"}

FALLS = P(260, 660)
d['chains'].append(random_chain('md_moon_howler', 'The Moon-Howler', [9, 12],
    "At moonrise the hounds of the vale howl at the north-west - and something answers from Darkness Falls...", 'm1', [
    {"id": "m1", "type": "cull", "name": "The Fleeing Hounds", "objective": "Turn the hounds running before the Moon-Howler",
     "announce": "Every hound in the vale is running from Darkness Falls tonight - and they'll tear through anyone in the way! Turn them!",
     "center": FALLS, "radius": 90, "time_s": 900, "kill": 12, "alive": 6, "mobs": [HOUND, HOUND, WOLFH],
     "success": "The hounds scatter - and in the moonlight above the falls, the thing they were running from comes down the rocks.",
     "fail": "The hounds run down into the vale, and the Moon-Howler follows them.", "on_success": "m2", "on_fail": "end",
     "reward": R(12, 90, 8)},
    {"id": "m2", "type": "boss", "name": "the Moon-Howler", "objective": "Bring down the Moon-Howler",
     "announce": "The Moon-Howler: a grey wolf as big as a horse, frost smoking off its fur. It howls at the moon, and the moon seems to flinch. A fight for the whole vale - bring friends.",
     "center": FALLS, "radius": 110, "time_s": 1500,
     "path": [P(260, 660), P(200, 520), P(330, 430), P(480, 560), P(420, 760), P(260, 660)],
     "boss": {"template": 60166676, "name": "the Moon-Howler", "level": 13, "size": 85, "pos": FALLS, "health_mult": 4,
              "guild": "out of the endless winter"},
     "adds": {"every_s": 40, "count": 2, "mobs": [HOUND, WOLFH]},
     "success": "The Moon-Howler falls, and the frost on its fur doesn't melt. Far in the north-west, something answers its last howl.",
     "fail": "The Moon-Howler goes back up into the mountains, and the vale's hounds howl till dawn.", "on_success": "end",
     "on_fail": "end", "reward": R(30, 220, 20, ["nu100_moon_howler_s_frost_fang", "nu100_moonrise_mantle"], 40)},
    ], time="night"))

MOUTH = P(690, 230)
d['chains'].append(random_chain('md_red_eye_sermon', 'The Red-Eye Sermon', [8, 11],
    "Drums at the Vendo Caverns - the vendo are gathering to hear the dragon's word...", 's1', [
    {"id": "s1", "type": "defend", "name": "Breaking the Sermon", "objective": "Keep Seeress Asa alive while she breaks the sermon",
     "announce": "The vendo are gathering at the Vendo Caverns to hear a dragon-preacher! Seeress Asa of Haggerfel has gone to break his sermon with the old songs - keep her alive!",
     "center": MOUTH, "radius": 70, "duration_s": 180, "protect": dict(SEER, name="Seeress Asa", level=10, pos=MOUTH, health_mult=8),
     "waves": {"every_s": 25, "count": 3, "from": [P(650, 200), P(740, 260), P(700, 300)], "mobs": [VW, VS]},
     "thanks": "\"The old songs are older than his dragon. They remember.\"",
     "success": "The drums stop. The vendo look at each other - and their red-eyed shaman shrieks and charges.",
     "fail": "Asa falls, and the sermon goes on into the night.", "on_success": "s2", "on_fail": "end", "reward": R(12, 90, 8)},
    {"id": "s2", "type": "boss", "name": "the Red-Eye Shaman", "objective": "Defeat the Red-Eye Shaman",
     "announce": "The Red-Eye Shaman, a dragon's eye painted across his whole face: 'The Mother sees you!'",
     "center": MOUTH, "radius": 70, "time_s": 1200,
     "boss": {"template": 60167590, "name": "the Red-Eye Shaman", "level": 12, "size": 60, "pos": MOUTH, "health_mult": 3, "guild": "of the Red Eye"},
     "adds": {"every_s": 40, "count": 2, "mobs": [VW]},
     "success": "The shaman falls, and the vendo wash the red paint off their fetishes in the stream.", "fail": "The vendo carry their shaman back into the caves, singing.",
     "on_success": "end", "on_fail": "end", "reward": R(25, 180, 14, ["nu100_red_eye_fetish"], 35)},
    ]))
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
