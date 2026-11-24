using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Reflection;
using DOL.AI.Brain;
using DOL.Database;
using DOL.GS.PacketHandler;
using DOL.GS.Reputation;
using DOL.GS.StoryQuests;
using Newtonsoft.Json;

namespace DOL.GS.DynamicEvents
{
    // A zone's siege (owner 2026-11-22, the Lough Derg plan's Dergan Island): one big group objective that changes the zone
    // when it's won and fights back afterwards. The zone's events feed a meter - its people's resolve - and failed ones
    // the enemy's strength. A full meter opens the assault: criers call it in the towns, a giver at a staging camp leads
    // it once enough are gathered (bots count), and its chain (cull, wards, boss, hold) takes the place. Held, the
    // place's garrison is gone (its zone build sites stay empty), a camp with its own vendors stands there, and after a
    // few real hours the enemy raids it - each raid sooner and harder; held off, the hold goes on; the last brings their
    // leader back with an army, and in the end the place falls and it all begins again. All of it is data in the zone's
    // events file ("siege"); the chains it starts are ordinary chains marked "manual". Its state outlasts a restart
    // (zone-sieges-state.json). See README.md.

    public class SiegeDef
    {
        public string Id;
        public string Name;                        // "Dergan Island"
        public string Enemy;                       // "the Dergans"
        [JsonProperty("resolve_name")] public string ResolveName = "Resolve";
        [JsonProperty("enemy_name")] public string EnemyName = "Enemy strength";
        public string Faction;                     // the reputation faction its camp serves (scripts/reputation)
        // (claude 2026-11-24, the Cursed Forest brief) a campaign's battle: no meters - it opens, raids and resets only
        // when the campaign says (LugCampaign: the Forest Gate is King Lug's first battle)
        public string Campaign;
        public Dictionary<string, int> Feeds = new();            // chain id: resolve when it is won
        [JsonProperty("feed_default")] public int FeedDefault;  // any other chain of the zone won
        public Dictionary<string, int> Quests = new();           // story quest id: resolve when someone finishes it
        [JsonProperty("enemy_feeds")] public Dictionary<string, int> EnemyFeeds = new();   // chain id: strength when lost
        [JsonProperty("enemy_default")] public int EnemyDefault = 5;
        [JsonProperty("war_chain")] public string WarChain;      // the enemy's own chain: it comes oftener as they grow
        public string Assault;                     // the chain that takes the place
        public List<string> Raids = new();         // the counter-attacks in order (the last one repeats, harder each time)
        [JsonProperty("last_raid")] public string LastRaid;      // their leader's return: lost, the place falls
        [JsonProperty("hold_h")] public double HoldH = 3;        // real hours before the first raid
        [JsonProperty("bots_go_after_m")] public double BotsGoAfterM = 45;   // open this long, the bots set out without
                                                   // a player (owner 2026-11-22) - three raids' answering time, well inside the hold
        [JsonProperty("raid_gap_h")] public List<double> RaidGapH = new();   // (none given: 2, 1.5, then 1 hour)
        public List<string> Criers = new();        // story NPC ids who call the news in the towns
        [JsonProperty("open_text")] public string OpenText;
        [JsonProperty("taken_text")] public string TakenText;
        [JsonProperty("repelled_text")] public string RepelledText;
        [JsonProperty("raid_text")] public string RaidText;
        [JsonProperty("held_text")] public string HeldText;
        [JsonProperty("fall_text")] public string FallText;
        [JsonProperty("carry_text")] public string CarryText = "The roane carry you across the water.";   // the war band
                                                   // taken to the landing (and a ferry ride)
        [JsonProperty("carried_cry")] public string CarriedCry = "The war band wouldn't wait any longer - the roane have carried them across to {0}!";
        public List<string> Sites = new();         // zone build sites (scripts/zonebuilds) that empty while it is held
        public double[] Staging;                   // where the war band gathers (the giver's post)
        public double[] Landing;                   // where the giver carries them
        public double[] Area;                      // the place itself: [x, y, radius m] (an island: who is on it)
        [JsonProperty("camp_npcs")] public List<SiegeNpcDef> CampNpcs = new();
        public List<SiegeNpcDef> Holdouts = new(); // a few of the enemy who stay on (the bounty master's island hunts)
        [JsonProperty("hostile_tier")] public string HostileTier = "yellow";
        // the realm's people near the place who are only there while it's held (owner 2026-11-23, Bugs & Fixes: the Forest
        // Gate's stable master and horse "should only come in when the Rangers hold the cursed forest entrance"): by name,
        // within held_only_m of the place
        [JsonProperty("held_only")] public List<string> HeldOnly = new();
        [JsonProperty("held_only_m")] public double HeldOnlyM = 200;   // its chains' ordinary monsters' con
                                                   // (an elite place: not the zone's rating's; bosses still go by head count)
        [JsonIgnore] public ZoneEventsDef ZoneDef;
    }

    public class SiegeNpcDef : NpcDef
    {
        public string Kind = "idle";               // idle | marks (sells for Marks of Valor) | coin | ferry | holdout
        public string Greet;
        public string Idle;                        // said now and then
        public List<SiegeStockDef> Stock = new();
        public double[] To;                        // a ferry: where it carries you
        [JsonProperty("respawn_s")] public int RespawnS = 300;
        public string Tier;                        // a holdout's con
    }

    public class SiegeStockDef
    {
        public string Item;
        public int Price;                          // marks (a marks merchant) - a coin merchant keeps the item's price
    }

    public enum SiegePhase { Building, Open, Assault, Held }

    /// <summary>A siege's state, apart from the world (tested on its own): the two meters, the phase, the hold and the
    /// raids.</summary>
    public class SiegeState
    {
        public double Resolve;
        public double Enemy;
        public SiegePhase Phase;
        public DateTime HeldSinceUtc;
        public DateTime OpenedUtc;                 // when the assault opened (the bots' patience runs from it)
        public DateTime NextRaidUtc;
        public int RaidIndex;                      // raids held off so far
        public string RaidRunning;                 // the raid chain under way (or waiting for someone to answer it)

