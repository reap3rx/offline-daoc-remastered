# Offline DAoC save sync (owner 2026-10-28): your progress follows you between computers through a Google Drive
# folder (default G:\My Drive\OfflineDAoC Saves - Google Drive for desktop).
#
#   -Play   (PLAY OFFLINE DAOC (SYNCED).cmd) pull a newer save from the cloud, mark the save "in use on <this PC>",
#           start the new client's launcher, then (hidden, in the background) push the save back every time the
#           server stops and when the launcher closes, and clear the mark.
#   -Push   (SAVE NOW (SYNC).cmd) push now - only while the server is stopped.
#   -Pull   pull the cloud save now (asks first when this PC has unsynced progress).
#   -Status what the cloud and this PC hold.
#
# What travels: the game database (runtime\data\opendaoc.sqlite3.db + its -wal/-shm while they exist), the realm
# event records, and the new client's settings, keybinds, quickbars and character looks. What stays per computer:
# the client's [display], [graphics] and [performance] settings (a work PC is not your gaming PC), shader caches, logs.
# The database is only ever copied while the server is stopped (a copy of an open SQLite database can be torn).
# Before anything is overwritten on this PC it is copied to runtime\save-sync\backups (the last 5 kept); the cloud
# keeps the previous save too (OfflineDAoC Saves\previous).
param(
    [switch]$Play, [switch]$Push, [switch]$Pull, [switch]$Status, [switch]$Watch,
    [int]$LauncherPid = 0,
    [string]$Root = "",                 # (tests) the game folder; default: two levels up from this script
    [string]$Cloud = "",                # (tests / other drive letters) the cloud folder
    [switch]$Yes                        # (tests) answer the questions with their default
)
$ErrorActionPreference = 'Stop'
if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
$StateDir = Join-Path $Root 'runtime\save-sync'
New-Item -ItemType Directory -Force $StateDir | Out-Null
$LogFile = Join-Path $StateDir 'sync.log'
$Machine = $env:COMPUTERNAME

function Log([string]$msg) {
    $line = "{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $msg
    Add-Content -Path $LogFile -Value $line
    if (-not $Watch) { Write-Host $msg }
}

function Ask([string]$question, [string]$default = 'n') {
    if ($Yes -or $Watch) { return $default }
    $a = Read-Host "$question"
    if (-not $a) { return $default }
    return $a.Trim().ToLower().Substring(0, 1)
}

# ---------------------------------------------------------------- where things are

function Find-Cloud {
    if ($Cloud) { return $Cloud }
    $cfg = Join-Path $StateDir 'cloud-folder.txt'           # this PC's own choice (another drive letter)
    if (Test-Path $cfg) {
        $p = (Get-Content $cfg -TotalCount 1).Trim()
        if ($p) { return $p }
    }
    if (Test-Path 'G:\My Drive\OfflineDAoC Saves') { return 'G:\My Drive\OfflineDAoC Saves' }
    foreach ($d in [char[]]'DEFGHIJKLMNOPQRSTUVWXYZ') {   # Drive for desktop may have another letter here
        $p = "${d}:\My Drive\OfflineDAoC Saves"
        if (Test-Path $p) { return $p }
    }
    return ""
}

$ClientSave = Join-Path $Root 'new-client\save\Godot\app_userdata\MMOEngine'
$DbDir = Join-Path $Root 'runtime\data'
$DbName = 'opendaoc.sqlite3.db'
$Local = @{
    db = Join-Path $DbDir $DbName
    events = Join-Path $Root 'runtime\server\realm-event-records.sqlite3'
}
$ClientFiles = @('settings.cfg', 'keybinds.cfg', 'server_looks.json')
$ClientDirs = @('server_quickbars', 'keybinds', 'world')
$MachineSections = @('display', 'graphics', 'performance')

