"""The high-quality pass for content first built with --no-upscale (owner 2026-11-02: "upscale the housing zones").

    python upscale_built.py zones=13,16,17 [housing]

For each built zone (godot/content/zones/zoneNNN): textures/original -> textures/x4plus and terrain/original ->
terrain/x4plus (Real-ESRGAN x4plus, then 2x of the original - build_zone's upscale_dir), and zone.json's terrain sets
gain their <set>_x4plus entries (what build_zone writes when it upscales). 'housing': content/housing's textures (the
houses, interiors and housing items) the same way. The clients load textures/x4plus whenever it exists.
The housing zones share most of their textures, so each distinct picture is upscaled once (by its bytes) and copied
to every folder that has it.
"""
import hashlib, json, shutil, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from assets_pipeline import ROOT
import build_zone

CONTENT = ROOT / 'godot/content'


def pairs(zones, housing):
    out = []
    for z in zones:
        d = CONTENT / 'zones' / f'zone{z:03d}'
        if not (d / 'zone.json').exists():
            print('zone', z, 'not built')
            continue
        out.append((d / 'textures/original', d / 'textures/x4plus'))
        out.append((d / 'terrain/original', d / 'terrain/x4plus'))
    if housing:
        out.append((CONTENT / 'housing/textures/original', CONTENT / 'housing/textures/x4plus'))
    return [(s, t) for s, t in out if s.is_dir()]


def main():
    zones = [int(v) for a in sys.argv[1:] if a.startswith('zones=') for v in a[6:].split(',') if v.strip()]
    todo = []                                        # (source png, destination png, hash)
    for src, dst in pairs(zones, 'housing' in sys.argv[1:]):
        for p in sorted(src.glob('*.png')):
            t = dst / p.name
            if t.exists() and t.stat().st_mtime >= p.stat().st_mtime:
                continue
            todo.append((p, t, hashlib.md5(p.read_bytes()).hexdigest()))
    unique = {h: p for p, _, h in todo}
    print(len(todo), 'textures to upscale,', len(unique), 'distinct')
    with tempfile.TemporaryDirectory() as tmp:
        src, big = Path(tmp) / 'src', Path(tmp) / 'big'
        src.mkdir()
        for h, p in unique.items():
            shutil.copy2(p, src / f'{h}.png')
        names = sorted(src.glob('*.png'))
        for i in range(0, len(names), 200):          # in batches, so a long run shows progress
            batch = Path(tmp) / f'b{i}'
            batch.mkdir()
            for n in names[i:i + 200]:
                shutil.move(str(n), batch / n.name)
            build_zone.upscale_dir(batch, big)
            print('upscaled', min(i + 200, len(names)), '/', len(names), flush=True)
        for p, t, h in todo:
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(big / f'{h}.png', t)
    for z in zones:
        f = CONTENT / 'zones' / f'zone{z:03d}' / 'zone.json'
        if not f.exists():
            continue
        info = json.loads(f.read_text(encoding='utf-8'))
        sets = info.get('terrain_sets', {})
        added = False
        for name in [k for k in sets if not k.endswith('_x4plus')]:
            if (f.parent / 'terrain/x4plus' / f'{name}.png').exists() and f'{name}_x4plus' not in sets:
                sets[f'{name}_x4plus'] = f'terrain/x4plus/{name}.png'
                added = True
        if added:
            f.write_text(json.dumps(info, indent=1), encoding='utf-8')
            print('zone', z, 'terrain', sorted(sets))


if __name__ == '__main__':
    main()
