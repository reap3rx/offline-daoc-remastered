using System;
using System.Collections.Generic;
using DOL.AI.Brain;
using DOL.GS.DynamicEvents;

namespace DOL.GS
{
    /// <summary>
    /// GW2-style scaling down (owner 2026-11-02, after the first event tests: "it would be better to have the players
    /// 'scaled down' so events have set level, but any higher level players can still participate"; the design he chose:
    /// events keep their own level and grow only with how many people come; anyone above an event's top level fights
    /// it as if they were that level + 1; the same in the open world, by the zone's top monster level).
    ///
    /// A player (or their pet) above the cap fights as if at the cap: their damage to the monster shrinks and its damage
    /// to them grows, by the ratio of their level to the cap. Lower players are not lifted (as in GW2). The cap:
    /// - an event's monster: the event's top level + 1 (bots helping at an event are scaled the same way);
    /// - anything else realm-less in a zone: the zone's top ordinary monster level + 1.
    /// Kills while scaled down in the open world pay a tenth of their experience and keep one drop in five; an event's
    /// monsters and its rewards pay in full (rewards at your real level).
    ///
    /// Event allies (a giver and their guards) support, they don't carry: half damage to the event's monsters, half
    /// damage taken from them, so they last long enough for you to see they're in trouble (owner: "ensure they do not
    /// die quickly").
    /// </summary>
    public static class LevelScaling
    {
        public static bool Enabled = true;
        const double MIN_OUT = 0.2;               // your damage never drops below a fifth
        const double MAX_IN = 2.5;                // its damage to you never more than 2.5 times
        const double KILL_XP = 0.1;               // a scaled kill's experience: a tenth of what it would have been
        const double GREY_XP_OF_LEVEL = 0.001;    // ...and a grey one (normally nothing) a thousandth of your level
        const int DROP_CHANCE = 20;               // a scaled kill keeps each of its drops one time in five
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

        /// <summary>The level you fight this monster at, at most.</summary>
        public static int Cap(GameLiving monster)
        {
            if (monster is EventNpc { Chain: not null } ev && ev.Chain.Def.Levels is { Length: > 0 } lv)
                return lv[^1] + 1;
            return ZoneTop(monster.CurrentZone, monster.CurrentRegion) + 1;
        }

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
                return gap <= 0 ? 1.0 : Math.Max(MIN_OUT, Math.Pow((you.Level - gap) / (double) you.Level, 1.2));
            }
            GameLiving victim = Fighter(target, IsEventFoe(attacker));
            if (victim != null)
            {
                int gap = Gap(victim, attacker);
                return gap <= 0 ? 1.0 : Math.Min(MAX_IN, Math.Pow(victim.Level / (double) Math.Max(1, victim.Level - gap), 0.8));
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

        /// <summary>Whether a drop from this kill stays (scaled down: only now and then; event monsters always).</summary>
        public static bool KeepDrop(GameObject killer, GameNPC killed)
        {
            if (killer is not GameLiving living || killed is EventNpc)
                return true;
            GameLiving you = Fighter(living, false);
            return you == null || Gap(you, killed) <= 0 || Util.Chance(DROP_CHANCE);
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
