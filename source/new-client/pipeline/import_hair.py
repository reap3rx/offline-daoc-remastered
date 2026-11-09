"""New hair styles and beards from .obj models (owner 2026-11-06: "adding some new hair styles ... I've been collecting
some .obj files"): each fitted to a race's own head and added to its figure as one more hair style (or beard).

The models (WoW Model Viewer exports: y up, x forward) are fitted by their scalp: scaled and placed so the cap of the
hair sits just outside the race's skull (a small search over size and position, the cap's points kept at a hair's
thickness from the skin, never inside), then every point still inside the head pushed out along the skin (smoothly,
so the strands don't tear). Each style is skinned whole to the head bone, its texture made grey (its own colour
taken out) so the race's hair colours tint it like the others.

The models' own art stays on the owner's machine (content/ is not in the repository).

    python import_hair.py <race folder> <spec.json>      spec: {"hair": [{"obj": path, "label": ...}], "beards": [...],
                                                                "moustaches": [...], "sideburns": [...]}
"""
import json, sys, re
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent))
from face_morphs import G, build, weld  # noqa: E402

GAP = 0.025          # the cap's distance off the skin, in head heights


def _mtl_textures(path):
    """Each material's texture (map_Kd) in the model's .mtl."""
    out, cur = {}, None
    mtl = Path(path).with_suffix('.mtl')
    if mtl.exists():
        for l in open(mtl, errors='ignore'):
            if l.startswith('newmtl'):
                cur = l.split(None, 1)[1].strip()
            elif l.startswith('map_Kd') and cur:
                out[cur] = l.split(None, 1)[1].strip()
    return out


def load_obj(path, jewels=False):
    """Positions in the head's frame (z up, the face toward -y), uvs, triangles - the hair geosets only (an export
    with a body geoset beside the hair: that one dropped). jewels: also the geoset drawn from the body's texture -
    a dwarf beard's braid rings (owner 2026-11-06: "missing the models for the rings in them") - and a fourth
    value, which triangles are those."""
    tex = _mtl_textures(path)
    V, VT, F, FT, J = [], [], [], [], []
    keep = True
    jew = False
    for l in open(path, errors='ignore'):
        if l.startswith('v '):
            V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('vt '):
            VT.append([float(x) for x in l.split()[1:3]])
        elif l.startswith('usemtl'):
            m = l.split(None, 1)[1].strip()
            hair = m.endswith('_Dbl') or not re.search(r'_\d+$', m)
            jew = not hair and _jewel_tex(tex.get(m, ''))
            keep = hair or (jewels and jew)
        elif l.startswith('f ') and keep:
            parts = [p.split('/') for p in l.split()[1:]]
            for k in range(1, len(parts) - 1):
                tri = [parts[0], parts[k], parts[k + 1]]
                F.append([int(p[0]) - 1 for p in tri])
                FT.append([int(p[1]) - 1 if len(p) > 1 and p[1] else int(p[0]) - 1 for p in tri])
                J.append(jew)
    V, VT, F, FT = np.array(V), np.array(VT), np.array(F), np.array(FT)
    # one vertex per corner (position + uv), then welded where both agree
    P = V[F.reshape(-1)][:, [2, 0, 1]] * [-1, -1, 1]
    UV = VT[FT.reshape(-1)] if len(VT) else np.zeros((len(P), 2))
    key = np.round(np.c_[P, UV] * 1e5).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    if jewels:
        return P[first], UV[first], inv.reshape(-1, 3), np.array(J, bool)
    return P[first], UV[first], inv.reshape(-1, 3)


def has_jewels(path):
    tex = _mtl_textures(path)
    return any(not (m.endswith('_Dbl') or not re.search(r'_\d+$', m)) and _jewel_tex(t) for m, t in tex.items())


def _jewel_tex(t):
    """A geoset drawn from the body's texture (a dwarf's braid rings) or a jewelry one (owner 2026-11-08: the Firbolg
    women's ponytail band missing - the Dracthyr exports' rings and bands)."""
    return 'Body' in t or 'jewelry' in t.lower()


def sub_mesh(Q, UV, T):
    """The points these triangles use, renumbered."""
    used = np.unique(T)
    remap = np.full(len(Q), -1, np.int64)
    remap[used] = np.arange(len(used))
    return Q[used], UV[used], remap[T]


def jewel_texture(obj, UV, tex_dirs):
    """The rings' part of the body texture they're drawn from (its own small texture, upscaled; the uvs remapped
    onto it). Untinted: metal stays metal whatever the hair colour."""
    import hashlib
    src = Path(obj).with_name(next(t for m, t in _mtl_textures(obj).items() if _jewel_tex(t)))
    img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    h, w = img.shape[:2]
    u0, v0 = np.floor(UV.min(0) * 64) / 64
    u1, v1 = np.ceil(UV.max(0) * 64) / 64
    u0, v0, u1, v1 = max(u0, 0), max(v0, 0), min(u1, 1), min(v1, 1)
    crop = img[int(round((1 - v1) * h)):int(round((1 - v0) * h)), int(round(u0 * w)):int(round(u1 * w))]
    tag = 'hj' + hashlib.md5(crop.tobytes()).hexdigest()[:10]
    cut = crop.ndim == 3 and crop.shape[2] == 4 and (crop[..., 3] < 128).mean() > 0.02   # (a band's cut-out shape)

    def keep_alpha(rgb):
        if not cut:
            return rgb[..., :3]
        a = cv2.resize(crop[..., 3], (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_LINEAR)
        return np.dstack([rgb[..., :3], a])
    for d in tex_dirs:
        dst = d / (tag + '.png')
        if not dst.exists():
            d.mkdir(parents=True, exist_ok=True)
            if d.name == 'original' or crop.shape[1] > 320:     # (a big piece of the atlas: sharp enough as it is)
                cv2.imwrite(str(dst), keep_alpha(crop))
            else:
                tmp = d.parent / 'hair_src' / (tag + '_c.png')
                tmp.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(tmp), crop[..., :3])
                big = upscale(tmp, d.parent / 'hair_src' / (tag + '.png'))
                cv2.imwrite(str(dst), keep_alpha(cv2.imread(str(big), cv2.IMREAD_UNCHANGED)))
    UVn = np.c_[(UV[:, 0] - u0) / (u1 - u0), (UV[:, 1] - v0) / (v1 - v0)]
    return tag, UVn


