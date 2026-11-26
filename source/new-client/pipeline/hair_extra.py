"""More hair sliders (owner 2026-11-26: "look at the sliders we have, and see if there are more we can have"): three
more hf_ fit targets on every hair style, beard, moustache and sideburns that has the fit sliders (pipeline/
import_hair.py's hf_lr ... hf_len), shared by the creator's Hair Sliders and the race's saved positions:

  hf_tilt    the whole piece turned about the skull's middle, its top back (+) or forward (-) - 12 degrees at 1
  hf_flare   the lower part spread out from the head (+) or drawn in (-), more the lower it hangs
  hf_volume  the piece fuller (+) or flatter (-), out along its own surface

Runs on a built figure (after face_extra); safe to run again (a figure that has them is left as it is).

    python hair_extra.py <race folder> [<out folder>]
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from face_morphs import G, weld
from face_extra import add_target

NEW = ['hf_tilt', 'hf_flare', 'hf_volume']
TILT = np.radians(12.0)


def skull(g):
    """The skull's middle and radius: a sphere through the head's upper half."""
    node = next(n for n in g.g['nodes'] if n.get('name') == 'head' and 'mesh' in n)
    P = np.concatenate([g.acc(p['attributes']['POSITION']).astype(np.float64) for p in g.g['meshes'][node['mesh']]['primitives']])
    top = P[P[:, 2] > np.percentile(P[:, 2], 50)]
    A = np.c_[2 * top, np.ones(len(top))]
    s, *_ = np.linalg.lstsq(A, (top * top).sum(1), rcond=None)
    c = s[:3]
    return c, float(np.sqrt(max(s[3] + c @ c, 1e-9)))


def fields(P, N, c, R):
    rel = P - c
    ct, st = np.cos(TILT), np.sin(TILT)
    tilt = np.zeros_like(P)
    tilt[:, 1] = rel[:, 1] * ct + rel[:, 2] * st - rel[:, 1]            # (figure axes: -y forward, z up)
    tilt[:, 2] = -rel[:, 1] * st + rel[:, 2] * ct - rel[:, 2]
    below = np.clip(-rel[:, 2] / (1.3 * R), 0, 1) ** 1.2
    flare = np.zeros_like(P)
    flare[:, 0] = rel[:, 0] * 0.3 * below
    flare[:, 1] = rel[:, 1] * 0.3 * below
    grp = weld(P)                                    # (one normal where vertices share a place: no cracks)
    Ng = np.zeros((grp.max() + 1, 3)); np.add.at(Ng, grp, N)
    Nn = Ng[grp] / np.maximum(np.linalg.norm(Ng[grp], axis=1, keepdims=True), 1e-12)
    volume = Nn * 0.035 * R
    return {'hf_tilt': tilt, 'hf_flare': flare, 'hf_volume': volume}


def run(folder, out=None):
    folder = Path(folder); out = Path(out or folder)
    g = G(folder / 'figure.gltf')
    c, R = skull(g)
    n = 0
    for mesh in g.g['meshes']:
        names = list(mesh.get('extras', {}).get('targetNames', []))
        if 'hf_size' not in names or 'hf_tilt' in names:
            continue
        for prim in mesh['primitives']:
            P = g.acc(prim['attributes']['POSITION']).astype(np.float64)
            N = g.acc(prim['attributes']['NORMAL']).astype(np.float64) if 'NORMAL' in prim['attributes'] else np.zeros_like(P)
            D = fields(P, N, c, R)
            for k in NEW:
                pa, na = add_target(g, D[k])
                prim['targets'].append({'POSITION': pa, 'NORMAL': na})
        mesh['extras']['targetNames'] = names + NEW
        if 'weights' in mesh:
            mesh['weights'] = mesh['weights'] + [0.0] * len(NEW)
        n += 1
    if n == 0 and out == folder:
        print('%s: hair sliders already there (or no fitted hair)' % folder.name)
        return
    out.mkdir(parents=True, exist_ok=True)
    g.save(out / 'figure.gltf')
    if out != folder:
        import shutil
        shutil.copy(folder / 'figure.json', out / 'figure.json')
    print('%s: %d hair pieces gain tilt, flare and volume (skull radius %.2f)' % (folder.name, n, R))


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
