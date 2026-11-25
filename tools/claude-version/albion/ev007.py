"""Llyn Barfog's dynamic events (claude 2026-11-24, "Albion - the plan", round 4): the four old chains kept and brought up to the
zone's Elite levels, a new night one - the Still Night (the lake goes still and the Gate stirs) - and the Lake Host's campaign:
the four shores' assaults and counters and the raid at the Gate of Annwn (Morgana le Fay: MorganaRaid.cs), armed by
AlbionCampaign.cs. Writes the zone's events file."""
import json, sys
from evcommon import mkP, R, mob, shift_levels, random_chain
from evcamp import giver, assault, cull, wards, hold, boss_stage, counter, around
Z = 7
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Llyn Barfog, the bearded lake, where the Lady's white cattle came up out of the water, Arthur's horse left its "
             "hoof-print in the stone, and Arthur dragged the Afanc out of the lake. Morgana le Fay sits at the Gate of Annwn on the "
             "south shore now, and her hounds, her cythraul and her Crimson hold the shores. Sir Percival's Lake Host means to take "
             "them back.")
SHIFT = {"llyn_barfog_renegades": ([45, 50], 30), "llyn_barfog_hounds_of_annwn": ([45, 47], 25),
         "llyn_barfog_unshriven": ([46, 48], 18), "llyn_barfog_adder_shallows": ([46, 46], 36)}
for c in d['chains']:
    if c['id'] in SHIFT:
        lv, sh = SHIFT[c['id']]
        shift_levels(c, lv, sh)

LOOK = {"template": 60167630, "model": 28, "equipment": "38762ab0-5f99-47cd-85b0-0bfaa37d71f9", "guild": "the Knights of the Lake"}
MAID = {"template": 60167630, "model": 38, "equipment": "eab1762c-33e7-4620-9e02-985d820d0369", "guild": "the Maidens of the Lake"}
INI = mob(12075, "crimson acolyte", (45, 47), size=50, guild="the Crimson")
GATEK = mob(12075, "crimson gatekeeper", (46, 48), guild="the Crimson")
GUARD = mob(12075, "guardian of Morgana", (47, 49), model=1900, guild="Morgana's Guard")
FAY = mob(12075, "fay knight", (48, 50), model=1900, guild="Morgana's Guard")
HOUND = mob(12999, "hound of Annwn", (45, 47), guild="the Hunt of Annwn")
CYTH = mob(13001, "cythraul", (45, 47), guild="out of Annwn")
WCYTH = mob(12129, "wicked cythraul", (47, 49), guild="out of Annwn")
GWR = mob(13014, "gwr-drwgiaid", (45, 47), guild="out of Annwn")
NECRO = mob(12117, "necromancer", (46, 48), guild="the Crimson")
SHADE = mob(12016, "shade of Camlann", (47, 49), model=485, guild="Mordred's host")

