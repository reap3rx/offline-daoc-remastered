using System.IO.Compression;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text.Json;

namespace OfflineDaoc.Launcher;

/// <summary>
/// Installs and updates the game from a release's manifest (owner 2026-11-11: "once the game is installed you will not
/// need the installer ... the launcher will check for updates and then update the local files"). A release is a set of
/// packs - zips of whole parts of the install, made by source/tools/release/build_release.py - and a manifest.json
/// naming each pack, the files in it and their hashes. The launcher compares the newest manifest with the one it
/// installed and fetches only the packs whose content changed (or whose files are missing). A player's own files are
/// in no pack, so an update never touches them: client\save, world\logs, and the world database after the first
/// install (an "install only" pack). Files a new release no longer has are removed.
/// The install: client\launcher (this program), client\godot, client\tools, world\server, world\data, tools\dotnet.
/// update.json beside the launcher names the feed; without it (a developer's copy) there are no updates.
/// </summary>
internal sealed class Updater
{
    internal sealed record PackFile(string Path, long Size, string Sha256);

    internal sealed class Pack
    {
        public string Id = "", File = "", Tag = "", Sha256 = "", Content = "";
        public long Size;
        public bool InstallOnly;
        public List<PackFile> Files = [];
    }

    internal sealed class Manifest
    {
        public string Version = "", Released = "", Notes = "", Download = "";
        public List<Pack> Packs = [];
        public string Json = "";

        public static Manifest Parse(string json)
        {
            using var doc = JsonDocument.Parse(json);
            JsonElement r = doc.RootElement;
            var m = new Manifest
            {
                Json = json,
                Version = Str(r, "version"), Released = Str(r, "released"), Notes = Str(r, "notes"),
                Download = Str(r, "download"),
            };
            foreach (JsonElement p in r.GetProperty("packs").EnumerateArray())
            {
                var pack = new Pack
                {
                    Id = Str(p, "id"), File = Str(p, "file"), Tag = Str(p, "tag"), Sha256 = Str(p, "sha256"),
                    Content = Str(p, "content"), Size = p.GetProperty("size").GetInt64(),
                    InstallOnly = p.TryGetProperty("install_only", out JsonElement io) && io.GetBoolean(),
                };
                foreach (JsonElement f in p.GetProperty("files").EnumerateArray())
                    pack.Files.Add(new PackFile(f[0].GetString()!, f[1].GetInt64(), f[2].GetString()!));
                m.Packs.Add(pack);
            }
            return m;
        }

        private static string Str(JsonElement e, string name) =>
            e.TryGetProperty(name, out JsonElement v) && v.ValueKind == JsonValueKind.String ? v.GetString()! : "";

        public string UrlOf(Pack p) => Download.Replace("{tag}", p.Tag).Replace("{file}", p.File);
    }

    internal sealed record Plan(Manifest Latest, List<Pack> Needed, long DownloadBytes, bool FirstInstall)
    {
        public bool UpToDate => Needed.Count == 0;
    }

    public readonly string LauncherDirectory;
    public readonly string InstallRoot;
    private readonly string _feed;
    private static readonly HttpClient Http = CreateHttp();

    public Updater(string launcherDirectory)
    {
        LauncherDirectory = Path.GetFullPath(launcherDirectory).TrimEnd(Path.DirectorySeparatorChar);
        InstallRoot = Path.GetFullPath(Path.Combine(LauncherDirectory, "..", ".."));
        _feed = ReadFeed(Path.Combine(LauncherDirectory, "update.json"));
    }

    /// <summary>There is somewhere to update from (a release install; a developer's copy has no update.json).</summary>
    public bool Enabled => _feed.Length > 0;
    private string InstalledPath => Path.Combine(LauncherDirectory, "installed-manifest.json");
    private string WorkDirectory => Path.Combine(InstallRoot, ".update");

    /// <summary>The game files are on this computer (the installer puts only the launcher here; the rest is downloaded).</summary>
    public bool GameInstalled => File.Exists(Path.Combine(InstallRoot, "client", "godot", "project.godot"))
        && File.Exists(Path.Combine(InstallRoot, "world", "server", "CoreServer.exe"));

    public Manifest? Installed
    {
        get
        {
            try { return File.Exists(InstalledPath) ? Manifest.Parse(File.ReadAllText(InstalledPath)) : null; }
            catch { return null; }
        }
    }

