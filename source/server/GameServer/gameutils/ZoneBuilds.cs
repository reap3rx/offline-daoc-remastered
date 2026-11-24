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
            public Dictionary<string, int> Guards = new();    // lower-cons kept close (owner's playtest: "bodyguards")
            public string DropName, DropSlot;                 // a named monster's own drop (owner's /zmark 12: "a unique drop")
            public bool Plain;                                // spawn as a plain monster, not its pattern's script (a NightSpawn)
            public int[] Spells;                              // spells it casts (spell ids): a caster boss's kit
            public bool CcImmune;
            public int GuardR = 260;                          // how far its guards stand
            public bool GuardsFollow;                         // its guards walk with it (a roaming caster and its pet)
            public int? Realm;                                // another realm's soldier fighting as a monster (0: a monster)
            public string Guild;                              // the line under the name (the Norse: "the Saltwolves")
            public int? Model;
        }

        sealed class SiteDef
        {
            public string Id, Kind;
            public int[] At, Area;
            public int R = 500;
            public int Spacing = 300;                          // a camp's members at least this far apart
            public bool SpacingSet;
            public string Time;                                // "night" or "day": only out then
            public int[] Ring;                                 // a camp's members between these two distances from its centre
            public List<int[]> Polygon;                        // wildlife only inside this outline
            public bool NoClear;                               // "clear" sites don't keep this one's monsters out
            public bool Even;                                  // a camp spread evenly over its whole circle, whatever the cons
            public HashSet<string> Names = new(StringComparer.OrdinalIgnoreCase);   // a "clear" site: these go
            public string Block;                               // ... and nothing of them (or "night": no night site's) is placed inside
            public int? Respawn;
            public List<int[]> Route, Points;
            public Dictionary<string, int> Spawn = new(), Each = new();
        }

        sealed class FactionDef
        {
            public int Id, Aggro = 50;
            public List<string> Enemies = new();
            /// <summary>A faction whose standing is each player's own and kept (the Azure in Lough Gur and on: neutral until a
            /// player's Azure Burning, AzureStanding.cs): registered with FactionMgr, so its aggro levels load and save, and
            /// shared by every zone file that names its id.</summary>
            public bool Shared;
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
            public List<string> Themes = new();
        }

        static readonly ConcurrentDictionary<int, List<string>> _themes = new();

        /// <summary>A zone file's themes (its "themes" list): the zone mark window's choices (ZoneMarks).</summary>
        public static IReadOnlyList<string> Themes(int zone) => _themes.TryGetValue(zone, out var t) ? t : null;

        public sealed class Report
        {
            public string Zone;
            public int Removed, Spawned, Missing, Blocked;
            public int ZoneId;
            public HashSet<GameNPC> Placed = new();
            public List<(GameNPC Npc, bool AtNight)> Timed = new();
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
                if (root.TryGetProperty("themes", out JsonElement th))
                    foreach (JsonElement x in th.EnumerateArray())
                        d.Themes.Add(x.GetString());
                if (root.TryGetProperty("tiers", out JsonElement tiers))
                    foreach (JsonProperty t in tiers.EnumerateObject())
                        d.Tiers[t.Name] = t.Value.GetString();
                if (root.TryGetProperty("factions", out JsonElement fs))
                    foreach (JsonProperty f in fs.EnumerateObject())
                    {
                        var fd = new FactionDef { Id = f.Value.GetProperty("id").GetInt32() };
                        if (f.Value.TryGetProperty("aggro", out JsonElement a)) fd.Aggro = a.GetInt32();
                        if (f.Value.TryGetProperty("shared", out JsonElement sh)) fd.Shared = sh.GetBoolean();
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
                    if (v.TryGetProperty("plain", out JsonElement pl)) md.Plain = pl.GetBoolean();
                    if (v.TryGetProperty("spells", out JsonElement spl)) md.Spells = Ints(spl);
                    if (v.TryGetProperty("cc_immune", out JsonElement cci)) md.CcImmune = cci.GetBoolean();
                    if (v.TryGetProperty("guard_r", out JsonElement gr)) md.GuardR = gr.GetInt32();
                    if (v.TryGetProperty("guards_follow", out JsonElement gf)) md.GuardsFollow = gf.GetBoolean();
                    if (v.TryGetProperty("model", out JsonElement mo)) md.Model = mo.GetInt32();
                    if (v.TryGetProperty("realm", out JsonElement rl)) md.Realm = rl.GetInt32();
                    if (v.TryGetProperty("guild", out JsonElement gd)) md.Guild = gd.GetString();
                    if (v.TryGetProperty("drop", out JsonElement dr))
                    {
                        md.DropName = Str(dr, "name");
                        md.DropSlot = Str(dr, "slot");
                    }
                    if (v.TryGetProperty("guards", out JsonElement gu))
                        foreach (JsonProperty p in gu.EnumerateObject()) md.Guards[p.Name] = p.Value.GetInt32();
                    d.Members[m.Name] = md;
                }
                foreach (JsonElement s in root.GetProperty("sites").EnumerateArray())
                {
                    var sd = new SiteDef { Id = Str(s, "id"), Kind = Str(s, "kind") ?? "camp" };
                    if (s.TryGetProperty("at", out JsonElement at)) sd.At = Ints(at);
                    if (s.TryGetProperty("area", out JsonElement ar)) sd.Area = Ints(ar);
                    if (s.TryGetProperty("r", out JsonElement rr)) sd.R = rr.GetInt32();
                    if (s.TryGetProperty("spacing", out JsonElement spc))
                    {
                        sd.Spacing = spc.GetInt32();
                        sd.SpacingSet = true;
                    }
                    if (s.TryGetProperty("ring", out JsonElement rg)) sd.Ring = Ints(rg);
                    if (s.TryGetProperty("polygon", out JsonElement pg)) sd.Polygon = pg.EnumerateArray().Select(Ints).ToList();
                    if (s.TryGetProperty("noclear", out JsonElement nc)) sd.NoClear = nc.GetBoolean();
                    if (s.TryGetProperty("even", out JsonElement ev)) sd.Even = ev.GetBoolean();
                    if (s.TryGetProperty("names", out JsonElement nm))
                        foreach (JsonElement x in nm.EnumerateArray()) sd.Names.Add(x.GetString());
                    sd.Block = Str(s, "block");
                    sd.Time = Str(s, "time");
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
                if (d.Themes.Count > 0)
                    _themes[d.Zone] = d.Themes;
            foreach (ZoneDef d in defs)
            {
                try
                {
                    Report r = Build(d);
                    Reports.Add(r);
                    Console.WriteLine($"[ZoneBuilds] {r.Zone}: {r.Removed} monsters taken out, {r.Spawned} placed" +
                        (r.Missing > 0 ? $", {r.Missing} not placed" : "") + (r.Blocked > 0 ? $", {r.Blocked} kept out by clear sites" : "") + (r.Notes.Count > 0 ? " - " + string.Join("; ", r.Notes.Take(8)) : ""));
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
                    if (o is GameNPC n && n.CurrentZone == zone && !rep.Placed.Contains(n) && !Exempt.TryGetValue(n, out object _) &&
                        n.TempProperties.GetProperty<object>(Quests.ClassicQuests.EventSpawnProperty) == null &&   // a quest's own encounter (Mandra's two youths)
                        sweepNames.Contains(n.Name) && Ordinary(n, d) &&
                        (n.GetType() == typeof(GameNPC) || replacedTypes.Contains(n.GetType().FullName)))
                    {
                        n.Delete();
                        rep.Removed++;
                    }
                return 30000;
            }, 30000);

            // "clear" sites (owner's /zmark thin-outs): what's named there now goes - kept monsters too (the roane on the
            // island) - and BuildSite keeps their kind (or a night site's monsters) from being placed inside
            foreach (SiteDef cs in d.Sites.Where(x => x.Kind == "clear" && x.At != null && x.Names.Count > 0))
                foreach (GameObject o in (region.Objects ?? Array.Empty<GameObject>()).ToArray())
                    if (o is GameNPC n && n.CurrentZone == zone && n.Realm == eRealm.None && n is not GameBot &&
                        cs.Names.Contains(n.Name) && InCircle(cs, n.X - zone.XOffset, n.Y - zone.YOffset))
                    {
                        n.Delete();
                        rep.Removed++;
                    }

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
                Faction f = kv.Value.Shared ? FactionMgr.GetFactionByID(kv.Value.Id) : null;
                if (f == null)
                {
                    f = new Faction();
                    f.LoadFromDatabase(new DbFaction { ID = kv.Value.Id, Name = kv.Key, BaseAggroLevel = kv.Value.Aggro });
                    if (kv.Value.Shared)
                    {
                        FactionMgr.Factions[kv.Value.Id] = f;
                        f.FriendFactions.Add(f);                 // killing one of them sours you with them all
                    }
                }
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
                    var placedBefore = new HashSet<GameNPC>(rep.Placed);
                    BuildSite(d, s, zone, region, pool, templates, factions, rng, rep);
                    _bySite[$"{d.Zone}:{s.Id}"] = rep.Placed.Where(n => !placedBefore.Contains(n)).ToList();
                    if (s.Time is "night" or "day")
                        foreach (GameNPC n in rep.Placed)
                            if (!placedBefore.Contains(n))
                                rep.Timed.Add((n, s.Time == "night"));
                }
                catch (Exception ex)
                {
                    rep.Notes.Add($"{s.Id}: {ex.Message}");
                }
            }

            // night (or day) sites: out only then - checked every half minute; one in a fight finishes it first
            if (rep.Timed.Count > 0)
                new ECSGameTimer(null, _ =>
                {
                    bool night = region.IsNightTime;
                    foreach (var (n, atNight) in rep.Timed)
                    {
                        bool want = atNight == night;
                        if (!want && n.ObjectState == GameObject.eObjectState.Active && n.IsAlive && !n.InCombat)
                            n.RemoveFromWorld();
                        // (put away, not dead: IsAlive is false for anything out of the world, so it was never brought back -
                        // owner 2026-11-23: Ceo Dubh, the finliaths, the Gravewarden and the haunted forest's night never came)
                        else if (want && n.ObjectState == GameObject.eObjectState.Inactive && n.Health > 0)
                            n.AddToWorld();
                    }
                    return 30000;
                }, 5000);
            return rep;
        }

        // ------------------------------------------------------------------ a roaming leader's companions

        static readonly List<(GameNPC Guard, GameNPC Leader)> _followers = new();
        static ECSGameTimer _followTimer;

        /// <summary>A companion that walks with its roaming leader and helps it (owner 2026-11-23, mark 28: "He was standing
        /// off to the side and not following the enchanter / or helping the enchanter" - a one-off Follow at placement was
        /// dropped by the brain's own walking and never came back after a respawn). Every three seconds: if the leader fights,
        /// the companion joins its fight; otherwise it keeps within a few steps of it, and its home moves with the leader so
        /// it never walks back to where it was placed.</summary>
        static void KeepWith(GameNPC guard, GameNPC leader)
        {
            lock (_followers)
            {
                _followers.Add((guard, leader));
                _followTimer ??= new ECSGameTimer(null, _ =>
                {
                    lock (_followers)
                        foreach (var (g, l) in _followers)
                            try
                            {
                                Tend(g, l);
                            }
                            catch
                            {
                            }
                    return 3000;
                }, 3000);
            }
        }

        static void Tend(GameNPC g, GameNPC l)
        {
            if (g.ObjectState != GameObject.eObjectState.Active || !g.IsAlive || l.ObjectState != GameObject.eObjectState.Active ||
                !l.IsAlive || g.CurrentRegion != l.CurrentRegion)
                return;
            if (l.InCombat && l.TargetObject is GameLiving foe && foe.IsAlive && !g.InCombat && g.IsWithinRadius(foe, 2500) &&
                g.Brain is StandardMobBrain gb)
            {
                gb.AddToAggroList(foe, 1);
                return;
            }
            if (g.InCombat)
                return;
            g.SpawnPoint = new Point3D(l.X, l.Y, l.Z);
            if (!g.IsWithinRadius(l, 220))
            {
                double a = Util.RandomDouble() * Math.PI * 2;
                g.WalkTo(new Point3D(l.X + (int) (Math.Cos(a) * 90), l.Y + (int) (Math.Sin(a) * 90), l.Z), (short) Math.Max(g.MaxSpeed, l.MaxSpeed));
            }
        }

        // ------------------------------------------------------------------ camp mates help each other

        const int AssistRange = 400, AssistMax = 2;
        static readonly ConcurrentDictionary<GameNPC, long> _lastCall = new();
        static readonly ConcurrentDictionary<GameNPC, string> _side = new();   // faction, else the camp or patrol

        /// <summary>Owner's playtest (2026-11-19): "Some villainous youth recruits weren't aggressive and walked past while
        /// their superiors fought. Camp members of one faction should join a fight next to them." When a player, a bot or a
        /// pet hits a camp or patrol member (or a faction member anywhere), up to two of its side right next to it who
        /// aren't fighting join in - next to it only, so a spaced-out camp can still be pulled one or two at a time; at
        /// most once every four seconds each, so a long fight doesn't keep pulling.</summary>
        static void CallFriends(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GameNPC n || !_side.TryGetValue(n, out string side) || args is not AttackedByEnemyEventArgs a)
                return;
            GameLiving attacker = a.AttackData?.Attacker;
            if (attacker == null || !attacker.IsAlive || attacker.Realm == eRealm.None)
                return;
            long now = GameLoop.GameLoopTime;
            if (_lastCall.TryGetValue(n, out long last) && now - last < 4000)
                return;
            _lastCall[n] = now;
            int joined = 0;
            foreach (GameNPC f in n.GetNPCsInRadius(AssistRange).OrderBy(f => f.GetDistanceTo(n)))
            {
                if (joined >= AssistMax)
                    break;
                if (f != n && f.IsAlive && !f.InCombat && _side.TryGetValue(f, out string fs) && fs == side &&
                    f.Brain is StandardMobBrain b && !b.HasAggro)
                {
                    b.AddToAggroList(attacker, 1);
                    joined++;
                }
            }
        }

        // ------------------------------------------------------------------ a named monster's own drop

        static readonly ConcurrentDictionary<GameNPC, (string Name, string Slot)> _drops = new();

        /// <summary>A named monster's own item, made for whoever killed it (their class, a level above theirs: levels
        /// don't decide where you hunt), with the monster's name for it - straight into their bags.</summary>
        static void DropUnique(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GameNPC n || !_drops.TryGetValue(n, out var drop) || args is not DyingEventArgs da)
                return;
            GamePlayer p = da.Killer as GamePlayer;
            if (p == null && da.Killer is GameNPC { Brain: IControlledBrain cb })
                p = cb.GetPlayerOwner();
            if (p == null && da.Killer is GameLiving kl && kl.Group != null)
                p = kl.Group.GetPlayersInTheGroup().FirstOrDefault();
            if (p == null)
                return;
            try
            {
                byte level = (byte) Math.Clamp(p.Level + 1, 1, 51);
                var cls = (eCharacterClass) p.CharacterClass.ID;
                GeneratedUniqueItem made = null;
                if (string.Equals(drop.Slot, "cloak", StringComparison.OrdinalIgnoreCase))
                    try { made = new GeneratedUniqueItem(p.Realm, cls, level, eObjectType.Magical, eInventorySlot.Cloak, 40); } catch { made = null; }
                made ??= AtlasROGManager.GenerateMonsterLootROG(p.Realm, cls, level, false);
                made.Name = drop.Name;
                made.AllowAdd = true;
                made.IsTradable = false;
                DbInventoryItem item = GameInventoryItem.Create<DbItemUnique>(made);
                item.IsROG = true;
                lock (p.Inventory.Lock)
                {
                    if (!p.Inventory.AddItem(eInventorySlot.FirstEmptyBackpack, item))
                    {
                        p.Out.SendMessage($"{n.Name} leaves {drop.Name}, but your bags are full.", PacketHandler.eChatType.CT_Important, PacketHandler.eChatLoc.CL_SystemWindow);
                        return;
                    }
                }
                p.Out.SendMessage($"You take {drop.Name} from {n.Name}.", PacketHandler.eChatType.CT_Loot, PacketHandler.eChatLoc.CL_SystemWindow);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZoneBuilds] drop {drop.Name}: {ex.Message}");
            }
        }

        static int TierIndex(ZoneDef d, string memberKey) =>
            d.Members.TryGetValue(memberKey, out MemberDef m) && m.Tier != null ? Array.IndexOf(TierNames, m.Tier.ToLowerInvariant()) : 1;

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
                case "clear":
                    break;

                case "wildlife":
                {
                    int[] area = s.Area ?? (s.Polygon != null
                        ? new[] { s.Polygon.Min(p => p[0]), s.Polygon.Min(p => p[1]), s.Polygon.Max(p => p[0]), s.Polygon.Max(p => p[1]) }
                        : null);
                    if (area == null)
                        break;
                    var taken = new List<Vector3>();
                    foreach (var kv in s.Spawn)
                        for (int i = 0; i < kv.Value; i++)
                        {
                            Func<Vector3> pick = () =>
                            {
                                for (int tries = 0; ; tries++)
                                {
                                    int lx = rng.Next(area[0], area[2]), ly = rng.Next(area[1], area[3]);
                                    if (s.Polygon == null || InPolygon(s.Polygon, lx, ly) || tries > 30)
                                        return W(lx, ly);
                                }
                            };
                            Vector3 at = s.SpacingSet ? Spaced(() => Good(pick), _ => true, taken, s.Spacing) : Good(pick);
                            taken.Add(at);
                            Place(d, kv.Key, at, s, region, templates, factions, rng, rep);
                        }
                    break;
                }

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
                    // owner's playtest (2026-11-19): "Spread camp members out more inside each camp, so a melee player can
                    // pull one or two at a time ... Stronger monsters can keep lower-con bodyguards near them, but leave
                    // room to pick the weaker ones off first." The strongest are placed first and deepest in, the weak
                    // round the edge, everyone at least Spacing apart; a member's guards stand a short way from it.
                    Vector3 c = W(s.At[0], s.At[1]);
                    var taken = new List<Vector3>();
                    foreach (var kv in s.Spawn.OrderByDescending(kv => TierIndex(d, kv.Key)))
                    {
                        int ti = TierIndex(d, kv.Key);
                        double inner = ti >= 4 ? 0 : ti == 3 ? 0.2 : 0.45;          // how far out they start, of R
                        double outer = ti >= 4 ? 0.35 : ti == 3 ? 0.7 : 1.0;
                        if (s.Even)
                        {
                            inner = 0;
                            outer = 1.0;
                        }
                        if (s.Ring is { Length: 2 })                    // between two distances (a horde round its boss)
                        {
                            inner = s.Ring[0] / (double) Math.Max(1, s.Ring[1]);
                            outer = 1.0;
                        }
                        int reach = s.Ring is { Length: 2 } ? s.Ring[1] : s.R;
                        for (int i = 0; i < kv.Value; i++)
                        {
                            Vector3 at = Spaced(() => Good(() => Near(zone, c, Math.Max(150, (int) (reach * outer)), rng)),
                                v => Vector2.Distance(new Vector2(v.X, v.Y), new Vector2(c.X, c.Y)) >= reach * inner, taken, s.Spacing);
                            taken.Add(at);
                            if (Place(d, kv.Key, at, s, region, templates, factions, rng, rep) is GameNPC leader &&
                                d.Members.TryGetValue(kv.Key, out MemberDef lm))
                                foreach (var g in lm.Guards)
                                    for (int k = 0; k < g.Value; k++)
                                    {
                                        Vector3 ga = Spaced(() => Near(zone, at, lm.GuardR, rng),
                                            v => Vector2.Distance(new Vector2(v.X, v.Y), new Vector2(at.X, at.Y)) >= Math.Min(120, lm.GuardR / 2), taken, 140);
                                        taken.Add(ga);
                                        if (Place(d, g.Key, ga, s, region, templates, factions, rng, rep) is GameNPC guard && lm.GuardsFollow)
                                            KeepWith(guard, leader);
                                    }
                        }
                    }
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

        /// <summary>A spot that keeps its distance from those already taken (and passes <paramref name="ok"/>): the first
        /// of a few tries that does, else the one that came closest.</summary>
        static Vector3 Spaced(Func<Vector3> pick, Func<Vector3, bool> ok, List<Vector3> taken, int spacing)
        {
            Vector3 best = default;
            float bestGap = -1;
            for (int i = 0; i < 12; i++)
            {
                Vector3 v = pick();
                float gap = float.MaxValue;
                foreach (Vector3 t in taken)
                    gap = Math.Min(gap, Vector2.Distance(new Vector2(v.X, v.Y), new Vector2(t.X, t.Y)));
                bool good = ok(v);
                if (good && gap >= spacing)
                    return v;
                float score = good ? gap : gap * 0.5f;
                if (score > bestGap)
                {
                    bestGap = score;
                    best = v;
                }
            }
            return best;
        }

        static bool InCircle(SiteDef c, int lx, int ly) =>
            (long) (lx - c.At[0]) * (lx - c.At[0]) + (long) (ly - c.At[1]) * (ly - c.At[1]) <= (long) c.R * c.R;

        static bool InPolygon(List<int[]> poly, int x, int y)
        {
            bool inside = false;
            for (int i = 0, j = poly.Count - 1; i < poly.Count; j = i++)
                if ((poly[i][1] > y) != (poly[j][1] > y) &&
                    x < (poly[j][0] - poly[i][0]) * (double) (y - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0])
                    inside = !inside;
            return inside;
        }

        /// <summary>A "clear" site keeps its kinds out (by member name or pattern), or with block "night" every night site's
        /// monsters, or with "all" everything - except a site marked noclear.</summary>
        static bool Blocked(ZoneDef d, SiteDef s, MemberDef m, int lx, int ly)
        {
            if (s.NoClear || s.Kind == "clear")
                return false;
            foreach (SiteDef c in d.Sites)
            {
                if (c.Kind != "clear" || c.At == null || !InCircle(c, lx, ly))
                    continue;
                if (c.Block == "all" || c.Block == "night" && s.Time == "night" ||
                    c.Names.Contains(m.From) || m.Name != null && c.Names.Contains(m.Name))
                    return true;
            }
            return false;
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
            Zone pz = WorldMgr.GetZone((ushort) d.Zone);
            if (pz != null && Blocked(d, s, m, (int) at.X - pz.XOffset, (int) at.Y - pz.YOffset))
            {
                rep.Blocked++;
                return null;
            }
            DbMob row = Copy(tpl);
            if (m.Plain)
                row.ClassType = DbMob.DEFAULT_NPC_CLASSTYPE;
            if (m.Model.HasValue)
                row.Model = (ushort) m.Model.Value;
            row.X = (int) at.X;
            row.Y = (int) at.Y;
            row.Z = (int) at.Z;
            row.Region = region.ID;
            row.Heading = (ushort) rng.Next(4096);
            row.PathID = null;
            if (m.Name != null)
                row.Name = m.Name;
            if (m.Realm.HasValue)
            {
                row.Realm = (byte) m.Realm.Value;
                row.Flags = 0;                                   // (a town guard's or a merchant's flags don't come along)
                row.Brain = "";
            }
            if (m.Guild != null)
                row.Guild = m.Guild;
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
            if (m.Spells is { Length: > 0 })
                npc.Spells = m.Spells.Select(id => SkillBase.GetSpellByID(id)).Where(sp => sp != null).ToList();
            if (m.CcImmune)
                npc.AddAbility(SkillBase.GetAbility(Abilities.CCImmunity));
            if (m.Faction != null && factions.TryGetValue(m.Faction, out Faction f))
                npc.Faction = f;
            if (m.DropName != null)
            {
                _drops[npc] = (m.DropName, m.DropSlot);
                GameEventMgr.AddHandler(npc, GameLivingEvent.Dying, DropUnique);
            }
            string side = m.Faction ?? (s.Kind is "camp" or "patrol" or null ? $"site:{s.Id}" : null);
            if (side != null)
            {
                _side[npc] = side;
                GameEventMgr.AddHandler(npc, GameLivingEvent.AttackedByEnemy, CallFriends);
            }
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

        static readonly ConcurrentDictionary<string, List<GameNPC>> _bySite = new();

        /// <summary>The monsters a site placed (a zone's siege sends an island's garrison away while it is held).</summary>
        public static IReadOnlyList<GameNPC> SiteNpcs(int zone, string site) =>
            _bySite.TryGetValue($"{zone}:{site}", out var l) ? l : (IReadOnlyList<GameNPC>) Array.Empty<GameNPC>();

        /// <summary>The sites a zone's build placed (King Lug's campaign sweeps all but the pockets of a won forest).</summary>
        public static IReadOnlyList<string> SiteIds(int zone) =>
            _bySite.Keys.Where(k => k.StartsWith(zone + ":")).Select(k => k.Substring(k.IndexOf(':') + 1)).ToList();

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
            if (args.Length > 1 && args[1].ToLowerInvariant() == "timed")
            {
                // the night (and day) sites' monsters: how many are out, put away, dead or gone
                foreach (ZoneBuilds.Report r in ZoneBuilds.Reports.Where(r => r.Timed.Count > 0))
                {
                    Zone z = WorldMgr.GetZone((ushort) r.ZoneId);
                    var c = r.Timed.GroupBy(t => $"{t.Npc.Name} ({(t.AtNight ? "night" : "day")})")
                        .Select(g => $"{g.Key}: {g.Count(t => t.Npc.ObjectState == GameObject.eObjectState.Active)} out, " +
                                     $"{g.Count(t => t.Npc.ObjectState == GameObject.eObjectState.Inactive)} away, " +
                                     $"{g.Count(t => t.Npc.ObjectState == GameObject.eObjectState.Deleted)} deleted, " +
                                     $"{g.Count(t => !t.Npc.IsAlive)} dead");
                    DisplayMessage(client, $"{r.Zone} (night {z?.ZoneRegion?.IsNightTime}): " + string.Join("; ", c));
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
