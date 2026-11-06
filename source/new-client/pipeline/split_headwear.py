"""Splits the Saracens' turbans off their hair styles (owner 2026-11-06: "some hairstyles that are hoods or turbans
... Turban can be an option on some of the other hairstyles ... the turban itself will have to be textured
differently").

The Catacombs Saracen styles are cloth and hair in one mesh, one texture: the turbans (the 'hair01' textures: the
wrapped cloth and its knot, beside the hair that shows under it) and the hoods ('hair02': a cloth with a checked band).
Each turban style's cloth triangles - the light, cloth parts of its white texture - become a 'turban_N' node (same
skin, attributes and morphs); its own node keeps the hair. The hoods stay as they are and are marked, for the creator
to leave out.

figure.json: 'turbans' [{node, label, style, tex}] (tex: the white texture, drawn as cloth and dyed), each style's
'turban' (1-based, 0 none: the one it wore) and 'hood' (true for the hood styles).

    python split_headwear.py <race folder> [--dry]
"""
import json, sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent))
from face_morphs import G  # noqa: E402

KINDS = {'sar_m': {'turban': 'hair01', 'hood': 'hair02'}, 'sar_f': {'turban': 'hair01', 'hood': 'hair02'}}


def white_tex(folder, st):
    names = [c['tex'] for c in st.get('colours', [])]
    pick = next((n for n in names if n.lower().endswith('_white')), names[0] if names else None)
    if pick is None:
        return None, None
    p = folder.parent.parent / 'fig3_textures' / 'original' / (pick.lower() + '.png')
    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    return pick, img


def cloth_tris(UV, T, img):
    """Cloth triangles: those whose texture is light (the white cloth) - the hair is dark in every colour."""
    h, w = img.shape[:2]
    a = img[..., 3].astype(np.float32) / 255 if img.shape[2] == 4 else np.ones((h, w), np.float32)
    lum = img[..., :3].astype(np.float32).mean(2) / 255
    cloth = ((lum > 0.42) & (a > 0.5)).astype(np.float32)
    cloth = cv2.blur(cloth, (5, 5))
    pts = np.concatenate([UV[T], UV[T].mean(1, keepdims=True)], 1)       # three corners and the middle
    x = np.clip((pts[..., 0] % 1.0) * w, 0, w - 1).astype(int)
    y = np.clip((pts[..., 1] % 1.0) * h, 0, h - 1).astype(int)
    return cloth[y, x].mean(1) > 0.5


def run(folder, dry=False):
    folder = Path(folder)
    meta_path = folder / 'figure.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    kind = KINDS.get(str(meta.get('prefix', '')))
    if not kind or meta.get('turbans') is not None:
        print('no headwear (or done):', folder.name)
        return
    g = G(folder / 'figure.gltf')
    nodes = {n.get('name'): n for n in g.g['nodes']}
    turbans, seen = [], {}
    for si, st in enumerate(meta.get('hair_styles', [])):
        st['turban'] = 0
        name = st.get('node')
        texs = ' '.join(c['tex'].lower() for c in st.get('colours', []))
        if kind['hood'] in texs:
            st['hood'] = True
        if not name or name not in nodes or kind['turban'] not in texs:
            continue
        hn = nodes[name]
        hm = g.g['meshes'][hn['mesh']]
        hp = hm['primitives'][0]
        UV = g.acc(hp['attributes']['TEXCOORD_0']).astype(np.float64)
        Th = g.acc(hp['indices']).astype(np.int64).reshape(-1, 3)
        Q = g.acc(hp['attributes']['POSITION']).astype(np.float64)
        tex, img = white_tex(folder, st)
        if img is None:
            print(name, 'no texture')
            continue
        is_c = cloth_tris(UV, Th, img)
        print('%-8s %d of %d triangles cloth' % (name, is_c.sum(), len(Th)))
        if is_c.sum() < 12:
            continue
        key = (round(float(Q[Th[is_c]].mean()), 3), int(is_c.sum()))
        if dry:
            continue
        acc = g.g['accessors'][hp['indices']]
        ctype = acc['componentType']
        dt = np.uint32 if ctype == 5125 else np.uint16

        def add_idx(tris):
            data = np.ascontiguousarray(tris.reshape(-1).astype(dt)).tobytes()
            data += b'\0' * (-len(data) % 4)
            g.g['buffers'].append({'byteLength': len(data)})
            g.b.append(bytearray(data))
            g.g['bufferViews'].append({'buffer': len(g.b) - 1, 'byteOffset': 0, 'byteLength': len(data), 'target': 34963})
            g.g['accessors'].append({'bufferView': len(g.g['bufferViews']) - 1, 'componentType': ctype,
                                     'count': int(tris.size), 'type': 'SCALAR'})
            return len(g.g['accessors']) - 1
        if (~is_c).sum() >= 3:
            hp['indices'] = add_idx(Th[~is_c])
        else:
            st['node'] = None                          # (all cloth: no hair left under it)
        if key in seen:
            st['turban'] = seen[key]
            continue
        tm = json.loads(json.dumps(hm))
        tm['name'] = 'turban_%d' % (len(turbans) + 1)
        tm['primitives'][0]['indices'] = add_idx(Th[is_c])
        g.g['meshes'].append(tm)
        tn = {k: v for k, v in hn.items() if k not in ('children', 'name', 'mesh')}
        tn['name'] = tm['name']
        tn['mesh'] = len(g.g['meshes']) - 1
        g.g['nodes'].append(tn)
        hi = g.g['nodes'].index(hn)
        parent = next((n for n in g.g['nodes'] if hi in n.get('children', [])), None)
        if parent is not None:
            parent['children'].append(len(g.g['nodes']) - 1)
        else:
            for sc in g.g.get('scenes', []):
                sc['nodes'].append(len(g.g['nodes']) - 1)
        turbans.append({'node': tm['name'], 'label': 'Turban %d' % (len(turbans) + 1), 'style': si, 'tex': tex})
        seen[key] = len(turbans)
        st['turban'] = len(turbans)
    print('turbans', [(t['node'], meta['hair_styles'][t['style']]['label']) for t in turbans],
          'hoods', [s['label'] for s in meta['hair_styles'] if s.get('hood')])
    if dry:
        return
    if turbans:
        g.save(folder / 'figure.gltf')
    meta['turbans'] = turbans
    meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')


if __name__ == '__main__':
    run(sys.argv[1], '--dry' in sys.argv)
