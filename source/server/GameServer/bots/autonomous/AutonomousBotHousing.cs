using System;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.Events;
using DOL.GS.Housing;
using DOL.GS.ServerProperties;
using DOL.Logging;

namespace DOL.GS;

/// <summary>
/// World bots and player housing (owner 2026-11-02: "All that would need to happen is bots building some houses in
/// the zones ... start with them just buying and placing some housing in some of the lots when they have sufficient
/// funds, and buying/placing/using consignment merchants").
///
/// Once a minute: a world bot of level 30 or more that owns no house and has saved enough for a lot, a deed, a few
/// weeks' rent and a reserve buys a free lot in its realm's housing (near the gate the classic zone leads in by, so
/// the houses gather where players arrive) and builds the biggest house it can afford (cottage, house, villa,
/// mansion), in its own looks. One with money to spare adds a porch and a consignment merchant, puts a few of its
/// backpack finds on it for sale, and collects what sells. Its lockbox is kept topped up from its savings, so the
/// server's rent never repossesses it while the bot has money. The house is the server's own (DbHouse, HouseMgr):
/// players see, visit and shop at it like any other; its OwnerID is the bot's market owner id
/// (AutonomousBotEconomy.GetOwnerId), so the consignment merchant shows the bot's listings.
/// </summary>
public static class AutonomousBotHousing
{
    private static readonly Logger log = LoggerManager.Create(typeof(AutonomousBotHousing));
    private const int TickMs = 60_000;
    private const int FirstTickMs = 120_000;
    private const int MinLevel = 30;
    private const int MaxBuysPerTick = 2;
    private const long Gold = 10_000;
    private const long Reserve = 200 * Gold;
    private const int RentWeeksUpFront = 4;
    private const long PorchAndConsignmentCost = 300 * Gold;    // the porch and consignment deeds' worth, roughly
    private const long ConsignmentMinimumSavings = 600 * Gold;  // left after the house, to want a shop as well
    private const int MaxConsignmentListings = 6;
    private const int NeighbourhoodLots = 80;                   // the nearest free lots to the gate it picks among
    private static readonly string[] Sizes = { "cottage", "house", "villa", "mansion" };
    private static readonly Random Rng = new();

    // the housing gate's arrival point per realm (ZonePoints 111 / 112 / 113: Caerwent, Erikstaad, Meath)
    private static readonly Dictionary<eRealm, (ushort Region, int X, int Y, string Prefix, int ModelBase)> Realms = new()
    {
        [eRealm.Albion] = (2, 585030, 561505, "alb", 1),
        [eRealm.Midgard] = (102, 526393, 561724, "mid", 5),
        [eRealm.Hibernia] = (202, 555546, 526065, "hib", 9),
    };

    [GameServerStartedEvent]
    public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
    {
        new ECSGameTimer(null, Tick, FirstTickMs);
    }

    private static int Tick(ECSGameTimer timer)
    {
        try
        {
            KeepHouses();
            int bought = 0;
            foreach (GameBot bot in AutonomousBotRegistry.Snapshot().OrderBy(_ => Rng.Next()))
            {
                if (bought >= MaxBuysPerTick)
                    break;
                if (TryBuyHouse(bot))
                    bought++;
            }
        }
        catch (Exception ex)
        {
            log.Error("AUTONOMOUS_HOUSING tick failed", ex);
        }
        return TickMs;
    }

    /// <summary>The house a bot owns, or null.</summary>
    public static House HouseOf(GameBot bot)
    {
        if (bot == null || bot.DatabaseID <= 0 || !Realms.TryGetValue(bot.Realm, out var r))
            return null;
        string owner = AutonomousBotEconomy.GetOwnerId(bot.DatabaseID);
        IDictionary<int, House> houses = HouseMgr.GetHouses(r.Region);
        return houses?.Values.FirstOrDefault(h => h.OwnerID == owner);
    }

    private static long Rent(int model) => HouseMgr.GetRentByModel(model);

    private static long DeedPrice(string realm, string size)
    {
        DbItemTemplate t = GameServer.Database.FindObjectByKey<DbItemTemplate>($"housing_{realm}_{size}_deed");
        return t?.Price ?? 0;
    }

