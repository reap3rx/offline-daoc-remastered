using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using DOL.GS;
using DOL.GS.Reputation;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Reputation (owner 2026-11-22): two factions a zone, five ranks, titles at Trusted / Honoured / Legend,
    /// realm reputation from every faction (each up to its Legend mark) and RvR, bots seeded with standing.</summary>
    [TestFixture]
    public sealed class UT_Reputation
    {
        static Assembly Asm => typeof(RepDefs).Assembly;

        static JToken Resource(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return JToken.Parse(r.ReadToEnd());
        }

        static RepZoneDef LoughDerg => RepDefs.ForZone(200);

        [TestCase(0, Rank.Unknown)] [TestCase(499, Rank.Unknown)] [TestCase(500, Rank.Familiar)] [TestCase(1500, Rank.Trusted)]
        [TestCase(3999, Rank.Trusted)] [TestCase(4000, Rank.Honoured)] [TestCase(10000, Rank.Legend)] [TestCase(99999, Rank.Legend)]
        public void RanksByPoints(double pts, Rank expected) => Assert.That(ReputationService.RankOf(pts), Is.EqualTo(expected));

        [Test]
        public void RealmRanksTakeFarMore()
        {
            Assert.That(ReputationService.RealmRankOf(10000), Is.EqualTo(Rank.Familiar));
            Assert.That(ReputationService.RealmRankOf(20000), Is.EqualTo(Rank.Trusted));
            Assert.That(ReputationService.RealmRankOf(119999), Is.EqualTo(Rank.Honoured));
            Assert.That(ReputationService.RealmRankOf(120000), Is.EqualTo(Rank.Legend));
        }

        [Test]
        public void LoughDergHasItsTwoFactionsWithTheirTitlesAndQuartermasters()
        {
            RepZoneDef z = LoughDerg;
            Assert.That(z, Is.Not.Null);
            Assert.That(z.Realm, Is.EqualTo(3));
            Assert.That(z.Factions.Select(f => f.Key), Is.EquivalentTo(new[] { "mag_mell_guard", "lucht_feasa" }));
            RepFactionDef guard = z.Faction("mag_mell_guard"), feasa = z.Faction("lucht_feasa");
            Assert.That(guard.Title(Rank.Trusted, false), Is.EqualTo("Shieldfriend of Mag Mell"));
            Assert.That(guard.Title(Rank.Honoured, true), Is.EqualTo("Sword of Mag Mell"));
            Assert.That(guard.Title(Rank.Legend, false), Is.EqualTo("Breaker of the Red Hand"));
            Assert.That(feasa.Name, Is.EqualTo("the Lucht Feasa of Loch Dearg"));
            Assert.That(feasa.Title(Rank.Trusted, false), Is.EqualTo("Friend of the Wise"));
            Assert.That(feasa.Title(Rank.Honoured, false), Is.EqualTo("Friend of the Good People"));
            Assert.That(feasa.Title(Rank.Legend, true), Is.EqualTo("Bean Feasa"));
            Assert.That(feasa.Title(Rank.Legend, false), Is.EqualTo("Fear Feasa"));
            Assert.That(feasa.Title(Rank.Familiar, false), Is.Null, "no title below Trusted");
            Assert.That(z.Faction(z.KillDefault), Is.Not.Null);
            Assert.That(z.Faction(z.EventDefault), Is.Not.Null);
            Assert.That(z.Faction(z.QuestDefault), Is.Not.Null);
            foreach (RepFactionDef f in z.Factions)
            {
                Assert.That(f.Quartermaster, Is.Not.Null, f.Key);
                Assert.That(f.Quartermaster.Stock.Select(s => s.Rank).Distinct(), Is.EquivalentTo(new[] { Rank.Trusted, Rank.Honoured, Rank.Legend }), f.Key);
            }
            Assert.That(RepDefs.Realm(eRealm.Hibernia).Titles, Is.EqualTo(new[] { "Defender of Hibernia", "Hero of Hibernia", "Legend of Hibernia" }));
        }

        [Test]
        public void TheQuartermastersItemsExistAtEveryLevel()
        {
            var ids = new HashSet<string>(Resource("StoryItems.rep200_lough_derg.json").Select(r => (string) r["Id_nb"]));
            foreach (RepStockDef s in LoughDerg.Factions.SelectMany(f => f.Quartermaster.Stock))
            {
                Assert.That(ids, Does.Contain(s.Item), s.Item);
                for (int l = 10; l <= 50; l += 5)
                    Assert.That(ids, Does.Contain($"{s.Item}_l{l}"), $"{s.Item}_l{l}");
                Assert.That(s.Price, Is.GreaterThan(0));
            }
        }

        [Test]
        public void EveryLoughDergStoryQuestAndEventCountsForAFaction()
        {
            RepZoneDef z = LoughDerg;
            foreach (JToken q in Resource("StoryQuests.hib_lough_derg.json")["quests"])
            {
                string id = (string) q["id"];
                Assert.That(z.Quests.ContainsKey(id), id);
                Assert.That(z.Faction(z.Quests[id]), Is.Not.Null, id);
            }
            foreach (JToken c in Resource("DynamicEvents.zone200_lough_derg.json")["chains"])
            {
                string id = (string) c["id"];
                Assert.That(z.Events.ContainsKey(id), id);
            }
            Assert.That(z.Quests.Values.All(k => z.Faction(k) != null));
            Assert.That(z.Events.Values.All(k => z.Faction(k) != null));
        }

        [Test]
        public void StoryChoicesCanPickASide()
        {
            Assert.That(ReputationService.QuestFaction("the_ladys_bargain", "took").Faction.Key, Is.EqualTo("mag_mell_guard"));
            Assert.That(ReputationService.QuestFaction("the_ladys_bargain", "asked").Faction.Key, Is.EqualTo("lucht_feasa"));
            Assert.That(ReputationService.QuestFaction("lesser_of_two_evils", "siabra").Faction.Key, Is.EqualTo("lucht_feasa"));
            Assert.That(ReputationService.QuestFaction("lesser_of_two_evils", "reeve").Faction.Key, Is.EqualTo("mag_mell_guard"));
            Assert.That(ReputationService.QuestFaction("changeling", "both").Faction.Key, Is.EqualTo("lucht_feasa"));
            Assert.That(ReputationService.QuestFaction("mandras_boy", "home").Faction.Key, Is.EqualTo("mag_mell_guard"));
            Assert.That(ReputationService.QuestFaction("no_such_quest", null).Faction, Is.Null);
        }

        [TestCase("villainous youth thug", "mag_mell_guard")] [TestCase("dergan lieutenant", "mag_mell_guard")]
        [TestCase("red wolfhound alpha", "mag_mell_guard")] [TestCase("moss sheerie", "lucht_feasa")]
        [TestCase("druid elder", "lucht_feasa")] [TestCase("siabra high enchanter", "lucht_feasa")]
        [TestCase("Ceo Dubh", "lucht_feasa")] [TestCase("something unheard of", "mag_mell_guard")]
        public void KillsCountForTheFactionWhoseFoeItIs(string name, string faction) =>
            Assert.That(ReputationService.KillFaction(LoughDerg, name).Key, Is.EqualTo(faction));

        [Test]
        public void OnlyYellowAndUpKillsPay_AndNeverEnoughToBeatQuestsAndEvents()
        {
            Assert.That(ReputationService.KillPoints(MonsterTiers.Grey), Is.EqualTo(0));
            Assert.That(ReputationService.KillPoints(MonsterTiers.Green), Is.EqualTo(0));
            Assert.That(ReputationService.KillPoints(MonsterTiers.Blue), Is.EqualTo(0));
            Assert.That(ReputationService.KillPoints(MonsterTiers.Yellow), Is.GreaterThan(0));
            Assert.That(ReputationService.KillPoints(MonsterTiers.Purple), Is.GreaterThan(ReputationService.KillPoints(MonsterTiers.Red)));
            // a yellow takes about a minute; a quest about fifteen, an event's stage about three
            Assert.That(ReputationService.KillYellow * 15, Is.LessThan(ReputationService.QuestPoints / 4));
            Assert.That(ReputationService.KillYellow * 3, Is.LessThan(ReputationService.EventGold / 3));
        }

        [Test]
        public void ASidesStoriesReachAboutTrusted_AndLegendTakesMore()
        {
            RepZoneDef z = LoughDerg;
            var group = Resource("StoryQuests.hib_lough_derg.json")["quests"].ToDictionary(q => (string) q["id"], q => (bool?) q["group"] ?? false);
            foreach (RepFactionDef f in z.Factions)
            {
                double pts = z.Quests.Where(kv => !kv.Key.Contains(':') && kv.Value == f.Key)
                    .Sum(kv => group[kv.Key] ? ReputationService.GroupQuestPoints : ReputationService.QuestPoints) * 0.8;   // Lough Derg is Peaceful
                Assert.That(ReputationService.RankOf(pts), Is.GreaterThanOrEqualTo(Rank.Trusted), f.Key);
                Assert.That(ReputationService.RankOf(pts), Is.LessThan(Rank.Legend), f.Key);
            }
        }

        [Test]
        public void RealmReputationCountsEachFactionOnlyUpToLegend()
        {
            var s = new ReputationService.Standing();
            s.Points["mag_mell_guard"] = 25000;
            s.Points["lucht_feasa"] = 3000;
            s.Rvr = 500;
            Assert.That(ReputationService.RealmPoints(s, eRealm.Hibernia), Is.EqualTo(10000 + 3000 + 500));
            Assert.That(ReputationService.RealmPoints(s, eRealm.Albion), Is.EqualTo(500), "another realm's zones don't count");
        }

        [Test]
        public void BotsArriveWithStandingByHowFarTheyHaveOutgrownAZone()
        {
            var low = new ReputationService.Standing();
            ReputationService.SeedInto(low, eRealm.Hibernia, 3, 42);
            Assert.That(low.Points.Values.Sum(), Is.EqualTo(0), "a new bot is Unknown");
            var mid = new ReputationService.Standing();
            ReputationService.SeedInto(mid, eRealm.Hibernia, 20, 42);
            var vet = new ReputationService.Standing();
            ReputationService.SeedInto(vet, eRealm.Hibernia, 35, 42);
            foreach (string k in new[] { "mag_mell_guard", "lucht_feasa" })
            {
                Assert.That(mid.Get(k), Is.GreaterThan(0));
                Assert.That(vet.Get(k), Is.GreaterThan(mid.Get(k) * 0.5));
                Assert.That(ReputationService.RankOf(vet.Get(k)), Is.LessThan(Rank.Legend), "Legend is rare, and never below 40");
            }
            var again = new ReputationService.Standing();
            ReputationService.SeedInto(again, eRealm.Hibernia, 35, 42);
            Assert.That(again.Points, Is.EquivalentTo(vet.Points), "the same bot always gets the same");
            int legends = 0;
            for (long id = 1; id <= 2000; id++)
            {
                var s = new ReputationService.Standing();
                ReputationService.SeedInto(s, eRealm.Hibernia, 50, id);
                legends += s.Points.Values.Count(v => v >= ReputationService.Thresholds[(int) Rank.Legend]);
            }
            int factions = RepDefs.Zones.Where(z => z.Realm == 3).Sum(z => z.Factions.Count);
            Assert.That(legends, Is.InRange(20 * factions, 110 * factions), "about 3% of level 40-50 veterans are a Legend with a faction");
        }

        [Test]
        public void StandingSurvivesItsJson()
        {
            var s = new ReputationService.Standing { Rvr = 12, Lock = "Sword of Mag Mell", Seeded = true };
            s.Points["lucht_feasa"] = 777;
            var back = Newtonsoft.Json.JsonConvert.DeserializeObject<ReputationService.Standing>(Newtonsoft.Json.JsonConvert.SerializeObject(s));
            Assert.That(back.Get("lucht_feasa"), Is.EqualTo(777));
            Assert.That(back.Rvr, Is.EqualTo(12));
            Assert.That(back.Lock, Is.EqualTo("Sword of Mag Mell"));
            Assert.That(back.Seeded, Is.True);
        }

        [Test]
        public void KinFactionsSpeedEachOtherUp()
        {
            // owner 2026-11-22: Honoured with a kin faction earns the other 50% faster, Legend twice as fast
            var fianna = new RepFactionDef { Key = "f", Kin = new List<string> { "guard" } };
            var pts = new Dictionary<string, double>();
            double K() => ReputationService.KinFactor(k => pts.GetValueOrDefault(k), fianna);
            Assert.That(K(), Is.EqualTo(1.0));
            pts["guard"] = ReputationService.Thresholds[(int) Rank.Trusted];
            Assert.That(K(), Is.EqualTo(1.0), "Trusted isn't enough");
            pts["guard"] = ReputationService.Thresholds[(int) Rank.Honoured];
            Assert.That(K(), Is.EqualTo(1.5));
            pts["guard"] = ReputationService.Thresholds[(int) Rank.Legend];
            Assert.That(K(), Is.EqualTo(2.0));
            Assert.That(ReputationService.KinFactor(k => 99999, new RepFactionDef { Key = "x" }), Is.EqualTo(1.0), "no kin, no change");
        }

        [Test]
        public void ASharedFactionIsOneFactionInTwoZones()
        {
            var home = new RepZoneDef { Zone = 207, Name = "Connacht" };
            var rowan = new RepFactionDef { Key = "rowan", ZoneDef = home };
            home.Factions.Add(rowan);
            var away = new RepZoneDef { Zone = 201, Name = "Silvermine", Shared = new List<string> { "rowan" } };
            away.Factions.Add(new RepFactionDef { Key = "wardens", ZoneDef = away });
            RepDefs.Share(new List<RepZoneDef> { home, away });
            Assert.That(away.Faction("rowan"), Is.SameAs(rowan), "the same standing in both");
            Assert.That(rowan.ZoneDef, Is.SameAs(home), "its home zone stays its own");
            RepDefs.Share(new List<RepZoneDef> { home, away });
            Assert.That(away.Factions.Count(f => f.Key == "rowan"), Is.EqualTo(1), "added once");
        }

        [Test]
        public void RealmReputationCountsASharedFactionOnce()
        {
            // every loaded faction once, however many zones list it
            Assert.That(RepDefs.AllFactions.Select(f => f.Key), Is.Unique);
        }
    }
}
