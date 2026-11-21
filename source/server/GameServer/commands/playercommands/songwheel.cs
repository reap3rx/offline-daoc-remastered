/*
 * /songwheel - the Bard's Song Wheel (HibernianKits). The Godot client asks for the songs to put on the wheel
 * ("/songwheel list" -> "#SNG|name;name;..."); "/songwheel" alone plays the song that fits the moment (the tap).
 */
namespace DOL.GS.Commands
{
	[CmdAttribute(
		"&songwheel",
		ePrivLevel.Player,
		"The Song Wheel: the song that fits now, or the list of your songs",
		"/songwheel | list")]
	public class SongWheelCommandHandler : AbstractCommandHandler, ICommandHandler
	{
		public void OnCommand(GameClient client, string[] args)
		{
			GamePlayer player = client?.Player;
			if (player == null)
				return;
			if (args.Length > 1 && args[1].ToLowerInvariant() == "list")
				HibernianKits.SendSongs(player);
			else if (player.IsAlive)
				HibernianKits.UseWheel(player);
		}
	}
}
