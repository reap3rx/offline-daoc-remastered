using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using DOL.AI.Brain;
using DOL.Events;
using DOL.GS.PacketHandler;
using Newtonsoft.Json;

namespace DOL.GS.DynamicEvents
{
    /// <summary>
    /// King Lug's campaign on the Cursed Forest (claude 2026-11-24, the zone brief and the owner's answers in Zone Reviews):
    ///   - only a General of the Host at Druim Cain starts it, and only for a player of level 45 or more (anyone may join);
    ///   - its first battle is Bri Leith's Forest Gate (a siege made a campaign battle: ZoneSiege, Def.Campaign "lug");
    ///   - then four checkpoints in the forest, each a harder power check (zone208 events, cf_cpN_assault), each held by the
    ///     Host's soldiers;
    ///   - held, the Host has thirty minutes to win the next one; if it doesn't, the court counter-attacks the last one
    ///     (cf_cpN_counter, or the Queen's Hunt at the Forest Gate). The Host's captain holds a while and falls without help;
    ///     lost, the Host steps back a checkpoint and the clock starts again - down to the Forest Gate, and out;
    ///   - past the Thorn Gate, the raid on the Queen's Seat (cf_queens_seat: Queen Cliodna, CliodnaRaid.cs);
    ///   - won, the Host holds the forest for four real hours: the fog lifts (the #SIEGE line's "lift"), the court is swept
    ///     out but for a few pockets, and the Host's quartermasters stand at the Seat. Then the Queen reconstitutes and it
    ///     all goes back. Without the campaign there are no events in the forest at all.
    /// Bots count: they take the givers' calls and fight the counters like anyone.
    /// </summary>
    public static class LugCampaign
    {
        public const ushort Region = 200;
        public const int ForestZone = 208, ValleyZone = 206;
        public const int MinLevel = 45;
        public const string GateSiege = "forest_gate";
        public const int Checkpoints = 4;
        public static readonly TimeSpan Window = TimeSpan.FromMinutes(30);         // to win the next checkpoint
        public static readonly TimeSpan VictoryHold = TimeSpan.FromHours(4);        // the forest the King's
        public static readonly TimeSpan GateWait = TimeSpan.FromMinutes(60);       // the Forest Gate not taken in this long: called off
        public static readonly TimeSpan Rest = TimeSpan.FromMinutes(20);           // after it ends, before a general will call it again

        public static readonly string[] Names = { "the Forest Gate", "the Hollow Road", "the Ford of Sorrows", "the Hag-Wood", "the Thorn Gate" };
        // the checkpoints (forest metres, as zone208's events have them) and the sites the Host sweeps while it holds them
        public static readonly double[][] Posts =
        {
            null,
            new[] { 430.0, 1080.0, 125.0 }, new[] { 682.0, 867.0, 125.0 }, new[] { 965.0, 705.0, 125.0 }, new[] { 1170.0, 640.0, 130.0 }
        };
        public static readonly string[][] HeldSites =
        {
            new[] { "pocket_west", "west_riders" },
            new[] { "cp1_garrison", "cp1_wood", "court_road" },     // (the court's road patrol walks every checkpoint)
            new[] { "cp2_garrison", "cp2_banks", "fear_dubh" },
            new[] { "cp3_garrison", "cp3_wood", "middle_wood" },
            new[] { "cp4_garrison", "cp4_wood" }
        };
        public static readonly double[] Seat = { 1320, 645, 119 };
        public const string PocketPrefix = "pocket_";

        // the General of the Host, at Druim Cain (Bri Leith metres): one look, always (owner: "a locked in appearance")
        public const string GeneralName = "General Fergna Ironhand";
        public const string GeneralGuild = "Marshal of the Host of Lug";
        public static readonly double[] GeneralAt = { 912, 66, 46, 3072 };
        public const int SoldierTemplate = 60157478;           // Druim Cain's champion: the Host's look
        public const ushort GeneralModel = 362, SoldierModel = 362;
        public const string HostEquipment = "0b7ecfe0-b579-44bc-819f-753a18263762";

        public enum Phase { Idle, Gate, Holding, Victory }

        public class State
        {
            public Phase Phase;
            public int Held = -1;                  // -1 none, 0 the Forest Gate, 1..4 the checkpoints
            public DateTime DeadlineUtc;           // the next checkpoint (or the raid) by then, or a counter-attack
            public DateTime StartedUtc;
            public DateTime VictoryUntilUtc;
            public DateTime RestUntilUtc;
            public string Counter;                 // the counter-attack under way
            public string StartedBy;
            public int Wins, Losses;
        }

        public static State S = new();
        static readonly List<GameNPC> _soldiers = new();
        static readonly Dictionary<int, List<GameNPC>> _posts = new();
        static readonly List<GameNPC> _seatCamp = new();
        static readonly List<GameNPC> _hidden = new();
        static LugGeneral _general;
        static bool _hooked;
        static long _nextSweep, _nextTell, _nextSave;
        static readonly Logging.Logger log = Logging.LoggerManager.Create(System.Reflection.MethodBase.GetCurrentMethod().DeclaringType);

