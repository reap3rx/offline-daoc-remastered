using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using DOL.GS;
using DOL.GS.DynamicEvents;
using DOL.GS.Quests;
using DOL.GS.StoryQuests;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Lough Derg's story arcs (2026-11-22) against the rest of the zone: what they hunt stands in the zone build,
/// the events they set off exist, every arc's chain is unbroken, and the old quests they fold in are turned off.</summary>
[TestFixture]
public class UT_LoughDergStories
{
    static string Resource(string endsWith)
    {
        Assembly asm = typeof(StoryQuestManager).Assembly;
        string name = asm.GetManifestResourceNames().Single(n => n.EndsWith(endsWith, StringComparison.OrdinalIgnoreCase));
        using var s = new StreamReader(asm.GetManifestResourceStream(name)!, Encoding.UTF8);
        return s.ReadToEnd();
    }

    static StoryFileDef Stories => JsonConvert.DeserializeObject<StoryFileDef>(Resource("hib_lough_derg.json"));

    [Test]
    public void EveryArcIsAnUnbrokenChain()
    {
        var f = Stories;
        var ids = f.Quests.Select(q => q.Id).ToHashSet();
        Assert.That(f.Quests, Has.Count.GreaterThanOrEqualTo(26));
        foreach (var q in f.Quests)
        {
            if (!string.IsNullOrEmpty(q.Requires))
                Assert.That(ids, Does.Contain(q.Requires), q.Id);
            Assert.That(f.Npcs.Select(n => n.Id), Does.Contain(q.Giver), q.Id);
            Assert.That(q.MinLevel, Is.EqualTo(0), q.Id + ": a quest's level is a recommendation, not a gate");
        }
    }

    [Test]
    public void WhatTheyHuntStandsInTheZone()
    {
        var build = JObject.Parse(Resource("zonebuilds.zone200_lough_derg.json"));
        var names = ((JObject) build["members"]!).Properties()
            .Select(p => (string) (p.Value["name"] ?? p.Value["from"])).ToHashSet(StringComparer.OrdinalIgnoreCase);
        names.Add("Hughar");                                     // (a named monster of the zone's own, kept by the build)
        foreach (var q in Stories.Quests)
            foreach (var st in q.Steps.Where(s => !string.IsNullOrEmpty(s.Target)))
                Assert.That(names, Does.Contain(st.Target), $"{q.Id}/{st.Id}");
    }

    [Test]
    public void TheEventsTheyWakeExist()
    {
        var events = JsonConvert.DeserializeObject<ZoneEventsDef>(Resource("DynamicEvents.zone200_lough_derg.json"));
        var chains = events.Chains.Where(c => c.Giver == null).Select(c => c.Id).ToHashSet();
        var woken = Stories.Quests.SelectMany(q => q.Endings.Values).Select(e => e.WakeEvent).Where(w => w != null).ToList();
        Assert.That(woken, Has.Count.GreaterThanOrEqualTo(4));
        foreach (string w in woken)
            Assert.That(chains, Does.Contain(w));
    }

    [Test]
    public void SpawnedStoryMonstersTakeATier()
    {
        Assert.Multiple(() =>
        {
            Assert.That(StoryQuestManager.TierOf("green"), Is.EqualTo(MonsterTiers.Green));
            Assert.That(StoryQuestManager.TierOf("Purple"), Is.EqualTo(MonsterTiers.Purple));
            Assert.That(StoryQuestManager.TierOf(""), Is.Null);
            Assert.That(StoryQuestManager.TierOf("mauve"), Is.Null);
        });
        foreach (var q in Stories.Quests)
            foreach (var st in q.Steps.Where(s => s.Mob?.Tier != null))
                Assert.That(StoryQuestManager.TierOf(st.Mob.Tier), Is.Not.Null, $"{q.Id}/{st.Id}");
    }

    [Test]
    public void FoldedQuestsAreTurnedOff()
    {
        foreach (int id in new[] { 20067, 20812, 20816, 20304, 20302, 20306, 20068, 20866, 20076, 20868, 20075 })
            Assert.That(QuestCleanup.BuiltIn, Does.Contain(id), id.ToString());
    }

    [Test]
    public void QuestsPayAtYourLevel() =>
        Assert.That(StoryQuestManager.XpAtLevel(30), Is.EqualTo(GamePlayer.GetExperienceAmountForLevel(30) - GamePlayer.GetExperienceAmountForLevel(29)));
}
