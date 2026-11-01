"""Catacombs pilot: open Hibernia's Underground Forest (region 96). Default is a read-only dry run.

  python tools\\claude-version\\catacombs_underground_forest_hib.py            (dry run)
  python tools\\claude-version\\catacombs_underground_forest_hib.py --apply    (server, launcher and game closed)
  python tools\\claude-version\\catacombs_underground_forest_hib.py --undo     (takes it all out again)

What --apply writes (after a backup next to the database):
  * 1200 monster and NPC spawns from the Eve of Darkness public database (MIT, github.com/Eve-of-Darkness/db-public,
    data/Mob.*.json, region 96), listed in catacombs_underground_forest_hib.mobs.json. Their NPC templates and gear
    are already in this database; the one Obelisk spawn whose template isn't is left out.
  * a Channeler Glasny at the forest's Hibernian outpost, to get home again
  * the teleport destination "Underground Forest" (Hibernia), offered by every Channeler Glasny and Young Seoltoir:
    the outpost's arrival spot (the public DB's "teleport spell effect" marker)
  * server property enabled_regions = 96, which opens the region although Catacombs stays in disabled_expansions
The zone's client content is built separately (build_zone.py 96). Spawns are found again by region 96 + their own
Mob_IDs, never by name.
"""
import argparse
import datetime
import json
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / 'runtime/data/opendaoc.sqlite3.db'
MOBS = Path(__file__).with_name('catacombs_underground_forest_hib.mobs.json')
REGION = 96
PORTER_ID = 'offline-catacombs-hib-forest-glasny'
TELEPORT_ID = 'offline-catacombs-hib-forest'
ARRIVAL = (18970, 20653, 16179, 3310)          # x, y, z, heading
PORTER = (18890, 20560, 16181, 3310)


def plan(db):
    mobs = json.loads(MOBS.read_text(encoding='utf-8'))
    have = {r[0] for r in db.execute('select Mob_ID from Mob where Region=?', (REGION,))}
    return mobs, have


def apply(db):
    mobs, have = plan(db)
    cols = list(mobs[0])
    sql = 'insert into Mob (%s) values (%s)' % (','.join(cols), ','.join('?' * len(cols)))
    added = 0
    for m in mobs:
        if m['Mob_ID'] in have:
            continue
        db.execute(sql, [m[c] for c in cols])
        added += 1
    # the way home: a copy of an existing Channeler Glasny row, moved to the outpost
    if not db.execute('select 1 from Mob where Mob_ID=?', (PORTER_ID,)).fetchone():
        src = db.execute("select * from Mob where ClassType='DOL.GS.Scripts.LiveTeleporter' and Realm=3 and Region=200 "
                         "limit 1").fetchone()
        names = [d[0] for d in db.execute('select * from Mob limit 0').description]
        row = dict(zip(names, src))
        row.update(Region=REGION, X=PORTER[0], Y=PORTER[1], Z=PORTER[2], Heading=PORTER[3], Mob_ID=PORTER_ID)
        db.execute('insert into Mob (%s) values (%s)' % (','.join(row), ','.join('?' * len(row))), list(row.values()))
    db.execute('delete from Teleport where Teleport_ID=?', (TELEPORT_ID,))
    db.execute("insert into Teleport (Type, TeleportID, Realm, RegionID, X, Y, Z, Heading, LastTimeRowUpdated, Teleport_ID) "
               "values ('', 'Underground Forest', 3, ?, ?, ?, ?, ?, ?, ?)",
               (REGION, *ARRIVAL, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), TELEPORT_ID))
    set_enabled(db, add=True)
    return added


def set_enabled(db, add):
    row = db.execute("select Value from ServerProperty where Key='enabled_regions'").fetchone()
    regions = [r for r in (row[0] if row else '').split(';') if r.strip()]
    regions = [r for r in regions if r != str(REGION)] + ([str(REGION)] if add else [])
    value = ';'.join(regions)
    if row:
        db.execute("update ServerProperty set Value=? where Key='enabled_regions'", (value,))
    else:
        db.execute("insert into ServerProperty (Category, Key, Description, DefaultValue, Value, LastTimeRowUpdated, "
                   "ServerProperty_ID) values ('world', 'enabled_regions', ?, '', ?, ?, ?)",
                   ('Serialized list of region IDs to open although their expansion is in disabled_expansions, '
                    'separated by semi-colon or a range with a dash (ie 96;97)', value,
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'offline-enabled-regions'))


def undo(db):
    mobs, _ = plan(db)
    ids = [m['Mob_ID'] for m in mobs] + [PORTER_ID]
    n = 0
    for i in range(0, len(ids), 500):
        part = ids[i:i + 500]
        n += db.execute('delete from Mob where Region=? and Mob_ID in (%s)' % ','.join('?' * len(part)),
                        [REGION, *part]).rowcount
    db.execute('delete from Teleport where Teleport_ID=?', (TELEPORT_ID,))
    set_enabled(db, add=False)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--undo', action='store_true')
    ap.add_argument('--db', default=str(DB))
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    mobs, have = plan(db)
    print(f'{len(mobs)} spawns listed, {len(have)} already in region {REGION}')
    if not (a.apply or a.undo):
        print('dry run: nothing written (--apply / --undo)')
        return
    backup = Path(a.db + '.before-catacombs-forest-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    shutil.copy2(a.db, backup)
    print('backup', backup)
    with db:
        if a.apply:
            print('added', apply(db), 'spawns, the outpost teleporter, the teleport and enabled_regions')
        else:
            print('removed', undo(db), 'spawns; teleport and enabled_regions entry gone')
    print('region 96 now:', db.execute('select count(*) from Mob where Region=?', (REGION,)).fetchone()[0], 'spawns;',
          'enabled_regions =', db.execute("select Value from ServerProperty where Key='enabled_regions'").fetchone())


if __name__ == '__main__':
    main()
