/*
 * The potion bag (owner 2026-10-27): sixteen more inventory slots that hold potions only, so an alchemist's (or
 * anyone's) potions don't eat the backpack. Potions there are ordinary inventory items - drag them in and out, put them
 * on the quickbar, use them from the bag - saved with the rest of the inventory.
 *
 * It lives in the saddlebag slots (FirstBagHorse 80 .. LastBagHorse 95): the server already keeps, saves, moves and
 * sends those, and the champion-level saddlebags they were for have no place in this game (no champion levels, no
 * saddlebag window in the client). GamePlayerInventory's saddlebag check is this bag's "potions only" rule instead.
 */
using DOL.Database;

namespace DOL.GS
{
	public static class PotionBag
	{
		public const eInventorySlot First = eInventorySlot.FirstBagHorse;
		public const eInventorySlot Last = eInventorySlot.LastBagHorse;

		public static bool IsBagSlot(eInventorySlot slot) => slot is >= First and <= Last;

		/// <summary>
		/// What the bag takes: a carried (not worn) item with a spell to use - potions (Magical / generic) and alchemy
		/// tinctures. Poisons have their own bag.
		/// </summary>
		public static bool Fits(DbInventoryItem item) =>
			item != null && Fits(item.Item_Type, item.Object_Type, item.SpellID);

		public static bool Fits(int itemType, int objectType, int spellId) =>
			itemType == (int) eInventorySlot.FirstBackpack && spellId != 0 &&
			(eObjectType) objectType is eObjectType.Magical or eObjectType.GenericItem or eObjectType.AlchemyTincture;
	}
}
