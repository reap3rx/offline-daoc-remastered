# The Remastered client - source

The client of Offline DAoC Remastered, built in Godot 4.7 (.NET). It speaks the DAoC network protocol of
the original client (game client version 1.127) to the local server: what it shows is decoded from
the server's packets. Players get it through the launcher and installer of
[Offline DAoC Remastered](https://github.com/reap3rx/offline-daoc-remastered/releases); see
[docs/PLAY.md](../../docs/PLAY.md).

## Layout

| Path | What it is |
|---|---|
| `godot/game/` | All client code: GDScript, plus the network client in C# (`net/DaocClient.cs`). `net/server.gd` and `net/server_world.gd` turn the server's packets into the game world. |
| `godot/tests/` | Probes and checks run inside the game (`tests/load_check.gd` compiles scripts with the autoloads present). |
| `godot/tools/` | Content maintenance scripts run inside Godot (`pack_scenes.gd` packs converted models into `.scn` files). |
| `pipeline/` | The Python content pipeline: it reads the original DAoC client's files (zones, NIF models, textures, sounds, interface art, game data) and writes the converted content into `godot/content`. |
| `tools/build_csharp.ps1` | Builds the C# network client into `godot/.godot/mono/temp/bin/Debug/MMOEngine.dll`. |

The repository holds the source only. The converted content (`godot/content`, about 44 GB) is derived
from the original game client's files and comes with the install.

## Two things to know before changing code

- **The server owns the game.** The launcher always starts the client with `--server=127.0.0.1`. The
  client's own older standalone game (combat, spells, pets, quests, tasks, bots, companions) was
  removed on 2026-11-15. Without a server the client is only a zone viewer for test probes; a few
  branches behind `not Server.active` remain and should not be extended.
- **The game runs from a copy.** Edit here, then copy the changed files to `new-client/godot/game` in
  the playable folder.

## Running from source

1. Install the .NET 10 SDK and Godot 4.7.2 (.NET build).
2. `godot/content` must be present (from an install, or built with the pipeline below).
   `godot/content/.gdignore` must stay: Godot must not import the content folder.
3. Build the network client: `tools\build_csharp.ps1` (again after every change to a `.cs` file;
   starting the game with `--path` does not compile C#).
4. Start the server from the launcher, then run
   `Godot_v4.7.2-stable_mono_win64.exe --path godot -- --server=127.0.0.1 --account=<name> --password=<password>`
   with the account from `runtime\account.txt`.

The launcher (`source/tools/OfflineDaoc.Launcher`) starts the engine the same way, with
`APPDATA=new-client\save`.

## Developer mode and performance

The debug text (Ctrl+F12), the bot inspector (Ctrl+F11) and the Ctrl+F1..F11 test keys work only when
`godot/dev_mode.txt` exists or the game is started with `--dev` (`game/ui/boot_settings.gd`). Releases
never include that file.

`game/perf_governor.gd` (the `Perf` autoload) keeps the frame rate by shedding per-character work under
load, and writes `perf_live.log` in the save folder: a line every two seconds, and a `[hitch]` line
naming what ran in any frame of 60 ms or more.

## The content pipeline

The pipeline needs Python 3.10+ (`pipeline/requirements-full.txt`), Real-ESRGAN for the 4x texture
upscale (`tools/realesrgan/realesrgan-ncnn-vulkan.exe` with its `models` folder), and the original DAoC
client's files (set `DAOC_CLIENT` to the client's folder). Each `build_*.py` script says at its top what
it builds and how to run it. A full rebuild takes many hours. After a model or effect rebuild, repack
the scenes:
`Godot --headless --path godot -s res://tools/pack_scenes.gd -- --force res://content/monsters/effects`.

## Release

See [docs/DEVELOPMENT.md](../../docs/DEVELOPMENT.md): `source/tools/release/make_release.ps1`, then
`publish_release.ps1`.
