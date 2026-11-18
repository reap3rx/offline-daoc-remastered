using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using DOL.Database;
using DOL.Events;
using DOL.GS.Commands;
using DOL.GS.PacketHandler;
using DOL.Logging;

namespace DOL.GS
{
    /// <summary>
    /// Novelty potions (owner 2026-11-18, the loot proposal: "Potions that have unique, fun effects that don't necessarily
    /// change gameplay"). They change how you look or move, never how strong you are:
    ///   Draught of the Wee Folk - two-thirds your size, 10 min        Giant's Brew - a third bigger, 10 min
    ///   Beast Tonic - a beast's shape from a fixed list (owner: "Fixed list, that way they don't end up something
    ///     annoyingly large or bugged looking"), 5 min                  Shadowmilk - stealth as a stealther of your level
    ///     would have it (owner: "a level 5 using it would still be caught in higher level zones"), 2 min; your companion
    ///     hides with you
    ///   Feather Draught - no falling damage and a higher jump, 5 min   Glowcap Juice - a soft glow, 15 min
    ///   Bubbling Flask - unlabelled: one of them, or a harmless backfire; a merchant names one for 5 silver (/identify)
    /// The looks are the new client's (a "#FX|kind|value|seconds" line); they end when you change region or die. Your
    /// companion has something to say about each.
    /// </summary>
    public static class NoveltyPotions
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        public sealed record Kind(string Id, string Name, int Model, int Seconds, string Description);

        public static readonly Kind[] Kinds =
        [
            new("novelty_shrink", "Draught of the Wee Folk", 554, 600, "You shrink to two-thirds of your size for 10 minutes. Changes nothing but how you look."),
            new("novelty_grow", "Giant's Brew", 605, 600, "You grow a third bigger for 10 minutes (not past the ceiling indoors). Changes nothing but how you look."),
            new("novelty_beast", "Beast Tonic", 2546, 300, "You take a beast's shape for 5 minutes - a wolf, a bear, a boar, a badger, a skeleton or a creature of your realm. Your strength is your own."),
            new("novelty_shadow", "Shadowmilk", 554, 120, "Stealth for 2 minutes, as a stealther of your level has it: monsters well above you can still find you. Attacking or being hurt ends it. Your companion hides with you."),
            new("novelty_feather", "Feather Draught", 605, 300, "For 5 minutes you jump higher and take no damage from falls."),
            new("novelty_glow", "Glowcap Juice", 2546, 900, "You glow softly in a random colour for 15 minutes - handy in dungeons."),
        ];
        public const string FlaskId = "novelty_flask";
        public const string FlaskName = "Bubbling Flask";

        // the beast shapes (monsters.json models): for everyone, and one of each realm's own
        static readonly int[] Beasts = [56, 96, 99, 572, 25];
        static readonly Dictionary<eRealm, int> RealmBeast = new() { [eRealm.Albion] = 57, [eRealm.Midgard] = 465, [eRealm.Hibernia] = 112 };
        static readonly string[] Glows = ["ffd27a", "9ad8ff", "b6ff9a", "ff9ad6", "c9a6ff", "fff4b0"];

        sealed class Active
        {
            public string Kind;
            public long Until;
        }

        static readonly ConcurrentDictionary<GamePlayer, List<Active>> _on = new();

        public static DbItemTemplate Template(string id) => GameServer.Database.FindObjectByKey<DbItemTemplate>(id);

        /// <summary>A potion for a kill's drop: one of the six, or (three times in ten) a Bubbling Flask.</summary>
        public static DbItemTemplate RandomDrop() =>
            Template(Util.Chance(30) ? FlaskId : Kinds[Util.Random(0, Kinds.Length - 1)].Id);

        public static bool Is(string idNb) => idNb == FlaskId || Kinds.Any(k => k.Id == idNb);

        /// <summary>The stealth level the potion gives (0 without it): a stealther's at your level.</summary>
        public static int StealthLevel(GameLiving who)
        {
            GamePlayer p = who as GamePlayer ?? (who is GameBot b && b.IsPersonalCompanion ? b.Owner as GamePlayer : null);
            if (p == null || !_on.TryGetValue(p, out var list))
                return 0;
            long now = GameLoop.GameLoopTime;
            lock (list)
                return list.Any(a => a.Kind == "novelty_shadow" && a.Until > now) ? who.Level : 0;
        }

        public static bool NoFallDamage(GamePlayer p)
        {
            if (p == null || !_on.TryGetValue(p, out var list))
                return false;
            long now = GameLoop.GameLoopTime;
            lock (list)
                return list.Any(a => a.Kind == "novelty_feather" && a.Until > now);
        }

