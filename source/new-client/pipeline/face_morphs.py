"""Face shapes (claude 2026-11-06, owner: "how hard would it be to have more detailed facial customization so you're
not picking between the same 4 or 5 faces?"). For a race figure's head, a set of new morph targets ("fx_<name>"), each
one feature moved: the nose's width, length, height and bridge; the eyes' spacing, height, size and depth; the brow's
height and depth; the cheekbones; the mouth's width, height and lips; the jaw's width; the chin's length and point;
the ears' size. One target per slider, used from -1 to 1.

Where each feature is comes from the head's own Catacombs morphs (FM1/2 the eyes, FM3/4 the nose, FM5/6 the lips,
FM7/8 the jaw - drawn by the client's artists), the rest from landmarks found from those (the brow above the eyes,
the cheekbones beside the nose, the ears at the sides). Every move fades to nothing at the head's open edges (the
neck seam with the body) and is the same on every copy of a position (the texture seams), and the target's normals
follow the new shape. The skull and the hairline are not moved: the hair meshes sit on them.

    python face_morphs.py <figure.gltf> <out.gltf> [--scale=1.0]
"""
import base64, json, sys
from pathlib import Path
import numpy as np

COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

# name, label, range note (all -1 .. 1)
FEATURES = [
    ('nose_width', 'Nose Width'), ('nose_length', 'Nose Length'), ('nose_height', 'Nose Height'),
    ('nose_bridge', 'Nose Bridge'), ('eye_spacing', 'Eye Spacing'), ('eye_height', 'Eye Height'),
    ('eye_size', 'Eye Size'), ('eye_depth', 'Eye Depth'), ('brow_height', 'Brow Height'), ('brow_depth', 'Brow Ridge'),
    ('cheekbones', 'Cheekbones'), ('mouth_width', 'Mouth Width'), ('mouth_height', 'Mouth Height'),
    ('lips', 'Lip Fullness'), ('jaw_width', 'Jaw Width'), ('chin_length', 'Chin Length'), ('chin_point', 'Chin Point'),
    ('ear_size', 'Ear Size'),
]


def arg(k, d):
    return float(next((a.split('=')[1] for a in sys.argv if a.startswith(f'--{k}=')), d))


class G:
    def __init__(self, path):
        self.path = Path(path)
        self.g = json.loads(self.path.read_text(encoding='utf-8'))
        self.b = [bytearray(base64.b64decode(x['uri'].split(',', 1)[1])) for x in self.g['buffers']]

    def acc(self, i):
        a = self.g['accessors'][i]
        bv = self.g['bufferViews'][a['bufferView']]
        n = NC[a['type']]
        arr = np.frombuffer(bytes(self.b[bv['buffer']]), COMP[a['componentType']], a['count'] * n,
                            bv.get('byteOffset', 0) + a.get('byteOffset', 0))
        return arr.reshape(a['count'], n) if n > 1 else arr

    def add_vec3(self, arr):
        """A float VEC3 accessor of arr in a new buffer of its own; returns its index."""
        arr = np.ascontiguousarray(arr, np.float32)
        data = arr.tobytes()
        self.g['buffers'].append({'byteLength': len(data)})
        self.b.append(bytearray(data))
        self.g['bufferViews'].append({'buffer': len(self.b) - 1, 'byteOffset': 0, 'byteLength': len(data)})
        self.g['accessors'].append({'bufferView': len(self.g['bufferViews']) - 1, 'componentType': 5126,
                                    'count': len(arr), 'type': 'VEC3', 'min': arr.min(0).tolist(), 'max': arr.max(0).tolist()})
        return len(self.g['accessors']) - 1

    def save(self, out):
        for i, x in enumerate(self.g['buffers']):
            x['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(bytes(self.b[i])).decode()
            x['byteLength'] = len(self.b[i])
        Path(out).write_text(json.dumps(self.g), encoding='utf-8')


def weld(P):
    """Index of each vertex's position group (texture seams split vertices at one place)."""
    key = np.round(P * 1e4).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    return inv.reshape(-1)


def vertex_normals(P, T, grp):
    n = np.zeros_like(P)
    f = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], f)
    g = np.zeros((grp.max() + 1, 3))
    np.add.at(g, grp, n)
    n = g[grp]
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def smooth(w, T, grp, iters=3):
    """Spread a weight over the mesh's neighbours (by position group)."""
    ng = grp.max() + 1
    W = np.zeros(ng)
    np.maximum.at(W, grp, w)
    e = np.concatenate([grp[T[:, [0, 1]]], grp[T[:, [1, 2]]], grp[T[:, [2, 0]]]])
    for _ in range(iters):
        s = np.zeros(ng)
        c = np.zeros(ng)
        np.add.at(s, e[:, 0], W[e[:, 1]])
        np.add.at(c, e[:, 0], 1)
        np.add.at(s, e[:, 1], W[e[:, 0]])
        np.add.at(c, e[:, 1], 1)
        W = 0.5 * W + 0.5 * s / np.maximum(c, 1)
    return W[grp]


