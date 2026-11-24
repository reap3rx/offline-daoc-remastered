using System;
using System.Linq;

namespace DOL.GS.DynamicEvents
{
    /// <summary>
    /// The cons of event and story monsters (owner 2026-11-22, one footing at every level): an event's monsters take
    /// their con from the zone's rating, and its boss from how many people are there and the rating - "Find a balance
    /// that gives a winnable challenge for whoever is there. So, not faceroll easy if there are a lot, but not
    /// impossible if there aren't." Within a con the boss's health grows a little with each extra person. Story quests
    /// are solo or solo with a companion: their bosses take the zone's rating and the quest's place among the zone's
    /// quests ("In Lough Derg as a peaceful zone, they will probably be blues or yellows depending on the level of the
    /// quest. In a zone like Cursed Forest, they may be reds"), two cons more for a GROUP quest.
    /// </summary>
    public static class EventCons
    {
        /// <summary>An event's or a story's ordinary monsters (cull, waves, adds, an escort's ambush, a garrison).</summary>
        public static sbyte Trash(ZoneRates.Rating r) => r switch
        {
            // (owner 2026-11-22: the "minions" are the zone's lowest con - green in a Peaceful zone, blue in a Wild one,
            // yellow in a Dangerous one, orange in a Deadly one)
            ZoneRates.Rating.Peaceful => MonsterTiers.Green,
            ZoneRates.Rating.Wild => MonsterTiers.Blue,
            ZoneRates.Rating.Dangerous => MonsterTiers.Yellow,
            _ => MonsterTiers.Orange
        };

        /// <summary>A boss's health against an ordinary monster of its con (owner 2026-11-22: a boss or named monster
        /// "should have more health than a regular mob of their con, probably at least 2x ... Zone bosses more than
        /// that"): twice, and a zone's big objective's (a siege's) three times.</summary>
        public const double BossHealth = 2.0, ZoneBossHealth = 3.0;

        // The head count each step up starts at, from the first tier: Peaceful and Wild start at yellow, Dangerous and
        // Deadly at orange (the roadmap's table, 22 Nov).
        static int[] Steps(ZoneRates.Rating r) => r switch
        {
            ZoneRates.Rating.Peaceful => new[] { 1, 2, 4, 6 },     // yellow, orange 2-3, red 4-5, purple 6+
            ZoneRates.Rating.Wild => new[] { 1, 2, 4, 5 },         // yellow, orange 2-3, red 4, purple 5+
            ZoneRates.Rating.Dangerous => new[] { 1, 2, 4 },       // orange, red 2-3, purple 4+
            ZoneRates.Rating.Deadly => new[] { 1, 2, 3 },          // orange, red 2, purple 3+
            _ => new[] { 1, 3 }                                    // (Elite) red, purple 3+
        };

        /// <summary>An event boss for this many people: its con, and its health within that con (1 = the con as it is).</summary>
        public static (sbyte tier, double health) Boss(ZoneRates.Rating r, int people)
        {
            people = Math.Max(1, people);
            int[] at = Steps(r);
            int i = 0;
            while (i + 1 < at.Length && people >= at[i + 1])
                i++;
            sbyte first = r <= ZoneRates.Rating.Wild ? MonsterTiers.Yellow : r >= ZoneRates.Rating.Elite ? MonsterTiers.Red : MonsterTiers.Orange;
            sbyte tier = (sbyte) Math.Min(MonsterTiers.Purple, first + i);
            double health = BossHealth * (1 + 0.15 * (people - at[i]));
            if (r >= ZoneRates.Rating.Dangerous && people >= 6)
                health += 1.0;                                     // ("purple, tougher" past a group's worth)
            return (tier, Math.Min(8.0, health));
        }

        /// <summary>A story quest's boss: the zone's rating, the lower or upper half of the zone's quest levels, and two
        /// cons more when the quest is made for a group.</summary>
        public static sbyte StoryBoss(ZoneRates.Rating r, bool upperHalf, bool group)
        {
            sbyte t = r switch
            {
                ZoneRates.Rating.Peaceful => upperHalf ? MonsterTiers.Yellow : MonsterTiers.Blue,
                ZoneRates.Rating.Wild => upperHalf ? MonsterTiers.Orange : MonsterTiers.Yellow,
                ZoneRates.Rating.Dangerous => MonsterTiers.Orange,
                ZoneRates.Rating.Deadly => upperHalf ? MonsterTiers.Red : MonsterTiers.Orange,
                _ => MonsterTiers.Red                              // (Elite)
            };
            return (sbyte) Math.Min(MonsterTiers.Purple, t + (group ? 2 : 0));
        }

        /// <summary>An event monster as it is made (ChainRuntime.Make): its con. A boss's is provisional until its fight
        /// starts (Lock) - a hunt's beast or an occupation's leader is made before anyone comes.</summary>
        public static void Apply(ChainRuntime chain, EventNpc npc, StageRuntime stage)
        {
            if (npc == null || chain?.Zone == null || npc.Role is not (EventRole.Hostile or EventRole.Boss))
                return;
            ZoneRates.Rating r = ZoneRates.RatingOf(chain.Zone);
            if (npc.Role == EventRole.Hostile)
            {
                sbyte t = chain.Def.HostileTier ?? Trash(r);
                if (stage?.Def != null && stage.Def.HealthMult > 1)
                    t++;                                           // (an elite garrison: a con up, not more health)
                MonsterTiers.SetTier(npc, (sbyte) Math.Min(MonsterTiers.Purple, t));
                return;
            }
            var (tier, health) = BossFor(chain, stage);
            MonsterTiers.SetTier(npc, tier);
            npc.ConHealth = health;
        }

        static (sbyte tier, double health) BossFor(ChainRuntime chain, StageRuntime stage)
        {
            if (chain.Def.BossTier is sbyte story)
            {
                // a story's boss: its own con; a little more health for each extra player along (not a companion)
                int players = stage?.PlayersHere ?? 1;
                return (story, BossHealth * (1 + 0.25 * Math.Max(0, players - 1)));
            }
            int people = stage?.PeopleHere ?? 1;
            if (stage?.Def?.Type == "occupy")
                people = Math.Max(people, 4);                      // (dug in, made before anyone came: a group's fight)
            var b = Boss(ZoneRates.RatingOf(chain.Zone), people);
            if (chain.Def.Manual)
                b.health *= ZoneBossHealth / BossHealth;           // (a siege's warlord: a zone boss)
            return b;
        }

        /// <summary>A boss's con settled as its fight starts, by who is there then (StageRuntime.Tick).</summary>
        public static void Lock(ChainRuntime chain, StageRuntime stage, EventNpc boss)
        {
            if (boss == null || boss.ConLocked || !boss.IsAlive)
                return;
            boss.ConLocked = true;
            var (tier, health) = BossFor(chain, stage);
            double pct = boss.Health / (double) Math.Max(1, boss.MaxHealth);
            if (MonsterTiers.Tier(boss) != tier)
                MonsterTiers.SetTier(boss, tier);
            boss.HealthMult = boss.HealthMult / Math.Max(0.01, boss.ConHealth) * health;
            boss.ConHealth = health;
            boss.Health = (int) Math.Max(1, boss.MaxHealth * pct);
        }
    }
}
