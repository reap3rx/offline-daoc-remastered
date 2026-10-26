# Capture a frozen new client (Godot) for diagnosis, before it is force-quit.
#   powershell -ExecutionPolicy Bypass -File tools\king\capture_freeze.ps1
# Writes E:\Offline DAOC 036c\claude-work\freeze-<date-time>\ with:
#   stacks.txt   every .NET thread's call stack (dotnet-stack)
#   threads.txt  every thread's state, CPU time and wait reason (Windows)
#   client.dmp   a minidump of the process (dotnet-dump, threads + stacks, no full memory)
#   godot.log / perf_live.log tails
$ErrorActionPreference = 'Continue'
$tools = Join-Path $env:USERPROFILE '.dotnet\tools'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$p = Get-Process | Where-Object { $_.ProcessName -like 'Godot*' } | Select-Object -First 1
if (-not $p) { Write-Host 'No Godot process is running.'; exit 1 }
$out = Join-Path (Split-Path $root -Parent) ("claude-work\freeze-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force $out | Out-Null
Write-Host "Capturing $($p.ProcessName) (pid $($p.Id), responding: $($p.Responding)) into $out"

"pid $($p.Id)  responding=$($p.Responding)  cpu=$($p.TotalProcessorTime)  ws=$([int]($p.WorkingSet64/1MB)) MB  started=$($p.StartTime)" | Set-Content (Join-Path $out 'threads.txt')
$p.Threads | Sort-Object TotalProcessorTime -Descending | ForEach-Object {
    "{0,6}  {1,-12} {2,-18} cpu {3}" -f $_.Id, $_.ThreadState, $(if ($_.ThreadState -eq 'Wait') { $_.WaitReason } else { '' }), $_.TotalProcessorTime
} | Add-Content (Join-Path $out 'threads.txt')

# CPU over 3 seconds: a busy loop climbs, a deadlock stays flat
$c1 = $p.TotalProcessorTime; Start-Sleep 3; $p.Refresh(); $c2 = $p.TotalProcessorTime
"cpu used in 3 s: $([int](($c2 - $c1).TotalMilliseconds)) ms" | Add-Content (Join-Path $out 'threads.txt')

& (Join-Path $tools 'dotnet-stack.exe') report -p $p.Id *> (Join-Path $out 'stacks.txt')
& (Join-Path $tools 'dotnet-dump.exe') collect -p $p.Id --type Mini -o (Join-Path $out 'client.dmp') *> (Join-Path $out 'dump-log.txt')

$save = Join-Path $root 'new-client\save\Godot\app_userdata\MMOEngine'
Get-Content (Join-Path $save 'logs\godot.log') -Tail 400 -ErrorAction SilentlyContinue | Set-Content (Join-Path $out 'godot-tail.log')
Get-Content (Join-Path $save 'perf_live.log') -Tail 60 -ErrorAction SilentlyContinue | Set-Content (Join-Path $out 'perf-tail.log')
Write-Host 'Done. You can close the game now.'
