"""Story quests written short (claude 2026-11-05, owner: "pushing through quests for the rest of the zones ... Multi
stage, taking you to unique and relatively unused parts of the map, good story, choices, nice rewards. Higher level
quests can be more stages"): a realm's quests as Python (story_<realm>.py, beside this) with the helpers below, written
out as the server's files - scripts/storyquests/quests/<realm>_<zone>.json - and each zone's reward spec,
named_uniques/storyNNN_<zone>.json (then story_items.py turns the spec into item rows, story_quests_fill_z.py gives
the places their heights).

    python tools/claude-version/story_gen.py story_alb story_mid story_hib
"""
import importlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QDIR = ROOT / 'source/server/GameServer/scripts/storyquests/quests'
SPECS = HERE / 'named_uniques'

REALM_MODELS = {1: {'m': 9, 'f': 38, 'old': 32}, 2: {'m': 213, 'f': 168, 'old': 157}, 3: {'m': 337, 'f': 365, 'old': 362}}
MIND = {1: ('Int', 'Pie'), 2: ('Pie', 'Int'), 3: ('Int', 'Emp')}
SLOTS = {'ring': 35, 'neck': 29, 'belt': 32, 'cloak': 26, 'bracer': 33, 'gem': 24}


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


# ------------------------------------------------------------------ the zone being written
class Zone:
    def __init__(self, zone, name, realm, file):
        self.zone, self.name, self.realm, self.file = zone, name, realm, file
        self.npcs, self.quests, self.items = [], [], []
        self.labels = {}

    def prefix(self):
        return 'sq%d' % self.zone

    # people
    def npc(self, id, name, at, kind='m', level=None, model=None, guild=None, idle=None, during=None, zone=None, size=None,
            hostile=False):
        n = {'id': id, 'zone': self.zone if zone is None else zone, 'realm': self.realm, 'name': name,
             'model': model or REALM_MODELS[self.realm].get(kind, 9), 'level': level or 20, 'pos': list(at)}
        if guild:
            n['guild'] = guild
        if idle:
            n['idle'] = idle
        if during:
            n['during'] = during
        if size:
            n['size'] = size
        if hostile:
            n['hostile'] = True
        self.npcs.append(n)
        return id

    # rewards: an item of the zone's, its bonuses from its kind and level
    def item(self, name, slot, level, kind, lore):
        L = max(5, level)
        a, b = max(1, round(L / 3)), max(1, round(L / 6))
        hits = round(L * 0.85)
        if kind == 'might':
            bon = {'Str': a, 'Con': a, 'Dex': b, 'Hits': hits}
        elif kind == 'finesse':
            bon = {'Dex': a, 'Qui': a, 'Str': b, 'Hits': hits}
        elif kind == 'mind':
            m1, m2 = MIND[self.realm]
            bon = {m1: a, m2: b, 'Dex': b, 'Power': max(1, round(L / 7)), 'Hits': round(L * 0.6)}
        elif kind == 'faith':
            m1, m2 = MIND[self.realm][::-1]
            bon = {m1: a, 'Con': b, 'Power': max(1, round(L / 7)), 'Hits': round(L * 0.6)}
        elif kind == 'ward':
            r = max(1, round(L / 8))
            bon = {'Con': a, 'Hits': round(L * 1.0), 'Body': r, 'Crush': r, 'Slash': r}
        elif kind == 'charm':
            bon = {'Qui': a, 'Con': b, 'Dex': b, 'Hits': round(L * 0.6), 'Power': max(1, round(L / 9))}
        else:
            raise SystemExit('item kind ' + kind)
        self.items.append({'story_reward': True, 'scaled': True, 'name': name, 'base': [41, SLOTS[slot]],
                           'level': min(50, L), 'bonuses': bon, 'lore': lore})
        return '%s_%s' % (self.prefix(), slug(name))

    def quest(self, id, title, level, giver, offer, accept, summary, steps, endings, topics=None, group=False,
              requires=None, decline=None, xp=None, marks=None):
        n = len(steps)
        xp = xp if xp is not None else min(100, 55 + 5 * n)
        marks = marks if marks is not None else min(14, 4 + n)
        q = {'id': id, 'title': title, 'level': level, 'giver': giver, 'offer': offer, 'accept': accept,
             'topics': topics or {}, 'summary': summary, 'steps': [], 'endings': {}}
        if group:
            q['group'] = True
        if requires:
            q['requires'] = requires
        if decline:
            q['decline'] = decline
        for i, st in enumerate(steps, 1):
            st = dict(st)
            st['id'] = 's%d' % i
            q['steps'].append(st)
        ids = {st.get('label'): st['id'] for st in q['steps'] if st.get('label')}
        self.labels[id] = ids
        for st in q['steps']:                                    # option.next / step.next by label
            st.pop('label', None)
            if st.get('next') in ids:
                st['next'] = ids[st['next']]
            for o in st.get('options', []):
                if o.get('next') in ids:
                    o['next'] = ids[o['next']]
        for k, e in endings.items():
            ch = e.get('choice', [])
            q['endings'][k] = {'text': e['text'], 'tragic': bool(e.get('tragic')),
                               'rewards': {'xp_pct': xp, 'copper_per_level': 50 + 3 * n, 'marks': marks,
                                           'items': e.get('items', []), 'choice': ch}}
        self.quests.append(q)

    def check(self):
        names = {'%s_%s' % (self.prefix(), slug(i['name'])) for i in self.items}
        npcs = {n['id'] for n in self.npcs}
        errs = []
        for n in self.npcs:                                       # during: "quest/label" -> "quest/sN"
            out = []
            for d in n.get('during', []):
                q, st = d.split('/')
                st = self.labels.get(q, {}).get(st, st)
                if q not in self.labels or st not in {x['id'] for x in next(qq for qq in self.quests if qq['id'] == q)['steps']}:
                    errs.append('npc %s during %s' % (n['id'], d))
                out.append('%s/%s' % (q, st))
            if out:
                n['during'] = out
        for q in self.quests:
            sids = {st['id'] for st in q['steps']}
            if q['giver'] not in npcs:
                errs.append('%s giver %s' % (q['id'], q['giver']))
            for st in q['steps']:
                if st.get('npc') and st['npc'] not in npcs:
                    errs.append('%s/%s npc %s' % (q['id'], st['id'], st['npc']))
                if st.get('next') and st['next'] not in sids:
                    errs.append('%s/%s next %s' % (q['id'], st['id'], st['next']))
                if st.get('ending') and st['type'] not in ('talk', 'choice'):
                    errs.append('%s/%s ends on a %s (no one to choose a reward from)' % (q['id'], st['id'], st['type']))
                if st.get('ending') and st['ending'] not in q['endings']:
                    errs.append('%s/%s ending %s' % (q['id'], st['id'], st['ending']))
                for o in st.get('options', []):
                    if o.get('next') and o['next'] not in sids or o.get('ending') and o['ending'] not in q['endings']:
                        errs.append('%s/%s option %s' % (q['id'], st['id'], o))
                    if '[%s]' % o['keyword'].lower() not in st['say'].lower():
                        errs.append('%s/%s keyword %s not in say' % (q['id'], st['id'], o['keyword']))
                if st.get('keyword') and '[%s]' % st['keyword'].lower() not in st['say'].lower():
                    errs.append('%s/%s keyword %s not in say' % (q['id'], st['id'], st['keyword']))
            if '[%s]' % q['accept'].lower() not in q['offer'].lower():
                errs.append('%s accept not in offer' % q['id'])
            for k, e in q['endings'].items():
                for it in e['rewards']['items'] + e['rewards']['choice']:
                    if it not in names:
                        errs.append('%s ending %s item %s' % (q['id'], k, it))
            last = q['steps'][-1]
            if not last.get('ending') and not (last.get('options') and all(o.get('ending') or o.get('next') for o in last['options'])) and 'default' not in q['endings']:
                errs.append('%s last step has no ending' % q['id'])
        return errs

    def write(self):
        errs = self.check()
        if errs:
            raise SystemExit('%s:\n  %s' % (self.name, '\n  '.join(errs)))
        QDIR.mkdir(parents=True, exist_ok=True)
        js = {'name': self.name, 'npcs': self.npcs, 'quests': self.quests}
        (QDIR / ('%s.json' % self.file)).write_text(json.dumps(js, indent=2, ensure_ascii=False), encoding='utf-8')
        spec = {'zone': self.zone, 'region': {1: 1, 2: 100, 3: 200}[self.realm], 'realm': self.realm, 'prefix': self.prefix(), 'story': True, 'items': self.items}
        (SPECS / ('story%03d_%s.json' % (self.zone, self.file.split('_', 1)[1]))).write_text(
            json.dumps(spec, indent=1, ensure_ascii=False), encoding='utf-8')
        return len(self.quests), len(self.items)