def skin_frame(P, T):
    """Vertex normals of the head (outward)."""
    N = np.zeros_like(P)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    if np.einsum('ij,ij->', P - P.mean(0), N) < 0:           # (the winding the other way: outward is the other side)
        N = -N
    return N


def nearest(A, B):
    d = np.full(len(A), np.inf)
    j = np.zeros(len(A), np.int64)
    for s in range(0, len(A), 256):
        dd = np.linalg.norm(A[s:s + 256, None, :] - B[None], axis=2)
        j[s:s + 256] = dd.argmin(1)
        d[s:s + 256] = dd.min(1)
    return d, j


def signed(Q, HP, HN):
    _, j = nearest(Q, HP)
    return np.einsum('ij,ij->i', Q - HP[j], HN[j]), j


def fit(Q, HP, HN, marks):
    """Size and place the hair on the head: its cap (the top of it) just outside the skull. Returns the placing (a
    function of the model's points: every style made on the same model head takes the same one), its parameters and
    how well it fits. Fitted on a style that covers the whole scalp (a top-knot or a tall ponytail would give its own
    width for the skull's)."""
    H = marks['H']
    eye = (marks['eyeL'] + marks['eyeR']) / 2
    skull = HP[HP[:, 2] > eye[2] + 0.05 * H]
    # the cap: the top of the hair, as deep as half its width
    wq = Q[:, 0].max() - Q[:, 0].min()
    cap = Q[Q[:, 2] > Q[:, 2].max() - 0.45 * wq]
    ws = skull[:, 0].max() - skull[:, 0].min()
    s = ws / max(cap[:, 0].max() - cap[:, 0].min(), 1e-9) * 1.04
    c_cap = np.array([(cap[:, 0].max() + cap[:, 0].min()) / 2, (cap[:, 1].max() + cap[:, 1].min()) / 2, cap[:, 2].max()])
    c_sk = np.array([(skull[:, 0].max() + skull[:, 0].min()) / 2, (skull[:, 1].max() + skull[:, 1].min()) / 2,
                     skull[:, 2].max() + GAP * H])
    sub = cap[np.linspace(0, len(cap) - 1, min(len(cap), 400)).astype(int)]

    def place(par, pts):
        sc, ty, tz = par
        return (pts - c_cap) * sc + c_sk + [0, ty, tz]

    def cost(par):
        sd, _ = signed(place(par, sub), HP, HN)
        sd = sd / H
        return float(np.mean((sd - GAP) ** 2) + 20 * np.mean(np.minimum(sd - 0.005, 0) ** 2))
    par = np.array([s, 0.0, 0.0])
    steps = np.array([0.08 * s, 0.04 * H, 0.04 * H])
    best = cost(par)
    for _ in range(6):                                  # coordinate search, halving the steps
        for _ in range(4):
            moved = False
            for k in range(3):
                for sg in (-1, 1):
                    p2 = par.copy()
                    p2[k] += sg * steps[k]
                    c2 = cost(p2)
                    if c2 < best:
                        par, best, moved = p2, c2, True
            if not moved:
                break
        steps *= 0.5
    return (lambda pts: place(par, pts)), par, best


def push_out(Q, T, HP, HN, H, clear=0.02):
    """Every point inside the head (or nearer it than a hair's width) out along the skin, the move smoothed over the
    mesh so the strands bend instead of tearing."""
    grp = weld(Q)
    sd, j = signed(Q, HP, HN)
    need = np.maximum(clear * H - sd, 0)
    need = np.minimum(need, 0.12 * H)                  # (an elf's ear through a fringe: let it through)
    D = HN[j] * need[:, None]
    ng = grp.max() + 1
    e = np.concatenate([grp[T[:, [0, 1]]], grp[T[:, [1, 2]]], grp[T[:, [2, 0]]]])
    G_ = np.zeros((ng, 3))
    np.add.at(G_, grp, D)
    cnt = np.bincount(grp, minlength=ng)[:, None]
    G_ = G_ / np.maximum(cnt, 1)
    for _ in range(4):
        S = np.zeros_like(G_)
        C = np.zeros(ng)
        np.add.at(S, e[:, 0], G_[e[:, 1]])
        np.add.at(S, e[:, 1], G_[e[:, 0]])
        np.add.at(C, e[:, 0], 1)
        np.add.at(C, e[:, 1], 1)
        sm = S / np.maximum(C, 1)[:, None]
        mag_g = np.linalg.norm(G_, axis=1)
        G_ = np.where((np.linalg.norm(sm, axis=1) > mag_g)[:, None], sm, G_)   # (spread, never shrink a push)
    return Q + G_[grp]


