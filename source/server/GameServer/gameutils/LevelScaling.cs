using System;
using System.Collections.Generic;
using DOL.AI.Brain;
using DOL.GS.DynamicEvents;

namespace DOL.GS
{
    /// <summary>
    /// GW2-style scaling down (owner 2026-11-02, after the first event tests: "it would be better to have the players
    /// 'scaled down' so events have set level, but any higher level players can still participate"; then: "is there
    /// a way to adjust the player so that when they're downscaled, they're maybe only +2 or +3 effective levels no
    /// matter where they go? Kind of how GW2 does it, where you feel stronger and maybe the content is easy, but not
    /// trivial").
    ///
    /// Against any ordinary monster, a player (or their pet; at an event, a bot too) above the monster's level + MARGIN
    /// fights as if they were that level: their damage to it shrinks and its damage to them grows, by the ratio of
    /// their level to the cap - steeply enough that a level 50 among level 22s wins easily but not in a blow. Lower
    /// players are not lifted (as in GW2). The cap is per monster, so it follows the monster wherever you go.
    /// Kills while scaled down pay a tenth of their experience; drops are the monster's own (the area's level) and
    /// come as if you were the capped level - no grey-con nothing; an event's monsters and its rewards pay in full
    /// (rewards at your real level).
    ///
    /// Event allies (a giver and their guards) support, they don't carry: half damage to the event's monsters, half
    /// damage taken from them, so they last long enough for you to see they're in trouble (owner: "ensure they do not
    /// die quickly").
    /// </summary>
    public static class LevelScaling
    {
        public static bool Enabled = true;
        const int MARGIN = 3;                     // you fight as the monster's level + this, at most
        const double OUT_EXP = 2.0;               // damage out: (cap / level) ^ this (a level 50 among 22s: a quarter)
        const double IN_EXP = 1.5;                // damage in: (level / cap) ^ this (the same: 2.8 times)
        const double MIN_OUT = 0.1;               // your damage never drops below a tenth
        const double MAX_IN = 4.0;                // its damage to you never more than four times
        const double KILL_XP = 0.1;               // a scaled kill's experience: a tenth of what it would have been
        const double GREY_XP_OF_LEVEL = 0.001;    // ...and a grey one (normally nothing) a thousandth of your level
        const double ALLY_OUT = 0.5;              // event allies' damage to the event's monsters
        const double ALLY_IN = 0.5;               // and the monsters' damage to them

        /// <summary>The one whose level counts for an attack: a player, a player's pet - and at an event, a bot.</summary>
        static GameLiving Fighter(GameLiving l, bool atEvent) => l switch
        {
            GamePlayer p => p,
            GameBot b when atEvent => b,
            GameNPC { Brain: IControlledBrain cb } => cb.GetLivingOwner() is GameLiving o && (o is GamePlayer || (atEvent && o is GameBot)) ? o : null,
            _ => null
        };

        /// <summary>A monster that can be scaled against: an ordinary realm-less NPC, not a bot, a pet or a guard.</summary>
        static bool Scalable(GameLiving l) =>
            l is GameNPC npc && npc is not GameBot && npc.Realm == eRealm.None && npc.Brain is not IControlledBrain;

        static bool IsEventFoe(GameLiving l) => l is EventNpc { IsEnemy: true, Chain: not null };

        /// <summary>The level you fight this monster at, at most: its own level + MARGIN (an event's monsters: at least
        /// the event's top level + 1, so its waves and boss feel of a piece).</summary>
        public static int Cap(GameLiving monster)
        {
            int cap = monster.Level + MARGIN;
            if (monster is EventNpc { Chain: not null } ev && ev.Chain.Def.Levels is { Length: > 0 } lv)
                cap = Math.Max(cap, lv[^1] + 1);
            return cap;
        }

        /// <summary>The level this fighter counts as against the monster (its own when not scaled).</summary>
        public static int EffectiveLevelAgainst(GameLiving fighter, GameLiving monster) =>
            fighter == null ? 0 : fighter.Level - Gap(fighter, monster);

        /// <summary>How many levels this fighter is scaled down by against the monster (0: not scaled).</summary>
        public static int Gap(GameLiving fighter, GameLiving monster)
        {
            if (!Enabled || fighter == null || monster == null || !Scalable(monster))
                return 0;
            return Math.Max(0, fighter.Level - Cap(monster));
        }

