"""Malmohus's dynamic events (claude 2026-11-25, "Midgard - the plan", round 4): the three old chains kept, and the Dragon-Oath:
the four posts' assaults and counters and the raid at the Wyrm-Temple (the Drakulv Hierophant: MidgardRaids.cs), armed by
AlbionCampaign.cs (MidgardCampaigns.Wyrm); won, Gjalpinulva's lair is open. Writes the zone's events file."""
import json, sys
from evcommon import mkP, R, mob, random_chain
from evcamp import giver, assault, cull, wards, hold, boss_stage, counter, around
Z = 116
P = mkP(Z)
SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding='utf-8'))
d['lore'] = ("Malmohus: the dragon's country. Gjalpinulva sleeps in her lair in the south-west, and her drakulv - with the svartalf they "
             "bought with her scale - hold every road to the Wyrm-Temple, where the Hierophant keeps the rite and waits for the other half "
             "of her true name. The volur and the King's huscarls have sworn the Dragon-Oath to take the south back before he finds it.")
LOOK = {"template": 60157473, "model": 160, "equipment": "SvasudGuard", "guild": "the Oath of the Volur"}
SEER = {"template": 60157473, "model": 168, "guild": "the Oath of the Volur"}
MISS = mob(60160115, "drakulv missionary", (50, 52), guild="Gjalpinulva's Drakulv")
PATROL = mob(60164855, "patrolling drakulv", (50, 52), guild="Gjalpinulva's Drakulv")
ARM = mob(60160110, "drakulv armguard", (51, 53), guild="Gjalpinulva's Drakulv")
AXE = mob(60160112, "drakulv axehand", (52, 54), guild="Gjalpinulva's Drakulv")
SAC = mob(60160117, "drakulv sacrificer", (52, 54), guild="Gjalpinulva's Drakulv")
ATT = mob(60160111, "drakulv attendant", (53, 55), guild="the Hierophant's Disciples")
PROT = mob(60160116, "drakulv protector", (54, 56), guild="Gjalpinulva's Drakulv")
EXEC = mob(60160116, "drakulv executioner", (55, 57), guild="Gjalpinulva's Drakulv")
FOIST = mob(55004, "svartalf foister", (51, 53), guild="the Scale-Traders")
INFIL = mob(55003, "svartalf infiltrator", (50, 52), guild="the Scale-Traders")
BLOOD = mob(55002, "svartalf bloodbinder", (53, 55), guild="the Scale-Traders")
VARG = mob(60165644, "scaled varg snarler", (52, 54), guild="the drakulv's hounds")

CP = {1: P(600, 300), 2: P(1350, 500), 3: P(750, 850), 4: P(700, 1200)}
SEAT = P(900, 1380)
LV = {1: [50, 53], 2: [51, 54], 3: [52, 55], 4: [53, 56]}
HUSC = [dict(LOOK, name="oath-sworn huscarl", level=53, count=3)]
PREFIX = "mh_cp"
d['chains'].append(assault(PREFIX, 1, "The Dragon-Oath on the Missionary Road", LV[1], 6,
    "The Oath-Captain is forming the Dragon-Oath up for the Missionary Road.",
    giver(LOOK, "Oath-Captain Halla", 55, P(860, 420),
          "The Missionary Road, west of here. Every missionary that ever walked into Midgard came down it, and they keep a post on it still. Six at least, and say [forward].",
          "forward", "Up the road! Break their post - then their sacrificer!", "The Oath holds the Missionary Road - and the next thirty minutes are ours.",
          "Back to the camp! We'll go again."), HUSC, [
    cull("Break the Missionary Road", "Break the drakulv post on the Missionary Road",
         "The Dragon-Oath is on the Missionary Road! Break the post!", CP[1], [MISS, PATROL, SAC], 24, "s2"),
    boss_stage("s2", "Arch-Missionary Thrand", "Arch-Missionary Thrand, who sent the first preachers north: 'I converted half of Svealand. I'll pray for you too.'",
               CP[1], {"template": 60160115, "name": "Arch-Missionary Thrand", "level": 55, "size": 62, "health_mult": 4, "guild": "of Gjalpinulva's Missionaries"},
               [MISS, PATROL], "Thrand falls in his own road. The north road is the Oath's.")], bot_min=48))
