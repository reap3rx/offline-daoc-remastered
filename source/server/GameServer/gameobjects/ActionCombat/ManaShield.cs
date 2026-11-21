/*
 * Action Combat: the Mana Shield (owner 2026-11-19: "give casters ... the ability to shield themselves with their mana
 * while holding right click (since they can't block or parry) ... whatever % of health damage they were about to take as
 * power damage instead").
 *
 * Anyone with no parry, block or evade at all (the pure casters, healers and clerics) holds right click (/ac ward on,
 * released: /ac ward off). While it is up:
 *   - a share of each blow (melee or arrow, not spells) goes to power instead of health: 50%, up to 70% with the caster's
 *     own stat (its mana stat) - the same share of their power as of their health ("% of health ... as power");
 *   - raising it costs 2% of power and holding it 1% a second; it drops when power runs out (what power can't pay for
 *     lands on health);
 *   - no casting (but the interrupt spells - ManaShield.AllowedWhileWarding), and they walk (the client);
 *   - a Perfect Ward: raised within WardPerfectMs before a blow lands (the wind-up ring gold), that blow is 90% warded
 *     and gives 3% of power back - once per raise.
 * The client is told: "ward|on|share" / "ward|off|why" and, per warded blow, "def|ward|taken|power|perfect".
 */
using System;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
	public static class ManaShield
	{
		public const int PerfectMs = 250;
		public const double BaseShare = 0.5, MaxShare = 0.7, PerfectShare = 0.9;
		public const int RaiseCostPercent = 2, UpkeepPercentPerSecond = 1, PerfectRefundPercent = 3;

		/// <summary>No parry, block or evade at all: the ward is theirs.</summary>
		public static bool CanWard(GamePlayer p) =>
			p?.CharacterClass != null && p.MaxMana > 0 &&
			!ActionCombat.CanDefend(p, eActionDefense.Parry) && !ActionCombat.CanDefend(p, eActionDefense.Block) &&
			!ActionCombat.CanDefend(p, eActionDefense.Dodge);

		/// <summary>The share it takes: 50%, +1% for every 10 of the caster's mana stat above 60, up to 70%.</summary>
		public static double Share(GamePlayer p)
		{
			eStat s = p.CharacterClass.ManaStat;
			int stat = s == eStat.UNDEFINED ? 60 : p.GetModified((eProperty) s);
			return Math.Clamp(BaseShare + (stat - 60) / 1000.0, BaseShare, MaxShare);
		}

		public static bool IsWarding(GamePlayer p) => p?.ActionCombat is { Enabled: true, Warding: true };

		public static void Set(GamePlayer p, bool on)
		{
			ActionCombatState state = ActionCombat.Get(p);
			if (!on)
			{
				if (state.Warding)
					Drop(p, state, "down");
				return;
			}
			if (state.Warding || !p.IsAlive)
				return;
			if (!CanWard(p))
			{
				p.Out.SendMessage("You can parry, block or evade - the mana shield is for those who can't.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}
			int cost = Math.Max(1, p.MaxMana * RaiseCostPercent / 100);
			if (p.Mana < cost)
			{
				ActionCombat.Send(p, "ward|off|empty");
				p.Out.SendMessage("You haven't the power to raise a mana shield.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}
			if (p.IsCasting)
				p.StopCurrentSpellcast();
			ChannelCasting.Cancel(p);
			p.ChangeMana(p, eManaChangeType.Spell, -cost);
			state.Warding = true;
			state.WardRaisedAt = GameLoop.GameLoopTime;
			state.WardPerfectUsed = false;
			ActionCombat.Send(p, $"ward|on|{(int) Math.Round(Share(p) * 100)}");
			long raised = state.WardRaisedAt;
			new ECSGameTimer(p, _ =>
			{
				if (!state.Warding || state.WardRaisedAt != raised)
					return 0;
				if (!p.IsAlive || !state.Enabled)
				{
					Drop(p, state, "down");
					return 0;
				}
				int upkeep = Math.Max(1, p.MaxMana * UpkeepPercentPerSecond / 100);
				if (p.Mana < upkeep)
				{
					Drop(p, state, "empty");
					return 0;
				}
				p.ChangeMana(p, eManaChangeType.Spell, -upkeep);
				return 1000;
			}, 1000);
		}

		static void Drop(GamePlayer p, ActionCombatState state, string why)
		{
			state.Warding = false;
			ActionCombat.Send(p, "ward|off|" + why);
			if (why == "empty")
				p.Out.SendMessage("Your mana shield collapses - you are out of power!", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
		}

		/// <summary>ActionCombat.ResolveDefense: a blow on a warding caster. True when the ward takes its share.</summary>
		public static bool Resolve(GamePlayer p, ActionCombatState state, AttackData ad, long now)
		{
			if (!state.Warding || !CanWard(p) || ad.AttackType == AttackData.eAttackType.Spell || p.Mana <= 0)
				return false;
			bool perfect = !state.WardPerfectUsed && now - state.WardRaisedAt <= PerfectMs;
			double share = perfect ? PerfectShare : Share(p);
			if (perfect)
				state.WardPerfectUsed = true;
			ad.ActionDefense = eActionDefense.Ward;
			ad.ActionAuto = !perfect;                              // (ActionAuto: an ordinary ward; false: the Perfect Ward)
			ad.ActionDamageFactor = 1.0 - share;
			return true;
		}

		/// <summary>ActionCombat.OnDefended: the warded part is paid from power - the same share of power as of health.
		/// What power can't pay for lands on health, and the ward drops.</summary>
		public static void Pay(GamePlayer p, AttackData ad)
		{
			ActionCombatState state = ActionCombat.Get(p);
			int saved = Math.Max(0, ad.ActionMitigated);
			int cost = (int) Math.Ceiling(saved * (double) Math.Max(1, p.MaxMana) / Math.Max(1, p.MaxHealth));
			bool perfect = !ad.ActionAuto;
			int paid = Math.Min(cost, p.Mana);
			if (paid > 0)
				p.ChangeMana(p, eManaChangeType.Spell, -paid);
			int through = 0;
			if (paid < cost && p.IsAlive)
			{
				through = (int) Math.Ceiling((cost - paid) * (double) p.MaxHealth / Math.Max(1, p.MaxMana));
				p.ChangeHealth(ad.Attacker, eHealthChangeType.Unknown, -Math.Min(through, Math.Max(0, p.Health - 1)));
				if (p.Health <= 1 && through > 0)
					p.TakeDamage(ad.Attacker, eDamageType.Natural, 1, 0);
			}
			if (perfect && p.IsAlive)
			{
				p.ChangeMana(p, eManaChangeType.Spell, p.MaxMana * PerfectRefundPercent / 100);
				HibernianKits.Bramble(p, ad.Attacker);       // (a Druid's Bramble Shield: root, then poison)
			}
			ActionCombat.Send(p, $"def|ward|{ad.Damage + through}|{paid}|{(perfect ? 1 : 0)}");
			if (perfect)
				p.Out.SendMessage($"Perfect ward! Your mana takes {ad.Attacker?.GetName(0, false)}'s blow: {paid} power spent, {ad.Damage} taken.",
					eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
			if (p.Mana <= 0 && state.Warding)
				Drop(p, state, "empty");
		}

		/// <summary>Spells a warding caster may still cast: the quick interrupts (no other casting behind the shield).</summary>
		public static bool AllowedWhileWarding(Spell spell) =>
			spell != null && spell.CastTime <= 0 && AllowedIds.Contains(spell.ID);

		public static readonly System.Collections.Generic.HashSet<int> AllowedIds = new();   // (ClassKits: the interrupts)
	}
}
