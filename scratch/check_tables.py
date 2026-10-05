import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' OR type='view';")
for r in c.fetchall():
    t_name = r[0]
    if any(k in t_name.lower() for k in ['bom', 'boc', 'part', 'offer', 'qry']):
        print(t_name)
