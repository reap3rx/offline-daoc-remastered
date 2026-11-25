"""The HD head (the character creator plan, phases 2-4): MakeHuman's CC0 head wrapped onto a race's classic head,
written into its figure.gltf as a node of its own ("head__hd": the client shows it on the player and the companion,
in place of "head"), with the face sliders as morph targets ("hx_<slider>-" / "hx_<slider>+", hd_sliders.py) and
the hair, beards and helms carrying the sliders that reach them. figure.json "hd_head" lists the features.

    python hd_head.py <race folder> [<out folder>]

What it keeps of the classic head: its texture layout (every new point takes the UV of the classic skin under it -
the faces, skin tones, tattoos, war paint and skin layers all still fit), its eyeballs (grown to the new lids) and
teeth, its bones and weights. What's new: the skin's mesh - real eyelids, lips, nostrils, ears.
"""
import json, sys, pickle
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import griddata

sys.path.insert(0, str(Path(__file__).parent))
from headio import G, load_head, bones, weld
from hd_wrap import mh_head, wrap, finish, transfer_uv, vertex_normals_simple, tris, _OBJ
import hd_wrap
from landmarks import race_landmarks, sphere_fit
from mhbase import read_target, TO_FIG
from hd_sliders import FEATURES, SLIDERS, gain

POINTED = ('elf', 'lur', 'inc', 'fro', 'fir')     # the races whose ears are their look: the classic ear is kept
EYE_UV_K = 1.25                         # the eyeball's picture drawn smaller about the pupil (it grew to the lids)
HAIR_REACH = 2.6                        # how far off the skin a hair / helm point still takes the skin's move


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


def add_sparse(g, d, normals, eps=1e-5):
    moved = np.flatnonzero((np.abs(d).max(1) > eps) | (np.abs(normals).max(1) > eps * 20))
    if len(moved) == 0:
        moved = np.array([0])
    idx = moved.astype(np.uint32)
    out = []
    for arr in (d, normals):
        vals = np.ascontiguousarray(arr[moved], np.float32)
        data = idx.tobytes() + vals.tobytes()
        g.g['buffers'].append({'byteLength': len(data)})
        g.b.append(bytearray(data))
        bi = len(g.b) - 1
        g.g['bufferViews'].append({'buffer': bi, 'byteOffset': 0, 'byteLength': idx.nbytes})
        iv = len(g.g['bufferViews']) - 1
        g.g['bufferViews'].append({'buffer': bi, 'byteOffset': idx.nbytes, 'byteLength': vals.nbytes})
        vv = len(g.g['bufferViews']) - 1
        full = np.zeros((len(d), 3), np.float32); full[moved] = vals
        g.g['accessors'].append({'componentType': 5126, 'count': len(d), 'type': 'VEC3', 'min': full.min(0).tolist(),
                                 'max': full.max(0).tolist(), 'sparse': {'count': int(len(moved)),
                                 'indices': {'bufferView': iv, 'componentType': 5125}, 'values': {'bufferView': vv}}})
        out.append(len(g.g['accessors']) - 1)
    return out


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


def add_sparse_pos(g, d, eps):
    """A hair / helm target: its points' moves, and a placeholder normal (one zero) - the light on hair barely changes."""
    moved = np.flatnonzero(np.abs(d).max(1) > eps)
    if len(moved) == 0:
        moved = np.array([0])
    pa = _sparse_one(g, moved, d[moved], len(d))
    na = _sparse_one(g, np.array([0]), np.zeros((1, 3)), len(d))
    return pa, na


