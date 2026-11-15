# Developing Offline DAoC Remastered

For people (and AI assistants) who change the code. Read [AGENTS.md](../AGENTS.md) first for the layout
and the rules. The old OfflineDAoC release line's version of this guide is in
[history/DEVELOPMENT-0.37.md](history/DEVELOPMENT-0.37.md).

## Build and test the server

You need the **.NET 10 SDK** on Windows.

```bash
dotnet build source/server/GameServer/GameServer.csproj -c Release
dotnet test source/server/Tests/Tests.csproj -c Release
dotnet test source/tools/OfflineDaoc.Launcher.Tests/OfflineDaoc.Launcher.Tests.csproj -c Release
```

- The build writes `source/server/Release/lib/GameServer.dll`.
- As of 0.2j, 2,825 of 2,851 server tests pass. The 26 failures are 6 distinct tests about bot
  behaviour; a change must not add to them.
- Some launcher tests expect that no local server is running.

## Deploy a server build

1. **Stop everything:** the launcher, the game and the server. Ask the owner first.
2. Copy `source/server/Release/lib/GameServer.dll` (and its `.pdb`) to `runtime/server`,
   `runtime/server/lib` and `runtime/server/win-x64`.
3. **Test in game.** Automated tests are not a substitute for an in-game check.

## Work on the client

- The code is `source/new-client/godot/game`; the game runs from `new-client/godot/game`. Copy changed
  files across, then start the game from the launcher.
- GDScript needs no build. After a change to a `.cs` file run `source/new-client/tools/build_csharp.ps1`.
- A probe is a script in `new-client/godot/tests` that runs inside the live game:
  `--auto-play=<realm>:<Character> --live-probe=<name>` after the usual `--server`, `--account` and
  `--password` arguments. Print results with a fixed prefix and read them from the engine's log.
- Developer keys and debug text need `godot/dev_mode.txt` or `--dev`. Releases never include that file.
- See [source/new-client/README.md](../source/new-client/README.md) for the client's layout and the
  content pipeline.

## Change the world database

Put the change in `db-changes/` as a dated SQL file and apply it with `db-changes/apply.py` (see
`db-changes/README.md`). The database itself is never committed.

## Release

Both scripts are in `source/tools/release` and explain themselves at the top.

1. `make_release.ps1 -Version <x> -Repo reap3rx/offline-daoc-remastered -Notes <notes file>` builds the
   launcher, makes a clean world database from the owner's (every trace of the owner removed and
   checked), packs the install into the release folder beside the game folder, and builds the installer.
   Packs that did not change are reused.
2. `publish_release.ps1 -Version <x> -Notes <notes file>` uploads to GitHub as a draft and publishes
   only when every file is up. Players' launchers see the release from that moment.

Stop the server before step 1. Publish only when the owner asks.

## Sharing safely

- **Never commit a played database.** It contains accounts, characters, bot rosters, inventories
  and economy history. Also keep `account.txt`, logs, dumps and backups out of commits.
- **Review before pushing.** Run `git diff --cached` before every push; `.gitignore` is a safety
  net only.
- **Local only:** the default setup is for one PC. Don't expose it to the internet as-is.
