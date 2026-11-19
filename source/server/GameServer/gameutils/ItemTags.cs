using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using DOL.Database;
using DOL.Events;
using DOL.Logging;

namespace DOL.GS
{
    /// <summary>
    /// What kind of thing a bag item is, for the new client's icons (owner 2026-11-18: "some of the icons make the junk or
    /// non item loot looks like it would be a usable item ... put something over the icon to indicate that the thing that
    /// dropped was of a certain type? Like junk, quest, etc. Actual gear doesn't need that unless it's a heirloom"):
    ///   junk     - for selling only (trophies, monster parts, vendor trash)
    ///   quest    - can't be sold, traded or dropped (a quest's item)
    ///   craft    - a crafting material (an ingredient of a recipe)
    ///   heirloom - a Legendary heirloom weapon (LootUses)
    /// Gear, potions and everything you can use get no tag. Sent as "#ITAG|slot:tag;slot:tag" (an empty tag clears it):
    /// all of them when you enter the game, the changed slots with every inventory update.
    /// </summary>
    public static class ItemTags
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);
        private static HashSet<string> _ingredients;
        private static readonly object Sync = new();

        static bool IsIngredient(string idNb)
        {
            lock (Sync)
            {
                if (_ingredients == null)
                {
                    _ingredients = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                    try
                    {
                        foreach (DbCraftedXItem x in GameServer.Database.SelectAllObjects<DbCraftedXItem>())
                            if (!string.IsNullOrEmpty(x.IngredientId_nb))
                                _ingredients.Add(x.IngredientId_nb);
                    }
                    catch (Exception e)
                    {
                        log.Warn($"ItemTags: recipes: {e.Message}");
                    }
                }
                return _ingredients.Contains(idNb ?? "");
            }
        }

        public static string Of(DbInventoryItem item)
        {
            DbItemTemplate t = item?.Template;
            if (t == null)
                return "";
            if (t.PackageID == LootUses.HeirloomMark)
                return "heirloom";
            if (t.Item_Type >= (int) eInventorySlot.MinEquipable && t.Item_Type <= (int) eInventorySlot.MaxEquipable)
                return "";                                          // gear: worn somewhere
            int ot = t.Object_Type;
            if (ot is >= (int) eObjectType._FirstWeapon and <= (int) eObjectType._LastArmor or >= (int) eObjectType.Shield and <= (int) eObjectType.Poison
                or >= (int) eObjectType._FirstHouse)
                return "";                                          // gear, ammunition, poisons, house pieces
            if (t.SpellID > 0 || t.SpellID1 > 0 || t.MaxCharges > 0 || t.Charges > 0 || LootOverhaul.IsDye(t) ||
                NoveltyPotions.Is(t.Id_nb) || t.Id_nb is LootUses.MapId or LootUses.KitTokenId ||
                CampingSupplies.TryParse(t.Id_nb, out _, out _) || PlayerWallet.IsCurrency(t.Id_nb) ||
                t.Id_nb.StartsWith("valor_", StringComparison.Ordinal) || t.Id_nb.Contains("respec", StringComparison.OrdinalIgnoreCase) ||
                ot is (int) eObjectType.AlchemyTincture or (int) eObjectType.SpellcraftGem)
                return "";                                          // things you use
            if (IsIngredient(t.Id_nb))
                return "craft";
            if (!t.IsDropable || !t.IsTradable)
                return "quest";
            return "junk";
        }

        static string Line(IEnumerable<(int Slot, string Tag)> tags)
        {
            var sb = new StringBuilder("#ITAG|");
            bool first = true;
            foreach (var (slot, tag) in tags)
            {
                if (!first) sb.Append(';');
                sb.Append(slot).Append(':').Append(tag);
                first = false;
            }
            return first ? null : sb.ToString();
        }

        /// <summary>The changed slots' tags (GamePlayerInventory.UpdateChangedSlots).</summary>
        public static void SendChanged(GamePlayer p, IEnumerable<(int Slot, DbInventoryItem Item)> changed)
        {
            if (!NewClient.Is(p))
                return;
            try
            {
                if (Line(changed.Select(c => (c.Slot, Of(c.Item)))) is string line)
                    NewClient.Send(p, line);
            }
            catch (Exception e)
            {
                log.Error("ItemTags.SendChanged", e);
            }
        }

        /// <summary>Every tagged item you carry or wear (entering the game).</summary>
        public static void SendAll(GamePlayer p)
        {
            if (!NewClient.Is(p) || p.Inventory == null)
                return;
            try
            {
                var tags = p.Inventory.AllItems.Where(i => i != null).Select(i => (i.SlotPosition, Of(i))).Where(x => x.Item2 != "").ToList();
                if (Line(tags) is string line)
                    NewClient.Send(p, line);
            }
            catch (Exception e)
            {
                log.Error("ItemTags.SendAll", e);
            }
        }

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, new DOLEventHandler((ev, s, a) =>
            {
                if (s is GamePlayer p)
                    new ECSGameTimer(p, _ => { SendAll(p); return 0; }, 2000);
            }));
        }
    }
}
