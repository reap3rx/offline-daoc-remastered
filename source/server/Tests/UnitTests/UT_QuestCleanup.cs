using DOL.GS.Quests;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Lough Derg's old quests turned off (QuestCleanup): the out-of-zone ones (phase 2), then the ones the story
/// arcs folded in (phase 5, 2026-11-22); the class paths and the zone's own small errands left on.</summary>
[TestFixture]
public sealed class UT_QuestCleanup
{
    [TestCase(21407, true)]      // Occupation of Lough Gur
    [TestCase(21526, true)]
    [TestCase(344, true)]        // a level 40 XP turn-in
    [TestCase(20238, true)]      // Ilisa's Trade
    [TestCase(20067, true)]      // Youth Gone Wrong: folded into Mandra's Boy
    [TestCase(20812, true)]      // Balm Hunt: folded into The Hill War
    [TestCase(21399, false)]     // Little Wind: left as it is
    [TestCase(20300, false)]     // Way of Magic: a class path quest
    [TestCase(400, false)]       // Scrap of Cloth XP Item: the zone's own level
    public void LoughDergsOldQuests(int id, bool off) =>
        Assert.That(QuestCleanup.IsDisabled(id), Is.EqualTo(off));
}
