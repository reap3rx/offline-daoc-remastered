using System;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// Your companion and the loot overhaul (owner 2026-11-18, the loot proposal): what it says about your novelty
    /// potions and finds, the kit token that refits its own kit at your level, and now and then a word about the piece of
    /// its kit that has fallen furthest behind ("My boots have seen better days").
    /// </summary>
    public static partial class PersonalCompanions
    {
        static readonly Dictionary<string, string[]> ReactLines = new()
        {
            ["novelty_shrink"] = ["I can see your boot laces from here, {player}.", "Mind the puddles - you might drown in one.", "Aww. Pocket-sized."],
            ["novelty_grow"] = ["Duck when we go through doors, {player}.", "Well, the monsters will see you coming now.", "Is it me, or is the sky closer?"],
            ["novelty_beast"] = ["...{player}? Is that you in there?", "If you start growling at the other beasts, I'm leaving.", "Fetch! No? Worth a try."],
            ["novelty_shadow"] = ["Quiet now - stay close and keep low.", "Shh. Follow my lead.", "Into the shadows we go."],
            ["novelty_feather"] = ["Light on your feet today!", "Don't float off without me.", "Go on, jump off something. I dare you."],
            ["novelty_glow"] = ["You're glowing, {player}. Literally.", "Handy - we'll never lose you in the dark.", "Moths are going to love you."],
            ["hiccup"] = ["Bless you? Hic-you? Whatever that was.", "Maybe stick to water for a while."],
            ["smoke"] = ["*cough* Was that supposed to happen?", "Well, that cleared the air. Or didn't."],
            ["map"] = ["A treasure map! Lead the way.", "X marks the spot - let's go dig.", "I knew today would be a good day."],
            ["heirloom"] = ["That blade's getting a story of its own.", "Your weapon remembers. Good - so will I."],
        };

        /// <summary>A line from your companion about what just happened to you (a potion, a map ...), unless it is quiet.</summary>
        public static void React(GamePlayer p, string kind)
        {
            try
            {
                if (p == null || Of(p) is not GameBot bot || !bot.IsAlive || bot.InCombat || !bot.IsWithinRadius(p, 1500) ||
                    !ReactLines.TryGetValue(kind, out string[] lines))
                    return;
                Record r = Load(p);
                if (r == null || r.Talk == "quiet")
                    return;
                string line = lines[Random.Shared.Next(lines.Length)].Replace("{player}", p.Name);
                new ECSGameTimer(bot, _ =>
                {
                    if (bot.IsAlive && bot.ObjectState == GameObject.eObjectState.Active)
                        bot.Say(line);
                    return 0;
                }, 1200 + Random.Shared.Next(1500));
            }
            catch (Exception ex)
            {
                log.Error("Companion: react", ex);
            }
        }

        /// <summary>The companion kit token: its own kit made again at your level (what you gave it and what it found stay).</summary>
        public static string RefitKit(GamePlayer p)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion to refit.";
            GameBot bot = Of(p);
            if (bot == null || !bot.IsAlive)
                return $"Call {r.Name} first - the kit is fitted on them.";
            if (bot.InCombat || p.InCombat)
                return $"{r.Name} is a bit busy right now.";
            foreach (DbInventoryItem k in Kept(p).Where(x => x.Creator == KitBy).ToList())
                GameServer.Database.DeleteObject(k);
            if (Spawn(p, r, false) is not GameBot fresh)
                return $"{r.Name} couldn't be refitted just now.";
            fresh.Say("New kit! It fits like it was made for me - because it was.");
            p.Out.SendMessage($"{r.Name}'s kit is refitted at level {p.Level}.", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            return null;
        }

        static readonly (eInventorySlot Slot, string Words)[] WishSlots =
        [
            (eInventorySlot.HeadArmor, "headgear"), (eInventorySlot.TorsoArmor, "chest pieces"), (eInventorySlot.ArmsArmor, "sleeves"),
            (eInventorySlot.HandsArmor, "gloves"), (eInventorySlot.LegsArmor, "leggings"), (eInventorySlot.FeetArmor, "boots"),
        ];
        static readonly string[] WishLines =
        [
            "My {piece} could do with replacing, {player}.", "If you come across {piece} my size, I wouldn't say no.",
            "I've patched my {piece} more times than I can count.", "I could use new {piece}, {player} - mine are older than some of these monsters.",
        ];

        /// <summary>A hint about the piece of its kit furthest behind its level (5 or more), now and then.</summary>
        static string Wish(GamePlayer p, GameBot bot)
        {
            if (bot.Inventory == null || Random.Shared.Next(3) != 0)
                return null;
            var worst = WishSlots.Select(w => (w.Words, Level: bot.Inventory.GetItem(w.Slot)?.Level ?? 0))
                .OrderBy(w => w.Level).First();
            if (bot.Level - worst.Level < 5)
                return null;
            return WishLines[Random.Shared.Next(WishLines.Length)].Replace("{piece}", worst.Words).Replace("{player}", p.Name);
        }
    }
}
