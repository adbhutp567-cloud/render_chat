import sqlite3
from pathlib import Path

db = Path('db.sqlite3')
if not db.exists():
    print('db.sqlite3 not found')
    raise SystemExit(1)

conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('Tables:')
for t in tables:
    print('-', t)
conn.close()
