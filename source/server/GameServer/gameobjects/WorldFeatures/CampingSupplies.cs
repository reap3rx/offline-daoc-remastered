using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;
using DOL.Logging;

namespace DOL.GS;

/// <summary>
/// Camping (owner 2026-11-11: "to simulate and stimulate interaction between bots and each other, and the player").
///   - Camping supplies: a campfire kit and a cooking pot in seven qualities (grey .. purple), 20 uses each, sold by a
///     Camping Supplier beside a merchant in every town - 1 gold for the cheapest, 2 platinum for the best, evenly
///     between.
///   - Using a campfire kit builds a campfire beside you for 10 minutes; a cooking pot goes over a campfire (it needs one).
///     Not in a town, not in a mob camp or near monsters, and not beside another fire.
///   - Anyone - player or bot, grouped or not - who sits at the fire for a minute gets its buffs for 30 minutes:
///     the fire a little less than the support classes' baseline strength, constitution, dexterity and armour factor of
///     its quality's level (grey under the lowest, purple under the best); the pot a damage shield, damage add, and
///     power and endurance regeneration. A real buff of the same kind still wins (the same effect groups).
///   - Bots come and sit at fires they see, chat a while or just take the warmth and go; they buy kits in town and
///     build fires when they rest out in the field (AutonomousCampfireVisits).
/// </summary>
public static class CampingSupplies
{
    private static readonly Logger Log = LoggerManager.Create(typeof(CampingSupplies));

    public sealed record Tier(int Number, int Level, string Fire, string Pot, long Price, string Color);

    // the cheapest 1 gold, the best 2 platinum, evenly between (copper: 100 = 1 silver, 10 000 = 1 gold, 10 000 000 = 1 plat)
    public static readonly Tier[] Tiers =
    [
        new(1, 2, "Smoky Campfire Kit", "Dented Tin Cookpot", 10_000, "grey"),
        new(2, 12, "Woodsman's Campfire Kit", "Iron Cookpot", 3_340_000, "green"),
        new(3, 20, "Traveler's Campfire Kit", "Traveler's Stewpot", 6_670_000, "blue"),
        new(4, 28, "Ranger's Campfire Kit", "Ranger's Cauldron", 10_000_000, "yellow"),
        new(5, 36, "Hearthstone Campfire Kit", "Hearthkeeper's Cauldron", 13_340_000, "orange"),
        new(6, 43, "Emberforged Campfire Kit", "Emberforged Cauldron", 16_670_000, "red"),
        new(7, 50, "Everburning Campfire Kit", "Feastmaster's Cauldron", 20_000_000, "purple"),
    ];

    public const string ItemListId = "camping_supplies";
    public const int Charges = 20;
    public const int FireModelBase = 32010;                  // + tier: the client's CampObjects
    public const int PotModelBase = 32020;
    public const int FireIcon = 2656;                        // objects.csv: Campfire
    public const int PotIcon = 538;                          // objects.csv: Dye pot
    public static readonly TimeSpan Lifetime = TimeSpan.FromMinutes(10);
    public const int BuffSeconds = 30 * 60;
    public const int SitSecondsNeeded = 60;
    public const ushort SitRadius = 420;                     // around the fire: a sitting circle
    public const ushort MonsterClearance = 1200;
    public const ushort TownFolkClearance = 1200;
    public const ushort BindClearance = 1500;
    public const ushort FireClearance = 700;
    public const ushort PotReach = 400;                      // a cooking pot goes over a fire this close

    public static string FireId(int tier) => $"camp_fire_{tier}";
    public static string PotId(int tier) => $"camp_pot_{tier}";

    public static bool TryParse(string idNb, out Tier tier, out bool pot)
    {
        tier = null;
        pot = false;
        if (string.IsNullOrEmpty(idNb) || !idNb.StartsWith("camp_", StringComparison.Ordinal))
            return false;
        pot = idNb.StartsWith("camp_pot_", StringComparison.Ordinal);
        if (!pot && !idNb.StartsWith("camp_fire_", StringComparison.Ordinal))
            return false;
        if (!int.TryParse(idNb[(idNb.LastIndexOf('_') + 1)..], out int n) || n < 1 || n > Tiers.Length)
            return false;
        tier = Tiers[n - 1];
        return true;
    }

