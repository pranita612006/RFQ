import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("All tables in db.sqlite3:")
for t in sorted(tables):
    print(" -", t)

conn.close()
