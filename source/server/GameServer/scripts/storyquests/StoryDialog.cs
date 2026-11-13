using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using DOL.Database;
using DOL.GS.DynamicEvents;
using DOL.GS.PacketHandler;
using DOL.GS.PacketHandler.Client.v168;
using Newtonsoft.Json;

namespace DOL.GS.StoryQuests
{
    /// <summary>
    /// The story quests' people talking to the new client (owner 2026-11-06: "a much more readable dialogue UI ... tied
    /// into making a quest window (kind of like WoW) where you can see the quest lore and possible rewards ... More use of
    /// the chat bubbles"). What a story NPC says goes to the new client as "#DLG|{json}" (NewClient's channel): the
    /// dialogue window shows the words with each [keyword] as a button, and for a quest offer the quest window's parts -
    /// its title, level, GROUP, what it asks, and every reward it can give (items with their bonuses and lore); for a
    /// reward choice, the items to pick from. The first sentence also floats over the speaker's head (NpcSpeech).
    /// "#QLOG|{json}" tells the journal a story quest's lore and rewards. The [keyword] answer stays a whisper.
    /// </summary>
    public static class StoryDialog
    {
        public const string Prefix = "#DLG|";
        public const string LogPrefix = "#QLOG|";

        static readonly Regex Brackets = new(@"\[([^\]]+)\]");

        /// <param name="kind">talk / offer / choice / reward / end / idle</param>
        public static void Say(GamePlayer p, GameNPC npc, string text, string kind = "talk", StoryQuestDef q = null,
            StoryQuest s = null, string ending = null, bool bubble = true)
        {
            if (p == null || npc == null || string.IsNullOrEmpty(text))
                return;
            if (!NewClient.Is(p))
            {
                npc.SayTo(p, text);
                return;
            }
            npc.TurnTo(p, 10000);
            var options = new List<object>();
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (Match m in Brackets.Matches(text))
            {
                string kw = m.Groups[1].Value;
                string role = "ask";
                if (q != null && kind == "offer" && Same(kw, q.Accept))
                    role = "accept";
                else if (kind == "choice")
                    role = "choice";
                else if (kind == "reward")
                    role = "reward";
                else if (s?.Step_ is StepDef st && st.Type == "talk" && Same(st.Keyword, kw))
                    role = "next";
                if (seen.Add(kw))
                    options.Add(new { kw, role });
            }
            StoryQuestDef def = q ?? s?.Def;
            var msg = new Dictionary<string, object>
            {
                ["oid"] = npc.ObjectID,
                ["name"] = npc.Name,
                ["kind"] = kind,
                ["text"] = text,
                ["options"] = options,
            };
            if (def != null)
                msg["quest"] = new { id = def.Id, title = def.Title, level = def.Level, group = def.Group, summary = def.Summary,
                    goal = s?.Step_?.Goal };
            if (kind == "offer" && def != null)
                msg["rewards"] = Rewards(p, def, null);
            if (kind == "reward" && s != null)
                msg["rewards"] = Rewards(p, def, ending, choiceOnly: true);
            if (kind == "end" && s != null && def != null && ending != null && def.Endings.TryGetValue(ending, out EndingDef e))
                msg["tragic"] = e.Tragic;
            NewClient.Send(p, Prefix + JsonConvert.SerializeObject(msg));
            if (bubble)
                NpcSpeech.SayTo(npc, p, Bubble(text));
        }

        /// <summary>The words' first sentence or two, without the brackets: what floats over the speaker's head.</summary>
        public static string Bubble(string text)
        {
            string t = Brackets.Replace(text ?? "", "$1").Replace('\n', ' ').Trim();
            while (t.Contains("  "))
                t = t.Replace("  ", " ");
            if (t.Length <= 110)
                return t;
            int cut = -1;
            foreach (char c in ".!?")
            {
                int i = t.IndexOf(c, 30);
                if (i > 0 && i < 140 && (cut < 0 || i < cut))
                    cut = i;
            }
            return cut > 0 ? t[..(cut + 1)] : t[..107].TrimEnd() + "...";
        }

