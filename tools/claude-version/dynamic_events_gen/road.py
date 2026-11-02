import heapq, math
STEP = 8.0

def depth(t, x, y):
    if t.water is None: return 0
    m = t.water.shape[0]
    i = int(t.water[min(max(int(y / t.size * m), 0), m - 1), min(max(int(x / t.size * m), 0), m - 1)])
    lv = t.levels.get(i)
    return 0 if lv is None else max(0.0, lv - t.z(x, y))

def astar(t, a, b, avoid=None, margin=300, maxgrade=0.6):
    x0 = max(60, min(a[0], b[0]) - margin); x1 = min(t.size - 60, max(a[0], b[0]) + margin)
    y0 = max(60, min(a[1], b[1]) - margin); y1 = min(t.size - 60, max(a[1], b[1]) + margin)
    nx = int((x1 - x0) / STEP) + 1; ny = int((y1 - y0) / STEP) + 1
    def P(i, j): return (x0 + i * STEP, y0 + j * STEP)
    def node(p): return (min(max(int(round((p[0] - x0) / STEP)), 0), nx - 1), min(max(int(round((p[1] - y0) / STEP)), 0), ny - 1))
    zc = {}; dc = {}
    def Z(n):
        if n not in zc:
            p = P(*n); zc[n] = t.z(*p); dc[n] = depth(t, *p)
        return zc[n]
    s, g = node(a), node(b)
    openq = [(0, s)]; came = {s: None}; cost = {s: 0}
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    while openq:
        _, n = heapq.heappop(openq)
        if n == g: break
        zn = Z(n)
        for di, dj in nb:
            m = (n[0] + di, n[1] + dj)
            if not (0 <= m[0] < nx and 0 <= m[1] < ny): continue
            L = STEP * math.hypot(di, dj)
            zm = Z(m)
            if abs(zm - zn) / L > maxgrade: continue
            d = dc[m]
            if d > 1.3: continue                      # deep water: no
            c = L * (1 + (4 if d > 0.05 else 0) + abs(zm - zn) / L * 2)
            if avoid and avoid(P(*m)): c += L * 3
            nc = cost[n] + c
            if nc < cost.get(m, 1e18):
                cost[m] = nc; came[m] = n
                heapq.heappush(openq, (nc + STEP * math.hypot(g[0] - m[0], g[1] - m[1]), m))
    if g not in came: return None
    path = []; n = g
    while n is not None: path.append(P(*n)); n = came[n]
    return path[::-1]

def simplify(t, pts, every=100):
    # keep points roughly every `every` m along the way, plus the turns
    out = [pts[0]]; run = 0
    for i in range(1, len(pts)):
        run += math.dist(pts[i - 1], pts[i])
        turn = False
        if 0 < i < len(pts) - 1:
            a = math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0]); b = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
            turn = abs((b - a + math.pi) % (2 * math.pi) - math.pi) > 0.5 and run > 30
        if run >= every or turn or i == len(pts) - 1:
            out.append(pts[i]); run = 0
    return out
