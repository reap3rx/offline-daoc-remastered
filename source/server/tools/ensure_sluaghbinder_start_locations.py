"""Seed valid Classic/SI Hibernian starts for the isolated Sluaghbinder.

The launcher only accepts authoritative StartupLocation rows.  This migration
copies the existing Celt/Firbolg Hibernian anchors to class 63, preserving the
same random-start behavior as the other Hibernian classes.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "runtime" / "data" / "opendaoc.sqlite3.db"
BACKUP_ROOT = ROOT / "runtime" / "deployment-backups"


def main() -> None:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_ROOT / f"sluaghbinder-starts-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup_db = backup_dir / "opendaoc.sqlite3.db"

    source = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(backup_db)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        already = conn.execute(
            "SELECT count(*) FROM StartupLocation WHERE RealmID=3 AND ClassID=63"
        ).fetchone()[0]
        if already:
            print(json.dumps({"status": "already-present", "rows": already}))
            return

        rows = conn.execute(
            """
            SELECT XPos, YPos, ZPos, Heading, Region, MinVersion, RealmID,
                   RaceID, ClientRegionID, LastTimeRowUpdated
            FROM StartupLocation
            WHERE MinVersion <= 168
              AND RealmID = 3
              AND RaceID IN (9, 10)
              AND ClassID IN (43, 44, 45, 46, 47, 48, 50, 55, 56)
              AND Region IN (200, 181)
              AND (XPos <> 0 OR YPos <> 0 OR ZPos <> 0)
            ORDER BY RaceID, Region, StartupLoc_ID
            """
        ).fetchall()

        unique: list[sqlite3.Row] = []
        seen: set[tuple[int, int, int, int, int]] = set()
        for row in rows:
            key = (row["RaceID"], row["Region"], row["XPos"], row["YPos"], row["ZPos"])
            if key not in seen:
                seen.add(key)
                unique.append(row)
        if not unique:
            raise RuntimeError("no valid Hibernian Celt/Firbolg start anchors found")

        with conn:
            conn.executemany(
                """
                INSERT INTO StartupLocation
                    (XPos, YPos, ZPos, Heading, Region, MinVersion, RealmID,
                     RaceID, ClassID, ClientRegionID, LastTimeRowUpdated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 63, ?, ?)
                """,
                [
                    (
                        row["XPos"],
                        row["YPos"],
                        row["ZPos"],
                        row["Heading"],
                        row["Region"],
                        row["MinVersion"],
                        row["RealmID"],
                        row["RaceID"],
                        row["ClientRegionID"],
                        row["LastTimeRowUpdated"],
                    )
                    for row in unique
                ],
            )
            quick = conn.execute("PRAGMA quick_check").fetchone()[0]
            if quick != "ok":
                raise RuntimeError(f"PRAGMA quick_check failed: {quick}")
    finally:
        conn.close()

    print(
        json.dumps(
            {
                "status": "created",
                "class_id": 63,
                "rows": len(unique),
                "races": sorted({row["RaceID"] for row in unique}),
                "regions": sorted({row["Region"] for row in unique}),
                "backup": str(backup_db),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
