"""The HD head's face maps (the HD look, owner 2026-11-25: makeup, brows, a smoother skin - "Dragon's Dogma 2's
character creator ... a gold standard"). The head has one layout for every race, so what the creator paints on it is
drawn here once, from the head itself, and the client draws the rest in face space:

  hd_face.png   each texel's face-space point, 16 bits a coordinate (r, g: u across in eye spacings - the eyes at
                -0.5 / +0.5 - high and low byte; b, a: v up, the eyes at 0). Face space is the classic skin layers' own
                (pipeline/skin_layers.py), so their war paints fit as they are, and the brows, liner, shadow, blush
                and freckles are drawn in it at draw time - placed by the player's sliders.
  hd_mask.png   r: the lips (their red, its edge sharp); g: the eyes' rim (1 on the lid's edge where it meets the
                eyeball, falling to 0 a third of an eye spacing out - the liner's width and the shadow's reach are
                thresholds on it); b: how much the texel is face (1 on the front, 0 round the ears and back - makeup
                and paint keep to it); a: the scalp (hairline up).
"""
import numpy as np, cv2
import hd_tex

U_RANGE = (-4.0, 4.0)
V_RANGE = (-6.0, 4.0)


def sphere_fit(X):
    A = np.c_[2 * X, np.ones(len(X))]
    b = (X * X).sum(1)
    s, *_ = np.linalg.lstsq(A, b, rcond=None)
    c = s[:3]
    return c, float(np.sqrt(s[3] + c @ c))


def encode16(x, lo, hi):
    q = np.clip((x - lo) / (hi - lo), 0, 1) * 65535.0
    q = np.round(q).astype(np.uint32)
    return (q >> 8).astype(np.uint8), (q & 255).astype(np.uint8)


def frame(res):
    """The face frame: the eyes' middle, the eye spacing, and the landmarks in face space."""
    L = res['L']
    em = (L['eyeL'] + L['eyeR']) / 2
    E = abs(L['eyeL'][0] - L['eyeR'][0])
    fs = lambda p: [round(float((p[0] - em[0]) / E), 4), round(float((p[2] - em[2]) / E), 4)]
    land = {k: fs(L[k]) for k in ('browL', 'mouthL', 'nose', 'chin', 'jawL')}
    return em, E, land


