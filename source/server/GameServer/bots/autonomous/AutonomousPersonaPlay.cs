using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.GS.PacketHandler;
using OfflineDaoc.Population;

namespace DOL.GS;

/// <summary>
/// The persona in play with you (owner 2026-11-11, "Living Bot Population - Plan" step 3, "Groups and invites"), said
/// aloud (owner 2026-11-16: "Bots should now also request the player or other bots to group with them by asking in chat
/// first before just opening a group invite. The player can reply in chat with a yes, and then they'll invite you, or
/// the player can invite them" - no whispers: "all local communication be done in the say channel so the chat bubbles
/// are over their head"):
///   - a bot answers your invitation by its Social trait: a grouper almost always comes, an either-way player usually
///     (less near its log-off time or mid-task), a soloer rarely - and says so aloud when it's near you;
///   - a grouper may ask you to group: it walks over and asks aloud ("Hey Fiona, want to group up?"). Answer in /say -
///     "yes", "yes please", "sure", "ok" ... or "no", "no thank you", "nah", "I'm good" ... (any case) - and on a yes it
///     sends you the invitation; or just invite it yourself. The question stands for 30 seconds; after a no (or no
///     answer) nobody asks you again for 10 minutes, and between offers there are 10 to 15 minutes, never while you
///     are in a full group.
/// Temporary helpers, companions and bots without a persona keep the old rule (they always come).
/// </summary>
public static class AutonomousPersonaPlay
{
    public const int OfferRange = 1600;                           // how near a grouper has to be to think of asking (units)
    public const int AskDistance = 230;                           // it walks this near before asking
    public const int AnswerWindowMs = 30_000;                     // the question stands this long
    public const int ApproachLimitMs = 45_000;
    public static readonly TimeSpan OfferGapMin = TimeSpan.FromMinutes(10);
    public static readonly TimeSpan OfferGapMax = TimeSpan.FromMinutes(15);
    public static readonly TimeSpan NoAgainFor = TimeSpan.FromMinutes(10);
    public static readonly TimeSpan AskAgainWindow = TimeSpan.FromMinutes(4);

    public enum Answer { None, Yes, No }

    private sealed class Offer
    {
        public GameBot Bot;
        public GamePlayer Player;
        public long Started;
        public long Asked;                                         // 0 while it walks over
        public long NextPath;
    }

    private static readonly ConcurrentDictionary<string, DateTime> NextOffer = new(StringComparer.OrdinalIgnoreCase);
    private static readonly ConcurrentDictionary<(long Bot, string Player), DateTime> Refused = new();
    private static readonly ConcurrentDictionary<(long Bot, string Player), DateTime> Offered = new();
    private static readonly ConcurrentDictionary<(long Bot, string Player), DateTime> Agreed = new();
    private static readonly ConcurrentDictionary<string, Offer> Offers = new(StringComparer.OrdinalIgnoreCase);
    private static readonly ConcurrentDictionary<long, string> OfferBy = new();          // bot id -> player it is asking
    private static readonly Random Rng = new();
    private static readonly DOL.Logging.Logger Log = DOL.Logging.LoggerManager.Create(typeof(AutonomousPersonaPlay));

    private static readonly string[] Accepts =
    [
        "Gladly. Lead on.", "I would be glad of the company.", "Aye, count me in.", "With pleasure, friend.",
        "Good, I was hoping someone would ask.", "Very well, I am with you.",
    ];

    private static readonly string[] SoloDeclines =
    [
        "Kind of you, but I hunt alone tonight.", "My thanks, but I keep my own counsel on the road.",
        "Another time, perhaps. I travel lighter on my own.", "I am grateful, but I mean to see this through alone.",
    ];

    private static readonly string[] LateDeclines =
    [
        "I would, but I must away soon. Another night, friend.", "The hour grows late for me. Ask me again tomorrow.",
        "I am near the end of my road tonight, sadly.",
    ];

    private static readonly string[] BusyDeclines =
    [
        "Not just now, I have a task to finish. Perhaps later.", "I am in the middle of something. Ask me again in a while.",
        "Let me finish what I started first, friend.",
    ];

