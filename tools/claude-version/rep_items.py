"""Reputation quartermasters' items (claude 2026-11-22, scripts/reputation): story_items.py on a spec
(named_uniques/repNNN_<zone>.json - made like the story items: name, slot, level, kind, lore), then every row is open to
every class and the Legend pieces (by id start, given after the spec) are a quarter stronger and can't be traded.

  python tools/claude-version/rep_items.py named_uniques/rep200_lough_derg.json rep200_mantle_of_the_red_hand_breaker rep200_mantle_of_the_lucht_feasa
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = sys.argv[1]
legend = tuple(sys.argv[2:])
subprocess.run([sys.executable, str(HERE / 'story_items.py'), spec], check=True)
out = HERE.parents[1] / 'source/server/GameServer/scripts/storyquests/items' / (Path(spec).stem + '.json')
rows = json.loads(out.read_text(encoding='utf-8'))
for r in rows:
    r['AllowedClasses'] = ''
    if legend and r['Id_nb'].startswith(legend):
        for i in range(1, 11):
            k = 'Bonus%d' % i
            if r.get(k) and r.get(k + 'Type'):
                r[k] = int(round(r[k] * 1.25))
        r['Description'] = (r.get('Description') or '') + " (A Legend's own: only its faction's Legends are sold one.)"
        r['IsTradable'] = 0
out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding='utf-8')
print('%d rows, %d legend' % (len(rows), sum(1 for r in rows if legend and r['Id_nb'].startswith(legend))))
