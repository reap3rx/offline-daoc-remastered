# Offline DAoC (owner 2026-10-28): builds every zone's model and texture caches now, so no zone is slow on its first
# visit. Runs a few headless copies of the game at low priority; safe to run while playing, but faster when not.
# Each computer builds its own (the caches live in new-client\godot\content, which isn't in git).
param([int]$Jobs = 3, [string]$Root = "")
if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
$godot = Join-Path $Root 'new-client\tools\godot_net\Godot_v4.7.2-stable_mono_win64_console.exe'
$proj = Join-Path $Root 'new-client\godot'
$zones = Get-ChildItem (Join-Path $proj 'content\zones') -Directory -Filter 'zone*' |
    Where-Object { Test-Path (Join-Path $_.FullName 'zone.json') } | ForEach-Object { [int]$_.Name.Substring(4) }
$logDir = Join-Path $Root 'runtime\save-sync'
New-Item -ItemType Directory -Force $logDir | Out-Null
Write-Host "Building caches for $($zones.Count) zones with $Jobs jobs (a few minutes; the first time can take 10-20)..."
$procs = @()
for ($j = 0; $j -lt $Jobs; $j++) {
    $mine = @($zones | Where-Object { ($zones.IndexOf($_) % $Jobs) -eq $j }) -join ','
    $log = Join-Path $logDir "prebuild_$j.log"
    $p = Start-Process -FilePath $godot -ArgumentList @('--headless', '--path', "`"$proj`"", '-s', 'res://game/tools/prebuild_caches.gd', '--', "--zones=$mine") `
        -PassThru -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError "$log.err"
    try { $p.PriorityClass = 'BelowNormal' } catch { }
    $procs += $p
}
$procs | ForEach-Object { $_.WaitForExit() }
$built = (Get-ChildItem $logDir -Filter 'prebuild_*.log' | Select-String -Pattern 'built in').Count
Write-Host "Done: $built zones read and cached."
