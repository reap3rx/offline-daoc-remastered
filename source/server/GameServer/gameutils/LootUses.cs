using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using DOL.Database;
using DOL.Events;
using DOL.GS.Commands;
using DOL.GS.PacketHandler;
using DOL.Logging;

namespace DOL.GS
{
    /// <summary>
    /// The loot overhaul's things you use (owner 2026-11-18, the loot proposal): dyes (use one: what you wear that takes it
    /// is offered; /dye), monster trophies (named after the monster, for a merchant), treasure maps (use one: a chest is
    /// marked on your map in the zone), the companion kit token (refits your companion's kit at your level), and heirloom
    /// weapons (a rare Legendary weapon that remembers its kills: +1 to its bonuses at 100, 500 and 2,000).
    /// </summary>
    public static class LootUses
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        public const string MapId = "loot_treasure_map";
        public const string KitTokenId = "valor_companion_kit";
        public const string HeirloomMark = "Heirloom";

        /// <summary>GamePlayer.UseSlot: one of these used. True when it was (used, or refused with a reason).</summary>
        public static bool TryUse(GamePlayer p, DbInventoryItem item)
        {
            if (p == null || item?.Template == null)
                return false;
            if (LootOverhaul.IsDye(item.Template))
            {
                DyeMenu(p, item);
                return true;
            }
            if (item.Id_nb == MapId)
            {
                UseMap(p, item);
                return true;
            }
            if (item.Id_nb == KitTokenId)
            {
                string why = PersonalCompanions.RefitKit(p);
                if (why != null)
                    p.Out.SendMessage(why, eChatType.CT_System, eChatLoc.CL_SystemWindow);
                else
                    p.Inventory.RemoveCountFromStack(item, 1);
                return true;
            }
            return NoveltyPotions.TryUse(p, item);
        }

        // ---------------------------------------------------------------- dyes

