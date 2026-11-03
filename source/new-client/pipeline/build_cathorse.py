"""The Catacombs horses (owner 2026-11-02: the personal mounts' own models): one skinned figure, every part.

    python build_cathorse.py [--no-upscale]

horsemap.csv's mounts (2033 standard, 2035 heavy, 2037 unicorn, 2034 nightmare, 2036 undead) are the client's
fig3 'Horse_Medium' figure (monnifs 751 Hawsie / 755 Clydesdale / 747 Unicorn / 737 Nightmare / 756 Undead, anim set
315 'Cata Horse': the cathorse_*.kfa clips): skeleton figures/fig3/sfig003.mpk horse_medium_skeleton.nif, parts in
fig016.mpk - Body01_Mount_{Horse,Clydesdale,Unicorn,Nightmare,Undead} (the coat), Armor01_Mount_Horse (the saddle and
the armour) and Barding01_Mount_Horse (the barding). Each part is made of shapes named by a material id
('Armor01_Mount_Horse:53'); horsematerialmap.csv picks a list of ids per choice (meshmateriallist.csv: the saddle shows
7, 53, 14; light armour 7, 53, 9, 15, 16, 17 ...; a negative id is hidden). Every shape is its own node here,
'<part>_<id>' (body_horse_4, armor_53, barding_38), so the client shows a choice's ids and hides the rest.

Writes content/monsters/cathorse/model.gltf, cathorse.json (bodies, the material lists, clips, strides) and the coat /
saddle / barding textures (textures/original, x4plus).
"""
import csv, io, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from assets_pipeline import CLIENT, ROOT
from daoc_mpk import read_mpk
from texture_index import TextureIndex
import nif_character as nc

OUT = ROOT / 'godot/content/monsters/cathorse'
SKELETON = ('sfig003.mpk', 'horse_medium_skeleton.nif')
BODIES = {'horse': ('body01_mount_horse.nif', 'horse_medium_brown'),
          'clydesdale': ('body01_mount_clydesdale.nif', 'horse_heavy_clydesdale'),
          'unicorn': ('body01_mount_unicorn.nif', 'horse_medium_white'),
          'nightmare': ('body01_mount_nightmare.nif', 'horse_nightmare'),
          'undead': ('body01_mount_undead.nif', 'horse_undead')}
ARMOR = ('armor01_mount_horse.nif', 'armor_mount_plainsaddle')
BARDING = ('barding01_mount_horse.nif', 'barding_medium_blanket_guild')
CLIPS = {'Idle': 'idle', 'Walk': 'walk', 'Run': 'run', 'Back': 'walk_back', 'Crawl': 'swim', 'Jump': 'jump',
         'Land': 'land', 'Slide Left': 'strafe_left', 'Slide Right': 'strafe_right'}
ANIM_SET = 315
MONNIFS = 751                                            # 'Hawsie' (strides)
EXTRA_TEXTURES = ['armor_mount_heroic', 'armor_saddle_starter', 'horse_medium_brown_tack', 'horse_medium_black_tack',
                  'horse_medium_white_tack', 'mount_armor_heroic', 'mount_armor_albheroic', 'mount_armor_midheroic',
                  'mount_armor_hibheroic', 'mount_armor_hibsaddle', 'mount_armor_midsaddle', 'horse_heavy_armor',
                  'barding_medium_fullsock_guild', 'barding_medium_halfsock_guild', 'barding_medium_yellow']


def table(g, name):
    return list(csv.reader(io.StringIO(g[name].decode('latin1'))))


def main():
    g = read_mpk(str(CLIENT / 'gamedata.mpk'))
    parts = []
    for kind, (nif, tex) in BODIES.items():
        parts.append(('fig016.mpk', nif, tex, (1.0, 1.0, 1.0), f'body_{kind}_{{mat}}'))
    parts.append(('fig016.mpk', ARMOR[0], ARMOR[1], (1.0, 1.0, 1.0), 'armor_{mat}'))
    parts.append(('fig016.mpk', BARDING[0], BARDING[1], (1.0, 1.0, 1.0), 'barding_{mat}'))
    clips = {CLIPS[k]: v for k, v in nc.clip_files(ANIM_SET, tuple(CLIPS)).items() if k in CLIPS}
    OUT.mkdir(parents=True, exist_ok=True)
    report, textures = nc.build_cata(SKELETON, parts, clips, str(OUT / 'model.gltf'), 'textures/original')
    # the material lists: horsematerialmap (horse kind row, part 0 armour / 1 barding / 2 body, selection) -> its
    # meshmateriallist ids
    mats = {r[0]: [int(x) for x in r[2:] if x.strip().lstrip('-').isdigit()]
            for r in table(g, 'meshmateriallist.csv') if r and r[0].isdigit()}
    choices = {}
    for r in table(g, 'horsematerialmap.csv'):
        if not r or not r[0].isdigit():
            continue
        choices.setdefault(r[0], {}).setdefault({'0': 'armor', '1': 'barding', '2': 'body'}.get(r[2], r[2]), []).append(
            {'label': r[1].split(':', 1)[-1].strip(), 'selection': int(r[3]), 'ids': mats.get(r[4], [])})
    mn = {r[0]: r for r in table(g, 'monnifs.csv') if r and r[0].isdigit()}[str(MONNIFS)]
    meta = {'gltf': 'res://content/monsters/cathorse/model.gltf', 'bodies': {k: v[1] for k, v in BODIES.items()},
            'armor_tex': ARMOR[1], 'barding_tex': BARDING[1], 'choices': choices,
            'clip_seconds': {k: v['seconds'] for k, v in report.items()},
            'strides_units': {'run': float(mn[4]), 'walk': float(mn[5]), 'back': float(mn[6]), 'strafe': float(mn[7])}}
    idx = TextureIndex()
    idx.figures_first = True
    (OUT / 'textures/original').mkdir(parents=True, exist_ok=True)
    coats = json.loads((ROOT / 'godot/content/monsters/mount_coats.json').read_text()) \
        if (ROOT / 'godot/content/monsters/mount_coats.json').exists() else {}
    for name in sorted({t.lower() for t in textures} | set(EXTRA_TEXTURES) | set(coats.values())):
        img = idx.image(name)
        if img is None:
            print('texture', name, 'NOT FOUND')
            continue
        img.save(OUT / 'textures/original' / f'{name}.png')
    (OUT / 'cathorse.json').write_text(json.dumps(meta, indent=1))
    if '--no-upscale' not in sys.argv:
        from build_zone import upscale_dir
        upscale_dir(OUT / 'textures/original', OUT / 'textures/x4plus', factor_after=4)
        gl = (OUT / 'model.gltf').read_text(encoding='utf-8').replace('"textures/original/', '"textures/x4plus/')
        (OUT / 'model.gltf').write_text(gl, encoding='utf-8')
    print('cathorse:', {k: v['seconds'] for k, v in report.items()}, len(textures), 'textures')


if __name__ == '__main__':
    main()
