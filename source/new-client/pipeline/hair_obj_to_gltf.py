"""A MakeHuman hair (CC0 system assets: hair/<name>/<name>.obj + _diffuse.png) as a small glTF for the hair test
(claude 2026-11-05, owner: "a test run on a hair replacement ... on one hair style"): triangles, smooth normals, UVs,
and its texture made colourless (the strands' light and dark and their alpha), to be coloured in the game by the hair
colour the character picked.
    python hair_obj_to_gltf.py <hair dir> <out dir>"""
import base64, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
name = src.name
V, T, F = [], [], []
for line in (src / f'{name}.obj').read_text(encoding='latin-1').splitlines():
    p = line.split()
    if not p:
        continue
    if p[0] == 'v':
        V.append([float(x) for x in p[1:4]])
    elif p[0] == 'vt':
        T.append([float(x) for x in p[1:3]])
    elif p[0] == 'f':
        c = [(int(a.split('/')[0]) - 1, int(a.split('/')[1]) - 1) for a in p[1:]]
        for i in range(1, len(c) - 1):
            F.append((c[0], c[i], c[i + 1]))
V, T = np.array(V), np.array(T)
keys, tris = {}, []
for f in F:
    tri = []
    for k in f:
        if k not in keys:
            keys[k] = len(keys)
        tri.append(keys[k])
    tris.append(tri)
order = sorted(keys, key=keys.get)
pos = np.array([V[v] for v, _ in order], np.float32)
uv = np.array([[T[t][0], 1.0 - T[t][1]] for _, t in order], np.float32)
tris = np.array(tris, np.uint32)
# smooth normals over shared positions
nrm = np.zeros_like(pos)
fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
vid = np.array([v for v, _ in order])
acc = np.zeros((len(V), 3))
for c in range(3):
    np.add.at(acc, vid[tris[:, c]], fn)
nrm = acc[vid]
nrm = (nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)).astype(np.float32)
# the texture without its colour: luminance around a mid grey, alpha kept
tex = next(src.glob('*_diffuse.png'))
im = np.asarray(Image.open(tex).convert('RGBA')).astype(np.float32) / 255
lum = im[..., :3] @ np.array([0.3, 0.59, 0.11])
a = im[..., 3]
m = (lum * a).sum() / max(a.sum(), 1e-6)
g = np.clip(lum / max(m, 1e-6) * 0.5, 0, 1)
Image.fromarray((np.dstack([g, g, g, a]) * 255 + 0.5).astype(np.uint8), 'RGBA').save(out / f'{name}_strands.png')
blob = b''
views, accs = [], []
def add(arr, ctype, atype, target, mm=False):
    global blob
    while len(blob) % 4:
        blob += b'\0'
    views.append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': arr.nbytes, 'target': target})
    blob += arr.tobytes()
    acc = {'bufferView': len(views) - 1, 'componentType': ctype, 'count': len(arr), 'type': atype}
    if mm:
        acc['min'] = arr.min(0).tolist(); acc['max'] = arr.max(0).tolist()
    accs.append(acc)
    return len(accs) - 1
ip = add(pos, 5126, 'VEC3', 34962, True); inn = add(nrm, 5126, 'VEC3', 34962); iu = add(uv, 5126, 'VEC2', 34962)
ii = add(tris.reshape(-1), 5125, 'SCALAR', 34963)
g = {'asset': {'version': '2.0', 'generator': 'hair_obj_to_gltf.py', 'extras': {'source': f'MakeHuman system assets hair/{name} (CC0)'}},
     'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'name': name, 'mesh': 0}],
     'meshes': [{'name': name, 'primitives': [{'attributes': {'POSITION': ip, 'NORMAL': inn, 'TEXCOORD_0': iu}, 'indices': ii, 'material': 0}]}],
     'materials': [{'name': name, 'doubleSided': True, 'alphaMode': 'MASK', 'alphaCutoff': 0.35,
                    'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0.0, 'roughnessFactor': 0.6}}],
     'textures': [{'source': 0}], 'images': [{'uri': f'{name}_strands.png'}],
     'buffers': [{'byteLength': len(blob), 'uri': 'data:application/octet-stream;base64,' + base64.b64encode(blob).decode()}],
     'bufferViews': views, 'accessors': accs}
(out / f'{name}.gltf').write_text(json.dumps(g), encoding='utf-8')
print(name, len(pos), 'verts', len(tris), 'tris', 'bbox', pos.min(0), pos.max(0))
