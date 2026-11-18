using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using DOL.Database;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>
/// The loot overhaul (gameutils/LootOverhaul.cs, owner 2026-11-18): quality tiers in their shares with their words, a
/// Legendary drop's own name, forged procs and the glow that goes with them.
/// </summary>
[TestFixture, NonParallelizable]
public sealed class UT_LootOverhaul
{
    private static readonly IObjectDatabase EmptyDatabase =
        DispatchProxy.Create<IObjectDatabase, UT_UnobservedConcentration.EmptyReads>();
    private GameServer _previousServer;
    private static bool _tables;

    private sealed class InertServer : GameServer
    {
        protected override IObjectDatabase DataBaseImpl => EmptyDatabase;
    }

    [SetUp]
    public void SetUp()
    {
        _previousServer = GameServer.Instance;
        GameServer.LoadTestDouble((InertServer) RuntimeHelpers.GetUninitializedObject(typeof(InertServer)));
        if (!_tables)
        {
            try { GeneratedUniqueItem.InitializeHashtables(); } catch (ArgumentException) { }
            _tables = true;
        }
    }

    [TearDown]
    public void TearDown() => GameServer.LoadTestDouble(_previousServer);

    [Test]
    public void Tiers_RollInTheirShares()
    {
        var counts = Enum.GetValues<LootOverhaul.Tier>().ToDictionary(t => t, _ => 0);
        for (int i = 0; i < 40000; i++)
            counts[LootOverhaul.RollTier()]++;
        Assert.That(counts[LootOverhaul.Tier.Shoddy] / 40000.0, Is.EqualTo(0.30).Within(0.015));
        Assert.That(counts[LootOverhaul.Tier.Plain] / 40000.0, Is.EqualTo(0.405).Within(0.015));
        Assert.That(counts[LootOverhaul.Tier.Fine] / 40000.0, Is.EqualTo(0.20).Within(0.015));
        Assert.That(counts[LootOverhaul.Tier.Superior] / 40000.0, Is.EqualTo(0.08).Within(0.01));
        Assert.That(counts[LootOverhaul.Tier.Legendary] / 40000.0, Is.EqualTo(0.015).Within(0.005));
    }

    [Test]
    public void Apply_GivesTheTiersQualityAndWord()
    {
        int legendary = 0;
        for (int i = 0; i < 400; i++)
        {
            var g = new GeneratedUniqueItem(false, eRealm.Hibernia, eCharacterClass.Ranger, 20, eObjectType.Reinforced, eInventorySlot.TorsoArmor);
            string before = g.Name;
            LootOverhaul.Tier tier = LootOverhaul.Apply(g, null);
            Assert.That(LootOverhaul.TierOf(g.Quality), Is.EqualTo(tier), g.Name);
            if (tier == LootOverhaul.Tier.Legendary)
            {
                legendary++;
                Assert.That(g.Name.Contains("'s ") || g.Name.Contains(" of "), g.Name);
                Assert.That(g.Description, Does.Contain(before));
            }
            else if (tier == LootOverhaul.Tier.Plain)
                Assert.That(g.Name.EndsWith(before), g.Name);
            else
                Assert.That(LootOverhaul.AllWords.Contains(g.Name.Split(' ')[0]), g.Name);
        }
    }

    [Test]
    public void Forged_WeaponGlowsInItsProcsColours()
    {
        for (int i = 0; i < 200; i++)
        {
            var w = new DbItemTemplate { Object_Type = (int) eObjectType.Blades, Item_Type = (int) eInventorySlot.RightHandWeapon, Level = 30 };
            string word = LootOverhaul.Forge(w, 30, true);
            Assert.That(w.ProcSpellID, Is.GreaterThan(0));
            Assert.That(w.Effect, Is.InRange(1, 20), "a blade's glows are rows 1-20");
            char kind = LootOverhaul.KindOfProc(w.ProcSpellID);
            Assert.That(word, Is.EqualTo(kind switch { 'B' => "Blood-forged", 'R' => "Rune-forged", _ => "Spell-forged" }));
        }
        var sword = new DbItemTemplate { Object_Type = (int) eObjectType.Blades, Item_Type = (int) eInventorySlot.RightHandWeapon };
        Assert.That(LootOverhaul.GlowFor(sword, 'C'), Is.AnyOf(14, 15), "frost on a blade: its cold rows");
        Assert.That(LootOverhaul.GlowFor(sword, 'B'), Is.AnyOf(13, 18), "blood on a blade: its red rows");
    }

    [Test]
    public void ForgedArmour_IsBlessed_AndDoesntGlow()
    {
        var chest = new DbItemTemplate { Object_Type = (int) eObjectType.Leather, Item_Type = (int) eInventorySlot.TorsoArmor };
        Assert.That(LootOverhaul.Forge(chest, 22, false), Is.EqualTo("Blessed"));
        Assert.That(chest.ProcSpellID / 10 * 10, Is.AnyOf(LootOverhaul.ProcHeal, LootOverhaul.ProcAblative));
        Assert.That(chest.Effect, Is.EqualTo(0));
    }
}
