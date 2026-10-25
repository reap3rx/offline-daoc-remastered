/*
 * Fealty: summon a retainer under the King / Queen's commander.
 * Spell.DamageType picks the retainer: 0 armsman, 1 cleric, 2 wizard, 3 sorcerer, 5 scout
 * (BdSubPet.SubPetType: Melee, Healer, Caster, Debuffer, Archer).
 * Unlike the Bonedancer, the retainers' levels have no combined cap: the commander's rank
 * (1-5 retainers) is the only limit.
 */
using DOL.AI.Brain;
using DOL.GS.PacketHandler;

namespace DOL.GS.Spells
{
	[SpellHandler(eSpellType.SummonRetainer)]
	public class SummonRetainer : SummonMinionHandler
	{
		public SummonRetainer(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

		protected override int MaxTotalMinionLevel => int.MaxValue;

		/// <summary>
		/// The King's own messages (the Bonedancer's say "your general ... as he can command"):
		/// the commander by name, and the right pronoun for its gender.
		/// </summary>
		public override bool CheckBeginCast(GameLiving selectedTarget)
		{
			if (Caster is GamePlayer)
			{
				GameNPC commander = Caster.ControlledBrain?.Body;

				if (commander == null)
				{
					MessageToCaster("You must summon your commander before you can call a retainer.", eChatType.CT_SpellResisted);
					return false;
				}

				if (commander.ControlledNpcList == null || commander.PetCount >= commander.ControlledNpcList.Length)
				{
					string pronoun = commander.Gender switch { eGender.Female => "she", eGender.Male => "he", _ => "they" };
					MessageToCaster($"Your {commander.Name} already commands as many retainers as {pronoun} can.", eChatType.CT_SpellResisted);
					return false;
				}
			}

			return base.CheckBeginCast(selectedTarget);
		}

		protected override IControlledBrain GetPetBrain(GameLiving owner)
		{
			BdSubPet.SubPetType type = (BdSubPet.SubPetType)Spell.DamageType;
			GameLiving commander = owner.ControlledBrain.Body;

			return type switch
			{
				BdSubPet.SubPetType.Melee => new BdMeleeBrain(commander),
				BdSubPet.SubPetType.Healer => new RoyalClericBrain(commander),
				BdSubPet.SubPetType.Caster => new BdCasterBrain(commander),
				BdSubPet.SubPetType.Debuffer => new BdDebufferBrain(commander),
				BdSubPet.SubPetType.Archer => new BdArcherBrain(commander),
				_ => new BdMeleeBrain(commander)
			};
		}

		protected override GameSummonedPet GetGamePet(INpcTemplate template)
		{
			return new RoyalRetainerPet(template);
		}
	}
}
