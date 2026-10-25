# Copy a fresh server build into the playable runtime.
#   powershell -ExecutionPolicy Bypass -File tools\king\deploy_server.ps1            deploy the build
#   powershell -ExecutionPolicy Bypass -File tools\king\deploy_server.ps1 -Restore   put the original v0.36c server files back
# The first deploy keeps the original files in E:\Offline DAOC 036c\claude-work\server-originals (never overwritten).
param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$build = Join-Path $root 'source\server\Release'
$runtime = Join-Path $root 'runtime\server'
$originals = Join-Path (Split-Path $root -Parent) 'claude-work\server-originals'

if (Get-Process CoreServer -ErrorAction SilentlyContinue) { throw 'The server is running. Click STOP SERVER in the launcher first.' }

$dllDirs = @('', 'lib', 'win-x64')
$files = @('GameServer.dll', 'GameServer.pdb')
$langFiles = Get-ChildItem (Join-Path $build 'languages') -Recurse -File | ForEach-Object { $_.FullName.Substring($build.Length + 1) }

if (-not (Test-Path $originals)) {
    foreach ($d in $dllDirs) { foreach ($f in $files) {
        $src = Join-Path (Join-Path $runtime $d) $f
        if (Test-Path $src) { $dst = Join-Path (Join-Path $originals $d) $f; New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null; Copy-Item $src $dst } } }
    Copy-Item (Join-Path $runtime 'languages') (Join-Path $originals 'languages') -Recurse
    Write-Host "Saved the original server files to $originals"
}

if ($Restore) {
    foreach ($d in $dllDirs) { foreach ($f in $files) {
        $src = Join-Path (Join-Path $originals $d) $f
        if (Test-Path $src) { Copy-Item $src (Join-Path (Join-Path $runtime $d) $f) -Force } } }
    Copy-Item (Join-Path $originals 'languages\*') (Join-Path $runtime 'languages') -Recurse -Force
    Write-Host 'Restored the original server files.'
    return
}

foreach ($d in $dllDirs) { foreach ($f in $files) { Copy-Item (Join-Path $build "lib\$f") (Join-Path (Join-Path $runtime $d) $f) -Force } }
foreach ($l in $langFiles) { $dst = Join-Path $runtime $l; New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null; Copy-Item (Join-Path $build $l) $dst -Force }
Write-Host 'Deployed GameServer.dll/.pdb (runtime\server, lib, win-x64) and the language files.'
