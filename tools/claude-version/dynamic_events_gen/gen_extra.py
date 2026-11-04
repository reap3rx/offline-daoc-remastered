"""Adds specs_extra.py's chains to the zones' existing event files (claude 2026-11-04) without touching the chains
already there: each new chain is built as gen.py builds one (kept clear of every place the zone's events already use),
gets its occupation stages (occupations.py: o1 / o2 when it fails), and a unique reward on its last boss
(rewards.py's rule, appended to the zone's named_uniques spec). Then run dynamic_events_fill_z.py on each file and
named_uniques.py --apply on each spec (server closed).

  python gen_extra.py <zones dir> <named_uniques dir> [zone ...]
Needs DAOC_SURVEY, DAOC_DB and DAOC_ZONES as gen.py. Re-running replaces the chains it added (same ids).
"""
import hashlib, json, os, re, sys
from pathlib import Path

sys.argv, ARGS = sys.argv[:1], sys.argv[1:]             # (gen.py reads its own argv at import)
import gen
import occupations
import rewards
from specs_extra import X

zones_dir, uniques_dir = Path(ARGS[0]), Path(ARGS[1])
only = [int(a) for a in ARGS[2:]]

for zid, specs in X.items():
    if only and zid not in only:
        continue
    f = next(zones_dir.glob('zone%03d_*.json' % zid))
    doc = json.loads(f.read_text(encoding='utf-8'))
    new_ids = {'%s_%s' % (gen.Z[zid]['file'], s['id']) for s in specs}
    doc['chains'] = [c for c in doc['chains'] if c['id'] not in new_ids]
    g = gen.ZoneGen(zid)
    used = []
    for c in doc['chains']:
        for st in c['stages']:
            if st.get('center'):
                used.append(tuple(st['center'][:2]))
        if c.get('giver', {}).get('pos'):
            used.append(tuple(c['giver']['pos'][:2]))
    g.used = list(used)
    t = g.t
    spec_path = next(uniques_dir.glob('zone%03d_*.json' % zid))
    uspec = json.loads(spec_path.read_text(encoding='utf-8'))
    for spec in specs:
        try:
            c = g.chain(spec)
        except SystemExit as e:
            if spec['kind'] != 'giver':
                print('   !!', e)
                continue
            # no road from the town to a camp of them: the same fight as a camp that starts on its own
            print('   !!', e, '- made a camp instead')
            spec = dict(spec, kind='camp', hint=spec.get('hint') or 'Trouble is brewing near %s...' % spec.get('town', 'town'),
                        why=spec['why'].split(' leads ')[0] + ' needs help: ' + spec['place'] + ' must be cleared.')
            c = g.chain(spec)
        # its failure: the occupation stages, as every other chain has them
        occ_used = list(g.used) + [tuple(st['center'][:2]) for cc in doc['chains'] for st in cc['stages'] if st['id'] in ('o1', 'o2') and st.get('center')]
        built = occupations.build(doc, c, g.s, t, occ_used)
        if built:
            c['stages'] += list(built)
            for st in c['stages']:
                if st['id'] in ('o1', 'o2'):
                    continue
                if st['type'] in ('boss', 'escort') or (st['type'] == 'defend' and st.get('protect_leader')):
                    st['on_fail'] = 'o1'
        # its unique, on the last boss (rewards.py's rule)
        i = len(doc['chains'])
        boss = [s for s in c['stages'] if s['type'] == 'boss'][-1]
        h = int(hashlib.md5(c['id'].encode()).hexdigest(), 16)
        base, words = rewards.SLOTS[h % len(rewards.SLOTS)]
        theme = rewards.FALLBACK_THEMES[rewards.REALM(zid)][(h // 7 + i) % 6]
        level = max(5, min(50, c['levels'][1] + 3))
        bname = boss['boss']['name']
        name = '%s %s' % (rewards.possessive(bname), words[(h // 3) % len(words)])
        bon = {k: max(1, round(v * level / 50)) for k, v in rewards.THEMES[theme].items()}
        iid = '%s_%s' % (uspec.get('prefix', 'nu%d' % zid), rewards.slug(name))
        uspec['items'] = [it for it in uspec['items'] if it.get('event_reward') != c['id']]
        uspec['items'].append({'event_reward': c['id'], 'scaled': True, 'name': name, 'base': list(base), 'level': level,
                               'bonuses': bon, 'lore': 'Won from %s when %s was ended.' % (re.sub(r'^The ', 'the ', bname), c['title'])})
        boss['reward'] = dict(boss.get('reward') or {}, items=[{'id': iid, 'gold_chance': 40, 'silver_chance': 20}])
        doc['chains'].append(c)
        at = c['stages'][0].get('center') or c['giver']['pos']
        print(zid, c['id'], c['levels'], 'at', at[:2], '| fails to', built[0]['center'] if built else None, '|', name)
    f.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding='utf-8')
    spec_path.write_text(json.dumps(uspec, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
