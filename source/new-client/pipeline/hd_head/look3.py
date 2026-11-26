"""The HD look's drawing, as the client's head shader does it (Fig3Figure: hd_look in the fragment shader) - in numpy,
for previews while tuning: brows, liner, shadow, lipstick and liner, blush, contour, skin detail. Keep in step with the
shader (same names, same numbers)."""
import numpy as np, cv2

PI = np.pi


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def decode_face(path, info):
    f = cv2.imread(str(path), -1).astype(np.float64)       # BGRA
    u = (f[..., 2] * 256 + f[..., 1]) / 65535.0
    v = (f[..., 0] * 256 + f[..., 3]) / 65535.0
    u0, u1 = info['u_range']; v0, v1 = info['v_range']
    return u0 + u * (u1 - u0), v0 + v * (v1 - v0)


# the brow shapes: [label, inner u shift, arch (eye spacings), peak (0..1 along), slope, half-thickness, inner frac,
# tail frac, length scale, coarse, gap]
BROWS = [
    ['Natural',      0.00, 0.050, 0.62,  0.00, 0.040, 1.00, 0.35, 1.00, 0.0, 0.0],
    ['Soft Arch',    0.00, 0.075, 0.58, -0.02, 0.036, 0.95, 0.30, 1.00, 0.0, 0.0],
    ['High Arch',    0.01, 0.120, 0.55, -0.05, 0.033, 0.90, 0.28, 0.98, 0.0, 0.0],
    ['Straight',     0.00, 0.015, 0.60,  0.00, 0.040, 1.00, 0.45, 1.02, 0.0, 0.0],
    ['Angled',       0.00, 0.100, 0.68,  0.06, 0.038, 0.85, 0.30, 1.00, 0.0, 0.0],
    ['Thick',        0.00, 0.040, 0.62,  0.00, 0.058, 1.00, 0.45, 1.00, 0.4, 0.0],
    ['Bushy',       -0.02, 0.040, 0.62,  0.02, 0.066, 1.05, 0.55, 1.03, 1.0, 0.0],
    ['Thin',         0.01, 0.060, 0.60, -0.02, 0.022, 0.90, 0.40, 0.98, 0.0, 0.0],
    ['Rounded',      0.00, 0.095, 0.50, -0.04, 0.038, 0.95, 0.35, 0.96, 0.0, 0.0],
    ['Feathered',    0.00, 0.060, 0.60,  0.00, 0.046, 1.00, 0.30, 1.00, 0.2, 0.0],
    ['Tapered',      0.00, 0.065, 0.60, -0.02, 0.050, 1.10, 0.15, 1.04, 0.0, 0.0],
    ['Scarred',      0.00, 0.055, 0.62,  0.00, 0.042, 1.00, 0.35, 1.00, 0.2, 0.42],
]


def brow(au, v, base, p, sl, hair):
    """-> (coverage 0..1, the brow's middle line v there). base: [inner u, inner v]; p: the shape; sl: the sliders
    (thick, arch, tail, space, height, angle) -1..1; hair: the hair texture (H, W, 3) float BGR."""
    _, du, arch, peak, slope, th, fi, ft, ls, coarse, gap = p
    thick, arch_s, tail, space, height, angle = sl
    u0 = base[0] + du + 0.06 * space
    ln = 0.64 * ls * (1 + 0.2 * tail)
    x = au - u0
    t = x / ln
    k = np.log(0.5) / np.log(peak)
    bump = np.sin(PI * np.clip(t, 0, 1) ** k)
    vc = base[1] + 0.06 * height + (slope + 0.08 * angle) * x + arch * (1 + 0.6 * arch_s) * bump
    w = 1.3 * th * (1 + 0.45 * thick) * (fi + (1 - fi) * smoothstep(0, 0.35, t)) * (1 + (ft - 1) * smoothstep(peak, 1.0, t))
    s = (v - vc) / np.maximum(w, 1e-4)
    body = 1 - smoothstep(0.55, 1.0, np.abs(s))
    ends = smoothstep(-0.03, 0.10, t) * (1 - smoothstep(0.86, 1.0, t))
    if gap > 0:
        ends = ends * smoothstep(0.02, 0.05, np.abs(t - gap))
    # the hairs: the texture in the brow's frame - the head's standing hairs fading into the body's lying ones
    Hh, Ww = hair.shape[0] // 2, hair.shape[1]
    tx = (x / 0.4 * Ww) % Ww
    ty = np.clip(0.5 - s / (2 * 1.4), 0, 1) * (Hh - 1)
    def samp(row):
        mx = tx.astype(np.float32); my = (ty + row * Hh).astype(np.float32)
        hm = cv2.remap(hair, mx, my, cv2.INTER_LINEAR)
        return hm[..., 2] * (1 - coarse) + hm[..., 1] * coarse
    hh = samp(0) * (1 - smoothstep(0.05, 0.25, t)) + samp(1) * smoothstep(0.05, 0.25, t)
    inside = 1 - smoothstep(0.85, 1.35, np.abs(s))
    a = np.clip(0.45 * body + 1.2 * hh * inside, 0, 1) * ends
    a = a * (np.abs(s) < 1.6)
    return a, vc


