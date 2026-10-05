import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    print("=== Distinct Remarks in tbl_bomcreation ===")
    cursor.execute('SELECT DISTINCT "Remark" FROM tbl_bomcreation;')
    print(cursor.fetchall())

    print("\n=== Distinct Status in tbl_bomcreation ===")
    cursor.execute('SELECT DISTINCT "Status" FROM tbl_bomcreation;')
    print(cursor.fetchall())

    print("\n=== Sample rows from tbl_bomcreation ===")
    cursor.execute('SELECT "Customer_ID", "ItemCreation_Id", "BOMCreation_Id", "Remark", "Status" FROM tbl_bomcreation LIMIT 10;')
    for row in cursor.fetchall():
        print(row)

    print("\n=== Sample rows from tbl_bomcreation_partselection ===")
    cursor.execute('SELECT "Customer_ID", "ItemCreation_Id", "BOMCreation_ID", "Part_Number" FROM tbl_bomcreation_partselection LIMIT 10;')
    for row in cursor.fetchall():
        print(row)
