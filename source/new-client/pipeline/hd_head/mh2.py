"""MakeHuman's whole head (CC0): the skin with its own eyeballs, lashes, teeth and tongue - each a 'proxy' bound to
the base mesh (.mhclo), so every target moves them with the skin. Figure axes (z up, the face toward -y)."""
import os, numpy as np
from pathlib import Path
from mhbase import read_obj, read_target, TO_FIG, MH, tris

SYS = str(Path(__file__).parent / 'mh_sys') if (Path(__file__).parent / 'mh_sys').exists() else '/home/claude/mh/sys'
PROXIES = {'eyes': 'eyes/low-poly/low-poly', 'teeth': 'teeth/teeth_base/teeth_base', 'tongue': 'tongue/tongue01/tongue01',
           'lash': 'eyelashes/eyelashes01/eyelashes01'}
_BASE = None


def base():
    global _BASE
    if _BASE is None:
        _BASE = read_obj()
    return _BASE


class Proxy:
    """A .mhclo: each of its points on three base points (weights, an offset scaled with the base's size)."""
    def __init__(self, rel, root=None):
        root = root or SYS
        path = os.path.join(root, rel + '.mhclo')
        self.scale = {}
        rows, on = [], False
        for line in open(path, encoding='utf-8', errors='replace'):
            a = line.split()
            if not a or a[0].startswith('#'):
                continue
            if a[0] in ('x_scale', 'y_scale', 'z_scale'):
                self.scale[a[0][0]] = (int(a[1]), int(a[2]), float(a[3]))
            elif a[0] == 'verts':
                on = True
            elif on:
                try:
                    nums = [float(x) for x in a]
                except ValueError:
                    on = False
                    continue
                if len(nums) == 1:
                    rows.append([nums[0], nums[0], nums[0], 1, 0, 0, 0, 0, 0])
                elif len(nums) == 9:
                    rows.append(nums)
                else:
                    on = False
        r = np.array(rows)
        self.idx = r[:, :3].astype(np.int64); self.w = r[:, 3:6]; self.off = r[:, 6:9]
        V, VT, F, FT, FG = read_obj(os.path.join(root, rel + '.obj'))
        assert len(V) == len(r), (rel, len(V), len(r))
        self.T, self.TT = tris(F, FT)
        self.VT = VT
        self.F, self.FT = F, FT

    def at(self, V):
        """Its points for the base points V (MakeHuman axes)."""
        s = np.ones(3)
        for k, ax in (('x', 0), ('y', 1), ('z', 2)):
            if k in self.scale:
                a, b, den = self.scale[k]
                s[ax] = abs(V[a, ax] - V[b, ax]) / den
        return (V[self.idx] * self.w[:, :, None]).sum(1) + self.off * s


def group_verts(gn):
    V, VT, F, FT, FG = base()
    ks = [k for k, g in enumerate(FG) if g == gn]
    return np.unique(np.concatenate([F[k] for k in ks]))


def macro(sex):
    V = base()[0].copy()
    i, d = read_target(f'macrodetails/caucasian-{sex}-young.target')
    V[i] += d
    return V


def catmull_clark(W, quads):
    """One round of Catmull-Clark on a quad mesh whose points are rows of W (each a mix of base points). -> (W, quads).
    Linear in the base points: a target's move of the base carries straight through."""
    from collections import defaultdict
    n = len(W)
    quads = [list(q) for q in quads]
    fp = np.array([W[q].mean(0) for q in quads])
    ef = defaultdict(list)
    for fi, q in enumerate(quads):
        for i in range(4):
            a, b = q[i], q[(i + 1) % 4]
            ef[(min(a, b), max(a, b))].append(fi)
    eidx = {e: i for i, e in enumerate(ef)}
    ep = np.zeros((len(ef), W.shape[1]))
    vf = defaultdict(list); ve = defaultdict(list); vb = defaultdict(list)
    for fi, q in enumerate(quads):
        for v in q:
            vf[v].append(fi)
    for e, fs in ef.items():
        mid = (W[e[0]] + W[e[1]]) / 2
        if len(fs) == 2:
            ep[eidx[e]] = (W[e[0]] + W[e[1]] + fp[fs[0]] + fp[fs[1]]) / 4
        else:
            ep[eidx[e]] = mid
            vb[e[0]].append(e[1]); vb[e[1]].append(e[0])
        ve[e[0]].append(mid); ve[e[1]].append(mid)
    vp = np.zeros_like(W)
    for v in range(n):
        if v in vb and len(vb[v]) == 2:
            vp[v] = (W[vb[v][0]] + 6 * W[v] + W[vb[v][1]]) / 8
        elif v in vf:
            k = len(vf[v])
            Fm = fp[vf[v]].mean(0); Rm = np.mean(ve[v], axis=0)
            vp[v] = (Fm + 2 * Rm + (k - 3) * W[v]) / k
        else:
            vp[v] = W[v]
    nf = len(quads)
    Wn = np.r_[vp, fp, ep]
    out = []
    for fi, q in enumerate(quads):
        for i in range(4):
            a, b, p = q[i], q[(i + 1) % 4], q[(i - 1) % 4]
            out.append([a, n + nf + eidx[(min(a, b), max(a, b))], n + fi, n + nf + eidx[(min(a, p), max(a, p))]])
    return Wn, out


class SmoothEyes:
    """The eyeballs: MakeHuman's own helper eyes (the very points its targets move with the lids), rounded off by two
    rounds of subdivision."""
    def __init__(self, rounds=2):
        px = Proxy(PROXIES['eyes'])
        self.base_idx = px.idx[:, 0]
        W = np.eye(len(self.base_idx)); quads = px.F
        uv = np.zeros((len(self.base_idx), 2))
        for f, ft in zip(px.F, px.FT):
            for a, b in zip(f, ft):
                uv[a] = px.VT[b]
        for _ in range(rounds):
            W, quads = catmull_clark(W, quads)
        self.W = W
        self.UV = W @ uv
        q = np.array(quads)
        self.T = np.r_[q[:, [0, 1, 2]], q[:, [0, 2, 3]]]

        self.k = None

    def at(self, V):
        """Its points for the base points V. The first call (the rest shape) sets each point out onto the helper eye's
        own sphere (subdivision alone shrinks it off the lids); after that every point moves as the helper's points
        under it do, by the same measure."""
        from landmarks import sphere_fit
        H = V[self.base_idx]
        X = self.W @ H
        if self.k is None:
            self.k = np.ones(len(X)); self.c0 = np.zeros_like(X); self.X0 = X.copy()
            for sel, hs in ((X[:, 0] > 0, H[:, 0] > 0), (X[:, 0] <= 0, H[:, 0] <= 0)):
                c, r = sphere_fit(H[hs])
                self.k[sel] = r / np.linalg.norm(X[sel] - c, axis=1)
                self.c0[sel] = c
        return self.c0 + (self.X0 - self.c0) * self.k[:, None] + (X - self.X0) * self.k[:, None]
