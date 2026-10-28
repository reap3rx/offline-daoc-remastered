@echo off
rem Brings this computer's Offline DAoC up to date with the latest changes on GitHub (server and new client).
rem Close the game first. See "SYNC AND UPDATE - READ ME.txt".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\sync\update.ps1" %*
pause