def welded_normals(P, T):
    grp = weld(P)
    n = vertex_normals_simple(P, T)
    acc = np.zeros((grp.max() + 1, 3)); np.add.at(acc, grp, n)
    n = acc[grp]
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def fix_uv(h, parts, L, PV, T2, vmap, UV, rings, P_mh_all, keep_ears=True):
    """The texture's special places: the eye pockets plain skin, the mouth and the ears by how they're seen."""
    extra = []
    T2 = T2.copy()
    skin_v = np.flatnonzero(parts['skin'])
    for sd, (c_r, r, inner) in rings.items():
        q = c_r + np.array([0, -0.6 * r, -1.15 * r])
        j = skin_v[np.argmin(np.linalg.norm(h['P'][skin_v] - q, axis=1))]
        UV[inner[vmap]] = h['UV'][j]
    NR = vertex_normals_simple(h['P'], h['T'])
    mm = (L['mouthL'] + L['mouthR']) / 2
    mw = abs(L['mouthL'][0] - L['mouthR'][0]) / 2
    sk = parts['skin'] & (NR[:, 1] < -0.25) & (np.abs(h['P'][:, 0] - mm[0]) < mw * 1.9) & (np.abs(h['P'][:, 2] - mm[2]) < 1.0) \
        & (h['P'][:, 1] < mm[1] + 0.6)
    box = (np.abs(PV[:, 0] - mm[0]) < mw * 1.35) & (np.abs(PV[:, 2] - mm[2]) < 0.55) & (PV[:, 1] < mm[1] + 0.8)
    g2 = griddata(h['P'][sk][:, [0, 2]], h['UV'][sk], PV[box][:, [0, 2]], method='linear')
    ok = ~np.isnan(g2).any(1)
    wx = np.clip((mw * 1.35 - np.abs(PV[box, 0] - mm[0])) / (0.3 * mw), 0, 1) * np.clip((0.55 - np.abs(PV[box, 2] - mm[2])) / 0.15, 0, 1)
    bi = np.flatnonzero(box)[ok]
    UV[bi] = UV[bi] * (1 - wx[ok, None]) + g2[ok] * wx[ok, None]
    # the ears: MakeHuman's ear (its own ear targets' points) takes the classic ear's picture, by where it is seen from
    # the side - from the classic ear's own UV island
    isl = hd_wrap.uv_islands(h['T'], h['UV'])
    for ek, sg, tf in ((('earL', 1, 'ears/l-ear-scale-incr.target'), ('earR', -1, 'ears/r-ear-scale-incr.target')) if keep_ears else ()):
        ec = L[ek]
        cand = [i for i in np.unique(isl) if parts['skin'][h['T'][isl == i]].all()
                and np.linalg.norm(h['P'][h['T'][isl == i]].mean((0, 1)) - ec) < 1.5 and (isl == i).sum() < 400]
        if not cand:
            continue
        ear_t = h['T'][np.isin(isl, cand)]
        ev = np.unique(ear_t)
        ei, ed = read_target(tf)
        mag = np.zeros(len(P_mh_all)); mag[ei] = np.linalg.norm(ed, axis=1)
        mine = mag[vmap] > 0.2 * mag.max()
        g3 = griddata(h['P'][ev][:, [1, 2]], h['UV'][ev], PV[mine][:, [1, 2]], method='nearest')
        UV[np.flatnonzero(mine)] = g3
        # the triangles where the ear meets the head: the head-side corners copied, in the ear's picture too (its edge
        # is plain skin) - across the two pictures they stretched into jagged patches
        mix = mine[T2].any(1) & ~mine[T2].all(1)
        for k in np.flatnonzero(mix):
            for j in range(3):
                v = T2[k, j]
                if not mine[v]:
                    uv = griddata(h['P'][ev][:, [1, 2]], h['UV'][ev], PV[v:v + 1][:, [1, 2]], method='nearest')[0]
                    extra.append((v, uv)); T2[k, j] = -len(extra)
    if extra:
        n0 = len(UV)
        T2[T2 < 0] = n0 - 1 - T2[T2 < 0]
        vmap = np.r_[vmap, vmap[[e[0] for e in extra]]]
        UV = np.r_[UV, np.array([e[1] for e in extra])]
    return UV, T2, vmap


def keep_lids(PV, dS, dO, oP, eyes, old, rings, vmap):
    """A shape's lids still rest on the eye (moved with the shape), never through it; the pocket stays behind it."""
    dS = dS.copy()
    for sd, (m, c, r, r_new) in eyes.items():
        mo = m[old]
        if not mo.any():
            continue
        # the eyeball as the shape leaves it: centre and size from its points' move
        q0 = oP[mo]; q1 = q0 + dO[mo]
        c1 = c + (q1 - q0).mean(0)
        k = np.median(np.linalg.norm(q1 - c1, axis=1) / np.maximum(np.linalg.norm(q0 - c, axis=1), 1e-9))
        r1 = r_new * k
        c_r, rr, inner = rings[sd]
        inn = inner[vmap]
        P1 = PV + dS
        d0 = np.linalg.norm(PV - c_r, axis=1)
        d1v = P1 - c1
        d1 = np.linalg.norm(d1v, axis=1)
        near = d0 < rr * 1.3
        out = near & ~inn & (d1 < r1 * 1.02)
        P1[out] = c1 + d1v[out] / d1[out, None] * r1 * 1.02
        pin = near & inn & (d1 > r1 * 0.97)
        P1[pin] = c1 + d1v[pin] / d1[pin, None] * r1 * 0.95
        dS = P1 - PV
    return dS


