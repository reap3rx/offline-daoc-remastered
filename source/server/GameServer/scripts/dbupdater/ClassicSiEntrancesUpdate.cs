using System;
using System.Reflection;
using DOL.Database;

namespace DOL.GS.DatabaseUpdate
{
    /// <summary>
    /// The Shrouded Isles entrances where they were at first (owner 2026-11-05: "this remake ... has meant to put the
    /// portal to SI back where it was originally"; an invisible portal by Cotswold took a scout to the Isle of Glass).
    /// The new client's own zone exits are the classic portals - Avalon Marsh, Gotar, the Shannon Estuary - and send
    /// these zone points; the modern spots in Cotswold, Mularn and Mag Mell had a server-side pad each
    /// (ShroudedIslesPortals, now gone), invisible in this world. The zone points' source, where bots walk to cross,
    /// moves to the classic portal too. The way back (154, 166, 168) already lands at them. At every start.
    /// </summary>
    [DatabaseUpdate]
    public class ClassicSiEntrancesUpdate : IDatabaseUpdater
    {
        private static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        // zone point id, region, x, y, z: the middle of the client's exit (zonejump.csv) in world units
        private static readonly (ushort Id, ushort Region, int X, int Y, int Z)[] Classic =
        [
            (153, 1, 462038, 632414, 1713),     // ALB SI ENTRANCE: Avalon Marsh
            (165, 100, 771504, 835882, 4700),   // MID SI ENTRANCE: Gotar
            (167, 200, 309863, 644828, 4880),   // SILVERMINE > DOMNANN: the Shannon Estuary
        ];

        public void Update()
        {
            try
            {
                int moved = 0;
                foreach (var c in Classic)
                {
                    DbZonePoint zp = null;
                    foreach (DbZonePoint p in GameServer.Database.SelectObjects<DbZonePoint>(DB.Column("Id").IsEqualTo(c.Id)))
                        zp = p;
                    if (zp == null || zp.SourceRegion == c.Region && zp.SourceX == c.X && zp.SourceY == c.Y && zp.SourceZ == c.Z)
                        continue;
                    zp.SourceRegion = c.Region;
                    zp.SourceX = c.X;
                    zp.SourceY = c.Y;
                    zp.SourceZ = c.Z;
                    GameServer.Database.SaveObject(zp);
                    moved++;
                }
                if (moved > 0)
                    log.Info($"Shrouded Isles entrances: {moved} back at the classic portals");
            }
            catch (Exception e)
            {
                log.Error("Shrouded Isles entrances", e);
            }
        }
    }
}
