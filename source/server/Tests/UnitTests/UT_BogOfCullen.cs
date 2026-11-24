using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using DOL.GS;
using DOL.GS.DynamicEvents;
using DOL.GS.EasterEggs;
using DOL.GS.Reputation;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>The Bog of Cullen (the zone brief and the owner's answers, 2026-11-24): Deadly, a little harder than Lough Gur; the
    /// Glimmer holds the Gemstone Tower (the set-piece); Badb the purple; the Azure hostile here; the wildlife cut and more Glimmer;
    /// the Clann of Alainn Bin and the Keeners of Cullen.</summary>
    [TestFixture]
    public sealed class UT_BogOfCullen
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone205_bog_of_cullen.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone205_bog_of_cullen.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_bog_of_cullen.json"));
        static HashSet<string> Items(string file) => JToken.Parse(Text("StoryItems." + file + ".json")).Select(r => (string) r["Id_nb"]).ToHashSet();

        static Dictionary<string, int> Tally(JToken b)
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
        public void ItIsDeadly_TheWildlifeCut_TheGlimmerAdded()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("deadly"));
            var t = Tally(b);
            int total = t.Values.Sum();
            Assert.That(total, Is.InRange(500, 680));
            double hard = (t.GetValueOrDefault("orange") + t.GetValueOrDefault("red")) / (double) total;
            Assert.That(hard, Is.GreaterThan(0.45), "a little harder than Lough Gur");
            Assert.That((string) b["tiers"]["Badb"], Is.EqualTo("purple"));
            var members = (JObject) b["members"];
            int Count(Func<string, bool> f) => b["sites"].SelectMany(s => (s["spawn"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                .Where(p => f(p.Name)).Sum(p => (int) p.Value);
            Assert.That(Count(n => n == "savage fishing bear"), Is.LessThanOrEqualTo(40), "77 bears cut back");
            Assert.That(Count(n => (string) members[n]["faction"] == "glimmer"), Is.GreaterThanOrEqualTo(80), "more of the Glimmer");
            Assert.That(members.Properties().Where(p => p.Name.StartsWith("azure")).All(p => (string) p.Value["faction"] == "azure_crusade"));
            Assert.That((int) b["factions"]["azure_crusade"]["aggro"], Is.GreaterThan(75), "hostile here, to everyone");
            Assert.That(b["sites"].Any(s => (string) s["kind"] == "clear" && s["names"].Any(n => (string) n == "far dorocha")), "Cliodna's guards gone");
        }

        [Test]
        public void ElevenEvents_AndTheGemstoneTower()
        {
            ZoneEventsDef z = Events;
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids, Is.Unique);
            Assert.That(ids.Count, Is.EqualTo(11));
            Assert.That(z.Chains.Single(c => c.Id == "bog_of_cullen_wayguards").Giver.Name, Is.EqualTo("Sentinel Una"), "Silvermine keeps its Muirne");
            SiegeDef d = z.Siege;
            Assert.That(d, Is.Not.Null);
            Assert.That(d.Faction, Is.EqualTo("keeners_of_cullen"));
            Assert.That(d.Assault, Is.EqualTo("bc_tower_assault"));
            Assert.That(d.LastRaid, Is.EqualTo("bc_tower_return"));
            ChainDef a = z.Chains.Single(c => c.Id == d.Assault);
            Assert.That(a.Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss" }), "the causeway, the three gems, the Gem-Warden");
            Assert.That(a.Stages[1].Wards.Count, Is.EqualTo(3));
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            foreach (string q in d.Quests.Keys)
                Assert.That(quests, Does.Contain(q));
            HashSet<string> ev = Items("ev205_bog_of_cullen"), gt = Items("gt205_gemstone_tower");
            foreach (ItemRewardDef i in z.Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>())
                         .Where(i => !i.Id.StartsWith("nu205_")))
                Assert.That(ev.Contains($"{i.Id}_l30") || gt.Contains($"{i.Id}_l30"), i.Id);
            foreach (SiegeStockDef st in d.CampNpcs.Where(n => n.Kind is "marks").SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(gt.Contains(st.Item) || gt.Contains(st.Item + "_l30"), st.Item);
        }

        [Test]
        public void NineteenQuests_TheOldTwoKept()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(19));
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("lhiannan").And.Contain("keening"), "old progress keeps its quest ids");
            Assert.That(qs.Count(q => (bool?) q["group"] == true), Is.EqualTo(4), "the Keening, the marshal, Badb, the lantern-bearer");
            foreach (JToken q in qs.Where(q => q["requires"] != null))
                Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
        }

        [Test]
        public void TheClannAndTheKeeners()
        {
            RepZoneDef z = RepDefs.ForZone(205);
            Assert.That(z, Is.Not.Null);
            Assert.That(z.Faction("clann_of_alainn_bin").Title(Rank.Legend, false), Is.EqualTo("Champion of Cullen"));
            Assert.That(z.Faction("keeners_of_cullen").Title(Rank.Legend, false), Is.EqualTo("Voice of the Keen"));
            Assert.That(RepDefs.Faction("sentinels_of_ceannai").Kin, Does.Contain("clann_of_alainn_bin"));
            Assert.That(RepDefs.Faction("aines_circle").Kin, Does.Contain("keeners_of_cullen"));
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            Assert.That(quests.All(q => z.Quests.ContainsKey(q)), "every quest is someone's");
        }

        [Test]
        public void TheLoneLight_InTheEasternBog()
        {
            Assert.That(ZoneEggs.ByTheLoneLight(1380, 560), Is.True);
            Assert.That(ZoneEggs.ByTheLoneLight(1278, 1294), Is.False, "not in Alainn Bin");
        }
    }
}
