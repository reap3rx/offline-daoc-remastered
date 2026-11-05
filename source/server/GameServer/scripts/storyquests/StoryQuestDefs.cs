using System.Collections.Generic;
using DOL.GS.DynamicEvents;
using Newtonsoft.Json;

namespace DOL.GS.StoryQuests
{
    // Story quests (owner 2026-11-05: "more quests ... engaging gameplay and story wise, that you can find in towns and
    // throughout the corners of every realm (to encourage exploration) ... quality of quests over quantity"). A file of
    // them is data, like the dynamic events: scripts/storyquests/quests/*.json (built into the server) or
    // runtime\server\story-quests\*.json (read at start-up; replaces a built-in file of the same name). Places are zone
    // metres as the new client's map shows them ([x, y] or [x, y, z]; 1 m = 40 units), each with its zone. See README.md.

    public class StoryFileDef
    {
        public string Name;
        public List<StoryNpcDef> Npcs = new();
        public List<StoryQuestDef> Quests = new();
    }

    /// <summary>Someone a quest needs: always there (a giver, a townsman) or only while someone is on one of the steps
    /// named in <see cref="During"/> (a ghost, a captive, a body).</summary>
    public class StoryNpcDef : NpcDef
    {
        public string Id;
        public int Zone;
        public int Realm;                              // 1-3 (0: the zone's realm); a hostile one is set by Hostile
        public bool Hostile;                           // a monster (it can be a kill step's target)
        public string Idle;                            // said on a click when it has nothing for you
        public List<string> During = new();            // "<quest>/<step>": there only then (empty: always)
        [JsonProperty("brain")] public string Brain;   // "peace" (default for friendly), "wander"
    }

    public class StoryQuestDef
    {
        public string Id;
        public string Title;
        public int Level = 1;                          // what it is meant for (the journal shows it)
        [JsonProperty("min_level")] public int MinLevel;   // can be taken from (default: Level - 3)
        public bool Group;                             // tuned for a group: GROUP in the log, and the giver says so
        public string Kind = "story";                  // "story" / "epic"
        public string Requires;                        // another quest's id that must be done first
        public List<int> Classes = new();              // only these classes (empty: anyone)
        public int Realm;                              // only this realm (0: the giver's)
        public string Giver;                           // the NPC id who offers it
        public string Offer;                           // what they say, with [keywords]; Accept is the one that takes it
        public string Accept = "help";
        public string Decline;                         // said for any other bracketed word in Offer that isn't a topic
        public Dictionary<string, string> Topics = new();  // other [keywords] in Offer: what they answer
        public string Summary;                         // the journal's line under the name
        public List<StepDef> Steps = new();
        public Dictionary<string, EndingDef> Endings = new();
        public RewardsDef Rewards;                     // the default ending's rewards
        [JsonIgnore] public StoryFileDef File;
    }

    public class StepDef
    {
        public string Id;
        public string Type;                            // talk | reach | search | kill | encounter | choice
        public string Goal;                            // the journal's goal line
        public int Zone;                               // where (with At): the map marker
        public double[] At;
        public double Radius = 15;                     // reach / search / kill spawns: metres
        public string Npc;                             // talk / choice: who
        public string Say;                             // talk / choice: what they say ([keywords] ok)
        public string Keyword;                         // talk: the [word] that moves on (empty: the click does)
        public string Text;                            // reach / search / kill / encounter done: what you find / see
        public ClueDef Clue;                           // search: the thing to click
        public QuestItemDef Give;                      // an item handed to you as the step ends (a letter, a locket)
        public string Take;                            // an item taken from you as the step ends (by its name)
        public NpcDef Mob;                             // kill: who (spawned for you near At)
        public string Target;                          // kill: or monsters of this name already there
        public int Count = 1;                          // kill: how many
        public List<StageDef> Stages = new();          // encounter: a dynamic-event chain of your own (boss, defend ...)
        public string Start;                           // encounter: its first stage (default the first)
        [JsonProperty("wake_m")] public double WakeM = 40; // encounter: how near starts it
        public List<OptionDef> Options = new();        // choice: the answers
        public string Next;                            // the step after this one (default: the next in the list)
        public string Ending;                          // this step ends the quest (an Endings key, or "default")
    }

    public class ClueDef
    {
        public string Name;
        public ushort Model;
    }

    public class QuestItemDef
    {
        public string Name;
        public ushort Model = 488;                     // (a scroll)
        public string Id;                              // an ItemTemplate instead of a made-up quest item
    }

    public class OptionDef
    {
        public string Keyword;
        public string Say;                             // their answer
        public string Next;                            // the step it leads to
        public string Ending;                          // or the ending it gives
    }

    public class EndingDef
    {
        public string Text;                            // said / shown at the end
        public RewardsDef Rewards;                     // (default: the quest's)
        public bool Tragic;                            // the journal says so
    }

    public class RewardsDef
    {
        [JsonProperty("xp_pct")] public double XpPct;          // of a level's experience at your level
        [JsonProperty("copper_per_level")] public int CopperPerLevel;
        public int Marks;                              // Marks of Valor
        public List<string> Items = new();             // item ids (their level version for you, when they have them)
        public List<string> Choice = new();            // pick one of these (by [name] at the end)
        public string Title;                           // a title earned
    }
}
