/*
 * The King / Queen's commander (Squire -> Shieldbearer -> Sergeant-at-Arms -> Knight-Errant -> Knight).
 * Built on the Bonedancer's CommanderPet, but:
 *  - it controls one retainer per rank (1 to 5), set by its NPC template (64001-64005);
 *  - it keeps its Albion arms and armor from its equipment template (no random Norse weapon);
 *  - its look is set by the summon spell: the caster's race, the opposite gender.
 */
using System;

namespace DOL.GS
{
	public class RoyalCommanderPet : CommanderPet
	{
		/// <summary>Commander NPC templates are 64001 (Squire) .. 64005 (Knight).</summary>
		public const int TemplateBase = 64000;

		/// <summary>Rank 1 (Squire) to 5 (Knight); also the number of retainers it commands.</summary>
		public int Rank { get; }

		public RoyalCommanderPet(INpcTemplate npcTemplate)
			: base(npcTemplate)
		{
			Rank = Math.Clamp(npcTemplate.TemplateId - TemplateBase, 1, 5);
			InitControlledBrainArray(Rank);

			// CommanderPet's constructor hands an unknown commander a random 1.65 Norse weapon and drops
			// its shield. Reload the template's own equipment (Albion sword, shield from Shieldbearer up).
			if (!string.IsNullOrEmpty(npcTemplate.Inventory))
			{
				EquipmentTemplateID = null;
				LoadEquipmentTemplateFromDatabase(npcTemplate.Inventory);
			}
		}
	}
}
