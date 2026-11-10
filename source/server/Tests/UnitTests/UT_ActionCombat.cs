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
    public void QuickSwingSoonestByWeaponSpeed()
    {
        Assert.That(ActionCombat.QuickMinMs(1500), Is.EqualTo(750));       // quicker than a dagger: the floor
        Assert.That(ActionCombat.QuickMinMs(2000), Is.EqualTo(750));
        Assert.That(ActionCombat.QuickMinMs(5500), Is.EqualTo(1750));
        Assert.That(ActionCombat.QuickMinMs(7000), Is.EqualTo(1750));      // the ceiling
        Assert.That(ActionCombat.QuickMinMs(3750), Is.EqualTo(1250));      // halfway
    }

    [Test]
    public void PowerAttackAboutASecondAfterTheLastBlow()
    {
        Assert.That(ActionCombat.AnytimeSoonestMs(2600), Is.EqualTo(1000));    // a sword: 1 s
        Assert.That(ActionCombat.AnytimeSoonestMs(1500), Is.EqualTo(1000));
        Assert.That(ActionCombat.AnytimeSoonestMs(5500), Is.EqualTo(1750));    // never sooner than a plain swing
    }

    [Test]
    public void QuickSwingDamageRampsToFull()
    {
        Assert.That(ActionCombat.QuickDamageFor(1000, 4000), Is.EqualTo(0.25).Within(1e-9));
        Assert.That(ActionCombat.QuickDamageFor(4000, 4000), Is.EqualTo(1.0).Within(1e-9));
        Assert.That(ActionCombat.QuickDamageFor(9000, 4000), Is.EqualTo(1.0).Within(1e-9));   // never above full
        // damage per second stays the classic one: a swing at the soonest does the same per second as a full one
        int full = 3000;
        int soon = ActionCombat.QuickMinMs(full);
        Assert.That(ActionCombat.QuickDamageFor(soon, full) / soon, Is.EqualTo(1.0 / full).Within(1e-9));
    }

    [Test]
    public void ParryAndBlockSaveMoreWithSpecAndArmor()
    {
        // owner 2026-11-09: at spec 50, block 85% (cloth) - 95% (buffed plate), parry 70% - 85%; never all of it
        double cloth = ActionCombat.ArmorScoreFor(51, 0.0, 50);
        double leather = ActionCombat.ArmorScoreFor(102, 0.10, 50);
        double plate = ActionCombat.ArmorScoreFor(102, 0.34, 50);
        double buffedPlate = ActionCombat.ArmorScoreFor(130, 0.34, 50);
        Assert.That(buffedPlate, Is.EqualTo(1.0).Within(1e-9));
        Assert.That(cloth, Is.LessThan(leather));
        Assert.That(leather, Is.LessThan(plate));
        Assert.That(1 - ActionCombat.BlockFactorFor(50, buffedPlate), Is.EqualTo(0.95).Within(0.002));
        Assert.That(1 - ActionCombat.BlockFactorFor(50, cloth), Is.EqualTo(0.85).Within(0.01));
        Assert.That(1 - ActionCombat.BlockFactorFor(50, leather), Is.EqualTo(0.905).Within(0.01));
        Assert.That(1 - ActionCombat.ParryFactorFor(50, buffedPlate), Is.EqualTo(0.85).Within(0.002));
        Assert.That(1 - ActionCombat.ParryFactorFor(50, cloth), Is.EqualTo(0.70).Within(0.01));
        Assert.That(ActionCombat.ParryFactorFor(0, plate), Is.EqualTo(0.8).Within(1e-9));
        Assert.That(ActionCombat.BlockFactorFor(0, plate), Is.EqualTo(0.5).Within(1e-9));
        Assert.That(ActionCombat.BlockFactorFor(80, 1.0), Is.GreaterThan(0.0), "never all of it");

        for (int spec = 0; spec <= 60; spec += 5)
        {
            foreach (double armor in new[] { 0.0, cloth, leather, plate, 1.0 })
            {
                Assert.That(ActionCombat.BlockFactorFor(spec, armor), Is.LessThan(ActionCombat.ParryFactorFor(spec, armor)), "a block saves more than a parry");
                Assert.That(ActionCombat.ParryFactorFor(spec + 5, armor), Is.LessThanOrEqualTo(ActionCombat.ParryFactorFor(spec, armor)));
            }
        }
    }

    [Test]
    public void ChainsGrowWithSkill()
    {
        // owner 2026-11-09: Evade I 1 monster in 0.5 s .. Evade VII 7 in 2 s
        Assert.That(ActionCombat.EvadeChainFor(0), Is.EqualTo((0, 0)));
        Assert.That(ActionCombat.EvadeChainFor(1), Is.EqualTo((1, 500)));
        Assert.That(ActionCombat.EvadeChainFor(7), Is.EqualTo((7, 2000)));
        // Riposte 1 at Parry 7 (0.75 s) .. Riposte 7 at Parry 50 (3 s)
        Assert.That(ActionCombat.RiposteRank(6), Is.EqualTo(0));
        Assert.That(ActionCombat.RiposteRank(7), Is.EqualTo(1));
        Assert.That(ActionCombat.RiposteRank(50), Is.EqualTo(7));
        Assert.That(ActionCombat.ParryChainFor(6), Is.EqualTo((0, 0)));
        Assert.That(ActionCombat.ParryChainFor(7), Is.EqualTo((1, 750)));
        Assert.That(ActionCombat.ParryChainFor(50), Is.EqualTo((7, 3000)));
        // Shields 1 (1 s) .. 50 (4 s): 8 / 9 / 10 with a small / medium / large shield at 50, the size alone at 1
        Assert.That(ActionCombat.BlockChainFor(1, 1), Is.EqualTo((1, 1000)));
        Assert.That(ActionCombat.BlockChainFor(1, 3), Is.EqualTo((3, 1000)));
        Assert.That(ActionCombat.BlockChainFor(50, 1), Is.EqualTo((8, 4000)));
        Assert.That(ActionCombat.BlockChainFor(50, 2), Is.EqualTo((9, 4000)));
        Assert.That(ActionCombat.BlockChainFor(50, 3), Is.EqualTo((10, 4000)));
        Assert.That(ActionCombat.BlockChainArc(1), Is.EqualTo(180));
        Assert.That(ActionCombat.BlockChainArc(2), Is.EqualTo(270));
        Assert.That(ActionCombat.BlockChainArc(3), Is.EqualTo(360));
    }

    [Test]
    public void EarlySwingsCostEndurance()
    {
        // owner 2026-11-09: 5% of max endurance at the soonest swing (first 15%, too much), falling to nothing at the
        // whole swing time
        int full = 3000;
        int soon = ActionCombat.QuickMinMs(full);
        Assert.That(ActionCombat.QuickSwingEnduranceShare(soon, full), Is.EqualTo(0.05).Within(1e-9));
        Assert.That(ActionCombat.QuickSwingEnduranceShare(full, full), Is.EqualTo(0.0));
        Assert.That(ActionCombat.QuickSwingEnduranceShare(9000, full), Is.EqualTo(0.0));
        Assert.That(ActionCombat.QuickSwingEnduranceShare((soon + full) / 2, full), Is.EqualTo(0.025).Within(0.001));
    }

    [Test]
    public void DualWieldQuickensThePlainSwing()
    {
        // owner 2026-11-09: higher dual wield spec, a faster plain swing (25% quicker at 50)
        Assert.That(ActionCombat.DualWieldSwingFactor(0), Is.EqualTo(1.0).Within(1e-9));
        Assert.That(ActionCombat.DualWieldSwingFactor(25), Is.EqualTo(0.875).Within(1e-9));
        Assert.That(ActionCombat.DualWieldSwingFactor(50), Is.EqualTo(0.75).Within(1e-9));
        Assert.That(ActionCombat.DualWieldSwingFactor(60), Is.EqualTo(0.75).Within(1e-9));
    }

    [Test]
    public void DefenseWindowsGrowWithSkill()
    {
        // owner 2026-10-28: 0.1 s dodge, 0.15 s block, 0.2 s parry to start
        Assert.That(ActionCombat.DodgeWindowFor(0, 0), Is.EqualTo(100));
        Assert.That(ActionCombat.BlockWindowFor(1, 0), Is.EqualTo(150));
        Assert.That(ActionCombat.ParryWindowFor(1, 0), Is.EqualTo(200));
        Assert.That(ActionCombat.ParryWindowFor(0, 0), Is.EqualTo(200));
        Assert.That(ActionCombat.ParryWindowFor(50, 0), Is.GreaterThan(ActionCombat.ParryWindowFor(20, 0)));
        Assert.That(ActionCombat.DodgeWindowFor(7, 0), Is.EqualTo(310));
        Assert.That(ActionCombat.ParryWindowFor(30, 3), Is.EqualTo(ActionCombat.ParryWindowFor(30, 0) + 60), "Mastery of Parrying widens it");
    }

    [Test]
    public void MissedDodgeCostsMostAndParryLeast()
    {
        foreach (int parry in new[] { 1, 4, 7, 12 })
        {
            int block = ActionCombat.BlockCostFor(parry, 0);
            int dodge = ActionCombat.DodgeCostFor(parry, block);
            Assert.That(block, Is.GreaterThan(parry));
            Assert.That(dodge, Is.GreaterThan(block));
        }

        Assert.That(ActionCombat.BlockCostFor(6, 11), Is.EqualTo(11), "at least the shield's own reactive");
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
        Assert.That(ActionCombat.ParryCooldownMs, Is.EqualTo(500));
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
