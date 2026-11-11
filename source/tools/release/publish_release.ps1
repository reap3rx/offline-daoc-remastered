# Offline DAoC Remastered: publish a built release to GitHub (owner 2026-11-11). After make_release.ps1:
#
#   .\publish_release.ps1 -Version 0.1.0 [-Repo reap3rx/offline-daoc-remastered] [-Notes notes.md] [-Out "...\Offline DAOC Release"]
#
# The release is made as a draft, every new pack is uploaded (each retried until it lands - a pack is up to 1.7 GB),
# then the installer and manifest.json, and only then is the draft published. Until that moment players' launchers
# don't see it: "latest" still points at the previous release, so nobody downloads half a release. Safe to run again
# after a dropped connection: files already on the release are skipped. Needs the GitHub CLI (gh), signed in.
param(
    [Parameter(Mandatory)][string]$Version,
    [string]$Repo = "reap3rx/offline-daoc-remastered",
    [string]$Notes = "",
    [string]$Out = ""
)
$ErrorActionPreference = 'Stop'
$Game = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
if (-not $Out) { $Out = Join-Path (Split-Path $Game -Parent) 'Offline DAOC Release' }
$tag = "v$Version"
$files = @(Get-Content (Join-Path $Out "$tag\upload.txt") | Where-Object { $_ -and -not $_.EndsWith('manifest.json') })
$setup = Join-Path $Out "Offline-DAoC-Remastered-Setup-$Version.exe"
if (Test-Path $setup) { $files += $setup }
$files += (Join-Path $Out "$tag\manifest.json")                    # last: the release is whole when it is there

$exists = $true
try { gh release view $tag --repo $Repo --json tagName 2>$null | Out-Null; if ($LASTEXITCODE) { $exists = $false } } catch { $exists = $false }
if (-not $exists) {
    $a = @('release', 'create', $tag, '--repo', $Repo, '--draft', '--title', "Offline DAoC Remastered $Version")
    if ($Notes) { $a += @('--notes-file', $Notes) } else { $a += @('--notes', "Offline DAoC Remastered $Version") }
    gh @a
    if ($LASTEXITCODE) { throw "Couldn't create the release." }
}
$have = @(gh release view $tag --repo $Repo --json assets --jq '.assets[] | select(.state == \"uploaded\") | .name')
$n = 0
foreach ($f in $files) {
    $n++
    $name = Split-Path $f -Leaf
    if ($have -contains $name -and $name -ne 'manifest.json') { Write-Host "[$n/$($files.Count)] $name - already up"; continue }
    for ($try = 1; ; $try++) {
        Write-Host ("[{0}/{1}] {2} ({3:N0} MB) {4:HH:mm:ss}" -f $n, $files.Count, $name, ((Get-Item $f).Length / 1MB), (Get-Date))
        gh release upload $tag $f --repo $Repo --clobber
        if (-not $LASTEXITCODE) { break }
        if ($try -ge 6) { throw "$name didn't upload after $try tries - run this again later to carry on." }
        Start-Sleep (20 * $try)
    }
}
gh release edit $tag --repo $Repo --draft=false --latest
if ($LASTEXITCODE) { throw "Couldn't publish the release." }
Write-Host "Published: https://github.com/$Repo/releases/tag/$tag"
