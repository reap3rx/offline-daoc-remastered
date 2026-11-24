using DOL.GS.Styles;

namespace DOL.GS
{
    /// <summary>
    /// Midgard's weapon lines' class versions (owner 2026-11-24, "Midgard Class Rework - the plan": "Go ahead with the build of
    /// Midgard's classes"). The same rules as Hibernia's and Albion's: every class's styles are its own rows; the same styles
    /// at the same levels and openings for everyone; what a style does when it lands is the class's. Sword, Axe and Hammer
    /// each cover the one- and two-handed weapons of their kind, so one class version serves both grips; the grip itself
    /// changes a style a little (risk against reward - MidgardKits.Grip). Taunt and detaunt slots become a cleave and a new
    /// style (taunts are shouts now - TauntShouts).
    ///   Warrior    (the Hero's / Armsman's counterpart) control: positionals stun, root, snare and sunder; reactives stagger;
    ///              chains a little heavier; its sweeps hit hardest.
    ///   Thane      (the Champion's / Paladin's) Thor's lightning on its chain finishers - kept below the pure fighters'
    ///              damage (owner: "make sure ... they don't outdamage the pure fighters like Warriors and Heroes").
    ///   Berserker  (the Blademaster's / Mercenary's) off-hand strikes and bleeds on the Left Axe; rage (MidgardKits).
    ///   Savage     (the Valewalker's / Reaver's) Hand to Hand: Feral Leap, Rending Claws; the blood price (MidgardKits).
    ///   Skald      the positionals daze; every style that lands is Saga (MidgardKits).
    ///   Shadowblade the positionals leave it Marked; Ravager drops threat; Garrote breaks spells.
    ///   Hunter     the positionals snare and root to make room for the bow; Leap Away.
    /// Proc spells: ids 30950-30969, hidden line "Style Rework Effects".
    /// </summary>
    public static partial class StyleRework
    {
        public const int ThorBolt = 30950, ThorBoltBig = 30951;

        // Midgard's style ids (the same in every class's rows)
        public const int SwordTaunt = 148, SwordDetaunt = 151, AxeTaunt = 178, AxeDetaunt = 181, HammerTaunt = 167, HammerDetaunt = 163,
            LeftTaunt = 195, LeftRavager = 193, HthTaunt = 372, HthDetaunt = 375, HthTaunt2 = 376, HthDetaunt2 = 380,
            SpearTaunt = 208, SpearDetaunt = 211;

        /// <summary>The Shadowblade's positionals that leave it Marked (a stealth opener on it always crits).</summary>
        public static readonly int[] ShadowbladeMarks = { 335, 338, 339, 343, 192, 201, 149, 160, 182, 188 };

        /// <summary>The Thane's chain finishers that call Thor's lightning (the big bolt on the last of each line).</summary>
        public static readonly int[] ThaneBolts = { 156, 158, 159, 187, 189, 190, 172, 174, 175 };
        static readonly int[] ThaneBigBolts = { 159, 190, 175 };

