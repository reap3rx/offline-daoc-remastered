using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.Logging;

namespace DOL.GS.Mounts
{
    /// <summary>
    /// A horse dealer (owner 2026-11-02, mounts' first pass: "get the mounts workable first"). The database has the
    /// horses (Item_Type 9: the Horse slot, SPD_ABS the horse's look, Level the rider's level and its speed tier -
    /// ControlledHorse.Speed: MOUNT_UNDER_LEVEL_35_SPEED / MOUNT_OVER_LEVEL_35_SPEED) but nobody sold them. A dealer
    /// stands beside every stable master; /summon (or /mount, or the client's Mount key) puts a bought horse into the
    /// Horse slot and calls it (a five-second whistle, standing still, out of combat).
    /// </summary>
    public class MountDealer : GameMerchant
    {
        public override bool Interact(GamePlayer player)
        {
            if (!base.Interact(player))
                return false;
            player.Out.SendMessage($"{Name} says, \"A good horse halves the road. Buy one, then /summon it (or press your Mount key) " +
                                   "standing still, out of a fight.\"", eChatType.CT_Say, eChatLoc.CL_ChatWindow);
            return true;
        }
    }

    public static class MountDealers
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        /// <summary>The dealers' stock: page 0, cheapest first (template ids of the database's horses).</summary>
        public static readonly string[] Stock =
        {
            // level 10 (the slower tier, 100 gold)
            "brownstandardmount", "blackstandardmount", "greystandardmount", "spottedstandardmount", "chocolatestandardmount",
            "clydesdalestandardmount", "dappledgreystandardmount", "appalossastandardmount", "leopardstandardmount",
            // level 20 (200 gold)
            "palominomount", "chocolatemount", "leopardmount", "primitivedunmount", "reddunmount", "shiredappledmount",
            // level 50 heavy horses (the faster tier, 350 gold)
            "brownheavymount", "blackheavymount", "greyheavymount", "spottedheavymount", "palominoheavymount",
            "chocolateheavymount", "clydesdaleheavymount", "appaloosaheavymount", "redunheavymount",
        };

        /// <summary>
        /// The look each horse sold here shows (gamedata horsemap.csv ID, ControlledHorse's horse byte). The database's
        /// horses carry ids that don't match their names (its "Palomino Mount" was a palomino unicorn, its "Brown Standard
        /// Mount" a chocolate heavy horse); the dealers' stock is set right here, in memory, at startup.
        /// </summary>
        private static readonly Dictionary<string, int> Looks = new()
        {
            ["brownstandardmount"] = 1, ["blackstandardmount"] = 2, ["greystandardmount"] = 4, ["spottedstandardmount"] = 6,
            ["chocolatestandardmount"] = 7, ["clydesdalestandardmount"] = 8, ["appalossastandardmount"] = 9,
            ["dappledgreystandardmount"] = 10, ["leopardstandardmount"] = 11,
            ["palominomount"] = 5, ["chocolatemount"] = 7, ["leopardmount"] = 11, ["primitivedunmount"] = 12,
            ["reddunmount"] = 13, ["shiredappledmount"] = 14,
            ["brownheavymount"] = 17, ["blackheavymount"] = 18, ["greyheavymount"] = 20, ["palominoheavymount"] = 21,
            ["spottedheavymount"] = 22, ["chocolateheavymount"] = 23, ["clydesdaleheavymount"] = 24,
            ["appaloosaheavymount"] = 25, ["redunheavymount"] = 28,
        };

        private static MerchantTradeItems _items;
        private static readonly List<MountDealer> _dealers = new();

        public static IReadOnlyList<MountDealer> Dealers => _dealers;

        public static MerchantTradeItems Items
        {
            get
            {
                if (_items != null)
                    return _items;
                var items = new MerchantTradeItems(null);
                int slot = 0;
                foreach (string id in Stock)
                {
                    DbItemTemplate t = GameServer.Database.FindObjectByKey<DbItemTemplate>(id);
                    if (t == null || t.Item_Type != (int)eInventorySlot.Horse)
                        continue;
                    if (Looks.TryGetValue(id, out int look))
                        t.SPD_ABS = look;
                    items.AddTradeItem(0, (eMerchantWindowSlot)slot++, t);
                }
                _items = items;
                return items;
            }
        }

        /// <summary>The horses a bot of this level can ride, cheapest first.</summary>
        public static IEnumerable<DbItemTemplate> Affordable(int level) =>
            Items.GetAllItems().Values.OfType<DbItemTemplate>().Where(t => t.Level <= level).OrderBy(t => t.Price);

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Spawn();
            }
            catch (Exception ex)
            {
                log.Error("MOUNT_DEALERS spawn failed", ex);
            }
        }

        public static void Spawn()
        {
            if (Items.GetAllItems().Count == 0)
            {
                log.Warn("MOUNT_DEALERS no horse templates found - no dealers");
                return;
            }
            int n = 0;
            foreach (Region region in WorldMgr.GetAllRegions())
            {
                foreach (GameStableMaster master in region.Objects.OfType<GameStableMaster>().ToList())
                {
                    if (master.ObjectState != GameObject.eObjectState.Active || master is null)
                        continue;
                    // beside the stable master, on its left
                    Point2D at = master.GetPointFromHeading((ushort)((master.Heading + 1024) % 4096), 110);
                    var dealer = new MountDealer
                    {
                        Name = "Horse Dealer",
                        GuildName = "Horses",
                        Model = master.Model,
                        Size = master.Size,
                        Level = master.Level,
                        Realm = master.Realm,
                        Flags = master.Flags,
                        X = at.X,
                        Y = at.Y,
                        Z = master.Z,
                        Heading = master.Heading,
                        CurrentRegion = master.CurrentRegion,
                        TradeItems = Items,
                        LoadedFromScript = true,
                    };
                    if (!string.IsNullOrEmpty(master.EquipmentTemplateID))
                        dealer.LoadEquipmentTemplateFromDatabase(master.EquipmentTemplateID);
                    if (dealer.AddToWorld())
                    {
                        _dealers.Add(dealer);
                        n++;
                    }
                }
            }
            log.Info($"MOUNT_DEALERS spawned {n} horse dealers ({Items.GetAllItems().Count} horses each)");
        }
    }
}
