using System;

namespace DOL.GS
{
    /// <summary>
    /// Loot follows you, and a harder monster pays better (owner 2026-11-20 bugs doc: "with the level rework, loot that
    /// drops for you should be at level no matter where you get it, not based on zone. Includes chests, monster drops,
    /// etc." and "Higher con mobs should have higher chance to drop better gear/items/more gold etc. Risk vs Reward."):
    ///   Level: a tiered monster's drops (items, coin, trophies) are made at the level its fight was set for - yours, or
    ///     your group's highest nearby (MonsterTiers.EngageLevel) - not the level it was placed at. A purple no longer
    ///     drops above you and a monster in a low zone no longer drops below you. Greys keep their own (lower) level.
    ///     Treasure chests: TreasureChests.LevelFor.
    ///   Con: each con above yellow rolls a random drop's quality tier once more and keeps the best (orange best of two,
    ///     red of three, purple of four); unique-drop chances already rise with con (LootGeneratorUniqueItem); coin is
    ///     multiplied by CoinFactor.
    /// </summary>
    public static class LootByCon
    {
        /// <summary>The level a monster's drops are made at.</summary>
        public static byte Level(GameNPC mob)
        {
            sbyte t = MonsterTiers.Tier(mob);
            if (t == MonsterTiers.None || t == MonsterTiers.Grey || mob.TierFightBase <= 0)
                return mob.Level;
            return (byte) Math.Clamp(mob.TierFightBase, 1, 50);
        }

        /// <summary>The monster's con for loot: -3 grey .. 3 purple (0 when it has no tier).</summary>
        public static int Con(GameNPC mob)
        {
            sbyte t = mob == null ? MonsterTiers.None : MonsterTiers.Tier(mob);
            return t == MonsterTiers.None ? 0 : t;
        }

        /// <summary>Extra quality rolls (best kept) for a con.</summary>
        public static int ExtraRolls(int con) => Math.Max(0, con);

        /// <summary>Coin against a yellow's.</summary>
        public static double CoinFactor(int con) => con switch
        {
            <= -3 => 0.5, -2 => 0.7, -1 => 0.85, 0 => 1.0, 1 => 1.35, 2 => 1.8, _ => 2.5
        };
    }
}
