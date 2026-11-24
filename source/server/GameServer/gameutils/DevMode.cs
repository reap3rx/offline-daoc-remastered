using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using DOL.Events;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// GM mode on the fly (owner 2026-11-21: "have a tick box to change between GM mode and regular mode while in game
    /// if I can, so I don't have to log out and shut down the server to change it"). An account that has ever logged in
    /// as a GM (or higher) is remembered in runtime\server\dev-accounts.txt with that level; /devmode on|off then switches
    /// it between that level and a player, live, and saves it so the next login keeps it. Accounts that were never a GM
    /// can't use it. The new client is told the level and whether it can switch ("#PRIV|level|0/1") for its Tools page.
    /// </summary>
    public static class DevMode
    {
        static readonly object Lock = new();
        static Dictionary<string, uint> _accounts;          // account name -> its GM level

        static string FilePath => Path.Combine(GameServer.Instance.Configuration.RootDirectory, "dev-accounts.txt");

        static Dictionary<string, uint> Accounts
        {
            get
            {
                lock (Lock)
                {
                    if (_accounts != null)
                        return _accounts;
                    _accounts = new Dictionary<string, uint>(StringComparer.OrdinalIgnoreCase);
                    try
                    {
                        if (File.Exists(FilePath))
                            foreach (string line in File.ReadAllLines(FilePath))
                            {
                                string[] p = line.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
                                if (p.Length >= 1 && !p[0].StartsWith('#'))
                                    _accounts[p[0]] = p.Length > 1 && uint.TryParse(p[1], out uint l) && l > 1 ? l : (uint) ePrivLevel.GM;
                            }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[DevMode] {ex.Message}");
                    }
                    return _accounts;
                }
            }
        }

        static void Save()
        {
            lock (Lock)
            {
                try
                {
                    File.WriteAllLines(FilePath, new[] { "# accounts that may switch GM mode in game (/devmode): name level" }
                        .Concat(Accounts.Select(kv => $"{kv.Key} {kv.Value}")));
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[DevMode] {ex.Message}");
                }
            }
        }

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args) =>
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, Entered);

        static void Entered(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GamePlayer p || p.Client?.Account == null)
                return;
            uint lvl = p.Client.Account.PrivLevel;
            if (lvl > (uint) ePrivLevel.Player)
            {
                lock (Lock)
                {
                    if (!Accounts.TryGetValue(p.Client.Account.Name, out uint had) || had != lvl)
                    {
                        Accounts[p.Client.Account.Name] = lvl;
                        Save();
                    }
                }
            }
            Send(p);
        }

        public static bool CanSwitch(GamePlayer p)
        {
            lock (Lock)
                return p?.Client?.Account != null && Accounts.ContainsKey(p.Client.Account.Name);
        }

        public static void Send(GamePlayer p)
        {
            if (p?.Client?.Account != null && NewClient.Is(p))
                NewClient.Send(p, $"#PRIV|{p.Client.Account.PrivLevel}|{(CanSwitch(p) ? 1 : 0)}");
        }

        /// <summary>Switch GM mode: on puts the account back at its GM level, off makes it a player. Saved.</summary>
        public static bool Switch(GamePlayer p, bool on)
        {
            if (!CanSwitch(p))
                return false;
            uint gm;
            lock (Lock)
                gm = Accounts[p.Client.Account.Name];
            p.Client.Account.PrivLevel = on ? gm : (uint) ePrivLevel.Player;
            try
            {
                GameServer.Database.SaveObject(p.Client.Account);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DevMode] save: {ex.Message}");
            }
            Send(p);
            return true;
        }
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&devmode", ePrivLevel.Player, "Switch GM mode on or off in game (accounts that have been a GM only)",
        "/devmode on | off | status")]
    public class DevModeCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client.Player;
            if (p == null)
                return;
            string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "status";
            if (sub == "status")
            {
                DevMode.Send(p);
                return;
            }
            if (!DevMode.CanSwitch(p))
            {
                DisplayMessage(client, "GM mode can only be switched on an account that has logged in as a GM.");
                DevMode.Send(p);
                return;
            }
            bool on = sub is "on" or "1" or "gm";
            DevMode.Switch(p, on);
            DisplayMessage(client, on ? "GM mode is ON." : "GM mode is OFF: you play as a player.");
        }
    }
}
