using System.Collections.Generic;
using Newtonsoft.Json;

namespace DOL.GS.DynamicEvents
{
    // Dynamic events (owner 2026-11-01: "emulate or take from GW2's dynamic events ... a system that is easy to duplicate
    // in other zones and realms"). A zone's events are data: scripts/dynamicevents/zones/zoneNNN_*.json (built into the
    // server) or runtime\server\dynamic-events\*.json (read at start-up, replaces a built-in file for the same zone).
    // A zone holds chains; a chain is a run of stages, each a reusable type (cull, defend, boss) given its own lore,
    // monsters and places; a stage's outcome picks the next stage. Points are zone metres as the new client shows them
    // ([x, y] or [x, y, z]; 1 m = 40 server units), z filled in by tools/claude-version/dynamic_events_fill_z.py.

    public class ZoneEventsDef
    {
        public int Zone;
        public ushort Region;
        public string Name;
        public string Lore;
        public int Realm;                          // the realm whose people live here (protected NPCs); 0 = by region
        public List<ChainDef> Chains = new();
    }

    public class ChainDef
    {
        public string Id;
        public string Title;
        public int[] Levels;
        [JsonProperty("first_delay_s")] public int[] FirstDelayS = { 300, 900 };
        [JsonProperty("interval_s")] public int[] IntervalS = { 1800, 2700 };
        public string Start;
        public List<StageDef> Stages = new();
        [JsonIgnore] public ZoneEventsDef ZoneDef;
    }

    public class StageDef
    {
        public string Id;
        public string Type;                        // cull | defend | boss
        public string Name;
        public string Objective;
        public string Announce;
        public double[] Center;
        public double Radius = 80;
        [JsonProperty("duration_s")] public int DurationS = 180;   // defend: hold this long
        [JsonProperty("time_s")] public int TimeS = 600;           // cull, boss: the time limit
        public int Kill = 10;                      // cull: how many to defeat
        public int Alive = 6;                      // cull: how many about at once
        public List<MobDef> Mobs = new();          // cull: what to spawn
        public NpcDef Protect;                     // defend: who to keep alive
        public WavesDef Waves;                     // defend: who comes for them
        public NpcDef Boss;                        // boss
        public WavesDef Adds;                      // boss: help it calls
        public string Success;
        public string Fail;
        [JsonProperty("on_success")] public string OnSuccess = "end";
        [JsonProperty("on_fail")] public string OnFail = "end";
        public RewardDef Reward;
    }

    public class MobDef
    {
        public int Template;                       // NpcTemplate id: look, gear, spells, stats
        public string Name;
        public int[] Level;                        // [min, max]
        public byte Size;
        public ushort Model;
    }

    public class NpcDef
    {
        public int Template;
        public string Name;
        public int Level;
        public byte Size;
        public ushort Model;
        public string Equipment;
        public double[] Pos;
        [JsonProperty("health_mult")] public double HealthMult = 1;
    }

    public class WavesDef
    {
        [JsonProperty("every_s")] public int EveryS = 30;
        public int Count = 3;
        public List<double[]> From = new();        // defend: where waves come from (boss adds: round the boss)
        public List<MobDef> Mobs = new();
    }

    public class RewardDef
    {
        [JsonProperty("xp_pct")] public double XpPct;            // of the level's experience, at gold
        [JsonProperty("copper_per_level")] public int CopperPerLevel;
        public ItemRewardDef Item;
    }

    public class ItemRewardDef
    {
        public string Id;
        [JsonProperty("gold_chance")] public int GoldChance;
        [JsonProperty("silver_chance")] public int SilverChance;
    }
}
