using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Text.RegularExpressions;
using DOL.AI.Brain;

namespace DOL.GS;

/// <summary>
/// Calls for help on the zone and realm defense channels, and the bots that answer them (owner 2026-11-16: "zone chat
/// ... players and bots can use it to ask for and answer for help with events and quests and the like. Bots tend to run
/// in to situations where they clearly need help but don't know how to ask for it" - "If they ask for help with
/// something they should wait for a reasonable amount of time for that help to actually arrive").
///   - A bot asks when it is losing a fight it can't win alone (two or more on it, or an orange or harder, and under half
///     health) and when an event near it is under way with few hands. It asks only when someone of its realm is in the
///     zone to hear it, and then waits where it is (resting) for the help, up to two and a half minutes.
///   - You ask with /z (or /rvr in the frontier): "help", "need a hand", "anyone around?", "lfg" ... Bots of your realm
///     that hear it and can help (free, not grouped, healthy, near enough to your level) answer on the channel - at most
///     one to three, the nearest - and come: to you, or to the event. One that comes to an "lfg" asks you aloud whether
///     you want to group (AutonomousPersonaPlay).
///   - Helpers that arrive fight whatever is on whoever asked, then go back to what they were doing once it's quiet.
/// A call follows whoever asked (it is where they are), and ends when they die, leave, or the fight has been over a
/// little while after help came - or after a few minutes regardless.
/// </summary>
public static class AutonomousHelpCalls
{
    public enum Kind { Fight, Event, Group }

    public const int AnswerDelayMinMs = 2_500;
    public const int AnswerDelayMaxMs = 6_000;
    public const int RequesterWaitMs = 150_000;            // a bot that asked waits this long at most for help to come
    public const int HelperTravelLimitMs = 180_000;        // a helper that hasn't got there by now gives up
    public const int QuietCloseMs = 15_000;                // the fight over this long after help came: done
    public const int BotCallCooldownMs = 8 * 60_000;       // a bot asks at most this often
    public const int ArrivalRadius = 500;
    public const int RvrReach = 40_000;                    // realm defense: helpers in the same region within this
    public const int MinRvrLevel = 35;
    public const int ZoneReach = 16_000;                   // zone chat: helpers this near (most of a zone, not all of it)
    public const int ZoneBotCallGapMs = 90_000;            // bots of one zone ask at most this often between them

    public sealed class Call
    {
        public int Id;
        public RealmChatChannels.Channel Channel;
        public Kind Kind;
        public GameLiving Requester;
        public string RequesterName;
        public eRealm Realm;
        public ushort RegionId;
        public Zone Zone;
        public Vector3 At;
        public string EventId = string.Empty;
        public string EventTitle = string.Empty;
        public int MinLevel;
        public int Wanted;
        public long Created;
        public long AnswerAt;
        public long Expires;
        public long QuietSince;
        public bool Answered;
        public bool Closed;
        public readonly Dictionary<long, long> Helpers = new();     // helper bot id -> when it was sent
        public readonly HashSet<long> Arrived = new();
        public bool RequesterIsPlayer => Requester is GamePlayer;
    }

    private static readonly object Sync = new();
    private static readonly List<Call> Calls = new();
    private static readonly Dictionary<long, Call> HelperOf = new();
    private static readonly Dictionary<long, long> NextBotCall = new();
    private static readonly Dictionary<ushort, long> NextZoneCall = new();
    private static readonly DOL.Logging.Logger Log = DOL.Logging.LoggerManager.Create(typeof(AutonomousHelpCalls));
    private static int _nextId;
    private static readonly Random Rng = new();

    // ---------------------------------------------------------------- pure rules (unit tested)