d['chains'].append(assault(PREFIX, 2, "The Dragon-Oath at the Svartalf Foist", LV[2], 6,
    "Huscarl Svein is forming the Dragon-Oath up for the Svartalf Foist.",
    giver(LOOK, "Huscarl Svein", 55, P(1180, 520),
          "The Svartalf Foist. The svartalf who sold themselves for her scale hold it, and their bloodbinders have three blood-wards round it. Six at least, and say [forward].",
          "forward", "Into the foist! Hold the three blood-wards, then find their binder!", "The Oath holds the Svartalf Foist.",
          "Back out! We'll go again."), HUSC, [
    cull("Break the Foist", "Break the svartalf in the Foist",
         "The Dragon-Oath is in the Svartalf Foist! Break them!", CP[2], [FOIST, INFIL, BLOOD], 26, "s2"),
    wards("s2", "The Blood-Wards", "Hold the three blood-wards at once while the volur break them",
          "Three blood-wards hold the foist for the dragon - stand at all three at once while the volur break them!",
          CP[2], [P(1320, 470), P(1380, 480), P(1350, 540)], ["the north ward", "the east ward", "the south ward"], [FOIST, BLOOD], "s3",
          "banner of the Oath"),
    boss_stage("s3", "Bloodbinder Rana", "Bloodbinder Rana, her arms scarred with dragon-runes: 'The Mother paid us in scale. What did your king ever pay?'",
               CP[2], {"template": 55002, "name": "Bloodbinder Rana", "level": 55, "size": 60, "health_mult": 4.5, "guild": "of the Scale-Traders"},
               [FOIST, BLOOD], "Rana falls, and the foist's wards go dark.")], bot_min=48))
d['chains'].append(assault(PREFIX, 3, "The Dragon-Oath on the Armguard Lines", LV[3], 6,
    "Shield-Maiden Hild is forming the Dragon-Oath up for the Armguard Lines.",
    giver(LOOK, "Shield-Maiden Hild", 56, P(900, 700),
          "The Armguard Lines. The drakulv dig in across the middle of Malmohus, and we take them and we hold them - the volur's banner goes up, and they'll come for it. Six at least, and say [forward].",
          "forward", "Into the lines! Break them, then hold the banner!", "The Oath holds the Armguard Lines.",
          "Fall back! We'll go again."), HUSC, [
    cull("Break the Armguard Lines", "Break the drakulv on the Armguard Lines",
         "The Dragon-Oath is on the Armguard Lines! Break them!", CP[3], [ARM, AXE, VARG], 26, "s2"),
    hold("s2", "The Volur's Banner", "Keep Volva Asa alive while the banner goes up",
         "Volva Asa is raising the volur's banner on the lines - and the drakulv are coming for it!",
         CP[3], dict(SEER, name="Volva Asa", level=54, health_mult=8, model=157), around(P, (750, 850)), [ARM, AXE, SAC], "s3",
         "\"It's up. Let the Hierophant see it from his temple.\""),
    boss_stage("s3", "Line-Jarl Steinolf", "Line-Jarl Steinolf, in drakulv scale over his old huscarl's mail: 'I swore to Eirik once. The Mother pays better.'",
               CP[3], {"template": 60160110, "name": "Line-Jarl Steinolf", "level": 56, "size": 66, "health_mult": 4.5, "guild": "Jarl of the Armguard Lines"},
               [ARM, AXE], "Steinolf falls, and the lines break.")], bot_min=48))
d['chains'].append(assault(PREFIX, 4, "The Dragon-Oath on the Temple Steps", LV[4], 8,
    "Volva Groa's own apprentice is forming the Dragon-Oath up for the Temple Steps.",
    giver(SEER, "Hallveig the Apprentice", 54, P(780, 1050),
          "The Temple Steps. The protectors and executioners - the last thing between us and the Hierophant. Eight at least, and say [forward].",
          "forward", "Up the steps! Break the rite-fires, then the warden!", "The Oath holds the Temple Steps - the Wyrm-Temple is in sight.",
          "Down the steps! We'll go again."), HUSC, [
    cull("Break the Temple Steps", "Break the drakulv on the Temple Steps",
         "The Dragon-Oath is on the Temple Steps! Break them!", CP[4], [PROT, EXEC, ATT], 28, "s2"),
    wards("s2", "The Rite-Fires", "Stand at the three rite-fires at once while the volur put them out",
          "Three rite-fires keep the dragon's sleep light - stand at all three at once and the volur will put them out!",
          CP[4], [P(670, 1170), P(730, 1180), P(700, 1240)], ["the scale fire", "the blood fire", "the name fire"], [PROT, ATT], "s3",
          "banner of the Oath"),
    boss_stage("s3", "Executioner Bjornvarg", "Executioner Bjornvarg, axe in both hands, the dragon's eye branded on his chest: 'The Hierophant says your names are already in the rite.'",
               CP[4], {"template": 60160116, "name": "Executioner Bjornvarg", "level": 57, "size": 70, "health_mult": 5, "guild": "Executioner of the Temple"},
               [PROT, EXEC], "Bjornvarg falls on the steps. Above: the Wyrm-Temple, and the smoke of the rite.")], bot_min=48))

