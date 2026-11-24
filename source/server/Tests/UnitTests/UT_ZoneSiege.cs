using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using DOL.GS;
using DOL.GS.DynamicEvents;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Dergan Island (owner 2026-11-22, the Lough Derg plan's Phase 6): the resolve meter opens the assault, the
    /// island is held for a few real hours before the raids, each raid comes sooner and harder, and the last one, lost,
    /// brings it down and starts it all again. Its data: the chains it starts, what feeds it, its sites and its stock.</summary>
    [TestFixture]
    public sealed class UT_ZoneSiege
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef LoughDerg => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone200_lough_derg.json"));

        static SiegeDef Def => LoughDerg.Siege;

        [Test]
        public void ResolveOpensTheAssaultOnlyWhenFull()
        {
            var s = new SiegeState();
            Assert.That(s.AddResolve(60), Is.False);
            Assert.That(s.Phase, Is.EqualTo(SiegePhase.Building));
            Assert.That(s.AddResolve(50), Is.True, "the meter fills: the assault opens");
            Assert.That(s.Resolve, Is.EqualTo(100));
            Assert.That(s.Phase, Is.EqualTo(SiegePhase.Open));
            Assert.That(s.AddResolve(10), Is.False, "nothing more once open");
            Assert.That(s.OpenedUtc, Is.EqualTo(DateTime.UtcNow).Within(TimeSpan.FromMinutes(1)), "the bots' patience runs from here");
            Assert.That(Def.BotsGoAfterM, Is.InRange(15, Def.HoldH * 60 / 2), "longer than a raid's answering time, well inside the hold");
        }

        [Test]
        public void TheEnemysStrengthMakesTheAssaultHarderAndTheirWarBandsCommoner()
        {
            var s = new SiegeState();
            Assert.That(s.AssaultToughness, Is.EqualTo(1.0));
            Assert.That(s.WarInterval, Is.EqualTo(1.0));
            s.AddEnemy(250);
            Assert.That(s.Enemy, Is.EqualTo(100), "capped");
            Assert.That(s.AssaultToughness, Is.EqualTo(1.5));
            Assert.That(s.WarInterval, Is.EqualTo(0.5));
        }

        [Test]
        public void HeldTheRaidsComeAfterTheHoldThenSoonerAndHarder()
        {
            SiegeDef d = Def;
            var s = new SiegeState();
            s.AddResolve(100);
            var t0 = new DateTime(2026, 11, 22, 12, 0, 0, DateTimeKind.Utc);
            s.Captured(t0, d);
            Assert.That(s.Phase, Is.EqualTo(SiegePhase.Held));
            Assert.That(s.NextRaidUtc, Is.EqualTo(t0.AddHours(d.HoldH)));
            Assert.That(d.HoldH, Is.InRange(2.0, 6.0), "a few real hours (owner)");
            var seen = new List<string>();
            double tough = 0;
            DateTime now = s.NextRaidUtc;
            TimeSpan lastGap = TimeSpan.MaxValue;
            for (int i = 0; i < d.Raids.Count + 2; i++)
            {
                seen.Add(s.NextRaid(d));
                Assert.That(s.RaidToughness, Is.GreaterThan(tough), "each raid harder");
                tough = s.RaidToughness;
                s.RaidHeld(now, d);
                TimeSpan gap = s.NextRaidUtc - now;
                Assert.That(gap, Is.LessThanOrEqualTo(lastGap), "each comes sooner (or as soon)");
                lastGap = gap;
                now = s.NextRaidUtc;
            }
            Assert.That(seen.Take(d.Raids.Count), Is.EqualTo(d.Raids));
            Assert.That(seen.Skip(d.Raids.Count), Is.All.EqualTo(d.LastRaid), "then the warlord's return, again and again");
            s.Fell();
            Assert.That(s.Phase, Is.EqualTo(SiegePhase.Building));
            Assert.That(s.Resolve, Is.EqualTo(0));
            Assert.That(s.RaidIndex, Is.EqualTo(0));
        }

        [Test]
        public void ARepelledAssaultSetsTheResolveBack()
        {
            var s = new SiegeState();
            s.AddResolve(100);
            s.Phase = SiegePhase.Assault;
            s.Repelled();
            Assert.That(s.Phase, Is.EqualTo(SiegePhase.Building));
            Assert.That(s.Resolve, Is.LessThan(100).And.GreaterThan(0));
            Assert.That(s.Enemy, Is.GreaterThan(0));
        }

        [Test]
        public void StateSurvivesItsJson()
        {
            var s = new SiegeState { Resolve = 42, Enemy = 7, Phase = SiegePhase.Held, RaidIndex = 2, NextRaidUtc = new DateTime(2026, 11, 23, 1, 2, 3, DateTimeKind.Utc) };
            var back = JsonConvert.DeserializeObject<SiegeState>(JsonConvert.SerializeObject(s));
            Assert.That(back.Phase, Is.EqualTo(SiegePhase.Held));
            Assert.That(back.RaidIndex, Is.EqualTo(2));
            Assert.That(back.NextRaidUtc, Is.EqualTo(s.NextRaidUtc));
        }

        [Test]
        public void DerganIslandsChainsAreThereAndOnlyTheSiegeStartsThem()
        {
            ZoneEventsDef z = LoughDerg;
            SiegeDef d = z.Siege;
            Assert.That(d, Is.Not.Null);
            var chains = z.Chains.ToDictionary(c => c.Id);
            foreach (string id in d.Raids.Append(d.LastRaid).Append(d.Assault))
            {
                Assert.That(chains.ContainsKey(id), id);
                Assert.That(chains[id].Manual, Is.True, id + " is the siege's to start");
                Assert.That(chains[id].BotMinLevel, Is.GreaterThanOrEqualTo(12), id + ": no low bots on the elite island");
            }
            ChainDef a = chains[d.Assault];
            Assert.That(a.Giver, Is.Not.Null, "a giver at the staging camp");
            Assert.That(a.MinPeople, Is.EqualTo(8), "eight or more, bots counting (owner)");
            Assert.That(a.Bots, Is.GreaterThan(DynamicEventManager.BotsPerEvent), "room for a war band of bots");
            Assert.That(a.Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss", "defend" }), "landing, wards, warlord, hold");
            StageDef wards = a.Stages[1];
            Assert.That(wards.Wards, Has.Count.EqualTo(3), "three ward-stones");
            Assert.That(wards.WardNames, Has.Count.EqualTo(3));
            Assert.That(wards.Boss, Is.Not.Null, "each with its keeper");
            foreach (string id in d.Raids.Append(d.LastRaid))
                Assert.That(chains[id].AutoFailS, Is.GreaterThan(0), id + ": ignored, it's lost");
            Assert.That(chains[d.WarChain].Manual, Is.False);
        }

        [Test]
        public void WhatFeedsTheMeterIsReal()
        {
            ZoneEventsDef z = LoughDerg;
            SiegeDef d = z.Siege;
            var chains = z.Chains.Select(c => c.Id).ToHashSet();
            foreach (string id in d.Feeds.Keys.Concat(d.EnemyFeeds.Keys))
                Assert.That(chains, Does.Contain(id));
            var quests = JToken.Parse(Text("StoryQuests.hib_lough_derg.json"))["quests"].Select(q => (string) q["id"]).ToHashSet();
            foreach (string id in d.Quests.Keys)
                Assert.That(quests, Does.Contain(id));
            // a player's run through the Red Lake story and a few events opens it; events alone take a while
            Assert.That(d.Quests.Values.Sum() + d.Feeds.Values.Sum(), Is.GreaterThanOrEqualTo(100));
            Assert.That(d.Feeds.Values.Max(), Is.LessThan(50), "no one event opens it");
        }

        [Test]
        public void TheIslandsGarrisonSitesAreTheZoneBuilds()
        {
            var sites = JToken.Parse(Text("ZoneBuilds.zone200_lough_derg.json"))["sites"].Select(s => (string) s["id"]).ToHashSet();
            foreach (string id in Def.Sites)
                Assert.That(sites, Does.Contain(id));
        }

        [Test]
        public void EveryPlaceIsInTheZone()
        {
            SiegeDef d = Def;
            var places = new List<double[]> { d.Staging, d.Landing };
            places.AddRange(d.CampNpcs.Select(n => n.Pos));
            places.AddRange(d.Holdouts.Select(n => n.Pos));
            places.AddRange(d.CampNpcs.Where(n => n.Kind == "ferry").Select(n => n.To));
            foreach (double[] p in places)
            {
                Assert.That(p, Is.Not.Null);
                Assert.That(p[0], Is.InRange(0, 1638));
                Assert.That(p[1], Is.InRange(0, 1638));
            }
            Assert.That(d.CampNpcs.Count(n => n.Kind == "ferry"), Is.EqualTo(2), "a ferry each way");
        }

        [Test]
        public void TheIslandIsWhereTheFightAndTheCampAre_AndTheStagingCampIsAcrossTheWater()
        {
            ZoneEventsDef z = LoughDerg;
            SiegeDef d = z.Siege;
            Assert.That(d.Area, Has.Length.EqualTo(3));
            bool On(double[] p) => Math.Sqrt(Math.Pow(p[0] - d.Area[0], 2) + Math.Pow(p[1] - d.Area[1], 2)) <= d.Area[2];
            Assert.That(On(d.Staging), Is.False, "bots gather on the shore, then the roane carry them over");
            Assert.That(On(d.Landing), Is.True);
            foreach (SiegeNpcDef n in d.CampNpcs.Concat(d.Holdouts))
                Assert.That(On(n.Pos), Is.EqualTo(!(n.Kind == "ferry" && On(n.To))), n.Name);
            ChainDef a = z.Chains.First(c => c.Id == d.Assault);
            foreach (StageDef s in a.Stages)
            {
                if (s.Center != null)
                    Assert.That(On(s.Center), s.Name);
                foreach (double[] w in s.Wards)
                    Assert.That(On(w), s.Name);
            }
        }

        [Test]
        public void TheCampsStockExistsAtEveryLevel()
        {
            var ids = JToken.Parse(Text("StoryItems.isl200_dergan_island.json")).ToDictionary(r => (string) r["Id_nb"]);
            foreach (SiegeNpcDef n in Def.CampNpcs.Where(n => n.Kind is "marks" or "coin"))
            {
                Assert.That(n.Stock, Is.Not.Empty, n.Name);
                foreach (SiegeStockDef s in n.Stock.Where(s => !s.Item.StartsWith("tw_")))
                {
                    Assert.That(ids.ContainsKey(s.Item), s.Item);
                    if (n.Kind == "marks")
                    {
                        Assert.That(s.Price, Is.GreaterThan(0), s.Item);
                        for (int l = 10; l <= 50; l += 5)
                            Assert.That(ids.ContainsKey($"{s.Item}_l{l}"), $"{s.Item}_l{l}");
                    }
                }
            }
            // the cloak's emblem: within what a classic emblem number carries (logo up to 127 in 16 bits)
            int emblem = (int) ids["isl200_cloak_of_the_taken_isle"]["Emblem"];
            Assert.That(emblem, Is.GreaterThan(0).And.LessThan(65536));
            Assert.That(emblem >> 9, Is.EqualTo(104));
            Assert.That(ids.Values.Where(r => ((string) r["Id_nb"]).StartsWith("isl200_cloak_of_the_taken_isle")).All(r => (int) r["Emblem"] == emblem));
        }
    }
}
