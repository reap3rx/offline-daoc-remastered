# Leaf cards and bark for every tree the game has (TreeSwap, all zones; claude 2026-11-17), cut from each original's own
# texture atlas (the x4plus upscale where there is one): the bark is the atlas's tallest fully opaque strip, the leaf
# card the rest of the atlas (or a box given below), stood on its stem and given a ragged spray outline so no card edge
# shows (owner: square pine cards). Output: web/tex/leaf_<atlas>.png, bark_<atlas>.png; a contact sheet to check.
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
S = sys.argv[1] if len(sys.argv) > 1 else "src_all"
O = "web/tex/"
# per atlas: leaf box / bark box as fractions of the atlas (x0, y0, x1, y1), rot (degrees, the stem to the bottom),
# dense (a solid mass of needles: holes through it), bark=None (no strip in it: use the family's)
OV = json.load(open("tex_overrides.json")) if os.path.exists("tex_overrides.json") else {}
def load(n):
    p = f"{S}/x4_{n}.png" if os.path.exists(f"{S}/x4_{n}.png") else f"{S}/{n}.png"
    i = Image.open(p).convert("RGBA"); r, g, b, a = i.split()
    return Image.merge("RGBA", (r, g, b, a.point(lambda v: 0 if v < 110 else min(255, int((v - 110) * 1.8)))))
def largest_strip(a):
    # the largest fully opaque rectangle at least 2.5x taller than wide (a bark strip), on a 128 grid
    H, W = a.shape; g = 128; sm = np.asarray(Image.fromarray(a).resize((g, g), Image.BOX)) > 245
    best = (0, None); hts = np.zeros(g, int)
    for y in range(g):
        hts = np.where(sm[y], hts + 1, 0)
        for x0 in range(g):
            if hts[x0] == 0: continue
            h = hts[x0]
            for x1 in range(x0, g):
                h = min(h, hts[x1])
                if h == 0: break
                w = x1 - x0 + 1
                if h >= 2.5 * w and h * w > best[0]:
                    best = (h * w, (x0 / g, (y - h + 1) / g, (x1 + 1) / g, (y + 1) / g))
    return best[1] if best[0] >= g * g * 0.02 else None
def ragged(img, dense, seed):
    a = np.asarray(img).astype(np.float32); H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
    rng = np.random.default_rng(seed)
    def nz(n): return np.asarray(Image.fromarray((rng.random((n, n)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    d = np.sqrt(((xx - 0.5) / 0.5) ** 2 + ((yy - 0.52) / 0.52) ** 2) + (nz(24) - 0.5) * 0.4
    m = np.clip((1.0 - d) / 0.15, 0, 1)
    if dense:
        m *= np.clip((nz(48) - 0.22) / 0.1, 0, 1)
    a[..., 3] *= m
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
def fit(img, size=512):
    bb = img.getbbox()
    if bb: img = img.crop(bb)
    w, h = img.size; s = size / max(w, h)
    img = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(img, ((size - img.size[0]) // 2, size - img.size[1])); return out
def bleed(img):
    arr = np.asarray(img).astype(np.float32); a = arr[..., 3]; have = (a > 8).astype(np.float32); rgb = arr[..., :3].copy()
    for r in (2, 6, 16, 48):
        num = np.stack([np.asarray(Image.fromarray((rgb[..., k] * have).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) for k in range(3)], -1)
        den = np.asarray(Image.fromarray((have * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)[..., None] / 255
        fill = num / np.maximum(den, 1e-3); new = (have < 0.5) & (den[..., 0] > 0.02); rgb[new] = fill[new]; have[new] = 1
    return Image.fromarray(np.dstack([rgb.clip(0, 255), a]).astype(np.uint8), "RGBA")
def box(img, f):
    W, H = img.size; return img.crop((int(f[0] * W), int(f[1] * H), int(f[2] * W), int(f[3] * H)))
atlases = sys.argv[2].split(",")
report = {}
for n in atlases:
    ov = OV.get(n, {}); im = load(n); W, H = im.size; a = np.asarray(im)[..., 3]
    bark_box = ov.get("bark_box") if "bark_box" in ov else largest_strip(a)
    if bark_box:
        bk = box(im, bark_box).convert("RGB")
        bk = bk.resize((128, 512), Image.LANCZOS) if bk.size[1] >= bk.size[0] else bk.rotate(90, expand=True).resize((128, 512), Image.LANCZOS)
        bk.save(O + f"bark_{n}.png")
    leaf = im.copy()
    if bark_box and "leaf_box" not in ov:
        d = ImageDraw.Draw(leaf); W2, H2 = leaf.size
        d.rectangle([bark_box[0] * W2 - 2, bark_box[1] * H2 - 2, bark_box[2] * W2 + 2, bark_box[3] * H2 + 2], fill=(0, 0, 0, 0))
    if "leaf_box" in ov: leaf = box(leaf, ov["leaf_box"])
    if ov.get("rot"): leaf = leaf.rotate(ov["rot"], expand=True, resample=Image.BICUBIC)
    leaf = fit(leaf)
    if not ov.get("no_ragged"):
        leaf = ragged(leaf, ov.get("dense", False), sum(map(ord, n)))
    bleed(leaf).save(O + f"leaf_{n}.png")
    report[n] = {"bark_box": bark_box, "size": [W, H]}
json.dump(report, open("out/tex2_report.json", "w"), indent=0)
# contact sheet: the atlas with the bark box, the leaf card, the bark
s = 180; sheet = Image.new("RGB", (s * 3 * 4, (len(atlases) + 3) // 4 * (s + 14)), "white"); dr = ImageDraw.Draw(sheet)
for i, n in enumerate(atlases):
    x = (i % 4) * s * 3; y = (i // 4) * (s + 14)
    def mag(p):
        im = Image.open(p).convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 0, 255, 255)); bg.alpha_composite(im); return bg.convert("RGB")
    at = mag(f"{S}/{n}.png").resize((s, s)); d2 = ImageDraw.Draw(at); bb = report[n]["bark_box"]
    if bb: d2.rectangle([bb[0] * s, bb[1] * s, bb[2] * s, bb[3] * s], outline=(0, 255, 255), width=2)
    sheet.paste(at, (x, y + 14)); sheet.paste(mag(O + f"leaf_{n}.png").resize((s, s)), (x + s, y + 14))
    if os.path.exists(O + f"bark_{n}.png"): sheet.paste(Image.open(O + f"bark_{n}.png").convert("RGB").resize((s // 4, s)), (x + 2 * s + 4, y + 14))
    dr.text((x + 2, y + 1), n, fill="black")
sheet.save("out/tex2_sheet.jpg", quality=85)
print("ok", len(atlases))
