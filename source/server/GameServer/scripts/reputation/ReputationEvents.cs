using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using DOL.Events;
using DOL.GS.DynamicEvents;
using DOL.GS.Keeps;
using DOL.GS.PacketHandler;
using DOL.GS.PlayerTitles;
using DOL.GS.ServerRules;
using DOL.GS.StoryQuests;
using Newtonsoft.Json;

namespace DOL.GS.Reputation
{
    /// <summary>Reputation's hooks into the world: what earns it, the ranks reached, the titles worn, the zone panel and
    /// the window, the bots' standing and their talk, the crier.</summary>
    public static partial class ReputationService
    {
        // ------------------------------------------------------------------ deeds

        /// <summary>AbstractServerRules: a monster killed. Yellow and up pay a little (the share of the work as for
        /// experience: a twentieth of its health is the whole kill).</summary>
        public static void OnKill(GameLiving awardee, GameNPC killed, double damagePercent)
        {
            try
            {
                if (awardee == null || killed == null || killed is GameBot)
                    return;
                double basePts = KillPoints(MonsterTiers.Tier(killed));
                RepZoneDef z = RepDefs.ForZone(killed.CurrentZone);
                if (basePts <= 0 || z == null)
                    return;
                GameLiving who = MonsterTiers.Combatant(awardee) ?? awardee;
                double share = damagePercent >= AbstractServerRules.OPEN_TAP_SHARE ? 1.0 : Math.Max(0, damagePercent) / AbstractServerRules.OPEN_TAP_SHARE;
                Gain(who, KillFaction(z, killed.Name), basePts * share, null, quiet: true);
            }
            catch (Exception e)
            {
                Console.WriteLine("[Reputation] kill: " + e.Message);
            }
        }

        /// <summary>A story quest finished (StoryQuestManager.Finished).</summary>
        public static void OnQuestFinished(GamePlayer p, StoryQuest s, string ending)
        {
            if (p == null || s?.Def == null)
                return;
            var (_, f) = QuestFaction(s.Def.Id, ending);
            if (f != null)
                Gain(p, f, s.Def.Group ? GroupQuestPoints : QuestPoints, s.Def.Title);
        }

        /// <summary>DynamicEventRuntime.GiveRewards: an event's stage paid out (tier 3 gold, 2 silver, 1 bronze).</summary>
        public static void OnEventStage(GameLiving who, ChainRuntime chain, int tier)
        {
            if (who == null || chain == null || chain.Private)
                return;
            RepZoneDef z = RepDefs.ForZone(chain.Zone);
            RepFactionDef f = EventFaction(z, chain.Def?.Id);
            if (f == null)
                return;
            Gain(who, f, tier >= 3 ? EventGold : tier == 2 ? EventSilver : EventBronze, chain.Def?.Title, quiet: who is not GamePlayer);
        }

        /// <summary>BountyQuest.Claim: a zone bounty paid (an event bounty counts for the event's faction).</summary>
        public static void OnBounty(GamePlayer p, ushort zoneId, string eventId, BountyDifficulty size)
        {
            RepFactionDef f = BountyFaction(zoneId, eventId);
            if (f != null)
                Gain(p, f, size == BountyDifficulty.VeryHard ? BountyLarge : size == BountyDifficulty.Hard ? BountySmall : BountySolo, "bounty");
        }

        public static RepFactionDef BountyFaction(ushort zoneId, string eventId)
        {
            RepZoneDef z = RepDefs.ForZone(zoneId);
            if (z == null)
                return null;
            return eventId != null ? EventFaction(z, eventId) : z.Faction(z.QuestDefault) ?? z.Factions.FirstOrDefault();
        }

        /// <summary>Honoured with the bounty's faction: its hunts pay an extra item and half again the Marks.</summary>
        public static bool BountyHonoured(GamePlayer p, ushort zoneId, string eventId) =>
            BountyFaction(zoneId, eventId) is RepFactionDef f && RankWith(p, f) >= Rank.Honoured;

        /// <summary>GameBot / players: realm points earned add to realm reputation (one for every ten).</summary>
        public static void OnRealmPoints(GameLiving who, long rp)
        {
            if (rp > 0)
                GainRealm(who, rp / RealmPointsPer);
        }

