using System.Collections.Generic;
using DOL.Database;

namespace DOL.GS.DatabaseUpdate
{
    /// <summary>
    /// The King / Queen's summons drawn as pets, not as buffs (owner 2026-11-04: "Some of the pet spell icons share the
    /// same icon style as the buffs ... Maybe they should look more like the pet icons for other classes?"). The footman
    /// shared Might of the Cub's fist and the bowman Swift Hand's. Every summon is now a figure, as the other pet classes'
    /// are: the commanders the framed figures, the frame rising with the rank (the icons the Cabalist's simulacra use);
    /// the retainers one colour per kind - armsman brown, cleric white, scout teal on gold, sorcerer violet, wizard ice.
    /// Done here, at every start before the spells load, so it reaches every copy of the world (the database travels with
    /// the save); db-changes/2026-11-04-king-pet-icons.sql is the same change as SQL.
    /// </summary>
    [DatabaseUpdate]
    public class KingPetIconsUpdate : IDatabaseUpdater
    {
        private static readonly Logging.Logger log = Logging.LoggerManager.Create(System.Reflection.MethodBase.GetCurrentMethod().DeclaringType);

        private static IEnumerable<(int id, int icon)> Wanted()
        {
            int[] commanders = { 801, 802, 803, 804, 805 };                 // Squire .. Knight (64100-64104)
            for (int i = 0; i < 5; i++)
                yield return (64100 + i, commanders[i]);
            int[] retainers = { 101, 451, 7217, 2801, 261 };                 // armsman, cleric, scout, sorcerer, wizard
            for (int k = 0; k < 5; k++)
                for (int i = 0; i < 5; i++)
                    yield return (64110 + k * 5 + i, retainers[k]);
        }

        public void Update()
        {
            int changed = 0;
            foreach (var (id, icon) in Wanted())
            {
                DbSpell s = DOLDB<DbSpell>.SelectObject(DB.Column("SpellID").IsEqualTo(id));
                if (s == null || s.Icon == icon)
                    continue;
                s.Icon = icon;
                GameServer.Database.SaveObject(s);
                changed++;
            }
            if (changed > 0)
                log.Info($"King's summons: {changed} spell icon(s) set to pet figures");
        }
    }
}
