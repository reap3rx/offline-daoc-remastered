using System;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// Selling to your companion (owner 2026-11-13: "I want the player to have the ability to sell to them (as if you're
    /// selling it to a merchant) in the context menu. Have them say something like 'Sure, I'll sell these for you next
    /// time we're in town' (but they sell immediately to the Companion, for a slight reduction in the amount you'd make if
    /// you sold it to a merchant in town. Maybe a 10% fee."): what a merchant would pay, less a tenth, paid at once.
    /// The companion's Interact menu lists what in your bags they would take; an item's own menu has it too.
    /// </summary>
    public static partial class PersonalCompanions
    {
        const int SellFeePercent = 10;

        static readonly string[] SellLines =
        {
            "Sure, I'll sell these for you next time we're in town.",
            "Leave it with me - I know a trader who'll take it.",
            "I'll get rid of that for you. Take this for now.",
            "Into my pack it goes. The merchants and I are old friends.",
            "Done. Don't ask what I'll get for it.",
        };

        /// <summary>What a merchant would pay for it (GameMerchant.OnPlayerAppraise), before the companion's fee.</summary>
        static long MerchantValue(DbInventoryItem item)
        {
            if (item == null || !FrontierSupplyMerchantPolicy.CanSell(item))
                return 0;
            int count = Math.Max(1, item.Count);
            int pack = Math.Max(1, item.PackSize);
            long val = item.Price * count / pack * ServerProperties.Properties.ITEM_SELL_RATIO / 100;
            if (item.Price == 1 && val == 0)
                val = item.Price * count / pack;
            return val;
        }

        static long CompanionPays(DbInventoryItem item)
        {
            long val = MerchantValue(item);
            return val <= 0 ? 0 : Math.Max(1, val * (100 - SellFeePercent) / 100);
        }

        static GameBot Buyer(GamePlayer p, out string why)
        {
            why = null;
            GameBot bot = Of(p);
            if (Load(p) == null)
                why = "You have no companion.";
            else if (bot == null || bot.ObjectState != GameObject.eObjectState.Active)
                why = "Your companion isn't with you.";
            else if (!bot.IsAlive)
                why = "Your companion is in no state to haggle.";
            else if (bot.CurrentRegionID != p.CurrentRegionID || !bot.IsWithinRadius(p, 1500))
                why = $"{bot.Name} is too far away.";
            return why == null ? bot : null;
        }

        /// <summary>/companion sell [slot]: no slot - the list of what they'd take; a slot - sold to them.</summary>
        public static string Sell(GamePlayer p, string slotArg)
        {
            GameBot bot = Buyer(p, out string why);
            if (bot == null)
                return why;
            if (!int.TryParse(slotArg.TrimEnd('+'), out int slotNo))     // (from the list: "<slot>+")
                return SellMenu(p, bot);
            DbInventoryItem item = p.Inventory.GetItem((eInventorySlot) slotNo);
            if (item == null || slotNo < (int) eInventorySlot.FirstBackpack || slotNo > (int) eInventorySlot.LastBackpack)
                return "That isn't in your bags.";
            long pays = CompanionPays(item);
            if (pays <= 0)
                return $"{bot.Name} shakes {(bot.Gender == eGender.Female ? "her" : "his")} head: no one would buy the {item.Name}.";
            string name = item.Name;
            int count = Math.Max(1, item.Count);
            if (!p.Inventory.RemoveItem(item))
                return "That can't be sold.";
            InventoryLogging.LogInventoryAction(p, bot, eInventoryActionType.Merchant, item.Template, item.Count);
            p.AddMoney(pays, $"{bot.Name} takes the {(count > 1 ? count + " " : "")}{name} off your hands and gives you {{0}} " +
                $"(a tenth less than a merchant's price).", eChatType.CT_Merchant, eChatLoc.CL_SystemWindow);
            bot.TurnTo(p);
            if (DateTime.UtcNow.Ticks % 3 == 0 || !_saleSaid.TryGetValue(p, out long at) || Environment.TickCount64 - at > 60_000)
            {
                bot.Say(SellLines[Random.Shared.Next(SellLines.Length)]);
                _saleSaid[p] = Environment.TickCount64;
            }
            if (slotArg.EndsWith("+", StringComparison.Ordinal))
                SellMenu(p, bot);                       // (from the list: the list again, for the next)
            return null;
        }

        static readonly System.Collections.Concurrent.ConcurrentDictionary<GamePlayer, long> _saleSaid = new();

        static string SellMenu(GamePlayer p, GameBot bot)
        {
            var entries = new List<(string, string)>();
            for (int s = (int) eInventorySlot.FirstBackpack; s <= (int) eInventorySlot.LastBackpack && entries.Count < 40; s++)
            {
                DbInventoryItem item = p.Inventory.GetItem((eInventorySlot) s);
                long pays = CompanionPays(item);
                if (pays <= 0)
                    continue;
                string count = item.Count > 1 ? $" x{item.Count}" : "";
                entries.Add(($"{item.Name}{count}: {Money.GetShortString(pays)}", $"/companion sell {s}+"));
            }
            if (entries.Count == 0)
                return $"{bot.Name} looks through your bags: nothing worth selling.";
            Menu(p, $"Sell to {bot.Name} ({SellFeePercent}% fee)", entries);
            return null;
        }
    }
}
