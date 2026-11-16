using System;
using System.Linq;
using DOL.Database;

namespace DOL.GS
{
    public static class BotStarterInstruments
    {
        public static bool Applies(eCharacterClass characterClass) =>
            characterClass is eCharacterClass.Bard or eCharacterClass.Minstrel;

        public static int ModelFor(eInstrumentType type) => type switch
        {
            eInstrumentType.Drum => 228,
            eInstrumentType.Lute => 227,
            eInstrumentType.Flute => 325,
            _ => throw new ArgumentOutOfRangeException(nameof(type)),
        };

        /// <summary>An instrument goes in the ranged slot only (owner 2026-11-16: a bot showed two instruments on its back -
        /// one in the two-handed slot, one in the ranged): one in the two-handed slot moves to the ranged slot when that is
        /// empty, else into the bags. True when something moved (the caller shows the change).</summary>
        public static bool Tidy(GameBot bot)
        {
            DbInventoryItem two = bot?.Inventory?.GetItem(eInventorySlot.TwoHandWeapon);
            if (two == null || two.Object_Type != (int)eObjectType.Instrument)
                return false;
            eInventorySlot to = bot.Inventory.GetItem(eInventorySlot.DistanceWeapon) == null ? eInventorySlot.DistanceWeapon
                : bot.Inventory.FindFirstEmptySlot(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);
            if (to == eInventorySlot.Invalid)
                return false;
            if (bot.ActiveWeaponSlot == eActiveWeaponSlot.TwoHanded)
                bot.SwitchWeapon(eActiveWeaponSlot.Standard);
            return bot.Inventory.MoveItem(eInventorySlot.TwoHandWeapon, to, two.Count);
        }

        public static bool Ensure(GameBot bot)
        {
            bool added = Tidy(bot);
            if (bot?.Inventory == null || bot.CharacterClass == null ||
                !Applies((eCharacterClass)bot.CharacterClass.ID)) return added;
            // One instrument plays every song (live patch 1.97; owner 2026-11-16): a bot needs one, not one of each kind.
            foreach (eInstrumentType type in new[] { eInstrumentType.Lute })
            {
                if (bot.Inventory.AllItems.Any(item => item.Object_Type == (int)eObjectType.Instrument && item.Model > 0 &&
                    (item.SlotPosition == Slot.RANGED || item.SlotPosition == Slot.TWOHAND ||
                     item.SlotPosition >= (int)eInventorySlot.FirstBackpack && item.SlotPosition <= (int)eInventorySlot.LastBackpack))) continue;

                eInventorySlot slot = bot.Inventory.GetItem(eInventorySlot.DistanceWeapon) == null ? eInventorySlot.DistanceWeapon :
                    bot.Inventory.FindFirstEmptySlot(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);
                if (slot == eInventorySlot.Invalid) continue; // Never overwrite earned loot in a full bag.
                var template = new DbItemUnique(new DbItemTemplate
                {
                    Id_nb = $"bot_starter_instrument_{bot.Realm}_{type}", Name = $"training {type.ToString().ToLowerInvariant()}",
                    Object_Type = (int)eObjectType.Instrument, Item_Type = Slot.TWOHAND,
                    DPS_AF = (int)type, Model = ModelFor(type), Level = 1, LevelRequirement = 1,
                    Realm = (int)bot.Realm, Quality = 100, Condition = 50000, MaxCondition = 50000,
                    Durability = 50000, MaxDurability = 50000, MaxCount = 1,
                    IsPickable = true, IsDropable = false, IsTradable = false,
                });
                var item = GameInventoryItem.Create(template);
                item.Creator = nameof(BotStarterInstruments);
                added |= bot.Inventory.AddItem(slot, item);
            }
            return added;
        }
    }
}
