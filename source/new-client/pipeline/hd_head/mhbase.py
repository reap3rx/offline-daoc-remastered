"""The MakeHuman (CC0) base mesh: read base.obj (groups, quads), its targets; figure axes (z up, faces -y)."""
import numpy as np, os
from pathlib import Path as _P
MH = str(_P(__file__).parent / 'makehuman') if (_P(__file__).parent / 'makehuman').exists() else '/home/claude/mh/mhsrc/makehuman/data'
TO_FIG = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])     # MH (y up, faces +z) -> figure (z up, faces -y)

def read_obj(path=MH + '/3dobjs/base.obj'):
    V, VT, F, FT, FG = [], [], [], [], []
    g = ''
    for line in open(path):
        if line.startswith('v '):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith('vt '):
            VT.append([float(x) for x in line.split()[1:3]])
        elif line.startswith('g '):
            g = line.split()[1]
        elif line.startswith('f '):
            parts = [p.split('/') for p in line.split()[1:]]
            F.append([int(p[0]) - 1 for p in parts])
            FT.append([int(p[1]) - 1 if len(p) > 1 and p[1] else -1 for p in parts])
            FG.append(g)
    return np.array(V), np.array(VT), F, FT, FG

def read_target(rel):
    """{vertex index: delta} as (idx array, (n,3) deltas), MH axes."""
    idx, d = [], []
    for line in open(os.path.join(MH, 'targets', rel)):
        if not line.strip() or line.startswith('#'):
            continue
        a = line.split()
        idx.append(int(a[0])); d.append([float(a[1]), float(a[2]), float(a[3])])
    return np.array(idx, np.int64), np.array(d)

def apply_target(V, rel, w=1.0):
    i, d = read_target(rel)
    V = V.copy()
    if len(i):
        V[i] += w * d
    return V

def tris(F, FT=None, keep=None):
    T, TT = [], []
    for k, f in enumerate(F):
        if keep is not None and not keep[k]:
            continue
        for j in range(1, len(f) - 1):
            T.append([f[0], f[j], f[j + 1]])
            if FT is not None:
                TT.append([FT[k][0], FT[k][j], FT[k][j + 1]])
    return np.array(T, np.int64), (np.array(TT, np.int64) if FT is not None else None)
