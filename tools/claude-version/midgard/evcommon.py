"""Shared bits for Albion's event scripts (claude 2026-11-24)."""
import json, sys, math
sys.path.insert(0, '/home/claude/z/geo')
import geo

def mkP(Z):
    def P(x, y):
        if not geo.dry(Z, x, y, 4):
            n = geo.dry_near(Z, x, y, 60)
            assert n, ('wet', x, y)
            x, y = n
        return [x, y, round(geo.h(Z, x, y), 1)]
    return P

def R(xp, cp, tokens=None, items=None, gold=40):
    r = {"xp_pct": xp, "copper_per_level": cp}
    if tokens: r["tokens"] = tokens
    if items: r["items"] = [{"id": i, "gold_chance": gold, "silver_chance": 20} for i in items]
    return r

def mob(t, name, lv, **kw):
    return dict({"template": t, "name": name, "level": list(lv)}, **kw)

def path(P, a, b, step=100):
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(d // step))
    return [P(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)) for i in range(1, n + 1)]

def move_stage(st, P, xy):
    st['center'] = P(*xy)
    for k in ('boss', 'protect'):
        if st.get(k) and 'pos' in st[k]:
            st[k]['pos'] = st['center']
    w = st.get('waves')
    if w and w.get('from'):
        w['from'] = [P(xy[0] + dx, xy[1] + dy) for dx, dy in [(-30, -30), (30, 30), (-30, 35)]]

def shift_levels(c, levels, sh):
    c['levels'] = levels
    for st in c['stages']:
        for grp in [st.get('mobs', []), (st.get('waves') or {}).get('mobs', []), (st.get('adds') or {}).get('mobs', [])] + [a.get('mobs', []) for a in st.get('ambushes', [])]:
            for m in grp:
                m['level'] = [m['level'][0] + sh, m['level'][1] + sh]
        for k in ('boss', 'protect'):
            if st.get(k) and isinstance(st[k].get('level'), int):
                st[k]['level'] += sh
    for g in [c.get('giver')] + c.get('guards', []):
        if g and isinstance(g.get('level'), int):
            g['level'] += sh

def random_chain(id, title, levels, hint, start, stages, **kw):
    c = {"id": id, "title": title, "levels": levels, "hint": hint, "rest_s": 45, "first_delay_s": [300, 1500],
         "interval_s": [1800, 3000], "start": start, "stages": stages}
    c.update(kw)
    return c

def occupy(id, name, objective, announce, center, mobs, leader, count=10):
    return {"id": id, "type": "occupy", "name": name, "objective": objective, "announce": announce, "center": center, "radius": 70,
            "count": count, "reinforce_s": 90, "mobs": mobs, "boss": dict(leader, pos=center),
            "success": "The road is clear again.", "fail": "", "on_success": "end", "on_fail": id,
            "reward": R(15, 100, 6)}
