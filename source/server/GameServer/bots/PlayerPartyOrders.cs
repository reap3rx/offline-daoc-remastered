using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.AI.Brain;
using DOL.GS.Commands;
using DOL.GS.PacketHandler;

namespace DOL.GS;

/// <summary>
/// Orders for the bots in your group (owner 2026-11-16: "Up will be default pull, but holding up will bring up a radial
/// window of commands you can give to your party of bots. Some good examples would be formation types (like columns,
/// horizontal or vertical line) Wait, follow, rest, camp, spread out, buff"; "Camp ... One bot will set up a camp (like
/// our camping feature) and everyone will sit around it and chat for a bit. This feature can happen even if a bot
/// doesn't have the items (just use one of the campfire items that are level appropriate)"; "/grind to be one of the
/// radial options"). /order &lt;what&gt;; the controller's order wheel (hold d-pad up) sends the same.
///   formation column | line | spread | normal - where each bot walks behind you (BotBrain.FollowFormation asks Slot);
///   wait - they stay where they stand until you order follow (they still fight what comes);
///   follow - back at your side, the formation as it was;
///   rest - they sit where they are until they're recovered, then follow;
///   camp - one of them builds a campfire of your level's kit, the rest sit around it and talk now and then; they stay
///          until you walk off (CampLeash) or order follow;
///   buff - they cast their buffs now;
///   grind - /grind on or off.
/// </summary>
public static class PlayerPartyOrders
{
    public enum Formation { Normal, Column, Line, Spread }

    public const int CampLeash = 900;           // walk this far from the fire and the camp breaks up
    public const int SeatRadius = 170;

    private sealed class Hold
    {
        public Vector3 Spot;
        public bool Sit;
        public bool Rest;                       // (sat to recover: up and following once recovered)
        public CampObject Fire;
        public bool Seated;
        public long SeatedAt;
        public long PathedAt;
        public bool Logged;
    }

    private static readonly DOL.Logging.Logger Log = DOL.Logging.LoggerManager.Create(typeof(PlayerPartyOrders));
    private static readonly ConcurrentDictionary<GamePlayer, Formation> Formations = new();
    private static readonly ConcurrentDictionary<GameBot, Hold> Holds = new();
    private static readonly ConcurrentDictionary<GamePlayer, long> NextCampTalk = new();

    /// <summary>The bots your orders reach: your group's bots that follow you.</summary>
    public static List<GameBot> Followers(GamePlayer player) =>
        player?.Group?.GetMembersInTheGroup().OfType<GameBot>()
            .Where(b => b.IsAlive && b.PlayerGroupLeader == player && b.ObjectState == GameObject.eObjectState.Active)
            .ToList() ?? [];

    public static string Order(GamePlayer player, string what, string arg)
    {
        if (player == null)
            return null;
        List<GameBot> bots = Followers(player);
        if (what is not ("grind" or "formation") && bots.Count == 0)
            return "No bots in your group follow you.";
        switch (what)
        {
            case "formation":
            case "column":
            case "line":
            case "spread":
            case "normal":
            {
                string kind = what == "formation" ? arg : what;
                Formation f = kind switch
                {
                    "column" or "file" => Formation.Column,
                    "line" or "row" => Formation.Line,
                    "spread" or "out" => Formation.Spread,
                    _ => Formation.Normal,
                };
                Formations[player] = f;
                foreach (GameBot b in bots)
                    Holds.TryRemove(b, out _);
                return f switch
                {
                    Formation.Column => "Your group falls in behind you in single file.",
                    Formation.Line => "Your group walks abreast of you in a line.",
                    Formation.Spread => "Your group spreads out around you.",
                    _ => "Your group keeps its usual places.",
                };
            }
            case "wait":
            case "stay":
            case "hold":
                foreach (GameBot b in bots)
                {
                    StandUp(b);
                    Holds[b] = new Hold { Spot = new(b.X, b.Y, b.Z) };
                    b.StopMovingOnPath();
                    b.StopMoving();
                }
                Say(bots, "Waiting here.", "We'll hold.", "Right here, then.");
                return "Your group waits where it stands. Order follow to bring them along.";
            case "follow":
                foreach (GameBot b in bots)
                {
                    StandUp(b);
                    Holds.TryRemove(b, out _);
                }
                Say(bots, "Coming.", "Right behind you.", "On your heels.");
                return "Your group follows you.";
            case "rest":
                foreach (GameBot b in bots)
                {
                    if (b.InCombat)
                        continue;
                    Holds[b] = new Hold { Spot = new(b.X, b.Y, b.Z), Sit = true, Rest = true };
                    b.StopMovingOnPath();
                    b.StopMoving();
                }
                return "Your group sits down to rest; they'll follow once they've recovered.";
            case "camp":
                return Camp(player, bots);
            case "buff":
                foreach (GameBot b in bots)
                    (b.Brain as BotBrain)?.BuffNow();
                Say(bots, "Buffs coming up.", "Hold still a moment.", "Let me see to that.");
                return "Your group sees to its buffs.";
            case "grind":
                if (PlayerCompanionGrind.IsActive(player))
                {
                    PlayerCompanionGrind.Stop(player, "ordered off");
                    return null;
                }
                return PlayerCompanionGrind.TryStart(player, out string msg) ? msg : msg;
            default:
                return "/order formation column|line|spread|normal, wait, follow, rest, camp, buff or grind.";
        }
    }

