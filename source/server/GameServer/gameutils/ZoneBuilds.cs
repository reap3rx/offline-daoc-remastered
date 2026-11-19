using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Reflection;
using System.Text.Json;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.DynamicEvents;
using DOL.GS.ServerProperties;
using DOL.GS.Movement;

namespace DOL.GS
{
    /// <summary>
    /// Zone rebuilds (owner 2026-11-19, "Purposeful PvE": "less mobs about ... the mobs placed around to feel like they
    /// should be there"). A zone file (scripts/zonebuilds/*.json, or runtime\server\zone-builds\*.json, which wins) says
    /// who lives in a zone and where; at start-up the zone's ordinary monsters are taken out of the world (the database
    /// is untouched - take the file away and they come back) and the file's are put in their place:
    ///   - members: a kind of monster, copied from an existing one ("from"), with its own name, con tier, faction,
    ///     aggression, roaming and size;
    ///   - sites: a camp (members round a point), wildlife (members spread over an area), a line (a shore: some at each
    ///     point), a patrol (a band walking a route, its leader first).
    /// Factions in the file can be each other's enemies: their monsters fight when they meet (the pests' feud).
    /// Kept: everything named (capitalised), the "keep" list, and anything that isn't an ordinary monster (events,
    /// guards, merchants, bots, scripted monsters).
    /// </summary>
    public static class ZoneBuilds
    {
        public static bool Enabled = true;

        sealed class MemberDef
        {
            public string From, Name, Tier, Faction;
            public int[] Aggro;
            public int? Roam;
            public double Size = 1.0;
        }

        sealed class SiteDef
        {
            public string Id, Kind;
            public int[] At, Area;
            public int R = 500;
            public int? Respawn;
            public List<int[]> Route, Points;
            public Dictionary<string, int> Spawn = new(), Each = new();
        }

        sealed class FactionDef
        {
            public int Id, Aggro = 50;
            public List<string> Enemies = new();
        }

        sealed class ZoneDef
        {
            public int Zone;
            public string Name;
            public HashSet<string> Keep = new(StringComparer.OrdinalIgnoreCase);
            public Dictionary<string, FactionDef> Factions = new();
            public Dictionary<string, string> Tiers = new(StringComparer.OrdinalIgnoreCase);
            public Dictionary<string, MemberDef> Members = new();
            public List<SiteDef> Sites = new();
        }

        public sealed class Report
        {
            public string Zone;
            public int Removed, Spawned, Missing;
            public int ZoneId;
            public HashSet<GameNPC> Placed = new();
            public List<string> Notes = new();
        }

        public static readonly List<Report> Reports = new();

        // ------------------------------------------------------------------ loading

        static List<ZoneDef> Load()
        {
            var defs = new Dictionary<int, ZoneDef>();
            Assembly asm = typeof(ZoneBuilds).Assembly;
            foreach (string res in asm.GetManifestResourceNames().Where(n => n.StartsWith("ZoneBuilds.") && n.EndsWith(".json")))
            {
                using Stream s = asm.GetManifestResourceStream(res);
                using var r = new StreamReader(s);
                if (Parse(r.ReadToEnd(), res) is ZoneDef d)
                    defs[d.Zone] = d;
            }
            string dir = Path.Combine(GameServer.Instance.Configuration.RootDirectory, "zone-builds");
            if (Directory.Exists(dir))
                foreach (string f in Directory.GetFiles(dir, "*.json").OrderBy(f => f))
                    if (Parse(File.ReadAllText(f), f) is ZoneDef d)
                        defs[d.Zone] = d;                   // a file there replaces the built-in one
            return defs.Values.ToList();
        }

