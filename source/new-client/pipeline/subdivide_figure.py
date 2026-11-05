"""A race figure (content/characters/races/<prefix>/figure.gltf) with its body, head, hair and cloak meshes made
smoother: Loop subdivision, the same rules for the face / hair morph targets (they are linear, so a morph keeps its
shape), skin weights carried to the new points, normals recomputed smooth. Everything else in the glTF - skeleton,
clips, extras - is left as it was. (2026-11-05, owner: "pretty blocky and hurts our lighting system": the comparison
of texture and geometry remasters.)

    python pipeline/subdivide_figure.py <in figure.gltf> <out figure.gltf> [levels=1] [--hard=<degrees>] [--crease=<degrees>]

Creases: an edge whose two faces fold by more than --crease (70) keeps its line (the curve rules) - an ear's rim, the
tip of a pointed ear, a pauldron's or a boot's edge - so they don't melt away (the first try thinned the ears).

UV seams: the glTF splits a vertex where its UVs (or normals) differ; the surface is welded by position for the
smoothing so seams don't open, and each side keeps its own UVs. Open edges (the neck hole, a sleeve's end) stay
exactly where they were, so two parts meeting there stay joined. The helm meshes (ADR_*) are left alone.
"""
import base64, json, re, sys
from collections import defaultdict

import numpy as np

COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
SMOOTH = re.compile(r'^(Body|Legs|Arms|Boots|Gloves|Cloak)\d+_|_head\d+$|_hair\d+$', re.I)


class Gltf:
    def __init__(self, path):
        self.g = json.load(open(path, encoding='utf-8'))
        self.bufs = [bytearray(base64.b64decode(b['uri'].split(',', 1)[1])) for b in self.g['buffers']]
        self.out = bytearray()

    def read(self, i):
        a = self.g['accessors'][i]
        bv = self.g['bufferViews'][a['bufferView']]
        n = NCOMP[a['type']]
        dt = np.dtype(COMP[a['componentType']])
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = bv.get('byteStride', 0)
        if stride and stride != n * dt.itemsize:
            raw = np.frombuffer(self.bufs[bv['buffer']], np.uint8, count=stride * a['count'], offset=off)
            arr = np.ndarray((a['count'], n), dt, raw.data, 0, (stride, dt.itemsize)).copy()
        else:
            arr = np.frombuffer(self.bufs[bv['buffer']], dt, count=a['count'] * n, offset=off).copy()
        return arr.reshape(a['count'], n) if n > 1 else arr

    def write(self, arr, ctype, atype, target=None, minmax=False):
        arr = np.ascontiguousarray(arr.astype(COMP[ctype]))
        while len(self.out) % 4:
            self.out.append(0)
        off = len(self.out)
        self.out += arr.tobytes()
        bv = {'buffer': len(self.bufs), 'byteOffset': off, 'byteLength': arr.nbytes}
        if target:
            bv['target'] = target
        self.g['bufferViews'].append(bv)
        acc = {'bufferView': len(self.g['bufferViews']) - 1, 'componentType': ctype,
               'count': int(arr.shape[0]), 'type': atype}
        if minmax:
            acc['min'] = arr.min(axis=0).tolist()
            acc['max'] = arr.max(axis=0).tolist()
        self.g['accessors'].append(acc)
        return len(self.g['accessors']) - 1

    def save(self, path):
        self.g['buffers'].append({'byteLength': len(self.out),
                                  'uri': 'data:application/octet-stream;base64,' + base64.b64encode(bytes(self.out)).decode()})
        json.dump(self.g, open(path, 'w', encoding='utf-8'), separators=(',', ':'))


