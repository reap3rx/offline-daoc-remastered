# Playing Offline DAoC Remastered

Dark Age of Camelot (Classic + Shrouded Isles, 1.65 rules) on your own PC: your own server, a world of
player bots, and a new game client. This guide covers installing, the launcher, and where things are.
How the game itself plays is in [GAMEPLAY.md](GAMEPLAY.md).

## What you need

- Windows 10 or 11 (64-bit).
- A graphics card that supports Vulkan or DirectX 12, with current drivers. A card with 8 GB of video
  memory or more is recommended at high settings.
- About 50 GB of free disk space; an SSD is best.
- 16 GB of memory or more is recommended: the server, its bots and the game all run on your PC. More
  memory lets you run a bigger bot population.

## Install

1. Download **Offline-DAoC-Remastered-Setup.exe** from the
   [latest release](https://github.com/reap3rx/offline-daoc-remastered/releases/latest).
2. Run it and pick a folder. No administrator rights are needed.
3. The launcher opens and downloads the game (about 45 GB). Leave it running; it resumes if interrupted.

## The launcher

The launcher is the one program you start. It does three jobs:

- **Runs your server.** Click **START SERVER** and wait until it shows as running. The server is the
  game world: monsters, bots, quests, items and your characters. It runs only on your PC.
- **Starts the game.** Click **ENTER REALM**. The game opens and logs in with your local account,
  which the launcher makes for you the first time.
- **Keeps the game up to date.** Each time it starts it checks for a new release and downloads only
  what changed. An update never touches your characters, world or settings.

When you finish, quit the game, then stop the server from the launcher before closing it.

**More than one computer:** install Google Drive for desktop, then choose *Connect Google Drive* in
the launcher's Options. Your save then follows you between computers. One computer needs nothing.

## The game client

The game is a new client built in the Godot engine. It shows the original game's zones, characters,
monsters, spells, sounds and music, converted from the original client's files and redrawn by a modern
renderer. Everything that happens in the world is decided by the server; the client draws it and sends
what you do.

Settings are under **Options** in game: graphics presets, the interface style (classic or modern),
movement style, keybinds and controller setup.

## Where things are

Inside the install folder:

| What | Where |
|---|---|
| Your characters, bots and world (your save) | `world\data\opendaoc.sqlite3.db` |
| Game settings, keybinds, quickbars and the game's logs | `client\save` |
| Server logs | `world\logs` |
| The launcher | `client\launcher` |
| The game and its content | `client\godot` |
| The server | `world\server` |

Back up `world\data\opendaoc.sqlite3.db` (with the server stopped) to keep a copy of your progress.

## Problems

Report problems on the [issues page](https://github.com/reap3rx/offline-daoc-remastered/issues). It
helps to say what you were doing and to attach a screenshot. For a performance problem, attach
`perf_live.log` from the game's settings folder.

Offline DAoC Remastered is a free fan project, not affiliated with Electronic Arts, Broadsword or
Mythic Entertainment.
