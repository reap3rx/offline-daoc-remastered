using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;

namespace DOL.GS.DynamicEvents
{
    public enum EventRole { Hostile, Protect, Boss, Ally, Giver, Node }

    /// <summary>A monster or NPC of an event: credits damage to its stage, tells it when it dies; a giver talks.</summary>
    public class EventNpc : GameNPC
    {
        public ChainRuntime Chain;
        public StageRuntime Stage;
        public EventRole Role;
        public double HealthMult = 1;
        public double ConHealth = 1;                 // a boss's health within its con, by head count (EventCons)
        public bool ConLocked;                       // its con settled as its fight started

        public bool IsEnemy => Role is EventRole.Hostile or EventRole.Boss;
        public override int MaxHealth => (int) Math.Max(1, base.MaxHealth * HealthMult);
        public override bool CanDropLoot => Role == EventRole.Boss;

        public override void TakeDamage(GameObject source, eDamageType damageType, int damageAmount, int criticalAmount)
        {
            base.TakeDamage(source, damageType, damageAmount, criticalAmount);
            Stage?.OnDamaged(this, source, damageAmount + criticalAmount);
        }

        /// <summary>Healing an event's people draws its monsters (owner 2026-11-23, Bugs & Fixes: "Event enemies should also
        /// start to gain aggression to anyone who heals the event NPCs"): the chain's monsters near the one healed take
        /// the healer on, by what was healed - the way a monster turns on whoever heals the one it's fighting.</summary>
        public override int ChangeHealth(GameObject changeSource, eHealthChangeType healthChangeType, int changeAmount)
        {
            int done = base.ChangeHealth(changeSource, healthChangeType, changeAmount);
            if (done > 0 && Chain != null && !IsEnemy && changeSource is GameLiving healer && healer != this && healer.IsAlive)
                foreach (EventNpc foe in Chain.EnemiesNear(this, 1600))
                    if (foe.Brain is StandardMobBrain b)
                        b.AddToAggroList(healer, Math.Max(1, done / 2));
            return done;
        }

        /// <summary>The worst-hurt of an event's own people near <paramref name="who"/> (the one being kept alive, a giver,
        /// their guards), under <paramref name="belowPct"/> - for a healer bot (BotBrain).</summary>
        public static GameLiving WoundedNear(GameLiving who, int radius, int belowPct)
        {
            if (who?.CurrentRegion == null)
                return null;
            EventNpc best = null;
            foreach (GameNPC n in who.GetNPCsInRadius((ushort) Math.Min(65000, radius)))
                if (n is EventNpc e && !e.IsEnemy && e.Role != EventRole.Node && e.IsAlive && e.Realm == who.Realm &&
                    e.ObjectState == eObjectState.Active && e.HealthPercent < belowPct && (best == null || e.HealthPercent < best.HealthPercent))
                    best = e;
            return best;
        }

        public override void ProcessDeath(GameObject killer)
        {
            Stage?.OnDied(this, killer);
            base.ProcessDeath(killer);
        }

        public override bool Interact(GamePlayer player)
        {
            if (Role == EventRole.Node && Stage != null)
            {
                if (!base.Interact(player))
                    return false;
                Stage.OnGathered(this, player);
                return true;
            }
            if (Role != EventRole.Giver || Chain == null)
                return base.Interact(player);
            if (!base.Interact(player))
                return false;
            Chain.Greet(player);
            return true;
        }

        public override bool WhisperReceive(GameLiving source, string text)
        {
            if (Role != EventRole.Giver || Chain == null || source is not GamePlayer player)
                return base.WhisperReceive(source, text);
            if (!base.WhisperReceive(source, text))
                return false;
            if (string.Equals(text?.Trim(), Chain.Def.Giver.Accept, StringComparison.OrdinalIgnoreCase))
                Chain.Accept(player);
            return true;
        }
    }

    /// <summary>An event monster's mind: an ordinary monster's, except that it has somewhere to be. Sent after someone
    /// (the NPC a defend stage protects, the giver on the road, the players at a boss) it runs there and attacks; it never
    /// walks back to where it appeared (its spawn point follows it - an event monster has no home to return to).</summary>
    public class EventMobBrain : StandardMobBrain
    {
        public GameLiving Goal;
        public Point3D Post;                         // an occupation's garrison: they go back to their post after a fight
        public GameLiving Escort;                    // an intercept's convoy guards: they keep with its leader

        public override void Think()
        {
            if (Body == null || !Body.IsAlive)
            {
                base.Think();
                return;
            }
            Body.SpawnPoint = Post ?? new Point3D(Body.X, Body.Y, Body.Z);
            if (Goal != null && (!Goal.IsAlive || Goal.ObjectState != GameObject.eObjectState.Active || Goal.CurrentRegion != Body.CurrentRegion))
                Goal = null;
            if (Escort != null && (!Escort.IsAlive || Escort.ObjectState != GameObject.eObjectState.Active))
                Escort = null;
            if (Goal == null && Escort != null && !HasAggro && !Body.IsWithinRadius(Escort, 260) && !Body.IsMoving)
                Body.PathTo(EventFollowSlots.Of(Body, Escort), (short) Math.Max(Body.MaxSpeed, Escort.MaxSpeed));
            if (Goal != null && !HasAggro)
            {
                if (Body.IsWithinRadius(Goal, 500))
                {
                    AddToAggroList(Goal, 100);
                    FSM.SetCurrentState(eFSMStateType.AGGRO);
                }
                else if (!Body.IsMoving)
                    Body.PathTo(new Vector3(Goal.X, Goal.Y, Goal.Z), Body.MaxSpeed);
            }
            base.Think();
        }
    }

    /// <summary>A giver's and their guards' mind: fight the chain's monsters that come near, otherwise keep up with
    /// whoever they follow; a giver whose chain has ended walks back to their post.</summary>
    public class EventAllyBrain : StandardMobBrain
    {
        public GameLiving Follow;
        public Point3D Home;
        public bool Steered;                         // a stage is walking them: no following, no going home

        public override void Think()
        {
            if (Body is not EventNpc me || !me.IsAlive)
            {
                base.Think();
                return;
            }
            Body.SpawnPoint = new Point3D(Body.X, Body.Y, Body.Z);
            if (!HasAggro && me.Chain != null)
            {
                // the chain's monsters near them, or near the one they follow (a guard runs to the giver's aid)
                GameLiving foe = me.Chain.EnemiesNear(me, 1600).OrderBy(n => n.GetDistanceTo(me)).FirstOrDefault()
                    ?? (Follow != null && Follow.IsAlive ? me.Chain.EnemiesNear(Follow, 1200).OrderBy(n => n.GetDistanceTo(Follow)).FirstOrDefault() : null)
                    ?? HelpFoe(me);
                if (foe != null)
                {
                    AddToAggroList(foe, 100);
                    FSM.SetCurrentState(eFSMStateType.AGGRO);
                }
                else if (!Steered && Follow != null && Follow.IsAlive && !Body.IsWithinRadius(Follow, 260))
                {
                    if (!Body.IsMoving)
                        Body.PathTo(EventFollowSlots.Of(Body, Follow), Body.MaxSpeed);
                }
                else if (!Steered && Follow == null && Home != null)
                {
                    if (Body.IsWithinRadius(Home, 60))
                    {
                        Home = null;
                        Body.TurnTo(me.Chain.GiverHeading);
                    }
                    else if (!Body.IsMoving)
                        Body.PathTo(new Vector3(Home.X, Home.Y, Home.Z), (short) Math.Max(100, Body.MaxSpeed / 2));
                }
            }
            base.Think();
        }

        /// <summary>(owner 2026-11-23, Bugs & Fixes: "Event NPCs should help you if you end up in a fight with non
        /// event-related NPCs if they're close by") - a monster fighting one of the people near them (a player or a bot
        /// in combat with it targeted): they go to help.</summary>
        static GameLiving HelpFoe(EventNpc me)
        {
            static bool Foe(GameObject o, EventNpc me) => o is GameNPC t && t.IsAlive && t.Realm == eRealm.None && t is not GameBot &&
                (t.Flags & GameNPC.eFlags.PEACE) == 0 && t.ObjectState == GameObject.eObjectState.Active && t.InCombat &&
                (t is not EventNpc e || e.IsEnemy) && me.IsWithinRadius(t, 1600);
            foreach (GameLiving p in me.Chain.PeopleNear(new Point3D(me.X, me.Y, me.Z), 1400).OrderBy(p => p.GetDistanceTo(me)))
                if (p.InCombat && Foe(p.TargetObject, me))
                    return (GameLiving) p.TargetObject;
            return null;
        }
    }

    /// <summary>Where a follower stands round the one it follows (owner 2026-11-16: event NPCs "tend to crowd on the same
    /// exact spot that the lead NPC is ... so everyone is stacked on each other. If they could have some sort of formation
    /// it would look better and more natural"): its own place on a loose ring behind the leader - the angle from its
    /// object id, 120 to 200 units out - so a giver's guards walk as an escort, not in a heap.</summary>
    public static class EventFollowSlots
    {
        public static Vector3 Of(GameObject follower, GameObject leader)
        {
            double heading = leader.Heading * Math.PI * 2 / 4096.0;
            double spread = ((follower.ObjectID * 2.399963) % (Math.PI * 1.4)) - Math.PI * 0.7;   // within 126 degrees of behind
            double a = heading + Math.PI + spread;
            double r = 120 + follower.ObjectID % 5 * 20;
            var want = new Vector3(leader.X - (float)(Math.Sin(a) * r), leader.Y + (float)(Math.Cos(a) * r), leader.Z);
            if (leader.CurrentZone == null)
                return want;
            return PathfindingProvider.Instance.GetMoveAlongSurface(leader.CurrentZone, new(leader.X, leader.Y, leader.Z), want,
                PathfindingProvider.Instance.DefaultFilters) ?? new Vector3(leader.X, leader.Y, leader.Z);
        }
    }

