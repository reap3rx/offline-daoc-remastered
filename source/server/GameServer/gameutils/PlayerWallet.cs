using System;
using System.Collections.Concurrent;
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
    /// The wallet (owner 2026-11-03: "I want inventory to not be a pain and currencies taking slots tend to be just that").
    /// Every currency the game pays in - Marks of Valor, the Darkness Falls daemon seals, aurulite, Atlantean glass,
    /// dragon scales - goes into the character's wallet instead of a backpack slot: whatever lands in the backpack
    /// (loot, event rewards, a trade, an old character's stacks at login) is moved there at once. The currency merchants
    /// (GameItemCurrencyMerchant, GameGuardMerchant) take payment from the wallet as well as the backpack. Kept on the
    /// character (DOLCharactersXCustomParam "wallet": "id=count;id=count"). The new client hears it as a "#WAL|" system
    /// line ({"Mark of Valor": 12, ...}) and shows it in the modern inventory; /wallet lists it in the chat.
    /// </summary>
    public static class PlayerWallet
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        public const string Prefix = "#WAL|";
        private const string ParamKey = "wallet";

        /// <summary>The currencies (ItemTemplate Id_nb, lower case) and the names they show under.</summary>
        public static readonly Dictionary<string, string> Currencies = new(StringComparer.OrdinalIgnoreCase)
        {
            ["event_mark"] = "Mark of Valor",
            ["diamondseal"] = "Daemon Diamond Seal",
            ["sapphireseal"] = "Daemon Sapphire Seal",
            ["emeraldseal"] = "Daemon Emerald Seal",
            ["fiery_diamond_seal"] = "Fiery Diamond Seal",
            ["freeemeraldseal"] = "Free Daemon Emerald Seal",
            ["bloodseal"] = "Blood Seal",
            ["aurulite"] = "Aurulite",
            ["atlanteanglass"] = "Atlantean Glass",
            ["dragonscales"] = "Dragon Scales",
        };

        private static readonly ConcurrentDictionary<string, Dictionary<string, int>> _wallets = new();
        private static readonly ConcurrentDictionary<string, bool> _sweepPending = new();

        public static bool IsCurrency(string idNb) => !string.IsNullOrEmpty(idNb) && Currencies.ContainsKey(idNb);

        public static string NameOf(string idNb) => Currencies.TryGetValue(idNb, out string n) ? n : idNb;

        private static Dictionary<string, int> Of(GamePlayer p)
        {
            return _wallets.GetOrAdd(p.ObjectId, _ =>
            {
                var w = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
                DbCoreCharacterXCustomParam rec = Record(p);
                foreach (string part in (rec?.Value ?? "").Split(';', StringSplitOptions.RemoveEmptyEntries))
                {
                    string[] kv = part.Split('=');
                    if (kv.Length == 2 && int.TryParse(kv[1], out int n) && n > 0)
                        w[kv[0]] = n;
                }
                return w;
            });
        }

        private static DbCoreCharacterXCustomParam Record(GamePlayer p) =>
            DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
                DB.Column("DOLCharactersObjectId").IsEqualTo(p.ObjectId).And(DB.Column("KeyName").IsEqualTo(ParamKey)));

        private static void Save(GamePlayer p, Dictionary<string, int> w)
        {
            string value = string.Join(";", w.Where(kv => kv.Value > 0).Select(kv => $"{kv.Key}={kv.Value}"));
            try
            {
                DbCoreCharacterXCustomParam rec = Record(p);
                if (rec == null)
                    GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(p.ObjectId, ParamKey, value));
                else
                {
                    rec.Value = value;
                    GameServer.Database.SaveObject(rec);
                }
            }
            catch (Exception e)
            {
                log.Error($"Wallet: could not save {p.Name}'s wallet", e);
            }
        }

        public static int Balance(GamePlayer p, string idNb)
        {
            if (p == null || !IsCurrency(idNb))
                return 0;
            var w = Of(p);
            lock (w)
                return w.TryGetValue(idNb, out int n) ? n : 0;
        }

        public static void Add(GamePlayer p, string idNb, int count)
        {
            if (p == null || count <= 0 || !IsCurrency(idNb))
                return;
            var w = Of(p);
            lock (w)
            {
                w[idNb] = (w.TryGetValue(idNb, out int n) ? n : 0) + count;
                Save(p, w);
            }
            Send(p);
        }

        /// <summary>Takes count from the wallet; false (nothing taken) when it holds less.</summary>
        public static bool Spend(GamePlayer p, string idNb, int count)
        {
            if (p == null || count <= 0)
                return count <= 0;
            var w = Of(p);
            lock (w)
            {
                int have = w.TryGetValue(idNb, out int n) ? n : 0;
                if (have < count)
                    return false;
                w[idNb] = have - count;
                Save(p, w);
            }
            Send(p);
            return true;
        }

        /// <summary>A currency merchant's price: what the backpack holds first, the rest from the wallet. False when
        /// both together hold less (nothing is taken then).</summary>
        public static bool Pay(GamePlayer p, string idNb, long total, GameObject to)
        {
            if (p == null || total <= 0)
                return total <= 0;
            lock (p.Inventory.Lock)
            {
                int inPack = p.Inventory.CountItemTemplate(idNb, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);
                if (inPack + Balance(p, idNb) < total)
                    return false;
                long removed = 0;
                var items = p.Inventory.GetItemRange(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);
                foreach (DbInventoryItem item in items)
                {
                    if (removed >= total)
                        break;
                    if (!string.Equals(item.Id_nb, idNb, StringComparison.OrdinalIgnoreCase))
                        continue;
                    int take = (int) Math.Min(item.Count, total - removed);
                    p.Inventory.RemoveCountFromStack(item, take);
                    InventoryLogging.LogInventoryAction(p, to, eInventoryActionType.Merchant, item.Template, take);
                    removed += take;
                }
                if (removed < total)
                    Spend(p, idNb, (int) (total - removed));
                return true;
            }
        }

        public static int Total(GamePlayer p, string idNb) =>
            p == null ? 0 : p.Inventory.CountItemTemplate(idNb, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack) + Balance(p, idNb);

        /// <summary>Currency items in the backpack, into the wallet (soon after an inventory change, outside its lock).</summary>
        public static void ScheduleSweep(GamePlayer p)
        {
            if (p == null || p.ObjectState != GameObject.eObjectState.Active || !_sweepPending.TryAdd(p.ObjectId, true))
                return;
            new ECSGameTimer(p, _ =>
            {
                _sweepPending.TryRemove(p.ObjectId, out bool _);
                Sweep(p);
                return 0;
            }, 50);
        }

        public static void Sweep(GamePlayer p)
        {
            if (p?.Inventory == null)
                return;
            var moved = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
            lock (p.Inventory.Lock)
            {
                foreach (DbInventoryItem item in p.Inventory.GetItemRange(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack).ToList())
                {
                    if (item == null || !IsCurrency(item.Id_nb) || item.Count <= 0)
                        continue;
                    int n = item.Count;
                    if (p.Inventory.RemoveItem(item))
                        moved[item.Id_nb] = (moved.TryGetValue(item.Id_nb, out int m) ? m : 0) + n;
                }
            }
            if (moved.Count == 0)
                return;
            var w = Of(p);
            lock (w)
            {
                foreach (var kv in moved)
                    w[kv.Key] = (w.TryGetValue(kv.Key, out int n) ? n : 0) + kv.Value;
                Save(p, w);
            }
            foreach (var kv in moved)
                p.Out.SendMessage($"{kv.Value} {NameOf(kv.Key)}{(kv.Value > 1 ? "s" : "")} into your wallet.", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
            Send(p);
        }

        public static void Send(GamePlayer p)
        {
            if (p?.Out == null)
                return;
            var w = Of(p);
            var sb = new StringBuilder("{");
            lock (w)
            {
                bool first = true;
                foreach (var kv in w.Where(kv => kv.Value > 0).OrderBy(kv => NameOf(kv.Key)))
                {
                    sb.Append(first ? "" : ",").Append('"').Append(NameOf(kv.Key).Replace("\"", "")).Append("\":").Append(kv.Value);
                    first = false;
                }
            }
            sb.Append('}');
            NewClient.Send(p, Prefix + sb);
        }

        [GameServerStartedEvent]
        public static void OnServerStart(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, new DOLEventHandler(PlayerEntered));
            GameEventMgr.AddHandler(GamePlayerEvent.Quit, new DOLEventHandler(PlayerQuit));
        }

        [GameServerStoppedEvent]
        public static void OnServerStopped(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.RemoveHandler(GamePlayerEvent.GameEntered, new DOLEventHandler(PlayerEntered));
            GameEventMgr.RemoveHandler(GamePlayerEvent.Quit, new DOLEventHandler(PlayerQuit));
        }

        private static void PlayerEntered(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GamePlayer p)
                return;
            Sweep(p);                                         // an old character's stacks of marks and seals
            Send(p);
        }

        private static void PlayerQuit(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is GamePlayer p)
                _wallets.TryRemove(p.ObjectId, out _);
        }
    }
}

namespace DOL.GS.Commands
{
    [Cmd("&wallet", ePrivLevel.Player, "Your wallet: Marks of Valor, seals and the other currencies", "/wallet")]
    public class WalletCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            var lines = PlayerWallet.Currencies.Keys.Select(k => (k, n: PlayerWallet.Balance(p, k))).Where(x => x.n > 0)
                .Select(x => $"  {PlayerWallet.NameOf(x.k)}: {x.n}").ToList();
            p.Out.SendMessage(lines.Count == 0 ? "Your wallet is empty." : "Your wallet:\n" + string.Join("\n", lines),
                eChatType.CT_System, eChatLoc.CL_SystemWindow);
            PlayerWallet.Send(p);
        }
    }
}
