# Offline DAoC update (owner 2026-10-28): brings this computer's game up to date with the GitHub repository -
# the same changes on every computer you play on.
#   1. pulls the latest changes (git pull - only fast-forward; nothing of yours is overwritten)
#   2. the server: rebuilt and installed when its source changed since it was last built here
#   3. the new client: every changed script / shader / C# file copied into new-client\godot\game, and the C# part
#      rebuilt when a .cs file changed
# Close the game (launcher, server and client) first. -DryRun only says what it would do.
param([switch]$DryRun, [string]$Root = "")
$ErrorActionPreference = 'Continue'      # (git and dotnet write progress to stderr: judged by their exit codes)
if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
Set-Location $Root
$StateDir = Join-Path $Root 'runtime\save-sync'
New-Item -ItemType Directory -Force $StateDir | Out-Null

function Say([string]$m, [string]$color = 'Gray') { Write-Host $m -ForegroundColor $color }

function Find-Dotnet {
    # an SDK, not just the runtime (the game folder's tools\dotnet is a runtime only)
    foreach ($d in @("$env:ProgramFiles\dotnet\dotnet.exe", 'dotnet')) {
        try {
            $sdks = & $d --list-sdks 2>$null
            if ($LASTEXITCODE -eq 0 -and ($sdks | Where-Object { $_ -match '^10\.' })) { return $d }
        } catch { }
    }
    return $null
}

# ---------------------------------------------------------------- 0. nothing running

$running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith($Root, [StringComparison]::OrdinalIgnoreCase) -and
    $_.Name -match '^(CoreServer|OfflineDAoC|Godot.*)\.exe$' }
if ($running -and -not $DryRun) {
    Say "Close the game first (launcher, server and client): $(($running | Select-Object -ExpandProperty Name -Unique) -join ', ')" Yellow
    exit 1
}

# ---------------------------------------------------------------- 1. pull

try { git --version | Out-Null } catch { Say "Git isn't installed on this computer: https://git-scm.com/download/win" Yellow; exit 1 }
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Say "Checking GitHub for changes ($branch)..."
git fetch origin 2>&1 | ForEach-Object { Say "  $_" DarkGray }
if ($LASTEXITCODE -ne 0) { Say "Couldn't reach GitHub - check the internet connection and that this computer is signed in to GitHub (git asks the first time)." Yellow; exit 1 }
$behind = [int](git rev-list --count "HEAD..origin/$branch")
$old = (git rev-parse HEAD).Trim()
if ($behind -eq 0) {
    Say "The code is up to date." Green
} elseif ($DryRun) {
    Say "Would pull $behind new change(s):" Cyan
    git log --oneline "HEAD..origin/$branch" | ForEach-Object { Say "  $_" }
} else {
    Say "Pulling $behind new change(s)..." Cyan
    git pull --ff-only origin $branch 2>&1 | ForEach-Object { Say "  $_" DarkGray }
    if ($LASTEXITCODE -ne 0) {
        Say "The pull stopped - files in this folder were changed here too:" Yellow
        git status --short | ForEach-Object { Say "  $_" }
        Say "Nothing was changed. Ask Claude to sort these out, then run the update again." Yellow
        exit 1
    }
    git log --oneline "$old..HEAD" | ForEach-Object { Say "  $_" }
}
$target = if ($DryRun) { "origin/$branch" } else { 'HEAD' }

# ---------------------------------------------------------------- 2. the server

