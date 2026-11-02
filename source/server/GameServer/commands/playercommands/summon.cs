using System;
using DOL.Database;
using DOL.GS.PacketHandler;

namespace DOL.GS.Commands
{
	[CmdAttribute("&summon", new string[] { "&mount" }, ePrivLevel.Player, "Summon your horse (or get off it)", "/summon", "/mount")]
	public class SummonHorseCommandHandler : AbstractCommandHandler, ICommandHandler
	{
		public void OnCommand(GameClient client, string[] args)
		{
			GamePlayer player = client.Player;
			if (player == null)
				return;
			try
			{
				if (args.Length > 1 && Convert.ToInt16(args[1]) == 0)
				{
					player.IsOnHorse = false;
					return;
				}
			}
			catch
			{
				DisplayMessage(client, "Incorrect format of the command");
				return;
			}

			// mounts' first pass (owner 2026-11-02): a horse bought from a horse dealer lies in the backpack and the new
			// client has no Horse slot to drag it to - the best one you can ride goes there now
			if (player.Inventory.GetItem(eInventorySlot.Horse) == null && !player.IsOnHorse)
				EquipBestHorse(player);

			if (player.Inventory.GetItem(eInventorySlot.Horse) != null)
				player.UseSlot(eInventorySlot.Horse, eUseType.Click);
			else
				DisplayMessage(client, "You have no horse. Horse dealers stand beside the stable masters.");
		}

		private static void EquipBestHorse(GamePlayer player)
		{
			DbInventoryItem best = null;
			for (eInventorySlot s = eInventorySlot.FirstBackpack; s <= eInventorySlot.LastBackpack; s++)
			{
				DbInventoryItem it = player.Inventory.GetItem(s);
				if (it == null || it.Item_Type != (int)eInventorySlot.Horse || it.Level > player.Level)
					continue;
				if (best == null || it.Level > best.Level)
					best = it;
			}
			if (best != null)
				player.Inventory.MoveItem((eInventorySlot)best.SlotPosition, eInventorySlot.Horse, 1);
		}
	}
}
