@echo off
rem Offline DAoC - the new client, with your progress synced through Google Drive (G:\My Drive\OfflineDAoC Saves).
rem Loads the newest save from the cloud, starts the launcher, and saves back to the cloud when you stop the server
rem or close the launcher. See "SYNC AND UPDATE - READ ME.txt".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\sync\savesync.ps1" -Play
if errorlevel 1 pause
