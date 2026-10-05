import os
import sys
sys.path.insert(0, r"d:\N-RFQ")
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as cur:
    print("=== VIEW DEFINITION ===")
    cur.execute("SELECT pg_get_viewdef('\"tbl_OfferSheetPartDetails\"', true);")
    row = cur.fetchone()
    print(row[0] if row else "None")

    print("\n=== SAMPLE FROM VIEW ===")
    cur.execute('SELECT * FROM "tbl_OfferSheetPartDetails" LIMIT 2;')
    cols = [d[0] for d in cur.description]
    print("Cols:", cols)
    for r in cur.fetchall():
        print(r)

    print("\n=== COLUMNS OF tbl_bom_partdetails_master ===")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'tbl_bom_partdetails_master';
    """)
    for r in cur.fetchall():
        print(r)

    print("\n=== COLUMNS OF tbl_bomcreation_partselection ===")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'tbl_bomcreation_partselection';
    """)
    for r in cur.fetchall():
        print(r)
