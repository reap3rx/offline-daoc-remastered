using System.Data.SQLite;
using System.Globalization;
using OfflineDaoc.Population;

namespace OfflineDaoc.Launcher;

/// <summary>
/// The living population's roster (owner 2026-11-10, "Living Bot Population - Plan": "Pick a size per realm ... Every
/// bot gets a lore name and a persona and starts not yet arrived. Building 2,000 records should take seconds, since
/// nothing logs in until the scheduler picks it"). Class and race follow the realm's usual mix (BotCharacterGenerator);
/// names come from runtime\data\bots\bot_names.json (BotLoreNames) and personas from BotPersona.Roll. The server's
/// scheduler (AutonomousPopulationController.Sessions) decides who is online.
/// Also the Population page's reads (counts by realm, band and class, recent logins and logouts) and its dials
/// (ServerProperty rows, PopulationKnobs).
/// </summary>
internal static class PopulationRoster
{
    public static string NamesFile(string root) => Path.Combine(root, "data", "bots", "bot_names.json");

    /// <summary>Tops each realm up to `perRealm` roster bots (never removes any). Returns how many were added per realm.</summary>
    public static int[] Build(string database, string root, int perRealm, Action<string>? progress = null)
    {
        BotLoreNames names = BotLoreNames.Load(NamesFile(root));
        using var connection = new SQLiteConnection($"Data Source={database};Version=3;Pooling=False;Default Timeout=30");
        connection.Open();
        using (var busy = connection.CreateCommand())
        {
            busy.CommandText = "PRAGMA busy_timeout=30000; PRAGMA foreign_keys=OFF;";
            busy.ExecuteNonQuery();
        }
        EnsureColumns(connection);
        using var transaction = connection.BeginTransaction();
        names.Reserve(ReadStrings(connection, transaction,
            "SELECT Name FROM offline_world_bots UNION SELECT Name FROM DOLCharacters UNION SELECT DISTINCT Name FROM Mob"));
        PopulationKnobs knobs = ReadKnobs(connection, transaction);
        bool sluagh = !string.Equals(ReadProperty(connection, transaction, "enable_sluaghbinder")?.Trim(), "false",
            StringComparison.OrdinalIgnoreCase);
        var added = new int[3];
        var rng = new Random();
        string now = DateTime.UtcNow.ToString("O");
        for (int realm = 1; realm <= 3; realm++)
        {
            int have;
            using (var count = connection.CreateCommand())
            {
                count.Transaction = transaction;
                count.CommandText = "SELECT COUNT(*) FROM offline_world_bots WHERE IsRetired=0 AND Realm=@r";
                count.Parameters.AddWithValue("@r", realm);
                have = Convert.ToInt32(count.ExecuteScalar(), CultureInfo.InvariantCulture);
            }
            int need = Math.Max(0, perRealm - have);
            for (int i = 0; i < need; i++)
            {
                (int classId, string className, int raceId, string raceName, int gender) = BotCharacterGenerator.Roll(realm, sluagh);
                string? name = names.Generate(raceId, gender, rng);
                if (name == null)
                {
                    i--;                                      // this race / sex has no names left: roll another
                    if (++_misses > 5000)
                        throw new InvalidOperationException("The lore name parts are used up - add parts to bot_names.json.");
                    continue;
                }
                BotPersona persona = BotPersona.Roll(rng, classId, knobs.CasualPct, knobs.TryhardPct);
                InsertNotYetArrived(connection, transaction, name, realm, classId, className, raceId, raceName, gender,
                    persona, now);
                added[realm - 1]++;
                if (added[realm - 1] % 250 == 0)
                    progress?.Invoke($"{RealmName(realm)}: {added[realm - 1]} of {need}");
            }
        }
        UpdateTargetProperties(connection, transaction);
        transaction.Commit();
        return added;
    }

    private static int _misses;

