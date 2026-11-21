using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Greens are fodder (owner 2026-11-21): never above a new character, softer, and a run of hits presses harder.</summary>
[TestFixture]
public sealed class UT_GreenFodder
{
    [Test]
    public void AGreenIsNeverAboveYou()
    {
        for (int l = 1; l <= 50; l++)
            Assert.That(MonsterTiers.ConGap(MonsterTiers.Green, l), Is.LessThanOrEqualTo(0.0), $"level {l}");
    }

    [Test]
    public void GreensTakeMoreAndHitSofterThanTheLadderAlone()
    {
        double outGreen = MonsterTiers.OutFactor(MonsterTiers.Green, 3), outBlue = MonsterTiers.OutFactor(MonsterTiers.Blue, 3);
        Assert.That(outGreen / outBlue, Is.GreaterThan(MonsterTiers.OutStep * 1.5));
        Assert.That(MonsterTiers.InFactor(MonsterTiers.Green, 3), Is.LessThan(MonsterTiers.InFactor(MonsterTiers.Blue, 3) / MonsterTiers.InStep));
    }
}
