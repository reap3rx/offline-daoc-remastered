using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using DOL.Database;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// What your companion wears (owner 2026-11-11: "Finds and uses its own drops unless the player hands it something
    /// better (gear window via Interact)"). It comes dressed for its level; on the way it finds a better piece now and
    /// then and puts it on ("found"); and you can hand it something from your bags ("yours") through the gear menu - its
    /// Interact menu's GEAR, or /companion gear - and take it back the same way. What it was given or found is kept as
    /// inventory rows owned by "companion-&lt;your character id&gt;" (the item itself, moved out of your bags - the same move
    /// a trade makes), so it is still there after a restart; it wears a copy of each.
    /// </summary>
    public static partial class PersonalCompanions
    {
        const string FoundBy = "companion-find";
        static readonly Dictionary<GamePlayer, long> _lastFind = new();

        static readonly (eInventorySlot Slot, string Label)[] GearSlots =
        [
            (eInventorySlot.HeadArmor, "Head"), (eInventorySlot.TorsoArmor, "Chest"), (eInventorySlot.ArmsArmor, "Arms"),
            (eInventorySlot.HandsArmor, "Hands"), (eInventorySlot.LegsArmor, "Legs"), (eInventorySlot.FeetArmor, "Feet"),
            (eInventorySlot.Cloak, "Cloak"), (eInventorySlot.Neck, "Neck"), (eInventorySlot.Jewelry, "Gem"),
            (eInventorySlot.Waist, "Belt"), (eInventorySlot.LeftBracer, "Left wrist"), (eInventorySlot.RightBracer, "Right wrist"),
            (eInventorySlot.LeftRing, "Left ring"), (eInventorySlot.RightRing, "Right ring"),
            (eInventorySlot.RightHandWeapon, "Main hand"), (eInventorySlot.LeftHandWeapon, "Off hand / shield"),
            (eInventorySlot.TwoHandWeapon, "Two-handed"), (eInventorySlot.DistanceWeapon, "Ranged"),
        ];

        static string GearOwner(GamePlayer p) => "companion-" + p.InternalID;

        static IList<DbInventoryItem> Kept(GamePlayer p) =>
            DOLDB<DbInventoryItem>.SelectObjects(DB.Column("OwnerID").IsEqualTo(GearOwner(p)));

        static string SlotLabel(eInventorySlot slot) => GearSlots.FirstOrDefault(g => g.Slot == slot).Label ?? slot.ToString();

        static bool Fits(DbInventoryItem item, eInventorySlot slot)
        {
            int t = item.Item_Type;
            return slot switch
            {
                eInventorySlot.LeftRing or eInventorySlot.RightRing => t is (int) eInventorySlot.LeftRing or (int) eInventorySlot.RightRing,
                eInventorySlot.LeftBracer or eInventorySlot.RightBracer => t is (int) eInventorySlot.LeftBracer or (int) eInventorySlot.RightBracer,
                _ => t == (int) slot,
            };
        }

        static int ArmorLevelOf(int objectType) => (eObjectType) objectType switch
        {
            eObjectType.Cloth => 1,
            eObjectType.Leather => 2,
            eObjectType.Studded or eObjectType.Reinforced => 3,
            eObjectType.Chain or eObjectType.Scale => 4,
            eObjectType.Plate => 5,
            _ => 0,
        };

        /// <summary>Whether your companion can use it (its armour, its weapons, a shield).</summary>
        static string CantUse(GameBot bot, DbInventoryItem item)
        {
            int ot = item.Object_Type;
            if (GlobalConstants.IsArmor(ot))
            {
                string ability = bot.Realm switch
                {
                    eRealm.Albion => Abilities.AlbArmor, eRealm.Midgard => Abilities.MidArmor, _ => Abilities.HibArmor,
                };
                int can = bot.GetAbilityLevel(ability);
                if (can > 0 && ArmorLevelOf(ot) > can)
                    return $"{bot.Name} can't wear armour that heavy.";
                return null;
            }
            if ((eObjectType) ot == eObjectType.Shield)
                return bot.HasAbility(Abilities.Shield) ? null : $"{bot.Name} doesn't use a shield.";
            if (item.Item_Type is (int) eInventorySlot.RightHandWeapon or (int) eInventorySlot.LeftHandWeapon or (int) eInventorySlot.TwoHandWeapon)
                return BotWeaponStats.CanUseMelee(bot, item) ? null : $"{bot.Name} hasn't the training for that weapon.";
            return null;
        }

        /// <summary>The companion dressed in what it was given and found (a copy of each, so its own coming and going
        /// never touches the kept items).</summary>
        static void Dress(GamePlayer p, GameBot bot)
        {
            try
            {
                foreach (DbInventoryItem kept in Kept(p))
                    if (kept.Template != null)
                        bot.WearCompanionItem(Copy(kept), (eInventorySlot) kept.SlotPosition, false);
            }
            catch (Exception ex)
            {
                log.Error($"Companion: dressing {bot.Name}", ex);
            }
        }

        static DbInventoryItem Copy(DbInventoryItem kept)
        {
            GameInventoryItem c = GameInventoryItem.Create(kept.Template);
            c.Count = 1;
            c.Condition = kept.Condition;
            c.Durability = kept.Durability;
            c.Color = kept.Color;
            c.Emblem = kept.Emblem;
            return c;
        }

        static void Menu(GamePlayer p, string title, List<(string Label, string Action)> entries)
        {
            static string Clean(string s) => (s ?? "").Replace("|", "/").Replace("=", "-");
            var line = new StringBuilder("#SMENU|").Append(Clean(title));
            foreach (var (label, action) in entries)
                line.Append('|').Append(Clean(label)).Append('=').Append(Clean(action));
            NewClient.Send(p, line.ToString());
        }

        /// <summary>The gear menu: every slot and what is in it; a slot: what from your bags could go there, and taking
        /// back what you gave.</summary>
        public static string GearMenu(GamePlayer p, string slotArg)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion.";
            GameBot bot = Of(p);
            var kept = Kept(p);
            if (!int.TryParse(slotArg, out int slotNo))
            {
                var entries = new List<(string, string)>();
                foreach (var (slot, label) in GearSlots)
                {
                    DbInventoryItem worn = bot?.Inventory?.GetItem(slot);
                    DbInventoryItem k = kept.FirstOrDefault(x => x.SlotPosition == (int) slot);
                    string what = k?.Template?.Name ?? worn?.Name ?? "-";
                    string whose = k == null ? "" : k.Creator == FoundBy ? " (found)" : " (yours)";
                    entries.Add(($"{label}: {what}{whose}", "/companion gear " + (int) slot));
                }
                Menu(p, $"{r.Name}'s gear", entries);
                return null;
            }
            var at = (eInventorySlot) slotNo;
            if (GearSlots.All(g => g.Slot != at))
                return "That isn't a slot your companion uses.";
            var list = new List<(string, string)>();
            DbInventoryItem given = kept.FirstOrDefault(x => x.SlotPosition == slotNo && x.Creator != FoundBy);
            if (given != null)
                list.Add(($"Take back {given.Template?.Name}", "/companion take " + slotNo));
            int offered = 0;
            for (var bag = eInventorySlot.FirstBackpack; bag <= eInventorySlot.LastBackpack && offered < 12; bag++)
            {
                DbInventoryItem it = p.Inventory.GetItem(bag);
                if (it == null || !Fits(it, at) || (bot != null && CantUse(bot, it) != null))
                    continue;
                list.Add(($"Give {it.Name}", $"/companion give {slotNo} {(int) bag}"));
                offered++;
            }
            if (offered == 0 && given == null)
                list.Add(("(nothing in your bags fits)", "/companion gear"));
            list.Add(("Back", "/companion gear"));
            Menu(p, $"{r.Name}: {SlotLabel(at)}", list);
            return null;
        }

        /// <summary>Hand your companion something from your bags for a slot (what you gave there before comes back).</summary>
        public static string Give(GamePlayer p, string slotArg, string bagArg)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion.";
            if (!int.TryParse(slotArg, out int slotNo) || !int.TryParse(bagArg, out int bagNo) || GearSlots.All(g => (int) g.Slot != slotNo) ||
                bagNo < (int) eInventorySlot.FirstBackpack || bagNo > (int) eInventorySlot.LastBackpack)
                return "/companion gear picks what to give.";
            var slot = (eInventorySlot) slotNo;
            DbInventoryItem item = p.Inventory.GetItem((eInventorySlot) bagNo);
            if (item == null)
                return "There's nothing there.";
            if (!Fits(item, slot))
                return $"{item.Name} doesn't go there.";
            GameBot bot = Of(p);
            if (bot != null && CantUse(bot, item) is string no)
                return no;
            if (bot != null && bot.InCombat)
                return $"{r.Name} is a bit busy right now.";
            // what was given there before comes back first
            DbInventoryItem before = Kept(p).FirstOrDefault(x => x.SlotPosition == slotNo && x.Creator != FoundBy);
            if (before != null && Take(p, slotArg) is string why)
                return why;
            // the vault's move: out of your inventory without deleting it, then the row is the companion's
            p.Inventory.BeginChanges();
            bool moved = p.Inventory.RemoveItemWithoutDbDeletion(item);
            p.Inventory.CommitChanges();
            if (!moved)
                return $"You can't part with {item.Name}.";
            item.OwnerID = GearOwner(p);
            item.SlotPosition = slotNo;
            GameInventoryObjectExtensions.SaveItem(item);
            // a find in that slot goes (yours wins)
            foreach (DbInventoryItem f in Kept(p).Where(x => x.SlotPosition == slotNo && x.Creator == FoundBy).ToList())
                GameServer.Database.DeleteObject(f);
            if (bot != null && bot.IsAlive)
            {
                bot.WearCompanionItem(Copy(item), slot, true);
                bot.TurnTo(p);
                bot.Say(Pick(GivenLines, p, bot).Replace("{item}", item.Name));
            }
            p.Out.SendMessage($"You give {item.Name} to {r.Name}.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            GearMenu(p, "");
            return null;
        }

        /// <summary>Take back what you gave your companion for a slot (into your bags).</summary>
        public static string Take(GamePlayer p, string slotArg)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion.";
            if (!int.TryParse(slotArg, out int slotNo))
                return "/companion gear picks what to take back.";
            DbInventoryItem kept = Kept(p).FirstOrDefault(x => x.SlotPosition == slotNo && x.Creator != FoundBy);
            if (kept == null)
                return "You didn't give your companion anything there.";
            eInventorySlot free = p.Inventory.FindFirstEmptySlot(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);
            if (free == eInventorySlot.Invalid)
                return "Your bags are full.";
            DbInventoryItem back = kept;
            p.Inventory.BeginChanges();
            bool ok = p.Inventory.AddItemWithoutDbAddition(free, back);
            p.Inventory.CommitChanges();
            if (!ok)
                return "You couldn't take it back just now.";
            back.OwnerID = p.InternalID;
            back.SlotPosition = (int) free;
            GameInventoryObjectExtensions.SaveItem(back);
            p.Out.SendMessage($"{r.Name} hands back {back.Name}.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            // dressed again for its level in that slot
            if (Of(p) is GameBot bot && bot.IsAlive && !bot.InCombat)
                Spawn(p, r, false);
            return null;
        }

        /// <summary>Now and then, after a fight, it finds something better for itself and puts it on.</summary>
        static void MaybeFind(GamePlayer p, GameBot bot)
        {
            long now = GameLoop.GameLoopTime;
            lock (_lastFind)
            {
                if (_lastFind.TryGetValue(p, out long last) && now - last < 600_000)
                    return;
                if (Random.Shared.NextDouble() > 0.03)
                    return;
                _lastFind[p] = now;
            }
            var armor = new[] { eInventorySlot.HeadArmor, eInventorySlot.TorsoArmor, eInventorySlot.ArmsArmor,
                eInventorySlot.HandsArmor, eInventorySlot.LegsArmor, eInventorySlot.FeetArmor };
            eInventorySlot slot = armor[Random.Shared.Next(armor.Length)];
            var kept = Kept(p);
            if (kept.Any(x => x.SlotPosition == (int) slot && x.Creator != FoundBy))
                return;                                            // what you gave it stays on
            DbInventoryItem current = bot.Inventory?.GetItem(slot);
            if (current == null || !GlobalConstants.IsArmor(current.Object_Type))
                return;
            var found = new GeneratedUniqueItem(false, bot.Realm, (eCharacterClass) bot.CharacterClass.ID,
                (byte) Math.Clamp((int) bot.Level, 1, 50), (eObjectType) current.Object_Type, slot);
            if (Score(found) <= Score(current) + 2)
                return;
            found.AllowAdd = true;
            GameServer.Database.AddObject(found);
            GameInventoryItem item = GameInventoryItem.Create(found);
            item.OwnerID = GearOwner(p);
            item.SlotPosition = (int) slot;
            item.Creator = FoundBy;
            GameServer.Database.AddObject(item);
            foreach (DbInventoryItem old in kept.Where(x => x.SlotPosition == (int) slot && x.Creator == FoundBy).ToList())
                GameServer.Database.DeleteObject(old);
            bot.WearCompanionItem(Copy(item), slot, true);
            bot.Say(Pick(FoundLines, p, bot).Replace("{item}", found.Name));
        }

        static int Score(DbInventoryItem t) => t.Level * 4 + t.Bonus1 + t.Bonus2 + t.Bonus3 + t.Bonus4 + t.Bonus5 + t.Bonus6;

        static int Score(DbItemTemplate t) => t.Level * 4 + t.Bonus1 + t.Bonus2 + t.Bonus3 + t.Bonus4 + t.Bonus5 + t.Bonus6;

        static readonly string[] GivenLines =
        [
            "{item}? For me? I'll take good care of it.",
            "Oh, that's a fine thing. Thank you, {player}.",
            "{item}... I won't let you down in this.",
        ];
        static readonly string[] FoundLines =
        [
            "Look at this - {item}. Better than what I had. Mind if I keep it?",
            "Found {item} on that last one. It fits like it was made for me!",
            "Someone dropped {item}. Their loss.",
        ];
    }
}
