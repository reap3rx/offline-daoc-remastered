using System;
using System.Linq;
using NUnit.Framework;

namespace DOL.GS.Tests;

/// <summary>The chat redesign (owner 2026-11-16): zone and realm defense channels, calls for help, group asking aloud.</summary>
[TestFixture]
public class UT_RealmChat
{
    [TestCase("yes")]
    [TestCase("Yes please")]
    [TestCase("YES PLEASE!")]
    [TestCase("sure")]
    [TestCase("Sure thing")]
    [TestCase("ok")]
    [TestCase("Okay.")]
    [TestCase("yeah")]
    [TestCase("yep, let's go")]
    [TestCase("aye")]
    [TestCase("absolutely!")]
    [TestCase("yes thank you")]
    [TestCase("yes Aldric")]
    [TestCase("Aldric, sure")]
    public void GroupAnswer_CommonYesPhrases(string text)
    {
        Assert.That(AutonomousPersonaPlay.ParseAnswer(text, "Aldric"), Is.EqualTo(AutonomousPersonaPlay.Answer.Yes));
    }

    [TestCase("no")]
    [TestCase("No thank you")]
    [TestCase("NO THANKS")]
    [TestCase("nope")]
    [TestCase("nah")]
    [TestCase("nah, I'm good")]
    [TestCase("I'm good")]
    [TestCase("not now")]
    [TestCase("maybe later")]
    [TestCase("no thanks Aldric")]
    [TestCase("thanks but no")]
    public void GroupAnswer_CommonNoPhrases(string text)
    {
        Assert.That(AutonomousPersonaPlay.ParseAnswer(text, "Aldric"), Is.EqualTo(AutonomousPersonaPlay.Answer.No));
    }

    [TestCase("where is the trainer?")]
    [TestCase("hello")]
    [TestCase("")]
    [TestCase("what level are you")]
    public void GroupAnswer_OtherTalkIsNeither(string text)
    {
        Assert.That(AutonomousPersonaPlay.ParseAnswer(text, "Aldric"), Is.EqualTo(AutonomousPersonaPlay.Answer.None));
    }

    [TestCase("help!", true)]
    [TestCase("Need a hand at the ruins", true)]
    [TestCase("anyone around? adds everywhere", true)]
    [TestCase("keep under attack, defend!", true)]
    [TestCase("nice weather today", false)]
    [TestCase("where is the stable master", false)]
    public void HelpWanted_ReadsCallsForHelp(string text, bool expected)
    {
        Assert.That(AutonomousHelpCalls.HelpWanted(text), Is.EqualTo(expected));
    }

    [TestCase("lfg", true)]
    [TestCase("LFG level 20 healer", true)]
    [TestCase("anyone want to group?", true)]
    [TestCase("looking for a group", true)]
    [TestCase("help!", false)]
    public void GroupWanted_ReadsLookingForGroup(string text, bool expected)
    {
        Assert.That(AutonomousHelpCalls.GroupWanted(text), Is.EqualTo(expected));
    }

    [Test]
    public void CanAnswer_OnlyFreeHealthyNearbyRealmMatesOfLevel()
    {
        Assert.That(AutonomousHelpCalls.CanAnswer(true, true, 100, 20, 17, true, true), Is.True);
        Assert.That(AutonomousHelpCalls.CanAnswer(false, true, 100, 20, 17, true, true), Is.False, "grouped");
        Assert.That(AutonomousHelpCalls.CanAnswer(true, false, 100, 20, 17, true, true), Is.False, "busy");
        Assert.That(AutonomousHelpCalls.CanAnswer(true, true, 40, 20, 17, true, true), Is.False, "hurt");
        Assert.That(AutonomousHelpCalls.CanAnswer(true, true, 100, 10, 17, true, true), Is.False, "too low");
        Assert.That(AutonomousHelpCalls.CanAnswer(true, true, 100, 20, 17, false, true), Is.False, "other realm");
        Assert.That(AutonomousHelpCalls.CanAnswer(true, true, 100, 20, 17, true, false), Is.False, "too far");
    }

