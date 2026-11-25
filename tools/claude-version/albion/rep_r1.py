"""Round 1's reputation (claude 2026-11-24, "Albion - the plan"): Camelot Hills - the Wardens of Cotswold and the Pendragon's
Watch (its home; shared with Black Mountains South, and Salisbury next); Black Mountains South - the Abbey Faithful, with a
Watch quartermaster in Humberton."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
import story_camelot_hills as ch
import story_black_mtns_south as bs
R = '/home/claude/lg/source/server/GameServer/scripts/reputation/'
WD, WA, AF = 'wardens_of_cotswold', 'pendragons_watch', 'abbey_faithful'

ward_q = {'bell_price', 'ch_wolves_at_the_fold', 'ch_still_wheel', 'ch_little_green_legs', 'ch_ants_in_the_furrow', 'ch_kings_deer',
          'ch_kings_road', 'ch_cronker'}
WATCH_STOCK = [{"item": "rep000_watch_friend_s_ring", "rank": "Trusted", "price": 40},
               {"item": "rep000_watch_road_belt", "rank": "Trusted", "price": 40},
               {"item": "rep000_sworn_torc_of_the_watch", "rank": "Honoured", "price": 80},
               {"item": "rep000_round_table_bracer", "rank": "Honoured", "price": 80},
               {"item": "rep000_mantle_of_the_shield_of_camelot", "rank": "Legend", "price": 150}]
WATCH_KILLS = ["crimson", "acolyte", "initiate", "hierophant", "undead filidh", "zombie", "skeleton", "spirit", "demon", "manes", "grumoz",
               "gorgoth", "fielath", "difwych", "grugyn", "bandit", "thaumaturge", "gamwell", "highwayman", "robber", "goblin", "red dwarf",
               "dwarf raider", "dwarf pillager", "frund", "agisthil", "grilk", "gobzini", "salizern", "spectral", "drowned", "giant spider"]
d0 = {
 "zone": 0, "name": "Camelot Hills", "levels": [1, 14], "realm": 1,
 "factions": [
  {"key": WD, "name": "the Wardens of Cotswold", "short": "the Wardens", "kin": [],
   "titles": ["Friend of Cotswold", "Warden's Right Hand", "Hearthward of Cotswold"],
   "speaker": "ch_warden_hollis", "town": "Cotswold",
   "kills": ["wolf", "sprite", "spriggarn", "dragon ant", "cutpurse", "poacher", "bandit", "drake", "frog", "snake", "sow", "boar",
             "bear", "spider", "thwori", "cronker", "faerie"],
   "quartermaster": {"name": "Warden-Quartermaster Edith", "guild": "the Wardens of Cotswold", "model": 38, "anchor": "ch_warden_hollis",
     "offset": [4, 3], "greet": "Cotswold looks after its own. Show me your standing with the Wardens.",
     "stock": [{"item": "rep000_friend_of_cotswold_s_ring", "rank": "Trusted", "price": 40},
               {"item": "rep000_hedge_warden_s_belt", "rank": "Trusted", "price": 40},
               {"item": "rep000_right_hand_s_torc", "rank": "Honoured", "price": 80},
               {"item": "rep000_cotswold_fold_bracer", "rank": "Honoured", "price": 80},
               {"item": "rep000_mantle_of_the_hearthward", "rank": "Legend", "price": 150}]}},
  {"key": WA, "name": "the Pendragon's Watch", "short": "the Watch", "kin": [],
   "titles": ["Watch-Friend", "Sworn to the Watch", "Shield of Camelot"],
   "speaker": "ch_captain_bonswell", "town": "Prydwen Keep", "kills": WATCH_KILLS,
   "quartermaster": {"name": "Watch-Quartermaster Rhun", "guild": "the Pendragon's Watch", "model": 9, "anchor": "ch_captain_bonswell",
     "offset": [-4, 3], "greet": "The Round Table's own stores, for those the Watch can count on. Show me your standing.",
     "stock": WATCH_STOCK}}],
 "kill_default": WA, "event_default": WA, "quest_default": WA,
 "quests": {q['id']: (WD if q['id'] in ward_q else WA) for q in ch.ZONES[0].quests},
 "events": {"camelot_hills_bandit_hollow": WD, "camelot_hills_ant_nest": WD, "camelot_hills_orchard_spriggarn": WD,
            "camelot_hills_barrow_wakes": WA, "ch_crimson_rite": WA, "ch_hunt_rides": WA, "ch_df_door": WA}}
json.dump(d0, open(R + 'rep000_camelot_hills.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

faith_q = {'willing_heart', 'bs_bishops_letters', 'bs_bells_of_vetusta', 'bs_dark_bishop', 'bs_camlann_dead', 'bs_drowned_reach', 'bs_badon_cairn'}
d2 = {
 "zone": 2, "name": "Black Mountains South", "levels": [1, 17], "realm": 1,
 "factions": [
  {"key": AF, "name": "the Abbey Faithful", "short": "the Faithful", "kin": [],
   "titles": ["Friend of the Abbey", "Keeper of the Hours", "Bell-Ringer of Vetusta"],
   "speaker": "bs_prior_anselm", "town": "Humberton",
   "kills": ["dark brother", "crimson", "sacrificer", "devout filidh", "filidh", "skeleton", "spectral", "drowned", "undead goblin",
             "abbot", "hrodric", "burhoff", "harish", "salizern", "initiate"],
   "quartermaster": {"name": "Brother Almoner Cuthbert", "guild": "the Abbey Faithful", "model": 32, "anchor": "bs_prior_anselm",
     "offset": [4, 3], "greet": "What the abbey could carry out with it, for the abbey's friends. Show me your standing with the Faithful.",
     "stock": [{"item": "rep002_lay_brother_s_charm", "rank": "Trusted", "price": 40},
               {"item": "rep002_white_cord_of_vetusta", "rank": "Trusted", "price": 40},
               {"item": "rep002_psalter_chain_torc", "rank": "Honoured", "price": 80},
               {"item": "rep002_cloister_stone_bracer", "rank": "Honoured", "price": 80},
               {"item": "rep002_mantle_of_the_bell_ringer", "rank": "Legend", "price": 150}]}}],
 "shared": [WA],
 "quartermasters": [{"faction": WA, "name": "Watch-Quartermaster Ifor", "guild": "the Pendragon's Watch", "model": 9,
                     "anchor": "bs_sergeant_mabyn", "offset": [4, 3],
                     "greet": "Rhun keeps the stores at Prydwen; I keep them here. Same stock, same rules - show me your standing with the Watch.",
                     "stock": WATCH_STOCK}],
 "kill_default": WA, "event_default": WA, "quest_default": WA,
 "quests": {q['id']: (AF if q['id'] in faith_q else WA) for q in bs.ZONES[0].quests},
 "events": {"bs_vetusta_assault": AF, "bs_vetusta_return": AF, "bs_badon_dead": AF, "black_mountains_south_goblin_fishers": WA,
            "black_mountains_south_red_dwarf_raid": WA, "black_mountains_south_highway_robbery": WA, "black_mountains_south_spider_hollow": WA}}
json.dump(d2, open(R + 'rep002_black_mtns_south.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d0['quests']), len(d2['quests']))
