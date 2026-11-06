/*
 * Action Combat: the caster's staff counter (the owner's design, 2026-11-01).
 *
 * A pure caster (Cabalist, Necromancer, Sorcerer, Theurgist, Wizard, Bonedancer, Runemaster, Spiritmaster, Warlock,
 * Animist, Bainshee, Eldritch, Enchanter, Mentalist) with a staff out holds the attack button about a second, like a
 * melee power attack, and lets go (/ac counter). That costs 10% of their power, hit or miss, and opens a window like
 * a parry: if an enemy's blow lands on them within 0.25 s the attacker is snared for 5 s, within 0.15 s rooted for
 * 5 s, within 0.10 s stunned for 5 s - the closer the read, the stronger. The blow itself still lands. Every caster
 * has it from level 1 (no spec, not listed with the styles). No resists, no immunity timers, no cooldown: the power
 * is the limit. The caster plays a Friar staff style's animation for each (StunAnim / RootAnim / SnareAnim).
 */
using System;
using DOL.Database;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS
{
	public static class CasterCounter
	{
		public const int ChargeCostPercent = 10;
		public const int SnareWindowMs = 250;
		public const int RootWindowMs = 150;
		public const int StunWindowMs = 100;
		public const int DurationSeconds = 5;
		public const int SnarePercent = 50;

		// Friar staff styles' animations (styles.csv Icon -> the client's staff clips): Stunning Wrath, Banish, Spinning Staff
		public const int StunAnim = 243;
		public const int RootAnim = 239;
		public const int SnareAnim = 230;

		// The spells' looks (spells.csv client effects): Stunned (red stun swirl), Jagged Roots (thorns), Earthsnare
		public const int StunEffect = 2132;
		public const int RootEffect = 2036;
		public const int SnareEffect = 2061;

		private static readonly eCharacterClass[] Casters =
		{
			eCharacterClass.Cabalist, eCharacterClass.Necromancer, eCharacterClass.Sorcerer, eCharacterClass.Theurgist,
			eCharacterClass.Wizard, eCharacterClass.Bonedancer, eCharacterClass.Runemaster, eCharacterClass.Spiritmaster,
			eCharacterClass.Warlock, eCharacterClass.Animist, eCharacterClass.Bainshee, eCharacterClass.Eldritch,
			eCharacterClass.Enchanter, eCharacterClass.Mentalist,
			// and the caster base classes before level 5 (owner 2026-11-05: a new Sorceress - still a Mage - couldn't)
			eCharacterClass.Mage, eCharacterClass.Elementalist, eCharacterClass.Disciple, eCharacterClass.Mystic,
			eCharacterClass.Magician, eCharacterClass.Forester
		};

		public static bool IsCaster(GamePlayer player) =>
			player?.CharacterClass != null && Array.IndexOf(Casters, (eCharacterClass) player.CharacterClass.ID) >= 0;

		/// <summary>A pure caster with a staff in hand: their held attack is the counter.</summary>
		public static bool CanCounter(GamePlayer player)
		{
			if (!IsCaster(player))
				return false;

			DbInventoryItem weapon = player.ActiveWeapon;
			return weapon != null && (eObjectType) weapon.Object_Type is eObjectType.Staff;
		}

		public static int Cost(GamePlayer player) => Math.Max(1, player.MaxMana * ChargeCostPercent / 100);

		/// <summary>The charged release: pay the power and open the window.</summary>
		public static void Release(GamePlayer player)
		{
			ActionCombatState state = ActionCombat.Get(player);

			if (!player.IsAlive || player.IsIncapacitated || !CanCounter(player))
				return;

			int cost = Cost(player);

			if (player.Mana < cost)
			{
				player.Out.SendMessage("You don't have enough power to counter!", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				ActionCombat.Send(player, "counter|tired");
				return;
			}

			player.ChangeMana(player, eManaChangeType.Spell, -cost);
			long now = GameLoop.GameLoopTime;
			state.CounterAt = now;
			state.CounterAnswered = false;
			ActionCombat.Send(player, "counter|open|" + SnareWindowMs);

			new ECSGameTimer(player, _ =>
			{
				if (state.CounterAt == now && !state.CounterAnswered && player.IsAlive)
				{
					player.Out.SendMessage("Your counter catches nothing.", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
					ActionCombat.Send(player, "counter|miss");
				}

				return 0;
			}, SnareWindowMs + 30);
		}

		/// <summary>A blow is landing on the player (ActionCombat.ResolveDefense): inside an open window, it is answered.</summary>
		public static void OnBlow(GamePlayer player, ActionCombatState state, AttackData ad, long now)
		{
			if (state.CounterAnswered || ad.Attacker is not GameLiving attacker || !attacker.IsAlive)
				return;

			long dt = now - state.CounterAt;

			if (dt < 0 || dt > SnareWindowMs)
				return;

			state.CounterAnswered = true;
			string kind = dt <= StunWindowMs ? "stun" : dt <= RootWindowMs ? "root" : "snare";
			Apply(player, attacker, kind);
		}

		private static void Apply(GamePlayer player, GameLiving target, string kind)
		{
			// no immunities (owner 2026-11-01): any left from an earlier counter or spell goes first
			foreach (eEffect immunity in new[] { eEffect.StunImmunity, eEffect.NPCStunImmunity, eEffect.SnareImmunity })
				foreach (ECSGameEffect e in new System.Collections.Generic.List<ECSGameEffect>(target.effectListComponent.GetEffects(immunity)))
					e.End();

			DbSpell db = new()
			{
				SpellID = kind == "stun" ? 990001 : kind == "root" ? 990002 : 990003,
				Name = kind == "stun" ? "Staff Counter: Stun" : kind == "root" ? "Staff Counter: Root" : "Staff Counter: Snare",
				Type = kind == "stun" ? eSpellType.UnresistableStun.ToString() : eSpellType.SpeedDecrease.ToString(),
				ClientEffect = kind == "stun" ? StunEffect : kind == "root" ? RootEffect : SnareEffect,
				Icon = kind == "stun" ? StunEffect : kind == "root" ? RootEffect : SnareEffect,
				Target = "Enemy",
				Range = 500,
				Duration = DurationSeconds,
				Value = kind == "root" ? 99 : kind == "snare" ? SnarePercent : 0,
				Description = "A caster's timed staff counter."
			};
			Spell spell = new(db, 1);
			SpellLine line = SkillBase.GetSpellLine(GlobalSpellsLines.Combat_Styles_Effect);
			ISpellHandler handler = kind == "stun"
				? ScriptMgr.CreateSpellHandler(player, spell, line)
				: new CounterSlowSpellHandler(player, spell, line);

			handler?.StartSpell(target);

			int anim = kind == "stun" ? StunAnim : kind == "root" ? RootAnim : SnareAnim;
			DbInventoryItem staff = player.ActiveWeapon;

			foreach (GamePlayer viewer in player.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
				viewer?.Out.SendCombatAnimation(player, target, (ushort) (staff?.Model ?? 0), 0, anim, 0, 11, target.HealthPercent);

			string what = kind == "stun" ? "stun" : kind == "root" ? "root" : "snare";
			player.Out.SendMessage($"Perfect timing! Your staff counter {what}s {target.GetName(0, false)}!", eChatType.CT_YouHit, eChatLoc.CL_SystemWindow);
			ActionCombat.Send(player, "counter|" + kind);
		}
	}

	/// <summary>The counter's snare / root: never resisted, the full 5 s, no immunity check (CasterCounter).</summary>
	public class CounterSlowSpellHandler : SpeedDecreaseSpellHandler
	{
		public CounterSlowSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

		public override double CalculateSpellResistChance(GameLiving target) => 0;

		protected override int CalculateEffectDuration(GameLiving target) => Spell.Duration;
	}
}