        static string StatePath => Path.Combine(GameServer.Instance.Configuration.RootDirectory, "lug-campaign-state.json");

        // ------------------------------------------------------------------ the rules (pure: tested)

        /// <summary>Who may raise the Host.</summary>
        public static string CanStart(int level, State s, DateTime nowUtc)
        {
            if (level < MinLevel)
                return $"The Host marches for champions, and you're not one yet. Come back at level {MinLevel} - then the King will hear your name.";
            if (s.Phase != Phase.Idle)
                return "The Host is already in the field. Go and join it.";
            if (nowUtc < s.RestUntilUtc)
                return $"The Host is resting after the last march. In {Math.Max(1, (int) Math.Ceiling((s.RestUntilUtc - nowUtc).TotalMinutes))} minutes it can march again.";
            return null;
        }

        /// <summary>The next battle's chain id while the Host holds <paramref name="held"/>: a checkpoint's assault, or the raid.</summary>
        public static string NextAssault(int held) => held >= Checkpoints ? "cf_queens_seat" : held >= 0 ? $"cf_cp{held + 1}_assault" : null;

        /// <summary>The counter-attack on what the Host holds (the Queen's Hunt at the Forest Gate is the siege's raid).</summary>
        public static string CounterFor(int held) => held >= 1 ? $"cf_cp{held}_counter" : null;

        /// <summary>The checkpoint a chain takes (cf_cp3_assault: 3; the raid: 5), or 0.</summary>
        public static int AssaultIndex(string chainId)
        {
            if (chainId == "cf_queens_seat")
                return Checkpoints + 1;
            if (chainId != null && chainId.StartsWith("cf_cp") && chainId.EndsWith("_assault") && int.TryParse(chainId.Substring(5, 1), out int n))
                return n;
            return 0;
        }

        public static int CounterIndex(string chainId) =>
            chainId != null && chainId.StartsWith("cf_cp") && chainId.EndsWith("_counter") && int.TryParse(chainId.Substring(5, 1), out int n) ? n : 0;

        /// <summary>A checkpoint won: held, and a fresh half-hour.</summary>
        public static void Won(State s, int n, DateTime nowUtc)
        {
            s.Phase = Phase.Holding;
            s.Held = n;
            s.DeadlineUtc = nowUtc + Window;
            s.Counter = null;
        }

        /// <summary>A counter-attack beaten off: the clock starts again.</summary>
        public static void CounterHeld(State s, DateTime nowUtc)
        {
            s.Counter = null;
            s.DeadlineUtc = nowUtc + Window;
        }

        /// <summary>A counter-attack lost: a step back (true while the Host still holds something).</summary>
        public static bool CounterLost(State s, DateTime nowUtc)
        {
            s.Counter = null;
            s.Held--;
            s.DeadlineUtc = nowUtc + Window;
            return s.Held >= 0;
        }

        public static void Victory(State s, DateTime nowUtc)
        {
            s.Phase = Phase.Victory;
            s.Held = Checkpoints + 1;
            s.Counter = null;
            s.VictoryUntilUtc = nowUtc + VictoryHold;
            s.Wins++;
        }

        public static void Over(State s, DateTime nowUtc, bool lost)
        {
            s.Phase = Phase.Idle;
            s.Held = -1;
            s.Counter = null;
            s.RestUntilUtc = nowUtc + Rest;
            if (lost)
                s.Losses++;
        }

        /// <summary>While the court holds the forest it is fogged in; won, the fog lifts.</summary>
        public static bool FogLifted(State s) => s.Phase == Phase.Victory;

        /// <summary>The panel's line.</summary>
        public static string Line(State s, DateTime nowUtc)
        {
            string Clock(DateTime until)
            {
                TimeSpan left = until - nowUtc;
                if (left.TotalSeconds <= 0)
                    return "now";
                return left.TotalHours >= 1 ? $"{(int) left.TotalHours}h {left.Minutes:00}m" : $"{Math.Max(1, (int) Math.Ceiling(left.TotalMinutes))}m";
            }
            switch (s.Phase)
            {
                case Phase.Gate:
                    return "The Host gathers at the Forest Gate";
                case Phase.Holding:
                    string held = s.Held >= 0 && s.Held < Names.Length ? Names[s.Held] : "the Thorn Gate";
                    if (s.Counter != null)
                        return $"The court strikes back at {held}!";
                    string next = s.Held >= Checkpoints ? "the Queen's Seat" : Names[s.Held + 1];
                    return $"Holding {held} - {next} in {Clock(s.DeadlineUtc)}";
                case Phase.Victory:
                    return $"The forest is the King's - {Clock(s.VictoryUntilUtc)} until the Queen returns";
                default:
                    return "The court holds the forest";
            }
        }

