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
    /// The Southern Muster's campaign on the Sheeroe Hills (claude 2026-11-24, the zone brief and the owner's answers in Zone
    /// Reviews: "I like the idea of the events being pushing into the zone"; "have the younger captain lead a host to your aid
    /// after the Inquisitor falls ... a group who wants to go with you to fell the dragon"; "the previous events success leads
    /// to the raid activating"). Made like King Lug's campaign (LugCampaign.cs), without a siege at the start:
    ///   - only the Muster's Marshal at the Healers' Camp starts it, and only for a player of level 45 or more (anyone may join);
    ///   - four checkpoints, each a harder power check (zone216 events, sh_cpN_assault), each held by the Muster's soldiers:
    ///     the Glimmering Upland, the Azure March (the Grand Inquisitor), the Middle Valleys, the East Valley;
    ///   - held, the Muster has thirty minutes to win the next one; if it doesn't, the Glimmer counter-attacks the last one
    ///     (sh_cpN_counter). Lost, the Muster steps back a checkpoint - back to the camp, and the march is over;
    ///   - past the East Valley, the raid on the Prince's Hollow (sh_princes_hollow: Maldahar the Glimmer Prince);
    ///   - won, the Muster holds the hills for four real hours: the Glimmer's glow lifts (the #SIEGE line's "lift"), its
    ///     monsters are swept out but for the pockets, the Muster's quartermaster stands in the hollow - and Cuuldurach's ring
    ///     is open: the Glimmer King can be fought (sealed in his son's light otherwise), and Captain Ailill's Azure host waits
    ///     by the ring to go in with whoever does.
    /// Bots count: they take the captains' calls and fight the counters like anyone.
    /// </summary>
    public static class MusterCampaign
    {
        public const ushort Region = 200;
        public const int HillsZone = 216;
        public const int MinLevel = 45;
        public const int Checkpoints = 4;
        public const string RaidChain = "sh_princes_hollow";
        public static readonly TimeSpan Window = TimeSpan.FromMinutes(30);
        public static readonly TimeSpan VictoryHold = TimeSpan.FromHours(4);
        public static readonly TimeSpan Rest = TimeSpan.FromMinutes(20);

        public static readonly string[] Names = { "the Healers' Camp", "the Glimmering Upland", "the Azure March", "the Middle Valleys", "the East Valley" };
        // the checkpoints (zone metres and heights, as zone216's events have them) and the sites the Muster sweeps while it holds them
        public static readonly double[][] Posts =
        {
            null,
            new[] { 250.0, 250.0, 88.6 }, new[] { 840.0, 300.0, 123.6 }, new[] { 1000.0, 780.0, 117.7 }, new[] { 1420.0, 1000.0, 89.3 }
        };
        public static readonly string[][] HeldSites =
        {
            new string[0],
            new[] { "cp1_garrison", "cp1_upland", "west_ridge" },
            new[] { "cp2_garrison", "cp2_march", "azure_pyre", "azure_east" },
            new[] { "cp3_garrison", "cp3_valleys", "middle_host" },
            new[] { "cp4_garrison", "cp4_valley" }
        };
        public static readonly double[] Hollow = { 900, 1240, 63.9 };
        public static readonly double[] AzureCamp = { 1330, 1400, 75.3 };     // ~115 m from the ring: outside the King's lair
        public const string PocketPrefix = "pocket_";
        public const string LiftKey = "sheeroe_hills";

        // the Marshal of the Muster, at the Healers' Camp
        public const string MarshalName = "Marshal Fionnuala";
        public const string MarshalGuild = "Marshal of the Southern Muster";
        public static readonly double[] MarshalAt = { 170, 880, 89.4, 1024 };
        public const int SoldierTemplate = 60165769;           // the Sentinels' look
        public const ushort SoldierModel = 328;
        public const string MusterEquipment = "0b7ecfe0-b579-44bc-819f-753a18263762";
        public const string MusterGuild = "the Southern Muster";
        public const int AzureTemplate = 60158171;             // azure avenger
        public const ushort AzureModel = 354;

        public enum Phase { Idle, Holding, Victory }

        public class State
        {
            public Phase Phase;
            public int Held = -1;                  // -1 none, 0 the Healers' Camp (the march has begun), 1..4 the checkpoints
            public DateTime DeadlineUtc;
            public DateTime StartedUtc;
            public DateTime VictoryUntilUtc;
            public DateTime RestUntilUtc;
            public string Counter;
            public string StartedBy;
            public int Wins, Losses;
        }

        public static State S = new();
        static bool _running;                      // (the campaign is loaded: until then, and in the tests, nothing is sealed)
        static readonly List<GameNPC> _soldiers = new();
        static readonly Dictionary<int, List<GameNPC>> _posts = new();
        static readonly List<GameNPC> _hollowCamp = new();
        static readonly List<GameNPC> _azure = new();
        static readonly List<GameNPC> _hidden = new();
        static MusterMarshal _marshal;
        static bool _hooked;
        static long _nextSweep, _nextTell, _nextSave;
        static readonly Logging.Logger log = Logging.LoggerManager.Create(System.Reflection.MethodBase.GetCurrentMethod().DeclaringType);

        static string StatePath => Path.Combine(GameServer.Instance.Configuration.RootDirectory, "muster-campaign-state.json");

        // ------------------------------------------------------------------ the rules (pure: tested)

        public static string CanStart(int level, State s, DateTime nowUtc)
        {
            if (level < MinLevel)
                return $"The hills would eat you alive. Come back at level {MinLevel}, and the Muster will march behind you.";
            if (s.Phase != Phase.Idle)
                return "The Muster is already in the hills. Go and join it.";
            if (nowUtc < s.RestUntilUtc)
                return $"The Muster is resting after the last march. In {Math.Max(1, (int) Math.Ceiling((s.RestUntilUtc - nowUtc).TotalMinutes))} minutes it can march again.";
            return null;
        }

        /// <summary>The Marshal's word: the march begins at the camp, with half an hour to take the upland.</summary>
        public static State Begin(State old, DateTime nowUtc, string by) =>
            new() { Phase = Phase.Holding, Held = 0, StartedUtc = nowUtc, DeadlineUtc = nowUtc + Window, StartedBy = by, Wins = old.Wins, Losses = old.Losses };

        public static string NextAssault(int held) => held >= Checkpoints ? RaidChain : held >= 0 ? $"sh_cp{held + 1}_assault" : null;

        /// <summary>The counter-attack on what the Muster holds (nothing comes for the camp: the march just ends).</summary>
        public static string CounterFor(int held) => held >= 1 ? $"sh_cp{held}_counter" : null;

        public static int AssaultIndex(string chainId)
        {
            if (chainId == RaidChain)
                return Checkpoints + 1;
            if (chainId != null && chainId.StartsWith("sh_cp") && chainId.EndsWith("_assault") && int.TryParse(chainId.Substring(5, 1), out int n))
                return n;
            return 0;
        }

        public static int CounterIndex(string chainId) =>
            chainId != null && chainId.StartsWith("sh_cp") && chainId.EndsWith("_counter") && int.TryParse(chainId.Substring(5, 1), out int n) ? n : 0;

        public static void Won(State s, int n, DateTime nowUtc)
        {
            s.Phase = Phase.Holding;
            s.Held = n;
            s.DeadlineUtc = nowUtc + Window;
            s.Counter = null;
        }

        public static void CounterHeld(State s, DateTime nowUtc)
        {
            s.Counter = null;
            s.DeadlineUtc = nowUtc + Window;
        }

        /// <summary>A counter-attack lost: a step back (true while the Muster still holds a checkpoint).</summary>
        public static bool CounterLost(State s, DateTime nowUtc)
        {
            s.Counter = null;
            s.Held--;
            s.DeadlineUtc = nowUtc + Window;
            return s.Held >= 1;
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

        /// <summary>The Glimmer King's ring: open only while the Muster holds the hills.</summary>
        public static bool RingOpen(State s) => s.Phase == Phase.Victory;

        /// <summary>For Cuuldurach himself (HibCuuldurach.cs) and the bots' realm raids: sealed in his son's light.</summary>
        public static bool CuuldurachSealed => _running && !RingOpen(S);

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
                case Phase.Holding:
                    string held = s.Held >= 0 && s.Held < Names.Length ? Names[s.Held] : "the East Valley";
                    if (s.Counter != null)
                        return $"The Glimmer strikes back at {held}!";
                    string next = s.Held >= Checkpoints ? "the Prince's Hollow" : Names[s.Held + 1];
                    return s.Held == 0 ? $"The Muster marches - {next} in {Clock(s.DeadlineUtc)}" : $"Holding {held} - {next} in {Clock(s.DeadlineUtc)}";
                case Phase.Victory:
                    return $"The hills are the Muster's - the King's ring is open - {Clock(s.VictoryUntilUtc)}";
                default:
                    return "The Glimmer holds the hills";
            }
        }

        public static double Progress(State s) => s.Phase switch
        {
            Phase.Holding => 5 + 19 * Math.Max(0, s.Held),
            Phase.Victory => 100,
            _ => 0
        };

        // ------------------------------------------------------------------ the world

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            _ = new ECSGameTimer(null, _ => { Start(); return 0; }, 26_000);
        }

        static void Start()
        {
            try
            {
                LoadState();
                Hook();
                Arm();
                PlaceMarshal();
                Reconcile();
                _running = true;
                _ = new ECSGameTimer(null, _ => { Tick(); return 1000; }, 1000);
                log.Info($"The Southern Muster's campaign: {S.Phase}, holding {S.Held}");
            }
            catch (Exception ex)
            {
                log.Warn("The Southern Muster's campaign: couldn't start", ex);
            }
        }

        static ChainRuntime Chain(string id) => DynamicEventManager.Chains.FirstOrDefault(c => c.Def.Id == id);

        static void Hook()
        {
            if (_hooked)
                return;
            _hooked = true;
            DynamicEventManager.ChainEnded += OnChainEnded;
        }

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

        public static bool Raise(GamePlayer p)
        {
            if (CanStart(p.Level, S, DateTime.UtcNow) is string why)
            {
                if (_marshal != null)
                    NpcSpeech.SayTo(_marshal, p, why);
                return false;
            }
            S = Begin(S, DateTime.UtcNow, p.Name);
            Realm($"The Southern Muster marches into the Sheeroe Hills! {p.Name} has the Marshal's word. Captain Brogan forms up for the Glimmering Upland - every sword is wanted.");
            Save();
            return true;
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
                    string next = a == Checkpoints ? "the Prince's Hollow itself" : Names[a + 1];
                    Tell($"{Cap(Names[a])} is the Muster's! {Cap(next)} within the half-hour - or the Glimmer comes back.");
                }
            }
            else if (k > 0 && S.Counter == c.Def.Id)
            {
                if (outcome == "success")
                {
                    CounterHeld(S, now);
                    Tell($"The Glimmer breaks against the Muster at {Names[k]}. The line holds - and the clock starts again.");
                }
                else
                {
                    Unhold(k);
                    if (CounterLost(S, now))
                        Tell($"{Cap(Names[k])} has fallen to the Glimmer! The Muster falls back to {Names[S.Held]}.");
                    else
                        Pushed();
                }
            }
            Save();
        }

        static string Cap(string s) => string.IsNullOrEmpty(s) ? s : s[0].ToString().ToUpper() + s.Substring(1);

        static void Tick()
        {
            try
            {
                long now = Environment.TickCount64;
                DateTime utc = DateTime.UtcNow;
                switch (S.Phase)
                {
                    case Phase.Holding:
                        if (S.Counter != null)
                        {
                            bool running = Chain(S.Counter) is ChainRuntime cc && (cc.Active || cc.Dormant);
                            if (!running)
                            {
                                S.Counter = null;
                                S.DeadlineUtc = utc + Window;
                            }
                        }
                        else if (utc >= S.DeadlineUtc)
                        {
                            ChainRuntime next = Chain(NextAssault(S.Held));
                            if (next != null && next.Active)
                                break;
                            if (S.Held == 0)
                            {
                                Tell("No one went up onto the upland. The Muster stands down at the Healers' Camp.");
                                End(false);
                            }
                            else
                                CounterAttack(now);
                        }
                        break;
                    case Phase.Victory:
                        if (utc >= S.VictoryUntilUtc)
                        {
                            Realm("The glow comes back into the Sheeroe Hills, valley by valley. The Glimmer King has called his light home, and his ring is shut again.");
                            End(false);
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
                log.Warn("The Southern Muster's campaign: tick", ex);
            }
        }

        static void CounterAttack(long now)
        {
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
            Realm("The Southern Muster has been pushed out of the Sheeroe Hills. It falls back on the Healers' Camp.");
            End(true);
        }

        static void Won_()
        {
            foreach (ChainRuntime c in DynamicEventManager.Chains.Where(c => c.Zone?.ID == HillsZone && c.Def.Id != RaidChain && (c.Active || c.Dormant)))
                try { c.End("success", Environment.TickCount64); } catch (Exception) { }
            Realm("Maldahar the Glimmer Prince has fallen! The Southern Muster holds the Sheeroe Hills, and the glow is going out. " +
                  "The Glimmer King's ring stands open - and Captain Ailill's Azure host waits beside it for anyone who'll go in.");
            for (int n = 1; n <= Checkpoints; n++)
                Hold(n);
            MakeHollowCamp();
            MakeAzureHost();
            Sweep();
            Save();
        }

        static void End(bool lost)
        {
            Over(S, DateTime.UtcNow, lost);
            foreach (var kv in _posts.ToList())
                Unhold(kv.Key);
            Clear(_hollowCamp);
            Clear(_azure);
            Restore();
            foreach (ChainRuntime c in DynamicEventManager.Chains.Where(c => c.Zone?.ID == HillsZone && (c.Active || c.Dormant)))
                try { c.End("fail", Environment.TickCount64); } catch (Exception) { }
            Save();
        }

        static void Clear(List<GameNPC> list)
        {
            foreach (GameNPC n in list)
                try { n.Delete(); } catch (Exception) { }
            list.Clear();
        }

        static void Reconcile()
        {
            if (S.Phase == Phase.Idle)
                return;
            S.Counter = null;
            int top = S.Phase == Phase.Victory ? Checkpoints : S.Held;
            for (int n = 1; n <= top; n++)
                Hold(n);
            if (S.Phase == Phase.Victory)
            {
                MakeHollowCamp();
                MakeAzureHost();
            }
            if (S.Phase == Phase.Holding && S.DeadlineUtc < DateTime.UtcNow + TimeSpan.FromMinutes(10))
                S.DeadlineUtc = DateTime.UtcNow + TimeSpan.FromMinutes(10);
        }

        // ------------------------------------------------------------------ the Muster's posts

        static Vector3 At(double[] m)
        {
            Zone z = WorldMgr.GetZone(HillsZone);
            return new((float) (z.XOffset + m[0] * 40), (float) (z.YOffset + m[1] * 40), (float) (m[2] * 40.13 + 20));
        }

        static void Hold(int n)
        {
            if (n < 1 || _posts.ContainsKey(n))
                return;
            var list = new List<GameNPC>();
            _posts[n] = list;
            Vector3 c = At(Posts[n]);
            list.Add(Soldier("Banner-Captain of the Muster", MusterGuild, SoldierTemplate, SoldierModel, c, 0, 51, true, new LugSoldierBrain()));
            for (int i = 0; i < 6; i++)
                list.Add(Soldier(i % 3 == 2 ? "keener of the Muster" : "spear of the Muster", MusterGuild, SoldierTemplate, SoldierModel, c, 500, 49, false, new LugSoldierBrain()));
            list.RemoveAll(x => x == null);
        }

        static void Unhold(int n)
        {
            if (!_posts.TryGetValue(n, out var list))
                return;
            Clear(list);
            _posts.Remove(n);
        }

        static void KeepPosts()
        {
            foreach (GameNPC s in _posts.Values.SelectMany(l => l).Concat(_azure))
                if (s is LugSoldier ls && !s.IsAlive && Environment.TickCount64 - ls.DiedAt > 120_000 && s.ObjectState != GameObject.eObjectState.Deleted)
                {
                    s.Health = s.MaxHealth;
                    s.MoveTo(s.CurrentRegionID, s.SpawnPoint.X, s.SpawnPoint.Y, s.SpawnPoint.Z, s.Heading);
                }
        }

        static GameNPC Soldier(string name, string guild, int template, ushort model, Vector3 c, double r, byte level, bool captain, StandardMobBrain brain)
        {
            Region region = WorldMgr.GetRegion(Region);
            if (region == null)
                return null;
            var n = new LugSoldier();
            if (NpcTemplateMgr.GetTemplate(template) is NpcTemplate t)
                n.LoadTemplate(t);
            n.Name = name;
            n.GuildName = guild;
            n.Model = model;
            n.Size = (byte) (captain ? 58 : 52);
            n.Level = level;
            n.Realm = eRealm.Hibernia;
            if (template == SoldierTemplate)
                n.LoadEquipmentTemplateFromDatabase(MusterEquipment);
            double a = Util.RandomDouble() * Math.PI * 2, d = r * Math.Sqrt(Util.RandomDouble());
            n.X = (int) (c.X + Math.Cos(a) * d);
            n.Y = (int) (c.Y + Math.Sin(a) * d);
            n.Z = (int) c.Z;
            n.Heading = (ushort) Util.Random(4095);
            n.CurrentRegion = region;
            n.LoadedFromScript = true;
            n.RespawnInterval = -1;
            n.SetOwnBrain(brain);
            if (!n.AddToWorld())
                return null;
            n.SpawnPoint = new Point3D(n.X, n.Y, n.Z);
            return n;
        }

        /// <summary>Captain Ailill's Azure host (the Inquisitor's turncoats): by the ring while it's open, and into the King's
        /// fight once someone has started it.</summary>
        static void MakeAzureHost()
        {
            if (_azure.Count > 0)
                return;
            Vector3 c = At(AzureCamp);
            _azure.Add(Soldier("Captain Ailill", "of the Azure, sworn to the Muster", AzureTemplate, AzureModel, c, 0, 54, true, new AzureHostBrain()));
            for (int i = 0; i < 7; i++)
                _azure.Add(Soldier(i % 2 == 0 ? "Ailill's avenger" : "Ailill's banisher", "of the Azure, sworn to the Muster", AzureTemplate, i % 2 == 0 ? (ushort) 354 : (ushort) 294, c, 400, 52, false, new AzureHostBrain()));
            _azure.RemoveAll(x => x == null);
        }

        static void MakeHollowCamp()
        {
            if (_hollowCamp.Count > 0)
                return;
            Region region = WorldMgr.GetRegion(Region);
            if (region == null)
                return;
            var host = new SiegeRuntime(new SiegeDef { Id = "southern_muster", Name = MusterGuild, Faction = "southern_muster" });
            Vector3 c = At(Hollow);
            foreach (SiegeNpcDef d in HollowCamp())
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
                n.LoadEquipmentTemplateFromDatabase(MusterEquipment);
                n.X = (int) (c.X + d.Pos[0] * 40);
                n.Y = (int) (c.Y + d.Pos[1] * 40);
                n.Z = (int) c.Z;
                n.Heading = (ushort) Util.Random(4095);
                n.CurrentRegion = region;
                n.LoadedFromScript = true;
                n.RespawnInterval = -1;
                if (n.AddToWorld())
                    _hollowCamp.Add(n);
            }
        }

        /// <summary>The hollow's camp (Pos: metres from the hollow).</summary>
        public static List<SiegeNpcDef> HollowCamp() => new()
        {
            new SiegeNpcDef
            {
                Kind = "marks", Name = "Quartermaster Eithne of the Muster", Guild = MusterGuild, Model = 328, Pos = new[] { -6.0, 4.0 },
                Greet = "The Prince's own hollow, and us standing in it. Marks of Valor, and the Muster's best - take it before the light comes back.",
                Stock = new()
                {
                    new SiegeStockDef { Item = "sh216_mantle_of_the_southern_muster", Price = 260 },
                    new SiegeStockDef { Item = "sh216_lightbreaker_s_torc", Price = 240 },
                    new SiegeStockDef { Item = "sh216_hollow_breaker_s_belt", Price = 220 },
                    new SiegeStockDef { Item = "sh216_ring_of_the_dark_lantern", Price = 220 },
                    new SiegeStockDef { Item = "sh216_bracer_of_the_east_valley", Price = 200 },
                    new SiegeStockDef { Item = "sh216_unshining_jewel", Price = 200 },
                }
            },
            new SiegeNpcDef
            {
                Kind = "idle", Name = "Keener Brid", Guild = MusterGuild, Model = 365, Pos = new[] { 5.0, 5.0 },
                Greet = "Listen. Nothing humming. For the first time since I was a girl the hills are just hills. South-east, past the valley, the King's ring is open - " +
                        "and he's in it, and awake. Ailill's people are waiting there for anyone mad enough."
            }
        };

        static void Sweep()
        {
            var away = new HashSet<GameNPC>();
            if (S.Phase == Phase.Victory)
            {
                foreach (string id in ZoneBuilds.SiteIds(HillsZone).Where(id => !id.StartsWith(PocketPrefix)))
                    away.UnionWith(ZoneBuilds.SiteNpcs(HillsZone, id));
            }
            else if (S.Phase == Phase.Holding && S.Held >= 1)
            {
                var posts = Enumerable.Range(1, Math.Min(S.Held, Checkpoints)).Select(n => At(Posts[n])).ToList();
                for (int n = 1; n <= Math.Min(S.Held, Checkpoints); n++)
                    foreach (string id in HeldSites[n])
                        away.UnionWith(ZoneBuilds.SiteNpcs(HillsZone, id));
                foreach (string id in ZoneBuilds.SiteIds(HillsZone))
                    foreach (GameNPC n in ZoneBuilds.SiteNpcs(HillsZone, id))
                        if (n.SpawnPoint != null && posts.Any(p => Math.Sqrt(Math.Pow(n.SpawnPoint.X - p.X, 2) + Math.Pow(n.SpawnPoint.Y - p.Y, 2)) < LugCampaign.PostClearUnits))
                            away.Add(n);
            }
            foreach (GameNPC n in away)
                if (n.ObjectState == GameObject.eObjectState.Active && n.IsAlive && !n.InCombat)
                {
                    n.RemoveFromWorld();
                    if (!_hidden.Contains(n))
                        _hidden.Add(n);
                }
            foreach (GameNPC n in _hidden.Where(n => !away.Contains(n)).ToList())
            {
                Bring(n);
                _hidden.Remove(n);
            }
        }

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

        static IEnumerable<GamePlayer> InHills() => ClientService.Instance.GetPlayers()
            .Where(p => p.CurrentRegionID == Region && p.CurrentZone != null && p.CurrentZone.ID == HillsZone);

        static void Tell(string text)
        {
            foreach (GamePlayer p in InHills())
            {
                p.Out.SendMessage("The Southern Muster", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                p.Out.SendMessage($"[The Southern Muster] {text}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
        }

        static void Realm(string text)
        {
            foreach (GamePlayer p in ClientService.Instance.GetPlayers().Where(p => p.Realm == eRealm.Hibernia))
                p.Out.SendMessage($"[The Southern Muster] {text}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        /// <summary>The zone panel's row, and "lift" for the client's Glimmer haze (fog_patches.json "lift": "sheeroe_hills").</summary>
        static void Broadcast(DateTime utc)
        {
            if (S.Phase == Phase.Idle)
                return;
            string json = JsonConvert.SerializeObject(new
            {
                name = "The Southern Muster", state = S.Phase == Phase.Victory ? "held" : S.Counter != null ? "assault" : "open",
                resolve = Progress(S), enemy = 0, line = Line(S, utc), raids = 0,
                lift = RingOpen(S) ? new[] { LiftKey } : Array.Empty<string>()
            });
            foreach (GamePlayer p in InHills())
                NewClient.Send(p, "#SIEGE|" + json);
        }

        // ------------------------------------------------------------------ the Marshal

        static void PlaceMarshal()
        {
            if (_marshal != null && _marshal.ObjectState == GameObject.eObjectState.Active)
                return;
            Region region = WorldMgr.GetRegion(Region);
            if (region == null || WorldMgr.GetZone(HillsZone) == null)
                return;
            var g = new MusterMarshal();
            if (NpcTemplateMgr.GetTemplate(SoldierTemplate) is NpcTemplate t)
                g.LoadTemplate(t);
            g.Name = MarshalName;
            g.GuildName = MarshalGuild;
            g.Model = 365;
            g.Size = 58;
            g.Level = 65;
            g.Realm = eRealm.Hibernia;
            g.Flags |= GameNPC.eFlags.PEACE;
            g.LoadEquipmentTemplateFromDatabase(MusterEquipment);
            Vector3 at = At(MarshalAt);
            g.X = (int) at.X;
            g.Y = (int) at.Y;
            g.Z = (int) at.Z;
            g.Heading = (ushort) MarshalAt[3];
            g.CurrentRegion = region;
            g.LoadedFromScript = true;
            g.RespawnInterval = -1;
            if (g.AddToWorld())
                _marshal = g;
        }

        // ------------------------------------------------------------------ kept on disk

        public static void Save()
        {
            try { File.WriteAllText(StatePath, JsonConvert.SerializeObject(S, Formatting.Indented)); }
            catch (Exception ex) { log.Warn("The Southern Muster's campaign: can't save", ex); }
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
                log.Warn("The Southern Muster's campaign: can't read the state", ex);
                S = new State();
            }
        }

        // ------------------------------------------------------------------ GM

        public static string Status() => $"The Southern Muster: {S.Phase}, holding {S.Held} ({(S.Held >= 0 && S.Held < Names.Length ? Names[S.Held] : "-")}), " +
            $"{Line(S, DateTime.UtcNow)}; counter {S.Counter ?? "none"}; the King's ring {(CuuldurachSealed ? "sealed" : "open")}; won {S.Wins}, lost {S.Losses}";

        public static void Gm(GamePlayer p, string sub, string arg)
        {
            DateTime utc = DateTime.UtcNow;
            switch (sub)
            {
                case "start":
                    S.RestUntilUtc = default;
                    if (S.Phase == Phase.Idle)
                        S = Begin(S, utc, p.Name);
                    break;
                case "take" when int.TryParse(arg, out int n) && n >= 1 && n <= Checkpoints:
                    if (S.Phase == Phase.Holding)
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
                    End(false);
                    S.RestUntilUtc = default;
                    break;
            }
            Save();
        }
    }

    /// <summary>The Marshal of the Southern Muster at the Healers' Camp: she alone sends the Muster into the hills.</summary>
    public class MusterMarshal : GameNPC
    {
        public override bool Interact(GamePlayer player)
        {
            if (!base.Interact(player))
                return false;
            MusterCampaign.State s = MusterCampaign.S;
            if (s.Phase != MusterCampaign.Phase.Idle)
            {
                NpcSpeech.SayTo(this, player, $"The Muster is in the hills. {MusterCampaign.Line(s, DateTime.UtcNow)}. Go - the captains will tell you where.");
                return true;
            }
            if (MusterCampaign.CanStart(player.Level, s, DateTime.UtcNow) is string why)
            {
                NpcSpeech.SayTo(this, player, why);
                return true;
            }
            SayTo(player, "The Sentinels, Aine's Circle, the Clann of Alainn Bin, the Keeners - every hall in the south has sent its spears, and they're all here, " +
                "in a field of madmen, waiting. The Glimmer King's light is in every valley from here to his ring. We take it back a valley at a time: " +
                "the upland, the Azure's march, the middle valleys, the east - then his son's hollow. It goes back if we stop. Will you give the word? Say [the Muster marches].");
            return true;
        }

        public override bool WhisperReceive(GameLiving source, string text)
        {
            if (source is not GamePlayer p || !base.WhisperReceive(source, text))
                return false;
            if (string.Equals(text?.Trim(), "the Muster marches", StringComparison.OrdinalIgnoreCase) && MusterCampaign.Raise(p))
                NpcSpeech.Say(this, "Horns! The Southern Muster marches! Up onto the upland - and no one turns back!");
            return true;
        }
    }

    /// <summary>Ailill's host: they fight what comes at them, and once the Glimmer King is fighting someone, they go in.</summary>
    public class AzureHostBrain : LugSoldierBrain
    {
        public override void Think()
        {
            if (Body != null && Body.IsAlive && !HasAggro)
            {
                GameNPC king = Body.GetNPCsInRadius(7000).OfType<HibCuuldurach>().FirstOrDefault(k => k.IsAlive && k.InCombat);
                if (king != null)
                {
                    AddToAggroList(king, 100);
                    FSM.SetCurrentState(eFSMStateType.AGGRO);
                }
            }
            base.Think();
        }
    }

    [Cmd("&muster", ePrivLevel.Player,
        "The Southern Muster's campaign on the Sheeroe Hills",
        "/muster - how it stands",
        "GM: /muster start | take <1-4> | counter | win | expire | reset")]
    public class MusterCommandHandler : Commands.AbstractCommandHandler, Commands.ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            if (client.Account.PrivLevel > (uint) ePrivLevel.Player && args.Length > 1)
                MusterCampaign.Gm(p, args[1].ToLowerInvariant(), args.Length > 2 ? args[2] : null);
            DisplayMessage(client, MusterCampaign.Status());
        }
    }
}
