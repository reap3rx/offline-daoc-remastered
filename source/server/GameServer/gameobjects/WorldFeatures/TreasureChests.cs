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
/// Owner 2026-11-22 (the Connacht brief): chests stand near monster spawns rather than anywhere - out in the wild only
/// when a zone has too few camps - and a chest in a harder area (the monsters round it) has a better chance at better
/// loot: more coin, finer armour, and a chance of a second piece (Danger, Bonus).
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
        public List<sbyte> Danger = [];                        // each pool spot's area: its monsters' usual con
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
        // the monsters' cons where they stand (read here, on the game loop): a spot's danger is its neighbours'
        (Vector3 Pos, sbyte Tier)[] tiers = zone.GetNPCsOfZone(eRealm.None)
            .Where(n => n != null && n.Level > 0 && n is not GameBot && (n.Flags & GameNPC.eFlags.PEACE) == 0 && !MonsterTiers.IsNamed(n.Name))
            .Select(n => (new Vector3(n.SpawnPoint.X, n.SpawnPoint.Y, n.SpawnPoint.Z), MonsterTiers.Tier(n)))
            .Where(t => t.Item2 != MonsterTiers.None && t.Item2 != MonsterTiers.Unset).ToArray();
        int seed = Rng.Next();
        System.Threading.Tasks.Task.Run(() =>
        {
            try
            {
                // the spots: near monster spawns (owner 2026-11-22) - a ridge or a coast now and then, the wild only when
                // the zone has too few camps to fill
                List<WorldFeatureSpots.Spot> spots = WorldFeatureSpots.Sample(zone, 160, TownMargin, new Random(seed), camps);
                if (spots.Count == 0)
                    return;
                int campSpots = spots.Count(s => s.Kind == WorldFeatureSpots.Kind.Camp);
                foreach (WorldFeatureSpots.Spot s in spots)
                {
                    int copies = Copies(s.Kind, campSpots);
                    sbyte danger = Danger(s.Pos, tiers);
                    for (int c = 0; c < copies; c++)
                    {
                        z.Pool.Add(s);
                        z.Danger.Add(danger);
                    }
                }
                if (z.Pool.Count == 0)
                    return;
                Ready.Enqueue(z);
            }
            catch (Exception exception)
            {
                Log.Warn($"Treasure spots for {zone.Description}: {exception.Message}");
            }
        });
    }

    /// <summary>How many times a spot goes in the pool: camps (near monster spawns) eight times, ridges and coasts once,
    /// the wild only in a zone with fewer camp spots than chests.</summary>
    public static int Copies(WorldFeatureSpots.Kind kind, int campSpots) => kind switch
    {
        WorldFeatureSpots.Kind.Camp => 8,
        WorldFeatureSpots.Kind.Wild => campSpots >= PerZone ? 0 : 1,
        _ => 1,
    };

    public const float DangerRadius = 2000;                   // the monsters within 50 m make an area's danger

    /// <summary>A spot's danger: the usual con (the median) of the monsters spawning within DangerRadius of it, named ones
    /// aside; blue when there are none.</summary>
    public static sbyte Danger(Vector3 at, (Vector3 Pos, sbyte Tier)[] tiers)
    {
        var near = tiers.Where(t => (t.Pos.X - at.X) * (t.Pos.X - at.X) + (t.Pos.Y - at.Y) * (t.Pos.Y - at.Y) < DangerRadius * DangerRadius)
            .Select(t => t.Tier).OrderBy(t => t).ToList();
        return near.Count == 0 ? MonsterTiers.Blue : near[near.Count / 2];
    }

    /// <summary>What a chest's area adds (owner 2026-11-22: "harder areas get a better chance at better loot"): coin and
    /// experience times Coin, a second piece of armour ExtraPct times in a hundred, and the armour's quality from MinQuality
    /// up. Blue and below: as before.</summary>
    public static (double Coin, int ExtraPct, int MinQuality) Bonus(sbyte danger) => danger switch
    {
        >= MonsterTiers.Red => (1.75, 50, 99),
        MonsterTiers.Orange => (1.45, 30, 98),
        MonsterTiers.Yellow => (1.2, 15, 97),
        _ => (1.0, 0, 96),
    };

    private static void SpawnOne(ZoneState z)
    {
        for (int attempt = 0; attempt < 12; attempt++)
        {
            int i = Rng.Next(z.Pool.Count);
            WorldFeatureSpots.Spot s = z.Pool[i];
            if (z.Live.Any(c => c.ObjectState == GameObject.eObjectState.Active &&
                                (long)(c.X - s.Pos.X) * (c.X - s.Pos.X) + (long)(c.Y - s.Pos.Y) * (c.Y - s.Pos.Y) < 1500L * 1500))
                continue;                                            // (not two together)
            var chest = new TreasureChest(z.Level, Rng.Next(TrapOneIn) == 0)
            {
                Danger = i < z.Danger.Count ? z.Danger[i] : MonsterTiers.Blue,
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

    /// <summary>A treasure map read (LootUses): a chest placed at one of the zone's spots 1,500 to 9,000 units from you
    /// (never trapped); null when the zone has no spots (a town, a dungeon, a zone not stocked yet).</summary>
    public static TreasureChest PlaceForMap(GamePlayer p)
    {
        ZoneState z;
        lock (Sync)
            z = Zones.FirstOrDefault(s => s.Zone == p.CurrentZone);
        if (z == null || z.Pool.Count == 0)
            return null;
        for (int attempt = 0; attempt < 40; attempt++)
        {
            int i = Rng.Next(z.Pool.Count);
            WorldFeatureSpots.Spot s = z.Pool[i];
            long d2 = (long)(s.Pos.X - p.X) * (long)(s.Pos.X - p.X) + (long)(s.Pos.Y - p.Y) * (long)(s.Pos.Y - p.Y);
            if (d2 < 1500L * 1500 || d2 > 9000L * 9000)
                continue;
            var chest = new TreasureChest(z.Level, false)
            {
                Danger = i < z.Danger.Count ? z.Danger[i] : MonsterTiers.Blue,
                X = (int)s.Pos.X, Y = (int)s.Pos.Y, Z = (int)s.Pos.Z, Heading = (ushort)Rng.Next(4096),
                CurrentRegionID = z.Zone.ZoneRegion.ID,
            };
            if (!chest.AddToWorld())
                continue;
            return chest;                                            // (yours: not the zone's thirty, and no refill once opened)
        }
        return null;
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

    /// <summary>The chest's level for `who`: always just above theirs, wherever it is (owner 2026-11-20 bugs doc: "loot
    /// that drops for you should be at level no matter where you get it, not based on zone. Includes chests"). A chest
    /// in a zone harder than you still pays a quarter more coin and experience (risk vs reward). scale: what the coin
    /// and experience are worth against a chest of their own level.</summary>
    public static (int Level, double Scale) LevelFor(int playerLevel, int zoneLevel)
    {
        playerLevel = Math.Clamp(playerLevel, 1, 50);
        zoneLevel = Math.Clamp(zoneLevel, 1, 50);
        return (Math.Min(50, playerLevel + 1), playerLevel < zoneLevel - 2 ? 1.25 : 1.0);
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
        (double bonus, int extraPct, int minQuality) = Bonus(chest.Danger);
        scale *= bonus;
        long coin = CoinFor(level, scale, Rng);
        DbItemTemplate armor = Armor(who, level, minQuality);
        DbItemTemplate extra = Rng.Next(100) < extraPct ? Armor(who, level, minQuality) : null;
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
            if (extra != null)
            {
                DbInventoryItem item2 = GameInventoryItem.Create(extra);
                if (player.Inventory.AddItem(eInventorySlot.FirstEmptyBackpack, item2))
                {
                    InventoryLogging.LogInventoryAction(chest, player, eInventoryActionType.Loot, item2.Template, 1);
                    player.Out.SendMessage($"Under it, {item2.Name}! Dangerous country hides better treasure.", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                }
            }
            // a Draught of Restoration now and then - more often in harder country (owner 2026-11-23)
            if (Rng.Next(100) < 8 + Math.Max(0, (int) chest.Danger) * 4 && LootUses.RestorationTemplate() is DbItemTemplate draught &&
                player.Inventory.AddTemplate(GameInventoryItem.Create(draught), 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                player.Out.SendMessage("Tucked in a corner: a Draught of Restoration.", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
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
    private static DbItemTemplate Armor(GameLiving who, int level, int minQuality = 96)
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
            t.Quality = Rng.Next(Math.Clamp(minQuality, 96, 100), 101);
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
    public sbyte Danger { get; init; } = MonsterTiers.Blue;    // its area (TreasureChests.Danger): better loot when harder
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
