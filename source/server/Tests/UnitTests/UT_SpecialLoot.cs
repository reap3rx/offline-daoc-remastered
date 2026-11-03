using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using DOL.Database;
using DOL.GS;
using DOL.GS.PlayerClass;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>
/// Special drops (gameutils/SpecialLoot.cs, owner 2026-11-02 "Item and weapon bonuses"): a named drop comes back as a
/// one-off with ToA bonuses from the taker's class pool, a proc, a finish; a drop the class can't use is remade for it,
/// keeping its name.
/// </summary>
[TestFixture, NonParallelizable]
public sealed class UT_SpecialLoot
{
    private static readonly IObjectDatabase EmptyDatabase =
        DispatchProxy.Create<IObjectDatabase, UT_UnobservedConcentration.EmptyReads>();
    private GameServer _previousServer;

    private sealed class InertServer : GameServer
    {
        protected override IObjectDatabase DataBaseImpl => EmptyDatabase;
    }

    private sealed class Taker : GamePlayer
    {
        public bool CanUse = true;
        public ICharacterClass Class = new ClassRanger();
        private Taker() : base(null, null) { }
        public override byte Level { get; set; }
        public override ICharacterClass CharacterClass => Class;
        public override eRealm Realm { get => eRealm.Hibernia; set { } }
        public override string Name { get => "Tester"; set { } }
        public override bool HasAbilityToUseItem(DbItemTemplate item) => CanUse;
    }

    [SetUp]
    public void SetUp()
    {
        _previousServer = GameServer.Instance;
        GameServer.LoadTestDouble((InertServer) RuntimeHelpers.GetUninitializedObject(typeof(InertServer)));
        if (!_tables)
        {
            try { GeneratedUniqueItem.InitializeHashtables(); } catch (ArgumentException) { }   // (once per process)
            _tables = true;
        }
    }

    private static bool _tables;

    [TearDown]
    public void TearDown() => GameServer.LoadTestDouble(_previousServer);

    private static Taker Player(byte level, bool canUse = true)
    {
        Taker t = (Taker) RuntimeHelpers.GetUninitializedObject(typeof(Taker));
        t.Level = level;
        t.CanUse = canUse;
        t.Class = new ClassRanger();
        return t;
    }

    private static DbItemTemplate NamedBow(int level) => new()
    {
        Id_nb = $"nu202_test_bow_l{level}", Name = "Bow of the Estuary", Level = level, Object_Type = (int) eObjectType.RecurvedBow,
        Item_Type = Slot.RANGED, Realm = 3, Model = 471, Quality = 100, MaxCount = 1, Bonus1 = 9, Bonus1Type = (int) eProperty.Dexterity,
        Bonus2 = 12, Bonus2Type = (int) eProperty.MaxHealth, DPS_AF = 12 + 3 * level, SPD_ABS = 45, Hand = 1
    };

    // the ToA properties the pools draw on (not all sit in eProperty's ToABonus_First..Last run)
    private static readonly int[] Toa =
    {
        (int) eProperty.MeleeDamage, (int) eProperty.MeleeSpeed, (int) eProperty.StyleDamage, (int) eProperty.FatigueConsumption, (int) eProperty.ResistPierce,
        (int) eProperty.SpellDamage, (int) eProperty.CastingSpeed, (int) eProperty.SpellRange, (int) eProperty.PowerPool, (int) eProperty.SpellDuration,
        (int) eProperty.DebuffEffectiveness, (int) eProperty.HealingEffectiveness, (int) eProperty.BuffEffectiveness, (int) eProperty.ArcherySpeed,
        (int) eProperty.RangedDamage, (int) eProperty.ArcheryRange, (int) eProperty.StrCapBonus, (int) eProperty.DexCapBonus, (int) eProperty.ConCapBonus,
        (int) eProperty.QuiCapBonus, (int) eProperty.AcuCapBonus, (int) eProperty.MaxHealthCapBonus, (int) eProperty.PowerPoolCapBonus
    };

    private static int[] ToaLines(DbItemTemplate u) => new[]
        {
            (u.Bonus1Type, u.Bonus1), (u.Bonus2Type, u.Bonus2), (u.Bonus3Type, u.Bonus3), (u.Bonus4Type, u.Bonus4), (u.Bonus5Type, u.Bonus5),
            (u.Bonus6Type, u.Bonus6), (u.Bonus7Type, u.Bonus7), (u.Bonus8Type, u.Bonus8), (u.Bonus9Type, u.Bonus9), (u.Bonus10Type, u.Bonus10)
        }
        .Where(b => b.Item2 > 0 && Toa.Contains(b.Item1)).Select(b => b.Item1).ToArray();

    [Test]
    public void NamedUniqueIsSpecial_PlainTemplateIsNot()
    {
        Assert.That(SpecialLoot.IsSpecial(NamedBow(30)), Is.True);
        Assert.That(SpecialLoot.IsSpecial(new DbItemTemplate { Id_nb = "nurse_cap", Name = "cap" }), Is.False, "not a named unique: no zone number");
        Assert.That(SpecialLoot.IsSpecial(new DbItemTemplate { Id_nb = "recurve_bow", Name = "recurve bow" }), Is.False);
    }

