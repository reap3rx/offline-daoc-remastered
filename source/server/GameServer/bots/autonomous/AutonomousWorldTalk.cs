using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Text.RegularExpressions;
using DOL.AI.Brain;

namespace DOL.GS;

/// <summary>
/// What bots say aloud about the world around them (owner 2026-11-16: "Immersive roleplay chatter should be done in /say
/// when nearby. Good context sensitive things like narrowly surviving a fight, event stages, things like 'I'm going to go
/// check out this area' or things about the weather, time, etc. Anything that brings flavor and makes the bots feel more
/// immersive and alive. No more faction chatter that tries to emulate players, we want them to feel like they're in and
/// reacting to the world around them"):
///   - after a fight it nearly lost: relief - or thanks to whoever saved it, by name (you, or another bot, who answers);
///   - after it stepped in for you when you were in trouble: "You alright?" (and "Anytime" when you thank it);
///   - setting off for a new hunting ground or an event: where it's going;
///   - an event's stage starting and ending near it: a word to the others there - and, when there are few hands, a call
///     on the zone channel (AutonomousHelpCalls);
///   - idle talk (AutonomousBotChatCoordinator): the rain, the dark, the dawn, the place, its hunting - and another bot
///     near it answering.
/// Everything here is said aloud, and only when someone (you) is near enough to hear it. It also notices a bot losing
/// a fight it can't win alone, and has it ask its zone for help (AutonomousHelpCalls).
/// </summary>
public static class AutonomousWorldTalk
{
    public const int LineGapMs = 60_000;                   // one flavour line a minute per bot, at most
    public const int DepartGapMs = 5 * 60_000;

    private sealed class Watch
    {
        public bool InFight;
        public int MinHealth = 100;
        public int MaxFoes;
        public long LastSample;
        public bool Called;
        public int WorstCon;
        public readonly HashSet<GameLiving> Allies = new();
        public List<string> FoeNames = new();
        public GamePlayer Rescued;
        public long RescuedAt;

        public void Start()
        {
            InFight = true;
            MinHealth = 100;
            MaxFoes = 0;
            WorstCon = 0;
            Called = false;
            Allies.Clear();
            FoeNames = new();
        }
    }

    private static readonly ConcurrentDictionary<long, Watch> Watches = new();
    private static readonly ConcurrentDictionary<long, long> NextLine = new();
    private static readonly ConcurrentDictionary<long, long> NextDepart = new();
    private static readonly ConcurrentDictionary<string, (GameBot Bot, long Until)> Thankable = new(StringComparer.OrdinalIgnoreCase);
    private static readonly ConcurrentDictionary<ushort, (long Tick, bool Any)> PlayersInRegion = new();
    private static readonly Random Rng = new();

    // ---------------------------------------------------------------- lines

    private static readonly string[] Survived =
    [
        "Phew... that was too close.", "Still standing. Barely.", "I'll feel that one in the morning.",
        "That nearly ended badly.", "Note to self: never pull that many again.", "By the gods, I thought I was finished.",
    ];

    private static readonly string[] ThanksSaved =
    [
        "Thanks, {name}! I thought I was done for.", "{name}, you saved my hide. Thank you!", "I owe you one, {name}.",
        "Bless you, {name}. That was nearly the end of me.", "Good timing, {name}! Thank you.",
    ];

    private static readonly string[] YoureWelcome =
    [
        "Anytime.", "Glad I was close by.", "Don't mention it.", "We look out for each other out here.", "Happy to help.",
    ];

    private static readonly string[] YouAlright =
    [
        "You alright, {name}? That looked rough.", "That was close, {name}. You okay?", "Easy there, {name} - you were nearly done for.",
        "Got your back, {name}.",
    ];

    private static readonly string[] Departing =
    [
        "I'm going to go check out {place}.", "Think I'll try my luck around {place}.", "Off to hunt {monster}. Good hunting, all!",
        "Time to move on - the {monster} won't hunt themselves.", "Heading over to {place}. Wish me luck.",
    ];

    private static readonly string[] DepartingEvent =
    [
        "There's trouble at {title} - I'm going to lend a hand.", "Heading to {title}. Come along if you're free!",
        "Something's happening at {title}. I'm going to take a look.",
    ];

