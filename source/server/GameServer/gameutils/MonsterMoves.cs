using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using DOL.AI.Brain;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS
{
    /// <summary>
    /// How monsters fight (owner 2026-11-19, "Purposeful PvE", steps 2 and 3): endurance as poise for everyone, and
    /// monsters using DAoC's own kinds of moves, more of them the higher their con (gameutils/MonsterTiers.cs).
    ///
    /// Endurance is the poise. Styles cost it, a missed defence press costs it (ActionCombat), a monster's guard that
    /// fails costs it; a successful block, parry or evade gives some back. Run low and the defences weaken (Defense),
    /// styles and specials stop (a monster's Pick), sprint stops (the engine). Monsters keep their own stamina here (0 -
    /// 100, it comes back by itself); players and bots use their real endurance. No stun from it.
    ///
    /// The ladder (owner's example), for humanoids with weapons:
    ///   green   an anytime style, a bit faster and harder than a plain blow; a positional when it is at your side or back
    ///   blue    + one reactive defence by its gear: a shield blocks, otherwise it parries; a guard stance (it holds its
    ///           weapon or shield up - attacking into it is mostly turned aside, and it answers with a counter)
    ///   yellow  + evades; a small frontal cone (strafe out of it)
    ///   orange  + chains: a style that lands is followed by another
    ///   red     the same, more often; purple + a ground slam (the only big circles)
    /// Beasts (no weapon): a heavy, slower blow (its own weightier ring), bites that carry DAoC's procs - poison,
    /// disease, bleeding, a snare - and from yellow the same small cone.
    /// Telegraphs go to action-mode players as "#AC|..." lines; bots and pets read them as well as they can (ReadChance).
    /// </summary>
    public static class MonsterMoves
    {
        public enum Blow : byte { Normal, Style, Chain, Counter, Heavy, Cone, Slam }
        public enum Def : byte { Evade, Parry, Block }

        public const int NormalMs = 600, StyleMs = 450, ChainMs = 400, CounterMs = 380, HeavyMs = 1100, ConeMs = 900, SlamMs = 1700;
        public const int SlamRadius = 350, ConeRadius = 320, ConeArc = 100;
        // (owner 2026-11-19 playtest: too much damage - a level 9's 141 health took 63 from a green's blow)
        public const double StyleFactor = 1.3, PositionalFactor = 1.5, ChainFactor = 1.35, CounterFactor = 1.3,
            HeavyFactor = 1.6, ConeFactor = 1.15, SlamFactor = 1.5;
        // (owner 2026-11-19: "Endurance costs for mobs need to be much higher ... If they get parried or evaded or
        // blocked, whatever they were trying to do should have a much bigger endurance cost, let's start with 3 times.
        // successfully blocking parrying or evading the player will restore as much ... Missed parry blocks or evades
        // also cost them.")
        public const double PlainCost = 4, StyleCost = 14, ChainCost = 10, CounterCost = 8, HeavyCost = 16, ConeCost = 20,
            DefendedTimes = 3, DefendGain = 12, MissedDefenseCost = 4, GuardFailCost = 24, RegenPerSecond = 4, LowStamina = 25;

        public static double CostOf(Blow b) => b switch
        {
            Blow.Style => StyleCost, Blow.Chain => ChainCost, Blow.Counter => CounterCost,
            Blow.Heavy => HeavyCost, Blow.Cone => ConeCost, Blow.Slam => 0, _ => PlainCost
        };

        public sealed class State
        {
            public Blow Pending;
            public Blow Last;
            public bool Positional;
            public bool ChainNext;
            public bool CounterNext;
            public long NextSlamAt;
            public long NextConeAt;
            public ushort ConeHeading;
            public double Stamina = 100;
            public long StaminaAt;
            public long HitAt;                 // when a foe last swung at it
            public long GuardUntil;
            public long NextGuardAt;
            public Def GuardKind;
            public bool TargetReacts;          // a bot / pet target saw this blow coming (rolled as it winds up)
        }

        static readonly ConditionalWeakTable<GameNPC, State> _states = new();
        static int _notes;

        /// <summary>A line in the server log for the first few hundred moves of a run (to check them in a probe).</summary>
        static void Note(GameNPC n, string what)
        {
            if (System.Threading.Interlocked.Increment(ref _notes) <= 300)
                Console.WriteLine($"[MonsterMoves] {n.Name} ({n.ObjectID}): {what}");
        }

        public static State Of(GameNPC n) => _states.GetValue(n, _ => new State { StaminaAt = GameLoop.GameLoopTime });

        /// <summary>A monster's competence: 0 green .. 5 purple; -1 untiered, grey, a bot or a pet.</summary>
        public static int Comp(GameLiving l)
        {
            if (l is not GameNPC n || n is GameBot)
                return -1;
            sbyte t = MonsterTiers.Tier(n);
            return t == MonsterTiers.None || t < MonsterTiers.Green ? -1 : t - MonsterTiers.Green;
        }

        /// <summary>Fights with a weapon: a humanoid body, or anything holding a weapon.</summary>
        public static bool Humanoid(GameNPC n) =>
            n.BodyType == (ushort) NpcTemplateMgr.eBodyType.Humanoid || n.BodyType == (ushort) NpcTemplateMgr.eBodyType.Giant ||
            n.Inventory?.GetItem(eInventorySlot.RightHandWeapon) != null || n.Inventory?.GetItem(eInventorySlot.TwoHandWeapon) != null;

        public static bool Shield(GameNPC n) =>
            n.LeftHandSwingChance == 0 && n.ActiveWeaponSlot == eActiveWeaponSlot.Standard &&
            n.Inventory?.GetItem(eInventorySlot.LeftHandWeapon) != null;

        // ------------------------------------------------------------------ stamina

        public static double Stamina(GameNPC n) => Stamina(Of(n), GameLoop.GameLoopTime);

        static double Stamina(State s, long now)
        {
            if (now > s.StaminaAt)
            {
                s.Stamina = Math.Min(100, s.Stamina + (now - s.StaminaAt) / 1000.0 * RegenPerSecond);
                s.StaminaAt = now;
            }
            return s.Stamina;
        }

        static void Spend(State s, double amount) => s.Stamina = Math.Max(0, Stamina(s, GameLoop.GameLoopTime) - amount);
        static void Gain(State s, double amount) => s.Stamina = Math.Min(100, Stamina(s, GameLoop.GameLoopTime) + amount);

        /// <summary>Endurance (or a monster's stamina) left, in percent; 100 for those it doesn't apply to.</summary>
        public static double EndurancePct(GameLiving l)
        {
            if (l is GamePlayer or GameBot)
                return l.MaxEndurance > 0 ? l.Endurance * 100.0 / l.MaxEndurance : 100;
            return Comp(l) >= 0 ? Stamina((GameNPC) l) : 100;
        }

        /// <summary>Tired defences: whole above half endurance, down to 35% of themselves at none.</summary>
        public static double DefenseFactor(GameLiving l) => TiredFactor(EndurancePct(l));

        public static double TiredFactor(double pct) => pct >= 50 ? 1.0 : 0.35 + 0.65 * Math.Max(0, pct) / 50.0;

        // ------------------------------------------------------------------ defences

        /// <summary>A passive evade / parry / block chance (0..1) as the defender's endurance and, for a tiered
        /// monster, its competence and guard make it.</summary>
        public static double Defense(GameLiving owner, AttackData ad, Def kind, double chance)
        {
            if (owner == null)
                return chance;
            int c = Comp(owner);
            if (c >= 0 && ad?.Attacker != null && owner.IsObjectInFront(ad.Attacker, 120) && !owner.IsCrowdControlled && !owner.IsCasting)
            {
                GameNPC n = (GameNPC) owner;
                bool hum = Humanoid(n), shield = Shield(n);
                double tc = kind switch
                {
                    Def.Block when shield && c >= 1 => 0.08 + 0.03 * c,
                    Def.Parry when hum && !shield && c >= 1 && ad.IsMeleeAttack => 0.08 + 0.03 * c,
                    Def.Evade when hum && c >= 2 => 0.04 + 0.025 * c,
                    _ => 0
                };
                State s = Of(n);
                if (s.GuardUntil > GameLoop.GameLoopTime && s.GuardKind == kind && (kind != Def.Parry || ad.IsMeleeAttack))
                    tc = Math.Max(tc, 0.55 + 0.05 * c);
                if (ad.AttackType == AttackData.eAttackType.Ranged && kind != Def.Block)
                    tc /= 3;
                chance = Math.Max(chance, tc);
            }
            return chance * DefenseFactor(owner);
        }

        // ------------------------------------------------------------------ guard stance

        public static bool Guarding(GameNPC n) =>
            _states.TryGetValue(n, out State s) && s.GuardUntil > GameLoop.GameLoopTime;

        public static long GuardLeft(GameNPC n) =>
            _states.TryGetValue(n, out State s) ? Math.Max(0, s.GuardUntil - GameLoop.GameLoopTime) : 0;

        /// <summary>Between blows, a blue-and-up humanoid under attack may raise its guard instead (baiting): ms, or 0.</summary>
        public static int TryGuard(GameNPC n)
        {
            int c = Comp(n);
            if (c < 1 || !Humanoid(n))
                return 0;
            State s = Of(n);
            long now = GameLoop.GameLoopTime;
            if (now < s.NextGuardAt || now - s.HitAt > 3000 || Stamina(s, now) < LowStamina)
                return 0;
            if (Util.RandomDouble() > 0.16 + 0.03 * c)
            {
                s.NextGuardAt = now + 2500;
                return 0;
            }
            int ms = 1400 + Util.Random(0, 800);
            s.GuardKind = Shield(n) ? Def.Block : c >= 2 && Util.RandomDouble() < 0.35 ? Def.Evade : Def.Parry;
            s.GuardUntil = now + ms;
            s.NextGuardAt = now + ms + Math.Max(3500, 7000 - c * 500);
            Tell(n, $"guard|{n.ObjectID}|{GuardCode(s.GuardKind)}|{ms}");
            Note(n, $"guard {GuardCode(s.GuardKind)} {ms} ms");
            return ms;
        }

        static string GuardCode(Def d) => d switch { Def.Block => "block", Def.Evade => "evade", _ => "parry" };

        static void EndGuard(GameNPC n, State s)
        {
            if (s.GuardUntil <= GameLoop.GameLoopTime)
                return;
            s.GuardUntil = 0;
            Tell(n, $"guardend|{n.ObjectID}");
        }

        // ------------------------------------------------------------------ choosing a blow

        /// <summary>The next blow's kind and its wind-up (ms), as a wind-up starts.</summary>
        public static (Blow kind, int ms) Pick(GameNPC npc)
        {
            int c = Comp(npc);
            if (c < 0)
                return (Blow.Normal, NormalMs);
            State s = Of(npc);
            long now = GameLoop.GameLoopTime;
            double st = Stamina(s, now);
            bool hum = Humanoid(npc);

            // follow-ups first: a counter after turning a blow aside, a chain after a style landed
            bool counter = s.CounterNext, chain = s.ChainNext;
            s.CounterNext = s.ChainNext = false;
            if (counter && hum && c >= 1 && st >= CounterCost)
            {
                Note(npc, "counter");
                return (Blow.Counter, CounterMs);
            }
            if (chain && c >= 3 && st >= ChainCost)
            {
                Note(npc, "chain");
                return (Blow.Chain, ChainMs);
            }
            if (s.Last != Blow.Normal)                       // otherwise never two specials in a row: room to breathe
                return (Blow.Normal, NormalMs);

            if (c >= 5 && now >= s.NextSlamAt && Util.RandomDouble() < 0.4)
            {
                s.NextSlamAt = now + 12000;
                return (Blow.Slam, SlamMs);
            }
            if (c >= 2 && now >= s.NextConeAt && st >= Math.Max(LowStamina, ConeCost) && Util.RandomDouble() < 0.35)
            {
                s.NextConeAt = now + Math.Max(8000, 16000 - c * 1500);
                return (Blow.Cone, ConeMs);
            }
            if (Util.RandomDouble() < 0.22 + 0.04 * c && st >= Math.Max(LowStamina, hum ? StyleCost : HeavyCost))
                return hum ? (Blow.Style, StyleMs) : (Blow.Heavy, HeavyMs);
            return (Blow.Normal, NormalMs);
        }

        public static void Begin(GameNPC npc, Blow kind, GameLiving target)
        {
            State s = Of(npc);
            s.Pending = kind;
            s.TargetReacts = false;
            s.Positional = kind is Blow.Style or Blow.Chain or Blow.Counter && target != null && !target.IsObjectInFront(npc, 120);
            if (kind == Blow.Cone)
                s.ConeHeading = target != null ? npc.GetHeading(target) : npc.Heading;
            Spend(s, kind == Blow.Normal ? 0 : CostOf(kind));   // (a plain blow costs only when it is turned aside)
        }

        /// <summary>The kind as the client draws it: n plain, s a style (ornate ring), p a positional style, h a heavy
        /// blow (weightier ring), c a cone, g a slam.</summary>
        public static string Code(GameNPC npc, Blow b) => b switch
        {
            Blow.Style or Blow.Chain or Blow.Counter => _states.TryGetValue(npc, out State s) && s.Positional ? "p" : "s",
            Blow.Heavy => "h", Blow.Cone => "c", Blow.Slam => "g", _ => "n"
        };

        public static void End(GameNPC npc)
        {
            if (!_states.TryGetValue(npc, out State s))
                return;
            s.Last = s.Pending;
            s.Pending = Blow.Normal;
            s.Positional = false;
        }

        public static Blow PendingOf(GameLiving attacker) =>
            attacker is GameNPC n && _states.TryGetValue(n, out State s) ? s.Pending : Blow.Normal;

        // ------------------------------------------------------------------ bots and companions

        /// <summary>How likely a bot (or a pet, by its owner) reads a telegraph aimed at it: imperfect on purpose; a
        /// companion better as its competence grows, a world bot a little better with its level.</summary>
        public static double ReadChance(GameLiving who)
        {
            GameBot bot = who as GameBot ?? (who is GameNPC { Brain: IControlledBrain cb } ? cb.GetLivingOwner() as GameBot : null);
            if (bot == null)
                return 0.5;                                     // a player's pet: its master's training
            int rank = PersonalCompanions.RankOf(bot);
            return rank >= 0 ? 0.35 + 0.04 * rank : Math.Min(0.65, 0.40 + bot.Level * 0.005);
        }

        /// <summary>A wind-up at a bot or a pet (not an action-mode player): roll whether it reads it.</summary>
        public static void TelegraphAtBot(GameNPC npc, GameLiving target, Blow kind)
        {
            if (kind != Blow.Normal)
                Of(npc).TargetReacts = Util.RandomDouble() < ReadChance(target);
        }

        /// <summary>A wind-up at a player: their companion may call it out.</summary>
        public static void TelegraphAtPlayer(GamePlayer player, Blow kind)
        {
            if (kind is Blow.Heavy or Blow.Cone or Blow.Slam)
                PersonalCompanions.Warn(player, kind);
        }

        // ------------------------------------------------------------------ damage and after the blow

        /// <summary>A blow's damage factor: a monster's style, heavy blow and the like hit harder.</summary>
        public static double HitFactor(AttackData ad)
        {
            if (ad?.Attacker is not GameNPC an || !_states.TryGetValue(an, out State s) || s.Pending == Blow.Normal)
                return 1.0;
            bool botRead = ad.Target is not GamePlayer && s.TargetReacts;   // a bot that read it braced for it
            double f = s.Pending switch
            {
                Blow.Style => s.Positional ? PositionalFactor : StyleFactor,
                Blow.Chain => ChainFactor,
                Blow.Counter => CounterFactor,
                Blow.Heavy => HeavyFactor,
                _ => 1.0
            };
            return botRead ? 1.0 + (f - 1.0) * 0.25 : f;
        }

        /// <summary>After any blow is worked out (AttackComponent): endurance back for a turned-aside blow, a monster's
        /// guard and counter, a landed style's chain, a beast's bite proc.</summary>
        public static void AfterBlow(AttackData ad)
        {
            TierCalibration.Seen(ad);
            if (ad?.Target == null || ad.Attacker == null || !ad.IsMeleeAttack && ad.AttackType != AttackData.eAttackType.Ranged)
                return;
            long now = GameLoop.GameLoopTime;
            bool defended = ad.AttackResult is eAttackResult.Evaded or eAttackResult.Parried or eAttackResult.Blocked;
            bool landed = ad.AttackResult is eAttackResult.HitUnstyled or eAttackResult.HitStyle;

            if (Comp(ad.Target) >= 0)
            {
                GameNPC tn = (GameNPC) ad.Target;
                State s = Of(tn);
                s.HitAt = now;
                if (defended)
                {
                    Note(tn, $"{ad.AttackResult} {ad.Attacker.Name}'s blow{(s.GuardUntil > now ? " (guarding)" : "")}, stamina {(int) Stamina(s, now)}");
                    Gain(s, DefendGain);
                    if (Humanoid(tn) && Comp(tn) >= 1)
                        s.CounterNext = true;                   // it answers a turned-aside blow
                    EndGuard(tn, s);
                }
                else if (landed && s.GuardUntil > now)
                {
                    Spend(s, GuardFailCost);                    // its guard was beaten
                    EndGuard(tn, s);
                }
                else if (landed && Comp(tn) >= 1 && Humanoid(tn))
                    Spend(s, MissedDefenseCost);                // a defence it tried and missed
            }
            else if (defended && ad.Target is GamePlayer or GameBot && ad.Target.MaxEndurance > 0)
            {
                // a successful block / parry / evade gives some endurance back; a timed one more
                int pct = ad.ActionDefense != eActionDefense.None && !ad.ActionAuto ? 5 : 2;
                int gain = Math.Max(1, ad.Target.MaxEndurance * pct / 100);
                ad.Target.ChangeEndurance(ad.Target, eEnduranceChangeType.Regenerate, gain);
            }

            int c = Comp(ad.Attacker);
            if (c >= 0 && defended)
            {
                // its blow turned aside: what it tried costs it three times over (it paid once as it began)
                State s = Of((GameNPC) ad.Attacker);
                Blow b = s.Pending;
                Spend(s, b == Blow.Normal ? PlainCost * DefendedTimes : CostOf(b) * (DefendedTimes - 1));
            }
            if (c >= 0 && landed)
            {
                GameNPC an = (GameNPC) ad.Attacker;
                State s = Of(an);
                if (s.Pending is Blow.Style or Blow.Counter && c >= 3)
                    s.ChainNext = true;
                if (!Humanoid(an))
                    TryProc(an, ad.Target, s.Pending, c);
            }
        }

        // ------------------------------------------------------------------ beasts' procs

        static readonly string[] PoisonWords = { "spider", "snake", "serpent", "scorpion", "wasp", "hornet", "beetle", "adder",
            "viper", "toad", "salamander", "centipede", "asp", "ant", "insect", "lizard", "newt" };
        static readonly string[] DiseaseWords = { "rat", "zombie", "ghoul", "corpse", "plague", "carrion", "bat", "rotting",
            "skeleton", "boggart", "fungus", "mold" };

        static readonly int[] Poisons = { 30000, 30004, 30009, 30014, 30019, 30019 };
        public const int DiseaseProc = 11243, SnareProc = 11201, BleedProcBase = 20200;

        /// <summary>Which DAoC proc this beast's bite carries.</summary>
        public static int ProcFor(GameNPC n, int c)
        {
            string name = (n.Name ?? "").ToLowerInvariant();
            foreach (string w in PoisonWords)
                if (name.Contains(w))
                    return Poisons[Math.Clamp(c, 0, 5)];
            foreach (string w in DiseaseWords)
                if (name.Contains(w))
                    return DiseaseProc;
            return (NpcTemplateMgr.eBodyType) n.BodyType switch
            {
                NpcTemplateMgr.eBodyType.Insect or NpcTemplateMgr.eBodyType.Reptile => Poisons[Math.Clamp(c, 0, 5)],
                NpcTemplateMgr.eBodyType.Undead => DiseaseProc,
                _ => BleedProcBase + Math.Clamp(c, 0, 5)
            };
        }

        static void TryProc(GameNPC n, GameLiving target, Blow b, int c)
        {
            if (!target.IsAlive || c == 0 && b != Blow.Heavy)
                return;
            double chance = b == Blow.Heavy ? 0.3 + 0.05 * c : 0.03 + 0.015 * c;
            if (Util.RandomDouble() >= chance)
                return;
            int id = b == Blow.Heavy && c >= 3 && Util.RandomDouble() < 0.4 ? SnareProc : ProcFor(n, c);
            try
            {
                Spell spell = SkillBase.GetSpellByID(id);
                SpellLine line = SkillBase.GetSpellLine(GlobalSpellsLines.Mob_Spells);
                if (spell == null || line == null)
                    return;
                ScriptMgr.CreateSpellHandler(n, spell, line)?.StartSpell(target);
                Note(n, $"proc {id} {spell.Name} on {target.Name}");
            }
            catch (Exception e)
            {
                Console.WriteLine($"[MonsterMoves] proc {id} from {n.Name}: {e.Message}");
            }
        }

        // ------------------------------------------------------------------ area blows: the cone, the slam

        /// <summary>The cone lands: everyone on the players' side in front of it (as it faced when it wound up) and in
        /// reach is hit. Strafe out of it, or a timed dodge.</summary>
        public static void Cone(GameNPC npc)
        {
            ushort heading = Of(npc).ConeHeading;
            Area(npc, ConeRadius, ConeFactor, "sweeps", v =>
            {
                int diff = Math.Abs(((npc.GetHeading(v) - heading) % 4096 + 4096 + 2048) % 4096 - 2048);
                return diff * 360.0 / 4096.0 <= ConeArc / 2.0;
            });
        }

        /// <summary>The slam lands (purple only): everyone on the players' side still inside the circle is hit.</summary>
        public static void Slam(GameNPC npc) => Area(npc, SlamRadius, SlamFactor, "slams the ground and hits", _ => true);

        static void Area(GameNPC npc, int radius, double factor, string verb, Func<GameLiving, bool> inside)
        {
            if (!npc.IsAlive)
                return;
            double baseDamage = npc.attackComponent.WeaponDamage(npc.ActiveWeapon, null, 1.0, out _);
            var hit = new List<GameLiving>();
            foreach (GamePlayer p in npc.GetPlayersInRadius((ushort) (radius + 40)))
                hit.Add(p);
            foreach (GameNPC o in npc.GetNPCsInRadius((ushort) (radius + 40)))
                if (o is GameBot || o.Brain is IControlledBrain)
                    hit.Add(o);
            foreach (GameLiving v in hit)
            {
                if (!v.IsAlive || MonsterTiers.Combatant(v) == null || !GameServer.ServerRules.IsAllowedToAttack(npc, v, true) || !inside(v))
                    continue;
                if (v is GamePlayer vp0 && ActionCombat.IsActive(vp0) && ActionCombat.Dodging(vp0))
                {
                    ActionCombat.Send(vp0, "def|dodge|0|0");
                    continue;                                   // a timed dodge rolls out of it
                }
                if (v is not GamePlayer && Util.RandomDouble() < ReadChance(v) + 0.15)
                {
                    StepOut(npc, v, radius);                    // a bot that saw it coming got out of it
                    continue;
                }
                double dmg = baseDamage * factor * 0.65;       // (about what armour would take off)
                if (MonsterTiers.TryDamageFactor(npc, v, out double f))
                    dmg *= f;
                int amount = Math.Max(1, (int) dmg);
                v.TakeDamage(npc, eDamageType.Crush, amount, 0);
                if (npc.Brain is StandardMobBrain b)
                    b.AddToAggroList(v, 1);
                if (v is GamePlayer vp)
                {
                    vp.Out.SendMessage($"{npc.GetName(0, true)} {verb} you for {amount} damage!",
                        eChatType.CT_Damaged, eChatLoc.CL_SystemWindow);
                    if (ActionCombat.IsActive(vp))
                        ActionCombat.Send(vp, $"fct|0|{amount}|0|in");
                }
            }
        }

        static void StepOut(GameNPC npc, GameLiving v, int radius)
        {
            if (v is not GameNPC mover)
                return;
            double dx = v.X - npc.X, dy = v.Y - npc.Y, len = Math.Max(1, Math.Sqrt(dx * dx + dy * dy));
            int x = (int) (npc.X + dx / len * (radius + 120)), y = (int) (npc.Y + dy / len * (radius + 120));
            mover.WalkTo(new Point3D(x, y, v.Z), (short) Math.Max((int) mover.MaxSpeed, 250));
        }

        /// <summary>Send an "#AC|..." line to the action-mode players near a monster.</summary>
        public static void Tell(GameNPC n, string line)
        {
            foreach (GamePlayer p in n.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                if (ActionCombat.IsActive(p))
                    ActionCombat.Send(p, line);
        }

        // ------------------------------------------------------------------ the plates' endurance and power lines

        static readonly ConcurrentDictionary<string, Dictionary<int, int>> _vitSent = new();
        static readonly ConcurrentDictionary<string, ushort> _vitRegion = new();

        /// <summary>Once a second (HeroInfo.Tick): "#VIT|oid:end:pow;..." for the monsters and bots near a player whose
        /// endurance or power changed (power -1: it has none). The plates draw them under the health bar.</summary>
        public static void PushVitals(GamePlayer p)
        {
            if (p?.Client == null)
                return;
            var sent = _vitSent.GetOrAdd(p.ObjectId, _ => new());
            var sb = new StringBuilder();
            lock (sent)
            {
                if (!_vitRegion.TryGetValue(p.ObjectId, out ushort reg) || reg != p.CurrentRegionID)
                {
                    sent.Clear();
                    _vitRegion[p.ObjectId] = p.CurrentRegionID;
                }
                var dead = new StringBuilder();
                foreach (GameNPC npc in p.GetNPCsInRadius(4000))
                {
                    if (!npc.IsAlive)
                    {
                        // a fallen bot (a companion waiting to be helped up): it lies where it fell (owner 2026-11-19:
                        // "they should be laying down dead where they die") - the client may only have it from a
                        // create packet, which carries no health
                        if (npc is GameBot && npc.ObjectState == GameObject.eObjectState.Active)
                        {
                            int dcode = -1 - (int) (GameLoop.GameLoopTime / 5000 % 1000000);   // (again every 5 s: a client that rebuilt it)
                            if (!sent.TryGetValue(npc.ObjectID, out int dwas) || dwas != dcode)
                            {
                                sent[npc.ObjectID] = dcode;
                                dead.Append(npc.ObjectID).Append(':').Append(npc.X).Append(':').Append(npc.Y).Append(':').Append(npc.Z).Append(';');
                            }
                        }
                        continue;
                    }
                    int end, pow;
                    if (npc is GameBot bot)
                    {
                        end = bot.EndurancePercent;
                        pow = bot.MaxMana > 0 ? bot.ManaPercent : -1;
                    }
                    else if (Comp(npc) >= 0)
                    {
                        end = (int) Math.Round(Stamina(npc));
                        pow = npc.Spells != null && npc.Spells.Count > 0 ? npc.ManaPercent : -1;
                    }
                    else
                        continue;
                    int code = end * 1000 + pow + 1;
                    if (sent.TryGetValue(npc.ObjectID, out int was) && was == code)
                        continue;
                    sent[npc.ObjectID] = code;
                    sb.Append(npc.ObjectID).Append(':').Append(end).Append(':').Append(pow).Append(';');
                    if (sb.Length > 900)
                    {
                        NewClient.Send(p, "#VIT|" + sb);
                        sb.Clear();
                    }
                }
                if (dead.Length > 0)
                    NewClient.Send(p, "#DEAD|" + dead);
            }
            if (sb.Length > 0)
                NewClient.Send(p, "#VIT|" + sb);
        }

        public static void Forget(GamePlayer p)
        {
            if (p == null)
                return;
            _vitSent.TryRemove(p.ObjectId, out _);
            _vitRegion.TryRemove(p.ObjectId, out _);
        }
    }
}