        /// <summary>A quest's rewards as the quest window shows them: per ending (or the one named), at your level.</summary>
        public static object Rewards(GamePlayer p, StoryQuestDef q, string onlyEnding, bool choiceOnly = false)
        {
            var endings = new List<(string key, RewardsDef r, EndingDef e)>();
            foreach (var (k, e) in q.Endings)
                if (onlyEnding == null || Same(k, onlyEnding))
                    endings.Add((k, e.Rewards ?? q.Rewards, e));
            if (endings.Count == 0 && q.Rewards != null)
                endings.Add(("default", q.Rewards, null));
            int lvl = p.Level;
            var fixedIds = new List<string>();
            var choiceIds = new List<string>();
            foreach (var (_, r, _) in endings)
            {
                if (r == null)
                    continue;
                if (!choiceOnly)
                    foreach (string id in r.Items)
                        if (!fixedIds.Contains(id))
                            fixedIds.Add(id);
                foreach (string id in r.Choice)
                    if (!choiceIds.Contains(id))
                        choiceIds.Add(id);
            }
            RewardsDef first = endings.Select(x => x.r).FirstOrDefault(r => r != null);
            int at = Math.Min(lvl, q.Level + 2);
            long levelXp = at < 50 ? GamePlayer.GetExperienceAmountForLevel(at) - GamePlayer.GetExperienceAmountForLevel(at - 1) : 0;
            return new
            {
                xp_pct = first?.XpPct ?? 0,
                xp = lvl < 50 && first != null ? (long) (Math.Max(0, levelXp) * first.XpPct / 100.0) : 0,
                copper = first != null ? (long) first.CopperPerLevel * lvl : 0,
                marks = first?.Marks ?? 0,
                endings = endings.Count,
                items = fixedIds.Select(id => Item(p, id)).Where(x => x != null).ToList(),
                choice = choiceIds.Select(id => Item(p, id)).Where(x => x != null).ToList(),
            };
        }

        static readonly Dictionary<int, string> Slots = new()
        {
            [24] = "Jewel", [26] = "Cloak", [29] = "Necklace", [32] = "Belt", [33] = "Bracer", [35] = "Ring", [21] = "Head",
            [22] = "Hands", [23] = "Feet", [25] = "Torso", [27] = "Legs", [28] = "Arms",
        };

        static object Item(GamePlayer p, string id)
        {
            if (StageRuntime.ItemAtLevel(id, p.Level) is not DbItemTemplate t)
                return null;
            var lines = new List<string>();
            try
            {
                new DetailDisplayHandler().WriteMagicalBonuses(lines, t, p.Client, false);
            }
            catch (Exception)
            {
            }
            lines = lines.Where(l => !string.IsNullOrWhiteSpace(l) && !l.Contains("Magical Bonuses", StringComparison.OrdinalIgnoreCase)).ToList();
            return new
            {
                id = t.Id_nb,
                name = t.Name,
                level = t.Level,
                model = t.Model,
                slot = Slots.TryGetValue(t.Item_Type, out string sl) ? sl : "",
                lines,
                lore = t.Description ?? "",
            };
        }

        /// <summary>The journal's page for a story quest: its lore and what it can give.</summary>
        public static void Log(GamePlayer p, StoryQuest s)
        {
            if (!NewClient.Is(p) || s?.Def == null)
                return;
            StoryQuestDef q = s.Def;
            NewClient.Send(p, LogPrefix + JsonConvert.SerializeObject(new
            {
                title = s.Name, id = q.Id, level = q.Level, group = q.Group, summary = q.Summary,
                lore = Brackets.Replace(q.Offer ?? "", "$1"), goal = s.Step_?.Goal ?? "", rewards = Rewards(p, q, null),
            }));
        }

        static bool Same(string a, string b) => string.Equals(a, b, StringComparison.OrdinalIgnoreCase);
    }
}
