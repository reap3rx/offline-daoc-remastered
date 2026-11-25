using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using DOL.GS.DynamicEvents;
using DOL.GS.Reputation;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Midgard's PvE rework, round 1 ("Midgard - the plan", 2026-11-24): the Vale of Mularn (Peaceful, the hub; both
    /// threads' first signs - the Moon-Howler at Darkness Falls, the dragon-preacher at the Vendo Caverns) and East Svealand
    /// (Peaceful; the Grey Hames have taken Ulfrstead, the fort to retake; drakelings at Nisse's Lair).</summary>
    [TestFixture]
    public sealed class UT_MidgardRound1
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
        public void BothArePeaceful_GreensAndBlues()
        {
            foreach (string f in new[] { "zone100_vale_of_mularn", "zone101_east_svealand" })
            {
                JToken b = Build(f);
                Assert.That((string) b["rating"], Is.EqualTo("peaceful"), f);
                var t = Tiers(b);
                int total = t.Values.Sum();
                Assert.That(total, Is.InRange(600, 1100), f);
                Assert.That((t.GetValueOrDefault("green") + t.GetValueOrDefault("blue")) / (double) total, Is.GreaterThan(0.85), f + ": mostly greens and blues");
                Assert.That(t.GetValueOrDefault("orange") + t.GetValueOrDefault("purple"), Is.EqualTo(0), f + ": nothing above red");
            }
        }

        [Test]
        public void TheStories_KeepTheOldQuests_AndShowBothThreads()
        {
            var old = new Dictionary<string, string[]> { ["mid_mularn"] = new[] { "huldra", "gormr" },
                ["mid_east_svealand"] = new[] { "thrall_price", "tomte_due" } };
            foreach (var (f, ids0) in old.Select(kv => (kv.Key, kv.Value)))
            {
                var qs = Stories(f)["quests"].ToList();
                Assert.That(qs.Count, Is.InRange(17, 30), f);
                var ids = qs.Select(q => (string) q["id"]).ToHashSet();
                Assert.That(ids, Is.SupersetOf(ids0), "old progress keeps its quest ids");
                foreach (JToken q in qs.Where(q => q["requires"] != null))
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            }
            string mularn = Stories("mid_mularn").ToString();
            Assert.That(mularn, Does.Contain("Raumarik"), "the west thread's first sign: frost out of Raumarik");
            Assert.That(mularn, Does.Contain("Gjalpinulva"), "the south thread's first sign: the dragon's preacher");
            Assert.That(Stories("mid_east_svealand").ToString(), Does.Contain("Gotar"), "the missionaries' road runs back to Gotar");
        }

        [Test]
        public void Ulfrstead_IsAFortToRetake()
        {
            ZoneEventsDef e = Events("zone101_east_svealand");
            SiegeDef d = e.Siege;
            Assert.That(d, Is.Not.Null);
            Assert.That(d.Faction, Is.EqualTo("steading_league"), "the zone's own faction");
            Assert.That(RepDefs.ForZone(101).Faction(d.Faction), Is.Not.Null);
            Assert.That(e.Chains.Single(c => c.Id == d.Assault).Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss" }));
            Assert.That(e.Chains.Any(c => c.Id == d.LastRaid));
            double Dist(double[] a, double[] b) => Math.Sqrt(Math.Pow(a[0] - b[0], 2) + Math.Pow(a[1] - b[1], 2));
            Assert.That(Dist(d.Staging, d.Area), Is.GreaterThan(d.Area[2]), "staging outside the fort");
            Assert.That(Dist(d.Landing, d.Area), Is.LessThan(d.Area[2]), "landing inside");
            foreach (SiegeNpcDef n in d.CampNpcs)
                Assert.That(Dist(n.Pos, d.Area), Is.LessThan(d.Area[2]), n.Name);
            HashSet<string> items = Items("uf101_ulfrstead");
            foreach (SiegeStockDef st in d.CampNpcs.SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(items.Any(i => i.StartsWith(st.Item)), st.Item);
            var nu = new HashSet<string>();
            foreach (string f in new[] { "ev100_mularn", "ev101_east_svealand", "uf101_ulfrstead" })
                nu.UnionWith(Items(f));
            foreach (string z in new[] { "zone100_vale_of_mularn", "zone101_east_svealand" })
                foreach (ItemRewardDef i in Events(z).Chains.Where(c => c.Id.StartsWith("md_") || c.Id.StartsWith("es_"))   // (the new chains: the old ones' drops are the zone's named uniques)
                             .SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                    Assert.That(nu.Any(x => x.StartsWith(i.Id)), i.Id);
            Assert.That(Events("zone100_vale_of_mularn").Chains.Single(c => c.Id == "md_moon_howler").Stages[1].Path.Count, Is.GreaterThan(2), "a hunt: it roams");
        }

        [Test]
        public void TheFactions_AndTheirKin()
        {
            RepZoneDef m = RepDefs.ForZone(100), s = RepDefs.ForZone(101);
            Assert.That(m.Faction("eiriks_huscarls"), Is.Not.Null);
            Assert.That(m.Faction("haggerfel_volur"), Is.Not.Null);
            Assert.That(s.Faction("steading_league"), Is.Not.Null);
            Assert.That(s.Faction("eiriks_huscarls"), Is.Not.Null, "the Huscarls are shared with East Svealand");
            Assert.That(RepDefs.Faction("eiriks_huscarls").Kin, Does.Contain("steading_league"));
            foreach (var (zone, f) in new[] { (100, "mid_mularn"), (101, "mid_east_svealand") })
                Assert.That(Stories(f)["quests"].Select(q => (string) q["id"]).All(q => RepDefs.ForZone(zone).Quests.ContainsKey(q)), "every quest is someone's");
        }
    }
}
