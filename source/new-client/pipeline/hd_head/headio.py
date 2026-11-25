"""Shared helpers for the HD head work: read a race figure's classic head, its skeleton, its UVs."""
import sys, json, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__)); sys.path.insert(1, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
import face_morphs as fm
from face_morphs import G, weld
fm.NC.setdefault('MAT4', 16)

def race_path(r):
    return f'/mnt/user-data/uploads/Offline DAOC 036c/claude-work/backup-body-shapes-20261125/races/{r}/figure.gltf'

def load_head(g):
    gg = g.g
    node = next(n for n in gg['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    prim = gg['meshes'][node['mesh']]['primitives'][0]
    a = prim['attributes']
    P = g.acc(a['POSITION']).astype(np.float64)
    UV = g.acc(a['TEXCOORD_0']).astype(np.float64)
    T = g.acc(prim['indices']).astype(np.int64).reshape(-1, 3)
    J = g.acc(a['JOINTS_0']).astype(np.int64)
    W = g.acc(a['WEIGHTS_0']).astype(np.float64)
    tg = [g.acc(t['POSITION']).astype(np.float64) for t in prim.get('targets', [])]
    names = gg['meshes'][node['mesh']].get('extras', {}).get('targetNames', [])
    return dict(P=P, UV=UV, T=T, J=J, W=W, targets=dict(zip(names, tg)), node=node, prim=prim)

def bones(g):
    s = g.g['skins'][0]
    N = g.g['nodes']
    names = [N[j].get('name', '') for j in s['joints']]
    ibm = g.acc(s['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)
    bind = np.linalg.inv(ibm)
    return {n: bind[i] for i, n in enumerate(names)}, names

def boundary_loops(T, grp):
    """Open edges (by welded position group) chained into loops of group ids."""
    from collections import defaultdict
    E = defaultdict(int)
    for t in grp[T]:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            E[(min(a, b), max(a, b))] += 1
    nb = defaultdict(list)
    for (a, b), c in E.items():
        if c == 1:
            nb[a].append(b); nb[b].append(a)
    seen, loops = set(), []
    for s0 in list(nb):
        if s0 in seen: continue
        loop = [s0]; seen.add(s0); prev = None; cur = s0
        while True:
            nxt = [x for x in nb[cur] if x != prev and x not in seen]
            if not nxt: break
            prev, cur = cur, nxt[0]; loop.append(cur); seen.add(cur)
        loops.append(loop)
    return loops
