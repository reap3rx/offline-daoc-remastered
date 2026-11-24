using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Owner 2026-11-22: "When I made a level 1 blademaster, I was doing 0 damage on a green badger ... We should
    /// make sure that any hit does some damage, even if resistances are factored in." (LevelScaling.Whole)</summary>
    [TestFixture]
    public sealed class UT_WholeDamage
    {
        [TestCase(0.3)] [TestCase(0.7)] [TestCase(0.0)] [TestCase(-2.0)] [TestCase(double.NaN)]
        public void ALandedHitNeverDoesNothing(double damage)
        {
            Assert.That(LevelScaling.Whole(damage, true), Is.EqualTo(1));
        }

        [Test]
        public void AFullyTurnedAsideBlowOrAFullyResistedSpellMayDoNothing()
        {
            Assert.That(LevelScaling.Whole(0.0, false), Is.EqualTo(0));
            Assert.That(LevelScaling.Whole(0.7, false), Is.EqualTo(0));
        }

        [TestCase(1.0, 1)] [TestCase(7.4, 7)] [TestCase(7.99, 7)] [TestCase(250.5, 250)]
        public void BiggerHitsAreCutDownAsBefore(double damage, int expected)
        {
            Assert.That(LevelScaling.Whole(damage, true), Is.EqualTo(expected));
            Assert.That(LevelScaling.Whole(damage, false), Is.EqualTo(expected));
        }
    }
}