    public static void InsertNotYetArrived(SQLiteConnection connection, SQLiteTransaction transaction, string name, int realm,
        int classId, string className, int raceId, string raceName, int gender, BotPersona persona, string now)
    {
        using var insert = connection.CreateCommand();
        insert.Transaction = transaction;
        insert.CommandText = """
            INSERT INTO offline_world_bots
                (Name, Realm, ClassId, ClassName, RaceId, RaceName, Gender, Level, Experience, RealmPoints,
                 ZoneName, Activity, IsOnline, IsAlive, LastUpdateUtc, MoneyCopper, InventoryRevision,
                 ZoneId, X, Y, Z, RegionId, Health, Mana, Endurance, BindRegionId, BindX, BindY, BindZ,
                 CurrentGoal, ObjectiveProgress, LastMeaningfulProgressUtc, IsRetired,
                 PersonaJson, HasArrived, LastLogoutUtc, SessionEndsUtc, SessionCount)
            VALUES
                (@name, @realm, @classId, @className, @raceId, @raceName, @gender, 1, 0, 0,
                 '', 'Not yet arrived', 0, 1, @now, 0, 0,
                 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
                 'Not yet arrived', 'Arrives when the starting zones have room', @now, 0,
                 @persona, 0, '', '', 0)
            """;
        insert.Parameters.AddWithValue("@name", name);
        insert.Parameters.AddWithValue("@realm", realm);
        insert.Parameters.AddWithValue("@classId", classId);
        insert.Parameters.AddWithValue("@className", className);
        insert.Parameters.AddWithValue("@raceId", raceId);
        insert.Parameters.AddWithValue("@raceName", raceName);
        insert.Parameters.AddWithValue("@gender", gender);
        insert.Parameters.AddWithValue("@now", now);
        insert.Parameters.AddWithValue("@persona", persona.ToJson());
        insert.ExecuteNonQuery();
    }

    /// <summary>The living population's columns (the server's schema reconciler adds them too; this lets the launcher
    /// build a roster before the server has run once).</summary>
    public static void EnsureColumns(SQLiteConnection connection)
    {
        var have = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        using (var info = connection.CreateCommand())
        {
            info.CommandText = "PRAGMA table_info(offline_world_bots)";
            using var reader = info.ExecuteReader();
            while (reader.Read())
                have.Add(reader.GetString(1));
        }
        foreach ((string column, string type) in new[]
        {
            ("PersonaJson", "TEXT NOT NULL DEFAULT ''"), ("HasArrived", "TINYINT(1) NOT NULL DEFAULT 0"),
            ("LastLogoutUtc", "TEXT NOT NULL DEFAULT ''"), ("SessionEndsUtc", "TEXT NOT NULL DEFAULT ''"),
            ("SessionCount", "INT(11) NOT NULL DEFAULT 0"),
        })
        {
            if (have.Contains(column))
                continue;
            using var alter = connection.CreateCommand();
            alter.CommandText = $"ALTER TABLE offline_world_bots ADD COLUMN {column} {type}";
            alter.ExecuteNonQuery();
        }
    }

    private static void UpdateTargetProperties(SQLiteConnection connection, SQLiteTransaction transaction)
    {
        using var command = connection.CreateCommand();
        command.Transaction = transaction;
        // a fresh roster (nobody arrived yet) starts its arrival weeks again at the server's next poll
        command.CommandText = """
            UPDATE ServerProperty SET Value='true' WHERE `Key`='population_enabled';
            UPDATE ServerProperty SET Value='' WHERE `Key`='population_launch_utc'
                AND NOT EXISTS (SELECT 1 FROM offline_world_bots WHERE HasArrived=1 AND IsRetired=0);
            """;
        command.ExecuteNonQuery();
    }

    public static string RealmName(int realm) => realm switch { 1 => "Albion", 2 => "Midgard", 3 => "Hibernia", _ => "?" };