KN = dict(LOOK, name="Oath-Captain of the Volur", level=55)
d['chains'].append(counter(PREFIX, 1, "the Missionary Road", "the drakulv", LV[1], CP[1], KN, around(P, (600, 300)), [MISS, PATROL, SAC], bot_min=48, title="The Drakulv Strike Back at the Missionary Road"))
d['chains'].append(counter(PREFIX, 2, "the Svartalf Foist", "the drakulv", LV[2], CP[2], KN, around(P, (1350, 500)), [FOIST, INFIL, BLOOD], bot_min=48, title="The Drakulv Strike Back at the Svartalf Foist"))
d['chains'].append(counter(PREFIX, 3, "the Armguard Lines", "the drakulv", LV[3], CP[3], KN, around(P, (750, 850)), [ARM, AXE, VARG], bot_min=48, title="The Drakulv Strike Back at the Armguard Lines"))
d['chains'].append(counter(PREFIX, 4, "the Temple Steps", "the drakulv", LV[4], CP[4], KN, around(P, (700, 1200)), [PROT, EXEC, ATT], bot_min=48, title="The Drakulv Strike Back at the Temple Steps"))

# ---------------------------------------------------------------- the raid: the Wyrm-Temple
d['chains'].append({
    "id": "mh_wyrm_temple", "title": "The Wyrm-Temple", "levels": [55, 60], "manual": True, "bots": 16, "bot_min_level": 50,
    "min_people": 10, "hint": "Volva Groa herself is gathering the Dragon-Oath before the Wyrm-Temple.", "rest_s": 15, "start": "t1",
    "giver": giver(SEER, "Volva Groa", 60, P(820, 1300),
                   "The Wyrm-Temple. The Hierophant's in there with his half of her name - and his Wyrm-Guard, and if he speaks it, one of her eldest. Two groups at least - ten, bots and all - and healers, and curers. Then say [by the Oath].",
                   "by the Oath", "By the Oath! Healers to the back, curers by them - and whatever climbs out of that pit, hold!",
                   "The rite is broken. Her name is safe.", "Back! Back down the steps! We'll come again.", hp=8, size=50) | {"model": 157},
    "guards": [dict(LOOK, name="oath-sworn huscarl", level=55, count=4), dict(SEER, name="volva of the Oath", level=53, count=2)],
    "stages": [
        {"id": "t1", "type": "boss", "name": "the Drakulv Hierophant", "objective": "Defeat the Drakulv Hierophant",
         "announce": "The Hierophant rises from the altar, in robes of red scale, the dragon's eye burning on his brow: 'Groa. You brought me the rest of her name. How kind.'",
         "center": SEAT, "radius": 90, "time_s": 2700,
         "boss": {"template": 60160117, "name": "the Drakulv Hierophant", "level": 60, "size": 75, "health_mult": 20, "guild": "High Priest of Gjalpinulva"},
         "adds": {"every_s": 55, "count": 3, "mobs": [PROT, ATT, AXE]},
         "success": "The Hierophant falls across his altar, and the half-name dies on his lips. The rite-smoke thins over Malmohus - and in her lair to the south-west, Gjalpinulva stirs.",
         "fail": "The Hierophant drives the Dragon-Oath from his temple.", "on_success": "end", "on_fail": "end",
         "reward": {"xp_pct": 60, "copper_per_level": 650, "tokens": 60,
                    "items": [{"id": "mh116_hierophant_s_eye_crown", "gold_chance": 60, "silver_chance": 25},
                              {"id": "mh116_wyrm_guard_s_scale", "gold_chance": 60, "silver_chance": 25},
                              {"id": "mh116_brood_elder_s_tooth", "gold_chance": 60, "silver_chance": 25}]}}]})
json.dump(d, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d['chains']), 'chains')
