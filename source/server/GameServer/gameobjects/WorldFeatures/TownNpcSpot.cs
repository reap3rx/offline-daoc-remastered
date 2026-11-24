using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.Database;

namespace DOL.GS;

/// <summary>Where to stand a town's own helper NPC (the Camping Supplier, the Quartermaster of Valor). Owner 2026-11-23:
/// in Ardee both stood in the walls of the building behind them. They went one step to the side of the merchant nearest
/// the town's middle - and Ardee's is indoors. Now: out in the open by the town's bind point (the square - where the
/// soulbind stone stands), a few steps off it, on the navmesh, in sight of it and clear of everyone else; facing the
/// stone. A town without a bind point nearby: beside the merchant as before, with the same checks.</summary>
public static class TownNpcSpot
{
    public readonly record struct Spot(Vector3 At, ushort Heading);

    // degrees round the base, in the order tried (the caller's side first), and the steps out (units)
    static readonly int[] Turns = { 90, -90, 45, -45, 135, -135, 0, 180 };
    const int BindReach = 2500;                  // a bind point this near the merchant is the town's square
    const int Clear = 150;                       // nobody else within this of the spot

    static readonly ConcurrentDictionary<ushort, List<Vector3>> _binds = new();

    public static Spot Beside(GameNPC near, int preferTurn = 90)
    {
        Zone zone = near.CurrentZone;
        Vector3 merchant = new(near.X, near.Y, near.Z);
        if (zone != null && Bind(near.CurrentRegionID, merchant) is Vector3 bind &&
            TryAround(zone, bind, 0, preferTurn, new[] { 260, 340, 440 }, out Spot s))
            return s;
        if (zone != null && TryAround(zone, merchant, near.Heading, preferTurn, new[] { 110, 160, 220 }, out s))
            return s;
        Vector3 old = Point(merchant, near.Heading, preferTurn, 110);
        return new Spot(old, near.Heading);
    }

    static Vector3? Bind(ushort region, Vector3 at)
    {
        List<Vector3> list = _binds.GetOrAdd(region, r =>
        {
            try
            {
                return DOLDB<DbBindPoint>.SelectObjects(DB.Column("Region").IsEqualTo(r))
                    .Select(b => new Vector3(b.X, b.Y, b.Z)).ToList();
            }
            catch
            {
                return new List<Vector3>();
            }
        });
        Vector3? best = null;
        float bestD = BindReach;
        foreach (Vector3 b in list)
        {
            float d = Vector2.Distance(new(b.X, b.Y), new(at.X, at.Y));
            if (d < bestD)
            {
                bestD = d;
                best = b;
            }
        }
        return best;
    }

    static bool TryAround(Zone zone, Vector3 baseAt, ushort baseHeading, int preferTurn, int[] steps, out Spot spot)
    {
        spot = default;
        var nav = PathfindingProvider.Instance;
        if (nav == null || !nav.IsAvailable || !nav.HasNavmesh(zone))
            return false;
        var others = zone.ZoneRegion.GetNPCsInRadius(new Point3D((int) baseAt.X, (int) baseAt.Y, (int) baseAt.Z), 1200)
            .Cast<GameNPC>().Select(n => new Vector2(n.X, n.Y)).ToList();
        Vector3 eye = baseAt + new Vector3(0, 0, 60);
        var turns = Turns.OrderBy(t => t == preferTurn ? 0 : Math.Sign(t) == Math.Sign(preferTurn) ? 1 : 2).ToArray();
        foreach (int step in steps)
            foreach (int turn in turns)
            {
                Vector3 p = Point(baseAt, baseHeading, turn, step);
                Vector3 s = p;
                if (!nav.TrySnapToMesh(zone, ref s, 128f))
                    continue;
                if (Vector2.Distance(new(s.X, s.Y), new(p.X, p.Y)) > 40 || Math.Abs(s.Z - baseAt.Z) > 100)
                    continue;                                    // the mesh is elsewhere: a wall, a ledge, a floor above
                if (!nav.HasLineOfSight(zone, eye, s + new Vector3(0, 0, 60), nav.DefaultFilters))
                    continue;                                    // behind something
                if (others.Any(o => Vector2.Distance(o, new(s.X, s.Y)) < Clear))
                    continue;                                    // someone stands there
                spot = new Spot(s, Facing(s, baseAt));
                return true;
            }
        return false;
    }

    /// <summary>DAoC headings: 4096 a circle; a heading's point is (X - sin a * d, Y + cos a * d).</summary>
    public static Vector3 Point(Vector3 from, ushort heading, int turnDeg, int step)
    {
        double a = (heading * 360.0 / 4096.0 + turnDeg) * Math.PI / 180.0;
        return new Vector3(from.X - (float) (Math.Sin(a) * step), from.Y + (float) (Math.Cos(a) * step), from.Z);
    }

    /// <summary>The heading from one point to look at another.</summary>
    public static ushort Facing(Vector3 from, Vector3 to)
    {
        double a = Math.Atan2(-(to.X - from.X), to.Y - from.Y);
        return (ushort) (((int) Math.Round(a * 4096.0 / (2 * Math.PI)) % 4096 + 4096) % 4096);
    }
}
