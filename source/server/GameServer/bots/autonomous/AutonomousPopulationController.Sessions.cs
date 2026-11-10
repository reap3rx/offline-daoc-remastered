using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using DOL.Database;
using DOL.GS.PacketHandler;
using OfflineDaoc.Population;

namespace DOL.GS;

/// <summary>
/// The living population's sessions (owner 2026-11-10, "Living Bot Population - Plan", step 1): each realm's online
/// count follows a daily curve on the PC's clock (PopulationCurve, the plan's shares doubled), inside the ceiling;
/// within it, bots log in by their own habits (PopulationPicker: schedule, room in the level band, class mix, time since
/// they last played) and play a session as long as their persona's (casual 30-90 minutes, regular 1-3 hours, tryhard
/// 2-5 hours). Logging out looks like a person stopping: the fight in hand is finished and no new pull starts, a
/// grouped bot says goodbye in party chat and leaves - with you in the group it stays up to half an hour past its time
/// while the group is busy - then it stands a moment and is gone, saved where it stopped. About 1 session in 200 ends
/// as if the connection dropped. Bots that have never played ("not yet arrived") log in only while the 1-9 band has
/// room for new arrivals, so a fresh roster arrives in waves. A restart fills to the hour's target over ten minutes.
/// </summary>
public static partial class AutonomousPopulationController
{
    public const int MaximumLoginsPerRealmPerPoll = 4;
    public const double RestartFillMinutes = 10.0;
    public const double PlayerGroupGraceMinutes = 30.0;
    public const double DropChance = 1.0 / 200.0;

    private sealed class Session
    {
        public DateTime EndsUtc;
        public bool Drop;
        public double ExtendedMinutes;
        public int Phase;                                      // 0 playing, 1 finishing up, 2 waving goodbye
        public DateTime PhaseUtc;
        public bool Busy;                                      // a step is posted to the game loop
    }

    private static readonly ConcurrentDictionary<long, Session> Sessions = new();
    private static readonly ConcurrentDictionary<long, BotPersona> Personas = new();
    private static readonly ConcurrentDictionary<eRealm, int> LastTargets = new();
    private static readonly ConcurrentDictionary<eRealm, DateTime> NextShorten = new();
    private static PopulationKnobs _knobs = new();
    private static DateTime _clockOriginLocal = DateTime.Now;
    private static readonly Random Rng = new();

    public static PopulationKnobs Knobs => _knobs;

    /// <summary>The clock the curve reads: the PC's own, or on the fast clock a day an hour from the server's start.</summary>
    public static DateTime ClockNow(DateTime nowUtc) =>
        _knobs.FastClock ? _clockOriginLocal + TimeSpan.FromTicks((long)((nowUtc - _startedUtc).Ticks * _knobs.ClockRate)) : DateTime.Now;

    public static int LastTarget(eRealm realm) => LastTargets.GetValueOrDefault(realm);

    private static void LoadKnobs()
    {
        _knobs = PopulationKnobs.FromProperties(ReadProperty);
        _launchUtc = DateTime.TryParse(ReadProperty(LaunchKey), null, System.Globalization.DateTimeStyles.RoundtripKind,
            out DateTime launch) ? launch.ToUniversalTime() : null;
    }

    public const string LaunchKey = "population_launch_utc";
    private static DateTime? _launchUtc;

    /// <summary>Days since the population's launch on the population's clock (a day an hour on the fast clock). The launch is
    /// stamped at the first poll that finds no stamp (the launcher clears it when it builds a fresh roster).</summary>
    private static double DaysSinceLaunch(DateTime nowUtc)
    {
        if (_launchUtc == null)
        {
            _launchUtc = nowUtc;
            try
            {
                DbServerProperty row = DOLDB<DbServerProperty>.SelectObject(DB.Column("Key").IsEqualTo(LaunchKey));
                if (row != null)
                {
                    row.Value = nowUtc.ToString("O");
                    GameServer.Database.SaveObject(row);
                }
            }
            catch (Exception exception)
            {
                Log.Warn($"Could not stamp the population's launch time: {exception.Message}");
            }
        }
        return (nowUtc - _launchUtc.Value).TotalDays * _knobs.ClockRate;
    }