# ------------------------------------------------------------------ steps
def talk(npc, goal, say, kw=None, give=None, take=None):
    s = {'type': 'talk', 'npc': npc, 'goal': goal, 'say': say}
    if kw:
        s['keyword'] = kw
    if give:
        s['give'] = {'name': give}
    if take:
        s['take'] = take
    return s


def reach(zone, at, goal, text, r=15, label=None):
    s = {'type': 'reach', 'zone': zone, 'at': list(at), 'radius': r, 'goal': goal, 'text': text}
    if label:
        s['label'] = label
    return s


def search(zone, at, goal, clue, model, text, give=None, take=None, label=None):
    s = {'type': 'search', 'zone': zone, 'at': list(at), 'goal': goal, 'clue': {'name': clue, 'model': model}, 'text': text}
    if give:
        s['give'] = {'name': give}
    if take:
        s['take'] = take
    if label:
        s['label'] = label
    return s


def kill(zone, at, goal, name, tpl, lv, count, model=None, text=None, r=25, label=None, next=None):
    mob = {'template': tpl, 'name': name, 'level': list(lv) if isinstance(lv, (list, tuple)) else [lv, lv]}
    if model:
        mob['model'] = model
    s = {'type': 'kill', 'zone': zone, 'at': list(at), 'radius': r, 'goal': goal, 'mob': mob, 'count': count}
    if text:
        s['text'] = text
    if label:
        s['label'] = label
    if next:
        s['next'] = next
    return s


