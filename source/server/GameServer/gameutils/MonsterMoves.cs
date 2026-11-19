using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using DOL.AI.Brain;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// Monsters that do more than auto-attack (owner 2026-11-18/19, "Purposeful PvE", first pass). A tiered monster's
    /// con says how much it knows (gameutils/MonsterTiers.cs): green plain blows with the variable wind-up Action Combat
    /// already has; blue a heavy blow now and then; yellow adds an unblockable one; orange and up slam the ground; the
    /// higher the con, the more often. Telegraphs (the client draws them, "#AC|..."):
    ///   - yellow wind-up (a heavy blow): parry, block or dodge it - a timed parry / block of it breaks the monster's poise;
    ///   - red wind-up (unblockable): only a dodge or stepping out of reach saves you;
    ///   - a ground circle filling up (a slam): get out of it before it lands.
    /// Poise: blue and up have a stagger bar. Your blows wear it down (styles more), a timed answer to a heavy blow takes a
    /// big bite, a kick (/ac kick, everyone's interrupt on a cooldown) takes one too and cancels a wind-up or a spell.
    /// Broken, the monster staggers for a few seconds - no blows, no spells - and takes more damage. It recovers after a
    /// few quiet seconds.
    /// </summary>
    public static class MonsterMoves
    {
        public enum Blow : byte { Normal, Heavy, Unblockable, Slam }

        public const int NormalMs = 600, HeavyMs = 1100, UnblockableMs = 1300, SlamMs = 1700;
        public const int SlamRadius = 350;
        public const double HeavyFactor = 1.8, UnblockableFactor = 2.2, SlamFactor = 1.6;
        public const double StaggeredTakes = 1.25;
        public const int StaggerMs = 3000;
        public const int KickCooldownMs = 10000;
        public const int KickRange = 300;

        public sealed class State
        {
            public Blow Pending;
            public Blow Last;
            public long NextSlamAt;
            public double Poise = -1;          // -1: full (set on first hit)
            public long PoiseHitAt;
            public long StaggerUntil;
            public bool CancelWindup;
            public bool TargetReacts;          // a bot / pet target saw this blow coming (rolled as it winds up)
            public int LastSentPoise = -2;
        }

        static readonly ConditionalWeakTable<GameNPC, State> _states = new();
        static readonly ConcurrentDictionary<string, long> _kickReady = new();

        public static State Of(GameNPC n) => _states.GetValue(n, _ => new State());

        static bool Knows(GameNPC n, out sbyte tier)
        {
            tier = MonsterTiers.Tier(n);
            return tier != MonsterTiers.None && tier > MonsterTiers.Green;
        }

        // ------------------------------------------------------------------ choosing a blow

        /// <summary>The next blow's kind and its wind-up (ms), as a wind-up starts.</summary>
        public static (Blow kind, int ms) Pick(GameNPC npc)
        {
            if (!Knows(npc, out sbyte t))
                return (Blow.Normal, NormalMs);
            State s = Of(npc);
            long now = GameLoop.GameLoopTime;
            if (s.Last != Blow.Normal)                       // never two specials in a row: room to breathe
                return (Blow.Normal, NormalMs);
            double heavy, unblock;
            int slamCd;
            switch (t)
            {
                case MonsterTiers.Blue: heavy = 0.22; unblock = 0; slamCd = 0; break;
                case MonsterTiers.Yellow: heavy = 0.22; unblock = 0.10; slamCd = 0; break;
                case MonsterTiers.Orange: heavy = 0.22; unblock = 0.14; slamCd = 14000; break;
                case MonsterTiers.Red: heavy = 0.22; unblock = 0.18; slamCd = 10000; break;
                default: heavy = 0.20; unblock = 0.20; slamCd = 8000; break;
            }
            if (slamCd > 0 && now >= s.NextSlamAt && Util.RandomDouble() < 0.5)
            {
                s.NextSlamAt = now + slamCd;
                return (Blow.Slam, SlamMs);
            }
            double r = Util.RandomDouble();
            if (r < unblock)
                return (Blow.Unblockable, UnblockableMs);
            if (r < unblock + heavy)
                return (Blow.Heavy, HeavyMs);
            return (Blow.Normal, NormalMs);
        }

        public static void Begin(GameNPC npc, Blow kind)
        {
            State s = Of(npc);
            s.Pending = kind;
            s.CancelWindup = false;
            s.TargetReacts = false;
        }

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
            if (kind is Blow.Heavy or Blow.Unblockable)
                Of(npc).TargetReacts = Util.RandomDouble() < ReadChance(target);
        }

        /// <summary>A wind-up at a player: their companion may call it out.</summary>
        public static void TelegraphAtPlayer(GamePlayer player, Blow kind)
        {
            if (kind != Blow.Normal)
                PersonalCompanions.Warn(player, kind);
        }

        public static void End(GameNPC npc)
        {
            if (!_states.TryGetValue(npc, out State s))
                return;
            s.Last = s.Pending;
            s.Pending = Blow.Normal;
        }

        public static Blow PendingOf(GameLiving attacker) =>
            attacker is GameNPC n && _states.TryGetValue(n, out State s) ? s.Pending : Blow.Normal;

        public static bool Staggered(GameNPC npc) =>
            _states.TryGetValue(npc, out State s) && s.StaggerUntil > GameLoop.GameLoopTime;

        public static bool TakeCancel(GameNPC npc)
        {
            if (!_states.TryGetValue(npc, out State s) || !s.CancelWindup)
                return false;
            s.CancelWindup = false;
            s.Pending = Blow.Normal;
            return true;
        }

        public static string Code(Blow b) => b switch { Blow.Heavy => "h", Blow.Unblockable => "u", Blow.Slam => "s", _ => "n" };

        // ------------------------------------------------------------------ damage

        /// <summary>A blow's damage factor: a monster's heavy / unblockable blow hits harder; a staggered monster takes more.</summary>
        public static double HitFactor(AttackData ad)
        {
            if (ad == null)
                return 1.0;
            double f = 1.0;
            Blow b = PendingOf(ad.Attacker);
            bool botRead = b != Blow.Normal && ad.Target is not GamePlayer && ad.Attacker is GameNPC an &&
                _states.TryGetValue(an, out State st) && st.TargetReacts;
            switch (b)
            {
                case Blow.Heavy: f *= botRead ? 0.3 : HeavyFactor; break;            // a bot that read it caught it
                case Blow.Unblockable: f *= botRead ? 0.1 : UnblockableFactor; break; // ... or stepped aside
            }
            if (ad.Target is GameNPC tn && Staggered(tn) && MonsterTiers.Combatant(ad.Attacker) != null)
                f *= StaggeredTakes;
            return f;
        }

        /// <summary>An unblockable blow can't be parried or blocked (a dodge still works).</summary>
        public static bool Unblockable(GameLiving attacker) => PendingOf(attacker) == Blow.Unblockable;

        // ------------------------------------------------------------------ poise

        static double MaxPoise(sbyte tier) => tier switch
        {
            MonsterTiers.Blue => 60,
            MonsterTiers.Yellow => 100,
            MonsterTiers.Orange => 160,
            MonsterTiers.Red => 250,
            MonsterTiers.Purple => 400,
            _ => 0
        };

        /// <summary>A player-side blow landed on a monster: wear its poise.</summary>
        public static void OnHit(AttackData ad)
        {
            if (ad?.Target is not GameNPC n || MonsterTiers.Combatant(ad.Attacker) == null)
                return;
            if (ad.AttackResult is not (eAttackResult.HitUnstyled or eAttackResult.HitStyle))
                return;
            Wear(n, ad.Style != null ? 12 : 6, ad.Attacker);
        }

        /// <summary>Wear a monster's poise by this much; broken, it staggers.</summary>
        public static void Wear(GameNPC n, double amount, GameLiving by)
        {
            if (!Knows(n, out sbyte t) || !n.IsAlive)
                return;
            State s = Of(n);
            long now = GameLoop.GameLoopTime;
            double max = MaxPoise(t);
            if (s.StaggerUntil > now || max <= 0)
                return;
            Recover(s, max, now);
            s.Poise = Math.Max(0, s.Poise - amount);
            s.PoiseHitAt = now;
            if (s.Poise <= 0)
            {
                s.StaggerUntil = now + StaggerMs;
                s.Poise = max;
                s.CancelWindup = true;
                if (n.IsCasting)
                    n.StopCurrentSpellcast();
                Tell(n, $"stagger|{n.ObjectID}|{StaggerMs}");
            }
            SendPoise(n, s, max);
        }

        static void Recover(State s, double max, long now)
        {
            if (s.Poise < 0)
                s.Poise = max;
            else if (now - s.PoiseHitAt > 5000)                 // after 5 quiet seconds: a quarter back per second
                s.Poise = Math.Min(max, s.Poise + (now - s.PoiseHitAt - 5000) / 1000.0 * 0.25 * max);
        }

        static void SendPoise(GameNPC n, State s, double max)
        {
            int pct = (int) Math.Round(s.Poise * 100 / max);
            if (pct == s.LastSentPoise)
                return;
            s.LastSentPoise = pct;
            Tell(n, $"poise|{n.ObjectID}|{pct}");
        }

        /// <summary>Send an "#AC|..." line to the action-mode players near a monster.</summary>
        public static void Tell(GameNPC n, string line)
        {
            foreach (GamePlayer p in n.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                if (ActionCombat.IsActive(p))
                    ActionCombat.Send(p, line);
        }

        /// <summary>A timed parry / block caught a heavy blow, or a dodge an unblockable one: a big bite of poise.</summary>
        public static void OnDefended(GamePlayer player, AttackData ad)
        {
            if (ad?.Attacker is not GameNPC n)
                return;
            Blow b = PendingOf(n);
            if (b == Blow.Heavy && ad.ActionDefense is eActionDefense.Parry or eActionDefense.Block && !ad.ActionAuto)
                Wear(n, 40, player);
            else if (b == Blow.Unblockable && ad.ActionDefense is eActionDefense.Dodge && !ad.ActionAuto)
                Wear(n, 15, player);
        }

        // ------------------------------------------------------------------ the slam

        /// <summary>The slam lands: everyone on the players' side still inside the circle is hit.</summary>
        public static void Slam(GameNPC npc)
        {
            if (!npc.IsAlive)
                return;
            double baseDamage = npc.attackComponent.WeaponDamage(npc.ActiveWeapon, null, 1.0, out _);
            var hit = new List<GameLiving>();
            foreach (GamePlayer p in npc.GetPlayersInRadius(SlamRadius))
                hit.Add(p);
            foreach (GameNPC o in npc.GetNPCsInRadius(SlamRadius))
                if (o is GameBot || o.Brain is IControlledBrain)
                    hit.Add(o);
            foreach (GameLiving v in hit)
            {
                if (!v.IsAlive || MonsterTiers.Combatant(v) == null || !GameServer.ServerRules.IsAllowedToAttack(npc, v, true))
                    continue;
                if (v is not GamePlayer && Util.RandomDouble() < ReadChance(v) + 0.15)
                {
                    StepOut(npc, v);                            // a bot that saw the circle got out of it
                    continue;
                }
                double dmg = baseDamage * SlamFactor * 0.65;   // (about what armour would take off)
                if (MonsterTiers.TryDamageFactor(npc, v, out double f))
                    dmg *= f;
                int amount = Math.Max(1, (int) dmg);
                v.TakeDamage(npc, eDamageType.Crush, amount, 0);
                if (npc.Brain is StandardMobBrain b)
                    b.AddToAggroList(v, 1);
                if (v is GamePlayer vp)
                {
                    vp.Out.SendMessage($"{npc.GetName(0, true)} slams the ground and hits you for {amount} damage!",
                        eChatType.CT_Damaged, eChatLoc.CL_SystemWindow);
                    if (ActionCombat.IsActive(vp))
                        ActionCombat.Send(vp, $"fct|0|{amount}|0|in");
                }
            }
        }

        static void StepOut(GameNPC npc, GameLiving v)
        {
            if (v is not GameNPC mover)
                return;
            double dx = v.X - npc.X, dy = v.Y - npc.Y, len = Math.Max(1, Math.Sqrt(dx * dx + dy * dy));
            int x = (int) (npc.X + dx / len * (SlamRadius + 120)), y = (int) (npc.Y + dy / len * (SlamRadius + 120));
            mover.WalkTo(new Point3D(x, y, v.Z), (short) Math.Max((int) mover.MaxSpeed, 250));
        }

        // ------------------------------------------------------------------ the kick

        /// <summary>/ac kick: everyone's interrupt on a cooldown - stops a spell or a wind-up, and bites into poise.</summary>
        public static void Kick(GamePlayer player)
        {
            long now = GameLoop.GameLoopTime;
            if (_kickReady.TryGetValue(player.ObjectId, out long ready) && now < ready)
            {
                ActionCombat.Send(player, $"kick|cd|{ready - now}");
                return;
            }
            if (player.TargetObject is not GameNPC n || !n.IsAlive || !player.IsWithinRadius(n, KickRange) ||
                !player.IsObjectInFront(n, 120) || !GameServer.ServerRules.IsAllowedToAttack(player, n, true))
            {
                ActionCombat.Send(player, "kick|far|0");
                return;
            }
            int cost = Math.Max(3, player.MaxEndurance * 5 / 100);
            if (player.Endurance < cost)
            {
                ActionCombat.Send(player, "kick|tired|0");
                return;
            }
            player.ChangeEndurance(player, eEnduranceChangeType.Spell, -cost);
            _kickReady[player.ObjectId] = now + KickCooldownMs;
            MonsterTiers.Touch(player, n);
            State s = Of(n);
            string what;
            if (n.IsCasting)
            {
                n.StopCurrentSpellcast();
                what = "interrupt";
                Wear(n, 30, player);
            }
            else if (s.Pending != Blow.Normal)
            {
                s.CancelWindup = true;
                what = "cancel";
                Wear(n, 40, player);
            }
            else
            {
                what = "hit";
                Wear(n, 15, player);
            }
            if (n.Brain is StandardMobBrain b)
                b.AddToAggroList(player, 1);
            ActionCombat.Send(player, $"kick|{what}|{KickCooldownMs}|{n.ObjectID}");
            if (what != "hit")
                Tell(n, $"cancel|{n.ObjectID}");
        }

        public static void Forget(GamePlayer p)
        {
            if (p != null)
                _kickReady.TryRemove(p.ObjectId, out _);
        }
    }
}
