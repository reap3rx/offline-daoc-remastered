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
    /// <summary>Albion's PvE rework, round 2 ("Albion - the plan", 2026-11-24): Salisbury Plains (Wild, Deadly round the Giants'
    /// Dance and the great barrow - owner: "more dangerous/deadly near Stonehenge Barrows"), Campacorentin Forest (Wild with a
    /// Dangerous deep wood - "a blend of Wild and Dangerous") and Avalon Marsh (Wild, Deadly toward Cornwall). Two sieges: the
    /// Giants' Dance and the Vigil Keep.</summary>
    [TestFixture]
    public sealed class UT_AlbionRound2
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

        static readonly (string Build, string Story, string Events, int Zone)[] Zones =
        {
            ("zone001_salisbury_plains", "alb_salisbury_plains", "zone001_salisbury_plains", 1),
            ("zone008_campacorentin_forest", "alb_campacorentin", "zone008_campacorentin_forest", 8),
            ("zone009_avalon_marsh", "alb_avalon_marsh", "zone009_avalon_marsh", 9),
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
        public void AllWild_WithTheirDeadlyCorners()
        {
            foreach (var z in Zones)
            {
                JToken b = Build(z.Build);
                Assert.That((string) b["rating"], Is.EqualTo("wild"), z.Build);
                var t = Tiers(b);
                int total = t.Values.Sum();
                Assert.That(total, Is.InRange(800, 1050), z.Build);
                double mid = (t.GetValueOrDefault("blue") + t.GetValueOrDefault("yellow")) / (double) total;
                Assert.That(mid, Is.GreaterThan(0.55), z.Build + ": mostly blues and yellows");
                Assert.That(t.GetValueOrDefault("orange") + t.GetValueOrDefault("red"), Is.GreaterThan(30), z.Build + ": a dangerous corner");
            }
            JToken sp = Build("zone001_salisbury_plains");
            Assert.That(sp["members"].Values().Any(m => (string) m["tier"] == "purple"), "Gogmagog's bones");
            Assert.That(sp["sites"].Single(s => (string) s["id"] == "the_dance")["spawn"].Values().Sum(v => (int) v), Is.GreaterThanOrEqualTo(10));
            Assert.That((string) Build("zone009_avalon_marsh")["tiers"]["Marsh Lord"], Is.EqualTo("purple"));
        }

        [Test]
        public void TheStories_KeepTheOldQuests_AndBothThreadsCross()
        {
            var old = new Dictionary<string, string[]> { ["alb_salisbury_plains"] = new[] { "under_stones", "white_horse" },
                ["alb_campacorentin"] = new[] { "page", "heretic" }, ["alb_avalon_marsh"] = new[] { "bog_king", "vigil" } };
            foreach (var z in Zones)
            {
                var qs = Stories(z.Story)["quests"].ToList();
                Assert.That(qs.Count, Is.InRange(17, 30), z.Story);
                var ids = qs.Select(q => (string) q["id"]).ToHashSet();
                Assert.That(ids, Is.SupersetOf(old[z.Story]), "old progress keeps its quest ids");
                foreach (JToken q in qs.Where(q => q["requires"] != null))
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            }
            string thorn = Stories("alb_campacorentin")["quests"].Single(q => (string) q["id"] == "cf_merlins_thorn").ToString();
            Assert.That(thorn, Does.Contain("white dragon").IgnoreCase.And.Contain("Afanc"), "Merlin points at both raids");
            Assert.That(Stories("alb_salisbury_plains")["quests"].Single(q => (string) q["id"] == "sp_the_dance").ToString(),
                Does.Contain("key under a crown"), "both threads at the Dance");
        }

        [Test]
        public void TheEvents_AndTheTwoForts()
        {
            foreach (var (zone, assault, faction, camp) in new[] { (1, "sp_dance_assault", "sisters_of_amesbury", "gd001_giants_dance"),
                         (9, "am_vigil_assault", "marsh_wardens", "vk009_vigil_keep") })
            {
                var z = Zones.Single(x => x.Zone == zone);
                ZoneEventsDef e = Events(z.Events);
                Assert.That(e.Chains.Select(c => c.Id), Is.Unique);
                SiegeDef d = e.Siege;
                Assert.That(d.Faction, Is.EqualTo(faction));
                Assert.That(d.Assault, Is.EqualTo(assault));
                Assert.That(e.Chains.Single(c => c.Id == d.Assault).Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss" }));
                var quests = Stories(z.Story)["quests"].Select(q => (string) q["id"]).ToHashSet();
                foreach (string q in d.Quests.Keys)
                    Assert.That(quests, Does.Contain(q));
                HashSet<string> items = Items(camp);
                foreach (SiegeStockDef st in d.CampNpcs.SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                    Assert.That(items.Any(i => i.StartsWith(st.Item)), st.Item);
            }
            ZoneEventsDef cf = Events("zone008_campacorentin_forest");
            Assert.That(cf.Chains.Any(c => c.Id == "cf_green_knight"), "the Green Knight's Game");
            var nu = new HashSet<string>();
            foreach (string f in new[] { "ev001_salisbury_plains", "ev008_campacorentin", "ev009_avalon_marsh", "gd001_giants_dance", "vk009_vigil_keep" })
                nu.UnionWith(Items(f));
            foreach (var z in Zones)
                foreach (ItemRewardDef i in Events(z.Events).Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>())
                             .Where(i => i.Id.StartsWith("nu00") || i.Id.StartsWith("gd001") || i.Id.StartsWith("vk009")))
                    Assert.That(nu.Any(x => x.StartsWith(i.Id)), i.Id);
        }

        [Test]
        public void TheFactions_AndTheirKin()
        {
            RepZoneDef sp = RepDefs.ForZone(1), cf = RepDefs.ForZone(8), am = RepDefs.ForZone(9);
            Assert.That(sp.Faction("sisters_of_amesbury").Title(Rank.Legend, false), Is.EqualTo("Mourner of the Long Knives"));
            Assert.That(sp.Shared, Does.Contain("pendragons_watch"));
            Assert.That(cf.Faction("thornwardens").Title(Rank.Legend, false), Is.EqualTo("Thornwarden of Campacorentin"));
            Assert.That(am.Faction("keepers_of_the_isle").Title(Rank.Legend, false), Is.EqualTo("Guardian of the Sleeper"));
            Assert.That(RepDefs.Faction("pendragons_watch").Kin, Does.Contain("marsh_wardens").And.Contain("ulfwych_rangers"));
            Assert.That(RepDefs.Faction("abbey_faithful").Kin, Does.Contain("thornwardens"));
            foreach (var (z, f) in new[] { (sp, "alb_salisbury_plains"), (cf, "alb_campacorentin"), (am, "alb_avalon_marsh") })
                Assert.That(Stories(f)["quests"].Select(q => (string) q["id"]).All(q => z.Quests.ContainsKey(q)), "every quest is someone's");
        }
    }
}
