"""Midgard round 1's reputation (claude 2026-11-24, "Midgard - the plan"): Vale of Mularn - King Eirik's Huscarls (their home;
shared with East Svealand, with a quartermaster in Vasudheim) and the Volur of Haggerfel; East Svealand - the Steading-League.
Midgard's kin: the soldiers (the Huscarls, the League) and the keepers of the old ways (the Volur)."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
import story_mularn as md, story_east_svealand as es
R = '/home/claude/lg/source/server/GameServer/scripts/reputation/'
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from midkin import SOLDIERS, LORE, kin   # (round 2 added the Shieldwall, the Woodwards, the Runecasters and the Seidr-Folk)
EH, HV, SL = 'eiriks_huscarls', 'haggerfel_volur', 'steading_league'
HUS_STOCK = [{"item": "rep100_huscarl_friend_s_ring", "rank": "Trusted", "price": 40},
             {"item": "rep100_jordheim_road_belt", "rank": "Trusted", "price": 40},
             {"item": "rep100_shield_of_jordheim_torc", "rank": "Honoured", "price": 80},
             {"item": "rep100_eirik_s_bracer", "rank": "Honoured", "price": 80},
             {"item": "rep100_mantle_of_eirik_s_champion", "rank": "Legend", "price": 150}]
volur_q = {'huldra', 'md_lurkers', 'md_outcasts', 'md_huldu_ring', 'md_bone_collectors', 'md_vendo_shamans', 'md_two_signs'}
d100 = {
 "zone": 100, "name": "Vale of Mularn", "levels": [1, 12], "realm": 2,
 "factions": [
  {"key": EH, "name": "King Eirik's Huscarls", "short": "the Huscarls", "kin": kin(EH),
   "titles": ["Huscarl-Friend", "Shield of Jordheim", "Eirik's Champion"], "speaker": "md_ragnhild", "town": "Mularn",
   "kills": ["hobgoblin", "water goblin", "wood-eater", "vendo", "hobyah", "preacher", "missionary", "wolfhound", "phantom hound",
             "spider", "snake", "drakeling", "dirge", "ghoul", "skeleton", "tomte", "lupine", "wildling", "hame"],
   "quartermaster": {"name": "Huscarl-Quartermaster Bjorn", "guild": "King Eirik's Huscarls", "model": 213, "anchor": "md_ragnhild",
     "offset": [4, 3], "greet": "The King's stores, for those the King can count on. Show me your standing with the Huscarls.",
     "stock": HUS_STOCK}},
  {"key": HV, "name": "the Volur of Haggerfel", "short": "the Volur", "kin": kin(HV),
   "titles": ["Seer-Friend", "Well-Reader", "Keeper of the Well"], "speaker": "md_ingrith", "town": "Haggerfel",
   "kills": ["huldu", "spirit", "hill person", "grendelorm", "shaman", "bone-collector", "phantom", "ghost"],
   "quartermaster": {"name": "Volva Thordis", "guild": "the Volur of Haggerfel", "model": 157, "anchor": "md_ingrith",
     "offset": [4, 3], "greet": "The well's gifts, for those who listen to it. Show me your standing with the Volur.",
     "stock": [{"item": "rep100_seer_friend_s_charm", "rank": "Trusted", "price": 40},
               {"item": "rep100_well_reader_s_ring", "rank": "Trusted", "price": 40},
               {"item": "rep100_nine_knot_bracer", "rank": "Honoured", "price": 80},
               {"item": "rep100_shield_of_jordheim_torc", "rank": "Honoured", "price": 80},
               {"item": "rep100_mantle_of_the_well_keeper", "rank": "Legend", "price": 150}]}}],
 "kill_default": EH, "event_default": EH, "quest_default": EH,
 "quests": {q['id']: (HV if q['id'] in volur_q else EH) for q in md.ZONES[0].quests},
 "events": {"md_moon_howler": EH, "md_red_eye_sermon": HV, "vale_of_mularn_vendo_barrow": EH, "vale_of_mularn_huldu": HV,
            "vale_of_mularn_wood_eaters": EH, "tower_veldon_watch": EH, "vale_of_mularn_hobgoblin_pranks": EH}}
json.dump(d100, open(R + 'rep100_mularn.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

league_q = {'es_crabs', 'es_ants', 'es_ant_mound', 'es_tomte_raiders', 'es_tomte_aggressors', 'es_sveawolves', 'es_lupines',
            'es_grey_hames', 'es_ulfrstead', 'thrall_price', 'tomte_due'}
d101 = {
 "zone": 101, "name": "East Svealand", "levels": [6, 16], "realm": 2,
 "factions": [
  {"key": SL, "name": "the Steading-League", "short": "the League", "kin": kin(SL),
   "titles": ["League-Friend", "Fold-Keeper", "Wolf-Breaker of Svealand"], "speaker": "es_hallgerd", "town": "Audliten",
   "kills": ["sveawolf", "lupine", "wildling", "grey hame", "hame", "tomte", "army ant", "crab", "lynx", "mauler", "thrall", "serpent"],
   "quartermaster": {"name": "League-Quartermaster Sigvor", "guild": "the Steading-League", "model": 168, "anchor": "es_hallgerd",
     "offset": [4, 3], "greet": "The League looks after its own. Show me your standing.",
     "stock": [{"item": "rep101_league_friend_s_ring", "rank": "Trusted", "price": 40},
               {"item": "rep101_steading_belt", "rank": "Trusted", "price": 40},
               {"item": "rep101_league_spearman_s_torc", "rank": "Honoured", "price": 80},
               {"item": "rep101_fold_keeper_s_bracer", "rank": "Honoured", "price": 80},
               {"item": "rep101_mantle_of_the_wolf_breaker", "rank": "Legend", "price": 150}]}}],
 "shared": [EH],
 "quartermasters": [{"faction": EH, "name": "Huscarl-Quartermaster Sten", "guild": "King Eirik's Huscarls", "model": 213,
                     "anchor": "es_brand", "offset": [4, 3],
                     "greet": "Bjorn keeps the stores at Mularn; I keep them here. Same stock, same rules - show me your standing with the Huscarls.",
                     "stock": HUS_STOCK}],
 "kill_default": SL, "event_default": SL, "quest_default": SL,
 "quests": {q['id']: (SL if q['id'] in league_q else EH) for q in es.ZONES[0].quests},
 "events": {"es_ulfrstead_assault": SL, "es_ulfrstead_return": SL, "es_hame_raid": SL, "es_drakeling_swarm": EH,
            "east_svealand_sveawolves": SL, "east_svealand_restless_dead": EH, "east_svealand_tomte": SL, "east_svealand_army_ants": SL}}
json.dump(d101, open(R + 'rep101_east_svealand.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d100['quests']), len(d101['quests']))