    // ---------------------------------------------------------------- start: the items, the list, the suppliers

    private static MerchantTradeItems _list;
    private static readonly List<CampObject> Live = [];
    private static readonly object LiveSync = new();

    [GameServerStartedEvent]
    public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
    {
        try
        {
            EnsureTemplates();
            _list = new MerchantTradeItems(ItemListId);
            int slot = 0;
            foreach (Tier t in Tiers)
            {
                _list.AddTradeItem(0, (eMerchantWindowSlot)slot++, Template(FireId(t.Number)));
                _list.AddTradeItem(0, (eMerchantWindowSlot)slot++, Template(PotId(t.Number)));
            }
            int suppliers = SpawnSuppliers();
            Log.Info($"CAMPING ready: {Tiers.Length * 2} kits, {suppliers} camping suppliers");
            _ = new ECSGameTimer(null, Tick, 5000);
        }
        catch (Exception exception)
        {
            Log.Error("Camping supplies failed to start", exception);
        }
    }

    public static DbItemTemplate Template(string idNb) => GameServer.Database.FindObjectByKey<DbItemTemplate>(idNb);

    private static void EnsureTemplates()
    {
        foreach (Tier t in Tiers)
        {
            Ensure(FireId(t.Number), t.Fire, t, FireIcon,
                $"Builds a campfire beside you for {Lifetime.TotalMinutes:0} minutes ({t.Color} quality). Sit at it for a minute and " +
                "everyone there is warmed: strength, constitution, dexterity and armor for 30 minutes. Not in towns or near monsters.");
            Ensure(PotId(t.Number), t.Pot, t, PotIcon,
                $"Hangs a cooking pot over a campfire ({t.Color} quality). Sit there for a minute and everyone is fed: a damage " +
                "shield, added damage, and power and endurance regeneration for 30 minutes. Needs a campfire.");
        }
    }

    private static void Ensure(string idNb, string name, Tier t, int model, string description)
    {
        DbItemTemplate existing = Template(idNb);
        DbItemTemplate it = existing ?? new DbItemTemplate();
        it.Id_nb = idNb;
        it.Name = name;
        it.Level = t.Level;
        it.Model = model;
        it.Object_Type = (int)eObjectType.GenericItem;
        it.Item_Type = 0;
        it.Charges = Charges;
        it.MaxCharges = Charges;
        it.Price = t.Price;
        it.Weight = 20;
        it.Realm = 0;
        it.IsDropable = true;
        it.IsPickable = true;
        it.IsTradable = true;
        it.CanDropAsLoot = false;
        it.Quality = 100;
        it.Condition = 50_000;
        it.MaxCondition = 50_000;
        it.Durability = 50_000;
        it.MaxDurability = 50_000;
        it.PackSize = 1;
        it.MaxCount = 1;
        it.Description = description;
        if (existing == null)
            GameServer.Database.AddObject(it);
        else
            GameServer.Database.SaveObject(it);
    }

