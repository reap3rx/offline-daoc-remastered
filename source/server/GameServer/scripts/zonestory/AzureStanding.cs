using System;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.StoryQuests;

namespace DOL.GS.ZoneStory
{
    /// <summary>
    /// The Order of the Azure goes from neutral to hostile, one player at a time (owner 2026-11-24, Lough Gur: "if you think they
    /// could play some sort of role in the story telling where you'd want them going from neutral to hostile, let me know" -
    /// the plan he took: their recruiter's first quests hunt the Glimmer; his last sends you to the touched folk's camp, where
    /// the order means to burn it with the people inside, and from then on the Azure are hostile to you).
    /// Lough Gur's zone file gives the Azure camp a shared faction (ZoneBuilds: "shared", registered with FactionMgr so each
    /// player's standing loads and saves) at a neutral base; finishing <see cref="TurnQuest"/> sets this player's standing to
    /// the worst there is. In the Bog of Cullen and beyond the Azure are hostile to everyone (their own faction there).
    /// </summary>
    public static class AzureStanding
    {
        public const int FactionId = 9300;
        public const string TurnQuest = "lg_azure_burning";

        /// <summary>Is the Azure camp hostile to this player now? (pure: tested)</summary>
        public static bool Hostile(int aggro) => Faction.StandingForAggro(aggro) == Faction.Standing.AGGRESIVE;

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            StoryQuestManager.Finished += OnQuestFinished;
        }

        static void OnQuestFinished(GamePlayer p, StoryQuest q, string ending)
        {
            try
            {
                if (p == null || q?.Def?.Id != TurnQuest)
                    return;
                Turn(p);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[AzureStanding] " + ex.Message);
            }
        }

        /// <summary>The Azure are this player's enemies from now on.</summary>
        public static void Turn(GamePlayer p)
        {
            Faction azure = FactionMgr.GetFactionByID(FactionId);
            if (azure == null || Hostile(azure.GetAggroLevel(p)))
                return;
            azure.AdjustAggroLevel(p, 200);
            p.Out.SendMessage("The Order of the Azure has marked you. Their crusaders on the south-east road will kill you on sight now.",
                eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }
    }
}
