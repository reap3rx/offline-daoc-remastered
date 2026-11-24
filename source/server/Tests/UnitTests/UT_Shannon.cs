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
    /// <summary>Shannon Estuary (the zone brief and the owner's markup, 2026-11-23): Wild, darkening toward Lough Gur, about
    /// 750 monsters, fourteen events with the Albion landing and the Eriu War-Camp siege (3 stages, the clans' recapture),
    /// 27 story quests, the Sentinels of Ceannai and Lucht an Tobair, Sinann the purple at Connla's Well.</summary>
    [TestFixture]
    public sealed class UT_Shannon
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone202_shannon_estuary.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone202_shannon_estuary.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_shannon.json"));
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
        public void ItIsWild_NearSevenHundredFifty_HarderTowardLoughGur()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("wild"));
            var count = Tally(b);
            int total = count.Values.Sum();
            Assert.That(total, Is.InRange(680, 820), "owner: many more mobs");
            Assert.That((count.GetValueOrDefault("blue") + count.GetValueOrDefault("yellow")) / (double) total, Is.GreaterThanOrEqualTo(0.6));
            Assert.That(count.GetValueOrDefault("purple"), Is.EqualTo(1), "Sinann");
            // the south (toward Lough Gur) is harder than the north
            double Hard(Func<JToken, bool> f)
            {
                var c = Tally(b, f);
                int n = c.Values.Sum();
                return n == 0 ? 0 : (c.GetValueOrDefault("orange") + c.GetValueOrDefault("red")) / (double) n;
            }
            Assert.That(Hard(s => Centre(s) is double[] c && c[1] > 1300), Is.GreaterThan(Hard(s => Centre(s) is double[] c && c[1] < 700) + 0.15));
            var clears = Build["sites"].Where(s => (string) s["kind"] == "clear").SelectMany(s => s["names"].Values<string>()).ToList();
            Assert.That(clears, Does.Contain("Abbadona").And.Contain("Kaen Kedger"), "Sinann replaces Abbadona; Kedger is the siege's");
        }

        [Test]
        public void FourteenEvents_TheLandingAndTheWarCamp()
        {
            ZoneEventsDef z = Events;
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids, Is.Unique);
            Assert.That(ids.Count, Is.EqualTo(14));
            foreach (string id in new[] { "shannon_rising_tide", "shannon_bridge_toll", "shannon_hazel_harvest", "shannon_serpent_upriver",
                         "shannon_well_wakes", AlbionLanding.ChainId })
                Assert.That(ids, Does.Contain(id));
            Assert.That(z.Chains.First(c => c.Id == "shannon_rising_tide").Time, Is.EqualTo("night"));
            ChainDef land = z.Chains.First(c => c.Id == AlbionLanding.ChainId);
            Assert.That(land.AutoFailS, Is.GreaterThan(0), "unanswered, the Albions dig in");
            Assert.That(land.Stages.First(s => s.Id == land.Start).OnFail, Is.EqualTo(AlbionLanding.BeachheadStage));
            StageDef head = land.Stages.First(s => s.Id == AlbionLanding.BeachheadStage);
            Assert.That(head.Type, Is.EqualTo("occupy"));
            Assert.That(head.OnFail, Is.EqualTo(AlbionLanding.BeachheadStage), "held until burned out");
            Assert.That(z.Chains.SelectMany(c => c.Stages).Any(s => s.Type == "boss" && s.Boss?.Name == "Arracht" && s.Path.Count > 2), "a hunt");
            HashSet<string> ev = Items("ev202_shannon"), wc = Items("wc202_war_camp");
            var old = new[] { "nu202_ant_queen_of_the_shannon_s_jewel", "nu202_tide_turned_s_mantle", "nu202_eriu_huntmaster", "nu202_queen_aoibheall" };
            foreach (ItemRewardDef i in z.Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                if (!old.Any(o => i.Id.StartsWith(o)))
                    Assert.That(ev.Contains($"{i.Id}_l30") || wc.Contains($"{i.Id}_l30"), i.Id);
        }

        [Test]
        public void TheWarCampIsAFullSiege_WithTheClansRecapture()
        {
            ZoneEventsDef z = Events;
            SiegeDef d = z.Siege;
            var chains = z.Chains.ToDictionary(c => c.Id);
            ChainDef a = chains[d.Assault];
            Assert.That(a.MinPeople, Is.EqualTo(6));
            Assert.That(a.Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "wards", "boss" }), "palisade, totems, Kedger");
            Assert.That(a.Stages[2].Boss.Name, Is.EqualTo("Kaen Kedger"));
            Assert.That(d.Raids.Count, Is.EqualTo(2));
            Assert.That(d.LastRaid, Is.Not.Null);
            Assert.That(d.Faction, Is.EqualTo("sentinels_of_ceannai"));
            Assert.That(d.BotsGoAfterM, Is.EqualTo(30));
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            foreach (string q in d.Quests.Keys)
                Assert.That(quests, Does.Contain(q));
            HashSet<string> wc = Items("wc202_war_camp");
            foreach (SiegeStockDef st in d.CampNpcs.Where(n => n.Kind is "marks" or "coin").SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(wc.Contains(st.Item) || wc.Contains(st.Item + "_l30"), st.Item);
            Assert.That(d.CampNpcs.Any(n => n.Kind == "ferry"), "a ferry back to Connla");
        }

        [Test]
        public void TwentySevenQuests_WithTheOldTwoFoldedIn()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(27));
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("false_light").And.Contain("eriu_hostage"), "old progress keeps its quest ids");
            Assert.That(ids, Does.Contain("sh_welcome_to_connla"), "the Connla start");
            Assert.That(qs.Count(q => (bool?) q["group"] == true), Is.GreaterThanOrEqualTo(3));
            foreach (JToken q in qs.Where(q => q["requires"] != null))
                Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            Assert.That(qs.Any(q => (string) q["id"] == "sh_sinann" && (bool?) q["group"] == true), "the well's finale");
        }

        [Test]
        public void TheSentinelsAndTheWell_AreKinToTheirNeighbours()
        {
            RepZoneDef z = RepDefs.ForZone(202);
            Assert.That(z, Is.Not.Null);
            Assert.That(z.Faction("sentinels_of_ceannai").Title(Rank.Legend, false), Is.EqualTo("Captain of Ceannai"));
            Assert.That(z.Faction("lucht_an_tobair").Title(Rank.Legend, false), Is.EqualTo("Fili of Connla's Well"));
            Assert.That(RepDefs.Faction("mag_mell_guard").Kin, Does.Contain("sentinels_of_ceannai"));
            Assert.That(RepDefs.Faction("lucht_feasa").Kin, Does.Contain("lucht_an_tobair"));
        }

        [Test]
        public void TheLandingsPatrols_HuntHibernians()
        {
            Assert.That(AlbionLanding.Routes.Length, Is.EqualTo(2));
            Assert.That(AlbionLanding.MaxPatrols * AlbionLanding.PatrolSize, Is.LessThanOrEqualTo(8), "a nuisance, not an army");
            Assert.That(AlbionLanding.PatrolBrain.Hunts(null), Is.False);
        }
    }
}
