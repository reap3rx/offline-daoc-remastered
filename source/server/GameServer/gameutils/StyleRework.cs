using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;
using DOL.GS.Styles;

namespace DOL.GS
{
    /// <summary>
    /// The weapon lines' class versions (owner 2026-11-19: "Champions ... would have their own special version of Large
    /// Weapons, same with Heroes, and then there would be a basic version of it ... the uniqueness is baked into the skill
    /// lines"). Every class's styles are its own rows already (style.ClassId); here each class's version of a line is
    /// reshaped at start-up - never written to the database, so it changes with the build. The same styles at the same
    /// levels and openings for everyone (what you learn on one carries over); what a style does when it lands is the
    /// class's: the Hero hits harder and controls (stuns, roots, bleeds), the Champion infuses Valor (its debuffs, around
    /// the target or in a cone). Positionals catch something turned away (often running at your healer): roots, deep
    /// snares, the big stun; front and reactive styles answer what is hitting you.
    ///
    /// Large Weapons (agreed 19 Nov), the taunt and detaunt gone (taunts are shouts now - TauntShouts):
    ///   lvl  style (opening)                 Hero                                Champion
    ///    4   Celtic Rage (after you parry)   endurance back                      drains the target's endurance to you
    ///    6   Celtic Sweep (anytime, cleave)  heavier on each it hits             Submission (DEX/QUI) on all it hits
    ///    8   Hamstring (behind)              root 4 s (breaks on damage)         Languor: deep snare that holds
    ///   10   Hibernian Force (side)          a deep bleed                        Debility pulses around the target
    ///   12   Hibernian Vigor (chain)         3 s stun                            Blast of Courage
    ///   18   Obliteration (chain)            heavier, the slow kept              the slow spreads around the target
    ///   21   Frontal Assault (in front)      a stagger: its wind-up broken       a cone of Demoralization ahead of you
    ///   25   Gigantic Blow (chain)           more growth, surer to hit           the blow and a Valor blast
    ///   29   Ultimate Recovery (after parry) 6 s stun                            Submission on what parried you
    ///   34   Demolish (chain)                armour sundered                     Atony pulses around the target
    ///   39   Shatter (after block)           bleed, its block broken a while     endurance drained around the target
    ///   44   Devastate (chain)               4 s stun                            Ultimate Demoralization around it
    ///   50   Annihilation (behind)           9 s stun and a grievous bleed       Blast of the Champion around it, Crawl
    /// Others (2, 15) as they were. Basic (a class learning the line later - not yet) keeps the line as it was.
    /// Proc spells: ids 30801-30899, hidden line "Style Rework Effects".
    /// </summary>
    public static class StyleRework
    {
        public const string HiddenLine = "Style Rework Effects";
        public const int Hero = 44, Champion = 45, Blademaster = 43;
        public const string LargeWeapons = "Large Weapons";

        // Large Weapons' style ids
        const int Rage = 291, Sweep = 292, Hamstring = 293, Force = 294, Vigor = 295, Obliteration = 297, Frontal = 298,
            Gigantic = 299, Recovery = 300, Demolish = 301, Shatter = 302, Devastate = 303, Annihilation = 304;

        // the proc spells
        // (ids 30801-30899: free in the database and in the scripts - the first try, 64101+, were the King's pets' summons)
        const int HamSnare = 30801, HamRoot = 30802, HamLanguor = 30803, DeepBleed = 30804, DebilityPulse = 30805,
            Stun3 = 30806, BlastCourage = 30807, LethargySpread = 30808, Stagger = 30809, DemoralizeCone = 30810,
            BlastBravery = 30811, Submission = 30812, Sunder = 30813, AtonyPulse = 30814, DrainAround = 30815,
            Stun4 = 30816, UltDemoralize = 30817, GrievousBleed = 30818, BlastChampion = 30819, Crawl = 30820,
            RageDrain = 30821,
            // (the other weapon lines)
            Debility1 = 30822, Root3 = 30823, Stun5 = 30824, SubmissionPulse = 30825, HasteSelf = 30826, ParrySelf = 30827,
            EvadeSelf = 30828, Dazed = 30829, Dent = 30830, Root6 = 30831, SmallBleed = 30832, TailBleed = 30833, BleedB1 = 30834,
            BleedB2 = 30835, BleedB3 = 30836, HeavySnare = 30837;

        /// <summary>Cleaving styles: (class, style id) -> its arc, how many more it reaches, its share of the blow, extra reach.</summary>
        static readonly Dictionary<(int, int), (int Arc, int Extra, double Factor, int Reach)> Cleaves = new();
        public const int CleaveArc = 120, CleaveExtra = 2;
        public const double CleaveFactor = 0.7, HeroCleaveFactor = 0.9;

        /// <summary>A style that buffs you when it lands: (class, style id) -> spell ids cast on yourself (the Blademaster's
        /// bursts of speed, parry and evade).</summary>
        static readonly Dictionary<(int, int), int[]> SelfProcs = new();

