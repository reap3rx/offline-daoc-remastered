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
    /// <summary>The Cliffs of Moher (the zone brief and the owner's answers, 2026-11-23/24): Dangerous with grace toward
    /// Connacht, about 630 monsters, eleven events with the Norse landings and the Longphort (a smaller siege), 24 story
    /// quests, the Watch of Moher and the Seers of Moher, the Grey Man the purple. The Norse are a raiding party: they skirmish
    /// at Tir Urphost and move on, never holding it.</summary>
    [TestFixture]
    public sealed class UT_Cliffs
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone203_cliffs_of_moher.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone203_cliffs_of_moher.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_cliffs_of_moher.json"));
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

        static double[] Centre(JToken s) => s["at"] is JArray at ? new[] { (double) at[0] / 40, (double) at[1] / 40 }
            : s["area"] is JArray a ? new[] { ((double) a[0] + (double) a[2]) / 80, ((double) a[1] + (double) a[3]) / 80 }
            : s["route"] is JArray r ? new[] { (double) r[0][0] / 40, (double) r[0][1] / 40 } : null;

        [Test]
        public void ItIsDangerous_WithGraceTowardConnacht()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("dangerous"));
            var count = Tally(b);
            int total = count.Values.Sum();
            Assert.That(total, Is.InRange(560, 720));
            double Hard(Func<JToken, bool> f)
            {
                var c = Tally(b, f);
                int n = c.Values.Sum();
                return n == 0 ? 0 : (c.GetValueOrDefault("orange") + c.GetValueOrDefault("red")) / (double) n;
            }
            // the west (the cliffs, the coves, the Norse) is hard; the Connacht side (east) gets grace
            Assert.That(Hard(s => Centre(s) is double[] c && c[0] < 500), Is.GreaterThan(Hard(s => Centre(s) is double[] c && c[0] > 1000) + 0.2));
            Assert.That((string) b["tiers"]["The Grey Man"], Is.EqualTo("purple"));
        }

        [Test]
        public void TheNorse_AreMonstersInMidgardsGear()
        {
            var members = (JObject) Build["members"];
            var norse = members.Properties().Where(p => p.Name.StartsWith("Norse")).ToList();
            Assert.That(norse.Count, Is.GreaterThanOrEqualTo(5));
            foreach (JProperty p in norse)
            {
                Assert.That((int?) p.Value["realm"], Is.EqualTo(0), p.Name + ": fights as a monster, not a Midgard guard");
                Assert.That((bool?) p.Value["plain"], Is.True, p.Name);
                Assert.That((string) p.Value["guild"], Does.Contain("Saltwolves"), p.Name);
            }
        }

        [Test]
        public void ElevenEvents_TheLongshipsRaidAndMoveOn()
        {
            ZoneEventsDef z = Events;
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids, Is.Unique);
            Assert.That(ids.Count, Is.EqualTo(11));
            foreach (string id in new[] { "cliffs_of_moher_cliff_dwellers", "cliffs_of_moher_fog_wraiths", "cliffs_of_moher_distorters",
                         "tower_moher_watch", "cliffs_of_moher_koalinth_raid", NorseLanding.ChainId, "cliffs_fetch_night",
                         "cliffs_wreckers_lights", "cliffs_aughisky_run" })
                Assert.That(ids, Does.Contain(id));
            Assert.That(z.Chains.First(c => c.Id == "cliffs_fetch_night").Time, Is.EqualTo("night"));
            ChainDef land = z.Chains.First(c => c.Id == NorseLanding.ChainId);
            Assert.That(land.AutoFailS, Is.GreaterThan(0));
            Assert.That(land.Stages.First(s => s.Id == land.Start).OnFail, Is.EqualTo(NorseLanding.BeachheadStage));
            StageDef head = land.Stages.First(s => s.Id == NorseLanding.BeachheadStage);
            Assert.That(head.Type, Is.EqualTo("occupy"));
            // the beachhead is in the coves, below the cliffs - never Tir Urphost (owner: "a skirmish and then move on")
            Assert.That(NorseLanding.Routes.SelectMany(r => r).All(p => p.x < 800), "the raiders turn back before the town's far side");
            Assert.That(NorseLanding.MaxPatrols * NorseLanding.PatrolSize, Is.LessThanOrEqualTo(8), "a raiding party, not an army");
            HashSet<string> ev = Items("ev203_cliffs"), lp = Items("lp203_longphort");
            foreach (ItemRewardDef i in z.Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                Assert.That(ev.Contains($"{i.Id}_l30") || lp.Contains($"{i.Id}_l30"), i.Id);
        }

        [Test]
        public void TheLongphortIsASmallerSiege()
        {
            ZoneEventsDef z = Events;
            SiegeDef d = z.Siege;
            Assert.That(d, Is.Not.Null);
            Assert.That(d.Faction, Is.EqualTo("watch_of_moher"));
            Assert.That(d.Raids.Count, Is.EqualTo(0), "smaller: only the one return");
            Assert.That(d.LastRaid, Is.EqualTo("cliffs_longphort_return"));
            Assert.That(d.BotsGoAfterM, Is.EqualTo(30));
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            foreach (string q in d.Quests.Keys)
                Assert.That(quests, Does.Contain(q));
            HashSet<string> lp = Items("lp203_longphort");
            foreach (SiegeStockDef st in d.CampNpcs.Where(n => n.Kind is "marks" or "coin").SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(lp.Contains(st.Item) || lp.Contains(st.Item + "_l30"), st.Item);
        }

        [Test]
        public void TwentyFourQuests_WithTheOldTwoFoldedIn()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(24));
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("fetch").And.Contain("koalinth_pact"), "old progress keeps its quest ids");
            Assert.That(qs.Count(q => (bool?) q["group"] == true), Is.GreaterThanOrEqualTo(2));
            foreach (JToken q in qs.Where(q => q["requires"] != null))
                Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            Assert.That(qs.Any(q => (string) q["id"] == "cm_grey_man" && (bool?) q["group"] == true), "the Grey Man's finale");
        }

        [Test]
        public void TheWatchAndTheSeers_AreKinToTheirNeighbours()
        {
            RepZoneDef z = RepDefs.ForZone(203);
            Assert.That(z, Is.Not.Null);
            Assert.That(z.Faction("watch_of_moher").Title(Rank.Legend, false), Is.EqualTo("Watch-Captain of Moher"));
            Assert.That(z.Faction("seers_of_moher").Title(Rank.Legend, false), Is.EqualTo("Seer of the Western Edge"));
            Assert.That(RepDefs.Faction("mag_mell_guard").Kin, Does.Contain("watch_of_moher"));
            Assert.That(RepDefs.Faction("lucht_feasa").Kin, Does.Contain("seers_of_moher"));
        }

        [Test]
        public void TheFetchsPenny_OnTheHighestCliff()
        {
            Assert.That(ZoneEggs.OnHeadland(120, 1585), Is.True);
            Assert.That(ZoneEggs.OnHeadland(805, 388), Is.False, "not in the Watchtower");
            Assert.That(ZoneEggs.Flips.All(f => f.Contains("Not today")), Is.True);
        }
    }
}
