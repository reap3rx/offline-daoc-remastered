"""The companion quest (owner 2026-11-11: at level 7 "a quest ... directs you to an NPC in the starting town (Cotswold,
Mularn, Mag Mell). Through dialog choices you pick its sex, class and race. Only valid race/class combos are offered,
and you can always go back."). Writes source/server/GameServer/scripts/storyquests/quests/companion.json: one quest a
realm, all choice steps - sex, then class, then the class's races - with [back] on each. PersonalCompanions.cs reads the
answers (StoryQuestManager.ChoiceMade) and makes the companion when it ends (Finished).

    python tools/claude-version/story_companion.py [out.json]
"""
import json
import sys

# (class, its races) - AutonomousBotIdentityGenerator.Choices, in the order the recruiter groups them
REALMS = {
    "alb": dict(
        realm=1, zone=0, town="Cotswold Village",
        npc=dict(id="companion_rowena", name="Rowena Ashby", model=38, guild="Adventurers' Guild", pos=[294, 712, 57.0]),
        hello="There you are, {name}. Word gets around - you've been making a name for yourself, and nobody should walk "
              "the long road alone. I keep a list of good people looking for someone worth following.",
        idle="Every road in Albion is easier with a friend on it.",
        groups=[
            ("Steel and shield", [("Armsman", "Heavy armour and a long polearm - they'll hold any line you draw.", "Avalonian Briton Highlander Inconnu Saracen"),
                                  ("Paladin", "A knight of the Church: sword, chant and an oath that doesn't bend.", "Avalonian Briton Highlander Saracen"),
                                  ("Mercenary", "Two blades and no patience for standing still.", "Avalonian Briton Highlander Inconnu Saracen"),
                                  ("Reaver", "A flail and a darker kind of devotion. Unsettling. Effective.", "Briton Inconnu Saracen")]),
            ("Faith and healing", [("Cleric", "Prayer that closes wounds - and calls back the dead.", "Avalonian Briton Highlander"),
                                   ("Friar", "A quarterstaff, a healing hand and a laugh for every road.", "Briton")]),
            ("The arcane", [("Wizard", "Fire and ice from a safe distance. Mostly safe.", "Avalonian Briton"),
                            ("Theurgist", "Summons the very air, earth and ice to fight for you.", "Avalonian Briton"),
                            ("Sorcerer", "Mind and body bent to their will - and a pet to boot.", "Avalonian Briton Inconnu Saracen"),
                            ("Cabalist", "Builds a servant of clay or stone and sends it ahead.", "Avalonian Briton Inconnu Saracen"),
                            ("Necromancer", "Fights through a shade from beyond. Don't stare at it.", "Briton Inconnu Saracen")]),
            ("Road and shadow", [("Scout", "A longbow, sharp eyes and a shield for when the arrows run out.", "Briton Highlander Inconnu Saracen"),
                                 ("Infiltrator", "You won't see them. Neither will the enemy - until too late.", "Briton Inconnu Saracen"),
                                 ("Minstrel", "Songs to speed your feet and lull your foes to sleep.", "Briton Highlander Saracen")]),
        ]),
    "mid": dict(
        realm=2, zone=100, town="Mularn",
        npc=dict(id="companion_ketil", name="Ketil Ravnsson", model=213, guild="Shield-Hall of Mularn", pos=[1258, 1362, 119.4]),
        hello="Ah - {name}. The skalds are already muttering your name, did you know? A name like that needs a shield-mate. "
              "I know good folk who'd follow you into the cold, if you'll have them.",
        idle="No one should go into the cold alone. Not in Midgard.",
        groups=[
            ("Axe and shield", [("Warrior", "Thick armour, a big shield, and no idea how to back down.", "Dwarf Kobold Norseman Troll Valkyn"),
                                ("Thane", "A hammer in one hand and Thor's thunder in the other.", "Dwarf Norseman Troll"),
                                ("Berserker", "When the rage takes them, every blow lands like a falling tree.", "Dwarf Norseman Troll Valkyn"),
                                ("Savage", "Hand-to-hand claws and a body hardened past pain.", "Dwarf Kobold Norseman Troll Valkyn"),
                                ("Skald", "Sings of the battle while fighting in it - and the songs help.", "Dwarf Kobold Norseman Troll")]),
            ("Healing and the spirits", [("Healer", "Mends the living, raises the fallen. Every war-band needs one.", "Dwarf Norseman"),
                                         ("Shaman", "Heals the body, sickens the foe - an old, earthy magic.", "Kobold Troll")]),
            ("Runes and the dead", [("Runemaster", "Carves the runes of Odin into bolts of pure force.", "Dwarf Kobold Norseman"),
                                    ("Spiritmaster", "Calls warrior spirits from Hel to fight at your side.", "Kobold Norseman"),
                                    ("Bonedancer", "Commands an army of bones. Cheerful company, considering.", "Kobold Troll Valkyn")]),
            ("Bow and shadow", [("Hunter", "A spear, a bow, and a hound that never loses the trail.", "Dwarf Kobold Norseman Valkyn"),
                                ("Shadowblade", "Two blades out of the dark. You'll only hear about it afterwards.", "Kobold Norseman Valkyn")]),
        ]),
    "hib": dict(
        realm=3, zone=200, town="Mag Mell",
        npc=dict(id="companion_caoimhe", name="Caoimhe Ni Dhuinn", model=365, guild="Fianna of Mag Mell", pos=[660, 190, 130.0]),
        hello="{name}! The birds have been singing about you, and they're rarely wrong. A path like yours shouldn't be walked "
              "alone - I know a few good souls who'd gladly walk it with you.",
        idle="The forest is kinder to two than to one. Remember that.",
        groups=[
            ("Blade and shield", [("Hero", "A shield, a spear, and a stubborn streak as old as the hills.", "Celt Firbolg Lurikeen Sylvan"),
                                  ("Blademaster", "Two blades, never still - quick as a hawk's stoop.", "Celt Elf Firbolg"),
                                  ("Champion", "A great sword and spells that sap the strength from foes.", "Celt Elf Lurikeen"),
                                  ("Valewalker", "A scythe and the forest's own magic. Strange, and strong.", "Celt Firbolg Sylvan"),
                                  ("Sluaghbinder", "Binds the restless dead of the Sluagh to their will.", "Celt Firbolg")]),
            ("Nurture and song", [("Druid", "The grove's healing - and a creature of the wild beside them.", "Celt Firbolg Sylvan"),
                                  ("Warden", "Heals, shields and fights. A friend in every way.", "Celt Firbolg Sylvan"),
                                  ("Bard", "Songs that heal, speed and calm - and a raised voice for the fallen.", "Celt Firbolg")]),
            ("Magic", [("Eldritch", "The void's cold light, thrown hard and far.", "Elf Lurikeen"),
                       ("Enchanter", "Bends light into weapons and a spirit to guard them.", "Elf Lurikeen"),
                       ("Mentalist", "Mind against mind, and gentle healing besides.", "Celt Elf Lurikeen"),
                       ("Animist", "Grows fungal servants from the earth itself. Oddly loyal things.", "Celt Firbolg Sylvan")]),
            ("Bow and shadow", [("Ranger", "A bow from the high forests - and they never miss twice.", "Celt Elf Lurikeen"),
                                ("Nightshade", "Silent, quick and gone before the body falls.", "Elf Lurikeen")]),
        ]),
}


