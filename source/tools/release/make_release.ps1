# Offline DAoC Remastered: build a release (owner 2026-11-11). Run from the game folder's source\tools\release:
#
#   .\make_release.ps1 -Version 0.1.0 -Repo OWNER/offline-daoc-remastered [-Notes notes.txt] [-Out "E:\Offline DAOC Release"]
#                      [-StageOnly]  (a plain install folder under -Out\stage to try, nothing packed)
#
# 1. publishes the launcher as one self-contained program (no .NET needed to start it)
# 2. makes the new world's database from yours with every trace of you taken out (make_world_db.py)
# 3. gathers the install and packs it, writes manifest.json (build_release.py) - unchanged packs are reused
# 4. builds the installer, when Inno Setup 6 is installed
# 5. says what to upload. Publishing is yours: gh release create (below), or the GitHub page.
# Stop the server first: step 2 copies the database (safe while it runs, but a stopped server's copy is the newest).
param(
    [Parameter(Mandatory)][string]$Version,
    [string]$Repo = "OWNER/offline-daoc-remastered",
    [string]$Notes = "",
    [string]$Out = "",
    [switch]$StageOnly
)
$ErrorActionPreference = 'Stop'
$Here = $PSScriptRoot
$Game = (Resolve-Path (Join-Path $Here '..\..\..')).Path               # playable-v0.36c
if (-not $Out) { $Out = Join-Path (Split-Path $Game -Parent) 'Offline DAOC Release' }
New-Item -ItemType Directory -Force $Out | Out-Null
$Dotnet = 'C:\Program Files\dotnet\dotnet.exe'
$Python = Join-Path (Split-Path $Game -Parent) 'claude-work\pyenv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = 'python' }

# a version with a letter (owner 2026-11-12: "0.1a") is the program's file version with the letter as a number (0.1.1)
$FileVersion = [regex]::Replace($Version, '([0-9])([a-z])$', { param($m) $m.Groups[1].Value + '.' + ([int][char]$m.Groups[2].Value - 96) })
Write-Host "== 1. the launcher"
$Launcher = Join-Path $Out 'launcher'
if (Test-Path $Launcher) { Remove-Item $Launcher -Recurse -Force }
& $Dotnet publish (Join-Path $Game 'source\tools\OfflineDaoc.Launcher\OfflineDaoc.Launcher.csproj') -c Release -r win-x64 `
    --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true `
    -p:EnableCompressionInSingleFile=true -p:DebugType=none -p:Version=$FileVersion -p:InformationalVersion=$Version -o $Launcher -nologo -v q
if ($LASTEXITCODE) { throw "The launcher didn't build." }

Write-Host "== 2. the new world"
$World = Join-Path $Out "world-$Version.db"
& $Python (Join-Path $Here 'make_world_db.py') (Join-Path $Game 'runtime\data\opendaoc.sqlite3.db') $World
if ($LASTEXITCODE) { throw "The world database failed its check." }

Write-Host "== 3. the packs and the manifest"
$args3 = @((Join-Path $Here 'build_release.py'), '--game', $Game, '--version', $Version, '--world', $World,
           '--launcher', $Launcher, '--out', $Out, '--repo', $Repo)
if ($Notes) { $args3 += @('--notes', $Notes) }
if ($StageOnly) { $args3 += '--stage-only' }
& $Python @args3
if ($LASTEXITCODE) { throw "Packing failed." }
if ($StageOnly) { Write-Host "Staged: $Out\stage - run client\launcher\OfflineDAoC.exe there to try it."; return }

Write-Host "== 4. the installer"
$Iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe", "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if ($Iscc) {
    & $Iscc /Q "/DVersion=$Version" "/DSource=$Out" (Join-Path $Here 'installer\OfflineDaocRemastered.iss')
    if ($LASTEXITCODE) { throw "The installer didn't build." }
} else {
    Write-Host "Inno Setup 6 isn't installed (https://jrsoftware.org/isdl.php) - no installer this time."
}

$tag = "v$Version"
$files = @(Get-Content (Join-Path $Out "$tag\upload.txt"))
$setup = Join-Path $Out "Offline-DAoC-Remastered-Setup-$Version.exe"
if (Test-Path $setup) { $files += $setup }
Write-Host ""
Write-Host "== 5. publish: $($files.Count) files for release $tag"
Write-Host "   gh release create $tag --repo $Repo --title `"Offline DAoC Remastered $Version`" --notes-file <notes> `"$($files -join '" "')`""
Write-Host "   (packs already published in an earlier release are not uploaded again - the manifest points at them)"
