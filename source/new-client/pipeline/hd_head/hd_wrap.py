"""The HD head (the character creator plan, phase 2): MakeHuman's CC0 head wrapped onto a race's classic head.

1. Landmarks (landmarks.py) on both heads; the MH head moved, turned and scaled onto them, then bent onto them (a
   thin-plate warp).
2. Low-frequency projection: each MH point's way to the classic skin, smoothed over the MH mesh, applied; again,
   finer each time. The head takes the race's shape - its skull, nose, jaw, cheekbones - while what is finer than
   about a centimetre stays MakeHuman's: the eyelids, the lips' edges, the nostrils, the ear's rim.
3. The eyelids fitted round the race's own eyeballs (kept, with their texture); the neck cut along the classic
   head's neck edge and welded to it exactly.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix, diags
from mhbase import read_obj, apply_target, TO_FIG, tris
from landmarks import mh_landmarks, race_landmarks, NAMES

_OBJ = None


def mh_head(sex):
    global _OBJ
    if _OBJ is None:
        _OBJ = read_obj()
    V, VT, F, FT, FG = _OBJ
    W = apply_target(V, f'macrodetails/caucasian-{sex}-young.target')
    P = W @ TO_FIG.T
    jc = {}
    for jn in ('joint-head', 'joint-neck', 'joint-l-eye', 'joint-r-eye', 'joint-jaw'):
        ks = [k for k, g in enumerate(FG) if g == jn]
        jc[jn] = P[np.unique(np.concatenate([F[k] for k in ks]))].mean(0)
    body = np.array([g == 'body' for g in FG])
    zc = jc['joint-neck'][2] - 0.35
    keepF = np.array([body[k] and P[F[k], 2].min() > zc for k in range(len(F))])
    return dict(P=P, V0=V, F=F, FT=FT, VT=VT, keepF=keepF, jc=jc)


def similarity(A, B):
    """s, R, t with B ~ s R A + t (Umeyama)."""
    ma, mb = A.mean(0), B.mean(0)
    a, b = A - ma, B - mb
    U, S, Vt = np.linalg.svd(b.T @ a / len(A))
    D = np.eye(3)
    if np.linalg.det(U @ Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / (a ** 2).sum(1).mean()
    return s, R, mb - s * R @ ma


def tps(src, dst, reg=0.0):
    """A 3D thin-plate (biharmonic, r) warp taking src to dst; returns f(points)."""
    n = len(src)
    K = np.linalg.norm(src[:, None] - src[None], axis=2)
    Pm = np.c_[np.ones(n), src]
    A = np.zeros((n + 4, n + 4))
    A[:n, :n] = K + reg * np.eye(n)
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


def adjacency(F, keepF, n):
    r, c = [], []
    for k in np.flatnonzero(keepF):
        f = F[k]
        for j in range(len(f)):
            r += [f[j], f[(j + 1) % len(f)]]
            c += [f[(j + 1) % len(f)], f[j]]
    A = coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel()
    return diags(1.0 / np.maximum(deg, 1)) @ A, deg > 0


def vertex_normals_simple(P, T):
    n = np.zeros_like(P)
    f = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], f)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def dense_surface(P, T, n=5):
    """Points over the triangles (a barycentric grid), for closest-point lookups."""
    bs = []
    for i in range(n + 1):
        for j in range(n + 1 - i):
            bs.append((i / n, j / n, 1 - i / n - j / n))
    bs = np.array(bs)
    Q = np.einsum('kb,tbd->tkd', bs, P[T]).reshape(-1, 3)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    return Q, np.repeat(fn, len(bs), axis=0)


def wrap(mh, race_P, race_T, skin_mask, L_race, keep_ears=True, passes=((40, 1.0), (24, 1.0), (14, 1.0), (9, 1.0), (7, 1.0))):
    P = mh['P'].copy()
    n = len(P)
    A, used = adjacency(mh['F'], mh['keepF'], n)
    L_mh = mh_landmarks(P, used, mh['jc'])
    src = np.array([L_mh[k] for k in NAMES]); dst = np.array([L_race[k] for k in NAMES])
    s, R, t = similarity(src, dst)
    P = (s * (R @ P.T)).T + t
    src2 = (s * (R @ src.T)).T + t
    f = tps(src2, dst, reg=0.0)
    P[used] = f(P[used])
    P_tps = P.copy()
    # the eyes' region keeps MakeHuman's lids (they only follow the brow and cheek round them): the classic head's
    # socket is a different shape, and pulled onto it the lids folded
    info0 = dict(scale=s, R=R, t=t, tps=f)
    eyes0 = mh_eyes(mh, info0, used)
    keep_eye = np.zeros(len(P))
    for side in ('L', 'R'):
        dm = np.linalg.norm(P - eyes0[side][0], axis=1) / eyes0[side][1]
        keep_eye = np.maximum(keep_eye, np.clip((2.2 - dm) / 0.6, 0, 1))
    # and the ears keep MakeHuman's (the classic ear is a flat card: pulled onto it, the ear was pressed into the head)
    from mhbase import read_target
    for ef in (('ears/l-ear-scale-incr.target', 'ears/r-ear-scale-incr.target') if keep_ears else ()):
        ei, ed = read_target(ef)
        w_e = np.zeros(len(P)); w_e[ei] = np.clip(np.linalg.norm(ed, axis=1) / (0.35 * np.linalg.norm(ed, axis=1).max()), 0, 1)
        keep_eye = np.maximum(keep_eye, w_e)
    # the classic skin as dense points, each with its triangle's normal
    Ts = race_T[skin_mask[race_T].all(1)]
    Q, QN = dense_surface(race_P, Ts)
    tree = cKDTree(Q)
    Tm, _ = tris(mh['F'], keep=mh['keepF'])
    for iters, gain in passes:
        N = vertex_normals_simple(P, Tm)
        _, idx = tree.query(P[used])
        # only where the MH point faces the way the skin it lands on does: the mouth's inside and the eye pockets
        # (facing in) get no pull of their own and follow their neighbours
        cosn = (N[used] * QN[idx]).sum(1)
        w = np.zeros(len(P))
        w[used] = np.clip((cosn - 0.3) / 0.4, 0, 1) * (1 - keep_eye[used])
        D = np.zeros_like(P)
        D[used] = (Q[idx] - P[used]) * w[used, None]
        for _ in range(iters):
            D = 0.5 * D + 0.5 * (A @ D)
            w = 0.5 * w + 0.5 * (A @ w)
        D = D / np.maximum(w, 1e-6)[:, None]
        P[used] += gain * D[used]
    return P, used, dict(scale=s, R=R, t=t, L_mh=L_mh, tps=f, P_tps=P_tps, L_race=L_race)


def mh_eyes(mh, info, used):
    """The MH eyeballs' spheres after the same move and warp (each side: centre, radius)."""
    from landmarks import sphere_fit
    V, VT, F, FT, FG = _OBJ
    out = {}
    for side, grpn in (('L', 'helper-l-eye'), ('R', 'helper-r-eye')):
        ks = [k for k, g in enumerate(FG) if g == grpn]
        vv = np.unique(np.concatenate([F[k] for k in ks]))
        Q = (info['scale'] * (info['R'] @ mh['P'][vv].T)).T + info['t']
        Q = info['tps'](Q)
        out[side] = sphere_fit(Q)
    return out