    // ---------------------------------------------------------------- following (BotBrain.FollowFormation)

    /// <summary>True while an order keeps the bot in place (wait, rest, camp): it walks to its spot, sits there when it
    /// should, and the formation leaves it alone.</summary>
    public static bool Holding(GameBot bot)
    {
        if (bot == null || !Holds.TryGetValue(bot, out Hold h))
            return false;
        GamePlayer leader = bot.PlayerGroupLeader;
        if (leader == null || !bot.IsAlive || leader.CurrentRegionID != bot.CurrentRegionID)
        {
            Release(bot);
            return false;
        }
        if (h.Fire != null && (h.Fire.ObjectState != GameObject.eObjectState.Active ||
                               !leader.IsWithinRadius(h.Fire, CampLeash)))
        {
            Release(bot);                                    // (you walked off, or the fire burned out)
            return false;
        }
        if (h.Rest && h.Seated && GameLoop.GameLoopTime - h.SeatedAt > 15_000 && !PlayerCompanionGrind.NeedsRecovery(bot))
        {
            Release(bot);                                    // (rested: up and after you)
            return false;
        }
        if (bot.InCombat)
            return false;                                    // (a fight comes first; the spot waits)
        float dx = bot.X - h.Spot.X, dy = bot.Y - h.Spot.Y;
        if (!h.Logged)
        {
            h.Logged = true;
            Log.Info($"PARTY_ORDER_HOLD bot={bot.Name} leader={leader.Name} sit={h.Sit} rest={h.Rest} fire={h.Fire != null} " +
                $"spot={(int)h.Spot.X},{(int)h.Spot.Y},{(int)h.Spot.Z} away={(int)Math.Sqrt(dx * dx + dy * dy)}");
        }
        if (dx * dx + dy * dy > 60 * 60)
        {
            long now = GameLoop.GameLoopTime;
            if (!bot.IsMoving && now - h.PathedAt > 1500)
            {
                h.PathedAt = now;
                bot.PathTo(h.Spot, bot.MaxSpeed);
                if (!bot.IsMoving)
                    bot.WalkTo(new Point3D((int)h.Spot.X, (int)h.Spot.Y, (int)h.Spot.Z), bot.MaxSpeed);   // (no path: straight there)
            }
            return true;
        }
        if (h.Sit && !h.Seated)
        {
            bot.StopMovingOnPath();
            bot.StopMoving();
            if (h.Fire != null)
                bot.TurnTo(h.Fire);
            h.Seated = true;
            h.SeatedAt = GameLoop.GameLoopTime;
            ShowSitting(bot, true);
        }
        if (h.Sit && !bot.IsRecoveryResting)
            bot.BeginRecoveryRest();
        if (h.Fire != null)
            CampTalk(leader, bot);
        return true;
    }

    private static void Release(GameBot bot)
    {
        if (Holds.TryRemove(bot, out Hold h) && h.Seated)
            StandUp(bot, h);
    }

    private static void StandUp(GameBot bot, Hold h = null)
    {
        if (h == null && !Holds.TryGetValue(bot, out h))
            return;
        if (h.Seated)
        {
            ShowSitting(bot, false);
            bot.WakeRecoveryRest();
            h.Seated = false;
        }
    }

    /// <summary>The bot's place behind its leader in the formation you ordered, or false for the usual one.</summary>
    public static bool Slot(GameBot bot, GamePlayer leader, out Vector3 at)
    {
        at = default;
        if (bot == null || leader == null || !Formations.TryGetValue(leader, out Formation f) || f == Formation.Normal)
            return false;
        List<GameBot> line = Followers(leader).OrderBy(b => b.GroupIndex).ThenBy(b => b.ObjectID).ToList();
        int i = Math.Max(0, line.IndexOf(bot));
        double heading = leader.Heading * Math.PI * 2 / 4096.0;
        Vector2 fwd = new((float)-Math.Sin(heading), (float)Math.Cos(heading));
        Vector2 side = new(fwd.Y, -fwd.X);
        Vector2 p = f switch
        {
            Formation.Column => -fwd * (110 + 95 * i),
            Formation.Line => side * (95 * ((i / 2) + 1) * (i % 2 == 0 ? 1 : -1)) - fwd * 30,
            _ => Rotate(fwd, Math.PI * 2 * i / Math.Max(1, line.Count)) * 330,
        };
        at = new Vector3(leader.X + p.X, leader.Y + p.Y, leader.Z);
        return true;
    }

