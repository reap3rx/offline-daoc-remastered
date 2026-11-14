"""The scalp cap as a skin layer (owner 2026-11-13: "Scalp cap in character creation: Can we just make it a texture
that overlays the scalp, rather than the hair model? I think it would work better."): where the race's cap shell
(figure.json hair_under, pipeline/import_hair.py) lies over the head, a mask in the head texture's own layout - the head
shader paints it in the hair colour, speckled like short hair (Fig3Figure._layers, way 3 as the stubble) - and the
shell itself is no longer drawn. Only its upper part, from well up the forehead to the crown and lower toward the back
(the owner: "more near the crown of the head, hidden by most hair styles"), drawn as slicked back hair: strands from front
to back in R (the hair colour) and the shade between them in G (Fig3Figure._layers, the layer's shade_chan).

    python scalp_layer.py <race folder> [more ...]   writes skin_scalp.png beside figure.gltf, adds it to figure.json's
                                                     skin_layers (its 'tex' list and a layer 'scalp')
    python scalp_layer.py <race folder> --preview    also scalp_preview.png (the face texture, the scalp painted dark)
"""
import json, sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import face_morphs as fmx
from skin_layers import raster, islands, SIZE

TEX_NAME = 'skin_scalp'


def mesh_of(g, name):
    """[(positions, uvs, triangles)] of the node's primitives."""
    node = next((n for n in g.g['nodes'] if n.get('name') == name and 'mesh' in n), None)
    if node is None:
        return []
    out = []
    for prim in g.g['meshes'][node['mesh']]['primitives']:
        P = g.acc(prim['attributes']['POSITION']).astype(np.float64)
        UV = g.acc(prim['attributes']['TEXCOORD_0']).astype(np.float64) if 'TEXCOORD_0' in prim['attributes'] else None
        T = g.acc(prim['indices']).astype(np.int64).reshape(-1, 3)
        out.append((P, UV, T))
    return out


def nearest(A, B, chunk=512):
    """Each point of A: its distance to the nearest point of B."""
    d = np.empty(len(A))
    for s in range(0, len(A), chunk):
        q = A[s:s + chunk]
        d[s:s + chunk] = np.sqrt(((q[:, None, :] - B[None, :, :]) ** 2).sum(2)).min(1)
    return d


