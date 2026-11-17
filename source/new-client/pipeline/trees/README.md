# Trees (TreeSwap)

The new trees, made with EZ-Tree (MIT, Daniel Greenheck: github.com/dgreenheck/ez-tree) run in headless Chromium.

    npm install @dgreenheck/ez-tree three playwright
    python make_tex.py <folder with the original tree textures>   # Lough Derg's leaf cards and bark -> web/tex
    python make_tex2.py <trees_src> <atlas,atlas,...>              # every other tree's, from its own atlas (tex_overrides.json)
    python add_species.py                                          # every other tree model as a species (families)
    python build_specs.py 6                                        # 6 seeded variants of each species in species.json
    node gen2.mjs specs.json out/set                               # .glb, far-card picture and preview per variant
    python package.py out/set <game>/new-client/godot/content/trees

species.json: each species' EZ-Tree preset and changes, the original models it replaces, its height in metres, how
far the original sinks into the ground, its bark and leaf pictures and the leaf tint. package.py's "zones" limits the
swap to some zones (empty: all). trees_src is claude-work/tree_gather.py's copy of each tree model and its textures.
Far pictures are baked unlit at the near leaves' brightness (bark at 1.15/1.75), so the game's far card at 1.75 matches.
