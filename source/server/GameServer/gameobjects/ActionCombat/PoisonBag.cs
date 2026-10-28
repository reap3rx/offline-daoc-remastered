/*
 * The poison bag (owner 2026-10-27): four bag slots in two sets - slots 1 + 2 and 3 + 4. The active set is put on your
 * weapons by itself, by the game's own poisoning rules (as GamePlayer.ApplyPoison: Envenom trained, a weapon that
 * takes poison, a poison of your Envenom level and your level, and not while in combat or mesmerized): the first
 * poison on the weapon in your hand (the right hand, or the two-hander drawn), the second on the left-hand weapon.
 * A weapon is poisoned again when its charges run out, or when the set changes (the other set's poison wiped off).
 * Shift + wheel (the client) switches sets.
 *
 * The bag HOLDS the poisons (owner 2026-10-27: they don't take backpack space): a stack dragged onto a bag slot leaves
 * the backpack for the bag; right-click puts it back. Any number of one poison fits in a slot. The contents are saved
 * on the character (DOLCharactersXCustomParam "PoisonBag": id:count,id:count,id:count,id:count;set), weightless.
 * An older bag (id,id,id,id;set - it only pointed at backpack stacks) takes those stacks in the first time it is used.
 * The client is told by "#AC|poisons|set|model~count~name|..." lines.
 */
