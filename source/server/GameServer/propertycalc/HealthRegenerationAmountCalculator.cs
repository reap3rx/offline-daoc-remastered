using System;
using DOL.AI.Brain;

namespace DOL.GS.PropertyCalc
{
    /// <summary>
    /// The health regen rate calculator
    /// 
    /// BuffBonusCategory1 is used for all buffs
    /// BuffBonusCategory2 is used for all debuffs (positive values expected here)
    /// BuffBonusCategory3 unused
    /// BuffBonusCategory4 unused
    /// BuffBonusMultCategory1 unused
    /// </summary>
    [PropertyCalculator(eProperty.HealthRegenerationAmount)]
    public class HealthRegenerationAmountCalculator : PropertyCalculator
    {
        public HealthRegenerationAmountCalculator() { }

        public override int CalcValue(GameLiving living, eProperty property)
        {
            if (living.IsDiseased || living.effectListComponent.ContainsEffectForEffectType(eEffect.Bleed))
                return 0;

            /* PATCH 1.87 COMBAT AND REGENERATION
              - While in combat, health and power regeneration ticks will happen twice as often.
              - Each tick of health and power is now twice as effective.
              - All health and power regeneration aids are now twice as effective.
             */

            // Reverted 1.87 changes.
            // From DoL's `living.Level * 0.6` above level 25, `10 + (living.Level * 0.2)` below level 26.
            // 15 health per tick at level 50 instead of 30.
            // (owner 2026-11-22: "there is no in-combat health regen unless you have a buff or proc that gives it to you.
            // So, the baseline health regen needs to go") - a player or a bot (companions too) in a fight heals only by
            // what a buff, a potion, a proc, an item or an ability gives; out of it, the rest floor below as before
            bool playerSide = living is GamePlayer || living is GameBot;
            bool noBaseline = playerSide && living.InCombat;
            double regen = noBaseline ? 0.0 : 2.5 + living.Level * 0.25;
            int debuff = living.SpecBuffBonusCategory[property];

            if (debuff < 0)
                debuff = -debuff;

            regen += living.BaseBuffBonusCategory[property] + living.AbilityBonus[property] + living.ItemBonus[property] - debuff;

            if (living is GameNPC npc && living is not GameBot)
            {
                // Halved regeneration amount for NPCs in combat.
                // NPCs (necromancer pets excluded) out of combat and without anything in their aggro list (so that it doesn't trigger when NPCs are being kited) get a huge bonus.
                if (npc.InCombat)
                    regen /= 2.0;
                else if (npc is not NecromancerPet && (npc.Brain is not StandardMobBrain brain || !brain.HasAggro))
                    regen = npc.MaxHealth * 0.125;
            }

            regen *= ServerProperties.Properties.HEALTH_REGEN_AMOUNT_MODIFIER;
            if (noBaseline)
                return Math.Max(0, (int) regen);                 // (nothing at all without a regeneration effect)
            if (playerSide)                                      // out of combat: GW2-style, full in seconds (ClassicRestRegeneration)
                regen = Math.Max(regen, ClassicRestRegeneration.OutOfCombatFloor(living.InCombat, living.MaxHealth,
                    ClassicRestRegeneration.OutOfCombatInterval(living)));
            return Math.Max(1, (int) regen);
        }
    }
}
