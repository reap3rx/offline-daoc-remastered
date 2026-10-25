/*
 * Fealty: Dismiss Troops - the King / Queen's commander sends away every retainer under its command,
 * so new ones can be called without dismissing (and re-buffing) the commander itself.
 */
using System.Collections.Generic;
using System.Linq;
using DOL.AI.Brain;
using DOL.GS.PacketHandler;

namespace DOL.GS.Spells
{
	[SpellHandler(eSpellType.DismissRetainers)]
	public class DismissRetainers : SpellHandler
	{
		public DismissRetainers(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

		public override bool HasPositiveEffect => true;

		private CommanderPet Commander => Caster?.ControlledBrain?.Body as CommanderPet;

		private static List<IControlledBrain> Retainers(CommanderPet commander)
		{
			lock (commander.ControlledNpcListLock)
				return commander.ControlledNpcList?.Where(brain => brain?.Body != null).ToList() ?? [];
		}

		public override bool CheckBeginCast(GameLiving selectedTarget)
		{
			CommanderPet commander = Commander;

			if (commander == null)
			{
				MessageToCaster("You have no commander whose troops you could dismiss.", eChatType.CT_SpellResisted);
				return false;
			}

			if (Retainers(commander).Count == 0)
			{
				MessageToCaster($"Your {commander.Name} has no troops to dismiss.", eChatType.CT_SpellResisted);
				return false;
			}

			return base.CheckBeginCast(selectedTarget);
		}

		public override void ApplyEffectOnTarget(GameLiving target)
		{
			CommanderPet commander = Commander;

			if (commander == null)
				return;

			List<IControlledBrain> retainers = Retainers(commander);

			foreach (IControlledBrain brain in retainers)
			{
				if (brain is ControlledMobBrain mobBrain)
					mobBrain.OnRelease();                    // ends the summon effect: the retainer leaves its commander
				else
					commander.RemoveControlledBrain(brain);
			}

			if (retainers.Count > 0)
				MessageToCaster($"Your {commander.Name} dismisses {(retainers.Count == 1 ? "the troop" : $"all {retainers.Count} troops")} from service.", eChatType.CT_Spell);
		}
	}
}
