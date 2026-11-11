using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.Logging;

namespace DOL.GS;

/// <summary>
/// Soulbind stones (owner 2026-11-11): small bind stones (three quarters the size) scattered through the outdoor zones,
/// at most three a zone, far from towns, bind stones and each other, in interesting places - a ridge, a coast, the edge
/// of a monster camp. You can't bind at one; when you die you choose: rise at the nearest soulbind stone of the region,
/// or at your bind stone (or take a resurrection if someone offers one). None in PvP zones. Bots use them too.
/// The stones are chosen once and kept in soulbind-stones.json (the server folder), so they stay put between restarts;
/// a zone without an entry (a new zone, or the file deleted) gets its stones at the next start.
/// </summary>
public static class SoulbindStones
{
    private static readonly Logger Log = LoggerManager.Create(typeof(SoulbindStones));

    public const int MaxPerZone = 3;
    public const float TownMargin = 3500;                     // beyond a town's own radius
    public const float BindDistance = 6000;                   // from any bind stone
    public const float Separation = 14000;                    // from each other
    public const ushort ModelAlbion = 32001, ModelMidgard = 32002, ModelHibernia = 32003;

    public sealed class Entry
    {
        public ushort Region { get; set; }
        public ushort Zone { get; set; }
        public int X { get; set; }
        public int Y { get; set; }
        public int Z { get; set; }
        public ushort Heading { get; set; }
        public string Kind { get; set; } = "";
    }

    public sealed class FileData
    {
        public int Version { get; set; } = 1;
        public List<ushort> Zones { get; set; } = [];         // zones already given their stones (even when none fit)
        public List<Entry> Stones { get; set; } = [];
    }

    private static readonly List<SoulbindStone> Live = [];
    private static readonly object Sync = new();

    public static string FilePath => Path.Combine(GameServer.Instance.Configuration.RootDirectory, "soulbind-stones.json");

    [GameServerStartedEvent]
    public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
    {
        try
        {
            FileData data = Load();
            int added = 0;
            var rng = new Random();
            foreach (Zone zone in WorldFeatureSpots.OutdoorPveZones())
            {
                if (data.Zones.Contains(zone.ID))
                    continue;
                List<Entry> picked = Choose(zone, rng);
                data.Stones.AddRange(picked);
                data.Zones.Add(zone.ID);
                added += picked.Count;
            }
            if (added > 0 || !File.Exists(FilePath))
                Save(data);
            int spawned = 0;
            foreach (Entry s in data.Stones)
                if (Spawn(s))
                    spawned++;
            Log.Info($"SOULBIND stones: {spawned} in the world ({added} new) - {FilePath}");
        }
        catch (Exception exception)
        {
            Log.Error("Soulbind stones failed to start", exception);
        }
    }

    private static FileData Load()
    {
        try
        {
            if (File.Exists(FilePath))
                return JsonSerializer.Deserialize<FileData>(File.ReadAllText(FilePath)) ?? new FileData();
        }
        catch (Exception exception)
        {
            Log.Warn($"Could not read {FilePath}: {exception.Message} - choosing the stones again");
        }
        return new FileData();
    }

