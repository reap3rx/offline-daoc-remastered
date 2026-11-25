"""Make geo grid<zone>.bin (410x410 cells at 4 m: height, water level or -1) from the client's zone folder."""
import json, struct, sys, os
from PIL import Image
src, zid, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = json.load(open(os.path.join(src, 'zone.json')))
b = open(os.path.join(src, 'heights_2x.f32'), 'rb').read(); n = int((len(b) / 4) ** .5)
H = struct.unpack('<%df' % (n * n), b); size = d['size_m']; c = size / (n - 1)
def h(x, y):
    fx, fy = min(max(x / c, 0), n - 1.001), min(max(y / c, 0), n - 1.001); i, j = int(fx), int(fy); ax, ay = fx - i, fy - j
    v = lambda a, bb: H[bb * n + a]
    return (v(i, j) * (1 - ax) + v(i + 1, j) * ax) * (1 - ay) + (v(i, j + 1) * (1 - ax) + v(i + 1, j + 1) * ax) * ay
ws = d.get('water') or []
levels = sorted({float(w['height']) for w in ws if isinstance(w, dict) and 'height' in w})
lvl = levels[-1] if levels else None
def level_for(g):
    # several bodies at different heights (ponds, a moat, lava): the lowest surface above this ground
    above = [L for L in levels if L > g - 0.5]
    return above[0] if above else levels[-1]
im = None
if os.path.exists(os.path.join(src, 'water.png')):
    im = Image.open(os.path.join(src, 'water.png')).convert('L')
N = 410; vals = []
for j in range(N):
    for i in range(N):
        x, y = i * 4.0, j * 4.0
        hh = h(x, y)
        wl = -1.0
        if im is not None and lvl is not None:
            px = min(int(x / size * im.size[0]), im.size[0] - 1); py = min(int(y / size * im.size[1]), im.size[1] - 1)
            if im.getpixel((px, py)) < 128:
                wl = float(level_for(hh))
        vals += [hh, wl]
open(out, 'wb').write(struct.pack('<%df' % len(vals), *vals))
print(zid, 'water levels', levels)
