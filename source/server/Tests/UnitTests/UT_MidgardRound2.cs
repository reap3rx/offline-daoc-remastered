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
    /// <summary>Midgard's PvE rework, round 2 ("Midgard - the plan", 2026-11-25): West Svealand (Wild; the Blodfelag's
    /// Blood-Hall, the siege, for the Huginfel Shieldwall; the frozen gully), Gotar (Wild; the Scale-Caravan, a boss hunt on the
    /// trade road; the scale-traders and their dragon-preacher) and Myrkwood Forest (Deadly, Midgard's HARD START at Galplen;
    /// the threads cross - werewolves and drakulv both hunt Volva Groa; the Blood-Moon Wolf, a boss hunt).</summary>
    [TestFixture]
    public sealed class UT_MidgardRound2
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
        public void TheRatings_WildWildAndDeadly()
        {
            foreach (var (f, rating) in new[] { ("zone102_west_svealand", "wild"), ("zone103_gotar", "wild"), ("zone105_myrkwood_forest", "deadly") })
            {
                JToken b = Build(f);
                Assert.That((string) b["rating"], Is.EqualTo(rating), f);
                var t = Tiers(b);
                int total = t.Values.Sum();
                Assert.That(total, Is.InRange(600, 1100), f);
                if (rating == "deadly")
                {
                    Assert.That((t.GetValueOrDefault("orange") + t.GetValueOrDefault("red")) / (double) total, Is.GreaterThan(0.75), f + ": oranges and reds everywhere");
                    Assert.That(t.GetValueOrDefault("purple"), Is.InRange(1, 4), f + ": a few named purples");
                }
                else
                    Assert.That(t.GetValueOrDefault("purple"), Is.EqualTo(0), f + ": nothing purple in the wild");
            }
        }

        [Test]
        public void Galplen_IsTheHardStart_WithAGentleDoorstep()
        {
            var c = LevelBands.Parse(Text(Asm.GetManifestResourceNames().Single(n => n.EndsWith("level_bands.json", StringComparison.OrdinalIgnoreCase))));
            var mid = LevelBands.StartsOf(c, eRealm.Midgard);
            Assert.That(mid.Select(s => s.Name), Is.EqualTo(new[] { "Mularn", "Audliten", "Huginfel", "Fort Atla", "Galplen" }));
            Assert.That(mid.Select(s => s.Rating), Is.EqualTo(new[] { "peaceful", "peaceful", "wild", "wild", "deadly" }));
            Assert.That(mid.Single(s => s.Hard).Name, Is.EqualTo("Galplen"));
            // Galplen inside Myrkwood's square (zone 105 at 92,106 of region 100's 8192-unit grid)
            LevelBands.Start g = mid.Last();
            Assert.That(g.X, Is.InRange(92 * 8192 + 2000, 92 * 8192 + 65536 - 2000));
            Assert.That(g.Y, Is.InRange(106 * 8192 + 2000, 106 * 8192 + 65536 - 2000));
            // the doorstep: only blues and yellows in the wild ground round the town
            JToken b = Build("zone105_myrkwood_forest");
            JToken door = b["sites"].Single(s => (string) s["id"] == "galplen_outskirts");
            foreach (JProperty sp in ((JObject) door["spawn"]).Properties())
                Assert.That((string) b["members"][sp.Name]["tier"], Is.AnyOf("blue", "yellow"), sp.Name);
            // and the three short quests there that walk a new character round the town
            var hard = Stories("mid_myrkwood")["quests"].Where(q => (int) q["level"] <= 7).Select(q => (string) q["id"]).ToList();
            Assert.That(hard, Is.EqualTo(new[] { "mw_frogs", "mw_myrkcats", "mw_carrion" }));
        }

        [Test]
        public void TheStories_KeepTheOldQuests_AndCrossTheThreads()
        {
            var old = new Dictionary<string, string[]> { ["mid_west_svealand"] = new[] { "oathbreaker", "wolf_cord" },
                ["mid_gotar"] = new[] { "nacken", "rune_stave" }, ["mid_myrkwood"] = new[] { "willow_voice", "mora" } };
            foreach (var (f, ids0) in old.Select(kv => (kv.Key, kv.Value)))
            {
                var qs = Stories(f)["quests"].ToList();
                Assert.That(qs.Count, Is.InRange(15, 30), f);
                var ids = qs.Select(q => (string) q["id"]).ToHashSet();
                Assert.That(ids, Is.SupersetOf(ids0), "old progress keeps its quest ids");
                foreach (JToken q in qs.Where(q => q["requires"] != null))
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            }
            string ws = Stories("mid_west_svealand").ToString(), gt = Stories("mid_gotar").ToString(), mw = Stories("mid_myrkwood").ToString();
            Assert.That(ws, Does.Contain("Hati").And.Contain("Raumarik"), "the west thread: the Blodfelag swear to the Wolf's son");
            Assert.That(gt, Does.Contain("Gjalpinulva").And.Contain("Malmohus"), "the south thread: the scale goes north for the dragon");
            Assert.That(mw, Does.Contain("Hati").And.Contain("Gjalpinulva").And.Contain("Volva Groa"), "where the threads cross");
            Assert.That(gt, Does.Contain("Galplen"), "Gotar sends you on to the volva");
        }

        [Test]
        public void TheBloodHall_IsASiege()
        {
            ZoneEventsDef e = Events("zone102_west_svealand");
            SiegeDef d = e.Siege;
            Assert.That(d, Is.Not.Null);
            Assert.That(d.Faction, Is.EqualTo("huginfel_shieldwall"), "the zone's own faction");
            Assert.That(RepDefs.ForZone(102).Faction(d.Faction), Is.Not.Null);
            Assert.That(e.Chains.Single(c => c.Id == d.Assault).Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss" }));
            Assert.That(e.Chains.Any(c => c.Id == d.LastRaid));
            double Dist(double[] a, double[] b) => Math.Sqrt(Math.Pow(a[0] - b[0], 2) + Math.Pow(a[1] - b[1], 2));
            Assert.That(Dist(d.Staging, d.Area), Is.GreaterThan(d.Area[2]), "staging outside the hall");
            Assert.That(Dist(d.Landing, d.Area), Is.LessThan(d.Area[2]), "landing inside");
            foreach (SiegeNpcDef n in d.CampNpcs)
                Assert.That(Dist(n.Pos, d.Area), Is.LessThan(d.Area[2]), n.Name);
            HashSet<string> items = Items("uf102_blood_hall");
            foreach (SiegeStockDef st in d.CampNpcs.SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(items.Any(i => i.StartsWith(st.Item)), st.Item);
            var ids = Stories("mid_west_svealand")["quests"].Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Is.SupersetOf(d.Quests.Keys), "the siege is fed by the zone's own quests");
            Assert.That(e.Chains.Select(c => c.Id), Is.SupersetOf(d.Feeds.Keys), "and its own events");
        }

        [Test]
        public void TheHunts_Roam_AndTheirRewardsExist()
        {
            Assert.That(Events("zone103_gotar").Chains.Single(c => c.Id == "gt_scale_caravan").Stages[1].Path.Count, Is.GreaterThan(2), "the Scale-Caravan roams the trade road");
            Assert.That(Events("zone105_myrkwood_forest").Chains.Single(c => c.Id == "mw_blood_moon").Stages[1].Path.Count, Is.GreaterThan(2), "the Blood-Moon Wolf roams the west wood");
            var nu = new HashSet<string>();
            foreach (string f in new[] { "ev102_west_svealand", "ev103_gotar", "ev105_myrkwood", "uf102_blood_hall" })
                nu.UnionWith(Items(f));
            foreach (string z in new[] { "zone102_west_svealand", "zone103_gotar", "zone105_myrkwood_forest" })
                foreach (ItemRewardDef i in Events(z).Chains.Where(c => c.Id.StartsWith("ws_") || c.Id.StartsWith("gt_") || c.Id.StartsWith("mw_"))
                             .SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                    Assert.That(nu.Any(x => x.StartsWith(i.Id)), i.Id);
        }

        [Test]
        public void TheFactions_AndTheirKin()
        {
            Assert.That(RepDefs.ForZone(102).Faction("huginfel_shieldwall"), Is.Not.Null);
            Assert.That(RepDefs.ForZone(102).Faction("eiriks_huscarls"), Is.Not.Null, "the Huscarls hold Vindsaul Faste");
            Assert.That(RepDefs.ForZone(103).Faction("nalliten_runecasters"), Is.Not.Null);
            Assert.That(RepDefs.ForZone(103).Faction("eiriks_huscarls"), Is.Not.Null, "the Huscarls hold Fort Atla");
            Assert.That(RepDefs.ForZone(105).Faction("galplen_woodwards"), Is.Not.Null);
            Assert.That(RepDefs.ForZone(105).Faction("seidr_folk"), Is.Not.Null);
            Assert.That(RepDefs.Faction("eiriks_huscarls").Kin, Is.SupersetOf(new[] { "steading_league", "huginfel_shieldwall", "galplen_woodwards" }), "the soldiers' kin");
            Assert.That(RepDefs.Faction("haggerfel_volur").Kin, Is.SupersetOf(new[] { "nalliten_runecasters", "seidr_folk" }), "the keepers of the old ways");
            foreach (var (zone, f) in new[] { (102, "mid_west_svealand"), (103, "mid_gotar"), (105, "mid_myrkwood") })
                Assert.That(Stories(f)["quests"].Select(q => (string) q["id"]).All(q => RepDefs.ForZone(zone).Quests.ContainsKey(q)), "every quest is someone's");
        }
    }
}
