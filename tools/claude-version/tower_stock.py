"""The tower quartermasters' stock and the Marks of Valor they take (owner 2026-11-02: towers the realm holds have
"special merchants that sell rare goods (good armor/weapons, things like respecs, good potions ...)"; paid in event
tokens, chosen like GW2's karma; armor and weapons, respecs, potions and tower-only cosmetics).

Writes, after one backup of the database (replacing any earlier '.before-*' backup):
  * event_mark - "Mark of Valor", the token dynamic events hand out (DynamicEventRuntime.GiveRewards)
  * per tower (dynamic_events_gen/towers.py), item list tower_<name>:
      page 1 - a 100% quality set for each of the realm's armour types (helm, gloves, boots, body, legs, arms) at the
               tower's gear level (its events' top level + 3), with that armour's wearers' stats
      page 2 - the realm's weapons and a shield at that level, the tower's own cloak (its name, its colours: a cloak
               model no merchant sells), healing / power / endurance draughts and elixirs, the combined buff and regen
               draughts, and single, full and realm respec stones (tw_respec_*: trainers take them as the usual ones)
    prices are counts of marks (the templates' Price - the merchant is an item-currency one).
Re-running replaces what it wrote (PackageID tw_*, lists tower_*, event_mark).

  python tools\\claude-version\\tower_stock.py               (dry run)
  python tools\\claude-version\\tower_stock.py --apply       (server closed)
"""
import argparse, datetime, json, shutil, sqlite3, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import named_uniques as nu                                    # base items, bonus caps, stat ids

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / 'runtime/data/opendaoc.sqlite3.db'

TOWERS = [  # id, name, realm, gear level, stock list
    ('westwood', 'Westwood', 1, 15), ('ogres_watch', 'Ogrewatch', 1, 18),
    ('sentry_tower', 'Myrkwood Sentry', 2, 16), ('veldon_watch', 'Veldon', 2, 16),
    ('giolladhe', 'Giolladhe', 3, 27), ('moher_watch', 'Moher', 3, 36),
]
ARMOUR = {1: [32, 33, 34, 35, 36], 2: [32, 33, 34, 35], 3: [32, 33, 37, 38]}
ARMOUR_WORD = {32: 'Woven', 33: 'Leather', 34: 'Studded', 35: 'Mail', 36: 'Plate', 37: 'Reinforced', 38: 'Scale'}
SLOT_WORD = {21: 'Helm', 22: 'Gloves', 23: 'Boots', 25: 'Jerkin', 27: 'Leggings', 28: 'Sleeves'}
BODY_WORD = {32: 'Robe', 35: 'Hauberk', 36: 'Breastplate', 38: 'Hauberk'}
WEAPONS = {  # (object type, item type): word
    1: [((2, 10), 'Mace'), ((3, 10), 'Sword'), ((4, 10), 'Rapier'), ((6, 12), 'Greatsword'), ((7, 12), 'Halberd'),
        ((24, 10), 'Flail'), ((8, 12), 'Staff'), ((9, 13), 'Longbow'), ((10, 13), 'Crossbow'), ((42, 11), 'Shield')],
    2: [((11, 10), 'Sword'), ((12, 10), 'Hammer'), ((13, 10), 'Axe'), ((11, 12), 'Greatsword'), ((13, 12), 'Great Axe'),
        ((14, 12), 'Spear'), ((17, 11), 'Hand Axe'), ((25, 11), 'Claw'), ((8, 12), 'Staff'), ((15, 13), 'Composite Bow'),
        ((42, 11), 'Shield')],
    3: [((19, 10), 'Blade'), ((20, 10), 'Club'), ((21, 10), 'Dirk'), ((22, 12), 'Great Blade'), ((23, 12), 'Spear'),
        ((26, 12), 'Scythe'), ((8, 12), 'Staff'), ((18, 13), 'Recurve Bow'), ((42, 11), 'Shield')],
}
COMMON = [  # copies (realm-free), id suffix, price in marks
    ('Strong_Draught_of_Healing', 2), ('Strong_Draught_of_Power', 2), ('Strong_Draught_of_Endurance', 2),
    ('Superior_Elixir_of_Instant_Healing', 4), ('Superior_Elixir_of_Instant_Power', 4),
    ('Superior_Elixir_of_Instant_Endurance', 4), ('CombinedBuffs_Draught', 6), ('CombinedRegens_Draught', 6),
    ('respec_single', 40), ('respec_realm', 100), ('respec_full', 150),
]
PRICE_ARMOUR, PRICE_WEAPON, PRICE_SHIELD, PRICE_CLOAK = 18, 30, 20, 60


