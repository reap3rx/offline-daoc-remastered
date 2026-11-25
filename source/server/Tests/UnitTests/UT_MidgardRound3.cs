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
    /// <summary>Midgard's PvE rework, round 3 ("Midgard - the plan", 2026-11-25): Muspelheim (Dangerous; the drakulv hatchery
    /// in the wyrm hills, the Brood-Sire a boss hunt), Skona Ravine (Dangerous; Ulfhamr, the werewolf hold, a siege for the Wolfsbane
    /// Rangers) and Vanern Swamp (Deadly; Hrafnsholm, the watch-hold the hagbui took, a fort to retake for the Wardens of Vanern).</summary>
    [TestFixture]
    public sealed class UT_MidgardRound3
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
        public void TheRatings_DangerousDangerousAndDeadly()
        {
            foreach (var (f, rating) in new[] { ("zone104_muspelheim", "dangerous"), ("zone106_skona_ravine", "dangerous"), ("zone107_vanern_swamp", "deadly") })
            {
                JToken b = Build(f);
                Assert.That((string) b["rating"], Is.EqualTo(rating), f);
                var t = Tiers(b);
                int total = t.Values.Sum();
                Assert.That(total, Is.InRange(600, 1100), f);
                double hard = (t.GetValueOrDefault("orange") + t.GetValueOrDefault("red")) / (double) total;
                Assert.That(t.GetValueOrDefault("green"), Is.EqualTo(0), f + ": nothing green");
                if (rating == "deadly")
                    Assert.That(hard, Is.GreaterThan(0.75), f + ": oranges and reds everywhere");
                else
                    Assert.That(hard, Is.InRange(0.3, 0.75), f + ": oranges among the yellows");
            }
        }

        [Test]
        public void TheStories_KeepTheOldQuests_AndFollowTheThreads()
        {
            var old = new Dictionary<string, string[]> { ["mid_muspelheim"] = new[] { "dagnar", "ragnvald" },
                ["mid_skona"] = new[] { "moonbound", "sidhe_maps" }, ["mid_vanern"] = new[] { "clay_child", "barrow_brother" } };
            foreach (var (f, ids0) in old.Select(kv => (kv.Key, kv.Value)))
            {
                var qs = Stories(f)["quests"].ToList();
                Assert.That(qs.Count, Is.InRange(14, 30), f);
                var ids = qs.Select(q => (string) q["id"]).ToHashSet();
                Assert.That(ids, Is.SupersetOf(ids0), "old progress keeps its quest ids");
                foreach (JToken q in qs.Where(q => q["requires"] != null))
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            }
            Assert.That(Stories("mid_muspelheim").ToString(), Does.Contain("Gjalpinulva").And.Contain("Hierophant"), "the south thread: the dragon's brood");
            Assert.That(Stories("mid_skona").ToString(), Does.Contain("Hati").And.Contain("Raumarik"), "the west thread: Hati's host gathers");
            Assert.That(Stories("mid_vanern").ToString(), Does.Contain("Hati").And.Contain("Raumarik"), "the west thread: the dead open the door");
        }

        [TestCase("zone106_skona_ravine", 106, "wolfsbane_rangers", "uf106_ulfhamr", "mid_skona")]
        [TestCase("zone107_vanern_swamp", 107, "vanern_wardens", "uf107_hrafnsholm", "mid_vanern")]
        public void TheStrongholds_AreSieges(string zf, int zone, string faction, string camp, string story)
        {
            ZoneEventsDef e = Events(zf);
            SiegeDef d = e.Siege;
            Assert.That(d, Is.Not.Null);
            Assert.That(d.Faction, Is.EqualTo(faction), "the zone's own faction");
            Assert.That(RepDefs.ForZone(zone).Faction(d.Faction), Is.Not.Null);
            Assert.That(e.Chains.Single(c => c.Id == d.Assault).Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss" }));
            Assert.That(e.Chains.Any(c => c.Id == d.LastRaid));
            double Dist(double[] a, double[] b) => Math.Sqrt(Math.Pow(a[0] - b[0], 2) + Math.Pow(a[1] - b[1], 2));
            Assert.That(Dist(d.Staging, d.Area), Is.GreaterThan(d.Area[2]), "staging outside");
            Assert.That(Dist(d.Landing, d.Area), Is.LessThan(d.Area[2]), "landing inside");
            foreach (SiegeNpcDef n in d.CampNpcs)
                Assert.That(Dist(n.Pos, d.Area), Is.LessThan(d.Area[2]), n.Name);
            HashSet<string> items = Items(camp);
            foreach (SiegeStockDef st in d.CampNpcs.SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(items.Any(i => i.StartsWith(st.Item)), st.Item);
            var ids = Stories(story)["quests"].Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Is.SupersetOf(d.Quests.Keys), "the siege is fed by the zone's own quests");
            Assert.That(e.Chains.Select(c => c.Id), Is.SupersetOf(d.Feeds.Keys), "and its own events");
            var build = Build(zf);
            Assert.That(build["sites"].Select(s => (string) s["id"]), Is.SupersetOf(d.Sites), "the hold's sites are the build's");
        }

        [Test]
        public void TheBroodSire_Roams_AndTheRewardsExist()
        {
            Assert.That(Events("zone104_muspelheim").Chains.Single(c => c.Id == "mu_brood_sire").Stages[1].Path.Count, Is.GreaterThan(2), "a hunt: it roams the wyrm hills");
            var nu = new HashSet<string>();
            foreach (string f in new[] { "ev104_muspelheim", "ev106_skona", "ev107_vanern", "uf106_ulfhamr", "uf107_hrafnsholm" })
                nu.UnionWith(Items(f));
            foreach (string z in new[] { "zone104_muspelheim", "zone106_skona_ravine", "zone107_vanern_swamp" })
                foreach (ItemRewardDef i in Events(z).Chains.Where(c => c.Id.StartsWith("mu_") || c.Id.StartsWith("sk_") || c.Id.StartsWith("vn_"))
                             .SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                    Assert.That(nu.Any(x => x.StartsWith(i.Id)), i.Id);
        }

        [Test]
        public void TheFactions_AndTheirKin()
        {
            Assert.That(RepDefs.ForZone(104).Faction("khizil_forge"), Is.Not.Null);
            Assert.That(RepDefs.ForZone(104).Faction("eiriks_huscarls"), Is.Not.Null, "the Huscarls at Brika's camp");
            Assert.That(RepDefs.ForZone(106).Faction("wolfsbane_rangers"), Is.Not.Null);
            Assert.That(RepDefs.ForZone(106).Faction("seithkona_circle"), Is.Not.Null);
            Assert.That(RepDefs.ForZone(107).Faction("vanern_wardens"), Is.Not.Null);
            Assert.That(RepDefs.Faction("eiriks_huscarls").Kin, Is.SupersetOf(new[] { "khizil_forge", "wolfsbane_rangers", "vanern_wardens" }), "the soldiers' kin");
            Assert.That(RepDefs.Faction("haggerfel_volur").Kin, Does.Contain("seithkona_circle"), "the keepers of the old ways");
            foreach (var (zone, f) in new[] { (104, "mid_muspelheim"), (106, "mid_skona"), (107, "mid_vanern") })
                Assert.That(Stories(f)["quests"].Select(q => (string) q["id"]).All(q => RepDefs.ForZone(zone).Quests.ContainsKey(q)), "every quest is someone's");
        }
    }
}
