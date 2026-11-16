using System.Collections.Generic;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>The pair of songs or chants a bot keeps (owner 2026-11-15: two at once, no twisting).</summary>
    [TestFixture]
    public class UT_BotSongPairPolicy
    {
        static readonly eSpellType[] BardSongs = [eSpellType.SpeedEnhancement, eSpellType.EnduranceRegenBuff,
            eSpellType.HealthRegenBuff, eSpellType.PowerRegenBuff];

        static List<eSpellType> Pick(eCharacterClass c, bool travel, bool fight, bool hurt, bool low, params eSpellType[] have) =>
            BotSongPairPolicy.Pick(c, travel, fight, hurt, low, have);

        [Test] public void BardTravelsWithSpeedAndEndurance() =>
            Assert.That(Pick(eCharacterClass.Bard, true, false, false, false, BardSongs),
                Is.EqualTo(new[] { eSpellType.SpeedEnhancement, eSpellType.EnduranceRegenBuff }));

        [Test] public void BardFightsWithEnduranceAndHealOrHealFirstWhenHurt()
        {
            Assert.That(Pick(eCharacterClass.Bard, false, true, false, false, BardSongs),
                Is.EqualTo(new[] { eSpellType.EnduranceRegenBuff, eSpellType.HealthRegenBuff }));
            Assert.That(Pick(eCharacterClass.Bard, false, true, true, false, BardSongs),
                Is.EqualTo(new[] { eSpellType.HealthRegenBuff, eSpellType.EnduranceRegenBuff }));
        }

        [Test] public void LowPowerCastersGetThePowerSong()
        {
            Assert.That(Pick(eCharacterClass.Bard, false, true, false, true, BardSongs),
                Is.EqualTo(new[] { eSpellType.PowerRegenBuff, eSpellType.EnduranceRegenBuff }));
            Assert.That(Pick(eCharacterClass.Bard, false, true, true, true, BardSongs),
                Is.EqualTo(new[] { eSpellType.HealthRegenBuff, eSpellType.PowerRegenBuff }));
        }

        [Test] public void NoSpeedInAFight() =>
            Assert.That(Pick(eCharacterClass.Minstrel, true, true, false, false, BardSongs), Does.Not.Contain(eSpellType.SpeedEnhancement));

        [Test] public void SkaldFightsWithDamageAdd() =>
            Assert.That(Pick(eCharacterClass.Skald, false, true, false, false, eSpellType.SpeedEnhancement,
                eSpellType.DamageAdd, eSpellType.HealthRegenBuff)[0], Is.EqualTo(eSpellType.DamageAdd));

        [Test] public void PaladinAndWardenPairs()
        {
            Assert.That(Pick(eCharacterClass.Paladin, false, true, false, false, eSpellType.EnduranceRegenBuff,
                eSpellType.SpecArmorFactorBuff, eSpellType.DamageAdd, eSpellType.CombatHeal),
                Is.EqualTo(new[] { eSpellType.DamageAdd, eSpellType.SpecArmorFactorBuff }));
            Assert.That(Pick(eCharacterClass.Paladin, false, true, true, false, eSpellType.EnduranceRegenBuff,
                eSpellType.SpecArmorFactorBuff, eSpellType.DamageAdd, eSpellType.CombatHeal),
                Is.EqualTo(new[] { eSpellType.CombatHeal, eSpellType.DamageAdd }));
            Assert.That(Pick(eCharacterClass.Warden, true, false, false, false, eSpellType.SpeedEnhancement,
                eSpellType.Bladeturn, eSpellType.DamageAdd), Is.EqualTo(new[] { eSpellType.SpeedEnhancement, eSpellType.Bladeturn }));
            Assert.That(Pick(eCharacterClass.Warden, true, true, false, false, eSpellType.SpeedEnhancement,
                eSpellType.Bladeturn, eSpellType.DamageAdd), Is.EqualTo(new[] { eSpellType.Bladeturn, eSpellType.DamageAdd }));
        }

        [Test] public void OnlyKnownSongsAndNeverMoreThanTwo()
        {
            Assert.That(Pick(eCharacterClass.Bard, true, false, false, false, eSpellType.HealthRegenBuff),
                Is.EqualTo(new[] { eSpellType.HealthRegenBuff }));
            Assert.That(Pick(eCharacterClass.Bard, false, false, true, true, BardSongs), Has.Count.EqualTo(2));
        }
    }
}
