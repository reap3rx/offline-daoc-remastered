using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.Logging;

namespace DOL.GS;

/// <summary>
/// Treasure chests (owner 2026-11-11): 30 to a zone in the outdoor PvE zones, out of towns, mostly at monster camps and
/// in interesting places (ridges, coasts, the wild). Open one (use it) for a piece of armour for your class at the
/// chest's level and of high quality, coin (ten times a monster's drop of that level) and some experience (about half a
/// bubble). The chest's level is yours, held down to just above the zone's in an easy zone ("a chest in Lough Derg
/// still gives something, but not as good as one in the Cursed Forest") and nudged up a little in a hard one. One chest
/// in a hundred is trapped: a burst of fire that kills everyone close by. An opened chest is gone; its place fills again
/// somewhere else in the zone after 1 to 4 hours. Bots open the chests they come across.
/// Chests appear zone by zone over the first minutes after a start (the spots are found on the navigation mesh).
/// </summary>
public static class TreasureChests
{
    private static readonly Logger Log = LoggerManager.Create(typeof(TreasureChests));

    public const int PerZone = 30;
    public const ushort Model = 1596;                         // objects.csv: Treasure Chest
    public const int TrapOneIn = 100;
    public const ushort TrapRadius = 350;
    public const ushort TrapEffect = 11116;                   // a ring of fire (the client's spell effect)
    public const ushort OpenRange = 300;
    public const ushort BotReach = 450;                       // a bot passing this close opens it
    public const float TownMargin = 1500;
    public static readonly TimeSpan RespawnMin = TimeSpan.FromHours(1);
    public static readonly TimeSpan RespawnMax = TimeSpan.FromHours(4);

    private sealed class ZoneState
    {
        public Zone Zone;
        public List<WorldFeatureSpots.Spot> Pool = [];
        public int Level;                                      // the zone's typical monster level
        public readonly List<TreasureChest> Live = [];
        public readonly List<long> Pending = [];               // ticks when an opened chest's place fills again
    }

    private static readonly List<ZoneState> Zones = [];
    private static readonly Queue<Zone> ToPrepare = new();
    private static readonly ConcurrentQueue<ZoneState> Ready = new();      // pools found on a worker, to stock
    private static int _slice;
    private static readonly object Sync = new();
    private static readonly Random Rng = new();

    [GameServerStartedEvent]
    public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
    {
        try
        {
            foreach (Zone zone in WorldFeatureSpots.OutdoorPveZones())
                ToPrepare.Enqueue(zone);
            Log.Info($"TREASURE chests: {ToPrepare.Count} zones to stock ({PerZone} each): " +
                     string.Join(", ", ToPrepare.Select(z => z.Description)));
            _ = new ECSGameTimer(null, Tick, 2_000);
        }
        catch (Exception exception)
        {
            Log.Error("Treasure chests failed to start", exception);
        }
    }

    private static int Tick(ECSGameTimer timer)
    {
        try
        {
            long now = GameLoop.GameLoopTime;
            // a zone a tick: its monsters read here, its spots found on a worker, its chests placed when they are ready
            if (ToPrepare.Count > 0)
                Prepare(ToPrepare.Dequeue());
            if (Ready.TryDequeue(out ZoneState ready))
            {
                lock (Sync)
                    Zones.Add(ready);
                for (int i = 0; i < PerZone; i++)
                    SpawnOne(ready);
            }
            ZoneState[] zones;
            lock (Sync)
                zones = Zones.ToArray();
            // a fifth of the zones a tick (each every 10 s): refills, and bots passing a chest
            _slice = (_slice + 1) % 5;
            lock (Sync)
            for (int zi = _slice; zi < zones.Length; zi += 5)
            {
                ZoneState z = zones[zi];
                z.Live.RemoveAll(c => c.ObjectState != GameObject.eObjectState.Active && !c.Opened);
                for (int k = z.Pending.Count - 1; k >= 0; k--)
                {
                    if (now < z.Pending[k])
                        continue;
                    z.Pending.RemoveAt(k);
                    SpawnOne(z);
                }
                foreach (TreasureChest chest in z.Live.ToArray())
                {
                    if (chest.Opened || chest.ObjectState != GameObject.eObjectState.Active)
                        continue;
                    foreach (GameNPC n in chest.GetNPCsInRadius(BotReach))
                    {
                        if (n is GameBot bot && bot.IsAutonomousWorldBot && !bot.IsTemporaryGroupHelper && bot.IsAlive &&
                            !bot.InCombat && bot.ObjectState == GameObject.eObjectState.Active)
                        {
                            Open(chest, bot);
                            break;
                        }
                    }
                }
            }
        }
        catch (Exception exception)
        {
            Log.Error("Treasure chest tick failed", exception);
        }
        return 2_000;
    }