def transplant_ears(h, parts, L, PV, T2, old, remap, oP, oUV, oT, ear_mh=None):
    """The classic ears (their mesh, UVs, weights) set into the new head: the classic skin standing off the new skin
    near each ear, grown out to its base; the new skin it covers taken away."""
    from scipy.sparse import coo_matrix
    Pc = h['P']
    PV = PV  # (flattened in place below)
    skin = parts['skin']
    # how far each classic point stands off the new skin's surface (not its points: they're sparser than the classic)
    Qd, _ = hd_wrap.dense_surface(PV, T2, n=4)
    dc, _ = cKDTree(Qd).query(Pc)
    half = np.percentile(np.abs(Pc[skin, 0]), 90)
    Ts = h['T'][skin[h['T']].all(1)]
    grp = weld(Pc)
    keep_v = np.zeros(len(Pc), bool)
    sets = {}
    for ek, sg in (('earL', 1), ('earR', -1)):
        near = skin & (np.linalg.norm(Pc - L[ek], axis=1) < 3.8) & (Pc[:, 0] * sg > 0.85 * half) \
            & (Pc[:, 2] > L[ek][2] - 1.3) & (Pc[:, 2] < L[ek][2] + 2.6)
        core = near & (dc > 0.35)
        sel = core.copy()
        for _ in range(2):                                    # out to the ear's base
            g_sel = np.zeros(grp.max() + 1, bool); g_sel[grp[sel]] = True
            touch = g_sel[grp[Ts]].any(1)
            grown = np.zeros(len(Pc), bool); grown[Ts[touch].ravel()] = True
            sel = (sel | grown) & near
        sets[ek] = (sel, sg)
        keep_v |= sel
    # the new skin under the classic ears goes
    pv = np.flatnonzero(keep_v)
    if len(pv) == 0:
        return T2, oP, oUV, oT, old, {}
    # MakeHuman's own ear smoothed flat into the skull (a membrane over it, pinned round its edge): no hole, and the
    # classic ear stands on it
    if ear_mh is not None and ear_mh.any():
        n = len(PV)
        e = np.concatenate([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]])
        e = np.concatenate([e, e[:, ::-1]])
        A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
        A.data[:] = 1.0
        deg = np.asarray(A.sum(1)).ravel()
        # (welded: the UV seams split points that are one place)
        g = weld(PV)
        free = np.zeros(g.max() + 1, bool); free[g[ear_mh]] = True
        fr = free[g]
        X = PV.copy()
        for _ in range(400):
            Q = (A @ X) / np.maximum(deg, 1)[:, None]
            # weld groups move together
            acc = np.zeros((g.max() + 1, 3)); np.add.at(acc, g, Q); cnt = np.bincount(g)
            Q = acc[g] / cnt[g][:, None]
            X[fr] = Q[fr]
        PV[:] = X
    # the ears' triangles added to the kept classic parts
    eT = Ts[keep_v[Ts].all(1)]
    add = np.setdiff1d(np.unique(eT), old)
    old2 = np.r_[old, add]
    remap2 = -np.ones(len(Pc), int); remap2[old2] = np.arange(len(old2))
    oP = np.r_[oP, Pc[add]]; oUV = np.r_[oUV, h['UV'][add]]
    oT = np.r_[oT, remap2[eT]]
    # (pushed off the skull a hair at their base, so the two skins don't fight)
    ear_sets = {}
    for ek, (sel, sg) in sets.items():
        m = np.isin(old2, np.flatnonzero(sel))
        base = m & (dc[old2] <= 0.35)
        oP[base] += np.array([sg * 0.015, 0, 0])
        root = oP[base].mean(0) if base.any() else oP[m].mean(0)
        reach = np.linalg.norm(oP[m] - root, axis=1)
        w = np.zeros(len(oP)); w[m] = np.clip(reach / max(reach.max(), 1e-6), 0, 1)
        ear_sets[ek] = (m, root, w, sg)
    print('  ears: the classic ears kept (%d points)' % len(add))
    return T2, oP, oUV, oT, old2, ear_sets


