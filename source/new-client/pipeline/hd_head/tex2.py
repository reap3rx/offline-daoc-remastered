"""The HD head's textures (v2), in its own layout (MakeHuman's head UVs repacked, hd_layout.py):

  hd_base.png    the skin: MakeHuman's CC0 skin for its features and detail (the lips, lids, nostrils, ears - drawn
                 for this very mesh), each race's own colouring from its classic face - only the colouring: the
                 classic face blurred to its tones, its painted eyes, lips and ears left out; close to the neck's
                 edge the classic skin itself, so the neck runs into the body without a line.
  hd_remap.png   each texel's place on the classic face texture (16 bits a coordinate): the client reads the brows,
                 freckles, scars, war paint and tattoos through it.
  hd_detail.png  the relief (r: height - pores, creases; a: the creases' shade).
Shared by every race (written once, beside the races): hd_eye.png (the eyeball: a: the iris, grey - the client
colours it), hd_mouth.png (teeth | tongue), hd_lash.png.
"""
import json
from pathlib import Path
import numpy as np, cv2
import hd_tex, mh2
from fit2 import vnormals

SIZE = hd_tex.SIZE
SHADE = 0.42                            # how dark the face's own shade goes at its deepest
SMOOTH = 0.05                           # the skin's smooth scale (of a head unit): finer than this is pores and speckle
# a race whose classic face is painted with deep shading of its own (the Firbolg man's cheeks, owner 2026-11-25): its
# tones taken wider, the shading left out (the new head shades itself)
TONE_WIDE = {'fir_m': 3.0}
SKINS = {'male': 'skins/young_caucasian_male/young_lightskinned_male_diffuse.png',
         'female': 'skins/young_caucasian_female/young_lightskinned_female_diffuse.png'}


def find_race_file(folder, name):
    prefix = Path(folder).resolve().name.replace('src_', '')
    for base in (Path(folder), Path(r'E:\Offline DAOC 036c\playable-v0.36c\new-client\godot\content\characters\races') / prefix,
                 Path('/mnt/user-data/uploads/Offline DAOC 036c/playable-v0.36c/new-client/godot/content/characters/races') / prefix):
        f = base / name
        if f.exists():
            return f
    return None


