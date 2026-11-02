"""Unique drops for a zone's named monsters (and its dynamic events' bosses). Default is a read-only dry run.

  python tools\\claude-version\\named_uniques.py named_uniques\\zone206_valley_of_bri_leith.json            (dry run)
  python tools\\claude-version\\named_uniques.py named_uniques\\zone206_valley_of_bri_leith.json --apply    (server closed)
  python tools\\claude-version\\named_uniques.py named_uniques\\zone206_valley_of_bri_leith.json --undo

A zone's spec (named_uniques/zoneNNN_*.json; "realm": 1 Albion, 2 Midgard, 3 Hibernia, the default) lists one curated item per named monster: its name, slot (an existing
item's [Object_Type, Item_Type] to take the look, speed and hand from), level, bonuses, an optional weapon proc and a
line of lore. --apply (after a backup next to the database):
  * writes each item template (Id_nb <prefix>_<slug>): the base item's model, speed and hand at the item's level, 100%
    quality, the listed bonuses; weapons get the level's DPS, armour the level's AF; a proc of the level's strength
  * makes the named monster drop it (LootTemplate <prefix>_<mob>, MobXLootTemplate row; chance per item, one drop)
  * sets those named monsters' respawn to the spec's respawn_s where it was shorter (old values kept in a ledger)
Items with "event": true drop from a dynamic event's boss (spawned by the event, never in the Mob table); items with
"event_reward" are handed out by the event itself to its best contributors. Re-running replaces what it wrote.
"""
import argparse
import datetime
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / 'runtime/data/opendaoc.sqlite3.db'

STATS = {'Str': 1, 'Dex': 2, 'Con': 3, 'Qui': 4, 'Int': 5, 'Pie': 6, 'Emp': 7, 'Cha': 8, 'Power': 9, 'Hits': 10,
         'Body': 11, 'Cold': 12, 'Crush': 13, 'Energy': 14, 'Heat': 15, 'Matter': 16, 'Slash': 17, 'Spirit': 18,
         'Thrust': 19, 'Stealth': 49, 'Shields': 43, 'Parry': 40, 'Light': 65, 'Void': 66, 'Mana': 67,
         'Enchantments': 70, 'Blades': 72, 'Blunt': 73, 'Piercing': 74, 'LargeWeapons': 75, 'Mentalism': 76,
         'Regrowth': 77, 'Nurture': 78, 'Nature': 79, 'Music': 80, 'CelticDual': 81, 'CelticSpear': 82,
         'RecurveBow': 83, 'Valor': 84, 'Verdant': 87, 'Creeping': 88, 'Arboreal': 89, 'Scythe': 90,
         'FocusLight': 128, 'FocusVoid': 133, 'FocusMana': 134, 'FocusEnchantments': 135, 'FocusMentalism': 136,
         'FocusVerdant': 142, 'FocusCreeping': 143, 'FocusArboreal': 144}
# weapon procs by level (the database's ProcDirectDamage<element><level> spells, 32100-32126)
PROC_LEVELS = [(20, 32100), (25, 32104), (30, 32108), (35, 32112), (40, 32116), (43, 32120), (47, 32124)]
ELEMENT = {'heat': 0, 'cold': 1, 'energy': 2, 'spirit': 3}
WEAPONS = {2, 3, 4, 5, 8, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 42, 45}
ARMOUR = {32: 1, 33: 2, 34: 2, 35: 2, 36: 2, 37: 2, 38: 2}   # cloth AF = level, the rest 2 x level


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def proc_for(level, element):
    spell = PROC_LEVELS[0][1]
    for lvl, sid in PROC_LEVELS:
        if level >= lvl - 2:
            spell = sid
    return spell + ELEMENT[element]


def base_item(db, obj, slot, level, realm=3):
    rows = db.execute("select * from ItemTemplate where Object_Type=? and Item_Type=? and Realm in (?, 0) and Model>0 "
                      "and Level between ? and ? and Id_nb not like 'nu%' order by abs(Level-?), Realm desc, "
                      "Quality desc limit 1", (obj, slot, realm, level - 12, level + 12, level)).fetchone()
    if not rows:
        rows = db.execute("select * from ItemTemplate where Object_Type=? and Item_Type=? and Model>0 "
                          "order by abs(Level-?) limit 1", (obj, slot, level)).fetchone()
    return rows


