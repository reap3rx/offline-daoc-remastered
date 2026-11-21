using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Charged shots (owner 2026-11-20): one button held through Quick -> Standard -> Critical -> Overdraw.</summary>
[TestFixture]
public sealed class UT_ChargedShots
{
    [Test]
    public void TheStagesComeInOrder()
    {
        var at = ActionCombat.StagesFor(3000, true, "archer");
        Assert.That(at.Quick, Is.EqualTo(1350));
        Assert.That(at.Crit, Is.EqualTo(3000 + 1050));
        Assert.That(at.Over, Is.EqualTo(at.Crit + ActionCombat.OverdrawGraceMs));
        Assert.That(ActionCombat.StageFor(1000, 3000, at, "archer", 2.0), Is.Null);              // let go too soon
        var quick = ActionCombat.StageFor(2000, 3000, at, "archer", 2.0)!.Value;
        Assert.That(quick.Name, Is.EqualTo("quick"));
        Assert.That(quick.Effectiveness, Is.InRange(0.55, 0.9));
        Assert.That(quick.Reach, Is.EqualTo(ActionCombat.QuickReach));
        var full = ActionCombat.StageFor(3200, 3000, at, "archer", 2.0)!.Value;
        Assert.That((full.Name, full.Effectiveness, full.Critical), Is.EqualTo(("full", 1.0, false)));
        var crit = ActionCombat.StageFor(4200, 3000, at, "archer", 2.0)!.Value;
        Assert.That((crit.Name, crit.Effectiveness, crit.Critical), Is.EqualTo(("critical", 2.0, true)));
        var over = ActionCombat.StageFor(at.Over + 10, 3000, at, "archer", 2.0)!.Value;
        Assert.That(over.Name, Is.EqualTo("overdrawn"));
        Assert.That(over.Miss, Is.GreaterThan(0.3));
    }

    [Test]
    public void WithoutCriticalShotTheFullDrawOverdraws()
    {
        var at = ActionCombat.StagesFor(3000, false, "archer");
        Assert.That(at.Crit, Is.EqualTo(int.MaxValue));
        Assert.That(ActionCombat.StageFor(3000 + ActionCombat.OverdrawGraceMs + 1, 3000, at, "archer", 2.0)!.Value.Effectiveness,
            Is.EqualTo(ActionCombat.OverdrawDamage));
    }

    [Test]
    public void BasicAndMovingShotsStopAtTheirLastStage()
    {
        var basic = ActionCombat.StagesFor(3000, false, "basic");
        var b = ActionCombat.StageFor(9000, 3000, basic, "basic", 2.0)!.Value;
        Assert.That((b.Effectiveness, b.Critical), Is.EqualTo((ActionCombat.BasicDamage, false)));
        var move = ActionCombat.StagesFor(3000, true, "move");
        var m = ActionCombat.StageFor(9000, 3000, move, "move", 2.0)!.Value;
        Assert.That(m.Name, Is.EqualTo("full"));
    }
}
