# Offline DAoC Remastered

**Dark Age of Camelot, rebuilt to play alone or with a world full of living player bots - on a new engine, with
remastered graphics.** Classic + Shrouded Isles, 1.65 rules, entirely on your own PC. Free.

> **A free fan project.** Not affiliated with, endorsed by or supported by Electronic Arts, Broadsword Online Games
> or Mythic Entertainment. Dark Age of Camelot and its art, world, music and sounds belong to their owners; the game's
> zones, models, textures and sounds here were converted from the original client's files. Nothing here is for sale,
> and no donations are taken. If you enjoy it, play the real thing too: [darkageofcamelot.com](https://www.darkageofcamelot.com/).
> Much of this project's code was written with Anthropic's Claude, an AI model, under the developer's direction - see
> [DISCLAIMER](source/tools/release/text/DISCLAIMER.txt).

## Install

1. Download **Offline-DAoC-Remastered-Setup.exe** from the [latest release](https://github.com/reap3rx/offline-daoc-remastered/releases/latest).
2. Run it and pick a folder with about **50 GB free** (an SSD is best). No administrator rights needed.
3. The launcher opens and downloads the game (about 45 GB). Leave it running; it can resume if it's interrupted.
4. Click **START SERVER**, then **ENTER REALM**.

From then on the launcher checks for updates each time it starts and downloads only what changed. Your characters,
world and settings are never touched by an update.

**Playing on more than one computer?** Install Google Drive for desktop, then in the launcher's Options choose
*Connect Google Drive*. Your save travels with you. Optional - one computer needs nothing.

**Needs:** Windows 10 or 11 (64-bit) and a graphics card with Vulkan support. More memory lets you run a bigger bot
population.

## What's in it

- **A new game client** (Godot 4): remastered zones, characters, spells and lighting; modern and classic interfaces;
  action combat with keyboard, mouse or controller.
- **A living world**: thousands of player bots with their own personalities who level, group, run dungeons, fight
  in RvR and battlegrounds, buy and sell, camp around fires - and answer your invites in character.
- **The classic game underneath**: the OpenDAoC server, set to Classic + Shrouded Isles and the 1.65 rules.

## Bugs, changes and what's next

The changelog for each build ships with its release notes. Report problems on the
[issues page](https://github.com/reap3rx/offline-daoc-remastered/issues).

## Building it yourself

Everything here is open: change it, fork it, make it your own. Start with
[DEVELOPMENT - START HERE.md](DEVELOPMENT%20-%20START%20HERE.md). The original game's assets are not in this
repository; the content pipeline (`source/new-client/pipeline`) converts them from a Dark Age of Camelot client you
have. Releases are made with `source/tools/release/make_release.ps1`.

## Credits

Mythic Entertainment, who made Dark Age of Camelot; Broadsword, who keep it running; u/zomboden and the Offline DAoC
community, whose single-player DAoC ([OfflineDAoC](https://github.com/shadowofze/OfflineDAoC)) this grew out of; the OpenDAoC and Dawn of Light projects; Godot Engine; NifTools;
Real-ESRGAN; Allakhazam's quest guides; and Anthropic's Claude. The full list:
[CREDITS](source/tools/release/text/CREDITS.txt).

## License

GNU General Public License v3 ([LICENSE](LICENSE)), as the OpenDAoC server it builds on. Third-party components keep
their own licenses ([THIRD_PARTY.md](THIRD_PARTY.md)). The license covers this project's code, not Dark Age of
Camelot's assets.