        public static bool TryUse(GamePlayer p, DbInventoryItem item)
        {
            if (!Is(item.Id_nb))
                return false;
            if (!p.IsAlive)
                return true;
            string kind = item.Id_nb;
            if (kind == "novelty_beast" && p.Model != p.CreationModel)
            {
                p.Out.SendMessage("You're already in another shape.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return true;
            }
            p.Inventory.RemoveCountFromStack(item, 1);
            p.Emote(eEmote.Drink);
            if (kind == FlaskId)
            {
                if (Util.Chance(30))
                {
                    Backfire(p);
                    return true;
                }
                kind = Kinds[Util.Random(0, Kinds.Length - 1)].Id;
                if (kind == "novelty_beast" && p.Model != p.CreationModel)
                    kind = "novelty_glow";
                p.Out.SendMessage($"The flask turns out to be {Kinds.First(k => k.Id == kind).Name}!", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            }
            Start(p, kind);
            return true;
        }

        static void Backfire(GamePlayer p)
        {
            switch (Util.Random(0, 2))
            {
                case 0:
                    p.Emote(eEmote.Stagger);
                    p.Out.SendMessage("*hic!* The flask was mostly fizz. *hic!*", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
                    PersonalCompanions.React(p, "hiccup");
                    break;
                case 1:
                    foreach (GamePlayer v in p.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                        v.Out.SendSpellEffectAnimation(p, p, 4050, 0, false, 1);
                    p.Out.SendMessage("Poof! A puff of smoke, and nothing else.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
                    PersonalCompanions.React(p, "smoke");
                    break;
                default:
                    Start(p, "novelty_shrink", 60, 0.35);
                    p.Out.SendMessage("You shrink... and shrink... to a very small you, for a minute.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
                    break;
            }
        }

        /// <summary>A potion's effect on you (seconds and size: its own unless given).</summary>
        static void Start(GamePlayer p, string kind, int seconds = 0, double size = 0)
        {
            Kind k = Kinds.First(x => x.Id == kind);
            int secs = seconds > 0 ? seconds : k.Seconds;
            var list = _on.GetOrAdd(p, _ => []);
            lock (list)
            {
                // one size and one shape at a time: the new one replaces the old
                string[] group = kind is "novelty_shrink" or "novelty_grow" ? ["novelty_shrink", "novelty_grow"] : [kind];
                list.RemoveAll(a => group.Contains(a.Kind));
                list.Add(new Active { Kind = kind, Until = GameLoop.GameLoopTime + secs * 1000L });
            }
            switch (kind)
            {
                case "novelty_shrink":
                    Fx(p, "size", (size > 0 ? size : 0.67).ToString("0.00", System.Globalization.CultureInfo.InvariantCulture), secs, k.Name);
                    break;
                case "novelty_grow":
                    Fx(p, "size", "1.33", secs, k.Name);
                    break;
                case "novelty_beast":
                    int[] pool = Beasts.Concat(RealmBeast.TryGetValue(p.Realm, out int own) ? [own] : []).ToArray();
                    int beast = pool[Util.Random(0, pool.Length - 1)];
                    p.Model = (ushort) beast;                          // (the model change: you, and everyone near, see the beast)
                    Fx(p, "shape", beast.ToString(), secs, k.Name);
                    break;
                case "novelty_shadow":
                    p.Stealth(true);
                    if (PersonalCompanions.Of(p) is GameBot bot && bot.IsAlive && !bot.InCombat)
                        bot.Stealth(true);                         // (it hides with you)
                    Fx(p, "stealth", "1", secs, k.Name);
                    break;
                case "novelty_feather":
                    Fx(p, "jump", "1.6", secs, k.Name);
                    break;
                case "novelty_glow":
                    Fx(p, "glow", Glows[Util.Random(0, Glows.Length - 1)], secs, k.Name);
                    break;
            }
            PersonalCompanions.React(p, kind);
        }

        static void Fx(GamePlayer p, string what, string value, int secs, string name) =>
            NewClient.Send(p, $"#FX|{what}|{value}|{secs}|{name}");

        static void End(GamePlayer p, Active a)
        {
            switch (a.Kind)
            {
                case "novelty_shrink":
                case "novelty_grow":
                    Fx(p, "size", "1", 0, "");
                    break;
                case "novelty_beast":
                    if (p.Model != p.CreationModel)
                        p.Model = p.CreationModel;
                    Fx(p, "shape", "0", 0, "");
                    break;
                case "novelty_shadow":
                    if (p.IsStealthed)
                        p.Stealth(false);
                    if (PersonalCompanions.Of(p) is GameBot bot && bot.IsStealthed)
                        bot.Stealth(false);
                    Fx(p, "stealth", "0", 0, "");
                    break;
                case "novelty_feather":
                    Fx(p, "jump", "1", 0, "");
                    break;
                case "novelty_glow":
                    Fx(p, "glow", "", 0, "");
                    break;
            }
        }

        /// <summary>Everything worn off (a region change, a death, logging out).</summary>
        public static void EndAll(GamePlayer p)
        {
            if (p == null || !_on.TryRemove(p, out var list))
                return;
            lock (list)
                foreach (Active a in list)
                    End(p, a);
        }

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GamePlayerEvent.RegionChanged, new DOLEventHandler((ev, s, a) => EndAll(s as GamePlayer)));
            GameEventMgr.AddHandler(GameLivingEvent.Dying, new DOLEventHandler((ev, s, a) => EndAll(s as GamePlayer)));
            GameEventMgr.AddHandler(GamePlayerEvent.Quit, new DOLEventHandler((ev, s, a) => { if (s is GamePlayer qp) _on.TryRemove(qp, out _); }));
            _ = new ECSGameTimer(null, Tick, 1000);
        }

        static int Tick(ECSGameTimer t)
        {
            try
            {
                long now = GameLoop.GameLoopTime;
                foreach (var (p, list) in _on.ToArray())
                {
                    if (p.ObjectState != GameObject.eObjectState.Active)
                    {
                        _on.TryRemove(p, out _);
                        continue;
                    }
                    List<Active> done;
                    lock (list)
                    {
                        done = list.Where(a => a.Until <= now).ToList();
                        list.RemoveAll(a => a.Until <= now);
                    }
                    foreach (Active a in done)
                    {
                        End(p, a);
                        p.Out.SendMessage($"The {Kinds.First(k => k.Id == a.Kind).Name} wears off.", eChatType.CT_SpellExpires, eChatLoc.CL_SystemWindow);
                    }
                    // the stealth was broken (an attack, a hit): the looks go with it
                    lock (list)
                        if (list.Any(a => a.Kind == "novelty_shadow") && !p.IsStealthed)
                        {
                            list.RemoveAll(a => a.Kind == "novelty_shadow");
                            Fx(p, "stealth", "0", 0, "");
                        }
                }
            }
            catch (Exception ex)
            {
                log.Error("NoveltyPotions.Tick", ex);
            }
            return 1000;
        }

        /// <summary>A merchant names your Bubbling Flasks for 5 silver each: each becomes what it is (or is poured out).</summary>
        public static string Identify(GamePlayer p)
        {
            if (!p.GetNPCsInRadius(400).OfType<GameMerchant>().Any())
                return "Find a merchant first - they know their potions.";
            var flasks = p.Inventory.GetItemRange(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack).Where(i => i?.Id_nb == FlaskId).ToList();
            int count = flasks.Sum(f => f.Count);
            if (count == 0)
                return "You have no Bubbling Flasks.";
            long cost = 500L * count;
            if (p.GetCurrentMoney() < cost)
                return $"Naming {count} flask{(count > 1 ? "s" : "")} costs {Money.GetString(cost)}.";
            p.RemoveMoney(cost);
            int poured = 0;
            var named = new Dictionary<string, int>();
            foreach (DbInventoryItem f in flasks)
            {
                int n = f.Count;
                p.Inventory.RemoveCountFromStack(f, n);
                for (int i = 0; i < n; i++)
                {
                    if (Util.Chance(30)) { poured++; continue; }
                    string id = Kinds[Util.Random(0, Kinds.Length - 1)].Id;
                    named[id] = named.GetValueOrDefault(id) + 1;
                }
            }
            foreach (var (id, n) in named)
                if (Template(id) is DbItemTemplate t)
                    p.Inventory.AddTemplate(GameInventoryItem.Create(t), n, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);
            string list = string.Join(", ", named.Select(kv => $"{kv.Value} {Kinds.First(k => k.Id == kv.Key).Name}"));
            p.Out.SendMessage($"The merchant sniffs each one: {(list == "" ? "nothing worth keeping" : list)}{(poured > 0 ? $"; {poured} had gone off and are poured away" : "")}. ({Money.GetString(cost)})",
                eChatType.CT_Merchant, eChatLoc.CL_SystemWindow);
            return null;
        }
    }

    [CmdAttribute("&identify", ePrivLevel.Player, "A merchant names your Bubbling Flasks (5 silver each)", "/identify")]
    public class IdentifyCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            if (NoveltyPotions.Identify(client.Player) is string why)
                DisplayMessage(client, why);
        }
    }
}
