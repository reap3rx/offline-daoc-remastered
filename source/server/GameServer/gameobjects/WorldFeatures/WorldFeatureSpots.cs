using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.Database;

namespace DOL.GS;

/// <summary>
/// Places in the open world for the new features (owner 2026-11-11 - soulbind stones and treasure chests): the
/// outdoor PvE zones (no capital, housing, dungeon, battleground or frontier), their towns (the world's town areas and
/// bind stones) to stay clear of, and spots on the navigation mesh sorted into what makes a place interesting - a ridge
/// (the high ground of its zone), a coast (just above the water), a monster camp (beside live spawns), or the wild.
/// </summary>
public static class WorldFeatureSpots
{
    public enum Kind { Wild, Ridge, Coast, Camp }

    public readonly record struct Spot(Vector3 Pos, Kind Kind);

    public readonly record struct Town(int X, int Y, int Radius);

    private static readonly ConcurrentDictionary<ushort, Town[]> Towns = new();

    // (the classic regions are flagged frontier for their old frontier zones - those zones are left out instead)
    public static bool IsOutdoorPveRegion(Region region) =>
        region != null && !region.IsRvR && !region.IsCapitalCity && !region.IsHousing &&
        !region.IsInstance && !region.IsDungeon && !BattlegroundBrackets.IsBattlegroundRegion(region.ID) && region.ID != 27;

    /// <summary>The classic regions' frontier zones (the PvP zones of 1.65; AutonomousWorldBotController.IsFrontierZone).</summary>
    public static bool IsFrontierZone(ushort regionId, ushort zoneId) =>
        regionId == 1 && zoneId is 11 or 12 or 14 or 15 ||
        regionId == 100 && zoneId is 111 or 112 or 113 or 115 ||
        regionId == 200 && zoneId is 210 or 211 or 212 or 214;

    /// <summary>The outdoor PvE zones with a navigation mesh.</summary>
    public static List<Zone> OutdoorPveZones()
    {
        var zones = new List<Zone>();
        IPathfindingMgr nav = PathfindingProvider.Instance;
        if (!nav.IsAvailable)
            return zones;
        foreach (Region region in WorldMgr.GetAllRegions())
        {
            if (!IsOutdoorPveRegion(region))
                continue;
            foreach (Zone zone in region.Zones)
                if (zone != null && !zone.IsDungeon && !zone.IsLava && !IsFrontierZone(region.ID, zone.ID) && nav.HasNavmesh(zone))
                    zones.Add(zone);
        }
        return zones;
    }

    /// <summary>The region's towns: its town areas (at their radius) and its bind stones (1500 round).</summary>
    public static Town[] TownsOf(Region region) => Towns.GetOrAdd(region.ID, id =>
    {
        var list = new List<Town>();
        foreach (DbArea area in DOLDB<DbArea>.SelectObjects(DB.Column("Region").IsEqualTo(id)))
            list.Add(new Town(area.X, area.Y, Math.Max(1000, area.Radius)));
        foreach (DbBindPoint bind in DOLDB<DbBindPoint>.SelectObjects(DB.Column("Region").IsEqualTo(id)))
            list.Add(new Town(bind.X, bind.Y, 1500));
        return list.ToArray();
    });

    /// <summary>Within a town (its radius plus `margin`)?</summary>
    public static bool NearTown(Region region, float x, float y, float margin) =>
        TownsOf(region).Any(t => Sq(x - t.X) + Sq(y - t.Y) < Sq(t.Radius + margin));

    /// <summary>Within `distance` of a bind stone?</summary>
    public static bool NearBind(Region region, float x, float y, float distance) =>
        TownsOf(region).Any(t => t.Radius == 1500 && Sq(x - t.X) + Sq(y - t.Y) < Sq(distance));

    private static double Sq(double v) => v * v;

    /// <summary>
    /// Up to `count` mesh spots in the zone, out of the water and clear of towns by `townMargin`, each with its kind:
    /// a ridge is in the top fifth of the zone's heights, a coast within 150 units above its water, a camp within 900
    /// units of a live monster spawn.
    /// </summary>
    public static List<Spot> Sample(Zone zone, int count, float townMargin, Random rng, Vector3[] camps = null)
    {
        var spots = new List<Spot>();
        IPathfindingMgr nav = PathfindingProvider.Instance;
        Region region = zone.ZoneRegion;
        if (region == null || !nav.IsAvailable || !nav.HasNavmesh(zone))
            return spots;
        var raw = new List<Vector3>();
        for (int i = 0; i < count * 4 && raw.Count < count; i++)
        {
            var center = new Vector3(zone.XOffset + rng.Next(zone.Width), zone.YOffset + rng.Next(zone.Height),
                Math.Max(0, zone.Waterlevel) + 2000);
            // the mesh under (x, y) at any height first - a random-point query needs a start on the mesh
            Vector3? floor = nav.GetClosestPoint(zone, center, 1200, 1200, 20000, nav.DefaultFilters);
            if (!floor.HasValue)
                continue;
            Vector3? p = nav.GetRandomPoint(zone, floor.Value, 2500, nav.DefaultFilters);
            if (!p.HasValue)
                continue;
            Vector3 v = p.Value;
            if (v.X < zone.XOffset + 300 || v.Y < zone.YOffset + 300 ||
                v.X > zone.XOffset + zone.Width - 300 || v.Y > zone.YOffset + zone.Height - 300)
                continue;                                            // (well inside its own zone)
            if (zone.Waterlevel > 0 && v.Z < zone.Waterlevel + 10)
                continue;                                            // (under or at the water)
            if (NearTown(region, v.X, v.Y, townMargin))
                continue;
            raw.Add(v);
        }
        if (raw.Count == 0)
            return spots;
        float ridge = raw.Select(v => v.Z).OrderBy(z => z).ElementAt((int)(raw.Count * 0.8));
        camps ??= CampsOf(zone);
        foreach (Vector3 v in raw)
        {
            Kind kind = Kind.Wild;
            if (zone.Waterlevel > 0 && v.Z - zone.Waterlevel < 150)
                kind = Kind.Coast;
            else if (v.Z >= ridge)
                kind = Kind.Ridge;
            if (camps.Any(c => Sq(c.X - v.X) + Sq(c.Y - v.Y) < 900 * 900))
                kind = kind == Kind.Wild ? Kind.Camp : kind;
            spots.Add(new Spot(v, kind));
        }
        return spots;
    }

    /// <summary>The zone's monster spawn points (read on the game loop; Sample can then run on a worker).</summary>
    public static Vector3[] CampsOf(Zone zone) => zone.GetNPCsOfZone(eRealm.None)
        .Where(n => n != null && n.Level > 0 && (n.Flags & GameNPC.eFlags.PEACE) == 0 && n is not GameBot)
        .Select(n => new Vector3(n.SpawnPoint.X, n.SpawnPoint.Y, n.SpawnPoint.Z)).ToArray();

    /// <summary>A spot near (x, y) on the mesh, or null.</summary>
    public static Vector3? Ground(Zone zone, Vector3 near, float radius)
    {
        IPathfindingMgr nav = PathfindingProvider.Instance;
        if (zone == null || !nav.IsAvailable || !nav.HasNavmesh(zone))
            return null;
        return nav.GetClosestPoint(zone, near, radius, radius, 400, nav.DefaultFilters);
    }
}
