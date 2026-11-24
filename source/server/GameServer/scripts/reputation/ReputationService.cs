using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using DOL.Database;
using DOL.Database.Attributes;
using DOL.GS.PacketHandler;
using DOL.GS.PlayerTitles;
using Newtonsoft.Json;

namespace DOL.GS.Reputation
{
    /// <summary>A player's or a bot's standing with every faction, and their realm deeds (one row each).</summary>
    [DataTable(TableName = "offline_reputation")]
    public class DbReputation : DataObject
    {
        string _owner;
        string _json;
        string _updated;

        public DbReputation()
        {
            AllowAdd = true;
            AllowDelete = true;
        }

        /// <summary>"c:&lt;character id&gt;" or "b:&lt;bot id&gt;".</summary>
        [PrimaryKey]
        public string OwnerKey { get => _owner; set { Dirty = true; _owner = value; } }

        [DataElement(AllowDbNull = true)]
        public string Json { get => _json; set { Dirty = true; _json = value; } }

        [DataElement(AllowDbNull = true)]
        public string UpdatedUtc { get => _updated; set { Dirty = true; _updated = value; } }
    }

    /// <summary>
    /// Reputation (owner 2026-11-22). Every zone has two factions (scripts/reputation, RepDefs) - for Lough Derg the Mag
    /// Mell Guard and the Lucht Feasa of Loch Dearg - with five ranks, Unknown, Familiar, Trusted, Honoured and Legend,
    /// and a title at Trusted, Honoured and Legend. Standing comes from story quests (the most: a side's stories reach
    /// about Trusted), events and bounties (repeatable: the road to Legend), and a little from yellow-and-up kills ("Not
    /// enough to make it worth it to grind vs doing events and the quests, but some so every player doesn't have to
    /// always do every quest"). All of it goes with the server's experience rate and the zone's rating ("tied to the
    /// overall XP rate of the server and the zone, so if players want a quicker experience it's tied to the EXP rate").
    ///
    /// Realm reputation ("an overall faction reputation that builds with more reputation you gain throughout all zones
    /// and RvR ... would take a lot of combined reputation to get legendary on"): every faction's standing counts up to
    /// its Legend mark - grinding one zone stops paying - plus RvR deeds (towers and keeps taken, realm points).
    ///
    /// Bots keep the same standings ("let the bots be able to track their reputation as well, and ones who earn a title
    /// will use that title"), arrive with some already, earn as they play, and react to people of high standing.
    /// </summary>
    public static partial class ReputationService
    {
        public static readonly double[] Thresholds = { 0, 500, 1500, 4000, 10000 };
        public static readonly double[] RealmThresholds = { 0, 5000, 15000, 40000, 120000 };

        // what each deed is worth before the rates (the server's experience rate x the zone's rating)
        public const double QuestPoints = 250, GroupQuestPoints = 450;
        public const double EventGold = 40, EventSilver = 28, EventBronze = 16;      // per stage
        public const double BountySolo = 60, BountySmall = 120, BountyLarge = 250;
        public const double KillYellow = 3, KillOrange = 6, KillRed = 15, KillPurple = 40;
        public const double TowerTaken = 80, KeepTaken = 200, RealmPointsPer = 10;  // realm: a point per 10 realm points
        public const double BotTricklePoints = 15;                                   // a working bot, every 5 minutes

        public static Rank RankOf(double points) => (Rank) Step(points, Thresholds);
        public static Rank RealmRankOf(double points) => (Rank) Step(points, RealmThresholds);

        static int Step(double points, double[] marks)
        {
            int r = 0;
            for (int i = 1; i < marks.Length; i++)
                if (points >= marks[i])
                    r = i;
            return r;
        }

        // ------------------------------------------------------------------ the standings

        public sealed class Standing
        {
            public ConcurrentDictionary<string, double> Points = new();
            public double Rvr;
            public string Lock;                                // a title chosen to wear always (null: by where you are)
            public bool Seeded;                                // a bot's starting standing has been given
            [JsonIgnore] public bool Dirty;
            [JsonIgnore] public DbReputation Row;
            [JsonIgnore] public readonly object Sync = new();

            public double Get(string key) => key != null && Points.TryGetValue(key, out double v) ? v : 0;
        }

        static readonly ConcurrentDictionary<string, Standing> _store = new();
        static volatile bool _loaded;

