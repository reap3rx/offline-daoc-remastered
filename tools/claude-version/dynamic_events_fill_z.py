"""Fills in the ground height (metres) of every point of a zone's dynamic-event file from the new client's height
grid, so the server knows where the ground is before its navmesh snaps a spawn to it.

  python tools\\claude-version\\dynamic_events_fill_z.py source\\server\\GameServer\\scripts\\dynamicevents\\zones\\zone206_valley_of_bri_leith.json

Points are [x, y] or [x, y, z] in zone metres (the client's units: 1 m = 40 server units); z is (re)written.
"""
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def heights(zone, root):
    d = root / ('new-client/godot/content/zones/zone%03d' % zone)
    info = json.loads((d / 'zone.json').read_text(encoding='utf-8'))
    hs = info['heights_size']
    raw = (d / info['heights']).read_bytes()
    h = struct.unpack('<%df' % (hs * hs), raw[:hs * hs * 4])
    size = info['size_m']

    def at(x, y):
        gx = min(max(x / size * (hs - 1), 0), hs - 1.001)
        gy = min(max(y / size * (hs - 1), 0), hs - 1.001)
        ix, iy = int(gx), int(gy)
        fx, fy = gx - ix, gy - iy
        top = h[iy * hs + ix] * (1 - fx) + h[iy * hs + ix + 1] * fx
        bot = h[(iy + 1) * hs + ix] * (1 - fx) + h[(iy + 1) * hs + ix + 1] * fx
        return round(top * (1 - fy) + bot * fy, 1)
    return at


def walk(o, at):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('center', 'pos') and isinstance(v, list) and len(v) in (2, 3):
                o[k] = [v[0], v[1], at(v[0], v[1])]
            elif k == 'from':
                o[k] = [[p[0], p[1], at(p[0], p[1])] for p in v]
            else:
                walk(v, at)
    elif isinstance(o, list):
        for v in o:
            walk(v, at)


def main():
    path = Path(sys.argv[1])
    root = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT
    doc = json.loads(path.read_text(encoding='utf-8'))
    walk(doc, heights(doc['zone'], root))
    text = json.dumps(doc, indent=2, ensure_ascii=False)
    # short lists of numbers (points, level ranges) and small objects (mob entries) on one line
    text = re.sub(r'\[\s*(-?[\d.]+(?:,\s*-?[\d.]+)*)\s*\]', lambda m: '[' + re.sub(r'\s+', ' ', m.group(1)) + ']', text)
    text = re.sub(r'\{[^{}\[\]]{0,160}\}', lambda m: re.sub(r'\s*\n\s*', ' ', m.group(0)), text)
    path.write_text(text + '\n', encoding='utf-8')
    print('filled', path)


if __name__ == '__main__':
    main()
