"""The HD head's textures (the character creator plan, owner 2026-11-25: "HD textures ... detailed", and the brows not
painted in): in the head's own layout (hd_layout.py), 2048 square -
  hd_remap.png  each texel's place on the classic face texture (16 bits a coordinate: R/G the u, B/A the v; A=0 where
                nothing is drawn) - the head shader reads every classic-layout texture through it: the skin layers,
                brows, freckles, scars, stubble, lip colour, tattoos, war paint, the eye colour
  hd_base.png   the race's base face (skin_layers' face_base: no painted brows - the brow chooser draws them), baked
  hd_detail.png (shared by every race) R the skin's fine relief - pores, the lids' creases, the lips' lines - and G its
                cavities (shading), from MakeHuman's head itself
Every texel is found on the classic skin by its own place on the head (not by its corners' UVs): no stretch across
the classic texture's seams. The places the classic texture has nothing for (the eye pockets, the mouth's inside, the
new ears) take the per-corner UVs the head's build worked out for them."""
import numpy as np
import cv2
from scipy.spatial import cKDTree
from scipy import ndimage

SIZE = 2048


def raster(UV2, T, attrs, size=SIZE):
    """Each texel inside a triangle (layout space): its barycentric mix of the corners' attrs. -> (img, mask)."""
    H = W = size
    out = np.zeros((H, W, attrs.shape[1]), np.float32)
    mask = np.zeros((H, W), bool)
    P2 = np.c_[UV2[:, 0] * W - 0.5, UV2[:, 1] * H - 0.5]          # (row = v: glTF and Godot read v downward)
    for t in T:
        a, b, c = P2[t]
        x0 = int(max(np.floor(min(a[0], b[0], c[0])), 0)); x1 = int(min(np.ceil(max(a[0], b[0], c[0])), W - 1))
        y0 = int(max(np.floor(min(a[1], b[1], c[1])), 0)); y1 = int(min(np.ceil(max(a[1], b[1], c[1])), H - 1))
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        w2 = 1 - w0 - w1
        ins = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        if not ins.any():
            continue
        v = w0[..., None] * attrs[t[0]] + w1[..., None] * attrs[t[1]] + w2[..., None] * attrs[t[2]]
        sub = out[y0:y1 + 1, x0:x1 + 1]
        sub[ins] = v[ins]
        mask[y0:y1 + 1, x0:x1 + 1] |= ins
    return out, mask


def pad(img, mask, px=12):
    """The texels round each piece take their nearest drawn texel's value (no seams in filtering or mips)."""
    dist, (iy, ix) = ndimage.distance_transform_edt(~mask, return_indices=True)
    out = img[iy, ix]
    return out, dist <= px


def classic_uv(Q, cP, cT, cUV):
    """Each point's UV on the classic skin: the nearest classic triangle's, the point dropped onto it."""
    n = 6
    bs = np.array([(i / n, j / n, 1 - i / n - j / n) for i in range(n + 1) for j in range(n + 1 - i)])
    S = np.einsum('kb,tbd->tkd', bs, cP[cT]).reshape(-1, 3)
    tid = np.repeat(np.arange(len(cT)), len(bs))
    _, j = cKDTree(S).query(Q, workers=-1)
    k = tid[j]
    A, B, C = cP[cT[k, 0]], cP[cT[k, 1]], cP[cT[k, 2]]
    e1, e2, pv = B - A, C - A, Q - A
    d11 = (e1 * e1).sum(1); d12 = (e1 * e2).sum(1); d22 = (e2 * e2).sum(1)
    p1 = (pv * e1).sum(1); p2 = (pv * e2).sum(1)
    den = d11 * d22 - d12 * d12
    l1 = (d22 * p1 - d12 * p2) / np.where(np.abs(den) < 1e-12, 1e-12, den)
    l2 = (d11 * p2 - d12 * p1) / np.where(np.abs(den) < 1e-12, 1e-12, den)
    l1 = np.clip(l1, 0, 1); l2 = np.clip(l2, 0, 1)
    s = l1 + l2
    over = s > 1
    l1[over] /= s[over]; l2[over] /= s[over]
    l0 = 1 - l1 - l2
    return l0[:, None] * cUV[cT[k, 0]] + l1[:, None] * cUV[cT[k, 1]] + l2[:, None] * cUV[cT[k, 2]]


