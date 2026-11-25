"""Raumarik's dynamic events (claude 2026-11-25, "Midgard - the plan", round 4): the three old chains kept, and the King's March:
the four posts' assaults and counters and the raid at Hati's Howe (Hati, the wolf that hunts the moon: MidgardRaids.cs), armed by
AlbionCampaign.cs (MidgardCampaigns.Winter). Writes the zone's events file."""
import json, sys
from evcommon import mkP, R, mob, random_chain
from evcamp import giver, assault, cull, wards, hold, boss_stage, counter, around
Z = 108
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Raumarik: the frozen north, where the winter never ends. Hati, the wolf that hunts the moon - Fenrir's son - waits in his "
             "howe in the west for the moon to run close enough to catch; when he catches it, the long winter comes for all of Midgard. "
             "His host holds the north - the fenrir soldiers and their mystics, the winterwolves, the wraiths and wights - and King "
             "Eirik's Host means to take it back.")
LOOK = {"template": 60157473, "model": 160, "equipment": "SvasudGuard", "guild": "King Eirik's Host"}
SEER = {"template": 60157473, "model": 168, "guild": "the Seithkona Circle"}
SOLD = mob(60160797, "fenrir soldier", (47, 49), guild="Hati's Host")
MYST = mob(60160797, "fenrir mystic", (48, 50), model=462, guild="Hati's Host")
WOLF = mob(60165623, "savage winterwolf", (47, 49), guild="Hati's Host")
WW = mob(60167987, "winter wolf", (45, 47), guild="Hati's Host")
WRAITH = mob(60167978, "windswept wraith", (47, 49), guild="of the endless winter")
WIGHT = mob(60159159, "chillsome wight", (47, 49), guild="of the endless winter")
LICH = mob(60161108, "frore lich", (49, 51), guild="of the endless winter")
ICE = mob(60162353, "icestrider chiller", (45, 47), guild="of the fells")
WEAVE = mob(60162357, "icestrider frostweaver", (46, 48), guild="of the fells")

CP = {1: P(1300, 471), 2: P(850, 650), 3: P(650, 1100), 4: P(450, 800)}
SEAT = P(320, 600)
LV = {1: [45, 48], 2: [46, 49], 3: [47, 50], 4: [48, 51]}
HUSC = [dict(LOOK, name="huscarl of the King", level=48, count=3)]
PREFIX = "rk_cp"
d['chains'].append(assault(PREFIX, 1, "The King's March on the Icestrider Fells", LV[1], 6,
    "The Banner-Huscarl is forming the King's Host up for the Icestrider Fells.",
    giver(LOOK, "Banner-Huscarl Thorvid", 50, P(1180, 800),
          "The Icestrider Fells, north-east. Hati's soldiers hold a post up there with the icestriders round them. Six at least, and say [forward].",
          "forward", "Up the fells! Break their post - then their mystic!", "The King's Host holds the Icestrider Fells - and the next thirty minutes are ours.",
          "Back to the camp! We'll go again."), HUSC, [
    cull("Break the Fells", "Break Hati's post on the Icestrider Fells",
         "The King's Host is on the Icestrider Fells! Break the post!", CP[1], [SOLD, WW, ICE, WEAVE], 24, "s2"),
    boss_stage("s2", "Frost-Mystic Hrimgerd", "Frost-Mystic Hrimgerd, ice in her braids, a wolf's skull on her staff: 'The fells are the first thing he'll see when he catches her. He'll want them clean.'",
               CP[1], {"template": 60160797, "name": "Frost-Mystic Hrimgerd", "level": 50, "model": 462, "size": 62, "health_mult": 4, "guild": "of Hati's Host"},
               [SOLD, WW], "Hrimgerd falls in the snow. The fells are the King's.")]))
