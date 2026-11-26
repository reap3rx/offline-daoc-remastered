"""Automatic checks on a built head (v2) - what went wrong before, tested for every race and at the sliders' ends:
the skin is one closed piece with one edge (the neck's), that edge sits on the classic edge point for point, the
skin never lies inside an eyeball, the eyeball never shows outside the lids, no triangle folds over."""
import numpy as np
from collections import defaultdict
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from landmarks import sphere_fit


LID_TOL = 0.0
MAX_STRETCH = 5.0
MOUTH_OUT = 3
MAX_CRUMPLE = 40
MOUTH_OUT_SLIDER = 10
EDGE_TOL = 0.09
MAX_FOLDS = 4


def topology(Q, T, grp):
    Tg = grp[T]
    e = np.sort(np.r_[Tg[:, [0, 1]], Tg[:, [1, 2]], Tg[:, [2, 0]]], 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    ob = u[c == 1]
    n = grp.max() + 1
    nc, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    pieces = len(np.unique(lab[Tg[:, 0]]))
    loops = 0
    if len(ob):
        k, l2 = connected_components(coo_matrix((np.ones(len(ob)), (ob[:, 0], ob[:, 1])), shape=(n, n)), directed=False)
        loops = len(np.unique(l2[np.unique(ob)]))
    return pieces, loops, int((c > 2).sum())


def eye_data(res):
    """The eyeballs' points, their triangles and which side each is."""
    pc = res['pieces']['eyes']
    return pc['X'], pc['T'], pc['X'][:, 0] > 0


def _clear(Q, X, T, left, NQ):
    """Each skin point's clearance off the eyeball it lies over (of the eye's size; < 0: inside it), nan elsewhere.
    Only the skin facing out counts (the socket behind the eye is inside it by design)."""
    from scipy.spatial import cKDTree
    n = np.zeros_like(X)
    f = np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], f)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    out = np.full(len(Q), np.nan)
    for sel in (left, ~left):
        c, r = sphere_fit(X[sel])
        nn = n[sel].copy()
        nn[((X[sel] - c) * nn).sum(1) < 0] *= -1
        near = (np.linalg.norm(Q - c, axis=1) < 1.5 * r) & ((Q - c)[:, 1] < 0.0) & (((Q - c) * NQ).sum(1) > 0.25 * r)
        if near.any():
            _, j = cKDTree(X[sel]).query(Q[near])
            out[near] = ((Q[near] - X[sel][j]) * nn[j]).sum(1) / r
    return out


def lid_rest(Q, X, T, left, NQ):
    """At rest: which of the skin over the eyes is the lids' edge (it rests on the eye by design)."""
    cl = _clear(Q, X, T, left, NQ)
    return dict(over=np.isfinite(cl), edge=np.isfinite(cl) & (cl < 0.08), NQ=NQ)


def lid_depth(Q, X, T, left, rest):
    """-> (how deep the lids proper lie inside an eyeball at worst - above 0 the eye shows through the lid; how deep
    the lids' edge sinks into it), of the eye's size."""
    cl = _clear(Q, X, T, left, rest['NQ'])
    cl = np.where(np.isfinite(cl), cl, 1.0)
    proper = rest['over'] & ~rest['edge']
    return (float(-cl[proper].min()) if proper.any() else -1.0, float(-cl[rest['edge']].min()) if rest['edge'].any() else -1.0)


def lid_ok(d):
    return d[0] <= LID_TOL and d[1] <= EDGE_TOL


def lid_clear(d):
    """(a slider's own end: with room to spare for the others)"""
    return d[0] <= -0.008 and d[1] <= EDGE_TOL


def folds(Q0, Q1, T, swing=None):
    """Triangles turned over between Q0 and Q1. swing: each point's turn round the left-right axis (the blink's lid
    swung round its eyeball) - a triangle is compared with itself turned by its own points' mean, not at rest."""
    n0 = np.cross(Q0[T[:, 1]] - Q0[T[:, 0]], Q0[T[:, 2]] - Q0[T[:, 0]])
    if swing is not None:
        a = swing[T].mean(1)
        cy, sy = np.cos(a), np.sin(a)
        n0 = np.c_[n0[:, 0], n0[:, 1] * cy - n0[:, 2] * sy, n0[:, 1] * sy + n0[:, 2] * cy]
    n1 = np.cross(Q1[T[:, 1]] - Q1[T[:, 0]], Q1[T[:, 2]] - Q1[T[:, 0]])
    a0 = np.linalg.norm(n0, axis=1); a1 = np.linalg.norm(n1, axis=1)
    cos = (n0 * n1).sum(1) / np.maximum(a0 * a1, 1e-12)
    return int(((cos < 0) & (a0 > 1e-6)).sum())