function Server-Running {
    $exe = Join-Path $Root 'runtime\server\CoreServer.exe'
    return @(Get-CimInstance Win32_Process -Filter "Name='CoreServer.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -eq $exe }).Count -gt 0
}

function Launcher-Running {
    $launcher = Join-Path $Root 'new-client\runtime\OfflineDAoC.exe'
    return @(Get-CimInstance Win32_Process -Filter "Name='OfflineDAoC.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -eq $launcher }).Count -gt 0
}

function Game-Running {
    return (Server-Running) -or (Launcher-Running)
}

# A server left running with no launcher (owner 2026-10-28: the launcher closed in a hurry left CoreServer running
# unseen, and the next PLAY said "already running"): offered to be stopped. Without its launcher it can't be asked to
# shut down, so it is closed; characters are saved when they log out. The earlier session's save watcher then saves
# to the cloud and clears the in-use mark - waited for here.
function Stop-LeftoverServer {
    $exe = Join-Path $Root 'runtime\server\CoreServer.exe'
    $procs = @(Get-CimInstance Win32_Process -Filter "Name='CoreServer.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -eq $exe })
    if ($procs.Count -eq 0) { return $true }
    $since = $procs[0].CreationDate
    Write-Host ""
    Write-Host "A game server from an earlier session is still running (started $since)."
    Write-Host "The launcher was closed without stopping it, so it has no window."
    $a = Ask "Stop it and play? [Y/n]" 'y'
    if ($a -eq 'n') { return $false }
    foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    $deadline = (Get-Date).AddSeconds(15)
    while ((Server-Running) -and (Get-Date) -lt $deadline) { Start-Sleep 1 }
    if (Server-Running) { Write-Host "The server didn't stop - close CoreServer in Task Manager, then try again."; return $false }
    Write-Host "Stopped. Saving the last session to the cloud..."
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        $watchers = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'savesync\.ps1' -and $_.CommandLine -match '-Watch' })
        if ($watchers.Count -eq 0) { break }
        Start-Sleep 2
    }
    return $true
}

function Local-Stamp {
    # newest write to anything that travels (the database's -wal holds recent progress until a checkpoint)
    $t = [datetime]::MinValue
    foreach ($f in @($Local.db, "$($Local.db)-wal", $Local.events, (Join-Path $ClientSave 'settings.cfg'))) {
        if (Test-Path $f) { $w = (Get-Item $f).LastWriteTimeUtc; if ($w -gt $t) { $t = $w } }
    }
    foreach ($d in $ClientDirs) {
        $p = Join-Path $ClientSave $d
        if (Test-Path $p) { Get-ChildItem $p -Recurse -File | ForEach-Object { if ($_.LastWriteTimeUtc -gt $t) { $t = $_.LastWriteTimeUtc } } }
    }
    return $t.ToString('o')
}

function Read-Json([string]$path) {
    if (Test-Path $path) { try { return Get-Content $path -Raw | ConvertFrom-Json } catch { } }
    return $null
}

function Write-Json([string]$path, $obj) {
    $tmp = "$path.tmp"
    $obj | ConvertTo-Json | Set-Content -Path $tmp -Encoding UTF8
    Move-Item -Force $tmp $path
}

$StateFile = Join-Path $StateDir 'state.json'

# ---------------------------------------------------------------- settings: keep this PC's machine sections

function Cfg-Sections([string]$text) {
    $out = [ordered]@{}
    $name = ''
    $out[$name] = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($text -split "`r?`n")) {
        if ($line -match '^\[(.+)\]\s*$') { $name = $Matches[1]; $out[$name] = New-Object System.Collections.Generic.List[string]; continue }
        $out[$name].Add($line)
    }
    return $out
}

