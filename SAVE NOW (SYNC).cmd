@echo off
rem Save your progress to Google Drive right now (the server must be stopped). Normally this happens by itself.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\sync\savesync.ps1" -Push
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\sync\savesync.ps1" -Status
pause