d['chains'].append(assault(PREFIX, 2, "The King's March on the Wraith Moor", LV[2], 6,
    "Huscarl Thorvid is forming the King's Host up for the Wraith Moor.",
    giver(LOOK, "Huscarl Thorvid", 51, P(1050, 600),
          "The Wraith Moor. The dead of the endless winter walk there, and Hati's soldiers have three frost-stones up to keep them walking. Six at least, and say [forward].",
          "forward", "Onto the moor! Hold the three frost-stones, then find the lich!", "The King's Host holds the Wraith Moor.",
          "Back off the moor! We'll go again."), HUSC, [
    cull("Break the Wraith Moor", "Break Hati's post on the Wraith Moor",
         "The King's Host is on the Wraith Moor! Break the post!", CP[2], [WRAITH, WIGHT, SOLD], 26, "s2"),
    wards("s2", "The Frost-Stones", "Hold the three frost-stones at once while the seithkona break them",
          "Three frost-stones keep the winter's dead walking - stand at all three at once while the seithkona break them!",
          CP[2], [P(820, 620), P(880, 630), P(850, 690)], ["the north stone", "the east stone", "the south stone"], [WIGHT, WRAITH], "s3",
          "banner of the King"),
    boss_stage("s3", "the Frore Lich", "The Frore Lich, a dead jarl in a crown of ice: 'I froze at the first winter. I'll see the last.'",
               CP[2], {"template": 60161108, "name": "the Frore Lich", "level": 51, "size": 66, "health_mult": 4.5, "guild": "of the endless winter"},
               [WRAITH, WIGHT], "The lich cracks like river-ice, and the moor's dead lie down.")]))
d['chains'].append(assault(PREFIX, 3, "The King's March on the Winterwolf Run", LV[3], 6,
    "Shield-Maiden Sigrun is forming the King's Host up for the Winterwolf Run.",
    giver(LOOK, "Shield-Maiden Sigrun", 51, P(820, 950),
          "The Winterwolf Run. The packs run there for Hati, and we take it and we hold it - the King's banner goes up, and they'll come for it. Six at least, and say [forward].",
          "forward", "Into the run! Break them, then hold the banner!", "The King's Host holds the Winterwolf Run.",
          "Fall back! We'll go again."), HUSC, [
    cull("Break the Winterwolf Run", "Break the packs on the Winterwolf Run",
         "The King's Host is in the Winterwolf Run! Break the packs!", CP[3], [WOLF, WOLF, SOLD], 26, "s2"),
    hold("s2", "The King's Banner", "Keep Seithkona Alfrun alive while the banner goes up",
         "Seithkona Alfrun is raising the King's banner on the run - and the packs are coming for it!",
         CP[3], dict(SEER, name="Seithkona Alfrun", level=49, health_mult=8), around(P, (650, 1100)), [WOLF, WW, SOLD], "s3",
         "\"It's up. Let him see it from his howe.\""),
    boss_stage("s3", "the Pack-Mother of the Run", "The Pack-Mother, a winterwolf as big as a horse, her muzzle grey with frost: 'My cubs run for Hati. So will yours.'",
               CP[3], {"template": 60165623, "name": "the Pack-Mother of the Run", "level": 52, "size": 85, "health_mult": 4.5, "guild": "of Hati's Host"},
               [WOLF, WW], "The Pack-Mother falls, and every wolf on the run howls once and scatters.")]))
d['chains'].append(assault(PREFIX, 4, "The King's March on the Fenrir Camp", LV[4], 8,
    "Huscarl-Marshal Hallvard's own sword-bearer is forming the King's Host up for the Fenrir Camp.",
    giver(LOOK, "Sword-Bearer Grim", 50, P(620, 760),
          "The Fenrir Camp. Hati's own soldiers - the greater fenrir - and the last thing between us and the howe. Eight at least, and say [forward].",
          "forward", "Into the camp! Break the totems, then their jarl!", "The King's Host holds the Fenrir Camp - the howe is in sight.",
          "Out of the camp! We'll go again."), HUSC, [
    cull("Break the Fenrir Camp", "Break Hati's soldiers in the Fenrir Camp",
         "The King's Host is in the Fenrir Camp! Break the soldiers!", CP[4], [SOLD, MYST, WOLF], 28, "s2"),
    wards("s2", "The Wolf-Totems", "Stand at the three wolf-totems at once while the huscarls bring them down",
          "Three wolf-totems call the camp's courage from Hati himself - stand at all three at once and the huscarls will fell them!",
          CP[4], [P(420, 770), P(480, 780), P(450, 840)], ["the bone totem", "the moon totem", "the blood totem"], [SOLD, MYST], "s3",
          "banner of the King"),
    boss_stage("s3", "Fenrir-Jarl Vargeisl", "Fenrir-Jarl Vargeisl, more wolf than man, in mail of frozen iron: 'Hati is my lord's lord's son. You'll not reach him over me.'",
               CP[4], {"template": 60160797, "name": "Fenrir-Jarl Vargeisl", "level": 53, "size": 70, "health_mult": 5, "guild": "Jarl of the Fenrir Camp"},
               [SOLD, MYST], "Vargeisl falls, and the camp breaks. Through the snow to the west: Hati's Howe.")]))

