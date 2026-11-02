using System;
using System.Collections.Concurrent;
using System.Linq;
using DOL.Database;
using DOL.GS.Mounts;
using DOL.GS.PacketHandler;
using DOL.Logging;

namespace DOL.GS;

/// <summary>
/// World bots and their horses (owner 2026-11-02: "Bots will need to want to purchase and use mounts too").
/// Buying: a bot level 10 or more with no horse, standing within reach of a horse dealer (MountDealers: beside every
/// stable master, where bots board their routes) and with comfortably more saved copper than the horse costs, buys the
/// best one it can ride (it goes into its Horse slot, persisted with the rest of its inventory).
/// Riding: after walking on for a few seconds out of combat where a horse may be ridden (not dungeons, instances,
/// capitals, nor RvR unless the horse is above level 35 - the players' ReasonForDisallowMounting), it whistles and
/// rides at the horse's speed (MaxSpeedCalculator: the player's out-of-combat run x the horse); it gets off in any
/// fight, cast, stable route, stealth, or after standing a while. Clients see the horse through ControlledHorse (0x4E)
/// with the bot's object id, refreshed every few seconds for new viewers.
/// </summary>
public static class AutonomousBotMounts
{
    private sealed class State
    {
        public long NextTick;
        public long MovingSince;
        public long StillSince;
        public long NextRefresh;
        public long NextShop;
    }

    private static readonly Logger log = LoggerManager.Create(typeof(AutonomousBotMounts));
    private static readonly ConcurrentDictionary<long, State> States = new();
    private const int MountAfterMovingMs = 3_000;
    private const int DismountAfterStillMs = 8_000;
    private const int DealerReach = 700;
    private const double PveRun = 1.25;                     // MaxSpeedCalculator's out-of-combat run (ENABLE_PVE_SPEED)

    public static void Pulse(GameBot bot)
    {
        if (bot == null || bot.ObjectState != GameObject.eObjectState.Active)
            return;
        long now = GameLoop.GameLoopTime;
        State st = States.GetOrAdd(bot.DatabaseID, _ => new State());
        if (now < st.NextTick)
            return;
        st.NextTick = now + 1_000;

        DbInventoryItem horse = bot.Inventory?.GetItem(eInventorySlot.Horse);
        if (horse == null)
        {
            if (bot.IsOnPersonalMount)
                Dismount(bot);
            if (now >= st.NextShop)
            {
                st.NextShop = now + 5_000 + bot.ObjectID % 2_000;
                TryBuyFromNearbyDealer(bot);
            }
            return;
        }

        if (bot.IsMoving)
        {
            st.StillSince = 0;
            if (st.MovingSince == 0)
                st.MovingSince = now;
        }
        else
        {
            st.MovingSince = 0;
            if (st.StillSince == 0)
                st.StillSince = now;
        }

        if (bot.IsOnPersonalMount)
        {
            if (MustDismount(bot) || !MayRideHere(bot, horse) || st.StillSince != 0 && now - st.StillSince > DismountAfterStillMs)
                Dismount(bot);
            else if (now >= st.NextRefresh)
            {
                st.NextRefresh = now + 4_000;
                Broadcast(bot, bot.PersonalMountId);
            }
        }
        else if (st.MovingSince != 0 && now - st.MovingSince > MountAfterMovingMs && !MustDismount(bot) &&
                 MayRideHere(bot, horse) && bot.Level >= horse.Level)
        {
            Mount(bot, horse);
            st.NextRefresh = now + 4_000;
        }
    }

    /// <summary>
    /// A companion (a bot in a player's group): it rides when its player rides - the same horse's look and speed, so
    /// it keeps up - and gets off with them or in any fight. It needs no horse of its own.
    /// </summary>
    public static void PulseCompanion(GameBot bot)
    {
        if (bot == null || bot.ObjectState != GameObject.eObjectState.Active || !(bot.IsTemporaryGroupHelper || bot.IsPlayerLedGroup))
            return;
        long now = GameLoop.GameLoopTime;
        State st = States.GetOrAdd(bot.DatabaseID, _ => new State());
        if (now < st.NextTick)
            return;
        st.NextTick = now + 700;
        GamePlayer leader = bot.PlayerGroupLeader ?? bot.Group?.Leader;
        bool want = leader != null && leader.IsOnHorse && leader.HasHorse && leader.CurrentRegion == bot.CurrentRegion &&
                    !MustDismount(bot) && bot.IsWithinRadius(leader, 3_000);
        if (want && !bot.IsOnPersonalMount)
        {
            bot.PersonalMountId = leader.ActiveHorse.ID;
            bot.PersonalMountSpeedFactor = leader.ActiveHorse.Speed * 0.01 * PveRun;
            bot.IsOnPersonalMount = true;
            bot.OnMaxSpeedChange();
            Broadcast(bot, bot.PersonalMountId);
            st.NextRefresh = now + 4_000;
        }
        else if (!want && bot.IsOnPersonalMount)
            Dismount(bot);
        else if (want && now >= st.NextRefresh)
        {
            st.NextRefresh = now + 4_000;
            Broadcast(bot, bot.PersonalMountId);
        }
    }