def eye_line(au, corners):
    (uo, vo), (ui, vi) = corners
    return vi + (vo - vi) * (au - ui) / (uo - ui)


def liner(au, v, dist, corners, up_w, lo_w, wing, smudge):
    ve = eye_line(au, corners)
    upper = smoothstep(-0.015, 0.015, v - ve)
    soft = 0.35 + 0.5 * smudge
    lu = (1 - smoothstep(up_w * (1 - soft), up_w * (1 + soft * 0.5), dist)) * upper
    lw_ = max(lo_w, 0.002)
    ll = (1 - smoothstep(lw_ * (1 - soft), lw_ * (1 + soft * 0.5), dist)) * (1 - upper) * (lo_w > 0.002)
    (uo, vo), _ = corners
    a = np.radians(22)
    px, py = au - (uo - 0.03), v - (vo + 0.01)
    along = px * np.cos(a) + py * np.sin(a)
    across = -px * np.sin(a) + py * np.cos(a)
    wl = 0.04 + 0.2 * wing
    wid = up_w * 0.75 * np.clip(1 - along / wl, 0, 1)
    wg = (along > 0) * (along < wl) * (1 - smoothstep(wid * 0.6, wid + 0.004, np.abs(across))) * (wing > 0.01)
    return np.clip(np.maximum(np.maximum(lu, ll), wg), 0, 1)


def shadow(au, v, dist, corners, style, size, vbrow):
    (uo, vo), (ui, vi) = corners
    ve = eye_line(au, corners)
    upper = smoothstep(-0.02, 0.02, v - ve)
    sz = 1 + 0.5 * size
    along = smoothstep(ui - 0.06, ui + 0.04, au) * (1 - smoothstep(uo + 0.02 * sz, uo + 0.12 * sz, au))
    if style == 1:      # Soft: the lid
        m = upper * (1 - smoothstep(0.05 * sz, 0.15 * sz, dist)) * along
    elif style == 2:    # Smoky: lid and under, darkest out
        m = (upper * (1 - smoothstep(0.04 * sz, 0.2 * sz, dist)) + 0.45 * (1 - upper) * (1 - smoothstep(0.02 * sz, 0.11 * sz, dist))) \
            * (0.55 + 0.45 * smoothstep(ui, uo, au)) * smoothstep(ui - 0.06, ui + 0.04, au) * (1 - smoothstep(uo + 0.08 * sz, uo + 0.2 * sz, au))
    elif style == 3:    # Winged: the lid swept out and up
        a = np.radians(28)
        px, py = au - uo, v - (vo + 0.04)
        al = px * np.cos(a) + py * np.sin(a); ac = -px * np.sin(a) + py * np.cos(a)
        wingm = np.exp(-(np.clip(al, 0, None) / (0.16 * sz)) ** 2 - (ac / (0.05 * sz)) ** 2) * (al > -0.1)
        m = np.maximum(upper * (1 - smoothstep(0.05 * sz, 0.14 * sz, dist)) * along, wingm * upper)
    elif style == 4:    # To the brow
        m = upper * (1 - smoothstep(vbrow - 0.1 * sz, vbrow - 0.02, v)) * smoothstep(ui - 0.04, ui + 0.06, au) \
            * (1 - smoothstep(uo + 0.04 * sz, uo + 0.16 * sz, au))
    elif style == 5:    # Halo: the lid's middle, light
        uc = 0.5 * (ui + uo)
        m = upper * np.exp(-((au - uc) / (0.14 * sz)) ** 2 - (np.clip(dist, 0, None) / (0.13 * sz)) ** 2) * 1.2
    else:
        m = np.zeros_like(au)
    return np.clip(m, 0, 1)


