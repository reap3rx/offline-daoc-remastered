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
    public enum EventRole { Hostile, Protect, Boss, Ally, Giver }

    /// <summary>A monster or NPC of an event: credits damage to its stage, tells it when it dies; a giver talks.</summary>
    public class EventNpc : GameNPC
    {
        public ChainRuntime Chain;
        public StageRuntime Stage;
        public EventRole Role;
        public double HealthMult = 1;

        public bool IsEnemy => Role is EventRole.Hostile or EventRole.Boss;
        public override int MaxHealth => (int) Math.Max(1, base.MaxHealth * HealthMult);
        public override bool CanDropLoot => Role == EventRole.Boss;

        public override void TakeDamage(GameObject source, eDamageType damageType, int damageAmount, int criticalAmount)
        {
            base.TakeDamage(source, damageType, damageAmount, criticalAmount);
            Stage?.OnDamaged(this, source, damageAmount + criticalAmount);
        }

        public override void ProcessDeath(GameObject killer)
        {
            Stage?.OnDied(this, killer);
            base.ProcessDeath(killer);
        }

        public override bool Interact(GamePlayer player)
        {
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

        public override void Think()
        {
            if (Body == null || !Body.IsAlive)
            {
                base.Think();
                return;
            }
            Body.SpawnPoint = new Point3D(Body.X, Body.Y, Body.Z);
            if (Goal != null && (!Goal.IsAlive || Goal.ObjectState != GameObject.eObjectState.Active || Goal.CurrentRegion != Body.CurrentRegion))
                Goal = null;
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
                EventNpc foe = me.Chain.EnemiesNear(me, 1600).OrderBy(n => n.GetDistanceTo(me)).FirstOrDefault()
                    ?? (Follow != null && Follow.IsAlive ? me.Chain.EnemiesNear(Follow, 1200).OrderBy(n => n.GetDistanceTo(Follow)).FirstOrDefault() : null);
                if (foe != null)
                {
                    AddToAggroList(foe, 100);
                    FSM.SetCurrentState(eFSMStateType.AGGRO);
                }
                else if (!Steered && Follow != null && Follow.IsAlive && !Body.IsWithinRadius(Follow, 260))
                {
                    if (!Body.IsMoving)
                        Body.PathTo(new Vector3(Follow.X, Follow.Y, Follow.Z), Body.MaxSpeed);
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
        public string LastOutcome = "";              // shown on the map a little while after it ends
        public long LastOutcomeUntil;
        public EventNpc Giver;
        public readonly List<EventNpc> Guards = new();
        public long GiverReadyAt;
        public ushort GiverHeading;
        bool _running;                               // between Begin and End (stages and rests)

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
            ClientService.Instance.GetPlayers().Where(p => p.CurrentRegion == Region && p.CurrentZone == Zone);

        /// <summary>Players and bots (they take part as players do) within r units of p.</summary>
        public IEnumerable<GameLiving> PeopleNear(Point3D p, double r)
        {
            ushort ur = (ushort) Math.Min(65000, r);
            foreach (GamePlayer pl in Region.GetPlayersInRadius(p, ur))
                if (pl.IsAlive && pl.ObjectState == GameObject.eObjectState.Active)
                    yield return pl;
            foreach (GameNPC n in Region.GetNPCsInRadius(p, ur))
                if (n is GameBot b && b.IsAlive)
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

        /// <summary>Where a waiting disturbance is, and how near wakes it.</summary>
        public Vector3 WakePoint => ToWorld(Def.Stages.First(s => s.Id == Def.Start).Center, false);
        public double WakeUnits => (Def.WakeM > 0 ? Def.WakeM : Def.Stages.First(s => s.Id == Def.Start).Radius + 60) * 40;

        public IEnumerable<EventNpc> EnemiesNear(GameObject at, double r) =>
            (Stage?.Spawned ?? Enumerable.Empty<EventNpc>()).Where(n => n.IsEnemy && n.IsAlive && at.IsWithinRadius(n, (int) r)).ToList();

        public void Tick(long now)
        {
            if (Def.Giver != null)
                KeepGiver(now);
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
                    if (now < NextStart)
                        return;
                    if (!AnyoneInZone())
                    {
                        NextStart = now + 60_000;           // nobody about: look again in a minute
                        return;
                    }
                    Dormant = true;                         // a disturbance: it waits for someone to come
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
            Stage = null;
            string next = won ? done.OnSuccess : done.OnFail;
            if (!string.IsNullOrEmpty(next) && next != "end" && Def.Stages.Any(s => s.Id == next))
            {
                PendingId = next;                           // a breather: sit, heal, gather up
                PendingAt = now + 1000L * Math.Max(3, Def.RestS);
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
            Stage = new StageRuntime(this, sd, now);
            Stage.Start();
        }

        public void End(string outcome, long now)
        {
            Stage?.Finish(false);
            Stage = null;
            PendingId = null;
            Dormant = false;
            _running = false;
            LastOutcome = outcome;
            LastOutcomeUntil = now + 30_000;
            NextStart = now + 1000L * Util.Random(Def.IntervalS[0], Def.IntervalS[Math.Min(1, Def.IntervalS.Length - 1)]);
            if (Def.Giver != null)
                ComeHome(now);
        }

        // ---------------------------------------------------------------- the giver and their party

        void KeepGiver(long now)
        {
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
            int lvl = Math.Max(Def.Giver.Level, StageRuntime.TargetLevelAround(this, new Point3D(Giver.X, Giver.Y, Giver.Z), 1500));
            foreach (NpcDef gd in Def.Guards)
                for (int i = 0; i < Math.Max(1, gd.Count); i++)
                {
                    var at = Around(new Vector3(Giver.X, Giver.Y, Giver.Z), 250);
                    EventNpc g = MakeNpc(gd, EventRole.Ally, at, Math.Max(gd.Level, lvl - 1));
                    if (g == null)
                        continue;
                    g.HealthMult = Math.Max(1, gd.HealthMult);
                    g.Health = g.MaxHealth;
                    ((EventAllyBrain) g.Brain).Follow = Giver;
                    Guards.Add(g);
                }
            if (Giver.Level < lvl)
            {
                Giver.Level = (byte) lvl;
                Giver.Health = Giver.MaxHealth;
            }
            if (Giver.Brain is EventAllyBrain b)
                b.Home = null;
        }

        /// <summary>The chain is over: the guards go back to the garrison, the giver walks back to their post (or, fallen,
        /// is back there after the cooldown).</summary>
        void ComeHome(long now)
        {
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
                if (role == EventRole.Protect)
                    npc.SetOwnBrain(new BlankBrain());
                else
                    npc.SetOwnBrain(new EventAllyBrain { AggroLevel = 0, AggroRange = 0 });
            }
            if (role == EventRole.Giver && Def.Giver?.Pos != null && Def.Giver.Pos.Length > 3)
                npc.Heading = (ushort) Def.Giver.Pos[3];
            if (!npc.AddToWorld())
                return null;
            npc.SpawnPoint = new Point3D(npc.X, npc.Y, npc.Z);
            npc.Health = npc.MaxHealth;
            return npc;
        }

        // ---------------------------------------------------------------- places

        /// <summary>Zone metres (the client's) to region units; z by the file's height, then the navmesh's floor.</summary>
        public Vector3 ToWorld(double[] p, bool snap = true)
        {
            var v = new Vector3((float) (Zone.XOffset + p[0] * 40), (float) (Zone.YOffset + p[1] * 40),
                p.Length > 2 ? (float) (p[2] * 40) : 0f);
            return snap ? Snap(v) : v;
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
        readonly Dictionary<GameLiving, int> _presence = new();
        long _nextWave, _nextAdds, _bossFightFrom;
        long _now;
        int _pathIndex;
        long _waitSaidAt;
        Vector3? _leadTo;                            // the giver's party is on its way to this stage's spot
        long _leadNext;
        public double Scale = 1;
        public int TargetLevel;                      // the level of the people here: the stage's monsters scale up to it
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
            TargetLevel = TargetLevelAround(Chain, CenterPoint, RadiusUnits * 1.5 + 2400);
            switch (Def.Type)
            {
                case "cull":
                    for (int i = 0; i < Def.Alive; i++)
                        SpawnHostile(Pick(Def.Mobs), Chain.Around(Center, RadiusUnits * 0.85), null);
                    break;
                case "defend":
                    if (Def.ProtectLeader && Chain.Leader != null)
                    {
                        Protect = Chain.Leader;
                        if (Protect.Brain is EventAllyBrain b)
                            b.Steered = true;
                        Protect.PathTo(Center, (short) Math.Max(120, Protect.MaxSpeed * 0.8));
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
            }
            LeadPartyHere();
            Announce(Def.Announce, true);
        }

        public void Tick(long now)
        {
            _now = now;
            if (Def.Type == "escort" && Chain.Leader != null)
                Center = LeaderSpot;
            Scale = ComputeScale();
            TargetLevel = Math.Max(TargetLevel, TargetLevelAround(Chain, CenterPoint, RadiusUnits * 1.5 + 2400));
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
                        for (int i = 0; i < n; i++)
                            SpawnHostile(Pick(Def.Waves.Mobs), Chain.Around(from, 300), Protect);
                    }
                    break;
                case "boss":
                    if (Boss == null || !Boss.IsAlive) { Outcome = StageOutcome.Success; return; }
                    if (Elapsed >= Def.TimeS) { Outcome = StageOutcome.Fail; return; }
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
            }
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
            if (Chain.Leader is not EventNpc lead || lead == Protect || Def.Type == "escort")
                return;
            if (lead.Brain is EventAllyBrain b)
                b.Steered = true;
            _leadTo = Chain.Around(Center, Math.Min(RadiusUnits * 0.4, 600));
            _leadNext = 0;
        }

        void KeepLeading()
        {
            if (_leadTo is not Vector3 to || Chain.Leader is not EventNpc lead || _now < _leadNext)
                return;
            _leadNext = _now + 3000;
            if (lead.IsWithinRadius(new Point3D((int) to.X, (int) to.Y, (int) to.Z), 250))
            {
                _leadTo = null;                         // there: they stand and fight (the brain still takes on foes)
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
            foreach (EventNpc n in Spawned.ToList())
            {
                n.Stage = null;
                if (n.IsAlive && n.ObjectState == GameObject.eObjectState.Active)
                    n.RemoveFromWorld();
            }
            Spawned.Clear();
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
            _ => 0
        };

        public int TimeLeft => Math.Max(0, (Def.Type == "defend" ? Def.DurationS : Def.TimeS) - Elapsed);

        public string ProgressLine => Def.Type switch
        {
            "cull" => $"{Kills} / {Def.Kill} defeated",
            "defend" => Protect != null ? $"{Protect.Name}: {Protect.HealthPercent}% health" : "",
            "boss" => Boss != null ? $"{Boss.Name}: {Boss.HealthPercent}% health" : "",
            "escort" => Chain.Leader != null ? $"{Chain.Leader.Name}: {Chain.Leader.HealthPercent}% health" : "",
            _ => ""
        };

        // ---------------------------------------------------------------- spawning (scaled to who is here)

        /// <summary>The level of the people at an event: the middle of the players' and bots' levels near it (0: nobody).
        /// Its monsters come at that level when it is above theirs (owner 2026-11-02: every event worth doing at any
        /// level - rewards and drops at your level).</summary>
        public static int TargetLevelAround(ChainRuntime chain, Point3D p, double r)
        {
            int[] levels = chain.PeopleNear(p, r).Select(l => (int) l.Level).OrderBy(l => l).ToArray();
            return levels.Length == 0 ? 0 : levels[levels.Length / 2];
        }

        int MobLevel(int[] range)
        {
            int lo = range == null || range.Length == 0 ? 1 : range[0];
            int hi = range == null || range.Length < 2 ? lo : range[1];
            int roll = Util.Random(lo, hi);
            if (TargetLevel <= hi)
                return roll;
            // above the event's own levels: the same spread, ending just under the people here
            return Math.Max(roll, TargetLevel - 1 - (hi - roll) / 2);
        }

        static MobDef Pick(List<MobDef> mobs) => mobs[Util.Random(mobs.Count - 1)];

        EventNpc SpawnHostile(MobDef m, Vector3 at, GameLiving target)
        {
            if (m == null)
                return null;
            var npc = Chain.Make(m.Template, m.Name, MobLevel(m.Level), m.Model, m.Size, null, m.Guild, at, EventRole.Hostile, this);
            if (npc == null)
                return null;
            Spawned.Add(npc);
            if (target != null && npc.Brain is EventMobBrain brain)
                brain.Goal = target;
            return npc;
        }

        EventNpc SpawnNpc(NpcDef d, EventRole role)
        {
            if (d == null)
                return null;
            Vector3 at = d.Pos != null ? Chain.ToWorld(d.Pos) : Center;
            int level = role == EventRole.Boss ? Math.Max(d.Level, TargetLevel + 1) : Math.Max(d.Level, TargetLevel);
            var npc = Chain.MakeNpc(d, role, at, level, this);
            if (npc == null)
                return null;
            Spawned.Add(npc);
            // (owner 2026-11-02: a boss was too much for eight bots and a hero - health 4x times the crowd scale, up to 12x)
            npc.HealthMult = Math.Max(1, Math.Min(3.0, d.HealthMult)) * (role == EventRole.Boss ? 1 + (Scale - 1) * 0.5 : 1);
            npc.Health = npc.MaxHealth;
            return npc;
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
            if (npc.Role == EventRole.Hostile)
                Kills++;
            GameLiving who = Credit(killer);
            if (who is GamePlayer || who is GameBot)
                _credit[who] = (_credit.TryGetValue(who, out double c) ? c : 0) + npc.MaxHealth * 0.1;
        }

        double ComputeScale()
        {
            int people = Chain.PeopleNear(CenterPoint, RadiusUnits * 1.5).Count();
            return Math.Min(3.0, 1.0 + 0.35 * Math.Max(0, people - 1));
        }

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
                long levelXp = who.Level > 1
                    ? GamePlayer.GetExperienceAmountForLevel(who.Level) - GamePlayer.GetExperienceAmountForLevel(who.Level - 1)
                    : GamePlayer.GetExperienceAmountForLevel(1);
                long xp = (long) (Math.Max(0, levelXp) * r.XpPct / 100.0 * mult);
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
                if (xp > 0 && p.Level < 50)
                    p.GainExperience(eXPSource.Quest, xp, false);
                if (copper > 0)
                    p.AddMoney(copper, "You are rewarded {0}.");
                foreach (ItemRewardDef it in items)
                {
                    if (string.IsNullOrEmpty(it.Id))
                        continue;
                    int chance = tier == 3 ? it.GoldChance : tier == 2 ? it.SilverChance : 0;
                    if (chance <= 0 || !Util.Chance(chance) || ItemAtLevel(it.Id, p.Level) is not DbItemTemplate tpl)
                        continue;
                    DbInventoryItem item = GameInventoryItem.Create(tpl);
                    if (!p.Inventory.AddTemplate(item, 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                        p.CreateItemOnTheGround(item);
                    p.Out.SendMessage($"You receive {tpl.Name}!", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
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
            if (string.IsNullOrEmpty(text))
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
