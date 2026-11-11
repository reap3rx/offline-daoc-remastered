#nullable enable
using System;
using System.Linq;
using DOL.GS;
using NUnit.Framework;
using OfflineDaoc.Population;

namespace DOL.UnitTests
{
    /// <summary>Camping supplies, treasure chests and the persona in play (owner 2026-11-11).</summary>
    public class UT_WorldFeatures
    {
        [Test]
        public void Camping_PricesRunEvenlyFromAGoldToTwoPlatinum()
        {
            var t = CampingSupplies.Tiers;
            Assert.That(t.Length, Is.EqualTo(7));
            Assert.That(t[0].Price, Is.EqualTo(10_000));
            Assert.That(t[^1].Price, Is.EqualTo(20_000_000));
            for (int i = 1; i < t.Length; i++)
                Assert.That(t[i].Price - t[i - 1].Price, Is.EqualTo(3_331_667).Within(10_000));
            Assert.That(t.Select(x => x.Color), Is.EqualTo(new[] { "grey", "green", "blue", "yellow", "orange", "red", "purple" }));
        }

        [Test]
        public void Camping_BuffsAreALittleUnderTheBaseline()
        {
            // the world's baseline buffs near level 47-50: a stat ~48, armour ~52-55
            Assert.That(CampingSupplies.StatFor(50), Is.InRange(40, 47));
            Assert.That(CampingSupplies.ArmorFor(50), Is.InRange(45, 54));
            Assert.That(CampingSupplies.StatFor(CampingSupplies.Tiers[0].Level), Is.LessThan(11));   // grey: under the lowest real buff (11)
            Assert.That(CampingSupplies.DamageAddFor(50), Is.LessThan(10.5));
            Assert.That(CampingSupplies.DamageShieldFor(50), Is.LessThan(4.9));
            Assert.That(CampingSupplies.RegenFor(7), Is.LessThan(5));
            for (int i = 1; i < CampingSupplies.Tiers.Length; i++)
                Assert.That(CampingSupplies.StatFor(CampingSupplies.Tiers[i].Level),
                    Is.GreaterThan(CampingSupplies.StatFor(CampingSupplies.Tiers[i - 1].Level)));
        }

        [Test]
        public void Camping_ItemIdsParse()
        {
            Assert.That(CampingSupplies.TryParse("camp_fire_3", out var tier, out bool pot), Is.True);
            Assert.That(tier!.Number, Is.EqualTo(3));
            Assert.That(pot, Is.False);
            Assert.That(CampingSupplies.TryParse("camp_pot_7", out tier, out pot), Is.True);
            Assert.That(pot, Is.True);
            Assert.That(CampingSupplies.TryParse("camp_fire_9", out _, out _), Is.False);
            Assert.That(CampingSupplies.TryParse("sword", out _, out _), Is.False);
        }

        [Test]
        public void Treasure_LevelFollowsTheZoneAndThePlayer()
        {
            // a level 50 in a level 5 zone: a level 7 chest, worth far less
            (int level, double scale) = TreasureChests.LevelFor(50, 5);
            Assert.That(level, Is.EqualTo(7));
            Assert.That(scale, Is.LessThan(0.3));
            // a level 10 in a level 40 zone: a little above its own level, a little richer
            (level, scale) = TreasureChests.LevelFor(10, 40);
            Assert.That(level, Is.InRange(12, 15));
            Assert.That(scale, Is.GreaterThan(1.0));
            // at level: its own
            (level, scale) = TreasureChests.LevelFor(30, 30);
            Assert.That(level, Is.EqualTo(31));
            Assert.That(scale, Is.EqualTo(1.0));
        }

        [Test]
        public void Treasure_ExperienceAveragesHalfABubble()
        {
            var rng = new Random(9);
            double sum = 0;
            for (int i = 0; i < 2000; i++)
                sum += TreasureChests.ExperienceFor(11_000, 1_000, 1.0, rng);
            Assert.That(sum / 2000, Is.EqualTo(500).Within(25));       // a bubble = 1000 here
        }

        [Test]
        public void Persona_WeighsWorkAndInvites()
        {
            var grouper = new BotPersona { Social = 90, Focus = 10, Drive = 50 };
            var soloer = new BotPersona { Social = 10, Focus = 90, Drive = 80, Skill = 70 };
            Assert.That(grouper.GroupAffinity(), Is.GreaterThan(grouper.SoloAffinity()));
            Assert.That(soloer.RvrAffinity(), Is.GreaterThan(grouper.RvrAffinity()));
            Assert.That(soloer.SoloConShift(), Is.EqualTo(1));
            Assert.That(new BotPersona { Drive = 10 }.SoloConShift(), Is.EqualTo(-1));
            Assert.That(grouper.InvitesPlayers(), Is.True);
            Assert.That(soloer.InvitesPlayers(), Is.False);
            Assert.That(grouper.EventJoinPercent(), Is.GreaterThan(soloer.EventJoinPercent()));
            var rng = new Random(4);
            int gYes = Enumerable.Range(0, 1000).Count(_ => grouper.AcceptsInvite(rng, 100, false));
            int sYes = Enumerable.Range(0, 1000).Count(_ => soloer.AcceptsInvite(rng, 100, false));
            int sAgain = Enumerable.Range(0, 1000).Count(_ => soloer.AcceptsInvite(rng, 100, true));
            Assert.That(gYes, Is.GreaterThan(900));
            Assert.That(sYes, Is.LessThan(250));
            Assert.That(sAgain, Is.GreaterThan(sYes));
        }

        [Test]
        public void Allocator_PersonaWeighsTheDrawButNotTheTotals()
        {
            var target = new AutonomousObjectiveAssignments.Allocation(50, 50, 0);
            var grouper = new BotPersona { Social = 95 };
            var soloer = new BotPersona { Social = 5 };
            var rng = new Random(2);
            int g = Enumerable.Range(0, 2000).Count(_ =>
                AutonomousObjectiveAssignments.ChoosePveObjective(target, 0, 0, rng, grouper) == eAutonomousObjectiveKind.GroupPve);
            int s = Enumerable.Range(0, 2000).Count(_ =>
                AutonomousObjectiveAssignments.ChoosePveObjective(target, 0, 0, rng, soloer) == eAutonomousObjectiveKind.GroupPve);
            Assert.That(g, Is.GreaterThan(1300));
            Assert.That(s, Is.LessThan(700));
            // a filled kind is never chosen however the persona leans
            Assert.That(Enumerable.Range(0, 200).All(_ =>
                AutonomousObjectiveAssignments.ChoosePveObjective(target, 0, 50, rng, grouper) == eAutonomousObjectiveKind.SoloPve), Is.True);
        }
    }
}
