"""Midgard round 3's reputation (claude 2026-11-25, "Midgard - the plan"): Muspelheim - the Forge of Khizil (and King Eirik's
Huscarls, shared, with a quartermaster at Brika's camp); Skona Ravine - the Wolfsbane Rangers and the Seithkona Circle; Vanern
Swamp - the Wardens of Vanern (and the Huscarls, with a quartermaster at the Wardens' camp). Kin: midkin.py."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from midkin import kin
from rep_m2 import HUS_STOCK, stock, qm
import story_muspelheim as mu, story_skona as sk, story_vanern as vn
R = '/home/claude/lg/source/server/GameServer/scripts/reputation/'
EH, KF, WR, SC, VW = 'eiriks_huscarls', 'khizil_forge', 'wolfsbane_rangers', 'seithkona_circle', 'vanern_wardens'
BY_TEXT = {"From King Eirik's Huscarls.": EH, "From the Forge of Khizil.": KF, "From the Wolfsbane Rangers.": WR,
           "From the Seithkona Circle.": SC, "From the Wardens of Vanern.": VW}
def owner(q, old):
    return old[q['id']] if q['id'] in old else BY_TEXT[q['endings']['default']['text']]

d104 = {
 "zone": 104, "name": "Muspelheim", "levels": [18, 28], "realm": 2,
 "factions": [
  {"key": KF, "name": "the Forge of Khizil", "short": "the Forge", "kin": kin(KF),
   "titles": ["Forge-Friend", "Hammer of Khizil", "Keeper of the Forge-Fire"], "speaker": "mu_thrain", "town": "Khizil's forge",
   "kills": ["dverge", "ashmonger", "soot", "flame thrower", "ashen", "fire ant", "sulphur", "fire flower", "lava lizard", "fire toad",
             "fire giant", "raukomaz", "tasm"],
   "quartermaster": {"name": "Forge-Quartermaster Dvalinn", "guild": "the Forge of Khizil", "model": 185, "anchor": "mu_thrain",
     "offset": [4, 3], "greet": "The forge's work, for those the forge can trust. Show me your standing.",
     "stock": stock("rep104_", ["forge_friend_s_ring", "khizil_smith_belt", "hammer_of_khizil_torc", "anvil_iron_bracer",
                                "mantle_of_the_forge_fire"])}}],
 "shared": [EH],
 "quartermasters": [qm(EH, "Huscarl-Quartermaster Hrolleif", "mu_hallkel", 213,
                       "The King's stores at Brika's camp, same stock as Mularn. Show me your standing with the Huscarls.")],
 "kill_default": EH, "event_default": EH, "quest_default": KF,
 "quests": {q['id']: owner(q, {'dagnar': EH, 'ragnvald': EH}) for q in mu.ZONES[0].quests},
 "events": {"mu_brood_sire": EH, "mu_forge_fire": KF, "muspelheim_fire_giant_outpost": EH, "muspelheim_burnt_sentries": EH,
            "muspelheim_wyrm_nest": EH, "muspelheim_fire_ants": KF}}
json.dump(d104, open(R + 'rep104_muspelheim.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

d106 = {
 "zone": 106, "name": "Skona Ravine", "levels": [28, 38], "realm": 2,
 "factions": [
  {"key": WR, "name": "the Wolfsbane Rangers", "short": "the Rangers", "kin": kin(WR),
   "titles": ["Ranger-Friend", "Wolfsbane-Sworn", "Breaker of Ulfhamr"], "speaker": "sk_jodur", "town": "the Stor Gothi's camp",
   "kills": ["werewolf", "wolfaur", "wolverine", "timber", "badger", "mauler", "brush cat", "wood rat", "orm", "sidhe"],
   "quartermaster": {"name": "Ranger-Quartermaster Hrefna", "guild": "the Wolfsbane Rangers", "model": 168, "anchor": "sk_jodur",
     "offset": [4, 3], "greet": "The Rangers' stores, for those who hunt with us. Show me your standing.",
     "stock": stock("rep106_", ["ranger_friend_s_ring", "wolfsbane_belt", "wolfsbane_sworn_torc", "grey_ranger_bracer",
                                "mantle_of_the_ulfhamr_breaker"])}},
  {"key": SC, "name": "the Seithkona Circle", "short": "the Circle", "kin": kin(SC),
   "titles": ["Circle-Friend", "Moon-Reader", "Keeper of the Moon-Stone"], "speaker": "sk_saga", "town": "the Seithkona Circle",
   "kills": ["tingler", "wind spirit", "tree frog", "willow", "skogsfru", "dryad", "treekeep", "moss maiden", "tree spirit", "drake"],
   "quartermaster": {"name": "Seithkona Thorhild", "guild": "the Seithkona Circle", "model": 157, "anchor": "sk_saga",
     "offset": [4, 3], "greet": "The Circle's gifts, for those who guard the moon. Show me your standing.",
     "stock": stock("rep106_", ["circle_friend_s_charm", "moon_reader_s_ring", "moon_phase_bracer", "wolfsbane_sworn_torc",
                                "mantle_of_the_moon_stone"])}}],
 "kill_default": WR, "event_default": WR, "quest_default": WR,
 "quests": {q['id']: owner(q, {'moonbound': SC, 'sidhe_maps': WR}) for q in sk.ZONES[0].quests},
 "events": {"sk_red_moon": SC, "sk_ulfhamr_assault": WR, "sk_ulfhamr_return": WR, "skona_ravine_werewolf_warders": WR,
            "skona_ravine_wolfaur_headsmen": WR, "skona_ravine_dryad_grove": SC}}
json.dump(d106, open(R + 'rep106_skona.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

d107 = {
 "zone": 107, "name": "Vanern Swamp", "levels": [36, 46], "realm": 2,
 "factions": [
  {"key": VW, "name": "the Wardens of Vanern", "short": "the Wardens", "kin": kin(VW),
   "titles": ["Warden-Friend", "Raven of Vanern", "Holder of Hrafnsholm"], "speaker": "vn_steinunn", "town": "the Wardens' camp",
   "kills": ["hagbui", "jotun", "orm", "mud crab", "mud frog", "viper", "spider"],
   "quartermaster": {"name": "Warden-Quartermaster Orlyg", "guild": "the Wardens of Vanern", "model": 213, "anchor": "vn_steinunn",
     "offset": [4, 3], "greet": "The Wardens' stores, for those who stand the watch with us. Show me your standing.",
     "stock": stock("rep107_", ["warden_friend_s_ring", "bog_iron_belt", "raven_of_vanern_torc", "rowan_ward_bracer",
                                "mantle_of_hrafnsholm"])}}],
 "shared": [EH],
 "quartermasters": [qm(EH, "Huscarl-Quartermaster Ulf", "vn_gisli", 213,
                       "The King's stores in Vanern, what's left of them. Same stock as Mularn. Show me your standing with the Huscarls.")],
 "kill_default": VW, "event_default": VW, "quest_default": VW,
 "quests": {q['id']: owner(q, {'clay_child': VW, 'barrow_brother': VW}) for q in vn.ZONES[0].quests},
 "events": {"vn_ice_road": EH, "vn_hrafnsholm_assault": VW, "vn_hrafnsholm_return": VW, "vanern_swamp_hagbui_barrow": VW,
            "vanern_swamp_clay_jotun": VW, "vanern_swamp_black_orms": EH}}
json.dump(d107, open(R + 'rep107_vanern.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
from collections import Counter
for d in (d104, d106, d107):
    print(d['zone'], len(d['quests']), Counter(d['quests'].values()))