        /// <summary>How far along (0..100) for the panel's bar.</summary>
        public static double Progress(State s) => s.Phase switch
        {
            Phase.Gate => 5,
            Phase.Holding => 10 + 18 * Math.Max(0, s.Held),
            Phase.Victory => 100,
            _ => 0
        };

        // ------------------------------------------------------------------ the world

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            _ = new ECSGameTimer(null, _ => { Start(); return 0; }, 25_000);   // (after the dynamic events and the sieges)
        }

        static void Start()
        {
            try
            {
                LoadState();
                Hook();
                Arm();
                PlaceGeneral();
                Reconcile(true);
                _ = new ECSGameTimer(null, _ => { Tick(); return 1000; }, 1000);
                log.Info($"King Lug's campaign: {S.Phase}, holding {S.Held}");
            }
            catch (Exception ex)
            {
                log.Warn("King Lug's campaign: couldn't start", ex);
            }
        }

        static ChainRuntime Chain(string id) => DynamicEventManager.Chains.FirstOrDefault(c => c.Def.Id == id);
        static SiegeRuntime Gate => ZoneSiege.ById(GateSiege);

        static void Hook()
        {
            if (_hooked)
                return;
            _hooked = true;
            DynamicEventManager.ChainEnded += OnChainEnded;
            ZoneSiege.Changed += OnSiege;
        }

        /// <summary>The forest's chains: each assault's captain comes only while the Host holds the place before it, and
        /// sets out only with enough hands (bots too - alone, once they've waited a quarter hour).</summary>
        static void Arm()
        {
            for (int n = 1; n <= Checkpoints + 1; n++)
            {
                ChainRuntime c = Chain(NextAssault(n - 1));
                if (c == null)
                    continue;
                int me = n;
                c.Available = () => S.Phase == Phase.Holding && S.Held == me - 1 && S.Counter == null;
                c.Gate = () => GateFor(c);
                c.Toughness = 1 + 0.15 * (me - 1);
                c.Def.HostileTier = MonsterTiers.Orange;
            }
            for (int n = 1; n <= Checkpoints; n++)
                if (Chain(CounterFor(n)) is ChainRuntime cc)
                {
                    cc.Toughness = 1 + 0.15 * (n - 1);
                    cc.Def.HostileTier = MonsterTiers.Orange;
                }
        }

        static readonly Dictionary<ChainRuntime, long> _giverSince = new();

        static string GateFor(ChainRuntime c)
        {
            if (c.Leader is not EventNpc g)
                return "Not yet.";
            var near = c.PeopleNear(new Point3D(g.X, g.Y, g.Z), 2000).ToList();
            int need = Math.Max(1, c.Def.MinPeople);
            if (near.Count < need)
                return $"Not with so few - {near.Count} of {need}. Gather more here, then tell me [{c.Def.Giver.Accept}].";
            long now = Environment.TickCount64;
            if (!_giverSince.TryGetValue(c, out long since))
                _giverSince[c] = since = now;
            if (!near.Any(p => p is GamePlayer) && now - since < 15 * 60_000)
                return "We wait for someone to lead it.";
            return null;
        }

        // ------------------------------------------------------------------ what happens

        /// <summary>The General's word: the Host marches.</summary>
        public static bool Raise(GamePlayer p)
        {
            if (CanStart(p.Level, S, DateTime.UtcNow) is string why)
            {
                if (_general != null)
                    NpcSpeech.SayTo(_general, p, why);
                return false;
            }
            S = new State { Phase = Phase.Gate, StartedUtc = DateTime.UtcNow, StartedBy = p.Name, Wins = S.Wins, Losses = S.Losses };
            Gate?.CampaignOpen();
            Realm($"King Lug's Host marches on the Cursed Forest! {p.Name} has the General's word. The Rangers of Druim Cain gather below the Forest Gate - every sword is wanted.");
            Save();
            return true;
        }

        static void OnSiege(SiegeRuntime s, string what)
        {
            if (s.Def.Id != GateSiege || S.Phase == Phase.Idle)
                return;
            DateTime now = DateTime.UtcNow;
            switch (what)
            {
                case "taken":
                    Won(S, 0, now);
                    Hold(0);
                    Tell("The Forest Gate is the King's! Captain Eogan is forming the Host just inside the forest - the Hollow Road within the half-hour, or the court comes back for the gate.");
                    break;
                case "repelled":
                    if (S.Phase == Phase.Gate)
                        _ = new ECSGameTimer(null, _ => { if (S.Phase == Phase.Gate) Gate?.CampaignOpen(); return 0; }, 60_000);
                    break;
                case "held":
                    CounterHeld(S, now);
                    break;
                case "fell":
                    Unhold(0);
                    Pushed();
                    break;
            }
            Save();
        }

