"""Offline DAoC Remastered: the release (owner 2026-11-11: "the installer will install the launcher and all necessary
game files, and then ... the launcher will check for updates and then update the local files").

Gathers only what a player needs from the working game folder into a clean install layout, cuts it into packs (zips
under GitHub's 2 GiB per-file limit) and writes the release's manifest.json. The launcher installs and updates from
that manifest: it downloads only the packs whose content changed since the version it has.

    python build_release.py --game "E:/Offline DAOC 036c/playable-v0.36c" --version 0.1.0 --world new-world.db
                            --launcher <the launcher's dotnet publish folder> --out "E:/Offline DAOC Release"
                            [--repo OWNER/REPO] [--notes notes.txt] [--stage-only]

The install it describes (and --stage-only writes out as plain folders, to try before publishing):
    DISCLAIMER.txt, CREDITS.txt, LICENSES/
    client/launcher/      the launcher (Offline DAoC Remastered.exe)
    client/godot/         the game: project, scripts, the .NET build, content/
    client/tools/godot_net/   the engine
    world/server/         the server (navmesh in its own packs)
    world/data/           the new world database (installed once, never replaced) and the bot names
    tools/dotnet/         the .NET runtime the server and the game run on
A player's own files are never in a pack: client/save (settings, keybinds), world/data/opendaoc.sqlite3.db after the
first install, world/logs, world/server's state files.

Packs keep their names between releases (pack_plan.json beside --out: how many buckets each large folder is cut into,
fixed once chosen, so a changed file moves only its own bucket). A pack whose files are unchanged is not built again:
the manifest points at the release that first carried it (published.json).
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

PACK_LIMIT = 1_700_000_000           # bytes of files per pack before zipping (GitHub's limit is 2 GiB a file)
STORED = {".png", ".jpg", ".jpeg", ".dds", ".ktx", ".ktx2", ".ogg", ".mp3", ".zip", ".webp", ".glb", ".ctex", ".scn"}
HERE = Path(__file__).resolve().parent


def sha256_file(path, cache):
    st = path.stat()
    key = str(path)
    hit = cache.get(key)
    if hit and hit[0] == st.st_size and hit[1] == int(st.st_mtime):
        return hit[2]
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    cache[key] = [st.st_size, int(st.st_mtime), h.hexdigest()]
    return cache[key][2]


def walk(root, skip_dirs=(), skip_files=(), skip_ext=()):
    """Files under root as (relative posix path, absolute path), leaving out the named folders / files / extensions."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        # a skipped folder is named by its path from root ("logs", ".godot/mono/temp/obj") - a nested folder that only
        # shares the name stays (runtimes/win-x64/native held the server's SQLite.Interop.dll)
        dirnames[:] = sorted(d for d in dirnames if (f"{rel_dir}/{d}" if rel_dir != "." else d) not in skip_dirs)
        for name in sorted(filenames):
            rel = f"{rel_dir}/{name}" if rel_dir != "." else name
            if name in skip_files or rel in skip_files or Path(name).suffix.lower() in skip_ext:
                continue
            yield rel, Path(dirpath) / name


