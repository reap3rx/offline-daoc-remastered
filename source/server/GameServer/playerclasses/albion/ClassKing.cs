/*
 * King / Queen - Ryan's custom Albion class (Offline DAoC mod).
 *
 * A royal light tank who leads a sworn retinue: a commander (Squire .. Knight)
 * who in turn commands up to five retainers (armsman, cleric, scout, sorcerer,
 * wizard).  The King fights with one-handed slashing weapons only (no shield,
 * no left hand), wears chain, and relies on top-tier evade and parry.
 *
 * Player-only: the class is never added to the launcher's or the autonomous
 * bot generator's class lists, so no bot can roll it.
 *
 * Created directly as King/Queen at level 1 (no base-class promotion).
 * Spec lines, abilities and spells live in the database (KingCareer,
 * Slash, Parry, Fealty, Majesty) - see tools/king/seed_king.py.
 */
using System;
using System.Collections.Generic;
using DOL.GS.Realm;
using DOL.Language;

namespace DOL.GS.PlayerClass
{
	[CharacterClass((int)eCharacterClass.King, "King", "King", "Queen")]
	public class ClassKing : CharacterClassBase
	{
		public ClassKing()
			: base()
		{
			m_profession = "PlayerClass.Profession.HouseofPendragon";
			// Highest specialization budget in the game (same as Infiltrator).
			m_specializationMultiplier = 25;
			m_primaryStat = eStat.STR;
			m_secondaryStat = eStat.DEX;
			m_tertiaryStat = eStat.QUI;
			// Majesty chants draw on the sovereign's presence.
			m_manaStat = eStat.CHR;
			m_wsbase = 440;
			m_baseHP = 880;
		}

		public override eClassType ClassType => eClassType.Hybrid;

		// Like the Warden: two pulsing Majesty decrees at once.
		public override ushort MaxPulsingSpells => 2;

		// One-handed slashing weapons only: no shield and no left-hand weapon.
		public override bool CanUseLefthandedWeapon => false;

		// Created directly as the advanced class.
		public override bool HasAdvancedFromBaseClass() => true;

		public override GameTrainer.eChampionTrainerType ChampionTrainerType()
		{
			return GameTrainer.eChampionTrainerType.Fighter;
		}

		/// <summary>
		/// Level titles: a Queen uses her own title list (PlayerClass.Queen.GetTitle.N).
		/// </summary>
		public override string GetTitle(GamePlayer player, int level)
		{
			if (player != null && player.Gender == eGender.Female)
			{
				int clamplevel = Math.Min(50, (level / 5) * 5);
				if (clamplevel > 0)
					return LanguageMgr.TryTranslateOrDefault(player, "!Queen!", string.Format("PlayerClass.Queen.GetTitle.{0}", clamplevel));
			}

			return base.GetTitle(player, level);
		}

		public override List<PlayerRace> EligibleRaces => new List<PlayerRace>()
		{
			PlayerRace.Briton, PlayerRace.Avalonian,
		};
	}
}
