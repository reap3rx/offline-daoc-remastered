"""Black Mountains North's dynamic events (claude 2026-11-24, "Albion - the plan", round 3): the four old chains kept, a new one -
the Pit-Fires (the Crimson light the dragons' pit by night) - and the zone's full siege, Dinas Emrys: the Crimson hold the hill
fort over the dragons' pit until the Garrison's resolve is full; held, the Garrison keeps it through a raid by the red-corded
tribes until the Dragon-Priestess comes back with the Crimson's whole strength. Writes the zone's events file."""
import json, sys
from evcommon import mkP, R, mob, path, move_stage, shift_levels, random_chain, occupy
Z = 3
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("The northern Black Mountains: Swanton Keep on the north road, Snowdonia Station in the south-east, and in the west Dinas "
             "Emrys - the hill fort where Vortigern's tower fell and the red and white dragons fought in the pit beneath. The Crimson "
             "hold it now and dig the pit open, because the dragons came up out of Annwn, and the way they came is a door.")
INI = mob(12075, "crimson acolyte", (26, 28), size=50, guild="the Crimson")
PRIEST = mob(12075, "crimson dragon-priest", (28, 30), guild="the Crimson")
HW = mob(12110, "red-corded hill warrior", (25, 27), guild="the Red-Corded Tribes")
HG = mob(12108, "red-corded hill guard", (26, 28), guild="the Red-Corded Tribes")
HS = mob(12109, "red-corded hill shaman", (27, 28), guild="the Red-Corded Tribes")
GARRISON = {"template": 60167630, "model": 28, "equipment": "38762ab0-5f99-47cd-85b0-0bfaa37d71f9", "guild": "the Snowdonia Garrison"}
BARD = {"template": 60167630, "model": 9, "equipment": "eab1762c-33e7-4620-9e02-985d820d0369", "guild": "the Emrys Circle"}

FIRE = P(340, 520)
d['chains'].append(random_chain('bn_pit_fires', 'The Pit-Fires', [24, 28],
    "Red fires on the hills round Dinas Emrys - the Crimson are lighting the pit-fires...", 'p1', [
    {"id": "p1", "type": "defend", "name": "The Fire-Hill", "objective": "Keep Bard Cadoc alive while he sings the fires out",
     "announce": "The Crimson have lit the pit-fires on the hills round Dinas Emrys - every fire opens the pit a little more! Bard Cadoc of the Emrys Circle has gone to sing them out.",
     "center": FIRE, "radius": 70, "duration_s": 180, "protect": dict(BARD, name="Bard Cadoc", level=26, pos=FIRE, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(300, 480), P(380, 560), P(300, 560)], "mobs": [INI, HW, HS]},
     "thanks": "\"Out. Every one of them. Let the pit stay cold tonight.\"",
     "success": "The fires gutter out - and the priest who lit them comes down the hill, furious.",
     "fail": "Cadoc falls, and the fires burn all night.", "on_success": "p2", "on_fail": "end", "reward": R(12, 120, 10)},
    {"id": "p2", "type": "boss", "name": "Fire-Priest Ithel", "objective": "Defeat Fire-Priest Ithel",
     "announce": "Fire-Priest Ithel, a red cord round his wrist for every fire: 'The red dragon was Albion's? The red dragon was ours first.' Bring friends.",
     "center": FIRE, "radius": 70, "time_s": 1200,
     "boss": {"template": 12075, "name": "Fire-Priest Ithel", "level": 29, "size": 60, "pos": FIRE, "health_mult": 3, "guild": "of the Crimson"},
     "adds": {"every_s": 40, "count": 2, "mobs": [INI]},
     "success": "Ithel falls, and the hills go dark.", "fail": "Ithel relights the fires.", "on_success": "end", "on_fail": "end",
     "reward": R(25, 200, 16, ["nu003_fire_priest_s_cord"], 35)},
    ], time="night"))

