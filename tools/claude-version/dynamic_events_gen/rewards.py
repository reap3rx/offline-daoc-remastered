"""One unique per event chain, its boss's reward (owner 2026-11-02: "make the uniques"): a cloak, belt, bracer, ring,
necklace or jewel - no class or armour type in the way - named for the boss, at the chain's level with level versions
every 5 levels (named_uniques.py "scaled"), handed out by the event to its gold (40%) and silver (20%) contributors.

  python rewards.py <zones dir> <named_uniques dir>

Writes named_uniques/zoneNNN_<name>.json (prefix nu<zone>) and puts the item on each chain's last boss stage; the
zone files keep everything else. Apply each spec with named_uniques.py --apply while the server is closed.
"""
import hashlib, json, re, sys
from pathlib import Path

SLOTS = [  # (Object_Type, Item_Type), the word for it
    ((41, 26), ['Cloak', 'Mantle', 'Shroud']),
    ((41, 32), ['Girdle', 'Belt', 'Sash']),
    ((41, 33), ['Bracer', 'Armband', 'Wristguard']),
    ((41, 35), ['Ring', 'Band', 'Signet']),
    ((41, 29), ['Torc', 'Pendant', 'Amulet']),
    ((41, 24), ['Stone', 'Jewel', 'Eye']),
]
THEMES = {  # bonuses at level 50 (named_uniques scales them down and caps them by level)
    'might':   {'Str': 15, 'Con': 15, 'Dex': 9, 'Hits': 40},
    'guile':   {'Dex': 15, 'Qui': 15, 'Str': 9, 'Hits': 30},
    'ward':    {'Con': 15, 'Hits': 50, 'Body': 6, 'Crush': 6, 'Slash': 6},
    'lore':    {'Int': 15, 'Dex': 9, 'Power': 6, 'Hits': 30},
    'faith':   {'Pie': 15, 'Con': 9, 'Power': 6, 'Hits': 30},
    'song':    {'Cha': 15, 'Emp': 12, 'Qui': 9, 'Hits': 30},
}
REALM = lambda z: 1 if z < 100 else 2 if z < 200 else 3
FALLBACK_THEMES = {1: ['might', 'guile', 'ward', 'lore', 'faith', 'song'],
                   2: ['might', 'ward', 'guile', 'faith', 'lore', 'song'],
                   3: ['guile', 'song', 'lore', 'might', 'ward', 'faith']}


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def possessive(name):
    n = re.sub(r'^The ', '', name)
    return n + ("'" if n.endswith('s') else "'s")


def main():
    zones, out = Path(sys.argv[1]), Path(sys.argv[2])
    for f in sorted(zones.glob('zone*.json')):
        doc = json.loads(f.read_text(encoding='utf-8'))
        z = doc['zone']
        if z == 206:
            continue                                   # Bri Leith has its own hand-made spec
        prefix = 'nu%d' % z
        items = []
        for i, c in enumerate(doc['chains']):
            boss = [s for s in c['stages'] if s['type'] == 'boss'][-1]
            h = int(hashlib.md5(c['id'].encode()).hexdigest(), 16)
            (base, words) = SLOTS[h % len(SLOTS)]
            theme = FALLBACK_THEMES[REALM(z)][(h // 7 + i) % 6]
            level = max(5, min(50, c['levels'][1] + 3))
            bname = boss['boss']['name']
            name = '%s %s' % (possessive(bname), words[(h // 3) % len(words)])
            bon = {k: max(1, round(v * level / 50)) for k, v in THEMES[theme].items()}
            items.append({'event_reward': c['id'], 'scaled': True, 'name': name, 'base': list(base), 'level': level,
                          'bonuses': bon, 'lore': 'Won from %s when %s was ended.' % (re.sub(r'^The ', 'the ', bname), c['title'])})
            iid = '%s_%s' % (prefix, slug(name))
            boss['reward'] = dict(boss.get('reward') or {}, items=[{'id': iid, 'gold_chance': 40, 'silver_chance': 20}])
        spec = {'zone': z, 'region': doc['region'], 'realm': REALM(z), 'prefix': prefix, 'respawn_s': 900, 'items': items}
        (out / f.name).write_text(json.dumps(spec, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
        f.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding='utf-8')
        print(z, len(items), ', '.join(i['name'] for i in items))


if __name__ == '__main__':
    main()
