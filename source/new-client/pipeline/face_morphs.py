"""Face shapes (claude 2026-11-06, owner: "how hard would it be to have more detailed facial customization so you're
not picking between the same 4 or 5 faces?"). For a race figure's head, a set of new morph targets ("fx_<name>"), each
one feature moved: the nose's width, length, height, bridge and tip (upturned or hooked); the eyes' spacing, height, size and depth; the brow's
height and depth; the cheekbones; the mouth's width, height and lips; the jaw's width; the chin's length and point;
the ears' size. One target per slider, used from -1 to 1.

Where each feature is comes from the head's own Catacombs morphs (FM1/2 the eyes, FM3/4 the nose, FM5/6 the lips,
FM7/8 the jaw - drawn by the client's artists), the rest from landmarks found from those (the brow above the eyes,
the cheekbones beside the nose, the ears at the sides). Every move fades to nothing at the head's open edges (the
neck seam with the body) and is the same on every copy of a position (the texture seams), and the target's normals
follow the new shape. The skull and the hairline are not moved: the hair meshes sit on them.

    python face_morphs.py <figure.gltf> <out.gltf> [--scale=1.0]
build_races.py runs it on every figure after the smoothing (skip with --no-face-shapes).
"""
import base64, json, sys
from pathlib import Path
import numpy as np

COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

