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
    /// <summary>The Sheeroe Hills (the zone brief and the owner's answers, 2026-11-24): Elite, nothing below orange; the Southern
    /// Muster's campaign pushing into the hills - the Marshal at the Healers' Camp (45+), four checkpoints each held 30 minutes,
    /// the Glimmer's counter-attacks, the raid on Maldahar the Glimmer Prince; won, four hours of the Muster's hills and
    /// Cuuldurach's ring open (sealed otherwise); Ailill's Azure host for the dragon; 14 story quests; the Southern Muster.</summary>
    [TestFixture]
    public sealed class UT_Sheeroe
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone216_sheeroe_hills.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone216_sheeroe_hills.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_sheeroe.json"));
        static HashSet<string> Items(string file) => JToken.Parse(Text("StoryItems." + file + ".json")).Select(r => (string) r["Id_nb"]).ToHashSet();

        [Test]
        public void TheGlimmersOwnCountry_NothingBelowOrange()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("elite"));
            var members = (JObject) b["members"];
            foreach (JProperty m in members.Properties())
                Assert.That((string) m.Value["tier"], Is.AnyOf("orange", "red", "purple"), m.Name);
            int total = 0;
            void Add(string member, int n)
            {
                JToken m = members[member];
                Assert.That(m, Is.Not.Null, member);
                total += n;
                foreach (JProperty g in (m["guards"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(g.Name, n * (int) g.Value);
            }
            foreach (JToken s in b["sites"])
                foreach (JProperty sp in (s["spawn"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(sp.Name, (int) sp.Value);
            Assert.That(total, Is.InRange(330, 450), "about 420, from 565");
            foreach (string lord in new[] { "Glimmer Saumer", "Glimmer Venlar", "Glimmer Kelegur", "Glimmer Zeit", "Glimmer Arios",
                         "Glimmer Zanllvi", "Glimmer Orist", "Glimmer Xaquira", "Glimmer Meldun", "Glimmer Mianed" })
                Assert.That((string) b["tiers"][lord], Is.EqualTo("purple"), lord);
            var ids = b["sites"].Select(s => (string) s["id"]).ToList();
            foreach (string[] held in MusterCampaign.HeldSites.Skip(1))
                foreach (string id in held)
                    Assert.That(ids, Does.Contain(id), "the campaign sweeps it");
            Assert.That(ids.Count(i => i.StartsWith(MusterCampaign.PocketPrefix)), Is.InRange(1, 3), "the Glimmer's victims stay after the win");
            var clears = b["sites"].Where(s => (string) s["kind"] == "clear").SelectMany(s => s["names"].Values<string>()).ToList();
            Assert.That(clears, Does.Contain("Maldahar the Glimmer Prince"), "he comes only as the campaign's raid");
        }

        [Test]
        public void TheMustersBattles_PushIntoTheHills()
        {
            ZoneEventsDef z = Events;
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids, Is.Unique);
            Assert.That(ids.Count, Is.EqualTo(11), "nine of the Muster's, and the two old side fights");
            Assert.That(ids, Does.Not.Contain("sheeroe_hills_azure_crusade"), "the Grand Inquisitor is the Azure March's boss now");
            for (int n = 0; n <= MusterCampaign.Checkpoints; n++)
                Assert.That(ids, Does.Contain(MusterCampaign.NextAssault(n)));
            for (int n = 1; n <= MusterCampaign.Checkpoints; n++)
            {
                Assert.That(ids, Does.Contain(MusterCampaign.CounterFor(n)));
                ChainDef a = z.Chains.First(c => c.Id == MusterCampaign.NextAssault(n - 1));
                Assert.That(a.Manual, Is.True);
                Assert.That(a.Giver, Is.Not.Null, "a captain of the Muster leads it");
                Assert.That(a.Stages.Last().Type, Is.EqualTo("boss"), "a power check");
                ChainDef k = z.Chains.First(c => c.Id == MusterCampaign.CounterFor(n));
                Assert.That(k.Stages[0].Type, Is.EqualTo("defend"));
                Assert.That(k.Stages[0].Protect.HealthMult, Is.GreaterThanOrEqualTo(10), "the Muster holds a while without help");
            }
            int Kill(int n) => z.Chains.First(c => c.Id == MusterCampaign.NextAssault(n - 1)).Stages[0].Kill;
            Assert.That(Kill(1) < Kill(2) && Kill(2) < Kill(3) && Kill(3) < Kill(4), "harder each time");
            ChainDef march = z.Chains.First(c => c.Id == "sh_cp2_assault");
            Assert.That(march.Stages.Last().Boss.Name, Is.EqualTo("The Azure Grand Inquisitor"));
            Assert.That(march.Stages.Last().Success, Does.Contain("Ailill"), "the young captain's turn");
            ChainDef raid = z.Chains.First(c => c.Id == MusterCampaign.RaidChain);
            Assert.That(raid.MinPeople, Is.GreaterThanOrEqualTo(10), "two groups");
            Assert.That(raid.Stages[0].Boss.Name, Is.EqualTo("Maldahar the Glimmer Prince"));
            HashSet<string> sh = Items("sh216_sheeroe_hills");
            foreach (ItemRewardDef i in z.Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>())
                         .Where(i => !i.Id.StartsWith("nu216_")))       // (the old side fights keep their own)
                Assert.That(sh.Contains($"{i.Id}_l30") || sh.Contains(i.Id), i.Id);
            foreach (SiegeStockDef st in MusterCampaign.HollowCamp().SelectMany(n => n.Stock ?? new List<SiegeStockDef>()))
                Assert.That(sh.Contains($"{st.Item}_l30") || sh.Contains(st.Item), st.Item);
        }

        [Test]
        public void TheCampaign_StepsForwardAndFallsBack()
        {
            var s = new MusterCampaign.State();
            DateTime t = new DateTime(2026, 11, 24, 12, 0, 0, DateTimeKind.Utc);
            Assert.That(MusterCampaign.CanStart(44, s, t), Is.Not.Null, "45 and up");
            Assert.That(MusterCampaign.CanStart(45, s, t), Is.Null);
            s = MusterCampaign.Begin(s, t, "Nighttest");
            Assert.That(s.Phase, Is.EqualTo(MusterCampaign.Phase.Holding));
            Assert.That(s.Held, Is.EqualTo(0), "the march begins at the camp");
            Assert.That(s.DeadlineUtc, Is.EqualTo(t + TimeSpan.FromMinutes(30)));
            Assert.That(MusterCampaign.CanStart(50, s, t), Is.Not.Null, "already marching");
            Assert.That(MusterCampaign.NextAssault(0), Is.EqualTo("sh_cp1_assault"));
            Assert.That(MusterCampaign.CounterFor(0), Is.Null, "nothing comes for the camp: the march just ends");
            MusterCampaign.Won(s, 1, t);
            MusterCampaign.Won(s, 2, t);
            MusterCampaign.CounterHeld(s, t.AddMinutes(40));
            Assert.That(s.DeadlineUtc, Is.EqualTo(t.AddMinutes(70)), "beaten off: the clock starts again");
            Assert.That(MusterCampaign.CounterLost(s, t), Is.True);
            Assert.That(s.Held, Is.EqualTo(1), "a step back");
            Assert.That(MusterCampaign.CounterLost(s, t), Is.False, "the upland lost: pushed out of the hills");
            MusterCampaign.Over(s, t, true);
            Assert.That(MusterCampaign.CanStart(50, s, t), Is.Not.Null, "the Muster rests a while");
            Assert.That(MusterCampaign.CanStart(50, s, t + MusterCampaign.Rest), Is.Null);
            Assert.That(MusterCampaign.RingOpen(s), Is.False, "the King's ring sealed");
            MusterCampaign.Victory(s, t);
            Assert.That(MusterCampaign.RingOpen(s), Is.True, "the raid opens with the hills won");
            Assert.That(s.VictoryUntilUtc - t, Is.EqualTo(TimeSpan.FromHours(4)));
            Assert.That(MusterCampaign.AssaultIndex("sh_cp3_assault"), Is.EqualTo(3));
            Assert.That(MusterCampaign.AssaultIndex(MusterCampaign.RaidChain), Is.EqualTo(5));
            Assert.That(MusterCampaign.CounterIndex("sh_cp2_counter"), Is.EqualTo(2));
            Assert.That(MusterCampaign.NextAssault(4), Is.EqualTo(MusterCampaign.RaidChain));
            Assert.That(MusterCampaign.CuuldurachSealed, Is.False, "not loaded (the tests, a server without the campaign): nothing sealed");
        }

        [Test]
        public void FourteenQuests_WithTheOldTwoFoldedIn()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(14));
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("elfshot").And.Contain("azure_village"), "old progress keeps its quest ids");
            Assert.That(qs.Count(q => (bool?) q["group"] == true), Is.GreaterThanOrEqualTo(4));
            foreach (JToken q in qs.Where(q => q["requires"] != null))
                Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            Assert.That(qs.All(q => (int) q["level"] >= 45), "Elite: 45 and up");
            Assert.That(Stories.ToString(), Does.Contain("Lug between us"), "the King's answer to Cliodna's letter");
        }

        [Test]
        public void TheSouthernMuster_KinToTheFourHalls()
        {
            RepZoneDef z = RepDefs.ForZone(216);
            Assert.That(z, Is.Not.Null);
            RepFactionDef m = z.Faction("southern_muster");
            Assert.That(m.Title(Rank.Legend, false), Is.EqualTo("Lightbreaker"));
            foreach (string k in new[] { "sentinels_of_ceannai", "aines_circle", "clann_of_alainn_bin", "keeners_of_cullen" })
            {
                Assert.That(m.Kin, Does.Contain(k));
                Assert.That(RepDefs.Faction(k).Kin, Does.Contain("southern_muster"), "kin both ways: " + k);
            }
            var quests = Stories["quests"].Select(q => (string) q["id"]).ToHashSet();
            Assert.That(quests.All(q => z.Quests.ContainsKey(q)), "every quest is someone's");
        }
    }
}