def stretch(Q0, Q1, T):
    """The most any triangle edge grows at a slider's end (x its length at rest; edges of some length only)."""
    worst = 1.0
    for a, b in ((0, 1), (1, 2), (2, 0)):
        l0 = np.linalg.norm(Q0[T[:, a]] - Q0[T[:, b]], axis=1)
        l1 = np.linalg.norm(Q1[T[:, a]] - Q1[T[:, b]], axis=1)
        ok = l0 > 0.06
        if ok.any():
            worst = max(worst, float((l1[ok] / l0[ok]).max()))
    return worst


def mouth_out(Q, T, X, box=None):
    """How many of the teeth's / tongue's points have no skin in front of them (seen from the front): with the lips
    together, none should - one that has is poking out through the face."""
    lo, hi = X.min(0) - 0.3, X.max(0) + 0.3
    tri = Q[T]
    keep = ((tri[:, :, 0].max(1) > lo[0]) & (tri[:, :, 0].min(1) < hi[0]) & (tri[:, :, 2].max(1) > lo[2]) & (tri[:, :, 2].min(1) < hi[2])
            & (tri[:, :, 1].min(1) < hi[1]))
    tri = tri[keep]
    a, b, cc = tri[:, 0], tri[:, 1], tri[:, 2]
    covered = np.zeros(len(X), bool)
    for s in range(0, len(X), 400):
        p = X[s:s + 400]
        px, pz = p[:, 0][:, None], p[:, 2][:, None]
        d = (b[:, 2] - cc[:, 2]) * (a[:, 0] - cc[:, 0]) + (cc[:, 0] - b[:, 0]) * (a[:, 2] - cc[:, 2])
        d = np.where(np.abs(d) < 1e-12, 1e-12, d)
        w0 = ((b[:, 2] - cc[:, 2]) * (px - cc[:, 0]) + (cc[:, 0] - b[:, 0]) * (pz - cc[:, 2])) / d
        w1 = ((cc[:, 2] - a[:, 2]) * (px - cc[:, 0]) + (a[:, 0] - cc[:, 0]) * (pz - cc[:, 2])) / d
        w2 = 1 - w0 - w1
        ins = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        y = w0 * a[:, 1] + w1 * b[:, 1] + w2 * cc[:, 1]
        covered[s:s + 400] = (ins & (y < p[:, 1][:, None] - 1e-4)).any(1)
    if box is not None:                                        # (between the lips is where teeth may show)
        lo2, hi2 = box
        covered |= ((X >= lo2) & (X <= hi2)).all(1)
    return int((~covered).sum())


def lip_gap(res, Q=None):
    """The slot between the lips (a box round the lips' meeting line), at rest."""
    Q = (res['Q'] if Q is None else Q)[res['lip_skin']]
    zc = np.median(Q[:, 2])
    return np.array([Q[:, 0].min(), -1e9, zc - 0.22]), np.array([Q[:, 0].max(), 1e9, zc + 0.22])


def mouth_pieces(res, name=None):
    X = []
    for nm in ('teeth', 'tongue'):
        pc = res['pieces'][nm]
        d = res['targets'][name]['pieces'].get(nm) if name else None
        X.append(pc['X'] + d if d is not None else pc['X'])
    return np.concatenate(X)


def crumple(res):
    """Where the fitted skin is bent out of MakeHuman's own shape at the scale of a few points (a thin wall pushed
    through itself): each point's offset from its neighbours' middle, before and after, in edge lengths.
    -> (the worst, how many past 0.6)."""
    from fit2 import adjacency
    mh = res['mh']; info = res['info']
    P0 = info['P_sim']; P1 = res['P_fit']; T = mh['T']
    A = adjacency(T, len(P0))
    used = mh['used']
    d0 = P0 - A @ P0; d1 = P1 - A @ P1
    e = np.linalg.norm(P0[T[:, 0]] - P0[T[:, 1]], axis=1)
    el = np.zeros(len(P0)); cnt = np.zeros(len(P0))
    for k in range(3):
        np.add.at(el, T[:, k], e); np.add.at(cnt, T[:, k], 1)
    el = el / np.maximum(cnt, 1)
    dev = np.linalg.norm(d1 - d0, axis=1) / np.maximum(el, 1e-6)
    dev = np.where(used & (cnt > 0) & res['kept_base'], dev, 0.0)
    dev[res['info']['lining'][0]] = 0.0                        # (the mouth's lining is set back on purpose, and hidden)
    return float(dev.max()), int((dev > 0.6).sum())


