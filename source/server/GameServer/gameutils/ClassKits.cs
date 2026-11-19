using System;
using System.Collections.Generic;
using DOL.Database;
using DOL.Events;

namespace DOL.GS
{
    /// <summary>
    /// The casters' new spells (owner 2026-11-19: "Look at each caster and think of cool unique spells ... Go ahead with
    /// ... all Hibernian casters"), added to their spec lines at start-up - never written to the database, so they can be
    /// tuned here and change with the build. Each is learned as its spec line reaches the level given (a level where its line
    /// has no other spell: the client calls a spell by its line and level); a spell with more
    /// than one rank upgrades in place (SpellFamilies: one family, by its group). The proc and snare spells they cast are
    /// kept in their own hidden line. Spell ids 97000-97099, groups 97000-97099.
    ///
    /// Hibernia:
    ///   Eldritch   Void Step (Void Mastery 10)        blink forward, the darkness left behind snares
    ///              Umbral Ward (Shadow Control 20)    buff: whatever strikes you may be slowed (its blows)
    ///   Enchanter  Glamour Ward (Empowering 10)       buff: whatever strikes you may be snared
    ///              Mirror Image (Bedazzling 15)       two images take your attackers' attention
    ///   Mentalist  Mind Spike (Mind Mastery 7+)       instant ranged interrupt; castable behind the Mana Shield
    ///              Thought Bulwark (Holism 19+)       a groupmate's blows half absorbed, to a limit
    ///   Animist    Rootbind Ward (Arboreal 10)        buff: whatever strikes you may be rooted, briefly
    ///              Thorn Wall (Creeping 13)           a line of brambles at the ground target snares what crosses it
    ///   Druid      Verdant Pulse (Regrowth 9)        healing shoots at your feet for your side
    ///              Bear's Hide (Nature 14+)           instant: half of the blows on you absorbed, to a limit
    ///   Bard       Discordant Note (Music 6+)         instant ranged interrupt; castable behind the Mana Shield
    ///              Lullaby Wave (Music 22)            a frontal cone mesmerize
    /// </summary>
    public static class ClassKits
    {
        public const string HiddenLine = "Class Kit Effects";

        // the sub-spells (procs, snares)
        public const int VoidSnare = 97050, UmbralSlow = 97051, GlamourSnare = 97052, RootbindRoot = 97053, ThornSnare = 97054;

