"""The HD head, rebuilt (v2; owner 2026-11-25: "completely rebuild the new heads, just trying to mimic their size and
shape"): MakeHuman's whole CC0 head - skin, its own eyeballs, lashes, teeth and tongue, its own ears - set to a race's
size and proportions (fit2.py), joined to the body along the classic head's lower edge (neck2.py), written into the
race's figure.gltf as nodes of their own: "head__hd" (the skin), "head__hd_eyes", "head__hd_mouth", "head__hd_lash".
Nothing of the classic head is kept in it: no classic eyeball, ear, UV or painted feature.

    python head2.py <race folder> [<out folder>]

The face sliders are MakeHuman's targets ("hx_<slider>-" / "hx_<slider>+", hd_sliders.py): the eyeballs, lashes and
teeth follow them as MakeHuman moves its own (they are bound to its mesh), so the lids and the eye can't part.
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))
from headio import G, load_head, bones, weld
from landmarks import race_landmarks
from mhbase import read_target, TO_FIG, tris, MH
from hd_sliders import FEATURES, SLIDERS, gain
import mh2, fit2, neck2, ear2
from hd_layout import layout

LONG_EAR = 1.3                          # a classic ear this much longer than MakeHuman's: the ear is drawn out to it
LONG_EARED = ('elf', 'lur', 'inc', 'fro', 'fir')    # ... for the races whose ears are their look (a human's stay MakeHuman's)
HAIR_REACH = 2.6
EYE_FIT = 0.975
SKIRT = 0.25                            # the lip tucked under the body's edge (hides any hairline gap) ...
SKIRT_IN = 0.4                          # ... and this far in under the body's skin (level with it, the two flickered)
EYES = (str(Path(MH).parent / 'data') if False else MH)   # (the high-poly eyes ship with MakeHuman itself)


def log(*a):
    print(*a); sys.stdout.flush()


# ---- glTF helpers (as hd_head.py) ---------------------------------------------------------------------------------
def add_acc(g, arr, comp, typ, target=None, minmax=False):
    arr = np.ascontiguousarray(arr, {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[comp])
    data = arr.tobytes()
    g.g['buffers'].append({'byteLength': len(data)})
    g.b.append(bytearray(data))
    bv = {'buffer': len(g.b) - 1, 'byteOffset': 0, 'byteLength': len(data)}
    if target:
        bv['target'] = target
    g.g['bufferViews'].append(bv)
    a = {'bufferView': len(g.g['bufferViews']) - 1, 'componentType': comp, 'count': len(arr), 'type': typ}
    if minmax:
        a['min'] = arr.reshape(len(arr), -1).min(0).tolist(); a['max'] = arr.reshape(len(arr), -1).max(0).tolist()
    g.g['accessors'].append(a)
    return len(g.g['accessors']) - 1


def _sparse_one(g, idx, vals, count):
    idx = np.ascontiguousarray(idx, np.uint32); vals = np.ascontiguousarray(vals, np.float32)
    data = idx.tobytes() + vals.tobytes()
    g.g['buffers'].append({'byteLength': len(data)})
    g.b.append(bytearray(data))
    bi = len(g.b) - 1
    g.g['bufferViews'].append({'buffer': bi, 'byteOffset': 0, 'byteLength': idx.nbytes})
    iv = len(g.g['bufferViews']) - 1
    g.g['bufferViews'].append({'buffer': bi, 'byteOffset': idx.nbytes, 'byteLength': vals.nbytes})
    vv = len(g.g['bufferViews']) - 1
    lo = np.minimum(vals.min(0), 0).tolist(); hi = np.maximum(vals.max(0), 0).tolist()
    g.g['accessors'].append({'componentType': 5126, 'count': int(count), 'type': 'VEC3', 'min': lo, 'max': hi,
                             'sparse': {'count': int(len(idx)), 'indices': {'bufferView': iv, 'componentType': 5125},
                                        'values': {'bufferView': vv}}})
    return len(g.g['accessors']) - 1


def add_sparse(g, d, dn=None, eps=1e-5):
    moved = np.flatnonzero(np.abs(d).max(1) > eps)
    if dn is not None:
        moved = np.union1d(moved, np.flatnonzero(np.abs(dn).max(1) > eps * 20))
    if len(moved) == 0:
        moved = np.array([0])
    pa = _sparse_one(g, moved, d[moved], len(d))
    na = _sparse_one(g, moved, dn[moved], len(d)) if dn is not None else _sparse_one(g, np.array([0]), np.zeros((1, 3)), len(d))
    return pa, na


def welded_normals(P, T, grp=None):
    grp = weld(P) if grp is None else grp
    n = np.zeros_like(P)
    f = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], f)
    acc = np.zeros((grp.max() + 1, 3)); np.add.at(acc, grp, n)
    n = acc[grp]
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def body_mesh(g, zmin):
    gg = g.g
    node = next(n for n in gg['nodes'] if n.get('name') == 'body' and 'mesh' in n)
    Ps, Ts, n0 = [], [], 0
    for prim in gg['meshes'][node['mesh']]['primitives']:
        P = g.acc(prim['attributes']['POSITION']).astype(float); T = g.acc(prim['indices']).astype(int).reshape(-1, 3)
        Ps.append(P); Ts.append(T + n0); n0 += len(P)
    P = np.concatenate(Ps); T = np.concatenate(Ts)
    return P, T[(P[T][:, :, 2] > zmin).all(1)]


def classic_weights(Q, cP, cT, cJ, cW, fold):
    """Each point's bones from the classic skin under it (the nearest triangle's corners, mixed); 'fold': bones
    counted as another ({from: to} - the classic lids' and eyeballs' as the head's)."""
    n = 5
    bs = np.array([(i / n, j / n, 1 - i / n - j / n) for i in range(n + 1) for j in range(n + 1 - i)])
    S = np.einsum('kb,tbd->tkd', bs, cP[cT]).reshape(-1, 3)
    _, j = cKDTree(S).query(Q)
    tid = j // len(bs); bc = bs[j % len(bs)]
    nb = int(cJ.max()) + 1
    for a, b in fold.items():
        nb = max(nb, a + 1, b + 1)
    dense = np.zeros((len(Q), nb))
    for c in range(3):
        v = cT[tid, c]
        for k in range(cJ.shape[1]):
            jj = cJ[v, k].copy()
            for a, b in fold.items():
                jj[jj == a] = b
            np.add.at(dense, (np.arange(len(Q)), jj), cW[v, k] * bc[:, c])
    return dense


def top4(dense):
    idx = np.argsort(-dense, axis=1, kind='stable')[:, :4]
    w = np.take_along_axis(dense, idx, 1)
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    idx[w <= 0] = 0
    return idx, w


def build(folder, out_folder=None):
    folder = Path(folder); prefix = folder.name.replace('src_', '')
    sex = 'female' if prefix.endswith('_f') else 'male'
    g = G(folder / 'figure.gltf')
    h = load_head(g)
    B, names = bones(g)
    L, parts = race_landmarks(h, names)
    cP, cT = h['P'], h['T']
    cgrp = weld(cP)
    mh = fit2.mh_head(sex)
    V, VT, F, FT, FG = mh2.base()
    VT = np.asarray(VT, float)
    body = body_mesh(g, cP[:, 2].min() - 3.0)
    P, info = fit2.fit(mh, cP, cT, parts['skin'], L, parts['eye_r'], body=body, log=log)
    s, R = info['s'], info['R']
    P_unit = P.copy()
    P_fit = P.copy()
    # the ears: a long-eared race's drawn out to the classic ear's tip
    drawn = {}; drawn_q = {}
    for sd, sx in (('L', 1), ('R', -1)):
        ce = ear2.classic_ear(cP, info['ears_c'], sx)
        me = ear2.mh_ear(P, mh['ear'][sd], sx)
        if ce is None:
            continue
        d = ce['tip'] - me['c']
        reach = ((P[me['m']] - me['c']) @ (d / np.linalg.norm(d))).max()
        k = np.linalg.norm(d) / reach
        if k > LONG_EAR and prefix.startswith(LONG_EARED):
            P, q = ear2.draw_out(P, mh['T'], mh['ear'][sd], sx, ce['tip'])
            fd = ear2.free_dist(P_unit, mh['T'], mh['ear'][sd] * (P_unit[:, 0] * sx > 0))
            fr = np.clip(fd / (0.3 * me['height']), 0, 1)
            drawn[sd] = k; drawn_q[sd] = (me['m'], q, fr * fr * (3 - 2 * fr))
    log('  ears: %s' % (', '.join('%s drawn out x%.2f' % (k, v) for k, v in drawn.items()) or 'MakeHuman\'s own, as they are'))
    # ---- the neck: cut along the classic head's lower edge ---------------------------------------------------------
    S, SN, Sup, Sidx = neck2.classic_seam(cP, cT, parts['skin'], cgrp)
    seam = neck2.Seam(S, SN, Sup)
    fb, _, _ = seam.f(P)
    faceKeep = np.array([mh['keepF'][k] and (fb[F[k]] > 0).any() for k in range(len(F))])
    lay, lay_scale = layout(VT, F, FT, faceKeep)
    T, TT = tris(F, FT, keep=faceKeep)
    key, rb, rvt = {}, [], []
    Trv = np.zeros_like(T)
    for k in range(len(T)):
        for c in range(3):
            kk = (int(T[k, c]), int(TT[k, c]))
            if kk not in key:
                key[kk] = len(rb); rb.append(kk[0]); rvt.append(kk[1])
            Trv[k, c] = key[kk]
    rb = np.array(rb); rvt = np.array(rvt)
    comb, T2 = neck2.clip(P[rb], Trv, fb[rb])
    CI = np.zeros((len(comb), 4), np.int64); CW = np.zeros((len(comb), 4)); UVi = np.zeros((len(comb), 2, 2)); UVm = np.zeros((len(comb), 2, 2))
    lay_uv = np.array([lay[int(v)] for v in rvt])
    mh_uv = VT[rvt]
    ca = np.array([c[0] for c in comb]); cb = np.array([c[1] for c in comb]); ct = np.array([c[2] for c in comb])
    CI[:, 0] = rb[ca]; CI[:, 1] = rb[cb]; CW[:, 0] = 1 - ct; CW[:, 1] = ct
    UV = lay_uv[ca] * (1 - ct)[:, None] + lay_uv[cb] * ct[:, None]
    UVM = mh_uv[ca] * (1 - ct)[:, None] + mh_uv[cb] * ct[:, None]
    pos = lambda X: (X[CI] * CW[:, :, None]).sum(1)
    Q = pos(P)
    grp = weld(Q)
    top = int(np.argmax(Q[:, 2]))
    A_ = neck2.main_component(grp[T2], grp.max() + 1, grp[top])
    T2 = T2[A_]
    usedv = np.zeros(len(Q), bool); usedv[np.unique(T2)] = True
    # the open edge (welded): one ring, on the classic edge
    from collections import defaultdict
    cnt = defaultdict(list)
    for ti, t in enumerate(T2):
        for k in range(3):
            a, b = t[k], t[(k + 1) % 3]
            cnt[(min(grp[a], grp[b]), max(grp[a], grp[b]))].append((ti, k))
    open_e = [v[0] for v in cnt.values() if len(v) == 1]
    ring = np.unique(np.array([[T2[ti, k], T2[ti, (k + 1) % 3]] for ti, k in open_e]).ravel())
    si, st, sq = seam.locate(Q[ring])
    off0 = np.linalg.norm(Q[ring] - sq, axis=1).max()
    adj = np.zeros_like(Q)
    adj[ring] = sq - Q[ring]
    par = np.full(len(Q), -1.0); par[ring] = si + st
    m = len(S)
    # every classic edge point becomes a point of the new edge (the two edges then close exactly)
    newT, dropT = [], set()
    extra_CI, extra_CW, extra_UV, extra_UVM, extra_adj, extra_par = [], [], [], [], [], []
    n0 = len(Q)
    for ti, k in open_e:
        u, v, w = T2[ti, k], T2[ti, (k + 1) % 3], T2[ti, (k + 2) % 3]
        pu, pv = par[u], par[v]
        dlt = (pv - pu + m / 2) % m - m / 2                       # (the short way round)
        if abs(dlt) < 1e-9:
            continue
        ks = []
        lo, hi = (pu, pu + dlt) if dlt > 0 else (pu + dlt, pu)
        for kk in range(int(np.floor(lo)) - 1, int(np.ceil(hi)) + 2):
            if lo + 1e-6 < kk < hi - 1e-6:
                ks.append(kk)
        if not ks:
            continue
        if dlt < 0:
            ks = ks[::-1]
        chain = [u]
        for kk in ks:
            tau = (kk - pu) / dlt
            ci = np.r_[CI[u, :2], CI[v, :2]]; cw = np.r_[CW[u, :2] * (1 - tau), CW[v, :2] * tau]
            extra_CI.append(ci); extra_CW.append(cw)
            extra_UV.append(UV[u] * (1 - tau) + UV[v] * tau); extra_UVM.append(UVM[u] * (1 - tau) + UVM[v] * tau)
            p_here = (P[ci] * cw[:, None]).sum(0)
            extra_adj.append(S[kk % m] - p_here); extra_par.append(float(kk % m))
            chain.append(n0 + len(extra_CI) - 1)
        chain.append(v)
        dropT.add(ti)
        for a, b in zip(chain[:-1], chain[1:]):
            newT.append([a, b, w])
    if extra_CI:
        CI = np.r_[CI, np.array(extra_CI)]; CW = np.r_[CW, np.array(extra_CW)]
        UV = np.r_[UV, np.array(extra_UV)]; UVM = np.r_[UVM, np.array(extra_UVM)]
        adj = np.r_[adj, np.array(extra_adj)]; par = np.r_[par, np.array(extra_par)]
        T2 = np.r_[T2[[i for i in range(len(T2)) if i not in dropT]], np.array(newT, np.int64)]
    Q = pos(P)
    grp = weld(Q + adj)
    ringm = par >= 0
    # the edge's move carried a little way up the skin, fading
    ng = grp.max() + 1
    Ag = fit2.adjacency(grp[T2], ng)
    pin = np.zeros(ng, bool); pin[grp[ringm]] = True
    sh = np.zeros((ng, 3)); sh[grp[ringm]] = adj[ringm]
    for _ in range(30):
        sh = np.where(pin[:, None], sh, 0.5 * sh + 0.5 * (Ag @ sh))
    adj = np.where(ringm[:, None], adj, sh[grp])
    Q = Q + adj
    log('  neck: cut on the classic edge - %d edge points (%d of them the classic edge\'s own), %.3f off it before joining' % (
        ringm.sum(), len(extra_CI), off0))
    # the lip under the body's edge
    ring_all = np.flatnonzero(ringm & np.isin(np.arange(len(Q)), np.unique(T2)))
    ri = np.floor(par[ring_all]).astype(int) % m; rt = par[ring_all] - np.floor(par[ring_all])
    r_up = seam.at(Sup, ri, rt); r_n = seam.at(SN, ri, rt)
    r_n /= np.maximum(np.linalg.norm(r_n, axis=1, keepdims=True), 1e-12)
    lip_of = -np.ones(len(Q), int); lip_of[ring_all] = len(Q) + np.arange(len(ring_all))
    Qlip = Q[ring_all] - SKIRT * r_up - SKIRT_IN * r_n
    lipT = []
    cnt = defaultdict(list)
    for ti, t in enumerate(T2):
        for k in range(3):
            a, b = t[k], t[(k + 1) % 3]
            cnt[(min(grp[a], grp[b]), max(grp[a], grp[b]))].append((a, b))
    for v in cnt.values():
        if len(v) == 1:
            a, b = v[0]
            if lip_of[a] >= 0 and lip_of[b] >= 0:
                lipT += [[b, a, lip_of[a]], [b, lip_of[a], lip_of[b]]]
    nS0 = len(Q)
    Q = np.r_[Q, Qlip]; CI = np.r_[CI, CI[ring_all]]; CW = np.r_[CW, CW[ring_all]]
    UV = np.r_[UV, UV[ring_all]]; UVM = np.r_[UVM, UVM[ring_all]]
    par = np.r_[par, par[ring_all]]
    T2 = np.r_[T2, np.array(lipT, np.int64)]
    is_lip = np.zeros(len(Q), bool); is_lip[nS0:] = True
    ringm = par >= 0
    # only the points the triangles use
    usedv = np.zeros(len(Q), bool); usedv[np.unique(T2)] = True
    remap = -np.ones(len(Q), int); remap[usedv] = np.arange(usedv.sum())
    Q, CI, CW, UV, UVM, par, is_lip, ringm = Q[usedv], CI[usedv], CW[usedv], UV[usedv], UVM[usedv], par[usedv], is_lip[usedv], ringm[usedv]
    T2 = remap[T2]
    grp = weld(Q)
    # normals: the skin's own; on the edge the classic edge's (the light runs on across the join)
    N = welded_normals(Q, T2, grp)
    ri = np.floor(par[ringm]).astype(int) % m; rt = par[ringm] - np.floor(par[ringm])
    rn = seam.at(SN, ri, rt); N[ringm] = rn / np.maximum(np.linalg.norm(rn, axis=1, keepdims=True), 1e-12)
    # bones: from the classic skin under each point; the edge's exactly the classic edge's
    fold = {names.index(nm): names.index('Bip01 Head') for nm in ('Bip01 EyeLids', 'Bip01 L Eyeball', 'Bip01 R Eyeball') if nm in names}
    cTs = cT[parts['skin'][cT].all(1)]
    dense = classic_weights(Q, cP, cTs, h['J'], h['W'], fold)
    gv = {gid: np.flatnonzero(cgrp == gid)[0] for gid in Sidx}
    sdense = np.zeros((m, dense.shape[1]))
    for k, gid in enumerate(Sidx):
        v = gv[gid]
        for c in range(h['J'].shape[1]):
            sdense[k, fold.get(int(h['J'][v, c]), int(h['J'][v, c]))] += h['W'][v, c]
    dense[ringm] = seam.at(sdense, ri, rt)
    Jn, Wn = top4(dense)
    # how much of a slider's move each point takes: none on the edge, all of it a little way up
    f_fin, _, _ = seam.f(Q)
    fall = np.clip(f_fin / 1.2, 0, 1); fall = fall * fall * (3 - 2 * fall)
    fall[ringm] = 0.0
    # ---- the eyes, lashes, teeth and tongue: MakeHuman's own, each moved with its unit ---------------------------
    Vm = mh['V']
    prox = {'eyes': mh2.SmoothEyes(), 'lash': mh2.Proxy(mh2.PROXIES['lash']),
            'teeth': mh2.Proxy(mh2.PROXIES['teeth']), 'tongue': mh2.Proxy(mh2.PROXIES['tongue'])}
    pieces = {}
    for nm, px in prox.items():
        X0 = px.at(Vm) @ TO_FIG.T
        X = np.zeros_like(X0)
        if nm in ('eyes', 'lash'):
            for sd, sel in (('L', X0[:, 0] > 0), ('R', X0[:, 0] <= 0)):
                su, Ru, tu = info['units']['eye' + sd]
                Xs = X0[sel]
                if nm == 'eyes':                                 # (a hair smaller than its socket: slack for the sliders)
                    from landmarks import sphere_fit
                    ce, _ = sphere_fit(Xs)
                    Xs = ce + (Xs - ce) * EYE_FIT
                X[sel] = (su * (Ru @ Xs.T)).T + tu
        else:                                                 # (the teeth and tongue: with the lips, as one piece)
            su, Ru, tu = info['units']['lips']
            X = (su * (Ru @ X0.T)).T + tu
        if nm == 'eyes':
            pieces[nm] = dict(px=px, X=X, vb=np.arange(len(X)), UV=np.c_[px.UV[:, 0], 1 - px.UV[:, 1]], T=px.T)
            continue
        # split at UV seams
        kd, vb, vuv = {}, [], []
        Tp = np.zeros_like(px.T)
        for k in range(len(px.T)):
            for c in range(3):
                kk = (int(px.T[k, c]), int(px.TT[k, c]))
                if kk not in kd:
                    kd[kk] = len(vb); vb.append(kk[0]); vuv.append(px.VT[kk[1]])
                Tp[k, c] = kd[kk]
        vb = np.array(vb); vuv = np.array(vuv, float)
        uvp = np.c_[vuv[:, 0], 1 - vuv[:, 1]]
        pieces[nm] = dict(px=px, X=X[vb], vb=vb, UV=uvp, T=Tp)
    # ---- the sliders ---------------------------------------------------------------------------------------------
    def fig(d):
        return s * (R @ (d @ TO_FIG.T).T).T
    targets = {}
    import check2
    limited = []
    eye_left = pieces['eyes']['X'][:, 0] > 0
    lid_rest = check2.lid_rest(Q, pieces['eyes']['X'], pieces['eyes']['T'], eye_left, N)
    Dmh = np.zeros_like(Vm)
    for key_, label, tminus, tplus, carry in SLIDERS:
        for sign, t in (('-', tminus), ('+', tplus)):
            if not t:
                continue
            rel = [t.format(s=sd) for sd in ('l', 'r')] if '{s}' in t else [t]
            Dmh[:] = 0
            for part in rel:
                i, d = read_target(part + '.target')
                if len(i):
                    Dmh[i] += d
            k = gain(key_, sign)
            D = fig(Dmh) * k
            for sd_, (em_, q_, fr_) in drawn_q.items():      # (a drawn-out ear: moved as a whole)
                D[em_] = ear2.ear_delta(P_unit, P, em_, q_, fr_, D, key_ in ('ear_lobe', 'ear_point'))
            dS = (D[CI] * CW[:, :, None]).sum(1) * fall[:, None]
            dP = {}
            for nm, pc in pieces.items():
                dd = (pc['px'].at(Vm + Dmh) - pc['px'].at(Vm))
                dd = fig(dd) * k
                if np.abs(dd).max() > 1e-5:
                    dP[nm] = dd[pc['vb']]
            # an end pushed past MakeHuman's own that folds the skin more than its own does, or any end that sinks
            # the skin into an eye on this head, is held back to where it doesn't
            lim = 1.0
            Xe = pieces['eyes']['X']; de = dP.get('eyes')
            f1 = check2.folds(Q, Q + dS / k, T2)
            while lim > 0.15:
                Q1 = Q + lim * dS
                X1 = Xe + lim * de if de is not None else Xe
                fold_ok = (lim * k <= 1.0 or check2.folds(Q, Q1, T2) <= f1 + check2.MAX_FOLDS) and check2.stretch(Q, Q1, T2) < check2.MAX_STRETCH
                if fold_ok and check2.lid_clear(check2.lid_depth(Q1, X1, pieces['eyes']['T'], eye_left, lid_rest)):
                    break
                lim -= 0.1
            if lim < 0.999:
                limited.append('%s%s x%.1f' % (key_, sign, lim))
                dS = dS * lim; dP = {a_: b_ * lim for a_, b_ in dP.items()}
            targets[f'hx_{key_}{sign}'] = dict(skin=dS, pieces=dP, carry=carry, folds1=f1)
    if limited:
        log('  sliders held back on this head: ' + ', '.join(limited))
    # sliders together: a feature's sliders all at their ends at once (every mix of ends for the ears' three, a few
    # dozen drawn at random for the eyes') must still leave the skin whole and the eyeball behind the lids - the
    # feature's sliders are all eased back until they do
    import itertools
    rng = np.random.default_rng(11)
    feat = {f[0]: [s_[0] for s_ in f[2] if s_[2] or s_[3]] for f in FEATURES}
    Xe = pieces['eyes']['X']; Te = pieces['eyes']['T']

    scale = {}

    def moved(combo):
        Q1 = Q.copy(); X1 = Xe.copy()
        for key_, sg in combo:
            t = targets.get('hx_%s%s' % (key_, sg))
            if t is None:
                continue
            k = scale.get((key_, sg), 1.0)
            Q1 += k * t['skin']
            if 'eyes' in t['pieces']:
                X1 += k * t['pieces']['eyes']
        return Q1, X1

    def lids_about_ok(Q1, X1):
        d = check2.lid_depth(Q1, X1, Te, eye_left, lid_rest)
        return d[0] <= 0.025 and d[1] <= 0.12

    groups = [('ears', [x for x in ('ear_size', 'ear_out', 'ear_tilt') if x in feat.get('ears', [])],
               lambda Q1, X1: check2.folds(Q, Q1, T2) <= 10 and check2.stretch(Q, Q1, T2) < check2.MAX_STRETCH),
              ('eyes', feat.get('eyes', []) + ['brow_ridge', 'brow_height'], lids_about_ok)]
    for gname, keys, good in groups:
        if len(keys) <= 4:
            combos = [list(zip(keys, sg)) for sg in itertools.product('-+', repeat=len(keys))]
        else:
            combos = []
            for _ in range(60):
                pick = rng.choice(len(keys), size=min(len(keys), int(rng.integers(2, 6))), replace=False)
                combos.append([(keys[i], '-+'[int(rng.integers(0, 2))]) for i in pick])
        for _ in range(8):
            bad = [c for c in combos if not good(*moved(c))]
            if not bad:
                break
            blame = set()
            for c in bad:                                      # (the one whose leaving mends it, else all of them)
                alone = [x for x in c if good(*moved([y for y in c if y != x]))]
                blame.update(alone[:1] if alone else c)
            for ks in blame:
                scale[ks] = scale.get(ks, 1.0) * 0.9
    if scale:
        for (key_, sg), k in scale.items():
            t = targets.get('hx_%s%s' % (key_, sg))
            if t is not None:
                t['skin'] = t['skin'] * k; t['pieces'] = {a_: b_ * k for a_, b_ in t['pieces'].items()}
        log('  eased for when they\'re used together: ' + ', '.join('%s%s x%.2f' % (a_, b_, k) for (a_, b_), k in sorted(scale.items())))
    lip_skin = (info['unit_w']['lips'][CI] * CW).sum(1) > 0.5
    kept_base = np.zeros(len(P), bool); kept_base[np.unique(CI[:, :2])] = True
    kept_base &= fb > 1.5                                   # (away from the neck's join: that is reshaped on purpose)
    return dict(g=g, h=h, names=names, parts=parts, L=L, info=info, mh=mh, prefix=prefix, sex=sex, lip_skin=lip_skin,
                P_fit=P_fit, kept_base=kept_base,
                Q=Q, T=T2, UV=UV, UVM=UVM, N=N, J=Jn, W=Wn, grp=grp, ring=ringm, lip=is_lip, fall=fall,
                pieces=pieces, targets=targets, seam=seam, CI=CI, CW=CW, P_base=P, drawn=drawn, lay_scale=lay_scale)


def write(res, folder, out_folder, textures=True):
    folder, out_folder = Path(folder), Path(out_folder)
    g = res['g']; gg = g.g; h = res['h']; names = res['names']
    hnode = next(n for n in gg['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    hprim = gg['meshes'][hnode['mesh']]['primitives'][0]
    jct = gg['accessors'][hprim['attributes']['JOINTS_0']]['componentType']
    head_b = names.index('Bip01 Head')
    parent = next((n for n in gg['nodes'] if gg['nodes'].index(hnode) in n.get('children', [])), None)

    def add_node(name, P, N, UV, J, W, T, tg):
        prim = {'attributes': {'POSITION': add_acc(g, P, 5126, 'VEC3', 34962, True), 'NORMAL': add_acc(g, N, 5126, 'VEC3', 34962),
                               'TEXCOORD_0': add_acc(g, UV, 5126, 'VEC2', 34962),
                               'JOINTS_0': add_acc(g, J, jct, 'VEC4', 34962), 'WEIGHTS_0': add_acc(g, W, 5126, 'VEC4', 34962)},
                'indices': add_acc(g, T.reshape(-1), 5125, 'SCALAR', 34963), 'material': hprim.get('material'), 'mode': 4}
        tn = []
        if tg:
            prim['targets'] = []
            for nm, (d, dn) in tg.items():
                pa, na = add_sparse(g, d, dn)
                prim['targets'].append({'POSITION': pa, 'NORMAL': na}); tn.append(nm)
        mesh = {'name': name, 'primitives': [prim]}
        if tn:
            mesh['weights'] = [0.0] * len(tn); mesh['extras'] = {'targetNames': tn}
        gg['meshes'].append(mesh)
        gg['nodes'].append({'name': name, 'mesh': len(gg['meshes']) - 1, 'skin': hnode.get('skin', 0)})
        ni = len(gg['nodes']) - 1
        if parent is not None:
            parent['children'].append(ni)
        else:
            gg['scenes'][gg.get('scene', 0)]['nodes'].append(ni)

    Q, T, N = res['Q'], res['T'], res['N']
    tg = {}
    for nm, t in res['targets'].items():
        d = t['skin']
        if np.abs(d).max() < 1e-5:
            continue
        dn = welded_normals(Q + d, T, res['grp']) - N
        dn[res['ring']] = 0
        tg[nm] = (d, dn)
    add_node('head__hd', Q, N, res['UV'], res['J'], res['W'], T, tg)
    nodes = {'eyes': 'head__hd_eyes', 'lash': 'head__hd_lash'}
    # the teeth and tongue: one mesh (one texture: the teeth's left, the tongue's right)
    for group, members in (('eyes', ['eyes']), ('lash', ['lash']), ('mouth', ['teeth', 'tongue'])):
        Ps, Us, Ts, n0 = [], [], [], 0
        for i, nm in enumerate(members):
            pc = res['pieces'][nm]
            uv = pc['UV'].copy()
            if group == 'mouth':
                uv[:, 0] = uv[:, 0] * 0.5 + 0.5 * i
            Ps.append(pc['X']); Us.append(uv); Ts.append(pc['T'] + n0); n0 += len(pc['X'])
        Pp = np.concatenate(Ps); Up = np.concatenate(Us); Tp = np.concatenate(Ts)
        Np = welded_normals(Pp, Tp)
        Jp = np.zeros((len(Pp), 4), int); Jp[:, 0] = head_b
        Wp = np.zeros((len(Pp), 4)); Wp[:, 0] = 1
        tgp = {}
        for tn_, t in res['targets'].items():
            if not any(nm in t['pieces'] for nm in members):
                continue
            d = np.concatenate([t['pieces'].get(nm, np.zeros_like(res['pieces'][nm]['X'])) for nm in members])
            tgp[tn_] = (d, None)
        add_node('head__hd_' + group, Pp, Np, Up, Jp, Wp, Tp, tgp)
    # the hair, beards, helms near the head: the sliders that reach them ('carry'), each point as the skin nearest it
    S = Q
    tree = cKDTree(S)
    lo, hi = S.min(0) - HAIR_REACH, S.max(0) + HAIR_REACH
    skip = ('head', 'body', 'legs', 'boots', 'arms', 'gloves', 'cloak', 'lbody')
    carried = 0
    for n in gg['nodes']:
        nm = n.get('name', '')
        if 'mesh' not in n or nm.split('_v')[0].split('__')[0] in skip or nm.startswith(skip):
            continue
        mesh = gg['meshes'][n['mesh']]
        if len(mesh['primitives']) != 1:
            continue
        tn = list(mesh.get('extras', {}).get('targetNames', []))
        prim2 = mesh['primitives'][0]
        Pq = g.acc(prim2['attributes']['POSITION']).astype(np.float64)
        if not np.all((Pq > lo) & (Pq < hi), axis=1).any():
            continue
        dist, j = tree.query(Pq)
        hair_w = 1 - np.clip((dist - 0.4) / (HAIR_REACH - 0.4), 0, 1)
        newn = []
        for name, t in res['targets'].items():
            if not t['carry']:
                continue
            dq = t['skin'][j] * hair_w[:, None]
            if np.abs(dq).max() < 0.02:
                continue
            dq[np.abs(dq).max(1) < 0.003] = 0.0
            pa, na = add_sparse(g, dq, None, 0.003)
            prim2.setdefault('targets', []).append({'POSITION': pa, 'NORMAL': na})
            newn.append(name)
        if newn:
            mesh.setdefault('extras', {})['targetNames'] = tn + newn
            mesh['weights'] = list(mesh.get('weights', [0.0] * len(tn))) + [0.0] * len(newn)
            carried += 1
    log(f'{folder.name}: HD head {len(Q)} skin points, {len(T)} triangles, {len(tg)} slider shapes; {carried} hair / helm meshes carry them')
    out_folder.mkdir(parents=True, exist_ok=True)
    tex_names = {}
    if textures:
        import tex2
        tex_names = tex2.bake(res, folder, out_folder, log=log)
    g.save(out_folder / 'figure.gltf')
    meta = json.loads((folder / 'figure.json').read_text(encoding='utf-8'))
    meta['hd_head'] = {'node': 'head__hd', 'v': 2, **tex_names, 'features': [
        {'key': f[0], 'label': f[1], 'sliders': [[s_[0], s_[1]] for s_ in f[2] if s_[2] or s_[3]], 'presets': [[p[0], p[1]] for p in f[3]]}
        for f in FEATURES]}
    (out_folder / 'figure.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')


if __name__ == '__main__':
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src
    res = build(src, out)
    import check2
    ok = check2.run(res, log=log)
    write(res, src, out, textures='--no-tex' not in sys.argv)
    sys.exit(0 if ok else 3)