KN = dict(LOOK, name="Banner-Huscarl of the King", level=50)
d['chains'].append(counter(PREFIX, 1, "the Icestrider Fells", "Hati's host", LV[1], CP[1], KN, around(P, (1300, 471)), [SOLD, WW, ICE], title="Hati's Host Strikes Back at the Icestrider Fells"))
d['chains'].append(counter(PREFIX, 2, "the Wraith Moor", "Hati's host", LV[2], CP[2], KN, around(P, (850, 650)), [WRAITH, WIGHT, SOLD], title="Hati's Host Strikes Back at the Wraith Moor"))
d['chains'].append(counter(PREFIX, 3, "the Winterwolf Run", "Hati's host", LV[3], CP[3], KN, around(P, (650, 1100)), [WOLF, WW, SOLD], title="Hati's Host Strikes Back at the Winterwolf Run"))
d['chains'].append(counter(PREFIX, 4, "the Fenrir Camp", "Hati's host", LV[4], CP[4], KN, around(P, (450, 800)), [SOLD, MYST, WOLF], title="Hati's Host Strikes Back at the Fenrir Camp"))

# ---------------------------------------------------------------- the raid: Hati's Howe
d['chains'].append({
    "id": "rk_hatis_howe", "title": "Hati's Howe", "levels": [50, 54], "manual": True, "bots": 16, "bot_min_level": 47,
    "min_people": 10, "hint": "Huscarl-Marshal Hallvard himself is gathering the King's Host before Hati's Howe.", "rest_s": 15, "start": "h1",
    "giver": giver(LOOK, "Huscarl-Marshal Hallvard", 60, P(430, 640),
                   "Hati's Howe. He's in there, watching the moon - and his brother Skoll will come when he calls, and the winter with him. Two groups at least - ten, bots and all - and healers, and curers. Then say [for the King].",
                   "for the King", "For the King! Healers to the back - and whatever comes out of the north, hold!",
                   "Hati is broken. The moon runs free tonight.", "Back! Back to the camp! We'll come again.", hp=8, size=58),
    "guards": [dict(LOOK, name="huscarl of the King", level=50, count=4), dict(SEER, name="seithkona of the Circle", level=48, count=2)],
    "stages": [
        {"id": "h1", "type": "boss", "name": "Hati, Who Hunts the Moon", "objective": "Defeat Hati, Who Hunts the Moon",
         "announce": "Hati comes out of his howe - a wolf the size of a longship, frost pouring off him, his eyes on the moon and then on you: 'She runs closer every night. You can't stop that. You can only be in my way.'",
         "center": SEAT, "radius": 90, "time_s": 2700,
         "boss": {"template": 60165623, "name": "Hati, Who Hunts the Moon", "level": 60, "size": 120, "health_mult": 20, "guild": "Son of Fenrir"},
         "adds": {"every_s": 55, "count": 3, "mobs": [SOLD, WOLF, WRAITH]},
         "success": "Hati falls in the snow before his howe with a howl that shakes the mountains - and is gone, into the north, his hide torn and his brother with him. Overhead, the moon runs on. Across Raumarik the winter mist begins to lift.",
         "fail": "Hati drives the King's Host from his howe.", "on_success": "end", "on_fail": "end",
         "reward": {"xp_pct": 60, "copper_per_level": 600, "tokens": 60,
                    "items": [{"id": "rk108_hati_s_moon_fang", "gold_chance": 60, "silver_chance": 25},
                              {"id": "rk108_skoll_s_sunset_pelt", "gold_chance": 60, "silver_chance": 25},
                              {"id": "rk108_fimbulwinter_shard", "gold_chance": 60, "silver_chance": 25}]}}]})
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
