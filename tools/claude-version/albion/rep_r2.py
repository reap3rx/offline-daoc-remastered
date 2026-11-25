"""Round 2's reputation (claude 2026-11-24, "Albion - the plan"): Salisbury Plains - the Sisters of Amesbury (and the
Pendragon's Watch, shared, with a quartermaster in West Downs); Campacorentin Forest - the Ulfwych Rangers and the Thornwardens;
Avalon Marsh - the Marsh Wardens and the Keepers of the Isle. Kin, as in Hibernia: the realm's soldiers (the Watch, the Wardens of
Cotswold, the Rangers, the Marsh Wardens) and its keepers of the old ways (the Abbey Faithful, the Sisters, the Thornwardens,
the Keepers of the Isle)."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
import story_salisbury_plains as sp, story_campacorentin as cf, story_avalon_marsh as am
R = '/home/claude/lg/source/server/GameServer/scripts/reputation/'
SOLDIERS = ["pendragons_watch", "wardens_of_cotswold", "ulfwych_rangers", "marsh_wardens"]
LORE = ["abbey_faithful", "sisters_of_amesbury", "thornwardens", "keepers_of_the_isle"]
WA = 'pendragons_watch'
WATCH_STOCK = [{"item": "rep000_watch_friend_s_ring", "rank": "Trusted", "price": 40},
               {"item": "rep000_watch_road_belt", "rank": "Trusted", "price": 40},
               {"item": "rep000_sworn_torc_of_the_watch", "rank": "Honoured", "price": 80},
               {"item": "rep000_round_table_bracer", "rank": "Honoured", "price": 80},
               {"item": "rep000_mantle_of_the_shield_of_camelot", "rank": "Legend", "price": 150}]
def kin(k): return [x for x in (SOLDIERS if k in SOLDIERS else LORE) if x != k]
def qm(name, guild, model, anchor, greet, items, off=(4, 3)):
    ranks = ["Trusted", "Trusted", "Honoured", "Honoured", "Legend"]
    prices = [40, 40, 80, 80, 150]
    return {"name": name, "guild": guild, "model": model, "anchor": anchor, "offset": list(off), "greet": greet,
            "stock": [{"item": i, "rank": r, "price": p} for i, r, p in zip(items, ranks, prices)]}

SA = 'sisters_of_amesbury'
watch_q = {'sp_wild_herd', 'sp_carrion', 'sp_diggers', 'sp_paymaster', 'sp_mephits', 'sp_footprints', 'sp_runaways', 'sp_cottrel',
           'sp_the_dance', 'sp_giants_swine', 'white_horse'}
d1 = {"zone": 1, "name": "Salisbury Plains", "levels": [10, 26], "realm": 1,
      "factions": [{"key": SA, "name": "the Sisters of Amesbury", "short": "the Sisters", "kin": kin(SA),
                    "titles": ["Friend of Amesbury", "Keeper of the Graves", "Mourner of the Long Knives"],
                    "speaker": "sp_abbess", "town": "West Downs",
                    "kills": ["ghast", "presence", "wandering spirit", "undead druid", "tomb raider", "raider", "hengist", "feast-master",
                              "giant skeleton", "gogmagog", "legionnaire", "liglim", "cynewulf", "slaver", "cottrel"],
                    "quartermaster": qm("Sister Almoner Ebba", SA[:0] + "the Sisters of Amesbury", 38, "sp_abbess",
                                        "Amesbury's gifts, for those who keep faith with the dead. Show me your standing.",
                                        ["rep001_friend_of_amesbury_s_ring", "rep001_grave_tender_s_belt", "rep001_keeper_of_the_graves_torc",
                                         "rep001_long_knives_bracer", "rep001_mantle_of_the_mourner"])}],
      "shared": [WA],
      "quartermasters": [dict(qm("Watch-Quartermaster Bedwin", "the Pendragon's Watch", 9, "sp_osfrid",
                                 "Rhun keeps the stores at Prydwen; I keep them here. Same stock, same rules - show me your standing with the Watch.",
                                 [s["item"] for s in WATCH_STOCK], (-4, 3)), faction=WA)],
      "kill_default": WA, "event_default": WA, "quest_default": SA,
      "quests": {q['id']: (WA if q['id'] in watch_q else SA) for q in sp.ZONES[0].quests},
      "events": {"sp_dance_assault": SA, "sp_dance_return": SA, "sp_feast_night": SA, "salisbury_plains_restless_plain": SA,
                 "salisbury_plains_tomb_robbers": SA, "sp_giants_muster": WA, "salisbury_plains_spriggarn_ambush": WA,
                 "salisbury_plains_basilisk_nest": WA}}
json.dump(d1, open(R + 'rep001_salisbury_plains.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

UR, TW = 'ulfwych_rangers', 'thornwardens'
thorn_q = {'cf_druid_barrow', 'cf_pixie_queen', 'cf_blood_roots', 'cf_druids_way', 'cf_merlins_thorn', 'cf_scroll', 'heretic', 'cf_waking_wood'}
d8 = {"zone": 8, "name": "Campacorentin Forest", "levels": [6, 24], "realm": 1,
      "factions": [{"key": UR, "name": "the Ulfwych Rangers", "short": "the Rangers", "kin": kin(UR),
                    "titles": ["Friend of the Rangers", "Ranger of Ulfwych", "Warden of the Greenway"],
                    "speaker": "cf_gwion", "town": "Caer Ulfwych",
                    "kills": ["goblin", "poacher", "ogre", "gorrak", "spider", "ciraron", "bandit", "wolf", "lion", "green man", "green knight",
                              "wisp", "longlegs", "grizzletooth", "thornpaw", "urfgrat"],
                    "quartermaster": qm("Ranger-Quartermaster Cadfan", "the Ulfwych Rangers", 9, "cf_gwion",
                                        "Rangers' kit, for the Rangers' friends. Show me your standing.",
                                        ["rep008_ranger_s_leaf_pin", "rep008_greenway_belt", "rep008_ulfwych_torc", "rep008_thorn_keeper_s_bracer",
                                         "rep008_mantle_of_the_greenway_warden"])},
                   {"key": TW, "name": "the Thornwardens", "short": "the Thornwardens", "kin": kin(TW),
                    "titles": ["Friend of the Thorn", "Keeper of the Sleep", "Thornwarden of Campacorentin"],
                    "speaker": "cf_elaine", "town": "Caer Ulfwych",
                    "kills": ["sacrificer", "crimson", "minion", "druid", "undead druid", "filidh", "pixie", "witch", "elithralia",
                              "accolon", "root-bleeder", "presence", "fellwood", "oak man"],
                    "quartermaster": qm("Thornwarden Olwen", "the Thornwardens", 38, "cf_elaine",
                                        "The thorn's gifts, for those who keep the old man's sleep. Show me your standing.",
                                        ["rep008_thornwarden_s_briar_charm", "rep008_sleep_keeper_s_ring", "rep008_thorn_keeper_s_bracer",
                                         "rep008_ulfwych_torc", "rep008_mantle_of_the_thornwarden"], (-4, 3))}],
      "kill_default": UR, "event_default": UR, "quest_default": UR,
      "quests": {q['id']: (TW if q['id'] in thorn_q else UR) for q in cf.ZONES[0].quests},
      "events": {"cf_thorn_night": TW, "cf_green_knight": UR, "campacorentin_forest_restless_knights": TW}}
json.dump(d8, open(R + 'rep008_campacorentin.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

MW, KI = 'marsh_wardens', 'keepers_of_the_isle'
isle_q = {'am_mists', 'am_black_barge', 'am_fallen_paladins', 'am_way_to_isle'}
d9 = {"zone": 9, "name": "Avalon Marsh", "levels": [5, 26], "realm": 1,
      "factions": [{"key": MW, "name": "the Marsh Wardens", "short": "the Wardens", "kin": kin(MW),
                    "titles": ["Friend of the Wardens", "Marsh-Warden", "Warden of the Drowned March"],
                    "speaker": "warden_brec", "town": "Caer Witrin",
                    "kills": ["bogman", "scrag", "scraek", "shambler", "golem", "giant", "wolf", "mist monster", "marsh lord", "ghoul", "vrask",
                              "lord-commander", "wisp", "leaper", "ogre", "bloody-bones", "zombie"],
                    "quartermaster": qm("Warden-Quartermaster Hefin", "the Marsh Wardens", 74, "warden_brec",
                                        "Wardens' kit - waxed, tarred and nearly dry. Show me your standing.",
                                        ["rep009_marsh_friend_s_ring", "rep009_wader_s_belt", "rep009_drowned_march_torc", "rep009_isle_mist_bracer",
                                         "rep009_mantle_of_the_drowned_march"])},
                   {"key": KI, "name": "the Keepers of the Isle", "short": "the Keepers", "kin": kin(KI),
                    "titles": ["Friend of the Isle", "Keeper of the Shore", "Guardian of the Sleeper"],
                    "speaker": "am_argante", "town": "the Isle's shore",
                    "kills": ["mist sprite", "phantom", "ghostly knight", "fiedel", "aryon", "oarsman", "oarsmaster", "crimson", "initiate",
                              "morgause", "pixie"],
                    "quartermaster": qm("Keeper Nimuel", "the Keepers of the Isle", 38, "am_argante",
                                        "The Isle's gifts, for those who keep the King's sleep. Show me your standing.",
                                        ["rep009_shore_keeper_s_charm", "rep009_apple_isle_ring", "rep009_isle_mist_bracer", "rep009_drowned_march_torc",
                                         "rep009_mantle_of_the_sleeper_s_guard"], (-4, 3))}],
      "kill_default": MW, "event_default": MW, "quest_default": MW,
      "quests": {q['id']: (KI if q['id'] in isle_q else MW) for q in am.ZONES[0].quests},
      "events": {"am_black_barge_night": KI, "am_vigil_assault": MW, "am_vigil_return": MW}}
json.dump(d9, open(R + 'rep009_avalon_marsh.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

# round 1's factions get their kin
for f in ['rep000_camelot_hills', 'rep002_black_mtns_south']:
    p = R + f + '.json'
    j = json.load(open(p, encoding='utf-8'))
    for fa in j['factions']:
        fa['kin'] = kin(fa['key'])
    json.dump(j, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d1['quests']), len(d8['quests']), len(d9['quests']))
