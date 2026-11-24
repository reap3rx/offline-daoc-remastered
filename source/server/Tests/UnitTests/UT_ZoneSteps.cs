using System;
using DOL.GS;
using DOL.GS.DynamicEvents;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Each zone rating a step harder (owner 2026-11-23: blues in a Wild zone "slightly harder than blue mobs in
/// Peaceful ... especially their special attacks ... noticeable" but not confusing; the moderate steps), and the fifth
/// rating, Elite (Cursed Forest, Sheeroe Hills).</summary>
[TestFixture]
public sealed class UT_ZoneSteps
{
    static readonly ZoneRates.Rating[] All = (ZoneRates.Rating[]) Enum.GetValues(typeof(ZoneRates.Rating));

    [Test]
    public void PeacefulIsTheBaseline()
    {
        Assert.That(ZoneRates.Hits(ZoneRates.Rating.Peaceful), Is.EqualTo(1.0));
        Assert.That(ZoneRates.Takes(ZoneRates.Rating.Peaceful), Is.EqualTo(1.0));
        Assert.That(ZoneRates.SpecialExtra(ZoneRates.Rating.Peaceful), Is.EqualTo(1.0));
    }

    [Test]
    public void EachRatingHitsHarderAndTakesLess()
    {
        for (int i = 1; i < All.Length; i++)
        {
            Assert.That(ZoneRates.Hits(All[i]), Is.GreaterThan(ZoneRates.Hits(All[i - 1])), $"{All[i]} hits");
            Assert.That(ZoneRates.Takes(All[i]), Is.LessThan(ZoneRates.Takes(All[i - 1])), $"{All[i]} takes");
            double special = ZoneRates.Hits(All[i]) * ZoneRates.SpecialExtra(All[i]);
            double prev = ZoneRates.Hits(All[i - 1]) * ZoneRates.SpecialExtra(All[i - 1]);
            Assert.That(special / prev, Is.GreaterThan(ZoneRates.Hits(All[i]) / ZoneRates.Hits(All[i - 1])),
                $"{All[i]}: a special steps up more than a blow");
        }
    }

    [Test]
    public void TheStepsAreNoticeableButNotConfusing()
    {
        // a Wild blue a little harder than a Peaceful one; an Elite one about a third harder, not twice
        Assert.That(ZoneRates.Hits(ZoneRates.Rating.Wild), Is.InRange(1.05, 1.12));
        Assert.That(ZoneRates.Hits(ZoneRates.Rating.Elite), Is.InRange(1.25, 1.4));
        Assert.That(ZoneRates.Hits(ZoneRates.Rating.Elite) * ZoneRates.SpecialExtra(ZoneRates.Rating.Elite), Is.EqualTo(1.48).Within(1e-9));
        Assert.That(ZoneRates.Takes(ZoneRates.Rating.Elite), Is.EqualTo(0.88).Within(1e-9));
    }

    [Test]
    public void EliteIsTheTopRating()
    {
        Assert.That(All[^1], Is.EqualTo(ZoneRates.Rating.Elite));
        Assert.That(ZoneRates.Factor(ZoneRates.Rating.Elite), Is.GreaterThan(ZoneRates.Factor(ZoneRates.Rating.Deadly)));
        Assert.That(MonsterTiers.PurpleByRating.Length, Is.EqualTo(All.Length), "a purple cap for every rating");
        Assert.That(EventCons.Trash(ZoneRates.Rating.Elite), Is.EqualTo(MonsterTiers.Orange));
        Assert.That(EventCons.Boss(ZoneRates.Rating.Elite, 1).tier, Is.EqualTo(MonsterTiers.Red));
        Assert.That(EventCons.Boss(ZoneRates.Rating.Elite, 3).tier, Is.EqualTo(MonsterTiers.Purple));
        Assert.That(EventCons.StoryBoss(ZoneRates.Rating.Elite, false, false), Is.EqualTo(MonsterTiers.Red));
        Assert.That(EventCons.StoryBoss(ZoneRates.Rating.Deadly, false, false), Is.EqualTo(MonsterTiers.Orange));
    }
}