def open_edge_mask(P, T, grp, fade):
    """0 at the mesh's open edges (by position), 1 from 'fade' away."""
    e = np.sort(np.concatenate([grp[T[:, [0, 1]]], grp[T[:, [1, 2]]], grp[T[:, [2, 0]]]]), axis=1)
    u, c = np.unique(e, axis=0, return_counts=True)
    be = u[c == 1]
    if len(be) == 0:
        return np.ones(len(P))
    gp = np.zeros((grp.max() + 1, 3))
    gp[grp] = P
    # the border's loops; only the lowest (the neck seam) - the mouth's and eyes' own openings move with the face
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b2 in be:
        parent[find(a)] = find(b2)
    loops = {}
    for v in np.unique(be.reshape(-1)):
        loops.setdefault(find(v), []).append(v)
    low = min(loops.values(), key=lambda vs: gp[vs, 2].mean())
    zcut = gp[low, 2].max()
    border = np.array([v for vs in loops.values() for v in vs if gp[vs, 2].mean() <= zcut])
    bp = gp[border]
    d = np.full(len(P), np.inf)
    for s in range(0, len(bp), 256):
        d = np.minimum(d, np.linalg.norm(P[:, None, :] - bp[None, s:s + 256], axis=2).min(1))
    return np.clip(d / fade, 0, 1) ** 1.5


def gauss(P, c, r):
    return np.exp(-np.sum((P - c) ** 2, axis=1) / (2 * r * r))


