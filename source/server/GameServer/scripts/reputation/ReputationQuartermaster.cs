using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.GS.DynamicEvents;
using DOL.GS.PacketHandler;
using DOL.GS.StoryQuests;

namespace DOL.GS.Reputation
{
    /// <summary>
    /// A faction's quartermaster (owner 2026-11-22: extra vendor stock at Trusted, more at Honoured, "a unique item at
    /// Legend"): sells for Marks of Valor what your standing has opened - each item at your level (its level version,
    /// <c>&lt;id&gt;_lNN</c>), so it keeps up as you do. Stands beside the faction's anchor NPC (Captain Lir, Wise-Woman
    /// Brid), put there when the server starts and put back if they go.
    /// </summary>
    public class ReputationQuartermaster : EventTokenMerchant
    {
        public RepFactionDef Faction;
        public RepQuartermasterDef Def;                        // its own stock and words (a zone's extra quartermaster)
        readonly ConcurrentDictionary<GamePlayer, MerchantTradeItems> _lists = new();

        public override bool Interact(GamePlayer player)
        {
            if (Faction == null)
                return base.Interact(player);
            if (!base.Interact(player))
                return false;
            return true;
        }

        protected override void SendInteractMessage(GamePlayer player)
        {
            Rank r = ReputationService.RankWith(player, Faction);
            string say = r < Rank.Trusted
                ? $"Come back when {Faction.Name} trust you. You're {r} with us now."
                : Def?.Greet ?? Faction.Quartermaster?.Greet ?? "Have a look.";
            NpcSpeech.SayTo(this, player, say);
            player.Out.SendMessage($"{Name} sells for Marks of Valor to those {Faction.Name} trust: {r} now. " +
                (r < Rank.Legend ? $"More opens at {(Rank) Math.Max((int) Rank.Trusted, (int) r + 1)}." : "Everything is open to you."),
                eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        /// <summary>What this player may buy now: each opened item at their level.</summary>
        public MerchantTradeItems ListFor(GamePlayer player)
        {
            var list = new MerchantTradeItems(null);
            Rank r = ReputationService.RankWith(player, Faction);
            int slot = 0;
            foreach (RepStockDef s in (Def ?? Faction?.Quartermaster)?.Stock ?? new List<RepStockDef>())
            {
                if (s.Rank > r)
                    continue;
                DbItemTemplate t = PricedAtLevel(s, player.Level);
                if (t == null)
                    continue;
                list.AddTradeItem(slot / MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS,
                    (eMerchantWindowSlot) (slot % MerchantTradeItems.MAX_ITEM_IN_TRADEWINDOWS), t);
                slot++;
            }
            return list;
        }

        static readonly ConcurrentDictionary<string, DbItemTemplate> _priced = new();

        /// <summary>The item's version for this level, its price set to the stock's Marks (a copy kept in memory: the
        /// database row keeps its coin value for selling it back).</summary>
        static DbItemTemplate PricedAtLevel(RepStockDef s, int level)
        {
            DbItemTemplate t = ChainRuntimeItems.AtLevel(s.Item, level);
            if (t == null)
                return null;
            return _priced.GetOrAdd($"{t.Id_nb}/{s.Price}", _ =>
            {
                var copy = (DbItemTemplate) t.Clone();
                copy.Price = s.Price;
                return copy;
            });
        }

        public override void SendMerchantWindow(GamePlayer player)
        {
            if (Faction == null)
            {
                base.SendMerchantWindow(player);
                return;
            }
            MerchantTradeItems list = ListFor(player);
            _lists[player] = list;
            TradeItems = list;
            player.Out.SendMerchantWindow(list, eMerchantWindowType.Count);
        }

        public override void OnPlayerBuy(GamePlayer player, int item_slot, int number)
        {
            if (Faction == null)
            {
                base.OnPlayerBuy(player, item_slot, number);
                return;
            }
            if (!_lists.TryGetValue(player, out MerchantTradeItems list))
                list = ListFor(player);
            TradeItems = list;
            base.OnPlayerBuy(player, item_slot, number);
        }

        // ------------------------------------------------------------------ putting them in the world

        static readonly ConcurrentDictionary<string, ReputationQuartermaster> _spawned = new();

        /// <summary>The faction's quartermaster if standing.</summary>
        public static ReputationQuartermaster Of(RepFactionDef f) =>
            f != null && _spawned.TryGetValue(f.Key, out var m) && m.ObjectState == GameObject.eObjectState.Active ? m : null;

        /// <summary>Every 30 s until all stand (their anchors may come into the world later), then every 5 minutes.</summary>
        public static void StartSpawning() => _ = new ECSGameTimer(null, _ => SpawnMissing() ? 300_000 : 30_000, 20_000);

        /// <summary>Each faction's quartermaster beside its anchor, when the anchor is there and they are not. True when
        /// every one stands.</summary>
        public static bool SpawnMissing()
        {
            bool all = true;
            foreach ((RepFactionDef f, RepQuartermasterDef q, string key) in Wanted())
            {
                if (_spawned.TryGetValue(key, out var old) && old.ObjectState == GameObject.eObjectState.Active)
                    continue;
                try
                {
                    GameNPC anchor = StoryQuestManager.Npc(q.Anchor);
                    if (anchor == null || anchor.CurrentRegion == null)
                    {
                        all = false;
                        continue;
                    }
                    var m = new ReputationQuartermaster { Faction = f, Def = q, Greet = q.Greet };
                    m.Name = q.Name;
                    m.GuildName = q.Guild ?? f.Short;
                    m.Level = 40;
                    m.Model = q.Model;
                    m.Size = 50;
                    double ox = q.Offset != null && q.Offset.Length > 0 ? q.Offset[0] : 3;
                    double oy = q.Offset != null && q.Offset.Length > 1 ? q.Offset[1] : 3;
                    m.X = anchor.X + (int) Math.Round(ox * 40);
                    m.Y = anchor.Y + (int) Math.Round(oy * 40);
                    m.Z = anchor.Z;
                    m.Heading = anchor.Heading;
                    m.CurrentRegion = anchor.CurrentRegion;
                    m.Realm = (eRealm) f.ZoneDef.Realm;
                    m.Flags |= GameNPC.eFlags.PEACE;
                    m.RespawnInterval = -1;
                    m.LoadedFromScript = true;
                    m.TradeItems = new MerchantTradeItems(null);
                    if (m.AddToWorld())
                    {
                        _spawned[key] = m;
                        Console.WriteLine($"[Reputation] {q.Name} stands by {anchor.Name} ({m.CurrentRegionID} {m.X} {m.Y})");
                    }
                    else
                        all = false;
                }
                catch (Exception e)
                {
                    all = false;
                    Console.WriteLine($"[Reputation] quartermaster {q.Name}: {e.Message}");
                }
            }
            return all;
        }

        /// <summary>Every quartermaster there should be: each faction's own (once, in its home zone), and each zone's extra
        /// ones (keyed faction@zone).</summary>
        public static IEnumerable<(RepFactionDef F, RepQuartermasterDef Q, string Key)> Wanted()
        {
            foreach (RepFactionDef f in RepDefs.AllFactions)
                if (f.Quartermaster != null)
                    yield return (f, f.Quartermaster, f.Key);
            foreach (RepZoneDef z in RepDefs.Zones)
                foreach (RepZoneQuartermasterDef q in z.Quartermasters)
                    if (z.Faction(q.Faction) is RepFactionDef f)
                        yield return (f, q, $"{f.Key}@{z.Zone}");
        }
    }

    /// <summary>An item's level version (as events and stories pay them).</summary>
    public static class ChainRuntimeItems
    {
        public static DbItemTemplate AtLevel(string id, int level) => StageRuntime.ItemAtLevel(id, level);
    }
}
