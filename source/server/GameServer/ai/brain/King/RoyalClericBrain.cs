/*
 * The King / Queen's cleric retainer: heals (the Bonedancer healer's rules) and keeps the
 * royal party's spec buffs up.
 */
using System.Linq;
using DOL.GS;

namespace DOL.AI.Brain
{
	public class RoyalClericBrain : BdHealerBrain
	{
		public RoyalClericBrain(GameLiving owner) : base(owner) { }

		protected override GameLiving FindTargetForDefensiveSpell(Spell spell)
		{
			switch (spell.SpellType)
			{
				case eSpellType.StrengthConstitutionBuff:
				case eSpellType.DexterityQuicknessBuff:
				case eSpellType.SpecArmorFactorBuff:
				case eSpellType.BaseArmorFactorBuff:
				case eSpellType.AcuityBuff:
				case eSpellType.StrengthBuff:
				case eSpellType.ConstitutionBuff:
				case eSpellType.DexterityBuff:
				{
					// Players first (the King and the group), then the commander and the other retainers.
					return BonedancerSupportTargets(spell, true)
						.Where(living => !LivingHasEffect(living, spell))
						.OrderBy(living => living is GamePlayer ? 0 : 1)
						.FirstOrDefault();
				}
				default:
					return base.FindTargetForDefensiveSpell(spell);
			}
		}
	}
}
