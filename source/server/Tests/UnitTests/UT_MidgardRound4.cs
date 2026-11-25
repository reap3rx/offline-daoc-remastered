using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using DOL.GS;
using DOL.GS.DynamicEvents;
using DOL.GS.Reputation;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Midgard's PvE rework, round 4 ("Midgard - the plan", 2026-11-25): Raumarik (Elite; Hati's seat - the King's March
    /// and Hati's raid at his howe) and Malmohus (Elite; Gjalpinulva's seat - the Dragon-Oath, the Hierophant's raid at the
    /// Wyrm-Temple, and the dragon sealed until it's won).</summary>
    [TestFixture]
    public sealed class UT_MidgardRound4
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events(string f) => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents." + f + ".json"));
        static JToken Build(string f) => JToken.Parse(Text("ZoneBuilds." + f + ".json"));
        static JToken Stories(string f) => JToken.Parse(Text("StoryQuests." + f + ".json"));
        static HashSet<string> Items(string file) => JToken.Parse(Text("StoryItems." + file + ".json")).Select(r => (string) r["Id_nb"]).ToHashSet();

        static readonly (AlbionCampaign C, string Build, string Story, string Events, string Spec)[] Zones =
        {
            (MidgardCampaigns.Winter, "zone108_raumarik", "mid_raumarik", "zone108_raumarik", "rk108_raumarik"),
            (MidgardCampaigns.Wyrm, "zone116_malmohus", "mid_malmohus", "zone116_malmohus", "mh116_malmohus"),
        };

        static Dictionary<string, int> Tiers(JToken b)
        {
            var members = (JObject) b["members"];
            var count = new Dictionary<string, int>();
            void Add(string member, int n)
            {
                JToken m = members[member];
                Assert.That(m, Is.Not.Null, member);
                count[(string) m["tier"]] = count.GetValueOrDefault((string) m["tier"]) + n;
                foreach (JProperty g in (m["guards"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(g.Name, n * (int) g.Value);
            }
            foreach (JToken s in b["sites"])
                foreach (JProperty sp in (s["spawn"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(sp.Name, (int) sp.Value);
            return count;
        }

        [Test]
        public void BothAreElite_NothingBelowOrange()
        {
            foreach (var z in Zones)
            {
                JToken b = Build(z.Build);
                Assert.That((string) b["rating"], Is.EqualTo("elite"), z.Build);
                var t = Tiers(b);
                Assert.That(t.Values.Sum(), Is.InRange(250, 700), z.Build);
                Assert.That(t.Keys, Is.SubsetOf(new[] { "orange", "red", "purple" }), z.Build + ": nothing below orange");
                Assert.That(t.GetValueOrDefault("purple"), Is.GreaterThanOrEqualTo(2), z.Build + ": named purples");
            }
        }

        [Test]
        public void TheCampaigns_AreMidgards_PostsSweepsAndPockets()
        {
            foreach (var z in Zones)
            {
                AlbionCampaign c = z.C;
                Assert.That(AlbionCampaign.All, Does.Contain(c));
                Assert.That(c.Side, Is.EqualTo(eRealm.Midgard));
                Assert.That(c.Region, Is.EqualTo(100));
                Assert.That(RepDefs.ForZone(c.Zone).Faction(c.HostFaction), Is.Not.Null, c.Key + ": the host is the zone's faction");
                var ids = Build(z.Build)["sites"].Select(s => (string) s["id"]).ToHashSet();
                foreach (string[] held in c.HeldSites.Skip(1))
                    Assert.That(ids, Is.SupersetOf(held), c.Key + ": the sites each post sweeps");
                Assert.That(ids.Count(i => i.StartsWith(AlbionCampaign.PocketPrefix)), Is.InRange(1, 8), c.Key + ": pockets stay after the win");
                Assert.That(c.Posts.Skip(1).All(p => p.Length == 3 && p[2] > 0), c.Key + ": every post has its height");

                var chains = Events(z.Events).Chains;
                var cids = chains.Select(x => x.Id).ToHashSet();
                for (int n = 0; n <= AlbionCampaign.Checkpoints; n++)
                    Assert.That(cids, Does.Contain(c.NextAssault(n)));
                for (int n = 1; n <= AlbionCampaign.Checkpoints; n++)
                {
                    Assert.That(cids, Does.Contain(c.CounterFor(n)));
                    ChainDef a = chains.First(x => x.Id == c.NextAssault(n - 1));
                    Assert.That(a.Manual, Is.True);
                    Assert.That(a.Giver, Is.Not.Null, a.Id + ": a captain gives it");
                    Assert.That(chains.First(x => x.Id == c.CounterFor(n)).Stages.Single().Type, Is.EqualTo("defend"));
                }
                ChainDef raid = chains.First(x => x.Id == c.RaidChain);
                Assert.That(raid.MinPeople, Is.GreaterThanOrEqualTo(8), "a raid");
                Assert.That(raid.Stages.Single().Type, Is.EqualTo("boss"));

                HashSet<string> items = Items(z.Spec);
                foreach (SiegeStockDef st in c.Camp().SelectMany(n => n.Stock ?? new List<SiegeStockDef>()))
                    Assert.That(items, Does.Contain(st.Item), st.Item);
                foreach (ItemRewardDef i in raid.Stages.SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                    Assert.That(items.Any(x => x.StartsWith(i.Id)), i.Id);
            }
            Assert.That(Events("zone108_raumarik").Chains.Single(c => c.Id == MidgardRaids.HatiChain).Stages[0].Boss.Name, Does.Contain("Hati"));
            Assert.That(Events("zone116_malmohus").Chains.Single(c => c.Id == MidgardRaids.HierophantChain).Stages[0].Boss.Name, Does.Contain("Hierophant"));
        }

        [Test]
        public void TheCampaigns_Rules_AndAlbionsStayAlbions()
        {
            DateTime t = new(2026, 11, 25, 20, 0, 0, DateTimeKind.Utc);
            AlbionCampaign winter = MidgardCampaigns.Winter, wyrm = MidgardCampaigns.Wyrm;
            var s = new AlbionCampaign.State();
            Assert.That(winter.CanStart(44, s, t), Is.Not.Null, "45 and up for Raumarik");
            Assert.That(winter.CanStart(45, s, t), Is.Null);
            Assert.That(wyrm.CanStart(49, s, t), Is.Not.Null, "50 and up for Malmohus");
            Assert.That(wyrm.CanStart(50, s, t), Is.Null);
            Assert.That(winter.NextAssault(0), Is.EqualTo("rk_cp1_assault"));
            Assert.That(wyrm.NextAssault(4), Is.EqualTo("mh_wyrm_temple"));
            Assert.That(winter.AssaultIndex("mh_cp3_assault"), Is.EqualTo(0), "each campaign hears only its own");
            Assert.That(wyrm.CounterIndex("mh_cp2_counter"), Is.EqualTo(2));
            Assert.That(winter.Line(s, t), Does.Contain("Raumarik"));
            Assert.That(wyrm.Line(s, t), Is.EqualTo("The drakulv hold Malmohus"));
            Assert.That(winter.Line(s, t), Is.EqualTo("Hati's host holds Raumarik"));
            Assert.That(AlbionCampaign.Lake.Side, Is.EqualTo(eRealm.Albion));
            Assert.That(AlbionCampaign.Lake.Region, Is.EqualTo(1));
            Assert.That(AlbionCampaign.Lake.Line(s, t), Is.EqualTo("Morgana's host holds Llyn Barfog"), "Albion's words as they were");
            Assert.That(AlbionCampaign.Moor.Line(s, t), Is.EqualTo("The giants hold Dartmoor"));
            Assert.That(AlbionCampaign.Moor.RaidPlace, Is.EqualTo("the Giants' Throne"));
            Assert.That(AlbionCampaign.All.Select(c => c.Key).Distinct().Count(), Is.EqualTo(AlbionCampaign.All.Length));
            Assert.That(AlbionCampaign.All.Select(c => c.StateFile).Distinct().Count(), Is.EqualTo(AlbionCampaign.All.Length), "each its own file");
            Assert.That(AlbionCampaign.GjalpinulvaSealed, Is.False, "not loaded (the tests): nothing is sealed");
        }

        [Test]
        public void TheRaids_HaveThreePhases_AndTheirChampionsShieldThem()
        {
            Assert.That(PhasedRaid.PhaseAt(1.0), Is.EqualTo(1));
            Assert.That(PhasedRaid.PhaseAt(0.65), Is.EqualTo(2));
            Assert.That(PhasedRaid.PhaseAt(0.30), Is.EqualTo(3));
            Assert.That(PhasedRaid.Floor(2, true), Is.EqualTo(PhasedRaid.SecondFloor));
            Assert.That(PhasedRaid.Floor(3, false), Is.EqualTo(0), "the champion down: the boss can be hurt again");
            foreach (PhasedRaid r in PhasedRaid.All)
            {
                Assert.That(r.Names, Has.Length.EqualTo(3));
                Assert.That(r.Champions, Has.Length.EqualTo(2));
                Assert.That(r.Adds, Has.Length.EqualTo(2));
                Assert.That(r.Calls, Has.Length.EqualTo(2));
                Assert.That(new[] { r.Bolt, r.Root, r.Aoe2, r.Aoe3 }, Has.None.Null);
            }
            var spells = PhasedRaid.All.SelectMany(r => new[] { r.Bolt, r.Root, r.Aoe2, r.Aoe3 }).Select(x => x.ID).ToList();
            Assert.That(spells.Distinct().Count(), Is.EqualTo(spells.Count), "every spell its own id");
            Assert.That(MidgardRaids.Hati.Champions[0].Name, Does.Contain("Skoll"));
        }

        [Test]
        public void TheStories_LeadToTheCampaigns()
        {
            var rk = Stories("mid_raumarik")["quests"].ToList();
            var mh = Stories("mid_malmohus")["quests"].ToList();
            Assert.That(rk.Select(q => (string) q["id"]), Is.SupersetOf(new[] { "red_dagger", "grani" }), "old progress keeps its quest ids");
            Assert.That(mh.Select(q => (string) q["id"]), Is.SupersetOf(new[] { "missionary", "svartalf_steel" }));
            Assert.That(mh.Single(q => (string) q["id"] == "missionary")["level"].Value<int>(), Is.GreaterThanOrEqualTo(50), "brought up to the Elite band");
            foreach (var qs in new[] { rk, mh })
            {
                Assert.That(qs.Count, Is.InRange(11, 30));
                var ids = qs.Select(q => (string) q["id"]).ToHashSet();
                foreach (JToken q in qs.Where(q => q["requires"] != null))
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            }
            Assert.That(rk.Single(q => (string) q["id"] == "rk_kings_march").ToString(), Does.Contain("Hallvard").And.Contain("for the King"));
            Assert.That(mh.Single(q => (string) q["id"] == "mh_oath").ToString(), Does.Contain("Groa").And.Contain("by the Oath"));
            Assert.That(MidgardCampaigns.Winter.MarshalName, Does.Contain("Hallvard"));
            Assert.That(MidgardCampaigns.Wyrm.MarshalName, Is.EqualTo("Volva Groa"));
        }

        [Test]
        public void TheFactions_JoinTheirKin()
        {
            foreach (var (zone, a, kinOf, f) in new[] { (108, "kings_host", "eiriks_huscarls", "mid_raumarik"), (116, "volur_oath", "haggerfel_volur", "mid_malmohus") })
            {
                RepZoneDef z = RepDefs.ForZone(zone);
                Assert.That(z.Faction(a), Is.Not.Null);
                Assert.That(RepDefs.Faction(kinOf).Kin, Does.Contain(a));
                Assert.That(Stories(f)["quests"].Select(q => (string) q["id"]).All(q => z.Quests.ContainsKey(q)), "every quest is someone's");
            }
        }
    }
}
