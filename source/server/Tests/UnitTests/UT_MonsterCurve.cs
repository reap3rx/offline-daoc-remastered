using System;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>
/// The fitted curve (MonsterTiers.InFactor / OutFactor, one footing at every level since 2026-11-22): each con up hits
/// harder and takes longer to bring down, the curve is a green's numbers at each level, and the endurance rules of
/// MonsterMoves (tired defences).
/// </summary>
[TestFixture, NonParallelizable]
public sealed class UT_MonsterCurve
{
    [Test]
    public void EachConAboveYouHitsHarderAndTakesLonger()
    {
        foreach (int level in new[] { 5, 15, 25, 35, 45, 50 })
            for (sbyte t = MonsterTiers.Green; t < MonsterTiers.Purple; t++)
            {
                Assert.That(MonsterTiers.InFactor((sbyte) (t + 1), level), Is.GreaterThan(MonsterTiers.InFactor(t, level)), $"hits, {t} at {level}");
                Assert.That(MonsterTiers.OutFactor((sbyte) (t + 1), level), Is.LessThan(MonsterTiers.OutFactor(t, level)), $"takes, {t} at {level}");
            }
    }

    [Test]
    public void AtTheCurvesPointsAGreenIsTheCurveItself()
    {
        MonsterTiers.ResetTierTuning();
        for (int i = 0; i < MonsterTiers.CurveLevels.Length; i++)
        {
            int lv = MonsterTiers.CurveLevels[i];
            Assert.That(MonsterTiers.InFactor(MonsterTiers.Green, lv), Is.EqualTo(MonsterTiers.InCurve[i] * MonsterTiers.Bite).Within(1e-9));
            Assert.That(MonsterTiers.OutFactor(MonsterTiers.Green, lv), Is.EqualTo(MonsterTiers.OutCurve[i] / MonsterTiers.Toughness).Within(1e-9));
        }
    }

    [Test]
    public void TiredDefencesFallBelowHalfEndurance()
    {
        Assert.That(MonsterMoves.TiredFactor(100), Is.EqualTo(1.0));
        Assert.That(MonsterMoves.TiredFactor(50), Is.EqualTo(1.0));
        Assert.That(MonsterMoves.TiredFactor(25), Is.EqualTo(0.675).Within(1e-9));
        Assert.That(MonsterMoves.TiredFactor(0), Is.EqualTo(0.35).Within(1e-9));
    }

    [Test]
    public void ADefendedBlowCostsThreeTimesWhatItTried()
    {
        Assert.That(MonsterMoves.CostOf(MonsterMoves.Blow.Normal) * MonsterMoves.DefendedTimes, Is.EqualTo(12));
        Assert.That(MonsterMoves.DefendGain, Is.EqualTo(12), "a defence gives back as much");
        Assert.That(MonsterMoves.CostOf(MonsterMoves.Blow.Style), Is.GreaterThan(MonsterMoves.CostOf(MonsterMoves.Blow.Normal)));
    }
}
