"""East Svealand's dynamic events (claude 2026-11-24, "Midgard - the plan", round 1): the four old chains kept, two new - the
Hame-Raid (at night the Grey Hames and their wolves raid a farm: the west thread) and the Drakeling Swarm (the brood at Nisse's
Lair breaks loose: the south thread) - and the zone's set-piece, Ulfrstead: a fort to retake (ZoneSiege), fed by the zone's
events and quests; held, the Steading-League keeps a camp in the steading until the Hame-Mother comes back for it.
Writes the zone's events file.   python ev101.py <in zone101 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, random_chain, occupy
Z = 101
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("East Svealand: Audliten, Dvalin and Vasudheim, wolf country of lakes and rivers. The wolves have grown bold: the "
             "sveawolves and lupines run with the Grey Hames, wild men in wolf-hames sworn to the Fenris-wolf's children, and together "
             "they have taken Ulfrstead. In the south, drakelings nest at Nisse's Lair, and a missionary feeds them.")
WILD = mob(60167945, "Grey Hame", (10, 12), guild="the Grey Hames")
SCOUT = mob(60167947, "Grey Hame scout", (9, 11), guild="the Grey Hames")
LUP = mob(60163490, "lupine snarler", (10, 12), guild="running with the Grey Hames")
GNAW = mob(60163487, "lupine gnawer", (9, 11), guild="running with the Grey Hames")
ENVY = mob(60160533, "envy drakeling", (11, 13), guild="the Brood of Nisse's Lair")
SILV = mob(60166050, "silverscale drakeling", (12, 14), guild="the Brood of Nisse's Lair")
LEAGUE = {"template": 60157473, "model": 213, "guild": "the Steading-League"}
HUSCARL = {"template": 60157473, "model": 160, "equipment": "SvasudGuard", "guild": "King Eirik's Huscarls"}

FARM = P(560, 700)
d['chains'].append(random_chain('es_hame_raid', 'The Hame-Raid', [10, 13],
    "Wolves howling round the moor farms - and men howling with them...", 'h1', [
    {"id": "h1", "type": "defend", "name": "The Moor Farm", "objective": "Keep Farmer Asgaut alive at his steading",
     "announce": "The Grey Hames and their wolves are raiding the moor farms tonight! Farmer Asgaut won't leave his steading - keep him alive!",
     "center": FARM, "radius": 70, "duration_s": 180, "protect": dict(LEAGUE, name="Farmer Asgaut", level=11, pos=FARM, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(520, 660), P(620, 740), P(600, 650)], "mobs": [WILD, LUP, GNAW]},
     "thanks": "\"My father built this steading. The wolves can build their own.\"",
     "success": "The raiders break - all but their leader, who pulls his wolf-hame over his face and comes on alone.",
     "fail": "Asgaut falls, and the Grey Hames burn the steading.", "on_success": "h2", "on_fail": "end", "reward": R(12, 100, 8)},
    {"id": "h2", "type": "boss", "name": "Hame-Brother Vargeir", "objective": "Defeat Hame-Brother Vargeir",
     "announce": "Hame-Brother Vargeir, his wolf-skin's jaws over his face: 'Fenrir's children walk! Kneel to the winter!'",
     "center": FARM, "radius": 70, "time_s": 1200,
     "boss": {"template": 60167945, "name": "Hame-Brother Vargeir", "level": 14, "size": 60, "pos": FARM, "health_mult": 3, "guild": "of the Grey Hames"},
     "adds": {"every_s": 40, "count": 2, "mobs": [LUP]},
     "success": "Vargeir falls, and his hame comes off. Under it he's a farmer's son from West Svealand.", "fail": "Vargeir drives the League off the moor.",
     "on_success": "end", "on_fail": "end", "reward": R(25, 200, 16, ["nu101_vargeir_s_wolf_hame"], 35)},
    ], time="night"))

NEST = P(980, 1150)
d['chains'].append(random_chain('es_drakeling_swarm', 'The Drakeling Swarm', [11, 14],
    "Drakelings boiling out of Nisse's Lair - the brood has broken loose...", 'd1', [
    {"id": "d1", "type": "cull", "name": "The Swarm", "objective": "Break the drakeling swarm at Nisse's Lair",
     "announce": "The drakeling brood at Nisse's Lair has broken loose and is swarming the south road! Break it!",
     "center": NEST, "radius": 80, "time_s": 900, "kill": 14, "alive": 6, "mobs": [ENVY, ENVY, SILV],
     "success": "The swarm thins - and the brood-mother crawls out of the lair, hissing.", "fail": "The swarm spreads up the south road.",
     "on_success": "d2", "on_fail": "end", "reward": R(12, 100, 8)},
    {"id": "d2", "type": "boss", "name": "the Silverscale Brood-Mother", "objective": "Defeat the Silverscale Brood-Mother",
     "announce": "The Silverscale Brood-Mother, as long as a longship's mast: she's been fed well. Bring friends.",
     "center": NEST, "radius": 80, "time_s": 1200,
     "boss": {"template": 60166050, "name": "the Silverscale Brood-Mother", "level": 15, "size": 80, "pos": NEST, "health_mult": 3.5, "guild": "of Nisse's Lair"},
     "adds": {"every_s": 40, "count": 2, "mobs": [ENVY]},
     "success": "The brood-mother falls, and the drakelings scatter into the dark of the lair.", "fail": "The brood-mother takes the south road.",
     "on_success": "end", "on_fail": "end", "reward": R(25, 200, 16, ["nu101_brood_mother_s_scale"], 35)},
    ]))

# ------------------------------------------------------------------ the set-piece: Ulfrstead
HALL, YARD = P(830, 640), P(850, 680)
STAGING = P(700, 520)
d['chains'].append({
    "id": "es_ulfrstead_assault", "title": "Retake Ulfrstead", "levels": [11, 15], "manual": True, "bots": 8, "min_people": 4,
    "bot_min_level": 8, "hint": "Reeve-Captain Hrefna is gathering the Steading-League on the ridge above Ulfrstead.", "rest_s": 15, "start": "u1",
    "giver": dict(LEAGUE, name="Reeve-Captain Hrefna", level=15, pos=STAGING, health_mult=3,
                  greet="The League's men are here, and they're angry. Ulfrstead is ours and the Grey Hames are leaving it, one way or another. Four at least, bots and all - say [for the League].",
                  accept="for the League", reply="Down to the steading! Clear the yard, hold the three doors, and drag their warden out!",
                  busy="Not yet. The League's men are still coming over the moor. Rest, and gather.", cooldown_s=120,
                  thanks="Ulfrstead is the League's again!", regret="Back up the ridge! We'll come again."),
    "guards": [dict(LEAGUE, name="League spearman", level=12, count=2), dict(HUSCARL, name="huscarl of Vasudheim", level=13, count=2)],
    "stages": [
        {"id": "u1", "type": "cull", "name": "The Yard", "objective": "Clear the Grey Hames and their wolves from the yard",
         "announce": "Into the yard! The Grey Hames and their wolves are coming out to meet us!", "center": YARD, "radius": 70,
         "time_s": 900, "kill": 20, "alive": 8, "mobs": [WILD, LUP, GNAW, SCOUT],
         "success": "The yard is ours. The Grey Hames fall back to the buildings.", "fail": "The League is thrown back up the ridge.",
         "on_success": "u2", "on_fail": "end", "reward": R(14, 120, 10)},
        {"id": "u2", "type": "wards", "name": "The Three Doors", "objective": "Hold the hall, the byre and the smithy doors at once",
         "announce": "They hold three doors - the hall, the byre and the smithy. Stand at all three at once and the League will bar them!",
         "center": HALL, "radius": 80, "wards": [P(810, 620), P(860, 650), P(830, 690)],
         "ward_names": ["the hall door", "the byre door", "the smithy door"], "ward_radius": 20, "hold_s": 30, "time_s": 900,
         "alive": 2, "mobs": [WILD, LUP], "reinforce_s": 40, "flag": 466, "flag_name": "banner of the League",
         "success": "The doors are barred - and out of the hall comes the Hame-Jarl himself.", "fail": "The doors hold. The League falls back.",
         "on_success": "u3", "on_fail": "end", "reward": R(14, 120, 10)},
        {"id": "u3", "type": "boss", "name": "Ulfar Hame-Jarl", "objective": "Defeat Ulfar Hame-Jarl",
         "announce": "Ulfar Hame-Jarl, the grey wolf's whole skin over his mail: 'Fenrir's children came to me in the snow. They'll come to you too.'",
         "center": HALL, "radius": 80, "time_s": 1200,
         "boss": {"template": 60167945, "name": "Ulfar Hame-Jarl", "level": 16, "size": 62, "health_mult": 2.5, "guild": "Jarl of the Grey Hames"},
         "adds": {"every_s": 35, "count": 3, "mobs": [WILD, LUP]},
         "success": "Ulfar falls on his own threshold. The League's banner goes up over Ulfrstead, and the family comes home.",
         "fail": "Ulfar drives the League out of the yard.", "on_success": "end", "on_fail": "end",
         "reward": R(35, 240, 20, ["uf101_ulfar_s_grey_hame"], 35)}]})
d['chains'].append({
    "id": "es_ulfrstead_return", "title": "The Hame-Mother", "levels": [12, 15], "manual": True, "bots": 8, "bot_min_level": 8,
    "hint": "Howling from every side of the moor: the Hame-Mother has come for Ulfrstead.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Hall Door", "objective": "Keep Reeve Halldor alive at the hall door",
         "announce": "Every wolf on the moor is coming for Ulfrstead! Hold the hall door!",
         "center": HALL, "radius": 70, "duration_s": 200,
         "protect": dict(LEAGUE, name="Reeve Halldor", level=14, pos=HALL, health_mult=5),
         "waves": {"every_s": 22, "count": 4, "from": [P(760, 600), P(900, 640), P(830, 730)], "mobs": [WILD, LUP, GNAW, SCOUT]},
         "success": "The first rush breaks - and the Hame-Mother comes over the wall.", "fail": "Reeve Halldor falls at the door.",
         "on_success": "x2", "on_fail": "end", "reward": R(20, 140, 14)},
        {"id": "x2", "type": "boss", "name": "the Hame-Mother", "objective": "Defeat the Hame-Mother",
         "announce": "The Hame-Mother - a lupine bigger than any you've seen, walking on two legs, with a necklace of farm-bells: 'My children were promised this place.'",
         "center": HALL, "radius": 70, "time_s": 900,
         "boss": {"template": 60163490, "name": "the Hame-Mother", "level": 16, "size": 75, "health_mult": 2.5, "guild": "Mother of the Grey Hames"},
         "adds": {"every_s": 35, "count": 3, "mobs": [LUP, GNAW]},
         "success": "The Hame-Mother falls. Ulfrstead holds - for now.", "fail": "The Hame-Mother takes Ulfrstead back.",
         "on_success": "end", "on_fail": "end", "reward": R(30, 200, 20, ["uf101_hame_mother_s_bell_necklace"], 35)}]})

UF = "uf101_"
d['siege'] = {
    "id": "ulfrstead", "name": "Ulfrstead", "enemy": "the Grey Hames",
    "resolve_name": "The League's resolve", "enemy_name": "The Grey Hames' hold", "faction": "steading_league",
    "feeds": {"es_hame_raid": 20, "east_svealand_sveawolves": 15, "east_svealand_tomte": 10, "east_svealand_army_ants": 5,
              "east_svealand_restless_dead": 5, "es_drakeling_swarm": 5},
    "feed_default": 5,
    "quests": {"es_sveawolves": 10, "es_lupines": 10, "es_grey_hames": 15, "es_ulfrstead": 25, "es_tomte_raiders": 5, "es_ant_mound": 5,
               "thrall_price": 10},
    "enemy_feeds": {"es_hame_raid": 15}, "enemy_default": 5, "war_chain": "es_hame_raid",
    "assault": "es_ulfrstead_assault", "raids": [], "last_raid": "es_ulfrstead_return", "hold_h": 2, "raid_gap_h": [2, 1.5, 1.5],
    "criers": ["es_hallgerd", "es_ketilbjorn"], "bots_go_after_m": 30,
    "open_text": "Hear me! The Steading-League means to take Ulfrstead back from the Grey Hames! Reeve-Captain Hrefna waits on the ridge above the steading. If no one leads within the half-hour, the League goes without you.",
    "taken_text": "Ulfrstead is the League's again! The family is home, and the League keeps the yard - go and see.",
    "repelled_text": "The League has been thrown back from Ulfrstead. The Grey Hames grow bolder.",
    "raid_text": "Howling on every side of the moor: the Grey Hames are coming back for Ulfrstead!",
    "held_text": "The wolves are thrown back from the walls. Ulfrstead holds.",
    "fall_text": "Ulfrstead has fallen to the Hame-Mother. The wolves have the steading again, and the League must rebuild its resolve.",
    "carry_text": "Reeve-Captain Hrefna leads you down the ridge at a run.",
    "carried_cry": "The League wouldn't wait any longer - they have stormed {0}!",
    "hostile_tier": "yellow", "sites": ["ulfrstead", "ulfrstead_yard"],
    "staging": STAGING, "landing": YARD, "area": [830, 650, 100],
    "camp_npcs": [
        dict(LEAGUE, kind="marks", name="League-Quartermaster Gyda", level=14, pos=P(810, 660),
             greet="The steading's own stores, for those who took it back and those who keep it.",
             stock=[{"item": UF + "ulfrstead_steading_cloak", "price": 60}, {"item": UF + "hall_door_ring", "price": 40},
                    {"item": UF + "league_spear_torc", "price": 40}, {"item": UF + "byre_beam_bracer", "price": 40},
                    {"item": "tw_strong_draught_of_healing", "price": 2}, {"item": "tw_strong_draught_of_power", "price": 2}]),
        dict(LEAGUE, kind="coin", name="Alewife Thordis", level=12, pos=P(845, 625), model=168,
             greet="The steading's ale and the steading's cures. The ale's better.",
             stock=[{"item": UF + "moor_ale"}, {"item": UF + "lingonberry_tonic"}, {"item": UF + "steading_mead"}]),
        dict(LEAGUE, kind="idle", name="League spearman", level=12, pos=P(840, 670), count=3,
             idle="They nailed a wolf-skin over the gate. We're burning it tonight."),
    ],
    "holdouts": [
        {"kind": "holdout", "name": "Grey Hame holdout", "template": 60167945, "level": 13, "pos": P(890, 610), "count": 3, "tier": "yellow", "respawn_s": 300}],
}
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
