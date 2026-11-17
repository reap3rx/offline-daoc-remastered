using System;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;

namespace DOL.GS.Quests
{
    /// <summary>
    /// A "Give" button for what an NPC is waiting for (owner 2026-11-16: "Need to have a way to give items to NPCs who are
    /// looking for them for bounty purposes in the controller UI ... Bandit Ears ... a button on the dialogue that says
    /// 'Give &lt;items&gt;.' and it will then take them from your inventory and give you the rewards. As it stands I have
    /// to use the mouse to drag the item to them"). Talking to an NPC that a quest step of yours sends items to (a
    /// collect or delivery step, a kill task's trade) while you carry them: it adds a line with [Give &lt;item&gt;] - a
    /// choice button in the new client's dialog, so A presses it. Picking it hands the items over one at a time exactly
    /// as dragging them onto the NPC does (GiveItem, then ReceiveItem), for as long as the NPC still wants one.
    /// </summary>
    public static class HandItemsOver
    {
        private const string GivePrefix = "Give ";
        private const int MaxPerPick = 50;

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GamePlayerEvent.InteractWith, new DOLEventHandler(OnInteract));
            GameEventMgr.AddHandler(GamePlayerEvent.Whisper, new DOLEventHandler(OnWhisper));
        }

        [GameServerStoppedEvent]
        public static void OnServerStopped(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.RemoveHandler(GamePlayerEvent.InteractWith, new DOLEventHandler(OnInteract));
            GameEventMgr.RemoveHandler(GamePlayerEvent.Whisper, new DOLEventHandler(OnWhisper));
        }

        /// <summary>The item ids this NPC takes from the player now.</summary>
        public static List<string> WantedIds(GamePlayer player, GameNPC npc)
        {
            var ids = new List<string>();
            foreach (DataQuest quest in player.QuestList.Keys.OfType<DataQuest>().ToArray())
            {
                if (quest.Step <= 0 || !string.Equals(quest.TargetName, npc.Name, StringComparison.OrdinalIgnoreCase))
                    continue;
                if (quest.StepType is DataQuest.eStepType.Collect or DataQuest.eStepType.CollectFinish)
                    ids.Add(quest.CurrentCollectItem);
                if (quest.StepType is DataQuest.eStepType.Deliver or DataQuest.eStepType.DeliverFinish)
                    ids.Add(quest.CurrentStepItemTemplate);
            }
            ids.AddRange(ClassicQuests.TradeWants(player, npc));
            return ids.Where(id => !string.IsNullOrWhiteSpace(id)).Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }

        /// <summary>Your carried items this NPC takes now (matched as the quests match them: the id contains the wanted one).</summary>
        public static List<DbInventoryItem> Carried(GamePlayer player, GameNPC npc)
        {
            List<string> ids = WantedIds(player, npc);
            if (ids.Count == 0)
                return [];
            var out_ = new List<DbInventoryItem>();
            for (eInventorySlot s = eInventorySlot.FirstBackpack; s <= eInventorySlot.LastBackpack; s++)
            {
                DbInventoryItem it = player.Inventory.GetItem(s);
                if (it != null && ids.Any(id => it.Id_nb.Contains(id, StringComparison.OrdinalIgnoreCase)))
                    out_.Add(it);
            }
            return out_;
        }

        private static void OnInteract(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                if (sender is not GamePlayer player || args is not InteractWithEventArgs touched || touched.Target is not GameNPC npc)
                    return;
                var names = Carried(player, npc).Select(i => i.Name).Distinct(StringComparer.OrdinalIgnoreCase).ToList();
                if (names.Count == 0)
                    return;
                string links = string.Join(" ", names.Select(n => $"[{GivePrefix}{n}]"));
                npc.SayTo(player, eChatLoc.CL_PopupWindow, $"Have you brought what I asked for? {links}");
            }
            catch (Exception ex)
            {
                log.Error("HandItemsOver offer failed", ex);
            }
        }

        private static void OnWhisper(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                if (sender is not GamePlayer player || args is not WhisperEventArgs whisper || whisper.Target is not GameNPC npc)
                    return;
                string text = (whisper.Text ?? string.Empty).Trim();
                if (!text.StartsWith(GivePrefix, StringComparison.OrdinalIgnoreCase))
                    return;
                string name = text[GivePrefix.Length..].Trim();
                int given = 0;
                for (int n = 0; n < MaxPerPick; n++)
                {
                    DbInventoryItem item = Carried(player, npc).FirstOrDefault(i => string.Equals(i.Name, name, StringComparison.OrdinalIgnoreCase));
                    if (item == null || !Hand(player, npc, item))
                        break;
                    given++;
                }
                if (given == 0)
                    player.Out.SendMessage($"{npc.GetName(0, true)} doesn't want that now.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            }
            catch (Exception ex)
            {
                log.Error("HandItemsOver give failed", ex);
            }
        }

        /// <summary>One item handed over as a drag onto the NPC does it (PlayerMoveItemRequestHandler): true when it went.</summary>
        private static bool Hand(GamePlayer player, GameNPC npc, DbInventoryItem item)
        {
            int before = item.Count;
            string owner = item.OwnerID;
            if (item.Count == 1)
            {
                player.Notify(GamePlayerEvent.GiveItem, player, new GiveItemEventArgs(player, npc, item));
                if (item.OwnerID == null)
                    return true;
            }
            npc.ReceiveItem(player, item);
            return item.OwnerID == null || item.OwnerID != owner || item.Count < before;
        }

        private static readonly DOL.Logging.Logger log = DOL.Logging.LoggerManager.Create(typeof(HandItemsOver));
    }
}
