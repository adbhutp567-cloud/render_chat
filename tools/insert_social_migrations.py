import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path('db.sqlite3')
if not DB.exists():
    print('db.sqlite3 not found')
    raise SystemExit(1)

migrations = [
    '0001_initial',
    '0002_token_max_lengths',
    '0003_extra_data_default_dict',
    '0004_app_provider_id_settings',
    '0005_socialtoken_nullable_app',
    '0006_alter_socialaccount_extra_data',
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

for name in migrations:
    cur.execute("SELECT 1 FROM django_migrations WHERE app='socialaccount' AND name=?", (name,))
    if cur.fetchone():
        print('Already present:', name)
        continue
    cur.execute(
        "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
        ('socialaccount', name, datetime.utcnow().isoformat()),
    )
    print('Inserted migration record:', name)

conn.commit()
conn.close()
print('Done')