    private static IEnumerable<string> ReadStrings(SQLiteConnection connection, SQLiteTransaction? transaction, string sql)
    {
        var list = new List<string>();
        using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = sql;
        using var reader = command.ExecuteReader();
        while (reader.Read())
            if (!reader.IsDBNull(0))
                list.Add(reader.GetString(0));
        return list;
    }

    public static string? ReadProperty(SQLiteConnection connection, SQLiteTransaction? transaction, string key)
    {
        using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = "SELECT Value FROM ServerProperty WHERE `Key`=@k LIMIT 1";
        command.Parameters.AddWithValue("@k", key);
        return command.ExecuteScalar() as string;
    }

    public static PopulationKnobs ReadKnobs(SQLiteConnection connection, SQLiteTransaction? transaction = null) =>
        PopulationKnobs.FromProperties(key => ReadProperty(connection, transaction, key));

    /// <summary>Writes a dial (the server reads it within half a minute).</summary>
    public static void WriteProperty(SQLiteConnection connection, string key, string value, string description)
    {
        using var update = connection.CreateCommand();
        update.CommandText = "UPDATE ServerProperty SET Value=@v WHERE `Key`=@k";
        update.Parameters.AddWithValue("@k", key);
        update.Parameters.AddWithValue("@v", value);
        if (update.ExecuteNonQuery() > 0)
            return;
        using var insert = connection.CreateCommand();
        insert.CommandText = """
            INSERT INTO ServerProperty (Category, `Key`, Description, DefaultValue, Value, LastTimeRowUpdated, ServerProperty_ID)
            VALUES ('autonomous_population', @k, @d, @v, @v, @t, lower(hex(randomblob(16))))
            """;
        insert.Parameters.AddWithValue("@k", key);
        insert.Parameters.AddWithValue("@d", description);
        insert.Parameters.AddWithValue("@v", value);
        insert.Parameters.AddWithValue("@t", DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture));
        insert.ExecuteNonQuery();
    }

    // ---------------------------------------------------------------- the Population page's view

    public sealed record BotLine(long BotId, string Name, int Realm, int Level, string ClassName, string RaceName,
        bool Online, bool Arrived, string LastLogoutUtc, string SessionEndsUtc, int Sessions, BotPersona? Persona);

    public static List<BotLine> ReadRoster(string database)
    {
        var list = new List<BotLine>();
        using var connection = new SQLiteConnection($"Data Source={database};Version=3;Read Only=True;Pooling=False;Default Timeout=5");
        connection.Open();
        var columns = new HashSet<string>(ReadStrings(connection, null, "SELECT name FROM pragma_table_info('offline_world_bots')"),
            StringComparer.OrdinalIgnoreCase);
        bool living = columns.Contains("PersonaJson");
        using var command = connection.CreateCommand();
        command.CommandText = living
            ? "SELECT BotId, Name, Realm, Level, ClassName, RaceName, IsOnline, HasArrived, LastLogoutUtc, SessionEndsUtc, SessionCount, PersonaJson FROM offline_world_bots WHERE IsRetired=0"
            : "SELECT BotId, Name, Realm, Level, ClassName, RaceName, IsOnline, 1, '', '', 0, '' FROM offline_world_bots WHERE IsRetired=0";
        using var reader = command.ExecuteReader();
        while (reader.Read())
            list.Add(new BotLine(reader.GetInt64(0), reader.GetString(1), reader.GetInt32(2), reader.GetInt32(3),
                reader.GetString(4), reader.GetString(5), reader.GetBoolean(6), Convert.ToInt32(reader.GetValue(7)) != 0,
                reader.IsDBNull(8) ? "" : reader.GetString(8), reader.IsDBNull(9) ? "" : reader.GetString(9),
                reader.IsDBNull(10) ? 0 : reader.GetInt32(10), BotPersona.Parse(reader.IsDBNull(11) ? null : reader.GetString(11))));
        return list;
    }
}
