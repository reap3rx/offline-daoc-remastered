# GM and developer tools

Tools for running your own world and for working on the game. None of this is needed to play.

## GM mode

GM mode gives your account the GM commands (teleporting, spawning, editing NPCs and items, and so on).
Turn it on with the GM option in the launcher. The server must be stopped when you change it.

Every command, by who may use it, is in [ALL-SERVER-COMMANDS.md](ALL-SERVER-COMMANDS.md): 218 player
commands, 66 GM commands and 15 administrator commands. That file is written from the server's code by
`tools/claude-version/list_server_commands.py`; run it again after adding a command. The everyday
commands are in [QUICK-COMMANDS.md](../QUICK-COMMANDS.md).

## Developer mode in the game client

Developer mode is on when the file `dev_mode.txt` exists in the game's `godot` folder, or when the game
is started with `--dev`. Releases never include that file. It unlocks:

| Key | What it does |
| --- | --- |
| Ctrl+F12 | Debug text on screen (for issue screenshots) |
| Ctrl+F11 | Inspect the targeted bot: what it is doing and its last decisions, in the chat |
| Ctrl+F1 | Cycle the terrain texture set |
| Ctrl+F2 | Switch between the upscaled and the original textures |
| Ctrl+F3 | Terrain detail grain on or off |
| Ctrl+F4 | Grass and ground clutter on or off |
| Ctrl+F5 | Jump to the next test spot in the zone |
| Ctrl+F6 | Fly |
| Ctrl+F7 | Jump an hour ahead |
| Ctrl+F8 | Time speed: normal, 20x, 120x |
| Ctrl+F9 | Force a storm on, off, or back to the weather's own choice |
| Ctrl+F10 | Ambient occlusion on or off |

It also unlocks the **hair fitting sliders** on the character creation screen. Each hair, beard and
head part gets sliders that move and scale it on the head, with save, disable and completed controls
for the race under them. Right-click a slider to reset it. The results are saved per race in
`source/new-client/pipeline/hair_tuning/<race>.json` and apply to every character of that race.

## Client commands (typed in chat, any mode)

| Command | What it does |
| --- | --- |
| `/look` | The look panel: sliders for the zone's remastered look (fog and mist, exposure and the rest), saved per zone |
| `/light` | Place lights where the world has no lamp: `/light <kind>`, `/light remove`, `/light undo`, `/light list`, at the spot the cursor points at |
| `/loc` | Your position, as the original client printed it |
| `/macro <name> <command>` | Makes a macro of a command, kept by the client |

## Performance log

The game writes `perf_live.log` in its settings folder: a line every two seconds with the frame rate
and where the frame's time went, and a `[hitch]` line naming what ran in any frame of 60 ms or more.

## Start options

The game accepts options after `--` on its command line. The ones used most in development:

| Option | What it does |
| --- | --- |
| `--dev` | Developer mode for this run |
| `--auto-play=<realm>:<Character>` | Log straight in as that character (`hib:Fiona`) |
| `--live-probe=<name>` | Run the probe script `tests/<name>.gd` inside the live game |
| `--mute` | No sound |
