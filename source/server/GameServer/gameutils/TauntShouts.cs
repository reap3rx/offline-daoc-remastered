using System;
using System.Collections.Generic;
using System.Linq;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS
{
    /// <summary>
    /// Taunts are shouts (owner 2026-11-19: "drop the taunt and detaunt styles ... all fighter based classes (Hero,
    /// Champion, Blademaster, Paladin, Armsman, etc..) [get] a ranged single target shout, and then eventually an AoE taunt
    /// shout. Stealthers and Minstrels do not apply"; "Taunts ... need to be really powerful and not have big
    /// cooldowns"; "give icons and put in the abilities window"):
    ///   Challenge (level 5): the target's threat on you becomes its highest plus half again and a margin, and it turns
    ///     on you at once - 1500 range, 8 s.
    ///   Battle Cry (level 20): the same on every monster within 600 of you - 20 s.
    /// Abilities, taught by each fighter class's career (its "...Career" specialization goes by your level), with the
    /// client's own shout icons (Taunting Shout, Bolstering Roar). The fighters' blows also make half again the threat
    /// (ThreatFactor). Bots that fight use them when a monster is on someone softer.
    /// </summary>
    public static class TauntShouts
    {
        public const string ChallengeKey = "Challenge", BattleCryKey = "Battle Cry";
        public const int ChallengeLevel = 5, BattleCryLevel = 20;
        public const int ChallengeRange = 1500, BattleCryRadius = 600;
        public const int ChallengeReuseMs = 8000, BattleCryReuseMs = 20000;
        public const ushort ShoutFx = 7353;                           // (the old taunt styles' own effect)
        public const double FighterThreat = 1.5;

        /// <summary>Fighter classes (their careers teach the shouts).</summary>
        public static readonly HashSet<eCharacterClass> Fighters = new()
        {
            eCharacterClass.Hero, eCharacterClass.Champion, eCharacterClass.Blademaster,
            eCharacterClass.Armsman, eCharacterClass.Paladin, eCharacterClass.Mercenary,
            eCharacterClass.Warrior, eCharacterClass.Thane, eCharacterClass.Berserker, eCharacterClass.Savage, eCharacterClass.Valkyrie,
        };

        /// <summary>Classes with Challenge but not Battle Cry (owner 2026-11-20: "Warden should get challenge, but not battle
        /// cry"). Their blows make no extra threat.</summary>
        public static readonly HashSet<eCharacterClass> ChallengeOnly = new() { eCharacterClass.Warden };

        static bool CanChallenge(GameLiving l)
        {
            int id = l switch
            {
                GamePlayer p => p.CharacterClass?.ID ?? 0,
                GameBot b => b.CharacterClass?.ID ?? 0,
                _ => 0
            };
            return IsFighter(l) || id != 0 && ChallengeOnly.Contains((eCharacterClass) id);
        }

        public static bool IsFighter(GameLiving l)
        {
            int id = l switch
            {
                GamePlayer p => p.CharacterClass?.ID ?? 0,
                GameBot b => b.CharacterClass?.ID ?? 0,
                _ => 0
            };
            return id != 0 && Fighters.Contains((eCharacterClass) id);
        }

        /// <summary>StandardMobBrain: a fighter's melee makes half again the threat.</summary>
        public static double ThreatFactor(GameLiving attacker, AttackData ad) =>
            ad != null && ad.IsMeleeAttack && IsFighter(attacker) ? FighterThreat : 1.0;

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Register();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[TauntShouts] " + ex);
            }
        }

        public static void Register()
        {
            var challenge = new DbAbility
            {
                KeyName = ChallengeKey, Name = ChallengeKey, IconID = 3464, InternalID = 3901, AbilityID = 3901,
                Description = "Shout a challenge at your target (1500 range): it turns on you at once, and you hold more of its anger than anyone else. 8 second reuse.",
            };
            var cry = new DbAbility
            {
                KeyName = BattleCryKey, Name = BattleCryKey, IconID = 974, InternalID = 3902, AbilityID = 3902,
                Description = "A roar that turns every enemy within 600 of you on you at once, and you hold more of their anger than anyone else. 20 second reuse.",
            };
            int n = 0;
            foreach (eCharacterClass c in Fighters)
            {
                string career = c + "Career";
                SkillBase.AddScriptedAbility(challenge, career, ChallengeLevel);
                SkillBase.AddScriptedAbility(cry, career, BattleCryLevel);
                n++;
            }
            foreach (eCharacterClass c in ChallengeOnly)
                SkillBase.AddScriptedAbility(challenge, c + "Career", ChallengeLevel);
            Console.WriteLine($"[TauntShouts] Challenge and Battle Cry for {n} fighter classes, Challenge for {ChallengeOnly.Count} more");
        }

        /// <summary>One monster turned on the shouter: its threat on them its highest plus half again and a margin.</summary>
        public static void Taunt(GameLiving shouter, GameNPC n)
        {
            if (n?.Brain is not StandardMobBrain brain || !n.IsAlive)
                return;
            MonsterTiers.Touch(shouter, n);
            long top = brain.TopAggro;
            long have = brain.AggroOf(shouter);
            long want = (long) (top * 1.5) + 50 + shouter.Level * 10;
            if (want > have)
                brain.AddToAggroList(shouter, want - have);
            if (n.TargetObject != shouter && n.IsWithinRadius(shouter, 3000))
                n.StartAttack(shouter);
        }

        static void Shout(GameLiving who, eEmote emote)
        {
            foreach (GamePlayer v in who.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendEmoteAnimation(who, emote);
        }

        static bool Foe(GameLiving who, GameNPC n) =>
            n != null && n.IsAlive && n.ObjectState == GameObject.eObjectState.Active && n.Brain is StandardMobBrain &&
            MonsterTiers.Combatant(n) == null && GameServer.ServerRules.IsAllowedToAttack(who, n, true);

        /// <summary>Challenge: the target (null: not a foe in range - why not, for a player).</summary>
        public static string Challenge(GameLiving who, GameNPC target)
        {
            if (!Foe(who, target))
                return "You must target an enemy to challenge.";
            if (!who.IsWithinRadius(target, ChallengeRange))
                return $"{target.GetName(0, true)} is too far away to hear your challenge.";
            Shout(who, eEmote.Taunt);
            Taunt(who, target);
            foreach (GamePlayer v in who.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(who, target, ShoutFx, 0, false, 1);
            Message.SystemToArea(who, $"{who.GetName(0, true)} challenges {target.GetName(0, false)}!", eChatType.CT_Emote, who);
            return null;
        }

        /// <summary>Battle Cry: every foe within reach; how many turned.</summary>
        public static int BattleCry(GameLiving who)
        {
            Shout(who, eEmote.Roar);
            int count = 0;
            foreach (GameNPC n in who.GetNPCsInRadius(BattleCryRadius))
            {
                if (!Foe(who, n))
                    continue;
                Taunt(who, n);
                foreach (GamePlayer v in who.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                    v.Out.SendSpellEffectAnimation(who, n, ShoutFx, 0, false, 1);
                count++;
            }
            foreach (GamePlayer v in who.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(who, who, ShoutFx, 0, false, 1);
            Message.SystemToArea(who, $"{who.GetName(0, true)} lets out a battle cry!", eChatType.CT_Emote, who);
            return count;
        }

        // ------------------------------------------------------------------ bots

        sealed class BotTimes
        {
            public long Next, ChallengeReady, CryReady;
        }

        static readonly System.Runtime.CompilerServices.ConditionalWeakTable<GameBot, BotTimes> _bots = new();

        /// <summary>BotBrain.Think: a fighting fighter bot shouts when a monster is on someone softer (not a fighter): Battle
        /// Cry for two or more near it, Challenge for one.</summary>
        public static void BotThink(GameBot bot)
        {
            if (bot == null || !bot.IsAlive || !bot.InCombat || bot.Level < ChallengeLevel || !CanChallenge(bot) || bot.IsIncapacitated)
                return;
            long now = GameLoop.GameLoopTime;
            BotTimes t = _bots.GetValue(bot, _ => new BotTimes());
            if (now < t.Next)
                return;
            t.Next = now + 1000;
            var side = new HashSet<GameLiving>();
            if (bot.Group != null)
                foreach (GameLiving m in bot.Group.GetMembersInTheGroup())
                    side.Add(m);
            if (MonsterTiers.Combatant(bot) is GameLiving lead)
                side.Add(lead);
            var onSoft = new List<GameNPC>();
            foreach (GameNPC n in bot.GetNPCsInRadius(ChallengeRange))
                if (Foe(bot, n) && n.TargetObject is GameLiving tl && tl != bot && side.Contains(tl) && !IsFighter(tl))
                    onSoft.Add(n);
            if (onSoft.Count == 0)
                return;
            int near = onSoft.Count(n => n.IsWithinRadius(bot, BattleCryRadius));
            if (near >= 2 && bot.Level >= BattleCryLevel && IsFighter(bot) && now >= t.CryReady)
            {
                BattleCry(bot);
                t.CryReady = now + BattleCryReuseMs;
            }
            else if (now >= t.ChallengeReady)
            {
                Challenge(bot, onSoft.OrderBy(n => n.GetDistanceTo(bot)).First());
                t.ChallengeReady = now + ChallengeReuseMs;
            }
        }
    }
}

namespace DOL.GS.SkillHandler
{
    using DOL.GS.PacketHandler;

    [SkillHandler(TauntShouts.ChallengeKey)]
    public class ChallengeAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive)
                return;
            string why = TauntShouts.Challenge(player, player.TargetObject as GameNPC);
            if (why != null)
            {
                player.Out.SendMessage(why, eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            player.Out.SendMessage($"{player.TargetObject.GetName(0, true)} turns on you!", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            player.DisableSkill(ab, TauntShouts.ChallengeReuseMs);
        }
    }

    [SkillHandler(TauntShouts.BattleCryKey)]
    public class BattleCryAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive)
                return;
            int n = TauntShouts.BattleCry(player);
            player.Out.SendMessage(n > 0 ? $"Your battle cry turns {n} {(n == 1 ? "enemy" : "enemies")} on you!" : "Your battle cry echoes, but no enemy is near.",
                eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            player.DisableSkill(ab, TauntShouts.BattleCryReuseMs);
        }
    }
}