    /// <summary>One chain of a zone. A timed chain: quiet until its time, then a disturbance (shown on the map) that
    /// wakes when a player or a bot comes near; a giver's chain: started by talking to its giver. Then its stages in
    /// turn, a rest between them.</summary>
    public class ChainRuntime
    {
        public readonly ChainDef Def;
        public readonly Region Region;
        public readonly Zone Zone;
        public StageRuntime Stage;
        public long NextStart;
        public bool Dormant;
        public string PendingId;                     // the next stage, after the rest
        public long PendingAt;
        public const int RestCapS = 15;                  // the breather between stages, at most
        public string LastOutcome = "";              // shown on the map a little while after it ends
        public long LastOutcomeUntil;
        public EventNpc Giver;
        public readonly List<EventNpc> Guards = new();
        public long GiverReadyAt;
        public ushort GiverHeading;
        bool _running;
        public readonly List<(GameObject obj, long until)> Lingering = new();   // gone after a while (a thank-you, a banner)
        public readonly List<GameNPC> Displaced = new();   // the realm's NPCs an occupation drove off (back when it's won)
        public EventTokenMerchant Merchant;
        public string ResumeStage;                   // an occupation that was running when the server stopped
        public long DormantSince;
        /// <summary>A private chain (a story quest's set-piece, StoryQuests): only these take part - the quester and
        /// their group. It isn't in DynamicEventManager.Chains (no bots, no map, no tracker); its owner ticks it.</summary>
        public Func<GameLiving, bool> Allow;
        public Action<string> OnEnded;               // "success" / "fail", when it ends
        public bool Private => Allow != null;
        public bool Quiet;                           // (a private chain called off: no more words)
        // a siege's chains (ZoneSiege): its monsters tougher by this, its giver there only while Available says so, and
        // Gate (a reason, or null) before it sets out; IntervalMult shortens a chain's quiet time (the enemy grows bolder)
        public double Toughness = 1;
        public Func<bool> Available;
        public Func<string> Gate;
        public double IntervalMult = 1;
        public bool Occupied => Stage?.Def.Type == "occupy" ||
            (PendingId != null && Def.Stages.FirstOrDefault(s => s.Id == PendingId)?.Type == "occupy");                               // between Begin and End (stages and rests)

        public ChainRuntime(ChainDef def, Region region, Zone zone, long now)
        {
            Def = def;
            Region = region;
            Zone = zone;
            NextStart = now + 1000L * Util.Random(def.FirstDelayS[0], def.FirstDelayS[Math.Min(1, def.FirstDelayS.Length - 1)]);
        }

        public bool Active => Stage != null || PendingId != null;
        public EventNpc Leader => Giver != null && Giver.IsAlive && Giver.ObjectState == GameObject.eObjectState.Active ? Giver : null;
        public eRealm HomeRealm => Def.ZoneDef.Realm switch
        {
            1 => eRealm.Albion, 2 => eRealm.Midgard, 3 => eRealm.Hibernia,
            _ => Region.ID >= 200 && Region.ID < 300 ? eRealm.Hibernia : Region.ID >= 100 && Region.ID < 200 ? eRealm.Midgard : eRealm.Albion
        };

        public IEnumerable<GamePlayer> PlayersInZone() =>
            ClientService.Instance.GetPlayers().Where(p => p.CurrentRegion == Region && (p.CurrentZone == Zone || Private) && (Allow == null || Allow(p)));

        /// <summary>Players and bots (they take part as players do) within r units of p.</summary>
        public IEnumerable<GameLiving> PeopleNear(Point3D p, double r)
        {
            ushort ur = (ushort) Math.Min(65000, r);
            foreach (GamePlayer pl in Region.GetPlayersInRadius(p, ur))
                if (pl.IsAlive && pl.ObjectState == GameObject.eObjectState.Active && (Allow == null || Allow(pl)))
                    yield return pl;
            foreach (GameNPC n in Region.GetNPCsInRadius(p, ur))
                if (n is GameBot b && b.IsAlive && (Allow == null || Allow(b)))
                    yield return b;
        }

        bool AnyoneInZone()
        {
            if (PlayersInZone().Any())
                return true;
            var mid = new Point3D(Zone.XOffset + Zone.Width / 2, Zone.YOffset + Zone.Height / 2, 0);
            return Region.GetNPCsInRadius(mid, (ushort) Math.Min(65000, Math.Max(Zone.Width, Zone.Height) * 0.75))
                .Any(n => n is GameBot b && b.IsAlive && b.CurrentZone == Zone);
        }

        /// <summary>Where a waiting disturbance is, and how near wakes it.
        /// (An intercept or escort start has no centre: its path's first point. A start without either: the zone's middle -
        /// 2026-11-22, Connacht's night revel and Silvermine's convoy, path-only starts, threw here and the throw out of
        /// the broadcast stopped every event's timer.)</summary>
        public Vector3 WakePoint => StartPoint(Def.Stages.FirstOrDefault(s => s.Id == Def.Start));

        Vector3 StartPoint(StageDef s)
        {
            if (s?.Center != null && s.Center.Length >= 2)
                return ToWorld(s.Center, false);
            if (s?.Path != null && s.Path.Count > 0 && s.Path[0] != null && s.Path[0].Length >= 2)
                return ToWorld(s.Path[0], false);
            return new Vector3(Zone.XOffset + Zone.Width / 2f, Zone.YOffset + Zone.Height / 2f, 0f);
        }
        public double WakeUnits => (Def.WakeM > 0 ? Def.WakeM : (Def.Stages.FirstOrDefault(s => s.Id == Def.Start)?.Radius ?? 60) + 60) * 40;

        public IEnumerable<EventNpc> EnemiesNear(GameObject at, double r) =>
            (Stage?.Spawned ?? Enumerable.Empty<EventNpc>()).Where(n => n.IsEnemy && n.IsAlive && at.IsWithinRadius(n, (int) r)).ToList();

