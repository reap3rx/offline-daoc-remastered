"""More face sliders for the classic head (owner 2026-11-25: "even on the heads that have the classic head shape ... add
sliders ... that might give more customization"): the head's own shape, the brow's angle, a muzzle for the beast races,
the nostrils, hollow cheeks and jowls. fx_<key> targets on the classic head, as pipeline/face_morphs.py's, found from
the same landmarks; the hair, beards and helms near the head take the same moves (sparse targets, fading off the skin).
Runs on a built figure (after face_morphs and the rest); figure.json face_shapes gains the new sliders.

    python face_extra.py <race folder> [<out folder>]
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))
import face_morphs as fm
from face_morphs import G, weld, vertex_normals, open_edge_mask, gauss, smooth
fm.NC.setdefault('MAT4', 16)

EXTRA = [
    ('head_width', 'Head Width'), ('head_length', 'Head Length'), ('crown', 'Crown Height'), ('temples', 'Temples'),
    ('forehead', 'Forehead'), ('brow_angle', 'Brow Angle'), ('muzzle', 'Muzzle'), ('muzzle_width', 'Muzzle Width'),
    ('nostrils', 'Nostrils'), ('cheek_hollow', 'Cheek Hollows'), ('jowls', 'Jowls'),
]
SKIP = ('head', 'body', 'lbody', 'legs', 'boots', 'arms', 'gloves', 'cloak')
GAIN = 1.5                     # (owner: as close to the line as is sensible - at 1.0 they barely read)


def fields(P, N, T, fmorph, scale):
    D0, marks = fm.build(P, N, T, fmorph, scale)
    grp = weld(P)
    H, hw = marks['H'], marks['hw']
    eyeL, eyeR, nose, mouth, chin = marks['eyeL'], marks['eyeR'], marks['nose_tip'], marks['mouth'], marks['chin']
    em = (eyeL + eyeR) / 2
    E = abs(eyeR[0] - eyeL[0])
    s = H / 10.0 * scale
    w = marks['_w']
    lips = np.clip(w['lips'] * 2.5, 0, 1)
    keep = 1 - lips
    Nn = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    edge = open_edge_mask(P, T, grp, 0.12 * H)
    cx = em[0]
    front = w['front']
    z = np.zeros_like(P)
    D = {}
    # the skull: from the mouth up, more the higher
    up = np.clip((P[:, 2] - mouth[2]) / (0.3 * H), 0, 1)
    d = z.copy(); d[:, 0] = (P[:, 0] - cx) * 0.11 * up; D['head_width'] = d
    yc = em[1] + 0.25 * H
    back = np.clip((P[:, 1] - em[1]) / (0.35 * H), 0, 1) * np.clip((P[:, 2] - (mouth[2] - 0.05 * H)) / (0.2 * H), 0, 1)
    d = z.copy(); d[:, 1] = (P[:, 1] - yc) * 0.14 * back; D['head_length'] = d
    brow_z = em[2] + 0.09 * H
    top = np.clip((P[:, 2] - brow_z) / (0.3 * H), 0, 1)
    d = z.copy(); d[:, 2] = (P[:, 2] - brow_z) * 0.14 * top; D['crown'] = d
    side = np.sign(P[:, 0] - cx)
    tc = np.stack([cx + side * 0.86 * hw, np.full(len(P), em[1] + 0.12 * H), np.full(len(P), em[2] + 0.1 * H)], 1)
    wt = np.exp(-((P - tc) ** 2).sum(1) / (2 * (0.11 * H) ** 2))
    d = z.copy(); d[:, 0] = side * 0.14 * s * wt; D['temples'] = d
    wf = np.clip((em[1] + 0.1 * H - P[:, 1]) / (0.1 * H), 0, 1) * np.exp(-((P[:, 2] - (brow_z + 0.14 * H)) / (0.1 * H)) ** 2) \
        * np.clip((0.75 * hw - np.abs(P[:, 0] - cx)) / (0.3 * hw), 0, 1)
    d = z.copy(); d[:, 1] = -0.16 * s * wf; d[:, 2] = 0.03 * s * wf; D['forehead'] = d
    # brow angle: the brow's outer ends up (+) or down
    out = np.clip((np.abs(P[:, 0] - cx) - 0.35 * E) / (0.6 * E), -0.6, 1.0)
    wb = np.exp(-((P[:, 2] - brow_z) / (0.07 * H)) ** 2) * np.clip((np.abs(eyeR[0] - cx) + 0.7 * E - np.abs(P[:, 0] - cx)) / (0.3 * E), 0, 1) \
        * front * (1 - np.clip(w['eye'] * 1.5, 0, 1) * 0.7)
    d = z.copy(); d[:, 2] = 0.12 * s * wb * out; D['brow_angle'] = d
    # the muzzle: the lower face - nose, lips, chin - forward together (the beasts' snouts; a flatter face at -)
    wm = front * np.clip((nose[2] + 0.06 * H - P[:, 2]) / (0.1 * H), 0, 1) * np.clip((P[:, 2] - (chin[2] - 0.06 * H)) / (0.08 * H), 0, 1) \
        * np.clip((0.6 * hw - np.abs(P[:, 0] - cx)) / (0.35 * hw), 0, 1)
    wm = np.clip(smooth(wm, T, grp, 3), 0, 1)
    d = z.copy(); d[:, 1] = -0.22 * s * wm; D['muzzle'] = d
    d = z.copy(); d[:, 0] = (P[:, 0] - cx) * 0.28 * wm; D['muzzle_width'] = d
    # the nostrils: the nose's lower half wider
    wn = w['nose'] * np.clip((nose[2] + 0.02 * H - P[:, 2]) / (0.04 * H), 0, 1)
    d = z.copy(); d[:, 0] = (P[:, 0] - nose[0]) * 0.4 * wn; D['nostrils'] = d
    # hollow cheeks: under the cheekbones, in along the skin
    hc = np.stack([cx + side * (np.abs(eyeR[0] - cx) + 0.2 * E), np.full(len(P), em[1] + 0.02 * H), np.full(len(P), mouth[2] + 0.1 * H)], 1)
    wh = np.exp(-((P - hc) ** 2).sum(1) / (2 * (0.08 * H) ** 2)) * front * (1 - w['nose'])
    D['cheek_hollow'] = -Nn * (0.18 * s * wh)[:, None]
    # jowls: the lower jaw's sides heavier - down and out
    jc = np.stack([cx + side * 0.62 * hw, np.full(len(P), em[1] + 0.12 * H), np.full(len(P), chin[2] + 0.06 * H)], 1)
    wj = np.exp(-((P - jc) ** 2).sum(1) / (2 * (0.1 * H) ** 2))
    d = z.copy(); d[:, 0] = side * 0.08 * s * wj; d[:, 2] = -0.1 * s * wj; d[:, 1] = -0.03 * s * wj; D['jowls'] = d
    for k in D:
        m = edge * (1.0 if k == 'muzzle' or k == 'muzzle_width' else keep)
        dk = D[k] * m[:, None] * fm.STRENGTH * GAIN
        g_ = np.zeros((grp.max() + 1, 3)); c_ = np.zeros(grp.max() + 1)
        np.add.at(g_, grp, dk); np.add.at(c_, grp, 1)
        D[k] = (g_ / np.maximum(c_, 1)[:, None])[grp]
    return D, H


def _sparse_one(g, idx, vals, count):
    idx = np.ascontiguousarray(idx, np.uint32); vals = np.ascontiguousarray(vals, np.float32)
    data = idx.tobytes() + vals.tobytes()
    g.g['buffers'].append({'byteLength': len(data)}); g.b.append(bytearray(data))
    bi = len(g.b) - 1
    g.g['bufferViews'].append({'buffer': bi, 'byteOffset': 0, 'byteLength': idx.nbytes}); iv = len(g.g['bufferViews']) - 1
    g.g['bufferViews'].append({'buffer': bi, 'byteOffset': idx.nbytes, 'byteLength': vals.nbytes}); vv = len(g.g['bufferViews']) - 1
    g.g['accessors'].append({'componentType': 5126, 'count': int(count), 'type': 'VEC3',
                             'min': np.minimum(vals.min(0), 0).tolist(), 'max': np.maximum(vals.max(0), 0).tolist(),
                             'sparse': {'count': int(len(idx)), 'indices': {'bufferView': iv, 'componentType': 5125},
                                        'values': {'bufferView': vv}}})
    return len(g.g['accessors']) - 1


def add_target(g, d, n=None, eps=1e-4):
    mv = np.flatnonzero(np.abs(d).max(1) > eps)
    if len(mv) == 0:
        mv = np.array([0])
    pa = _sparse_one(g, mv, d[mv], len(d))
    if n is None:
        na = _sparse_one(g, np.array([0]), np.zeros((1, 3)), len(d))
    else:
        mn = np.flatnonzero(np.abs(n).max(1) > eps) if (np.abs(n) > eps).any() else np.array([0])
        na = _sparse_one(g, mn, n[mn], len(d))
    return pa, na


def run(folder, out=None):
    folder = Path(folder); out = Path(out or folder)
    scale = fm.RACE_SCALE.get(folder.name[:3], 1.0)
    g = G(folder / 'figure.gltf')
    node = next(n for n in g.g['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    mesh = g.g['meshes'][node['mesh']]
    names = list(mesh.get('extras', {}).get('targetNames', []))
    if any(n == 'fx_' + EXTRA[0][0] for n in names):
        print(folder.name, 'already has the extra face sliders'); return
    prim = mesh['primitives'][0]
    P = g.acc(prim['attributes']['POSITION']).astype(np.float64)
    N = g.acc(prim['attributes']['NORMAL']).astype(np.float64)
    T = g.acc(prim['indices']).astype(np.int64).reshape(-1, 3)
    fmorph = [g.acc(t['POSITION']).astype(np.float64) for t in prim.get('targets', [])[:8]]
    D, H = fields(P, N, T, fmorph, scale)
    grp = weld(P); n0 = vertex_normals(P, T, grp)
    for k, _ in EXTRA:
        pa, na = add_target(g, D[k], vertex_normals(P + D[k], T, grp) - n0)
        prim['targets'].append({'POSITION': pa, 'NORMAL': na})
    mesh['extras']['targetNames'] = names + ['fx_' + k for k, _ in EXTRA]
    if 'weights' in mesh:
        mesh['weights'] = mesh['weights'] + [0.0] * len(EXTRA)
    # the hair, beards, helms (everything worn on the head): each point as the skin nearest it, fading off the skin
    tree = cKDTree(P)
    reach = 0.18 * H
    lo, hi = P.min(0) - reach, P.max(0) + reach
    carried = 0
    for n in g.g['nodes']:
        nm = n.get('name', '')
        if 'mesh' not in n or nm.split('__')[0].split('_v')[0] in SKIP or nm.startswith(('head', 'cloak')):
            continue
        hm = g.g['meshes'][n['mesh']]
        if len(hm['primitives']) != 1:
            continue
        p2 = hm['primitives'][0]
        Q = g.acc(p2['attributes']['POSITION']).astype(np.float64)
        if not np.all((Q > lo) & (Q < hi), axis=1).any():
            continue
        hn = list(hm.get('extras', {}).get('targetNames', []))
        if len(p2.get('targets', [])) != len(hn):
            continue
        dist, j = tree.query(Q, k=4)
        wgt = 1.0 / np.maximum(dist, 1e-4); wgt /= wgt.sum(1, keepdims=True)
        fall = np.clip(1.0 - (dist.min(1) - 0.01 * H) / reach, 0, 1)
        new = []
        for k, _ in EXTRA:
            dq = (D[k][j] * wgt[..., None]).sum(1) * fall[:, None]
            pa, na = add_target(g, dq, None, eps=0.002)
            p2.setdefault('targets', []).append({'POSITION': pa, 'NORMAL': na})
            new.append('fx_' + k)
        hm.setdefault('extras', {})['targetNames'] = hn + new
        if 'weights' in hm or hn:
            hm['weights'] = list(hm.get('weights', [0.0] * len(hn))) + [0.0] * len(new)
        carried += 1
    out.mkdir(parents=True, exist_ok=True)
    g.save(out / 'figure.gltf')
    meta = json.loads((folder / 'figure.json').read_text(encoding='utf-8'))
    fs = [x for x in meta.get('face_shapes', []) if x[0] not in dict(EXTRA)]
    meta['face_shapes'] = fs + [[k, lab] for k, lab in EXTRA]
    (out / 'figure.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print('%s: %d extra face sliders, %d hair / helm meshes follow them' % (folder.name, len(EXTRA), carried))


# ---- the beast races' own (the character creator plan, phase 5 - owner 2026-11-26): the Valkyn's tusks (its lower
# teeth, grown from their roots - the Troll's and Kobold's teeth sit behind closed lips, so they have none to grow) and
# the Sylvan's crest (the leaves standing off the skull, longer or shorter). The rest of phase 5 - muzzle, its width,
# head width, brow ridge, ear angle - the beast races already have (face_morphs, and the extra sliders above).
BEAST = {'val': ['tusks'], 'syl': ['crest']}
BEAST_LABELS = {'tusks': 'Tusk Size', 'crest': 'Crest'}


def beast_fields(P, T, keys):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    grp = weld(P); ng = grp.max() + 1; Tg = grp[T]
    A = coo_matrix((np.ones(len(Tg) * 3), (Tg.ravel(), np.roll(Tg, 1, 1).ravel())), shape=(ng, ng))
    _, lab = connected_components(A, directed=False)
    lab = lab[grp]
    sizes = np.bincount(lab)
    skin = np.argmax(sizes)
    H = float(np.ptp(P[lab == skin][:, 2]))
    D = {}
    if 'tusks' in keys:
        # the teeth: the small pieces in the middle (x ~ 0); the eyes are the pair off to the sides
        small = [i for i in range(len(sizes)) if i != skin and abs(P[lab == i][:, 0].mean()) < 0.05 * H]
        d = np.zeros_like(P)
        if small:
            low = min(small, key=lambda i: P[lab == i][:, 2].mean())
            m = lab == low
            Q = P[m]
            base = np.array([Q[:, 0].mean(), Q[:, 1].mean(), np.percentile(Q[:, 2], 10)])
            # grown up and out from the gum line: the points above it most (the tusks' tips)
            k = np.clip((Q[:, 2] - base[2]) / max(np.ptp(Q[:, 2]), 1e-6), 0, 1)
            dd = (Q - base) * 0.8
            dd[:, 2] *= 1.0 + 0.6 * k
            d[m] = dd * (0.4 + 0.6 * k)[:, None]
        D['tusks'] = d
    if 'crest' in keys:
        Ps = P[lab == skin]
        top = Ps[Ps[:, 2] > np.percentile(Ps[:, 2], 40)]
        A_ = np.c_[2 * top, np.ones(len(top))]
        s_, *_ = np.linalg.lstsq(A_, (top * top).sum(1), rcond=None)
        c = s_[:3]; R = float(np.sqrt(s_[3] + c @ c))
        r = np.linalg.norm(P - c, axis=1)
        w = np.clip((r - 1.02 * R) / (0.12 * R), 0, 1) * (lab == skin) * (P[:, 2] > c[2] - 0.2 * R)
        D["crest"] = (P - c) * (0.7 * w * (r - R) / np.maximum(r, 1e-6))[:, None]
    return D


def run_beast(folder, out=None):
    folder = Path(folder); out = Path(out or folder)
    keys = BEAST.get(folder.name[:3])
    if not keys:                                        # (not a beast race: nothing to add)
        return
    g = G(folder / 'figure.gltf')
    node = next(n for n in g.g['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    mesh = g.g['meshes'][node['mesh']]
    names = list(mesh.get('extras', {}).get('targetNames', []))
    if any(n == 'fx_' + keys[0] for n in names):
        print(folder.name, 'already has its beast sliders'); return
    prim = mesh['primitives'][0]
    P = g.acc(prim['attributes']['POSITION']).astype(np.float64)
    T = g.acc(prim['indices']).astype(np.int64).reshape(-1, 3)
    D = beast_fields(P, T, keys)
    grp = weld(P); n0 = vertex_normals(P, T, grp)
    for k in keys:
        pa, na = add_target(g, D[k], vertex_normals(P + D[k], T, grp) - n0)
        prim['targets'].append({'POSITION': pa, 'NORMAL': na})
    mesh['extras']['targetNames'] = names + ['fx_' + k for k in keys]
    if 'weights' in mesh:
        mesh['weights'] = mesh['weights'] + [0.0] * len(keys)
    out.mkdir(parents=True, exist_ok=True)
    g.save(out / 'figure.gltf')
    meta = json.loads((folder / 'figure.json').read_text(encoding='utf-8'))
    fs = [x for x in meta.get('face_shapes', []) if x[0] not in keys]
    meta['face_shapes'] = fs + [[k, BEAST_LABELS[k]] for k in keys]
    (out / 'figure.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print('%s: beast sliders %s (moves up to %s)' % (folder.name, ', '.join(keys),
          ', '.join('%.2f' % np.linalg.norm(D[k], axis=1).max() for k in keys)))


if __name__ == '__main__':
    if sys.argv[1] == '--beast':
        run_beast(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
