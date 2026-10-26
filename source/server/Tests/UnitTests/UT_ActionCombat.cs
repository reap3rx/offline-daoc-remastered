using DOL.Database;
using DOL.GS;
using DOL.GS.Styles;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>
/// Action Combat: which button a style belongs to, and how much of a blow a timed parry / block lets through.
/// </summary>
[TestFixture]
public sealed class UT_ActionCombat
{
    private static Style Make(Style.eOpening opening, int value, Style.eAttackResultRequirement result) =>
        new(new DbStyle
        {
            ID = 1,
            Name = "Test",
            SpecKeyName = "Slash",
            OpeningRequirementType = (int) opening,
            OpeningRequirementValue = value,
            AttackResultRequirement = (int) result
        }, null);

    [Test]
    public void StylesSortIntoTheirButtons()
    {
        Assert.That(ActionCombat.KindOf(Make(Style.eOpening.Offensive, 0, Style.eAttackResultRequirement.Any)), Is.EqualTo("anytime"));
        Assert.That(ActionCombat.KindOf(Make(Style.eOpening.Positional, (int) Style.eOpeningPosition.Back, Style.eAttackResultRequirement.Any)), Is.EqualTo("position"));
        Assert.That(ActionCombat.KindOf(Make(Style.eOpening.Positional, (int) Style.eOpeningPosition.Front, Style.eAttackResultRequirement.Any)), Is.EqualTo("position"));
        Assert.That(ActionCombat.KindOf(Make(Style.eOpening.Defensive, 0, Style.eAttackResultRequirement.Parry)), Is.EqualTo("reactive"));
        Assert.That(ActionCombat.KindOf(Make(Style.eOpening.Defensive, 0, Style.eAttackResultRequirement.Evade)), Is.EqualTo("reactive"));
        Assert.That(ActionCombat.KindOf(Make(Style.eOpening.Offensive, 0, Style.eAttackResultRequirement.Parry)), Is.EqualTo("reactive"));
        Assert.That(ActionCombat.KindOf(Make(Style.eOpening.Offensive, 412, Style.eAttackResultRequirement.Style)), Is.EqualTo("chain"));
        Assert.That(ActionCombat.KindOf(Make(Style.eOpening.Offensive, 0, Style.eAttackResultRequirement.Hit)), Is.EqualTo("chain"));
    }

    [Test]
    public void ParrySpecReducesWhatGetsThrough()
    {
        Assert.That(ActionCombat.ParryFactorForSpec(0), Is.EqualTo(0.8).Within(1e-9));
        Assert.That(ActionCombat.ParryFactorForSpec(1), Is.EqualTo(0.6).Within(1e-9));
        Assert.That(ActionCombat.ParryFactorForSpec(50), Is.EqualTo(0.1).Within(1e-9));
        Assert.That(ActionCombat.ParryFactorForSpec(25), Is.LessThan(ActionCombat.ParryFactorForSpec(10)));
        Assert.That(ActionCombat.ParryFactorForSpec(80), Is.EqualTo(0.05).Within(1e-9));
    }

    [Test]
    public void ShieldSpecReducesWhatGetsThrough()
    {
        Assert.That(ActionCombat.BlockFactorForSpec(0), Is.EqualTo(0.5).Within(1e-9));
        Assert.That(ActionCombat.BlockFactorForSpec(1), Is.EqualTo(0.4).Within(1e-9));
        Assert.That(ActionCombat.BlockFactorForSpec(50), Is.EqualTo(0.0).Within(1e-9));
    }

    [Test]
    public void PartialDefenseNeedsATimedParryOrBlock()
    {
        AttackData ad = new() { AttackResult = eAttackResult.Parried };
        Assert.That(ad.IsActionPartialDefense, Is.False, "a dice parry lets nothing through");
        ad.ActionDefense = eActionDefense.Parry;
        Assert.That(ad.IsActionPartialDefense, Is.True);
        ad.AttackResult = eAttackResult.HitUnstyled;
        Assert.That(ad.IsActionPartialDefense, Is.False);
        ad.ActionDefense = eActionDefense.Dodge;
        ad.AttackResult = eAttackResult.Evaded;
        Assert.That(ad.IsActionPartialDefense, Is.False, "a dodge avoids the whole blow");
    }
}