        static void OnChainEnded(ChainRuntime c, string outcome)
        {
            if (S.Phase is Phase.Idle)
                return;
            DateTime now = DateTime.UtcNow;
            int a = AssaultIndex(c.Def.Id), k = CounterIndex(c.Def.Id);
            if (a > 0 && outcome == "success" && S.Phase == Phase.Holding && S.Held == a - 1)
            {
                _giverSince.Remove(c);
                if (a > Checkpoints)
                {
                    Victory(S, now);
                    Won_();
                }
                else
                {
                    Won(S, a, now);
                    Hold(a);
                    Sweep();
                    string next = a == Checkpoints ? "the Queen's Seat itself" : Names[a + 1];
                    Tell($"{Names[a][0].ToString().ToUpper() + Names[a].Substring(1)} is the King's! The Host holds it. {next[0].ToString().ToUpper() + next.Substring(1)} within the half-hour - or the court comes back.");
                }
            }
            else if (k > 0 && S.Counter == c.Def.Id)
            {
                if (outcome == "success")
                {
                    CounterHeld(S, now);
                    Tell($"The court breaks against the Host at {Names[k]}. The line holds - and the clock starts again.");
                }
                else
                {
                    Unhold(k);
                    if (CounterLost(S, now))
                        Tell($"{Names[k][0].ToString().ToUpper() + Names[k].Substring(1)} has fallen to the court! The Host falls back to {Names[S.Held]}.");
                    else
                        Pushed();
                }
            }
            Save();
        }

        static void Tick()
        {
            try
            {
                long now = Environment.TickCount64;
                DateTime utc = DateTime.UtcNow;
                switch (S.Phase)
                {
                    case Phase.Gate:
                        if (utc - S.StartedUtc > GateWait && Gate?.Assault?.Active != true)
                        {
                            Tell("No one came to the Forest Gate. The Host goes home to Druim Cain.");
                            End(false, true);
                        }
                        break;
                    case Phase.Holding:
                        if (S.Counter != null)
                        {
                            bool running = S.Held == 0 ? Gate?.RaidUnderWay == true : Chain(S.Counter) is ChainRuntime cc && (cc.Active || cc.Dormant);
                            if (!running)
                                S.Counter = null;              // (gone without word - a GM, a restart: the clock starts again)
                            if (!running)
                                S.DeadlineUtc = utc + Window;
                        }
                        else if (utc >= S.DeadlineUtc)
                        {
                            ChainRuntime next = Chain(NextAssault(S.Held));
                            if (next != null && next.Active)
                                break;                         // (they're at it now: the court waits on the outcome)
                            CounterAttack(now);
                        }
                        break;
                    case Phase.Victory:
                        if (utc >= S.VictoryUntilUtc)
                        {
                            Realm("The fog comes back into the Cursed Forest. Queen Cliodna has reconstituted, and the court holds the forest again.");
                            End(false, false);
                        }
                        break;
                }
                if (now >= _nextSweep)
                {
                    _nextSweep = now + 15_000;
                    Sweep();
                    KeepPosts();
                }
                if (now >= _nextTell)
                {
                    _nextTell = now + 5000;
                    Broadcast(utc);
                }
                if (now >= _nextSave)
                {
                    _nextSave = now + 60_000;
                    Save();
                }
            }
            catch (Exception ex)
            {
                log.Warn("King Lug's campaign: tick", ex);
            }
        }

        static void CounterAttack(long now)
        {
            if (S.Held == 0)
            {
                if (Gate?.CampaignRaid(now) == true)
                {
                    S.Counter = "gate";
                    Tell("The Queen's Hunt is coming for the Forest Gate! Hold it, or the Host is pushed out of the forest!");
                }
                else
                    S.DeadlineUtc = DateTime.UtcNow + TimeSpan.FromMinutes(2);
                return;
            }
            if (Chain(CounterFor(S.Held)) is ChainRuntime c && !c.Active)
            {
                S.Counter = c.Def.Id;
                c.Begin(c.Def.Start, now);
            }
            else
                S.DeadlineUtc = DateTime.UtcNow + TimeSpan.FromMinutes(2);
        }

        static void Pushed()
        {
            Realm("King Lug's Host has been pushed out of the Cursed Forest. The court holds the border again.");
            End(true, true);
        }

        static void Won_()
        {
            // a counter-attack or an assault still running when the Queen falls is over: the court has nothing left to send
            foreach (ChainRuntime c in DynamicEventManager.Chains.Where(c => c.Zone?.ID == ForestZone && c.Def.Id != CliodnaRaid.ChainId && (c.Active || c.Dormant)))
                try { c.End("success", Environment.TickCount64); } catch (Exception) { }
            if (Gate?.RaidUnderWay == true && Gate.RaidChains.TryGetValue(Gate.State.RaidRunning, out ChainRuntime hunt))
                try { hunt.End("success", Environment.TickCount64); } catch (Exception) { }
            Realm("Queen Cliodna has fallen! King Lug's Host holds the Cursed Forest, and the fog is lifting. The Host's quartermasters wait at the Queen's Seat.");
            for (int n = 0; n <= Checkpoints; n++)
                Hold(n);
            MakeSeatCamp();
            Sweep();
            Save();
        }

