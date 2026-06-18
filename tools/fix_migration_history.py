import sqlite3
from pathlib import Path

# Find db.sqlite3 by walking up from this file
here = Path(__file__).resolve()
root = here
DB = None
for parent in [here] + list(here.parents):
    candidate = parent / 'db.sqlite3'
    if candidate.exists():
        DB = candidate
        break

if DB is None:
    print('db.sqlite3 not found in workspace parents from', here)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()

print('Before deletion:')
for row in cur.execute("SELECT app, name FROM django_migrations WHERE app IN ('socialaccount','sites') ORDER BY app, name").fetchall():
    print(row)

cur.execute("DELETE FROM django_migrations WHERE app='socialaccount'")
deleted = conn.total_changes
conn.commit()
print('Deleted rows:', deleted)

print('After deletion:')
for row in cur.execute("SELECT app, name FROM django_migrations WHERE app IN ('socialaccount','sites') ORDER BY app, name").fetchall():
    print(row)

conn.close()

print('Done')