def bake_remap(PV, T2, UV2, UVs, special, cP, cT, cUV):
    """-> the classic UV of every texel (H, W, 2) and the drawn mask. special (per corner, 0..1): where the corners'
    own UVs are used instead of the projection."""
    attrs = np.c_[PV, UVs, special]
    img, mask = raster(UV2, T2, attrs)
    Q = img[mask][:, :3].astype(np.float64)
    proj = classic_uv(Q, cP, cT, cUV)
    own = img[mask][:, 3:5]
    sp = np.clip(img[mask][:, 5:6], 0, 1)
    uv = proj * (1 - sp) + own * sp
    out = np.zeros(img.shape[:2] + (2,), np.float32)
    out[mask] = uv
    return out, mask


def encode_remap(uv, mask):
    q = np.clip(np.round(np.clip(uv, 0, 1) * 65535), 0, 65535).astype(np.uint32)
    rgba = np.zeros(uv.shape[:2] + (4,), np.uint8)
    rgba[..., 0] = q[..., 0] >> 8; rgba[..., 1] = q[..., 0] & 255
    rgba[..., 2] = q[..., 1] >> 8; rgba[..., 3] = q[..., 1] & 255
    rgba[~mask] = 0
    return rgba


def bake_base(uv, mask, base_bgra):
    """The base face looked up through the remap, at 2048 (bicubic from the 1024 picture), lightly sharpened."""
    Hs, Ws = base_bgra.shape[:2]
    mx = (uv[..., 0] * Ws - 0.5).astype(np.float32)
    my = (uv[..., 1] * Hs - 0.5).astype(np.float32)       # (glTF UV: v down the image, as the client reads it)
    img = cv2.remap(base_bgra, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    blur = cv2.GaussianBlur(img, (0, 0), 1.2)
    img = cv2.addWeighted(img, 1.35, blur, -0.35, 0)
    return img


def detail(PV, T2, UV2, eyes, mouth, nose):
    """The shared relief: pores (finer and denser on the nose and cheeks, few on the lips and lids), creases where the
    head itself curves in (the lids' folds, the nose-to-cheek line, the lips' meeting, the ears' folds) and fine
    vertical lines on the lips."""
    n = len(PV)
    # mean curvature (umbrella) per point: + where the surface dips in
    nb = [[] for _ in range(n)]
    for t in T2:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            nb[t[a]].append(t[b]); nb[t[b]].append(t[a])
    lap = np.array([PV[list(set(x))].mean(0) - PV[i] if x else np.zeros(3) for i, x in enumerate(nb)])
    from fit2 import vnormals
    N = vnormals(PV, T2)
    curv = (lap * N).sum(1)
    E = np.linalg.norm(eyes[0] - eyes[1])
    dl = lambda c, r: np.exp(-((PV - c) ** 2).sum(1) / (r * r))
    on_lips = dl(mouth, 0.45 * E)
    on_lids = np.maximum(dl(eyes[0], 0.5 * E), dl(eyes[1], 0.5 * E))
    pore_amt = np.clip(0.55 + 0.6 * dl(nose, 0.9 * E) - 0.5 * on_lids - 0.8 * on_lips, 0.1, 1.2)
    # the lips' coordinate across (for their vertical lines)
    attrs = np.c_[curv, pore_amt, on_lips, (PV[:, 0] - mouth[0]) / E]
    img, mask = raster(UV2, T2, attrs)
    img, near = pad(img, mask, 24)
    cv = img[..., 0]
    scale = np.percentile(np.abs(cv[mask]), 98) + 1e-9
    crease = np.clip(cv / scale, -1, 1)
    crease = cv2.GaussianBlur(crease.astype(np.float32), (0, 0), 2.0)
    rng = np.random.default_rng(5)
    def noise(sig):
        z = rng.standard_normal((SIZE, SIZE)).astype(np.float32)
        z = cv2.GaussianBlur(z, (0, 0), sig)
        return z / (z.std() + 1e-9)
    pores = np.clip(noise(1.1) * 0.8 - 0.9, -3, 0) * -1          # small pits
    fine = noise(2.5) * 0.25 + noise(6) * 0.15
    lipline = np.sin(img[..., 3] * 70.0) * 0.5 * np.clip(img[..., 2] * 1.6 - 0.4, 0, 1)
    h = 0.5 - 0.22 * pores * img[..., 1] + 0.05 * fine - 0.18 * np.clip(crease, 0, 1) + 0.04 * lipline
    ao = 1.0 - 0.4 * np.clip(crease, 0, 1) - 0.02 * pores * img[..., 1]
    out = np.zeros((SIZE, SIZE, 4), np.uint8)
    out[..., 2] = np.clip(h * 255, 0, 255)          # (BGR: R = the height)
    out[..., 1] = np.clip(ao * 255, 0, 255)
    out[..., 0] = 128
    out[..., 3] = 255
    return out
