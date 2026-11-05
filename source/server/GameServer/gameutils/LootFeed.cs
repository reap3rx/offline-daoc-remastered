using System;
using DOL.Database;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// The loot feed (owner 2026-11-04: "loot that you pick up appears on a scrolling, and then disappearing graphic on
    /// the side of the screen ... the icon of the item, the name, the quality, and the sell value ... money, trash, and
    /// other currency drops ... so you don't have to look at the event window"). Whatever reaches a player's bags or
    /// purse from the world - a pickup, a group's share, a quest's or an event's reward - is told to the new client as a
    /// system line it keeps out of the chat:
    ///   "#LOOT|i|count|model|quality|sell value (copper, the whole stack)|level|con (-3 grey .. 3 purple)|kind|name"
    ///       kind: "item", "currency" (it goes to the wallet) or "trash" (worth nothing to a merchant)
    ///   "#LOOT|m|copper"
    /// The classic client hears the same text as a system line; only the new client reads it.
    /// </summary>
    public static class LootFeed
    {
        public const string Prefix = "#LOOT|";

        public static void Item(GamePlayer p, DbItemTemplate t, int count)
        {
            if (p?.Out == null || t == null || p.Client == null)
                return;
            try
            {
                count = Math.Max(1, count);
                int pack = Math.Max(1, t.PackSize);
                long value = t.Price * count / pack * ServerProperties.Properties.ITEM_SELL_RATIO / 100;
                if (t.Price == 1 && value == 0)
                    value = t.Price * count / pack;
                int level = Math.Max(0, t.Level);
                int con = ConLevels.GetConLevel(Math.Clamp((int) p.Level, 0, 50), Math.Clamp(level, 0, 99));
                string kind = PlayerWallet.IsCurrency(t.Id_nb) ? "currency" : value <= 0 ? "trash" : "item";
                string name = PlayerWallet.IsCurrency(t.Id_nb) ? PlayerWallet.NameOf(t.Id_nb) : t.Name;
                p.Out.SendMessage($"{Prefix}i|{count}|{t.Model}|{t.Quality}|{value}|{level}|{con}|{kind}|{name}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            }
            catch (Exception)
            {
                // the feed is never worth a lost item
            }
        }

        public static void Money(GamePlayer p, long copper)
        {
            if (p?.Out == null || copper <= 0 || p.Client == null)
                return;
            p.Out.SendMessage($"{Prefix}m|{copper}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        /// <summary>From InventoryLogging: what came to a player from the world (not a trade, a merchant, a house).</summary>
        internal static void FromLog(object source, object destination, eInventoryActionType type, DbItemTemplate item, int count)
        {
            if (destination is GamePlayer p && Feeds(source, type))
                Item(p, item, count);
        }

        internal static void FromLog(object source, object destination, eInventoryActionType type, long money)
        {
            if (destination is GamePlayer p && (Feeds(source, type) || (type == eInventoryActionType.Other && source is GamePlayer)))
                Money(p, money);                                     // (Other from a player: a realm kill's bounty)
        }

        private static bool Feeds(object source, eInventoryActionType type) =>
            (type == eInventoryActionType.Loot || type == eInventoryActionType.Quest) &&
            !(source is string s && s.StartsWith("(HOUSE", StringComparison.OrdinalIgnoreCase));
    }
}