def ear_move(oP, ear_sets, key, sign):
    """A kept classic ear's slider: grown about its root (size), swung out from the head (out), turned (tilt)."""
    d = np.zeros_like(oP)
    sgn = 1.0 if sign == '+' else -1.0
    for ek, (m, root, w, sg) in ear_sets.items():
        q = oP[m] - root
        if key == 'ear_size':
            d[m] = q * (0.22 * sgn) * w[m, None]
        elif key == 'ear_out':
            th = 0.25 * sgn * sg                                # about the up axis at the root, the tip out or in
            c, s_ = np.cos(th), np.sin(th)
            rx = q[:, 0] * c - q[:, 1] * s_; ry = q[:, 0] * s_ + q[:, 1] * c
            d[m, 0] = (rx - q[:, 0]) * w[m]; d[m, 1] = (ry - q[:, 1]) * w[m]
        elif key == 'ear_tilt':
            th = 0.25 * sgn                                     # about the side axis: the tip up or down
            c, s_ = np.cos(th), np.sin(th)
            ry = q[:, 1] * c - q[:, 2] * s_; rz = q[:, 1] * s_ + q[:, 2] * c
            d[m, 1] = (ry - q[:, 1]) * w[m]; d[m, 2] = (rz - q[:, 2]) * w[m]
    return d


def made_shape(key, sign, PV, oP, ear_sets, ear_mask, L):
    """The sliders MakeHuman has no target for. ear_flare: each ear turned about the front-back line through its root,
    the tip out (+) or in, the lobe hardly moving."""
    dS = np.zeros_like(PV); dO = np.zeros_like(oP)
    sgn = 1.0 if sign == '+' else -1.0
    if key == 'ear_flare':
        if ear_sets:
            for ek, (m, root, w, sx) in ear_sets.items():
                dO[m] = _flare(oP[m], root, sx, sgn) * w[m, None]
        else:
            for ek, sx in (('earL', 1.0), ('earR', -1.0)):
                side = (PV[:, 0] * sx > 0) & (ear_mask > 0)
                if not side.any():
                    continue
                q = PV[side]
                root = np.array([L[ek][0] - sx * 0.25, L[ek][1], L[ek][2] - 0.3])
                dS[side] = _flare(q, root, sx, sgn) * ear_mask[side, None]
    return dS, dO


def _flare(q, root, sx, sgn, ang=0.38):
    """Points turned about the front-back axis through root: the part above swings out (sx: the ear's side)."""
    th = -ang * sgn * sx
    r = q - root
    c, s_ = np.cos(th), np.sin(th)
    x = r[:, 0] * c - r[:, 2] * s_
    z = r[:, 0] * s_ + r[:, 2] * c
    d = np.zeros_like(q)
    d[:, 0] = x - r[:, 0]; d[:, 2] = z - r[:, 2]
    # (only what's above the root swings much: the lobe stays put)
    up = np.clip(r[:, 2] / 1.2 + 0.3, 0, 1)
    return d * up[:, None]


def eye_texture(folder):
    """The race's first face texture (its eyes' picture), or None."""
    try:
        from PIL import Image
        meta = json.loads((Path(folder) / 'figure.json').read_text(encoding='utf-8'))
        name = str(meta['faces'][0]['tex']).lower()
        for base in (Path(folder).resolve().parent.parent / 'fig3_textures' / 'x4plus',
                     Path(folder).resolve().parent.parent / 'fig3_textures' / 'original',
                     Path(r'E:\Offline DAOC 036c\playable-v0.36c\new-client\godot\content\characters\fig3_textures\x4plus'),
                     Path('/mnt/user-data/uploads/Offline DAOC 036c/playable-v0.36c/new-client/godot/content/characters/fig3_textures/x4plus')):
            f = base / (name + '.png')
            if f.exists():
                return np.asarray(Image.open(f).convert('RGB'), np.float32) / 255
    except Exception:
        pass
    return None


