using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using DOL.AI.Brain;
using DOL.GS.DynamicEvents;

namespace DOL.GS
{
    /// <summary>
    /// Zone bounties for the PvE overhaul (owner 2026-11-21: "There can be a bounty master in each zone's main
    /// settlement that gives out bounties for that zone, considering the player's level. They can offer a bounty meant
    /// for a solo player, a small group, or a big group, and that can determine what the bounty points at (like killing
    /// higher con mobs as a group)").
    ///
    /// Monsters scale to whoever fights them (MonsterTiers), so a bounty points at a con tier in the master's own zone,
    /// not a level: solo hunts take greens, blues or a few yellows; a small group takes yellows in number or the
    /// oranges; a large group takes a red camp boss or a purple. The pay is worked out at the player's level when it is
    /// claimed, so a bounty can never be outleveled. The size is saved in the old "difficulty" slot (0, 1, 2).
    /// </summary>
    public static class ZoneBounties
    {
        public const string Scope = "zone";

        /// <summary>What the master calls each size.</summary>
        public static string SizeName(BountyDifficulty size) => size switch
        {
            BountyDifficulty.Hard => "Small Group",
            BountyDifficulty.VeryHard => "Large Group",
            _ => "Solo"
        };

        public static string SizeWho(BountyDifficulty size) => size switch
        {
            BountyDifficulty.Hard => "two to four",
            BountyDifficulty.VeryHard => "a full group",
            _ => "one"
        };

        /// <summary>Dialogue words for a size ("solo", "small group", "large group", "big group"), or the old ones.</summary>
        public static bool TryParseSize(string text, out BountyDifficulty size)
        {
            switch (text?.Trim().ToLowerInvariant())
            {
                case "solo":
                    size = BountyDifficulty.Normal;
                    return true;
                case "small group":
                case "group":
                    size = BountyDifficulty.Hard;
                    return true;
                case "large group":
                case "big group":
                    size = BountyDifficulty.VeryHard;
                    return true;
                default:
                    return BountyDifficultyRules.TryParseChoice(text, out size);
            }
        }

        /// <summary>The kills a hunt needs: a solo hunt 8 greens, 6 blues or 3 yellows; a small group 8 yellows or two
        /// oranges; a large group one red or purple (or, where a zone has none, four oranges). Never more than three
        /// times the monsters that stand in the zone, so a thin type doesn't mean waiting on respawns.</summary>
        public static int KillsFor(BountyDifficulty size, sbyte tier, int spawnCount)
        {
            int kills = size switch
            {
                BountyDifficulty.VeryHard => tier >= MonsterTiers.Red ? 1 : 4,
                BountyDifficulty.Hard => tier >= MonsterTiers.Orange ? 2 : 8,
                _ => tier switch
                {
                    MonsterTiers.Green => 8,
                    MonsterTiers.Blue => 6,
                    _ => 3
                }
            };
            return Math.Max(1, Math.Min(kills, Math.Max(1, spawnCount) * 3));
        }

        /// <summary>The targets a size may point at, best first; the first rule that finds anything wins.</summary>
        public static BountyTargetCandidate[] Pool(IEnumerable<BountyTargetCandidate> targets, BountyDifficulty size,
            string previousName = null)
        {
            var all = (targets ?? Array.Empty<BountyTargetCandidate>()).Where(t => t != null &&
                t.Tier is >= MonsterTiers.Green and <= MonsterTiers.Purple).ToArray();
            var rules = size switch
            {
                BountyDifficulty.VeryHard => new Func<BountyTargetCandidate, bool>[]
                {
                    t => t.Tier >= MonsterTiers.Red,
                    t => t.Tier == MonsterTiers.Orange
                },
                BountyDifficulty.Hard => new Func<BountyTargetCandidate, bool>[]
                {
                    t => t.Tier == MonsterTiers.Orange || t.Tier == MonsterTiers.Yellow && t.SpawnCount >= 4,
                    t => t.Tier == MonsterTiers.Yellow
                },
                _ => new Func<BountyTargetCandidate, bool>[]
                {
                    t => t.Tier is >= MonsterTiers.Green and <= MonsterTiers.Yellow && t.SpawnCount >= 3,
                    t => t.Tier is >= MonsterTiers.Green and <= MonsterTiers.Yellow
                }
            };

            foreach (var rule in rules)
            {
                var pool = all.Where(rule).ToArray();
                if (pool.Length == 0)
                    continue;
                // never the same monster twice in a row, unless it's the only one
                var fresh = BountyTargetCatalog.ExcludeMonsterName(pool, previousName);
                return fresh.Length > 0 ? fresh : pool;
            }
            return Array.Empty<BountyTargetCandidate>();
        }

        /// <summary>A kill counts when the monster has the target's name and stands in the bounty's zone.</summary>
        public static bool Counts(BountyTargetCandidate target, string npcName, eRealm npcRealm, ushort? npcZone) =>
            target != null && npcRealm == eRealm.None && npcZone.HasValue && npcZone.Value == target.ZoneId &&
            string.Equals(npcName, target.Name, StringComparison.OrdinalIgnoreCase);

        // ------------------------------------------------------------------ a zone's huntable monsters

        // Every type a zone has shown, kept between scans: a camp boss that is dead and waiting to respawn is not in the
        // world, but it is still a fair bounty.
        static readonly ConcurrentDictionary<ushort, ConcurrentDictionary<string, BountyTargetCandidate>> Seen = new();