    private static void Prepare(Zone zone)
    {
        var z = new ZoneState { Zone = zone };
        GameNPC[] mobs = zone.GetNPCsOfZone(eRealm.None).Where(n => n != null && n.Level > 0 && n is not GameBot).ToArray();
        z.Level = mobs.Length == 0 ? 10 : (int)Math.Round(mobs.Select(n => (double)n.Level).OrderBy(l => l).ElementAt(mobs.Length / 2));
        System.Numerics.Vector3[] camps = WorldFeatureSpots.CampsOf(zone);
        int seed = Rng.Next();
        System.Threading.Tasks.Task.Run(() =>
        {
            try
            {
                // the spots: three times as many at monster camps as in the wild, twice at ridges and coasts
                List<WorldFeatureSpots.Spot> spots = WorldFeatureSpots.Sample(zone, 160, TownMargin, new Random(seed), camps);
                if (spots.Count == 0)
                    return;
                foreach (WorldFeatureSpots.Spot s in spots)
                {
                    int copies = s.Kind switch { WorldFeatureSpots.Kind.Camp => 3, WorldFeatureSpots.Kind.Wild => 1, _ => 2 };
                    for (int c = 0; c < copies; c++)
                        z.Pool.Add(s);
                }
                Ready.Enqueue(z);
            }
            catch (Exception exception)
            {
                Log.Warn($"Treasure spots for {zone.Description}: {exception.Message}");
            }
        });
    }

    private static void SpawnOne(ZoneState z)
    {
        for (int attempt = 0; attempt < 12; attempt++)
        {
            WorldFeatureSpots.Spot s = z.Pool[Rng.Next(z.Pool.Count)];
            if (z.Live.Any(c => c.ObjectState == GameObject.eObjectState.Active &&
                                (long)(c.X - s.Pos.X) * (c.X - s.Pos.X) + (long)(c.Y - s.Pos.Y) * (c.Y - s.Pos.Y) < 1500L * 1500))
                continue;                                            // (not two together)
            var chest = new TreasureChest(z.Level, Rng.Next(TrapOneIn) == 0)
            {
                X = (int)s.Pos.X, Y = (int)s.Pos.Y, Z = (int)s.Pos.Z, Heading = (ushort)Rng.Next(4096),
                CurrentRegionID = z.Zone.ZoneRegion.ID,
            };
            if (!chest.AddToWorld())
                continue;
            chest.State = z;
            z.Live.Add(chest);
            return;
        }
        z.Pending.Add(GameLoop.GameLoopTime + 10 * 60_000);         // (no room just now: try again in a while)
    }

    // ---------------------------------------------------------------- opening one

    /// <summary>`who` opens the chest: the trap, or the loot. True when it opened.</summary>
    public static bool Open(TreasureChest chest, GameLiving who)
    {
        lock (chest.OpenLock)
        {
            if (chest.Opened || chest.ObjectState != GameObject.eObjectState.Active)
                return false;
            chest.Opened = true;
        }
        chest.RemoveFromWorld();
        if (chest.State is ZoneState z)
        {
            lock (Sync)
            {
                z.Live.Remove(chest);
                long wait = (long)(RespawnMin.TotalMilliseconds + Rng.NextDouble() * (RespawnMax - RespawnMin).TotalMilliseconds);
                z.Pending.Add(GameLoop.GameLoopTime + wait);
            }
        }
        if (chest.Trapped)
        {
            Spring(chest, who);
            return true;
        }
        Loot(chest, who);
        return true;
    }

