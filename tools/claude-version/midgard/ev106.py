"""Skona Ravine's dynamic events (claude 2026-11-25, "Midgard - the plan", round 3): the three old chains kept, one new - the Red
Moon (at night the werewolves come howling to the Seithkona Circle to stop the seers reading the moon's road; a moon-caller leads
them: the west thread) - and the zone's set-piece, Ulfhamr: a siege (ZoneSiege) for the Wolfsbane Rangers, fed by the zone's
events and quests; taken, the Rangers keep a camp in the hold until the Moon-Mother leads the packs back for it.
Writes the zone's events file.   python ev106.py <in zone106 json> <out json>"""
import json, sys
from evcommon import mkP, R, mob, path, random_chain, occupy
Z = 106
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Skona Ravine: the Stor Gothi's camp and the Seithkona Circle on the edges of a deep, wooded ravine. In its middle "
             "stands Ulfhamr, the werewolf hold, where the wolfaur headsmen and the warders gather Fenrir's kin for Hati's host in "
             "Raumarik. The seithkona read the moon's road, and the moon is afraid. From the south the first silverscale drakes creep "
             "up out of Malmohus.")
GUARD = mob(60167861, "werewolf guard", (31, 33), guild="Fenrir's Kin")
WARD = mob(60167872, "werewolf warder", (32, 34), guild="Fenrir's Kin")
HEAD = mob(60168002, "wolfaur headsman", (33, 35), guild="Fenrir's Kin")
SKULK = mob(60167871, "werewolf skulker", (30, 32), guild="Fenrir's Kin")
RANGER = {"template": 60157473, "model": 213, "guild": "the Wolfsbane Rangers"}
SEER = {"template": 60157473, "model": 168, "guild": "the Seithkona Circle"}

# ------------------------------------------------------------------ the Red Moon
CIRCLE = P(1350, 280)
d['chains'].append(random_chain('sk_red_moon', 'The Red Moon', [31, 35],
    "The moon rises red over the ravine, and the howling comes closer to the Seithkona Circle...", 'r1', [
    {"id": "r1", "type": "defend", "name": "The Moon-Reading", "objective": "Keep Seithkona Rannveig alive while she reads the moon",
     "announce": "A red moon over Skona, and the werewolves are coming for the Seithkona Circle to stop the seers reading the moon's road! Seithkona Rannveig won't leave the stone - keep her alive!",
     "center": CIRCLE, "radius": 70, "duration_s": 200, "protect": dict(SEER, name="Seithkona Rannveig", level=33, pos=CIRCLE, health_mult=8),
     "waves": {"every_s": 24, "count": 3, "from": [P(1290, 330), P(1410, 340), P(1300, 220)], "mobs": [SKULK, GUARD, WARD]},
     "thanks": "\"The moon's road runs north-west, to the ice. Hati's waiting there. Tell Jodur.\"",
     "success": "The packs fall back - and a werewolf in a cloak of moon-pale fur walks out of the trees, howling at the red moon.",
     "fail": "Rannveig falls at the stone, and the moon goes dark.", "on_success": "r2", "on_fail": "end", "reward": R(14, 160, 12)},
    {"id": "r2", "type": "boss", "name": "the Moon-Caller", "objective": "Defeat the Moon-Caller",
     "announce": "The Moon-Caller, a werewolf priest with the moon's phases cut into his hide: 'Hati hunts. The moon runs. Your seers will not warn her.'",
     "center": CIRCLE, "radius": 80, "time_s": 1200,
     "boss": {"template": 60167872, "name": "the Moon-Caller", "level": 36, "size": 70, "pos": CIRCLE, "health_mult": 3, "guild": "of Fenrir's Kin"},
     "adds": {"every_s": 40, "count": 2, "mobs": [SKULK]},
     "success": "The Moon-Caller falls among the stones, and the moon goes white.", "fail": "The Moon-Caller drives you from the circle.",
     "on_success": "end", "on_fail": "end", "reward": R(28, 260, 20, ["nu106_moon_caller_s_hide"], 35)},
    ], time="night"))

