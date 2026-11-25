"""Spec: an item spec writer for Midgard's rebuilt zones (claude 2026-11-25, from specs_m1)."""
import json, sys
sys.path.insert(0, '/home/claude/lg/tools/claude-version')
from story_gen import Zone, slug
D = '/home/claude/lg/tools/claude-version/named_uniques/'

class Spec(Zone):
    def __init__(self, zone, name, prefix):
        super().__init__(zone, name, 2, 'x')
        self.pfx = prefix
    def prefix(self):
        return self.pfx
    def write_spec(self, fname, extra=None):
        s = {'zone': self.zone, 'region': 100, 'realm': 2, 'prefix': self.pfx, 'story': True, 'items': self.items}
        s.update(extra or {})
        json.dump(s, open(D + fname, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        return ['%s_%s' % (self.pfx, slug(i['name'])) for i in self.items]