        public void Tick(long now)
        {
            for (int i = Lingering.Count - 1; i >= 0; i--)
                if (now >= Lingering[i].until)
                {
                    if (Lingering[i].obj.ObjectState == GameObject.eObjectState.Active)
                        Lingering[i].obj.RemoveFromWorld();
                    Lingering.RemoveAt(i);
                }
            if (ResumeStage != null && now - DynamicEventManager.StartedAt > 15_000)
            {
                string id = ResumeStage;
                ResumeStage = null;
                if (Def.Stages.Any(st => st.Id == id))
                    Begin(id, now);
            }
            if (Def.Giver != null)
                KeepGiver(now);
            if (Def.Merchant != null)
                KeepMerchant();
            if (Stage == null)
            {
                if (PendingId != null)
                {
                    if (now >= PendingAt)
                    {
                        string id = PendingId;
                        PendingId = null;
                        Begin(id, now);
                    }
                    return;
                }
                if (Def.Giver != null)
                    return;                                 // started by talking to the giver
                if (!Dormant)
                {
                    if (Def.Manual)
                        return;                             // (a siege's chain: the siege wakes it)
                    if (now < NextStart)
                        return;
                    if (Def.Time is "night" or "day" && Region.IsNightTime != (Def.Time == "night"))
                    {
                        NextStart = now + 60_000;           // not its hour: look again in a minute
                        return;
                    }
                    if (!AnyoneInZone())
                    {
                        NextStart = now + 60_000;           // nobody about: look again in a minute
                        return;
                    }
                    Dormant = true;                         // a disturbance: it waits for someone to come
                    DormantSince = now;
                    return;
                }
                if (Def.AutoFailS > 0 && now - DormantSince > 1000L * Def.AutoFailS)
                {
                    // nobody answered: it goes the enemy's way (owner 2026-11-02: failure with "real world consequence")
                    StageDef first = Def.Stages.First(st => st.Id == Def.Start);
                    Dormant = false;
                    foreach (GamePlayer pl in PlayersInZone())
                        pl.Out.SendMessage($"{Def.Title}: no one answered the call. {first.Fail}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                    if (!string.IsNullOrEmpty(first.OnFail) && first.OnFail != "end" && Def.Stages.Any(st => st.Id == first.OnFail))
                    {
                        _running = true;
                        Begin(first.OnFail, now);
                    }
                    else
                        End("fail", now);
                    return;
                }
                Vector3 w = WakePoint;
                if (PeopleNear(new Point3D((int) w.X, (int) w.Y, (int) w.Z), WakeUnits).Any())
                    Begin(Def.Start, now);
                return;
            }
            Stage.Tick(now);
            if (Stage.Outcome == StageOutcome.None)
                return;
            bool won = Stage.Outcome == StageOutcome.Success;
            StageDef done = Stage.Def;
            Stage.Finish(won);
            if (!Private)
                DynamicEventManager.OnStageEnded(this, done, won);
            Stage = null;
            string next = won ? done.OnSuccess : done.OnFail;
            if (!string.IsNullOrEmpty(next) && next != "end" && Def.Stages.Any(s => s.Id == next))
            {
                PendingId = next;                           // a breather: sit, heal, gather up
                // (owner 2026-11-13: "Catch your breath portion of events shortened to 15 seconds")
                PendingAt = now + 1000L * Math.Clamp(Def.RestS, 3, RestCapS);
            }
            else
                End(won ? "success" : "fail", now);
        }

        public void Begin(string stageId, long now)
        {
            Dormant = false;
            if (!_running)
            {
                _running = true;
                if (Def.Giver != null)
                    SetOut();
            }
            StageDef sd = Def.Stages.First(s => s.Id == stageId);
            if (sd.Type == "occupy" && Def.Giver != null)
                PartyHome();                            // the march is over: the land is the enemy's until it's taken back
            Stage = new StageRuntime(this, sd, now);
            if (!Private)
                DynamicEventManager.OnStageBeginning(this, sd);
            Stage.Start();
            if (!Private)
                DynamicEventManager.SaveState();
        }

        public void End(string outcome, long now)
        {
            Stage?.Finish(false);
            Stage = null;
            PendingId = null;
            RestoreDisplaced();
            if (!Private)
                DynamicEventManager.SaveState();
            Dormant = false;
            _running = false;
            OnEnded?.Invoke(outcome);
            LastOutcome = outcome;
            LastOutcomeUntil = now + 30_000;
            NextStart = now + (long) (1000L * Util.Random(Def.IntervalS[0], Def.IntervalS[Math.Min(1, Def.IntervalS.Length - 1)]) * Math.Clamp(IntervalMult, 0.2, 1.0));
            if (!Private)
                DynamicEventManager.OnChainEnded(this, outcome);
            if (Def.Giver != null)
            {
                if (Leader != null)
                    NpcSpeech.Say(Leader, outcome == "success"
                        ? Def.Giver.Thanks ?? $"We did it - well fought, all of you. {(string.IsNullOrEmpty(Leader.GuildName) ? "Everyone" : "The " + Leader.GuildName)} will hear what you did today."
                        : Def.Giver.Regret ?? "Fall back! We'll try again another day.");
                ComeHome(now);
            }
        }

        // ---------------------------------------------------------------- the giver and their party

        void KeepGiver(long now)
        {
            if (Available != null && !Active && !Available())
            {
                if (Giver != null && Giver.ObjectState == GameObject.eObjectState.Active)
                    Giver.RemoveFromWorld();        // (not now: the siege isn't ready for them)
                return;
            }
            if (Giver != null && Giver.ObjectState == GameObject.eObjectState.Active && Giver.IsAlive)
                return;
            if (Active || now < GiverReadyAt)
                return;
            if (Giver != null && Giver.ObjectState == GameObject.eObjectState.Active)
                Giver.RemoveFromWorld();
            Giver = MakeNpc(Def.Giver, EventRole.Giver, ToWorld(Def.Giver.Pos), Def.Giver.Level);
            if (Giver != null)
            {
                Giver.HealthMult = Math.Max(1, Def.Giver.HealthMult);
                Giver.Health = Giver.MaxHealth;
                GiverHeading = Giver.Heading;
            }
        }

        public void Greet(GamePlayer player)
        {
            if (Occupied)
            {
                StageDef occ = Stage?.Def ?? Def.Stages.First(s => s.Id == PendingId);
                NpcSpeech.SayTo(Giver, player, Def.Giver.Occupied ?? $"We lost that fight, and now they've dug in - {occ.Objective.ToLowerInvariant()}. Gather more swords and drive them out, then we'll talk.");
                return;
            }
            if (Active)
            {
                NpcSpeech.SayTo(Giver, player, "We're already on our way - keep up!");
                return;
            }
            if (Environment.TickCount64 < GiverReadyAt)
            {
                NpcSpeech.SayTo(Giver, player, Def.Giver.Busy);
                return;
            }
            string greet = Def.Giver.Greet ?? $"Will you come with us? Say when you're [{Def.Giver.Accept}].";
            Giver.SayTo(player, greet.Contains('[') ? greet : $"{greet} [{Def.Giver.Accept}]");
        }

        public void Accept(GamePlayer player)
        {
            long now = Environment.TickCount64;
            if (Active || Leader == null || now < GiverReadyAt)
            {
                Greet(player);
                return;
            }
            if (Gate?.Invoke() is string why)
            {
                NpcSpeech.SayTo(Giver, player, why);
                return;
            }
            if (!string.IsNullOrEmpty(Def.Giver.Reply))
                NpcSpeech.Say(Giver, Def.Giver.Reply);
            Begin(Def.Start, now);
        }

        /// <summary>A bot standing by the giver when the chain could start takes them up on it (bots answer the call too).</summary>
        public bool BotAccepts(GameBot bot)
        {
            long now = Environment.TickCount64;
            if (Def.Giver == null || Active || Leader == null || now < GiverReadyAt || !bot.IsWithinRadius(Giver, 600))
                return false;
            if (Gate?.Invoke() != null)
                return false;                       // (a siege's war band: they wait for enough people, and for you)
            Begin(Def.Start, now);
            return true;
        }

        /// <summary>The giver sets out: their guards fall in beside them.</summary>
        void SetOut()
        {
            if (Leader == null)
                return;
            foreach (EventNpc g in Guards)
                if (g.ObjectState == GameObject.eObjectState.Active)
                    g.RemoveFromWorld();
            Guards.Clear();
            foreach (NpcDef gd in Def.Guards)
                for (int i = 0; i < Math.Max(1, gd.Count); i++)
                {
                    var at = Around(new Vector3(Giver.X, Giver.Y, Giver.Z), 250);
                    EventNpc g = MakeNpc(gd, EventRole.Ally, at, gd.Level);
                    if (g == null)
                        continue;
                    g.HealthMult = Math.Max(1, gd.HealthMult);
                    g.Health = g.MaxHealth;
                    ((EventAllyBrain) g.Brain).Follow = Giver;
                    Guards.Add(g);
                }
            if (Giver.Brain is EventAllyBrain b)
                b.Home = null;
        }

        /// <summary>The chain is over: the guards go back to the garrison, the giver walks back to their post (or, fallen,
        /// is back there after the cooldown).</summary>
        /// <summary>The giver's party goes home (an occupation began): the guards back to the garrison, the giver to their
        /// post. The chain goes on (it isn't over until the land is taken back).</summary>
        void PartyHome()
        {
            foreach (EventNpc g in Guards)
                if (g.ObjectState == GameObject.eObjectState.Active)
                    g.RemoveFromWorld();
            Guards.Clear();
            if (Leader != null && Giver.Brain is EventAllyBrain b)
            {
                b.Steered = false;
                b.Follow = null;
                b.ClearAggroList();
                Vector3 home = ToWorld(Def.Giver.Pos);
                b.Home = new Point3D((int) home.X, (int) home.Y, (int) home.Z);
            }
        }

        /// <summary>The place's merchant stands there while the realm holds it.</summary>
        void KeepMerchant()
        {
            bool want = !Occupied && Displaced.Count == 0;
            bool there = Merchant != null && Merchant.ObjectState == GameObject.eObjectState.Active;
            if (want == there)
                return;
            if (!want)
            {
                Merchant.RemoveFromWorld();
                return;
            }
            MerchantDef d = Def.Merchant;
            Vector3 at = ToWorld(d.Pos);
            Merchant = new EventTokenMerchant { Greet = d.Greet };
            if (d.Template > 0 && NpcTemplateMgr.GetTemplate(d.Template) is NpcTemplate tpl)
                Merchant.LoadTemplate(tpl);
            Merchant.Name = d.Name;
            Merchant.GuildName = d.Guild ?? "Marks of Valor";
            Merchant.Level = (byte) Math.Max(1, d.Level);
            if (d.Model > 0) Merchant.Model = d.Model;
            if (!string.IsNullOrEmpty(d.Equipment))
                Merchant.LoadEquipmentTemplateFromDatabase(d.Equipment);
            Merchant.TradeItems = new MerchantTradeItems(d.Stock);
            Merchant.X = (int) at.X;
            Merchant.Y = (int) at.Y;
            Merchant.Z = (int) at.Z;
            Merchant.Heading = d.Pos != null && d.Pos.Length > 3 ? (ushort) d.Pos[3] : (ushort) 0;
            Merchant.CurrentRegion = Region;
            Merchant.Realm = HomeRealm;
            Merchant.Flags |= GameNPC.eFlags.PEACE;
            Merchant.RespawnInterval = -1;
            Merchant.LoadedFromScript = true;
            Merchant.AddToWorld();
        }

        /// <summary>An occupation drives off the realm's NPCs near its spot (a captured tower's guards and merchants).</summary>
        public void Displace(Vector3 center, double units)
        {
            foreach (GameNPC n in Region.GetNPCsInRadius(new Point3D((int) center.X, (int) center.Y, (int) center.Z), (ushort) Math.Min(65000, units)).ToList())
            {
                if (n is EventNpc || n is GameBot || n is EventTokenMerchant || n.Realm == eRealm.None || !n.IsAlive ||
                    n.Brain is IControlledBrain || Displaced.Contains(n))
                    continue;
                n.RemoveFromWorld();
                Displaced.Add(n);
            }
        }

        public void RestoreDisplaced()
        {
            foreach (GameNPC n in Displaced)
                if (n.ObjectState != GameObject.eObjectState.Active)
                {
                    n.Health = n.MaxHealth;
                    n.AddToWorld();
                }
            Displaced.Clear();
        }

        void ComeHome(long now)
        {
            foreach (var (obj, _) in Lingering.Where(l => l.obj is GameStaticItem).ToList())
            {
                if (obj.ObjectState == GameObject.eObjectState.Active)
                    obj.RemoveFromWorld();
                Lingering.RemoveAll(l => l.obj == obj);
            }
            foreach (EventNpc g in Guards)
                if (g.ObjectState == GameObject.eObjectState.Active)
                    g.RemoveFromWorld();
            Guards.Clear();
            GiverReadyAt = now + 1000L * Math.Max(0, Def.Giver.CooldownS);
            if (Leader != null && Giver.Brain is EventAllyBrain b)
            {
                b.Steered = false;
                b.Follow = null;
                Vector3 home = ToWorld(Def.Giver.Pos);
                b.Home = new Point3D((int) home.X, (int) home.Y, (int) home.Z);
                Giver.Level = (byte) Math.Max(1, Def.Giver.Level);
                Giver.Health = Giver.MaxHealth;
            }
        }

        // ---------------------------------------------------------------- making NPCs

        public EventNpc MakeNpc(NpcDef d, EventRole role, Vector3 at, int level, StageRuntime stage = null)
        {
            if (d == null)
                return null;
            return Make(d.Template, d.Name, level > 0 ? level : d.Level, d.Model, d.Size, d.Equipment, d.Guild, at, role, stage);
        }

        public EventNpc Make(int template, string name, int level, ushort model, byte size, string equipment, string guild,
            Vector3 at, EventRole role, StageRuntime stage)
        {
            var npc = new EventNpc { Chain = this, Stage = stage, Role = role };
            if (template > 0 && NpcTemplateMgr.GetTemplate(template) is NpcTemplate tpl)
                npc.LoadTemplate(tpl);
            if (!string.IsNullOrEmpty(name)) npc.Name = name;
            // the line under the name: an event's monsters carry its title, so you can tell them from the locals
            npc.GuildName = guild ?? (role is EventRole.Hostile or EventRole.Boss ? Def.Title : "");
            if (level > 0) npc.Level = (byte) Math.Clamp(level, 1, 255);
            if (model > 0) npc.Model = model;
            if (size > 0) npc.Size = size;
            if (!string.IsNullOrEmpty(equipment))
                npc.LoadEquipmentTemplateFromDatabase(equipment);
            npc.X = (int) at.X;
            npc.Y = (int) at.Y;
            npc.Z = (int) at.Z;
            npc.Heading = (ushort) Util.Random(4095);
            npc.CurrentRegion = Region;
            npc.RespawnInterval = -1;
            npc.RoamingRange = 0;
            npc.LoadedFromScript = true;
            if (role is EventRole.Hostile or EventRole.Boss)
            {
                npc.Realm = eRealm.None;
                npc.SetOwnBrain(new EventMobBrain { AggroLevel = 100, AggroRange = role == EventRole.Boss ? 900 : 650 });
            }
            else
            {
                npc.Realm = HomeRealm;
                npc.Flags = (GameNPC.eFlags) 0;     // (no peace flag: the chain's monsters may attack them)
                if (role is EventRole.Protect or EventRole.Node)
                    npc.SetOwnBrain(new BlankBrain());
                else
                    npc.SetOwnBrain(new EventAllyBrain { AggroLevel = 0, AggroRange = 0 });
            }
            if (role == EventRole.Giver && Def.Giver?.Pos != null && Def.Giver.Pos.Length > 3)
                npc.Heading = (ushort) Def.Giver.Pos[3];
            if (!npc.AddToWorld())
                return null;
            npc.SpawnPoint = new Point3D(npc.X, npc.Y, npc.Z);
            EventCons.Apply(this, npc, stage);           // its con: the zone's rating, and for a boss who is there
            npc.Health = npc.MaxHealth;
            return npc;
        }

        // ---------------------------------------------------------------- places

        /// <summary>Zone metres (the client's) to region units; z by the file's height, then the navmesh's floor.</summary>
        public Vector3 ToWorld(double[] p, bool snap = true)
        {
            var v = new Vector3((float) (Zone.XOffset + p[0] * 40), (float) (Zone.YOffset + p[1] * 40),
                p.Length > 2 ? (float) (p[2] * 40) : 0f);
            if (!snap)
                return v;
            Vector3 s = Snap(v);
            // an upper floor the navmesh doesn't have (Mag Mell's town hall): the place's own height, not the ground under it
            return p.Length > 2 && s.Z < v.Z - 100 ? v : s;
        }

        public Vector3 Snap(Vector3 v)
        {
            var nav = PathfindingProvider.Instance;
            if (nav != null && nav.IsAvailable && nav.HasNavmesh(Zone))
            {
                Vector3? floor = nav.GetClosestPoint(Zone, v, 96, 96, 2048, nav.DefaultFilters);
                if (floor.HasValue)
                    return floor.Value;
            }
            return v;
        }

        /// <summary>A spot on the ground within r units of c.</summary>
        public Vector3 Around(Vector3 c, double r)
        {
            double a = Util.RandomDouble() * Math.PI * 2, d = Math.Sqrt(Util.RandomDouble()) * r;
            return Snap(new Vector3(c.X + (float) (Math.Cos(a) * d), c.Y + (float) (Math.Sin(a) * d), c.Z));
        }

        public double ZoneMetresX(float x) => (x - Zone.XOffset) / 40.0;
        public double ZoneMetresY(float y) => (y - Zone.YOffset) / 40.0;
    }