def space_smooth(P, D, sigma):
    tree = cKDTree(P)
    pairs = tree.query_ball_point(P, 2.5 * sigma)
    out = np.zeros_like(D)
    for i, nb in enumerate(pairs):
        nb = np.asarray(nb)
        w = np.exp(-((P[nb] - P[i]) ** 2).sum(1) / (sigma * sigma))
        out[i] = (D[nb] * w[:, None]).sum(0) / w.sum()
    return out


def neck_seam(race_P, race_T, skin, grp):
    """The classic head's neck edge (its open loop), as points round the neck, ordered by angle."""
    from headio import boundary_loops
    Ts = race_T[skin[race_T].all(1)]
    loops = boundary_loops(Ts, grp)
    Pg = np.zeros((grp.max() + 1, 3)); Pg[grp] = race_P
    L = min(loops, key=lambda l: Pg[l][:, 2].mean())                  # (the lowest loop: the neck)
    S = Pg[L]
    c = S.mean(0)
    th = np.arctan2(S[:, 1] - c[1], S[:, 0] - c[0])
    o = np.argsort(th)
    return S[o], th[o], c, np.array(L)[o]


def seam_at(S, th, c, q_th):
    """The seam's point at these angles (linear along the loop, wrapping round)."""
    th2 = np.r_[th[-1] - 2 * np.pi, th, th[0] + 2 * np.pi]
    S2 = np.r_[S[-1:], S, S[:1]]
    out = np.zeros((len(q_th), 3))
    for k in range(3):
        out[:, k] = np.interp(q_th, th2, S2[:, k])
    return out


