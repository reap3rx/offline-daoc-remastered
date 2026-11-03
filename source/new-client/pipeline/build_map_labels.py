"""The painted maps' lettering and markers on their own (owner 2026-11-02: "making the maps more high-rez").

The zones drawn from above (godot/tests/map_render.gd -> content/maps/render/z<zone>.jpg) are sharp but carry no
names. The client's painted maps carry the names - white letters with a black edge - and the white markers (towers,
camps, dungeon doors) and yellow arrows to the next zones. This lifts those out of each painted map (content/maps/
x4plus/z<zone>.png, the same square as the render) into a see-through layer the map and minimap draw over the render:

    content/maps/render/z<zone>_labels.png      RGBA, the painted map's size
    content/maps/render/z<zone>_labels.json     {"size": n, "boxes": [[x, y, w, h], ...]} - each name or marker's box,
                                                so the map can draw them at one size whatever its zoom

    python build_map_labels.py [zone ...]       (default: every zone with a render)
"""
import json, sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from assets_pipeline import ROOT

MAPS = ROOT / 'godot/content/maps'


def labels(painted: Path) -> Image.Image:
    im = np.asarray(Image.open(painted).convert('RGB')).astype(np.int16)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mn = im.min(axis=2)
    mx = im.max(axis=2)
    white = (mn > 165) & ((mx - mn) < 60)                    # the letters and the markers
    yellow = (r > 170) & (g > 140) & (b < 120) & (r - b > 80)  # the arrows to the next zones
    ink = white | yellow
    near = np.asarray(Image.fromarray((ink * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) > 0
    edge = near & (mx < 70)                                   # their black edge
    alpha = np.where(ink, 255, np.where(edge, 230, 0)).astype(np.uint8)
    return Image.fromarray(np.dstack([im.astype(np.uint8), alpha]), 'RGBA')


def boxes(lab: Image.Image) -> list:
    a = np.asarray(lab)[..., 3] > 0
    joined = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0   # a word's letters
    parts, n = ndimage.label(joined)
    out = []
    for sl in ndimage.find_objects(parts):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if (x1 - x0) * (y1 - y0) < 40:
            continue                                              # specks
        out.append([int(x0), int(y0), int(x1 - x0), int(y1 - y0)])
    return out


def main():
    zones = [int(a) for a in sys.argv[1:] if a.isdigit()]
    if not zones:
        zones = sorted(int(p.stem[1:4]) for p in (MAPS / 'render').glob('z[0-9][0-9][0-9].jpg'))
    info = json.loads((MAPS / 'maps.json').read_text()).get('zones', {})
    for z in zones:
        name = info.get(str(z), {}).get('map', '') or ('z%03d.png' % z)
        painted = MAPS / 'x4plus' / name
        if not painted.exists():
            painted = MAPS / 'original' / name
        if not painted.exists():
            print(z, 'no painted map')
            continue
        out = MAPS / 'render' / ('z%03d_labels.png' % z)
        lab = labels(painted)
        lab.save(out)
        b = boxes(lab)
        (MAPS / 'render' / ('z%03d_labels.json' % z)).write_text(json.dumps({"size": lab.size[0], "boxes": b}))
        print(z, out.name, len(b), 'labels')


if __name__ == '__main__':
    main()