def scaled_bonuses(bonuses, base_level, level):
    """An item's bonuses at another level: in proportion, within what an item of that level carries."""
    f = level / float(base_level)
    out = {}
    for name, val in bonuses.items():
        t = STATS[name]
        v = max(1, int(round(val * f)))
        if t <= 9:
            v = min(v, max(1, level // 2))                       # stats and power
        elif t == 10:
            v = min(v, int(level * 1.2))                         # hits
        elif t <= 19:
            v = min(v, max(1, level // 5))                       # resists
        elif t >= 128:
            v = min(v, level)                                    # focus
        else:
            v = min(v, max(1, level // 15))                      # skills
        out[name] = v
    return out


def plan(db, spec):
    cols = [d[0] for d in db.execute('select * from ItemTemplate limit 0').description]
    out = []
    todo = []
    for it in spec['items']:
        idnb = '%s_%s' % (spec['prefix'], slug(it['name']))
        todo.append((it, it['level'], it['bonuses'], idnb))
        # an event reward comes at the taker's level: versions every 5 levels (<id>_lNN, DynamicEventRuntime.ItemAtLevel)
        if it.get('scaled'):
            for lv in range(10, 51, 5):
                v = dict({k: x for k, x in it.items() if k != 'mob'}, level=lv,
                         bonuses=scaled_bonuses(it['bonuses'], it['level'], lv), scaled_of=idnb)
                todo.append((v, lv, v['bonuses'], '%s_l%d' % (idnb, lv)))
    for it, lvl, bonuses, idnb in todo:
        b = base_item(db, it['base'][0], it['base'][1], it['level'], spec.get('realm', 3))
        if b is None:
            raise SystemExit('no base item for %s %s' % (it['name'], it['base']))
        row = dict(zip(cols, b))
        row.update(Id_nb=idnb, ItemTemplate_ID=idnb, TranslationId='', Name=it['name'], Level=lvl, Quality=100,
                   Condition=50000, MaxCondition=50000, Durability=50000, MaxDurability=50000, IsNotLosingDur=0,
                   Realm=spec.get('realm', 3), Bonus=35, BonusLevel=0, LevelRequirement=0, ExtraBonus=0, ExtraBonusType=0,
                   SpellID=0, Charges=0, MaxCharges=0, SpellID1=0, Charges1=0, MaxCharges1=0, CanUseEvery=0,
                   ProcSpellID=0, ProcSpellID1=0, ProcChance=0, PoisonSpellID=0, PoisonCharges=0, PoisonMaxCharges=0,
                   IsPickable=1, IsDropable=1, CanDropAsLoot=1, IsTradable=1, IsIndestructible=0, MaxCount=1,
                   PackSize=1, Price=int(lvl * lvl * 60), PackageID=spec['prefix'], Description=it.get('lore', ''),
                   ClassType='', SalvageYieldID=0,
                   LastTimeRowUpdated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        obj = it['base'][0]
        if obj in WEAPONS and obj not in (42,):
            row['DPS_AF'] = int(round(12 + 3 * lvl))                     # 1.2 + 0.3 x level DPS
        elif obj == 42:
            row['DPS_AF'] = int(round(12 + 3 * lvl))
        elif obj in ARMOUR:
            row['DPS_AF'] = ARMOUR[obj] * lvl
        for k in range(1, 11):
            row['Bonus%d' % k] = 0
            row['Bonus%dType' % k] = 0
        for k, (name, val) in enumerate(bonuses.items(), 1):
            row['Bonus%d' % k] = val
            row['Bonus%dType' % k] = STATS[name]
        if it.get('proc'):
            row['ProcSpellID'] = proc_for(lvl, it['proc'])
        out.append((it, row, b))
    return cols, out


def ledger_path(spec_path):
    return Path(spec_path).with_suffix('.ledger.json')


def zone_box(db, spec):
    z = db.execute('select OffsetX,OffsetY,Width,Height from Zones where ZoneID=?', (spec['zone'],)).fetchone()
    return z[0] * 8192, z[1] * 8192, (z[0] + z[2]) * 8192, (z[1] + z[3]) * 8192


def named_spawns(db, spec, mob):
    x0, y0, x1, y1 = zone_box(db, spec)
    return db.execute('select Mob_ID,RespawnInterval from Mob where Name=? and Region=? and X>=? and X<? and Y>=? and Y<?',
                      (mob, spec['region'], x0, x1, y0, y1)).fetchall()


def undo(db, spec, spec_path):
    p = spec['prefix']
    db.execute("delete from ItemTemplate where PackageID=? and Id_nb like ?", (p, p + '_%'))
    db.execute("delete from LootTemplate where TemplateName like ?", (p + '_%',))
    db.execute("delete from MobXLootTemplate where LootTemplateName like ?", (p + '_%',))
    lp = ledger_path(spec_path)
    if lp.exists():
        for mob_id, old in json.loads(lp.read_text()).items():
            db.execute('update Mob set RespawnInterval=? where Mob_ID=?', (old, mob_id))


def apply(db, spec, spec_path, cols, items):
    undo(db, spec, spec_path)
    sql = 'insert into ItemTemplate (%s) values (%s)' % (','.join(cols), ','.join('?' * len(cols)))
    lp = ledger_path(spec_path)
    ledger = json.loads(lp.read_text()) if lp.exists() else {}
    by_mob = {}
    for it, row, _ in items:
        db.execute(sql, [row[c] for c in cols])
        if it.get('mob'):
            by_mob.setdefault(it['mob'], []).append((row['Id_nb'], it.get('chance', 40)))
    for mob, drops in by_mob.items():
        tname = '%s_%s' % (spec['prefix'], slug(mob))
        for idnb, chance in drops:
            db.execute('insert into LootTemplate (TemplateName, ItemTemplateID, Chance, Count, LastTimeRowUpdated, '
                       'LootTemplate_ID) values (?,?,?,1,?,?)', (tname, idnb, chance, '2000-01-01 00:00:00',
                                                                  '%s_%s' % (tname, idnb)))
        db.execute('insert into MobXLootTemplate (MobName, LootTemplateName, DropCount, LastTimeRowUpdated, '
                   'MobXLootTemplate_ID) values (?,?,1,?,?)', (mob, tname, '2000-01-01 00:00:00', tname))
        if not any(it.get('event') for it in spec['items'] if it.get('mob') == mob):
            for mob_id, resp in named_spawns(db, spec, mob):
                if resp is not None and 0 <= resp < spec['respawn_s']:
                    ledger.setdefault(mob_id, resp)
                    db.execute('update Mob set RespawnInterval=? where Mob_ID=?', (spec['respawn_s'], mob_id))
    lp.write_text(json.dumps(ledger, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--undo', action='store_true')
    ap.add_argument('--db', default=str(DB))
    ap.add_argument('--no-backup', action='store_true', help='(a batch of specs: back up once yourself first)')
    a = ap.parse_args()
    spec_path = Path(a.spec) if Path(a.spec).is_absolute() else Path(__file__).parent / a.spec
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    db = sqlite3.connect(a.db)
    cols, items = plan(db, spec)
    variants = sum(1 for it, _, _ in items if it.get('scaled_of'))
    for it, row, b in items:
        if it.get('scaled_of'):
            continue
        bon = ', '.join('%s %+d' % (k, v) for k, v in it['bonuses'].items())
        who = it.get('mob') or ('event reward ' + it.get('event_reward', ''))
        spawns = '' if it.get('event') or not it.get('mob') else ' (%d spawn%s)' % (
            len(named_spawns(db, spec, it['mob'])), '' if len(named_spawns(db, spec, it['mob'])) == 1 else 's')
        print('%-34s L%-2d %-28s %s%s  [look of %s]%s' % (row['Name'], row['Level'], who + spawns, bon,
              ', proc %d' % row['ProcSpellID'] if row['ProcSpellID'] else '', b[2],
              ', DPS/AF %d' % row['DPS_AF'] if row['DPS_AF'] else ''))
    if variants:
        print('(+ %d level versions of the event rewards, every 5 levels from 10 to 50)' % variants)
    if not (a.apply or a.undo):
        print('\n(dry run - nothing written)')
        return
    if not a.no_backup:
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        # one backup only (owner): the new one replaces any earlier '<db>.before-*' backup
        new = Path(a.db + '.before-%s-%s' % (spec['prefix'], stamp))
        shutil.copy2(a.db, new)
        for old in Path(a.db).parent.glob(Path(a.db).name + '.before-*'):
            if old != new:
                old.unlink()
        print('backup', new)
    if a.undo:
        undo(db, spec, spec_path)
    else:
        apply(db, spec, spec_path, cols, items)
    db.commit()
    print('\n%s.' % ('Removed' if a.undo else 'Written'))


if __name__ == '__main__':
    main()
