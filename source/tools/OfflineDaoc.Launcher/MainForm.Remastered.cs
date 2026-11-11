using System.Diagnostics;
using System.Data.SQLite;

namespace OfflineDaoc.Launcher;

/// <summary>
/// The Remastered launcher's own parts (owner 2026-11-11): installing the game and keeping it up to date (Updater), and
/// your progress on more than one computer through Google Drive (CloudSave).
///   - The installer puts only this launcher on the computer; the first start downloads the game (INSTALL GAME).
///   - Each start asks the release feed whether there is a newer version; UPDATE fetches only what changed.
///   - Options > CLOUD SAVE connects a Google Drive folder; with it on, the cloud's save is taken before you play and
///     yours goes up each time the server stops.
/// </summary>
internal sealed partial class MainForm
{
    private const int FirstRosterPerRealm = 2000;
    private Updater? _updater;
    private Updater.Plan? _updatePlan;
    private bool _updating;
    private readonly Button _updateButton = ActionButton("CHECK UPDATES", Color.FromArgb(150, 118, 52));
    private CloudSave? _cloud;
    private readonly Label _cloudStatus = new() { AutoSize = true, MaximumSize = new Size(620, 0), ForeColor = DaocTheme.Parchment, Font = new Font("Georgia", 9f) };
    private readonly Button _cloudButton = new() { AutoSize = true, Text = "Connect Google Drive…" };

    private string ClientSaveFolder => Path.GetFullPath(Path.Combine(_launcherRoot, "..", "save", "Godot", "app_userdata", "MMOEngine"));

    private void InitRemastered()
    {
        _updater = new Updater(_launcherRoot);
        _updateButton.Click += async (_, _) => await UpdateClickedAsync();
        _updateButton.Visible = _updater.Enabled;
        _cloud = new CloudSave(_root, _database, Path.Combine(_serverDirectory, "realm-event-records.sqlite3"), ClientSaveFolder);
        _cloudButton.Click += (_, _) => ToggleCloud();
        ShowCloudState();
    }

    /// <summary>When the window first shows: the install (first start), the update check, the cloud's save.</summary>
    private async Task RemasteredShownAsync()
    {
        if (_updater == null || !_updater.Enabled)
        {
            CloudSyncIn();
            return;
        }
        _updater.CleanUp();
        if (!_updater.GameInstalled)
        {
            _startButton.Enabled = _playButton.Enabled = false;
            _updateButton.Text = "INSTALL GAME";
            _footer.Text = "Welcome! The game itself is not on this computer yet - checking the download…";
        }
        await CheckForUpdatesAsync(quiet: true);
        if (_updater.GameInstalled)
            CloudSyncIn();
    }

    private async Task CheckForUpdatesAsync(bool quiet)
    {
        if (_updater == null || _updating)
            return;
        _updateButton.Enabled = false;
        try
        {
            _updatePlan = await _updater.CheckAsync(CancellationToken.None);
            Updater.Plan p = _updatePlan;
            if (p.FirstInstall)
            {
                _updateButton.Text = "INSTALL GAME";
                _footer.Text = $"Ready to install Offline DAoC Remastered {p.Latest.Version}: {p.DownloadBytes / 1e9:F1} GB to download. Click INSTALL GAME.";
            }
            else if (p.UpToDate)
            {
                _updateButton.Text = "UP TO DATE";
                if (!quiet) _footer.Text = $"You have the newest version ({p.Latest.Version}).";
            }
            else
            {
                _updateButton.Text = $"UPDATE {p.Latest.Version}";
                _footer.Text = $"Version {p.Latest.Version} is out ({FormatBytes(p.DownloadBytes)} to download). Stop the server and click UPDATE.";
            }
        }
        catch (Exception e)
        {
            if (!_updater.GameInstalled)
                _footer.Text = "Can't reach the download right now (" + e.Message + "). Check your internet connection and click INSTALL GAME to try again.";
            else if (!quiet)
                _footer.Text = "Can't check for updates right now: " + e.Message;
            _updateButton.Text = _updater.GameInstalled ? "CHECK UPDATES" : "INSTALL GAME";
            _updatePlan = null;
        }
        finally
        {
            _updateButton.Enabled = true;
        }
    }

