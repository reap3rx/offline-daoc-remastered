using System;
using System.Collections.Concurrent;

namespace DOL.GS
{
    /// <summary>
    /// Your companion in the new monster fights (owner 2026-11-19, "Purposeful PvE"): it calls out the telegraphs it sees
    /// coming at you - a heavy blow, a sweep, a slam - which also teaches them; and how well it reads the ones aimed at itself
    /// grows with its competence (MonsterMoves).
    /// </summary>
    public static partial class PersonalCompanions
    {
        static readonly ConcurrentDictionary<GamePlayer, long> _warnedAt = new();

        static readonly string[] ConeLines =
        {
            "It's going to sweep - get to its side!", "Step out of its swing!", "Off its front!",
        };
        static readonly string[] SlamLines =
        {
            "It's going to slam - out of the circle!", "Move, move - it's about to hit the ground!", "Get clear!",
        };
        static readonly string[] HeavyLines =
        {
            "Heavy one coming - catch it!", "Watch the big swing!",
        };

        /// <summary>The owner of a companion (null for any other bot).</summary>
        public static GamePlayer OwnerOf(GameBot bot)
        {
            if (bot == null)
                return null;
            foreach (var kv in _active)
                if (kv.Value == bot)
                    return kv.Key;
            return null;
        }

        /// <summary>A companion's competence rank (0 green .. 10 legendary), -1 for any other bot.</summary>
        public static int RankOf(GameBot bot)
        {
            GamePlayer p = OwnerOf(bot);
            if (p == null)
                return -1;
            Record r = Load(p);
            return r == null ? 0 : CompetenceRank(r.Competence);
        }

        /// <summary>A monster is winding up something nasty at you: your companion may shout a warning.</summary>
        public static void Warn(GamePlayer p, MonsterMoves.Blow kind)
        {
            try
            {
                if (p == null || Of(p) is not GameBot bot || !bot.IsAlive || !bot.IsWithinRadius(p, 2500))
                    return;
                long now = GameLoop.GameLoopTime;
                if (_warnedAt.TryGetValue(p, out long at) && now - at < 20000)
                    return;
                string[] lines = kind switch
                {
                    MonsterMoves.Blow.Cone => ConeLines,
                    MonsterMoves.Blow.Slam => SlamLines,
                    MonsterMoves.Blow.Heavy => HeavyLines,
                    _ => null
                };
                double chance = kind == MonsterMoves.Blow.Heavy ? 0.15 : 0.4;
                if (lines == null || Random.Shared.NextDouble() > chance)
                    return;
                Record r = Load(p);
                if (r == null || r.Talk == "quiet")
                    return;
                _warnedAt[p] = now;
                bot.Say(lines[Random.Shared.Next(lines.Length)]);
            }
            catch (Exception)
            {
            }
        }
    }
}
