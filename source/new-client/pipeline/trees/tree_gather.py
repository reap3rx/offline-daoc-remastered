# Copy every tree model (and its textures, x4plus where there is one) from the zone content into claude-work/trees_src
# for the tree generator (claude 2026-11-17).
import json, os, shutil, zipfile
root = r"E:\Offline DAOC 036c\playable-v0.36c\new-client\godot\content\zones"
out = r"E:\Offline DAOC 036c\claude-work\trees_src"
TREES = """helm helm2 hoaktree hbirchsingle nbirchtree holdgrove hlowtree hbareskny hdeadtree hweepwill bighibtree chestnut yew
alder iarnwood elm1 elm2 oak1 bwillow pintre1 bpinea bpinetree bvrgrn1 vrgrn1 maple beech beech_gnarl beech_gnarl_dead
mightyoak mightyoak-small talloak1 ash appletree hollytree bbare1 bbare2 b_htoakb b_htoak1 bspanmoss bmtntre1 npinea
npintre1 npinea-s npinetree-s npintre-s npinedk npinetree nvrgrn1-s spruce stonepine creepywebpine""".split()
os.makedirs(out, exist_ok=True)
found = {}
for z in sorted(os.listdir(root)):
    md = os.path.join(root, z, "models")
    if not os.path.isdir(md):
        continue
    for t in TREES:
        if t in found:
            continue
        p = os.path.join(md, t + ".gltf")
        if os.path.exists(p):
            found[t] = z
            shutil.copy(p, os.path.join(out, t + ".gltf"))
            g = json.load(open(p))
            for im in g.get("images", []):
                name = os.path.basename(im["uri"])
                for sub in ("x4plus", "original"):
                    src = os.path.join(root, z, "textures", sub, name)
                    if os.path.exists(src):
                        shutil.copy(src, os.path.join(out, ("x4_" if sub == "x4plus" else "") + name))
            # the detail textures too (nif_materials slots)
            for m in g.get("extras", {}).get("nif_materials", []):
                for sl in m.get("slots", {}).values():
                    for sub in ("x4plus", "original"):
                        src = os.path.join(root, z, "textures", sub, sl["tex"] + ".png")
                        if os.path.exists(src):
                            shutil.copy(src, os.path.join(out, ("x4_" if sub == "x4plus" else "") + sl["tex"] + ".png"))
print("found", len(found), "of", len(TREES), "missing", [t for t in TREES if t not in found])
json.dump(found, open(os.path.join(out, "found.json"), "w"), indent=0)
tot = sum(os.path.getsize(os.path.join(out, f)) for f in os.listdir(out))
print("bytes", tot, "files", len(os.listdir(out)))
