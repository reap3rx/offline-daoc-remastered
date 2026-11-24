using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using DOL.GS;
using DOL.GS.DynamicEvents;
using DOL.GS.EasterEggs;
using DOL.GS.Reputation;
using DOL.GS.ZoneStory;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Lough Gur (the zone brief and the owner's answers, 2026-11-24): Deadly, blending to Dangerous at the Shannon border;
    /// Culraid the realm's hard start; no cull ("Keep a high mob count in this zone"); the ursine out of Treibh Caillte in the east;
    /// nine events with the Earl's Ride (a moving boss); 26 story quests; Aine's Circle and the Sentinels of Ceannai (shared); the
    /// Azure neutral until a player's Burning.</summary>
    [TestFixture]
    public sealed class UT_LoughGur
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone204_lough_gur.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone204_lough_gur.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_lough_gur.json"));
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

        static double Hard(JToken b, Func<JToken, bool> f)
        {
            var c = Tally(b, f);
            int n = c.Values.Sum();
            return n == 0 ? 0 : (c.GetValueOrDefault("orange") + c.GetValueOrDefault("red") + c.GetValueOrDefault("purple")) / (double) n;
        }

        [Test]
        public void ItIsDeadly_FullOfMonsters_GentleOnlyAtCulraid()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("deadly"));
            int total = Tally(b).Values.Sum();
            Assert.That(total, Is.InRange(600, 760), "no cull: about 700 with the named and the farm (owner: \"Keep a high mob count\")");
            // Culraid's corner (the north-west, the Shannon side) is the gentlest ground; the south and the east are hard
            double culraid = Hard(b, s => Centre(s) is double[] c && c[0] < 520 && c[1] < 340);
            double south = Hard(b, s => Centre(s) is double[] c && c[1] > 1050);
            double east = Hard(b, s => Centre(s) is double[] c && c[0] > 1280);
            Assert.That(culraid, Is.LessThan(0.1), "the hard start's corner: greens, blues and a few yellows");
            Assert.That(south, Is.GreaterThan(culraid + 0.3));
            Assert.That(east, Is.GreaterThan(culraid + 0.3));
            Assert.That((string) b["tiers"]["Melancholic Fairy Queen"], Is.EqualTo("purple"));
        }

        [Test]
        public void TheUrsine_ComeOutOfTreibhCaillte_IntoTheEast()
        {
            JToken b = Build;
            var members = (JObject) b["members"];
            foreach (string u in new[] { "ursine warrior", "ursine shaman", "ursine sorcerer", "ursine thrall" })
                Assert.That(members[u], Is.Not.Null, u);
            var ursine = b["sites"].Where(s => (s["spawn"] as JObject)?.Properties().Any(p => p.Name.StartsWith("ursine")) == true).ToList();
            Assert.That(ursine.Count, Is.GreaterThanOrEqualTo(6));
            Assert.That(ursine.All(s => Centre(s)[0] > 1250), "the east (owner: \"occupy a lot of the eastern area\")");
            Assert.That(Tally(b, s => ursine.Contains(s)).Values.Sum(), Is.GreaterThanOrEqualTo(80), "tough camps, many of them");
        }

        [Test]
        public void TheAzure_AreNeutral_UntilTheBurning()
        {
            JToken b = Build;
            JToken azure = b["factions"]["azure"];
            Assert.That((int) azure["id"], Is.EqualTo(AzureStanding.FactionId));
            Assert.That((bool?) azure["shared"], Is.True, "each player's own standing, kept (FactionMgr)");
            Assert.That(AzureStanding.Hostile((int) azure["aggro"]), Is.False, "neutral to a newcomer");
            Assert.That(AzureStanding.Hostile(100), Is.True, "and hostile once turned");
            Assert.That(((JObject) b["members"]).Properties().Where(p => p.Name.StartsWith("azure")).All(p => (string) p.Value["faction"] == "azure"));
            var turn = Stories["quests"].Single(q => (string) q["id"] == AzureStanding.TurnQuest);
            Assert.That((string) turn["endings"]["default"]["wake_event"], Is.EqualTo("lg_azure_burning"), "the turn wakes the Burning");
            Assert.That(Events.Chains.Any(c => c.Id == "lg_azure_burning"));
        }

        [Test]
        public void NineEvents_TheEarlRidesAndHalts()
        {
            ZoneEventsDef z = Events;
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids, Is.Unique);
            Assert.That(ids.Count, Is.EqualTo(9));
            foreach (string id in new[] { "lough_gur_gurite_raiders", "lough_gur_luch_swarm", "lough_gur_cluricaun_revel", "lough_gur_gurite_ferry",
                         "lg_lights_on_the_lake", "lg_earls_ride", "lg_fairy_taking", "lg_deamhan_night", "lg_azure_burning" })
                Assert.That(ids, Does.Contain(id));
            ChainDef ride = z.Chains.Single(c => c.Id == "lg_earls_ride");
            Assert.That(ride.Time, Is.EqualTo("night"));
            StageDef r1 = ride.Stages.Single(s => s.Id == ride.Start);
            Assert.That(r1.Type, Is.EqualTo("intercept"), "a moving boss (owner: \"I loved your idea of a moving boss\")");
            Assert.That(r1.Stops.Count, Is.EqualTo(3), "three halts");
            Assert.That(r1.Stops.All(i => i > 0 && i < r1.Path.Count));
            Assert.That(r1.StopSays.Count, Is.EqualTo(3));
            Assert.That(r1.Boss.Name, Is.EqualTo("Gearoid Iarla"));
            Assert.That(ride.Stages.Single(s => s.Id == r1.OnFail).Type, Is.EqualTo("occupy"), "unanswered, his host holds the shore");
            HashSet<string> ev = Items("ev204_lough_gur");
            foreach (ItemRewardDef i in z.Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>())
                         .Where(i => !i.Id.StartsWith("nu204_")))          // (the old chains' own: the zone's named uniques, in the database)
                Assert.That(ev.Contains($"{i.Id}_l30"), i.Id);
        }

        [Test]
        public void TwentySixQuests_TheOldTwoKept_TheThreadsMeetOnTheCrannog()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(26));
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("cluricaun").And.Contain("amadan"), "old progress keeps its quest ids");
            Assert.That(qs.Count(q => (bool?) q["group"] == true), Is.EqualTo(3), "the Gurite-King, the Fairy Queen, the crannog");
            foreach (JToken q in qs.Where(q => q["requires"] != null))
                Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            // the hard start's own little arc begins at level 2, in Culraid
            Assert.That((int) qs.Single(q => (string) q["id"] == "lg_walking_wood")["level"], Is.LessThanOrEqualTo(3));
            // the unseelie envoy carries Cliodna's letter to the Glimmer King (owner: "Keep it. I like it")
            string envoy = qs.Single(q => (string) q["id"] == "lg_envoy").ToString();
            Assert.That(envoy, Does.Contain("Unseelie").And.Contain("Cuuldurach"));
            Assert.That(Build["keep"].Select(k => (string) k), Does.Contain("unseelie envoy"));
        }

        [Test]
        public void AinesCircle_AndTheSentinelsShared()
        {
            RepZoneDef z = RepDefs.ForZone(204);
            Assert.That(z, Is.Not.Null);
            Assert.That(z.Faction("aines_circle").Title(Rank.Legend, false), Is.EqualTo("Keeper of Lough Gur"));
            Assert.That(z.Shared, Does.Contain("sentinels_of_ceannai"));
            Assert.That(z.Quartermasters.Single().Faction, Is.EqualTo("sentinels_of_ceannai"));
            Assert.That(RepDefs.Faction("lucht_feasa").Kin, Does.Contain("aines_circle"));
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            Assert.That(quests.All(q => z.Quests.ContainsKey(q)), "every quest is someone's");
        }

        [Test]
        public void AinesComb_AtDawn_OnTheEastShore()
        {
            Assert.That(ZoneEggs.OnAinesShore(1182, 884), Is.True);
            Assert.That(ZoneEggs.OnAinesShore(1174, 978), Is.False, "not in Innis Carthaig");
            Assert.That(ZoneEggs.Dawn(6 * 3_600_000u), Is.True);
        }
    }
}