        static ZoneDef Parse(string json, string from)
        {
            try
            {
                using JsonDocument doc = JsonDocument.Parse(json, new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true });
                JsonElement root = doc.RootElement;
                if (root.TryGetProperty("enabled", out JsonElement en) && en.ValueKind == JsonValueKind.False)
                    return null;
                var d = new ZoneDef { Zone = root.GetProperty("zone").GetInt32(), Name = Str(root, "name") };
                if (root.TryGetProperty("keep", out JsonElement keep))
                    foreach (JsonElement k in keep.EnumerateArray())
                        d.Keep.Add(k.GetString());
                if (root.TryGetProperty("tiers", out JsonElement tiers))
                    foreach (JsonProperty t in tiers.EnumerateObject())
                        d.Tiers[t.Name] = t.Value.GetString();
                if (root.TryGetProperty("factions", out JsonElement fs))
                    foreach (JsonProperty f in fs.EnumerateObject())
                    {
                        var fd = new FactionDef { Id = f.Value.GetProperty("id").GetInt32() };
                        if (f.Value.TryGetProperty("aggro", out JsonElement a)) fd.Aggro = a.GetInt32();
                        if (f.Value.TryGetProperty("enemies", out JsonElement e))
                            foreach (JsonElement x in e.EnumerateArray())
                                fd.Enemies.Add(x.GetString());
                        d.Factions[f.Name] = fd;
                    }
                foreach (JsonProperty m in root.GetProperty("members").EnumerateObject())
                {
                    JsonElement v = m.Value;
                    var md = new MemberDef { From = Str(v, "from") ?? m.Name, Name = Str(v, "name"), Tier = Str(v, "tier"), Faction = Str(v, "faction") };
                    if (v.TryGetProperty("aggro", out JsonElement ag)) md.Aggro = ag.EnumerateArray().Select(x => x.GetInt32()).ToArray();
                    if (v.TryGetProperty("roam", out JsonElement ro)) md.Roam = ro.GetInt32();
                    if (v.TryGetProperty("size", out JsonElement sz)) md.Size = sz.GetDouble();
                    d.Members[m.Name] = md;
                }
                foreach (JsonElement s in root.GetProperty("sites").EnumerateArray())
                {
                    var sd = new SiteDef { Id = Str(s, "id"), Kind = Str(s, "kind") ?? "camp" };
                    if (s.TryGetProperty("at", out JsonElement at)) sd.At = Ints(at);
                    if (s.TryGetProperty("area", out JsonElement ar)) sd.Area = Ints(ar);
                    if (s.TryGetProperty("r", out JsonElement rr)) sd.R = rr.GetInt32();
                    if (s.TryGetProperty("respawn", out JsonElement rs)) sd.Respawn = rs.GetInt32();
                    if (s.TryGetProperty("route", out JsonElement rt)) sd.Route = rt.EnumerateArray().Select(Ints).ToList();
                    if (s.TryGetProperty("points", out JsonElement pt)) sd.Points = pt.EnumerateArray().Select(Ints).ToList();
                    if (s.TryGetProperty("spawn", out JsonElement sp))
                        foreach (JsonProperty p in sp.EnumerateObject()) sd.Spawn[p.Name] = p.Value.GetInt32();
                    if (s.TryGetProperty("each", out JsonElement ea))
                        foreach (JsonProperty p in ea.EnumerateObject()) sd.Each[p.Name] = p.Value.GetInt32();
                    d.Sites.Add(sd);
                }
                return d;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZoneBuilds] {from}: {ex.Message}");
                return null;
            }
        }

        static string Str(JsonElement e, string key) => e.TryGetProperty(key, out JsonElement v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
        static int[] Ints(JsonElement e) => e.EnumerateArray().Select(x => x.GetInt32()).ToArray();

        // ------------------------------------------------------------------ building

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            if (!Enabled)
                return;
            List<ZoneDef> defs = Load();
            foreach (ZoneDef d in defs)
            {
                try
                {
                    Report r = Build(d);
                    Reports.Add(r);
                    Console.WriteLine($"[ZoneBuilds] {r.Zone}: {r.Removed} monsters taken out, {r.Spawned} placed" +
                        (r.Missing > 0 ? $", {r.Missing} not placed" : "") + (r.Notes.Count > 0 ? " - " + string.Join("; ", r.Notes.Take(8)) : ""));
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[ZoneBuilds] zone {d.Zone}: {ex}");
                }
            }
        }

        /// <summary>Whether an NPC is one of the zone's ordinary monsters, for the rebuild to take out.</summary>
        static bool Ordinary(GameNPC n, ZoneDef d)
        {
            if (n is GameBot || n is EventNpc || n is GameGuard || n is GameMerchant || n is GameTrainingDummy)
                return false;
            if (n.Realm != eRealm.None || n.Brain is IControlledBrain)
                return false;
            if ((n.Flags & (GameNPC.eFlags.PEACE | GameNPC.eFlags.CANTTARGET)) != 0)
                return false;
            if (string.IsNullOrEmpty(n.Name) || char.IsUpper(n.Name[0]) || d.Keep.Contains(n.Name))
                return false;
            return true;
        }

        static Report Build(ZoneDef d)
        {
            var rep = new Report { Zone = d.Name ?? d.Zone.ToString(), ZoneId = d.Zone };
            Zone zone = WorldMgr.GetZone((ushort) d.Zone);
            Region region = zone?.ZoneRegion;
            if (zone == null || region == null)
            {
                rep.Notes.Add("no such zone");
                return rep;
            }

            // what lives there now: the ground they stand on is where the new ones may stand
            var pool = new List<Vector3>();
            var originals = new List<GameNPC>();
            var templates = new Dictionary<string, DbMob>(StringComparer.OrdinalIgnoreCase);
            foreach (GameObject o in region.Objects ?? Array.Empty<GameObject>())
            {
                if (o is not GameNPC n || n.CurrentZone != zone)
                    continue;
                if (n.Realm == eRealm.None && n is not GameBot)
                    pool.Add(new Vector3(n.X, n.Y, n.Z));
                if (Ordinary(n, d))
                    originals.Add(n);
            }

            // the members' patterns: each "from" an existing monster's row
            foreach (MemberDef m in d.Members.Values)
            {
                if (templates.ContainsKey(m.From))
                    continue;
                GameNPC like = originals.FirstOrDefault(n => string.Equals(n.Name, m.From, StringComparison.OrdinalIgnoreCase));
                DbMob row = like?.InternalID != null ? GameServer.Database.FindObjectByKey<DbMob>(like.InternalID) : null;
                row ??= DOLDB<DbMob>.SelectObject(DB.Column("Name").IsEqualTo(m.From).And(DB.Column("Region").IsEqualTo(region.ID)));
                row ??= DOLDB<DbMob>.SelectObject(DB.Column("Name").IsEqualTo(m.From));
                if (row != null)
                    templates[m.From] = row;
                else
                    rep.Notes.Add($"no monster called '{m.From}'");
            }

            // out: plain monsters, and scripted ones only of a kind the file puts back (its members' patterns' scripts:
            // the blackthorns, changelings, night spawns) - other scripts (a named boss, the farm) stay
            var replacedTypes = new HashSet<string>(templates.Values.Select(t => t.ClassType ?? "").Where(t => t != ""));
            foreach (GameNPC n in originals)
            {
                if (n.GetType() != typeof(GameNPC) && !replacedTypes.Contains(n.GetType().FullName))
                    continue;
                n.Delete();
                rep.Removed++;
            }
            // ... and any that turn up later (night spawns, one dead at start-up coming back): swept every half minute -
            // only kinds the zone had or the file uses (never a quest's or a script's own spawn of another name)
            var sweepNames = new HashSet<string>(originals.Select(n => n.Name), StringComparer.OrdinalIgnoreCase);
            foreach (MemberDef m in d.Members.Values)
                sweepNames.Add(m.From);
            new ECSGameTimer(null, _ =>
            {
                foreach (GameObject o in region.Objects ?? Array.Empty<GameObject>())
                    if (o is GameNPC n && n.CurrentZone == zone && !rep.Placed.Contains(n) && !Exempt.TryGetValue(n, out object _) && sweepNames.Contains(n.Name) && Ordinary(n, d) &&
                        (n.GetType() == typeof(GameNPC) || replacedTypes.Contains(n.GetType().FullName)))
                    {
                        n.Delete();
                        rep.Removed++;
                    }
                return 30000;
            }, 30000);

            // kept monsters given a tier by hand
            if (d.Tiers.Count > 0)
                foreach (GameObject o in region.Objects ?? Array.Empty<GameObject>())
                    if (o is GameNPC n && n.CurrentZone == zone && n.Realm == eRealm.None && d.Tiers.TryGetValue(n.Name, out string tn))
                    {
                        int ti = Array.IndexOf(TierNames, tn.ToLowerInvariant());
                        if (ti >= 0)
                            MonsterTiers.SetTier(n, (sbyte) (ti - 3));
                    }

            // factions, and their feuds
            var factions = new Dictionary<string, Faction>();
            foreach (var kv in d.Factions)
            {
                var f = new Faction();
                f.LoadFromDatabase(new DbFaction { ID = kv.Value.Id, Name = kv.Key, BaseAggroLevel = kv.Value.Aggro });
                factions[kv.Key] = f;
            }
            foreach (var kv in d.Factions)
                foreach (string enemy in kv.Value.Enemies)
                    if (factions.TryGetValue(enemy, out Faction ef))
                    {
                        factions[kv.Key].EnemyFactions.Add(ef);
                        ef.EnemyFactions.Add(factions[kv.Key]);
                    }

            var rng = new Random(d.Zone * 7919);
            foreach (SiteDef s in d.Sites)
            {
                try
                {
                    BuildSite(d, s, zone, region, pool, templates, factions, rng, rep);
                }
                catch (Exception ex)
                {
                    rep.Notes.Add($"{s.Id}: {ex.Message}");
                }
            }
            return rep;
        }

        static void BuildSite(ZoneDef d, SiteDef s, Zone zone, Region region, List<Vector3> pool,
            Dictionary<string, DbMob> templates, Dictionary<string, Faction> factions, Random rng, Report rep)
        {
            Vector3 W(int lx, int ly) => Ground(zone, pool, zone.XOffset + lx, zone.YOffset + ly);
            // a spot is good where monsters have stood before (not out in a lake): a few tries, then the last one
            Vector3 Good(Func<Vector3> pick)
            {
                Vector3 v = pick();
                for (int i = 0; i < 8 && Far(pool, v); i++)
                    v = pick();
                return v;
            }

            switch (s.Kind)
            {
                case "wildlife":
                    foreach (var kv in s.Spawn)
                        for (int i = 0; i < kv.Value; i++)
                        {
                            Vector3 at = Good(() => W(rng.Next(s.Area[0], s.Area[2]), rng.Next(s.Area[1], s.Area[3])));
                            Place(d, kv.Key, at, s, region, templates, factions, rng, rep);
                        }
                    break;

                case "line":
                    foreach (int[] p in s.Points)
                        foreach (var kv in s.Each)
                            for (int i = 0; i < kv.Value; i++)
                                Place(d, kv.Key, Near(zone, W(p[0], p[1]), 350, rng), s, region, templates, factions, rng, rep);
                    foreach (var kv in s.Spawn)
                        for (int i = 0; i < kv.Value; i++)
                        {
                            int[] p = s.Points[rng.Next(s.Points.Count)];
                            Place(d, kv.Key, Near(zone, W(p[0], p[1]), 400, rng), s, region, templates, factions, rng, rep);
                        }
                    break;

                case "patrol":
                {
                    // a band on a loop: each its own copy of the route, a little to one side, so they walk as a column
                    // and the brain's own patrolling (which keeps looking for a fight) moves them
                    Vector3 start = W(s.Route[0][0], s.Route[0][1]);
                    var route = s.Route.Select(p => W(p[0], p[1])).ToList();
                    int k = 0;
                    foreach (var kv in s.Spawn)
                        for (int i = 0; i < kv.Value; i++, k++)
                            if (Place(d, kv.Key, Near(zone, start, 120, rng), s, region, templates, factions, rng, rep, roam: 0) is GameNPC n)
                            {
                                int off = (k % 2 == 0 ? 1 : -1) * ((k + 1) / 2) * 70;
                                string id = $"zb:{d.Zone}:{s.Id}:{k}";
                                MovementMgr.RegisterPath(id, EPathType.Loop,
                                    route.Select(p => ((int) p.X + off, (int) p.Y + off, (int) p.Z, 170)).ToList());
                                n.PathID = id;
                            }
                    break;
                }

                default:                                         // a camp
                {
                    Vector3 c = W(s.At[0], s.At[1]);
                    foreach (var kv in s.Spawn)
                        for (int i = 0; i < kv.Value; i++)
                            Place(d, kv.Key, Good(() => Near(zone, c, s.R, rng)), s, region, templates, factions, rng, rep);
                    break;
                }
            }
        }

        /// <summary>The ground near a spot: the height of the nearest monster that stood near it, then the navmesh.</summary>
        static Vector3 Ground(Zone zone, List<Vector3> pool, int x, int y)
        {
            float z = 0, best = float.MaxValue;
            foreach (Vector3 p in pool)
            {
                float dd = (p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y);
                if (dd < best)
                {
                    best = dd;
                    z = p.Z;
                }
            }
            var v = new Vector3(x, y, z);
            if (PathfindingProvider.Instance.IsAvailable && PathfindingProvider.Instance.HasNavmesh(zone))
            {
                Vector3? g = PathfindingProvider.Instance.GetClosestPoint(zone, v, 250, 250, 1500, PathfindingProvider.Instance.DefaultFilters);
                if (g.HasValue)
                    return g.Value;
            }
            return v;
        }

        static bool Far(List<Vector3> pool, Vector3 v)
        {
            foreach (Vector3 p in pool)
                if ((p.X - v.X) * (p.X - v.X) + (p.Y - v.Y) * (p.Y - v.Y) < 1100f * 1100f)
                    return false;
            return true;
        }

        static Vector3 Near(Zone zone, Vector3 c, int r, Random rng)
        {
            if (PathfindingProvider.Instance.IsAvailable && PathfindingProvider.Instance.HasNavmesh(zone))
            {
                Vector3? p = PathfindingProvider.Instance.GetRandomPoint(zone, c, r, PathfindingProvider.Instance.DefaultFilters);
                if (p.HasValue && Math.Abs(p.Value.Z - c.Z) < 600)
                    return p.Value;
            }
            double a = rng.NextDouble() * Math.PI * 2, dist = Math.Sqrt(rng.NextDouble()) * r;
            return new Vector3((float) (c.X + Math.Cos(a) * dist), (float) (c.Y + Math.Sin(a) * dist), c.Z);
        }

        static readonly string[] TierNames = { "grey", "green", "blue", "yellow", "orange", "red", "purple" };

        static GameNPC Place(ZoneDef d, string memberKey, Vector3 at, SiteDef s, Region region, Dictionary<string, DbMob> templates,
            Dictionary<string, Faction> factions, Random rng, Report rep, int? roam = null)
        {
            if (!d.Members.TryGetValue(memberKey, out MemberDef m) || !templates.TryGetValue(m.From, out DbMob tpl))
            {
                rep.Missing++;
                return null;
            }
            DbMob row = Copy(tpl);
            row.X = (int) at.X;
            row.Y = (int) at.Y;
            row.Z = (int) at.Z;
            row.Region = region.ID;
            row.Heading = (ushort) rng.Next(4096);
            row.PathID = null;
            if (m.Name != null)
                row.Name = m.Name;
            if (m.Aggro is { Length: 2 })
            {
                row.AggroLevel = m.Aggro[0];
                row.AggroRange = m.Aggro[1];
            }
            row.RoamingRange = roam ?? m.Roam ?? (s.Kind == "camp" ? 0 : tpl.RoamingRange);
            if (s.Respawn.HasValue)
                row.RespawnInterval = s.Respawn.Value;

            GameNPC npc = Create(row.ClassType) ?? new GameNPC();
            npc.LoadFromDatabase(row);
            npc.LoadedFromScript = true;                         // never saved: the database keeps the zone as it was
            if (m.Name != null)
                npc.Name = m.Name;
            if (Math.Abs(m.Size - 1.0) > 0.01)
                npc.Size = (byte) Math.Clamp(npc.Size * m.Size, 1, 255);
            if (m.Faction != null && factions.TryGetValue(m.Faction, out Faction f))
                npc.Faction = f;
            npc.CurrentRegion = region;
            if (!npc.AddToWorld())
            {
                rep.Missing++;
                return null;
            }
            int t = m.Tier != null ? Array.IndexOf(TierNames, m.Tier.ToLowerInvariant()) : -1;
            if (t >= 0)
                MonsterTiers.SetTier(npc, (sbyte) (t - 3));
            rep.Spawned++;
            rep.Placed.Add(npc);
            return npc;
        }

        /// <summary>Monsters the sweeper leaves alone (TierCalibration's own).</summary>
        public static readonly System.Runtime.CompilerServices.ConditionalWeakTable<GameNPC, object> Exempt = new();

        /// <summary>A copy of a monster's record to spawn from (never saved).</summary>
        public static DbMob CopyMob(DbMob tpl) => Copy(tpl);

        static DbMob Copy(DbMob tpl)
        {
            var row = new DbMob();
            foreach (PropertyInfo p in typeof(DbMob).GetProperties(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly))
                if (p.CanRead && p.CanWrite && p.GetIndexParameters().Length == 0)
                    p.SetValue(row, p.GetValue(tpl));
            return row;
        }

        static GameNPC Create(string classType)
        {
            if (string.IsNullOrEmpty(classType) || classType == "DOL.GS.GameNPC")
                return null;
            foreach (Assembly script in ScriptMgr.GameServerScripts)
                try
                {
                    if (script.CreateInstance(classType, false) is GameNPC n)
                        return n;
                }
                catch (Exception)
                {
                }
            return null;
        }

    }
}