        /// <summary>The monster types of a zone that a bounty may point at, with their con tier and how many stand there.</summary>
        public static IReadOnlyList<BountyTargetCandidate> Targets(Zone zone)
        {
            if (zone == null || zone.ZoneRegion == null)
                return Array.Empty<BountyTargetCandidate>();

            var counts = new Dictionary<string, (int Count, Dictionary<sbyte, int> Tiers, GameNPC Rep)>(StringComparer.OrdinalIgnoreCase);
            GameObject[] objects = zone.ZoneRegion.Objects;
            if (objects != null)
                foreach (GameObject o in objects)
                {
                    if (o is not GameNPC n || o is GameBot || n.CurrentZone != zone || n.Realm != eRealm.None ||
                        n.Brain is IControlledBrain || string.IsNullOrWhiteSpace(n.Name) ||
                        (n.Flags & (GameNPC.eFlags.PEACE | GameNPC.eFlags.CANTTARGET)) != 0)
                        continue;
                    sbyte tier = MonsterTiers.Tier(n);
                    if (tier is MonsterTiers.None or MonsterTiers.Grey)
                        continue;
                    if (BountyTargetCatalog.HurtsStableReputation(n.Faction?.Id ?? 0))
                        continue;
                    if (!counts.TryGetValue(n.Name, out var c))
                        c = (0, new Dictionary<sbyte, int>(), n);
                    c.Tiers[tier] = c.Tiers.TryGetValue(tier, out int k) ? k + 1 : 1;
                    counts[n.Name] = (c.Count + 1, c.Tiers, c.Rep);
                }

            var seen = Seen.GetOrAdd(zone.ID, _ => new ConcurrentDictionary<string, BountyTargetCandidate>(StringComparer.OrdinalIgnoreCase));
            foreach (var kv in counts)
            {
                GameNPC rep = kv.Value.Rep;
                sbyte tier = kv.Value.Tiers.OrderByDescending(t => t.Value).ThenByDescending(t => t.Key).First().Key;
                Point3D at = rep.SpawnPoint ?? new Point3D(rep.X, rep.Y, rep.Z);
                int count = seen.TryGetValue(kv.Key, out var old) ? Math.Max(old.SpawnCount, kv.Value.Count) : kv.Value.Count;
                seen[kv.Key] = new BountyTargetCandidate
                {
                    Name = rep.Name,
                    Level = 0,
                    Tier = tier,
                    RegionId = zone.ZoneRegion.ID,
                    ZoneId = zone.ID,
                    ZoneName = zone.Description,
                    X = at.X,
                    Y = at.Y,
                    Z = at.Z,
                    RepresentativeMobId = rep.InternalID ?? rep.Name,
                    SpawnCount = count
                };
            }
            return seen.Values.ToArray();
        }

        // ------------------------------------------------------------------ event bounties

        public const int EventKills = 6;

        /// <summary>A dynamic event running in this zone now (a stage under way with monsters to fight), or null.</summary>
        public static ChainRuntime LiveEvent(Zone zone)
        {
            if (zone == null)
                return null;
            foreach (ChainRuntime c in DynamicEventManager.Chains)
                if (c.Zone == zone && c.Stage != null && !c.Private && c.Stage.Spawned.Any(n => n.IsEnemy && n.IsAlive))
                    return c;
            return null;
        }

        public static BountyTargetCandidate EventTarget(string chainId)
        {
            ChainRuntime c = DynamicEventManager.Chains.FirstOrDefault(x => x.Def.Id == chainId);
            if (c == null)
                return null;
            var at = c.Stage?.Center ?? c.WakePoint;
            return new BountyTargetCandidate
            {
                Name = c.Def.Title,
                Tier = MonsterTiers.Yellow,
                RegionId = c.Region.ID,
                ZoneId = c.Zone.ID,
                ZoneName = c.Zone.Description,
                X = (int) at.X,
                Y = (int) at.Y,
                Z = (int) at.Z,
                RepresentativeMobId = chainId,
                SpawnCount = EventKills
            };
        }

        /// <summary>A kill counts for an event bounty when it is one of that event's own monsters.</summary>
        public static bool CountsForEvent(string chainId, GameNPC npc) =>
            npc is EventNpc en && en.IsEnemy && en.Chain?.Def?.Id == chainId;

        public static bool IsEventBoss(GameNPC npc) => npc is EventNpc { Role: EventRole.Boss };

        /// <summary>Marks of Valor a claim pays: 1, 3 or 8 by size, halved (at least 1) after a reroll.</summary>
        public static int Marks(BountyDifficulty size, bool rerolled)
        {
            int marks = size switch
            {
                BountyDifficulty.Hard => 3,
                BountyDifficulty.VeryHard => 8,
                _ => 1
            };
            return rerolled ? Math.Max(1, marks / 2) : marks;
        }

        /// <summary>Gold at level 50, where experience means nothing: 15, 35 or 100 by size, halved after a reroll.</summary>
        public static int CapGold(BountyDifficulty size, bool rerolled)
        {
            int gold = size switch
            {
                BountyDifficulty.Hard => 35,
                BountyDifficulty.VeryHard => 100,
                _ => 15
            };
            return rerolled ? gold / 2 : gold;
        }

        public static string TierName(sbyte tier) => tier switch
        {
            MonsterTiers.Green => "green",
            MonsterTiers.Blue => "blue",
            MonsterTiers.Yellow => "yellow",
            MonsterTiers.Orange => "orange",
            MonsterTiers.Red => "red",
            MonsterTiers.Purple => "purple",
            _ => "grey"
        };
    }
}
