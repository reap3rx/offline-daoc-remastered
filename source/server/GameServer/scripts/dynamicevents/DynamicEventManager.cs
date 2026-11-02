using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Reflection;
using System.Text;
using DOL.Events;
using DOL.GS.PacketHandler;
using Newtonsoft.Json;

namespace DOL.GS.DynamicEvents
{
    /// <summary>
    /// Loads the zones' dynamic events, runs them on a one-second timer and tells the players' clients about them:
    /// "#EV|" system lines (the new client takes them out of the chat, as it does Action Combat's "#AC|") carrying the
    /// zone's events as JSON every two seconds - the tracker shows the ones you are near, the map all of them.
    /// </summary>
    public static class DynamicEventManager
    {
        public const string Prefix = "#EV|";
        static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);
        public static readonly List<ChainRuntime> Chains = new();
        static ECSGameTimer _timer;
        static long _ticks;
        static readonly HashSet<GamePlayer> _told = new();

        static long Now => Environment.TickCount64;
        public static long StartedAt;

        // ---------------------------------------------------------------- what outlasts a restart: occupations

        static string StatePath => Path.Combine(GameServer.Instance.Configuration.RootDirectory, "dynamic-events-state.json");
        static bool _loading;

        /// <summary>The occupations running (a captured tower, a road the siog hold - or a tower being retaken): written
        /// whenever a stage starts or a chain ends, read at start-up - an occupation is still there when the server
        /// comes back.</summary>
        public static void SaveState()
        {
            if (_loading)
                return;
            try
            {
                var held = Chains.Where(c => c.Occupied || c.Displaced.Count > 0 || c.ResumeStage != null)
                    .ToDictionary(c => c.Def.Id, c => c.ResumeStage ?? c.Stage?.Def.Id ?? c.PendingId);
                File.WriteAllText(StatePath, JsonConvert.SerializeObject(held, Formatting.Indented));
            }
            catch (Exception ex)
            {
                log.Warn("Dynamic events: can't save the occupations", ex);
            }
        }

        static void LoadState()
        {
            try
            {
                if (!File.Exists(StatePath))
                    return;
                var held = JsonConvert.DeserializeObject<Dictionary<string, string>>(File.ReadAllText(StatePath));
                foreach (var (id, stage) in held ?? new())
                    if (Chains.FirstOrDefault(c => c.Def.Id == id) is ChainRuntime c && c.Def.Stages.Any(s => s.Id == stage))
                    {
                        c.ResumeStage = stage;
                        Trace($"{c.Def.Title}: still occupied ({stage})");
                    }
            }
            catch (Exception ex)
            {
                log.Warn("Dynamic events: can't read the occupations", ex);
            }
        }

        public static void Trace(string line) => log.Info("Dynamic events: " + line);

