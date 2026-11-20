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
        public const int Hero = 44, Champion = 45;
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
            RageDrain = 30821;

        /// <summary>Cleaving styles: (style id) - for every class that has them.</summary>
        static readonly HashSet<int> Cleaves = new() { Sweep };
        public const int CleaveArc = 120, CleaveExtra = 2;
        public const double CleaveFactor = 0.7, HeroCleaveFactor = 0.9;
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
            }
            Console.WriteLine($"[StyleRework] Large Weapons: {changed} style changes for the Hero and Champion");
        }

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
            st != null && _about.TryGetValue((st.ClassID, st.ID), out string s) && st.Spec == LargeWeapons ? s : null;

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
                if (Cleaves.Contains(st.ID))
                    Cleave(owner, ad, st);
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

        /// <summary>MonsterMoves.Defense: a broken guard blocks half as often.</summary>
        public static double BlockFactor(GameLiving defender) =>
            defender != null && _guardBroken.TryGetValue(defender, out StrongBox<long> until) && until.Value > GameLoop.GameLoopTime ? 0.5 : 1.0;

        /// <summary>The cleave: up to CleaveExtra more enemies in the arc in front of you take a share of the blow (and the
        /// style's procs - a Champion's Submission lands on all of them).</summary>
        static void Cleave(GameLiving owner, AttackData ad, Style st)
        {
            int reach = Math.Max(150, owner.attackComponent.AttackRange) + 50;
            double factor = st.ClassID == Hero ? HeroCleaveFactor : CleaveFactor;
            int dmg = Math.Max(1, (int) ((ad.Damage + ad.CriticalDamage) * factor));
            var hit = new List<GameLiving>();
            foreach (GameNPC n in owner.GetNPCsInRadius((ushort) reach))
            {
                if (hit.Count >= CleaveExtra)
                    break;
                if (n == ad.Target || !n.IsAlive || n.ObjectState != GameObject.eObjectState.Active || !owner.IsObjectInFront(n, CleaveArc))
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
