using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Starter weapons hit harder while you are new (owner 2026-11-20).</summary>
[TestFixture]
public sealed class UT_TrainingWeapons
{
    [Test]
    public void TheBonusFadesByLevelFifteen()
    {
        Assert.That(TrainingWeapons.Bonus(1), Is.EqualTo(2.0));
        Assert.That(TrainingWeapons.Bonus(8), Is.EqualTo(1.5).Within(0.001));
        Assert.That(TrainingWeapons.Bonus(15), Is.EqualTo(1.0));
        Assert.That(TrainingWeapons.Bonus(40), Is.EqualTo(1.0));
        for (int l = 1; l < 15; l++)
            Assert.That(TrainingWeapons.Bonus(l + 1), Is.LessThan(TrainingWeapons.Bonus(l)));
    }
}