FORT, STAGING, LANDING = P(170, 370), P(380, 380), P(240, 410)
d['chains'].append({
    "id": "bn_dinas_assault", "title": "The Siege of Dinas Emrys", "levels": [26, 30], "manual": True, "bots": 10, "min_people": 6,
    "bot_min_level": 22, "hint": "Castellan Rhydderch is gathering the Snowdonia Garrison east of Dinas Emrys.", "rest_s": 15, "start": "s1",
    "giver": dict(GARRISON, name="Castellan Rhydderch", level=30, pos=STAGING, health_mult=3,
                  greet="Dinas Emrys. Vortigern couldn't hold it and neither will they. Six at least, bots and all - say [for Emrys].",
                  accept="for Emrys", reply="Through the gate! Take the walls, hold the three pit-stones, and bring down the Dragon-Priestess!",
                  busy="Not yet. The garrison is still forming up.", cooldown_s=120, thanks="Dinas Emrys is Albion's again!",
                  regret="Fall back down the hill! We'll come again."),
    "guards": [dict(GARRISON, name="garrison shieldman", level=26, count=3), dict(BARD, name="bard of the Emrys Circle", level=24, count=1)],
    "stages": [
        {"id": "s1", "type": "cull", "name": "The Gate and the Walls", "objective": "Take the gate and the walls of Dinas Emrys",
         "announce": "Up the hill! The red-corded tribes hold the gate, the Crimson hold the walls!", "center": FORT, "radius": 90, "time_s": 900,
         "kill": 22, "alive": 8, "mobs": [HW, HG, INI], "success": "The walls are ours. The Crimson fall back to the pit.",
         "fail": "The garrison is thrown back down the hill.", "on_success": "s2", "on_fail": "end", "reward": R(15, 160, 12)},
        {"id": "s2", "type": "wards", "name": "The Pit-Stones", "objective": "Hold the three pit-stones at once",
         "announce": "Three standing stones ring the pit - the Crimson sing through them. Stand on all three at once and the bards will sing them dumb!",
         "center": FORT, "radius": 90, "wards": [P(140, 345), P(175, 335), P(155, 380)],
         "ward_names": ["the red stone", "the white stone", "the door-stone"], "ward_radius": 16, "hold_s": 35, "time_s": 900,
         "alive": 2, "mobs": [INI, PRIEST], "reinforce_s": 35, "flag": 466, "flag_name": "banner of the Garrison",
         "success": "The stones fall silent - and the Dragon-Priestess rises out of the pit.", "fail": "The Crimson drive the garrison off the stones.",
         "on_success": "s3", "on_fail": "end", "reward": R(15, 160, 12)},
        {"id": "s3", "type": "boss", "name": "the Dragon-Priestess", "objective": "Defeat the Dragon-Priestess",
         "announce": "The Dragon-Priestess climbs out of the pit, red-scaled to the elbows: 'My Lady opens doors. You close them. One of us is on the wrong side.'",
         "center": FORT, "radius": 90, "time_s": 1200,
         "boss": {"template": 12075, "name": "the Dragon-Priestess", "level": 31, "size": 64, "health_mult": 3, "guild": "of the Crimson"},
         "adds": {"every_s": 35, "count": 3, "mobs": [INI, PRIEST]},
         "success": "The Dragon-Priestess falls into her own pit. The Garrison's banner goes up over Dinas Emrys, and the bards sing the pit cold.",
         "fail": "The Dragon-Priestess drives the garrison out of the fort.", "on_success": "end", "on_fail": "end",
         "reward": R(40, 300, 26, ["de003_dragon_priestess_s_scale"], 35)}]})
d['chains'].append({
    "id": "bn_dinas_raid", "title": "The Tribes Come Back", "levels": [26, 30], "manual": True, "bots": 8, "bot_min_level": 22,
    "hint": "War-horns in the hills: the red-corded tribes are coming for Dinas Emrys.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Gate", "objective": "Keep Sergeant Owain alive at the gate",
         "announce": "The red-corded tribes are at the gate! Hold it!", "center": FORT, "radius": 80, "duration_s": 180,
         "protect": dict(GARRISON, name="Sergeant Owain", level=28, pos=LANDING, health_mult=5),
         "waves": {"every_s": 22, "count": 4, "from": [P(260, 480), P(300, 380), P(230, 300)], "mobs": [HW, HG, HS]},
         "success": "The tribes break and run back into the hills.", "fail": "Owain falls at the gate.",
         "on_success": "end", "on_fail": "end", "reward": R(25, 200, 18, ["de003_tribal_war_horn"], 35)}]})
d['chains'].append({
    "id": "bn_dinas_return", "title": "The Crimson's Whole Strength", "levels": [27, 30], "manual": True, "bots": 10, "bot_min_level": 22,
    "hint": "The pit is glowing again: the Crimson are coming for Dinas Emrys with everything they have.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Pit's Edge", "objective": "Keep Bard Cadoc alive at the pit's edge",
         "announce": "Crimson in every gully, and the pit glowing! Keep the bard singing!", "center": FORT, "radius": 80, "duration_s": 200,
         "protect": dict(BARD, name="Bard Cadoc", level=28, pos=FORT, health_mult=5),
         "waves": {"every_s": 22, "count": 4, "from": [P(120, 420), P(220, 300), P(240, 440)], "mobs": [INI, PRIEST, HS]},
         "success": "The first rush breaks - and the Crimson's Red Hierarch comes up out of the pit.", "fail": "Cadoc falls, and the pit opens.",
         "on_success": "x2", "on_fail": "end", "reward": R(20, 180, 16)},
        {"id": "x2", "type": "boss", "name": "the Red Hierarch", "objective": "Defeat the Red Hierarch",
         "announce": "The Red Hierarch, Morgana's own right hand: 'She sends her regards, and her patience is ended.'",
         "center": FORT, "radius": 80, "time_s": 900,
         "boss": {"template": 12117, "name": "the Red Hierarch", "level": 32, "size": 62, "health_mult": 3, "guild": "of the Crimson"},
         "adds": {"every_s": 35, "count": 3, "mobs": [PRIEST, INI]},
         "success": "The Red Hierarch falls. Dinas Emrys holds - for now.", "fail": "The Crimson take Dinas Emrys back.",
         "on_success": "end", "on_fail": "end", "reward": R(35, 260, 22, ["de003_hierarch_s_seal"], 35)}]})

