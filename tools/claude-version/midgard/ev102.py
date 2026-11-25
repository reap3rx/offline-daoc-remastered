"""West Svealand's dynamic events (claude 2026-11-25, "Midgard - the plan", round 2): the four old chains kept, one new - the
Windcallers' Night (at night the Blodfelag's windcallers sing a blizzard down on the western farms and a storm-haxa rides it: the
west thread) - and the zone's set-piece, the Blood-Hall: a siege (ZoneSiege) for the Huginfel Shieldwall, fed by the zone's events
and quests; taken, the Shieldwall keeps a camp in the hall until the Haxa-Mother comes back for it.
Writes the zone's events file.   python ev102.py <in zone102 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, random_chain, occupy
Z = 102
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("West Svealand: Huginfel and Vindsaul Faste on the frontier. In the west the Blodfelag - the blood-fellowship - swear "
             "blood-oaths to the Fenris-wolf's children; their windcallers sing snow down in summer, their haxa read Raumarik's frost "
             "in bowls of blood, and their Blood-Hall stands full of thralls' chains. A gully in the south-west has frozen and will not thaw.")
DRENG = mob(60158514, "blodfelag dreng", (15, 17), guild="the Blodfelag")
SVARD = mob(60158526, "blodfelag svard", (16, 18), guild="the Blodfelag")
WIND = mob(20015, "blodfelag windcaller", (16, 18), guild="the Blodfelag")
HAXA = mob(20016, "blodfelag haxa", (17, 19), guild="the Blodfelag")
WOLFW = mob(60158532, "blodfelag wolfwarrior", (17, 19), guild="the Blodfelag")
HOUND = mob(60158529, "blodfelag warhound", (15, 17), guild="the Blodfelag")
FROTH = mob(60161138, "frothing sveawolf", (16, 18), guild="running with the Blodfelag")
IMP = mob(60166283, "snow imp", (16, 18), guild="out of the endless winter")
SHIELD = {"template": 60157473, "model": 160, "equipment": "SvasudGuard", "guild": "the Huginfel Shieldwall"}
FARMER = {"template": 60157473, "model": 213, "guild": "the Huginfel Shieldwall"}

# ------------------------------------------------------------------ the Windcallers' Night
FARM = P(560, 1060)
d['chains'].append(random_chain('ws_windcallers_night', "The Windcallers' Night", [15, 18],
    "Snow on the wind out of the west, in summer - the windcallers are singing...", 'w1', [
    {"id": "w1", "type": "defend", "name": "The Snowbound Farm", "objective": "Keep Farmer Torgny alive at his snowbound farm",
     "announce": "The Blodfelag's windcallers are singing a blizzard down on the western farms! Farmer Torgny won't leave his beasts - keep him alive!",
     "center": FARM, "radius": 70, "duration_s": 180, "protect": dict(FARMER, name="Farmer Torgny", level=16, pos=FARM, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(500, 1010), P(620, 1100), P(520, 1120)], "mobs": [DRENG, HOUND, IMP]},
     "thanks": "\"Snow in summer. My grandfather said this would come. Nobody believed him either.\"",
     "success": "The raiders break - and out of the blizzard comes the one riding it, a haxa with frost in her hair.",
     "fail": "Torgny falls, and the snow covers the farm by morning.", "on_success": "w2", "on_fail": "end", "reward": R(12, 110, 10)},
    {"id": "w2", "type": "boss", "name": "the Storm-Haxa", "objective": "Defeat the Storm-Haxa",
     "announce": "The Storm-Haxa, her bowl of blood frozen to her hands: 'The Wolf's son hunts the moon, and the winter comes behind him!' A fight for many - bring friends.",
     "center": FARM, "radius": 90, "time_s": 1200,
     "path": [P(560, 1060), P(470, 980), P(380, 1060), P(470, 1150), P(560, 1060)],
     "boss": {"template": 20016, "name": "the Storm-Haxa", "level": 19, "size": 65, "pos": FARM, "health_mult": 3.5, "guild": "of the Blodfelag"},
     "adds": {"every_s": 40, "count": 2, "mobs": [WIND, IMP]},
     "success": "The Storm-Haxa falls, and the snow stops - mid-flake, it seems. Her bowl cracks, and the blood in it runs, warm, at last.",
     "fail": "The Storm-Haxa rides her blizzard back into the west.", "on_success": "end", "on_fail": "end",
     "reward": R(28, 220, 18, ["nu102_storm_haxa_s_frozen_bowl", "nu102_blizzard_rider_s_mantle"], 35)},
    ], time="night"))

# ------------------------------------------------------------------ the set-piece: the Blood-Hall
HALL, YARD = P(420, 820), P(470, 870)
STAGING = P(640, 760)
d['chains'].append({
    "id": "ws_blood_hall_assault", "title": "Storm the Blood-Hall", "levels": [16, 20], "manual": True, "bots": 8, "min_people": 4,
    "bot_min_level": 12, "hint": "Shield-Marshal Ase is gathering the Huginfel Shieldwall on the rise east of the Blood-Hall.", "rest_s": 15, "start": "b1",
    "giver": dict(SHIELD, name="Shield-Marshal Ase", level=20, pos=STAGING, health_mult=3,
                  greet="The Shieldwall is here, and every man of it has a neighbour in that hall's chains. Four at least, bots and all - say [for Huginfel].",
                  accept="for Huginfel", reply="Shields up! Clear the yard, break the chains at the pens, and drag their warden out of his hall!",
                  busy="Not yet. The Shieldwall is still coming up from Huginfel. Rest, and gather.", cooldown_s=120,
                  thanks="The Blood-Hall is broken! Every chain in it is ours to cut.", regret="Back to the rise! We'll come again."),
    "guards": [dict(SHIELD, name="Shieldwall spearman", level=17, count=2), dict(SHIELD, name="huscarl of Vindsaul", level=18, count=2)],
    "stages": [
        {"id": "b1", "type": "cull", "name": "The Yard", "objective": "Clear the Blodfelag and their warhounds from the yard",
         "announce": "Into the yard! The Blodfelag are loosing their warhounds on us!", "center": YARD, "radius": 70,
         "time_s": 900, "kill": 20, "alive": 8, "mobs": [DRENG, HOUND, SVARD, FROTH],
         "success": "The yard is ours. The Blodfelag fall back into the hall.", "fail": "The Shieldwall is thrown back to the rise.",
         "on_success": "b2", "on_fail": "end", "reward": R(14, 130, 12)},
        {"id": "b2", "type": "wards", "name": "The Thrall-Pens", "objective": "Hold the three thrall-pens at once while the chains are cut",
         "announce": "The thralls are chained in three pens round the hall! Stand at all three at once and the Shieldwall will cut them loose!",
         "center": HALL, "radius": 80, "wards": [P(390, 790), P(450, 800), P(420, 860)],
         "ward_names": ["the north pen", "the east pen", "the south pen"], "ward_radius": 20, "hold_s": 30, "time_s": 900,
         "alive": 2, "mobs": [SVARD, WIND], "reinforce_s": 40, "flag": 466, "flag_name": "banner of the Shieldwall",
         "success": "The chains are cut and the thralls stagger free - and out of the hall comes the man who chained them.", "fail": "The pens hold. The Shieldwall falls back.",
         "on_success": "b3", "on_fail": "end", "reward": R(14, 130, 12)},
        {"id": "b3", "type": "boss", "name": "Hrolf Blood-Oath", "objective": "Defeat Hrolf Blood-Oath, Jarl of the Blodfelag",
         "announce": "Hrolf Blood-Oath, a wolf's pelt over his mail and his arms scarred with oaths: 'I swore to hold the door when the Wolf breaks his chain. I'll hold this one first.'",
         "center": HALL, "radius": 80, "time_s": 1200,
         "boss": {"template": 60158532, "name": "Hrolf Blood-Oath", "level": 21, "size": 62, "health_mult": 2.5, "guild": "Jarl of the Blodfelag"},
         "adds": {"every_s": 35, "count": 3, "mobs": [WOLFW, HOUND]},
         "success": "Hrolf falls in his own doorway. The Shieldwall's banner goes up over the Blood-Hall, and the chains come down.",
         "fail": "Hrolf drives the Shieldwall out of the yard.", "on_success": "end", "on_fail": "end",
         "reward": R(35, 260, 20, ["uf102_hrolf_s_oath_scarred_pelt"], 35)}]})
d['chains'].append({
    "id": "ws_blood_hall_return", "title": "The Haxa-Mother", "levels": [17, 20], "manual": True, "bots": 8, "bot_min_level": 12,
    "hint": "A blizzard out of the west, and the howling of the wolfwarriors: the Haxa-Mother has come for the Blood-Hall.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Hall Door", "objective": "Keep Shield-Warden Sola alive at the hall door",
         "announce": "Every Blodfelag in the west is coming for the Blood-Hall! Hold the door!",
         "center": HALL, "radius": 70, "duration_s": 200,
         "protect": dict(SHIELD, name="Shield-Warden Sola", level=19, pos=HALL, health_mult=5),
         "waves": {"every_s": 22, "count": 4, "from": [P(350, 780), P(380, 900), P(330, 840)], "mobs": [DRENG, SVARD, WOLFW, HOUND]},
         "success": "The first rush breaks - and the Haxa-Mother walks out of the snow.", "fail": "Shield-Warden Sola falls at the door.",
         "on_success": "x2", "on_fail": "end", "reward": R(20, 150, 14)},
        {"id": "x2", "type": "boss", "name": "the Haxa-Mother", "objective": "Defeat the Haxa-Mother",
         "announce": "The Haxa-Mother - bent and white-haired, frost spreading from her feet, with a bowl of blood that steams in the cold: 'I read your end in it. Come and see.'",
         "center": HALL, "radius": 70, "time_s": 900,
         "boss": {"template": 20016, "name": "the Haxa-Mother", "level": 21, "size": 70, "health_mult": 2.5, "guild": "Mother of the Blodfelag"},
         "adds": {"every_s": 35, "count": 3, "mobs": [HAXA, IMP]},
         "success": "The Haxa-Mother falls. The Blood-Hall holds - for now.", "fail": "The Haxa-Mother takes the Blood-Hall back.",
         "on_success": "end", "on_fail": "end", "reward": R(30, 220, 20, ["uf102_haxa_mother_s_steaming_bowl"], 35)}]})

UF = "uf102_"
d['siege'] = {
    "id": "blood_hall", "name": "the Blood-Hall", "enemy": "the Blodfelag",
    "resolve_name": "The Shieldwall's resolve", "enemy_name": "The Blodfelag's hold", "faction": "huginfel_shieldwall",
    "feeds": {"ws_windcallers_night": 20, "west_svealand_blodfelag_camp": 15, "west_svealand_oathbreakers": 10,
              "west_svealand_skogsfru": 5, "west_svealand_svartalf_cairn": 5},
    "feed_default": 5,
    "quests": {"ws_thralls": 5, "ws_oathbreakers": 10, "ws_henchmen": 10, "ws_warhounds": 10, "ws_windcallers": 15,
               "ws_wolfwarriors": 15, "ws_haxa": 15, "ws_blood_hall": 25, "oathbreaker": 10, "wolf_cord": 10},
    "enemy_feeds": {"ws_windcallers_night": 15}, "enemy_default": 5, "war_chain": "ws_windcallers_night",
    "assault": "ws_blood_hall_assault", "raids": [], "last_raid": "ws_blood_hall_return", "hold_h": 2, "raid_gap_h": [2, 1.5, 1.5],
    "criers": ["ws_sigvaldi", "huscarl_grettir"], "bots_go_after_m": 30,
    "open_text": "Hear me! The Huginfel Shieldwall means to storm the Blodfelag's Blood-Hall! Shield-Marshal Ase waits on the rise east of the hall. If no one leads within the half-hour, the Shieldwall goes without you.",
    "taken_text": "The Blood-Hall is broken! The thralls are free, and the Shieldwall keeps the hall - go and see.",
    "repelled_text": "The Shieldwall has been thrown back from the Blood-Hall. The Blodfelag grow bolder.",
    "raid_text": "A blizzard out of the west: the Blodfelag are coming back for the Blood-Hall!",
    "held_text": "The Blodfelag are thrown back from the walls. The Blood-Hall holds.",
    "fall_text": "The Blood-Hall has fallen to the Haxa-Mother. The Blodfelag have their hall again, and the Shieldwall must rebuild its resolve.",
    "carry_text": "Shield-Marshal Ase leads you down the rise at a run.",
    "carried_cry": "The Shieldwall wouldn't wait any longer - they have stormed {0}!",
    "hostile_tier": "yellow", "sites": ["blood_hall", "blood_hall_yard"],
    "staging": STAGING, "landing": YARD, "area": [430, 830, 100],
    "camp_npcs": [
        dict(SHIELD, kind="marks", name="Shieldwall-Quartermaster Arne", level=19, pos=P(450, 840),
             greet="The hall's stores, for those who broke it and those who hold it.",
             stock=[{"item": UF + "blood_hall_breaker_s_cloak", "price": 60}, {"item": UF + "cut_chain_ring", "price": 40},
                    {"item": UF + "shieldwall_boss_torc", "price": 40}, {"item": UF + "thrall_pen_bracer", "price": 40},
                    {"item": "tw_strong_draught_of_healing", "price": 2}, {"item": "tw_strong_draught_of_power", "price": 2}]),
        dict(FARMER, kind="coin", name="Freed-Thrall Unn", level=16, pos=P(400, 850), model=168,
             greet="They made me brew for them. I brew for you now. It's better.",
             stock=[{"item": UF + "hall_ale"}, {"item": UF + "juniper_draught"}, {"item": UF + "freedwoman_s_mead"}]),
        dict(SHIELD, kind="idle", name="Shieldwall spearman", level=17, pos=P(470, 820), count=3,
             idle="We burned the wolf's skull off the door. The thralls cheered louder than we did."),
    ],
    "holdouts": [
        {"kind": "holdout", "name": "Blodfelag holdout", "template": 60158514, "level": 18, "pos": P(360, 760), "count": 3, "tier": "yellow", "respawn_s": 300}],
}
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
