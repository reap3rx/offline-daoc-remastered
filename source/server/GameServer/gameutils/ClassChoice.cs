using System;
using System.Collections.Generic;
using System.Linq;
using DOL.Events;
using DOL.GS.Commands;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// No base classes (owner 2026-11-19: "new players, like bots, will start out as the class they choose. No more base
    /// classes. They're just not fun and will leave players at a disadvantage"). Creation only takes a real class
    /// (GlobalConstants.STARTING_CLASSES_DICT no longer lists the base classes; the Sluaghbinder is made a Sluaghbinder at
    /// once). A character still in a base class - made before this - is asked to choose on entering the game: a menu of
    /// the classes that base leads to for its race; picking one makes it that class at the level it is, as a trainer's
    /// promotion did (its specs start over, its points come back).
    /// </summary>
    public static class ClassChoice
    {
        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, new DOLEventHandler(PlayerEntered));
        }

        public static bool IsBase(GamePlayer p) => p?.CharacterClass != null && !p.CharacterClass.HasAdvancedFromBaseClass();

        /// <summary>The real classes a character in a base class can become (its base, its race).</summary>
        public static List<ICharacterClass> ChoicesFor(GamePlayer p)
        {
            var list = new List<ICharacterClass>();
            if (!IsBase(p))
                return list;
            // the Hibernian Acolyte is the old Sluaghbinder novice: that is its only way on
            if (p.Realm == eRealm.Hibernia && p.CharacterClass.ID == (int) eCharacterClass.Acolyte)
            {
                if (ScriptMgr.FindCharacterClass((int) eCharacterClass.Sluaghbinder) is ICharacterClass sl)
                    list.Add(sl);
                return list;
            }
            if (!GlobalConstants.STARTING_CLASSES_DICT.TryGetValue(p.Realm, out List<eCharacterClass> allowed))
                return list;
            foreach (eCharacterClass c in allowed.Distinct())
            {
                ICharacterClass cc = ScriptMgr.FindCharacterClass((int) c);
                if (cc == null || !cc.HasAdvancedFromBaseClass() || cc.BaseName != p.CharacterClass.Name)
                    continue;
                if (!cc.EligibleRaces.Exists(r => (int) r.ID == p.Race))
                    continue;
                if (GlobalConstants.CLASS_GENDER_CONSTRAINTS_DICT.TryGetValue(c, out eGender g) && g != p.Gender)
                    continue;
                list.Add(cc);
            }
            return list;
        }

        static void PlayerEntered(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GamePlayer p || !IsBase(p))
                return;
            new ECSGameTimer(p, _ =>
            {
                Offer(p);
                return 0;
            }, 4000);
        }

        /// <summary>The choice, as an interact-style menu (#SMENU): one line per class.</summary>
        public static void Offer(GamePlayer p)
        {
            if (p?.Client == null || !IsBase(p))
                return;
            List<ICharacterClass> choices = ChoicesFor(p);
            if (choices.Count == 0)
                return;
            var line = new System.Text.StringBuilder("#SMENU|Choose your class");
            foreach (ICharacterClass c in choices)
            {
                string name = p.Gender == eGender.Female && !string.IsNullOrEmpty(c.FemaleName) ? c.FemaleName : c.Name;
                line.Append('|').Append(name).Append("=/chooseclass ").Append(c.ID);
            }
            NewClient.Send(p, line.ToString());
            p.Out.SendMessage($"Base classes are gone: choose the class {p.Name} will be (/chooseclass shows the choices again).",
                eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        /// <summary>Become a real class. Null when done, else why not.</summary>
        public static string Choose(GamePlayer p, int classId)
        {
            if (!IsBase(p))
                return "You already have your class.";
            ICharacterClass c = ChoicesFor(p).FirstOrDefault(x => x.ID == classId);
            if (c == null)
                return "That class isn't open to you.";
            if (p.InCombat)
                return "Not while fighting.";
            if (!p.SetCharacterClass(c.ID))
                return "That didn't work.";
            p.styleComponent.RemoveAllStyles();
            p.RemoveAllAbilities();
            p.RemoveAllSpellLines();
            p.RespecAll();                                          // (the base's points come back for the class's lines)
            p.CharacterClass.OnLevelUp(p, p.Level);
            p.RefreshSpecDependantSkills(true);
            p.StartPowerRegeneration();
            p.Out.SendUpdatePlayerSkills(true);
            p.Out.SendUpdatePlayer();
            p.Out.SendMessage($"You are now a {p.CharacterClass.Name}.", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            p.SaveIntoDatabase();
            return null;
        }
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&chooseclass", ePrivLevel.Player, "Choose your class (a character still in a base class)", "/chooseclass [class id]")]
    public class ChooseClassCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            if (args.Length < 2 || !int.TryParse(args[1], out int id))
            {
                if (ClassChoice.IsBase(p))
                    ClassChoice.Offer(p);
                else
                    DisplayMessage(client, $"You are a {p.CharacterClass.Name}.");
                return;
            }
            string why = ClassChoice.Choose(p, id);
            if (why != null)
                DisplayMessage(client, why);
        }
    }
}
