using System;
using System.Collections.Generic;
using System.Linq;
using DOL.AI.Brain;

namespace DOL.GS
{
    /// <summary>
    /// World bots now help their own realm's players and other bots fighting monsters near
    /// them, whether or not they share a group (owner 2026-11-13: "Bots will try to help out a
    /// player or other bots in trouble or help kill mobs if they're nearby ... Even when not in
    /// a group"). Before this a bot only ever assisted its own group, so it would walk past a
    /// player dying to two monsters.
    /// - Someone in trouble (under 60% health, two or more monsters on them, or an orange or
    ///   harder monster) is always helped.
    /// - Another bot's ordinary fight is joined now and then (about a third of the time,
    ///   decided once per bot and monster, so the bot does not flip-flop).
    /// - A player's ordinary fight is left alone: a bot that out-damages the player would take
    ///   the kill's loot (loot goes to the top damage dealer).
    /// The bot must itself be fit (half health or more) and the monster must not be too hard for
    /// it (orange at most), and it only acts when it is not already fighting. Its own group's
    /// fights stay with the group code (TryAssistAutonomousPveCombat).
    /// </summary>
    public static class AutonomousNearbyHelp
    {
        public const int Radius = 1500;
        public const int ScanMilliseconds = 2000;
        public const int OrdinaryBotFightPercent = 35;

        public enum Need { None, Ordinary, Trouble }

        /// <summary>Pure rule: how much the ally needs help.</summary>
        public static Need Assess(int allyHealthPercent, int monstersOnAlly, int worstConToAlly)
        {
            if (monstersOnAlly <= 0) return Need.None;
            if (allyHealthPercent < 60 || monstersOnAlly >= 2 || worstConToAlly >= (int)ConColor.ORANGE)
                return Need.Trouble;
            return Need.Ordinary;
        }

        /// <summary>Pure rule: does this bot step in?</summary>
        public static bool Joins(Need need, bool allyIsHuman, int botHealthPercent, int foeConToBot, int roll)
        {
            if (need == Need.None || botHealthPercent < 50) return false;
            if (foeConToBot <= (int)ConColor.GREY || foeConToBot > (int)ConColor.ORANGE) return false;
            if (need == Need.Trouble) return true;
            return !allyIsHuman && roll < OrdinaryBotFightPercent;
        }

        /// <summary>A stable 0-99 roll per bot and monster.</summary>
        public static int Roll(int botId, int foeId) =>
            (int)((uint)HashCode.Combine(botId, foeId) % 100);

        public sealed class Choice
        {
            public GameLiving Ally;
            public GameNPC Foe;
            public Need Need;
        }

        public static Choice Find(GameBot bot)
        {
            if (bot?.IsAlive != true || bot.CurrentZone == null || bot.HealthPercent < 50)
                return null;

            IEnumerable<GameLiving> humans = bot.GetPlayersInRadius(Radius).Cast<GameLiving>();
            IEnumerable<GameLiving> bots = bot.GetNPCsInRadius(Radius).OfType<GameBot>()
                .Where(other => other != bot && !other.IsTemporaryGroupHelper).Cast<GameLiving>();

            Choice best = null;
            foreach (GameLiving ally in humans.Concat(bots))
            {
                if (ally == null || ally == bot || !ally.IsAlive || ally.Realm != bot.Realm ||
                    ally.CurrentRegionID != bot.CurrentRegionID || ally.ObjectState != GameObject.eObjectState.Active)
                    continue;
                if (bot.Group != null && bot.Group.IsInTheGroup(ally))
                    continue;   // the group's own fights are handled by the group code
                if (!ally.InCombat)
                    continue;

                List<GameNPC> foes = MonstersOn(bot, ally);
                if (foes.Count == 0)
                    continue;
                int worstCon = foes.Max(foe => ally.GetConLevel(foe));
                Need need = Assess(ally.HealthPercent, foes.Count, worstCon);
                // The monster to take: one already hitting the ally that is not yet on someone else,
                // then the weakest (finish it), nearest first.
                GameNPC foe = foes
                    .OrderBy(candidate => candidate.TargetObject == ally ? 0 : 1)
                    .ThenBy(candidate => candidate.HealthPercent)
                    .ThenBy(candidate => bot.GetDistanceTo(candidate))
                    .FirstOrDefault(candidate => Joins(need, ally is GamePlayer, bot.HealthPercent,
                        bot.GetConLevel(candidate), Roll(bot.ObjectID, candidate.ObjectID)));
                if (foe == null)
                    continue;
                if (!PathfindingProvider.Instance.HasLineOfSight(bot.CurrentZone, new(bot.X, bot.Y, bot.Z),
                        new(foe.X, foe.Y, foe.Z), PathfindingProvider.Instance.DefaultFilters))
                    continue;

                // Trouble first, then players, then the nearest.
                if (best == null || need > best.Need ||
                    need == best.Need && (ally is GamePlayer && best.Ally is not GamePlayer ||
                        (ally is GamePlayer) == (best.Ally is GamePlayer) &&
                        bot.GetDistanceTo(ally) < bot.GetDistanceTo(best.Ally)))
                    best = new Choice { Ally = ally, Foe = foe, Need = need };
            }
            return best;
        }

        /// <summary>Living monsters (no realm, nobody's pet) fighting this ally that the bot may attack.</summary>
        private static List<GameNPC> MonstersOn(GameBot bot, GameLiving ally)
        {
            var result = new List<GameNPC>();
            void Consider(GameObject candidate)
            {
                if (candidate is not GameNPC npc || npc is GameBot || result.Contains(npc) || !npc.IsAlive ||
                    npc.Realm != eRealm.None || npc.ObjectState != GameObject.eObjectState.Active ||
                    npc.CurrentRegionID != bot.CurrentRegionID || npc.Brain is IControlledBrain ||
                    !bot.IsWithinRadius(npc, Radius + 500) ||
                    !GameServer.ServerRules.IsAllowedToAttack(bot, npc, true))
                    return;
                result.Add(npc);
            }

            foreach (GameLiving attacker in ally.attackComponent.AttackerTracker.Attackers.ToList())
                if (attacker?.TargetObject == ally || attacker is GameNPC { InCombat: true })
                    Consider(attacker);
            if (ally.TargetObject is GameNPC target && target.InCombat &&
                (target.TargetObject == ally || ally.attackComponent.AttackState))
                Consider(target);
            return result;
        }
    }
}