        static void OnKeepTaken(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                if (args is not KeepEventArgs { Keep: not null } taken)
                    return;
                AbstractGameKeep keep = taken.Keep;
                Region region = WorldMgr.GetRegion(keep.Region);
                if (region == null)
                    return;
                bool tower = keep is GameKeepTower;
                double pts = tower ? TowerTaken : KeepTaken;
                string what = tower ? "tower taken" : "keep taken";
                var at = new Point3D(keep.X, keep.Y, keep.Z);
                foreach (GamePlayer p in ClientService.Instance.GetPlayers())
                    if (p.CurrentRegion == region && p.Realm == keep.Realm && p.IsAlive && p.IsWithinRadius(at, 4000))
                        GainRealm(p, pts, what);
                foreach (GameNPC n in region.GetNPCsInRadius(at, 4000))
                    if (n is GameBot b && b.Realm == keep.Realm && b.IsAlive)
                        GainRealm(b, pts);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[Reputation] keep: " + ex.Message);
            }
        }

        // ------------------------------------------------------------------ ranks reached

        static void RankedUp(GameLiving who, RepFactionDef f, Rank r)
        {
            string title = f.Title(r, Female(who));
            if (who is GamePlayer p)
            {
                p.Out.SendMessage($"{f.Short}: {r.ToString().ToUpper()}", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                p.Out.SendMessage($"Your standing with {f.Name} is now {r}." + (title != null ? $" You may now be called {title}." : "") +
                    Unlocks(f, r), eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                NewClient.Send(p, $"#REPUP|{f.Short}|{r}|{title ?? ""}");
                if (title != null)
                    WearTitle(p);
                Save(p);
                Push(p);
            }
            if (r == Rank.Legend)
                Crier(who, f, title);
        }

        static string Unlocks(RepFactionDef f, Rank r) => r switch
        {
            Rank.Familiar => " Merchants in " + (f.ZoneDef.Name ?? "the zone") + " give you 5% off.",
            Rank.Trusted when f.Quartermaster != null => $" {f.Quartermaster.Name} will sell you their Trusted stock.",
            Rank.Honoured => " Merchants there give you 10% off" + (f.Key == (f.ZoneDef.QuestDefault ?? "") ? ", and the Bounty Master's hunts pay more." : ".") +
                (f.Quartermaster != null ? $" {f.Quartermaster.Name} has more for you." : ""),
            Rank.Legend when f.Quartermaster != null => $" {f.Quartermaster.Name} will sell you a Legend's own piece.",
            _ => ""
        };

        static void RealmRankedUp(GameLiving who, Rank r)
        {
            RepRealmDef realm = RepDefs.Realm(who.Realm);
            int i = (int) r - (int) Rank.Trusted;
            string title = realm != null && i >= 0 && i < realm.Titles.Count ? realm.Titles[i] : null;
            if (who is GamePlayer p)
            {
                p.Out.SendMessage($"{realm?.Name ?? "Realm"} reputation: {r.ToString().ToUpper()}", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                p.Out.SendMessage($"Your standing with {realm?.Name ?? "your realm"} is now {r}." + (title != null ? $" You may now be called {title}." : ""),
                    eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                NewClient.Send(p, $"#REPUP|{realm?.Name ?? "Realm"}|{r}|{title ?? ""}");
                if (title != null)
                    WearTitle(p);
                Save(p);
                Push(p);
            }
            if (r == Rank.Legend)
            {
                string line = $"{who.Name} is now a Legend of {realm?.Name ?? "the realm"}" + (title != null ? $": {title}!" : "!");
                foreach (GamePlayer other in ClientService.Instance.GetPlayers())
                    if (other.Realm == who.Realm)
                        other.Out.SendMessage(line, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
        }

        /// <summary>The crier: the faction's speaker calls it out, and the zone hears of it.</summary>
        static void Crier(GameLiving who, RepFactionDef f, string title)
        {
            try
            {
                GameNPC speaker = StoryQuestManager.Npc(f.Speaker);
                string said = $"Hear me, all! {who.Name} is named {title ?? "a Legend"} - a Legend of {f.Name}!";
                if (speaker != null)
                    NpcSpeech.Say(speaker, said);
                string line = $"[{f.Town ?? f.ZoneDef.Name}] {who.Name} is now a Legend of {f.Name}" + (title != null ? $": {title}!" : "!");
                foreach (GamePlayer p in ClientService.Instance.GetPlayers())
                    if (p.CurrentZone?.ID == f.ZoneDef.Zone)
                        p.Out.SendMessage(line, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
            catch (Exception e)
            {
                Console.WriteLine("[Reputation] crier: " + e.Message);
            }
        }

        // ------------------------------------------------------------------ titles worn

        public static ReputationPlayerTitle PlayerTitle =>
            PlayerTitleMgr.GetTitleByTypeName(typeof(ReputationPlayerTitle).FullName) as ReputationPlayerTitle;

        /// <summary>A title earned: given, and worn when they wear none (or already wear this one).</summary>
        public static void WearTitle(GamePlayer p)
        {
            ReputationPlayerTitle t = PlayerTitle;
            if (p == null || t == null)
                return;
            if (!p.Titles.Contains(t))
                p.AddTitle(t);
            if (p.CurrentTitle == null || p.CurrentTitle == PlayerTitleMgr.ClearTitle)
                p.CurrentTitle = t;
            else if (p.CurrentTitle == t)
                p.UpdateCurrentTitle();
            _wornTitle[p] = TitleFor(p);
        }

        static readonly ConcurrentDictionary<GamePlayer, string> _wornTitle = new();

        /// <summary>Their worn reputation title changes with the zone: tell them and those around.</summary>
        static void CheckWornTitle(GamePlayer p)
        {
            if (p.CurrentTitle is not ReputationPlayerTitle)
                return;
            string now = TitleFor(p);
            if (_wornTitle.TryGetValue(p, out string was) && was == now)
                return;
            _wornTitle[p] = now;
            p.UpdateCurrentTitle();
        }

        /// <summary>/rep title: lock on one of your titles (by its number in /rep), or "auto" to go by where you are.</summary>
        public static string LockTitle(GamePlayer p, string arg)
        {
            Standing s = Of(p);
            if (s == null)
                return "You have no reputation yet.";
            var titles = TitlesEarned(p);
            if (string.IsNullOrWhiteSpace(arg) || arg.Equals("auto", StringComparison.OrdinalIgnoreCase))
            {
                lock (s.Sync)
                {
                    s.Lock = null;
                    s.Dirty = true;
                }
                WearTitle(p);
                return "Your reputation title now follows where you are.";
            }
            string chosen = int.TryParse(arg, out int n) && n >= 1 && n <= titles.Count ? titles[n - 1].Title
                : titles.FirstOrDefault(t => t.Title.Equals(arg, StringComparison.OrdinalIgnoreCase)).Title;
            if (chosen == null)
                return "You haven't earned that title. /rep lists yours.";
            lock (s.Sync)
            {
                s.Lock = chosen;
                s.Dirty = true;
            }
            ReputationPlayerTitle t = PlayerTitle;
            if (t != null && !p.Titles.Contains(t))
                p.AddTitle(t);
            if (t != null && p.CurrentTitle != t)
                p.CurrentTitle = t;
            else
                p.UpdateCurrentTitle();
            _wornTitle[p] = chosen;
            Push(p);
            return $"You will be called {chosen} wherever you go (/rep title auto to undo).";
        }

        // ------------------------------------------------------------------ the zone panel and the window

        static readonly ConcurrentDictionary<GamePlayer, long> _pushDue = new();

        public static void PushSoon(GamePlayer p) => _pushDue.TryAdd(p, GameLoop.GameLoopTime + 500);

        static object Bar(string name, double pts, double[] marks, string title)
        {
            int r = Step(pts, marks);
            return new
            {
                name,
                rank = ((Rank) r).ToString(),
                points = Math.Floor(pts),
                lo = marks[r],
                hi = r + 1 < marks.Length ? marks[r + 1] : marks[r],
                title = title ?? ""
            };
        }

        /// <summary>"#REP|{zone, factions:[{name, rank, points, lo, hi, title}], realm:{...}, title}" for the Zone panel.</summary>
        public static void Push(GamePlayer p)
        {
            if (p == null || !NewClient.Is(p))
                return;
            _pushDue.TryRemove(p, out _);
            Standing s = Of(p);
            if (s == null)
                return;
            RepZoneDef z = RepDefs.ForZone(p.CurrentZone);
            bool female = Female(p);
            var factions = new List<object>();
            if (z != null && z.Realm == (int) p.Realm)
                foreach (RepFactionDef f in z.Factions)
                {
                    double pts = s.Get(f.Key);
                    factions.Add(Bar(f.Short, pts, Thresholds, f.Title(RankOf(pts), female)));
                }
            RepRealmDef realm = RepDefs.Realm(p.Realm);
            double rp = RealmPoints(p);
            Rank rr = RealmRankOf(rp);
            int ti = (int) rr - (int) Rank.Trusted;
            object realmBar = Bar(realm?.Name ?? "Realm", rp, RealmThresholds,
                realm != null && ti >= 0 && ti < realm.Titles.Count ? realm.Titles[ti] : null);
            NewClient.Send(p, "#REP|" + JsonConvert.SerializeObject(new { zone = z?.Name ?? "", factions, realm = realmBar, title = TitleFor(p) }));
        }

        /// <summary>"#REPW|..." for the Reputation window: every zone's factions in your realm, with their titles, your
        /// realm standing, and the titles you've earned (numbered for /rep title).</summary>
        public static void SendWindow(GamePlayer p)
        {
            Standing s = Of(p);
            if (s == null)
                return;
            bool female = Female(p);
            var zones = new List<object>();
            foreach (RepZoneDef z in RepDefs.Zones.Where(z => z.Realm == (int) p.Realm))
            {
                var fs = new List<object>();
                foreach (RepFactionDef f in z.Factions)
                {
                    double pts = s.Get(f.Key);
                    Rank r = RankOf(pts);
                    fs.Add(new
                    {
                        name = f.Name,
                        rank = r.ToString(),
                        points = Math.Floor(pts),
                        lo = Thresholds[(int) r],
                        hi = (int) r + 1 < Thresholds.Length ? Thresholds[(int) r + 1] : Thresholds[(int) r],
                        titles = new[] { Rank.Trusted, Rank.Honoured, Rank.Legend }.Select(k => new { rank = k.ToString(), title = f.Title(k, female), earned = r >= k }),
                        next = NextUnlock(f, r, female)
                    });
                }
                zones.Add(new { name = z.Name, factions = fs });
            }
            RepRealmDef realm = RepDefs.Realm(p.Realm);
            double rp = RealmPoints(p);
            Rank rr = RealmRankOf(rp);
            var earned = TitlesEarned(p);
            var payload = new
            {
                title = TitleFor(p),
                locked = s.Lock ?? "",
                titles = earned.Select((t, i) => new { n = i + 1, title = t.Title, from = t.Faction, rank = t.Rank.ToString() }),
                realm = new
                {
                    name = realm?.Name ?? "Realm",
                    rank = rr.ToString(),
                    points = Math.Floor(rp),
                    lo = RealmThresholds[(int) rr],
                    hi = (int) rr + 1 < RealmThresholds.Length ? RealmThresholds[(int) rr + 1] : RealmThresholds[(int) rr],
                    rvr = Math.Floor(s.Rvr),
                    titles = new[] { Rank.Trusted, Rank.Honoured, Rank.Legend }.Select(k => new
                    {
                        rank = k.ToString(),
                        title = realm != null && (int) k - 2 < realm.Titles.Count ? realm.Titles[(int) k - 2] : "",
                        earned = rr >= k
                    })
                },
                zones
            };
            NewClient.Send(p, "#REPW|" + JsonConvert.SerializeObject(payload));
        }

        static string NextUnlock(RepFactionDef f, Rank r, bool female) => r switch
        {
            Rank.Unknown => $"Next - Familiar ({Thresholds[1]:N0}): 5% off with {f.ZoneDef.Name}'s merchants",
            Rank.Familiar => $"Next - Trusted ({Thresholds[2]:N0}): the title {f.Title(Rank.Trusted, female)}" + (f.Quartermaster != null ? $", {f.Quartermaster.Name}'s stock" : ""),
            Rank.Trusted => $"Next - Honoured ({Thresholds[3]:N0}): the title {f.Title(Rank.Honoured, female)}, 10% off" + (f.Quartermaster != null ? ", more stock" : ""),
            Rank.Honoured => $"Next - Legend ({Thresholds[4]:N0}): the title {f.Title(Rank.Legend, female)} and a Legend's own piece",
            _ => "You are a Legend here."
        };

        // ------------------------------------------------------------------ bots: their standing

        /// <summary>A bot's starting standing (owner: "the world doesn't start with everyone Unknown"): with each zone of
        /// its realm it has outgrown, some standing - more the further past the zone it is; a rare veteran is a Legend.
        /// Seeded by its id, so the same bot always gets the same.</summary>
        static void Seed(GameBot bot, Standing s)
        {
            lock (s.Sync)
            {
                if (s.Seeded)
                    return;
                s.Seeded = true;
                s.Dirty = true;
                if (!bot.IsAutonomousWorldBot || bot.IsTemporaryGroupHelper)
                    return;
                SeedInto(s, bot.Realm, bot.Level, bot.DatabaseID);
            }
        }

        public static void SeedInto(Standing s, eRealm realm, int level, long id)
        {
            var rng = new Random((int) (Math.Abs(id * 7919L) % int.MaxValue));
            foreach (RepZoneDef z in RepDefs.Zones)
            {
                if (z.Realm != (int) realm)
                    continue;
                int lo = z.Levels.Length > 0 ? z.Levels[0] : 1;
                int hi = z.Levels.Length > 1 ? z.Levels[1] : 50;
                if (level <= lo + 2)
                    continue;
                double frac = Math.Clamp((level - lo) / (double) (hi - lo + 15), 0, 1);
                foreach (RepFactionDef f in z.Factions)
                {
                    double pts = frac * Thresholds[(int) Rank.Honoured] * (0.25 + 0.95 * rng.NextDouble());
                    if (level >= 40 && rng.NextDouble() < 0.03)
                        pts = Thresholds[(int) Rank.Legend] + rng.Next(0, 2000);
                    s.Points[f.Key] = Math.Round(pts);
                }
            }
            if (level >= 20)
                s.Rvr = Math.Round(rng.NextDouble() * level * 60);
        }

        static long _nextTrickle;

        /// <summary>Every five minutes: a bot working a zone with factions (fighting lately) earns a little - its own
        /// quests and errands, which it doesn't run as you do.</summary>
        static void Trickle(long now)
        {
            if (now < _nextTrickle)
                return;
            _nextTrickle = now + 300_000;
            var rng = new Random();
            foreach (GameBot bot in AutonomousBotRegistry.Snapshot())
            {
                if (bot == null || !bot.IsAlive || bot.IsTemporaryGroupHelper)
                    continue;
                RepZoneDef z = RepDefs.ForZone(bot.CurrentZone);
                if (z == null || z.Realm != (int) bot.Realm)
                    continue;
                if (now - bot.LastAttackTickPvE > 300_000 && now - bot.LastAttackedByEnemyTickPvE > 300_000)
                    continue;
                Gain(bot, z.Factions[rng.Next(z.Factions.Count)], BotTricklePoints, quiet: true);
            }
        }

        // ------------------------------------------------------------------ bots' titles on their plates

        static readonly ConcurrentDictionary<GamePlayer, Dictionary<int, string>> _titlesSent = new();
        static readonly ConcurrentDictionary<GamePlayer, ushort> _titlesRegion = new();

        /// <summary>"#TITLES|oid=title;..." for the bots near a player whose worn title changed (oid= : none now).</summary>
        static void PushTitles(GamePlayer p)
        {
            if (!NewClient.Is(p) || p.CurrentRegion == null)
                return;
            var sent = _titlesSent.GetOrAdd(p, _ => new());
            var parts = new List<string>();
            if (!_titlesRegion.TryGetValue(p, out ushort reg) || reg != p.CurrentRegionID)
            {
                sent.Clear();
                _titlesRegion[p] = p.CurrentRegionID;
                parts.Add("!");                                // (a new region: the client forgets the old ones)
            }
            var seen = new HashSet<int>();
            foreach (GameNPC n in p.GetNPCsInRadius(4000))
            {
                if (n is not GameBot b || !b.IsAlive || b.Realm != p.Realm)
                    continue;
                string t = TitleFor(b) ?? "";
                seen.Add(b.ObjectID);
                bool had = sent.TryGetValue(b.ObjectID, out string was);
                sent[b.ObjectID] = t;
                if (had ? was == t : t == "")
                    continue;                                  // (unchanged, or nothing to say)
                parts.Add($"{b.ObjectID}={t.Replace(';', ',').Replace('=', '-')}");
            }
            foreach (int gone in sent.Keys.Where(k => !seen.Contains(k)).ToList())
            {
                if (sent[gone] != "")
                    parts.Add($"{gone}=");                     // (out of sight: its id may be someone else's next)
                sent.Remove(gone);
            }
            if (parts.Count > 0)
                NewClient.Send(p, "#TITLES|" + string.Join(";", parts));
        }

        // ------------------------------------------------------------------ bots talking about people of standing

        static readonly ConcurrentDictionary<string, long> _talkPair = new();
        static readonly ConcurrentDictionary<long, long> _talkBot = new();
        static readonly ConcurrentDictionary<GamePlayer, long> _talkHeard = new();
        static readonly ConcurrentDictionary<string, long> _greeted = new();
        static readonly Random _rng = new();

        static readonly string[] LegendToYou =
        {
            "{title}! It's an honour.", "Make way - that's {name}, {title}!", "Is that really {name}? The {short} sing your praises.",
            "{name}... a Legend of the {short}, right here."
        };
        static readonly string[] LegendOther =
        {
            "Look - {name}, {title}.", "That's {name}. They say the {short} owe {them} everything.", "Mind your manners. That's {title} {name}."
        };
        static readonly string[] HonouredToYou =
        {
            "{name}? I've heard the {short} speak well of you.", "Good to see you, {name}. Word of your deeds reached {town}.",
            "The {short} could use more like you, {name}."
        };
        static readonly string[] HonouredOther =
        {
            "There goes {name} - the {short} think the world of {them}.", "That's {name}. Good with a blade, they say, and better company."
        };

        static string Fill(string line, GameLiving who, RepFactionDef f, string title) => line
            .Replace("{name}", who.Name).Replace("{title}", title ?? "").Replace("{short}", f.Short)
            .Replace("{town}", f.Town ?? f.ZoneDef.Name).Replace("{them}", who.Gender == eGender.Female ? "her" : "him");

        /// <summary>Who someone is here: their best faction of the zone and its rank.</summary>
        static (RepFactionDef F, Rank R) Notable(GameLiving who, RepZoneDef z)
        {
            RepFactionDef best = null;
            double bestPts = 0;
            foreach (RepFactionDef f in z.Factions)
            {
                double pts = Points(who, f);
                if (pts > bestPts)
                {
                    best = f;
                    bestPts = pts;
                }
            }
            return (best, RankOf(bestPts));
        }

        /// <summary>Every few seconds near each player: a bot near someone of high standing here says so - you, or
        /// another bot - and the faction's speaker greets you when you come by (owner: "bots commenting when another
        /// bot or player with a higher reputation in that area will make it feel more impactful").</summary>
        static void Chatter(GamePlayer p, long now)
        {
            RepZoneDef z = RepDefs.ForZone(p.CurrentZone);
            if (z == null || z.Realm != (int) p.Realm || !p.IsAlive)
                return;
            // the speaker's greeting
            foreach (RepFactionDef f in z.Factions)
            {
                if (RankWith(p, f) < Rank.Honoured)
                    continue;
                GameNPC sp = StoryQuestManager.Npc(f.Speaker);
                string key = $"{p.ObjectId}/{f.Key}";
                if (sp == null || sp.CurrentRegion != p.CurrentRegion || !sp.IsWithinRadius(p, 700) ||
                    (_greeted.TryGetValue(key, out long g) && now < g))
                    continue;
                _greeted[key] = now + 30 * 60_000;
                string t = f.Title(RankWith(p, f), Female(p)) ?? p.Name;
                NpcSpeech.Say(sp, RankWith(p, f) >= Rank.Legend ? $"{t}! {f.Town ?? "We"} is glad of you." : $"Good to see you, {p.Name}. The {f.Short} remember what you've done.");
                return;
            }
            if (_talkHeard.TryGetValue(p, out long heard) && now < heard)
                return;
            // the people of standing here: you, and the bots near you
            var bots = p.GetNPCsInRadius(1600).OfType<GameBot>()
                .Where(b => b.IsAlive && b.IsAutonomousWorldBot && b.Realm == p.Realm && !b.InCombat).ToList();
            if (bots.Count == 0)
                return;
            var notable = new List<(GameLiving Who, RepFactionDef F, Rank R)>();
            var (pf, pr) = Notable(p, z);
            if (pf != null && pr >= Rank.Honoured)
                notable.Add((p, pf, pr));
            foreach (GameBot b in bots)
            {
                var (bf, br) = Notable(b, z);
                if (bf != null && br >= Rank.Honoured)
                    notable.Add((b, bf, br));
            }
            foreach (var (who, f, r) in notable.OrderBy(_ => _rng.Next()))
            {
                GameBot speaker = bots.Where(b => b != who && b.IsWithinRadius(who, WorldMgr.SAY_DISTANCE) && b.IsWithinRadius(p, WorldMgr.SAY_DISTANCE) &&
                        (!_talkBot.TryGetValue(b.DatabaseID, out long nb) || now >= nb) &&
                        (!_talkPair.TryGetValue($"{b.DatabaseID}/{who.ObjectID}", out long np) || now >= np))
                    .OrderBy(_ => _rng.Next()).FirstOrDefault();
                if (speaker == null)
                    continue;
                string title = f.Title(r, Female(who));
                var (sf, sr) = Notable(speaker, z);
                string line;
                if (who is GameBot other && sf == f && sr >= Rank.Honoured)
                {
                    // two of standing: a greeting, and its answer
                    line = $"Well met, {other.Name}.";
                    string sTitle = sf.Title(sr, Female(speaker)) ?? speaker.Name;
                    AutonomousHelpCalls.Later(other, 2_200, () => other.Say($"And you, {sTitle}."));
                }
                else
                {
                    string[] pool = r >= Rank.Legend ? (who == p ? LegendToYou : LegendOther) : (who == p ? HonouredToYou : HonouredOther);
                    line = Fill(pool[_rng.Next(pool.Length)], who, f, title);
                }
                _talkBot[speaker.DatabaseID] = now + 3 * 60_000;
                _talkPair[$"{speaker.DatabaseID}/{who.ObjectID}"] = now + 30 * 60_000;
                _talkHeard[p] = now + 45_000;
                speaker.TurnTo(who, 4000);
                AutonomousHelpCalls.Later(speaker, 300, () => speaker.Say(line));
                return;
            }
        }

        // ------------------------------------------------------------------ the clock

        static long _nextTitles, _nextChatter, _nextPanel, _nextSave;

        static int Tick(ECSGameTimer t)
        {
            long now = GameLoop.GameLoopTime;
            try
            {
                foreach (var (p, due) in _pushDue)
                    if (now >= due)
                        Push(p);
                bool titles = now >= _nextTitles, chatter = now >= _nextChatter, panel = now >= _nextPanel;
                if (titles)
                    _nextTitles = now + 3_000;
                if (chatter)
                    _nextChatter = now + 6_000;
                if (panel)
                    _nextPanel = now + 30_000;
                if (titles || chatter || panel)
                    foreach (GamePlayer p in ClientService.Instance.GetPlayers())
                    {
                        if (p?.ObjectState != GameObject.eObjectState.Active)
                            continue;
                        if (titles)
                            PushTitles(p);
                        if (chatter)
                            Chatter(p, now);
                        if (panel)
                        {
                            Push(p);
                            CheckWornTitle(p);
                        }
                    }
                Trickle(now);
                if (now >= _nextSave)
                {
                    _nextSave = now + 60_000;
                    SaveDirty(400);
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("[Reputation] tick: " + e.Message);
            }
            return 1000;
        }

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            LoadAll();
            StoryQuestManager.Finished += OnQuestFinished;
            GameEventMgr.AddHandler(KeepEvent.KeepTaken, OnKeepTaken);
            GameEventMgr.AddHandler(GamePlayerEvent.GainedRealmPoints, new DOLEventHandler((ev, s, a) =>
            {
                if (s is GamePlayer rp && a is GainedRealmPointsEventArgs g)
                    OnRealmPoints(rp, g.RealmPoints);
            }));
            GameEventMgr.AddHandler(GamePlayerEvent.Quit, new DOLEventHandler((ev, s, a) =>
            {
                if (s is GamePlayer qp)
                {
                    Save(qp);
                    _wornTitle.TryRemove(qp, out _);
                    _titlesSent.TryRemove(qp, out _);
                    _titlesRegion.TryRemove(qp, out _);
                    _pushDue.TryRemove(qp, out _);
                    _talkHeard.TryRemove(qp, out _);
                }
            }));
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, new DOLEventHandler((ev, s, a) =>
            {
                if (s is GamePlayer gp)
                {
                    if (TitlesEarned(gp).Count > 0)
                        WearTitle(gp);
                    PushSoon(gp);
                }
            }));
            GameEventMgr.AddHandler(GamePlayerEvent.RegionChanged, new DOLEventHandler((ev, s, a) => { if (s is GamePlayer zp) PushSoon(zp); }));
            ReputationQuartermaster.StartSpawning();
            _ = new ECSGameTimer(null, Tick, 5000);
        }

        [GameServerStoppedEvent]
        public static void OnServerStopped(DOLEvent e, object sender, EventArgs args) => SaveDirty();
    }
}
