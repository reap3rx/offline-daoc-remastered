using System.Linq;
using DOL.GS;
using DOL.GS.Quests;
using DOL.Network;
using NUnit.Framework;

namespace DOL.UnitTests;

[TestFixture]
public class UT_ZoneBounties
{
    static BountyTargetCandidate T(string name, sbyte tier, int count, ushort zone = 200) => new()
    {
        Name = name, Tier = tier, SpawnCount = count, ZoneId = zone, RegionId = 200, ZoneName = "Lough Derg",
        RepresentativeMobId = name
    };

    static readonly BountyTargetCandidate[] Derg =
    {
        T("badger", MonsterTiers.Green, 17),
        T("lough wolf", MonsterTiers.Blue, 14),
        T("siabra archer", MonsterTiers.Yellow, 3),
        T("druid", MonsterTiers.Yellow, 6),
        T("villainous youth lieutenant", MonsterTiers.Orange, 2),
        T("Bertha", MonsterTiers.Orange, 1),
        T("rowdy ringleader", MonsterTiers.Red, 1),
        T("Hughar", MonsterTiers.Red, 1),
        T("ambient rat", MonsterTiers.Grey, 9),
        T("lone toad", MonsterTiers.Green, 1),
    };

    [Test]
    public void SoloHuntsPointAtGreensBluesAndYellowsThatStandInNumber()
    {
        var pool = ZoneBounties.Pool(Derg, BountyDifficulty.Normal);
        Assert.That(pool.Select(t => t.Name), Is.EquivalentTo(new[] { "badger", "lough wolf", "siabra archer", "druid" }));
    }

    [Test]
    public void SmallGroupHuntsPointAtOrangesOrYellowsInNumber()
    {
        var pool = ZoneBounties.Pool(Derg, BountyDifficulty.Hard);
        Assert.That(pool.Select(t => t.Name), Is.EquivalentTo(new[] { "druid", "villainous youth lieutenant", "Bertha" }));
    }

    [Test]
    public void LargeGroupHuntsPointAtRedsAndFallBackToOranges()
    {
        Assert.That(ZoneBounties.Pool(Derg, BountyDifficulty.VeryHard).Select(t => t.Name),
            Is.EquivalentTo(new[] { "rowdy ringleader", "Hughar" }));
        var noReds = Derg.Where(t => t.Tier != MonsterTiers.Red).ToArray();
        Assert.That(ZoneBounties.Pool(noReds, BountyDifficulty.VeryHard).All(t => t.Tier == MonsterTiers.Orange), Is.True);
    }

    [Test]
    public void GreyCrittersAreNeverBounties()
    {
        foreach (BountyDifficulty size in new[] { BountyDifficulty.Normal, BountyDifficulty.Hard, BountyDifficulty.VeryHard })
            Assert.That(ZoneBounties.Pool(Derg, size).Any(t => t.Tier == MonsterTiers.Grey), Is.False);
    }

    [Test]
    public void TheLastHuntIsNotRepeatedUnlessItIsTheOnlyOne()
    {
        Assert.That(ZoneBounties.Pool(Derg, BountyDifficulty.VeryHard, "Hughar").Select(t => t.Name),
            Is.EqualTo(new[] { "rowdy ringleader" }));
        var one = new[] { T("Hughar", MonsterTiers.Red, 1) };
        Assert.That(ZoneBounties.Pool(one, BountyDifficulty.VeryHard, "hughar"), Has.Length.EqualTo(1));
    }

    [TestCase(BountyDifficulty.Normal, MonsterTiers.Green, 17, 8)]
    [TestCase(BountyDifficulty.Normal, MonsterTiers.Blue, 14, 6)]
    [TestCase(BountyDifficulty.Normal, MonsterTiers.Yellow, 6, 3)]
    [TestCase(BountyDifficulty.Normal, MonsterTiers.Green, 2, 6)]
    [TestCase(BountyDifficulty.Hard, MonsterTiers.Yellow, 6, 8)]
    [TestCase(BountyDifficulty.Hard, MonsterTiers.Orange, 2, 2)]
    [TestCase(BountyDifficulty.Hard, MonsterTiers.Orange, 1, 2)]
    [TestCase(BountyDifficulty.VeryHard, MonsterTiers.Red, 1, 1)]
    [TestCase(BountyDifficulty.VeryHard, MonsterTiers.Orange, 1, 3)]
    public void KillsFollowTheTierAndNeverOutrunTheZone(BountyDifficulty size, sbyte tier, int count, int kills) =>
        Assert.That(ZoneBounties.KillsFor(size, tier, count), Is.EqualTo(kills));

