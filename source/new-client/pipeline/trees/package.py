# content/trees for the game (TreeSwap): trees.json, each variant's .glb, the species' far-card atlases, the textures.
import json, os, shutil, sys
from PIL import Image
src = sys.argv[1]; dst = sys.argv[2]
import numpy as np
from PIL import ImageFilter
def bleed(img):
    arr = np.asarray(img).astype(np.float32); a = arr[..., 3]; m = (a > 8).astype(np.float32)
    rgb = arr[..., :3].copy(); have = m.copy()
    for r in (2, 6, 16, 48):
        num = np.stack([np.asarray(Image.fromarray((rgb[..., k] * have).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) for k in range(3)], -1)
        den = np.asarray(Image.fromarray((have * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)[..., None] / 255
        fill = num / np.maximum(den, 1e-3)
        new = (have < 0.5) & (den[..., 0] > 0.02)
        rgb[new] = fill[new]; have[new] = 1
    out = np.dstack([rgb.clip(0, 255), a]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")
os.makedirs(dst, exist_ok=True)
sp = json.load(open("species.json")); gen = {g["name"]: g for g in json.load(open(os.path.join(src, "generated.json")))}
BARK_UV = {"bark_moss": [2.0, 0.6], "bark_birch": [1.0, 0.35], "bark_pine": [1.5, 0.4]}
man = {"version": 2, "zones": [200], "made_by": "EZ-Tree (MIT, Daniel Greenheck) via pipeline/trees", "models": {}, "species": {}}
used_tex = set()
for name, s in sp.items():
    vs = sorted([g for g in gen if gen[g]["species"] == name], key=lambda n: int(n.rsplit("_", 1)[1]))
    if not vs: continue
    for m in s["models"]: man["models"][m] = name
    # the far pictures: one row per variant, VIEWS pictures of 256 x 512 across; the clear pixels coloured from their
    # neighbours (no dark fringe as the mipmaps blend them in)
    views = int(gen[vs[0]]["far"].get("views", 2)); cw = 256
    atlas = Image.new("RGBA", (cw * views, 512 * len(vs)), (0, 0, 0, 0))
    for i, v in enumerate(vs):
        atlas.paste(Image.open(os.path.join(src, v + "_far.png")).convert("RGBA"), (0, i * 512))
        shutil.copy(os.path.join(src, v + ".glb"), os.path.join(dst, v + ".glb"))
    atlas = bleed(atlas)
    atlas.save(os.path.join(dst, f"far_{name}.png"))
    man["species"][name] = {"variants": [v + ".glb" for v in vs], "bark": s["bark"] + ".png", "leaf": s["leaf"] + ".png",
        "tint": s["leafTint"], "height": s["height"], "bark_uv": BARK_UV.get(s["bark"], [1, 1]),
        "sink": s["sink"],
        **{k: s[k] for k in ("tone", "sat", "bark_tone") if k in s},
        "far": {"atlas": f"far_{name}.png", "views": views, "rows": len(vs), "cards": [gen[v]["far"] for v in vs]}}
    used_tex |= {s["bark"], s["leaf"]}
for t in used_tex: shutil.copy(f"web/tex/{t}.png", os.path.join(dst, t + ".png"))
for f in ["LICENSE"]: shutil.copy("node_modules/@dgreenheck/ez-tree/LICENSE", os.path.join(dst, "EZ-TREE-LICENSE.txt"))
json.dump(man, open(os.path.join(dst, "trees.json"), "w"), indent=1)
print(len(man["models"]), "models,", len(man["species"]), "species")