def mblur(img, mask, sigma):
    """A blur that only mixes what the mask holds (and fills what it doesn't from round it)."""
    m = mask.astype(np.float32)
    num = cv2.GaussianBlur(img * m[..., None], (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)
    return num / np.maximum(den, 1e-4)[..., None], den


def fill(img, mask):
    """What the mask doesn't hold filled from the nearest it does (wide blurs first, finer after)."""
    out = img.copy(); have = mask.copy()
    for sigma in (6, 16, 48, 128):
        b, den = mblur(out, have, sigma)
        new = (~have) & (den > 0.02)
        out[new] = b[new]; have = have | new
    return out


def bake(res, folder, out_folder, log=print):
    Q, T, UV, UVM = res['Q'], res['T'], res['UV'], res['UVM']
    h, parts, L, info, mh = res['h'], res['parts'], res['L'], res['info'], res['mh']
    out_folder = Path(out_folder)
    cTs = h['T'][parts['skin'][h['T']].all(1)]
    f_seam, _, _ = res['seam'].f(Q)
    # per-point marks: the eyes' region, the ears, the lips (MakeHuman's own)
    P0 = mh['P']
    def base_attr(a):
        return (a[res['CI']] * res['CW']).sum(1)
    eye_m = np.zeros(len(P0))
    for sd in 'LR':
        c, r = mh['eyes'][sd]
        eye_m = np.maximum(eye_m, np.clip((1.9 - np.linalg.norm(P0 - c, axis=1) / r) / 0.5, 0, 1))
    ear_m = np.clip(mh['ear']['L'] + mh['ear']['R'], 0, 1)
    lip_m = np.zeros(len(P0))
    from mhbase import read_target
    for nm in ('mouth/mouth-upperlip-volume-incr', 'mouth/mouth-lowerlip-volume-incr'):
        i, d = read_target(nm + '.target'); mg = np.linalg.norm(d, axis=1)
        lip_m[i] = np.maximum(lip_m[i], np.clip(mg / (0.35 * mg.max()), 0, 1))
    # the scalp (above the brows and behind the ears' line): MakeHuman's skin there is speckled with shaved hair
    E = info['E']; em = (L['eyeL'] + L['eyeR']) / 2
    scalp = np.clip((Q[:, 2] - (L['browL'][2] + 0.45 * E)) / (0.5 * E), 0, 1)
    scalp = np.maximum(scalp, np.clip((Q[:, 1] - (em[1] + 1.5 * E)) / (0.6 * E), 0, 1) * np.clip((Q[:, 2] - (em[2] - 1.2 * E)) / (0.5 * E), 0, 1))
    # the face's own shade: where the head dips in at the scale of its features (the eye sockets, the nose's sides,
    # under the lip, the ear's bowl) - the painted faces drew this; here it is the mesh's
    from fit2 import adjacency
    grp = res['grp']; ng = grp.max() + 1
    Ag = adjacency(grp[T], ng)
    Pg = np.zeros((ng, 3)); Pg[grp] = Q
    Ng = np.zeros((ng, 3)); np.add.at(Ng, grp, res['N']); Ng /= np.maximum(np.linalg.norm(Ng, axis=1, keepdims=True), 1e-9)
    shade = np.zeros(ng); S_ = Pg.copy(); done = 0
    for n_it, depth in ((6, 0.05), (20, 0.14), (60, 0.35)):
        for _ in range(n_it - done):
            S_ = 0.5 * S_ + 0.5 * (Ag @ S_)
        done = n_it
        shade += np.clip(((S_ - Pg) * Ng).sum(1) / depth, 0, 1) / 3.0
    for _ in range(2):
        shade = 0.5 * shade + 0.5 * (Ag @ shade)
    shade = shade[grp] * np.clip(f_seam / 1.5, 0, 1)
    attrs = np.c_[Q, UVM, base_attr(eye_m), base_attr(ear_m), base_attr(lip_m), np.clip(f_seam, -1, 50), scalp, shade]
    img, mask = hd_tex.raster(UV, T, attrs)
    # 1. the remap
    Qm = img[mask][:, :3].astype(np.float64)
    cuv = np.zeros(img.shape[:2] + (2,), np.float32)
    cuv[mask] = hd_tex.classic_uv(Qm, h['P'], cTs, h['UV'])
    cuvp, wide = hd_tex.pad(cuv, mask, 12)
    cv2.imwrite(str(out_folder / 'hd_remap.png'), cv2.cvtColor(hd_tex.encode_remap(cuvp, wide), cv2.COLOR_RGBA2BGRA))
    names = {'remap': 'hd_remap'}
    # 2. the skin
    meta = json.loads((Path(folder) / 'figure.json').read_text(encoding='utf-8'))
    bname = (meta.get('skin_layers', {}) or {}).get('base', '')
    bf = find_race_file(folder, bname + '.png') if bname else None
    skin = cv2.imread(str(Path(mh2.SYS) / SKINS[res['sex']]), cv2.IMREAD_COLOR)
    x4 = Path(mh2.SYS) / (SKINS[res['sex']][:-4] + '_x4.png')
    if x4.exists():                                                 # (the same picture run through the upscaler)
        skin = cv2.imread(str(x4), cv2.IMREAD_COLOR)
    Hs, Ws = skin.shape[:2]
    full, _ = hd_tex.pad(img, mask, 12)
    mx = (full[..., 3] * Ws - 0.5).astype(np.float32); my = ((1 - full[..., 4]) * Hs - 0.5).astype(np.float32)
    M = cv2.remap(skin, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
    # texels per unit of the head (for the blurs' widths)
    a3 = np.linalg.norm(np.cross(Q[T[:, 1]] - Q[T[:, 0]], Q[T[:, 2]] - Q[T[:, 0]]), axis=1).sum() / 2
    u1 = UV[T[:, 1]] - UV[T[:, 0]]; u2 = UV[T[:, 2]] - UV[T[:, 0]]
    a2 = np.abs(u1[:, 0] * u2[:, 1] - u1[:, 1] * u2[:, 0]).sum() / 2
    ppu = np.sqrt(a2 / a3) * SIZE
    sig = 0.4 * ppu * TONE_WIDE.get(Path(folder).resolve().name.replace('src_', ''), 1.0)
    if bf is not None:
        base = cv2.imread(str(bf), cv2.IMREAD_COLOR)
        Hb, Wb = base.shape[:2]
        C = cv2.remap(base, (cuvp[..., 0] * Wb - 0.5).astype(np.float32), (cuvp[..., 1] * Hb - 0.5).astype(np.float32),
                      cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
        # the classic face's tones, without what it painted where the new head has its own: the eyes, lips, ears
        own = np.clip(np.maximum(np.maximum(full[..., 5], full[..., 6]), full[..., 7]), 0, 1)
        ok = wide & (own < 0.3)
        Cf = fill(C, ok)
        C_low, _ = mblur(Cf, wide, sig)
        M_low, _ = mblur(M, wide, sig)
        ratio = np.clip(M / np.maximum(M_low, 0.02), 0.25, 2.2)
        ratio = 1 + (ratio - 1) * (1 - 0.85 * np.clip(full[..., 9], 0, 1))[..., None]
        # smooth by default (the HD look, owner 2026-11-25: "I'd like to go for a smoother texture"): the skin's own
        # features (the lips, the lids, the nostrils) at their scale, its pores and speckle taken out - those go to
        # hd_detail's green, which the Skin Detail slider brings back
        ratio_s = cv2.GaussianBlur(ratio.astype(np.float32), (0, 0), SMOOTH * ppu)
        hf = np.clip((ratio / np.maximum(ratio_s, 0.05)).mean(-1), 0.5, 1.5)
        out = C_low * ratio_s
        # the neck's edge: the classic skin itself (the join shows no line), a little way up
        fs = np.clip(full[..., 8] / 1.6, 0, 1); fs = fs * fs * (3 - 2 * fs)
        # (softened a little way up from the edge: where the new neck stands well off the classic one - the Firbolg
        # man's - the nearest classic triangle jumps about, and its skin came out in steps)
        Cb, _ = mblur(C, wide, 0.08 * ppu)
        gs = np.clip(full[..., 8] / 0.5, 0, 1)[..., None]
        Cn = C * (1 - gs) + Cb * gs
        out = Cn * (1 - fs[..., None]) + out * fs[..., None]
        log('  skin: MakeHuman\'s detail in the race\'s own tones (%.0f texels a unit, tones over %.0f texels)' % (ppu, sig))
    else:
        out = M
        hf = np.ones(M.shape[:2], np.float32)
        log('  skin: MakeHuman\'s own (no classic base face found for the tones)')
    sh = np.clip(full[..., 10], 0, 1)
    out = out * (1 - SHADE * sh)[..., None] * (1 + 0.5 * SHADE * sh[..., None] * np.array([0.0, 0.0, 0.35]))   # (a warm shade)
    out8 = np.clip(out * 255, 0, 255).astype(np.uint8)
    cv2.imwrite(str(out_folder / 'hd_base.png'), out8)
    names['albedo'] = 'hd_base'
    # 3. the relief
    em = [L['eyeL'], L['eyeR']]
    mm = (L['mouthL'] + L['mouthR']) / 2
    det = hd_tex.detail(Q, T, UV, em, mm, L['nose'])
    # BGRA: r = the creases' height, g = the skin's fine colour (its pores, speckle: 128 = none), b = the pores'
    # height, a = the creases' shade
    hf8 = np.clip(128 + (hf - 1) * 255, 0, 255).astype(np.uint8)
    cv2.imwrite(str(out_folder / 'hd_detail.png'), np.dstack([det[..., 0], hf8, det[..., 2], det[..., 1]]))
    names['detail'] = 'hd_detail'
    # 4. the face maps (the HD look: brows, makeup, war paint, freckles drawn in face space)
    import mask3
    # the race's own painted brows (its default face's, from the classic skin layers) brought onto this head
    brow = None
    sl = meta.get('skin_layers', {}) or {}
    try:
        fm = (sl.get('face_map') or [{}])[0]
        opt = int(fm.get('brows', 1) or 1)
        chans = next(d['chan'] for d in sl.get('layers', []) if d['key'] == 'brows')
        ch = chans[max(opt, 1) - 1]
        bfile = find_race_file(folder, sl['tex'][ch // 4] + '.png')
        if bfile is not None:
            bim = cv2.imread(str(bfile), cv2.IMREAD_UNCHANGED)
            bm = bim[..., [2, 1, 0, 3][ch % 4]].astype(np.float32) / 255
            Hc, Wc = bm.shape
            brow = cv2.remap(bm, (cuvp[..., 0] * Wc - 0.5).astype(np.float32), (cuvp[..., 1] * Hc - 0.5).astype(np.float32),
                             cv2.INTER_LINEAR) * wide
    except (StopIteration, KeyError, IndexError, ValueError):
        brow = None
    fmap, mmap, finfo = mask3.maps(res, full, wide, M, full[..., 7], full[..., 9], log=log, brow=brow)
    cv2.imwrite(str(out_folder / 'hd_face.png'), fmap)
    cv2.imwrite(str(out_folder / 'hd_mask.png'), mmap)
    names['face'] = 'hd_face'; names['mask'] = 'hd_mask'; names['face_info'] = finfo
    if meta.get('tattoos'):                  # (a race with tattoos: their map in face space)
        tmap, trange = mask3.tattoo_map(res, full, wide, cuvp)
        cv2.imwrite(str(out_folder / 'hd_tattoo.png'), tmap)
        names['tattoo'] = 'hd_tattoo'; names['tattoo_range'] = trange
    names['uv_k'] = round(float(1.0 / max(res.get('lay_scale', 1.5), 1e-6)), 4)
    shared(out_folder.parent / '_hd_shared', log)
    return names


def shared(folder, log=print):
    """The eyeball, mouth and lash textures (the same for every race)."""
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    if not (folder / 'hd_brow_hair.png').exists():                  # (the HD look's brows: their hairs)
        import brows3
        brows3.make(folder / 'hd_brow_hair.png')
    if not (folder / 'hd_age.png').exists():                        # (the HD look's age lines and scars)
        import marks3
        marks3.make(folder)
    if not (folder / 'hd_eye_polar.png').exists() and (folder / 'hd_eye.png').exists():
        import eyes3                                                # (the HD look's eyes: the iris drawn)
        eyes3.make(folder, mh2.SYS)
    if (folder / 'hd_eye.png').exists() and (folder / 'hd_mouth.png').exists() and (folder / 'hd_lash.png').exists():
        return
    e = cv2.imread(str(Path(mh2.SYS) / 'eyes/materials/brown_eye.png'), cv2.IMREAD_UNCHANGED)[..., :3].astype(np.float32) / 255
    hsv = cv2.cvtColor(e, cv2.COLOR_BGR2HSV)
    # the iris: strongly coloured or dark, inside the eye's disc (the sclera is pale and grey-pink)
    iris = ((hsv[..., 1] > 0.45) | (hsv[..., 2] < 0.35)).astype(np.uint8)
    iris = cv2.morphologyEx(iris, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, stats, cen = cv2.connectedComponentsWithStats(iris)
    keep = np.zeros_like(iris)
    for i in np.argsort(-stats[1:, cv2.CC_STAT_AREA])[:2] + 1:      # (the two irises)
        cx, cy = cen[i]; rad = np.sqrt(stats[i, cv2.CC_STAT_AREA] / np.pi)
        cv2.circle(keep, (int(round(cx)), int(round(cy))), int(rad * 1.02), 1, -1)
    a = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 3.0)
    lum = e @ np.array([0.11, 0.59, 0.30], np.float32)
    m = keep > 0
    grey = np.clip(lum / max(np.percentile(lum[m], 92), 1e-3), 0, 1.2) ** 1.5   # (the iris's own light and dark, its fibres)
    out = np.zeros(e.shape[:2] + (4,), np.float32)
    scl = e.copy()
    out[..., :3] = scl * (1 - a[..., None]) + grey[..., None] * a[..., None]
    out[..., 3] = a
    out = cv2.resize(out, (512, 512), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(folder / 'hd_eye.png'), np.clip(out * 255, 0, 255).astype(np.uint8))
    import eyes3                                                    # (the HD look: the eye's white, the iris drawn)
    eyes3.make(folder, mh2.SYS)
    t = cv2.imread(str(Path(mh2.SYS) / 'teeth/teeth_base/teeth.png'), cv2.IMREAD_UNCHANGED)[..., :3]
    g = cv2.imread(str(Path(mh2.SYS) / 'tongue/tongue01/tongue01_diffuse.png'), cv2.IMREAD_COLOR)
    mo = np.hstack([cv2.resize(t, (512, 512), interpolation=cv2.INTER_AREA), cv2.resize(g, (512, 512), interpolation=cv2.INTER_AREA)])
    cv2.imwrite(str(folder / 'hd_mouth.png'), mo)
    la = cv2.imread(str(Path(mh2.SYS) / 'eyelashes/eyelashes01/eyelashes01.png'), cv2.IMREAD_UNCHANGED)
    la[..., 3] = np.clip(la[..., 3].astype(np.float32) * 1.25 - 76, 0, 255).astype(np.uint8)   # (thinned: fine lashes, not spikes)
    cv2.imwrite(str(folder / 'hd_lash.png'), la)
    log('  shared textures: hd_eye, hd_mouth, hd_lash')
