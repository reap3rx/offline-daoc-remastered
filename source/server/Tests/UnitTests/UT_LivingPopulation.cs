#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NUnit.Framework;
using OfflineDaoc.Population;

namespace DOL.UnitTests
{
    /// <summary>The living population's model (owner 2026-11-10, "Living Bot Population - Plan"): the doubled online
    /// curve, band quotas, the picker, sessions, personas and the lore names.</summary>
    public class UT_LivingPopulation
    {
        [Test]
        public void Curve_IsDoubledAndPeaksInPrimeTime()
        {
            var day = new DateTime(2026, 11, 10);
            double prime = PopulationCurve.Share(day.AddHours(21), drift: false);
            double night = PopulationCurve.Share(day.AddHours(5), drift: false);
            double afternoon = PopulationCurve.Share(day.AddHours(13), drift: false);
            Assert.That(prime, Is.EqualTo(0.24).Within(0.001));
            Assert.That(night, Is.EqualTo(0.06).Within(0.001));
            Assert.That(afternoon, Is.EqualTo(0.12).Within(0.001));
            for (int m = 0; m < 24 * 60; m += 7)
            {
                double s = PopulationCurve.Share(day.AddMinutes(m));
                Assert.That(s, Is.InRange(0.05, 0.27), $"minute {m}");
            }
        }

        [Test]
        public void Target_RespectsTheCeiling()
        {
            var knobs = new PopulationKnobs();
            DateTime prime = new DateTime(2026, 11, 10, 21, 0, 0);
            Assert.That(PopulationCurve.Target(2000, prime, knobs), Is.LessThanOrEqualTo(250));
            Assert.That(PopulationCurve.Target(2000, prime, knobs with { MaxOnlinePerRealm = 100 }), Is.EqualTo(100));
            Assert.That(PopulationCurve.Target(0, prime, knobs), Is.EqualTo(0));
        }

        [Test]
        public void Knobs_ParseAndClamp()
        {
            var values = new Dictionary<string, string>
            {
                [PopulationKnobs.KeyMaxOnline] = "99999", [PopulationKnobs.KeyPersonaMix] = "40/40/20",
                [PopulationKnobs.KeyChatLevel] = "Lively", [PopulationKnobs.KeyFastClock] = "true",
                [PopulationKnobs.KeyCurveScale] = "junk",
            };
            PopulationKnobs k = PopulationKnobs.FromProperties(key => values.GetValueOrDefault(key));
            Assert.That(k.MaxOnlinePerRealm, Is.EqualTo(5000));
            Assert.That(k.CasualPct, Is.EqualTo(40));
            Assert.That(k.TryhardPct, Is.EqualTo(20));
            Assert.That(k.ChatLevel, Is.EqualTo("lively"));
            Assert.That(k.FastClock, Is.True);
            Assert.That(k.ClockRate, Is.EqualTo(24));
            Assert.That(k.CurveScale, Is.EqualTo(1.0));
        }

        [Test]
        public void Persona_RoundTripsAndRollsTheMix()
        {
            var rng = new Random(7);
            var tiers = new Dictionary<string, int>();
            for (int i = 0; i < 4000; i++)
            {
                BotPersona p = BotPersona.Roll(rng, 6);
                BotPersona back = BotPersona.Parse(p.ToJson());
                Assert.That(back, Is.Not.Null);
                Assert.That(back!.ToJson(), Is.EqualTo(p.ToJson()));
                tiers[p.Tier] = tiers.GetValueOrDefault(p.Tier) + 1;
            }
            Assert.That(tiers[BotPersona.Casual] / 4000.0, Is.InRange(0.18, 0.32));
            Assert.That(tiers[BotPersona.Tryhard] / 4000.0, Is.InRange(0.13, 0.27));
            Assert.That(BotPersona.Parse(""), Is.Null);
            Assert.That(BotPersona.Parse("{broken"), Is.Null);
        }

