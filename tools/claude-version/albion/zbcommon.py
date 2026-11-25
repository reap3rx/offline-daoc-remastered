"""Shared helpers for Albion's zone builds (claude 2026-11-24): zone metres in, zone units out, water checked."""
import json, sys
sys.path.insert(0, '/home/claude/z/geo')
import geo
M = 40
class Build:
    def __init__(self, zone, name, rating, wildmult=1.0):
        self.Z, self.name, self.rating, self.S, self.members, self.W = zone, name, rating, [], {}, wildmult
    def dry(self, x, y):
        if not geo.dry(self.Z, x, y, 4):
            n = geo.dry_near(self.Z, x, y, 60)
            assert n, ('wet', self.name, x, y)
            print('  moved', (x, y), '->', n)
            x, y = n
        return x, y
    def u(self, x, y):
        x, y = self.dry(x, y)
        return [int(x * M), int(y * M)]
    @staticmethod
    def area(x0, y0, x1, y1): return [int(x0 * M), int(y0 * M), int(x1 * M), int(y1 * M)]
    def camp(self, i, x, y, r, spawn, respawn=300, **kw):
        self.S.append(dict({"id": i, "kind": "camp", "at": self.u(x, y), "r": int(r * M), "respawn": respawn, "spawn": spawn}, **kw))
    def wild(self, i, x0, y0, x1, y1, spawn, **kw):
        sp = {k: max(1, round(v * self.W)) for k, v in spawn.items()}
        self.S.append(dict({"id": i, "kind": "wildlife", "area": self.area(x0, y0, x1, y1), "spawn": sp, "spacing": 260}, **kw))
    def patrol(self, i, pts, spawn, **kw):
        self.S.append(dict({"id": i, "kind": "patrol", "route": [self.u(x, y) for x, y in pts], "spawn": spawn}, **kw))
    def clear(self, i, x, y, r, names):
        self.S.append({"id": i, "kind": "clear", "at": [int(x * M), int(y * M)], "r": int(r * M), "names": names})
    def write(self, path, themes, notes, keep, tiers, factions):
        d = {"zone": self.Z, "name": self.name, "rating": self.rating, "themes": themes, "notes": notes, "keep": keep,
             "tiers": tiers, "factions": factions, "members": self.members, "sites": self.S}
        members = self.members
        tiers_n, tot = {}, 0
        for s in self.S:
            for k, v in s.get("spawn", {}).items():
                assert k in members, ('no member', k)
                t = members[k]["tier"]; tiers_n[t] = tiers_n.get(t, 0) + v; tot += v
                for g, gv in members[k].get("guards", {}).items():
                    tg = members[g]["tier"]; tiers_n[tg] = tiers_n.get(tg, 0) + v * gv; tot += v * gv
                if members[k].get("faction"):
                    assert members[k]["faction"] in factions, ('faction', k)
        for k in members:
            assert any(k in s.get("spawn", {}) for s in self.S) or any(k in m.get("guards", {}) for m in members.values()), ('unused', k)
        print(self.name, "placed", tot, {t: "%d (%.0f%%)" % (n, 100 * n / tot) for t, n in sorted(tiers_n.items())})
        json.dump(d, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
