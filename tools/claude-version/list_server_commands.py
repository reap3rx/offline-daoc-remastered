"""Writes docs/gm/ALL-SERVER-COMMANDS.md from the server's own command registrations (every [Cmd(...)] attribute
under source/server/GameServer). Run from the repository's root after adding or changing a command:

    python tools/claude-version/list_server_commands.py
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "source" / "server" / "GameServer"
OUT = ROOT / "docs" / "gm" / "ALL-SERVER-COMMANDS.md"
LEVELS = [("Player", "Player commands", "Anyone can use these."),
          ("GM", "GM commands", "Need GM mode (the launcher's GM option, set while the server is stopped)."),
          ("Admin", "Administrator commands", "Need an administrator account.")]


def commands():
    rows = []
    for d, _, files in os.walk(SRC):
        for f in files:
            if not f.endswith(".cs"):
                continue
            text = (Path(d) / f).read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"\[Cmd(?:Attribute)?\s*\((.*?)\)\s*\]", text, re.S):
                a = m.group(1)
                name = re.search(r'"(&[^"]+)"', a)
                if not name:
                    continue
                priv = re.search(r"ePrivLevel\.(\w+)", a)
                al = re.search(r"new\s+string\s*\[\s*\]\s*\{(.*?)\}", a, re.S)
                aliases = re.findall(r'"(&[^"]+)"', al.group(1)) if al else []
                rest = [s for s in re.findall(r'"((?:[^"\\]|\\.)*)"', a) if not s.startswith("&")]
                # a description that is a language key (GMCommands.Jump.Description) says nothing here
                texts = [s for s in rest if not re.fullmatch(r"[A-Za-z]+(\.[A-Za-z0-9_]+)+", s)]
                usage = [s for s in texts if s.lstrip().startswith(("/", "'/"))]
                desc = next((s for s in texts if s not in usage), "")
                rows.append((priv.group(1) if priv else "Player", "/" + name.group(1)[1:],
                             ["/" + x[1:] for x in aliases], desc, usage))
    return sorted(rows, key=lambda r: r[1].lower())


def cell(s):
    return s.replace("|", "\\|").replace("\n", " ").replace("\\\"", '"').strip()


def main():
    rows = commands()
    out = ["# All server commands", "",
           "Every command the server registers, by who may use it. Written by "
           "`tools/claude-version/list_server_commands.py` from the code; do not edit by hand. "
           "Many are inherited from the server the game is built on and are untested here. "
           "The everyday ones are in [QUICK-COMMANDS.md](../QUICK-COMMANDS.md).", ""]
    for level, title, note in LEVELS:
        mine = [r for r in rows if r[0] == level]
        out += [f"## {title} ({len(mine)})", "", note, "", "| Command | Also | What it does | Usage |", "| --- | --- | --- | --- |"]
        for _, name, aliases, desc, usage in mine:
            out.append("| `%s` | %s | %s | %s |" % (name, " ".join("`%s`" % a for a in aliases), cell(desc),
                                                 "<br>".join("`%s`" % cell(u) for u in usage[:6])))
        out.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print(f"{len(rows)} commands -> {OUT}")


if __name__ == "__main__":
    main()
