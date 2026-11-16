using System.Collections.Generic;
using System.Linq;

namespace DOL.GS
{
    /// <summary>
    /// Which two songs or chants a bot runs (owner 2026-11-15: no more twisting - live patch 1.97 lets Bards,
    /// Minstrels, Skalds, Paladins and Wardens run two at once). The bot picks the pair that fits what it is doing and
    /// keeps it: travelling, fighting (a hurt group, casters low on power) or resting. The first two of each list the
    /// bot knows are its pair.
    /// </summary>
    public static class BotSongPairPolicy
    {
        public const int HOLD_MS = 15_000;          // a pair is kept at least this long unless travel / fight / rest changes
        public const int LOW_POWER_START = 40;      // the group's casters average below this power % ...
        public const int LOW_POWER_END = 70;        // ... until they are back above this

        public static List<eSpellType> Pick(eCharacterClass characterClass, bool travel, bool fight, bool hurt,
            bool lowPower, ICollection<eSpellType> have) =>
            Order(characterClass, travel, fight, hurt, lowPower).Where(have.Contains).Distinct().Take(2).ToList();

        /// <summary>travel, fight or rest: a change of these switches the pair at once; anything else waits HOLD_MS.</summary>
        public static string Mode(bool travel, bool fight) => fight ? "fight" : travel ? "travel" : "rest";

        public static IEnumerable<eSpellType> Order(eCharacterClass characterClass, bool travel, bool fight, bool hurt, bool lowPower)
        {
            switch (characterClass)
            {
                case eCharacterClass.Paladin:
                    if (fight)
                    {
                        if (hurt) yield return eSpellType.CombatHeal;
                        yield return eSpellType.DamageAdd;
                        yield return eSpellType.SpecArmorFactorBuff;
                        yield return eSpellType.EnduranceRegenBuff;
                    }
                    else
                    {
                        if (hurt) yield return eSpellType.CombatHeal;
                        yield return eSpellType.EnduranceRegenBuff;
                        yield return eSpellType.SpecArmorFactorBuff;
                        yield return eSpellType.DamageAdd;
                    }
                    yield break;
                case eCharacterClass.Warden:
                    if (travel && !fight) yield return eSpellType.SpeedEnhancement;
                    yield return eSpellType.Bladeturn;
                    yield return eSpellType.DamageAdd;
                    yield break;
            }
            // Bard, Minstrel, Skald
            if (fight)
            {
                if (characterClass == eCharacterClass.Skald) yield return eSpellType.DamageAdd;
                if (hurt) yield return eSpellType.HealthRegenBuff;
                if (lowPower) yield return eSpellType.PowerRegenBuff;
                yield return eSpellType.EnduranceRegenBuff;
                yield return eSpellType.HealthRegenBuff;
                yield return eSpellType.PowerRegenBuff;
                yield return eSpellType.DamageAdd;
            }
            else if (travel || !hurt && !lowPower)           // (standing about with nothing to mend: the travel pair)
            {
                yield return eSpellType.SpeedEnhancement;
                if (lowPower) yield return eSpellType.PowerRegenBuff;
                yield return eSpellType.EnduranceRegenBuff;
                yield return eSpellType.HealthRegenBuff;
                yield return eSpellType.PowerRegenBuff;
            }
            else
            {
                if (lowPower) yield return eSpellType.PowerRegenBuff;
                if (hurt) yield return eSpellType.HealthRegenBuff;
                yield return eSpellType.PowerRegenBuff;
                yield return eSpellType.HealthRegenBuff;
                yield return eSpellType.EnduranceRegenBuff;
            }
        }
    }
}