def maps(res, img, mask, M, lip_m, scalp, log=print, brow=None):
    """img: the raster of [Q (3), ...] (padded); M: MakeHuman's skin in this layout (0..1 BGR); lip_m: the lips'
    weight per texel (MakeHuman's lip shapes); scalp: per texel. -> (hd_face BGRA, hd_mask BGRA, info)."""
    Q = img[..., :3].astype(np.float64)
    em, E, land = frame(res)
    u = (Q[..., 0] - em[0]) / E
    v = (Q[..., 2] - em[2]) / E
    fwd = (em[1] - Q[..., 1]) / E                       # (figure axes: -y is forward)
    uh, ul = encode16(u, *U_RANGE)
    vh, vl = encode16(v, *V_RANGE)
    face = np.dstack([vh, ul, uh, vl])                  # (BGRA: r = u high, g = u low, b = v high, a = v low)
    # the eyes' rim: how near the skin lies to the eyeball's surface, on the eye's front
    X = res['pieces']['eyes']['X']
    rim = np.zeros(u.shape, np.float32)
    corners = {}
    for sd, sel in (('L', X[:, 0] > 0), ('R', X[:, 0] <= 0)):
        c, r = sphere_fit(X[sel])
        d = np.linalg.norm(Q - c, axis=-1)
        cl = (d - r) / E
        front = np.clip(((c[1] - Q[..., 1]) / r - 0.1) / 0.5, 0, 1)     # (in front of the eye's middle)
        near = np.clip(1 - cl / 0.33, 0, 1) ** 1.3 * front * np.clip((3.2 * r - d) / (0.8 * r), 0, 1)
        rim = np.maximum(rim, cv2.GaussianBlur(near.astype(np.float32), (0, 0), 2.0))
        # the eye's corners in face space: the rim's outermost and innermost points at the lid's edge
        edge = (near > 0.9) & mask
        uu = u[edge]; vv = v[edge]
        if len(uu):
            o = np.argmax(np.abs(uu)); i_ = np.argmin(np.abs(uu))
            corners[sd] = [[round(float(uu[o]), 3), round(float(vv[o]), 3)], [round(float(uu[i_]), 3), round(float(vv[i_]), 3)]]
    # the lips: MakeHuman's skin is redder there (Lab a*) than the skin round them - its edge, inside the reach of
    # MakeHuman's lip shapes, holes closed
    lab = cv2.cvtColor(np.clip(M * 255, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    a = lab[..., 1]
    ring = mask & (lip_m > 0.01) & (lip_m < 0.2)
    core = mask & (lip_m > 0.7)
    if ring.any() and core.any():
        a0, a1 = np.median(a[ring]), np.median(a[core])
        s_ = np.clip((a - a0) / max(a1 - a0, 1.0), 0, 1.2) * np.clip(lip_m / 0.15, 0, 1)
        s_ = cv2.GaussianBlur(s_.astype(np.float32), (0, 0), 1.5)
        lips = np.clip((s_ - 0.3) / 0.35, 0, 1)
        lips = cv2.morphologyEx(lips, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        lips = cv2.GaussianBlur(lips, (0, 0), 1.0)
    else:
        lips = np.zeros_like(rim)
    # how much is face: the front, fading round the cheeks to the ears and up the forehead into the scalp
    facew = np.clip((fwd + 0.2) / 0.6, 0, 1) * np.clip((1.35 - np.abs(u)) / 0.3, 0, 1)
    out = np.dstack([facew, rim, lips, scalp])          # (BGRA: r = lips, g = rim, b = face, a = scalp)
    out = np.clip(out * 255, 0, 255).astype(np.uint8)
    info = {'u_range': list(U_RANGE), 'v_range': list(V_RANGE), 'land': land, 'corners': corners,
            'brow': brow_line(u, v, mask, brow, corners, log)}
    log('  face maps: eye corners %s' % corners)
    return face, out, info


def brow_line(u, v, mask, brow, corners, log=print):
    """Where this race's brows go (owner 2026-11-25: the HD brows "look kind of small and oddly placed, like they're up
    high and in"): the race's own painted brows (the classic face's, brought onto this head - brow: their mask in this
    layout), fitted in face space: the inner end, the length, the height there, the slope from end to end, the arch
    above that line and the half-thickness. Without them: from the eye's corners."""
    cs = [c for c in corners.values()] if corners else []
    uo = float(np.mean([abs(c[0][0]) for c in cs])) if cs else 0.72
    ui = float(np.mean([abs(c[1][0]) for c in cs])) if cs else 0.22
    out = {'u0': round(ui - 0.03, 3), 'len': round(uo + 0.16 - (ui - 0.03), 3), 'v0': 0.24, 'slope': 0.0, 'arch': 0.04, 'th': 0.045}
    if brow is None:
        log('  brows: from the eyes\' corners (no painted brows to follow)')
        return out
    au = np.abs(u)
    sel = mask & (brow > 0.25) & (v > -0.1) & (v < 0.9) & (au < 1.2)
    if sel.sum() < 200:
        log('  brows: from the eyes\' corners (the painted brows too faint)')
        return out
    u0, u1 = np.percentile(au[sel], [3, 97])
    xs, vs, ws, ths = [], [], [], []
    for us in np.linspace(u0 + 0.03, u1 - 0.03, 12):
        s_ = sel & (np.abs(au - us) < 0.03)
        if s_.sum() < 8:
            continue
        w = brow[s_]
        xs.append(us - u0); vs.append(float((v[s_] * w).sum() / w.sum())); ws.append(float(w.sum()))
        lo, hi = np.percentile(v[s_], [10, 90])
        ths.append((hi - lo) / 2)
    if len(xs) < 4:
        return out
    a, b, c = np.polyfit(xs, vs, 2, w=np.sqrt(ws))[::-1]
    L = float(u1 - u0)
    v0 = a
    slope = (b * L + c * L * L) / L                     # (the chord from end to end)
    arch = -c * L * L / 4                               # (the middle above the chord)
    th = float(np.clip(np.median(ths) * 0.85, 0.045, 0.075))   # (never thinner than a full natural brow)
    out = {'u0': round(float(u0), 3), 'len': round(L, 3), 'v0': round(float(v0), 3), 'slope': round(float(slope), 3),
           'arch': round(float(np.clip(arch, -0.02, 0.12)), 3), 'th': round(th, 3)}
    log('  brows: the race\'s own - from %.2f across, %.2f long, %.2f up, slope %.2f, arch %.2f, half-thickness %.3f' % (
        out['u0'], out['len'], out['v0'], out['slope'], out['arch'], out['th']))
    return out


T_RANGE = (-2.2, 2.2, -2.6, 2.4)      # the tattoo map's face space: u across, v up
T_RES = 0.01                          # face units a texel


def tattoo_map(res, img, mask, cuv, facew=None):
    """Face space -> the classic face's UV (owner 2026-11-26: the race tattoos on the HD head with their own position,
    size and turn): each texel of a grid over the face holds the classic UV there (16 bits a coordinate, as the remap),
    so the client reads a tattoo at any face-space point - moved, scaled, turned. -> (BGRA image, range)."""
    from scipy import ndimage
    Q = img[..., :3].astype(np.float64)
    em, E, _ = frame(res)
    u = (Q[..., 0] - em[0]) / E
    v = (Q[..., 2] - em[2]) / E
    fwd = (em[1] - Q[..., 1]) / E
    u0, u1, v0, v1 = T_RANGE
    W = int(round((u1 - u0) / T_RES)); H = int(round((v1 - v0) / T_RES))
    sel = mask & (fwd > -0.25) & (u > u0) & (u < u1) & (v > v0) & (v < v1)
    ix = ((u[sel] - u0) / T_RES).astype(int).clip(0, W - 1)
    iy = ((v1 - v[sel]) / T_RES).astype(int).clip(0, H - 1)
    acc = np.zeros((H, W, 2)); cnt = np.zeros((H, W)); fw = np.full((H, W), -1e9)
    # the front-most texel wins each cell (the face, not the jaw's underside behind it)
    order = np.argsort(fwd[sel])
    acc[iy[order], ix[order]] = cuv[sel][order]
    cnt[iy[order], ix[order]] = 1
    have = cnt > 0
    have = ndimage.binary_closing(have, iterations=2) & have | have
    dist, (jy, jx) = ndimage.distance_transform_edt(~have, return_indices=True)
    out = acc[jy, jx]
    out = cv2.GaussianBlur(out.astype(np.float32), (0, 0), 0.7)
    import hd_tex
    rgba = hd_tex.encode_remap(out, dist < 40)
    return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA), list(T_RANGE)