# name, label, range note (all -1 .. 1)
FEATURES = [
    ('nose_width', 'Nose Width'), ('nose_length', 'Nose Length'), ('nose_height', 'Nose Height'),
    ('nose_bridge', 'Nose Bridge'), ('nose_tip', 'Nose Tip'), ('eye_spacing', 'Eye Spacing'), ('eye_height', 'Eye Height'),
    ('eye_size', 'Eye Size'), ('eye_depth', 'Eye Depth'), ('eye_tilt', 'Eye Slant'), ('eye_squint', 'Eye Squint'),
    ('brow_height', 'Brow Height'), ('brow_depth', 'Brow Ridge'), ('nose_tip_size', 'Nose Tip Size'),
    ('cheekbones', 'Cheekbones'), ('cheek_puff', 'Cheek Fullness'), ('mouth_width', 'Mouth Width'),
    ('mouth_height', 'Mouth Height'), ('lips', 'Lip Fullness'), ('upper_lip', 'Upper Lip'), ('lower_lip', 'Lower Lip'),
    ('smile', 'Smile'), ('lip_out', 'Lip Pout'),
    ('jaw_width', 'Jaw Width'), ('jaw_height', 'Jaw Angle'), ('jaw_sharp', 'Jaw Definition'),
    ('chin_length', 'Chin Length'), ('chin_point', 'Chin Depth'), ('chin_width', 'Chin Width'),
    ('ear_size', 'Ear Size'), ('ear_out', 'Ears Out'), ('ear_tilt', 'Ear Tilt'),
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


def open_loops(P, T, grp):
    """The mesh's open edge loops (by position): a list of point arrays."""
    e = np.sort(np.concatenate([grp[T[:, [0, 1]]], grp[T[:, [1, 2]]], grp[T[:, [2, 0]]]]), axis=1)
    u, c = np.unique(e, axis=0, return_counts=True)
    be = u[c == 1]
    gp = np.zeros((grp.max() + 1, 3))
    gp[grp] = P
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
    return [gp[vs] for vs in loops.values()]


def space_smooth(w, P, r):
    """A weight averaged over the points within about r in space (crosses the mesh's gaps, e.g. the lips' seam)."""
    out = np.zeros(len(P))
    for s0 in range(0, len(P), 512):
        k = np.exp(-np.sum((P[s0:s0 + 512, None, :] - P[None]) ** 2, axis=2) / (2 * r * r))
        out[s0:s0 + 512] = (k * w[None]).sum(1) / k.sum(1)
    return out


def gauss(P, c, r):
    return np.exp(-np.sum((P - c) ** 2, axis=1) / (2 * r * r))


def build(P, N, T, fm, scale=1.0):
    """The new targets' position deltas: {name: (n, 3)}. P: positions (z up, the face toward -y)."""
    grp = weld(P)
    lo, hi = P.min(0), P.max(0)
    H = hi[2] - lo[2]
    hw = max(-lo[0], hi[0])

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
    # the face's size: the head mesh's height, unless the mesh carries more than a head's worth (the Shar's horns made
    # it 2.5x: every move came out 2.5x, a snout instead of a nose) - then five eye spacings, a head's height
    H = min(H, 5.0 * abs(eyeR[0] - eyeL[0]))
    hw = min(hw, 0.3 * H)
    s = H / 10.0 * scale                                   # a feature's move: a tenth of the head, at full slider
    nose_tip = P[np.argmin(np.where(w_nose > 0.5, P[:, 1], np.inf))]
    mouth = centroid(w_lip ** 2)
    chin_sel = w_jaw * gauss(P * [1, 0, 0], 0, 0.25 * hw)
    chin = centroid(chin_sel ** 2)
    front = np.clip((eye_mid[1] + 0.25 * H - P[:, 1]) / (0.25 * H), 0, 1)   # the face half, not the back of the head
    # not every race's FM7/8 is its jaw (the elves', firbolgs', Shar's, Valkyn's move the ears or the whole head): a
    # 'chin' found above the mouth or behind the face means the jaw comes from the shape instead - the chin the
    # midline's low forward corner below the mouth, the jaw the face below the mouth
    if not (chin[2] < mouth[2] and chin[1] < eye_mid[1] + 0.1 * H):
        w_jaw = np.clip((mouth[2] + 0.02 * H - P[:, 2]) / (0.1 * H), 0, 1) * front
        mid = np.abs(P[:, 0] - mouth[0]) < 0.06 * H
        # (low and forward: the chin's corner, not the lower lip above it nor the neck below and behind it)
        cand = np.where(mid & (P[:, 2] < mouth[2] - 0.06 * H) & (P[:, 2] > mouth[2] - 0.22 * H),
                        P[:, 2] + 2.0 * P[:, 1], np.inf)
        if np.isfinite(cand.min()):
            chin = P[np.argmin(cand)].copy()
        print('  (the jaw from the shape: FM7/8 are not this head\'s jaw)')
    Nn = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    # the lips' weight smoothed through space, not along the mesh: the upper and lower lip are not joined, so a move
    # that took them differently at their seam opened the mouth (the teeth showed); the mouth's moves use it, every
    # other move leaves the lips alone (and the area under the nose with them)
    w_ls = np.clip(space_smooth(w_lip, P, 0.035 * H) * 1.15, 0, 1)
    keep_mouth = 1 - np.clip(space_smooth(w_lip, P, 0.08 * H) * 2.5, 0, 1)
    D = {}
    z = np.zeros_like(P)
    # nose
    d = z.copy(); d[:, 0] = (P[:, 0] - nose_tip[0]) * 0.45 * w_nose; D['nose_width'] = d
    d = z.copy(); d[:, 1] = -0.35 * s * w_nose ** 1.5; D['nose_length'] = d
    d = z.copy(); d[:, 2] = 0.25 * s * w_nose; D['nose_height'] = d
    up = np.clip((P[:, 2] - nose_tip[2]) / max(eye_mid[2] - nose_tip[2], 1e-6), 0, 1)
    d = z.copy(); d[:, 1] = -0.3 * s * w_nose * up; D['nose_bridge'] = d
    # the tip (owner: "upturn the tip of the nose"): the lower nose turns up about a point between the eyes and the
    # tip, the nostrils showing more; -1 hooks it down
    pivot = nose_tip + (eye_mid - nose_tip) * 0.55
    pivot[0] = nose_tip[0]
    pivot[1] = nose_tip[1] + 0.3 * (eye_mid[1] - nose_tip[1])  # on the nose's ridge, so the tip lifts more than it grows
    w_tip = w_nose * np.clip(gauss(P, nose_tip + [0, 0.01 * H, -0.02 * H], 0.075 * H) * 1.3, 0, 1) \
        * np.clip((pivot[2] - P[:, 2]) / max(pivot[2] - nose_tip[2], 1e-6), 0, 1)
    th = -0.34                                              # radians at full slider: the tip swings up
    ry, rz = P[:, 1] - pivot[1], P[:, 2] - pivot[2]
    d = z.copy()
    d[:, 1] = (ry * np.cos(th) - rz * np.sin(th) - ry) * w_tip
    d[:, 2] = (ry * np.sin(th) + rz * np.cos(th) - rz) * w_tip
    D['nose_tip'] = d
    # the tip's size (owner 2026-11-06): the ball of the nose grown about its own middle, a little inside the tip
    tipc = nose_tip + [0, 0.035 * H, 0.01 * H]
    w_ts = w_nose * np.clip(gauss(P, tipc, 0.06 * H) * 1.2, 0, 1)
    D['nose_tip_size'] = (P - tipc) * 0.45 * w_ts[:, None]
    # eyes (each side about its own centre)
    side = np.sign(P[:, 0])
    d = z.copy(); d[:, 0] = side * 0.18 * s * w_eye; D['eye_spacing'] = d
    d = z.copy(); d[:, 2] = 0.18 * s * w_eye; D['eye_height'] = d
    c = np.where((P[:, 0] < 0)[:, None], eyeL, eyeR)
    core = w_eye ** 2
    D['eye_size'] = (P - c) * 0.22 * core[:, None] * [1, 0.3, 1]
    d = z.copy(); d[:, 1] = 0.22 * s * core; D['eye_depth'] = d
    # slant (owner 2026-11-06): each eye turned about its centre, the outer corner up (+) or down
    th = np.sign(P[:, 0]) * 0.22
    rx, rz = P[:, 0] - c[:, 0], P[:, 2] - c[:, 2]
    d = z.copy()
    d[:, 0] = (rx * np.cos(th) - rz * np.sin(th) - rx) * core
    d[:, 2] = (rx * np.sin(th) + rz * np.cos(th) - rz) * core
    D['eye_tilt'] = d
    # squint (owner 2026-11-06): the lids drawn toward the eye's middle line, the lower one a little more
    d = z.copy()
    dz = P[:, 2] - c[:, 2]
    d[:, 2] = -dz * 0.32 * core * np.where(dz < 0, 1.25, 1.0)
    D['eye_squint'] = d
    # brow: the ridge over the eyes, a narrow band (owner 2026-11-06: a round region a quarter of the head across moved
    # the whole upper face) - its height the most forward row above each eye, across the eyes and between them
    E = abs(eyeR[0] - eyeL[0])
    zs = []
    for e in (eyeL, eyeR):
        sel = (np.abs(P[:, 0] - e[0]) < 0.35 * E) & (P[:, 2] > e[2]) & (P[:, 2] < e[2] + 0.25 * H)
        if sel.sum() > 3:
            ys = P[sel, 1]
            top = sel.nonzero()[0][ys <= np.percentile(ys, 10)]
            zs.append(float(np.median(P[top, 2])))
    brow_z = float(np.mean(zs)) if zs else eye_mid[2] + 0.08 * H
    across = np.clip((abs(eyeR[0]) + 0.55 * E - np.abs(P[:, 0] - eye_mid[0])) / (0.3 * E), 0, 1)
    w_brow = np.exp(-((P[:, 2] - brow_z) / (0.06 * H)) ** 2) * across * front * (1 - 0.8 * core)
    d = z.copy(); d[:, 2] = 0.15 * s * w_brow; D['brow_height'] = d
    D['brow_depth'] = Nn * (0.18 * s * w_brow)[:, None]
    # cheekbones: below and outside each eye
    # (owner 2026-11-06: it widened the whole face - now the bone's own ridge, under the outer eye, and mostly forward)
    ck = 0.075 * H
    ckL = eyeL + [-0.3 * abs(eyeL[0]), -0.0, -0.11 * H]
    ckR = eyeR + [0.3 * abs(eyeR[0]), -0.0, -0.11 * H]
    above_mouth = np.clip((P[:, 2] - (mouth[2] + 0.08 * H)) / (0.08 * H), 0, 1)
    w_ck = np.clip(gauss(P, ckL, ck) + gauss(P, ckR, ck), 0, 1) * front * (1 - w_nose) * (1 - core) * above_mouth
    D['cheekbones'] = Nn * (0.3 * s * w_ck)[:, None] + np.stack([np.sign(P[:, 0]) * 0.03 * s * w_ck, z[:, 1], z[:, 2]], 1)
    # the cheeks' flesh (owner 2026-11-06: "sunken or puffy"): beside the mouth, under the cheekbones, along the skin
    cz = mouth[2] + 0.1 * H
    cx = 0.5 * (abs(eyeL[0]) + abs(eyeR[0])) + 0.02 * H
    q = ((np.abs(P[:, 0]) - cx) / (0.09 * H)) ** 2 + ((P[:, 2] - cz) / (0.1 * H)) ** 2
    w_cp = np.exp(-q) * front * (1 - w_nose) * (1 - core)
    D['cheek_puff'] = Nn * (0.28 * s * w_cp)[:, None]
    # mouth (owner 2026-11-06: the old moves took the whole mouth area - now the lips themselves): the seam is the
    # lips' own open edges; each lip a band above / below it, the corners at its ends
    lps = [q_ for q_ in open_loops(P, T, grp) if np.linalg.norm(q_.mean(0)[[0, 2]] - mouth[[0, 2]]) < 0.12 * H]
    S = np.concatenate(lps) if lps else mouth[None]
    mx, zc = mouth[0], 0.5 * (S[:, 2].max() + S[:, 2].min())
    hm = max((S[:, 0].max() - S[:, 0].min()) / 2, 0.05 * H)
    sy = S[:, 1].min()
    dx, dz = P[:, 0] - mx, P[:, 2] - zc
    along = np.clip((hm * 1.12 - np.abs(dx)) / (0.3 * hm), 0, 1)
    infront = np.clip((sy + 0.03 * H - P[:, 1]) / (0.03 * H), 0, 1)
    # (nothing at the seam itself: a lip that grew at its edge parted the mouth)
    dseam = np.full(len(P), np.inf)
    for s0 in range(0, len(S), 256):
        dseam = np.minimum(dseam, np.linalg.norm(P[:, None, :] - S[None, s0:s0 + 256], axis=2).min(1))
    off_seam = np.clip((dseam - 0.004 * H) / (0.018 * H), 0, 1)
    w_up = along * infront * off_seam * (dz > 0) * np.clip((0.065 * H - dz) / (0.03 * H), 0, 1)
    w_lo = along * infront * off_seam * (dz < 0) * np.clip((0.075 * H + dz) / (0.035 * H), 0, 1)
    # (a lip's height about the seam more than its push out: drawn in along the skin, thin lips showed the mouth's
    # inside)
    ms = s * float(np.clip(0.08 * H / hm, 1.0, 1.8))     # (small mouths - the lurikeen's - a bigger move of their own)
    D['upper_lip'] = Nn * (0.035 * ms * w_up)[:, None] + np.stack([z[:, 0], z[:, 1], 0.5 * dz * w_up], 1)
    D['lower_lip'] = Nn * (0.04 * ms * w_lo)[:, None] + np.stack([z[:, 0], z[:, 1], 0.5 * dz * w_lo], 1)
    D['lips'] = D['upper_lip'] + D['lower_lip']
    # the seam's two edges get the same weight (they sit alike about its middle), so the mouth stays shut
    w_mw = np.clip((hm * 1.6 - np.abs(dx)) / (0.6 * hm), 0, 1) * np.clip(1 - np.abs(dz) / (0.11 * H), 0, 1) \
        * np.clip((sy + 0.08 * H - P[:, 1]) / (0.05 * H), 0, 1)
    d = z.copy(); d[:, 0] = dx * 0.3 * w_mw; D['mouth_width'] = d
    d = z.copy(); d[:, 2] = 0.15 * s * w_ls; D['mouth_height'] = d
    w_cn = np.exp(-((np.abs(dx) - hm) ** 2 + dz ** 2) / (2 * (0.55 * hm) ** 2)) \
        * np.clip((sy + 0.08 * H - P[:, 1]) / (0.05 * H), 0, 1)
    d = z.copy(); d[:, 2] = 0.16 * ms * w_cn; d[:, 1] = 0.04 * ms * w_cn; D['smile'] = d
    w_po = along * np.clip(1 - np.abs(dz) / (0.08 * H), 0, 1) * infront
    d = z.copy(); d[:, 1] = -0.12 * ms * w_po; D['lip_out'] = d
    # the seam's two edges (upper lip's, lower lip's) moved as one: each seam point takes the mean of itself and the
    # other edge's point across from it, so no mouth move opens the mouth
    if len(lps) >= 2:
        lps2 = sorted(lps, key=lambda q_: q_[:, 2].mean())[-2:]
        idx = []
        for q_ in lps2:
            dd = np.full(len(P), np.inf)
            for s0 in range(0, len(q_), 256):
                dd = np.minimum(dd, np.linalg.norm(P[:, None, :] - q_[None, s0:s0 + 256], axis=2).min(1))
            idx.append(np.nonzero(dd < 1e-5 * H)[0])
        a_, b_ = idx
        if len(a_) and len(b_):
            pa, pb = P[a_], P[b_]
            na = b_[np.argmin(np.abs(pa[:, None, 0] - pb[None, :, 0]) + 0.3 * np.abs(pa[:, None, 1] - pb[None, :, 1]), axis=1)]
            nb = a_[np.argmin(np.abs(pb[:, None, 0] - pa[None, :, 0]) + 0.3 * np.abs(pb[:, None, 1] - pa[None, :, 1]), axis=1)]
            for k in MOUTH_KEYS:
                if k in D:
                    dk = D[k]
                    va, vb = (dk[a_] + dk[na]) / 2, (dk[b_] + dk[nb]) / 2
                    dk[a_], dk[b_] = va, vb
    # jaw and chin
    # (from below the lower lip, and never the lips: a jaw or chin that took the lower lip and not the upper opened
    # the mouth)
    low = np.clip((mouth[2] - 0.03 * H - P[:, 2]) / (0.17 * H), 0, 1) * (1 - w_ls)
    # the jaw (owner 2026-11-06: the old width moved the neck more than the jaw): its angles - the widest points of the
    # lower face, each side - and the jawline from them to the chin; nothing below the chin's level (the neck)
    noneck = np.clip((P[:, 2] - (chin[2] - 0.12 * H)) / (0.08 * H), 0, 1) * (1 - w_ls)
    gon = {}
    for sg in (-1, 1):
        sel = (np.sign(P[:, 0]) == sg) & (P[:, 2] > chin[2]) & (P[:, 2] < mouth[2])
        if sel.sum() > 5:
            ax = np.abs(P[sel, 0])
            top = sel.nonzero()[0][ax >= np.percentile(ax, 90)]
            gon[sg] = np.median(P[top], axis=0)
        else:
            gon[sg] = np.array([sg * 0.8 * hw, eye_mid[1] + 0.3 * H, (chin[2] + mouth[2]) / 2])
    G_ = np.where((P[:, 0] < 0)[:, None], gon[-1], gon[1])
    w_ang = np.clip(gauss(P, G_, 0.13 * H) * 1.2, 0, 1) * noneck
    side = np.sign(P[:, 0])
    d = z.copy(); d[:, 0] = side * 0.2 * s * w_ang + P[:, 0] * 0.06 * w_jaw * low * noneck; D['jaw_width'] = d
    d = z.copy(); d[:, 2] = 0.18 * s * w_ang; D['jaw_height'] = d
    # definition: the jawline's edge (from each angle down to the chin) - its underside drawn in and up, its side out,
    # so the edge turns crisp (+) or rounds off (-)
    gx = np.abs(G_[:, 0] - chin[0])
    edge_z = chin[2] + (G_[:, 2] - chin[2]) * np.clip(np.abs(P[:, 0] - chin[0]) / np.maximum(gx, 1e-6), 0, 1)
    R = np.exp(-((P[:, 2] - edge_z) / (0.06 * H)) ** 2) * np.clip((G_[:, 1] + 0.06 * H - P[:, 1]) / (0.06 * H), 0, 1) \
        * (1 - w_ls) * np.clip((P[:, 2] - (chin[2] - 0.2 * H)) / (0.06 * H), 0, 1)
    w_under = np.clip(-Nn[:, 2] * 1.5, 0, 1)
    D['jaw_sharp'] = (-Nn * (w_under * 0.14 * s)[:, None] + Nn * ((1 - w_under) * 0.08 * s)[:, None]) * R[:, None]
    w_chin = np.clip(gauss(P, chin, 0.16 * H), 0, 1) * front * low
    d = z.copy(); d[:, 2] = -0.28 * s * w_chin; D['chin_length'] = d
    d = z.copy(); d[:, 1] = -0.25 * s * w_chin; D['chin_point'] = d
    # width: the chin's sides out from its middle (-: narrowed to a point)
    w_cw = np.clip(gauss(P, chin, 0.12 * H), 0, 1) * front * low
    d = z.copy(); d[:, 0] = (P[:, 0] - chin[0]) * 0.45 * w_cw; D['chin_width'] = d
    # ears: the outermost parts at the eyes' height, behind the face
    ear_z = (eye_mid[2] + nose_tip[2]) / 2
    w_ear = np.clip((np.abs(P[:, 0]) - 0.78 * hw) / (0.12 * hw), 0, 1) * gauss(P * [0, 0, 1], [0, 0, ear_z], 0.14 * H) \
        * np.clip((P[:, 1] - eye_mid[1]) / (0.15 * H), 0, 1)
    w_ear = np.clip(smooth(w_ear, T, grp, 2), 0, 1)
    root = np.stack([np.sign(P[:, 0]) * 0.78 * hw, np.full(len(P), eye_mid[1] + 0.3 * H), np.full(len(P), ear_z)], 1)
    D['ear_size'] = (P - root) * 0.35 * w_ear[:, None]
    # (owner 2026-11-06: ears that stick out, ears that point up) - each turned about its root
    pv = root + [0, -0.06 * H, 0]
    r = P - pv
    th = -np.sign(P[:, 0]) * 0.35                               # out: the back of the ear swings away from the head
    d = z.copy()
    d[:, 0] = (r[:, 0] * np.cos(th) - r[:, 1] * np.sin(th) - r[:, 0]) * w_ear
    d[:, 1] = (r[:, 0] * np.sin(th) + r[:, 1] * np.cos(th) - r[:, 1]) * w_ear
    D['ear_out'] = d
    th = 0.3                                                    # tilt: the back of the ear swings up
    d = z.copy()
    d[:, 1] = (r[:, 1] * np.cos(th) - r[:, 2] * np.sin(th) - r[:, 1]) * w_ear
    d[:, 2] = (r[:, 1] * np.sin(th) + r[:, 2] * np.cos(th) - r[:, 2]) * w_ear
    D['ear_tilt'] = d
    # every move: gone at the open edges, one value per position; only the mouth's own moves touch the lips
    for k in D:
        dk = D[k] * (edge if k in MOUTH_KEYS else edge * keep_mouth)[:, None] * STRENGTH
        g = np.zeros((grp.max() + 1, 3))
        cnt = np.zeros(grp.max() + 1)
        np.add.at(g, grp, dk)
        np.add.at(cnt, grp, 1)
        D[k] = (g / np.maximum(cnt, 1)[:, None])[grp]
    marks = {'eyeL': eyeL, 'eyeR': eyeR, 'nose_tip': nose_tip, 'mouth': mouth, 'chin': chin, 'H': H, 'hw': hw}
    # (for pipeline/skin_layers.py: the regions too; '_' keys are not printed)
    marks['_w'] = {'eye': w_eye, 'nose': w_nose, 'lip': w_lip, 'lips': w_ls, 'jaw': w_jaw, 'front': front,
                   'lip_up': w_up, 'lip_lo': w_lo}
    return D, marks


MOUTH_KEYS = ('mouth_width', 'mouth_height', 'lips', 'upper_lip', 'lower_lip', 'smile', 'lip_out')

# every slider's full move (owner 2026-11-06: the extremes were the worst - a quarter less, then back up 15%)
STRENGTH = 0.8625      # (0.75, then owner 2026-11-06 again: 'too aggressive ... increase it 15%')

# races whose features need a bigger move to show (the trolls' heads are wide and craggy: at 1.0 the sliders barely read)
RACE_SCALE = {'tro': 1.5}


def main():
    run(sys.argv[1], sys.argv[2], arg('scale', 0) or None)


def run(src, out, scale=None):
    """Adds the fx_ targets to src's head and hair, writes out (may be src) and records the sliders in figure.json
    'face_shapes' ([name, label] each)."""
    if scale is None:
        scale = RACE_SCALE.get(Path(src).resolve().parent.name[:3], 1.0)
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
        D, marks = build(P, N, T, fm, scale)
        if pi == 0:
            print('landmarks', {k: (np.round(v, 2).tolist() if hasattr(v, 'tolist') else round(v, 2)) for k, v in marks.items() if not k.startswith('_')})
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
    meta_out = Path(out).with_name('figure.json')
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        meta['face_shapes'] = [[k, lab] for k, lab in FEATURES]
        meta_out.write_text(json.dumps(meta, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