        static int MidgardLines()
        {
            Hidden(Db(ThorBolt, "Thor's Strike", "DirectDamage", damage: 35, damageType: (int) eDamageType.Energy, effect: 3508, msg1: "Lightning strikes you!"));
            Hidden(Db(ThorBoltBig, "Thor's Hammerfall", "DirectDamage", damage: 80, damageType: (int) eDamageType.Energy, effect: 3541, msg1: "Thor's hammer falls on you!"));

            const int Th = MidgardKits.Thane, Wa = MidgardKits.Warrior, Sb = MidgardKits.Shadowblade, Sk = MidgardKits.Skald,
                Hu = MidgardKits.Hunter, Be = MidgardKits.Berserker, Sa = MidgardKits.Savage;
            int[] none = new int[0];
            int n = 0;
            string saga = " Saga: a stack when it lands.";
            string marked = " It is left Marked for 15 seconds: a stealth opener on it always crits.";

            // ---- the taunt and detaunt slots: a cleave and a new style, every class with the line
            foreach (int c in new[] { Th, Wa, Sb, Sk, Hu, Be, Sa })
            {
                double f = c == Wa ? HeroCleaveFactor : CleaveFactor;
                n += Reshape(c, SwordTaunt, "Sweeping Blade", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: none);
                CleaveAt(c, SwordTaunt, CleaveArc, CleaveExtra, f);
                About(c, SwordTaunt, $"A wide sweep of the sword: also hits up to two more enemies in front of you ({f * 100:0}% of the blow)." + (c == Sk ? saga : ""));
                n += Reshape(c, SwordDetaunt, "Steady Blade", 0, 0, 0, growth: 0.45, hit: 0, def: 15, end: 10, procs: none);
                About(c, SwordDetaunt, "A careful cut: your defense is raised until your next swing." + (c == Sk ? saga : ""));
            }
            foreach (int c in new[] { Th, Wa, Sb, Sk, Be, Sa })
            {
                double f = c == Wa ? HeroCleaveFactor : CleaveFactor;
                n += Reshape(c, AxeTaunt, "Cleaving Arc", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: none);
                CleaveAt(c, AxeTaunt, CleaveArc, CleaveExtra, f);
                About(c, AxeTaunt, $"A great arc of the axe: also hits up to two more enemies in front of you ({f * 100:0}% of the blow)." + (c == Sk ? saga : ""));
                n += Reshape(c, AxeDetaunt, "Biting Edge", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 10, procs: new[] { TailBleed });
                About(c, AxeDetaunt, "A biting cut that leaves a bleed." + (c == Sk ? saga : ""));
            }
            foreach (int c in new[] { Th, Wa, Sk, Be, Sa })
            {
                double f = c == Wa ? HeroCleaveFactor : CleaveFactor;
                n += Reshape(c, HammerTaunt, "Thunderous Sweep", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: new[] { Dazed });
                CleaveAt(c, HammerTaunt, CleaveArc, CleaveExtra, f);
                About(c, HammerTaunt, $"A crushing sweep of the hammer: also hits up to two more enemies in front of you ({f * 100:0}% of the blow), and dazes all it hits (slower attacks)." + (c == Sk ? saga : ""));
                n += Reshape(c, HammerDetaunt, "Ringing Hammer", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 10, procs: new[] { Dent });
                About(c, HammerDetaunt, "A ringing blow that dents its armour: your blows bite a little deeper for 15 seconds." + (c == Sk ? saga : ""));
            }

            // ---- the Warrior: control (its sweeps already hit hardest)
            n += Procs(Wa, 149, new[] { Root3 }); Say(Wa, 149, "roots it for 3 seconds (damage frees it).");
            n += Procs(Wa, 160, new[] { Stun3, Sunder }); Say(Wa, 160, "stuns for 3 seconds and sunders its armour.");
            n += Procs(Wa, 182, new[] { Root6, Sunder }); Say(Wa, 182, "roots it for 6 seconds (damage frees it) and sunders its armour. Stop one running at your healer.");
            n += Procs(Wa, 186, new[] { Stagger }); Say(Wa, 186, "staggers it, breaking the blow it is winding up.");
            n += Procs(Wa, 188, new[] { HeavySnare }); Say(Wa, 188, "pins its leg - a heavy snare that holds through damage.");
            n += Procs(Wa, 166, new[] { Stun3 }); Say(Wa, 166, "stuns for 3 seconds.");
            n += Procs(Wa, 171, new[] { Root6, Sunder }); Say(Wa, 171, "roots it for 6 seconds (damage frees it) and sunders its armour.");
            foreach (int id in new[] { 147, 154, 155, 177, 184, 185, 162, 169, 173 })
                if (Ref(Wa, id) is Style ws)
                {
                    n += AddProcs(Wa, id, new[] { Stagger });
                    About(Wa, id, Opening(ws) + "the blow lands, and staggers it for 2 seconds.");
                }
            foreach (int id in new[] { 156, 158, 159, 187, 189, 190, 172, 174, 175 })
                n += Grow(Wa, id, 0.1);

            // ---- the Thane: Thor's lightning on the chain finishers
            foreach (int id in ThaneBolts)
                if (Ref(Th, id) is Style ts)
                {
                    bool big = System.Array.IndexOf(ThaneBigBolts, id) >= 0;
                    n += AddProcs(Th, id, new[] { big ? ThorBoltBig : ThorBolt });
                    About(Th, id, Opening(ts) + (big ? "Thor's hammer falls on your foe." : "lightning strikes your foe.") +
                        " With a two-handed weapon the bolt arcs to one more enemy beside it.");
                }

            // ---- the Berserker: the Left Axe's off-hand strikes and bleeds (rage - MidgardKits)
            n += AddProcs(Be, 192, new[] { BleedB1 }); Strike(Be, 192); Say(Be, 192, "an open wound, and your off-hand strikes again.");
            n += AddProcs(Be, 201, new[] { GrievousBleed }); Strike(Be, 201); Say(Be, 201, "a grievous bleed, and your off-hand strikes again.");
            foreach (int id in new[] { 199, 204, 205 })
                if (Ref(Be, id) is Style bs)
                {
                    n += AddProcs(Be, id, none);
                    Strike(Be, id);
                    About(Be, id, Opening(bs) + "your off-hand strikes again.");
                }
            n += AddProcs(Be, LeftRavager, none); Self(Be, LeftRavager, HasteSelf); Say(Be, LeftRavager, "your axes quicken for 8 seconds.");
            n += Reshape(Be, LeftTaunt, "Whirling Axes", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 20, procs: none);
            CleaveAt(Be, LeftTaunt, 360, 3, CleaveFactor);
            About(Be, LeftTaunt, "Spin with both axes: also hits up to three more enemies all around you (70% of the blow).");
            foreach (int id in new[] { 149, 160, 182, 188, 166, 171 })
                if (Ref(Be, id) is Style bp)
                {
                    n += AddProcs(Be, id, new[] { BleedB1 });
                    About(Be, id, Opening(bp) + "an open wound that bleeds.");
                }

            // ---- the Savage: Hand to Hand (the blood price - MidgardKits)
            n += Reshape(Sa, HthTaunt, "Savage Sweep", 0, 0, 0, growth: 0.6, hit: 5, def: 0, end: 15, procs: none);
            CleaveAt(Sa, HthTaunt, CleaveArc, CleaveExtra, CleaveFactor);
            About(Sa, HthTaunt, "A raking sweep of the claws: also hits up to two more enemies in front of you (70% of the blow).");
            n += Reshape(Sa, HthDetaunt, "Feral Leap", 0, 0, 0, growth: 0.7, hit: 10, def: 0, end: 12, procs: new[] { Stagger });
            About(Sa, HthDetaunt, "You leap at your foe: it is staggered for 2 seconds.");
            n += Reshape(Sa, HthTaunt2, "Rending Claws", 0, 0, 0, growth: 0.8, hit: 10, def: 0, end: 12, procs: new[] { BleedB2 });
            About(Sa, HthTaunt2, "Claws that rend: a bleed that stacks with your others.");
            n += Reshape(Sa, HthDetaunt2, "Kelgor's Guard", 0, 0, 0, growth: 0.5, hit: 0, def: 15, end: 10, procs: none);
            About(Sa, HthDetaunt2, "A guarded flurry: your defense is raised until your next swing.");
            n += AddProcs(Sa, 373, new[] { BleedB1 }); Say(Sa, 373, "an open wound that bleeds.");
            n += AddProcs(Sa, 382, new[] { HamSnare }); Say(Sa, 382, "snares it for 8 seconds.");
            foreach (int id in new[] { 149, 166, 188 })
                if (Ref(Sa, id) is Style sp1)
                {
                    n += AddProcs(Sa, id, new[] { HamSnare });
                    About(Sa, id, Opening(sp1) + "snares it for 8 seconds.");
                }
            foreach (int id in new[] { 160, 171, 182 })
                if (Ref(Sa, id) is Style sp2)
                {
                    n += AddProcs(Sa, id, new[] { BleedB1 });
                    About(Sa, id, Opening(sp2) + "an open wound that bleeds.");
                }
            foreach (Style hs in SkillBase.GetStyleList(Specs.HandToHand, Sa))
                if (Ref(Sa, hs.ID) is Style h2 && Describe(h2) == null)
                    About(Sa, h2.ID, Opening(h2) + "Blood price: if a Savagery buff is on you, the blow wins back 2% of your health.");

            // ---- the Skald: the positionals daze; every style is Saga
            foreach (int id in new[] { 149, 160, 182, 188, 166, 171 })
                if (Ref(Sk, id) is Style ks)
                {
                    n += AddProcs(Sk, id, new[] { Dazed });
                    About(Sk, id, Opening(ks) + "dazes it - its attacks slow." + saga);
                }
            foreach (string spec in new[] { Specs.Sword, Specs.Axe, Specs.Hammer })
                foreach (Style ks2 in SkillBase.GetStyleList(spec, Sk))
                    if (Ref(Sk, ks2.ID) is Style k3 && Describe(k3) == null)
                        About(Sk, k3.ID, Opening(k3) + "Saga: when it lands you gain a stack (up to 5); at 5 your next shout hits everything in front of you and rallies your group.");

            // ---- the Shadowblade: Marked positionals, Ravager's fade, Garrote
            foreach (int id in ShadowbladeMarks)
                if (Ref(Sb, id) is Style ms)
                {
                    n += AddProcs(Sb, id, new[] { Exposed });
                    About(Sb, id, Opening(ms) + "the blow lands." + marked);
                }
            n += AddProcs(Sb, LeftRavager, none); Self(Sb, LeftRavager, EvadeSelf);
            Say(Sb, LeftRavager, "a feint and a fade: your foe's anger at you falls to a quarter, and your feet grow light (evade up for 6 seconds).");
            n += Reshape(Sb, LeftTaunt, "Shadow Flurry", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 15, procs: none);
            CleaveAt(Sb, LeftTaunt, 90, 1, CleaveFactor);
            About(Sb, LeftTaunt, "Both axes in a narrow flurry: also hits one more enemy just in front of you (70% of the blow).");
            About(Sb, HibernianHybrids.Garrote, "Snares it, and breaks the spell it is casting.");

            // ---- the Hunter: room for the bow
            n += Procs(Hu, 149, new[] { HamSnare }); Say(Hu, 149, "snares it for 8 seconds - step back and draw.");
            n += Procs(Hu, 160, new[] { Root6 }); Say(Hu, 160, "roots it for 6 seconds (damage frees it) - step back and draw.");
            n += Procs(Hu, 214, new[] { HamSnare }); Say(Hu, 214, "snares it for 8 seconds - step back and draw.");
            n += Procs(Hu, 218, new[] { Root6 }); Say(Hu, 218, "roots it for 6 seconds (damage frees it) - step back and draw.");
            n += Reshape(Hu, SpearTaunt, "Sweeping Spear", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: none);
            CleaveAt(Hu, SpearTaunt, 150, CleaveExtra, CleaveFactor, 75);
            About(Hu, SpearTaunt, "A long sweep of the spear: also hits up to two more enemies in a wide arc in front of you, further out than other sweeps (70% of the blow).");
            n += Reshape(Hu, SpearDetaunt, "Leap Away", 0, 0, 0, growth: 0.3, hit: 10, def: 0, end: 10, procs: new[] { Stagger });
            Self(Hu, SpearDetaunt, DisengageRush);
            About(Hu, SpearDetaunt, "A kick and a leap away: staggers it for 2 seconds, you run 50% faster for 4 seconds, and its anger at you halves.");
            return n;
        }
    }
}
