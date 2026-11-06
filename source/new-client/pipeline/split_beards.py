"""Splits the beards off the male hair styles so a beard can be worn with any hair style.

The Catacombs hair meshes carry their beard (and moustache, sideburns) as part of the style: hair_1 is a scalp plus a
full beard, hair_4 the same scalp without. The beard pieces are separate connected pieces of the mesh (no bone of their
own - the Beard bones carry no weight): every welded piece whose middle sits below the eyes and in front of the ears
is beard. Each style with one gets a 'beard_N' node (same skin, attributes and morph targets - fx_ face shapes, the
helm morphs - with just the beard's triangles) and its own node keeps the rest.

figure.json: 'beards' [{node, label, style}] (style: the hair style whose textures and colours it wears), and each
hair style's 'beard' (1-based index into beards, 0 none: the look it had). Run after face_morphs/skin_layers.

    python split_beards.py <race folder> [--dry]
"""
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from face_morphs import G, weld, build  # noqa: E402


def pieces(T, grp):
    """Connected piece of each triangle (welded by position)."""
    parent = np.arange(grp.max() + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for t in grp[T]:
        r = [find(int(i)) for i in t]
        for x in r[1:]:
            parent[find(x)] = find(r[0])
    return np.array([find(int(grp[t[0]])) for t in T])


def classify(P, Q, T, eye, H, chin):
    """Beard triangles (bool per triangle) of a hair mesh Q/T over the head P. A piece that sits mostly on the skin
    below the cheeks, or whose middle is below the eyes and at the face, is beard whole; a piece with both (hair to
    the chin, a dwarf's beard grown into the sideburns) is cut: what lies on the mouth and chin, and what hangs in
    front below the chin."""
    C = Q[T].mean(1)
    d = np.zeros(len(C))
    ii = np.zeros(len(C), np.int64)
    for s0 in range(0, len(C), 256):                    # the nearest head point (no scipy on the build machine)
        dd = np.linalg.norm(C[s0:s0 + 256, None, :] - P[None], axis=2)
        ii[s0:s0 + 256] = dd.argmin(1)
        d[s0:s0 + 256] = dd.min(1)
    S = (P[ii] - eye) / H
    rel = (C - eye) / H
    cz, cy = (chin[2] - eye[2]) / H, (chin[1] - eye[1]) / H
    zone = (d < 0.09 * H) & (S[:, 2] < -0.13) & (S[:, 1] < 0.16)
    core = (d < 0.09 * H) & (S[:, 2] < -0.13) & (S[:, 1] < 0.05) & (np.abs(S[:, 0]) < 0.3)
    hang = (rel[:, 2] < cz - 0.03) & (rel[:, 1] < cy + 0.2) & (np.abs(rel[:, 0]) < 0.22)
    comp = pieces(T, weld(Q))
    out = np.zeros(len(T), bool)
    info = []
    for c in np.unique(comp):
        m = comp == c
        r = rel[m].mean(0)
        if zone[m].mean() > 0.6 or (r[2] < -0.12 and r[1] < 0.12):
            out[m] = True
            kind = 'beard'
        elif core[m].mean() > 0.04:
            out[m] = core[m] | hang[m]
            kind = 'cut %d' % out[m].sum()
        else:
            kind = 'hair'
        info.append((int(m.sum()), np.round(r, 2).tolist(), kind))
    return out, info


def colour_rgb(folder, meta):
    """Each hair colour's average colour ('rgb': texture x tint), for the beard to take the colour nearest the hair's
    - the styles' colour lists are not alike everywhere (a dwarf's braided styles start from another blonde)."""
    import cv2
    tex_dir = folder.parent.parent / 'fig3_textures' / 'x4plus'
    seen = {}
    for st in meta.get('hair_styles', []):
        for c in st.get('colours', []):
            t = c['tex'].lower()
            if t not in seen:
                img = None
                for d in (tex_dir, tex_dir.parent / 'original'):
                    if (d / (t + '.png')).exists():
                        img = cv2.imread(str(d / (t + '.png')), cv2.IMREAD_UNCHANGED)
                        break
                if img is not None:
                    img = cv2.resize(img, (128, 128), interpolation=cv2.INTER_AREA)
                    a = img[..., 3] > 128 if img.ndim == 3 and img.shape[2] == 4 else np.ones(img.shape[:2], bool)
                    seen[t] = img[..., :3][a].astype(np.float64).mean(0)[::-1] / 255.0 if a.any() else None
                else:
                    seen[t] = None
            if seen[t] is not None:
                c['rgb'] = [round(float(x), 3) for x in seen[t] * np.array(c.get('tint', [1, 1, 1]))]


def run(folder, dry=False):
    folder = Path(folder)
    src = folder / 'figure.gltf'
    meta_path = folder / 'figure.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    if not str(meta.get('prefix', '')).endswith('_m'):
        colour_rgb(folder, meta)                      # (every race's colours measured: the creator's own hair colour)
        meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
        print('not male: colours measured', folder.name)
        return
    if meta.get('beards'):
        colour_rgb(folder, meta)
        meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
        print('already split', folder.name, '(colours measured)')
        return
    g = G(src)
    head = next(n for n in g.g['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    prim = g.g['meshes'][head['mesh']]['primitives'][0]
    P = g.acc(prim['attributes']['POSITION']).astype(np.float64)
    N = g.acc(prim['attributes']['NORMAL']).astype(np.float64)
    T = g.acc(prim['indices']).astype(np.int64).reshape(-1, 3)
    names = g.g['meshes'][head['mesh']].get('extras', {}).get('targetNames', [])
    fm = [g.acc(t['POSITION']).astype(np.float64) for t, nm in zip(prim['targets'], names) if not nm.startswith('fx_')][:8]
    _, marks = build(P, N, T, fm)
    eye = (marks['eyeL'] + marks['eyeR']) / 2
    H = marks['H']
    nodes = {n.get('name'): n for n in g.g['nodes']}
    beards = []
    seen = {}
    for si, st in enumerate(meta.get('hair_styles', [])):
        st['beard'] = 0
        name = st.get('node')
        if not name or name not in nodes:
            continue
        hn = nodes[name]
        hm = g.g['meshes'][hn['mesh']]
        if len(hm['primitives']) != 1:
            print(name, 'several primitives: left whole')
            continue
        hp = hm['primitives'][0]
        Q = g.acc(hp['attributes']['POSITION']).astype(np.float64)
        Th = g.acc(hp['indices']).astype(np.int64).reshape(-1, 3)
        is_b, info = classify(P, Q, Th, eye, H, marks['chin'])
        print('%-8s %s' % (name, info))
        if is_b.sum() < 12:
            continue
        if is_b.all():                            # a beard and no hair: the node becomes the beard, the style bald
            if dry:
                continue
            nb = 'beard_%d' % (len(beards) + 1)
            hh = meta.get('helm_hair', {})
            if name in hh:
                hh[nb] = hh.pop(name)
            hn['name'] = nb
            hm['name'] = nb
            beards.append({'node': nb, 'label': 'Beard %d' % (len(beards) + 1), 'style': si})
            st['node'] = None
            st['beard'] = len(beards)
            continue
        # the same beard on two styles (some races repeat a mesh): one entry
        key = (round(float(Q[Th[is_b]].mean()), 4), int(is_b.sum()))
        if key in seen:
            st['beard'] = seen[key]
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
        hp['indices'] = add_idx(Th[~is_b])
        if key in seen:
            continue                              # this style's copy dropped, the first one's node serves
        bm = json.loads(json.dumps(hm))
        bm['name'] = 'beard_%d' % (len(beards) + 1)
        bm['primitives'][0]['indices'] = add_idx(Th[is_b])
        g.g['meshes'].append(bm)
        bn = {k: v for k, v in hn.items() if k not in ('children', 'name', 'mesh')}
        bn['name'] = bm['name']
        bn['mesh'] = len(g.g['meshes']) - 1
        g.g['nodes'].append(bn)
        parent = next((n for n in g.g['nodes'] if g.g['nodes'].index(hn) in n.get('children', [])), None)
        if parent is not None:
            parent['children'].append(len(g.g['nodes']) - 1)
        else:
            for sc in g.g.get('scenes', []):
                sc['nodes'].append(len(g.g['nodes']) - 1)
        beards.append({'node': bm['name'], 'label': 'Beard %d' % (len(beards) + 1), 'style': si})
        seen[key] = len(beards)
        st['beard'] = len(beards)
        hh = meta.get('helm_hair', {})
        if name in hh:
            hh[bm['name']] = hh[name]
    print('beards', [(b['node'], meta['hair_styles'][b['style']]['node']) for b in beards])
    if dry or not beards:
        return
    g.save(src)
    meta['beards'] = beards
    colour_rgb(folder, meta)
    meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print('wrote', src)


if __name__ == '__main__':
    run(sys.argv[1], '--dry' in sys.argv)