DE = "de003_"
d['siege'] = {
    "id": "dinas_emrys", "name": "Dinas Emrys", "enemy": "the Crimson",
    "resolve_name": "The Garrison's resolve", "enemy_name": "The Crimson's hold", "faction": "snowdonia_garrison",
    "feeds": {"bn_pit_fires": 20, "black_mountains_north_hill_folk": 15, "black_mountains_north_smugglers_road": 10,
              "black_mountains_north_old_mine": 5, "black_mountains_north_warg_pack": 5},
    "feed_default": 5,
    "quests": {"crimson_bargain": 10, "bn_red_road": 10, "bn_forest_chief": 15, "bn_red_tribes": 15, "bn_hill_chief": 20,
               "bn_necromancers": 15, "bn_dinas_emrys": 25, "bn_red_cords_south": 10},
    "enemy_feeds": {"bn_pit_fires": 20, "black_mountains_north_hill_folk": 10}, "enemy_default": 5, "war_chain": "bn_pit_fires",
    "assault": "bn_dinas_assault", "raids": ["bn_dinas_raid"], "last_raid": "bn_dinas_return", "hold_h": 3, "raid_gap_h": [2, 1.5, 1.5],
    "criers": ["bn_rhydderch", "bn_taliesin", "captain_mardoc"], "bots_go_after_m": 30,
    "open_text": "Hear me! The Snowdonia Garrison marches on Dinas Emrys to take the fort back from the Crimson! Castellan Rhydderch waits east of the fort. If no one leads within the half-hour, the Garrison goes without you.",
    "taken_text": "Dinas Emrys is Albion's again! The Garrison's banner flies over the fort, and the bards are singing the pit cold - go and see.",
    "repelled_text": "The Garrison has been thrown back from Dinas Emrys. The Crimson grow bolder.",
    "raid_text": "War-horns in the hills: they are coming back for Dinas Emrys!",
    "held_text": "The attack on Dinas Emrys is thrown back. The fort holds.",
    "fall_text": "Dinas Emrys has fallen to the Crimson. The pit glows again, and the Garrison must rebuild its resolve.",
    "carry_text": "Castellan Rhydderch leads you up the hill at a run.",
    "carried_cry": "The Garrison wouldn't wait any longer - they have stormed {0}!",
    "hostile_tier": "orange", "sites": ["dinas_emrys", "dinas_gate", "dragons_pit"],
    "staging": STAGING, "landing": LANDING, "area": [170, 370, 110],
    "camp_npcs": [
        dict(GARRISON, kind="marks", name="Garrison-Quartermaster Ffion", level=28, pos=P(200, 390),
             greet="The fort's stores, for those who took it and those who hold it.",
             stock=[{"item": DE + "cloak_of_emrys_s_fort", "price": 60}, {"item": DE + "pit_stone_ring", "price": 40},
                    {"item": DE + "hill_fort_torc", "price": 40}, {"item": DE + "garrison_wall_bracer", "price": 40},
                    {"item": "tw_strong_draught_of_healing", "price": 2}, {"item": "tw_strong_draught_of_power", "price": 2}]),
        dict(BARD, kind="coin", name="Bard-Physician Elffin", level=26, pos=P(150, 400),
             greet="Remedies and a song. The remedies cost coin; the songs are free.",
             stock=[{"item": DE + "mountain_draught"}, {"item": DE + "bard_s_honey_tonic"}, {"item": DE + "emrys_mead"}]),
        dict(GARRISON, kind="idle", name="garrison shieldman", level=26, pos=P(180, 380), count=3,
             idle="Don't look down the pit. The bards say it's cold now. It doesn't feel cold."),
        dict(BARD, kind="idle", name="Bard Cadoc", level=26, pos=P(160, 355), idle="Listen - the pit is quiet. That's my song holding it."),
    ],
    "holdouts": [
        {"kind": "holdout", "name": "red-corded holdout", "template": 12110, "level": 27, "pos": P(110, 420), "count": 3, "tier": "orange", "respawn_s": 300},
        {"kind": "holdout", "name": "crimson pit-skulker", "template": 12075, "level": 28, "pos": P(130, 320), "count": 2, "tier": "orange", "respawn_s": 600}],
}
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