    private static void Save(FileData data) =>
        File.WriteAllText(FilePath, JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = true }));

    /// <summary>A zone's stones: up to three, the most interesting first, each far from the last.</summary>
    public static List<Entry> Choose(Zone zone, Random rng)
    {
        var chosen = new List<Entry>();
        Region region = zone.ZoneRegion;
        List<WorldFeatureSpots.Spot> spots = WorldFeatureSpots.Sample(zone, 220, TownMargin, rng)
            .Where(s => !WorldFeatureSpots.NearBind(region, s.Pos.X, s.Pos.Y, BindDistance))
            .ToList();
        // interesting first: a ridge or a coast, then a camp's edge, then anywhere; a little chance mixes them
        var scored = spots.Select(s => (Spot: s, Score: s.Kind switch
        {
            WorldFeatureSpots.Kind.Ridge => 3.0,
            WorldFeatureSpots.Kind.Coast => 2.6,
            WorldFeatureSpots.Kind.Camp => 1.6,
            _ => 1.0,
        } + rng.NextDouble() * 1.5)).OrderByDescending(x => x.Score).ToList();
        int want = rng.Next(100) < 70 ? MaxPerZone : MaxPerZone - 1;
        foreach (var (spot, _) in scored)
        {
            if (chosen.Count >= want)
                break;
            if (chosen.Any(c => Vector2.DistanceSquared(new(c.X, c.Y), new(spot.Pos.X, spot.Pos.Y)) < Separation * Separation))
                continue;
            chosen.Add(new Entry
            {
                Region = region.ID, Zone = zone.ID, X = (int)spot.Pos.X, Y = (int)spot.Pos.Y, Z = (int)spot.Pos.Z,
                Heading = (ushort)rng.Next(4096), Kind = spot.Kind.ToString().ToLowerInvariant(),
            });
        }
        return chosen;
    }

    private static bool Spawn(Entry e)
    {
        Region region = WorldMgr.GetRegion(e.Region);
        if (region == null)
            return false;
        Zone zone = region.GetZone(e.X, e.Y);
        eRealm realm = zone != null && zone.Realm != eRealm.None ? zone.Realm : RealmOfRegion(e.Region);
        var stone = new SoulbindStone
        {
            Model = realm switch { eRealm.Midgard => ModelMidgard, eRealm.Hibernia => ModelHibernia, _ => ModelAlbion },
            Name = "Soulbind Stone",
            X = e.X, Y = e.Y, Z = e.Z, Heading = e.Heading, CurrentRegionID = e.Region,
            LoadedFromScript = true,
        };
        if (!stone.AddToWorld())
            return false;
        lock (Sync)
            Live.Add(stone);
        return true;
    }

    private static eRealm RealmOfRegion(ushort region) => region switch
    {
        100 or 101 or 151 or 111 or 112 or 113 => eRealm.Midgard,
        200 or 201 or 181 or 211 or 212 => eRealm.Hibernia,
        _ => eRealm.Albion,
    };

    /// <summary>The soulbind stone nearest (x, y) in the region, or null.</summary>
    public static SoulbindStone Nearest(ushort region, int x, int y)
    {
        lock (Sync)
            return Live.Where(s => s.CurrentRegionID == region && s.ObjectState == GameObject.eObjectState.Active)
                .OrderBy(s => (long)(s.X - x) * (s.X - x) + (long)(s.Y - y) * (s.Y - y)).FirstOrDefault();
    }

    /// <summary>Where a release to the nearest soulbind stone puts `who` (a step off the stone), or false.</summary>
    public static bool TryReleasePoint(GameLiving who, out ushort region, out int x, out int y, out int z, out ushort heading)
    {
        region = who.CurrentRegionID;
        x = y = z = 0;
        heading = 0;
        SoulbindStone stone = Nearest(who.CurrentRegionID, who.X, who.Y);
        if (stone == null)
            return false;
        double a = Random.Shared.NextDouble() * Math.PI * 2;
        x = stone.X + (int)(Math.Sin(a) * 120);
        y = stone.Y + (int)(Math.Cos(a) * 120);
        z = stone.Z;
        Zone zone = stone.CurrentZone;
        Vector3? ground = WorldFeatureSpots.Ground(zone, new Vector3(x, y, z), 150);
        if (ground.HasValue)
            (x, y, z) = ((int)ground.Value.X, (int)ground.Value.Y, (int)ground.Value.Z);
        else
            (x, y, z) = (stone.X + 60, stone.Y, stone.Z);
        heading = (ushort)((Math.Atan2(stone.X - x, y - stone.Y) * 2048 / Math.PI + 4096) % 4096);
        return true;
    }
}

/// <summary>A soulbind stone: you can't bind here - it only calls back the fallen nearby.</summary>
public class SoulbindStone : GameStaticItem
{
    public override bool Interact(GamePlayer player)
    {
        if (!base.Interact(player))
            return false;
        player.Out.SendMessage("A soulbind stone. You cannot bind your soul here, but should you fall in this land you may rise at the nearest such stone.",
            eChatType.CT_System, eChatLoc.CL_SystemWindow);
        return true;
    }
}
