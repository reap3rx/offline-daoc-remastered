"""Upscale fig3 textures with a spandrel model: python upscale.py <model.pth> <in dir> <out dir> key1 key2 ...
(keys are file stems, any case). RGBA: the alpha upscaled on its own (as RGB) and put back."""
import sys, torch, numpy as np
from pathlib import Path
from PIL import Image
from spandrel import ModelLoader
model = ModelLoader().load_from_file(sys.argv[1]).cuda().eval()
src, dst = Path(sys.argv[2]), Path(sys.argv[3]); dst.mkdir(parents=True, exist_ok=True)
files = {p.stem.lower(): p for p in src.glob('*.png')}
def run(rgb):
    t = torch.from_numpy(rgb).permute(2, 0, 1)[None].float().cuda() / 255.0
    with torch.no_grad():
        o = model(t)
    return (o[0].permute(1, 2, 0).clamp(0, 1).cpu().numpy() * 255 + 0.5).astype(np.uint8)
for k in sys.argv[4:]:
    p = files.get(k.lower())
    if not p: print('missing', k); continue
    im = Image.open(p)
    a = np.asarray(im.convert('RGBA'))
    rgb = run(np.ascontiguousarray(a[..., :3]))
    if im.mode in ('RGBA', 'LA') or 'transparency' in im.info:
        al = run(np.ascontiguousarray(np.repeat(a[..., 3:4], 3, axis=2)))[..., 0]
        out = Image.fromarray(np.dstack([rgb, al]), 'RGBA')
    else:
        out = Image.fromarray(rgb, 'RGB')
    out.save(dst / p.name)
    print('done', p.name, out.size)
