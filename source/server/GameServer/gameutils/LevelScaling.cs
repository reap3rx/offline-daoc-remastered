using System;
using DOL.AI.Brain;

namespace DOL.GS
{
    /// <summary>
    /// GW2-style scaling down (owner 2026-11-02: "you should still feel powerful, but not just 1-shotting, so every zone
    /// and every event you come across you can still participate and get something"; "very minimal experience and loot
    /// for killing low level mobs while scaled down ... an event gives out its normal experience").
    /// A player (or their pet) fighting a monster more than MARGIN levels below them fights it as if they were only
    /// MARGIN levels above it: their damage to it shrinks, its damage to them grows, both by the level gap. Bots and
    /// realm enemies are untouched. Experience from such a kill is a small fraction (grinding low monsters pays little);
    /// dynamic events pay their own rewards at your level, and their monsters scale up to you anyway.
    /// </summary>
    public static class LevelScaling
    {
        public static bool Enabled = true;
        public const int MARGIN = 5;              // fights up to this many levels down are normal
        const double MIN_OUT = 0.2;               // your damage never drops below a fifth
        const double MAX_IN = 2.5;                // its damage to you never more than 2.5 times
        const double KILL_XP = 0.1;               // a scaled kill's experience: a tenth of what it would have been
        const double GREY_XP_OF_LEVEL = 0.001;    // ...and a grey one (normally nothing) a thousandth of your level

        static GamePlayer PlayerOf(GameLiving l) => l switch
        {
            GamePlayer p => p,
            GameNPC { Brain: IControlledBrain cb } => cb.GetPlayerOwner(),
            _ => null
        };

        /// <summary>A monster that can be scaled against: an ordinary realm-less NPC, not a bot, a pet or a guard.</summary>
        static bool Scalable(GameLiving l) =>
            l is GameNPC npc && npc is not GameBot && npc.Realm == eRealm.None && npc.Brain is not IControlledBrain;

        /// <summary>How many levels the player is scaled down by against this monster (0: not scaled).</summary>
        public static int Gap(GamePlayer player, GameLiving monster)
        {
            if (!Enabled || player == null || monster == null)
                return 0;
            return Math.Max(0, player.Level - (monster.Level + MARGIN));
        }

        /// <summary>Damage factor for an attack (melee or spell): the attacker's, against this target.</summary>
        public static double DamageFactor(GameLiving attacker, GameLiving target)
        {
            if (!Enabled || attacker == null || target == null)
                return 1.0;
            GamePlayer you = PlayerOf(attacker);
            if (you != null && Scalable(target))
            {
                int gap = Gap(you, target);
                return gap <= 0 ? 1.0 : Math.Max(MIN_OUT, Math.Pow((target.Level + MARGIN) / (double) you.Level, 1.2));
            }
            GamePlayer victim = PlayerOf(target);
            if (victim != null && Scalable(attacker))
            {
                int gap = Gap(victim, attacker);
                return gap <= 0 ? 1.0 : Math.Min(MAX_IN, Math.Pow(victim.Level / (double) (attacker.Level + MARGIN), 0.8));
            }
            return 1.0;
        }

        const int DROP_CHANCE = 20;               // a scaled kill keeps each of its drops (items, coin) one time in five

        /// <summary>Whether a drop from this kill stays (scaled down: only now and then; event monsters always).</summary>
        public static bool KeepDrop(GameObject killer, GameNPC killed)
        {
            if (killer is not GameLiving living || killed is DynamicEvents.EventNpc)
                return true;
            GamePlayer you = PlayerOf(living);
            return you == null || Gap(you, killed) <= 0 || Util.Chance(DROP_CHANCE);
        }

        /// <summary>The experience for a kill while scaled down (base already worked out; 0 for a grey one).</summary>
        public static long KillExperience(GamePlayer player, GameNPC killed, long baseXp)
        {
            if (Gap(player, killed) <= 0 || killed is DynamicEvents.EventNpc)
                return baseXp;
            if (baseXp > 0)
                return Math.Max(1, (long) (baseXp * KILL_XP));
            long level = GamePlayer.GetExperienceAmountForLevel(player.Level) - GamePlayer.GetExperienceAmountForLevel(player.Level - 1);
            return player.Level >= 50 ? 0 : Math.Max(1, (long) (level * GREY_XP_OF_LEVEL));
        }
    }
}