function Merge-Settings([string]$incoming, [string]$target) {
    # the incoming settings, with this PC's [display] / [graphics] / [performance] kept
    $inc = Cfg-Sections (Get-Content $incoming -Raw)
    if (Test-Path $target) {
        $mine = Cfg-Sections (Get-Content $target -Raw)
        foreach ($s in $MachineSections) {
            if ($mine.Contains($s)) { $inc[$s] = $mine[$s] } elseif ($inc.Contains($s)) { $inc.Remove($s) }
        }
    }
    $sb = New-Object System.Text.StringBuilder
    foreach ($k in $inc.Keys) {
        if ($k -ne '') { [void]$sb.AppendLine("[$k]") }
        foreach ($l in $inc[$k]) { [void]$sb.AppendLine($l) }
    }
    # (no byte-order mark: the client reads it with Godot's ConfigFile)
    [System.IO.File]::WriteAllText("$target.tmp", $sb.ToString().TrimEnd() + "`r`n", (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -Force "$target.tmp" $target
}

# ---------------------------------------------------------------- copying

function Backup-Local([string]$why) {
    $dir = Join-Path $StateDir ("backups\{0:yyyyMMdd-HHmmss}-{1}" -f (Get-Date), $why)
    New-Item -ItemType Directory -Force $dir | Out-Null
    foreach ($f in @($Local.db, "$($Local.db)-wal", "$($Local.db)-shm", $Local.events)) {
        if (Test-Path $f) { Copy-Item $f $dir }
    }
    if (Test-Path $ClientSave) {
        $c = New-Item -ItemType Directory -Force (Join-Path $dir 'client')
        foreach ($f in $ClientFiles) { $p = Join-Path $ClientSave $f; if (Test-Path $p) { Copy-Item $p $c } }
        foreach ($d in $ClientDirs) { $p = Join-Path $ClientSave $d; if (Test-Path $p) { Copy-Item $p $c -Recurse } }
    }
    $all = @(Get-ChildItem (Join-Path $StateDir 'backups') -Directory | Sort-Object Name)
    if ($all.Count -gt 5) { $all | Select-Object -First ($all.Count - 5) | Remove-Item -Recurse -Force }
    Log "Backed up this PC's save to $dir"
}

function Do-Push([string]$cloud) {
    if (Server-Running) { throw "The server is running - stop it (STOP SERVER in the launcher) before saving to the cloud." }
    if (-not (Test-Path $Local.db)) { throw "No game database at $($Local.db)." }
    $prev = Join-Path $cloud 'previous'
    $stage = Join-Path $cloud 'uploading'
    if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
    New-Item -ItemType Directory -Force $stage | Out-Null
    # everything into a staging folder first, then swapped in: a half-written save never replaces a whole one
    foreach ($f in @($Local.db, "$($Local.db)-wal", "$($Local.db)-shm", $Local.events)) {
        if (Test-Path $f) { Copy-Item $f $stage }
    }
    $cs = New-Item -ItemType Directory -Force (Join-Path $stage 'client')
    foreach ($f in $ClientFiles) { $p = Join-Path $ClientSave $f; if (Test-Path $p) { Copy-Item $p $cs } }
    foreach ($d in $ClientDirs) { $p = Join-Path $ClientSave $d; if (Test-Path $p) { Copy-Item $p $cs -Recurse } }
    $cur = Join-Path $cloud 'current'
    if (Test-Path $cur) {
        if (Test-Path $prev) { Remove-Item $prev -Recurse -Force }
        Rename-Item $cur 'previous'
    }
    Rename-Item $stage 'current'
    $stamp = Local-Stamp
    $info = [ordered]@{ saved_at = (Get-Date).ToUniversalTime().ToString('o'); computer = $Machine; local_stamp = $stamp;
        db_bytes = (Get-Item $Local.db).Length }
    Write-Json (Join-Path $cloud 'save-info.json') $info
    Write-Json $StateFile ([ordered]@{ synced_saved_at = $info.saved_at; local_stamp = $stamp; computer = $Machine })
    Log ("Saved to the cloud ({0:N0} MB) from {1}." -f ($info.db_bytes / 1MB), $Machine)
}

function Do-PullFiles([string]$cloud, $info) {
    $cur = Join-Path $cloud 'current'
    if (-not (Test-Path (Join-Path $cur $DbName))) { throw "The cloud save is incomplete (no database in $cur)." }
    Backup-Local 'before-pull'
    foreach ($s in @('-wal', '-shm')) { $f = "$($Local.db)$s"; if (Test-Path $f) { Remove-Item $f -Force } }
    New-Item -ItemType Directory -Force $DbDir | Out-Null
    foreach ($n in @($DbName, "$DbName-wal", "$DbName-shm")) {
        $p = Join-Path $cur $n
        if (Test-Path $p) { Copy-Item $p (Join-Path $DbDir $n) -Force }
    }
    $ev = Join-Path $cur 'realm-event-records.sqlite3'
    if (Test-Path $ev) { Copy-Item $ev $Local.events -Force }
    $cc = Join-Path $cur 'client'
    if (Test-Path $cc) {
        New-Item -ItemType Directory -Force $ClientSave | Out-Null
        foreach ($f in $ClientFiles) {
            $p = Join-Path $cc $f
            if (-not (Test-Path $p)) { continue }
            if ($f -eq 'settings.cfg') { Merge-Settings $p (Join-Path $ClientSave $f) } else { Copy-Item $p $ClientSave -Force }
        }
        foreach ($d in $ClientDirs) {
            $p = Join-Path $cc $d
            if (-not (Test-Path $p)) { continue }
            $dst = Join-Path $ClientSave $d
            if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
            Copy-Item $p $dst -Recurse
        }
    }
    Write-Json $StateFile ([ordered]@{ synced_saved_at = $info.saved_at; local_stamp = (Local-Stamp); computer = $Machine })
    Log ("Loaded the cloud save from {0} ({1})." -f $info.computer, ([datetime]$info.saved_at).ToLocalTime())
}

# Pull when the cloud has a save this PC hasn't taken yet. Returns $false when the person chose not to play.
function Sync-In([string]$cloud) {
    $info = Read-Json (Join-Path $cloud 'save-info.json')
    $state = Read-Json $StateFile
    if ($null -eq $info) { Log "The cloud folder has no save yet - this PC's save goes up when you finish."; return $true }
    $cloudNew = ($null -eq $state) -or ($state.synced_saved_at -ne $info.saved_at)
    $localNew = ($null -ne $state) -and ((Local-Stamp) -gt $state.local_stamp)
    if (-not $cloudNew) {
        if ($localNew) { Log "This PC has progress newer than the cloud - it goes up when you finish." } else { Log "Up to date with the cloud." }
        return $true
    }
    $when = ([datetime]$info.saved_at).ToLocalTime()
    if ($null -eq $state -and (Test-Path $Local.db)) {
        Write-Host ""
        Write-Host "First sync on this computer. The cloud save is from $($info.computer) ($when)."
        Write-Host "This computer has its own game database too."
        $a = Ask "Use the CLOUD save here (C) or keep THIS computer's and send it up when you finish (K)? [C/k]" 'c'
        if ($a -eq 'k') { Log "Kept this PC's save (first sync)."; Write-Json $StateFile ([ordered]@{ synced_saved_at = $info.saved_at; local_stamp = '0'; computer = $Machine }); return $true }
        Do-PullFiles $cloud $info
        return $true
    }
    if ($localNew) {
        Write-Host ""
        Write-Host "Both have new progress: the cloud save from $($info.computer) ($when), and unsynced play on this computer."
        Write-Host "(Whichever you don't pick is kept in runtime\save-sync\backups or the cloud's 'previous' folder.)"
        $a = Ask "Use the CLOUD save (C) or THIS computer's (K)? [c/k, Enter = cancel]" 'x'
        if ($a -eq 'c') { Do-PullFiles $cloud $info; return $true }
        if ($a -eq 'k') { Log "Kept this PC's save over the cloud's (it goes up when you finish)."; return $true }
        return $false
    }
    Do-PullFiles $cloud $info
    return $true
}

function Set-Lock([string]$cloud) {
    Write-Json (Join-Path $cloud 'in-use.json') ([ordered]@{ computer = $Machine; since = (Get-Date).ToUniversalTime().ToString('o') })
}

function Clear-Lock([string]$cloud) {
    $lock = Read-Json (Join-Path $cloud 'in-use.json')
    if ($lock -and $lock.computer -eq $Machine) { Remove-Item (Join-Path $cloud 'in-use.json') -Force }
}

# ---------------------------------------------------------------- the modes

$cloud = Find-Cloud

if ($Status) {
    Write-Host "This computer: $Machine   game folder: $Root"
    if (-not $cloud -or -not (Test-Path $cloud)) { Write-Host "Cloud folder: NOT FOUND (is Google Drive for desktop running and signed in?)"; exit 1 }
    Write-Host "Cloud folder: $cloud"
    $info = Read-Json (Join-Path $cloud 'save-info.json'); $lock = Read-Json (Join-Path $cloud 'in-use.json'); $state = Read-Json $StateFile
    if ($info) { Write-Host ("Cloud save: from {0}, {1}" -f $info.computer, ([datetime]$info.saved_at).ToLocalTime()) } else { Write-Host "Cloud save: none yet" }
    if ($lock) { Write-Host ("In use on: {0} since {1}" -f $lock.computer, ([datetime]$lock.since).ToLocalTime()) }
    if ($state) { Write-Host ("This PC last synced the save of {0}; unsynced progress here: {1}" -f ([datetime]$state.synced_saved_at).ToLocalTime(), ((Local-Stamp) -gt $state.local_stamp)) }
    exit 0
}

if ($Push) {
    if (-not $cloud -or -not (Test-Path $cloud)) { Write-Host "Can't reach the cloud folder - is Google Drive for desktop running and signed in?"; exit 1 }
    Do-Push $cloud
    exit 0
}

if ($Pull) {
    if (-not $cloud -or -not (Test-Path $cloud)) { Write-Host "Can't reach the cloud folder - is Google Drive for desktop running and signed in?"; exit 1 }
    if (Game-Running) { Write-Host "Close the game (launcher and server) first."; exit 1 }
    if (-not (Sync-In $cloud)) { exit 1 }
    exit 0
}

if ($Watch) {
    # hidden, while you play: push each time the server stops, and once more when the launcher closes
    try {
        $wasRunning = $false
        $dirty = $false
        while ($true) {
            $up = Server-Running
            if ($up) { $wasRunning = $true; $dirty = $true }
            if ($wasRunning -and -not $up -and $dirty) {
                Start-Sleep 3
                try { Do-Push $cloud; $dirty = $false } catch { Log "Save to cloud failed: $_" }
                $wasRunning = $false
            }
            $launcher = if ($LauncherPid) { Get-Process -Id $LauncherPid -ErrorAction SilentlyContinue } else { $null }
            if (-not $launcher -and -not $up) { break }
            Start-Sleep 5
        }
        $st = Read-Json $StateFile
        if ($dirty -or $null -eq $st -or ((Local-Stamp) -gt $st.local_stamp)) { Do-Push $cloud }
        Clear-Lock $cloud
        Log "Session over - save in the cloud, in-use mark cleared."
    } catch {
        Log "SAVE SYNC PROBLEM: $_"
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show("Offline DAoC could not save your progress to Google Drive:`n`n$_`n`nYour progress is safe on this computer. Run 'SAVE NOW (SYNC).cmd' once Google Drive is working.", "Offline DAoC save sync") | Out-Null
    }
    exit 0
}

if ($Play) {
    if ((Server-Running) -and -not (Launcher-Running)) {
        if (-not (Stop-LeftoverServer)) { Start-Sleep 3; exit 1 }
    }
    if (Game-Running) { Write-Host "The game is already running on this computer."; Start-Sleep 3; exit 1 }
    $synced = $false
    if (-not $cloud -or -not (Test-Path $cloud)) {
        Write-Host "Can't reach the save folder in Google Drive (is Google Drive for desktop running and signed in?)."
        $a = Ask "Play anyway, without syncing? Your progress stays on this computer. [y/N]" 'n'
        if ($a -ne 'y') { exit 1 }
    } else {
        $lock = Read-Json (Join-Path $cloud 'in-use.json')
        if ($lock -and $lock.computer -ne $Machine) {
            $since = ([datetime]$lock.since).ToLocalTime()
            Write-Host ""
            Write-Host "The save is marked as in use on $($lock.computer) since $since."
            Write-Host "If you're still playing there, quit there first (its progress hasn't been saved to the cloud yet)."
            $a = Ask "Play here anyway (that computer's unsaved progress would be left behind)? [y/N]" 'n'
            if ($a -ne 'y') { exit 1 }
        }
        if (-not (Sync-In $cloud)) { exit 1 }
        Set-Lock $cloud
        $synced = $true
    }
    $env:DOTNET_ROOT = Join-Path $Root 'tools\dotnet'
    $env:DOTNET_ROOT_X64 = $env:DOTNET_ROOT
    $env:DOTNET_MULTILEVEL_LOOKUP = '0'
    $launcher = Start-Process -FilePath (Join-Path $Root 'new-client\runtime\OfflineDAoC.exe') -WorkingDirectory (Join-Path $Root 'new-client\runtime') -PassThru
    if ($synced) {
        Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            "`"$PSCommandPath`"", '-Watch', '-LauncherPid', $launcher.Id, '-Root', "`"$Root`"", '-Cloud', "`"$cloud`"")
        Log "Playing - your progress is saved to the cloud when you stop the server or close the launcher."
    }
    exit 0
}

Write-Host "Use -Play, -Push, -Pull or -Status."
