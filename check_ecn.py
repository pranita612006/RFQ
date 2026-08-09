import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()
from django.db import connection

c = connection.cursor()
c.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE LOWER(table_name) LIKE '%%ecn%%' 
       OR LOWER(table_name) LIKE '%%itemcard%%'
    ORDER BY table_name
""")
tables = [r[0] for r in c.fetchall()]
print("Tables found:", tables)

for tbl in tables:
    c.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, [tbl])
    cols = c.fetchall()
    print(f"\n--- {tbl} ({len(cols)} columns) ---")
    for col_name, col_type in cols:
        print(f"  {col_name}: {col_type}")
