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
    /// <summary>The Cursed Forest (the zone brief and the owner's answers, 2026-11-24): the Unseelie Court's seat, Elite, nothing
    /// below orange; King Lug's campaign - a general at Druim Cain (45+), the Forest Gate, four checkpoints each held 30
    /// minutes, the court's counter-attacks cascading back, the raid on Queen Cliodna (three phases), four hours of the King's
    /// forest; 14 story quests; the Host of Lug.</summary>
    [TestFixture]
    public sealed class UT_CursedForest
    {
        static Assembly Asm => typeof(ZoneSiege).Assembly;

        static string Text(string name)
        {
            using Stream s = Asm.GetManifestResourceStream(name);
            Assert.That(s, Is.Not.Null, name);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }

        static ZoneEventsDef Events => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone208_cursed_forest.json"));
        static ZoneEventsDef Valley => JsonConvert.DeserializeObject<ZoneEventsDef>(Text("DynamicEvents.zone206_valley_of_bri_leith.json"));
        static JToken Build => JToken.Parse(Text("ZoneBuilds.zone208_cursed_forest.json"));
        static JToken Stories => JToken.Parse(Text("StoryQuests.hib_cursed_forest.json"));
        static HashSet<string> Items(string file) => JToken.Parse(Text("StoryItems." + file + ".json")).Select(r => (string) r["Id_nb"]).ToHashSet();

        [Test]
        public void TheCourtHoldsIt_NothingBelowOrange()
        {
            JToken b = Build;
            Assert.That((string) b["rating"], Is.EqualTo("elite"));
            var members = (JObject) b["members"];
            foreach (JProperty m in members.Properties())
                Assert.That((string) m.Value["tier"], Is.AnyOf("orange", "red", "purple"), m.Name);
            int total = 0, named = 0;
            void Add(string member, int n)
            {
                JToken m = members[member];
                total += n;
                if (char.IsUpper(member[0]) && (string) m["tier"] == "purple")
                    named += n;
                foreach (JProperty g in (m["guards"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(g.Name, n * (int) g.Value);
            }
            foreach (JToken s in b["sites"])
                foreach (JProperty sp in (s["spawn"] as JObject)?.Properties() ?? Enumerable.Empty<JProperty>())
                    Add(sp.Name, (int) sp.Value);
            Assert.That(total, Is.InRange(300, 420));
            Assert.That(named, Is.GreaterThanOrEqualTo(5), "owner: about 5+ named purple mini-bosses");
            var ids = b["sites"].Select(s => (string) s["id"]).ToList();
            foreach (string[] held in LugCampaign.HeldSites.Skip(1))
                foreach (string id in held)
                    Assert.That(ids, Does.Contain(id), "the campaign sweeps it");
            Assert.That(ids.Count(i => i.StartsWith(LugCampaign.PocketPrefix)), Is.InRange(2, 4), "a few farm pockets after the win");
            var clears = b["sites"].Where(s => (string) s["kind"] == "clear").SelectMany(s => s["names"].Values<string>()).ToList();
            Assert.That(clears, Does.Contain("Faerie Queen"), "Cliodna's seat now");
            Assert.That(members.Properties().Count(m => (int?) m.Value["model"] == CliodnaRaid.BainsheeModel), Is.GreaterThanOrEqualTo(3), "bainshees");
        }

        [Test]
        public void OnlyTheCampaignsBattles_InTheForest()
        {
            ZoneEventsDef z = Events;
            Assert.That(z.Chains.All(c => c.Manual), "no events but the campaign's");
            var ids = z.Chains.Select(c => c.Id).ToList();
            Assert.That(ids.Count, Is.EqualTo(9));
            for (int n = 0; n <= LugCampaign.Checkpoints; n++)
                Assert.That(ids, Does.Contain(LugCampaign.NextAssault(n)));
            for (int n = 1; n <= LugCampaign.Checkpoints; n++)
            {
                Assert.That(ids, Does.Contain(LugCampaign.CounterFor(n)));
                ChainDef a = z.Chains.First(c => c.Id == LugCampaign.NextAssault(n - 1));
                Assert.That(a.Giver, Is.Not.Null, "a captain of the Host leads it");
                Assert.That(a.Stages.Last().Type, Is.EqualTo("boss"), "a power check");
                ChainDef k = z.Chains.First(c => c.Id == LugCampaign.CounterFor(n));
                Assert.That(k.Stages[0].Type, Is.EqualTo("defend"));
                Assert.That(k.Stages[0].Protect.HealthMult, Is.GreaterThanOrEqualTo(10), "the Host holds a while without help");
            }
            // harder each time
            int Kill(int n) => z.Chains.First(c => c.Id == LugCampaign.NextAssault(n - 1)).Stages[0].Kill;
            Assert.That(Kill(1) < Kill(2) && Kill(2) < Kill(3) && Kill(3) < Kill(4));
            ChainDef raid = z.Chains.First(c => c.Id == CliodnaRaid.ChainId);
            Assert.That(raid.MinPeople, Is.GreaterThanOrEqualTo(12), "two or three groups");
            Assert.That(raid.Stages[0].Boss.Name, Is.EqualTo("Queen Cliodna"));
            Assert.That(raid.Stages[0].TimeS, Is.GreaterThanOrEqualTo(2400), "a long fight");
            HashSet<string> cf = Items("cf208_cursed_forest");
            foreach (ItemRewardDef i in z.Chains.SelectMany(c => c.Stages).SelectMany(s => s.Reward?.Items ?? new List<ItemRewardDef>()))
                Assert.That(cf.Contains($"{i.Id}_l30") || cf.Contains(i.Id), i.Id);
            foreach (SiegeStockDef st in LugCampaign.SeatCamp().SelectMany(n => n.Stock))
                Assert.That(cf.Contains($"{st.Item}_l30") || cf.Contains(st.Item), st.Item);
        }

        [Test]
        public void TheForestGate_IsTheCampaignsFirstBattle()
        {
            SiegeDef d = Valley.Siege;
            Assert.That(d.Campaign, Is.EqualTo("lug"));
            Assert.That(d.Id, Is.EqualTo(LugCampaign.GateSiege));
            Assert.That(d.Feeds, Is.Empty, "no resolve to build: only the General starts it");
            Assert.That(d.LastRaid, Is.EqualTo("bri_forest_gate_raid"), "the Queen's Hunt comes as the counter-attack");
        }

        [Test]
        public void TheCampaign_StepsForwardAndFallsBack()
        {
            var s = new LugCampaign.State();
            DateTime t = new DateTime(2026, 11, 24, 12, 0, 0, DateTimeKind.Utc);
            Assert.That(LugCampaign.CanStart(44, s, t), Is.Not.Null, "45 and up");
            Assert.That(LugCampaign.CanStart(45, s, t), Is.Null);
            s.Phase = LugCampaign.Phase.Gate;
            Assert.That(LugCampaign.CanStart(50, s, t), Is.Not.Null, "already marching");
            LugCampaign.Won(s, 0, t);
            Assert.That(s.DeadlineUtc, Is.EqualTo(t + LugCampaign.Window));
            Assert.That(LugCampaign.Window, Is.EqualTo(TimeSpan.FromMinutes(30)));
            LugCampaign.Won(s, 1, t);
            LugCampaign.Won(s, 2, t);
            LugCampaign.CounterHeld(s, t.AddMinutes(40));
            Assert.That(s.Held, Is.EqualTo(2));
            Assert.That(s.DeadlineUtc, Is.EqualTo(t.AddMinutes(70)), "beaten off: the clock starts again");
            Assert.That(LugCampaign.CounterLost(s, t), Is.True);
            Assert.That(s.Held, Is.EqualTo(1), "a step back");
            Assert.That(LugCampaign.CounterLost(s, t), Is.True);
            Assert.That(LugCampaign.CounterLost(s, t), Is.False, "the Forest Gate lost: pushed out");
            LugCampaign.Over(s, t, true);
            Assert.That(s.Phase, Is.EqualTo(LugCampaign.Phase.Idle));
            Assert.That(LugCampaign.CanStart(50, s, t), Is.Not.Null, "the Host rests a while");
            Assert.That(LugCampaign.CanStart(50, s, t + LugCampaign.Rest), Is.Null);
            LugCampaign.Victory(s, t);
            Assert.That(LugCampaign.FogLifted(s), Is.True);
            Assert.That(s.VictoryUntilUtc - t, Is.EqualTo(TimeSpan.FromHours(4)));
            Assert.That(LugCampaign.AssaultIndex("cf_cp3_assault"), Is.EqualTo(3));
            Assert.That(LugCampaign.AssaultIndex(CliodnaRaid.ChainId), Is.EqualTo(5));
            Assert.That(LugCampaign.CounterIndex("cf_cp2_counter"), Is.EqualTo(2));
            Assert.That(LugCampaign.NextAssault(4), Is.EqualTo(CliodnaRaid.ChainId));
            Assert.That(LugCampaign.CounterFor(0), Is.Null, "the gate's counter is the Queen's Hunt");
        }

        [Test]
        public void Cliodna_ElfHagBainshee()
        {
            Assert.That(CliodnaRaid.PhaseAt(1.0), Is.EqualTo(1));
            Assert.That(CliodnaRaid.PhaseAt(0.5), Is.EqualTo(2));
            Assert.That(CliodnaRaid.PhaseAt(0.2), Is.EqualTo(3));
            Assert.That(CliodnaRaid.Look(3).model, Is.EqualTo(CliodnaRaid.BainsheeModel));
            Assert.That(CliodnaRaid.Look(3).size, Is.GreaterThan(CliodnaRaid.Look(2).size));
            Assert.That(CliodnaRaid.Look(2).size, Is.GreaterThan(CliodnaRaid.Look(1).size));
            Assert.That(CliodnaRaid.Rot.SpellType, Is.EqualTo(eSpellType.Disease), "curers wanted");
            Assert.That(CliodnaRaid.Venom.SpellType, Is.EqualTo(eSpellType.DamageOverTime), "poison: curers again");
        }

        [Test]
        public void FourteenQuests_WithTheOldTwoFoldedIn()
        {
            var qs = Stories["quests"].ToList();
            Assert.That(qs.Count, Is.EqualTo(14));
            var ids = qs.Select(q => (string) q["id"]).ToHashSet();
            Assert.That(ids, Does.Contain("leprechaun").And.Contain("goborchend"), "old progress keeps its quest ids");
            Assert.That(qs.Count(q => (bool?) q["group"] == true), Is.GreaterThanOrEqualTo(2));
            foreach (JToken q in qs.Where(q => q["requires"] != null))
                Assert.That(ids, Does.Contain((string) q["requires"]), (string) q["id"]);
            Assert.That(qs.All(q => (int) q["level"] >= 45), "Elite: 45 and up");
        }

        [Test]
        public void TheHostOfLug_KinToTheRealmsSoldiers()
        {
            RepZoneDef z = RepDefs.ForZone(208);
            Assert.That(z, Is.Not.Null);
            RepFactionDef h = z.Faction("host_of_lug");
            Assert.That(h.Title(Rank.Legend, false), Is.EqualTo("Champion of the Lamfhota"));
            Assert.That(h.Kin, Does.Contain("rangers_druim_cain"), "the Rangers shared");
            Assert.That(RepDefs.Faction("rangers_druim_cain").Kin, Does.Contain("host_of_lug"), "kin both ways");
        }
    }
}