        /// <summary>The meter grows (to 100); true when that fills it and the assault opens.</summary>
        public bool AddResolve(double pts)
        {
            if (Phase != SiegePhase.Building || pts <= 0)
                return false;
            Resolve = Math.Min(100, Resolve + pts);
            if (Resolve < 100)
                return false;
            Phase = SiegePhase.Open;
            OpenedUtc = DateTime.UtcNow;
            return true;
        }

        public void AddEnemy(double pts)
        {
            if (Phase is SiegePhase.Building or SiegePhase.Open)
                Enemy = Math.Clamp(Enemy + pts, 0, 100);
        }

        /// <summary>How much tougher their side is (the assault's defenders, by the strength they've gathered).</summary>
        public double AssaultToughness => 1 + 0.5 * Enemy / 100.0;

        /// <summary>A raid's monsters: each held-off raid makes the next one harder.</summary>
        public double RaidToughness => 1 + 0.2 * RaidIndex;

        /// <summary>The enemy's own chain comes oftener as they grow: down to half its quiet time at full strength.</summary>
        public double WarInterval => 1 - 0.5 * Enemy / 100.0;

        public void Captured(DateTime nowUtc, SiegeDef d)
        {
            Phase = SiegePhase.Held;
            HeldSinceUtc = nowUtc;
            NextRaidUtc = nowUtc.AddHours(Math.Max(0.01, d.HoldH));
            RaidIndex = 0;
            RaidRunning = null;
            Resolve = 100;
            Enemy = 0;
        }

        /// <summary>The assault thrown back: the resolve sags, the enemy takes heart.</summary>
        public void Repelled()
        {
            Phase = SiegePhase.Building;
            Resolve = 65;
            Enemy = Math.Min(100, Enemy + 15);
        }

        /// <summary>Which raid comes next: the listed ones in turn, then the last one (again and again).</summary>
        public string NextRaid(SiegeDef d) => RaidIndex < d.Raids.Count ? d.Raids[RaidIndex] : d.LastRaid ?? d.Raids.LastOrDefault();

        public void RaidHeld(DateTime nowUtc, SiegeDef d)
        {
            RaidRunning = null;
            List<double> gaps = d.RaidGapH.Count > 0 ? d.RaidGapH : new List<double> { 2, 1.5, 1 };
            double gap = gaps[Math.Min(RaidIndex, gaps.Count - 1)];
            RaidIndex++;
            NextRaidUtc = nowUtc.AddHours(Math.Max(0.01, gap));
        }

        public void Fell()
        {
            Phase = SiegePhase.Building;
            Resolve = 0;
            Enemy = 0;
            RaidIndex = 0;
            RaidRunning = null;
        }
    }

    /// <summary>One zone's siege in the world.</summary>
    public class SiegeRuntime
    {
        public readonly SiegeDef Def;
        public SiegeState State = new();
        public ChainRuntime Assault;
        public readonly Dictionary<string, ChainRuntime> RaidChains = new();
        public ChainRuntime War;
        public Region Region;
        public Zone Zone;
        readonly HashSet<string> _lostThisRun = new();
        readonly List<GameNPC> _hidden = new();
        readonly List<GameNPC> _heldOnly = new();
        bool _heldOnlyFound;
        long _nextHeldOnly;

        /// <summary>The place's held-only people (Def.HeldOnly): in the world while it's held, away the rest of the time.</summary>
        void KeepHeldOnly(long now)
        {
            if (Def.HeldOnly.Count == 0 || now < _nextHeldOnly || Def.Area == null)
                return;
            _nextHeldOnly = now + 5000;
            if (!_heldOnlyFound)
            {
                _heldOnlyFound = true;
                Vector3 c = World(new[] { Def.Area[0], Def.Area[1] });
                var names = new HashSet<string>(Def.HeldOnly, StringComparer.OrdinalIgnoreCase);
                foreach (GameNPC n in Region.GetNPCsInRadius(new Point3D((int) c.X, (int) c.Y, (int) c.Z), (ushort) Math.Min(65000, Def.HeldOnlyM * 40)))
                    if (names.Contains(n.Name) && n.Realm != eRealm.None)
                        _heldOnly.Add(n);
            }
            bool held = State.Phase == SiegePhase.Held;
            foreach (GameNPC n in _heldOnly)
                if (held && n.ObjectState != GameObject.eObjectState.Active && n.ObjectState != GameObject.eObjectState.Deleted)
                    n.AddToWorld();
                else if (!held && n.ObjectState == GameObject.eObjectState.Active)
                    n.RemoveFromWorld();
        }
        readonly List<GameNPC> _camp = new();
        long _nextSweep, _nextTell, _nextIdle;

        public SiegeRuntime(SiegeDef def) => Def = def;

        public bool IsMine(ChainRuntime c) => c != null && c.Zone == Zone && c.Region == Region;
        public bool IsSiegeChain(ChainRuntime c) => c == Assault || RaidChains.ContainsValue(c);

        public Vector3 World(double[] p) => Assault != null ? Assault.ToWorld(p) :
            new Vector3((float) (Zone.XOffset + p[0] * 40), (float) (Zone.YOffset + p[1] * 40), p.Length > 2 ? (float) (p[2] * 40) : 0);

        public IEnumerable<GamePlayer> PlayersInZone() =>
            ClientService.Instance.GetPlayers().Where(p => p?.CurrentRegion == Region && p.CurrentZone == Zone && p.ObjectState == GameObject.eObjectState.Active);

