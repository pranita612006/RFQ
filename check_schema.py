from django.db import connection
c = connection.cursor()
c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tbl_bso_saleslines' ORDER BY ordinal_position")
rows = c.fetchall()
cols = [r[0] for r in rows]
print("SALESLINES:", cols)
