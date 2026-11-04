"""Claude's three bots (owner 2026-11-04): Claudin (Albion, Briton friar), Klauda (Midgard, kobold runemaster) and
Clodagh (Hibernia, Celt bard), level 1, starting in their realm's hub town, added as the launcher adds bots (the
population target follows). Their words: GameServer/bots/autonomous/AutonomousBotPersonas.cs. Server closed.
  python add_claude_bots.py [database]"""
import sqlite3, sys, datetime
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[2] / 'runtime/data/opendaoc.sqlite3.db')
BOTS = [  # name, realm, class id, class, race id, race, gender (1 male, 2 female), hub (region, x, y, z)
    ('Claudin', 1, 10, 'Friar', 1, 'Briton', 1, (1, 559646, 511301, 2456)),
    ('Klauda', 2, 29, 'Runemaster', 8, 'Kobold', 2, (100, 805891, 724274, 4680)),
    ('Clodagh', 3, 48, 'Bard', 9, 'Celt', 2, (200, 346031, 490867, 5200)),
]
c = sqlite3.connect(DB)
now = datetime.datetime.utcnow().isoformat() + 'Z'
for name, realm, cid, cname, rid, rname, gender, (reg, x, y, z) in BOTS:
    if c.execute("select 1 from offline_world_bots where Name=? union select 1 from DOLCharacters where Name=?", (name, name)).fetchone():
        print(name, 'already exists')
        continue
    c.execute("""INSERT INTO offline_world_bots
        (Name, Realm, ClassId, ClassName, RaceId, RaceName, Gender, Level, Experience, RealmPoints,
         ZoneName, Activity, IsOnline, IsAlive, LastUpdateUtc, MoneyCopper, InventoryRevision,
         ZoneId, X, Y, Z, RegionId, Health, Mana, Endurance, BindRegionId, BindX, BindY, BindZ,
         CurrentGoal, ObjectiveProgress, LastMeaningfulProgressUtc, IsRetired)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 0, 'Classic starting area', 'Queued at randomized starting location', 0, 1, ?, 0, 0,
                0, ?, ?, ?, ?, 1, 0, 0, ?, ?, ?, ?, 'Awaiting staggered login queue', ?, ?, 0)""",
              (name, realm, cid, cname, rid, rname, gender, now, x, y, z, reg, reg, x, y, z,
               'Claude\'s bot: starts in the realm\'s hub town', now))
    print('added', name, cname, rname, 'realm', realm)
n = c.execute("select count(*) from offline_world_bots where IsRetired=0").fetchone()[0]
c.execute("UPDATE offline_population_settings SET Value=CASE Key WHEN 'PopulationEnabled' THEN 'true' WHEN 'ActiveTarget' THEN ? ELSE Value END WHERE Key IN ('PopulationEnabled','ActiveTarget')", (str(n),))
c.execute("UPDATE ServerProperty SET Value=CASE `Key` WHEN 'population_enabled' THEN 'true' WHEN 'active_target' THEN ? ELSE Value END WHERE `Key` IN ('population_enabled','active_target')", (str(n),))
c.commit()
print('bots now', n, '| population', c.execute("select Key, Value from offline_population_settings where Key in ('PopulationEnabled','ActiveTarget','HardActiveCap')").fetchall())
