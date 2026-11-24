using System;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.Events;
using DOL.GS.Scripts;

namespace DOL.GS
{
    /// <summary>
    /// The realms' hard starts (owner 2026-11-24: "one deadly zone being a starting location for the crazies. The tryhard bots
    /// might favor this location on starting"; each realm gets one, "easy/medium/hard starting ones"): a start choice in
    /// level_bands.json marked "hard" - Hibernia's Culraid in Lough Gur. The old world never meant these villages for new
    /// characters, so at start-up each gets what a starting town needs and lacks: a master trainer (every class of the realm)
    /// and a bind point - only where none stands within 75 metres already. Nothing is saved: take the start away and they go.
    /// The bots' side is StartupLocations.ChooseAutonomousLocation.
    /// </summary>
    public static class HardStarts
    {
        const int Near = 3000;                               // 75 metres: something already there will do

        static readonly Dictionary<eRealm, (string name, ushort model)> Trainers = new()
        {
            [eRealm.Albion] = ("Master Trainer Corwin", 39),
            [eRealm.Midgard] = ("Master Trainer Hallvard", 153),
            [eRealm.Hibernia] = ("Master Trainer Fiachra", 302),
        };

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            foreach (eRealm realm in new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia })
                foreach (LevelBands.Start s in LevelBands.StartsOf(realm).Where(s => s.Hard))
                {
                    try { Furnish(realm, s); }
                    catch (Exception ex) { Console.WriteLine($"[HardStarts] {s.Name}: {ex.Message}"); }
                }
        }

        static void Furnish(eRealm realm, LevelBands.Start s)
        {
            Region region = WorldMgr.GetRegion(s.Region);
            if (region == null)
                return;
            if (s.Trainer is { Length: >= 3 } t && !region.Objects.OfType<GameTrainer>().Any(n => n != null && n.ObjectState == GameObject.eObjectState.Active
                    && Math.Abs(n.X - t[0]) < Near && Math.Abs(n.Y - t[1]) < Near))
            {
                var (name, model) = Trainers[realm];
                var tr = new AtlasTrainer
                {
                    Name = name, GuildName = "Master Trainer", Model = model, Realm = realm, Level = 50, Size = 50,
                    X = t[0], Y = t[1], Z = t[2], Heading = (ushort) (t.Length > 3 ? t[3] : 0), CurrentRegionID = s.Region,
                    Flags = GameNPC.eFlags.PEACE,
                };
                tr.LoadedFromScript = true;
                tr.AddToWorld();
                Console.WriteLine($"[HardStarts] {s.Name}: a master trainer");
            }
            if (s.Bind is { Length: >= 3 } b && !region.GetAreasOfSpot(b[0], b[1], b[2]).OfType<Area.BindArea>().Any())
            {
                var bp = new DbBindPoint { X = b[0], Y = b[1], Z = b[2], Region = s.Region, Radius = 750, Realm = (int) realm };
                region.AddArea(new Area.BindArea("bind point", bp));
                Console.WriteLine($"[HardStarts] {s.Name}: a bind point");
            }
        }
    }
}