def finish(mh, P, used, info, race_P, race_T, parts, grp_race):
    """Lips and lids together, the lids clear of the eyeballs, the neck cut on the classic seam."""
    P = P.copy()
    # 1. the whole wrap's move, smoothed through space as well (the upper and lower lip, the lids, the ear's two
    #    sides move as one where they touch)
    D = P[used] - info['P_tps'][used]
    P[used] = info['P_tps'][used] + space_smooth(info['P_tps'][used], D, 0.22)
    # 2. the eyes: the classic eyeballs grown to the MH pocket, the lids kept just clear of them
    eyes = mh_eyes(mh, info, used)
    rings = {}
    for side in ('L', 'R'):
        # the race's own eyeball, where its bone turns it (owner 2026-11-25: moved into MakeHuman's socket, it swung out
        # through the lid as the eye turned) - the lids fit round it there
        c_r = info['L_race']['eye' + side]
        r_mh = eyes[side][1]
        # the race's own eyeball size, a touch bigger at most (owner 2026-11-25: grown to MakeHuman's it was too big -
        # the elves' poked out of the corners)
        r = min(r_mh, parts['eye_r'] * 1.12)
        # its front no further forward than MakeHuman's eye's (the elves' sit forward of the new socket: they bulged
        # through the lids)
        fwd = max(0.0, -(c_r - eyes[side][0])[1])
        r = min(r, r_mh - 1.5 * fwd)
        # no bigger than the skin beside the eye's outer corner allows (the elves' narrow faces: it poked through)
        dmx = np.linalg.norm(info['P_tps'] - eyes[side][0], axis=1) / r_mh
        outward = (P[:, 0] - c_r[0]) * np.sign(c_r[0]) > 0.3 * r_mh
        ring = used & outward & (dmx > 1.3) & (dmx < 2.6)
        if ring.any():
            r = min(r, 0.93 * float(np.percentile(np.linalg.norm(P[ring] - c_r, axis=1), 2)))
        # the lids and socket drawn in round the smaller eye (owner 2026-11-25: the elves' - MakeHuman's opening stayed
        # its own size and the eye's side showed), fading out round it
        if r < r_mh:
            dm0 = np.linalg.norm(info['P_tps'] - eyes[side][0], axis=1) / r_mh
            dP = P - c_r
            k_in = 1 - (1 - r / r_mh) * np.clip((2.3 - dm0) / 1.0, 0, 1) * used
            P = c_r + dP * k_in[:, None]
        d = P - c_r
        dist = np.linalg.norm(d, axis=1)
        # which is pocket and which is lid: inside MakeHuman's own eyeball (before the wrap) is the pocket
        dm = np.linalg.norm(info['P_tps'] - eyes[side][0], axis=1) / r_mh
        near = used & (dm < 1.3)
        inner = near & (dm < 0.995)
        outer = near & ~inner
        # the eyeball no bigger than the skin round the lids lets it be (a race whose face lies closer over the eye -
        # the Shar - had it bulge through beside the socket)
        # (no fit of the eyeball to the skin round it: it shrank the Lurikeen's eyes shut - the Shar, whose eyes need
        # it, wait for their own fix)
        A_eye, _ = adjacency(mh['F'], mh['keepF'], len(P))
        lid = near & (dm > 0.9) & (dm < 1.3)
        for it in range(14):
            d = P - c_r
            dist = np.linalg.norm(d, axis=1)
            m = outer & (dist < r * 1.02)
            P[m] = c_r + d[m] / dist[m, None] * r * 1.02              # the lids rest on the eye, never through it
            m = outer & (dm < 1.1) & (dist > r * 1.04)                 # and the lid's edge down onto it (no gap)
            P[m] = c_r + d[m] / dist[m, None] * r * 1.04
            # the pocket stays behind the eye, hidden: each point as far in as it was in MakeHuman's (a touch more)
            m = inner
            P[m] = c_r + d[m] / dist[m, None] * (r * 0.95 * dm[m])[:, None]
            if it < 13:                                                # (and the lids' margin relaxed between)
                Q = A_eye @ P
                P[lid] = 0.6 * P[lid] + 0.4 * Q[lid]
        rings[side] = (c_r, r, inner.copy())
    # 3. the neck: faces below the classic seam go, the new edge sits on the seam
    S, th, c, Lidx = neck_seam(race_P, race_T, parts['skin'], grp_race)
    qth = np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0])
    zs = seam_at(S, th, c, qth)[:, 2]
    above = P[:, 2] >= zs
    keepF = np.array([mh['keepF'][k] and above[mh['F'][k]].all() for k in range(len(mh['F']))])
    T, _ = tris(mh['F'], keep=keepF)
    from headio import boundary_loops
    loops = boundary_loops(T, np.arange(len(P)))
    edge = np.array(max(loops, key=len))
    tgt = seam_at(S, th, c, qth[edge])
    shift = np.zeros_like(P); shift[edge] = tgt - P[edge]
    A, usedK = adjacency(mh['F'], keepF, len(P))
    pin = np.zeros(len(P), bool); pin[edge] = True
    # the rows above the edge follow it, fading (a relaxed spread of the edge's move)
    for _ in range(25):
        shift = np.where(pin[:, None], shift, 0.5 * shift + 0.5 * (A @ shift))
    P[usedK] += shift[usedK]
    return P, usedK, keepF, T, edge, rings


