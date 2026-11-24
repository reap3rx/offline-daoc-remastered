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
    /// <summary>Silvermine Mountains (the zone brief, 2026-11-22): Wild, near 800 monsters with a few greens round Howth,
    /// eight events, 24 story quests, the Mine-Wardens of Howth and the Order of the Rowan (shared with Connacht), the
    /// Silver Mine siege, and the old blademaster on the lake's island.</summary>
    [TestFixture]
    public sealed class UT_Silvermine
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone201_silvermine_mountains.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone201_silvermine_mountains.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_silvermine.json"));
        static HashSet<string> Items(string file) => JToken.Parse(Text("StoryItems." + file + ".json")).Select(r => (string) r["Id_nb"]).ToHashSet();

        // ------------------------------------------------------------------ the zone build

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
        public void ItIsWild_NearEightHundred_MostlyBluesAndYellows_TheGreensByHowth()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("wild"));
            var count = Tally(b);
            int total = count.Values.Sum();
            Assert.That(total, Is.InRange(720, 880), "owner: keep near 800");
            double by = (count.GetValueOrDefault("blue") + count.GetValueOrDefault("yellow")) / (double) total;
            Assert.That(by, Is.GreaterThanOrEqualTo(0.65), "Wild: mostly blues and yellows");
            Assert.That(count.GetValueOrDefault("green") / (double) total, Is.LessThan(0.2), "few greens");
            // the greens are round Howth (a starting zone to come)
            var nearHowth = Tally(b, s => Centre(s) is double[] c && Math.Sqrt(Math.Pow(c[0] - 562, 2) + Math.Pow(c[1] - 1083, 2)) < 300);
            Assert.That(nearHowth.GetValueOrDefault("green"), Is.GreaterThanOrEqualTo(count.GetValueOrDefault("green") * 0.6), "owner: a few greens near Howth");
        }

        [Test]
        public void NothingOfTheBuildIsOnTheIsland()
        {
            foreach (JToken s in Build["sites"])
            {
                if (s["area"] is JArray a)
                    Assert.That(905 * 40 >= (int) a[0] && 905 * 40 <= (int) a[2] && 682 * 40 >= (int) a[1] && 682 * 40 <= (int) a[3], Is.False, (string) s["id"]);
                if (Centre(s) is double[] c)
                    Assert.That(Math.Sqrt(Math.Pow(c[0] - 905, 2) + Math.Pow(c[1] - 682, 2)), Is.GreaterThan(80), (string) s["id"]);
            }
        }

        // ------------------------------------------------------------------ events and the Silver Mine

        [Test]
        public void EightEventsAndTheSiegesTwo()
        {
            ZoneEventsDef z = Events;
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids, Is.Unique);
            foreach (string id in new[] { "silvermine_mountains_sheevra_warband", "silvermine_mountains_gray_spectres", "silvermine_mountains_spraggon_warren",
                         "silvermine_mountains_walking_rocks", "silvermine_stones_walk", "silvermine_moon_silver_convoy", "silvermine_badger_drive", "silvermine_deep_wind" })
                Assert.That(ids, Does.Contain(id));
            Assert.That(z.Chains.First(c => c.Id == "silvermine_stones_walk").Time, Is.EqualTo("night"));
            Assert.That(z.Chains.First(c => c.Id == "silvermine_deep_wind").Time, Is.EqualTo("night"));
            Assert.That(z.Chains.First(c => c.Id == "silvermine_moon_silver_convoy").Stages[0].Type, Is.EqualTo("intercept"));
            var spectres = z.Chains.First(c => c.Id == "silvermine_mountains_gray_spectres");
            Assert.That(spectres.Stages[1].Center[0], Is.GreaterThan(1300), "the spectres are at the Fallen Camp now, in the south-east");
            HashSet<string> ev = Items("ev201_silvermine"), mn = Items("mn201_silver_mine");
            var old = new[] { "nu201_dubhan", "nu201_gray_lady", "nu201_spraggon_chief_nuadh", "nu201_grinding_stone" };   // (in the world's database)
            foreach (ItemRewardDef i in z.Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                if (!old.Any(o => i.Id.StartsWith(o)))
                    Assert.That(ev.Contains($"{i.Id}_l30") || mn.Contains($"{i.Id}_l30"), i.Id);
        }

        [Test]
        public void TheSilverMineIsASmallerSiege()
        {
            ZoneEventsDef z = Events;
            SiegeDef d = z.Siege;
            var chains = z.Chains.ToDictionary(c => c.Id);
            ChainDef a = chains[d.Assault];
            Assert.That(a.MinPeople, Is.EqualTo(4));
            Assert.That(a.Stages.Select(s => s.Type), Is.EqualTo(new[] { "cull", "boss" }), "storm the huts, then Dergal and Camlin");
            Assert.That(a.Stages[1].Adds.Mobs.Any(m => m.Name == "Overseer Camlin"), "Camlin fights beside him");
            Assert.That(d.Raids, Is.Empty);
            Assert.That(d.HoldH, Is.EqualTo(2));
            Assert.That(d.BotsGoAfterM, Is.EqualTo(30));
            Assert.That(d.Faction, Is.EqualTo("mine_wardens"));
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            foreach (string q in d.Quests.Keys)
                Assert.That(quests, Does.Contain(q));
            Assert.That(d.Quests.Values.Sum() + d.Feeds.Values.Sum(), Is.GreaterThanOrEqualTo(100));
            // Dergal and Camlin leave their huts for good (the assault brings them), so the camp is never theirs
            var clears = Build["sites"].Where(s => (string) s["kind"] == "clear").SelectMany(s => s["names"].Values<string>()).ToList();
            Assert.That(clears, Does.Contain("Chieftain Dergal").And.Contain("Overseer Camlin"));
            var rows = JToken.Parse(Text("StoryItems.mn201_silver_mine.json")).ToDictionary(r => (string) r["Id_nb"]);
            foreach (SiegeStockDef st in d.CampNpcs.Where(n => n.Kind is "marks" or "coin").SelectMany(n => n.Stock).Where(x => !x.Item.StartsWith("tw_")))
                Assert.That(rows.ContainsKey(st.Item), st.Item);
            Assert.That((int) rows["mn201_cloak_of_the_reopened_mine"]["Emblem"] >> 9, Is.EqualTo(86), "a Hibernian knot");
        }

        // ------------------------------------------------------------------ the story

        [Test]
        public void TwentyThreeQuestsInSixArcs_WithTheOldTwoFoldedIn()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(24));      // (23, and The Road to Howth for an Ardagh start)
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("walking_stones").And.Contain("sheevra_mine"), "old progress keeps its quest ids");
            Assert.That(qs.Count(q => (bool?) q["group"] == true), Is.GreaterThanOrEqualTo(5));
            foreach (JToken q in qs.Where(q => q["requires"] != null))
                Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            Assert.That(Text("StoryQuests.hib_silvermine.json"), Does.Contain("Wicker Fields"), "the trail leads to Connacht");
        }

        // ------------------------------------------------------------------ reputation

        [Test]
        public void TheMineWardens_AndTheRowanSharedWithConnacht()
        {
            RepZoneDef z = RepDefs.ForZone(201), cn = RepDefs.ForZone(207);
            RepFactionDef mw = z.Faction("mine_wardens");
            Assert.That(mw.Title(Rank.Trusted, false), Is.EqualTo("Shaftwarden"));
            Assert.That(mw.Title(Rank.Honoured, false), Is.EqualTo("Silverhand"));
            Assert.That(mw.Title(Rank.Legend, true), Is.EqualTo("Airgetlam"));
            Assert.That(mw.Kin, Is.EquivalentTo(new[] { "mag_mell_guard", "fianna_druim_ligen", "rangers_druim_cain", "sentinels_of_ceannai", "watch_of_moher", "host_of_lug", "clann_of_alainn_bin" }), "the realm's soldiers");
            Assert.That(RepDefs.Faction("mag_mell_guard").Kin, Does.Contain("mine_wardens"));
            Assert.That(RepDefs.Faction("fianna_druim_ligen").Kin, Does.Contain("mine_wardens"));
            Assert.That(z.Faction("order_of_the_rowan"), Is.SameAs(cn.Faction("order_of_the_rowan")), "one Rowan, one standing");
            Assert.That(z.Faction("order_of_the_rowan").ZoneDef, Is.SameAs(cn));
            Assert.That(RepDefs.AllFactions.Count(f => f.Key == "order_of_the_rowan"), Is.EqualTo(1), "counted once for realm reputation");
            var wanted = ReputationQuartermaster.Wanted().ToList();
            Assert.That(wanted.Count(w => w.F.Key == "order_of_the_rowan"), Is.EqualTo(2), "Sadhbh in Ardee and her cousin at the ranger's post");
            Assert.That(wanted.Select(w => w.Key), Is.Unique);
            var people = Stories["npcs"].Select(n => (string) n["id"]).ToHashSet();
            Assert.That(people, Does.Contain(z.Quartermasters.Single().Anchor));
            Assert.That(people, Does.Contain(mw.Speaker));
            foreach (JToken q in Stories["quests"])
                Assert.That(z.Faction(z.Quests.GetValueOrDefault((string) q["id"])), Is.Not.Null, (string) q["id"]);
            foreach (ChainDef c in Events.Chains)
                Assert.That(z.Faction(z.Events.GetValueOrDefault(c.Id)), Is.Not.Null, c.Id);
            Assert.That(ReputationService.KillFaction(z, "sheevra swordsman").Key, Is.EqualTo("mine_wardens"));
            Assert.That(ReputationService.KillFaction(z, "gray spectre").Key, Is.EqualTo("order_of_the_rowan"));
            Assert.That(ReputationService.KillFaction(z, "rogue druid").Key, Is.EqualTo("order_of_the_rowan"));
            HashSet<string> ids = Items("rep201_silvermine");
            foreach (RepStockDef s in mw.Quartermaster.Stock)
                Assert.That(ids, Does.Contain($"{s.Item}_l40"), s.Item);
        }

        [Test]
        public void EachSidesStoriesHereReachAboutTrusted()
        {
            RepZoneDef z = RepDefs.ForZone(201);
            var group = Stories["quests"].ToDictionary(q => (string) q["id"], q => (bool?) q["group"] ?? false);
            foreach (string key in new[] { "mine_wardens", "order_of_the_rowan" })
            {
                double pts = z.Quests.Where(kv => !kv.Key.Contains(':') && kv.Value == key)
                    .Sum(kv => group[kv.Key] ? ReputationService.GroupQuestPoints : ReputationService.QuestPoints);   // Wild: 1x
                Assert.That(ReputationService.RankOf(pts), Is.EqualTo(Rank.Trusted), key);
            }
        }

        // ------------------------------------------------------------------ the old blademaster

        [Test]
        public void TheOldBlademasterSitsOnTheIsland()
        {
            Assert.That(OldBlademaster.X0, Is.EqualTo(319488 + 905 * 40), "Silvermine's offset, 905 m east");
            Assert.That(OldBlademaster.Y0, Is.EqualTo(548864 + 682 * 40), "682 m south: the island in the lake");
        }

        [Test]
        public void HeTalksToEveryone_ButDuelsOnlyALevelFiftyBlademaster()
        {
            string Accept(string s) => s.Contains($"[{OldBlademaster.Accept}]") ? "offer" : "remark";
            for (int roll = 0; roll < 12; roll++)
            {
                Assert.That(Accept(OldBlademaster.Remark(false, 50, false, roll)), Is.EqualTo("remark"));
                Assert.That(Accept(OldBlademaster.Remark(true, 49, false, roll)), Is.EqualTo("remark"));
            }
            Assert.That(Accept(OldBlademaster.Remark(true, 50, false, 0)), Is.EqualTo("offer"));
            Assert.That(Accept(OldBlademaster.Remark(true, 50, true, 0)), Is.EqualTo("offer"), "again, for the joy of it");
        }

        [TestCase(50, 30, 10, eObjectType.Blades)]
        [TestCase(20, 50, 10, eObjectType.Blunt)]
        [TestCase(20, 10, 50, eObjectType.Piercing)]
        [TestCase(40, 40, 40, eObjectType.Blades)]
        [TestCase(1, 44, 44, eObjectType.Blunt)]
        public void TheBladesMatchTheirBestWeaponLine(int blades, int blunt, int piercing, eObjectType expected)
        {
            var spec = new Dictionary<string, int> { ["Blades"] = blades, ["Blunt"] = blunt, ["Piercing"] = piercing };
            Assert.That(OldBlademaster.WeaponFor(k => spec[k]), Is.EqualTo(expected));
        }
    }
}
