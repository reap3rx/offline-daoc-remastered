# The extra foliage's bushes (Foliage, owner 2026-11-17) into content/trees: bushes.json and each variant's .glb (their
# leaf and bark pictures are the trees' own, already there - package.py).
import json, os, shutil, sys
src = sys.argv[1]; dst = sys.argv[2]
B = json.load(open("bushes.json"))
os.makedirs(dst, exist_ok=True)
SINK = {"juniper": 0.08, "sapling": 0.03, "thicket": 0.18}
man = {"version": 1, "made_by": "EZ-Tree (MIT, Daniel Greenheck) via pipeline/trees", "kinds": {}}
for k, b in B.items():
    vs = sorted(f[:-4] for f in os.listdir(src) if f.startswith(k + "_") and f.endswith(".glb") and f[len(k) + 1:-4].isdigit())
    for v in vs:
        shutil.copy(os.path.join(src, v + ".glb"), os.path.join(dst, v + ".glb"))
    tail = k.split("_", 1)[1]
    sink = SINK.get(tail, 0.22)
    if tail == "thicket" and b["preset"] == "Pine Small":
        sink = 0.08
    man["kinds"][k] = {"variants": [v + ".glb" for v in vs], "leaf": b["leaf"] + ".png", "bark": b["bark"] + ".png",
                       "tint": b["leafTint"], "height": b["height"], "plant_sink": sink}
    for t in (b["leaf"], b["bark"]):
        if not os.path.exists(os.path.join(dst, t + ".png")):
            print("missing texture in", dst, t)
json.dump(man, open(os.path.join(dst, "bushes.json"), "w"), indent=1)
print(len(man["kinds"]), "kinds")
