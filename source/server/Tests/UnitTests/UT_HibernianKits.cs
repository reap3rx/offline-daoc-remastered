using System.Linq;
using DOL.Database;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>The Warden / Bard / Druid kits (HibernianKits, agreed 2026-11-20).</summary>
[TestFixture]
public sealed class UT_HibernianKits
{
    private static Spell Pet(int id, string name, int level) =>
        new(new DbSpell { SpellID = id, Name = name, Type = "SummonDruidPet", Target = "Self", CastTime = 6 }, level);

    // owner: "One summon with bear / wolf / wisp forms" - the nature spirit's ranks are one button (other pets stay apart)
    [Test]
    public void TheNatureSpiritIsOneSummon()
    {
        var spells = new Skill[]
        {
            Pet(5251, "Call Minor Nature Spirit", 1), Pet(5253, "Call Nature Spirit", 12), Pet(5255, "Call Greater Nature Spirit", 32),
            Pet(9999, "Some Other Pet", 5),
        };
        Assert.That(SpellFamilies.BestOnly(spells).Select(s => s.Name),
            Is.EquivalentTo(new[] { "Call Greater Nature Spirit", "Some Other Pet" }));
    }

    [Test]
    public void TheRanksComeWhereAgreed()
    {
        Assert.That(HibernianKits.BulwarkAt, Is.EqualTo(new[] { 2, 10, 18 }));
        Assert.That(HibernianKits.BrambleAt, Is.EqualTo(new[] { 5, 15, 25, 35, 45 }));
        Assert.That(HibernianKits.RallyReuseMs, Is.EqualTo(30000));
        Assert.That(HibernianKits.AnthemReuse, Is.EqualTo(20));
        Assert.That(HibernianKits.CrescendoMax, Is.EqualTo(5));
        Assert.That(HibernianKits.RejuvMax, Is.EqualTo(3));
    }
}