def smooth_normals(pos, tris, weld, nweld, keep=None, hard_cos=None):
    """Area-weighted normals summed per welded point; with keep (the old per-corner normals) and hard_cos, a corner
    whose old normal differs from the welded average by more than the hard angle keeps its own side's (hard edges)."""
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    acc = np.zeros((nweld, 3))
    for c in range(3):
        np.add.at(acc, weld[tris[:, c]], fn)
    n = acc[weld]
    if keep is not None and hard_cos is not None:
        side = np.zeros((len(pos), 3))
        for c in range(3):
            np.add.at(side, tris[:, c], fn)
        sn = side / np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-12)
        wn = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        kn = keep / np.maximum(np.linalg.norm(keep, axis=1, keepdims=True), 1e-12)
        # where the source split this point's normals (a hard edge), the per-side average
        split = np.zeros(nweld, bool)
        cosv = np.einsum('ij,ij->i', kn, wn)
        np.logical_or.at(split, weld, cosv < hard_cos)
        n = np.where(split[weld][:, None], sn, wn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def loop_once(pos, uv, joints, weights, targets, tris, normals_in, hard_cos, crease_cos=None):
    nv = len(pos)
    # weld by position
    key = np.round(pos / 1e-4).astype(np.int64)
    _, weld, inv_counts = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    weld = weld.reshape(-1)
    nw = weld.max() + 1
    first = np.zeros(nw, np.int64)
    first[weld[::-1]] = np.arange(nv)[::-1]
    wt = weld[tris]
    # welded edges, their faces and opposite points
    edge_faces = defaultdict(list)
    edge_fids = defaultdict(list)
    for f, (a, b, c) in enumerate(wt):
        for u, v, o in ((a, b, c), (b, c, a), (c, a, b)):
            if u != v:
                edge_faces[(min(u, v), max(u, v))].append(o)
                edge_fids[(min(u, v), max(u, v))].append(f)
    Pw0 = pos[first]
    fn = np.cross(Pw0[wt[:, 1]] - Pw0[wt[:, 0]], Pw0[wt[:, 2]] - Pw0[wt[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    edges = list(edge_faces)
    eidx = {e: i for i, e in enumerate(edges)}
    nbrs = defaultdict(set)
    bnbrs = defaultdict(set)                       # open edges and creases: the curve rules
    sharp = set()
    openv = set()                                  # on an open edge: where two parts meet (neck, wrist, ankle)
    for (u, v), opp in edge_faces.items():
        nbrs[u].add(v)
        nbrs[v].add(u)
        crease = False
        if len(opp) == 2 and crease_cos is not None:
            f0, f1 = edge_fids[(u, v)]
            crease = float(np.dot(fn[f0], fn[f1])) < crease_cos   # a sharp fold: an ear's rim, a pauldron's edge
        if len(opp) != 2 or crease:
            bnbrs[u].add(v)
            bnbrs[v].add(u)
            sharp.add((u, v))
        if len(opp) != 2:
            openv.update((u, v))

    def stencils():
        rows_old = []
        for w in range(nw):
            if w in openv:                         # stays put: the part beside it has the same edge (the first
                rows_old.append([(w, 1.0)])        # try rounded a shirt's V-neck away from the neck: a black gap)
            elif w in bnbrs:
                b = sorted(bnbrs[w])
                rows_old.append([(w, 1.0)] if len(b) != 2 else [(w, 0.75), (b[0], 0.125), (b[1], 0.125)])
            else:
                n = len(nbrs[w])
                if n == 0:
                    rows_old.append([(w, 1.0)])
                    continue
                beta = 3.0 / (8.0 * n) if n > 3 else 3.0 / 16.0
                rows_old.append([(w, 1 - n * beta)] + [(u, beta) for u in nbrs[w]])
        rows_edge = []
        for (u, v) in edges:
            opp = edge_faces[(u, v)]
            rows_edge.append([(u, .375), (v, .375), (opp[0], .125), (opp[1], .125)] if (u, v) not in sharp
                             else [(u, .5), (v, .5)])
        return rows_old, rows_edge

    rows_old, rows_edge = stencils()

    def apply(rows, X):
        out = np.zeros((len(rows), X.shape[1]))
        for i, r in enumerate(rows):
            for w, c in r:
                out[i] += c * X[w]
        return out

    def subdiv(P):            # welded positions -> (old points, edge points)
        Pw = P[first]
        return apply(rows_old, Pw), apply(rows_edge, Pw)

    old_p, edge_p = subdiv(pos)
    t_old = [subdiv(pos + d) for d in targets]
    # new vertices: the old ones (each keeps its UV and weights), then one per (corner pair) edge use
    corner_pair = {}
    new_pos, new_uv, new_j, new_w, new_t = [old_p[weld]], [uv], [joints], [weights], [[o[weld] for o, _ in t_old]]
    ex_pos, ex_uv, ex_j, ex_w, ex_t = [], [], [], [], [[] for _ in targets]
    ewelded = []
    out_tris = []
    for (a, b, c) in tris:
        mids = []
        for u, v in ((a, b), (b, c), (c, a)):
            k = (min(u, v), max(u, v))
            if k not in corner_pair:
                corner_pair[k] = nv + len(ex_pos)
                ei = eidx.get((min(weld[u], weld[v]), max(weld[u], weld[v])))
                if ei is None:                             # (a degenerate edge: both ends at one point)
                    ewelded.append(-1 - int(weld[u]))
                    ex_pos.append(old_p[weld[u]])
                else:
                    ewelded.append(ei)
                    ex_pos.append(edge_p[ei])
                ex_uv.append((uv[u] + uv[v]) / 2)
                acc = defaultdict(float)
                for j, w in zip(joints[u], weights[u]):
                    acc[int(j)] += w / 2
                for j, w in zip(joints[v], weights[v]):
                    acc[int(j)] += w / 2
                top = sorted(acc.items(), key=lambda x: -x[1])[:4]
                s = sum(w for _, w in top) or 1.0
                top += [(0, 0.0)] * (4 - len(top))
                ex_j.append([j for j, _ in top])
                ex_w.append([w / s for _, w in top])
                for ti, (to, te) in enumerate(t_old):
                    ex_t[ti].append(te[ei] if ei is not None else to[weld[u]])
            mids.append(corner_pair[k])
        ab, bc, ca = mids
        out_tris += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
    P = np.vstack([old_p[weld], np.array(ex_pos)])
    UV = np.vstack([uv, np.array(ex_uv)])
    J = np.vstack([joints, np.array(ex_j)])
    W = np.vstack([weights, np.array(ex_w)])
    T = [np.vstack([o[weld], np.array(ex_t[ti])]) for ti, (o, _) in enumerate(t_old)]
    tris2 = np.array(out_tris, np.int64)
    ew = np.array(ewelded)
    weld2 = np.concatenate([weld, np.where(ew >= 0, nw + ew, -1 - ew)])   # (a degenerate edge's point is its end's)
    # normals: the old corners keep a hard side where the source had one; the new edge points follow theirs
    keep = None
    if normals_in is not None:
        keep = np.vstack([normals_in, (normals_in[[k[0] for k in corner_pair]] + normals_in[[k[1] for k in corner_pair]]) / 2])
    N = smooth_normals(P, tris2, weld2, weld2.max() + 1, keep, hard_cos)
    deltas = [t - P for t in T]
    return P, UV, J, W, deltas, tris2, N


def smooth_file(src, dst, levels=1, hard=60.0, crease=70.0):
    """build_races.py calls this on each figure it writes (the remaster, owner 2026-11-05)."""
    hard_cos = np.cos(np.radians(hard))
    crease_cos = np.cos(np.radians(crease)) if crease > 0 else None
    G = Gltf(src)
    extras = G.g.setdefault('asset', {}).setdefault('extras', {})
    if extras.get('subdivided'):
        print(src, 'is smoothed already')
        return
    extras['subdivided'] = levels
    done = 0
    for mesh in G.g['meshes']:
        if not SMOOTH.search(mesh['name']):
            continue
        for prim in mesh['primitives']:
            if prim.get('mode', 4) != 4 or 'indices' not in prim:
                continue
            at = prim['attributes']
            pos = G.read(at['POSITION']).astype(np.float64)
            nrm = G.read(at['NORMAL']).astype(np.float64) if 'NORMAL' in at else None
            # every other per-vertex attribute (the UV sets - a cloak's pattern and emblem UVs too -, colours)
            # rides along as one matrix: kept on the old points, averaged on the new
            lin = [k for k in sorted(at) if k not in ('POSITION', 'NORMAL', 'TANGENT', 'JOINTS_0', 'WEIGHTS_0')]
            cols = [G.read(at[k]).astype(np.float64).reshape(len(pos), -1) for k in lin]
            widths = [c.shape[1] for c in cols]
            uv = np.hstack(cols)
            jo = G.read(at['JOINTS_0']).astype(np.int64)
            we = G.read(at['WEIGHTS_0']).astype(np.float64)
            tg = [G.read(t['POSITION']).astype(np.float64) for t in prim.get('targets', [])]
            tris = G.read(prim['indices']).astype(np.int64).reshape(-1, 3)
            for _ in range(levels):
                pos, uv, jo, we, tg, tris, nrm = loop_once(pos, uv, jo, we, tg, tris, nrm, hard_cos, crease_cos)
            at['POSITION'] = G.write(pos, 5126, 'VEC3', 34962, minmax=True)
            at['NORMAL'] = G.write(nrm, 5126, 'VEC3', 34962)
            o = 0
            for k, wdt in zip(lin, widths):
                at[k] = G.write(uv[:, o:o + wdt], 5126, {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}[wdt], 34962)
                o += wdt
            at['JOINTS_0'] = G.write(jo, 5123, 'VEC4', 34962)
            at['WEIGHTS_0'] = G.write(we, 5126, 'VEC4', 34962)
            for t, d in zip(prim.get('targets', []), tg):
                t['POSITION'] = G.write(d, 5126, 'VEC3', 34962, minmax=True)
                t.pop('NORMAL', None)
            prim['indices'] = G.write(tris.reshape(-1), 5125, 'SCALAR', 34963)
            done += 1
        print(mesh['name'], len(tris), 'triangles')
    G.save(dst)
    print(done, 'primitives smoothed')


def main():
    levels = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 1
    hard = next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--hard=')), 60.0)
    crease = next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--crease=')), 70.0)
    smooth_file(sys.argv[1], sys.argv[2], levels, hard, crease)


if __name__ == '__main__':
    main()