        [Test]
        public void Quotas_CapEachBand()
        {
            int[] q = PopulationPicker.BandQuotas(100, [900, 50, 30, 10, 5, 5]);
            Assert.That(q.Max(), Is.LessThanOrEqualTo(40));
            Assert.That(q[5], Is.GreaterThanOrEqualTo(2));
            int[] fresh = PopulationPicker.BandQuotas(100, new int[6]);
            Assert.That(fresh[0], Is.GreaterThan(0));
        }

        [Test]
        public void Picker_HoldsNewcomersToTheArrivalRoom()
        {
            var rng = new Random(3);
            var offline = Enumerable.Range(1, 200).Select(i => new PopulationPicker.Candidate(i, 1, 2,
                BotPersona.Roll(rng, 2), 1e6, false, false)).ToList();
            var online = new PopulationPicker.Online();
            for (int i = 0; i < 30; i++)
                online.Add(1, 2, newcomer: true);
            int full = PopulationPicker.ArrivalRoom(online, 30, 2000, 100);
            Assert.That(full, Is.EqualTo(0));
            Assert.That(PopulationPicker.Pick(offline, online, 100, new int[6], DateTime.Now, full, rng), Is.Null);
            Assert.That(PopulationPicker.ArrivalRoom(online, 40, 105, 100), Is.EqualTo(5), "the arrival pace caps the room too");
            Assert.That(PopulationPicker.Pick(offline, online, 100, new int[6], DateTime.Now, 5, rng), Is.Not.Null);
            Assert.That(PopulationArrivals.Allowed(2000, 0), Is.EqualTo(120));
            Assert.That(PopulationArrivals.Allowed(2000, 30), Is.EqualTo(2000));
        }

        [Test]
        public void Sessions_StayInTheirRange()
        {
            var rng = new Random(11);
            for (int i = 0; i < 2000; i++)
            {
                BotPersona p = BotPersona.Roll(rng, 2);
                double m = PopulationPicker.SessionMinutes(p, 1.0, rng);
                Assert.That(m, Is.InRange(10, p.SessionMinutes.Max * 1.7 + 0.001));
            }
        }

