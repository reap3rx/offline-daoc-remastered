using DOL.Database;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>
/// The King / Queen's Fealty summons must count as pet effects: releasing a pet (the pet window's
/// RELEASE, Dismiss Troops, a commander's death releasing its retainers) only ends effects of type Pet.
/// </summary>
[TestFixture]
public sealed class UT_KingFealty
{
    private static Spell Summon(string type) => new(new DbSpell
    {
        SpellID = 64100,
        Name = type,
        Type = type,
        Target = "Self",
        Duration = 65535,
        LifeDrainReturn = 64001,
        Damage = -95,
        Value = 50
    }, 1);

    [TestCase("SummonRoyalCommander")]
    [TestCase("SummonRetainer")]
    public void RoyalSummonsArePetEffects(string type)
    {
        Assert.That(EffectHelper.GetEffectFromSpell(Summon(type)), Is.EqualTo(eEffect.Pet),
            $"{type} must map to eEffect.Pet or released / orphaned royal pets never leave");
    }

    [Test]
    public void BonedancerSummonsStillArePetEffects()
    {
        Assert.That(EffectHelper.GetEffectFromSpell(Summon("SummonCommander")), Is.EqualTo(eEffect.Pet));
        Assert.That(EffectHelper.GetEffectFromSpell(Summon("SummonMinion")), Is.EqualTo(eEffect.Pet));
    }
}
