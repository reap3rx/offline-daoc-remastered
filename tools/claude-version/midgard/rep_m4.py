"""Midgard round 4's reputation (claude 2026-11-25, "Midgard - the plan"): Raumarik - King Eirik's Host (the King's March; and the
Seithkona Circle, shared, with a quartermaster at the trappers' camp); Malmohus - the Oath of the Volur (the Dragon-Oath; and King
Eirik's Huscarls, shared, with a quartermaster at Halla's camp). The campaigns' hosts are these factions (MidgardCampaigns.cs).
Kin: midkin.py."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
sys.path.insert(0, '/home/claude/lg/tools/claude-version/midgard')
from midkin import kin
from rep_m2 import HUS_STOCK, stock
import story_raumarik as rk, story_malmohus as mh
R = '/home/claude/lg/source/server/GameServer/scripts/reputation/'
EH, KH, SC, VO = 'eiriks_huscarls', 'kings_host', 'seithkona_circle', 'volur_oath'
BY_TEXT = {"From King Eirik's Huscarls.": EH, "From King Eirik's Host.": KH, "From the Seithkona Circle.": SC,
           "From the Oath of the Volur.": VO}
def owner(q, old):
    return old[q['id']] if q['id'] in old else BY_TEXT[q['endings']['default']['text']]
CIRCLE_STOCK = stock("rep106_", ["circle_friend_s_charm", "moon_reader_s_ring", "moon_phase_bracer", "wolfsbane_sworn_torc",
                                 "mantle_of_the_moon_stone"])

d108 = {
 "zone": 108, "name": "Raumarik", "levels": [44, 54], "realm": 2,
 "factions": [
  {"key": KH, "name": "King Eirik's Host", "short": "the Host", "kin": kin(KH),
   "titles": ["Host-Friend", "Moon-Warden", "Breaker of Hati"], "speaker": "rk_steinar", "town": "the trappers' camp",
   "kills": ["fenrir", "winterwolf", "winter wolf", "wraith", "wight", "lich", "icestrider", "frost bound", "broadleaf", "bounty hunter",
             "wolverine", "wyvern", "cyclops", "undead"],
   "quartermaster": {"name": "Host-Quartermaster Gudrun", "guild": "King Eirik's Host", "model": 168, "anchor": "rk_steinar",
     "offset": [4, 3], "greet": "The Host's stores, for those who march with it. Show me your standing.",
     "stock": stock("rep108_", ["host_friend_s_ring", "king_s_host_belt", "moon_warden_torc", "frost_iron_bracer",
                                "mantle_of_hati_s_breaker"])}}],
 "shared": [SC],
 "quartermasters": [{"faction": SC, "name": "Seithkona Thordis", "guild": "the Seithkona Circle", "model": 157, "anchor": "rk_ylva",
                     "offset": [4, 3], "greet": "The Circle's gifts, carried north. Same as Skona's. Show me your standing with the Circle.",
                     "stock": CIRCLE_STOCK}],
 "kill_default": KH, "event_default": KH, "quest_default": KH,
 "quests": {q['id']: owner(q, {'red_dagger': KH, 'grani': KH}) for q in rk.ZONES[0].quests},
 "events": {**{"rk_cp%d_%s" % (n, k): KH for n in range(1, 5) for k in ("assault", "counter")}, "rk_hatis_howe": KH,
            "raumarik_icestriders": KH, "raumarik_white_wights": SC, "raumarik_frost_bears": KH}}
json.dump(d108, open(R + 'rep108_raumarik.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

d116 = {
 "zone": 116, "name": "Malmohus", "levels": [50, 60], "realm": 2,
 "factions": [
  {"key": VO, "name": "the Oath of the Volur", "short": "the Oath", "kin": kin(VO),
   "titles": ["Oath-Friend", "Oath-Sworn", "Keeper of the True Name"], "speaker": "mh_asa", "town": "Halla's camp",
   "kills": ["drakulv", "svartalf", "varg", "mara", "marodor", "crawler"],
   "quartermaster": {"name": "Oath-Quartermaster Thorgerd", "guild": "the Oath of the Volur", "model": 157, "anchor": "mh_asa",
     "offset": [4, 3], "greet": "The Oath's stores, for those who swore it. Show me your standing.",
     "stock": stock("rep116_", ["oath_friend_s_charm", "oath_sworn_ring", "nine_knot_scale_bracer", "true_name_keeper_s_torc",
                                "mantle_of_the_dragon_oath_sworn"])}}],
 "shared": [EH],
 "quartermasters": [{"faction": EH, "name": "Huscarl-Quartermaster Bersi", "guild": "King Eirik's Huscarls", "model": 213, "anchor": "mh_ketil",
                     "offset": [4, 3], "greet": "The King's stores, as far south as they go. Same stock as Mularn. Show me your standing with the Huscarls.",
                     "stock": HUS_STOCK}],
 "kill_default": VO, "event_default": VO, "quest_default": VO,
 "quests": {q['id']: owner(q, {'missionary': EH, 'svartalf_steel': EH}) for q in mh.ZONES[0].quests},
 "events": {**{"mh_cp%d_%s" % (n, k): VO for n in range(1, 5) for k in ("assault", "counter")}, "mh_wyrm_temple": VO,
            "malmohus_drakulv_rite": VO, "malmohus_drakulv_patrols": EH, "malmohus_svartalf_foisters": EH}}
json.dump(d116, open(R + 'rep116_malmohus.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
from collections import Counter
for d in (d108, d116):
    print(d['zone'], len(d['quests']), Counter(d['quests'].values()))