    [Test]
    public void HelpersWanted_AndMinimumLevel()
    {
        Assert.That(AutonomousHelpCalls.HelpersWanted(AutonomousHelpCalls.Kind.Group, RealmChatChannels.Channel.Zone), Is.EqualTo(1));
        Assert.That(AutonomousHelpCalls.HelpersWanted(AutonomousHelpCalls.Kind.Fight, RealmChatChannels.Channel.Zone), Is.EqualTo(2));
        Assert.That(AutonomousHelpCalls.HelpersWanted(AutonomousHelpCalls.Kind.Fight, RealmChatChannels.Channel.Rvr), Is.EqualTo(3));
        Assert.That(AutonomousHelpCalls.MinimumLevel(AutonomousHelpCalls.Kind.Fight, 20, 0, RealmChatChannels.Channel.Zone), Is.EqualTo(17));
        Assert.That(AutonomousHelpCalls.MinimumLevel(AutonomousHelpCalls.Kind.Event, 5, 12, RealmChatChannels.Channel.Zone), Is.EqualTo(10));
        Assert.That(AutonomousHelpCalls.MinimumLevel(AutonomousHelpCalls.Kind.Fight, 20, 0, RealmChatChannels.Channel.Rvr), Is.EqualTo(AutonomousHelpCalls.MinRvrLevel));
    }

    [Test]
    public void YellsForHelp_ReachOnlyNearbyBots()
    {
        Assert.That(AutonomousHelpCalls.Reach(RealmChatChannels.Channel.Local), Is.LessThan(AutonomousHelpCalls.Reach(RealmChatChannels.Channel.Zone)));
        Assert.That(AutonomousHelpCalls.Reach(RealmChatChannels.Channel.Local), Is.GreaterThan(WorldMgr.YELL_DISTANCE));
        Assert.That(AutonomousHelpCalls.HelpersWanted(AutonomousHelpCalls.Kind.Fight, RealmChatChannels.Channel.Local), Is.EqualTo(2));
    }

    [TestCase(eClassType.ListCaster, eCharacterClass.Wizard, true)]
    [TestCase(eClassType.Hybrid, eCharacterClass.Cleric, true)]
    [TestCase(eClassType.Hybrid, eCharacterClass.Healer, true)]
    [TestCase(eClassType.Hybrid, eCharacterClass.Bard, true)]
    [TestCase(eClassType.PureTank, eCharacterClass.Armsman, false)]
    [TestCase(eClassType.ListCaster, eCharacterClass.Valewalker, false)]
    [TestCase(eClassType.Hybrid, eCharacterClass.Paladin, false)]
    public void CastersAndHealers_RunFromFightsTheyAreLosing(eClassType type, eCharacterClass cls, bool runs)
    {
        Assert.That(AutonomousWorldTalk.Runs(type, cls), Is.EqualTo(runs));
    }

    [Test]
    public void ChannelLines_AreTaggedForTheClient()
    {
        Assert.That(RealmChatChannels.Format(RealmChatChannels.Channel.Zone, "Aldric", "  Help   at the ruins! "),
            Is.EqualTo("[Zone] Aldric: Help at the ruins!"));
        Assert.That(RealmChatChannels.Format(RealmChatChannels.Channel.Rvr, "Aldric", "Caer Benowyc is under attack!"),
            Does.StartWith("[RvR] Aldric: "));
        Assert.That(RealmChatChannels.Format(RealmChatChannels.Channel.Zone, "A", new string('x', 500)).Length,
            Is.LessThanOrEqualTo("[Zone] A: ".Length + RealmChatChannels.MaxLength));
    }

    [Test]
    public void DescribeFoes_ReadsLikeSpeech()
    {
        Assert.That(AutonomousHelpCalls.DescribeFoes(["giant spider"]), Is.EqualTo("a giant spider"));
        Assert.That(AutonomousHelpCalls.DescribeFoes(["orc grunt", "orc grunt", "orc shaman"]), Is.EqualTo("an orc grunt and 2 more"));
        Assert.That(AutonomousHelpCalls.DescribeFoes(["Bloodfang"]), Is.EqualTo("Bloodfang"));
    }

    [TestCase("thanks!", true)]
    [TestCase("Thank you so much", true)]
    [TestCase("ty", true)]
    [TestCase("hello", false)]
    public void Thanks_IsRecognised(string text, bool expected)
    {
        Assert.That(AutonomousWorldTalk.IsThanks(text), Is.EqualTo(expected));
    }

    [Test]
    public void IdleLines_HaveNoPlayerEmulation()
    {
        string[] forbidden = ["lfg", "wts", "wtb", "/send", "faction", "noob", "lol"];
        for (int i = 0; i < 300; i++)
        {
            AutonomousWorldTalk.Topic t = AutonomousWorldTalk.IdleTopic(null, i % 2 == 0 ? "bandit" : null);
            Assert.That(t.Opening, Is.Not.Empty);
            Assert.That(t.Replies, Is.Not.Empty);
            foreach (string line in t.Replies.Append(t.Opening))
            {
                Assert.That(line, Does.Not.Contain("{"), line);
                foreach (string f in forbidden)
                    Assert.That(line, Does.Not.Contain(f).IgnoreCase, line);
            }
        }
    }
}
