using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;
using DOL.GS.Styles;

namespace DOL.GS
{
    /// <summary>
    /// The Nightshade, the Ranger and the Valewalker (agreed 21 Nov; owner: "Go ahead and build it!"). Their weapon lines'
    /// own versions are in StyleRework (WildLines); what they do beyond the styles is here. Built at start-up, never
    /// written to the database.
    ///
    /// Nightshade - the assassin:
    ///   Ambush           the first blow from stealth can't be parried, blocked or dodged (a stealth opener never could)
    ///   Voidstep         (owner: "for every level of Stealth, they gain 1% chance to vanish on a successful dodge, allowing
    ///                    them to use their stealth opener again. They will stay undetectable for 5 seconds before usual
    ///                    stealth checks apply ... a name that ties into their void magic") - a dodge that slips a blow may
    ///                    step you into the void: hidden, the monsters lose you, nothing finds you for 5 seconds
    ///   Dart of Night    (the instant nuke) doesn't break stealth, and breaks a monster's spell
    ///   Exposed          the Blades / Piercing positionals leave it Exposed for 15 s: a stealth opener on it always crits
    ///   Garrote          also breaks a monster's spell; Fade / the detaunts drop most of its anger at you
    /// Ranger - the skirmisher:
    ///   Forest Shadow    a 60 s reuse, half the duration (a disengage, not a travel buff)
    ///   Camouflage       a shot from stealth from 1000 or more away doesn't reveal you; the monster searches where the
    ///                    arrow came from. Once every 30 s
    ///   Penetrating Arrow critical and overdrawn shots pass on through to 1 / 2 / 3 enemies behind, for half
    ///   Disengage        (Celtic Dual) a stagger, a burst of speed and half your threat gone
    ///   (the Pathfinding damage add already rides on arrows: WeaponAction's damage adds go on every weapon hit)
    /// Valewalker - the reaper:
    ///   Creeping Rot     each scythe style that lands on a foe with your Nature's poison (Nausea .. Bane) on it feeds it:
    ///                    +15% a tick and 4 s longer, up to 5 times (owner: "have the styles amplify the effect of the DoT and
    ///                    extend its duration with a cap of 5")
    ///   Reap             a perfect dodge or parry: your next style casts your life drain on its target - the rank before
    ///                    your best, like a quick cast (owner)
    ///   Nature's Shield  (style) 10 s of arrows and bolts from in front turned aside
    ///   Bitter Harvest   (style) 30% of its damage comes back to you as health
    /// Spell ids 97200-97299; ability ids 3930-3939.
    /// </summary>
    public static class HibernianHybrids
    {
        public const int Nightshade = 49, Ranger = 50, Valewalker = 56, Animist = 55;
        const int ForestShadow = 97220;

        public const int VoidstepHiddenMs = 5000, VoidstepDelayMs = 1;
        public const int ExposedMs = 15000;
        public const int CamoReuseMs = 30000, CamoMinRange = 1000;
        public const int PierceReach = 600, PierceWidth = 120;
        public const double PierceShare = 0.5;
        public const int RotMax = 5, RotExtendMs = 4000;
        public const double RotStep = 0.15;
        public const int ReapWindowMs = 8000, NatureShieldMs = 10000, NatureShieldArc = 120;
        public const double BitterHarvestShare = 0.30;
        public const int DartGroup = 5511, RotGroup = 11209, DrainGroup = 11011;
        public const string DrainLine = "Valewalker Arboreal Path Base";
        public const string VoidstepKey = "Voidstep", AmbushKey = "Ambush", RotKey = "Creeping Rot", ReapKey = "Reap", SproutKey = "Sprouting Ward";
        public const int SproutCooldownMs = 8000, SproutLifeMs = 10000;

