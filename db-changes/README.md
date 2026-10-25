# Database changes

One SQL file per change, named `YYYY-MM-DD-short-description.sql`.
Each file has the change at the top and an `-- UNDO` section that reverses it.
Run them against `runtime/data/opendaoc.sqlite3.db` with the server stopped.
