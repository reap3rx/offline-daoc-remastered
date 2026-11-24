"""Dergan Island's camp goods (claude 2026-11-22, the Lough Derg plan's Phase 6): story_items.py on
named_uniques/isl200_dergan_island.json (jewellery and cloaks at every level, open to every class), the cloak of the taken
isle given its emblem (the whirlpool, h_emblem_024, on red), then the Mardagh alchemist's draughts: copies of the
realm's own potions under fae names, at their coin prices. All of it into
source/server/GameServer/scripts/storyquests/items/isl200_dergan_island.json (the server adds them at start).

  python tools/claude-version/island_items.py named_uniques/isl200_dergan_island.json
"""
import json, sqlite3, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import named_uniques as nu

EMBLEM = (104 << 9) | (3 << 7) | (0 << 3) | 0          # logo 104 (h_emblem_024, the spiral), solid primary red
POTIONS = [  # source template, new id, name, words
    ('Strong_Draught_of_Healing', 'isl200_glowcap_draught', 'Glowcap Draught', 'Glowcaps from the Mardagh woods, steeped in mere-water. It heals; it also glows a bit.'),
    ('Strong_Draught_of_Power', 'isl200_mere_dew_tonic', 'Mere-Dew Tonic', 'Dew gathered off the Lady\'s mere before sunrise. For the mind more than the body.'),
    ('Strong_Draught_of_Endurance', 'isl200_fae_fire_cordial', 'Fae-Fire Cordial', 'Burns going down. The fae drink it neat; you probably shouldn\'t.'),
    ('Superior_Elixir_of_Instant_Healing', 'isl200_red_lake_elixir', 'Red Lake Elixir', 'Mardagh\'s best: a draught for when the fight is going badly and fast.'),
    ('CombinedRegens_Draught', 'isl200_blackthorn_brew', 'Blackthorn Brew', 'Blackthorn, rowan and something the alchemist won\'t name. Everything comes back a little faster.'),
]

spec = sys.argv[1]
subprocess.run([sys.executable, str(HERE / 'story_items.py'), spec], check=True)
out = HERE.parents[1] / 'source/server/GameServer/scripts/storyquests/items' / (Path(spec).stem + '.json')
rows = json.loads(out.read_text(encoding='utf-8'))
for r in rows:
    r['AllowedClasses'] = ''
    if r['Id_nb'].startswith('isl200_cloak_of_the_taken_isle'):
        r['Emblem'] = EMBLEM
        r['Color'] = 0
db = sqlite3.connect('file:%s?mode=ro' % nu.DB.as_posix(), uri=True)
cols = [d[0] for d in db.execute('select * from ItemTemplate limit 0').description]
n = 0
for src, nid, name, words in POTIONS:
    b = db.execute('select * from ItemTemplate where Id_nb=?', (src,)).fetchone()
    if b is None:
        print('missing', src)
        continue
    d = dict(zip(cols, b))
    d.pop('LastTimeRowUpdated', None)
    d.update(Id_nb=nid, ItemTemplate_ID=nid, Name=name, Description=words, PackageID='isl200', Realm=0, TranslationId='')
    rows.append(d)
    n += 1
out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding='utf-8')
print('%d rows (%d draughts) -> %s' % (len(rows), n, out))
