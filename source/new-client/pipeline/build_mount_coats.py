"""The personal mounts' coats (owner 2026-11-02: "convert the mount models to the new client").

horsemap.csv gives each horse a monster model (2033 standard, 2035 heavy, 2037 unicorn ...) and a coat: a column of
fig3haircolormap.csv's row for that kind of horse (48 Standard, 50 Heavy, 52 Unicorn, 49 Nightmare, 51 Undead,
53 Epic), whose skins.csv id names the coat texture (Horse_Medium_Brown, Horse_Medium_palamino, Horse_Spotted ...).
Those models are the Catacombs part horses (Body01_Mount_Horse, Armor01_Mount_Horse saddle, Barding01_Mount_Horse),
whose meshes this client doesn't carry (only their cathorse_*.kfa clips); monsters.csv draws all of them with the
classic saddled horse (figure 784, Classic_Body01_Mount_Horse), whose own skin is Horse_Medium_Brown - the same UV
layout as every Horse_Medium_* coat. So each coat is written next to that horse's built model and the client swaps
it in (game/world/mounts.gd):

    content/monsters/classic_body01_mount_horse__horse_medium_brown/coats/{original,x4plus}/<coat>.png
    content/monsters/mount_coats.json        {horse id: coat name} for the coats that fit the classic horse

    python build_mount_coats.py [--no-upscale] [--sheet=<png>]
"""
import csv, io, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from assets_pipeline import CLIENT, ROOT
from daoc_mpk import read_mpk
from texture_index import TextureIndex

OUT = ROOT / 'godot/content/monsters'
HORSE = 'classic_body01_mount_horse__horse_medium_brown'
ROWS = {'2033': '48', '2035': '50', '2037': '52', '2184': '52', '2164': '52', '2223': '52',
        '2034': '49', '2036': '51'}
# every horse's coat: the Catacombs bodies (build_cathorse.py) take them all; the classic saddled horse (the fallback)
# only the Horse_Medium_* family, spotted, Clydesdale and Arboreal (its UV layout - mounts.gd keeps the others off it)
FITS = ('horse_medium_', 'horse_spotted', 'horse_heavy_clydesdale', 'arboreal_horse')


def table(g, name):
    return list(csv.reader(io.StringIO(g[name].decode('latin1'))))


def main():
    g = read_mpk(str(CLIENT / 'gamedata.mpk'))
    skins = {r[0]: r[1].rsplit('.', 1)[0] for r in table(g, 'skins.csv') if r and r[0].isdigit()}
    hair = {r[0]: [r[i] for i in range(3, len(r), 3)] for r in table(g, 'fig3haircolormap.csv') if r and r[0].isdigit()}
    coats = {}
    for r in table(g, 'horsemap.csv'):
        if not r or not r[0].isdigit() or r[2] not in ROWS:
            continue
        cols = hair.get(ROWS[r[2]], [])
        i = int(r[3] or 0)
        name = skins.get(cols[i].strip(), '') if i < len(cols) else ''
        if name:
            coats[int(r[0])] = name.lower()
    idx = TextureIndex()
    idx.figures_first = True
    d = OUT / HORSE / 'coats'
    (d / 'original').mkdir(parents=True, exist_ok=True)
    made = {}
    for name in sorted(set(coats.values())):
        img = idx.image(name)
        if img is None:
            print('coat', name, 'NOT FOUND')
            continue
        img.convert('RGB').save(d / 'original' / f'{name}.png')
        made[name] = img.size
        print('coat', name, img.size)
    coats = {k: v for k, v in coats.items() if v in made}
    (OUT / 'mount_coats.json').write_text(json.dumps({str(k): v for k, v in sorted(coats.items())}, indent=1))
    if '--no-upscale' not in sys.argv:
        from build_zone import upscale_dir
        upscale_dir(d / 'original', d / 'x4plus', factor_after=4)
    sheet = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--sheet=')), None)
    if sheet:
        from PIL import Image, ImageDraw
        names = sorted(made)
        t = 256
        out = Image.new('RGB', (t * 6, (t + 16) * ((len(names) + 5) // 6)), 'white')
        for i, n in enumerate(names):
            im = Image.open(d / 'original' / f'{n}.png').resize((t, t))
            x, y = (i % 6) * t, (i // 6) * (t + 16)
            out.paste(im, (x, y + 16))
            ImageDraw.Draw(out).text((x + 2, y + 2), n, fill='black')
        out.save(sheet)
    print(len(coats), 'horses,', len(made), 'coats')


if __name__ == '__main__':
    main()
