using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>The Nightshade, the Ranger and the Valewalker (agreed 21 Nov): Voidstep's chance, Penetrating Arrow's line,
/// Creeping Rot's growth.</summary>
[TestFixture]
public sealed class UT_HibernianHybrids
{
    [Test]
    public void VoidstepIsOnePercentAPointOfStealth()
    {
        Assert.That(HibernianHybrids.VoidstepPercent(0), Is.EqualTo(0));
        Assert.That(HibernianHybrids.VoidstepPercent(1), Is.EqualTo(1));
        Assert.That(HibernianHybrids.VoidstepPercent(50), Is.EqualTo(50));
        Assert.That(HibernianHybrids.VoidstepPercent(60), Is.EqualTo(60), "(+ items / realm abilities count too)");
    }

    [Test]
    public void TheArrowGoesOnThroughOnlyBehindTheTarget()
    {
        // shooter at the origin, target 1000 east
        Assert.That(HibernianHybrids.BehindInLine(0, 0, 1000, 0, 1300, 50), Is.True, "just behind, a little to the side");
        Assert.That(HibernianHybrids.BehindInLine(0, 0, 1000, 0, 900, 0), Is.False, "in front of the target");
        Assert.That(HibernianHybrids.BehindInLine(0, 0, 1000, 0, 1300, 400), Is.False, "too far off the line");
        Assert.That(HibernianHybrids.BehindInLine(0, 0, 1000, 0, 1000 + HibernianHybrids.PierceReach + 50, 0), Is.False, "out of reach");
        Assert.That(HibernianHybrids.BehindInLine(0, 0, 0, 1000, 30, 1200), Is.True, "any direction");
    }

    [Test]
    public void TheRotGrowsFiveTimesAndNoMore()
    {
        Assert.That(HibernianHybrids.RotFactor(0), Is.EqualTo(1.0));
        Assert.That(HibernianHybrids.RotFactor(1), Is.EqualTo(1.0 + HibernianHybrids.RotStep).Within(1e-9));
        Assert.That(HibernianHybrids.RotFactor(9), Is.EqualTo(HibernianHybrids.RotFactor(HibernianHybrids.RotMax)).Within(1e-9));
    }
}
