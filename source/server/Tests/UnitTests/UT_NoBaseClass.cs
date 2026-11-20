using DOL.Database;
using DOL.Events;
using DOL.GS;
using DOL.GS.GameEvents;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>No base classes (owner 2026-11-19: "once the character is created, they are a level 1 enchantress"): the
/// class picked at creation stays, even with the old start_as_base_class property on (an Enchantress came out a
/// Magician).</summary>
[TestFixture]
public sealed class UT_NoBaseClass
{
    [Test]
    public void ACreatedCharacterKeepsItsClass()
    {
        bool was = StartAsBaseClass.START_AS_BASE_CLASS;
        try
        {
            StartAsBaseClass.START_AS_BASE_CLASS = true;
            var ch = new DbCoreCharacter { Class = (int) eCharacterClass.Enchanter, Realm = (int) eRealm.Hibernia };
            StartAsBaseClass.OnCharacterCreation(DatabaseEvent.CharacterCreated, null, new CharacterEventArgs(ch, null));
            Assert.That(ch.Class, Is.EqualTo((int) eCharacterClass.Enchanter));
        }
        finally
        {
            StartAsBaseClass.START_AS_BASE_CLASS = was;
        }
    }
}
