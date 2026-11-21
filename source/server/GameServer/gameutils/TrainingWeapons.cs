using System;
using DOL.Database;

namespace DOL.GS
{
    /// <summary>
    /// The practice weapons new characters and bots start with (owner 2026-11-20: "The training weapons given to new players
    /// and bots need to be buffed in damage some. They do like 1 damage and killing greens at level 1 is impossible without a
    /// group"). They are level 0, 1.2 DPS - under even a level-1 weapon's cap. A training weapon now counts as a weapon at
    /// your level's DPS cap, and hits harder still while you are new: twice as hard at level 1, fading to no extra by
    /// level 15 (by then you have found or bought a real weapon). Its tooltip numbers stay as they were.
    /// </summary>
    public static class TrainingWeapons
    {
        public const double StartBonus = 2.0;
        public const int FadeByLevel = 15;

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

        /// <summary>The extra a training weapon hits for at this level: StartBonus at level 1, 1.0 from FadeByLevel.</summary>
        public static double Bonus(int level)
        {
            if (level >= FadeByLevel)
                return 1.0;
            double t = Math.Clamp((level - 1) / (double) (FadeByLevel - 1), 0, 1);
            return StartBonus + (1.0 - StartBonus) * t;
        }

        /// <summary>A weapon's DPS for the damage formula (before the DPS bonus): capped as ever; a training weapon at the cap
        /// and its new-character bonus on top.</summary>
        public static double Dps(DbInventoryItem weapon, double dpsCap, int level)
        {
            double dps = Math.Min(weapon.DPS_AF * 0.1, dpsCap);
            return IsTraining(weapon) ? dpsCap * Bonus(level) : dps;
        }
    }
}
