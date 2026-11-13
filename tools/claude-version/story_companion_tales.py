"""Your companion's own story (owner 2026-11-11: "They would come with their own quest lines as well, telling a personal
story to them, maybe 1 every 10 levels, starting at level 15, then one at level 50"). Writes
source/server/GameServer/scripts/storyquests/quests/companion_story.json: five chapters a realm (cstory_<realm>_<level>,
levels 15, 25, 35, 45, 50), each a road to walk, a fight, and your companion's words after it. PersonalCompanions.Mind.cs
starts a chapter when you are ready (your level, out of a fight, the companion beside you); its words are filled in for
your companion: {cname}, {cclass}, {clesson} (what its class taught it), {he} / {him} / {his} (MoreWords).

Each chapter's place is a monster spawn in a zone of that level band (gameutils/data/level_bands.json), picked from the
database by how its original level ranks in the zone (the bands keep that order), so the road leads somewhere the
monsters are about the chapter's level; its boss and friends take that monster's strength (its template) at the
chapter's level, in the shape of people of the realm (models).

    python tools/claude-version/story_companion_tales.py [out.json]      (run in the game folder: reads the database)
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "runtime/data/opendaoc.sqlite3.db"
INDEX = ROOT / "new-client/godot/content/zones/zones_index.json"
BANDS = ROOT / "source/server/GameServer/gameutils/data/level_bands.json"

CHAPTERS = [15, 25, 35, 45, 50]

REALMS = {
    "alb": dict(realm=1, zones={15: 8, 25: 9, 35: 6, 45: 10, 50: 4},
                mentor="Master Aldous Wren", m_he="he", m_him="him", m_his="his",
                group="the Grey Hand", relic="the Seal of Wren", traitor="Garrick Vane", t_he="he",
                bosses=["Grey Hand Cutthroat-Chief", "Sister Morwen of the Grey Hand", "Gaoler Brannoc",
                        "Garrick Vane", "the Grey Master"],
                swear="Light above", models=(9, 38), female=[1], minion="Grey Hand cutthroat"),
    "mid": dict(realm=2, zones={15: 103, 25: 105, 35: 106, 45: 108, 50: 116},
                mentor="Sigrid Hammerhand", m_he="she", m_him="her", m_his="her",
                group="the Unsworn", relic="the oath-ring of Hammerhand", traitor="Hrafn Oathless", t_he="he",
                bosses=["Unsworn Raid-Leader", "Ulfa the Unsworn", "Jailer Skeggi",
                        "Hrafn Oathless", "the Unsworn King"],
                swear="By Odin's eye", models=(213, 168), female=[1], minion="Unsworn raider"),
    "hib": dict(realm=3, zones={15: 206, 25: 203, 35: 204, 45: 216, 50: 208},
                mentor="Aodhan of the Grey Branch", m_he="he", m_him="him", m_his="his",
                group="the Hollow Court", relic="the Silver Branch", traitor="Niamh Brightspear", t_he="she",
                bosses=["Hollow Court Reaver", "the Hollow Knight", "Warden Dubh",
                        "Niamh Brightspear", "the Hollow Queen"],
                swear="Lugh's light", models=(337, 365), female=[3, 4], minion="Hollow Court sidhe"),
}


def chapter_texts(r, i, zone_name, final_zone):
    m, mh, mhim, mhis = r["mentor"], r["m_he"], r["m_him"], r["m_his"]
    Mh = mh.capitalize()
    g, relic, tr = r["group"], r["relic"], r["traitor"]
    G = g[0].upper() + g[1:]
    if i == 0:
        return dict(
            title="Letters from Home",
            offer=f"{{name}}, wait - a moment. A courier found me with this: a letter from {m}, the {{cclass}} who taught me "
                  f"{{clesson}}. It's strange. {Mh} says {mh} found something in {zone_name}, and that if I don't hear from "
                  f"{mhim} by the new moon I should come looking. That was a month ago. I know we've our own road... "
                  f"but will you come with me?",
            reach_goal=f"Find {m}'s camp in {zone_name}",
            reach_text=f"{m}'s camp has been torn apart: the tent slashed, the fire kicked out, and a grey handprint "
                       f"daubed on a stone." if r["realm"] == 1 else
                       f"{m}'s camp has been torn apart: the tent slashed, the fire kicked out, a broken shield left "
                       f"in the ashes." if r["realm"] == 2 else
                       f"{m}'s camp has been torn apart: the shelter pulled down, the fire scattered, and a ring of "
                       f"dead white flowers around it.",
            announce=f"They come out of hiding as if they had been waiting. 'More of the old one's friends? Good. Fewer "
                     f"to hunt later.'",
            done=f"Among the leader's things: {m}'s journal, half its pages torn out.",
            say=f"This is {m}'s journal. {Mh} would never leave it behind - not willingly. There's a name in here, "
                f"'{g}', and a meeting place. {{name}}, I have to know what happened to {mhim}. Will you see this "
                f"through with me? [I will]")
    if i == 1:
        return dict(
            title=G,
            offer=f"I've read the journal every night. The last whole page says {g} meet in {zone_name}, and that they "
                  f"want {relic} - whatever that is. {m} went to see for {mhim}self. Let's go and see for ourselves.",
            reach_goal=f"Find where {g} meet in {zone_name}",
            reach_text="Ashes of a meeting fire, and the marks of a great many boots. Not long gone.",
            announce=f"A voice from the shadows: 'The student comes looking for the master. How sweet. How foolish.'",
            done=f"The lieutenant's orders name a prison, and a prisoner: {m}.",
            say=f"{m}'s alive! A prisoner - but alive. {{name}}, I could kiss you. Don't worry, I won't. We go after "
                f"{mhim}, yes? [Onward]")
    if i == 2:
        return dict(
            title="The Empty Cage",
            offer=f"The orders said {m} is held in {zone_name}. I've barely slept since. Please - let's go now.",
            reach_goal=f"Find the prison of {g} in {zone_name}",
            reach_text=f"An empty cage. Scratched into its bars, in {m}'s hand: 'Not the relic. Me. They want what I know.'",
            announce="The jailer rattles a ring of keys. 'Come for the old one? You're a week late. But you'll do instead.'",
            done=f"The jailer's ledger says {m} was moved a week ago, further into the wild - and names who sold "
                 f"{mhim} out: {tr}.",
            say=f"Moved. Again. And {tr}... {m}'s own student, before me. I'm sorry, {{name}} - I'm angry, and none of "
                f"it's at you. Thank you for staying. [Always]")
    if i == 3:
        return dict(
            title="Old Debts",
            offer=f"I know where {tr} is now: {zone_name}. {m} trusted {tr} like a son, like a daughter. I want to "
                  f"look {tr} in the eye. Come with me?",
            reach_goal=f"Find {tr} in {zone_name}",
            reach_text=f"{tr} is waiting for you, as if they knew you would come.",
            announce=f"{tr} draws, unhurried. 'The master always did like you better. Let's see why.'",
            done=f"{tr} falls to one knee. 'The master is in {final_zone}, with the one who leads {g}. Go, then. You "
                 f"were always the better student.'",
            say=f"I thought beating {tr} would feel like something. It just feels tired. One more road, {{name}}. The "
                f"last one. [Let's end it]")
    return dict(
        title="The Last Lesson",
        offer=f"This is it. {m} is in {zone_name}, with the one who leads {g}. Whatever happens there... I'm glad it's "
              f"you beside me, {{name}}.",
        reach_goal=f"Find {m} in {zone_name}",
        reach_text=f"{m} is there - chained, grey-faced, alive. And between you and {mhim}: the one who leads {g}.",
        announce=f"'{relic.capitalize()} was never the prize. Your master's mind was. And now yours.'",
        done=f"The leader of {g} falls, and the chains fall with them. {m} stands, slowly, and looks at {{cname}} for "
             f"a long time.",
        say=f"{m} says I've nothing left to learn from {mhim}. That the rest I learned from you. I don't know about "
            f"that. But I know I'm not going anywhere, {{name}}. Not without you. [Nor I without you]")


def zone_box(index, zone):
    z = index[str(zone)]
    return z["region"], z["x"] * 8192, z["y"] * 8192, (z["x"] + z["w"]) * 8192, (z["y"] + z["h"]) * 8192, z["name"]


def lowest(level_text):
    try:
        return int(str(level_text).split("-")[0].split(";")[0])
    except ValueError:
        return 0


def pick_spot(con, index, bands, zone, level):
    region, x0, y0, x1, y1, zname = zone_box(index, zone)
    band = bands["zones"][str(zone)]
    f = 0.0 if band["max"] == band["min"] else min(1.0, max(0.0, (level - band["min"]) / (band["max"] - band["min"])))
    rows = con.execute(
        "select m.X, m.Y, m.Z, m.NPCTemplateID, m.Name, t.Level from Mob m join NpcTemplate t on t.TemplateId = m.NPCTemplateID "
        "where m.Region=? and m.X between ? and ? and m.Y between ? and ? and m.Realm=0 and m.NPCTemplateID > 0 "
        "and lower(substr(m.Name,1,1)) = substr(m.Name,1,1)", (region, x0, x1, y0, y1)).fetchall()
    rows = [r for r in rows if lowest(r[5]) > 0]
    if not rows:
        raise SystemExit(f"no monsters in zone {zone}")
    rows.sort(key=lambda r: lowest(r[5]))
    r = rows[min(len(rows) - 1, int(f * (len(rows) - 1)))]
    x, y, z, tpl, name = r[0], r[1], r[2], r[3], r[4]
    return zname, [round((x - x0) / 40.0), round((y - y0) / 40.0), round(z / 40.0, 1)], tpl, name


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "source/server/GameServer/scripts/storyquests/quests/companion_story.json")
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    bands = json.loads(BANDS.read_text(encoding="utf-8"))
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    data = dict(name="companion_story", npcs=[], quests=[])
    for key, r in REALMS.items():
        places = {lvl: pick_spot(con, index, bands, r["zones"][lvl], lvl) for lvl in CHAPTERS}
        for i, lvl in enumerate(CHAPTERS):
            zname, at, tpl, mob = places[lvl]
            zone = r["zones"][lvl]
            t = chapter_texts(r, i, zname, places[CHAPTERS[-1]][0])
            boss = r["bosses"][i]
            q = dict(
                id=f"cstory_{key}_{lvl}", title=t["title"], level=lvl, min_level=lvl, realm=r["realm"], kind="story",
                requires=f"cstory_{key}_{CHAPTERS[i - 1]}" if i else None,
                offer=t["offer"], summary=f"Your companion's own story, chapter {i + 1} of 5.",
                steps=[
                    dict(id="road", type="reach", zone=zone, at=at, radius=25, goal=t["reach_goal"], text=t["reach_text"]),
                    dict(id="fight", type="encounter", zone=zone, at=at, wake_m=30, goal="Defeat " + boss,
                         stages=[dict(id="b1", type="boss", name=boss, center=at, radius=35, time_s=900,
                                      objective="Defeat " + boss, announce=t["announce"],
                                      boss=dict(template=tpl, name=boss, level=lvl + 2, health_mult=2.2,
                                                model=r["models"][1 if i in r["female"] else 0]),
                                      success=boss + " falls.", fail="You fall back.",
                                      adds=dict(every_s=35, count=1, mobs=[dict(template=tpl, name=r["minion"], level=[lvl - 1, lvl],
                                                                                model=r["models"][0])]))],
                         text=t["done"]),
                    dict(id="words", type="companion", zone=zone, at=at, goal="Talk with your companion", say=t["say"],
                         ending="done"),
                ],
                endings={"done": dict(text="", rewards=dict(xp_pct=50, copper_per_level=60, marks=10))},
            )
            if not q["requires"]:
                del q["requires"]
            data["quests"].append(q)
            print(f"{q['id']}: {zname} {at} boss '{boss}' as a {mob} ({tpl})")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(out)


if __name__ == "__main__":
    main()
