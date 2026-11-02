"""Builds zones/zoneNNN_<name>.json dynamic-event files for the classic zones from specs.py (the hand-written part:
foes, bosses, people, places, lore), the database survey (survey.py -> zones3.json: monster templates, levels and
where they live; towns and their guards) and the new client's terrain (dry, gentle ground away from towns and
buildings for each event, and a walkable road for escorts).

  python survey.py <copy of the server database .sqlite>          [zones3.json]
  python gen.py <out dir> [zone ...]
  python ../dynamic_events_fill_z.py <out dir>/zoneNNN_*.json      (ground heights)

Set DAOC_ZONES if the client's zone folders are not at new-client/godot/content/zones; DAOC_SURVEY / DAOC_DB
for zones3.json and the database copy."""
import json, math, random, re, sys, os
import numpy as np
from terrain import Terrain
from specs import Z

HERE = os.path.dirname(os.path.abspath(__file__))
SURV = json.load(open(os.environ.get('DAOC_SURVEY') or os.path.join(HERE, 'zones3.json')))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)
REALM = lambda z: 1 if z < 100 else 2 if z < 200 else 3
FALLBACK_GUARD = {1: 0, 2: 100, 3: 200}


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class ZoneGen:
    def __init__(self, zid):
        self.z = zid
        self.s = SURV[str(zid)]
        self.t = Terrain(zid)
        self.types = {t['name']: t for t in self.s['types']}
        self.realm = np.array(self.s['realm_pts'] or [[-9999, -9999]], float)
        self.mobs = np.array(self.s['mob_pts'] or [[-9999, -9999]], float)
        self.used = []
        self.rng = random.Random(zid * 7919)

    def foe(self, name):
        t = self.types.get(name)
        if not t:
            raise SystemExit('zone %d: no monster %r' % (self.z, name))
        return t

    def far_from_town(self, p, d=200):
        return np.min(np.hypot(self.realm[:, 0] - p[0], self.realm[:, 1] - p[1])) >= d

    def natives(self, p, r=60):
        return int(np.sum(np.hypot(self.mobs[:, 0] - p[0], self.mobs[:, 1] - p[1]) < r))

    def spot(self, anchor, rmin=40, rmax=320, ideal=110, near=None, near_d=(140, 280), town_d=200, relaxed=False):
        best = None
        for r in range(rmin, rmax + 1, 15):
            for k in range(24):
                a = k / 24 * 2 * math.pi
                p = (anchor[0] + r * math.cos(a), anchor[1] + r * math.sin(a))
                if near is not None and not (near_d[0] <= dist(p, near) <= near_d[1]):
                    continue
                if any(dist(p, u) < 230 for u in self.used):
                    continue
                if not self.far_from_town(p, town_d):
                    continue
                dh = self.t.ok_area(*p, r=45 if not relaxed else 35, maxdh=12 if not relaxed else 18)
                if dh is None:
                    continue
                score = self.natives(p) * 6 + abs(r - ideal) / 25 + dh / 2
                if best is None or score < best[0]:
                    best = (score, p)
        if best is None and not relaxed:
            return self.spot(anchor, rmin, rmax + 150, ideal, near, (near_d[0] - 40, near_d[1] + 80), min(town_d, 150), relaxed=True)
        return best[1] if best else None

    def dry_near(self, p, r=12, rmax=60):
        for rr in range(0, rmax, 6):
            for k in range(12):
                a = k / 12 * 2 * math.pi
                q = (p[0] + rr * math.cos(a), p[1] + rr * math.sin(a))
                if self.t.ok_area(*q, r=r, maxdh=6) is not None:
                    return q
        return None

    def guard(self, town=None):
        towns = self.s['towns']
        if not towns:
            towns = SURV[str(FALLBACK_GUARD[REALM(self.z)])]['towns']
        if town:
            areas = [a for a in self.s['areas'] if town.lower() in a[0].lower()]
            if areas:
                ax, ay = areas[0][1], areas[0][2]
                towns = sorted(towns, key=lambda t: dist((t['x'], t['y']), (ax, ay)))
        return towns[0]

    # ---- builders ----
    def mobdefs(self, names):
        out = []
        for n in names:
            t = self.foe(n)
            lv = list(t['lv'])
            if lv[1] - lv[0] > 4:
                lv = [lv[0], lv[0] + 4]
            out.append({'template': t['tpl'], 'name': n, 'level': lv})
        return out

    def levels(self, mobs):
        return [min(m['level'][0] for m in mobs), max(m['level'][1] for m in mobs)]

    def npc_from_guard(self, g, name, level, guild=None, health=4, extra=None):
        gname, model, equip, tpl, glv, size, gguild, cls = g['guard']
        d = {'name': name}
        if tpl and tpl > 0:
            d['template'] = tpl
        d['level'] = level
        d['model'] = model
        if equip:
            d['equipment'] = equip
        if guild:
            d['guild'] = guild
        d['health_mult'] = health
        if extra:
            d.update(extra)
        return d

    def boss(self, spec, lv, at):
        bname, bfoe = spec['boss']
        t = self.foe(bfoe)
        sizes = [int(x) for x in re.findall(r'\d+', str(self.size_of(t)))] or [50]
        return {'template': t['tpl'], 'name': bname, 'level': lv[1] + 3, 'size': min(110, int(max(sizes) * 1.3)),
                'pos': [round(at[0]), round(at[1])], 'health_mult': 2.5}

    def size_of(self, t):
        return SIZES.get(t['tpl'], '50')

    def cull_stage(self, sid, spec, at, mobs, nxt, lead):
        place = spec['place']
        return {'id': sid, 'type': 'cull', 'name': 'Clear %s' % title_place(place),
                'objective': 'Clear %s' % place,
                'announce': lead,
                'center': [round(at[0]), round(at[1])], 'radius': 60, 'time_s': 1200, 'kill': 12, 'alive': 7,
                'mobs': mobs,
                'success': 'You have cleared %s. %s comes out to fight.' % (place, spec['boss'][0]),
                'fail': 'They hold %s. They will be bolder next time.' % place,
                'on_success': nxt, 'on_fail': 'end',
                'reward': {'xp_pct': 12, 'copper_per_level': 80}}

    def boss_stage(self, sid, spec, at, mobs, lv, done):
        b = self.boss(spec, lv, at)
        return {'id': sid, 'type': 'boss', 'name': spec['boss'][0], 'objective': 'Defeat %s' % mid_name(spec['boss'][0]),
                'announce': '%s stands at %s. Bring friends.' % (spec['boss'][0], spec['place']),
                'center': [round(at[0]), round(at[1])], 'radius': 70, 'time_s': 1200,
                'boss': b, 'adds': {'every_s': 60, 'count': 2, 'mobs': mobs[:1]},
                'success': '%s falls. %s' % (spec['boss'][0], done),
                'fail': '%s slips away - for now.' % spec['boss'][0],
                'on_success': 'end', 'on_fail': 'end',
                'reward': {'xp_pct': 20, 'copper_per_level': 150}}

    def anchor(self, spec):
        cl = self.foe(spec['foes'][0])['cl']
        return (cl[0][0], cl[0][1])

    def chain(self, spec):
        mobs = self.mobdefs(spec['foes'])
        lv = self.levels(mobs)
        cid = '%s_%s' % (Z[self.z]['file'], spec['id'])
        c = {'id': cid, 'title': spec['title'], 'levels': lv, 'hint': spec.get('hint') or '%s is looking for help in %s.' % (spec['giver'][0], spec.get('town') or 'town'), 'rest_s': 45}
        kind = spec['kind']
        done = 'The way is safe again.'
        if kind == 'camp':
            at = self.spot(self.anchor(spec))
            if not at:
                raise SystemExit('zone %d %s: no spot' % (self.z, cid))
            self.used.append(at)
            c.update(first_delay_s=[120, 900], interval_s=[1500, 2700], start='a1')
            c['stages'] = [self.cull_stage('a1', spec, at, mobs, 'a2', spec['why']),
                           self.boss_stage('a2', spec, at, mobs, lv, done)]
        elif kind == 'defend':
            a = self.spot(self.anchor(spec), ideal=200, rmax=380)
            if not a:
                raise SystemExit('zone %d %s: no spot' % (self.z, cid))
            self.used.append(a)
            b = self.spot(self.anchor(spec), rmin=20, ideal=60, near=a) or self.spot(a, rmin=150, rmax=320, ideal=200) or a
            if b is not a:
                self.used.append(b)
            g = self.guard()
            pname, task = spec['protect']
            ppos = self.dry_near(a, r=4) or a
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            froms = []
            for da in (-0.8, 0, 0.8):
                q = (a[0] + 85 * math.cos(ang + da), a[1] + 85 * math.sin(ang + da))
                froms.append(self.dry_near(q, r=6) or q)
            protect = self.npc_from_guard(g, pname, lv[1], guild=None, health=10, extra={'pos': [round(ppos[0]), round(ppos[1])]})
            protect.pop('guild', None)
            c.update(first_delay_s=[120, 900], interval_s=[1500, 2700], start='d1')
            c['stages'] = [
                {'id': 'd1', 'type': 'defend', 'name': 'Protect %s' % pname, 'objective': 'Protect %s, who is %s' % (pname, task),
                 'announce': spec['why'], 'center': [round(a[0]), round(a[1])], 'radius': 70, 'duration_s': 180,
                 'protect': protect,
                 'waves': {'every_s': 30, 'count': 2, 'from': [[round(p[0]), round(p[1])] for p in froms], 'mobs': mobs},
                 'success': '"That\'s done," says %s. "They came from over there - let\'s finish this."' % pname,
                 'fail': '%s falls. The attackers are left to do as they please - for now.' % pname,
                 'on_success': 'd2', 'on_fail': 'end', 'reward': {'xp_pct': 8, 'copper_per_level': 60}},
                self.cull_stage('d2', spec, b, mobs, 'd3', 'They came from %s. Follow them back and clear it out.' % spec['place']),
                self.boss_stage('d3', spec, b, mobs, lv, done)]
        else:
            town = self.guard(spec.get('town'))
            tc = (town['x'], town['y'])
            # the foe camp: a cluster of these monsters 300-900 m from the town, nearest 550 m
            cands = []
            for n in spec['foes']:
                for x, y, k in self.foe(n)['cl']:
                    d = dist((x, y), tc)
                    if 180 <= d <= 950:
                        cands.append((abs(d - 550), (x, y)))
            cands.sort()
            if not cands:
                raise SystemExit('zone %d %s: no camp in reach of %s' % (self.z, cid, spec.get('town')))
            res = None
            for _, anc in cands[:10]:
                for ideal in (60, 120, 180):
                    at = self.spot(anc, rmin=20, rmax=260, ideal=ideal, town_d=150)
                    if not at:
                        break
                    gp, path = self.road(tc, at)
                    if path:
                        res = (at, gp, path)
                        break
                if res:
                    break
            if not res:
                raise SystemExit('zone %d %s: no road from %s' % (self.z, cid, spec.get('town')))
            at, gp, path = res
            self.used.append(at)
            gname, gguild, greet = spec['giver']
            giver = self.npc_from_guard(town, gname, min(lv[1] + 8, 65), guild=gguild, health=4)
            giver['pos'] = [round(gp[0]), round(gp[1])]
            giver.update({'greet': greet, 'accept': 'ready',
                          'reply': 'Good. Stay close - they will have watchers out. With me!',
                          'busy': "We've only just come back. Give my people a while to rest, then find me again.",
                          'cooldown_s': 900})
            guard = self.npc_from_guard(town, guard_name(gguild, town), lv[1] + 2, guild=gguild, health=2)
            guard['count'] = 3
            mid = max(1, len(path) // 2)
            c.update(giver=giver, guards=[guard], start='g1')
            c['stages'] = [
                {'id': 'g1', 'type': 'escort', 'name': 'The Road to %s' % title_place(spec['place']),
                 'objective': 'Go with %s to %s' % (gname, spec['place']), 'announce': spec['why'],
                 'radius': 60, 'time_s': 1500, 'path': [[round(p[0]), round(p[1])] for p in path],
                 'ambushes': [{'at': mid, 'count': 3, 'say': 'Ambush! To me - hold together!', 'mobs': mobs[:2]}],
                 'success': '%s reaches %s. "There they are. Clear them out!"' % (gname, spec['place']),
                 'fail': '%s falls on the road. The others carry the body home.' % gname,
                 'on_success': 'g2', 'on_fail': 'end', 'reward': {'xp_pct': 10, 'copper_per_level': 60}},
                self.cull_stage('g2', spec, at, mobs, 'g3', 'Clear %s!' % spec['place']),
                self.boss_stage('g3', spec, at, mobs, lv, '%s will hear of this in the taverns tonight.' % cap(spec.get('town') or 'the town'))]
        return c

    def road(self, tc, at):
        # the giver stands at the edge of town towards the camp; the road is the easiest way there (A* over the
        # terrain: no deep water, nothing steeper than 30 degrees, fords cost extra)
        import road
        ang = math.atan2(at[1] - tc[1], at[0] - tc[0])
        gp = None
        for r in range(25, 110, 8):
            for da in (0, 0.3, -0.3, 0.6, -0.6, 0.9, -0.9):
                q = (tc[0] + r * math.cos(ang + da), tc[1] + r * math.sin(ang + da))
                if self.t.ok_area_nofix(*q):
                    gp = q
                    break
            if gp:
                break
        if not gp:
            return None, None
        pts = road.astar(self.t, gp, at)
        if not pts:
            return gp, None
        L = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        if L > 1.6 * dist(gp, at) + 100:
            return gp, None
        return gp, road.simplify(self.t, pts)[1:]


def guard_name(guild, town):
    g = town['guard'][0]
    g = re.sub(r'^(Guard|Sentinel|Guardian|Flayer|Viking|Watch)\s+[A-Z][a-z]+$', r'\1', g)
    return g if g[0].isupper() else g.title()


def mid_name(n):
    return 'the' + n[3:] if n.startswith('The ') else n


def cap(s):
    return s[0].upper() + s[1:]


def title_place(p):
    p = re.sub(r'^the ', '', p)
    return ' '.join(w if w in ('of', 'the') else w[0].upper() + w[1:] for w in p.split())


def task_gerund(t):
    return t.replace("singing", "they sing").replace("carving", "he carves") if False else re.sub(r'^(\w+)ing', lambda m: 'they finish ' + m.group(0), t)


# template sizes from the database (for bosses)
import sqlite3
_c = sqlite3.connect(os.environ.get('DAOC_DB') or os.path.join(HERE, 'db.sqlite'))
SIZES = {r[0]: r[1] for r in _c.execute('select TemplateId, Size from NpcTemplate')}


def ok_area_nofix(self, x, y):
    if self.wet(x, y):
        return False
    zs = [self.z(x + dx, y + dy) for dx, dy in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4))]
    return max(zs) - min(zs) < 2.0
Terrain.ok_area_nofix = ok_area_nofix

SKIP_USED = {206}
if __name__ == '__main__':
    only = [int(a) for a in sys.argv[2:]]
    for zid, zs in Z.items():
        if only and zid not in only:
            continue
        g = ZoneGen(zid)
        doc = {'zone': zid, 'region': g.s['region'], 'name': g.s['name'], 'lore': zs['lore'], 'chains': []}
        for spec in zs['chains']:
            try:
                doc['chains'].append(g.chain(spec))
            except SystemExit as e:
                print('   !!', e)
        path = os.path.join(OUT, 'zone%03d_%s.json' % (zid, zs['file']))
        json.dump(doc, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        print(zid, g.s['name'], ', '.join('%s %s %s' % (c['id'], c['levels'], c['stages'][0].get('center') or c['giver']['pos']) for c in doc['chains']))
