"""The character creator's skin layers (owner 2026-11-06, the roadmap's third step): masks painted onto each race's
head texture layout - brows, freckles, age lines, scars, stubble, lip colour and war paint - that the figure's head
shader colours and blends over whichever face texture is worn (Fig3Figure, look 'brows', 'freckles', ...).

How: the head mesh's own landmarks (pipeline/face_morphs.py: the eyes, nose tip, mouth and chin, found from the
Catacombs morphs) give a face space in eye spacings - u across (the eyes at -0.5 / +0.5), v up (the eyes at 0), f
forward. Every layer is drawn once in that face space (cv2 lines, dots, fills), then each texel of the head texture
looks up its own face-space point (the mesh rasterised into its UVs) - so one drawing fits every race's face, their
own proportions. Only the face and scalp pieces of the texture take layers (the eyeballs, teeth and ears are pieces
of their own). The sides of the head share texels left and right (the client's textures mirror them): what is drawn
there is drawn on both sides.

    python skin_layers.py <race folder> [more ...]      writes skin_layers_<n>.png beside figure.gltf and the
                                                        'skin_layers' entry of figure.json
    python skin_layers.py <race folder> --preview=<png> also the face texture with every layer on, for a look
"""
import json, sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import face_morphs as fmx

SIZE = 1024                                    # the masks' size (the x4plus face textures are 1024)
FS = 0.005                                     # face space: one drawing pixel, in eye spacings
U0, U1, V0, V1 = -2.6, 2.6, -4.2, 3.0          # the drawing's extent (u across, v up)

ONE_SIDED = {('scar', 0), ('scar', 1), ('scar', 2), ('scar', 3)}   # drawn on one side of the face only

# the layers: look key, label, kind, the options (each one mask) - the client lists them in this order
LAYERS = [
    ('brows', 'Brows', 'hair', ['Fuller', 'Thick', 'Heavy']),
    ('freckles', 'Freckles', 'freckle', ['Light', 'Many']),
    ('age', 'Age Lines', 'age', ['Lines']),
    ('scar', 'Scar', 'scar', ['Cheek', 'Eye', 'Lip', 'Brow']),
    ('stubble', 'Stubble', 'hair', ['Stubble']),
    ('lips', 'Lip Colour', 'lip', ['Lips']),
    ('paint', 'War Paint', 'paint', ['Mask', 'Claws', 'Half', 'Chin', 'Sweep', 'Spirals']),
]


def px(u, v):
    return int(round((u - U0) / FS)), int(round((V1 - v) / FS))


def canvas():
    return np.zeros((int((V1 - V0) / FS) + 1, int((U1 - U0) / FS) + 1), np.float32)


def line(c, pts, w, val=1.0, both=False):
    """A polyline through face-space points, w eye spacings wide; both: mirrored on the other side as well."""
    for sgn in ((1, -1) if both else (1,)):
        p = np.array([px(sgn * u, v) for u, v in pts], np.int32)
        cv2.polylines(c, [p], False, val, max(1, int(round(w / FS))), cv2.LINE_AA)


def taper(c, pts, w0, w1, val=1.0, both=False, n=24):
    """A stroke whose width runs from w0 to w1 along the points (a brush, a brow)."""
    pts = np.array(pts, float)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    t = np.linspace(0, seg[-1], n)
    q = np.c_[np.interp(t, seg, pts[:, 0]), np.interp(t, seg, pts[:, 1])]
    for sgn in ((1, -1) if both else (1,)):
        for i in range(n - 1):
            w = w0 + (w1 - w0) * i / (n - 2)
            a, b = px(sgn * q[i, 0], q[i, 1]), px(sgn * q[i + 1, 0], q[i + 1, 1])
            cv2.line(c, a, b, val, max(1, int(round(w / FS))), cv2.LINE_AA)


def curve(a, b, bulge, n=16):
    """Points from a to b bowed sideways by bulge (eye spacings, + to the left of a->b)."""
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    nrm = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-9)
    t = np.linspace(0, 1, n)[:, None]
    return a + d * t + nrm * (bulge * 4 * t * (1 - t))


def blur(c, r):
    k = max(1, int(round(r / FS))) | 1
    return cv2.GaussianBlur(c, (k, k), 0)