def blush(au, v, size, height):
    sz = 1 + 0.4 * size
    cy = -0.42 + 0.12 * height
    return np.exp(-(((au - 0.62) / (0.2 * sz)) ** 2 + ((v - cy) / (0.15 * sz)) ** 2) * 1.2)


def contour(au, v):
    # under the cheekbone (a band from the ear's front down towards the mouth's corner), the nose's sides
    a0 = np.array([1.0, -0.38]); a1 = np.array([0.55, -0.74])
    d = a1 - a0
    t = np.clip(((au - a0[0]) * d[0] + (v - a0[1]) * d[1]) / (d @ d), 0, 1)
    dist = np.hypot(au - (a0[0] + t * d[0]), v - (a0[1] + t * d[1]))
    cheek = np.exp(-(dist / 0.07) ** 2) * (1 - 0.6 * t)
    nose = np.exp(-((au - 0.12) / 0.035) ** 2) * smoothstep(-0.7, -0.5, v) * (1 - smoothstep(0.05, 0.25, v))
    return np.clip(cheek + 0.7 * nose, 0, 1)


def lin(c):
    return np.power(np.array(c, float), 2.2)


def compose(base, face_uv, mask, hair, look, info):
    """base: hd_base (H, W, 3) RGB 0..1 (the skin tone already in); -> the coloured skin, RGB 0..1 (linear-ish)."""
    u, v = face_uv
    au = np.abs(u)
    lips, rim, facew = mask[..., 2], mask[..., 1], mask[..., 0]
    dist = 0.33 * (1 - np.power(np.clip(rim, 0, 1), 1 / 1.3))
    cs = info['corners']
    corners = [[(abs(cs['L'][0][0]) + abs(cs['R'][0][0])) / 2, (cs['L'][0][1] + cs['R'][0][1]) / 2],
               [(abs(cs['L'][1][0]) + abs(cs['R'][1][0])) / 2, (cs['L'][1][1] + cs['R'][1][1]) / 2]]
    col = np.power(base, 2.2)
    lum0 = (col @ [0.3, 0.59, 0.11])
    ref = np.median(lum0)
    shade = np.clip(lum0 / max(ref, 1e-3), 0.55, 1.25)[..., None]
    mix = lambda c, t, m: c * (1 - m[..., None]) + t * m[..., None]
    if look.get('contour', 0) > 0:
        col = col * (1 - 0.45 * look['contour'] * contour(au, v) * facew)[..., None]
    if look.get('blush', 0) > 0:
        col = mix(col, lin(look['blush_color']) * shade, blush(au, v, look.get('blush_size', 0), look.get('blush_y', 0)) * look['blush'] * 0.95 * facew)
    rb = info.get('brow', {})
    p = list(BROWS[look.get('hd_brow', 0)])
    # (as the client: the race's own line, the shape's differences from Natural over it)
    p[2] = max(rb.get('arch', 0.05) + (p[2] - 0.05), -0.03)
    p[4] = rb.get('slope', 0.0) + p[4]
    p[5] = rb.get('th', 0.052) * (p[5] / 0.04) / 1.3
    p[8] = p[8] * rb.get('len', 0.64) / 0.64
    bb = [rb.get('u0', 0.10), rb.get('v0', info['land']['browL'][1] - 0.03)]
    a_b, vb = brow(au, v, bb, p, look.get('brow_sl', [0] * 6), hair)
    if look.get('shadow', 0) > 0:
        col = mix(col, lin(look['shadow_color']) * shade, shadow(au, v, dist, corners, look['shadow'], look.get('shadow_size', 0), vb) * look.get('shadow_amt', 0.7))
    if look.get('liner', 0) > 0:
        lw = {1: (0.028, 0.0, 0.0), 2: (0.05, 0.018, 0.0), 3: (0.045, 0.03, 1.0)}[look['liner']]
        col = mix(col, lin(look.get('liner_color', (0.03, 0.025, 0.03))), liner(au, v, dist, corners, lw[0], lw[1] + 0.03 * look.get('liner_lower', 0), look.get('liner_wing', 0), lw[2]) * look.get('liner_amt', 0.9))
    if look.get('lip_color'):
        col = mix(col, lin(look['lip_color']) * shade, lips * look.get('lip_amt', 0.6))
    col = mix(col, lin(look.get('brow_color', (0.18, 0.12, 0.08))), a_b * look.get('brow_amt', 1.0))
    return np.power(np.clip(col, 0, 1), 1 / 2.2)
