using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Text;
using DOL.AI.Brain;
using DOL.Database;
using DOL.GS.PacketHandler;
using Newtonsoft.Json;

namespace DOL.GS.DynamicEvents
{
    public enum EventRole { Hostile, Protect, Boss }

    /// <summary>A monster or NPC an event stage spawned: credits damage to the event, tells it when it dies.</summary>
    public class EventNpc : GameNPC
    {
        public StageRuntime Stage;
        public EventRole Role;
        public double HealthMult = 1;

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
    }

    /// <summary>An event monster's mind: an ordinary monster's, except that it has somewhere to be. Sent after someone
    /// (the NPC a defend stage protects, the players at a boss) it runs there and attacks; it never walks back to where it
    /// appeared (its spawn point follows it - an event monster has no home to return to).</summary>
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

    /// <summary>One chain of a zone: idle until its time comes (and someone is in the zone), then its stages in turn.</summary>
    public class ChainRuntime
    {
        public readonly ChainDef Def;
        public readonly Region Region;
        public readonly Zone Zone;
        public StageRuntime Stage;
        public long NextStart;
        public string LastOutcome = "";              // shown on the map a little while after it ends
        public long LastOutcomeUntil;

        public ChainRuntime(ChainDef def, Region region, Zone zone, long now)
        {
            Def = def;
            Region = region;
            Zone = zone;
            NextStart = now + 1000L * Util.Random(def.FirstDelayS[0], def.FirstDelayS[Math.Min(1, def.FirstDelayS.Length - 1)]);
        }

        public bool Active => Stage != null;
        public eRealm HomeRealm => Def.ZoneDef.Realm switch
        {
            1 => eRealm.Albion, 2 => eRealm.Midgard, 3 => eRealm.Hibernia,
            _ => Region.ID >= 200 && Region.ID < 300 ? eRealm.Hibernia : Region.ID >= 100 && Region.ID < 200 ? eRealm.Midgard : eRealm.Albion
        };

        public IEnumerable<GamePlayer> PlayersInZone() =>
            ClientService.Instance.GetPlayers().Where(p => p.CurrentRegion == Region && p.CurrentZone == Zone);

