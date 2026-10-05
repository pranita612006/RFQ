from django.db import connection
c = connection.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
rfq = [t for t in tables if 'rfq' in t.lower()]
print('RFQ tables:', rfq)