        /// <summary>A style whose off-hand strikes again: (class, style id) -> its share of the blow.</summary>
        static readonly Dictionary<(int, int), double> OffhandStrikes = new();
        public const double OffhandShare = 0.4;
        public const ushort SweepFx = 474, SweepHitFx = 2143;   // (Blasting Gale's swirl; a rending slash)

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Register();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[StyleRework] " + ex);
            }
        }

        public static void Register()
        {
            // ---- the proc spells
            Hidden(Db(HamSnare, "Hamstrung", "StyleSpeedDecrease", value: 40, duration: 8, effect: 2135, msg1: "Your leg is cut and you slow!"));
            Hidden(Db(HamRoot, "Hamstrung", "SpeedDecrease", value: 99, duration: 4, effect: 11310, icon: 11361, msg1: "Your hamstring is cut - you can't move!"));
            Hidden(Db(HamLanguor, "Languor", "UnbreakableSpeedDecrease", value: 50, duration: 8, effect: 5437, icon: 5437, msg1: "Your legs grow heavy!"));
            Hidden(Db(DeepBleed, "Deep Bleeding", "StyleBleeding", damage: 8, duration: 32, frequency: 40, damageType: 10, effect: 2130));
            Hidden(Db(DebilityPulse, "Debility", "StrengthConstitutionDebuff", value: 20, duration: 20, radius: 300, effect: 5401, icon: 5401));
            Hidden(Db(Stun3, "Stunned", "StyleStun", duration: 3, effect: 2132));
            Hidden(Db(BlastCourage, "Blast of Courage", "DirectDamage", damage: 40, damageType: 12, effect: 5428));
            Hidden(Db(LethargySpread, "Lethargy", "CombatSpeedDebuff", value: 15, duration: 20, radius: 300, effect: 5421, icon: 5421));
            Hidden(Db(Stagger, "Staggered", "StyleStun", duration: 2, effect: 2132));
            Hidden(Db(DemoralizeCone, "Demoralization", "CombatSpeedDebuff", value: 15, duration: 15, range: 400, radius: 90,
                target: "Cone", effect: 5423, icon: 5423));
            Hidden(Db(BlastBravery, "Blast of Bravery", "DirectDamage", damage: 70, damageType: 12, effect: 5429));
            Hidden(Db(Submission, "Submission", "DexterityQuicknessDebuff", value: 25, duration: 30, effect: 5411, icon: 5411));
            Hidden(Db(Sunder, "Sundered Armor", "ArmorAbsorptionDebuff", value: 15, duration: 20, effect: 2140, icon: 2140,
                msg1: "Your armor is sundered!"));
            Hidden(Db(AtonyPulse, "Atony", "StrengthConstitutionDebuff", value: 30, duration: 20, radius: 300, effect: 5403, icon: 5403));
            Hidden(Db(DrainAround, "Draining Valor", "EnduranceDrain", damage: 12, radius: 300, effect: 5436));
            Hidden(Db(Stun4, "Stunned", "StyleStun", duration: 4, effect: 2132));
            Hidden(Db(UltDemoralize, "Ultimate Demoralization", "CombatSpeedDebuff", value: 19, duration: 20, radius: 300, effect: 5427, icon: 5427));
            Hidden(Db(GrievousBleed, "Grievous Bleeding", "StyleBleeding", damage: 12, duration: 40, frequency: 40, damageType: 10, effect: 2130));
            Hidden(Db(BlastChampion, "Blast of the Champion", "DirectDamage", damage: 150, damageType: 12, radius: 300, effect: 5435));
            Hidden(Db(Crawl, "Crawl", "UnbreakableSpeedDecrease", value: 60, duration: 10, effect: 5440, icon: 5440, msg1: "You can barely move!"));
            Hidden(Db(RageDrain, "Valor's Thirst", "EnduranceDrain", damage: 8, effect: 5436));

            // ---- Large Weapons: the Hero's and the Champion's versions
            int changed = 0;
            foreach (int cls in new[] { Hero, Champion })
            {
                bool hero = cls == Hero;
                // the taunt and detaunt become the cleave and the early back positional
                changed += Reshape(cls, Sweep, "Celtic Sweep", open: 0, value: 0, result: 0, growth: 0.55, hit: 5, def: 0, end: 15,
                    procs: hero ? new int[0] : new[] { Submission });
                changed += Reshape(cls, Hamstring, "Hamstring", open: 2, value: 0, result: 0, growth: 0.6, hit: 10, def: 0, end: 10,
                    procs: new[] { hero ? HamRoot : HamLanguor });
                changed += Procs(cls, Rage, hero ? new int[0] : new[] { RageDrain });
                changed += Procs(cls, Force, hero ? new[] { DeepBleed } : new[] { DebilityPulse });
                changed += Procs(cls, Vigor, hero ? new[] { Stun3 } : new[] { BlastCourage });
                if (hero)
                    changed += Grow(cls, Obliteration, 0.2);
                else
                    changed += Procs(cls, Obliteration, new[] { LethargySpread });
                changed += Procs(cls, Frontal, hero ? new[] { Stagger } : new[] { DemoralizeCone });
                if (hero)
                    changed += Grow(cls, Gigantic, 0.15, hit: 10);
                else
                    changed += Procs(cls, Gigantic, new[] { BlastBravery });
                if (!hero)
                    changed += Procs(cls, Recovery, new[] { Submission });
                changed += hero ? Procs(cls, Demolish, new[] { Sunder }) : Procs(cls, Demolish, new[] { AtonyPulse });
                if (!hero)
                    changed += Procs(cls, Shatter, new[] { DrainAround });
                changed += Procs(cls, Devastate, hero ? new[] { Stun4 } : new[] { UltDemoralize });
                changed += hero ? AddProcs(cls, Annihilation, new[] { GrievousBleed }) : Procs(cls, Annihilation, new[] { BlastChampion, Crawl });
                Cleaves[(cls, Sweep)] = (CleaveArc, CleaveExtra, hero ? HeroCleaveFactor : CleaveFactor, 0);
            }
            Console.WriteLine($"[StyleRework] Large Weapons: {changed} style changes for the Hero and Champion");
            Console.WriteLine($"[StyleRework] the other Hibernian lines: {OtherLines()} style changes");
            Dump();
        }

        // ------------------------------------------------------------------ the other Hibernian lines (agreed 20 Nov)
        //   Hero: stuns, roots, bleeds, heavier chains.  Champion: Valor's debuffs around the target, blasts, drains.
        //   Blademaster (the dual-wield duelist): bursts of attack speed, parry / evade up after a good opening, an off-hand
        //   strike, bleeds that stack. Every class: the taunt / detaunt slots become a cleave and a new style.

        static int OtherLines()
        {
            Hidden(Db(Debility1, "Debility", "StrengthConstitutionDebuff", value: 20, duration: 20, effect: 5401, icon: 5401));
            Hidden(Db(Root3, "Rooted", "SpeedDecrease", value: 99, duration: 3, effect: 11310, icon: 11361, msg1: "You can't move!"));
            Hidden(Db(Stun5, "Stunned", "StyleStun", duration: 5, effect: 2132));
            Hidden(Db(SubmissionPulse, "Submission", "DexterityQuicknessDebuff", value: 25, duration: 20, radius: 300, effect: 5411, icon: 5411));
            Hidden(Db(HasteSelf, "Blade Rush", "CombatSpeedBuff", value: 15, duration: 8, target: "Self", effect: 413, icon: 413,
                msg1: "Your blades quicken!"));
            Hidden(Db(ParrySelf, "Riposte Stance", "ParryBuff", value: 15, duration: 8, target: "Self", effect: 412, icon: 412,
                msg1: "You fall into a riposte stance."));
            Hidden(Db(EvadeSelf, "Light Feet", "EvadeBuff", value: 15, duration: 6, target: "Self", effect: 411, icon: 411,
                msg1: "Your feet grow light."));
            Hidden(Db(Dazed, "Dazed", "CombatSpeedDebuff", value: 20, duration: 6, effect: 2140, icon: 2140, msg1: "You are dazed!"));
            Hidden(Db(Dent, "Dented Armor", "ArmorAbsorptionDebuff", value: 8, duration: 15, effect: 2140, icon: 2140));
            Hidden(Db(Root6, "Rooted", "SpeedDecrease", value: 99, duration: 6, effect: 11310, icon: 11361, msg1: "You can't move!"));
            Hidden(Db(SmallBleed, "Bleeding", "StyleBleeding", damage: 3, duration: 12, frequency: 40, damageType: 10, effect: 2130));
            Hidden(Db(TailBleed, "Bleeding", "StyleBleeding", damage: 5, duration: 20, frequency: 40, damageType: 10, effect: 2130));
            Hidden(Db(BleedB1, "Open Wound", "StyleBleeding", damage: 4, duration: 20, frequency: 40, damageType: 10, effect: 2130));
            Hidden(Db(BleedB2, "Twin Wounds", "StyleBleeding", damage: 6, duration: 30, frequency: 40, damageType: 10, effect: 2130));
            Hidden(Db(BleedB3, "Third Wound", "StyleBleeding", damage: 6, duration: 30, frequency: 40, damageType: 10, effect: 2130));
            Hidden(Db(HeavySnare, "Pinned", "UnbreakableSpeedDecrease", value: 60, duration: 10, effect: 2135, icon: 2135,
                msg1: "A spear pins your leg!"));

            int n = 0;
            const int H = Hero, C = Champion, B = Blademaster;
            int[] none = new int[0];

            // ---- Blades (Hero, Champion, Blademaster)
            n += Procs(H, 246, new[] { Stagger }); About(H, 246, "After you parry: staggers it for 2 seconds.");
            n += Procs(C, 246, new[] { RageDrain }); About(C, 246, "After you parry: you drain your foe's endurance into your own.");
            n += AddProcs(B, 246, none); Self(B, 246, ParrySelf); About(B, 246, "After you parry: slows its attacks, and you fall into a riposte stance (parry up for 8 seconds).");
            foreach (int c in new[] { H, C, B })
            {
                n += Reshape(c, 247, "Arcing Blade", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: c == C ? new[] { Debility1 } : none);
                CleaveAt(c, 247, c == B ? 180 : CleaveArc, CleaveExtra, c == H ? HeroCleaveFactor : CleaveFactor);
                n += Reshape(c, 248, "Guarded Strike", 0, 0, 0, growth: 0.45, hit: 0, def: 15, end: 10, procs: none);
                About(c, 248, "A careful blow: your defense is raised until your next swing.");
            }
            About(H, 247, "A wide slash: also hits up to two more enemies in front of you, hard (90% of the blow).");
            About(C, 247, "A wide slash: also hits up to two more enemies in front of you (70% of the blow) and saps their strength and constitution.");
            About(B, 247, "A wide slash: also hits up to two more enemies around your front (70% of the blow).");
            n += Procs(H, 249, new[] { Root3 }); About(H, 249, "From the side: roots it for 3 seconds (damage frees it).");
            n += Procs(C, 249, new[] { LethargySpread }); About(C, 249, "From the side: lethargy spreads from your foe - everything around it attacks slower.");
            n += AddProcs(B, 249, none); Self(B, 249, HasteSelf); About(B, 249, "From the side: snares it, and your blades quicken for 8 seconds.");
            n += Procs(H, 256, new[] { Stun5, DeepBleed }); About(H, 256, "From behind: stuns for 5 seconds and leaves a deep bleed.");
            n += Procs(C, 256, new[] { SubmissionPulse }); About(C, 256, "From behind: Submission spreads from your foe - all around it lose dexterity and quickness.");
            n += Procs(B, 256, new[] { GrievousBleed }); Strike(B, 256); About(B, 256, "From behind: a grievous bleed, and your off-hand strikes again.");
            n += Grow(H, 259, 0.2); n += Procs(H, 259, new[] { Stun4 }); About(H, 259, "After Revenging Blade: a heavy blow that stuns for 4 seconds.");
            n += Procs(C, 259, new[] { BlastChampion }); About(C, 259, "After Revenging Blade: Blast of the Champion bursts around your foe.");
            n += AddProcs(B, 259, none); Strike(B, 259); Self(B, 259, HasteSelf); About(B, 259, "After Revenging Blade: your off-hand strikes again and your blades quicken.");

            // ---- Blunt (Hero, Champion, Blademaster)
            foreach (int c in new[] { H, C, B })
            {
                n += Reshape(c, 262, "Shockwave", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: new[] { Dazed });
                CleaveAt(c, 262, CleaveArc, CleaveExtra, c == H ? HeroCleaveFactor : CleaveFactor);
                About(c, 262, $"A crushing sweep: also hits up to two more enemies in front of you ({(c == H ? 90 : 70)}% of the blow), and dazes all it hits (slower attacks).");
                n += Reshape(c, 263, "Rattle", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 10, procs: new[] { Dent });
                About(c, 263, "A ringing blow that dents its armour: your blows bite a little deeper for 15 seconds.");
            }
            n += Procs(H, 264, new[] { Stun3 }); About(H, 264, "From the side: stuns for 3 seconds.");
            n += Procs(C, 264, new[] { DebilityPulse }); About(C, 264, "From the side: Debility pulses from your foe, sapping the strength and constitution of all around it.");
            n += AddProcs(B, 264, none); Self(B, 264, EvadeSelf); About(B, 264, "From the side: slows its attacks, and your feet grow light (evade up for 6 seconds).");
            n += Procs(H, 269, new[] { Root6 }); About(H, 269, "From behind: roots it for 6 seconds (damage frees it). Stop one running at your healer.");
            n += Procs(C, 269, new[] { Crawl }); About(C, 269, "From behind: Crawl - it can barely move, through damage.");
            n += Grow(B, 269, 0.15); Strike(B, 269); About(B, 269, "From behind: a heavy blow, and your off-hand strikes again.");
            n += Procs(H, 272, new[] { Stun3 }); About(H, 272, "After you parry: stuns for 3 seconds.");
            n += Procs(C, 272, new[] { AtonyPulse }); About(C, 272, "After you parry: Atony pulses from your foe, sapping the strength and constitution of all around it.");
            n += AddProcs(B, 272, none); Self(B, 272, HasteSelf); About(B, 272, "After you parry: slows its attacks, and your blades quicken.");
            n += AddProcs(H, 274, new[] { Sunder }); About(H, 274, "After Stunning Blow: a long stun, and its armour is sundered.");
            n += Procs(C, 274, new[] { BlastChampion, UltDemoralize }); About(C, 274, "After Stunning Blow: Blast of the Champion and Ultimate Demoralization burst around your foe.");
            n += AddProcs(B, 274, none); Strike(B, 274); About(B, 274, "After Stunning Blow: a long stun, and your off-hand strikes again.");

            // ---- Piercing (Hero, Champion, Blademaster)
            n += Procs(H, 276, new[] { Root3 }); About(H, 276, "From behind: roots it for 3 seconds (damage frees it).");
            n += Procs(C, 276, new[] { Submission }); About(C, 276, "From behind: Submission - its dexterity and quickness fall.");
            n += AddProcs(B, 276, new[] { BleedB1 }); About(B, 276, "From behind: two wounds that bleed together.");
            foreach (int c in new[] { H, C, B })
            {
                n += Reshape(c, 277, "Wasp Swarm", 0, 0, 0, growth: 0.5, hit: 10, def: 0, end: 15, procs: new[] { SmallBleed });
                CleaveAt(c, 277, CleaveArc, CleaveExtra, c == H ? HeroCleaveFactor : CleaveFactor);
                About(c, 277, $"A flurry of jabs: also hits up to two more enemies in front of you ({(c == H ? 90 : 70)}% of the blow), and each of them bleeds.");
                n += Reshape(c, 279, "Scorpion's Tail", 2, 1, 0, growth: 0.6, hit: 10, def: 0, end: 10, procs: new[] { TailBleed });
                About(c, 279, "From the side: a stinging thrust that leaves a bleed.");
            }
            n += AddProcs(H, 283, new[] { Stun3 }); About(H, 283, "From the side: snares it and stuns for 3 seconds.");
            n += Procs(C, 283, new[] { LethargySpread }); About(C, 283, "From the side: lethargy spreads from your foe - everything around it attacks slower.");
            n += AddProcs(B, 283, none); Self(B, 283, HasteSelf); About(B, 283, "From the side: snares it, and your blades quicken.");
            About(H, 284, "After you evade: stuns for 5 seconds.");
            n += Procs(C, 284, new[] { DrainAround }); About(C, 284, "After you evade: Valor drains the endurance of everything around your foe.");
            n += AddProcs(B, 284, none); Self(B, 284, EvadeSelf); About(B, 284, "After you evade: stuns for 5 seconds, and your feet grow light (evade up).");
            n += Procs(H, 289, new[] { GrievousBleed }); About(H, 289, "After Dragonspider: a grievous bleed.");
            n += Procs(C, 289, new[] { BlastChampion }); About(C, 289, "After Dragonspider: Blast of the Champion bursts around your foe.");
            n += AddProcs(B, 289, new[] { BleedB2, BleedB3 }); About(B, 289, "After Dragonspider: three wounds that bleed together.");

            // ---- Celtic Spear (Hero)
            n += Procs(H, 307, new[] { HeavySnare }); About(H, 307, "From behind: pins its leg - a heavy snare that holds through damage.");
            n += Reshape(H, 308, "Flanking Spear", 2, 1, 0, growth: 0.6, hit: 10, def: 0, end: 10, procs: new[] { Root3 });
            About(H, 308, "From the side: roots it for 3 seconds (damage frees it).");
            n += Reshape(H, 309, "Sweeping Spear", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: none);
            CleaveAt(H, 309, 150, CleaveExtra, HeroCleaveFactor, 75);
            About(H, 309, "A long sweep of the spear: also hits up to two more enemies in a wide arc in front of you, further out than other sweeps (90% of the blow).");
            n += Procs(H, 318, new[] { Stun4 }); About(H, 318, "From the side: stuns for 4 seconds.");

            // ---- Celtic Dual (Blademaster)
            n += Reshape(B, 322, "Gale Spin", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 20, procs: none);
            CleaveAt(B, 322, 360, 3, CleaveFactor);
            About(B, 322, "Spin with both blades: also hits up to three more enemies all around you (70% of the blow).");
            n += Reshape(B, 326, "Thunderclap", 0, 323, 7, growth: 0.8, hit: 10, def: 0, end: 10, procs: new[] { Stun3 });
            About(B, 326, "After Snow Shower: both blades crash down - stuns for 3 seconds.");
            n += AddProcs(B, 323, none); Self(B, 323, HasteSelf); About(B, 323, "From behind: snares it, and your blades quicken.");
            n += AddProcs(B, 327, none); Self(B, 327, HasteSelf); About(B, 327, "From the side: stuns for 4 seconds, and your blades quicken.");
            n += AddProcs(B, 333, none); Strike(B, 333); About(B, 333, "After Meteor Shower: a great bleed, and your off-hand strikes again.");
            n += AddProcs(B, 334, none); Strike(B, 334); About(B, 334, "After Tempest: slows its attacks, and your off-hand strikes again.");
            return n;
        }

        /// <summary>What each class's version of the reshaped lines does, written to style-rework.txt beside the server (a check).</summary>
        static void Dump()
        {
            try
            {
                var sb = new System.Text.StringBuilder();
                foreach (var cls in new[] { Hero, Champion, Blademaster })
                    foreach (string spec in new[] { "Large Weapons", "Blades", "Blunt", "Piercing", "Celtic Spear", "Celtic Dual" })
                        foreach (Style st in SkillBase.GetStyleList(spec, cls))
                        {
                            Style r = Ref(cls, st.ID) ?? st;
                            string procs = string.Join(", ", r.Procs.Select(p => $"{p.Spell.Name}[{p.Spell.ID}]{(p.ClassId != 0 ? "" : "*")}"));
                            string self = SelfProcs.TryGetValue((cls, r.ID), out int[] sp) ? " self:" + string.Join("/", sp) : "";
                            string strike = OffhandStrikes.ContainsKey((cls, r.ID)) ? " +offhand" : "";
                            string cleave = Cleaves.TryGetValue((cls, r.ID), out var c) ? $" cleave {c.Arc}deg x{c.Extra} {c.Factor}" : "";
                            sb.AppendLine($"{cls} {spec} {r.SpecLevelRequirement,2} {r.Name} ({r.OpeningRequirementType} {r.OpeningRequirementValue} {r.AttackResultRequirement}) | {procs}{self}{strike}{cleave} | {Describe(r)}");
                        }
                System.IO.File.WriteAllText("style-rework.txt", sb.ToString());
            }
            catch (Exception e)
            {
                Console.WriteLine("[StyleRework] dump: " + e.Message);
            }
        }

        static void About(int cls, int id, string text) => _about[(cls, id)] = text;
        static void Self(int cls, int id, params int[] spells) => SelfProcs[(cls, id)] = spells;
        static void Strike(int cls, int id, double share = OffhandShare) => OffhandStrikes[(cls, id)] = share;
        static void CleaveAt(int cls, int id, int arc, int extra, double factor, int reach = 0) => Cleaves[(cls, id)] = (arc, extra, factor, reach);

        // ------------------------------------------------------------------ the reshaping

        static Style Ref(int cls, int id) => SkillBase.GetStyleRef(id, cls);

        static int Reshape(int cls, int id, string name, int open, int value, int result, double growth, int hit, int def, int end, int[] procs)
        {
            Style st = Ref(cls, id);
            if (st == null)
                return 0;
            DbStyle d = st.Db;
            d.Name = name;
            st.Name = name;
            d.OpeningRequirementType = open;
            d.OpeningRequirementValue = value;
            d.AttackResultRequirement = result;
            d.GrowthRate = growth;
            d.BonusToHit = hit;
            d.BonusToDefense = def;
            d.EnduranceCost = end;
            SetProcs(st, cls, procs);
            return 1;
        }

        static int Procs(int cls, int id, int[] procs)
        {
            Style st = Ref(cls, id);
            if (st == null)
                return 0;
            SetProcs(st, cls, procs);
            return 1;
        }

        static int AddProcs(int cls, int id, int[] procs)
        {
            Style st = Ref(cls, id);
            if (st == null)
                return 0;
            // (the database's own procs go class-specific too - a class proc hides the all-class ones from players)
            var keep = st.Procs.Select(x => x.Spell).ToList();
            st.Procs.Clear();
            foreach (Spell k in keep)
                st.Procs.Add(new StyleProcInfo(k, cls, 100));
            foreach (int p in procs)
                if (SkillBase.GetSpellByID(p) is Spell s)
                    st.Procs.Add(new StyleProcInfo(s, cls, 100));
            return 1;
        }

        static int Grow(int cls, int id, double more, int hit = 0)
        {
            Style st = Ref(cls, id);
            if (st == null)
                return 0;
            st.Db.GrowthRate += more;
            st.Db.BonusToHit += hit;
            return 1;
        }

        /// <summary>The style's procs become these, for its class (the database's own ones go).</summary>
        static void SetProcs(Style st, int cls, int[] procs)
        {
            st.Procs.Clear();
            foreach (int p in procs)
                if (SkillBase.GetSpellByID(p) is Spell s)
                    st.Procs.Add(new StyleProcInfo(s, cls, 100));
        }

        static void Hidden(DbSpell d)
        {
            if (SkillBase.GetSpellByID(d.SpellID) is Spell taken)
            {
                Console.WriteLine($"[StyleRework] spell id {d.SpellID} is already {taken.Name} - {d.Name} not added");
                return;
            }
            SkillBase.AddScriptedSpell(HiddenLine, new Spell(d, 1));
        }

        static DbSpell Db(int id, string name, string type, double value = 0, double damage = 0, int damageType = 0, int duration = 0,
            int frequency = 0, int range = 0, int radius = 0, string target = "Enemy", int effect = 0, int icon = 0, string msg1 = "") =>
            new DbSpell
            {
                SpellID = id, Name = name, Type = type, Target = target, Value = value, Damage = damage, DamageType = damageType,
                Duration = duration, Frequency = frequency, Range = range, Radius = radius, ClientEffect = effect,
                Icon = icon != 0 ? icon : effect, Message1 = msg1, Description = name,
            };

        // ------------------------------------------------------------------ the tooltip's line

        static readonly Dictionary<(int, int), string> _about = new()
        {
            [(Hero, Rage)] = "Turn your parry into a counter: you get some endurance back.",
            [(Champion, Rage)] = "Turn your parry into a counter: you drain your foe's endurance into your own.",
            [(Hero, Sweep)] = "A wide sweep: also hits up to two more enemies in front of you, hard (90% of the blow).",
            [(Champion, Sweep)] = "A wide sweep: also hits up to two more enemies in front of you (70% of the blow) and saps their dexterity and quickness.",
            [(Hero, Hamstring)] = "From behind: cut its hamstring - it is rooted for a moment (any damage frees it). Stop one running at your healer.",
            [(Champion, Hamstring)] = "From behind: Valor's Languor - a heavy snare that holds through damage. Stop one running at your healer.",
            [(Hero, Force)] = "From the side: a deep bleed.",
            [(Champion, Force)] = "From the side: Debility pulses from your foe, sapping the strength and constitution of all around it.",
            [(Hero, Vigor)] = "After Celtic Rage: stuns for 3 seconds.",
            [(Champion, Vigor)] = "After Celtic Rage: a Blast of Courage strikes your foe.",
            [(Hero, Obliteration)] = "After Hibernian Force: a crushing blow that also slows its attacks.",
            [(Champion, Obliteration)] = "After Hibernian Force: lethargy spreads from your foe - everything around it attacks slower.",
            [(Hero, Frontal)] = "From the front: staggers it, breaking the blow it is winding up.",
            [(Champion, Frontal)] = "From the front: a wave of Demoralization - everything in front of you attacks slower.",
            [(Hero, Gigantic)] = "After Hibernian Vigor: a huge blow, surer to land.",
            [(Champion, Gigantic)] = "After Hibernian Vigor: a huge blow and a Blast of Bravery.",
            [(Hero, Recovery)] = "After it parries you: stuns for 6 seconds.",
            [(Champion, Recovery)] = "After it parries you: Submission - its dexterity and quickness fall, so it parries less.",
            [(Hero, Demolish)] = "After Obliteration: sunders its armour - your blows bite deeper.",
            [(Champion, Demolish)] = "After Obliteration: Atony pulses from your foe, sapping the strength and constitution of all around it.",
            [(Hero, Shatter)] = "After it blocks you: a bleed, and its guard is broken - it blocks half as often for a while.",
            [(Champion, Shatter)] = "After it blocks you: Valor drains the endurance of everything around your foe.",
            [(Hero, Devastate)] = "After Ultimate Recovery: stuns for 4 seconds.",
            [(Champion, Devastate)] = "After Ultimate Recovery: Ultimate Demoralization - everything around your foe attacks much slower.",
            [(Hero, Annihilation)] = "From behind: a massive blow, a long stun and a grievous bleed.",
            [(Champion, Annihilation)] = "From behind: Blast of the Champion bursts around your foe, and Crawl all but stops it.",
        };

        /// <summary>The tooltip's first line for a style of a reshaped line, or null.</summary>
        public static string Describe(Style st) =>
            st != null && _about.TryGetValue((st.ClassID, st.ID), out string s) ? s : null;

        // ------------------------------------------------------------------ when a style lands (WeaponAction)

        static readonly ConditionalWeakTable<GameLiving, StrongBox<long>> _guardBroken = new();

        /// <summary>A styled blow landed: the cleave's extra targets, and the class versions' extras.</summary>
        public static void AfterStyle(GameLiving owner, AttackData ad)
        {
            Style st = ad?.Style;
            if (st == null || owner == null || ad.Target == null)
                return;
            try
            {
                if (Cleaves.TryGetValue((st.ClassID, st.ID), out var cl))
                    Cleave(owner, ad, st, cl);
                if (SelfProcs.TryGetValue((st.ClassID, st.ID), out int[] self))
                    foreach (int id in self)
                        if (SkillBase.GetSpellByID(id) is Spell sp)
                            ScriptMgr.CreateSpellHandler(owner, sp, SkillBase.GetSpellLine(GlobalSpellsLines.Combat_Styles_Effect))?.StartSpell(owner);
                if (OffhandStrikes.TryGetValue((st.ClassID, st.ID), out double share))
                    OffhandStrike(owner, ad, share);
                if (st.Spec == LargeWeapons && st.ClassID == Hero)
                {
                    if (st.ID == Rage)                        // the parry flows into the counter: endurance back
                        owner.ChangeEndurance(owner, eEnduranceChangeType.Regenerate, Math.Max(1, owner.MaxEndurance * 8 / 100));
                    else if (st.ID == Shatter)                // its guard broken for a while
                        _guardBroken.AddOrUpdate(ad.Target, new StrongBox<long>(GameLoop.GameLoopTime + 12000));
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"[StyleRework] after {st.Name}: {e.Message}");
            }
        }

        /// <summary>The Blademaster's second weapon strikes the same foe again for a share of the blow.</summary>
        static void OffhandStrike(GameLiving owner, AttackData ad, double share)
        {
            GameLiving t = ad.Target;
            if (t == null || !t.IsAlive)
                return;
            int dmg = Math.Max(1, (int) ((ad.Damage + ad.CriticalDamage) * share));
            var extra = new AttackData
            {
                Attacker = owner, Target = t, Damage = dmg, DamageType = ad.DamageType, AttackType = ad.AttackType,
                AttackResult = eAttackResult.HitUnstyled, Weapon = ad.Weapon, CausesCombat = true,
            };
            t.OnAttackedByEnemy(extra);
            owner.DealDamage(extra);
            foreach (GamePlayer v in owner.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
            {
                v.Out.SendCombatAnimation(null, t, 0, 0, 0, 0, 0x0A, t.HealthPercent);
                v.Out.SendSpellEffectAnimation(owner, t, SweepHitFx, 0, false, 1);
            }
            if (owner is GamePlayer p)
                p.Out.SendMessage($"Your off-hand strikes {t.GetName(0, false)} again for {dmg} damage!", eChatType.CT_YouHit, eChatLoc.CL_SystemWindow);
        }

        /// <summary>MonsterMoves.Defense: a broken guard blocks half as often.</summary>
        public static double BlockFactor(GameLiving defender) =>
            defender != null && _guardBroken.TryGetValue(defender, out StrongBox<long> until) && until.Value > GameLoop.GameLoopTime ? 0.5 : 1.0;

        /// <summary>The cleave: up to CleaveExtra more enemies in the arc in front of you take a share of the blow (and the
        /// style's procs - a Champion's Submission lands on all of them).</summary>
        static void Cleave(GameLiving owner, AttackData ad, Style st, (int Arc, int Extra, double Factor, int Reach) cl)
        {
            int reach = Math.Max(150, owner.attackComponent.AttackRange) + 50 + cl.Reach;
            double factor = cl.Factor;
            int dmg = Math.Max(1, (int) ((ad.Damage + ad.CriticalDamage) * factor));
            var hit = new List<GameLiving>();
            foreach (GameNPC n in owner.GetNPCsInRadius((ushort) reach))
            {
                if (hit.Count >= cl.Extra)
                    break;
                if (n == ad.Target || !n.IsAlive || n.ObjectState != GameObject.eObjectState.Active || (cl.Arc < 360 && !owner.IsObjectInFront(n, cl.Arc)))
                    continue;
                if (!GameServer.ServerRules.IsAllowedToAttack(owner, n, true) || MonsterTiers.Combatant(n) != null)
                    continue;
                hit.Add(n);
            }
            // the sweep: a gust of wind around you (Blasting Gale's swirl and whoosh), a slash on everything it catches
            foreach (GamePlayer v in owner.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(owner, owner, SweepFx, 0, false, 1);
            foreach (GameLiving t in hit)
            {
                MonsterTiers.Touch(owner, t);
                var extra = new AttackData
                {
                    Attacker = owner, Target = t, Damage = dmg, DamageType = ad.DamageType, AttackType = ad.AttackType,
                    AttackResult = eAttackResult.HitUnstyled, Weapon = ad.Weapon, CausesCombat = true,
                };
                t.OnAttackedByEnemy(extra);
                owner.DealDamage(extra);
                foreach (GamePlayer v in owner.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                {
                    v.Out.SendCombatAnimation(null, t, 0, 0, 0, 0, 0x0A, t.HealthPercent);
                    v.Out.SendSpellEffectAnimation(owner, t, SweepHitFx, 0, false, 1);
                }
                if (owner is GamePlayer op)
                    op.Out.SendMessage($"Your sweep hits {t.GetName(0, false)} for {dmg} damage!", eChatType.CT_YouHit, eChatLoc.CL_SystemWindow);
                if (ad.StyleEffects != null)
                    foreach (ISpellHandler proc in ad.StyleEffects)
                        if (proc?.Spell != null && proc.Spell.Radius == 0)   // (an area proc already reached them)
                            ScriptMgr.CreateSpellHandler(owner, proc.Spell, proc.SpellLine)?.StartSpell(t);
            }
        }
    }
}