    private static readonly string[] AskedAgain =
    [
        "Well, since you ask so kindly a second time... very well.", "You are persistent. All right, I will come along.",
    ];

    private static readonly string[] Asks =
    [
        "Hey {name}, care to join me? I could use the company.", "{name}! Want to group up? Two blades are better than one out here.",
        "You hunting these parts too, {name}? Want to team up?", "Fancy some company, {name}? We could group.",
        "Hail, {name}. Looking for a group? I'd be glad to join you.",
    ];

    private static readonly string[] YesReplies =
    [
        "Great! I'll send you an invite.", "Wonderful - inviting you now.", "Excellent. Here's the invite.",
    ];

    private static readonly string[] NoReplies =
    [
        "No worries. Good hunting!", "Fair enough. Safe travels, {name}.", "Another time, then!",
    ];

    private static readonly string[] Lapsed =
    [
        "Guess not. Good hunting, {name}!", "No answer? Fair enough. Safe travels.", "Busy, I see. Another time!",
    ];

    private static readonly string[] AfterInvitedDirectly =
    [
        "Perfect, thanks!", "Ha, you beat me to it. Lead on!", "Even better. Let's go.",
    ];

    // ---------------------------------------------------------------- yes and no (unit tested)

    private static readonly HashSet<string> YesPhrases =
    [
        "yes", "yes please", "yeah", "yea", "yep", "yup", "ya", "yah", "sure", "sure thing", "ok", "okay", "k", "kk",
        "alright", "all right", "aye", "of course", "absolutely", "definitely", "certainly", "gladly", "sounds good",
        "why not", "sure why not", "lets go", "let's go", "lets do it", "let's do it", "please", "please do", "y",
        "yes thanks", "yes thank you", "love to", "i'd love to", "id love to", "would love to", "count me in", "im in",
        "i'm in", "go ahead", "invite me", "inv", "inv me", "invite", "yes sure", "ok sure", "okay sure", "sure thanks",
        "sure thank you", "sounds great", "yes let's", "yes lets", "ok thanks", "okay thanks",
    ];

    private static readonly HashSet<string> NoPhrases =
    [
        "no", "no thanks", "no thank you", "nope", "nah", "no thx", "no ty", "n", "not now", "not right now", "maybe later",
        "later", "pass", "i'll pass", "ill pass", "i'm good", "im good", "i'm fine", "im fine", "no way", "not today",
        "not interested", "no sorry", "sorry no", "i'm ok", "im ok", "i'm okay", "im okay", "no i'm good", "no im good",
        "i prefer solo", "i'm solo", "im solo", "nah thanks", "nah i'm good", "nah im good", "no thanks though",
        "thanks but no", "thanks but no thanks", "no thank you though", "not this time", "another time",
    ];

    private static readonly HashSet<string> YesFirstWords =
        ["yes", "yeah", "yea", "yep", "yup", "sure", "ok", "okay", "alright", "aye", "absolutely", "definitely", "certainly", "gladly", "ya", "yah"];

    private static readonly HashSet<string> NoWords = ["no", "nope", "nah"];

    public static string Normalize(string text)
    {
        if (string.IsNullOrWhiteSpace(text))
            return string.Empty;
        var chars = text.ToLowerInvariant().Select(c => char.IsLetterOrDigit(c) || c == '\'' ? c : ' ').ToArray();
        return string.Join(' ', new string(chars).Split(' ', StringSplitOptions.RemoveEmptyEntries));
    }

