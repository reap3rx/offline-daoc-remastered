using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace OfflineDaoc.Launcher;

/// <summary>
/// Your progress on more than one computer (owner 2026-11-11: "during a new install the player would have the
/// opportunity to sync a google drive account ... if they wanted to play on multiple computers, otherwise it's not
/// necessary"). The save goes to a folder in Google Drive - "My Drive\OfflineDAoC Saves", kept in step by Google Drive
/// for desktop - so there is nothing to sign in to here: the launcher only copies files into and out of that folder.
/// The same scheme as the developer's tools\sync\savesync.ps1 (and its folder, so the two read each other's saves):
///   current\   the save: the game database (+ -wal / -shm), the realm event records, client\ (settings, keybinds,
///              quickbars, character looks). previous\: the one before. save-info.json: when and from which computer.
///   in-use.json  the computer playing now (another computer is warned).
/// The database is only copied while the server is stopped. What stays per computer: the client's [display],
/// [graphics] and [performance] settings. Before a pull replaces anything here it is backed up (world\save-sync\backups,
/// the last 5).
/// </summary>
internal sealed class CloudSave
{
    public const string FolderName = "OfflineDAoC Saves";
    private static readonly string[] ClientFiles = ["settings.cfg", "keybinds.cfg", "server_looks.json"];
    private static readonly string[] ClientDirs = ["server_quickbars", "keybinds", "world"];
    private static readonly string[] MachineSections = ["display", "graphics", "performance"];

    private readonly string _stateDir;
    private readonly string _database;
    private readonly string _events;
    private readonly string _clientSave;
    private readonly string _machine = Environment.MachineName;

    public CloudSave(string worldRoot, string database, string events, string clientSave)
    {
        _stateDir = Path.Combine(worldRoot, "save-sync");
        _database = database;
        _events = events;
        _clientSave = clientSave;
    }

    private string ConfigPath => Path.Combine(_stateDir, "cloud.json");
    private string StatePath => Path.Combine(_stateDir, "state.json");

    /// <summary>The cloud folder this computer syncs with ("" when sync is off).</summary>
    public string Folder
    {
        get
        {
            JsonNode? c = ReadJson(ConfigPath);
            return c?["enabled"]?.GetValue<bool>() == true ? c["folder"]?.GetValue<string>() ?? "" : "";
        }
    }

    public bool Enabled => Folder.Length > 0;
    public bool Reachable => Enabled && Directory.Exists(Folder);

    public void Enable(string folder)
    {
        Directory.CreateDirectory(folder);
        Directory.CreateDirectory(_stateDir);
        WriteJson(ConfigPath, new JsonObject { ["enabled"] = true, ["folder"] = folder });
    }

    public void Disable()
    {
        Directory.CreateDirectory(_stateDir);
        WriteJson(ConfigPath, new JsonObject { ["enabled"] = false, ["folder"] = Folder });
    }

    /// <summary>Google Drive for desktop's "My Drive" on this computer (any drive letter), or "".</summary>
    public static string FindMyDrive()
    {
        foreach (DriveInfo d in DriveInfo.GetDrives())
        {
            try
            {
                string p = Path.Combine(d.RootDirectory.FullName, "My Drive");
                if (d.IsReady && Directory.Exists(p))
                    return p;
            }
            catch { }
        }
        return "";
    }

    // ---------------------------------------------------------------- what the cloud holds

    public sealed record Info(string SavedAt, string Computer);

    public Info? CloudInfo()
    {
        JsonNode? n = ReadJson(Path.Combine(Folder, "save-info.json"));
        return n == null ? null : new Info(n["saved_at"]?.GetValue<string>() ?? "", n["computer"]?.GetValue<string>() ?? "");
    }

    /// <summary>Another computer is playing on the save now (its name and since when), or null.</summary>
    public (string Computer, DateTime Since)? InUseElsewhere()
    {
        JsonNode? n = ReadJson(Path.Combine(Folder, "in-use.json"));
        string who = n?["computer"]?.GetValue<string>() ?? "";
        if (who.Length == 0 || who == _machine)
            return null;
        DateTime.TryParse(n?["since"]?.GetValue<string>(), out DateTime since);
        return (who, since.ToLocalTime());
    }

    public void MarkInUse() =>
        WriteJson(Path.Combine(Folder, "in-use.json"), new JsonObject { ["computer"] = _machine, ["since"] = DateTime.UtcNow.ToString("o") });

    public void ClearInUse()
    {
        string p = Path.Combine(Folder, "in-use.json");
        if (ReadJson(p)?["computer"]?.GetValue<string>() == _machine)
            File.Delete(p);
    }