        public static string KeyOf(GameLiving who) => who switch
        {
            GamePlayer p when !string.IsNullOrEmpty(p.ObjectId) => "c:" + p.ObjectId,
            GameBot b when b.DatabaseID > 0 => "b:" + b.DatabaseID,
            _ => null
        };

        /// <summary>Everyone's standings, read once (a few thousand small rows at most).</summary>
        public static void LoadAll()
        {
            if (_loaded)
                return;
            try
            {
                foreach (DbReputation row in GameServer.Database.SelectAllObjects<DbReputation>())
                {
                    if (string.IsNullOrEmpty(row.OwnerKey))
                        continue;
                    Standing s = Parse(row.Json);
                    s.Row = row;
                    _store[row.OwnerKey] = s;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("[Reputation] load: " + e.Message);
            }
            _loaded = true;
        }

        static Standing Parse(string json)
        {
            try
            {
                return string.IsNullOrEmpty(json) ? new Standing() : JsonConvert.DeserializeObject<Standing>(json) ?? new Standing();
            }
            catch
            {
                return new Standing();
            }
        }

        /// <summary>Their standing (made when first asked for; a bot's comes with its starting standing).</summary>
        public static Standing Of(GameLiving who)
        {
            string key = KeyOf(who);
            if (key == null)
                return null;
            if (!_loaded)
                LoadAll();
            Standing s = _store.GetOrAdd(key, _ => new Standing());
            if (who is GameBot bot && !s.Seeded)
                Seed(bot, s);
            return s;
        }

        /// <summary>Tests: a standing for a key, no database.</summary>
        public static Standing ForKey(string key) => _store.GetOrAdd(key, _ => new Standing());

        public static void Forget(string key) => _store.TryRemove(key, out _);

        /// <summary>Write the changed standings (all, or up to <paramref name="max"/>).</summary>
        public static int SaveDirty(int max = int.MaxValue)
        {
            int n = 0;
            foreach (var (key, s) in _store)
            {
                if (n >= max)
                    break;
                if (!s.Dirty)
                    continue;
                if (Save(key, s))
                    n++;
            }
            return n;
        }

        public static bool Save(GameLiving who) => KeyOf(who) is string key && _store.TryGetValue(key, out Standing s) && s.Dirty && Save(key, s);

        static bool Save(string key, Standing s)
        {
            try
            {
                string json;
                lock (s.Sync)
                {
                    json = JsonConvert.SerializeObject(s);
                    s.Dirty = false;
                }
                if (s.Row == null)
                {
                    s.Row = new DbReputation { OwnerKey = key, Json = json, UpdatedUtc = DateTime.UtcNow.ToString("o") };
                    GameServer.Database.AddObject(s.Row);
                }
                else
                {
                    s.Row.Json = json;
                    s.Row.UpdatedUtc = DateTime.UtcNow.ToString("o");
                    GameServer.Database.SaveObject(s.Row);
                }
                return true;
            }
            catch (Exception e)
            {
                Console.WriteLine($"[Reputation] save {key}: {e.Message}");
                s.Dirty = true;
                return false;
            }
        }

        // ------------------------------------------------------------------ reading them

        public static double Points(GameLiving who, RepFactionDef f) => f == null ? 0 : Of(who)?.Get(f.Key) ?? 0;
        public static Rank RankWith(GameLiving who, RepFactionDef f) => RankOf(Points(who, f));

        /// <summary>Realm reputation: each faction's standing up to its Legend mark (so it takes many zones), and the
        /// realm deeds.</summary>
        public static double RealmPoints(GameLiving who)
        {
            Standing s = Of(who);
            if (s == null)
                return 0;
            lock (s.Sync)
                return RealmPoints(s, who.Realm);
        }

        public static double RealmPoints(Standing s, eRealm realm)
        {
            double sum = s.Rvr;
            foreach (RepFactionDef f in RepDefs.AllFactions)
                if (f.ZoneDef.Realm == (int) realm)
                    sum += Math.Min(s.Get(f.Key), Thresholds[(int) Rank.Legend]);
            return sum;
        }

        public static Rank RealmRank(GameLiving who) => RealmRankOf(RealmPoints(who));

        static bool Female(GameLiving who) => who?.Gender == eGender.Female;

        /// <summary>The titles they have earned, best first: their zones' factions' (Trusted and up) and their realm's.</summary>
        public static List<(string Title, string Faction, Rank Rank)> TitlesEarned(GameLiving who)
        {
            var list = new List<(string, string, Rank)>();
            Standing s = Of(who);
            if (s == null)
                return list;
            bool female = Female(who);
            foreach (RepFactionDef f in RepDefs.AllFactions)
            {
                if (f.ZoneDef.Realm != (int) who.Realm)
                    continue;
                Rank r = RankOf(s.Get(f.Key));
                for (Rank k = Rank.Trusted; k <= r; k++)
                    if (f.Title(k, female) is string t)
                        list.Add((t, f.Short, k));
            }
            Rank rr = RealmRankOf(RealmPoints(s, who.Realm));
            RepRealmDef realm = RepDefs.Realm(who.Realm);
            for (Rank k = Rank.Trusted; k <= rr && realm != null; k++)
            {
                int i = (int) k - (int) Rank.Trusted;
                if (i < realm.Titles.Count)
                    list.Add((realm.Titles[i], realm.Name, k));
            }
            return list.OrderByDescending(t => t.Item3).ThenBy(t => t.Item1).ToList();
        }

        /// <summary>The title they wear now (owner: "have that title auto apply when you're in that zone"): one they
        /// locked on, if they still have it; else in a zone with factions, their best title there; elsewhere (or with no
        /// title in this zone) their realm title. "" when they have none.</summary>
        public static string TitleFor(GameLiving who)
        {
            Standing s = Of(who);
            if (s == null)
                return "";
            bool female = Female(who);
            if (!string.IsNullOrEmpty(s.Lock) && TitlesEarned(who).Any(t => t.Title == s.Lock))
                return s.Lock;
            RepZoneDef z = RepDefs.ForZone(who.CurrentZone);
            if (z != null && z.Realm == (int) who.Realm)
            {
                RepFactionDef best = null;
                double bestPts = -1;
                foreach (RepFactionDef f in z.Factions)
                {
                    double p = s.Get(f.Key);
                    if (RankOf(p) >= Rank.Trusted && p > bestPts)
                    {
                        best = f;
                        bestPts = p;
                    }
                }
                if (best != null)
                    return best.Title(RankOf(bestPts), female) ?? "";
            }
            Rank rr = RealmRankOf(RealmPoints(s, who.Realm));
            RepRealmDef realm = RepDefs.Realm(who.Realm);
            int i = (int) rr - (int) Rank.Trusted;
            return realm != null && i >= 0 && i < realm.Titles.Count ? realm.Titles[i] : "";
        }

        // ------------------------------------------------------------------ gaining it

        /// <summary>The rate a deed is multiplied by: the server's experience rate (bots: theirs) x the zone's rating.</summary>
        public static double Rate(GameLiving who, Zone zone)
        {
            double server = who is GameBot ? ServerProperties.Properties.BOT_XP_RATE : ServerProperties.Properties.XP_RATE;
            if (server <= 0)
                server = 1.0;
            return server * (zone == null ? 1.0 : ZoneRates.Factor(ZoneRates.RatingOf(zone)));
        }

        /// <summary>Add to a faction's standing (the base amount, multiplied by the rates here). Returns what was added.</summary>
        public static double Gain(GameLiving who, RepFactionDef f, double basePoints, string why = null, bool quiet = false, bool rated = true)
        {
            if (who == null || f == null || basePoints <= 0 || (int) who.Realm != f.ZoneDef.Realm)
                return 0;
            Standing s = Of(who);
            if (s == null)
                return 0;
            double add = rated ? basePoints * Rate(who, WorldMgr.GetZone((ushort) f.ZoneDef.Zone)) : basePoints;
            Rank before, after, realmBefore, realmAfter;
            double now;
            lock (s.Sync)
            {
                if (rated)
                    add *= KinFactor(s.Get, f);
                double was = s.Get(f.Key);
                realmBefore = RealmRankOf(RealmPoints(s, who.Realm));
                now = was + add;
                s.Points[f.Key] = now;
                s.Dirty = true;
                before = RankOf(was);
                after = RankOf(now);
                realmAfter = RealmRankOf(RealmPoints(s, who.Realm));
            }
            if (who is GamePlayer p)
            {
                if (!quiet && add >= 1)
                    p.Out.SendMessage($"{f.Short} reputation +{add:0}{(string.IsNullOrEmpty(why) ? "" : " (" + why + ")")}.",
                        eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                PushSoon(p);
            }
            if (after > before)
                RankedUp(who, f, after);
            if (realmAfter > realmBefore)
                RealmRankedUp(who, realmAfter);
            return add;
        }

        /// <summary>Kin factions (owner 2026-11-22: the realm's soldiers in different zones, the keepers of the old lore):
        /// Honoured with one of a faction's kin earns it 50% faster, Legend twice as fast - the best kin counts.</summary>
        public static double KinFactor(Func<string, double> points, RepFactionDef f)
        {
            double best = 1.0;
            foreach (string k in f?.Kin ?? new List<string>())
            {
                Rank r = RankOf(points(k));
                best = Math.Max(best, r >= Rank.Legend ? KinLegend : r >= Rank.Honoured ? KinHonoured : 1.0);
            }
            return best;
        }

        public const double KinHonoured = 1.5, KinLegend = 2.0;

        /// <summary>Realm deeds (RvR): realm reputation only.</summary>
        public static double GainRealm(GameLiving who, double basePoints, string why = null, bool rated = true)
        {
            if (who == null || basePoints <= 0)
                return 0;
            Standing s = Of(who);
            if (s == null)
                return 0;
            double server = who is GameBot ? ServerProperties.Properties.BOT_XP_RATE : ServerProperties.Properties.XP_RATE;
            double add = rated ? basePoints * (server > 0 ? server : 1.0) : basePoints;
            Rank before, after;
            lock (s.Sync)
            {
                before = RealmRankOf(RealmPoints(s, who.Realm));
                s.Rvr += add;
                s.Dirty = true;
                after = RealmRankOf(RealmPoints(s, who.Realm));
            }
            if (who is GamePlayer p)
            {
                if (!string.IsNullOrEmpty(why) && add >= 1)
                    p.Out.SendMessage($"Realm reputation +{add:0} ({why}).", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                PushSoon(p);
            }
            if (after > before)
                RealmRankedUp(who, after);
            return add;
        }

        // ------------------------------------------------------------------ what counts toward what

        /// <summary>The faction a monster of this name is the foe of, in this zone (the zone's default when none).</summary>
        public static RepFactionDef KillFaction(RepZoneDef z, string name)
        {
            if (z == null)
                return null;
            string n = (name ?? "").ToLowerInvariant();
            foreach (RepFactionDef f in z.Factions)
                if (f.Kills.Any(w => n.Contains(w.ToLowerInvariant())))
                    return f;
            return z.Faction(z.KillDefault) ?? z.Factions.FirstOrDefault();
        }

        public static double KillPoints(sbyte tier) => tier switch
        {
            MonsterTiers.Yellow => KillYellow,
            MonsterTiers.Orange => KillOrange,
            MonsterTiers.Red => KillRed,
            MonsterTiers.Purple => KillPurple,
            _ => 0
        };

        /// <summary>A story quest's faction: by its ending where that picks a side, else the quest's.</summary>
        public static (RepZoneDef Zone, RepFactionDef Faction) QuestFaction(string questId, string ending)
        {
            foreach (RepZoneDef z in RepDefs.Zones)
            {
                if (ending != null && z.Quests.TryGetValue(questId + ":" + ending, out string byEnding))
                    return (z, z.Faction(byEnding));
                if (z.Quests.TryGetValue(questId, out string key))
                    return (z, z.Faction(key));
            }
            return (null, null);
        }

        public static RepFactionDef EventFaction(RepZoneDef z, string chainId)
        {
            if (z == null)
                return null;
            if (chainId != null && z.Events.TryGetValue(chainId, out string key))
                return z.Faction(key);
            return z.Faction(z.EventDefault) ?? z.Factions.FirstOrDefault();
        }

        /// <summary>A merchant's price for you in a zone with factions: 5% off at Familiar with either, 10% at Honoured.</summary>
        public static double PriceFactor(GamePlayer p, GameNPC merchant)
        {
            RepZoneDef z = RepDefs.ForZone(merchant?.CurrentZone);
            if (p == null || z == null || z.Realm != (int) p.Realm)
                return 1.0;
            Rank best = z.Factions.Select(f => RankWith(p, f)).DefaultIfEmpty(Rank.Unknown).Max();
            return best >= Rank.Honoured ? 0.90 : best >= Rank.Familiar ? 0.95 : 1.0;
        }

        public static string Num(double v) => v.ToString("0", CultureInfo.InvariantCulture);
    }
}