    private static Vector2 Rotate(Vector2 v, double a) =>
        new((float)(v.X * Math.Cos(a) - v.Y * Math.Sin(a)), (float)(v.X * Math.Sin(a) + v.Y * Math.Cos(a)));

    // ---------------------------------------------------------------- camp

    private static string Camp(GamePlayer player, List<GameBot> bots)
    {
        if (player.InCombat || bots.Any(b => b.InCombat))
            return "Not while there's fighting.";
        CampObject fire = CampingSupplies.NearestFire(player, 600);
        GameBot builder = null;
        if (fire == null)
        {
            // the builder: whoever stands nearest you; a kit of your level (they always have one for this)
            builder = bots.OrderBy(b => b.GetDistanceTo(player)).First();
            int level = Math.Max(1, (int)player.Level);
            CampingSupplies.Tier tier = CampingSupplies.Tiers.Where(t => t.Level <= level).LastOrDefault() ?? CampingSupplies.Tiers[0];
            builder.StopMovingOnPath();
            builder.StopMoving();
            if (!CampingSupplies.TryPlace(builder, tier, false, out string why))
                return why ?? "There's no room for a fire here.";
            fire = CampingSupplies.NearestFire(builder, 300);
            if (fire == null)
                return "The fire wouldn't catch.";
            builder.Say(Pick(BuildLines));
        }
        int n = 0;
        foreach (GameBot b in bots)
        {
            double angle = Math.PI * 2 * n++ / Math.Max(3, bots.Count + 1) + Math.PI / 6;
            var centre = new Vector3(fire.X, fire.Y, fire.Z);
            var seat = new Vector3(fire.X + (float)(Math.Sin(angle) * SeatRadius), fire.Y + (float)(Math.Cos(angle) * SeatRadius), fire.Z);
            if (fire.CurrentZone != null)                    // (on the ground round the fire, not in a rock)
                seat = PathfindingProvider.Instance.GetMoveAlongSurface(fire.CurrentZone, centre, seat,
                    PathfindingProvider.Instance.DefaultFilters) ?? seat;
            Holds[b] = new Hold
            {
                Spot = seat,
                Sit = true,
                Fire = fire,
            };
        }
        NextCampTalk[player] = GameLoop.GameLoopTime + 12_000;
        return builder != null
            ? $"{builder.Name} builds a campfire, and your group gathers round it. Walk off (or order follow) to break camp."
            : "Your group gathers round the fire. Walk off (or order follow) to break camp.";
    }

    /// <summary>Now and then one of them says something by the fire.</summary>
    private static void CampTalk(GamePlayer leader, GameBot bot)
    {
        long now = GameLoop.GameLoopTime;
        if (!NextCampTalk.TryGetValue(leader, out long at) || now < at)
            return;
        NextCampTalk[leader] = now + Random.Shared.Next(25_000, 55_000);
        bot.Say(Pick(CampLines));
    }

    private static void ShowSitting(GameBot bot, bool on)
    {
        foreach (GamePlayer p in bot.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
            NewClient.Send(p, $"#SIT|{bot.ObjectID}|{(on ? 1 : 0)}");
    }

    private static void Say(List<GameBot> bots, params string[] lines)
    {
        if (bots.Count > 0)
            bots[Random.Shared.Next(bots.Count)].Say(lines[Random.Shared.Next(lines.Length)]);
    }

    private static string Pick(string[] lines) => lines[Random.Shared.Next(lines.Length)];

    private static readonly string[] BuildLines =
    [
        "I'll get a fire going.", "Leave the fire to me.", "Here - this spot's dry enough.", "A fire, then. Gather round.",
    ];

    private static readonly string[] CampLines =
    [
        "Nothing like a fire after a long day.", "Anyone else's feet aching?", "I could sit here all night.",
        "Pass the bread, would you?", "Quiet out here tonight.", "Remember that last fight? Too close.",
        "My grandmother told stories by fires like this.", "Smells like rain coming.", "Wake me if anything comes.",
        "I'm almost warm again.", "Good company, good fire. Can't ask for more.", "Who's taking first watch?",
    ];
}

/// <summary>/order: your bots' orders (the controller's order wheel sends these).</summary>
[CmdAttribute("&order", ePrivLevel.Player, "Orders for the bots in your group",
    "/order formation column|line|spread|normal | wait | follow | rest | camp | buff | grind")]
public class PartyOrderCommandHandler : AbstractCommandHandler, ICommandHandler
{
    public void OnCommand(GameClient client, string[] args)
    {
        GamePlayer p = client?.Player;
        if (p == null)
            return;
        string what = args.Length > 1 ? args[1].ToLowerInvariant() : "";
        string arg = args.Length > 2 ? args[2].ToLowerInvariant() : "";
        string said = PlayerPartyOrders.Order(p, what, arg);
        if (!string.IsNullOrEmpty(said))
            p.Out.SendMessage(said, eChatType.CT_System, eChatLoc.CL_SystemWindow);
    }
}
