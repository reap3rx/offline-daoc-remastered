/*
 * The poison bag (owner 2026-10-27): four poisons picked from the backpack in two sets - slots 1 + 2 and 3 + 4.
 * The active set is put on your weapons by itself, by the game's own poisoning rules (GamePlayer.ApplyPoison:
 * Envenom trained, a weapon that takes poison, a poison of your Envenom level and your level, and not while in
 * combat or mesmerized): the first poison on the weapon in your hand (the right hand, or the two-hander drawn),
 * the second on the left-hand weapon. A weapon is poisoned again when its charges run out, or when the set changes
 * (the other set's poison wiped off). Shift + wheel (the client) switches sets.
 * The bag keeps the poisons' item templates - the stacks stay in the backpack; it is saved on the character
 * (DOLCharactersXCustomParam "PoisonBag": id1,id2,id3,id4;set). The client is told by "#AC|poisons|..." lines.
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
		public int Set;                        // 0: slots 1 + 2, 1: slots 3 + 4
		public ECSGameTimer Timer;
		public string LastSent = "";
		public readonly HashSet<string> Warned = new();
	}

	public static class PoisonBag
	{
		public const string ParamKey = "PoisonBag";
		public const int TickMs = 2000;

		private static readonly Dictionary<GamePlayer, PoisonBagState> _states = new();
		private static readonly object _lock = new();

		public static PoisonBagState Get(GamePlayer player)
		{
			lock (_lock)
			{
				if (_states.TryGetValue(player, out PoisonBagState state))
					return state;

				state = Load(player);
				_states[player] = state;
				return state;
			}
		}

		private static DbCoreCharacterXCustomParam Record(GamePlayer player)
		{
			return DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
				DB.Column("DOLCharactersObjectId").IsEqualTo(player.ObjectId).And(DB.Column("KeyName").IsEqualTo(ParamKey)));
		}

		private static PoisonBagState Load(GamePlayer player)
		{
			PoisonBagState state = new();
			string value = Record(player)?.Value ?? "";
			string[] parts = value.Split(';');
			string[] ids = parts[0].Split(',');

			for (int i = 0; i < 4 && i < ids.Length; i++)
				state.Templates[i] = ids[i].Trim();

			if (parts.Length > 1 && int.TryParse(parts[1], out int set))
				state.Set = set == 1 ? 1 : 0;

			return state;
		}

		private static void Save(GamePlayer player, PoisonBagState state)
		{
			string value = string.Join(",", state.Templates) + ";" + state.Set;
			DbCoreCharacterXCustomParam record = Record(player);

			if (record == null)
				GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(player.ObjectId, ParamKey, value));
			else
			{
				record.Value = value;
				GameServer.Database.SaveObject(record);
			}
		}

		private static bool IsPoison(DbInventoryItem item) => item != null && item.Object_Type == (int) eObjectType.Poison;

		private static IEnumerable<DbInventoryItem> Backpack(GamePlayer player) =>
			player.Inventory.GetItemRange(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);

		/// <summary>The backpack's first stack of this poison (null: none left).</summary>
		private static DbInventoryItem Find(GamePlayer player, string templateId)
		{
			if (string.IsNullOrEmpty(templateId))
				return null;

			return Backpack(player).FirstOrDefault(i => IsPoison(i) && i.Id_nb == templateId);
		}

		private static int Count(GamePlayer player, string templateId)
		{
			if (string.IsNullOrEmpty(templateId))
				return 0;

			return Backpack(player).Where(i => IsPoison(i) && i.Id_nb == templateId).Sum(i => Math.Max(1, i.Count));
		}

		// ------------------------------------------------------------------ commands (/ac poison ...)

		public static void Command(GamePlayer player, string[] args)
		{
			PoisonBagState state = Get(player);
			string sub = args.Length > 2 ? args[2].ToLowerInvariant() : "query";

			switch (sub)
			{
				case "set" when args.Length > 4 && int.TryParse(args[3], out int bagSlot) && int.TryParse(args[4], out int invSlot):
				{
					DbInventoryItem item = player.Inventory.GetItem((eInventorySlot) invSlot);

					if (bagSlot < 1 || bagSlot > 4)
						return;

					if (!IsPoison(item))
					{
						player.Out.SendMessage("Only poisons go in the poison bag.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
						break;
					}

					state.Templates[bagSlot - 1] = item.Id_nb;
					state.Warned.Clear();
					Save(player, state);
					player.Out.SendMessage($"{item.Name} goes in your poison bag (set {(bagSlot <= 2 ? 1 : 2)}, {(bagSlot % 2 == 1 ? "main hand" : "left hand")}).", eChatType.CT_System, eChatLoc.CL_SystemWindow);
					break;
				}
				case "clear" when args.Length > 3 && int.TryParse(args[3], out int clearSlot) && clearSlot is >= 1 and <= 4:
					state.Templates[clearSlot - 1] = "";
					Save(player, state);
					break;
				case "swap":
					state.Set = 1 - state.Set;
					state.Warned.Clear();
					Save(player, state);
					player.Out.SendMessage($"Poison set {state.Set + 1}: {NameOf(player, state.Templates[state.Set * 2])} / {NameOf(player, state.Templates[state.Set * 2 + 1])}" +
						(player.InCombat ? " - applied once you are out of combat." : "."), eChatType.CT_System, eChatLoc.CL_SystemWindow);
					break;
			}

			state.LastSent = "";
			EnsureTimer(player, state);
			Apply(player, state);
			SendState(player, state);
		}

		private static string NameOf(GamePlayer player, string templateId)
		{
			if (string.IsNullOrEmpty(templateId))
				return "nothing";

			return Find(player, templateId)?.Name ?? GameServer.Database.FindObjectByKey<DbItemTemplate>(templateId)?.Name ?? templateId;
		}

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
			ApplyOne(player, state, state.Templates[state.Set * 2], main);
			ApplyOne(player, state, state.Templates[state.Set * 2 + 1], left);
		}

		private static void ApplyOne(GamePlayer player, PoisonBagState state, string templateId, DbInventoryItem weapon)
		{
			if (weapon == null || string.IsNullOrEmpty(templateId))
				return;

			DbInventoryItem poison = Find(player, templateId);

			if (poison == null)
				return;

			int spellId = poison.PoisonSpellID != 0 ? poison.PoisonSpellID : poison.Template.PoisonSpellID;

			// already carrying this poison with charges left: nothing to do
			if (weapon.PoisonSpellID == spellId && weapon.PoisonCharges > 0)
				return;

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

				return;
			}

			if (player.ApplyPoison(poison, weapon))
				player.Out.SendInventoryItemsUpdate(eInventoryWindowType.Equipment, [weapon]);
		}

		/// <summary>#AC|poisons|set|invslot~count~name (x4): what each bag slot holds (invslot 0: none left in the backpack).</summary>
		public static void SendState(GamePlayer player, PoisonBagState state)
		{
			List<string> parts = new() { "poisons", state.Set.ToString() };

			for (int i = 0; i < 4; i++)
			{
				string id = state.Templates[i];

				if (string.IsNullOrEmpty(id))
				{
					parts.Add("0~0~");
					continue;
				}

				DbInventoryItem item = Find(player, id);
				string name = (item?.Name ?? NameOf(player, id)).Replace("|", "/").Replace("~", "-");
				parts.Add($"{(item != null ? (int) item.SlotPosition : 0)}~{Count(player, id)}~{name}");
			}

			string line = string.Join("|", parts);

			if (line == state.LastSent)
				return;

			state.LastSent = line;
			ActionCombat.Send(player, line);
		}
	}
}