def grey_texture(src, dst, cap=False, alpha_src=None):
    """The model's texture without its own colour: its brightness, about mid-grey, so a tint gives any colour. The
    scalp cap's a shade darker and even (it sits under the hair: a light streak in it read as bare skin)."""
    img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    rgb = img[..., :3].astype(np.float32) / 255
    lum = rgb @ np.array([0.11, 0.59, 0.3], np.float32)
    a0 = cv2.imread(str(alpha_src), cv2.IMREAD_UNCHANGED) if alpha_src else None
    if a0 is not None and a0.ndim == 3 and a0.shape[2] == 4 and (a0[..., 3] < 128).mean() > 0.02:
        # (owner 2026-11-08: grey patches through the Lurikeen's hair, and others') - these models' texture is a
        # highlights layer (WoW lays it over a plain base colour): its alpha says where. Where it is clear its
        # colour means nothing (dark roots, black): those parts made the plain middle brightness, so the strands
        # run on unbroken. (Not a cut-out: kept as the alpha, the styles all but vanished.)
        a = cv2.resize(a0[..., 3], (lum.shape[1], lum.shape[0]), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
        mid = float(np.median(lum[a > 0.5])) if (a > 0.5).any() else float(np.median(lum))
        lum = a * lum + (1 - a) * mid
    lum = lum / max(float(np.median(lum)), 1e-3) * 0.55
    if cap:
        lum = np.minimum(lum * 0.8, 0.5)
    out = np.clip(lum * 255, 0, 255).astype(np.uint8)
    alpha = np.full_like(out, 255)
    out = np.stack([out, out, out, alpha], -1)
    cv2.imwrite(str(dst), out)
    return 0.55


def add_mesh(g, like_node, name, P, N, UV, T, joint):
    """A skinned mesh (one joint) as a node beside like_node (its skin, its parent)."""
    def add_acc(arr, ctype, typ, target=None, minmax=False):
        data = np.ascontiguousarray(arr).tobytes()
        data += b'\0' * (-len(data) % 4)
        g.g['buffers'].append({'byteLength': len(data)})
        g.b.append(bytearray(data))
        bv = {'buffer': len(g.b) - 1, 'byteOffset': 0, 'byteLength': len(data)}
        if target:
            bv['target'] = target
        g.g['bufferViews'].append(bv)
        acc = {'bufferView': len(g.g['bufferViews']) - 1, 'componentType': ctype, 'count': int(len(arr)), 'type': typ}
        if minmax:
            acc['min'] = arr.min(0).tolist()
            acc['max'] = arr.max(0).tolist()
        g.g['accessors'].append(acc)
        return len(g.g['accessors']) - 1
    n = len(P)
    attrs = {'POSITION': add_acc(P.astype(np.float32), 5126, 'VEC3', 34962, True),
             'NORMAL': add_acc(N.astype(np.float32), 5126, 'VEC3', 34962),
             'TEXCOORD_0': add_acc(np.c_[UV[:, 0], 1 - UV[:, 1]].astype(np.float32), 5126, 'VEC2', 34962),
             'JOINTS_0': add_acc(np.tile(np.array([joint, 0, 0, 0], np.uint16), (n, 1)), 5123, 'VEC4', 34962),
             'WEIGHTS_0': add_acc(np.tile(np.array([1, 0, 0, 0], np.float32), (n, 1)), 5126, 'VEC4', 34962)}
    idx = add_acc(T.reshape(-1).astype(np.uint32), 5125, 'SCALAR', 34963)
    like = g.g['meshes'][like_node['mesh']]['primitives'][0]
    prim = {'attributes': attrs, 'indices': idx}
    if 'material' in like:
        prim['material'] = like['material']
    g.g['meshes'].append({'name': name, 'primitives': [prim]})
    node = {k: v for k, v in like_node.items() if k not in ('children', 'name', 'mesh')}
    node['name'] = name
    node['mesh'] = len(g.g['meshes']) - 1
    g.g['nodes'].append(node)
    li = g.g['nodes'].index(like_node)
    parent = next((x for x in g.g['nodes'] if li in x.get('children', [])), None)
    if parent is not None:
        parent['children'].append(len(g.g['nodes']) - 1)
    else:
        for sc in g.g.get('scenes', []):
            sc['nodes'].append(len(g.g['nodes']) - 1)


def wrap(Q, T, HP, HN, H, off=0.014):
    """The cap drawn onto the skull: each point moved along the skin's normal until it sits off it by off (head
    heights), the moves smoothed over the cap so its curve stays the skin's, not the mesh's facets."""
    grp = weld(Q)
    idx = np.zeros((len(Q), 6), np.int64)
    dist = np.zeros((len(Q), 6))
    for s0 in range(0, len(Q), 256):
        dd = np.linalg.norm(Q[s0:s0 + 256, None, :] - HP[None], axis=2)
        ii = np.argpartition(dd, 6, axis=1)[:, :6]
        idx[s0:s0 + 256] = ii
        dist[s0:s0 + 256] = np.take_along_axis(dd, ii, 1)
    w = 1.0 / np.maximum(dist, 1e-5) ** 2
    w /= w.sum(1, keepdims=True)
    P0 = (HP[idx] * w[..., None]).sum(1)
    N0 = (HN[idx] * w[..., None]).sum(1)
    N0 /= np.maximum(np.linalg.norm(N0, axis=1, keepdims=True), 1e-9)
    sd = np.einsum('ij,ij->i', Q - P0, N0)
    D = N0 * (off * H - sd)[:, None]
    ng = grp.max() + 1
    e = np.concatenate([grp[T[:, [0, 1]]], grp[T[:, [1, 2]]], grp[T[:, [2, 0]]]])
    G_ = np.zeros((ng, 3))
    np.add.at(G_, grp, D)
    G_ /= np.maximum(np.bincount(grp, minlength=ng), 1)[:, None]
    for _ in range(2):
        S = np.zeros_like(G_)
        C = np.zeros(ng)
        np.add.at(S, e[:, 0], G_[e[:, 1]])
        np.add.at(S, e[:, 1], G_[e[:, 0]])
        np.add.at(C, e[:, 0], 1)
        np.add.at(C, e[:, 1], 1)
        G_ = 0.5 * G_ + 0.5 * S / np.maximum(C, 1)[:, None]
    Q = Q + G_[grp]
    return push_out(Q, T, HP, HN, H, clear=off * 0.6)      # (nothing left under the skin after the smoothing)


def upscale(src, out):
    """The model's small texture made 4x as the race's own hair sources were (Real-ESRGAN x4plus, tools/realesrgan):
    the strands drawn on a cubic-resized 256 came out blocky ("the texture seems to be rough"). Cubic if the tool
    isn't there."""
    import subprocess
    out.parent.mkdir(parents=True, exist_ok=True)
    exe = next(Path(__file__).parent.parent.joinpath('tools', 'realesrgan').glob('*/realesrgan-ncnn-vulkan.exe'), None)
    if exe is not None:
        tmp = out.with_suffix('.rgb.png')
        img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
        cv2.imwrite(str(tmp), img[..., :3])
        r = subprocess.run([str(exe), '-i', str(tmp), '-o', str(out), '-n', 'realesrgan-x4plus', '-s', '4'],
                           cwd=str(exe.parent), capture_output=True)
        tmp.unlink(missing_ok=True)
        if r.returncode == 0 and out.exists():
            return out
    img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    cv2.imwrite(str(out), cv2.resize(img, (img.shape[1] * 4, img.shape[0] * 4), interpolation=cv2.INTER_CUBIC))
    return out


def even_out(path, cap=False):
    """The texture's middle brightness put at the grey the colours assume (0.55: tint = the race colour / 0.55), so a
    style - and the cap - comes out in the colour the race's own hair has (owner 2026-11-06: the scalp didn't match
    the hair colour). The cap's light and dark also evened (a short cut's even colour, no streaks)."""
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    rgb = im[..., :3].astype(np.float32) / 255
    lum = rgb @ np.array([0.11, 0.59, 0.3], np.float32)
    isl = lum > 0.02
    if im.shape[2] == 4 and (im[..., 3] < 128).mean() > 0.02:
        isl &= im[..., 3] >= 128                     # (a cut-out's clear parts not counted)
    if cap:
        base = cv2.GaussianBlur(lum, (0, 0), 24)
        rgb = rgb * (0.55 + 0.6 * (lum - base))[..., None] / np.maximum(lum, 1e-3)[..., None]
        lum = rgb @ np.array([0.11, 0.59, 0.3], np.float32)
    rgb = rgb * (0.55 / max(float(np.median(lum[isl])), 1e-3))
    im[..., :3] = np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)
    cv2.imwrite(str(path), im)