# ---------------------------------------------------------------- the Still Night (night): the lake goes still, the Gate stirs
SHORE = P(700, 1120)
d['chains'].append(random_chain('lb_still_night', 'The Still Night', [46, 49],
    "The lake has gone still as glass - and on the south shore, the Gate of Annwn is stirring...", 'n1', [
    {"id": "n1", "type": "defend", "name": "The Moving Water", "objective": "Keep Maiden Celemon alive while she sings the lake moving",
     "announce": "Llyn Barfog has gone still - and while the lake is still, Morgana's Gate can open! Maiden Celemon of the Lake is singing the water awake. Keep her alive!",
     "center": SHORE, "radius": 70, "duration_s": 200, "protect": dict(MAID, name="Maiden Celemon", level=48, pos=SHORE, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": around(P, (700, 1150)), "mobs": [HOUND, CYTH, SHADE]},
     "thanks": "\"Listen - the water's moving. The Gate can't open on moving water.\"",
     "success": "The lake ripples, then rolls - and something that came halfway through the Gate is caught on the shore.",
     "fail": "Celemon falls, and the lake stays still till dawn.", "on_success": "n2", "on_fail": "end", "reward": R(14, 160, 12)},
    {"id": "n2", "type": "boss", "name": "the Shade of Camlann", "objective": "Defeat the Shade of Camlann",
     "announce": "A knight in black mail, half-there, still bleeding from the last battle: 'I fell at Camlann. I don't stay fallen.' Bring friends.",
     "center": SHORE, "radius": 70, "time_s": 1200,
     "boss": {"template": 12016, "name": "the Shade of Camlann", "level": 51, "model": 485, "size": 70, "pos": SHORE, "health_mult": 4,
              "guild": "Mordred's host"},
     "adds": {"every_s": 40, "count": 2, "mobs": [SHADE, HOUND]},
     "success": "The shade comes apart like mist on moving water.", "fail": "The shade walks back into the Gate, and something else comes out.",
     "on_success": "end", "on_fail": "end", "reward": R(28, 260, 20, ["nu007_camlann_shade_s_gorget"], 40)},
    ], time="night"))

# ---------------------------------------------------------------- the Lake Host's campaign
CP = {1: P(1000, 520), 2: P(560, 430), 3: P(260, 820), 4: P(500, 1300)}
SEAT = P(760, 1230)
LV = {1: [44, 47], 2: [45, 48], 3: [46, 49], 4: [47, 50]}
KNIGHTS = [dict(LOOK, name="knight of the Lake", level=48, count=3)]
PREFIX = "lb_cp"
d['chains'].append(assault(PREFIX, 1, "The Lake Host at the Afanc's Shore", LV[1], 6,
    "The Banner-Knight is forming the Lake Host up for the Afanc's Shore.",
    giver(LOOK, "Banner-Knight Lamorak", 50, P(930, 640),
          "The Afanc's Shore - the north shore, where Arthur dragged the beast out. The Crimson hold it now. Six at least, and say [forward].",
          "forward", "To the shore! Break their post - then their warden!", "The Lake Host holds the Afanc's Shore - and the next thirty minutes are ours.",
          "Fall back to the merchants! We'll go again."), KNIGHTS, [
    cull("Break the Afanc's Shore", "Break Morgana's post on the Afanc's Shore",
         "The Lake Host is at the Afanc's Shore! Break the post!", CP[1], [INI, HOUND, GATEK], 24, "s2"),
    boss_stage("s2", "Red-Key Warden Iddawc", "Red-Key Warden Iddawc, who carried the false word at Camlann: 'Every war needs a liar. I was Arthur's. Now I'm hers.'",
               CP[1], {"template": 12075, "name": "Red-Key Warden Iddawc", "level": 50, "size": 62, "health_mult": 4, "guild": "of the Crimson"},
               [INI, HOUND], "Iddawc falls among his red keys. The north shore is the Lake's.")]))
d['chains'].append(assault(PREFIX, 2, "The Lake Host at the Bwgan Hills", LV[2], 6,
    "Sir Lamorak is forming the Lake Host up for the Bwgan Hills.",
    giver(LOOK, "Sir Lamorak", 51, P(900, 470),
          "The Bwgan Hills. The Crimson have ward-stones up there, and a necromancer raising the hills' dead to stand in front of them. Six at least, and say [forward].",
          "forward", "Up the hills! Hold the three ward-stones, then find the necromancer!",
          "The Lake Host holds the Bwgan Hills.", "Back down the hills! We'll go again."), KNIGHTS, [
    cull("Break the Bwgan Hills", "Break the Crimson's post in the Bwgan Hills",
         "The Lake Host is in the Bwgan Hills! Break the post!", CP[2], [INI, CYTH, NECRO, GATEK], 26, "s2"),
    wards("s2", "The Ward-Stones", "Hold the three ward-stones at once while the Maidens unbind them",
          "Three red-keyed ward-stones hold the hills for Morgana - stand at all three at once while the Maidens sing them open!",
          CP[2], [P(520, 400), P(600, 410), P(560, 470)], ["the north stone", "the east stone", "the south stone"], [INI, NECRO], "s3",
          "pennant of the Lake"),
    {**boss_stage("s3", "Necromancer Gwyddno", "Necromancer Gwyddno: 'The hills are full of the dead. They all owe her something.'",
                  CP[2], {"template": 12117, "name": "Necromancer Gwyddno", "level": 51, "size": 60, "health_mult": 4.5, "guild": "of the Crimson"},
                  [CYTH, NECRO], "Gwyddno falls, and the dead in the hills lie down again.")}]))
d['chains'].append(assault(PREFIX, 3, "The Lake Host at the Western Shore", LV[3], 6,
    "Dame Lionors is forming the Lake Host up for the Western Shore.",
    giver(LOOK, "Dame Lionors", 51, P(500, 560),
          "The Western Shore. Morgana's guard hold it, and the hounds run there. We take it and we hold it - the Maidens' banner goes up, and they'll come at it. Six at least, and say [forward].",
          "forward", "To the shore! Break them, then hold the banner!", "The Lake Host holds the Western Shore.",
          "Fall back! We'll go again."), KNIGHTS, [
    cull("Break the Western Shore", "Break Morgana's guard on the Western Shore",
         "The Lake Host is on the Western Shore! Break the guard!", CP[3], [GUARD, HOUND, WCYTH], 26, "s2"),
    hold("s2", "The Maidens' Banner", "Keep Maiden Laudine alive while the banner goes up",
         "Maiden Laudine is raising the Lake's banner on the Western Shore - and the hunt is coming for it!",
         CP[3], dict(MAID, name="Maiden Laudine", level=49, health_mult=8), around(P, (260, 820)), [HOUND, GWR, WCYTH], "s3",
         "\"It's up. Let her see it from her Gate.\""),
    boss_stage("s3", "Gwrgi Garwlwyd", "Gwrgi Garwlwyd, the dog-man of Annwn, comes up the shore on all fours: 'The Huntsman's dead. I'm hungrier than he was.'",
               CP[3], {"template": 12999, "name": "Gwrgi Garwlwyd", "level": 52, "model": 24, "size": 75, "health_mult": 4.5, "guild": "of the Hunt of Annwn"},
               [HOUND, GWR], "Gwrgi falls, and every hound on the shore howls once and runs.")]))
d['chains'].append(assault(PREFIX, 4, "The Lake Host at the Fay Wood", LV[4], 8,
    "Sir Percival's own squire is forming the Lake Host up for the Fay Wood.",
    giver(LOOK, "Squire Dindrane", 50, P(320, 1040),
          "The Fay Wood. Morgana's kin - green steel and glamour - and the last thing between us and the Gate. Eight at least, and say [forward].",
          "forward", "Into the wood! Break the fay rings, then the fay lord!", "The Lake Host holds the Fay Wood - the Gate is in sight.",
          "Out of the wood! We'll go again."), KNIGHTS, [
    cull("Break the Fay Wood", "Break Morgana's knights in the Fay Wood",
         "The Lake Host is in the Fay Wood! Break the knights!", CP[4], [FAY, GUARD, WCYTH], 28, "s2"),
    wards("s2", "The Fay Rings", "Stand in the three fay rings at once while the Maidens break the glamour",
          "Three fay rings hold the wood's glamour - stand in all three at once and the Maidens will break it!",
          CP[4], [P(460, 1270), P(540, 1280), P(500, 1340)], ["the oak ring", "the thorn ring", "the toadstool ring"], [FAY, WCYTH], "s3",
          "pennant of the Lake"),
    boss_stage("s3", "Guiomar the Fay Lord", "Guiomar, Morgana's first love and still her knight, in green steel: 'She was a girl in Camelot once. Arthur's court made her this. Remember that, when you reach her.'",
               CP[4], {"template": 12075, "name": "Guiomar the Fay Lord", "level": 53, "model": 1900, "size": 66, "health_mult": 5, "guild": "Lord of the Fay Wood"},
               [FAY, GUARD], "Guiomar falls, and the glamour goes out of the wood like a held breath. Through the trees: the Gate of Annwn.")]))

KN = dict(LOOK, name="Banner-Knight of the Lake", level=50)
d['chains'].append(counter(PREFIX, 1, "the Afanc's Shore", "Morgana's host", LV[1], CP[1], KN, around(P, (1000, 520)), [INI, HOUND, GATEK], title="Morgana's Host Strikes Back at The Afanc's Shore"))
d['chains'].append(counter(PREFIX, 2, "the Bwgan Hills", "Morgana's host", LV[2], CP[2], KN, around(P, (560, 430)), [CYTH, NECRO, INI], title="Morgana's Host Strikes Back at The Bwgan Hills"))
d['chains'].append(counter(PREFIX, 3, "the Western Shore", "Morgana's host", LV[3], CP[3], KN, around(P, (260, 820)), [HOUND, GWR, GUARD], title="Morgana's Host Strikes Back at The Western Shore"))
d['chains'].append(counter(PREFIX, 4, "the Fay Wood", "Morgana's host", LV[4], CP[4], KN, around(P, (500, 1300)), [FAY, WCYTH, GUARD], title="Morgana's Host Strikes Back at The Fay Wood"))

# ---------------------------------------------------------------- the raid: the Gate of Annwn
d['chains'].append({
    "id": "lb_gate_of_annwn", "title": "The Gate of Annwn", "levels": [48, 52], "manual": True, "bots": 16, "bot_min_level": 47,
    "min_people": 10, "hint": "Sir Percival himself is gathering the Lake Host before the Gate of Annwn.", "rest_s": 15, "start": "g1",
    "giver": giver(LOOK, "Sir Percival", 60, P(600, 1250),
                   "The Gate of Annwn. Morgana is in it - and behind her, her nephew's ghost, and the beast Arthur killed. Two groups at least - ten, bots and all - and healers, and curers. Then say [for the Lady].",
                   "for the Lady", "For the Lady! Healers to the back, curers by them - and whatever comes out of that Gate, hold!",
                   "The Gate is shut. Llyn Barfog is the Lady's again.", "Back! Back to the wood! We'll come again.", hp=8, size=58),
    "guards": [dict(LOOK, name="knight of the Lake", level=50, count=4), dict(MAID, name="maiden of the Lake", level=48, count=2)],
    "stages": [
        {"id": "g1", "type": "boss", "name": "Morgana le Fay", "objective": "Defeat Morgana le Fay",
         "announce": "Morgana le Fay steps out of the Gate of Annwn, in a black crown, smiling: 'My brother's knights. How sweet. Do you know what's behind me? You will.'",
         "center": SEAT, "radius": 90, "time_s": 2700,
         "boss": {"template": 700000001, "name": "Morgana le Fay", "level": 60, "size": 60, "health_mult": 20, "guild": "Queen of Annwn's Gate"},
         "adds": {"every_s": 55, "count": 3, "mobs": [GUARD, FAY, HOUND]},
         "success": "Morgana screams - not in pain; in rage - and is gone, into the Gate, and the Gate closes behind her like a door in a wind. Across the lake the mist begins to lift.",
         "fail": "Morgana drives the Lake Host from the Gate.", "on_success": "end", "on_fail": "end",
         "reward": {"xp_pct": 60, "copper_per_level": 600, "tokens": 60,
                    "items": [{"id": "lb007_morgana_s_black_crown", "gold_chance": 60, "silver_chance": 25},
                              {"id": "lb007_mordred_s_wrath", "gold_chance": 60, "silver_chance": 25},
                              {"id": "lb007_afanc_tooth_charm", "gold_chance": 60, "silver_chance": 25}]}}]})

json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
