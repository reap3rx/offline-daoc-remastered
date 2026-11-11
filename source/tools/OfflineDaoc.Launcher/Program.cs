namespace OfflineDaoc.Launcher;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        if (args.Length == 1 && args[0] == "--prepare-portable-account")
        {
            // the new client's launcher keeps its account with the game it plays (server_root.txt)
            PortableCredentials.ReadOrCreate(MainForm.ServerRootFor(AppContext.BaseDirectory));
            return;
        }
        if (args.Length == 2 && args[0] == "--build-roster" && int.TryParse(args[1], out int perRealm))
        {
            // the living population's roster, from a shell (the Population page's BUILD ROSTER)
            string root = MainForm.ServerRootFor(AppContext.BaseDirectory);
            int[] added = PopulationRoster.Build(Path.Combine(root, "data", "opendaoc.sqlite3.db"), root, perRealm, Console.WriteLine);
            Console.WriteLine($"Added {added[0]} Albion, {added[1]} Midgard, {added[2]} Hibernia.");
            return;
        }
        if (args.Length >= 1 && args[0] == "--update")
        {
            // the install / update without the window (tests, scripted installs): update-log.txt beside the launcher
            string log = Path.Combine(AppContext.BaseDirectory, "update-log.txt");
            void Log(string s) => File.AppendAllText(log, $"{DateTime.Now:HH:mm:ss} {s}{Environment.NewLine}");
            try
            {
                var updater = new Updater(AppContext.BaseDirectory);
                if (!updater.Enabled) { Log("no update.json - nothing to update from"); return; }
                Updater.Plan plan = updater.CheckAsync(CancellationToken.None).GetAwaiter().GetResult();
                Log($"latest {plan.Latest.Version}: {plan.Needed.Count} packs, {plan.DownloadBytes / 1e6:F0} MB (first install: {plan.FirstInstall})");
                string last = "";
                bool restart = updater.ApplyAsync(plan, (d, t, w) => { if (w != last) { last = w; Log(w); } }, CancellationToken.None).GetAwaiter().GetResult();
                Log($"done - installed {plan.Latest.Version}{(restart ? " (the launcher itself changed)" : "")}");
            }
            catch (Exception e) { Log("FAILED: " + e); }
            return;
        }
        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
    }
}
