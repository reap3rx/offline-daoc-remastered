# Offline DAoC Remastered: switch the game between its saved worlds (claude 2026-11-03, owner: ship the fresh Beta
# world with the old world included to switch to). The world you leave is set aside first (one copy kept), so you can
# always switch back to it.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$data = Join-Path $root 'runtime\data'
$worlds = Join-Path $data 'worlds'
$db = Join-Path $data 'opendaoc.sqlite3.db'
$events = Join-Path $root 'runtime\server\dynamic-events-state.json'
if (Get-Process CoreServer -ErrorAction SilentlyContinue) {
    Write-Host 'The game server is running. Stop it in the launcher (or close the launcher), then try again.' -ForegroundColor Yellow
    exit 1
}
New-Item -ItemType Directory -Force $worlds | Out-Null
$choices = @()
$fresh = Join-Path $worlds 'fresh-beta-world.sqlite3.db'
if (Test-Path $fresh) { $choices += ,@('A fresh Beta world: no characters, no bots, every house lot for sale', $fresh, '') }
Get-ChildItem $worlds -Filter 'my-world-*.sqlite3.db' | Sort-Object Name | ForEach-Object {
    $choices += ,@("Your world from $($_.BaseName -replace '^my-world-','' -replace '\.sqlite3$','') (your characters and bots as they were)", $_.FullName, ($_.FullName -replace '\.sqlite3\.db$', '.dynamic-events-state.json'))
}
$aside = Join-Path $worlds 'set-aside.sqlite3.db'
if (Test-Path $aside) { $choices += ,@("The world you left last time (set aside $((Get-Item $aside).LastWriteTime.ToString('yyyy-MM-dd HH:mm')))", $aside, ($aside -replace '\.sqlite3\.db$', '.dynamic-events-state.json')) }
Write-Host ''
Write-Host 'Which world do you want to play?' -ForegroundColor Cyan
for ($i = 0; $i -lt $choices.Count; $i++) { Write-Host ("  {0}. {1}" -f ($i + 1), $choices[$i][0]) }
$pick = Read-Host 'Number (Enter = cancel)'
if (-not $pick) { exit 0 }
$n = [int]$pick - 1
if ($n -lt 0 -or $n -ge $choices.Count) { Write-Host 'No such world.'; exit 1 }
$from = $choices[$n][1]
# set the current world aside (the set-aside copy itself is moved to a temporary name first if it's the one chosen)
if ($from -eq $aside) { $tmp = Join-Path $worlds 'switching.sqlite3.db'; Move-Item $aside $tmp -Force; $from = $tmp
    if (Test-Path ($aside -replace '\.sqlite3\.db$', '.dynamic-events-state.json')) { Move-Item ($aside -replace '\.sqlite3\.db$', '.dynamic-events-state.json') ($tmp -replace '\.sqlite3\.db$', '.dynamic-events-state.json') -Force }
    $choices[$n][2] = $tmp -replace '\.sqlite3\.db$', '.dynamic-events-state.json' }
if (Test-Path $db) {
    Copy-Item $db $aside -Force
    if (Test-Path $events) { Copy-Item $events ($aside -replace '\.sqlite3\.db$', '.dynamic-events-state.json') -Force }
    else { Remove-Item ($aside -replace '\.sqlite3\.db$', '.dynamic-events-state.json') -ErrorAction SilentlyContinue }
}
Remove-Item "$db-shm", "$db-wal" -ErrorAction SilentlyContinue
Copy-Item $from $db -Force
if ($choices[$n][2] -and (Test-Path $choices[$n][2])) { Copy-Item $choices[$n][2] $events -Force } else { Remove-Item $events -ErrorAction SilentlyContinue }
if ($from -like '*switching.sqlite3.db') { Remove-Item $from, ($from -replace '\.sqlite3\.db$', '.dynamic-events-state.json') -ErrorAction SilentlyContinue }
Write-Host ''
Write-Host "Done: $($choices[$n][0])." -ForegroundColor Green
Write-Host 'The world you were playing is kept as "the world you left last time".'
