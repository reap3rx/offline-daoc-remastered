/*
 * /druidform - the form of a Druid's nature spirit (HibernianKits): bear, wolf or wisp; "next" goes round them (the pet
 * window's FORM button).
 */
using System;
using DOL.GS.PacketHandler;

namespace DOL.GS.Commands
{
	[CmdAttribute(
		"&druidform",
		ePrivLevel.Player,
		"Your nature spirit's form",
		"/druidform bear | wolf | wisp | next")]
	public class DruidFormCommandHandler : AbstractCommandHandler, ICommandHandler
	{
		public void OnCommand(GameClient client, string[] args)
		{
			GamePlayer player = client?.Player;
			if (player == null)
				return;
			if (HibernianKits.ClassOf(player) != HibernianKits.Druid)
			{
				player.Out.SendMessage("Only a Druid's nature spirit changes its form.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}
			string want = args.Length > 1 ? args[1].ToLowerInvariant() : "next";
			HibernianKits.Form f;
			if (want == "next")
				f = (HibernianKits.Form) (((int) HibernianKits.FormOf(player) + 1) % 3);
			else if (!Enum.TryParse(want, true, out f))
			{
				DisplaySyntax(client);
				return;
			}
			HibernianKits.SetForm(player, f);
		}
	}
}