        public void Tick(long now)
        {
            if (Stage == null)
            {
                if (now < NextStart)
                    return;
                if (!PlayersInZone().Any(p => p.Client?.Account?.PrivLevel >= 1))
                {
                    NextStart = now + 60_000;               // nobody to see it: look again in a minute
                    return;
                }
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
                Begin(next, now + 3000);
            else
                End(won ? "success" : "fail", now);
        }

        public void Begin(string stageId, long now)
        {
            StageDef sd = Def.Stages.First(s => s.Id == stageId);
            Stage = new StageRuntime(this, sd, now);
            Stage.Start();
        }

        public void End(string outcome, long now)
        {
            Stage?.Finish(false);
            Stage = null;
            LastOutcome = outcome;
            LastOutcomeUntil = now + 30_000;
            NextStart = now + 1000L * Util.Random(Def.IntervalS[0], Def.IntervalS[Math.Min(1, Def.IntervalS.Length - 1)]);
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
        readonly Dictionary<GamePlayer, int> _presence = new();
        long _nextWave, _nextAdds;
        long _now;
        public double Scale = 1;
        public static bool DEBUG_TRACE = false;   // (the defend stage logs its monsters every 10 s)

        public StageRuntime(ChainRuntime chain, StageDef def, long now)
        {
            Chain = chain;
            Def = def;
            Started = now;
            _now = now;
        }

        int Elapsed => (int) ((_now - Started) / 1000);
        public double RadiusUnits => Def.Radius * 40;

        public void Start()
        {
            Center = Chain.ToWorld(Def.Center);
            Scale = ComputeScale();
            switch (Def.Type)
            {
                case "cull":
                    for (int i = 0; i < Def.Alive; i++)
                        SpawnHostile(Pick(Def.Mobs), Chain.Around(Center, RadiusUnits * 0.85), null);
                    break;
                case "defend":
                    Protect = SpawnNpc(Def.Protect, EventRole.Protect);
                    _nextWave = _now + 8000;
                    break;
                case "boss":
                    Boss = SpawnNpc(Def.Boss, EventRole.Boss);
                    _nextAdds = _now + 1000L * (Def.Adds?.EveryS ?? 30);
                    break;
            }
            Announce(Def.Announce, true);
        }

        public void Tick(long now)
        {
            _now = now;
            Scale = ComputeScale();
            foreach (GamePlayer p in PlayersNear(1.3))
                _presence[p] = _presence.TryGetValue(p, out int s) ? s + 1 : 1;
            Spawned.RemoveAll(n => n == null || n.ObjectState == GameObject.eObjectState.Deleted);
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
                            DynamicEventManager.Trace($"{h.Name}: {h.GetDistanceTo(Protect) / 40:0} m from {Protect?.Name}, moving {h.IsMoving}, speed {h.MaxSpeed}, " +
                                $"brain {h.Brain?.GetType().Name} {(h.Brain as StandardMobBrain)?.FSM?.GetCurrentState()?.StateType}, aggro {(h.Brain as StandardMobBrain)?.HasAggro}, " +
                                $"combat {h.InCombat}, target {h.TargetObject?.Name}, goal {((h.Brain as EventMobBrain)?.Goal)?.Name}");
                    if (Protect == null || !Protect.IsAlive) { Outcome = StageOutcome.Fail; return; }
                    if (Elapsed >= Def.DurationS) { Outcome = StageOutcome.Success; return; }
                    if (Def.Waves != null && now >= _nextWave && Def.DurationS - Elapsed > 10)
                    {
                        _nextWave = now + 1000L * Def.Waves.EveryS;
                        var from = Def.Waves.From.Count > 0 ? Chain.ToWorld(Def.Waves.From[Util.Random(Def.Waves.From.Count - 1)]) : Center;
                        int n = (int) Math.Round(Def.Waves.Count * Scale);
                        for (int i = 0; i < n; i++)
                            SpawnHostile(Pick(Def.Waves.Mobs), Chain.Around(from, 300), Protect);
                    }
                    break;
                case "boss":
                    if (Boss == null || !Boss.IsAlive) { Outcome = StageOutcome.Success; return; }
                    if (Elapsed >= Def.TimeS) { Outcome = StageOutcome.Fail; return; }
                    if (Def.Adds != null && now >= _nextAdds && Boss.InCombat)
                    {
                        _nextAdds = now + 1000L * Def.Adds.EveryS;
                        var target = PlayersNear(1.5).Cast<GameLiving>().OrderBy(p => p.GetDistanceTo(Boss)).FirstOrDefault();
                        int n = (int) Math.Round(Def.Adds.Count * Math.Min(Scale, 2.0));
                        var at = new Vector3(Boss.X, Boss.Y, Boss.Z);
                        for (int i = 0; i < n; i++)
                            SpawnHostile(Pick(Def.Adds.Mobs), Chain.Around(at, 350), target);
                    }
                    break;
            }
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
        }

        // ---------------------------------------------------------------- progress (the tracker)

        public double Progress => Def.Type switch
        {
            "cull" => Math.Min(1.0, Kills / (double) Math.Max(1, Def.Kill)),
            "defend" => Math.Min(1.0, Elapsed / (double) Math.Max(1, Def.DurationS)),
            "boss" => Boss == null ? 1.0 : 1.0 - Boss.Health / (double) Math.Max(1, Boss.MaxHealth),
            _ => 0
        };

        public int TimeLeft => Math.Max(0, (Def.Type == "defend" ? Def.DurationS : Def.TimeS) - Elapsed);

        public string ProgressLine => Def.Type switch
        {
            "cull" => $"{Kills} / {Def.Kill} defeated",
            "defend" => Protect != null ? $"{Protect.Name}: {Protect.HealthPercent}% health" : "",
            "boss" => Boss != null ? $"{Boss.Name}: {Boss.HealthPercent}% health" : "",
            _ => ""
        };

        // ---------------------------------------------------------------- spawning

        static MobDef Pick(List<MobDef> mobs) => mobs[Util.Random(mobs.Count - 1)];

        EventNpc SpawnHostile(MobDef m, Vector3 at, GameLiving target)
        {
            if (m == null)
                return null;
            int lvl = m.Level == null || m.Level.Length == 0 ? 1 : Util.Random(m.Level[0], m.Level[Math.Min(1, m.Level.Length - 1)]);
            var npc = Make(m.Template, m.Name, lvl, m.Model, m.Size, null, at, EventRole.Hostile);
            if (npc == null)
                return null;
            if (target != null && npc.Brain is EventMobBrain brain)
                brain.Goal = target;
            return npc;
        }

        EventNpc SpawnNpc(NpcDef d, EventRole role)
        {
            if (d == null)
                return null;
            Vector3 at = d.Pos != null ? Chain.ToWorld(d.Pos) : Center;
            var npc = Make(d.Template, d.Name, d.Level, d.Model, d.Size, d.Equipment, at, role);
            if (npc == null)
                return null;
            npc.HealthMult = Math.Max(1, d.HealthMult) * (role == EventRole.Boss ? Scale : 1);
            npc.Health = npc.MaxHealth;
            return npc;
        }

        EventNpc Make(int template, string name, int level, ushort model, byte size, string equipment, Vector3 at, EventRole role)
        {
            var npc = new EventNpc { Stage = this, Role = role };
            if (template > 0 && NpcTemplateMgr.GetTemplate(template) is NpcTemplate tpl)
                npc.LoadTemplate(tpl);
            if (!string.IsNullOrEmpty(name)) npc.Name = name;
            npc.GuildName = "";
            if (level > 0) npc.Level = (byte) Math.Clamp(level, 1, 255);
            if (model > 0) npc.Model = model;
            if (size > 0) npc.Size = size;
            if (!string.IsNullOrEmpty(equipment))
                npc.LoadEquipmentTemplateFromDatabase(equipment);
            npc.X = (int) at.X;
            npc.Y = (int) at.Y;
            npc.Z = (int) at.Z;
            npc.Heading = (ushort) Util.Random(4095);
            npc.CurrentRegion = Chain.Region;
            npc.RespawnInterval = -1;
            npc.RoamingRange = 0;
            npc.LoadedFromScript = true;
            if (role == EventRole.Protect)
            {
                npc.Realm = Chain.HomeRealm;
                npc.Flags = (GameNPC.eFlags) 0;   // (no peace flag: the stage's monsters may attack them)
                npc.SetOwnBrain(new BlankBrain());
            }
            else
            {
                npc.Realm = eRealm.None;
                npc.SetOwnBrain(new EventMobBrain { AggroLevel = 100, AggroRange = role == EventRole.Boss ? 900 : 650 });
            }
            if (!npc.AddToWorld())
                return null;
            npc.SpawnPoint = new Point3D(npc.X, npc.Y, npc.Z);
            npc.Health = npc.MaxHealth;
            Spawned.Add(npc);
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
            if (npc.Role == EventRole.Protect || amount <= 0)
                return;
            GameLiving who = Credit(source);
            if (who is GamePlayer || who is GameBot)
                _credit[who] = (_credit.TryGetValue(who, out double c) ? c : 0) + amount;
        }

        public void OnDied(EventNpc npc, GameObject killer)
        {
            if (npc.Role == EventRole.Protect)
                return;
            if (npc.Role == EventRole.Hostile)
                Kills++;
            GameLiving who = Credit(killer);
            if (who is GamePlayer || who is GameBot)
                _credit[who] = (_credit.TryGetValue(who, out double c) ? c : 0) + npc.MaxHealth * 0.1;
        }

        IEnumerable<GamePlayer> PlayersNear(double mult) =>
            Chain.Region.GetPlayersInRadius(new Point3D((int) Center.X, (int) Center.Y, (int) Center.Z),
                (ushort) Math.Min(65000, RadiusUnits * mult));

        double ComputeScale()
        {
            var point = new Point3D((int) Center.X, (int) Center.Y, (int) Center.Z);
            ushort r = (ushort) Math.Min(65000, RadiusUnits * 1.5);
            int people = Chain.Region.GetPlayersInRadius(point, r).Count + Chain.Region.GetNPCsInRadius(point, r).OfType<GameBot>().Count();
            return Math.Min(3.0, 1.0 + 0.35 * Math.Max(0, people - 1));
        }

        /// <summary>Gold, silver or bronze by share of the work (damage dealt to the event's monsters, kills), bronze for
        /// being there; experience as a share of the level, money by level, and the stage's item by chance.</summary>
        void GiveRewards()
        {
            var players = new HashSet<GamePlayer>(_presence.Where(kv => kv.Value >= 15).Select(kv => kv.Key));
            foreach (var who in _credit.Keys.OfType<GamePlayer>())
                players.Add(who);
            double best = _credit.Count > 0 ? _credit.Values.Max() : 0;
            RewardDef r = Def.Reward;
            foreach (GamePlayer p in players)
            {
                if (p.ObjectState != GameObject.eObjectState.Active || p.CurrentRegion != Chain.Region)
                    continue;
                double c = _credit.TryGetValue(p, out double v) ? v : 0;
                int tier = best > 0 && c >= best * 0.5 ? 3 : best > 0 && c >= best * 0.15 ? 2 : 1;
                double mult = tier == 3 ? 1.0 : tier == 2 ? 0.7 : 0.4;
                string medal = tier == 3 ? "Gold" : tier == 2 ? "Silver" : "Bronze";
                p.Out.SendMessage($"{Chain.Def.Title}: {Def.Name} complete - {medal} contribution.", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                if (r.XpPct > 0 && p.Level < 50)
                {
                    long levelXp = p.ExperienceForNextLevel - p.ExperienceForCurrentLevel;
                    long xp = (long) (levelXp * r.XpPct / 100.0 * mult);
                    if (xp > 0)
                        p.GainExperience(eXPSource.Quest, xp, false);
                }
                if (r.CopperPerLevel > 0)
                    p.AddMoney((long) (r.CopperPerLevel * p.Level * mult), "You are rewarded {0}.");
                if (r.Item != null && !string.IsNullOrEmpty(r.Item.Id))
                {
                    int chance = tier == 3 ? r.Item.GoldChance : tier == 2 ? r.Item.SilverChance : 0;
                    if (chance > 0 && Util.Chance(chance) &&
                        GameServer.Database.FindObjectByKey<DbItemTemplate>(r.Item.Id) is DbItemTemplate tpl)
                    {
                        DbInventoryItem item = GameInventoryItem.Create(tpl);
                        if (!p.Inventory.AddTemplate(item, 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                            p.CreateItemOnTheGround(item);
                        p.Out.SendMessage($"You receive {tpl.Name}!", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                    }
                }
            }
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