def uv_islands(T, UV):
    """Each classic triangle's UV island (triangles joined where they share a UV corner)."""
    from scipy.sparse.csgraph import connected_components
    key = np.round(UV * 4096).astype(np.int64)
    _, uid = np.unique(key, axis=0, return_inverse=True)
    uid = uid.reshape(-1)
    n = len(T)
    r = np.repeat(np.arange(n), 3)
    c = uid[T].reshape(-1)
    m = uid.max() + 1
    A = coo_matrix((np.ones(len(r)), (r, c + n)), shape=(n + m, n + m))
    _, lab = connected_components(A, directed=False)
    return lab[:n]


def transfer_uv(P, T, race_P, race_T, race_UV, skin_mask, n=8):
    """UVs for the new head from the classic skin under it -> (index into P per new vertex, UV, triangles).

    Each point takes the UV of the classic point it lies on. Where a new triangle straddles a cut in the classic UVs
    (its corners' UVs much further apart than its size allows - the face and the side of the head meet at a slit),
    its odd corner takes the UV of its neighbours' classic triangle, that triangle's mapping carried on past its
    edge; such a corner is a new vertex (the seam)."""
    Ts = race_T[skin_mask[race_T].all(1)]
    bs = np.array([(i / n, j / n, 1 - i / n - j / n) for i in range(n + 1) for j in range(n + 1 - i)])
    Q = np.einsum('kb,tbd->tkd', bs, race_P[Ts]).reshape(-1, 3)
    QU = np.einsum('kb,tbd->tkd', bs, race_UV[Ts]).reshape(-1, 2)
    QT = np.repeat(np.arange(len(Ts)), len(bs))
    tree = cKDTree(Q)
    used = np.unique(T)
    _, idx = tree.query(P[used])
    vt = np.full(len(P), -1); vt[used] = QT[idx]
    vuv = np.zeros((len(P), 2)); vuv[used] = QU[idx]
    # each classic triangle's UV per unit length
    A3 = np.linalg.norm(np.cross(race_P[Ts[:, 1]] - race_P[Ts[:, 0]], race_P[Ts[:, 2]] - race_P[Ts[:, 0]]), axis=1)
    u1, u2 = race_UV[Ts[:, 1]] - race_UV[Ts[:, 0]], race_UV[Ts[:, 2]] - race_UV[Ts[:, 0]]
    A2 = np.abs(u1[:, 0] * u2[:, 1] - u1[:, 1] * u2[:, 0])
    k_uv = np.sqrt(A2 / np.maximum(A3, 1e-12))

    def through(v, k):
        a3 = race_P[Ts[k]]
        e1, e2, pv = a3[1] - a3[0], a3[2] - a3[0], P[v] - a3[0]
        G2 = np.array([[e1 @ e1, e1 @ e2], [e1 @ e2, e2 @ e2]])
        l1, l2 = np.linalg.solve(G2 + 1e-12 * np.eye(2), [pv @ e1, pv @ e2])
        bc = np.clip(np.array([1 - l1 - l2, l1, l2]), -1.0, 2.0)
        return bc @ race_UV[Ts[k]]

    verts = {}
    out_v, out_uv, out_T = [], [], []
    nseam = 0

    def vert(v, uv):
        key = (int(v), int(round(uv[0] * 20000)), int(round(uv[1] * 20000)))
        if key not in verts:
            verts[key] = len(out_v)
            out_v.append(int(v)); out_uv.append(uv)
        return verts[key]

    for t in T:
        uv = vuv[t].copy()
        ok = True
        for a, b in ((0, 1), (1, 2), (2, 0)):
            dp = np.linalg.norm(P[t[a]] - P[t[b]])
            kk = max(k_uv[vt[t[a]]], k_uv[vt[t[b]]])
            if np.linalg.norm(uv[a] - uv[b]) > 2.5 * kk * dp + 0.006:
                ok = False
        if not ok:
            nseam += 1
            # the corner the other two agree with least is the odd one; all three through the others' triangle
            # the side of the cut the triangle's middle lies on; all three corners through that side's triangle
            _, jc = tree.query(P[t].mean(0))
            ref = QT[jc]
            uv = np.array([through(v, ref) for v in t])
        out_T.append([vert(t[j], uv[j]) for j in range(3)])
    print('  uv: %d triangles across a cut' % nseam)
    return np.array(out_v), np.array(out_uv), np.array(out_T)
