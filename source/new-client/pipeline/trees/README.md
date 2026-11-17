# Trees (TreeSwap)

The new trees, made with EZ-Tree (MIT, Daniel Greenheck: github.com/dgreenheck/ez-tree) run in headless Chromium.

    npm install @dgreenheck/ez-tree three playwright
    python make_tex.py <folder with the original tree textures>   # leaf cards and bark -> web/tex
    python build_specs.py 6                                        # 6 seeded variants of each species in species.json
    node gen2.mjs specs.json out/set                               # .glb, far-card picture and preview per variant
    python package.py out/set <game>/new-client/godot/content/trees

species.json: each species' EZ-Tree preset and changes, the original models it replaces, its height in metres, how
far the original sinks into the ground, its bark and leaf pictures and the leaf tint. package.py's "zones" limits the
swap to the pilot zones (Lough Derg, 200) until it is signed off.
