"""Camping, soulbind stones and treasure chests (owner 2026-11-11): the models the server's new world objects show,
gathered into godot/content/camping so NifScene can load them (its textures beside it, as the effects keep theirs).

  campfire.gltf / effect_campfire_sfx.gltf   the zones' stone ring and its burning logs (fire, smoke, embers)
  valcampfire.gltf                           Midgard's ringed fire pit (the better camps)
Each glTF's images are pointed at textures/original (and x4plus when the zones have an upscaled copy). Run from
source/new-client:  python pipeline/build_camping.py <path to new-client/godot>
"""
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# the godot folder with the built content (an argument, else new-client/godot beside this pipeline)
GODOT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'godot'
ZONES = GODOT / 'content' / 'zones'
OUT = GODOT / 'content' / 'camping'

MODELS = ['campfire.gltf', 'effect_campfire_sfx.gltf', 'valcampfire.gltf']


def find_model(name):
    for z in sorted(ZONES.glob('zone*')):
        p = z / 'models' / name
        if p.exists():
            return p
    return None


def textures_of(doc):
    names = set()
    for im in doc.get('images', []):
        names.add(Path(im['uri']).stem)
    ex = doc.get('extras', {})
    for m in ex.get('nif_materials', []):
        for slot in (m.get('slots') or {}).values():
            if isinstance(slot, dict) and slot.get('tex'):
                names.add(slot['tex'])
    for p in ex.get('nif_particles', []):
        if p.get('texture'):
            names.add(p['texture'])
    return names


def find_texture(zone_dir, name, kind):
    for d in [zone_dir] + sorted(ZONES.glob('zone*')):
        for ext in ('.png', '.bc'):
            p = d / 'textures' / kind / (name + ext)
            if p.exists():
                yield p
        if any((d / 'textures' / kind).glob(name + '.*')):
            return


def main():
    (OUT / 'textures' / 'original').mkdir(parents=True, exist_ok=True)
    (OUT / 'textures' / 'x4plus').mkdir(parents=True, exist_ok=True)
    missing = []
    for name in MODELS:
        src = find_model(name)
        if src is None:
            missing.append(name)
            continue
        doc = json.loads(src.read_text(encoding='utf-8'))
        for im in doc.get('images', []):
            im['uri'] = 'textures/original/' + Path(im['uri']).name
        for buf in doc.get('buffers', []):
            uri = buf.get('uri', '')
            if uri and not uri.startswith('data:'):
                shutil.copy2(src.parent / uri, OUT / Path(uri).name)
                buf['uri'] = Path(uri).name
        (OUT / name).write_text(json.dumps(doc), encoding='utf-8')
        zone_dir = src.parent.parent
        for tex in textures_of(doc):
            found = False
            for kind in ('original', 'x4plus'):
                for p in find_texture(zone_dir, tex, kind):
                    shutil.copy2(p, OUT / 'textures' / kind / p.name)
                    found = True
            if not found:
                missing.append(tex)
        print('camping:', name, 'from', src.parent.parent.name)
    if missing:
        print('missing:', ', '.join(sorted(set(missing))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
