using System;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>
/// The fitted power curve (MonsterTiers.InFactor / OutFactor, owner 2026-11-19): each con above your band hits harder
/// and takes longer to bring down, an even con the same at every level of the curve's shape, and the endurance rules of
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
    public void TheStepIsTheSameEverywhere()
    {
        double r = MonsterTiers.InFactor(MonsterTiers.Blue, 20) / MonsterTiers.InFactor(MonsterTiers.Green, 20);
        Assert.That(r, Is.EqualTo(MonsterTiers.InStep).Within(1e-9));
        double o = MonsterTiers.OutFactor(MonsterTiers.Green, 33) / MonsterTiers.OutFactor(MonsterTiers.Blue, 33);
        Assert.That(o, Is.EqualTo(MonsterTiers.OutStep).Within(1e-9));
    }

    [Test]
    public void AtTheCurvesPointsAnEvenConIsTheCurveItself()
    {
        // level 30.5 is a yellow's band centre; at the points the factor is the curve times the step to the gap
        for (int i = 0; i < MonsterTiers.CurveLevels.Length; i++)
        {
            int lv = MonsterTiers.CurveLevels[i];
            double gap = MonsterTiers.ConGap(MonsterTiers.Yellow, lv);
            Assert.That(MonsterTiers.InFactor(MonsterTiers.Yellow, lv),
                Is.EqualTo(MonsterTiers.InCurve[i] * Math.Pow(MonsterTiers.InStep, gap) * MonsterTiers.Bite).Within(1e-9));
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
