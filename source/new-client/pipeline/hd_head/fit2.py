"""The whole-head fit (v2): MakeHuman's head set to a race's size and proportions - nothing pinned to the classic
surface's detail, the eyes / ears / mouth each kept whole (moved, turned and scaled as one piece).

1. landmarks on both heads -> move, turn, scale; a soft (regularised) bend for the proportions;
2. a coarse pull onto the classic skin (the skull, cheeks, jaw; the scalp closely - hair and helms were made for it);
3. the eye, ear and mouth units set back to MakeHuman's own shape (a similarity fitted to the skin round each).
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix, diags
import mh2
from mhbase import TO_FIG, tris, read_target
from landmarks import common, sphere_fit

FIT_NAMES = ['eyeL', 'eyeR', 'mouthL', 'mouthR', 'nose', 'chin', 'top', 'back', 'browL', 'browR', 'jawL', 'jawR']


def similarity(A, B, w=None):
    """s, R, t with B ~ s R A + t (Umeyama, weighted)."""
    w = np.ones(len(A)) if w is None else w
    w = w / w.sum()
    ma, mb = (A * w[:, None]).sum(0), (B * w[:, None]).sum(0)
    a, b = A - ma, B - mb
    U, S, Vt = np.linalg.svd((b * w[:, None]).T @ a)
    D = np.eye(3)
    if np.linalg.det(U @ Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / ((a ** 2).sum(1) * w).sum()
    return s, R, mb - s * R @ ma


def tps(src, dst, reg=0.0):
    n = len(src)
    K = np.linalg.norm(src[:, None] - src[None], axis=2)
    Pm = np.c_[np.ones(n), src]
    A = np.zeros((n + 4, n + 4))
    A[:n, :n] = K - reg * np.eye(n)          # (r is conditionally negative definite in 3D)
    A[:n, n:] = Pm
    A[n:, :n] = Pm.T
    b = np.zeros((n + 4, 3))
    b[:n] = dst - src
    x = np.linalg.solve(A, b)
    w, aff = x[:n], x[n:]
    def f(Q):
        Kq = np.linalg.norm(Q[:, None] - src[None], axis=2)
        return Q + Kq @ w + np.c_[np.ones(len(Q)), Q] @ aff
    return f


def adjacency(T, n):
    r = np.r_[T[:, 0], T[:, 1], T[:, 2], T[:, 1], T[:, 2], T[:, 0]]
    c = np.r_[T[:, 1], T[:, 2], T[:, 0], T[:, 0], T[:, 1], T[:, 2]]
    A = coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel()
    return diags(1.0 / np.maximum(deg, 1)) @ A


def vnormals(P, T):
    n = np.zeros_like(P)
    f = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], f)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def dense(P, T, n=5):
    bs = np.array([(i / n, j / n, 1 - i / n - j / n) for i in range(n + 1) for j in range(n + 1 - i)])
    Q = np.einsum('kb,tbd->tkd', bs, P[T]).reshape(-1, 3)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    return Q, np.repeat(fn, len(bs), axis=0), np.repeat(np.arange(len(T)), len(bs))


def mh_head(sex):
    """MakeHuman's head in figure axes: its points, the skin's quads from the chest up, the joints, the ear / eye sets."""
    V, VT, F, FT, FG = mh2.base()
    Vm = mh2.macro(sex)
    P = Vm @ TO_FIG.T
    jc = {j: P[mh2.group_verts(j)].mean(0) for j in ('joint-head', 'joint-neck', 'joint-l-eye', 'joint-r-eye')}
    body = np.array([g == 'body' for g in FG])
    zc = jc['joint-neck'][2] - 1.1
    keepF = np.array([body[k] and P[F[k], 2].min() > zc and np.abs(P[F[k], 0]).max() < 1.6 for k in range(len(F))])
    T, TT = tris(F, FT, keep=keepF)
    used = np.zeros(len(P), bool); used[np.unique(T)] = True
    head = used & (P[:, 2] > jc['joint-neck'][2] - 0.35)
    eyes = {}
    for sd, gn in (('L', 'helper-l-eye'), ('R', 'helper-r-eye')):
        eyes[sd] = sphere_fit(P[mh2.group_verts(gn)])
    ear = {}
    for sd in 'LR':                                              # (the ear itself: what its own shape targets move)
        m = np.zeros(len(P))
        for nm in ('wing-incr', 'wing-decr'):
            i, d = read_target('ears/%s-ear-%s.target' % (sd.lower(), nm))
            mg = np.linalg.norm(d, axis=1)
            m[i[mg > 0.05 * mg.max()]] = 1.0
        ear[sd] = m
    return dict(V=Vm, P=P, T=T, TT=TT, VT=VT, used=used, head=head, jc=jc, eyes=eyes, ear=ear, keepF=keepF)


def mh_landmarks(mh):
    P, head = mh['P'], mh['head']
    eL, eR = mh['eyes']['L'], mh['eyes']['R']
    i, d = read_target('mouth/mouth-angles-up.target')
    mag = np.linalg.norm(d, axis=1)
    out = {}
    for k, sg in (('mouthL', 1), ('mouthR', -1)):
        s = (P[i, 0] * sg > 0)
        out[k] = P[i[s][np.argsort(-mag[s], kind='stable')[:4]]].mean(0)
    E = np.linalg.norm(eL[0] - eR[0])
    front = head & (P[:, 1] < eL[0][1] + 0.6 * E)
    L = common(P, eL[0], eR[0], out['mouthL'], out['mouthR'], front, head)
    return L


def eye_front(L, rL, rR):
    """The landmarks with each eye's front point in place of its centre (a small eye set forward and a large one set
    deep show at the same place)."""
    L = dict(L)
    L['eyeL'] = L['eyeL'] + np.array([0, -rL, 0]); L['eyeR'] = L['eyeR'] + np.array([0, -rR, 0])
    return L


def classic_ears(cP, cT, P_fit, T, L, E):
    """The classic skin's ear points: what stands out past the fitted head's side. -> bool per classic point."""
    Q, QN, _ = dense(P_fit, T, 4)
    d, j = cKDTree(Q).query(cP)
    out = ((cP - Q[j]) * QN[j]).sum(1)
    em = (L['eyeL'] + L['eyeR']) / 2
    side = (np.abs(cP[:, 0]) > 0.55 * np.abs(cP[:, 0]).max()) | (np.abs(cP[:, 0]) > 1.0 * E)
    return side & (d > 0.3) & (out > 0.2) & (cP[:, 1] > em[1] + 0.6 * E) & (cP[:, 2] > em[2] - 1.3 * E) & (cP[:, 2] < em[2] + 1.8 * E)


def mouth_lining(mh):
    """The mouth's lining (the bag behind the lips, up behind the nose and down the throat): a piece of its own in
    MakeHuman's texture layout. -> (its points that no outer skin uses, its rim points on the lips, the outer skin's
    triangles)."""
    from hd_layout import islands
    V, VT, F, FT, FG = mh2.base()
    corners, lab = islands(F, FT, mh['keepF'])
    cl = dict(zip(corners.tolist(), lab.tolist()))
    T, TT, P = mh['T'], mh['TT'], mh['P']
    tl = np.array([cl[int(t[0])] for t in TT])
    main = np.bincount(tl).argmax()
    # the lining: the piece (not the main one) whose middle lies nearest the mouth, inside the head
    i, d = read_target('mouth/mouth-angles-up.target')
    mouth = P[i].mean(0)
    best, bd = None, 1e9
    for k in np.unique(tl):
        if k == main:
            continue
        c = P[T[tl == k]].mean((0, 1))
        dd = np.linalg.norm(c - mouth)
        if dd < bd:
            best, bd = k, dd
    in_l = np.zeros(len(P), bool); in_l[np.unique(T[tl == best])] = True
    in_o = np.zeros(len(P), bool); in_o[np.unique(T[tl != best])] = True
    return np.flatnonzero(in_l & ~in_o), np.flatnonzero(in_l & in_o), T[tl == main]


def lining_depth(P, lin, rim, To):
    """Each lining point: how far behind the outer skin it lies (< 0 behind), and how far behind it has to be at
    least (nothing at the lips' rim, more with distance from it)."""
    Q, QN, _ = dense(P, To, 4)
    _, j = cKDTree(Q).query(P[lin])
    h = ((P[lin] - Q[j]) * QN[j]).sum(1)
    dr, _ = cKDTree(P[rim]).query(P[lin])
    return h, QN[j], dr


def fit(mh, cP, cT, cskin, Lc, eye_r, body=None, reg=0.6, log=print):
    """-> the head's points in the figure's frame, and what was done (scale, turn, the units' similarities)."""
    P0 = mh['P']; T = mh['T']; n = len(P0)
    Lm = eye_front(mh_landmarks(mh), mh['eyes']['L'][1], mh['eyes']['R'][1])
    Lr = eye_front(Lc, eye_r, eye_r)
    src = np.array([Lm[k] for k in FIT_NAMES]); dst = np.array([Lr[k] for k in FIT_NAMES])
    s, R, t = similarity(src, dst)
    sim = lambda Q: (s * (R @ Q.T)).T + t
    P1 = sim(P0)
    E = np.linalg.norm(Lc['eyeL'] - Lc['eyeR'])
    f = tps(sim(src), dst, reg=reg * E)
    used = mh['used']
    P2 = P1.copy(); P2[used] = f(P1[used])
    log('  fit: scale %.3f, landmarks off by %.2f after the move, %.2f after the bend (of the eyes\' spacing %.2f)' % (
        s, np.linalg.norm(sim(src) - dst, axis=1).mean(), np.linalg.norm(f(sim(src)) - dst, axis=1).mean(), E))
    # the units kept whole: weights per point (1 inside, fading out)
    unit_w = {}
    for sd in 'LR':
        c, r = mh['eyes'][sd]
        dm = np.linalg.norm(P0 - c, axis=1) / r
        unit_w['eye' + sd] = np.clip((3.0 - dm) / 1.0, 0, 1)
        unit_w['ear' + sd] = mh['ear'][sd].copy()
    # the lips: kept whole too (closed as MakeHuman's are - pulled onto the classic mouth they parted)
    lip = np.zeros(n)
    for nm in ('mouth/mouth-upperlip-volume-incr', 'mouth/mouth-lowerlip-volume-incr'):
        i, d = read_target(nm + '.target'); mg = np.linalg.norm(d, axis=1)
        lip[i[mg > 0.15 * mg.max()]] = 1.0
    unit_w['lips'] = lip
    # the nose's end (tip, nostrils, their insides): whole as well - its thin walls crumpled under the pull, and a bit
    # of a nostril's inside came out through its wing (owner's check build, the Briton woman)
    nose = np.zeros(n)
    for nm in ('nose/nose-nostrils-width-incr', 'nose/nose-flaring-incr', 'nose/nose-nostrils-angle-up', 'nose/nose-point-up',
               'nose/nose-point-width-incr'):                # (targets the sliders use too: they ship with the pipeline)
        i, d = read_target(nm + '.target'); mg = np.linalg.norm(d, axis=1)
        nose[i[mg > 0.3 * mg.max()]] = 1.0
    unit_w['nose'] = nose
    A = adjacency(T, n)
    for k in ('earL', 'earR', 'lips', 'nose'):                           # (the ear's root with it: a ring or two of the skull)
        w = unit_w[k]
        for _ in range(3):
            w = np.maximum(w, 0.75 * (A @ w))
        unit_w[k] = w
    held = np.clip(sum(unit_w.values()), 0, 1)
    # 2. the coarse pull onto the classic skin (without its ears)
    Ts = cT[cskin[cT].all(1)]
    ears_c = classic_ears(cP, Ts, P2, T, Lc, E)
    Tn = Ts[~ears_c[Ts].any(1)]
    Q, QN, _ = dense(cP, Tn)
    if body is not None:                                         # (the body past the head's edge: the shoulders land on it)
        Qb, QNb, _ = dense(body[0], body[1])
        Q = np.r_[Q, Qb]; QN = np.r_[QN, QNb]
    tree = cKDTree(Q)
    em = (Lc['eyeL'] + Lc['eyeR']) / 2
    mm = (Lc['mouthL'] + Lc['mouthR']) / 2
    P = P2.copy()
    # how closely each part follows: the scalp and the back of the head all the way, the face only coarsely, the
    # neck all the way (it meets the body)
    zb = Lc['browL'][2] + 0.25 * E
    scalp = np.clip((P[:, 2] - zb) / (0.5 * E), 0, 1)
    scalp = np.maximum(scalp, np.clip((P[:, 1] - (em[1] + 1.2 * E)) / (0.6 * E), 0, 1))
    neck = np.clip(((Lc['chin'][2] - 0.2 * E) - P[:, 2]) / (0.6 * E), 0, 1) * np.clip((P[:, 1] - (Lc['chin'][1] + 0.5 * E)) / (0.5 * E), 0, 1)
    neck = np.maximum(neck, np.clip(((Lc['chin'][2] - 1.0 * E) - P[:, 2]) / (0.5 * E), 0, 1))
    close = np.maximum(scalp, neck)
    for iters, part in ((40, None), (24, None), (14, close), (8, close), (5, close)):
        N = vnormals(P, T)
        d, idx = tree.query(P[used])
        cosn = (N[used] * QN[idx]).sum(1)
        w = np.zeros(n)
        w[used] = np.clip((cosn - 0.3) / 0.4, 0, 1) * (1 - held[used])
        if part is not None:
            w *= part
        D = np.zeros_like(P)
        D[used] = (Q[idx] - P[used]) * w[used, None]
        for _ in range(iters):
            D = 0.5 * D + 0.5 * (A @ D)
            w = 0.5 * w + 0.5 * (A @ w)
        if part is not None:
            g = part.copy()
            for _ in range(iters):
                g = 0.5 * g + 0.5 * (A @ g)
            D = D / np.maximum(w, 1e-6)[:, None] * np.clip(g, 0, 1)[:, None]
        else:
            D = D / np.maximum(w, 1e-6)[:, None]
        P[used] += D[used]
    # 3. each unit back to MakeHuman's own shape: the similarity that best carries it to where the skin round it went
    units = {}
    for k, w in unit_w.items():
        core = w > 0.999
        ring = used & (w > 0.02) & ~core
        both = used & (w > 0.02)
        ww = np.where(core[both], 0.35, 1.0)                      # (the skin round it leads; the unit itself follows)
        su, Ru, tu = similarity(P0[both], P[both], ww)
        Pu = (su * (Ru @ P0.T)).T + tu
        P = P + (Pu - P) * w[:, None]
        units[k] = (su, Ru, tu)
        log('  %s: kept whole, x%.3f of MakeHuman\'s size (%d points)' % (k, su / s, core.sum()))
    # the mouth's lining stays behind the skin over it (the skin beside the nose went back onto the classic face and
    # a corner of the lining stood out through it - the owner's check build, the Briton woman)
    lin, rim, To = mouth_lining(mh)
    moved = 0
    for _ in range(4):
        h, n_, dr = lining_depth(P, lin, rim, To)
        want = -np.minimum(0.045 * E, 0.5 * dr)
        m_ = h > want
        P[lin[m_]] += ((want - h)[m_])[:, None] * n_[m_]
        moved = max(moved, int(m_.sum()))
    log('  the mouth\'s lining: %d of its %d points set back behind the skin' % (moved, len(lin)))
    # the mouth's inside (teeth, tongue): the lips' and jaw's similarity
    md = np.linalg.norm(P0 - (Lm['mouthL'] + Lm['mouthR']) / 2, axis=1)
    mE = np.linalg.norm(mh['eyes']['L'][0] - mh['eyes']['R'][0])
    mw = used & (md < 0.9 * mE)
    units['mouth'] = similarity(P0[mw], P[mw])
    return P, dict(s=s, R=R, t=t, units=units, unit_w=unit_w, E=E, ears_c=ears_c, Lm=Lm, Lr=Lr, P_sim=P1, sim=sim, held=held,
                   lining=(lin, rim, To))
