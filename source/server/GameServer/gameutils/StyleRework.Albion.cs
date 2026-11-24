using System.Collections.Generic;
using DOL.Database;
using DOL.GS.Styles;

namespace DOL.GS
{
    /// <summary>
    /// Albion's weapon lines' class versions (owner 2026-11-24, "Albion Class Rework - the plan": "Go ahead and knock out all
    /// Albion classes"). The same rules as Hibernia's: every class's styles are its own rows; the same styles at the same
    /// levels and openings for everyone; what a style does when it lands is the class's. Taunt and detaunt slots become a
    /// cleave and a new style (taunts are shouts now - TauntShouts).
    ///   Armsman   (the Hero's counterpart) control by reach and armour: roots, deep snares, sunder, stagger; Two Handed
    ///             hits heaviest; Polearm's Brace stops what charges in front, its sweep reaches further.
    ///   Mercenary (the Blademaster's) off-hand strikes and stacking bleeds, and dirty fighting: blind, weaken, kick.
    ///   Paladin   (the Champion's) holy blasts on the chain finishers; its positionals and reactives surge its chants
    ///             (AlbionKits).
    ///   Reaver    (the Valewalker's) the positionals siphon life; every Flexible style that lands tethers (AlbionKits);
    ///             the whip's sweep reaches furthest; Binding Lash.
    ///   Friar     the staff's sweep and a guarded blow; every Staff style heals the group (Sermon - AlbionKits).
    ///   Minstrel  the positionals daze and snare; every style that lands is Tempo (AlbionKits).
    ///   Scout     the positionals root and snare to make room for the bow; Fall Back.
    ///   Infiltrator the positionals leave it Marked (a stealth opener on it always crits); the detaunts drop threat.
    /// Proc spells: ids 30900-30949, hidden line "Style Rework Effects".
    /// </summary>
    public static partial class StyleRework
    {
        public const int Blinded = 30900, Weakened = 30901, HolyBlast = 30902, HolyBlastBig = 30903, BraceRoot = 30904, SoulSiphon = 30905;

        // Albion's style ids (the same in every class's rows)
        public const int SlashTaunt = 59, SlashDetaunt = 61, CrushTaunt = 74, CrushDetaunt = 79, ThrustTaunt = 134, ThrustDetaunt = 138,
            PoleTaunt = 91, PoleDetaunt = 88, TwoTaunt = 103, TwoDetaunt = 104, DualTaunt = 119, DualDetaunt = 123,
            FlexTaunt = 357, FlexDetaunt = 363, StaffTaunt = 240, StaffDetaunt = 235, StaffOpener = 230;

        /// <summary>The Infiltrator's positionals that leave it Marked (HibernianHybrids' Exposed: a stealth opener always crits).</summary>
        public static readonly int[] InfiltratorMarks = { 57, 64, 68, 141, 143, 118, 126, 338 };

