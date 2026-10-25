"""Apply (or undo) one db-changes/*.sql file to the Offline DAoC database.

    python db-changes/apply.py db-changes/<file>.sql          apply the change
    python db-changes/apply.py db-changes/<file>.sql --undo   run its UNDO section

* Refuses to run while the server (CoreServer.exe) is running.
* Copies the database to E:/Offline DAOC 036c/db-backup/opendaoc.sqlite3.db first
  (one backup only: each run overwrites the previous backup).
* Runs everything in ONE transaction: all or nothing.
Each .sql file holds the change, then a line "-- UNDO", then the statements that reverse it.
"""
import shutil, sqlite3, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent            # playable-v0.36c
DB = ROOT / 'runtime' / 'data' / 'opendaoc.sqlite3.db'
BACKUP_DIR = ROOT.parent / 'db-backup'


def server_running() -> bool:
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq CoreServer.exe'], capture_output=True, text=True).stdout
    return 'CoreServer.exe' in out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    sql_file = Path(sys.argv[1])
    undo = '--undo' in sys.argv[2:]
    text = sql_file.read_text(encoding='utf-8')
    change, _, reverse = text.partition('\n-- UNDO')
    script = reverse.split('\n', 1)[1] if undo else change
    if undo and not reverse:
        print('This file has no -- UNDO section.')
        return 1
    if server_running():
        print('The server is running. Click STOP SERVER in the launcher first.')
        return 1
    BACKUP_DIR.mkdir(exist_ok=True)
    shutil.copy2(DB, BACKUP_DIR / DB.name)
    print('Backed up the database to', BACKUP_DIR / DB.name)
    con = sqlite3.connect(DB, isolation_level=None)
    try:
        con.execute('BEGIN')
        for stmt in split_statements(script):
            con.execute(stmt)
        con.execute('COMMIT')
    except Exception as e:
        con.execute('ROLLBACK')
        print('FAILED, nothing was changed:', e)
        return 1
    finally:
        con.close()
    print(('Undid ' if undo else 'Applied ') + sql_file.name)
    return 0


def split_statements(script: str):
    """Split on ';' at line ends, skipping comment-only lines."""
    buf = []
    for line in script.splitlines():
        if line.strip().startswith('--') and not buf:
            continue
        buf.append(line)
        if line.rstrip().endswith(';') and sqlite3.complete_statement('\n'.join(buf)):
            stmt = '\n'.join(buf).strip()
            if stmt.strip(';').strip():
                yield stmt
            buf = []
    rest = '\n'.join(buf).strip()
    if rest:
        yield rest


if __name__ == '__main__':
    sys.exit(main())
