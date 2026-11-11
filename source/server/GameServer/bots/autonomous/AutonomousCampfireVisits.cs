using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.Database;
using OfflineDaoc.Population;

namespace DOL.GS;

/// <summary>
/// Bots and campfires (owner 2026-11-11: "Bots should want to come sit by campfires when they see them in the world and
/// chat with the players or each other while they do. They won't always chat, some will sit for the buffs and then just
/// leave, but others might hang out for a while. Bots will want to buy and use campfires if they can"):
///   - a solo bot that sees a fire (within 2500 units, out of combat) may walk over and sit - by its persona: a grouper
///     or a casual likes company, a tryhard seldom stops - for the minute that warms it, then leaves, or lingers a few
///     minutes if it is sociable or chatty;
///   - bots at a fire talk now and then (more the chattier they are), and greet a player who sits with them;
///   - a bot with a kit that rests out in the field may build a fire (and hang its pot), and bots buy kits when they
///     visit a merchant and have the coin to spare.
/// The controller asks Hold(bot) each turn while the bot is out of combat; a visit owns the bot's movement until it
/// ends. Combat ends it at once.
/// </summary>
public static class AutonomousCampfireVisits
{
    public const int NoticeRange = 2500;
    public const int SeatRadius = 200;

    private sealed class Visit
    {
        public CampObject Fire;
        public long SatAt;                      // when it reached its seat (0: walking)
        public long LeaveAt;
        public Vector3 Seat;
        public long StartedAt;
    }

    private static readonly ConcurrentDictionary<long, Visit> Visits = new();
    private static readonly ConcurrentDictionary<(int Fire, long Bot), bool> Considered = new();
    private static readonly ConcurrentDictionary<long, long> LastWarmed = new();
    private static readonly ConcurrentDictionary<long, long> NextBuildCheck = new();
    private static readonly ConcurrentDictionary<int, long> NextChatter = new();
    private static readonly ConcurrentDictionary<(int Fire, string Player), bool> Greeted = new();
    private static readonly Random Rng = new();

    public static bool IsVisiting(GameBot bot) => bot != null && Visits.ContainsKey(bot.DatabaseID);

    public static void NoteWarmed(GameLiving who)
    {
        if (who is GameBot b)
            LastWarmed[b.DatabaseID] = GameLoop.GameLoopTime;
    }

    private static bool Eligible(GameBot b) =>
        b != null && b.IsAutonomousWorldBot && !b.IsTemporaryGroupHelper && b.PersistentRecord != null && b.Group == null &&
        b.IsAlive && !b.InCombat && !b.IsCasting && b.ObjectState == GameObject.eObjectState.Active &&
        !b.IsOnHorse && !b.IsOnStableMasterRoute && !b.IsPlayerLedGroup;