    public static BotPersona PersonaOf(OfflineWorldBotRecord record)
    {
        if (Personas.TryGetValue(record.BotId, out BotPersona cached))
            return cached;
        BotPersona persona = BotPersona.Parse(record.PersonaJson);
        if (persona == null)
        {
            persona = AutonomousBotPersonas.IsSpecial(record.Name)
                ? AutonomousBotPersonas.SpecialPersona(record.Name)
                : BotPersona.Roll(Rng, record.ClassId, _knobs.CasualPct, _knobs.TryhardPct);
            record.PersonaJson = persona.ToJson();              // (saved with the record at its first login)
        }
        Personas[record.BotId] = persona;
        return persona;
    }

    private static double MinutesSinceLogout(OfflineWorldBotRecord record, DateTime nowUtc)
    {
        if (string.IsNullOrWhiteSpace(record.LastLogoutUtc) ||
            !DateTime.TryParse(record.LastLogoutUtc, null, System.Globalization.DateTimeStyles.RoundtripKind, out DateTime at))
            return 1e6;
        return Math.Max(0, (nowUtc - at.ToUniversalTime()).TotalMinutes * _knobs.ClockRate);
    }

    /// <summary>The realm's online target now: the curve's, filled in over the first ten minutes after a start.</summary>
    private static int RealmTarget(int rosterSize, DateTime local, DateTime nowUtc)
    {
        int target = PopulationCurve.Target(rosterSize, local, _knobs);
        double fill = Math.Clamp((nowUtc - _startedUtc).TotalMinutes / RestartFillMinutes, 0.0, 1.0);
        return (int)Math.Ceiling(target * fill);
    }

