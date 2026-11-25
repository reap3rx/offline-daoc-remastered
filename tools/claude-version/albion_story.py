"""Shared helpers for Albion's rebuilt zone stories (claude 2026-11-24, round 2 on): the zone's older quests kept by id, people
placed on dry ground, "about 300 m north-east of X" directions, hunt steps. Each story_<zone>.py makes one Story and writes its
quests the story_gen way."""
import json, math, sys
sys.path.insert(0, '/home/claude/z/geo')
from story_gen import Zone, HERE
try:
    import geo
except ImportError:
    geo = None

CRATE, BEDROLL, LANTERN = 1347, 1882, 1876
M, F, OLD = 9, 38, 32


class Story:
    def __init__(self, zone, name, file, spec, old_ids, old_npcs, old_items):
        self.Z = zone
        self.z = Zone(zone, name, 1, file)
        self.AT, self.NAMES = {}, {}
        q = json.loads((HERE.parents[1] / ('source/server/GameServer/scripts/storyquests/quests/%s.json' % file)).read_text(encoding='utf-8'))
        sp = json.loads((HERE / ('named_uniques/%s.json' % spec)).read_text(encoding='utf-8'))
        for qq in q['quests']:
            if qq['id'] in old_ids:
                for e in qq['endings'].values():
                    e['rewards'].setdefault('items', [])
                    e['rewards'].setdefault('choice', [])
                self.z.quests.append(qq)
                self.z.labels[qq['id']] = {}
        for n in q['npcs']:
            if n['id'] in old_npcs:
                self.z.npcs.append(n)
                self.NAMES[n['id']] = n['name']
                self.AT[n['id']] = tuple(n['pos'][:2])
        for it in sp['items']:
            if it['name'] in old_items:
                self.z.items.append(it)

    def P(self, x, y):
        if geo and not geo.dry(self.Z, x, y, 4):
            n = geo.dry_near(self.Z, x, y, 60)
            if n:
                return n
        return (x, y)

    def person(self, id, name, xy, kind, level, **kw):
        xy = self.P(*xy)
        self.NAMES[id] = name
        self.AT[id] = tuple(xy)
        self.z.npc(id, name, list(xy), kind, level, **kw)

    def where(self, to, frm):
        fx, fy = self.AT[frm]
        dx, dy = to[0] - fx, to[1] - fy
        d = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(-dy, dx)) % 360
        names = ['east', 'north-east', 'north', 'north-west', 'west', 'south-west', 'south', 'south-east']
        dirn = names[int(((ang + 22.5) % 360) // 45)]
        dist = ('%d m' % (round(d / 10) * 10)) if d < 950 else ('%.1f km' % (d / 1000))
        return 'about %s %s of %s' % (dist, dirn, self.NAMES[frm])

    def hunt(self, xy, goal, target, count=1, text=None, r=50):
        st = {'type': 'kill', 'zone': self.Z, 'at': list(self.P(*xy)), 'radius': r, 'goal': goal, 'target': target, 'count': count}
        if text:
            st['text'] = text
        return st
