using System;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Quests;

namespace DOL.GS.StoryQuests
{
    /// <summary>
    /// One player's story quest (StoryQuestManager runs them all). Every story quest is this type; its id, step, count
    /// and the things it gave you are the DbQuest's custom properties (q, s, n, items, choice). A RewardQuest so the
    /// journal shows its goal line (QuestEntry's goals) - its offer and reward windows aren't used: the NPCs talk.
    /// </summary>
    public class StoryQuest : RewardQuest
    {
        public StoryQuestDef Def { get; private set; }
        public string QuestId => GetCustomProperty("q") ?? "";
        public string StepId => GetCustomProperty("s") ?? "";
        public int Count => int.TryParse(GetCustomProperty("n"), out int n) ? n : 0;
        /// <summary>The ending it is waiting on while you pick your reward ("" when not).</summary>
        public string Choosing => GetCustomProperty("choose") ?? "";

        public StoryQuest(GamePlayer player, DbQuest db) : base(player, db)
        {
            Def = StoryQuestManager.Quest(QuestId);
            Level = Def?.Level ?? 1;
        }

        public StoryQuest(GamePlayer player, StoryQuestDef def) : base(player, 1)
        {
            Def = def;
            Level = Math.Clamp(def.Level, 1, 50);
            SetCustomProperty("q", def.Id);
            SetCustomProperty("s", def.Steps.Count > 0 ? def.Steps[0].Id : "");
            SetCustomProperty("n", "0");
            SaveIntoDatabase();
            RebuildGoals();
        }

        public StepDef Step_ => Def?.Steps.FirstOrDefault(s => s.Id == StepId);

        public override bool SameQuest(AbstractQuest other) => other is StoryQuest s && s.QuestId == QuestId;

        public override string Name => Def == null ? "A forgotten tale" :
            (Def.Kind == "epic" ? "Epic: " : "") + Def.Title + (Def.Group ? " [GROUP]" : "");

        public override string Description
        {
            get
            {
                if (Def == null)
                    return "This story is no longer told. Abandon it from the journal.";
                string carry = Items.Count > 0 ? " You carry: " + string.Join(", ", Items) + "." : "";
                string d = (Def.Summary ?? "") + carry;
                return d.Length > 250 ? d[..250] : d;
            }
        }

        public override string Story => Def?.Offer ?? "";
        public override string Summary => Def?.Summary ?? "";
        public override string Conclusion => "";

        public override bool CheckQuestQualification(GamePlayer player) => Def != null && StoryQuestManager.CanTake(player, Def);

        public override void Notify(DOLEvent e, object sender, EventArgs args) { }

        public override void OnQuestAssigned(GamePlayer player)
        {
            player.Out.SendMessage($"You have begun {Name}.", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
            player.Out.SendSoundEffect(7, 0, 0, 0, 0, 0);
        }

        // ---------------------------------------------------------------- the quest items it hands you (no inventory)

        public List<string> Items => (GetCustomProperty("items") ?? "").Split('|', StringSplitOptions.RemoveEmptyEntries).ToList();

        public void GiveStoryItem(string name)
        {
            var l = Items;
            if (!l.Contains(name))
                l.Add(name);
            SetCustomProperty("items", string.Join("|", l));
        }

        public void TakeStoryItem(string name)
        {
            var l = Items;
            l.RemoveAll(x => string.Equals(x, name, StringComparison.OrdinalIgnoreCase));
            SetCustomProperty("items", string.Join("|", l));
        }

        // ---------------------------------------------------------------- moving on

        public void SetStep(string id, int count = 0)
        {
            SetCustomProperty("s", id);
            SetCustomProperty("n", count.ToString());
            SaveIntoDatabase();
            RebuildGoals();
            QuestPlayer.Out.SendQuestUpdate(this);
        }

        public void SetCount(int n)
        {
            SetCustomProperty("n", n.ToString());
            SaveIntoDatabase();
            RebuildGoals();
            QuestPlayer.Out.SendQuestUpdate(this);
        }

        public void SetChoosing(string ending)
        {
            SetCustomProperty("choose", ending ?? "");
            SaveIntoDatabase();
        }

        /// <summary>The journal's goal line: the current step's, with its count.</summary>
        public void RebuildGoals()
        {
            Goals.Clear();
            StepDef st = Step_;
            if (st == null)
                return;
            string g = st.Goal ?? "";
            if (st.Type == "kill" && st.Count > 1)
                g += $" ({Math.Min(Count, st.Count)}/{st.Count})";
            if (!string.IsNullOrEmpty(Choosing))
                g = "Choose your reward.";
            var goal = new QuestGoal("step", this, g, QuestGoal.GoalType.ScoutMission, 1, 1, null);
            Goals.Add(goal);
        }

        /// <summary>Done: the rewards (StoryQuestManager.Reward), then off the list and into the finished one.</summary>
        public void Complete(string ending, string chosen)
        {
            StoryQuestManager.Reward(QuestPlayer, this, ending, chosen);
            SetCustomProperty("e", ending ?? "default");
            SetCustomProperty("choose", "");
            Step = -2;
            if (QuestPlayer.QuestList.TryRemove(this, out byte index))
                QuestPlayer.AvailableQuestIndexes.Enqueue(index);
            QuestPlayer.AddFinishedQuest(this);
            QuestPlayer.Out.SendQuestRemove(index);
            QuestPlayer.Out.SendSoundEffect(11, 0, 0, 0, 0, 0);
            SaveIntoDatabase();
            QuestPlayer.SaveIntoDatabase();
        }

        public override void FinishQuest() => Complete("default", null);

        public string EndingTaken => GetCustomProperty("e") ?? "";
    }
}