def gather(game, launcher, world_db, generated):
    """component -> {install path: source file}"""
    game = Path(game)
    nc = game / "new-client"
    comps = {}

    def add(comp, dest_prefix, items):
        d = comps.setdefault(comp, {})
        for rel, src in items:
            d[f"{dest_prefix}/{rel}" if dest_prefix else rel] = src

    # the launcher (a self-contained publish) and where it finds the world
    add("launcher", "client/launcher", walk(launcher, skip_ext={".pdb"}))
    add("launcher", "client/launcher", walk(generated))         # server_root.txt, update.json
    # the engine and the .NET runtime
    add("engine", "client/tools/godot_net", walk(nc / "tools" / "godot_net"))
    add("dotnet", "tools/dotnet", walk(game / "tools" / "dotnet"))
    # the game: everything in the Godot project but its content, the tests and the developer's own files
    add("game", "client/godot", walk(nc / "godot",
                                     skip_dirs={"content", "tests", ".godot/mono/temp/obj", ".godot/editor", ".godot/shader_cache"},
                                     skip_files={"dev_mode.txt"}, skip_ext={".log", ".tmp"}))
    # content: one component per folder (the big ones are cut into buckets later)
    for sub in sorted(p for p in (nc / "godot" / "content").iterdir() if p.is_dir()):
        add(f"content-{sub.name}", f"client/godot/content/{sub.name}", walk(sub, skip_ext={".log", ".tmp"}))
    # the hair fits tuned in the creator (they live beside the pipeline on the developer's machine)
    tuning = game / "source" / "new-client" / "pipeline" / "hair_tuning"
    if tuning.is_dir():
        add("content-characters", "client/godot/content/characters/hair_tuning",
            ((p.name, p) for p in sorted(tuning.glob("*.json"))))
    # the server: its program and data, none of the running state
    server = game / "runtime" / "server"
    add("server", "world/server", walk(server,
        skip_dirs={"logs", "navmesh", "win-x64", "scripts", "story-quests"},
        skip_files={"bot-ai-delay.json", "bot-goals.json", "bot-world.json", "bot-world.request", "rvr-world.json",
                    "dynamic-events-state.json", "realm-event-records.sqlite3"},
        skip_ext={".old-counter", ".pdb", ".log", ".bak"}))
    add("navmesh", "world/server/navmesh", walk(server / "navmesh"))
    add("world-data", "world/data/bots", walk(game / "runtime" / "data" / "bots"))
    # the new world: installed once, a player's own from then on
    add("world-db", "world/data", [("opendaoc.sqlite3.db", Path(world_db))])
    # what a player reads
    texts = [("DISCLAIMER.txt", HERE / "text" / "DISCLAIMER.txt"), ("CREDITS.txt", HERE / "text" / "CREDITS.txt")]
    lic = [("LICENSES/OpenDAoC-GPL.txt", game / "source" / "server" / "LICENSE"),
           ("LICENSES/Godot-MIT.txt", nc / "tools" / "godot_net" / "LICENSE.txt"),
           ("LICENSES/dotnet-MIT.txt", game / "tools" / "dotnet" / "LICENSE.txt"),
           ("LICENSES/dotnet-third-party.txt", game / "tools" / "dotnet" / "ThirdPartyNotices.txt"),
           ("LICENSES/THIRD_PARTY.md", game / "THIRD_PARTY.md")]
    add("docs", "", [(r, s) for r, s in texts + lic if Path(s).is_file()])
    return comps


INSTALL_ONLY = {"world-db"}


def plan_packs(comps, sizes, plan_path):
    """component -> buckets of install paths; the bucket counts kept in pack_plan.json once chosen."""
    plan = json.loads(plan_path.read_text()) if plan_path.exists() else {}
    packs = {}
    for comp, files in comps.items():
        total = sum(sizes[p] for p in files)
        n = plan.get(comp) or max(1, math.ceil(total / (PACK_LIMIT * 0.7)))     # room to grow before a bucket fills
        plan[comp] = n
        if n == 1:
            packs[comp] = sorted(files)
            continue
        buckets = [[] for _ in range(n)]
        for p in sorted(files):
            buckets[int(hashlib.md5(p.encode()).hexdigest(), 16) % n].append(p)
        for i, b in enumerate(buckets):
            if b:
                packs[f"{comp}-{i + 1:02d}"] = b
    for pid, files in packs.items():
        size = sum(sizes[p] for p in files)
        if size > PACK_LIMIT:
            raise SystemExit(f"{pid} holds {size / 1e9:.2f} GB - raise its bucket count in {plan_path} (a one-time reshuffle)")
    plan_path.write_text(json.dumps(plan, indent=1, sort_keys=True))
    return packs