# ------------------------------------------------------------------ the set-piece: Ulfhamr
HOLD, YARD = P(920, 720), P(860, 800)
STAGING = P(720, 560)
d['chains'].append({
    "id": "sk_ulfhamr_assault", "title": "Break Ulfhamr", "levels": [33, 37], "manual": True, "bots": 8, "min_people": 4,
    "bot_min_level": 25, "hint": "Ranger-Marshal Hjordis is gathering the Wolfsbane Rangers on the slope north-west of Ulfhamr.", "rest_s": 15, "start": "u1",
    "giver": dict(RANGER, name="Ranger-Marshal Hjordis", level=37, pos=STAGING, health_mult=3,
                  greet="The Rangers are here, and every one of them has lost someone to that hold. Four at least, bots and all - say [for the Rangers].",
                  accept="for the Rangers", reply="Wolfsbane on your blades! Clear the yard, break their moon-stones, and drag their warden out!",
                  busy="Not yet. The Rangers are still coming in from the woods. Rest, and gather.", cooldown_s=120,
                  thanks="Ulfhamr is broken! Hati's host will have to gather somewhere else.", regret="Back to the slope! We'll come again."),
    "guards": [dict(RANGER, name="Wolfsbane ranger", level=34, count=2), dict(SEER, name="seithkona of the Circle", level=34, count=2)],
    "stages": [
        {"id": "u1", "type": "cull", "name": "The Yard", "objective": "Clear the werewolves from the hold's yard",
         "announce": "Into the yard! The guards and the headsmen are coming out to meet us!", "center": YARD, "radius": 70,
         "time_s": 900, "kill": 20, "alive": 8, "mobs": [GUARD, HEAD, SKULK, WARD],
         "success": "The yard is ours. The werewolves fall back into the hold.", "fail": "The Rangers are thrown back up the slope.",
         "on_success": "u2", "on_fail": "end", "reward": R(14, 160, 12)},
        {"id": "u2", "type": "wards", "name": "The Moon-Stones", "objective": "Hold the three moon-stones at once while the seithkona break them",
         "announce": "Three moon-stones feed the hold's wards! Stand at all three at once and the seithkona will break them!",
         "center": HOLD, "radius": 80, "wards": [P(890, 690), P(950, 700), P(920, 760)],
         "ward_names": ["the north stone", "the east stone", "the south stone"], "ward_radius": 20, "hold_s": 30, "time_s": 900,
         "alive": 2, "mobs": [WARD, GUARD], "reinforce_s": 40, "flag": 466, "flag_name": "banner of the Rangers",
         "success": "The moon-stones crack - and out of the hold comes its warden, howling.", "fail": "The stones hold. The Rangers fall back.",
         "on_success": "u3", "on_fail": "end", "reward": R(14, 160, 12)},
        {"id": "u3", "type": "boss", "name": "Hold-Jarl Ulfgrim", "objective": "Defeat Hold-Jarl Ulfgrim",
         "announce": "Hold-Jarl Ulfgrim, a werewolf in a jarl's mail with a wolf-skull helm: 'When the moon runs red we go north to Hati. You'll be the meat we bring.'",
         "center": HOLD, "radius": 80, "time_s": 1200,
         "boss": {"template": 60167853, "name": "Hold-Jarl Ulfgrim", "level": 38, "size": 65, "health_mult": 2.5, "guild": "Jarl of Ulfhamr"},
         "adds": {"every_s": 35, "count": 3, "mobs": [GUARD, HEAD]},
         "success": "Ulfgrim falls on his own threshold. The Rangers' banner goes up over Ulfhamr.",
         "fail": "Ulfgrim drives the Rangers out of the yard.", "on_success": "end", "on_fail": "end",
         "reward": R(35, 300, 22, ["uf106_ulfgrim_s_skull_helm"], 35)}]})
d['chains'].append({
    "id": "sk_ulfhamr_return", "title": "The Moon-Mother", "levels": [34, 37], "manual": True, "bots": 8, "bot_min_level": 25,
    "hint": "Howling from every side of the ravine: the Moon-Mother has come for Ulfhamr.", "wake_m": 200, "auto_fail_s": 900, "start": "x1",
    "stages": [
        {"id": "x1", "type": "defend", "name": "The Hold Gate", "objective": "Keep Ranger Ketilridr alive at the hold gate",
         "announce": "Every pack in the ravine is coming for Ulfhamr! Hold the gate!",
         "center": HOLD, "radius": 70, "duration_s": 200,
         "protect": dict(RANGER, name="Ranger Ketilridr", level=35, pos=HOLD, health_mult=5, model=168),
         "waves": {"every_s": 22, "count": 4, "from": [P(980, 660), P(990, 800), P(850, 680)], "mobs": [GUARD, HEAD, SKULK, WARD]},
         "success": "The first rush breaks - and the Moon-Mother comes over the wall.", "fail": "Ranger Ketilridr falls at the gate.",
         "on_success": "x2", "on_fail": "end", "reward": R(20, 180, 14)},
        {"id": "x2", "type": "boss", "name": "the Moon-Mother", "objective": "Defeat the Moon-Mother",
         "announce": "The Moon-Mother - a she-wolf taller than the gate, her fur white as the moon she hunts: 'My cubs were promised this hold, and the north after it.'",
         "center": HOLD, "radius": 70, "time_s": 900,
         "boss": {"template": 60167849, "name": "the Moon-Mother", "level": 38, "size": 80, "health_mult": 2.5, "guild": "Mother of Fenrir's Kin"},
         "adds": {"every_s": 35, "count": 3, "mobs": [GUARD, SKULK]},
         "success": "The Moon-Mother falls. Ulfhamr holds - for now.", "fail": "The Moon-Mother takes Ulfhamr back.",
         "on_success": "end", "on_fail": "end", "reward": R(30, 260, 20, ["uf106_moon_mother_s_white_pelt"], 35)}]})

