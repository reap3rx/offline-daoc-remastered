/*
 * Fealty: summon the King / Queen's commander.
 * Spell.LifeDrainReturn = NPC template (64001-64005), Spell.Damage = level as % of the caster's.
 * The commander keeps one name and look for the whole career (RoyalRetinue).
 */
using System.Linq;
using DOL.GS.Realm;

namespace DOL.GS.Spells
{
	[SpellHandler(eSpellType.SummonRoyalCommander)]
	public class SummonRoyalCommander : SummonCommanderPet
	{
		public SummonRoyalCommander(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

		protected override GameSummonedPet GetGamePet(INpcTemplate template)
		{
			RoyalCommanderPet pet = new(template);

			// The commander is of the caster's own race and the opposite gender.
			if (Caster is GamePlayer player)
			{
				PlayerRace race = PlayerRace.AllRaces.FirstOrDefault(r => (int)r.ID == player.Race);
				eGender gender = player.Gender == eGender.Male ? eGender.Female : eGender.Male;
				eLivingModel model = race?.GetModel(gender) ?? eLivingModel.None;

				if (model == eLivingModel.None)
				{
					gender = player.Gender;
					model = race?.GetModel(gender) ?? eLivingModel.None;
				}

				if (model != eLivingModel.None)
				{
					pet.Model = (ushort)model;
					pet.Gender = gender;
				}

				// One commander for the whole career: "Squire Anne" grows into "Knight Anne".
				pet.Name = $"{pet.Name} {RoyalRetinue.GetOrCreateCommanderName(player, gender)}";
				pet.GuildName = RoyalRetinue.GuildNameFor(player);
			}

			return pet;
		}
	}
}
