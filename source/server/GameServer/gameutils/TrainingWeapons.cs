using System;
using DOL.Database;

namespace DOL.GS
{
    /// <summary>
    /// The practice weapons new characters and bots start with (owner 2026-11-20: "The training weapons given to new players
    /// and bots need to be buffed in damage some. They do like 1 damage and killing greens at level 1 is impossible without a
    /// group"). They are level 0, 1.2 DPS in the database. Since 2026-11-22 (one footing at every level - owner: "if it
    /// takes 12 auto attack hits for a level 1 to kill a green mob with a blue practice sword, it will take a level 50 12
    /// auto attack hits to kill a green mob with a blue conned practice sword") a training weapon is the baseline itself:
    /// a plain weapon at the level that cons blue to you, whatever your level, with no extra while you are new - the curve
    /// (MonsterTiers.OutCurve) already makes a green the same fight at level 1 as at 50. Its tooltip numbers stay as they were.
    /// </summary>
    public static class TrainingWeapons
    {
        /// <summary>The starter weapons: the database's "training_*" (and their "training ..." names) and the bots' starters.</summary>
        public static bool IsTraining(DbInventoryItem item)
        {
            if (item == null)
                return false;
            string id = item.Id_nb ?? "";
            string name = item.Name ?? "";
            return id.StartsWith("training", StringComparison.OrdinalIgnoreCase) ||
                id.StartsWith("bot_starter", StringComparison.OrdinalIgnoreCase) ||
                name.StartsWith("training ", StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>The DPS of a plain weapon that cons blue to this level (DAoC's 1.2 + 0.3 per item level).</summary>
        public static double BlueDps(int level) =>
            1.2 + 0.3 * Math.Max(0, MonsterTiers.LevelFor(Math.Max(1, level), MonsterTiers.Blue, level));

        /// <summary>A weapon's DPS for the damage formula (before the DPS bonus): capped as ever; a training weapon at the
        /// baseline's blue-conned DPS for your level.</summary>
        public static double Dps(DbInventoryItem weapon, double dpsCap, int level)
        {
            double dps = Math.Min(weapon.DPS_AF * 0.1, dpsCap);
            return IsTraining(weapon) ? Math.Min(dpsCap, BlueDps(level)) : dps;
        }
    }
}