    private static HttpClient CreateHttp()
    {
        var http = new HttpClient(new SocketsHttpHandler { AllowAutoRedirect = true, MaxAutomaticRedirections = 10 })
        {
            Timeout = Timeout.InfiniteTimeSpan,
        };
        http.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("OfflineDAoCRemastered", "1.0"));
        return http;
    }

    private static string ReadFeed(string path)
    {
        try
        {
            if (!File.Exists(path)) return "";
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            return doc.RootElement.TryGetProperty("feed", out JsonElement f) ? f.GetString() ?? "" : "";
        }
        catch { return ""; }
    }

    /// <summary>The newest release and what this computer needs from it.</summary>
    public async Task<Plan> CheckAsync(CancellationToken ct)
    {
        using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        cts.CancelAfter(TimeSpan.FromSeconds(30));
        string json = await Http.GetStringAsync(_feed, cts.Token);
        Manifest latest = Manifest.Parse(json);
        Manifest? installed = Installed;
        bool first = installed == null || !GameInstalled;
        return await Task.Run(() =>
        {
            var have = installed?.Packs.ToDictionary(p => p.Id, p => p.Content) ?? [];
            var needed = new List<Pack>();
            foreach (Pack p in latest.Packs)
            {
                bool missing = p.Files.Any(f => !File.Exists(Full(f.Path)));
                if (p.InstallOnly ? missing && !p.Files.Any(f => File.Exists(Full(f.Path)))
                                  : missing || !have.TryGetValue(p.Id, out string? c) || c != p.Content)
                    needed.Add(p);
            }
            return new Plan(latest, needed, needed.Sum(p => p.Size), first);
        }, ct);
    }

    private string Full(string rel) => Path.GetFullPath(Path.Combine(InstallRoot, rel.Replace('/', Path.DirectorySeparatorChar)));

    /// <summary>Fetches and lays down the plan's packs. progress(done bytes, total bytes, what). True when this launcher's
    /// own files changed (it needs a restart).</summary>
    public async Task<bool> ApplyAsync(Plan plan, Action<long, long, string> progress, CancellationToken ct)
    {
        Directory.CreateDirectory(WorkDirectory);
        long total = plan.DownloadBytes, before = 0;
        long free = new DriveInfo(Path.GetPathRoot(InstallRoot)!).AvailableFreeSpace;
        long unpacked = plan.Needed.Sum(p => p.Files.Sum(f => f.Size));
        long biggest = plan.Needed.Count == 0 ? 0 : plan.Needed.Max(p => p.Size);
        if (free < unpacked + biggest + 1_000_000_000L)
            throw new IOException($"Not enough free space on {Path.GetPathRoot(InstallRoot)}: about {(unpacked + biggest) / 1e9 + 1:F1} GB is needed, {free / 1e9:F1} GB is free.");
        bool launcherChanged = false;
        int n = 0;
        foreach (Pack pack in plan.Needed)
        {
            n++;
            string label = $"pack {n} of {plan.Needed.Count} ({pack.Id})";
            string zip = Path.Combine(WorkDirectory, pack.File);
            long start = before;
            await DownloadAsync(plan.Latest.UrlOf(pack), zip, pack, (d) => progress(start + d, total, "Downloading " + label), ct);
            progress(start + pack.Size, total, "Unpacking " + label);
            launcherChanged |= await Task.Run(() => Unpack(zip, pack, ct), ct);
            File.Delete(zip);
            before += pack.Size;
        }
        // files the new release no longer has (never a player's: those are in no pack)
        Manifest? old = Installed;
        if (old != null)
        {
            var keep = new HashSet<string>(plan.Latest.Packs.SelectMany(p => p.Files).Select(f => f.Path), StringComparer.OrdinalIgnoreCase);
            foreach (PackFile f in old.Packs.Where(p => !p.InstallOnly).SelectMany(p => p.Files))
                if (!keep.Contains(f.Path))
                    try { File.Delete(Full(f.Path)); } catch { /* in use: left for the next update */ }
        }
        File.WriteAllText(InstalledPath + ".tmp", plan.Latest.Json);
        File.Move(InstalledPath + ".tmp", InstalledPath, true);
        try { Directory.Delete(WorkDirectory, true); } catch { }
        return launcherChanged;
    }

    private static async Task DownloadAsync(string url, string path, Pack pack, Action<long> progress, CancellationToken ct)
    {
        if (File.Exists(path) && new FileInfo(path).Length == pack.Size && await HashAsync(path, ct) == pack.Sha256)
            return;                                                  // (an earlier try got all of it)
        string part = path + ".part";
        for (int attempt = 1; ; attempt++)
        {
            try
            {
                long have = File.Exists(part) ? new FileInfo(part).Length : 0;
                if (have > pack.Size) { File.Delete(part); have = 0; }
                using var request = new HttpRequestMessage(HttpMethod.Get, url);
                if (have > 0) request.Headers.Range = new RangeHeaderValue(have, null);
                using HttpResponseMessage response = await Http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct);
                if (have > 0 && response.StatusCode != System.Net.HttpStatusCode.PartialContent)
                    have = 0;                                       // the host won't resume: start over
                response.EnsureSuccessStatusCode();
                await using (Stream body = await response.Content.ReadAsStreamAsync(ct))
                await using (var file = new FileStream(part, have > 0 ? FileMode.Append : FileMode.Create, FileAccess.Write, FileShare.None, 1 << 20))
                {
                    var buffer = new byte[1 << 20];
                    long done = have;
                    int read;
                    while ((read = await body.ReadAsync(buffer, ct)) > 0)
                    {
                        await file.WriteAsync(buffer.AsMemory(0, read), ct);
                        done += read;
                        progress(done);
                    }
                }
                if (await HashAsync(part, ct) != pack.Sha256)
                {
                    File.Delete(part);
                    throw new InvalidDataException($"{pack.File} arrived damaged.");
                }
                File.Move(part, path, true);
                return;
            }
            catch (Exception e) when (e is HttpRequestException or IOException or InvalidDataException && attempt < 5 && !ct.IsCancellationRequested)
            {
                await Task.Delay(TimeSpan.FromSeconds(3 * attempt), ct);
            }
        }
    }

    private static async Task<string> HashAsync(string path, CancellationToken ct)
    {
        await using var s = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 20, true);
        return Convert.ToHexString(await SHA256.HashDataAsync(s, ct)).ToLowerInvariant();
    }

    /// <summary>A pack's files into place. A file in use (this launcher's own) is moved aside as .old and replaced.</summary>
    private bool Unpack(string zipPath, Pack pack, CancellationToken ct)
    {
        bool launcher = false;
        using ZipArchive zip = ZipFile.OpenRead(zipPath);
        foreach (ZipArchiveEntry entry in zip.Entries)
        {
            ct.ThrowIfCancellationRequested();
            if (entry.FullName.EndsWith('/'))
                continue;
            string dest = Full(entry.FullName);
            if (!dest.StartsWith(InstallRoot, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException($"{pack.File} holds a file outside the game folder ({entry.FullName}).");
            if (pack.InstallOnly && File.Exists(dest))
                continue;                                          // a player's own (the world database) is never replaced
            Directory.CreateDirectory(Path.GetDirectoryName(dest)!);
            string tmp = dest + ".new";
            entry.ExtractToFile(tmp, true);
            try { File.Move(tmp, dest, true); }
            catch (IOException) when (File.Exists(dest))
            {
                File.Move(dest, dest + ".old", true);              // running: Windows lets it be renamed, not replaced
                File.Move(tmp, dest);
            }
            catch (UnauthorizedAccessException) when (File.Exists(dest))
            {
                File.Move(dest, dest + ".old", true);
                File.Move(tmp, dest);
            }
            if (dest.StartsWith(LauncherDirectory + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                launcher = true;
        }
        return launcher;
    }

    /// <summary>The .old files an earlier update left beside the launcher (they were in use then).</summary>
    public void CleanUp()
    {
        try
        {
            foreach (string f in Directory.EnumerateFiles(LauncherDirectory, "*.old", SearchOption.AllDirectories))
                try { File.Delete(f); } catch { }
        }
        catch { }
    }

    public static int CompareVersions(string a, string b)
    {
        static int[] Parts(string v) => v.TrimStart('v', 'V').Split('.', '-').Select(x => int.TryParse(x, out int n) ? n : 0).ToArray();
        int[] x = Parts(a), y = Parts(b);
        for (int i = 0; i < Math.Max(x.Length, y.Length); i++)
        {
            int c = (i < x.Length ? x[i] : 0).CompareTo(i < y.Length ? y[i] : 0);
            if (c != 0) return c;
        }
        return 0;
    }
}
