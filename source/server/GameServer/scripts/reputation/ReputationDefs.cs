using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using Newtonsoft.Json;

namespace DOL.GS.Reputation
{
    /// <summary>
    /// The factions of a zone (owner 2026-11-22: "maybe something like 2 per zone. There can be the faction tied to the
    /// ruling faction of Tir Na Nog who's fighting the bandits and Dergans and the like, and then one tied to the druids,
    /// celts etc tied to dealing with the Fae creatures"): scripts/reputation/repNNN_zone.json, one file per zone, so the
    /// next zone is data - its two factions, their titles, who speaks for them, their quartermaster's stock, and which
    /// story quests, events and monsters count toward which.
    /// </summary>
    public class RepZoneDef
    {
        public int Zone;
        public string Name;
        public int Realm = 3;
        public int[] Levels = { 1, 50 };                      // what the zone is for (a bot's starting standing)
        public List<RepFactionDef> Factions = new();
        [JsonProperty("kill_default")] public string KillDefault;
        [JsonProperty("event_default")] public string EventDefault;
        [JsonProperty("quest_default")] public string QuestDefault;
        public Dictionary<string, string> Quests = new();     // quest id (or "quest:ending") -> faction key
        public Dictionary<string, string> Events = new();     // event chain id -> faction key
        public List<RepZoneQuartermasterDef> Quartermasters = new();   // more quartermasters here, for any faction here
                                                              // (Silvermine's Rowan quartermaster, a cousin of Ardee's)
        public List<string> Shared = new();                   // another zone's factions that are here too (owner
                                                              // 2026-11-22: the Order of the Rowan in Connacht and
                                                              // Silvermine) - one standing, counted once

        public RepFactionDef Faction(string key) => key == null ? null : Factions.FirstOrDefault(f => f.Key == key);
    }

    public class RepFactionDef
    {
        public string Key;
        public string Name;                                   // "the Mag Mell Guard"
        public string Short;                                  // "Mag Mell Guard"
        public List<string> Titles = new();                   // Trusted, Honoured, Legend ("female|male" where they differ)
        public string Speaker;                                // the story NPC who speaks for it (greetings, the crier)
        public string Town;
        public List<string> Kills = new();                    // words in a monster's name that make it this faction's foe
        public RepQuartermasterDef Quartermaster;
        public List<string> Kin = new();                      // kin factions (owner 2026-11-22): Honoured with one of
                                                              // them earns this one 50% faster, Legend twice as fast
        [JsonIgnore] public RepZoneDef ZoneDef;               // its home zone (a shared faction's is the one it's from)

        /// <summary>The title for a rank (Trusted and up), by the bearer's gender where it has two.</summary>
        public string Title(Rank rank, bool female)
        {
            int i = (int) rank - (int) Rank.Trusted;
            if (i < 0 || i >= Titles.Count)
                return null;
            string t = Titles[i];
            int bar = t.IndexOf('|');
            return bar < 0 ? t : female ? t[..bar] : t[(bar + 1)..];
        }
    }

    public class RepQuartermasterDef
    {
        public string Name;
        public string Guild;
        public ushort Model = 337;
        public string Anchor;                                 // a story NPC to stand beside
        public double[] Offset = { 3, 3 };                    // metres east / south of them
        public string Greet;
        public List<RepStockDef> Stock = new();
    }

    /// <summary>A zone's own quartermaster for one of its factions (a shared one's, in the other zone).</summary>
    public class RepZoneQuartermasterDef : RepQuartermasterDef
    {
        public string Faction;                                // the faction's key
    }

    public class RepStockDef
    {
        public string Item;                                   // an item id (its level version is sold: <id>_lNN)
        public Rank Rank = Rank.Trusted;
        public int Price;                                     // Marks of Valor
    }

    public class RepRealmDef
    {
        public string Name;
        public List<string> Titles = new();
    }

    public class RepRealmsFile
    {
        public Dictionary<string, RepRealmDef> Realms = new();
    }

    public enum Rank { Unknown = 0, Familiar = 1, Trusted = 2, Honoured = 3, Legend = 4 }

    public static class RepDefs
    {
        static List<RepZoneDef> _zones;
        static Dictionary<int, RepRealmDef> _realms;
        static readonly object _lock = new();

        public static IReadOnlyList<RepZoneDef> Zones { get { Load(); return _zones; } }

        public static RepZoneDef ForZone(int zoneId) => Zones.FirstOrDefault(z => z.Zone == zoneId);
        public static RepZoneDef ForZone(Zone zone) => zone == null ? null : ForZone(zone.ID);

        public static RepRealmDef Realm(eRealm realm)
        {
            Load();
            return _realms.TryGetValue((int) realm, out RepRealmDef r) ? r : null;
        }

        /// <summary>A faction anywhere, by its key.</summary>
        public static RepFactionDef Faction(string key) => Zones.SelectMany(z => z.Factions).FirstOrDefault(f => f.Key == key);

        /// <summary>Every faction once (a shared one is in more than one zone's list).</summary>
        public static IEnumerable<RepFactionDef> AllFactions => Zones.SelectMany(z => z.Factions).Distinct();

        public static void Reload()
        {
            lock (_lock)
            {
                _zones = null;
                _realms = null;
            }
            Load();
        }

        /// <summary>A zone's shared factions: the home zone's own instance, added to its list.</summary>
        public static void Share(List<RepZoneDef> zones)
        {
            foreach (RepZoneDef z in zones)
                foreach (string key in z.Shared)
                {
                    RepFactionDef f = zones.Where(o => o != z).SelectMany(o => o.Factions).FirstOrDefault(x => x.Key == key && x.ZoneDef != z);
                    if (f == null)
                        Console.WriteLine($"[Reputation] {z.Name}: no faction '{key}' to share");
                    else if (!z.Factions.Contains(f))
                        z.Factions.Add(f);
                }
        }

        static void Load()
        {
            if (_zones != null)
                return;
            lock (_lock)
            {
                if (_zones != null)
                    return;
                var zones = new List<RepZoneDef>();
                var realms = new Dictionary<int, RepRealmDef>();
                Assembly asm = typeof(RepDefs).Assembly;
                foreach (string res in asm.GetManifestResourceNames().Where(n => n.StartsWith("Reputation.") && n.EndsWith(".json")).OrderBy(n => n))
                {
                    try
                    {
                        using var s = new StreamReader(asm.GetManifestResourceStream(res)!, Encoding.UTF8);
                        string json = s.ReadToEnd();
                        if (res.EndsWith("realms.json"))
                        {
                            RepRealmsFile f = JsonConvert.DeserializeObject<RepRealmsFile>(json);
                            foreach (var (k, v) in f?.Realms ?? new())
                                if (int.TryParse(k, out int id))
                                    realms[id] = v;
                            continue;
                        }
                        RepZoneDef z = JsonConvert.DeserializeObject<RepZoneDef>(json);
                        if (z == null || z.Factions.Count + z.Shared.Count == 0)
                            continue;
                        foreach (RepFactionDef f in z.Factions)
                            f.ZoneDef = z;
                        zones.Add(z);
                    }
                    catch (Exception e)
                    {
                        Console.WriteLine($"[Reputation] {res}: {e.Message}");
                    }
                }
                Share(zones);
                _realms = realms;
                _zones = zones;
            }
        }
    }
}
