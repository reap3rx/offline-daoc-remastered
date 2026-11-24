using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>The /tier tune window's per-tier numbers (owner 2026-11-21): each tier's hits, takes and press on top of the curve.</summary>
[TestFixture, NonParallelizable]
public sealed class UT_TierTuning
{
    [TearDown]
    public void Reset() => MonsterTiers.ResetTierTuning();

    [Test]
    public void ATiersHitsAndTakesScaleOnlyThatTier()
    {
        MonsterTiers.ResetTierTuning();
        double inY = MonsterTiers.InFactor(MonsterTiers.Yellow, 20), outY = MonsterTiers.OutFactor(MonsterTiers.Yellow, 20);
        double inB = MonsterTiers.InFactor(MonsterTiers.Blue, 20);
        MonsterTiers.TierHits[3] = 1.5;
        MonsterTiers.TierTakes[3] = 0.5;
        Assert.That(MonsterTiers.InFactor(MonsterTiers.Yellow, 20), Is.EqualTo(inY * 1.5).Within(1e-9));
        Assert.That(MonsterTiers.OutFactor(MonsterTiers.Yellow, 20), Is.EqualTo(outY * 0.5).Within(1e-9));
        Assert.That(MonsterTiers.InFactor(MonsterTiers.Blue, 20), Is.EqualTo(inB).Within(1e-9));
    }

    [Test]
    public void PressingCountsOnEveryConButACritter()
    {
        MonsterTiers.ResetTierTuning();
        for (sbyte t = MonsterTiers.Green; t <= MonsterTiers.Purple; t++)
            Assert.That(MonsterTiers.PressStepFor(t), Is.GreaterThan(0), t.ToString());
        Assert.That(MonsterTiers.PressStepFor(MonsterTiers.Grey), Is.EqualTo(0));
        Assert.That(MonsterTiers.PressStepFor(MonsterTiers.None), Is.EqualTo(0));
        MonsterTiers.TierPress[5] = 0.05;
        Assert.That(MonsterTiers.PressStepFor(MonsterTiers.Red), Is.EqualTo(0.05));
    }

    [Test]
    public void ResetBringsBackTheTargetsAsFitted()
    {
        MonsterTiers.GreenTakes = 9;
        MonsterTiers.ResetTierTuning();
        Assert.That(MonsterTiers.GreenTakes, Is.EqualTo(1.0));
        Assert.That(MonsterTiers.GreenHits, Is.EqualTo(1.0));
    }
}
