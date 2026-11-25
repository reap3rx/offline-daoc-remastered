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
    /// <summary>Albion's PvE rework, round 1 ("Albion - the plan", Zone Reviews, 2026-11-24): Camelot Hills and Black Mountains
    /// South, both Peaceful. The Crimson's thread runs from Mithra's Tomb to "the Bishop" at Vetusta Abbey; the Pendragon's
    /// Watch is shared between them; Vetusta is the fort to retake.</summary>
    [TestFixture]
    public sealed class UT_AlbionRound1
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

        static int Placed(JToken b)
        {
            var members = (JObject) b["members"];
            int n = 0;
            void Add(string member, int k)
            {
                JToken m = members[member];
                Assert.That(m, Is.Not.Null, member);
                n += k;
                foreach (JProperty g in (m["guards"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(g.Name, k * (int) g.Value);
            }
            foreach (JToken s in b["sites"])
                foreach (JProperty sp in (s["spawn"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(sp.Name, (int) sp.Value);
            return n;
        }

        [Test]
        public void BothArePeaceful_AndFull()
        {
            JToken ch = Build("zone000_camelot_hills"), bs = Build("zone002_black_mountains_south");
            Assert.That((string) ch["rating"], Is.EqualTo("peaceful"));
            Assert.That((string) bs["rating"], Is.EqualTo("peaceful"));
            Assert.That(Placed(ch), Is.InRange(800, 1100));
            Assert.That(Placed(bs), Is.InRange(700, 1000));
            Assert.That((string) bs["tiers"]["Dark Bishop Burhoff"], Is.EqualTo("red"), "the Bishop is the zone's top");
        }

        [Test]
        public void TheStories_KeepTheOldQuests_AndFollowTheThread()
        {
            var ch = Stories("alb_camelot_hills")["quests"].ToList();
            var bs = Stories("alb_black_mtns_south")["quests"].ToList();
            Assert.That(ch.Count, Is.InRange(17, 30));
            Assert.That(bs.Count, Is.InRange(17, 30));
            var chIds = ch.Select(q => (string) q["id"]).ToHashSet();
            var bsIds = bs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(chIds, Is.SupersetOf(new[] { "tomb_keeps", "pilgrims", "bell_price" }), "old progress keeps its quest ids");
            Assert.That(bsIds, Is.SupersetOf(new[] { "singing_bridge", "willing_heart" }));
            foreach (var (qs, ids) in new[] { (ch, chIds), (bs, bsIds) })
                foreach (JToken q in qs.Where(q => q["requires"] != null))
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            Assert.That(ch.Single(q => (string) q["id"] == "ch_tomb_warden").ToString(), Does.Contain("Go north to the Bishop"),
                "the tomb's letter points to Vetusta");
            Assert.That(bs.Single(q => (string) q["id"] == "bs_dark_bishop").ToString(), Does.Contain("Giants' Dance"),
                "the Bishop's map points on to Salisbury");
        }

        [Test]
        public void TheEvents_AndVetusta()
        {
            ZoneEventsDef ch = Events("zone000_camelot_hills"), bs = Events("zone002_black_mountains_south");
            Assert.That(ch.Chains.Select(c => c.Id), Is.Unique.And.Contains("ch_crimson_rite"));
            Assert.That(ch.Chains.Count, Is.EqualTo(7));
            Assert.That(bs.Chains.Count, Is.EqualTo(7));
            SiegeDef d = bs.Siege;
            Assert.That(d, Is.Not.Null);
            Assert.That(d.Faction, Is.EqualTo("abbey_faithful"));
            ChainDef a = bs.Chains.Single(c => c.Id == d.Assault);
            Assert.That(a.Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss" }), "the yard, the three doors, Hrodric");
            Assert.That(bs.Chains.Any(c => c.Id == d.LastRaid));
            var quests = Stories("alb_black_mtns_south")["quests"].Select(q => (string) q["id"]).ToHashSet();
            foreach (string q in d.Quests.Keys)
                Assert.That(quests, Does.Contain(q));
            HashSet<string> va = Items("va002_vetusta");
            foreach (SiegeStockDef st in d.CampNpcs.SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(va.Any(i => i.StartsWith(st.Item)), st.Item);
            HashSet<string> nu = Items("ev000_camelot_hills");
            nu.UnionWith(Items("ev002_black_mtns_south"));
            nu.UnionWith(va);
            foreach (ItemRewardDef i in ch.Chains.Concat(bs.Chains).SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>())
                         .Where(i => i.Id.StartsWith("nu00") || i.Id.StartsWith("va002")))
                Assert.That(nu.Any(x => x.StartsWith(i.Id)), i.Id);
        }

        [Test]
        public void TheWardens_TheWatch_AndTheFaithful()
        {
            RepZoneDef ch = RepDefs.ForZone(0), bs = RepDefs.ForZone(2);
            Assert.That(ch, Is.Not.Null);
            Assert.That(bs, Is.Not.Null);
            Assert.That(ch.Faction("pendragons_watch").Title(Rank.Legend, false), Is.EqualTo("Shield of Camelot"));
            Assert.That(ch.Faction("wardens_of_cotswold").Title(Rank.Legend, false), Is.EqualTo("Hearthward of Cotswold"));
            Assert.That(bs.Faction("abbey_faithful").Title(Rank.Legend, false), Is.EqualTo("Bell-Ringer of Vetusta"));
            Assert.That(bs.Shared, Does.Contain("pendragons_watch"), "one Watch across the heartland");
            foreach (var (z, f) in new[] { (ch, "alb_camelot_hills"), (bs, "alb_black_mtns_south") })
                Assert.That(Stories(f)["quests"].Select(q => (string) q["id"]).All(q => z.Quests.ContainsKey(q)), "every quest is someone's");
        }
    }
}
