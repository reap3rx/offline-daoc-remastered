# Every remaining tree in the game as a species (claude 2026-11-17): a family's EZ-Tree shape, the original's own
# height and sink (from its model) and its own leaf and bark pictures (make_tex2.py). Writes species.json.
import json, os, copy
sp = json.load(open("species.json")); dims = json.load(open("src_all/dims.json"))
E = copy.deepcopy
FAM = {
 "elm": {"preset": "Oak Large", "options": E(sp["elm"]["options"])},
 "oak": {"preset": "Oak Medium", "options": E(sp["oak"]["options"])},
 "tall": {"preset": "Oak Large", "options": {"branch": {"angle": {"1": 40, "2": 45, "3": 35}, "children": {"0": 7, "1": 4, "2": 3},
          "length": {"0": 70, "1": 24, "2": 12, "3": 5}, "start": {"1": 0.5}, "force": {"strength": 0.01}, "radius": {"0": 1.8}},
          "leaves": {"count": 7, "size": 8, "sizeVariance": 0.4, "angle": 30, "start": 0.2}}},
 "small": {"preset": "Oak Small", "options": {"branch": {"children": {"0": 8, "1": 5, "2": 3}, "start": {"1": 0.25}},
          "leaves": {"count": 8, "size": 3.5, "sizeVariance": 0.4, "angle": 30}}},
 "dead": {"preset": "Oak Large", "options": E(sp["dead"]["options"])},
 "bare": {"preset": "Aspen Large", "options": E(sp["bare"]["options"])},
 "pine": {"preset": "Pine Large", "options": E(sp["grovepine"]["options"])},
 "pinemid": {"preset": "Pine Medium", "options": {"bark": {"textureScale": {"x": 1, "y": 5}}, "branch": {"children": {"0": 50, "1": 3},
          "start": {"1": 0.18}, "gnarliness": {"0": 0.0, "1": 0.05}, "twist": {"0": 0, "1": 0}},
          "leaves": {"count": 16, "size": 2.6, "sizeVariance": 0.35}}},
 "spruce": {"preset": "Pine Small", "options": E(sp["yew"]["options"])},
 "willow": {"preset": "Aspen Large", "droop": 0.05, "options": {"branch": {"angle": {"1": 55, "2": 70}, "children": {"0": 9, "1": 5, "2": 3},
          "start": {"1": 0.35}, "radius": {"0": 1.4}}, "leaves": {"count": 14, "size": 4.5, "sizeVariance": 0.3, "angle": 10}}},
 "giant": {"preset": "Oak Large", "options": {"branch": {"angle": {"1": 55, "2": 45, "3": 35}, "children": {"0": 8, "1": 5, "2": 3},
          "length": {"0": 160, "1": 34, "2": 14, "3": 6}, "start": {"1": 0.7}, "radius": {"0": 3.2, "1": 0.6},
          "gnarliness": {"0": 0.02, "1": 0.15}, "force": {"strength": 0.006}},
          "leaves": {"count": 12, "size": 4.5, "sizeVariance": 0.4, "angle": 30, "start": 0.15}}},
}
DEF_BARK = {"pine": "bark_pine", "pinemid": "bark_pine", "spruce": "bark_pine"}
# model: (family, atlas, extra)
M = {
 "elm1": ("elm", "tree1", {}), "elm2": ("elm", "tree2", {}), "alder": ("tall", "alder", {}),
 "appletree": ("elm", "appletree", {}), "beech": ("tall", "beech", {}), "chestnut": ("tall", "chestnut", {}),
 "yew": ("elm", "yew", {}), "maple": ("tall", "maple", {}), "stonepine": ("oak", "stonepine", {}),
 "talloak1": ("tall", "talloak1", {}), "ash": ("tall", "ash", {}), "oak1": ("oak", "oak1", {}),
 "beech_gnarl": ("oak", "beech_gnarl", {}), "b_htoak1": ("oak", "b_htoak1", {}), "hollytree": ("small", "hollytree", {}),
 "b_htoakb": ("dead", "b_htoakb", {}), "beech_gnarl_dead": ("dead", "beech_gnarl_dead", {}), "bbare1": ("dead", "bbare1", {}),
 "bbare2": ("bare", "b-bare2", {"clump": 2}),
 "pintre1": ("pinemid", "pintren", {}), "npintre1": ("pinemid", "npintren", {}), "npintre-s": ("pinemid", "n_s_pintren", {}),
 "bpinea": ("pinemid", "bpinean", {}), "npinea": ("pinemid", "npinean", {}), "npinea-s": ("pinemid", "npinean1-s", {}),
 "bpinetree": ("pinemid", "bpinetreen", {}), "npinetree": ("pinemid", "npinetreen", {}), "npinetree-s": ("pinemid", "npinetreen_s", {}),
 "npinedk": ("pinemid", "npinendk", {}), "creepywebpine": ("pinemid", "bscrypinen", {}),
 "bvrgrn1": ("spruce", "bvrgrn1", {}), "vrgrn1": ("spruce", "vrgrn1", {}), "nvrgrn1-s": ("spruce", "nvrgrn1-s", {}),
 "spruce": ("spruce", "spruce", {}),
 "bwillow": ("willow", "bwillown2", {}), "hweepwill": ("willow", "hweepwilln", {}), "bspanmoss": ("willow", "bspanmossn", {}),
 "bighibtree": ("giant", "bighibtree", {}), "iarnwood": ("giant", "iarnwood", {}),
 "mightyoak": ("giant", "mightyoak", {}), "mightyoak-small": ("giant", "mightyoak", {}),
}
for m, (fam, atlas, extra) in M.items():
    name = m.replace("-", "_")
    d = dims[m]; f = FAM[fam]
    bark = f"bark_{atlas}" if os.path.exists(f"web/tex/bark_{atlas}.png") else DEF_BARK.get(fam, "bark_moss")
    e = {"models": [m], "preset": f["preset"], "height": round(d["h"], 1), "sink": round(-d["ymin"] * 0.85, 1),
         "bark": bark, "leaf": f"leaf_{atlas}", "leafTint": "#ffffff", "options": E(f["options"]), "family": fam}
    if fam in ("pine", "pinemid", "spruce"): e["lean"] = 0.002
    if "droop" in f: e["droop"] = f["droop"]
    if fam == "giant":
        e["variants"] = 4
    e.update(extra)
    sp[name] = e
json.dump(sp, open("species.json", "w"), indent=1)
print(len(sp), "species")
