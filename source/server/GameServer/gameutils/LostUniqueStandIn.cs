using System;
using System.Reflection;
using DOL.Database;

namespace DOL.GS
{
    /// <summary>
    /// A one-off item whose own template never reached the database comes back as "(blank item)" (owner 2026-11-14: "Some
    /// items come up as blank items when the game is reloaded ... usually armor or weapons ... They were equipped
    /// beforehand"). The treasure chests' armour was such a one-off (GeneratedUniqueItem keeps AllowAdd = false until its
    /// giver says otherwise; TreasureChests never did), so its row in the inventory pointed at a template that was never
    /// written. Those rolled stats are gone; as the inventory loads, such an item is made again - a fresh roll of the same
    /// kind for its owner: the armour piece for the slot it is worn in (one of the armour slots when in the bags), a weapon
    /// in a weapon slot, at the level its condition tells (a rolled item's condition is 2000 a level). Saved under the
    /// missing template's own id, so the inventory row needs no change.
    /// </summary>
    public static class LostUniqueStandIn
    {
        private static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        private static readonly eInventorySlot[] ArmorSlots =
        [
            eInventorySlot.HeadArmor, eInventorySlot.HandsArmor, eInventorySlot.FeetArmor,
            eInventorySlot.TorsoArmor, eInventorySlot.LegsArmor, eInventorySlot.ArmsArmor
        ];

        /// <summary>Pure rule: the level a rolled item's condition tells (2000 a level), else the owner's.</summary>
        public static int LevelFromCondition(int condition, int ownerLevel) =>
            condition >= 1000 ? Math.Clamp((int) Math.Round(condition / 2000.0), 1, 51) : Math.Clamp(ownerLevel, 1, 51);

        /// <summary>True when the item was blank and now has a stand-in.</summary>
        public static bool Mend(GamePlayer player, DbInventoryItem item)
        {
            if (player == null || item == null || string.IsNullOrEmpty(item.UTemplate_Id) ||
                !item.UTemplate_Id.StartsWith("Unique_", StringComparison.Ordinal) ||
                item.Id_nb is not (DbItemTemplate.m_blankItem or DbInventoryItem.BLANK_ITEM))  // (the stand-in DbInventoryItem.Template makes)
                return false;
            try
            {
                var cls = (eCharacterClass) player.CharacterClass.ID;
                eRealm realm = player.Realm is eRealm.Albion or eRealm.Midgard or eRealm.Hibernia ? player.Realm : eRealm.Albion;
                byte level = (byte) LevelFromCondition(item.Condition, player.Level);
                var slot = (eInventorySlot) item.SlotPosition;
                GeneratedUniqueItem g;
                if (slot is eInventorySlot.RightHandWeapon or eInventorySlot.LeftHandWeapon or eInventorySlot.TwoHandWeapon)
                {
                    eObjectType weapon = realm switch
                    {
                        eRealm.Midgard => GeneratedUniqueItem.GetMidgardWeapon(cls),
                        eRealm.Hibernia => GeneratedUniqueItem.GetHiberniaWeapon(cls),
                        _ => GeneratedUniqueItem.GetAlbionWeapon(cls)
                    };
                    g = new GeneratedUniqueItem(false, realm, cls, level, weapon, GeneratedUniqueItem.GenerateItemType(weapon));
                }
                else
                {
                    eInventorySlot piece = Array.IndexOf(ArmorSlots, slot) >= 0 ? slot : ArmorSlots[Random.Shared.Next(ArmorSlots.Length)];
                    eObjectType armor = realm switch
                    {
                        eRealm.Midgard => GeneratedUniqueItem.GetMidgardArmorType(cls, level),
                        eRealm.Hibernia => GeneratedUniqueItem.GetHiberniaArmorType(cls, level),
                        _ => GeneratedUniqueItem.GetAlbionArmorType(cls, level)
                    };
                    g = new GeneratedUniqueItem(false, realm, cls, level, armor, piece);
                }
                g.Id_nb = item.UTemplate_Id;
                g.AllowAdd = true;
                g.Description = "Made again: the item that was here was lost.";
                if (!GameServer.Database.AddObject(g))
                    return false;
                item.Template = g;
                log.Info($"Lost unique {item.UTemplate_Id} of {player.Name} (slot {item.SlotPosition}): made again as {g.Name}");
                return true;
            }
            catch (Exception e)
            {
                log.Error($"Lost unique {item.UTemplate_Id} of {player.Name}", e);
                return false;
            }
        }
    }
}