using System;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
	public sealed class PoisonBagState
	{
		public string[] Templates = ["", "", "", ""];
		public int[] Counts = new int[4];
		public int Set;                        // 0: slots 1 + 2, 1: slots 3 + 4
		public bool Legacy;                    // saved by the first version: the stacks are still in the backpack
		public ECSGameTimer Timer;
		public string LastSent = "";
		public readonly HashSet<string> Warned = new();
	}

	public static class PoisonBag
	{
		public const string ParamKey = "PoisonBag";
		public const int TickMs = 2000;

		private static readonly Dictionary<GamePlayer, PoisonBagState> _states = new();
		private static readonly Dictionary<string, DbItemTemplate> _templates = new();
		private static readonly object _lock = new();

		public static PoisonBagState Get(GamePlayer player)
		{
			lock (_lock)
			{
				if (_states.TryGetValue(player, out PoisonBagState state))
					return state;

				state = Parse(Record(player)?.Value ?? "");
				_states[player] = state;
				return state;
			}
		}

		private static DbCoreCharacterXCustomParam Record(GamePlayer player)
		{
			return DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
				DB.Column("DOLCharactersObjectId").IsEqualTo(player.ObjectId).And(DB.Column("KeyName").IsEqualTo(ParamKey)));
		}

		/// <summary>"id:count,...;set" (or the first version's "id,id,id,id;set").</summary>
		public static PoisonBagState Parse(string value)
		{
			PoisonBagState state = new();
			string[] parts = value.Split(';');
			string[] entries = parts[0].Split(',');

			for (int i = 0; i < 4 && i < entries.Length; i++)
			{
				string e = entries[i].Trim();

				if (e.Length == 0)
					continue;

				int colon = e.LastIndexOf(':');

				if (colon < 0)
				{
					state.Templates[i] = e;
					state.Legacy = true;
					continue;
				}

				state.Templates[i] = e[..colon];
				state.Counts[i] = int.TryParse(e[(colon + 1)..], out int n) ? Math.Max(0, n) : 0;

				if (state.Counts[i] == 0)
					state.Templates[i] = "";
			}

			if (parts.Length > 1 && int.TryParse(parts[1], out int set))
				state.Set = set == 1 ? 1 : 0;

			return state;
		}

		public static string Format(PoisonBagState state) =>
			string.Join(",", Enumerable.Range(0, 4).Select(i =>
				string.IsNullOrEmpty(state.Templates[i]) || state.Counts[i] <= 0 ? "" : $"{state.Templates[i]}:{state.Counts[i]}")) + ";" + state.Set;

		private static void Save(GamePlayer player, PoisonBagState state)
		{
			string value = Format(state);
			DbCoreCharacterXCustomParam record = Record(player);

			if (record == null)
				GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(player.ObjectId, ParamKey, value));
			else
			{
				record.Value = value;
				GameServer.Database.SaveObject(record);
			}
		}

		private static DbItemTemplate Template(string id)
		{
			if (string.IsNullOrEmpty(id))
				return null;

			lock (_lock)
			{
				if (!_templates.TryGetValue(id, out DbItemTemplate t))
				{
					t = GameServer.Database.FindObjectByKey<DbItemTemplate>(id);
					_templates[id] = t;
				}

				return t;
			}
		}

		private static bool IsPoison(DbInventoryItem item) => item != null && item.Object_Type == (int) eObjectType.Poison;

		private static bool InBackpack(DbInventoryItem item) =>
			item != null && item.SlotPosition >= (int) eInventorySlot.FirstBackpack && item.SlotPosition <= (int) eInventorySlot.LastBackpack;

		private static void Clear(PoisonBagState state, int i)
		{
			state.Templates[i] = "";
			state.Counts[i] = 0;
		}

		/// <summary>Puts a bag slot's poisons back in the backpack (all or nothing). False: no room.</summary>
		private static bool TakeOut(GamePlayer player, PoisonBagState state, int i)
		{
			if (string.IsNullOrEmpty(state.Templates[i]) || state.Counts[i] <= 0)
			{
				Clear(state, i);
				return true;
			}

			DbItemTemplate t = Template(state.Templates[i]);

			if (t == null)
			{
				Clear(state, i);                   // (a poison the database no longer has)
				return true;
			}

			if (!player.Inventory.AddTemplate(GameInventoryItem.Create(t), state.Counts[i], eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
				return false;

			InventoryLogging.LogInventoryAction("(poison bag)", player, eInventoryActionType.Other, t, state.Counts[i]);
			Clear(state, i);
			return true;
		}

		/// <summary>The first version's bag: the backpack stacks it pointed at move into it.</summary>
		private static void TakeInLegacy(GamePlayer player, PoisonBagState state)
		{
			state.Legacy = false;

			for (int i = 0; i < 4; i++)
			{
				string id = state.Templates[i];

				if (string.IsNullOrEmpty(id) || state.Counts[i] > 0)
					continue;

				foreach (DbInventoryItem item in player.Inventory.GetItemRange(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack).ToList())
				{
					if (!IsPoison(item) || item.Id_nb != id)
						continue;

					int n = Math.Max(1, item.Count);

					if (player.Inventory.RemoveItem(item))
						state.Counts[i] += n;
				}

				if (state.Counts[i] == 0)
					state.Templates[i] = "";
			}

			Save(player, state);
		}

		// ------------------------------------------------------------------ commands (/ac poison ...)

		public static void Command(GamePlayer player, string[] args)
		{
			PoisonBagState state = Get(player);
			string sub = args.Length > 2 ? args[2].ToLowerInvariant() : "query";

			if (state.Legacy)
				TakeInLegacy(player, state);

			switch (sub)
			{
				case "set" when args.Length > 4 && int.TryParse(args[3], out int bagSlot) && int.TryParse(args[4], out int invSlot):
					Put(player, state, bagSlot - 1, player.Inventory.GetItem((eInventorySlot) invSlot));
					break;
				case "clear" when args.Length > 3 && int.TryParse(args[3], out int clearSlot) && clearSlot is >= 1 and <= 4:
					if (TakeOut(player, state, clearSlot - 1))
						Save(player, state);
					else
						player.Out.SendMessage("There is no room in your backpack for those poisons.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
					break;
				case "swap":
					state.Set = 1 - state.Set;
					state.Warned.Clear();
					Save(player, state);
					player.Out.SendMessage($"Poison set {state.Set + 1}: {NameOf(state, state.Set * 2)} / {NameOf(state, state.Set * 2 + 1)}" +
						(player.InCombat ? " - applied once you are out of combat." : "."), eChatType.CT_System, eChatLoc.CL_SystemWindow);
					break;
			}

			state.LastSent = "";
			EnsureTimer(player, state);
			Apply(player, state);
			SendState(player, state);
		}

		/// <summary>A backpack stack of poison into bag slot i: added to the same poison, or in place of another (that one back to the backpack).</summary>
		private static void Put(GamePlayer player, PoisonBagState state, int i, DbInventoryItem item)
		{
			if (i is < 0 or > 3)
				return;

			if (!IsPoison(item) || !InBackpack(item))
			{
				player.Out.SendMessage("Only poisons from your backpack go in the poison bag.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}

			DbItemTemplate t = Template(item.Id_nb);

			if (t == null)
			{
				player.Out.SendMessage($"{item.Name} can't go in the poison bag.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}

			int n = Math.Max(1, item.Count);
			int oldCount = state.Counts[i];
			bool same = state.Templates[i] == item.Id_nb;

			if (!player.Inventory.RemoveItem(item))
				return;

			InventoryLogging.LogInventoryAction(player, "(poison bag)", eInventoryActionType.Other, t, n);

			if (!same && oldCount > 0 && !TakeOut(player, state, i))
			{
				// no room for what the slot held (bigger than the one stack it gave way to): undo
				player.Inventory.AddTemplate(GameInventoryItem.Create(t), n, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);
				player.Out.SendMessage("There is no room in your backpack for the poisons in that bag slot.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
				return;
			}

			state.Templates[i] = item.Id_nb;
			state.Counts[i] = (same ? oldCount : 0) + n;
			state.Warned.Clear();
			Save(player, state);
			player.Out.SendMessage($"{n} {t.Name} into your poison bag (set {(i < 2 ? 1 : 2)}, {(i % 2 == 0 ? "main hand" : "left hand")}): {state.Counts[i]} there.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
		}

		private static string NameOf(PoisonBagState state, int i) =>
			string.IsNullOrEmpty(state.Templates[i]) ? "nothing" : Template(state.Templates[i])?.Name ?? state.Templates[i];

		private static void EnsureTimer(GamePlayer player, PoisonBagState state)
		{
			if (state.Timer is { IsAlive: true } || state.Templates.All(string.IsNullOrEmpty))
				return;

			state.Timer = new ECSGameTimer(player, Tick, TickMs);
		}

		private static int Tick(ECSGameTimer timer)
		{
			if (timer.Owner is not GamePlayer player || player.ObjectState is not GameObject.eObjectState.Active || player.Client == null)
			{
				if (timer.Owner is GamePlayer gone)
					lock (_lock) { _states.Remove(gone); }

				return 0;
			}

			PoisonBagState state = Get(player);

			if (state.Templates.All(string.IsNullOrEmpty))
				return 0;

			Apply(player, state);
			SendState(player, state);
			return TickMs;
		}

		// ------------------------------------------------------------------ putting the set on the weapons

		/// <summary>The weapons the set goes on: the one in your hand (right hand or the two-hander), and the left hand's.</summary>
		private static (DbInventoryItem main, DbInventoryItem left) Weapons(GamePlayer player)
		{
			DbInventoryItem main = player.ActiveWeaponSlot switch
			{
				eActiveWeaponSlot.TwoHanded => player.Inventory.GetItem(eInventorySlot.TwoHandWeapon),
				_ => player.Inventory.GetItem(eInventorySlot.RightHandWeapon)
			};
			DbInventoryItem left = player.Inventory.GetItem(eInventorySlot.LeftHandWeapon);

			if (left != null && (left.Object_Type == (int) eObjectType.Shield || !GlobalConstants.IsWeapon(left.Object_Type)))
				left = null;

			return (main, left);
		}

		public static void Apply(GamePlayer player, PoisonBagState state)
		{
			if (player.GetModifiedSpecLevel(Specs.Envenom) < 1 || !player.IsAlive)
				return;

			// the game's rule: never in combat (or mesmerized) - the bag waits until you are out of it
			if (player.InCombat || EffectListService.GetEffectOnTarget(player, eEffect.Mez) != null)
				return;

			(DbInventoryItem main, DbInventoryItem left) = Weapons(player);
			bool used = ApplyOne(player, state, state.Set * 2, main);
			used |= ApplyOne(player, state, state.Set * 2 + 1, left);

			if (used)
				Save(player, state);
		}

		/// <summary>One dose from bag slot i onto the weapon - GamePlayer.ApplyPoison's rules and effect. True: a dose used.</summary>
		private static bool ApplyOne(GamePlayer player, PoisonBagState state, int i, DbInventoryItem weapon)
		{
			string templateId = state.Templates[i];

			if (weapon == null || string.IsNullOrEmpty(templateId) || state.Counts[i] <= 0)
				return false;

			DbItemTemplate poison = Template(templateId);

			if (poison == null)
				return false;

			// already carrying this poison with charges left: nothing to do
			if (weapon.PoisonSpellID == poison.PoisonSpellID && weapon.PoisonCharges > 0)
				return false;

			// what ApplyPoison would refuse, said once (not every two seconds)
			string refusal = null;

			if (!GlobalConstants.IsWeapon(weapon.Object_Type) || !GamePlayer.CanPoisonWeapon(weapon.Object_Type) || !player.HasAbilityToUseItem(weapon.Template))
				refusal = $"Your {weapon.Name} can't be poisoned.";
			else if (player.GetModifiedSpecLevel(Specs.Envenom) < poison.Level || player.Level < poison.Level)
				refusal = $"Your Envenom isn't high enough for {poison.Name} yet.";

			if (refusal != null)
			{
				if (state.Warned.Add(templateId + "@" + weapon.Id_nb))
					player.Out.SendMessage(refusal, eChatType.CT_System, eChatLoc.CL_SystemWindow);

				return false;
			}

			weapon.PoisonCharges = poison.PoisonCharges;
			weapon.PoisonMaxCharges = poison.PoisonMaxCharges;
			weapon.PoisonSpellID = poison.PoisonSpellID;
			player.Out.SendInventoryItemsUpdate(eInventoryWindowType.Equipment, [weapon]);

			if (--state.Counts[i] <= 0)
				Clear(state, i);

			InventoryLogging.LogInventoryAction(player, "(poison)", eInventoryActionType.Other, poison);
			player.Out.SendMessage($"You apply {poison.Name} to {weapon.GetName(0, false)}.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
			return true;
		}

		/// <summary>#AC|poisons|set|model~count~name (x4): what each bag slot holds (count 0: empty).</summary>
		public static void SendState(GamePlayer player, PoisonBagState state)
		{
			List<string> parts = new() { "poisons", state.Set.ToString() };

			for (int i = 0; i < 4; i++)
			{
				DbItemTemplate t = Template(state.Templates[i]);

				if (t == null || state.Counts[i] <= 0)
				{
					parts.Add("0~0~");
					continue;
				}

				parts.Add($"{t.Model}~{state.Counts[i]}~{t.Name.Replace("|", "/").Replace("~", "-")}");
			}

			string line = string.Join("|", parts);

			if (line == state.LastSent)
				return;

			state.LastSent = line;
			ActionCombat.Send(player, line);
		}
	}
}
