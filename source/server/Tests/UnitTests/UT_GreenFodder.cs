using DOL.GS;
using DOL.GS.DynamicEvents;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>One footing at every level (owner 2026-11-22): a con is the same fight at level 1 and at 50 - the curve only
/// evens out DAoC's own numbers - greens are the softest, and events and story quests pick their bosses' cons by
/// the zone's rating and who is there.</summary>
[TestFixture, NonParallelizable]
public sealed class UT_GreenFodder
{
    [TearDown]
    public void Reset() => MonsterTiers.ResetTierTuning();

    [Test]
    public void AConIsTheSameFightAtEveryLevel()
    {
        MonsterTiers.ResetTierTuning();
        for (sbyte t = MonsterTiers.Green; t <= MonsterTiers.Purple; t++)
        {
            double o1 = MonsterTiers.OutFactor(t, 1) / MonsterTiers.OutFactor(MonsterTiers.Green, 1);
            double i1 = MonsterTiers.InFactor(t, 1) / MonsterTiers.InFactor(MonsterTiers.Green, 1);
            for (int l = 2; l <= 50; l++)
            {
                Assert.That(MonsterTiers.OutFactor(t, l) / MonsterTiers.OutFactor(MonsterTiers.Green, l), Is.EqualTo(o1).Within(1e-9), $"takes, {t} at {l}");
                Assert.That(MonsterTiers.InFactor(t, l) / MonsterTiers.InFactor(MonsterTiers.Green, l), Is.EqualTo(i1).Within(1e-9), $"hits, {t} at {l}");
            }
        }
    }

    [Test]
    public void AGreenTakesTheBaselineTenToTwelveSwings()
    {
        Assert.That(MonsterTiers.BaseSwings[1], Is.InRange(10.0, 13.0), "a green, before pressing takes a little off");
        Assert.That(MonsterTiers.BaseSwings, Is.Ordered.Ascending);
        Assert.That(MonsterTiers.BaseLasts, Is.Ordered.Descending);
    }

    [Test]
    public void APurplesStrengthFollowsItsZonesRating()
    {
        Assert.That(MonsterTiers.PurpleByRating, Is.Ordered.Ascending);
        Assert.That(MonsterTiers.PurpleByRating[(int) ZoneRates.Rating.Dangerous], Is.EqualTo(1.0));
    }

    [TestCase(ZoneRates.Rating.Peaceful, 1, MonsterTiers.Yellow)]
    [TestCase(ZoneRates.Rating.Peaceful, 3, MonsterTiers.Orange)]
    [TestCase(ZoneRates.Rating.Peaceful, 5, MonsterTiers.Red)]
    [TestCase(ZoneRates.Rating.Peaceful, 8, MonsterTiers.Purple)]
    [TestCase(ZoneRates.Rating.Wild, 4, MonsterTiers.Red)]
    [TestCase(ZoneRates.Rating.Wild, 5, MonsterTiers.Purple)]
    [TestCase(ZoneRates.Rating.Dangerous, 1, MonsterTiers.Orange)]
    [TestCase(ZoneRates.Rating.Dangerous, 3, MonsterTiers.Red)]
    [TestCase(ZoneRates.Rating.Dangerous, 4, MonsterTiers.Purple)]
    [TestCase(ZoneRates.Rating.Deadly, 2, MonsterTiers.Red)]
    [TestCase(ZoneRates.Rating.Deadly, 3, MonsterTiers.Purple)]
    public void AnEventBossTakesItsConFromWhoIsThere(ZoneRates.Rating r, int people, sbyte tier) =>
        Assert.That(EventCons.Boss(r, people).tier, Is.EqualTo(tier));

    [Test]
    public void WithinAConABossGrowsALittleWithEachPerson()
    {
        Assert.That(EventCons.Boss(ZoneRates.Rating.Peaceful, 1).health, Is.EqualTo(EventCons.BossHealth),
            "a boss has twice the health of an ordinary monster of its con (owner 2026-11-22)");
        Assert.That(EventCons.Boss(ZoneRates.Rating.Peaceful, 3).health, Is.GreaterThan(EventCons.Boss(ZoneRates.Rating.Peaceful, 2).health));
        Assert.That(EventCons.Boss(ZoneRates.Rating.Deadly, 8).health, Is.GreaterThan(EventCons.Boss(ZoneRates.Rating.Peaceful, 8).health),
            "a crowd at a Deadly zone's purple meets a tougher one");
    }

    [Test]
    public void StoryBossesAreSoloSizedUnlessTheQuestIsForAGroup()
    {
        Assert.That(EventCons.StoryBoss(ZoneRates.Rating.Peaceful, false, false), Is.EqualTo(MonsterTiers.Blue));
        Assert.That(EventCons.StoryBoss(ZoneRates.Rating.Peaceful, true, false), Is.EqualTo(MonsterTiers.Yellow));
        Assert.That(EventCons.StoryBoss(ZoneRates.Rating.Peaceful, true, true), Is.EqualTo(MonsterTiers.Red));
        Assert.That(EventCons.StoryBoss(ZoneRates.Rating.Deadly, true, false), Is.EqualTo(MonsterTiers.Red));
        Assert.That(EventCons.Trash(ZoneRates.Rating.Peaceful), Is.EqualTo(MonsterTiers.Green));
    }

    [TestCase(ZoneRates.Rating.Peaceful, MonsterTiers.Green)] [TestCase(ZoneRates.Rating.Wild, MonsterTiers.Blue)]
    [TestCase(ZoneRates.Rating.Dangerous, MonsterTiers.Yellow)] [TestCase(ZoneRates.Rating.Deadly, MonsterTiers.Orange)]
    public void AnEventsMinionsAreTheZonesLowestCon(ZoneRates.Rating r, sbyte tier) =>
        Assert.That(EventCons.Trash(r), Is.EqualTo(tier));

    [Test]
    public void NamedMonstersAreSturdierThanTheirCon()
    {
        Assert.That(MonsterTiers.IsNamed("Nock"), Is.True);
        Assert.That(MonsterTiers.IsNamed("red wolfhound"), Is.False);
        Assert.That(MonsterTiers.NamedSturdiness, Is.GreaterThanOrEqualTo(2.0));
        Assert.That(EventCons.ZoneBossHealth, Is.GreaterThan(EventCons.BossHealth));
    }
}