def hair_textures(src, tag, tex_dirs, flow_dir, cap=False):
    """The model's texture upscaled, made grey (retinted by the hair colours), then redrawn as strands with its flow
    map (pipeline/hair_strands.py - the race's own hair had it: soft strands, lit as hair, not the raised relief)."""
    from hair_strands import strands
    flow_dir.mkdir(parents=True, exist_ok=True)
    big = upscale(src, tex_dirs[0].parent / 'hair_src' / (tag.lower() + '.png'))
    for d in tex_dirs:
        dst = d / (tag.lower() + '.png')
        grey_texture(big, dst, alpha_src=src)
        im = cv2.imread(str(dst), cv2.IMREAD_UNCHANGED)
        if im.shape[1] < 1024:
            k = 1024 / im.shape[1]
            cv2.imwrite(str(dst), cv2.resize(im, (1024, int(round(im.shape[0] * k))), interpolation=cv2.INTER_CUBIC))
        if cap:                                  # (fine, short, low contrast: a close crop, not painted locks)
            strands(dst, dst, flow_dir / (tag.lower() + '.png'), L=16, keep=0.0, contrast=0.14)
        elif _cut_out(src):                      # (the painted locks and waves kept, strands along them - below)
            strands(dst, dst, flow_dir / (tag.lower() + '.png'), L=30, keep=0.12, contrast=0.12, painted=True)
        else:
            strands(dst, dst, flow_dir / (tag.lower() + '.png'), L=40, keep=0.12)
        even_out(dst, cap)


def uv_mask(UV, T, rows_down=False, size=256):
    """Where on its texture a mesh draws (its triangles in uv space): an atlas's unused parts left out of its colour
    (owner 2026-11-08: the Kobold's new beards and styles far lighter than its own hair - the Kobold's hair texture
    is mostly unused light atlas)."""
    m = np.zeros((size, size), np.uint8)
    uv = np.mod(np.asarray(UV, np.float64), 1.0)
    px = np.c_[uv[:, 0] * size, (uv[:, 1] if rows_down else 1 - uv[:, 1]) * size]
    tri = np.round(px[np.asarray(T)] * 4).astype(np.int32)          # (2 bits of sub-pixel)
    cv2.fillPoly(m, list(tri), 1, lineType=cv2.LINE_8, shift=2)
    return m.astype(bool)


def _lin_mean(path, mask=None):
    """A texture's mean colour in linear light over its covered pixels (alpha over half, not the atlas's black) -
    and where the mesh draws on it, if given."""
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    img = cv2.resize(img, (256, 256), interpolation=cv2.INTER_AREA)
    rgb = img[..., :3][..., ::-1].astype(np.float64) / 255
    a = img[..., 3] > 128 if img.shape[2] == 4 else np.ones(img.shape[:2], bool)
    a &= rgb.max(-1) > 0.02
    if mask is not None and (a & mask).sum() > 50:
        a &= mask
    return (rgb[a] ** 2.2).mean(0) if a.any() else None


def colours_for(tag, base_cols, tex_dir, ours_mask=None, theirs_mask=None):
    """The race's hair colours on a grey texture. The tint is matched in linear light (the shader's tint is a
    source_color: made linear, then times the texture): the race's own texture x its tint averaged as the GPU sees it,
    over this texture's own average - the plain ratio of the sRGB averages ('rgb') came out darker and more saturated
    than the hair beside it (owner 2026-11-06: "the scalp style does not match the hair color")."""
    ours = _lin_mean(tex_dir / (tag.lower() + '.png'), ours_mask)
    out = []
    for c_ in base_cols:
        theirs = _lin_mean(tex_dir / (str(c_['tex']).lower() + '.png'), theirs_mask)
        if ours is None or theirs is None:
            tint = [round(float(x) / 0.55, 4) for x in c_['rgb']]
        else:
            want = theirs * np.array(c_.get('tint', [1, 1, 1]), np.float64) ** 2.2
            tint = [round(float(np.clip(x, 0, 3)), 4) for x in (want / np.maximum(ours, 1e-4)) ** (1 / 2.2)]
        out.append({'tex': tag, 'chan': '', 'tint': tint, 'rgb': c_['rgb']})
    return out


