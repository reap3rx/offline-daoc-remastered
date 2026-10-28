/*
 * Friendly spells cast on yourself by default (owner 2026-10-27): a player's realm-target spell (heals, concentration
 * and timed buffs, cures ...) goes to the selected target only when that is an ally - another player of the realm, a
 * companion bot, or a pet / summoned creature; with nothing selected, a monster or enemy, or any other NPC (merchant,
 * guard, trainer ...) selected, it is cast on you. SpellHandler.CheckBeginCast, eSpellTarget.REALM.
 */
using DOL.AI.Brain;

namespace DOL.GS
{
	public static class AllyTarget
	{
		public static bool IsAlly(GamePlayer caster, GameLiving target)
		{
			if (target == null)
				return false;

			if (target == caster)
				return true;

			if (!GameServer.ServerRules.IsSameRealm(caster, target, true))
				return false;                      // a monster, an enemy

			return target switch
			{
				GamePlayer => true,
				GameBot => true,                   // your companions
				GameNPC npc => npc.Brain is IControlledBrain,   // pets, summons, turrets - not merchants and guards
				_ => false
			};
		}
	}
}
