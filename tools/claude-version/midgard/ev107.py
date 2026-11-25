"""Vanern Swamp's dynamic events (claude 2026-11-25, "Midgard - the plan", round 3): the three old chains kept, one new - the Ice
Road (the jotun outcasts haul Raumarik's ice south behind a frost-herald: the west thread) - and the zone's set-piece, Hrafnsholm:
a fort to retake (ZoneSiege) for the Wardens of Vanern, fed by the zone's events and quests; held, the Wardens keep a camp in the
hold until the hagbui unchain their jotun and send him to take it back.
Writes the zone's events file.   python ev107.py <in zone107 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, random_chain, occupy
Z = 107
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Vanern Swamp: a deadly marsh with the Wardens' camp in the south-east. As the long winter comes, the hagbui - the "
             "barrow-dead of Vanern's old thanes - have risen and taken Hrafnsholm, the Wardens' watch-hold on the north-west ridge, and "
             "chained a jotun in its yard to work their cold forge. The jotun outcasts of the north haul Raumarik's ice south, waiting "
             "for Hati and the winter.")
BERS = mob(60161914, "hagbui berserker", (41, 43), guild="the Hagbui")
GUARD = mob(60161916, "hagbui guard", (40, 42), guild="the Hagbui")
RUNE = mob(60161917, "hagbui runemaster", (42, 44), guild="the Hagbui")
THANE = mob(60161921, "hagbui thane", (43, 45), guild="the Hagbui")
SPIRIT = mob(60161919, "hagbui spiritmaster", (41, 43), guild="the Hagbui")
OUTC = mob(60162686, "jotun outcast", (43, 45), guild="of the ice road")
ORM = mob(60163137, "large enslaved orm runner", (41, 43), guild="hauling for the jotun")
WARDEN = {"template": 60157473, "model": 160, "equipment": "SvasudGuard", "guild": "the Wardens of Vanern"}
SEER = {"template": 60157473, "model": 168, "guild": "the Wardens of Vanern"}

# ------------------------------------------------------------------ the Ice Road
ROAD = P(700, 220)
d['chains'].append(random_chain('vn_ice_road', 'The Ice Road', [41, 45],
    "Frost on the bog in summer, and the crack of jotun whips in the north...", 'i1', [
    {"id": "i1", "type": "cull", "name": "The Ice-Haulers", "objective": "Break the jotun outcasts hauling ice down the north road",
     "announce": "The jotun outcasts are hauling Raumarik's ice south across Vanern! Break the haulers before the road reaches Hrafnsholm!",
     "center": ROAD, "radius": 90, "time_s": 900, "kill": 12, "alive": 6, "mobs": [ORM, ORM, OUTC],
     "success": "The haulers break - and the one driving them comes down the road, frost smoking off him.",
     "fail": "The ice reaches the hagbui's ridge.", "on_success": "i2", "on_fail": "end", "reward": R(14, 180, 12)},
    {"id": "i2", "type": "boss", "name": "Frost-Herald Hrimgrim", "objective": "Defeat Frost-Herald Hrimgrim",
     "announce": "Frost-Herald Hrimgrim, a jotun with icicles for a beard and a horn of ice: 'When Hati catches the moon, we walk south on this road. Stand in it, little men.'",
     "center": ROAD, "radius": 90, "time_s": 1200,
     "path": [P(700, 220), P(560, 160), P(620, 300), P(760, 280), P(700, 220)],
     "boss": {"template": 60162687, "name": "Frost-Herald Hrimgrim", "level": 46, "size": 70, "pos": ROAD, "health_mult": 3.5, "guild": "Herald of the Winter"},
     "adds": {"every_s": 40, "count": 2, "mobs": [OUTC]},
     "success": "Hrimgrim falls, and his horn shatters. The ice on the road begins, at last, to melt.",
     "fail": "Hrimgrim blows his horn, and the ice road runs on toward Hrafnsholm.", "on_success": "end", "on_fail": "end",
     "reward": R(30, 300, 22, ["nu107_hrimgrim_s_ice_horn"], 35)},
    ]))

# ------------------------------------------------------------------ the set-piece: Hrafnsholm
HOLD, YARD = P(240, 250), P(300, 300)
STAGING = P(440, 150)
d['chains'].append({
    "id": "vn_hrafnsholm_assault", "title": "Retake Hrafnsholm", "levels": [42, 46], "manual": True, "bots": 8, "min_people": 4,
    "bot_min_level": 32, "hint": "Warden-Marshal Thorstein is gathering the Wardens of Vanern on the ridge east of Hrafnsholm.", "rest_s": 15, "start": "h1",
    "giver": dict(WARDEN, name="Warden-Marshal Thorstein", level=46, pos=STAGING, health_mult=3,
                  greet="Three hundred years the Wardens held that hold. The dead took it in a night. We take it back today. Four at least, bots and all - say [for Hrafnsholm].",
                  accept="for Hrafnsholm", reply="Rowan and iron! Clear the yard, break the rune-chains, and put their thane back in his barrow!",
                  busy="Not yet. The Wardens are still coming up through the bog. Rest, and gather.", cooldown_s=120,
                  thanks="Hrafnsholm is the Wardens' again!", regret="Back to the ridge! We'll come again."),
    "guards": [dict(WARDEN, name="Warden of Vanern", level=43, count=2), dict(SEER, name="rune-woman of Vanern", level=43, count=2)],
    "stages": [
        {"id": "h1", "type": "cull", "name": "The Yard", "objective": "Clear the hagbui from the yard",
         "announce": "Into the yard! The dead are coming out to meet us!", "center": YARD, "radius": 70,
         "time_s": 900, "kill": 20, "alive": 8, "mobs": [BERS, GUARD, SPIRIT, BERS],
         "success": "The yard is ours. The hagbui fall back to the hall.", "fail": "The Wardens are thrown back to the ridge.",
         "on_success": "h2", "on_fail": "end", "reward": R(14, 200, 12)},
        {"id": "h2", "type": "wards", "name": "The Rune-Chains", "objective": "Hold the three rune-posts at once while the rune-women break the jotun's chains",
         "announce": "The chained jotun is bound by three rune-posts! Stand at all three at once and the rune-women will break the chains - or the dead will turn him on us!",
         "center": HOLD, "radius": 80, "wards": [P(210, 220), P(270, 230), P(240, 290)],
         "ward_names": ["the north post", "the east post", "the south post"], "ward_radius": 20, "hold_s": 30, "time_s": 900,
         "alive": 2, "mobs": [RUNE, GUARD], "reinforce_s": 40, "flag": 466, "flag_name": "raven banner of the Wardens",
         "success": "The chains fall, and the jotun walks off into the swamp without a word - and out of the hall comes the thane who chained him.", "fail": "The rune-posts hold. The Wardens fall back.",
         "on_success": "h3", "on_fail": "end", "reward": R(14, 200, 12)},
        {"id": "h3", "type": "boss", "name": "Barrow-Jarl Hrafnkel", "objective": "Defeat Barrow-Jarl Hrafnkel",
         "announce": "Barrow-Jarl Hrafnkel, dead three hundred years, frost in his beard and his barrow-gold on his arms: 'I held this hold before your grandfathers' grandfathers. I hold it for the winter now.'",
         "center": HOLD, "radius": 80, "time_s": 1200,
         "boss": {"template": 60161921, "name": "Barrow-Jarl Hrafnkel", "level": 47, "size": 65, "health_mult": 2.5, "guild": "Jarl of the Hagbui"},
         "adds": {"every_s": 35, "count": 3, "mobs": [BERS, THANE]},
         "success": "Hrafnkel falls on his own hearth and is dust. The Wardens' raven goes up over Hrafnsholm, the right way up.",
         "fail": "Hrafnkel drives the Wardens out of the yard.", "on_success": "end", "on_fail": "end",
         "reward": R(35, 340, 24, ["uf107_hrafnkel_s_barrow_gold"], 35)}]})
d['chains'].append({
    "id": "vn_hrafnsholm_return", "title": "The Unchained", "levels": [43, 46], "manual": True, "bots": 8, "bot_min_level": 32,
    "hint": "The ground shakes in the west: the hagbui have chained a new jotun, and sent him for Hrafnsholm.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Hall Door", "objective": "Keep Rune-Woman Asdis alive at the hall door",
         "announce": "Every barrow in Vanern has opened, and the dead are coming for Hrafnsholm! Hold the door!",
         "center": HOLD, "radius": 70, "duration_s": 200,
         "protect": dict(SEER, name="Rune-Woman Asdis", level=44, pos=HOLD, health_mult=5),
         "waves": {"every_s": 22, "count": 4, "from": [P(180, 200), P(200, 320), P(300, 200)], "mobs": [BERS, GUARD, SPIRIT, THANE]},
         "success": "The first rush breaks - and the ground shakes. A jotun in black rune-chains walks out of the bog.", "fail": "Rune-Woman Asdis falls at the door.",
         "on_success": "x2", "on_fail": "end", "reward": R(20, 220, 16)},
        {"id": "x2", "type": "boss", "name": "Bergelmir the Chained", "objective": "Defeat Bergelmir the Chained",
         "announce": "Bergelmir the Chained - a jotun bound in the hagbui's black chains, their runes burning cold on his skin. He doesn't want to fight you. He has no choice.",
         "center": HOLD, "radius": 70, "time_s": 900,
         "boss": {"template": 60158735, "name": "Bergelmir the Chained", "level": 47, "size": 90, "health_mult": 3, "guild": "Slave of the Hagbui"},
         "adds": {"every_s": 35, "count": 3, "mobs": [RUNE, BERS]},
         "success": "Bergelmir falls, and his chains break with him. 'Thank you,' he says. Hrafnsholm holds - for now.", "fail": "Bergelmir breaks the hall door, and the dead pour in.",
         "on_success": "end", "on_fail": "end", "reward": R(30, 300, 22, ["uf107_bergelmir_s_broken_chain"], 35)}]})

UF = "uf107_"
d['siege'] = {
    "id": "hrafnsholm", "name": "Hrafnsholm", "enemy": "the Hagbui",
    "resolve_name": "The Wardens' resolve", "enemy_name": "The hagbui's hold", "faction": "vanern_wardens",
    "feeds": {"vn_ice_road": 15, "vanern_swamp_hagbui_barrow": 20, "vanern_swamp_clay_jotun": 5, "vanern_swamp_black_orms": 5},
    "feed_default": 5,
    "quests": {"vn_berserkers": 10, "vn_spiritmasters": 15, "vn_runemasters": 15, "vn_hrafnsholm": 25, "vn_crippled": 10,
               "vn_outcasts": 10, "barrow_brother": 10},
    "enemy_feeds": {"vn_ice_road": 15}, "enemy_default": 5, "war_chain": "vn_ice_road",
    "assault": "vn_hrafnsholm_assault", "raids": [], "last_raid": "vn_hrafnsholm_return", "hold_h": 2, "raid_gap_h": [2, 1.5, 1.5],
    "criers": ["vn_steinunn", "vn_gisli"], "bots_go_after_m": 30,
    "open_text": "Hear me! The Wardens of Vanern mean to take back Hrafnsholm from the hagbui! Warden-Marshal Thorstein waits on the ridge east of the hold. If no one leads within the half-hour, the Wardens go without you.",
    "taken_text": "Hrafnsholm is the Wardens' again! The jotun is free, and the Wardens keep the hold - go and see.",
    "repelled_text": "The Wardens have been thrown back from Hrafnsholm. The dead grow bolder.",
    "raid_text": "The ground shakes in the west: the hagbui are coming back for Hrafnsholm!",
    "held_text": "The dead are thrown back from the walls. Hrafnsholm holds.",
    "fall_text": "Hrafnsholm has fallen to the hagbui and their chained jotun. The dead hold it again, and the Wardens must rebuild their resolve.",
    "carry_text": "Warden-Marshal Thorstein leads you down off the ridge at a run.",
    "carried_cry": "The Wardens wouldn't wait any longer - they have stormed {0}!",
    "hostile_tier": "yellow", "sites": ["hrafnsholm", "hrafnsholm_yard"],
    "staging": STAGING, "landing": YARD, "area": [260, 270, 110],
    "camp_npcs": [
        dict(WARDEN, kind="marks", name="Warden-Quartermaster Kolfinna", level=44, pos=P(280, 290), model=168, equipment=None,
             greet="The hold's stores, for those who took it back and those who keep it.",
             stock=[{"item": UF + "hrafnsholm_raven_cloak", "price": 60}, {"item": UF + "rune_chain_ring", "price": 40},
                    {"item": UF + "watch_hold_torc", "price": 40}, {"item": UF + "barrow_breaker_bracer", "price": 40},
                    {"item": "tw_strong_draught_of_healing", "price": 2}, {"item": "tw_strong_draught_of_power", "price": 2}]),
        dict(SEER, kind="coin", name="Bog-Brewer Hallveig", level=42, pos=P(230, 280), model=157,
             greet="Bog-ale and rowan-water. The rowan's for the dead.",
             stock=[{"item": UF + "bog_ale"}, {"item": UF + "rowan_water"}, {"item": UF + "warden_s_mead"}]),
        dict(WARDEN, kind="idle", name="Warden of Vanern", level=43, pos=P(270, 240), count=3,
             idle="We turned the banner the right way up. Three hundred years. It still fits the pole."),
    ],
    "holdouts": [
        {"kind": "holdout", "name": "hagbui holdout", "template": 60161914, "level": 43, "pos": P(180, 320), "count": 3, "tier": "yellow", "respawn_s": 300}],
}
for n in d['siege']['camp_npcs']:
    if n.get('equipment') is None:
        n.pop('equipment', None)
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
