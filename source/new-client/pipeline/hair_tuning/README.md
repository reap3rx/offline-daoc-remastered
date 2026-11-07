# Hair tuning

One file per race and sex (`bri_m.json`, `elf_f.json`, ...), written by the character creator's tuning controls
(the folder existing turns them on). Each part — `hair:<folder>/<model>`, `beard:...`, `moustache:...`,
`sideburns:...`, or a race's own style by its node — keeps:

- `fit`: the slider values saved for this race (every figure's default for that part until they are baked in)
- `disabled`: left out of the creator, bots and NPCs for this race
- `done`: the date it was decided

When every race is done, `pipeline/import_hair.py` bakes the fits into the meshes, drops the parts disabled for
every race, and the creator keeps only the Length slider.
