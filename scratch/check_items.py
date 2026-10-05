import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection

with connection.cursor() as cur:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tbl_itemcard'")
    print("tbl_itemcard columns:")
    for r in cur.fetchall():
        print(" ", r)
    
    cur.execute("SELECT * FROM tbl_itemcard WHERE customerid = 'CUST-001'")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print("\ntbl_itemcard CUST-001 rows:")
    for r in rows:
        print(" ", dict(zip(cols, r)))

    cur.execute("SELECT * FROM tbl_bso_saleslines WHERE customer_id = 'CUST-001'")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print("\ntbl_bso_saleslines CUST-001 rows:")
    for r in rows:
        print(" ", dict(zip(cols, r)))
