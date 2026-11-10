"""The weapon twirls the Catacombs animations lost (owner 2026-11-09: "there are some Hibernian piercing styles that
are supposed to twirl the dagger/rapier in like a 360 degree spin before thrusting ... bugged in the catacombs models
even in the official version").

The classic clips spin the weapon on its own bone, Bip01 R Held / L Held (a_h_1t_cs01_04.kfa: about 770 degrees in
its first 0.6 s); the Catacombs copies (Cat_A_H_1T_CS01_04.kfa) keep that bone still, so the blade only follows the
hand. For every combat and style clip whose Catacombs Held bone is still while the classic one moves, this writes the
classic Held track: godot/content/characters/held_twirls.json {clip: {bone: {"t": [s...], "q": [[x, y, z, w]...]}}}.
Fig3Figure lays it over the Catacombs clip as a change from the classic clip's first key, so the grip stays the
Catacombs one and only the spin is added.

    python pipeline/build_held_twirls.py [--content <godot/content folder>]   (default: this tree's godot/content)
"""
import csv, io, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from assets_pipeline import CLIENT, ROOT
from daoc_mpk import read_mpk
import nif_character as nc
import build_races as br

OUT = ROOT / 'godot/content/characters/held_twirls.json'
CLASSIC_ROW, CATA_ROW = '49', '244'          # canims.csv: Elf / Celt Female (classic), Cata Elf Female - every
                                              # humanoid row names the same a_h_* / Cat_A_H_* files
BONES = ('Bip01 R Held', 'Bip01 L Held')


def turn(qs):
    """Total angle (degrees) a rotation track sweeps, key to key."""
    out = 0.0
    for a, b in zip(qs[:-1], qs[1:]):
        out += np.degrees(2 * np.arccos(min(1.0, abs(float(np.dot(a, b))))))
    return out


def main():
    global OUT
    if '--content' in sys.argv:
        content = Path(sys.argv[sys.argv.index('--content') + 1])
        OUT = content / 'characters/held_twirls.json'
        br.OUT = content / 'characters'                      # (style_clips reads classes/styles.json beside it)
    g = read_mpk(str(CLIENT / 'gamedata.mpk'))
    rows = list(csv.reader(io.StringIO(g['canims.csv'].decode('latin1'))))
    header = rows[1]
    classic = next(r for r in rows[2:] if r and r[0].strip() == CLASSIC_ROW)
    cata = next(r for r in rows[2:] if r and r[0].strip() == CATA_ROW)
    _, _, files = nc.animation_tables()
    names = (CLIENT / 'figures/animnode.dat').read_bytes().decode('latin1').split('\r\n')
    cols, _ = br.style_clips()
    clips = dict(br.COMBAT_CLIPS)
    clips.update(cols)
    out = {}
    for col, clip in sorted(clips.items()):
        if col not in header:
            continue
        i = header.index(col)
        a, b = classic[i].strip() if i < len(classic) else '', cata[i].strip() if i < len(cata) else ''
        if a not in files or b not in files or not files[a][2].strip() or not files[b][2].strip():
            continue
        ka, kb = files[a][2].strip(), files[b][2].strip()
        try:
            ta, _ = nc.read_clip(ka, names)
            tb, _ = nc.read_clip(kb, names)
        except StopIteration:
            continue
        try:
            length = float(files[a][3]) / float(files[a][5])
        except (ValueError, ZeroDivisionError):
            length = None
        for bone in BONES:
            if 'rot' not in ta.get(bone, {}) or 'rot' not in tb.get(bone, {}):
                continue
            t, q = ta[bone]['rot']
            q = np.asarray(q, dtype=float)
            if length:
                keep = np.asarray(t) <= length + 1e-4
                t, q = np.asarray(t)[keep], q[keep]
            moved, still = turn(q), turn(np.asarray(tb[bone]['rot'][1], dtype=float))
            if moved < 60.0 or still > 5.0:
                continue
            out.setdefault(clip, {})[bone] = {'t': [round(float(x), 4) for x in t],
                                              'q': [[round(float(c), 5) for c in v] for v in q]}
            print(f'{clip:24s} {bone}: {ka} turns {moved:.0f} deg, {kb} {still:.0f}')
    OUT.write_text(json.dumps(out), encoding='utf-8')
    print(len(out), 'clips ->', OUT)


if __name__ == '__main__':
    main()