    /// <summary>Every 5 s (CampingSupplies' tick): visits begin, and resting bots with kits may build fires.</summary>
    public static void Tick(CampObject[] fires)
    {
        long now = GameLoop.GameLoopTime;
        foreach (var (id, v) in Visits.ToArray())
            if (v.Fire.ObjectState != GameObject.eObjectState.Active || now >= v.LeaveAt || now - v.StartedAt > 12 * 60_000)
            {
                if (AutonomousBotRegistry.TryGet(id, out GameBot gone))
                    End(gone);
                else
                    Visits.TryRemove(id, out _);
            }
        foreach (CampObject fire in fires)
        {
            foreach (GameNPC n in fire.GetNPCsInRadius(NoticeRange))
            {
                if (n is not GameBot bot || !Eligible(bot) || Visits.ContainsKey(bot.DatabaseID))
                    continue;
                if (!Considered.TryAdd((fire.ObjectID, bot.DatabaseID), true))
                    continue;                                       // (it decides once per fire)
                BotPersona p = AutonomousPopulationController.PersonaOf(bot.PersistentRecord);
                double chance = p.SocialKind switch { "group" => 0.75, "solo" => 0.3, _ => 0.5 };
                if (p.Tier == BotPersona.Casual) chance += 0.1;
                if (p.Tier == BotPersona.Tryhard) chance -= 0.3;
                if (LastWarmed.TryGetValue(bot.DatabaseID, out long warmed) && now - warmed < 25 * 60_000)
                    chance *= 0.15;                                 // (still warm from the last fire)
                if (fire.BuiltBy == bot.Name)
                    chance = 1.0;
                if (Rng.NextDouble() >= chance)
                    continue;
                double angle = (bot.DatabaseID * 2.399963) % (Math.PI * 2);   // its own seat round the ring
                double linger = p.SocialKind == "group" || p.Chat > 60
                    ? 120 + Rng.Next(240)
                    : p.Tier == BotPersona.Tryhard ? Rng.Next(10) : Rng.Next(40);
                Visits[bot.DatabaseID] = new Visit
                {
                    Fire = fire,
                    Seat = new Vector3(fire.X + (float)(Math.Sin(angle) * SeatRadius), fire.Y + (float)(Math.Cos(angle) * SeatRadius), fire.Z),
                    StartedAt = now,
                    LeaveAt = long.MaxValue,                        // (set when it sits: the minute, then its linger)
                };
                _lingerSeconds[bot.DatabaseID] = CampingSupplies.SitSecondsNeeded + 8 + linger;
            }
        }
        foreach (var (id, v) in Visits.ToArray())                  // (players who came along since see them seated)
            if (v.SatAt > 0 && AutonomousBotRegistry.TryGet(id, out GameBot seated))
                ShowSitting(seated, true);
        foreach (var key in Considered.Keys.Where(k => fires.All(f => f.ObjectID != k.Fire)).ToArray())
            Considered.TryRemove(key, out _);
        foreach (var key in Greeted.Keys.Where(k => fires.All(f => f.ObjectID != k.Fire)).ToArray())
            Greeted.TryRemove(key, out _);
        TryBuildFires(fires, now);
    }

    private static readonly ConcurrentDictionary<long, double> _lingerSeconds = new();

    /// <summary>The controller's turn: true while the bot is walking to or sitting at a fire (it owns movement).</summary>
    public static bool Hold(GameBot bot)
    {
        if (bot == null || !Visits.TryGetValue(bot.DatabaseID, out Visit v))
            return false;
        long now = GameLoop.GameLoopTime;
        if (v.Fire.ObjectState != GameObject.eObjectState.Active || now >= v.LeaveAt || bot.InCombat || bot.Group != null)
        {
            if (v.SatAt > 0 && now >= v.LeaveAt && now - v.SatAt > 100_000 && !bot.InCombat && Rng.NextDouble() < 0.6)
                bot.Say(Farewell());                                // (a long sit ends with a goodbye)
            End(bot);
            return false;
        }
        float dx = bot.X - v.Seat.X, dy = bot.Y - v.Seat.Y;
        if (v.SatAt == 0)
        {
            if (dx * dx + dy * dy > 90 * 90)
            {
                if (!bot.IsMoving || now - v.StartedAt < 1000)
                    bot.PathTo(v.Seat, bot.MaxSpeed);
                Status(bot, "Walking to a campfire", $"Heading for the warmth of a campfire built by {v.Fire.BuiltBy}");
                if (now - v.StartedAt > 3 * 60_000)
                    End(bot);                                       // (no way there)
                return true;
            }
            bot.StopMovingOnPath();
            bot.StopMoving();
            bot.TurnTo(v.Fire);
            v.SatAt = now;
            ShowSitting(bot, true);
            v.LeaveAt = now + (long)(_lingerSeconds.GetValueOrDefault(bot.DatabaseID, 75) * 1000);
        }
        if (!bot.IsRecoveryResting)
            bot.BeginRecoveryRest();
        Status(bot, "Sitting by a campfire", "Taking the warmth of the fire before moving on");
        return true;
    }

    private static void End(GameBot bot)
    {
        if (Visits.TryRemove(bot.DatabaseID, out Visit v) && v.SatAt > 0)
            ShowSitting(bot, false);
        _lingerSeconds.TryRemove(bot.DatabaseID, out _);
        bot.WakeRecoveryRest();
    }

