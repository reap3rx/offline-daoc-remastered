/*
 * /ac - Action Combat (see gameobjects/ActionCombat/ActionCombat.cs). The Godot client sends these from its
 * mouse and keys; they can also be typed.
 */
using DOL.GS.PacketHandler;

namespace DOL.GS.Commands
{
	[CmdAttribute(
		"&ac",
		ePrivLevel.Player,
		"Action combat: click-to-swing melee with timed parry, block and dodge",
		"/ac on | off | toggle | info",
		"/ac swing | style <anytime|position|reactive|chain>",
		"/ac parry | guard <on|off> | dodge")]
	public class ActionCombatCommandHandler : AbstractCommandHandler, ICommandHandler
	{
		public void OnCommand(GameClient client, string[] args)
		{
			GamePlayer player = client?.Player;

			if (player == null)
				return;

			string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "info";
			ActionCombatState state = ActionCombat.Get(player);

			switch (sub)
			{
				case "query":
					ActionCombat.Send(player, "mode|" + (state.Enabled ? "1" : "0"));
					return;
				case "on":
				case "off":
				case "toggle":
				{
					bool on = sub == "on" || (sub == "toggle" && !state.Enabled);
					ActionCombat.SetEnabled(player, on);
					player.Out.SendMessage(on
						? "Action combat ON: click to swing, hold for an anytime style; Position / Reactive / Chain buttons; right mouse to parry (hold to guard); double-tap a direction to dodge."
						: "Action combat OFF: classic auto-attack.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
					return;
				}
				case "info":
					player.Out.SendMessage(ActionCombat.Describe(player), eChatType.CT_System, eChatLoc.CL_SystemWindow);
					return;
				case "quiver":                       // (the quiver window works in classic mode too)
					ActionCombat.SelectQuiver(player, args.Length > 2 ? args[2].ToLowerInvariant() : "next");
					return;
			}

			if (!state.Enabled)
				return;                  // the client's buttons do nothing in classic mode

			switch (sub)
			{
				case "swing":
					ActionCombat.QueueSwing(player);
					break;
				case "style":
					if (args.Length > 2)
						ActionCombat.QueueStyle(player, args[2].ToLowerInvariant());
					break;
				case "parry":
					ActionCombat.PressParry(player);
					break;
				case "guard":
					ActionCombat.SetGuard(player, args.Length > 2 && args[2].ToLowerInvariant() == "on");
					break;
				case "dodge":
					ActionCombat.PressDodge(player);
					break;
				case "draw":
					ActionCombat.StartDraw(player, args.Length > 2 && args[2].ToLowerInvariant() == "crit");
					break;
				case "loose":
					ActionCombat.Loose(player);
					break;
				case "cancel":
					ActionCombat.CancelDraw(player, null);
					break;
				default:
					DisplaySyntax(client);
					break;
			}
		}
	}
}