def realm_quest(key, r):
    npc = r["npc"]
    who = npc["name"].split()[0]
    sex_q = r["hello"] + "\n\nTell me who you'd want at your shoulder. A [man] or a [woman]?"
    lines = []
    for title, classes in r["groups"]:
        lines.append(title + ": " + ", ".join(f"[{c}]" for c, _, _ in classes))
    class_q = "And their calling?\n\n" + "\n".join(lines) + "\n\nOr go [back]."

    def race_q(cls, blurb, races):
        rs = races.split()
        art = "An" if cls[0] in "AEIOU" else "A"
        return f"{art} {cls}. {blurb}\n\nAnd of what people? " + ", ".join(f"[{x}]" for x in rs) + ".\n\nOr go [back]."

    steps = [dict(id="sex", type="choice", npc=npc["id"], goal=f"Speak with {npc['name']} in {r['town']}", say=sex_q,
                  options=[dict(keyword="man", say="A man. Good.\n\n" + class_q, next="class"),
                           dict(keyword="woman", say="A woman. Good.\n\n" + class_q, next="class")]),
             dict(id="class", type="choice", npc=npc["id"], goal=f"Tell {who} your companion's calling", say=class_q,
                  options=[dict(keyword="back", say=sex_q, next="sex")] +
                          [dict(keyword=c, say=race_q(c, b, rs), next="race_" + c) for _, cl in r["groups"] for c, b, rs in cl])]
    for _, cl in r["groups"]:
        for c, b, rs in cl:
            steps.append(dict(id="race_" + c, type="choice", npc=npc["id"], goal=f"Tell {who} your companion's people", say=race_q(c, b, rs),
                              options=[dict(keyword="back", say=class_q, next="class")] +
                                      [dict(keyword=x, ending="joined") for x in rs.split()]))
    return dict(
        id="companion_" + key, title="A Friend for the Road", level=7, min_level=7, realm=r["realm"], giver=npc["id"],
        offer=f"You've the look of someone who shouldn't walk the roads alone, {{name}}. I find companions for people like "
              f"you - folk who'll stand at your shoulder for the long road. Shall I find you a [companion]?",
        accept="companion",
        summary=f"{npc['name']} of {r['town']} finds travelling companions for adventurers. {who} has someone in mind for you.",
        steps=steps,
        endings={"joined": dict(text="Then I know just the one - they've been waiting for someone like you.\n\nThere. "
                                     "Look after each other out there, {name}. And call for them whenever you need them.")},
    )


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "source/server/GameServer/scripts/storyquests/quests/companion.json"
    data = dict(name="companion", npcs=[], quests=[])
    for key, r in REALMS.items():
        n = dict(r["npc"])
        n.update(zone=r["zone"], realm=r["realm"], level=40, idle=r["idle"])
        data["npcs"].append(n)
        q = realm_quest(key, r)
        # checks: every step reached, every keyword in its question
        ids = {s["id"] for s in q["steps"]}
        for s in q["steps"]:
            for o in s["options"]:
                assert o.get("next") in ids or o.get("ending") in q["endings"], (s["id"], o)
                assert f"[{o['keyword']}]" in s["say"], (s["id"], o["keyword"])
        data["quests"].append(q)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(out, sum(len(q["steps"]) for q in data["quests"]), "steps")


if __name__ == "__main__":
    main()
