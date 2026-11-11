using System;
using System.Linq;
using DOL.GS.PacketHandler;

namespace DOL.GS.Commands
{
    /// <summary>
    /// GM tests for the world features (owner 2026-11-11 - camping, soulbind stones, treasure chests):
    ///   /wf chest [trap]  a treasure chest in front of you (trap: the 1-in-100 trapped kind)
    ///   /wf stone         where the nearest soulbind stone of this region is
    ///   /wf die           you fall where you stand (to try the death window)
    /// </summary>
    [CmdAttribute("&wf", ePrivLevel.GM, "World feature tests: /wf chest [trap] | /wf stone | /wf die", "/wf chest [trap]", "/wf stone", "/wf die")]
    public class WorldFeaturesCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            string what = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            switch (what)
            {
                case "chest":
                {
                    double a = p.Heading * Math.PI * 2 / 4096.0;
                    var chest = new TreasureChest(Math.Max(1, (int)p.Level), args.Length > 2 && args[2].Equals("trap", StringComparison.OrdinalIgnoreCase))
                    {
                        X = p.X - (int)(Math.Sin(a) * 120), Y = p.Y + (int)(Math.Cos(a) * 120), Z = p.Z,
                        Heading = p.Heading, CurrentRegionID = p.CurrentRegionID,
                    };
                    chest.AddToWorld();
                    DisplayMessage(client, $"A treasure chest{(chest.Trapped ? " (trapped)" : "")} appears before you.");
                    break;
                }
                case "stone":
                {
                    SoulbindStone s = SoulbindStones.Nearest(p.CurrentRegionID, p.X, p.Y);
                    DisplayMessage(client, s == null ? "No soulbind stone in this region." :
                        $"Nearest soulbind stone: {s.X}, {s.Y}, {s.Z} ({(int)Math.Sqrt((double)(s.X - p.X) * (s.X - p.X) + (double)(s.Y - p.Y) * (s.Y - p.Y))} units)");
                    break;
                }
                case "die":
                    p.TakeDamage(p, eDamageType.Natural, p.Health + p.MaxHealth, 0);
                    break;
                default:
                    DisplaySyntax(client);
                    break;
            }
        }
    }
}