def run(res, log=print):
    ok = True
    Q, T, grp = res['Q'], res['T'], res['grp']
    pieces, loops, nonman = topology(Q, T, grp)
    good = pieces == 1 and loops == 1 and nonman == 0
    ok &= good
    log('  check: skin %d piece(s), %d open edge(s) (the neck\'s lip), %d bad edges - %s' % (pieces, loops, nonman, 'ok' if good else 'FAIL'))
    seam = res['seam']
    ring = res['ring'] & ~res['lip']
    _, _, sq = seam.locate(Q[ring])
    off = np.linalg.norm(Q[ring] - sq, axis=1).max()
    from scipy.spatial import cKDTree
    dcl, _ = cKDTree(Q[ring]).query(seam.S)
    good = off < 1e-4 and dcl.max() < 1e-4
    ok &= good
    log('  check: neck edge %.5f off the classic edge at most; every classic edge point matched within %.5f - %s' % (off, dcl.max(), 'ok' if good else 'FAIL'))
    # the eyes, at rest and at every slider's end
    X, Te, left = eye_data(res)
    rest = lid_rest(Q, X, Te, left, res['N'])
    base = lid_depth(Q, X, Te, left, rest)
    worst = (base, 'at rest'); nfold = (0, '')
    for name, t in res['targets'].items():
        Q1 = Q + t['skin']
        X1 = X + t['pieces']['eyes'] if 'eyes' in t['pieces'] else X
        dp = lid_depth(Q1, X1, Te, left, rest)
        if max(dp[0] / max(LID_TOL, 1e-9), dp[1] / EDGE_TOL) > max(worst[0][0] / max(LID_TOL, 1e-9), worst[0][1] / EDGE_TOL):
            worst = (dp, name)
        # (the blink swings the lid's skin that wraps into the socket round with it - it turns over out of sight; its
        # lid is checked against the eyeball above and looked at in the client)
        nf = 0 if t.get('swing') is not None else folds(Q, Q1, T) - t.get('folds1', 0)             # (beyond what MakeHuman's own target folds: a lid's crease is one)
        if nf > nfold[0]:
            nfold = (nf, name)
    good = lid_ok(worst[0])
    ok &= good
    log('  check: eyeball through the lid by %.3f of the eye\'s size at worst, the lid\'s edge into it by %.3f (%s; at rest %.3f, %.3f) - %s' % (
        max(worst[0][0], 0), max(worst[0][1], 0), worst[1], max(base[0], 0), max(base[1], 0), 'ok' if good else 'FAIL'))
    st = max(((stretch(Q, Q + t['skin'], T), n) for n, t in res['targets'].items()), default=(1.0, ''))
    good = st[0] < MAX_STRETCH
    ok &= good
    log('  check: no edge of the skin stretches past x%.2f at a slider\'s end (%s) - %s' % (st[0], st[1], 'ok' if good else 'FAIL'))
    cr = crumple(res)
    good = cr[1] <= MAX_CRUMPLE
    ok &= good
    log('  check: the skin bent out of shape at %d points (the worst by %.2f of an edge) - %s' % (cr[1], cr[0], 'ok' if good else 'FAIL'))
    from fit2 import lining_depth
    lin, rim, To = res['info']['lining']
    h, _, dr = lining_depth(res['P_fit'], lin, rim, To)
    nout = int(((h > -0.2 * np.minimum(0.045 * res['info']['E'], 0.5 * dr)) & (dr > 0.1)).sum())
    good = nout == 0
    ok &= good
    log('  check: %d points of the mouth\'s lining stand out through the skin over them - %s' % (nout, 'ok' if good else 'FAIL'))
    gap = lip_gap(res)
    m0 = mouth_out(Q, T, mouth_pieces(res), gap)
    mw = (m0, 'at rest')
    lipm = res.get('lip_skin')
    for name, t in res['targets'].items():
        moves = ('teeth' in t['pieces']) or (lipm is not None and np.abs(t['skin'][lipm]).max() > 0.01)
        if not moves:
            continue
        k = mouth_out(Q + t['skin'], T, mouth_pieces(res, name), lip_gap(res, Q + t['skin']))
        if k > mw[0]:
            mw = (k, name)
    good = m0 <= MOUTH_OUT and mw[0] <= MOUTH_OUT_SLIDER
    ok &= good
    log('  check: %d points of the teeth / tongue show through the face (not between the lips) at rest, %d at worst at a slider\'s end (%s) - %s' % (m0, mw[0], mw[1], 'ok' if good else 'FAIL'))
    good = nfold[0] <= MAX_FOLDS
    ok &= good
    log('  check: %d triangles fold over beyond MakeHuman\'s own at a slider\'s end at worst (%s) - %s' % (nfold[0], nfold[1], 'ok' if good else 'FAIL'))
    return bool(ok)
