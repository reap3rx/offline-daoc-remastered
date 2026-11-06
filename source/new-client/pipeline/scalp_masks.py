"""Scalp masks (claude 2026-11-05, owner: a Sorceress's braid crown "not touching her head" - a slit of pale, shiny skin
between the crown and the hair under it, in the original model): for each race figure and hair style, which part of
the head sits under that hair, as a mask in the head's UV space. Fig3Figure tints the head there to the hair's colour,
matte - a gap in the hair then shows dark scalp, as real hair does at a parting, not lit skin.

A head vertex is under the hair when rays from it - along its normal and in a cone around it - meet the hair within a
short distance (a slit lets the normal's ray out, the slanted ones still meet the hair on either side). The share of
rays that meet it is the mask's strength, so the hairline fades. Also each hair texture's average colour (its strands,
by their alpha), for the tint.

    python scalp_masks.py <races dir> <figure gltf dir or ''> <textures dir> <out dir> [--reach=0.12]
<figure gltf dir>: where the unsmoothed figures are (<dir>/<prefix>/figure.gltf) - quicker, same UVs; '' = the races'.
Writes <out>/<prefix>_<style index>.png and <out>/colors.json."""
import base64, json, sys
from pathlib import Path
import numpy as np, cv2

COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
RES = 256


def arg(k, d):
    return float(next((a.split('=')[1] for a in sys.argv if a.startswith(f'--{k}=')), d))


class G:
    def __init__(self, path):
        self.g = json.load(open(path, encoding='utf-8'))
        self.b = [base64.b64decode(x['uri'].split(',', 1)[1]) for x in self.g['buffers']]

    def acc(self, i):
        a = self.g['accessors'][i]
        bv = self.g['bufferViews'][a['bufferView']]
        n = NC[a['type']]
        arr = np.frombuffer(self.b[bv['buffer']], COMP[a['componentType']], a['count'] * n,
                            bv.get('byteOffset', 0) + a.get('byteOffset', 0))
        return arr.reshape(a['count'], n) if n > 1 else arr

    def mesh(self, node_name):
        node = next((n for n in self.g['nodes'] if n.get('name') == node_name and 'mesh' in n), None)
        if node is None:
            return None
        P, N, U, T = [], [], [], []
        base = 0
        for p in self.g['meshes'][node['mesh']]['primitives']:
            at = p['attributes']
            pos = self.acc(at['POSITION']).astype(np.float64)
            P.append(pos)
            N.append(self.acc(at['NORMAL']).astype(np.float64) if 'NORMAL' in at else np.zeros_like(pos))
            U.append(self.acc(at['TEXCOORD_0']).astype(np.float64) if 'TEXCOORD_0' in at else np.zeros((len(pos), 2)))
            T.append(self.acc(p['indices']).astype(np.int64).reshape(-1, 3) + base)
            base += len(pos)
        return np.vstack(P), np.vstack(N), np.vstack(U), np.vstack(T)


def ray_hits(orig, dirs, tri, reach):
    """For each ray: does it meet a triangle within reach (Moller-Trumbore, both faces)."""
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    hit = np.zeros(len(orig), bool)
    for s in range(0, len(orig), 512):
        o = orig[s:s + 512, None, :]
        d = dirs[s:s + 512, None, :]
        pv = np.cross(d, e2[None])
        det = np.einsum('rtk,tk->rt', pv, e1)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = o - v0[None]
        u = np.einsum('rtk,rtk->rt', tv, pv) * inv
        qv = np.cross(tv, e1[None])
        v = np.einsum('rtk,rtk->rt', np.broadcast_to(d, qv.shape), qv) * inv
        t = np.einsum('rtk,tk->rt', qv, e2) * inv
        h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < reach)
        hit[s:s + 512] = h.any(axis=1)
    return hit


def cone(n, k=8, ang=40.0):
    """The normal and k directions around it at ang degrees."""
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    a = np.where(np.abs(n[:, :1]) < 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]]))
    t1 = np.cross(n, a)
    t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
    t2 = np.cross(n, t1)
    out = [n]
    c, s = np.cos(np.radians(ang)), np.sin(np.radians(ang))
    for i in range(k):
        ph = 2 * np.pi * i / k
        out.append(n * c + (t1 * np.cos(ph) + t2 * np.sin(ph)) * s)
    return out


def mask_for(head, hair, reach_frac):
    P, N, U, T = head
    HP, _, _, HT = hair
    size = np.ptp(P, axis=0).max()
    reach = reach_frac * size
    tri = HP[HT]
    # only the hair near the head matters
    dirs = cone(N)
    hits = np.zeros(len(P))
    orig = P + N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12) * 1e-4 * size
    for d in dirs:
        hits += ray_hits(orig, d, tri, reach)
    w = np.clip((hits / len(dirs) - 0.15) / 0.5, 0, 1)
    # the scalp only - above the eyes (a beard is hair too, but the lips and chin under it stay skin); the figures
    # stand z up
    z = P[:, 2]
    lo, hi = z.min(), z.max()
    w *= np.clip((z - (lo + arg("above", 0.55) * (hi - lo))) / (0.1 * (hi - lo)), 0, 1)
    img = np.zeros((RES, RES), np.float32)
    for f in T:
        uv = U[f] * RES
        pts = np.round(uv * 16).astype(np.int32)              # (subpixel: shift 4)
        val = float(w[f].mean())
        if val > 0:
            cv2.fillConvexPoly(img, pts, val, lineType=cv2.LINE_AA, shift=4)
    # close small holes (a slit's own texels), then soften
    k = np.ones((5, 5), np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, k)
    img = cv2.GaussianBlur(img, (0, 0), 2.0)
    return img, float(w.mean())


def main():
    races, base_dir, tex_dir, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    reach = arg('reach', 0.12)
    texfiles = {p.stem.lower(): p for p in tex_dir.glob('*.png')}
    colors = {}
    for fj in sorted(races.glob('*/figure.json')):
        meta = json.load(open(fj, encoding='utf-8'))
        prefix = fj.parent.name
        gpath = Path(base_dir) / prefix / 'figure.gltf' if base_dir else fj.parent / 'figure.gltf'
        if not gpath.exists():
            continue
        g = G(gpath)
        head = g.mesh('head')
        if head is None:
            continue
        for i, st in enumerate(meta.get('hair_styles', [])):
            node = st.get('node')
            hair = g.mesh(node) if node else None
            if hair is None:
                continue
            img, cover = mask_for(head, hair, reach)
            cv2.imwrite(str(out / f'{prefix}_{i}.png'), (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
            for c in st.get('colours', []):
                key = c['tex'].lower()
                if key in colors or key not in texfiles:
                    continue
                im = cv2.imread(str(texfiles[key]), cv2.IMREAD_UNCHANGED)
                im = cv2.resize(im, (128, 128), interpolation=cv2.INTER_AREA).astype(np.float64) / 255
                a = im[..., 3] if im.shape[2] == 4 else np.ones(im.shape[:2])
                a = a * (im[..., :3].max(axis=2) > 0.02)
                rgb = (im[..., :3] * a[..., None]).sum((0, 1)) / max(a.sum(), 1e-6)
                colors[key] = [round(float(rgb[2]), 4), round(float(rgb[1]), 4), round(float(rgb[0]), 4)]
        print(prefix, len(meta.get('hair_styles', [])), 'styles', flush=True)
    (out / 'colors.json').write_text(json.dumps(colors, indent=0), encoding='utf-8')
    print('colours', len(colors))


if __name__ == '__main__':
    main()
