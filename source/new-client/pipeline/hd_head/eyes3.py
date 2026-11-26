"""The HD eyes (the HD look, step 4 - owner 2026-11-25: iris patterns, iris and pupil size, each eye its own colour, the
eye-white's tint, a glow): the eyeball's textures, shared by every race.

  hd_eye.png        the eyeball: its white (MakeHuman's, the iris painted out - the client draws the iris); a: where
                    MakeHuman's iris was (kept for older clients)
  hd_eye_polar.png  each texel's place round its iris: r, g its direction (cos, sin: 0.5 + / 2), b its distance from
                    the iris's middle (iris radii / 2: the iris's rim at 0.5), a which eye (0 the left's iris, 1 the
                    right's)
  hd_iris.png       the iris patterns, one row each: x round the iris (0 .. 1), y out from the pupil's edge to the
                    rim (0 .. 1 within the row); grey 0.5 the iris's own colour, darker and lighter its fibres
"""
import numpy as np, cv2
from pathlib import Path

PATTERNS = ['Natural', 'Fibrous', 'Starburst', 'Ringed', 'Speckled', 'Smooth']
PW, PH = 512, 128


def irises(e):
    """-> [(cx, cy, r)] the two irises in the texture's pixels, [MakeHuman's iris mask]."""
    hsv = cv2.cvtColor(e, cv2.COLOR_BGR2HSV)
    iris = ((hsv[..., 1] > 0.45) | (hsv[..., 2] < 0.35)).astype(np.uint8)
    iris = cv2.morphologyEx(iris, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, stats, cen = cv2.connectedComponentsWithStats(iris)
    out = []
    keep = np.zeros_like(iris)
    for i in np.argsort(-stats[1:, cv2.CC_STAT_AREA])[:2] + 1:
        cx, cy = cen[i]
        r = np.sqrt(stats[i, cv2.CC_STAT_AREA] / np.pi)
        out.append((float(cx), float(cy), float(r)))
        cv2.circle(keep, (int(round(cx)), int(round(cy))), int(r * 1.02), 1, -1)
    return out, keep


def noise(rng, shape, sig):
    z = rng.standard_normal(shape).astype(np.float32)
    w = shape[1]
    z = cv2.GaussianBlur(np.hstack([z, z, z]), (0, 0), sig[1], sigmaY=sig[0], borderType=cv2.BORDER_REFLECT)[:, w:2 * w]   # (round the iris: seamless)
    return z / (z.std() + 1e-9)


def patterns(e, iris_list):
    """The rows of hd_iris.png (each PH x PW, grey about 0.5)."""
    rng = np.random.default_rng(3)
    rows = []
    a = np.linspace(0, 2 * np.pi, PW, endpoint=False)[None, :]
    q = np.linspace(0, 1, PH)[:, None]
    # Natural: MakeHuman's own iris unwrapped (pupil's edge at 0.28 of the radius to the rim)
    cx, cy, r = iris_list[0]
    rr = (0.28 + 0.66 * q) * r
    mx = (cx + np.cos(a) * rr).astype(np.float32); my = (cy + np.sin(a) * rr).astype(np.float32)
    g = cv2.remap(e, mx, my, cv2.INTER_LINEAR) @ np.array([0.11, 0.59, 0.30], np.float32)
    g = g / max(np.median(g), 1e-3) * 0.5
    rows.append(np.clip(g, 0, 1))
    # the rest drawn: fibres (fine radial streaks), a starburst (light round the pupil), a ring (dark rim, a collarette),
    # speckles, smooth
    fib = noise(rng, (PH, PW), (30, 1.2)) * 0.6 + noise(rng, (PH, PW), (8, 0.8)) * 0.4
    rows.append(np.clip(0.5 + 0.17 * fib - 0.12 * q ** 3, 0, 1))
    burst = np.clip(1 - q / 0.45, 0, 1) ** 1.5 * (0.7 + 0.3 * noise(rng, (PH, PW), (20, 2.0)))
    rows.append(np.clip(0.45 + 0.35 * burst + 0.1 * fib, 0, 1))
    coll = np.exp(-((q - 0.32) / 0.06) ** 2) * (0.6 + 0.4 * noise(rng, (PH, PW), (2, 6)))
    rows.append(np.clip(0.5 + 0.22 * coll + 0.08 * fib - 0.25 * np.clip((q - 0.78) / 0.22, 0, 1), 0, 1))
    sp = np.zeros((PH, PW), np.float32)
    for _ in range(160):
        x, y = rng.integers(0, PW), rng.uniform(0.1, 0.9) * PH
        cv2.circle(sp, (int(x), int(y)), int(rng.integers(2, 6)), float(rng.uniform(0.5, 1)), -1, cv2.LINE_AA)
    sp = cv2.GaussianBlur(sp, (0, 0), 1.0)
    rows.append(np.clip(0.5 + 0.08 * fib - 0.3 * sp, 0, 1))
    rows.append(np.clip(0.5 + 0.04 * fib - 0.06 * q, 0, 1))
    return np.vstack(rows)


def make(folder, sys_dir):
    folder = Path(folder)
    e8 = cv2.imread(str(Path(sys_dir) / 'eyes/materials/brown_eye.png'), cv2.IMREAD_UNCHANGED)[..., :3]
    e = e8.astype(np.float32) / 255
    ir, keep = irises(e)
    H, W = e.shape[:2]
    # the white: the iris painted out (from round it)
    hole = cv2.dilate(keep, np.ones((9, 9), np.uint8)) > 0
    white = e8.copy()
    yy0, xx0 = np.mgrid[0:e8.shape[0], 0:e8.shape[1]]
    for cx, cy, r in ir:                               # (the white round each iris, its colour, faintly mottled)
        d = np.hypot(xx0 - cx, yy0 - cy)
        ring = (d > 1.15 * r) & (d < 1.5 * r)
        med = np.median(e8[ring], 0)
        sel = hole & (d < 1.3 * r)
        white[sel] = np.clip(med + np.random.default_rng(1).normal(0, 2.0, (sel.sum(), 3)), 0, 255).astype(np.uint8)
    white = np.where(hole[..., None], cv2.GaussianBlur(white, (0, 0), 2.0), white)
    # the polar map: each texel against the nearer iris; which eye is which: the eyes' UVs (the left eye's iris is
    # the one up and right in the texture: head2's left eye's front at uv about (0.70, 0.30))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ds = [np.hypot(xx - cx, yy - cy) for cx, cy, r in ir]
    near = np.argmin(np.stack(ds), 0)
    left = int(np.argmin([abs(cx / W - 0.70) + abs(cy / H - 0.30) for cx, cy, r in ir]))
    pol = np.zeros((H, W, 4), np.float32)
    for k, (cx, cy, r) in enumerate(ir):
        sel = near == k
        dx, dy = (xx - cx) / r, (yy - cy) / r
        d = np.hypot(dx, dy)
        pol[..., 0] = np.where(sel, 0.5 + 0.5 * dx / np.maximum(d, 1e-6), pol[..., 0])
        pol[..., 1] = np.where(sel, 0.5 + 0.5 * dy / np.maximum(d, 1e-6), pol[..., 1])
        pol[..., 2] = np.where(sel, np.clip(d / 2, 0, 1), pol[..., 2])
        pol[..., 3] = np.where(sel, 0.0 if k == left else 1.0, pol[..., 3])
    S = 1024
    out = np.dstack([cv2.resize(white, (S, S), interpolation=cv2.INTER_AREA),
                     cv2.resize((cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 3) * 255).astype(np.uint8), (S, S), interpolation=cv2.INTER_AREA)])
    cv2.imwrite(str(folder / 'hd_eye.png'), out)
    pol8 = np.clip(cv2.resize(pol, (S, S), interpolation=cv2.INTER_NEAREST) * 255, 0, 255).astype(np.uint8)
    cv2.imwrite(str(folder / 'hd_eye_polar.png'), pol8[..., [2, 1, 0, 3]])     # (BGRA: r cos, g sin, b distance, a eye)
    pat = patterns(e, ir)
    cv2.imwrite(str(folder / 'hd_iris.png'), np.clip(pat * 255, 0, 255).astype(np.uint8))
    return ir


if __name__ == '__main__':
    import sys
    print(make(sys.argv[1], sys.argv[2]))