    public static bool TryBuyHouse(GameBot bot)
    {
        if (bot?.IsAutonomousWorldBot != true || bot.IsTemporaryGroupHelper || bot.DatabaseID <= 0 || bot.Level < MinLevel ||
            bot.InCombat || !Realms.TryGetValue(bot.Realm, out var r) || HouseOf(bot) != null)
            return false;
        long money = AutonomousBotEconomy.GetMoney(bot.DatabaseID);
        if (money < 1000 * Gold)                               // (the cheapest cottage and its lot are over 1,300 gold)
            return false;
        Region region = WorldMgr.GetRegion(r.Region);
        if (region == null)
            return false;
        List<GameLotMarker> free = region.Objects.OfType<GameLotMarker>()
            .Where(m => m.ObjectState == GameObject.eObjectState.Active && m.DatabaseItem != null &&
                        string.IsNullOrEmpty(m.DatabaseItem.OwnerID))
            .OrderBy(m => (long)(m.X - r.X) * (m.X - r.X) + (long)(m.Y - r.Y) * (m.Y - r.Y))
            .Take(NeighbourhoodLots).ToList();
        if (free.Count == 0)
            return false;
        GameLotMarker marker = free[Rng.Next(free.Count)];
        DbHouse lot = marker.DatabaseItem;
        long lotPrice = HouseTemplateMgr.GetLotPrice(lot);
        // the biggest house it can afford with rent up front and a reserve kept
        int size = -1;
        long deed = 0;
        for (int s = Sizes.Length - 1; s >= 0; s--)
        {
            long d = DeedPrice(r.Prefix, Sizes[s]);
            if (d > 0 && money >= lotPrice + d + Rent(r.ModelBase + s) * RentWeeksUpFront + Reserve)
            {
                size = s;
                deed = d;
                break;
            }
        }
        if (size < 0)
            return false;
        int model = r.ModelBase + size;
        long rentUpFront = Rent(model) * RentWeeksUpFront;
        long total = lotPrice + deed + rentUpFront;
        lock (lot)
        {
            if (!string.IsNullOrEmpty(lot.OwnerID) || !AutonomousBotEconomy.TrySpend(bot.DatabaseID, total))
                return false;
            lot.OwnerID = AutonomousBotEconomy.GetOwnerId(bot.DatabaseID);
            lot.Name = bot.Name;
            lot.Model = model;
            lot.LastPaid = DateTime.Now;
            lot.KeptMoney = rentUpFront;
            lot.RoofMaterial = Rng.Next(3);
            lot.WallMaterial = Rng.Next(3);
            lot.DoorMaterial = Rng.Next(4);
            lot.TrussMaterial = Rng.Next(10);
            lot.WindowMaterial = 0;
            lot.Porch = false;
            var house = new House(lot);
            HouseMgr.AddHouse(house);
            foreach (GamePlayer p in marker.GetPlayersInRadius(500))
                house.Exit(p, true);
            marker.RemoveFromWorld();
            marker.Delete();
            if (bot.PersistentRecord != null)
                bot.PersistentRecord.Activity = $"Bought a {Sizes[size]} in housing (lot {lot.HouseNumber})";
            bot.MarkAutonomousStateDirty();
            AutonomousBotStatusPersistence.Queue(bot, true);
            log.Info($"AUTONOMOUS_HOUSE_BOUGHT bot=\"{bot.Name}\" level={bot.Level} realm={bot.Realm} lot={lot.HouseNumber} " +
                     $"house={Sizes[size]} model={model} paid={total / Gold}g left={(money - total) / Gold}g");
            if (money - total >= ConsignmentMinimumSavings + PorchAndConsignmentCost)
                TryOpenShop(bot, house);
            return true;
        }
    }

    /// <summary>A porch and a consignment merchant on it (the porch and consignment deeds' worth spent).</summary>
    public static bool TryOpenShop(GameBot bot, House house)
    {
        if (house == null || house.ConsignmentMerchant != null || !AutonomousBotEconomy.TrySpend(bot.DatabaseID, PorchAndConsignmentCost))
            return false;
        if (!house.Porch)
            house.AddPorch();
        if (!house.AddConsignment(0))
        {
            AutonomousBotEconomy.AddMoney(bot.DatabaseID, PorchAndConsignmentCost);
            return false;
        }
        log.Info($"AUTONOMOUS_HOUSE_SHOP bot=\"{bot.Name}\" lot={house.HouseNumber}");
        StockShop(bot, house);
        return true;
    }

