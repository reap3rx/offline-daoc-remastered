"""New hair styles and beards from .obj models (owner 2026-11-06: "adding some new hair styles ... I've been collecting
some .obj files"): each fitted to a race's own head and added to its figure as one more hair style (or beard).

The models (WoW Model Viewer exports: y up, x forward) are fitted by their scalp: scaled and placed so the cap of the
hair sits just outside the race's skull (a small search over size and position, the cap's points kept at a hair's
thickness from the skin, never inside), then every point still inside the head pushed out along the skin (smoothly,
so the strands don't tear). Each style is skinned whole to the head bone, its texture made grey (its own colour
taken out) so the race's hair colours tint it like the others.

The models' own art stays on the owner's machine (content/ is not in the repository).

    python import_hair.py <race folder> <spec.json>      spec: {"hair": [{"obj": path, "label": ...}], "beards": [...]}
"""
import json, sys, re
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent))
from face_morphs import G, build, weld  # noqa: E402

GAP = 0.025          # the cap's distance off the skin, in head heights


def load_obj(path):
    """Positions in the head's frame (z up, the face toward -y), uvs, triangles - the hair geosets only (an export
    with a body geoset beside the hair: that one dropped)."""
    V, VT, F, FT = [], [], [], []
    keep = True
    for l in open(path, errors='ignore'):
        if l.startswith('v '):
            V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('vt '):
            VT.append([float(x) for x in l.split()[1:3]])
        elif l.startswith('usemtl'):
            keep = l.strip().endswith('_Dbl') or not re.search(r'_\d+$', l.strip())
        elif l.startswith('f ') and keep:
            parts = [p.split('/') for p in l.split()[1:]]
            for k in range(1, len(parts) - 1):
                tri = [parts[0], parts[k], parts[k + 1]]
                F.append([int(p[0]) - 1 for p in tri])
                FT.append([int(p[1]) - 1 if len(p) > 1 and p[1] else int(p[0]) - 1 for p in tri])
    V, VT, F, FT = np.array(V), np.array(VT), np.array(F), np.array(FT)
    # one vertex per corner (position + uv), then welded where both agree
    P = V[F.reshape(-1)][:, [2, 0, 1]] * [-1, -1, 1]
    UV = VT[FT.reshape(-1)] if len(VT) else np.zeros((len(P), 2))
    key = np.round(np.c_[P, UV] * 1e5).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return P[first], UV[first], inv.reshape(-1, 3)


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


def grey_texture(src, dst, cap=False):
    """The model's texture without its own colour: its brightness, about mid-grey, so a tint gives any colour. The
    scalp cap's a shade darker and even (it sits under the hair: a light streak in it read as bare skin)."""
    img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    rgb = img[..., :3].astype(np.float32) / 255
    lum = rgb @ np.array([0.11, 0.59, 0.3], np.float32)
    lum = lum / max(float(np.median(lum)), 1e-3) * 0.55
    if cap:
        lum = np.minimum(lum * 0.8, 0.5)
    out = np.clip(lum * 255, 0, 255).astype(np.uint8)
    out = np.stack([out, out, out, np.full_like(out, 255)], -1)
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


def hair_textures(src, tag, tex_dirs, flow_dir, cap=False):
    """The model's texture made grey (retinted by the hair colours), then redrawn as strands with its flow map
    (pipeline/hair_strands.py - the race's own hair had it: soft strands, lit as hair, not the raised relief)."""
    from hair_strands import strands
    flow_dir.mkdir(parents=True, exist_ok=True)
    for d in tex_dirs:
        dst = d / (tag.lower() + '.png')
        grey_texture(src, dst, cap=cap)
        im = cv2.imread(str(dst), cv2.IMREAD_UNCHANGED)
        if im.shape[1] < 1024:                  # (as the race's own: strands drawn at 1024 wide - on the models' 256
            k = 1024 / im.shape[1]               # the noise came out in blotches)
            cv2.imwrite(str(dst), cv2.resize(im, (1024, int(round(im.shape[0] * k))), interpolation=cv2.INTER_CUBIC))
        strands(dst, dst, flow_dir / (tag.lower() + '.png'), L=40 if not cap else 24, keep=0.15)


