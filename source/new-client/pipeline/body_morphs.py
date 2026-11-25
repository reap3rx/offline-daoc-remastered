"""Body shapes (claude 2026-11-25, owner: "as many sliders to customize the shape as possible given the body we have to
work with"; the character creator plan, phase 1). For a race figure, a set of new morph targets ("bx_<name>") on every
body, leg, boot, arm, glove and cloak mesh - the starter clothes and every armour variant alike - so a slider reshapes
the figure in whatever it wears: the belly, the love handles, the back's width, the traps and shoulders, the upper
chest, the delts, biceps, triceps and forearms, the hips' flare, the inner thighs, quads, hamstrings, knees and ankles,
and two that mix them: weight (soft) and muscle (hard); on women the bust's lift and spacing too.

How. Each target is a function of where a point is and which bones carry it (its skin weights), not of the mesh it
belongs to, so every armour piece moves the way the skin under it moves and two parts meeting at a seam (a sleeve's
end, the boots' top) move alike. Each feature is a field round its bone: a point's place along the bone (t), the way
it faces from the bone's axis (front, back, out, in) and its weight on that bone choose how much it moves; it moves
straight out from the axis. How far is measured on the race's own body - the median radius of its bare clothes at
that place along the bone - not on the point's own distance, so a pauldron or a cloak a hand off the skin moves by
what the skin moves and doesn't balloon.

Limits (owner, on the plan: "within reasonable limits while also giving as much freedom as we can without getting
unrealistic"): every slider is -1 .. 1. At 1 a muscle grows by about half the limb's radius there (a strongman's arm),
the belly by most of the waist's (a heavy gut over the belt), the love handles and hips by under half; the traps and
shoulders rise by about 5 cm. At -1 a feature shrinks by less than it grows (the client scales the negative side:
figure.json body_shapes' last number) - flatter, never hollow.

The targets are written sparse (only the points a feature moves), with their normals.

    python body_morphs.py <figure.gltf> <out.gltf>
build_races.py runs it on every figure after the face shapes (skip with --no-body-shapes).
"""
import base64, json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import face_morphs  # noqa: E402
from face_morphs import G, weld, vertex_normals  # noqa: E402
face_morphs.NC.setdefault('MAT4', 16)

# name, label, group, women only
FEATURES = [
    ('weight', 'Weight', 'OVERALL', False), ('muscle', 'Muscle', 'OVERALL', False),
    ('chest_size', 'Bust', 'UPPER BODY', True),
    ('traps', 'Trapezius', 'UPPER BODY', False), ('upper_chest', 'Upper Chest', 'UPPER BODY', False), ('bust_lift', 'Bust Lift', 'UPPER BODY', True),
    ('bust_spacing', 'Bust Spacing', 'UPPER BODY', True), ('back_width', 'Back Width', 'UPPER BODY', False),
    ('belly', 'Belly', 'UPPER BODY', False), ('love_handles', 'Love Handles', 'UPPER BODY', False),
    ('delts', 'Shoulder Muscle', 'ARMS', False), ('biceps', 'Biceps', 'ARMS', False), ('triceps', 'Triceps', 'ARMS', False),
    ('forearms', 'Forearms', 'ARMS', False),
    ('hips', 'Hips', 'LOWER BODY', False), ('glutes', 'Glutes', 'LOWER BODY', False),
    ('hip_flare', 'Hip Flare', 'LOWER BODY', False), ('inner_thighs', 'Inner Thighs', 'LOWER BODY', False),
    ('quads', 'Front Thighs', 'LOWER BODY', False), ('hamstrings', 'Back Thighs', 'LOWER BODY', False),
    ('knees', 'Knees', 'LOWER BODY', False), ('ankles', 'Ankles', 'LOWER BODY', False),
]
PARTS = ('body', 'legs', 'boots', 'arms', 'gloves', 'cloak')
UP = np.array([0.0, 0.0, 1.0])
FRONT = np.array([0.0, -1.0, 0.0])                 # (the figures face -y, z up: the toes point -y)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def bump(x, a, peak, b):
    """0 at a, 1 at peak, 0 at b (smooth)."""
    return np.where(x < peak, smoothstep(a, peak, x), 1.0 - smoothstep(peak, b, x))


