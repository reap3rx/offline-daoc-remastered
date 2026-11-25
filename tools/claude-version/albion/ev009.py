"""Avalon Marsh's dynamic events (claude 2026-11-24, "Albion - the plan", round 2): the four old chains kept on the new layout,
a new one - the Black Barge (it crosses at the new moon for Morgana's people) - and the zone's set-piece, the Vigil Keep: a fort
to retake (ZoneSiege) from the Drowned Vigil's ghouls; held, the Marsh Wardens keep a camp there until the Drowned
Lord-Commander comes back for it. Writes the zone's events file.   python ev009.py <in json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, move_stage, shift_levels, random_chain, occupy
Z = 9
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Avalon Marsh, round the Isle where Arthur sleeps. Caer Witrin stands on its island of apples, the Drowned Vigil still "
             "holds its keep in the north-west, and the black barge that carried the King is crossing again by night - for Morgana's "
             "people. In the west, Golestandt's giants lay a road of Cornish granite toward the Isle.")
ch = {c['id']: c for c in d['chains']}
for st in ch['avalon_marsh_leapers_pool']['stages']:
    if st['id'] in ('a1', 'a2'):
        move_stage(st, P, (979, 1300))

SPRITE = mob(12029, "mist sprite", (16, 18))
OAR = mob(12016, "drowned oarsman", (18, 20))
INI = mob(12075, "crimson initiate", (18, 20), guild="the Crimson")
GF = mob(12017, "ghoul footman", (19, 21), guild="the Drowned Vigil")
GK = mob(12018, "ghoul knight", (20, 22), guild="the Drowned Vigil")
GL = mob(12019, "ghoul lord", (21, 23), guild="the Drowned Vigil")
WARDEN = {"template": 60161835, "model": 74, "equipment": "537f261b-a7ba-4cc1-a75a-dea0c78150f3", "guild": "the Marsh Wardens"}

SHORE = P(1090, 490)
d['chains'].append(random_chain('am_black_barge_night', 'The Black Barge', [18, 22],
    "No moon tonight - and a long black boat is sliding through the mist toward the Isle...", 'b1', [
    {"id": "b1", "type": "cull", "name": "The Mist", "objective": "Cut through the mist round the landing",
     "announce": "The black barge is crossing to the Isle with Morgana's people aboard, and the mist round the landing has turned on everyone. Get to the landing!",
     "center": SHORE, "radius": 80, "time_s": 1200, "kill": 12, "alive": 6, "mobs": [SPRITE, SPRITE, INI],
     "success": "The mist thins. The barge grinds onto the landing, and its oarsmen stand up.",
     "fail": "The barge reaches the Isle.", "on_success": "b2", "on_fail": "end", "reward": R(12, 100, 8)},
    {"id": "b2", "type": "boss", "name": "the Oarsmaster", "objective": "Defeat the barge's Oarsmaster",
     "announce": "The Oarsmaster, drowned three hundred years, lifts his oar like a spear: 'We row for the key and the crown.' Bring friends.",
     "center": SHORE, "radius": 80, "time_s": 1200,
     "boss": {"template": 12016, "name": "the Oarsmaster", "level": 22, "size": 62, "pos": SHORE, "health_mult": 3, "guild": "of the Black Barge"},
     "adds": {"every_s": 40, "count": 2, "mobs": [OAR, INI]},
     "success": "The Oarsmaster falls back into the water, and the barge drifts empty on the mist.",
     "fail": "The barge lands its passengers on the Isle.", "on_success": "end", "on_fail": "end",
     "reward": R(25, 180, 14, ["nu009_oarsmaster_s_ring"], 35)},
    ], time="night"))

KEEP, STAGING, LANDING = P(360, 245), P(525, 305), P(430, 270)
d['chains'].append({
    "id": "am_vigil_assault", "title": "Retake the Vigil Keep", "levels": [20, 24], "manual": True, "bots": 8, "min_people": 4,
    "bot_min_level": 16, "hint": "Warden-Sergeant Cai is gathering the Marsh Wardens east of the Drowned Vigil's keep.", "rest_s": 15, "start": "v1",
    "giver": dict(WARDEN, name="Warden-Sergeant Cai", level=24, pos=STAGING, health_mult=3,
                  greet="The Vigil's held that keep for three hundred years with nobody to relieve them. We're the relief. Four at least, bots and all - say [relieve the Vigil].",
                  accept="relieve the Vigil", reply="Through the walls! Hold the gate, the chapel and the tower, and put down whoever commands them!",
                  busy="Not yet. Rest, and gather.", cooldown_s=120, thanks="The Vigil Keep is ours! They're relieved!",
                  regret="Back into the reeds! We'll come again."),
    "guards": [dict(WARDEN, name="marsh warden", level=20, count=3)],
    "stages": [
        {"id": "v1", "type": "cull", "name": "The Walls", "objective": "Cut through the Vigil's dead on the walls",
         "announce": "Over the walls! The Vigil's dead are turning out to meet us, in good order, as they always did!", "center": KEEP, "radius": 80,
         "time_s": 900, "kill": 18, "alive": 7, "mobs": [GF, GF, GK], "success": "The walls are ours. The ghouls fall back to the gate, the chapel and the tower.",
         "fail": "The wardens are thrown back into the reeds.", "on_success": "v2", "on_fail": "end", "reward": R(15, 140, 10)},
        {"id": "v2", "type": "wards", "name": "Gate, Chapel and Tower", "objective": "Hold the gate, the chapel and the tower at once",
         "announce": "The Vigil hold three posts - the gate, the chapel and the tower. Stand on all three at once and they'll know they've been relieved!",
         "center": KEEP, "radius": 80, "wards": [P(395, 280), P(340, 255), P(360, 215)],
         "ward_names": ["the gate", "the chapel", "the tower"], "ward_radius": 18, "hold_s": 30, "time_s": 900,
         "alive": 2, "mobs": [GF, GK], "reinforce_s": 40, "flag": 466, "flag_name": "banner of the Marsh Wardens",
         "success": "The posts are relieved - and the Vigil's marshal comes out of the keep to see who dares.",
         "fail": "The Vigil drive the wardens off their posts.", "on_success": "v3", "on_fail": "end", "reward": R(15, 140, 10)},
        {"id": "v3", "type": "boss", "name": "Ghoul-Marshal Vrask", "objective": "Defeat Ghoul-Marshal Vrask",
         "announce": "Ghoul-Marshal Vrask, in drowned plate: 'No relief came. No relief will come. Stand to!'",
         "center": KEEP, "radius": 80, "time_s": 1200,
         "boss": {"template": 12019, "name": "Ghoul-Marshal Vrask", "level": 25, "size": 64, "health_mult": 2.5, "guild": "Marshal of the Drowned Vigil"},
         "adds": {"every_s": 35, "count": 2, "mobs": [GK, GL]},
         "success": "Vrask falls - and with him, every ghoul on the walls lowers its weapon. 'Relieved,' something whispers. The Marsh Wardens raise their banner on the tower.",
         "fail": "Vrask holds the keep.", "on_success": "end", "on_fail": "end", "reward": R(35, 260, 22, ["vk009_vrask_s_gorget"], 35)}]})
d['chains'].append({
    "id": "am_vigil_return", "title": "The Drowned Lord-Commander", "levels": [21, 24], "manual": True, "bots": 8, "bot_min_level": 16,
    "hint": "The water round the Vigil Keep is rising, and something is walking up out of it.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Chapel", "objective": "Keep Warden-Chaplain Mabon alive in the chapel",
         "announce": "The drowned are coming up out of the marsh round the keep - the whole Vigil, three hundred years of it. Hold the chapel!",
         "center": KEEP, "radius": 70, "duration_s": 200, "protect": dict(WARDEN, name="Warden-Chaplain Mabon", level=22, pos=KEEP, health_mult=5),
         "waves": {"every_s": 22, "count": 4, "from": [P(300, 260), P(380, 190), P(330, 300)], "mobs": [GF, GK, GL]},
         "success": "The first rush breaks - and the Lord-Commander walks up out of the water.", "fail": "Mabon falls in the chapel.",
         "on_success": "x2", "on_fail": "end", "reward": R(20, 160, 14)},
        {"id": "x2", "type": "boss", "name": "the Drowned Lord-Commander", "objective": "Defeat the Drowned Lord-Commander",
         "announce": "The Drowned Lord-Commander, streaming marsh-water: 'Who relieved my Vigil without my order?'",
         "center": KEEP, "radius": 70, "time_s": 900,
         "boss": {"template": 12019, "name": "the Drowned Lord-Commander", "level": 25, "size": 66, "health_mult": 2.5, "guild": "of the Drowned Vigil"},
         "adds": {"every_s": 35, "count": 2, "mobs": [GK]},
         "success": "The Lord-Commander sinks back into the marsh. The keep holds - for now.", "fail": "The Vigil take their keep back.",
         "on_success": "end", "on_fail": "end", "reward": R(30, 220, 20, ["vk009_lord_commander_s_seal"], 35)}]})

VK = "vk009_"
d['siege'] = {
    "id": "vigil_keep", "name": "the Vigil Keep", "enemy": "the Drowned Vigil",
    "resolve_name": "The Wardens' resolve", "enemy_name": "The Vigil's hold", "faction": "marsh_wardens",
    "feeds": {"avalon_marsh_ghoul_court": 20, "am_black_barge_night": 10, "avalon_marsh_bogmen": 5, "avalon_marsh_shamblers": 10,
              "avalon_marsh_leapers_pool": 5},
    "feed_default": 5,
    "quests": {"vigil": 15, "am_ghoul_court": 15, "am_vigil_banner": 25, "am_causeway": 10, "am_giant_wolves": 5, "am_mist_monsters": 10},
    "enemy_feeds": {"avalon_marsh_ghoul_court": 20}, "enemy_default": 5, "war_chain": "avalon_marsh_ghoul_court",
    "assault": "am_vigil_assault", "raids": [], "last_raid": "am_vigil_return", "hold_h": 2, "raid_gap_h": [2, 1.5, 1.5],
    "criers": ["warden_brec", "am_maelor"], "bots_go_after_m": 30,
    "open_text": "Hear me! The Marsh Wardens mean to relieve the Drowned Vigil and take their keep! Warden-Sergeant Cai waits in the reeds east of the keep. If no one leads within the half-hour, the Wardens go without you.",
    "taken_text": "The Vigil Keep is ours! The Marsh Wardens' banner flies on the tower and the Vigil are relieved - go and see.",
    "repelled_text": "The Wardens have been thrown back from the Vigil Keep. The drowned grow bolder.",
    "raid_text": "The water is rising round the Vigil Keep: the drowned are coming back for it!",
    "held_text": "The drowned are thrown back into the marsh. The keep holds.",
    "fall_text": "The Vigil Keep has fallen to the Drowned Lord-Commander. The Wardens must rebuild their resolve.",
    "carry_text": "Warden-Sergeant Cai leads you through the reeds at a run.",
    "carried_cry": "The Wardens wouldn't wait any longer - they have stormed {0}!",
    "hostile_tier": "orange", "sites": ["vigil_keep", "vigil_walls", "vigil_marsh"],
    "staging": STAGING, "landing": LANDING, "area": [360, 245, 110],
    "camp_npcs": [
        dict(WARDEN, kind="marks", name="Warden-Quartermaster Ysbail", level=22, pos=P(380, 265),
             greet="The keep's stores - what three hundred years of damp didn't ruin, and what we brought. For the relief.",
             stock=[{"item": VK + "cloak_of_the_relief", "price": 60}, {"item": VK + "vigil_tower_ring", "price": 40},
                    {"item": VK + "drowned_plate_bracer", "price": 40}, {"item": VK + "marsh_warden_s_torc", "price": 40},
                    {"item": "tw_strong_draught_of_healing", "price": 2}, {"item": "tw_strong_draught_of_power", "price": 2}]),
        dict(WARDEN, kind="coin", name="Apple-Wife Morfydd", model=38, level=20, pos=P(345, 270),
             greet="Cider and cures from Caer Witrin's orchards. Coin, if you please.",
             stock=[{"item": VK + "apple_isle_draught"}, {"item": VK + "marsh_tonic"}, {"item": VK + "witrin_cider"}]),
        dict(WARDEN, kind="idle", name="marsh warden", level=20, pos=P(370, 230), count=3,
             idle="Three hundred years they stood here. I've done three hours and my feet are wet."),
    ],
    "holdouts": [
        {"kind": "holdout", "name": "ghoul straggler", "template": 12017, "level": 21, "pos": P(300, 200), "count": 3, "tier": "orange", "respawn_s": 300},
        {"kind": "holdout", "name": "drowned knight", "template": 12018, "level": 22, "pos": P(420, 170), "count": 2, "tier": "orange", "respawn_s": 600}],
}
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
