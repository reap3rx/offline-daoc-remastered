using System;
using System.Runtime.CompilerServices;
using DOL.Database;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// What the reworked shield styles do besides their procs (StyleRework.ShieldLine, owner 2026-11-20):
    ///   Numb: the block timing is WideBlockBonusMs more forgiving for WideBlockMs (ActionCombat.Window).
    ///   Incapacitate: the next AutoBlockCharges blows from in front within AutoBlockMs are blocked for you.
    ///   Brutalize (Shield Wall): every blow from in front is blocked for ShieldWallMs.
    /// Blocked for you = in Action Combat as a chained block (ActionCombat's defense: no press needed); for bots and
    /// anyone else, a sure block (AttackComponent.CheckBlock). A shield must be carried.
    /// Also the Shield Mastery ability (owner 2026-11-20: "in the training window (and abilities window) when you get to
    /// certain level of shield, you have the extra target blocks, and those should be mentioned there"): ranks I-VII at
    /// Shields 8, 15, 22, 29, 36, 43 and 50 - the extra attackers a timed block also turns aside (ActionCombat.BlockChainFor:
    /// one more each rank, on top of the shield's size: small 1, medium 2, large 3).
    /// </summary>
    public static class ShieldBoost
    {
        public const int WideBlockMs = 8000, WideBlockBonusMs = 150;
        public const int AutoBlockCharges = 2, AutoBlockMs = 8000, ShieldWallMs = 8000;
        public const string MasteryKey = "Shield Mastery";
        public static readonly int[] MasteryAt = { 8, 15, 22, 29, 36, 43, 50 };

        sealed class Boost
        {
            public long WideUntil, AutoUntil;
            public int AutoLeft;
        }

        static readonly ConditionalWeakTable<GameLiving, Boost> _boosts = new();

        public static void WidenBlock(GameLiving who)
        {
            _boosts.GetValue(who, _ => new Boost()).WideUntil = GameLoop.GameLoopTime + WideBlockMs;
            (who as GamePlayer)?.Out.SendMessage("You set your shield - your blocks come easier.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
        }

        public static void AutoBlock(GameLiving who, int charges, int ms)
        {
            Boost b = _boosts.GetValue(who, _ => new Boost());
            b.AutoLeft = charges;
            b.AutoUntil = GameLoop.GameLoopTime + ms;
            (who as GamePlayer)?.Out.SendMessage(charges >= 99 ? "You raise a wall of shield!" : "You hold your shield high.",
                eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
        }

        /// <summary>ActionCombat.Window: the block window's extra milliseconds now.</summary>
        public static int WindowBonus(GameLiving who) =>
            _boosts.TryGetValue(who, out Boost b) && GameLoop.GameLoopTime < b.WideUntil ? WideBlockBonusMs : 0;

        /// <summary>A blow blocked for them: a held auto-block, a shield carried, the attacker in front. Spends a charge.</summary>
        public static bool TakeAutoBlock(GameLiving who, AttackData ad)
        {
            if (who == null || ad?.Attacker == null || !_boosts.TryGetValue(who, out Boost b) || b.AutoLeft <= 0 ||
                GameLoop.GameLoopTime > b.AutoUntil)
                return false;
            if (who.ActiveLeftWeapon is not DbInventoryItem shield || (eObjectType) shield.Object_Type is not eObjectType.Shield)
                return false;
            if (!who.IsObjectInFront(ad.Attacker, 120))
                return false;
            b.AutoLeft--;
            return true;
        }

        /// <summary>Shield Mastery's ranks in the Shields specialization (shown in the trainer and the abilities list).</summary>
        public static void Register()
        {
            var dba = new DbAbility
            {
                KeyName = MasteryKey, Name = MasteryKey, IconID = 412, InternalID = 3903, AbilityID = 3903,
                Description = "After a timed block your shield also turns aside one blow from each of several more attackers for a " +
                    "moment: one more for each rank of Shield Mastery, plus your shield's size (small 1, medium 2, large 3). A small " +
                    "shield covers your front, a medium one 270 degrees, a large one all round. Ranks at Shields 8, 15, 22, 29, 36, 43 " +
                    "and 50; higher Shields also makes each block take more of the blow.",
            };
            for (int i = 0; i < MasteryAt.Length; i++)
                SkillBase.AddScriptedAbility(dba, Specs.Shields, MasteryAt[i], 0, i + 1);
            Console.WriteLine("[ShieldBoost] Shield Mastery I-VII in Shields");
        }
    }
}
