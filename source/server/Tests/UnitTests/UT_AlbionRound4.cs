using System;
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
    /// <summary>Albion's PvE rework, round 4 ("Albion - the plan", 2026-11-24): Llyn Barfog (Elite; Morgana's seat - the Lake Host's
    /// campaign and Morgana's raid at the Gate of Annwn) and Dartmoor (Elite; Golestandt's lair - the Dragon-Watch's campaign, the
    /// Giants' Throne, and the dragon sealed until it's won).</summary>
    [TestFixture]
    public sealed class UT_AlbionRound4
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

        static readonly (AlbionCampaign C, string Build, string Story, string Events, string Spec)[] Zones =
        {
            (AlbionCampaign.Lake, "zone007_llyn_barfog", "alb_llyn_barfog", "zone007_llyn_barfog", "lb007_llyn_barfog"),
            (AlbionCampaign.Moor, "zone004_dartmoor", "alb_dartmoor", "zone004_dartmoor", "dm004_dartmoor"),
        };

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
        public void BothAreElite_NothingBelowOrange()
        {
            foreach (var z in Zones)
            {
                JToken b = Build(z.Build);
                Assert.That((string) b["rating"], Is.EqualTo("elite"), z.Build);
                var t = Tiers(b);
                Assert.That(t.Values.Sum(), Is.InRange(250, 700), z.Build);
                Assert.That(t.Keys, Is.SubsetOf(new[] { "orange", "red", "purple" }), z.Build + ": nothing below orange");
                Assert.That(t.GetValueOrDefault("purple"), Is.GreaterThanOrEqualTo(2), z.Build + ": named purples");
            }
        }

        [Test]
        public void TheCampaigns_PostsSweepsAndPockets()
        {
            foreach (var z in Zones)
            {
                AlbionCampaign c = z.C;
                var ids = Build(z.Build)["sites"].Select(s => (string) s["id"]).ToHashSet();
                foreach (string[] held in c.HeldSites.Skip(1))
                    Assert.That(ids, Is.SupersetOf(held), c.Key + ": the sites each post sweeps");
                Assert.That(ids.Count(i => i.StartsWith(AlbionCampaign.PocketPrefix)), Is.InRange(1, 4), c.Key + ": pockets stay after the win");
                Assert.That(c.Posts.Skip(1).All(p => p.Length == 3 && p[2] > 0), c.Key + ": every post has its height");

                var chains = Events(z.Events).Chains;
                var cids = chains.Select(x => x.Id).ToHashSet();
                for (int n = 0; n <= AlbionCampaign.Checkpoints; n++)
                    Assert.That(cids, Does.Contain(c.NextAssault(n)));
                for (int n = 1; n <= AlbionCampaign.Checkpoints; n++)
                {
                    Assert.That(cids, Does.Contain(c.CounterFor(n)));
                    ChainDef a = chains.First(x => x.Id == c.NextAssault(n - 1));
                    Assert.That(a.Manual, Is.True);
                    Assert.That(a.Giver, Is.Not.Null, a.Id + ": a captain gives it");
                    Assert.That(chains.First(x => x.Id == c.CounterFor(n)).Stages.Single().Type, Is.EqualTo("defend"));
                }
                ChainDef raid = chains.First(x => x.Id == c.RaidChain);
                Assert.That(raid.MinPeople, Is.GreaterThanOrEqualTo(8), "a raid");
                Assert.That(raid.Stages.Single().Type, Is.EqualTo("boss"));

                HashSet<string> items = Items(z.Spec);
                foreach (SiegeStockDef st in c.Camp().SelectMany(n => n.Stock ?? new List<SiegeStockDef>()))
                    Assert.That(items.Any(x => x.StartsWith(st.Item)), st.Item);
                foreach (ItemRewardDef i in raid.Stages.SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                    Assert.That(items.Any(x => x.StartsWith(i.Id)), i.Id);
            }
            Assert.That(Events("zone007_llyn_barfog").Chains.Single(c => c.Id == MorganaRaid.ChainId).Stages[0].Boss.Name, Does.Contain("Morgana"));
        }

        [Test]
        public void TheCampaigns_Rules()
        {
            DateTime t = new(2026, 11, 24, 20, 0, 0, DateTimeKind.Utc);
            AlbionCampaign lake = AlbionCampaign.Lake, moor = AlbionCampaign.Moor;
            var s = new AlbionCampaign.State();
            Assert.That(lake.CanStart(44, s, t), Is.Not.Null, "45 and up for the lake");
            Assert.That(lake.CanStart(45, s, t), Is.Null);
            Assert.That(moor.CanStart(49, s, t), Is.Not.Null, "50 and up for the moor");
            Assert.That(moor.CanStart(50, s, t), Is.Null);
            s = AlbionCampaign.Begin(s, t, "Albpve");
            Assert.That(s.Phase, Is.EqualTo(AlbionCampaign.Phase.Holding));
            Assert.That(lake.CanStart(50, s, t), Is.Not.Null, "already marching");
            Assert.That(lake.NextAssault(0), Is.EqualTo("lb_cp1_assault"));
            Assert.That(moor.NextAssault(4), Is.EqualTo("dm_giants_throne"));
            Assert.That(lake.CounterFor(0), Is.Null, "nothing comes for the merchants: the march just ends");
            Assert.That(lake.AssaultIndex("lb_cp3_assault"), Is.EqualTo(3));
            Assert.That(lake.AssaultIndex("dm_cp3_assault"), Is.EqualTo(0), "each campaign hears only its own");
            Assert.That(moor.CounterIndex("dm_cp2_counter"), Is.EqualTo(2));
            AlbionCampaign.Won(s, 2, t);
            Assert.That(AlbionCampaign.CounterLost(s, t), Is.True, "back to the first post");
            Assert.That(s.Held, Is.EqualTo(1));
            Assert.That(AlbionCampaign.CounterLost(s, t), Is.False, "pushed out");
            AlbionCampaign.Won(s, 4, t);
            AlbionCampaign.Victory(s, t);
            Assert.That(AlbionCampaign.IsWon(s), Is.True);
            Assert.That(s.VictoryUntilUtc, Is.EqualTo(t + AlbionCampaign.VictoryHold));
            AlbionCampaign.Over(s, t, false);
            Assert.That(s.Phase, Is.EqualTo(AlbionCampaign.Phase.Idle));
            Assert.That(lake.CanStart(50, s, t), Is.Not.Null, "resting");
            Assert.That(lake.CanStart(50, s, t + AlbionCampaign.Rest), Is.Null);
            Assert.That(AlbionCampaign.GolestandtSealed, Is.False, "not loaded (the tests): nothing is sealed");
        }

        [Test]
        public void Morgana_HasThreePhases_AndHerChampionsShieldHer()
        {
            Assert.That(MorganaRaid.PhaseAt(1.0), Is.EqualTo(1));
            Assert.That(MorganaRaid.PhaseAt(0.65), Is.EqualTo(2));
            Assert.That(MorganaRaid.PhaseAt(0.30), Is.EqualTo(3));
            Assert.That(MorganaRaid.Floor(2, true), Is.EqualTo(MorganaRaid.WrathFloor));
            Assert.That(MorganaRaid.Floor(3, true), Is.EqualTo(MorganaRaid.AfancFloor));
            Assert.That(MorganaRaid.Floor(2, false), Is.EqualTo(0), "the Wrath of Mordred down: she can be hurt again");
            Assert.That(MorganaRaid.WrathFloor, Is.LessThan(MorganaRaid.WrathAt));
            Assert.That(MorganaRaid.AfancFloor, Is.LessThan(MorganaRaid.AfancAt));
        }

        [Test]
        public void TheStories_LeadToTheCampaigns()
        {
            var lb = Stories("alb_llyn_barfog")["quests"].ToList();
            var dm = Stories("alb_dartmoor")["quests"].ToList();
            Assert.That(lb.Select(q => (string) q["id"]), Is.SupersetOf(new[] { "hounds", "psalter" }), "old progress keeps its quest ids");
            Assert.That(dm.Select(q => (string) q["id"]), Is.SupersetOf(new[] { "quarry_oath", "dragons_tithe" }));
            Assert.That(lb.Where(q => (string) q["id"] is "hounds" or "psalter").All(q => (int) q["level"] >= 44), "brought up to the Elite band");
            foreach (var qs in new[] { lb, dm })
            {
                Assert.That(qs.Count, Is.InRange(12, 30));
                var ids = qs.Select(q => (string) q["id"]).ToHashSet();
                foreach (JToken q in qs.Where(q => q["requires"] != null))
                    Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            }
            Assert.That(lb.Single(q => (string) q["id"] == "lb_lady").ToString(), Does.Contain("Percival"));
            Assert.That(dm.Single(q => (string) q["id"] == "dm_throne").ToString(), Does.Contain("Constantine"));
            Assert.That(AlbionCampaign.Lake.MarshalName, Is.EqualTo("Sir Percival"));
            Assert.That(AlbionCampaign.Moor.MarshalName, Does.Contain("Constantine"));
        }

        [Test]
        public void TheFactions_JoinTheirKin()
        {
            foreach (var (zone, a, b, f) in new[] { (7, "knights_of_the_lake", "maidens_of_the_lake", "alb_llyn_barfog"),
                         (4, "dragon_watch", "quarry_oath", "alb_dartmoor") })
            {
                RepZoneDef z = RepDefs.ForZone(zone);
                Assert.That(z.Faction(a), Is.Not.Null);
                Assert.That(z.Faction(b), Is.Not.Null);
                Assert.That(RepDefs.Faction("pendragons_watch").Kin, Does.Contain(a));
                Assert.That(RepDefs.Faction("abbey_faithful").Kin, Does.Contain(b));
                Assert.That(Stories(f)["quests"].Select(q => (string) q["id"]).All(q => z.Quests.ContainsKey(q)), "every quest is someone's");
            }
        }
    }
}