        public void Tell(string text, bool screen = false)
        {
            if (string.IsNullOrEmpty(text))
                return;
            foreach (GamePlayer p in PlayersInZone())
            {
                if (screen)
                    p.Out.SendMessage($"{Def.Name}", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                p.Out.SendMessage($"[{Def.Name}] {text}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
        }

        /// <summary>The criers in the towns say it aloud (their bubbles), and the zone hears it.</summary>
        public void Cry(string text)
        {
            if (string.IsNullOrEmpty(text))
                return;
            foreach (string id in Def.Criers)
                try
                {
                    if (StoryQuestManager.Npc(id) is GameNPC n && n.ObjectState == GameObject.eObjectState.Active)
                        NpcSpeech.Say(n, text);
                }
                catch (Exception) { }
            Tell(text, true);
        }

        // ------------------------------------------------------------------ what feeds the meters

        public void OnChainEnded(ChainRuntime c, string outcome, long now)
        {
            if (c == Assault)
            {
                if (outcome == "success")
                    Capture(now);
                else
                {
                    State.Repelled();
                    RestoreGarrison();
                    Cry(Def.RepelledText ?? $"The assault on {Def.Name} is thrown back. {Def.Enemy} take heart.");
                    ZoneSiege.Tell(this, "repelled");
                }
                ZoneSiege.Save();
                return;
            }
            if (RaidChains.ContainsValue(c))
            {
                if (State.Phase != SiegePhase.Held)
                    return;
                if (outcome == "success")
                {
                    State.RaidHeld(DateTime.UtcNow, Def);
                    Cry(Def.HeldText ?? $"The raid on {Def.Name} is beaten off. The camp stands.");
                    ZoneSiege.Tell(this, "held");
                }
                else
                    Fall();
                ZoneSiege.Save();
                return;
            }
            if (!IsMine(c) || c.Private || Def.Campaign != null)
                return;
            bool lost = _lostThisRun.Remove(c.Def.Id);
            if (outcome == "success")
            {
                double pts = Def.Feeds.TryGetValue(c.Def.Id, out int f) ? f : Def.FeedDefault;
                if (lost)
                    pts /= 2;                        // (won back after it went their way: half)
                Feed(pts, c.Def.Title);
            }
        }

        public void OnStageEnded(ChainRuntime c, StageDef s, bool won)
        {
            if (won || !IsMine(c) || c.Private || IsSiegeChain(c) || Def.Campaign != null || !_lostThisRun.Add(c.Def.Id))
                return;
            int pts = Def.EnemyFeeds.TryGetValue(c.Def.Id, out int f) ? f : Def.EnemyDefault;
            State.AddEnemy(pts);
        }

        public void OnQuestFinished(GamePlayer p, string questId)
        {
            if (p?.CurrentRegion == Region && Def.Quests.TryGetValue(questId ?? "", out int pts))
                Feed(pts, null);
        }

        public void Feed(double pts, string what)
        {
            if (pts <= 0 || State.Phase != SiegePhase.Building || Def.Campaign != null)
                return;
            if (State.AddResolve(pts))
            {
                Cry(Def.OpenText ?? $"{Def.ResolveName} is high! The assault on {Def.Name} can begin - gather at the staging camp.");
                ZoneSiege.Save();
            }
        }

        // ------------------------------------------------------------------ the assault

        /// <summary>Minutes until the bots set out on their own (0: they would now).</summary>
        public double BotsGoInM => Math.Max(0, Def.BotsGoAfterM - (DateTime.UtcNow - State.OpenedUtc).TotalMinutes);

        /// <summary>Why the war band can't set out yet (null: it can) - enough people at the giver, you among them, or,
        /// once the bots have waited long enough, enough of them alone.</summary>
        public string Gate()
        {
            if (Assault?.Leader is not EventNpc g)
                return "Not yet.";
            var near = Assault.PeopleNear(new Point3D(g.X, g.Y, g.Z), 2000).Concat(WarBand(Environment.TickCount64)).Distinct().ToList();
            int need = Math.Max(1, Assault.Def.MinPeople);
            if (near.Count < need)
                return $"Not with so few - {near.Count} of {need}. Gather more here, then tell me you're [{Assault.Def.Giver.Accept}].";
            if (!near.Any(p => p is GamePlayer) && BotsGoInM > 0)
                return "We wait for someone to lead it.";
            return null;
        }

        /// <summary>The war band crosses: everyone gathered at the giver (and the giver, and their party) is carried to
        /// the landing.</summary>
        public void Ferry(ChainRuntime c)
        {
            SweepGarrison();                         // (the assault's own monsters hold it now)
            if (Def.Landing == null || c.Leader is not EventNpc g)
                return;
            Vector3 land = World(Def.Landing);
            var who = c.PeopleNear(new Point3D(g.X, g.Y, g.Z), 2400).Concat(WarBand(Environment.TickCount64)).Distinct().ToList();
            _arrived.Clear();
            if (!who.Any(p => p is GamePlayer))
                Cry(string.Format(Def.CarriedCry ?? "{0}", Def.Name));
            foreach (GameLiving l in who)
            {
                Vector3 at = c.Around(land, 300);
                if (l is GamePlayer p)
                {
                    p.Out.SendMessage(Def.CarryText, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                    p.MoveTo(Region.ID, (int) at.X, (int) at.Y, (int) at.Z, p.Heading);
                }
                else
                    l.MoveTo(Region.ID, (int) at.X, (int) at.Y, (int) at.Z, l.Heading);
            }
            foreach (EventNpc n in c.Guards.Append(g).Where(n => n != null && n.IsAlive))
            {
                Vector3 at = c.Around(land, 200);
                n.MoveTo(Region.ID, (int) at.X, (int) at.Y, (int) at.Z, n.Heading);
            }
        }

        // ------------------------------------------------------------------ taken, held, lost

        public void Capture(long now)
        {
            State.Captured(DateTime.UtcNow, Def);
            Cry(Def.TakenText ?? $"{Def.Name} is ours!");
            SweepGarrison();
            KeepCamp();
            ZoneSiege.Save();
            ZoneSiege.Tell(this, "taken");
        }

        public void Fall(bool quiet = false)
        {
            State.Fell();
            if (!quiet)
                Cry(Def.FallText ?? $"{Def.Name} has fallen to {Def.Enemy}.");
            foreach (GameNPC n in _camp)
                try { n.Delete(); } catch (Exception) { }
            _camp.Clear();
            RestoreGarrison();
            ZoneSiege.Save();
            if (!quiet)
                ZoneSiege.Tell(this, "fell");
        }

        // ------------------------------------------------------------------ a campaign's battle (Def.Campaign)

        /// <summary>The campaign opens the assault: the giver comes, the war band gathers.</summary>
        public void CampaignOpen()
        {
            if (State.Phase == SiegePhase.Held)
                return;
            State.Phase = SiegePhase.Open;
            State.Resolve = 100;
            State.OpenedUtc = DateTime.UtcNow;
            ZoneSiege.Save();
        }

        /// <summary>The campaign sends the enemy back for the place now (a counter-attack): its raid begins at once,
        /// and the defenders hold as long as they can.</summary>
        public bool CampaignRaid(long now)
        {
            if (State.Phase != SiegePhase.Held || State.RaidRunning != null)
                return false;
            string id = State.NextRaid(Def);
            if (id == null || !RaidChains.TryGetValue(id, out ChainRuntime c) || c.Active)
                return false;
            c.Toughness = State.RaidToughness;
            State.RaidRunning = id;
            Cry(Def.RaidText ?? c.Def.Hint);
            c.Begin(c.Def.Start, now);
            ZoneSiege.Save();
            return true;
        }

        public bool RaidUnderWay => State.RaidRunning != null;

        /// <summary>The campaign is over (won and spent, or lost): back to the start, quietly.</summary>
        public void CampaignReset()
        {
            Resetting = true;
            try
            {
                Fall(true);
                foreach (ChainRuntime c in RaidChains.Values.Append(Assault).Where(c => c != null && (c.Active || c.Dormant)))
                    try { c.End("fail", Environment.TickCount64); } catch (Exception) { }
                State.Fell();
                ZoneSiege.Save();
            }
            finally { Resetting = false; }
        }

        public bool Resetting;

        /// <summary>While it is held its garrison is away: what the zone build placed there is taken out (and taken out
        /// again when it comes back from the dead); the rest of the time they are put back.</summary>
        void SweepGarrison()
        {
            foreach (string site in Def.Sites)
                foreach (GameNPC n in ZoneBuilds.SiteNpcs(Zone.ID, site))
                    if (n.ObjectState == GameObject.eObjectState.Active && n.IsAlive && !n.InCombat)
                    {
                        n.RemoveFromWorld();
                        if (!_hidden.Contains(n))
                            _hidden.Add(n);
                    }
        }

        void RestoreGarrison()
        {
            foreach (GameNPC n in _hidden)
                if (n.ObjectState != GameObject.eObjectState.Active && n.ObjectState != GameObject.eObjectState.Deleted)
                {
                    n.Health = n.MaxHealth;
                    n.AddToWorld();
                }
            _hidden.Clear();
        }

        /// <summary>The camp: its people and vendors, the ferries, and the holdouts the bounty master sends you after.</summary>
        void KeepCamp()
        {
            _camp.RemoveAll(n => n == null || n.ObjectState == GameObject.eObjectState.Deleted);
            if (_camp.Count > 0)
                return;
            foreach (SiegeNpcDef d in Def.CampNpcs.Concat(Def.Holdouts))
                for (int i = 0; i < Math.Max(1, d.Count); i++)
                    try
                    {
                        GameNPC n = MakeCampNpc(d, i);
                        if (n != null)
                            _camp.Add(n);
                    }
                    catch (Exception e)
                    {
                        Console.WriteLine($"[Siege] {d.Name}: {e.Message}");
                    }
        }

        GameNPC MakeCampNpc(SiegeNpcDef d, int i)
        {
            GameNPC n = d.Kind switch
            {
                "marks" => new SiegeMarksMerchant { Siege = this, Def = d },
                "coin" => new SiegeCoinMerchant { Siege = this, Def = d },
                "ferry" => new SiegeFerry { Siege = this, Def = d },
                _ => new SiegeCampNpc { Siege = this, Def = d }
            };
            if (d.Template > 0 && NpcTemplateMgr.GetTemplate(d.Template) is NpcTemplate tpl)
                n.LoadTemplate(tpl);
            n.Name = d.Name;
            n.GuildName = d.Guild ?? "";
            n.Level = (byte) Math.Max(1, d.Level);
            if (d.Model > 0) n.Model = d.Model;
            if (d.Size > 0) n.Size = d.Size;
            if (!string.IsNullOrEmpty(d.Equipment))
                n.LoadEquipmentTemplateFromDatabase(d.Equipment);
            Vector3 at = d.Kind == "holdout" || i > 0 ? Assault.Around(World(d.Pos), d.Kind == "holdout" ? 500 : 120) : World(d.Pos);
            n.X = (int) at.X;
            n.Y = (int) at.Y;
            n.Z = (int) at.Z;
            n.Heading = d.Pos != null && d.Pos.Length > 3 ? (ushort) d.Pos[3] : (ushort) Util.Random(4095);
            n.CurrentRegion = Region;
            n.LoadedFromScript = true;
            if (d.Kind == "holdout")
            {
                n.Realm = eRealm.None;
                n.RespawnInterval = Math.Max(30, d.RespawnS) * 1000;
                n.SetOwnBrain(new StandardMobBrain { AggroLevel = 100, AggroRange = 450 });
            }
            else
            {
                n.Realm = Assault.HomeRealm;
                n.Flags |= GameNPC.eFlags.PEACE;
                n.RespawnInterval = -1;
            }
            if (d.Kind == "coin" && n is SiegeCoinMerchant cm)
                cm.Stock();
            if (!n.AddToWorld())
                return null;
            n.SpawnPoint = new Point3D(n.X, n.Y, n.Z);
            if (d.Kind == "holdout" && d.Tier != null)
            {
                int t = Array.IndexOf(new[] { "grey", "green", "blue", "yellow", "orange", "red", "purple" }, d.Tier.ToLowerInvariant());
                if (t >= 0)
                    MonsterTiers.SetTier(n, (sbyte) (t - 3));
            }
            return n;
        }

        // ------------------------------------------------------------------ bots across the water

        long _nextFerry;
        readonly Dictionary<GameBot, long> _signedUp = new();
        readonly Dictionary<GameBot, long> _arrived = new();   // bots that reached the giver (they count for 10 minutes)

        /// <summary>The bots of the war band: those that reached the staging camp in the last ten minutes. A bot doesn't
        /// stand still while it waits (live test 22 Nov: they came and went), so having come is what counts.</summary>
        public List<GameBot> WarBand(long now) => _arrived.Where(kv => now - kv.Value < 600_000 && kv.Key.IsAlive &&
            kv.Key.ObjectState == GameObject.eObjectState.Active && kv.Key.CurrentRegion == Region).Select(kv => kv.Key).ToList();

        /// <summary>Whether someone is on the place (the island) - within its Area.</summary>
        public bool OnIsland(GameObject o)
        {
            if (Def.Area == null || Def.Area.Length < 3 || o == null)
                return true;
            Vector3 c = World(new[] { Def.Area[0], Def.Area[1] });
            double dx = o.X - c.X, dy = o.Y - c.Y;
            return Math.Sqrt(dx * dx + dy * dy) <= Def.Area[2] * 40;
        }

        /// <summary>The fight is on the island (the assault under way, a raid on the camp): a bot not on it goes to the
        /// roane at the staging camp first.</summary>
        public Vector3? BotWaypoint(ChainRuntime c, GameBot bot)
        {
            if (Def.Staging == null || Def.Area == null || OnIsland(bot))
                return null;
            return BotWaypointFor(c) ? World(Def.Staging) : null;
        }

        /// <summary>Bots with the assault or a raid who have reached the staging camp are carried across (players take
        /// the ferry themselves, or come with the war band).</summary>
        void FerryBots(long now)
        {
            if (now < _nextFerry || Def.Staging == null)
                return;
            _nextFerry = now + 3000;
            Vector3 staging = World(Def.Staging);
            var shore = new Point3D((int) staging.X, (int) staging.Y, (int) staging.Z);
            // the war band gathering (the assault open, or a raid on): a bot that signed up a while ago and is still far
            // off rides in to the staging camp - the region is wide and they have their own business on the way
            // (live test 22 Nov: twelve signed up, one had arrived three minutes later)
            bool gathering = State.Phase is SiegePhase.Open or SiegePhase.Assault ||
                (State.Phase == SiegePhase.Held && RaidChains.Values.Any(r => r.Active || r.Dormant));
            if (gathering)
                foreach (ChainRuntime c in RaidChains.Values.Append(Assault).Where(c => c != null && (c.Active || c.Dormant || c.Leader != null)))
                    foreach (GameBot b in DynamicEventManager.BotsWith(c))
                    {
                        if (c == Assault && c.Leader is EventNpc giver && b.IsWithinRadius(giver, 2000))
                            _arrived[b] = now;
                        if (!_signedUp.TryGetValue(b, out long since))
                        {
                            _signedUp[b] = now;
                            continue;
                        }
                        if (now - since < 120_000 || OnIsland(b) || b.IsWithinRadius(shore, 24000))
                            continue;
                        if (b.InCombat)
                        {
                            _signedUp[b] = now - 100_000;   // (after this fight)
                            continue;
                        }
                        Vector3 at = c.Around(staging, 600);
                        int far = (int) (b.GetDistanceTo(shore) / 40);
                        b.StopMoving();
                        b.MoveTo(Region.ID, (int) at.X, (int) at.Y, (int) at.Z, b.Heading);
                        Console.WriteLine($"[Siege] {b.Name} rides in to the staging camp from {far} m ({(b.IsWithinRadius(shore, 3000) ? "there" : "not there")})");
                        _signedUp[b] = now;
                    }
            else
            {
                _signedUp.Clear();
                _arrived.Clear();
            }
            foreach (ChainRuntime c in RaidChains.Values.Append(Assault).Where(c => c != null))
            {
                if (BotWaypointFor(c) == false)
                    continue;
                Vector3 to = World(c == Assault ? Def.Landing ?? Def.Staging : Def.CampNpcs.FirstOrDefault()?.Pos ?? Def.Landing);
                foreach (GameBot b in DynamicEventManager.BotsWith(c))
                    if (!OnIsland(b) && b.IsWithinRadius(shore, 1600) && !b.InCombat)
                    {
                        Vector3 at = c.Around(to, 250);
                        b.MoveTo(Region.ID, (int) at.X, (int) at.Y, (int) at.Z, b.Heading);
                    }
            }
        }

        bool BotWaypointFor(ChainRuntime c) => (c == Assault && c.Stage != null) ||
            (RaidChains.ContainsValue(c) && State.Phase == SiegePhase.Held && (c.Active || c.Dormant));

        // ------------------------------------------------------------------ every second

        public void Tick(long now)
        {
            if (Assault != null)
            {
                Assault.Toughness = State.AssaultToughness;
                if (State.Phase == SiegePhase.Open && Assault.Active)
                    State.Phase = SiegePhase.Assault;
                else if (State.Phase == SiegePhase.Assault && !Assault.Active)
                    State.Phase = SiegePhase.Open;       // (it ended without word - a restart, a GM stop)
            }
            if (War != null)
                War.IntervalMult = State.WarInterval;
            FerryBots(now);
            KeepHeldOnly(now);
            if (State.Phase == SiegePhase.Held)
            {
                if (now >= _nextSweep)
                {
                    _nextSweep = now + 15_000;
                    SweepGarrison();
                    KeepCamp();
                }
                if (Def.Campaign == null)
                    TickRaids(now);
                else if (State.RaidRunning != null && RaidChains.TryGetValue(State.RaidRunning, out ChainRuntime rr) && !rr.Active && !rr.Dormant)
                    State.RaidRunning = null;
                if (now >= _nextIdle)
                {
                    _nextIdle = now + 90_000;
                    GameNPC who = _camp.Where(n => n is SiegeCampNpc c && !string.IsNullOrEmpty(c.Def.Idle) && n.ObjectState == GameObject.eObjectState.Active)
                        .OrderBy(_ => Util.Random(1000)).FirstOrDefault();
                    if (who is SiegeCampNpc sc && who.GetPlayersInRadius(1500).Any())
                        NpcSpeech.Say(who, sc.Def.Idle, 1500);
                }
            }
            if (now >= _nextTell && Def.Campaign == null)
            {
                _nextTell = now + 5000;
                Broadcast();
            }
        }

        /// <summary>When a raid is due (and someone is in the zone to answer it), it's a disturbance at the camp: answered,
        /// it's fought; ignored too long (its auto_fail_s), it's lost.</summary>
        void TickRaids(long now)
        {
            if (State.RaidRunning != null)
            {
                if (RaidChains.TryGetValue(State.RaidRunning, out ChainRuntime run) && (run.Active || run.Dormant))
                    return;
                State.RaidRunning = null;                // (gone without an ending: a GM stopped it)
            }
            if (DateTime.UtcNow < State.NextRaidUtc || !PlayersInZone().Any())
                return;
            string id = State.NextRaid(Def);
            if (id == null || !RaidChains.TryGetValue(id, out ChainRuntime c) || c.Active)
                return;
            c.Toughness = State.RaidToughness;
            c.Dormant = true;
            c.DormantSince = now;
            State.RaidRunning = id;
            Cry(id == Def.LastRaid ? $"{c.Def.Hint}" : Def.RaidText ?? c.Def.Hint);
            ZoneSiege.Save();
        }

        // ------------------------------------------------------------------ the zone panel

        public string Line()
        {
            switch (State.Phase)
            {
                case SiegePhase.Building:
                    return $"{Def.ResolveName} {State.Resolve:0}%" + (State.Enemy >= 1 ? $"  -  {Def.EnemyName} {State.Enemy:0}%" : "");
                case SiegePhase.Open:
                    double m = BotsGoInM;
                    return m > 0 ? $"The assault is open - the bots go alone in {Math.Ceiling(m)}m" : $"The assault is open - the bots go as soon as they're {Math.Max(1, Assault?.Def.MinPeople ?? 1)}";
                case SiegePhase.Assault:
                    return "The assault is under way";
                default:
                    if (State.RaidRunning != null)
                        return "Under attack!";
                    TimeSpan left = State.NextRaidUtc - DateTime.UtcNow;
                    return left.TotalMinutes < 1 ? "Raiders are coming" : $"Held  -  raiders expected in {(left.TotalHours >= 1 ? $"{(int) left.TotalHours}h {left.Minutes:00}m" : $"{left.Minutes}m")}";
            }
        }

        void Broadcast()
        {
            string json = JsonConvert.SerializeObject(new
            {
                name = Def.Name, state = State.Phase.ToString().ToLowerInvariant(), resolve = Math.Round(State.Resolve, 1),
                enemy = Math.Round(State.Enemy, 1), line = Line(), raids = State.RaidIndex
            });
            foreach (GamePlayer p in PlayersInZone())
                NewClient.Send(p, "#SIEGE|" + json);
        }
    }

    /// <summary>The zones' sieges: loaded with the dynamic events, ticked with them, their state kept on disk.</summary>
    public static class ZoneSiege
    {
        public static readonly List<SiegeRuntime> All = new();
        static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);
        static bool _hooked;
        static long _nextSave;

        static string StatePath => Path.Combine(GameServer.Instance.Configuration.RootDirectory, "zone-sieges-state.json");

        public static void Load(IEnumerable<ZoneEventsDef> zones)
        {
            All.Clear();
            foreach (ZoneEventsDef z in zones)
            {
                if (z.Siege == null)
                    continue;
                z.Siege.ZoneDef = z;
                var s = new SiegeRuntime(z.Siege)
                {
                    Region = WorldMgr.GetRegion(z.Region),
                    Zone = WorldMgr.GetZone((ushort) z.Zone)
                };
                if (s.Region == null || s.Zone == null)
                    continue;
                ChainRuntime Find(string id) => DynamicEventManager.Chains.FirstOrDefault(c => c.Def.Id == id);
                s.Assault = Find(z.Siege.Assault);
                foreach (string id in z.Siege.Raids.Append(z.Siege.LastRaid).Where(x => x != null).Distinct())
                    if (Find(id) is ChainRuntime rc)
                        s.RaidChains[id] = rc;
                s.War = z.Siege.WarChain != null ? Find(z.Siege.WarChain) : null;
                int ti = Array.IndexOf(new[] { "grey", "green", "blue", "yellow", "orange", "red", "purple" }, (z.Siege.HostileTier ?? "").ToLowerInvariant());
                foreach (ChainRuntime c in s.RaidChains.Values.Append(s.Assault).Where(c => c != null))
                    if (ti >= 0)
                        c.Def.HostileTier = (sbyte) (ti - 3);
                if (s.Assault != null)
                {
                    SiegeRuntime me = s;
                    s.Assault.Available = () => me.State.Phase is SiegePhase.Open or SiegePhase.Assault;
                    s.Assault.Gate = me.Gate;
                }
                All.Add(s);
            }
            LoadState();
            if (!_hooked)
            {
                _hooked = true;
                DynamicEventManager.ChainEnded += (c, o) => { foreach (SiegeRuntime s in All) s.OnChainEnded(c, o, Environment.TickCount64); };
                DynamicEventManager.StageEnded += (c, st, won) => { foreach (SiegeRuntime s in All) s.OnStageEnded(c, st, won); };
                DynamicEventManager.StageBeginning += (c, st) =>
                {
                    foreach (SiegeRuntime s in All)
                        if (c == s.Assault && st.Id == c.Def.Start)
                            s.Ferry(c);
                };
                StoryQuestManager.Finished += (p, q, ending) => { foreach (SiegeRuntime s in All) s.OnQuestFinished(p, q?.QuestId); };
                DynamicEventManager.BotWaypoint = (c, bot) =>
                {
                    foreach (SiegeRuntime s in All)
                        if (s.IsSiegeChain(c))
                            return s.BotWaypoint(c, bot);
                    return null;
                };
            }
            if (All.Count > 0)
                log.Info($"Zone sieges: {string.Join(", ", All.Select(s => $"{s.Def.Name} ({s.State.Phase}, resolve {s.State.Resolve:0})"))}");
        }

        public static void Tick(long now)
        {
            foreach (SiegeRuntime s in All)
                s.Tick(now);
            if (now >= _nextSave)
            {
                _nextSave = now + 60_000;
                Save();
            }
        }

        public static SiegeRuntime In(Zone zone) => All.FirstOrDefault(s => s.Zone == zone);

        public static SiegeRuntime ById(string id) => All.FirstOrDefault(s => s.Def.Id == id);

        /// <summary>A siege was taken, its raid held, it fell, or its assault was thrown back ("taken", "held", "fell",
        /// "repelled"): a campaign that owns it hears.</summary>
        public static event Action<SiegeRuntime, string> Changed;

        internal static void Tell(SiegeRuntime s, string what)
        {
            if (s.Resetting)
                return;
            try { Changed?.Invoke(s, what); }
            catch (Exception ex) { log.Warn("Zone sieges: a listener threw", ex); }
        }

        public static void Save()
        {
            try
            {
                if (All.Count == 0)
                    return;
                var state = All.ToDictionary(s => s.Def.Id, s => s.State);
                File.WriteAllText(StatePath, JsonConvert.SerializeObject(state, Formatting.Indented));
            }
            catch (Exception ex)
            {
                log.Warn("Zone sieges: can't save", ex);
            }
        }

        static void LoadState()
        {
            try
            {
                if (!File.Exists(StatePath))
                    return;
                var state = JsonConvert.DeserializeObject<Dictionary<string, SiegeState>>(File.ReadAllText(StatePath)) ?? new();
                foreach (SiegeRuntime s in All)
                    if (state.TryGetValue(s.Def.Id, out SiegeState st) && st != null)
                    {
                        s.State = st;
                        if (st.Phase == SiegePhase.Assault)
                            st.Phase = SiegePhase.Open;   // (an assault cut off by a restart: gather again)
                        if (st.Phase == SiegePhase.Open && st.OpenedUtc == default)
                            st.OpenedUtc = DateTime.UtcNow;
                        st.RaidRunning = null;            // (a raid cut off: it comes again, its time is past)
                    }
            }
            catch (Exception ex)
            {
                log.Warn("Zone sieges: can't read the state", ex);
            }
        }
    }

    // ------------------------------------------------------------------ the camp's people

    /// <summary>One of the camp's people: says their piece when clicked.</summary>
    public class SiegeCampNpc : GameNPC
    {
        public SiegeRuntime Siege;
        public SiegeNpcDef Def;

        public override bool Interact(GamePlayer player)
        {
            if (!base.Interact(player))
                return false;
            string g = Greeting();
            if (!string.IsNullOrEmpty(g))
            {
                if (g.Contains('['))
                    SayTo(player, g);                // (a keyword to answer: the NPC window)
                else
                    NpcSpeech.SayTo(this, player, g);
            }
            return true;
        }

        protected virtual string Greeting() => Def?.Greet;
    }

    /// <summary>The roane who carry you between the shore and the camp while it is held.</summary>
    public class SiegeFerry : SiegeCampNpc
    {
        protected override string Greeting()
        {
            string g = Def?.Greet ?? "Want to go across?";
            return g.Contains("[cross]") ? g : g + " Just say [cross].";
        }

        public override bool WhisperReceive(GameLiving source, string text)
        {
            if (source is not GamePlayer p || !base.WhisperReceive(source, text))
                return false;
            if (!string.Equals(text?.Trim(), "cross", StringComparison.OrdinalIgnoreCase) || Def.To == null || Siege?.Assault == null)
                return true;
            Vector3 at = Siege.Assault.Around(Siege.World(Def.To), 150);
            p.Out.SendMessage("The roane carry you across the water.", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            p.MoveTo(CurrentRegionID, (int) at.X, (int) at.Y, (int) at.Z, p.Heading);
            return true;
        }
    }

    /// <summary>A camp vendor for Marks of Valor: each item at your level, a little cheaper the better the camp's faction
    /// knows you (Familiar 5%, Honoured 10% off - owner: the island's vendors belong to the Mag Mell Guard).</summary>
    public class SiegeMarksMerchant : EventTokenMerchant
    {
        public SiegeRuntime Siege;
        public SiegeNpcDef Def;
        readonly ConcurrentDictionary<GamePlayer, MerchantTradeItems> _lists = new();
        static readonly ConcurrentDictionary<string, DbItemTemplate> _priced = new();

        protected override void SendInteractMessage(GamePlayer player)
        {
            NpcSpeech.SayTo(this, player, Def?.Greet ?? "Marks of Valor buy what coin can't. Have a look.");
            double f = Discount(player);
            player.Out.SendMessage($"{Name} sells for Marks of Valor - you earn them in events." +
                (f < 1 ? $" Your standing with {Faction()?.Name ?? "them"} takes {Math.Round((1 - f) * 100)}% off." : ""),
                eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        RepFactionDef Faction() => string.IsNullOrEmpty(Siege?.Def.Faction) ? null : RepDefs.Faction(Siege.Def.Faction);

        public double Discount(GamePlayer p)
        {
            RepFactionDef f = Faction();
            if (f == null || p == null)
                return 1;
            Rank r = ReputationService.RankWith(p, f);
            return r >= Rank.Honoured ? 0.90 : r >= Rank.Familiar ? 0.95 : 1.0;
        }

        public MerchantTradeItems ListFor(GamePlayer player)
        {
            var list = new MerchantTradeItems(null);
            double f = Discount(player);
            int slot = 0;
            foreach (SiegeStockDef s in Def?.Stock ?? new List<SiegeStockDef>())
            {
                DbItemTemplate t = StageRuntime.ItemAtLevel(s.Item, player.Level);
                if (t == null)
                    continue;
                int price = Math.Max(1, (int) Math.Ceiling((s.Price > 0 ? s.Price : t.Price) * f));
                DbItemTemplate priced = _priced.GetOrAdd($"{t.Id_nb}/{price}", _ =>
                {
                    var copy = (DbItemTemplate) t.Clone();
                    copy.Price = price;
                    return copy;
                });
                list.AddTradeItem(slot / MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS,
                    (eMerchantWindowSlot) (slot % MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS), priced);
                slot++;
            }
            return list;
        }

        public override void SendMerchantWindow(GamePlayer player)
        {
            MerchantTradeItems list = ListFor(player);
            _lists[player] = list;
            TradeItems = list;
            player.Out.SendMerchantWindow(list, eMerchantWindowType.Count);
        }

        public override void OnPlayerBuy(GamePlayer player, int item_slot, int number)
        {
            if (!_lists.TryGetValue(player, out MerchantTradeItems list))
                list = ListFor(player);
            TradeItems = list;
            base.OnPlayerBuy(player, item_slot, number);
        }
    }

    /// <summary>A camp vendor for coin (the alchemist): the items at their own prices.</summary>
    public class SiegeCoinMerchant : GameMerchant
    {
        public SiegeRuntime Siege;
        public SiegeNpcDef Def;

        public void Stock()
        {
            var list = new MerchantTradeItems(null);
            int slot = 0;
            foreach (SiegeStockDef s in Def?.Stock ?? new List<SiegeStockDef>())
                if (GameServer.Database.FindObjectByKey<DbItemTemplate>(s.Item) is DbItemTemplate t)
                {
                    list.AddTradeItem(slot / MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS,
                        (eMerchantWindowSlot) (slot % MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS), t);
                    slot++;
                }
            TradeItems = list;
        }

        public override bool Interact(GamePlayer player)
        {
            if (!base.Interact(player))
                return false;
            if (!string.IsNullOrEmpty(Def?.Greet))
                NpcSpeech.SayTo(this, player, Def.Greet);
            return true;
        }
    }

    // ------------------------------------------------------------------ the GM's levers

    [Cmd("&siege", ePrivLevel.Player,
        "This zone's siege",
        "/siege - how it stands",
        "GM: /siege resolve <n> | enemy <n> | open | impatient | start | capture | raid | fall | reset | goto <staging|landing|camp>")]
    public class SiegeCommandHandler : Commands.AbstractCommandHandler, Commands.ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            SiegeRuntime s = ZoneSiege.In(p.CurrentZone);
            if (s == null)
            {
                DisplayMessage(client, "No siege in this zone.");
                return;
            }
            string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            bool gm = client.Account.PrivLevel > (uint) ePrivLevel.Player;
            long now = Environment.TickCount64;
            if (gm)
                switch (sub)
                {
                    case "resolve" when args.Length > 2 && double.TryParse(args[2], out double r):
                        if (s.State.Phase == SiegePhase.Building)
                        {
                            s.State.Resolve = 0;
                            s.Feed(Math.Clamp(r, 0, 100), "GM");
                            if (s.State.Phase == SiegePhase.Building)
                                s.State.Resolve = Math.Clamp(r, 0, 100);
                        }
                        break;
                    case "enemy" when args.Length > 2 && double.TryParse(args[2], out double en):
                        s.State.Enemy = Math.Clamp(en, 0, 100);
                        break;
                    case "open":
                        if (s.State.Phase == SiegePhase.Building)
                            s.Feed(100, "GM");
                        break;
                    case "capture":
                        if (s.Assault?.Active == true)
                            s.Assault.End("fail", now);
                        s.Capture(now);
                        break;
                    case "raid":
                        if (s.State.Phase == SiegePhase.Held)
                            s.State.NextRaidUtc = DateTime.UtcNow;
                        break;
                    case "fall":
                        if (s.State.Phase == SiegePhase.Held)
                            s.Fall();
                        break;
                    case "start":
                        // testing: the assault sets out now, however few are at the giver
                        if (s.State.Phase is SiegePhase.Open && s.Assault is ChainRuntime a && !a.Active)
                            a.Begin(a.Def.Start, now);
                        break;
                    case "impatient":
                        // testing: the bots have waited as long as they will
                        s.State.OpenedUtc = DateTime.UtcNow.AddMinutes(-s.Def.BotsGoAfterM - 1);
                        break;
                    case "goto" when args.Length > 2:
                    {
                        double[] to = args[2] switch
                        {
                            "staging" => s.Def.Staging,
                            "landing" => s.Def.Landing,
                            _ => s.Def.CampNpcs.FirstOrDefault()?.Pos
                        };
                        if (to != null)
                        {
                            Vector3 at = s.World(to);
                            p.MoveTo(s.Region.ID, (int) at.X, (int) at.Y, (int) at.Z + 20, p.Heading);
                        }
                        break;
                    }
                    case "reset":
                        if (s.State.Phase == SiegePhase.Held)
                            s.Fall();
                        s.State = new SiegeState();
                        break;
                }
            ZoneSiege.Save();
            DisplayMessage(client, $"{s.Def.Name}: {s.State.Phase} - {s.Line()} (resolve {s.State.Resolve:0}, {s.Def.EnemyName} {s.State.Enemy:0}, raids held {s.State.RaidIndex})");
            if (gm && s.Assault != null)
            {
                var bots = DynamicEventManager.BotsWith(s.Assault);
                int atGiver = s.Assault.Leader is EventNpc g ? bots.Count(b => b.IsWithinRadius(g, 2000)) : 0;
                string far = s.Assault.Leader is EventNpc g2 && bots.Count > 0 ? $", the rest about {bots.Where(b => !b.IsWithinRadius(g2, 2000)).Select(b => b.GetDistanceTo(g2) / 40).DefaultIfEmpty(0).Average():0} m away" : "";
                DisplayMessage(client, $"Bots with the assault: {bots.Count} ({atGiver} at the giver, {s.WarBand(now).Count} in the war band, {bots.Count(s.OnIsland)} on the island{far})" +
                    string.Concat(s.RaidChains.Values.Select(c => $"; with {c.Def.Title}: {DynamicEventManager.BotsWith(c).Count}")));
            }
        }
    }
}
