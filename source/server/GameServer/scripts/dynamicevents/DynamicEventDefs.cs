using System.Collections.Generic;
using Newtonsoft.Json;

namespace DOL.GS.DynamicEvents
{
    // Dynamic events (owner 2026-11-01: "emulate or take from GW2's dynamic events ... a system that is easy to duplicate
    // in other zones and realms"). A zone's events are data: scripts/dynamicevents/zones/zoneNNN_*.json (built into the
    // server) or runtime\server\dynamic-events\*.json (read at start-up, replaces a built-in file for the same zone).
    // A zone holds chains; a chain is a run of stages, each a reusable type (cull, defend, boss, escort) given its own
    // lore, monsters and places; a stage's outcome picks the next stage. A chain either wakes on its own (its time comes:
    // a "disturbance" shows on the map, and it starts when a player or a bot comes near) or is started by talking to its
    // giver (an NPC who then leads the way with a party of guards). Points are zone metres as the new client shows them
    // ([x, y] or [x, y, z]; 1 m = 40 server units), z filled in by tools/claude-version/dynamic_events_fill_z.py.
    // See README.md.

    public class ZoneEventsDef
    {
        public int Zone;
        public ushort Region;
        public string Name;
        public string Lore;
        public int Realm;                          // the realm whose people live here (allies, givers); 0 = by region
        public List<ChainDef> Chains = new();
    }

    public class ChainDef
    {
        public string Id;
        public string Title;
        public int[] Levels;                       // what it is meant for; its monsters scale up to whoever takes part
        public string Hint = "There is a disturbance in this area...";   // the map, while it waits for someone to come
        [JsonProperty("first_delay_s")] public int[] FirstDelayS = { 300, 900 };
        [JsonProperty("interval_s")] public int[] IntervalS = { 1800, 2700 };
        [JsonProperty("rest_s")] public int RestS = 30;                  // between stages: time to sit and recover
        [JsonProperty("wake_m")] public double WakeM;                    // how near wakes it (0: its first stage's radius + 60 m)
        public string Start;
        public GiverDef Giver;                     // set: started by talking to this NPC, not by the timer
        public List<NpcDef> Guards = new();        // the giver's party (with a giver): they follow and fight with them
        public List<StageDef> Stages = new();
        [JsonIgnore] public ZoneEventsDef ZoneDef;
    }

    public class GiverDef : NpcDef
    {
        public string Greet;                       // said on a click; the accept keyword is offered in brackets
        public string Accept = "ready";
        public string Reply;                       // said when they set off
        public string Busy = "Not now - we've only just come back. Find me again a little later.";
        [JsonProperty("cooldown_s")] public int CooldownS = 600;
        public string Thanks;                      // said when the chain is won (default: a word of thanks)
        public string Regret;                      // said when it is lost
    }

    public class StageDef
    {
        public string Id;
        public string Type;                        // cull | defend | boss | escort
        public string Name;
        public string Objective;
        public string Announce;
        public double[] Center;
        public double Radius = 80;
        [JsonProperty("duration_s")] public int DurationS = 180;   // defend: hold this long
        [JsonProperty("time_s")] public int TimeS = 1200;          // cull, boss, escort: the time limit
        public int Kill = 10;                      // cull: how many to defeat
        public int Alive = 6;                      // cull: how many about at once
        public List<MobDef> Mobs = new();          // cull: what to spawn
        public NpcDef Protect;                     // defend: who to keep alive
        [JsonProperty("protect_leader")] public bool ProtectLeader;  // defend: keep the chain's giver alive instead
        public WavesDef Waves;                     // defend: who comes for them
        public NpcDef Boss;                        // boss
        public WavesDef Adds;                      // boss: help it calls
        public List<double[]> Path = new();        // escort: the giver's way, point by point
        public List<AmbushDef> Ambushes = new();   // escort: who waits along it
        public int Flag;                           // defend (protect_leader): the leader plants a banner (item model: 464 Albion, 465 Midgard, 466 Hibernian pennant) at center
        [JsonProperty("flag_name")] public string FlagName;
        public string Thanks;                      // defend: what the one you kept alive says when it's over
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
        public string Guild;                       // the line under the name (default: <the chain's title>)
    }

    public class NpcDef
    {
        public int Template;
        public string Name;
        public int Level;
        public byte Size;
        public ushort Model;
        public string Equipment;
        public string Guild;
        public double[] Pos;
        [JsonProperty("health_mult")] public double HealthMult = 1;
        public int Count = 1;                      // guards: how many of this kind
    }

    public class WavesDef
    {
        [JsonProperty("every_s")] public int EveryS = 30;
        public int Count = 3;
        public List<double[]> From = new();        // defend: where waves come from (boss adds: round the boss)
        public List<MobDef> Mobs = new();
    }

    public class AmbushDef
    {
        public int At;                             // escort: when the giver reaches this point of the path (0 = the first)
        public int Count = 3;
        public string Say;                         // the giver's warning
        public List<MobDef> Mobs = new();
    }

    public class RewardDef
    {
        [JsonProperty("xp_pct")] public double XpPct;            // of the level's experience, at gold
        [JsonProperty("copper_per_level")] public int CopperPerLevel;
        public ItemRewardDef Item;
        public List<ItemRewardDef> Items = new();
    }

    public class ItemRewardDef
    {
        public string Id;                          // the item; at your level when it has level versions (<id>_lNN)
        [JsonProperty("gold_chance")] public int GoldChance;
        [JsonProperty("silver_chance")] public int SilverChance;
    }
}