    /// <summary>Gets off at once (combat, a cast, a stable route) - callers may use it before acting.</summary>
    public static void Dismount(GameBot bot)
    {
        if (bot == null || !bot.IsOnPersonalMount)
            return;
        bot.IsOnPersonalMount = false;
        bot.PersonalMountSpeedFactor = 1.0;
        bot.OnMaxSpeedChange();
        Broadcast(bot, 0);
    }

    private static void Mount(GameBot bot, DbInventoryItem horse)
    {
        byte id = (byte)(horse.SPD_ABS <= 0 ? 1 : Math.Min(255, horse.SPD_ABS));
        double horseSpeed = (horse.Level <= 35 ? ServerProperties.Properties.MOUNT_UNDER_LEVEL_35_SPEED
            : ServerProperties.Properties.MOUNT_OVER_LEVEL_35_SPEED) * 0.01;
        bot.PersonalMountId = id;
        bot.PersonalMountSpeedFactor = horseSpeed * PveRun;
        bot.IsOnPersonalMount = true;
        foreach (GamePlayer viewer in bot.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
            viewer?.Out.SendEmoteAnimation(bot, eEmote.Horse_whistle);
        bot.OnMaxSpeedChange();
        Broadcast(bot, id);
        if (FirstRides.TryAdd(bot.DatabaseID, 0))
            log.Info($"AUTONOMOUS_MOUNT_RIDE bot=\"{bot.Name}\" horse={id} speed={bot.MaxSpeed} zone=\"{bot.CurrentZone?.Description}\"");
    }

    private static readonly ConcurrentDictionary<long, byte> FirstRides = new();

    private static bool MustDismount(GameBot bot) =>
        !bot.IsAlive || bot.InCombat || bot.IsAttacking || bot.IsCasting || bot.IsOnStableMasterRoute || bot.IsOnHorse ||
        bot.IsStealthed || GameRelic.IsPlayerCarryingRelic(bot);

    private static bool MayRideHere(GameBot bot, DbInventoryItem horse)
    {
        Region region = bot.CurrentRegion;
        if (region == null || region.IsDungeon || region.IsInstance || region.IsCapitalCity)
            return false;
        if ((region.IsRvR || bot.CurrentZone?.IsRvR == true) && horse.Level <= 35)
            return false;
        return true;
    }

    /// <summary>ControlledHorse (PacketLib180's layout): the rider's object id, the horse (0: off), barding, saddle.</summary>
    private static void Broadcast(GameBot bot, byte horseId)
    {
        foreach (GamePlayer viewer in bot.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
        {
            if (viewer?.Out == null)
                continue;
            using var pak = PooledObjectFactory.GetForTick<GSTCPPacketOut>().Init(AbstractPacketLib.GetPacketCode(eServerPackets.ControlledHorse));
            pak.WriteShort((ushort)bot.ObjectID);
            pak.WriteByte(horseId);
            pak.WriteByte(0);
            pak.WriteShort(0);
            pak.WriteByte(0);
            pak.WriteByte(0);
            viewer.Out.SendTCP(pak);
        }
    }

    /// <summary>
    /// A horse dealer within reach: the best horse the bot can ride and comfortably afford (it keeps at least twice the
    /// price saved), charged from its saved copper and put in its Horse slot.
    /// </summary>
    public static bool TryBuyFromNearbyDealer(GameBot bot)
    {
        if (bot?.IsAutonomousWorldBot != true || bot.IsTemporaryGroupHelper || bot.Inventory == null || bot.Level < 10 ||
            bot.InCombat || bot.Inventory.GetItem(eInventorySlot.Horse) != null)
            return false;
        MountDealer dealer = bot.GetNPCsInRadius(DealerReach).OfType<MountDealer>()
            .FirstOrDefault(d => d.Realm == eRealm.None || d.Realm == bot.Realm);
        if (dealer == null)
            return false;
        long money = AutonomousBotEconomy.GetMoney(bot.DatabaseID);
        DbItemTemplate pick = MountDealers.Affordable(bot.Level)
            .Where(t => t.Price > 0 && money >= t.Price * 3)
            .OrderByDescending(t => t.Level).ThenBy(t => t.Price)
            .FirstOrDefault();
        if (pick == null)
            return false;
        DbInventoryItem item = GameInventoryItem.Create(pick);
        if (item == null || !AutonomousBotEconomy.TrySpend(bot.DatabaseID, pick.Price))
            return false;
        if (!bot.Inventory.AddItem(eInventorySlot.Horse, item))
        {
            AutonomousBotEconomy.AddMoney(bot.DatabaseID, pick.Price);
            return false;
        }
        AutonomousBotEconomy.MarkInventoryChanged(bot);
        bot.MarkAutonomousStateDirty();
        AutonomousBotStatusPersistence.Queue(bot, true);
        if (bot.PersistentRecord != null)
            bot.PersistentRecord.Activity = $"Bought {pick.Name} from {dealer.Name}";
        log.Info($"AUTONOMOUS_MOUNT_BOUGHT bot=\"{bot.Name}\" level={bot.Level} horse=\"{pick.Name}\" price={pick.Price}");
        return true;
    }
}
