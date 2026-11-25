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
    /// Albion's two campaigns (claude 2026-11-24, "Albion - the plan", round 4: "Llyn Barfog - Elite, Morgana's seat: Morgana's
    /// campaign and raid"; "Dartmoor - Elite, Golestandt's lair: Golestandt's campaign and raid"). Made like the Southern Muster's
    /// (MusterCampaign.cs), one class for both, each with its own word, its own posts and its own file on disk:
    ///   - the Lake Host (Llyn Barfog): only Sir Percival at the Barfog merchants starts it, for a player of level 45 or more;
    ///     four posts round the lake (lb_cpN_assault), held by the Knights of the Lake; held, thirty minutes to take the next or
    ///     Morgana's host strikes back (lb_cpN_counter); past the Fay Wood, the raid at the Gate of Annwn (lb_gate_of_annwn:
    ///     Morgana, MorganaRaid.cs). Won, the lake is the Host's for four real hours: her mist lifts, her host is swept out but
    ///     for a few pockets, and the Host's quartermaster stands at the Gate.
    ///   - the Dragon-Watch (Dartmoor): only Sir Constantine of Cornwall at Grimspound starts it, for a player of level 50 or more;
    ///     four posts down the moor (dm_cpN_assault), held by the Dragon-Watch; past the Pounders' Road, the raid on the
    ///     Giants' Throne (dm_giants_throne: Cormoran of the Mount, for two or three groups). Won, the moor is the Watch's for four hours, its
    ///     quartermaster stands at the throne - and Golestandt's lair is open: the dragon can be fought (sealed in the giants'
    ///     stone otherwise: AlbGolestandt.cs, the bots' realm raids).
    /// Bots count: they take the captains' calls and fight the counters like anyone.
    /// </summary>
    public class AlbionCampaign
    {
        public const ushort Region = 1;
        public const int Checkpoints = 4;
        public static readonly TimeSpan Window = TimeSpan.FromMinutes(30);
        public static readonly TimeSpan VictoryHold = TimeSpan.FromHours(4);
        public static readonly TimeSpan Rest = TimeSpan.FromMinutes(20);
        public const string PocketPrefix = "pocket_";
        public const int SoldierTemplate = 60167630;                     // Albion's garrison look (Black Mountains North's)
        public const string SoldierEquipment = "38762ab0-5f99-47cd-85b0-0bfaa37d71f9";

        // ------------------------------------------------------------------ what each campaign is

        public string Key, Title, Guild, Enemy, Prefix, RaidChain, LiftKey, StateFile, Word;
        public int Zone, MinLevel;
        public string[] Names;                      // [0] where it starts, [1..4] the posts
        public double[][] Posts;                    // zone metres and heights (metres), [0] unused
        public string[][] HeldSites;                // the zone build's sites swept while a post is held
        public double[] Seat;                       // the raid's place: the camp stands there when it's won
        public string MarshalName, MarshalGuild, MarshalGreet, MarshalShout;
        public double[] MarshalAt;                  // x, y, height, heading
        public ushort MarshalModel = 28, SoldierModel = 28;
        public string CaptainName, SpearName, ArcherName;
        public string TooLow, Marching, NoOne, Victorious, Expired, PushedOut, CounterWord, HeldWord, Started;
        public Func<List<SiegeNpcDef>> Camp;

        // ------------------------------------------------------------------ the two

        public static readonly AlbionCampaign Lake = new()
        {
            Key = "lake", Title = "The Lake Host", Guild = "the Knights of the Lake", Enemy = "Morgana's host", Prefix = "lb_cp",
            RaidChain = "lb_gate_of_annwn", LiftKey = "llyn_barfog", StateFile = "lake-campaign-state.json", Word = "for the Lady",
            Zone = 7, MinLevel = 45,
            Names = new[] { "the Barfog merchants", "the Afanc's Shore", "the Bwgan Hills", "the Western Shore", "the Fay Wood" },
            Posts = new[]
            {
                null, new[] { 1000.0, 520.0, 70.8 }, new[] { 560.0, 430.0, 109.3 }, new[] { 260.0, 820.0, 130.4 }, new[] { 500.0, 1300.0, 127.4 }
            },
            HeldSites = new[]
            {
                new string[0],
                new[] { "cp1_garrison", "cp1_shore" },
                new[] { "cp2_garrison", "cp2_hills" },
                new[] { "cp3_garrison", "cp3_shore", "west_hounds" },
                new[] { "cp4_garrison", "cp4_wood" }
            },
            Seat = new[] { 760.0, 1230.0, 117.7 },
            MarshalName = "Sir Percival", MarshalGuild = "Marshal of the Lake Host", MarshalAt = new[] { 905.0, 760.0, 53.1, 1024 },
            MarshalGreet = "Morgana sits at the Gate of Annwn on the south shore, and every hound and cythraul in this valley is hers. The Lady's knights have come " +
                           "from every hall in Albion, and we take the lake back a shore at a time - the Afanc's shore, the bwgan hills, the western shore, the fay wood - " +
                           "then the Gate itself. It all goes back if we stop. Will you give the word? Say [for the Lady].",
            MarshalShout = "Horns! The Lake Host marches! North shore first - and no one turns back!",
            CaptainName = "Banner-Knight of the Lake", SpearName = "knight of the Lake", ArcherName = "longbowman of the Lake",
            TooLow = "Morgana's hounds would have your bones before the first shore. Come back at level {0}, and the Host will march behind you.",
            Marching = "The Lake Host is already on the shore. Go and join it.",
            NoOne = "No one went up the north shore. The Lake Host stands down at the merchants.",
            Victorious = "Morgana le Fay is broken at the Gate of Annwn! The Lake Host holds Llyn Barfog, and her mist is lifting off the water. The Gate is shut - for now.",
            Expired = "The mist comes back over Llyn Barfog, shore by shore. Morgana has mended her gate, and the Host must march again.",
            PushedOut = "The Lake Host has been driven off the shores of Llyn Barfog. It falls back on the merchants.",
            CounterWord = "Morgana's host strikes back at {0}!", HeldWord = "Holding {0} - {1} in {2}",
            Started = "The Lake Host marches on Llyn Barfog! {0} has Sir Percival's word. The Banner-Knight forms up for the Afanc's Shore - every sword is wanted.",
            Camp = () => new()
            {
                new SiegeNpcDef
                {
                    Kind = "marks", Name = "Quartermaster Elaine of the Lake", Guild = "the Knights of the Lake", Model = 38, Pos = new[] { -6.0, 4.0 },
                    Greet = "The Gate of Annwn, shut, and us standing on it. Marks of Valor, and the Lake's best - take it before the mist comes back.",
                    Stock = new()
                    {
                        new SiegeStockDef { Item = "lb007_mantle_of_the_lake_host", Price = 260 },
                        new SiegeStockDef { Item = "lb007_gate_warden_s_torc", Price = 240 },
                        new SiegeStockDef { Item = "lb007_girdle_of_the_bearded_lake", Price = 220 },
                        new SiegeStockDef { Item = "lb007_ring_of_the_shut_gate", Price = 220 },
                        new SiegeStockDef { Item = "lb007_afanc_hide_bracer", Price = 200 },
                        new SiegeStockDef { Item = "lb007_tear_of_the_lady", Price = 200 },
                    }
                },
                new SiegeNpcDef
                {
                    Kind = "idle", Name = "Maiden Nimue's Herald", Guild = "the Maidens of the Lake", Model = 38, Pos = new[] { 5.0, 5.0 },
                    Greet = "Listen. No hounds. For the first time in a hundred years the lake is only a lake. My Lady sends her thanks - and says Morgana is not dead, only beaten."
                }
            }
        };

        public static readonly AlbionCampaign Moor = new()
        {
            Key = "moor", Title = "The Dragon-Watch", Guild = "the Dragon-Watch", Enemy = "the giants", Prefix = "dm_cp",
            RaidChain = "dm_giants_throne", LiftKey = "dartmoor", StateFile = "moor-campaign-state.json", Word = "wake the Watch",
            Zone = 4, MinLevel = 50,
            Names = new[] { "Grimspound", "the Stonecrush Diggings", "the Pony Moor", "the Stonecallers' Ring", "the Pounders' Road" },
            Posts = new[]
            {
                null, new[] { 230.0, 720.0, 91.0 }, new[] { 960.0, 380.0, 26.5 }, new[] { 760.0, 800.0, 14.2 }, new[] { 1060.0, 1180.0, 11.1 }
            },
            HeldSites = new[]
            {
                new string[0],
                new[] { "cp1_garrison", "cp1_diggings" },
                new[] { "cp2_garrison", "cp2_moor" },
                new[] { "cp3_garrison", "cp3_ring", "middle_giants" },
                new[] { "cp4_garrison", "cp4_road" }
            },
            Seat = new[] { 1240.0, 1420.0, 5.6 },
            MarshalName = "Sir Constantine of Cornwall", MarshalGuild = "Marshal of the Dragon-Watch", MarshalAt = new[] { 128.0, 335.0, 119.2, 3072 },
            MarshalModel = 28,
            MarshalGreet = "Golestandt is awake, and every giant on the moor is marching to his tune. Old Gogmagog's throne stands empty in the south-east - and the giants " +
                           "mean to fill it. The Watch takes the moor back a valley at a time: the Stonecrush diggings, the pony moor, the stonecallers' ring, the pounders' road - " +
                           "then the throne. Break the giants, and the dragon has no army. Will you give the word? Say [wake the Watch].",
            MarshalShout = "Horns! The Dragon-Watch marches! Down to the diggings - and no one turns back!",
            CaptainName = "Banner-Warden of the Watch", SpearName = "dragonslayer of the Watch", ArcherName = "crossbowman of the Watch",
            TooLow = "The giants would grind you into the road. Come back at level {0}, and the Watch will march behind you.",
            Marching = "The Dragon-Watch is already on the moor. Go and join it.",
            NoOne = "No one went down to the diggings. The Dragon-Watch stands down at Grimspound.",
            Victorious = "Cormoran has fallen at the Giants' Throne, and his granite crown with him! The Dragon-Watch holds Dartmoor, and the giants are scattering into the hills. " +
                         "Golestandt's lair stands open - and he is awake, and alone.",
            Expired = "The giants come back down off the hills, and the throne stone is warm again. Golestandt's lair is shut in giants' granite once more.",
            PushedOut = "The Dragon-Watch has been driven off Dartmoor. It falls back on Grimspound.",
            CounterWord = "The giants strike back at {0}!", HeldWord = "Holding {0} - {1} in {2}",
            Started = "The Dragon-Watch marches on Dartmoor! {0} has Sir Constantine's word. The Banner-Warden forms up for the Stonecrush diggings - every sword is wanted.",
            Camp = () => new()
            {
                new SiegeNpcDef
                {
                    Kind = "marks", Name = "Quartermaster Hob of the Watch", Guild = "the Dragon-Watch", Model = 28, Pos = new[] { -6.0, 4.0 },
                    Greet = "Gogmagog's own throne, and a Grimspound man sitting on it. Marks of Valor, and the Watch's best - before the giants come back.",
                    Stock = new()
                    {
                        new SiegeStockDef { Item = "dm004_mantle_of_the_dragon_watch", Price = 260 },
                        new SiegeStockDef { Item = "dm004_throne_breaker_s_torc", Price = 240 },
                        new SiegeStockDef { Item = "dm004_giant_s_girdle", Price = 220 },
                        new SiegeStockDef { Item = "dm004_ring_of_grimspound", Price = 220 },
                        new SiegeStockDef { Item = "dm004_granite_bracer", Price = 200 },
                        new SiegeStockDef { Item = "dm004_dragon_s_eye_jewel", Price = 200 },
                    }
                },
                new SiegeNpcDef
                {
                    Kind = "idle", Name = "Sir Wystan", Guild = "the Dragon-Watch", Model = 9, Pos = new[] { 5.0, 5.0 },
                    Greet = "Hear that? Nothing. No drums. South of here, past the knockers' hollow, Golestandt's lair is open, and he knows it. " +
                            "I'd wait for friends, if I were you. I didn't, once."
                }
            }
        };

        public static readonly AlbionCampaign[] All = { Lake, Moor };

        // ------------------------------------------------------------------ the state

        public enum Phase { Idle, Holding, Victory }

        public class State
        {
            public Phase Phase;
            public int Held = -1;                  // -1 none, 0 the march has begun, 1..4 the posts
            public DateTime DeadlineUtc;
            public DateTime StartedUtc;
            public DateTime VictoryUntilUtc;
            public DateTime RestUntilUtc;
            public string Counter;
            public string StartedBy;
            public int Wins, Losses;
        }

        public State S = new();
        bool _running;
        readonly Dictionary<int, List<GameNPC>> _posts = new();
        readonly List<GameNPC> _camp = new();
        readonly List<GameNPC> _hidden = new();
        AlbionMarshal _marshal;
        bool _hooked;
        long _nextSweep, _nextTell, _nextSave;
        readonly Dictionary<ChainRuntime, long> _giverSince = new();
        static readonly Logging.Logger log = Logging.LoggerManager.Create(System.Reflection.MethodBase.GetCurrentMethod().DeclaringType);

        string StatePath => Path.Combine(GameServer.Instance.Configuration.RootDirectory, StateFile);

        public static AlbionCampaign For(string key) => All.FirstOrDefault(c => c.Key == key);

        // ------------------------------------------------------------------ the rules (pure: tested)

        public string CanStart(int level, State s, DateTime nowUtc)
        {
            if (level < MinLevel)
                return string.Format(TooLow, MinLevel);
            if (s.Phase != Phase.Idle)
                return Marching;
            if (nowUtc < s.RestUntilUtc)
                return $"{Cap(Title.Replace("The ", "the "))} is resting after the last march. In {Math.Max(1, (int) Math.Ceiling((s.RestUntilUtc - nowUtc).TotalMinutes))} minutes it can march again.";
            return null;
        }

        public static State Begin(State old, DateTime nowUtc, string by) =>
            new() { Phase = Phase.Holding, Held = 0, StartedUtc = nowUtc, DeadlineUtc = nowUtc + Window, StartedBy = by, Wins = old.Wins, Losses = old.Losses };

        public string NextAssault(int held) => held >= Checkpoints ? RaidChain : held >= 0 ? $"{Prefix}{held + 1}_assault" : null;

        public string CounterFor(int held) => held >= 1 ? $"{Prefix}{held}_counter" : null;

        public int AssaultIndex(string chainId)
        {
            if (chainId == RaidChain)
                return Checkpoints + 1;
            if (chainId != null && chainId.StartsWith(Prefix) && chainId.EndsWith("_assault") && int.TryParse(chainId.Substring(Prefix.Length, 1), out int n))
                return n;
            return 0;
        }

        public int CounterIndex(string chainId) =>
            chainId != null && chainId.StartsWith(Prefix) && chainId.EndsWith("_counter") && int.TryParse(chainId.Substring(Prefix.Length, 1), out int n) ? n : 0;

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

        public static bool IsWon(State s) => s.Phase == Phase.Victory;

        /// <summary>For Golestandt himself (AlbGolestandt.cs) and the bots' realm raids: sealed in the giants' stone until the
        /// Dragon-Watch holds the moor. (Before the campaign is loaded, and in the tests, nothing is sealed.)</summary>
        public static bool GolestandtSealed => Moor._running && !IsWon(Moor.S);

        public string Line(State s, DateTime nowUtc)
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
                    string held = s.Held >= 0 && s.Held < Names.Length ? Names[s.Held] : Names[Checkpoints];
                    if (s.Counter != null)
                        return string.Format(CounterWord, held);
                    string next = s.Held >= Checkpoints ? RaidPlace : Names[s.Held + 1];
                    return s.Held == 0 ? $"{Title} marches - {next} in {Clock(s.DeadlineUtc)}" : string.Format(HeldWord, held, next, Clock(s.DeadlineUtc));
                case Phase.Victory:
                    return $"{Cap(Where)} is {Title.Replace("The ", "the ")}'s - {Clock(s.VictoryUntilUtc)}";
                default:
                    return $"{Cap(Enemy)} {(Key == "lake" ? "holds" : "hold")} {Where}";
            }
        }

        public string RaidPlace => Key == "lake" ? "the Gate of Annwn" : "the Giants' Throne";
        public string Where => Key == "lake" ? "Llyn Barfog" : "Dartmoor";

        public static double Progress(State s) => s.Phase switch
        {
            Phase.Holding => 5 + 19 * Math.Max(0, s.Held),
            Phase.Victory => 100,
            _ => 0
        };

        static string Cap(string s) => string.IsNullOrEmpty(s) ? s : s[0].ToString().ToUpper() + s.Substring(1);

        // ------------------------------------------------------------------ the world

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            foreach (AlbionCampaign c in All)
            {
                AlbionCampaign me = c;
                _ = new ECSGameTimer(null, _ => { me.Start(); return 0; }, 27_000);
            }
        }

        void Start()
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
                log.Info($"{Title}'s campaign: {S.Phase}, holding {S.Held}");
            }
            catch (Exception ex)
            {
                log.Warn($"{Title}'s campaign: couldn't start", ex);
            }
        }

        static ChainRuntime Chain(string id) => DynamicEventManager.Chains.FirstOrDefault(c => c.Def.Id == id);

        void Hook()
        {
            if (_hooked)
                return;
            _hooked = true;
            DynamicEventManager.ChainEnded += OnChainEnded;
        }

        void Arm()
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

        string GateFor(ChainRuntime c)
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

        public bool Raise(GamePlayer p)
        {
            if (CanStart(p.Level, S, DateTime.UtcNow) is string why)
            {
                if (_marshal != null)
                    NpcSpeech.SayTo(_marshal, p, why);
                return false;
            }
            S = Begin(S, DateTime.UtcNow, p.Name);
            Realm(string.Format(Started, p.Name));
            Save();
            return true;
        }

        void OnChainEnded(ChainRuntime c, string outcome)
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
                    string next = a == Checkpoints ? RaidPlace + " itself" : Names[a + 1];
                    Tell($"{Cap(Names[a])} is {Title.Replace("The ", "the ")}'s! {Cap(next)} within the half-hour - or {Enemy} come{(Key == "lake" ? "s" : "")} back.");
                }
            }
            else if (k > 0 && S.Counter == c.Def.Id)
            {
                if (outcome == "success")
                {
                    CounterHeld(S, now);
                    Tell($"{Cap(Enemy)} break{(Key == "lake" ? "s" : "")} against the line at {Names[k]}. It holds - and the clock starts again.");
                }
                else
                {
                    Unhold(k);
                    if (CounterLost(S, now))
                        Tell($"{Cap(Names[k])} has fallen to {Enemy}! {Title} falls back to {Names[S.Held]}.");
                    else
                        Pushed();
                }
            }
            Save();
        }

        void Tick()
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
                                Tell(NoOne);
                                End(false);
                            }
                            else
                                CounterAttack(now);
                        }
                        break;
                    case Phase.Victory:
                        if (utc >= S.VictoryUntilUtc)
                        {
                            Realm(Expired);
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
                log.Warn($"{Title}'s campaign: tick", ex);
            }
        }

        void CounterAttack(long now)
        {
            if (Chain(CounterFor(S.Held)) is ChainRuntime c && !c.Active)
            {
                S.Counter = c.Def.Id;
                c.Begin(c.Def.Start, now);
            }
            else
                S.DeadlineUtc = DateTime.UtcNow + TimeSpan.FromMinutes(2);
        }

        void Pushed()
        {
            Realm(PushedOut);
            End(true);
        }

        void Won_()
        {
            foreach (ChainRuntime c in DynamicEventManager.Chains.Where(c => c.Zone?.ID == Zone && c.Def.Id != RaidChain && (c.Active || c.Dormant)))
                try { c.End("success", Environment.TickCount64); } catch (Exception) { }
            Realm(Victorious);
            for (int n = 1; n <= Checkpoints; n++)
                Hold(n);
            MakeCamp();
            Sweep();
            Save();
        }

        void End(bool lost)
        {
            Over(S, DateTime.UtcNow, lost);
            foreach (var kv in _posts.ToList())
                Unhold(kv.Key);
            Clear(_camp);
            Restore();
            foreach (ChainRuntime c in DynamicEventManager.Chains.Where(c => c.Zone?.ID == Zone && (c.Active || c.Dormant) &&
                                                                              (AssaultIndex(c.Def.Id) > 0 || CounterIndex(c.Def.Id) > 0)))
                try { c.End("fail", Environment.TickCount64); } catch (Exception) { }
            Save();
        }

        static void Clear(List<GameNPC> list)
        {
            foreach (GameNPC n in list)
                try { n.Delete(); } catch (Exception) { }
            list.Clear();
        }

        void Reconcile()
        {
            if (S.Phase == Phase.Idle)
                return;
            S.Counter = null;
            int top = S.Phase == Phase.Victory ? Checkpoints : S.Held;
            for (int n = 1; n <= top; n++)
                Hold(n);
            if (S.Phase == Phase.Victory)
                MakeCamp();
            if (S.Phase == Phase.Holding && S.DeadlineUtc < DateTime.UtcNow + TimeSpan.FromMinutes(10))
                S.DeadlineUtc = DateTime.UtcNow + TimeSpan.FromMinutes(10);
        }

        // ------------------------------------------------------------------ the posts

        Vector3 At(double[] m)
        {
            Zone z = WorldMgr.GetZone((ushort) Zone);
            var v = new Vector3((float) (z.XOffset + m[0] * 40), (float) (z.YOffset + m[1] * 40), (float) (m[2] * 40.13 + 20));
            var nav = PathfindingProvider.Instance;
            if (nav != null && nav.IsAvailable && nav.HasNavmesh(z))
            {
                Vector3? floor = nav.GetClosestPoint(z, v, 96, 96, 2048, nav.DefaultFilters);
                if (floor.HasValue)
                    return floor.Value;
            }
            return v;
        }

        void Hold(int n)
        {
            if (n < 1 || _posts.ContainsKey(n))
                return;
            var list = new List<GameNPC>();
            _posts[n] = list;
            Vector3 c = At(Posts[n]);
            list.Add(Soldier(CaptainName, c, 0, 51, true));
            for (int i = 0; i < 6; i++)
                list.Add(Soldier(i % 3 == 2 ? ArcherName : SpearName, c, 500, 49, false));
            list.RemoveAll(x => x == null);
        }

        void Unhold(int n)
        {
            if (!_posts.TryGetValue(n, out var list))
                return;
            Clear(list);
            _posts.Remove(n);
        }

        void KeepPosts()
        {
            foreach (GameNPC s in _posts.Values.SelectMany(l => l))
                if (s is LugSoldier ls && !s.IsAlive && Environment.TickCount64 - ls.DiedAt > 120_000 && s.ObjectState != GameObject.eObjectState.Deleted)
                {
                    s.Health = s.MaxHealth;
                    s.MoveTo(s.CurrentRegionID, s.SpawnPoint.X, s.SpawnPoint.Y, s.SpawnPoint.Z, s.Heading);
                }
        }

        GameNPC Soldier(string name, Vector3 c, double r, byte level, bool captain)
        {
            Region region = WorldMgr.GetRegion(Region);
            if (region == null)
                return null;
            var n = new LugSoldier();
            if (NpcTemplateMgr.GetTemplate(SoldierTemplate) is NpcTemplate t)
                n.LoadTemplate(t);
            n.Name = name;
            n.GuildName = Guild;
            n.Model = SoldierModel;
            n.Size = (byte) (captain ? 58 : 52);
            n.Level = level;
            n.Realm = eRealm.Albion;
            n.LoadEquipmentTemplateFromDatabase(SoldierEquipment);
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

        void MakeCamp()
        {
            if (_camp.Count > 0)
                return;
            Region region = WorldMgr.GetRegion(Region);
            if (region == null)
                return;
            var host = new SiegeRuntime(new SiegeDef { Id = Key + "_host", Name = Guild, Faction = Key == "lake" ? "knights_of_the_lake" : "dragon_watch" });
            Vector3 c = At(Seat);
            foreach (SiegeNpcDef d in Camp())
            {
                GameNPC n = d.Kind == "marks" ? new SiegeMarksMerchant { Siege = host, Def = d } : new SiegeCampNpc { Siege = host, Def = d };
                if (NpcTemplateMgr.GetTemplate(SoldierTemplate) is NpcTemplate t)
                    n.LoadTemplate(t);
                n.Name = d.Name;
                n.GuildName = d.Guild;
                n.Model = d.Model;
                n.Size = 54;
                n.Level = 55;
                n.Realm = eRealm.Albion;
                n.Flags |= GameNPC.eFlags.PEACE;
                n.LoadEquipmentTemplateFromDatabase(SoldierEquipment);
                n.X = (int) (c.X + d.Pos[0] * 40);
                n.Y = (int) (c.Y + d.Pos[1] * 40);
                n.Z = (int) c.Z;
                n.Heading = (ushort) Util.Random(4095);
                n.CurrentRegion = region;
                n.LoadedFromScript = true;
                n.RespawnInterval = -1;
                if (n.AddToWorld())
                    _camp.Add(n);
            }
        }

        void Sweep()
        {
            var away = new HashSet<GameNPC>();
            if (S.Phase == Phase.Victory)
            {
                foreach (string id in ZoneBuilds.SiteIds(Zone).Where(id => !id.StartsWith(PocketPrefix)))
                    away.UnionWith(ZoneBuilds.SiteNpcs(Zone, id));
            }
            else if (S.Phase == Phase.Holding && S.Held >= 1)
            {
                var posts = Enumerable.Range(1, Math.Min(S.Held, Checkpoints)).Select(n => At(Posts[n])).ToList();
                for (int n = 1; n <= Math.Min(S.Held, Checkpoints); n++)
                    foreach (string id in HeldSites[n])
                        away.UnionWith(ZoneBuilds.SiteNpcs(Zone, id));
                foreach (string id in ZoneBuilds.SiteIds(Zone))
                    foreach (GameNPC n in ZoneBuilds.SiteNpcs(Zone, id))
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

        void Restore()
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

        IEnumerable<GamePlayer> InZone() => ClientService.Instance.GetPlayers()
            .Where(p => p.CurrentRegionID == Region && p.CurrentZone != null && p.CurrentZone.ID == Zone);

        void Tell(string text)
        {
            foreach (GamePlayer p in InZone())
            {
                p.Out.SendMessage(Title, eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                p.Out.SendMessage($"[{Title}] {text}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
        }

        void Realm(string text)
        {
            foreach (GamePlayer p in ClientService.Instance.GetPlayers().Where(p => p.Realm == eRealm.Albion))
                p.Out.SendMessage($"[{Title}] {text}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        /// <summary>The zone panel's row, and "lift" for the client's fog (fog_patches.json "lift": LiftKey).</summary>
        void Broadcast(DateTime utc)
        {
            if (S.Phase == Phase.Idle)
                return;
            string json = JsonConvert.SerializeObject(new
            {
                name = Title, state = S.Phase == Phase.Victory ? "held" : S.Counter != null ? "assault" : "open",
                resolve = Progress(S), enemy = 0, line = Line(S, utc), raids = 0,
                lift = IsWon(S) ? new[] { LiftKey } : Array.Empty<string>()
            });
            foreach (GamePlayer p in InZone())
                NewClient.Send(p, "#SIEGE|" + json);
        }

        // ------------------------------------------------------------------ the Marshal

        void PlaceMarshal()
        {
            if (_marshal != null && _marshal.ObjectState == GameObject.eObjectState.Active)
                return;
            Region region = WorldMgr.GetRegion(Region);
            if (region == null || WorldMgr.GetZone((ushort) Zone) == null)
                return;
            var g = new AlbionMarshal { Campaign = this };
            if (NpcTemplateMgr.GetTemplate(SoldierTemplate) is NpcTemplate t)
                g.LoadTemplate(t);
            g.Name = MarshalName;
            g.GuildName = MarshalGuild;
            g.Model = MarshalModel;
            g.Size = 58;
            g.Level = 65;
            g.Realm = eRealm.Albion;
            g.Flags |= GameNPC.eFlags.PEACE;
            g.LoadEquipmentTemplateFromDatabase(SoldierEquipment);
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

        public void Save()
        {
            try { File.WriteAllText(StatePath, JsonConvert.SerializeObject(S, Formatting.Indented)); }
            catch (Exception ex) { log.Warn($"{Title}'s campaign: can't save", ex); }
        }

        void LoadState()
        {
            try
            {
                if (File.Exists(StatePath))
                    S = JsonConvert.DeserializeObject<State>(File.ReadAllText(StatePath)) ?? new State();
            }
            catch (Exception ex)
            {
                log.Warn($"{Title}'s campaign: can't read the state", ex);
                S = new State();
            }
        }

        // ------------------------------------------------------------------ GM

        public string Status() => $"{Title}: {S.Phase}, holding {S.Held} ({(S.Held >= 0 && S.Held < Names.Length ? Names[S.Held] : "-")}), " +
            $"{Line(S, DateTime.UtcNow)}; counter {S.Counter ?? "none"}" + (Key == "moor" ? $"; Golestandt {(GolestandtSealed ? "sealed" : "open")}" : "") +
            $"; won {S.Wins}, lost {S.Losses}";

        public void Gm(GamePlayer p, string sub, string arg)
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

    /// <summary>A campaign's marshal (Sir Percival at the Barfog merchants, Sir Constantine at Grimspound): they alone send
    /// the host out.</summary>
    public class AlbionMarshal : GameNPC
    {
        public AlbionCampaign Campaign;

        public override bool Interact(GamePlayer player)
        {
            if (!base.Interact(player) || Campaign == null)
                return false;
            AlbionCampaign.State s = Campaign.S;
            if (s.Phase != AlbionCampaign.Phase.Idle)
            {
                NpcSpeech.SayTo(this, player, $"{Campaign.Line(s, DateTime.UtcNow)}. Go - the captains will tell you where.");
                return true;
            }
            if (Campaign.CanStart(player.Level, s, DateTime.UtcNow) is string why)
            {
                NpcSpeech.SayTo(this, player, why);
                return true;
            }
            SayTo(player, Campaign.MarshalGreet);
            return true;
        }

        public override bool WhisperReceive(GameLiving source, string text)
        {
            if (source is not GamePlayer p || !base.WhisperReceive(source, text) || Campaign == null)
                return false;
            if (string.Equals(text?.Trim(), Campaign.Word, StringComparison.OrdinalIgnoreCase) && Campaign.Raise(p))
                NpcSpeech.Say(this, Campaign.MarshalShout);
            return true;
        }
    }

    [Cmd("&albcampaign", ePrivLevel.Player,
        "Albion's campaigns: the Lake Host on Llyn Barfog, the Dragon-Watch on Dartmoor",
        "/albcampaign - how they stand",
        "GM: /albcampaign <lake|moor> start | take <1-4> | counter | win | expire | reset")]
    public class AlbionCampaignCommandHandler : Commands.AbstractCommandHandler, Commands.ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            if (client.Account.PrivLevel > (uint) ePrivLevel.Player && args.Length > 2 && AlbionCampaign.For(args[1].ToLowerInvariant()) is AlbionCampaign c)
                c.Gm(p, args[2].ToLowerInvariant(), args.Length > 3 ? args[3] : null);
            foreach (AlbionCampaign k in AlbionCampaign.All)
                DisplayMessage(client, k.Status());
        }
    }
}
