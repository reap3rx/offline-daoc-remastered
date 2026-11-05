"""Upscale fig3 textures with a spandrel model on the GPU (claude 2026-11-05: the character remaster, 4x-UltraSharp).
    python upscale_spandrel.py <model.pth> <in dir> <out dir> key1 key2 ...   (file stems, any case)
    python upscale_spandrel.py <model.pth> <in dir> <out dir> --all            (every png; ones already done skipped)
RGBA: the alpha upscaled on its own (as RGB) and put back. Big textures go through in tiles."""
import sys, torch, numpy as np
from pathlib import Path
from PIL import Image
from spandrel import ModelLoader
model = ModelLoader().load_from_file(sys.argv[1]).cuda().eval().half()
src, dst = Path(sys.argv[2]), Path(sys.argv[3]); dst.mkdir(parents=True, exist_ok=True)
files = {p.stem.lower(): p for p in src.glob('*.png')}
TILE, PAD, S = 512, 16, 4

def run(rgb):
    h, w = rgb.shape[:2]
    out = np.zeros((h * S, w * S, 3), np.uint8)
    for y in range(0, h, TILE):
        for x in range(0, w, TILE):
            y0, x0 = max(0, y - PAD), max(0, x - PAD)
            y1, x1 = min(h, y + TILE + PAD), min(w, x + TILE + PAD)
            t = torch.from_numpy(np.ascontiguousarray(rgb[y0:y1, x0:x1])).permute(2, 0, 1)[None].half().cuda() / 255.0
            with torch.no_grad():
                o = model(t)[0].permute(1, 2, 0).float().clamp(0, 1).cpu().numpy()
            o = (o * 255 + 0.5).astype(np.uint8)
            ty, tx = (y - y0) * S, (x - x0) * S
            hh, ww = min(TILE, h - y) * S, min(TILE, w - x) * S
            out[y * S:y * S + hh, x * S:x * S + ww] = o[ty:ty + hh, tx:tx + ww]
    return out

keys = list(files) if sys.argv[4:] == ['--all'] else [k.lower() for k in sys.argv[4:]]
done = 0
for k in keys:
    p = files.get(k)
    if not p:
        print('missing', k); continue
    if sys.argv[4:] == ['--all'] and (dst / p.name).exists():
        continue
    im = Image.open(p)
    a = np.asarray(im.convert('RGBA'))
    rgb = run(a[..., :3])
    if im.mode in ('RGBA', 'LA', 'P') and (a[..., 3] < 255).any():
        al = run(np.repeat(a[..., 3:4], 3, axis=2))[..., 0]
        out = Image.fromarray(np.dstack([rgb, al]), 'RGBA')
    else:
        out = Image.fromarray(rgb, 'RGB')
    out.save(dst / p.name)
    done += 1
    if done % 50 == 0:
        print('done', done, flush=True)
print('finished', done)
