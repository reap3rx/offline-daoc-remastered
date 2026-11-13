"""The companion quest, "A Friend for the Road" (owner 2026-11-11 / 2026-11-12: at level 7 a quest sends you to someone
in your starting town; "maybe it's an older person who says something like they saw a new adventurer going off into some
dangerous area. You ask them who it was, and they something like 'Oh, it was this man... or was it a woman?' like
they're a confused old person ... Then the old person directs you to the direction they went, and there you'd go on a
short quest where you save them from some sort of mini boss mob. After that, you talk to them, they thank you, and ask
to join you."). Writes source/server/GameServer/scripts/storyquests/quests/companion.json, one quest a realm:

  sex      (choice)     the old one can't remember: a [man]? a [woman]?
  class    (choice)     "one of those ... oh, what do you call them": the realm's classes, or [back]
  race_X   (choice)     "and what folk?": the class's races only, or [back]; a race sends you down the road
  rescue   (encounter)  the camp where they were cornered: its leader (and its friends) to beat
  thank    (companion)  the one you saved, who thanks you and asks to come along (PersonalCompanions.cs)

PersonalCompanions.cs records the answers (StoryQuestManager.ChoiceMade: sex, class, race; the name comes with the race),
fills in {cname} / {he} / {He} / {him} / {his} (StoryQuestManager.MoreWords), puts the rescued one at the camp for the
last step and makes them your companion when the quest ends.

    python tools/claude-version/story_companion.py [out.json]
"""
import json
import sys

