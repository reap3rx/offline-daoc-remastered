using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using DOL.Database;
using DOL.Database.Attributes;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace DOL.GS.DatabaseUpdate
{
    /// <summary>
    /// The story quests' reward items (scripts/storyquests/items/*.json, made by tools/claude-version/story_items.py):
    /// put into the ItemTemplate table at every start, before anything loads - added when missing, set right when a
    /// column differs. The database travels with the save, so items made here reach every copy of the world.
    /// </summary>
    [DatabaseUpdate]
    public class StoryItemsUpdate : IDatabaseUpdater
    {
        private static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        /// <summary>Equal as the database keeps them: null and "" are the same text.</summary>
        static bool Same(object a, object b) =>
            a is string || b is string ? (a as string ?? "") == (b as string ?? "") : Equals(a, b);

        public void Update()
        {
            int added = 0, changed = 0;
            Assembly asm = typeof(StoryItemsUpdate).Assembly;
            var props = typeof(DbItemTemplate).GetProperties(BindingFlags.Public | BindingFlags.Instance)
                .Where(p => p.CanWrite && p.GetCustomAttribute<DataElement>() != null)
                .ToDictionary(p => p.Name, StringComparer.OrdinalIgnoreCase);
            foreach (string res in asm.GetManifestResourceNames().Where(n => n.StartsWith("StoryItems.") && n.EndsWith(".json")))
            {
                try
                {
                    using var s = new StreamReader(asm.GetManifestResourceStream(res)!, Encoding.UTF8);
                    var rows = JsonConvert.DeserializeObject<List<Dictionary<string, JToken>>>(s.ReadToEnd());
                    foreach (var row in rows ?? new())
                    {
                        if (!row.TryGetValue("Id_nb", out JToken idTok))
                            continue;
                        string id = idTok.ToString();
                        DbItemTemplate t = GameServer.Database.FindObjectByKey<DbItemTemplate>(id);
                        bool isNew = t == null;
                        t ??= new DbItemTemplate();
                        bool diff = false;
                        foreach (var (col, val) in row)
                        {
                            if (!props.TryGetValue(col, out PropertyInfo p) || val == null || val.Type == JTokenType.Null)
                                continue;
                            object v;
                            try { v = val.ToObject(p.PropertyType); }
                            catch { continue; }
                            object cur = p.GetValue(t);
                            if (Same(cur, v))
                                continue;
                            p.SetValue(t, v);
                            if (isNew || !Same(p.GetValue(t), cur))     // (a setter that tidies it, AllowedClasses "0" -> "")
                                diff = true;
                        }
                        if (isNew)
                        {
                            t.Id_nb = id;
                            GameServer.Database.AddObject(t);
                            added++;
                        }
                        else if (diff)
                        {
                            GameServer.Database.SaveObject(t);
                            changed++;
                        }
                    }
                }
                catch (Exception ex)
                {
                    log.Error($"Story quest items: {res}", ex);
                }
            }
            if (added + changed > 0)
                log.Info($"Story quest items: {added} added, {changed} set right");
        }
    }
}
