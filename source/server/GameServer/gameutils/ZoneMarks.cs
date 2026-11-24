using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using DOL.Events;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// Zone design marks (owner 2026-11-21: "instead of me describing individual spots, we could build a tool that lets
    /// me mark things in game for you to read? Like a window that lets me choose from mob types and difficulty from some
    /// presets based on the zone design, and then a window to jot some notes down for that spawn, then putting a marker
    /// down in game"). /zmark opens the window; a mark is saved where you stand, with what you picked and your notes, to
    /// runtime\server\zone-marks\zoneNNN.json, and a glowing orb named for it stands there (only for you to see what you
    /// marked - it does nothing). The zone builder reads the files to turn them into spawns.
    /// </summary>
    public static class ZoneMarks
    {
        public sealed class Mark
        {
            public int Id { get; set; }
            public int Zone { get; set; }
            public string ZoneName { get; set; }
            public int X { get; set; }
            public int Y { get; set; }
            public int Z { get; set; }
            public int Heading { get; set; }
            public string Kind { get; set; }
            public string Theme { get; set; }
            public string Difficulty { get; set; }
            public string Size { get; set; }
            public string Time { get; set; }
            public string Route { get; set; }
            public string Note { get; set; }
            public string By { get; set; }
            public string Made { get; set; }
            public string GameTime { get; set; }
        }

        public static readonly string[] Kinds =
        {
            "Camp", "Small group", "Scatter (wildlife)", "Patrol point", "Single (named or boss)", "Thin out here", "Note only"
        };

        public static readonly string[] Difficulties =
        {
            "Grey critters", "Mostly green", "Green and blue", "Blues, yellow leader", "Yellows, orange leader",
            "Oranges and reds", "Red boss with guards", "Purple (raid)"
        };

        public static readonly string[] Sizes = { "1", "2-3", "4-6", "7-10", "11-15", "16+" };
        public static readonly string[] Times = { "Always", "Night only", "Day only" };

        static readonly string[] DefaultThemes =
        {
            "Wildlife", "Bandits", "Undead", "Fae", "Elementals", "Giants", "Other (see notes)"
        };

        static readonly object Lock = new();
        static readonly Dictionary<int, List<Mark>> ByZone = new();
        static readonly Dictionary<int, GameNPC> Orbs = new();
        static readonly Dictionary<GamePlayer, StringBuilder> Notes = new();

        static string Dir => Path.Combine(GameServer.Instance.Configuration.RootDirectory, "zone-marks");
        static string FileFor(int zone) => Path.Combine(Dir, $"zone{zone:000}.json");

        static readonly JsonSerializerOptions Json = new() { WriteIndented = true };

        public static IReadOnlyList<string> ThemesFor(int zone)
        {
            var t = ZoneBuilds.Themes(zone);
            return t is { Count: > 0 } ? t.Concat(new[] { "Other (see notes)" }).Distinct().ToArray() : DefaultThemes;
        }

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                if (!Directory.Exists(Dir))
                    return;
                foreach (string f in Directory.GetFiles(Dir, "zone*.json"))
                {
                    var marks = JsonSerializer.Deserialize<List<Mark>>(File.ReadAllText(f)) ?? new List<Mark>();
                    if (marks.Count == 0)
                        continue;
                    lock (Lock)
                        ByZone[marks[0].Zone] = marks;
                    foreach (Mark m in marks)
                        ShowOrb(m);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZoneMarks] {ex.Message}");
            }
        }

        static void Save(int zone)
        {
            List<Mark> marks;
            lock (Lock)
                marks = ByZone.TryGetValue(zone, out var l) ? l.ToList() : new List<Mark>();
            Directory.CreateDirectory(Dir);
            File.WriteAllText(FileFor(zone), JsonSerializer.Serialize(marks, Json));
        }

        public static void AddNote(GamePlayer p, string text)
        {
            lock (Lock)
            {
                if (!Notes.TryGetValue(p, out var sb))
                    Notes[p] = sb = new StringBuilder();
                if (sb.Length < 4000)
                    sb.Append(text);
            }
        }

        static string TakeNote(GamePlayer p)
        {
            lock (Lock)
            {
                if (!Notes.Remove(p, out var sb))
                    return "";
                return sb.ToString().Trim();
            }
        }

        static string Pick(IReadOnlyList<string> list, string index) =>
            int.TryParse(index, out int i) && i >= 0 && i < list.Count ? list[i] : list[0];

        public static Mark Add(GamePlayer p, string kind, string theme, string difficulty, string size, string time, string route)
        {
            Zone z = p.CurrentZone;
            if (z == null)
                return null;
            var m = new Mark
            {
                Zone = z.ID,
                ZoneName = z.Description,
                X = p.X - z.XOffset,
                Y = p.Y - z.YOffset,
                Z = p.Z,
                Heading = p.Heading,
                Kind = Pick(Kinds, kind),
                Theme = Pick(ThemesFor(z.ID), theme),
                Difficulty = Pick(Difficulties, difficulty),
                Size = Pick(Sizes, size),
                Time = Pick(Times, time),
                Route = string.IsNullOrWhiteSpace(route) || route == "-" ? null : route.Replace('_', ' '),
                Note = TakeNote(p),
                By = p.Name,
                Made = DateTime.Now.ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture),
                GameTime = p.CurrentRegion?.IsNightTime == true ? "night" : "day"
            };
            lock (Lock)
            {
                if (!ByZone.TryGetValue(z.ID, out var list))
                    ByZone[z.ID] = list = new List<Mark>();
                m.Id = ByZone.Values.SelectMany(l => l).Select(x => x.Id).DefaultIfEmpty(0).Max() + 1;
                list.Add(m);
            }
            Save(z.ID);
            ShowOrb(m);
            return m;
        }

        public static Mark Remove(GamePlayer p, int id)
        {
            Mark gone = null;
            lock (Lock)
            {
                foreach (var list in ByZone.Values)
                {
                    gone = id > 0 ? list.FirstOrDefault(m => m.Id == id) : null;
                    if (gone == null && id <= 0 && p.CurrentZone != null && list.Count > 0 && list[0].Zone == p.CurrentZone.ID)
                        gone = list.OrderBy(m => Dist(p, m)).FirstOrDefault(m => Dist(p, m) < 2000);
                    if (gone != null)
                    {
                        list.Remove(gone);
                        break;
                    }
                }
            }
            if (gone == null)
                return null;
            Save(gone.Zone);
            if (Orbs.Remove(gone.Id, out GameNPC orb))
                orb.Delete();
            return gone;
        }

        static double Dist(GamePlayer p, Mark m)
        {
            Zone z = p.CurrentZone;
            if (z == null || z.ID != m.Zone)
                return double.MaxValue;
            double dx = p.X - z.XOffset - m.X, dy = p.Y - z.YOffset - m.Y;
            return Math.Sqrt(dx * dx + dy * dy);
        }

        public static IReadOnlyList<Mark> Near(GamePlayer p, int max = 8)
        {
            lock (Lock)
                return ByZone.Values.SelectMany(l => l).Where(m => p.CurrentZone != null && m.Zone == p.CurrentZone.ID)
                    .OrderBy(m => Dist(p, m)).Take(max).ToArray();
        }

        public static int Count(int zone)
        {
            lock (Lock)
                return ByZone.TryGetValue(zone, out var l) ? l.Count : 0;
        }

        /// <summary>A glowing orb where the mark is, named for it: it can't be fought and does nothing.</summary>
        static void ShowOrb(Mark m)
        {
            try
            {
                Zone z = WorldMgr.GetZone((ushort) m.Zone);
                if (z?.ZoneRegion == null)
                    return;
                var orb = new GameNPC
                {
                    Name = $"mark {m.Id}: {m.Kind.ToLowerInvariant()}",
                    GuildName = Short($"{m.Theme} - {m.Difficulty}", 40),
                    Model = 1391,                       // the empyrean orb
                    Size = 35,
                    Level = 1,
                    Realm = eRealm.None,
                    CurrentRegion = z.ZoneRegion,
                    X = m.X + z.XOffset,
                    Y = m.Y + z.YOffset,
                    Z = m.Z + 60,
                    Heading = (ushort) m.Heading,
                    LoadedFromScript = true,
                    MaxSpeedBase = 0,
                    Flags = GameNPC.eFlags.PEACE | GameNPC.eFlags.FLYING
                };
                if (orb.AddToWorld())
                {
                    if (Orbs.Remove(m.Id, out GameNPC old))
                        old.Delete();
                    Orbs[m.Id] = orb;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZoneMarks] orb {m.Id}: {ex.Message}");
            }
        }

        static string Short(string s, int n) => s.Length <= n ? s : s[..(n - 1)] + ".";

        /// <summary>The window's lists and the marks nearby: "#ZMARK|{json}".</summary>
        public static string WindowJson(GamePlayer p)
        {
            Zone z = p.CurrentZone;
            var near = Near(p).Select(m => new
            {
                id = m.Id, kind = m.Kind, theme = m.Theme, difficulty = m.Difficulty, size = m.Size, time = m.Time,
                route = m.Route, note = m.Note, dist = (int) Dist(p, m)
            });
            return JsonSerializer.Serialize(new
            {
                zone = z?.ID ?? 0,
                zoneName = z?.Description ?? "",
                count = z == null ? 0 : Count(z.ID),
                kinds = Kinds,
                themes = z == null ? DefaultThemes : ThemesFor(z.ID),
                difficulties = Difficulties,
                sizes = Sizes,
                times = Times,
                near
            });
        }
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&zmark", ePrivLevel.Player, "Mark a spot for the zone's design (opens the window)",
        "/zmark - the window", "/zmark del [id] - remove a mark (the nearest without an id)", "/zmark list")]
    public class ZoneMarkCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client.Player;
            if (p == null)
                return;
            string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            switch (sub)
            {
                case "note":                                   // the notes arrive first, a piece at a time
                    ZoneMarks.AddNote(p, string.Join(" ", args.Skip(2)) + " ");
                    return;
                case "add":                                    // add <kind> <theme> <difficulty> <size> <time> [route]
                {
                    if (args.Length < 7)
                        return;
                    ZoneMarks.Mark m = ZoneMarks.Add(p, args[2], args[3], args[4], args[5], args[6], args.Length > 7 ? args[7] : null);
                    if (m != null)
                        DisplayMessage(client, $"Mark {m.Id} saved: {m.Kind}, {m.Theme}, {m.Difficulty}, {m.Size}, {m.Time}" +
                            (m.Route != null ? $", route {m.Route}" : "") + ".");
                    break;
                }
                case "del":
                {
                    int id = args.Length > 2 && int.TryParse(args[2], out int n) ? n : 0;
                    ZoneMarks.Mark m = ZoneMarks.Remove(p, id);
                    DisplayMessage(client, m != null ? $"Mark {m.Id} removed." : "No mark to remove (none within 2000 units).");
                    break;
                }
                case "list":
                    foreach (ZoneMarks.Mark m in ZoneMarks.Near(p, 20))
                        DisplayMessage(client, $"{m.Id}: {m.Kind}, {m.Theme}, {m.Difficulty}, {m.Size}, {m.Time} at {m.X},{m.Y}" +
                            (string.IsNullOrEmpty(m.Note) ? "" : $" - {m.Note}"));
                    return;
            }
            if (NewClient.Is(p))
                NewClient.Send(p, "#ZMARK|" + ZoneMarks.WindowJson(p));
            else if (sub == "")
                DisplayMessage(client, "The zone mark window needs the new client. /zmark list shows the marks here.");
        }
    }
}