    /// <summary>
    /// Every bot house: rent kept paid from the bot's savings, the shop's takings collected, the shop restocked from
    /// the bot's backpack while the bot is in the world.
    /// </summary>
    private static void KeepHouses()
    {
        foreach (var r in Realms.Values)
        {
            IDictionary<int, House> houses = HouseMgr.GetHouses(r.Region);
            if (houses == null)
                continue;
            foreach (House house in houses.Values.ToList())
            {
                if (house.Model <= 0 || !AutonomousBotEconomy.TryParseOwnerId(house.OwnerID, out long botId))
                    continue;
                long rent = Rent(house.Model);
                if (house.KeptMoney < rent * 2 && AutonomousBotEconomy.TrySpend(botId, rent * 2))
                {
                    house.KeptMoney += rent * 2;
                    house.SaveIntoDatabase();
                }
                GameConsignmentMerchant cm = house.ConsignmentMerchant;
                if (cm != null && cm.TotalMoney > 0)
                {
                    long takings = cm.TotalMoney;
                    cm.TotalMoney = 0;
                    AutonomousBotEconomy.AddMoney(botId, takings);
                    log.Info($"AUTONOMOUS_HOUSE_TAKINGS lot={house.HouseNumber} owner={house.Name} copper={takings}");
                }
                if (cm != null && AutonomousBotRegistry.TryGet(botId, out GameBot bot) && bot != null)
                    StockShop(bot, house);
            }
        }
    }

    /// <summary>Up to MaxConsignmentListings of the bot's more valuable backpack finds on its consignment merchant.</summary>
    private static void StockShop(GameBot bot, House house)
    {
        if (bot?.Inventory == null || house?.ConsignmentMerchant == null || bot.InCombat)
            return;
        string owner = AutonomousBotEconomy.GetOwnerId(bot.DatabaseID);
        lock (RealmExchangeBroker.TransactionLock)
        lock (AutonomousBotStatusPersistence.DatabaseWriteLock)
        {
            var used = MarketCache.SearchItems(new ItemQuery { Owner = owner }).Select(i => i.SlotPosition).ToHashSet();
            int onSale = MarketCache.SearchItems(new ItemQuery { Owner = owner }).Count(i => i.OwnerLot == house.HouseNumber);
            if (onSale >= MaxConsignmentListings)
                return;
            var candidates = bot.Inventory.AllItems
                .Where(i => i != null && i.IsTradable && !string.IsNullOrWhiteSpace(i.Name) && i.OwnerLot == 0 &&
                            i.SlotPosition >= (int)eInventorySlot.FirstBackpack && i.SlotPosition <= (int)eInventorySlot.LastBackpack &&
                            i.IsPersisted && !BotSiegeRuntime.IsSupply(i.Id_nb) &&
                            !AutonomousBotEconomy.TryGetEquipmentUpgrade(bot, i, out _))
                .Select(i => (Item: i, Price: AutonomousBotEconomy.RecommendListingPrice(i)))
                .Where(c => c.Price >= Math.Max(100, c.Item.Level * c.Item.Level * 6))
                .OrderByDescending(c => c.Price)
                .Take(MaxConsignmentListings - onSale)
                .ToList();
            foreach (var (item, price) in candidates)
            {
                int slot = -1;
                for (int s = (int)eInventorySlot.Consignment_First; s <= (int)eInventorySlot.Consignment_Last; s++)
                    if (!used.Contains(s)) { slot = s; break; }
                if (slot < 0 || !bot.Inventory.RemoveItemWithoutDbDeletion(item))
                    break;
                int was = item.SlotPosition;
                item.OwnerID = owner;
                item.OwnerLot = (ushort)house.HouseNumber;
                item.SlotPosition = slot;
                item.SellPrice = price;
                if (!GameServer.Database.SaveObject(item))
                {
                    item.OwnerLot = 0;
                    item.SellPrice = 0;
                    bot.Inventory.AddItem((eInventorySlot)was, item);
                    continue;
                }
                used.Add(slot);
                MarketCache.AddItem(item);
                log.Info($"AUTONOMOUS_HOUSE_LISTED bot=\"{bot.Name}\" lot={house.HouseNumber} item=\"{item.Name}\" price={price}");
            }
            if (candidates.Count > 0)
            {
                AutonomousBotEconomy.MarkInventoryChanged(bot);
                bot.MarkAutonomousStateDirty();
                AutonomousBotStatusPersistence.Queue(bot, true);
            }
        }
    }
}