        static void DyeMenu(GamePlayer p, DbInventoryItem dye)
        {
            var line = new StringBuilder("#SMENU|").Append(Clean(dye.Name));
            int n = 0;
            foreach (DbInventoryItem worn in p.Inventory.EquippedItems)
            {
                if (worn?.Template == null || LootOverhaul.DyeModelFor(worn.Template) != dye.Model || !(LootOverhaul.IsWeapon(worn.Template) || LootOverhaul.IsArmor(worn.Template) || worn.Item_Type == Slot.CLOAK))
                    continue;
                line.Append('|').Append(Clean($"Dye {worn.Name}")).Append('=').Append($"/dye {dye.SlotPosition} {worn.SlotPosition}");
                n++;
            }
            if (n == 0)
            {
                string what = dye.Model == LootOverhaul.ClothDyeModel ? "cloth" : dye.Model == LootOverhaul.LeatherDyeModel ? "leather" : "metal armour or a weapon";
                p.Out.SendMessage($"You aren't wearing anything that {dye.Name} would take to - it needs {what}.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            NewClient.Send(p, line.ToString());
        }

        static string Clean(string s) => (s ?? "").Replace("|", "/").Replace("=", "-");

        /// <summary>The dye in that bag slot onto what you wear in that slot.</summary>
        public static string ApplyDye(GamePlayer p, int bagSlot, int wornSlot)
        {
            DbInventoryItem dye = p.Inventory.GetItem((eInventorySlot) bagSlot);
            DbInventoryItem worn = p.Inventory.GetItem((eInventorySlot) wornSlot);
            if (dye?.Template == null || !LootOverhaul.IsDye(dye.Template))
                return "That's not a dye.";
            if (worn?.Template == null || wornSlot >= (int) eInventorySlot.FirstBackpack)
                return "Wear what you want to dye.";
            if (LootOverhaul.DyeModelFor(worn.Template) != dye.Model)
                return $"{dye.Name} won't take to {worn.Name}.";
            worn.Color = dye.Color;
            GameInventoryObjectExtensions.SaveItem(worn);
            p.Inventory.RemoveCountFromStack(dye, 1);
            p.Out.SendInventoryItemsUpdate(new[] { worn });
            p.UpdateEquipmentAppearance();
            p.Out.SendMessage($"You dye {worn.Name}.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            return null;
        }

        // ---------------------------------------------------------------- trophies

        public static bool IsNamed(GameNPC mob)
        {
            string n = mob?.Name?.Trim() ?? "";
            return n.Length > 0 && char.IsUpper(n[0]) && mob.Realm == eRealm.None && mob is not GameBot;
        }

        static readonly Dictionary<NpcTemplateMgr.eBodyType, (string[] Parts, int Model)> TrophyParts = new()
        {
            [NpcTemplateMgr.eBodyType.Animal] = (["Pelt", "Fang", "Claw"], 100),
            [NpcTemplateMgr.eBodyType.Humanoid] = (["Insignia", "Trinket", "Token"], 485),
            [NpcTemplateMgr.eBodyType.Undead] = (["Bone", "Skull Fragment"], 103),
            [NpcTemplateMgr.eBodyType.Insect] = (["Carapace", "Mandible"], 614),
            [NpcTemplateMgr.eBodyType.Reptile] = (["Scale", "Claw"], 118),
            [NpcTemplateMgr.eBodyType.Plant] = (["Root", "Bark"], 610),
            [NpcTemplateMgr.eBodyType.Elemental] = (["Shard", "Core"], 488),
            [NpcTemplateMgr.eBodyType.Demon] = (["Horn", "Ember"], 118),
            [NpcTemplateMgr.eBodyType.Dragon] = (["Scale", "Tooth"], 118),
            [NpcTemplateMgr.eBodyType.Giant] = (["Tooth", "Knucklebone"], 106),
            [NpcTemplateMgr.eBodyType.Magical] = (["Essence", "Mote"], 488),
        };
        static readonly string[] NamedParts = ["Tusk", "Head", "Heart", "Crest", "Trophy"];
        static readonly System.Collections.Concurrent.ConcurrentDictionary<string, DbItemTemplate> _trophies = new();

        /// <summary>The monster's trophy (made the first time one drops): "Grey Wolf Pelt", "Grimwold's Tusk" - stackable,
        /// worth a little at any merchant by the monster's level.</summary>
        public static DbItemTemplate Trophy(GameNPC mob)
        {
            string name = mob.Name?.Trim();
            if (string.IsNullOrEmpty(name))
                return null;
            bool named = IsNamed(mob);
            var body = (NpcTemplateMgr.eBodyType) mob.BodyType;
            (string[] parts, int model) = TrophyParts.TryGetValue(body, out var tp) ? tp : (new[] { "Trophy", "Keepsake" }, 488);
            string part = named ? NamedParts[Math.Abs(name.GetHashCode()) % NamedParts.Length] : parts[Math.Abs(name.GetHashCode()) % parts.Length];
            string title = string.Join(" ", name.Split(' ', StringSplitOptions.RemoveEmptyEntries).Select(w => char.ToUpper(w[0]) + w[1..]));
            string full = named ? $"{title}'s {part}" : $"{title} {part}";
            string id = "trophy_" + new string(full.ToLowerInvariant().Select(c => char.IsLetterOrDigit(c) ? c : '_').ToArray());
            if (id.Length > 100)
                id = id[..100];
            if (_trophies.TryGetValue(id, out DbItemTemplate made))
                return made;
            if (GameServer.Database.FindObjectByKey<DbItemTemplate>(id) is DbItemTemplate have)
                return _trophies[id] = have;
            int level = Math.Clamp((int) mob.Level, 1, 50);
            var t = new DbItemTemplate
            {
                Id_nb = id, Name = full, Level = level, Model = model, Object_Type = (int) eObjectType.GenericItem, Item_Type = 0,
                Price = Math.Max(10, level * level * (named ? 40 : 6)), Weight = 1, Realm = 0, Quality = 100, Condition = 50_000,
                MaxCondition = 50_000, Durability = 50_000, MaxDurability = 50_000, PackSize = 1, MaxCount = 50,
                IsDropable = true, IsPickable = true, IsTradable = true, CanDropAsLoot = true,
                Description = named ? $"Proof you bested {name}. A collector at any merchant will pay for it." : $"Taken from {(name.StartsWith("the ", StringComparison.OrdinalIgnoreCase) ? name : "a " + name)}. Worth a little to any merchant.",
            };
            // (a template added here is not found again by its key until a restart: kept here, so it's added once)
            try
            {
                GameServer.Database.AddObject(t);
            }
            catch (Exception e)
            {
                log.Warn($"Trophy {id}: {e.Message}");
            }
            return _trophies[id] = t;
        }

        // ---------------------------------------------------------------- treasure maps

        public static DbItemTemplate MapTemplate() => GameServer.Database.FindObjectByKey<DbItemTemplate>(MapId);

        static void UseMap(GamePlayer p, DbInventoryItem item)
        {
            if (p.InCombat)
            {
                p.Out.SendMessage("You can't read a map in the middle of a fight!", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            TreasureChest chest = TreasureChests.PlaceForMap(p);
            if (chest == null)
            {
                p.Out.SendMessage("The map's markings don't match anything around here - try it out in the wilds.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            p.Inventory.RemoveCountFromStack(item, 1);
            double dx = chest.X - p.X, dy = chest.Y - p.Y;
            string dir = Compass(dx, dy);
            p.Out.SendMessage($"The map shows a chest about {(int) Math.Round(Math.Sqrt(dx * dx + dy * dy) / 100.0) * 100} paces {dir} of here. It's marked on your map.",
                eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            NewClient.Send(p, $"#CMARK|{chest.CurrentRegionID}|{chest.X}|{chest.Y}|{chest.Z}|Treasure");
            PersonalCompanions.React(p, "map");
        }

        static string Compass(double dx, double dy)
        {
            double a = (Math.Atan2(dx, -dy) * 180 / Math.PI + 360) % 360;   // 0 north (-y), 90 east (+x)
            string[] names = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"];
            return names[(int) Math.Round(a / 45.0) % 8];
        }

        // ---------------------------------------------------------------- heirlooms and kills

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GameLivingEvent.EnemyKilled, new DOLEventHandler(OnEnemyKilled));
        }

        static readonly int[] HeirloomSteps = [100, 500, 2000];

        static void OnEnemyKilled(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                if (sender is not GamePlayer p || args is not EnemyKilledEventArgs k || k.Target is not GameNPC mob || mob.Realm != eRealm.None)
                    return;
                ValorQuartermasters.OnKill(p, mob);
                DbInventoryItem w = p.ActiveWeapon;
                if (w?.Template is not DbItemUnique u || u.PackageID != HeirloomMark)
                    return;
                w.Experience++;
                GameInventoryObjectExtensions.SaveItem(w);
                int step = Array.IndexOf(HeirloomSteps, (int) w.Experience);
                if (step < 0)
                    return;
                (int type, int add) = GrowOne(u);
                if (type == 0)
                    return;
                GameServer.Database.SaveObject(u);
                p.ItemBonus[(eProperty) type] += add;                // (equipped now: what it adds shows at once)
                p.Out.SendUpdatePlayerSkills(true);
                p.Out.SendCharStatsUpdate();
                p.Out.SendInventoryItemsUpdate(new[] { w });
                p.Out.SendMessage($"{w.Name} remembers {w.Experience} kills - it grows stronger!", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                PersonalCompanions.React(p, "heirloom");
            }
            catch (Exception ex)
            {
                log.Error("LootUses.OnEnemyKilled", ex);
            }
        }

        /// <summary>+1 on its first bonus line (its stat or skill): (the property, 1), or (0, 0) when it has none.</summary>
        static (int, int) GrowOne(DbItemTemplate u)
        {
            if (u.Bonus1Type > 0) { u.Bonus1 += 1; return (u.Bonus1Type, 1); }
            if (u.Bonus2Type > 0) { u.Bonus2 += 1; return (u.Bonus2Type, 1); }
            if (u.Bonus3Type > 0) { u.Bonus3 += 1; return (u.Bonus3Type, 1); }
            return (0, 0);
        }

        /// <summary>A Legendary weapon now and then is an heirloom (one in ten).</summary>
        public static void MaybeHeirloom(DbItemTemplate u)
        {
            if (u == null || !LootOverhaul.IsWeapon(u) || !Util.Chance(10))
                return;
            u.PackageID = HeirloomMark;
            u.Description = $"{u.Description} Heirloom: it remembers its kills and grows stronger at 100, 500 and 2,000.".Trim();
        }
    }

    [CmdAttribute("&dye", ePrivLevel.Player, "Dye what you wear (use a dye from your bags)", "/dye <dye slot> <worn slot>")]
    public class DyeCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            if (args.Length < 3 || !int.TryParse(args[1], out int bag) || !int.TryParse(args[2], out int worn))
            {
                DisplayMessage(client, "Use a dye from your bags to pick what to dye.");
                return;
            }
            if (LootUses.ApplyDye(client.Player, bag, worn) is string why)
                DisplayMessage(client, why);
        }
    }
}
