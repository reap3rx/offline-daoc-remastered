"""Midgard round 2's reputation (claude 2026-11-25, "Midgard - the plan"): West Svealand - the Huginfel Shieldwall (and King
Eirik's Huscarls, shared, with a quartermaster at Vindsaul Faste); Gotar - the Nalliten Runecasters (and the Huscarls, with a
quartermaster at Fort Atla); Myrkwood - the Galplen Woodwards and the Seidr-Folk. Kin: midkin.py."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from midkin import kin
import story_west_svealand as ws, story_gotar as gt, story_myrkwood as mw
R = '/home/claude/lg/source/server/GameServer/scripts/reputation/'
EH, SW, NR, GW, SF = 'eiriks_huscarls', 'huginfel_shieldwall', 'nalliten_runecasters', 'galplen_woodwards', 'seidr_folk'
HUS_STOCK = [{"item": "rep100_huscarl_friend_s_ring", "rank": "Trusted", "price": 40},
             {"item": "rep100_jordheim_road_belt", "rank": "Trusted", "price": 40},
             {"item": "rep100_shield_of_jordheim_torc", "rank": "Honoured", "price": 80},
             {"item": "rep100_eirik_s_bracer", "rank": "Honoured", "price": 80},
             {"item": "rep100_mantle_of_eirik_s_champion", "rank": "Legend", "price": 150}]
BY_TEXT = {"From King Eirik's Huscarls.": EH, "From the Huginfel Shieldwall.": SW, "From the Nalliten Runecasters.": NR,
           "From the Galplen Woodwards.": GW, "From the Seidr-Folk.": SF}

def owner(q, old):
    if q['id'] in old:
        return old[q['id']]
    return BY_TEXT[q['endings']['default']['text']]

def stock(p, names):
    ranks = ["Trusted", "Trusted", "Honoured", "Honoured", "Legend"]
    price = {"Trusted": 40, "Honoured": 80, "Legend": 150}
    return [{"item": p + n, "rank": r, "price": price[r]} for n, r in zip(names, ranks)]

def qm(faction, name, anchor, model, greet):
    return {"faction": faction, "name": name, "guild": "King Eirik's Huscarls", "model": model, "anchor": anchor, "offset": [4, 3],
            "greet": greet, "stock": HUS_STOCK}

d102 = {
 "zone": 102, "name": "West Svealand", "levels": [10, 20], "realm": 2,
 "factions": [
  {"key": SW, "name": "the Huginfel Shieldwall", "short": "the Shieldwall", "kin": kin(SW),
   "titles": ["Shield-Friend", "Shieldwall-Sworn", "Breaker of the Blood-Hall"], "speaker": "ws_sigvaldi", "town": "Huginfel",
   "kills": ["blodfelag", "thrall", "oathbreaker", "henchman", "windcaller", "haxa", "wolfwarrior", "warhound", "svard", "dreng",
             "partisan", "sveawolf", "phantom wolf", "she-wolf", "snow imp", "frosty colt", "cold light"],
   "quartermaster": {"name": "Shieldwall-Quartermaster Ingolf", "guild": "the Huginfel Shieldwall", "model": 213, "anchor": "ws_sigvaldi",
     "offset": [4, 3], "greet": "The Shieldwall's stores, for those who stand in it. Show me your standing.",
     "stock": stock("rep102_", ["shield_friend_s_ring", "huginfel_gate_belt", "shieldwall_sworn_torc", "linden_shield_bracer",
                                "mantle_of_the_blood_hall_breaker"])}}],
 "shared": [EH],
 "quartermasters": [qm(EH, "Huscarl-Quartermaster Orm", "huscarl_grettir", 213,
                       "The King's stores at Vindsaul Faste, same stock as Mularn. Show me your standing with the Huscarls.")],
 "kill_default": SW, "event_default": SW, "quest_default": SW,
 "quests": {q['id']: owner(q, {'oathbreaker': SW, 'wolf_cord': EH}) for q in ws.ZONES[0].quests},
 "events": {"ws_windcallers_night": SW, "ws_blood_hall_assault": SW, "ws_blood_hall_return": SW,
            "west_svealand_blodfelag_camp": SW, "west_svealand_oathbreakers": SW, "west_svealand_skogsfru": EH,
            "west_svealand_svartalf_cairn": EH}}
json.dump(d102, open(R + 'rep102_west_svealand.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

d103 = {
 "zone": 103, "name": "Gotar", "levels": [12, 22], "realm": 2,
 "factions": [
  {"key": NR, "name": "the Nalliten Runecasters", "short": "the Runecasters", "kin": kin(NR),
   "titles": ["Stave-Friend", "Rune-Reader", "Keeper of the Staves"], "speaker": "gt_runa", "town": "Nalliten",
   "kills": ["svartalf", "dragon-preacher", "drakeling", "seithkona", "gotawitch", "seithr", "host of the", "wisp", "pook", "carrion"],
   "quartermaster": {"name": "Stave-Keeper Asta", "guild": "the Nalliten Runecasters", "model": 157, "anchor": "gt_runa",
     "offset": [4, 3], "greet": "The staves' gifts, for those who read them true. Show me your standing with the Runecasters.",
     "stock": stock("rep103_", ["stave_friend_s_charm", "rune_reader_s_ring", "carved_stave_bracer", "nalliten_seer_torc",
                                "mantle_of_the_stave_keeper"])}}],
 "shared": [EH],
 "quartermasters": [qm(EH, "Huscarl-Quartermaster Hrapp", "gt_hallbjorn", 213,
                       "The King's stores at Fort Atla, same stock as Mularn. Show me your standing with the Huscarls.")],
 "kill_default": EH, "event_default": EH, "quest_default": NR,
 "quests": {q['id']: owner(q, {'nacken': EH, 'rune_stave': NR}) for q in gt.ZONES[0].quests},
 "events": {"gt_scale_caravan": EH, "gt_drowned_bell": EH, "gotar_drowned_ship": EH, "gotar_hobgoblins": NR,
            "gotar_wildlings": EH, "gotar_pine_imps": NR}}
json.dump(d103, open(R + 'rep103_gotar.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

d105 = {
 "zone": 105, "name": "Myrkwood Forest", "levels": [22, 32], "realm": 2,
 "factions": [
  {"key": GW, "name": "the Galplen Woodwards", "short": "the Woodwards", "kin": kin(GW),
   "titles": ["Woodward-Friend", "Axe of Galplen", "Warden of the Myrkwood"], "speaker": "mw_thora", "town": "Galplen",
   "kills": ["worg", "werewolf", "svartalf", "missionary", "dragon-preacher", "decaying", "myrk shadow", "corpse eater", "skeleton",
             "undead", "myrkcat", "frog", "carrion", "slither", "venomspitter"],
   "quartermaster": {"name": "Woodward-Quartermaster Leif", "guild": "the Galplen Woodwards", "model": 213, "anchor": "mw_thora",
     "offset": [4, 3], "greet": "The Woodwards' stores, for those who keep the roads open. Show me your standing.",
     "stock": stock("rep105_", ["woodward_friend_s_ring", "galplen_axe_belt", "axe_of_galplen_torc", "black_tree_bracer",
                                "mantle_of_the_myrkwood_warden"])}},
  {"key": SF, "name": "the Seidr-Folk", "short": "the Seidr-Folk", "kin": kin(SF),
   "titles": ["Seidr-Friend", "Dream-Walker", "Keeper of the Volva"], "speaker": "mw_groa", "town": "the volva's hut",
   "kills": ["willow", "haunt", "tingler", "arachite", "spider", "mora", "dark hound", "soul sinker"],
   "quartermaster": {"name": "Seidr-Woman Ylva", "guild": "the Seidr-Folk", "model": 168, "anchor": "mw_groa",
     "offset": [4, 3], "greet": "Groa's gifts, for those who keep her safe. Show me your standing with the Seidr-Folk.",
     "stock": stock("rep105_", ["seidr_friend_s_charm", "dream_walker_s_ring", "seidr_thread_bracer", "axe_of_galplen_torc",
                                "mantle_of_the_volva_s_keeper"])}}],
 "kill_default": GW, "event_default": GW, "quest_default": GW,
 "quests": {q['id']: owner(q, {'willow_voice': GW, 'mora': SF}) for q in mw.ZONES[0].quests},
 "events": {"mw_blood_moon": GW, "mw_seer_hunt": SF, "myrkwood_forest_werewolf_den": GW, "myrkwood_forest_arachite_brood": SF,
            "myrkwood_forest_decaying_trolls": GW, "tower_sentry_tower": GW, "myrkwood_forest_mora_riders": SF}}
json.dump(d105, open(R + 'rep105_myrkwood.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
from collections import Counter
for d in (d102, d103, d105):
    print(d['zone'], len(d['quests']), Counter(d['quests'].values()))
