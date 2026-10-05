import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%bop%'")
print("BOP Tables in sqlite3:", cursor.fetchall())

cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%bop%'")
print("BOP Views in sqlite3:", cursor.fetchall())

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = [r[0] for r in cursor.fetchall()]

for tbl in all_tables:
    if 'bop' in tbl.lower() or 'approve' in tbl.lower():
        cursor.execute(f"PRAGMA table_info('{tbl}')")
        cols = cursor.fetchall()
        print(f"\n--- {tbl} Columns ---")
        for c in cols:
            print(f"  {c[1]} ({c[2]})")
        
        cursor.execute(f"SELECT count(*) FROM '{tbl}'")
        print(f"Count: {cursor.fetchone()[0]}")

conn.close()
