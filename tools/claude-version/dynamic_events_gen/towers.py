"""Guard towers that can fall (owner 2026-11-02: "guard towers ... being captured by bad NPCs, which despawn the normal
friendly NPCs that are there. If it's captured ... a 'recapture' event that would be hard for solo players/bots to win,
more like group events from GW2. If friendly NPCs hold that tower, having some special merchants that sell rare goods").
A pilot of two towers per realm.

Each tower is a chain in its zone's file:
  t1 defend  - the assault: the tower's sergeant must live through waves for four minutes. Won: the tower holds.
               Nobody comes within ten minutes of the alarm (auto_fail_s): it falls anyway.
  c1 occupy  - captured: the realm's people at the tower are driven off (displace_m), an elite garrison and its captain
               hold it - hard for one player, a group's fight - and they replace their fallen while nobody presses them.
  c2 defend  - retaken: hold it while the enemy counter-attacks; lost, they have it again (c1).
While the realm holds it, a quartermaster stands at its foot and sells for Marks of Valor (stock: tower_stock.py).

  python towers.py <zones dir> <server database copy>          (then dynamic_events_fill_z.py on the changed files)
"""
import json, math, os, sqlite3, sys
from terrain import Terrain

TOWERS = [
    dict(zone=8, file='zone008_campacorentin_forest.json', id='tower_westwood', name='Westwood Tower', at=(653, 582),
         levels=[8, 12], foes=['sylvan goblin hunter', 'sylvan goblin warrior'], captain='Warchief Grubskull',
         sergeant='Sergeant Aldric', qm='Quartermaster Bede', people='the sylvan goblins',
         hint='Goblin war-drums beat around Westwood Tower...'),
    dict(zone=8, file='zone008_campacorentin_forest.json', id='tower_ogres_watch', name="Ogre's Watch", at=(518, 1338),
         levels=[12, 15], foes=['wood ogre scourge', 'wood ogre berserker', 'wood ogre seer'], captain='Grashk the Wall-Breaker',
         sergeant='Sergeant Wenna', qm='Quartermaster Osbert', people='the wood ogres',
         hint="Trees are falling around the Ogre's Watch tower..."),
    dict(zone=105, file='zone105_myrkwood_forest.json', id='tower_sentry_tower', name='Sentry Tower', at=(883, 1005),
         levels=[10, 13], foes=['decaying troll', 'decaying norseman', 'corpse eater'], captain='The Corpse-King',
         sergeant='Sentry Crush', qm='Quartermaster Hrefna', people='the walking dead',
         hint='The dead are stirring around the Sentry Tower...'),
    dict(zone=100, file='zone100_vale_of_mularn.json', id='tower_veldon_watch', name='Veldon Watchtower', at=(1107, 122),
         levels=[10, 13], foes=['hobyah', 'hill cat'], captain='The Hobyah Nightmother',
         sergeant='Dreng Oddnaug', qm='Quartermaster Tove', people='the hobyahs',
         hint='Something is moving in the hills around the Veldon Watchtower...'),
    dict(zone=206, file='zone206_valley_of_bri_leith.json', id='tower_giolladhe', name="Giolladhe's Tower", at=(122, 1299),
         levels=[19, 24], foes=['faerie steed', 'faerie drake'], captain='The Huntsman of the Sidhe',
         sergeant='Sentinel Giolladhe', qm='Quartermaster Maudalin', people='the Wild Hunt',
         hint="Horns of the Wild Hunt sound around Giolladhe's Tower..."),
    dict(zone=203, file='zone203_cliffs_of_moher.json', id='tower_moher_watch', name='Moher Watchtower', at=(802, 376),
         levels=[31, 33], foes=['greater zephyr', 'aughisky'], captain='The Storm-Rider',
         sergeant='Sentinel Cinead', qm='Quartermaster Maible', people='the storm-spirits',
         hint='A storm is gathering over the Moher Watchtower...'),
]


