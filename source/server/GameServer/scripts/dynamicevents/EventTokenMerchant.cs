using DOL.GS.PacketHandler;

namespace DOL.GS.DynamicEvents
{
    /// <summary>
    /// A merchant who sells for Marks of Valor (owner 2026-11-02: towers held by the realm get "special merchants that sell
    /// rare goods ... good armor/weapons, things like respecs, good potions"; paid in event tokens, like GW2's karma).
    /// Marks ("event_mark", tools/claude-version/tower_stock.py) are handed out by dynamic events' rewards. The stock is
    /// an ordinary MerchantItem list; prices are counts of marks (the item templates' Price).
    /// </summary>
    public class EventTokenMerchant : GameItemCurrencyMerchant
    {
        public const string MarkId = "event_mark";
        public override string MoneyKey => MarkId;
        public string Greet;

        protected override void SendInteractMessage(GamePlayer player)
        {
            NpcSpeech.SayTo(this, player, Greet ?? "Marks of Valor buy what coin can't. Have a look.");
            player.Out.SendMessage($"{Name} sells for Marks of Valor - you earn them in events.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }
    }
}