    [Test]
    public void KillsCountOnlyInTheBountysZone()
    {
        var wolf = T("lough wolf", MonsterTiers.Blue, 14);
        Assert.Multiple(() =>
        {
            Assert.That(ZoneBounties.Counts(wolf, "Lough Wolf", eRealm.None, 200), Is.True);
            Assert.That(ZoneBounties.Counts(wolf, "lough wolf", eRealm.None, 201), Is.False);
            Assert.That(ZoneBounties.Counts(wolf, "lough wolf", eRealm.Hibernia, 200), Is.False);
            Assert.That(ZoneBounties.Counts(wolf, "lough wolf", eRealm.None, null), Is.False);
            Assert.That(ZoneBounties.Counts(wolf, "badger", eRealm.None, 200), Is.False);
        });
    }

    [TestCase("solo", BountyDifficulty.Normal)]
    [TestCase("small group", BountyDifficulty.Hard)]
    [TestCase("large group", BountyDifficulty.VeryHard)]
    [TestCase("big group", BountyDifficulty.VeryHard)]
    [TestCase("hard", BountyDifficulty.Hard)]
    public void SizesParse(string text, BountyDifficulty size)
    {
        Assert.That(ZoneBounties.TryParseSize(text, out BountyDifficulty parsed), Is.True);
        Assert.That(parsed, Is.EqualTo(size));
    }

    [Test]
    public void MarksAndCapGoldGrowWithSizeAndHalveOnReroll()
    {
        Assert.Multiple(() =>
        {
            Assert.That(ZoneBounties.Marks(BountyDifficulty.Normal, false), Is.EqualTo(1));
            Assert.That(ZoneBounties.Marks(BountyDifficulty.Normal, true), Is.EqualTo(1));
            Assert.That(ZoneBounties.Marks(BountyDifficulty.Hard, false), Is.EqualTo(3));
            Assert.That(ZoneBounties.Marks(BountyDifficulty.VeryHard, true), Is.EqualTo(4));
            Assert.That(ZoneBounties.CapGold(BountyDifficulty.VeryHard, false), Is.EqualTo(100));
            Assert.That(ZoneBounties.CapGold(BountyDifficulty.Normal, true), Is.EqualTo(7));
        });
    }

    [Test]
    public void ZoneJournalFitsTheOldClientAndSaysItPaysAtYourLevel()
    {
        var target = T("villainous youth lieutenant with an unusually long name for testing", MonsterTiers.Orange, 2);
        string d = BountyQuest.FormatZoneJournalDescription(target, 1, 2, false, BountyDifficulty.Hard, false);
        string n = BountyQuest.FormatZoneQuestName(target, BountyDifficulty.Hard);
        Assert.Multiple(() =>
        {
            Assert.That(BaseServer.DefaultEncoding.GetByteCount(d), Is.LessThanOrEqualTo(255));
            Assert.That(d, Does.Contain("1/2"));
            Assert.That(d, Does.Contain("Pays at your level"));
            Assert.That(n, Does.StartWith("Small Group Bounty: "));
        });
    }

    [Test]
    public void EventJournalFitsTheOldClient()
    {
        var t = T("The Summoner's Muster and a very long event title for the journal", MonsterTiers.Yellow, 6);
        string d = BountyQuest.FormatEventJournalDescription(t, 2, ZoneBounties.EventKills, false, false);
        Assert.That(BaseServer.DefaultEncoding.GetByteCount(d), Is.LessThanOrEqualTo(255));
        Assert.That(d, Does.Contain("2/6"));
    }
}
