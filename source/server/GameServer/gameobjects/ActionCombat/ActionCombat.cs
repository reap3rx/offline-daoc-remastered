/*
 * Action Combat: an opt-in, player-only way to fight in melee (the owner's design, 2026-10-26).
 *
 * Classic DAoC rules stay for everyone else - mobs, gamebots, companions, and any player who leaves it off.
 * With it on (/ac on, the Godot client's F9):
 *   - No auto-attack. Every swing is a click (/ac swing), gated by the weapon's own timer; one swing buffers.
 *   - Holding the attack button fires the best anytime style (/ac style anytime); the Position, Reactive and
 *     Chain buttons fire the best usable style of that kind. A reactive skips the swing timer.
 *   - Your swings never miss in range (no miss, no level fumble) and always whiff out of range. Monsters still
 *     evade, parry and block at random; if they turn aside one of your STYLES you stumble (double recovery).
 *   - Your own defense is timing, not dice: a parry press (/ac parry) opens a 0.25 s window. A blow landing
 *     in it is Parried (unlocking parry reactives) and you take only part of it - less the more Parry you have.
 *     With a shield the press is a block, scaled by Shields. Holding guard (/ac guard on) softens every blow at
 *     an endurance cost. A dodge (/ac dodge) opens an evade window (longer with Evade), at an endurance cost.
 *   - Monsters fighting you wind up for WindupMs before their blow lands, and your client is told (a cue to
 *     time the parry on).
 * The client and server talk through "#AC|..." system lines the Godot client takes out of the chat.
 */
using System;
using System.Text;
using DOL.Database;
using DOL.GS.PacketHandler;
using DOL.GS.Styles;

namespace DOL.GS
{
	public enum eActionDefense : byte
	{
		None = 0,
		Parry = 1,
		Block = 2,
		Dodge = 3,
		Guard = 4
	}

	public sealed class ActionCombatState
	{
		public bool Enabled;
		public bool SwingQueued;
		public long ParryPressedAt = -100000;
		public long ParryReadyAt;
		public long DodgeAt = -100000;
		public int DodgeWindowMs;
		public long DodgeReadyAt;
		public bool Guarding;
		public bool FumblePending;
		public long FumbledUntil;
		public string LastReady = "";
		public long NextReadyCheck;
	}

	public static class ActionCombat
	{
		public const string ParamKey = "ActionCombat";
		public const string Prefix = "#AC|";

		public const int WindupMs = 600;           // a monster's telegraphed wind-up before its blow lands
		public const int ParryWindowMs = 250;      // the timed parry / block window
		public const int ParryCooldownMs = 500;    // a missed press can't be retried before this
		public const int DodgeCooldownMs = 1200;
		public const int IdlePollMs = 50;          // how often an idle attack action checks for a click
		public const double GuardFactor = 0.75;    // damage taken while holding guard
		public const double GuardShieldFactor = 0.6;

		public static bool IsActive(GameLiving living)
		{
			return living is GamePlayer player && player.ActionCombat is { Enabled: true };
		}

		public static ActionCombatState Get(GamePlayer player)
		{
			return player.ActionCombat ??= new ActionCombatState { Enabled = LoadEnabled(player) };
		}

		public static void Send(GamePlayer player, string line)
		{
			player?.Out.SendMessage(Prefix + line, eChatType.CT_System, eChatLoc.CL_SystemWindow);
		}

		// ------------------------------------------------------------------ the toggle (kept on the character)

		private static bool LoadEnabled(GamePlayer player)
		{
			DbCoreCharacterXCustomParam record = DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
				DB.Column("DOLCharactersObjectId").IsEqualTo(player.ObjectId).And(DB.Column("KeyName").IsEqualTo(ParamKey)));
			return record != null && record.Value == "1";
		}

		public static void SetEnabled(GamePlayer player, bool on)
		{
			ActionCombatState state = Get(player);
			state.Enabled = on;
			state.SwingQueued = false;
			state.Guarding = false;
			state.FumblePending = false;
			state.LastReady = "";

			DbCoreCharacterXCustomParam record = DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
				DB.Column("DOLCharactersObjectId").IsEqualTo(player.ObjectId).And(DB.Column("KeyName").IsEqualTo(ParamKey)));

