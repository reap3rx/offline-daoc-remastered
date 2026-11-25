"""The HD head's own texture layout: MakeHuman's head UVs (its pieces - the face and scalp, the ears, the neck), packed
into a square of their own at one texel density. The same for every race and both sexes (one topology)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

PAD = 0.012


def islands(F, FT, keep):
    ks = np.flatnonzero(keep)
    corners = np.unique(np.concatenate([FT[k] for k in ks]))
    idx = {c: i for i, c in enumerate(corners)}
    r, c_ = [], []
    for k in ks:
        f = FT[k]
        for j in range(len(f)):
            r.append(idx[f[j]]); c_.append(idx[f[(j + 1) % len(f)]])
    n = len(corners)
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c_)), shape=(n, n)), directed=False)
    return corners, lab


def layout(VT, F, FT, keep):
    """-> {vt index: new uv} for the head's pieces, packed into 0..1."""
    VT = np.asarray(VT, float)
    corners, lab = islands(F, FT, keep)
    boxes = []
    for i in np.unique(lab):
        cs = corners[lab == i]
        q = VT[cs].copy()
        lo, hi = q.min(0), q.max(0)
        rot = (hi - lo)[1] > 1.3 * (hi - lo)[0]              # (tall pieces lie on their side: they pack tighter)
        if rot:
            q = np.c_[q[:, 1], -q[:, 0]]
        lo, hi = q.min(0), q.max(0)
        boxes.append((i, cs, lo, hi - lo, q))
    boxes.sort(key=lambda b: -b[3][1])                  # tallest first

    def pack(s):
        x = y = rowh = 0.0
        place = {}
        for i, cs, lo, sz, q in boxes:
            w, h = sz * s
            if x + w > 1.0:
                x, y, rowh = 0.0, y + rowh + PAD, 0.0
            if w > 1.0:
                return None
            place[i] = (x, y)
            x += w + PAD
            rowh = max(rowh, h)
        return place if y + rowh <= 1.0 else None

    lo_s, hi_s = 0.1, 10.0
    for _ in range(40):
        mid = (lo_s + hi_s) / 2
        if pack(mid):
            lo_s = mid
        else:
            hi_s = mid
    s = lo_s
    place = pack(s)
    out = {}
    for i, cs, lo, sz, q in boxes:
        ox, oy = place[i]
        for c, qq in zip(cs, q):
            out[int(c)] = (qq - lo) * s + [ox + PAD / 2, oy + PAD / 2]
    return out, s