def boss(zone, at, goal, text, name, tpl, lv, announce, objective=None, model=None, hp=2.2, adds=None, every=25,
         count=2, wake=30, success=None, fail=None, label=None, next=None, ending=None):
    b = {'template': tpl, 'name': name, 'level': lv, 'health_mult': hp}
    if model:
        b['model'] = model
    st = {'id': 'b1', 'type': 'boss', 'name': name, 'center': list(at), 'radius': 30, 'time_s': 600,
          'objective': objective or goal, 'announce': announce, 'boss': b,
          'success': success or ('%s falls.' % name), 'fail': fail or 'You fall back.'}
    if adds:
        st['adds'] = {'every_s': every, 'count': count,
                      'mobs': [{'template': t, 'name': n, 'level': list(l) if isinstance(l, (list, tuple)) else [l, l]}
                               for t, n, l in adds]}
    s = {'type': 'encounter', 'zone': zone, 'at': list(at), 'wake_m': wake, 'goal': goal, 'text': text, 'stages': [st]}
    if label:
        s['label'] = label
    if next:
        s['next'] = next
    if ending:
        s['ending'] = ending
    return s


def defend(zone, at, goal, text, who, tpl, lv, announce, waves, objective, model=None, duration=90, every=20, count=2,
           froms=None, then_boss=None, wake=30, thanks=None, label=None):
    """Keep someone alive through waves (waves: [(tpl, name, lv)]), then optionally a boss (a dict for boss())."""
    froms = froms or [[at[0] + 12, at[1] + 6], [at[0] - 10, at[1] - 10]]
    d = {'id': 'd1', 'type': 'defend', 'name': objective, 'center': list(at), 'radius': 30, 'duration_s': duration,
         'objective': objective, 'announce': announce,
         'protect': {'template': tpl, 'name': who, 'level': lv, **({'model': model} if model else {})},
         'waves': {'every_s': every, 'count': count, 'from': [list(f) for f in froms],
                   'mobs': [{'template': t, 'name': n, 'level': list(l) if isinstance(l, (list, tuple)) else [l, l]}
                            for t, n, l in waves]},
         'thanks': thanks or 'You came for me.', 'success': 'They break off.', 'fail': '%s falls.' % who,
         'on_fail': 'end'}
    stages = [d]
    if then_boss:
        d['on_success'] = 'd2'
        b = then_boss
        bb = {'template': b['tpl'], 'name': b['name'], 'level': b['lv'], 'health_mult': b.get('hp', 2.2)}
        if b.get('model'):
            bb['model'] = b['model']
        stages.append({'id': 'd2', 'type': 'boss', 'name': b['name'], 'center': list(at), 'radius': 30, 'time_s': 480,
                       'objective': b.get('objective', 'Defeat %s' % b['name']), 'announce': b['announce'], 'boss': bb,
                       'success': '%s falls.' % b['name'], 'fail': 'You fall back.'})
    s = {'type': 'encounter', 'zone': zone, 'at': list(at), 'wake_m': wake, 'goal': goal, 'text': text, 'stages': stages}
    if label:
        s['label'] = label
    return s


def choice(npc, goal, say, options, label=None):
    """options: [(keyword, say, 'ending:<key>' | 'next:<label>')]"""
    opts = []
    for kw, sy, to in options:
        o = {'keyword': kw, 'say': sy}
        k, v = to.split(':', 1)
        o['ending' if k == 'ending' else 'next'] = v
        opts.append(o)
    s = {'type': 'choice', 'npc': npc, 'goal': goal, 'say': say, 'options': opts}
    if label:
        s['label'] = label
    return s


def L(label, step):
    step = dict(step)
    step['label'] = label
    return step


def end_talk(npc, goal, say, ending, label=None):
    s = talk(npc, goal, say)
    s['ending'] = ending
    if label:
        s['label'] = label
    return s


def main():
    sys.path.insert(0, str(HERE))
    total = [0, 0]
    for modname in sys.argv[1:]:
        mod = importlib.import_module(modname)
        for z in mod.ZONES:
            q, i = z.write()
            total[0] += q
            total[1] += i
            print('%-28s %d quests, %d items' % (z.name, q, i))
    print('total', total)


if __name__ == '__main__':
    main()