        [GameServerStartedEvent]
        public static void OnServerStart(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                StartedAt = Now;
                _loading = true;
                Load();
                LoadState();
                _loading = false;
                _timer = new ECSGameTimer(null, Tick, 1000);
            }
            catch (Exception ex)
            {
                log.Error("Dynamic events didn't start", ex);
            }
        }

        [GameServerStoppedEvent]
        public static void OnServerStop(DOLEvent e, object sender, EventArgs args)
        {
            _timer?.Stop();
            foreach (ChainRuntime c in Chains)
                c.Stage?.Finish(false);
            Chains.Clear();
        }

        /// <summary>The built-in zone files, then runtime\server\dynamic-events\*.json (a file there replaces the
        /// built-in one for its zone).</summary>
        public static void Load()
        {
            var byZone = new Dictionary<int, ZoneEventsDef>();
            Assembly asm = typeof(DynamicEventManager).Assembly;
            foreach (string res in asm.GetManifestResourceNames().Where(n => n.StartsWith("DynamicEvents.") && n.EndsWith(".json")))
            {
                using var s = new StreamReader(asm.GetManifestResourceStream(res)!, Encoding.UTF8);
                Add(byZone, s.ReadToEnd(), res);
            }
            string dir = Path.Combine(GameServer.Instance.Configuration.RootDirectory, "dynamic-events");
            if (Directory.Exists(dir))
                foreach (string f in Directory.GetFiles(dir, "*.json").OrderBy(f => f))
                    Add(byZone, File.ReadAllText(f, Encoding.UTF8), f);
            Chains.Clear();
            foreach (ZoneEventsDef z in byZone.Values)
            {
                Region region = WorldMgr.GetRegion(z.Region);
                Zone zone = WorldMgr.GetZone((ushort) z.Zone);
                if (region == null || zone == null)
                {
                    log.Warn($"Dynamic events: zone {z.Zone} (region {z.Region}) isn't loaded - its events are off");
                    continue;
                }
                foreach (ChainDef c in z.Chains)
                {
                    c.ZoneDef = z;
                    if (c.Stages.Count == 0)
                        continue;
                    c.Start ??= c.Stages[0].Id;
                    Chains.Add(new ChainRuntime(c, region, zone, Now));
                }
            }
            log.Info($"Dynamic events: {Chains.Count} chains in {byZone.Count} zones");
        }

        static void Add(Dictionary<int, ZoneEventsDef> byZone, string json, string from)
        {
            try
            {
                var z = JsonConvert.DeserializeObject<ZoneEventsDef>(json);
                if (z != null && z.Zone >= 0 && z.Chains.Count > 0)      // (zone 0 is Camelot Hills)
                    byZone[z.Zone] = z;
            }
            catch (Exception ex)
            {
                log.Error($"Dynamic events: can't read {from}", ex);
            }
        }

        static int Tick(ECSGameTimer timer)
        {
            long now = Now;
            foreach (ChainRuntime c in Chains)
            {
                try
                {
                    c.Tick(now);
                }
                catch (Exception ex)
                {
                    log.Error($"Dynamic event {c.Def.Id} failed - ended", ex);
                    try { c.End("fail", now); } catch { }
                }
            }
            if (++_ticks % 2 == 0)
                Broadcast(now);
            if (_ticks % 5 == 0)
                BotsAtGivers();
            return 1000;
        }

        // ---------------------------------------------------------------- the clients

        static void Broadcast(long now)
        {
            var seen = new HashSet<GamePlayer>();
            foreach (GamePlayer p in ClientService.Instance.GetPlayers())
            {
                if (p?.CurrentZone == null || p.ObjectState != GameObject.eObjectState.Active)
                    continue;
                var list = new List<object>();
                foreach (ChainRuntime c in Chains)
                {
                    if (c.Zone != p.CurrentZone || c.Region != p.CurrentRegion)
                        continue;
                    object d = Describe(c, p, now);
                    if (d != null)
                        list.Add(d);
                }
                if (list.Count == 0 && !_told.Contains(p))
                    continue;
                seen.Add(p);
                if (list.Count > 0)
                    _told.Add(p);
                else
                    _told.Remove(p);
                p.Out.SendMessage(Prefix + JsonConvert.SerializeObject(list), eChatType.CT_System, eChatLoc.CL_SystemWindow);
            }
            _told.RemoveWhere(p => !seen.Contains(p) && p.ObjectState != GameObject.eObjectState.Active);
        }

        /// <summary>One chain for one player's client: running (its stage), resting before the next stage, a disturbance
        /// waiting for someone, a giver who would lead you, or how it ended (a little while). Nothing when quiet.</summary>
        static object Describe(ChainRuntime c, GamePlayer p, long now)
        {
            int zone = c.Zone.ID;
            if (c.Stage != null)
            {
                StageRuntime s = c.Stage;
                double dx = p.X - s.Center.X, dy = p.Y - s.Center.Y;
                bool near = Math.Sqrt(dx * dx + dy * dy) <= s.RadiusUnits + 2400;    // within 60 m of its edge
                return new
                {
                    id = c.Def.Id, title = c.Def.Title, stage = s.Def.Name, kind = s.Def.Type, objective = s.Def.Objective,
                    line = s.ProgressLine, progress = Math.Round(s.Progress, 3), time_left = s.TimeLeft,
                    x = Math.Round(c.ZoneMetresX(s.Center.X), 1), y = Math.Round(c.ZoneMetresY(s.Center.Y), 1),
                    r = s.Def.Radius, zone, levels = c.Def.Levels, near, state = s.Def.Type == "occupy" ? "occupied" : "active"
                };
            }
            if (c.PendingId != null)
            {
                StageDef next = c.Def.Stages.First(st => st.Id == c.PendingId);
                Vector3 at = next.Center != null ? c.ToWorld(next.Center, false)
                    : c.Leader != null ? new Vector3(c.Leader.X, c.Leader.Y, c.Leader.Z) : c.WakePoint;
                double dx = p.X - at.X, dy = p.Y - at.Y;
                return new
                {
                    id = c.Def.Id, title = c.Def.Title, stage = next.Name, objective = next.Objective, line = "Catch your breath",
                    time_left = (int) Math.Max(0, (c.PendingAt - now) / 1000), x = Math.Round(c.ZoneMetresX(at.X), 1),
                    y = Math.Round(c.ZoneMetresY(at.Y), 1), r = next.Radius, zone, levels = c.Def.Levels,
                    near = Math.Sqrt(dx * dx + dy * dy) <= next.Radius * 40 + 4000, state = "next"
                };
            }
            if (c.Dormant)
            {
                Vector3 w = c.WakePoint;
                return new
                {
                    id = c.Def.Id, title = c.Def.Title, hint = c.Def.Hint, x = Math.Round(c.ZoneMetresX(w.X), 1),
                    y = Math.Round(c.ZoneMetresY(w.Y), 1), r = c.WakeUnits / 40, zone, levels = c.Def.Levels, state = "dormant"
                };
            }
            if (c.Def.Giver != null && c.Leader != null && now >= c.GiverReadyAt)
                return new
                {
                    id = c.Def.Id, title = c.Def.Title, giver = c.Giver.Name, hint = $"{c.Giver.Name} is looking for help",
                    x = Math.Round(c.ZoneMetresX(c.Giver.X), 1), y = Math.Round(c.ZoneMetresY(c.Giver.Y), 1), r = 0,
                    zone, levels = c.Def.Levels, state = "giver"
                };
            if (now < c.LastOutcomeUntil)
                return new { id = c.Def.Id, title = c.Def.Title, state = c.LastOutcome, zone };
            return null;
        }

        // ---------------------------------------------------------------- bots

        static readonly Dictionary<ChainRuntime, Dictionary<GameBot, long>> _botsAt = new();
        public const int BotsPerEvent = 6;

        /// <summary>Somewhere an autonomous bot can help (owner 2026-11-02: "bots should seek out events ... and want the
        /// rewards"): a running event, one resting between stages, a disturbance or a giver waiting, within about a zone
        /// (1.6 km) in the bot's region, that the bot is not too low for and that hasn't its fill of bots already. Gives
        /// where to go and what to fight there (its current monsters).</summary>
        public static bool TryBotTarget(GameBot bot, out BotEventTarget target)
        {
            target = null;
            if (bot?.CurrentRegion == null || Chains.Count == 0)
                return false;
            long now = Now;
            ChainRuntime best = null;
            double bestD = double.MaxValue;
            Vector3 bestAt = default;
            foreach (ChainRuntime c in Chains)
            {
                if (c.Region != bot.CurrentRegion || c.Def.Levels == null || bot.Level < c.Def.Levels[0] - 2)
                    continue;
                Vector3 at;
                if (c.Stage != null)
                    at = c.Stage.Center;
                else if (c.PendingId != null || c.Dormant)
                    at = c.Leader != null ? new Vector3(c.Leader.X, c.Leader.Y, c.Leader.Z) : c.WakePoint;
                else if (c.Def.Giver != null && c.Leader != null && now >= c.GiverReadyAt)
                    at = new Vector3(c.Giver.X, c.Giver.Y, c.Giver.Z);
                else
                    continue;
                var mine = _botsAt.TryGetValue(c, out var m) ? m : _botsAt[c] = new Dictionary<GameBot, long>();
                foreach (GameBot old in mine.Where(kv => kv.Value < now || !kv.Key.IsAlive).Select(kv => kv.Key).ToList())
                    mine.Remove(old);
                if (mine.Count >= BotsPerEvent && !mine.ContainsKey(bot))
                    continue;
                double dx = bot.X - at.X, dy = bot.Y - at.Y, d = Math.Sqrt(dx * dx + dy * dy);
                if (d > 65000 || d >= bestD)
                    continue;
                best = c;
                bestD = d;
                bestAt = at;
            }
            if (best == null)
                return false;
            if (!_botsAt[best].ContainsKey(bot))
                Trace($"{bot.Name} (level {bot.Level}) sets out to help with {best.Def.Title}");
            _botsAt[best][bot] = now + 10 * 60_000;
            target = new BotEventTarget(best.Def.Id, best.Def.Title, CurrentMonster(best), best.Zone.Description,
                best.Region.ID, (int) bestAt.X, (int) bestAt.Y, (int) bestAt.Z, best);
            return true;
        }

        /// <summary>Where a bot helping a chain should be now and what it should fight (owner 2026-11-02: a bot "left just
        /// before the last event ... during one of the resting period. They might need a bit more awareness that events
        /// have stages"). False when the chain is over: the bot may go. While it runs - a stage, the rest between
        /// stages, a march - the bot stays with it: the stage's spot (or the giver), the nearest of its monsters.</summary>
        public static bool BotEventFocus(string chainId, GameBot bot, out Vector3 at, out GameNPC foe, out string doing)
        {
            at = default;
            foe = null;
            doing = "";
            ChainRuntime c = Chains.FirstOrDefault(x => x.Def.Id == chainId);
            if (c == null || bot == null || c.Region != bot.CurrentRegion)
                return false;
            long now = Now;
            if (c.Stage != null)
            {
                at = c.Def.Giver != null && c.Leader != null && c.Stage.Def.Type is "escort" or "defend"
                    ? new Vector3(c.Leader.X, c.Leader.Y, c.Leader.Z) : c.Stage.Center;
                foe = c.Stage.Spawned.Where(n => n.IsEnemy && n.IsAlive && n.ObjectState == GameObject.eObjectState.Active &&
                        bot.IsWithinRadius(n, 3000))
                    .OrderBy(n => n.GetDistanceTo(bot)).FirstOrDefault();
                doing = $"{c.Def.Title}: {c.Stage.Def.Objective}";
            }
            else if (c.PendingId != null)
            {
                StageDef next = c.Def.Stages.First(st => st.Id == c.PendingId);
                at = c.Leader != null ? new Vector3(c.Leader.X, c.Leader.Y, c.Leader.Z)
                    : next.Center != null ? c.ToWorld(next.Center, false) : c.WakePoint;
                doing = $"{c.Def.Title}: resting before {next.Name}";
            }
            else if (c.Dormant)
            {
                at = c.WakePoint;
                doing = $"{c.Def.Title}: looking into the disturbance";
            }
            else if (c.Def.Giver != null && c.Leader != null && now >= c.GiverReadyAt)
            {
                at = new Vector3(c.Giver.X, c.Giver.Y, c.Giver.Z);
                doing = $"{c.Def.Title}: going to {c.Giver.Name}";
            }
            else
                return false;
            if (_botsAt.TryGetValue(c, out var mine))
                mine[bot] = now + 10 * 60_000;                  // still with it
            return true;
        }

        /// <summary>A bot sent to a waiting giver that has got there takes them up on it.</summary>
        static void BotsAtGivers()
        {
            foreach (ChainRuntime c in Chains)
            {
                if (c.Def.Giver == null || c.Active || c.Leader == null || !_botsAt.TryGetValue(c, out var mine))
                    continue;
                GameBot here = mine.Keys.FirstOrDefault(b => b.IsAlive && b.CurrentRegion == c.Region && b.IsWithinRadius(c.Giver, 600));
                if (here != null)
                    c.BotAccepts(here);
            }
        }

        /// <summary>What a bot should fight at a chain now: its stage's monsters (the boss, a wave, a cull's first kind),
        /// else its first stage's.</summary>
        static string CurrentMonster(ChainRuntime c)
        {
            StageDef s = c.Stage?.Def ?? c.Def.Stages.FirstOrDefault(st => st.Id == (c.PendingId ?? c.Def.Start));
            if (s == null)
                return "";
            return s.Type switch
            {
                "boss" => s.Boss?.Name ?? "",
                "defend" => s.Waves?.Mobs.FirstOrDefault()?.Name ?? "",
                "escort" => s.Ambushes.SelectMany(a => a.Mobs).FirstOrDefault()?.Name ?? "",
                _ => s.Mobs.FirstOrDefault()?.Name ?? ""
            };
        }
    }

    public sealed record BotEventTarget(string Id, string Title, string MonsterName, string ZoneName, ushort RegionId,
        int X, int Y, int Z, ChainRuntime Chain);

    [CmdAttribute("&events", ePrivLevel.Player,
        "Dynamic events in your zone",
        "/events - the events window: this zone's events, to start, wake or stop (testing)",
        "/events list - what's happening in this zone, in the chat",
        "/events start <id> [stage] - start an event now, at a stage if given (testing)",
        "/events stop <id> - end an event now (testing)",
        "/events wake <id> - make it a disturbance now, waiting for someone to come near (testing)")]
    public class DynamicEventsCommandHandler : Commands.AbstractCommandHandler, Commands.ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client.Player;
            if (p == null)
                return;
            var here = DynamicEventManager.Chains.Where(c => c.Zone == p.CurrentZone).ToList();
            if (args.Length >= 3 && args[1] == "wake")
            {
                ChainRuntime w = DynamicEventManager.Chains.FirstOrDefault(x => x.Def.Id.Equals(args[2], StringComparison.OrdinalIgnoreCase));
                if (w == null || w.Active || w.Def.Giver != null) { DisplayMessage(client, $"Can't wake {args[2]} now."); return; }
                w.Dormant = true;
                DisplayMessage(client, $"{w.Def.Title}: waiting for someone to come near.");
                return;
            }
            if (args.Length >= 3 && (args[1] == "start" || args[1] == "stop"))
            {
                ChainRuntime c = DynamicEventManager.Chains.FirstOrDefault(x => x.Def.Id.Equals(args[2], StringComparison.OrdinalIgnoreCase));
                if (c == null) { DisplayMessage(client, $"No event called {args[2]}."); return; }
                long now = Environment.TickCount64;
                if (args[1] == "start")
                {
                    if (c.Active) { DisplayMessage(client, $"{c.Def.Title} is already running."); return; }
                    // (a stage id after the event's: start there - testing a chain's later stages)
                    string from = args.Length >= 4 && c.Def.Stages.Any(st => st.Id == args[3]) ? args[3] : c.Def.Start;
                    c.Begin(from, now);
                }
                else
                {
                    if (!c.Active && !c.Dormant) { DisplayMessage(client, $"{c.Def.Title} isn't running."); return; }
                    c.End("fail", now);
                }
                DisplayMessage(client, $"{c.Def.Title}: {(args[1] == "start" ? "started" : "stopped")}.");
                return;
            }
            if (args.Length < 2 || args[1] == "window")
            {
                // (owner 2026-11-02: "a window that comes up when I type /events where I can just click on an event and
                // spawn it in the region I'm in") - the new client opens it from this line (game/ui/events_window.gd)
                long t = Environment.TickCount64;
                var rows = here.Select(c => new
                {
                    id = c.Def.Id, title = c.Def.Title, levels = c.Def.Levels, giver = c.Def.Giver?.Name ?? "",
                    stages = c.Def.Stages.Count,
                    state = c.Stage != null ? "running: " + c.Stage.Def.Name
                        : c.PendingId != null ? "resting"
                        : c.Dormant ? "disturbance"
                        : c.Def.Giver != null ? (c.Leader != null && t >= c.GiverReadyAt ? "giver waiting" : "giver resting")
                        : $"quiet ({Math.Max(0, (c.NextStart - t) / 60000)} min)",
                    active = c.Active
                }).ToList();
                p.Out.SendMessage("#EVL|" + JsonConvert.SerializeObject(new { zone = p.CurrentZone?.Description ?? "", events = rows }),
                    eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            if (here.Count == 0) { DisplayMessage(client, "No events in this zone."); return; }
            foreach (ChainRuntime c in here)
            {
                long now = Environment.TickCount64;
                string state = c.Stage != null ? $"{c.Stage.Def.Name} - {c.Stage.Def.Objective} ({c.Stage.ProgressLine}, {c.Stage.TimeLeft} s left)"
                    : c.PendingId != null ? $"resting before the next stage ({Math.Max(0, (c.PendingAt - now) / 1000)} s)"
                    : c.Dormant ? $"a disturbance - waiting for someone to come near"
                    : c.Def.Giver != null ? (c.Leader != null && now >= c.GiverReadyAt ? $"{c.Giver.Name} is looking for help" : "the giver is resting")
                    : $"quiet (next in about {Math.Max(0, (c.NextStart - now) / 60000)} min)";
                DisplayMessage(client, $"{c.Def.Title} [{c.Def.Id}]: {state}");
            }
        }
    }
}