class Skel:
    def __init__(self, g):
        s = g.g['skins'][0]
        N = g.g['nodes']
        self.names = [N[j].get('name', '') for j in s['joints']]
        ibm = g.acc(s['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)
        bind = np.linalg.inv(ibm)
        self.pos = {n: bind[i][:3, 3] for i, n in enumerate(self.names)}
        self.idx = {n: i for i, n in enumerate(self.names)}

    def p(self, n):
        return self.pos['Bip01 ' + n]

    def group(self, J, W, names):
        """A point's summed weight on these bones."""
        ids = [self.idx['Bip01 ' + n] for n in names if 'Bip01 ' + n in self.idx]
        m = np.isin(J, ids)
        return (W * m).sum(1)


def seg_param(P, a, b):
    """Each point's place along a-b (t, unclamped) and its offset from the axis (clamped to the segment)."""
    ab = b - a
    t = ((P - a) @ ab) / max(ab @ ab, 1e-9)
    foot = a + np.clip(t, 0.0, 1.0)[:, None] * ab
    r = P - foot
    return t, r


def unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


class Body:
    """The race's body: its bones, its limbs as segments, and its bare radius along each."""

    def __init__(self, sk, base, parts=None):
        self.sk = sk
        p = sk.p
        self.z_pelvis, self.z_spine, self.z_spine1 = p('Pelvis')[2], p('Spine')[2], p('Spine1')[2]
        self.z_spine2, self.z_neck = p('Spine2')[2], p('Neck')[2]
        self.z_clav = (p('L Clavicle')[2] + p('L UpperArm')[2]) / 2
        self.y_axis = p('Spine1')[1]
        self.half_hips = abs(p('L Thigh')[0])
        self.limbs = {}
        for side, sx in (('L', 1.0), ('R', -1.0)):
            self.limbs[side + 'upper'] = (p(side + ' UpperArm'), p(side + ' Forearm'), sx)
            self.limbs[side + 'fore'] = (p(side + ' Forearm'), p(side + ' Hand'), sx)
            self.limbs[side + 'thigh'] = (p(side + ' Thigh'), p(side + ' Calf'), sx)
            self.limbs[side + 'calf'] = (p(side + ' Calf'), p(side + ' Foot'), sx)
        # the bare radius: the starter clothes' (body / legs / arms / gloves) median distance from each axis
        P, J, W = base
        self.R = {}
        groups = {'upper': ['UpperArm', 'BicepTwist'], 'fore': ['Forearm', 'ForeTwist', 'ForeTwist1'],
                  'thigh': ['Thigh', 'ThighTwist'], 'calf': ['Calf']}
        for kind, bones in groups.items():
            prof = np.zeros(11)
            for side in 'LR':
                a, b, _ = self.limbs[side + kind]
                w = sk.group(J, W, [side + ' ' + n for n in bones])
                t, r = seg_param(P, a, b)
                rho = np.linalg.norm(r, axis=1)
                for k in range(11):
                    sel = (w > 0.5) & (np.abs(t - k / 10) < 0.08)
                    prof[k] += np.median(rho[sel]) / 2 if sel.sum() > 3 else np.nan
            self.R[kind] = self._fill(prof)
        # the torso: by height, from the pelvis to the neck
        wt = sk.group(J, W, ['Pelvis', 'Spine', 'Spine1', 'Spine2'])
        hz = np.linspace(self.z_pelvis - 4, self.z_neck, 13)
        rho = np.linalg.norm((P - np.array([0, self.y_axis, 0]))[:, :2], axis=1)
        prof = np.array([np.median(rho[(wt > 0.5) & (np.abs(P[:, 2] - z) < 1.5)]) if ((wt > 0.5) & (np.abs(P[:, 2] - z) < 1.5)).sum() > 3
                         else np.nan for z in hz])
        self.torso_z, self.torso_R = hz, self._fill(prof)
        # the waist: the torso's narrowest between the hip joints and the ribs
        self.z_hip = (p('L Thigh')[2] + p('R Thigh')[2]) / 2
        self.thigh_len = np.linalg.norm(p('L Calf') - p('L Thigh'))
        zz = np.linspace(self.z_hip + 1.0, self.z_spine2, 24)
        self.z_waist = float(zz[np.argmin(self.torso_R_at(zz))])
        parts = parts or {}
        self.bust = self.glute = None
        if 'body' in parts:
            self.bust = self._mound(*parts['body'], ['Spine2'], FRONT, 0.22, None)
        zh = self.z_hip - 0.12 * self.thigh_len
        wl = sk.group(J, W, ['Pelvis', 'Spine', 'L Thigh', 'R Thigh', 'L ThighTwist', 'R ThighTwist'])
        sel = (wl > 0.5) & (np.abs(P[:, 2] - zh) < 1.5)
        self.hip_half = float(np.percentile(np.abs(P[sel, 0]), 98)) if sel.sum() > 10 else abs(p('L Thigh')[0]) * 2

    def _mound(self, P, J, W, T, bones, a, rfrac, zband):
        """The breasts or the buttocks on the bare clothes: each side's apex (furthest along a) and the mounds' radius
        across; then the wall under them - a membrane stretched over the region round both, pinned at its edge (each
        point the average of its neighbours) - and each point's bump, how far it stands off that wall.
        -> {'apex': {side: point}, 'rb': radius, 'src': points, 'bump': their bumps (only where they stand off)}"""
        w = self.sk.group(J, W, bones)
        sel = w > 0.5
        if zband:
            sel &= (P[:, 2] > zband[0]) & (P[:, 2] < zband[1])
        f = P @ a
        sel &= f > np.median(f[sel]) if sel.any() else sel
        if sel.sum() < 20:
            return None
        Wd = np.percentile(np.abs(P[sel, 0]), 98) * 2
        rb = rfrac * Wd
        out = {}
        for s in (1.0, -1.0):
            m = sel & (P[:, 0] * s > 0.12 * Wd) & (P[:, 0] * s < 0.42 * Wd)
            if m.sum() < 8:
                return None
            fm = f[m]
            top = P[m][fm >= np.percentile(fm, 96)]
            apex = top.mean(0)
            # the wall: points round the mound just past its edge - above, below and toward the middle (not the
            # flank, which curves away)
            d = P - apex
            dperp = np.linalg.norm(d - np.outer(d @ a, a), axis=1)
            ring = (w > 0.3) & (dperp > 1.15 * rb) & (dperp < 1.6 * rb) & (d[:, 0] * s < 0.5 * rb) & (f > np.median(f[sel]) - rb)
            out[s] = apex
        # the region: round each apex, on the facing side
        free = np.zeros(len(P), bool)
        wr = self.sk.group(J, W, ['Pelvis', 'Spine', 'Spine1', 'Spine2', 'L Thigh', 'R Thigh', 'L ThighTwist', 'R ThighTwist'])
        for s, apex in out.items():
            d = P - apex
            dp = np.linalg.norm(d - np.outer(d @ a, a), axis=1)
            free |= (wr > 0.5) & (dp < 1.5 * rb) & ((d @ a) > -2.5 * rb)
        grp = weld(P)
        ng = grp.max() + 1
        X = np.zeros((ng, 3))
        cnt = np.zeros(ng)
        np.add.at(X, grp, P)
        np.add.at(cnt, grp, 1)
        X /= cnt[:, None]
        fg = np.zeros(ng, bool)
        np.logical_or.at(fg, grp, free)
        pin = np.zeros(ng, bool)                             # a group with any point outside stays put
        np.logical_or.at(pin, grp, ~free)
        fg &= ~pin
        e = np.concatenate([grp[T[:, [0, 1]]], grp[T[:, [1, 2]]], grp[T[:, [2, 0]]]])
        e = np.concatenate([e, e[:, ::-1]])
        e = e[e[:, 0] != e[:, 1]]
        deg = np.bincount(e[:, 0], minlength=ng).astype(np.float64)
        M = X.copy()
        for _ in range(600):
            acc = np.zeros((ng, 3))
            np.add.at(acc, e[:, 0], M[e[:, 1]])
            nb = acc / np.maximum(deg, 1)[:, None]
            M[fg] = nb[fg]
        bg = X - M
        m = np.linalg.norm(bg, axis=1)
        top = np.percentile(m[m > 1e-4], 99) if (m > 1e-4).any() else 0.0
        bg *= smoothstep(0.15 * top, 0.45 * top, m)[:, None]      # (the ribs' own curve under the membrane stays put)
        for _ in range(12):                                         # and smooth, so the flat side doesn't ripple
            acc = np.zeros((ng, 3))
            np.add.at(acc, e[:, 0], bg[e[:, 1]])
            bg = 0.5 * bg + 0.5 * acc / np.maximum(deg, 1)[:, None]
        bump = bg[grp]
        keep = np.linalg.norm(bump, axis=1) > 1e-4
        return {'apex': out, 'rb': rb, 'a': a, 'src': P[keep], 'bump': bump[keep]}

    @staticmethod
    def _fill(a):
        a = np.array(a, dtype=np.float64)
        ok = ~np.isnan(a)
        if not ok.any():
            return np.full(len(a), 3.0)
        return np.interp(np.arange(len(a)), np.flatnonzero(ok), a[ok])

    def limb_R(self, kind, t):
        return np.interp(np.clip(t, 0, 1), np.linspace(0, 1, 11), self.R[kind])

    def torso_R_at(self, z):
        return np.interp(z, self.torso_z, self.torso_R)


def fields(body, P, J, W):
    """The primitive displacement fields for these points: {name: (n, 3)} at slider 1."""
    sk = body.sk
    n = len(P)
    out = {}
    # ---- the torso: radial from the spine's vertical axis
    c = np.zeros_like(P)
    c[:, 1] = body.y_axis
    c[:, 2] = P[:, 2]
    rv = P - c
    rv[:, 2] = 0.0
    rh = unit(rv)
    front = rh @ FRONT                                   # 1 front, -1 back
    side = np.abs(rh[:, 0])
    R = body.torso_R_at(P[:, 2])
    wt = sk.group(J, W, ['Pelvis', 'Spine', 'Spine1', 'Spine2'])
    wneck = sk.group(J, W, ['Neck'])
    wclav = sk.group(J, W, ['L Clavicle', 'R Clavicle'])
    z = P[:, 2]
    zp, zs, zs1, zs2, zn = body.z_pelvis, body.z_spine, body.z_spine1, body.z_spine2, body.z_neck
    # belly: the front below the ribs
    m = wt * bump(z, zp - 1.0, (zs + zs1) / 2, zs2 - 0.5) * np.clip(front, 0, 1) ** 1.3
    out['belly'] = rh * (R * 0.80 * m)[:, None]
    # love handles: the sides just above the hips, a little to the back
    m = wt * bump(z, zp, zs + 0.3 * (zs1 - zs), zs1 + 0.5 * (zs2 - zs1)) * side ** 2 * np.clip(1.0 - np.abs(front + 0.25), 0, 1)
    out['love_handles'] = rh * (R * 0.45 * m)[:, None]
    # back width (the lats): the back and sides under the shoulder blades, out to the sides
    m = wt * bump(z, zs1 - 1.0, zs2, zs2 + 0.6 * (zn - zs2)) * np.clip(side * 0.8 - front * 0.6, 0, 1)
    d = rh.copy()
    d[:, 1] *= 0.4
    out['back_width'] = unit(d) * (R * 0.38 * m)[:, None]
    # upper chest: the front above the nipples, below the collarbones
    m = (wt + wclav * 0.5) * bump(z, zs2 - 1.0, zs2 + 0.55 * (zn - zs2), zn - 0.5) * np.clip(front, 0, 1) ** 1.5 * (1 - smoothstep(4.5, 8.0, np.abs(P[:, 0])))
    out['upper_chest'] = rh * (R * 0.30 * m)[:, None]
    # bust (women; owner 2026-11-25: "scale from a more flat chested woman to one well endowed, while keeping a
    # natural breast shape at all stages") and glutes ("a more thick backside, to a more slender and toned one"):
    # each mound grows from the wall under it - its height above the wall scaled, its base a little wider, and a full
    # one sits a touch lower (so the thin side lifts) - nothing at its edge, so it never pulls at the tip
    # each point takes the bump of the bare skin nearest it (an armour plate or the skirt moves as the skin under it)
    for key, mound, bones, rise in (('chest_size', body.bust, ['Spine', 'Spine1', 'Spine2'], 0.12),):
        out[key] = np.zeros((n, 3))
        if mound is None or len(mound['src']) == 0:
            continue
        rb, S, B = mound['rb'], mound['src'], mound['bump']
        wg = sk.group(J, W, bones)
        lo, hi = S.min(0) - 1.2 * rb, S.max(0) + 1.2 * rb
        near = np.flatnonzero(np.all((P > lo) & (P < hi), axis=1) & (wg > 0.05))
        D = np.zeros((n, 3))
        for i0 in range(0, len(near), 1500):
            ii = near[i0:i0 + 1500]
            d2 = ((P[ii, None, :] - S[None, :, :]) ** 2).sum(-1)
            k = np.argsort(d2, axis=1)[:, :4]
            dk = np.sqrt(np.take_along_axis(d2, k, 1))
            wk = 1.0 / (dk + 0.05) ** 2
            v = (B[k] * wk[:, :, None]).sum(1) / wk.sum(1)[:, None]
            D[ii] = v * (1 - smoothstep(0.5 * rb, 1.1 * rb, dk[:, 0]))[:, None]
        D *= wg[:, None]
        mag = np.linalg.norm(D, axis=1)
        # a full mound spreads a little across and sits a touch lower; the thin side lifts
        spread = np.zeros((n, 3))
        for s, apex in mound['apex'].items():
            q = P - apex
            perp = q - np.outer(q @ mound['a'], mound['a'])
            spread += unit(perp) * (mag * 0.2 * (P[:, 0] * s > 0))[:, None]
        out[key] = (D + spread - np.outer(mag * rise, UP)) * 0.5
    # glutes: each buttock a rounded swell straight back, by where a point is across and up - the skin, the trousers
    # and a tunic's skirt over them all move alike (the skirt flares below); a full seat sits a touch lower
    wl = sk.group(J, W, ['Pelvis', 'Spine', 'L Thigh', 'R Thigh', 'L ThighTwist', 'R ThighTwist'])
    Rs = float(body.torso_R_at(body.z_hip))
    behind = smoothstep(0.0, 0.4 * Rs, P[:, 1] - body.y_axis)          # (+y is behind)
    cz = body.z_hip - 0.2 * body.thigh_len
    g = np.zeros(n)
    for s in (1.0, -1.0):
        cx = s * 0.45 * body.hip_half
        g += np.exp(-((P[:, 0] - cx) / (0.34 * body.hip_half)) ** 2 - ((z - cz) / (0.26 * body.thigh_len)) ** 2)
    amt = wl * behind * np.minimum(g, 1.0) * Rs * 0.28
    out['glutes'] = np.outer(amt, -FRONT) - np.outer(amt * 0.2, UP)
    # hips (owner: "allow for more of an hourglass figure"): out to the sides at the hip joints, nothing at the waist
    # and nothing by mid-thigh; the inner thighs and the legs' spacing stay
    wl = sk.group(J, W, ['Pelvis', 'Spine', 'L Thigh', 'R Thigh', 'L ThighTwist', 'R ThighTwist'])
    zh = body.z_hip - 0.12 * body.thigh_len
    prof = bump(z, body.z_hip - 0.7 * body.thigh_len, zh, max(body.z_waist, zh + 1.0))
    gx = smoothstep(0.25 * body.hip_half, 1.0 * body.hip_half, np.abs(P[:, 0]))
    out['hips'] = np.outer(np.sign(P[:, 0]) * wl * prof * gx * body.hip_half * 0.2, np.array([1.0, 0, 0]))
    # bust (women): lift and spacing of the region the shader's bust bulge swells
    bust = wt * bump(z, zs1 + 0.3 * (zs2 - zs1), zs2 + 0.15 * (zn - zs2), zn - 1.0) * np.clip(front - 0.25, 0, 1) * bump(np.abs(P[:, 0]), 0.3, 2.6, 6.0)
    out['bust_lift'] = np.outer(bust, UP) * (zn - zs2) * 0.22
    sx = np.sign(P[:, 0])
    out['bust_spacing'] = np.outer(bust * sx, np.array([1.0, 0, 0])) * 1.1
    # traps: the slope from the neck to the shoulder - up and a little out, nothing at the neck's top (the head's seam)
    ax = np.abs(P[:, 0])
    m = (wt + wneck + wclav) * bump(z, zs2 + 0.4 * (zn - zs2), body.z_clav + 0.8, zn + 1.2) * bump(ax, 0.8, 3.0, 6.5) \
        * np.clip(-front * 0.3 + 0.7, 0, 1) * (1 - smoothstep(zn + 0.2, zn + 1.6, z))
    out['traps'] = np.outer(m, UP) * 2.2
    # (shoulder slope: the clavicles turned, Fig3Figure.BodyShape - owner 2026-11-25, the shape pushed "at a weird point")
    # ---- the limbs: radial from each bone, by the side facing
    for k in ('delts', 'biceps', 'triceps', 'forearms', 'hip_flare', 'inner_thighs', 'quads', 'hamstrings', 'knees', 'ankles'):
        out[k] = np.zeros((n, 3))
    for side in 'LR':
        sxv = np.array([1.0 if side == 'L' else -1.0, 0, 0])
        a, b, _ = body.limbs[side + 'upper']
        t, r = seg_param(P, a, b)
        rh = unit(r)
        w = sk.group(J, W, [side + ' UpperArm', side + ' BicepTwist', side + ' Pauldron', side + ' Clavicle'])
        Ru = body.limb_R('upper', t)
        outward = rh @ sxv                                # away from the body
        fr = rh @ FRONT
        m = w * bump(t, -0.25, 0.12, 0.55) * np.clip(outward * 0.7 + 0.5, 0, 1)
        out['delts'] += rh * (Ru * 0.45 * m)[:, None]
        wa = sk.group(J, W, [side + ' UpperArm', side + ' BicepTwist'])
        m = wa * bump(t, 0.15, 0.58, 1.0) * np.clip(fr, 0, 1) ** 1.2
        out['biceps'] += rh * (Ru * 0.55 * m)[:, None]
        m = wa * bump(t, 0.1, 0.45, 0.95) * np.clip(-fr, 0, 1) ** 1.2
        out['triceps'] += rh * (Ru * 0.45 * m)[:, None]
        a, b, _ = body.limbs[side + 'fore']
        t, r = seg_param(P, a, b)
        rh = unit(r)
        w = sk.group(J, W, [side + ' Forearm', side + ' ForeTwist', side + ' ForeTwist1'])
        m = w * bump(t, -0.05, 0.28, 0.85)
        out['forearms'] += rh * (body.limb_R('fore', t) * 0.40 * m)[:, None]
        # the thigh
        a, b, _ = body.limbs[side + 'thigh']
        t, r = seg_param(P, a, b)
        rh = unit(r)
        Rt = body.limb_R('thigh', t)
        w = sk.group(J, W, [side + ' Thigh', side + ' ThighTwist'])
        wp = sk.group(J, W, ['Pelvis', 'Spine'])
        outward = rh @ sxv
        fr = rh @ FRONT
        m = (w + wp * 0.6) * bump(t, -0.2, 0.12, 0.5) * np.clip(outward, 0, 1) ** 1.2
        out['hip_flare'] += rh * (Rt * 0.42 * m)[:, None]
        m = w * bump(t, -0.05, 0.25, 0.7) * np.clip(-outward, 0, 1) ** 1.3
        out['inner_thighs'] += rh * (Rt * 0.38 * m)[:, None]
        m = w * bump(t, 0.05, 0.55, 0.95) * np.clip(fr, 0, 1) ** 1.2
        out['quads'] += rh * (Rt * 0.38 * m)[:, None]
        m = w * bump(t, 0.05, 0.45, 0.9) * np.clip(-fr, 0, 1) ** 1.2
        out['hamstrings'] += rh * (Rt * 0.34 * m)[:, None]
        # the knee: the thigh's end and the calf's top, all round, a little more to the front
        wk = sk.group(J, W, [side + ' Thigh', side + ' ThighTwist', side + ' Calf'])
        ac, bc, _ = body.limbs[side + 'calf']
        tc, rc = seg_param(P, ac, bc)
        dk = np.linalg.norm(P - ac, axis=1)
        rk = unit(P - ac - np.outer(((P - ac) @ unit((bc - ac)[None])[0]), unit((bc - ac)[None])[0]))
        m = wk * (1 - smoothstep(0.0, body.limb_R('calf', 0.0) * 1.6, dk)) * np.clip(rk @ FRONT * 0.4 + 0.6, 0, 1)
        out['knees'] += rk * (body.limb_R('calf', np.zeros(n)) * 0.32 * m)[:, None]
        # the ankle: the calf's lower end
        rh = unit(rc)
        w = sk.group(J, W, [side + ' Calf'])
        m = w * bump(tc, 0.55, 0.88, 1.12)
        out['ankles'] += rh * (body.limb_R('calf', tc) * 0.35 * m)[:, None]
    # ---- the mixes
    out['weight'] = (out['belly'] * 0.8 + out['love_handles'] * 0.8 + out['back_width'] * 0.3 + out['upper_chest'] * 0.2
                     + out['triceps'] * 0.6 + out['biceps'] * 0.25 + out['forearms'] * 0.2 + out['hip_flare'] * 0.6
                     + out['inner_thighs'] * 0.7 + out['hamstrings'] * 0.3 + out['quads'] * 0.2 + out['knees'] * 0.3
                     + out['ankles'] * 0.25 + out['traps'] * 0.3)
    out['muscle'] = (out['delts'] * 0.8 + out['biceps'] * 0.8 + out['triceps'] * 0.6 + out['forearms'] * 0.6
                     + out['traps'] * 0.6 + out['back_width'] * 0.7 + out['upper_chest'] * 0.7 + out['quads'] * 0.7
                     + out['hamstrings'] * 0.4 - out['belly'] * 0.35 - out['love_handles'] * 0.4)
    for k, f in SCALE.items():
        out[k] = out[k] * f
    return out


# below 0 a feature shrinks by this share of what it grows (flatter, never hollow)
SHRINK = {'belly': 0.1, 'love_handles': 1.0, 'weight': 0.55, 'muscle': 0.5,       # (the client scales a slider's negative side)
          'chest_size': 1.3, 'glutes': 0.6, 'hips': 0.6}
# the owner's ranges (2026-11-25): back width halved, traps -20%, belly's full side -10% (its thin side ~15% of what it
# was: SHRINK), love handles' full side -30% (thin side as was)
SCALE = {'back_width': 0.5, 'traps': 0.8, 'belly': 0.9, 'love_handles': 0.7}


def add_sparse(g, d, normals):
    """A sparse morph target: only the points that move (POSITION and NORMAL share the index list)."""
    moved = np.flatnonzero((np.abs(d).max(1) > 1e-5) | (np.abs(normals).max(1) > 1e-5))
    count = len(d)
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
        full = np.zeros((count, 3), np.float32)
        full[moved] = vals
        g.g['accessors'].append({'componentType': 5126, 'count': count, 'type': 'VEC3',
                                 'min': full.min(0).tolist(), 'max': full.max(0).tolist(),
                                 'sparse': {'count': int(len(moved)), 'indices': {'bufferView': iv, 'componentType': 5125},
                                            'values': {'bufferView': vv}}})
        out.append(len(g.g['accessors']) - 1)
    return out


def run(src, out, female=None):
    g = G(src)
    sk = Skel(g)
    nodes = [n for n in g.g['nodes'] if 'mesh' in n and n.get('name', '').split('_v')[0].split('_')[0] in PARTS]
    if female is None:
        female = Path(src).resolve().parent.name.endswith('_f')
    feats = [f for f in FEATURES if female or not f[3]]

    def prim_data(prim):
        a = prim['attributes']
        P = g.acc(a['POSITION']).astype(np.float64)
        J = g.acc(a['JOINTS_0']).astype(np.int64)
        W = g.acc(a['WEIGHTS_0']).astype(np.float64)
        if W.dtype != np.float64 or W.max() > 1.5:
            W = W / max(W.max(), 1)
        return P, J, W

    # the bare body: the starter clothes
    base = [], [], []
    by_part = {}
    tris = {}
    for n in nodes:
        if n['name'] in ('body', 'legs', 'boots', 'arms', 'gloves'):
            for prim in g.g['meshes'][n['mesh']]['primitives']:
                bp = by_part.setdefault(n['name'], ([], [], []))
                off = sum(len(x) for x in bp[0])
                tris.setdefault(n['name'], []).append(g.acc(prim['indices']).astype(np.int64).reshape(-1, 3) + off)
                for lst, l2, v in zip(base, bp, prim_data(prim)):
                    lst.append(v)
                    l2.append(v)
    body = Body(sk, tuple(np.concatenate(x) for x in base), {k: tuple(np.concatenate(x) for x in v) + (np.concatenate(tris[k]),)
                                                             for k, v in by_part.items()})
    total = 0
    for n in nodes:
        mesh = g.g['meshes'][n['mesh']]
        names = mesh.get('extras', {}).get('targetNames', [])
        if any(x.startswith('bx_') for x in names):
            raise SystemExit('already has bx_ targets')
        for prim in mesh['primitives']:
            P, J, W = prim_data(prim)
            Nm = g.acc(prim['attributes']['NORMAL']).astype(np.float64)
            T = g.acc(prim['indices']).astype(np.int64).reshape(-1, 3)
            F = fields(body, P, J, W)
            grp = weld(P)
            n0 = vertex_normals(P, T, grp)
            # a part's own hard edges keep their normals: the target's normal moves by the change of the smooth one
            for name, _, _, _ in feats:
                d = F[name]
                dn = vertex_normals(P + d, T, grp) - n0
                pa, na = add_sparse(g, d, dn)
                prim.setdefault('targets', []).append({'POSITION': pa, 'NORMAL': na})
                total += int((np.abs(d).max(1) > 1e-5).sum())
        mesh.setdefault('extras', {})['targetNames'] = names + ['bx_' + f[0] for f in feats]
        if 'weights' in mesh or names:
            mesh['weights'] = mesh.get('weights', [0.0] * len(names)) + [0.0] * len(feats)
        print('%-10s %-16s %6d points' % (n['name'], mesh.get('name', ''), sum(g.g['accessors'][p['attributes']['POSITION']]['count'] for p in mesh['primitives'])))
    print('torso radius', np.round(body.torso_R, 2).tolist())
    print('limb radius', {k: np.round(v, 2).tolist() for k, v in body.R.items()})
    print('moved points (all targets)', total)
    g.save(out)
    meta_path = Path(src).with_name('figure.json')
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        meta['body_shapes'] = [[f[0], f[1], f[2], SHRINK.get(f[0], 0.85)] for f in feats]
        Path(out).with_name('figure.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print('wrote', out)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
