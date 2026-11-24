"""A siege camp's goods, any zone (claude 2026-11-22; island_items.py made general for the Wicker Fields): story_items.py
on the spec, every row open to every class, the camp cloak (the spec's "camp": "cloak" id start) given its emblem, then the
coin vendor's draughts - copies of the realm's own potions under the camp's names, at their coin prices.

  python tools/claude-version/camp_items.py named_uniques/wf207_wicker_fields.json

The spec's "camp" block: {"cloak": "<id start>", "emblem": <int>, "draughts": [[source template, new id, name, words], ...]}
"""
import json, sqlite3, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import named_uniques as nu

spec_path = Path(sys.argv[1]) if Path(sys.argv[1]).is_absolute() else HERE / sys.argv[1]
camp = json.loads(spec_path.read_text(encoding='utf-8')).get('camp', {})
subprocess.run([sys.executable, str(HERE / 'story_items.py'), str(spec_path)], check=True)
out = HERE.parents[1] / 'source/server/GameServer/scripts/storyquests/items' / (spec_path.stem + '.json')
rows = json.loads(out.read_text(encoding='utf-8'))
for r in rows:
    r['AllowedClasses'] = ''
    if camp.get('cloak') and r['Id_nb'].startswith(camp['cloak']):
        r['Emblem'] = camp['emblem']
        r['Color'] = 0
db = sqlite3.connect('file:%s?mode=ro' % nu.DB.as_posix(), uri=True)
cols = [d[0] for d in db.execute('select * from ItemTemplate limit 0').description]
n = 0
for src, nid, name, words in camp.get('draughts', []):
    b = db.execute('select * from ItemTemplate where Id_nb=?', (src,)).fetchone()
    if b is None:
        print('missing', src)
        continue
    d = dict(zip(cols, b))
    d.pop('LastTimeRowUpdated', None)
    d.update(Id_nb=nid, ItemTemplate_ID=nid, Name=name, Description=words, PackageID=nid.split('_')[0], Realm=0, TranslationId='')
    rows.append(d)
    n += 1
out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding='utf-8')
print('%d rows (%d draughts) -> %s' % (len(rows), n, out))