UF = "uf106_"
d['siege'] = {
    "id": "ulfhamr", "name": "Ulfhamr", "enemy": "Fenrir's Kin",
    "resolve_name": "The Rangers' resolve", "enemy_name": "The werewolves' hold", "faction": "wolfsbane_rangers",
    "feeds": {"sk_red_moon": 20, "skona_ravine_werewolf_warders": 15, "skona_ravine_wolfaur_headsmen": 15, "skona_ravine_dryad_grove": 5},
    "feed_default": 5,
    "quests": {"sk_skulkers": 5, "sk_wolverines": 5, "sk_moon_stone": 10, "sk_guards": 10, "sk_warders": 15, "sk_headsmen": 15,
               "sk_ulfhamr": 25, "moonbound": 10},
    "enemy_feeds": {"sk_red_moon": 15}, "enemy_default": 5, "war_chain": "sk_red_moon",
    "assault": "sk_ulfhamr_assault", "raids": [], "last_raid": "sk_ulfhamr_return", "hold_h": 2, "raid_gap_h": [2, 1.5, 1.5],
    "criers": ["sk_jodur", "sk_saga"], "bots_go_after_m": 30,
    "open_text": "Hear me! The Wolfsbane Rangers mean to break Ulfhamr, the werewolf hold! Ranger-Marshal Hjordis waits on the slope north-west of the hold. If no one leads within the half-hour, the Rangers go without you.",
    "taken_text": "Ulfhamr is broken! The Rangers keep the hold - go and see.",
    "repelled_text": "The Rangers have been thrown back from Ulfhamr. The werewolves grow bolder.",
    "raid_text": "Howling on every side of the ravine: the werewolves are coming back for Ulfhamr!",
    "held_text": "The werewolves are thrown back from the walls. Ulfhamr holds.",
    "fall_text": "Ulfhamr has fallen to the Moon-Mother. The werewolves have their hold again, and the Rangers must rebuild their resolve.",
    "carry_text": "Ranger-Marshal Hjordis leads you down the slope at a run.",
    "carried_cry": "The Rangers wouldn't wait any longer - they have stormed {0}!",
    "hostile_tier": "yellow", "sites": ["ulfhamr", "ulfhamr_yard"],
    "staging": STAGING, "landing": YARD, "area": [910, 740, 110],
    "camp_npcs": [
        dict(RANGER, kind="marks", name="Ranger-Quartermaster Bodvar", level=35, pos=P(900, 760),
             greet="The hold's stores, for those who broke it and those who hold it.",
             stock=[{"item": UF + "ulfhamr_breaker_s_cloak", "price": 60}, {"item": UF + "moon_stone_ring", "price": 40},
                    {"item": UF + "wolfsbane_torc", "price": 40}, {"item": UF + "hold_gate_bracer", "price": 40},
                    {"item": "tw_strong_draught_of_healing", "price": 2}, {"item": "tw_strong_draught_of_power", "price": 2}]),
        dict(SEER, kind="coin", name="Herb-Wife Gro", level=33, pos=P(940, 720),
             greet="Wolfsbane tea, and better things. The tea's for the wolves.",
             stock=[{"item": UF + "ranger_s_ale"}, {"item": UF + "wolfsbane_tonic"}, {"item": UF + "moonlit_mead"}]),
        dict(RANGER, kind="idle", name="Wolfsbane ranger", level=34, pos=P(880, 780), count=3,
             idle="We pulled the rangers' cloaks off the gate-post. We'll bury them properly."),
    ],
    "holdouts": [
        {"kind": "holdout", "name": "werewolf holdout", "template": 60167861, "level": 34, "pos": P(980, 690), "count": 3, "tier": "yellow", "respawn_s": 300}],
}
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
