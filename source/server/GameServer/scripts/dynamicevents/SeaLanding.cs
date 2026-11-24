using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.AI.Brain;
using DOL.Events;
using DOL.GS.PacketHandler;

namespace DOL.GS.DynamicEvents
{
    /// <summary>
    /// A raid from the sea (owner 2026-11-23): an enemy realm's ships put in on a Hibernian coast as one of the zone's dynamic
    /// events - the landing, the captain, and, if nobody answers, a beachhead. This adds what an event can't: the ships in the bay
    /// while it runs, word to both realms, and - once the beachhead holds - patrols marching out to hunt Hibernians, players and
    /// bots alike. The Shannon Estuary's Albion landing and the Cliffs of Moher's Norse landings are two of these.
    ///
    /// Each one's window is public (WindowOpen, NextWindowUtc, Beachhead) so a later cross-realm raid (Roadmap Inbox: a
    /// recruiter at the raiders' own port, invaders who die respawning at their own bind) can line its sign-up up with it.
    /// </summary>
    public sealed class SeaLanding
    {
        public string ChainId;
        public string BeachheadStage = "l3";
        public eRealm From;                                  // whose ships they are (the word goes to that realm too)
        public ushort ShipModel;
        public string ShipName;
        public int ZoneX, ZoneY, WaterZ;                     // the zone's offset and the bay's water line (units)
        public (double x, double y, ushort heading)[] Ships = Array.Empty<(double, double, ushort)>();
        public (double x, double y)[][] Routes = Array.Empty<(double, double)[]>();
        public (int template, string name)[] Patrol = Array.Empty<(int, string)>();
        public string PatrolGuild;
        public int MaxPatrols = 2;
        public int PatrolEveryMs = 4 * 60_000;
        public string Sighted, SightedHome, Dug, Beaten, GoneHome, GaveUp, Marched;

        public int PatrolSize => Patrol.Length;

        readonly List<GameStaticItem> _ships = new();
        readonly List<List<EventNpc>> _patrols = new();
        ECSGameTimer _timer;
        long _nextPatrol;
        int _route;

        ChainRuntime Chain => DynamicEventManager.Chains.FirstOrDefault(c => c.Def.Id == ChainId);

        /// <summary>The fleet is in (the chain is running, or waiting for someone to answer it).</summary>
        public bool WindowOpen => Chain is ChainRuntime c && (c.Active || c.Dormant);
        /// <summary>The raiders hold their camp ashore.</summary>
        public bool Beachhead => Chain?.Stage?.Def.Id == BeachheadStage;
        /// <summary>When the next fleet is due (null while one is in, or the zone's events aren't loaded).</summary>
        public DateTime? NextWindowUtc
        {
            get
            {
                ChainRuntime c = Chain;
                if (c == null || WindowOpen)
                    return null;
                return DateTime.UtcNow.AddMilliseconds(Math.Max(0, c.NextStart - GameLoop.GameLoopTime));
            }
        }

        public void Hook()
        {
            DynamicEventManager.StageBeginning += (c, s) => { if (c.Def.Id == ChainId) Safe(() => Began(c, s)); };
            DynamicEventManager.ChainEnded += (c, o) => { if (c.Def.Id == ChainId) Safe(() => Ended(o)); };
        }

        static void Safe(Action a)
        {
            try { a(); }
            catch (Exception ex) { Console.WriteLine("[SeaLanding] " + ex.Message); }
        }

        void Began(ChainRuntime c, StageDef s)
        {
            if (_ships.Count == 0)
            {
                Launch(c);
                Tell(eRealm.Hibernia, Sighted);
                Tell(From, SightedHome);
            }
            if (s.Id == BeachheadStage)
            {
                _nextPatrol = GameLoop.GameLoopTime + 60_000;
                _timer ??= new ECSGameTimer(null, _ => { Safe(() => Tick(c)); return _timer == null ? 0 : 10_000; }, 10_000);
                Tell(eRealm.Hibernia, Dug);
            }
        }

        void Ended(string outcome)
        {
            foreach (GameStaticItem ship in _ships)
                if (ship.ObjectState == GameObject.eObjectState.Active)
                    ship.RemoveFromWorld();
            _ships.Clear();
            Disband();
            _timer?.Stop();
            _timer = null;
            if (outcome == "success")
                Tell(eRealm.Hibernia, Beaten);
            Tell(From, outcome == "success" ? GoneHome : GaveUp);
        }

        void Launch(ChainRuntime c)
        {
            foreach (var (x, y, heading) in Ships)
            {
                var ship = new GameStaticItem
                {
                    Name = ShipName, Model = ShipModel, Heading = heading, Realm = From,
                    X = ZoneX + (int) (x * 40), Y = ZoneY + (int) (y * 40), Z = WaterZ, CurrentRegion = c.Region
                };
                if (ship.AddToWorld())
                    _ships.Add(ship);
            }
        }

