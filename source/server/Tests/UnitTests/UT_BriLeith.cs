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
    /// <summary>The Valley of Bri Leith (the zone brief and the owner's markup, 2026-11-23): Wild, darkening to the harder
    /// monsters by the Cursed Forest's edge, ten events, 27 story quests, the Rangers of Druim Cain and Muintir Etaine,
    /// the Forest Gate (won: an easier road into the Cursed Forest; raided: lost), and the scarlet fly at Moon Lake.</summary>
    [TestFixture]
    public sealed class UT_BriLeith
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone206_valley_of_bri_leith.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone206_valley_of_bri_leith.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_bri_leith.json"));
        static HashSet<string> Items(string file) => JToken.Parse(Text("StoryItems." + file + ".json")).Select(r => (string) r["Id_nb"]).ToHashSet();

        static Dictionary<string, int> Tally(JToken b, Func<JToken, bool> site = null)
        {
            var members = (JObject) b["members"];
            var count = new Dictionary<string, int>();
            void Add(string member, int n)
            {
                JToken m = members[member];
                Assert.That(m, Is.Not.Null, member);
                string t = (string) m["tier"];
                count[t] = count.GetValueOrDefault(t) + n;
                foreach (JProperty g in (m["guards"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(g.Name, n * (int) g.Value);
            }
            foreach (JToken s in b["sites"].Where(s => site == null || site(s)))
                foreach (JProperty sp in (s["spawn"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(sp.Name, (int) sp.Value);
            return count;
        }

        [Test]
        public void ItIsWild_MostlyBluesAndYellows_WithOneElder()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("wild"));
            var count = Tally(b);
            int total = count.Values.Sum();
            Assert.That(total, Is.InRange(560, 720));
            Assert.That((count.GetValueOrDefault("blue") + count.GetValueOrDefault("yellow")) / (double) total, Is.GreaterThanOrEqualTo(0.6));
            Assert.That(count.GetValueOrDefault("purple"), Is.EqualTo(1), "Fuamnach, on the Eye of the Wind");
            Assert.That(count.GetValueOrDefault("orange") + count.GetValueOrDefault("red"), Is.GreaterThan(0), "the warning by the Cursed Forest");
        }

        [Test]
        public void TenEvents_TheGateAndItsRaid()
        {
            ZoneEventsDef z = Events;
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids, Is.Unique);
            Assert.That(ids.Count, Is.EqualTo(10));
            foreach (string id in new[] { "bri_fuamnachs_gale", "bri_changeling_swap", "bri_stones_rise", "bri_forest_gate_assault", "bri_forest_gate_raid" })
                Assert.That(ids, Does.Contain(id));
            Assert.That(z.Chains.First(c => c.Id == "bri_changeling_swap").Time, Is.EqualTo("night"));
            SiegeDef d = z.Siege;
            Assert.That(d.Faction, Is.EqualTo("rangers_druim_cain"));
            Assert.That(d.LastRaid, Is.EqualTo("bri_forest_gate_raid"), "owner: raided, and can be lost");
            Assert.That(d.Sites, Does.Contain("cf_edge_n"), "won: fewer monsters on the road into the Cursed Forest");
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            foreach (string q in d.Quests.Keys)
                Assert.That(quests, Does.Contain(q));
            HashSet<string> ev = Items("ev206_bri_leith"), fg = Items("fg206_forest_gate");
            foreach (SiegeStockDef st in d.CampNpcs.Where(n => n.Kind is "marks" or "coin").SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(fg.Contains(st.Item) || fg.Contains(st.Item + "_l30"), st.Item);
            Assert.That(ev, Is.Not.Empty);
        }

        [Test]
        public void TwentySevenQuests_WithTheOldTwoFoldedIn()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(27));
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("veil").And.Contain("oak_heart"), "old progress keeps its quest ids");
            Assert.That(ids, Does.Contain("bl_road_to_caille"), "the Brynach start");
            foreach (JToken q in qs.Where(q => q["requires"] != null))
                Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
        }

        [Test]
        public void TheRangersAndTheHill_AreKinToTheirNeighbours()
        {
            RepZoneDef z = RepDefs.ForZone(206);
            Assert.That(z, Is.Not.Null);
            RepFactionDef r = z.Faction("rangers_druim_cain"), h = z.Faction("muintir_etaine");
            Assert.That(r, Is.Not.Null);
            Assert.That(h, Is.Not.Null);
            Assert.That(RepDefs.Faction("fianna_druim_ligen").Kin, Does.Contain("rangers_druim_cain"));
            Assert.That(RepDefs.Faction("order_of_the_rowan").Kin, Does.Contain("muintir_etaine"));
        }

        [Test]
        public void TheScarletFly_OnTheShoreAtNight_AndTheHazelnutAtDawn()
        {
            Assert.That(ZoneEggs.OnShore(1360 + 150, 1360 + 150), Is.True, "the lake's banks");
            Assert.That(ZoneEggs.OnShore(1360 + 400, 1360), Is.False);
            Assert.That(ZoneEggs.AtWell(1350, 680), Is.True);
            Assert.That(ZoneEggs.AtWell(1350, 1000), Is.False);
            Assert.That(ZoneEggs.Dawn(6 * 3_600_000u), Is.True);
            Assert.That(ZoneEggs.Dawn(12 * 3_600_000u), Is.False);
            Assert.That(ZoneEggs.Gulls.All(g => g.All(c => c < 128)), Is.True, "plain letters");
        }
    }
}