    public enum StageOutcome { None, Success, Fail }

    /// <summary>A stage running: its spawns, progress, contributions and rewards.</summary>
    public class StageRuntime
    {
        public readonly ChainRuntime Chain;
        public readonly StageDef Def;
        public readonly long Started;
        public StageOutcome Outcome;
        public Vector3 Center;
        public int Kills;
        public EventNpc Protect, Boss;
        public readonly List<EventNpc> Spawned = new();
        readonly Dictionary<GameLiving, double> _credit = new();
        readonly Dictionary<GamePlayer, int> _carried = new();      // gather + deliver: picked, not yet handed in
        public const int DeliverReach = 350;

        /// <summary>What this player carries for a gather-and-deliver stage (0 for anything else).</summary>
        public int Carried(GamePlayer p) => Def.Deliver && p != null && _carried.TryGetValue(p, out int n) ? n : 0;
        readonly Dictionary<GameLiving, int> _presence = new();
        long _nextWave, _nextAdds, _bossFightFrom;
        long _now;
        int _pathIndex;
        long _rideHoldUntil;                                 // intercept with stops: halted until then
        readonly HashSet<int> _ridesHalted = new();
        long _waitSaidAt;
        Vector3? _leadTo;                            // the giver's party is on its way to this stage's spot
        long _leadNext;
        public double Scale = 1;
        public static bool DEBUG_TRACE = false;      // (the defend stage logs its monsters every 10 s)

        public StageRuntime(ChainRuntime chain, StageDef def, long now)
        {
            Chain = chain;
            Def = def;
            Started = now;
            _now = now;
        }

        int Elapsed => (int) ((_now - Started) / 1000);
        public double RadiusUnits => Def.Radius * 40;
        Point3D CenterPoint => new((int) Center.X, (int) Center.Y, (int) Center.Z);
        Vector3 LeaderSpot => Chain.Leader is EventNpc l ? new Vector3(l.X, l.Y, l.Z) : Vector3.Zero;

        public void Start()
        {
            Center = Def.Type == "escort" && Chain.Leader != null ? LeaderSpot
                : Def.Center != null ? Chain.ToWorld(Def.Center)
                : Chain.Leader != null ? LeaderSpot : Vector3.Zero;
            Scale = ComputeScale();
            switch (Def.Type)
            {
                case "cull":
                    for (int i = 0; i < Def.Alive; i++)
                        SpawnHostile(Pick(Def.Mobs), Chain.Around(Center, RadiusUnits * 0.85), null);
                    break;
                case "defend":
                    if (Def.ProtectLeader && Chain.Leader != null)
                    {
                        // (owner 2026-11-02: the ranger "stood still during the defend the flag portion ... no flag was
                        // placed": the walk was one order a fight could cancel) - kept walking to the spot, then the banner
                        Protect = Chain.Leader;
                        if (Protect.Brain is EventAllyBrain b)
                            b.Steered = true;
                        _leadTo = Center;
                        _leadNext = 0;
                    }
                    else
                        Protect = SpawnNpc(Def.Protect, EventRole.Protect);
                    _nextWave = _now + 8000;
                    break;
                case "boss":
                    Boss = SpawnNpc(Def.Boss, EventRole.Boss);
                    _nextAdds = _now + 1000L * (Def.Adds?.EveryS ?? 30);
                    break;
                case "escort":
                    if (Chain.Leader?.Brain is EventAllyBrain lb)
                        lb.Steered = true;
                    break;
                case "gather":
                    if (Def.Protect != null)
                        Protect = SpawnNpc(Def.Protect, EventRole.Protect);
                    for (int i = 0; i < Def.NodeCount; i++)
                        SpawnNode();
                    for (int i = 0; i < Def.Alive; i++)
                        SpawnHostile(Pick(Def.Mobs), Chain.Around(Center, RadiusUnits * 0.85), null);
                    break;
                case "intercept":
                {
                    Vector3 from = Def.Path.Count > 0 ? Chain.ToWorld(Def.Path[0]) : Center;
                    Boss = SpawnNpc(Def.Boss, EventRole.Boss, from);
                    if (Boss?.Brain is EventMobBrain cart)
                    {
                        cart.AggroLevel = 0;                 // the convoy keeps going: it fights back, it doesn't go looking
                        cart.AggroRange = 0;
                    }
                    _pathIndex = 1;
                    for (int i = 0; Boss != null && i < Def.Alive; i++)
                        if (SpawnHostile(Pick(Def.Mobs), Chain.Around(from, 250), null)?.Brain is EventMobBrain eb)
                            eb.Escort = Boss;
                    break;
                }
                case "clash":
                    MakeSides();
                    for (int i = 0; i < Def.Alive; i++)
                        SpawnSide(i % 2);
                    break;
                case "wards":
                    StartWards();
                    break;
                case "occupy":
                    // (owner 2026-11-02: failed events should have a "real world consequence" - like GW2's Queensdale
                    // bandits taking the pipes: they hold the place, and stay until they are driven out)
                    if (Def.DisplaceM > 0)
                        Chain.Displace(Center, Def.DisplaceM * 40);
                    // the garrison: the full count for a group, three fifths of it for one or two people (they are
                    // dug in and fight at your pace, but all of them is still a wall to a pair)
                    for (int i = 0; i < GarrisonSize(); i++)
                        Garrison(Pick(Def.Mobs));
                    if (Def.Boss != null)
                    {
                        Boss = SpawnNpc(Def.Boss, EventRole.Boss);
                        if (Boss?.Brain is EventMobBrain bb)
                            bb.Post = new Point3D(Boss.X, Boss.Y, Boss.Z);
                    }
                    _nextWave = _now + 1000L * Math.Max(20, Def.ReinforceS);
                    break;
            }
            LeadPartyHere();
            Announce(Def.Announce, true);
            // the bots there say something - and call the zone when there are few hands (AutonomousWorldTalk)
            try { AutonomousWorldTalk.OnEventStage(Chain, this, null); }
            catch (Exception) { }
        }

