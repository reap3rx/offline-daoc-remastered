using System;

namespace DOL.GS.Commands
{
    [Cmd(
        "&release", ["&rel"],
        ePrivLevel.Player,
        "When you are dead you can '/release'. This will bring you back to your bindpoint!",
        "/release")]
    public class ReleaseCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            if (args.Length <= 1)
            {
                client.Player.Release(eReleaseType.Normal, false);
                return;
            }

            string toArgument = args[1];

            // owner 2026-11-11: two ways back from death - the nearest soulbind stone, or your bind stone (or a
            // resurrection someone offers); /release city and /release house go to your bind stone now
            if (toArgument.Equals("soulbind", StringComparison.OrdinalIgnoreCase) ||
                toArgument.Equals("stone", StringComparison.OrdinalIgnoreCase))
            {
                client.Player.Release(eReleaseType.Soulbind, false);
                return;
            }

            if (toArgument.Equals("city", StringComparison.OrdinalIgnoreCase) ||
                toArgument.Equals("house", StringComparison.OrdinalIgnoreCase))
            {
                client.Player.Release(eReleaseType.Bind, false);
                return;
            }

            if (toArgument.Equals("bind", StringComparison.OrdinalIgnoreCase))
            {
                client.Player.Release(eReleaseType.Bind, false);
                return;
            }
        }
    }
}
