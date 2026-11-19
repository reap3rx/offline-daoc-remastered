using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>
/// Fixed con tiers and full scaling (gameutils/MonsterTiers.cs, owner 2026-11-19): the level a monster takes for a fight
/// cons its tier to whoever it fights, and its tier is its con to everyone.
/// </summary>
[TestFixture, NonParallelizable]
public sealed class UT_MonsterTiers
{
    private static void Ready(bool on) =>
        typeof(MonsterTiers).GetField("_ready", BindingFlags.NonPublic | BindingFlags.Static)!.SetValue(null, on);

    [Test]
    public void FightLevelConsItsTierAtEveryLevel()
    {
        for (int b = 2; b <= 50; b++)                          // (level 1 has no green: nothing is below level 0)
            for (sbyte t = MonsterTiers.Green; t <= MonsterTiers.Red; t++)
            {
                int l = MonsterTiers.LevelFor(b, t, 10);
                Assert.That(ConLevels.GetConLevel(b, l), Is.EqualTo((int) t), $"level {b}, tier {t}: {l}");
            }
    }

    [Test]
    public void CrittersConGreyAndPurpleNeverBelowItsOwnLevel()
    {
        for (int b = 5; b <= 50; b++)
            Assert.That(ConLevels.GetConLevel(b, MonsterTiers.LevelFor(b, MonsterTiers.Grey, 1)), Is.EqualTo(-3), $"level {b}");
        Assert.That(MonsterTiers.LevelFor(20, MonsterTiers.Purple, 75), Is.EqualTo(75));
        Assert.That(ConLevels.GetConLevel(30, MonsterTiers.LevelFor(30, MonsterTiers.Purple, 5)), Is.EqualTo(3));
        Assert.That(MonsterTiers.LevelFor(30, MonsterTiers.Yellow, 5), Is.EqualTo(30));
    }

    [Test]
    public void ATieredMonsterConsItsTierToAnyone()
    {
        Ready(true);
        try
        {
            var orc = (GameNPC) RuntimeHelpers.GetUninitializedObject(typeof(GameNPC));
            orc.MonsterTier = MonsterTiers.Orange;
            var critter = (GameNPC) RuntimeHelpers.GetUninitializedObject(typeof(GameNPC));
            critter.MonsterTier = MonsterTiers.Grey;
            var plain = (GameNPC) RuntimeHelpers.GetUninitializedObject(typeof(GameNPC));
            plain.MonsterTier = MonsterTiers.None;

            Assert.That(MonsterTiers.TryCon(plain, orc, out int c), Is.True);
            Assert.That(c, Is.EqualTo(1));
            Assert.That(MonsterTiers.TryCon(orc, plain, out c), Is.True);
            Assert.That(c, Is.EqualTo(-1));
            Assert.That(MonsterTiers.TryCon(plain, critter, out c), Is.True);
            Assert.That(c, Is.EqualTo(-3));
            Assert.That(MonsterTiers.TryCon(orc, critter, out _), Is.False, "monster against monster: by level as before");
        }
        finally
        {
            Ready(false);
        }
    }
}