        // StyleRework.WildLines' styles that do something here: (class, style id)
        public static readonly HashSet<(int, int)> ExposeStyles = new() { (Nightshade, 249), (Nightshade, 256), (Nightshade, 276), (Nightshade, 283) };
        public static readonly Dictionary<(int, int), int> ThreatKept = new()
        {
            [(Nightshade, 326)] = 25, [(Nightshade, 248)] = 25, [(Nightshade, 279)] = 25,   // Fade, Enervating Blade, Scorpion
            [(Ranger, 326)] = 50,                                                             // Disengage
        };
        public const int Garrote = 342, NaturesShieldStyle = 394, BitterHarvest = 396;

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Register();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[HibernianHybrids] " + ex);
            }
        }

        public static void Register()
        {
            int n = RangerBook();
            int a = AnimistBook();
            Abilities();
            Console.WriteLine($"[HibernianHybrids] Nightshade, Ranger and Valewalker: {n} Forest Shadow ranks reshaped; Animist: {a} spells trimmed");
        }

        // ------------------------------------------------------------------ the books

        static int RangerBook()
        {
            // Forest Shadow (owner: "Much shorter reuse (60 s instead of 10 min) and half the duration")
            var ranks = SkillBase.GetSpellList(Specs.Pathfinding).Where(s => s.Group == 5461).OrderBy(s => s.Level).ToList();
            if (ranks.Count == 0)
                return 0;
            SkillBase.RemoveLineSpells(Specs.Pathfinding, s => s.Group == 5461);
            int i = 0;
            foreach (Spell s in ranks)
            {
                DbSpell d = CloneDb(s, ForestShadow + i++);
                d.RecastDelay = 60;
                d.Duration = Math.Max(5, s.Duration / 2000);
                d.Description = $"Run {s.Value - 100}% faster for {d.Duration} seconds - to break away. 60 second reuse.";
                if (SkillBase.GetSpellByID(d.SpellID) == null)
                    SkillBase.AddScriptedSpell(Specs.Pathfinding, new Spell(d, s.Level));
            }
            return ranks.Count;
        }

        // ---- the Animist's book (owner 2026-11-21: "Go ahead with the trim as you described, and you can keep constraining
        // spirit"): one family a job. Out: the single-target damage bombers (Spirit of Anger .. Hatred - Wisp does it and
        // lowers a resistance, Circle covers groups), the single root bombers (Spreading .. Rampant Vines - Constraining
        // Spirit roots an area), the single melee-debuff turrets (Spore Spewer .. Cannon - Sporespawn pulses it on all around),
        // the turret regeneration (Spirit of Remedy .. Nourishing - Healing Spirit), the long weak group absorb (Essence of the
        // Tree / Forest - Guardian Emissary, Protecting Spirit) and Shield of Wood (Woodspirit Sheath bubbles everyone around).
        // The two resistance vents become one: Vent of Resistance .. Shielding, all six magic resistances.
        const int VentTurret = 97230, VentSub = 97240;

        static int AnimistBook()
        {
            int n = 0;
            n += SkillBase.RemoveLineSpells("Arboreal Mastery", s => s.Group == 11130);
            n += SkillBase.RemoveLineSpells("Creeping Path", s => s.Group == 11334);
            n += SkillBase.RemoveLineSpells("Creeping Path Spec", s => s.Group == 11443);
            n += SkillBase.RemoveLineSpells("Verdant Path Spec", s => s.Group == 11642);
            n += SkillBase.RemoveLineSpells("Verdant Path", s => s.Group is 11509 or 11553);
            var vents = SkillBase.GetSpellList("Verdant Path").Where(s => s.Group == 11545).OrderBy(s => s.Level).ToList();
            if (vents.Count == 0)
                return n;
            n += SkillBase.RemoveLineSpells("Verdant Path", s => s.Group is 11545 or 11549);
            for (int i = 0; i < vents.Count; i++)
            {
                Spell v = vents[i];
                Spell sub = SkillBase.GetSpellByID(v.SubSpellID);
                if (sub == null || SkillBase.GetSpellByID(VentTurret + i) != null)
                    continue;
                DbSpell sd = CloneDb(sub, VentSub + i);
                sd.Type = "AllMagicResistsBuff";
                sd.Name = sub.Name.Replace("Elemental ", "");
                sd.Description = $"Improves resistance to heat, cold, matter, body, spirit and energy by {sub.Value} for all friends within its range.";
                if (SkillBase.GetSpellByID(sd.SpellID) == null)
                    SkillBase.AddScriptedSpell(HibernianKits.KitLine, new Spell(sd, 1));
                DbSpell td = CloneDb(v, VentTurret + i);
                td.SubSpellID = VentSub + i;
                td.Name = v.Name.Replace("Elemental ", "");
                td.Description = $"A turret that, while it stands, raises all six magic resistances by {sub.Value} for every friend within its range.";
                SkillBase.AddScriptedSpell("Verdant Path", new Spell(td, v.Level));
                n--;                                    // (a vent kept, as one)
            }
            return n;
        }

        static DbSpell CloneDb(Spell s, int id) => new DbSpell
        {
            SpellID = id, Name = s.Name, Type = s.SpellType.ToString(), Target = s.Target.ToString(), Range = s.Range, Radius = s.Radius,
            Value = s.Value, Damage = s.Damage, DamageType = (int) s.DamageType, Duration = s.Duration / 1000, Frequency = s.Frequency / 100,
            Pulse = s.Pulse, PulsePower = s.PulsePower, Power = s.Power, CastTime = s.CastTime / 1000.0, RecastDelay = s.RecastDelay / 1000,
            ClientEffect = s.ClientEffect, Icon = s.Icon, SpellGroup = s.Group, EffectGroup = s.EffectGroup, Message1 = s.Message1,
            Message2 = s.Message2, Message3 = s.Message3, Message4 = s.Message4, Description = s.Description,
            SharedTimerGroup = s.SharedTimerGroup, MoveCast = s.MoveCast, Uninterruptible = s.Uninterruptible, SubSpellID = s.SubSpellID,
            Concentration = s.Concentration, InstrumentRequirement = s.InstrumentRequirement,
        };

        static void Abilities()
        {
            var ambush = new DbAbility
            {
                KeyName = AmbushKey, Name = AmbushKey, IconID = 0, InternalID = 3930, AbilityID = 3930,
                Description = "Your first blow from stealth can't be parried, blocked or dodged by a monster.",
            };
            SkillBase.AddScriptedAbility(ambush, "NightshadeCareer", 1);
            var step = new DbAbility
            {
                KeyName = VoidstepKey, Name = VoidstepKey, IconID = 0, InternalID = 3931, AbilityID = 3931,
                Description = "When you dodge a blow, you may step into the void: 1% for each point of Stealth. You slip into stealth, " +
                    "the monsters lose you, and nothing can find you for 5 seconds - open on it again.",
            };
            SkillBase.AddScriptedAbility(step, Specs.Stealth, 1, Nightshade);
            var rot = new DbAbility
            {
                KeyName = RotKey, Name = RotKey, IconID = 0, InternalID = 3932, AbilityID = 3932,
                Description = $"Each scythe style that lands on a foe with your Nature's poison on it feeds the rot: the poison hits " +
                    $"{RotStep * 100:0}% harder and lasts {RotExtendMs / 1000} seconds longer, up to {RotMax} times.",
            };
            SkillBase.AddScriptedAbility(rot, Specs.Arboreal_Path, 1, Valewalker);
            var reap = new DbAbility
            {
                KeyName = ReapKey, Name = ReapKey, IconID = 0, InternalID = 3933, AbilityID = 3933,
                Description = "A perfect dodge or parry: your next style also casts your life drain on its target - the rank before " +
                    "your best, as a quick cast would. (8 seconds to use it.)",
            };
            SkillBase.AddScriptedAbility(reap, "ValewalkerCareer", 2);
            var sprout = new DbAbility
            {
                KeyName = SproutKey, Name = SproutKey, IconID = 0, InternalID = 3934, AbilityID = 3934,
                Description = $"A perfect ward plants a turret at your feet for {SproutLifeMs / 1000} seconds - a tangler if Arboreal Path is your " +
                    $"stronger line, otherwise a sporespawn (or your damage turret before you have either), one rank below your best. Once every " +
                    $"{SproutCooldownMs / 1000} seconds.",
            };
            SkillBase.AddScriptedAbility(sprout, Specs.Creeping_Path, 1, Animist);
            if (SkillBase.GetDbAbility(DOL.GS.Abilities.Camouflage) is DbAbility camo)
                camo.Description = $"A shot from stealth from {CamoMinRange} or more away doesn't give you away: the monster searches where " +
                    $"the arrow came from. Once every {CamoReuseMs / 1000} seconds.";
            if (SkillBase.GetDbAbility(DOL.GS.Abilities.PenetratingArrow) is DbAbility pen)
                pen.Description = "Your critical and overdrawn shots go on through to one more enemy behind your target for each rank, " +
                    "for half the damage.";
        }

        // ------------------------------------------------------------------ state

        sealed class State
        {
            public long HiddenUntil, ExposedUntil, CamoReady, CamoHiddenUntil, ReapUntil, NatureShieldUntil, SproutReady;
        }

        static readonly ConditionalWeakTable<GameLiving, State> _state = new();
        static State Of(GameLiving l) => _state.GetValue(l, _ => new State());
        static bool Has(GameLiving l, out State s) => _state.TryGetValue(l, out s);
        static long Now => GameLoop.GameLoopTime;

        static readonly ConditionalWeakTable<ECSGameEffect, StrongBox<int>> _rot = new();

        static int ClassOf(GameLiving l) => HibernianKits.ClassOf(l);

        static void Say(GameLiving l, string text, eChatType type = eChatType.CT_Spell)
        {
            if (l is GamePlayer p)
                p.Out.SendMessage(text, type, eChatLoc.CL_SystemWindow);
        }

        static void Fx(GameLiving from, GameLiving to, ushort fx)
        {
            foreach (GamePlayer v in to.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(from, to, fx, 0, false, 1);
        }

        // ------------------------------------------------------------------ hooks: a style landed (StyleRework.AfterStyle)

        public static void AfterStyle(GameLiving owner, AttackData ad)
        {
            Style st = ad?.Style;
            if (st == null || ad.Target is not GameLiving t)
                return;
            int cls = ClassOf(owner);
            if (cls != Nightshade && cls != Ranger && cls != Valewalker)
                return;
            var key = (st.ClassID, st.ID);
            if (ExposeStyles.Contains(key))
            {
                Of(t).ExposedUntil = Now + ExposedMs;
                Say(owner, $"{t.GetName(0, true)} is exposed - your next opener on it will find its mark.");
            }
            if (ThreatKept.TryGetValue(key, out int kept))
                DropThreat(owner, t, kept);
            if (cls == Nightshade && st.Spec == Specs.Critical_Strike && st.ID == Garrote)
                BreakSpell(owner, t, "Your garrote");
            if (cls == Valewalker)
            {
                if (st.Spec == Specs.Scythe)
                    FeedRot(owner, t);
                if (st.ID == NaturesShieldStyle && st.Spec == Specs.Scythe)
                {
                    Of(owner).NatureShieldUntil = Now + NatureShieldMs;
                    Say(owner, $"Nature's Shield: arrows and bolts from in front of you are turned aside for {NatureShieldMs / 1000} seconds.");
                }
                if (st.ID == BitterHarvest && st.Spec == Specs.Scythe)
                    HibernianKits.Heal(owner, owner, (int) ((ad.Damage + ad.CriticalDamage) * BitterHarvestShare), 11011, "Bitter Harvest");
                if (Has(owner, out State s) && s.ReapUntil > Now)
                {
                    s.ReapUntil = 0;
                    Reap(owner, t);
                }
            }
        }

        // ------------------------------------------------------------------ hooks: a blow turned aside (AttackComponent)

        public static void AfterDefense(AttackData ad)
        {
            if (ad?.Target is not GameLiving d || ad.Attacker is not GameLiving a || !d.IsAlive)
                return;
            int cls = ClassOf(d);
            if (cls != Nightshade && cls != Valewalker)
                return;
            try
            {
                bool action = d is GamePlayer p && ActionCombat.IsActive(p) && ad.ActionDefense is not eActionDefense.None;
                bool evaded = action ? ad.ActionDefense is eActionDefense.Dodge : ad.AttackResult is eAttackResult.Evaded;
                bool parried = action ? ad.ActionDefense is eActionDefense.Parry : ad.AttackResult is eAttackResult.Parried;
                if (cls == Nightshade && evaded && !d.IsStealthed && Util.Chance((int) Math.Round(VoidstepPercent(d.GetModifiedSpecLevel(Specs.Stealth)))))
                    new ECSGameTimer(d, _ =>
                    {
                        Voidstep(d);
                        return 0;
                    }, VoidstepDelayMs);
                else if (cls == Valewalker && (evaded || parried) && (action ? !ad.ActionAuto : Util.Chance(35)))
                {
                    Of(d).ReapUntil = Now + ReapWindowMs;
                    Say(d, "Reap! Your next style drains life.");
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("[HibernianHybrids] after defense: " + e.Message);
            }
        }

        // ------------------------------------------------------------------ the Nightshade

        /// <summary>The chance (percent) a dodge vanishes you: 1% per level of Stealth, gear's bonus levels included. (2026-11-23:
        /// it went to Util.Chance(double), which reads a 0-1 chance - so any Stealth at all was a certainty.)</summary>
        public static double VoidstepPercent(int stealthSpec) => Math.Clamp(stealthSpec, 0, 100);

        /// <summary>A Nightshade steps into the void: hidden, every monster near loses it, nothing finds it for a while.</summary>
        public static void Voidstep(GameLiving ns, string said = null)
        {
            if (ns == null || !ns.IsAlive || ns.IsStealthed || ns.ObjectState != GameObject.eObjectState.Active)
                return;
            State s = Of(ns);
            s.HiddenUntil = Now + VoidstepHiddenMs;
            ns.Stealth(true);
            if (!ns.IsStealthed)
            {
                s.HiddenUntil = 0;
                return;
            }
            LoseTrack(ns);
            ushort fx = (ushort) (SkillBase.GetSpellByID(5511)?.ClientEffect ?? 5511);
            Fx(ns, ns, fx);
            Say(ns, said ?? "Voidstep! You slip into the void - nothing can find you for a few seconds.", eChatType.CT_Important);
        }

        /// <summary>Every monster after this one gives up the chase (as stealthing and Vanish do).</summary>
        static void LoseTrack(GameLiving l)
        {
            foreach (GameLiving attacker in l.attackComponent.AttackerTracker.Attackers.ToList())
                Forget(attacker, l);
            foreach (GameNPC n in l.GetNPCsInRadius(2000))
                if (n.Brain is IOldAggressiveBrain)
                    Forget(n, l);
        }

        static void Forget(GameLiving who, GameLiving l)
        {
            if (who is GameNPC n && n.Brain is IOldAggressiveBrain brain && n.Brain is not IControlledBrain)
            {
                brain.RemoveFromAggroList(l);
                if (n.TargetObject == l)
                {
                    n.TargetObject = null;
                    n.attackComponent.StopAttack();
                }
            }
        }

        /// <summary>Voidstep's grace: no stealth check finds it, and no blow brings it out.</summary>
        public static bool Undetectable(GameLiving l) => l != null && Has(l, out State s) && s.HiddenUntil > Now;

        /// <summary>A Nightshade's blow from stealth can't be turned aside (AttackComponent: Ambush).</summary>
        public static bool Ambush(AttackData ad) =>
            ad?.Attacker is GameLiving a && ad.Target is GameNPC && a.IsStealthed && ad.IsMeleeAttack && ClassOf(a) is Nightshade or AlbionKits.Infiltrator or MidgardKits.Shadowblade;

        /// <summary>A stealth opener on an Exposed foe always crits.</summary>
        public static int CritChance(AttackData ad, int chance)
        {
            if (ad?.Style == null || !ad.Style.StealthRequirement || ad.Target == null || ClassOf(ad.Attacker) is not (Nightshade or AlbionKits.Infiltrator or MidgardKits.Shadowblade))
                return chance;
            return Has(ad.Target, out State s) && s.ExposedUntil > Now ? 100 : chance;
        }

        public static bool IsExposed(GameLiving t) => t != null && Has(t, out State s) && s.ExposedUntil > Now;

        /// <summary>Exposed for ExposedMs (an Infiltrator's Marked: AlbionKits).</summary>
        public static void Expose(GameLiving t)
        {
            if (t != null)
                Of(t).ExposedUntil = Now + ExposedMs;
        }

        /// <summary>Dart of Night: no stealth lost to throw it (SpellHandler.UnstealthCaster...).</summary>
        public static bool QuietSpell(GameLiving caster, Spell spell) =>
            spell != null && spell.Group == DartGroup && ClassOf(caster) == Nightshade;

        /// <summary>NightshadeNuke: a Dart of Night breaks the spell its target is casting.</summary>
        public static void AfterNightshadeNuke(GameLiving caster, Spell spell, GameLiving target)
        {
            if (spell != null && spell.Group == DartGroup)
                BreakSpell(caster, target, "Your dart");
        }

        public static void BreakSpell(GameLiving by, GameLiving t, string what)
        {
            if (t == null || !t.IsAlive || !t.IsCasting)
                return;
            t.StopCurrentSpellcast();
            Say(by, $"{what} breaks {t.GetName(0, false)}'s spell!");
        }

        /// <summary>Fade / Disengage / the Nightshade's detaunts: the monster keeps only this share of its anger at you.</summary>
        public static void DropThreat(GameLiving owner, GameLiving t, int keptPercent)
        {
            if (t is not GameNPC n || n.Brain is not StandardMobBrain b)
                return;
            long had = b.GetBaseAggroAmount(owner);
            if (had > 0)
                b.AddToAggroList(owner, -(had * (100 - keptPercent) / 100));
        }

        // ------------------------------------------------------------------ the Ranger

        /// <summary>ActionCombat.Loose: a shot from stealth with Camouflage - true when it keeps you hidden (and the monster
        /// is sent searching where it came from once the arrow lands).</summary>
        public static bool CamouflageShot(GamePlayer p, GameLiving target, int flightMs)
        {
            if (p == null || target == null || !p.IsStealthed || !p.HasAbility(DOL.GS.Abilities.Camouflage))
                return false;
            State s = Of(p);
            if (Now < s.CamoReady || p.GetDistanceTo(target) < CamoMinRange)
                return false;
            s.CamoReady = Now + CamoReuseMs;
            s.CamoHiddenUntil = Now + flightMs + 600;
            var from = new Point3D(p.X, p.Y, p.Z);
            new ECSGameTimer(p, _ =>
            {
                if (target is GameNPC n && n.IsAlive && n.Brain is IOldAggressiveBrain && n.Brain is not IControlledBrain)
                {
                    Forget(n, p);
                    n.WalkTo(from, (short) Math.Max((int) n.MaxSpeed, 150));
                    Say(p, $"Your arrow flies unseen - {n.GetName(0, false)} searches for you.");
                }
                return 0;
            }, Math.Max(1, flightMs + 80));
            return true;
        }

        /// <summary>WeaponAction: a camouflaged shot landing doesn't bring you out of stealth.</summary>
        public static bool KeepsHidden(GamePlayer p) => p != null && Has(p, out State s) && s.CamoHiddenUntil > Now;

        /// <summary>Is (nx, ny) on through from the shooter (px, py) past the target (tx, ty) - within reach behind it and
        /// width from the arrow's line?</summary>
        public static bool BehindInLine(double px, double py, double tx, double ty, double nx, double ny, int reach = PierceReach, int width = PierceWidth)
        {
            double dx = tx - px, dy = ty - py, len = Math.Sqrt(dx * dx + dy * dy);
            if (len < 1)
                return false;
            dx /= len;
            dy /= len;
            double vx = nx - tx, vy = ny - ty;
            double along = vx * dx + vy * dy;
            if (along <= 0 || along > reach)
                return false;
            double side = Math.Abs(vx * -dy + vy * dx);
            return side <= width;
        }

        /// <summary>ActionCombat.Loose: Penetrating Arrow - a critical or overdrawn shot goes on through to one more enemy behind
        /// the target for each rank, for half.</summary>
        public static void PierceThrough(GamePlayer p, GameLiving target, DbInventoryItem weapon, double effectiveness, int full,
            eRangedAttackType type, DbInventoryItem ammo, double miss, int flightMs)
        {
            int rank = p.GetAbilityLevel(DOL.GS.Abilities.PenetratingArrow);
            if (rank <= 0 || target == null)
                return;
            var behind = target.GetNPCsInRadius((ushort) PierceReach).Cast<GameNPC>()
                .Where(n => n != target && n.IsAlive && n.ObjectState == GameObject.eObjectState.Active && MonsterTiers.Combatant(n) == null &&
                    GameServer.ServerRules.IsAllowedToAttack(p, n, true) && BehindInLine(p.X, p.Y, target.X, target.Y, n.X, n.Y))
                .OrderBy(n => n.GetDistanceTo(target)).Take(rank).ToList();
            if (behind.Count == 0)
                return;
            new ECSGameTimer(p, _ =>
            {
                foreach (GameNPC n in behind)
                {
                    if (!n.IsAlive || !p.IsAlive)
                        continue;
                    MonsterTiers.Touch(p, n);
                    new WeaponAction(p, n, weapon, effectiveness * PierceShare, full, type, ammo) { ActionMissChance = miss }.Execute();
                }
                Say(p, behind.Count == 1 ? "Your arrow passes on through!" : $"Your arrow passes on through {behind.Count} foes!");
                return 0;
            }, Math.Max(1, flightMs + 120));
        }

        // ------------------------------------------------------------------ the Valewalker

        public static double RotFactor(int stacks) => 1.0 + RotStep * Math.Clamp(stacks, 0, RotMax);

        static ECSGameSpellEffect RotOn(GameLiving caster, GameLiving t) =>
            t?.effectListComponent.GetSpellEffects(eEffect.DamageOverTime)?
                .FirstOrDefault(e => e.IsActive && e.SpellHandler?.Caster == caster && e.SpellHandler.Spell?.Group == RotGroup);

        static void FeedRot(GameLiving vw, GameLiving t)
        {
            ECSGameSpellEffect e = RotOn(vw, t);
            if (e == null)
                return;
            StrongBox<int> box = _rot.GetValue(e, _ => new StrongBox<int>(0));
            if (box.Value >= RotMax)
                return;
            box.Value++;
            if (e.Duration > 0)
                e.ExpireTick += RotExtendMs;
            Say(vw, $"Creeping Rot {box.Value}/{RotMax}: your poison on {t.GetName(0, false)} spreads.");
        }

        /// <summary>DoTSpellHandler: a Valewalker's fed poison hits harder.</summary>
        public static double DotFactor(GameLiving caster, GameLiving t, Spell spell)
        {
            if (spell == null || spell.Group != RotGroup || ClassOf(caster) != Valewalker)
                return 1.0;
            ECSGameSpellEffect e = RotOn(caster, t);
            return e != null && _rot.TryGetValue(e, out StrongBox<int> box) ? RotFactor(box.Value) : 1.0;
        }

        /// <summary>Reap: the life drain the rank before your best (your best when there is none before it).</summary>
        public static Spell ReapSpell(GameLiving vw)
        {
            List<Spell> list = SkillBase.GetSpellList(DrainLine);
            Spell best = list.Where(s => s.Group == DrainGroup && s.Level <= vw.Level).OrderBy(s => s.Level).LastOrDefault();
            if (best == null)
                return null;
            return SpellFamilies.PreviousRank(best, list) ?? best;
        }

        static void Reap(GameLiving vw, GameLiving t)
        {
            Spell sp = ReapSpell(vw);
            SpellLine line = SkillBase.GetSpellLine(DrainLine);
            if (sp == null || line == null || !t.IsAlive)
                return;
            ScriptMgr.CreateSpellHandler(vw, sp, line)?.StartSpell(t);
            Say(vw, $"Reap: {sp.Name} drains {t.GetName(0, false)}!");
        }

        // ------------------------------------------------------------------ the Animist (agreed 21 Nov)

        // the turret families a Sprouting Ward may plant: (line, spell group, spec - null for a baseline line)
        static readonly (string Line, int Group, string Spec)[] SproutFamilies =
        {
            ("Arboreal Mastery", 11146, Specs.Arboreal_Path),          // Tangler Sapling .. Elder Tangler: roots what comes near
            ("Creeping Path Spec", 11436, Specs.Creeping_Path),        // Sporespawn Seedling .. Elder Sporespawn: weaker blows around it
            ("Creeping Path", 11350, null),                            // Forest's Advocate .. Forest's Core: damage
        };

        /// <summary>The turret a Sprouting Ward plants: the stronger of Arboreal Path (a tangler) and Creeping Path (a
        /// sporespawn), else the damage turret; the rank below the best known (the best when there is none below).</summary>
        public static (Spell Spell, SpellLine Line)? SproutTurret(GameLiving a)
        {
            int arb = a.GetModifiedSpecLevel(Specs.Arboreal_Path), creep = a.GetModifiedSpecLevel(Specs.Creeping_Path);
            var order = arb >= creep ? new[] { 0, 1, 2 } : new[] { 1, 0, 2 };
            foreach (int i in order)
            {
                var f = SproutFamilies[i];
                int known = f.Spec == null ? a.Level : a.GetModifiedSpecLevel(f.Spec);
                List<Spell> list = SkillBase.GetSpellList(f.Line);
                Spell best = list.Where(s => s.Group == f.Group && s.Level <= known).OrderBy(s => s.Level).LastOrDefault();
                if (best != null && SkillBase.GetSpellLine(f.Line) is SpellLine line)
                    return (SpellFamilies.PreviousRank(best, list) ?? best, line);
            }
            return null;
        }

        /// <summary>ManaShield.Pay: an Animist's perfect ward plants a turret at its feet for a few seconds.</summary>
        public static void Sprout(GamePlayer p)
        {
            if (p == null || ClassOf(p) != Animist || !p.IsAlive)
                return;
            State s = Of(p);
            if (Now < s.SproutReady)
                return;
            if (DOL.GS.ServerProperties.Properties.TURRET_PLAYER_CAP_COUNT > 0 && p.PetCount >= DOL.GS.ServerProperties.Properties.TURRET_PLAYER_CAP_COUNT)
                return;
            var t = SproutTurret(p);
            if (t == null)
                return;
            s.SproutReady = Now + SproutCooldownMs;
            Spell sp = t.Value.Spell.Copy();
            sp.Duration = SproutLifeMs;
            sp.CastTime = 0;
            GroundTarget gt = p.GroundTarget;
            bool had = gt.IsValid;
            int ox = gt.X, oy = gt.Y, oz = gt.Z;
            bool view = gt.InView;
            try
            {
                gt.Set(p.X, p.Y, p.Z);
                gt.InView = true;
                ScriptMgr.CreateSpellHandler(p, sp, t.Value.Line)?.StartSpell(p);
            }
            finally
            {
                if (had)
                {
                    gt.Set(ox, oy, oz);
                    gt.InView = view;
                }
                else
                    gt.Unset();
            }
            Say(p, $"Your ward takes root - {sp.Name} springs up at your feet!");
        }

        /// <summary>AttackComponent: Nature's Shield turning aside an arrow or a bolt from in front.</summary>
        public static bool NatureShieldBlocks(GameLiving defender, AttackData ad) =>
            ad != null && ad.Attacker != null && (ad.AttackType is AttackData.eAttackType.Ranged or AttackData.eAttackType.Spell) &&
            Has(defender, out State s) && s.NatureShieldUntil > Now && defender.IsObjectInFront(ad.Attacker, NatureShieldArc);
    }
}
