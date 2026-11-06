"""Where the body sliders' bust (pecs) and glutes swell (Fig3Figure.BodyShape._bulge): figure.json "body_marks".

From the rest pose: the chest's skin (weighted most to Spine2) - on each side the part that stands furthest forward is
the bust's middle; the seat's (Pelvis, the thighs' tops) furthest back the glutes'. Each in its bone's own frame
(Biped: x up the spine, z across; front is the way the toes point), with a radius and the way it swells.

    python body_marks.py <race folder>...
"""
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import face_morphs  # noqa: E402
from face_morphs import G  # noqa: E402
face_morphs.NC.setdefault("MAT4", 16)

SKIP = ('head', 'hair', 'beard', 'cloak', 'fullhelm', 'helm')


def run(folder):
    folder = Path(folder)
    meta_path = folder / 'figure.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    g = G(folder / 'figure.gltf')
    N = g.g['nodes']
    skin = g.g['skins'][0]
    joints = skin['joints']
    names = [N[j].get('name', '') for j in joints]
    ibm = g.acc(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)
    ji = {n: i for i, n in enumerate(names)}
    P, J = [], []
    head = []
    for n in N:
        nm = n.get('name', '')
        if 'mesh' not in n:
            continue
        for p in g.g['meshes'][n['mesh']]['primitives']:
            if 'JOINTS_0' not in p['attributes']:
                continue
            pos = g.acc(p['attributes']['POSITION']).astype(np.float64)
            if nm == 'head':
                head.append(pos)
            if nm.startswith(SKIP):
                continue
            jj = g.acc(p['attributes']['JOINTS_0']).astype(int)
            ww = g.acc(p['attributes']['WEIGHTS_0']).astype(np.float64)
            P.append(pos)
            J.append(jj[np.arange(len(jj)), ww.argmax(1)])
    P = np.concatenate(P)
    J = np.concatenate(J)

    def local(bone, pts):
        m = ibm[ji['Bip01 ' + bone]]
        return pts @ m[:3, :3].T + m[:3, 3]

    # front: the way the toes point, in the chest's frame
    def joint(n):
        return np.linalg.inv(ibm[ji['Bip01 ' + n]])[:3, 3]
    toe = local('Spine2', np.array([joint('L Toe0') - joint('L Foot') + joint('Spine2')]))[0]
    front = 1.0 if toe[1] > 0 else -1.0
    out = {}
    for key, bones, sgn, bone in (('bust', ['Spine2'], front, 'Spine2'),
                                  ('glute', ['Pelvis', 'Spine', 'L Thigh', 'R Thigh'], -front, 'Pelvis')):
        sel = np.isin(J, [ji['Bip01 ' + b] for b in bones if 'Bip01 ' + b in ji])
        L = local(bone, P[sel])
        if key == 'glute':                                  # the seat: from the hip joints to a third down the thigh
            thigh = np.linalg.norm(joint('L Calf') - joint('L Thigh'))
            L = L[(L[:, 0] < 0.15 * thigh) & (L[:, 0] > -0.4 * thigh)]
        W = np.percentile(np.abs(L[:, 2]), 98) * 2
        r = 0.22 * W if key == 'bust' else 0.26 * W
        side = {}
        for s, nm in ((1, 'l'), (-1, 'rt')):
            m = (L[:, 2] * s > 0.12 * W) & (L[:, 2] * s < 0.42 * W)
            Q = L[m]
            f = Q[:, 1] * sgn
            top = Q[f >= np.percentile(f, 96)]
            ctr = top.mean(0)
            ctr[1] -= sgn * r * 0.45                         # its middle a little inside the skin
            side[nm] = [round(float(x), 3) for x in ctr]
        side['r'] = round(float(r), 3)
        side['dir'] = [0.0, float(sgn), 0.0]
        out[key] = side
    meta['body_marks'] = out
    meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print(folder.name, json.dumps(out))


if __name__ == '__main__':
    for f in sys.argv[1:]:
        run(f)