$serverCommit = (git log -1 --format=%H $target -- source/server).Trim()
$builtFile = Join-Path $StateDir 'server-built-from.txt'
$built = if (Test-Path $builtFile) { (Get-Content $builtFile -TotalCount 1).Trim() } else { '' }
if ($serverCommit -and $serverCommit -ne $built) {
    if ($DryRun) {
        Say "Would rebuild and install the server (its source changed since the last build here)." Cyan
    } else {
        $dotnet = Find-Dotnet
        if (-not $dotnet) {
            Say "The server changed, but the .NET 10 SDK isn't installed here: https://dotnet.microsoft.com/download/dotnet/10.0" Yellow
            Say "Install it, then run the update again (the rest is done)." Yellow
        } else {
            Say "Building the server (a minute or two)..." Cyan
            & $dotnet build (Join-Path $Root 'source\server\GameServer\GameServer.csproj') -c Release -v q --nologo 2>&1 |
                Select-String -Pattern ' error |Build succeeded|Warn' | ForEach-Object { Say "  $($_.Line)" DarkGray }
            if ($LASTEXITCODE -ne 0) { Say "The server build failed - the old server stays installed. Tell Claude." Red; exit 1 }
            & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\king\deploy_server.ps1')
            if ($LASTEXITCODE -ne 0) { Say "Installing the server build failed - tell Claude." Red; exit 1 }
            Set-Content -Path $builtFile -Value $serverCommit
            Say "Server updated." Green
        }
    }
} else {
    Say "The server is up to date." Green
}

# ---------------------------------------------------------------- 3. the new client

$src = Join-Path $Root 'source\new-client\godot\game'
$dst = Join-Path $Root 'new-client\godot\game'
$copied = 0
$csChanged = $false
if (-not (Test-Path $dst)) {
    Say "No new client in this folder (new-client\godot) - copy the whole game folder from your main computer first." Yellow
} elseif ($DryRun -and $behind -gt 0) {
    $files = git diff --name-only "HEAD..origin/$branch" -- source/new-client/godot/game
    if ($files) { Say "Would update $(@($files).Count) client file(s)." Cyan }
} else {
    Get-ChildItem $src -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($src.Length + 1)
        $to = Join-Path $dst $rel
        if (-not (Test-Path $to) -or (Get-FileHash $_.FullName).Hash -ne (Get-FileHash $to).Hash) {
            if ($DryRun) { Say "  would copy $rel" } else {
                New-Item -ItemType Directory -Force (Split-Path $to) | Out-Null
                Copy-Item $_.FullName $to -Force
            }
            $script:copied++
            if ($_.Extension -eq '.cs') { $script:csChanged = $true }
        }
    }
    if ($copied -gt 0) { Say "$(if ($DryRun) { 'Would update' } else { 'Updated' }) $copied client file(s)." Green } else { Say "The client is up to date." Green }
    if ($csChanged -and -not $DryRun) {
        $dotnet = Find-Dotnet
        if (-not $dotnet) {
            Say "The client's C# part changed, but the .NET 10 SDK isn't installed here: https://dotnet.microsoft.com/download/dotnet/10.0" Yellow
        } else {
            Say "Building the client's C# part..." Cyan
            & $dotnet build (Join-Path $Root 'new-client\godot\MMOEngine.csproj') -c Debug -v q --nologo 2>&1 |
                Select-String -Pattern ' error |Build succeeded' | ForEach-Object { Say "  $($_.Line)" DarkGray }
            if ($LASTEXITCODE -ne 0) { Say "The client's C# build failed - tell Claude." Red; exit 1 }
        }
    } elseif ($csChanged) { Say "Would rebuild the client's C# part." Cyan }
}

# ---------------------------------------------------------------- anything that needs a hand

if ($behind -gt 0) {
    $range = "$old..$target"
    if (git diff --name-only $range -- source/tools/OfflineDaoc.Launcher) {
        Say "Note: the launcher's source changed - ask Claude to rebuild it on this computer." Yellow
    }
}
# ---------------------------------------------------------------- 4. the zones' caches (models, compressed textures)

if (-not $DryRun -and (Test-Path $dst)) {
    Say "Building any missing zone caches (quick when they're all there)..." Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\sync\prebuild_caches.ps1') -Root $Root
}

Say ""
Say "Done$(if ($DryRun) { ' (dry run - nothing was changed)' })." Green
