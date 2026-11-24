using System.IO;
using System.Linq;
using DOL.GS.DynamicEvents;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>The rebuilt zones' quest objectives say what to do, where and how many (owner 2026-11-23: "I would like
    /// the quest objectives to be a bit more descriptive" - "Search under the market stalls" didn't say what or where).</summary>
    [TestFixture]
    public sealed class UT_QuestGoals
    {
        static JToken Quests(string file)
        {
            var asm = typeof(ZoneSiege).Assembly;
            using var r = new StreamReader(asm.GetManifestResourceStream("StoryQuests." + file + ".json")!);
            return JToken.Parse(r.ReadToEnd());
        }

        [TestCase("hib_connacht")]
        [TestCase("hib_silvermine")]
        public void EveryObjective_SaysWhatWhereAndHowMany(string file)
        {
            foreach (JToken q in Quests(file)["quests"])
                foreach (JToken s in q["steps"])
                {
                    string goal = (string) s["goal"], type = (string) s["type"], what = $"{q["id"]} {s["id"]}: '{goal}'";
                    Assert.That(goal.Length, Is.InRange(12, 120), what);
                    if (type == "search")
                        Assert.That(goal, Does.Contain("click the glinting spot"), what + " - how to search");
                    if (type == "kill" && (int?) s["count"] > 1)
                        Assert.That(goal, Does.Contain(((int) s["count"]).ToString()), what + " - how many");
                    if (type is "reach" or "kill" && goal.Contains("Go to"))
                        Assert.That(goal, Does.Match(@"\d+ m|beside|at the|in the"), what + " - where");
                }
        }

        /// <summary>Owner 2026-11-23: "let's make it so that the quests are scattered throughout the zone as much as we can,
        /// so that it brings interest and reason to explore the zone" - the main town keeps several, but a good share of
        /// every rebuilt zone's quests is handed out by people out in the zone (100 m or more past every town's edge).</summary>
        [TestCase("hib_connacht", "1354,1262,44;1300,674,37;1163,44,87")]     // Ardee, Basar, Druim Ligen (centre, radius m)
        [TestCase("hib_silvermine", "560,1078,50;800,113,44")]               // Howth, Ardagh
        public void AThirdOfTheQuests_AreGivenOutInTheZone(string file, string towns)
        {
            var t = towns.Split(';').Select(x => x.Split(',').Select(double.Parse).ToArray()).ToArray();
            JToken q = Quests(file);
            var at = q["npcs"].ToDictionary(n => (string) n["id"], n => ((double) n["pos"][0], (double) n["pos"][1]));
            int all = 0, field = 0;
            foreach (JToken quest in q["quests"])
            {
                all++;
                var (x, y) = at[(string) quest["giver"]];
                if (t.All(c => System.Math.Sqrt((x - c[0]) * (x - c[0]) + (y - c[1]) * (y - c[1])) > c[2] + 100))
                    field++;
            }
            Assert.That(field, Is.GreaterThanOrEqualTo(all / 3.0), $"{field} of {all} quests are given out in the zone");
        }
    }
}
