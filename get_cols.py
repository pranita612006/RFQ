import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='tbl_bso_saleslines' ORDER BY ordinal_position")
    print("=== tbl_bso_saleslines ===")
    for row in c.fetchall():
        print(row)

    c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='tbl_blanketso' ORDER BY ordinal_position")
    print("=== tbl_blanketso ===")
    for row in c.fetchall():
        print(row)
