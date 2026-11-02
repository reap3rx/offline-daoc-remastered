using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
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

        public static void Trace(string line) => log.Info("Dynamic events: " + line);

        [GameServerStartedEvent]
        public static void OnServerStart(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Load();
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
                if (z != null && z.Zone > 0)
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
                    if (c.Stage != null)
                        list.Add(Describe(c, p));
                    else if (now < c.LastOutcomeUntil)
                        list.Add(new { id = c.Def.Id, title = c.Def.Title, state = c.LastOutcome, zone = (int) c.Zone.ID });
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

        static object Describe(ChainRuntime c, GamePlayer p)
        {
            StageRuntime s = c.Stage;
            double dx = p.X - s.Center.X, dy = p.Y - s.Center.Y;
            bool near = Math.Sqrt(dx * dx + dy * dy) <= s.RadiusUnits + 2400;    // within 60 m of its edge
            return new
            {
                id = c.Def.Id,
                title = c.Def.Title,
                stage = s.Def.Name,
                kind = s.Def.Type,
                objective = s.Def.Objective,
                line = s.ProgressLine,
                progress = Math.Round(s.Progress, 3),
                time_left = s.TimeLeft,
                x = Math.Round(c.ZoneMetresX(s.Center.X), 1),
                y = Math.Round(c.ZoneMetresY(s.Center.Y), 1),
                r = s.Def.Radius,
                zone = (int) c.Zone.ID,
                levels = c.Def.Levels,
                near,
                state = "active"
            };
        }
    }

    [CmdAttribute("&events", ePrivLevel.Player,
        "Dynamic events in your zone",
        "/events - what's happening in this zone",
        "/events start <id> - start an event now (testing)",
        "/events stop <id> - end an event now (testing)")]
    public class DynamicEventsCommandHandler : Commands.AbstractCommandHandler, Commands.ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client.Player;
            if (p == null)
                return;
            var here = DynamicEventManager.Chains.Where(c => c.Zone == p.CurrentZone).ToList();
            if (args.Length >= 3 && (args[1] == "start" || args[1] == "stop"))
            {
                ChainRuntime c = DynamicEventManager.Chains.FirstOrDefault(x => x.Def.Id.Equals(args[2], StringComparison.OrdinalIgnoreCase));
                if (c == null) { DisplayMessage(client, $"No event called {args[2]}."); return; }
                long now = Environment.TickCount64;
                if (args[1] == "start")
                {
                    if (c.Active) { DisplayMessage(client, $"{c.Def.Title} is already running."); return; }
                    c.Begin(c.Def.Start, now);
                }
                else
                    c.End("fail", now);
                DisplayMessage(client, $"{c.Def.Title}: {(args[1] == "start" ? "started" : "stopped")}.");
                return;
            }
            if (here.Count == 0) { DisplayMessage(client, "No events in this zone."); return; }
            foreach (ChainRuntime c in here)
            {
                long now = Environment.TickCount64;
                string state = c.Active ? $"{c.Stage.Def.Name} - {c.Stage.Def.Objective} ({c.Stage.ProgressLine}, {c.Stage.TimeLeft} s left)"
                    : $"quiet (next in about {Math.Max(0, (c.NextStart - now) / 60000)} min)";
                DisplayMessage(client, $"{c.Def.Title} [{c.Def.Id}]: {state}");
            }
        }
    }
}