        public void Tick(long now)
        {
            _now = now;
            if (Boss != null && !Boss.ConLocked && Boss.IsAlive && (Boss.InCombat || (Boss.Brain as StandardMobBrain)?.HasAggro == true))
                EventCons.Lock(Chain, this, Boss);           // its con by who is there as the fight starts
            if (Def.Type == "escort" && Chain.Leader != null)
                Center = LeaderSpot;
            Scale = ComputeScale();
            foreach (GameLiving p in Chain.PeopleNear(CenterPoint, RadiusUnits * 1.3))
                _presence[p] = _presence.TryGetValue(p, out int s) ? s + 1 : 1;
            Spawned.RemoveAll(n => n == null || n.ObjectState == GameObject.eObjectState.Deleted);
            KeepLeading();
            switch (Def.Type)
            {
                case "cull":
                    if (Kills >= Def.Kill) { Outcome = StageOutcome.Success; return; }
                    if (Elapsed >= Def.TimeS) { Outcome = StageOutcome.Fail; return; }
                    int alive = Spawned.Count(n => n.IsAlive && n.Role == EventRole.Hostile);
                    int want = Math.Min((int) Math.Round(Def.Alive * Math.Min(Scale, 2.0)), Def.Kill - Kills);
                    for (int i = alive; i < want; i++)
                        SpawnHostile(Pick(Def.Mobs), Chain.Around(Center, RadiusUnits * 0.85), null);
                    if (alive <= 3)
                        BringStragglers(now);
                    break;
                case "defend":
                    if (DEBUG_TRACE && Elapsed % 10 == 0)
                        foreach (EventNpc h in Spawned.Where(n => n.Role == EventRole.Hostile))
                            DynamicEventManager.Trace($"{h.Name}: {h.GetDistanceTo(Protect) / 40:0} m from {Protect?.Name}, moving {h.IsMoving}, " +
                                $"{(h.Brain as StandardMobBrain)?.FSM?.GetCurrentState()?.StateType}, aggro {(h.Brain as StandardMobBrain)?.HasAggro}, target {h.TargetObject?.Name}");
                    if (Protect == null || !Protect.IsAlive) { Outcome = StageOutcome.Fail; return; }
                    if (Elapsed >= Def.DurationS) { Outcome = StageOutcome.Success; return; }
                    if (Def.Waves != null && now >= _nextWave && Def.DurationS - Elapsed > 10)
                    {
                        _nextWave = now + 1000L * Def.Waves.EveryS;
                        var from = Def.Waves.From.Count > 0 ? Chain.ToWorld(Def.Waves.From[Util.Random(Def.Waves.From.Count - 1)]) : Center;
                        int n = Math.Max(1, (int) Math.Round(Def.Waves.Count * Scale));
                        // a wave waits while the last two are still mostly up: they don't pile up on a group that is
                        // holding but not winning fast (owner 2026-11-02: the siege's second stage overwhelmed a full group)
                        int standing = Spawned.Count(x => x.IsAlive && x.Role == EventRole.Hostile);
                        if (standing >= n * 2)
                            n = 0;
                        for (int i = 0; i < n; i++)
                            SpawnHostile(Pick(Def.Waves.Mobs), Chain.Around(from, 300), Protect);
                    }
                    break;
                case "boss":
                    if (Boss == null || !Boss.IsAlive) { Outcome = StageOutcome.Success; return; }
                    if (Elapsed >= Def.TimeS) { Outcome = StageOutcome.Fail; return; }
                    if (Def.Path.Count > 1 && !Boss.InCombat && (Boss.Brain as StandardMobBrain)?.HasAggro != true)
                        Roam(Boss);                          // a hunt: it walks its range until someone finds it
                    // adds (owner 2026-11-02: "the minute we killed one of them, a few more would spawn in"): the first call
                    // a while into the fight, then every so often, and only while fewer than a call's worth are still up
                    if (Def.Adds != null && Boss.InCombat)
                    {
                        if (_bossFightFrom == 0)
                        {
                            _bossFightFrom = now;
                            _nextAdds = now + 1000L * Math.Max(25, Def.Adds.EveryS / 2);
                        }
                        int cap = Math.Max(1, (int) Math.Round(Def.Adds.Count * Math.Min(Scale, 1.6)));
                        int up = Spawned.Count(x => x.IsAlive && x.Role == EventRole.Hostile);
                        if (now >= _nextAdds && up < cap)
                        {
                            _nextAdds = now + 1000L * Math.Max(60, Def.Adds.EveryS);
                            GameLiving target = Chain.PeopleNear(CenterPoint, RadiusUnits * 1.5).OrderBy(p => p.GetDistanceTo(Boss)).FirstOrDefault();
                            var at = new Vector3(Boss.X, Boss.Y, Boss.Z);
                            for (int i = up; i < cap; i++)
                                SpawnHostile(Pick(Def.Adds.Mobs), Chain.Around(at, 350), target);
                        }
                    }
                    break;
                case "escort":
                    TickEscort();
                    break;
                case "gather":
                {
                    if (Def.Deliver)
                        HandIn();
                    if (Kills >= Def.Kill) { Outcome = StageOutcome.Success; return; }
                    if (Elapsed >= Def.TimeS) { Outcome = StageOutcome.Fail; return; }
                    if (Def.Protect != null && (Protect == null || !Protect.IsAlive)) { Outcome = StageOutcome.Fail; return; }
                    int nodes = Spawned.Count(n => n.IsAlive && n.Role == EventRole.Node);
                    if (nodes < Def.NodeCount && now >= _nextWave)
                    {
                        _nextWave = now + 4000;              // a picked one grows back elsewhere, a few seconds on
                        SpawnNode();
                    }
                    int guards = Spawned.Count(n => n.IsAlive && n.Role == EventRole.Hostile);
                    int wantGuards = (int) Math.Round(Def.Alive * Math.Min(Scale, 2.0));
                    if (guards < wantGuards && now >= _nextAdds)
                    {
                        _nextAdds = now + 20_000;
                        SpawnHostile(Pick(Def.Mobs), Chain.Around(Center, RadiusUnits * 0.85), null);
                    }
                    break;
                }
                case "intercept":
                    TickIntercept();
                    break;
                case "clash":
                {
                    if (Kills >= Def.Kill) { Outcome = StageOutcome.Success; return; }
                    if (Elapsed >= Def.TimeS) { Outcome = StageOutcome.Fail; return; }
                    if (now >= _nextWave)
                    {
                        _nextWave = now + 6000;
                        int perSide = (int) Math.Round(Def.Alive * Math.Min(Scale, 2.0) / 2.0);
                        for (int side = 0; side < 2; side++)
                            if (Spawned.Count(n => n.IsAlive && n.Role == EventRole.Hostile && SideOf(n) == side) < perSide)
                                SpawnSide(side);
                    }
                    break;
                }
                case "wards":
                    TickWards();
                    break;
                case "occupy":
                    int holding = Spawned.Count(n => n.IsAlive && n.IsEnemy);
                    if (holding == 0) { Outcome = StageOutcome.Success; return; }
                    // they dig in: the fallen are replaced, but only while nobody is pressing them
                    if (now >= _nextWave)
                    {
                        _nextWave = now + 1000L * Math.Max(20, Def.ReinforceS);
                        int garrison = Spawned.Count(n => n.IsAlive && n.Role == EventRole.Hostile);
                        if (garrison < GarrisonSize() && !Chain.PeopleNear(CenterPoint, RadiusUnits * 2.5).Any())
                            Garrison(Pick(Def.Mobs));
                    }
                    break;
            }
        }

        int GarrisonSize() => Math.Max(1, (int) Math.Round(Math.Max(1, Def.Count) * Math.Clamp(0.6 + 0.06 * (PeopleHere - 1), 0.6, 1.0)));

        /// <summary>One of an occupation's garrison, at a post in the area that they keep.</summary>
        EventNpc Garrison(MobDef m)
        {
            Vector3 at = Chain.Around(Center, RadiusUnits * 0.8);
            EventNpc npc = SpawnHostile(m, at, null);
            if (npc?.Brain is EventMobBrain b)
                b.Post = new Point3D((int) at.X, (int) at.Y, (int) at.Z);
            return npc;
        }

        /// <summary>The giver walks the path, a point at a time - only while someone is with them, and never in the middle
        /// of a fight; at an ambush point the ambush springs.</summary>
        void TickEscort()
        {
            EventNpc lead = Chain.Leader;
            if (lead == null) { Outcome = StageOutcome.Fail; return; }
            if (Elapsed >= Def.TimeS) { Outcome = StageOutcome.Fail; return; }
            // never in the middle of a fight - and the road is not done until its ambushers are (owner 2026-11-02: the
            // last ambush "spawned and then was just gone instantly": the stage ended on reaching the last point)
            bool fighting = lead.InCombat || (lead.Brain as StandardMobBrain)?.HasAggro == true || Chain.EnemiesNear(lead, 1400).Any()
                || Spawned.Any(n => n.IsAlive && n.Role == EventRole.Hostile);
            if (fighting)
            {
                if (lead.IsMoving && !lead.InCombat)
                    lead.StopMoving();
                return;
            }
            if (_pathIndex >= Def.Path.Count) { Outcome = StageOutcome.Success; return; }
            Vector3 target = Chain.ToWorld(Def.Path[_pathIndex]);
            if (lead.IsWithinRadius(new Point3D((int) target.X, (int) target.Y, (int) target.Z), 200))
            {
                bool sprung = false;
                foreach (AmbushDef a in Def.Ambushes.Where(a => a.At == _pathIndex))
                {
                    sprung = true;
                    if (!string.IsNullOrEmpty(a.Say))
                        NpcSpeech.Say(lead, a.Say);
                    int n = Math.Max(1, (int) Math.Round(a.Count * Math.Min(Scale, 2.0)));
                    for (int i = 0; i < n; i++)
                        SpawnHostile(Pick(a.Mobs), Chain.Around(target, 700), lead);
                }
                _pathIndex++;
                if (sprung)
                {
                    lead.StopMoving();
                    return;
                }
                if (_pathIndex >= Def.Path.Count)
                    return;
                target = Chain.ToWorld(Def.Path[_pathIndex]);
                lead.PathTo(target, EscortSpeed(lead));     // straight on to the next point (no stop at each one)
                return;
            }
            bool company = Chain.PeopleNear(new Point3D(lead.X, lead.Y, lead.Z), 1400).Any();
            if (!company)
            {
                lead.StopMoving();
                if (_now >= _waitSaidAt)                // (once in a while, not every time someone lags a step)
                {
                    _waitSaidAt = _now + 45_000;
                    NpcSpeech.Say(lead, "Don't fall behind - I'll wait for you.", 6000);
                }
                return;
            }
            if (!lead.IsMoving)
                lead.PathTo(target, EscortSpeed(lead));
        }