# (class, what the old one remembers of them, its races) - AutonomousBotIdentityGenerator.Choices
REALMS = {
    "alb": dict(
        realm=1, zone=0, town="Cotswold Village",
        npc=dict(id="companion_hesketh", name="Old Mother Hesketh", model=38, guild="", pos=[294, 712, 57.0]),
        hello="Oh! You there - {name}, isn't it? You've the look of someone who knows which end of a sword is which. "
              "Listen, dear. Not an hour ago somebody went marching off down the south-east road after those cutpurses "
              "that have been robbing the farms. All on their own! Young, and far too pleased with themselves. It was "
              "a young... now, was it a [man]? Or was it a [woman]? Dear me. My eyes aren't what they were.",
        idle="Mind the cutpurses on the south-east road, dear. And eat something.",
        where="Off down the south-east road, toward the cutpurses' camp past the old farm fields.",
        thanks="Light above, that was close! I had them, you know. Right up until I didn't. I'm {cname} - and you're "
               "{name}? Old Mother Hesketh sent you, didn't she. She worries.\n\nI owe you my life, and I don't like "
               "owing. So here's a thought: I was a fool to come out here alone, and I'll not make that mistake twice. "
               "Let me come with you. I'll watch your back, and you can keep me from doing anything this stupid again. "
               "What do you say? [Come along, then] [Glad to have you]",
        rescue=dict(at=[500, 900, 59.7], goal="Find the reckless adventurer at the cutpurses' camp, south-east of Cotswold",
                    boss=dict(template=12076, name="Rook the Cutpurse Captain", level=8, health_mult=1.5),
                    adds=dict(template=12076, name="cutpurse", level=[5, 6]),
                    announce="Behind a toppled cart someone is shouting for help - the cutpurses have them cornered. "
                             "Their captain turns, grinning. 'Another hero? We'll have your purse as well.'",
                    done="The last of the cutpurses scatters into the hedges. From behind the cart, the one you came "
                         "for climbs out - bruised, scraped, and grinning."),
        groups=[
            ("Was it one of the steel-and-shield sort?", [
                ("Armsman", "All that plate - you could hear the clanking from the well.", "Avalonian Briton Highlander Inconnu Saracen"),
                ("Paladin", "Shining like a chapel window, and singing hymns as {he} went. Off-key.", "Avalonian Briton Highlander Saracen"),
                ("Mercenary", "Two swords and not a shred of patience between them.", "Avalonian Briton Highlander Inconnu Saracen"),
                ("Reaver", "One of those flail-swinging sorts with the dark prayers. Gave me a turn, {he} did.", "Briton Inconnu Saracen")]),
            ("One of the praying sort?", [
                ("Cleric", "Blessed my hip on the way past, bless {him}. It's never felt better.", "Avalonian Briton Highlander"),
                ("Friar", "A great big staff and a laugh you could hear in Camelot.", "Briton")]),
            ("Or one of those magic folk?", [
                ("Wizard", "Singed my washing hanging out to dry - by accident, {he} said.", "Avalonian Briton"),
                ("Theurgist", "Had a little cloud of something following {him} about. Buzzing.", "Avalonian Briton"),
                ("Sorcerer", "Looked straight through me as if {he} could read my thoughts. Rude.", "Avalonian Briton Inconnu Saracen"),
                ("Cabalist", "Had a great lump of clay walking behind {him}, like a dog.", "Avalonian Briton Inconnu Saracen"),
                ("Necromancer", "Pale as milk, and a shadow that didn't move when {he} did.", "Briton Inconnu Saracen")]),
            ("Or the quick, quiet kind?", [
                ("Scout", "A longbow taller than I am, and a shield on {his} back.", "Briton Highlander Inconnu Saracen"),
                ("Infiltrator", "I didn't hear {him} coming. I didn't hear {him} going either.", "Briton Inconnu Saracen"),
                ("Minstrel", "Humming all the way down the road, and I was humming it too.", "Briton Highlander Saracen")]),
        ]),
    "mid": dict(
        realm=2, zone=100, town="Mularn",
        npc=dict(id="companion_gunnar", name="Old Gunnar One-Ear", model=213, guild="", pos=[1258, 1362, 117.0]),
        hello="Eh? Oh, it's you - {name}. I know that face, I never forget a face. Ears, now, ears I forget. Ha! Listen. "
              "Somebody went off east along the shore this morning, after the raiders that have been bothering the "
              "fishermen. Alone! The young never listen. It was a... hm. A [man], was it? Or a [woman]? "
              "Bah. My one good eye is getting worse than the other one.",
        idle="Raiders on the east shore, I tell everyone. Nobody listens to old Gunnar.",
        where="East along the shore, where the raiders have their camp. Go on - and don't let the young fool die!",
        thanks="By Odin's eye, I thought that was the end of me! {cname}, that's my name - and you're {name}, the one old "
               "Gunnar keeps going on about. He sent you, didn't he?\n\nI owe you a life-debt, and in Midgard we pay "
               "those. So: I'll stand with you. Shield to shield, wherever you're going, until the debt's paid and then "
               "some. Will you have me? [Shield to shield] [Glad to have you]",
        rescue=dict(at=[1400, 1250, 117.7], goal="Find the reckless adventurer at the raiders' camp, east of Mularn",
                    boss=dict(template=60162147, name="Hrolf Fish-Thief", level=8, health_mult=1.5),
                    adds=dict(template=60162147, name="shore raider", level=[5, 6]),
                    announce="On the shingle, someone is backed against an upturned boat with a raider's axe at their "
                             "throat. The raider-chief laughs. 'Two fools for the price of one!'",
                    done="The raiders flee up the shore. From behind the boat, the one you came for stands up, "
                         "spitting sand and grinning."),
        groups=[
            ("One of the axe-and-shield sort?", [
                ("Warrior", "A shield like a barn door. Nearly took my good ear off with it.", "Dwarf Kobold Norseman Troll Valkyn"),
                ("Thane", "Smelled of lightning. You know the smell. Like after a storm.", "Dwarf Norseman Troll"),
                ("Berserker", "Growling at nothing all the way down the road. Reminded me of me.", "Dwarf Norseman Troll Valkyn"),
                ("Savage", "Bare-armed in this cold, and claws on {his} fists!", "Dwarf Kobold Norseman Troll Valkyn"),
                ("Skald", "Singing one of the old songs, the long one, about the giants.", "Dwarf Kobold Norseman Troll")]),
            ("One of the healers?", [
                ("Healer", "Fixed my knee as {he} walked past. Didn't even ask. Good knee now.", "Dwarf Norseman"),
                ("Shaman", "Bones and feathers rattling all over {him}. Proper old ways.", "Kobold Troll")]),
            ("Or the rune folk, the spirit folk?", [
                ("Runemaster", "Muttering runes, and the air went all crackly.", "Dwarf Kobold Norseman"),
                ("Spiritmaster", "There was a ghost walking with {him}. A warrior's ghost. I'm sure of it.", "Kobold Norseman"),
                ("Bonedancer", "Three skeletons trotting behind {him} like puppies!", "Kobold Troll Valkyn")]),
            ("Or the hunting, sneaking kind?", [
                ("Hunter", "A spear, a bow, and a hound sniffing my boots.", "Dwarf Kobold Norseman Valkyn"),
                ("Shadowblade", "Two blades, and gone before I'd blinked my good eye.", "Kobold Norseman Valkyn")]),
        ]),
    "hib": dict(
        realm=3, zone=200, town="Mag Mell",
        npc=dict(id="companion_tadhg", name="Old Tadhg", model=337, guild="", pos=[660, 190, 130.0]),
        hello="Ah, {name}! The very one. Sit, sit - no, don't sit, there isn't time. Some youngster went off down the "
              "south road an hour since, after that gang of rowdies that have been robbing travellers. On their own, "
              "mind you! Reckless as a hare in spring. It was a... a [man], I think? Or a [woman]? "
              "The faeries have been at my memory again.",
        idle="Rowdies on the south road. I told the guards. They laughed. Laughed!",
        where="South, down the road from the town hall. The rowdies camp by the stones. Run, now!",
        thanks="Lugh's light, you came at the perfect moment - I was just about to win, honestly. I'm {cname}. And "
               "you'd be {name}? Old Tadhg sent you. Of course he did.\n\nListen: I came out here alone because I "
               "thought I had to prove something. I don't think I do any more. I'd rather walk with someone worth "
               "following. Would you have me along? [Walk with me] [Glad to have you]",
        rescue=dict(at=[560, 380, 123.9], goal="Find the reckless adventurer at the rowdies' camp, south of Mag Mell",
                    boss=dict(template=60165445, name="Fearghal the Rowdy", level=8, health_mult=1.5),
                    adds=dict(template=60167680, name="villainous youth", level=[5, 6]),
                    announce="Among the stones someone is fending off three rowdies at once, and losing. A big lump of "
                             "a man cracks his knuckles. 'Here's another one wants a hiding!'",
                    done="The rowdies run for the trees. Leaning on a standing stone, the one you came for catches "
                         "their breath - and laughs."),
        groups=[
            ("Was it one of the blade-and-shield sort?", [
                ("Hero", "A shield and a spear, and a jaw like a cliff.", "Celt Firbolg Lurikeen Sylvan"),
                ("Blademaster", "Two blades, spinning them about just walking. Showing off.", "Celt Elf Firbolg"),
                ("Champion", "A sword as tall as {him}, and a bit of magic about {him} besides.", "Celt Elf Lurikeen"),
                ("Valewalker", "Carrying a scythe! In spring! The forest smell on {him} was lovely, though.", "Celt Firbolg Sylvan"),
                ("Sluaghbinder", "Something cold followed {him}. Whispering. I didn't like it.", "Celt Firbolg")]),
            ("One of the nurturing sort?", [
                ("Druid", "Flowers came up where {he} walked. Honestly. Look, there's one.", "Celt Firbolg Sylvan"),
                ("Warden", "Gave me a pat on the shoulder and my aches went - just like that.", "Celt Firbolg Sylvan"),
                ("Bard", "A harp on {his} back and a song I can't get out of my head.", "Celt Firbolg")]),
            ("Or the magic folk?", [
                ("Eldritch", "Eyes like the empty sky at night. Gave me the shivers.", "Elf Lurikeen"),
                ("Enchanter", "Little lights dancing round {him}, like midges made of glass.", "Elf Lurikeen"),
                ("Mentalist", "Knew my name before I said it. I'd swear to it.", "Celt Elf Lurikeen"),
                ("Animist", "Mushrooms! Walking mushrooms, following {him} down the road.", "Celt Firbolg Sylvan")]),
            ("Or the bow and shadow kind?", [
                ("Ranger", "A bow from the high woods, and eyes that missed nothing.", "Celt Elf Lurikeen"),
                ("Nightshade", "There one moment, gone the next. Like a cat.", "Elf Lurikeen")]),
        ]),
}