        /// <summary>Damage factor for an attack (melee or spell): the attacker's, against this target.</summary>
        public static double DamageFactor(GameLiving attacker, GameLiving target)
        {
            if (!Enabled || attacker == null || target == null)
                return 1.0;
            // an event's allies and its monsters
            if (attacker is EventNpc { IsEnemy: false, Role: EventRole.Ally or EventRole.Giver } && IsEventFoe(target))
                return ALLY_OUT;
            if (target is EventNpc { IsEnemy: false, Role: EventRole.Ally or EventRole.Giver } && IsEventFoe(attacker))
                return ALLY_IN;
            GameLiving you = Fighter(attacker, IsEventFoe(target));
            if (you != null)
            {
                int gap = Gap(you, target);
                return gap <= 0 ? 1.0 : Math.Max(MIN_OUT, Math.Pow((you.Level - gap) / (double) you.Level, OUT_EXP));
            }
            GameLiving victim = Fighter(target, IsEventFoe(attacker));
            if (victim != null)
            {
                int gap = Gap(victim, attacker);
                return gap <= 0 ? 1.0 : Math.Min(MAX_IN, Math.Pow(victim.Level / (double) Math.Max(1, victim.Level - gap), IN_EXP));
            }
            return 1.0;
        }

        /// <summary>The experience for a kill while scaled down (base already worked out; 0 for a grey one).</summary>
        public static long KillExperience(GamePlayer player, GameNPC killed, long baseXp)
        {
            if (killed is EventNpc || Gap(player, killed) <= 0)
                return baseXp;
            if (baseXp > 0)
                return Math.Max(1, (long) (baseXp * KILL_XP));
            long level = GamePlayer.GetExperienceAmountForLevel(player.Level) - GamePlayer.GetExperienceAmountForLevel(player.Level - 1);
            return player.Level >= 50 ? 0 : Math.Max(1, (long) (level * GREY_XP_OF_LEVEL));
        }

        /// <summary>Whether a drop from this kill stays: always - scaled down you get the area's drops like anyone
        /// there (owner 2026-11-02: the GW2 way; the drops are the monster's level, not yours).</summary>
        public static bool KeepDrop(GameObject killer, GameNPC killed) => true;

        /// <summary>The con of a monster to its killer for loot (ROG drop chances): by the killer's scaled level, so a
        /// level 50 scaled to 25 among level 22s isn't "grey" and dropless.</summary>
        public static int LootCon(GameLiving killer, GameNPC killed)
        {
            if (killer == null || killed == null)
                return 0;
            GameLiving you = Fighter(killer, IsEventFoe(killed)) ?? killer;
            int level = EffectiveLevelAgainst(you, killed);
            return ConLevels.GetConLevel(level > 0 ? level : killer.EffectiveLevel, killed.EffectiveLevel);
        }

        // ---------------------------------------------------------------- a zone's top monster level

        static readonly Dictionary<int, (int top, long until)> _zoneTop = new();
        static readonly object _lock = new();

        /// <summary>The zone's top ordinary monster level: of its realm-less monsters (not named ones, bots, pets or
        /// events' monsters), the level 95% of them are at or under - one odd giant doesn't lift a whole zone. Looked up
        /// again every ten minutes; 50 when nothing is known.</summary>
        public static int ZoneTop(Zone zone, Region region)
        {
            if (zone == null || region == null)
                return 50;
            long now = Environment.TickCount64;
            lock (_lock)
                if (_zoneTop.TryGetValue(zone.ID, out var c) && now < c.until)
                    return c.top;
            var levels = new List<int>();
            GameObject[] all = region.Objects;
            if (all != null)
                foreach (GameObject o in all)
                    if (o is GameNPC n && n is not GameBot && n is not EventNpc && n.Realm == eRealm.None &&
                        n.Brain is not IControlledBrain && n.CurrentZone == zone && n.Level > 0 &&
                        !string.IsNullOrEmpty(n.Name) && char.IsLower(n.Name[0]))
                        levels.Add(n.Level);
            int top = 50;
            if (levels.Count > 0)
            {
                levels.Sort();
                top = levels[Math.Min(levels.Count - 1, (int) (levels.Count * 0.95))];
            }
            lock (_lock)
                _zoneTop[zone.ID] = (top, now + 600_000);
            return top;
        }
    }
}
