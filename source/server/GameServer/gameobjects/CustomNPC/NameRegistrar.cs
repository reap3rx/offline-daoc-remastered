/* 01/03/2005
   Written by Gavinius */

using System;
using System.Collections;
using DOL;
using DOL.Database;
using DOL.GS;
using DOL.GS.Commands;
using DOL.GS.PacketHandler;
using DOL.Language;

namespace DOL.GS
{
	[NPCGuildScript("Name Registrar")]
	public class NameRegistrar : GameNPC
	{
		public override IList GetExamineMessages(GamePlayer player)
		{
			IList list = new ArrayList(2);
            list.Add(LanguageMgr.GetTranslation(player.Client.Account.Language, "NameRegistrar.YouExamine", GetName(0, false), GetPronoun(0, true), GetAggroLevelString(player, false)));
            return list;
		}

		public override bool Interact(GamePlayer player)
		{
			if(base.Interact(player))
			{
				/* Get primary crafting skill (if any) */
				int CraftSkill = 0;
				if (player.CraftingPrimarySkill != eCraftingSkill.NoCrafting)
					CraftSkill = player.GetCraftingSkillValue(player.CraftingPrimarySkill);

				/* Check if level and/or crafting skill let you have a lastname */
				if (player.Level < LastnameCommandHandler.LASTNAME_MIN_LEVEL && CraftSkill < LastnameCommandHandler.LASTNAME_MIN_CRAFTSKILL)
					SayTo(player, eChatLoc.CL_SystemWindow, LanguageMgr.GetTranslation(player.Client.Account.Language, "NameRegistrar.ReturnToMe", LastnameCommandHandler.LASTNAME_MIN_LEVEL));
				else
                    SayTo(player, eChatLoc.CL_SystemWindow, LanguageMgr.GetTranslation(player.Client.Account.Language, "NameRegistrar.LastName"));
                // a companion's new name is written here too (owner 2026-11-11)
                if (PersonalCompanions.Load(player) is PersonalCompanions.Record companion)
                    SayTo(player, eChatLoc.CL_SystemWindow, $"Your companion, {companion.Name}, may take a new name in my book as well: /companion rename <name>.");
                return true;
			}
			return false;
		}

	}
}