    /// <summary>The new client draws the bot seated (#SIT|oid|1) - GameBots have no sitting state of their own.</summary>
    private static void ShowSitting(GameBot bot, bool on)
    {
        foreach (GamePlayer p in bot.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
            NewClient.Send(p, $"#SIT|{bot.ObjectID}|{(on ? 1 : 0)}");
    }

    private static void Status(GameBot bot, string activity, string progress)
    {
        if (bot.PersistentRecord == null || bot.PersistentRecord.Activity == activity)
            return;
        bot.PersistentRecord.Activity = activity;
        bot.PersistentRecord.ObjectiveProgress = progress;
        bot.MarkAutonomousStateDirty();
    }

    // ---------------------------------------------------------------- building a fire

    private static void TryBuildFires(CampObject[] fires, long now)
    {
        foreach (GameBot bot in AutonomousBotRegistry.Snapshot())
        {
            if (!Eligible(bot) || !bot.IsRecoveryResting || bot.IsMoving || Visits.ContainsKey(bot.DatabaseID) || bot.Inventory == null)
                continue;
            if (NextBuildCheck.TryGetValue(bot.DatabaseID, out long next) && now < next)
                continue;
            NextBuildCheck[bot.DatabaseID] = now + 60_000;
            if (LastWarmed.TryGetValue(bot.DatabaseID, out long warmed) && now - warmed < 25 * 60_000)
                continue;
            if (fires.Any(f => f.CurrentRegionID == bot.CurrentRegionID && bot.IsWithinRadius(f, 2000)))
                continue;
            DbInventoryItem kit = Kit(bot, false);
            if (kit == null || Rng.NextDouble() > 0.35)
                continue;
            if (!CampingSupplies.TryParse(kit.Id_nb, out CampingSupplies.Tier tier, out _) ||
                !CampingSupplies.TryPlace(bot, tier, false, out _))
                continue;
            UseCharge(bot, kit);
            DbInventoryItem pot = Kit(bot, true);
            if (pot != null && CampingSupplies.TryParse(pot.Id_nb, out CampingSupplies.Tier potTier, out _) &&
                CampingSupplies.TryPlace(bot, potTier, true, out _))
                UseCharge(bot, pot);
            Status(bot, "Built a campfire", "Resting by its own fire");
        }
    }

    private static DbInventoryItem Kit(GameBot bot, bool pot) =>
        bot.Inventory.GetItemRange(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack)
            .Where(i => i != null && CampingSupplies.TryParse(i.Id_nb, out _, out bool isPot) && isPot == pot && i.Charges > 0)
            .OrderByDescending(i => i.Level).FirstOrDefault();

    private static void UseCharge(GameBot bot, DbInventoryItem item)
    {
        item.Charges--;
        if (item.Charges < 1)
            bot.Inventory.RemoveItem(item);
        AutonomousBotEconomy.MarkInventoryChanged(bot);
        bot.MarkAutonomousStateDirty();
        AutonomousBotStatusPersistence.Queue(bot, true);
    }

    /// <summary>At a merchant: a bot with coin to spare buys the best kit it can comfortably afford (a quarter of its
    /// purse at most) and a pot to go with it, when it has none.</summary>
    public static bool TryBuyKits(GameBot bot)
    {
        if (bot?.IsAutonomousWorldBot != true || bot.IsTemporaryGroupHelper || bot.Inventory == null)
            return false;
        bool bought = false;
        foreach (bool pot in new[] { false, true })
        {
            if (Kit(bot, pot) != null)
                continue;
            long purse = AutonomousBotEconomy.GetMoney(bot.DatabaseID);
            CampingSupplies.Tier tier = CampingSupplies.Tiers
                .Where(t => t.Price * 4 <= purse && t.Level <= bot.Level + 8)
                .OrderByDescending(t => t.Number).FirstOrDefault();
            if (tier == null)
                break;
            DbItemTemplate template = CampingSupplies.Template(pot ? CampingSupplies.PotId(tier.Number) : CampingSupplies.FireId(tier.Number));
            eInventorySlot slot = bot.Inventory.FindFirstEmptySlot(eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack);
            if (template == null || slot == eInventorySlot.Invalid || !AutonomousBotEconomy.TrySpend(bot.DatabaseID, tier.Price))
                break;
            if (!bot.Inventory.AddItem(slot, GameInventoryItem.Create(template)))
            {
                AutonomousBotEconomy.AddMoney(bot.DatabaseID, tier.Price);
                break;
            }
            bought = true;
        }
        if (bought)
        {
            AutonomousBotEconomy.MarkInventoryChanged(bot);
            bot.MarkAutonomousStateDirty();
            AutonomousBotStatusPersistence.Queue(bot, true);
        }
        return bought;
    }

    // ---------------------------------------------------------------- talk at the fire

    private static readonly string[] Openers =
    [
        "Nothing like a warm fire after a long hunt.", "Pass the stew, would you? My legs ache from the road.",
        "I could sit here till dawn and not regret it.", "The night is colder than it looks out there.",
        "Has anyone found good hunting today?", "A fire like this makes a camp feel like home.",
        "My boots are full of mud and my purse is empty. A good day, then.", "Watch the sparks - I singed my cloak last time.",
        "I heard the roads north are thick with beasts lately.", "A moment's rest, then back to it.",
    ];

    private static readonly string[] Replies =
    [
        "Aye, it is a welcome thing.", "I'll not argue with that.", "Truer words were never spoken by a campfire.",
        "Rest while you can, friend.", "Mind you don't eat all of it.", "I've had worse company, and worse fires.",
        "Ha! You and me both.", "Let's hope the beasts keep their distance tonight.",
    ];

    private static readonly string[] Greetings =
    [
        "Welcome, {0}. Pull up a log and warm yourself.", "Evening, {0}. There's room by the fire.",
        "Sit, {0}, sit. The fire's free.", "Well met, {0}. Rest your feet a while.",
    ];

    private static readonly string[] Farewells =
    [
        "That'll do me. Safe travels, all.", "Warm enough to face the road again. Farewell.",
        "My thanks for the fire. Good hunting.",
    ];

    /// <summary>The sitters at a fire (every 5 s): a greeting for a player who sits down, and now and then some talk.</summary>
    public static void Chatter(CampObject fire, HashSet<GameLiving> here)
    {
        long now = GameLoop.GameLoopTime;
        GameBot[] bots = here.OfType<GameBot>().Where(b => Eligible(b) && CampingSupplies.IsSitting(b)).ToArray();
        if (bots.Length == 0)
            return;
        foreach (GamePlayer player in here.OfType<GamePlayer>())
        {
            if (!CampingSupplies.IsSitting(player) || !Greeted.TryAdd((fire.ObjectID, player.Name), true))
                continue;
            GameBot host = bots.OrderByDescending(b => AutonomousPopulationController.PersonaOf(b.PersistentRecord).Chat).First();
            Say(host, string.Format(Greetings[Rng.Next(Greetings.Length)], player.Name), 1500);
            NextChatter[fire.ObjectID] = now + 40_000;
            return;
        }
        if (NextChatter.TryGetValue(fire.ObjectID, out long next) && now < next)
            return;
        NextChatter[fire.ObjectID] = now + 45_000 + Rng.Next(60_000);
        GameBot speaker = bots[Rng.Next(bots.Length)];
        BotPersona p = AutonomousPopulationController.PersonaOf(speaker.PersistentRecord);
        if (Rng.Next(100) >= p.Chat + (here.Count > 1 ? 15 : -20))
            return;                                                  // (a quiet one, or nobody to talk to)
        Say(speaker, Openers[Rng.Next(Openers.Length)], 0);
        GameBot other = bots.Where(b => b != speaker).OrderBy(_ => Rng.Next()).FirstOrDefault();
        if (other != null && Rng.NextDouble() < 0.6)
            Say(other, Replies[Rng.Next(Replies.Length)], 3000 + Rng.Next(2500));
    }

    /// <summary>A visit ending after a while at the fire: a sociable bot says goodbye.</summary>
    public static string Farewell() => Farewells[Rng.Next(Farewells.Length)];

    private static void Say(GameBot bot, string line, int delayMs)
    {
        if (delayMs <= 0)
        {
            bot.Say(line);
            return;
        }
        _ = new ECSGameTimer(bot, _ =>
        {
            if (bot.IsAlive && !bot.InCombat)
                bot.Say(line);
            return 0;
        }, delayMs);
    }
}
