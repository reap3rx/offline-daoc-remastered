using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Midgard's class kits (MidgardKits, StyleRework.Midgard - the owner's answers in "Midgard Class Rework - the plan",
/// 2026-11-24).</summary>
[TestFixture]
public sealed class UT_MidgardKits
{
    [Test]
    public void TheClassIdsAreMidgards()
    {
        Assert.That(MidgardKits.Thane, Is.EqualTo((int) eCharacterClass.Thane));
        Assert.That(MidgardKits.Warrior, Is.EqualTo((int) eCharacterClass.Warrior));
        Assert.That(MidgardKits.Shadowblade, Is.EqualTo((int) eCharacterClass.Shadowblade));
        Assert.That(MidgardKits.Skald, Is.EqualTo((int) eCharacterClass.Skald));
        Assert.That(MidgardKits.Hunter, Is.EqualTo((int) eCharacterClass.Hunter));
        Assert.That(MidgardKits.Healer, Is.EqualTo((int) eCharacterClass.Healer));
        Assert.That(MidgardKits.Spiritmaster, Is.EqualTo((int) eCharacterClass.Spiritmaster));
        Assert.That(MidgardKits.Shaman, Is.EqualTo((int) eCharacterClass.Shaman));
        Assert.That(MidgardKits.Runemaster, Is.EqualTo((int) eCharacterClass.Runemaster));
        Assert.That(MidgardKits.Bonedancer, Is.EqualTo((int) eCharacterClass.Bonedancer));
        Assert.That(MidgardKits.Berserker, Is.EqualTo((int) eCharacterClass.Berserker));
        Assert.That(MidgardKits.Savage, Is.EqualTo((int) eCharacterClass.Savage));
    }

    // owner: "Maybe they get more offense but take a bit more damage ... make sure it's balanced"
    [Test]
    public void TheGripIsRiskAgainstReward()
    {
        Assert.That(MidgardKits.GripBonus, Is.EqualTo(MidgardKits.GripRisk - 1.0).Within(1e-9), "a two-hander gives what it gains");
        Assert.That(MidgardKits.GripGuard, Is.LessThan(1.0));
        Assert.That(1.0 - MidgardKits.GripGuard, Is.LessThanOrEqualTo(MidgardKits.GripBonus), "the board's cover no more than the two-hander's bite");
    }

    // owner: "make sure that ... they don't outdamage the pure fighters like Warriors and Heroes"
    [Test]
    public void ThorsLightningStaysUnderThePaladinsBlast()
    {
        Assert.That(StyleRework.ThaneBolts, Has.Length.EqualTo(9));
        Assert.That(StyleRework.ThaneBolts, Does.Contain(159).And.Contain(190).And.Contain(175));
    }

    [Test]
    public void TheShadowbladesMarksAreItsPositionals()
    {
        Assert.That(StyleRework.ShadowbladeMarks, Does.Contain(335).And.Contain(192).And.Contain(201));
        Assert.That(StyleRework.ShadowbladeMarks, Does.Not.Contain(StyleRework.LeftRavager));
    }

    [Test]
    public void OnlyMidgardsFightersHaveAGrip()
    {
        foreach (int c in new[] { MidgardKits.Thane, MidgardKits.Warrior, MidgardKits.Berserker, MidgardKits.Savage, MidgardKits.Skald,
                     MidgardKits.Shadowblade, MidgardKits.Hunter })
            Assert.That(MidgardKits.IsMidgardMelee(c), Is.True, c.ToString());
        foreach (int c in new[] { MidgardKits.Healer, MidgardKits.Shaman, MidgardKits.Runemaster, MidgardKits.Spiritmaster,
                     MidgardKits.Bonedancer, AlbionKits.Armsman, 34 })
            Assert.That(MidgardKits.IsMidgardMelee(c), Is.False, c.ToString());
    }

    [Test]
    public void TheKitIdsAreInMidgardsRange()
    {
        foreach (int id in new[] { MidgardKits.RavenWard, MidgardKits.MarchOfTheDead, MidgardKits.SongOfAesir + 1, MidgardKits.RoarDaze })
            Assert.That(id, Is.InRange(97400, 97499));
    }
}
