using System;
using System.Linq;
using System.Reflection;
using DOL.Database;

namespace DOL.GS.DatabaseUpdate
{
    /// <summary>
    /// Items whose one-off template was never saved (SpecialLoot.Enrich, 2026-11-02 to 11-05, marked its uniques
    /// AllowAdd = false, so the named drops, event and story rewards it made were "(blank item)" after a restart): each
    /// one's unique made again from the template it came from (the part of its id before '#'), at every start. Its
    /// rolled extras (ToA stats, a proc) are gone; the item, its level and its own stats come back. A rare random drop
    /// (Unique_...) has nothing to come from and stays as it is.
    /// </summary>
    [DatabaseUpdate]
    public class LostUniquesUpdate : IDatabaseUpdater
    {
        private static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        public void Update()
        {
            try
            {
                int mended = 0;
                var rows = GameServer.Database.SelectObjects<DbInventoryItem>(DB.Column("UTemplate_Id").IsLike("%" + DbItemUnique.UNIQUE_SEPARATOR + "%"));
                foreach (string id in rows.Select(r => r.UTemplate_Id).Where(id => !string.IsNullOrEmpty(id)).Distinct())
                {
                    if (GameServer.Database.FindObjectByKey<DbItemUnique>(id) != null)
                        continue;
                    string from = id[..id.IndexOf(DbItemUnique.UNIQUE_SEPARATOR, StringComparison.Ordinal)];
                    if (GameServer.Database.FindObjectByKey<DbItemTemplate>(from) is not DbItemTemplate t || t.IsStackable)
                        continue;
                    var u = new DbItemUnique(t) { Id_nb = id, AllowAdd = true };
                    if (GameServer.Database.AddObject(u))
                        mended++;
                }
                if (mended > 0)
                    log.Info($"Lost uniques: {mended} items made whole again");
            }
            catch (Exception e)
            {
                log.Error("Lost uniques", e);
            }
        }
    }
}
