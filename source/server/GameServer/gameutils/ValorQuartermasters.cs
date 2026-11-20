using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using DOL.Database;
using DOL.Events;
using DOL.GS.DynamicEvents;
using DOL.GS.PacketHandler;
using DOL.GS.StoryQuests;
using DOL.Logging;

namespace DOL.GS
{
    /// <summary>
    /// A Quartermaster of Valor in every town (owner 2026-11-18, the loot proposal): sells for Marks of Valor what a solo
    /// player needs to keep current - Fine armour and weapons fitted to your class and level (in 5-level steps), healing
    /// and power potions, timed elixirs, ordinary dyes, the novelty potions, the companion kit token and a single-line
    /// respec. Marks now also come from named monsters near your level (1), every 10 kills that aren't grey (1) and story
    /// quests at your level (2, 3 from level 30); the events pay what they paid.
    /// </summary>
    public class ValorQuartermaster : EventTokenMerchant
    {
        public const string FitPrefix = "valor_fit_";

        protected override void SendInteractMessage(GamePlayer player)
        {
            NpcSpeech.SayTo(this, player, "Marks of Valor, friend? I'll fit you out - armour to your measure, potions, dyes and the odd curiosity.");
            player.Out.SendMessage($"{Name} sells for Marks of Valor: named monsters, hunting, quests and events earn them.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        public override void OnPlayerBuy(GamePlayer player, int item_slot, int number)
        {
            int page = item_slot / MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS;
            int slot = item_slot % MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS;
            DbItemTemplate t = TradeItems?.GetItem(page, (eMerchantWindowSlot) slot);
            if (t == null)
                return;
            if (!ValorQuartermasters.IsMade(t.Id_nb))
            {
                base.OnPlayerBuy(player, item_slot, number);
                return;
            }
            number = Math.Clamp(number, 1, 10);
            lock (player.Inventory.Lock)
            {
                long cost = t.Price * number;
                if (PlayerWallet.Total(player, MarkId) < cost)
                {
                    player.Out.SendMessage($"That's {cost} Mark{(cost > 1 ? "s" : "")} of Valor - you haven't enough.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                    return;
                }
                int given = 0;
                for (int i = 0; i < number; i++)
                {
                    (DbItemTemplate make, int count) = ValorQuartermasters.Make(t.Id_nb, player);
                    if (make == null)
                        break;
                    if (!player.Inventory.AddTemplate(GameInventoryItem.Create(make), count, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                    {
                        player.Out.SendMessage("Your backpack is full.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                        break;
                    }
                    player.Out.SendMessage($"You buy {(count > 1 ? count + " " : "")}{make.Name} for {t.Price} Mark{(t.Price > 1 ? "s" : "")} of Valor.", eChatType.CT_Merchant, eChatLoc.CL_SystemWindow);
                    given++;
                }
                if (given > 0)
                    PlayerWallet.Pay(player, MarkId, t.Price * given, this);
            }
        }
    }

    public static class ValorQuartermasters
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        public const string ListId = "valor_quartermaster";

        static readonly (string Id, string Name, int Price, int Model)[] Fitted =
        [
            ("valor_fit_head", "Fine helm, fitted to you", 4, 834), ("valor_fit_torso", "Fine chest armour, fitted to you", 4, 378),
            ("valor_fit_arms", "Fine sleeves, fitted to you", 4, 247), ("valor_fit_hands", "Fine gloves, fitted to you", 4, 248),
            ("valor_fit_legs", "Fine leggings, fitted to you", 4, 246), ("valor_fit_feet", "Fine boots, fitted to you", 4, 437),
            ("valor_fit_weapon", "Fine weapon, fitted to you", 6, 310),
        ];
        static readonly (string Id, string Name, int Price, int Model)[] Made =
        [
            ("valor_dye_satchel", "A satchel of dye (an ordinary colour)", 1, 229),
        ];
        static readonly (string Id, string From, string Name)[] Elixirs =
        [
            ("valor_elixir_str", "Elixir_of_Strength", "Elixir of Strength"), ("valor_elixir_con", "Elixir_of_Fortitude", "Elixir of Fortitude"),
            ("valor_elixir_dex", "Elixir_of_Dexterity", "Elixir of Dexterity"),
        ];

        public static bool IsMade(string id) => id != null && (id.StartsWith(ValorQuartermaster.FitPrefix, StringComparison.Ordinal) ||
                                                                Made.Any(m => m.Id == id));

        static MerchantTradeItems _list;

        /// <summary>The list's templates (LootOverhaulDatabase makes them at the start): the placeholders the quartermaster
        /// makes up for you, the elixirs and the respec at mark prices.</summary>
        internal static void EnsureTemplates()
        {
            foreach (var f in Fitted)
                Ensure(f.Id, f.Name, f.Price, f.Model, "Made to your class and level (in steps of five) when you buy it: a Fine piece.");
            foreach (var m in Made)
                Ensure(m.Id, m.Name, m.Price, m.Model, "Made up for you when you buy it.");
            foreach (var e in Elixirs)
            {
                if (GameServer.Database.FindObjectByKey<DbItemTemplate>(e.From) is not DbItemTemplate from)
                    continue;
                var t = GameServer.Database.FindObjectByKey<DbItemTemplate>(e.Id);
                bool fresh = t == null;                          // (a new template's key isn't empty: it has a made-up one)
                t ??= new DbItemTemplate();
                t.Id_nb = e.Id; t.Name = e.Name; t.Model = from.Model; t.Object_Type = from.Object_Type; t.Item_Type = from.Item_Type;
                t.SpellID = from.SpellID; t.Charges = from.Charges; t.MaxCharges = from.MaxCharges; t.CanUseEvery = from.CanUseEvery;
                t.Price = 2; t.Level = 1; t.Weight = from.Weight; t.Quality = 100; t.Condition = 50_000; t.MaxCondition = 50_000;
                t.Durability = 50_000; t.MaxDurability = 50_000; t.PackSize = 1; t.MaxCount = 1; t.IsDropable = true; t.IsPickable = true;
                t.IsTradable = true; t.Description = "A single stat buff for 20 minutes.";
                if (fresh) GameServer.Database.AddObject(t); else GameServer.Database.SaveObject(t);
            }
            ValorPotions.EnsureTemplates();
            if (GameServer.Database.FindObjectByKey<DbItemTemplate>("respec_single") is DbItemTemplate rs &&
                GameServer.Database.FindObjectByKey<DbItemTemplate>("valor_respec_single") == null)
            {
                var r = (DbItemTemplate) rs.Clone();
                r.Id_nb = "valor_respec_single";
                r.Price = 25;
                r.AllowAdd = true;
                GameServer.Database.AddObject(r);
            }
        }

        static void Ensure(string id, string name, int price, int model, string description)
        {
            var t = GameServer.Database.FindObjectByKey<DbItemTemplate>(id);
            bool fresh = t == null;
            t ??= new DbItemTemplate();
            t.Id_nb = id; t.Name = name; t.Price = price; t.Model = model; t.Object_Type = (int) eObjectType.GenericItem;
            t.Item_Type = 0; t.Level = 1; t.Weight = 1; t.Quality = 100; t.Condition = 50_000; t.MaxCondition = 50_000;
            t.Durability = 50_000; t.MaxDurability = 50_000; t.PackSize = 1; t.MaxCount = 1; t.Description = description;
            t.IsDropable = false; t.IsPickable = false; t.IsTradable = false; t.CanDropAsLoot = false;
            if (fresh) GameServer.Database.AddObject(t); else GameServer.Database.SaveObject(t);
        }

        static MerchantTradeItems List()
        {
            if (_list != null)
                return _list;
            var list = new MerchantTradeItems(ListId);
            int slot = 0;
            void Add(string id)
            {
                if (GameServer.Database.FindObjectByKey<DbItemTemplate>(id) is DbItemTemplate t)
                    list.AddTradeItem(slot / MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS, (eMerchantWindowSlot) (slot++ % MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS), t);
            }
            foreach (var f in Fitted) Add(f.Id);
            foreach (var m in Made) Add(m.Id);
            foreach (var e in Elixirs) Add(e.Id);
            foreach (var v in ValorPotions.Kinds) Add(v.Id);
            foreach (var k in NoveltyPotions.Kinds) Add(k.Id);
            Add(LootUses.KitTokenId);
            Add("valor_respec_single");
            _list = list;
            return list;
        }

        /// <summary>What the quartermaster makes up for this player from a placeholder: the item and how many.</summary>
        public static (DbItemTemplate, int) Make(string id, GamePlayer p)
        {
            int level = Math.Clamp(Math.Max(1, p.Level / 5 * 5), 1, 50);
            var cls = (eCharacterClass) p.CharacterClass.ID;
            eRealm realm = p.Realm is eRealm.Albion or eRealm.Midgard or eRealm.Hibernia ? p.Realm : eRealm.Albion;
            switch (id)
            {
                case "valor_heal_potions":
                    return (Potion(p.Level, "Healing"), 1);
                case "valor_power_potions":
                    return (Potion(p.Level, "Power"), 1);
                case "valor_dye_satchel":
                    return (LootOverhaul.PickDye(0, p.Level), 1);
            }
            if (!id.StartsWith(ValorQuartermaster.FitPrefix, StringComparison.Ordinal))
                return (null, 0);
            GeneratedUniqueItem g;
            if (id == "valor_fit_weapon")
            {
                eObjectType wt = realm switch
                {
                    eRealm.Midgard => GeneratedUniqueItem.GetMidgardWeapon(cls),
                    eRealm.Hibernia => GeneratedUniqueItem.GetHiberniaWeapon(cls),
                    _ => GeneratedUniqueItem.GetAlbionWeapon(cls),
                };
                g = new GeneratedUniqueItem(false, realm, cls, (byte) level, wt, GeneratedUniqueItem.GenerateItemType(wt));
            }
            else
            {
                eInventorySlot slot = id switch
                {
                    "valor_fit_head" => eInventorySlot.HeadArmor, "valor_fit_torso" => eInventorySlot.TorsoArmor,
                    "valor_fit_arms" => eInventorySlot.ArmsArmor, "valor_fit_hands" => eInventorySlot.HandsArmor,
                    "valor_fit_legs" => eInventorySlot.LegsArmor, _ => eInventorySlot.FeetArmor,
                };
                eObjectType at = realm switch
                {
                    eRealm.Midgard => GeneratedUniqueItem.GetMidgardArmorType(cls, (byte) level),
                    eRealm.Hibernia => GeneratedUniqueItem.GetHiberniaArmorType(cls, (byte) level),
                    _ => GeneratedUniqueItem.GetAlbionArmorType(cls, (byte) level),
                };
                g = new GeneratedUniqueItem(false, realm, cls, (byte) level, at, slot);
            }
            g.Quality = Util.Random(93, 95);
            g.Price = Money.SetAutoPrice(g.Level, g.Quality);
            g.Name = $"{LootOverhaul.Word(LootOverhaul.Tier.Fine, g)} {g.Name}";
            g.Condition = g.MaxCondition;
            g.AllowAdd = true;
            GameServer.Database.AddObject(g);
            return (g, 1);
        }

        static readonly Dictionary<string, List<DbItemTemplate>> _potions = new();

        /// <summary>The best healing / power potion of the world's merchants at or under your level.</summary>
        static DbItemTemplate Potion(int level, string what)
        {
            lock (_potions)
            {
                if (!_potions.TryGetValue(what, out var pool))
                {
                    pool = GameServer.Database.SelectObjects<DbItemTemplate>(DB.Column("Object_Type").IsEqualTo((int) eObjectType.Magical)
                            .And(DB.Column("Name").IsLike($"%Draught of {what}%")))
                        .Where(t => t.SpellID > 0 && !t.Id_nb.Contains('#') && !t.Id_nb.StartsWith("tw_")).OrderBy(t => t.Level).ToList();
                    if (pool.Count == 0 && GameServer.Database.FindObjectByKey<DbItemTemplate>(what == "Healing" ? "Elixir_of_Healing" : "Elixir_of_Instant_Power") is DbItemTemplate e)
                        pool.Add(e);
                    _potions[what] = pool;
                }
                return pool.LastOrDefault(t => t.Level <= level) ?? pool.FirstOrDefault();
            }
        }

        // ---------------------------------------------------------------- the quartermasters in town

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            StoryQuestManager.Finished += OnQuestFinished;
            _ = new ECSGameTimer(null, _ =>
            {
                try
                {
                    log.Info($"VALOR quartermasters: {Spawn()} in town");
                }
                catch (Exception ex)
                {
                    log.Error("Valor quartermasters failed", ex);
                }
                return 0;
            }, 18_000);
        }

        static int Spawn()
        {
            int count = 0;
            var placed = new List<(ushort Region, int X, int Y)>();
            foreach (Region region in WorldMgr.GetAllRegions())
            {
                if (region == null || region.IsHousing || region.IsRvR || region.IsInstance || region.ID == 27)
                    continue;
                var towns = new List<(int X, int Y, int Radius)>();
                foreach (DbArea area in DOLDB<DbArea>.SelectObjects(DB.Column("Region").IsEqualTo(region.ID)))
                    if (area.ClassType is "DOL.GS.Area+Circle" or "DOL.GS.Area+SafeArea")
                        towns.Add((area.X, area.Y, Math.Max(800, area.Radius)));
                if (region.IsCapitalCity)
                    foreach (DbBindPoint bind in DOLDB<DbBindPoint>.SelectObjects(DB.Column("Region").IsEqualTo(region.ID)))
                        towns.Add((bind.X, bind.Y, 3000));
                foreach (var town in towns)
                {
                    if (placed.Any(p => p.Region == region.ID && Sq(p.X - town.X) + Sq(p.Y - town.Y) < Sq(3000)))
                        continue;
                    Zone zone = region.GetZone(town.X, town.Y);
                    if (zone == null)
                        continue;
                    GameMerchant near = new[] { eRealm.Albion, eRealm.Midgard, eRealm.Hibernia }
                        .SelectMany(r => zone.GetNPCsOfZone(r))
                        .OfType<GameMerchant>()
                        .Where(m => m is not GameItemCurrencyMerchant && m.Name != "Camping Supplier" && m.TradeItems != null && m.IsAlive &&
                                    Sq(m.X - town.X) + Sq(m.Y - town.Y) <= Sq(town.Radius + 500))
                        .OrderBy(m => Sq(m.X - town.X) + Sq(m.Y - town.Y))
                        .FirstOrDefault();
                    if (near == null)
                        continue;
                    double a = near.Heading * Math.PI * 2 / 4096.0 + Math.PI / 2;
                    var q = new ValorQuartermaster
                    {
                        Name = "Quartermaster of Valor", GuildName = "Marks of Valor", Model = near.Model, Size = near.Size, Level = 40,
                        Realm = near.Realm, CurrentRegionID = near.CurrentRegionID, Heading = near.Heading,
                        X = near.X + (int) (Math.Sin(a) * 110), Y = near.Y - (int) (Math.Cos(a) * 110), Z = near.Z,
                        TradeItems = List(), Flags = near.Flags,
                    };
                    q.LoadedFromScript = true;
                    if (q.AddToWorld())
                    {
                        placed.Add((region.ID, near.X, near.Y));
                        count++;
                    }
                }
            }
            return count;
        }

        static long Sq(long v) => v * v;

        // ---------------------------------------------------------------- earning marks

        static readonly ConcurrentDictionary<GamePlayer, int> _kills = new();

        public static void Give(GamePlayer p, int marks, string why)
        {
            if (p == null || marks <= 0 || GameServer.Database.FindObjectByKey<DbItemTemplate>(EventTokenMerchant.MarkId) is not DbItemTemplate mark)
                return;
            if (p.Inventory.AddTemplate(GameInventoryItem.Create(mark), marks, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
            {
                p.Out.SendMessage($"You earn {marks} Mark{(marks > 1 ? "s" : "")} of Valor ({why}).", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                LootFeed.Item(p, mark, marks);
            }
        }

        /// <summary>A kill: a named monster near your level is a mark, and so is every tenth kill that isn't grey.</summary>
        public static void OnKill(GamePlayer p, GameNPC mob)
        {
            int con = LevelScaling.LootCon(p, mob);
            if (con <= -3)
                return;
            if (LootUses.IsNamed(mob) && con >= -1)
                Give(p, 1, $"{mob.Name} bested");
            int n = _kills.AddOrUpdate(p, 1, (_, v) => v + 1);
            if (n >= 10)
            {
                _kills[p] = 0;
                Give(p, 1, "a good hunt");
            }
        }

        static void OnQuestFinished(GamePlayer p, StoryQuest s, string ending)
        {
            try
            {
                int level = s?.Def?.Level ?? p.Level;
                if (Math.Abs(level - p.Level) <= 5)
                    Give(p, p.Level >= 30 ? 3 : 2, "a quest done");
            }
            catch (Exception e)
            {
                log.Error("Valor: quest marks", e);
            }
        }
    }
}
