using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace DOL.GS.Quests
{
    /// <summary>
    /// Old quests turned off, zone by zone, as each zone is finished (the Lough Derg plan, phase 2: "Vanilla or old
    /// quests can be removed" - owner 2026-11-21). A turned-off quest is left in the database, only no longer offered:
    /// the quest cache skips it (GameObject.FillDataQuestCache), so its giver stops showing it. Anyone already on one
    /// can still finish it. runtime\server\disabled-quests.txt adds more ids (one per line, # for notes) without a build.
    /// </summary>
    public static class QuestCleanup
    {
        /// <summary>Lough Derg (2026-11-22): quests that start here but send you out of the zone, mostly at levels the
        /// zone isn't for, and three XP turn-ins for level 40+. The ones the faction stories will fold in stay on.</summary>
        static readonly (int Id, string Why)[] LoughDerg =
        {
            (344, "Vial of Moss Juice XP Item: level 40+"),
            (346, "Long White Boar Tusk XP Item: level 40+"),
            (366, "Morass Leech Blood XP Item: level 41+"),
            (20238, "Ilisa's Trade: level 40, four other zones"),
            (20317, "Magic's Scar: level 36, all outside Lough Derg"),
            (20747, "Stolen Ore B (class 50): sheevra, mermen and Bran the Giant elsewhere"),
            (20748, "Stolen Ore B (class 46)"),
            (20749, "Stolen Ore B (class 44)"),
            (20750, "Stolen Ore B (class 40)"),
            (20781, "Seek the Moonstone C (class 45): Tracker Tremain and Kern elsewhere"),
            (20782, "Seek the Moonstone C (class 41)"),
            (20783, "Seek the Moonstone C (class 48)"),
            (20784, "Seek the Moonstone C (class 49)"),
            (20904, "Search for Nasco's Spear: level 27, elsewhere"),
            (20905, "Search for Nasco's Spear (other classes)"),
            (20078, "Essence of Hostility: level 24, Rolling Stone and hill hounds elsewhere"),
            (21405, "Sheerie Mischief: level 22, elsewhere"),
            (21406, "Bria's Savior: level 24, elsewhere"),
            // Occupation of Lough Gur: Lough Gur's own story (24 class versions) - it goes back on there when that zone is done
            (21407, "Occupation of Lough Gur"), (21408, "Occupation of Lough Gur"), (21409, "Occupation of Lough Gur"),
            (21410, "Occupation of Lough Gur"), (21411, "Occupation of Lough Gur"), (21412, "Occupation of Lough Gur"),
            (21413, "Occupation of Lough Gur"), (21414, "Occupation of Lough Gur"), (21415, "Occupation of Lough Gur"),
            (21416, "Occupation of Lough Gur"), (21417, "Occupation of Lough Gur"), (21418, "Occupation of Lough Gur"),
            (21515, "Occupation of Lough Gur"), (21516, "Occupation of Lough Gur"), (21517, "Occupation of Lough Gur"),
            (21518, "Occupation of Lough Gur"), (21519, "Occupation of Lough Gur"), (21520, "Occupation of Lough Gur"),
            (21521, "Occupation of Lough Gur"), (21522, "Occupation of Lough Gur"), (21523, "Occupation of Lough Gur"),
            (21524, "Occupation of Lough Gur"), (21525, "Occupation of Lough Gur"), (21526, "Occupation of Lough Gur"),
            // Folded into the faction story arcs (2026-11-22, storyquests/quests/hib_lough_derg.json): their givers,
            // targets and best ideas live on there, written for the rebuilt zone
            (20067, "Youth Gone Wrong: now Mandra's Boy (story arc)"),
            (20812, "Balm Hunt: now Balm Hunt, The Hill War"), (20813, "Balm Hunt"), (20814, "Balm Hunt"), (20815, "Balm Hunt"), (20816, "Balm Hunt"),
            (20304, "Rhian's Dyes: now Three Kinds of Trouble, The Hill War"),
            (20302, "Balance of Nature: now Balance of Nature, The Alchemist's Garden"),
            (20306, "Beautiful Music: now Beautiful Music, The Alchemist's Garden"),
            (20068, "Kylirean's New Armor: now The Watch's New Armour, The Stolen Harvest"),
            (20866, "Lesser of Two Evils: now The Lesser of Two Evils, The Stolen Harvest"),
            (20076, "Alastriona's Chest: Hughar's part is now Hughar's Ledger; the rest sent you to three other zones"),
            (20868, "Riona's Revenge: now Riona's Revenge, Who Woke the Barrow?"),
            (20075, "Regional Distinctions: the Lough Derg part is now What the Roane Saw; the rest crossed four zones"),
        };

        /// <summary>The guards', merchants' and crafters' old tasks (/task, whisper "task") are retired: repeatable work
        /// comes from the Bounty Masters (owner 2026-11-21: "No /whisper tasks. Tasks can come from the Bounty Master").</summary>
        public static bool GuardTasksRetired = true;

        /// <summary>What a would-be task giver says instead: where the nearest Bounty Master is.</summary>
        public static bool TellAboutBounties(GamePlayer player, GameLiving giver)
        {
            if (player == null || giver == null || giver.Realm == eRealm.None)
                return false;
            BountyMasterNPC master = BountyMasterRuntime.GetMaster(player.Realm);
            foreach (GameObject o in player.CurrentRegion?.Objects ?? System.Array.Empty<GameObject>())
                if (o is BountyMasterNPC m && m.Realm == player.Realm &&
                    (master == null || player.GetDistanceTo(m) < player.GetDistanceTo(master)))
                    master = m;
            string where = master == null ? "a Bounty Master" : $"{master.Name}, the Bounty Master in {master.CurrentZone?.Description}";
            player.Out.SendMessage($"{giver.Name} says, \"We don't hand out tasks any more. Ask {where} for work.\"",
                PacketHandler.eChatType.CT_Say, PacketHandler.eChatLoc.CL_ChatWindow);
            return true;
        }

        static HashSet<int> _ids;

        public static IReadOnlyCollection<int> BuiltIn => LoughDerg.Select(q => q.Id).ToArray();

        /// <summary>Whether a data quest is turned off.</summary>
        public static bool IsDisabled(int id)
        {
            _ids ??= Load();
            return _ids.Contains(id);
        }

        public static void Reload() => _ids = Load();

        static HashSet<int> Load()
        {
            var ids = new HashSet<int>(BuiltIn);
            try
            {
                string root = GameServer.Instance?.Configuration?.RootDirectory;
                string f = root == null ? null : Path.Combine(root, "disabled-quests.txt");
                if (f != null && File.Exists(f))
                    foreach (string line in File.ReadAllLines(f))
                    {
                        string t = line.Split('#')[0].Trim();
                        if (int.TryParse(t, out int id))
                            ids.Add(id);
                    }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[QuestCleanup] {ex.Message}");
            }
            return ids;
        }
    }
}
