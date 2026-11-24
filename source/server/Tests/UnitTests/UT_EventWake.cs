using System.IO;
using System.Linq;
using DOL.GS.DynamicEvents;
using Newtonsoft.Json;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Every event can say where it waits (2026-11-22: Connacht's night revel and Silvermine's moon-silver convoy
    /// start with an intercept - a path, no centre - and the wake point threw while they waited; the throw came out of
    /// the events' timer and stopped every event until a restart).</summary>
    [TestFixture]
    public sealed class UT_EventWake
    {
        [Test]
        public void EveryChainsFirstStage_HasACentreOrAPath()
        {
            var asm = typeof(ZoneSiege).Assembly;
            int n = 0;
            foreach (string res in asm.GetManifestResourceNames().Where(r => r.StartsWith("DynamicEvents.") && r.EndsWith(".json")))
            {
                using var rd = new StreamReader(asm.GetManifestResourceStream(res)!);
                var z = JsonConvert.DeserializeObject<ZoneEventsDef>(rd.ReadToEnd());
                foreach (ChainDef c in z?.Chains ?? new())
                {
                    string start = c.Start ?? c.Stages.FirstOrDefault()?.Id;      // (as the manager loads it)
                    StageDef s = c.Stages.FirstOrDefault(st => st.Id == start);
                    Assert.That(s, Is.Not.Null, $"{res} {c.Id}: its start stage '{start}'");
                    bool centre = s.Center != null && s.Center.Length >= 2;
                    bool path = s.Path != null && s.Path.Count > 0 && s.Path[0] != null && s.Path[0].Length >= 2;
                    Assert.That(centre || path, Is.True, $"{res} {c.Id}: its start stage has neither a centre nor a path");
                    n++;
                }
            }
            Assert.That(n, Is.GreaterThan(100));
        }
    }
}
