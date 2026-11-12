using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using DOL.Database;
using DOL.GS.DynamicEvents;
using DOL.Logging;
using Newtonsoft.Json;

namespace DOL.GS
{
    /// <summary>
    /// Zone level bands (owner 2026-11-02: "let's clean up the zone bands ... the lowest level mobs near [the starting
    /// towns], and then growing outward ... Cursed Forest and Sheeroe Hills should be the elite zones still ... make sure
    /// the SI zones are banded in an intelligent way as well, as well as dungeons in each zone if the level of the zone
    /// that the dungeon is in changes drastically. Albion and Midgard can be the same").
    ///
    /// Nothing in the database changes: an outdoor monster's level is remapped as it spawns (GameNPC.LoadFromDatabase
    /// and each respawn), from its original level and where it stands, by gameutils/data/level_bands.json (or
    /// runtime/server/level-bands.json):
    /// - each banded zone has a band [min, max]; a monster's place in it is mostly how far it stands from the nearest
    ///   starting town of its region (0 at the zone's nearest spot to one, 1 at its farthest; gradient_weight), the rest
    ///   where its original level ranked among the zone's monsters - so camps keep their relative order and the levels
    ///   grow outward from the towns across zone lines. Elite zones ("gradient": false) go by rank alone;
    /// - a monster far over its zone (original level above the zone's 90th percentile + boss_margin: named ones,
    ///   bosses) sits up to boss_extra_max levels over the band; level keep_at_or_above (60) and up is left alone;
    /// - a dungeon entered from a banded zone moves by as much as the zone moved at its entrance, when that is at
    ///   least dungeon_shift_min levels;
    /// - the dynamic events' levels (chains, their monsters, givers, guards, bosses) are mapped the same way at load.
    /// Only realm-less, non-peaceful database monsters are touched (no guards, merchants, bots, pets, event NPCs);
    /// a saved monster keeps its original level in the database.
    /// </summary>
    public static class LevelBands
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);
        private const string ResourceSuffix = "level_bands.json";
        private static readonly object _lock = new();
        private static bool _ready;
        private static Config _config;
        private static readonly Dictionary<ushort, ZoneBand> _bands = new();
        private static readonly Dictionary<ushort, ZoneStats> _stats = new();
        private static readonly Dictionary<ushort, int> _dungeonShift = new();

        public sealed class Anchor
        {
            public string Name;
            public ushort Region;
            public int X, Y;
        }

        public sealed class ZoneBand
        {
            public string Name;
            public int Min, Max;
            public bool Gradient = true;
        }

        public sealed class Start
        {
            public string Name;
            public ushort Region;
            public int X, Y, Z;
            public ushort Heading;
        }

        public sealed class Config
        {
            public bool Enabled = true;
            public Dictionary<string, Start> Starts = new();
            [JsonProperty("gradient_weight")] public double GradientWeight = 0.65;
            [JsonProperty("boss_margin")] public int BossMargin = 8;
            [JsonProperty("boss_extra_max")] public int BossExtraMax = 6;
            [JsonProperty("keep_at_or_above")] public int KeepAtOrAbove = 60;
            [JsonProperty("dungeon_shift_min")] public int DungeonShiftMin = 5;
            [JsonProperty("dungeon_exclude")] public List<int> DungeonExclude = new();
            public List<Anchor> Anchors = new();
            public Dictionary<string, ZoneBand> Zones = new();
        }

        private sealed class ZoneStats
        {
            public int[] Levels = Array.Empty<int>();     // the zone's original ordinary levels, sorted
            public int P50, P90;
            public double DMin = double.MaxValue, DMax;   // its monsters' distances to the nearest starting town
        }

        public static bool Enabled
        {
            get
            {
                Ensure();
                return _config?.Enabled == true;
            }
        }

        /// <summary>Whether this monster's level is banded: an outdoor-world, realm-less, non-peaceful database mob.</summary>
        public static bool Applies(GameNPC npc) =>
            npc != null && npc is not GameBot && npc is not EventNpc && npc is not GameConsignmentMerchant &&
            npc.Realm == eRealm.None && (npc.Flags & GameNPC.eFlags.PEACE) == 0 && npc.Brain is not AI.Brain.IControlledBrain;

        /// <summary>The level a monster of this original level standing here comes at.</summary>
        public static byte Remap(ushort regionId, int x, int y, byte level)
        {
            if (level == 0 || !Enabled || level >= _config.KeepAtOrAbove)
                return level;
            Zone zone = WorldMgr.GetRegion(regionId)?.GetZone(x, y);
            if (zone != null && _bands.TryGetValue(zone.ID, out ZoneBand band) && _stats.TryGetValue(zone.ID, out ZoneStats st) &&
                st.Levels.Length > 0)
                // (a starting zone's band begins at 0 - owner 2026-11-12: "some level 0 mobs near the starting areas.
                // Level 1s are actually quite tough for a brand new player or bot")
                return (byte) Math.Clamp(Banded(band, st, regionId, x, y, level), band.Min <= 0 ? 0 : 1, 255);
            if (_dungeonShift.TryGetValue(regionId, out int shift))
                return (byte) Math.Clamp(level + shift, 1, _config.KeepAtOrAbove - 1);
            return level;
        }

        private static int Banded(ZoneBand band, ZoneStats st, ushort regionId, int x, int y, int level)
        {
            if (level > st.P90 + _config.BossMargin)
                return band.Max + Math.Clamp(1 + (level - st.P90 - _config.BossMargin) / 4, 1, _config.BossExtraMax);
            // mid-rank of the original level among the zone's
            int below = LowerBound(st.Levels, level);
            int upTo = LowerBound(st.Levels, level + 1);
            double rank = st.Levels.Length > 1 ? (below + (upTo - below) * 0.5) / st.Levels.Length : 0.5;
            double p = rank;
            if (band.Gradient && st.DMax > st.DMin)
            {
                double d = NearestAnchor(regionId, x, y);
                double pd = Math.Clamp((d - st.DMin) / (st.DMax - st.DMin), 0, 1);
                p = _config.GradientWeight * pd + (1 - _config.GradientWeight) * rank;
            }
            return (int) Math.Round(band.Min + p * (band.Max - band.Min));
        }

        private static int LowerBound(int[] a, int v)
        {
            int lo = 0, hi = a.Length;
            while (lo < hi)
            {
                int mid = (lo + hi) / 2;
                if (a[mid] < v) lo = mid + 1; else hi = mid;
            }
            return lo;
        }

        private static double NearestAnchor(ushort regionId, int x, int y)
        {
            double best = double.MaxValue;
            foreach (Anchor a in _config.Anchors)
                if (a.Region == regionId)
                    best = Math.Min(best, Math.Sqrt((double) (a.X - x) * (a.X - x) + (double) (a.Y - y) * (a.Y - y)));
            return best;
        }

        private static void Ensure()
        {
            if (_ready)
                return;
            lock (_lock)
            {
                if (_ready)
                    return;
                try
                {
                    Load();
                }
                catch (Exception e)
                {
                    log.Error("Level bands: could not load - levels are as in the database", e);
                    _config = new Config { Enabled = false };
                }
                _ready = true;
            }
        }

        private static void Load()
        {
            string text = null;
            string over = Path.Combine(GameServer.Instance.Configuration.RootDirectory, "level-bands.json");
            if (File.Exists(over))
                text = File.ReadAllText(over, Encoding.UTF8);
            else
            {
                Assembly asm = typeof(LevelBands).Assembly;
                string res = asm.GetManifestResourceNames().FirstOrDefault(n => n.EndsWith(ResourceSuffix, StringComparison.OrdinalIgnoreCase));
                if (res != null)
                    using (var s = new StreamReader(asm.GetManifestResourceStream(res)!, Encoding.UTF8))
                        text = s.ReadToEnd();
            }
            _config = text != null ? JsonConvert.DeserializeObject<Config>(text) : new Config { Enabled = false };
            if (_config == null || !_config.Enabled)
            {
                _config ??= new Config { Enabled = false };
                log.Info("Level bands: off");
                return;
            }
            foreach (var kv in _config.Zones)
                if (ushort.TryParse(kv.Key, out ushort id))
                    _bands[id] = kv.Value;
            // the zones' original levels and distances, from the database (as the world loads them)
            var levels = new Dictionary<ushort, List<int>>();
            var dist = new Dictionary<ushort, ZoneStats>();
            foreach (DbMob m in GameServer.Database.SelectAllObjects<DbMob>())
            {
                if (m.Realm != 0 || m.Level <= 0 || m.Level >= _config.KeepAtOrAbove || (m.Flags & (uint) GameNPC.eFlags.PEACE) != 0)
                    continue;
                Zone z = WorldMgr.GetRegion(m.Region)?.GetZone(m.X, m.Y);
                if (z == null || !_bands.ContainsKey(z.ID))
                    continue;
                if (!levels.TryGetValue(z.ID, out var list))
                    levels[z.ID] = list = new List<int>();
                list.Add(m.Level);
                if (!dist.TryGetValue(z.ID, out ZoneStats st))
                    dist[z.ID] = st = new ZoneStats();
                double d = NearestAnchor(m.Region, m.X, m.Y);
                if (d < double.MaxValue)
                {
                    st.DMin = Math.Min(st.DMin, d);
                    st.DMax = Math.Max(st.DMax, d);
                }
            }
            foreach (var kv in levels)
            {
                ZoneStats st = dist[kv.Key];
                st.Levels = kv.Value.OrderBy(l => l).ToArray();
                st.P50 = st.Levels[st.Levels.Length / 2];
                st.P90 = st.Levels[Math.Min(st.Levels.Length - 1, (int) (st.Levels.Length * 0.9))];
                _stats[kv.Key] = st;
            }
            // dungeons entered from a banded zone: moved as the zone moved at the entrance
            foreach (DbZonePoint zp in GameServer.Database.SelectAllObjects<DbZonePoint>())
            {
                Region target = WorldMgr.GetRegion(zp.TargetRegion);
                if (target == null || !target.IsDungeon || target.IsCapitalCity || target.IsRvR || _dungeonShift.ContainsKey(zp.TargetRegion) ||
                    _config.DungeonExclude.Contains(zp.TargetRegion))
                    continue;
                Zone src = WorldMgr.GetRegion(zp.SourceRegion)?.GetZone(zp.SourceX, zp.SourceY);
                if (src == null || !_bands.TryGetValue(src.ID, out ZoneBand band) || !_stats.TryGetValue(src.ID, out ZoneStats st))
                    continue;
                int before = st.P50;
                int after = Banded(band, st, zp.SourceRegion, zp.SourceX, zp.SourceY, before);
                int shift = after - before;
                if (Math.Abs(shift) >= _config.DungeonShiftMin)
                {
                    _dungeonShift[zp.TargetRegion] = shift;
                    log.Info($"Level bands: dungeon region {zp.TargetRegion} ({target.Description}) from {src.Description}: {shift:+#;-#;0} levels");
                }
            }
            foreach (var kv in _stats.OrderBy(k => k.Key))
            {
                ZoneBand b = _bands[kv.Key];
                log.Info($"Level bands: zone {kv.Key} {b.Name}: was {kv.Value.Levels[0]}-{kv.Value.P50}-{kv.Value.P90} (min/median/p90), " +
                         $"now {b.Min}-{b.Max}{(b.Gradient ? " outward from the towns" : "")}; {kv.Value.Levels.Length} monsters");
            }
        }

        /// <summary>Where every new character of this realm starts (the realm's hub town), or null: the database's
        /// StartupLocation as ever.</summary>
        public static Start StartOf(eRealm realm)
        {
            Ensure();
            return _config?.Enabled == true && _config.Starts != null && _config.Starts.TryGetValue(((int) realm).ToString(), out Start s) &&
                   s != null && s.Region > 0 ? s : null;
        }

        /// <summary>A monster's level in the database, before the bands (its live level when not banded).</summary>
        public static byte UnbandedLevel(GameNPC npc) => npc?.UnbandedLevel > 0 ? npc.UnbandedLevel : npc?.Level ?? 0;

        /// <summary>
        /// A banded monster's drops at its new level: a named drop with level versions (named_uniques.py's
        /// &lt;id&gt;_lNN, in fives) comes in the version for the monster's level; other items - period trinkets, quest
        /// pieces, money - as they are. (ROG drops and money already follow the monster's level.)
        /// </summary>
        public static DbItemTemplate[] LootAtLevel(GameNPC mob, DbItemTemplate[] drops)
        {
            if (mob == null || drops == null || drops.Length == 0 || !Enabled || mob.UnbandedLevel == 0 || mob.UnbandedLevel == mob.Level)
                return drops;
            for (int i = 0; i < drops.Length; i++)
            {
                DbItemTemplate d = drops[i];
                if (d == null || string.IsNullOrEmpty(d.Id_nb))
                    continue;
                string id = d.Id_nb;
                int us = id.LastIndexOf("_l", StringComparison.Ordinal);
                if (us > 0 && int.TryParse(id[(us + 2)..], out _))
                    id = id[..us];                       // already a level version: its family
                DbItemTemplate v = DynamicEvents.StageRuntime.ItemAtLevel(id, mob.Level);
                if (v != null && v.Id_nb != d.Id_nb)
                    drops[i] = v;
            }
            return drops;
        }

        /// <summary>A dynamic event chain's levels mapped as the monsters where it starts.</summary>
        public static void RemapChain(ChainDef c, ushort regionId, Zone zone)
        {
            if (!Enabled || c == null || zone == null)
                return;
            double[] at = c.Stages.FirstOrDefault(s => s.Center is { Length: >= 3 })?.Center;
            int x = zone.XOffset + (at != null ? (int) (at[0] / 0.025) : zone.Width / 2);
            int y = zone.YOffset + (at != null ? (int) (at[2] / 0.025) : zone.Height / 2);
            int Map(int l) => l <= 0 ? l : Remap(regionId, x, y, (byte) Math.Min(255, l));
            void MapRange(int[] r)
            {
                if (r == null)
                    return;
                for (int i = 0; i < r.Length; i++)
                    r[i] = Map(r[i]);
            }
            void MapMobs(IEnumerable<MobDef> mobs)
            {
                if (mobs != null)
                    foreach (MobDef m in mobs)
                        MapRange(m.Level);
            }
            void MapNpc(NpcDef n)
            {
                if (n != null)
                    n.Level = Map(n.Level);
            }
            MapRange(c.Levels);
            MapNpc(c.Giver);
            if (c.Guards != null)
                foreach (NpcDef g in c.Guards)
                    MapNpc(g);
            foreach (StageDef s in c.Stages)
            {
                MapMobs(s.Mobs);
                MapNpc(s.Protect);
                MapNpc(s.Boss);
                MapMobs(s.Waves?.Mobs);
                MapMobs(s.Adds?.Mobs);
                if (s.Ambushes != null)
                    foreach (AmbushDef a in s.Ambushes)
                        MapMobs(a.Mobs);
            }
        }
    }
}
