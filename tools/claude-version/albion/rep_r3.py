"""Round 3's reputation (claude 2026-11-24, "Albion - the plan"): Black Mountains North - the Snowdonia Garrison and the Emrys
Circle; Cornwall - the Men of Tintagel and the Oath of Corineus; Lyonesse - the Lyonesse Remnant and the Harpers of Tristan. Each
joins Albion's soldiers or its keepers of the old ways as kin."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
import story_black_mtns_north as bn, story_cornwall as cw, story_lyonesse as ly
R = '/home/claude/lg/source/server/GameServer/scripts/reputation/'
SOLDIERS = ["pendragons_watch", "wardens_of_cotswold", "ulfwych_rangers", "marsh_wardens", "snowdonia_garrison", "men_of_tintagel", "lyonesse_remnant"]
LORE = ["abbey_faithful", "sisters_of_amesbury", "thornwardens", "keepers_of_the_isle", "emrys_circle", "oath_of_corineus", "harpers_of_tristan"]
def kin(k): return [x for x in (SOLDIERS if k in SOLDIERS else LORE) if x != k]
def qm(name, guild, model, anchor, greet, items, off=(4, 3)):
    ranks = ["Trusted", "Trusted", "Honoured", "Honoured", "Legend"]
    prices = [40, 40, 80, 80, 150]
    return {"name": name, "guild": guild, "model": model, "anchor": anchor, "offset": list(off), "greet": greet,
            "stock": [{"item": i, "rank": r, "price": p} for i, r, p in zip(items, ranks, prices)]}
def fac(key, name, short, titles, speaker, town, kills, quartermaster):
    return {"key": key, "name": name, "short": short, "kin": kin(key), "titles": titles, "speaker": speaker, "town": town,
            "kills": kills, "quartermaster": quartermaster}
def zone(zid, name, levels, f1, f2, _d, quests, second_q, events):
    return {"zone": zid, "name": name, "levels": levels, "realm": 1, "factions": [f1, f2],
            "kill_default": f1["key"], "event_default": f1["key"], "quest_default": f1["key"],
            "quests": {q['id']: (f2["key"] if q['id'] in second_q else f1["key"]) for q in quests}, "events": events}

SG, EC = 'snowdonia_garrison', 'emrys_circle'
d3 = zone(3, "Black Mountains North", [16, 30],
    fac(SG, "the Snowdonia Garrison", "the Garrison", ["Friend of the Garrison", "Snowdonia Shieldman", "Warden of the North March"],
        "bn_rhydderch", "Swanton Keep", ["warg", "smuggler", "tracker", "forest chief", "cockatrice", "beak", "hill", "alrek", "goblin", "maiden",
                                         "lion", "spider", "smugluk"],
        qm("Garrison-Quartermaster Iolo", "the Snowdonia Garrison", 9, "bn_rhydderch", "Garrison kit, for the Garrison's friends. Show me your standing.",
           ["rep003_garrison_friend_s_ring", "rep003_north_march_belt", "rep003_snowdonia_shieldman_s_torc", "rep003_dragon_reader_s_bracer",
            "rep003_mantle_of_the_north_march"])),
    fac(EC, "the Emrys Circle", "the Circle", ["Friend of Emrys", "Dragon-Reader", "Keeper of Emrys's Fort"],
        "bn_taliesin", "Snowdonia Station", ["crimson", "acolyte", "priest", "priestess", "hierarch", "pit-warden", "necromancer", "sacrificer",
                                             "filidh", "undead druid", "cauld lad", "arawnite"],
        qm("Circle-Keeper Morfudd", "the Emrys Circle", 38, "bn_taliesin", "The Circle's gifts, for those who keep the prophecies. Show me your standing.",
           ["rep003_emrys_charm", "rep003_prophet_s_ring", "rep003_dragon_reader_s_bracer", "rep003_snowdonia_shieldman_s_torc",
            "rep003_mantle_of_the_dragon_readers"], (-4, 3))),
    None, bn.ZONES[0].quests,
    {'bn_prophets_graves', 'bn_red_cords_south', 'bn_cauld_lad', 'bn_necromancers', 'bn_dragons_pit', 'crimson_bargain'},
    {"bn_pit_fires": EC, "bn_dinas_assault": SG, "bn_dinas_raid": SG, "bn_dinas_return": SG})
MT, OC = 'men_of_tintagel', 'oath_of_corineus'
d6 = zone(6, "Cornwall", [2, 44],
    fac(MT, "the Men of Tintagel", "Tintagel", ["Friend of Tintagel", "Tintagel Shieldman", "Duke's Champion"],
        "lt_penhale", "Cornwall Station", ["wolf", "bear", "spider", "ghostly", "jarrel", "den mother", "pack leader", "stalker", "cat",
                                           "boogey", "rooter"],
        qm("Sergeant-Quartermaster Hedra", "the Men of Tintagel", 38, "cw_jory", "Tintagel's stores, for Tintagel's friends. Show me your standing.",
           ["rep006_tintagel_friend_s_ring", "rep006_duke_s_road_belt", "rep006_tintagel_shieldman_s_torc", "rep006_giant_wrestler_s_bracer",
            "rep006_mantle_of_the_duke_s_champion"])),
    fac(OC, "the Oath of Corineus", "the Oath", ["Oath-Friend", "Giant-Wrestler", "Heir of Corineus"],
        "cw_gerens", "Cornwall Station", ["giant", "legionnaire", "centurion", "legate", "aquilifer", "ninth", "cirfans", "drake", "muryan",
                                          "bucca", "beech", "aricoer", "favius", "tusker"],
        qm("Oath-Keeper Wenna", "the Oath of Corineus", 38, "cw_gerens", "The Oath's gifts, for those who stand against giants. Show me your standing.",
           ["rep006_oath_friend_s_charm", "rep006_corinean_ring", "rep006_giant_wrestler_s_bracer", "rep006_tintagel_shieldman_s_torc",
            "rep006_mantle_of_the_heir_of_corineus"], (-4, 3))),
    None, cw.ZONES[0].quests,
    {'cw_muryans', 'cw_buccas', 'cw_old_beeches', 'cw_rooters', 'cw_ninth_road', 'cw_favius', 'cw_eagle', 'cw_giant_graves', 'cw_quarry_road',
     'cw_cirfans', 'drowned_ninth'},
    {"cw_eagle_marches": OC, "cw_bucca_storm": OC})
LR, HT = 'lyonesse_remnant', 'harpers_of_tristan'
d10 = zone(10, "Lyonesse", [40, 52],
    fac(LR, "the Lyonesse Remnant", "the Remnant", ["Friend of the Remnant", "Remnant Knight", "Sword of Lyonesse"],
        "ly_meliot", "the Remnant's camp", ["peallaidh", "storm", "bone snapper", "moorlich", "knight", "footman", "pikeman", "meliodas",
                                            "lizard", "freybug", "goblin", "dunter"],
        qm("Remnant-Quartermaster Cador", "the Lyonesse Remnant", 9, "ly_meliot", "What the Remnant saved from the sea. Show me your standing.",
           ["rep010_remnant_friend_s_ring", "rep010_remnant_knight_s_belt", "rep010_sword_of_lyonesse_torc", "rep010_harper_s_bracer",
            "rep010_mantle_of_the_sword_of_lyonesse"])),
    fac(HT, "the Harpers of Tristan", "the Harpers", ["Friend of the Harp", "Harper of Lyonesse", "Keeper of Tristan's Lay"],
        "ly_gwennol", "the Remnant's camp", ["hamadryad", "witherwoode", "cailleach", "hound", "sailor", "captain", "priest of arawn",
                                             "arawnite", "shepherd", "farmer", "townsman", "bwca"],
        qm("Harper Elowen", "the Harpers of Tristan", 38, "ly_gwennol", "The Harpers' gifts, for those who keep the songs. Show me your standing.",
           ["rep010_harp_friend_s_charm", "rep010_lay_keeper_s_ring", "rep010_harper_s_bracer", "rep010_sword_of_lyonesse_torc",
            "rep010_mantle_of_tristan_s_lay"], (-4, 3))),
    None, ly.ZONES[0].quests,
    {'ly_tristans_harp', 'ly_black_sail', 'ly_hamadryads', 'ly_gabriel_hounds', 'ly_witherwoode', 'ly_cailleach', 'last_evening', 'ly_last_day'},
    {"ly_white_storm": LR, "ly_black_sail_night": HT})
for d, f in [(d3, 'rep003_black_mtns_north'), (d6, 'rep006_cornwall'), (d10, 'rep010_lyonesse')]:
    json.dump(d, open(R + f + '.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for f in ['rep000_camelot_hills', 'rep002_black_mtns_south', 'rep001_salisbury_plains', 'rep008_campacorentin', 'rep009_avalon_marsh']:
    p = R + f + '.json'
    j = json.load(open(p, encoding='utf-8'))
    for fa in j['factions']:
        fa['kin'] = kin(fa['key'])
    json.dump(j, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d3['quests']), len(d6['quests']), len(d10['quests']))