def noise(shape, scale, seed):
    """Smooth value noise, features about 'scale' eye spacings."""
    rng = np.random.default_rng(seed)
    h, w = shape
    s = max(2, int(scale / FS))
    small = rng.random((h // s + 2, w // s + 2)).astype(np.float32)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)[:h, :w]


def ragged(c, seed, amount=0.35, scale=0.05):
    """A painted edge: the stroke's soft border eaten by noise."""
    n = noise(c.shape, scale, seed)
    return np.clip((blur(c, 0.02) - amount * n) / (1 - amount), 0, 1)


def draw(L, rng):
    """Every mask in face space. L: the landmarks in face space (v_n nose tip, v_m mouth, v_c chin)."""
    vn, vm, vc = L['v_n'], L['v_m'], L['v_c']
    M = {}
    # --- brows: an arch over each eye, hair strokes along it (over the face texture's own painted brows)
    brow = L['brow']
    for k, (w, strokes) in enumerate([(0.07, 500), (0.10, 800), (0.14, 1100)]):
        c = canvas()
        taper(c, brow, w * 1.15, w * 0.45, 0.55, both=True)
        pts = np.array(brow)
        for _ in range(strokes):                       # the hairs: short strokes leaning out and up
            t = rng.random()
            seg = t * (len(pts) - 1)
            i = min(int(seg), len(pts) - 2)
            p = pts[i] + (pts[i + 1] - pts[i]) * (seg - i)
            wid = w * (1.15 - 0.7 * t)
            q = p + [0, (rng.random() - 0.5) * wid]
            ang = np.radians(15 + 25 * rng.random()) * (1 if t > 0.15 else 3)
            L2 = 0.05 + 0.04 * rng.random()
            e = q + [np.cos(ang) * L2, np.sin(ang) * L2]
            for sgn in (1, -1):
                cv2.line(c, px(sgn * q[0], q[1]), px(sgn * e[0], e[1]), 0.6 + 0.4 * rng.random(), 1, cv2.LINE_AA)
        M['brows', k] = np.clip(blur(c, 0.012), 0, 1)
    # --- freckles: dots over the nose and cheeks; many: the whole face
    for k, (n, region) in enumerate([(900, 'cheeks'), (2600, 'face')]):
        c = canvas()
        for _ in range(n * 4):
            u, v = rng.uniform(-1.3, 1.3), rng.uniform(vc - 0.2, 1.4)
            if region == 'cheeks':
                d = np.exp(-((abs(u) - 0.5) ** 2 / 0.09 + (v + 0.4) ** 2 / 0.08)) \
                    + np.exp(-(u ** 2 / 0.03 + (v + 0.25) ** 2 / 0.06))
            else:
                d = 0.35 + 0.65 * np.exp(-((abs(u) - 0.35) ** 2 / 0.4 + (v + 0.3) ** 2 / 0.5))
            if rng.random() > d * 0.25:
                continue
            r = rng.uniform(0.008, 0.022)
            cv2.circle(c, px(u, v), max(1, int(r / FS)), float(rng.uniform(0.35, 1.0)), -1, cv2.LINE_AA)
        M['freckles', k] = np.clip(blur(c, 0.008), 0, 1)
    # --- age lines: forehead, frown, crow's feet, under the eyes, nose-to-mouth folds, mouth corners
    c = canvas()
    for i, v in enumerate([0.88, 1.03, 1.18]):
        pts = [(u, v + 0.025 * np.sin(u * 5 + i)) for u in np.linspace(-0.62 + 0.08 * i, 0.62 - 0.08 * i, 20)]
        taper(c, pts[:10], 0.006, 0.018, 0.8)
        taper(c, pts[9:], 0.018, 0.006, 0.8)
    for sgn in (1, -1):
        line(c, [(sgn * 0.07, 0.30), (sgn * 0.09, 0.55)], 0.016, 0.8)
        for a in (-28, -6, 18):
            r = np.radians(a)
            taper(c, [(sgn * 0.84, 0.02), (sgn * (0.84 + 0.25 * np.cos(r)), 0.02 + 0.25 * np.sin(r))], 0.016, 0.004, 0.7)
        taper(c, [(sgn * u, v) for u, v in curve((0.28, -0.17), (0.78, -0.12), -0.06)], 0.01, 0.01, 0.6)
        taper(c, [(sgn * u, v) for u, v in curve((0.26, vn + 0.04), (0.44, vm - 0.08), -0.1)], 0.024, 0.01, 0.9)
        taper(c, [(sgn * 0.37, vm - 0.06), (sgn * 0.40, vm - 0.34)], 0.018, 0.006, 0.6)
    M['age', 0] = np.clip(blur(c, 0.012), 0, 1)
    # --- scars: jagged lines with stitch marks (each on one side of the face)
    scars = [[(-0.95, -0.15), (-0.62, -0.42), (-0.33, -0.78)],
             [(0.47, 0.72), (0.52, 0.28), (0.55, -0.05), (0.6, -0.48)],
             [(-0.14, vm + 0.26), (-0.12, vm), (-0.08, vm - 0.36)],
             [(0.28, 0.95), (0.42, 0.62), (0.58, 0.28)]]
    for k, pts in enumerate(scars):
        c = canvas()
        pts = np.array(pts, float)
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        t = np.linspace(0, seg[-1], 40)
        q = np.c_[np.interp(t, seg, pts[:, 0]), np.interp(t, seg, pts[:, 1])]
        q += rng.normal(0, 0.006, q.shape)
        w = 0.022 + 0.022 * np.sin(np.linspace(0, np.pi, len(q)))
        for i in range(len(q) - 1):
            cv2.line(c, px(*q[i]), px(*q[i + 1]), 1.0, max(1, int(w[i] / FS)), cv2.LINE_AA)
        for i in range(3, len(q) - 3, 6):              # stitch marks across it
            d = q[i + 1] - q[i - 1]
            n_ = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-9) * 0.045
            cv2.line(c, px(*(q[i] - n_)), px(*(q[i] + n_)), 0.7, max(1, int(0.008 / FS)), cv2.LINE_AA)
        M['scar', k] = np.clip(blur(c, 0.01), 0, 1)
    # --- stubble: the beard's area, speckled; never the lips
    c = canvas()
    top = min(vn - 0.08, vm + 0.3)                     # (under the nose - or just over the lip, where the nose sits high)
    poly = [(0, top), (0.30, top + 0.04), (0.47, vm + 0.02), (0.75, vm + 0.18), (1.12, -0.18), (1.28, 0.22),
            (1.42, 0.22), (1.45, -0.4), (1.3, vc - 0.3), (0.6, vc - 0.55), (0, vc - 0.6)]
    for sgn in (1, -1):
        cv2.fillPoly(c, [np.array([px(sgn * u, v) for u, v in poly], np.int32)], 1.0, cv2.LINE_AA)
    # (owner 2026-11-06: it ended in a hard line on the neck) - thinning out from the jaw down instead
    rows = V1 - FS * np.arange(c.shape[0], dtype=np.float32)
    ramp = np.clip((rows - (vc - 0.6)) / 0.5, 0, 1)[:, None]
    M['stubble', 0] = blur(c, 0.08) * ramp ** 1.5      # (the area: the hairs are speckled in the texture's own space)
    # --- war paint (the lips' own mask comes from the texture, below)
    paints = []
    c = canvas()                                       # mask: a band across the eyes, tapering to the temples
    band = [(-1.28, 0.05), (-1.0, 0.22), (-0.5, 0.3), (0, 0.22), (0.5, 0.3), (1.0, 0.22), (1.28, 0.05),
            (1.0, -0.22), (0.5, -0.26), (0.12, -0.18), (0, -0.28), (-0.12, -0.18), (-0.5, -0.26), (-1.0, -0.22)]
    cv2.fillPoly(c, [np.array([px(u, v) for u, v in band], np.int32)], 1.0, cv2.LINE_AA)
    paints.append(c)
    c = canvas()                                       # claws: three strokes down each cheek
    for i in range(3):
        a = (0.42 + 0.14 * i, -0.22 - 0.03 * i)
        b = (0.62 + 0.16 * i, -0.85 - 0.04 * i)
        taper(c, [a, b], 0.075, 0.02, 1.0, both=True)
    paints.append(c)
    c = canvas()                                       # band: across the brow, tapering to the temples
    band = [(-1.25, 0.45), (-0.8, 0.68), (0, 0.74), (0.8, 0.68), (1.25, 0.45), (0.8, 0.42), (0, 0.44), (-0.8, 0.42)]
    cv2.fillPoly(c, [np.array([px(u, v) for u, v in band], np.int32)], 1.0, cv2.LINE_AA)
    paints.append(c)
    c = canvas()                                       # chin: three stripes from the lower lip down
    for u in (-0.16, 0.0, 0.16):
        taper(c, [(u, vm - 0.1), (u * 1.2, vc - 0.18)], 0.06, 0.035, 1.0)
    paints.append(c)
    c = canvas()                                       # sweep: from the brows up to the temples, a dot on the cheek
    taper(c, curve((0.18, 0.36), (1.25, 0.95), 0.12), 0.08, 0.02, 1.0, both=True)
    for sgn in (1, -1):
        cv2.circle(c, px(sgn * 0.62, -0.42), int(0.055 / FS), 1.0, -1, cv2.LINE_AA)
    paints.append(c)
    c = canvas()                                       # spirals: a woad spiral on each cheek, one on the brow
    for cu, cv_, R, both in ((0.66, -0.5, 0.24, True), (0.0, 0.75, 0.2, False)):
        th = np.linspace(0, 3.2 * np.pi, 90)
        r = R * th / th[-1]
        pts = list(zip(cu + r * np.cos(th), cv_ + r * np.sin(th)))
        line(c, pts, 0.035, 1.0, both=both)
    paints.append(c)
    for k, c in enumerate(paints):
        M['paint', k] = ragged(c, 100 + k)
    return M


def raster(UV, T, attrs, keep, size):
    """The mesh drawn into its UVs: per texel each attribute (n, k) interpolated, and which texels are covered."""
    out = np.zeros((size, size, attrs.shape[1]), np.float32)
    cov = np.zeros((size, size), bool)
    for t in T:
        if not keep[t].all():
            continue
        uv = UV[t] * size
        x0, y0 = np.floor(uv.min(0)).astype(int)
        x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1 + 1, size), min(y1 + 1, size)
        if x1 <= x0 or y1 <= y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        p = np.stack([xs.ravel() + .5, ys.ravel() + .5], 1)
        a, b, c = uv
        v0, v1, v2 = b - a, c - a, p - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        w1 = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        w2 = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        w0 = 1 - w1 - w2
        m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not m.any():
            continue
        val = w0[m, None] * attrs[t[0]] + w1[m, None] * attrs[t[1]] + w2[m, None] * attrs[t[2]]
        out[p[m, 1].astype(int), p[m, 0].astype(int)] = val
        cov[p[m, 1].astype(int), p[m, 0].astype(int)] = True
    return out, cov


