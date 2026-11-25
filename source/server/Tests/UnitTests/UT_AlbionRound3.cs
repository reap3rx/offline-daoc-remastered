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
    /// <summary>Albion's PvE rework, round 3 ("Albion - the plan", 2026-11-24): Black Mountains North (Dangerous; the full siege of
    /// Dinas Emrys, over the dragons' pit), Cornwall (Deadly; Albion's hard start at Cornwall Station; the Drowned Ninth out of
    /// Cardova) and Lyonesse (Deadly; Tristan's drowned country under the white dragon's storm).</summary>
    [TestFixture]
    public sealed class UT_AlbionRound3
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

        static readonly (string Build, string Story, string Events, int Zone, string Rating)[] Zones =
        {
            ("zone003_black_mountains_north", "alb_black_mtns_north", "zone003_black_mountains_north", 3, "dangerous"),
            ("zone006_cornwall", "alb_cornwall", "zone006_cornwall", 6, "deadly"),
            ("zone010_lyonesse", "alb_lyonesse", "zone010_lyonesse", 10, "deadly"),
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
        public void TheRatings_AndTheirCons()
        {
            foreach (var z in Zones)
            {
                JToken b = Build(z.Build);
                Assert.That((string) b["rating"], Is.EqualTo(z.Rating), z.Build);
                var t = Tiers(b);
                int total = t.Values.Sum();
                Assert.That(total, Is.InRange(450, 800), z.Build);
                double hard = (t.GetValueOrDefault("orange") + t.GetValueOrDefault("red")) / (double) total;
                if (z.Rating == "deadly")
                    Assert.That(hard, Is.GreaterThan(0.6), z.Build + ": oranges and reds");
                else
                    Assert.That((t.GetValueOrDefault("yellow") + t.GetValueOrDefault("orange")) / (double) total, Is.GreaterThan(0.7), z.Build + ": yellows and oranges");
            }
            Assert.That((string) Build("zone006_cornwall")["tiers"]["Cirfans"], Is.EqualTo("purple"));
            Assert.That((string) Build("zone010_lyonesse")["tiers"]["Cailleach Uragaig"], Is.EqualTo("purple"));
        }

        [Test]
        public void CornwallStation_IsAlbionsHardStart()
        {
            string res = Asm.GetManifestResourceNames().Single(n => n.EndsWith("level_bands.json", System.StringComparison.OrdinalIgnoreCase));
            using var rd = new StreamReader(Asm.GetManifestResourceStream(res)!);
            var hard = DOL.GS.LevelBands.StartsOf(DOL.GS.LevelBands.Parse(rd.ReadToEnd()), DOL.GS.eRealm.Albion).Single(x => x.Hard);
            Assert.That(hard.Name, Is.EqualTo("Cornwall Station"));
            Assert.That(hard.Rating, Is.EqualTo("deadly"));
            var qs = Stories("alb_cornwall")["quests"].ToList();
            Assert.That(qs.Where(q => (int) q["level"] <= 7).Select(q => (string) q["id"]),
                Is.EquivalentTo(new[] { "cw_moor_bears", "cw_spiderlings", "cw_moor_wolves" }), "three short quests on the moor");
        }

        [Test]
        public void TheStories_KeepTheOldQuests()
        {
            var old = new Dictionary<string, string[]> { ["alb_black_mtns_north"] = new[] { "last_shift", "crimson_bargain" },
                ["alb_cornwall"] = new[] { "white_wolf", "drowned_ninth" }, ["alb_lyonesse"] = new[] { "last_evening", "arawn_sacrament" } };
            foreach (var z in Zones)
            {
                var qs = Stories(z.Story)["quests"].ToList();
                Assert.That(qs.Count, Is.InRange(17, 30), z.Story);
                var ids = qs.Select(q => (string) q["id"]).ToHashSet();
                Assert.That(ids, Is.SupersetOf(old[z.Story]), "old progress keeps its quest ids");
                foreach (JToken q in qs.Where(q => q["requires"] != null))
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            }
            Assert.That(Stories("alb_black_mtns_north")["quests"].Single(q => (string) q["id"] == "bn_necromancers").ToString(),
                Does.Contain("Llyn Barfog"), "the pit's far end is Morgana's lake");
        }

        [Test]
        public void DinasEmrys_IsAFullSiege()
        {
            ZoneEventsDef e = Events("zone003_black_mountains_north");
            SiegeDef d = e.Siege;
            Assert.That(d.Faction, Is.EqualTo("snowdonia_garrison"));
            Assert.That(d.Raids, Is.Not.Empty, "a raid before the last one");
            Assert.That(e.Chains.Single(c => c.Id == d.Assault).Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss" }));
            HashSet<string> items = Items("de003_dinas_emrys");
            foreach (SiegeStockDef st in d.CampNpcs.SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(items.Any(i => i.StartsWith(st.Item)), st.Item);
            var nu = new HashSet<string>();
            foreach (string f in new[] { "ev003_black_mtns_north", "ev006_cornwall", "ev010_lyonesse", "de003_dinas_emrys" })
                nu.UnionWith(Items(f));
            foreach (var z in Zones)
                foreach (ItemRewardDef i in Events(z.Events).Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>())
                             .Where(i => i.Id.StartsWith("nu0") || i.Id.StartsWith("de003")))
                    Assert.That(nu.Any(x => x.StartsWith(i.Id)), i.Id);
        }

        [Test]
        public void TheFactions_JoinTheirKin()
        {
            foreach (var (zone, a, b, f) in new[] { (3, "snowdonia_garrison", "emrys_circle", "alb_black_mtns_north"),
                         (6, "men_of_tintagel", "oath_of_corineus", "alb_cornwall"), (10, "lyonesse_remnant", "harpers_of_tristan", "alb_lyonesse") })
            {
                RepZoneDef z = RepDefs.ForZone(zone);
                Assert.That(z.Faction(a), Is.Not.Null);
                Assert.That(z.Faction(b), Is.Not.Null);
                Assert.That(RepDefs.Faction("pendragons_watch").Kin, Does.Contain(a));
                Assert.That(RepDefs.Faction("abbey_faithful").Kin, Does.Contain(b));
                Assert.That(Stories(f)["quests"].Select(q => (string) q["id"]).All(q => z.Quests.ContainsKey(q)), "every quest is someone's");
            }
        }
    }
}
