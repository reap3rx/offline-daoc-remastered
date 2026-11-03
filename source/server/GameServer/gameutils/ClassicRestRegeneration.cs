namespace DOL.GS
{
    /// <summary>One timing/stance rule for real players and NPC-backed playerbots.
    /// Native property calculators still apply level, buffs, debuffs and server modifiers.</summary>
    public static class ClassicRestRegeneration
    {
        /// <summary>
        /// Out of combat, GW2-style (owner 2026-11-02: "when you're out of combat your resources replenish much quicker"):
        /// a player or bot who hasn't fought for a few seconds gets health and power back in about OUT_OF_COMBAT_FULL_S
        /// seconds whatever their level - a floor under the classic per-tick amount, on the classic interval (6 s, 3 s
        /// sitting) - and endurance in about half that while standing still or walking (not sprinting, not fighting).
        /// In combat the classic numbers stand, so a fight is still a fight.
        /// </summary>
        public const double OUT_OF_COMBAT_FULL_S = 12.0;
        public const double OUT_OF_COMBAT_ENDURANCE_FULL_S = 6.0;

        /// <summary>The out-of-combat floor for one tick of health or power: enough to fill from empty in
        /// OUT_OF_COMBAT_FULL_S at this interval; 0 in combat.</summary>
        public static int OutOfCombatFloor(bool inCombat, int max, int intervalMs) =>
            inCombat || max <= 0 ? 0 : (int) System.Math.Ceiling(max * intervalMs / 1000.0 / OUT_OF_COMBAT_FULL_S);

        /// <summary>The out-of-combat floor for one second of endurance (the endurance tick); 0 in combat or sprinting.</summary>
        public static int OutOfCombatEnduranceFloor(bool inCombat, bool sprinting, int max) =>
            inCombat || sprinting || max <= 0 ? 0 : (int) System.Math.Ceiling(max / OUT_OF_COMBAT_ENDURANCE_FULL_S);

        public static int HealthAndPowerInterval(bool sitting, bool inCombat)
        {
            return (6 - (sitting ? 3 : 0) + (inCombat ? 8 : 0) - (sitting && inCombat ? 1 : 0)) * 1000;
        }

        public static int BaseEndurancePerTick(bool sitting, bool inCombat, bool moving)
        {
            return inCombat || moving ? 0 : sitting ? 4 : 1;
        }
    }
}
