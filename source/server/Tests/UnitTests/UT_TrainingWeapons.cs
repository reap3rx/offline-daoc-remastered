using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Starter weapons are the one-footing baseline (owner 2026-11-22): a plain blue-conned weapon of your level, no
/// extra while you are new.</summary>
[TestFixture]
public sealed class UT_TrainingWeapons
{
    [Test]
    public void ATrainingWeaponIsABlueWeaponOfYourLevel()
    {
        for (int l = 1; l <= 50; l++)
        {
            int blue = MonsterTiers.LevelFor(l, MonsterTiers.Blue, l);
            Assert.That(TrainingWeapons.BlueDps(l), Is.EqualTo(1.2 + 0.3 * System.Math.Max(0, blue)).Within(1e-9), $"level {l}");
            Assert.That(blue, Is.LessThanOrEqualTo(l), $"level {l}: a blue is never above you");
        }
        Assert.That(TrainingWeapons.BlueDps(50), Is.GreaterThan(TrainingWeapons.BlueDps(10)));
    }
}
