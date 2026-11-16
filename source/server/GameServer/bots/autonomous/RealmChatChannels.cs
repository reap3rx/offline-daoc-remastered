using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using DOL.GS.PacketHandler;

namespace DOL.GS;

/// <summary>The two channels that reach beyond earshot (owner 2026-11-16: "Zone, and a realm defense channel where bots
/// and the player can ask for more for RvR activities, should really be the only non local speech bubble
/// communication"):
///   - zone (/zone, /z): your realm in the zone you're in - asking for and answering help with events, quests and hard
///     fights;
///   - realm defense (/rvr, /rd): your realm everywhere - RvR calls to arms, keep and relic alarms, the realm's raids.
/// Everything else is said aloud (/say: a bubble over the speaker's head). Faction chat, /send, /tell, /region and
/// /broadcast are gone: this is a single-player game, and the bots' talk belongs in the world around you.
/// Lines go out as "[Zone] Name: text" / "[RvR] Name: text" (the client sorts them into their own chat types by that
/// tag).</summary>
public static class RealmChatChannels
{
    public enum Channel { Zone, Rvr }

    public const string ZoneTag = "[Zone]";
    public const string RvrTag = "[RvR]";
    public const int MaxLength = 240;

    public static string Tag(Channel channel) => channel == Channel.Zone ? ZoneTag : RvrTag;

    /// <summary>The line as the chat shows it.</summary>
    public static string Format(Channel channel, string speaker, string text)
    {
        string safe = Regex.Replace(text ?? string.Empty, @"\s+", " ").Trim();
        if (safe.Length > MaxLength)
            safe = safe[..MaxLength];
        return $"{Tag(channel)} {speaker}: {safe}";
    }

    /// <summary>The players who hear a zone line: the speaker's realm, in that zone.</summary>
    public static List<GamePlayer> ZoneAudience(eRealm realm, Zone zone)
    {
        if (zone == null)
            return [];
        return ClientService.Instance.GetPlayersOfZone(zone)
            .Where(p => p != null && p.Realm == realm && p.ObjectState == GameObject.eObjectState.Active)
            .ToList();
    }

    public static bool HasZoneAudience(eRealm realm, Zone zone) => ZoneAudience(realm, zone).Count > 0;

    public static bool HasRealmAudience(eRealm realm) => ClientService.Instance.GetPlayersOfRealm(realm).Count > 0;

    public static void SendZone(string speaker, eRealm realm, Zone zone, string text)
    {
        if (string.IsNullOrWhiteSpace(text) || zone == null)
            return;
        string line = Format(Channel.Zone, speaker, text);
        foreach (GamePlayer p in ZoneAudience(realm, zone))
            p.Out.SendMessage(line, eChatType.CT_Broadcast, eChatLoc.CL_ChatWindow);
    }

    public static void SendRvr(string speaker, eRealm realm, string text)
    {
        if (string.IsNullOrWhiteSpace(text) || realm == eRealm.None)
            return;
        string line = Format(Channel.Rvr, speaker, text);
        foreach (GamePlayer p in ClientService.Instance.GetPlayersOfRealm(realm))
            p.Out.SendMessage(line, eChatType.CT_Broadcast, eChatLoc.CL_ChatWindow);
    }

    /// <summary>A bot speaking on a channel (its realm; for zone chat, its zone).</summary>
    public static void Send(GameBot bot, Channel channel, string text)
    {
        if (bot == null)
            return;
        if (channel == Channel.Zone)
            SendZone(bot.Name, bot.Realm, bot.CurrentZone, text);
        else
            SendRvr(bot.Name, bot.Realm, text);
    }

    // ---------------------------------------------------------------- the player's lines

    private const string Tick = "Offline_Realm_Channel_Tick";

    /// <summary>/zone or /rvr typed by the player: shown, then the bots that hear it may answer (AutonomousHelpCalls).
    /// False when it was refused (muted, too fast); the reason was already told.</summary>
    public static bool FromPlayer(GamePlayer player, Channel channel, string message)
    {
        if (player == null || string.IsNullOrWhiteSpace(message))
            return false;
        if (player.IsMuted)
        {
            player.Out.SendMessage("You have been muted.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            return false;
        }
        long last = player.TempProperties.GetProperty<long>(Tick);
        if (last > 0 && GameLoop.GameLoopTime - last < 900)
        {
            player.Out.SendMessage("Slow down! Think before you say each word!", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            return false;
        }
        player.TempProperties.SetProperty(Tick, GameLoop.GameLoopTime);
        message = message.Trim();
        if (channel == Channel.Zone)
        {
            if (player.CurrentZone == null)
                return false;
            SendZone(player.Name, player.Realm, player.CurrentZone, message);
        }
        else
            SendRvr(player.Name, player.Realm, message);
        try { AutonomousHelpCalls.OnPlayerChannel(player, channel, message); }
        catch (Exception e) { log.Error("Realm channel answer failed", e); }
        return true;
    }

    private static readonly DOL.Logging.Logger log = DOL.Logging.LoggerManager.Create(typeof(RealmChatChannels));

    // ---------------------------------------------------------------- places, for the lines

    /// <summary>Where someone is, the way a player would say it in zone chat: the area's name if it has one, and the loc
    /// in thousands ("near Barrow Wakes, loc 24k 31k").</summary>
    public static string PlaceOf(GameObject who)
    {
        if (who?.CurrentZone == null)
            return "around here";
        string area = null;
        try
        {
            area = who.CurrentAreas?.OfType<AbstractArea>()
                .Select(a => a.Description)
                .FirstOrDefault(d => !string.IsNullOrWhiteSpace(d) && !d.Equals(who.CurrentZone.Description, StringComparison.OrdinalIgnoreCase));
        }
        catch (InvalidOperationException) { }                // (the areas changed under this thread)
        int lx = Math.Max(0, (who.X - who.CurrentZone.XOffset) / 1000);
        int ly = Math.Max(0, (who.Y - who.CurrentZone.YOffset) / 1000);
        return string.IsNullOrWhiteSpace(area) ? $"loc {lx}k {ly}k" : $"near {area}, loc {lx}k {ly}k";
    }
}