    /// <summary>A Camping Supplier beside a merchant in every town (the world's town areas, and the capitals' bind
    /// stones): the merchant nearest the town's middle, the supplier a few steps off.</summary>
    private static int SpawnSuppliers()
    {
        int count = 0;
        var placed = new List<(ushort Region, int X, int Y)>();
        foreach (Region region in WorldMgr.GetAllRegions())
        {
            if (region == null || region.IsHousing || region.IsRvR || region.IsInstance)
                continue;
            var towns = new List<(int X, int Y, int Z, int Radius)>();
            foreach (DbArea area in DOLDB<DbArea>.SelectObjects(DB.Column("Region").IsEqualTo(region.ID)))
                if (area.ClassType is "DOL.GS.Area+Circle" or "DOL.GS.Area+SafeArea")
                    towns.Add((area.X, area.Y, area.Z, Math.Max(800, area.Radius)));
            if (region.IsCapitalCity)
                foreach (DbBindPoint bind in DOLDB<DbBindPoint>.SelectObjects(DB.Column("Region").IsEqualTo(region.ID)))
                    towns.Add((bind.X, bind.Y, bind.Z, 3000));
            foreach (var town in towns)
            {
                if (placed.Any(p => p.Region == region.ID && Sq(p.X - town.X) + Sq(p.Y - town.Y) < Sq(3000)))
                    continue;
                Zone zone = region.GetZone(town.X, town.Y);
                if (zone == null)
                    continue;
                // (by map distance: a town area's height is often 0)
                GameMerchant near = new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia, eRealm.None }
                    .SelectMany(r => zone.GetNPCsOfZone(r))
                    .OfType<GameMerchant>()
                    .Where(m => m.GetType() == typeof(GameMerchant) && m.IsAlive &&
                                Sq(m.X - town.X) + Sq(m.Y - town.Y) <= Sq(town.Radius))
                    .OrderBy(m => Sq(m.X - town.X) + Sq(m.Y - town.Y))
                    .FirstOrDefault();
                if (near == null)
                    continue;
                if (SpawnSupplier(near))
                {
                    placed.Add((region.ID, near.X, near.Y));
                    count++;
                }
            }
        }
        return count;
    }

    private static bool SpawnSupplier(GameMerchant beside)
    {
        double a = beside.Heading * Math.PI * 2 / 4096.0 + Math.PI / 2;    // a step to the merchant's side
        var supplier = new GameMerchant
        {
            Name = "Camping Supplier",
            GuildName = "Camp Supplies",
            Model = beside.Model,
            Size = beside.Size,
            Level = 30,
            Realm = beside.Realm,
            CurrentRegionID = beside.CurrentRegionID,
            Heading = beside.Heading,
            X = beside.X + (int)(Math.Sin(a) * -110),
            Y = beside.Y + (int)(Math.Cos(a) * 110),
            Z = beside.Z,
            TradeItems = _list,
            Flags = beside.Flags,
        };
        return supplier.AddToWorld();
    }

    private static long Sq(long v) => v * v;

    // ---------------------------------------------------------------- using a kit

    /// <summary>GamePlayer.UseSlot: a camping kit used. True when it was one (used or refused with a reason).</summary>
    public static bool TryUse(GamePlayer player, DbInventoryItem item)
    {
        if (player == null || item == null || !TryParse(item.Id_nb, out Tier tier, out bool pot))
            return false;
        if (!TryPlace(player, tier, pot, out string why))
        {
            player.Out.SendMessage(why, eChatType.CT_System, eChatLoc.CL_SystemWindow);
            return true;
        }
        item.Charges--;
        if (item.Charges < 1)
            player.Inventory.RemoveCountFromStack(item, 1);
        else
            player.Out.SendInventoryItemsUpdate(new[] { item });
        player.Out.SendMessage(pot
                ? $"You hang the {tier.Pot.ToLowerInvariant()} over the fire. ({Math.Max(0, item.Charges)} uses left)"
                : $"You build a campfire. Sit by it a while. ({Math.Max(0, item.Charges)} uses left)",
            eChatType.CT_System, eChatLoc.CL_SystemWindow);
        return true;
    }

    /// <summary>Builds the fire (or hangs the pot) for `who`, or says why not.</summary>
    public static bool TryPlace(GameLiving who, Tier tier, bool pot, out string why)
    {
        why = null;
        if (who?.CurrentRegion == null || !who.IsAlive)
        {
            why = "You can't do that now.";
            return false;
        }
        if (who.InCombat)
        {
            why = "You can't make camp in the middle of a fight!";
            return false;
        }
        if (pot)
        {
            CampObject fire = NearestFire(who, PotReach);
            if (fire == null)
            {
                why = "A cooking pot needs a campfire - stand by one first.";
                return false;
            }
            if (fire.Pot != null)
            {
                why = "There is already a pot over that fire.";
                return false;
            }
            var p = new CampObject(tier, true, fire, who.Name)
            {
                X = fire.X, Y = fire.Y, Z = fire.Z, Heading = fire.Heading, CurrentRegionID = fire.CurrentRegionID,
            };
            if (!p.AddToWorld())
            {
                why = "The pot won't sit right here.";
                return false;
            }
            fire.Pot = p;
            lock (LiveSync)
                Live.Add(p);
            return true;
        }

        double a = who.Heading * Math.PI * 2 / 4096.0;
        int x = who.X - (int)(Math.Sin(a) * 90), y = who.Y + (int)(Math.Cos(a) * 90), z = who.Z;
        why = WhyNotHere(who, x, y, z);
        if (why != null)
            return false;
        var f = new CampObject(tier, false, null, who.Name)
        {
            X = x, Y = y, Z = z, Heading = who.Heading, CurrentRegionID = who.CurrentRegionID,
        };
        if (!f.AddToWorld())
        {
            why = "You can't build a fire here.";
            return false;
        }
        lock (LiveSync)
            Live.Add(f);
        Log.Info($"CAMPFIRE built by {who.Name} tier={tier.Number} region={who.CurrentRegionID} at {x},{y},{z}");
        return true;
    }

    /// <summary>Why a fire can't be built at this spot (null: it can).</summary>
    public static string WhyNotHere(GameLiving who, int x, int y, int z)
    {
        Region region = who.CurrentRegion;
        if (region.IsCapitalCity || region.IsHousing)
            return "You can't build a campfire in town.";
        foreach (IArea area in region.GetAreasOfSpot(x, y, z))
            if (area is Area.Circle)
                return "You can't build a campfire in town.";
        if (BotReleaseBindPoints.IsNearBindstone(region.ID, x, y, z, BindClearance))
            return "You can't build a campfire this close to a bind stone.";
        foreach (GameNPC npc in who.GetNPCsInRadius(Math.Max(MonsterClearance, TownFolkClearance)))
        {
            if (npc == null || !npc.IsAlive || npc is GameBot || npc.Brain is IControlledBrain || npc.ObjectState != GameObject.eObjectState.Active)
                continue;
            long d2 = Sq(npc.X - x) + Sq(npc.Y - y);
            if (npc.Realm == eRealm.None && (npc.Flags & GameNPC.eFlags.PEACE) == 0 && npc.Level > 0 && d2 < Sq(MonsterClearance))
                return "It's not safe to make camp here - there are monsters about.";
            if (npc.Realm != eRealm.None && d2 < Sq(TownFolkClearance))
                return "You can't build a campfire in town.";
        }
        lock (LiveSync)
            if (Live.Any(o => !o.IsPot && o.CurrentRegionID == region.ID && Sq(o.X - x) + Sq(o.Y - y) < Sq(FireClearance)))
                return "There's already a campfire here - go and sit by it!";
        return null;
    }

    public static CampObject NearestFire(GameObject near, int within)
    {
        lock (LiveSync)
            return Live.Where(o => !o.IsPot && o.CurrentRegionID == near.CurrentRegionID && o.ObjectState == GameObject.eObjectState.Active &&
                                   Sq(o.X - near.X) + Sq(o.Y - near.Y) <= Sq(within))
                .OrderBy(o => Sq(o.X - near.X) + Sq(o.Y - near.Y)).FirstOrDefault();
    }

    public static CampObject[] Fires()
    {
        lock (LiveSync)
            return Live.Where(o => !o.IsPot && o.ObjectState == GameObject.eObjectState.Active).ToArray();
    }

    // ---------------------------------------------------------------- the fire's warmth

    // a sitter's minute at a fire: (fire object id, sitter) -> when they sat; and who has had this fire's buffs
    private static readonly ConcurrentDictionary<(int Fire, GameLiving Who), long> SatSince = new();
    private static readonly ConcurrentDictionary<(int Fire, GameLiving Who), bool> Warmed = new();

    public static bool IsSitting(GameLiving who) => who switch
    {
        GamePlayer p => p.IsSitting,
        GameBot b => b.IsRecoveryResting && !b.IsMoving,
        _ => false,
    };

    private static int Tick(ECSGameTimer timer)
    {
        try
        {
            long now = GameLoop.GameLoopTime;
            CampObject[] all;
            lock (LiveSync)
            {
                foreach (CampObject gone in Live.Where(o => o.ObjectState != GameObject.eObjectState.Active || now >= o.ExpiresTick).ToArray())
                {
                    Live.Remove(gone);
                    if (gone.ObjectState == GameObject.eObjectState.Active)
                        gone.RemoveFromWorld();
                    if (!gone.IsPot && gone.Pot != null && gone.Pot.ObjectState == GameObject.eObjectState.Active)
                        gone.Pot.ExpiresTick = now;                 // (the pot goes cold with its fire)
                }
                all = Live.Where(o => !o.IsPot).ToArray();
            }
            foreach (CampObject fire in all)
            {
                var here = new HashSet<GameLiving>();
                foreach (GamePlayer p in fire.GetPlayersInRadius(SitRadius))
                    here.Add(p);
                foreach (GameNPC n in fire.GetNPCsInRadius(SitRadius))
                    if (n is GameBot b)
                        here.Add(b);
                foreach (GameLiving who in here)
                {
                    var key = (fire.ObjectID, who);
                    if (!who.IsAlive || !IsSitting(who) || who.InCombat)
                    {
                        SatSince.TryRemove(key, out _);
                        continue;
                    }
                    long since = SatSince.GetOrAdd(key, now);
                    if (now - since < SitSecondsNeeded * 1000 || Warmed.ContainsKey(key))
                        continue;
                    Warmed[key] = true;
                    Warm(who, fire);
                }
                AutonomousCampfireVisits.Chatter(fire, here);
            }
            foreach (var key in SatSince.Keys.Where(k => all.All(f => f.ObjectID != k.Fire)).ToArray())
                SatSince.TryRemove(key, out _);
            foreach (var key in Warmed.Keys.Where(k => all.All(f => f.ObjectID != k.Fire)).ToArray())
                Warmed.TryRemove(key, out _);
            AutonomousCampfireVisits.Tick(all);
        }
        catch (Exception exception)
        {
            Log.Error("Camping tick failed", exception);
        }
        return 5000;
    }

    private static void Warm(GameLiving who, CampObject fire)
    {
        AutonomousCampfireVisits.NoteWarmed(who);
        foreach (Spell spell in FireSpells(fire.Tier))
            Cast(who, spell);
        bool fed = fire.Pot != null && fire.Pot.ObjectState == GameObject.eObjectState.Active;
        if (fed)
            foreach (Spell spell in PotSpells(fire.Pot.Tier))
                Cast(who, spell);
        if (who is GamePlayer player)
            player.Out.SendMessage(fed
                    ? "The fire's warmth and a hot meal restore you."
                    : "The fire's warmth restores you.",
                eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
    }

    private static void Cast(GameLiving who, Spell spell)
    {
        ISpellHandler handler = ScriptMgr.CreateSpellHandler(who, spell, Line);
        handler?.StartSpell(who);
    }

    // ---------------------------------------------------------------- the buffs

    private static SpellLine _line;
    private static SpellLine Line => _line ??= new SpellLine("CampingSupplies", "Camping", "unknown", true);

    private static readonly ConcurrentDictionary<int, Spell[]> FireCache = new();
    private static readonly ConcurrentDictionary<int, Spell[]> PotCache = new();

    // The support classes' baseline buffs (the world's spell table): a single stat ~10 + 0.8 x level, armour factor
    // ~10 + level, damage add ~1 + 0.2 x level dps, damage shield ~0.6 + 0.09 x level dps, regeneration chants 1 - 5.
    // A fire gives 85% of what its quality's level would (owner: "slightly worse").
    public const double Worse = 0.85;

    public static int StatFor(int level) => (int)Math.Round(Worse * (10 + 0.8 * level));
    public static int ArmorFor(int level) => (int)Math.Round(Worse * (10 + level));
    public static double DamageAddFor(int level) => Math.Round(Worse * (1.0 + 0.2 * level), 1);
    public static double DamageShieldFor(int level) => Math.Round(Worse * (0.6 + 0.09 * level), 1);
    public static int RegenFor(int tier) => Math.Max(1, (tier + 1) / 2);

    public static Spell[] FireSpells(Tier t) => FireCache.GetOrAdd(t.Number, _ =>
    [
        Buff(96000 + t.Number * 20 + 1, $"Campfire's Vigor", eSpellType.StrengthBuff, StatFor(t.Level), 0, 3161, 4),
        Buff(96000 + t.Number * 20 + 2, $"Campfire's Hardiness", eSpellType.ConstitutionBuff, StatFor(t.Level), 0, 3181, 201),
        Buff(96000 + t.Number * 20 + 3, $"Campfire's Nimbleness", eSpellType.DexterityBuff, StatFor(t.Level), 0, 3171, 202),
        Buff(96000 + t.Number * 20 + 4, $"Campfire's Shelter", eSpellType.BaseArmorFactorBuff, ArmorFor(t.Level), 0, 3151, 1),
    ]);

    public static Spell[] PotSpells(Tier t) => PotCache.GetOrAdd(t.Number, _ =>
    [
        Buff(96000 + t.Number * 20 + 11, "Hearty Stew: Thorns", eSpellType.DamageShield, 0, DamageShieldFor(t.Level), 11024, 0, 10),
        Buff(96000 + t.Number * 20 + 12, "Hearty Stew: Zeal", eSpellType.DamageAdd, 0, DamageAddFor(t.Level), 3205, 0, 15),
        Buff(96000 + t.Number * 20 + 13, "Hearty Stew: Clarity", eSpellType.PowerRegenBuff, RegenFor(t.Number), 0, 8082, 0),
        Buff(96000 + t.Number * 20 + 14, "Hearty Stew: Stamina", eSpellType.EnduranceRegenBuff, RegenFor(t.Number), 0, 8081, 0),
    ]);

    private static Spell Buff(int id, string name, eSpellType type, int value, double damage, int icon, int effectGroup, int damageType = 0)
    {
        var s = new DbSpell
        {
            SpellID = id,
            Name = name,
            Type = type.ToString(),
            Value = value,
            Damage = damage,
            DamageType = damageType,
            Duration = BuffSeconds,
            Icon = icon,
            ClientEffect = icon,
            Target = eSpellTarget.SELF.ToString(),
            Range = 0,
            CastTime = 0,
            Concentration = 0,
            EffectGroup = effectGroup,
            Description = "Camping: a warm fire and good food.",
        };
        s.AllowAdd = false;
        return new Spell(s, 50);
    }
}

