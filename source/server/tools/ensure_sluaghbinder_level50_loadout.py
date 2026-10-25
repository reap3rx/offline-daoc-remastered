"""Add the isolated Sluaghbinder level-50 launcher loadout, if absent.

This migration is deliberately scoped to the Sluaghbinder test copy.  It clones
the already validated Hibernian templates into class-63-only templates so the
launcher can roll the class at level 50 without weakening class restrictions on
existing items or touching the source installation.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "runtime" / "data" / "opendaoc.sqlite3.db"
BACKUP_ROOT = ROOT / "runtime" / "deployment-backups"


def main() -> None:
    if not DB.is_file():
        raise SystemExit(f"database not found: {DB}")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_ROOT / f"sluaghbinder-level50-{stamp}"
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
        existing = conn.execute(
            "SELECT count(*) FROM offline_level50_loadouts WHERE ClassId=63"
        ).fetchone()[0]
        if existing:
            if existing < 15:
                raise RuntimeError(
                    f"class 63 already has an incomplete loadout ({existing} rows)"
                )
            print(json.dumps({"status": "already-present", "rows": existing}))
            return

        slots = [21, 22, 23, 25, 27, 28, 24, 26, 29, 32, 33, 34, 35, 36]
        sources = [
            (slot, f"offline50_20260904_c44_s{slot}_t{38 if slot in slots[:6] else 41}")
            for slot in slots
        ]
        # Put the normal one-handed blunt and shield in the equipped slots.
        sources.extend(
            [
                (10, "offline50_20260904_c45_s10_t20"),
                (11, "offline50_20260904_c45_s11_t42"),
                # Keep a scythe available in the backpack for Bane/Covenant.
                (40, "offline50_20260904_c56_s12_t26"),
            ]
        )

        columns = [row[1] for row in conn.execute("PRAGMA table_info(ItemTemplate)")]
        insert_sql = (
            "INSERT INTO ItemTemplate ("
            + ",".join('"' + c + '"' for c in columns)
            + ") VALUES ("
            + ",".join("?" for _ in columns)
            + ")"
        )

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        loadout_rows: list[tuple[int, int, str]] = []
        with conn:
            for slot, source_id in sources:
                row = conn.execute(
                    "SELECT * FROM ItemTemplate WHERE Id_nb=?", (source_id,)
                ).fetchone()
                if row is None:
                    raise RuntimeError(f"source item template missing: {source_id}")
                item = dict(row)
                new_id = f"offline50_20260920_c63_s{slot}_t{item['Object_Type']}"
                item["Id_nb"] = new_id
                item["ItemTemplate_ID"] = uuid.uuid4().hex
                item["Name"] = f"Offline level 50 Sluaghbinder {item['Object_Type']}/{slot}"
                item["AllowedClasses"] = "63"
                item["PackageID"] = "Offline50-20260920"
                item["Description"] = "Classic level 50 Sluaghbinder class template"
                item["LastTimeRowUpdated"] = now
                conn.execute(insert_sql, [item.get(c) for c in columns])
                loadout_rows.append((63, slot, new_id))

            conn.executemany(
                "INSERT INTO offline_level50_loadouts(ClassId,SlotPosition,TemplateId) VALUES (?,?,?)",
                loadout_rows,
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
                "rows": len(loadout_rows),
                "backup": str(backup_db),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