    private static readonly Regex HelpWords = new(
        @"\b(help|helps|helping|assist|assistance|hand|backup|back\s?up|save me|rescue|heal me|need (a |some )?(heal|healer|tank|people|hands?)|anyone (around|near|nearby|close)|adds?|train|overrun|dying|inc|incoming|rally|defend|defense|under attack|attacking|siege|sieged|relic)\b",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex GroupWords = new(
        @"\b(lfg|lfm|lf\d?m|looking for (a )?(group|party|people|someone)|group (up|me)?|party (up)?|join me|want to group|wanna group|need (a )?group)\b",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    /// <summary>A line asking for help (a fight, an event, a keep).</summary>
    public static bool HelpWanted(string text) => !string.IsNullOrWhiteSpace(text) && HelpWords.IsMatch(text);

    /// <summary>A line looking for a group.</summary>
    public static bool GroupWanted(string text) => !string.IsNullOrWhiteSpace(text) && GroupWords.IsMatch(text);

    /// <summary>Whether a bot can answer a call: free (not grouped, not fighting, not travelling by horse), healthy, of
    /// the caller's realm, near enough, and not too low for it.</summary>
    public static bool CanAnswer(bool solo, bool idle, int healthPercent, int level, int minLevel, bool sameRealm, bool inReach) =>
        solo && idle && sameRealm && inReach && healthPercent >= 60 && level >= minLevel;

    /// <summary>How many come: one for a group, two for a fight (three in the frontier), three for an event.</summary>
    public static int HelpersWanted(Kind kind, RealmChatChannels.Channel channel) => kind switch
    {
        Kind.Group => 1,
        Kind.Event => 3,
        _ => channel == RealmChatChannels.Channel.Rvr ? 3 : 2,
    };

    /// <summary>The lowest level that answers: a few below the one asking (an event: its own lowest, less two).</summary>
    public static int MinimumLevel(Kind kind, int requesterLevel, int eventMinLevel, RealmChatChannels.Channel channel)
    {
        int min = kind == Kind.Event && eventMinLevel > 0 ? eventMinLevel - 2 : requesterLevel - 3;
        if (channel == RealmChatChannels.Channel.Rvr)
            min = Math.Max(min, MinRvrLevel);
        return Math.Max(1, min);
    }

    // ---------------------------------------------------------------- lines

    private static readonly string[] FightAsks =
    [
        "Help! {foes} on me {place}!", "Could use a hand {place} - {foes} are too much for me!",
        "Anyone near {place}? {foes} have me pinned!", "Need help {place}, {foes}! I won't last long!",
    ];

    private static readonly string[] EventAsks =
    [
        "{title} is under way {place} - we need more hands!", "Anyone free? {title}, {place}. Come help!",
        "Need help with {title} {place}!", "{title} {place} - there aren't enough of us, come quick!",
    ];

    private static readonly string[] Coming =
    [
        "On my way!", "Coming!", "Heading there now.", "Hold on, I'm coming.", "Be there shortly.", "omw, hang on",
    ];

    private static readonly string[] ComingToPlayer =
    [
        "On my way, {name}!", "Hang on, {name}, coming!", "Coming to you, {name}.", "{name}, I'm close - be right there.",
    ];

    private static readonly string[] ComingToGroup =
    [
        "I can join you, {name}. Coming to you.", "I'm free - on my way to you, {name}.", "I'll group with you, {name}. Heading your way.",
    ];

    private static readonly string[] ComingToEvent =
    [
        "Heading to {title} now.", "On my way to help with {title}!", "I'll be at {title} shortly.",
    ];

    private static readonly string[] Busy =
    [
        "Can't right now, sorry!", "Busy here myself, sorry.", "Wish I could, I'm tied up.",
    ];

    private static readonly string[] Waiting =
    [
        "Thanks! I'll hold here.", "Thank you - I'll wait for you here.", "Bless you. I'll stay put.",
    ];

    private static readonly string[] ArrivedLines =
    [
        "I'm here! What have we got?", "Made it! Where are they?", "Here! Let's see to this.",
    ];

    private static readonly string[] ArrivedForPlayer =
    [
        "I'm here, {name}!", "Made it, {name}! Point me at them.", "{name}! I came as quick as I could.",
    ];

    private static readonly string[] ThanksForComing =
    [
        "Thanks for coming! I owe you one.", "Glad you came. That could've gone badly.", "Thank you, friend. Truly.",
    ];

    private static readonly string[] YoureWelcome =
    [
        "Anytime.", "Glad I could help.", "That's what we're here for.", "Stay safe out there.",
    ];

    public static string Pick(string[] lines, Random rng = null) => lines[(rng ?? Rng).Next(lines.Length)];

    public static string Fill(string line, string name = null, string place = null, string foes = null, string title = null) =>
        line.Replace("{name}", name ?? "friend").Replace("{place}", place ?? "here").Replace("{foes}", foes ?? "they")
            .Replace("{title}", title ?? "the event");

    /// <summary>"a giant spider", "Bloodfang", "a forest bear and 2 more".</summary>
    public static string DescribeFoes(IReadOnlyList<string> names)
    {
        if (names == null || names.Count == 0)
            return "monsters";
        string first = names[0];
        string one = first.Length > 0 && char.IsUpper(first[0]) ? first
            : ("aeiou".Contains(char.ToLowerInvariant(first[0])) ? "an " : "a ") + first;
        return names.Count == 1 ? one : $"{one} and {names.Count - 1} more";
    }

    // ---------------------------------------------------------------- asking

    private static long KeyOf(GameLiving who) => who is GameBot b ? b.DatabaseID : -(long)who.ObjectID - 1;

    /// <summary>A bot losing a fight asks its zone for help (WorldTalk notices the trouble). True when it asked.</summary>
    public static bool TryFightCall(GameBot bot, IReadOnlyList<string> foeNames)
    {
        if (bot?.CurrentZone == null || bot.Group != null || !bot.IsAutonomousWorldBot || bot.IsTemporaryGroupHelper ||
            !RealmChatChannels.HasZoneAudience(bot.Realm, bot.CurrentZone))
            return false;
        long now = GameLoop.GameLoopTime;
        RealmChatChannels.Channel channel = bot.CurrentZone.IsRvR ? RealmChatChannels.Channel.Rvr : RealmChatChannels.Channel.Zone;
        lock (Sync)
        {
            if (NextBotCall.TryGetValue(bot.DatabaseID, out long next) && now < next)
                return false;
            if (Calls.Any(c => !c.Closed && c.Requester == bot))
                return false;
            if (NextZoneCall.TryGetValue(bot.CurrentZone.ID, out long zoneNext) && now < zoneNext)
                return false;
            NextBotCall[bot.DatabaseID] = now + BotCallCooldownMs;
            NextZoneCall[bot.CurrentZone.ID] = now + ZoneBotCallGapMs;
        }
        string text = Fill(Pick(FightAsks), place: RealmChatChannels.PlaceOf(bot), foes: DescribeFoes(foeNames));
        RealmChatChannels.Send(bot, channel, text);
        Open(bot, channel, Kind.Fight, string.Empty, string.Empty, 0);
        return true;
    }

    /// <summary>A bot at an event with few hands asks the zone (WorldTalk, at a stage's start).</summary>
    public static bool TryEventCall(GameBot bot, string eventId, string title, Vector3 at, int eventMinLevel)
    {
        if (bot?.CurrentZone == null || !RealmChatChannels.HasZoneAudience(bot.Realm, bot.CurrentZone))
            return false;
        long now = GameLoop.GameLoopTime;
        lock (Sync)
        {
            if (Calls.Any(c => !c.Closed && c.Kind == Kind.Event && c.EventId == eventId))
                return false;
            if (NextBotCall.TryGetValue(bot.DatabaseID, out long next) && now < next)
                return false;
            NextBotCall[bot.DatabaseID] = now + BotCallCooldownMs;
        }
        RealmChatChannels.Send(bot, RealmChatChannels.Channel.Zone,
            Fill(Pick(EventAsks), place: RealmChatChannels.PlaceOf(bot), title: title));
        Call call = Open(bot, RealmChatChannels.Channel.Zone, Kind.Event, eventId, title, eventMinLevel);
        call.At = at;
        return true;
    }

    /// <summary>The player's /zone or /rvr line: a call for help or a group, else perhaps an answer from someone who
    /// knows (the way to a place, a stable master, a spell).</summary>
    public static void OnPlayerChannel(GamePlayer player, RealmChatChannels.Channel channel, string text)
    {
        if (player?.CurrentRegion == null)
            return;
        if (channel == RealmChatChannels.Channel.Zone && GroupWanted(text) &&
            (player.Group == null || player.Group.MemberCount < 8))
        {
            Open(player, channel, Kind.Group, string.Empty, string.Empty, 0);
            return;
        }
        if (HelpWanted(text))
        {
            if (channel == RealmChatChannels.Channel.Zone && NearEvent(player, out string id, out string title, out Vector3 at, out int min))
            {
                Call call = Open(player, channel, Kind.Event, id, title, min);
                call.At = at;
            }
            else
                Open(player, channel, Kind.Fight, string.Empty, string.Empty, 0);
            return;
        }
        // not a call: someone who heard may answer a question
        if (!AutonomousChatKnowledge.TryAnswer(player, text, out string answer) || string.IsNullOrWhiteSpace(answer))
        {
            if (AutonomousChatIntentModel.Predict(text) != eAutonomousChatIntent.Greeting || Rng.NextDouble() > 0.6)
                return;
            answer = Pick(["Hello!", "Greetings.", "Hail!", "Well met."]);
        }
        GameBot speaker = Listeners(player, channel).Where(b => !b.InCombat).OrderBy(_ => Rng.Next()).FirstOrDefault();
        if (speaker != null)
            Later(speaker, 2_000 + Rng.Next(2_500), () => RealmChatChannels.Send(speaker, channel, answer));
    }

    /// <summary>An event under way near the player (a stage running, or resting between two).</summary>
    private static bool NearEvent(GamePlayer player, out string id, out string title, out Vector3 at, out int minLevel)
    {
        id = title = string.Empty;
        at = default;
        minLevel = 0;
        foreach (DynamicEvents.ChainRuntime c in DynamicEvents.DynamicEventManager.Chains.ToArray())
        {
            if (c?.Region != player.CurrentRegion || !c.Active || c.Private)
                continue;
            Vector3 center = c.Stage != null ? c.Stage.Center
                : c.Leader != null ? new Vector3(c.Leader.X, c.Leader.Y, c.Leader.Z) : c.WakePoint;
            float dx = center.X - player.X, dy = center.Y - player.Y;
            if (dx * dx + dy * dy > 5000f * 5000f)
                continue;
            id = c.Def.Id;
            title = c.Def.Title;
            at = center;
            minLevel = c.Def.Levels?.FirstOrDefault() ?? 0;
            return true;
        }
        return false;
    }

    /// <summary>The bots that hear a channel line from `who`: its realm, in its zone (zone chat) or its region (realm
    /// defense), awake and in the world.</summary>
    private static IEnumerable<GameBot> Listeners(GameLiving who, RealmChatChannels.Channel channel) =>
        AutonomousBotRegistry.Snapshot().Where(b => b != null && b != who && b.IsAutonomousWorldBot && !b.IsTemporaryGroupHelper &&
            b.IsAlive && b.ObjectState == GameObject.eObjectState.Active && b.Realm == who.Realm &&
            (channel == RealmChatChannels.Channel.Zone
                ? b.CurrentZone == who.CurrentZone
                : b.CurrentRegionID == who.CurrentRegionID && b.IsWithinRadius(who, RvrReach)));

    private static Call Open(GameLiving requester, RealmChatChannels.Channel channel, Kind kind, string eventId, string title, int eventMin)
    {
        long now = GameLoop.GameLoopTime;
        var call = new Call
        {
            Channel = channel,
            Kind = kind,
            Requester = requester,
            RequesterName = requester.Name,
            Realm = requester.Realm,
            RegionId = requester.CurrentRegionID,
            Zone = requester.CurrentZone,
            At = new Vector3(requester.X, requester.Y, requester.Z),
            EventId = eventId ?? string.Empty,
            EventTitle = title ?? string.Empty,
            MinLevel = MinimumLevel(kind, requester.Level, eventMin, channel),
            Wanted = HelpersWanted(kind, channel),
            Created = now,
            AnswerAt = now + AnswerDelayMinMs + Rng.Next(AnswerDelayMaxMs - AnswerDelayMinMs),
            Expires = now + kind switch { Kind.Event => 120_000, Kind.Group => 240_000, _ => 240_000 },
        };
        lock (Sync)
        {
            foreach (Call old in Calls.Where(c => !c.Closed && c.Requester == requester))
                CloseLocked(old);                              // (one call each: the new one replaces it)
            call.Id = ++_nextId;
            Calls.Add(call);
        }
        return call;
    }

    // ---------------------------------------------------------------- the pulse (coordinator service phase)

    public static void Pulse(long now)
    {
        List<Call> toAnswer = null;
        List<(GameLiving Requester, GameBot Helper)> thanks = null;
        lock (Sync)
        {
            if (Calls.Count == 0)
                return;
            foreach (Call c in Calls.ToArray())
            {
                if (c.Closed)
                {
                    Calls.Remove(c);
                    continue;
                }
                GameLiving r = c.Requester;
                bool gone = r == null || r.ObjectState != GameObject.eObjectState.Active || r.CurrentRegionID != c.RegionId;
                if (gone || now >= c.Expires || (c.Kind == Kind.Fight && !r.IsAlive))
                {
                    CloseLocked(c);
                    continue;
                }
                if (c.Kind != Kind.Event)
                    c.At = new Vector3(r.X, r.Y, r.Z);
                foreach (long id in c.Helpers.Keys.ToArray())
                {
                    bool keep = AutonomousBotRegistry.TryGet(id, out GameBot h) && h.IsAlive && h.Group == null &&
                                h.CurrentRegionID == c.RegionId && h.ObjectState == GameObject.eObjectState.Active &&
                                (c.Arrived.Contains(id) || now - c.Helpers[id] < HelperTravelLimitMs);
                    if (!keep)
                    {
                        c.Helpers.Remove(id);
                        HelperOf.Remove(id);
                    }
                }
                if (!c.Answered)
                {
                    if (now >= c.AnswerAt)
                        (toAnswer ??= new()).Add(c);
                    continue;
                }
                if (c.Helpers.Count == 0 && c.Arrived.Count == 0)
                {
                    CloseLocked(c);                             // nobody is coming (any more): stop waiting
                    continue;
                }
                if (c.Kind == Kind.Fight && c.Arrived.Count > 0)
                {
                    if (r.InCombat)
                        c.QuietSince = 0;
                    else if (c.QuietSince == 0)
                        c.QuietSince = now;
                    else if (now - c.QuietSince >= QuietCloseMs)
                    {
                        if (r is GameBot && AutonomousBotRegistry.TryGet(c.Arrived.First(), out GameBot first))
                            (thanks ??= new()).Add((r, first));
                        CloseLocked(c);
                    }
                }
            }
        }
        if (toAnswer != null)
            foreach (Call c in toAnswer)
                Answer(c, now);
        if (thanks != null)
            foreach ((GameLiving requester, GameBot helper) in thanks)
                if (requester is GameBot rb && rb.IsAlive && rb.IsWithinRadius(helper, WorldMgr.SAY_DISTANCE))
                {
                    Later(rb, 500, () => rb.Say(Pick(ThanksForComing)));
                    Later(helper, 2_300, () => helper.Say(Pick(YoureWelcome)));
                }
    }

    /// <summary>Who answers a call: the nearest bots that hear it and can help, each saying so on the channel.</summary>
    private static void Answer(Call call, long now)
    {
        GameLiving r = call.Requester;
        GameBot[] heard = Listeners(r, call.Channel).ToArray();
        HashSet<long> busyHelpers;
        lock (Sync)
            busyHelpers = HelperOf.Keys.ToHashSet();
        GameBot[] helpers = heard
            .Where(b => !busyHelpers.Contains(b.DatabaseID) && !IsAsking(b) && !AutonomousPersonaPlay.IsOffering(b) &&
                CanAnswer(b.Group == null && !b.IsPlayerLedGroup, !b.InCombat && !b.IsCasting && !b.IsOnStableMasterRoute &&
                          !GameRelic.IsPlayerCarryingRelic(b),
                    b.HealthPercent, b.Level, call.MinLevel, b.Realm == call.Realm,
                    b.GetDistanceTo(new Point3D((int)call.At.X, (int)call.At.Y, (int)call.At.Z)) <=
                        (call.Channel == RealmChatChannels.Channel.Zone ? ZoneReach : RvrReach)))
            .OrderBy(b => b.GetDistanceTo(new Point3D((int)call.At.X, (int)call.At.Y, (int)call.At.Z)))
            .Take(call.Wanted)
            .ToArray();
        lock (Sync)
        {
            call.Answered = true;
            if (call.Closed)
                return;
            foreach (GameBot h in helpers)
            {
                call.Helpers[h.DatabaseID] = now;
                HelperOf[h.DatabaseID] = call;
            }
        }
        string why = string.Join(" ", heard.GroupBy(b =>
                busyHelpers.Contains(b.DatabaseID) ? "helping" : b.Group != null || b.IsPlayerLedGroup ? "grouped" :
                b.InCombat ? "fighting" : b.IsCasting ? "casting" : b.IsOnStableMasterRoute ? "riding" :
                b.HealthPercent < 60 ? "hurt" : b.Level < call.MinLevel ? "low" :
                b.GetDistanceTo(new Point3D((int)call.At.X, (int)call.At.Y, (int)call.At.Z)) >
                    (call.Channel == RealmChatChannels.Channel.Zone ? ZoneReach : RvrReach) ? "far" : "ok")
            .Select(g => $"{g.Key}={g.Count()}"));
        Log.Info($"HELP_CALL id={call.Id} ({why}) kind={call.Kind} channel={call.Channel} from=\"{call.RequesterName}\" level>={call.MinLevel} " +
                 $"zone=\"{call.Zone?.Description}\" heard={heard.Length} helpers=\"{string.Join(",", helpers.Select(h => $"{h.Name}({h.Level},{h.GetDistanceTo(new Point3D((int)call.At.X, (int)call.At.Y, (int)call.At.Z))})"))}\"");
        int i = 0;
        foreach (GameBot h in helpers)
        {
            string line = call.Kind switch
            {
                Kind.Group => Fill(Pick(ComingToGroup), name: call.RequesterName),
                Kind.Event => Fill(Pick(ComingToEvent), title: call.EventTitle),
                _ when call.RequesterIsPlayer => Fill(Pick(ComingToPlayer), name: call.RequesterName),
                _ => Pick(Coming),
            };
            GameBot speaker = h;
            Later(speaker, 400 + i++ * (1_500 + Rng.Next(1_500)), () => RealmChatChannels.Send(speaker, call.Channel, line));
        }
        if (helpers.Length > 0 && r is GameBot rb && call.Kind == Kind.Fight)
            Later(rb, 400 + i * 1_800 + 1_200, () => { if (rb.IsAlive) RealmChatChannels.Send(rb, call.Channel, Pick(Waiting)); });
        if (helpers.Length == 0 && call.RequesterIsPlayer && Rng.NextDouble() < 0.6)
        {
            GameBot busy = heard.Where(b => b.InCombat || b.Group != null).OrderBy(_ => Rng.Next()).FirstOrDefault();
            if (busy != null)
                Later(busy, 1_500, () => RealmChatChannels.Send(busy, call.Channel, Pick(Busy)));
        }
    }

    // ---------------------------------------------------------------- the controller's side

    /// <summary>The call this bot is answering, if any.</summary>
    public static Call AssignmentOf(GameBot bot)
    {
        if (bot == null)
            return null;
        lock (Sync)
            return HelperOf.TryGetValue(bot.DatabaseID, out Call c) && !c.Closed ? c : null;
    }

    /// <summary>Whether this bot asked for help and is waiting for it (holding where it is).</summary>
    public static bool IsWaiting(GameBot bot)
    {
        if (bot == null)
            return false;
        long now = GameLoop.GameLoopTime;
        lock (Sync)
            return Calls.Any(c => !c.Closed && c.Requester == bot && c.Kind == Kind.Fight && c.Arrived.Count == 0 &&
                                  now - c.Created < RequesterWaitMs && (!c.Answered || c.Helpers.Count > 0));
    }

    private static bool IsAsking(GameBot bot)
    {
        lock (Sync)
            return Calls.Any(c => !c.Closed && c.Requester == bot);
    }

    /// <summary>Where the call wants its helpers now.</summary>
    public static Vector3 Where(Call call)
    {
        lock (Sync)
            return call.At;
    }

    /// <summary>A helper got there: it says so (aloud), and for a group call asks the player whether to group.</summary>
    public static void ReportArrived(GameBot helper, Call call)
    {
        bool first;
        lock (Sync)
        {
            if (call.Closed || !call.Helpers.ContainsKey(helper.DatabaseID) || !call.Arrived.Add(helper.DatabaseID))
                return;
            first = call.Arrived.Count == 1;
        }
        Log.Info($"HELP_ARRIVED id={call.Id} kind={call.Kind} helper={helper.Name} for=\"{call.RequesterName}\"");
        if (call.Kind == Kind.Group && call.Requester is GamePlayer gp)
        {
            AutonomousPersonaPlay.BeginOffer(gp, helper, approached: true, answeringCall: true);
            Release(helper);
            lock (Sync)
                CloseLocked(call);
            return;
        }
        if (!first && Rng.NextDouble() < 0.6)
            return;
        string line = call.RequesterIsPlayer ? Fill(Pick(ArrivedForPlayer), name: call.RequesterName) : Pick(ArrivedLines);
        helper.Say(line);
    }

    /// <summary>What a helper that got there should fight: what is on whoever asked.</summary>
    public static GameLiving FoeFor(GameBot helper, Call call)
    {
        GameLiving r = call.Requester;
        if (r == null || !r.IsAlive || r.CurrentRegionID != helper.CurrentRegionID)
            return null;
        GameLiving best = null;
        double bestD = double.MaxValue;
        void Consider(GameObject o)
        {
            if (o is not GameLiving foe || foe == helper || !foe.IsAlive || foe.ObjectState != GameObject.eObjectState.Active ||
                foe.CurrentRegionID != helper.CurrentRegionID || foe.Realm == helper.Realm ||
                !helper.IsWithinRadius(foe, 2_500) || (foe is GameNPC n && n.Brain is IControlledBrain && foe.Realm == eRealm.None) ||
                !GameServer.ServerRules.IsAllowedToAttack(helper, foe, true))
                return;
            double d = helper.GetDistanceTo(foe);
            if (d < bestD)
            {
                bestD = d;
                best = foe;
            }
        }
        try
        {
            foreach (GameLiving attacker in r.attackComponent.AttackerTracker.Attackers.ToList())
                if (attacker?.TargetObject == r || attacker?.InCombat == true)
                    Consider(attacker);
        }
        catch (InvalidOperationException) { }
        if (best == null && r.InCombat && r.TargetObject is GameLiving t && t.InCombat)
            Consider(t);
        return best;
    }

    /// <summary>The bot stops answering (it went elsewhere, or the call took it to an event camp).</summary>
    public static void Release(GameBot bot)
    {
        if (bot == null)
            return;
        lock (Sync)
            if (HelperOf.Remove(bot.DatabaseID, out Call c))
                c.Helpers.Remove(bot.DatabaseID);
    }

    private static void CloseLocked(Call c)
    {
        c.Closed = true;
        foreach (long id in c.Helpers.Keys)
            if (HelperOf.TryGetValue(id, out Call mine) && mine == c)
                HelperOf.Remove(id);
        c.Helpers.Clear();
    }

    /// <summary>On the game loop after a moment (speech is never sent from a bot's thinking thread).</summary>
    public static void Later(GameObject owner, int delayMs, Action action)
    {
        _ = new ECSGameTimer(owner, _ =>
        {
            try
            {
                if (owner is not GameLiving l || l.ObjectState == GameObject.eObjectState.Active)
                    action();
            }
            catch (Exception) { }
            return 0;
        }, Math.Max(1, delayMs));
    }

    /// <summary>For tests and /gm checks: the open calls.</summary>
    public static int OpenCount
    {
        get { lock (Sync) return Calls.Count(c => !c.Closed); }
    }
}