def armour_bonuses(obj, lvl):
    a = max(1, lvl // 3)
    b = max(1, lvl // 4)
    if obj == 32:
        return {'Int': b, 'Pie': b, 'Emp': b, 'Dex': b, 'Power': max(1, lvl // 10), 'Hits': int(lvl * 0.6)}
    if obj == 33:
        return {'Dex': a, 'Qui': a, 'Str': b, 'Hits': int(lvl * 0.8)}
    if obj in (34, 37):
        return {'Str': a, 'Dex': a, 'Con': b, 'Hits': int(lvl * 0.8)}
    if obj in (35, 38):
        return {'Str': a, 'Con': a, 'Pie' if obj == 35 else 'Emp': b, 'Hits': int(lvl * 0.8)}
    return {'Str': a, 'Con': a, 'Hits': lvl, 'Slash': max(1, lvl // 10), 'Crush': max(1, lvl // 10), 'Thrust': max(1, lvl // 10)}


def stock_for(name, realm, lvl):
    """[(item spec, price, page)] - item specs as named_uniques takes them."""
    out = []
    for obj in ARMOUR[realm]:
        for slot, word in SLOT_WORD.items():
            w = BODY_WORD.get(obj, word) if slot == 25 else word
            out.append(({'name': "%s Warden's %s %s" % (name, ARMOUR_WORD[obj], w), 'base': [obj, slot], 'level': lvl,
                         'bonuses': armour_bonuses(obj, lvl), 'lore': 'Issued to those who held %s.' % name}, PRICE_ARMOUR, 0))
    for (obj, slot), word in WEAPONS[realm]:
        bon = {'Con': max(1, lvl // 3), 'Hits': int(lvl * 0.8)} if obj == 42 else \
            {'Str': max(1, lvl // 3), 'Dex': max(1, lvl // 4), 'Hits': int(lvl * 0.5)}
        out.append(({'name': "%s Warden's %s" % (name, word), 'base': [obj, slot], 'level': lvl, 'bonuses': bon,
                     'lore': 'From the armoury of %s.' % name}, PRICE_SHIELD if obj == 42 else PRICE_WEAPON, 1))
    out.append(({'name': "%s Defender's Cloak" % name, 'base': [41, 26], 'level': lvl,
                 'bonuses': {'Con': max(1, lvl // 4), 'Hits': lvl},
                 'lore': 'Only those who fought for %s wear its colours.' % name}, PRICE_CLOAK, 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--db', default=str(DB))
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    cols = [d[0] for d in db.execute('select * from ItemTemplate limit 0').description]
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rows, lists = [], []
    # the mark
    base = db.execute("select * from ItemTemplate where Id_nb='aurulite'").fetchone()
    mark = dict(zip(cols, base))
    mark.update(Id_nb='event_mark', ItemTemplate_ID='event_mark', Name='Mark of Valor', PackageID='tw_common',
                Description='Earned by standing with the realm in its events. Tower quartermasters take them.',
                IsTradable=0, MaxCount=5000, Price=0, LastTimeRowUpdated=now)
    rows.append(mark)
    # the shared goods: potions, respec stones (copies, realm-free, priced in marks)
    common = []
    for src, price in COMMON:
        r = db.execute('select * from ItemTemplate where Id_nb=?', (src,)).fetchone()
        if r is None:
            print('missing', src)
            continue
        d = dict(zip(cols, r))
        nid = 'tw_' + src.lower()
        d.update(Id_nb=nid, ItemTemplate_ID=nid, Realm=0, Price=price, PackageID='tw_common', LastTimeRowUpdated=now,
                 Level=1 if not src.startswith('respec') else d['Level'])
        rows.append(d)
        common.append(nid)
    # each tower's gear
    for tid, name, realm, lvl in TOWERS:
        spec = {'prefix': 'tw_' + tid, 'realm': realm, 'items': []}
        priced = stock_for(name, realm, lvl)
        spec['items'] = [p[0] for p in priced]
        _, planned = nu.plan(db, spec)
        lst = 'tower_' + tid
        slots = {0: 0, 1: 0}
        for (it, row, b), (_, price, page) in zip(planned, priced):
            row.update(Price=price, PackageID='tw_' + tid, LastTimeRowUpdated=now, Condition=50000, Durability=50000)
            rows.append(row)
            lists.append((lst, row['Id_nb'], page, slots[page]))
            slots[page] += 1
        for nid in common:
            lists.append((lst, nid, 1, slots[1]))
            slots[1] += 1
        print('%-14s realm %d level %d: %d armour, %d on page 2' % (tid, realm, lvl, slots[0], slots[1]))
        if slots[0] > 30 or slots[1] > 30:
            raise SystemExit('too many items for a page')
    if not a.apply:
        for r in rows[:3] + rows[-3:]:
            print(r['Id_nb'], r['Name'], r['Level'], r['Price'], r.get('Bonus1Type'), r.get('Bonus1'))
        print('\n%d templates, %d list rows (dry run - nothing written)' % (len(rows), len(lists)))
        return
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    new = Path(a.db + '.before-towerstock-%s' % stamp)
    shutil.copy2(a.db, new)
    for old in Path(a.db).parent.glob(Path(a.db).name + '.before-*'):
        if old != new:
            old.unlink()
    print('backup', new)
    db.execute("delete from ItemTemplate where Id_nb='event_mark' or PackageID like 'tw\\_%' escape '\\'")
    db.execute("delete from MerchantItem where ItemListID like 'tower\\_%' escape '\\'")
    sql = 'insert into ItemTemplate (%s) values (%s)' % (','.join(cols), ','.join('?' * len(cols)))
    for r in rows:
        db.execute(sql, [r[c] for c in cols])
    for lst, iid, page, slot in lists:
        db.execute('insert into MerchantItem (ItemListID, ItemTemplateID, PageNumber, SlotPosition, LastTimeRowUpdated, '
                   'MerchantItem_ID) values (?,?,?,?,?,?)', (lst, iid, page, slot, now, '%s_%d_%d' % (lst, page, slot)))
    db.commit()
    print('Written: %d templates, %d list rows.' % (len(rows), len(lists)))


if __name__ == '__main__':
    main()
