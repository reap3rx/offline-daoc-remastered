# Variant specs: each species' options jittered by a seeded random (length, angle, children, lean, leaf size).
import json, random, sys, copy
import os; sp = json.load(open(os.environ.get("SPECIES", "species.json"))); n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
out = []
for name, s in sp.items():
    if only and name not in only: continue
    for v in range(s.get("variants", n)):
        r = random.Random(f"{name}/{v}"); o = copy.deepcopy(s["options"]); b = o.setdefault("branch", {})
        for k in ("length",):
            for lv in list(b.get(k, {}).keys()): b[k][lv] = round(b[k][lv] * r.uniform(0.85, 1.15), 2)
        for lv in list(b.get("angle", {}).keys()): b["angle"][lv] = round(b["angle"][lv] + r.uniform(-8, 8), 1)
        lean = r.uniform(0, s.get("lean", 0.012)); a = r.uniform(0, 6.283)
        import math
        b["force"] = {"direction": {"x": round(math.cos(a) * 0.35, 3), "y": 1, "z": round(math.sin(a) * 0.35, 3)}, "strength": round(b.get("force", {}).get("strength", 0.0) + lean, 4)}
        if s.get("droop"):                       # willows: the boughs hang (the force pulls down)
            b["force"] = {"direction": {"x": 0, "y": -1, "z": 0}, "strength": s["droop"]}
        # lighter trunks and branches (owner 2026-11-17: frame cost close to the old trees): fewer sides and sections
        b["segments"] = s.get("segments", {"0": 8, "1": 4, "2": 3, "3": 3})
        b["sections"] = s.get("sections", {"0": 10, "1": 6, "2": 4, "3": 3})
        lf = o.setdefault("leaves", {}); lf["size"] = round(lf.get("size", 3) * r.uniform(0.88, 1.12), 2)
        out.append({"name": f"{name}_{v}", "species": name, "preset": s["preset"], "options": o, "seed": r.randrange(1, 99999),
                    "height": round(s["height"] * r.uniform(0.92, 1.08), 2), "sink": s["sink"], "clump": s.get("clump", 1),
                    "bark": s["bark"], "leaf": s["leaf"], "leafTint": s["leafTint"], "shot": v < 2})
json.dump(out, open(os.environ.get("SPECS_OUT", "specs.json"), "w"), indent=1); print(len(out), "specs")
