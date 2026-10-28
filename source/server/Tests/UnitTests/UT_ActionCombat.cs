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

[TestFixture]
public sealed class UT_ActionCombatArchery
{
    [Test]
    public void FullDrawHardlyMissesAndFullCriticalAlwaysCrits()
    {
        ActionCombat.ShotNumbers normal = ActionCombat.ShotFor(1.0, false, false, 2.0);
        Assert.That(normal.Effectiveness, Is.EqualTo(1.0));
        Assert.That(normal.Miss, Is.EqualTo(ActionCombat.FullDrawMiss));
        ActionCombat.ShotNumbers crit = ActionCombat.ShotFor(1.0, false, true, 2.0);
        Assert.That(crit.CritChance, Is.EqualTo(1.0));
        Assert.That(crit.CritEffectiveness, Is.EqualTo(2.0));
    }

    [Test]
    public void EarlyReleaseIsWeakerAndMissesMore()
    {
        ActionCombat.ShotNumbers half = ActionCombat.ShotFor(0.5, false, false, 2.0);
        ActionCombat.ShotNumbers most = ActionCombat.ShotFor(0.9, false, false, 2.0);
        Assert.That(half.Effectiveness, Is.LessThan(most.Effectiveness));
        Assert.That(half.Miss, Is.GreaterThan(most.Miss));
        ActionCombat.ShotNumbers critHalf = ActionCombat.ShotFor(0.5, false, true, 2.0);
        Assert.That(critHalf.CritChance, Is.LessThan(0.1), "an early critical shot rarely crits");
        Assert.That(critHalf.Miss, Is.GreaterThan(half.Miss));
    }

    [Test]
    public void OverdrawHitsHarderButMissesOften()
    {
        ActionCombat.ShotNumbers over = ActionCombat.ShotFor(1.0, true, false, 2.0);
        Assert.That(over.Effectiveness, Is.GreaterThan(1.0));
        Assert.That(over.Miss, Is.GreaterThan(0.3));
    }

    [Test]
    public void MissedDefenseCostsAReactivesFatigue()
    {
        // speed x rating / 40, +1 under 4.0 speed (StyleProcessor.CalculateEnduranceCost)
        Assert.That(StyleProcessor.RawFatigue(ActionCombat.MissedDefenseRating, 37), Is.EqualTo(7));   // 3.7 sword: 6 + 1
        Assert.That(StyleProcessor.RawFatigue(ActionCombat.MissedDefenseRating, 55), Is.EqualTo(9));   // 5.5 two-hander
        Assert.That(StyleProcessor.RawFatigue(10, 25), Is.EqualTo(7));
        Assert.That(ActionCombat.ParryWindowMs + ActionCombat.ParryCooldownMs, Is.EqualTo(750));
    }

    [Test]
    public void PoisonBagSavesItsContents()
    {
        PoisonBagState bag = PoisonBag.Parse("lethal_poison:12,,weak_poison:3,dead:0;1");
        Assert.That(bag.Templates, Is.EqualTo(new[] { "lethal_poison", "", "weak_poison", "" }));
        Assert.That(bag.Counts, Is.EqualTo(new[] { 12, 0, 3, 0 }));
        Assert.That(bag.Set, Is.EqualTo(1));
        Assert.That(bag.Legacy, Is.False);
        Assert.That(PoisonBag.Format(bag), Is.EqualTo("lethal_poison:12,,weak_poison:3,;1"));

        // the first version only pointed at backpack stacks: those are taken in on first use
        PoisonBagState old = PoisonBag.Parse("lethal_poison,weak_poison,,;0");
        Assert.That(old.Legacy, Is.True);
        Assert.That(old.Templates[1], Is.EqualTo("weak_poison"));
        Assert.That(PoisonBag.Parse("").Templates, Is.All.Empty);
    }

    [Test]
    public void PotionBagTakesPotionsOnly()
    {
        Assert.That(PotionBag.Fits(40, (int) eObjectType.Magical, 15563), Is.True);          // a potion
        Assert.That(PotionBag.Fits(40, (int) eObjectType.AlchemyTincture, 9001), Is.True);   // a tincture
        Assert.That(PotionBag.Fits(40, (int) eObjectType.GenericItem, 0), Is.False);         // a quest item
        Assert.That(PotionBag.Fits(40, (int) eObjectType.Poison, 0), Is.False);              // the poison bag's
        Assert.That(PotionBag.Fits(35, (int) eObjectType.Magical, 77), Is.False);            // a charged ring
        Assert.That(PotionBag.IsBagSlot(eInventorySlot.FirstBagHorse) && PotionBag.IsBagSlot(eInventorySlot.LastBagHorse), Is.True);
        Assert.That(PotionBag.IsBagSlot(eInventorySlot.LastBackpack), Is.False);
    }
}