    private static string FormatBytes(long b) => b >= 1_000_000_000 ? $"{b / 1e9:F1} GB" : $"{Math.Max(1, b / 1_000_000)} MB";

    private async Task UpdateClickedAsync()
    {
        if (_updater == null || _updating)
            return;
        if (_updatePlan == null || _updatePlan.UpToDate)
        {
            await CheckForUpdatesAsync(quiet: false);
            if (_updatePlan == null || _updatePlan.UpToDate)
                return;
        }
        if (IsServerRunning() || FindExactServerProcess() is not null || GameClientRunning())
        {
            MessageBox.Show(this, "Close the game and stop the server first - the update replaces their files.", "Update", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        Updater.Plan plan = _updatePlan;
        bool first = plan.FirstInstall;
        if (!first && !string.IsNullOrWhiteSpace(plan.Latest.Notes) &&
            MessageBox.Show(this, $"Version {plan.Latest.Version}\n\n{plan.Latest.Notes.Trim()}\n\nUpdate now? ({FormatBytes(plan.DownloadBytes)})", "Update",
                MessageBoxButtons.OKCancel, MessageBoxIcon.Information) != DialogResult.OK)
            return;
        _updating = true;
        _startButton.Enabled = _playButton.Enabled = _updateButton.Enabled = false;
        var progress = new Progress<(long Done, long Total, string What)>(p =>
        {
            int pct = p.Total > 0 ? (int)(100 * p.Done / p.Total) : 100;
            _updateButton.Text = (first ? "INSTALLING " : "UPDATING ") + pct + "%";
            _footer.Text = $"{p.What} - {FormatBytes(p.Done)} of {FormatBytes(p.Total)}. You can leave this running.";
        });
        bool restart = false;
        try
        {
            IProgress<(long, long, string)> report = progress;
            restart = await _updater.ApplyAsync(plan, (d, t, w) => report.Report((d, t, w)), CancellationToken.None);
            if (first)
                await FirstInstallAsync();
            _footer.Text = first ? $"Offline DAoC Remastered {plan.Latest.Version} is installed. Click START SERVER, then ENTER REALM." :
                $"Updated to {plan.Latest.Version}.";
            _updatePlan = null;
            _updateButton.Text = "UP TO DATE";
        }
        catch (Exception e)
        {
            MessageBox.Show(this, $"The {(first ? "install" : "update")} stopped: {e.Message}\n\nClick the button again to carry on where it left off.",
                "Offline DAoC Remastered", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            _updateButton.Text = first ? "INSTALL GAME" : "RETRY UPDATE";
        }
        finally
        {
            _updating = false;
            _updateButton.Enabled = true;
            await RefreshDashboardAsync();
        }
        if (restart)
        {
            MessageBox.Show(this, "The launcher itself was updated - it will restart now.", "Offline DAoC Remastered", MessageBoxButtons.OK, MessageBoxIcon.Information);
            Process.Start(new ProcessStartInfo(Path.Combine(_launcherRoot, Path.GetFileName(Environment.ProcessPath!))) { UseShellExecute = true });
            _closeAfterServerStop = true;
            Close();
        }
    }

    /// <summary>A new world's first start: its own living population, and the offer to keep the save in Google Drive.</summary>
    private async Task FirstInstallAsync()
    {
        _footer.Text = "Rolling this world's population of player bots…";
        try
        {
            await Task.Run(() => PopulationRoster.Build(_database, _root, FirstRosterPerRealm));
        }
        catch (Exception e)
        {
            MessageBox.Show(this, "The bot roster could not be made (" + e.Message + "). Use the Population tab's BUILD ROSTER later.",
                "Offline DAoC Remastered", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        if (_cloud != null && !_cloud.Enabled &&
            MessageBox.Show(this,
                "Do you want to play on more than one computer?\n\n" +
                "Offline DAoC Remastered can keep your progress in your Google Drive, so another computer with the game picks up where you left off. " +
                "It needs Google Drive for desktop, signed in to your Google account.\n\n" +
                "If you only play here, choose No - you can turn it on later in Options.",
                "Cloud save (optional)", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
            ConnectCloud();
    }

    private bool GameClientRunning()
    {
        string exe = Path.GetFileNameWithoutExtension(NewClientExecutable);
        foreach (Process p in Process.GetProcessesByName(exe))
        {
            try
            {
                if (p.MainModule?.FileName is string f && f.StartsWith(Path.GetFullPath(Path.Combine(_launcherRoot, "..")), StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            catch { return true; }
        }
        return false;
    }

    // ---------------------------------------------------------------- cloud save

    internal Control BuildCloudSavePanel()
    {
        var surface = new InsetPanel { Dock = DockStyle.Top, Height = 150, Margin = new Padding(18), Padding = new Padding(20), Accent = DaocTheme.Gold };
        var flow = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown, WrapContents = false, BackColor = Color.Transparent };
        flow.Controls.Add(new Label { AutoSize = true, Text = "CLOUD SAVE  •  GOOGLE DRIVE", Font = new Font("Georgia", 13f, FontStyle.Bold), ForeColor = DaocTheme.GoldLight });
        flow.Controls.Add(new Label
        {
            AutoSize = true, MaximumSize = new Size(820, 0), ForeColor = DaocTheme.Parchment, Font = new Font("Georgia", 9f), Margin = new Padding(3, 6, 3, 6),
            Text = "Optional: play on more than one computer. Your progress is kept in Google Drive (My Drive\\OfflineDAoC Saves) - taken when the launcher starts, " +
                   "saved each time you stop the server. Needs Google Drive for desktop, signed in. Don't play on two computers at once.",
        });
        StyleInputButton(_cloudButton);
        flow.Controls.Add(_cloudButton);
        flow.Controls.Add(_cloudStatus);
        surface.Controls.Add(flow);
        return surface;
    }

    private static void StyleInputButton(Button b)
    {
        b.FlatStyle = FlatStyle.Flat;
        b.BackColor = DaocTheme.StoneLight;
        b.ForeColor = DaocTheme.GoldLight;
        b.Font = new Font("Georgia", 9f, FontStyle.Bold);
    }

    private void ShowCloudState()
    {
        if (_cloud == null)
            return;
        if (!_cloud.Enabled)
        {
            _cloudButton.Text = "Connect Google Drive…";
            _cloudStatus.Text = "Off - your progress stays on this computer.";
            return;
        }
        _cloudButton.Text = "Turn off cloud save";
        CloudSave.Info? info = _cloud.Reachable ? _cloud.CloudInfo() : null;
        _cloudStatus.Text = !_cloud.Reachable ? $"On, but {_cloud.Folder} can't be reached - is Google Drive for desktop running?" :
            info == null ? $"On - {_cloud.Folder} (no save there yet)." :
            $"On - {_cloud.Folder}. Last save from {info.Computer}, {(DateTime.TryParse(info.SavedAt, out DateTime t) ? t.ToLocalTime().ToString("g") : info.SavedAt)}.";
    }

    private void ToggleCloud()
    {
        if (_cloud == null)
            return;
        if (_cloud.Enabled)
        {
            _cloud.Disable();
            ShowCloudState();
            return;
        }
        ConnectCloud();
    }

    private void ConnectCloud()
    {
        if (_cloud == null)
            return;
        string myDrive = CloudSave.FindMyDrive();
        if (myDrive.Length == 0)
        {
            if (MessageBox.Show(this,
                    "Google Drive for desktop isn't on this computer (or isn't signed in).\n\nInstall it, sign in with your Google account, then click Connect Google Drive again (Options tab).\n\nOpen the download page now?",
                    "Cloud save", MessageBoxButtons.YesNo, MessageBoxIcon.Information) == DialogResult.Yes)
                Process.Start(new ProcessStartInfo("https://www.google.com/drive/download/") { UseShellExecute = true });
            return;
        }
        string folder = Path.Combine(myDrive, CloudSave.FolderName);
        try
        {
            _cloud.Enable(folder);
            if (!IsServerRunning())
            {
                if (_cloud.CloudInfo() != null) CloudSyncIn();
                else _cloud.Push(s => _footer.Text = s);
            }
        }
        catch (Exception e)
        {
            MessageBox.Show(this, "Couldn't use " + folder + ": " + e.Message, "Cloud save", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        ShowCloudState();
    }

    /// <summary>Before playing: the cloud's save, when it is newer (asks when both changed).</summary>
    private void CloudSyncIn()
    {
        if (_cloud == null || !_cloud.Enabled || IsServerRunning() || FindExactServerProcess() is not null)
            return;
        if (!_cloud.Reachable)
        {
            _footer.Text = "Cloud save: Google Drive can't be reached - you are playing this computer's save.";
            return;
        }
        try
        {
            if (_cloud.InUseElsewhere() is { } other &&
                MessageBox.Show(this, $"Your save is marked as in use on {other.Computer} since {other.Since:g}.\n\nIf you are still playing there, quit there first - " +
                    "its progress hasn't reached the cloud yet.\n\nPlay here anyway?", "Cloud save", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes)
            {
                _startButton.Enabled = false;
                _footer.Text = "Waiting for the other computer - restart the launcher when it has finished.";
                return;
            }
            bool go = _cloud.SyncIn(question => MessageBox.Show(this, question, "Cloud save", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Question) switch
            {
                DialogResult.Yes => CloudSave.Choice.Cloud,
                DialogResult.No => CloudSave.Choice.Local,
                _ => CloudSave.Choice.Cancel,
            }, s => _footer.Text = s);
            if (!go)
            {
                _startButton.Enabled = false;
                _footer.Text = "Nothing was changed. Restart the launcher to choose again.";
                return;
            }
            _cloud.MarkInUse();
        }
        catch (Exception e)
        {
            MessageBox.Show(this, "Cloud save problem: " + e.Message + "\n\nYou are playing this computer's save.", "Cloud save", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        ShowCloudState();
    }

    /// <summary>The server stopped: your progress up to the cloud.</summary>
    private void CloudPushAfterStop()
    {
        if (_cloud == null || !_cloud.Enabled)
            return;
        CloudSave cloud = _cloud;
        _ = Task.Run(async () =>
        {
            await Task.Delay(3000);                      // (the server lets go of the database)
            try
            {
                if (!cloud.Reachable) throw new IOException("Google Drive can't be reached");
                cloud.Push(s => BeginInvoke(() => { _footer.Text = s; ShowCloudState(); }));
            }
            catch (Exception e)
            {
                BeginInvoke(() => MessageBox.Show(this, "Your progress could not be saved to Google Drive: " + e.Message +
                    "\n\nIt is safe on this computer and goes up the next time the server stops.", "Cloud save", MessageBoxButtons.OK, MessageBoxIcon.Warning));
            }
        });
    }

    /// <summary>The launcher closes (the server stopped): anything not yet saved goes up, and the save is free again.</summary>
    private void CloudOnClose()
    {
        if (_cloud == null || !_cloud.Enabled || !_cloud.Reachable || _serverProcess is { HasExited: false })
            return;
        try
        {
            if (_cloud.LocalChanged())
                _cloud.Push(_ => { });
            _cloud.ClearInUse();
        }
        catch { /* the next stop or start catches up */ }
    }
}