def build(P, N, T, fm, scale=1.0):
    """The new targets' position deltas: {name: (n, 3)}. P: positions (z up, the face toward -y)."""
    grp = weld(P)
    lo, hi = P.min(0), P.max(0)
    H = hi[2] - lo[2]
    hw = max(-lo[0], hi[0])
    s = H / 10.0 * scale                                   # a feature's move: a tenth of the head, at full slider

    def region(a, b):
        w = np.linalg.norm(fm[a], axis=1) + np.linalg.norm(fm[b], axis=1)
        w = w / max(w.max(), 1e-9)
        return np.clip(smooth(np.clip(w * 1.6, 0, 1), T, grp, 3), 0, 1)

    w_eye, w_nose, w_lip, w_jaw = region(0, 1), region(2, 3), region(4, 5), region(6, 7)
    edge = open_edge_mask(P, T, grp, 0.12 * H)

    def centroid(w, sel=None):
        m = w if sel is None else w * sel
        return (P * m[:, None]).sum(0) / max(m.sum(), 1e-9)

    left, right = (P[:, 0] < 0).astype(float), (P[:, 0] > 0).astype(float)
    eyeL, eyeR = centroid(w_eye ** 2, left), centroid(w_eye ** 2, right)
    eye_mid = (eyeL + eyeR) / 2
    nose_tip = P[np.argmin(np.where(w_nose > 0.5, P[:, 1], np.inf))]
    mouth = centroid(w_lip ** 2)
    chin_sel = w_jaw * gauss(P * [1, 0, 0], 0, 0.25 * hw)
    chin = centroid(chin_sel ** 2)
    front = np.clip((eye_mid[1] + 0.25 * H - P[:, 1]) / (0.25 * H), 0, 1)   # the face half, not the back of the head
    Nn = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    D = {}
    z = np.zeros_like(P)
    # nose
    d = z.copy(); d[:, 0] = (P[:, 0] - nose_tip[0]) * 0.45 * w_nose; D['nose_width'] = d
    d = z.copy(); d[:, 1] = -0.35 * s * w_nose ** 1.5; D['nose_length'] = d
    d = z.copy(); d[:, 2] = 0.25 * s * w_nose; D['nose_height'] = d
    up = np.clip((P[:, 2] - nose_tip[2]) / max(eye_mid[2] - nose_tip[2], 1e-6), 0, 1)
    d = z.copy(); d[:, 1] = -0.3 * s * w_nose * up; D['nose_bridge'] = d
    # eyes (each side about its own centre)
    side = np.sign(P[:, 0])
    d = z.copy(); d[:, 0] = side * 0.18 * s * w_eye; D['eye_spacing'] = d
    d = z.copy(); d[:, 2] = 0.18 * s * w_eye; D['eye_height'] = d
    c = np.where((P[:, 0] < 0)[:, None], eyeL, eyeR)
    core = w_eye ** 2
    D['eye_size'] = (P - c) * 0.22 * core[:, None] * [1, 0.3, 1]
    d = z.copy(); d[:, 1] = 0.22 * s * core; D['eye_depth'] = d
    # brow: above each eye and between them
    rb = 0.13 * H
    browL, browR = eyeL + [0, -0.05 * H, 0.12 * H], eyeR + [0, -0.05 * H, 0.12 * H]
    w_brow = np.clip(gauss(P, browL, rb) + gauss(P, browR, rb) + 0.6 * gauss(P, (browL + browR) / 2, rb), 0, 1) * front * (1 - 0.6 * core)
    d = z.copy(); d[:, 2] = 0.15 * s * w_brow; D['brow_height'] = d
    D['brow_depth'] = Nn * (0.18 * s * w_brow)[:, None]
    # cheekbones: below and outside each eye
    ck = 0.12 * H
    ckL = eyeL + [-0.35 * abs(eyeL[0]), -0.0, -0.12 * H]
    ckR = eyeR + [0.35 * abs(eyeR[0]), -0.0, -0.12 * H]
    w_ck = np.clip(gauss(P, ckL, ck) + gauss(P, ckR, ck), 0, 1) * front * (1 - w_nose) * (1 - core)
    D['cheekbones'] = Nn * (0.2 * s * w_ck)[:, None] + np.stack([np.sign(P[:, 0]) * 0.08 * s * w_ck, z[:, 1], z[:, 2]], 1)
    # mouth
    d = z.copy(); d[:, 0] = (P[:, 0] - mouth[0]) * 0.3 * w_lip; D['mouth_width'] = d
    d = z.copy(); d[:, 2] = 0.15 * s * w_lip; D['mouth_height'] = d
    D['lips'] = Nn * (0.12 * s * w_lip ** 2)[:, None]
    # jaw and chin
    low = np.clip((mouth[2] + 0.05 * H - P[:, 2]) / (0.2 * H), 0, 1)
    d = z.copy(); d[:, 0] = P[:, 0] * 0.22 * w_jaw * low; D['jaw_width'] = d
    w_chin = np.clip(gauss(P, chin, 0.16 * H), 0, 1) * front * low
    d = z.copy(); d[:, 2] = -0.28 * s * w_chin; D['chin_length'] = d
    d = z.copy(); d[:, 1] = -0.25 * s * w_chin; D['chin_point'] = d
    # ears: the outermost parts at the eyes' height, behind the face
    ear_z = (eye_mid[2] + nose_tip[2]) / 2
    w_ear = np.clip((np.abs(P[:, 0]) - 0.78 * hw) / (0.12 * hw), 0, 1) * gauss(P * [0, 0, 1], [0, 0, ear_z], 0.14 * H) \
        * np.clip((P[:, 1] - eye_mid[1]) / (0.15 * H), 0, 1)
    w_ear = np.clip(smooth(w_ear, T, grp, 2), 0, 1)
    root = np.stack([np.sign(P[:, 0]) * 0.78 * hw, np.full(len(P), eye_mid[1] + 0.3 * H), np.full(len(P), ear_z)], 1)
    D['ear_size'] = (P - root) * 0.35 * w_ear[:, None]
    # every move: gone at the open edges, one value per position
    for k in D:
        dk = D[k] * edge[:, None]
        g = np.zeros((grp.max() + 1, 3))
        cnt = np.zeros(grp.max() + 1)
        np.add.at(g, grp, dk)
        np.add.at(cnt, grp, 1)
        D[k] = (g / np.maximum(cnt, 1)[:, None])[grp]
    marks = {'eyeL': eyeL, 'eyeR': eyeR, 'nose_tip': nose_tip, 'mouth': mouth, 'chin': chin, 'H': H, 'hw': hw}
    return D, marks


