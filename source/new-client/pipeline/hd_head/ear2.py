"""The ears (v2): always MakeHuman's own ear, one skin with the head. A long-eared race's (the elves', the Lurikeen's,
the Inconnu's) is that ear drawn out to the classic ear's tip - never the classic ear set onto the new skull."""
import numpy as np
from scipy.spatial import cKDTree


def classic_ear(cP, ears_c, sx):
    """One side's classic ear: its root (where it leaves the skull), its tip, its length."""
    m = ears_c & (cP[:, 0] * sx > 0)
    if m.sum() < 6:
        return None
    Q = cP[m]
    inner = Q[np.abs(Q[:, 0]) < np.percentile(np.abs(Q[:, 0]), 25)]
    root = inner.mean(0)
    tip = Q[np.argmax(np.linalg.norm(Q - root, axis=1))]
    return dict(root=root, tip=tip, length=float(np.linalg.norm(tip - root)), pts=Q)


def mh_ear(P, w_ear, sx):
    """The fitted MakeHuman ear's own measures: its middle, its top point, its height."""
    m = (w_ear > 0.999) & (P[:, 0] * sx > 0)
    Q = P[m]
    c = Q.mean(0)
    top = Q[np.argmax(Q[:, 2] + 0.3 * Q[:, 1])]
    return dict(c=c, top=top, height=float(np.ptp(Q[:, 2])), m=m)


def free_dist(P, T, ear):
    """How far along the skin each ear point is from the ear's root (the skull's skin round it)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    n = len(P)
    r = np.r_[T[:, 0], T[:, 1], T[:, 2]]; c = np.r_[T[:, 1], T[:, 2], T[:, 0]]
    w = np.linalg.norm(P[r] - P[c], axis=1)
    G = coo_matrix((np.r_[w, w], (np.r_[r, c], np.r_[c, r])), shape=(n, n)).tocsr()
    em = ear > 0.5
    src = np.unique(np.r_[r[em[c] & ~em[r]], c[em[r] & ~em[c]]])
    d = dijkstra(G, indices=src, min_only=True)
    d[~np.isfinite(d)] = 0
    return d * em


def draw_out(P, T, ear, sx, tip, start=0.15, power=1.5, slim=0.6, log=None):
    """The ear drawn out to 'tip': a stretch along the line from the ear's middle to the tip - nothing before 'start'
    of the ear's own reach that way, the far end all the way to the tip - and slimmed toward that line as it goes
    (a point, not a paddle). The ear's root stays on the head. -> new P."""
    e = mh_ear(P, ear, sx)
    m = e['m']
    d = tip - e['c']; Lt = np.linalg.norm(d); d = d / Lt
    proj = (P - e['c']) @ d
    Lm = proj[m].max()
    if Lt <= Lm * 1.05:
        return P, np.zeros(len(P))
    u = np.clip((proj / Lm - start) / (1 - start), 0, 1)
    fd = free_dist(P, T, ear * (P[:, 0] * sx > 0))
    free = np.clip(fd / (0.22 * e['height']), 0, 1)
    free = free * free * (3 - 2 * free)
    q = (u ** power) * free * m
    q = q / max(q.max(), 1e-9)
    Pn = P + q[:, None] * (Lt - Lm) * d
    rel = Pn - e['c']
    along = rel @ d
    perp = rel - along[:, None] * d
    Pn = Pn - perp * (q * slim)[:, None]
    # the move evened out over the ear's skin (no kink where the drawn part leaves the root)
    from fit2 import adjacency
    A = adjacency(T, len(P))
    D = Pn - P
    for _ in range(4):
        D = np.where(m[:, None], 0.5 * D + 0.5 * (A @ D), 0.0)
    k = np.linalg.norm(Pn[m] - P[m], axis=1).max() / max(np.linalg.norm(D[m], axis=1).max(), 1e-9)
    D = D * min(k, 1.25)
    dl = np.linalg.norm(D, axis=1)
    return P + D, dl / max(dl.max(), 1e-9)


def ear_delta(P_unit, P_drawn, m, q, free, D, keep_rest):
    """A slider's move for a drawn-out ear. D: the move MakeHuman's target gives its own (undrawn) ear's points. The
    drawn ear takes what that move does to the ear as a whole - where it goes, how it turns and grows (a similarity
    fitted to MakeHuman's ear before and after): its free part exactly that, its root running into the skull's own
    move. keep_rest: a target that reshapes a part (the lobe, the point) also gives the undrawn part that reshaping.
    -> the ear points' moves."""
    from fit2 import similarity
    if np.abs(D[m]).max() < 1e-6:
        return D[m]
    s, R, t = similarity(P_unit[m], P_unit[m] + D[m])
    whole = lambda X: (s * (R @ X.T)).T + t
    part = whole(P_unit[m]) - P_unit[m]
    w = free[m][:, None]
    out = w * (whole(P_drawn[m]) - P_drawn[m]) + (1 - w) * part
    rest = D[m] - part
    if keep_rest:
        out = out + rest * (1 - np.clip(q[m] * 3.0, 0, 1))[:, None]
    else:
        out = out + rest * (1 - w)                             # (at the root: the target's own run-in to the skull)
    return out