        /// <summary>Back to the start: the Host goes home, the court's monsters come back, the Forest Gate is the court's.</summary>
        static void End(bool lost, bool quietGate)
        {
            Over(S, DateTime.UtcNow, lost);
            foreach (var kv in _posts.ToList())
                Unhold(kv.Key);
            foreach (GameNPC n in _seatCamp)
                try { n.Delete(); } catch (Exception) { }
            _seatCamp.Clear();
            Restore();
            foreach (ChainRuntime c in DynamicEventManager.Chains.Where(c => c.Zone?.ID == ForestZone && (c.Active || c.Dormant)))
                try { c.End("fail", Environment.TickCount64); } catch (Exception) { }
            Gate?.CampaignReset();
            Save();
        }

        /// <summary>After a restart: the world put back the way the state says.</summary>
        static void Reconcile(bool quiet)
        {
            if (S.Phase == Phase.Idle)
            {
                if (Gate != null && Gate.State.Phase != SiegePhase.Building)
                    Gate.CampaignReset();
                return;
            }
            if (S.Phase == Phase.Gate)
            {
                Gate?.CampaignOpen();
                return;
            }
            S.Counter = null;
            int top = S.Phase == Phase.Victory ? Checkpoints : S.Held;
            for (int n = 0; n <= top; n++)
                Hold(n);
            if (S.Phase == Phase.Victory)
                MakeSeatCamp();
            if (S.Phase == Phase.Holding && S.DeadlineUtc < DateTime.UtcNow + TimeSpan.FromMinutes(10))
                S.DeadlineUtc = DateTime.UtcNow + TimeSpan.FromMinutes(10);   // (a restart: a little grace)
        }

        // ------------------------------------------------------------------ the Host's posts

        static ZoneOffsets Forest => new(WorldMgr.GetZone(ForestZone));

        readonly struct ZoneOffsets
        {
            readonly Zone _z;
            public ZoneOffsets(Zone z) => _z = z;
            public Vector3 At(double[] m) => new((float) (_z.XOffset + m[0] * 40), (float) (_z.YOffset + m[1] * 40), (float) (m[2] * 40));
        }

        static void Hold(int n)
        {
            if (_posts.ContainsKey(n))
                return;
            var list = new List<GameNPC>();
            _posts[n] = list;
            if (n == 0)
                return;                                    // (the Forest Gate's camp is the siege's own)
            Vector3 c = Forest.At(Posts[n]);
            list.Add(Soldier("Banner-Captain of the Host", c, 0, 51, true));
            for (int i = 0; i < 6; i++)
                list.Add(Soldier(i % 3 == 2 ? "druid of the Host" : "spear of the Host", c, 500, 49, false));
            list.RemoveAll(x => x == null);
        }

        static void Unhold(int n)
        {
            if (!_posts.TryGetValue(n, out var list))
                return;
            foreach (GameNPC s in list)
                try { s.Delete(); } catch (Exception) { }
            _posts.Remove(n);
        }

        /// <summary>The fallen of the Host come back while it holds the place (a long, slow trickle - two minutes).</summary>
        static void KeepPosts()
        {
            foreach (var kv in _posts)
                foreach (GameNPC s in kv.Value)
                    if (s is LugSoldier ls && !s.IsAlive && Environment.TickCount64 - ls.DiedAt > 120_000 && s.ObjectState != GameObject.eObjectState.Deleted)
                    {
                        s.Health = s.MaxHealth;
                        s.MoveTo(s.CurrentRegionID, s.SpawnPoint.X, s.SpawnPoint.Y, s.SpawnPoint.Z, s.Heading);
                    }
        }

        static GameNPC Soldier(string name, Vector3 c, double r, byte level, bool captain)
        {
            Region region = WorldMgr.GetRegion(Region);
            if (region == null)
                return null;
            var n = new LugSoldier();
            if (NpcTemplateMgr.GetTemplate(SoldierTemplate) is NpcTemplate t)
                n.LoadTemplate(t);
            n.Name = name;
            n.GuildName = "the Host of Lug";
            n.Model = SoldierModel;
            n.Size = (byte) (captain ? 58 : 52);
            n.Level = level;
            n.Realm = eRealm.Hibernia;
            n.LoadEquipmentTemplateFromDatabase(HostEquipment);
            double a = Util.RandomDouble() * Math.PI * 2, d = r * Math.Sqrt(Util.RandomDouble());
            n.X = (int) (c.X + Math.Cos(a) * d);
            n.Y = (int) (c.Y + Math.Sin(a) * d);
            n.Z = (int) c.Z;
            n.Heading = (ushort) Util.Random(4095);
            n.CurrentRegion = region;
            n.LoadedFromScript = true;
            n.RespawnInterval = -1;
            n.SetOwnBrain(new LugSoldierBrain());
            if (!n.AddToWorld())
                return null;
            n.SpawnPoint = new Point3D(n.X, n.Y, n.Z);
            return n;
        }