    /// <summary>A yes or a no to "want to group?", in the words people use (any case, punctuation ignored): "yes",
    /// "yes please", "sure", "ok" ... "no", "no thank you", "nah", "I'm good" ...; a name after it is fine ("yes Bob").</summary>
    public static Answer ParseAnswer(string text, string botName = null)
    {
        string t = Normalize(text);
        if (t.Length == 0)
            return Answer.None;
        if (!string.IsNullOrWhiteSpace(botName))
        {
            string n = Normalize(botName);
            if (t.EndsWith(" " + n))
                t = t[..^(n.Length + 1)];
            else if (t.StartsWith(n + " "))
                t = t[(n.Length + 1)..];
        }
        if (NoPhrases.Contains(t))
            return Answer.No;
        if (YesPhrases.Contains(t))
            return Answer.Yes;
        string[] words = t.Split(' ');
        if (NoWords.Contains(words[0]))
            return Answer.No;
        if (YesFirstWords.Contains(words[0]) && !words.Skip(1).Any(NoWords.Contains))
            return Answer.Yes;
        if (words.Length <= 4 && words.Any(NoWords.Contains))
            return Answer.No;
        return Answer.None;
    }

    // ---------------------------------------------------------------- your invitation

    public static BotPersona PersonaFor(GameBot bot) =>
        bot?.IsAutonomousWorldBot == true && !bot.IsTemporaryGroupHelper && bot.PersistentRecord != null
            ? AutonomousPopulationController.PersonaOf(bot.PersistentRecord) : null;

    /// <summary>Whether `bot` takes `player`'s invitation; when it doesn't, it has already told the player why.</summary>
    public static bool AnswerInvite(GamePlayer player, GameBot bot)
    {
        BotPersona persona = PersonaFor(bot);
        if (persona == null || player == null)
            return true;
        var key = (bot.DatabaseID, player.Name);
        if (Agreed.TryRemove(key, out _))
            return true;                                         // it asked you, you said yes: it already said so
        bool askedAgain = Refused.TryGetValue(key, out DateTime refusedUtc) && DateTime.UtcNow - refusedUtc < AskAgainWindow;
        if (Offered.TryRemove(key, out DateTime offeredUtc) && DateTime.UtcNow - offeredUtc < TimeSpan.FromMinutes(10))
        {
            EndOffer(bot);
            return Say(player, bot, AfterInvitedDirectly, true);  // it asked you first: you invited it instead
        }
        double minutesLeft = AutonomousPopulationController.MinutesLeftInSession(bot);
        if (persona.AcceptsInvite(Rng, minutesLeft, askedAgain))
        {
            Refused.TryRemove(key, out _);
            EndOffer(bot);
            return Say(player, bot, askedAgain && persona.SocialKind != "group" ? AskedAgain : Accepts, true);
        }
        Refused[key] = DateTime.UtcNow;
        string[] lines = minutesLeft < 10 ? LateDeclines : persona.SocialKind == "solo" ? SoloDeclines : BusyDeclines;
        return Say(player, bot, lines, false);
    }

    /// <summary>Aloud when it's near you; from afar a refusal is only a line in your system window.</summary>
    private static bool Say(GamePlayer player, GameBot bot, string[] lines, bool result)
    {
        string line = lines[Rng.Next(lines.Length)].Replace("{name}", player.Name);
        if (bot.CurrentRegionID == player.CurrentRegionID && bot.IsWithinRadius(player, WorldMgr.SAY_DISTANCE))
            bot.Say(line);
        else if (!result)
            player.Out.SendMessage($"{bot.Name} declines your invitation.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
        return result;
    }

    // ---------------------------------------------------------------- its asking you

    /// <summary>On the game loop, now and then: a grouper near an ungrouped player may come and ask.</summary>
    public static void TickOffers()
    {
        DateTime now = DateTime.UtcNow;
        GameBot[] bots = null;
        foreach (eRealm realm in new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia })
        {
            foreach (GamePlayer player in ClientService.Instance.GetPlayersOfRealm(realm))
            {
                if (player == null || player.Group != null || !player.IsAlive || player.InCombat ||
                    player.ObjectState != GameObject.eObjectState.Active || player.CurrentRegion == null ||
                    Offers.ContainsKey(player.Name))
                    continue;
                if (NextOffer.TryGetValue(player.Name, out DateTime next) && now < next)
                    continue;
                bots ??= AutonomousBotRegistry.Snapshot();
                GameBot offerer = bots
                    .Where(b => b.Realm == player.Realm && b.Group == null && b.IsAlive && !b.InCombat && !b.IsCasting &&
                                b.ObjectState == GameObject.eObjectState.Active && b.CurrentRegion == player.CurrentRegion &&
                                b.IsWithinRadius(player, OfferRange) && Math.Abs(b.Level - player.Level) <= 4 &&
                                !b.IsOnHorse && !b.IsOnStableMasterRoute && !OfferBy.ContainsKey(b.DatabaseID) &&
                                !(Refused.TryGetValue((b.DatabaseID, player.Name), out DateTime r) && now - r < NoAgainFor) &&
                                AutonomousHelpCalls.AssignmentOf(b) == null &&
                                PersonaFor(b)?.InvitesPlayers() == true &&
                                AutonomousPopulationController.MinutesLeftInSession(b) > 20)
                    .OrderBy(b => b.GetDistanceTo(player))
                    .FirstOrDefault();
                if (offerer == null)
                    continue;
                // one offer, then a good while before the next (from any bot): 10 to 15 minutes
                NextOffer[player.Name] = now + OfferGapMin + TimeSpan.FromSeconds(Rng.Next((int)(OfferGapMax - OfferGapMin).TotalSeconds));
                BeginOffer(player, offerer, approached: false);
            }
        }
    }