    /// <summary>One poll of the schedule: logins for each realm short of its target, logouts for sessions that ended.</summary>
    private static void PollSchedule(OfflineWorldBotRecord[] roster, DateTime nowUtc)
    {
        DateTime local = ClockNow(nowUtc);
        StepLogouts(nowUtc);
        GameBot[] live = AutonomousBotRegistry.Snapshot();
        bool satisfied = true;
        foreach (eRealm realm in new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia })
        {
            OfflineWorldBotRecord[] realmRoster = roster.Where(r => r.Realm == (int)realm).ToArray();
            int arrived = realmRoster.Count(r => r.HasArrived);
            double days = DaysSinceLaunch(nowUtc);
            int target = RealmTarget(PopulationArrivals.Known(realmRoster.Length, arrived, days), local, nowUtc);
            LastTargets[realm] = target;
            GameBot[] realmLive = live.Where(b => b.Realm == realm).ToArray();
            OfflineWorldBotRecord[] pending = realmRoster.Where(r => PendingSpawns.ContainsKey(r.BotId)).ToArray();
            int online = realmLive.Length + pending.Length;
            if (online > target * 1.15 + 2)
                ShortenOneSession(realm, realmLive, nowUtc);
            int missing = target - online;
            if (missing <= 0)
                continue;
            satisfied = false;

            var stats = new PopulationPicker.Online();
            foreach (GameBot bot in realmLive)
                stats.Add(bot.Level, bot.PersistentRecord?.ClassId ?? 0, bot.PersistentRecord?.SessionCount <= 1);
            foreach (OfflineWorldBotRecord p in pending)
                stats.Add(p.Level, p.ClassId, !p.HasArrived);
            int room = PopulationPicker.ArrivalRoom(stats, _knobs.NewArrivals,
                PopulationArrivals.Allowed(realmRoster.Length, days), arrived);
            int[] arrivedByBand = new int[PopulationCurve.Bands];
            foreach (OfflineWorldBotRecord r in realmRoster)
                if (r.HasArrived)
                    arrivedByBand[PopulationCurve.Band(r.Level)]++;
            var byId = new Dictionary<long, OfflineWorldBotRecord>();
            var candidates = new List<PopulationPicker.Candidate>();
            foreach (OfflineWorldBotRecord r in realmRoster)
            {
                if (r.IsOnline || AutonomousBotRegistry.Contains(r.BotId) || PendingSpawns.ContainsKey(r.BotId))
                    continue;
                byId[r.BotId] = r;
                candidates.Add(new(r.BotId, r.Level, r.ClassId, PersonaOf(r), MinutesSinceLogout(r, nowUtc), r.HasArrived,
                    AutonomousBotPersonas.IsSpecial(r.Name)));
            }
            int logins = Math.Min(missing, MaximumLoginsPerRealmPerPoll);
            for (int i = 0; i < logins; i++)
            {
                PopulationPicker.Candidate? pick = PopulationPicker.Pick(candidates, stats, target, arrivedByBand, local,
                    room, Rng);
                if (pick == null)
                    break;
                candidates.Remove(pick.Value);
                OfflineWorldBotRecord record = byId[pick.Value.BotId];
                stats.Add(pick.Value.Arrived ? record.Level : 1, record.ClassId, !pick.Value.Arrived);
                if (!pick.Value.Arrived)
                    room--;
                if (!EnqueueLogin(record))
                    break;
            }
        }
        _populationSatisfied = satisfied;
    }

    /// <summary>Far over the target (the evening winding down faster than sessions end): the soonest-ending session of a
    /// bot not grouped with a real player ends now - one per realm every few seconds.</summary>
    private static void ShortenOneSession(eRealm realm, GameBot[] realmLive, DateTime nowUtc)
    {
        if (NextShorten.TryGetValue(realm, out DateTime next) && nowUtc < next)
            return;
        NextShorten[realm] = nowUtc.AddSeconds(5);
        GameBot pick = realmLive
            .Where(b => !GroupedWithPlayer(b) && Sessions.TryGetValue(b.DatabaseID, out Session s) && s.Phase == 0)
            .OrderBy(b => Sessions[b.DatabaseID].EndsUtc)
            .FirstOrDefault();
        if (pick != null && Sessions.TryGetValue(pick.DatabaseID, out Session session) && session.EndsUtc > nowUtc)
            session.EndsUtc = nowUtc;
    }

    private static bool GroupedWithPlayer(GameBot bot) => bot.Group?.GetPlayersInTheGroup().Count > 0;

    /// <summary>A bot just entered the world: its session starts (length by its persona, now and then a dropped line).</summary>
    private static void BeginSession(GameBot bot, OfflineWorldBotRecord record)
    {
        BotPersona persona = PersonaOf(record);
        double minutes = PopulationPicker.SessionMinutes(persona, _knobs.SessionScale, Rng);
        var session = new Session { EndsUtc = DateTime.UtcNow.AddMinutes(minutes / _knobs.ClockRate) };
        if (Rng.NextDouble() < DropChance)
        {
            session.Drop = true;                               // its connection "dies" part way through
            session.EndsUtc = DateTime.UtcNow.AddMinutes(minutes / _knobs.ClockRate * (0.2 + Rng.NextDouble() * 0.7));
        }
        Sessions[bot.DatabaseID] = session;
        record.HasArrived = true;
        record.SessionCount++;
        record.SessionEndsUtc = session.EndsUtc.ToString("O");
        if (string.IsNullOrWhiteSpace(record.PersonaJson))
            record.PersonaJson = persona.ToJson();
    }

    private static void StepLogouts(DateTime nowUtc)
    {
        foreach ((long botId, Session session) in Sessions)
        {
            if (!AutonomousBotRegistry.Contains(botId))
            {
                if (!PendingSpawns.ContainsKey(botId))
                    Sessions.TryRemove(botId, out _);
                continue;
            }
            if (session.Busy || nowUtc < session.EndsUtc)
                continue;
            if (session.Phase == 2 && nowUtc < session.PhaseUtc)
                continue;
            session.Busy = true;
            NpcService.Instance.Post(LogoutStep, botId);
        }
    }

    // Party goodbyes, by realm (the roleplay voice comes with the chat step; these are its first lines).
    private static readonly Dictionary<eRealm, string[]> Goodbyes = new()
    {
        [eRealm.Albion] = ["I must away. My thanks for the company.", "The hour grows late - I take my leave. Fare well, all.",
            "I am called home. Walk in the light, friends.", "That will do for me tonight. God keep you."],
        [eRealm.Midgard] = ["I must go. Good hunting to you all.", "My mead is waiting. Farewell, friends.",
            "Enough for tonight. May Odin watch over you.", "I am off home. Fight well."],
        [eRealm.Hibernia] = ["I must away, my thanks for the company.", "The night calls me home. Go softly, friends.",
            "That is all for me tonight. May Danu keep you.", "I leave you here. Safe roads, all of you."],
    };

    private static void LogoutStep(long botId)
    {
        if (!Sessions.TryGetValue(botId, out Session session))
            return;
        try
        {
            if (!AutonomousBotRegistry.TryGet(botId, out GameBot bot) || bot.ObjectState != GameObject.eObjectState.Active)
            {
                Sessions.TryRemove(botId, out _);
                return;
            }
            DateTime now = DateTime.UtcNow;
            if (session.Drop)
            {
                LogOff(bot, "Lost connection");                // (mid-fight or not: the line just went dead)
                return;
            }
            if (session.Phase == 0)
            {
                session.Phase = 1;
                session.PhaseUtc = now;
            }
            if (session.Phase == 1)
            {
                // with you in its group it stays a while longer while the group is busy (up to half an hour)
                if (GroupedWithPlayer(bot) && GroupBusy(bot) && session.ExtendedMinutes < PlayerGroupGraceMinutes)
                {
                    session.ExtendedMinutes += 5;
                    session.Phase = 0;
                    session.EndsUtc = now.AddMinutes(5 / _knobs.ClockRate);
                    return;
                }
                if (bot.InCombat && (now - session.PhaseUtc).TotalMinutes < 4)
                    return;                                    // finishes the fight it's in
                bot.StopAttack();
                bot.StopMoving();
                bot.Brain?.Stop();                             // (no new pull)
                Group group = bot.Group;
                if (group != null && group.MemberCount > 1)
                {
                    string[] lines = Goodbyes.GetValueOrDefault(bot.Realm, Goodbyes[eRealm.Albion]);
                    group.SendMessageToGroupMembers(bot, lines[Rng.Next(lines.Length)], eChatType.CT_Group, eChatLoc.CL_ChatWindow);
                    group.RemoveMember(bot);
                }
                if (bot.ObjectState != GameObject.eObjectState.Active)
                {
                    Sessions.TryRemove(botId, out _);
                    return;
                }
                session.Phase = 2;
                session.PhaseUtc = now.AddSeconds(3 + Rng.Next(4)); // stands a moment, then is gone
                return;
            }
            LogOff(bot, "Logged off");
        }
        catch (Exception exception)
        {
            Log.Error($"Autonomous logout step for bot {botId} failed", exception);
            Sessions.TryRemove(botId, out _);
        }
        finally
        {
            session.Busy = false;
        }
    }

    private static bool GroupBusy(GameBot bot) =>
        bot.Group?.GetMembersInTheGroup().Any(m => m.InCombat) == true;

    private static void LogOff(GameBot bot, string activity)
    {
        long botId = bot.DatabaseID;
        Sessions.TryRemove(botId, out _);
        OfflineWorldBotRecord record = bot.PersistentRecord;
        if (record != null)
        {
            record.LastLogoutUtc = DateTime.UtcNow.ToString("O");
            record.SessionEndsUtc = string.Empty;
            record.Activity = activity;
        }
        Group group = bot.Group;
        group?.RemoveMember(bot);
        if (bot.ObjectState == GameObject.eObjectState.Active)
            bot.Delete();                                      // (saves its state where it stands: IsOnline false)
        if (record != null)
        {
            record.Activity = activity;
            record.Dirty = true;
            lock (AutonomousBotStatusPersistence.DatabaseWriteLock)
                GameServer.Database.SaveObject(record);
        }
        Log.Info($"Autonomous character {bot.Name} {activity.ToLowerInvariant()} (session over).");
    }
}
