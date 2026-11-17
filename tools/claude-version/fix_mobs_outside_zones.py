"""Bring the 283 monsters that sit outside every zone back into their dungeons (2026-11-16, Bugs doc).

At startup the server skipped 283 Mob rows in four dungeons because no zone covers where they stand:
  - Tomb of Mithra (region 21): 113 rows at X 73,728+ - one 65,536 wrap too far east (X - 65,536 puts them among
    the dungeon's own spawns);
  - Krondon (region 61): 17 rows with Y under 8,192 - one 65,536 wrap too far north. Among them are the named
    Drihten Elreden, Lurfos the Herald, Orylle and Orshom Brond; the Krondon scripts place their adds at the
    wrapped-back coordinates (OrylleAndOrshom.cs puts Orshom's Fire at 31,406 / 69,599 = 4,055 + 65,536);
  - Iarnvidiur's Lair (region 161): 42 rows near X 489,000 - seven 65,536 wraps east (X - 458,752);
  - Summoner's Hall (region 233): 111 rows and no Zones row at all. The client has the zone (content/zones/zone233,
    1,638.4 m like every dungeon), so it gets the standard dungeon row: zone 233, offset 1/1, 8x8.
A shifted row that lands within DUP units of a spawn of the same name already there is a duplicate and is deleted
rather than stacked on top of it.

  python fix_mobs_outside_zones.py          # dry run: what would change
  python fix_mobs_outside_zones.py apply    # server stopped; backs up the DB first. Idempotent: a second run finds nothing.
"""
import collections, datetime, math, os, shutil, sqlite3, subprocess, sys, uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB = os.environ.get("OFFLINE_DAOC_DB") or os.path.join(ROOT, "runtime", "data", "opendaoc.sqlite3.db")
Z0, Z1 = 8192, 8192 + 65536          # a dungeon zone at offset 1/1, 8x8 (in 8,192-unit steps)
DUP = 150
SHIFTS = {21: (-65536, 0), 61: (0, 65536), 161: (-458752, 0)}

apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
if apply and "coreserver" in subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower():
    sys.exit("CoreServer is running; stop the server first.")

inside = lambda x, y: Z0 <= x < Z1 and Z0 <= y < Z1
con = sqlite3.connect(DB)
moves, drops = [], []
for region, (dx, dy) in SHIFTS.items():
    assert con.execute("select OffsetX, OffsetY, Width, Height from Zones where RegionID=?", (region,)).fetchall() == [(1, 1, 8, 8)], region
    rows = con.execute("select Mob_ID, Name, X, Y, Z from Mob where Region=?", (region,)).fetchall()
    good = [r for r in rows if inside(r[2], r[3])]
    byname = collections.defaultdict(list)
    for r in good:
        byname[r[1]].append(r)
    for mob_id, name, x, y, z in (r for r in rows if not inside(r[2], r[3])):
        nx, ny = x + dx, y + dy
        assert inside(nx, ny), (region, name, x, y)
        near = min((math.hypot(nx - g[2], ny - g[3]) + abs(z - g[4]) for g in byname[name]), default=1e9)
        (drops if near < DUP else moves).append((region, mob_id, name, (x, y), (nx, ny), round(near)))
summoners = con.execute("select count(*) from Zones where RegionID=233").fetchone()[0] == 0
for region in SHIFTS:
    m = sum(1 for r in moves if r[0] == region); d = sum(1 for r in drops if r[0] == region)
    print(f"region {region}: move {m}, delete {d} duplicates")
print("Summoner's Hall zone row:", "add" if summoners else "already there",
      f"({con.execute('select count(*) from Mob where Region=233').fetchone()[0]} mobs)")
named = [r[2] for r in moves if r[0] == 61 and r[2][0].isupper()]
print("Krondon named back:", sorted(set(named)))
if not apply:
    sys.exit("dry run; pass 'apply' to write")

backup = DB.replace(".db", f".before-zone-mob-fix-{datetime.datetime.now():%Y%m%d-%H%M%S}.db")
shutil.copy2(DB, backup)
print("backup", backup)
try:
    for region, mob_id, name, (x, y), (nx, ny), _ in moves:
        assert con.execute("update Mob set X=?, Y=? where Mob_ID=? and X=? and Y=?", (nx, ny, mob_id, x, y)).rowcount == 1
    for region, mob_id, *_ in drops:
        assert con.execute("delete from Mob where Mob_ID=?", (mob_id,)).rowcount == 1
    if summoners:
        assert con.execute("select count(*) from Zones where ZoneID=233").fetchone()[0] == 0
        con.execute("insert into Zones (ZoneID, RegionID, Name, IsLava, DivingFlag, WaterLevel, OffsetY, OffsetX, Width, Height,"
                    " Experience, Realmpoints, Bountypoints, Coin, Realm, LastTimeRowUpdated, Zones_ID)"
                    " values (233, 233, ?, 0, 0, 0, 1, 1, 8, 8, 0, 0, 0, 0, 0, ?, ?)",
                    ("Summoner's Hall", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(uuid.uuid4())))
    con.commit()
finally:
    con.close()
print(f"moved {len(moves)}, deleted {len(drops)} duplicates" + (", added the Summoner's Hall zone" if summoners else ""))