        /// <summary>A brisk walk (owner 2026-11-02: "a little too slow"): about a player's run, never slower than 170.</summary>
        static short EscortSpeed(GameNPC lead) => (short) Math.Max(170, Math.Min((int) lead.MaxSpeed, 200));

        /// <summary>A giver's party goes where a stage is (a cull or a boss after the march): the giver walks there and
        /// the guards follow; they fight the chain's monsters on the way and at the spot (owner 2026-11-02: the rangers
        /// "did not move at all ... did not help us with the boss").</summary>
        void LeadPartyHere()
        {
            if (Chain.Leader is not EventNpc lead || Def.Type is "escort" or "gather" || (Def.Type == "defend" && Def.ProtectLeader))
                return;                                 // (a gather's giver waits at the edge for what you bring)
            if (lead.Brain is EventAllyBrain b)
                b.Steered = true;
            _leadTo = Chain.Around(Center, Math.Min(RadiusUnits * 0.4, 600));
            _leadNext = 0;
        }

        /// <summary>The leader plants the stage's banner where they stand: it stays until the party goes home.</summary>
        void PlantFlag(EventNpc lead)
        {
            var flag = new GameStaticItem
            {
                Model = (ushort) Def.Flag,
                Name = Def.FlagName ?? $"Banner of {lead.GuildName}",
                X = lead.X + 40, Y = lead.Y, Z = lead.Z, Heading = lead.Heading, CurrentRegion = lead.CurrentRegion
            };
            if (flag.AddToWorld())
                Chain.Lingering.Add((flag, long.MaxValue));
            NpcSpeech.Say(lead, "The banner stands! Hold here - don't let them reach it!");
        }

        void KeepLeading()
        {
            if (_leadTo is not Vector3 to || Chain.Leader is not EventNpc lead || _now < _leadNext)
                return;
            _leadNext = _now + 3000;
            if (lead.IsWithinRadius(new Point3D((int) to.X, (int) to.Y, (int) to.Z), 250))
            {
                _leadTo = null;                         // there: they stand and fight (the brain still takes on foes)
                if (Def.Flag > 0 && lead == Protect)
                    PlantFlag(lead);
                return;
            }
            if (!lead.InCombat && (lead.Brain as StandardMobBrain)?.HasAggro != true && !lead.IsMoving)
                lead.PathTo(to, EscortSpeed(lead));
        }

        /// <summary>The stage is over: rewards on a win, its text to the zone, its leftovers taken away.</summary>
        public void Finish(bool won)
        {
            if (Outcome == StageOutcome.None)
                Outcome = won ? StageOutcome.Success : StageOutcome.Fail;
            if (won && Def.Reward != null)
                GiveRewards();
            string text = won ? Def.Success : Def.Fail;
            if (!string.IsNullOrEmpty(text))
                Announce(text, false);
            try { AutonomousWorldTalk.OnEventStage(Chain, this, Outcome == StageOutcome.Success); }
            catch (Exception) { }
            foreach (EventNpc n in Spawned.ToList())
            {
                n.Stage = null;
                if (won && n == Protect && n.IsAlive && n.Role == EventRole.Protect && !Chain.Quiet)
                {
                    NpcSpeech.Say(n, Def.Thanks ?? "Thank you - I'd never have lived through that on my own.");
                    Chain.Lingering.Add((n, _now + 20_000));
                    continue;
                }
                if (n.IsAlive && n.ObjectState == GameObject.eObjectState.Active)
                    n.RemoveFromWorld();
            }
            Spawned.Clear();
            ClearWards();
            if (Chain.Leader?.Brain is EventAllyBrain lb)
                lb.Steered = false;
            foreach (EventNpc ally in Chain.Guards.Append(Chain.Leader).Where(a => a != null && a.IsAlive))
                if (ally.Brain is StandardMobBrain ab)
                {
                    ab.ClearAggroList();
                    ally.attackComponent?.StopAttack();
                    ab.FSM?.SetCurrentState(eFSMStateType.IDLE);
                }
        }

        // ---------------------------------------------------------------- progress (the tracker)

        public double Progress => Def.Type switch
        {
            "cull" => Math.Min(1.0, Kills / (double) Math.Max(1, Def.Kill)),
            "defend" => Math.Min(1.0, Elapsed / (double) Math.Max(1, Def.DurationS)),
            "boss" => Boss == null ? 1.0 : 1.0 - Boss.Health / (double) Math.Max(1, Boss.MaxHealth),
            "escort" => Math.Min(1.0, _pathIndex / (double) Math.Max(1, Def.Path.Count)),
            "occupy" => 1.0 - Math.Min(1.0, Spawned.Count(n => n.IsAlive && n.IsEnemy) / (double) Math.Max(1, Def.Count + (Def.Boss != null ? 1 : 0))),
            "gather" or "clash" => Math.Min(1.0, Kills / (double) Math.Max(1, Def.Kill)),
            "intercept" => Math.Min(1.0, _pathIndex / (double) Math.Max(1, Def.Path.Count)),
            "wards" => _wards.Count == 0 ? 0 : Math.Min(1.0, (_wards.Count(w => w.Held) +
                (_allHeldSince > 0 ? Math.Min(1.0, (_now - _allHeldSince) / (1000.0 * Math.Max(1, Def.HoldS))) : 0)) / (_wards.Count + 1.0)),
            _ => 0
        };

        public int TimeLeft => Def.Type == "occupy" ? 0 : Math.Max(0, (Def.Type == "defend" ? Def.DurationS : Def.TimeS) - Elapsed);

        public string ProgressLine => Def.Type switch
        {
            "cull" => $"{Kills} / {Def.Kill} defeated",
            "defend" => Protect != null ? $"{Protect.Name}: {Protect.HealthPercent}% health" : "",
            "boss" => Boss != null ? $"{Boss.Name}: {Boss.HealthPercent}% health" : "",
            "escort" => Chain.Leader != null ? $"{Chain.Leader.Name}: {Chain.Leader.HealthPercent}% health" : "",
            "occupy" => $"{Spawned.Count(n => n.IsAlive && n.IsEnemy)} still hold it" + (Boss != null && Boss.IsAlive ? $" - {Boss.Name} among them" : ""),
            "gather" => $"{Kills} / {Def.Kill} {(Def.Deliver ? "delivered" : "gathered")}" + (Protect != null ? $" - {Protect.Name}: {Protect.HealthPercent}%" : ""),
            "clash" => $"{Kills} / {Def.Kill} defeated",
            "intercept" => Boss != null ? $"{Boss.Name}: {Boss.HealthPercent}% health - {Math.Max(0, Def.Path.Count - _pathIndex)} legs from safety" : "",
            "wards" => _allHeldSince > 0
                ? $"All {_wards.Count} wards held - {Math.Max(0, Def.HoldS - (int) ((_now - _allHeldSince) / 1000))} s more"
                : $"Wards held: {_wards.Count(w => w.Held)} / {_wards.Count}" + (_wards.Any(w => !w.Held) ? $" ({string.Join(", ", _wards.Where(w => !w.Held).Select(w => w.Name))} still theirs)" : ""),
            _ => ""
        };

        // ---------------------------------------------------------------- spawning (scaled to who is here)

        int MobLevel(int[] range)
        {
            int lo = range == null || range.Length == 0 ? 1 : range[0];
            int hi = range == null || range.Length < 2 ? lo : range[1];
            // the event's own level, always (owner 2026-11-02: an event "scaled up" to a level-42 bot was too hard for the
            // lower players there - higher people are scaled down instead: gameutils/LevelScaling.cs)
            return Util.Random(lo, hi);
        }

        static MobDef Pick(List<MobDef> mobs) => mobs[Util.Random(mobs.Count - 1)];

        readonly Dictionary<EventNpc, long> _quietSince = new();
        long _nextStraggler;

        /// <summary>The last few of a cull that nobody has fought for a minute - one that came up in a hole, under the
        /// ground or behind a wall - are brought out near the people fighting (owner 2026-11-23, Bugs & Fixes: the
        /// Spraggon Warren "only spawned 11 of the 12 spraggons ... Me or the bots couldn't find the last one").</summary>
        void BringStragglers(long now)
        {
            if (now < _nextStraggler)
                return;
            _nextStraggler = now + 5000;
            var people = Chain.PeopleNear(CenterPoint, RadiusUnits * 1.6).ToList();
            if (people.Count == 0)
                return;
            foreach (EventNpc n in Spawned.Where(n => n.IsAlive && n.Role == EventRole.Hostile).ToList())
            {
                if (n.InCombat || (n.Brain as StandardMobBrain)?.HasAggro == true || !_quietSince.TryGetValue(n, out long since))
                {
                    _quietSince[n] = now;
                    continue;
                }
                if (now - since < 60_000)
                    continue;
                GameLiving near = people.OrderBy(p => p.GetDistanceTo(n)).First();
                Vector3 at = Chain.Around(new Vector3(near.X, near.Y, near.Z), 500);
                n.MoveTo(n.CurrentRegionID, (int) at.X, (int) at.Y, (int) at.Z, n.Heading);
                n.SpawnPoint = new Point3D((int) at.X, (int) at.Y, (int) at.Z);
                _quietSince[n] = now;
            }
        }

        EventNpc SpawnHostile(MobDef m, Vector3 at, GameLiving target)
        {
            if (m == null)
                return null;
            var npc = Chain.Make(m.Template, m.Name, MobLevel(m.Level), m.Model, m.Size, m.Equipment, m.Guild, at, EventRole.Hostile, this);
            if (npc == null)
                return null;
            Spawned.Add(npc);
            if (Chain.Toughness > 1.001)
            {
                npc.HealthMult *= Chain.Toughness;       // (a siege's enemy grown bolder: ZoneSiege)
                npc.Health = npc.MaxHealth;
            }
            // (an elite garrison, health_mult over 1: a con up instead - EventCons.Apply)
            if (target != null && npc.Brain is EventMobBrain brain)
                brain.Goal = target;
            return npc;
        }