/// <summary>A campfire or a cooking pot in the world (CampingSupplies): its quality, its 10 minutes, its fire.</summary>
public class CampObject : GameStaticItem
{
    public CampingSupplies.Tier Tier { get; }
    public bool IsPot { get; }
    public CampObject Fire { get; }
    public CampObject Pot { get; set; }
    public string BuiltBy { get; }
    public long ExpiresTick { get; set; }

    public CampObject(CampingSupplies.Tier tier, bool pot, CampObject fire, string builtBy)
    {
        Tier = tier;
        IsPot = pot;
        Fire = fire;
        BuiltBy = builtBy ?? string.Empty;
        Model = (ushort)((pot ? CampingSupplies.PotModelBase : CampingSupplies.FireModelBase) + tier.Number);
        Name = pot ? tier.Pot : "Campfire";
        LoadedFromScript = true;
        ExpiresTick = GameLoop.GameLoopTime + (long)CampingSupplies.Lifetime.TotalMilliseconds;
    }

    public override bool Interact(GamePlayer player)
    {
        if (!base.Interact(player))
            return false;
        int minutes = (int)Math.Max(0, Math.Ceiling((ExpiresTick - GameLoop.GameLoopTime) / 60000.0));
        player.Out.SendMessage(IsPot
                ? $"A {Tier.Color} quality pot of stew bubbles over the fire."
                : $"A {Tier.Color} quality campfire, built by {BuiltBy}. It will burn for about {minutes} more minute{(minutes == 1 ? "" : "s")}. Sit by it a while.",
            eChatType.CT_System, eChatLoc.CL_SystemWindow);
        return true;
    }
}
