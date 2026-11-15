# Offline DAoC Remastered — instructions for AI assistants and developers

Read this first, then [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). This file is also loaded by
Claude Code as `CLAUDE.md`.

## What this is

Offline DAoC Remastered is a single-player Dark Age of Camelot (Classic + Shrouded Isles, 1.65): an
OpenDAoC-based server (.NET 10, SQLite) with living player bots and companions, played through a new
client written in Godot 4.7 (.NET), started by a Windows launcher. It grew out of the original
OfflineDAoC v0.36c and has its own version line (0.1, 0.2, 0.2a ... 0.2j at the time of writing). The
goal is a remaster: keep the spirit of DAoC, make it feel like a modern game.

The guides of the old OfflineDAoC release line (0.37, its three editions, the patcher) are in
`docs/history/` for reference only. Nothing in them describes how Remastered is built or released.

## Layout

| Path | What it is |
|---|---|
| `source/server` | Game server, all bot AI, tests (`Tests/`). The solution is `Dawn of Light.sln`. |
| `source/server/GameServer/bots` | Companion bots (`PersonalCompanions*.cs`), class AI, bot brains |
| `source/server/GameServer/bots/autonomous` | Autonomous gamebots: goals, camps, groups, travel, watchdog |
| `source/server/GameServer/scripts` | Story quests, dynamic events, named monsters, custom NPCs and commands |
| `source/new-client/godot/game` | The client's code (GDScript, plus the network client in C#: `net/DaocClient.cs`) |
| `source/new-client/godot/tests` | Probes and checks run inside the game (`--live-probe=<name>`) |
| `source/new-client/pipeline` | Python content pipeline: converts the original client's files into `godot/content` |
| `source/tools/OfflineDaoc.Launcher` | The launcher (server control, updates, cloud saves), tests in `OfflineDaoc.Launcher.Tests` |
| `source/tools/release` | `make_release.ps1`, `publish_release.ps1`, `build_release.py`, `make_world_db.py`, the installer script |
| `db-changes/` | SQL changes to the world database, applied with `apply.py` |
| `tools/claude-version` | Database helpers and generators. Many are one-off changes already applied; read a script's header before running it. |
| `tools/pet-art`, `tools/asset-tool` | Art pipeline for the original client's models, skins and effects |
| `docs/` | Player and developer guides; `docs/history/` holds the old release line's notes |

In the playable folder (not in Git):
- `new-client/godot`: the client as it runs (a copy of `source/new-client/godot` plus `content/`, about 44 GB of converted game content)
- `new-client/runtime`: the launcher players start (`OfflineDAoC.exe`); `new-client/save`: settings, keybinds and logs
- `runtime/server`: the server binaries and navigation meshes
- `runtime/data/opendaoc.sqlite3.db`: world data plus the player's saves
- `runtime/client-opendaoc/app`: the original game client, kept as the content pipeline's source

## Rules

- **Protect player data.**
  - Never commit or publish a played database, `account.txt`, logs, bot rosters, backups or
    credentials.
  - Public releases are built only by `source/tools/release/make_release.ps1`. Its world database comes
    from `make_world_db.py`, which takes every trace of the owner out and checks the result. No account ships.
  - Never ship DXVK (`d3d9.dll`, `dxvk.conf`), diagnostics switches or the new client's
    `dev_mode.txt`.
- **Keep the owner's gameplay rules.** Preserve these unless the owner asks otherwise:
  - real loot, inventories, coins and equipment upgrades
  - the Realm Exchange
  - stablemaster routes
  - selling only at natural task breaks
  - gamebots start without armor and earn it
  - Darkness Falls is open to solo bots
- **Tell bot types apart.** Real players, companion bots and autonomous gamebots are different.
  Check which one a change affects.
- **Don't start or deploy without permission.**
  - Never start a server or copy builds over a running install without asking.
  - Only one server can use port 10300 at a time.
- **Build and test separately.** Deploy only tested outputs, with a backup of what you replace:
  `GameServer.dll` goes to `runtime/server`, `runtime/server/lib` and `runtime/server/win-x64`.
- **Client files:**
  - Keep hash guards on any binary patch; never patch an unverified `game.dll`.
  - Private art is added under new IDs; stock models, skins and effects are never edited in place.
  - `tools/pet-art` shows the pattern: byte copies of NIFs with same-length texture renames, and
    new catalog rows.
- **Navigation:** don't rebuild or replace navmeshes globally to fix one route without evidence.
- **Be honest in reports.** Report automated tests separately from real in-game checks. Don't
  describe Darkness Falls raid AI, Legion or the hardest level 70+ encounters as implemented.
- **Keep the old releases.** Published releases and their tags are not rewritten.
- **Commit and publish only when the owner asks.** A release reaches players' launchers the moment it is published.

## Useful facts

- **One way to play.** The launcher always starts the client against the local server
  (`--server=127.0.0.1`). The client also contains an older standalone game (its own combat, quests,
  bots and companions, everything behind `not Server.active`). It never runs and is being removed;
  do not extend it, and check which side a system lives on before changing it (the server owns
  companions, quests, loot and combat).
- **Two copies of the client code.** Edit `source/new-client/godot/game`, then copy the changed files to
  `new-client/godot/game` to run them. Only the source copy is in Git.
- **Custom classes.** The Sluaghbinder (Hibernia; `ServerProperties.Properties.ENABLE_SLUAGHBINDER`,
  on) stays until the owner designs its replacement. The King / Queen (Albion, player-only,
  `playerclasses/albion/ClassKing.cs`, database steps in `db-changes/`) is part of Remastered and not
  finished: its epic quest and a play-through to 50 are open.
- **Performance.** The client's `Perf` autoload (`game/perf_governor.gd`) writes `perf_live.log` in the
  save folder every two seconds, and a `[hitch]` line naming what ran in any frame of 60 ms or more.
  Start there before guessing at a performance problem.
- **Item model chain:** `objects.csv` model ID → `items.csv` row → `items/<nif>`.
  - Shields that carry an emblem take their base texture from a `pskins.csv` override.
  - `tools/pet-art/nif4_geom.py` reads the old 4.x item NIFs that pyffi can't.
- **Original client art, spells and sounds:** read [docs/CLIENT-MODDING-GUIDE.txt](docs/CLIENT-MODDING-GUIDE.txt)
  before changing models, meshes, skins, spell effects, icons or NPC sounds.
- **Server settings:** Offline-specific settings are in the database tables
  `offline_population_settings` and `offline_local_options`, and in `runtime/server/bot-goals.json`.
- **Known test state:** 2,851 server tests, 26 failing (6 distinct tests, all bot behaviour) as of 0.2j.

The owner may customize their fork's rules. These are safety defaults, not a ban on changes the
owner asks for.
