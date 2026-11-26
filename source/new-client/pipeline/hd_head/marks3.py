"""The HD look's age and marks (step 5 - owner 2026-11-25: an age slider - lines, crow's feet, smile lines, a softer
jaw, grey hair - and freckles, moles, placed scars, weathering): drawn once in face space, shared by every race (the
client maps each race's own nose, mouth and chin onto these - Fig3Figure's shader, hd_canon).

  hd_age.png    the age lines, by when they come: r the first (from about a quarter: the smile lines, under the eyes,
                the crow's feet), g the middle (the forehead, the frown, the marionette lines), b the last (the lips'
                lines, more forehead); a the age's shade (under the eyes, the temples, beside the nose, the jowls).
                Face space u -1.6 .. 1.6 across, v 1.4 .. -2.2 down (canonical: nose -0.65, mouth -1.08, chin -1.68).
  hd_scars.png  the scars, each a 256 tile (3 x 2) of 0.8 eye spacings, its middle the scar's: r the scar, g its
                raised edge.
"""
import numpy as np, cv2

U0, U1, V0, V1 = -1.6, 1.6, -2.2, 1.4
FS = 0.003
VN, VM, VC = -0.65, -1.08, -1.68
SCARS = ['Slash', 'Gash', 'Claw', 'Lip', 'Brow', 'Burn']


def px(u, v):
    return int(round((u - U0) / FS)), int(round((V1 - v) / FS))


def canvas():
    return np.zeros((int((V1 - V0) / FS) + 1, int((U1 - U0) / FS) + 1), np.float32)


def taper(c, pts, w0, w1, val=1.0, both=True, n=24):
    pts = np.array(pts, float)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    t = np.linspace(0, seg[-1], n)
    q = np.c_[np.interp(t, seg, pts[:, 0]), np.interp(t, seg, pts[:, 1])]
    for sgn in ((1, -1) if both else (1,)):
        for i in range(n - 1):
            w = w0 + (w1 - w0) * i / (n - 1)
            cv2.line(c, px(sgn * q[i][0], q[i][1]), px(sgn * q[i + 1][0], q[i + 1][1]), val, max(1, int(round(w / FS))), cv2.LINE_AA)


def curve(a, b, bulge, n=16):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a; nrm = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-9)
    t = np.linspace(0, 1, n)[:, None]
    return a + d * t + nrm * bulge * np.sin(np.pi * t)


def blur(c, r):
    return cv2.GaussianBlur(c, (0, 0), r / FS)


def age():
    rng = np.random.default_rng(7)
    early, mid, late, shade = canvas(), canvas(), canvas(), canvas()
    # early: the smile lines (nose to mouth), under the eyes, the crow's feet
    taper(early, curve((0.29, VN - 0.02), (0.46, VM - 0.1), -0.07), 0.034, 0.014, 1.0)
    taper(early, curve((0.3, -0.16), (0.74, -0.12), -0.05), 0.014, 0.008, 0.7)
    for a in (-30, -8, 16):
        r = np.radians(a)
        taper(early, [(0.82, 0.0), (0.82 + 0.2 * np.cos(r), 0.0 + 0.2 * np.sin(r))], 0.012, 0.004, 0.8)
    # mid: the forehead, the frown, the marionette lines
    for i, v in enumerate([0.85, 1.0, 1.15]):
        pts = [(u, v + 0.02 * np.sin(u * 5 + i)) for u in np.linspace(0.0, 0.62 - 0.08 * i, 12)]
        taper(mid, pts, 0.016, 0.006, 0.8)
    taper(mid, [(0.06, 0.28), (0.08, 0.55)], 0.014, 0.008, 0.8)
    taper(mid, [(0.4, VM - 0.05), (0.44, VM - 0.36)], 0.016, 0.006, 0.7)
    # late: the lips' fine lines, the forehead's fourth, the cheeks' creases
    for u in np.linspace(0.05, 0.3, 6):
        taper(late, [(u + rng.normal(0, 0.01), VM + 0.06), (u + rng.normal(0, 0.01), VM + 0.16)], 0.006, 0.003, 0.6)
    taper(late, [(u, 1.28 + 0.02 * np.sin(u * 6)) for u in np.linspace(0.0, 0.4, 10)], 0.012, 0.005, 0.6)
    taper(late, curve((0.62, -0.5), (0.7, -0.85), 0.04), 0.014, 0.006, 0.6)
    # the shade: under the eyes, the temples, beside the nose's fold, the jowls
    for (cu, cv_, ru, rv, k) in ((0.5, -0.2, 0.2, 0.08, 1.0), (1.05, 0.35, 0.16, 0.3, 0.7), (0.38, VN - 0.2, 0.08, 0.2, 0.6),
                                 (0.72, VC + 0.15, 0.18, 0.16, 0.6)):
        cv2.ellipse(shade, px(cu, cv_), (int(ru / FS), int(rv / FS)), 0, 0, 360, k, -1)
        cv2.ellipse(shade, px(-cu, cv_), (int(ru / FS), int(rv / FS)), 0, 0, 360, k, -1)
    out = np.dstack([blur(shade, 0.06), blur(late, 0.008), blur(mid, 0.011), blur(early, 0.012) * 1.3])   # BGRA: b late ...
    out = np.dstack([out[..., 1], out[..., 2], out[..., 3], out[..., 0]])                        # -> b late, g mid, r early, a shade
    return np.clip(out, 0, 1)