def follow_face(g, node_name, Q, HP, hp, names, H):
    """The head's face-slider targets (fx_, pipeline/face_morphs.py) on a new mesh: each point takes the moves of the
    head's nearest points, fading out a little way off the skin (as face_morphs does for the race's own hair)."""
    fx = [(k, t) for k, t in zip(names, hp.get('targets', [])) if k.startswith('fx_')]
    if not fx:
        return
    node = next(n for n in g.g['nodes'] if n.get('name') == node_name)
    mesh = g.g['meshes'][node['mesh']]
    idx = np.zeros((len(Q), 4), np.int64)
    dist = np.zeros((len(Q), 4))
    for s0 in range(0, len(Q), 512):
        dd = np.linalg.norm(Q[s0:s0 + 512, None, :] - HP[None], axis=2)
        ii = np.argpartition(dd, 4, axis=1)[:, :4]
        idx[s0:s0 + 512] = ii
        dist[s0:s0 + 512] = np.take_along_axis(dd, ii, 1)
    wgt = 1.0 / np.maximum(dist, 1e-4)
    wgt /= wgt.sum(1, keepdims=True)
    fall = np.clip(1.0 - (dist.min(1) - 0.01 * H) / (0.06 * H), 0, 1)
    prim = mesh['primitives'][0]
    for k, t in fx:
        D = g.acc(t['POSITION']).astype(np.float64)
        d = (D[idx] * wgt[..., None]).sum(1) * fall[:, None]
        prim.setdefault('targets', []).append({'POSITION': g.add_vec3(d), 'NORMAL': g.add_vec3(np.zeros_like(d))})
    mesh.setdefault('extras', {})['targetNames'] = [k for k, _ in fx]
    mesh['weights'] = [0.0] * len(fx)


FIT = [('lr', 'Left / Right'), ('up', 'Up / Down'), ('fwd', 'Forward / Back'), ('size', 'Size'), ('height', 'Height'),
       ('width', 'Width'), ('depth', 'Depth'), ('wrap', 'Wrap'), ('len', 'Length')]


def add_fit_targets(g, node_name, HP, marks, face=False):
    """Morph targets the creator's hair sliders drive (owner 2026-11-06: "could we have hair sliders ... placement,
    size, and length"; then: "A left/right slider ... one that kind of bends the sides backward (like curves the
    sides more towards the jawline) ... breaking the size sliders into size height, and size width ... a slider that
    affects the width from back to front", and freer ranges to fit every style by hand). Each a function of the point
    alone, so a beard's rings (a mesh of their own) move with it. At 1: 10% of the head across, 15% up / forward,
    35% bigger (all ways, or one), the sides drawn back, a long style 60% longer."""
    H = marks['H']
    eye = (marks['eyeL'] + marks['eyeR']) / 2
    sk = HP[HP[:, 2] > eye[2]]
    cen = np.array([(sk[:, 0].max() + sk[:, 0].min()) / 2, (sk[:, 1].max() + sk[:, 1].min()) / 2,
                    (eye[2] + HP[:, 2].max()) / 2])
    zl = eye[2] + 0.1 * H
    if face:                                       # (a beard or moustache: about the mouth, its length below it)
        m = marks['mouth']
        cen = np.array([m[0], m[1], m[2]])
        zl = m[2] - 0.02 * H
    node = next(n for n in g.g['nodes'] if n.get('name') == node_name)
    mesh = g.g['meshes'][node['mesh']]
    names = list(mesh.get('extras', {}).get('targetNames', []))
    if any(n.startswith('hf_') for n in names):
        return
    for prim in mesh['primitives']:
        P = g.acc(prim['attributes']['POSITION']).astype(np.float64)
        if len(prim.get('targets', [])) != len(names):
            prim['targets'] = prim.get('targets', [])[:len(names)]
        z = np.zeros_like(P)
        o = np.zeros(len(P))
        dx = P[:, 0] - cen[0]
        ds = {'lr': z + [0.1 * H, 0, 0], 'up': z + [0, 0, 0.15 * H], 'fwd': z + [0, -0.15 * H, 0],
              'size': (P - cen) * 0.35,
              'height': np.c_[o, o, (P[:, 2] - cen[2]) * 0.35],
              'width': np.c_[dx * 0.35, o, o],
              'depth': np.c_[o, (P[:, 1] - cen[1]) * 0.35, o],
              # the sides back (and a little in) by the square of the distance from the middle
              'wrap': np.c_[-0.25 * dx * np.abs(dx) / H, 0.9 * dx ** 2 / H, o],
              'len': np.c_[o, o, np.minimum(P[:, 2] - zl, 0) * 0.6]}
        for k, _ in FIT:
            prim.setdefault('targets', []).append({'POSITION': g.add_vec3(ds[k]), 'NORMAL': g.add_vec3(z)})
    mesh.setdefault('extras', {})['targetNames'] = names + ['hf_' + k for k, _ in FIT]
    mesh['weights'] = list(mesh.get('weights', [0.0] * len(names))) + [0.0] * len(FIT)


def tex_of(obj):
    """The model's own texture (its .mtl's map_Kd, not a body texture)."""
    obj = Path(obj)
    return obj.with_name(next(l.split(None, 1)[1].strip() for l in open(obj.with_suffix('.mtl'), errors='ignore')
                              if l.startswith('map_Kd') and 'Body' not in l))


def shared_tag(src, kind):
    """One game texture per model texture, shared by every race (the models' textures are few: most styles of one
    WoW head share one) - named by its content: hx<hash> hair, hc<hash> the cap's flavour."""
    import hashlib
    return '%s%s' % (kind, hashlib.md5(Path(src).read_bytes()).hexdigest()[:10])