        /// <summary>The forest won: the Host's quartermaster and its druid at the Seat (the best Marks of Valor stock).</summary>
        static void MakeSeatCamp()
        {
            if (_seatCamp.Count > 0)
                return;
            Region region = WorldMgr.GetRegion(Region);
            if (region == null)
                return;
            var host = new SiegeRuntime(new SiegeDef { Id = "host_of_lug", Name = "the Host of Lug", Faction = "host_of_lug" });
            Vector3 c = Forest.At(Seat);
            foreach (SiegeNpcDef d in SeatCamp())
            {
                GameNPC n = d.Kind == "marks" ? new SiegeMarksMerchant { Siege = host, Def = d } : new SiegeCampNpc { Siege = host, Def = d };
                if (NpcTemplateMgr.GetTemplate(SoldierTemplate) is NpcTemplate t)
                    n.LoadTemplate(t);
                n.Name = d.Name;
                n.GuildName = d.Guild;
                n.Model = d.Model;
                n.Size = 54;
                n.Level = 55;
                n.Realm = eRealm.Hibernia;
                n.Flags |= GameNPC.eFlags.PEACE;
                n.LoadEquipmentTemplateFromDatabase(HostEquipment);
                n.X = (int) (c.X + d.Pos[0] * 40);
                n.Y = (int) (c.Y + d.Pos[1] * 40);
                n.Z = (int) c.Z;
                n.Heading = (ushort) Util.Random(4095);
                n.CurrentRegion = region;
                n.LoadedFromScript = true;
                n.RespawnInterval = -1;
                if (n.AddToWorld())
                    _seatCamp.Add(n);
            }
        }

        /// <summary>The Seat's camp (Pos here: metres from the Seat).</summary>
        public static List<SiegeNpcDef> SeatCamp() => new()
        {
            new SiegeNpcDef
            {
                Kind = "marks", Name = "Quartermaster Cathbad of the Host", Guild = "the Host of Lug", Model = 362, Pos = new[] { -6.0, 4.0 },
                Greet = "The King pays well for the Queen's Seat. Marks of Valor, and the Host's own make - the best there is.",
                Stock = new()
                {
                    new SiegeStockDef { Item = "cf208_mantle_of_the_host", Price = 260 },
                    new SiegeStockDef { Item = "cf208_lamfhota_s_spear_torc", Price = 240 },
                    new SiegeStockDef { Item = "cf208_seat_breaker_s_belt", Price = 220 },
                    new SiegeStockDef { Item = "cf208_ring_of_the_long_arm", Price = 220 },
                    new SiegeStockDef { Item = "cf208_bracer_of_the_thorn_gate", Price = 200 },
                    new SiegeStockDef { Item = "cf208_fogless_jewel", Price = 200 },
                }
            },
            new SiegeNpcDef
            {
                Kind = "idle", Name = "Druid Senach", Guild = "the Host of Lug", Model = 362, Pos = new[] { 5.0, 5.0 },
                Greet = "Breathe it in. No fog. For the first time in a hundred years you can see from one side of this forest to the other. Enjoy it - she'll be back."
            }
        };

        /// <summary>The court's monsters the Host keeps out of what it holds - and, the forest won, out of all of it but
        /// the pockets.</summary>
        static void Sweep()
        {
            var away = new HashSet<GameNPC>();
            if (S.Phase == Phase.Victory)
            {
                foreach (string id in ZoneBuilds.SiteIds(ForestZone).Where(id => !id.StartsWith(PocketPrefix)))
                    away.UnionWith(ZoneBuilds.SiteNpcs(ForestZone, id));
            }
            else if (S.Phase == Phase.Holding && S.Held >= 1)
            {
                // the checkpoints' own sites, and anything of the court's whose home is near a held post (live test 24 Nov:
                // wanderers from the next wood came in on the Host's banner-captain)
                var posts = Enumerable.Range(1, Math.Min(S.Held, Checkpoints)).Select(n => Forest.At(Posts[n])).ToList();
                for (int n = 1; n <= Math.Min(S.Held, Checkpoints); n++)
                    foreach (string id in HeldSites[n])
                        away.UnionWith(ZoneBuilds.SiteNpcs(ForestZone, id));
                foreach (string id in ZoneBuilds.SiteIds(ForestZone))
                    foreach (GameNPC n in ZoneBuilds.SiteNpcs(ForestZone, id))
                        if (n.SpawnPoint != null && posts.Any(p => Math.Abs(n.SpawnPoint.X - p.X) < PostClearUnits && Math.Abs(n.SpawnPoint.Y - p.Y) < PostClearUnits &&
                                Math.Sqrt(Math.Pow(n.SpawnPoint.X - p.X, 2) + Math.Pow(n.SpawnPoint.Y - p.Y, 2)) < PostClearUnits))
                            away.Add(n);
            }
            foreach (GameNPC n in away)
                if (n.ObjectState == GameObject.eObjectState.Active && n.IsAlive && !n.InCombat)
                {
                    n.RemoveFromWorld();
                    if (!_hidden.Contains(n))
                        _hidden.Add(n);
                }
            // what's no longer to be kept out comes back
            foreach (GameNPC n in _hidden.Where(n => !away.Contains(n)).ToList())
            {
                Bring(n);
                _hidden.Remove(n);
            }
        }