    private static void Spring(TreasureChest chest, GameLiving opener)
    {
        Log.Info($"TREASURE trap sprung by {opener.Name} region={chest.CurrentRegionID} at {chest.X},{chest.Y}");
        var victims = new List<GameLiving> { opener };
        foreach (GamePlayer p in WorldMgr.GetPlayersCloseToSpot(chest.CurrentRegionID, chest.X, chest.Y, chest.Z, TrapRadius))
            if (!victims.Contains(p)) victims.Add(p);
        foreach (GameNPC n in WorldMgr.GetNPCsCloseToSpot(chest.CurrentRegionID, chest.X, chest.Y, chest.Z, TrapRadius))
            if (n is GameBot && !victims.Contains(n)) victims.Add(n);
        foreach (GameLiving v in victims.Where(v => v.IsAlive))
        {
            foreach (GamePlayer viewer in v.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                viewer.Out.SendSpellEffectAnimation(v, v, TrapEffect, 0, false, 1);
            if (v is GamePlayer vp)
                vp.Out.SendMessage("The chest was trapped! A burst of fire engulfs you!", eChatType.CT_YouWereHit, eChatLoc.CL_SystemWindow);
            v.TakeDamage(chest, eDamageType.Heat, v.Health + v.MaxHealth, 0);
        }
    }

    /// <summary>The chest's level for `who`: theirs, held to just above the zone's in an easy zone, a little above
    /// theirs in a hard one. scale: what the coin and experience are worth against a chest of their own level.</summary>
    public static (int Level, double Scale) LevelFor(int playerLevel, int zoneLevel)
    {
        playerLevel = Math.Clamp(playerLevel, 1, 50);
        zoneLevel = Math.Clamp(zoneLevel, 1, 50);
        if (playerLevel > zoneLevel + 2)
        {
            int level = Math.Min(50, zoneLevel + 2);
            double scale = Math.Max(0.15, Math.Pow((double)level / playerLevel, 2));
            return (level, scale);
        }
        if (playerLevel < zoneLevel - 2)
            return (Math.Min(50, playerLevel + 2 + Math.Min(3, (zoneLevel - playerLevel) / 5)), 1.25);
        return (Math.Min(50, playerLevel + 1), 1.0);
    }

    public static long CoinFor(int level, double scale, Random rng)
    {
        int lvl = Math.Max(1, level + 1);
        double mob = (2 + lvl * lvl * lvl / 8.0) * 1.25 * ServerProperties.Properties.MONEY_DROP;   // a monster's average drop
        return Math.Max(1, (long)(mob * 10 * scale * (0.75 + rng.NextDouble() * 0.5)));
    }

    public static long ExperienceFor(long nextLevelXp, long thisLevelXp, double scale, Random rng)
    {
        double bubble = Math.Max(0, nextLevelXp - thisLevelXp) / 10.0;
        return (long)(bubble * (0.3 + rng.NextDouble() * 0.4) * scale);   // about half a bubble
    }

    private static readonly int[] ArmorSlots =
        [(int)eInventorySlot.HeadArmor, (int)eInventorySlot.HandsArmor, (int)eInventorySlot.FeetArmor,
         (int)eInventorySlot.TorsoArmor, (int)eInventorySlot.LegsArmor, (int)eInventorySlot.ArmsArmor];

    private static void Loot(TreasureChest chest, GameLiving who)
    {
        int whoLevel = who.Level;
        (int level, double scale) = LevelFor(whoLevel, chest.ZoneLevel);
        long coin = CoinFor(level, scale, Rng);
        DbItemTemplate armor = Armor(who, level);
        if (who is GamePlayer player)
        {
            player.Out.SendMessage("You open the treasure chest!", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            if (armor != null)
            {
                DbInventoryItem item = GameInventoryItem.Create(armor);
                if (player.Inventory.AddItem(eInventorySlot.FirstEmptyBackpack, item))
                {
                    InventoryLogging.LogInventoryAction(chest, player, eInventoryActionType.Loot, item.Template, 1);
                    player.Out.SendMessage($"You find {item.Name} in the chest.", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                }
                else
                    player.Out.SendMessage("Your backpack is full - you leave the armor behind.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            }
            player.AddMoney(coin, "You find {0} in the chest.");
            InventoryLogging.LogInventoryAction(chest, player, eInventoryActionType.Loot, coin);
            long xp = ExperienceFor(player.ExperienceForNextLevel, player.ExperienceForCurrentLevel, scale, Rng);
            if (xp > 0 && player.Level < 50)
                player.GainExperience(eXPSource.Other, xp);
            return;
        }
        if (who is GameBot bot && bot.IsAutonomousWorldBot)
        {
            AutonomousBotEconomy.AddMoney(bot.DatabaseID, coin);
            if (armor != null && bot.Inventory != null)
            {
                DbInventoryItem item = GameInventoryItem.Create(armor);
                if (bot.Inventory.AddItem(eInventorySlot.FirstEmptyBackpack, item))
                {
                    AutonomousBotEconomy.MarkInventoryChanged(bot);
                    try { AutonomousBotEconomy.TryEquipOwnedUpgrade(bot, item, "treasure"); }
                    catch (Exception) { /* kept in the backpack */ }
                }
            }
            long xp = ExperienceFor(GamePlayer.GetExperienceAmountForLevel(bot.Level), GamePlayer.GetExperienceAmountForLevel(bot.Level - 1), scale, Rng);
            if (xp > 0)
                bot.GainExperience(new GainedExperienceEventArgs(xp, 0, 0, 0, 0, 0, false, false, eXPSource.Other));
            bot.MarkAutonomousStateDirty();
            AutonomousBotStatusPersistence.Queue(bot, true);
            if (bot.PersistentRecord != null)
                bot.PersistentRecord.Activity = "Found a treasure chest";
            if (Rng.Next(3) == 0)
                bot.Say(Rng.Next(3) switch { 0 => "Ha! Treasure!", 1 => "Now what have we here...", _ => "A lucky find, this." });
            Log.Info($"TREASURE opened by bot {bot.Name} level={bot.Level} chestLevel={level} coin={coin}");
        }
    }

    /// <summary>A piece of armour `who` can wear, of the chest's level and high quality (the world's random item maker).</summary>
    private static DbItemTemplate Armor(GameLiving who, int level)
    {
        try
        {
            var cls = (eCharacterClass)(who is GamePlayer p ? p.CharacterClass.ID : who is GameBot b ? b.CharacterClass.ID : 0);
            eRealm realm = who.Realm is eRealm.Albion or eRealm.Midgard or eRealm.Hibernia ? who.Realm : eRealm.Albion;
            byte lvl = (byte)Math.Clamp(level, 1, 51);
            eObjectType type = realm switch
            {
                eRealm.Midgard => GeneratedUniqueItem.GetMidgardArmorType(cls, lvl),
                eRealm.Hibernia => GeneratedUniqueItem.GetHiberniaArmorType(cls, lvl),
                _ => GeneratedUniqueItem.GetAlbionArmorType(cls, lvl),
            };
            var slot = (eInventorySlot)ArmorSlots[Rng.Next(ArmorSlots.Length)];
            DbItemTemplate t = new GeneratedUniqueItem(false, realm, cls, lvl, type, slot);
            t.Quality = Rng.Next(96, 101);
            t.Condition = t.MaxCondition;
            t.Durability = t.MaxDurability;
            t.AllowAdd = true;          // kept with the item (a rolled one-off is never written without it: the chests'
                                        // armour came back "(blank item)" after a restart - owner 2026-11-14)
            return t;
        }
        catch (Exception exception)
        {
            Log.Warn($"Treasure armor for {who.Name}: {exception.Message}");
            return null;
        }
    }
}

/// <summary>A treasure chest in the world: use it to open it (TreasureChests).</summary>
public class TreasureChest : GameStaticItem
{
    public int ZoneLevel { get; }
    public bool Trapped { get; }
    public bool Opened { get; set; }
    public object State { get; set; }
    public readonly object OpenLock = new();

    public TreasureChest(int zoneLevel, bool trapped)
    {
        ZoneLevel = zoneLevel;
        Trapped = trapped;
        Model = TreasureChests.Model;
        Name = "Treasure Chest";
        LoadedFromScript = true;
    }

    public override bool Interact(GamePlayer player)
    {
        if (!base.Interact(player))
            return false;
        if (!player.IsAlive)
            return false;
        if (!IsWithinRadius(player, TreasureChests.OpenRange))
        {
            player.Out.SendMessage("You are too far away to open the chest.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            return false;
        }
        return TreasureChests.Open(this, player);
    }
}