def build(folder, out_folder=None):
    folder = Path(folder)
    out_folder = Path(out_folder or folder)
    prefix = folder.name
    sex = 'female' if prefix.endswith('_f') else 'male'
    g = G(folder / 'figure.gltf')
    h = load_head(g)
    B, names = bones(g)
    L, parts = race_landmarks(h, names)
    # appendages (the Shar's horns): classic skin islands of their own (in the texture) standing well off the skull -
    # kept as they are, as the eyes are, and the wrap doesn't reach for them
    Ts = h['T'][parts['skin'][h['T']].all(1)]
    isl = hd_wrap.uv_islands(Ts, h['UV'])
    main = np.bincount(isl).argmax()
    cen = h['P'][np.unique(Ts[isl == main])]
    c0 = cen.mean(0)
    r_main = np.percentile(np.linalg.norm(cen - c0, axis=1), 97)
    app = np.zeros(len(h['P']), bool)
    for i in np.unique(isl):
        if i == main:
            continue
        v = np.unique(Ts[isl == i])
        if np.linalg.norm(h['P'][v] - c0, axis=1).max() > 1.2 * r_main:
            app[v] = True
    if app.any():
        print('  appendages kept as they are: %d points' % app.sum())
        parts = dict(parts)
        parts['skin'] = parts['skin'] & ~app
    mh = mh_head(sex)
    # the race's ears: human-sized, MakeHuman's sculpted ear is kept; long ones (the Inconnu's, the elves', the
    # Lurikeen's) - how far the ear stands out past the skull - the ear follows the classic one instead
    Ps = h['P'][parts['skin']]
    Hh = np.ptp(Ps[:, 2]); ax = np.abs(Ps[:, 0])
    band = np.abs(Ps[:, 2] - (Ps[:, 2].min() + 0.55 * Hh)) < 0.25 * Hh
    beyond = (ax.max() - np.percentile(ax[band], 80)) / Hh
    keep_ears = beyond < 0.13 and not prefix.startswith(POINTED)
    # (the wrap keeps MakeHuman's compact ear either way - pulled out onto a long classic ear it stretched the skull's
    # skin with it; a long-eared race's MakeHuman ear is swapped for the classic one after)
    print('  ears: %s (stand out %.3f of the head)' % ('MakeHuman\'s' if keep_ears else 'the race\'s own', beyond))
    P0, used, info = wrap(mh, h['P'], h['T'], parts['skin'], L, keep_ears=True)
    P, usedK, keepF, T, edge, rings = finish(mh, P0, used, info, h['P'], h['T'], parts, weld(h['P']))
    vmap, UV, T2 = transfer_uv(P, T, h['P'], h['T'], h['UV'], parts['skin'])
    PV = P[vmap]
    UV, T2, vmap = fix_uv(h, parts, L, PV, T2, vmap, UV, rings, P, keep_ears)
    PV = P[vmap]
    # (a safety net: below the mouth the new skin lies on the classic neck - a triangle far off it is a stray flap
    # from the neck's cut)
    Qn, _ = hd_wrap.dense_surface(h['P'], h['T'][parts['skin'][h['T']].all(1)], n=4)
    cz = PV[T2].mean(1)
    dn, _ = cKDTree(Qn).query(cz)
    stray = (cz[:, 2] < (L['mouthL'][2] - 0.5)) & (dn > 1.0)
    if stray.any():
        print('  %d stray triangles at the neck dropped' % stray.sum())
        T2 = T2[~stray]
    # the classic eyeballs, grown to the lids, their picture drawn smaller about the pupil; the teeth as they are
    eyes = {}
    for sd in 'LR':
        m = parts['eye' + sd]
        c, r = sphere_fit(h['P'][m])
        eyes[sd] = (m, c, r, rings[sd][1])
    keep_eye_teeth = ~parts['skin']                    # eyes, teeth and any other piece (the Shar's arm spikes)
    old = np.flatnonzero(keep_eye_teeth)
    remap = -np.ones(len(h['P']), int); remap[old] = np.arange(len(old))
    oT = h['T'][keep_eye_teeth[h['T']].all(1)]
    oP = h['P'][old].copy(); oUV = h['UV'][old].copy()
    for sd, (m, c, r, r_new) in eyes.items():
        mo = m[old]
        oP[mo] = rings[sd][0] + (oP[mo] - c) * (r_new / r)    # grown, and set in the new lids' socket
        pu = h['UV'][m][np.argmin(h['P'][m][:, 1])]
        # the picture scaled so the white the classic lids showed is what the new lids show (owner 2026-11-25: the
        # lurikeen's painted lids showed on the eyeball): the opening's angle off the eye's front, old and new
        def opening(Q, cc, rr):
            dq = Q - cc
            dd = np.linalg.norm(dq, axis=1)
            ang = np.arccos(np.clip(-dq[:, 1] / np.maximum(dd, 1e-9), -1, 1))
            a_ = ang[(dd < 1.35 * rr) & (ang < 1.4)]
            return float(np.mean(np.sort(a_)[:max(3, len(a_) // 7)])) if len(a_) > 6 else None
        th_c = opening(h['P'][parts['skin']], c, r)
        th_h = opening(PV, rings[sd][0], r_new)
        k_uv = float(np.clip(th_c / th_h, 0.6, 1.6)) if th_c and th_h else EYE_UV_K
        print('  eye %s: opening %.2f -> %.2f rad, picture x%.2f' % (sd, th_c or 0, th_h or 0, k_uv))
        du = (oUV[mo] - pu) * k_uv
        rim = np.linalg.norm(h['UV'][m] - pu, axis=1).max() * 0.97
        dl = np.linalg.norm(du, axis=1, keepdims=True)
        oUV[mo] = pu + du * np.minimum(1.0, rim / np.maximum(dl, 1e-9))
    eyes = {sd: (m, rings[sd][0], r_new, r_new) for sd, (m, c, r, r_new) in eyes.items()}   # (now: where they sit)
    oP[parts['teeth'][old]] += np.array([0, 0.14, 0])        # (the teeth just behind the lips: they showed between them)
    # the pointed ears (POINTED): the classic ear itself, in place of the new skin over it
    ear_sets = {}
    ear_flat = np.zeros(len(PV), bool)
    if not keep_ears:
        ear_mh = np.zeros(len(PV), bool)
        for tf in ('ears/l-ear-scale-incr.target', 'ears/r-ear-scale-incr.target'):
            ei, ed = read_target(tf)
            mag = np.zeros(len(P)); mag[ei] = np.linalg.norm(ed, axis=1)
            ear_mh |= mag[vmap] > 0.3 * mag.max()
        ear_flat = ear_mh
        T2, oP, oUV, oT_new, old, ear_sets = transplant_ears(h, parts, L, PV, T2, old, remap, oP, oUV,
                                                              remap[oT], ear_mh)
        oT = None
    nS = len(PV)
    allP = np.r_[PV, oP]
    allUV = np.r_[UV, oUV]
    allT = np.r_[T2, (remap[oT] if oT is not None else oT_new) + nS]
    # bones: each new skin point takes the weights of the classic skin point nearest it
    sk = np.flatnonzero(parts['skin'])
    _, near = cKDTree(h['P'][sk]).query(PV)
    J = np.r_[h['J'][sk[near]], h['J'][old]]
    W = np.r_[h['W'][sk[near]], h['W'][old]]
    W = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
    N = np.r_[welded_normals(PV, T2), vertex_normals_simple(oP, (remap[oT] if oT is not None else oT_new))]
    # the sliders: MakeHuman's targets in the figure's frame (the wrap's turn and scale), the eyeballs and teeth moved
    # as MakeHuman moves its own
    s, R = info['scale'], info['R']
    V, VT, F, FT, FG = hd_wrap._OBJ
    # how near each point is to an eye (1 at the lids, 0 two eye-widths out) - the lower lid's sliders stay there
    eye_near = np.zeros(len(PV))
    for sd in 'LR':
        c_r, rr = rings[sd][0], rings[sd][1]
        eye_near = np.maximum(eye_near, np.clip((2.0 - np.linalg.norm(PV - c_r, axis=1) / rr) / 0.6, 0, 1))
    # the ears' points (MakeHuman's, kept on the head) for the tip flare
    ear_mask = np.zeros(len(PV))
    for tf in ('ears/l-ear-scale-incr.target', 'ears/r-ear-scale-incr.target'):
        ei, ed = read_target(tf)
        mag = np.zeros(len(P)); mag[ei] = np.linalg.norm(ed, axis=1)
        sx = 1.0 if tf.startswith('ears/l') else -1.0
        ec = L['earL' if sx > 0 else 'earR']
        out_ = np.clip((PV[:, 0] * sx - (abs(ec[0]) - 0.4)) / 0.3, 0, 1) \
            * np.clip((1.0 - np.abs(PV[:, 1] - ec[1])) / 0.3, 0, 1) \
            * np.clip((PV[:, 2] - (ec[2] - 1.3)) / 0.3, 0, 1) * np.clip((ec[2] + 1.7 - PV[:, 2]) / 0.3, 0, 1)
        ear_mask = np.maximum(ear_mask, np.clip((mag[vmap] / max(mag.max(), 1e-9) - 0.3) / 0.3, 0, 1) * out_)
    if ear_sets:
        ear_mask[:] = 0.0                                    # (the classic ears carry it instead)
    def gverts(gn):
        ks = [k for k, gg in enumerate(FG) if gg == gn]
        return np.unique(np.concatenate([F[k] for k in ks]))
    helpers = {'L': gverts('helper-l-eye'), 'R': gverts('helper-r-eye'),
               'teeth': np.r_[gverts('helper-upper-teeth'), gverts('helper-lower-teeth')]}
    mh_pts = (s * (R @ mh['P'].T)).T + info['t']             # (MakeHuman's points moved as the wrap began)
    def target_delta(rel):
        D = np.zeros((len(mh_pts), 3))
        for part in rel:
            i, d = read_target(part + '.target')
            if len(i):
                D[i] += s * (R @ (d @ TO_FIG.T).T).T
        return D
    targets = {}
    for key, label, tminus, tplus, carry in SLIDERS:
        for sign, t in (('-', tminus), ('+', tplus)):
            if not t:                                          # (a slider made here, not by a MakeHuman target)
                dS, dO = made_shape(key, sign, PV, oP, ear_sets, ear_mask, L)
                targets[f'hx_{key}{sign}'] = (np.r_[dS, dO], carry)
                continue
            rel = [t.format(s=sd) for sd in ('l', 'r')] if '{s}' in t else [t]
            D = target_delta(rel)
            dS = D[vmap]
            dO = np.zeros_like(oP)
            for sd in 'LR':
                hv = helpers[sd]
                if np.abs(D[hv]).max() > 1e-6:
                    c0, r0 = sphere_fit(mh_pts[hv]); c1, r1 = sphere_fit(mh_pts[hv] + D[hv])
                    mo = eyes[sd][0][old]
                    dO[mo] = (c1 - c0) + (oP[mo] - eyes[sd][1]) * (r1 / r0 - 1)
            if ear_sets and key.startswith('ear_'):
                dO = ear_move(oP, ear_sets, key, sign)
            elif ear_sets:
                # the kept classic ears ride on the skin at their base (owner 2026-11-25: the head's width left them
                # floating)
                for ek, (m_, root_, w_, sx_) in ear_sets.items():
                    j_ = np.argmin(np.linalg.norm(PV - root_, axis=1))
                    near_ = np.linalg.norm(PV - PV[j_], axis=1) < 0.5
                    dO[m_] = dS[near_].mean(0)
            ht = helpers['teeth']
            if np.abs(D[ht]).max() > 1e-6:
                dO[parts['teeth'][old]] = D[ht].mean(0)
            k = gain(key, sign)
            dS = dS * k; dO = dO * k
            if key in ('eye_bags', 'eye_bag_height'):         # (owner: it pulled the cheeks up - kept to the lid)
                dS = dS * eye_near[:, None]
            if ear_sets is not None and len(ear_sets) and key.startswith('ear_'):
                dS = dS * (~ear_flat)[:, None]
            dS = keep_lids(PV, dS, dO, oP, eyes, old, rings, vmap)
            targets[f'hx_{key}{sign}'] = (np.r_[dS, dO], carry)
    return dict(g=g, h=h, P=allP, UV=allUV, T=allT, J=J, W=W, N=N, targets=targets, nS=nS, info=info, L=L)


def write(res, folder, out_folder):
    folder, out_folder = Path(folder), Path(out_folder)
    g = res['g']; gg = g.g
    hnode = next(n for n in gg['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    hmesh = gg['meshes'][hnode['mesh']]
    hprim = hmesh['primitives'][0]
    P, UV, T, J, W, N = res['P'], res['UV'], res['T'], res['J'], res['W'], res['N']
    jacc = gg['accessors'][hprim['attributes']['JOINTS_0']]
    prim = {'attributes': {'POSITION': add_acc(g, P, 5126, 'VEC3', 34962, True), 'NORMAL': add_acc(g, N, 5126, 'VEC3', 34962),
                           'TEXCOORD_0': add_acc(g, UV, 5126, 'VEC2', 34962),
                           'JOINTS_0': add_acc(g, J, jacc['componentType'], 'VEC4', 34962),
                           'WEIGHTS_0': add_acc(g, W, 5126, 'VEC4', 34962)},
            'indices': add_acc(g, T.reshape(-1), 5125, 'SCALAR', 34963), 'material': hprim.get('material'), 'mode': 4,
            'targets': []}
    names = []
    for name, (d, carry) in res['targets'].items():
        dn = welded_normals(P + d, T) - N
        pa, na = add_sparse(g, d, dn)
        prim['targets'].append({'POSITION': pa, 'NORMAL': na})
        names.append(name)
    gg['meshes'].append({'name': 'head__hd', 'primitives': [prim], 'weights': [0.0] * len(names), 'extras': {'targetNames': names}})
    node = {'name': 'head__hd', 'mesh': len(gg['meshes']) - 1, 'skin': hnode.get('skin', 0)}
    gg['nodes'].append(node)
    ni = len(gg['nodes']) - 1
    parent = next((n for n in gg['nodes'] if gg['nodes'].index(hnode) in n.get('children', [])), None)
    if parent is not None:
        parent['children'].append(ni)
    else:
        gg['scenes'][gg.get('scene', 0)]['nodes'].append(ni)
    # the hair, beards, helms near the head: the sliders that reach them ('carry'), each point as the skin nearest it
    S = P[:res['nS']]
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
        newn = []
        for prim2 in mesh['primitives']:
            Q = g.acc(prim2['attributes']['POSITION']).astype(np.float64)
            if not np.all((Q > lo) & (Q < hi), axis=1).any():
                break
            dist, j = tree.query(Q)
            hair_w = 1 - np.clip((dist - 0.4) / (HAIR_REACH - 0.4), 0, 1)
            for name, (d, carry) in res['targets'].items():
                if not carry:
                    continue
                dq = d[:res['nS']][j] * hair_w[:, None]
                if np.abs(dq).max() < 0.02:
                    continue
                dq[np.abs(dq).max(1) < 0.003] = 0.0
                pa, na = add_sparse_pos(g, dq, 0.003)
                prim2.setdefault('targets', []).append({'POSITION': pa, 'NORMAL': na})
                newn.append(name)
        else:
            if newn:
                if len(mesh['primitives']) > 1:
                    pass
                mesh.setdefault('extras', {})['targetNames'] = tn + newn
                mesh['weights'] = list(mesh.get('weights', [0.0] * len(tn))) + [0.0] * len(newn)
                carried += 1
    print(f'{folder.name}: HD head {len(P)} points, {len(T)} triangles, {len(names)} slider shapes; {carried} hair / helm '
          f'meshes carry them')
    out_folder.mkdir(parents=True, exist_ok=True)
    g.save(out_folder / 'figure.gltf')
    meta = json.loads((folder / 'figure.json').read_text(encoding='utf-8'))
    meta['hd_head'] = {'node': 'head__hd', 'features': [
        {'key': f[0], 'label': f[1], 'sliders': [[s[0], s[1]] for s in f[2]], 'presets': [[p[0], p[1]] for p in f[3]]}
        for f in FEATURES]}
    (out_folder / 'figure.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')


if __name__ == '__main__':
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src
    res = build(src, out)
    write(res, src, out)
    # a small preview for checking the head without the whole figure: its mesh, UVs, the classic head, and the
    # sliders' moves at the ends
    meta = json.loads((Path(src) / 'figure.json').read_text(encoding='utf-8'))
    h = res['h']
    np.savez_compressed(Path(out) / 'hd_preview.npz', P=res['P'], T=res['T'], UV=res['UV'], cP=h['P'], cT=h['T'], cUV=h['UV'],
                        tex=str(meta['faces'][0]['tex']).lower(), **{k: v[0].astype(np.float32) for k, v in res['targets'].items()})
