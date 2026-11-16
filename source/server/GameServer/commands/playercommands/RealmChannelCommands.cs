using System;
using System.Linq;
using DOL.GS.PacketHandler;

namespace DOL.GS.Commands;

/// <summary>/zone (/z): talk to your realm in this zone - ask for help with an event, a quest or a hard fight, or look
/// for a group; bots that hear it and can help answer and come (owner 2026-11-16). A GM's /zone info, divingflag,
/// waterlevel and bonus are still the zone tools (/gmzone).</summary>
[CmdAttribute("&zone", new string[] { "&z" }, ePrivLevel.Player,
    "Talk to your realm in this zone: ask for help with events, quests and hard fights, or look for a group",
    "/zone <message> (or /z <message>)")]
public sealed class ZoneChatCommand : AbstractCommandHandler, ICommandHandler
{
    private static readonly string[] GmWords = ["info", "divingflag", "waterlevel", "bonus"];

    public void OnCommand(GameClient client, string[] args)
    {
        if (client?.Player == null)
            return;
        if (args.Length >= 2 && client.Account.PrivLevel > (uint)ePrivLevel.Player &&
            GmWords.Contains(args[1].ToLowerInvariant()))
        {
            new ZoneCommandHandler().OnCommand(client, args);
            return;
        }
        if (args.Length < 2)
        {
            client.Out.SendMessage("Usage: /zone <message> - your realm in this zone hears it (ask for help, or for a group).",
                eChatType.CT_System, eChatLoc.CL_SystemWindow);
            return;
        }
        RealmChatChannels.FromPlayer(client.Player, RealmChatChannels.Channel.Zone, string.Join(" ", args, 1, args.Length - 1));
    }
}

/// <summary>/rvr (/rd): realm defense - your whole realm hears it: calls to arms, keeps and relics under attack, help in
/// the frontier (owner 2026-11-16).</summary>
[CmdAttribute("&rvr", new string[] { "&rd" }, ePrivLevel.Player,
    "Realm defense: call your realm to arms or for help in the frontier",
    "/rvr <message> (or /rd <message>)")]
public sealed class RealmDefenseChatCommand : AbstractCommandHandler, ICommandHandler
{
    public void OnCommand(GameClient client, string[] args)
    {
        if (client?.Player == null)
            return;
        if (args.Length < 2)
        {
            client.Out.SendMessage("Usage: /rvr <message> - realm defense: your whole realm hears it.",
                eChatType.CT_System, eChatLoc.CL_SystemWindow);
            return;
        }
        RealmChatChannels.FromPlayer(client.Player, RealmChatChannels.Channel.Rvr, string.Join(" ", args, 1, args.Length - 1));
    }
}