        public static readonly HashSet<int> Interrupts = new();

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Register();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[ClassKits] " + ex);
            }
        }

        static int _added;

        public static void Register()
        {
            // ---- the hidden effects
            Hidden(Db(VoidSnare, "Void Grasp", "SpeedDecrease", "Enemy", value: 50, duration: 2, effect: 4561, icon: 4551, group: 97050,
                msg1: "The void clutches at your legs!"));
            Hidden(Db(UmbralSlow, "Umbral Haze", "CombatSpeedDebuff", "Enemy", value: 25, duration: 5, effect: 4251, icon: 4251, group: 97051,
                msg1: "Darkness slows your blows!"));
            Hidden(Db(GlamourSnare, "Glamoured", "SpeedDecrease", "Enemy", value: 40, duration: 5, effect: 5281, icon: 5281, group: 97052,
                msg1: "A glamour tangles your feet!"));
            Hidden(Db(RootbindRoot, "Rootbound", "SpeedDecrease", "Enemy", value: 99, duration: 3, effect: 11310, icon: 11361, group: 97053,
                msg1: "Roots burst from the ground and hold you!"));
            Hidden(Db(ThornSnare, "Thorns", "SpeedDecrease", "Enemy", value: 60, duration: 2, effect: 5281, icon: 5281, group: 97054,
                msg1: "Thorns tear at your legs!"));

            // ---- Eldritch
            Add("Void Mastery", 10, Db(97000, "Void Step", "VoidStep", "Self", value: 700, radius: 220, duration: 6, sub: VoidSnare,
                power: -6, recast: 15, effect: 4561, icon: 4551, group: 97000,
                desc: "Step through the void a short way ahead; the darkness you leave snares enemies in it."));
            Add("Shadow Control", 20, Db(97001, "Umbral Ward", "DefensiveProc", "Self", value: UmbralSlow, frequency: 30, duration: 600,
                power: -8, cast: 3, effect: 4161, icon: 4161, group: 97001, msg1: "Shadows gather about you.", msg2: "Shadows gather about {0}.",
                desc: "Shadows guard you: whatever strikes you may find its blows slowed."));
            // ---- Enchanter
            Add("Empowering", 10, Db(97002, "Glamour Ward", "DefensiveProc", "Self", value: GlamourSnare, frequency: 30, duration: 600,
                power: -8, cast: 3, effect: 4451, icon: 4451, group: 97002, msg1: "A shimmering glamour surrounds you.",
                msg2: "A shimmering glamour surrounds {0}.", desc: "A glamour guards you: whatever strikes you may be snared."));
            Add("Bedazzling", 15, Db(97003, "Mirror Image", "MirrorImage", "Self", value: 25, duration: 8, power: -10, recast: 30,
                effect: 4221, icon: 4221, group: 97003, desc: "Two images of you step out and draw your enemies' attacks."));
            // ---- Mentalist
            Rank("Mind Mastery", new[] { 7, 20, 34, 44 }, new[] { "Mind Spike", "Mind Lance", "Mind Pike", "Mind Spear" },
                (i, n) => Db(97004, n, "DirectDamage", "Enemy", damage: new[] { 25, 60, 95, 130 }[i], damageType: 12,
                    range: 1500, power: -4, recast: 12, effect: 4421, icon: 4421, group: 97004,
                    desc: "An instant spike of thought that interrupts the target's casting."), true);
            Rank("Holism", new[] { 19, 37 }, new[] { "Thought Bulwark", "Thought Bastion" },
                (i, n) => Db(97010 + i, n, "AblativeArmor", "Realm", value: new[] { 200, 450 }[i], damage: 50, range: 1500, duration: 15,
                    power: -8, recast: 30, effect: 4301, icon: 4301, group: 97010, msg1: "A wall of thought shields you.",
                    msg2: "A wall of thought shields {0}.", desc: "Your thought shields a friend: half of each blow on them is absorbed, to a limit."), false);
            // ---- Animist
            Add("Arboreal Mastery", 10, Db(97012, "Rootbind Ward", "DefensiveProc", "Self", value: RootbindRoot, frequency: 25, duration: 600,
                power: -8, cast: 3, effect: 11237, icon: 11237, group: 97012, msg1: "Roots wind up around your legs.",
                msg2: "Roots wind up around {0}'s legs.", desc: "Roots guard you: whatever strikes you may be held for a moment."));
            Add("Creeping Path Spec", 13, Db(97013, "Thorn Wall", "ThornWall", "Area", radius: 120, range: 1500, duration: 10, sub: ThornSnare,
                power: -8, cast: 1, recast: 25, effect: 5281, icon: 5281, group: 97013,
                desc: "A line of brambles grows across your ground target and snares enemies that cross it."));
            // ---- Druid
            Add("Regrowth Druid Spec", 9, Db(97014, "Verdant Pulse", "VerdantPulse", "Self", value: 60, radius: 350, duration: 12,
                power: -10, cast: 2, recast: 30, effect: 4851, icon: 4851, group: 97014,
                desc: "Healing shoots spring up at your feet and heal your side among them every 2 seconds."));
            Rank("Druid Nature Spec", new[] { 14, 31, 45 }, new[] { "Bear's Hide", "Bear's Bulwark", "Ursine Bulwark" },
                (i, n) => Db(97015 + i, n, "AblativeArmor", "Self", value: new[] { 150, 350, 600 }[i], damage: 50, duration: 15,
                    power: -6, recast: 45, effect: 5271, icon: 11238, group: 97015, msg1: "Your skin hardens like a bear's hide.",
                    msg2: "{0}'s skin hardens like a bear's hide.", desc: "Instant: half of each blow on you is absorbed, to a limit."), false);
            // ---- Bard
            Rank("Bard Music Spec", new[] { 6, 17, 31, 42 }, new[] { "Discordant Note", "Discordant Chord", "Discordant Peal", "Discordant Clangor" },
                (i, n) => Db(97020 + i, n, "DirectDamage", "Enemy", damage: new[] { 20, 50, 85, 120 }[i], damageType: 10, range: 1500,
                    power: -4, recast: 12, effect: 5361, icon: 5361, group: 97020,
                    desc: "An instant jarring note that interrupts the target's casting."), true);
            Add("Bard Music Spec", 22, Db(97025, "Lullaby Wave", "Mesmerize", "Cone", range: 600, radius: 60, duration: 12, power: -10,
                cast: 2.5, recast: 30, effect: 5371, icon: 5371, group: 97025, desc: "A wave of lullaby that mesmerizes what stands in front of you."));

            foreach (int id in Interrupts)
                ManaShield.AllowedIds.Add(id);
            Console.WriteLine($"[ClassKits] {_added} class kit spells added");
        }

        static void Rank(string line, int[] levels, string[] names, Func<int, string, DbSpell> make, bool interrupt)
        {
            for (int i = 0; i < levels.Length; i++)
            {
                DbSpell d = make(i, names[i]);
                d.SpellID = d.SpellGroup + i;
                Add(line, levels[i], d);
                if (interrupt)
                    Interrupts.Add(d.SpellID);
            }
        }

        static void Add(string line, int level, DbSpell d)
        {
            SkillBase.AddScriptedSpell(line, new Spell(d, level));
            _added++;
        }

        static void Hidden(DbSpell d) => SkillBase.AddScriptedSpell(HiddenLine, new Spell(d, 1));

        static DbSpell Db(int id, string name, string type, string target, double value = 0, double damage = 0, int damageType = 0,
            int range = 0, int radius = 0, int duration = 0, int frequency = 0, int sub = 0, int power = 0, double cast = 0,
            int recast = 0, int effect = 0, int icon = 0, int group = 0, string msg1 = "", string msg2 = "", string desc = "") =>
            new DbSpell
            {
                SpellID = id, Name = name, Type = type, Target = target, Value = value, Damage = damage, DamageType = damageType,
                Range = range, Radius = radius, Duration = duration, Frequency = frequency, SubSpellID = sub, Power = power,
                CastTime = cast, RecastDelay = recast, ClientEffect = effect, Icon = icon, SpellGroup = group,
                Message1 = msg1, Message2 = msg2, Description = desc,
            };
    }
}