def scars():
    rng = np.random.default_rng(9)
    T = 256
    span = 0.8
    out = np.zeros((2 * T, 3 * T, 2), np.float32)
    def tp(u, v):
        return (u / span + 0.5) * T, (0.5 - v / span) * T
    for k, nm in enumerate(SCARS):
        c = np.zeros((T, T), np.float32); ridge = np.zeros((T, T), np.float32)
        if nm in ('Slash', 'Gash', 'Lip', 'Brow'):
            L = {'Slash': 0.6, 'Gash': 0.5, 'Lip': 0.28, 'Brow': 0.3}[nm]
            wmax = {'Slash': 0.02, 'Gash': 0.04, 'Lip': 0.018, 'Brow': 0.022}[nm]
            t = np.linspace(-0.5, 0.5, 40)
            pts = np.c_[t * L * 0.3, t * L] + rng.normal(0, 0.004, (40, 2))
            w = wmax * (0.4 + 0.6 * np.sin(np.linspace(0, np.pi, 40)))
            for i in range(39):
                a, b = tp(*pts[i]), tp(*pts[i + 1])
                cv2.line(c, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1.0, max(1, int(w[i] / span * T)), cv2.LINE_AA)
                cv2.line(ridge, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1.0, max(1, int(w[i] / span * T * 1.8)), cv2.LINE_AA)
            if nm == 'Gash':
                for i in range(4, 36, 6):
                    d = pts[i + 1] - pts[i - 1]; n_ = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-9) * 0.04
                    a, b = tp(*(pts[i] - n_)), tp(*(pts[i] + n_))
                    cv2.line(c, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 0.7, 2, cv2.LINE_AA)
        elif nm == 'Claw':
            for o in (-0.07, 0.0, 0.07):
                t = np.linspace(-0.5, 0.5, 30)
                pts = np.c_[o + t * 0.12, t * 0.5]
                for i in range(29):
                    a, b = tp(*pts[i]), tp(*pts[i + 1])
                    wd = max(1, int(0.016 * np.sin(np.pi * i / 29) / span * T) + 1)
                    cv2.line(c, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1.0, wd, cv2.LINE_AA)
                    cv2.line(ridge, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1.0, wd * 2, cv2.LINE_AA)
        else:   # Burn: a mottled patch
            yy, xx = np.mgrid[0:T, 0:T] / T - 0.5
            n_ = cv2.GaussianBlur(rng.standard_normal((T, T)).astype(np.float32), (0, 0), 6)
            n_ /= n_.std()
            c = np.clip((0.32 - np.hypot(xx * 1.2, yy) + 0.06 * n_) / 0.05, 0, 1)
            ridge = np.clip((0.36 - np.hypot(xx * 1.2, yy) + 0.06 * n_) / 0.05, 0, 1) - c * 0.5
        c = cv2.GaussianBlur(c, (0, 0), 1.0)
        ridge = cv2.GaussianBlur(ridge, (0, 0), 2.0)
        oy, ox = (k // 3) * T, (k % 3) * T
        c[0, :] = c[-1, :] = c[:, 0] = c[:, -1] = 0
        out[oy:oy + T, ox:ox + T, 0] = c
        out[oy:oy + T, ox:ox + T, 1] = np.clip(ridge - c * 0.6, 0, 1)
    return out


def make(folder):
    from pathlib import Path
    folder = Path(folder)
    a = age()
    cv2.imwrite(str(folder / 'hd_age.png'), np.clip(a * 255, 0, 255).astype(np.uint8))
    s = scars()
    cv2.imwrite(str(folder / 'hd_scars.png'), np.clip(np.dstack([np.zeros_like(s[..., 0]), s[..., 1], s[..., 0]]) * 255, 0, 255).astype(np.uint8))


if __name__ == '__main__':
    import sys
    make(sys.argv[1])