def bake(folder, preview=False):
    folder = Path(folder)
    meta_path = folder / 'figure.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    hu = meta.get('hair_under') or {}
    sl = meta.get('skin_layers')
    if not hu.get('node') or not sl:
        print(folder.name, 'no scalp cap or no skin layers: skipped')
        return
    g = fmx.G(str(folder / 'figure.gltf'))
    head = mesh_of(g, 'head')
    cap = mesh_of(g, hu['node'])
    if not head or not cap:
        print(folder.name, 'no head / cap mesh: skipped')
        return
    P, UV, T = head[0]
    C = np.concatenate([c[0] for c in cap])
    z0, z1 = P[:, 2].min(), P[:, 2].max()
    H = z1 - z0                                             # the head's height (z up)
    # the cap's own spacing: how far apart its points are (its shell lies a little off the skin)
    samp = C[np.random.default_rng(1).choice(len(C), min(400, len(C)), replace=False)]
    dd = np.sqrt(((samp[:, None, :] - C[None, :, :]) ** 2).sum(2))
    dd[dd < 1e-9] = np.inf
    spacing = float(np.median(dd.min(1)))
    d = nearest(P, C)
    # under the shell: within its height off the skin (+ its own point spacing), fading out over a little more
    near = float(np.percentile(d, 10))                      # the shell's height over the scalp it covers
    t0 = near + 1.5 * spacing
    t1 = t0 + 0.035 * H
    m = np.clip((t1 - d) / max(t1 - t0, 1e-9), 0.0, 1.0)
    # which way the face looks along y: the cap comes down lowest at the back of the head (the nape), so the face is
    # the other way
    low = C[C[:, 2] < np.percentile(C[:, 2], 15)]
    front = -1.0 if low[:, 1].mean() > C[:, 1].mean() else 1.0
    fwd = P[:, 1] * front                                   # + toward the face
    f_mid = (fwd.max() + fwd.min()) / 2
    f_half = max((fwd.max() - fwd.min()) / 2, 1e-6)
    # only the big pieces of the texture (the face and scalp - not the eyeballs, teeth, ears)
    isl = islands(T, len(P))
    area = {}
    for t in T:
        a, b, c = UV[t]
        area[isl[t[0]]] = area.get(isl[t[0]], 0) + abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2
    total = sum(area.values())
    keep = np.array([area.get(isl[i], 0) > 0.08 * total for i in range(len(P))])
    # per texel: the shell's cover and where on the head it is (owner 2026-11-13, the first bake: "too low and far down
    # on the face. It needs to be more near the crown of the head, hidden by most hair styles, and the texture should be
    # more hair like ... slicked back hair")
    attrs = np.c_[m, (P[:, 2] - z0) / H, (fwd - f_mid) / f_half, P[:, 0] / f_half, (P[:, 2] - (z0 + 0.62 * H)) / f_half]
    tex, cov = raster(UV, T, attrs.astype(np.float32), keep, SIZE)
    shell = np.where(cov, tex[..., 0], 0.0)
    u, v = tex[..., 1], tex[..., 2]                         # height on the head 0..1; front (+1) .. back (-1)
    # the hairline: well up the forehead in front, lower toward the back of the head (the nape stays covered)
    cut = 0.73 + 0.15 * v
    edge = np.clip((u - cut) / 0.05, 0.0, 1.0)
    edge = edge * edge * (3 - 2 * edge)
    mask = (shell * edge).astype(np.float32)
    mask = cv2.GaussianBlur(mask, (0, 0), SIZE / 700)
    mask = np.clip(mask * 1.6, 0.0, 1.0)                    # (solid where it lies on the head, soft only at its edge)
    # slicked back: strands along the head's meridians, front to back - by the angle around the front-back axis
    ang = np.arctan2(tex[..., 3], tex[..., 4])
    rng = np.random.default_rng(7)
    n = 4096
    line = cv2.GaussianBlur(rng.random((1, n)).astype(np.float32), (0, 0), 1.6).ravel()
    line = (line - line.min()) / max(line.max() - line.min(), 1e-6)
    wob = 0.012 * np.sin(v * 7.0 + ang * 3.0)               # (strands bend a little on their way back)
    idx = ((ang + wob + np.pi) / (2 * np.pi) * (n - 1) * 0.5).astype(np.int64) % n
    strands = line[idx]
    broad = cv2.GaussianBlur(rng.random((1, n)).astype(np.float32), (0, 0), 40).ravel()
    broad = (broad - broad.min()) / max(broad.max() - broad.min(), 1e-6)
    strands = np.clip(0.75 * strands + 0.25 * broad[idx], 0, 1)
    # the hairline: a little ragged, short hairs thinning out
    speck = cv2.GaussianBlur(rng.random((SIZE, SIZE)).astype(np.float32), (0, 0), 0.7)
    speck = (speck - speck.min()) / max(speck.max() - speck.min(), 1e-6)
    thin = np.clip(mask * 1.6, 0, 1)
    body = np.clip(mask * (0.86 + 0.14 * strands) * np.where(mask < 0.4, 0.7 + 0.5 * speck, 1.0), 0, 1)
    gaps = np.clip(thin * (1.0 - strands) ** 1.6, 0, 1)    # darker between the strands
    rgba = np.zeros((SIZE, SIZE, 4), np.uint8)
    rgba[..., 2] = (body * 255).astype(np.uint8)            # (cv2 is BGRA: index 2 = R, the layer's channel)
    rgba[..., 1] = (gaps * 255).astype(np.uint8)            # G: the shade between the strands
    rgba[..., 3] = 255
    cv2.imwrite(str(folder / (TEX_NAME + '.png')), rgba)
    m = shell                                               # (for the report below)
    texs = sl.setdefault('tex', [])
    if TEX_NAME not in texs:
        if len(texs) >= 7:                                  # (the head shader takes seven layer textures)
            print(folder.name, 'seven layer textures already: skipped')
            return
        texs.append(TEX_NAME)
    chan = texs.index(TEX_NAME) * 4
    layers = [l for l in sl.get('layers', []) if l.get('key') != 'scalp']
    proto = next((l for l in layers if l.get('key') == 'stubble'), {})
    entry = {k: v for k, v in proto.items() if k not in ('key', 'label', 'chan', 'opts', 'options')}
    entry.update({'key': 'scalp', 'label': 'Scalp', 'kind': 'hair', 'chan': [chan], 'shade_chan': chan + 1})
    if 'opts' in proto:
        entry['opts'] = ['Cap']
    if 'options' in proto:
        entry['options'] = ['Cap']
    layers.append(entry)
    sl['layers'] = layers
    meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
    on = mask > 0.5
    print('%s scalp: %.1f%% of the texture, lowest at %.2f of the head height (front %.2f); face toward %s y; chan %d'
          % (folder.name, 100 * on.mean(), float(u[on].min()) if on.any() else -1,
             float(u[on & (v > 0.5)].min()) if (on & (v > 0.5)).any() else -1, '-' if front < 0 else '+', chan))
    if preview:
        tex_dir = folder.parent.parent / 'fig3_textures' / 'x4plus'
        f = tex_dir / (meta['faces'][0]['tex'].lower() + '.png')
        im = cv2.imread(str(f)) if f.exists() else np.full((SIZE, SIZE, 3), 180, np.uint8)
        im = cv2.resize(im, (SIZE, SIZE)).astype(np.float32)
        hair = np.array([40, 60, 95], np.float32)
        out = im * (1 - body[..., None]) + hair * body[..., None]
        out = out * (1 - 0.6 * gaps[..., None]) + hair * 0.45 * 0.6 * gaps[..., None]
        cv2.imwrite(str(folder / 'scalp_preview.png'), out.astype(np.uint8))


if __name__ == '__main__':
    pv = '--preview' in sys.argv
    for a in sys.argv[1:]:
        if not a.startswith('--'):
            bake(a, pv)
