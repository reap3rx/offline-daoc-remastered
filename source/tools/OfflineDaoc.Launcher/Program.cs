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
        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
    }
}
