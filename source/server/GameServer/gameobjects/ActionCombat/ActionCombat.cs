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
 *   - Your own defense is timing, not dice (owner 2026-10-28): a parry press (/ac parry) opens a short window -
 *     0.2 s untrained, wider with Parry spec and Mastery of Parrying. A blow landing in it is Parried (unlocking
 *     parry reactives) and you take only part of it - less the more Parry you have. With a shield the press is a
 *     block: a narrower window (0.15 s, wider with Shields / Mastery of Blocking) that saves more of the blow.
 *     A dodge (/ac dodge) is the narrowest (0.1 s, wider with Evade / Dodger) and avoids the whole blow. A press
 *     that catches something is free; in combat one that catches nothing costs endurance - a reactive style's for
 *     a parry, half again for a block, twice for a dodge. Holding guard (/ac guard on) softens every blow at an
 *     endurance cost.
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
		public bool ParryOnly;                 // the press was "parry, not block" (a shield carried: Shift + right mouse)
		public bool ParryAnswered;             // the press caught a blow (else, in combat, it costs endurance)
		public int ParryWindowMs = 200;        // this press's window (parry or block, by skill)
		public long DodgeAt = -100000;
		public int DodgeWindowMs;
		public long DodgeReadyAt;
		public bool DodgeAnswered;
		public string LastWindows = "";
		public bool Guarding;
		public bool FumblePending;
		// A reaction answers one opening: the blow you parried / blocked / dodged (the enemy's attack), or your own
		// blow it turned aside. Once a reactive style is used on it, it is spent until a new one comes.
		public AttackData SpentEnemyOpening;
		public AttackData SpentOwnOpening;
		public long FumbledUntil;
		public string LastReady = "";
		public long NextReadyCheck;
		// Archery: a drawn shot (normal or critical), held until it is loosed.
		public bool Drawing;
		public bool DrawCrit;
		public long DrawStart;
		public int DrawFullMs;
		public bool Overdrawing;
		public ECSGameTimer DrawTimer;
		public long NextShotAt;                // shots are at least ShotDelayMs apart
	}

	public static class ActionCombat
	{
		public const string ParamKey = "ActionCombat";
		public const string Prefix = "#AC|";

		public const int WindupMs = 600;           // a monster's telegraphed wind-up before its blow lands
		// The timed windows (owner 2026-10-28: "very small at low skill, and get easier with levels"): the base, what
		// each point of spec (Evade level for a dodge) adds, and what each level of the matching realm ability adds.
		public const int ParryWindowBaseMs = 200;
		public const int BlockWindowBaseMs = 150;
		public const int DodgeWindowBaseMs = 100;
		public const int WindowPerSpecMs = 3;      // Parry / Shields: spec 50 = +147 ms
		public const int WindowPerEvadeMs = 30;    // Evade VII = +210 ms
		public const int WindowPerRealmAbilityMs = 20;
		public const int ParryCooldownMs = 500;    // after the window closes, no new press before this (owner 2026-10-27: no spam)
		public const int MissedDefenseRating = 7;  // a missed press with no reactive style known: a typical reactive's cost
		public const double MissedBlockCost = 1.5; // a missed block / dodge costs this many missed parries (owner 2026-10-28)
		public const double MissedDodgeCost = 2.0;
		public const int IdlePollMs = 50;          // how often an idle attack action checks for a click
		public const double GuardFactor = 0.75;    // damage taken while holding guard
		public const double GuardShieldFactor = 0.6;
		public const double QuickSwingSpeed = 0.75;  // a plain swing recovers in 75% of the weapon's time ...
		public const double QuickSwingDamage = 0.7;  // ... for 70% of its damage (a little less damage per second)

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
			SendWindows(player, true);
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
			Style style = Resolve(player, kind);

			// Position / Reactive / Chain do nothing unless their condition is met (no swing, no air punch).
			if (style == null && kind != "anytime")
				return;

			if (!EnsureAttacking(player))
				return;

			if (style == null)
			{
				state.Guarding = false;
				state.SwingQueued = true;          // no anytime style known: a plain swing
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

				if (IsOpeningSpent(player, style))
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

		/// <summary>The opening a reactive style answers (null for other styles).</summary>
		public static AttackData OpeningOf(GamePlayer player, Style style)
		{
			if (style == null || KindOf(style) != "reactive")
				return null;

			if (style.OpeningRequirementType is Style.eOpening.Defensive)
				return (player.TargetObject as GameLiving)?.attackComponent?.attackAction?.LastAttackData;

			return player.attackComponent.attackAction?.LastAttackData;
		}

		public static bool IsOpeningSpent(GamePlayer player, Style style)
		{
			AttackData opening = OpeningOf(player, style);

			if (opening == null)
				return false;

			ActionCombatState state = Get(player);
			return style.OpeningRequirementType is Style.eOpening.Defensive
				? ReferenceEquals(opening, state.SpentEnemyOpening)
				: ReferenceEquals(opening, state.SpentOwnOpening);
		}

		public static void SpendOpening(GamePlayer player, Style style, AttackData opening)
		{
			if (opening == null)
				return;

			ActionCombatState state = Get(player);

			if (style.OpeningRequirementType is Style.eOpening.Defensive)
				state.SpentEnemyOpening = opening;
			else
				state.SpentOwnOpening = opening;
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
			SendWindows(player);                  // (spec / level / realm abilities change them)

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

		public static void PressParry(GamePlayer player, bool parryOnly = false)
		{
			ActionCombatState state = Get(player);
			long now = GameLoop.GameLoopTime;

			if (now < state.ParryReadyAt || !player.attackComponent.AttackState || !player.IsAlive)
				return;                            // (a sheathed weapon parries nothing: the client draws it first)

			bool block = HasShield(player) && !parryOnly;
			eActionDefense kind = block ? eActionDefense.Block : eActionDefense.Parry;

			// In combat a press that catches nothing costs endurance (owner 2026-10-27) - so there has to be enough
			// for it up front. One that catches a blow costs nothing.
			int cost = player.InCombat ? MissedDefenseCost(player, kind) : 0;

			if (cost > 0 && player.Endurance < cost)
			{
				state.ParryReadyAt = now + ParryCooldownMs;
				player.Out.SendMessage(block ? "You are too tired to block!" : "You are too tired to parry!", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				Send(player, "def|tired|0");
				return;
			}

			int window = Window(player, kind);
			state.ParryOnly = parryOnly;
			state.ParryPressedAt = now;
			state.ParryAnswered = false;
			state.ParryWindowMs = window;
			state.ParryReadyAt = now + window + ParryCooldownMs;   // half a second after the window closes

			if (cost > 0)
				ChargeIfMissed(player, () => state.ParryPressedAt == now && !state.ParryAnswered, cost, window);
		}

		public static void PressDodge(GamePlayer player)
		{
			ActionCombatState state = Get(player);
			long now = GameLoop.GameLoopTime;

			if (now < state.DodgeReadyAt || !player.IsAlive || player.IsIncapacitated || !player.attackComponent.AttackState)
				return;

			int cost = player.InCombat ? MissedDefenseCost(player, eActionDefense.Dodge) : 0;

			if (cost > 0 && player.Endurance < cost)
			{
				state.DodgeReadyAt = now + ParryCooldownMs;
				player.Out.SendMessage("You are too tired to dodge!", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				Send(player, "def|tired|0");
				return;
			}

			int window = Window(player, eActionDefense.Dodge);
			state.DodgeAt = now;
			state.DodgeWindowMs = window;
			state.DodgeAnswered = false;
			state.DodgeReadyAt = now + window + ParryCooldownMs;
			state.Guarding = false;

			if (cost > 0)
				ChargeIfMissed(player, () => state.DodgeAt == now && !state.DodgeAnswered, cost, window);
		}

		/// <summary>When the window has closed: if the press caught nothing, its endurance is paid.</summary>
		private static void ChargeIfMissed(GamePlayer player, Func<bool> missed, int cost, int window)
		{
			new ECSGameTimer(player, _ =>
			{
				if (missed() && player.IsAlive)
				{
					int paid = Math.Min(cost, player.Endurance);
					player.ChangeEndurance(player, eEnduranceChangeType.Spell, -paid);
					Send(player, $"def|miss|{paid}");
				}

				return 0;
			}, window + 20);
		}

		/// <summary>How long a parry / block / dodge press stays open for this player (ms).</summary>
		public static int Window(GamePlayer player, eActionDefense kind) => kind switch
		{
			eActionDefense.Block => BlockWindowFor(player.GetModifiedSpecLevel(Specs.Shields), RealmAbilityLevel<RealmAbilities.MasteryOfBlocking>(player)),
			eActionDefense.Dodge => DodgeWindowFor(player.GetAbilityLevel(Abilities.Evade), RealmAbilityLevel<RealmAbilities.AtlasOF_Dodger>(player)),
			_ => ParryWindowFor(player.GetModifiedSpecLevel(Specs.Parry), RealmAbilityLevel<RealmAbilities.MasteryOfParrying>(player))
		};

		public static int ParryWindowFor(int spec, int realmAbility) =>
			ParryWindowBaseMs + WindowPerSpecMs * Math.Clamp(spec - 1, 0, 60) + WindowPerRealmAbilityMs * realmAbility;

		public static int BlockWindowFor(int spec, int realmAbility) =>
			BlockWindowBaseMs + WindowPerSpecMs * Math.Clamp(spec - 1, 0, 60) + WindowPerRealmAbilityMs * realmAbility;

		public static int DodgeWindowFor(int evade, int realmAbility) =>
			DodgeWindowBaseMs + WindowPerEvadeMs * Math.Clamp(evade, 0, 7) + WindowPerRealmAbilityMs * realmAbility;

		private static int RealmAbilityLevel<T>(GamePlayer player) where T : Ability
		{
			foreach (object a in player.GetAllAbilities())
			{
				if (a is T ability)
					return Math.Max(0, ability.Level);
			}

			return 0;
		}

		/// <summary>
		/// What a press that catches nothing costs (owner 2026-10-28: dodge the most, block moderate, parry the least):
		/// a parry costs the cheapest reactive style (after a parry / block / evade) you know for your weapon - or,
		/// knowing none, a typical reactive's cost at its speed; a block half again (at least the shield's own
		/// reactive); a dodge twice a parry.
		/// </summary>
		public static int MissedDefenseCost(GamePlayer player, eActionDefense kind)
		{
			int parry = ReactiveCost(player, player.ActiveWeapon);

			return kind switch
			{
				eActionDefense.Block => BlockCostFor(parry, ReactiveCost(player, player.ActiveLeftWeapon ?? player.ActiveWeapon)),
				eActionDefense.Dodge => DodgeCostFor(parry, BlockCostFor(parry, 0)),
				_ => parry
			};
		}

		public static int BlockCostFor(int parryCost, int shieldReactiveCost) =>
			Math.Max(shieldReactiveCost, (int) Math.Ceiling(parryCost * MissedBlockCost));

		public static int DodgeCostFor(int parryCost, int blockCost) =>
			Math.Max(blockCost + 1, (int) Math.Ceiling(parryCost * MissedDodgeCost));

		private static int ReactiveCost(GamePlayer player, DbInventoryItem weapon)
		{
			if (weapon == null)
				return StyleProcessor.EnduranceCostForRating(player, MissedDefenseRating, 30);   // (bare hands)

			int best = int.MaxValue;

			foreach (Style style in player.styleComponent.GetStyleList())
			{
				if (style.OpeningRequirementType is not Style.eOpening.Defensive || !StyleProcessor.IsStyleForWeapon(style, player, weapon))
					continue;

				best = Math.Min(best, StyleProcessor.EnduranceCostFor(player, style, weapon));
			}

			return best != int.MaxValue ? best : StyleProcessor.EnduranceCostForRating(player, MissedDefenseRating, weapon.SPD_ABS);
		}

		/// <summary>The client's timing (its press gating and the wind-up ring's "now"): sent when it changes.</summary>
		public static void SendWindows(GamePlayer player, bool force = false)
		{
			ActionCombatState state = player.ActionCombat;

			if (state == null)
				return;

			string line = $"windows|{Window(player, eActionDefense.Parry)}|{Window(player, eActionDefense.Block)}|{Window(player, eActionDefense.Dodge)}|{ParryCooldownMs}";

			if (!force && line == state.LastWindows)
				return;

			state.LastWindows = line;
			Send(player, line);
		}

		public static void SetGuard(GamePlayer player, bool on)
		{
			Get(player).Guarding = on && player.IsAlive;
		}

		/// <summary>Parry spec 1 takes 60% of the blow, 50 takes 20%; untrained 80% (owner 2026-10-28: a parry saves the
		/// least, a block more, a dodge all of it).</summary>
		public static double ParryFactor(GamePlayer player) => ParryFactorForSpec(player.GetModifiedSpecLevel(Specs.Parry));

		public static double ParryFactorForSpec(int spec)
		{
			if (spec <= 0)
				return 0.8;

			return Math.Clamp(0.6 - 0.4 * (spec - 1) / 49.0, 0.15, 0.6);
		}

		/// <summary>Shields 1 takes 40% of the blow, 50 takes 10%; untrained 50%.</summary>
		public static double BlockFactor(GamePlayer player) => BlockFactorForSpec(player.GetModifiedSpecLevel(Specs.Shields));

		public static double BlockFactorForSpec(int spec)
		{
			if (spec <= 0)
				return 0.5;

			return Math.Clamp(0.4 - 0.3 * (spec - 1) / 49.0, 0.05, 0.4);
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
				state.DodgeAnswered = true;
				state.DodgeReadyAt = now;        // (a dodge that avoided a blow can be followed at once)
				ad.ActionDefense = eActionDefense.Dodge;
				ad.EvadeChance = 100;
				return eAttackResult.Evaded;
			}

			if (inFront && now - state.ParryPressedAt <= state.ParryWindowMs)
			{
				ad.ArmorHitLocation = player.CalculateArmorHitLocation(ad);
				bool caught = HasShield(player) && (!state.ParryOnly || !ad.IsMeleeAttack) || ad.IsMeleeAttack;

				if (caught)
				{
					state.ParryAnswered = true;
					state.ParryReadyAt = now;    // a good parry can be followed by another right away
				}

				// With a shield the press blocks - unless it was a parry press (to open a parry reaction).
				if (HasShield(player) && (!state.ParryOnly || !ad.IsMeleeAttack))
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
					player.Out.SendMessage($"Timed parry! You turn {ad.Attacker.GetName(0, false)}'s blow aside: {ad.ActionMitigated} damage saved, {ad.Damage} taken.", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
					Send(player, $"def|parry|{ad.Damage}|{ad.ActionMitigated}");
					break;
				case eActionDefense.Block:
					player.Out.SendMessage($"Timed block! You catch {ad.Attacker.GetName(0, false)}'s blow on your shield: {ad.ActionMitigated} damage saved, {ad.Damage} taken.", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
					Send(player, $"def|block|{ad.Damage}|{ad.ActionMitigated}");
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

		/// <summary>
		/// Floating combat text: every point of damage a player deals (or their pet deals) or takes, reported to
		/// them as "fct|target oid (0 = you)|amount|critical|out / pet / in". Called from GameLiving.TakeDamage.
		/// </summary>
		public static void ReportDamage(GameLiving target, GameObject source, int damage, int critical)
		{
			int amount = damage + critical;

			if (amount <= 0 || target == null)
				return;

			string crit = critical > 0 ? "1" : "0";

			if (target is GamePlayer hurt)
				Send(hurt, $"fct|0|{amount}|{crit}|in");

			if (source is GamePlayer attacker && attacker != target)
				Send(attacker, $"fct|{target.ObjectID}|{amount}|{crit}|out");
			else if (source is GameNPC pet && pet.Brain is AI.Brain.IControlledBrain brain &&
				brain.GetPlayerOwner() is GamePlayer owner && owner != target)
				Send(owner, $"fct|{target.ObjectID}|{amount}|{crit}|pet");
		}

		// ------------------------------------------------------------------ monsters spreading out

		public const int RingRadius = 100;          // where monsters stand around an action player (2.5 m)
		public const int RingScanRadius = 450;
		public const double RingMaxStepDegrees = 60;

		private static bool IsRingAttacker(GameNPC npc, GamePlayer player)
		{
			return npc.IsAlive && npc.IsAttacking && npc.TargetObject == player &&
				npc.ActiveWeaponSlot is not eActiveWeaponSlot.Distance &&
				npc.Brain is not AI.Brain.IControlledBrain && npc.MaxSpeedBase > 0;
		}

		/// <summary>
		/// Monsters meleeing an action player spread around them instead of stacking on one spot (owner 2026-10-26:
		/// stacked monsters were hard to target apart). Two or more take slots on a ring: in their present order
		/// around the player, at most RingMaxStepDegrees apart (two stand 60 degrees apart, six close the circle),
		/// the ring turned to where they already are so nobody walks far. False: follow as usual (one alone).
		/// </summary>
		public static bool TryGetRingSlot(GameNPC npc, GamePlayer player, out System.Numerics.Vector3 slot)
		{
			slot = default;

			if (!IsActive(player) || !IsRingAttacker(npc, player))
				return false;

			System.Collections.Generic.List<(GameNPC npc, double angle)> ring = new();

			foreach (GameNPC other in player.GetNPCsInRadius(RingScanRadius))
			{
				if (other == npc || IsRingAttacker(other, player))
					ring.Add((other, Math.Atan2(other.Y - player.Y, other.X - player.X)));
			}

			if (ring.Count < 2)
				return false;

			ring.Sort((a, b) => a.angle != b.angle ? a.angle.CompareTo(b.angle) : a.npc.ObjectID.CompareTo(b.npc.ObjectID));
			double step = Math.Min(2 * Math.PI / ring.Count, RingMaxStepDegrees * Math.PI / 180.0);

			// Where the ring sits: the turn that keeps everyone closest to where they stand.
			double sx = 0, sy = 0;

			for (int i = 0; i < ring.Count; i++)
			{
				sx += Math.Cos(ring[i].angle - i * step);
				sy += Math.Sin(ring[i].angle - i * step);
			}

			double baseAngle = Math.Atan2(sy, sx);
			int index = ring.FindIndex(x => x.npc == npc);

			if (index < 0)
				return false;                       // (not near the player yet: run up as usual)
			double a = baseAngle + index * step;
			slot = new System.Numerics.Vector3((float) (player.X + Math.Cos(a) * RingRadius), (float) (player.Y + Math.Sin(a) * RingRadius), player.Z);
			return true;
		}

		// ------------------------------------------------------------------ archery (bows, crossbows, thrown)

		public const int ShotDelayMs = 1000;          // the least time between two shots (owner 2026-10-26: no arrow spam)
		public const int OverdrawGraceMs = 1200;      // held this long past full draw, the bow starts to overdraw
		public const int DrawTickMs = 250;
		public const double OverdrawDamage = 1.6;     // an overdrawn shot that lands
		public const double OverdrawMiss = 0.40;
		public const double FullDrawMiss = 0.03;

		private static bool IsBow(DbInventoryItem weapon) => weapon != null && weapon.SlotPosition == Slot.RANGED;

		/// <summary>
		/// The shot button pressed (/ac draw normal|crit): the bow is drawn. Full draw takes what a shot takes in the
		/// classic game (the critical shot's longer draw for a critical). The client roots you while you draw.
		/// </summary>
		public static void StartDraw(GamePlayer player, bool crit)
		{
			ActionCombatState state = Get(player);

			if (state.Drawing)
				return;

			if (GameLoop.GameLoopTime < state.NextShotAt - 100)
			{
				Send(player, "draw|0");                // still recovering from the last shot
				return;
			}

			DbInventoryItem weapon = player.ActiveWeapon;

			if (player.ActiveWeaponSlot is not eActiveWeaponSlot.Distance || !IsBow(weapon))
			{
				Send(player, "draw|0");
				return;
			}

			string refusal = null;

			if (!player.IsAlive || player.IsIncapacitated)
				refusal = "You can't draw your bow now.";
			else if (crit && player.GetAbilityLevel(Abilities.Critical_Shot) <= 0)
				refusal = "You haven't learned Critical Shot yet.";
			else if (player.rangeAttackComponent.UpdateAmmo(weapon) == null)
				refusal = "You must select a quiver slot to draw from!";
			else if (!player.rangeAttackComponent.IsAmmoCompatible)
				refusal = "You can't use your selected quiver slot with this weapon!";
			else if (player.Endurance < (crit ? RangeAttackComponent.CRITICAL_SHOT_ENDURANCE_COST : RangeAttackComponent.DEFAULT_ENDURANCE_COST))
				refusal = "You are too tired to draw your bow!";

			if (refusal != null)
			{
				player.Out.SendMessage(refusal, eChatType.CT_System, eChatLoc.CL_SystemWindow);
				Send(player, "draw|0");
				return;
			}

			// The full draw: the classic shot time (Quickness, archery speed, the critical shot's own draw).
			RangeAttackComponent ranged = player.rangeAttackComponent;
			eRangedAttackType before = ranged.RangedAttackType;
			ranged.RangedAttackType = crit ? eRangedAttackType.Critical : eRangedAttackType.Normal;
			int full = player.attackComponent.AttackSpeed(weapon);
			ranged.RangedAttackType = before is eRangedAttackType.Critical ? eRangedAttackType.Normal : before;

			state.Drawing = true;
			state.DrawCrit = crit;
			state.DrawStart = GameLoop.GameLoopTime;
			state.DrawFullMs = Math.Max(500, full);
			state.Overdrawing = false;
			state.DrawTimer?.Stop();
			state.DrawTimer = new ECSGameTimer(player, DrawTick, DrawTickMs);
			// the bow's reach without the height bonus (the client adds that itself for the out-of-range warning)
			int reach = player.attackComponent.AttackRange;

			if (player.TargetObject is GameLiving aimed)
				reach -= (player.Z - aimed.Z) / 2;

			Send(player, $"draw|{state.DrawFullMs}|{OverdrawGraceMs}|{(crit ? 1 : 0)}|{reach}");
		}

		private static int DrawTick(ECSGameTimer timer)
		{
			if (timer.Owner is not GamePlayer player)
				return 0;

			ActionCombatState state = Get(player);

			if (!state.Drawing)
				return 0;

			if (!player.IsAlive || player.IsIncapacitated || player.ActiveWeaponSlot is not eActiveWeaponSlot.Distance)
			{
				CancelDraw(player, null);
				return 0;
			}

			if (player.IsBeingInterruptedByOther)
			{
				CancelDraw(player, "Your shot is interrupted!");
				return 0;
			}

			long held = GameLoop.GameLoopTime - state.DrawStart;

			if (held > state.DrawFullMs + OverdrawGraceMs)
			{
				// Overdrawn: the arms burn - endurance drains fast, and an empty pool ends it.
				int drain = Math.Max(2, player.MaxEndurance * 3 / 100);

				if (!state.Overdrawing)
				{
					state.Overdrawing = true;
					Send(player, "overdraw");
				}

				if (player.Endurance < drain + RangeAttackComponent.DEFAULT_ENDURANCE_COST)
				{
					CancelDraw(player, "Your arms give out and you lower your bow.");
					return 0;
				}

				player.ChangeEndurance(player, eEnduranceChangeType.Spell, -drain);
			}

			return DrawTickMs;
		}

		public static void CancelDraw(GamePlayer player, string why)
		{
			ActionCombatState state = Get(player);

			if (!state.Drawing)
				return;

			state.Drawing = false;
			state.Overdrawing = false;
			state.DrawTimer?.Stop();
			state.DrawTimer = null;

			if (why != null)
				player.Out.SendMessage(why, eChatType.CT_System, eChatLoc.CL_SystemWindow);

			Send(player, "draw|0");
		}

		/// <summary>
		/// The shot button let go (/ac loose): the arrow goes, as good as the draw. Early: weaker and likelier to miss
		/// (a critical rarely crits). Full: hardly misses (a critical always crits). Overdrawn: far stronger, often misses.
		/// </summary>
		public static void Loose(GamePlayer player)
		{
			ActionCombatState state = Get(player);

			if (!state.Drawing)
				return;

			long held = GameLoop.GameLoopTime - state.DrawStart;
			bool crit = state.DrawCrit;
			bool over = state.Overdrawing || held > state.DrawFullMs + OverdrawGraceMs;
			int full = state.DrawFullMs;
			state.Drawing = false;
			state.Overdrawing = false;
			state.DrawTimer?.Stop();
			state.DrawTimer = null;

			DbInventoryItem weapon = player.ActiveWeapon;
			GameLiving target = AttackableTarget(player);
			string refusal = null;

			if (player.ActiveWeaponSlot is not eActiveWeaponSlot.Distance || !IsBow(weapon))
				refusal = "";
			else if (target == null)
				refusal = "You need a target to shoot at.";
			else if (!player.IsWithinRadius(target, player.attackComponent.AttackRange))
				refusal = $"{target.GetName(0, true)} is too far away.";
			else if (!player.TargetInView)
				refusal = $"You can't see {target.GetName(0, false)}.";
			else if (!player.IsObjectInFront(target, 90))
				refusal = $"{target.GetName(0, true)} is not in front of you.";
			else if (player.rangeAttackComponent.UpdateAmmo(weapon) == null)
				refusal = "You are out of ammunition.";

			if (refusal != null)
			{
				if (refusal != "")
					player.Out.SendMessage(refusal + " You lower your bow.", eChatType.CT_System, eChatLoc.CL_SystemWindow);

				Send(player, "draw|0");
				return;
			}

			double f = Math.Clamp(held / (double) full, 0.0, 1.0);
			double critMod = Math.Clamp(2 + (player.EffectiveLevel - target.EffectiveLevel) * 0.075, 1.1, 2.0);
			ShotNumbers numbers = ShotFor(f, over, crit, critMod);
			bool critical = crit && Util.Chance(numbers.CritChance);
			double effectiveness = critical ? numbers.CritEffectiveness : numbers.Effectiveness;
			double miss = numbers.Miss;
			string quality = over ? "overdrawn" : f >= 1.0 ? "full" : "early";

			// The arrow: endurance and ammunition, the release animation, then the hit when it gets there.
			RangeAttackComponent ranged = player.rangeAttackComponent;
			eRangedAttackType type = critical ? eRangedAttackType.Critical : eRangedAttackType.Normal;
			ranged.RangedAttackType = type;
			DbInventoryItem ammo = ranged.Ammo;
			ranged.RemoveEnduranceAndAmmoOnShot();
			ranged.RangedAttackType = eRangedAttackType.Normal;

			int ticksToTarget = player.GetDistanceTo(target) * 1000 / RangeAttackComponent.PROJECTILE_FLIGHT_SPEED;
			byte flightDuration = (byte) (ticksToTarget > 350 ? 1 + (ticksToTarget - 350) / 75 : 1);
			bool thrown = weapon.Object_Type == (int) eObjectType.Thrown;

			foreach (GamePlayer viewer in player.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
			{
				if (thrown)
					viewer.Out.SendInterruptAnimation(player);

				viewer.Out.SendCombatAnimation(player, target, (ushort) weapon.Model, 0x00, viewer.Out.BowShoot, flightDuration, 0x00, target.HealthPercent);
			}

			WeaponAction shot = new(player, target, weapon, effectiveness, full, type, ammo) { ActionMissChance = miss };
			player.attackComponent.weaponAction = shot;
			player.Stealth(false);

			if (ticksToTarget > 0)
				new ECSGameTimer(player, new ECSGameTimer.ECSTimerCallback(shot.Execute), ticksToTarget);
			else
				shot.Execute();

			state.NextShotAt = GameLoop.GameLoopTime + ShotDelayMs;
			Send(player, $"shot|{quality}|{(critical ? 1 : 0)}");
		}

		public readonly record struct ShotNumbers(double Effectiveness, double CritEffectiveness, double CritChance, double Miss);

		/// <summary>
		/// A shot by its draw: f = share of the full draw (0..1), over = overdrawn. Normal: early 35%..100% damage and
		/// 3%..53% miss, full 100% / 3%, overdrawn 160% / 40%. Critical: crit chance f^4 early (always when full or
		/// overdrawn), the critical shot's damage (critMod; x1.3 overdrawn), miss 5%..65% early, 3% full, 45% overdrawn.
		/// </summary>
		public static ShotNumbers ShotFor(double f, bool over, bool crit, double critMod)
		{
			f = Math.Clamp(f, 0.0, 1.0);
			double early = 0.35 + 0.65 * f;

			if (crit)
			{
				double chance = over || f >= 1.0 ? 1.0 : Math.Pow(f, 4);
				double miss = over ? OverdrawMiss + 0.05 : f >= 1.0 ? FullDrawMiss : 0.05 + (1 - f) * 0.6;
				return new(over ? early * 1.3 : early, over ? critMod * 1.3 : critMod, chance, miss);
			}

			double eff = over ? OverdrawDamage : f >= 1.0 ? 1.0 : early;
			double normalMiss = over ? OverdrawMiss : f >= 1.0 ? FullDrawMiss : FullDrawMiss + (1 - f) * 0.5;
			return new(eff, eff, 0.0, normalMiss);
		}

		/// <summary>/ac quiver 1-4 | next | prev: the quiver slot your arrows come from (the quiver window, Shift + wheel).</summary>
		public static void SelectQuiver(GamePlayer player, string which)
		{
			eActiveQuiverSlot[] slots = [eActiveQuiverSlot.First, eActiveQuiverSlot.Second, eActiveQuiverSlot.Third, eActiveQuiverSlot.Fourth];
			eInventorySlot[] items = [eInventorySlot.FirstQuiver, eInventorySlot.SecondQuiver, eInventorySlot.ThirdQuiver, eInventorySlot.FourthQuiver];
			int current = Array.IndexOf(slots, player.rangeAttackComponent.ActiveQuiverSlot);

			if (which is "next" or "prev")
			{
				int dir = which == "next" ? 1 : -1;
				int from = current >= 0 ? current : (dir > 0 ? -1 : 4);

				for (int i = 1; i <= 4; i++)
				{
					int at = ((from + dir * i) % 4 + 4) % 4;

					if (player.Inventory.GetItem(items[at]) != null && at != current)
					{
						player.SwitchQuiver(slots[at], true);
						return;
					}
				}

				player.Out.SendMessage(current >= 0 ? "You have no other arrows in your quiver." : "Your quiver is empty.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}

			if (int.TryParse(which, out int n) && n is >= 1 and <= 4)
			{
				if (player.Inventory.GetItem(items[n - 1]) == null)
					player.Out.SendMessage($"The quiver slot {n} is empty!", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				else
					player.SwitchQuiver(slots[n - 1], true);
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
			sb.AppendLine($"Timed parry takes {ParryFactor(player) * 100:0}% of a blow (Parry {player.GetModifiedSpecLevel(Specs.Parry)}); window {Window(player, eActionDefense.Parry)} ms; a miss in combat costs {MissedDefenseCost(player, eActionDefense.Parry)} endurance.");

			if (HasShield(player))
				sb.AppendLine($"Timed block takes {BlockFactor(player) * 100:0}% (Shields {player.GetModifiedSpecLevel(Specs.Shields)}); window {Window(player, eActionDefense.Block)} ms; a miss costs {MissedDefenseCost(player, eActionDefense.Block)}.");

			sb.AppendLine($"Dodge avoids the whole blow (Evade {player.GetAbilityLevel(Abilities.Evade)}); window {Window(player, eActionDefense.Dodge)} ms; a miss costs {MissedDefenseCost(player, eActionDefense.Dodge)}.");
			sb.Append($"After a press, {ParryCooldownMs} ms past its window before the next - at once after one that caught a blow.");
			return sb.ToString();
		}
	}
}