    /// <summary>`bot` sets out to ask `player` (approached: it is already beside them - a zone-chat "lfg" it answered).</summary>
    public static void BeginOffer(GamePlayer player, GameBot bot, bool approached, bool answeringCall = false)
    {
        if (player == null || bot == null)
            return;
        if (answeringCall)
            NextOffer[player.Name] = DateTime.UtcNow + OfferGapMin;
        var offer = new Offer { Bot = bot, Player = player, Started = GameLoop.GameLoopTime };
        if (Offers.TryGetValue(player.Name, out Offer old) && old.Bot != bot)
            OfferBy.TryRemove(old.Bot.DatabaseID, out _);
        Offers[player.Name] = offer;
        OfferBy[bot.DatabaseID] = player.Name;
    }

    /// <summary>Whether this bot is on its way to ask someone, or waiting for their answer.</summary>
    public static bool IsOffering(GameBot bot) => bot != null && OfferBy.ContainsKey(bot.DatabaseID);

    private static void EndOffer(GameBot bot)
    {
        if (bot != null && OfferBy.TryRemove(bot.DatabaseID, out string name) &&
            Offers.TryGetValue(name, out Offer o) && o.Bot == bot)
            Offers.TryRemove(name, out _);
    }

    private static void Decline(GameBot bot, GamePlayer player)
    {
        Refused[(bot.DatabaseID, player.Name)] = DateTime.UtcNow;
        Offered.TryRemove((bot.DatabaseID, player.Name), out _);
        DateTime quiet = DateTime.UtcNow + NoAgainFor;          // (nobody else asks you in the next 10 minutes either)
        if (!NextOffer.TryGetValue(player.Name, out DateTime next) || next < quiet)
            NextOffer[player.Name] = quiet;
    }

