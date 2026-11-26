# The HD head, rebuilt (v2, 2026-11-25)

MakeHuman's whole CC0 head (skin, its own eyeballs, lashes, teeth, tongue, ears) set to a race's size and proportions
and written into the race's figure.gltf as "head__hd", "head__hd_eyes", "head__hd_mouth", "head__hd_lash".
Nothing of the classic head is kept in it. The first build (hd_head.py, hd_wrap.py: the new skin with the classic
eyeballs, ears and neck edge stitched in) is superseded.

    python head2.py <race folder with figure.gltf / figure.json> <out folder>

- fit2.py   landmarks -> move / turn / scale, a soft bend, a coarse pull onto the classic skin; the eyes, ears and lips
            each kept whole (a similarity) so lids fit their eyeball and lips stay closed
- ear2.py   long-eared races: MakeHuman's ear drawn out to the classic ear's tip
- neck2.py  the cut along the classic head's lower edge, every classic edge point a point of the new edge
- tex2.py   hd_base / hd_remap / hd_detail beside the figure; hd_eye / hd_mouth / hd_lash shared (content/characters/hd_head)
- mask3.py  the face maps (the HD look): hd_face (each texel's face-space point) and hd_mask (lips, the eyes' rim,
            face, scalp) - the client draws brows, liner, shadow, blush, contour and lip colour in face space
- brows3.py the brows' hairs (hd_brow_hair.png, shared)
- eyes3.py  the eyes drawn (hd_eye white, hd_eye_polar, hd_iris patterns, shared)
- marks3.py the age lines and scars in face space (hd_age, hd_scars, shared)
- look3.py  the client shader's HD look in numpy, for previews while tuning (keep in step with Fig3Figure's shader)
- check2.py what went wrong before, tested on every build and at every slider's end (exit code 3 on a failure)
- mh2.py    MakeHuman's proxies (.mhclo) and the subdivided helper eyes

Needs beside these files: `makehuman` (MakeHuman's data: 3dobjs/base.obj, targets) and `mh_sys` (the CC0 "MakeHuman
system assets" pack: skins, eyes, eyelashes, teeth, tongue -
https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip).
Python: numpy, scipy, opencv-python-headless.