def _cut_out(path):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    return im is not None and im.ndim == 3 and im.shape[2] == 4 and (im[..., 3] < 128).mean() > 0.02


TEXTURES_REV = 1794188400      # (2026-11-08: the highlights layers' clear parts evened, their strands along the
                               # painting - hair_strands painted; made again before this)


def ensure_textures(src, tag, tex_dirs, flow_dir, cap=False):
    """The shared texture made once (hair_textures), kept while newer than its source - and made again where the
    source is a highlights layer and its copy older than the fix for those (TEXTURES_REV)."""
    dst = tex_dirs[0] / (tag.lower() + '.png')
    if all((d / (tag.lower() + '.png')).exists() for d in tex_dirs) and (flow_dir / (tag.lower() + '.png')).exists() \
            and dst.stat().st_mtime >= Path(src).stat().st_mtime and (cap or not _cut_out(src)
                                                                      or dst.stat().st_mtime >= TEXTURES_REV):
        return
    hair_textures(src, tag, tex_dirs, flow_dir, cap=cap)


def model_source(obj):
    """Which WoW model the export came from (its materials' path): exports of one model share its frame."""
    mats = [l.split(None, 1)[1].strip() for l in open(obj, errors='ignore') if l.startswith('usemtl')]
    return ' '.join(sorted({re.sub(r'\.m2_.*$', '', m) for m in mats}))


def length_label(Q, marks):
    """Short / Medium / Long by where the hair ends: above the ears' middle, above the chin, below."""
    H = marks['H']
    eye = (marks['eyeL'] + marks['eyeR']) / 2
    lo = Q[:, 2].min()
    if lo > eye[2] - 0.12 * H:
        return 'Short'
    if lo > marks['chin'][2] - 0.1 * H:
        return 'Medium'
    return 'Long'


def coverage(Q, HP, marks):
    """How much of the skull a placed style covers (the share of the head's points above the brow with hair near)."""
    H = marks['H']
    eye = (marks['eyeL'] + marks['eyeR']) / 2
    sk = HP[HP[:, 2] > eye[2] + 0.1 * H]
    d, _ = nearest(sk, Q[np.linspace(0, len(Q) - 1, min(len(Q), 3000)).astype(int)])
    return float((d < 0.05 * H).mean())


def model_frames(frames, HP, HN, marks):
    """Each WoW model's placing on this head (owner 2026-11-06, the sorted folders): the exports of one model share
    its frame - its styles, beards and moustaches sit where its head was - so one placing serves them all: the fit of
    whichever of the model's fuller styles (spec 'frames': candidates per model) covers this skull best. (Each style
    fitted on itself put a mohawk's cap where the skull is; a top-knot's, a ponytail's, likewise.)"""
    out = {}
    for src, cands in frames.items():
        best = None
        for c in cands:
            try:
                Q, UV, T = load_obj(c)
            except Exception:
                continue
            f_ = fit(Q, HP, HN, marks)
            cv = coverage(f_[0](Q), HP, marks)
            if best is None or cv > best[0]:
                best = (cv, f_, Path(c).parent.name + '/' + Path(c).name)
        if best:
            out[src] = best[1] + (best[2],)
    return out