    private static readonly Dictionary<string, string[]> StageStart = new()
    {
        ["boss"] = ["That's a big one. Careful, everyone!", "Here it comes! Spread out!", "Steady... that thing is huge."],
        ["defend"] = ["Here they come! Hold the line!", "Stand fast, they're coming!", "Protect them, whatever happens!"],
        ["escort"] = ["Stay close, we move together.", "Keep your eyes on the road. Ambush country.", "Let's get them there in one piece."],
        ["cull"] = ["Let's thin them out.", "Plenty to go around. Have at them!", "Clear them out!"],
        ["occupy"] = ["They've taken the place. Let's take it back!", "Push them out!", "This land is ours - drive them off!"],
    };

    private static readonly string[] StageWon =
    [
        "We did it!", "Ha! That'll teach them.", "Well fought, everyone.", "That's done. Catch your breath.", "Victory!",
    ];

    private static readonly string[] StageLost =
    [
        "We couldn't hold them...", "Blast. That's a loss.", "Next time. We'll get them next time.", "Fall back, it's lost!",
    ];

    private static readonly Regex ThanksWords = new(@"\b(thanks|thank you|thank u|thx|ty|tyvm|cheers|appreciate it|much obliged)\b",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    public static bool IsThanks(string text) => !string.IsNullOrWhiteSpace(text) && ThanksWords.IsMatch(text);

    private static string Pick(string[] lines) => lines[Rng.Next(lines.Length)];

    // ---------------------------------------------------------------- who hears

    /// <summary>Someone (a player) near enough to hear this bot.</summary>
    public static bool Heard(GameLiving speaker) => speaker?.CurrentRegion != null &&
        speaker.GetPlayersInRadius(WorldMgr.SAY_DISTANCE).Any(p => p.ObjectState == GameObject.eObjectState.Active);

    private static bool AnyPlayerInRegion(GameObject o)
    {
        if (o?.CurrentRegion == null)
            return false;
        long now = GameLoop.GameLoopTime;
        if (PlayersInRegion.TryGetValue(o.CurrentRegionID, out var c) && now - c.Tick < 2_000)
            return c.Any;
        bool any = ClientService.Instance.GetPlayersOfRegion(o.CurrentRegion).Count > 0;
        PlayersInRegion[o.CurrentRegionID] = (now, any);
        return any;
    }

    private static bool LineDue(GameBot bot, long now, int gap = LineGapMs)
    {
        if (NextLine.TryGetValue(bot.DatabaseID, out long next) && now < next)
            return false;
        NextLine[bot.DatabaseID] = now + gap;
        return true;
    }

    // ---------------------------------------------------------------- fights

    /// <summary>The controller calls this each turn (in and out of combat): it follows the bot's fights.</summary>
    public static void Observe(GameBot bot)
    {
        if (bot == null || !bot.IsAutonomousWorldBot || bot.IsTemporaryGroupHelper || !AnyPlayerInRegion(bot))
            return;
        long now = GameLoop.GameLoopTime;
        Watch w = Watches.GetOrAdd(bot.DatabaseID, _ => new Watch());
        if (!bot.IsAlive)
        {
            w.InFight = false;
            return;
        }
        if (bot.InCombat)
        {
            if (!w.InFight)
                w.Start();
            if (now - w.LastSample < 1_000)
                return;
            w.LastSample = now;
            Sample(bot, w);
            // losing a fight it can't win alone: it asks its zone (only when it is alone - a group helps itself)
            if (!w.Called && bot.Group == null && !bot.IsPlayerLedGroup && bot.HealthPercent < 45 &&
                (w.MaxFoes >= 2 || w.WorstCon >= (int)ConColor.ORANGE))
            {
                w.Called = true;
                AutonomousHelpCalls.TryFightCall(bot, w.FoeNames);
            }
            return;
        }
        if (!w.InFight)
            return;
        w.InFight = false;
        try { FightOver(bot, w, now); }
        catch (Exception) { }
    }

    private static void Sample(GameBot bot, Watch w)
    {
        w.MinHealth = Math.Min(w.MinHealth, bot.HealthPercent);
        var foes = new List<GameLiving>();
        try
        {
            foreach (GameLiving a in bot.attackComponent.AttackerTracker.Attackers.ToList())
                if (a != null && a.IsAlive && a.Realm != bot.Realm && !foes.Contains(a))
                    foes.Add(a);
        }
        catch (InvalidOperationException) { }
        if (bot.TargetObject is GameLiving t && t.IsAlive && t.Realm != bot.Realm && t.InCombat && !foes.Contains(t))
            foes.Add(t);
        w.MaxFoes = Math.Max(w.MaxFoes, foes.Count);
        if (foes.Count > 0)
        {
            w.FoeNames = foes.Select(f => f.Name).ToList();
            foreach (GameLiving f in foes)
                w.WorstCon = Math.Max(w.WorstCon, (int)bot.GetConLevel(f));
        }
        foreach (GameLiving f in foes)
        {
            try
            {
                foreach (GameLiving g in f.XPGainers.Keys.ToList())
                {
                    if (g == null || g == bot || g.Realm != bot.Realm || g is GameNPC { Brain: IControlledBrain })
                        continue;
                    if (bot.Group != null && bot.Group.IsInTheGroup(g))
                        continue;
                    w.Allies.Add(g);
                }
            }
            catch (Exception) { }
        }
    }

    private static void FightOver(GameBot bot, Watch w, long now)
    {
        if (!Heard(bot))
            return;
        GameLiving saver = w.Allies.Where(a => a.IsAlive && a.ObjectState == GameObject.eObjectState.Active &&
                a.CurrentRegionID == bot.CurrentRegionID && bot.IsWithinRadius(a, 1_500))
            .OrderBy(a => a is GamePlayer ? 0 : 1).FirstOrDefault();
        if (w.MinHealth <= 25 || saver is GamePlayer && w.MinHealth < 60)
        {
            if (!LineDue(bot, now))
                return;
            if (saver != null)
            {
                bot.Say(Pick(ThanksSaved).Replace("{name}", saver.Name));
                if (saver is GameBot sb && sb.IsWithinRadius(bot, WorldMgr.SAY_DISTANCE))
                    AutonomousHelpCalls.Later(sb, 2_000 + Rng.Next(1_000), () => { if (sb.IsAlive) sb.Say(Pick(YoureWelcome)); });
            }
            else
                bot.Say(Pick(Survived));
            return;
        }
        GamePlayer rescued = w.Rescued;
        if (rescued != null && now - w.RescuedAt < 60_000 && rescued.IsAlive && rescued.CurrentRegionID == bot.CurrentRegionID &&
            bot.IsWithinRadius(rescued, 1_500))
        {
            w.Rescued = null;
            if (!LineDue(bot, now))
                return;
            bot.Say(Pick(YouAlright).Replace("{name}", rescued.Name));
            Thankable[rescued.Name] = (bot, now + 45_000);
        }
    }

    /// <summary>The bot stepped into someone's fight (AutonomousNearbyHelp): a player in trouble is remembered, to ask
    /// after them when it's over.</summary>
    public static void NoteHelping(GameBot bot, GameLiving ally, bool trouble)
    {
        if (bot == null || !trouble || ally is not GamePlayer p)
            return;
        Watch w = Watches.GetOrAdd(bot.DatabaseID, _ => new Watch());
        w.Rescued = p;
        w.RescuedAt = GameLoop.GameLoopTime;
        Thankable[p.Name] = (bot, GameLoop.GameLoopTime + 90_000);
    }

    /// <summary>Your words aloud: a thank-you to a bot that just helped you gets an answer. True when it was one.</summary>
    public static bool OnPlayerSaid(GamePlayer player, string text)
    {
        if (player == null || !IsThanks(text) || !Thankable.TryGetValue(player.Name, out var t))
            return false;
        if (GameLoop.GameLoopTime > t.Until || t.Bot == null || !t.Bot.IsAlive ||
            t.Bot.CurrentRegionID != player.CurrentRegionID || !t.Bot.IsWithinRadius(player, WorldMgr.SAY_DISTANCE + 200))
            return false;
        Thankable.TryRemove(player.Name, out _);
        GameBot bot = t.Bot;
        AutonomousHelpCalls.Later(bot, 1_000 + Rng.Next(800), () => bot.Say(Pick(YoureWelcome)));
        return true;
    }

    /// <summary>A bot that helped someone (an answered call, a rescue) can be thanked for it for a while.</summary>
    public static void MarkThankable(GamePlayer player, GameBot bot, int forMs = 60_000)
    {
        if (player != null && bot != null)
            Thankable[player.Name] = (bot, GameLoop.GameLoopTime + forMs);
    }

    // ---------------------------------------------------------------- setting off

    /// <summary>A solo bot chose a new hunting ground (or an event): it may say where it's going.</summary>
    public static void SettingOff(GameBot bot, string place, string monster, string eventTitle = null)
    {
        if (bot == null || bot.Group != null || !AnyPlayerInRegion(bot) || Rng.NextDouble() > 0.4 || !Heard(bot))
            return;
        long now = GameLoop.GameLoopTime;
        if (NextDepart.TryGetValue(bot.DatabaseID, out long next) && now < next)
            return;
        NextDepart[bot.DatabaseID] = now + DepartGapMs;
        string line = !string.IsNullOrWhiteSpace(eventTitle)
            ? Pick(DepartingEvent).Replace("{title}", eventTitle)
            : Pick(Departing).Replace("{place}", string.IsNullOrWhiteSpace(place) ? "the next valley" : place)
                .Replace("{monster}", string.IsNullOrWhiteSpace(monster) ? "game" : monster);
        AutonomousHelpCalls.Later(bot, 300, () => bot.Say(line));
    }

    // ---------------------------------------------------------------- events

    /// <summary>An event's stage began (won: null) or ended near some bots: one of them says something, if you can hear
    /// it; at a start with few hands, one of them calls the zone for help.</summary>
    public static void OnEventStage(DynamicEvents.ChainRuntime chain, DynamicEvents.StageRuntime stage, bool? won)
    {
        if (chain == null || stage == null || chain.Private || chain.Quiet || chain.Region == null)
            return;
        Vector3 c = stage.Center;
        var at = new Point3D((int)c.X, (int)c.Y, (int)c.Z);
        GameBot[] here = chain.Region.GetNPCsInRadius(at, 2_500).OfType<GameBot>()
            .Where(b => b.IsAutonomousWorldBot && !b.IsTemporaryGroupHelper && b.IsAlive &&
                        b.ObjectState == GameObject.eObjectState.Active)
            .ToArray();
        if (here.Length == 0)
            return;
        GameBot speaker = here.Where(Heard).OrderBy(_ => Rng.Next()).FirstOrDefault();
        if (speaker != null)
        {
            string line = won == null
                ? Pick(StageStart.TryGetValue(stage.Def.Type ?? string.Empty, out var s) ? s : StageStart["cull"])
                : won == true ? Pick(StageWon) : Pick(StageLost);
            AutonomousHelpCalls.Later(speaker, 800 + Rng.Next(1_500), () => speaker.Say(line));
        }
        if (won != null)
            return;
        int people = chain.PeopleNear(at, 2_500).Count();
        if (people >= 4)
            return;
        GameBot caller = here.Where(b => b.Group == null).OrderBy(_ => Rng.Next()).FirstOrDefault();
        if (caller != null)
            AutonomousHelpCalls.TryEventCall(caller, chain.Def.Id, chain.Def.Title, c, chain.Def.Levels?.FirstOrDefault() ?? 0);
    }

    // ---------------------------------------------------------------- bots grouping up

    /// <summary>A bot group formed with members standing together: the leader asks aloud and they answer - when you are
    /// there to hear it (owner 2026-11-16: bots "request ... other bots to group with them by asking in chat first").</summary>
    public static void GroupedUp(GameBot leader, IReadOnlyList<GameBot> members)
    {
        if (leader == null || members == null || members.Count == 0 || !AnyPlayerInRegion(leader) || !Heard(leader))
            return;
        GameBot near = members.FirstOrDefault(m => m != leader && m.IsAlive && m.CurrentRegionID == leader.CurrentRegionID &&
                                                   m.IsWithinRadius(leader, WorldMgr.SAY_DISTANCE));
        if (near == null)
            return;
        string ask = Pick(["{name}, want to group up?", "Hey {name}, care to join us?", "{name}! We could use you. Group?"]).Replace("{name}", near.Name);
        string yes = Pick(["Sure, lead the way.", "Gladly!", "Aye, I'm in.", "Why not. Let's go."]);
        AutonomousHelpCalls.Later(leader, 200, () => leader.Say(ask));
        AutonomousHelpCalls.Later(near, 2_000 + Rng.Next(800), () => near.Say(yes));
    }

    // ---------------------------------------------------------------- idle talk

    public sealed record Topic(string Opening, string[] Replies);

    private static readonly (string Opening, string[] Replies)[] Storm =
    [
        ("Of course it starts raining the moment I leave town.", ["Keeps the dust down, at least.", "Could be worse. Could be snow."]),
        ("This storm isn't letting up.", ["Give it an hour.", "I've stopped noticing. Mostly."]),
        ("Rain again. My boots will never dry.", ["Wool socks. Trust me.", "Ha! Mine neither."]),
        ("Hear that thunder? Close one.", ["Stay off the hilltops.", "The gods are restless tonight."]),
    ];

    private static readonly (string Opening, string[] Replies)[] Night =
    [
        ("Dark already? The day went fast.", ["It always does when you're hunting.", "Aye. Keep a torch handy."]),
        ("Keep your eyes open - things come out at night.", ["That's why I'm still awake.", "Don't I know it."]),
        ("I hate hunting in the dark.", ["The night pays better, they say.", "Stay near the others and you'll be fine."]),
        ("Look at those stars.", ["Beautiful. Don't let the wolves sneak up on you, though.", "Makes you forget the war for a moment."]),
    ];

    private static readonly (string Opening, string[] Replies)[] Dawn =
    [
        ("Sun's coming up. Good - I've had enough of the dark.", ["Best time of day for hunting.", "Feels good to see again."]),
        ("Morning already? Where did the night go?", ["Same place they all go.", "Time flies when you're swinging a sword."]),
    ];

    private static readonly (string Opening, string[] Replies)[] Dusk =
    [
        ("Sun's going down. Better finish up before dark.", ["One more pull, then.", "Aye, I'll head in soon."]),
        ("Pretty sunset tonight.", ["Enjoy it. The night's long.", "It is. Rare to stop and notice."]),
    ];

    private static readonly (string Opening, string[] Replies)[] Place =
    [
        ("Quiet around {zone} today.", ["Don't jinx it.", "Enjoy it while it lasts."]),
        ("{zone} is lovely when nothing's trying to eat you.", ["Ha! Which is never.", "True enough."]),
        ("Anyone else think the beasts around {zone} have been bolder lately?", ["Now that you mention it... yes.", "They smell the war."]),
        ("I remember when {zone} was safe to walk at night.", ["Was it ever?", "Times change."]),
    ];

    private static readonly (string Opening, string[] Replies)[] Hunting =
    [
        ("Back to the {monster}, then.", ["Good hunting.", "Save some for me!"]),
        ("These {monster} keep me busy.", ["Watch for adds.", "Better busy than bored."]),
        ("That last {monster} put up a real fight.", ["They're tougher than they look.", "You're still standing, aren't you?"]),
    ];

    private static readonly (string Opening, string[] Replies)[] General =
    [
        ("My pack is getting heavy. Time to see a merchant soon.", ["Sell the junk, keep the coin.", "Mine too."]),
        ("One more level and I can finally train.", ["You'll get there.", "Don't forget your trainer!"]),
        ("Could use a hot meal and a soft bed.", ["Couldn't we all.", "The inn's not far."]),
        ("Anyone heard news from the frontier?", ["Only that it's bloody, as ever.", "The keeps change hands every day."]),
    ];

    /// <summary>Idle talk for a bot standing near you: about the weather where it is, the hour, the place or its
    /// hunting. Null when it has nothing to say.</summary>
    public static Topic IdleTopic(GameBot bot, string monster)
    {
        string zone = bot?.CurrentZone?.Description ?? "these lands";
        var pool = new List<(string, string[])>();
        bool dungeon = bot?.CurrentZone?.IsDungeon == true;
        if (!dungeon && InStorm(bot))
            pool.AddRange(Storm);
        if (!dungeon)
        {
            int hour = GameHour();
            if (hour >= 21 || hour < 5)
                pool.AddRange(Night);
            else if (hour < 8)
                pool.AddRange(Dawn);
            else if (hour >= 18)
                pool.AddRange(Dusk);
        }
        bool weatherOrTime = pool.Count > 0;
        if (!weatherOrTime || Rng.NextDouble() < 0.4)
        {
            pool.AddRange(Place);
            pool.AddRange(General);
            if (!string.IsNullOrWhiteSpace(monster))
                pool.AddRange(Hunting);
        }
        (string open, string[] replies) = pool[Rng.Next(pool.Count)];
        string Fill(string s) => s.Replace("{zone}", zone).Replace("{monster}", string.IsNullOrWhiteSpace(monster) ? "beasts" : monster);
        return new Topic(Fill(open), replies.Select(Fill).ToArray());
    }

    /// <summary>The hour of the game day (0-23).</summary>
    public static int GameHour()
    {
        try { return (int)(WorldMgr.GetCurrentGameTime() / 3_600_000 % 24); }
        catch (Exception) { return 12; }
    }

    /// <summary>The region's storm over this spot (the server's weather - the same the client shows).</summary>
    public static bool InStorm(GameObject o)
    {
        try
        {
            RegionWeather weather = GameServer.Instance?.WorldManager?.WeatherManager?[o.CurrentRegionID];
            if (weather == null || weather.Intensity == 0 || weather.StartTime == 0)
                return false;
            long position = weather.CurrentPosition(Scheduler.SimpleScheduler.Ticks);
            return o.X > position - weather.Width && o.X < position;
        }
        catch (Exception) { return false; }
    }
}