        /// <summary>A month of one realm, minute by minute, on the model alone: online tracks the curve, the newcomers
        /// arrive over weeks, and no band floods.</summary>
        [Test]
        public void SimulatedMonth_TracksTheCurveAndArrivesInWaves()
        {
            var rng = new Random(42);
            var knobs = new PopulationKnobs();
            const int roster = 2000;
            var bots = Enumerable.Range(1, roster).Select(i => new SimBot
            {
                Id = i, Class = 1 + rng.Next(15), Persona = BotPersona.Roll(rng, 1 + rng.Next(15)),
            }).ToList();
            DateTime start = new DateTime(2026, 11, 1, 0, 0, 0);
            var weekArrived = new List<int>();
            double sqErr = 0;
            int samples = 0;
            for (int minute = 0; minute < 28 * 24 * 60; minute++)
            {
                DateTime now = start.AddMinutes(minute);
                foreach (SimBot b in bots.Where(b => b.Online && b.EndsAt <= now))
                {
                    b.Online = false;
                    b.LastOut = now;
                }
                if (minute % 30 == 0)                          // a levelling stand-in: online bots gain a level each 2-4 hours
                    foreach (SimBot b in bots.Where(b => b.Online && b.Level < 50 && rng.Next(6) == 0))
                        b.Level++;
                double days = minute / (24.0 * 60);
                int arrived = bots.Count(b => b.Arrived);
                int target = PopulationCurve.Target(PopulationArrivals.Known(roster, arrived, days), now, knobs);
                var online = new PopulationPicker.Online();
                var arrivedByBand = new int[PopulationCurve.Bands];
                foreach (SimBot b in bots)
                {
                    if (b.Online)
                        online.Add(b.Level, b.Class, b.Sessions == 1);
                    if (b.Arrived)
                        arrivedByBand[PopulationCurve.Band(b.Level)]++;
                }
                int room = PopulationPicker.ArrivalRoom(online, knobs.NewArrivals, PopulationArrivals.Allowed(roster, days), arrived);
                for (int n = 0; n < 4 && online.Total < target; n++)
                {
                    var offline = bots.Where(b => !b.Online).Select(b => new PopulationPicker.Candidate(b.Id, b.Level, b.Class,
                        b.Persona, b.LastOut == default ? 1e6 : (now - b.LastOut).TotalMinutes, b.Arrived, false)).ToList();
                    PopulationPicker.Candidate? c = PopulationPicker.Pick(offline, online, target, arrivedByBand, now,
                        room, rng);
                    if (c == null)
                        break;
                    SimBot bot = bots[(int)c.Value.BotId - 1];
                    if (!bot.Arrived)
                        room--;
                    bot.Sessions++;
                    bot.Online = true;
                    bot.Arrived = true;
                    bot.EndsAt = now.AddMinutes(PopulationPicker.SessionMinutes(bot.Persona, 1.0, rng));
                    online.Add(bot.Level, bot.Class, bot.Sessions == 1);
                }
                if (minute > 2 * 24 * 60 && minute % 15 == 0)
                {
                    sqErr += Math.Pow(online.Total - target, 2);
                    samples++;
                }
                if (minute % (7 * 24 * 60) == 7 * 24 * 60 - 1)
                    weekArrived.Add(bots.Count(b => b.Arrived));
            }
            double rms = Math.Sqrt(sqErr / samples);
            TestContext.WriteLine($"rms {rms:0.0}; arrived by week: {string.Join(", ", weekArrived)}");
            Assert.That(rms, Is.LessThan(40), "online should track the curve's target");
            Assert.That(weekArrived[0], Is.InRange(roster * 0.2, roster * 0.45), "a week in: about a third have arrived");
            Assert.That(weekArrived[2], Is.InRange(roster * 0.75, roster * 1.0));
            Assert.That(weekArrived[3], Is.GreaterThanOrEqualTo(roster * 0.97), "everyone has arrived by week four");
        }

        private sealed class SimBot
        {
            public int Id, Class, Level = 1, Sessions;
            public BotPersona Persona = null!;
            public bool Online, Arrived;
            public DateTime EndsAt, LastOut;
        }

        [Test]
        public void LoreNames_FillABigRosterCleanly()
        {
            string file = FindNames();
            BotLoreNames names = BotLoreNames.Load(file);
            names.Reserve(["Arthur", "Claudin"]);
            var rng = new Random(5);
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var skeletons = new HashSet<string>();
            int made = 0;
            foreach (int race in BotLoreNames.RaceNames.Keys)
                for (int gender = 1; gender <= 2; gender++)
                    for (int i = 0; i < 130; i++)
                    {
                        string? n = names.Generate(race, gender, rng);
                        Assert.That(n, Is.Not.Null, $"race {race} gender {gender} ran out at {i}");
                        Assert.That(names.Screen(n!), Is.Null, n);
                        Assert.That(seen.Add(n!), Is.True, n);
                        Assert.That(skeletons.Add(BotLoreNames.Skeleton(n!)), Is.True, n);
                        made++;
                    }
            Assert.That(made, Is.EqualTo(15 * 2 * 130));
            Assert.That(names.Screen("Merlin"), Is.Not.Null);
        }

        private static string FindNames()
        {
            for (DirectoryInfo? d = new DirectoryInfo(TestContext.CurrentContext.TestDirectory); d != null; d = d.Parent)
            {
                string p = Path.Combine(d.FullName, "server", "GameServer", "bots", "autonomous", "data", "bot_names.json");
                if (File.Exists(p))
                    return p;
                p = Path.Combine(d.FullName, "source", "server", "GameServer", "bots", "autonomous", "data", "bot_names.json");
                if (File.Exists(p))
                    return p;
            }
            Assert.Fail("bot_names.json not found");
            return "";
        }
    }
}
