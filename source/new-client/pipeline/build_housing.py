"""Player housing (owner 2026-11-02: "take a first pass at putting Foundations in the game", then "interiors,
purchasing, and decorating"): the houses the server places (HouseCreate 0xD1: house model 1-12, Albion / Midgard /
Hibernia cottage, house, villa, mansion; 13-14 the tier 5s), their interiors (HouseEnter 0x08), the lot markers on empty
lots (GameLotMarker: objects 1306 Midgard, 1307 Hibernia, 1308 Albion), and the furniture, garden pieces and hookpoint
objects players put in and around them (HousingItem 0x09, HouseChangeGarden 0xD2, the hookpoints' objects).

Chain: phousing/phousing.mpk ph_houses.csv (ID, description, NIF Exterior, NIF Interior, ...) -> phousing/nifs/<NIF>.npk;
objects: gamedata objects.csv (col 36 "HouseItem Nif", else col 2) -> items.csv NIF name -> phousing/nifs or items/.
Converted with nif_static (Godot axes, metres) and drawn by the client with the zones' layered materials
(game/world/housing.gd). The houses' choosable parts are tagged (nif_static.GROUP_TAG -> mesh names grp_<tag>__<n>):
  roofN / wallN       the roof / wall styles (RoofMaterial / WallMaterial 0-2: the NIF's roof00.. / wall00..)
  porch, tent         the porch (bought with a porch deed) and its awning (PorchRoofColor)
  shields, banners    the guild emblem pieces (outdoor / indoor guild banner and shield)
  carpetN             the interior's rugs (Rug1Color..Rug4Color, tints.csv colours)
  floorpN / wallpN    the interior's placement planes (never drawn): furniture stands on floorplaneN / hangs on
                      wallplaneN - the HousingItem's Position is the plane's number
  doorN               the door styles (DoorMaterial 0-9: the NIF's door00..) Named points come out as well: the garden's
GPointN (a garden item's Position is the point's number), the interior's EntryPoint and V / T / M / B points (vault,
crafting table, merchant, bindstone). The interiors' hookpoints come from the server database (HouseHookpointOffset,
read only): {id: [x, y, z (metres, interior frame), heading]}.

    python build_housing.py

Writes godot/content/housing/models/*.gltf, godot/content/housing/textures/original/<texture>.png and
godot/content/housing/housing.json {houses: {model: {name, file, interior, points}}, interiors: {model: {file,
points, hookpoints}}, objects: {model: {name, file}}, woods: [texture ...]}.
The housing zones themselves are ordinary terrain zones: build_zone.py <zone> --no-upscale (phousing/zones)."""
import csv, io, json, re, sqlite3, sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from assets_pipeline import CLIENT, ROOT
from daoc_mpk import read_mpk
from netimmerse import read_nif
from texture_index import TextureIndex
from build_zone import save_if_changed
import nif_static

OUT = ROOT / 'godot/content/housing'
DB = ROOT.parent.parent / 'runtime/data/opendaoc.sqlite3.db'      # the server's database (read only): hookpoints
LOT_OBJECTS = (1306, 1307, 1308)
POINT = re.compile(r'(?i)^(entrypoint|[vtmb]point\d*|gpoint\d+|smokepoint\d*|mpoint\d*)$')
WOODS = [f'ph_wood{k:02d}_hd' for k in range(1, 11)]               # ph_textures.csv 50-59: the house's wood (supports)


def tag(names):
    """The choosable part a shape belongs to (its nearest tagged ancestor), or None."""
    for n in reversed([n.lower() for n in names]):
        m = re.match(r'^(roof|wall|door)(\d+)$', n)
        if m:
            return f'{m.group(1)}{int(m.group(2))}'
        m = re.match(r'^floorplane(\d+)$', n)
        if m:
            return f'floorp{int(m.group(1))}'
        m = re.match(r'^wallplane(\d+)$', n)
        if m:
            return f'wallp{int(m.group(1))}'
        m = re.match(r'^carpet(\d+)$', n)
        if m:
            return f'carpet{int(m.group(1))}'
        if n in ('porch', 'tent', 'shields', 'banners'):
            return n
        if n == 'floors':
            return 'floorp0'
        if n == 'walls':
            return 'wallp0'
    return None


def nif_bytes(files, name):
    """A NIF from phousing/nifs (or items/): <name>.nif, or the one inside <name>.npk (an MPAK)."""
    p = files.get(name.lower() + '.nif')
    if p is not None:
        return p.read_bytes()
    p = files.get(name.lower() + '.npk')
    if p is None:
        return None
    return next((v for k, v in read_mpk(str(p)).items() if k.endswith('.nif')), None)


def points(raw):
    """{name: [x, y, z]} of the NIF's named points, Godot axes and metres in the model's frame."""
    out = {}
    nif = read_nif(raw)

    def walk(b, pm):
        if b is None:
            return
        m = nif_static.local_matrix(b) @ pm
        nm = b.get('name') or ''
        if POINT.match(nm):
            p = nif_static.DAOC_TO_GODOT @ m[3, :3] * nif_static.UNITS_TO_METRES
            out[nm.lower()] = [round(float(v), 4) for v in p]
        for c in (b.get('children') or []):
            walk(c, m)

    for r in nif.roots:
        walk(r, np.identity(4))
    return out


def hookpoints():
    """{house model: {hookpoint id: [x, y, z, heading]}} - HouseHookpointOffset (DAoC units from the house; the interior
    is never turned: x east, y south, z up) in the interior's frame (Godot axes, metres)."""
    if not DB.exists():
        print('no server database at', DB, '- no hookpoints')
        return {}
    con = sqlite3.connect(f'file:{DB.as_posix()}?mode=ro', uri=True)
    out = {}
    for model, hid, x, y, z, heading in con.execute('select HouseModel, HookpointID, X, Y, Z, Heading from HouseHookpointOffset'):
        out.setdefault(str(model), {})[str(hid)] = [round(x * 0.025, 4), round(z * 0.025, 4), round(y * 0.025, 4), int(heading)]
    con.close()
    return out


