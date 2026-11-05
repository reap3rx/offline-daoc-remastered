using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using DOL.Database;

namespace DOL.GS.DatabaseUpdate
{
    /// <summary>
    /// Merchants who sold another realm's goods (the public database's lists: Albion's fletcher sold Hibernia's
    /// arrows, so a scout couldn't put them in the quiver - "You cannot equip an item from another realm!", owner
    /// 2026-11-05). At every start, for each merchant list: an item of another realm
    /// becomes the same item of this realm (same name, type and slot; the closest level), or of no realm - and when
    /// there is none, a copy of it is made for this realm (id_r&lt;realm&gt;). What players already bought from those
    /// lists is changed to it too, for characters of that realm. A list shared by merchants of several realms is copied
    /// (&lt;list&gt;_r&lt;realm&gt;) for the realm whose goods it got wrong, and that realm's merchants sell from the copy.
    /// </summary>
    [DatabaseUpdate]
    public class MerchantRealmUpdate : IDatabaseUpdater
    {
        private static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        public void Update()
        {
            try
            {
                var mobsOf = new Dictionary<string, List<DbMob>>(StringComparer.OrdinalIgnoreCase);
                foreach (DbMob m in GameServer.Database.SelectObjects<DbMob>(DB.Column("ItemsListTemplateID").IsNotNull()))
                {
                    if (string.IsNullOrEmpty(m.ItemsListTemplateID))
                        continue;
                    if (!mobsOf.TryGetValue(m.ItemsListTemplateID, out var l))
                        mobsOf[m.ItemsListTemplateID] = l = new List<DbMob>();
                    l.Add(m);
                }

                var swap = new Dictionary<(string, int), string>();     // (old id, realm) -> this realm's id
                int fixedItems = 0, made = 0, dropped = 0, split = 0;
                foreach (var (list, mobs) in mobsOf)
                {
                    var realms = mobs.Select(m => (int) m.Realm).Where(r => r is 1 or 2 or 3).Distinct().ToList();
                    if (realms.Count == 0)
                        continue;
                    var items = GameServer.Database.SelectObjects<DbMerchantItem>(DB.Column("ItemListID").IsEqualTo(list));
                    bool shared = mobs.Select(m => (int) m.Realm).Distinct().Count() > 1;
                    foreach (int realm in realms)
                    {
                        // this realm's version of each thing on the list (null: it's fine as it is)
                        var to = new Dictionary<DbMerchantItem, string>();
                        foreach (DbMerchantItem mi in items)
                        {
                            DbItemTemplate t = GameServer.Database.FindObjectByKey<DbItemTemplate>(mi.ItemTemplateID);
                            if (t == null || t.Realm == 0 || t.Realm == realm)
                                continue;
                            if (!swap.TryGetValue((t.Id_nb, realm), out string twin))
                                swap[(t.Id_nb, realm)] = twin = Twin(t, realm, ref made);
                            if (twin != null)
                                to[mi] = twin;
                        }
                        if (to.Count == 0)
                            continue;
                        if (!shared)
                        {
                            // the list is this realm's alone: put it right in place
                            var have = new HashSet<string>(items.Select(i => i.ItemTemplateID), StringComparer.OrdinalIgnoreCase);
                            foreach (var (mi, twin) in to)
                            {
                                if (have.Contains(twin))
                                {
                                    GameServer.Database.DeleteObject(mi);       // (it already sells this realm's)
                                    dropped++;
                                    continue;
                                }
                                have.Add(twin);
                                mi.ItemTemplateID = twin;
                                mi.Dirty = true;
                                GameServer.Database.SaveObject(mi);
                                fixedItems++;
                            }
                            continue;
                        }
                        // merchants of several realms share it (Albion's fletcher and a Hibernian one): this realm's
                        // merchants get a copy of the list with their realm's goods
                        string mine = $"{list}_r{realm}";
                        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                        foreach (DbMerchantItem mi in items)
                        {
                            string id = to.TryGetValue(mi, out string twin) ? twin : mi.ItemTemplateID;
                            if (!seen.Add(id))
                                continue;
                            GameServer.Database.AddObject(new DbMerchantItem
                            {
                                ItemListID = mine, ItemTemplateID = id, PageNumber = mi.PageNumber, SlotPosition = mi.SlotPosition
                            });
                            fixedItems += twin != null ? 1 : 0;
                        }
                        foreach (DbMob m in mobs.Where(m => m.Realm == realm))
                        {
                            m.ItemsListTemplateID = mine;
                            GameServer.Database.SaveObject(m);
                        }
                        split++;
                    }
                }

                // what was bought from them, by characters of that realm
                int bought = 0;
                if (swap.Count > 0)
                {
                    var realmOfChar = GameServer.Database.SelectAllObjects<DbCoreCharacter>().ToDictionary(c => c.ObjectId, c => c.Realm);
                    foreach (var group in swap.Where(s => s.Value != null).GroupBy(s => s.Key.Item1))
                    {
                        var rows = GameServer.Database.SelectObjects<DbInventoryItem>(DB.Column("ITemplate_Id").IsEqualTo(group.Key));
                        foreach (DbInventoryItem it in rows)
                        {
                            if (it.OwnerID == null || !realmOfChar.TryGetValue(it.OwnerID, out int realm))
                                continue;
                            string to = group.FirstOrDefault(s => s.Key.Item2 == realm).Value;
                            if (to == null)
                                continue;
                            it.ITemplate_Id = to;
                            GameServer.Database.SaveObject(it);
                            bought++;
                        }
                    }
                }
                if (fixedItems + made + dropped + bought + split > 0)
                    log.Info($"Merchant realms: {fixedItems} goods set to their merchant's realm ({made} made for it, {dropped} doubles dropped, {split} lists copied for a realm), {bought} bought items changed");
            }
            catch (Exception e)
            {
                log.Error("Merchant realms", e);
            }
        }

        /// <summary>The same thing in this realm: by name, type and slot, of this realm or none, the closest level;
        /// else a copy of it made for the realm.</summary>
        static string Twin(DbItemTemplate t, int realm, ref int made)
        {
            var same = GameServer.Database.SelectObjects<DbItemTemplate>(DB.Column("Name").IsEqualTo(t.Name)
                    .And(DB.Column("Object_Type").IsEqualTo(t.Object_Type)).And(DB.Column("Item_Type").IsEqualTo(t.Item_Type)))
                .Where(x => x.Realm == realm || x.Realm == 0)
                .OrderBy(x => Math.Abs(x.Level - t.Level)).ThenBy(x => x.Realm == realm ? 0 : 1).ThenBy(x => x.Id_nb.Length)
                .FirstOrDefault();
            if (same != null)
                return same.Id_nb;
            string id = $"{t.Id_nb}_r{realm}";
            if (GameServer.Database.FindObjectByKey<DbItemTemplate>(id) != null)
                return id;
            var copy = new DbItemTemplate(t) { Id_nb = id, Realm = realm, AllowAdd = true };
            if (!GameServer.Database.AddObject(copy))
                return null;
            made++;
            return id;
        }
    }
}
