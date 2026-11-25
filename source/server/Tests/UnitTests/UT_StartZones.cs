using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using DOL.GS;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>The starting-town choice at character creation (owner 2026-11-22: "Peaceful zones and wild zones will be
    /// offered as starting zones on character creation to help spread out players and bots (who will also get randomly
    /// assigned one of the zones as their starting zone) Players will be made aware that starting in a Wild zone is more
    /// difficult"): level_bands.json start_choices after the realm's hub; the client's content/rules/start_zones.json
    /// shows the same list.</summary>
    [TestFixture]
    public sealed class UT_StartZones
    {
        static Assembly Asm => typeof(LevelBands).Assembly;

        static string BandsText()
        {
            string res = Asm.GetManifestResourceNames().Single(n => n.EndsWith("level_bands.json", StringComparison.OrdinalIgnoreCase));
            using var r = new StreamReader(Asm.GetManifestResourceStream(res)!);
            return r.ReadToEnd();
        }

        static LevelBands.Config Bands => LevelBands.Parse(BandsText());

        static readonly string[] Ratings = { "peaceful", "wild", "dangerous", "deadly", "elite" };

        [Test]
        public void Hibernia_StartsAtMagMell_Ardee_Ardagh_Brynach_Connla_OrCulraid_InThatOrder()
        {
            // (Brynach and Connla added 2026-11-23 with the Valley of Bri Leith and Shannon Estuary rebuilds: "Yes, Connla
            // should be a starting zone", Brynach "Yes, I like that")
            var hib = LevelBands.StartsOf(Bands, eRealm.Hibernia);
            Assert.That(hib.Select(s => s.Name), Is.EqualTo(new[] { "Mag Mell", "Ardee", "Ardagh", "Brynach", "Connla", "Culraid" }));
            Assert.That(hib.Select(s => s.Rating), Is.EqualTo(new[] { "peaceful", "peaceful", "wild", "wild", "wild", "deadly" }));
            // Ardee in Connacht (zone 207), Ardagh in the Silvermine Mountains (201): region 200, inside the zone's square
            void In(LevelBands.Start s, int ox, int oy)
            {
                Assert.That(s.Region, Is.EqualTo(200), s.Name);
                Assert.That(s.X, Is.InRange(ox + 2000, ox + 65536 - 2000), s.Name);
                Assert.That(s.Y, Is.InRange(oy + 2000, oy + 65536 - 2000), s.Name);
                Assert.That(s.Z, Is.GreaterThan(0), s.Name);
            }
            In(hib[1], 286720, 417792);
            In(hib[2], 319488, 548864);
            In(hib[3], 385024, 483328);                        // the Valley of Bri Leith (206)
            In(hib[4], 286720, 614400);                        // Shannon Estuary (202)
            In(hib[5], 286720, 679936);                        // Lough Gur (204): Culraid, the hard start
        }

        [Test]
        public void EveryStartChoice_HasItsScreenText_InPlainLetters()
        {
            var c = Bands;
            foreach (eRealm realm in new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia })
            {
                var all = LevelBands.StartsOf(c, realm);
                Assert.That(all, Is.Not.Empty, realm.ToString());
                if (all.Count < 2)
                    continue;                                  // one town: the screen isn't shown
                foreach (var s in all)
                {
                    Assert.That(s.Name, Is.Not.Empty);
                    Assert.That(s.Zone, Is.Not.Empty, s.Name);
                    Assert.That(Ratings, Does.Contain(s.Rating), s.Name);
                    Assert.That(s.Blurb, Is.Not.Empty, s.Name);
                    Assert.That((s.Name + s.Zone + s.Blurb).All(ch => ch < 128), Is.True, s.Name + ": plain letters (the chat's encoding)");
                }
                Assert.That(all.Select(s => s.Name).Distinct().Count(), Is.EqualTo(all.Count), "one entry per town");
            }
        }

        [Test]
        public void TheRatings_MatchTheZoneBuilds()
        {
            var builds = Asm.GetManifestResourceNames().Where(n => n.StartsWith("ZoneBuilds.") && n.EndsWith(".json"))
                .Select(n => { using var r = new StreamReader(Asm.GetManifestResourceStream(n)!); return JToken.Parse(r.ReadToEnd()); })
                .Where(b => b["zone"] != null && b["rating"] != null)
                .ToDictionary(b => (int) b["zone"], b => ((string) b["rating"]).ToLowerInvariant());
            var hib = LevelBands.StartsOf(Bands, eRealm.Hibernia);
            Assert.That(builds[207], Is.EqualTo(hib.Single(s => s.Name == "Ardee").Rating));
            Assert.That(builds[201], Is.EqualTo(hib.Single(s => s.Name == "Ardagh").Rating));
            Assert.That(builds[206], Is.EqualTo(hib.Single(s => s.Name == "Brynach").Rating));
            Assert.That(builds[202], Is.EqualTo(hib.Single(s => s.Name == "Connla").Rating));
            Assert.That(builds[204], Is.EqualTo(hib.Single(s => s.Name == "Culraid").Rating));
        }

        [Test]
        public void TheStartZones_BeginLow_TheWildOneAStepHarder()
        {
            var z = Bands.Zones;
            Assert.That(z["207"].Min, Is.EqualTo(0), "Connacht, a peaceful start: level 0 monsters by Ardee as by Mag Mell");
            Assert.That(z["201"].Min, Is.InRange(1, 4), "the Silvermine Mountains, a wild start: harder, still for level 1");
            Assert.That(z["201"].Min, Is.GreaterThan(z["207"].Min));
            Assert.That(z["206"].Min, Is.InRange(1, 4), "the Valley of Bri Leith, a wild start");
            Assert.That(z["202"].Min, Is.InRange(1, 4), "Shannon Estuary, a wild start");
        }

        [Test]
        public void EveryStartTown_IsALevelAnchor_WithoutDoublingMagMell()
        {
            var c = Bands;
            int before = c.Anchors.Count;
            LevelBands.AddStartAnchors(c);
            Assert.That(c.Anchors.Count, Is.EqualTo(before + 10), "Ardee, Ardagh, Brynach, Connla, Culraid, Humberton, West Downs, Caer Ulfwych, Adribard's Retreat and Cornwall Station");
            Assert.That(c.Anchors.Count(a => a.Name == "Ardee" && a.Region == 200), Is.EqualTo(1));
            Assert.That(c.Anchors.Count(a => a.Name == "Ardagh" && a.Region == 200), Is.EqualTo(1));
            LevelBands.AddStartAnchors(c);
            Assert.That(c.Anchors.Count, Is.EqualTo(before + 10), "twice is once");
        }

        [Test]
        public void TheHardStart_IsOnePerRealm_InADeadlyZone_WithATrainerAndABindPoint()
        {
            // (owner 2026-11-24: "one deadly zone being a starting location for the crazies"; every realm gets one, "easy/medium/hard
            // starting ones" - Albion's and Midgard's come with their reviews)
            foreach (eRealm realm in new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia })
            {
                var hard = LevelBands.StartsOf(Bands, realm).Where(s => s.Hard).ToList();
                Assert.That(hard.Count, Is.LessThanOrEqualTo(1), realm + ": one hard start at most");
                foreach (var s in hard)
                {
                    Assert.That(s.Rating, Is.EqualTo("deadly"), s.Name);
                    Assert.That(s.Blurb, Does.StartWith("HARD START"), s.Name + ": the screen says so");
                    Assert.That(s.Trainer, Has.Length.EqualTo(4), s.Name);
                    Assert.That(s.Bind, Has.Length.EqualTo(3), s.Name);
                    Assert.That(Math.Abs(s.Trainer[0] - s.X) + Math.Abs(s.Trainer[1] - s.Y), Is.LessThan(1500), s.Name + ": the trainer by the start");
                    Assert.That(Math.Abs(s.Bind[0] - s.X) + Math.Abs(s.Bind[1] - s.Y), Is.LessThan(750), s.Name + ": the start inside the bind point");
                }
            }
            Assert.That(LevelBands.StartsOf(Bands, eRealm.Hibernia).Single(s => s.Hard).Name, Is.EqualTo("Culraid"));
        }

        [Test]
        public void TheTryhardBots_FavourTheHardStart_TheCasualOnesNever()
        {
            var easy = new DOL.GS.GameEvents.StartupLocation { XPos = 1 };
            var wild = new DOL.GS.GameEvents.StartupLocation { XPos = 2 };
            var hard = new DOL.GS.GameEvents.StartupLocation { XPos = 3 };
            var all = new[] { easy, wild, hard };
            int Count(string tier)
            {
                var rng = new Random(7);
                int n = 0;
                for (int i = 0; i < 4000; i++)
                    if (ReferenceEquals(DOL.GS.GameEvents.StartupLocations.ChooseAutonomousLocation(all, tier, l => l.XPos == 3, rng), hard))
                        n++;
                return n;
            }
            Assert.That(Count("casual"), Is.EqualTo(0));
            Assert.That(Count("regular"), Is.InRange(1000, 1700), "a third, like any other start");
            Assert.That(Count("tryhard"), Is.InRange(2700, 3300), "six times as likely as each other start: three in four");
            Assert.That(DOL.GS.GameEvents.StartupLocations.ChooseAutonomousLocation(new[] { hard }, "casual", l => true, new Random(1)), Is.SameAs(hard),
                "the only start is still a start");
        }

        [Test]
        public void NoHub_NoChoices()
        {
            var c = LevelBands.Parse("{\"start_choices\": {\"3\": [{\"name\": \"Ardee\", \"region\": 200, \"x\": 1, \"y\": 1, \"z\": 1}]}}");
            Assert.That(LevelBands.StartsOf(c, eRealm.Hibernia), Is.Empty, "without the hub the database's StartupLocation stands");
        }

        [Test]
        public void TheClientsList_IsTheServers()
        {
            string file = null;
            for (var d = new DirectoryInfo(TestContext.CurrentContext.TestDirectory); d != null && file == null; d = d.Parent)
            {
                string f = Path.Combine(d.FullName, "new-client", "godot", "content", "rules", "start_zones.json");
                if (File.Exists(f))
                    file = f;
            }
            if (file == null)
                Assert.Ignore("new-client/godot/content/rules/start_zones.json not found above the test folder");
            var client = JObject.Parse(File.ReadAllText(file))["realms"] as JObject;
            var c = Bands;
            foreach (eRealm realm in new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia })
            {
                var server = LevelBands.StartsOf(c, realm);
                var list = client?[((int) realm).ToString()] as JArray;
                Assert.That(list, Is.Not.Null, realm.ToString());
                Assert.That(list.Select(t => (string) t["name"]), Is.EqualTo(server.Select(s => s.Name)), realm + ": the same towns, in order");
                for (int i = 0; i < server.Count; i++)
                {
                    Assert.That((string) list[i]["zone"] ?? "", Is.EqualTo(server[i].Zone ?? ""), server[i].Name);
                    Assert.That((string) list[i]["rating"] ?? "", Is.EqualTo(server[i].Rating ?? ""), server[i].Name);
                    Assert.That((string) list[i]["blurb"] ?? "", Is.EqualTo(server[i].Blurb ?? ""), server[i].Name);
                }
            }
        }
    }
}