def main():
    zdir, dbp = sys.argv[1], sys.argv[2]
    c = sqlite3.connect(dbp)
    zones = {r[0]: r for r in c.execute('select ZoneID,RegionID,OffsetX,OffsetY from Zones')}
    tpl_by_name = {}
    for r in c.execute('select TemplateId,Name from NpcTemplate'):
        tpl_by_name.setdefault(r[1].lower(), r[0])
    files = {}
    for tw in TOWERS:
        path = os.path.join(zdir, tw['file'])
        doc = files.get(path) or json.load(open(path, encoding='utf-8'))
        files[path] = doc
        zid, reg, ox, oy = zones[tw['zone']]
        x0, y0 = ox * 8192, oy * 8192
        tx, ty = tw['at']
        # the tower's people: its guards' look for the sergeant and the quartermaster
        rows = list(c.execute('select Name,X,Y,ClassType,Model,EquipmentTemplateID,NPCTemplateID,Level from Mob where Region=? '
                              'and Realm>0 and X between ? and ? and Y between ? and ?',
                              (reg, x0 + (tx - 60) * 40, x0 + (tx + 60) * 40, y0 + (ty - 60) * 40, y0 + (ty + 60) * 40)))
        guards = [r for r in rows if 'Guard' in (r[3] or '')] or rows
        g = min(guards, key=lambda r: math.hypot((r[1] - x0) / 40 - tx, (r[2] - y0) / 40 - ty))
        look = {'model': g[4]}
        if g[5]:
            look['equipment'] = g[5]
        if g[6] and g[6] > 0:
            look['template'] = g[6]
        t = Terrain(tw['zone'])
        def ground(dx, dy):
            for r in range(10, 40, 3):
                for k in range(12):
                    a = math.atan2(dy, dx) + (k - 6) * 0.35
                    p = (tx + r * math.cos(a), ty + r * math.sin(a))
                    if t.ok_area_nofix(*p):
                        return [round(p[0]), round(p[1])]
            return [tx + dx, ty + dy]
        lo, hi = tw['levels']
        mobs = []
        for f in tw['foes']:
            tid = tpl_by_name.get(f)
            if tid is None:
                raise SystemExit('no template for %s' % f)
            mobs.append({'template': tid, 'name': f, 'level': [lo, hi]})
        elite = [dict(m, level=[hi + 1, hi + 3]) for m in mobs]
        froms = [[round(tx + 90 * math.cos(a)), round(ty + 90 * math.sin(a))] for a in (0.4, 2.5, 4.6)]
        sgt = dict(look, name=tw['sergeant'], level=hi + 2, pos=ground(-12, 0), health_mult=15)
        chain = {
            'id': tw['id'], 'title': 'The Siege of %s' % tw['name'], 'levels': [lo, hi], 'tower': tw['name'],
            'hint': tw['hint'], 'rest_s': 45, 'first_delay_s': [1800, 3600], 'interval_s': [5400, 9000],
            'wake_m': 180, 'auto_fail_s': 600, 'start': 't1',
            'merchant': dict(look, name=tw['qm'], level=hi + 5, pos=ground(0, 12), stock='tower_' + tw['id'][6:],
                             guild='Marks of Valor',
                             greet='While %s stands, I can sell you what coin won\'t buy. Marks of Valor only.' % tw['name']),
            'stages': [
                {'id': 't1', 'type': 'defend', 'name': 'Hold %s' % tw['name'],
                 'objective': 'Keep %s alive while %s attack the tower' % (tw['sergeant'], tw['people']),
                 'announce': '%s are attacking %s! %s calls for every sword nearby.' % (tw['people'][0].upper() + tw['people'][1:], tw['name'], tw['sergeant']),
                 'center': [tx, ty], 'radius': 60, 'duration_s': 240,
                 'protect': sgt,
                 'waves': {'every_s': 25, 'count': 3, 'from': froms, 'mobs': mobs},
                 'thanks': '"The tower holds! Drinks are on me when the quartermaster isn\'t looking."',
                 'success': '%s break off the attack. %s holds.' % (tw['people'][0].upper() + tw['people'][1:], tw['name']),
                 'fail': '%s has fallen to %s.' % (tw['name'], tw['people']),
                 'on_success': 'end', 'on_fail': 'c1',
                 'reward': {'xp_pct': 15, 'copper_per_level': 100, 'tokens': 8}},
                {'id': 'c1', 'type': 'occupy', 'name': 'Retake %s' % tw['name'],
                 'objective': 'Drive %s out of %s' % (tw['people'], tw['name']),
                 'announce': '%s hold %s. Its guards are gone, its quartermaster fled. It will take a war-band to win it back.' % (tw['people'][0].upper() + tw['people'][1:], tw['name']),
                 'center': [tx, ty], 'radius': 50, 'count': 14, 'reinforce_s': 45, 'displace_m': 45, 'health_mult': 2.5,
                 'mobs': elite,
                 'boss': {'template': mobs[0]['template'], 'name': tw['captain'], 'level': hi + 4, 'pos': [tx, ty],
                          'health_mult': 6},
                 'success': '%s is dead and the tower is ours - for now. They will be back.' % tw['captain'],
                 'fail': '', 'on_success': 'c2', 'on_fail': 'c1',
                 'reward': {'xp_pct': 30, 'copper_per_level': 250, 'tokens': 25}},
                {'id': 'c2', 'type': 'defend', 'name': 'Hold the Gate',
                 'objective': 'Keep %s alive until the garrison is back' % tw['sergeant'],
                 'announce': '%s is raising the realm\'s colours again - and %s are coming back for the tower!' % (tw['sergeant'], tw['people']),
                 'center': [tx, ty], 'radius': 60, 'duration_s': 150,
                 'protect': sgt,
                 'waves': {'every_s': 25, 'count': 3, 'from': froms, 'mobs': mobs},
                 'thanks': '"%s is ours again. The quartermaster will be glad to see you."' % tw['name'],
                 'success': '%s is held by the realm again. Its garrison and quartermaster are back.' % tw['name'],
                 'fail': '%s falls, and %s take the tower back.' % (tw['sergeant'], tw['people']),
                 'on_success': 'end', 'on_fail': 'c1',
                 'reward': {'xp_pct': 15, 'copper_per_level': 120, 'tokens': 10}},
            ],
        }
        doc['chains'] = [ch for ch in doc['chains'] if ch['id'] != tw['id']] + [chain]
        print(tw['zone'], tw['id'], 'guard look', g[0], look, 'sergeant at', sgt['pos'], 'qm at', chain['merchant']['pos'])
    for path, doc in files.items():
        json.dump(doc, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
