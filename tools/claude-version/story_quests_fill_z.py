"""Fills in the ground height (metres) of every place in a story-quest file (scripts/storyquests/quests/*.json):
people's pos, steps' at, encounter stages' center / from / pos - each by its zone. Outdoors from the new client's
height grid (as dynamic_events_fill_z.py); in a dungeon (no height grid of the ground) from the nearest of the zone's
NPC spawns (npcs.json), which stand on its floors.

  python tools\\claude-version\\story_quests_fill_z.py source\\server\\GameServer\\scripts\\storyquests\\quests\\alb_camelot_hills.json
"""
import json, math, sys
from pathlib import Path
import dynamic_events_fill_z as dz

ROOT = Path(__file__).resolve().parents[2]
_cache = {}


def height_fn(zone):
    if zone in _cache:
        return _cache[zone]
    d = ROOT / ('new-client/godot/content/zones/zone%03d' % zone)
    info = json.loads((d / 'zone.json').read_text(encoding='utf-8'))
    if not info.get('dungeon') and info.get('heights'):
        fn = dz.heights(zone, ROOT)
    else:
        npcs = json.loads((d / 'npcs.json').read_text(encoding='utf-8')).get('spawns', [])
        pts = [s['pos'] for s in npcs] + [s['pos'] for s in info.get('spots', [])]

        def fn(x, y):
            best = min(pts, key=lambda p: (p[0] - x) ** 2 + (p[2] - y) ** 2)
            return round(best[1], 1)
    _cache[zone] = fn
    return fn


def fix(p, zone):
    if isinstance(p, list) and len(p) >= 2 and zone is not None:
        h = height_fn(zone)(p[0], p[1])
        return [p[0], p[1], h] + p[3:4] if len(p) > 3 else [p[0], p[1], h]
    return p


def main():
    path = Path(sys.argv[1])
    doc = json.loads(path.read_text(encoding='utf-8'))
    for n in doc.get('npcs', []):
        n['pos'] = fix(n.get('pos'), n.get('zone', 0))
    for q in doc.get('quests', []):
        for st in q.get('steps', []):
            z = st.get('zone')
            if st.get('at'):
                st['at'] = fix(st['at'], z)
            for sd in st.get('stages', []):
                if sd.get('center'):
                    sd['center'] = fix(sd['center'], z)
                for key in ('waves', 'adds'):
                    w = sd.get(key)
                    if w and w.get('from'):
                        w['from'] = [fix(f, z) for f in w['from']]
                for key in ('protect', 'boss'):
                    if sd.get(key) and sd[key].get('pos'):
                        sd[key]['pos'] = fix(sd[key]['pos'], z)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('heights filled:', path)


if __name__ == '__main__':
    main()
