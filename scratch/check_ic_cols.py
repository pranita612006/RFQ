import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    for t in ['tbl_itemcard', 'tbl_itemcard_ecn', 'tbl_applytemplate', 'tbl_itemcard_invoice', 'tbl_rfq_details']:
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", [t])
        cols = cursor.fetchall()
        print(f"=== {t} ({len(cols)} columns) ===")
        for c in cols:
            print(f"  {c[0]}: {c[1]}")