        static int AlbionLines()
        {
            Hidden(Db(Blinded, "Blinded", "ToHitDebuff", value: 20, duration: 8, effect: 2140, icon: 2140, msg1: "Grit in your eyes - you can barely see!"));
            Hidden(Db(Weakened, "Weakened", "MeleeDamageDebuff", value: 15, duration: 10, effect: 5401, icon: 5401, msg1: "A cheap blow saps your strength!"));
            Hidden(Db(HolyBlast, "Holy Blast", "DirectDamage", damage: 45, damageType: (int) eDamageType.Spirit, effect: 1671, msg1: "Holy light sears you!"));
            Hidden(Db(HolyBlastBig, "Holy Smite", "DirectDamage", damage: 100, damageType: (int) eDamageType.Spirit, effect: 1677, msg1: "Holy light sears you!"));
            Hidden(Db(BraceRoot, "Braced", "SpeedDecrease", value: 99, duration: 2, effect: 11310, icon: 11361, msg1: "You run onto the braced polearm!"));
            var siphon = Db(SoulSiphon, "Soul Siphon", "Lifedrain", value: -70, damage: 20, damageType: (int) eDamageType.Spirit, effect: 9611,
                msg1: "Your life is drawn out of you!");
            siphon.LifeDrainReturn = 70;
            Hidden(siphon);

            const int P = AlbionKits.Paladin, A = AlbionKits.Armsman, Sc = AlbionKits.Scout, Mi = AlbionKits.Minstrel,
                I = AlbionKits.Infiltrator, F = AlbionKits.Friar, Me = AlbionKits.Mercenary, R = AlbionKits.Reaver;
            int[] none = new int[0];
            int n = 0;
            string surge = " A Paladin's positional or reactive style that lands also surges its chants (both pulse at once).";
            string tempo = " Tempo: a stack when it lands.";
            string marked = " It is left Marked for 15 seconds: a stealth opener on it always crits.";

            // ---- the taunt and detaunt slots: a cleave and a new style, every class with the line
            foreach (int c in new[] { P, A, Sc, Mi, I, Me, R })
            {
                n += Reshape(c, SlashTaunt, "Sweeping Slash", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: none);
                CleaveAt(c, SlashTaunt, CleaveArc, CleaveExtra, c == A ? HeroCleaveFactor : CleaveFactor);
                About(c, SlashTaunt, $"A wide slash: also hits up to two more enemies in front of you ({(c == A ? 90 : 70)}% of the blow)." + (c == Mi ? tempo : ""));
                n += Reshape(c, ThrustTaunt, "Flurry of Thrusts", 0, 0, 0, growth: 0.5, hit: 10, def: 0, end: 15, procs: new[] { SmallBleed });
                CleaveAt(c, ThrustTaunt, CleaveArc, CleaveExtra, c == A ? HeroCleaveFactor : CleaveFactor);
                About(c, ThrustTaunt, $"A flurry of thrusts: also hits up to two more enemies in front of you ({(c == A ? 90 : 70)}% of the blow), and each of them bleeds." + (c == Mi ? tempo : ""));
            }
            foreach (int c in new[] { P, A, Sc, Mi, R })
            {
                n += Reshape(c, SlashDetaunt, "Steady Cut", 0, 0, 0, growth: 0.45, hit: 0, def: 15, end: 10, procs: none);
                About(c, SlashDetaunt, "A careful cut: your defense is raised until your next swing." + (c == Mi ? tempo : ""));
            }
            foreach (int c in new[] { P, A, Mi, Me, R })
            {
                n += Reshape(c, ThrustDetaunt, "Needle Thrust", 2, 1, 0, growth: 0.6, hit: 10, def: 0, end: 10, procs: new[] { TailBleed });
                About(c, ThrustDetaunt, "From the side: a needling thrust that leaves a bleed." + (c == Mi ? tempo : ""));
            }
            foreach (int c in new[] { P, A, Me, R })
            {
                n += Reshape(c, CrushTaunt, "Crushing Sweep", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 15, procs: new[] { Dazed });
                CleaveAt(c, CrushTaunt, CleaveArc, CleaveExtra, c == A ? HeroCleaveFactor : CleaveFactor);
                About(c, CrushTaunt, $"A crushing sweep: also hits up to two more enemies in front of you ({(c == A ? 90 : 70)}% of the blow), and dazes all it hits (slower attacks).");
                n += Reshape(c, CrushDetaunt, "Ringing Blow", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 10, procs: new[] { Dent });
                About(c, CrushDetaunt, "A ringing blow that dents its armour: your blows bite a little deeper for 15 seconds.");
            }
            foreach (int c in new[] { P, A })
            {
                n += Reshape(c, TwoTaunt, "Great Sweep", 0, 0, 0, growth: 0.6, hit: 5, def: 0, end: 15, procs: none);
                CleaveAt(c, TwoTaunt, CleaveArc, CleaveExtra, c == A ? HeroCleaveFactor : CleaveFactor);
                About(c, TwoTaunt, $"A great two-handed sweep: also hits up to two more enemies in front of you ({(c == A ? 90 : 70)}% of the blow).");
                n += Reshape(c, TwoDetaunt, "Sundering Blow", 0, 0, 0, growth: 0.55, hit: 5, def: 0, end: 12, procs: new[] { c == A ? Sunder : Dent });
                About(c, TwoDetaunt, c == A ? "A blow that sunders its armour: your blows bite deeper for 20 seconds." :
                    "A ringing blow that dents its armour: your blows bite a little deeper for 15 seconds.");
            }

            // ---- the Infiltrator: the detaunts drop threat, the positionals Mark
            n += Reshape(I, SlashDetaunt, "Slipping Cut", 0, 0, 0, growth: 0.45, hit: 5, def: 10, end: 10, procs: none);
            About(I, SlashDetaunt, "A slipping cut: your foe's anger at you falls to a quarter.");
            n += Reshape(I, ThrustDetaunt, "Quick Sting", 0, 0, 0, growth: 0.45, hit: 10, def: 0, end: 10, procs: none);
            About(I, ThrustDetaunt, "A quick sting and a step away: your foe's anger at you falls to a quarter.");
            n += Reshape(I, DualTaunt, "Shadow Flurry", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 15, procs: none);
            CleaveAt(I, DualTaunt, 90, 1, CleaveFactor);
            About(I, DualTaunt, "Both blades in a narrow flurry: also hits one more enemy just in front of you (70% of the blow).");
            n += Reshape(I, DualDetaunt, "Fade", 0, 0, 0, growth: 0.3, hit: 10, def: 10, end: 10, procs: none);
            Self(I, DualDetaunt, EvadeSelf);
            About(I, DualDetaunt, "A feint and a fade: your foe's anger at you falls to a quarter, and your feet grow light (evade up for 6 seconds).");
            foreach (int id in InfiltratorMarks)
                if (Ref(I, id) is Style ms)
                {
                    n += AddProcs(I, id, new[] { Exposed });
                    About(I, id, Opening(ms) + "the blow lands." + marked);
                }
            About(I, 342, "Snares it, and breaks the spell it is casting.");

            // ---- the Armsman: control by reach and armour
            n += Procs(A, 57, new[] { Root3 }); Say(A, 57, "roots it for 3 seconds (damage frees it).");
            n += Procs(A, 64, new[] { HeavySnare }); Say(A, 64, "pins its leg - a heavy snare that holds through damage.");
            n += Procs(A, 68, new[] { Root6, Sunder }); Say(A, 68, "roots it for 6 seconds (damage frees it) and sunders its armour. Stop one running at your healer.");
            n += AddProcs(A, 63, new[] { Stagger }); Say(A, 63, "staggers it for 2 seconds.");
            n += Procs(A, 72, new[] { Stun3 }); Say(A, 72, "stuns for 3 seconds.");
            n += Procs(A, 80, new[] { Root6, Sunder }); Say(A, 80, "roots it for 6 seconds (damage frees it) and sunders its armour.");
            n += Procs(A, 82, new[] { Stun3 }); Say(A, 82, "stuns for 3 seconds.");
            n += Procs(A, 141, new[] { Root6 }); Say(A, 141, "roots it for 6 seconds (damage frees it).");
            n += Procs(A, 143, new[] { HeavySnare }); Say(A, 143, "pins its leg - a heavy snare that holds through damage.");
            n += Procs(A, 87, new[] { Root3 }); Say(A, 87, "roots it for 3 seconds (damage frees it).");
            n += Procs(A, 95, new[] { HeavySnare, Sunder }); Say(A, 95, "pins its leg and sunders its armour.");
            n += AddProcs(A, 100, new[] { Sunder }); Say(A, 100, "a long snare, and its armour is sundered.");
            foreach (int id in new[] { 92, 94, 96, 98, 99 })
                n += Grow(A, id, 0.1);
            n += Reshape(A, PoleTaunt, "Sweeping Halberd", 0, 0, 0, growth: 0.6, hit: 5, def: 0, end: 15, procs: none);
            CleaveAt(A, PoleTaunt, 150, CleaveExtra, HeroCleaveFactor, 75);
            About(A, PoleTaunt, "A long sweep of the polearm: also hits up to two more enemies in a wide arc in front of you, further out than other sweeps (90% of the blow).");
            n += Reshape(A, PoleDetaunt, "Brace", 2, 2, 0, growth: 0.5, hit: 10, def: 10, end: 10, procs: new[] { Stagger, BraceRoot });
            About(A, PoleDetaunt, "From the front: set the polearm - what runs onto it is staggered and held for 2 seconds.");
            n += Procs(A, 102, new[] { Stun3 }); Say(A, 102, "stuns for 3 seconds.");
            n += Procs(A, 107, new[] { Root3 }); Say(A, 107, "roots it for 3 seconds (damage frees it).");
            n += Procs(A, 113, new[] { Root6, Sunder }); Say(A, 113, "roots it for 6 seconds (damage frees it) and sunders its armour.");
            foreach (int id in new[] { 105, 109, 111, 114, 115 })
                n += Grow(A, id, 0.15);

            // ---- the Paladin: holy blasts on the chain finishers (its chants surge from AlbionKits)
            foreach (int id in new[] { 69, 70, 84, 85, 142, 145, 114, 115 })
                if (Ref(P, id) is Style ps)
                {
                    n += AddProcs(P, id, new[] { id is 70 or 85 or 115 ? HolyBlastBig : HolyBlast });
                    About(P, id, Opening(ps) + (id is 70 or 85 or 115 ? "a Holy Smite sears your foe." : "a Holy Blast sears your foe.") + surge);
                }
            foreach (int c in new[] { 57, 64, 68, 63, 72, 80, 82, 76, 81, 132, 137, 140, 141, 143, 102, 107, 108, 113 })
                if (Ref(P, c) is Style ps2 && Describe(ps2) == null)
                    About(P, c, Opening(ps2) + "the blow lands." + surge);

            // ---- the Mercenary: off-hand strikes, stacking bleeds, dirty fighting
            n += Procs(Me, 57, new[] { Weakened }); Say(Me, 57, "a cheap blow - it hits 15% softer for 10 seconds.");
            n += AddProcs(Me, 64, none); Strike(Me, 64); Say(Me, 64, "your off-hand strikes again.");
            n += Procs(Me, 68, new[] { Blinded, BleedB1 }); Say(Me, 68, "dirt in its eyes (it misses more for 8 seconds) and an open wound.");
            Strike(Me, 69); Strike(Me, 70); Say(Me, 69, "your off-hand strikes again."); Say(Me, 70, "your off-hand strikes again.");
            n += AddProcs(Me, 72, none); Strike(Me, 72); Say(Me, 72, "stuns for 2 seconds, and your off-hand strikes again.");
            n += Procs(Me, 80, new[] { Blinded }); Say(Me, 80, "dirt in its eyes - it misses more for 8 seconds.");
            n += Procs(Me, 82, new[] { Weakened }); Say(Me, 82, "a cheap blow - it hits 15% softer for 10 seconds.");
            Strike(Me, 85); Say(Me, 85, "your off-hand strikes again.");
            n += Procs(Me, 141, new[] { Blinded, BleedB1 }); Say(Me, 141, "dirt in its eyes (it misses more) and an open wound.");
            n += Procs(Me, 143, new[] { Weakened }); Say(Me, 143, "a cheap blow - it hits 15% softer for 10 seconds.");
            Strike(Me, 142); Strike(Me, 145); Say(Me, 142, "a bleed, and your off-hand strikes again."); Say(Me, 145, "a stun, and your off-hand strikes again.");
            n += Reshape(Me, SlashDetaunt, "Cheap Shot", 0, 0, 0, growth: 0.4, hit: 10, def: 0, end: 10, procs: new[] { Blinded, Weakened });
            About(Me, SlashDetaunt, "A kick and a fistful of dirt: it misses more and hits softer for a few seconds.");
            n += Procs(Me, 118, new[] { Blinded, BleedB1 }); Say(Me, 118, "dirt in its eyes (it misses more) and an open wound.");
            n += Procs(Me, 126, new[] { Weakened }); Say(Me, 126, "a cheap blow - it hits 15% softer for 10 seconds.");
            n += AddProcs(Me, 117, new[] { Stagger }); Say(Me, 117, "a kick that staggers it, and a bleed.");
            foreach (int id in new[] { 124, 128, 129 })
            {
                n += AddProcs(Me, id, none);
                Strike(Me, id);
                if (Ref(Me, id) is Style ds)
                    About(Me, id, Opening(ds) + "your off-hand strikes again.");
            }
            n += AddProcs(Me, 130, new[] { BleedB2 }); Strike(Me, 130); Say(Me, 130, "a second wound bleeds with the first, and your off-hand strikes again.");
            n += Reshape(Me, DualTaunt, "Whirling Blades", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 20, procs: none);
            CleaveAt(Me, DualTaunt, 360, 3, CleaveFactor);
            About(Me, DualTaunt, "Spin with both blades: also hits up to three more enemies all around you (70% of the blow).");
            n += Reshape(Me, DualDetaunt, "Gutter Kick", 0, 0, 0, growth: 0.4, hit: 10, def: 0, end: 10, procs: new[] { Blinded, Weakened });
            About(Me, DualDetaunt, "A kick and a fistful of dirt: it misses more and hits softer for a few seconds.");

            // ---- the Reaver: the positionals siphon life; Flexible
            foreach (int id in new[] { 57, 64, 68, 72, 80, 82, 141, 143 })
                if (Ref(R, id) is Style rs)
                {
                    n += AddProcs(R, id, new[] { SoulSiphon });
                    About(R, id, Opening(rs) + "a Soul Siphon draws its life into you.");
                }
            n += Reshape(R, FlexTaunt, "Lash", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 15, procs: none);
            CleaveAt(R, FlexTaunt, 150, CleaveExtra, CleaveFactor, 100);
            About(R, FlexTaunt, "A long lash of the flail: also hits up to two more enemies in a wide arc in front of you, further out than any other sweep (70% of the blow). It tethers its target.");
            n += Reshape(R, FlexDetaunt, "Binding Lash", 0, 0, 0, growth: 0.5, hit: 10, def: 0, end: 12, procs: new[] { HeavySnare });
            About(R, FlexDetaunt, "The chain wraps its legs: a heavy snare that holds through damage. It tethers its target.");
            foreach (Style fs in SkillBase.GetStyleList(Specs.Flexible, R))
                if (Ref(R, fs.ID) is Style f2 && Describe(f2) == null)
                    About(R, f2.ID, Opening(f2) + "Soul Tether: for 10 seconds a tenth of all your damage comes back to you as health, and it is snared if it runs from you.");

            // ---- the Friar: the staff's sweep and a guarded blow (Sermon of the Staff heals on every one - AlbionKits)
            string sermon = " Sermon of the Staff: your group around you is healed (more the closer they stand).";
            n += Reshape(F, StaffTaunt, "Spinning Sweep", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 20, procs: none);
            CleaveAt(F, StaffTaunt, 360, 3, CleaveFactor);
            About(F, StaffTaunt, "The staff spins all round you: also hits up to three more enemies (70% of the blow)." + sermon);
            n += Reshape(F, StaffDetaunt, "Guarded Staff", 0, 0, 0, growth: 0.45, hit: 0, def: 15, end: 10, procs: none);
            About(F, StaffDetaunt, "A guarded blow: your defense is raised until your next swing." + sermon);
            n += Reshape(F, StaffOpener, "Spinning Staff", 0, 0, 0, growth: 0.5, hit: 5, def: 0, end: 8, procs: none);
            About(F, StaffOpener, "A quick spin of the staff: more than a plain swing, for a little endurance." + sermon);
            foreach (Style fs in SkillBase.GetStyleList(Specs.Staff, F))
                if (Ref(F, fs.ID) is Style f3 && Describe(f3) == null)
                    About(F, f3.ID, "Sermon of the Staff: when it lands your group around you is healed (more the closer they stand).");

            // ---- the Minstrel: the positionals daze and snare (Tempo - AlbionKits)
            n += AddProcs(Mi, 57, new[] { Dazed }); Say(Mi, 57, "dazes it - its attacks slow." + tempo);
            n += AddProcs(Mi, 64, new[] { Dazed }); Say(Mi, 64, "snares and dazes it." + tempo);
            n += Procs(Mi, 68, new[] { HamSnare, Dazed }); Say(Mi, 68, "snares and dazes it." + tempo);
            n += Procs(Mi, 141, new[] { HamSnare, Dazed }); Say(Mi, 141, "snares and dazes it." + tempo);
            n += AddProcs(Mi, 143, new[] { Dazed }); Say(Mi, 143, "slows its attacks further." + tempo);
            foreach (string spec in new[] { Specs.Slash, Specs.Thrust })
                foreach (Style ms in SkillBase.GetStyleList(spec, Mi))
                    if (Ref(Mi, ms.ID) is Style m2 && Describe(m2) == null)
                        About(Mi, m2.ID, "Tempo: when it lands you gain a stack (up to 5); at 5 your next mesmerize or stun is instant and can't be resisted.");

            // ---- the Scout: room for the bow
            n += Procs(Sc, 57, new[] { HamSnare }); Say(Sc, 57, "snares it for 8 seconds - step back and draw.");
            n += Procs(Sc, 64, new[] { HamSnare }); Say(Sc, 64, "snares it for 8 seconds - step back and draw.");
            n += Procs(Sc, 68, new[] { Root6 }); Say(Sc, 68, "roots it for 6 seconds (damage frees it) - step back and draw.");
            n += Procs(Sc, 141, new[] { Root6 }); Say(Sc, 141, "roots it for 6 seconds (damage frees it) - step back and draw.");
            n += Procs(Sc, 143, new[] { HamSnare }); Say(Sc, 143, "snares it for 8 seconds - step back and draw.");
            n += Reshape(Sc, ThrustDetaunt, "Fall Back", 0, 0, 0, growth: 0.3, hit: 10, def: 0, end: 10, procs: new[] { Stagger });
            Self(Sc, ThrustDetaunt, DisengageRush);
            About(Sc, ThrustDetaunt, "A kick and a leap away: staggers it for 2 seconds, you run 50% faster for 4 seconds, and its anger at you halves.");
            return n;
        }

        /// <summary>The tooltip's opening words for a style: "From behind: ", "After you parry: ", "After Cross Slash: "...</summary>
        static string Opening(Style st)
        {
            DbStyle d = st.Db;
            switch (d.OpeningRequirementType)
            {
                case 2:
                    return d.OpeningRequirementValue switch { 0 => "From behind: ", 1 => "From the side: ", _ => "From the front: " };
                case 1:
                    return d.AttackResultRequirement switch { 3 => "After you parry: ", 4 => "After you block: ", 5 => "After you evade: ", _ => "" };
                default:
                    if (d.OpeningRequirementValue > 0 && d.AttackResultRequirement == 7 && SkillBase.GetStyleRef(d.OpeningRequirementValue, st.ClassID) is Style prev)
                        return $"After {prev.Name}: ";
                    return d.AttackResultRequirement switch { 3 => "After it parries you: ", 4 => "After it blocks you: ", 5 => "After it evades you: ", _ => "" };
            }
        }

        static void Say(int cls, int id, string what)
        {
            if (Ref(cls, id) is Style st)
            {
                string o = Opening(st);
                About(cls, id, o == "" ? char.ToUpper(what[0]) + what.Substring(1) : o + what);
            }
        }
    }
}
