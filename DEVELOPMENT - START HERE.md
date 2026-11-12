# Developer start

**Offline DAoC Remastered**: a single-player Dark Age of Camelot (Classic + Shrouded Isles, 1.65) - the OpenDAoC
server with living player bots, played through a new Godot client. It grew out of the original
[OfflineDAoC](https://github.com/shadowofze/OfflineDAoC) by u/zomboden and the Offline DAoC community, and was built
on from there with Anthropic's Claude.

Read these first:
- [AGENTS.md](AGENTS.md): project rules and layout.
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): how to build, test and deploy.
- [source/new-client/README.md](source/new-client/README.md): the new client's source and how to run it.
- [docs/LLM-QUICKSTART.md](docs/LLM-QUICKSTART.md): how to customize with your own AI assistant.

The folder:
- `source/` - everything that is built: the server (`source/server`), the new client (`source/new-client`, with the
  content pipeline that converts the original game's files), the launcher (`source/tools/OfflineDaoc.Launcher`) and the
  release tools (`source/tools/release`).
- `new-client/` - the client as it runs (the Godot project, its converted content, the launcher in `new-client/runtime`).
- `runtime/` - the server as it runs, its world database (`runtime/data`) and the original client the pipeline reads.

Play from `new-client/runtime/OfflineDAoC.exe` (the launcher). Releases: `source/tools/release/make_release.ps1`, then
`publish_release.ps1` - see the comments at the top of each. Keep saves out of commits, and report automated tests
separately from in-game checks.
