# Offline DAoC Mod (personal)

Ryan's personal modifications to OfflineDAoC v0.36c (an offline OpenDAoC / Dark Age of Camelot server).
Upstream project: https://github.com/shadowofze/OfflineDAoC (GPL-2.0, see LICENSE).

The first commit is the unmodified v0.36c install; every change after that is a mod.

## What's tracked here
- `source/`: server C# source
- `docs/`, `tools/`, start scripts, readmes
- `runtime/server/config/` and the small server `.json` settings
- `db-changes/`: every database edit as a dated SQL script (with an undo section)

## What's NOT tracked (too large / not ours)
- The game client (`new-client/`), logs, navmesh, bundled .NET, patch backups
- The database `runtime/data/opendaoc.sqlite3.db` (over GitHub's 100 MB limit)

## Database backups
Before each database edit, a copy is saved to
`E:\Offline DAOC 036c\db-backup\opendaoc.sqlite3.db` (outside this repo).
Only one backup is kept; each new backup overwrites the previous one.
To restore it: stop the server, then copy that file back over `runtime\data\opendaoc.sqlite3.db`.
