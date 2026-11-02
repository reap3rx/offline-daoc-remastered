"""Player housing outdoors (owner 2026-11-02: "take a first pass at putting Foundations in the game"): the house
exteriors the server places (HouseCreate 0xD1: house model 1-12, Albion / Midgard / Hibernia cottage, house, villa,
mansion) and the lot markers that stand on empty lots (GameLotMarker: objects 1306 Midgard, 1307 Hibernia,
1308 Albion).

Chain: phousing/phousing.mpk ph_houses.csv (ID, description, NIF Exterior, NIF Interior, ...) -> phousing/nifs/
<NIF Exterior>.npk; the lot markers: gamedata objects.csv -> items.csv (MLot / Hlot / Alot) -> phousing/nifs/<name>.nif.
Converted with nif_static (Godot axes, metres) and drawn by the client with the zones' layered materials
(game/world/housing.gd).

    python build_housing.py

Writes godot/content/housing/models/<nif>.gltf, godot/content/housing/textures/original/<texture>.png and
godot/content/housing/housing.json {houses: {model: {name, file, interior}}, objects: {model: {name, file}}}.
The housing zones themselves are ordinary terrain zones: build_zone.py <zone> --no-upscale (phousing/zones)."""
import csv, io, json, sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from assets_pipeline import CLIENT, ROOT
from daoc_mpk import read_mpk
from texture_index import TextureIndex
from build_zone import save_if_changed
import nif_static

OUT = ROOT / 'godot/content/housing'
LOT_OBJECTS = (1306, 1307, 1308)


def nif_bytes(files, name):
    """A NIF from phousing/nifs: <name>.nif, or the one inside <name>.npk (an MPAK)."""
    p = files.get(name.lower() + '.nif')
    if p is not None:
        return p.read_bytes()
    p = files.get(name.lower() + '.npk')
    if p is None:
        return None
    return next((v for k, v in read_mpk(str(p)).items() if k.endswith('.nif')), None)


def main():
    files = {p.name.lower(): p for p in (CLIENT / 'phousing/nifs').iterdir()}
    ph = read_mpk(str(CLIENT / 'phousing/phousing.mpk'))
    rows = [r for r in csv.reader(io.StringIO(ph['ph_houses.csv'].decode('latin1'))) if r and r[0].strip().isdigit()]
    g = read_mpk(str(CLIENT / 'gamedata.mpk'))
    objects = {r[0]: r for r in csv.reader(io.StringIO(g['objects.csv'].decode('latin1'))) if r and r[0].isdigit()}
    items = {r[0]: r for r in csv.reader(io.StringIO(g['items.csv'].decode('latin1'))) if r and r[0].isdigit()}
    mdir = OUT / 'models'
    mdir.mkdir(parents=True, exist_ok=True)
    (ROOT / 'godot/content/.gdignore').touch()
    tex, out, missing = set(), {'houses': {}, 'objects': {}}, []

    def convert(nif_name):
        raw = nif_bytes(files, nif_name)
        if raw is None:
            missing.append(nif_name + ' (no NIF)')
            return None
        base = nif_name.lower()
        info = nif_static.convert(raw, str(mdir / f'{base}.gltf'), '../textures/original')
        tex.update(info['textures'])
        for w in info['warnings']:
            print('  warning', base, w)
        print(f'{base}: {info["triangles"]} triangles, {info["collision_triangles"]} collision')
        return f'models/{base}.gltf'

    for r in rows:
        model, desc, ext, interior = int(r[0]), r[1].strip(), r[2].strip(), r[3].strip() if len(r) > 3 else ''
        if not ext:
            continue                                   # the table's first line (its row count)
        f = convert(ext)
        if f:
            out['houses'][str(model)] = {'name': desc, 'file': f, 'interior': interior.lower()}
    for m in LOT_OBJECTS:
        o = objects.get(str(m))
        it = items.get(o[2].strip()) if o else None
        if it is None:
            missing.append(f'object {m} (no objects / items.csv row)')
            continue
        f = convert(it[2].strip())
        if f:
            out['objects'][str(m)] = {'name': o[1].strip(), 'file': f}
    idx = TextureIndex()
    odir = OUT / 'textures/original'
    odir.mkdir(parents=True, exist_ok=True)
    for n in sorted(tex):
        doubled = n.endswith(('__d2', '__x2'))
        img = idx.image(n[:-4] if doubled else n) or nif_static.EMBEDDED.get(n[:-4] if doubled else n)
        if img is None and n.startswith('ph_woodxx'):
            img = idx.image('ph_wood01_hd')            # the house's wood slot: the client fills it from the house's
                                                       # wood material (ph_textures.csv 50-59); the first one for now
        if img is None:
            missing.append('texture ' + n)
            continue
        if doubled and n.endswith('__d2'):
            img = Image.fromarray(np.clip(np.asarray(img.convert('RGB'), np.float32) * 2.0, 0, 255).astype(np.uint8))
        save_if_changed(img, odir / f'{n}.png')
    out['missing'] = missing
    (OUT / 'housing.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(len(out['houses']), 'houses,', len(out['objects']), 'objects,', len(tex), 'textures; missing:', missing)


if __name__ == '__main__':
    main()
