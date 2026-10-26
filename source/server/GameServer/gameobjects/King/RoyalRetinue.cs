/*
 * The King / Queen's sworn commander keeps one identity for the whole career: the first summon picks a
 * personal name that fits the commander's gender, stored on the character (DOLCharactersXCustomParam
 * "KingCommanderName"), and every later summon - every rank - uses it: Squire Anne, Shieldbearer Anne ...
 * The commander also carries the guild line "<King's name>'s Retinue"; the new client draws anything of a
 * Retinue with a face, hair and skin seeded by that line and the personal name, so the look stays too.
 */
using System.Linq;
using DOL.Database;

namespace DOL.GS
{
	public static class RoyalRetinue
	{
		public const string NameKey = "KingCommanderName";
		public const string GuildSuffix = "'s Retinue";

		private static readonly string[] FemaleNames =
		{
			"Anne", "Elaine", "Enid", "Isolde", "Lynette", "Laudine", "Vivienne", "Ragnell", "Blanchefleur",
			"Clarissant", "Elowen", "Rowena", "Gwendolyn", "Brangaine", "Lunete", "Nimue", "Morwenna", "Ysolde"
		};

		private static readonly string[] MaleNames =
		{
			"Gareth", "Bedivere", "Percival", "Tristan", "Gawain", "Kay", "Lamorak", "Bors", "Ector", "Galahad",
			"Owain", "Pelleas", "Dagonet", "Lionel", "Geraint", "Caradoc", "Lucan", "Agravaine"
		};

		public static string GuildNameFor(GamePlayer player) => player.Name + GuildSuffix;

		/// <summary>The commander's personal name, chosen once (by its gender) and kept on the character.</summary>
		public static string GetOrCreateCommanderName(GamePlayer player, eGender commanderGender)
		{
			DbCoreCharacterXCustomParam record = DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
				DB.Column("DOLCharactersObjectId").IsEqualTo(player.ObjectId).And(DB.Column("KeyName").IsEqualTo(NameKey)));

			if (record != null && !string.IsNullOrWhiteSpace(record.Value))
				return record.Value;

			string[] pool = commanderGender == eGender.Female ? FemaleNames : MaleNames;
			string name = pool[Util.Random(pool.Length - 1)];

			if (record == null)
				GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(player.ObjectId, NameKey, name));
			else
			{
				record.Value = name;
				GameServer.Database.SaveObject(record);
			}

			return name;
		}
	}
}