        public const int PostClearUnits = 250 * 40;           // the court keeps its distance from a post the Host holds

        static void Restore()
        {
            foreach (GameNPC n in _hidden)
                Bring(n);
            _hidden.Clear();
        }

        static void Bring(GameNPC n)
        {
            if (n.ObjectState != GameObject.eObjectState.Active && n.ObjectState != GameObject.eObjectState.Deleted)
            {
                n.Health = n.MaxHealth;
                n.AddToWorld();
            }
        }

        // ------------------------------------------------------------------ the word

        static IEnumerable<GamePlayer> InCampaignZones() => ClientService.Instance.GetPlayers()
            .Where(p => p.CurrentRegionID == Region && p.CurrentZone != null && (p.CurrentZone.ID == ForestZone || p.CurrentZone.ID == ValleyZone));

        static void Tell(string text)
        {
            foreach (GamePlayer p in InCampaignZones())
            {
                p.Out.SendMessage("King Lug's Campaign", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                p.Out.SendMessage($"[King Lug's Campaign] {text}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
        }

        /// <summary>The whole realm hears (Hibernia's region).</summary>
        static void Realm(string text)
        {
            foreach (GamePlayer p in ClientService.Instance.GetPlayers().Where(p => p.Realm == eRealm.Hibernia))
                p.Out.SendMessage($"[King Lug's Campaign] {text}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        /// <summary>The zone panel's row (the siege row: event_tracker.gd), in the Valley and the forest - and "lift" the
        /// client's fog patches read (fog_patches.gd: a patch with "lift": "cursed_forest" fades out while it's there).</summary>
        static void Broadcast(DateTime utc)
        {
            if (S.Phase == Phase.Idle)
                return;
            string json = JsonConvert.SerializeObject(new
            {
                name = "King Lug's Campaign", state = S.Phase == Phase.Victory ? "held" : S.Counter != null ? "assault" : "open",
                resolve = Progress(S), enemy = 0, line = Line(S, utc), raids = 0,
                lift = FogLifted(S) ? new[] { "cursed_forest" } : Array.Empty<string>()
            });
            foreach (GamePlayer p in InCampaignZones())
                NewClient.Send(p, "#SIEGE|" + json);
        }

        // ------------------------------------------------------------------ the General

        static void PlaceGeneral()
        {
            if (_general != null && _general.ObjectState == GameObject.eObjectState.Active)
                return;
            Region region = WorldMgr.GetRegion(Region);
            Zone valley = WorldMgr.GetZone(ValleyZone);
            if (region == null || valley == null)
                return;
            var g = new LugGeneral();
            if (NpcTemplateMgr.GetTemplate(SoldierTemplate) is NpcTemplate t)
                g.LoadTemplate(t);
            g.Name = GeneralName;
            g.GuildName = GeneralGuild;
            g.Model = GeneralModel;
            g.Size = 60;
            g.Level = 65;
            g.Realm = eRealm.Hibernia;
            g.Flags |= GameNPC.eFlags.PEACE;
            g.LoadEquipmentTemplateFromDatabase(HostEquipment);
            g.X = (int) (valley.XOffset + GeneralAt[0] * 40);
            g.Y = (int) (valley.YOffset + GeneralAt[1] * 40);
            g.Z = (int) (GeneralAt[2] * 40);
            g.Heading = (ushort) GeneralAt[3];
            g.CurrentRegion = region;
            g.LoadedFromScript = true;
            g.RespawnInterval = -1;
            if (g.AddToWorld())
                _general = g;
        }

        // ------------------------------------------------------------------ kept on disk

        public static void Save()
        {
            try { File.WriteAllText(StatePath, JsonConvert.SerializeObject(S, Formatting.Indented)); }
            catch (Exception ex) { log.Warn("King Lug's campaign: can't save", ex); }
        }

        static void LoadState()
        {
            try
            {
                if (File.Exists(StatePath))
                    S = JsonConvert.DeserializeObject<State>(File.ReadAllText(StatePath)) ?? new State();
            }
            catch (Exception ex)
            {
                log.Warn("King Lug's campaign: can't read the state", ex);
                S = new State();
            }
        }

        // ------------------------------------------------------------------ GM

        public static string Status() => $"King Lug's campaign: {S.Phase}, holding {S.Held} ({(S.Held >= 0 && S.Held < Names.Length ? Names[S.Held] : "-")}), " +
            $"{Line(S, DateTime.UtcNow)}; counter {S.Counter ?? "none"}; won {S.Wins}, lost {S.Losses}";

        public static void Gm(GamePlayer p, string sub, string arg)
        {
            DateTime utc = DateTime.UtcNow;
            long now = Environment.TickCount64;
            switch (sub)
            {
                case "start":
                    S.RestUntilUtc = default;
                    if (S.Phase == Phase.Idle)
                    {
                        S = new State { Phase = Phase.Gate, StartedUtc = utc, StartedBy = p.Name, Wins = S.Wins, Losses = S.Losses };
                        Gate?.CampaignOpen();
                    }
                    break;
                case "take" when int.TryParse(arg, out int n) && n >= 0 && n <= Checkpoints:
                    if (n == 0)
                    {
                        if (S.Phase == Phase.Gate && Gate is SiegeRuntime g)
                        {
                            if (g.Assault?.Active == true)
                                g.Assault.End("fail", now);
                            g.Capture(now);
                        }
                    }
                    else if (S.Phase == Phase.Holding)
                    {
                        for (int i = S.Held + 1; i <= n; i++)
                            Hold(i);
                        Won(S, n, utc);
                    }
                    break;
                case "counter":
                    if (S.Phase == Phase.Holding)
                        S.DeadlineUtc = utc;
                    break;
                case "win":
                    if (S.Phase == Phase.Holding)
                    {
                        Victory(S, utc);
                        Won_();
                    }
                    break;
                case "expire":
                    if (S.Phase == Phase.Victory)
                        S.VictoryUntilUtc = utc;
                    break;
                case "reset":
                    End(false, true);
                    S.RestUntilUtc = default;
                    break;
            }
            Save();
        }
    }

    /// <summary>The General of the Host at Druim Cain: he alone sends the Host into the forest.</summary>
    public class LugGeneral : GameNPC
    {
        public override bool Interact(GamePlayer player)
        {
            if (!base.Interact(player))
                return false;
            LugCampaign.State s = LugCampaign.S;
            if (s.Phase != LugCampaign.Phase.Idle)
            {
                NpcSpeech.SayTo(this, player, $"The Host is in the field. {LugCampaign.Line(s, DateTime.UtcNow)}. Go - the Rangers will show you the way from the Forest Gate.");
                return true;
            }
            if (LugCampaign.CanStart(player.Level, s, DateTime.UtcNow) is string why)
            {
                NpcSpeech.SayTo(this, player, why);
                return true;
            }
            SayTo(player, "The Cursed Forest is the Unseelie Queen's house, and every trouble in the north grows out of it. The King has given me his Host to burn it out - " +
                "the Forest Gate first, then the court's four strongholds, then Cliodna on her seat. It's a long fight, and it goes back if we stop. " +
                "Will you give the word? Say [raise the Host].");
            return true;
        }

        public override bool WhisperReceive(GameLiving source, string text)
        {
            if (source is not GamePlayer p || !base.WhisperReceive(source, text))
                return false;
            if (string.Equals(text?.Trim(), "raise the Host", StringComparison.OrdinalIgnoreCase) && LugCampaign.Raise(p))
                NpcSpeech.Say(this, "Sound the horns! The Host of Lug marches on the Cursed Forest! To the Forest Gate - and no one turns back!");
            return true;
        }
    }

    /// <summary>One of the Host at a checkpoint it holds.</summary>
    public class LugSoldier : GameNPC
    {
        public long DiedAt;

        public override void Die(GameObject killer)
        {
            DiedAt = Environment.TickCount64;
            base.Die(killer);
        }
    }

    /// <summary>The Host fights the court: any monster (or event monster) near its post.</summary>
    public class LugSoldierBrain : StandardMobBrain
    {
        public LugSoldierBrain()
        {
            AggroLevel = 0;
            AggroRange = 0;
            ThinkInterval = 1500;
        }

        public override void Think()
        {
            if (Body != null && Body.IsAlive && !HasAggro)
            {
                GameNPC foe = Body.GetNPCsInRadius(900).OfType<GameNPC>()
                    .Where(n => n.IsAlive && n.Realm == eRealm.None && n is not GameBot && (n.Flags & GameNPC.eFlags.PEACE) == 0 &&
                                (n is EventNpc e ? e.IsEnemy : true) && n.ObjectState == GameObject.eObjectState.Active)
                    .OrderBy(n => n.GetDistanceTo(Body)).FirstOrDefault();
                if (foe != null)
                {
                    AddToAggroList(foe, 100);
                    FSM.SetCurrentState(eFSMStateType.AGGRO);
                }
                else if (Body.SpawnPoint != null && !Body.IsWithinRadius(Body.SpawnPoint, 400) && !Body.IsMoving)
                    Body.WalkTo(Body.SpawnPoint, Body.MaxSpeed);
            }
            base.Think();
        }
    }

    [Cmd("&lug", ePrivLevel.Player,
        "King Lug's campaign on the Cursed Forest",
        "/lug - how it stands",
        "GM: /lug start | take <0-4> | counter | win | expire | reset")]
    public class LugCommandHandler : Commands.AbstractCommandHandler, Commands.ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            if (client.Account.PrivLevel > (uint) ePrivLevel.Player && args.Length > 1)
                LugCampaign.Gm(p, args[1].ToLowerInvariant(), args.Length > 2 ? args[2] : null);
            DisplayMessage(client, LugCampaign.Status());
        }
    }
}