    /// <summary>The newest write to anything that travels.</summary>
    private string LocalStamp()
    {
        DateTime t = DateTime.MinValue;
        foreach (string f in new[] { _database, _database + "-wal", _events, Path.Combine(_clientSave, "settings.cfg") })
            if (File.Exists(f) && File.GetLastWriteTimeUtc(f) > t) t = File.GetLastWriteTimeUtc(f);
        foreach (string d in ClientDirs.Select(d => Path.Combine(_clientSave, d)).Where(Directory.Exists))
            foreach (string f in Directory.EnumerateFiles(d, "*", SearchOption.AllDirectories))
                if (File.GetLastWriteTimeUtc(f) > t) t = File.GetLastWriteTimeUtc(f);
        return t.ToString("o");
    }

    /// <summary>This computer has progress the cloud hasn't had yet.</summary>
    public bool LocalChanged()
    {
        JsonNode? s = ReadJson(StatePath);
        return s == null || string.CompareOrdinal(LocalStamp(), s["local_stamp"]?.GetValue<string>() ?? "") > 0;
    }

    public enum Choice { Cloud, Local, Cancel }

    /// <summary>Before playing: take the cloud's save when it is newer. ask(question) decides when both have changed.
    /// False when the player chose not to go on.</summary>
    public bool SyncIn(Func<string, Choice> ask, Action<string> log)
    {
        Info? info = CloudInfo();
        JsonNode? state = ReadJson(StatePath);
        if (info == null)
        {
            log("The cloud has no save yet - yours goes up when you stop the server.");
            return true;
        }
        bool cloudNew = state == null || state["synced_saved_at"]?.GetValue<string>() != info.SavedAt;
        bool localNew = state != null && LocalChanged();
        if (!cloudNew)
        {
            log(localNew ? "This computer's progress is newer than the cloud's - it goes up when you stop the server." : "Your save is up to date with the cloud.");
            return true;
        }
        string when = DateTime.TryParse(info.SavedAt, out DateTime w) ? w.ToLocalTime().ToString("g") : info.SavedAt;
        if (state == null && File.Exists(_database))
        {
            Choice c = ask($"This is the first sync on this computer.\n\nThe cloud holds a save from {info.Computer} ({when}), and this computer has its own game too.\n\nYes: play the CLOUD save here.\nNo: keep THIS computer's save (it replaces the cloud's when you stop the server).");
            if (c == Choice.Cancel) return false;
            if (c == Choice.Local)
            {
                WriteState(info.SavedAt, "0");
                log("Kept this computer's save.");
                return true;
            }
            Pull(info, log);
            return true;
        }
        if (localNew)
        {
            Choice c = ask($"Both have new progress: the cloud's save from {info.Computer} ({when}), and play on this computer that never reached the cloud.\n\nYes: play the CLOUD save.\nNo: keep THIS computer's.\n(The one you don't pick is kept in a backup.)");
            if (c == Choice.Cancel) return false;
            if (c == Choice.Local) { log("Kept this computer's save over the cloud's."); return true; }
        }
        Pull(info, log);
        return true;
    }

    private void Pull(Info info, Action<string> log)
    {
        string cur = Path.Combine(Folder, "current");
        string db = Path.GetFileName(_database);
        if (!File.Exists(Path.Combine(cur, db)))
            throw new IOException("The cloud save is incomplete (it has no game database).");
        Backup("before-pull");
        foreach (string s in new[] { "-wal", "-shm" })
            if (File.Exists(_database + s)) File.Delete(_database + s);
        Directory.CreateDirectory(Path.GetDirectoryName(_database)!);
        foreach (string n in new[] { db, db + "-wal", db + "-shm" })
            if (File.Exists(Path.Combine(cur, n))) File.Copy(Path.Combine(cur, n), Path.Combine(Path.GetDirectoryName(_database)!, n), true);
        string ev = Path.Combine(cur, Path.GetFileName(_events));
        if (File.Exists(ev)) File.Copy(ev, _events, true);
        string cc = Path.Combine(cur, "client");
        if (Directory.Exists(cc))
        {
            Directory.CreateDirectory(_clientSave);
            foreach (string f in ClientFiles.Where(f => File.Exists(Path.Combine(cc, f))))
            {
                if (f == "settings.cfg") MergeSettings(Path.Combine(cc, f), Path.Combine(_clientSave, f));
                else File.Copy(Path.Combine(cc, f), Path.Combine(_clientSave, f), true);
            }
            foreach (string d in ClientDirs.Where(d => Directory.Exists(Path.Combine(cc, d))))
            {
                string dst = Path.Combine(_clientSave, d);
                if (Directory.Exists(dst)) Directory.Delete(dst, true);
                CopyDir(Path.Combine(cc, d), dst);
            }
        }
        WriteState(info.SavedAt, LocalStamp());
        log($"Loaded your save from the cloud ({info.Computer}).");
    }

