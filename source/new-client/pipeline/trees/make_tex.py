# Leaf and bark textures for the new trees, cut from the original Hibernian tree atlases (x4plus upscales):
# leaf cards stand on their stem (bottom centre), bark tiles vertically.
from PIL import Image, ImageFilter
import sys
R = (sys.argv[1] if len(sys.argv) > 1 else "ref").rstrip("/") + "/"   # the original tree textures (a zone's textures/x4plus)
O = "/home/claude/trees/web/tex/"
def im(n):
    i = Image.open(R + n).convert("RGBA"); r, g, b, a = i.split()
    return Image.merge("RGBA", (r, g, b, a.point(lambda v: 0 if v < 110 else min(255, int((v - 110) * 1.8)))))
def fit(img, size=512):
    w, h = img.size; s = size / max(w, h)
    img = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(img, ((size - img.size[0]) // 2, size - img.size[1])); return out
def bleed(img):
    # colour the clear pixels with nearby leaf colour so mipmaps don't fringe pink/black
    a = img.split()[3]; rgb = img.convert("RGB")
    blur = rgb.filter(ImageFilter.GaussianBlur(8)); base = Image.new("RGB", img.size, tuple(int(c) for c in rgb.resize((1, 1), Image.BOX).getpixel((0, 0))))
    filled = Image.composite(rgb, blur, a.point(lambda v: 255 if v > 8 else 0))
    out = filled.copy(); out.putalpha(a); return out
# elm: the helm spray, its base turned to the bottom
elm = im("helm1n.png").crop((60, 0, 512, 512)).rotate(-90 + 40, expand=True, resample=Image.BICUBIC)
bleed(fit(elm.crop(elm.getbbox()))).save(O + "leaf_elm.png")
# oak: the left spray of the oak atlas (base already at the bottom right) -> stand it up
oak = im("helm2n.png").crop((60, 0, 512, 512)).rotate(-90 + 40, expand=True, resample=Image.BICUBIC)
bleed(fit(oak.crop(oak.getbbox()))).save(O + "leaf_oak.png")
# birch: the leaf cluster, split into two rounder clumps
b = im("hbirchtreen.png").crop((0, 0, 410, 512))
bleed(fit(b.crop((0, 0, 410, 300)))).save(O + "leaf_birch.png")
# pine: half the grove tree's needle spray, base (the right edge) turned down
p = im("holdgrove.png").crop((0, 0, 400, 400)).rotate(-90, expand=True, resample=Image.BICUBIC)
p = fit(p.crop(p.getbbox()))
# (owner 2026-11-17: the pine cards showed as squares up close - the spray's base is a solid mass to the card's edge)
# a ragged spray shape from the stem, and gaps through the mass, so no card edge shows
import numpy as np
pa = np.asarray(p).astype(np.float32); H, W = pa.shape[:2]
yy, xx = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
rng = np.random.default_rng(3)
def nz(n): return np.asarray(Image.fromarray((rng.random((n, n)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
d = np.sqrt(((xx - 0.5) / 0.48) ** 2 + ((yy - 0.55) / 0.5) ** 2) + (nz(24) - 0.5) * 0.4
pa[..., 3] *= np.clip((1.0 - d) / 0.15, 0, 1) * np.clip((nz(48) - 0.22) / 0.1, 0, 1)
bleed(Image.fromarray(pa.clip(0, 255).astype(np.uint8), "RGBA")).save(O + "leaf_pine.png")
# dead twigs: the dead tree's bare spray
d = im("hdeadtree.png"); d = d.crop(d.getbbox())
bleed(fit(d.crop((0, 0, d.size[0] // 2, d.size[1])))).save(O + "leaf_dead.png")
# barks
im("holdgrove.png").crop((512, 0, 1024, 1024)).convert("RGB").resize((256, 512), Image.LANCZOS).save(O + "bark_pine.png")
im("hbirchtreen.png").crop((412, 0, 512, 512)).convert("RGB").resize((128, 512), Image.LANCZOS).save(O + "bark_birch.png")
im("hbaresknyn.png").crop((0, 0, 70, 1024)).convert("RGB").resize((128, 512), Image.LANCZOS).save(O + "bark_moss.png")
print("ok")
