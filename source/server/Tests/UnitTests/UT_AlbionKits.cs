using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Albion's class kits (AlbionKits, StyleRework.Albion - the owner's answers in "Albion Class Rework - the plan",
/// 2026-11-24).</summary>
[TestFixture]
public sealed class UT_AlbionKits
{
    [Test]
    public void TheClassIdsAreAlbions()
    {
        Assert.That(AlbionKits.Paladin, Is.EqualTo((int) eCharacterClass.Paladin));
        Assert.That(AlbionKits.Armsman, Is.EqualTo((int) eCharacterClass.Armsman));
        Assert.That(AlbionKits.Scout, Is.EqualTo((int) eCharacterClass.Scout));
        Assert.That(AlbionKits.Minstrel, Is.EqualTo((int) eCharacterClass.Minstrel));
        Assert.That(AlbionKits.Theurgist, Is.EqualTo((int) eCharacterClass.Theurgist));
        Assert.That(AlbionKits.Cleric, Is.EqualTo((int) eCharacterClass.Cleric));
        Assert.That(AlbionKits.Wizard, Is.EqualTo((int) eCharacterClass.Wizard));
        Assert.That(AlbionKits.Sorcerer, Is.EqualTo((int) eCharacterClass.Sorcerer));
        Assert.That(AlbionKits.Infiltrator, Is.EqualTo((int) eCharacterClass.Infiltrator));
        Assert.That(AlbionKits.Friar, Is.EqualTo((int) eCharacterClass.Friar));
        Assert.That(AlbionKits.Mercenary, Is.EqualTo((int) eCharacterClass.Mercenary));
        Assert.That(AlbionKits.Necromancer, Is.EqualTo((int) eCharacterClass.Necromancer));
        Assert.That(AlbionKits.Cabalist, Is.EqualTo((int) eCharacterClass.Cabalist));
        Assert.That(AlbionKits.Reaver, Is.EqualTo((int) eCharacterClass.Reaver));
    }

    // owner: "The stun is fine, but no longer than 4 seconds for such a powerful AoE"; Ice Shell "Fine, great spell"
    [Test]
    public void TheAgreedNumbers()
    {
        Assert.That(AlbionKits.ThunderChordSeconds, Is.LessThanOrEqualTo(4));
        Assert.That(AlbionKits.IceShellMs, Is.EqualTo(3000));
        Assert.That(AlbionKits.GuardAt, Is.EqualTo(HibernianKits.BulwarkAt), "the Friar's Blessed Guard ranks as the Warden's Bulwark");
        Assert.That(AlbionKits.AegisAt, Is.EqualTo(HibernianKits.BrambleAt), "the Cleric's Holy Aegis ranks as the Druid's Bramble Shield");
        Assert.That(AlbionKits.PrayerReuseMs, Is.EqualTo(HibernianKits.RallyReuseMs), "Call to Prayer as Rallying Cry");
        Assert.That(AlbionKits.TempoMax, Is.EqualTo(HibernianKits.CrescendoMax), "Tempo as Crescendo");
        Assert.That(AlbionKits.NestReuseMs, Is.EqualTo(HibernianHybrids.CamoReuseMs), "Hidden Nest as Camouflage");
        Assert.That(AlbionKits.NestMinRange, Is.EqualTo(HibernianHybrids.CamoMinRange));
    }

    [Test]
    public void PinningShotGrowsWithLongbows()
    {
        Assert.That(AlbionKits.PinSeconds(1), Is.EqualTo(3));
        Assert.That(AlbionKits.PinSeconds(20), Is.EqualTo(4));
        Assert.That(AlbionKits.PinSeconds(50), Is.EqualTo(5));
    }

    [Test]
    public void LingeringVenomStacksToThree()
    {
        Assert.That(AlbionKits.VenomFactor(0), Is.EqualTo(1.0));
        Assert.That(AlbionKits.VenomFactor(3), Is.EqualTo(1.45).Within(1e-9));
        Assert.That(AlbionKits.VenomFactor(9), Is.EqualTo(AlbionKits.VenomFactor(3)), "capped at three");
    }

    [Test]
    public void TheInfiltratorsMarksAreItsPositionals()
    {
        Assert.That(StyleRework.InfiltratorMarks, Does.Contain(118).And.Contain(126).And.Contain(338));
        Assert.That(StyleRework.InfiltratorMarks, Does.Not.Contain(335), "Backstab, a stealth opener, isn't one of them");
    }
}
