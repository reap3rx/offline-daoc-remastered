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
    /// <summary>Connacht (the zone brief, 2026-11-22): Peaceful, about a thousand monsters, eight events, 25 story quests
    /// and an easter egg, the Fianna of Druim Ligen and the Order of the Rowan, and the Wicker Fields - a smaller siege on
    /// Dergan Island's system. Also the checks every rebuilt zone should pass (every siege, every story file).</summary>
    [TestFixture]
    public sealed class UT_Connacht
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static IEnumerable<string> Resources(string prefix) =>
            Asm.GetManifestResourceNames().Where(n => n.StartsWith(prefix) && n.EndsWith(".json")).OrderBy(n => n);

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone207_connacht.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone207_connacht.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_connacht.json"));
        static HashSet<string> Items(string file) => JToken.Parse(Text("StoryItems." + file + ".json")).Select(r => (string) r["Id_nb"]).ToHashSet();

        static readonly string[] TierNames = { "grey", "green", "blue", "yellow", "orange", "red", "purple" };

        // ------------------------------------------------------------------ the zone build

        [Test]
        public void ItIsPeaceful_AboutAThousandMonsters_MostlyGreensAndBlues()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("peaceful"), "owner: Peaceful - the law of Ardee, Druim Ligen and the gate");
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
            foreach (JToken s in b["sites"])
                foreach (JProperty sp in (s["spawn"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(sp.Name, (int) sp.Value);
            int total = count.Values.Sum();
            Assert.That(total, Is.InRange(850, 1100), "owner: closer to 1000");
            double gb = (count.GetValueOrDefault("green") + count.GetValueOrDefault("blue")) / (double) total;
            double hot = (count.GetValueOrDefault("orange") + count.GetValueOrDefault("red") + count.GetValueOrDefault("purple")) / (double) total;
            Assert.That(gb, Is.GreaterThanOrEqualTo(0.6), "Peaceful: mostly greens and blues");
            Assert.That(hot, Is.LessThan(0.08), "the danger is in a few places (the gate, the fields), not everywhere");
        }

        [Test]
        public void TheOldVoicesAndWitheLeaveTheFields_AndWitheWalksTheNorthBank()
        {
            JToken b = Build;
            var clears = b["sites"].Where(s => (string) s["kind"] == "clear").ToList();
            Assert.That(clears.Any(s => s["names"].Values<string>().Contains("Voice of the Azure")));
            Assert.That(clears.Any(s => s["names"].Values<string>().Contains("Withe")));
            Assert.That(b["keep"].Values<string>(), Does.Not.Contain("Voice of the Azure"), "the Voice is the siege's boss now");
            Assert.That(b["sites"].Any(s => s["spawn"]?["Withe"] != null));
            Assert.That(b["sites"].Any(s => s["spawn"]?["The Dullahan"] != null && (string) s["time"] == "night"), "the easter egg rides at night");
        }

        // ------------------------------------------------------------------ events

        [Test]
        public void EightEventsAndTheSiegesTwo()
        {
            ZoneEventsDef z = Events;
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids, Is.Unique);
            foreach (string id in new[] { "connacht_wickermen", "connacht_streaming_wisps", "connacht_wind_ghouls", "connacht_anger_sprites",
                         "connacht_gate_stirs", "connacht_fools_revel", "connacht_river_siabra", "connacht_fishing_bears" })
                Assert.That(ids, Does.Contain(id));
            Assert.That(z.Chains.First(c => c.Id == "connacht_gate_stirs").Time, Is.EqualTo("night"));
            Assert.That(z.Chains.First(c => c.Id == "connacht_fools_revel").Time, Is.EqualTo("night"));
            Assert.That(z.Chains.First(c => c.Id == "connacht_fishing_bears").Stages[0].Type, Is.EqualTo("gather"));
            Assert.That(z.Chains.First(c => c.Id == "connacht_fools_revel").Stages[0].Type, Is.EqualTo("intercept"));
            string all = Text("DynamicEvents.zone207_connacht.json");
            Assert.That(all, Does.Not.Contain("Grainne"), "the woodward is Muireann (Silvermine has a Grainne)");
            Assert.That(all, Does.Contain("Muireann the Woodward"));
        }

        [Test]
        public void TheNewEventsRewardsExist()
        {
            HashSet<string> ev = Items("ev207_connacht"), wf = Items("wf207_wicker_fields");
            foreach (ChainDef c in Events.Chains)
                foreach (StageDef s in c.Stages)
                    foreach (ItemRewardDef i in s.Reward?.Items ?? new List<ItemRewardDef>())
                    {
                        if (i.Id.StartsWith("nu207_") && !ev.Contains(i.Id))
                            continue;   // (the four old events' rewards are in the world's database already)
                        Assert.That(ev.Contains(i.Id) || wf.Contains(i.Id), i.Id);
                        for (int l = 10; l <= 50; l += 5)
                            Assert.That(ev.Contains($"{i.Id}_l{l}") || wf.Contains($"{i.Id}_l{l}"), $"{i.Id}_l{l}");
                    }
            Assert.That(ev, Does.Contain("nu207_morcant_s_gate_ember"));
        }

        // ------------------------------------------------------------------ the Wicker Fields

        [Test]
        public void TheWickerFieldsAreASmallerSiege()
        {
            ZoneEventsDef z = Events;
            SiegeDef d = z.Siege;
            Assert.That(d, Is.Not.Null);
            var chains = z.Chains.ToDictionary(c => c.Id);
            ChainDef a = chains[d.Assault];
            Assert.That(a.MinPeople, Is.EqualTo(4), "four or more, bots counting (the brief)");
            Assert.That(a.Stages.Select(s => s.Type), Is.EqualTo(new[] { "wards", "boss" }), "break the circles, then the Voice");
            Assert.That(d.Raids, Is.Empty, "one kind of raid");
            Assert.That(chains[d.LastRaid].AutoFailS, Is.GreaterThan(0), "ignored, the fields burn");
            Assert.That(d.HoldH, Is.EqualTo(2), "two hours after it's taken");
            Assert.That(d.BotsGoAfterM, Is.EqualTo(30), "bots go alone after 30 minutes");
            Assert.That(d.Faction, Is.EqualTo("order_of_the_rowan"));
            Assert.That(d.CarryText, Does.Not.Contain("roane"), "no seals in the Wicker Fields");
            var s = new SiegeState();
            s.AddResolve(100);
            s.Captured(DateTime.UtcNow, d);
            Assert.That(s.NextRaid(d), Is.EqualTo(d.LastRaid));
            s.RaidHeld(DateTime.UtcNow, d);
            Assert.That(s.NextRaid(d), Is.EqualTo(d.LastRaid), "the same raid again");
            Assert.That(s.RaidToughness, Is.GreaterThan(1), "a little harder each time");
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            foreach (string q in d.Quests.Keys)
                Assert.That(quests, Does.Contain(q));
            Assert.That(d.Quests.Values.Sum() + d.Feeds.Values.Sum(), Is.GreaterThanOrEqualTo(100), "the arcs and the events fill it");
        }

        [Test]
        public void TheCampsCloakHasTheTree_AndItsStockExistsAtEveryLevel()
        {
            JToken rows = JToken.Parse(Text("StoryItems.wf207_wicker_fields.json"));
            var ids = rows.ToDictionary(r => (string) r["Id_nb"]);
            foreach (SiegeNpcDef n in Events.Siege.CampNpcs.Where(n => n.Kind is "marks" or "coin"))
                foreach (SiegeStockDef st in n.Stock.Where(x => !x.Item.StartsWith("tw_")))
                {
                    Assert.That(ids.ContainsKey(st.Item), st.Item);
                    if (n.Kind == "marks")
                        for (int l = 10; l <= 50; l += 5)
                            Assert.That(ids.ContainsKey($"{st.Item}_l{l}"), $"{st.Item}_l{l}");
                }
            int emblem = (int) ids["wf207_cloak_of_the_freed_fields"]["Emblem"];
            Assert.That(emblem >> 9, Is.EqualTo(81), "the Hibernian Tree (h_emblem_001)");
            Assert.That(emblem, Is.LessThan(65536));
        }

        // ------------------------------------------------------------------ every siege (generic)

        static IEnumerable<ZoneEventsDef> Sieges() => Resources("DynamicEvents.")
            .Select(n => JsonConvert.DeserializeObject<ZoneEventsDef>(Text(n))).Where(z => z.Siege != null);

        [Test]
        public void EverySiegesChainsAreItsOwn_AndItsPlacesMakeSense()
        {
            foreach (ZoneEventsDef z in Sieges())
            {
                SiegeDef d = z.Siege;
                var chains = z.Chains.ToDictionary(c => c.Id);
                foreach (string id in d.Raids.Append(d.LastRaid).Append(d.Assault))
                {
                    Assert.That(chains.ContainsKey(id), z.Name + ": " + id);
                    Assert.That(chains[id].Manual, Is.True, id);
                }
                Assert.That(chains[d.Assault].Giver, Is.Not.Null, d.Name);
                foreach (string id in d.Feeds.Keys.Concat(d.EnemyFeeds.Keys))
                    Assert.That(chains.ContainsKey(id), d.Name + " feed " + id);
                Assert.That(d.BotsGoAfterM, Is.InRange(15, d.HoldH * 60 / 2), d.Name);
                bool On(double[] p) => Math.Sqrt(Math.Pow(p[0] - d.Area[0], 2) + Math.Pow(p[1] - d.Area[1], 2)) <= d.Area[2];
                Assert.That(On(d.Staging), Is.False, d.Name + ": the war band gathers outside");
                Assert.That(On(d.Landing), Is.True, d.Name);
                foreach (SiegeNpcDef n in d.CampNpcs.Where(n => n.Kind != "ferry").Concat(d.Holdouts))
                    Assert.That(On(n.Pos), d.Name + ": " + n.Name);
                var sites = JToken.Parse(Text($"ZoneBuilds.{Resources("ZoneBuilds.").Select(r => r[11..^5]).First(r => r.StartsWith($"zone{z.Zone:000}_"))}.json"))["sites"]
                    .Select(s => (string) s["id"]).ToHashSet();
                foreach (string s in d.Sites)
                    Assert.That(sites, Does.Contain(s), d.Name);
                RepZoneDef rz = RepDefs.ForZone(z.Zone);
                Assert.That(rz?.Faction(d.Faction), Is.Not.Null, d.Name + "'s faction");
            }
        }

        // ------------------------------------------------------------------ the story

        [Test]
        public void TwentyFiveQuestsInSixArcs_PlusTheSalmon_WithTheOldTwoFoldedIn()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(26));
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("rowdies").And.Contain("wickerman"), "old progress keeps its quest ids");
            Assert.That(ids, Does.Contain("cn_salmon_of_knowledge"), "the easter egg");
            Assert.That(qs.Count(q => (bool?) q["group"] == true), Is.GreaterThanOrEqualTo(6), "the arcs' finales are group quests");
            foreach (JToken q in qs)
                if (q["requires"] != null)
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            // every place in the zone
            foreach (JToken st in qs.SelectMany(q => q["steps"]))
                if (st["at"] is JArray at)
                {
                    Assert.That((double) at[0], Is.InRange(0, 1638));
                    Assert.That((double) at[1], Is.InRange(0, 1638));
                }
        }

        [Test]
        public void TheStoryHuntsTheZonesOwnMonsters()
        {
            // a kill step with a "target" counts the zone build's monsters: each must be one it places, or one it keeps
            foreach (string res in Resources("StoryQuests."))
            {
                JToken f = JToken.Parse(Text(res));
                foreach (JToken q in f["quests"] ?? new JArray())
                    foreach (JToken st in q["steps"])
                    {
                        if ((string) st["type"] != "kill" || st["target"] == null)
                            continue;
                        int zone = (int) st["zone"];
                        string build = Resources("ZoneBuilds.").FirstOrDefault(r => r.StartsWith($"ZoneBuilds.zone{zone:000}_"));
                        if (build == null || zone is not (207 or 201))
                            continue;                     // (Lough Derg's are checked by its own tests)
                        JToken b = JToken.Parse(Text(build));
                        var names = ((JObject) b["members"]).Properties()
                            .SelectMany(p => new[] { p.Name, (string) p.Value["name"] ?? p.Name })
                            .Concat(((JObject) b["tiers"]).Properties().Select(p => p.Name)).ToHashSet(StringComparer.OrdinalIgnoreCase);
                        Assert.That(names, Does.Contain((string) st["target"]), $"{q["id"]}: {st["target"]}");
                    }
            }
        }

        [Test]
        public void StoryPeopleAndQuestsHaveOneIdAcrossEveryFile()
        {
            // ids are global (StoryQuestManager): the same id in two files and one of them silently loses its person -
            // Connacht's Ronan and Lough Derg's Ronan of the Roane did, before Connacht's became cn_ronan
            var npcs = new Dictionary<string, string>();
            var quests = new Dictionary<string, string>();
            foreach (string res in Resources("StoryQuests."))
            {
                JToken f = JToken.Parse(Text(res));
                foreach (JToken n in f["npcs"] ?? new JArray())
                {
                    string id = (string) n["id"];
                    Assert.That(npcs.TryAdd(id, res), Is.True, $"person '{id}' in {res} and {npcs.GetValueOrDefault(id)}");
                }
                foreach (JToken q in f["quests"] ?? new JArray())
                {
                    string id = (string) q["id"];
                    Assert.That(quests.TryAdd(id, res), Is.True, $"quest '{id}' in {res} and {quests.GetValueOrDefault(id)}");
                }
            }
        }

        [Test]
        public void RebuiltZonesSendPlainLetters()
        {
            // live check 22 Nov: "Bébhinn" came out as "BAcbhinn" in chat - names, titles and words the server sends keep to
            // plain letters (the zone files of the rebuilt zones, their stories and their factions)
            foreach (string res in new[] { "DynamicEvents.zone207_connacht.json", "ZoneBuilds.zone207_connacht.json", "StoryQuests.hib_connacht.json",
                         "Reputation.rep207_connacht.json", "DynamicEvents.zone201_silvermine_mountains.json", "ZoneBuilds.zone201_silvermine_mountains.json",
                         "StoryQuests.hib_silvermine.json", "Reputation.rep201_silvermine.json" })
            {
                string t = Text(res);
                int i = t.IndexOf(t.FirstOrDefault(c => c > 127));
                Assert.That(t.All(c => c < 128), Is.True, res + ": " + (i >= 0 ? t.Substring(Math.Max(0, i - 30), 40) : ""));
            }
        }

        // ------------------------------------------------------------------ reputation

        [Test]
        public void TheFiannaAndTheRowan_KinToLoughDergs()
        {
            RepZoneDef z = RepDefs.ForZone(207);
            Assert.That(z, Is.Not.Null);
            RepFactionDef fi = z.Faction("fianna_druim_ligen"), ro = z.Faction("order_of_the_rowan");
            Assert.That(fi.Title(Rank.Trusted, false), Is.EqualTo("Friend of the Fian"));
            Assert.That(fi.Title(Rank.Legend, true), Is.EqualTo("Rigfennid"));
            Assert.That(ro.Title(Rank.Legend, true), Is.EqualTo("Bandrui"));
            Assert.That(ro.Title(Rank.Legend, false), Is.EqualTo("Drui"));
            Assert.That(fi.Kin, Does.Contain("mag_mell_guard"));
            Assert.That(ro.Kin, Is.EquivalentTo(new[] { "lucht_feasa", "muintir_etaine", "lucht_an_tobair", "seers_of_moher", "aines_circle", "keeners_of_cullen" }));
            Assert.That(RepDefs.Faction("mag_mell_guard").Kin, Does.Contain("fianna_druim_ligen"), "kin both ways");
            Assert.That(RepDefs.Faction("lucht_feasa").Kin, Does.Contain("order_of_the_rowan"));
            foreach (string k in RepDefs.AllFactions.SelectMany(f => f.Kin))
                Assert.That(RepDefs.Faction(k), Is.Not.Null, k);
            Assert.That(ReputationService.KillFaction(z, "azure idolater").Key, Is.EqualTo("order_of_the_rowan"));
            Assert.That(ReputationService.KillFaction(z, "manes demon").Key, Is.EqualTo("fianna_druim_ligen"));
            Assert.That(ReputationService.KillFaction(z, "amadan touched").Key, Is.EqualTo("order_of_the_rowan"));
            Assert.That(ReputationService.KillFaction(z, "siabra raider").Key, Is.EqualTo("fianna_druim_ligen"));
        }

        [Test]
        public void EveryConnachtQuestAndEventCountsForAFaction_AndTheQuartermastersStockExists()
        {
            RepZoneDef z = RepDefs.ForZone(207);
            foreach (JToken q in Stories["quests"])
                Assert.That(z.Faction(z.Quests.GetValueOrDefault((string) q["id"])), Is.Not.Null, (string) q["id"]);
            foreach (ChainDef c in Events.Chains)
                Assert.That(z.Faction(z.Events.GetValueOrDefault(c.Id)), Is.Not.Null, c.Id);
            HashSet<string> ids = Items("rep207_connacht");
            foreach (RepStockDef s in z.Factions.Where(f => f.ZoneDef == z).SelectMany(f => f.Quartermaster.Stock))
            {
                Assert.That(ids, Does.Contain(s.Item), s.Item);
                for (int l = 10; l <= 50; l += 5)
                    Assert.That(ids, Does.Contain($"{s.Item}_l{l}"));
            }
            var people = Stories["npcs"].Select(n => (string) n["id"]).ToHashSet();
            foreach (RepFactionDef f in z.Factions)
            {
                Assert.That(people, Does.Contain(f.Speaker), f.Key);
                Assert.That(people, Does.Contain(f.Quartermaster.Anchor), f.Key);
            }
        }

        [Test]
        public void EachSidesStoriesReachAboutTrusted()
        {
            RepZoneDef z = RepDefs.ForZone(207);
            var group = Stories["quests"].ToDictionary(q => (string) q["id"], q => (bool?) q["group"] ?? false);
            foreach (RepFactionDef f in z.Factions.Where(f => f.ZoneDef == z))
            {
                double pts = z.Quests.Where(kv => !kv.Key.Contains(':') && kv.Value == f.Key)
                    .Sum(kv => group[kv.Key] ? ReputationService.GroupQuestPoints : ReputationService.QuestPoints) * 0.8;   // Peaceful
                Assert.That(ReputationService.RankOf(pts), Is.EqualTo(Rank.Trusted), f.Key);
            }
        }
    }
}
