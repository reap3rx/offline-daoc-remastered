/*
 * Action Combat: an opt-in, player-only way to fight in melee (the owner's design, 2026-10-26).
 *
 * Classic DAoC rules stay for everyone else - mobs, gamebots, companions, and any player who leaves it off.
 * With it on (/ac on, the Godot client's F9):
 *   - No auto-attack, and nothing queues (owner 2026-11-01): a click does something only if it can right now.
 *     A plain swing (/ac swing) can come as soon as QuickMinMs after the last one - 0.75 s for the quickest weapons
 *     to 1.75 s for the slowest - and lands for the share of its damage the weapon has recovered: full damage once
 *     its whole classic swing time has passed, less before (damage per second is the classic game's either way).
 *   - Styles want the whole swing time since the last blow (a reactive excepted: it answers its opening at once).
 *     Their lights (and the held attack's glow) come on only when a press would fire one; a press while dark does
 *     nothing. Holding the attack button and letting go fires the best anytime style (/ac style anytime); the
 *     Position, Reactive and Chain buttons fire the best usable style of that kind.
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
 *   - Swinging early tires you (owner 2026-11-09): in combat, a plain swing before the weapon's whole swing time costs
 *     endurance - QuickSwingMaxEnduranceShare (5%) of your maximum at its soonest, nothing at the whole swing time;
 *     with none left you still swing. Dual wielders' plain swings come round faster with Dual Wield / Celtic Dual /
 *     Left Axe spec (PlainSwingMs).
 *   - Fighting several at once (owner 2026-11-09): a timed dodge / parry / block that catches a blow starts a chain -
 *     for a short window after it, blows from OTHER monsters are turned aside the same way, one per monster, as many
 *     monsters as the chain has charges: Evade I-VII 1-7 charges over 0.5-2 s; Riposte 1-7 (Parry 7, 14, 21, 29,
 *     36, 43, 50) over 0.75-3 s; Shields 1-50 0-7 charges plus 1 / 2 / 3 for a small / medium / large shield over
 *     1-4 s. A parry chain and a small shield cover your front, a medium shield 270 degrees, a large one all round;
 *     a dodge chain any side. Every parry (timed or chained) by someone with Riposte 1+ strikes back: half an
 *     off-hand swing dual wielding, else 15% of a main-hand swing.
 *   - What a parry / block saves depends on spec and on the armor the blow lands on (owner 2026-11-09): its armor
 *     rating (AF with your buffs, raised by its absorb) against a buffed plate wearer's of your level. At spec 50,
 *     a block saves 85% (cloth) to 95% (buffed plate), a parry 70% to 85%; never all of it.
 * The client and server talk through "#AC|..." system lines the Godot client takes out of the chat.
 */