        EventNpc SpawnNpc(NpcDef d, EventRole role, Vector3? where = null)
        {
            if (d == null)
                return null;
            Vector3 at = where ?? (d.Pos != null ? Chain.ToWorld(d.Pos) : Center);
            int level = d.Level;
            var npc = Chain.MakeNpc(d, role, at, level, this);
            if (npc == null)
                return null;
            Spawned.Add(npc);
            // a boss's toughness is its con now, by head count (EventCons, owner 2026-11-22) - the file's health_mult
            // was tuned against the old levels, so it counts only for the people an event keeps alive
            npc.HealthMult = role == EventRole.Boss ? npc.ConHealth : Math.Max(1, Math.Min(3.0, d.HealthMult));
            if (npc.IsEnemy && Chain.Toughness > 1.001)
                npc.HealthMult *= Chain.Toughness;
            npc.Health = npc.MaxHealth;
            return npc;
        }

        // ---------------------------------------------------------------- gather, intercept, clash, hunt

        /// <summary>A thing to pick up (a glowcap, a sheaf of stolen grain): peaceful, still, somewhere in the area.</summary>
        void SpawnNode()
        {
            if (Def.Nodes.Count == 0)
                return;
            MobDef m = Pick(Def.Nodes);
            var npc = Chain.Make(m.Template, m.Name, 1, m.Model, m.Size, null, m.Guild ?? "", Chain.Around(Center, RadiusUnits * 0.9),
                EventRole.Node, this);
            if (npc == null)
                return;
            npc.Flags |= GameNPC.eFlags.PEACE;
            Spawned.Add(npc);
        }