        void Tick(ChainRuntime c)
        {
            if (!Beachhead)
            {
                Disband();
                return;
            }
            foreach (List<EventNpc> p in _patrols.ToList())
            {
                p.RemoveAll(n => n == null || !n.IsAlive || n.ObjectState != GameObject.eObjectState.Active);
                if (p.Count == 0)
                    _patrols.Remove(p);
            }
            long now = GameLoop.GameLoopTime;
            if (now < _nextPatrol || _patrols.Count >= MaxPatrols || Routes.Length == 0)
                return;
            _nextPatrol = now + PatrolEveryMs;
            (double x, double y)[] route = Routes[_route++ % Routes.Length];
            Vector3[] way = route.Select(p => c.ToWorld(new[] { p.x, p.y })).ToArray();
            var patrol = new List<EventNpc>();
            int lv = Math.Max(c.Def.Levels?[0] ?? 20, 20);
            foreach (var (tpl, name) in Patrol)
            {
                EventNpc n = c.Make(tpl, name, lv + Util.Random(0, 2), 0, 0, null, PatrolGuild, c.Around(way[0], 3 * 40), EventRole.Hostile, null);
                if (n == null)
                    continue;
                n.SetOwnBrain(new PatrolBrain { Way = way, Leader = patrol.FirstOrDefault(), AggroLevel = 100, AggroRange = 700 });
                patrol.Add(n);
            }
            if (patrol.Count > 0)
            {
                _patrols.Add(patrol);
                foreach (GamePlayer pl in c.PlayersInZone())
                    pl.Out.SendMessage(Marched, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
        }

        void Disband()
        {
            foreach (EventNpc n in _patrols.SelectMany(p => p))
                if (n != null && n.ObjectState == GameObject.eObjectState.Active)
                    n.RemoveFromWorld();
            _patrols.Clear();
        }

        static void Tell(eRealm realm, string words)
        {
            if (string.IsNullOrEmpty(words))
                return;
            foreach (GamePlayer p in ClientService.Instance.GetPlayers())
                if (p != null && p.Realm == realm)
                    p.Out.SendMessage(words, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        /// <summary>The patrols' mind: walk the route out and back; any Hibernian - player or bot - that comes in sight is
        /// hunted down (owner: "patrols that will attack Hibernian players and bots"). A raiding party passes through a town
        /// and moves on: it never stops to hold anything (owner 2026-11-23, the Norse: "only a skirmish and then move on").</summary>
        public class PatrolBrain : EventMobBrain
        {
            public Vector3[] Way;
            public GameNPC Leader;              // the patrol's first: the others keep with it
            int _leg;
            long _nextLook;

            public static bool Hunts(GameLiving l) =>
                l != null && l.IsAlive && l.Realm == eRealm.Hibernia && (l is GamePlayer || l is GameBot) &&
                l.ObjectState == GameObject.eObjectState.Active;

            public override void Think()
            {
                if (Body != null && Body.IsAlive && !HasAggro && GameLoop.GameLoopTime >= _nextLook)
                {
                    _nextLook = GameLoop.GameLoopTime + 2000;
                    GameLiving prey = Body.GetPlayersInRadius(900).Cast<GameLiving>()
                        .Concat(Body.GetNPCsInRadius(900).OfType<GameBot>())
                        .Where(Hunts).OrderBy(l => Body.GetDistanceTo(l)).FirstOrDefault();
                    if (prey != null)
                        Goal = prey;
                    else if (Goal == null && Way != null && Way.Length > 0 && !Body.IsMoving)
                    {
                        if (Leader != null && Leader.IsAlive && Leader.ObjectState == GameObject.eObjectState.Active)
                        {
                            if (!Body.IsWithinRadius(Leader, 160))
                                Body.PathTo(EventFollowSlots.Of(Body, Leader), Body.MaxSpeed);
                        }
                        else
                        {
                            Vector3 next = Way[_leg % Way.Length];
                            if (Vector2.DistanceSquared(new(Body.X, Body.Y), new(next.X, next.Y)) < 120f * 120f)
                                next = Way[++_leg % Way.Length];
                            Body.PathTo(next, (short) Math.Max(100, Body.MaxSpeed / 2));
                        }
                    }
                }
                base.Think();
            }
        }
    }

    /// <summary>The Shannon Estuary's Albion landing (owner 2026-11-23: "Albion ships and 'mobs' ... on the coast near the top
    /// left of the map, and staging a camp there. If they get established, they will send out patrols that will attack
    /// Hibernian players and bots").</summary>
    public static class AlbionLanding
    {
        public const string ChainId = "shannon_albion_landing";
        public const string BeachheadStage = "l3";
        public static readonly SeaLanding L = new()
        {
            ChainId = ChainId, BeachheadStage = BeachheadStage, From = eRealm.Albion, ShipModel = 2646, ShipName = "Albion ship",
            ZoneX = 286720, ZoneY = 614400, WaterZ = 4612,
            Ships = new[] { (45.0, 340.0, (ushort) 1024), (60.0, 445.0, (ushort) 1100) },
            Routes = new[]
            {
                new[] { (200.0, 410.0), (260.0, 470.0), (250.0, 560.0), (290.0, 620.0), (250.0, 560.0), (260.0, 470.0) },   // the strand toward Connla
                new[] { (200.0, 410.0), (300.0, 360.0), (420.0, 330.0), (540.0, 380.0), (420.0, 330.0), (300.0, 360.0) },   // the north bank
            },
            Patrol = new[] { (60167629, "Albion footman"), (60157693, "Albion bowman"), (60161836, "Albion sergeant") },
            PatrolGuild = "the Saltmarsh Company patrol",
            Sighted = "Albion sails in the bay north of Connla! The Saltmarsh Company is landing on the Shannon Estuary's north-west coast.",
            SightedHome = "Word on the docks: the Saltmarsh Company has sailed to raid the Hibernian coast at the Shannon Estuary.",
            Dug = "The Albions have a beachhead on the Shannon Estuary's north-west coast - their patrols are hunting Hibernians!",
            Beaten = "The Albion landing on the Shannon Estuary is beaten. Their sails are turning for home.",
            GoneHome = "The Saltmarsh Company is limping home from Hibernia.",
            GaveUp = "The Saltmarsh Company has given up its Hibernian beachhead.",
            Marched = "An Albion patrol has marched out of the beachhead."
        };
        public static (double x, double y)[][] Routes => L.Routes;
        public static int MaxPatrols => L.MaxPatrols;
        public static int PatrolSize => L.PatrolSize;
        public static bool WindowOpen => L.WindowOpen;
        public static bool Beachhead => L.Beachhead;
        public static DateTime? NextWindowUtc => L.NextWindowUtc;

        public class PatrolBrain : SeaLanding.PatrolBrain { }

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args) => L.Hook();
    }

    /// <summary>The Cliffs of Moher's Norse landings (owner 2026-11-23: "an invasion scenario there as well, this time from
    /// Midgard"; the raiders are "a raiding party, trying to sew chaos around the realm. If they attack Tir Urphost, it will
    /// only be a skirmish and then move on, not an occupation"). The Grey Man's fog hides the longships until they're ashore.</summary>
    public static class NorseLanding
    {
        public const string ChainId = "cliffs_longships";
        public const string BeachheadStage = "l3";
        public static readonly SeaLanding L = new()
        {
            ChainId = ChainId, BeachheadStage = BeachheadStage, From = eRealm.Midgard, ShipModel = 1615, ShipName = "Midgard longship",
            ZoneX = 221184, ZoneY = 417792, WaterZ = 1170,
            Ships = new[] { (45.0, 590.0, (ushort) 1024), (60.0, 690.0, (ushort) 980) },
            Routes = new[]
            {
                // up the ravine from the middle cove, across the fields to the edge of Tir Urphost (a skirmish), on to the
                // watchtower road, and back down
                new[] { (180.0, 640.0), (300.0, 700.0), (450.0, 650.0), (600.0, 620.0), (650.0, 560.0), (760.0, 420.0), (600.0, 620.0), (450.0, 650.0), (300.0, 700.0) },
                // south along the shingle, up onto the southern cliff tops and across toward the moor
                new[] { (180.0, 640.0), (200.0, 900.0), (420.0, 900.0), (550.0, 780.0), (420.0, 900.0), (200.0, 900.0) },
            },
            Patrol = new[] { (60167667, "Norse raider"), (60167654, "Norse bowman"), (60159139, "Norse huscarl") },
            PatrolGuild = "the Saltwolves' raiding party",
            Sighted = "Longships out of the fog under the Cliffs of Moher! Norse raiders are coming ashore in the middle cove.",
            SightedHome = "Word in the mead-halls: the Saltwolves have sailed to raid the Hibernian coast at the Cliffs of Moher.",
            Dug = "The Norse are ashore under the Cliffs of Moher - their raiding parties are loose on the cliff paths!",
            Beaten = "The Norse landing under the Cliffs of Moher is thrown back into the sea.",
            GoneHome = "The Saltwolves are rowing home from Hibernia with empty holds.",
            GaveUp = "The Saltwolves have burned their camp on the Hibernian shore and sailed for home.",
            Marched = "A Norse raiding party has climbed out of the cove."
        };
        public static (double x, double y)[][] Routes => L.Routes;
        public static int MaxPatrols => L.MaxPatrols;
        public static int PatrolSize => L.PatrolSize;
        public static bool WindowOpen => L.WindowOpen;
        public static bool Beachhead => L.Beachhead;
        public static DateTime? NextWindowUtc => L.NextWindowUtc;

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args) => L.Hook();
    }
}