def realm_quest(key, r):
    npc = r["npc"]
    who = npc["name"]
    sex_q = r["hello"]

    def class_list(pron):
        lines = []
        for ask, classes in r["groups"]:
            lines.append(ask + " " + ", ".join(f"[{c}]" for c, _, _ in classes))
        return (f"{pron} looked like one of those... oh, what do you call them...\n\n" + "\n".join(lines) +
                "\n\nOr was I wrong about the rest? Let me go [back] a bit.")

    def race_q(cls, blurb, races):
        rs = races.split()
        art = "An" if cls[0] in "AEIOU" else "A"
        folk = ", ".join(f"[{x}]" for x in rs[:-1]) + (" or " if len(rs) > 1 else "") + f"[{rs[-1]}]"
        return (f"{art} {cls}! Yes, that's it. {blurb}\n\nNow, what folk was {{he}}? I can see the face plain as day, "
                f"but... {folk}?\n\nOr have I got the calling wrong? Let me go [back].")

    def chose(cls):
        return [dict(keyword=x, say=f"{'An' if x[0] in 'AEIOU' else 'A'} {x}! Of course it was. {r['where']}", next="rescue")
                for x in cls.split()]

    steps = [dict(id="sex", type="choice", npc=npc["id"], goal=f"Speak with {who} in {r['town']}", say=sex_q,
                  options=[dict(keyword="man", say="A man! Yes - yes, a young man, I'm sure of it now. "
                                                    + class_list("He").replace("{he}", "he").replace("{He}", "He")
                                                    .replace("{him}", "him").replace("{his}", "his"), next="class"),
                           dict(keyword="woman", say="A woman! Yes - a young woman, I'm sure of it now. "
                                                     + class_list("She").replace("{he}", "she").replace("{He}", "She")
                                                     .replace("{him}", "her").replace("{his}", "her"), next="class")]),
             dict(id="class", type="choice", npc=npc["id"], goal=f"Help {who} remember the adventurer's calling",
                  say="Where was I? Oh yes. " + class_list("{He}"),
                  options=[dict(keyword="back", say=sex_q, next="sex")] +
                          [dict(keyword=c, say=race_q(c, b, rs), next="race_" + c) for _, cl in r["groups"] for c, b, rs in cl])]
    for _, cl in r["groups"]:
        for c, b, rs in cl:
            steps.append(dict(id="race_" + c, type="choice", npc=npc["id"], goal=f"Help {who} remember the adventurer's folk",
                              say=race_q(c, b, rs),
                              options=[dict(keyword="back", say="Where was I? Oh yes. " + class_list("{He}"), next="class")] +
                                      chose(rs)))
    rs = r["rescue"]
    steps.append(dict(id="rescue", type="encounter", zone=r["zone"], at=rs["at"], wake_m=35, goal=rs["goal"],
                      text=rs["done"],
                      stages=[dict(id="b1", type="boss", name=rs["boss"]["name"], center=rs["at"], radius=30, time_s=600,
                                   objective="Defeat " + rs["boss"]["name"], announce=rs["announce"],
                                   boss=rs["boss"], success=rs["boss"]["name"] + " falls.", fail="You fall back.",
                                   adds=dict(every_s=40, count=1, mobs=[rs["adds"]]))]))
    steps.append(dict(id="thank", type="companion", zone=r["zone"], at=rs["at"], goal="Speak with the adventurer you saved",
                      say=r["thanks"], ending="joined"))
    return dict(
        id="companion_" + key, title="A Friend for the Road", level=7, min_level=7, realm=r["realm"], giver=npc["id"],
        offer=f"You! {{name}}! Have you a moment for an old one's worry? Someone's gone off alone where they oughtn't. "
              f"Will you [help]?",
        accept="help",
        summary=f"{who} of {r['town']} saw a young adventurer go off alone toward trouble - if only the old one could "
                f"remember who it was.",
        steps=steps,
        endings={"joined": dict(text="")},
    )


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "source/server/GameServer/scripts/storyquests/quests/companion.json"
    data = dict(name="companion", npcs=[], quests=[])
    for key, r in REALMS.items():
        n = dict(r["npc"])
        n.update(zone=r["zone"], realm=r["realm"], level=40, idle=r["idle"])
        if not n["guild"]:
            del n["guild"]
        data["npcs"].append(n)
        q = realm_quest(key, r)
        # checks: every step reached, every keyword in its question
        ids = {s["id"] for s in q["steps"]}
        for s in q["steps"]:
            for o in s.get("options", []):
                assert o.get("next") in ids or o.get("ending") in q["endings"], (s["id"], o)
                assert f"[{o['keyword']}]" in s["say"], (s["id"], o["keyword"])
        data["quests"].append(q)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(out, sum(len(q["steps"]) for q in data["quests"]), "steps")


if __name__ == "__main__":
    main()