def colours_for(tag, base_cols):
    """The race's hair colours on a grey texture: each one's measured colour ('rgb', pipeline/split_beards.py) over
    the grey's 0.55."""
    return [{'tex': tag, 'chan': '', 'tint': [round(float(x) / 0.55, 4) for x in c_['rgb']], 'rgb': c_['rgb']}
            for c_ in base_cols]


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
    if any(s_.get('imported') for s_ in styles) or any(b.get('imported') for b in meta.get('beards', [])):
        print('already imported:', folder.name)
        return
    like = nodes[next(s['node'] for s in styles if s.get('node') and s['node'] in nodes)]
    base_cols = next(s['colours'] for s in styles if s.get('node') and s['colours'] and 'rgb' in s['colours'][0])
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
        stex = '%s_ns' % prefix
        src = Path(item['obj']).with_name(next(l.split(None, 1)[1].strip() for l in
                                              open(Path(item['obj']).with_suffix('.mtl'), errors='ignore')
                                              if l.startswith('map_Kd') and 'Body' not in l))
        hair_textures(src, stex, tex_dirs, flow_dir, cap=True)
        meta['hair_under'] = {'node': node, 'tex': stex, 'label': item.get('label', 'Scalp Cap'),
                              'colours': colours_for(stex, base_cols)}
        out.append((node, Q, T))
        print('%-12s %-28s %d tris' % (node, Path(item['obj']).name, len(T)))
    for kind in ('hair', 'beards'):
        for k, item in enumerate(spec.get(kind, [])):
            Q, UV, T = load_obj(item['obj'])
            ref = item.get('ref', item['obj'])                 # (the style the model's head is fitted on)
            if ref not in places:
                Qr = load_obj(ref)[0]
                places[ref] = fit(Qr, HP, HN, marks) if kind == 'hair' else fit_beard(Qr, HP, HN, marks)
            place, par, c = places[ref]
            Q = place(Q)
            Q = push_out(Q, T, HP, HN, H)
            N = skin_frame(Q, T)
            tag = '%s_%s%d' % (prefix, 'nh' if kind == 'hair' else 'nb', k + 1)
            node = 'new_hair_%d' % (k + 1) if kind == 'hair' else 'new_beard_%d' % (k + 1)
            add_mesh(g, like, node, Q, N, UV, T, jhead)
            tex_src = Path(item['obj']).with_name(next(l.split(None, 1)[1].strip() for l in
                                                       open(Path(item['obj']).with_suffix('.mtl'), errors='ignore')
                                                       if l.startswith('map_Kd') and 'Body' not in l))
            hair_textures(tex_src, tag, tex_dirs, flow_dir)
            cols = colours_for(tag, base_cols)
            entry = {'label': item.get('label', node), 'node': node, 'mesh': Path(item['obj']).name, 'colours': cols,
                     'imported': True}
            if kind == 'hair':
                entry['beard'] = 0
                styles.append(entry)
            else:                                      # (a beard carries its own colours: no style of its own)
                meta.setdefault('beards', []).append({'node': node, 'label': item.get('label', node), 'style': 0,
                                                      'colours': cols, 'imported': True})
            out.append((node, Q, T))
            print('%-12s %-28s scale %.3f  fit %.5f  %d tris' % (node, Path(item['obj']).name, par[0], c, len(T)))
    for node, Q, T in out:                         # (the face sliders move them as they move the race's own hair)
        follow_face(g, node, Q, HP, hp, names, H)
    g.save(folder / 'figure.gltf')
    meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
    return HP, HT, out


def fit_beard(Q, HP, HN, marks):
    """A beard by the face: its top (the moustache's line) under the nose, its width the jaw's."""
    H = marks['H']
    mouth, chin = marks['mouth'], marks['chin']
    jaw = HP[(HP[:, 2] < mouth[2]) & (HP[:, 2] > chin[2] - 0.05 * H) & (HP[:, 1] < mouth[1] + 0.25 * H)]
    s = (jaw[:, 0].max() - jaw[:, 0].min()) / max(Q[:, 0].max() - Q[:, 0].min(), 1e-9) * 1.08
    c_q = np.array([(Q[:, 0].max() + Q[:, 0].min()) / 2, Q[:, 1].min(), Q[:, 2].max()])
    c_h = np.array([mouth[0], mouth[1] - 0.02 * H, marks['nose_tip'][2] - 0.04 * H])
    return (lambda pts: (pts - c_q) * s + c_h), np.array([s, 0, 0]), 0.0


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