using System;
using System.Collections.Generic;
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
		public long CounterAt = -100000;       // a caster's staff counter released (CasterCounter)
		public bool CounterAnswered;
		public string LastWindows = "";
		public bool Guarding;
		public bool FumblePending;
		// The multi-foe chain started by a timed defense that caught a blow (ActionCombat.StartChain).
		public eActionDefense ChainKind;
		public long ChainUntil;
		public int ChainLeft;
		public GameLiving ChainFrom;
		public HashSet<GameLiving> ChainUsed = new();
		// A reaction answers one opening: the blow you parried / blocked / dodged (the enemy's attack), or your own
		// blow it turned aside. Once a reactive style is used on it, it is spent until a new one comes.
		public AttackData SpentEnemyOpening;
		public AttackData SpentOwnOpening;
		// The last style's blow (WeaponAction): chains follow it, plain swings don't count (owner 2026-11-10).
		public AttackData LastStyleData;
		public long LastStyleAt = -100000;      // when it went
		public int LastStyleFullMs = 1;         // the weapon's whole swing time then
		public long LastPositionalAt = -100000; // when your last positional style went (its own reuse clock)
		public long FumbledUntil;
		public long LastSwingAt = -100000;     // when your last blow (or whiff) went
		public int LastSwingFullMs = 1;         // that weapon's whole swing time then (full damage, styles ready)
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
		// The player's own style picks per slot (ActionCombat.StyleSlots): style ID; a slot not here is "best usable".
		public Dictionary<string, int> StylePicks;
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

		// ------------------------------------------------------------------ early swings tire you (owner 2026-11-09)

		public const double QuickSwingMaxEnduranceShare = 0.05;   // (owner 2026-11-09: 15% was too much)

		/// <summary>The share of maximum endurance a plain swing this long after the last blow costs: the most at its
		/// soonest, falling evenly to nothing at the weapon's whole swing time.</summary>
		public static double QuickSwingEnduranceShare(long elapsedMs, int fullMs)
		{
			if (fullMs <= 0 || elapsedMs >= fullMs)
				return 0.0;

			int soonest = Math.Min(QuickMinMs(fullMs), fullMs - 1);

			if (elapsedMs <= soonest)
				return QuickSwingMaxEnduranceShare;

			return QuickSwingMaxEnduranceShare * (fullMs - elapsedMs) / (double) (fullMs - soonest);
		}

		/// <summary>What a plain swing now costs this player (0 out of combat or at the whole swing time). Never a reason
		/// not to swing (owner 2026-11-09: "still able to do a basic swing even if their stamina is gone") - it takes
		/// what endurance there is.</summary>
		public static int QuickSwingCost(GamePlayer player)
		{
			if (!player.InCombat)
				return 0;

			double share = QuickSwingEnduranceShare(SinceLastSwing(player), PlainSwingMs(player));
			return share <= 0 ? 0 : (int) Math.Ceiling(player.MaxEndurance * share);
		}

		// ------------------------------------------------------------------ fighting several at once (owner 2026-11-09)

		public static readonly int[] RiposteSpecs = { 7, 14, 21, 29, 36, 43, 50 };

		public static int RiposteRank(int parrySpec)
		{
			int rank = 0;

			foreach (int at in RiposteSpecs)
			{
				if (parrySpec >= at)
					rank++;
			}

			return rank;
		}

		/// <summary>Evade I-VII: 1-7 other monsters within 0.5-2 s of the dodge.</summary>
		public static (int Charges, int WindowMs) EvadeChainFor(int evade)
		{
			int e = Math.Clamp(evade, 0, 7);
			return e == 0 ? (0, 0) : (e, 500 + (e - 1) * 250);
		}

		/// <summary>Riposte 1-7: 1-7 other monsters within 0.75-3 s of the parry.</summary>
		public static (int Charges, int WindowMs) ParryChainFor(int parrySpec) => ParryChainForRank(RiposteRank(parrySpec));

		public static (int Charges, int WindowMs) ParryChainForRank(int rank)
		{
			int r = Math.Clamp(rank, 0, 7);
			return r == 0 ? (0, 0) : (r, 750 + (r - 1) * 375);
		}

		/// <summary>The Riposte ability's level (I-VII): trained with Parry at 7, 14, 21, 29, 36, 43 and 50 - the database's
		/// SpecXAbility rows (db-changes 2026-11-09-riposte-ability.sql), so it shows in the trainer's preview and the
		/// abilities list like any other (owner 2026-11-09).</summary>
		public const string RiposteAbility = "Riposte";

		public static int RiposteLevel(GamePlayer player) => player.GetAbilityLevel(RiposteAbility);

		/// <summary>Shields 1-50: 0-7 other monsters, plus the shield's size (1 small, 2 medium, 3 large), within 1-4 s.</summary>
		public static (int Charges, int WindowMs) BlockChainFor(int shieldSpec, int shieldSize)
		{
			if (shieldSpec <= 0)
				return (0, 0);

			int s = Math.Clamp(shieldSpec, 1, 50);
			return ((s - 1) * 7 / 49 + Math.Clamp(shieldSize, 1, 3), 1000 + (s - 1) * 3000 / 49);
		}

		/// <summary>How far round a chained block reaches: small shield the front, medium 270 degrees, large all round.</summary>
		public static int BlockChainArc(int shieldSize) => shieldSize >= 3 ? 360 : shieldSize == 2 ? 270 : 180;

		private static int ShieldSize(GamePlayer player)
		{
			DbInventoryItem left = player.ActiveLeftWeapon;
			return left == null ? 1 : Math.Clamp(left.Type_Damage, 1, 3);
		}

		/// <summary>A timed defense caught a blow from `from`: a new chain for the others (replacing any running).</summary>
		private static void StartChain(GamePlayer player, ActionCombatState state, eActionDefense kind, GameLiving from, long now)
		{
			(int charges, int window) = kind switch
			{
				eActionDefense.Dodge => EvadeChainFor(player.GetAbilityLevel(Abilities.Evade)),
				eActionDefense.Block => BlockChainFor(player.GetModifiedSpecLevel(Specs.Shields), ShieldSize(player)),
				eActionDefense.Parry => ParryChainForRank(RiposteLevel(player)),
				_ => (0, 0)
			};

			state.ChainKind = kind;
			state.ChainLeft = charges;
			state.ChainUntil = charges > 0 ? now + window : 0;
			state.ChainFrom = from;
			state.ChainUsed.Clear();
		}

		/// <summary>A blow the running chain turns aside: a different monster from the one that started it, one not yet
		/// turned aside in this chain, inside the window, on the side the chain covers.</summary>
		private static eActionDefense ChainFor(GamePlayer player, ActionCombatState state, AttackData ad, long now)
		{
			if (state.ChainLeft <= 0 || now > state.ChainUntil || ad.Attacker == state.ChainFrom || state.ChainUsed.Contains(ad.Attacker))
				return eActionDefense.None;

			switch (state.ChainKind)
			{
				case eActionDefense.Dodge:
					return eActionDefense.Dodge;
				case eActionDefense.Parry:
					return ad.IsMeleeAttack && player.IsObjectInFront(ad.Attacker, 180) && player.ActiveWeapon != null
						? eActionDefense.Parry : eActionDefense.None;
				case eActionDefense.Block:
				{
					if (!HasShield(player))
						return eActionDefense.None;

					int arc = BlockChainArc(ShieldSize(player));
					return arc >= 360 || player.IsObjectInFront(ad.Attacker, arc) ? eActionDefense.Block : eActionDefense.None;
				}
			}

			return eActionDefense.None;
		}

		/// <summary>The riposte: every parry by someone with Riposte 1+ strikes the parried monster back a moment later.
		/// Dual wielding, half an off-hand swing; else 15% of a main-hand swing. No styles, procs or damage adds.</summary>
		public const double RiposteDualWieldShare = 0.5;
		public const double RiposteShare = 0.15;
		public const int RiposteDelayMs = 250;

		private static void Riposte(GamePlayer player, GameLiving attacker)
		{
			if (attacker == null || RiposteLevel(player) <= 0)
				return;

			new ECSGameTimer(player, _ =>
			{
				if (!player.IsAlive || !attacker.IsAlive || player.IsIncapacitated || !player.attackComponent.AttackState ||
					!player.IsWithinRadius(attacker, player.attackComponent.AttackRange + 50))
					return 0;

				DbInventoryItem main = player.ActiveWeapon;
				DbInventoryItem left = player.ActiveLeftWeapon;
				bool dual = left != null && (eObjectType) left.Object_Type is not eObjectType.Shield && main != null &&
					player.attackComponent.CanUseLefthandedWeapon;
				DbInventoryItem weapon = dual ? left : main;

				if (weapon == null)
					return 0;

				double share = dual ? RiposteDualWieldShare : RiposteShare;
				int speed = player.attackComponent.AttackSpeed(weapon);
				WeaponAction action = new(player, attacker, weapon, null, share, speed, null);
				AttackData counter = player.attackComponent.LivingMakeAttack(action, attacker, weapon, null, share, speed, false, true);

				if (counter.AttackResult is eAttackResult.HitUnstyled or eAttackResult.HitStyle)
				{
					player.DealDamage(counter);
					player.Out.SendMessage($"You riposte {attacker.GetName(0, false)} for {counter.Damage + counter.CriticalDamage} damage!", eChatType.CT_YouHit, eChatLoc.CL_SystemWindow);
					Send(player, $"riposte|{attacker.ObjectID}|{counter.Damage + counter.CriticalDamage}");
				}

				return 0;
			}, RiposteDelayMs);
		}
		// A plain swing's soonest (owner 2026-11-01): 0.75 s for the quickest weapons (a 2.0 s swing time or less) to
		// 1.75 s for the slowest (5.5 s and up), in between by the weapon's swing time now (quickness, haste in it).
		public const int QuickMinFastMs = 750;
		public const int QuickMinSlowMs = 1750;

		// The power attack (an anytime style) about 1 s after the last blow (owner 2026-11-01: holding the button is the
		// wait), never sooner than a plain swing could go; its damage grows over the swing time like a plain swing's.
		public const int AnytimeMinMs = 1000;

		public static int AnytimeSoonestMs(int fullMs) => Math.Max(AnytimeMinMs, QuickMinMs(fullMs));

		public static int QuickMinMs(int fullMs) =>
			Math.Clamp(QuickMinFastMs + (int) ((fullMs - 2000) * (QuickMinSlowMs - QuickMinFastMs) / 3500.0), QuickMinFastMs, QuickMinSlowMs);

		/// <summary>The share of a plain swing's damage after this long since the last blow (full at the whole swing time).</summary>
		public static double QuickDamageFor(long elapsedMs, int fullMs) =>
			fullMs <= 0 ? 1.0 : Math.Clamp(elapsedMs / (double) fullMs, 0.0, 1.0);

		/// <summary>The weapon's whole swing time now (ms).</summary>
		public static int FullSwingMs(GamePlayer player) =>
			Math.Max(1, player.attackComponent.AttackSpeed(player.ActiveWeapon, player.ActiveLeftWeapon));

		/// <summary>
		/// A plain swing's whole time (full damage) with two weapons (owner 2026-11-09: "if you're trained high in any of
		/// the dual wield skill lines, that basic swing timer should be faster and faster"): Dual Wield, Celtic Dual or
		/// Left Axe at 50 bring it in by DualWieldQuickestShare. The off-hand still joins a share of swings by the classic
		/// left-hand chance. Styles keep the whole swing time.
		/// </summary>
		public const double DualWieldQuickestShare = 0.25;

		public static double DualWieldSwingFactor(int dualSpec) =>
			1.0 - DualWieldQuickestShare * Math.Clamp(dualSpec, 0, 50) / 50.0;

		public static int DualWieldSpec(GamePlayer player)
		{
			DbInventoryItem left = player.ActiveLeftWeapon;

			if (left == null || (eObjectType) left.Object_Type is eObjectType.Shield || player.ActiveWeapon == null ||
				!player.attackComponent.CanUseLefthandedWeapon || player.ActiveWeaponSlot is not eActiveWeaponSlot.Standard)
				return 0;

			return Math.Max(player.GetModifiedSpecLevel(Specs.Dual_Wield),
				Math.Max(player.GetModifiedSpecLevel(Specs.Celtic_Dual), player.GetModifiedSpecLevel(Specs.Left_Axe)));
		}

		public static int PlainSwingMs(GamePlayer player) =>
			Math.Max(1, (int) (FullSwingMs(player) * DualWieldSwingFactor(DualWieldSpec(player))));

		public static long SinceLastSwing(GamePlayer player) => GameLoop.GameLoopTime - Get(player).LastSwingAt;

		/// <summary>A plain swing could go now (its soonest time past, not stumbling).</summary>
		public static bool SwingReady(GamePlayer player)
		{
			ActionCombatState state = Get(player);
			return GameLoop.GameLoopTime >= state.FumbledUntil && SinceLastSwing(player) >= QuickMinMs(PlainSwingMs(player));
		}

		/// <summary>The weapon has recovered fully: a style could go now (not stumbling).</summary>
		public static bool Recovered(GamePlayer player)
		{
			ActionCombatState state = Get(player);
			return GameLoop.GameLoopTime >= state.FumbledUntil && SinceLastSwing(player) >= Math.Min(state.LastSwingFullMs, FullSwingMs(player));
		}

		/// <summary>A blow (or a whiff) just went: the clocks for the next swing and the next style start now.</summary>
		public static void MarkSwing(GamePlayer player, int fullMs)
		{
			ActionCombatState state = Get(player);
			state.LastSwingAt = GameLoop.GameLoopTime;
			state.LastSwingFullMs = Math.Max(1, fullMs);
			int plain = Math.Max(1, (int) (state.LastSwingFullMs * DualWieldSwingFactor(DualWieldSpec(player))));   // (the plain swing's arc)
			Send(player, $"timer|{plain}|{QuickMinMs(plain)}|{AnytimeSoonestMs(state.LastSwingFullMs)}");
		}

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
			NewClient.Send(player, Prefix + line);
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

			// Too soon after the last blow: nothing (no queue - press again when it can go).
			if (!SwingReady(player))
				return;

			if (!EnsureAttacking(player))
				return;

			state.Guarding = false;
			state.SwingQueued = true;
			player.styleComponent.NextCombatStyle = null;
			player.styleComponent.NextCombatBackupStyle = null;
			player.attackComponent.attackAction?.ExpediteMeleeTick();
		}

		/// <summary>"anytime", "position", "reactive" or "chain": queue the best usable style of that kind.</summary>
		public static void QueueStyle(GamePlayer player, string kind)
		{
			ActionCombatState state = Get(player);
			Style style = Resolve(player, kind);

			// Position / Reactive / Chain do nothing unless their condition is met (no swing, no air punch).
			if (style == null && kind != "anytime")
				return;

			// No anytime style ready (none known, or the weapon not recovered): the release is a plain swing if one
			// can go now (the client sends the style only while its glow is on; this covers a race with the lights).
			if (style == null || !StyleReady(player, kind))
			{
				if (kind == "anytime")
					QueueSwing(player);
				return;
			}

			if (!EnsureAttacking(player))
				return;

			state.Guarding = false;
			state.SwingQueued = true;
			player.styleComponent.NextCombatStyle = style;
			player.styleComponent.NextCombatBackupStyle = null;
			player.styleComponent.NextCombatStyleTime = GameLoop.GameLoopTime;
			player.attackComponent.attackAction?.ExpediteMeleeTick();   // it goes now - nothing waits
		}

		/// <summary>
		/// A style of this kind could go now (owner 2026-11-10: "light attacks should not interrupt or be tied into the
		/// style use timing at all"):
		///   reactive - at once when its opening comes;
		///   position - at once when you are in position; its reuse clock starts only when a positional goes (the
		///              weapon's whole swing time, quickness and haste in it);
		///   chain    - the soonest a plain swing could follow the style it chains from (QuickMinMs: 0.75 s for the
		///              quickest weapons to 1.75 s for the slowest, by the swing time now), counted from that style;
		///   anytime  - as before, from the last blow.
		/// Light swings in between don't hold a style back, beyond StyleAfterSwingMs for the swing to finish.
		/// </summary>
		public const int StyleAfterSwingMs = 450;

		public static bool StyleReady(GamePlayer player, string kind)
		{
			ActionCombatState state = Get(player);
			long now = GameLoop.GameLoopTime;

			if (now < state.FumbledUntil)
				return false;

			if (kind == "anytime")
				return SinceLastSwing(player) >= AnytimeSoonestMs(Math.Min(state.LastSwingFullMs, FullSwingMs(player)));

			return StyleClockReady(kind, now, state.LastSwingAt, state.LastStyleAt, state.LastPositionalAt,
				state.LastStyleFullMs, FullSwingMs(player));
		}

		/// <summary>The style clocks for a reactive, a positional or a chain (see StyleReady); fullMs the weapon's whole
		/// swing time now, lastStyleFullMs the one when the last style went.</summary>
		public static bool StyleClockReady(string kind, long now, long lastSwingAt, long lastStyleAt, long lastPositionalAt,
			int lastStyleFullMs, int fullMs) => kind switch
		{
			"reactive" => true,
			"position" => now - lastSwingAt >= StyleAfterSwingMs && now - lastPositionalAt >= fullMs,
			"chain" => now - lastSwingAt >= StyleAfterSwingMs && now - lastStyleAt >= ChainSoonestMs(lastStyleFullMs, fullMs),
			_ => now - lastSwingAt >= fullMs
		};

		/// <summary>How soon a chain may follow the style before it: by the weapon's swing time (speed, quickness, haste).</summary>
		public static int ChainSoonestMs(int lastStyleFullMs, int fullMs) => QuickMinMs(Math.Min(lastStyleFullMs, fullMs));

		/// <summary>A style's blow went (WeaponAction): the chains follow it, a positional starts its reuse clock.</summary>
		public static void MarkStyle(GamePlayer player, AttackData attackData)
		{
			ActionCombatState state = Get(player);
			state.LastStyleData = attackData;
			state.LastStyleAt = GameLoop.GameLoopTime;
			state.LastStyleFullMs = FullSwingMs(player);

			if (attackData.Style != null && KindOf(attackData.Style) == "position")
				state.LastPositionalAt = GameLoop.GameLoopTime;
		}

		/// <summary>The style a chain on this target follows: none if the last style was on someone else (owner
		/// 2026-11-10: "sometimes the chain style will be available on the next mob without having done the first style").</summary>
		public static AttackData ChainOpening(GamePlayer player, GameLiving target)
		{
			AttackData last = Get(player).LastStyleData;
			return last != null && last.Target == target ? last : null;
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

				if (!PickAllows(player, style, weapon))
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

		/// <summary>The reaction windows the enemy's blows opened are spent (your own last blow is the power attack now,
		/// so what it opens is new).</summary>
		public static void CloseReactions(GamePlayer player)
		{
			ActionCombatState state = Get(player);
			AttackData enemy = (player.TargetObject as GameLiving)?.attackComponent?.attackAction?.LastAttackData;

			if (enemy != null)
				state.SpentEnemyOpening = enemy;
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

			state.NextReadyCheck = now + 100;
			StringBuilder sb = new("ready|");

			// lit only when a press would fire it right now (owner 2026-11-01: no queue - the light is the go)
			foreach (string kind in new[] { "position", "reactive", "chain", "anytime" })
				sb.Append(StyleReady(player, kind) && Resolve(player, kind) != null ? '1' : '0');

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
			state.FumblePending = true;                   // (PlayerAttackAction: the stumble - twice the swing time)
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

			bool block = HasShield(player) && !parryOnly && CanDefend(player, eActionDefense.Block);
			eActionDefense kind = block ? eActionDefense.Block : eActionDefense.Parry;

			if (!CanDefend(player, kind))
			{
				state.ParryReadyAt = now + ParryCooldownMs;
				player.Out.SendMessage("You have not learned to parry.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}

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

			if (!CanDefend(player, eActionDefense.Dodge))
			{
				state.DodgeReadyAt = now + ParryCooldownMs;
				player.Out.SendMessage("You have not learned to evade.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}

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
		/// 0: this character can't do it at all (owner 2026-10-30: classes that never learn parry, evade or shields -
		/// casters - can't parry, dodge or block in action combat either).
		public static int Window(GamePlayer player, eActionDefense kind)
		{
			if (!CanDefend(player, kind))
				return 0;

			return kind switch
			{
				eActionDefense.Block => BlockWindowFor(player.GetModifiedSpecLevel(Specs.Shields), RealmAbilityLevel<RealmAbilities.MasteryOfBlocking>(player)),
				eActionDefense.Dodge => DodgeWindowFor(player.GetAbilityLevel(Abilities.Evade), RealmAbilityLevel<RealmAbilities.AtlasOF_Dodger>(player)),
				_ => ParryWindowFor(player.GetModifiedSpecLevel(Specs.Parry), RealmAbilityLevel<RealmAbilities.MasteryOfParrying>(player))
			};
		}

		/// <summary>Whether the character has the skill at all: Parry spec, Shields spec, the Evade ability.</summary>
		public static bool CanDefend(GamePlayer player, eActionDefense kind) => kind switch
		{
			eActionDefense.Block => player.GetBaseSpecLevel(Specs.Shields) > 0,
			eActionDefense.Dodge => player.GetAbilityLevel(Abilities.Evade) > 0,
			eActionDefense.Parry => player.GetBaseSpecLevel(Specs.Parry) > 0,
			_ => true
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

			string line = $"windows|{Window(player, eActionDefense.Parry)}|{Window(player, eActionDefense.Block)}|{Window(player, eActionDefense.Dodge)}|{ParryCooldownMs}|{(CasterCounter.CanCounter(player) ? CasterCounter.Cost(player) : 0)}";

			if (!force && line == state.LastWindows)
				return;

			state.LastWindows = line;
			Send(player, line);
		}

		public static void SetGuard(GamePlayer player, bool on)
		{
			Get(player).Guarding = on && player.IsAlive;
		}

		/// <summary>The armor the blow lands on, 0..1: its rating (AF with your buffs, raised by its absorb as the
		/// classic damage formula does) against a buffed plate wearer's of your level (owner 2026-11-09: "base this on
		/// the Armor Factor stat versus the armor type ... since you can mix types of armor and there are AF buffs").</summary>
		public const double FullArmorRatingPerLevel = 3.6;

		public static double ArmorScore(GamePlayer player, eArmorSlot slot)
		{
			if (slot is eArmorSlot.NOTSET)
				return 0;

			return ArmorScoreFor(player.GetArmorAF(slot), player.GetArmorAbsorb(slot), player.Level);
		}

		public static double ArmorScoreFor(double af, double absorb, int level) =>
			Math.Clamp(af / Math.Max(0.05, 1 - absorb) / (FullArmorRatingPerLevel * Math.Max(1, level)), 0.0, 1.0);

		/// <summary>What a block saves at Shields 50: 85% on cloth to 95% on buffed plate (owner 2026-11-09).</summary>
		public static double BlockSavedAt50(double armor) => 0.737 + 0.213 * Math.Sqrt(Math.Clamp(armor, 0, 1));

		/// <summary>What a parry saves at Parry 50: 70% on cloth to 85% on buffed plate (a parry ripostes instead).</summary>
		public static double ParrySavedAt50(double armor) => 0.531 + 0.319 * Math.Sqrt(Math.Clamp(armor, 0, 1));

		/// <summary>The share of a parried blow still taken: Parry 1 saves half of what Parry 50 would; untrained 80% taken.</summary>
		public static double ParryFactorFor(int spec, double armor)
		{
			if (spec <= 0)
				return 0.8;

			double k = 0.5 + 0.5 * (Math.Clamp(spec, 1, 50) - 1) / 49.0;
			return 1.0 - ParrySavedAt50(armor) * k;
		}

		/// <summary>The share of a blocked blow still taken: Shields 1 saves two thirds of what Shields 50 would; untrained 50%.</summary>
		public static double BlockFactorFor(int spec, double armor)
		{
			if (spec <= 0)
				return 0.5;

			double k = 2.0 / 3.0 + (1.0 / 3.0) * (Math.Clamp(spec, 1, 50) - 1) / 49.0;
			return 1.0 - BlockSavedAt50(armor) * k;
		}

		public static double ParryFactor(GamePlayer player, AttackData ad) =>
			ParryFactorFor(player.GetModifiedSpecLevel(Specs.Parry), ArmorScore(player, ad.ArmorHitLocation));

		public static double BlockFactor(GamePlayer player, AttackData ad) =>
			BlockFactorFor(player.GetModifiedSpecLevel(Specs.Shields), ArmorScore(player, ad.ArmorHitLocation));

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
			CasterCounter.OnBlow(player, state, ad, now);      // (a caster's staff counter: the blow still lands)
			bool inFront = player.IsObjectInFront(ad.Attacker, 180);

			if (now - state.DodgeAt <= state.DodgeWindowMs)
			{
				state.DodgeAnswered = true;
				state.DodgeReadyAt = now;        // (a dodge that avoided a blow can be followed at once)
				StartChain(player, state, eActionDefense.Dodge, ad.Attacker, now);
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
					StartChain(player, state, eActionDefense.Block, ad.Attacker, now);
					ad.ActionDefense = eActionDefense.Block;
					ad.ActionDamageFactor = BlockFactor(player, ad);
					ad.BlockChance = 100;
					return eAttackResult.Blocked;
				}

				if (ad.IsMeleeAttack)
				{
					StartChain(player, state, eActionDefense.Parry, ad.Attacker, now);
					ad.ActionDefense = eActionDefense.Parry;
					ad.ActionDamageFactor = ParryFactor(player, ad);
					ad.ParryChance = 100;
					return eAttackResult.Parried;
				}
			}

			// The chain a timed defense started: other monsters' blows turned aside the same way, one each.
			eActionDefense chained = ChainFor(player, state, ad, now);

			if (chained is not eActionDefense.None)
			{
				state.ChainLeft--;
				state.ChainUsed.Add(ad.Attacker);
				ad.ActionAuto = true;
				ad.ActionDefense = chained;

				switch (chained)
				{
					case eActionDefense.Dodge:
						ad.EvadeChance = 100;
						return eAttackResult.Evaded;
					case eActionDefense.Block:
						ad.ArmorHitLocation = player.CalculateArmorHitLocation(ad);
						ad.ActionDamageFactor = BlockFactor(player, ad);
						ad.BlockChance = 100;
						return eAttackResult.Blocked;
					default:
						ad.ArmorHitLocation = player.CalculateArmorHitLocation(ad);
						ad.ActionDamageFactor = ParryFactor(player, ad);
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
					player.Out.SendMessage(ad.ActionAuto
						? $"Riposte! You turn {ad.Attacker.GetName(0, false)}'s blow aside too: {ad.ActionMitigated} damage saved, {ad.Damage} taken."
						: $"Timed parry! You turn {ad.Attacker.GetName(0, false)}'s blow aside: {ad.ActionMitigated} damage saved, {ad.Damage} taken.", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
					Send(player, $"def|parry|{ad.Damage}|{ad.ActionMitigated}" + (ad.ActionAuto ? "|auto" : ""));
					Riposte(player, ad.Attacker);
					break;
				case eActionDefense.Block:
					player.Out.SendMessage(ad.ActionAuto
						? $"Your shield catches {ad.Attacker.GetName(0, false)}'s blow too: {ad.ActionMitigated} damage saved, {ad.Damage} taken."
						: $"Timed block! You catch {ad.Attacker.GetName(0, false)}'s blow on your shield: {ad.ActionMitigated} damage saved, {ad.Damage} taken.", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);
					Send(player, $"def|block|{ad.Damage}|{ad.ActionMitigated}" + (ad.ActionAuto ? "|auto" : ""));
					break;
				case eActionDefense.Dodge:
					if (ad.ActionAuto)
						player.Out.SendMessage($"You slip {ad.Attacker.GetName(0, false)}'s blow too!", eChatType.CT_Missed, eChatLoc.CL_SystemWindow);

					Send(player, ad.ActionAuto ? "def|dodge|0|0|auto" : "def|dodge|0");
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

		// ------------------------------------------------------------------ style picks (owner 2026-10-30)
		// The Action Combat Styles window: which style each button / reaction fires. Unpicked slots fire the best
		// usable style of their kind, as before. A pick stands only while the weapon in hand can do it.

		public const string PicksKey = "ActionCombatStyles";
		public static readonly string[] StyleSlots = { "anytime", "parry", "block", "dodge", "front", "side", "back" };

		/// <summary>Which pick slot a style belongs to, or null (chains, reactions to your own avoided blows).</summary>
		public static string SlotOf(Style style)
		{
			if (style.OpeningRequirementType is Style.eOpening.Positional)
			{
				return (Style.eOpeningPosition) style.OpeningRequirementValue switch
				{
					Style.eOpeningPosition.Back => "back",
					Style.eOpeningPosition.Side => "side",
					_ => "front"
				};
			}

			if (style.OpeningRequirementType is Style.eOpening.Defensive)
			{
				return style.AttackResultRequirement switch
				{
					Style.eAttackResultRequirement.Parry => "parry",
					Style.eAttackResultRequirement.Block => "block",
					Style.eAttackResultRequirement.Evade => "dodge",
					_ => null
				};
			}

			return KindOf(style) == "anytime" ? "anytime" : null;
		}

		private static Dictionary<string, int> Picks(GamePlayer player)
		{
			ActionCombatState state = Get(player);

			if (state.StylePicks != null)
				return state.StylePicks;

			state.StylePicks = new Dictionary<string, int>();
			DbCoreCharacterXCustomParam record = DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
				DB.Column("DOLCharactersObjectId").IsEqualTo(player.ObjectId).And(DB.Column("KeyName").IsEqualTo(PicksKey)));

			foreach (string pair in (record?.Value ?? "").Split(';', StringSplitOptions.RemoveEmptyEntries))
			{
				string[] kv = pair.Split('=');

				if (kv.Length == 2 && int.TryParse(kv[1], out int id) && id > 0)
					state.StylePicks[kv[0]] = id;
			}

			return state.StylePicks;
		}

		/// <summary>False when the player picked another style for this style's slot (and can use that one with this weapon).</summary>
		public static bool PickAllows(GamePlayer player, Style style, DbInventoryItem weapon)
		{
			string slot = SlotOf(style);

			if (slot == null || !Picks(player).TryGetValue(slot, out int id) || id == style.ID)
				return true;

			foreach (Style known in player.styleComponent.GetStyleList())
			{
				if (known.ID != id)
					continue;

				DbInventoryItem w = (eObjectType) known.WeaponTypeRequirement is eObjectType.Shield ? player.ActiveLeftWeapon : player.ActiveWeapon;
				return w == null || !StyleProcessor.IsStyleForWeapon(known, player, w);   // the pick can't be done now: any will do
			}

			return true;                                    // the picked style is no longer known
		}

		public static void SetPick(GamePlayer player, string slot, string value)
		{
			if (Array.IndexOf(StyleSlots, slot) < 0)
				return;

			Dictionary<string, int> picks = Picks(player);

			if (int.TryParse(value, out int id) && id > 0)
				picks[slot] = id;
			else
				picks.Remove(slot);

			StringBuilder sb = new();

			foreach (KeyValuePair<string, int> kv in picks)
				sb.Append(kv.Key).Append('=').Append(kv.Value).Append(';');

			DbCoreCharacterXCustomParam record = DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
				DB.Column("DOLCharactersObjectId").IsEqualTo(player.ObjectId).And(DB.Column("KeyName").IsEqualTo(PicksKey)));

			if (record == null)
				GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(player.ObjectId, PicksKey, sb.ToString()));
			else
			{
				record.Value = sb.ToString();
				GameServer.Database.SaveObject(record);
			}

			SendStyleSlot(player, slot);
		}

		/// <summary>The window's contents: per slot, the pick (0 = best usable) and the styles you know for it.</summary>
		public static void SendStyles(GamePlayer player)
		{
			foreach (string slot in StyleSlots)
				SendStyleSlot(player, slot);

			Send(player, "styles|end");
		}

		private static void SendStyleSlot(GamePlayer player, string slot)
		{
			Picks(player).TryGetValue(slot, out int picked);
			StringBuilder sb = new($"styles|{slot}|{picked}");

			foreach (Style style in player.styleComponent.GetStyleList())
			{
				if (SlotOf(style) == slot)
					sb.Append('|').Append(style.ID).Append('~').Append(style.Name.Replace("|", "/").Replace("~", "-"));
			}

			Send(player, sb.ToString());
		}

		public static string Describe(GamePlayer player)
		{
			ActionCombatState state = Get(player);
			StringBuilder sb = new();
			sb.AppendLine($"Action combat is {(state.Enabled ? "ON" : "OFF")}.");
			double chest = ArmorScore(player, eArmorSlot.TORSO);
			(int pc, int pw) = ParryChainForRank(RiposteLevel(player));
			sb.AppendLine($"Timed parry takes {ParryFactorFor(player.GetModifiedSpecLevel(Specs.Parry), chest) * 100:0}% of a blow on your chest (Parry {player.GetModifiedSpecLevel(Specs.Parry)}, armor {chest * 100:0}%); window {Window(player, eActionDefense.Parry)} ms; a miss in combat costs {MissedDefenseCost(player, eActionDefense.Parry)} endurance. Riposte {RiposteLevel(player)}: {pc} more for {pw} ms.");

			if (HasShield(player))
			{
				(int bc, int bw) = BlockChainFor(player.GetModifiedSpecLevel(Specs.Shields), ShieldSize(player));
				sb.AppendLine($"Timed block takes {BlockFactorFor(player.GetModifiedSpecLevel(Specs.Shields), chest) * 100:0}% (Shields {player.GetModifiedSpecLevel(Specs.Shields)}); window {Window(player, eActionDefense.Block)} ms; a miss costs {MissedDefenseCost(player, eActionDefense.Block)}. Then {bc} more for {bw} ms, {BlockChainArc(ShieldSize(player))} degrees round.");
			}

			(int ec, int ew) = EvadeChainFor(player.GetAbilityLevel(Abilities.Evade));
			sb.AppendLine($"Dodge avoids the whole blow (Evade {player.GetAbilityLevel(Abilities.Evade)}); window {Window(player, eActionDefense.Dodge)} ms; a miss costs {MissedDefenseCost(player, eActionDefense.Dodge)}. Then {ec} more for {ew} ms.");
			sb.Append($"After a press, {ParryCooldownMs} ms past its window before the next - at once after one that caught a blow.");
			return sb.ToString();
		}
	}
}
