"""Round 4's reputation (claude 2026-11-24, "Albion - the plan"): Llyn Barfog - the Knights of the Lake and the Maidens of the Lake;
Dartmoor - the Dragon-Watch and the Quarry-Oath of Grimspound. Each joins Albion's soldiers or its keepers of the old ways as kin
(and every earlier Albion faction learns its new kin)."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
import story_llyn_barfog as lb, story_dartmoor as dm
R = '/home/claude/lg/source/server/GameServer/scripts/reputation/'
SOLDIERS = ["pendragons_watch", "wardens_of_cotswold", "ulfwych_rangers", "marsh_wardens", "snowdonia_garrison", "men_of_tintagel",
            "lyonesse_remnant", "knights_of_the_lake", "dragon_watch"]
LORE = ["abbey_faithful", "sisters_of_amesbury", "thornwardens", "keepers_of_the_isle", "emrys_circle", "oath_of_corineus",
        "harpers_of_tristan", "maidens_of_the_lake", "quarry_oath"]
def kin(k): return [x for x in (SOLDIERS if k in SOLDIERS else LORE) if x != k]
def qm(name, guild, model, anchor, greet, items, off=(4, 3)):
    ranks = ["Trusted", "Trusted", "Honoured", "Honoured", "Legend"]
    prices = [40, 40, 80, 80, 150]
    return {"name": name, "guild": guild, "model": model, "anchor": anchor, "offset": list(off), "greet": greet,
            "stock": [{"item": i, "rank": r, "price": p} for i, r, p in zip(items, ranks, prices)]}
def fac(key, name, short, titles, speaker, town, kills, quartermaster):
    return {"key": key, "name": name, "short": short, "kin": kin(key), "titles": titles, "speaker": speaker, "town": town,
            "kills": kills, "quartermaster": quartermaster}
def zone(zid, name, levels, f1, f2, quests, second_q, events):
    return {"zone": zid, "name": name, "levels": levels, "realm": 1, "factions": [f1, f2],
            "kill_default": f1["key"], "event_default": f1["key"], "quest_default": f1["key"],
            "quests": {q['id']: (f2["key"] if q['id'] in second_q else f1["key"]) for q in quests}, "events": events}

KL, ML = 'knights_of_the_lake', 'maidens_of_the_lake'
ev7 = {c: KL for c in ["lb_cp1_assault", "lb_cp2_assault", "lb_cp3_assault", "lb_cp4_assault", "lb_cp1_counter", "lb_cp2_counter",
                       "lb_cp3_counter", "lb_cp4_counter", "lb_gate_of_annwn", "llyn_barfog_renegades"]}
ev7.update({"lb_still_night": ML, "llyn_barfog_hounds_of_annwn": ML, "llyn_barfog_unshriven": ML})
d7 = zone(7, "Llyn Barfog", [44, 55],
    fac(KL, "the Knights of the Lake", "the Lake's knights", ["Friend of the Lake", "Knight of the Lake", "the Lady's Champion"],
        "lb_bors", "the Barfog merchants", ["toad", "afanc", "crimson", "gatekeeper", "guardian", "fay knight", "branwen", "iddawc",
                                            "guiomar", "morgana", "renegade", "bear", "boar", "gorger", "adder"],
        qm("Lake-Quartermaster Ector", "the Knights of the Lake", 28, "lb_bors", "The Lake's armoury, for the Lake's friends. Show me your standing.",
           ["rep007_lake_friend_s_ring", "rep007_shore_knight_s_belt", "rep007_knight_of_the_lake_s_torc", "rep007_white_cattle_bracer",
            "rep007_mantle_of_the_lady_s_champion"])),
    fac(ML, "the Maidens of the Lake", "the Maidens", ["Maiden-Friend", "Friend of the Lady", "Daughter of the Lake"],
        "lb_lunete", "the Barfog merchants", ["hound", "cwn annwn", "huntsman", "cythraul", "gwr-drwgiaid", "gwrgi", "necromancer",
                                             "bwgan", "bwgwl", "monk", "legion", "shade", "king of the barfog", "cyclops"],
        qm("Maiden Elaine", "the Maidens of the Lake", 38, "lb_lunete", "The Lady's gifts, for those who keep her lake. Show me your standing.",
           ["rep007_maiden_friend_s_charm", "rep007_lady_s_ring", "rep007_white_cattle_bracer", "rep007_knight_of_the_lake_s_torc",
            "rep007_mantle_of_the_lake_s_daughter"], (-4, 3))),
    lb.ZONES[0].quests,
    {'hounds', 'lb_huntsman', 'lb_cattle', 'lb_cythraul', 'lb_hill_king', 'psalter', 'lb_legion', 'lb_letters', 'lb_lady'},
    ev7)
DW, QO = 'dragon_watch', 'quarry_oath'
ev4 = {c: DW for c in ["dm_cp1_assault", "dm_cp2_assault", "dm_cp3_assault", "dm_cp4_assault", "dm_cp1_counter", "dm_cp2_counter",
                       "dm_cp3_counter", "dm_cp4_counter", "dm_giants_throne", "dartmoor_pounders"]}
ev4.update({"dm_dragons_breath": QO, "dartmoor_herdsmen_cairn": QO, "dartmoor_stonecallers": QO})
d4 = zone(4, "Dartmoor", [50, 60],
    fac(DW, "the Dragon-Watch", "the Watch", ["Watch-Friend", "Dragonslayer of the Watch", "the Dragon's Bane"],
        "bryn_asquith", "Grimspound", ["stonecrush", "excavator", "rockgrinder", "demolisher", "kez", "outlooker", "pounder",
                                       "stonelord", "gorm", "cormoran", "trehan", "krag", "golestandt", "brigand"],
        qm("Watch-Quartermaster Hob", "the Dragon-Watch", 28, "bryn_asquith", "The Watch's armoury, for the Watch's friends. Show me your standing.",
           ["rep004_watch_friend_s_ring", "rep004_slayer_s_road_belt", "rep004_dragon_watch_torc", "rep004_quarry_cut_bracer",
            "rep004_mantle_of_the_dragon_s_bane"])),
    fac(QO, "the Quarry-Oath of Grimspound", "the Oath", ["Oath-Friend of Grimspound", "Stonewright", "Keeper of the Quarry-Oath"],
        "dm_hedda", "Grimspound", ["herdsman", "gatherer", "stonecaller", "stoneshaper", "herald", "tegbuk", "knocker", "giant",
                                   "elder", "oracle", "stonemender", "reinforcer", "bodrugan", "ysgawen"],
        qm("Oath-Keeper Morwenna", "the Quarry-Oath of Grimspound", 38, "dm_hedda", "Grimspound's best, for the oath's friends. Show me your standing.",
           ["rep004_oath_friend_s_stone", "rep004_stonewright_s_ring", "rep004_quarry_cut_bracer", "rep004_dragon_watch_torc",
            "rep004_mantle_of_the_oath_keeper"], (-4, 3))),
    dm.ZONES[0].quests,
    {'quarry_oath', 'dm_ponies', 'dm_tegbuk', 'dm_stonecallers', 'dm_speaking_stone', 'dm_herald', 'dm_knockers'},
    ev4)
for d, f in [(d7, 'rep007_llyn_barfog'), (d4, 'rep004_dartmoor')]:
    json.dump(d, open(R + f + '.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for f in ['rep000_camelot_hills', 'rep002_black_mtns_south', 'rep001_salisbury_plains', 'rep008_campacorentin', 'rep009_avalon_marsh',
          'rep003_black_mtns_north', 'rep006_cornwall', 'rep010_lyonesse']:
    p = R + f + '.json'
    j = json.load(open(p, encoding='utf-8'))
    for fa in j['factions']:
        fa['kin'] = kin(fa['key'])
    json.dump(j, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d7['quests']), len(d4['quests']))