def islands(T, n):
    """The UV pieces: connected triangles (texture seams split the vertices, so shared indices = one piece)."""
    parent = np.arange(n)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for t in T:
        r = [find(i) for i in t]
        for x in r[1:]:
            parent[x] = r[0]
    return np.array([find(i) for i in range(n)])


def hair_rgb(meta, tex_dir):
    """Each hair colour's average colour (the brows' and stubble's), from the first style that has colours."""
    for st in meta.get('hair_styles', []):
        cols = st.get('colours', [])
        if not cols:
            continue
        out = []
        for c in cols:
            img = cv2.imread(str(tex_dir / (c['tex'].lower() + '.png')), cv2.IMREAD_UNCHANGED)
            if img is None:
                out.append([0.25, 0.18, 0.12])
                continue
            a = img[..., 3] > 128 if img.shape[2] == 4 else np.ones(img.shape[:2], bool)
            rgb = img[..., :3][a].astype(np.float64).mean(0)[::-1] / 255.0
            out.append([round(float(x), 3) for x in rgb * np.array(c.get('tint', [1, 1, 1]))])
        return out
    return []


def split_faces(Fs, B4, tex, cov, front, wide, lipw, L, female=False):
    """The race's faces taken apart (owner 2026-11-06: "the textures on the face are tied to the face ... I'd like to
    choose ..."): a base face with no brows (the faces' median, the brows lifted out - lightened toward the skin
    around them, nothing else touched), and from each face what it paints over that base - its brows, its beard or
    stubble, its age lines - as masks the creator offers on their own. face_map: what each original face was."""
    lum = lambda x: x[..., :3].mean(-1)
    tu, tv = tex[..., 0], tex[..., 1]
    B = B4[..., :3]
    brow = np.array(L['brow'])
    kq = np.polyfit(brow[:, 0], brow[:, 1], 2)
    bv = np.polyval(kq, np.clip(np.abs(tu), 0.1, 1.0))
    lowv = np.maximum(bv - 0.13, 0.13)                       # (above the eyelids: those are dark too, and stay)
    band = cov & (np.abs(tu) < 1.15) & (tv > lowv) & (tv < bv + 0.2) & (front > 0.5)
    fade = (np.clip((tv - lowv) / 0.05, 0, 1) * np.clip((bv + 0.2 - tv) / 0.05, 0, 1)
            * np.clip((1.15 - np.abs(tu)) / 0.1, 0, 1) * band)
    band8 = cv2.dilate(band.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    # the skin the brows sit on: the face around the band, spread over it
    outside = (cov & ~band8).astype(np.float32)
    num = cv2.GaussianBlur(B * outside[..., None], (0, 0), 18)
    den = cv2.GaussianBlur(outside, (0, 0), 18)[..., None]
    est = num / np.maximum(den, 1e-4)
    dk = np.clip((lum(est) - lum(B)) / (0.25 * lum(est) + 1e-3), 0, 1) * fade
    dk = cv2.GaussianBlur(dk, (0, 0), 1.5)[..., None]
    base = B4.copy()
    base[..., :3] = B * (1 - dk) + est * dk
    # each face's brows: where it is darker than the bare base, in the band
    brows = [np.clip((lum(base) - lum(F)) / (0.35 * lum(base) + 1e-3), 0, 1) * fade for F in Fs]
    # beards / stubble the faces paint: darker than the median under the nose, clearly so over the area
    lipcut = 1 - np.clip(lipw * 1.6, 0, 1)
    breg = cov & (wide > 0.3) & (tv < L['v_n'] - 0.02) & (tv > L['v_c'] - 0.6)
    beards, beard_of = [], []
    cheeks = cov & (front > 0.6) & (tv > L['v_n'] + 0.05) & (tv < -0.15)
    for i, F in enumerate(Fs):
        if female:                                 # (no beards: a darker lower face there is a face's shading)
            break
        diff = (lum(B) - lum(F)) / (0.3 * lum(B) + 1e-3)
        off = float(np.median(diff[cheeks])) if cheeks.any() else 0.0   # (a face darker all over is not a beard)
        a = np.clip(diff - max(off, 0.0), 0, 1) * breg * lipcut
        if breg.any() and float(a[breg].mean()) > 0.1:
            beard_of.append(i)
            beards.append(cv2.GaussianBlur(a, (3, 3), 0))
    # age lines: the fine dark detail a face has over the face, well beyond the others'
    eyes_open = (np.abs(tv) < 0.12) & (np.abs(tu) < 0.95)
    areg = cov & (front > 0.5) & ~band8 & ~eyes_open & (lipw < 0.3) & (tv > L['v_m'] - 0.4)
    hf = [lum(F) - cv2.GaussianBlur(lum(F), (0, 0), 6) for F in Fs]
    upper = areg & (tv > L['v_n'] - 0.1)
    hB = lum(B) - cv2.GaussianBlur(lum(B), (0, 0), 6)
    en = np.array([float(np.clip(hB - h, 0, None)[upper].mean()) if upper.any() else 0 for h in hf])   # (darker lines)
    print('  line detail by face', np.round(en * 1000, 1))
    ages, age_of = [], []
    for i in np.argsort(-en):
        if en[i] > 1.2 * np.median(en) and i not in beard_of and len(ages) < 2:
            age_of.append(int(i))
            ages.append(np.clip(-hf[i] / 0.05, 0, 1) * areg)
    face_map = []
    for i in range(len(Fs)):
        face_map.append({'brows': i + 1, 'age_style': age_of.index(i) if i in age_of else -1,
                         'stubble_style': (beard_of.index(i) + 1) if i in beard_of else -1})
    print('  faces split: %d brows, beards from %s, age from %s' % (len(brows), [b + 1 for b in beard_of], [a + 1 for a in age_of]))
    return {'base': base, 'brows': brows, 'beards': beards, 'ages': ages, 'face_map': face_map}


def bake(folder, preview=None):
    folder = Path(folder)
    gltf, meta_path = folder / 'figure.gltf', folder / 'figure.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    tex_dir = folder.parent.parent / 'fig3_textures' / 'x4plus'
    if not (tex_dir / (meta['faces'][0]['tex'].lower() + '.png')).exists():
        tex_dir = tex_dir.parent / 'original'
    g = fmx.G(str(gltf))
    node = next(n for n in g.g['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    prim = g.g['meshes'][node['mesh']]['primitives'][0]
    P = g.acc(prim['attributes']['POSITION']).astype(np.float64)
    N = g.acc(prim['attributes']['NORMAL']).astype(np.float64)
    UV = g.acc(prim['attributes']['TEXCOORD_0']).astype(np.float64)
    T = g.acc(prim['indices']).astype(np.int64).reshape(-1, 3)
    fm = [g.acc(t['POSITION']).astype(np.float64) for t in prim['targets'][:8]]
    _, marks = fmx.build(P, N, T, fm)
    eL, eR = marks['eyeL'], marks['eyeR']
    em = (eL + eR) / 2
    E = abs(eR[0] - eL[0])
    L = {'v_n': (marks['nose_tip'][2] - em[2]) / E, 'v_m': (marks['mouth'][2] - em[2]) / E,
         'v_c': (marks['chin'][2] - em[2]) / E}
    # the pieces that take layers: the big ones (the face, the scalp) - not the eyeballs, teeth, ears
    isl = islands(T, len(P))
    area = {}
    for t in T:
        a, b, c = UV[t]
        area[isl[t[0]]] = area.get(isl[t[0]], 0) + abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2
    total = sum(area.values())
    keep = np.array([area.get(isl[i], 0) > 0.08 * total for i in range(len(P))])
    fu, fv, ff = (P[:, 0] - em[0]) / E, (P[:, 2] - em[2]) / E, (em[1] - P[:, 1]) / E
    # the mirrored pieces (both sides of the head in the same texels): a one-sided layer (half the face painted, a scar)
    # stays off them, or it shows on both sides
    Pm = P * [-1, 1, 1]
    mir = np.zeros(len(P))
    for s0 in range(0, len(P), 256):
        d = np.linalg.norm(P[None, :, :] - Pm[s0:s0 + 256, None, :], axis=2)
        j = d.argmin(1)
        ok = (d.min(1) < 0.02 * E) & (np.abs(P[s0:s0 + 256, 0] - em[0]) > 0.2 * E)
        mir[s0:s0 + 256] = np.where(ok, (np.abs(UV[s0:s0 + 256] - UV[j]).sum(1) < 0.01).astype(float), np.nan)
    one_sided = np.ones(len(P))
    for i in np.unique(isl):
        sel = isl == i
        f_ = np.nanmean(mir[sel]) if np.isfinite(mir[sel]).any() else 0.0
        if f_ > 0.5:
            one_sided[sel] = 0.0
    attrs = np.c_[fu, fv, ff, marks['_w']['lips'], one_sided]
    tex, cov = raster(UV, T, attrs, keep, SIZE)
    # every face texture of the race, and their median: the face they share (what one face alone paints - a beard,
    # wrinkles, a scar - falls out of it; the brows, which all paint, are taken out below)
    Fs = []
    for fc in meta['faces']:
        im = cv2.imread(str(tex_dir / (fc['tex'].lower() + '.png')), cv2.IMREAD_UNCHANGED)
        if im is None:
            raise SystemExit('no face texture %s' % (tex_dir / (fc['tex'].lower() + '.png')))
        if im.ndim == 2:
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        if im.shape[2] == 3:
            im = np.dstack([im, np.full(im.shape[:2], 255, im.dtype)])
        Fs.append(cv2.resize(im, (SIZE, SIZE), interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
    Fs = np.stack(Fs)                                       # (faces, SIZE, SIZE, BGRA)
    B4 = np.median(Fs, axis=0)
    img = B4[..., :3].copy()
    # the painted eyes and brows (the morphs' eye region sits a little high, and every race paints its brows at its
    # own height): the face texture seen in face space - the eye opening the darkest row across the eyes, the brow
    # the darkest point above it, column by column
    lum = img.mean(2)
    sel = cov & (tex[..., 2] > -0.6)
    gu = np.clip(((np.abs(tex[..., 0][sel])) / 0.05).astype(int), 0, 39)
    gv = np.clip(((tex[..., 1][sel] + 1.0) / 0.025).astype(int), 0, 119)
    acc = np.zeros((40, 120)); cnt = np.zeros((40, 120))
    np.add.at(acc, (gu, gv), lum[sel]); np.add.at(cnt, (gu, gv), 1)
    prof = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    rows = np.nanmean(prof[7:13], axis=0)                      # |u| 0.35 .. 0.65, by v
    vv = -1.0 + 0.025 * (np.arange(120) + 0.5)
    band = (vv > -0.35) & (vv < 0.35) & np.isfinite(rows)
    eye_v = float(vv[band][np.nanargmin(rows[band])]) if band.any() else 0.0
    brow = []
    for iu in range(2, 21):
        col = prof[iu]
        b = (vv > eye_v + 0.1) & (vv < eye_v + 0.75) & np.isfinite(col)
        if b.sum() < 5:
            continue
        j = np.nanargmin(np.where(b, col, np.nan))
        contrast = np.nanmedian(col[b]) - col[j]
        if contrast > 0.04:
            brow.append(((iu + 0.5) * 0.05, vv[j] - eye_v))
    if len(brow) >= 6:
        bu = np.array([b[0] for b in brow]); bvv = np.array([b[1] for b in brow])
        k = np.polyfit(bu, bvv, 2)
        us = np.linspace(max(0.1, bu.min()), min(1.05, bu.max()), 6)
        brow = [(float(u), float(np.polyval(k, u))) for u in us]
        how = 'painted'
    else:
        brow = [(0.12, 0.22), (0.35, 0.3), (0.62, 0.34), (0.85, 0.3), (1.02, 0.22)]
        how = 'drawn'
    tex[..., 1] -= eye_v                                    # v = 0 at the eyes' opening
    for k_ in ('v_n', 'v_m', 'v_c'):
        L[k_] -= eye_v
    L['brow'] = brow
    print('  eyes at %+.2f, brows %s %s' % (eye_v, how, ' '.join('%.2f,%.2f' % b for b in brow)))
    f = tex[..., 2]
    front = np.clip((f + 1.15) / 0.45, 0, 1) * cov           # the face and its sides, not the back of the head
    wide = np.clip((f + 1.9) / 0.5, 0, 1) * cov               # (the stubble's sideburns reach further back)
    lipw = tex[..., 3]
    single = np.clip(tex[..., 4], 0, 1)
    # the lips: the texture's own - the widest patch redder than the skin, below the nose (the mesh's mouth region
    # alone put a dwarf's lip colour on his red nose); its middle is the mouth for the drawing too
    b_, g_, r_ = img[..., 0], img[..., 1], img[..., 2]
    red = r_ - (g_ + b_) / 2
    near = lipw > 0.25
    tu, tv = tex[..., 0], tex[..., 1]
    mesh_ok = L['v_n'] - 0.9 < L['v_m'] < L['v_n'] - 0.25     # (where the mesh's mouth is believable, near it)
    zone = cov & (single > 0.5) & (front > 0.5) & (np.abs(tu) < 0.6) & (tv < L['v_n'] - 0.2) & (tv > L['v_n'] - 1.05)
    # redder and darker than the skin, texel by texel: the painted lips' own outline
    lipness = red - 0.35 * img.mean(2)
    best, how = None, 'mesh'
    if zone.sum() > 200:
        zl = lipness[zone]
        for k_sd in (1.2, 0.8, 0.5):
            thr = zl.mean() + k_sd * zl.std()
            binm = ((lipness > thr) & zone).astype(np.uint8)
            binm = cv2.morphologyEx(binm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            n_, lab, st, _ = cv2.connectedComponentsWithStats(binm, 8)
            for i in range(1, n_):
                sel_ = lab == i
                if sel_.sum() < 60:
                    continue
                us, vs = tu[sel_], tv[sel_]
                w, h = us.max() - us.min(), vs.max() - vs.min()
                v_mid = float(np.median(vs))
                if w < 0.3 or w < 1.2 * h or abs(float(np.median(us))) > 0.15:
                    continue
                if mesh_ok and abs(v_mid - L['v_m']) > 0.3:
                    continue
                score = w * float(lipness[sel_].mean() - zl.mean())
                if best is None or score > best[0]:
                    best = (score, sel_, v_mid, lab, n_)
            if best:
                break
    if best:                                           # the other lip: what passes the same test just above / below
        sel_ = best[1].copy()
        lab, n_ = best[3], best[4]
        for i in range(1, n_):
            o = lab == i
            if o.sum() >= 30 and abs(float(np.median(tv[o])) - best[2]) < 0.2 and np.abs(tu[o]).max() < 0.5:
                sel_ |= o
        sel_ &= (tv > best[2] - 0.10) & (tv < best[2] + 0.16)   # (not the shadow under the lower lip)
        best = (best[0], sel_, best[2])
    if best:
        # (soft: how lip-like each texel is, near the found lips - owner 2026-11-06: a hard stamped shape looked like a
        # first try at lipstick)
        m_ = cv2.dilate(best[1].astype(np.uint8), np.ones((7, 7), np.uint8)).astype(np.float32)
        near_l = cv2.GaussianBlur(m_, (9, 9), 0)
        lo_, sd_ = float(zl.mean()), float(zl.std()) + 1e-4
        lip_raw = np.clip((lipness - lo_ - 0.2 * sd_) / (1.4 * sd_), 0, 1) * near_l * cov
        if abs(best[2] - L['v_m']) > 0.08:                   # the mesh's mouth was off: the chin moves with it
            L['v_m'] = best[2]
            L['v_c'] = min(L['v_c'], best[2] - 0.45)
        how = 'painted'
    else:
        skin_red = float(np.median(red[cov & (front > 0.9) & ~near])) if (cov & ~near).any() else 0.1
        lip_raw = np.clip((red - skin_red - 0.008) / 0.035, 0, 1) * np.clip((lipw - 0.15) / 0.25, 0, 1)
    lip_mask = cv2.GaussianBlur(lip_raw, (5, 5), 0)
    print('  lips %s, mouth %.2f' % (how, L['v_m']))
    split = split_faces(Fs, B4, tex, cov, front, wide, lipw, L, folder.name.endswith('_f'))
    cv2.imwrite(str(folder / 'face_base.png'), (np.clip(split['base'], 0, 1) * 255 + 0.5).astype(np.uint8))
    import os
    if os.environ.get('SKIN_DUMP'):
        np.savez_compressed(os.environ['SKIN_DUMP'], tex=tex, cov=cov, front=front, single=single, lip=lip_mask,
                            L=json.dumps({k: v for k, v in L.items()}))
    # the face-space drawing, looked up by every texel
    rng = np.random.default_rng(7)
    M = draw(L, rng)
    mapx = ((tex[..., 0] - U0) / FS).astype(np.float32)
    mapy = ((V1 - tex[..., 1]) / FS).astype(np.float32)
    srng = np.random.default_rng(11)
    speck = cv2.GaussianBlur((srng.random((SIZE, SIZE)) < 0.4).astype(np.float32) * srng.uniform(0.6, 1.0, (SIZE, SIZE)).astype(np.float32), (3, 3), 0) * 1.5
    speck = np.clip(speck, 0, 1)
    def drawn(key, k):
        if key == 'lips':
            return lip_mask
        m = cv2.remap(M[key, k], mapx, mapy, cv2.INTER_LINEAR, borderValue=0)
        if key == 'stubble':                       # speckled texel by texel (in face space it smeared on the jaw's
            m = m * wide                               # stretch); where the area fades the hairs thin out, not
            sparse = np.clip((speck - (1 - m) * 0.9) / 0.25, 0, 1)                     # just grow faint
            lipcut = 1 - np.clip(cv2.dilate(lip_mask, np.ones((7, 7), np.uint8)) * 1.5, 0, 1)    # (the lips' own outline:
            return np.clip(m * 1.3, 0, 1) * sparse * (0.4 + 0.6 * speck) * lipcut                # the mesh's lip region
                                                                                                  # reached the chin)
        m = m * front
        if (key, k) in ONE_SIDED:
            m = m * single
        if key in ('freckles', 'age'):
            m = m * (1 - np.clip(lipw * 1.6, 0, 1))      # never on the lips
        return m
    layers = []                                    # (key, label, kind, options, masks)
    for key, label, kind, opts in LAYERS:
        if key == 'brows':                         # the faces' own brows (the base has none)
            layers.append((key, label, kind, ['Style %d' % (i + 1) for i in range(len(split['brows']))], split['brows']))
        elif key == 'age':                         # the faces' own lines, then the drawn ones
            n = len(split['ages'])
            layers.append((key, label, kind, (['Weathered'] if n == 1 else ['Weathered %d' % (i + 1) for i in range(n)])
                           + ['Lines'], split['ages'] + [drawn(key, 0)]))
        elif key == 'stubble':                     # a shadow (drawn), then the faces' painted beards
            layers.append((key, label, kind, ['Shadow'] + ['Beard %d' % (i + 1) for i in range(len(split['beards']))],
                           [drawn(key, 0)] + split['beards']))
        else:
            layers.append((key, label, kind, opts, [drawn(key, k) for k in range(len(opts))]))
    masks = [np.clip(m, 0, 1) for l_ in layers for m in l_[4]]
    # bleed the masks a few texels past the pieces' edges (mipmaps and filtering at the seams)
    k3 = np.ones((3, 3), np.uint8)
    out = []
    for m in masks:
        mm = m.copy()
        c = cov.copy()
        for _ in range(4):
            grown = cv2.dilate(mm, k3)
            mm = np.where(c, mm, grown)
            c = cv2.dilate(c.astype(np.uint8), k3).astype(bool)
        out.append(mm)
    while len(out) % 4:
        out.append(np.zeros_like(out[0]))
    names = []
    for i in range(0, len(out), 4):
        rgba = np.stack(out[i:i + 4], -1)
        name = 'skin_layers_%d' % (i // 4)
        cv2.imwrite(str(folder / (name + '.png')), cv2.cvtColor((rgba * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGBA2BGRA))
        names.append(name)
    ch = 0
    entry = {'tex': names, 'layers': [], 'base': 'face_base', 'face_map': split['face_map']}
    for key, label, kind, opts, _ in layers:
        entry['layers'].append({'key': key, 'label': label, 'kind': kind, 'options': opts,
                                'chan': list(range(ch, ch + len(opts)))})
        ch += len(opts)
    entry['hair_rgb'] = hair_rgb(meta, tex_dir)
    meta['skin_layers'] = entry
    meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print(folder.name, 'skin layers:', len(masks), 'masks in', len(names), 'textures; nose %.2f mouth %.2f chin %.2f'
          % (L['v_n'], L['v_m'], L['v_c']))
    if preview:
        # every layer at once, roughly as the shader will: dark for hair / age, brown freckles, pale scars, paint
        p = img[..., ::-1].copy()
        i = 0
        cols = {'hair': (0.18, 0.12, 0.08), 'freckle': None, 'age': None, 'scar': None, 'lip': (0.6, 0.1, 0.15),
                'paint': (0.1, 0.25, 0.6)}
        p = split['base'][..., 2::-1].copy()
        for key, label, kind, opts, _ in layers:
            for k in range(len(opts)):
                m = masks[i][..., None]
                i += 1
                if key == 'paint' and k != 4 and k != 5:
                    continue
                if key == 'brows' and k != 1:
                    continue
                if key == 'stubble' and k != len(opts) - 1:
                    continue
                if key == 'age' and k != 0:
                    continue
                if kind == 'freckle':
                    if k == 0:
                        p = p * (1 - m * (1 - np.array([0.62, 0.48, 0.38])))
                elif kind == 'age':
                    p = p * (1 - 0.45 * m)
                elif kind == 'scar':
                    p = p * (1 + m * (np.array([1.25, 1.05, 1.0]) - 1))
                else:
                    p = p * (1 - m) + np.array(cols[kind]) * m
        cv2.imwrite(str(preview), (np.clip(p[..., ::-1], 0, 1) * 255).astype(np.uint8))


if __name__ == '__main__':
    prev = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--preview=')), None)
    for a in sys.argv[1:]:
        if not a.startswith('--'):
            bake(a, prev)
