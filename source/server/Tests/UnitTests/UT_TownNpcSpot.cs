using System.Numerics;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>The town helpers' spot maths (TownNpcSpot): a heading's point and the heading back to where they look.</summary>
    [TestFixture]
    public sealed class UT_TownNpcSpot
    {
        [TestCase(0, 0)]
        [TestCase(1024, 0)]
        [TestCase(2048, 90)]
        [TestCase(3000, -45)]
        public void FacingBack_IsTheWayBack(int heading, int turn)
        {
            var from = new Vector3(1000, 2000, 0);
            Vector3 p = TownNpcSpot.Point(from, (ushort) heading, turn, 300);
            Assert.That(Vector3.Distance(p, from), Is.EqualTo(300).Within(0.5));
            // from the spot, looking back at the start, is the opposite way
            int back = (heading + (int) System.Math.Round(turn * 4096 / 360.0) + 2048) % 4096;
            Assert.That(TownNpcSpot.Facing(p, from), Is.EqualTo(back).Within(2));
        }

        [Test]
        public void HeadingZero_LooksSouth()
        {
            // DAoC: heading 0 faces +Y (the GameObject heading convention used across the server)
            Vector3 p = TownNpcSpot.Point(Vector3.Zero, 0, 0, 100);
            Assert.That(p.X, Is.EqualTo(0).Within(0.01));
            Assert.That(p.Y, Is.EqualTo(100).Within(0.01));
            Assert.That(TownNpcSpot.Facing(Vector3.Zero, new Vector3(0, 100, 0)), Is.EqualTo(0));
        }
    }
}