def main():
    src, out = sys.argv[1], sys.argv[2]
    g = G(src)
    node = next(n for n in g.g['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    mesh = g.g['meshes'][node['mesh']]
    names = mesh.get('extras', {}).get('targetNames', [])
    if any(n.startswith('fx_') for n in names):
        raise SystemExit('already has fx_ targets')
    for pi, prim in enumerate(mesh['primitives']):
        P = g.acc(prim['attributes']['POSITION']).astype(np.float64)
        N = g.acc(prim['attributes']['NORMAL']).astype(np.float64)
        T = g.acc(prim['indices']).astype(np.int64).reshape(-1, 3)
        fm = [g.acc(t['POSITION']).astype(np.float64) for t in prim.get('targets', [])[:8]]
        if len(fm) < 8:
            raise SystemExit('the head has no Catacombs morphs to find its features by')
        D, marks = build(P, N, T, fm, arg('scale', 1.0))
        if pi == 0:
            print('landmarks', {k: (np.round(v, 2).tolist() if hasattr(v, 'tolist') else round(v, 2)) for k, v in marks.items()})
        grp = weld(P)
        n0 = vertex_normals(P, T, grp)
        for k, _ in FEATURES:
            d = D[k]
            n1 = vertex_normals(P + d, T, grp)
            t = {'POSITION': g.add_vec3(d), 'NORMAL': g.add_vec3(n1 - n0)}
            prim.setdefault('targets', []).append(t)
            if pi == 0:
                print('%-12s max %.3f moved %d' % (k, np.linalg.norm(d, axis=1).max(), int((np.linalg.norm(d, axis=1) > 1e-4).sum())))
    mesh.setdefault('extras', {})['targetNames'] = names + ['fx_' + k for k, _ in FEATURES]
    if 'weights' in mesh:
        mesh['weights'] = mesh['weights'] + [0.0] * len(FEATURES)
    # the hair styles (beards, moustaches, sideburns: meshes of their own) follow the face: each point takes the moves
    # of the head's nearest points, fading out a little way off the skin
    hp = g.acc(mesh['primitives'][0]['attributes']['POSITION']).astype(np.float64)
    hd = {k: np.array(D[k]) for k, _ in FEATURES}
    H = hp[:, 2].max() - hp[:, 2].min()
    meta_path = Path(src).with_name('figure.json')
    hair_nodes = set()
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        hair_nodes = {st.get('node') for st in meta.get('hair_styles', []) if st.get('node')}
    for n in g.g['nodes']:
        if n.get('name') not in hair_nodes or 'mesh' not in n:
            continue
        hm = g.g['meshes'][n['mesh']]
        hnames = hm.get('extras', {}).get('targetNames', [])
        moved = 0
        for prim in hm['primitives']:
            Q = g.acc(prim['attributes']['POSITION']).astype(np.float64)
            idx = np.zeros((len(Q), 4), np.int64)
            dist = np.zeros((len(Q), 4))
            for s0 in range(0, len(Q), 512):
                dd = np.linalg.norm(Q[s0:s0 + 512, None, :] - hp[None], axis=2)
                ii = np.argpartition(dd, 4, axis=1)[:, :4]
                idx[s0:s0 + 512] = ii
                dist[s0:s0 + 512] = np.take_along_axis(dd, ii, 1)
            wgt = 1.0 / np.maximum(dist, 1e-4)
            wgt /= wgt.sum(1, keepdims=True)
            fall = np.clip(1.0 - (dist.min(1) - 0.01 * H) / (0.06 * H), 0, 1)
            if len(prim.get('targets', [])) != len(hnames):
                prim['targets'] = prim.get('targets', [])[:len(hnames)]
            for k, _ in FEATURES:
                d = (hd[k][idx] * wgt[..., None]).sum(1) * fall[:, None]
                moved = max(moved, int((np.linalg.norm(d, axis=1) > 1e-4).sum()))
                prim.setdefault('targets', []).append({'POSITION': g.add_vec3(d), 'NORMAL': g.add_vec3(np.zeros_like(d))})
        hm.setdefault('extras', {})['targetNames'] = hnames + ['fx_' + k for k, _ in FEATURES]
        if 'weights' in hm:
            hm['weights'] = hm['weights'] + [0.0] * len(FEATURES)
        print('hair %-10s follows the face (%d points)' % (n['name'], moved))
    g.save(out)
    print('wrote', out)


if __name__ == '__main__':
    main()
