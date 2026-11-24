using System.Linq;
using System.Numerics;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Treasure chests (owner 2026-11-22, the Connacht brief): near monster spawns rather than anywhere, and a
    /// better chance at better loot where the area is harder.</summary>
    [TestFixture]
    public sealed class UT_TreasureDanger
    {
        [Test]
        public void ChestsStandByTheCamps_TheWildOnlyWhenThereAreTooFew()
        {
            Assert.That(TreasureChests.Copies(WorldFeatureSpots.Kind.Camp, 50), Is.GreaterThan(TreasureChests.Copies(WorldFeatureSpots.Kind.Ridge, 50) * 4));
            Assert.That(TreasureChests.Copies(WorldFeatureSpots.Kind.Wild, TreasureChests.PerZone), Is.EqualTo(0));
            Assert.That(TreasureChests.Copies(WorldFeatureSpots.Kind.Wild, 5), Is.EqualTo(1), "a zone with few camps still fills");
        }

        [Test]
        public void AnAreasDangerIsItsMonstersUsualCon()
        {
            var tiers = new (Vector3, sbyte)[]
            {
                (new Vector3(0, 0, 0), MonsterTiers.Orange), (new Vector3(400, 0, 0), MonsterTiers.Orange),
                (new Vector3(0, 400, 0), MonsterTiers.Yellow), (new Vector3(10000, 0, 0), MonsterTiers.Purple),
            };
            Assert.That(TreasureChests.Danger(Vector3.Zero, tiers), Is.EqualTo(MonsterTiers.Orange), "the far purple doesn't count");
            Assert.That(TreasureChests.Danger(new Vector3(30000, 0, 0), tiers), Is.EqualTo(MonsterTiers.Blue), "nobody near: an easy spot");
        }

        [Test]
        public void HarderAreasPayBetter()
        {
            sbyte[] cons = { MonsterTiers.Grey, MonsterTiers.Green, MonsterTiers.Blue, MonsterTiers.Yellow, MonsterTiers.Orange, MonsterTiers.Red, MonsterTiers.Purple };
            var b = cons.Select(TreasureChests.Bonus).ToList();
            Assert.That(b[0], Is.EqualTo(b[2]), "blue and below: as before");
            Assert.That(b[2].Coin, Is.EqualTo(1.0));
            for (int i = 3; i < b.Count; i++)
            {
                Assert.That(b[i].Coin, Is.GreaterThanOrEqualTo(b[i - 1].Coin));
                Assert.That(b[i].ExtraPct, Is.GreaterThanOrEqualTo(b[i - 1].ExtraPct));
                Assert.That(b[i].MinQuality, Is.GreaterThanOrEqualTo(b[i - 1].MinQuality).And.LessThanOrEqualTo(100));
            }
            Assert.That(b[5].ExtraPct, Is.GreaterThan(b[3].ExtraPct), "a red area: a real chance of a second piece");
        }
    }
}
