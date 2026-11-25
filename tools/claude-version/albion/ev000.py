"""Camelot Hills' dynamic events (claude 2026-11-24, "Albion - the plan"): the four old chains moved onto the new layout and
tied to the zone's arcs (the Road Gang, the Crimson's barrows, the ant ridge, the spriggarn hills), and three new ones:
the Crimson Rite (the zone's set-piece, a boss hunt at night at Mithra's Tomb), the Hunt Rides (the Difwych brothers' hunt
raises Grugyn Silver-Bristle, the Twrch Trwyth's son) and the Door at Darkness Falls. Writes the zone's events file.
  python ev000.py <in zone000 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, move_stage, shift_levels, random_chain, occupy
Z = 0
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("The green hills below Camelot. Arthur is gone to Avalon and the Round Table's survivors keep the realm - but the roads "
             "are full of bandits paid in red-sealed silver, the dead are walking in the barrow fields, and in Mithra's old tomb the "
             "Crimson, Morgana le Fay's mortal cult, has begun its first rite under Camelot's nose.")
ch = {c['id']: c for c in d['chains']}

# ------------------------------------------------------------------ the old chains, moved
b = ch['camelot_hills_bandit_hollow']
b['title'] = "The Road Gang's Toll"
b['hint'] = "Smoke from the Road Gang's camp in the hills east of the crossroads..."
shift_levels(b, [6, 9], 0)
for st in b['stages']:
    if st['id'] in ('a1', 'a2'):
        move_stage(st, P, (850, 1010))
    else:
        move_stage(st, P, (560, 830))
b['stages'][0]['name'] = "Clear the Road Gang's Camp"
b['stages'][0]['objective'] = "Clear the Road Gang's camp in the hills"
b['stages'][1]['announce'] = "Ranulf Blackhand, the Road Gang's paymaster, comes out with a purse of red-sealed silver on his belt. 'Paid to keep the Watch busy, friend. Nothing personal.'"
b['stages'][2]['name'] = "Ranulf's Men Hold the Camelot Road"
b['stages'][2]['objective'] = "Drive the bandits off the Camelot road"
b['stages'][2]['announce'] = "Ranulf Blackhand's bandits have come down to the Camelot road and set a toll. Nobody passes without paying - in coin or in blood."

w = ch['camelot_hills_barrow_wakes']
w['hint'] = "Red lights in the barrow fields, and the dead are walking..."
shift_levels(w, [9, 11], 4)
for st in w['stages']:
    move_stage(st, P, (1060, 1120) if st['id'] == 'd1' else (1100, 1150) if st['id'] in ('d2', 'd3') else (850, 1150))
w['stages'][0]['objective'] = "Protect Brother Aelred, who is unsaying the Crimson's call over the barrow"
w['stages'][0]['announce'] = "Brother Aelred, Brother Idris's curate, has come to unsay the red-robes' call over the barrow. The dead have heard him."
w['stages'][3]['name'] = "The Dead Hold the Road to Prydwen Keep"
w['stages'][3]['objective'] = "Drive the dead off the road to Prydwen Keep"

a = ch['camelot_hills_ant_nest']
a['hint'] = "Sergeant Wystan is gathering the Wardens in Cotswold to burn the ant queen's mound."
g1 = a['stages'][0]
g1['path'] = g1['path'] + path(P, g1['path'][-1], (1110, 560))
for st in a['stages']:
    if st['id'] in ('g2', 'g3'):
        move_stage(st, P, (1110, 560))
a['giver']['guild'] = 'the Wardens of Cotswold'
for gd in a['guards']:
    gd['guild'] = 'the Wardens of Cotswold'

o = ch['camelot_hills_orchard_spriggarn']
o['giver']['guild'] = 'the Wardens of Cotswold'
for gd in o['guards']:
    gd['guild'] = 'the Wardens of Cotswold'
o['giver']['greet'] = "The spriggarn are stripping the Cotswold orchards bare - and dancing on what's left. The Reeve wants them taught manners. Will you come? Tell me when you're [ready]."

# ------------------------------------------------------------------ new: the Crimson Rite (the set-piece)
ACO = mob(12284, "crimson acolyte", (11, 13), guild="the Crimson")
INI = mob(12075, "crimson initiate", (12, 14), guild="the Crimson")
UFI = mob(12620, "undead filidh", (11, 12))
ZOM = mob(12585, "rotting zombie", (11, 12))
RITE, TOMB = P(1255, 1060), P(1330, 995)
WATCH = {"template": 60167630, "model": 28, "equipment": "38762ab0-5f99-47cd-85b0-0bfaa37d71f9", "guild": "the Pendragon's Watch"}
d['chains'].append(random_chain('ch_crimson_rite', 'The Crimson Rite', [11, 14],
    "Chanting under the eastern hill, and red light in the mouth of Mithra's Tomb...", 'r1', [
    {"id": "r1", "type": "defend", "name": "The Rite Stone", "objective": "Keep Brother Cynan alive while he breaks the rite stone",
     "announce": "The Crimson are holding their rite tonight! Brother Cynan of the eastern hamlet has gone to break the rite stone in the barrow fields - and the dead are rising to stop him.",
     "center": RITE, "radius": 70, "duration_s": 180,
     "protect": {"name": "Brother Cynan", "template": 60167630, "model": 32, "equipment": "eab1762c-33e7-4620-9e02-985d820d0369",
                 "level": 12, "pos": RITE, "health_mult": 8, "guild": "the Church of Albion"},
     "waves": {"every_s": 25, "count": 3, "from": [P(1290, 1020), P(1220, 1100), P(1300, 1100)], "mobs": [UFI, ZOM, ACO]},
     "thanks": "\"It's broken! Now - the tomb. Whoever leads the rite is still chanting.\"",
     "success": "The rite stone cracks. In the tomb mouth the chanting falters, then starts again, louder.",
     "fail": "Brother Cynan falls, and the rite goes on into the night.", "on_success": "r2", "on_fail": "o1", "reward": R(10, 80, 6)},
    {"id": "r2", "type": "cull", "name": "The Tomb Mouth", "objective": "Break the Crimson at the mouth of Mithra's Tomb",
     "announce": "To the tomb! Cut down the red-robes before they finish the rite!", "center": TOMB, "radius": 60, "time_s": 1200,
     "kill": 14, "alive": 7, "mobs": [ACO, ACO, INI], "success": "The red-robes break - and the Hierophant comes up out of the dark.",
     "fail": "The Crimson hold the tomb.", "on_success": "r3", "on_fail": "o1", "reward": R(12, 90, 8)},
    {"id": "r3", "type": "boss", "name": "Hierophant Cadan", "objective": "Defeat Hierophant Cadan of the Crimson",
     "announce": "Hierophant Cadan, in red over a Roman breastplate: 'The Lady sleeps in no one's shadow. Not even her brother's.' This is a fight for a group.",
     "center": TOMB, "radius": 70, "time_s": 1200,
     "boss": {"template": 12075, "name": "Hierophant Cadan", "level": 15, "size": 60, "pos": TOMB, "health_mult": 3, "guild": "Hierophant of the Crimson"},
     "adds": {"every_s": 40, "count": 2, "mobs": [ACO, UFI]},
     "success": "Hierophant Cadan falls on the tomb's threshold, and every dead thing in the barrow fields lies down. The Watch will hear of this in Camelot.",
     "fail": "Cadan finishes the rite. Something under the hill has heard.", "on_success": "end", "on_fail": "o1",
     "reward": R(30, 200, 16, ["nu000_hierophant_s_red_cord"], 35)},
    occupy("o1", "The Crimson Hold the Barrow Road", "Drive the Crimson and their dead off the barrow road",
           "The rite went on. The Crimson and their risen dead have come out onto the barrow road and turn back anyone who passes.",
           P(1180, 900), [ACO, UFI, ZOM], {"template": 12075, "name": "Crimson rite-keeper", "level": 14, "health_mult": 2}),
    ], time="night"))

# ------------------------------------------------------------------ new: the Hunt Rides
HOUND = mob(12137, "hound of the Difwych", (9, 11), size=58)
HUNT = mob(12308, "Difwych huntsman", (10, 11), guild="the Difwych Hunt")
HILL = P(1360, 520)
d['chains'].append(random_chain('ch_hunt_rides', 'The Hunt Rides', [9, 12],
    "Horns in the eastern hills, and hounds baying at something that isn't there...", 'h1', [
    {"id": "h1", "type": "cull", "name": "The Hunt in Full Cry", "objective": "Turn the Difwych hunt in the eastern hills",
     "announce": "The Difwych hunt is out in full cry across the eastern hills, chasing a boar twenty years gone - and running down anyone in the way.",
     "center": HILL, "radius": 80, "time_s": 1200, "kill": 14, "alive": 7, "mobs": [HOUND, HOUND, HUNT],
     "success": "The hounds scatter - and something answers their horns. A boar, silver-bristled, as big as a cart.",
     "fail": "The hunt rides on.", "on_success": "h2", "on_fail": "o1", "reward": R(12, 90, 8)},
    {"id": "h2", "type": "boss", "name": "Grugyn Silver-Bristle", "objective": "Bring down Grugyn Silver-Bristle",
     "announce": "Grugyn Silver-Bristle, son of the Twrch Trwyth, out of the old tales and into the hills: the brothers' horns have called up the boar they never caught. Bring friends.",
     "center": HILL, "radius": 80, "time_s": 1200,
     "boss": {"template": 12746, "name": "Grugyn Silver-Bristle", "level": 13, "size": 75, "pos": HILL, "health_mult": 3},
     "adds": {"every_s": 45, "count": 2, "mobs": [mob(12246, "young boar", (9, 10)), HOUND]},
     "success": "Grugyn falls, and the horns go quiet in the hills. For one night, at least, the Difwych hunt is over.",
     "fail": "Grugyn crashes away into the hills, the hunt behind him.", "on_success": "end", "on_fail": "o1",
     "reward": R(25, 180, 14, ["nu000_silver_bristle_charm"], 35)},
    occupy("o1", "The Hunt Holds the Ridge Road", "Drive the Difwych hounds off the ridge road",
           "The Difwych hounds have spread down onto the ridge road and run down anyone they find.",
           P(1150, 720), [HOUND, HUNT], {"template": 12308, "name": "Difwych whipper-in", "level": 12, "health_mult": 2}),
    ]))

# ------------------------------------------------------------------ new: the Door at Darkness Falls
MANES = mob(12370, "manes demon", (11, 13))
GRUM = mob(12359, "grumoz demon", (12, 13))
DOOR = P(1240, 1300)
d['chains'].append(random_chain('ch_df_door', 'The Door at Darkness Falls', [11, 14],
    "Brimstone on the wind below Darkness Falls - the door is cracking again...", 'f1', [
    {"id": "f1", "type": "defend", "name": "Hold the Door", "objective": "Keep Sergeant Ffion alive while the Watch shores up the door",
     "announce": "The door to Darkness Falls is cracking! Sir Barwick's sergeant, Ffion, is holding it with the Watch while the masons work - and the demons are coming through.",
     "center": DOOR, "radius": 70, "duration_s": 180,
     "protect": dict(WATCH, name="Sergeant Ffion", level=14, pos=DOOR, health_mult=8),
     "waves": {"every_s": 22, "count": 3, "from": [P(1270, 1340), P(1290, 1310), P(1250, 1350)], "mobs": [MANES, MANES, GRUM]},
     "thanks": "\"Sir Barwick will want to hear of this. Barwick, mind. Not Berwick.\"",
     "success": "The masons are done - and the thing that was pushing hardest comes through before the door closes.",
     "fail": "Sergeant Ffion falls and the door swings open.", "on_success": "f2", "on_fail": "o1", "reward": R(12, 90, 8)},
    {"id": "f2", "type": "boss", "name": "Gorgoth the Door-Breaker", "objective": "Defeat Gorgoth the Door-Breaker",
     "announce": "Gorgoth the Door-Breaker, a grumoz the size of a haywain: 'BERWICK.' Bring friends.",
     "center": DOOR, "radius": 70, "time_s": 1200,
     "boss": {"template": 12359, "name": "Gorgoth the Door-Breaker", "level": 15, "size": 65, "pos": DOOR, "health_mult": 3},
     "adds": {"every_s": 40, "count": 2, "mobs": [MANES]},
     "success": "Gorgoth bursts like a coal in a fire. The door holds another month.",
     "fail": "Gorgoth breaks through.", "on_success": "end", "on_fail": "o1",
     "reward": R(25, 180, 14, ["nu000_door_breaker_s_horn"], 35)},
    occupy("o1", "Demons Hold the Barrow Road", "Drive the demons off the road below Darkness Falls",
           "Demons are loose below Darkness Falls and have taken the road.", P(1120, 1250), [MANES, GRUM],
           {"template": 12359, "name": "grumoz warleader", "level": 14, "health_mult": 2}),
    ]))

json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
