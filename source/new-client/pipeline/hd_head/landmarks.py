"""Matching landmarks on a race's classic head and the MakeHuman head (figure axes: z up, the face toward -y)."""
import numpy as np
from mhbase import read_target
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

NAMES = ['eyeL', 'eyeR', 'mouthL', 'mouthR', 'nose', 'chin', 'earL', 'earR', 'top', 'back', 'browL', 'browR', 'jawL', 'jawR']

def sphere_fit(Q):
    A = np.c_[2 * Q, np.ones(len(Q))]
    b = (Q ** 2).sum(1)
    x = np.linalg.lstsq(A, b, rcond=None)[0]
    c = x[:3]
    return c, np.sqrt(x[3] + c @ c)

def components(P, T, grp):
    e = np.concatenate([grp[T[:, [0, 1]]], grp[T[:, [1, 2]]]])
    n = grp.max() + 1
    nc, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    return lab[grp]

def common(P, eyeL, eyeR, mouthL, mouthR, front_sel, skull_sel):
    """The landmarks both heads find the same way, from the eyes and mouth corners."""
    em = (eyeL + eyeR) / 2
    mm = (mouthL + mouthR) / 2
    E = np.linalg.norm(eyeL - eyeR)
    L = {'eyeL': eyeL, 'eyeR': eyeR, 'mouthL': mouthL, 'mouthR': mouthR}
    mid = np.abs(P[:, 0]) < 0.12 * E
    # nose tip: the midline's most forward point between the mouth and the eyes
    s = mid & (P[:, 2] > mm[2] + 0.15 * (em[2] - mm[2])) & (P[:, 2] < em[2]) & front_sel
    L['nose'] = P[s][np.argmin(P[s, 1])]
    # chin: the midline's low forward corner below the mouth
    s = mid & (P[:, 2] < mm[2] - 0.35 * E) & (P[:, 2] > mm[2] - 1.6 * E) & front_sel
    L['chin'] = P[s][np.argmin(P[s, 2] + 1.5 * P[s, 1])]
    # brows: above each eye, the most forward point
    for k, e in (('browL', eyeL), ('browR', eyeR)):
        s = (np.abs(P[:, 0] - e[0]) < 0.2 * E) & (P[:, 2] > e[2] + 0.2 * E) & (P[:, 2] < e[2] + 0.9 * E) & front_sel
        L[k] = P[s][np.argmin(P[s, 1])]
    # jaw corners: the widest point of the face at the mouth's height, toward the back of the jaw
    for k, sg in (('jawL', 1), ('jawR', -1)):
        s = (P[:, 0] * sg > 0) & (np.abs(P[:, 2] - (mm[2] - 0.3 * E)) < 0.25 * E) & (P[:, 1] < em[1] + 1.2 * E) & skull_sel
        L[k] = P[s][np.argmax(P[s, 0] * sg)]
    s = skull_sel
    L['top'] = P[s][np.argmax(P[s, 2])]
    s = skull_sel & (np.abs(P[:, 0]) < 0.3 * E) & (P[:, 2] > em[2] - 0.3 * E) & (P[:, 2] < em[2] + 1.0 * E)
    L['back'] = P[s][np.argmax(P[s, 1])]
    return L

def race_landmarks(h, names):
    """h: headio.load_head result. -> (landmarks, parts mask dict)."""
    from face_morphs import weld
    P, T, J, W = h['P'], h['T'], h['J'], h['W']
    grp = weld(P)
    lab = components(P, T, grp)
    big = np.bincount(lab).argmax()
    skin = lab == big
    eyes = {}
    for side, nm in (('L', 'Bip01 L Eyeball'), ('R', 'Bip01 R Eyeball')):
        bi = names.index(nm)
        comp = [c for c in np.unique(lab) if c != big and ((J[lab == c] == bi) & (W[lab == c] > 0.5)).any()]
        m = np.isin(lab, comp)
        eyes[side] = sphere_fit(P[m]) + (m,)
    teeth = ~skin & ~eyes['L'][2] & ~eyes['R'][2]
    # (only pieces in the mouth: the Shar's head carries their arms' spikes as pieces of its own)
    em = (eyes['L'][0] + eyes['R'][0]) / 2
    E0 = np.linalg.norm(eyes['L'][0] - eyes['R'][0])
    for c in np.unique(lab[teeth]):
        m = lab == c
        q = P[m].mean(0)
        if abs(q[0]) > E0 or q[2] > em[2] or q[2] < em[2] - 3.5 * E0 or np.linalg.norm(q - em) > 4 * E0:
            teeth &= ~m
    # mouth corners: the teeth strips' ends sit just inside them; the corner is the skin's lip-line point beside each end
    tq = P[teeth]
    mL = tq[np.argmax(tq[:, 0])]; mR = tq[np.argmin(tq[:, 0])]
    zc = tq[:, 2].mean()
    out = {}
    for k, e, sg in (('mouthL', mL, 1), ('mouthR', mR, -1)):
        s = skin & (np.abs(P[:, 2] - zc) < 0.25) & (P[:, 1] < e[1] + 0.3) & (P[:, 0] * sg > abs(e[0]) * 0.7)
        cand = P[s]
        # the corner: the lip-line's outermost point that is still at the lips' front
        k2 = np.argmin(np.abs(cand[:, 0] - sg * (abs(e[0]) + 0.1)) + 2 * np.abs(cand[:, 2] - zc))
        out[k] = cand[k2]
    E = np.linalg.norm(eyes['L'][0] - eyes['R'][0])
    front = skin & (P[:, 1] < eyes['L'][0][1] + 0.6 * E)
    L = common(P, eyes['L'][0], eyes['R'][0], out['mouthL'], out['mouthR'], front, skin)
    # ears: the skin's widest points near the eyes' height, the ear's middle
    for k, sg in (('earL', 1), ('earR', -1)):
        s = skin & (P[:, 0] * sg > 0) & (np.abs(P[:, 2] - L['eyeL'][2] + 0.4 * E) < 1.1 * E)
        x = P[s, 0] * sg
        sel = P[s][x > np.percentile(x, 93)]
        L[k] = sel.mean(0)
    return L, dict(skin=skin, eyeL=eyes['L'][2], eyeR=eyes['R'][2], teeth=teeth, eye_r=(eyes['L'][1] + eyes['R'][1]) / 2)

def mh_landmarks(P, used, joint_c):
    """P: MH head points (figure axes); used: the head's vertex mask; joint_c: {joint group: centre}."""
    eyeL, eyeR = joint_c['joint-l-eye'], joint_c['joint-r-eye']
    i, d = read_target('mouth/mouth-angles-up.target')
    mag = np.linalg.norm(d, axis=1)
    out = {}
    for k, sg in (('mouthL', 1), ('mouthR', -1)):
        s = (P[i, 0] * sg > 0)
        top = i[s][np.argsort(-mag[s], kind='stable')[:4]]
        out[k] = P[top].mean(0)
    E = np.linalg.norm(eyeL - eyeR)
    front = used & (P[:, 1] < eyeL[1] + 0.6 * E)
    L = common(P, eyeL, eyeR, out['mouthL'], out['mouthR'], front, used)
    for k, f in (('earL', 'ears/l-ear-scale-incr.target'), ('earR', 'ears/r-ear-scale-incr.target')):
        i, d = read_target(f)
        w = np.linalg.norm(d, axis=1)
        L[k] = (P[i] * w[:, None]).sum(0) / w.sum()
    return L