    /// <summary>After playing (the server stopped): this computer's save up to the cloud.</summary>
    public void Push(Action<string> log)
    {
        if (!File.Exists(_database))
            return;
        string stage = Path.Combine(Folder, "uploading");
        if (Directory.Exists(stage)) Directory.Delete(stage, true);
        Directory.CreateDirectory(stage);
        foreach (string f in new[] { _database, _database + "-wal", _database + "-shm", _events }.Where(File.Exists))
            File.Copy(f, Path.Combine(stage, Path.GetFileName(f)), true);
        string cs = Directory.CreateDirectory(Path.Combine(stage, "client")).FullName;
        foreach (string f in ClientFiles.Where(f => File.Exists(Path.Combine(_clientSave, f))))
            File.Copy(Path.Combine(_clientSave, f), Path.Combine(cs, f), true);
        foreach (string d in ClientDirs.Where(d => Directory.Exists(Path.Combine(_clientSave, d))))
            CopyDir(Path.Combine(_clientSave, d), Path.Combine(cs, d));
        // the whole save is written first, then swapped in: a half-copied save never replaces a whole one
        string cur = Path.Combine(Folder, "current"), prev = Path.Combine(Folder, "previous");
        if (Directory.Exists(cur))
        {
            if (Directory.Exists(prev)) Directory.Delete(prev, true);
            Directory.Move(cur, prev);
        }
        Directory.Move(stage, cur);
        string saved = DateTime.UtcNow.ToString("o"), stamp = LocalStamp();
        WriteJson(Path.Combine(Folder, "save-info.json"), new JsonObject
        {
            ["saved_at"] = saved, ["computer"] = _machine, ["local_stamp"] = stamp, ["db_bytes"] = new FileInfo(_database).Length,
        });
        WriteState(saved, stamp);
        log($"Your progress is saved to Google Drive ({new FileInfo(_database).Length / 1048576} MB).");
    }

    private void WriteState(string savedAt, string stamp)
    {
        Directory.CreateDirectory(_stateDir);
        WriteJson(StatePath, new JsonObject { ["synced_saved_at"] = savedAt, ["local_stamp"] = stamp, ["computer"] = _machine });
    }

    private void Backup(string why)
    {
        string root = Path.Combine(_stateDir, "backups");
        string dir = Path.Combine(root, $"{DateTime.Now:yyyyMMdd-HHmmss}-{why}");
        Directory.CreateDirectory(dir);
        foreach (string f in new[] { _database, _database + "-wal", _database + "-shm", _events }.Where(File.Exists))
            File.Copy(f, Path.Combine(dir, Path.GetFileName(f)), true);
        if (Directory.Exists(_clientSave))
        {
            string c = Directory.CreateDirectory(Path.Combine(dir, "client")).FullName;
            foreach (string f in ClientFiles.Where(f => File.Exists(Path.Combine(_clientSave, f))))
                File.Copy(Path.Combine(_clientSave, f), Path.Combine(c, f), true);
            foreach (string d in ClientDirs.Where(d => Directory.Exists(Path.Combine(_clientSave, d))))
                CopyDir(Path.Combine(_clientSave, d), Path.Combine(c, d));
        }
        foreach (string old in Directory.GetDirectories(root).OrderBy(d => d).SkipLast(5))
            Directory.Delete(old, true);
    }

    /// <summary>The incoming settings, with this computer's [display] / [graphics] / [performance] kept.</summary>
    private static void MergeSettings(string incoming, string target)
    {
        var inc = Sections(File.ReadAllText(incoming));
        if (File.Exists(target))
        {
            var mine = Sections(File.ReadAllText(target));
            foreach (string s in MachineSections)
            {
                if (mine.TryGetValue(s, out List<string>? lines)) inc[s] = lines;
                else inc.Remove(s);
            }
        }
        var sb = new StringBuilder();
        foreach (var (name, lines) in inc)
        {
            if (name.Length > 0) sb.Append('[').Append(name).Append("]\r\n");
            foreach (string l in lines) sb.Append(l).Append("\r\n");
        }
        File.WriteAllText(target + ".tmp", sb.ToString().TrimEnd() + "\r\n", new UTF8Encoding(false));
        File.Move(target + ".tmp", target, true);
    }

    private static Dictionary<string, List<string>> Sections(string text)
    {
        var o = new Dictionary<string, List<string>> { [""] = [] };
        string name = "";
        foreach (string line in text.Split('\n').Select(l => l.TrimEnd('\r')))
        {
            if (line.StartsWith('[') && line.TrimEnd().EndsWith(']'))
            {
                name = line.Trim()[1..^1];
                o[name] = [];
                continue;
            }
            o[name].Add(line);
        }
        return o;
    }

    private static void CopyDir(string from, string to)
    {
        Directory.CreateDirectory(to);
        foreach (string f in Directory.EnumerateFiles(from))
            File.Copy(f, Path.Combine(to, Path.GetFileName(f)), true);
        foreach (string d in Directory.EnumerateDirectories(from))
            CopyDir(d, Path.Combine(to, Path.GetFileName(d)));
    }

    private static JsonNode? ReadJson(string path)
    {
        try { return File.Exists(path) ? JsonNode.Parse(File.ReadAllText(path)) : null; }
        catch { return null; }
    }

    private static void WriteJson(string path, JsonNode node)
    {
        File.WriteAllText(path + ".tmp", node.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
        File.Move(path + ".tmp", path, true);
    }
}
