"""The neck (v2): the new head cut exactly along the classic head's lower edge (where the body begins) and joined to
it point for point - every classic edge point is a point of the new edge, so the two close without a gap."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from headio import boundary_loops
from fit2 import adjacency, vnormals


def classic_seam(cP, cT, cskin, grp):
    """The classic head's lower edge as an ordered ring: its points, their normals, the way up the skin from each."""
    Ts = cT[cskin[cT].all(1)]
    loops = boundary_loops(Ts, grp)
    Pg = np.zeros((grp.max() + 1, 3)); Pg[grp] = cP
    Lp = min(loops, key=lambda l: Pg[l][:, 2].mean())
    S = Pg[Lp]
    # normals (welded) and the direction into the skin, from the triangles on the edge
    Tg = grp[Ts]
    fn = np.cross(Pg[Tg[:, 1]] - Pg[Tg[:, 0]], Pg[Tg[:, 2]] - Pg[Tg[:, 0]])
    N = np.zeros_like(Pg); U = np.zeros_like(Pg)
    cen = Pg[Tg].mean(1)
    for k in range(3):
        np.add.at(N, Tg[:, k], fn)
        np.add.at(U, Tg[:, k], cen - Pg[Tg[:, k]])
    N = N[Lp] / np.maximum(np.linalg.norm(N[Lp], axis=1, keepdims=True), 1e-12)
    tan = np.roll(S, -1, 0) - np.roll(S, 1, 0)
    tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
    up = np.cross(N, tan)
    sgn = np.sign((up * U[Lp]).sum(1)); sgn[sgn == 0] = 1
    if np.median(sgn) < 0:
        up = -up
    up /= np.maximum(np.linalg.norm(up, axis=1, keepdims=True), 1e-12)
    return S, N, up, np.array(Lp)


class Seam:
    def __init__(self, S, N, up, n=24):
        self.S, self.N, self.up = S, N, up
        m = len(S)
        ts = np.arange(n) / n
        i0 = np.repeat(np.arange(m), n); i1 = (i0 + 1) % m; tt = np.tile(ts, m)
        self.Q = S[i0] * (1 - tt[:, None]) + S[i1] * tt[:, None]
        self.QU = up[i0] * (1 - tt[:, None]) + up[i1] * tt[:, None]
        self.QN = N[i0] * (1 - tt[:, None]) + N[i1] * tt[:, None]
        self.par = i0 + tt
        self.tree = cKDTree(self.Q)

    def locate(self, P):
        """Each point's nearest place on the ring's line: (segment, t along it, the place)."""
        _, j = self.tree.query(P)
        m = len(self.S)
        i0 = np.floor(self.par[j]).astype(int) % m
        best = None
        for di in (-1, 0, 1):
            i = (i0 + di) % m
            a, b = self.S[i], self.S[(i + 1) % m]
            ab = b - a
            t = np.clip(((P - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
            q = a + t[:, None] * ab
            d = np.linalg.norm(P - q, axis=1)
            if best is None:
                best = [i.copy(), t.copy(), q.copy(), d.copy()]
            else:
                k = d < best[3]
                best[0][k] = i[k]; best[1][k] = t[k]; best[2][k] = q[k]; best[3][k] = d[k]
        return best[0], best[1], best[2]

    def at(self, arr, i, t):
        """A per-ring-point array along the ring at (segment, t)."""
        return arr[i] * (1 - t)[:, None] + arr[(i + 1) % len(self.S)] * t[:, None]

    def f(self, P):
        """> 0: the head's side of the edge. (Anything higher than the edge's highest point is the head's: on the
        Dwarf, Lurikeen and Inconnu women the back of the skull lay nearest the back of the neck's edge, whose 'up'
        leans back, and came out below it - a hole cut in the back of the head.)"""
        d, j = self.tree.query(P)
        f = ((P - self.Q[j]) * self.QU[j]).sum(1)
        return np.maximum(f, P[:, 2] - self.S[:, 2].max()), d, j


def clip(P, T, f):
    """The triangles where f > 0, cut along f = 0. -> (combos [(a, b, t)], triangles): new point = P[a] + t (P[b] - P[a])."""
    comb = [(i, i, 0.0) for i in range(len(P))]
    edge = {}
    def cut(a, b):
        key = (a, b) if a < b else (b, a)
        if key not in edge:
            ta = f[key[0]] / (f[key[0]] - f[key[1]])
            edge[key] = len(comb); comb.append((key[0], key[1], float(np.clip(ta, 0.02, 0.98))))
        return edge[key]
    out = []
    for t in T:
        ins = f[t] > 0
        k = ins.sum()
        if k == 3:
            out.append(list(t))
        elif k == 0:
            continue
        else:
            for r in range(3):
                a, b, c = t[r], t[(r + 1) % 3], t[(r + 2) % 3]
                if k == 1 and f[a] > 0:
                    out.append([a, cut(a, b), cut(a, c)]); break
                if k == 2 and f[a] <= 0:
                    ab, ca = cut(a, b), cut(c, a)
                    out.append([ab, b, c]); out.append([ab, c, ca]); break
    return comb, np.array(out, np.int64)


def main_component(T, n, seed):
    A = coo_matrix((np.ones(len(T) * 3), (T.ravel(), np.roll(T, 1, 1).ravel())), shape=(n, n))
    _, lab = connected_components(A, directed=False)
    return lab[T[:, 0]] == lab[seed]


