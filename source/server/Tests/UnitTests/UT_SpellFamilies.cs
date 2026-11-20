using System.Linq;
using DOL.Database;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>One spell per job (SpellFamilies, owner 2026-11-19): a line's ranks of the same spell are one family and a
/// player keeps only its best learned rank; the spellbook's roadmap shows one row a family with its next upgrade.</summary>
[TestFixture]
public sealed class UT_SpellFamilies
{
    private static Spell S(int id, string name, int level, string type = "DirectDamage", int group = 0, double cast = 2.5, int radius = 0) =>
        new(new DbSpell { SpellID = id, Name = name, Type = type, Target = "Enemy", SpellGroup = group, CastTime = cast, Radius = radius, Range = 1500, DamageType = 11 }, level);

    [Test]
    public void TheBestRankOfEachFamilyStays()
    {
        var spells = new Skill[]
        {
            S(1, "Gleam Ray", 1, group: 4101), S(2, "Moon Ray", 6, group: 4101), S(3, "Sun Ray", 17, group: 4101),
            S(4, "Prismatic Flare", 5, "Stun", group: 4121),
            S(5, "Lesser Null Squall", 3, radius: 350), S(6, "Null Squall", 5, radius: 350),   // no group: by what it does
            S(7, "Shadowburst", 1),                                                              // single target: its own family
        };
        var best = SpellFamilies.BestOnly(spells).Select(s => s.Name).ToList();
        Assert.That(best, Is.EquivalentTo(new[] { "Sun Ray", "Prismatic Flare", "Null Squall", "Shadowburst" }));
    }

    [Test]
    public void TheRoadmapShowsWhatYouHaveAndWhatItBecomes()
    {
        var line = new[] { S(1, "Gleam Ray", 1, group: 4101), S(2, "Moon Ray", 6, group: 4101), S(3, "Sun Ray", 17, group: 4101) };
        var rows = SpellFamilies.Roadmap(line, 8).ToList();
        Assert.That(rows, Has.Count.EqualTo(1));
        Assert.That(rows[0].shown.Name, Is.EqualTo("Moon Ray"));
        Assert.That(rows[0].have, Is.True);
        Assert.That(rows[0].next?.Name, Is.EqualTo("Sun Ray"));
        var none = SpellFamilies.Roadmap(line, 0).Single();
        Assert.That(none.have, Is.False);
        Assert.That(none.shown.Name, Is.EqualTo("Gleam Ray"));
    }

    // owner 2026-11-19: "New pets shouldn't replace older pets, because the pets have different utility"
    [Test]
    public void PetsAreNeverRanksOfEachOther()
    {
        var spells = new Skill[]
        {
            S(10, "Underhill Ally", 5, "SummonUnderhill", group: 900), S(11, "Underhill Compatriot", 20, "SummonUnderhill", group: 900),
        };
        Assert.That(SpellFamilies.BestOnly(spells).Select(s => s.Name), Is.EquivalentTo(new[] { "Underhill Ally", "Underhill Compatriot" }));
    }

    // the tooltip's "A more powerful version of ..."
    [Test]
    public void ARankKnowsTheOneBeforeIt()
    {
        var line = new[] { S(1, "Gleam Ray", 1, group: 4101), S(2, "Moon Ray", 6, group: 4101), S(3, "Sun Ray", 17, group: 4101), S(4, "Other", 6) };
        Assert.That(SpellFamilies.PreviousRank(line[2], line)?.Name, Is.EqualTo("Moon Ray"));
        Assert.That(SpellFamilies.PreviousRank(line[1], line)?.Name, Is.EqualTo("Gleam Ray"));
        Assert.That(SpellFamilies.PreviousRank(line[0], line), Is.Null);
        Assert.That(SpellFamilies.PreviousRank(line[3], line), Is.Null);
    }

    // channelling: the quick mark comes sooner with dexterity
    [Test]
    public void TheQuickMarkComesSoonerWithDexterity()
    {
        Assert.That(ChannelCasting.QuickShare(60), Is.EqualTo(0.6).Within(1e-9));
        Assert.That(ChannelCasting.QuickShare(110), Is.EqualTo(0.5).Within(1e-9));
        Assert.That(ChannelCasting.QuickShare(250), Is.EqualTo(0.4).Within(1e-9));
        Assert.That(ChannelCasting.QuickShare(10), Is.EqualTo(0.6).Within(1e-9));
    }
}