namespace DOL.GS.Commands
{
    using System;
    using System.Collections.Generic;
    using System.Linq;
    using DOL.AI.Brain;
    [CmdAttribute("&zonebuild", ePrivLevel.GM, "What the zone rebuilds did at start-up (ZoneBuilds)", "/zonebuild")]
    public class ZoneBuildCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            if (ZoneBuilds.Reports.Count == 0)
            {
                DisplayMessage(client, "No zone rebuilds ran.");
                return;
            }
            if (args.Length > 2 && args[1].ToLowerInvariant() == "find")
            {
                string name = string.Join(" ", args.Skip(2));
                foreach (ZoneBuilds.Report r in ZoneBuilds.Reports)
                {
                    Zone z = WorldMgr.GetZone((ushort) r.ZoneId);
                    foreach (GameNPC n in r.Placed.Where(n => string.Equals(n.Name, name, StringComparison.OrdinalIgnoreCase)).Take(12))
                        DisplayMessage(client, $"{n.Name} at {n.X - z.XOffset},{n.Y - z.YOffset} {(n.IsAlive ? "alive" : "dead")} " +
                            $"state {(n.Brain as StandardMobBrain)?.FSM?.GetCurrentState()?.StateType} path {n.PathID ?? "-"} " +
                            $"combat {n.InCombat} target {(n.TargetObject as GameLiving)?.Name ?? "-"} moving {n.IsMoving}");
                }
                return;
            }
            if (args.Length > 1 && args[1].ToLowerInvariant() == "left")
            {
                foreach (ZoneBuilds.Report r in ZoneBuilds.Reports)
                {
                    Zone z = WorldMgr.GetZone((ushort) r.ZoneId);
                    var left = new Dictionary<string, int>();
                    foreach (GameObject o in z?.ZoneRegion?.Objects ?? Array.Empty<GameObject>())
                        if (o is GameNPC n && n.CurrentZone == z && n.Realm == eRealm.None && n is not GameBot && !r.Placed.Contains(n))
                            left[n.Name] = left.GetValueOrDefault(n.Name) + 1;
                    DisplayMessage(client, $"{r.Zone} kept: " + string.Join(", ", left.OrderByDescending(k => k.Value).Select(k => $"{k.Key} {k.Value}")));
                }
                return;
            }
            foreach (ZoneBuilds.Report r in ZoneBuilds.Reports)
                DisplayMessage(client, $"{r.Zone}: {r.Removed} taken out, {r.Spawned} placed, {r.Missing} not placed" +
                    (r.Notes.Count > 0 ? " - " + string.Join("; ", r.Notes) : ""));
        }
    }
}
