using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>A blank one-off is made again at the level its condition tells (owner 2026-11-14).</summary>
    [TestFixture]
    public class UT_LostUniqueNov14
    {
        [TestCase(7999, 30, ExpectedResult = 4, TestName = "Level 4 armour")]
        [TestCase(11999, 30, ExpectedResult = 6, TestName = "Level 6 armour")]
        [TestCase(20000, 30, ExpectedResult = 10, TestName = "Level 10 armour")]
        [TestCase(19995, 30, ExpectedResult = 10, TestName = "A little worn")]
        [TestCase(0, 17, ExpectedResult = 17, TestName = "No condition: the owner's level")]
        [TestCase(500000, 30, ExpectedResult = 51, TestName = "Capped at 51")]
        public int LevelFromCondition(int condition, int owner) => LostUniqueStandIn.LevelFromCondition(condition, owner);
    }
}
