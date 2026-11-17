# content/trees for the game (TreeSwap): trees.json, each variant's .glb, the species' far-card atlases, the textures.
import json, os, shutil, sys
from PIL import Image
src = sys.argv[1]; dst = sys.argv[2]
os.makedirs(dst, exist_ok=True)
sp = json.load(open("species.json")); gen = {g["name"]: g for g in json.load(open(os.path.join(src, "generated.json")))}
BARK_UV = {"bark_moss": [2.0, 0.6], "bark_birch": [1.0, 0.35], "bark_pine": [1.5, 0.4]}
man = {"version": 1, "zones": [200], "made_by": "EZ-Tree (MIT, Daniel Greenheck) via pipeline/trees", "models": {}, "species": {}}
used_tex = set()
for name, s in sp.items():
    vs = sorted([g for g in gen if gen[g]["species"] == name], key=lambda n: int(n.rsplit("_", 1)[1]))
    if not vs: continue
    for m in s["models"]: man["models"][m] = name
    atlas = Image.new("RGBA", (512 * len(vs), 512), (0, 0, 0, 0))
    for i, v in enumerate(vs):
        atlas.paste(Image.open(os.path.join(src, v + "_far.png")).convert("RGBA"), (i * 512, 0))
        shutil.copy(os.path.join(src, v + ".glb"), os.path.join(dst, v + ".glb"))
    atlas.save(os.path.join(dst, f"far_{name}.png"))
    man["species"][name] = {"variants": [v + ".glb" for v in vs], "bark": s["bark"] + ".png", "leaf": s["leaf"] + ".png",
        "tint": s["leafTint"], "height": s["height"], "bark_uv": BARK_UV.get(s["bark"], [1, 1]),
        "far": {"atlas": f"far_{name}.png", "cards": [gen[v]["far"] for v in vs]}}
    used_tex |= {s["bark"], s["leaf"]}
for t in used_tex: shutil.copy(f"web/tex/{t}.png", os.path.join(dst, t + ".png"))
for f in ["LICENSE"]: shutil.copy("node_modules/@dgreenheck/ez-tree/LICENSE", os.path.join(dst, "EZ-TREE-LICENSE.txt"))
json.dump(man, open(os.path.join(dst, "trees.json"), "w"), indent=1)
print(len(man["models"]), "models,", len(man["species"]), "species")
