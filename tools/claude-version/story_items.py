"""Story quest rewards (scripts/storyquests): a named_uniques-style spec of items (named_uniques/storyNNN_*.json:
name, base slot, level, bonuses, lore, "scaled" for level versions) turned into full ItemTemplate rows, written to
source/server/GameServer/scripts/storyquests/items/<spec name>.json. The server puts them into its database at every
start (StoryItemsUpdate, a DatabaseUpdate - added when missing, set right when changed), so they reach every copy of
the world without touching a save. Needs a database copy only to pick each item's look (its base item).

  python tools\\claude-version\\story_items.py named_uniques\\story000_camelot_hills.json
"""
import json, sys
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import named_uniques as nu

spec_path = Path(sys.argv[1]) if Path(sys.argv[1]).is_absolute() else HERE / sys.argv[1]
spec = json.loads(spec_path.read_text(encoding='utf-8'))
db = sqlite3.connect('file:%s?mode=ro' % nu.DB.as_posix(), uri=True)
cols, items = nu.plan(db, spec)
rows = []
for it, row, _ in items:
    row = dict(row)
    row.pop('LastTimeRowUpdated', None)
    rows.append(row)
out = nu.ROOT / 'source/server/GameServer/scripts/storyquests/items' / (spec_path.stem + '.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding='utf-8')
print('%d rows (%d items) -> %s' % (len(rows), len(spec['items']), out))
