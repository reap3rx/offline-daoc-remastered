using System;
using System.Collections.Concurrent;
using System.Linq;
using DOL.GS.PacketHandler;
using OfflineDaoc.Population;

namespace DOL.GS;

/// <summary>
/// The persona in play with you (owner 2026-11-11, "Living Bot Population - Plan" step 3, "Groups and invites"):
///   - a bot answers your invitation by its Social trait: a grouper almost always comes, an either-way player usually
///     (less near its log-off time or mid-task), a soloer rarely - and always says so in character, never silence;
///   - a grouper may offer you a group unasked: one whisper and an invitation you can accept or decline, at most one
///     such offer every 20 to 30 minutes across all bots, and never while you are already in a group.
/// Temporary helpers, companions and bots without a persona keep the old rule (they always come).
/// </summary>
public static class AutonomousPersonaPlay
{
    public const int OfferRange = 1600;                           // how near a grouper has to be to offer (units)
    public static readonly TimeSpan OfferGapMin = TimeSpan.FromMinutes(20);
    public static readonly TimeSpan OfferGapMax = TimeSpan.FromMinutes(30);
    public static readonly TimeSpan AskAgainWindow = TimeSpan.FromMinutes(4);

    private static readonly ConcurrentDictionary<string, DateTime> NextOffer = new(StringComparer.OrdinalIgnoreCase);
    private static readonly ConcurrentDictionary<(long Bot, string Player), DateTime> Refused = new();
    private static readonly ConcurrentDictionary<(long Bot, string Player), DateTime> Offered = new();
    private static readonly Random Rng = new();

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

    private static readonly string[] Offers =
    [
        "You look to be hunting these parts too. Care to join me?", "Fancy some company? I could use a sword arm.",
        "Two blades are better than one out here. Shall we hunt together?", "I am looking for companions. Will you join me?",
    ];

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
        bool askedAgain = Refused.TryGetValue(key, out DateTime refusedUtc) && DateTime.UtcNow - refusedUtc < AskAgainWindow;
        if (Offered.TryRemove(key, out DateTime offeredUtc) && DateTime.UtcNow - offeredUtc < TimeSpan.FromMinutes(10))
            return Say(player, bot, Accepts, true);              // it asked you first
        double minutesLeft = AutonomousPopulationController.MinutesLeftInSession(bot);
        if (persona.AcceptsInvite(Rng, minutesLeft, askedAgain))
        {
            Refused.TryRemove(key, out _);
            return Say(player, bot, askedAgain && persona.SocialKind != "group" ? AskedAgain : Accepts, true);
        }
        Refused[key] = DateTime.UtcNow;
        string[] lines = minutesLeft < 10 ? LateDeclines : persona.SocialKind == "solo" ? SoloDeclines : BusyDeclines;
        return Say(player, bot, lines, false);
    }

    private static bool Say(GamePlayer player, GameBot bot, string[] lines, bool result)
    {
        Whisper(player, bot, lines[Rng.Next(lines.Length)]);
        return result;
    }

    public static void Whisper(GamePlayer player, GameBot bot, string text) =>
        player?.Out.SendMessage($"{bot.Name} sends, \"{text}\"", eChatType.CT_Send, eChatLoc.CL_ChatWindow);

    /// <summary>On the game loop, now and then: a grouper near an ungrouped player may offer a group.</summary>
    public static void TickOffers()
    {
        DateTime now = DateTime.UtcNow;
        GameBot[] bots = null;
        foreach (eRealm realm in new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia })
        {
            foreach (GamePlayer player in ClientService.Instance.GetPlayersOfRealm(realm))
            {
                if (player == null || player.Group != null || !player.IsAlive || player.InCombat ||
                    player.ObjectState != GameObject.eObjectState.Active || player.CurrentRegion == null)
                    continue;
                if (NextOffer.TryGetValue(player.Name, out DateTime next) && now < next)
                    continue;
                bots ??= AutonomousBotRegistry.Snapshot();
                GameBot offerer = bots
                    .Where(b => b.Realm == player.Realm && b.Group == null && b.IsAlive && !b.InCombat && !b.IsCasting &&
                                b.ObjectState == GameObject.eObjectState.Active && b.CurrentRegion == player.CurrentRegion &&
                                b.IsWithinRadius(player, OfferRange) && Math.Abs(b.Level - player.Level) <= 4 &&
                                !b.IsOnHorse && !b.IsOnStableMasterRoute &&
                                PersonaFor(b)?.InvitesPlayers() == true &&
                                AutonomousPopulationController.MinutesLeftInSession(b) > 20)
                    .OrderBy(b => b.GetDistanceTo(player))
                    .FirstOrDefault();
                if (offerer == null)
                    continue;
                // one offer, then a good while before the next (from any bot): 20 to 30 minutes
                NextOffer[player.Name] = now + OfferGapMin + TimeSpan.FromSeconds(Rng.Next((int)(OfferGapMax - OfferGapMin).TotalSeconds));
                Offer(player, offerer);
            }
        }
    }

    private static void Offer(GamePlayer player, GameBot bot)
    {
        Offered[(bot.DatabaseID, player.Name)] = DateTime.UtcNow;
        Whisper(player, bot, Offers[Rng.Next(Offers.Length)]);
        player.Out.SendCustomDialog($"{bot.Name} invites you to join a group. Do you accept?", (p, response) =>
        {
            if (response != 0x01)
            {
                Offered.TryRemove((bot.DatabaseID, p.Name), out _);
                Whisper(p, bot, "No matter. Good hunting to you.");
                return;
            }
            // you lead (the group your bots follow): the offerer joins you
            if (bot.ObjectState != GameObject.eObjectState.Active || !bot.IsAlive)
                return;
            BotGroupInvite.TryInvite(p, bot);
        });
    }
}
