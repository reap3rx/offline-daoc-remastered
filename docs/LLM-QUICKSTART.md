# Customize Offline DAoC Remastered with your own AI assistant

You can make the game your own with an AI coding assistant such as Claude Code or Codex. You don't
need the author's permission to fork it.

## 1. Get your own copy

1. **Fork it:** click **Fork** on the GitHub page, then clone your fork.
2. **Get a playable game:** install the game as described in [PLAY.md](PLAY.md). The source alone
   isn't the playable game: the converted game content comes with the install.
3. **Keep two folders:** the source checkout, where you edit code, and the installed game, where you
   test builds.

## 2. Start your assistant with this prompt

> This is my fork of Offline DAoC Remastered, a single-player DAoC: an OpenDAoC-based server with
> player bots and companions, and a Godot game client. Read AGENTS.md and docs/DEVELOPMENT.md first.
> My source checkout is this folder; my installed game is at [path to the install folder]. Look at
> the current code before changing it. Don't start the server or replace files in the installed game
> without asking me, and back up anything you replace. Protect my account, characters, bots, items,
> coins and saves. Build and run the tests separately, make only the change I ask for, and tell me
> exactly what changed and how it was verified. The change I want is: [describe it].

## 3. Where things live

| To change… | Look in |
|---|---|
| The game client: interface, world, controls, graphics | `source/new-client/godot/game` (see its [README](../source/new-client/README.md)) |
| Autonomous gamebot goals, camps, groups, travel | `source/server/GameServer/bots/autonomous` |
| Companion bots and class combat AI | `source/server/GameServer/bots` |
| Story quests, dynamic events, custom NPCs and commands | `source/server/GameServer/scripts` |
| Combat rules, spells, pets | `source/server/GameServer` |
| The launcher | `source/tools/OfflineDaoc.Launcher` |
| World data (spawns, spells, items) | the game's world database. Write changes as a script in `db-changes/` with a backup, and never commit a played database |

## Good habits

- **Back up first.** Copy your world database before testing a change to the server or its data.
- **Commit only source.** Commit source changes to your fork, not files from your installed game.
- **Verify in game.** Say what was tested in game and what was only covered by automated tests.
- **Keep the licenses and credits** ([THIRD_PARTY.md](../THIRD_PARTY.md)). A pull request to this
  project is a proposal; it won't merge by itself.
