using System;
using System.Collections.Concurrent;
using System.IO;
using System.Linq;
using DOL.GS.PacketHandler;

namespace DOL.GS.Commands
{
    /// <summary>
    /// GM: pick an NPC up and carry it somewhere else (owner 2026-11-23, Bugs & Fixes: "GM Mode: A way to pick up NPCs and
    /// drag them, and move them to a new location? I could fix bugged placements that way").
    ///   /grab          - your target (an NPC, not a player or a bot) follows you, a couple of steps in front of you;
    ///   /grab drop     - it stays where it is now. One the database keeps (a classic NPC) is saved there; one a zone
    ///                    build, an event or a story placed is written to placement-fixes.txt in the server folder, in
    ///                    zone metres, so the fix can go into its file;
    ///   /grab cancel   - it goes back where it was.
    /// </summary>
    [CmdAttribute("&grab", ePrivLevel.GM, "GM: carry your target NPC to a new spot", "/grab [name] | /grab drop | /grab cancel")]
    public class GrabCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        sealed class Carry
        {
            public GameNPC Npc;
            public int X, Y, Z;
            public ushort Heading;
            public ECSGameTimer Timer;
        }

        static readonly ConcurrentDictionary<GamePlayer, Carry> _carrying = new();

        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer gm = client?.Player;
            if (gm == null)
                return;
            string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            if (sub is "drop" or "cancel")
            {
                if (!_carrying.TryRemove(gm, out Carry c))
                {
                    DisplayMessage(client, "You aren't carrying anything.");
                    return;
                }
                c.Timer?.Stop();
                GameNPC n = c.Npc;
                if (sub == "cancel")
                {
                    n.MoveTo(n.CurrentRegionID, c.X, c.Y, c.Z, c.Heading);
                    DisplayMessage(client, $"{n.Name} is back where it was.");
                    return;
                }
                n.Heading = gm.Heading;
                n.SpawnPoint = new Point3D(n.X, n.Y, n.Z);
                n.SpawnHeading = n.Heading;
                string where = Where(n);
                if (!n.LoadedFromScript && !string.IsNullOrEmpty(n.InternalID))
                {
                    n.SaveIntoDatabase();
                    DisplayMessage(client, $"{n.Name} saved at {where} (the database's own NPC).");
                }
                else
                {
                    try
                    {
                        string line = $"{DateTime.Now:yyyy-MM-dd HH:mm} | {n.Name} | {n.GuildName} | {where} | world {n.X} {n.Y} {n.Z} heading {n.Heading}";
                        File.AppendAllText(Path.Combine(GameServer.Instance.Configuration.RootDirectory, "placement-fixes.txt"), line + Environment.NewLine);
                    }
                    catch (Exception e)
                    {
                        DisplayMessage(client, "Couldn't write placement-fixes.txt: " + e.Message);
                    }
                    DisplayMessage(client, $"{n.Name} placed at {where}. A zone build, event or story NPC: written to placement-fixes.txt so the fix can go into its file (until then it goes back there on a restart).");
                }
                return;
            }
            if (_carrying.ContainsKey(gm))
            {
                DisplayMessage(client, "You're already carrying something: /grab drop or /grab cancel.");
                return;
            }
            GameNPC npc = gm.TargetObject as GameNPC;
            if (args.Length > 1 && sub is not ("drop" or "cancel"))
            {
                // /grab <name>: the nearest NPC of that name (live test 24 Nov: a target set from the client didn't always
                // reach the server's side)
                string name = string.Join(" ", args, 1, args.Length - 1);
                npc = gm.GetNPCsInRadius(2000).Cast<GameNPC>()
                    .Where(n => n is not GameBot && n.IsAlive && string.Equals(n.Name, name, StringComparison.OrdinalIgnoreCase))
                    .OrderBy(n => n.GetDistanceTo(gm)).FirstOrDefault();
            }
            if (npc == null || npc is GameBot || !npc.IsAlive)
            {
                DisplayMessage(client, "Target an NPC first (not a player or a bot), or /grab <its name> when it's near.");
                return;
            }
            var carry = new Carry { Npc = npc, X = npc.X, Y = npc.Y, Z = npc.Z, Heading = npc.Heading };
            npc.StopMoving();
            carry.Timer = new ECSGameTimer(gm, timer =>
            {
                if (!_carrying.ContainsKey(gm) || gm.ObjectState != GameObject.eObjectState.Active || npc.ObjectState != GameObject.eObjectState.Active)
                {
                    _carrying.TryRemove(gm, out _);
                    return 0;
                }
                double a = gm.Heading * Math.PI * 2 / 4096.0;
                int x = gm.X - (int) (Math.Sin(a) * 90), y = gm.Y + (int) (Math.Cos(a) * 90);
                if (Math.Abs(npc.X - x) > 8 || Math.Abs(npc.Y - y) > 8 || Math.Abs(npc.Z - gm.Z) > 8)
                {
                    npc.StopMoving();
                    npc.MoveTo(gm.CurrentRegionID, x, y, gm.Z, gm.Heading);
                }
                return 300;
            }, 300);
            _carrying[gm] = carry;
            DisplayMessage(client, $"You pick up {npc.Name}. Walk to the new spot, then /grab drop (or /grab cancel).");
        }

        static string Where(GameNPC n)
        {
            Zone z = n.CurrentZone;
            return z == null ? $"{n.X},{n.Y},{n.Z}" : $"{z.Description} (zone {z.ID}) at {(n.X - z.XOffset) / 40.0:0} m, {(n.Y - z.YOffset) / 40.0:0} m, {n.Z / 40.0:0.0} m";
        }
    }
}
