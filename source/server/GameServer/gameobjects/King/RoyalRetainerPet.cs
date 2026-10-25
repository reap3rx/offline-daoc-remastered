/*
 * A King / Queen's retainer: an armsman, cleric, scout, sorcerer or wizard sworn to the royal commander.
 * A Bonedancer-style sub-pet that keeps the arms and armor of its own equipment template.
 */
namespace DOL.GS
{
	public class RoyalRetainerPet : BdSubPet
	{
		private readonly string m_equipmentTemplate;

		public RoyalRetainerPet(INpcTemplate npcTemplate)
			: base(npcTemplate)
		{
			m_equipmentTemplate = npcTemplate.Inventory;
		}

		public override bool AddToWorld()
		{
			// Make sure the template's equipment is on before the first create packet.
			if (Inventory == null && !string.IsNullOrEmpty(m_equipmentTemplate))
			{
				EquipmentTemplateID = null;
				LoadEquipmentTemplateFromDatabase(m_equipmentTemplate);
			}

			return base.AddToWorld();
		}
	}
}