    /// <summary>The controller asks this each turn out of combat: true while the bot is walking over to ask you or
    /// waiting for your answer (it owns the bot's movement).</summary>
    public static bool Hold(GameBot bot)
    {
        if (bot == null || !OfferBy.TryGetValue(bot.DatabaseID, out string name) || !Offers.TryGetValue(name, out Offer o) ||
            o.Bot != bot)
            return false;
        GamePlayer p = o.Player;
        long now = GameLoop.GameLoopTime;
        if (bot.InCombat || bot.Group != null || !bot.IsAlive || p == null || !p.IsAlive ||
            p.ObjectState != GameObject.eObjectState.Active || p.CurrentRegionID != bot.CurrentRegionID ||
            p.Group != null && (p.Group.IsInTheGroup(bot) || p.Group.MemberCount >= ServerProperties.Properties.GROUP_MAX_MEMBER))
        {
            EndOffer(bot);
            return false;
        }
        double distance = bot.GetDistanceTo(p);
        if (o.Asked == 0)
        {
            if (distance > AskDistance)
            {
                if (distance > 3000 || now - o.Started > ApproachLimitMs)
                {
                    EndOffer(bot);
                    return false;
                }
                if (now >= o.NextPath || !bot.IsMoving)
                {
                    bot.PathTo(new Vector3(p.X, p.Y, p.Z), bot.MaxSpeed);
                    o.NextPath = now + 2_000;
                }
                Status(bot, $"Walking over to {p.Name}", $"Going to ask {p.Name} to group");
                return true;
            }
            bot.StopMovingOnPath();
            bot.StopMoving();
            bot.TurnTo(p);
            bot.Say(Asks[Rng.Next(Asks.Length)].Replace("{name}", p.Name));
            o.Asked = now;
            Offered[(bot.DatabaseID, p.Name)] = DateTime.UtcNow;
            Log.Info($"GROUP_ASK bot={bot.Name} player={p.Name}");
            Status(bot, $"Asked {p.Name} to group", "Waiting for an answer");
            return true;
        }
        if (now - o.Asked > AnswerWindowMs || distance > 1200)
        {
            if (distance <= WorldMgr.SAY_DISTANCE)
                bot.Say(Lapsed[Rng.Next(Lapsed.Length)].Replace("{name}", p.Name));
            Decline(bot, p);
            EndOffer(bot);
            return false;
        }
        if (bot.IsMoving)
        {
            bot.StopMovingOnPath();
            bot.StopMoving();
        }
        if ((now - o.Asked) % 4_000 < 600)
            bot.TurnTo(p);
        return true;
    }

    /// <summary>Your words aloud near a bot that asked you: a yes or a no ends the question. True when it was one.</summary>
    public static bool OnPlayerSaid(GamePlayer player, string text)
    {
        if (player == null || !Offers.TryGetValue(player.Name, out Offer o) || o.Asked == 0)
            return false;
        GameBot bot = o.Bot;
        if (bot == null || !bot.IsAlive || bot.CurrentRegionID != player.CurrentRegionID ||
            !bot.IsWithinRadius(player, WorldMgr.SAY_DISTANCE + 200))
            return false;
        Answer answer = ParseAnswer(text, bot.Name);
        if (answer == Answer.None)
            return false;
        EndOffer(bot);
        if (answer == Answer.No)
        {
            Decline(bot, player);
            AutonomousHelpCalls.Later(bot, 900, () => bot.Say(NoReplies[Rng.Next(NoReplies.Length)].Replace("{name}", player.Name)));
            return true;
        }
        Offered.TryRemove((bot.DatabaseID, player.Name), out _);
        AutonomousHelpCalls.Later(bot, 900, () => bot.Say(YesReplies[Rng.Next(YesReplies.Length)]));
        AutonomousHelpCalls.Later(bot, 2_200, () => SendInvite(player, bot));
        return true;
    }

    /// <summary>Its invitation: your dialog; accepting it puts it in your group (you lead - the group your bots follow).</summary>
    private static void SendInvite(GamePlayer player, GameBot bot)
    {
        if (player.ObjectState != GameObject.eObjectState.Active || !bot.IsAlive || bot.ObjectState != GameObject.eObjectState.Active)
            return;
        player.Out.SendCustomDialog($"{bot.Name} invites you to join a group. Do you accept?", (p, response) =>
        {
            if (response != 0x01)
            {
                Decline(bot, p);
                if (bot.IsAlive && bot.IsWithinRadius(p, WorldMgr.SAY_DISTANCE))
                    bot.Say("Oh. Another time, then.");
                return;
            }
            if (bot.ObjectState != GameObject.eObjectState.Active || !bot.IsAlive)
                return;
            Agreed[(bot.DatabaseID, p.Name)] = DateTime.UtcNow;
            BotGroupInvite.TryInvite(p, bot);
        });
    }

    private static void Status(GameBot bot, string activity, string progress)
    {
        if (bot.PersistentRecord == null || bot.PersistentRecord.Activity == activity)
            return;
        bot.PersistentRecord.Activity = activity;
        bot.PersistentRecord.ObjectiveProgress = progress;
        bot.MarkAutonomousStateDirty();
    }
}