def face_frames(spec, native, HP, HN, marks):
    """Beards and moustaches of a WoW model whose hair isn't this race's own (a dwarf's beard on a Briton): placed by
    the face, not the skull - its skull's frame put a dwarf's beard over the eyes (their faces aren't ours). Sized by
    the model's beards: the top of a beard (its cheeks) as wide as this jaw, the median over the model's beards (by
    its moustaches alone they came out "much too small", owner 2026-11-06); placed by its moustaches: their tops (the
    nose) under this nose. A model with moustaches only: as wide as a moustache on this mouth."""
    from collections import defaultdict
    H = marks['H']
    mouth, chin = marks['mouth'], marks['chin']
    jaw = HP[(HP[:, 2] < mouth[2]) & (HP[:, 2] > chin[2] - 0.05 * H) & (HP[:, 1] < mouth[1] + 0.25 * H)]
    jw = np.ptp(jaw[:, 0])
    c_h = np.array([mouth[0], mouth[1] - 0.03 * H, marks['nose_tip'][2] - 0.035 * H])
    beards, musts = defaultdict(list), defaultdict(list)
    for kind, into in (('beards', beards), ('moustaches', musts)):
        for it in spec.get(kind, []):
            src = model_source(it['obj'])
            if src not in native:
                into[src].append(load_obj(it['obj'])[0])
    for it in spec.get('sideburns', []):           # (a model with sideburns only: sized as its beards would be)
        src = model_source(it['obj'])
        if src not in native and src not in beards and src not in musts:
            beards.setdefault('side:' + src, []).append(load_obj(it['obj'])[0])
    for k in [k for k in beards if k.startswith('side:')]:
        beards[k[5:]] = beards.pop(k)
    out = {}
    for src in set(beards) | set(musts):
        bs, ms = beards.get(src, []), musts.get(src, [])
        if bs:
            rows = []
            for Q in bs:
                band = Q[Q[:, 2] > Q[:, 2].max() - 0.3 * np.ptp(Q[:, 2])]
                rows.append((jw * 1.15 / max(np.ptp(band[:, 0]), 1e-9), Q))
            s_ = float(np.median([r[0] for r in rows]))
            Qr = min(rows, key=lambda r: abs(r[0] - s_))[1]
            band = Qr[Qr[:, 2] > Qr[:, 2].max() - 0.3 * np.ptp(Qr[:, 2])]
            c_q = np.array([(band[:, 0].max() + band[:, 0].min()) / 2, band[:, 1].min(), Qr[:, 2].max()])
            how = 'beards'
        else:
            ws = sorted((np.ptp(Q[:, 0]), i) for i, Q in enumerate(ms))
            s_ = jw * 0.62 / max(ws[len(ws) // 2][0], 1e-9)
            how = 'moustaches'
        if ms:
            c_q = np.median(np.array([[(m[:, 0].max() + m[:, 0].min()) / 2, m[:, 1].min(), m[:, 2].max()] for m in ms]), 0)
        out[src] = ((lambda pts, c_q=c_q, s_=s_: (pts - c_q) * s_ + c_h), np.array([s_, 0, 0]), 0.0, 'face by ' + how)
    return out


def group_places(items, HP, HN, marks, kind, frames=None):
    """Each item's placing: its model's frame (model_frames); a model with none - hair: fitted on itself; a beard or
    moustache: by the jaw (a moustache at a moustache's width)."""
    frames = frames or {}
    places = {}
    for it in items:
        src = it.get('src') or model_source(it['obj'])
        if src in frames:
            places[it['obj']] = frames[src]
        elif kind == 'hair':
            places[it['obj']] = fit(load_obj(it['obj'])[0], HP, HN, marks) + ('',)
        else:
            Q = load_obj(it['obj'])[0]
            places[it['obj']] = fit_beard(Q, HP, HN, marks, width=1.08 if it.get('kind') in ('beards', 'sideburns') else 0.62) + ('',)
    return places


def run(folder, spec_path, preview=None):
    folder = Path(folder)
    spec = json.loads(Path(spec_path).read_text(encoding='utf-8'))
    meta_path = folder / 'figure.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    g = G(folder / 'figure.gltf')
    nodes = {n.get('name'): n for n in g.g['nodes']}
    head = nodes['head']
    hp = g.g['meshes'][head['mesh']]['primitives'][0]
    HP = g.acc(hp['attributes']['POSITION']).astype(np.float64)
    HT = g.acc(hp['indices']).astype(np.int64).reshape(-1, 3)
    names = g.g['meshes'][head['mesh']].get('extras', {}).get('targetNames', [])
    fm = [g.acc(t['POSITION']).astype(np.float64) for t, k in zip(hp['targets'], names) if not k.startswith('fx_')][:8]
    _, marks = build(HP, g.acc(hp['attributes']['NORMAL']).astype(np.float64), HT, fm)
    HN = skin_frame(HP, HT)
    H = marks['H']
    joints = g.g['skins'][0]['joints']
    jhead = next(i for i, j in enumerate(joints) if g.g['nodes'][j].get('name') == 'Bip01 Head')
    styles = meta['hair_styles']
    if any(s_.get('imported') for s_ in styles) or any(b.get('imported') for b in meta.get('beards', [])) \
            or meta.get('hair_under'):
        print('already imported:', folder.name)
        return
    like = nodes[next(s['node'] for s in styles if s.get('node') and s['node'] in nodes)]
    if not any(s_.get('node') and s_['colours'] and 'rgb' in s_['colours'][0] for s_ in styles):
        from split_beards import colour_rgb          # (a race whose hair had no beard to split: not measured yet)
        colour_rgb(folder, meta)
    base_st = next(s for s in styles if s.get('node') and s['colours'] and 'rgb' in s['colours'][0])
    base_cols = base_st['colours']
    base_mask = None                               # (where the race's own style draws on its texture)
    bn = next((n for n in g.g['nodes'] if n.get('name') == base_st['node'] and 'mesh' in n), None)
    if bn is not None:
        bp = g.g['meshes'][bn['mesh']]['primitives'][0]
        if 'TEXCOORD_0' in bp['attributes']:
            base_mask = uv_mask(g.acc(bp['attributes']['TEXCOORD_0']).astype(float),
                                g.acc(bp['indices']).astype(int).reshape(-1, 3), rows_down=True)
    prefix = meta['prefix']
    tex_dirs = [folder.parent.parent / 'fig3_textures' / d for d in ('x4plus', 'original')]
    flow_dir = folder.parent.parent / 'fig3_textures' / 'hairflow'
    out = []
    places = {}
    if spec.get('scalp'):
        # (owner 2026-11-06: the models' "Var 1" is a cap tight on the scalp - "put on UNDER the hair every time, that
        # way the player can decide if they like it on or off": one per race, its own toggle in the creator, worn
        # under any style, the race's own ones too, in the hair's colour). Placed as the styles are, then drawn onto
        # this race's skull (each point to a hair's breadth off the skin), so it fits every head the same.
        # (fitted on itself, not on a style's head: placed by a full style it sat back - a receding hairline)
        item = spec['scalp']
        Q, UV, T = load_obj(item['obj'])
        ref = item.get('ref', item['obj'])
        place = fit(load_obj(ref)[0], HP, HN, marks)[0]
        Q = place(Q)
        eye = (marks['eyeL'] + marks['eyeR']) / 2
        sk = HP[HP[:, 2] > eye[2]]
        cen = np.array([(sk[:, 0].max() + sk[:, 0].min()) / 2, (sk[:, 1].max() + sk[:, 1].min()) / 2, eye[2]])
        Q = cen + (Q - cen) * float(item.get('grow', 1.0))      # (a little more of the head, if asked)
        Q = wrap(Q, T, HP, HN, H, off=float(item.get('off', 0.014)))
        node = 'new_scalp'
        add_mesh(g, like, node, Q, skin_frame(Q, T), UV, T, jhead)
        src = tex_of(item['obj'])
        stex = shared_tag(src, 'hc')
        ensure_textures(src, stex, tex_dirs, flow_dir, cap=True)
        meta['hair_under'] = {'node': node, 'tex': stex, 'label': item.get('label', 'Scalp Cap'),
                              'colours': colours_for(stex, base_cols, tex_dirs[0], uv_mask(UV, T), base_mask)}
        out.append((node, Q, T))
        print('%-12s %-28s %d tris' % (node, Path(item['obj']).name, len(T)))
    # the styles, beards and moustaches (owner 2026-11-06: sorted by head group - pipeline: claude-work/make_specs.py)
    counts = {}
    native = {model_source(it['obj']) for it in spec.get('hair', [])}
    # (candidates: the model's styles in this race's own list too - the widest from other folders alone missed the
    # good ones: an elf's short styles sank into her head)
    cands = {k: list(v) for k, v in spec.get('frames', {}).items() if k in native}
    for it in spec.get('hair', []):
        cands.setdefault(model_source(it['obj']), [])
        if it['obj'] not in cands[model_source(it['obj'])]:
            cands[model_source(it['obj'])].append(it['obj'])
    frames = model_frames(cands, HP, HN, marks)
    faces = face_frames(spec, native, HP, HN, marks)
    for src, f_ in frames.items():
        print('frame %-50s by %s  scale %.3f' % (src[-50:], f_[3], f_[1][0]))
    for kind in ('hair', 'beards', 'moustaches', 'sideburns'):
        items = [dict(it, kind=kind) for it in spec.get(kind, [])]
        if not items:
            continue
        places = group_places(items, HP, HN, marks, 'hair' if kind == 'hair' else 'face',
                              frames if kind == 'hair' else dict(frames, **faces))
        made = []
        for k, item in enumerate(items):
            Q, UV, T, J = load_obj(item['obj'], jewels=True)
            place, par, c, by = places[item['obj']]
            Q = place(Q)
            Q = push_out(Q, T, HP, HN, H)            # (the rings with the hair: they stay in their braids)
            node = {'hair': 'new_hair_%d', 'beards': 'new_beard_%d', 'moustaches': 'new_must_%d',
                    'sideburns': 'new_side_%d'}[kind] % (k + 1)
            jewel = None
            if J.any():
                Qj, UVj, Tj = sub_mesh(Q, UV, T[J])
                jtag, UVj = jewel_texture(item['obj'], UVj, tex_dirs)
                add_mesh(g, like, node + '_j', Qj, skin_frame(Qj, Tj), UVj, Tj, jhead)
                jewel = {'node': node + '_j', 'tex': jtag}
                out.append((node + '_j', Qj, Tj))
                Q, UV, T = sub_mesh(Q, UV, T[~J])
            N = skin_frame(Q, T)
            add_mesh(g, like, node, Q, N, UV, T, jhead)
            src = tex_of(item['obj'])
            tag = shared_tag(src, 'hx')
            ensure_textures(src, tag, tex_dirs, flow_dir)
            cols = colours_for(tag, base_cols, tex_dirs[0], uv_mask(UV, T), base_mask)
            if kind == 'hair':
                lab = item.get('label') or length_label(Q, marks)
            else:
                lab = item.get('label') or {'beards': 'Beard', 'moustaches': 'Moustache', 'sideburns': 'Sideburns'}[kind]
            counts[lab] = counts.get(lab, 0) + 1
            if not item.get('label'):
                lab = '%s %d' % (lab, counts[lab])
            entry = {'label': lab, 'node': node, 'mesh': Path(item['obj']).name, 'colours': cols, 'imported': True,
                     'model': str(Path(item['obj']).parent.name) + '/' + Path(item['obj']).name}
            if jewel:
                entry['jewels'] = jewel
            if kind == 'hair':
                entry['beard'] = 0
                made.append((lab, entry))
            elif kind == 'beards':                     # (a beard carries its own colours: no style of its own)
                entry['style'] = 0
                meta.setdefault('beards', []).append(entry)
            else:
                meta.setdefault(kind, []).append(entry)
            out.append((node, Q, T))
            print('%-12s %-30s %-12s scale %.3f  fit %.5f  %d tris%s' % (node, entry['model'][-30:], lab, par[0], c, len(T),
                                                                       ('  (frame %s)' % by) if by else ''))
        if kind == 'hair':                             # (in the creator: short to long, after the race's own)
            order = {'Short': 0, 'Medium': 1, 'Long': 2}
            made.sort(key=lambda m: (order.get(m[0].split()[0], 3), int(m[0].split()[-1]) if m[0].split()[-1].isdigit() else 0))
            styles.extend(e for _, e in made)
    for node, Q, T in out:                         # (the face sliders move them as they move the race's own hair)
        follow_face(g, node, Q, HP, hp, names, H)
    have = {n.get('name') for n in g.g['nodes']}
    for st in styles:                              # (the creator's hair sliders: every style, the race's own too)
        if st.get('node') and st['node'] in have:
            add_fit_targets(g, st['node'], HP, marks)
            st['fit'] = True
            if st.get('jewels'):
                add_fit_targets(g, st['jewels']['node'], HP, marks)
    for st in meta.get('beards', []) + meta.get('moustaches', []) + meta.get('sideburns', []):   # (owner 2026-11-06:
        if st.get('node') and st['node'] in have:                    # "some of the beards ... are too small")
            add_fit_targets(g, st['node'], HP, marks, face=True)
            st['fit'] = True
            if st.get('jewels'):                                     # (the rings: the same moves, by the same sliders)
                add_fit_targets(g, st['jewels']['node'], HP, marks, face=True)
    g.save(folder / 'figure.gltf')
    meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
    return HP, HT, out


def fit_beard(Q, HP, HN, marks, width=1.08):
    """A beard by the face: its top (the moustache's line) under the nose, its width the jaw's (width: of the jaw)."""
    H = marks['H']
    mouth, chin = marks['mouth'], marks['chin']
    jaw = HP[(HP[:, 2] < mouth[2]) & (HP[:, 2] > chin[2] - 0.05 * H) & (HP[:, 1] < mouth[1] + 0.25 * H)]
    s = (jaw[:, 0].max() - jaw[:, 0].min()) / max(Q[:, 0].max() - Q[:, 0].min(), 1e-9) * width
    c_q = np.array([(Q[:, 0].max() + Q[:, 0].min()) / 2, Q[:, 1].min(), Q[:, 2].max()])
    c_h = np.array([mouth[0], mouth[1] - 0.02 * H, marks['nose_tip'][2] - 0.04 * H])
    return (lambda pts: (pts - c_q) * s + c_h), np.array([s, 0, 0]), 0.0


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
