# Render every outdoor zone from above (godot/tests/map_render.gd) -> content/maps/render/z<id>.jpg, then run
# python build_map_labels.py for their names. Skips zones already drawn unless -redo. docs/MODERN_UI.md.
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\new-client\godot')).Path    # the playable client
$godot = (Resolve-Path (Join-Path $root '..\tools\godot_net\Godot_v4.7.2-stable_mono_win64_console.exe')).Path
$maps = Get-Content "$root\content\maps\maps.json" -Raw | ConvertFrom-Json
$ids = @()
foreach ($d in Get-ChildItem "$root\content\zones" -Directory) {
  $id = [int]($d.Name -replace 'zone','')
  $zj = Join-Path $d.FullName 'zone.json'
  if (-not (Test-Path $zj)) { continue }
  $head = (Get-Content $zj -Raw)
  if ($head -match '"dungeon": *true' -or $head -match '"city": *true') { continue }
  $z = $maps.zones."$id"
  if ($null -eq $z -or -not $z.map) { continue }
  if ($z.map_rect) { continue }
  if (Test-Path "$root\content\maps\render\z$('{0:D3}' -f $id).jpg") { if ($args -notcontains '-redo') { continue } }
  $ids += $id
}
"zones: $($ids -join ',')"
cd $root
foreach ($id in $ids) {
  if (Get-Process -Name CoreServer -ErrorAction SilentlyContinue) { 'server running: stop'; break }
  $out = (Join-Path $env:TEMP "map_render_$id.txt")
  $p = Start-Process -FilePath $godot -ArgumentList '--path','.','res://game/zone_viewer.tscn','--',"--zone=$id",'--probe=map_render','--time=15.5' -RedirectStandardOutput $out -RedirectStandardError "$out.err" -PassThru
  $ok = $false
  for ($i=0; $i -lt 60; $i++) { Start-Sleep 3; if (Select-String -Path $out -Pattern '\[map\] saved' -Quiet) { $ok = $true; break }; if ($p.HasExited) { break } }
  Start-Sleep 3
  Get-Process Godot* -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep 1
  "$id $(if ($ok) { (Select-String -Path $out -Pattern '\[map\] saved').Line } else { 'FAILED' })"
}
'ALL DONE'