			if (record == null)
				GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(player.ObjectId, ParamKey, on ? "1" : "0"));
			else
			{
				record.Value = on ? "1" : "0";
				GameServer.Database.SaveObject(record);
			}

			Send(player, "mode|" + (on ? "1" : "0"));
		}

		// ------------------------------------------------------------------ attacking

		public static GameLiving AttackableTarget(GamePlayer player)
		{
			if (player.TargetObject is not GameLiving target || !target.IsAlive || target.ObjectState is not GameObject.eObjectState.Active)
				return null;

			return GameServer.ServerRules.IsAllowedToAttack(player, target, true) ? target : null;
		}

		/// <summary>Puts the player in attack mode on their target if needed. False (and a whiff) if there is nothing to hit.</summary>
		public static bool EnsureAttacking(GamePlayer player)
		{
			if (player.ActiveWeaponSlot is eActiveWeaponSlot.Distance)
			{
				player.Out.SendMessage("Action combat is melee only for now - switch to a melee weapon.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return false;
			}

			GameLiving target = AttackableTarget(player);

			if (target == null)
			{
				Send(player, "whiff");
				return false;
			}

			if (!player.attackComponent.AttackState)
				player.attackComponent.RequestStartAttack(target);

			return true;
		}

		public static void QueueSwing(GamePlayer player)
		{
			ActionCombatState state = Get(player);

			if (!EnsureAttacking(player))
				return;

			state.Guarding = false;
			state.SwingQueued = true;
		}

		/// <summary>"anytime", "position", "reactive" or "chain": queue the best usable style of that kind.</summary>
		public static void QueueStyle(GamePlayer player, string kind)
		{
			ActionCombatState state = Get(player);

			if (!EnsureAttacking(player))
				return;

			Style style = Resolve(player, kind);

			if (style == null)
			{
				if (kind == "anytime")
				{
					state.Guarding = false;
					state.SwingQueued = true;      // no anytime style known: a plain swing
				}
				else
					player.Out.SendMessage($"No {kind} style is open right now.", eChatType.CT_System, eChatLoc.CL_SystemWindow);

				return;
			}

			state.Guarding = false;
			state.SwingQueued = true;
			player.styleComponent.NextCombatStyle = style;
			player.styleComponent.NextCombatBackupStyle = null;
			player.styleComponent.NextCombatStyleTime = GameLoop.GameLoopTime;

			// A reaction is immediate: it doesn't wait for the swing timer (unless you're still stumbling).
			if (kind == "reactive" && GameLoop.GameLoopTime >= state.FumbledUntil)
				player.attackComponent.attackAction?.ExpediteMeleeTick();
		}

		public static Style Resolve(GamePlayer player, string kind)
		{
			if (AttackableTarget(player) == null)
				return null;

			AttackData last = player.attackComponent.attackAction?.LastAttackData;
			Style best = null;
			int bestScore = int.MinValue;

			foreach (Style style in player.styleComponent.GetStyleList())
			{
				if (KindOf(style) != kind)
					continue;

				DbInventoryItem weapon = (eObjectType) style.WeaponTypeRequirement is eObjectType.Shield ? player.ActiveLeftWeapon : player.ActiveWeapon;

				if (weapon == null || !StyleProcessor.CanUseStyle(last, player, style, weapon) || !StyleProcessor.HasEnduranceFor(player, weapon, style))
					continue;

				int score = style.SpecLevelRequirement * 10;

				// A chain that follows the very style just landed beats a generic "after any hit" follow-up.
				if (kind == "chain" && style.OpeningRequirementValue != 0)
					score += 1000;

				// Reactions to what the enemy just did come before reactions to your own avoided blow.
				if (kind == "reactive" && style.OpeningRequirementType is Style.eOpening.Defensive)
					score += 1000;

				if (score > bestScore)
				{
					bestScore = score;
					best = style;
				}
			}

			return best;
		}

		public static string KindOf(Style style)
		{
			switch (style.OpeningRequirementType)
			{
				case Style.eOpening.Positional:
					return "position";
				case Style.eOpening.Defensive:
					return "reactive";
			}

			if (style.OpeningRequirementValue != 0)
				return "chain";

			return style.AttackResultRequirement switch
			{
				Style.eAttackResultRequirement.Any => "anytime",
				Style.eAttackResultRequirement.Hit or Style.eAttackResultRequirement.Style => "chain",
				_ => "reactive" // after your blow was missed, parried, blocked, evaded or fumbled
			};
		}

		/// <summary>The ready lights: which buttons would fire a style right now. Sent when it changes.</summary>
		public static void PollReady(GamePlayer player, bool force = false)
		{
			ActionCombatState state = player.ActionCombat;

			if (state == null || !state.Enabled)
				return;

			long now = GameLoop.GameLoopTime;

			if (!force && now < state.NextReadyCheck)
				return;

			state.NextReadyCheck = now + 150;
			StringBuilder sb = new("ready|");

			foreach (string kind in new[] { "position", "reactive", "chain", "anytime" })
				sb.Append(Resolve(player, kind) != null ? '1' : '0');

			string ready = sb.ToString();

			if (ready == state.LastReady)
				return;

			state.LastReady = ready;
			Send(player, ready);
		}

		public static void ClearReady(GamePlayer player)
		{
			ActionCombatState state = player.ActionCombat;

			if (state == null || !state.Enabled || state.LastReady == "ready|0000")
				return;

			state.LastReady = "ready|0000";
			Send(player, state.LastReady);
		}

		/// <summary>A monster evaded / parried / blocked one of your styles: you stumble.</summary>
		public static void OnStyleAvoided(GamePlayer player, AttackData ad)
		{
			ActionCombatState state = Get(player);
			state.FumblePending = true;
			string how = ad.AttackResult switch
			{
				eAttackResult.Evaded => "dodges",
				eAttackResult.Blocked => "blocks",
				_ => "parries"
			};
			player.Out.SendMessage($"{ad.Target.GetName(0, true)} {how} your {ad.Style.Name} - you stumble off balance!", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
			Send(player, "fumble");
		}

		// ------------------------------------------------------------------ defending

		public static void PressParry(GamePlayer player)
		{
			ActionCombatState state = Get(player);
			long now = GameLoop.GameLoopTime;

			if (now < state.ParryReadyAt)
				return;

			state.ParryPressedAt = now;
			state.ParryReadyAt = now + ParryCooldownMs;
		}

		public static void SetGuard(GamePlayer player, bool on)
		{
			Get(player).Guarding = on && player.IsAlive;
		}

		public static void PressDodge(GamePlayer player)
		{
			ActionCombatState state = Get(player);
			long now = GameLoop.GameLoopTime;

			if (now < state.DodgeReadyAt || !player.IsAlive || player.IsIncapacitated)
				return;

			int cost = Math.Max(10, player.MaxEndurance * 15 / 100);

			if (player.Endurance < cost)
			{
				player.Out.SendMessage("You are too tired to dodge!", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				Send(player, "def|tired|0");
				return;
			}

			player.ChangeEndurance(player, eEnduranceChangeType.Spell, -cost);
			int evade = player.GetAbilityLevel(Abilities.Evade);
			state.DodgeAt = now;
			state.DodgeWindowMs = 200 + 40 * evade;   // 200 ms untrained .. 480 ms with Evade VII
			state.DodgeReadyAt = now + DodgeCooldownMs;
			state.Guarding = false;
			player.movementComponent?.PauseMovementChecks(900);   // the client's dodge hop runs faster than a run
		}

		/// <summary>Parry spec 1 takes 60% of the blow, 50 takes 10%; untrained 80%.</summary>
		public static double ParryFactor(GamePlayer player) => ParryFactorForSpec(player.GetModifiedSpecLevel(Specs.Parry));

		public static double ParryFactorForSpec(int spec)
		{
			if (spec <= 0)
				return 0.8;

			return Math.Clamp(0.6 - 0.5 * (spec - 1) / 49.0, 0.05, 0.6);
		}

		/// <summary>Shields 1 takes 40% of the blow, 50 takes nothing; untrained 50%.</summary>
		public static double BlockFactor(GamePlayer player) => BlockFactorForSpec(player.GetModifiedSpecLevel(Specs.Shields));

		public static double BlockFactorForSpec(int spec)
		{
			if (spec <= 0)
				return 0.5;

			return Math.Clamp(0.4 - 0.4 * (spec - 1) / 49.0, 0.0, 0.4);
		}

		private static bool HasShield(GamePlayer player)
		{
			DbInventoryItem left = player.ActiveLeftWeapon;
			return left != null && (eObjectType) left.Object_Type is eObjectType.Shield;
		}

		/// <summary>
		/// The defender's answer to a blow, in place of the evade / parry / block dice. Returns Evaded (a dodge),
		/// Parried / Blocked (timed - ad.ActionDamageFactor is the share still taken), or Any to go on to the hit
		/// (ad.ActionDamageFactor below 1 while guarding).
		/// </summary>
		public static eAttackResult ResolveDefense(GamePlayer player, AttackData ad, bool defenseDisabled)
		{
			ActionCombatState state = Get(player);
			ad.ActionDamageFactor = 1.0;

			if (defenseDisabled || player.IsIncapacitated || player.IsSitting || ad.Attacker == null)
				return eAttackResult.Any;

			long now = GameLoop.GameLoopTime;
			bool inFront = player.IsObjectInFront(ad.Attacker, 180);

			if (now - state.DodgeAt <= state.DodgeWindowMs)
			{
				ad.ActionDefense = eActionDefense.Dodge;
				ad.EvadeChance = 100;
				return eAttackResult.Evaded;
			}

			if (inFront && now - state.ParryPressedAt <= ParryWindowMs)
			{
				ad.ArmorHitLocation = player.CalculateArmorHitLocation(ad);
				state.ParryReadyAt = now;    // a good parry can be followed by another right away

				if (HasShield(player))
				{
					ad.ActionDefense = eActionDefense.Block;
					ad.ActionDamageFactor = BlockFactor(player);
					ad.BlockChance = 100;
					return eAttackResult.Blocked;
				}

				if (ad.IsMeleeAttack)
				{
					ad.ActionDefense = eActionDefense.Parry;
					ad.ActionDamageFactor = ParryFactor(player);
					ad.ParryChance = 100;
					return eAttackResult.Parried;
				}
			}

			if (state.Guarding && inFront)
			{
				int cost = 3 + player.MaxEndurance * 2 / 100;

				if (player.Endurance >= cost)
				{
					player.ChangeEndurance(player, eEnduranceChangeType.Spell, -cost);
					ad.ActionDefense = eActionDefense.Guard;
					ad.ActionDamageFactor = HasShield(player) ? GuardShieldFactor : GuardFactor;
				}
				else
				{
					state.Guarding = false;
					player.Out.SendMessage("You are too tired to hold your guard!", eChatType.CT_System, eChatLoc.CL_SystemWindow);
					Send(player, "def|tired|0");
				}
			}

			return eAttackResult.Any;
		}

		/// <summary>After the blow is worked out: tell the defender how it went.</summary>
		public static void OnDefended(GamePlayer player, AttackData ad)
		{
			switch (ad.ActionDefense)
			{
				case eActionDefense.Parry:
					player.Out.SendMessage($"Timed parry! You turn {ad.Attacker.GetName(0, false)}'s blow aside and take {ad.Damage} damage.", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
					Send(player, "def|parry|" + ad.Damage);
					break;
				case eActionDefense.Block:
					player.Out.SendMessage($"Timed block! You catch {ad.Attacker.GetName(0, false)}'s blow on your shield and take {ad.Damage} damage.", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
					Send(player, "def|block|" + ad.Damage);
					break;
				case eActionDefense.Dodge:
					Send(player, "def|dodge|0");
					break;
				case eActionDefense.Guard:
					if (ad.AttackResult is eAttackResult.HitUnstyled or eAttackResult.HitStyle)
						Send(player, "def|guard|" + ad.Damage);
					break;
			}
		}

		public static void SendWindup(GamePlayer player, GameNPC attacker, int ms)
		{
			Send(player, $"windup|{attacker.ObjectID}|{ms}");
		}

		public static string Describe(GamePlayer player)
		{
			ActionCombatState state = Get(player);
			StringBuilder sb = new();
			sb.AppendLine($"Action combat is {(state.Enabled ? "ON" : "OFF")}.");
			sb.AppendLine($"Timed parry takes {ParryFactor(player) * 100:0}% of a blow (Parry {player.GetModifiedSpecLevel(Specs.Parry)}); window {ParryWindowMs} ms.");

			if (HasShield(player))
				sb.AppendLine($"Timed block takes {BlockFactor(player) * 100:0}% (Shields {player.GetModifiedSpecLevel(Specs.Shields)}).");

			sb.Append($"Dodge window {200 + 40 * player.GetAbilityLevel(Abilities.Evade)} ms (Evade {player.GetAbilityLevel(Abilities.Evade)}), costs 15% endurance.");
			return sb.ToString();
		}
	}
}