def housing_object_models():
    """Every object model a housing item can show (the server's housing goods: Object_Type 49-71, deeds' kin)."""
    if not DB.exists():
        return set()
    con = sqlite3.connect(f'file:{DB.as_posix()}?mode=ro', uri=True)
    ms = {r[0] for r in con.execute("select distinct Model from ItemTemplate where (Object_Type between 49 and 71 "
                                    "or Id_nb like 'housing%') and Model > 0")}
    con.close()
    return ms


def main():
    files = {p.name.lower(): p for p in (CLIENT / 'phousing/nifs').iterdir()}
    item_files = {p.name.lower(): p for p in (CLIENT / 'items').iterdir()}
    ph = read_mpk(str(CLIENT / 'phousing/phousing.mpk'))
    rows = [r for r in csv.reader(io.StringIO(ph['ph_houses.csv'].decode('latin1'))) if r and r[0].strip().isdigit()]
    g = read_mpk(str(CLIENT / 'gamedata.mpk'))
    objects = {r[0]: r for r in csv.reader(io.StringIO(g['objects.csv'].decode('latin1'))) if r and r[0].isdigit()}
    items = {r[0]: r for r in csv.reader(io.StringIO(g['items.csv'].decode('latin1'))) if r and r[0].isdigit()}
    mdir = OUT / 'models'
    mdir.mkdir(parents=True, exist_ok=True)
    (ROOT / 'godot/content/.gdignore').touch()
    tex, missing = set(WOODS), []
    out = {'houses': {}, 'interiors': {}, 'objects': {}, 'woods': WOODS}

    def convert(nif_name, prefix='', raw=None, tagged=False):
        raw = raw if raw is not None else nif_bytes(files, nif_name)
        if raw is None:
            missing.append(nif_name + ' (no NIF)')
            return None
        base = prefix + nif_name.lower()
        nif_static.GROUP_TAG = tag if tagged else None
        try:
            info = nif_static.convert(raw, str(mdir / f'{base}.gltf'), '../textures/original')
        except Exception as e:                             # (a few old item NIFs are not read)
            missing.append(f'{nif_name} ({type(e).__name__}: {e})')
            return None
        finally:
            nif_static.GROUP_TAG = None
        tex.update(info['textures'])
        print(f'{base}: {info["triangles"]} triangles, {info["collision_triangles"]} collision, {info["doors"]} door leaves')
        return f'models/{base}.gltf'

    for r in rows:
        model, desc, ext = int(r[0]), r[1].strip(), r[2].strip()
        interior = r[3].strip() if len(r) > 3 else ''
        if not ext:
            continue                                       # the table's first line (its row count)
        raw = nif_bytes(files, ext)
        f = convert(ext, raw=raw, tagged=True)
        if not f:
            continue
        pts = points(raw)
        out['houses'][str(model)] = {'name': desc, 'file': f, 'interior': interior.lower(),
                                     'garden': {k[6:]: v for k, v in pts.items() if k.startswith('gpoint')},
                                     'points': {k: v for k, v in pts.items() if not k.startswith('gpoint')}}
        if interior:
            iraw = nif_bytes(files, interior)
            fi = convert(interior, raw=iraw, tagged=True)
            if fi:
                out['interiors'][str(model)] = {'file': fi, 'points': points(iraw)}
    for model, hps in hookpoints().items():
        if model in out['interiors']:
            out['interiors'][model]['hookpoints'] = hps
    wanted = set(LOT_OBJECTS) | housing_object_models()
    print(len(wanted), 'housing object models')
    done = {}
    for m in sorted(wanted):
        o = objects.get(str(m))
        if o is None:
            missing.append(f'object {m} (no objects.csv row)')
            continue
        num = o[36].strip() if len(o) > 36 and o[36].strip() not in ('', '0') else o[2].strip()
        it = items.get(num)
        if it is None:
            missing.append(f'object {m} (no items.csv row {num})')
            continue
        nif = it[2].strip()
        if nif.lower() not in done:
            raw = nif_bytes(files, nif) or nif_bytes(item_files, nif)
            done[nif.lower()] = convert(nif, 'obj_', raw=raw) if raw is not None else None
            if raw is None:
                missing.append(f'object {m} ({nif} not in phousing/nifs or items)')
        if done[nif.lower()]:
            out['objects'][str(m)] = {'name': o[1].strip(), 'file': done[nif.lower()]}
    idx = TextureIndex()
    odir = OUT / 'textures/original'
    odir.mkdir(parents=True, exist_ok=True)
    for n in sorted(tex):
        doubled = n.endswith(('__d2', '__x2'))
        img = idx.image(n[:-4] if doubled else n) or nif_static.EMBEDDED.get(n[:-4] if doubled else n)
        if img is None and n.startswith('ph_woodxx'):
            img = idx.image('ph_wood01_hd')            # the wood placeholder: the client swaps in the house's wood
        if img is None:
            missing.append('texture ' + n)
            continue
        if doubled and n.endswith('__d2'):
            img = Image.fromarray(np.clip(np.asarray(img.convert('RGB'), np.float32) * 2.0, 0, 255).astype(np.uint8))
        save_if_changed(img, odir / f'{n}.png')
    out['missing'] = missing
    (OUT / 'housing.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(len(out['houses']), 'houses,', len(out['interiors']), 'interiors,', len(out['objects']), 'objects,', len(tex),
          'textures; missing:', missing)


if __name__ == '__main__':
    main()
