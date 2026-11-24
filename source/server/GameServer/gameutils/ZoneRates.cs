using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// What a zone's monsters are worth (owner 2026-11-20: "We don't really have any incentive for players to leave the
    /// 'peaceful' danger rating areas ... XP modifiers for each type of zone. 0.8x for peaceful, 1.0 for Wild, 1.2x for
    /// Dangerous, 1.4x for Deadly. Also, to incentivize exploration ... a 2x bonus that deteriorates by .5 every hour, until
    /// it gets to a .5x exp rate (penalty) where it sits. It resets after 24 hours" - with the agreed refinements: the hours
    /// count only time spent in the zone; event and quest experience aren't touched; zones without a rating yet get one
    /// from their old level range; bots move on when their rate drops under 1x; a Zone panel shows the rate):
    ///   Rate = the zone's rating factor x your exploration factor there. Monster kill experience and the coin monsters
    ///   drop are multiplied by it (AbstractServerRules).
    ///   Exploration: a fresh zone pays 2x; every hour you spend in it takes 0.5 off, down to 0.5x, and every 2 hours spent
    ///   anywhere else (logged out too) gives 0.5 back, up to 2x. So a Deadly zone goes 2.8, 2.1, 1.4, 0.7; a Peaceful one
    ///   1.6, 1.2, 0.8, 0.4 - and roaming three or more zones keeps you well above 1x.
    ///   Ratings: a zone build's "rating" (scripts/zonebuilds/*.json); else from the median level its monsters were placed
    ///   at: under 15 Peaceful, 15-29 Wild, 30-44 Dangerous, 45+ Deadly (until each zone's review sets its own).
    /// Players' visits are kept with the character (DbCoreCharacterXCustomParam "zonevisits"); bots' in memory.
    /// </summary>
    public static class ZoneRates
    {
        /// <summary>(Elite added 2026-11-23, owner: "we will also need an Elite rating for a zone, which will be the Cursed
        /// Forest and Sheeroe Hills" - the step past Deadly.)</summary>
        public enum Rating { Peaceful, Wild, Dangerous, Deadly, Elite }

        public const double ExploreStart = 2.0, ExploreStep = 0.5, ExploreFloor = 0.5;
        public const double StepMinutes = 60, ResetHours = 24;
        /// <summary>Away from a zone (elsewhere or logged out), its exploration comes back: half a minute of its hours for
        /// every minute away - 0.5x back for every 2 hours, full 2x again 6 hours after its floor (owner 2026-11-20: "A
        /// recovery rate is a great solution ... Go with that", instead of a reset 24 hours after the first visit, which a
        /// 2-hour reset would have let two neighbouring zones ping-pong around).</summary>
        public const double RecoverPerMinuteAway = 0.5;
        const long AwaySeconds = 120;
        const string ParamKey = "zonevisits";
        const int TickMs = 30_000;

        public static double Factor(Rating r) => r switch
        {
            Rating.Peaceful => 0.8, Rating.Wild => 1.0, Rating.Dangerous => 1.2, Rating.Deadly => 1.4, _ => 1.6
        };

        // ------------------------------------------------------------------ each rating a step harder

        /// <summary>Each rating a step harder than the one below (owner 2026-11-23: "higher zone difficulty tiers [should]
        /// actually feel more difficult. So blue mobs in Wild are slightly harder than blue mobs in Peaceful ... maybe their
        /// attacks do a bit more damage (especially their special attacks) ... It shouldn't be so drastic that people are
        /// confused ... but it should be noticeable"; the moderate steps chosen): per step above Peaceful a monster hits
        /// HitStep harder, its special attacks (styles, heavy blows, cones, slams) SpecialStep harder in all, and it takes
        /// TakeStep less damage. Elite (four steps): hits +32%, specials +48%, takes 12% less.</summary>
        public const double HitStep = 0.08, SpecialStep = 0.12, TakeStep = 0.03;

        public static int Step(Rating r) => (int) r;

        /// <summary>How hard a monster of this rating hits, against the same con in a Peaceful zone.</summary>
        public static double Hits(Rating r) => 1.0 + HitStep * Step(r);

        /// <summary>A special attack's further factor on top of Hits (so a special is SpecialStep a step harder in all).</summary>
        public static double SpecialExtra(Rating r) => (1.0 + SpecialStep * Step(r)) / Hits(r);

        /// <summary>The damage a monster of this rating takes, against the same con in a Peaceful zone.</summary>
        public static double Takes(Rating r) => 1.0 - TakeStep * Step(r);

        public static double HitsIn(Zone z) => z == null ? 1.0 : Hits(RatingOf(z));
        public static double SpecialExtraIn(Zone z) => z == null ? 1.0 : SpecialExtra(RatingOf(z));
        public static double TakesIn(Zone z) => z == null ? 1.0 : Takes(RatingOf(z));

        // ------------------------------------------------------------------ ratings

        static Dictionary<int, Rating> _authored;
        static readonly ConcurrentDictionary<int, Rating> _ratings = new();

        static Dictionary<int, Rating> Authored()
        {
            if (_authored != null)
                return _authored;
            var d = new Dictionary<int, Rating>();
            try
            {
                Assembly asm = typeof(ZoneRates).Assembly;
                foreach (string res in asm.GetManifestResourceNames().Where(n => n.StartsWith("ZoneBuilds.") && n.EndsWith(".json")))
                {
                    using Stream s = asm.GetManifestResourceStream(res);
                    using var r = new StreamReader(s);
                    Read(r.ReadToEnd(), d);
                }
                string dir = Path.Combine(GameServer.Instance.Configuration.RootDirectory, "zone-builds");
                if (Directory.Exists(dir))
                    foreach (string f in Directory.GetFiles(dir, "*.json").OrderBy(f => f))
                        Read(File.ReadAllText(f), d);
            }
            catch (Exception e)
            {
                Console.WriteLine("[ZoneRates] ratings: " + e.Message);
            }
            return _authored = d;
        }

        static void Read(string json, Dictionary<int, Rating> d)
        {
            try
            {
                using JsonDocument doc = JsonDocument.Parse(json, new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true });
                JsonElement root = doc.RootElement;
                if (root.TryGetProperty("zone", out JsonElement z) && root.TryGetProperty("rating", out JsonElement r) &&
                    Enum.TryParse(r.GetString(), true, out Rating rating))
                    d[z.GetInt32()] = rating;
            }
            catch { }
        }

        public static Rating RatingOf(Zone zone)
        {
            if (zone == null)
                return Rating.Wild;
            return _ratings.GetOrAdd(zone.ID, _ =>
            {
                if (Authored().TryGetValue(zone.ID, out Rating r))
                    return r;
                int median = MonsterTiers.ZoneMedianLevel(zone, zone.ZoneRegion);
                return median <= 0 ? Rating.Peaceful : median < 15 ? Rating.Peaceful : median < 30 ? Rating.Wild
                    : median < 45 ? Rating.Dangerous : Rating.Deadly;
            });
        }

        // ------------------------------------------------------------------ visits

        sealed class Visit
        {
            public long LastUnix;           // seconds: when it was last counted
            public double Minutes;          // its hours drawn down (minutes spent there, less what time away gave back)
        }

        sealed class Visits
        {
            public readonly Dictionary<int, Visit> ByZone = new();
            public readonly Dictionary<string, long> EventsDone = new();   // event -> unix seconds of its last bonus
            public int LastZone = -1;
            public long LastTick;           // game loop ms of the last count
            public bool Dirty;
            public long NextMoveCheck;
        }

        static readonly ConditionalWeakTable<GameLiving, Visits> _visits = new();

        static long NowUnix => DateTimeOffset.UtcNow.ToUnixTimeSeconds();

        static Visits Of(GameLiving who) => _visits.GetValue(who, w => w is GamePlayer p ? Load(p) : new Visits());

        /// <summary>A zone's drawn-down minutes now, with what the time away has given back (no change made).</summary>
        static double MinutesNow(Visit visit, long now)
        {
            if (visit == null)
                return 0;
            long gap = now - visit.LastUnix;
            return gap > AwaySeconds ? Math.Max(0, visit.Minutes - gap / 60.0 * RecoverPerMinuteAway) : visit.Minutes;
        }

        static double MinutesNow(Visits v, Zone zone) =>
            v.ByZone.TryGetValue(zone.ID, out Visit visit) ? MinutesNow(visit, NowUnix) : 0;

        /// <summary>Their visit to the zone they're in, its time away settled.</summary>
        static Visit Settle(Visits v, Zone zone)
        {
            long now = NowUnix;
            if (!v.ByZone.TryGetValue(zone.ID, out Visit visit))
            {
                visit = new Visit { LastUnix = now };
                v.ByZone[zone.ID] = visit;
                v.Dirty = true;
            }
            else if (now - visit.LastUnix > AwaySeconds)
            {
                visit.Minutes = MinutesNow(visit, now);
                visit.LastUnix = now;
                v.Dirty = true;
            }
            return visit;
        }

        /// <summary>Count the time since the last count toward the zone they're in (gaps of over two minutes - logged
        /// out, a long load - don't count).</summary>
        public static void Touch(GameLiving who)
        {
            Zone zone = who?.CurrentZone;
            if (zone == null)
                return;
            Visits v = Of(who);
            long now = GameLoop.GameLoopTime;
            Visit visit = Settle(v, zone);
            if (v.LastZone == zone.ID && v.LastTick > 0)
            {
                long gap = now - v.LastTick;
                if (gap > 0 && gap <= 120_000)
                {
                    visit.Minutes += gap / 60_000.0;
                    v.Dirty = true;
                }
            }
            visit.LastUnix = NowUnix;
            v.LastZone = zone.ID;
            v.LastTick = now;
        }

        public static double ExploreFactor(GameLiving who, Zone zone)
        {
            if (who == null || zone == null)
                return 1.0;
            int steps = (int) Math.Floor(MinutesNow(Of(who), zone) / StepMinutes);
            return Math.Max(ExploreFloor, ExploreStart - ExploreStep * steps);
        }

        /// <summary>The rate where they are now: the zone's rating x their exploration there.</summary>
        public static double Rate(GameLiving who)
        {
            Zone zone = who?.CurrentZone;
            if (zone == null)
                return 1.0;
            Touch(who);
            return Factor(RatingOf(zone)) * ExploreFactor(who, zone);
        }

        /// <summary>A kill's experience / coin multiplier for this player or bot (pets: their owner's).</summary>
        public static double KillFactor(GameLiving who)
        {
            try
            {
                return Rate(MonsterTiers.Combatant(who) ?? who);
            }
            catch
            {
                return 1.0;
            }
        }

        /// <summary>Minutes until the exploration factor here next drops (-1: at the floor).</summary>
        public static double MinutesToNextDrop(GameLiving who, Zone zone)
        {
            if (ExploreFactor(who, zone) <= ExploreFloor)
                return -1;
            return StepMinutes - MinutesNow(Of(who), zone) % StepMinutes;
        }

        // ------------------------------------------------------------------ events

        public const double FirstEventBonus = 1.5;

        /// <summary>DynamicEventRuntime: the experience multiplier for finishing this event - 1.5x the first time in 24
        /// hours (then it is marked done), else 1x. Event experience is never touched by the zone's rate.</summary>
        public static double EventFactor(GameLiving who, string eventKey)
        {
            if (who == null || string.IsNullOrEmpty(eventKey))
                return 1.0;
            Visits v = Of(who);
            string key = eventKey.Replace(':', ' ').Replace(';', ' ');
            long now = NowUnix;
            if (v.EventsDone.TryGetValue(key, out long at) && now - at < ResetHours * 3600)
                return 1.0;
            v.EventsDone[key] = now;
            v.Dirty = true;
            (who as GamePlayer)?.Out.SendMessage($"First time today: {FirstEventBonus:0.#}x experience!", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            return FirstEventBonus;
        }

        // ------------------------------------------------------------------ bots

        /// <summary>AutonomousWorldBotController: a soloing bot leaves a camp whose zone pays under 1x (checked every few
        /// minutes, so it doesn't flit).</summary>
        public static bool ShouldMoveOn(GameBot bot)
        {
            if (bot == null)
                return false;
            Visits v = Of(bot);
            long now = GameLoop.GameLoopTime;
            if (now < v.NextMoveCheck)
                return false;
            v.NextMoveCheck = now + 300_000 + bot.ObjectID % 60_000;
            return Rate(bot) < 1.0;
        }

        /// <summary>A bot choosing a camp: the zones that pay it at least 1x, if any; else all.</summary>
        public static T[] PreferPaying<T>(GameBot bot, T[] camps, Func<T, Zone> zoneOf)
        {
            if (bot == null || camps == null || camps.Length < 2)
                return camps;
            T[] paying = camps.Where(c => zoneOf(c) is not Zone z || Factor(RatingOf(z)) * ExploreFactor(bot, z) >= 1.0).ToArray();
            return paying.Length > 0 ? paying : camps;
        }

        // ------------------------------------------------------------------ players: saving, the zone panel

        static Visits Load(GamePlayer p)
        {
            var v = new Visits();
            try
            {
                DbCoreCharacterXCustomParam rec = Record(p);
                foreach (string part in (rec?.Value ?? "").Split(';', StringSplitOptions.RemoveEmptyEntries))
                {
                    string[] f = part.Split(':');
                    if (f.Length == 3 && f[0] == "e" && long.TryParse(f[2], out long done))
                        v.EventsDone[f[1]] = done;
                    else if (f.Length == 3 && int.TryParse(f[0], out int zone) && long.TryParse(f[1], out long first) &&
                        double.TryParse(f[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double min))
                        v.ByZone[zone] = new Visit { LastUnix = first, Minutes = min };
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("[ZoneRates] load: " + e.Message);
            }
            return v;
        }

        static DbCoreCharacterXCustomParam Record(GamePlayer p) =>
            DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
                DB.Column("DOLCharactersObjectId").IsEqualTo(p.ObjectId).And(DB.Column("KeyName").IsEqualTo(ParamKey)));

        static void Save(GamePlayer p)
        {
            if (!_visits.TryGetValue(p, out Visits v) || !v.Dirty)
                return;
            long now = NowUnix;
            string value = string.Join(";", v.ByZone.Where(kv => MinutesNow(kv.Value, now) > 0)
                .Select(kv => $"{kv.Key}:{kv.Value.LastUnix}:{kv.Value.Minutes.ToString("0.##", System.Globalization.CultureInfo.InvariantCulture)}")
                .Concat(v.EventsDone.Where(kv => now - kv.Value < ResetHours * 3600).Select(kv => $"e:{kv.Key}:{kv.Value}")));
            try
            {
                DbCoreCharacterXCustomParam rec = Record(p);
                if (rec == null)
                    GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(p.ObjectId, ParamKey, value));
                else
                {
                    rec.Value = value;
                    GameServer.Database.SaveObject(rec);
                }
                v.Dirty = false;
            }
            catch (Exception e)
            {
                Console.WriteLine("[ZoneRates] save: " + e.Message);
            }
        }

        /// <summary>The zone panel's line: "#ZXP|zone|rating|rate|exploration|minutes to the next drop (-1 none)".</summary>
        public static void Push(GamePlayer p)
        {
            Zone zone = p?.CurrentZone;
            if (zone == null)
                return;
            double rate = Rate(p);
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            NewClient.Send(p, $"#ZXP|{(zone.Description ?? "").Replace("|", "/")}|{RatingOf(zone)}|{rate.ToString("0.0#", ci)}|" +
                $"{ExploreFactor(p, zone).ToString("0.0#", ci)}|{MinutesToNextDrop(p, zone).ToString("0", ci)}");
        }

        static int _saveCountdown;

        static int Tick(ECSGameTimer t)
        {
            try
            {
                bool save = ++_saveCountdown >= 10;          // every 5 minutes
                if (save)
                    _saveCountdown = 0;
                foreach (GamePlayer p in ClientService.Instance.GetPlayers())
                {
                    if (p?.ObjectState != GameObject.eObjectState.Active)
                        continue;
                    Push(p);
                    if (save)
                        Save(p);
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("[ZoneRates] tick: " + e.Message);
            }
            return TickMs;
        }

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GamePlayerEvent.Quit, new DOLEventHandler((ev, s, a) => { if (s is GamePlayer qp) Save(qp); }));
            GameEventMgr.AddHandler(GamePlayerEvent.RegionChanged, new DOLEventHandler((ev, s, a) => { if (s is GamePlayer zp) Push(zp); }));
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, new DOLEventHandler((ev, s, a) => { if (s is GamePlayer gp) Push(gp); }));
            _ = new ECSGameTimer(null, Tick, TickMs);
        }
    }
}