        /// <summary>A node picked: it counts for whoever picked it, it goes, and now and then a guardian jumps out.</summary>
        public void OnGathered(EventNpc node, GamePlayer player)
        {
            if (Outcome != StageOutcome.None || node.Role != EventRole.Node || !node.IsAlive || !player.IsWithinRadius(node, 300))
                return;
            if (Def.Deliver && Chain.Leader != null)
            {
                int carrying = _carried[player] = Carried(player) + 1;
                player.Out.SendMessage($"You pick {node.Name}. You carry {carrying} - bring them to {Chain.Leader.Name}.", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
            else
            {
                Kills++;
                _credit[player] = (_credit.TryGetValue(player, out double c) ? c : 0) + 200;
                player.Out.SendMessage(Def.Gathered ?? $"You gather {node.Name}. ({Kills}/{Def.Kill})", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
            Spawned.Remove(node);
            node.RemoveFromWorld();
            if (Def.Mobs.Count > 0 && Util.Chance(Def.AmbushChance))
                SpawnHostile(Pick(Def.Mobs), Chain.Around(new Vector3(player.X, player.Y, player.Z), 300), player);
        }

        /// <summary>Gather + deliver: whoever carries some and stands by the giver hands them in - they count now.</summary>
        void HandIn()
        {
            EventNpc giver = Chain.Leader;
            if (giver == null)
                return;
            foreach (GamePlayer p in _carried.Where(kv => kv.Value > 0).Select(kv => kv.Key).ToList())
            {
                if (p.ObjectState != GameObject.eObjectState.Active || p.CurrentRegion != giver.CurrentRegion || !p.IsWithinRadius(giver, DeliverReach))
                    continue;
                int n = _carried[p];
                _carried[p] = 0;
                Kills += n;
                _credit[p] = (_credit.TryGetValue(p, out double c) ? c : 0) + 200 * n;
                p.Out.SendMessage($"You hand {giver.Name} {n}. ({Math.Min(Kills, Def.Kill)}/{Def.Kill})", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                NpcSpeech.SayTo(giver, p, Kills >= Def.Kill ? "That's the lot - wonderful!" : "Lovely. More, if you can find them!");
            }
        }

        /// <summary>The convoy walks its road, a point at a time, stopping only to fight; it wins if it gets there.</summary>
        void TickIntercept()
        {
            if (Boss == null || !Boss.IsAlive) { Outcome = StageOutcome.Success; return; }
            if (Elapsed >= Def.TimeS || _pathIndex >= Def.Path.Count && Boss.IsWithinRadius(new Point3D(
                    (int) Chain.ToWorld(Def.Path[^1]).X, (int) Chain.ToWorld(Def.Path[^1]).Y, (int) Chain.ToWorld(Def.Path[^1]).Z), 250))
            {
                Outcome = StageOutcome.Fail;
                return;
            }
            Center = new Vector3(Boss.X, Boss.Y, Boss.Z);
            if (Environment.TickCount64 < _rideHoldUntil)
                return;                                      // a ride's halt: his host is down off their horses
            if (Boss.InCombat || (Boss.Brain as StandardMobBrain)?.HasAggro == true)
                return;
            if (_pathIndex >= Def.Path.Count)
                _pathIndex = Def.Path.Count - 1;
            Vector3 to = Chain.ToWorld(Def.Path[_pathIndex]);
            if (Boss.IsWithinRadius(new Point3D((int) to.X, (int) to.Y, (int) to.Z), 200))
            {
                int stop = Def.Stops.IndexOf(_pathIndex);
                if (stop >= 0 && _ridesHalted.Add(_pathIndex))
                {
                    _rideHoldUntil = Environment.TickCount64 + Def.StopS * 1000L;
                    Boss.StopMoving();
                    Announce(stop < Def.StopSays.Count ? Def.StopSays[stop] : $"{Boss.Name} halts, and his host comes down round him!", false);
                    for (int i = 0; i < Def.StopCount && Def.Mobs.Count > 0; i++)
                        SpawnHostile(Pick(Def.Mobs), Chain.Around(new Vector3(Boss.X, Boss.Y, Boss.Z), 200), null);
                    return;
                }
                if (_pathIndex < Def.Path.Count - 1)
                    _pathIndex++;
                else
                    _pathIndex = Def.Path.Count;             // there: the next tick calls it lost
                return;
            }
            if (!Boss.IsMoving)
                Boss.PathTo(to, (short) Math.Max(60, Def.Speed));
        }

        /// <summary>A roaming boss walks its path round and round while nobody fights it.</summary>
        void Roam(EventNpc boss)
        {
            Vector3 to = Chain.ToWorld(Def.Path[_pathIndex % Def.Path.Count]);
            if (boss.IsWithinRadius(new Point3D((int) to.X, (int) to.Y, (int) to.Z), 200))
            {
                _pathIndex = (_pathIndex + 1) % Def.Path.Count;
                return;
            }
            if (!boss.IsMoving)
                boss.PathTo(to, (short) Math.Max(60, Def.Speed));
        }

        readonly Faction[] _sides = new Faction[2];

        /// <summary>Two sides that fight each other on sight (and anyone who comes in among them).</summary>
        void MakeSides()
        {
            for (int s = 0; s < 2; s++)
            {
                var f = new Faction();
                f.LoadFromDatabase(new DbFaction { ID = 9900 + s, Name = $"{Chain.Def.Id}:{s}", BaseAggroLevel = 100 });
                _sides[s] = f;
            }
            _sides[0].EnemyFactions.Add(_sides[1]);
            _sides[1].EnemyFactions.Add(_sides[0]);
        }

        int SideOf(EventNpc n) => n.Faction == _sides[1] ? 1 : 0;

        void SpawnSide(int side)
        {
            var mine = Def.Mobs.Where(m => m.Side == side).ToList();
            if (mine.Count == 0)
                return;
            // each side comes in from its own half of the area, and they meet in the middle
            double a = side == 0 ? Math.PI : 0;
            var from = new Vector3((float) (Center.X + Math.Cos(a) * RadiusUnits * 0.6), (float) (Center.Y + Math.Sin(a) * RadiusUnits * 0.6), Center.Z);
            EventNpc npc = SpawnHostile(Pick(mine), Chain.Around(from, RadiusUnits * 0.35), null);
            if (npc != null)
                npc.Faction = _sides[side];
        }

        // ---------------------------------------------------------------- wards (a siege's second stage)

        sealed class Ward
        {
            public Vector3 At;
            public string Name;
            public bool Held;
            public long NextPush;
            public GameStaticItem Banner;
        }

        readonly List<Ward> _wards = new();
        long _allHeldSince;

        double WardUnits => Math.Max(8, Def.WardRadius) * 40;

        /// <summary>Each ward: its keeper (the stage's Boss) and Alive of its guards, round the stone.</summary>
        void StartWards()
        {
            for (int i = 0; i < Def.Wards.Count; i++)
            {
                var w = new Ward
                {
                    At = Chain.ToWorld(Def.Wards[i]),
                    Name = i < Def.WardNames.Count ? Def.WardNames[i] : (i == 0 ? "first" : i == 1 ? "second" : i == 2 ? "third" : $"ward {i + 1}")
                };
                _wards.Add(w);
                if (Def.Boss != null)
                {
                    EventNpc keeper = SpawnNpc(Def.Boss, EventRole.Hostile, Chain.Around(w.At, WardUnits * 0.3));
                    if (keeper?.Brain is EventMobBrain kb)
                        kb.Post = new Point3D((int) w.At.X, (int) w.At.Y, (int) w.At.Z);
                }
                for (int k = 0; k < Def.Alive; k++)
                {
                    Vector3 at = Chain.Around(w.At, WardUnits * 0.8);
                    if (SpawnHostile(Pick(Def.Mobs), at, null)?.Brain is EventMobBrain gb)
                        gb.Post = new Point3D((int) at.X, (int) at.Y, (int) at.Z);
                }
            }
        }

        /// <summary>A ward is ours when none of its guards stand at it and one of us does; theirs again when they come
        /// back and none of us is there. Every ward held at once, for HoldS: won. While a ward is ours they push back
        /// at it (fewer while they still have people standing there).</summary>
        void TickWards()
        {
            if (Elapsed >= Def.TimeS) { Outcome = StageOutcome.Fail; return; }
            foreach (Ward w in _wards)
            {
                var spot = new Point3D((int) w.At.X, (int) w.At.Y, (int) w.At.Z);
                int foes = Spawned.Count(n => n.IsEnemy && n.IsAlive && n.IsWithinRadius(spot, (int) (WardUnits * 1.2)));
                bool ours = Chain.PeopleNear(spot, WardUnits).Any();
                if (!w.Held && foes == 0 && ours)
                {
                    w.Held = true;
                    w.NextPush = _now + 1000L * Math.Max(20, Def.ReinforceS);
                    w.Banner = new GameStaticItem
                    {
                        Model = (ushort) (Def.Flag > 0 ? Def.Flag : 466), Name = Def.FlagName ?? "Hibernian banner",
                        X = (int) w.At.X, Y = (int) w.At.Y, Z = (int) w.At.Z, CurrentRegion = Chain.Region
                    };
                    if (!w.Banner.AddToWorld())
                        w.Banner = null;
                    Announce($"The {w.Name} ward is ours! ({_wards.Count(x => x.Held)} of {_wards.Count})", false);
                }
                else if (w.Held && foes > 0 && !ours)
                {
                    w.Held = false;
                    if (w.Banner?.ObjectState == GameObject.eObjectState.Active)
                        w.Banner.RemoveFromWorld();
                    w.Banner = null;
                    Announce($"They have taken back the {w.Name} ward!", false);
                }
                if (w.Held && _now >= w.NextPush)
                {
                    w.NextPush = _now + 1000L * Math.Max(20, Def.ReinforceS);
                    int n = Math.Max(1, (int) Math.Round(2 * Math.Min(Scale, 2.0)));
                    if (foes < n * 2)
                    {
                        double a = Util.RandomDouble() * Math.PI * 2;
                        var from = new Vector3(w.At.X + (float) (Math.Cos(a) * WardUnits * 3), w.At.Y + (float) (Math.Sin(a) * WardUnits * 3), w.At.Z);
                        GameLiving at = Chain.PeopleNear(spot, WardUnits * 1.5).FirstOrDefault();
                        for (int i = 0; i < n; i++)
                            SpawnHostile(Pick(Def.Mobs), Chain.Around(from, 250), at);
                    }
                }
            }
            if (_wards.Count > 0 && _wards.All(w => w.Held))
            {
                if (_allHeldSince == 0)
                {
                    _allHeldSince = _now;
                    Announce($"Every ward is ours - hold them for {Def.HoldS} seconds!", false);
                }
                else if (_now - _allHeldSince >= 1000L * Math.Max(1, Def.HoldS))
                    Outcome = StageOutcome.Success;
            }
            else
                _allHeldSince = 0;
        }

        void ClearWards()
        {
            foreach (Ward w in _wards)
                if (w.Banner?.ObjectState == GameObject.eObjectState.Active)
                    w.Banner.RemoveFromWorld();
            _wards.Clear();
        }

        // ---------------------------------------------------------------- who took part

        static GameLiving Credit(GameObject source)
        {
            if (source is GameNPC { Brain: IControlledBrain cb } && cb.GetLivingOwner() is GameLiving owner)
                return owner;
            return source as GameLiving;
        }

        public void OnDamaged(EventNpc npc, GameObject source, int amount)
        {
            if (!npc.IsEnemy || amount <= 0)
                return;
            GameLiving who = Credit(source);
            if (who is GamePlayer || who is GameBot)
                _credit[who] = (_credit.TryGetValue(who, out double c) ? c : 0) + amount;
        }

        public void OnDied(EventNpc npc, GameObject killer)
        {
            if (!npc.IsEnemy)
                return;
            GameLiving who = Credit(killer);
            if (npc.Role == EventRole.Hostile && (Def.Type != "clash" || who is GamePlayer || who is GameBot))
                Kills++;
            if (who is GamePlayer || who is GameBot)
                _credit[who] = (_credit.TryGetValue(who, out double c) ? c : 0) + npc.MaxHealth * 0.1;
        }

        /// <summary>How many more come with more people (owner 2026-11-02, the Bri Leith tower siege with a full group:
        /// "way too many enemies spawned ... if one person tries to take it on, they will be overwhelmed. But a full group
        /// should be able to take care of it with only little difficulty, and a half group it would be a challenge but
        /// doable"): the base counts are for one or two; four people see about half as many again, eight twice as many,
        /// never more - a group's healing and crowd control grow faster than its head count.</summary>
        double ComputeScale()
        {
            int people = Chain.PeopleNear(CenterPoint, RadiusUnits * 1.5).Count();
            return Math.Min(2.0, 1.0 + 0.15 * Math.Max(0, people - 1));
        }

        /// <summary>The people here, for the stages whose numbers go by head count rather than the scale.</summary>
        public int PeopleHere => Chain.PeopleNear(CenterPoint, RadiusUnits * 1.5).Count();
        public int PlayersHere => Math.Max(1, Chain.PeopleNear(CenterPoint, RadiusUnits * 1.5).Count(p => p is GamePlayer));

        /// <summary>Gold, silver or bronze by share of the work (damage dealt to the event's monsters, kills), bronze for
        /// being there; experience as a share of your level, money by your level, and the stage's items by chance - each
        /// at your level where it has level versions. Bots are paid as players are.</summary>
        void GiveRewards()
        {
            var people = new HashSet<GameLiving>(_presence.Where(kv => kv.Value >= 15).Select(kv => kv.Key));
            foreach (GameLiving who in _credit.Keys)
                people.Add(who);
            double best = _credit.Count > 0 ? _credit.Values.Max() : 0;
            RewardDef r = Def.Reward;
            var items = new List<ItemRewardDef>(r.Items ?? new List<ItemRewardDef>());
            if (r.Item != null)
                items.Add(r.Item);
            foreach (GameLiving who in people)
            {
                if (who.ObjectState != GameObject.eObjectState.Active || who.CurrentRegion != Chain.Region)
                    continue;
                double c = _credit.TryGetValue(who, out double v) ? v : 0;
                int tier = best > 0 && c >= best * 0.5 ? 3 : best > 0 && c >= best * 0.15 ? 2 : 1;
                double mult = tier == 3 ? 1.0 : tier == 2 ? 0.7 : 0.4;
                string medal = tier == 3 ? "Gold" : tier == 2 ? "Silver" : "Bronze";
                DOL.GS.Reputation.ReputationService.OnEventStage(who, Chain, tier);   // the event's faction (scripts/reputation)
                long levelXp = who.Level > 1
                    ? GamePlayer.GetExperienceAmountForLevel(who.Level) - GamePlayer.GetExperienceAmountForLevel(who.Level - 1)
                    : GamePlayer.GetExperienceAmountForLevel(1);
                long xp = (long) (Math.Max(0, levelXp) * r.XpPct / 100.0 * mult);
                xp = (long) (xp * ZoneRates.EventFactor(who, $"{Chain.Def.Title}/{Def.Name}"));   // first time today: 1.5x (ZoneRates)
                long copper = (long) (r.CopperPerLevel * who.Level * mult);
                if (who is GameBot bot)
                {
                    if (xp > 0 && bot.Level < 50)
                        bot.GainExperience(new GainedExperienceEventArgs(xp, 0, 0, 0, 0, 0, false, false, eXPSource.Quest));
                    if (copper > 0)
                        AutonomousBotEconomy.AddMoney(bot.DatabaseID, copper);
                    continue;
                }
                if (who is not GamePlayer p)
                    continue;
                p.Out.SendMessage($"{Chain.Def.Title}: {Def.Name} complete - {medal} contribution.", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                int marks = (int) Math.Round((r.Tokens > 0 ? r.Tokens : Math.Max(1, r.XpPct / 4)) * mult);
                if (marks > 0 && GameServer.Database.FindObjectByKey<DbItemTemplate>(EventTokenMerchant.MarkId) is DbItemTemplate mark)
                {
                    DbInventoryItem m = GameInventoryItem.Create(mark);
                    if (p.Inventory.AddTemplate(m, marks, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                    {
                        p.Out.SendMessage($"You receive {marks} {mark.Name}{(marks > 1 ? "s" : "")}.", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                        LootFeed.Item(p, mark, marks);
                    }
                }
                if (xp > 0 && p.Level < 50)
                    p.GainExperience(eXPSource.Quest, xp, false);
                if (copper > 0)
                {
                    p.AddMoney(copper, "You are rewarded {0}.");
                    LootFeed.Money(p, copper);
                }
                foreach (ItemRewardDef it in items)
                {
                    if (string.IsNullOrEmpty(it.Id))
                        continue;
                    int chance = tier == 3 ? it.GoldChance : tier == 2 ? it.SilverChance : 0;
                    if (chance <= 0 || !Util.Chance(chance) || ItemAtLevel(it.Id, p.Level) is not DbItemTemplate tpl)
                        continue;
                    tpl = SpecialLoot.Enrich(tpl, p, $"{Chain.Def.Title}: {Def.Name}");   // ToA stats, a proc, a glow, for their class
                    DbInventoryItem item = GameInventoryItem.Create(tpl);
                    if (!p.Inventory.AddTemplate(item, 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                        p.CreateItemOnTheGround(item);
                    p.Out.SendMessage($"You receive {tpl.Name}!", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                    LootFeed.Item(p, tpl, 1);
                }
            }
        }

        /// <summary>An event item at the taker's level: its level version (<id>_lNN, in fives - named_uniques.py makes them)
        /// at or below your level, else the item itself.</summary>
        public static DbItemTemplate ItemAtLevel(string id, int level)
        {
            for (int l = Math.Min(50, level) / 5 * 5; l >= 5; l -= 5)
                if (GameServer.Database.FindObjectByKey<DbItemTemplate>($"{id}_l{l}") is DbItemTemplate v)
                    return v;
            return GameServer.Database.FindObjectByKey<DbItemTemplate>(id);
        }

        void Announce(string text, bool start)
        {
            if (string.IsNullOrEmpty(text) || Chain.Quiet)
                return;
            foreach (GamePlayer p in Chain.PlayersInZone())
            {
                if (start)
                    p.Out.SendMessage($"{Chain.Def.Title}: {Def.Name}", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                p.Out.SendMessage(text, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
        }
    }
}
