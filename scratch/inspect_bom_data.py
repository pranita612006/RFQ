import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    print("--- tbl_bomcreation remarks & status ---")
    cursor.execute("""
        SELECT DISTINCT "Remark", "Status" FROM tbl_bomcreation;
    """)
    print("tbl_bomcreation distinct Remark & Status:", cursor.fetchall())

    cursor.execute("""
        SELECT COUNT(*) FROM tbl_bomcreation;
    """)
    print("Total rows in tbl_bomcreation:", cursor.fetchone()[0])

    cursor.execute("""
        SELECT COUNT(*) FROM tbl_bomcreation_partselection;
    """)
    print("Total rows in tbl_bomcreation_partselection:", cursor.fetchone()[0])

    print("\nSample rows from tbl_bomcreation:")
    cursor.execute("""
        SELECT "Customer_ID", "ItemCreation_Id", "BOMCreation_Id", "Remark", "Status" FROM tbl_bomcreation LIMIT 5;
    """)
    print(cursor.fetchall())

    print("\nSample rows from tbl_bomcreation_partselection:")
    cursor.execute("""
        SELECT "Customer_ID", "ItemCreation_Id", "BOMCreation_ID", "Table_Id" FROM tbl_bomcreation_partselection LIMIT 5;
    """)
    print(cursor.fetchall())
