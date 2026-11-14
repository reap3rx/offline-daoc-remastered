using DOL.GS;
using NUnit.Framework;
using Need = DOL.GS.AutonomousNearbyHelp.Need;

namespace DOL.UnitTests
{
    /// <summary>World bots help their realm's players and bots near them, grouped or not (bugs N11, 2026-11-13).</summary>
    [TestFixture]
    public class UT_NearbyHelpNov13
    {
        [TestCase(90, 0, 0, ExpectedResult = Need.None, TestName = "Nothing on the ally")]
        [TestCase(90, 1, 0, ExpectedResult = Need.Ordinary, TestName = "One yellow monster at good health")]
        [TestCase(55, 1, 0, ExpectedResult = Need.Trouble, TestName = "Low health is trouble")]
        [TestCase(95, 2, -1, ExpectedResult = Need.Trouble, TestName = "Two monsters is trouble")]
        [TestCase(95, 1, 1, ExpectedResult = Need.Trouble, TestName = "An orange monster is trouble")]
        public Need Assess(int hp, int monsters, int con) => AutonomousNearbyHelp.Assess(hp, monsters, con);

        [TestCase(Need.Trouble, true, 80, 0, 99, ExpectedResult = true, TestName = "Always helps a player in trouble")]
        [TestCase(Need.Ordinary, true, 80, 0, 0, ExpectedResult = false, TestName = "Leaves a player's ordinary fight (loot)")]
        [TestCase(Need.Ordinary, false, 80, 0, 10, ExpectedResult = true, TestName = "Sometimes joins a bot's fight")]
        [TestCase(Need.Ordinary, false, 80, 0, 90, ExpectedResult = false, TestName = "Not always")]
        [TestCase(Need.Trouble, false, 40, 0, 0, ExpectedResult = false, TestName = "Not while badly hurt itself")]
        [TestCase(Need.Trouble, false, 90, 2, 0, ExpectedResult = false, TestName = "Not against a red monster")]
        [TestCase(Need.Trouble, false, 90, -3, 0, ExpectedResult = false, TestName = "Not against a grey monster")]
        public bool Joins(Need need, bool human, int botHp, int con, int roll) =>
            AutonomousNearbyHelp.Joins(need, human, botHp, con, roll);

        [Test]
        public void RollIsStablePerBotAndMonster()
        {
            Assert.That(AutonomousNearbyHelp.Roll(5, 9), Is.EqualTo(AutonomousNearbyHelp.Roll(5, 9)));
            Assert.That(AutonomousNearbyHelp.Roll(5, 9), Is.InRange(0, 99));
        }
    }
}