def build_zip(dest, files, srcs):
    tmp = dest.with_suffix(".part")
    with zipfile.ZipFile(tmp, "w", allowZip64=True) as z:
        for p in files:
            kind = zipfile.ZIP_STORED if Path(p).suffix.lower() in STORED else zipfile.ZIP_DEFLATED
            z.write(srcs[p], p, compress_type=kind, compresslevel=6 if kind == zipfile.ZIP_DEFLATED else None)
    tmp.replace(dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--world", required=True, help="the new world database (make_world_db.py)")
    ap.add_argument("--launcher", required=True, help="the launcher's publish folder")
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", default="OWNER/offline-daoc-remastered")
    ap.add_argument("--notes", default="")
    ap.add_argument("--min-launcher", default="")
    ap.add_argument("--stage-only", action="store_true", help="write the install as folders under --out/stage instead")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cache_path = out / "hash-cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    generated = out / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "server_root.txt").write_text("..\\..\\world\n")
    (generated / "update.json").write_text(json.dumps(
        {"feed": f"https://github.com/{a.repo}/releases/latest/download/manifest.json"}, indent=1))
    comps = gather(a.game, a.launcher, a.world, generated)
    srcs = {p: s for files in comps.values() for p, s in files.items()}
    t0 = time.time()
    sizes, hashes = {}, {}
    for i, (p, s) in enumerate(sorted(srcs.items())):
        sizes[p] = s.stat().st_size
        hashes[p] = sha256_file(s, cache)
        if i % 2000 == 0:
            print(f"  hashing {i}/{len(srcs)} ({time.time() - t0:.0f}s)", flush=True)
            cache_path.write_text(json.dumps(cache))
    cache_path.write_text(json.dumps(cache))
    print(f"{len(srcs)} files, {sum(sizes.values()) / 1e9:.2f} GB")

    if a.stage_only:
        stage = out / "stage"
        for p, s in srcs.items():
            d = stage / p
            d.parent.mkdir(parents=True, exist_ok=True)
            if not d.exists() or d.stat().st_size != sizes[p]:
                shutil.copy2(s, d)
        print(f"staged -> {stage}")
        return

    packs = plan_packs(comps, sizes, out / "pack_plan.json")
    published_path = out / "published.json"
    published = json.loads(published_path.read_text()) if published_path.exists() else {}
    pack_dir = out / "packs"
    pack_dir.mkdir(exist_ok=True)
    tag = f"v{a.version}"
    upload = []
    entries = []
    for pid in sorted(packs):
        files = packs[pid]
        content = hashlib.sha256("\n".join(f"{p}\t{hashes[p]}" for p in files).encode()).hexdigest()
        name = f"{pid}-{content[:10]}.zip"
        zpath = pack_dir / name
        if name not in published:
            if not zpath.exists():
                print(f"  packing {name} ({sum(sizes[p] for p in files) / 1e6:.0f} MB, {len(files)} files)", flush=True)
                build_zip(zpath, files, srcs)
            published[name] = {"tag": tag, "sha256": sha256_file(zpath, cache), "size": zpath.stat().st_size}
            upload.append(zpath)
        info = published[name]
        entries.append({"id": pid, "file": name, "tag": info["tag"], "size": info["size"], "sha256": info["sha256"],
                        "content": content, "install_only": pid in INSTALL_ONLY,
                        "files": [[p, sizes[p], hashes[p]] for p in files]})
    manifest = {
        "product": "Offline DAoC Remastered", "version": a.version, "released": time.strftime("%Y-%m-%d"),
        "notes": Path(a.notes).read_text(encoding="utf-8") if a.notes and Path(a.notes).exists() else a.notes,
        "min_launcher": a.min_launcher or a.version,
        "download": f"https://github.com/{a.repo}/releases/download/{{tag}}/{{file}}",
        "packs": entries,
    }
    (out / tag).mkdir(exist_ok=True)
    (out / tag / "manifest.json").write_text(json.dumps(manifest, separators=(",", ":")))
    published_path.write_text(json.dumps(published, indent=1, sort_keys=True))
    cache_path.write_text(json.dumps(cache))
    total = sum(e["size"] for e in entries)
    new = sum(p.stat().st_size for p in upload)
    print(f"{tag}: {len(entries)} packs, {total / 1e9:.2f} GB to install; {len(upload)} new packs ({new / 1e9:.2f} GB) to upload")
    (out / tag / "upload.txt").write_text("\n".join(str(p) for p in upload + [out / tag / "manifest.json"]))


if __name__ == "__main__":
    sys.exit(main())
