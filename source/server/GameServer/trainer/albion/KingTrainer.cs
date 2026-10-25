/*
 * Herald of the Crown - trainer for Ryan's custom King / Queen class.
 */
using DOL.GS.PacketHandler;

namespace DOL.GS.Trainer
{
	[NPCGuildScript("King Trainer", eRealm.Albion)]
	public class KingTrainer : GameTrainer
	{
		public override eCharacterClass TrainedClass => eCharacterClass.King;

		public override bool Interact(GamePlayer player)
		{
			if (!base.Interact(player))
				return false;

			if (player.CharacterClass.ID == (int)TrainedClass)
			{
				player.Out.SendMessage(Name + " bows deeply. \"Your Majesty. The Crown's arms are Slash and Parry; " +
					"Fealty binds your sworn retinue, and Majesty carries your royal decrees to all who ride beside you.\"",
					eChatType.CT_Say, eChatLoc.CL_ChatWindow);
				OfferTraining(player);
			}
			else
			{
				player.Out.SendMessage(Name + " says, \"I serve the Crown alone, traveler.\"", eChatType.CT_Say, eChatLoc.CL_ChatWindow);
				CheckChampionTraining(player);
			}

			return true;
		}
	}
}
