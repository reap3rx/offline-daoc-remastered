using System;
using DOL.Database;
using DOL.Events;

namespace DOL.GS
{
    /// <summary>
    /// The charged shots (ActionCombat's archery; owner 2026-11-20: "No more draggable Rapid Fire or Critical Shot skills
    /// in the spellbook; Critical Shot shows in the abilities tab as a skill they have"). Rapid Fire is the quick shot
    /// now and leaves every class; Critical Shot stays learned (it opens the critical stage of the draw) but as a line of
    /// text, not a button (icon 0: the client's passive abilities).
    /// </summary>
    public static class ArcheryRework
    {
        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                int gone = SkillBase.RemoveAbilityEverywhere(Abilities.RapidFire);
                if (SkillBase.GetDbAbility(Abilities.Critical_Shot) is DbAbility crit)
                {
                    crit.IconID = 0;
                    crit.Description = "Your draw has a critical stage: hold the shot past the full draw (the ring turns gold) and the " +
                        "arrow is a critical shot. Hold on longer and the bow overdraws.";
                }
                Console.WriteLine($"[ArcheryRework] Rapid Fire taken from {gone} specialization rows; Critical Shot a passive");
            }
            catch (Exception ex)
            {
                Console.WriteLine("[ArcheryRework] " + ex);
            }
        }
    }
}