    [TestCase(10, 1, 1)]
    [TestCase(30, 1, 2)]
    [TestCase(50, 3, 3)]
    public void ANamedDropGetsClassToaBonusesByLevel(int level, int atLeast, int atMost)
    {
        DbItemTemplate t = NamedBow(level);
        DbItemTemplate u = SpecialLoot.Enrich(t, Player((byte) level), "test");
        Assert.That(u, Is.Not.SameAs(t));
        Assert.That(u, Is.InstanceOf<DbItemUnique>(), "a one-off of the template");
        Assert.That(u.Name, Is.EqualTo("Bow of the Estuary"));
        Assert.That(u.Bonus1, Is.EqualTo(9), "the drop's own stats stay");
        int[] toa = ToaLines(u);
        Assert.That(toa.Length, Is.InRange(atLeast, atMost), $"ToA lines at level {level}: {string.Join(",", toa)}");
        int[] archer = { (int) eProperty.ArcherySpeed, (int) eProperty.RangedDamage, (int) eProperty.ArcheryRange, (int) eProperty.DexCapBonus,
                         (int) eProperty.StyleDamage, (int) eProperty.MeleeDamage, (int) eProperty.QuiCapBonus, (int) eProperty.MaxHealthCapBonus,
                         (int) eProperty.FatigueConsumption };
        Assert.That(toa, Is.SubsetOf(archer), "a Ranger's pool");
        Assert.That(u.ProcSpellID, Is.Not.Zero, "a proc on every special weapon");
        Assert.That(u.ProcChance, Is.EqualTo(10));
        Assert.That(t.Bonus3, Is.Zero, "the template itself untouched");
    }

    [Test]
    public void LowLevelBonusesAreSmallerThanTopLevelOnes()
    {
        int low = 0, high = 0;
        for (int i = 0; i < 40; i++)
        {
            low += ToaAmounts(SpecialLoot.Enrich(NamedBow(10), Player(10), "t")).Sum();
            high += ToaAmounts(SpecialLoot.Enrich(NamedBow(50), Player(50), "t")).Sum();
        }
        Assert.That(low, Is.LessThan(high / 3), $"level 10 total {low} vs level 50 {high}");
    }

    private static int[] ToaAmounts(DbItemTemplate u) => new[]
        {
            (u.Bonus3Type, u.Bonus3), (u.Bonus4Type, u.Bonus4), (u.Bonus5Type, u.Bonus5), (u.Bonus6Type, u.Bonus6)
        }.Where(b => b.Item2 > 0).Select(b => b.Item2).ToArray();

    [Test]
    public void ADropTheClassCantUseIsRemadeForIt()
    {
        DbItemTemplate hammer = new()
        {
            Id_nb = "nu202_test_hammer", Name = "Maul of the Estuary", Level = 40, Object_Type = (int) eObjectType.Hammer, Item_Type = Slot.TWOHAND,
            Realm = 2, Model = 12, Quality = 100, MaxCount = 1, Description = "Lore.", Hand = 1
        };
        DbItemTemplate u = SpecialLoot.Enrich(hammer, Player(40, canUse: false), "test");
        Assert.That(u, Is.InstanceOf<GeneratedUniqueItem>(), "rolled afresh for the class");
        Assert.That(u.Name, Is.EqualTo("Maul of the Estuary"), "keeps its name");
        Assert.That(u.Description, Is.EqualTo("Lore."));
        Assert.That(u.Object_Type, Is.Not.EqualTo((int) eObjectType.Hammer), "a Ranger's weapon kind");
        Assert.That(u.Realm, Is.EqualTo((int) eRealm.Hibernia));
        Assert.That(u.Level, Is.EqualTo(40));
        Assert.That(ToaLines(u).Length, Is.InRange(2, 3), Lines(u));
    }

    private static string Lines(DbItemTemplate u) => string.Join(" ", new[]
        {
            (u.Bonus1Type, u.Bonus1), (u.Bonus2Type, u.Bonus2), (u.Bonus3Type, u.Bonus3), (u.Bonus4Type, u.Bonus4), (u.Bonus5Type, u.Bonus5),
            (u.Bonus6Type, u.Bonus6), (u.Bonus7Type, u.Bonus7), (u.Bonus8Type, u.Bonus8), (u.Bonus9Type, u.Bonus9), (u.Bonus10Type, u.Bonus10)
        }.Select(b => $"{b.Item1}:{b.Item2}"));

    [Test]
    public void EffectsMatchTheWeaponFamily()
    {
        Assert.That(SpecialLoot.EffectRange(eObjectType.Sword, true), Is.EqualTo((21, 33)));
        Assert.That(SpecialLoot.EffectRange(eObjectType.Sword, false), Is.EqualTo((1, 20)));
        Assert.That(SpecialLoot.EffectRange(eObjectType.Staff, true), Is.EqualTo((90, 94)));
        Assert.That(SpecialLoot.EffectRange(eObjectType.RecurvedBow, true), Is.EqualTo((0, 0)), "no glow rows for bows");
        DbItemTemplate sword = new() { Object_Type = (int) eObjectType.Blades, Item_Type = Slot.RIGHTHAND, Level = 50 };
        for (int i = 0; i < 20 && sword.Effect == 0; i++)
            SpecialLoot.Finish(sword, 50);
        Assert.That(sword.Effect, Is.InRange(1, 20));
        Assert.That(sword.Color, Is.Not.Zero);
    }

    [Test]
    public void MoneyAndStacksPassThrough()
    {
        DbItemTemplate arrows = new() { Id_nb = "nu202_arrows", Name = "arrows", MaxCount = 20, Level = 20 };
        Assert.That(SpecialLoot.Enrich(arrows, Player(20), "t"), Is.SameAs(arrows));
        Assert.That(SpecialLoot.Enrich(NamedBow(20), null, "t").Id_nb, Is.EqualTo("nu202_test_bow_l20"), "no player taker: as it was");
    }
}
